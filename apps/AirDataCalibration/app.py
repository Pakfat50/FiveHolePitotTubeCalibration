from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from calibration import calibration_digest, read_coefficients, read_surface_points, save_calibration, read_log, analyze_intervals, fit, estimate, compare_samples, error_totals
from c_export import export_c
from charts import SURFACES, time_history, surface_mesh, draw_surface, comparison_history

root=tk.Tk()
root.title('5孔ピトー管 較正')
root.geometry(f"{min(1000,root.winfo_screenwidth()-45)}x{min(760,root.winfo_screenheight()-95)}")
identity_bar=ttk.Frame(root,padding=(10,5))
identity_bar.pack(fill='x')
ttk.Label(identity_bar,text='使用中の較正データ：').pack(side='left')
calibration_identity=tk.StringVar(value='未選択')
ttk.Label(identity_bar,textvariable=calibration_identity).pack(side='left')
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
loaded_path=None
saved_csv=None
preview_points=[]
OUTPUT_DIR=Path(__file__).resolve().parent / 'output'
files=ttk.Treeview(frame,columns=('file','q'),show='headings',height=7)
for col,title,width in [('file','計測CSV',510),('q','基準動圧 [Pa]',120)]:
    files.heading(col,text=title);files.column(col,width=width)
files.pack(fill='both',expand=True)
def ask_q(path,value=None):
    return simpledialog.askfloat('基準動圧',f'{path}\n基準動圧 [Pa]',parent=root,initialvalue=value,minvalue=0.000001)
def add():
    for p in filedialog.askopenfilenames(parent=root,filetypes=[('計測CSV','*.csv')]):
        if files.exists(p): continue
        q=ask_q(p)
        if q is not None:
            try:
                logs[p]=read_log(p)
            except Exception as exc:
                messagebox.showerror('CSV読込',str(exc),parent=root)
                continue
            files.insert('','end',iid=p,values=(p,q))
            files.selection_set(p)
            inputs_changed()
def edit():
    for item in files.selection():
        q=ask_q(item,float(files.set(item,'q')))
        if q is not None:
            files.set(item,'q',q)
            inputs_changed()
def remove():
    for item in files.selection():
        del logs[item]
        files.delete(item)
    inputs_changed()
bar=ttk.Frame(frame);bar.pack(anchor='w',pady=5)
for title,fn in [('CSV追加（複数選択可）',add),('基準動圧を変更',edit),('選択を除外',remove)]:
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

def refresh_calibration_identity():
    if coef is None:
        text='未選択'
    elif loaded_path is not None:
        text=f'読込済み　{loaded_path.name}'
    elif saved_csv is not None:
        text=f'保存済み　{saved_csv.name}'
    else:
        text='未保存（一時）'
    calibration_identity.set(text)

def run(save=True):
    global coef,mesh,used_intervals,loaded_path,saved_csv,preview_points
    try:
        settings=parameters()
        points=[]
        ranges={}
        for p in files.get_children():
            selected,ranges[p]=analyze(p,settings)
            points.extend(selected)
        model=fit(points,settings[3])
        next_mesh=surface_mesh(points,model)
        update_rmse(model,ranges)
        loaded_path=saved_csv=None
        preview_points=points
        coef,mesh,used_intervals=model,next_mesh,ranges
        refresh_calibration_identity()
        result.set(f'{len(points)} 静定区間を使用。3D較正曲面を表示できます。')
        if not save:
            tabs.select(surfaces)
            return
        saved_csv=save_current()
        refresh_calibration_identity()
        result.set(f'保存先：output/{saved_csv.name}')
    except Exception as exc: messagebox.showerror('較正',str(exc),parent=root)

def save_current():
    for point in preview_points:
        vals=estimate(coef,*[point[k] for k in ('total_Pa','aoa_Pa','aos_Pa')])
        point.update(zip(('alpha_fit_deg','beta_fit_deg','q_fit_Pa'),vals))
    digest=calibration_digest(((logs[p],float(files.set(p,'q'))) for p in used_intervals),parameters())
    return save_calibration(OUTPUT_DIR,coef,preview_points,digest)

def generate_c():
    global saved_csv
    try:
        if coef is None:
            raise ValueError('先に較正を実行するか、較正結果を読み込んでください。')
        if loaded_path is None and saved_csv is None:
            saved_csv=save_current()
            refresh_calibration_identity()
        header=export_c(OUTPUT_DIR/'C',coef,loaded_path or saved_csv)
        result.set(f'Cコード保存先：output/C/{header.name}')
    except Exception as exc:
        messagebox.showerror('Cコード生成',str(exc),parent=root)

def update_rmse(model,ranges):
    sums=np.zeros((2,3))
    counts=np.zeros((2,3),dtype=np.int64)
    table_rows=[]
    labels=dataset_labels()
    for p,intervals in ranges.items():
        qref=float(files.set(p,'q'))
        pred,truth=compare_samples(logs[p],qref,model)
        ss,n=error_totals(pred,truth,intervals)
        table_rows.extend(rmse_values(labels[p],qref,ss,n))
        sums+=ss
        counts+=n
    if len(ranges)>1:
        table_rows.extend(rmse_values('全CSV','—',sums,counts))
    rmse_table.delete(*rmse_table.get_children())
    for row in table_rows:
        rmse_table.insert('','end',values=row)

def load_result():
    global coef,mesh,used_intervals,loaded_path
    filename=filedialog.askopenfilename(parent=root,title='較正結果読込',initialdir=OUTPUT_DIR if OUTPUT_DIR.is_dir() else OUTPUT_DIR.parent,
                                        filetypes=[('係数CSV','*.csv')])
    if not filename:
        return
    try:
        path=Path(filename)
        model=read_coefficients(path)
        companion=path.with_name(path.stem+'_points.csv')
        points=read_surface_points(companion) if companion.exists() else []
        next_mesh=surface_mesh(points,model)
        settings=parameters() if logs else None
        ranges={p:analyze(p,settings)[1] for p in logs}
        update_rmse(model,ranges)
        coef,mesh,used_intervals,loaded_path=model,next_mesh,ranges,path
        refresh_calibration_identity()
        result.set(f'読込：{path.name}')
        tabs.select(surfaces)
        show_surface()
    except Exception as exc:
        messagebox.showerror('較正結果読込',str(exc),parent=root)

actions=ttk.Frame(frame)
actions.pack(anchor='w',pady=7)
ttk.Button(actions,text='較正して曲面を表示',command=lambda: run(False)).pack(side='left')
ttk.Button(actions,text='較正して係数CSVを保存',command=run).pack(side='left')
ttk.Button(actions,text='較正結果読込',command=load_result).pack(side='left')
ttk.Button(actions,text='Cコード生成',command=generate_c).pack(side='left')
def dataset_labels():
    names=[Path(p).name for p in logs]
    return {p: Path(p).name if names.count(Path(p).name)==1 else str(Path(p)) for p in logs}

def rmse_values(label,qref,sums,counts):
    values=np.sqrt(np.divide(sums,counts,out=np.full_like(sums,np.nan),where=counts>0))
    for scope,row in zip(('全有効区間','採用静定区間'),values):
        yield (label,qref,scope,*[f'{v:.3f}' if np.isfinite(v) else '—' for v in row])

rmse_box=ttk.LabelFrame(frame,text='データ別RMSE',padding=4)
rmse_box.pack(fill='x')
rmse_table=ttk.Treeview(rmse_box,columns=('file','q','scope','alpha','beta','dp'),show='headings',height=4)
for key,title,width in [('file','CSV',190),('q','基準動圧 [Pa]',100),('scope','評価区間',110),
                        ('alpha','AoA [°]',80),('beta','AoS [°]',80),('dp','動圧 [Pa]',90)]:
    rmse_table.heading(key,text=title)
    rmse_table.column(key,width=width,anchor='w' if key in ('file','scope') else 'e')
rmse_scroll=ttk.Scrollbar(rmse_box,command=rmse_table.yview)
rmse_table.configure(yscrollcommand=rmse_scroll.set)
rmse_scroll.pack(side='right',fill='y')
rmse_table.pack(fill='x',expand=True)
test=ttk.LabelFrame(frame,text='作成した係数で推定',padding=8);test.pack(fill='x')
inputs=[entry(test,i,n,'') for i,n in enumerate(('Total [Pa]','AoA [Pa]','AoS [Pa]'))]
def predict():
    try:
        if coef is None:raise ValueError('先に較正を実行してください。')
        v=[float(i.get()) for i in inputs]
        if not np.isfinite(v).all():raise ValueError('有限の数値を入力してください。')
        a,b,q=estimate(coef,*v)
        result.set(f'迎角 α = {a:.2f}°　 横滑り角 β = {b:.2f}°　 動圧 = {q:.2f} Pa')
    except ValueError as exc:messagebox.showerror('推定',str(exc),parent=root)
ttk.Button(test,text='推定',command=predict).grid(row=1,column=2,padx=12)
ttk.Label(frame,textvariable=result).pack(anchor='w',pady=8)
class DatasetTabs:
    """横に収まらない数のCSVでも矢印で移動できるタブ。グラフは一枚を再利用する。"""
    def __init__(self,parent):
        bar=ttk.Frame(parent)
        bar.pack(fill='x')
        self.pages={}
        self.notebook=ttk.Notebook(bar,height=1)
        for label,delta in (('▶',1),('◀',-1)):
            ttk.Button(bar,text=label,width=3,command=lambda d=delta:self.step(d)).pack(side='right')
        self.notebook.pack(side='left',fill='x',expand=True)

    def step(self,delta):
        keys=list(self.pages)
        if keys:
            index=keys.index(self.current())
            self.select(keys[max(0,min(len(keys)-1,index+delta))])

    def current(self):
        selected=self.notebook.select()
        return next((p for p,page in self.pages.items() if str(page)==selected),None)

    def select(self,p):
        if p in self.pages and self.current()!=p:
            self.notebook.select(self.pages[p])

    def update_files(self,labels):
        for p in list(self.pages):
            if p not in labels:
                self.pages.pop(p).destroy()
        for p,label in labels.items():
            if p not in self.pages:
                self.pages[p]=ttk.Frame(self.notebook)
                self.notebook.add(self.pages[p],text=label)
            else:
                self.notebook.tab(self.pages[p],text=label)

history_files=DatasetTabs(history)
history_note=tk.StringVar()
ttk.Label(history,textvariable=history_note).pack(anchor='w')

surface_bar=ttk.Frame(surfaces)
surface_bar.pack(fill='x')
surface_choice=ttk.Combobox(surface_bar,state='readonly',values=SURFACES,width=16)
surface_choice.current(0)
surface_choice.pack(side='left')
surface_note=tk.StringVar()
ttk.Label(surface_bar,textvariable=surface_note).pack(side='left',padx=10)

comparison_files=DatasetTabs(comparison)
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
    p=comparison_files.current()
    cfig.clear()
    if coef is None or p not in used_intervals:
        compare_note.set('入力・較正タブで較正を実行してください。')
    else:
        pred,truth=compare_samples(logs[p],float(files.set(p,'q')),coef)
        comparison_history(cfig,logs[p][:,0],pred,truth,used_intervals[p])
        compare_note.set(f'{Path(p).name}（{files.set(p,"q")} Pa）　青実線：推定値　橙破線：真値　緑の帯：選択ログの静定区間')
    ctool.update()
    ccanvas.draw_idle()

def show_history(event=None):
    hfig.clear()
    p=history_files.current()
    if p in logs:
        try:
            points,intervals=analyze(p,parameters())
            time_history(hfig,logs[p],intervals)
            history_note.set(f'{Path(p).name}（{files.set(p,"q")} Pa）　緑の帯は平均に使用する区間（{len(points)} 区間）です。')
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
        domain='赤点：静定区間の実測値' if len(mesh[3]) else '静定点CSVなし：仮の表示範囲（各差圧比 ±1）'
        source=f'{loaded_path.name}　' if loaded_path else ''
        surface_note.set(source+domain+'　左ドラッグ：回転　右ドラッグ：拡大・縮小')
    stool.update()
    scanvas.draw_idle()

def inputs_changed(*_):
    global coef,mesh
    used_intervals.clear()
    rmse_table.delete(*rmse_table.get_children())
    labels=dataset_labels()
    for group in (history_files,comparison_files):
        group.update_files(labels)
    if loaded_path is not None:
        try:
            settings=parameters() if logs else None
            ranges={p:analyze(p,settings)[1] for p in logs}
            update_rmse(coef,ranges)
            used_intervals.update(ranges)
            result.set(f'読込：{loaded_path.name}')
        except ValueError as exc:
            result.set(str(exc))
        return
    coef=mesh=None
    refresh_calibration_identity()
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
        history_files.select(selected[0])
        comparison_files.select(selected[0])

def dataset_changed(group,other,view,draw):
    if tabs.select()==str(view):
        other.select(group.current())
        draw()

files.bind('<<TreeviewSelect>>',select_history_file)
history_files.notebook.bind('<<NotebookTabChanged>>',lambda e:dataset_changed(history_files,comparison_files,history,show_history))
comparison_files.notebook.bind('<<NotebookTabChanged>>',lambda e:dataset_changed(comparison_files,history_files,comparison,show_comparison))
surface_choice.bind('<<ComboboxSelected>>',show_surface)
tabs.bind('<<NotebookTabChanged>>',tab_changed)
for param in params:
    param.trace_add('write',inputs_changed)
root.mainloop()
