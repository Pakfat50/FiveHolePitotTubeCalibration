from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from calibration import TERMS, read_log, analyze_intervals, fit, estimate, write_rows, compare_samples, error_totals
from charts import SURFACES, time_history, surface_mesh, draw_surface, comparison_history

root=tk.Tk()
root.title('5孔ピトー管 較正')
root.geometry(f"{min(1000,root.winfo_screenwidth()-45)}x{min(760,root.winfo_screenheight()-95)}")
tabs=ttk.Notebook(root)
tabs.pack(fill='both',expand=True)
frame=ttk.Frame(tabs,padding=10)
history=ttk.Frame(tabs,padding=8)
surfaces=ttk.Frame(tabs,padding=8)
comparison=ttk.Frame(tabs,padding=8)
for page, name in ((frame,'入力・較正'),(history,'時系列'),(surfaces,'3D較正曲面'),(comparison,'推定値と真値')):
    tabs.add(page,text=name)
logs={}
used_intervals={}
coef=None
mesh=None
files=ttk.Treeview(frame,columns=('file','q'),show='headings',height=7)
for col,title,width in [('file','計測CSV',510),('q','基準動圧 [Pa]',120)]:
    files.heading(col,text=title);files.column(col,width=width)
files.pack(fill='both',expand=True)
def ask_q(value=None):
    return simpledialog.askfloat('基準動圧','このCSVの基準動圧 [Pa]',initialvalue=value,minvalue=0.000001)
def add():
    for p in filedialog.askopenfilenames(filetypes=[('計測CSV','*.csv')]):
        if files.exists(p): continue
        q=ask_q()
        if q is not None:
            try:
                logs[p]=read_log(p)
            except Exception as exc:
                messagebox.showerror('CSV読込',str(exc))
                continue
            files.insert('','end',iid=p,values=(p,q))
            files.selection_set(p)
            inputs_changed()
def edit():
    for item in files.selection():
        q=ask_q(float(files.set(item,'q')))
        if q is not None:
            files.set(item,'q',q)
            inputs_changed()
def remove():
    for item in files.selection():
        del logs[item]
        files.delete(item)
    inputs_changed()
bar=ttk.Frame(frame);bar.pack(anchor='w',pady=5)
for title,fn in [('CSV追加',add),('基準動圧を変更',edit),('選択を除外',remove)]:
    ttk.Button(bar,text=title,command=fn).pack(side='left')
settings=ttk.LabelFrame(frame,text='静定区間・格子設定',padding=8);settings.pack(fill='x')
def entry(parent,i,title,default):
    ttk.Label(parent,text=title).grid(row=i,column=0,sticky='w')
    v=tk.StringVar(value=default);ttk.Entry(parent,textvariable=v,width=12).grid(row=i,column=1)
    return v
params=[entry(settings,i,n,d) for i,(n,d) in enumerate([
    ('静定中の各軸の最大振れ幅 [°]','0.3'),('最短静定時間 [s]','1.0'),
    ('平均から除く前後の時間 [s/端]','0.15'),('流れ角の格子間隔 [°]','1.0')])]
result=tk.StringVar(value='計測CSVを追加してください。')
def parameters():
    width,duration,trim,step=[float(v.get()) for v in params]
    if not np.isfinite([width,duration,trim,step]).all() or min(width,duration,step)<=0 or trim<0 or duration<=2*trim:
        raise ValueError('静定幅・格子間隔は正、最短時間は前後除外時間の合計より大きくしてください。')
    return width,duration,trim,step

def analyze(p,settings):
    return analyze_intervals(logs[p],p,float(files.set(p,'q')),*settings[:3])

def run(save=True):
    global coef,mesh,used_intervals
    try:
        settings=parameters()
        points=[]
        ranges={}
        for p in files.get_children():
            selected,ranges[p]=analyze(p,settings)
            points.extend(selected)
        model=fit(points,settings[3])
        sums=np.zeros((2,3))
        counts=np.zeros((2,3),dtype=np.int64)
        for p,intervals in ranges.items():
            pred,truth=compare_samples(logs[p],float(files.set(p,'q')),model)
            ss,n=error_totals(pred,truth,intervals)
            sums+=ss
            counts+=n
        rmse=np.sqrt(np.divide(sums,counts,out=np.full_like(sums,np.nan),where=counts>0))
        mesh=surface_mesh(points,model)
        used_intervals=ranges
        for var,row in zip(rmse_rows,rmse):
            var.set('     '.join(f'{name}  {v:.3f} {unit}' if np.isfinite(v) else f'{name}  —'
                                 for name,v,unit in zip(('AoA','AoS','動圧'),row,('°','°','Pa'))))
        coef=model
        result.set(f'{len(points)} 静定区間を使用。3D較正曲面を表示できます。')
        if not save:
            tabs.select(surfaces)
            return
        for point in points:
            vals=estimate(model,*[point[k] for k in ('total_Pa','aoa_Pa','aos_Pa')])
            point.update(zip(('alpha_fit_deg','beta_fit_deg','q_fit_Pa'),vals))
        rows=[dict(power_aoa=i,power_aos=j,alpha_deg=c[0],beta_deg=c[1],q_factor=c[2])
              for (i,j),c in zip(TERMS,model)]
        out=filedialog.asksaveasfilename(title='係数CSVの保存',defaultextension='.csv',initialfile='coefficients.csv')
        if not out:return
        points_file=Path(out).with_name(Path(out).stem+'_points.csv')
        if points_file.exists() and not messagebox.askyesno('静定点CSVの上書き',str(points_file)):return
        write_rows(points_file,points);write_rows(out,rows)
        coef=model
        result.set(f'{len(points)} 静定区間を使用。係数と静定点CSVを保存しました。')
    except Exception as exc: messagebox.showerror('較正',str(exc))
actions=ttk.Frame(frame)
actions.pack(anchor='w',pady=7)
ttk.Button(actions,text='較正して曲面を表示',command=lambda: run(False)).pack(side='left')
ttk.Button(actions,text='較正して係数CSVを保存',command=run).pack(side='left')
rmse_box=ttk.LabelFrame(frame,text='RMSE（読み込んだ全CSV・各サンプルを等重みで集計）',padding=4)
rmse_box.pack(fill='x')
rmse_rows=[]
for i,name in enumerate(('全有効区間','採用した静定区間')):
    var=tk.StringVar(value='—')
    rmse_rows.append(var)
    ttk.Label(rmse_box,text=name).grid(row=i,column=0,sticky='w',padx=4)
    ttk.Label(rmse_box,textvariable=var).grid(row=i,column=1,sticky='w',padx=8)
test=ttk.LabelFrame(frame,text='作成した係数で推定',padding=8);test.pack(fill='x')
inputs=[entry(test,i,n,'') for i,n in enumerate(('Total [Pa]','AoA [Pa]','AoS [Pa]'))]
def predict():
    try:
        if coef is None:raise ValueError('先に較正を実行してください。')
        v=[float(i.get()) for i in inputs]
        if not np.isfinite(v).all():raise ValueError('有限の数値を入力してください。')
        a,b,q=estimate(coef,*v)
        result.set(f'迎角 α = {a:.2f}°　 横滑り角 β = {b:.2f}°　 動圧 = {q:.2f} Pa')
    except ValueError as exc:messagebox.showerror('推定',str(exc))
ttk.Button(test,text='推定',command=predict).grid(row=1,column=2,padx=12)
ttk.Label(frame,textvariable=result).pack(anchor='w',pady=8)
history_bar=ttk.Frame(history)
history_bar.pack(fill='x')
ttk.Label(history_bar,text='表示するCSV').pack(side='left')
selected_csv=tk.StringVar()
file_choice=ttk.Combobox(history_bar,state='readonly',textvariable=selected_csv)
file_choice.pack(side='left',expand=True,fill='x',padx=6)
history_note=tk.StringVar()
ttk.Label(history,textvariable=history_note).pack(anchor='w')

surface_bar=ttk.Frame(surfaces)
surface_bar.pack(fill='x')
surface_choice=ttk.Combobox(surface_bar,state='readonly',values=SURFACES,width=16)
surface_choice.current(0)
surface_choice.pack(side='left')
surface_note=tk.StringVar()
ttk.Label(surface_bar,textvariable=surface_note).pack(side='left',padx=10)

comparison_bar=ttk.Frame(comparison)
comparison_bar.pack(fill='x')
ttk.Label(comparison_bar,text='表示するCSV').pack(side='left')
compare_choice=ttk.Combobox(comparison_bar,state='readonly',textvariable=selected_csv)
compare_choice.pack(side='left',expand=True,fill='x',padx=6)
compare_note=tk.StringVar()
ttk.Label(comparison,textvariable=compare_note).pack(anchor='w')

def make_canvas(parent):
    figure=Figure(figsize=(8,5),constrained_layout=True)
    canvas=FigureCanvasTkAgg(figure,master=parent)
    toolbar=NavigationToolbar2Tk(canvas,parent,pack_toolbar=False)
    toolbar.pack(side='bottom',fill='x')
    canvas.get_tk_widget().pack(fill='both',expand=True)
    return figure,canvas,toolbar

hfig,hcanvas,htool=make_canvas(history)
sfig,scanvas,stool=make_canvas(surfaces)

cfig,ccanvas,ctool=make_canvas(comparison)

def show_comparison(event=None):
    p=selected_csv.get()
    cfig.clear()
    if coef is None or p not in used_intervals:
        compare_note.set('入力・較正タブで較正を実行してください。')
    else:
        pred,truth=compare_samples(logs[p],float(files.set(p,'q')),coef)
        comparison_history(cfig,logs[p][:,0],pred,truth,used_intervals[p])
        compare_note.set('青実線：推定値　橙破線：真値　緑の帯：較正に採用した静定区間')
    ctool.update()
    ccanvas.draw_idle()

def show_history(event=None):
    hfig.clear()
    p=file_choice.get()
    if p in logs:
        try:
            points,intervals=analyze(p,parameters())
            time_history(hfig,logs[p],intervals)
            history_note.set(f'緑の帯は平均に使用する区間（{len(points)} 区間）です。')
        except ValueError as exc:
            history_note.set(str(exc))
    else:
        history_note.set('入力・較正タブで計測CSVを追加してください。')
    htool.update()
    hcanvas.draw_idle()

def show_surface(event=None):
    sfig.clear()
    if mesh is None:
        surface_note.set('入力・較正タブで「較正して曲面を表示」を押してください。')
    else:
        draw_surface(sfig,mesh,surface_choice.current())
        surface_note.set('赤点：静定区間の実測値　左ドラッグ：回転　右ドラッグ：拡大・縮小')
    stool.update()
    scanvas.draw_idle()

def inputs_changed(*_):
    global coef,mesh
    coef=mesh=None
    used_intervals.clear()
    for var in rmse_rows:
        var.set('—')
    choices=files.get_children()
    compare_choice.configure(values=choices)
    file_choice.configure(values=choices)
    selected=files.selection()
    if selected:
        file_choice.set(selected[0])
    elif file_choice.get() not in choices:
        file_choice.set(choices[0] if choices else '')
    result.set('入力・設定を反映しました。較正を実行してください。')

def tab_changed(event):
    page=tabs.select()
    if page==str(history):
        show_history()
    elif page==str(comparison):
        show_comparison()
    elif page==str(surfaces):
        show_surface()

def select_history_file(event):
    selected=files.selection()
    if selected:
        file_choice.set(selected[0])

files.bind('<<TreeviewSelect>>',select_history_file)
file_choice.bind('<<ComboboxSelected>>',show_history)
compare_choice.bind('<<ComboboxSelected>>',show_comparison)
surface_choice.bind('<<ComboboxSelected>>',show_surface)
tabs.bind('<<NotebookTabChanged>>',tab_changed)
for param in params:
    param.trace_add('write',inputs_changed)
root.mainloop()
