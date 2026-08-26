"""較正機構のシミュレーション制御および表示を行う。"""

import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from models import CalibrationPlan, PointEvaluation


class SimulationController:
    """正規化された再生進捗を較正点へ対応付け、SimulationViewを駆動する。

    引数:
        view: SimulationView互換のPresentation依存オブジェクト。

    対応要求:
        REQ-SIM-001, REQ-SIM-002
    """

    def __init__(self, view) -> None:
        self.view = view
        self.duration_s: float | None = None

    # 対応要求: REQ-SIM-001, REQ-SIM-002
    def start(self, plan: CalibrationPlan, duration_s: float = 10.0) -> None:
        """実際のGコード保持時間とは独立した約10秒の再生を開始する。"""
        self.duration_s = duration_s
        self.view.initialize(plan)
        if not plan.points:
            return
        self.view.start_animation(
            plan=plan,
            duration_s=duration_s,
            frame_provider=lambda progress: self._frame_at(plan, progress),
        )

    # 対応要求: REQ-SIM-002
    def _frame_at(self, plan: CalibrationPlan, progress: float) -> PointEvaluation:
        """正規化進捗に対応する走査点を選択する。"""
        if not plan.points:
            raise ValueError("較正点が存在しません。")
        normalized = min(1.0, max(0.0, progress))
        index = round(normalized * (len(plan.points) - 1))
        return plan.points[index]


class SimulationView:
    """横面図・正面図と現在較正点情報をアニメーション表示する。

    対応要求:
        REQ-SIM-002, REQ-SIM-003, REQ-SIM-004
    """

    FRAME_INTERVAL_MS = 100

    def __init__(self) -> None:
        self.figure = None
        self.side_axes = None
        self.front_axes = None
        self.status_text = ""
        self.current_point_index = None
        self.final_state_visible = False
        self.animation = None
        self._status_artist = None
        self._progress_artist = None
        self._plan = None

    # 対応要求: REQ-SIM-003
    def initialize(self, plan: CalibrationPlan) -> None:
        """横面図と正面図、および状態表示領域を初期化する。"""
        self._plan = plan
        self.figure = plt.figure(figsize=(11.0, 6.8))
        grid = self.figure.add_gridspec(2, 2, height_ratios=(8, 1.7))
        self.side_axes = self.figure.add_subplot(grid[0, 0])
        self.front_axes = self.figure.add_subplot(grid[0, 1])
        status_axes = self.figure.add_subplot(grid[1, :])

        self.side_axes.set_title("横面図（ピッチ / X-Y補正）")
        self.front_axes.set_title("正面図（ロール）")
        self.side_axes.set_aspect("equal", adjustable="box")
        self.front_axes.set_aspect("equal", adjustable="box")
        self.side_axes.grid(True, alpha=0.25)
        self.front_axes.grid(True, alpha=0.25)

        status_axes.set_axis_off()
        self._status_artist = status_axes.text(0.01, 0.72, "", transform=status_axes.transAxes, va="top")
        self._progress_artist = status_axes.plot([0.01, 0.01], [0.18, 0.18], linewidth=8)[0]
        status_axes.plot([0.01, 0.99], [0.18, 0.18], linewidth=8, alpha=0.15)
        status_axes.set_xlim(0.0, 1.0)
        status_axes.set_ylim(0.0, 1.0)

        self.figure.suptitle("5孔ピトー管 較正シミュレーション")
        self.figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
        self.final_state_visible = False

    # 対応要求: REQ-SIM-002
    def start_animation(self, plan: CalibrationPlan, duration_s: float, frame_provider) -> None:
        """指定時間で全較正点を走査するMatplotlibアニメーションを開始する。"""
        frame_count = max(2, round(duration_s * 1000.0 / self.FRAME_INTERVAL_MS) + 1)

        def update(frame_index: int):
            progress = frame_index / (frame_count - 1)
            point = frame_provider(progress)
            self.render_frame(point, progress)
            if frame_index == frame_count - 1:
                self.show_final_state()
            return ()

        # animationをメンバーとして保持し、Figure表示後のGCによる停止を防止する。
        self.animation = FuncAnimation(
            self.figure,
            update,
            frames=frame_count,
            interval=self.FRAME_INTERVAL_MS,
            repeat=False,
            blit=False,
        )
        self.figure.canvas.draw_idle()

    # 対応要求: REQ-SIM-003, REQ-SIM-004
    def render_frame(self, point: PointEvaluation, progress: float) -> None:
        """現在点の機構姿勢と必要な状態情報を描画する。"""
        self.current_point_index = point.point.index
        state = "ZA範囲外" if point.rotational_error else (
            "XY飽和" if point.x_saturated or point.y_saturated else "正常"
        )
        command = point.command
        self.status_text = (
            f"Point {point.point.index + 1} / AoA {point.point.aoa:.2f} / AoS {point.point.aos:.2f} / "
            f"X {command.x:.2f} / Y {command.y:.2f} / Z {command.z:.2f} / A {command.a:.2f} / "
            f"状態 {state} / 進捗 {progress * 100:.0f}%"
        )

        if self.side_axes is not None:
            self._draw_side_view(point)
        if self.front_axes is not None:
            self._draw_front_view(point)
        if self._status_artist is not None:
            self._status_artist.set_text(self.status_text)
        if self._progress_artist is not None:
            end_x = 0.01 + 0.98 * min(1.0, max(0.0, progress))
            self._progress_artist.set_data([0.01, end_x], [0.18, 0.18])
        if self.figure is not None:
            self.figure.canvas.draw_idle()

    # 対応要求: REQ-SIM-003
    def _draw_side_view(self, point: PointEvaluation) -> None:
        """X/Y並進位置とピッチ姿勢を横面図へ描画する。"""
        axes = self.side_axes
        axes.clear()
        axes.set_title("横面図（ピッチ / X-Y補正）")
        axes.set_xlabel("X [mm]")
        axes.set_ylabel("Y [mm]")
        axes.grid(True, alpha=0.25)
        axes.set_aspect("equal", adjustable="box")

        # 通常はCalibrationPlan.settingsを使用する。単体テストのMock等で設定値を
        # 数値化できない場合だけ既定寸法へフォールバックし、Viewを停止させない。
        lx, ly = 100.0, 0.0
        settings = getattr(self._plan, "settings", None)
        if settings is not None:
            try:
                lx = float(settings.tip_offset_x)
                ly = float(settings.tip_offset_y)
            except (TypeError, ValueError):
                pass

        theta = math.radians(point.command.z)
        pivot_x = point.command.x
        pivot_y = point.command.y
        tip_x = pivot_x + lx * math.cos(theta) - ly * math.sin(theta)
        tip_y = pivot_y + lx * math.sin(theta) + ly * math.cos(theta)

        axes.plot([pivot_x, tip_x], [pivot_y, tip_y], linewidth=5)
        axes.scatter([pivot_x], [pivot_y], marker="o", s=55)
        axes.scatter([tip_x], [tip_y], marker=">", s=75)

        margin = max(20.0, abs(lx) * 0.25, abs(ly) * 0.25)
        xmin = min(pivot_x, tip_x) - margin
        xmax = max(pivot_x, tip_x) + margin
        ymin = min(pivot_y, tip_y) - margin
        ymax = max(pivot_y, tip_y) + margin
        if xmax - xmin < 2 * margin:
            xmax = xmin + 2 * margin
        if ymax - ymin < 2 * margin:
            ymax = ymin + 2 * margin
        axes.set_xlim(xmin, xmax)
        axes.set_ylim(ymin, ymax)
        axes.text(
            0.02, 0.96,
            f"Z={point.command.z:.2f}°\nX={pivot_x:.2f} mm\nY={pivot_y:.2f} mm",
            transform=axes.transAxes,
            va="top",
        )

    # 対応要求: REQ-SIM-003
    def _draw_front_view(self, point: PointEvaluation) -> None:
        """ピトー管のロール姿勢を正面図へ描画する。"""
        axes = self.front_axes
        axes.clear()
        axes.set_title("正面図（ロール）")
        axes.set_xlabel("水平")
        axes.set_ylabel("垂直")
        axes.grid(True, alpha=0.25)
        axes.set_aspect("equal", adjustable="box")

        radius = 1.0
        angle = math.radians(point.command.a)
        circle = plt.Circle((0.0, 0.0), radius, fill=False, linewidth=2, alpha=0.35)
        axes.add_patch(circle)
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        axes.plot([-dx, dx], [-dy, dy], linewidth=5)
        axes.plot([0.0], [0.0], marker="o", markersize=7)
        axes.set_xlim(-1.35, 1.35)
        axes.set_ylim(-1.35, 1.35)
        axes.text(0.02, 0.96, f"A={point.command.a:.2f}°", transform=axes.transAxes, va="top")

    def show_final_state(self) -> None:
        """再生終了後も最終較正状態を表示したままにする。

        対応要求:
            REQ-SIM-002, REQ-SIM-004
        """
        self.final_state_visible = True
