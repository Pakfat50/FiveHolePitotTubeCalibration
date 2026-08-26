"""較正設定の入力値検証を行う。

このCore層モジュールはTkinterへ依存せず、ユーザー入力の範囲、点数、
距離、保持時間、Feed rate、軸可動範囲を検証する。
"""

import math

from models import CalibrationSettings, Severity, ValidationIssue, ValidationResult


class InputValidator:
    """較正設定を検証し、検出した問題をすべて返す。

    検証では最初のエラーで打ち切らず、1回の呼び出しですべての入力項目を
    評価する。これによりGUIは複数の不正フィールドを同時に強調表示できる。

    対応要求:
        REQ-VALID-001, REQ-VALID-002
    """

    # 対応要求: REQ-VALID-001, REQ-VALID-002
    def validate(self, settings: CalibrationSettings) -> ValidationResult:
        """すべての較正入力項目を検証する。

        引数:
            settings: 解析済みの較正設定。

        戻り値:
            フィールド単位で検出した問題をすべて含むValidationResult。
            生成を禁止するエラーがない場合のみ入力を有効とする。

        対応要求:
            REQ-INPUT-001, REQ-INPUT-002, REQ-INPUT-003, REQ-INPUT-004,
            REQ-INPUT-005, REQ-VALID-001, REQ-VALID-002
        """
        issues: list[ValidationIssue] = []

        # AoA/AoSの走査範囲は両端を含むため、最小値と最大値が同じ場合も
        # 有効な走査範囲を構成できない。したがって minimum < maximum を必須とする。
        self._require_strict_range(issues, "aoa_range", settings.aoa_min, settings.aoa_max, "AoA")
        self._require_strict_range(issues, "aos_range", settings.aos_min, settings.aos_max, "AoS")

        # 両端を含む較正点列を生成するには各方向2点以上が必要となる。
        if settings.aoa_points < 2:
            issues.append(self._error("aoa_points", "AoA較正点数は2点以上である必要があります。"))
        if settings.aos_points < 2:
            issues.append(self._error("aos_points", "AoS較正点数は2点以上である必要があります。"))

        # Lx/Lyは幾何学計算に直接使用するため、0以下だけでなくNaNや無限大も
        # 明示的に除外する。math.isfiniteを先に判定し、非有限値を比較演算へ渡さない。
        self._require_positive_finite(issues, "tip_offset_x", settings.tip_offset_x, "Lx")
        self._require_positive_finite(issues, "tip_offset_y", settings.tip_offset_y, "Ly")

        # 保持時間とFeed rateはそれぞれ仕様上の下限値を含む。
        # 非有限値はGRBL出力値として成立しないため、下限判定とは別に除外する。
        if not math.isfinite(settings.hold_time_s) or settings.hold_time_s < 0.1:
            issues.append(self._error("hold_time_s", "較正点保持時間は0.1 s以上の有限値である必要があります。"))
        if not math.isfinite(settings.feed_rate) or settings.feed_rate < 1.0:
            issues.append(self._error("feed_rate", "Feed rateは1 unit/min以上の有限値である必要があります。"))

        # 各実軸の可動範囲も minimum < maximum を必須とする。
        # X/Y/Z/Aのどれか1軸でも不正なら、その軸を特定できる個別Issueを残す。
        for field, label, axis_range in (
            ("x_range", "X軸", settings.axis_limits.x),
            ("y_range", "Y軸", settings.axis_limits.y),
            ("z_range", "Z軸", settings.axis_limits.z),
            ("a_range", "A軸", settings.axis_limits.a),
        ):
            self._require_strict_range(issues, field, axis_range.minimum, axis_range.maximum, label)

        # 現在の入力検証で生成するIssueはすべて処理禁止のERRORである。
        # 将来WARNINGが追加されても、ERRORの有無だけで有効性を判定できるようにする。
        is_valid = not any(issue.severity is Severity.ERROR for issue in issues)
        return ValidationResult(issues=issues, is_valid=is_valid)

    @staticmethod
    def _error(field: str, message: str) -> ValidationIssue:
        """入力エラーを表すValidationIssueを生成する。"""
        return ValidationIssue(field=field, severity=Severity.ERROR, message=message)

    @classmethod
    def _require_strict_range(
        cls,
        issues: list[ValidationIssue],
        field: str,
        minimum: float,
        maximum: float,
        label: str,
    ) -> None:
        """最小値が最大値より小さいことを検証する。"""
        if minimum >= maximum:
            issues.append(cls._error(field, f"{label}の最小値は最大値より小さくする必要があります。"))

    @classmethod
    def _require_positive_finite(
        cls,
        issues: list[ValidationIssue],
        field: str,
        value: float,
        label: str,
    ) -> None:
        """値が0より大きい有限値であることを検証する。"""
        if not math.isfinite(value) or value <= 0.0:
            issues.append(cls._error(field, f"{label}は0より大きい有限値である必要があります。"))
