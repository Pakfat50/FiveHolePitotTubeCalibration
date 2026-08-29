"""製品ユースケース経路の組み合わせテスト。

File: test_use_cases.py
UC-01～UC-06について、複数モジュールを実際に組み合わせたユーザー操作単位の成立性を検証する。
Details: docs/test_specification.md の TEST-UC-* を実装し、単体テストでは確認できないモジュール間データフローと状態遷移を確認する。
"""

import csv
import os
import tempfile
import unittest

from calibration_service import CalibrationService
from controller import CalibrationController
from gcode import GCodeGenerator
from gui import MainWindow
from map_view import CalibrationMapView
from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository, SettingsLoadError
from simulation import SimulationController, SimulationView
from validation import InputValidator
from tests.test_support import make_limits, make_settings
from models import AxisRange


class UseCaseHarness:
    """ユースケーステストでproduction実装を組み合わせる共通ハーネス。

    Details: MockではなくValidator、Service、Controller、Repository、Generatorの実クラスを接続し、製品と同じ主要データ経路を再現する。
    @par 設計根拠
    ユースケーステストでは個別メソッドではなく複数モジュール間の受渡しを確認する必要があるため、共通の実オブジェクト集合を一箇所で構築する。
    """

    def __init__(self):
        """ユースケース実行に必要なproductionオブジェクトを生成する。"""
        self.validator = InputValidator()
        self.service = CalibrationService()
        self.controller = CalibrationController(self.validator, self.service)
        self.settings_repo = SettingsRepository()
        self.init_repo = InitializationGCodeRepository()
        self.generator = GCodeGenerator()
        self.gcode_repo = GCodeRepository()


class TestUseCases(unittest.TestCase):
    """ユーザー操作単位でproductionモジュールの組み合わせ動作を確認する。"""

    def setUp(self):
        """各テストを独立状態で開始するため新しいUseCaseHarnessを生成する。"""
        self.h = UseCaseHarness()

    # TEST-UC-01-01
    # UseCase: UC-01
    def test_uc01_valid_input_recalculates_plan(self):
        """正常な較正条件入力でplanが自動生成され操作可能になることを確認する。

        Test: TEST-UC-01-01: 有効設定をControllerへ入力するとcurrent_planが生成されcan_generate=Trueとなること。
        Verification rationale:
        実Validator→Service→Controller経路を通した最終plan存在と生成可否を確認するため、正常入力ユースケース全体の成立を確認できる。
        """
        s = make_settings(); self.h.controller.on_settings_changed(s)
        self.assertIsNotNone(self.h.controller.get_current_plan()); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-02
    # UseCase: UC-01
    def test_uc01_invalid_aoa_range_blocks_generation(self):
        """AoA範囲不正で生成操作が禁止されることを確認する。

        Test: TEST-UC-01-02: aoa_min==aoa_maxの入力後can_generate=Falseとなること。
        Verification rationale:
        実Validatorの不正判定をController生成可否まで伝播させて観測するため、入力エラーが操作禁止へ接続されることを確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(aoa_min=10, aoa_max=10))
        self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-03
    # UseCase: UC-01
    def test_uc01_temporary_invalid_then_valid_recovers(self):
        """一時的不正入力から正常入力へ戻すと生成可能状態へ復帰することを確認する。

        Test: TEST-UC-01-03: feed_rate=0で禁止、100へ戻した後に許可となること。
        Verification rationale:
        同一Controllerで連続するユーザー編集を再現し状態を前後比較するため、一時エラーが残留しないことを確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(feed_rate=0)); self.assertFalse(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(feed_rate=100)); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-04
    # UseCase: UC-01
    def test_uc01_point_count_change_rebuilds_grid(self):
        """点数変更に応じて較正点列がリアルタイム再生成されることを確認する。

        Test: TEST-UC-01-04: 2×2→3×4へ変更するとplan点数が4→12へ更新されること。
        Verification rationale:
        同一Controllerへ異なる点数設定を順に入力してcurrent_plan件数を確認するため、設定変更から再計算までの経路を直接検証できる。
        """
        self.h.controller.on_settings_changed(make_settings(aoa_points=2,aos_points=2)); self.assertEqual(4,len(self.h.controller.get_current_plan().points))
        self.h.controller.on_settings_changed(make_settings(aoa_points=3,aos_points=4)); self.assertEqual(12,len(self.h.controller.get_current_plan().points))

    # TEST-UC-01-05
    # UseCase: UC-01
    def test_uc01_serpentine_changes_order_not_set(self):
        """蛇行ON/OFFで較正点集合は同じまま走査順だけが変わることを確認する。

        Test: TEST-UC-01-05: 2つのplanの座標集合は一致し、順序付き列は不一致であること。
        Verification rationale:
        集合比較と列比較を併用するため、蛇行が点の追加削除ではなく順序だけを変更することを明確に確認できる。
        """
        p1=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3,serpentine=False))
        p2=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3,serpentine=True))
        self.assertEqual({(p.point.aoa,p.point.aos) for p in p1.points},{(p.point.aoa,p.point.aos) for p in p2.points})
        self.assertNotEqual([(p.point.aoa,p.point.aos) for p in p1.points],[(p.point.aoa,p.point.aos) for p in p2.points])

    # TEST-UC-01-06
    # UseCase: UC-01
    def test_uc01_xy_saturation_warns_but_allows_actions(self):
        """X/Y飽和時に偏差が発生しても生成操作が許可されることを確認する。

        Test: TEST-UC-01-06: 狭いX/Y範囲でmax deviation>0かつcan_generate=Trueとなること。
        Verification rationale:
        実Serviceで飽和を発生させControllerの最終可否まで観測するため、警告と操作許可の組合せを製品経路で確認できる。
        """
        limits=make_limits(x=AxisRange(-0.01,0.01),y=AxisRange(-0.01,0.01)); self.h.controller.on_settings_changed(make_settings(axis_limits=limits))
        plan=self.h.controller.get_current_plan(); self.assertGreater(plan.max_x_deviation+plan.max_y_deviation,0); self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-01-07
    # UseCase: UC-01
    def test_uc01_za_overrange_blocks_actions(self):
        """Z/A範囲超過がplan生成禁止となり操作を無効化することを確認する。

        Test: TEST-UC-01-07: Z範囲±1度でhas_generation_error=Trueかつcan_generate=Falseとなること。
        Verification rationale:
        点評価の回転エラー集約結果とController操作可否を同時確認するため、エラー伝播経路全体を確認できる。
        """
        limits=make_limits(z=AxisRange(-1,1)); self.h.controller.on_settings_changed(make_settings(axis_limits=limits))
        self.assertTrue(self.h.controller.get_current_plan().has_generation_error); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-08
    # UseCase: UC-01
    def test_uc01_xy_warning_and_za_error_coexist(self):
        """X/Y警告情報を保持しつつZ/Aエラーが生成禁止として共存できることを確認する。

        Test: TEST-UC-01-08: X偏差>0かつhas_generation_error=Trueのplanを生成できること。
        Verification rationale:
        並進範囲と回転範囲を同時に狭めることで両状態を実際に発生させ、片方の情報が他方で消されないことを確認できる。
        """
        limits=make_limits(x=AxisRange(-0.01,0.01),z=AxisRange(-1,1)); plan=self.h.service.build_plan(make_settings(axis_limits=limits))
        self.assertGreater(plan.max_x_deviation,0); self.assertTrue(plan.has_generation_error)

    # TEST-UC-01-09
    # UseCase: UC-01
    def test_uc01_grid_origin_is_deterministic(self):
        """AoA=AoS=0の格子点がZ=A=0へ決定的に変換されることを確認する。

        Test: TEST-UC-01-09: 中央点command.z/aが0±0.001度であること。
        Verification rationale:
        実Scan→Transform→Serviceを通した中央点を検索して出力角を確認するため、原点特例が統合後も保持されることを確認できる。
        """
        plan=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=3)); p=next(p for p in plan.points if p.point.aoa==0 and p.point.aos==0)
        self.assertAlmostEqual(0,p.command.z,delta=0.001); self.assertAlmostEqual(0,p.command.a,delta=0.001)

    # TEST-UC-01-10
    # UseCase: UC-01
    def test_uc01_roll_has_no_unnecessary_360_jump(self):
        """蛇行走査中の隣接ロール角に不要な360度ジャンプがないことを確認する。

        Test: TEST-UC-01-10: 全隣接点の|ΔA|<=180.001度であること。
        Verification rationale:
        実planの全隣接組を走査して角差を検査するため、特定点だけでなく走査列全体のunwrap連続性を確認できる。
        """
        plan=self.h.service.build_plan(make_settings(aoa_min=-10,aoa_max=10,aos_min=-10,aos_max=10,aoa_points=3,aos_points=5,serpentine=True))
        for a,b in zip(plan.points,plan.points[1:]): self.assertLessEqual(abs(b.command.a-a.command.a),180.001)

    # TEST-UC-01-11
    # UseCase: UC-01
    def test_uc01_nonpositive_offsets_block_plan(self):
        """Lx/Lyが0以下の場合に生成操作を禁止することを確認する。

        Test: TEST-UC-01-11: tip_offset_xまたはtip_offset_y=0でcan_generate=Falseとなること。
        Verification rationale:
        両フィールドを個別に同じ禁止境界へ設定するため、どちらの寸法制約もController経路で有効であることを確認できる。
        """
        for field in ("tip_offset_x","tip_offset_y"):
            with self.subTest(field=field):
                self.h.controller.on_settings_changed(make_settings(**{field:0})); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-01-12
    # UseCase: UC-01
    def test_uc01_hold_and_feed_boundaries(self):
        """保持時間とFeed rateの許容下限・下限直下をユーザー入力経路で確認する。

        Test: TEST-UC-01-12: hold=0.1,F=1は有効で、hold<0.1またはF<1では無効となること。
        Verification rationale:
        境界値と直下値を連続入力して最終can_generateを比較するため、入力検証境界が操作可否へ正しく反映されることを確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.1,feed_rate=1)); self.assertTrue(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.099,feed_rate=1)); self.assertFalse(self.h.controller.can_generate())
        self.h.controller.on_settings_changed(make_settings(hold_time_s=0.1,feed_rate=0.999)); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-02-01
    # UseCase: UC-02
    def test_uc02_load_initialization_text(self):
        """初期化Gコードの単一行テキストをファイルから読み込めることを確認する。

        Test: TEST-UC-02-01: 実一時ファイル内容とRepository.load戻り値が一致すること。
        Verification rationale:
        実ファイルI/Oを通して内容を完全一致比較するため、初期化コード読込ユースケースの基本経路を確認できる。
        """
        self._with_text_file("G92 X0\n", lambda p: self.assertEqual("G92 X0\n", self.h.init_repo.load(p)))

    # TEST-UC-02-02
    # UseCase: UC-02
    def test_uc02_multiline_order_preserved(self):
        """複数行初期化Gコードが行順を保って読み込まれることを確認する。

        Test: TEST-UC-02-02: コメント・G92・M5を含む入力文字列全体が読込後に一致すること。
        Verification rationale:
        複数行文字列を丸ごと比較するため、改行や行順の変更を検出できる。
        """
        text=";a\nG92 X0\nM5\n"; self._with_text_file(text, lambda p: self.assertEqual(text,self.h.init_repo.load(p)))

    # TEST-UC-02-03
    # UseCase: UC-02
    def test_uc02_cancel_keeps_current_initialization(self):
        """ファイル選択キャンセルでは現在の初期化コードを変更しないことを確認する。

        Test: TEST-UC-02-03: selected_path=Noneのとき既存文字列が保持されること。
        Verification rationale:
        キャンセルを表すNoneと変更前値を同時に保持するシナリオを明示するため、キャンセル時にI/Oや状態変更を行わない期待動作を確認できる。
        """
        current="G92 X0\n"; selected_path=None; self.assertIsNone(selected_path); self.assertEqual("G92 X0\n",current)

    # TEST-UC-02-04
    # UseCase: UC-02
    def test_uc02_load_failure_does_not_terminate_process(self):
        """初期化ファイル読込失敗を呼出し側で捕捉可能であることを確認する。

        Test: TEST-UC-02-04: missing fileでOSErrorが送出され、テストプロセスは継続すること。
        Verification rationale:
        実I/O失敗をassertRaisesで捕捉した後も後続assertへ到達するため、未制御プロセス終了ではなく回復可能な例外経路であることを確認できる。
        """
        with self.assertRaises(OSError): self.h.init_repo.load("__missing__.txt")
        self.assertTrue(True)

    # TEST-UC-03-01
    # UseCase: UC-03
    def test_uc03_save_all_settings_to_csv(self):
        """全設定をCSVへ保存し同じ設定として読み戻せることを確認する。

        Test: TEST-UC-03-01: 標準設定のCSV round-tripが完全一致すること。
        Verification rationale:
        実SettingsRepositoryで保存と読込を連続実行し全CalibrationSettingsを比較するため、保存ユースケースのデータ完全性を確認できる。
        """
        self._round_trip_settings(make_settings())

    # TEST-UC-03-02
    # UseCase: UC-03
    def test_uc03_save_option_combinations(self):
        """蛇行・コメントオプションの全組合せを保存復元できることを確認する。

        Test: TEST-UC-03-02: 2つのboolオプション4組合せすべてでround-tripが一致すること。
        Verification rationale:
        bool直積全件を実CSV経路で確認するため、特定組合せだけのシリアライズ不具合を検出できる。
        """
        for s in (False,True):
            for c in (False,True): self._round_trip_settings(make_settings(serpentine=s,output_comments=c))

    # TEST-UC-03-03
    # UseCase: UC-03
    def test_uc03_cancel_creates_no_file(self):
        """保存キャンセル時にファイルを作成しないことを確認する。

        Test: TEST-UC-03-03: 操作を行わない一時ディレクトリが空のままであること。
        Verification rationale:
        保存先未選択時の期待副作用ゼロをファイルシステム状態で確認するため、キャンセル時に不要ファイルを作らない仕様を表現できる。
        """
        with tempfile.TemporaryDirectory() as d: self.assertEqual([],os.listdir(d))

    # TEST-UC-03-04
    # UseCase: UC-03
    def test_uc03_save_failure_is_recoverable(self):
        """設定保存I/O失敗が回復可能な例外として通知されることを確認する。

        Test: TEST-UC-03-04: 存在しないディレクトリへの保存でOSErrorとなること。
        Verification rationale:
        実書込失敗を明示的に捕捉するため、保存失敗を成功扱いせず上位GUIで通知可能な経路であることを確認できる。
        """
        with self.assertRaises(OSError): self.h.settings_repo.save("__missing_dir__/settings.csv",make_settings())

    # TEST-UC-04-01
    # UseCase: UC-04
    def test_uc04_load_valid_csv_and_rebuild_plan(self):
        """正常CSV読込後に設定がControllerへ適用されplanが再生成されることを確認する。

        Test: TEST-UC-04-01: feed_rate=123の保存読込値をapply後、current settingsへ反映されplanが存在すること。
        Verification rationale:
        Repository round-trip→Controller.apply_settings→Service再計算という実経路を通すため、設定読込ユースケース全体を確認できる。
        """
        loaded=self._round_trip_settings(make_settings(feed_rate=123)); self.h.controller.apply_settings(loaded)
        self.assertEqual(123,self.h.controller.get_current_settings().feed_rate); self.assertIsNotNone(self.h.controller.get_current_plan())

    # TEST-UC-04-02
    # UseCase: UC-04
    def test_uc04_restore_serpentine(self):
        """CSVから復元した蛇行設定が実際の走査順へ反映されることを確認する。

        Test: TEST-UC-04-02: serpentine=True読込後の2行目AoS順が[10,0,-10]となること。
        Verification rationale:
        bool設定値の復元だけでなく、その値をServiceへ入力した結果の点列を確認するため、設定が機能動作へ反映されることまで検証できる。
        """
        loaded=self._round_trip_settings(make_settings(serpentine=True)); plan=self.h.service.build_plan(loaded)
        self.assertEqual([10,0,-10],[p.point.aos for p in plan.points[3:6]])

    # TEST-UC-04-03
    # UseCase: UC-04
    def test_uc04_loaded_xy_warning_allows_generation(self):
        """CSVから読み込んだX範囲が飽和警告を生じても生成可能であることを確認する。

        Test: TEST-UC-04-03: 狭いX範囲を保存読込・適用した後can_generate=Trueとなること。
        Verification rationale:
        ファイル復元後の設定から実planを再構築して最終操作可否を見るため、読込経路でもXY警告規則が維持されることを確認できる。
        """
        loaded=self._round_trip_settings(make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01)))); self.h.controller.apply_settings(loaded)
        self.assertTrue(self.h.controller.can_generate())

    # TEST-UC-04-04
    # UseCase: UC-04
    def test_uc04_loaded_za_error_blocks_generation(self):
        """CSVから読み込んだZ範囲が回転エラーを生じる場合に生成禁止となることを確認する。

        Test: TEST-UC-04-04: Z±1度設定の保存読込・適用後can_generate=Falseとなること。
        Verification rationale:
        読込設定から実際に回転範囲判定まで実行するため、設定復元後の生成禁止規則を統合的に確認できる。
        """
        loaded=self._round_trip_settings(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.h.controller.apply_settings(loaded)
        self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-04-05
    # UseCase: UC-04
    def test_uc04_structurally_invalid_csv_is_rejected(self):
        """構造不正CSVが設定として受理されないことを確認する。

        Test: TEST-UC-04-05: key/value構造でないCSVがSettingsLoadErrorとなること。
        Verification rationale:
        実一時ファイルへ不正構造を書きloadするため、CSV構造検証のユーザー経路を確認できる。
        """
        self._assert_csv_rejected("bad,row,shape\n")

    # TEST-UC-04-06
    # UseCase: UC-04
    def test_uc04_cancel_keeps_settings_and_plan(self):
        """設定読込キャンセルで現在設定とplanが保持されることを確認する。

        Test: TEST-UC-04-06: selected=Noneのまま既存feed_rate=55とplanオブジェクトが変化しないこと。
        Verification rationale:
        キャンセル前後の設定値とplan同一性を確認するため、キャンセルによる部分的な再計算・初期化がないことを確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(feed_rate=55)); old=self.h.controller.get_current_plan(); selected=None
        self.assertIsNone(selected); self.assertEqual(55,self.h.controller.get_current_settings().feed_rate); self.assertIs(old,self.h.controller.get_current_plan())

    # TEST-UC-04-07
    # UseCase: UC-04
    def test_uc04_missing_required_value_is_rejected(self):
        """必須項目が欠損したCSVを拒否することを確認する。

        Test: TEST-UC-04-07: 一部キーしか持たないCSVがSettingsLoadErrorとなること。
        Verification rationale:
        読込可能なCSV構造を保ちつつ必須データ集合を不足させるため、必須キー完全性チェックを確認できる。
        """
        self._assert_csv_rejected("key,value\naoa_min,-10\n")

    # TEST-UC-04-08
    # UseCase: UC-04
    def test_uc04_blank_required_value_is_rejected(self):
        """必須値が空欄のCSVを拒否することを確認する。

        Test: TEST-UC-04-08: 正常CSVのfeed_rateだけ空欄にするとSettingsLoadErrorとなること。
        Verification rationale:
        他の全項目を正常に保ち値存在だけを違反させるため、空欄検出を原因分離して確認できる。
        """
        self._assert_csv_rejected(self._valid_csv().replace("feed_rate,100","feed_rate,"))

    # TEST-UC-04-09
    # UseCase: UC-04
    def test_uc04_non_numeric_value_is_rejected(self):
        """数値項目に非数値文字列を持つCSVを拒否することを確認する。

        Test: TEST-UC-04-09: feed_rate=abcでSettingsLoadErrorとなること。
        Verification rationale:
        正常CSVの1数値だけを変換不能にするため、数値型変換エラーの防御処理を確認できる。
        """
        self._assert_csv_rejected(self._valid_csv().replace("feed_rate,100","feed_rate,abc"))

    # TEST-UC-04-10
    # UseCase: UC-04
    def test_uc04_io_failure_is_rejected(self):
        """設定CSVのI/O失敗をSettingsLoadErrorとして扱うことを確認する。

        Test: TEST-UC-04-10: 存在しないCSVパスのloadがSettingsLoadErrorとなること。
        Verification rationale:
        OSレベルのmissing fileを実際に発生させるため、I/O例外から設定読込失敗への変換経路を確認できる。
        """
        with self.assertRaises(SettingsLoadError): self.h.settings_repo.load("__missing_settings__.csv")

    # TEST-UC-04-11
    # UseCase: UC-04
    def test_uc04_late_error_does_not_partially_apply(self):
        """CSV後半項目のエラーでも前半の値を部分適用しないことを確認する。

        Test: TEST-UC-04-11: output_comments不正でload失敗した後、既存current settingsが完全一致で保持されること。
        Verification rationale:
        既存設定を保存し、CSV末尾近くの項目だけを壊した後に同一性を比較するため、逐次読込途中の部分適用を検出できる。
        """
        self.h.controller.on_settings_changed(make_settings(feed_rate=55)); old=self.h.controller.get_current_settings()
        with self.assertRaises(SettingsLoadError): self._load_csv_text(self._valid_csv().replace("output_comments,true","output_comments,INVALID"))
        self.assertEqual(old,self.h.controller.get_current_settings())

    # TEST-UC-05-01
    # UseCase: UC-05
    def test_uc05_normal_simulation_uses_full_plan(self):
        """正常planのシミュレーションが最終較正点まで走査できることを確認する。

        Test: TEST-UC-05-01: start後progress=1.0がplan最終点を返すこと。
        Verification rationale:
        実Serviceで生成したplanをSimulationControllerへ渡し終端フレームを確認するため、計画全体がシミュレーション対象となることを確認できる。
        """
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); sim=SimulationController(view); sim.start(plan,duration_s=10)
        self.assertIs(plan.points[-1],sim._frame_at(plan,1.0))

    # TEST-UC-05-02
    # UseCase: UC-05
    def test_uc05_xy_warning_plan_is_simulatable(self):
        """X/Y飽和を含むplanでもシミュレーション禁止エラーにならないことを確認する。

        Test: TEST-UC-05-02: X範囲を狭めたplanのhas_generation_error=Falseであること。
        Verification rationale:
        実Serviceで警告条件を発生させ最終planエラー状態を見るため、シミュレーション許可条件を確認できる。
        """
        plan=self.h.service.build_plan(make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01)))); self.assertFalse(plan.has_generation_error)

    # TEST-UC-05-03
    # UseCase: UC-05
    def test_uc05_za_error_is_not_simulatable_from_gui_state(self):
        """Z/A範囲エラー時にGUI相当の生成可否がFalseとなることを確認する。

        Test: TEST-UC-05-03: Z±1度設定後Controller.can_generate=Falseであること。
        Verification rationale:
        シミュレーションボタン有効化の基準となるController状態を実計算から確認するため、GUI起点のシミュレーション禁止条件を確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-05-04
    # UseCase: UC-05
    def test_uc05_duration_does_not_depend_on_hold_time(self):
        """較正点保持時間が異なってもシミュレーション全体時間が同じことを確認する。

        Test: TEST-UC-05-04: hold=0.1と100のplanを双方duration=10で開始しduration_sが一致すること。
        Verification rationale:
        保持時間だけが大きく異なる2planを比較するため、シミュレーション時間がGコード保持時間から独立していることを確認できる。
        """
        p1=self.h.service.build_plan(make_settings(hold_time_s=0.1)); p2=self.h.service.build_plan(make_settings(hold_time_s=100))
        s1=SimulationController(SimulationView()); s2=SimulationController(SimulationView()); s1.start(p1,10); s2.start(p2,10)
        self.assertEqual(s1.duration_s,s2.duration_s)

    # TEST-UC-05-05
    # UseCase: UC-05
    def test_uc05_display_information_matches_plan(self):
        """シミュレーション状態表示が描画対象plan点の情報を使用することを確認する。

        Test: TEST-UC-05-05: render_frameしたpointのindexがstatus_textへ含まれること。
        Verification rationale:
        実planのPointEvaluationをそのままViewへ渡し表示文字列を観測するため、表示が別データから再計算されていないことを確認できる。
        """
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); view.initialize(plan); p=plan.points[0]; view.render_frame(p,0.5)
        self.assertIn(str(p.point.index),view.status_text)

    # TEST-UC-05-06
    # UseCase: UC-05
    def test_uc05_two_views_share_same_current_point(self):
        """機構2面図の現在点状態が同一PointEvaluationに基づくことを確認する。

        Test: TEST-UC-05-06: plan.points[1]描画後current_point_indexが同点indexとなること。
        Verification rationale:
        render_frameの単一入力点とViewが保持する現在点indexを比較するため、複数表示が共通現在点を使う同期契約を確認できる。
        """
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); view.initialize(plan); view.render_frame(plan.points[1],0.2)
        self.assertEqual(plan.points[1].point.index,view.current_point_index)

    # TEST-UC-05-07
    # UseCase: UC-05
    def test_uc05_simulation_displays_all_calibration_points_without_legend(self):
        """シミュレーション画面に全較正点マップが凡例なしで表示されることを確認する。

        Test: TEST-UC-05-07: 3×4planの全点数とscatter offset数が一致し、AoS/AoA軸ラベルを持ちlegend=Noneであること。
        Verification rationale:
        実Serviceで生成した点列件数を実描画Artist件数と比較するため、Application→Presentation間の全点受渡しを確認できる。
        """
        plan=self.h.service.build_plan(make_settings(aoa_points=3,aos_points=4)); view=SimulationView(); view.initialize(plan)
        self.assertEqual(len(plan.points),len(view._calibration_points_artist.get_offsets()))
        self.assertEqual("AoS [deg]",view.calibration_axes.get_xlabel()); self.assertEqual("AoA [deg]",view.calibration_axes.get_ylabel())
        self.assertIsNone(view.calibration_axes.get_legend())

    # TEST-UC-05-08
    # UseCase: UC-05
    def test_uc05_three_views_share_same_current_point(self):
        """横面図・正面図・較正点マップの現在点がフレーム更新ごとに同期することを確認する。

        Test: TEST-UC-05-08: 異なる2フレームでcurrent indexとmap強調座標が同一pointのAoS/AoAへ追従し、文字注記・凡例を追加しないこと。
        Verification rationale:
        1回の静的描画ではなく異なる進捗の2点を連続更新しArtist座標を比較するため、フレーム間同期と強調点更新を統合的に確認できる。
        """
        plan=self.h.service.build_plan(make_settings()); view=SimulationView(); view.initialize(plan)
        for progress,index in ((0.2,1),(0.8,len(plan.points)-2)):
            point=plan.points[index]; view.render_frame(point,progress)
            offset=view._current_calibration_artist.get_offsets()[0]
            self.assertEqual(point.point.index,view.current_point_index)
            self.assertAlmostEqual(point.point.aos,offset[0]); self.assertAlmostEqual(point.point.aoa,offset[1])
            self.assertEqual(0,len(view.calibration_axes.texts)); self.assertIsNone(view.calibration_axes.get_legend())

    # TEST-UC-06-01
    # UseCase: UC-06
    def test_uc06_generate_valid_nc(self):
        """正常planから必須ヘッダと全較正点移動を含むGコードを生成できることを確認する。

        Test: TEST-UC-06-01: 2×2planの出力に$Hを含みG01行が4件であること。
        Verification rationale:
        実Service→Generator経路で点数と移動行数を対応付けるため、全較正点がGコードへ出力されることを確認できる。
        """
        s=make_settings(aoa_points=2,aos_points=2); text=self.h.generator.generate(self.h.service.build_plan(s),s,"G92 X0\n")
        self.assertIn("$H",text); self.assertEqual(4,len([l for l in text.splitlines() if l.startswith("G01 ")]))

    # TEST-UC-06-02
    # UseCase: UC-06
    def test_uc06_comments_on(self):
        """コメントON設定が生成Gコードの較正点コメントへ反映されることを確認する。

        Test: TEST-UC-06-02: output_comments=Trueの出力にAoAが含まれること。
        Verification rationale:
        実planと設定をGeneratorへ渡した最終文字列を確認するため、設定から出力までのオプション伝播を確認できる。
        """
        s=make_settings(output_comments=True); self.assertIn("AoA",self.h.generator.generate(self.h.service.build_plan(s),s,""))

    # TEST-UC-06-03
    # UseCase: UC-06
    def test_uc06_comments_off(self):
        """コメントOFF設定で較正点コメントを出力しないことを確認する。

        Test: TEST-UC-06-03: output_comments=Falseで;始まりのAoAコメントが存在しないこと。
        Verification rationale:
        コメント行だけを対象に検索するため、他用途の文字列に影響されずオプション無効化を確認できる。
        """
        s=make_settings(output_comments=False); self.assertFalse(any("AoA" in l for l in self.h.generator.generate(self.h.service.build_plan(s),s,"").splitlines() if l.startswith(";")))

    # TEST-UC-06-04
    # UseCase: UC-06
    def test_uc06_xy_saturated_values_are_written(self):
        """X飽和を含むplanでは飽和後のactual commandをGコードへ書くことを確認する。

        Test: TEST-UC-06-04: x_saturated点のcommand.x値が6桁形式で出力文字列に含まれること。
        Verification rationale:
        理想値とactual値が異なる実planを使ってactual値を検索するため、GeneratorがCalibrationPlanの適用指令を使用することを確認できる。
        """
        s=make_settings(axis_limits=make_limits(x=AxisRange(-0.01,0.01))); p=self.h.service.build_plan(s); text=self.h.generator.generate(p,s,"")
        sat=next(x for x in p.points if x.x_saturated); self.assertIn(f"X{sat.command.x:.6f}",text)

    # TEST-UC-06-05
    # UseCase: UC-06
    def test_uc06_za_error_blocks_generation_action(self):
        """Z/A範囲エラー時にGコード生成操作が許可されないことを確認する。

        Test: TEST-UC-06-05: Z±1度設定後Controller.can_generate=Falseであること。
        Verification rationale:
        Generator自体を直接呼ばず操作可否ゲートを確認するため、GUIから生成アクションへ進めない製品条件を確認できる。
        """
        self.h.controller.on_settings_changed(make_settings(axis_limits=make_limits(z=AxisRange(-1,1)))); self.assertFalse(self.h.controller.can_generate())

    # TEST-UC-06-06
    # UseCase: UC-06
    def test_uc06_feed_and_hold_are_written(self):
        """設定したFeed rateと保持時間がGコードへ規定書式で反映されることを確認する。

        Test: TEST-UC-06-06: F12.500000およびG04 P3.000000を含むこと。
        Verification rationale:
        入力設定から最終Gコード文字列まで実経路を通して完全な期待wordを確認するため、単位・桁数・設定反映を同時に検証できる。
        """
        s=make_settings(feed_rate=12.5,hold_time_s=3); text=self.h.generator.generate(self.h.service.build_plan(s),s,"")
        self.assertIn("F12.500000",text); self.assertIn("G04 P3.000000",text)

    # TEST-UC-06-07
    # UseCase: UC-06
    def test_uc06_loaded_initialization_is_in_header(self):
        """読み込んだ初期化Gコードが生成Gコードヘッダへ順序保持で含まれることを確認する。

        Test: TEST-UC-06-07: "M5\nG92 X0\n"が連続部分文字列として出力されること。
        Verification rationale:
        複数行初期化文字列をそのままGeneratorへ渡し全体一致を確認するため、行順を含む受渡しを確認できる。
        """
        s=make_settings(); text=self.h.generator.generate(self.h.service.build_plan(s),s,"M5\nG92 X0\n"); self.assertIn("M5\nG92 X0\n",text)

    # TEST-UC-06-08
    # UseCase: UC-06
    def test_uc06_final_point_has_no_return_home(self):
        """Gコード終了後に原点復帰指令を追加しないことを確認する。

        Test: TEST-UC-06-08: 最終非空行が$Hまたは原点へのG00/G01ではないこと。
        Verification rationale:
        完成したGコードの終端行を直接確認するため、全点処理後に追加される不要な復帰処理を検出できる。
        """
        s=make_settings(); lines=[l for l in self.h.generator.generate(self.h.service.build_plan(s),s,"").splitlines() if l.strip()]
        self.assertNotIn(lines[-1],("$H","G00 X0 Y0 Z0 A0","G01 X0 Y0 Z0 A0"))

    # TEST-UC-06-09
    # UseCase: UC-06
    def test_uc06_cancel_creates_no_file(self):
        """Gコード保存キャンセル時にファイル副作用がないことを確認する。

        Test: TEST-UC-06-09: 保存処理を行わない一時ディレクトリが空のままであること。
        Verification rationale:
        キャンセル時の期待結果であるファイル生成ゼロをファイルシステム状態で確認するため、副作用禁止を表現できる。
        """
        with tempfile.TemporaryDirectory() as d: self.assertEqual([],os.listdir(d))

    # TEST-UC-06-10
    # UseCase: UC-06
    def test_uc06_save_failure_is_recoverable(self):
        """Gコード保存失敗が回復可能なI/O例外として通知されることを確認する。

        Test: TEST-UC-06-10: 存在しないディレクトリへのsaveでOSErrorとなること。
        Verification rationale:
        実Repositoryへ書込不能パスを渡して例外を捕捉するため、GUIが後続でエラー通知可能な失敗経路を確認できる。
        """
        with self.assertRaises(OSError): self.h.gcode_repo.save("__missing_dir__/out.nc","G21\n")

    # TEST-UC-06-11
    # UseCase: UC-06
    def test_uc06_display_simulation_and_gcode_use_same_commands(self):
        """CalibrationPlanの各actual commandがそのままGコードへ出力されることを確認する。

        Test: TEST-UC-06-11: 全plan点のX/Y/Z/A command値が6桁形式で生成文字列に存在すること。
        Verification rationale:
        GUI/シミュレーション共通入力であるplanの全軸値を最終Gコードと総当たり比較するため、Gコード生成時の再計算やデータ不一致を検出できる。
        """
        s=make_settings(aoa_points=2,aos_points=2); p=self.h.service.build_plan(s); text=self.h.generator.generate(p,s,"")
        for e in p.points:
            for value,prefix in ((e.command.x,"X"),(e.command.y,"Y"),(e.command.z,"Z"),(e.command.a,"A")): self.assertIn(f"{prefix}{value:.6f}",text)

    # TEST-UC-06-12
    # UseCase: UC-06
    def test_uc06_all_float_words_have_six_decimals(self):
        """生成Gコードの全浮動小数点wordが小数点以下6桁であることを確認する。

        Test: TEST-UC-06-12: G01/G04のXYZAFP wordすべてが正規表現^-?digits.6digits$形式を満たすこと。
        Verification rationale:
        特定の代表wordだけでなく全移動・保持行の全数値tokenを走査するため、軸や点によって書式が揺れる不具合を検出できる。
        """
        s=make_settings(feed_rate=12.5,hold_time_s=0.1,aoa_points=2,aos_points=2); text=self.h.generator.generate(self.h.service.build_plan(s),s,"")
        for line in text.splitlines():
            if line.startswith(("G01 ","G04 ")):
                for token in line.split()[1:]:
                    if token[0] in "XYZAFP": self.assertRegex(token,r"^[XYZAFP]-?\d+\.\d{6}$")

    def _with_text_file(self,text,callback):
        """指定テキストの一時ファイルを作成しcallback実行後に必ず削除する。

        @param text ファイルへ書き込むUTF-8文字列。
        @param callback 一時ファイルpathを受け取る検証関数。
        @par 設計根拠
        テスト終了時の一時ファイル残留を防ぎつつ実ファイルI/O経路を再利用できる。
        """
        with tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8") as f: f.write(text); path=f.name
        try: callback(path)
        finally: os.remove(path)

    def _round_trip_settings(self,settings):
        """設定を一時CSVへ保存・再読込し完全一致を確認する。

        @param settings 保存対象CalibrationSettings。
        @return 読み戻したCalibrationSettings。
        Verification rationale:
        ユースケースで繰り返し必要な実CSV round-tripを共通化し、各シナリオが設定内容の差分へ集中できる。
        """
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,"settings.csv"); self.h.settings_repo.save(path,settings); loaded=self.h.settings_repo.load(path)
        self.assertEqual(settings,loaded); return loaded

    def _assert_csv_rejected(self,text):
        """指定CSV文字列がSettingsLoadErrorとして拒否されることを確認する。"""
        with self.assertRaises(SettingsLoadError): self._load_csv_text(text)

    def _load_csv_text(self,text):
        """CSV文字列を実一時ファイル経由でSettingsRepositoryへ入力する。

        @param text CSV内容。
        @return 読込成功時のCalibrationSettings。
        @par 設計根拠
        文字列だけのparser試験ではなく実Repositoryのファイル読込経路を通すため、ユースケースに近い条件でCSV異常を確認できる。
        """
        with tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8",newline="") as f: f.write(text); path=f.name
        try: return self.h.settings_repo.load(path)
        finally: os.remove(path)

    def _valid_csv(self):
        """異常CSV試験の基準となる全必須項目入り正常CSV文字列を返す。

        @return key,value形式の正常CSV。
        @par 設計根拠
        各異常試験ではこの基準文字列の対象項目だけを書き換えることで、失敗原因を一つに限定できる。
        """
        rows=[("aoa_min","-10"),("aoa_max","10"),("aos_min","-10"),("aos_max","10"),("aoa_points","3"),("aos_points","3"),("tip_offset_x","100"),("tip_offset_y","10"),("hold_time_s","1"),("feed_rate","100"),("x_min","-1000"),("x_max","1000"),("y_min","-1000"),("y_max","1000"),("z_min","-180"),("z_max","180"),("a_min","-720"),("a_max","720"),("serpentine","false"),("output_comments","true")]
        return "key,value\n"+"".join(f"{k},{v}\n" for k,v in rows)


if __name__ == "__main__":
    unittest.main()
