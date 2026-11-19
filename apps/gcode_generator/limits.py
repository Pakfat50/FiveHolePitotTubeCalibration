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

        Args:
            command: 理想X/Y/Z/A指令。
            limits: 軸可動範囲。

        Returns:
            理想指令を保持し、X/Yのみ必要に応じて飽和させ、Z/A範囲超過を
            フラグ化したPointEvaluation。較正点との対応付けはCalibrationServiceで行う。

        対応要求:
            REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
        """
        # 並進軸X/Yは範囲を超えても生成禁止にはせず、機械的に到達可能な
        # 端点へ飽和させる。同時に理想値との差を個別に保持する。
        x, x_saturated, x_deviation = self._saturate_translation(command.x, limits.x)
        y, y_saturated, y_deviation = self._saturate_translation(command.y, limits.y)

        # 回転軸Z/Aは角度を変更すると要求AoA/AoSそのものが変わるため、
        # 飽和させない。範囲外かどうかだけを検出し、元の指令値をそのまま保持する。
        z_in_range = self._rotation_in_range(command.z, limits.z)
        a_in_range = self._rotation_in_range(command.a, limits.a)
        rotational_error = not (z_in_range and a_in_range)

        actual_command = AxisCommand(x=x, y=y, z=command.z, a=command.a)

        # evaluate()は軸指令だけを評価するCore処理であり、どのCalibrationPointに
        # 属するかは知らない。pointは後段のCalibrationServiceが実点へ置き換える。
        return PointEvaluation(
            point=None,  # type: ignore[arg-type]
            ideal_command=command,
            command=actual_command,
            x_saturated=x_saturated,
            y_saturated=y_saturated,
            x_deviation=x_deviation,
            y_deviation=y_deviation,
            rotational_error=rotational_error,
        )

    # 対応要求: REQ-LIMIT-001, REQ-LIMIT-002
    def _saturate_translation(self, value: float, axis_range: AxisRange) -> tuple[float, bool, float]:
        """並進指令を可動範囲内へ飽和させ、飽和有無と絶対逸脱量を返す。

        Args:
            value: 理想並進指令。
            axis_range: 許容並進範囲。

        Returns:
            ``(実指令値, 飽和有無, 逸脱量)``のタプル。

        対応要求:
            REQ-LIMIT-001, REQ-LIMIT-002
        """
        # clamp(value, min, max)を明示的に実装し、端点は範囲内として扱う。
        saturated_value = min(max(value, axis_range.minimum), axis_range.maximum)
        saturated = saturated_value != value
        deviation = abs(value - saturated_value) if saturated else 0.0
        return saturated_value, saturated, deviation

    # 対応要求: REQ-LIMIT-003
    def _rotation_in_range(self, value: float, axis_range: AxisRange) -> bool:
        """回転軸指令を変更せず、可動範囲内かを判定する。

        Args:
            value: ZまたはA指令 [deg]
            axis_range: 許容角度範囲。

        Returns:
            端点を含めて範囲内の場合True。

        対応要求:
            REQ-LIMIT-003
        """
        return axis_range.minimum <= value <= axis_range.maximum
