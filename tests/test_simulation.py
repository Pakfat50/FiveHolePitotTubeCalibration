import unittest
from unittest.mock import Mock

from simulation import SimulationController, SimulationView


class TestSimulation(unittest.TestCase):
    def setUp(self):
        self.view = Mock(spec=SimulationView)
        self.controller = SimulationController(self.view)
        self.points = [Mock(point=Mock(index=i), command=Mock(x=i,y=i,z=i,a=i)) for i in range(5)]
        self.plan = Mock(points=self.points)

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

    # TEST-UNIT-097
    # Requirements: REQ-SIM-003
    def test_side_view_is_initialized(self):
        view = SimulationView()
        view.initialize(self.plan)
        self.assertTrue(hasattr(view, "side_axes"))

    # TEST-UNIT-098
    # Requirements: REQ-SIM-003
    def test_front_view_is_initialized(self):
        view = SimulationView()
        view.initialize(self.plan)
        self.assertTrue(hasattr(view, "front_axes"))

    # TEST-UNIT-099
    # Requirements: REQ-SIM-004
    def test_render_frame_updates_required_information(self):
        view = SimulationView(); view.initialize(self.plan)
        point = Mock(point=Mock(index=3, aoa=1.0, aos=2.0), command=Mock(x=3.0,y=4.0,z=5.0,a=6.0), rotational_error=False, x_saturated=False, y_saturated=False)
        view.render_frame(point, 0.5)
        text = view.status_text
        for token in ("4", "1.00", "2.00", "3.00", "4.00", "5.00", "6.00", "50"):
            self.assertIn(token, text)

    # TEST-UNIT-122
    # Requirements: REQ-SIM-002
    def test_start_requests_timed_animation(self):
        self.controller.start(self.plan, duration_s=10.0)
        self.view.start_animation.assert_called_once()
        kwargs = self.view.start_animation.call_args.kwargs
        self.assertIs(self.plan, kwargs["plan"])
        self.assertEqual(10.0, kwargs["duration_s"])
        self.assertIs(self.points[0], kwargs["frame_provider"](0.0))
        self.assertIs(self.points[-1], kwargs["frame_provider"](1.0))

    # TEST-UNIT-123
    # Requirements: REQ-SIM-003
    def test_render_frame_draws_side_and_front_mechanism(self):
        view = SimulationView(); view.initialize(self.plan)
        point = Mock(point=Mock(index=0, aoa=0.0, aos=0.0), command=Mock(x=1.0,y=2.0,z=10.0,a=20.0), rotational_error=False, x_saturated=False, y_saturated=False)
        view.render_frame(point, 0.25)
        self.assertGreaterEqual(len(view.side_axes.lines), 1)
        self.assertGreaterEqual(len(view.front_axes.lines), 2)

    # TEST-UNIT-124
    # Requirements: REQ-SIM-004
    def test_progress_bar_updates_with_progress(self):
        view = SimulationView(); view.initialize(self.plan)
        point = Mock(point=Mock(index=0, aoa=0.0, aos=0.0), command=Mock(x=0.0,y=0.0,z=0.0,a=0.0), rotational_error=False, x_saturated=False, y_saturated=False)
        view.render_frame(point, 0.5)
        xdata = list(view._progress_artist.get_xdata())
        self.assertAlmostEqual(0.50, xdata[-1], places=2)


if __name__ == "__main__": unittest.main()
