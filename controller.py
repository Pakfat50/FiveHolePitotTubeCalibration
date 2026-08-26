"""アプリケーション状態と再計算を管理するコントローラ。"""

from models import CalibrationPlan, CalibrationSettings, ValidationResult


class CalibrationController:
    """入力検証、較正計画再構築、生成可否を制御する。

    引数:
        validator: InputValidator互換の依存オブジェクト。
        service: CalibrationService互換の依存オブジェクト。

    対応要求:
        REQ-VALID-001, REQ-VALID-002, REQ-VALID-003, REQ-SCAN-001,
        REQ-GUI-003
    """

    def __init__(self, validator, service) -> None:
        self.validator = validator
        self.service = service
        self._settings: CalibrationSettings | None = None
        self._plan: CalibrationPlan | None = None
        self._validation: ValidationResult | None = None

    # 対応要求: REQ-VALID-001, REQ-SCAN-001
    def on_settings_changed(self, raw_input) -> ValidationResult:
        """設定変更を検証し、有効な場合のみ較正計画を再構築する。

        引数:
            raw_input: 現在の公開API契約ではPresentation層から渡される、
                解析済みのCalibrationSettings。

        戻り値:
            最新のValidationResult。

        対応要求:
            REQ-VALID-001, REQ-VALID-002, REQ-SCAN-001
        """
        raise NotImplementedError

    # 対応要求: REQ-GUI-003
    def apply_settings(self, settings: CalibrationSettings) -> ValidationResult:
        """読込済み設定を一括適用し、その後に検証と再構築を行う。

        引数:
            settings: CSVから全項目の解析に成功した設定。

        戻り値:
            最新のValidationResult。

        対応要求:
            REQ-GUI-003, REQ-VALID-001
        """
        raise NotImplementedError

    def get_current_settings(self) -> CalibrationSettings | None:
        """現在受理されている設定を返す。

        戻り値:
            現在の設定。まだ設定が受理されていない場合はNone。

        対応要求:
            REQ-GUI-003
        """
        return self._settings

    def get_current_plan(self) -> CalibrationPlan | None:
        """直近の有効な較正計画を返す。

        戻り値:
            現在の較正計画。有効な計画が存在しない場合はNone。

        対応要求:
            REQ-SIM-001, REQ-GCODE-003
        """
        return self._plan

    # 対応要求: REQ-VALID-002, REQ-VALID-003
    def can_generate(self) -> bool:
        """シミュレーションおよびGコード生成が許可されるかを返す。

        戻り値:
            入力検証に合格し、かつZ/A可動範囲エラーがない場合のみTrue。

        対応要求:
            REQ-VALID-002, REQ-VALID-003, REQ-LIMIT-003
        """
        raise NotImplementedError
