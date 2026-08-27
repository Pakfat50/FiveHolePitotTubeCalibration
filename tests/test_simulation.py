import math
import unittest
from unittest.mock import Mock

from simulation import SimulationController, SimulationView


class TestSimulation(unittest.TestCase):
    def setUp(self):
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
        self.assertIs(self.points[0], self.controller._frame_at(self.plan, 0.0))

    # TEST-UNIT-094
    # Requirements: REQ-SIM-002
    def test_end_frame_is_last_point(self):
        self.assertIs(self.points[-1], self.controller._frame_at(self.plan, 1.0))

    # TEST-UNIT-095
    # Requirements: REQ-SIM-002
    def test_middle_progress_maps_to_scan_order(self):
        self.assertIs(self.points[2], self.controller._frame_at(self.plan, 0.5))

    # TEST-UNIT-096
    # Requirements: REQ-SIM-002
    def test_playback_duration_is_independent_of_hold_time(self):
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
