import unittest
from unittest.mock import Mock

from gui import MainWindow
from repositories import SettingsLoadError
from tests.test_support import make_settings


class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.controller = Mock()
        self.settings_repo = Mock()
        self.init_repo = Mock()
        self.gcode_generator = Mock()
        self.gcode_repo = Mock()
        self.map_view = Mock()
        self.sim_controller = Mock()
        self.window = MainWindow(
            root=Mock(),
            controller=self.controller,
            settings_repository=self.settings_repo,
            initialization_repository=self.init_repo,
            gcode_generator=self.gcode_generator,
            gcode_repository=self.gcode_repo,
            map_view=self.map_view,
            simulation_controller=self.sim_controller,
            build_ui=False,
        )

    # TEST-UNIT-100
    # Requirements: REQ-GUI-001, REQ-GUI-004
    def test_required_japanese_labels_and_buttons_are_defined(self):
        labels = self.window.required_labels()
        for text in ("シミュレーション", "Gコード生成", "設定保存", "設定読込"):
            self.assertIn(text, labels)

    # TEST-UNIT-101
    # Requirements: REQ-VALID-001, REQ-GUI-005
    def test_validation_error_is_non_modal_and_field_specific(self):
        issue = Mock(field="feed_rate", message="Feed rateが不正", severity=Mock(name="ERROR"))
        self.window._update_validation_display(Mock(issues=[issue]))
        self.assertIn("feed_rate", self.window.field_errors)
        self.assertFalse(self.window.modal_dialog_requested)

    # TEST-UNIT-102
    # Requirements: REQ-VALID-001, REQ-GUI-005
    def test_validation_error_clears_after_recovery(self):
        issue = Mock(field="feed_rate", message="error", severity=Mock(name="ERROR"))
        self.window._update_validation_display(Mock(issues=[issue]))
        self.window._update_validation_display(Mock(issues=[]))
        self.assertNotIn("feed_rate", self.window.field_errors)

    # TEST-UNIT-103
    # Requirements: REQ-LIMIT-002, REQ-GUI-005
    def test_xy_warning_shows_separate_deviations_without_resultant(self):
        plan = Mock(max_x_deviation=1.25, max_y_deviation=2.5, has_generation_error=False)
        self.window._update_plan_status(plan)
        text = self.window.status_message
        self.assertIn("X", text); self.assertIn("1.25", text); self.assertIn("Y", text); self.assertIn("2.5", text)
        self.assertNotIn("合成", text)

    # TEST-UNIT-104
    # Requirements: REQ-LIMIT-003, REQ-GUI-005
    def test_rotational_error_disables_actions(self):
        self.controller.can_generate.return_value = False
        self.window._update_action_state()
        self.assertFalse(self.window.simulation_enabled)
        self.assertFalse(self.window.gcode_enabled)

    # TEST-UNIT-105
    # Requirements: REQ-GUI-005
    def test_valid_plan_enables_actions(self):
        self.controller.can_generate.return_value = True
        self.window._update_action_state()
        self.assertTrue(self.window.simulation_enabled)
        self.assertTrue(self.window.gcode_enabled)

    # TEST-UNIT-106
    # Requirements: REQ-INPUT-006
    def test_initialization_gcode_load_success(self):
        self.init_repo.load.return_value = "G92 X0\n"
        self.window._on_load_initialization("init.txt")
        self.assertEqual("G92 X0\n", self.window.initialization_text)

    # TEST-UNIT-107
    # Requirements: REQ-GUI-003, REQ-GUI-004
    def test_save_settings_passes_current_settings_to_repository(self):
        settings = make_settings(); self.controller.get_current_settings.return_value = settings
        self.window._on_save_settings("settings.csv")
        self.settings_repo.save.assert_called_once_with("settings.csv", settings)

    # TEST-UNIT-108
    # Requirements: REQ-GUI-003, REQ-GUI-004
    def test_load_settings_applies_and_revalidates(self):
        settings = make_settings(); self.settings_repo.load.return_value = settings
        self.window._on_load_settings("settings.csv")
        self.controller.apply_settings.assert_called_once_with(settings)

    # TEST-UNIT-109
    # Requirements: REQ-SIM-001, REQ-GUI-004
    def test_simulation_uses_current_plan(self):
        plan = Mock(); self.controller.get_current_plan.return_value = plan
        self.window._on_simulate()
        self.sim_controller.start.assert_called_once_with(plan, duration_s=10.0)

    # TEST-UNIT-110
    # Requirements: REQ-GCODE-001, REQ-GUI-004
    def test_generate_gcode_sequence(self):
        plan = Mock(); settings = make_settings()
        self.controller.get_current_plan.return_value = plan
        self.controller.get_current_settings.return_value = settings
        self.gcode_generator.generate.return_value = "G21\n"
        self.window.initialization_text = ""
        self.window._on_generate_gcode("out.nc")
        self.gcode_generator.generate.assert_called_once_with(plan, settings, "")
        self.gcode_repo.save.assert_called_once_with("out.nc", "G21\n")

    # TEST-UNIT-121
    # Requirements: REQ-GUI-003, REQ-GUI-005
    def test_failed_csv_load_keeps_existing_state_and_notifies_user(self):
        old_settings = make_settings(feed_rate=55.0); old_plan = Mock()
        self.controller.get_current_settings.return_value = old_settings
        self.controller.get_current_plan.return_value = old_plan
        self.settings_repo.load.side_effect = SettingsLoadError("feed_rateがありません")
        self.window._on_load_settings("bad.csv")
        self.controller.apply_settings.assert_not_called()
        self.assertIn("feed_rate", self.window.status_message)
        self.assertFalse(self.window.modal_dialog_requested)


if __name__ == "__main__": unittest.main()
