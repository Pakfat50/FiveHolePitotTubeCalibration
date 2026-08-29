"""較正機構のシミュレーション制御および表示を行う。"""

import math

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider

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
        self.plan: CalibrationPlan | None = None
        self.current_point_index: int | None = None
        self.playback_state = "idle"

    # 対応要求: REQ-SIM-001, REQ-SIM-002, REQ-SIM-007
    def start(self, plan: CalibrationPlan, duration_s: float = 10.0) -> None:
        """先頭の較正点からシミュレーションを再生する。

        引数:
            plan: 再生対象の較正計画。
            duration_s: シミュレーション全体の再生時間[s]。

        対応要求:
            REQ-SIM-001, REQ-SIM-002, REQ-SIM-007
        """
        self.duration_s = duration_s
        self.plan = plan
        self.current_point_index = 0 if plan.points else None
        self.playback_state = "playing"
        self.view.initialize(plan)
        self.view.set_playback_callbacks(self.pause, self.resume, self.seek_to_point)
        if not plan.points:
            self.playback_state = "paused"
            self.view.set_playback_state("paused")
            return
        self.view.render_frame(plan.points[0], 0.0)
        self.view.start_animation(
            plan=plan,
            duration_s=duration_s,
            frame_provider=lambda progress: self._frame_at(plan, progress),
            on_complete=self.on_animation_complete,
        )
        self.view.set_playback_state("playing")

    # 対応要求: REQ-SIM-008
    def pause(self) -> None:
        """現在位置を保持したままアニメーションを一時停止する。

アニメーションタイマーだけを停止し、現在較正点、3画面の描画状態、およびシークバーの位置は変更しない。再生状態を ``paused`` へ遷移させ、Viewの操作ボタン表示を更新する。

        戻り値:
            None

        対応要求:
            REQ-SIM-008
        """
        if self.playback_state != "playing":
            return
        self.view.pause_animation()
        self.playback_state = "paused"
        self.view.set_playback_state("paused")

    # 対応要求: REQ-SIM-009
    def resume(self) -> None:
        """一時停止中は現在位置から、完了後は先頭から再生する。

``paused`` 状態では既存のアニメーションタイマーを再開する。``completed`` 状態では現在点を先頭へ戻し、新しいアニメーションを生成する。

        戻り値:
            None

        対応要求:
            REQ-SIM-009
        """
        if self.plan is None or not self.plan.points:
            return
        if self.playback_state == "completed":
            self.current_point_index = 0
            self.view.render_frame(self.plan.points[0], 0.0)
            self.view.restart_animation(
                self.plan,
                self.duration_s or 10.0,
                lambda progress: self._frame_at(self.plan, progress),
                self.on_animation_complete,
            )
        elif self.playback_state == "paused":
            self.view.resume_animation()
        else:
            return
        self.playback_state = "playing"
        self.view.set_playback_state("playing")

    # 対応要求: REQ-SIM-010, REQ-SIM-011, REQ-SIM-012
    def seek_to_point(self, point_index: int) -> None:
        """指定された較正点へ移動し、移動後は一時停止状態にする。

引数:
            point_index: 走査順における較正点インデックス。範囲外は端点へ補正する。

        動作:
            再生中の場合はタイマーを停止し、指定点を3画面と状態表示へ即時反映する。シーク後の再生状態は常に ``paused`` とする。

        戻り値:
            None

        対応要求:
            REQ-SIM-010, REQ-SIM-011, REQ-SIM-012
        """
        if self.plan is None or not self.plan.points:
            return
        if self.playback_state == "playing":
            self.view.pause_animation()
        index = max(0, min(int(round(point_index)), len(self.plan.points) - 1))
        self.current_point_index = index
        progress = index / max(1, len(self.plan.points) - 1)
        self.view.render_frame(self.plan.points[index], progress)
        self.playback_state = "paused"
        self.view.set_playback_state("paused")

    # 対応要求: REQ-SIM-009
    def restart_from_beginning(self) -> None:
        """完了後のシミュレーションを先頭から再生する。

再生完了状態でのみ再生再開処理を行う。先頭較正点を表示した後、約10秒のアニメーションを新たに開始する。

        戻り値:
            None

        対応要求:
            REQ-SIM-009
        """
        if self.playback_state == "completed":
            self.resume()

    # 対応要求: REQ-SIM-013
    def on_animation_complete(self) -> None:
        """最終較正点を保持し、自動ループせず完了状態へ遷移する。

最終フレーム到達時に呼び出され、最終較正点のインデックスを保持する。Viewへ完了状態を通知し、再生ボタン表示へ切り替える。

        戻り値:
            None

        対応要求:
            REQ-SIM-013
        """
        if self.plan is not None and self.plan.points:
            self.current_point_index = len(self.plan.points) - 1
        self.playback_state = "completed"
        self.view.show_final_state()
        self.view.set_playback_state("completed")

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
        REQ-SIM-002, REQ-SIM-003, REQ-SIM-004, REQ-SIM-005, REQ-SIM-006, REQ-SIM-007..016
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
        self.seek_slider = None
        self.playback_button = None
        self._playback_state = "idle"
        self._playback_callbacks = None
        self._updating_seek_slider = False
        self._animation_args = None

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
        """全較正点のL字形状を含む固定横面図範囲を算出する。"""
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

            elbow_x = pivot_x - ly * math.sin(theta)
            elbow_y = pivot_y + ly * math.cos(theta)
            tip_x = elbow_x + lx * math.cos(theta)
            tip_y = elbow_y + lx * math.sin(theta)
            xs.extend((pivot_x, elbow_x, tip_x))
            ys.extend((pivot_y, elbow_y, tip_y))

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

        status_axes.set_axis_on()
        status_axes.set_xticks([])
        status_axes.set_yticks([])
        status_axes.set_xlim(0.0, 1.0)
        status_axes.set_ylim(0.0, 1.0)
        self._status_artist = status_axes.text(0.02, 0.92, "", transform=status_axes.transAxes, va="top")
        # 旧プログレスバーの内部互換用Artist。表示は透明化し、実UIはSliderへ置換する。
        self._progress_artist = status_axes.plot([0.02, 0.02], [0.08, 0.08], linewidth=0, alpha=0.0)[0]
        slider_max = max(0, len(getattr(plan, "points", ())) - 1)
        self.seek_slider = Slider(
            ax=status_axes,
            label="",
            valmin=0,
            valmax=max(1, slider_max),
            valinit=0,
            valstep=1,
            color="tab:blue",
            initcolor="none",
            track_color="0.85",
        )
        self.seek_slider.valmax = slider_max
        # Matplotlibの版によりSliderのつまみ属性名が異なるため公開別名を設定する。
        self.seek_slider.handle = getattr(self.seek_slider, "handle", self.seek_slider._handle)
        self.seek_slider.handle.set_markersize(16)
        self.seek_slider.on_changed(self._on_seek)
        self.playback_button = Button(
            self.figure.add_axes((0.86, 0.08, 0.10, 0.08)),
            "▶",
            color="0.90",
            hovercolor="0.75",
        )
        self.playback_button.on_clicked(self._on_play_pause)

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
    def start_animation(
        self,
        plan: CalibrationPlan,
        duration_s: float,
        frame_provider,
        on_complete=None,
    ) -> None:
        """指定時間で全較正点を走査するMatplotlibアニメーションを開始する。

        引数:
            plan: 再生対象の較正計画。
            duration_s: シミュレーション全体の再生時間[s]。
            frame_provider: 正規化進捗から現在点を返す関数。
            on_complete: 最終フレーム到達時に呼び出すコールバック。

        対応要求:
            REQ-SIM-002, REQ-SIM-013
        """
        frame_count = max(2, round(duration_s * 1000.0 / self.FRAME_INTERVAL_MS) + 1)

        def update(frame_index: int):
            progress = frame_index / (frame_count - 1)
            point = frame_provider(progress)
            self.render_frame(point, progress)
            if frame_index == frame_count - 1:
                self.show_final_state()
                if on_complete is not None:
                    on_complete()
            return ()

        # animationをメンバーとして保持し、Figure表示後のGCによる停止を防止する。
        self._animation_args = (plan, duration_s, frame_provider, on_complete)
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
        self._update_seek_slider(point.point.index)
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
        total_points = len(getattr(self._plan, "points", ()))
        self.status_text = (
            f"Point {point.point.index + 1} / {total_points} / AoA {point.point.aoa:.2f} / AoS {point.point.aos:.2f} / "
            f"X {command.x:.2f} / Y {command.y:.2f} / Z {command.z:.2f} / A {command.a:.2f} / "
            f"{state_label} {state} / {progress_label} {progress * 100:.0f}%"
        )
        display_text = (
            f"Point {point.point.index + 1} / {total_points}\n"
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
        """Lx/LyのL字オフセットと実ピッチ姿勢を固定範囲の横面図へ描画する。

        ピッチ回転中心からLy方向へ延びた後、そこからピトー管軸方向へLxだけ
        延びるL字形状を剛体としてZ角で回転させる。Lx側線分の向きが実際の
        ピトー管軸方向を表す。

        引数:
            point: 現在表示する較正点評価結果。

        対応要求:
            REQ-SIM-003
        """
        axes = self.side_axes
        axes.clear()
        self._configure_side_axes()

        lx, ly = self._get_dimensions()
        theta = math.radians(point.command.z)
        pivot_x = point.command.x
        pivot_y = point.command.y

        # 基準姿勢のLyベクトル(0, Ly)とLxベクトル(Lx, 0)を同じZ角で回転する。
        elbow_x = pivot_x - ly * math.sin(theta)
        elbow_y = pivot_y + ly * math.cos(theta)
        tip_x = elbow_x + lx * math.cos(theta)
        tip_y = elbow_y + lx * math.sin(theta)

        ly_line = axes.plot([pivot_x, elbow_x], [pivot_y, elbow_y], linewidth=5)[0]
        body_color = ly_line.get_color()
        axes.plot([elbow_x, tip_x], [elbow_y, tip_y], linewidth=5, color=body_color)
        axes.scatter([pivot_x], [pivot_y], marker="o", s=55, color=body_color)

        # Lx側線分の末端だけに矢印を重ね、ピトー管軸方向を一意に示す。
        direction_x = tip_x - elbow_x
        direction_y = tip_y - elbow_y
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

        axes.text(
            0.02, 0.96,
            f"Z={point.command.z:.2f}°\nX={pivot_x:.2f} mm\nY={pivot_y:.2f} mm",
            transform=axes.transAxes,
            va="top",
        )

    # 対応要求: REQ-SIM-003
    def _draw_front_view(self, point: PointEvaluation) -> None:
        """ピトー管のロール方向を半径矢印で正面図へ描画する。

        反転時にも方向を一意に識別できるよう、中心から外周へ向かう矢印のみで
        ロール方向を表し、反対側まで延びる直径線や角度円弧、方向文字は描画しない。

        引数:
            point: 現在表示する較正点評価結果。

        対応要求:
            REQ-SIM-003
        """
        axes = self.front_axes
        axes.clear()
        self._configure_front_axes()

        radius = 1.0
        angle = math.radians(point.command.a)
        circle = plt.Circle((0.0, 0.0), radius, fill=False, linewidth=2, alpha=0.35)
        axes.add_patch(circle)
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        axes.annotate(
            "",
            xy=(dx, dy),
            xytext=(0.0, 0.0),
            arrowprops={
                "arrowstyle": "-|>",
                "linewidth": 5,
                "mutation_scale": 16,
            },
        )
        axes.plot([0.0], [0.0], marker="o", markersize=7)
        axes.text(0.02, 0.96, f"A={point.command.a:.2f}°", transform=axes.transAxes, va="top")

    # 対応要求: REQ-SIM-008, REQ-SIM-009, REQ-SIM-010, REQ-SIM-011, REQ-SIM-014, REQ-SIM-015, REQ-SIM-016
    def bind_playback_controls(self, pause_callback, resume_callback, seek_callback) -> None:
        """再生操作の通知先をControllerへ設定する。

引数:
            pause_callback: 一時停止操作を処理するControllerの呼出し可能オブジェクト。
            resume_callback: 再生操作を処理するControllerの呼出し可能オブジェクト。
            seek_callback: 較正点シークを処理するControllerの呼出し可能オブジェクト。

        対応要求:
            REQ-SIM-008, REQ-SIM-009, REQ-SIM-010
        """ self._playback_callbacks = (pause_callback, resume_callback, seek_callback)

    def set_playback_callbacks(self, pause_callback, resume_callback, seek_callback) -> None:
        """再生操作の通知先をControllerへ設定する。

SimulationControllerが利用する公開APIであり、内部のコールバック登録処理へ委譲する。

        引数:
            pause_callback: 一時停止処理。
            resume_callback: 再生処理。
            seek_callback: 較正点シーク処理。

        対応要求:
            REQ-SIM-008, REQ-SIM-009, REQ-SIM-010
        """ self.bind_playback_controls(pause_callback, resume_callback, seek_callback)

    def pause_animation(self) -> None:
        """Matplotlibアニメーションのタイマーを停止する。

描画済みの現在較正点を変更せず、FuncAnimationのイベントソースだけを停止する。

        対応要求:
            REQ-SIM-008, REQ-SIM-011
        """
        if self.animation is not None and self.animation.event_source is not None:
            self.animation.event_source.stop()

    def resume_animation(self) -> None:
        """一時停止中のMatplotlibアニメーションを再開する。

一時停止で停止したFuncAnimationのイベントソースを再開する。再生完了後の先頭からの再生は ``restart_animation`` が担当する。

        対応要求:
            REQ-SIM-009
        """
        if self.animation is not None and self.animation.event_source is not None:
            self.animation.event_source.start()

    def restart_animation(self, plan, duration_s, frame_provider, on_complete=None) -> None:
        """完了済みアニメーションを新しいフレーム列で先頭から再生する。

引数:
            plan: 再生対象の較正計画。
            duration_s: 全体の再生時間[s]。
            frame_provider: 正規化進捗から現在点を返す関数。
            on_complete: 最終フレーム到達時のコールバック。

        対応要求:
            REQ-SIM-009
        """ self.start_animation(plan, duration_s, frame_provider, on_complete)

    def set_playback_state(self, state: str) -> None:
        """再生状態を保持し、状態に応じてボタン表示を切り替える。

引数:
            state: ``playing``, ``paused`` または ``completed`` の再生状態。

        ボタン表示:
            ``playing`` では「Ⅱ」、それ以外では「▶」を表示する。

        対応要求:
            REQ-SIM-016
        """ self._playback_state = state
        if self.playback_button is None:
            return
        self.playback_button.label.set_text("Ⅱ" if state == "playing" else "▶")
        if self.figure is not None:
            self.figure.canvas.draw_idle()

    def _on_play_pause(self, _event) -> None:
        """再生/一時停止ボタンの押下をControllerへ通知する。

再生中はpause callback、それ以外はresume callbackを呼び出す。完了状態の再生処理はController側で先頭再生として扱う。

        引数:
            _event: Matplotlib Buttonが渡すクリックイベント。

        対応要求:
            REQ-SIM-008, REQ-SIM-009, REQ-SIM-016
        """
        if self._playback_callbacks is None:
            return
        pause_callback, resume_callback, _seek_callback = self._playback_callbacks
        if self._playback_state == "playing":
            pause_callback()
        else:
            resume_callback()

    def _on_seek(self, value) -> None:
        """シーク操作をControllerへ通知する。

引数:
            value: シークバーが示す較正点インデックス。小数は最も近い整数へ丸める。

        再生中の一時停止と、指定点への即時描画はControllerへ委譲する。内部同期によるシークバー更新時は再入を抑止する。

        対応要求:
            REQ-SIM-010, REQ-SIM-011, REQ-SIM-012
        """
        if self._updating_seek_slider or self._playback_callbacks is None:
            return
        _pause_callback, _resume_callback, seek_callback = self._playback_callbacks
        seek_callback(int(round(value)))

    def _update_seek_slider(self, point_index: int) -> None:
        """現在較正点へシークバーを同期する。

引数:
            point_index: 走査順における現在較正点インデックス。

        Controllerからの描画更新でSlider callbackが再帰的に発火しないよう、同期中フラグを使用する。

        対応要求:
            REQ-SIM-012, REQ-SIM-014
        """
        if self.seek_slider is None:
            return
        self._updating_seek_slider = True
        try:
            self.seek_slider.set_val(int(point_index))
        finally:
            self._updating_seek_slider = False

    def show_final_state(self) -> None:
        """再生終了後も最終較正状態を表示したままにする。

        対応要求:
            REQ-SIM-002, REQ-SIM-004, REQ-SIM-006, REQ-SIM-013
        """
        self.final_state_visible = True
