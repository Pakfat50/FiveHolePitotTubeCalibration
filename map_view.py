"""Matplotlib view for the AoA/AoS calibration point map."""

from models import CalibrationPlan


class CalibrationMapView:
    """Render calibration points and visually distinguish limit states.

    Requirements:
        REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
    """

    # Requirements: REQ-GUI-002
    def render(self, plan: CalibrationPlan):
        """Render AoS horizontally and AoA vertically from one shared plan.

        Args:
            plan: CalibrationPlan whose points include warning/error state.

        Returns:
            View-specific render result, if any.

        Requirements:
            REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
        """
        raise NotImplementedError
