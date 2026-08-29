"""較正計画生成サービスの単体テスト。

File: test_calibration_service.py
CalibrationService が点列生成・角度変換・XY補正・制限判定を統合して正しい CalibrationPlan を構築することを検証する。
Details: docs/test_specification.md の TEST-UNIT-060..065 に対応する。
"""

import unittest

from calibration_service import CalibrationService
from tests.test_support import make_limits, make_settings
from models import AxisRange


class TestCalibrationService(unittest.TestCase):
    """複数Core処理を統合した較正計画の整合性を確認する。"""

    def setUp(self):
        """各テストで独立した CalibrationService を生成する。"""
        self.service = CalibrationService()

    # TEST-UNIT-060
    # Requirements: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001
    def test_build_plan_creates_evaluation_for_every_point(self):
        """全較正点に対してPointEvaluationが生成されることを確認する。

        Test: TEST-UNIT-060: 2×3の格子設定から6件のplan.pointsを生成すること。
        Details: ScanPlanner以降の処理をCalibrationService経由で実行し最終評価件数を確認する。
        Verification rationale:
        入力点数の直積と最終PointEvaluation件数を比較するため、統合処理途中で点が欠落していないことを確認できる。
        See Also: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001
        """
        plan = self.service.build_plan(make_settings(aoa_points=2, aos_points=3))
        self.assertEqual(6, len(plan.points))

    # TEST-UNIT-061
    # Requirements: REQ-LIMIT-002
    def test_plan_aggregates_max_xy_deviation(self):
        """planの最大X/Y偏差が各点偏差の最大値と一致することを確認する。

        Test: TEST-UNIT-061: max_x_deviation/max_y_deviationがPointEvaluation群の最大偏差を保持すること。
        Details: X/Y可動範囲を狭めて飽和を発生させ、集約値を各点から再計算した最大値と比較する。
        Verification rationale:
        元データである全PointEvaluationから独立にmaxを算出して比較するため、集約値の取りこぼしや軸取り違えを検出できる。
        See Also: REQ-LIMIT-002
        """
        limits = make_limits(x=AxisRange(-0.1, 0.1), y=AxisRange(-0.1, 0.1))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertAlmostEqual(max(p.x_deviation for p in plan.points), plan.max_x_deviation)
        self.assertAlmostEqual(max(p.y_deviation for p in plan.points), plan.max_y_deviation)

    # TEST-UNIT-062
    # Requirements: REQ-LIMIT-003
    def test_any_rotational_error_blocks_generation(self):
        """1点でもZ/A範囲外があればplanが生成禁止状態になることを確認する。

        Test: TEST-UNIT-062: 狭いZ範囲でrotational_errorが発生し、has_generation_error=Trueとなること。
        Details: Z範囲を±1度へ狭め、点別エラーとplan集約エラーを同時に確認する。
        Verification rationale:
        点レベルの回転エラー存在とplanレベルの生成禁止フラグを対応付けて観測するため、any集約条件を直接検証できる。
        See Also: REQ-LIMIT-003
        """
        limits = make_limits(z=AxisRange(-1.0, 1.0))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(plan.has_generation_error)
        self.assertTrue(any(p.rotational_error for p in plan.points))

    # TEST-UNIT-063
    # Requirements: REQ-LIMIT-001, REQ-LIMIT-002
    def test_xy_saturation_alone_does_not_block_generation(self):
        """X/Y飽和だけではplanを生成禁止にしないことを確認する。

        Test: TEST-UNIT-063: X/Y飽和点が存在してもhas_generation_error=Falseであること。
        Details: X/Y可動範囲だけを極端に狭め、飽和の発生と生成可否を観測する。
        Verification rationale:
        並進警告が実際に発生する条件で生成禁止フラグが立たないことを確認するため、警告とエラーの分類を統合レベルで検証できる。
        See Also: REQ-LIMIT-001, REQ-LIMIT-002
        """
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(any(p.x_saturated or p.y_saturated for p in plan.points))
        self.assertFalse(plan.has_generation_error)

    # TEST-UNIT-064
    # Requirements: REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-004
    def test_serpentine_plan_keeps_scan_order_and_continuity(self):
        """蛇行走査順とロール角連続性がplan内で維持されることを確認する。

        Test: TEST-UNIT-064: AoS行が交互反転し、隣接点A角差が不要な180度超ジャンプを持たないこと。
        Details: 3×3蛇行planについてAoS順序と隣接A角差の両方を検証する。
        Verification rationale:
        点列順序とその順序を前提にした連続角を同じplanで観測するため、ScanPlannerとAngleTransformerの連携が成立していることを確認できる。
        See Also: REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-004
        """
        plan = self.service.build_plan(make_settings(aoa_points=3, aos_points=3, serpentine=True))
        rows = [[p.point.aos for p in plan.points[i:i+3]] for i in range(0, 9, 3)]
        self.assertEqual([[-10,0,10],[10,0,-10],[-10,0,10]], rows)
        for previous, current in zip(plan.points, plan.points[1:]):
            self.assertLessEqual(abs(current.command.a - previous.command.a), 180.0 + 1e-9)

    # TEST-UNIT-065
    # Requirements: REQ-POS-001, REQ-LIMIT-001
    def test_ideal_and_actual_commands_are_both_preserved(self):
        """X/Y飽和時に理想指令と実指令の両方が保持されることを確認する。

        Test: TEST-UNIT-065: 飽和点ではideal_commandとcommandのX/Yが異なること。
        Details: X/Y範囲を狭めて飽和点を取得し、飽和前後の座標タプルを比較する。
        Verification rationale:
        同一PointEvaluation内の理想値と適用値を直接比較するため、偏差算出に必要な飽和前情報が失われていないことを確認できる。
        See Also: REQ-POS-001, REQ-LIMIT-001
        """
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        saturated = next(p for p in plan.points if p.x_saturated or p.y_saturated)
        self.assertNotEqual((saturated.ideal_command.x, saturated.ideal_command.y),
                            (saturated.command.x, saturated.command.y))


if __name__ == "__main__":
    unittest.main()
