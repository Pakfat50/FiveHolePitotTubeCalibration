import os
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import MouseEvent
from matplotlib.figure import Figure

from calibration import calibration_digest, save_calibration, analyze_intervals, basis, fit, compare_samples, error_totals
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
    def test_short_result_names(self):
        first=samples()
        other=first.copy()
        other[0,3]+=1
        runs=[(first,100),(other,120)]
        settings=(.3,1,.15,1)
        digest=calibration_digest(runs,settings)
        self.assertEqual(digest,calibration_digest(reversed(runs),settings))
        self.assertNotEqual(digest,calibration_digest([(first,100),(first,120)],settings))
        self.assertNotEqual(digest,calibration_digest([(first,120),(other,100)],settings))
        self.assertNotEqual(digest,calibration_digest(runs,(.4,1,.15,1)))
        with TemporaryDirectory() as folder:
            directory=Path(folder)
            coef=np.ones((10,3))
            points=[{'total_Pa':100}]
            path=save_calibration(directory,coef,points,digest)
            self.assertEqual(path.name,f'cal_{digest[:4]}.csv')
            self.assertEqual(path,save_calibration(directory,coef,points,digest))
            other_digest=digest[:4]+('f' if digest[4]!='f' else '0')+digest[5:]
            collision=save_calibration(directory,coef,points,other_digest)
            self.assertEqual(collision.name,f'cal_{other_digest[:6]}.csv')
            self.assertTrue(path.exists())

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
            p,q='first/run.csv','second/run.csv'
            first=samples()
            second=first.copy()
            second[:,3:6]*=2
            app.root.update()
            answers=iter(('100','220'))
            owners=[]
            def answer_dialog(dialog, window):
                owners.append((str(dialog.transient()),dialog.grab_current()))
                dialog.entry.insert(0,next(answers))
                dialog.ok()
            with patch.object(app.filedialog,'askopenfilenames',return_value=(p,q)) as choose, \
                 patch.object(app.tk.Toplevel,'wait_window',answer_dialog), \
                 patch.object(app,'read_log',side_effect=[first,second]):
                app.add()
            self.assertIs(choose.call_args.kwargs['parent'],app.root)
            self.assertEqual([owner for owner,_ in owners],[str(app.root)]*2)
            self.assertTrue(all(isinstance(grab,app.simpledialog.Dialog) for _,grab in owners))
            app.root.update()
            self.assertEqual(set(app.history_files.pages),{p,q})
            self.assertNotEqual(app.dataset_labels()[p],app.dataset_labels()[q])
            app.tabs.select(app.history)
            app.root.update()
            self.assertEqual(len(app.hfig.axes[0].patches),25)
            with patch('tkinter.messagebox.showerror', side_effect=AssertionError):
                app.run(False)
            app.root.update()
            self.assertEqual(app.calibration_identity.get(),'未保存（一時）')
            self.assertEqual(app.sfig.axes[0].name,'3d')
            app.surface_choice.current(2)
            app.show_surface()
            self.assertIn('q_ref',app.sfig.axes[0].get_zlabel())
            app.tabs.select(app.comparison)
            app.root.update()
            self.assertEqual(len(app.cfig.axes),3)
            app.comparison_files.select(q)
            app.root.update()
            np.testing.assert_allclose(app.cfig.axes[2].lines[1].get_ydata()[0],220)
            self.assertEqual(app.history_files.current(),q)
            app.comparison_files.select(p)
            app.root.update()
            self.assertAlmostEqual(app.cfig.axes[2].lines[1].get_ydata()[0],100)
            rows=[app.rmse_table.item(item,'values') for item in app.rmse_table.get_children()]
            self.assertEqual(len(rows),6)
            self.assertEqual([float(row[-1]) for row in rows[:4]],[5,5,10,10])
            self.assertAlmostEqual(float(rows[-1][-1]),np.sqrt(62.5),places=3)
            app.files.selection_set(q)
            app.remove()
            self.assertIsNone(app.coef)
            self.assertEqual(app.calibration_identity.get(),'未選択')
            self.assertFalse(app.rmse_table.get_children())
            self.assertEqual(list(app.comparison_files.pages),[p])
            with TemporaryDirectory() as folder, patch.object(app,'OUTPUT_DIR',Path(folder)/'output'), patch.object(app.messagebox,'showerror',side_effect=AssertionError):
                app.run(False)
                app.generate_c()
                self.assertEqual(app.calibration_identity.get(),f'保存済み　{app.saved_csv.name}')
                app.run(True)
                outputs=sorted(app.OUTPUT_DIR.glob('*.csv'))
                models=[path for path in outputs if not path.stem.endswith('_points')]
                self.assertEqual((len(outputs),len(models)),(2,1))
                original=app.coef.copy()
                model=models[0]
                self.assertEqual(app.calibration_identity.get(),f'保存済み　{model.name}')
                with patch.object(app.filedialog,'askopenfilename',return_value=str(model)):
                    app.load_result()
                    np.testing.assert_array_equal(app.coef,original)
                    self.assertEqual(len(app.mesh[3]),25)
                    self.assertEqual(len(app.rmse_table.get_children()),2)
                    app.files.selection_set(p)
                    app.remove()
                    model.with_name(model.stem+'_points.csv').unlink()
                    app.load_result()
                    app.generate_c()
                    self.assertEqual(app.calibration_identity.get(),f'読込済み　{model.name}')
                    self.assertTrue((app.OUTPUT_DIR/'C'/model.with_suffix('.h').name).is_file())
                    self.assertEqual(len(app.mesh[3]),0)
                    np.testing.assert_array_equal(app.coef,original)
        finally:
            app.root.destroy()
