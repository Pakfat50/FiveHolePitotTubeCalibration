"""5孔ピトー管較正GUIアプリケーションのエントリポイント。"""

import tkinter as tk
from tkinter import font as tkfont, ttk

from calibration_service import CalibrationService
from controller import CalibrationController
from gcode import GCodeGenerator
from gui import MainWindow
from map_view import CalibrationMapView
from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository
from simulation import SimulationController, SimulationView
from validation import InputValidator


# 対応要求: REQ-GUI-001, REQ-GUI-004
def configure_ui_theme(root: tk.Tk) -> None:
    """Windowsを主対象として、読みやすい日本語フォントと操作部品の外観を設定する。

    Windowsではメイリオを優先し、利用できない環境ではYu Gothic UI、
    Noto Sans CJK JP、Tk既定フォントの順でフォールバックする。

    引数:
        root: Tkinterのルートウィンドウ。

    対応要求:
        REQ-GUI-001, REQ-GUI-004
    """
    available = set(tkfont.families(root))
    preferred_families = ("Meiryo UI", "Meiryo", "Yu Gothic UI", "Noto Sans CJK JP")
    family = next((name for name in preferred_families if name in available), None)
    if family is None:
        family = tkfont.nametofont("TkDefaultFont").actual("family")

    for named_font in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkCaptionFont", "TkSmallCaptionFont"):
        try:
            tkfont.nametofont(named_font).configure(family=family, size=10)
        except tk.TclError:
            pass
    try:
        tkfont.nametofont("TkHeadingFont").configure(family=family, size=10, weight="bold")
    except tk.TclError:
        pass

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure(".", font=(family, 10))
    style.configure("TButton", padding=(10, 6), font=(family, 10))
    style.configure(
        "Simulation.TButton", padding=(16, 8), font=(family, 10, "bold"),
        foreground="#ffffff", background="#3578c4", borderwidth=1,
    )
    style.map(
        "Simulation.TButton",
        background=[("active", "#2865a8"), ("disabled", "#a8b6c6")],
        foreground=[("disabled", "#eef2f6")],
    )
    style.configure(
        "Generate.TButton", padding=(18, 8), font=(family, 10, "bold"),
        foreground="#ffffff", background="#27864a", borderwidth=1,
    )
    style.map(
        "Generate.TButton",
        background=[("active", "#1f703d"), ("disabled", "#a8b6ad")],
        foreground=[("disabled", "#eef2f0")],
    )


# 対応要求: REQ-GUI-001, REQ-GUI-004
def tune_vertical_layout(application: MainWindow) -> None:
    """1280x900内に全項目を収めつつ、左側設定項目の余白を確保する。

    前版よりLabelFrame間隔・内部余白・入力行余白を広げ、設定項目の視認性を
    高める。一方で初期化Gコード欄と下部操作欄は900px高の範囲内に維持する。

    引数:
        application: 構築済みMainWindow。

    対応要求:
        REQ-GUI-001, REQ-GUI-004
    """
    def walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from walk(child)

    for widget in walk(application.main_frame):
        if isinstance(widget, ttk.LabelFrame):
            if str(widget.cget("text")) != "較正点マップ":
                widget.configure(padding=7)
                if widget.winfo_manager() == "pack":
                    pack_info = widget.pack_info()
                    if pack_info.get("pady", 0):
                        widget.pack_configure(pady=(0, 6))
        elif isinstance(widget, ttk.Entry) and widget.winfo_manager() == "grid":
            widget.grid_configure(pady=2)
        elif isinstance(widget, ttk.Label) and widget.winfo_manager() == "grid":
            grid_info = widget.grid_info()
            if int(grid_info.get("column", 0)) <= 3:
                try:
                    widget.grid_configure(pady=2)
                except tk.TclError:
                    pass


def build_application(root: tk.Tk) -> MainWindow:
    """アプリケーションの依存関係を構築し、MainWindowを返す。

    対応要求:
        REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004, REQ-SIM-001,
        REQ-GCODE-001
    """
    configure_ui_theme(root)
    controller = CalibrationController(InputValidator(), CalibrationService())
    map_view = CalibrationMapView()
    simulation_view = SimulationView()
    simulation_controller = SimulationController(simulation_view)

    application = MainWindow(
        root=root,
        controller=controller,
        settings_repository=SettingsRepository(),
        initialization_repository=InitializationGCodeRepository(),
        gcode_generator=GCodeGenerator(),
        gcode_repository=GCodeRepository(),
        map_view=map_view,
        simulation_controller=simulation_controller,
        build_ui=True,
    )

    root.geometry("1280x900")
    root.minsize(1100, 820)
    tune_vertical_layout(application)
    application.simulation_button.configure(style="Simulation.TButton")
    application.gcode_button.configure(style="Generate.TButton")
    return application


def main() -> None:
    """アプリケーション依存関係を構築し、GUIを起動する。

    対応要求:
        REQ-GUI-004
    """
    root = tk.Tk()
    application = build_application(root)
    application.run()


if __name__ == "__main__":
    main()
