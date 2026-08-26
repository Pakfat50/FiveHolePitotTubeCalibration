"""Infrastructure repositories for settings and G-code files."""

from models import CalibrationSettings


class SettingsLoadError(Exception):
    """Expected, non-fatal failure while loading a settings CSV.

    The presentation layer catches this error, keeps the pre-load settings and
    CalibrationPlan unchanged, and notifies the user non-modally.

    Requirements:
        REQ-GUI-003, REQ-GUI-005
    """


class SettingsRepository:
    """Persist calibration settings as CSV without a schema-version field.

    Requirements:
        REQ-GUI-003
    """

    # Requirements: REQ-GUI-003
    def save(self, path: str, settings: CalibrationSettings) -> None:
        """Save all input conditions and options to a CSV file.

        Args:
            path: Destination path.
            settings: Settings to serialize.

        Raises:
            OSError: When the file cannot be written.

        Requirements:
            REQ-GUI-003
        """
        raise NotImplementedError

    # Requirements: REQ-GUI-003
    def load(self, path: str) -> CalibrationSettings:
        """Load settings atomically from CSV.

        Required fields must all exist, be non-blank, structurally valid, and
        convertible before a CalibrationSettings object is returned. No partial
        settings object is exposed on failure.

        Args:
            path: CSV path to read.

        Returns:
            Fully parsed CalibrationSettings.

        Raises:
            SettingsLoadError: For missing/blank fields, malformed CSV, numeric
                conversion failures, or file-I/O failures.

        Requirements:
            REQ-GUI-003
        """
        raise NotImplementedError


class InitializationGCodeRepository:
    """Read initialization G-code text from a user-selected file.

    Requirements:
        REQ-INPUT-006
    """

    # Requirements: REQ-INPUT-006
    def load(self, path: str) -> str:
        """Read initialization G-code text.

        Args:
            path: Text-file path.

        Returns:
            File contents preserving line order.

        Raises:
            OSError: When the file cannot be read.

        Requirements:
            REQ-INPUT-006
        """
        raise NotImplementedError


class GCodeRepository:
    """Write generated G-code text to an `.nc` file.

    Requirements:
        REQ-GCODE-001
    """

    # Requirements: REQ-GCODE-001
    def save(self, path: str, text: str) -> None:
        """Write generated G-code to the selected path.

        Args:
            path: Destination `.nc` path.
            text: Complete G-code text.

        Raises:
            OSError: When the file cannot be written.

        Requirements:
            REQ-GCODE-001
        """
        raise NotImplementedError
