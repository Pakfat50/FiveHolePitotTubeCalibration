"""Pitot-tip X/Y compensation calculations."""


class PositionCompensator:
    """Calculate X/Y translation required after pitch rotation.

    Roll is ignored because the roll axis lies on the Pitot tube longitudinal
    axis and therefore does not move the tip.

    Requirements:
        REQ-POS-001, REQ-POS-002
    """

    # Requirements: REQ-POS-001, REQ-POS-002
    def calculate_xy(self, theta: float, lx: float, ly: float) -> tuple[float, float]:
        """Calculate translation commands that keep the tip at tunnel center.

        Args:
            theta: Actual pitch angle [deg].
            lx: Reference X distance from pitch center to tip [mm].
            ly: Reference Y distance from pitch center to tip [mm].

        Returns:
            Required ``(x, y)`` translations [mm].

        Requirements:
            REQ-POS-001, REQ-POS-002
        """
        raise NotImplementedError
