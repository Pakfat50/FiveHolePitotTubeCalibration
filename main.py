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

    # Linux上のGUIレビューでも破綻しないよう、指定フォントが無い場合は
    # Tkの標準フォントが実際に使用しているファミリを採用する。
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
    # Windows/Linux間で背景色の指定結果が大きく変わらないよう、配色可能なclamを使用する。
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", font=(family, 10))
    style.configure("TButton", padding=(10, 6), font=(family, 10))

    # 主要操作は一般のファイル操作より強く視認できる専用スタイルとする。
    style.configure(
        "Simulation.TButton",
        padding=(16, 8),
        font=(family, 10, "bold"),
        foreground="#ffffff",
        background="#3578c4",
        borderwidth=1,
    )
    style.map(
        "Simulation.TButton",
        background=[("active", "#2865a8"), ("disabled", "#a8b6c6")],
        foreground=[("disabled", "#eef2f6")],
    )
    style.configure(
        "Generate.TButton",
        padding=(18, 8),
        font=(family, 10, "bold"),
        foreground="#ffffff",
        background="#27864a",
        borderwidth=1,
    )
    style.map(
        "Generate.TButton",
        background=[("active", "#1f703d"), ("disabled", "#a8b6ad")],
        foreground=[("disabled", "#eef2f0")],
    )


def build_application(root: tk.Tk) -> MainWindow:
    """アプリケーションの依存関係を構築し、MainWindowを返す。

    引数:
        root: Tkinterのルートウィンドウ。

    戻り値:
        すべての依存関係が接続済みのMainWindow。

    対応要求:
        REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004, REQ-SIM-001,
        REQ-GCODE-001
    """
    configure_ui_theme(root)

    validator = InputValidator()
    calibration_service = CalibrationService()
    controller = CalibrationController(validator, calibration_service)

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

    # 対応要求: REQ-GUI-001, REQ-GUI-004
    # フルHD以上の実運用ディスプレイを前提に、全入力欄と操作部を一画面へ収める。
    root.geometry("1280x900")
    root.minsize(1100, 820)

    # 一般操作と主要実行操作の優先度を視覚的に分ける。
    application.simulation_button.configure(style="Simulation.TButton")
    application.gcode_button.configure(style="Generate.TButton")

    return application


def main() -> None:
    """アプリケーション依存関係を構築し、GUIを起動する。

    Presentation -> Application -> Domain/Core の依存方向に従い、
    ファイルI/OはInfrastructure層へ分離して構築する。

    対応要求:
        REQ-GUI-004
    """
    root = tk.Tk()
    application = build_application(root)
    application.run()


if __name__ == "__main__":
    main()
