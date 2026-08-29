"""入力検証機能の単体テスト。

File: test_validation.py
InputValidator の入力境界・異常値・複合エラーを検証する。
docs/test_specification.md に定義された TEST-UNIT-001..016,111..116 を実装する。
"""

import math
import unittest

from validation import InputValidator
from tests.test_support import make_limits, make_settings
from models import AxisRange


class TestInputValidator(unittest.TestCase):
    """InputValidator の要求適合性を確認するテストクラス。"""

    def setUp(self):
        """各テストで独立した InputValidator を生成する。"""
        self.validator = InputValidator()

    def test_valid_settings(self):
        """TEST-UNIT-001

        テスト目的:
            正常設定が有効として受理されることを確認する。

        テスト手順:
            1. 標準の正常設定を validate() に入力し、is_valid と ERROR issue の有無を観測する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            全入力が仕様範囲内の場合、検証結果が有効でエラーを含まないこと。

        検証根拠:
            正常入力に対する公開検証結果そのものを確認するため、入力検証が正常系を誤って拒否しないことを直接判定できる。
        """
        result = self.validator.validate(make_settings())
        self.assertTrue(result.is_valid)
        self.assertFalse(any(i.severity.name == "ERROR" for i in result.issues))

    def test_aoa_min_equal_max(self):
        """TEST-UNIT-002

        テスト目的:
            AoA最小値と最大値が等しい場合を拒否することを確認する。

        テスト手順:
            1. 境界条件として最小値と最大値を同値にし、is_valid=False を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aoa_min == aoa_max は不正入力であること。

        検証根拠:
            仕様が禁止する等号境界を直接入力して検証結果を観測するため、AoA範囲の厳密な大小関係を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aoa_min=10, aoa_max=10)).is_valid)

    def test_aoa_min_greater_than_max(self):
        """TEST-UNIT-003

        テスト目的:
            AoA最小値が最大値を超える場合を拒否することを確認する。

        テスト手順:
            1. 逆転したAoA範囲を与え、検証結果が無効になることを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aoa_min > aoa_max は不正入力であること。

        検証根拠:
            範囲逆転という代表的な異常条件を直接与えるため、AoA範囲整合性判定を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aoa_min=11, aoa_max=10)).is_valid)

    def test_aos_min_equal_max(self):
        """TEST-UNIT-004

        テスト目的:
            AoS最小値と最大値が等しい場合を拒否することを確認する。

        テスト手順:
            1. AoS範囲の等号境界を入力し、is_valid=False を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aos_min == aos_max は不正入力であること。

        検証根拠:
            AoSに対して仕様が禁止する境界値を直接試験するため、範囲判定を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aos_min=10, aos_max=10)).is_valid)

    def test_aos_min_greater_than_max(self):
        """TEST-UNIT-005

        テスト目的:
            AoS最小値が最大値を超える場合を拒否することを確認する。

        テスト手順:
            1. 逆転したAoS範囲を入力し、無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aos_min > aos_max は不正入力であること。

        検証根拠:
            入力整合性違反を直接与えて公開判定を確認するため、AoS範囲検証を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aos_min=11, aos_max=10)).is_valid)

    def test_aoa_points_minimum_valid(self):
        """TEST-UNIT-006

        テスト目的:
            AoA点数の下限2点が有効であることを確認する。

        テスト手順:
            1. 許容下限値を入力し、検証が成功することを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aoa_points=2 は有効であること。

        検証根拠:
            下限値そのものを試験することで、境界を1点ずらして誤判定する実装を検出できる。
        """
        self.assertTrue(self.validator.validate(make_settings(aoa_points=2)).is_valid)

    def test_aoa_points_too_small(self):
        """TEST-UNIT-007

        テスト目的:
            AoA点数が2未満の場合を拒否することを確認する。

        テスト手順:
            1. 下限直下の値を入力し、検証が失敗することを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aoa_points=1 は不正であること。

        検証根拠:
            下限直下を確認するため、点数下限制約の境界を正確に判定できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aoa_points=1)).is_valid)

    def test_aos_points_too_small(self):
        """TEST-UNIT-008

        テスト目的:
            AoS点数が2未満の場合を拒否することを確認する。

        テスト手順:
            1. AoS点数を下限直下に設定し、無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            aos_points=1 は不正であること。

        検証根拠:
            AoS点数制約に対し禁止値を直接入力するため、最小点数の検証を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(aos_points=1)).is_valid)

    def test_feed_rate_invalid(self):
        """TEST-UNIT-009

        テスト目的:
            Feed rate の0・負値・非有限値を拒否することを確認する。

        テスト手順:
            1. 0、負値、NaN、+InfをsubTestで個別に入力して無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            仕様外のFeed rateはすべて無効であること。

        検証根拠:
            数値範囲違反と非有限値の両系統を網羅するため、下限制約と有限値制約を同時に確認できる。
        """
        for value in (0.0, -1.0, math.nan, math.inf):
            with self.subTest(value=value):
                self.assertFalse(self.validator.validate(make_settings(feed_rate=value)).is_valid)

    def test_hold_time_invalid(self):
        """TEST-UNIT-010

        テスト目的:
            保持時間の下限未満・非有限値を拒否することを確認する。

        テスト手順:
            1. 代表的な下限違反値と非有限値を個別に検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            0.1秒未満、NaN、+Infの保持時間は無効であること。

        検証根拠:
            下限近傍を含む複数の禁止入力で公開判定を確認するため、保持時間制約を確認できる。
        """
        for value in (0.0, 0.099, -1.0, math.nan, math.inf):
            with self.subTest(value=value):
                self.assertFalse(self.validator.validate(make_settings(hold_time_s=value)).is_valid)

    def test_distance_non_finite(self):
        """TEST-UNIT-011

        テスト目的:
            Lx/Lyの非有限値を拒否することを確認する。

        テスト手順:
            1. X/Y両寸法についてNaNとInfを組み合わせて検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            tip_offset_x/y にNaNまたはInfを指定した場合は無効であること。

        検証根拠:
            両フィールドそれぞれで非有限値を直接入力するため、有限実数であるという仕様を確認できる。
        """
        for field in ("tip_offset_x", "tip_offset_y"):
            for value in (math.nan, math.inf):
                with self.subTest(field=field, value=value):
                    self.assertFalse(self.validator.validate(make_settings(**{field: value})).is_valid)

    def test_x_range_equal(self):
        """TEST-UNIT-012

        テスト目的:
            X軸可動範囲の最小値と最大値が等しい場合を拒否する。

        テスト手順:
            1. X軸だけを等号境界にして検証結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            X minimum == maximum は無効であること。

        検証根拠:
            他軸を正常に保ったままX軸だけを違反させるため、X範囲検証を分離して確認できる。
        """
        limits = make_limits(x=AxisRange(1.0, 1.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    def test_y_range_reversed(self):
        """TEST-UNIT-013

        テスト目的:
            Y軸可動範囲が逆転した場合を拒否する。

        テスト手順:
            1. Y軸だけを逆転させ、検証結果が無効となることを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            Y minimum > maximum は無効であること。

        検証根拠:
            Y軸の範囲整合性違反を単独で与えるため、該当軸の判定を直接確認できる。
        """
        limits = make_limits(y=AxisRange(2.0, 1.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    def test_z_range_invalid(self):
        """TEST-UNIT-014

        テスト目的:
            Z軸可動範囲が成立しない場合を拒否する。

        テスト手順:
            1. Z軸の最小・最大を同値にして検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            Z minimum >= maximum は無効であること。

        検証根拠:
            回転軸Zの範囲だけを不正化して判定を見るため、軸別入力検証を確認できる。
        """
        limits = make_limits(z=AxisRange(2.0, 2.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    def test_a_range_invalid(self):
        """TEST-UNIT-015

        テスト目的:
            A軸可動範囲が逆転した場合を拒否する。

        テスト手順:
            1. A軸だけを逆転させ、検証結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            A minimum > maximum は無効であること。

        検証根拠:
            A軸の不正範囲を単独で入力するため、ロール軸の範囲検証を確認できる。
        """
        limits = make_limits(a=AxisRange(3.0, 2.0))
        self.assertFalse(self.validator.validate(make_settings(axis_limits=limits)).is_valid)

    def test_multiple_errors_are_reported(self):
        """TEST-UNIT-016

        テスト目的:
            複数の入力不正を同時に報告できることを確認する。

        テスト手順:
            1. AoA範囲、点数、Feed rateを同時に不正化し、ERROR数が3件以上であることを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            複数フィールドが不正な場合、単一エラーで打ち切らず複数issueを返すこと。

        検証根拠:
            独立した3種類の不正条件を同時入力しissue数を観測するため、全項目を継続検証する動作を確認できる。
        """
        result = self.validator.validate(make_settings(aoa_min=10, aoa_max=10, aoa_points=1, feed_rate=0))
        self.assertGreaterEqual(sum(i.severity.name == "ERROR" for i in result.issues), 3)

    def test_lx_zero_is_invalid(self):
        """TEST-UNIT-111

        テスト目的:
            Lx=0を拒否することを確認する。

        テスト手順:
            1. 仕様境界値0.0を入力して無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            Lxは0より大きくなければならない。

        検証根拠:
            禁止境界そのものを入力するため、Lx>0という厳密不等号の実装を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(tip_offset_x=0.0)).is_valid)

    def test_ly_negative_is_invalid(self):
        """TEST-UNIT-112

        テスト目的:
            Lyが負値の場合を拒否することを確認する。

        テスト手順:
            1. 代表的な負値-0.1を入力して検証結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            Ly<=0 は無効であること。

        検証根拠:
            正値制約に明確に違反する入力を与えるため、Lyの符号条件を確認できる。
        """
        self.assertFalse(self.validator.validate(make_settings(tip_offset_y=-0.1)).is_valid)

    def test_hold_time_minimum_is_valid(self):
        """TEST-UNIT-113

        テスト目的:
            保持時間0.1秒が有効であることを確認する。

        テスト手順:
            1. 下限値そのものを入力し、is_valid=Trueを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            hold_time_s=0.1 は許容下限として有効であること。

        検証根拠:
            許容境界を直接試験するため、>=0.1 の境界条件を確認できる。
        """
        self.assertTrue(self.validator.validate(make_settings(hold_time_s=0.1)).is_valid)

    def test_hold_time_below_minimum_is_invalid(self):
        """TEST-UNIT-114

        テスト目的:
            保持時間が0.1秒をわずかに下回る場合を拒否する。

        テスト手順:
            1. 境界直下0.099999を入力し、無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            hold_time_s<0.1 は無効であること。

        検証根拠:
            下限直下を試験することで、丸めや比較演算子の誤りによる誤受理を検出できる。
        """
        self.assertFalse(self.validator.validate(make_settings(hold_time_s=0.099999)).is_valid)

    def test_feed_rate_minimum_is_valid(self):
        """TEST-UNIT-115

        テスト目的:
            Feed rateの下限1.0が有効であることを確認する。

        テスト手順:
            1. 許容下限値を入力して検証成功を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            feed_rate=1.0 は有効であること。

        検証根拠:
            下限値そのものを観測するため、>=1.0という境界条件を直接確認できる。
        """
        self.assertTrue(self.validator.validate(make_settings(feed_rate=1.0)).is_valid)

    def test_feed_rate_below_minimum_is_invalid(self):
        """TEST-UNIT-116

        テスト目的:
            Feed rateが1.0をわずかに下回る場合を拒否する。

        テスト手順:
            1. 境界直下0.999999を入力して無効判定を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            feed_rate<1.0 は無効であること。

        検証根拠:
            下限直下を直接試験するため、比較演算子や境界処理の誤りを検出できる。
        """
        self.assertFalse(self.validator.validate(make_settings(feed_rate=0.999999)).is_valid)


if __name__ == "__main__":
    unittest.main()
