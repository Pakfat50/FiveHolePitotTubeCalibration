import math
import unittest

from validation import InputValidator
from tests.test_support import make_limits, make_settings
from models import AxisRange


class TestInputValidator(unittest.TestCase):
    def setUp(self):
        self.validator = InputValidator()

    # TEST-UNIT-001
    # Requirements: REQ-VALID-001, REQ-VALID-002
    def test_valid_settings(self):
        result = self.validator.validate(make_settings())
        self.assertTrue(result.is_valid)
        self.assertFalse(any(i.severity.name == "ERROR" for i in result.issues))

    # TEST-UNIT-002
    # Requirements: REQ-INPUT-001, REQ-VALID-002
    def test_aoa_min_equal_max(self):
        self.assertFalse(self.validator.validate(make_settings(aoa_min=10, aoa_max=10)).is_valid)

    # TEST-UNIT-003
    # Requirements: REQ-INPUT-001, REQ-VALID-002
    def test_aoa_min_greater_than_max(self):
        self.assertFalse(self.validator.validate(make_settings(aoa_min=11, aoa_max=10)).is_valid)

    # TEST-UNIT-004
    # Requirements: REQ-INPUT-001, REQ-VALID-002
    def test_aos_min_equal_max(self):
        self.assertFalse(self.validator.validate(make_settings(aos_min=10, aos_max=10)).is_valid)

    # TEST-UNIT-005
    # Requirements: REQ-INPUT-001, REQ-VALID-002
    def test_aos_min_greater_than_max(self):
        self.assertFalse(self.validator.validate(make_settings(aos_min=11, aos_max=10)).is_valid)

    # TEST-UNIT-006
    # Requirements: REQ-INPUT-002, REQ-VALID-002
    def test_aoa_points_minimum_valid(self):
        self.assertTrue(self.validator.validate(make_settings(aoa_points=2)).is_valid)

    # TEST-UNIT-007
    # Requirements: REQ-INPUT-002, REQ-VALID-002
    def test_aoa_points_too_small(self):
        self.assertFalse(self.validator.validate(make_settings(aoa_points=1)).is_valid)

    # TEST-UNIT-008
    # Requirements: REQ-INPUT-002, REQ-VALID-002
    def test_aos_points_too_small(self):
        self.assertFalse(self.validator.validate(make_settings(aos_points=1)).is_valid)

    # TEST-UNIT-009
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_feed_rate_invalid(self):
        for value in (0.0, -1.0, math.nan, math.inf):
            with self.subTest(value=value):
                self.assertFalse(self.validator.validate(make_settings(feed_rate=value)).is_valid)

    # TEST-UNIT-010
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_hold_time_invalid(self):
        for value in (0.0, 0.099, -1.0, math.nan, math.inf):
            with self.subTest(value=value):
                self.assertFalse(self.validator.validate(make_settings(hold_time_s=value)).is_valid)

    # TEST-UNIT-011
    # Requirements: REQ-INPUT-003, REQ-VALID-002
    def test_distance_non_finite(self):
        for field in ("tip_offset_x", "tip_offset_y"):
            for value in (math.nan, math.inf):
                with self.subTest(field=field, value=value):
                    self.assertFalse(self.validator.validate(make_settings(**{field: value})).is_valid)

    # TEST-UNIT-012
    # Requirements: REQ-INPUT-005, REQ-VALID-002
    def test_x_range_equal(self):
        limits = make_limits(x=AxisRange(1.0, 1.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    # TEST-UNIT-013
    # Requirements: REQ-INPUT-005, REQ-VALID-002
    def test_y_range_reversed(self):
        limits = make_limits(y=AxisRange(2.0, 1.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    # TEST-UNIT-014
    # Requirements: REQ-INPUT-005, REQ-VALID-002
    def test_z_range_invalid(self):
        limits = make_limits(z=AxisRange(2.0, 2.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    # TEST-UNIT-015
    # Requirements: REQ-INPUT-005, REQ-VALID-002
    def test_a_range_invalid(self):
        limits = make_limits(a=AxisRange(3.0, 2.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    # TEST-UNIT-016
    # Requirements: REQ-VALID-001
    def test_multiple_errors_are_reported(self):
        result = self.validator.validate(make_settings(aoa_min=10, aoa_max=10, aoa_points=1, feed_rate=0))
        self.assertGreaterEqual(sum(i.severity.name == "ERROR" for i in result.issues), 3)

    # TEST-UNIT-111
    # Requirements: REQ-INPUT-003, REQ-VALID-002
    def test_lx_zero_is_invalid(self):
        self.assertFalse(self.validator.validate(make_settings(tip_offset_x=0.0)).is_valid)

    # TEST-UNIT-112
    # Requirements: REQ-INPUT-003, REQ-VALID-002
    def test_ly_negative_is_invalid(self):
        self.assertFalse(self.validator.validate(make_settings(tip_offset_y=-0.1)).is_valid)

    # TEST-UNIT-113
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_hold_time_minimum_is_valid(self):
        self.assertTrue(self.validator.validate(make_settings(hold_time_s=0.1)).is_valid)

    # TEST-UNIT-114
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_hold_time_below_minimum_is_invalid(self):
        self.assertFalse(self.validator.validate(make_settings(hold_time_s=0.099999)).is_valid)

    # TEST-UNIT-115
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_feed_rate_minimum_is_valid(self):
        self.assertTrue(self.validator.validate(make_settings(feed_rate=1.0)).is_valid)

    # TEST-UNIT-116
    # Requirements: REQ-INPUT-004, REQ-VALID-002
    def test_feed_rate_below_minimum_is_invalid(self):
        self.assertFalse(self.validator.validate(make_settings(feed_rate=0.999999)).is_valid)


if __name__ == "__main__":
    unittest.main()
