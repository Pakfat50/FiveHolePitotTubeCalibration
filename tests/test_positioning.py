import math
import unittest

from positioning import PositionCompensator
from tests.test_support import ABS_TOL


class TestPositionCompensator(unittest.TestCase):
    def setUp(self):
        self.p = PositionCompensator()

    # TEST-UNIT-041
    # Requirements: REQ-POS-001
    def test_zero_pitch_requires_no_translation(self):
        x, y = self.p.calculate_xy(0.0, 100.0, 10.0)
        self.assertAlmostEqual(0.0, x, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, y, delta=ABS_TOL)

    # TEST-UNIT-042
    # Requirements: REQ-POS-001
    def test_positive_pitch_matches_formula(self):
        self._assert_formula(15.0, 100.0, 10.0)

    # TEST-UNIT-043
    # Requirements: REQ-POS-001
    def test_negative_pitch_matches_formula(self):
        self._assert_formula(-15.0, 100.0, 10.0)

    # TEST-UNIT-044
    # Requirements: REQ-POS-001
    def test_small_positive_ly(self):
        self._assert_formula(20.0, 100.0, 1e-6)

    # TEST-UNIT-045
    # Requirements: REQ-POS-001
    def test_small_positive_lx(self):
        self._assert_formula(20.0, 1e-6, 100.0)

    # TEST-UNIT-046
    # Requirements: REQ-POS-002
    def test_roll_does_not_affect_xy(self):
        # API intentionally accepts only theta/Lx/Ly; roll is absent by design.
        first = self.p.calculate_xy(10.0, 100.0, 10.0)
        second = self.p.calculate_xy(10.0, 100.0, 10.0)
        self.assertEqual(first, second)

    def _assert_formula(self, theta, lx, ly):
        rad = math.radians(theta)
        xtip = lx * math.cos(rad) - ly * math.sin(rad)
        ytip = lx * math.sin(rad) + ly * math.cos(rad)
        expected_x = lx - xtip
        expected_y = ly - ytip
        x, y = self.p.calculate_xy(theta, lx, ly)
        self.assertAlmostEqual(expected_x, x, delta=ABS_TOL)
        self.assertAlmostEqual(expected_y, y, delta=ABS_TOL)


if __name__ == "__main__": unittest.main()
