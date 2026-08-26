"""AoA/AoS to actual Z/A angle transformation."""

from models import AxisLimits


class AngleTransformer:
    """Transform requested flow angles to pitch/roll mechanism commands.

    The mechanism is modeled as pitch rotation followed by roll about the Pitot
    tube axis. Equivalent solutions are selected using travel and continuity.

    Requirements:
        REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    """

    # Requirements: REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    def transform(self, aoa: float, aos: float, previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """Calculate actual pitch Z and roll A for one AoA/AoS point.

        Args:
            aoa: Requested AoA [deg].
            aos: Requested AoS [deg].
            previous: Previous selected ``(z, a)`` command, or None at start.
            limits: Allowed axis ranges used during equivalent-solution choice.

        Returns:
            Selected ``(z, a)`` angle pair [deg].

        Requirements:
            REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
        """
        raise NotImplementedError

    # Requirements: REQ-TRANS-002
    def _generate_equivalent_solutions(self, theta: float, phi: float) -> list[tuple[float, float]]:
        """Generate mechanism-angle candidates representing the same flow pose.

        Args:
            theta: Basic pitch solution [deg].
            phi: Basic roll solution [deg].

        Returns:
            Equivalent ``(z, a)`` candidates.

        Requirements:
            REQ-TRANS-002
        """
        raise NotImplementedError

    # Requirements: REQ-TRANS-003
    def _select_solution(self, candidates: list[tuple[float, float]], previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """Select a candidate by travel, continuity, motion, then |roll|.

        Args:
            candidates: Equivalent angle candidates.
            previous: Previous selected command or None.
            limits: Allowed Z/A ranges.

        Returns:
            Selected ``(z, a)`` candidate.

        Requirements:
            REQ-TRANS-003
        """
        raise NotImplementedError

    # Requirements: REQ-TRANS-004
    def _unwrap_angle(self, angle: float, previous: float | None) -> float:
        """Unwrap roll to the equivalent angle nearest the previous roll.

        Args:
            angle: Current roll angle [deg].
            previous: Previous roll angle [deg], or None.

        Returns:
            Equivalent angle avoiding unnecessary ±360-degree jumps.

        Requirements:
            REQ-TRANS-004
        """
        raise NotImplementedError
