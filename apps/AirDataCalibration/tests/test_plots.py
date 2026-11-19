import os
import unittest
from unittest.mock import patch

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import MouseEvent
from matplotlib.figure import Figure

from calibration import analyze_intervals, basis, fit, compare_samples, error_totals
from charts import draw_surface, time_history, surface_mesh, comparison_history


def samples():
    blocks=[]
    for alpha in (-12,-6,0,6,12):
        for beta in (-12,-6,0,6,12):
            a,b=np.radians([alpha,beta])
            x,y,z=np.cos(a)*np.cos(b),np.sin(b),np.sin(a)*np.cos(b)
            pitch,roll=np.degrees([np.arctan2(np.hypot(y,z),x),np.arctan2(y,z)])
            row=[0,pitch,roll,100,alpha,beta]
            block=np.tile(row,(150,1))
            block[:,0]=len(blocks)*1600+np.arange(150)*10
            blocks.append(block)
    return np.vstack(blocks)


class TestPlots(unittest.TestCase):
    def test_history_matches_trimmed_rows_after_clock_reset(self):
        raw=samples()[:300]
        raw[150:,0]-=1600
        original=raw.copy()
        points,ranges=analyze_intervals(raw,'test',100,.3,1,.15)
        self.assertEqual(ranges,[(15,135),(165,285)])
        self.assertEqual([p['n'] for p in points],[120,120])
        np.testing.assert_equal(raw,original)
        fig=Figure()
        time_history(fig,raw,ranges)
        top,bottom=fig.axes
        self.assertEqual(len(top.patches),2)
        self.assertEqual(len(bottom.lines),3)
        top.set_xlim(.2,.8)
        self.assertEqual(bottom.get_xlim(),(.2,.8))
        self.assertTrue(np.isnan(bottom.lines[0].get_xdata()).any())

    def test_surfaces_match_exported_polynomial_and_rotate(self):
        points,_=analyze_intervals(samples(),'test',100,.3,1,.15)
        coef=fit(points,1)
        mesh=surface_mesh(points,coef)
        np.testing.assert_allclose(mesh[2],basis(*mesh[0].T)@coef)
        self.assertEqual(len(mesh[3]),25)
        fig=Figure()
        canvas=FigureCanvasAgg(fig)
        for i in range(3):
            ax=draw_surface(fig,mesh,i)
            canvas.draw()
            x,y=ax.transAxes.transform((.5,.5))
            angle=(ax.elev,ax.azim,ax.roll)
            for name,dx in [('button_press_event',0),('motion_notify_event',40),('button_release_event',40)]:
                event=MouseEvent(name,canvas,x+dx,y,button=1)
                canvas.callbacks.process(name,event)
            self.assertNotEqual(angle,(ax.elev,ax.azim,ax.roll))

    def test_reference_and_sample_rmse(self):
        # 推定値を0°, 0°, Totalとする既知係数。Total=0は推定不能。
        coef=np.zeros((10,3))
        coef[0,2]=1
        raw=np.array([[0,30,90,90,0,0],[10,0,0,120,0,0],[20,0,0,0,0,0]],float)
        pred,truth=compare_samples(raw,100,coef)
        np.testing.assert_allclose(truth[0],[0,30,100],atol=1e-12)
        np.testing.assert_allclose(pred[:2,2],[90,120])
        self.assertTrue(np.isnan(pred[-1]).all())
        ss,n=error_totals(pred,truth,[(0,1)])
        np.testing.assert_array_equal(n,[[2,2,2],[1,1,1]])
        np.testing.assert_allclose(np.sqrt(ss/n),[[0,30/np.sqrt(2),np.sqrt(250)],[0,30,10]],atol=1e-12)
        fig=Figure()
        comparison_history(fig,raw[:,0],pred,truth,[(0,1)])
        self.assertEqual([len(ax.lines) for ax in fig.axes],[2,2,2])
        np.testing.assert_equal(fig.axes[2].lines[1].get_ydata(),[100,100,100])
        fig.axes[1].set_xlim(0,.01)
        self.assertEqual(fig.axes[2].get_xlim(),(0,.01))

    @unittest.skipUnless(os.environ.get('DISPLAY') or os.name=='nt','GUI display required')
    def test_embedded_tabs(self):
        with patch('tkinter.Tk.mainloop'):
            import app
        try:
            p='sample.csv'
            app.logs[p]=samples()
            app.files.insert('','end',iid=p,values=(p,100))
            app.files.selection_set(p)
            app.inputs_changed()
            app.tabs.select(app.history)
            app.root.update()
            self.assertEqual(len(app.hfig.axes[0].patches),25)
            with patch('tkinter.messagebox.showerror', side_effect=AssertionError):
                app.run(False)
            app.root.update()
            self.assertEqual(app.sfig.axes[0].name,'3d')
            app.surface_choice.current(2)
            app.show_surface()
            self.assertIn('q_ref',app.sfig.axes[0].get_zlabel())
            app.tabs.select(app.comparison)
            app.root.update()
            self.assertEqual(len(app.cfig.axes),3)
            self.assertIn('0.000 Pa',app.rmse_rows[1].get())
            app.inputs_changed()
            self.assertEqual(app.rmse_rows[1].get(),'—')
        finally:
            app.root.destroy()
