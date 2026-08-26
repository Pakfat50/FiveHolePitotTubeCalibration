"""Calibration mechanism simulation controller and view."""

from models import CalibrationPlan, PointEvaluation


class SimulationController:
    """Map normalized playback progress to points and drive the simulation view.

    Args:
        view: SimulationView-compatible presentation dependency.

    Requirements:
        REQ-SIM-001, REQ-SIM-002
    """

    def __init__(self, view) -> None:
        self.view = view
        self.duration_s: float | None = None

    # Requirements: REQ-SIM-002
    def start(self, plan: CalibrationPlan, duration_s: float = 10.0) -> None:
        """Start playback without reproducing the real G-code hold time.

        Args:
            plan: Shared calibration plan.
            duration_s: Target total playback duration, normally about 10 s.

        Requirements:
            REQ-SIM-001, REQ-SIM-002
        """
        raise NotImplementedError

    # Requirements: REQ-SIM-002
    def _frame_at(self, plan: CalibrationPlan, progress: float) -> PointEvaluation:
        """Select the scan point corresponding to normalized progress.

        Args:
            plan: Calibration plan in scan order.
            progress: Playback progress in the inclusive range 0..1.

        Returns:
            PointEvaluation corresponding to the playback position.

        Requirements:
            REQ-SIM-002
        """
        raise NotImplementedError


class SimulationView:
    """Display side/front mechanism views and current-point information.

    Requirements:
        REQ-SIM-003, REQ-SIM-004
    """

    # Requirements: REQ-SIM-003
    def initialize(self, plan: CalibrationPlan) -> None:
        """Initialize simultaneous side and front abstract views.

        Args:
            plan: Shared calibration plan.

        Requirements:
            REQ-SIM-003
        """
        raise NotImplementedError

    # Requirements: REQ-SIM-003, REQ-SIM-004
    def render_frame(self, point: PointEvaluation, progress: float) -> None:
        """Render one frame and required textual status.

        Args:
            point: Current evaluated calibration point.
            progress: Normalized playback progress.

        Requirements:
            REQ-SIM-003, REQ-SIM-004
        """
        raise NotImplementedError

    def show_final_state(self) -> None:
        """Leave the final calibration state displayed after playback.

        Requirements:
            REQ-SIM-002, REQ-SIM-004
        """
        raise NotImplementedError
