"""Application state and recalculation controller."""

from models import CalibrationPlan, CalibrationSettings, ValidationResult


class CalibrationController:
    """Coordinate validation, plan rebuilding, and generation availability.

    Args:
        validator: InputValidator-compatible dependency.
        service: CalibrationService-compatible dependency.

    Requirements:
        REQ-VALID-001, REQ-VALID-002, REQ-VALID-003, REQ-SCAN-001,
        REQ-GUI-003
    """

    def __init__(self, validator, service) -> None:
        self.validator = validator
        self.service = service
        self._settings: CalibrationSettings | None = None
        self._plan: CalibrationPlan | None = None
        self._validation: ValidationResult | None = None

    # Requirements: REQ-VALID-001, REQ-SCAN-001
    def on_settings_changed(self, raw_input) -> ValidationResult:
        """Validate changed settings and rebuild the plan only when valid.

        Args:
            raw_input: Parsed CalibrationSettings supplied by the presentation
                layer in the current API contract.

        Returns:
            Latest ValidationResult.

        Requirements:
            REQ-VALID-001, REQ-VALID-002, REQ-SCAN-001
        """
        raise NotImplementedError

    # Requirements: REQ-GUI-003
    def apply_settings(self, settings: CalibrationSettings) -> ValidationResult:
        """Atomically apply loaded settings, then validate and rebuild.

        Args:
            settings: Fully parsed settings loaded from CSV.

        Returns:
            Latest ValidationResult.

        Requirements:
            REQ-GUI-003, REQ-VALID-001
        """
        raise NotImplementedError

    def get_current_settings(self) -> CalibrationSettings | None:
        """Return the currently accepted settings.

        Returns:
            Current settings or None before any settings are accepted.

        Requirements:
            REQ-GUI-003
        """
        return self._settings

    def get_current_plan(self) -> CalibrationPlan | None:
        """Return the most recent valid calculation plan.

        Returns:
            Current plan or None if no valid plan exists.

        Requirements:
            REQ-SIM-001, REQ-GCODE-003
        """
        return self._plan

    # Requirements: REQ-VALID-002, REQ-VALID-003
    def can_generate(self) -> bool:
        """Report whether simulation and G-code generation are permitted.

        Returns:
            True only when input validation passes and no Z/A range error exists.

        Requirements:
            REQ-VALID-002, REQ-VALID-003, REQ-LIMIT-003
        """
        raise NotImplementedError
