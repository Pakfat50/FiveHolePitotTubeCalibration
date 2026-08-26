import unittest
from unittest.mock import Mock

from matplotlib.colors import to_rgba

from map_view import CalibrationMapView


class TestCalibrationMapView(unittest.TestCase):
    def setUp(self):
        self.view = CalibrationMapView()

    # TEST-UNIT-090
    # Requirements: REQ-GUI-002
    def test_axes_are_aos_horizontal_aoa_vertical(self):
        plan = Mock(points=[])
        self.view.render(plan)
        self.assertEqual("AoS", self.view.axes.get_xlabel())
        self.assertEqual("AoA", self.view.axes.get_ylabel())

    # TEST-UNIT-091
    # Requirements: REQ-GUI-002, REQ-LIMIT-001
    def test_saturated_points_use_distinct_visual_group(self):
        normal = Mock(point=Mock(aos=0, aoa=0), x_saturated=False, y_saturated=False, rotational_error=False)
        saturated = Mock(point=Mock(aos=1, aoa=1), x_saturated=True, y_saturated=False, rotational_error=False)
        self.view.render(Mock(points=[normal, saturated]))
        self.assertEqual(2, len(self.view.axes.collections))
        colors = [tuple(collection.get_facecolors()[0]) for collection in self.view.axes.collections]
        self.assertIn(to_rgba(self.view.NORMAL_COLOR), colors)
        self.assertIn(to_rgba(self.view.SATURATED_COLOR), colors)

    # TEST-UNIT-092
    # Requirements: REQ-GUI-002, REQ-LIMIT-003
    def test_rotational_error_points_use_distinct_visual_group_without_third_color(self):
        normal = Mock(point=Mock(aos=0, aoa=0), x_saturated=False, y_saturated=False, rotational_error=False)
        error = Mock(point=Mock(aos=1, aoa=1), x_saturated=False, y_saturated=False, rotational_error=True)
        self.view.render(Mock(points=[normal, error]))
        self.assertEqual(2, len(self.view.axes.collections))
        colors = {tuple(collection.get_edgecolors()[0]) for collection in self.view.axes.collections}
        self.assertEqual({to_rgba(self.view.NORMAL_COLOR)}, colors)
        legend_labels = self.view.axes.get_legend_handles_labels()[1]
        self.assertTrue(any("生成禁止" in label for label in legend_labels))

    # TEST-UNIT-122
    # Requirements: REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
    def test_saturated_rotational_error_keeps_saturation_color_and_error_marker_group(self):
        error = Mock(point=Mock(aos=1, aoa=1), x_saturated=True, y_saturated=False, rotational_error=True)
        self.view.render(Mock(points=[error]))
        self.assertEqual(1, len(self.view.axes.collections))
        collection = self.view.axes.collections[0]
        self.assertEqual(to_rgba(self.view.SATURATED_COLOR), tuple(collection.get_edgecolors()[0]))
        legend_labels = self.view.axes.get_legend_handles_labels()[1]
        self.assertEqual(["X/Y飽和・Z/A範囲外（生成禁止）"], legend_labels)


if __name__ == "__main__": unittest.main()
