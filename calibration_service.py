"""Application service that builds a complete calibration plan."""

from models import CalibrationPlan, CalibrationSettings


class CalibrationService:
    """Orchestrate scan, transform, compensation, and limit evaluation.

    The produced CalibrationPlan is the single calculation result shared by the
    GUI map, simulation, and G-code generation.

    Requirements:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
        REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
        REQ-LIMIT-003
    """

    # Requirements: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    def build_plan(self, settings: CalibrationSettings) -> CalibrationPlan:
        """Build the full ordered calibration plan from validated settings.

        Args:
            settings: Settings that already passed input validation.

        Returns:
            CalibrationPlan containing every PointEvaluation, maximum X/Y
            deviations, and aggregate generation-blocking status.

        Requirements:
            REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
            REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
            REQ-LIMIT-003
        """
        raise NotImplementedError
