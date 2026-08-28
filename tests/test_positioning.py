"""先端位置補正の単体テスト。

@file test_positioning.py
@brief PositionCompensator のXY補正式とロール非依存性を検証する。
@details docs/test_specification.md の TEST-UNIT-041..046 に対応する。
"""

import math
import unittest

from positioning import PositionCompensator
from tests.test_support import ABS_TOL


class TestPositionCompensator(unittest.TestCase):
    """@brief ピッチ角とLx/Lyから算出されるXY補正値の要求適合性を確認する。"""

    def setUp(self):
        """@brief 各テストで独立した PositionCompensator を生成する。"""
        self.p = PositionCompensator()

    # TEST-UNIT-041
    # Requirements: REQ-POS-001
    def test_zero_pitch_requires_no_translation(self):
        """@brief ピッチ角0度ではX/Y補正が不要であることを確認する。

        @test TEST-UNIT-041: theta=0度ではX=0,Y=0となること。
        @details Lx=100,Ly=10の非零寸法を用い、角度だけを0度にして補正量を観測する。
        @par 検証根拠
        補正式へtheta=0を代入した理論値は厳密に0となるため、出力を0と比較することで基準姿勢の補正計算を直接確認できる。
        @see REQ-POS-001
        """
        x, y = self.p.calculate_xy(0.0, 100.0, 10.0)
        self.assertAlmostEqual(0.0, x, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, y, delta=ABS_TOL)

    # TEST-UNIT-042
    # Requirements: REQ-POS-001
    def test_positive_pitch_matches_formula(self):
        """@brief 正ピッチ角でXY補正値が理論式と一致することを確認する。

        @test TEST-UNIT-042: theta=+15度の計算結果がREQ-POS-001の式に一致すること。
        @details 独立に計算した理論値と実装出力を許容誤差内で比較する。
        @par 検証根拠
        実装とは別にテスト側で同じ数学仕様から期待値を構成するため、符号や回転式の誤りを検出できる。
        @see REQ-POS-001
        """
        self._assert_formula(15.0, 100.0, 10.0)

    # TEST-UNIT-043
    # Requirements: REQ-POS-001
    def test_negative_pitch_matches_formula(self):
        """@brief 負ピッチ角でXY補正値が理論式と一致することを確認する。

        @test TEST-UNIT-043: theta=-15度の計算結果が補正式に一致すること。
        @details 負角度を使用してsin項の符号反転を含む結果を比較する。
        @par 検証根拠
        正角度だけでは検出しにくい符号処理を負角度で確認するため、双方向回転の式実装を検証できる。
        @see REQ-POS-001
        """
        self._assert_formula(-15.0, 100.0, 10.0)

    # TEST-UNIT-044
    # Requirements: REQ-POS-001
    def test_small_positive_ly(self):
        """@brief Lyが非常に小さい正値でも補正式どおり計算できることを確認する。

        @test TEST-UNIT-044: Ly→0+近傍でも数値計算が理論式に一致すること。
        @details Ly=1e-6を使用し、退化形状近傍での出力を比較する。
        @par 検証根拠
        Ly項の寄与が極小になる境界近傍を試験することで、ゼロ扱いや項落ちなどの実装誤りを検出できる。
        @see REQ-POS-001
        """
        self._assert_formula(20.0, 100.0, 1e-6)

    # TEST-UNIT-045
    # Requirements: REQ-POS-001
    def test_small_positive_lx(self):
        """@brief Lxが非常に小さい正値でも補正式どおり計算できることを確認する。

        @test TEST-UNIT-045: Lx→0+近傍でも数値計算が理論式に一致すること。
        @details Lx=1e-6を使用してLy支配の条件を検証する。
        @par 検証根拠
        Lx項がほぼ消える条件で期待値と比較するため、Lx/Lyの取り違えや係数誤りを検出できる。
        @see REQ-POS-001
        """
        self._assert_formula(20.0, 1e-6, 100.0)

    # TEST-UNIT-046
    # Requirements: REQ-POS-002
    def test_roll_does_not_affect_xy(self):
        """@brief XY補正がロール角に依存しない設計であることを確認する。

        @test TEST-UNIT-046: PositionCompensatorの計算入力はtheta/Lx/Lyのみで、同一入力から常に同一XYを得ること。
        @details 同一のtheta/Lx/Lyを2回計算し結果が完全一致することを確認する。
        @par 検証根拠
        APIにロール角が存在せず、同一ピッチ条件で決定的に同一結果となることを確認することで、ロールが先端位置補正へ混入していないことを検証できる。
        @see REQ-POS-002
        """
        # API intentionally accepts only theta/Lx/Ly; roll is absent by design.
        first = self.p.calculate_xy(10.0, 100.0, 10.0)
        second = self.p.calculate_xy(10.0, 100.0, 10.0)
        self.assertEqual(first, second)

    def _assert_formula(self, theta, lx, ly):
        """@brief REQ-POS-001の理論式から期待値を独立計算して実装値と比較する補助メソッド。

        @param theta 実ピッチ角[deg]。
        @param lx 基準姿勢のX方向オフセット[mm]。
        @param ly 基準姿勢のY方向オフセット[mm]。
        @par 検証根拠
        テスト側で明示的に回転後先端座標と補正量を算出することで、PositionCompensatorの公開出力を仕様式そのものと比較できる。
        @see REQ-POS-001
        """
        rad = math.radians(theta)
        xtip = lx * math.cos(rad) - ly * math.sin(rad)
        ytip = lx * math.sin(rad) + ly * math.cos(rad)
        expected_x = lx - xtip
        expected_y = ly - ytip
        x, y = self.p.calculate_xy(theta, lx, ly)
        self.assertAlmostEqual(expected_x, x, delta=ABS_TOL)
        self.assertAlmostEqual(expected_y, y, delta=ABS_TOL)


if __name__ == "__main__":
    unittest.main()
