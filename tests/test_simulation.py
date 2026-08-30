"""シミュレーション制御・表示の単体テスト。

File: test_simulation.py
SimulationController のフレーム選択と SimulationView の横面図・正面図・状態表示・較正点マップ同期を検証する。
docs/test_specification.md の TEST-UNIT-093..099,122,123 に対応する。
"""

import math
import unittest
from unittest.mock import Mock

from simulation import SimulationController, SimulationView


class TestSimulation(unittest.TestCase):
    """シミュレーションが同一planの走査順と現在点を正しく可視化することを確認する。"""

    def setUp(self):
        """Controller用Mock Viewと、View描画にも利用できる代表的なplanを準備する。"""
        self.view = Mock(spec=SimulationView)
        self.controller = SimulationController(self.view)
        self.points = [
            Mock(
                point=Mock(index=i, aoa=float(i), aos=float(i)),
                command=Mock(x=float(i), y=float(i), z=float(i), a=float(i)),
                rotational_error=False,
                x_saturated=False,
                y_saturated=False,
            )
            for i in range(5)
        ]
        self.plan = Mock(
            points=self.points,
            settings=Mock(tip_offset_x=100.0, tip_offset_y=20.0),
        )

    def test_start_frame_is_first_point(self):
        """TEST-UNIT-093

        テスト目的:
            再生進捗0.0が最初の較正点へ対応することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            _frame_at(plan,0.0)がpoints[0]を返すこと。

        検証根拠:
            正規化進捗の始端を直接入力して同一オブジェクト参照を確認するため、開始フレームのマッピングを一意に検証できる。
        """
        self.assertIs(self.points[0], self.controller._frame_at(self.plan, 0.0))

    def test_end_frame_is_last_point(self):
        """TEST-UNIT-094

        テスト目的:
            再生進捗1.0が最後の較正点へ対応することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            _frame_at(plan,1.0)がpoints[-1]を返すこと。

        検証根拠:
            正規化進捗の終端と走査列終端を直接対応付けるため、最終点が再生から欠落しないことを確認できる。
        """
        self.assertIs(self.points[-1], self.controller._frame_at(self.plan, 1.0))

    def test_middle_progress_maps_to_scan_order(self):
        """TEST-UNIT-095

        テスト目的:
            中間進捗が走査順の中央点へ対応することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            5点planのprogress=0.5でpoints[2]を返すこと。

        検証根拠:
            始端・終端以外の代表点を確認することで、単純な端点特例ではなく走査順全体の進捗マッピング式を検証できる。
        """
        self.assertIs(self.points[2], self.controller._frame_at(self.plan, 0.5))

    def test_playback_duration_is_independent_of_hold_time(self):
        """TEST-UNIT-096

        テスト目的:
            シミュレーション再生時間がplanの保持時間ではなく指定duration_sで決まることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            start(plan,10.0)がViewへduration_s=10.0と同一planを渡し、frame_providerが始端・終端を正しく返すこと。

        検証根拠:
            ControllerがViewへ渡す再生設定と生成したframe_providerを直接観測するため、Gコード保持時間に依存しない約10秒再生構成を確認できる。
        """
        self.controller.start(self.plan, duration_s=10.0)
        self.assertEqual(10.0, self.controller.duration_s)
        self.view.start_animation.assert_called_once()
        kwargs = self.view.start_animation.call_args.kwargs
        self.assertIs(self.plan, kwargs["plan"])
        self.assertEqual(10.0, kwargs["duration_s"])
        self.assertIs(self.points[0], kwargs["frame_provider"](0.0))
        self.assertIs(self.points[-1], kwargs["frame_provider"](1.0))

    def test_side_view_is_initialized(self):
        """TEST-UNIT-097

        テスト目的:
            横面図がLx/LyのL字形状を実ピッチ角で剛体回転して表示することを確認する。

        テスト手順:
            1. Lx=100,Ly=20について基準姿勢と30度姿勢の線分端点をMatplotlib Line2Dから取得し、回転式で独立計算した座標と比較する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            Z=0でpivot→Ly→Lxの基準L字となり、Z=30度では両線分が理論回転座標へ移ること。表示範囲は固定され、不要なLx/Ly/先端/中心文字や寸法矢印を持たず、先端方向矢印は1本だけであること。

        検証根拠:
            見た目の画像比較ではなく、描画に使用された2線分の数値座標を仕様幾何と直接比較するため、L字の構造・回転方向・寸法反映を精密に検証できる。さらにAxes範囲、文字Artist、矢印Artistを直接観測することで、表示上の禁止要素と固定スケールも確認できる。
        """
        view = SimulationView()
        view.initialize(self.plan)
        self.assertTrue(hasattr(view, "side_axes"))
        initial_xlim = view.side_axes.get_xlim()
        initial_ylim = view.side_axes.get_ylim()

        zero_point = Mock(
            point=Mock(index=0, aoa=0.0, aos=0.0),
            command=Mock(x=0.0, y=0.0, z=0.0, a=0.0),
            rotational_error=False,
            x_saturated=False,
            y_saturated=False,
        )
        view.render_frame(zero_point, 0.0)
        first_xlim = view.side_axes.get_xlim()
        first_ylim = view.side_axes.get_ylim()

        self.assertGreaterEqual(len(view.side_axes.lines), 2)
        ly_line = view.side_axes.lines[0]
        lx_line = view.side_axes.lines[1]
        self.assertEqual([0.0, 0.0], list(ly_line.get_xdata()))
        self.assertEqual([0.0, 20.0], list(ly_line.get_ydata()))
        self.assertEqual([0.0, 100.0], list(lx_line.get_xdata()))
        self.assertEqual([20.0, 20.0], list(lx_line.get_ydata()))

        tilted_point = Mock(
            point=Mock(index=4, aoa=30.0, aos=0.0),
            command=Mock(x=4.0, y=4.0, z=30.0, a=0.0),
            rotational_error=False,
            x_saturated=False,
            y_saturated=False,
        )
        view.render_frame(tilted_point, 1.0)

        theta = math.radians(30.0)
        expected_elbow_x = 4.0 - 20.0 * math.sin(theta)
        expected_elbow_y = 4.0 + 20.0 * math.cos(theta)
        expected_tip_x = expected_elbow_x + 100.0 * math.cos(theta)
        expected_tip_y = expected_elbow_y + 100.0 * math.sin(theta)

        ly_line = view.side_axes.lines[0]
        lx_line = view.side_axes.lines[1]
        self.assertAlmostEqual(4.0, ly_line.get_xdata()[0], places=6)
        self.assertAlmostEqual(4.0, ly_line.get_ydata()[0], places=6)
        self.assertAlmostEqual(expected_elbow_x, ly_line.get_xdata()[1], places=6)
        self.assertAlmostEqual(expected_elbow_y, ly_line.get_ydata()[1], places=6)
        self.assertAlmostEqual(expected_elbow_x, lx_line.get_xdata()[0], places=6)
        self.assertAlmostEqual(expected_elbow_y, lx_line.get_ydata()[0], places=6)
        self.assertAlmostEqual(expected_tip_x, lx_line.get_xdata()[1], places=6)
        self.assertAlmostEqual(expected_tip_y, lx_line.get_ydata()[1], places=6)

        self.assertEqual(initial_xlim, first_xlim)
        self.assertEqual(initial_ylim, first_ylim)
        self.assertEqual(initial_xlim, view.side_axes.get_xlim())
        self.assertEqual(initial_ylim, view.side_axes.get_ylim())

        labels = [text.get_text() for text in view.side_axes.texts]
        for prohibited in ("Lx", "Ly", "先端", "Tip", "ピッチ中心", "Pitch center"):
            self.assertFalse(any(prohibited in label for label in labels))

        arrows = [
            text for text in view.side_axes.texts
            if getattr(text, "arrow_patch", None) is not None
        ]
        self.assertEqual(1, len(arrows))
        tip_arrow = arrows[0]
        self.assertAlmostEqual(expected_tip_x, tip_arrow.xy[0], places=6)
        self.assertAlmostEqual(expected_tip_y, tip_arrow.xy[1], places=6)

    def test_front_view_is_initialized(self):
        """TEST-UNIT-098

        テスト目的:
            正面図がロール方向を中心から外周への半径矢印だけで表示することを確認する。

        テスト手順:
            1. 複数フレーム描画後にAxes範囲、ticks、Annotation座標、Text内容を取得して比較する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            軸ラベル・数値目盛を持たず固定範囲を維持し、矢印始点が中心、終点半径が1.0で、方向説明文字を表示しないこと。

        検証根拠:
            ロール方向を表すAnnotationの幾何を直接測定するため、直径線への退行や逆方向表示を検出できる。不要情報もAxesの公開Artistから確認することで表示仕様を自動検証できる。
        """
        view = SimulationView()
        view.initialize(self.plan)
        self.assertTrue(hasattr(view, "front_axes"))
        initial_xlim = view.front_axes.get_xlim()
        initial_ylim = view.front_axes.get_ylim()

        view.render_frame(self.points[0], 0.0)
        first_xlim = view.front_axes.get_xlim()
        first_ylim = view.front_axes.get_ylim()
        view.render_frame(self.points[-1], 1.0)

        self.assertGreaterEqual(len(view.front_axes.lines), 1)
        self.assertEqual(initial_xlim, first_xlim)
        self.assertEqual(initial_ylim, first_ylim)
        self.assertEqual(initial_xlim, view.front_axes.get_xlim())
        self.assertEqual(initial_ylim, view.front_axes.get_ylim())
        self.assertEqual("", view.front_axes.get_xlabel())
        self.assertEqual("", view.front_axes.get_ylabel())
        self.assertEqual([], list(view.front_axes.get_xticks()))
        self.assertEqual([], list(view.front_axes.get_yticks()))

        arrows = [
            text for text in view.front_axes.texts
            if getattr(text, "arrow_patch", None) is not None
        ]
        self.assertEqual(1, len(arrows))
        roll_arrow = arrows[0]
        self.assertAlmostEqual(0.0, roll_arrow.xyann[0], places=6)
        self.assertAlmostEqual(0.0, roll_arrow.xyann[1], places=6)
        self.assertAlmostEqual(1.0, math.hypot(*roll_arrow.xy), places=6)
        self.assertFalse(any(text.get_text() in ("先端", "Tip", "先端方向", "Tip direction") for text in view.front_axes.texts))

    def test_render_frame_updates_required_information(self):
        """TEST-UNIT-099

        テスト目的:
            現在点情報と進捗表示がrender_frameで更新されることを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            point番号、AoA/AoS、X/Y/Z/A、50%進捗がstatus_textに反映され、progress bar終点が0.50になること。

        検証根拠:
            各値を互いに異なる数値に設定して文字列中の存在と進捗Artist座標を確認するため、フィールド取り違えや更新漏れを検出できる。
        """
        view = SimulationView()
        view.initialize(self.plan)
        point = Mock(
            point=Mock(index=3, aoa=1.0, aos=2.0),
            command=Mock(x=3.0, y=4.0, z=5.0, a=6.0),
            rotational_error=False,
            x_saturated=False,
            y_saturated=False,
        )
        view.render_frame(point, 0.5)
        text = view.status_text
        for token in ("4", "1.00", "2.00", "3.00", "4.00", "5.00", "6.00", "50"):
            self.assertIn(token, text)
        xdata = list(view._progress_artist.get_xdata())
        self.assertAlmostEqual(0.50, xdata[-1], places=2)

    def test_calibration_map_displays_all_points_without_legend(self):
        """TEST-UNIT-122

        テスト目的:
            シミュレーション較正点マップが全点をAoS横軸・AoA縦軸で凡例なし表示することを確認する。

        テスト手順:
            1. テスト対象の処理を実行し、結果を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            全plan点の(AoS,AoA)座標集合とscatter offsetsが一致し、軸ラベルが単位付きで凡例を持たないこと。

        検証根拠:
            描画済みscatterの実座標集合をplanの全点から構成した期待集合と比較するため、点の欠落・軸逆転・余分な点を直接検出できる。
        """
        view = SimulationView()
        view.initialize(self.plan)

        self.assertIsNotNone(view.calibration_axes)
        self.assertEqual("AoS [deg]", view.calibration_axes.get_xlabel())
        self.assertEqual("AoA [deg]", view.calibration_axes.get_ylabel())
        offsets = view._calibration_points_artist.get_offsets()
        self.assertEqual(len(self.points), len(offsets))
        expected = {(float(point.point.aos), float(point.point.aoa)) for point in self.points}
        actual = {(float(x), float(y)) for x, y in offsets}
        self.assertEqual(expected, actual)
        self.assertIsNone(view.calibration_axes.get_legend())

    def test_current_calibration_point_color_tracks_rendered_point(self):
        """TEST-UNIT-123

        テスト目的:
            現在較正点の強調がrender_frame対象点へ同期し、色だけで識別されることを確認する。

        テスト手順:
            1. 現在点Artistのoffsetとfacecolorを直接取得し、2回のrender_frame前後で比較する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            2つの異なる点を連続描画したときcurrent scatter座標とcurrent_point_indexが各点へ追従し、通常点と色が異なり、文字注記・凡例を追加しないこと。

        検証根拠:
            同一Artistが異なる点へ実際に移動することを観測するため、初期表示だけでなくフレーム間同期を検証できる。また通常点ArtistとのRGBA比較とText/Legend不在確認により、色のみ強調という仕様を直接確認できる。
        """
        view = SimulationView()
        view.initialize(self.plan)

        view.render_frame(self.points[1], 0.25)
        first_offset = view._current_calibration_artist.get_offsets()[0]
        self.assertAlmostEqual(self.points[1].point.aos, first_offset[0])
        self.assertAlmostEqual(self.points[1].point.aoa, first_offset[1])
        self.assertEqual(self.points[1].point.index, view.current_point_index)

        normal_color = view._calibration_points_artist.get_facecolors()[0]
        current_color = view._current_calibration_artist.get_facecolors()[0]
        self.assertFalse((normal_color == current_color).all())

        view.render_frame(self.points[4], 0.75)
        second_offset = view._current_calibration_artist.get_offsets()[0]
        self.assertAlmostEqual(self.points[4].point.aos, second_offset[0])
        self.assertAlmostEqual(self.points[4].point.aoa, second_offset[1])
        self.assertEqual(self.points[4].point.index, view.current_point_index)
        self.assertEqual(0, len(view.calibration_axes.texts))
        self.assertIsNone(view.calibration_axes.get_legend())


    def test_start_sets_playing_state_at_first_point(self):
        """TEST-UNIT-126

        テスト目的:
            開始時に先頭点・再生中状態・一時停止ボタンが設定される。

        テスト手順:
            1. start()を実行し、Controllerの状態とViewへの再生状態通知を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            有効planの開始後に先頭インデックス、playing状態、状態通知を確認する。

        検証根拠:
            開始処理が再生位置と再生状態を初期化し、Viewの操作ボタン表示制御へ伝達する経路を直接検証する。 Preconditions: 複数の較正点を含むplanとViewモックが準備されている Postconditions: 先頭点が選択され、再生状態がplayingになる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.assertEqual("playing", self.controller.playback_state)
        self.assertEqual(0, self.controller.current_point_index)
        self.view.set_playback_state.assert_called_with("playing")

    def test_pause_stops_animation_and_keeps_current_point(self):
        """TEST-UNIT-127

        テスト目的:
            一時停止で現在点を保持し、タイマーを停止する。

        テスト手順:
            1. 再生中のControllerを現在点2へ設定して一時停止し、状態・インデックス・View呼び出しを検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            現在点インデックスを保持してpause()が呼び出されることを確認する。

        検証根拠:
            一時停止処理が再生位置を変更せず、アニメーションタイマーだけを停止することを直接確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.current_point_index = 2
        self.controller.pause()
        self.assertEqual("paused", self.controller.playback_state)
        self.assertEqual(2, self.controller.current_point_index)
        self.view.pause_animation.assert_called_once()
        self.view.set_playback_state.assert_called_with("paused")

    def test_resume_restarts_from_current_point(self):
        """TEST-UNIT-128

        テスト目的:
            一時停止から現在位置で再生を再開する。

        テスト手順:
            1. 現在点2で一時停止した後に再開し、再生状態・位置・View呼び出しを検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            resume()が現在位置でViewの再開処理を呼び出すことを確認する。

        検証根拠:
            一時停止からの再開で先頭へ戻らず、保持した位置から再生する仕様を確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.current_point_index = 2
        self.controller.pause()
        self.controller.resume()
        self.assertEqual("playing", self.controller.playback_state)
        self.assertEqual(2, self.controller.current_point_index)
        self.view.resume_animation.assert_called_once()

    def test_seek_while_paused_selects_point(self):
        """TEST-UNIT-129

        テスト目的:
            一時停止中のシークが指定点を保持する。

        テスト手順:
            1. 一時停止中に点3へシークし、状態・現在点・描画対象・正規化進捗を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            指定インデックス3が進捗0.75として描画されることを確認する。

        検証根拠:
            較正点単位のシーク結果をController状態とView描画引数の双方で確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.pause()
        self.controller.seek_to_point(3)
        self.assertEqual("paused", self.controller.playback_state)
        self.assertEqual(3, self.controller.current_point_index)
        self.view.render_frame.assert_called()
        point, progress = self.view.render_frame.call_args.args
        self.assertIs(self.points[3], point)
        self.assertAlmostEqual(0.75, progress)

    def test_seek_while_playing_pauses_automatically(self):
        """TEST-UNIT-130

        テスト目的:
            再生中のシーク開始で自動一時停止する。

        テスト手順:
            1. 再生中に点3へシークし、タイマー停止、状態遷移、指定点選択を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            シーク前にViewの停止処理が1回呼び出されることを確認する。

        検証根拠:
            操作時に自動一時停止する要求を、停止処理の呼び出しと最終状態から直接確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.seek_to_point(3)
        self.assertEqual("paused", self.controller.playback_state)
        self.view.pause_animation.assert_called_once()
        self.view.set_playback_state.assert_called_with("paused")

    def test_seek_renders_selected_point_immediately(self):
        """TEST-UNIT-131

        テスト目的:
            シーク時に指定点の描画と進捗が即時更新される。

        テスト手順:
            1. 点4へのシーク直後にrender_frameの引数を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            最終点の描画と進捗1.0を確認する。

        検証根拠:
            操作完了を待たずに指定点と終端進捗が描画へ反映されることを直接確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.view.reset_mock()
        self.controller.seek_to_point(4)
        self.view.render_frame.assert_called_once_with(self.points[4], 1.0)

    def test_animation_completion_stays_at_last_point(self):
        """TEST-UNIT-132

        テスト目的:
            再生完了で最終点に留まり、自動ループしない。

        テスト手順:
            1. 完了コールバックを実行し、最終点保持、完了状態、View通知を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            completed状態と最終インデックスを確認する。

        検証根拠:
            完了後に先頭へ自動復帰せず、最後の位置で一時停止相当の完了状態になることを確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.on_animation_complete()
        self.assertEqual("completed", self.controller.playback_state)
        self.assertEqual(4, self.controller.current_point_index)
        self.view.set_playback_state.assert_called_with("completed")

    def test_resume_after_completion_restarts_at_first_point(self):
        """TEST-UNIT-133

        テスト目的:
            完了後の再生で先頭へ戻る。

        テスト手順:
            1. 完了状態から再生を実行し、先頭点描画と再生状態を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            先頭点と進捗0.0の描画を確認する。

        検証根拠:
            完了後の再生操作でのみ先頭へ戻る仕様を、描画対象と進捗から確認できる。
        """

        self.controller.start(self.plan, duration_s=10.0)
        self.controller.on_animation_complete()
        self.controller.resume()
        self.assertEqual("playing", self.controller.playback_state)
        self.assertEqual(0, self.controller.current_point_index)
        self.view.render_frame.assert_called()
        point, progress = self.view.render_frame.call_args.args
        self.assertIs(self.points[0], point)
        self.assertEqual(0.0, progress)

    def test_view_has_point_based_seek_bar_with_large_handle(self):
        """TEST-UNIT-134

        テスト目的:
            シークバーが既存進捗表示を置換し、点単位・大きなつまみを持つ。

        テスト手順:
            1. Sliderの範囲、ステップ、つまみサイズ、再生ボタンの生成状態を検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            最小/最大値、整数分解能相当の構成、大きなつまみを確認する。

        検証根拠:
            較正点単位でドラッグ操作できる範囲と、操作しやすい大きさのつまみをUI部品の設定値から確認できる。
        """

        view = SimulationView()
        view.initialize(self.plan)
        self.assertIsNotNone(view.seek_slider)
        self.assertEqual(0, view.seek_slider.valmin)
        self.assertEqual(4, view.seek_slider.valmax)
        self.assertGreaterEqual(view.seek_slider.handle.get_markersize(), 10)
        self.assertEqual("s", view.seek_slider.handle.get_marker())
        self.assertFalse(view.seek_slider.valtext.get_visible())
        self.assertIsNot(view.seek_slider.ax, view._status_artist.axes)
        self.assertIsNotNone(view.playback_button)

    def test_playback_button_label_follows_state(self):
        """TEST-UNIT-135

        テスト目的:
            再生状態に応じて一時停止/再生ボタン表示を切り替える。

        テスト手順:
            1. 各再生状態を設定し、Buttonラベルを取得して比較する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            playingでは「Ⅱ」、paused/completedでは「▶」を確認する。

        検証根拠:
            状態と表示ラベルの対応を直接確認することで、再生中の一時停止操作と停止中の再生操作を検証できる。
        """

        view = SimulationView()
        view.initialize(self.plan)
        view.set_playback_state("playing")
        self.assertIn("Ⅱ", view.playback_button.label.get_text())
        view.set_playback_state("paused")
        self.assertIn("▶", view.playback_button.label.get_text())
        view.set_playback_state("completed")
        self.assertIn("▶", view.playback_button.label.get_text())

    def test_progress_text_uses_point_count_not_time(self):
        """TEST-UNIT-136

        テスト目的:
            進捗表示が現在点/全点であり、時間表示を使用しない。

        テスト手順:
            1. 中間点を描画し、status_textに点数表示が含まれ、時間表記が含まれないことを検証する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            5点中3点の表示と時間表記の不在を確認する。

        検証根拠:
            シークバーと同じ意味を持つ進捗情報が時間ではなく較正点単位で表示されることを確認できる。
        """

        view = SimulationView()
        view.initialize(self.plan)
        view.render_frame(self.points[2], 0.5)
        self.assertIn("3 / 5", view.status_text)
        self.assertNotIn("10.0 s", view.status_text)


if __name__ == "__main__":
    unittest.main()
