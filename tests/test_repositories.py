"""設定・初期化Gコード・生成GコードのRepository単体テスト。

@file test_repositories.py
@brief CSV設定保存読込、テキスト読込、NC保存、各種I/O・構造エラー処理を検証する。
@details docs/test_specification.md の TEST-UNIT-076..083,117..120 に対応する。
"""

import csv
import os
import tempfile
import unittest

from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository, SettingsLoadError
from tests.test_support import make_settings


class TestRepositories(unittest.TestCase):
    """@brief Repository群が正常データを損失なく保持し、異常データを明示的に失敗として扱うことを確認する。"""

    # TEST-UNIT-076
    # Requirements: REQ-GUI-003
    def test_settings_csv_round_trip(self):
        """@brief 設定CSVの保存→読込で全設定値が一致することを確認する。

        @test TEST-UNIT-076: SettingsRepository.save/load の往復後に元のCalibrationSettingsと一致すること。
        @par 検証根拠
        同一オブジェクト内容を保存前後で完全比較するため、各フィールドの欠落・型変換・値変化をまとめて検出できる。
        @see REQ-GUI-003
        """
        repo = SettingsRepository()
        settings = make_settings()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "settings.csv")
            repo.save(path, settings)
            loaded = repo.load(path)
        self.assertEqual(settings, loaded)

    # TEST-UNIT-077
    # Requirements: REQ-GUI-003
    def test_options_round_trip(self):
        """@brief boolオプションの全組合せがCSV往復で保持されることを確認する。

        @test TEST-UNIT-077: serpentine/output_commentsの4組合せが保存前後で一致すること。
        @par 検証根拠
        True/False直積を全列挙するため、文字列化・bool復元の片側だけが壊れる実装を検出できる。
        @see REQ-GUI-003
        """
        repo = SettingsRepository()
        for serpentine in (False, True):
            for comments in (False, True):
                with self.subTest(serpentine=serpentine, comments=comments), tempfile.TemporaryDirectory() as d:
                    s = make_settings(serpentine=serpentine, output_comments=comments)
                    p = os.path.join(d, "settings.csv"); repo.save(p, s)
                    loaded = repo.load(p)
                    self.assertEqual((serpentine, comments), (loaded.serpentine, loaded.output_comments))

    # TEST-UNIT-078
    # Requirements: REQ-GUI-003
    def test_axis_ranges_round_trip(self):
        """@brief X/Y/Z/A可動範囲がCSV往復で保持されることを確認する。

        @test TEST-UNIT-078: loaded.axis_limitsが保存前axis_limitsと一致すること。
        @par 検証根拠
        AxisLimits全体を等価比較するため、8個のmin/max値のどれか1つでも欠落・取り違えがあれば検出できる。
        @see REQ-GUI-003
        """
        repo = SettingsRepository(); settings = make_settings()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "settings.csv"); repo.save(p, settings); loaded = repo.load(p)
        self.assertEqual(settings.axis_limits, loaded.axis_limits)

    # TEST-UNIT-079
    # Requirements: REQ-GUI-003
    def test_structurally_invalid_csv_returns_explicit_error(self):
        """@brief 構造不正CSVをSettingsLoadErrorとして拒否することを確認する。

        @test TEST-UNIT-079: key/value形式でないCSV読込が明示的な設定読込エラーになること。
        @par 検証根拠
        実ファイルへ不正行構造を書き込み公開load()を呼ぶため、CSV parserからRepository例外への防御経路を実際に確認できる。
        @see REQ-GUI-003
        """
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write("this,is,not,key,value\n")
            path = f.name
        try:
            with self.assertRaises(SettingsLoadError): SettingsRepository().load(path)
        finally: os.remove(path)

    # TEST-UNIT-080
    # Requirements: REQ-INPUT-006
    def test_initialization_gcode_utf8_multiline(self):
        """@brief UTF-8日本語を含む複数行初期化Gコードをそのまま読み込めることを確認する。

        @test TEST-UNIT-080: ファイル内容とload()戻り値が完全一致すること。
        @par 検証根拠
        日本語・コメント・複数行を含む文字列全体を比較するため、文字コード・改行・行順の保持を同時に確認できる。
        @see REQ-INPUT-006
        """
        content = "; 初期化\nG92 X0\nM5\n"
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write(content); path = f.name
        try: self.assertEqual(content, InitializationGCodeRepository().load(path))
        finally: os.remove(path)

    # TEST-UNIT-081
    # Requirements: REQ-INPUT-006
    def test_missing_initialization_file_raises_ioerror(self):
        """@brief 存在しない初期化GコードファイルでI/Oエラーが通知されることを確認する。

        @test TEST-UNIT-081: missing pathに対するload()がOSErrorを送出すること。
        @par 検証根拠
        確実に存在しないパスを公開APIへ渡すため、読込失敗が成功扱いや空文字扱いにならないことを確認できる。
        @see REQ-INPUT-006
        """
        with self.assertRaises(OSError): InitializationGCodeRepository().load("__missing_init__.txt")

    # TEST-UNIT-082
    # Requirements: REQ-GCODE-001
    def test_save_nc_file(self):
        """@brief Gコードを指定した.ncファイルへUTF-8で保存できることを確認する。

        @test TEST-UNIT-082: save後の実ファイル内容が入力テキストと一致すること。
        @par 検証根拠
        一時ディレクトリ上の実ファイルを再オープンして内容比較するため、Repositoryの書込副作用そのものを確認できる。
        @see REQ-GCODE-001
        """
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.nc"); GCodeRepository().save(path, "G21\n")
            with open(path, encoding="utf-8") as f: self.assertEqual("G21\n", f.read())

    # TEST-UNIT-083
    # Requirements: REQ-GCODE-001
    def test_gcode_save_failure_is_reported(self):
        """@brief Gコード保存失敗がOSErrorとして呼出し元へ通知されることを確認する。

        @test TEST-UNIT-083: 存在しないディレクトリへのsaveがOSErrorを送出すること。
        @par 検証根拠
        書込不能パスを使用することで実I/O失敗を発生させ、例外が握り潰されないことを確認できる。
        @see REQ-GCODE-001
        """
        with self.assertRaises(OSError): GCodeRepository().save(os.path.join("__missing_dir__", "out.nc"), "G21\n")

    # TEST-UNIT-117
    # Requirements: REQ-GUI-003
    def test_missing_required_csv_key(self):
        """@brief 必須CSVキー欠損を読込失敗として扱うことを確認する。

        @test TEST-UNIT-117: feed_rateキー欠損でSettingsLoadErrorとなること。
        @par 検証根拠
        正常CSV集合から必須キー1件だけを除去するため、欠損検出ロジックを他の構造異常から分離して確認できる。
        @see REQ-GUI-003
        """
        self._assert_bad_csv({"feed_rate": None})

    # TEST-UNIT-118
    # Requirements: REQ-GUI-003
    def test_blank_required_csv_value(self):
        """@brief 必須CSV値が空欄の場合を読込失敗として扱うことを確認する。

        @test TEST-UNIT-118: feed_rate=""でSettingsLoadErrorとなること。
        @par 検証根拠
        キーは存在するが値だけ空欄という条件を作るため、キー欠損とは別の空値検証を確認できる。
        @see REQ-GUI-003
        """
        self._assert_bad_csv({"feed_rate": ""}, omit_none=False)

    # TEST-UNIT-119
    # Requirements: REQ-GUI-003
    def test_non_numeric_csv_value(self):
        """@brief 数値項目に変換不能文字列がある場合を読込失敗として扱うことを確認する。

        @test TEST-UNIT-119: feed_rate="abc"でSettingsLoadErrorとなること。
        @par 検証根拠
        CSV構造と必須値存在を正常に保ったまま型変換だけを失敗させるため、数値変換エラー処理を分離して検証できる。
        @see REQ-GUI-003
        """
        self._assert_bad_csv({"feed_rate": "abc"}, omit_none=False)

    # TEST-UNIT-120
    # Requirements: REQ-GUI-003
    def test_settings_io_failure_is_wrapped(self):
        """@brief 設定ファイルI/O失敗がSettingsLoadErrorへ統一されることを確認する。

        @test TEST-UNIT-120: 存在しない設定CSV読込でSettingsLoadErrorとなること。
        @par 検証根拠
        OSレベルのfile-not-foundを発生させてRepository公開例外型を確認するため、呼出し側が一貫して処理できる例外ラップを検証できる。
        @see REQ-GUI-003
        """
        with self.assertRaises(SettingsLoadError): SettingsRepository().load("__missing_settings__.csv")

    def _assert_bad_csv(self, changes, omit_none=True):
        """@brief 基準CSVの一部を意図的に壊しSettingsLoadErrorを確認する補助メソッド。

        @param changes 変更するkey/value辞書。
        @param omit_none None指定キーをCSVから欠損させるかどうか。
        @par 検証根拠
        それ以外の全必須項目を正常値に固定することで、各異常テストが対象フィールドの不正だけを原因として失敗する状態を作れる。
        """
        base = {
            "aoa_min":"-10", "aoa_max":"10", "aos_min":"-10", "aos_max":"10",
            "aoa_points":"3", "aos_points":"3", "tip_offset_x":"100", "tip_offset_y":"10",
            "hold_time_s":"1", "feed_rate":"100", "x_min":"-1000", "x_max":"1000",
            "y_min":"-1000", "y_max":"1000", "z_min":"-180", "z_max":"180",
            "a_min":"-720", "a_max":"720", "serpentine":"false", "output_comments":"true"
        }
        base.update(changes)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["key","value"])
            for k,v in base.items():
                if v is None and omit_none: continue
                w.writerow([k,v]); path=f.name
        try:
            with self.assertRaises(SettingsLoadError): SettingsRepository().load(path)
        finally: os.remove(path)


if __name__ == "__main__":
    unittest.main()
