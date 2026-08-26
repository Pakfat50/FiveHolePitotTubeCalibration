"""G-code text generation from a precomputed CalibrationPlan."""

from models import CalibrationPlan, CalibrationSettings, PointEvaluation


class GCodeGenerator:
    """Generate GRBL-compatible calibration G-code without recalculating axes.

    Requirements:
        REQ-INPUT-004, REQ-INPUT-006, REQ-INPUT-007, REQ-GCODE-002,
        REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
    """

    # Requirements: REQ-GCODE-002, REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
    def generate(self, plan: CalibrationPlan, settings: CalibrationSettings, initialization_text: str) -> str:
        """Generate complete G-code text from the shared calculation plan.

        Args:
            plan: Precomputed calibration plan used by all output paths.
            settings: Settings supplying feed, hold, and comment options.
            initialization_text: User-loaded initialization G-code.

        Returns:
            Complete `.nc` text. Floating-point X/Y/Z/A/F/P values use six
            digits after the decimal point and no return-to-origin is appended.

        Requirements:
            REQ-GCODE-002, REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
        """
        raise NotImplementedError

    # Requirements: REQ-GCODE-002
    def _format_header(self, initialization_text: str) -> list[str]:
        """Format initialization, homing, G21, G90, and G94 header lines.

        Args:
            initialization_text: User-loaded initialization G-code.

        Returns:
            Header lines in required order.

        Requirements:
            REQ-INPUT-006, REQ-GCODE-002
        """
        raise NotImplementedError

    # Requirements: REQ-INPUT-004, REQ-GCODE-003, REQ-GCODE-004
    def _format_point(self, point_eval: PointEvaluation, settings: CalibrationSettings) -> list[str]:
        """Format one simultaneous move, hold, and optional point comment.

        Args:
            point_eval: Evaluated point whose ``command`` is the actual output.
            settings: Feed rate, hold time, and comment option.

        Returns:
            G-code lines for one calibration point.

        Requirements:
            REQ-INPUT-004, REQ-INPUT-007, REQ-GCODE-003, REQ-GCODE-004
        """
        raise NotImplementedError
