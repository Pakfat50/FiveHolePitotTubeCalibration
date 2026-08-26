"""5孔ピトー管較正GUIアプリケーションのエントリポイント。"""

import tkinter as tk

from calibration_service import CalibrationService
from controller import CalibrationController
from gcode import GCodeGenerator
from gui import MainWindow
from map_view import CalibrationMapView
from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository
from simulation import SimulationController, SimulationView
from validation import InputValidator


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
    validator = InputValidator()
    calibration_service = CalibrationService()
    controller = CalibrationController(validator, calibration_service)

    map_view = CalibrationMapView()
    simulation_view = SimulationView()
    simulation_controller = SimulationController(simulation_view)

    return MainWindow(
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
