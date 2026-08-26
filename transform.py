"""AoA/AoSを実機構のZ/A角へ変換する。"""

from models import AxisLimits


class AngleTransformer:
    """要求された流れ角を実ピッチ／実ロール指令へ変換する。

    機構はピッチ回転後にピトー管軸周りのロール回転を行うものとして扱う。
    等価解は可動範囲と前較正点からの連続性を考慮して選択する。

    対応要求:
        REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    """

    # 対応要求: REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    def transform(self, aoa: float, aos: float, previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """1つのAoA/AoS点から実ピッチZと実ロールAを算出する。

        引数:
            aoa: 要求AoA [deg]。
            aos: 要求AoS [deg]。
            previous: 前回選択した``(z, a)``指令。先頭点ではNone。
            limits: 等価解選択に使用する軸可動範囲。

        戻り値:
            選択した``(z, a)``角度 [deg]。

        対応要求:
            REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
        """
        raise NotImplementedError

    # 対応要求: REQ-TRANS-002
    def _generate_equivalent_solutions(self, theta: float, phi: float) -> list[tuple[float, float]]:
        """同一の流れ姿勢を表す機構角度の候補解を生成する。

        引数:
            theta: 基本ピッチ解 [deg]。
            phi: 基本ロール解 [deg]。

        戻り値:
            等価な``(z, a)``候補解。

        対応要求:
            REQ-TRANS-002
        """
        raise NotImplementedError

    # 対応要求: REQ-TRANS-003
    def _select_solution(self, candidates: list[tuple[float, float]], previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """可動範囲、連続性、移動量、|roll|の優先順位で候補を選択する。

        引数:
            candidates: 等価な角度候補。
            previous: 前回選択した指令。先頭点ではNone。
            limits: 許容Z/A範囲。

        戻り値:
            選択した``(z, a)``候補。

        対応要求:
            REQ-TRANS-003
        """
        raise NotImplementedError

    # 対応要求: REQ-TRANS-004
    def _unwrap_angle(self, angle: float, previous: float | None) -> float:
        """前回ロール角に最も近い等価角へunwrapする。

        引数:
            angle: 現在のロール角 [deg]。
            previous: 前回ロール角 [deg]。先頭点ではNone。

        戻り値:
            不要な±360 degジャンプを避けた等価角。

        対応要求:
            REQ-TRANS-004
        """
        raise NotImplementedError
