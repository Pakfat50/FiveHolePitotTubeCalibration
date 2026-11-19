"""5孔ピトー管の静定点抽出、流れ角への変換、TM765型の較正。"""
import csv
import hashlib
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


def flow_angles(pitch, roll):
    """装置の姿勢からTM765の迎角・横滑り角へ変換する（スカラー・配列共通）。"""
    th,ph = np.deg2rad(pitch),np.deg2rad(roll)
    x,y,z = np.cos(th),np.sin(th)*np.sin(ph),np.sin(th)*np.cos(ph)
    return np.rad2deg(np.arctan2(z,x)),np.rad2deg(np.arctan2(y,np.hypot(x,z)))


def stable_points(path, qref, width, min_sec, trim):
    """両軸の全振幅が許容幅以内の連続区間を検出し、前後を除いて平均する。"""
    return analyze_intervals(read_log(path), path, qref, width, min_sec, trim)[0]


def analyze_intervals(raw, path, qref, width, min_sec, trim):
    """平均値と使用した行の半開区間を返す。角度の展開は作業コピーで行う。"""
    data = raw.copy()
    points = []
    intervals = []
    start = 0
    def finish(end):
        block = data[start:end]
        if len(block)<2 or block[-1,0]-block[0,0] < 1000*min_sec:
            return
        first = np.searchsorted(block[:,0], block[0,0]+1000*trim)
        last = np.searchsorted(block[:,0], block[-1,0]-1000*trim, side='right')
        b = block[first:last]
        if len(b)<2:
            return
        pitch,roll,total,aoa,aos = b[:,1:].mean(axis=0)
        if total<=0 or abs(pitch)>=90:
            return
        alpha,beta = flow_angles(pitch,roll)
        intervals.append((start+first,start+last))
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
    return points, intervals


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

def compare_samples(raw, qref, coef):
    """CSV各行の推定値と真値を、迎角・横滑り角・動圧の列順で返す。"""
    time,pitch,roll,total,aoa,aos = raw.T
    valid = np.isfinite(time) & np.isfinite(total) & (total > 0) & np.isfinite(aoa) & np.isfinite(aos)
    predicted = np.full((len(raw),3),np.nan)
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        fitted = basis(aoa[valid]/total[valid],aos[valid]/total[valid]) @ coef
        fitted[:,2] *= total[valid]
        predicted[valid] = np.where(np.isfinite(fitted),fitted,np.nan)
    attitude_ok = np.isfinite(pitch) & np.isfinite(roll) & (np.abs(pitch)<90)
    truth = np.full_like(predicted,np.nan)
    truth[attitude_ok,:2] = np.column_stack(flow_angles(pitch[attitude_ok],roll[attitude_ok]))
    truth[:,2] = qref
    truth[~np.isfinite(time)] = np.nan
    return predicted,truth


def error_totals(predicted, truth, intervals):
    """全区間・採用区間別、出力別の二乗誤差和と有効数（ファイル間で加算可）。"""
    residual = predicted-truth
    accepted = np.zeros(len(residual),dtype=bool)
    for first,last in intervals:
        accepted[first:last] = True
    squares = np.where(np.isfinite(residual), residual, 0)**2
    valid = np.isfinite(residual)
    return (np.stack((squares.sum(axis=0),squares[accepted].sum(axis=0))),
            np.stack((valid.sum(axis=0),valid[accepted].sum(axis=0))))


def read_coefficients(path):
    """指数で10項を照合し、従来形式の係数CSVも行順に依存せず復元する。"""
    columns = ('alpha_deg', 'beta_deg', 'q_factor')
    terms = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'power_aoa', 'power_aos', *columns}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError('較正係数CSVを選択してください。必要な列が不足しています。')
        for row in reader:
            term = int(row['power_aoa']), int(row['power_aos'])
            values = [float(row[key]) for key in columns]
            if term not in TERMS or term in terms or not np.isfinite(values).all():
                raise ValueError('係数CSVに不正な指数、重複項、または非有限値があります。')
            terms[term] = values
    if len(terms) != len(TERMS):
        raise ValueError('3次較正式の10項が揃っていません。')
    return np.array([terms[t] for t in TERMS])


def read_surface_points(path):
    """係数に付属する静定点のうち、曲面の表示に必要な列を読む。"""
    columns = ('aoa_Pa', 'aos_Pa', 'total_Pa', 'qref_Pa', 'alpha_deg', 'beta_deg')
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(columns).issubset(reader.fieldnames or ()):
            raise ValueError('静定点CSVの列が不足しています。')
        points = [{k: float(row[k]) for k in columns} for row in reader]
    if not points or any(p['total_Pa'] <= 0 or not np.isfinite(list(p.values())).all() for p in points):
        raise ValueError('静定点CSVの値を確認してください。')
    return points


def calibration_digest(datasets, settings):
    """較正に使う6列と基準動圧、設定を照合する。パスやログの選択順には依存しない。"""
    parts = []
    for raw, qref in datasets:
        h = hashlib.sha256(np.asarray([qref], dtype='<f8').tobytes())
        h.update(np.asarray(raw, dtype='<f8', order='C').tobytes())
        parts.append(h.digest())
    digest = hashlib.sha256(b'AirDataCalibration-v1\0')
    digest.update(np.asarray(settings, dtype='<f8').tobytes())
    for part in sorted(parts):
        digest.update(part)
    return digest.hexdigest()


def save_calibration(directory, model, points, digest):
    """通常はハッシュの先頭4桁で保存する。既存結果と衝突した場合だけ2桁ずつ延長する。"""
    directory.mkdir(parents=True, exist_ok=True)
    rows = [dict(power_aoa=i, power_aos=j, alpha_deg=a, beta_deg=b, q_factor=k,
                 input_sha256=digest)
            for (i,j), (a,b,k) in zip(TERMS, model)]
    for length in range(4, len(digest)+1, 2):
        stem = f'cal_{digest[:length]}'
        out = directory / f'{stem}.csv'
        companion = directory / f'{stem}_points.csv'
        if out.exists():
            with out.open(encoding='utf-8-sig', newline='') as stream:
                saved = list(csv.DictReader(stream))
            if len(saved)==len(TERMS) and all(row.get('input_sha256')==digest for row in saved) and companion.is_file():
                if np.allclose(read_coefficients(out), model, rtol=1e-12, atol=1e-12):
                    return out
            continue
        created = []
        try:
            for path, data in ((companion, points), (out, rows)):
                with path.open('x', encoding='utf-8-sig', newline='') as stream:
                    created.append(path)
                    writer = csv.DictWriter(stream, fieldnames=list(data[0]))
                    writer.writeheader()
                    writer.writerows(data)
            return out
        except FileExistsError:
            for path in created:
                path.unlink(missing_ok=True)
        except Exception:
            for path in created:
                path.unlink(missing_ok=True)
            raise
    raise FileExistsError('同じ識別子のファイルが既にあります。output フォルダを確認してください。')
