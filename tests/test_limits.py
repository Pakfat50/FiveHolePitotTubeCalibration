"""軸可動範囲判定の単体テスト。

File: test_limits.py
LimitEvaluator のX/Y飽和、偏差量、Z/A範囲エラーを検証する。
Details:
    docs/test_specification.md の TEST-UNIT-047..059 に対応する。
"""

import unittest

from limits import LimitEvaluator
from models import AxisCommand
from tests.test_support import ABS_TOL, make_limits


class TestLimitEvaluator(unittest.TestCase):
    """@brief 軸種別ごとの可動範囲処理が要求仕様どおり異なることを確認する。"""

    def setUp(self):
        """@brief 各テストで標準可動範囲を持つ評価器を準備する。"""
        self.e = LimitEvaluator()
        self.limits = make_limits()

    def _eval(self, **kwargs):
        """@brief 指定軸だけを変更した AxisCommand を評価する補助メソッド。

        Details:
            未指定軸を0に固定することで、対象軸の範囲処理を他軸から分離して観測する。
        """
            values = {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0}
            values.update(kwargs)
            return self.e.evaluate(AxisCommand(**values), self.limits)

    # TEST-UNIT-047
    # Requirements: REQ-LIMIT-001, REQ-VALID-003
    def test_all_axes_in_range(self):
        """@brief 全軸が範囲内なら飽和・回転エラーが発生しないことを確認する。

        Test:
            TEST-UNIT-047: 正常指令ではx/y_saturated=Falseかつrotational_error=Falseであること。
        Verification rationale:
            全軸0という明確な範囲内指令の評価結果を直接確認するため、正常系で誤警告・誤エラーがないことを判定できる。
        See Also:
            REQ-LIMIT-001, REQ-VALID-003
        """
        r = self._eval()
        self.assertFalse(r.x_saturated or r.y_saturated or r.rotational_error)

    # TEST-UNIT-048
    # Requirements: REQ-LIMIT-001
    def test_x_above_max_saturates(self):
        """@brief X上限超過時に上限へ飽和することを確認する。

        Test:
            TEST-UNIT-048: X=1200に対し指令値1000、x_saturated=Trueとなること。
        Verification rationale:
            上限を200超える入力に対し、飽和後値と飽和フラグを同時確認するため、値のクランプと状態通知の両方を検証できる。
        See Also:
            REQ-LIMIT-001
        """
        r = self._eval(x=1200.0)
        self.assertEqual(1000.0, r.command.x); self.assertTrue(r.x_saturated)

    # TEST-UNIT-049
    # Requirements: REQ-LIMIT-001
    def test_x_below_min_saturates(self):
        """@brief X下限超過時に下限へ飽和することを確認する。

        Test:
            TEST-UNIT-049: X=-1200に対し指令値-1000となること。
        Verification rationale:
            下限側の超過入力と飽和値を直接比較するため、上限側とは独立に負方向のクランプを確認できる。
        See Also:
            REQ-LIMIT-001
        """
        self.assertEqual(-1000.0, self._eval(x=-1200.0).command.x)

    # TEST-UNIT-050
    # Requirements: REQ-LIMIT-001
    def test_y_above_max_saturates(self):
        """@brief Y上限超過時に上限へ飽和することを確認する。

        Test:
            TEST-UNIT-050: Y=1200に対し指令値1000となること。
        Verification rationale:
            Y軸だけを上限超過させて出力値を観測するため、Y軸の上限飽和処理を分離して確認できる。
        See Also:
            REQ-LIMIT-001
        """
        self.assertEqual(1000.0, self._eval(y=1200.0).command.y)

    # TEST-UNIT-051
    # Requirements: REQ-LIMIT-001
    def test_y_below_min_saturates(self):
        """@brief Y下限超過時に下限へ飽和することを確認する。

        Test:
            TEST-UNIT-051: Y=-1200に対し指令値-1000となること。
        Verification rationale:
            Y軸負方向の範囲外入力を直接与えるため、Y下限側の飽和を確認できる。
        See Also:
            REQ-LIMIT-001
        """
        self.assertEqual(-1000.0, self._eval(y=-1200.0).command.y)

    # TEST-UNIT-052
    # Requirements: REQ-LIMIT-002
    def test_x_deviation(self):
        """@brief X飽和時の理想値からの逸脱量を確認する。

        Test:
            TEST-UNIT-052: X=1200、上限1000ではx_deviation=200であること。
        Verification rationale:
            入力値と飽和値の差が既知の条件で偏差出力を比較するため、警告に使用するX偏差計算を直接検証できる。
        See Also:
            REQ-LIMIT-002
        """
        self.assertAlmostEqual(200.0, self._eval(x=1200.0).x_deviation, delta=ABS_TOL)

    # TEST-UNIT-053
    # Requirements: REQ-LIMIT-002
    def test_y_deviation(self):
        """@brief Y飽和時の理想値からの逸脱量を確認する。

        Test:
            TEST-UNIT-053: Y=-1200、下限-1000ではy_deviation=200であること。
        Verification rationale:
            負方向飽和でも偏差を正の距離として返すことを既知差分200で確認できる。
        See Also:
            REQ-LIMIT-002
        """
        self.assertAlmostEqual(200.0, self._eval(y=-1200.0).y_deviation, delta=ABS_TOL)

    # TEST-UNIT-054
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_z_above_max_not_clamped(self):
        """@brief Z上限超過時に値を飽和せず回転エラーとすることを確認する。

        Test:
            TEST-UNIT-054: Z=200を保持したままrotational_error=Trueとなること。
        Verification rationale:
            出力Zが入力値のまま残ることとエラーフラグを同時確認するため、回転軸を飽和させない仕様を直接検証できる。
        See Also:
            REQ-LIMIT-003, REQ-VALID-003
        """
        r = self._eval(z=200.0)
        self.assertEqual(200.0, r.command.z); self.assertTrue(r.rotational_error)

    # TEST-UNIT-055
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_z_below_min_not_clamped(self):
        """@brief Z下限超過時にも値を保持して回転エラーとすることを確認する。

        Test:
            TEST-UNIT-055: Z=-200を保持したままrotational_error=Trueとなること。
        Verification rationale:
            負方向範囲外でも非飽和とエラー判定を同時観測するため、Z軸両側の仕様を確認できる。
        See Also:
            REQ-LIMIT-003, REQ-VALID-003
        """
        r = self._eval(z=-200.0)
        self.assertEqual(-200.0, r.command.z); self.assertTrue(r.rotational_error)

    # TEST-UNIT-056
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_a_above_max_not_clamped(self):
        """@brief A上限超過時に値を飽和せず回転エラーとすることを確認する。

        Test:
            TEST-UNIT-056: A=800を保持したままrotational_error=Trueとなること。
        Verification rationale:
            ロール軸の大きな上限超過で値保持とエラーを確認するため、A軸の非飽和規則を検証できる。
        See Also:
            REQ-LIMIT-003, REQ-VALID-003
        """
        r = self._eval(a=800.0)
        self.assertEqual(800.0, r.command.a); self.assertTrue(r.rotational_error)

    # TEST-UNIT-057
    # Requirements: REQ-LIMIT-003, REQ-VALID-003
    def test_a_below_min_not_clamped(self):
        """@brief A下限超過時に値を飽和せず回転エラーとすることを確認する。

        Test:
            TEST-UNIT-057: A=-800を保持したままrotational_error=Trueとなること。
        Verification rationale:
            A軸負方向でも入力値保持とエラー発生を直接確認するため、両側範囲超過処理を検証できる。
        See Also:
            REQ-LIMIT-003, REQ-VALID-003
        """
        r = self._eval(a=-800.0)
        self.assertEqual(-800.0, r.command.a); self.assertTrue(r.rotational_error)

    # TEST-UNIT-058
    # Requirements: REQ-LIMIT-001, REQ-LIMIT-003
    def test_xy_only_overrange_is_not_generation_error(self):
        """@brief X/Yだけの範囲超過では生成禁止エラーにならないことを確認する。

        Test:
            TEST-UNIT-058: X/Y飽和が同時発生してもrotational_error=Falseであること。
        Verification rationale:
            並進軸2軸を同時に範囲外へし、飽和フラグと回転エラーなしを確認することで、警告と生成禁止の分類を直接検証できる。
        See Also:
            REQ-LIMIT-001, REQ-LIMIT-003
        """
        r = self._eval(x=1200, y=-1200)
        self.assertTrue(r.x_saturated and r.y_saturated); self.assertFalse(r.rotational_error)

    # TEST-UNIT-059
    # Requirements: REQ-LIMIT-003
    def test_translation_and_rotation_overrange_combined(self):
        """@brief 並進軸と回転軸が同時範囲外でも各軸規則が独立適用されることを確認する。

        Test:
            TEST-UNIT-059: Xは1000へ飽和し、Zは200のまま保持され、回転エラーになること。
        Verification rationale:
            XとZを同時に超過させて異なる期待処理を一度に観測するため、軸種別処理の混同を検出できる。
        See Also:
            REQ-LIMIT-003
        """
        r = self._eval(x=1200, z=200)
        self.assertEqual(1000.0, r.command.x); self.assertEqual(200.0, r.command.z); self.assertTrue(r.rotational_error)


if __name__ == "__main__":
    unittest.main()
