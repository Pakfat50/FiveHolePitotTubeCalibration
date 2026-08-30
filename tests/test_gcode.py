"""Gコード生成の単体テスト。

File: test_gcode.py
GCodeGenerator のヘッダ、各較正点指令、書式、コメント、終了位置を検証する。
docs/test_specification.md の TEST-UNIT-066..075 に対応する。
"""

import unittest

from calibration_service import CalibrationService
from gcode import GCodeGenerator
from tests.test_support import make_settings, make_limits
from models import AxisRange


class TestGCodeGenerator(unittest.TestCase):
    """CalibrationPlan から要求どおりのGコード文字列が生成されることを確認する。"""

    def setUp(self):
        """実planを生成できるServiceとGeneratorを準備する。"""
        self.generator = GCodeGenerator()
        self.service = CalibrationService()

    def _generate(self, settings=None, init="G92 X0\n"):
        """指定設定から実planを構築しGコード文字列を返す補助メソッド。

        検証根拠:
        MockではなくCalibrationServiceが生成したplanを入力するため、GCodeGeneratorが実際のデータ構造を正しく文字列化できることを確認できる。
        """
        settings = settings or make_settings(aoa_points=2, aos_points=2)
        plan = self.service.build_plan(settings)
        return self.generator.generate(plan, settings, init)

    def test_header_contains_required_commands(self):
        """TEST-UNIT-066

        テスト目的:
            必須ヘッダコマンドが生成Gコードに含まれることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            初期化見出し、$H、G21、G90、G94を含むこと。

        検証根拠:
            仕様で列挙された必須トークンを生成文字列から直接検索するため、各必須ヘッダ要素の欠落を検出できる。
        """
        text = self._generate()
        for token in ("; User initialization G-code", "$H", "G21", "G90", "G94"):
            self.assertIn(token, text)

    def test_initialization_text_preserved_in_order(self):
        """TEST-UNIT-067

        テスト目的:
            ユーザー初期化Gコードが内容・行順を保って出力されることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            複数行初期化テキストがそのまま連続部分文字列として含まれること。

        検証根拠:
            入力した複数行文字列全体の一致を確認するため、個別行の存在だけでなく行順と改行保持も検証できる。
        """
        init = ";a\nG92 X0\nM5\n"
        text = self._generate(init=init)
        self.assertIn(init, text)

    def test_each_move_has_four_axes_and_feed(self):
        """TEST-UNIT-068

        テスト目的:
            各G01移動行がX/Y/Z/A/Fをすべて含むことを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            全移動指令に4軸とFeed wordが存在すること。

        検証根拠:
            全G01行を抽出して各wordを反復確認するため、一部較正点だけ出力項目が欠ける不具合も検出できる。
        """
        lines = [l for l in self._generate().splitlines() if l.startswith("G01 ")]
        self.assertTrue(lines)
        for line in lines:
            for word in ("X", "Y", "Z", "A", "F"):
                self.assertIn(word, line)

    def test_g_numbers_are_zero_padded(self):
        """TEST-UNIT-069

        テスト目的:
            移動・保持G番号が2桁ゼロ埋め表記であることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            G01およびG04表記が生成されること。

        検証根拠:
            実出力文字列のG番号表現を直接確認するため、G1/G4のような非ゼロ埋め出力を検出できる。
        """
        text = self._generate()
        self.assertIn("G01 ", text)
        self.assertIn("G04 ", text)

    def test_feed_rate_has_six_decimal_places(self):
        """TEST-UNIT-070

        テスト目的:
            Feed rateが小数点以下6桁で出力されることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            feed_rate=12.5がF12.500000となること。

        検証根拠:
            小数桁数が視認可能な値を入力し完全な期待文字列を比較するため、丸め・桁数・F接頭辞を同時に確認できる。
        """
        text = self._generate(make_settings(feed_rate=12.5, aoa_points=2, aos_points=2))
        self.assertIn("F12.500000", text)

    def test_hold_time_has_six_decimal_places(self):
        """TEST-UNIT-071

        テスト目的:
            保持時間がG04 P<秒>の6桁小数で出力されることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            hold_time_s=3.0がG04 P3.000000となること。

        検証根拠:
            G番号・P word・秒単位値・小数桁数を1つの期待文字列で比較するため、保持指令書式を直接検証できる。
        """
        text = self._generate(make_settings(hold_time_s=3.0, aoa_points=2, aos_points=2))
        self.assertIn("G04 P3.000000", text)

    def test_comments_enabled(self):
        """TEST-UNIT-072

        テスト目的:
            コメント出力ONで較正点コメントにAoA/AoSが含まれることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            output_comments=TrueでAoA/AoSコメントを生成すること。

        検証根拠:
            オプションON時の生成文字列に較正角識別子が存在することを確認するため、コメント生成経路が有効化されることを判定できる。
        """
        text = self._generate(make_settings(output_comments=True, aoa_points=2, aos_points=2))
        self.assertIn("AoA", text); self.assertIn("AoS", text)

    def test_comments_disabled(self):
        """TEST-UNIT-073

        テスト目的:
            コメント出力OFFで較正点コメントが生成されないことを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            output_comments=FalseではAoAを含む点コメントが0件であること。

        検証根拠:
            コメント行だけを抽出して件数0を確認するため、初期化コード等の他文字列に影響されずオプション無効化を検証できる。
        """
        text = self._generate(make_settings(output_comments=False, aoa_points=2, aos_points=2))
        point_comments = [l for l in text.splitlines() if l.startswith(";") and "AoA" in l]
        self.assertEqual([], point_comments)

    def test_no_return_home_after_final_point(self):
        """TEST-UNIT-074

        テスト目的:
            最終較正点後に原点復帰指令を追加しないことを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            最終非空行が$HまたはXYZ A=0への復帰移動ではないこと。

        検証根拠:
            終端行そのものを禁止指令集合と比較するため、生成終了時の自動復帰追加を直接検出できる。
        """
        lines = [l.strip() for l in self._generate().splitlines() if l.strip()]
        self.assertFalse(lines[-1] in ("$H", "G00 X0 Y0 Z0 A0", "G01 X0 Y0 Z0 A0"))

    def test_saturated_actual_command_is_written(self):
        """TEST-UNIT-075

        テスト目的:
            X/Y飽和時に理想値ではなく実際の飽和後指令値をGコードへ出力することを確認する。

        テスト手順:
            1. 実CalibrationServiceで飽和planを作り、そのPointEvaluationのactual commandを出力と比較する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            saturated.command.x/yの6桁値が生成文字列に含まれること。

        検証根拠:
            理想値と実値が異なる条件でactual commandを期待値に使うため、GCodeGeneratorが誤ってideal_commandを参照する不具合を検出できる。
        """
        limits = make_limits(x=AxisRange(-0.01, 0.01), y=AxisRange(-0.01, 0.01))
        settings = make_settings(axis_limits=limits, aoa_points=2, aos_points=2)
        plan = self.service.build_plan(settings)
        saturated = next(p for p in plan.points if p.x_saturated or p.y_saturated)
        text = self.generator.generate(plan, settings, "")
        self.assertIn(f"X{saturated.command.x:.6f}", text)
        self.assertIn(f"Y{saturated.command.y:.6f}", text)


if __name__ == "__main__":
    unittest.main()
