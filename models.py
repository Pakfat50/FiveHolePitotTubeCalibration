"""Domain data models for the 5-hole Pitot calibration application.

The models in this module are shared across the Core, Application, Infrastructure,
and Presentation layers. They intentionally contain no GUI or file-I/O dependency.

Architecture source:
    docs/architecture_design.md sections 4, 6, 8, and 10.
"""

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Validation issue severity.

    Values:
        ERROR: Blocking validation error.
        WARNING: Non-blocking warning.

    Requirements:
        REQ-VALID-001, REQ-VALID-002, REQ-VALID-003
    """

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class AxisRange:
    """Minimum and maximum travel of one physical axis.

    Args:
        minimum: Minimum permitted command value.
        maximum: Maximum permitted command value.

    Requirements:
        REQ-INPUT-005, REQ-VALID-002
    """

    minimum: float
    maximum: float


@dataclass(frozen=True)
class AxisLimits:
    """Travel ranges for X, Y, Z, and A axes.

    Args:
        x: X-axis travel range.
        y: Y-axis travel range.
        z: Z-axis travel range.
        a: A-axis travel range.

    Requirements:
        REQ-INPUT-005, REQ-VALID-003
    """

    x: AxisRange
    y: AxisRange
    z: AxisRange
    a: AxisRange


@dataclass(frozen=True)
class CalibrationSettings:
    """Validated calibration input conditions and user options.

    Args:
        aoa_min: Minimum AoA in degrees.
        aoa_max: Maximum AoA in degrees.
        aos_min: Minimum AoS in degrees.
        aos_max: Maximum AoS in degrees.
        aoa_points: Number of AoA calibration points including endpoints.
        aos_points: Number of AoS calibration points including endpoints.
        tip_offset_x: Lx, X-direction distance from pitch center to Pitot tip [mm].
        tip_offset_y: Ly, Y-direction distance from pitch center to Pitot tip [mm].
        hold_time_s: Hold time at each calibration point [s].
        feed_rate: GRBL G94 composite feed rate F [unit/min].
        axis_limits: X/Y/Z/A travel limits.
        serpentine: Whether to reverse AoS direction on alternating AoA rows.
        output_comments: Whether generated G-code includes point comments.

    Requirements:
        REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004,
        REQ-INPUT-005, REQ-INPUT-007
    """

    aoa_min: float
    aoa_max: float
    aos_min: float
    aos_max: float
    aoa_points: int
    aos_points: int
    tip_offset_x: float
    tip_offset_y: float
    hold_time_s: float
    feed_rate: float
    axis_limits: AxisLimits
    serpentine: bool
    output_comments: bool


@dataclass(frozen=True)
class CalibrationPoint:
    """One requested calibration point in scan order.

    Args:
        index: Zero-based scan index.
        aoa: Requested angle of attack [deg].
        aos: Requested angle of sideslip [deg].

    Requirements:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    """

    index: int
    aoa: float
    aos: float


@dataclass(frozen=True)
class AxisCommand:
    """Command values for simultaneous X/Y/Z/A motion.

    Args:
        x: X translation command [mm].
        y: Y translation command [mm].
        z: Actual pitch command [deg].
        a: Actual roll command [deg].

    Requirements:
        REQ-TRANS-002, REQ-POS-001, REQ-GCODE-003
    """

    x: float
    y: float
    z: float
    a: float


@dataclass(frozen=True)
class PointEvaluation:
    """Calculated and limit-evaluated command for one calibration point.

    Args:
        point: Requested AoA/AoS point.
        ideal_command: Command before X/Y saturation.
        command: Actual command used by simulation and G-code.
        x_saturated: True when X was clamped to its travel range.
        y_saturated: True when Y was clamped to its travel range.
        x_deviation: Absolute X deviation caused by saturation [mm].
        y_deviation: Absolute Y deviation caused by saturation [mm].
        rotational_error: True when Z or A exceeds its allowed range.

    Requirements:
        REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    """

    point: CalibrationPoint
    ideal_command: AxisCommand
    command: AxisCommand
    x_saturated: bool
    y_saturated: bool
    x_deviation: float
    y_deviation: float
    rotational_error: bool


@dataclass(frozen=True)
class ValidationIssue:
    """Field-level validation issue for non-modal GUI presentation.

    Args:
        field: Input-field identifier.
        severity: Error or warning severity.
        message: Human-readable Japanese-facing reason.

    Requirements:
        REQ-VALID-001, REQ-GUI-005
    """

    field: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """Result returned by input validation.

    Args:
        issues: All detected field-level validation issues.
        is_valid: True only when no blocking input error exists.

    Requirements:
        REQ-VALID-001, REQ-VALID-002
    """

    issues: list[ValidationIssue]
    is_valid: bool


@dataclass(frozen=True)
class CalibrationPlan:
    """Single source of calculated calibration commands for all outputs.

    The same plan is consumed by the map, simulation, and G-code generator so
    coordinate calculations are not repeated independently.

    Args:
        settings: Settings used to create this plan.
        points: Limit-evaluated points in scan order.
        max_x_deviation: Maximum X saturation deviation [mm].
        max_y_deviation: Maximum Y saturation deviation [mm].
        has_generation_error: True when any Z/A command is out of range.

    Requirements:
        REQ-LIMIT-002, REQ-LIMIT-003, REQ-SCAN-001, REQ-SIM-001,
        REQ-GCODE-003
    """

    settings: CalibrationSettings
    points: list[PointEvaluation]
    max_x_deviation: float
    max_y_deviation: float
    has_generation_error: bool
