"""時系列図と、実測の差圧比領域内での逆較正曲面。"""
import numpy as np
from scipy.spatial import Delaunay
from calibration import basis

SURFACES = ('迎角 α', '横滑り角 β', '動圧補正係数')
ZLABELS = ('Angle of attack [deg]', 'Sideslip [deg]', 'q_ref / Total [-]')


def time_history(figure, raw, intervals):
    figure.clear()
    attitude, pressure = figure.subplots(2, 1, sharex=True)
    attitude.set_ylabel('Angle [deg]')
    pressure.set_ylabel('Differential pressure [Pa]')
    pressure.set_xlabel('Elapsed time [s]')
    ticks = raw[:, 0]
    # 時計が巻き戻ったら新しい時系列として直後に並べ、境界の線は切る。
    delta = np.diff(ticks)
    elapsed = np.r_[0, np.cumsum(np.where(np.isfinite(delta) & (delta > 0), delta, 0))]/1000 if len(raw) else ticks
    cuts = np.flatnonzero(~np.isfinite(delta) | (delta <= 0) | (delta > 50)) + 1
    x = np.insert(elapsed, cuts, np.nan)
    for axis in (attitude, pressure):
        for i, (first, last) in enumerate(intervals):
            axis.axvspan(elapsed[first], elapsed[last-1], color='#45ae84', alpha=.22,
                         label='Used for calibration' if i == 0 and axis is attitude else None)
        axis.grid(alpha=.25)
    for axis, col, name, color in (
        (attitude,2,'Roll','#215c9c'), (attitude,1,'Pitch','#b34d14'),
        (pressure,3,'Total','#006e60'), (pressure,4,'AoA','#215c9c'), (pressure,5,'AoS','#b34d14')):
        values = np.where(np.isfinite(ticks),raw[:,col],np.nan)
        axis.plot(x,np.insert(values,cuts,np.nan),label=name,color=color,linewidth=1)
    for axis in (attitude,pressure):
        axis.legend(loc='upper left', ncol=3, fontsize=8)


def surface_mesh(points, coef):
    """測定点の凸包境界を含む細分メッシュ上でCSVと同じ10項を評価する。"""
    ratios = np.array([[p['aoa_Pa']/p['total_Pa'],p['aos_Pa']/p['total_Pa']] for p in points])
    measured = np.array([[p['alpha_deg'],p['beta_deg'],p['qref_Pa']/p['total_Pa']] for p in points])
    hull = Delaunay(np.unique(ratios, axis=0))
    a,s = np.meshgrid(*(np.linspace(lo,hi,36) for lo,hi in zip(ratios.min(axis=0),ratios.max(axis=0))))
    grid = np.column_stack([a.ravel(),s.ravel()])
    nodes = np.unique(np.vstack([ratios,grid[hull.find_simplex(grid)>=0]]),axis=0)
    faces = Delaunay(nodes).simplices
    fitted = basis(*nodes.T) @ coef
    return nodes, faces, fitted, ratios, measured


def draw_surface(figure, mesh, index):
    figure.clear()
    ax = figure.add_subplot(projection='3d')
    nodes, faces, fitted, ratios, measured = mesh
    ax.plot_trisurf(*nodes.T, fitted[:,index], triangles=faces, cmap='viridis',
                    alpha=.74, linewidth=0, antialiased=True)
    ax.scatter(*ratios.T, measured[:,index],color='#ad301a',s=17,depthshade=False,label='Measured')
    ax.set(xlabel='AoA / Total [-]',ylabel='AoS / Total [-]',zlabel=ZLABELS[index])
    ax.legend(loc='upper left')
    return ax
