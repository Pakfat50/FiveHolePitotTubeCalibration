import unittest
from unittest.mock import Mock

from controller import CalibrationController
from tests.test_support import make_settings


class TestCalibrationController(unittest.TestCase):
    def setUp(self):
        self.validator = Mock()
        self.service = Mock()
        self.controller = CalibrationController(self.validator, self.service)

    # TEST-UNIT-084
    # Requirements: REQ-VALID-001, REQ-SCAN-001
    def test_valid_input_rebuilds_plan(self):
        valid = Mock(is_valid=True, issues=[])
        plan = Mock(has_generation_error=False)
        self.validator.validate.return_value = valid
        self.service.build_plan.return_value = plan
        settings = make_settings()
        self.controller.on_settings_changed(settings)
        self.validator.validate.assert_called_once_with(settings)
        self.service.build_plan.assert_called_once_with(settings)
        self.assertIs(plan, self.controller.get_current_plan())

    # TEST-UNIT-085
    # Requirements: REQ-VALID-001, REQ-VALID-002
    def test_invalid_input_does_not_rebuild_plan(self):
        self.validator.validate.return_value = Mock(is_valid=False, issues=[Mock()])
        self.controller.on_settings_changed(make_settings())
        self.service.build_plan.assert_not_called()
        self.assertFalse(self.controller.can_generate())

    # TEST-UNIT-086
    # Requirements: REQ-VALID-001
    def test_invalid_then_valid_recovers(self):
        self.validator.validate.side_effect = [Mock(is_valid=False, issues=[Mock()]), Mock(is_valid=True, issues=[])]
        self.service.build_plan.return_value = Mock(has_generation_error=False)
        settings = make_settings()
        self.controller.on_settings_changed(settings)
        self.assertFalse(self.controller.can_generate())
        self.controller.on_settings_changed(settings)
        self.assertTrue(self.controller.can_generate())

    # TEST-UNIT-087
    # Requirements: REQ-VALID-003, REQ-LIMIT-001
    def test_xy_warning_plan_can_generate(self):
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=False, max_x_deviation=1.0, max_y_deviation=2.0)
        self.controller.on_settings_changed(make_settings())
        self.assertTrue(self.controller.can_generate())

    # TEST-UNIT-088
    # Requirements: REQ-VALID-003, REQ-LIMIT-003
    def test_rotational_error_plan_cannot_generate(self):
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=True)
        self.controller.on_settings_changed(make_settings())
        self.assertFalse(self.controller.can_generate())

    # TEST-UNIT-089
    # Requirements: REQ-GUI-003
    def test_apply_settings_updates_and_revalidates(self):
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=False)
        settings = make_settings(feed_rate=123.0)
        self.controller.apply_settings(settings)
        self.assertEqual(settings, self.controller.get_current_settings())
        self.validator.validate.assert_called_once_with(settings)
        self.service.build_plan.assert_called_once_with(settings)


if __name__ == "__main__": unittest.main()
