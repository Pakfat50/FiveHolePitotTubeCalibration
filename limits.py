"""軸可動範囲の評価とX/Y飽和処理を行う。"""

from models import AxisCommand, AxisLimits, AxisRange, PointEvaluation


class LimitEvaluator:
    """並進軸を飽和させ、回転軸の範囲超過を検出する。

    対応要求:
        REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    """

    # 対応要求: REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    def evaluate(self, command: AxisCommand, limits: AxisLimits) -> PointEvaluation:
        """1つの理想軸指令を設定済みの全軸可動範囲に対して評価する。

        引数:
            command: 理想X/Y/Z/A指令。
            limits: 軸可動範囲。

        戻り値:
            理想指令を保持し、X/Yのみ必要に応じて飽和させ、Z/A範囲超過を
            フラグ化したPointEvaluation。

        対応要求:
            REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
        """
        raise NotImplementedError

    # 対応要求: REQ-LIMIT-001, REQ-LIMIT-002
    def _saturate_translation(self, value: float, axis_range: AxisRange) -> tuple[float, bool, float]:
        """並進指令を可動範囲内へ飽和させ、飽和有無と絶対逸脱量を返す。

        引数:
            value: 理想並進指令。
            axis_range: 許容並進範囲。

        戻り値:
            ``(実指令値, 飽和有無, 逸脱量)``のタプル。

        対応要求:
            REQ-LIMIT-001, REQ-LIMIT-002
        """
        raise NotImplementedError

    # 対応要求: REQ-LIMIT-003
    def _rotation_in_range(self, value: float, axis_range: AxisRange) -> bool:
        """回転軸指令を変更せず、可動範囲内かを判定する。

        引数:
            value: ZまたはA指令 [deg]。
            axis_range: 許容角度範囲。

        戻り値:
            端点を含めて範囲内の場合True。

        対応要求:
            REQ-LIMIT-003
        """
        raise NotImplementedError
