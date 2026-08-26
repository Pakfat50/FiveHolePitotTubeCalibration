"""5孔ピトー管較正アプリケーションのドメインデータモデル。

本モジュールのモデルはCore、Application、Infrastructure、Presentation各層で
共有する。GUIやファイルI/Oへの依存は持たない。

設計根拠:
    docs/architecture_design.md の4章、6章、8章、10章。
"""

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """入力検証問題の重大度。

    値:
        ERROR: 処理を禁止する入力エラー。
        WARNING: 処理を禁止しない警告。

    対応要求:
        REQ-VALID-001, REQ-VALID-002, REQ-VALID-003
    """

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class AxisRange:
    """1物理軸の最小・最大可動範囲。

    引数:
        minimum: 許容する最小指令値。
        maximum: 許容する最大指令値。

    対応要求:
        REQ-INPUT-005, REQ-VALID-002
    """

    minimum: float
    maximum: float


@dataclass(frozen=True)
class AxisLimits:
    """X、Y、Z、A各軸の可動範囲。

    引数:
        x: X軸可動範囲。
        y: Y軸可動範囲。
        z: Z軸可動範囲。
        a: A軸可動範囲。

    対応要求:
        REQ-INPUT-005, REQ-VALID-003
    """

    x: AxisRange
    y: AxisRange
    z: AxisRange
    a: AxisRange


@dataclass(frozen=True)
class CalibrationSettings:
    """検証対象となる較正入力条件およびユーザーオプション。

    引数:
        aoa_min: AoA最小値 [deg]。
        aoa_max: AoA最大値 [deg]。
        aos_min: AoS最小値 [deg]。
        aos_max: AoS最大値 [deg]。
        aoa_points: 両端を含むAoA較正点数。
        aos_points: 両端を含むAoS較正点数。
        tip_offset_x: Lx。ピッチ中心からピトー管先端までのX方向距離 [mm]。
        tip_offset_y: Ly。ピッチ中心からピトー管先端までのY方向距離 [mm]。
        hold_time_s: 各較正点での保持時間 [s]。
        feed_rate: GRBL G94の合成送り速度F [unit/min]。
        axis_limits: X/Y/Z/A可動範囲。
        serpentine: AoA行ごとにAoS走査方向を反転するか。
        output_comments: 生成Gコードへ較正点コメントを出力するか。

    対応要求:
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
    """走査順序上の1つの要求較正点。

    引数:
        index: 0始まりの走査インデックス。
        aoa: 要求AoA [deg]。
        aos: 要求AoS [deg]。

    対応要求:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    """

    index: int
    aoa: float
    aos: float


@dataclass(frozen=True)
class AxisCommand:
    """X/Y/Z/Aの同時軸指令値。

    引数:
        x: X並進指令 [mm]。
        y: Y並進指令 [mm]。
        z: 実ピッチ指令 [deg]。
        a: 実ロール指令 [deg]。

    対応要求:
        REQ-TRANS-002, REQ-POS-001, REQ-GCODE-003
    """

    x: float
    y: float
    z: float
    a: float


@dataclass(frozen=True)
class PointEvaluation:
    """1較正点に対する計算結果および可動範囲評価結果。

    引数:
        point: 要求AoA/AoS較正点。
        ideal_command: X/Y飽和前の理想指令。
        command: シミュレーションおよびGコードで使用する実指令。
        x_saturated: Xが可動範囲端へ飽和した場合True。
        y_saturated: Yが可動範囲端へ飽和した場合True。
        x_deviation: 飽和によるX方向絶対逸脱量 [mm]。
        y_deviation: 飽和によるY方向絶対逸脱量 [mm]。
        rotational_error: ZまたはAが許容範囲を超える場合True。

    対応要求:
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
    """GUIへ非モーダル表示するフィールド単位の入力検証問題。

    引数:
        field: 入力フィールド識別子。
        severity: エラーまたは警告の重大度。
        message: ユーザーへ表示する日本語の理由。

    対応要求:
        REQ-VALID-001, REQ-GUI-005
    """

    field: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """入力検証結果。

    引数:
        issues: 検出したフィールド単位の問題一覧。
        is_valid: 処理を禁止する入力エラーがない場合のみTrue。

    対応要求:
        REQ-VALID-001, REQ-VALID-002
    """

    issues: list[ValidationIssue]
    is_valid: bool


@dataclass(frozen=True)
class CalibrationPlan:
    """すべての出力で共有する較正軸指令の単一計算結果。

    座標計算を各機能で独立に繰り返さないよう、較正点マップ、
    シミュレーション、Gコード生成で同一の計画を使用する。

    引数:
        settings: 本計画の生成に使用した設定。
        points: 走査順序に並んだ可動範囲評価済み較正点。
        max_x_deviation: X飽和による最大逸脱量 [mm]。
        max_y_deviation: Y飽和による最大逸脱量 [mm]。
        has_generation_error: Z/A指令が1点でも範囲外の場合True。

    対応要求:
        REQ-LIMIT-002, REQ-LIMIT-003, REQ-SCAN-001, REQ-SIM-001,
        REQ-GCODE-003
    """

    settings: CalibrationSettings
    points: list[PointEvaluation]
    max_x_deviation: float
    max_y_deviation: float
    has_generation_error: bool
