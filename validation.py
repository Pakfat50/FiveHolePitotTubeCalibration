"""較正設定の入力値検証を行う。

このCore層モジュールはTkinterへ依存せず、ユーザー入力の範囲、点数、
距離、保持時間、Feed rate、軸可動範囲を検証する。
"""

from models import CalibrationSettings, ValidationResult


class InputValidator:
    """較正設定を検証し、検出した問題をすべて返す。

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
        raise NotImplementedError
