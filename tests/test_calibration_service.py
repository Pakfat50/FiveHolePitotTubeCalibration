"""較正計画生成サービスの単体テスト。

File: test_calibration_service.py
CalibrationService が点列生成・角度変換・XY補正・制限判定を統合して正しい CalibrationPlan を構築することを検証する。
docs/test_specification.md の TEST-UNIT-060..065 に対応する。
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

    def test_build_plan_creates_evaluation_for_every_point(self):
        """TEST-UNIT-060

        テスト目的:
            全較正点に対してPointEvaluationが生成されることを確認する。

        テスト手順:

            1. AoAを2点、AoSを3点の格子として設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. 生成されたplan.pointsの件数を6件と比較する。

        パスクライテリア:
            plan.pointsが6件であり、すべての較正点に対応するPointEvaluationが生成されていること。

        検証根拠:
            入力点数の直積と最終PointEvaluation件数を比較するため、統合処理途中で点が欠落していないことを確認できる。
        """
        plan = self.service.build_plan(make_settings(aoa_points=2, aos_points=3))
        self.assertEqual(6, len(plan.points))

    def test_plan_aggregates_max_xy_deviation(self):
        """TEST-UNIT-061

        テスト目的:
            planの最大X/Y偏差が各点偏差の最大値と一致することを確認する。

        テスト手順:

            1. X/Y可動範囲をそれぞれ-0.1から0.1に設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. 全PointEvaluationからX/Y偏差の最大値を独立に算出する。
            4. 算出した最大値をplan.max_x_deviationおよびplan.max_y_deviationと比較する。

        パスクライテリア:
            全PointEvaluationから算出したX/Y偏差の最大値と、planが保持する最大X/Y偏差がそれぞれ一致すること。

        検証根拠:
            元データである全PointEvaluationから独立にmaxを算出して比較するため、集約値の取りこぼしや軸取り違えを検出できる。
        """
        limits = make_limits(x=AxisRange(-0.1, 0.1), y=AxisRange(-0.1, 0.1))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertAlmostEqual(max(p.x_deviation for p in plan.points), plan.max_x_deviation)
        self.assertAlmostEqual(max(p.y_deviation for p in plan.points), plan.max_y_deviation)

    def test_any_rotational_error_blocks_generation(self):
        """TEST-UNIT-062

        テスト目的:
            1点でもZ/A範囲外があればplanが生成禁止状態になることを確認する。

        テスト手順:

            1. Z軸可動範囲を-1.0から1.0に設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. 各PointEvaluationのrotational_errorを確認する。
            4. plan.has_generation_errorの値を確認する。

        パスクライテリア:
            rotational_errorが真のPointEvaluationが1件以上存在し、plan.has_generation_errorがTrueであること。

        検証根拠:
            点レベルの回転エラー存在とplanレベルの生成禁止フラグを対応付けて観測するため、any集約条件を直接検証できる。
        """
        limits = make_limits(z=AxisRange(-1.0, 1.0))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(plan.has_generation_error)
        self.assertTrue(any(p.rotational_error for p in plan.points))

    def test_xy_saturation_alone_does_not_block_generation(self):
        """TEST-UNIT-063

        テスト目的:
            X/Y飽和だけではplanを生成禁止にしないことを確認する。

        テスト手順:

            1. X/Y可動範囲をそれぞれ-0.01から0.01に設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. 各PointEvaluationのX/Y飽和状態を確認する。
            4. plan.has_generation_errorの値を確認する。

        パスクライテリア:
            XまたはYが飽和したPointEvaluationが1件以上存在し、plan.has_generation_errorがFalseであること。

        検証根拠:
            並進警告が発生する条件と生成禁止フラグを同時に判定するため、警告とエラーが正しく分類されていることを確認できる。
        """
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        self.assertTrue(any(p.x_saturated or p.y_saturated for p in plan.points))
        self.assertFalse(plan.has_generation_error)

    def test_serpentine_plan_keeps_scan_order_and_continuity(self):
        """TEST-UNIT-064

        テスト目的:
            蛇行走査順とロール角連続性がplan内で維持されることを確認する。

        テスト手順:

            1. AoAを3点、AoSを3点、蛇行走査を有効として設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. 各AoA行のAoS走査順が交互に反転していることを確認する。
            4. 隣接するPointEvaluation間のA角差を計算する。

        パスクライテリア:
            AoS行が期待する蛇行順序と一致し、すべての隣接点のA角差が180度以下であること。

        検証根拠:
            点列順序とその順序を前提にした連続角を同じplanで観測するため、ScanPlannerとAngleTransformerの連携が成立していることを確認できる。
        """
        plan = self.service.build_plan(make_settings(aoa_points=3, aos_points=3, serpentine=True))
        rows = [[p.point.aos for p in plan.points[i:i+3]] for i in range(0, 9, 3)]
        self.assertEqual([[-10,0,10],[10,0,-10],[-10,0,10]], rows)
        for previous, current in zip(plan.points, plan.points[1:]):
            self.assertLessEqual(abs(current.command.a - previous.command.a), 180.0 + 1e-9)

    def test_ideal_and_actual_commands_are_both_preserved(self):
        """TEST-UNIT-065

        テスト目的:
            X/Y飽和時に理想指令と実指令の両方が保持されることを確認する。

        テスト手順:

            1. X/Y可動範囲をそれぞれ-0.01から0.01に設定する。
            2. 設定をCalibrationServiceへ渡して較正計画を生成する。
            3. XまたはYが飽和したPointEvaluationを1件選択する。
            4. ideal_commandとcommandのX/Y座標を比較する。

        パスクライテリア:
            飽和したPointEvaluationにおいて、ideal_commandとcommandのX/Y座標が異なること。

        検証根拠:
            同一PointEvaluation内の理想値と適用値を比較するため、偏差算出に必要な飽和前情報が失われていないことを確認できる。
        """
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        plan = self.service.build_plan(make_settings(axis_limits=limits))
        saturated = next(p for p in plan.points if p.x_saturated or p.y_saturated)
        self.assertNotEqual((saturated.ideal_command.x, saturated.ideal_command.y),
                            (saturated.command.x, saturated.command.y))


if __name__ == "__main__":
    unittest.main()
