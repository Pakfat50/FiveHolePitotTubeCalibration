import unittest
from unittest.mock import Mock

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
        self.assertGreaterEqual(len(self.view.axes.collections), 2)

    # TEST-UNIT-092
    # Requirements: REQ-GUI-002, REQ-LIMIT-003
    def test_rotational_error_points_use_distinct_visual_group(self):
        normal = Mock(point=Mock(aos=0, aoa=0), x_saturated=False, y_saturated=False, rotational_error=False)
        error = Mock(point=Mock(aos=1, aoa=1), x_saturated=False, y_saturated=False, rotational_error=True)
        self.view.render(Mock(points=[normal, error]))
        self.assertGreaterEqual(len(self.view.axes.collections), 2)


if __name__ == "__main__": unittest.main()
