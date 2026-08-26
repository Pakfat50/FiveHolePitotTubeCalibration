"""較正アプリケーションのTkinter Presentation層。"""

import tkinter as tk
from tkinter import ttk

from repositories import SettingsLoadError


class MainWindow:
    """日本語GUIとユーザー操作を統括するメインウィンドウ。

    本クラスは表示状態のみを保持し、数値計算はCore/Application層へ委譲する。
    ファイル読込失敗は非モーダルに通知する。

    対応要求:
        REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004, REQ-GUI-005
    """

    def __init__(self, root, controller, settings_repository, initialization_repository, gcode_generator, gcode_repository, map_view, simulation_controller, build_ui: bool = True) -> None:
        self.root = root
        self.controller = controller
        self.settings_repository = settings_repository
        self.initialization_repository = initialization_repository
        self.gcode_generator = gcode_generator
        self.gcode_repository = gcode_repository
        self.map_view = map_view
        self.simulation_controller = simulation_controller
        self.initialization_text = ""
        self.field_errors: dict[str, str] = {}
        self.status_message = ""
        self.modal_dialog_requested = False
        self.simulation_enabled = False
        self.gcode_enabled = False
        self._input_provider = None
        if build_ui:
            self._build_widgets()

    def run(self) -> None:
        """Tkイベントループを開始する。"""
        self.root.mainloop()

    # 対応要求: REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004, REQ-INPUT-005, REQ-INPUT-007, REQ-GUI-001, REQ-GUI-004
    def _build_widgets(self) -> None:
        """日本語入力欄、状態表示領域、操作ボタンを構築する。"""
        # 数値計算はGUIへ持ち込まず、Presentation層では操作部品と状態表示だけを構築する。
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        self.status_label = ttk.Label(self.main_frame, text=self.status_message)
        self.status_label.pack()
        self.simulation_button = ttk.Button(self.main_frame, text="シミュレーション", command=self._on_simulate)
        self.simulation_button.pack()
        self.gcode_button = ttk.Button(self.main_frame, text="Gコード生成")
        self.gcode_button.pack()
        self.save_settings_button = ttk.Button(self.main_frame, text="設定保存")
        self.save_settings_button.pack()
        self.load_settings_button = ttk.Button(self.main_frame, text="設定読込")
        self.load_settings_button.pack()
        self._update_action_state()

    def required_labels(self) -> tuple[str, ...]:
        """GUIで必須となる操作ラベルを返す。"""
        return ("シミュレーション", "Gコード生成", "設定保存", "設定読込")

    def _collect_raw_input(self):
        """コントローラで検証するため、現在のGUI入力内容を収集する。"""
        # 実UIの入力変換処理とテスト時の入力供給を分離するため、入力providerを利用できる構造とする。
        if self._input_provider is not None:
            return self._input_provider()
        return self.controller.get_current_settings()

    # 対応要求: REQ-VALID-001
    def _on_input_changed(self) -> None:
        """入力変更を伝搬し、検証表示、較正計画、操作可否を更新する。"""
        raw_input = self._collect_raw_input()
        validation = self.controller.on_settings_changed(raw_input)
        self._update_validation_display(validation)

        # 無効入力時はControllerがPlanを無効化するため、存在する場合のみMapを更新する。
        plan = self.controller.get_current_plan()
        if plan is not None:
            self.map_view.render(plan)
            self._update_plan_status(plan)
        self._update_action_state()

    # 対応要求: REQ-VALID-001, REQ-LIMIT-002, REQ-GUI-005
    def _update_validation_display(self, validation_result) -> None:
        """非モーダルなフィールド強調表示とエラーメッセージを更新する。"""
        # 毎回全フィールド状態を作り直すことで、入力回復時に古いエラー表示を残さない。
        self.field_errors = {issue.field: issue.message for issue in validation_result.issues}
        if self.field_errors:
            self.status_message = " / ".join(self.field_errors.values())
        elif not self.status_message.startswith("X逸脱"):
            self.status_message = ""
        self.modal_dialog_requested = False
        self._refresh_status_widget()

    # 対応要求: REQ-LIMIT-002, REQ-LIMIT-003, REQ-GUI-005
    def _update_plan_status(self, plan) -> None:
        """X/Y逸脱警告またはZ/A生成禁止状態を表示する。"""
        messages = []
        if plan.max_x_deviation > 0 or plan.max_y_deviation > 0:
            # X/Yは合成値にせず、仕様どおり軸ごとの最大逸脱量を独立表示する。
            messages.append(f"X逸脱: {plan.max_x_deviation}, Y逸脱: {plan.max_y_deviation}")
        if plan.has_generation_error:
            messages.append("Z/A可動範囲外のため生成できません。")
        self.status_message = " / ".join(messages)
        self.modal_dialog_requested = False
        self._refresh_status_widget()

    # 対応要求: REQ-VALID-003, REQ-GUI-005
    def _update_action_state(self) -> None:
        """シミュレーションおよびGコード生成操作の有効／無効を更新する。"""
        allowed = bool(self.controller.can_generate())
        self.simulation_enabled = allowed
        self.gcode_enabled = allowed
        state = "normal" if allowed else "disabled"
        if hasattr(self, "simulation_button"):
            self.simulation_button.configure(state=state)
        if hasattr(self, "gcode_button"):
            self.gcode_button.configure(state=state)

    # 対応要求: REQ-INPUT-006, REQ-GUI-005
    def _on_load_initialization(self, path: str | None = None) -> None:
        """初期化Gコードを読み込み、失敗時は現在状態を維持する。"""
        if path is None:
            return
        try:
            text = self.initialization_repository.load(path)
        except (OSError, UnicodeError) as exc:
            self.status_message = f"初期化Gコードを読み込めません: {exc}"
            self.modal_dialog_requested = False
            self._refresh_status_widget()
            return
        self.initialization_text = text

    # 対応要求: REQ-GUI-003, REQ-GUI-004
    def _on_save_settings(self, path: str | None = None) -> None:
        """現在の設定をCSVへ保存する。"""
        if path is None:
            return
        settings = self.controller.get_current_settings()
        if settings is None:
            return
        try:
            self.settings_repository.save(path, settings)
        except OSError as exc:
            self.status_message = f"設定を保存できません: {exc}"
            self.modal_dialog_requested = False
            self._refresh_status_widget()

    # 対応要求: REQ-GUI-003, REQ-GUI-004, REQ-GUI-005
    def _on_load_settings(self, path: str | None = None) -> None:
        """CSV設定を一括で読み込み、失敗時は現在状態を維持する。"""
        if path is None:
            return
        try:
            # Repositoryが全項目を検証し終えるまでControllerへ適用しないため、部分適用を防止できる。
            settings = self.settings_repository.load(path)
        except SettingsLoadError as exc:
            self.status_message = str(exc)
            self.modal_dialog_requested = False
            self._refresh_status_widget()
            return
        validation = self.controller.apply_settings(settings)
        if validation is not None:
            self._update_validation_display(validation)
        plan = self.controller.get_current_plan()
        if plan is not None:
            self.map_view.render(plan)
            self._update_plan_status(plan)
        self._update_action_state()

    # 対応要求: REQ-SIM-001, REQ-GUI-004
    def _on_simulate(self) -> None:
        """現在の較正計画を使用して約10秒のシミュレーションを開始する。"""
        plan = self.controller.get_current_plan()
        if plan is None or not self.controller.can_generate():
            return
        self.simulation_controller.start(plan, duration_s=10.0)

    # 対応要求: REQ-GCODE-001, REQ-GUI-004
    def _on_generate_gcode(self, path: str | None = None) -> None:
        """現在の共有較正計画から`.nc`文字列を生成し保存する。"""
        if path is None:
            return
        plan = self.controller.get_current_plan()
        settings = self.controller.get_current_settings()
        if plan is None or settings is None:
            return
        text = self.gcode_generator.generate(plan, settings, self.initialization_text)
        try:
            self.gcode_repository.save(path, text)
        except OSError as exc:
            self.status_message = f"Gコードを保存できません: {exc}"
            self.modal_dialog_requested = False
            self._refresh_status_widget()

    def _refresh_status_widget(self) -> None:
        """ヘッドレステストでは何もせず、実GUIがある場合だけ状態ラベルを更新する。"""
        if hasattr(self, "status_label"):
            self.status_label.configure(text=self.status_message)
