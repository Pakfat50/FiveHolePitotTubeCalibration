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


def configure_ui_theme(root: tk.Tk) -> None:
    """読みやすい日本語フォントと主要操作部品の外観を設定する。

    対応要求:
        REQ-GUI-001, REQ-GUI-004
    """
    available = set(tkfont.families(root))
    family = next(
        (name for name in ("Meiryo UI", "Meiryo", "Yu Gothic UI", "Noto Sans CJK JP") if name in available),
        tkfont.nametofont("TkDefaultFont").actual("family"),
    )
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkCaptionFont", "TkSmallCaptionFont"):
        try:
            tkfont.nametofont(name).configure(family=family, size=10)
        except tk.TclError:
            pass

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure(".", font=(family, 10))
    style.configure("TButton", padding=(10, 6), font=(family, 10))
    style.configure("TLabelframe.Label", font=(family, 10, "bold"), padding=(8, 2))

    style.configure(
        "Simulation.TButton", padding=(16, 8), font=(family, 10, "bold"),
        foreground="#ffffff", background="#3578c4",
    )
    style.map("Simulation.TButton", background=[("active", "#2865a8"), ("disabled", "#a8b6c6")])
    style.configure(
        "Generate.TButton", padding=(18, 8), font=(family, 10, "bold"),
        foreground="#ffffff", background="#27864a",
    )
    style.map("Generate.TButton", background=[("active", "#1f703d"), ("disabled", "#a8b6ad")])


def tune_vertical_layout(application: MainWindow) -> None:
    """フルHD環境で各設定グループをゆったり表示する。

    対応要求:
        REQ-GUI-001, REQ-GUI-004
    """
    def walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from walk(child)

    for widget in walk(application.main_frame):
        if isinstance(widget, ttk.LabelFrame) and str(widget.cget("text")) != "較正点マップ":
            widget.configure(padding=9, labelanchor="nw")
            if widget.winfo_manager() == "pack" and widget.pack_info().get("pady", 0):
                widget.pack_configure(pady=(0, 9))
        elif isinstance(widget, ttk.Entry) and widget.winfo_manager() == "grid":
            widget.grid_configure(pady=3)
        elif isinstance(widget, ttk.Label) and widget.winfo_manager() == "grid":
            info = widget.grid_info()
            if int(info.get("column", 0)) <= 3:
                widget.grid_configure(pady=3)


def build_application(root: tk.Tk) -> MainWindow:
    """依存関係を構築してMainWindowを返す。

    対応要求:
        REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004,
        REQ-SIM-001, REQ-GCODE-001
    """
    configure_ui_theme(root)
    controller = CalibrationController(InputValidator(), CalibrationService())
    simulation_controller = SimulationController(SimulationView())
    application = MainWindow(
        root=root,
        controller=controller,
        settings_repository=SettingsRepository(),
        initialization_repository=InitializationGCodeRepository(),
        gcode_generator=GCodeGenerator(),
        gcode_repository=GCodeRepository(),
        map_view=CalibrationMapView(),
        simulation_controller=simulation_controller,
        build_ui=True,
    )
    root.geometry("1360x960")
    root.minsize(1180, 860)
    tune_vertical_layout(application)
    application.simulation_button.configure(style="Simulation.TButton")
    application.gcode_button.configure(style="Generate.TButton")
    return application


def main() -> None:
    """GUIアプリケーションを起動する。"""
    root = tk.Tk()
    build_application(root).run()


if __name__ == "__main__":
    main()
