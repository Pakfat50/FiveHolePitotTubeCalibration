"""較正計画全体を構築するアプリケーションサービス。"""

from limits import LimitEvaluator
from models import AxisCommand, CalibrationPlan, CalibrationSettings, PointEvaluation
from positioning import PositionCompensator
from scan import ScanPlanner
from transform import AngleTransformer


class CalibrationService:
    """走査、座標変換、位置補正、可動範囲判定を統合する。

    生成するCalibrationPlanは、GUIの較正点マップ、シミュレーション、
    Gコード生成で共通利用する単一の計算結果とする。

    対応要求:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
        REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
        REQ-LIMIT-003
    """

    def __init__(self) -> None:
        """較正計画構築に使用するCoreサービスを生成する。"""
        self._scan_planner = ScanPlanner()
        self._angle_transformer = AngleTransformer()
        self._position_compensator = PositionCompensator()
        self._limit_evaluator = LimitEvaluator()

    # 対応要求: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    def build_plan(self, settings: CalibrationSettings) -> CalibrationPlan:
        """検証済み設定から走査順序を保持した較正計画全体を構築する。

        Args:
            settings: 入力検証に合格済みの較正設定。

        Returns:
            全PointEvaluation、X/Y最大逸脱量、および生成禁止状態を
            集約したCalibrationPlan。

        対応要求:
            REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
            REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
            REQ-LIMIT-003
        """
        # まずAoA/AoSの全較正点を確定する。以降の処理はこの順序を変えず、
        # 同じCalibrationPlanを表示・シミュレーション・Gコード生成へ渡す。
        scan_points = self._scan_planner.generate_points(settings)
        evaluations: list[PointEvaluation] = []

        # 前較正点のZ/Aを保持し、AngleTransformerへ渡すことで、走査順に沿って
        # ロール角のunwrapと等価解選択を連続的に行う。
        previous_angles: tuple[float, float] | None = None

        for point in scan_points:
            z, a = self._angle_transformer.transform(
                point.aoa,
                point.aos,
                previous_angles,
                settings.axis_limits,
            )

            # ピッチ回転による先端位置変化をX/Y並進で補正する。
            # ロールは長手軸周りの回転なのでXY補正計算には含めない。
            x, y = self._position_compensator.calculate_xy(
                z,
                settings.tip_offset_x,
                settings.tip_offset_y,
            )
            ideal_command = AxisCommand(x=x, y=y, z=z, a=a)

            # X/Yは必要なら飽和、Z/Aは値を変えずに範囲外だけを検出する。
            limit_result = self._limit_evaluator.evaluate(ideal_command, settings.axis_limits)

            # LimitEvaluatorは軸指令単体を扱うためpointを知らない。
            # ここで走査点と評価結果を結合し、CalibrationPlanの正式な点データとする。
            evaluation = PointEvaluation(
                point=point,
                ideal_command=limit_result.ideal_command,
                command=limit_result.command,
                x_saturated=limit_result.x_saturated,
                y_saturated=limit_result.y_saturated,
                x_deviation=limit_result.x_deviation,
                y_deviation=limit_result.y_deviation,
                rotational_error=limit_result.rotational_error,
            )
            evaluations.append(evaluation)
            previous_angles = (z, a)

        # XY警告では合成逸脱量を作らず、XとYを独立に最大値集約する。
        max_x_deviation = max((p.x_deviation for p in evaluations), default=0.0)
        max_y_deviation = max((p.y_deviation for p in evaluations), default=0.0)

        # Z/A範囲外が1点でも存在すれば計画全体を生成禁止とする。
        # XY飽和だけではこのフラグを立てない。
        has_generation_error = any(p.rotational_error for p in evaluations)

        return CalibrationPlan(
            settings=settings,
            points=evaluations,
            max_x_deviation=max_x_deviation,
            max_y_deviation=max_y_deviation,
            has_generation_error=has_generation_error,
        )
