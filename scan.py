"""Calibration point scan planning."""

from models import CalibrationPoint, CalibrationSettings


class ScanPlanner:
    """Generate the equally spaced AoA/AoS scan sequence.

    Requirements:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    """

    # Requirements: REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    def generate_points(self, settings: CalibrationSettings) -> list[CalibrationPoint]:
        """Generate calibration points in the configured scan order.

        Args:
            settings: Valid settings containing AoA/AoS ranges, counts, and
                serpentine option.

        Returns:
            Calibration points with endpoints included, AoA as outer loop and
            AoS as inner loop; alternate AoS rows are reversed when serpentine
            scanning is enabled.

        Requirements:
            REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
        """
        raise NotImplementedError
