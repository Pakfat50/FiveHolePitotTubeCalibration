"""シミュレーション制御・表示の単体テスト。

@file test_simulation.py
@brief SimulationController のフレーム選択と SimulationView の横面図・正面図・状態表示・較正点マップ同期を検証する。
@details docs/test_specification.md の TEST-UNIT-093..099,122,123 に対応する。
"""

import math
import unittest
from unittest.mock import Mock

from simulation import SimulationController, SimulationView


class TestSimulation(unittest.TestCase):
    """@brief シミュレーションが同一planの走査順と現在点を正しく可視化することを確認する。"""

    def setUp(self):
        """@brief Controller用Mock Viewと、View描画にも利用できる代表的なplanを準備する。"""
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

    # TEST-UNIT-093
    # Requirements: REQ-SIM-002
    def test_start_frame_is_first_point(self):
        """@brief 再生進捗0.0が最初の較正点へ対応することを確認する。

        @test TEST-UNIT-093: _frame_at(plan,0.0)がpoints[0]を返すこと。
        @par 検証根拠
        正規化進捗の始端を直接入力して同一オブジェクト参照を確認するため、開始フレームのマッピングを一意に検証できる。
        @see REQ-SIM-002
        """
        self.assertIs(self.points[0], self.controller._frame_at(self.plan, 0.0))

    # TEST-UNIT-094
    # Requirements: REQ-SIM-002
    def test_end_frame_is_last_point(self):
        """@brief 再生進捗1.0が最後の較正点へ対応することを確認する。

        @test TEST-UNIT-094: _frame_at(plan,1.0)がpoints[-1]を返すこと。
        @par 検証根拠
        正規化進捗の終端と走査列終端を直接対応付けるため、最終点が再生から欠落しないことを確認できる。
        @see REQ-SIM-002
        """
        self.assertIs(self.points[-1], self.controller._frame_at(self.plan, 1.0))

    # TEST-UNIT-095
    # Requirements: REQ-SIM-002
    def test_middle_progress_maps_to_scan_order(self):
        """@brief 中間進捗が走査順の中央点へ対応することを確認する。

        @test TEST-UNIT-095: 5点planのprogress=0.5でpoints[2]を返すこと。
        @par 検証根拠
        始端・終端以外の代表点を確認することで、単純な端点特例ではなく走査順全体の進捗マッピング式を検証できる。
        @see REQ-SIM-002
        """
        self.assertIs(self.points[2], self.controller._frame_at(self.plan, 0.5))

    # TEST-UNIT-096
    # Requirements: REQ-SIM-002
    def test_playback_duration_is_independent_of_hold_time(self):
        """@brief シミュレーション再生時間がplanの保持時間ではなく指定duration_sで決まることを確認する。

        @test TEST-UNIT-096: start(plan,10.0)がViewへduration_s=10.0と同一planを渡し、frame_providerが始端・終端を正しく返すこと。
        @par 検証根拠
        ControllerがViewへ渡す再生設定と生成したframe_providerを直接観測するため、Gコード保持時間に依存しない約10秒再生構成を確認できる。
        @see REQ-SIM-002
        """
        self.controller.start(self.plan, duration_s=10.0)
        self.assertEqual(10.0, self.controller.duration_s)
        self.view.start_animation.assert_called_once()
        kwargs = self.view.start_animation.call_args.kwargs
        self.assertIs(self.plan, kwargs["plan"])
        self.assertEqual(10.0, kwargs["duration_s"])
        self.assertIs(self.points[0], kwargs["frame_provider"](0.0))
        self.assertIs(self.points[-1], kwargs["frame_provider"](1.0))

    # TEST-UNIT-097
    # Requirements: REQ-SIM-003
    def test_side_view_is_initialized(self):
        """@brief 横面図がLx/LyのL字形状を実ピッチ角で剛体回転して表示することを確認する。

        @test TEST-UNIT-097: Z=0でpivot→Ly→Lxの基準L字となり、Z=30度では両線分が理論回転座標へ移ること。表示範囲は固定され、不要なLx/Ly/先端/中心文字や寸法矢印を持たず、先端方向矢印は1本だけであること。
        @details Lx=100,Ly=20について基準姿勢と30度姿勢の線分端点をMatplotlib Line2Dから取得し、回転式で独立計算した座標と比較する。
        @par 検証根拠
        見た目の画像比較ではなく、描画に使用された2線分の数値座標を仕様幾何と直接比較するため、L字の構造・回転方向・寸法反映を精密に検証できる。さらにAxes範囲、文字Artist、矢印Artistを直接観測することで、表示上の禁止要素と固定スケールも確認できる。
        @see REQ-SIM-003
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

    # TEST-UNIT-098
    # Requirements: REQ-SIM-003
    def test_front_view_is_initialized(self):
        """@brief 正面図がロール方向を中心から外周への半径矢印だけで表示することを確認する。

        @test TEST-UNIT-098: 軸ラベル・数値目盛を持たず固定範囲を維持し、矢印始点が中心、終点半径が1.0で、方向説明文字を表示しないこと。
        @details 複数フレーム描画後にAxes範囲、ticks、Annotation座標、Text内容を取得して比較する。
        @par 検証根拠
        ロール方向を表すAnnotationの幾何を直接測定するため、直径線への退行や逆方向表示を検出できる。不要情報もAxesの公開Artistから確認することで表示仕様を自動検証できる。
        @see REQ-SIM-003
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

    # TEST-UNIT-099
    # Requirements: REQ-SIM-004
    def test_render_frame_updates_required_information(self):
        """@brief 現在点情報と進捗表示がrender_frameで更新されることを確認する。

        @test TEST-UNIT-099: point番号、AoA/AoS、X/Y/Z/A、50%進捗がstatus_textに反映され、progress bar終点が0.50になること。
        @par 検証根拠
        各値を互いに異なる数値に設定して文字列中の存在と進捗Artist座標を確認するため、フィールド取り違えや更新漏れを検出できる。
        @see REQ-SIM-004
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

    # TEST-UNIT-122
    # Requirements: REQ-SIM-005
    def test_calibration_map_displays_all_points_without_legend(self):
        """@brief シミュレーション較正点マップが全点をAoS横軸・AoA縦軸で凡例なし表示することを確認する。

        @test TEST-UNIT-122: 全plan点の(AoS,AoA)座標集合とscatter offsetsが一致し、軸ラベルが単位付きで凡例を持たないこと。
        @par 検証根拠
        描画済みscatterの実座標集合をplanの全点から構成した期待集合と比較するため、点の欠落・軸逆転・余分な点を直接検出できる。
        @see REQ-SIM-005
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

    # TEST-UNIT-123
    # Requirements: REQ-SIM-006
    def test_current_calibration_point_color_tracks_rendered_point(self):
        """@brief 現在較正点の強調がrender_frame対象点へ同期し、色だけで識別されることを確認する。

        @test TEST-UNIT-123: 2つの異なる点を連続描画したときcurrent scatter座標とcurrent_point_indexが各点へ追従し、通常点と色が異なり、文字注記・凡例を追加しないこと。
        @details 現在点Artistのoffsetとfacecolorを直接取得し、2回のrender_frame前後で比較する。
        @par 検証根拠
        同一Artistが異なる点へ実際に移動することを観測するため、初期表示だけでなくフレーム間同期を検証できる。また通常点ArtistとのRGBA比較とText/Legend不在確認により、色のみ強調という仕様を直接確認できる。
        @see REQ-SIM-006
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


if __name__ == "__main__":
    unittest.main()
