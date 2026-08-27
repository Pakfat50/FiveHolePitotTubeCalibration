"""較正機構のシミュレーション制御および表示を行う。"""

import math

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
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
        """実際のGコード保持時間とは独立した約10秒の再生を開始する。

        引数:
            plan: 再生対象の較正計画。
            duration_s: シミュレーション全体の再生時間[s]。

        対応要求:
            REQ-SIM-001, REQ-SIM-002
        """
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
        """正規化進捗に対応する走査点を選択する。

        引数:
            plan: 再生対象の較正計画。
            progress: 0.0から1.0までの正規化再生進捗。

        戻り値:
            進捗に対応する較正点評価結果。

        例外:
            ValueError: 較正点が存在しない場合。

        対応要求:
            REQ-SIM-002
        """
        if not plan.points:
            raise ValueError("較正点が存在しません。")
        normalized = min(1.0, max(0.0, progress))
        index = round(normalized * (len(plan.points) - 1))
        return plan.points[index]


class SimulationView:
    """機構姿勢・較正点マップ・現在較正点情報をアニメーション表示する。

    対応要求:
        REQ-SIM-002, REQ-SIM-003, REQ-SIM-004, REQ-SIM-005, REQ-SIM-006
    """

    FRAME_INTERVAL_MS = 100
    FRONT_LIMIT = 1.35
    CALIBRATION_POINT_COLOR = "tab:blue"
    CURRENT_POINT_COLOR = "tab:red"
    CALIBRATION_POINT_SIZE = 45

    def __init__(self) -> None:
        self.figure = None
        self.side_axes = None
        self.front_axes = None
        self.calibration_axes = None
        self.status_text = ""
        self.current_point_index = None
        self.final_state_visible = False
        self.animation = None
        self._status_artist = None
        self._progress_artist = None
        self._calibration_points_artist = None
        self._current_calibration_artist = None
        self._plan = None
        self._side_xlim = (-150.0, 150.0)
        self._side_ylim = (-150.0, 150.0)
        self._calibration_xlim = (-1.0, 1.0)
        self._calibration_ylim = (-1.0, 1.0)
        self._japanese_graph_text = False

    # 対応要求: REQ-SIM-003, REQ-SIM-005, REQ-GUI-001
    def _configure_matplotlib_font(self) -> None:
        """利用可能な日本語フォントをMatplotlibへ設定する。

        Windowsではメイリオ系、LinuxではNoto Sans CJK JPを優先する。
        日本語フォントが見つからない環境では英語ラベルへ切り替え、豆腐文字を防ぐ。

        対応要求:
            REQ-SIM-003, REQ-SIM-005, REQ-GUI-001
        """
        available = {font.name for font in font_manager.fontManager.ttflist}
        preferred = ("Meiryo UI", "Meiryo", "Yu Gothic UI", "Noto Sans CJK JP")
        family = next((name for name in preferred if name in available), None)
        if family is not None:
            rcParams["font.family"] = [family]
            self._japanese_graph_text = True
        else:
            rcParams["font.family"] = ["DejaVu Sans"]
            self._japanese_graph_text = False
        rcParams["axes.unicode_minus"] = False

    def _text(self, japanese: str, english: str) -> str:
        """日本語描画可否に応じた表示文字列を返す。"""
        return japanese if self._japanese_graph_text else english

    def _get_dimensions(self) -> tuple[float, float]:
        """較正計画からLx/Lyを取得し、取得不能時は既定寸法へフォールバックする。"""
        lx, ly = 100.0, 0.0
        settings = getattr(self._plan, "settings", None)
        if settings is not None:
            try:
                lx = float(settings.tip_offset_x)
                ly = float(settings.tip_offset_y)
            except (TypeError, ValueError):
                pass
        return lx, ly

    # 対応要求: REQ-SIM-003
    def _calculate_side_limits(self, plan: CalibrationPlan) -> None:
        """全較正点のピボットと先端を含む固定横面図範囲を算出する。"""
        self._plan = plan
        lx, ly = self._get_dimensions()
        xs: list[float] = []
        ys: list[float] = []

        for point in getattr(plan, "points", ()):
            try:
                pivot_x = float(point.command.x)
                pivot_y = float(point.command.y)
                theta = math.radians(float(point.command.z))
            except (TypeError, ValueError):
                continue
            tip_x = pivot_x + lx * math.cos(theta) - ly * math.sin(theta)
            tip_y = pivot_y + lx * math.sin(theta) + ly * math.cos(theta)
            xs.extend((pivot_x, tip_x))
            ys.extend((pivot_y, tip_y))

        if not xs or not ys:
            self._side_xlim = (-150.0, 150.0)
            self._side_ylim = (-150.0, 150.0)
            return

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        span_x = max(xmax - xmin, 1.0)
        span_y = max(ymax - ymin, 1.0)
        characteristic_length = max(abs(lx), abs(ly), 1.0)
        margin = max(10.0, 0.08 * max(span_x, span_y), 0.08 * characteristic_length)
        self._side_xlim = (xmin - margin, xmax + margin)
        self._side_ylim = (ymin - margin, ymax + margin)

    # 対応要求: REQ-SIM-005
    def _calculate_calibration_limits(self, plan: CalibrationPlan) -> None:
        """全較正点が範囲外にならない固定AoA/AoS表示範囲を算出する。

        引数:
            plan: 全較正点を含む較正計画。

        対応要求:
            REQ-SIM-005
        """
        aos_values = [float(point.point.aos) for point in getattr(plan, "points", ())]
        aoa_values = [float(point.point.aoa) for point in getattr(plan, "points", ())]
        if not aos_values or not aoa_values:
            self._calibration_xlim = (-1.0, 1.0)
            self._calibration_ylim = (-1.0, 1.0)
            return

        def limits(values: list[float]) -> tuple[float, float]:
            minimum = min(values)
            maximum = max(values)
            span = max(maximum - minimum, 1.0)
            margin = max(1.0, span * 0.08)
            return minimum - margin, maximum + margin

        self._calibration_xlim = limits(aos_values)
        self._calibration_ylim = limits(aoa_values)

    # 対応要求: REQ-SIM-003, REQ-SIM-005
    def initialize(self, plan: CalibrationPlan) -> None:
        """機構2面図、較正点マップ、および状態表示領域を初期化する。

        引数:
            plan: シミュレーション対象の較正計画。

        対応要求:
            REQ-SIM-003, REQ-SIM-005
        """
        self._plan = plan
        self._configure_matplotlib_font()
        self._calculate_side_limits(plan)
        self._calculate_calibration_limits(plan)

        self.figure = plt.figure(figsize=(12.0, 8.0))
        grid = self.figure.add_gridspec(2, 2, height_ratios=(1.05, 0.95), hspace=0.28, wspace=0.22)
        self.side_axes = self.figure.add_subplot(grid[0, 0])
        self.front_axes = self.figure.add_subplot(grid[0, 1])
        self.calibration_axes = self.figure.add_subplot(grid[1, 0])
        status_axes = self.figure.add_subplot(grid[1, 1])

        self._configure_side_axes()
        self._configure_front_axes()
        self._draw_calibration_map(plan)

        status_axes.set_axis_off()
        self._status_artist = status_axes.text(0.02, 0.92, "", transform=status_axes.transAxes, va="top")
        self._progress_artist = status_axes.plot([0.02, 0.02], [0.08, 0.08], linewidth=9)[0]
        status_axes.plot([0.02, 0.98], [0.08, 0.08], linewidth=9, alpha=0.15)
        status_axes.set_xlim(0.0, 1.0)
        status_axes.set_ylim(0.0, 1.0)

        self.figure.suptitle(self._text("5孔ピトー管 較正シミュレーション", "Five-hole Pitot Calibration Simulation"))
        self.figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
        self.final_state_visible = False

    # 対応要求: REQ-SIM-003
    def _configure_side_axes(self) -> None:
        """横面図の見出しと固定軸範囲を設定する。"""
        axes = self.side_axes
        axes.set_title(self._text("横面図（ピッチ / X-Y補正）", "Side View (Pitch / X-Y Compensation)"))
        axes.set_xlabel("X [mm]")
        axes.set_ylabel("Y [mm]")
        axes.grid(True, alpha=0.25)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlim(*self._side_xlim)
        axes.set_ylim(*self._side_ylim)

    # 対応要求: REQ-SIM-003
    def _configure_front_axes(self) -> None:
        """正面図の見出しと固定表示範囲を設定する。

        正面図の座標値は物理量を表さないため、軸ラベルと数値目盛は表示しない。

        対応要求:
            REQ-SIM-003
        """
        axes = self.front_axes
        axes.set_title(self._text("正面図（ロール）", "Front View (Roll)"))
        axes.set_xlabel("")
        axes.set_ylabel("")
        axes.set_xticks([])
        axes.set_yticks([])
        axes.grid(False)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlim(-self.FRONT_LIMIT, self.FRONT_LIMIT)
        axes.set_ylim(-self.FRONT_LIMIT, self.FRONT_LIMIT)

    # 対応要求: REQ-SIM-005
    def _configure_calibration_axes(self) -> None:
        """シミュレーション用較正点マップの固定軸を設定する。

        対応要求:
            REQ-SIM-005
        """
        axes = self.calibration_axes
        axes.set_title(self._text("較正点マップ", "Calibration Point Map"))
        axes.set_xlabel("AoS [deg]")
        axes.set_ylabel("AoA [deg]")
        axes.grid(True, alpha=0.25)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlim(*self._calibration_xlim)
        axes.set_ylim(*self._calibration_ylim)

    # 対応要求: REQ-SIM-005
    def _draw_calibration_map(self, plan: CalibrationPlan) -> None:
        """全較正点をシミュレーション用マップへ静的に描画する。

        凡例や現在点を説明する文字注記は追加しない。現在点は別のArtistを
        同じ座標へ重ね、その色だけを変えることで表現する。

        引数:
            plan: 全較正点を含む較正計画。

        対応要求:
            REQ-SIM-005
        """
        self._configure_calibration_axes()
        coordinates = [(float(point.point.aos), float(point.point.aoa)) for point in plan.points]
        aos_values = [coordinate[0] for coordinate in coordinates]
        aoa_values = [coordinate[1] for coordinate in coordinates]
        self._calibration_points_artist = self.calibration_axes.scatter(
            aos_values,
            aoa_values,
            s=self.CALIBRATION_POINT_SIZE,
            color=self.CALIBRATION_POINT_COLOR,
            zorder=2,
        )
        self._current_calibration_artist = self.calibration_axes.scatter(
            [],
            [],
            s=self.CALIBRATION_POINT_SIZE,
            color=self.CURRENT_POINT_COLOR,
            zorder=3,
        )

    # 対応要求: REQ-SIM-002
    def start_animation(self, plan: CalibrationPlan, duration_s: float, frame_provider) -> None:
        """指定時間で全較正点を走査するMatplotlibアニメーションを開始する。

        引数:
            plan: 再生対象の較正計画。
            duration_s: シミュレーション全体の再生時間[s]。
            frame_provider: 正規化進捗から現在点を返す関数。

        対応要求:
            REQ-SIM-002
        """
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

    # 対応要求: REQ-SIM-003, REQ-SIM-004, REQ-SIM-006
    def render_frame(self, point: PointEvaluation, progress: float) -> None:
        """現在点の機構姿勢、較正点強調および状態情報を同期して描画する。

        引数:
            point: 現在表示する較正点評価結果。
            progress: 0.0から1.0までの正規化再生進捗。

        対応要求:
            REQ-SIM-003, REQ-SIM-004, REQ-SIM-006
        """
        self.current_point_index = point.point.index
        if self._japanese_graph_text:
            state = "ZA範囲外" if point.rotational_error else (
                "XY飽和" if point.x_saturated or point.y_saturated else "正常"
            )
            state_label = "状態"
            progress_label = "進捗"
        else:
            state = "ZA out of range" if point.rotational_error else (
                "XY saturated" if point.x_saturated or point.y_saturated else "Normal"
            )
            state_label = "State"
            progress_label = "Progress"

        command = point.command
        self.status_text = (
            f"Point {point.point.index + 1} / AoA {point.point.aoa:.2f} / AoS {point.point.aos:.2f} / "
            f"X {command.x:.2f} / Y {command.y:.2f} / Z {command.z:.2f} / A {command.a:.2f} / "
            f"{state_label} {state} / {progress_label} {progress * 100:.0f}%"
        )
        display_text = (
            f"Point {point.point.index + 1}\n"
            f"AoA {point.point.aoa:+.2f}°    AoS {point.point.aos:+.2f}°\n"
            f"X {command.x:.2f} mm    Y {command.y:.2f} mm\n"
            f"Z {command.z:.2f}°    A {command.a:.2f}°\n"
            f"{state_label}: {state}    {progress_label}: {progress * 100:.0f}%"
        )

        if self.side_axes is not None:
            self._draw_side_view(point)
        if self.front_axes is not None:
            self._draw_front_view(point)
        self._update_current_calibration_point(point)
        if self._status_artist is not None:
            self._status_artist.set_text(display_text)
        if self._progress_artist is not None:
            end_x = 0.02 + 0.96 * min(1.0, max(0.0, progress))
            self._progress_artist.set_data([0.02, end_x], [0.08, 0.08])
        if self.figure is not None:
            self.figure.canvas.draw_idle()

    # 対応要求: REQ-SIM-006
    def _update_current_calibration_point(self, point: PointEvaluation) -> None:
        """較正点マップの強調点を現在のAoA/AoSへ移動する。

        引数:
            point: 横面図・正面図と同じ現在較正点。

        対応要求:
            REQ-SIM-006
        """
        if self._current_calibration_artist is None:
            return
        self._current_calibration_artist.set_offsets([[float(point.point.aos), float(point.point.aoa)]])

    # 対応要求: REQ-SIM-003
    def _draw_side_view(self, point: PointEvaluation) -> None:
        """X/Y並進位置とピッチ姿勢を固定範囲の横面図へ描画する。"""
        axes = self.side_axes
        axes.clear()
        self._configure_side_axes()

        lx, ly = self._get_dimensions()
        theta = math.radians(point.command.z)
        pivot_x = point.command.x
        pivot_y = point.command.y
        tip_x = pivot_x + lx * math.cos(theta) - ly * math.sin(theta)
        tip_y = pivot_y + lx * math.sin(theta) + ly * math.cos(theta)

        body_line = axes.plot([pivot_x, tip_x], [pivot_y, tip_y], linewidth=5)[0]
        body_color = body_line.get_color()
        axes.scatter([pivot_x], [pivot_y], marker="o", s=55, color=body_color)

        # 固定向きの三角マーカーではなく、ピトー管本体の方向ベクトルに沿う矢印を描く。
        direction_x = tip_x - pivot_x
        direction_y = tip_y - pivot_y
        direction_length = math.hypot(direction_x, direction_y)
        if direction_length > 0.0:
            unit_x = direction_x / direction_length
            unit_y = direction_y / direction_length
            arrow_length = min(direction_length * 0.25, max(8.0, direction_length * 0.12))
            arrow_start_x = tip_x - unit_x * arrow_length
            arrow_start_y = tip_y - unit_y * arrow_length
            axes.annotate(
                "",
                xy=(tip_x, tip_y),
                xytext=(arrow_start_x, arrow_start_y),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": body_color,
                    "linewidth": 2.5,
                    "mutation_scale": 14,
                },
            )

        axes.text(tip_x, tip_y, self._text("先端", "Tip"), va="bottom", ha="left")
        axes.text(
            0.02, 0.96,
            f"Z={point.command.z:.2f}°\nX={pivot_x:.2f} mm\nY={pivot_y:.2f} mm",
            transform=axes.transAxes,
            va="top",
        )

    # 対応要求: REQ-SIM-003
    def _draw_front_view(self, point: PointEvaluation) -> None:
        """ピトー管のロール姿勢を固定範囲の正面図へ描画する。"""
        axes = self.front_axes
        axes.clear()
        self._configure_front_axes()

        radius = 1.0
        angle = math.radians(point.command.a)
        circle = plt.Circle((0.0, 0.0), radius, fill=False, linewidth=2, alpha=0.35)
        axes.add_patch(circle)
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        axes.plot([-dx, dx], [-dy, dy], linewidth=5)
        axes.plot([0.0], [0.0], marker="o", markersize=7)
        axes.text(0.02, 0.96, f"A={point.command.a:.2f}°", transform=axes.transAxes, va="top")

    def show_final_state(self) -> None:
        """再生終了後も最終較正状態を表示したままにする。

        対応要求:
            REQ-SIM-002, REQ-SIM-004, REQ-SIM-006
        """
        self.final_state_visible = True
