"""Input validation for calibration settings.

This Core-layer module validates user-entered ranges, counts, distances, hold
time, feed rate, and axis ranges without depending on Tkinter.
"""

from models import CalibrationSettings, ValidationResult


class InputValidator:
    """Validate calibration settings and report all detected issues.

    Requirements:
        REQ-VALID-001, REQ-VALID-002
    """

    # Requirements: REQ-VALID-001, REQ-VALID-002
    def validate(self, settings: CalibrationSettings) -> ValidationResult:
        """Validate all calibration input fields.

        Args:
            settings: Parsed calibration settings.

        Returns:
            ValidationResult containing every field-level issue. Input is valid
            only when no blocking error is present.

        Requirements:
            REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004,
            REQ-INPUT-005, REQ-VALID-001, REQ-VALID-002
        """
        raise NotImplementedError
