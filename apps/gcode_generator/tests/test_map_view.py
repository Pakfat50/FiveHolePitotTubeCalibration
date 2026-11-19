"""メインGUI較正点マップ表示の単体テスト。

File: test_map_view.py
CalibrationMapView の軸方向、飽和点、回転エラー点、日本語フォント選択を検証する。
docs/test_specification.md に対応する較正点マップ表示テストを実装する。
"""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from matplotlib import rcParams
from matplotlib.colors import to_rgba

from map_view import CalibrationMapView


class TestCalibrationMapView(unittest.TestCase):
    """較正点の状態と日本語表示がGUI上で仕様どおり描画されることを確認する。"""

    def setUp(self):
        """各テストで独立した CalibrationMapView を生成する。"""
        self.view = CalibrationMapView()

    def test_axes_are_aos_horizontal_aoa_vertical(self):
        """TEST-UNIT-090

        テスト目的:
            較正点マップの横軸がAoS、縦軸がAoAであることを確認する。

        テスト手順:
            1. 点を含まないplanを描画し、軸設定だけを分離して観測する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            render後のxlabel="AoS"、ylabel="AoA"であること。

        検証根拠:
            Matplotlib Axesの公開ラベル値を直接確認するため、表示軸の取り違えを確実に検出できる。
        """
        plan = Mock(points=[])
        self.view.render(plan)
        self.assertEqual("AoS", self.view.axes.get_xlabel())
        self.assertEqual("AoA", self.view.axes.get_ylabel())

    def test_saturated_points_use_distinct_visual_group(self):
        """TEST-UNIT-091

        テスト目的:
            X/Y飽和点が正常点と異なる色グループで描画されることを確認する。

        テスト手順:
            1. 状態以外の条件を単純化した2点を描画し、collection数とfacecolorを確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            正常点と飽和点を同時描画したときNORMAL_COLORとSATURATED_COLORの2 collectionが存在すること。

        検証根拠:
            正常点・警告点を同一図上で比較し実際の描画色をRGBA値で照合するため、視覚的識別性をプログラム的に直接検証できる。
        """
        normal = Mock(point=Mock(aos=0, aoa=0), x_saturated=False, y_saturated=False, rotational_error=False)
        saturated = Mock(point=Mock(aos=1, aoa=1), x_saturated=True, y_saturated=False, rotational_error=False)
        self.view.render(Mock(points=[normal, saturated]))
        self.assertEqual(2, len(self.view.axes.collections))
        colors = [tuple(collection.get_facecolors()[0]) for collection in self.view.axes.collections]
        self.assertIn(to_rgba(self.view.NORMAL_COLOR), colors)
        self.assertIn(to_rgba(self.view.SATURATED_COLOR), colors)

    def test_rotational_error_points_use_distinct_visual_group_without_third_color(self):
        """TEST-UNIT-092

        テスト目的:
            Z/A生成禁止点が識別可能で、不要な第3色を導入しないことを確認する。

        テスト手順:
            1. edgecolor集合とlegend labelを同時に確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            正常点と回転エラー点が別collectionとなり、色は通常色のまま生成禁止ラベルで識別できること。

        検証根拠:
            色設計と生成禁止の意味表示を別々に観測するため、エラー点が識別可能でありながら規定外色を追加していないことを確認できる。
        """
        normal = Mock(point=Mock(aos=0, aoa=0), x_saturated=False, y_saturated=False, rotational_error=False)
        error = Mock(point=Mock(aos=1, aoa=1), x_saturated=False, y_saturated=False, rotational_error=True)
        self.view.render(Mock(points=[normal, error]))
        self.assertEqual(2, len(self.view.axes.collections))
        colors = {tuple(collection.get_edgecolors()[0]) for collection in self.view.axes.collections}
        self.assertEqual({to_rgba(self.view.NORMAL_COLOR)}, colors)
        legend_labels = self.view.axes.get_legend_handles_labels()[1]
        expected_term = "生成禁止" if self.view._japanese_graph_text else "generation disabled"
        self.assertTrue(any(expected_term in label for label in legend_labels))

    def test_saturated_rotational_error_keeps_saturation_color_and_error_marker_group(self):
        """TEST-UNIT-125

        テスト目的:
            X/Y飽和とZ/A範囲外が同時発生した点の複合表示を確認する。

        テスト手順:
            1. x_saturated=Trueかつrotational_error=Trueの1点を描画し、色と凡例文言を確認する。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            複合状態点は飽和色を維持し、凡例でZ/A生成禁止も識別できること。

        検証根拠:
            2種類の状態を同一点に同時付与し、双方の視覚情報が失われていないことを観測するため、状態優先順位・複合表現を直接検証できる。
        """
        error = Mock(point=Mock(aos=1, aoa=1), x_saturated=True, y_saturated=False, rotational_error=True)
        self.view.render(Mock(points=[error]))
        self.assertEqual(1, len(self.view.axes.collections))
        collection = self.view.axes.collections[0]
        self.assertEqual(to_rgba(self.view.SATURATED_COLOR), tuple(collection.get_edgecolors()[0]))
        legend_labels = self.view.axes.get_legend_handles_labels()[1]
        expected_label = (
            "X/Y飽和・Z/A範囲外（生成禁止）"
            if self.view._japanese_graph_text
            else "X/Y saturated - Z/A out of range (generation disabled)"
        )
        self.assertEqual([expected_label], legend_labels)

    def test_japanese_font_selection_and_english_fallback(self):
        """TEST-UNIT-124

        テスト目的:
            日本語フォントの選択と、未搭載環境での英語フォールバックを確認する。

        テスト手順:
            1. Figure生成後にフォント一覧だけをMock化し、Meiryoが存在するケースと日本語フォントが存在しないケースでフォント選択処理を直接呼び出す。
            2. テスト対象のメソッドを呼び出して結果を取得する。
            3. 取得した結果を期待値と比較する。

        パスクライテリア:
            日本語対応フォントありでは日本語文字列、なしでは英語文字列を選択すること。

        検証根拠:
            MatplotlibのFigure生成・内部フォント探索を偽フォント一覧から分離し、製品コードのフォント候補判定結果と_text()の言語選択を直接観測する。これによりOS依存なしに日本語表示経路と文字化け回避経路を検証できる。
        """
        original_family = list(rcParams["font.family"])
        try:
            with patch(
                "map_view.font_manager.fontManager.ttflist",
                [SimpleNamespace(name="Meiryo")],
            ):
                self.view._configure_matplotlib_font()
                self.assertTrue(self.view._japanese_graph_text)
                self.assertEqual("Meiryo", self.view._graph_font_family)
                self.assertEqual("非飽和", self.view._text("非飽和", "Unsaturated"))

            with patch(
                "map_view.font_manager.fontManager.ttflist",
                [SimpleNamespace(name="DejaVu Sans")],
            ):
                self.view._configure_matplotlib_font()
                self.assertFalse(self.view._japanese_graph_text)
                self.assertEqual("DejaVu Sans", self.view._graph_font_family)
                self.assertEqual("Unsaturated", self.view._text("非飽和", "Unsaturated"))
        finally:
            rcParams["font.family"] = original_family


if __name__ == "__main__":
    unittest.main()
