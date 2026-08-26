"""Axis travel evaluation and X/Y saturation."""

from models import AxisCommand, AxisLimits, AxisRange, CalibrationPoint, PointEvaluation


class LimitEvaluator:
    """Apply translational saturation and detect rotational range errors.

    Requirements:
        REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    """

    # Requirements: REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    def evaluate(self, point: CalibrationPoint, command: AxisCommand, limits: AxisLimits) -> PointEvaluation:
        """Evaluate one ideal command against all configured axis limits.

        Args:
            point: Calibration point associated with the command.
            command: Ideal X/Y/Z/A command.
            limits: Axis travel ranges.

        Returns:
            PointEvaluation preserving the ideal command, applying X/Y
            saturation only, and flagging any Z/A range violation.

        Requirements:
            REQ-VALID-003, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
        """
        raise NotImplementedError

    # Requirements: REQ-LIMIT-001, REQ-LIMIT-002
    def _saturate_translation(self, value: float, axis_range: AxisRange) -> tuple[float, bool, float]:
        """Clamp one translation and report saturation and absolute deviation.

        Args:
            value: Ideal translation.
            axis_range: Allowed translation range.

        Returns:
            Tuple ``(actual, saturated, deviation)``.

        Requirements:
            REQ-LIMIT-001, REQ-LIMIT-002
        """
        raise NotImplementedError

    # Requirements: REQ-LIMIT-003
    def _rotation_in_range(self, value: float, axis_range: AxisRange) -> bool:
        """Check a rotation without altering the command value.

        Args:
            value: Z or A command [deg].
            axis_range: Allowed angular range.

        Returns:
            True when the value is inside the range including endpoints.

        Requirements:
            REQ-LIMIT-003
        """
        raise NotImplementedError
