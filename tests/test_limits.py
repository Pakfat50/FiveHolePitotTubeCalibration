import unittest

from limits import LimitEvaluator
from models import AxisCommand
from tests.test_support import ABS_TOL, make_limits


class TestLimitEvaluator(unittest.TestCase):
    def setUp(self):
        self.e = LimitEvaluator()
        self.limits = make_limits()

    def _eval(self, **kwargs):
        values = {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0}
        values.update(kwargs)
        return self.e.evaluate(AxisCommand(**values), self.limits)

    # TEST-UNIT-047
    # Requirements: REQ-LIMIT-001, REQ-VALID-003
    def test_all_axes_in_range(self):
        r = self._eval()
        self.assertFalse(r.x_saturated or r.y_saturated or r.rotational_error)

    # TEST-UNIT-048
    # Requirements: REQ-LIMIT-001
    def test_x_above_max_saturates(self):
        r = self._eval(x=1200.0)
        self.assertEqual(1000.0, r.command.x); self.assertTrue(r.x_saturated)

    # TEST-UNIT-049
    # Requirements: REQ-LIMIT-001
    def test_x_below_min_saturates(self):
        self.assertEqual(-1000.0, self._eval(x=-1200.0).command.x)

    # TEST-UNIT-050
    # Requirements: REQ-LIMIT-001
    def test_y_above_max_saturates(self):
        self.assertEqual(1000.0, self._eval(y=1200.0).command.y)

    # TEST-UNIT-051
    # Requirements: REQ-LIMIT-001
    def test_y_below_min_saturates(self):
        self.assertEqual(-1000.0, self._eval(y=-1200.0).command.y)

    # TEST-UNIT-052
    # Requirements: REQ-LIMIT-002
    def test_x_deviation(self):
        self.assertAlmostEqual(200.0, self._eval(x=1200.0).x_deviation, delta=ABS_TOL)

    # TEST-UNIT-053
    # Requirements: REQ-LIMIT-002
    def test_y_deviation(self):
        self.assertAlmostEqual(200.0, self._eval(y=-1200.0).y_deviation, delta=ABS_TOL)

    # TEST-UNIT-054
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_z_above_max_not_clamped(self):
        r = self._eval(z=200.0)
        self.assertEqual(200.0, r.command.z); self.assertTrue(r.rotational_error)

    # TEST-UNIT-055
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_z_below_min_not_clamped(self):
        r = self._eval(z=-200.0)
        self.assertEqual(-200.0, r.command.z); self.assertTrue(r.rotational_error)

    # TEST-UNIT-056
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_a_above_max_not_clamped(self):
        r = self._eval(a=800.0)
        self.assertEqual(800.0, r.command.a); self.assertTrue(r.rotational_error)

    # TEST-UNIT-057
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_a_below_min_not_clamped(self):
        r = self._eval(a=-800.0)
        self.assertEqual(-800.0, r.command.a); self.assertTrue(r.rotational_error)

    # TEST-UNIT-058
    # Requirements: REQ-LIMIT-001, REQ-LIMIT-003
    def test_xy_only_overrange_is_not_generation_error(self):
        r = self._eval(x=1200, y=-1200)
        self.assertTrue(r.x_saturated and r.y_saturated); self.assertFalse(r.rotational_error)

    # TEST-UNIT-059
    # Requirements: REQ-LIMIT-003
    def test_translation_and_rotation_overrange_combined(self):
        r = self._eval(x=1200, z=200)
        self.assertEqual(1000.0, r.command.x); self.assertEqual(200.0, r.command.z); self.assertTrue(r.rotational_error)


if __name__ == "__main__": unittest.main()
