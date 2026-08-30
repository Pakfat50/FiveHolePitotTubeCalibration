"""アプリケーション制御の単体テスト。

File: test_controller.py
CalibrationController の検証・plan再生成・生成可否・設定適用を検証する。
docs/test_specification.md の TEST-UNIT-084..089 に対応する。
"""

import unittest
from unittest.mock import Mock

from controller import CalibrationController
from tests.test_support import make_settings


class TestCalibrationController(unittest.TestCase):
    """Controller が Validator と Service を正しい条件で呼び分け、状態を保持することを確認する。"""

    def setUp(self):
        """依存先をMock化しController単体の制御判断だけを観測可能にする。"""
        self.validator = Mock()
        self.service = Mock()
        self.controller = CalibrationController(self.validator, self.service)

    def test_valid_input_rebuilds_plan(self):
        """TEST-UNIT-084

        テスト目的:
            有効入力では検証後にplanを再生成し保持することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            valid設定変更でvalidate→build_planが実行され、生成planがcurrent_planになること。

        検証根拠:
            Mockの呼出し引数・回数とController内部公開状態を同時に確認するため、有効入力時の制御フローを直接検証できる。
        """
        valid = Mock(is_valid=True, issues=[])
        plan = Mock(has_generation_error=False)
        self.validator.validate.return_value = valid
        self.service.build_plan.return_value = plan
        settings = make_settings()
        self.controller.on_settings_changed(settings)
        self.validator.validate.assert_called_once_with(settings)
        self.service.build_plan.assert_called_once_with(settings)
        self.assertIs(plan, self.controller.get_current_plan())

    def test_invalid_input_does_not_rebuild_plan(self):
        """TEST-UNIT-085

        テスト目的:
            不正入力ではplanを再生成せず生成不可になることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            validateが無効ならbuild_planを呼ばずcan_generate=Falseとすること。

        検証根拠:
            Service未呼出しと生成不可状態を確認することで、不正入力から計算処理へ進まないガード条件を検証できる。
        """
        self.validator.validate.return_value = Mock(is_valid=False, issues=[Mock()])
        self.controller.on_settings_changed(make_settings())
        self.service.build_plan.assert_not_called()
        self.assertFalse(self.controller.can_generate())

    def test_invalid_then_valid_recovers(self):
        """TEST-UNIT-086

        テスト目的:
            一時的不正入力が解消された後に生成可能状態へ自動復帰することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            連続2回の設定変更でinvalid→validとなった場合、can_generateがFalse→Trueへ変化すること。

        検証根拠:
            同一Controller上で状態遷移を連続観測するため、エラー状態が残留せず再検証結果へ追従することを確認できる。
        """
        self.validator.validate.side_effect = [Mock(is_valid=False, issues=[Mock()]), Mock(is_valid=True, issues=[])]
        self.service.build_plan.return_value = Mock(has_generation_error=False)
        settings = make_settings()
        self.controller.on_settings_changed(settings)
        self.assertFalse(self.controller.can_generate())
        self.controller.on_settings_changed(settings)
        self.assertTrue(self.controller.can_generate())

    def test_xy_warning_plan_can_generate(self):
        """TEST-UNIT-087

        テスト目的:
            X/Y偏差を含む警告planでも生成可能であることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            max_x/y_deviationが非零でもgeneration_error=Falseならcan_generate=Trueであること。

        検証根拠:
            警告情報を持つplanを明示的に与えて生成可否だけを観測するため、XY警告が禁止条件へ誤昇格しないことを確認できる。
        """
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=False, max_x_deviation=1.0, max_y_deviation=2.0)
        self.controller.on_settings_changed(make_settings())
        self.assertTrue(self.controller.can_generate())

    def test_rotational_error_plan_cannot_generate(self):
        """TEST-UNIT-088

        テスト目的:
            Z/A生成禁止エラーplanでは生成不可となることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            has_generation_error=Trueなら入力自体が有効でもcan_generate=Falseであること。

        検証根拠:
            Validation成功とplan生成エラーを意図的に組み合わせるため、入力エラーとは独立した回転軸禁止条件を確認できる。
        """
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=True)
        self.controller.on_settings_changed(make_settings())
        self.assertFalse(self.controller.can_generate())

    def test_apply_settings_updates_and_revalidates(self):
        """TEST-UNIT-089

        テスト目的:
            読み込んだ設定適用時に現在設定更新と再検証・再計算を行うことを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            apply_settings後、設定を保持しvalidate/build_planへ同じ設定を渡すこと。

        検証根拠:
            保存設定値、Validator呼出し、Service呼出しを同時に確認するため、設定読込後の適用経路をController単位で検証できる。
        """
        self.validator.validate.return_value = Mock(is_valid=True, issues=[])
        self.service.build_plan.return_value = Mock(has_generation_error=False)
        settings = make_settings(feed_rate=123.0)
        self.controller.apply_settings(settings)
        self.assertEqual(settings, self.controller.get_current_settings())
        self.validator.validate.assert_called_once_with(settings)
        self.service.build_plan.assert_called_once_with(settings)


if __name__ == "__main__":
    unittest.main()
