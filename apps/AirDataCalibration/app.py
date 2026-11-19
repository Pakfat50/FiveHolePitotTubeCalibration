from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import numpy as np
from calibration import TERMS, stable_points, fit, estimate, write_rows

root=tk.Tk()
root.title('5孔ピトー管 較正')
frame=ttk.Frame(root,padding=14)
frame.pack(fill='both',expand=True)
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
        if q is not None: files.insert('','end',iid=p,values=(p,q))
def edit():
    for item in files.selection():
        q=ask_q(float(files.set(item,'q')))
        if q is not None: files.set(item,'q',q)
bar=ttk.Frame(frame);bar.pack(anchor='w',pady=5)
for title,fn in [('CSV追加',add),('基準動圧を変更',edit),('選択を除外',lambda: files.delete(*files.selection()))]:
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
coef=None
def run():
    global coef
    try:
        width,duration,trim,step=[float(v.get()) for v in params]
        if not np.isfinite([width,duration,trim,step]).all() or min(width,duration,step)<=0 or trim<0 or duration<=2*trim:
            raise ValueError('設定値と前後除外後の有効時間を確認してください。')
        points=[]
        for p in files.get_children():
            points.extend(stable_points(p,float(files.set(p,'q')),width,duration,trim))
        model=fit(points,step)
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
ttk.Button(frame,text='較正して係数CSVを保存',command=run).pack(anchor='w',pady=7)
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
root.mainloop()
