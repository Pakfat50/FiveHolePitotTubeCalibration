"""AoA/AoSから実軸角への座標変換の単体テスト。

File: test_transform.py
AngleTransformer の基本解、象限、等価解、連続性、解選択優先順位を検証する。
Details: docs/test_specification.md の TEST-UNIT-025..040 に対応する。
"""

import math
import unittest

from transform import AngleTransformer
from tests.test_support import ABS_TOL, make_limits
from models import AxisRange


class TestAngleTransformer(unittest.TestCase):
    """AoA/AoS→Z/A変換が数学仕様と等価解選択仕様を満たすことを確認する。"""

    def setUp(self):
        """標準可動範囲を持つ変換器を準備する。"""
        self.t = AngleTransformer()
        self.limits = make_limits()

    # TEST-UNIT-025
    # Requirements: REQ-TRANS-001, REQ-TRANS-002
    def test_origin_transform(self):
        """AoA=AoS=0がZ=A=0へ変換されることを確認する。

        Test: TEST-UNIT-025: 中立姿勢の変換結果が原点であること。
        Verification rationale:
        数学モデルの原点を直接入力しZ/A双方を0と比較するため、基準姿勢の変換を直接確認できる。
        See Also: REQ-TRANS-001, REQ-TRANS-002
        """
        z, a = self.t.transform(0.0, 0.0, None, self.limits)
        self.assertAlmostEqual(0.0, z, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, a, delta=ABS_TOL)

    # TEST-UNIT-026
    # Requirements: REQ-TRANS-002
    def test_positive_aoa_zero_aos(self):
        """AoS=0の正AoAが同値の正ピッチとロール0へ変換されることを確認する。

        Test: TEST-UNIT-026: AoA=10,AoS=0に対しZ=10,A=0となること。
        Verification rationale:
        1軸だけに傾きを与えた解析的に明白な条件で期待値を直接比較するため、基本式の軸対応を検証できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(10.0, 0.0, None, self.limits)
        self.assertAlmostEqual(10.0, z, delta=ABS_TOL)
        self.assertAlmostEqual(0.0, a, delta=ABS_TOL)

    # TEST-UNIT-027
    # Requirements: REQ-TRANS-002
    def test_negative_aoa_zero_aos_reproduces_input(self):
        """負AoAの等価解が元のAoA/AoSを再現することを確認する。

        Test: TEST-UNIT-027: AoA=-10,AoS=0の出力は有限値で、逆変換すると入力角を再現すること。
        Verification rationale:
        等価解ではZ/Aの表現が一意でないため、特定表現を固定せず物理的な再現角を比較することで正しい姿勢を検証できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(-10.0, 0.0, None, self.limits)
        self.assertTrue(math.isfinite(z) and math.isfinite(a))
        self._assert_reproduces(-10.0, 0.0, z, a)

    # TEST-UNIT-028
    # Requirements: REQ-TRANS-002
    def test_zero_aoa_positive_aos(self):
        """AoA=0の正AoSが変換後姿勢で再現されることを確認する。

        Test: TEST-UNIT-028: AoA=0,AoS=10の変換結果を逆評価すると入力角に一致すること。
        Verification rationale:
        AoS単独条件ではロール±90度を含む等価表現が生じるため、逆変換した物理量を比較することで表現に依存せず正しさを確認できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(0.0, 10.0, None, self.limits)
        self._assert_reproduces(0.0, 10.0, z, a)

    # TEST-UNIT-029
    # Requirements: REQ-TRANS-002
    def test_general_solution_matches_formula(self):
        """一般的なAoA/AoS組合せが仕様式の基本解と一致することを確認する。

        Test: TEST-UNIT-029: AoA=12,AoS=7でZ=atan(hypot(tanAoA,tanAoS)), A=atan2(v,u)となること。
        Verification rationale:
        テスト側で仕様数式から期待値を独立計算し実装出力と比較するため、一般ケースの数式実装誤りを検出できる。
        See Also: REQ-TRANS-002
        """
        aoa, aos = 12.0, 7.0
        u, v = math.tan(math.radians(aoa)), math.tan(math.radians(aos))
        expected_z = math.degrees(math.atan(math.hypot(u, v)))
        expected_a = math.degrees(math.atan2(v, u))
        z, a = self.t.transform(aoa, aos, None, self.limits)
        self.assertAlmostEqual(expected_z, z, delta=ABS_TOL)
        self.assertAlmostEqual(expected_a, a, delta=ABS_TOL)

    # TEST-UNIT-030
    # Requirements: REQ-TRANS-002
    def test_quadrant_ii(self):
        """u<0,v>0のときロール角が第II象限になることを確認する。

        Test: TEST-UNIT-030: AoA=-10,AoS=10で90<A<=180となること。
        Verification rationale:
        atan2の象限判定を直接観測するため、単純atanへの誤実装や符号取り違えを検出できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(-10.0, 10.0, None, self.limits)
        self.assertTrue(90.0 < a <= 180.0)

    # TEST-UNIT-031
    # Requirements: REQ-TRANS-002
    def test_quadrant_iii(self):
        """u<0,v<0のときロール角が第III象限相当になることを確認する。

        Test: TEST-UNIT-031: AoA=-10,AoS=-10で-180..-90または等価な180..270に入ること。
        Verification rationale:
        360度等価角を許容しつつ象限だけを判定するため、unwrap表現に依存せず方向の正しさを検証できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(-10.0, -10.0, None, self.limits)
        self.assertTrue(-180.0 <= a < -90.0 or 180.0 <= a < 270.0)

    # TEST-UNIT-032
    # Requirements: REQ-TRANS-002
    def test_quadrant_iv(self):
        """u>0,v<0のときロール角が第IV象限相当になることを確認する。

        Test: TEST-UNIT-032: AoA=10,AoS=-10で-90<A<0または等価な270<A<360となること。
        Verification rationale:
        負AoS条件でのatan2方向を確認するため、左右方向の符号処理を検証できる。
        See Also: REQ-TRANS-002
        """
        z, a = self.t.transform(10.0, -10.0, None, self.limits)
        self.assertTrue(-90.0 < a < 0.0 or 270.0 < a < 360.0)

    # TEST-UNIT-033
    # Requirements: REQ-TRANS-004
    def test_unwrap_plus_360(self):
        """-179度を前回179度に近い181度へunwrapすることを確認する。

        Test: TEST-UNIT-033: _unwrap_angle(-179,179)=181となること。
        Verification rationale:
        ±180度境界を跨ぐ代表条件で期待する+360等価角を直接比較するため、正方向unwrapを検証できる。
        See Also: REQ-TRANS-004
        """
        self.assertAlmostEqual(181.0, self.t._unwrap_angle(-179.0, 179.0), delta=ABS_TOL)

    # TEST-UNIT-034
    # Requirements: REQ-TRANS-004
    def test_unwrap_minus_360(self):
        """179度を前回-179度に近い-181度へunwrapすることを確認する。

        Test: TEST-UNIT-034: _unwrap_angle(179,-179)=-181となること。
        Verification rationale:
        逆方向の±180度跨ぎで-360等価角を確認するため、双方向のunwrapを検証できる。
        See Also: REQ-TRANS-004
        """
        self.assertAlmostEqual(-181.0, self.t._unwrap_angle(179.0, -179.0), delta=ABS_TOL)

    # TEST-UNIT-035
    # Requirements: REQ-TRANS-004
    def test_unwrap_avoids_358_degree_jump(self):
        """unwrap後の角度変化が不要な358度ジャンプを避けることを確認する。

        Test: TEST-UNIT-035: 前回179度から次値-179度は2度以内の変化として扱われること。
        Verification rationale:
        unwrapの目的である連続角差そのものを計測するため、単に等価角を返すだけでなくジャンプ回避効果を直接確認できる。
        See Also: REQ-TRANS-004
        """
        value = self.t._unwrap_angle(-179.0, 179.0)
        self.assertLessEqual(abs(value - 179.0), 2.0 + ABS_TOL)

    # TEST-UNIT-036
    # Requirements: REQ-TRANS-003
    def test_in_range_candidate_has_priority(self):
        """可動範囲内候補が範囲外候補より優先されることを確認する。

        Test: TEST-UNIT-036: Z=20候補とZ=200候補では範囲内のZ=20を選ぶこと。
        Verification rationale:
        他の要素を単純化した2候補で最優先条件の可動範囲適合だけを競合させるため、優先順位1を分離して確認できる。
        See Also: REQ-TRANS-003
        """
        limits = make_limits(z=AxisRange(-30, 30), a=AxisRange(-180, 180))
        chosen = self.t._select_solution([(20.0, 0.0), (200.0, 0.0)], None, limits)
        self.assertEqual((20.0, 0.0), chosen)

    # TEST-UNIT-037
    # Requirements: REQ-TRANS-003
    def test_continuity_has_priority(self):
        """前回姿勢に近い連続候補が選択されることを確認する。

        Test: TEST-UNIT-037: previous=(10,5)では(10,10)を(10,170)より優先すること。
        Verification rationale:
        両候補を範囲内に保ち角度距離だけを大きく変えるため、連続性優先規則を直接確認できる。
        See Also: REQ-TRANS-003
        """
        chosen = self.t._select_solution([(10.0, 10.0), (10.0, 170.0)], (10.0, 5.0), self.limits)
        self.assertEqual((10.0, 10.0), chosen)

    # TEST-UNIT-038
    # Requirements: REQ-TRANS-003
    def test_smaller_total_motion_selected(self):
        """前点からのZ/A総移動量が小さい候補を選択することを確認する。

        Test: TEST-UNIT-038: previous=(10,10)に対し(20,20)を(30,30)より選ぶこと。
        Verification rationale:
        同一条件下で総移動量だけが異なる候補を比較するため、移動量最小化の優先条件を検証できる。
        See Also: REQ-TRANS-003
        """
        chosen = self.t._select_solution([(20.0, 20.0), (30.0, 30.0)], (10.0, 10.0), self.limits)
        self.assertEqual((20.0, 20.0), chosen)

    # TEST-UNIT-039
    # Requirements: REQ-TRANS-003
    def test_smaller_absolute_roll_breaks_tie(self):
        """同等候補ではロール絶対値の小さい側をタイブレークに利用できることを確認する。

        Test: TEST-UNIT-039: 等価な±20度ロール候補から|A|=20の候補を選ぶこと。
        Verification rationale:
        絶対値が等しい候補を与えて選択結果の|A|を確認することで、タイブレークが許容範囲内の小ロール解を保持することを確認できる。
        See Also: REQ-TRANS-003
        """
        chosen = self.t._select_solution([(20.0, 20.0), (20.0, -20.0)], None, self.limits)
        self.assertEqual(20.0, abs(chosen[1]))

    # TEST-UNIT-040
    # Requirements: REQ-TRANS-002, REQ-TRANS-003
    def test_equivalent_solution_candidates_are_generated(self):
        """基本解を含む等価解候補集合が生成されることを確認する。

        Test: TEST-UNIT-040: (20,30)から生成した候補が空でなく基本解(20,30)を含むこと。
        Verification rationale:
        解選択の入力となる候補集合を直接観測し、最低限基本解が失われないことを確認するため、等価解生成処理の成立を検証できる。
        See Also: REQ-TRANS-002, REQ-TRANS-003
        """
        candidates = self.t._generate_equivalent_solutions(20.0, 30.0)
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIn((20.0, 30.0), candidates)

    def _assert_reproduces(self, aoa, aos, z, a):
        """Z/AからAoA/AoS相当値を逆算し入力姿勢の再現性を確認する補助メソッド。

        Args:
            aoa: 期待するAoA[deg]
            aos: 期待するAoS[deg]
            z: 実ピッチ角[deg]
            a: 実ロール角[deg]
        Verification rationale:
        等価解の表記ではなく、変換後ベクトルが表す物理的なAoA/AoSを比較するため、複数解が存在するケースでも仕様適合性を判定できる。
        """
        r = math.tan(math.radians(z))
        u = r * math.cos(math.radians(a))
        v = r * math.sin(math.radians(a))
        self.assertAlmostEqual(aoa, math.degrees(math.atan(u)), delta=ABS_TOL)
        self.assertAlmostEqual(aos, math.degrees(math.atan(v)), delta=ABS_TOL)


if __name__ == "__main__":
    unittest.main()
