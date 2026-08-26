import unittest

from calibration_service import CalibrationService
from tests.test_support import make_limits, make_settings
from models import AxisRange


class TestCalibrationService(unittest.TestCase):
    def setUp(self):
        self.service = CalibrationService()

    # TEST-UNIT-060
    # Requirements: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001
    def test_build_plan_creates_evaluation_for_every_point(self):
        plan = self.service.build_plan(make_settings(aoa_points=2, aos_points=3))
        self.assertEqual(6, len(plan.points))

    # TEST-UNIT-061
    # Requirements: REQ-LIMIT-002
    def test_plan_aggregates_max_xy_deviation(self):
        limits = make_limits(x=AxisRange(-0.1, 0.1), y=AxisRange(-0.1, 0.1))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertAlmostEqual(max(p.x_deviation for p in plan.points), plan.max_x_deviation)
        self.assertAlmostEqual(max(p.y_deviation for p in plan.points), plan.max_y_deviation)

    # TEST-UNIT-062
    # Requirements: REQ-LIMIT-003
    def test_any_rotational_error_blocks_generation(self):
        limits = make_limits(z=AxisRange(-1.0, 1.0))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(plan.has_generation_error)
        self.assertTrue(any(p.rotational_error for p in plan.points))

    # TEST-UNIT-063
    # Requirements: REQ-LIMIT-001, REQ-LIMIT-002
    def test_xy_saturation_alone_does_not_block_generation(self):
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(any(p.x_saturated or p.y_saturated for p in plan.points))
        self.assertFalse(plan.has_generation_error)

    # TEST-UNIT-064
    # Requirements: REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-004
    def test_serpentine_plan_keeps_scan_order_and_continuity(self):
        plan = self.service.build_plan(make_settings(aoa_points=3, aos_points=3, serpentine=True))
        rows = [[p.point.aos for p in plan.points[i:i+3]] for i in range(0, 9, 3)]
        self.assertEqual([[-10,0,10],[10,0,-10],[-10,0,10]], rows)
        for previous, current in zip(plan.points, plan.points[1:]):
            self.assertLessEqual(abs(current.command.a - previous.command.a), 180.0 + 1e-9)

    # TEST-UNIT-065
    # Requirements: REQ-POS-001, REQ-LIMIT-001
    def test_ideal_and_actual_commands_are_both_preserved(self):
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        saturated = next(p for p in plan.points if p.x_saturated or p.y_saturated)
        self.assertNotEqual((saturated.ideal_command.x, saturated.ideal_command.y),
                            (saturated.command.x, saturated.command.y))


if __name__ == "__main__": unittest.main()
