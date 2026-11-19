"""5孔ピトー管の静定点抽出、流れ角への変換、TM765型の較正。"""
import csv
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay
from scipy.interpolate import RBFInterpolator

FIELDS = ('timestamp_ms','pitch_deg','roll_deg','dp_total_Pa','dp_aoa_Pa','dp_aos_Pa')
TERMS = [(0,0),(1,0),(0,1),(2,0),(1,1),(0,2),(3,0),(2,1),(1,2),(0,3)]


def read_log(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        missing = set(FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path}: 列がありません {missing}')
        def number(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return np.nan
        return np.asarray([[number(row[k]) for k in FIELDS] for row in reader], float).reshape(-1,6)


def stable_points(path, qref, width, min_sec, trim):
    """両軸の全振幅が許容幅以内の連続区間を検出し、前後を除いて平均する。"""
    data = read_log(path)
    points = []
    start = 0
    def finish(end):
        block = data[start:end]
        if len(block)<2 or block[-1,0]-block[0,0] < 1000*min_sec:
            return
        b = block[(block[:,0]>=block[0,0]+1000*trim)&(block[:,0]<=block[-1,0]-1000*trim)]
        if len(b)<2:
            return
        pitch,roll,total,aoa,aos = b[:,1:].mean(axis=0)
        if total<=0 or abs(pitch)>=90:
            return
        th,ph = np.deg2rad([pitch,roll])
        x,y,z = np.cos(th),np.sin(th)*np.sin(ph),np.sin(th)*np.cos(ph)
        alpha,beta = np.rad2deg([np.arctan2(z,x),np.arctan2(y,np.hypot(x,z))])
        points.append(dict(file=str(path),start_ms=b[0,0],end_ms=b[-1,0],n=len(b),
                           pitch_deg=pitch,roll_deg=(roll+180)%360-180,alpha_deg=alpha,beta_deg=beta,
                           total_Pa=total,aoa_Pa=aoa,aos_Pa=aos,qref_Pa=qref))
    # 欠測や時刻断絶をまたいで別姿勢を連結しない。
    for i,row in enumerate(data):
        if not np.isfinite(row).all():
            finish(i)
            start=i+1
            continue
        if i>start and not (0 < row[0]-data[i-1,0] <= 50):
            finish(i)
            start=i
        if i==start:
            low=row[1:3].copy(); high=low.copy()
            continue
        row[2]=data[i-1,2]+(row[2]-data[i-1,2]+180)%360-180
        lo=np.minimum(low,row[1:3]); hi=np.maximum(high,row[1:3])
        if np.any(hi-lo>width):
            finish(i)
            start=i
            low=row[1:3].copy(); high=low.copy()
        else:
            low,high=lo,hi
    finish(len(data))
    return points


def basis(a,s):
    return np.stack([a**i*s**j for i,j in TERMS],axis=-1)


def fit(points, step):
    if len(points)<10:
        raise ValueError('静定点が不足しています（異なる流向が最低10点必要です）。')
    angles=np.array([[p['alpha_deg'],p['beta_deg']] for p in points])
    values=np.array([[p[k]/p['total_Pa'] for k in ('aoa_Pa','aos_Pa','qref_Pa')] for p in points])
    unique,idx=np.unique(angles.round(6),axis=0,return_inverse=True)
    if len(unique)<10 or np.linalg.matrix_rank(unique-unique.mean(axis=0))<2:
        raise ValueError('2方向に広がった異なる流向が10点以上必要です。')
    means=np.zeros((len(unique),3))
    np.add.at(means,idx,values)
    means/=np.bincount(idx)[:,None]
    if np.linalg.matrix_rank(basis(means[:,0],means[:,1]))<10:
        raise ValueError('実測差圧比では3次式の10項を識別できません。較正姿勢を追加してください。')
    lower=np.ceil(unique.min(axis=0)/step); upper=np.floor(unique.max(axis=0)/step)
    if np.prod(np.maximum(0,upper-lower+1))>500000:
        raise ValueError('格子が細かすぎます。格子間隔を大きくしてください。')
    grid=np.stack(np.meshgrid(*(np.arange(l,h+1)*step for l,h in zip(lower,upper))),axis=-1).reshape(-1,2)
    grid=grid[Delaunay(unique).find_simplex(grid,tol=1e-10)>=0]
    if len(grid)<10:
        raise ValueError('実測範囲内の格子点が不足しています。格子間隔を小さくしてください。')
    # 散在点向けの2次元薄板スプライン。格子は実測角の凸包内に限定する。
    a,s,k=RBFInterpolator(unique,means,kernel='thin_plate_spline')(grid).T
    coef,_,rank,_=np.linalg.lstsq(basis(a,s),np.column_stack((grid,k)),rcond=None)
    if rank<10:
        raise ValueError('格子点で3次式の10項を識別できません。')
    return coef


def estimate(coef,total,aoa,aos):
    if total<=0:
        raise ValueError('推定には正のTotal差圧が必要です。')
    alpha,beta,k=basis(aoa/total,aos/total)@coef
    return alpha,beta,total*k


def write_rows(path, rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
