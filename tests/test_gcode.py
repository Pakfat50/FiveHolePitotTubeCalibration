import unittest

from calibration_service import CalibrationService
from gcode import GCodeGenerator
from tests.test_support import make_settings, make_limits
from models import AxisRange


class TestGCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = GCodeGenerator()
        self.service = CalibrationService()

    def _generate(self, settings=None, init="G92 X0\n"):
        settings = settings or make_settings(aoa_points=2, aos_points=2)
        plan = self.service.build_plan(settings)
        return self.generator.generate(plan, settings, init)

    # TEST-UNIT-066
    # Requirements: REQ-GCODE-002
    def test_header_contains_required_commands(self):
        text = self._generate()
        for token in ("; User initialization G-code", "$H", "G21", "G90", "G94"):
            self.assertIn(token, text)

    # TEST-UNIT-067
    # Requirements: REQ-INPUT-006, REQ-GCODE-002
    def test_initialization_text_preserved_in_order(self):
        init = ";a\nG92 X0\nM5\n"
        text = self._generate(init=init)
        self.assertIn(init, text)

    # TEST-UNIT-068
    # Requirements: REQ-GCODE-003
    def test_each_move_has_four_axes_and_feed(self):
        lines = [l for l in self._generate().splitlines() if l.startswith("G01 ")]
        self.assertTrue(lines)
        for line in lines:
            for word in ("X", "Y", "Z", "A", "F"):
                self.assertIn(word, line)

    # TEST-UNIT-069
    # Requirements: REQ-GCODE-003
    def test_g_numbers_are_zero_padded(self):
        text = self._generate()
        self.assertIn("G01 ", text)
        self.assertIn("G04 ", text)

    # TEST-UNIT-070
    # Requirements: REQ-INPUT-004, REQ-GCODE-003
    def test_feed_rate_has_six_decimal_places(self):
        text = self._generate(make_settings(feed_rate=12.5, aoa_points=2, aos_points=2))
        self.assertIn("F12.500000", text)

    # TEST-UNIT-071
    # Requirements: REQ-INPUT-004, REQ-GCODE-003
    def test_hold_time_has_six_decimal_places(self):
        text = self._generate(make_settings(hold_time_s=3.0, aoa_points=2, aos_points=2))
        self.assertIn("G04 P3.000000", text)

    # TEST-UNIT-072
    # Requirements: REQ-INPUT-007, REQ-GCODE-004
    def test_comments_enabled(self):
        text = self._generate(make_settings(output_comments=True, aoa_points=2, aos_points=2))
        self.assertIn("AoA", text); self.assertIn("AoS", text)

    # TEST-UNIT-073
    # Requirements: REQ-INPUT-007, REQ-GCODE-004
    def test_comments_disabled(self):
        text = self._generate(make_settings(output_comments=False, aoa_points=2, aos_points=2))
        point_comments = [l for l in text.splitlines() if l.startswith(";") and "AoA" in l]
        self.assertEqual([], point_comments)

    # TEST-UNIT-074
    # Requirements: REQ-GCODE-005
    def test_no_return_home_after_final_point(self):
        lines = [l.strip() for l in self._generate().splitlines() if l.strip()]
        self.assertFalse(lines[-1] in ("$H", "G00 X0 Y0 Z0 A0", "G01 X0 Y0 Z0 A0"))

    # TEST-UNIT-075
    # Requirements: REQ-LIMIT-001, REQ-GCODE-003
    def test_saturated_actual_command_is_written(self):
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        settings = make_settings(axis_limits=limits, aoa_points=2, aos_points=2)
        plan = self.service.build_plan(settings)
        saturated = next(p for p in plan.points if p.x_saturated or p.y_saturated)
        text = self.generator.generate(plan, settings, "")
        self.assertIn(f"X{saturated.command.x:.6f}", text)
        self.assertIn(f"Y{saturated.command.y:.6f}", text)


if __name__ == "__main__": unittest.main()
