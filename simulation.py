"""較正機構のシミュレーション制御および表示を行う。"""

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
        raise NotImplementedError

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
        raise NotImplementedError


class SimulationView:
    """横面図・正面図と現在較正点情報を表示する。

    対応要求:
        REQ-SIM-003, REQ-SIM-004
    """

    # 対応要求: REQ-SIM-003
    def initialize(self, plan: CalibrationPlan) -> None:
        """横面図と正面図の抽象表示を同時に初期化する。

        引数:
            plan: 共有較正計画。

        対応要求:
            REQ-SIM-003
        """
        raise NotImplementedError

    # 対応要求: REQ-SIM-003, REQ-SIM-004
    def render_frame(self, point: PointEvaluation, progress: float) -> None:
        """1フレームと必要な状態文字列を描画する。

        引数:
            point: 現在の評価済み較正点。
            progress: 正規化された再生進捗。

        対応要求:
            REQ-SIM-003, REQ-SIM-004
        """
        raise NotImplementedError

    def show_final_state(self) -> None:
        """再生終了後も最終較正状態を表示したままにする。

        対応要求:
            REQ-SIM-002, REQ-SIM-004
        """
        raise NotImplementedError
