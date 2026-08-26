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
        for token in ("3", "1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "50"):
            self.assertIn(token, text)


if __name__ == "__main__": unittest.main()
