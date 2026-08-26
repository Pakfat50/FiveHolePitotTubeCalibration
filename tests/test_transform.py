import math
import unittest

from transform import AngleTransformer
from tests.test_support import ABS_TOL, make_limits
from models import AxisRange


class TestAngleTransformer(unittest.TestCase):
    def setUp(self):
        self.t = AngleTransformer()
        self.limits = make_limits()

    # TEST-UNIT-025
    # Requirements: REQ-TRANS-001, REQ-TRANS-002
    def test_origin_transform(self):
        z, a = self.t.transform(0.0, 0.0, None, self.limits)
        self.assertAlmostEqual(0.0, z, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, a, delta=ABS_TOL)

    # TEST-UNIT-026
    # Requirements: REQ-TRANS-002
    def test_positive_aoa_zero_aos(self):
        z, a = self.t.transform(10.0, 0.0, None, self.limits)
        self.assertAlmostEqual(10.0, z, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, a, delta=ABS_TOL)

    # TEST-UNIT-027
    # Requirements: REQ-TRANS-002
    def test_negative_aoa_zero_aos_reproduces_input(self):
        z, a = self.t.transform(-10.0, 0.0, None, self.limits)
        self.assertTrue(math.isfinite(z) and math.isfinite(a))
        self._assert_reproduces(-10.0, 0.0, z, a)

    # TEST-UNIT-028
    # Requirements: REQ-TRANS-002
    def test_zero_aoa_positive_aos(self):
        z, a = self.t.transform(0.0, 10.0, None, self.limits)
        self._assert_reproduces(0.0, 10.0, z, a)

    # TEST-UNIT-029
    # Requirements: REQ-TRANS-002
    def test_general_solution_matches_formula(self):
        aoa, aos = 12.0, 7.0
        u, v = math.tan(math.radians(aoa)), math.tan(math.radians(aos))
        expected_z = math.degrees(math.atan(math.hypot(u, v)))
        expected_a = math.degrees(math.atan2(v, u))
        z, a = self.t.transform(aoa, aos, None, self.limits)
        self.assertAlmostEqual(expected_z, z, delta=ABS_TOL)
        self.assertAlmostEqual(expected_a, a, delta=ABS_TOL)

    # TEST-UNIT-030
    # Requirements: REQ-TRANS-002
    def test_quadrant_ii(self):
        z, a = self.t.transform(-10.0, 10.0, None, self.limits)
        self.assertTrue(90.0 < a <= 180.0)

    # TEST-UNIT-031
    # Requirements: REQ-TRANS-002
    def test_quadrant_iii(self):
        z, a = self.t.transform(-10.0, -10.0, None, self.limits)
        self.assertTrue(-180.0 <= a < -90.0 or 180.0 <= a < 270.0)

    # TEST-UNIT-032
    # Requirements: REQ-TRANS-002
    def test_quadrant_iv(self):
        z, a = self.t.transform(10.0, -10.0, None, self.limits)
        self.assertTrue(-90.0 < a < 0.0 or 270.0 < a < 360.0)

    # TEST-UNIT-033
    # Requirements: REQ-TRANS-004
    def test_unwrap_plus_360(self):
        self.assertAlmostEqual(181.0, self.t._unwrap_angle(-179.0, 179.0), delta=ABS_TOL)

    # TEST-UNIT-034
    # Requirements: REQ-TRANS-004
    def test_unwrap_minus_360(self):
        self.assertAlmostEqual(-181.0, self.t._unwrap_angle(179.0, -179.0), delta=ABS_TOL)

    # TEST-UNIT-035
    # Requirements: REQ-TRANS-004
    def test_unwrap_avoids_358_degree_jump(self):
        value = self.t._unwrap_angle(-179.0, 179.0)
        self.assertLessEqual(abs(value - 179.0), 2.0 + ABS_TOL)

    # TEST-UNIT-036
    # Requirements: REQ-TRANS-003
    def test_in_range_candidate_has_priority(self):
        limits = make_limits(z=AxisRange(-30, 30), a=AxisRange(-180, 180))
        chosen = self.t._select_solution([(20.0, 0.0), (200.0, 0.0)], None, limits)
        self.assertEqual((20.0, 0.0), chosen)

    # TEST-UNIT-037
    # Requirements: REQ-TRANS-003
    def test_continuity_has_priority(self):
        chosen = self.t._select_solution([(10.0, 10.0), (10.0, 170.0)], (10.0, 5.0), self.limits)
        self.assertEqual((10.0, 10.0), chosen)

    # TEST-UNIT-038
    # Requirements: REQ-TRANS-003
    def test_smaller_total_motion_selected(self):
        chosen = self.t._select_solution([(20.0, 20.0), (30.0, 30.0)], (10.0, 10.0), self.limits)
        self.assertEqual((20.0, 20.0), chosen)

    # TEST-UNIT-039
    # Requirements: REQ-TRANS-003
    def test_smaller_absolute_roll_breaks_tie(self):
        chosen = self.t._select_solution([(20.0, 20.0), (20.0, -20.0)], None, self.limits)
        self.assertEqual(20.0, abs(chosen[1]))

    # TEST-UNIT-040
    # Requirements: REQ-TRANS-002, REQ-TRANS-003
    def test_equivalent_solution_candidates_are_generated(self):
        candidates = self.t._generate_equivalent_solutions(20.0, 30.0)
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIn((20.0, 30.0), candidates)

    def _assert_reproduces(self, aoa, aos, z, a):
        r = math.tan(math.radians(z))
        u = r * math.cos(math.radians(a))
        v = r * math.sin(math.radians(a))
        self.assertAlmostEqual(aoa, math.degrees(math.atan(u)), delta=ABS_TOL)
        self.assertAlmostEqual(aos, math.degrees(math.atan(v)), delta=ABS_TOL)


if __name__ == "__main__": unittest.main()
