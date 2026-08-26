"""較正アプリケーションのTkinter Presentation層。"""

import tkinter as tk
from tkinter import filedialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models import AxisLimits, AxisRange, CalibrationPlan, CalibrationSettings, ValidationResult
from repositories import SettingsLoadError


class MainWindow:
    """日本語GUIとユーザー操作を統括するメインウィンドウ。

    本クラスは入力UI、較正点マップ、非モーダル状態表示、ファイル操作を提供し、
    数値計算はCore/Application層へ委譲する。

    対応要求:
        REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004,
        REQ-INPUT-005, REQ-INPUT-006, REQ-INPUT-007, REQ-VALID-001,
        REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004, REQ-GUI-005
    """

    DEFAULT_VALUES = {
        "aoa_min": "-10.0",
        "aoa_max": "10.0",
        "aos_min": "-10.0",
        "aos_max": "10.0",
        "aoa_points": "5",
        "aos_points": "5",
        "tip_offset_x": "100.0",
        "tip_offset_y": "10.0",
        "hold_time_s": "1.0",
        "feed_rate": "100.0",
        "x_min": "-1000.0",
        "x_max": "1000.0",
        "y_min": "-1000.0",
        "y_max": "1000.0",
        "z_min": "-180.0",
        "z_max": "180.0",
        "a_min": "-720.0",
        "a_max": "720.0",
    }

    def __init__(self, root, controller, settings_repository, initialization_repository,
                 gcode_generator, gcode_repository, map_view, simulation_controller,
                 build_ui: bool = True) -> None:
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
        self.status_message = "入力値を設定してください。"
        self.modal_dialog_requested = False
        self.simulation_enabled = False
        self.gcode_enabled = False
        self._input_provider = None
        self._widget_vars: dict[str, tk.StringVar] = {}
        self._entry_widgets: dict[str, ttk.Entry] = {}
        self._updating_widgets = False
        self.map_canvas = None
        if build_ui:
            self._build_widgets()
            self._on_gui_input_changed()

    def run(self) -> None:
        """Tkイベントループを開始する。"""
        self.root.mainloop()

    # 対応要求: REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004, REQ-INPUT-005, REQ-INPUT-006, REQ-INPUT-007, REQ-GUI-001, REQ-GUI-002, REQ-GUI-004
    def _build_widgets(self) -> None:
        """日本語入力欄、較正点マップ、状態表示領域、操作ボタンを構築する。"""
        self.root.title("5孔ピトー管 較正Gコード生成")
        self.root.geometry("1180x780")
        self.root.minsize(960, 680)

        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        title = ttk.Label(self.main_frame, text="5孔ピトー管 較正Gコード生成", font=("TkDefaultFont", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self._build_input_panel(self.main_frame)
        self._build_map_panel(self.main_frame)
        self._build_status_and_actions(self.main_frame)
        self._update_action_state()

    def _build_input_panel(self, parent) -> None:
        """左側の較正条件、装置条件、可動範囲、オプションを構築する。"""
        outer = ttk.Frame(parent)
        outer.grid(row=1, column=0, sticky="nsw", padx=(0, 10))

        calibration = ttk.LabelFrame(outer, text="較正条件", padding=8)
        calibration.pack(fill="x", pady=(0, 8))
        self._add_range_row(calibration, 0, "AoA [deg]", "aoa_min", "aoa_max")
        self._add_value_row(calibration, 1, "AoA 点数", "aoa_points")
        self._add_range_row(calibration, 2, "AoS [deg]", "aos_min", "aos_max")
        self._add_value_row(calibration, 3, "AoS 点数", "aos_points")

        geometry = ttk.LabelFrame(outer, text="装置寸法", padding=8)
        geometry.pack(fill="x", pady=(0, 8))
        self._add_value_row(geometry, 0, "Lx [mm]", "tip_offset_x")
        self._add_value_row(geometry, 1, "Ly [mm]", "tip_offset_y")

        motion = ttk.LabelFrame(outer, text="移動条件", padding=8)
        motion.pack(fill="x", pady=(0, 8))
        self._add_value_row(motion, 0, "較正点保持時間 [s]", "hold_time_s")
        self._add_value_row(motion, 1, "Feed rate F [unit/min]", "feed_rate")

        limits = ttk.LabelFrame(outer, text="実軸可動範囲", padding=8)
        limits.pack(fill="x", pady=(0, 8))
        for row, axis in enumerate(("x", "y", "z", "a")):
            unit = "mm" if axis in ("x", "y") else "deg"
            self._add_range_row(limits, row, f"{axis.upper()} [{unit}]", f"{axis}_min", f"{axis}_max")

        options = ttk.LabelFrame(outer, text="オプション", padding=8)
        options.pack(fill="x", pady=(0, 8))
        self.serpentine_var = tk.BooleanVar(value=True)
        self.output_comments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="蛇行走査を使用する", variable=self.serpentine_var,
                        command=self._on_gui_input_changed).pack(anchor="w")
        ttk.Checkbutton(options, text="Gコードコメントを出力する", variable=self.output_comments_var,
                        command=self._on_gui_input_changed).pack(anchor="w")

        initialization = ttk.LabelFrame(outer, text="初期化Gコード", padding=8)
        initialization.pack(fill="x")
        self.initialization_path_label = ttk.Label(initialization, text="未読込", width=31)
        self.initialization_path_label.pack(side="left", fill="x", expand=True)
        ttk.Button(initialization, text="ファイル選択...", command=self._choose_initialization_file).pack(side="right")

    def _build_map_panel(self, parent) -> None:
        """右側にAoA/AoS較正点マップを埋め込む。"""
        map_frame = ttk.LabelFrame(parent, text="較正点マップ", padding=8)
        map_frame.grid(row=1, column=1, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)

        self.map_view.axes.set_xlabel("AoS [deg]")
        self.map_view.axes.set_ylabel("AoA [deg]")
        self.map_view.axes.grid(True, alpha=0.3)
        self.map_canvas = FigureCanvasTkAgg(self.map_view.figure, master=map_frame)
        self.map_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.map_canvas.draw_idle()

    def _build_status_and_actions(self, parent) -> None:
        """画面下部の非モーダル状態表示と操作ボタンを構築する。"""
        bottom = ttk.Frame(parent)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        bottom.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(bottom, text=self.status_message, anchor="w", relief="sunken", padding=6)
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        files = ttk.Frame(bottom)
        files.grid(row=1, column=0, sticky="w")
        ttk.Button(files, text="設定読込", command=self._choose_load_settings).pack(side="left", padx=(0, 6))
        ttk.Button(files, text="設定保存", command=self._choose_save_settings).pack(side="left")

        actions = ttk.Frame(bottom)
        actions.grid(row=1, column=1, sticky="e")
        self.simulation_button = ttk.Button(actions, text="シミュレーション", command=self._on_simulate)
        self.simulation_button.pack(side="left", padx=(0, 8))
        self.gcode_button = ttk.Button(actions, text="Gコード生成", command=self._choose_generate_gcode)
        self.gcode_button.pack(side="left")

    def _add_range_row(self, parent, row: int, label: str, minimum_key: str, maximum_key: str) -> None:
        """最小値・最大値を横並びにした入力行を追加する。"""
        ttk.Label(parent, text=label, width=20).grid(row=row, column=0, sticky="w", pady=2)
        self._add_entry(parent, row, 1, minimum_key)
        ttk.Label(parent, text="～").grid(row=row, column=2, padx=4)
        self._add_entry(parent, row, 3, maximum_key)

    def _add_value_row(self, parent, row: int, label: str, key: str) -> None:
        """単一値の入力行を追加する。"""
        ttk.Label(parent, text=label, width=20).grid(row=row, column=0, sticky="w", pady=2)
        self._add_entry(parent, row, 1, key, columnspan=3)

    def _add_entry(self, parent, row: int, column: int, key: str, columnspan: int = 1) -> None:
        """入力変更をリアルタイム検証へ接続したEntryを追加する。"""
        variable = tk.StringVar(value=self.DEFAULT_VALUES[key])
        entry = ttk.Entry(parent, textvariable=variable, width=11)
        entry.grid(row=row, column=column, columnspan=columnspan, sticky="ew", pady=2)
        variable.trace_add("write", lambda *_args: self._on_gui_input_changed())
        self._widget_vars[key] = variable
        self._entry_widgets[key] = entry

    def required_labels(self) -> tuple[str, ...]:
        """GUIで必須となる操作ラベルを返す。"""
        return ("シミュレーション", "Gコード生成", "設定保存", "設定読込")

    def _collect_raw_input(self):
        """コントローラで検証するため、現在のGUI入力内容を収集する。"""
        if self._input_provider is not None:
            return self._input_provider()
        if not self._widget_vars:
            return self.controller.get_current_settings()
        return self._settings_from_widgets()

    def _settings_from_widgets(self) -> CalibrationSettings:
        """現在の入力欄をCalibrationSettingsへ変換する。"""
        def f(key: str) -> float:
            return float(self._widget_vars[key].get())

        def i(key: str) -> int:
            return int(self._widget_vars[key].get())

        return CalibrationSettings(
            aoa_min=f("aoa_min"), aoa_max=f("aoa_max"),
            aos_min=f("aos_min"), aos_max=f("aos_max"),
            aoa_points=i("aoa_points"), aos_points=i("aos_points"),
            tip_offset_x=f("tip_offset_x"), tip_offset_y=f("tip_offset_y"),
            hold_time_s=f("hold_time_s"), feed_rate=f("feed_rate"),
            axis_limits=AxisLimits(
                x=AxisRange(f("x_min"), f("x_max")),
                y=AxisRange(f("y_min"), f("y_max")),
                z=AxisRange(f("z_min"), f("z_max")),
                a=AxisRange(f("a_min"), f("a_max")),
            ),
            serpentine=bool(self.serpentine_var.get()),
            output_comments=bool(self.output_comments_var.get()),
        )

    # 対応要求: REQ-VALID-001, REQ-VALID-002
    def _on_gui_input_changed(self) -> None:
        """GUI入力を解析し、一時的な不正入力を非モーダルに処理する。"""
        if self._updating_widgets:
            return
        try:
            settings = self._settings_from_widgets()
        except (TypeError, ValueError):
            self.field_errors = {"input": "数値として解釈できない入力があります。"}
            self.status_message = self.field_errors["input"]
            self.simulation_enabled = False
            self.gcode_enabled = False
            self._refresh_status_widget()
            self._update_button_widgets()
            return
        self._on_input_changed(settings)

    # 対応要求: REQ-VALID-001
    def _on_input_changed(self, raw_input=None) -> None:
        """入力変更を伝搬し、検証表示、較正計画、操作可否を更新する。"""
        if raw_input is None:
            raw_input = self._collect_raw_input()
        validation = self.controller.on_settings_changed(raw_input)
        self._update_validation_display(validation)

        plan = self.controller.get_current_plan()
        if isinstance(plan, CalibrationPlan):
            self.map_view.render(plan)
            self.map_view.axes.grid(True, alpha=0.3)
            self._update_plan_status(plan)
            if self.map_canvas is not None:
                self.map_canvas.draw_idle()
        self._update_action_state()

    # 対応要求: REQ-VALID-001, REQ-LIMIT-002, REQ-GUI-005
    def _update_validation_display(self, validation_result) -> None:
        """非モーダルなフィールド強調表示とエラーメッセージを更新する。"""
        self.field_errors = {issue.field: issue.message for issue in validation_result.issues}
        if self.field_errors:
            self.status_message = " / ".join(self.field_errors.values())
        elif not self.status_message.startswith("X逸脱"):
            self.status_message = "入力値は有効です。"
        self.modal_dialog_requested = False
        self._refresh_status_widget()

    # 対応要求: REQ-LIMIT-002, REQ-LIMIT-003, REQ-GUI-005
    def _update_plan_status(self, plan) -> None:
        """X/Y逸脱警告またはZ/A生成禁止状態を表示する。"""
        messages = []
        if plan.max_x_deviation > 0 or plan.max_y_deviation > 0:
            messages.append(f"X逸脱: {plan.max_x_deviation}, Y逸脱: {plan.max_y_deviation}")
        if plan.has_generation_error:
            messages.append("Z/A可動範囲外のため生成できません。")
        if messages:
            self.status_message = " / ".join(messages)
        elif not self.field_errors:
            self.status_message = f"入力値は有効です。較正点数: {len(plan.points)}"
        self.modal_dialog_requested = False
        self._refresh_status_widget()

    # 対応要求: REQ-VALID-003, REQ-GUI-005
    def _update_action_state(self) -> None:
        """シミュレーションおよびGコード生成操作の有効／無効を更新する。"""
        allowed = bool(self.controller.can_generate())
        self.simulation_enabled = allowed
        self.gcode_enabled = allowed
        self._update_button_widgets()

    def _update_button_widgets(self) -> None:
        """保持中の操作可否を実際のTkボタンへ反映する。"""
        if hasattr(self, "simulation_button"):
            self.simulation_button.configure(state="normal" if self.simulation_enabled else "disabled")
        if hasattr(self, "gcode_button"):
            self.gcode_button.configure(state="normal" if self.gcode_enabled else "disabled")

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
        if hasattr(self, "initialization_path_label"):
            self.initialization_path_label.configure(text=path)
        self.status_message = "初期化Gコードを読み込みました。"
        self._refresh_status_widget()

    def _choose_initialization_file(self) -> None:
        """初期化Gコードのファイル選択ダイアログを表示する。"""
        path = filedialog.askopenfilename(title="初期化Gコードを選択", filetypes=[("Text/G-code", "*.txt *.nc *.gcode"), ("すべてのファイル", "*.*")])
        if path:
            self._on_load_initialization(path)

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
            return
        self.status_message = "設定を保存しました。"
        self._refresh_status_widget()

    def _choose_save_settings(self) -> None:
        """設定CSV保存先を選択する。"""
        path = filedialog.asksaveasfilename(title="設定を保存", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            self._on_save_settings(path)

    # 対応要求: REQ-GUI-003, REQ-GUI-004, REQ-GUI-005
    def _on_load_settings(self, path: str | None = None) -> None:
        """CSV設定を一括で読み込み、失敗時は現在状態を維持する。"""
        if path is None:
            return
        try:
            settings = self.settings_repository.load(path)
        except SettingsLoadError as exc:
            self.status_message = str(exc)
            self.modal_dialog_requested = False
            self._refresh_status_widget()
            return
        validation = self.controller.apply_settings(settings)
        if isinstance(validation, ValidationResult):
            self._update_validation_display(validation)
        self._apply_settings_to_widgets(settings)
        plan = self.controller.get_current_plan()
        if isinstance(plan, CalibrationPlan):
            self.map_view.render(plan)
            self.map_view.axes.grid(True, alpha=0.3)
            self._update_plan_status(plan)
            if self.map_canvas is not None:
                self.map_canvas.draw_idle()
        self._update_action_state()

    def _choose_load_settings(self) -> None:
        """設定CSV読込元を選択する。"""
        path = filedialog.askopenfilename(title="設定を読み込む", filetypes=[("CSV", "*.csv")])
        if path:
            self._on_load_settings(path)

    def _apply_settings_to_widgets(self, settings: CalibrationSettings) -> None:
        """読み込んだ設定を入力欄へ一括反映する。"""
        if not self._widget_vars:
            return
        values = {
            "aoa_min": settings.aoa_min, "aoa_max": settings.aoa_max,
            "aos_min": settings.aos_min, "aos_max": settings.aos_max,
            "aoa_points": settings.aoa_points, "aos_points": settings.aos_points,
            "tip_offset_x": settings.tip_offset_x, "tip_offset_y": settings.tip_offset_y,
            "hold_time_s": settings.hold_time_s, "feed_rate": settings.feed_rate,
            "x_min": settings.axis_limits.x.minimum, "x_max": settings.axis_limits.x.maximum,
            "y_min": settings.axis_limits.y.minimum, "y_max": settings.axis_limits.y.maximum,
            "z_min": settings.axis_limits.z.minimum, "z_max": settings.axis_limits.z.maximum,
            "a_min": settings.axis_limits.a.minimum, "a_max": settings.axis_limits.a.maximum,
        }
        self._updating_widgets = True
        try:
            for key, value in values.items():
                self._widget_vars[key].set(str(value))
            self.serpentine_var.set(settings.serpentine)
            self.output_comments_var.set(settings.output_comments)
        finally:
            self._updating_widgets = False

    # 対応要求: REQ-SIM-001, REQ-GUI-004
    def _on_simulate(self) -> None:
        """現在の較正計画を使用して約10秒のシミュレーションを開始する。"""
        plan = self.controller.get_current_plan()
        if plan is None or not self.controller.can_generate():
            return
        self.simulation_controller.start(plan, duration_s=10.0)
        view = getattr(self.simulation_controller, "view", None)
        figure = getattr(view, "figure", None)
        if figure is not None:
            figure.show()

    # 対応要求: REQ-GCODE-001, REQ-GUI-004
    def _on_generate_gcode(self, path: str | None = None) -> None:
        """現在の共有較正計画から`.nc`文字列を生成し保存する。"""
        if path is None:
            return
        plan = self.controller.get_current_plan()
        settings = self.controller.get_current_settings()
        if plan is None or settings is None or not self.controller.can_generate():
            return
        text = self.gcode_generator.generate(plan, settings, self.initialization_text)
        try:
            self.gcode_repository.save(path, text)
        except OSError as exc:
            self.status_message = f"Gコードを保存できません: {exc}"
            self.modal_dialog_requested = False
            self._refresh_status_widget()
            return
        self.status_message = "Gコードを保存しました。"
        self._refresh_status_widget()

    def _choose_generate_gcode(self) -> None:
        """Gコード保存先を選択する。"""
        path = filedialog.asksaveasfilename(title="Gコードを保存", defaultextension=".nc", filetypes=[("NC file", "*.nc")])
        if path:
            self._on_generate_gcode(path)

    def _refresh_status_widget(self) -> None:
        """ヘッドレステストでは何もせず、実GUIがある場合だけ状態ラベルを更新する。"""
        if hasattr(self, "status_label"):
            self.status_label.configure(text=self.status_message)
