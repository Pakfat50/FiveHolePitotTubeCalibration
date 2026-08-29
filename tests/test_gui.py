"""MainWindow のGUI制御単体テスト。

File: test_gui.py
日本語表示要素、非モーダル検証表示、警告/エラー状態、各操作イベントの依存呼出しを検証する。
Details:
    docs/test_specification.md の TEST-UNIT-100..110,121 に対応する。
"""

import unittest
from unittest.mock import Mock, patch

from gui import MainWindow
from repositories import SettingsLoadError
from tests.test_support import make_settings


class TestMainWindow(unittest.TestCase):
    """@brief build_ui=FalseでMainWindowのイベント制御と表示状態をGUI実体から分離して確認する。"""

    def setUp(self):
        """@brief MainWindowの全外部依存をMock化して制御ロジックだけを観測可能にする。"""
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
        """@brief 必須操作ボタンの日本語ラベル定義を確認する。

        Test:
            TEST-UNIT-100: シミュレーション、Gコード生成、設定保存、設定読込の4ラベルを持つこと。
        Verification rationale:
            MainWindowが公開するrequired_labels()を直接照合するため、UI構築前でも必須日本語操作名称の欠落を検出できる。
        See Also:
            REQ-GUI-001, REQ-GUI-004
        """
        labels = self.window.required_labels()
        for text in ("シミュレーション", "Gコード生成", "設定保存", "設定読込"):
            self.assertIn(text, labels)

    # TEST-UNIT-101
    # Requirements: REQ-VALID-001, REQ-GUI-005
    def test_validation_error_changes_target_background_and_shows_existing_message(self):
        """@brief 入力エラー時に該当Entryの背景だけを変え、既存メッセージ領域へ理由を表示することを確認する。

        Test:
            TEST-UNIT-101: feed_rateエラー時、feed_rateだけをエラーstyleとし、status_messageへ理由を表示し、モーダル表示しないこと。
        Details:
            エラー用背景色はレビュー承認済みの薄い赤 #FFECEC とする。エラーstyleはfieldbackgroundだけを設定し、枠設定や新規GUI要素を追加しない。
        Verification rationale:
            実Entry相当Mockへのstyle適用とstatus_messageを同時観測するため、対象欄の視覚強調と既存メッセージ領域への理由表示を確認できる。さらにStyle.configureの引数を確認することで、枠色等を上書きせず背景色だけを変更することを確認できる。
        See Also:
            REQ-VALID-001, REQ-GUI-005
        """
        feed_entry = Mock()
        hold_entry = Mock()
        self.window._entry_widgets = {
            "feed_rate": feed_entry,
            "hold_time_s": hold_entry,
        }

        issue = Mock(field="feed_rate", message="Feed rateが不正", severity=Mock(name="ERROR"))
        self.window._update_validation_display(Mock(issues=[issue]))

        self.assertEqual("#FFECEC", self.window.ENTRY_ERROR_BACKGROUND)
        feed_entry.configure.assert_called_with(style=self.window.ENTRY_ERROR_STYLE)
        hold_entry.configure.assert_called_with(style=self.window.ENTRY_NORMAL_STYLE)
        self.assertIn("feed_rate", self.window.field_errors)
        self.assertEqual("Feed rateが不正", self.window.status_message)
        self.assertFalse(self.window.modal_dialog_requested)

        style = Mock()
        with patch("gui.ttk.Style", return_value=style):
            self.window._configure_validation_styles()
        style.configure.assert_called_once_with(
            self.window.ENTRY_ERROR_STYLE,
            fieldbackground=self.window.ENTRY_ERROR_BACKGROUND,
        )

        # 数値へ変換できない入力も、汎用inputエラーではなく該当Entryを特定する。
        self.window._widget_vars = {
            "feed_rate": Mock(get=Mock(return_value="abc")),
            "hold_time_s": Mock(get=Mock(return_value="1.0")),
        }
        self.assertEqual({"feed_rate"}, self.window._find_numeric_parse_errors())
        self.window._on_gui_input_changed()
        self.assertIn("数値として解釈できない", self.window.status_message)
        self.assertFalse(self.window.modal_dialog_requested)

    # TEST-UNIT-102
    # Requirements: REQ-VALID-001, REQ-GUI-005
    def test_validation_error_background_and_message_clear_after_recovery(self):
        """@brief 入力不正解消後にEntry背景と既存メッセージ領域のエラー理由が自動解除されることを確認する。

        Test:
            TEST-UNIT-102: issue有り→issue無しの連続更新後、feed_rateへ通常styleが再適用され、入力エラー理由が消えること。
        Verification rationale:
            同一Entryへのstyle呼出し順とstatus_messageの遷移を観測するため、内部field_errorsだけ消えて背景色またはエラーメッセージが残留する不具合を検出できる。
        See Also:
            REQ-VALID-001, REQ-GUI-005
        """
        feed_entry = Mock()
        self.window._entry_widgets = {"feed_rate": feed_entry}
        issue = Mock(field="feed_rate", message="error", severity=Mock(name="ERROR"))

        self.window._update_validation_display(Mock(issues=[issue]))
        self.assertEqual("error", self.window.status_message)
        self.window._update_validation_display(Mock(issues=[]))

        self.assertEqual(
            [
                unittest.mock.call(style=self.window.ENTRY_ERROR_STYLE),
                unittest.mock.call(style=self.window.ENTRY_NORMAL_STYLE),
            ],
            feed_entry.configure.call_args_list,
        )
        self.assertNotIn("feed_rate", self.window.field_errors)
        self.assertEqual("入力値は有効です。", self.window.status_message)

    # TEST-UNIT-103
    # Requirements: REQ-LIMIT-002, REQ-GUI-005
    def test_xy_warning_shows_separate_deviations_without_resultant(self):
        """@brief X/Y飽和警告が各軸偏差を別々に表示し合成距離を表示しないことを確認する。

        Test:
            TEST-UNIT-103: status_messageにX=1.25,Y=2.5を含み「合成」を含まないこと。
        Verification rationale:
            異なるX/Y偏差値を与えて双方の数値と禁止語を同時確認するため、軸別表示と合成距離非表示を直接検証できる。
        See Also:
            REQ-LIMIT-002, REQ-GUI-005
        """
        plan = Mock(max_x_deviation=1.25, max_y_deviation=2.5, has_generation_error=False)
        self.window._update_plan_status(plan)
        text = self.window.status_message
        self.assertIn("X", text); self.assertIn("1.25", text); self.assertIn("Y", text); self.assertIn("2.5", text)
        self.assertNotIn("合成", text)

    # TEST-UNIT-104
    # Requirements: REQ-LIMIT-003, REQ-GUI-005
    def test_rotational_error_disables_actions(self):
        """@brief Controllerが生成不可を返す場合にSim/G-code操作が両方無効になることを確認する。

        Test:
            TEST-UNIT-104: can_generate=Falseでsimulation_enabled=Falseかつgcode_enabled=Falseとなること。
        Verification rationale:
            UI状態更新の唯一の入力条件をMockで固定し2操作の状態を直接観測するため、生成禁止エラー時の操作抑止を確認できる。
        See Also:
            REQ-LIMIT-003, REQ-GUI-005
        """
        self.controller.can_generate.return_value = False
        self.window._update_action_state()
        self.assertFalse(self.window.simulation_enabled)
        self.assertFalse(self.window.gcode_enabled)

    # TEST-UNIT-105
    # Requirements: REQ-GUI-005
    def test_valid_plan_enables_actions(self):
        """@brief 生成可能状態ではSim/G-code操作が両方有効になることを確認する。

        Test:
            TEST-UNIT-105: can_generate=Trueでsimulation_enabled/gcode_enabled=Trueとなること。
        Verification rationale:
            TEST-UNIT-104の反対条件を同じ公開状態で観測するため、有効化・無効化双方の状態更新を境界なく確認できる。
        See Also:
            REQ-GUI-005
        """
        self.controller.can_generate.return_value = True
        self.window._update_action_state()
        self.assertTrue(self.window.simulation_enabled)
        self.assertTrue(self.window.gcode_enabled)

    # TEST-UNIT-106
    # Requirements: REQ-INPUT-006
    def test_initialization_gcode_load_success(self):
        """@brief 初期化Gコード読込成功時に内容をMainWindowが保持することを確認する。

        Test:
            TEST-UNIT-106: Repository戻り値"G92 X0\n"がinitialization_textへ保存されること。
        Verification rationale:
            I/OをMock化して成功内容だけを固定し、Window内部保持値を比較するため、イベント処理による受渡しを直接検証できる。
        See Also:
            REQ-INPUT-006
        """
        self.init_repo.load.return_value = "G92 X0\n"
        self.window._on_load_initialization("init.txt")
        self.assertEqual("G92 X0\n", self.window.initialization_text)

    # TEST-UNIT-107
    # Requirements: REQ-GUI-003, REQ-GUI-004
    def test_save_settings_passes_current_settings_to_repository(self):
        """@brief 設定保存イベントがControllerの現在設定をRepositoryへ渡すことを確認する。

        Test:
            TEST-UNIT-107: _on_save_settings("settings.csv")でsave(path,current_settings)を1回呼ぶこと。
        Verification rationale:
            Controller戻り値とRepository呼出し引数を同一オブジェクトで照合するため、保存対象設定の取り違えを検出できる。
        See Also:
            REQ-GUI-003, REQ-GUI-004
        """
        settings = make_settings(); self.controller.get_current_settings.return_value = settings
        self.window._on_save_settings("settings.csv")
        self.settings_repo.save.assert_called_once_with("settings.csv", settings)

    # TEST-UNIT-108
    # Requirements: REQ-GUI-003, REQ-GUI-004
    def test_load_settings_applies_and_revalidates(self):
        """@brief 設定読込成功時に読み込んだ設定をControllerへ適用することを確認する。

        Test:
            TEST-UNIT-108: Repositoryのloaded settingsをapply_settingsへ1回渡すこと。
        Verification rationale:
            読込値とController呼出し引数を同一オブジェクトで確認するため、GUI側での部分変換や誤適用を検出できる。
        See Also:
            REQ-GUI-003, REQ-GUI-004
        """
        settings = make_settings(); self.settings_repo.load.return_value = settings
        self.window._on_load_settings("settings.csv")
        self.controller.apply_settings.assert_called_once_with(settings)

    # TEST-UNIT-109
    # Requirements: REQ-SIM-001, REQ-GUI-004
    def test_simulation_uses_current_plan(self):
        """@brief シミュレーションイベントがControllerのcurrent planを10秒指定で使用することを確認する。

        Test:
            TEST-UNIT-109: SimulationController.start(plan,duration_s=10.0)を1回呼ぶこと。
        Verification rationale:
            Controllerから得たplanとSimControllerへの引数同一性を確認するため、別計算結果を使用せず同一planを渡す設計を確認できる。
        See Also:
            REQ-SIM-001, REQ-GUI-004
        """
        plan = Mock(); self.controller.get_current_plan.return_value = plan
        self._prepare_generation_state(True)
        self.window._on_simulate()
        self.sim_controller.start.assert_called_once_with(plan, duration_s=10.0)

    # TEST-UNIT-110
    # Requirements: REQ-GCODE-001, REQ-GUI-004
    def test_generate_gcode_sequence(self):
        """@brief Gコード生成イベントがcurrent plan/settingsから生成しRepositoryへ保存することを確認する。

        Test:
            TEST-UNIT-110: Generatorへplan/settings/initを渡し、生成文字列を指定pathへsaveすること。
        Verification rationale:
            GeneratorとRepositoryの両Mock呼出しを確認するため、GUIイベントのデータフローと保存先受渡しを直接検証できる。
        See Also:
            REQ-GCODE-001, REQ-GUI-004
        """
        plan = Mock(); settings = make_settings()
        self.controller.get_current_plan.return_value = plan
        self.controller.get_current_settings.return_value = settings
        self._prepare_generation_state(True)
        self.gcode_generator.generate.return_value = "G21\n"
        self.window.initialization_text = ""
        self.window._on_generate_gcode("out.nc")
        self.gcode_generator.generate.assert_called_once_with(plan, settings, "")
        self.gcode_repo.save.assert_called_once_with("out.nc", "G21\n")

    # TEST-UNIT-121
    # Requirements: REQ-GUI-003, REQ-GUI-005
    def test_failed_csv_load_keeps_existing_state_and_notifies_user(self):
        """@brief 設定CSV読込失敗時に既存状態を変更せず非モーダル通知することを確認する。

        Test:
            TEST-UNIT-121: SettingsLoadError時にapply_settingsを呼ばず、理由をstatus_messageへ表示し、モーダル要求しないこと。
        Details:
            既存settings/planを保持した状態でRepositoryだけを失敗させる。
        Verification rationale:
            適用API未呼出し、エラー理由表示、非モーダル状態を同時確認するため、部分適用禁止とユーザー通知を一連の失敗経路として検証できる。
        See Also:
            REQ-GUI-003, REQ-GUI-005
        """
        old_settings = make_settings(feed_rate=55.0); old_plan = Mock()
        self.controller.get_current_settings.return_value = old_settings
        self.controller.get_current_plan.return_value = old_plan
        self.settings_repo.load.side_effect = SettingsLoadError("feed_rateがありません")
        self.window._on_load_settings("bad.csv")
        self.controller.apply_settings.assert_not_called()
        self.assertIn("feed_rate", self.window.status_message)
        self.assertFalse(self.window.modal_dialog_requested)

    def _prepare_generation_state(self, can_generate: bool) -> None:
        """@brief 操作イベントテスト用にControllerの生成可否を固定する。"""
        self.controller.can_generate.return_value = can_generate


if __name__ == "__main__":
    unittest.main()
