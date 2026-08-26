"""較正機構のシミュレーション制御および表示を行う。"""

import matplotlib.pyplot as plt

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

    # 対応要求: REQ-SIM-002
    def start(self, plan: CalibrationPlan, duration_s: float = 10.0) -> None:
        """実際のGコード保持時間を再現せずに再生を開始する。

        引数:
            plan: 共有較正計画。
            duration_s: 目標総再生時間。通常は約10秒。

        対応要求:
            REQ-SIM-001, REQ-SIM-002
        """
        # シミュレーション時間はGコードのhold_time_sとは独立に保持する。
        self.duration_s = duration_s
        self.view.initialize(plan)

        # GUI側のタイマー駆動に依存しない最小実装として、開始時に先頭点、
        # 終了時に最終点を描画する。フレーム選択規則は_frame_atへ集約する。
        if plan.points:
            self.view.render_frame(self._frame_at(plan, 0.0), 0.0)
            self.view.render_frame(self._frame_at(plan, 1.0), 1.0)
            self.view.show_final_state()

    # 対応要求: REQ-SIM-002
    def _frame_at(self, plan: CalibrationPlan, progress: float) -> PointEvaluation:
        """正規化進捗に対応する走査点を選択する。

        引数:
            plan: 走査順序に並んだ較正計画。
            progress: 0から1までの再生進捗。

        戻り値:
            再生位置に対応するPointEvaluation。

        対応要求:
            REQ-SIM-002
        """
        if not plan.points:
            raise ValueError("較正点が存在しません。")

        # 進捗を0～1へ制限し、走査順序の先頭を0、末尾を1として最近傍の
        # インデックスへ対応付ける。0.5は5点なら中央のindex=2となる。
        normalized = min(1.0, max(0.0, progress))
        index = round(normalized * (len(plan.points) - 1))
        return plan.points[index]


class SimulationView:
    """横面図・正面図と現在較正点情報を表示する。

    対応要求:
        REQ-SIM-003, REQ-SIM-004
    """

    def __init__(self) -> None:
        self.figure = None
        self.side_axes = None
        self.front_axes = None
        self.status_text = ""
        self.current_point_index = None
        self.final_state_visible = False

    # 対応要求: REQ-SIM-003
    def initialize(self, plan: CalibrationPlan) -> None:
        """横面図と正面図の抽象表示を同時に初期化する。

        引数:
            plan: 共有較正計画。

        対応要求:
            REQ-SIM-003
        """
        # 横面図と正面図を別Axesとして保持し、同じPointEvaluationを用いて
        # ピッチ/X/Yとロールを同期表示できる構造にする。
        self.figure = plt.figure()
        self.side_axes = self.figure.add_subplot(1, 2, 1)
        self.front_axes = self.figure.add_subplot(1, 2, 2)
        self.side_axes.set_title("横面図")
        self.front_axes.set_title("正面図")
        self.final_state_visible = False

    # 対応要求: REQ-SIM-003, REQ-SIM-004
    def render_frame(self, point: PointEvaluation, progress: float) -> None:
        """1フレームと必要な状態文字列を描画する。

        引数:
            point: 現在の評価済み較正点。
            progress: 正規化された再生進捗。

        対応要求:
            REQ-SIM-003, REQ-SIM-004
        """
        self.current_point_index = point.point.index
        state = "ZA範囲外" if point.rotational_error else (
            "XY飽和" if point.x_saturated or point.y_saturated else "正常"
        )

        # GUIがそのまま表示できるよう、要求される全情報を1つの状態文字列に集約する。
        self.status_text = (
            f"Point {point.point.index} / AoA {point.point.aoa} / AoS {point.point.aos} / "
            f"X {point.command.x} / Y {point.command.y} / Z {point.command.z} / A {point.command.a} / "
            f"状態 {state} / 進捗 {progress * 100:.0f}%"
        )

        if self.side_axes is not None:
            self.side_axes.set_xlabel(f"X={point.command.x}, Y={point.command.y}, Z={point.command.z}")
        if self.front_axes is not None:
            self.front_axes.set_xlabel(f"A={point.command.a}")

    def show_final_state(self) -> None:
        """再生終了後も最終較正状態を表示したままにする。

        対応要求:
            REQ-SIM-002, REQ-SIM-004
        """
        self.final_state_visible = True
