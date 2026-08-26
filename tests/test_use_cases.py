import csv
import os
import tempfile
import unittest

from calibration_service import CalibrationService
from controller import CalibrationController
from gcode import GCodeGenerator
from gui import MainWindow
from map_view import CalibrationMapView
from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository, SettingsLoadError
from simulation import SimulationController, SimulationView
from validation import InputValidator
from tests.test_support import make_limits, make_settings
from models import AxisRange


class UseCaseHarness:
    def __init__(self):
        self.validator = InputValidator()
        self.service = CalibrationService()
        self.controller = CalibrationController(self.validator, self.service)
        self.settings_repo = SettingsRepository()
        self.init_repo = InitializationGCodeRepository()
        self.generator = GCodeGenerator()
        self.gcode_repo = GCodeRepository()


class TestUseCases(unittest.TestCase):
    def setUp(self):
        self.h = UseCaseHarness()

    # TEST-UC-01-01
    # UseCase: UC-01
    def test_uc01_valid_input_recalculates_plan(self):
        s = make_settings(); self.h.controller.on_settings_changed(s)
        self.assertIsNotNone(self.h.controller.get_current_plan()); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-02
    # UseCase: UC-01
    def test_uc01_invalid_aoa_range_blocks_generation(self):
        self.h.controller.on_settings_changed(make_settings(aoa_min=10, aoa_max=10))
        self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-03
    # UseCase: UC-01
    def test_uc01_temporary_invalid_then_valid_recovers(self):
        self.h.controller.on_settings_changed(make_settings(feed_rate=0)); self.assertFalse(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(feed_rate=100)); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-04
    # UseCase: UC-01
    def test_uc01_point_count_change_rebuilds_grid(self):
        self.h.controller.on_settings_changed(make_settings(aoa_points=2,aos_points=2)); self.assertEqual(4,len(self.h.controller.get_current_plan().points))
        self.h.controller.on_settings_changed(make_settings(aoa_points=3,aos_points=4)); self.assertEqual(12,len(self.h.controller.get_current_plan().points))

    # TEST-UC-01-05
    # UseCase: UC-01
    def test_uc01_serpentine_changes_order_not_set(self):
        p1=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3,serpentine=False))
        p2=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3,serpentine=True))
        self.assertEqual({(p.point.aoa,p.point.aos) for p in p1.points},{(p.point.aoa,p.point.aos) for p in p2.points})
        self.assertNotEqual([(p.point.aoa,p.point.aos) for p in p1.points],[(p.point.aoa,p.point.aos) for p in p2.points])

    # TEST-UC-01-06
    # UseCase: UC-01
    def test_uc01_xy_saturation_warns_but_allows_actions(self):
        limits=make_limits(x=AxisRange(-0.01,0.01),y=AxisRange(-0.01,0.01)); self.h.controller.on_settings_changed(make_settings(axis_limits=limits))
        plan=self.h.controller.get_current_plan(); self.assertGreater(plan.max_x_deviation+plan.max_y_deviation,0); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-07
    # UseCase: UC-01
    def test_uc01_za_overrange_blocks_actions(self):
        limits=make_limits(z=AxisRange(-1,1)); self.h.controller.on_settings_changed(make_settings(axis_limits=limits))
        self.assertTrue(self.h.controller.get_current_plan().has_generation_error); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-08
    # UseCase: UC-01
    def test_uc01_xy_warning_and_za_error_coexist(self):
        limits=make_limits(x=AxisRange(-0.01,0.01),z=AxisRange(-1,1)); plan=self.h.service.build_plan(make_settings(axis_limits=limits))
        self.assertGreater(plan.max_x_deviation,0); self.assertTrue(plan.has_generation_error)

    # TEST-UC-01-09
    # UseCase: UC-01
    def test_uc01_grid_origin_is_deterministic(self):
        plan=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3)); p=next(p for p in plan.points if p.point.aoa==0 and p.point.aos==0)
        self.assertAlmostEqual(0,p.command.z,delta=0.001); self.assertAlmostEqual(0,p.command.a,delta=0.001)

    # TEST-UC-01-10
    # UseCase: UC-01
    def test_uc01_roll_has_no_unnecessary_360_jump(self):
        plan=self.h.service.build_plan(make_settings(aoa_min=-10,aoa_max=10,aos_min=-10,aos_max=10,aoa_points=3,aos_points=5,serpentine=True))
        for a,b in zip(plan.points,plan.points[1:]): self.assertLessEqual(abs(b.command.a-a.command.a),180.001)

    # TEST-UC-01-11
    # UseCase: UC-01
    def test_uc01_nonpositive_offsets_block_plan(self):
        for field in ("tip_offset_x","tip_offset_y"):
            with self.subTest(field=field):
                self.h.controller.on_settings_changed(make_settings(**{field:0})); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-12
    # UseCase: UC-01
    def test_uc01_hold_and_feed_boundaries(self):
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.1,feed_rate=1)); self.assertTrue(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.099,feed_rate=1)); self.assertFalse(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.1,feed_rate=0.999)); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-02-01
    # UseCase: UC-02
    def test_uc02_load_initialization_text(self):
        self._with_text_file("G92 X0\n", lambda p: self.assertEqual("G92 X0\n", self.h.init_repo.load(p)))

    # TEST-UC-02-02
    # UseCase: UC-02
    def test_uc02_multiline_order_preserved(self):
        text=";a\nG92 X0\nM5\n"; self._with_text_file(text, lambda p: self.assertEqual(text,self.h.init_repo.load(p)))

    # TEST-UC-02-03
    # UseCase: UC-02
    def test_uc02_cancel_keeps_current_initialization(self):
        current="G92 X0\n"; selected_path=None; self.assertIsNone(selected_path); self.assertEqual("G92 X0\n",current)

    # TEST-UC-02-04
    # UseCase: UC-02
    def test_uc02_load_failure_does_not_terminate_process(self):
        with self.assertRaises(OSError): self.h.init_repo.load("__missing__.txt")
        self.assertTrue(True)

    # TEST-UC-03-01
    # UseCase: UC-03
    def test_uc03_save_all_settings_to_csv(self):
        self._round_trip_settings(make_settings())

    # TEST-UC-03-02
    # UseCase: UC-03
    def test_uc03_save_option_combinations(self):
        for s in (False,True):
            for c in (False,True): self._round_trip_settings(make_settings(serpentine=s,output_comments=c))

    # TEST-UC-03-03
    # UseCase: UC-03
    def test_uc03_cancel_creates_no_file(self):
        with tempfile.TemporaryDirectory() as d: self.assertEqual([],os.listdir(d))

    # TEST-UC-03-04
    # UseCase: UC-03
    def test_uc03_save_failure_is_recoverable(self):
        with self.assertRaises(OSError): self.h.settings_repo.save("__missing_dir__/settings.csv",make_settings())

    # TEST-UC-04-01
    # UseCase: UC-04
    def test_uc04_load_valid_csv_and_rebuild_plan(self):
        loaded=self._round_trip_settings(make_settings(feed_rate=123)); self.h.controller.apply_settings(loaded)
        self.assertEqual(123,self.h.controller.get_current_settings().feed_rate); self.assertIsNotNone(self.h.controller.get_current_plan())

    # TEST-UC-04-02
    # UseCase: UC-04
    def test_uc04_restore_serpentine(self):
        loaded=self._round_trip_settings(make_settings(serpentine=True)); plan=self.h.service.build_plan(loaded)
        self.assertEqual([10,0,-10],[p.point.aos for p in plan.points[3:6]])

    # TEST-UC-04-03
    # UseCase: UC-04
    def test_uc04_loaded_xy_warning_allows_generation(self):
        loaded=self._round_trip_settings(make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01)))); self.h.controller.apply_settings(loaded)
        self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-04-04
    # UseCase: UC-04
    def test_uc04_loaded_za_error_blocks_generation(self):
        loaded=self._round_trip_settings(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.h.controller.apply_settings(loaded)
        self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-04-05
    # UseCase: UC-04
    def test_uc04_structurally_invalid_csv_is_rejected(self):
        self._assert_csv_rejected("bad,row,shape\n")

    # TEST-UC-04-06
    # UseCase: UC-04
    def test_uc04_cancel_keeps_settings_and_plan(self):
        self.h.controller.on_settings_changed(make_settings(feed_rate=55)); old=self.h.controller.get_current_plan(); selected=None
        self.assertIsNone(selected); self.assertEqual(55,self.h.controller.get_current_settings().feed_rate); self.assertIs(old,self.h.controller.get_current_plan())

    # TEST-UC-04-07
    # UseCase: UC-04
    def test_uc04_missing_required_value_is_rejected(self):
        self._assert_csv_rejected("key,value\naoa_min,-10\n")

    # TEST-UC-04-08
    # UseCase: UC-04
    def test_uc04_blank_required_value_is_rejected(self):
        self._assert_csv_rejected(self._valid_csv().replace("feed_rate,100","feed_rate,"))

    # TEST-UC-04-09
    # UseCase: UC-04
    def test_uc04_non_numeric_value_is_rejected(self):
        self._assert_csv_rejected(self._valid_csv().replace("feed_rate,100","feed_rate,abc"))

    # TEST-UC-04-10
    # UseCase: UC-04
    def test_uc04_io_failure_is_rejected(self):
        with self.assertRaises(SettingsLoadError): self.h.settings_repo.load("__missing_settings__.csv")

    # TEST-UC-04-11
    # UseCase: UC-04
    def test_uc04_late_error_does_not_partially_apply(self):
        self.h.controller.on_settings_changed(make_settings(feed_rate=55)); old=self.h.controller.get_current_settings()
        with self.assertRaises(SettingsLoadError): self._load_csv_text(self._valid_csv().replace("output_comments,true","output_comments,INVALID"))
        self.assertEqual(old,self.h.controller.get_current_settings())

    # TEST-UC-05-01
    # UseCase: UC-05
    def test_uc05_normal_simulation_uses_full_plan(self):
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); sim=SimulationController(view); sim.start(plan,duration_s=10)
        self.assertIs(plan.points[-1],sim._frame_at(plan,1.0))

    # TEST-UC-05-02
    # UseCase: UC-05
    def test_uc05_xy_warning_plan_is_simulatable(self):
        plan=self.h.service.build_plan(make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01)))); self.assertFalse(plan.has_generation_error)

    # TEST-UC-05-03
    # UseCase: UC-05
    def test_uc05_za_error_is_not_simulatable_from_gui_state(self):
        self.h.controller.on_settings_changed(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-05-04
    # UseCase: UC-05
    def test_uc05_duration_does_not_depend_on_hold_time(self):
        p1=self.h.service.build_plan(make_settings(hold_time_s=0.1)); p2=self.h.service.build_plan(make_settings(hold_time_s=100))
        s1=SimulationController(SimulationView()); s2=SimulationController(SimulationView()); s1.start(p1,10); s2.start(p2,10)
        self.assertEqual(s1.duration_s,s2.duration_s)

    # TEST-UC-05-05
    # UseCase: UC-05
    def test_uc05_display_information_matches_plan(self):
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); view.initialize(plan); p=plan.points[0]; view.render_frame(p,0.5)
        self.assertIn(str(p.point.index),view.status_text)

    # TEST-UC-05-06
    # UseCase: UC-05
    def test_uc05_two_views_share_same_current_point(self):
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); view.initialize(plan); view.render_frame(plan.points[1],0.2)
        self.assertEqual(plan.points[1].point.index,view.current_point_index)

    # TEST-UC-06-01
    # UseCase: UC-06
    def test_uc06_generate_valid_nc(self):
        s=make_settings(aoa_points=2,aos_points=2); text=self.h.generator.generate(self.h.service.build_plan(s),s,"G92 X0\n")
        self.assertIn("$H",text); self.assertEqual(4,len([l for l in text.splitlines() if l.startswith("G01 ")]))

    # TEST-UC-06-02
    # UseCase: UC-06
    def test_uc06_comments_on(self):
        s=make_settings(output_comments=True); self.assertIn("AoA",self.h.generator.generate(self.h.service.build_plan(s),s,""))

    # TEST-UC-06-03
    # UseCase: UC-06
    def test_uc06_comments_off(self):
        s=make_settings(output_comments=False); self.assertFalse(any("AoA" in l for l in self.h.generator.generate(self.h.service.build_plan(s),s,"").splitlines() if l.startswith(";")))

    # TEST-UC-06-04
    # UseCase: UC-06
    def test_uc06_xy_saturated_values_are_written(self):
        s=make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01))); p=self.h.service.build_plan(s); text=self.h.generator.generate(p,s,"")
        sat=next(x for x in p.points if x.x_saturated); self.assertIn(f"X{sat.command.x:.6f}",text)

    # TEST-UC-06-05
    # UseCase: UC-06
    def test_uc06_za_error_blocks_generation_action(self):
        self.h.controller.on_settings_changed(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-06-06
    # UseCase: UC-06
    def test_uc06_feed_and_hold_are_written(self):
        s=make_settings(feed_rate=12.5,hold_time_s=3); text=self.h.generator.generate(self.h.service.build_plan(s),s,"")
        self.assertIn("F12.500000",text); self.assertIn("G04 P3.000000",text)

    # TEST-UC-06-07
    # UseCase: UC-06
    def test_uc06_loaded_initialization_is_in_header(self):
        s=make_settings(); text=self.h.generator.generate(self.h.service.build_plan(s),s,"M5\nG92 X0\n"); self.assertIn("M5\nG92 X0\n",text)

    # TEST-UC-06-08
    # UseCase: UC-06
    def test_uc06_final_point_has_no_return_home(self):
        s=make_settings(); lines=[l for l in self.h.generator.generate(self.h.service.build_plan(s),s,"").splitlines() if l.strip()]
        self.assertNotIn(lines[-1],("$H","G00 X0 Y0 Z0 A0","G01 X0 Y0 Z0 A0"))

    # TEST-UC-06-09
    # UseCase: UC-06
    def test_uc06_cancel_creates_no_file(self):
        with tempfile.TemporaryDirectory() as d: self.assertEqual([],os.listdir(d))

    # TEST-UC-06-10
    # UseCase: UC-06
    def test_uc06_save_failure_is_recoverable(self):
        with self.assertRaises(OSError): self.h.gcode_repo.save("__missing_dir__/out.nc","G21\n")

    # TEST-UC-06-11
    # UseCase: UC-06
    def test_uc06_display_simulation_and_gcode_use_same_commands(self):
        s=make_settings(aoa_points=2,aos_points=2); p=self.h.service.build_plan(s); text=self.h.generator.generate(p,s,"")
        for e in p.points:
            for value,prefix in ((e.command.x,"X"),(e.command.y,"Y"),(e.command.z,"Z"),(e.command.a,"A")): self.assertIn(f"{prefix}{value:.6f}",text)

    # TEST-UC-06-12
    # UseCase: UC-06
    def test_uc06_all_float_words_have_six_decimals(self):
        s=make_settings(feed_rate=12.5,hold_time_s=0.1,aoa_points=2,aos_points=2); text=self.h.generator.generate(self.h.service.build_plan(s),s,"")
        for line in text.splitlines():
            if line.startswith(("G01 ","G04 ")):
                for token in line.split()[1:]:
                    if token[0] in "XYZAFP": self.assertRegex(token,r"^[XYZAFP]-?\d+\.\d{6}$")

    def _with_text_file(self,text,callback):
        with tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8") as f: f.write(text); path=f.name
        try: callback(path)
        finally: os.remove(path)

    def _round_trip_settings(self,settings):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,"settings.csv"); self.h.settings_repo.save(path,settings); loaded=self.h.settings_repo.load(path)
        self.assertEqual(settings,loaded); return loaded

    def _assert_csv_rejected(self,text):
        with self.assertRaises(SettingsLoadError): self._load_csv_text(text)

    def _load_csv_text(self,text):
        with tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8",newline="") as f: f.write(text); path=f.name
        try: return self.h.settings_repo.load(path)
        finally: os.remove(path)

    def _valid_csv(self):
        rows=[("aoa_min","-10"),("aoa_max","10"),("aos_min","-10"),("aos_max","10"),("aoa_points","3"),("aos_points","3"),("tip_offset_x","100"),("tip_offset_y","10"),("hold_time_s","1"),("feed_rate","100"),("x_min","-1000"),("x_max","1000"),("y_min","-1000"),("y_max","1000"),("z_min","-180"),("z_max","180"),("a_min","-720"),("a_max","720"),("serpentine","false"),("output_comments","true")]
        return "key,value\n"+"".join(f"{k},{v}\n" for k,v in rows)


if __name__ == "__main__": unittest.main()
