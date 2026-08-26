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

    # 対応要求: REQ-VALID-001, REQ-VALID-002, REQ-SCAN-001
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
        # 入力が変化するたびに必ず検証を行う。検証結果はGUIが非モーダル表示に
        # 利用できるよう、成功・失敗に関係なく最新値として保持する。
        validation = self.validator.validate(raw_input)
        self._validation = validation

        if not validation.is_valid:
            # 一時的な不正入力中は較正計画を再構築しない。以前の有効な計画を
            # 誤って生成処理へ流用しないよう、現在の計画を無効化する。
            self._plan = None
            return validation

        # すべての入力条件が有効になった時点で初めて設定を受理し、同じ設定から
        # CalibrationPlanを一度だけ再構築する。以後、GUI・シミュレーション・
        # G-code生成はこの共有Planを参照する。
        self._settings = raw_input
        self._plan = self.service.build_plan(raw_input)
        return validation

    # 対応要求: REQ-GUI-003, REQ-VALID-001
    def apply_settings(self, settings: CalibrationSettings) -> ValidationResult:
        """読込済み設定を一括適用し、その後に検証と再構築を行う。

        引数:
            settings: CSVから全項目の解析に成功した設定。

        戻り値:
            最新のValidationResult。

        対応要求:
            REQ-GUI-003, REQ-VALID-001
        """
        # SettingsRepository側で全項目の読込・型変換が完了した設定だけを受け取り、
        # 通常の設定変更と同じ検証経路へ通す。検証処理を二重実装しないことで、
        # GUI直接入力とCSV読込後で判定規則が分岐することを防ぐ。
        return self.on_settings_changed(settings)

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

    # 対応要求: REQ-VALID-002, REQ-VALID-003, REQ-LIMIT-003
    def can_generate(self) -> bool:
        """シミュレーションおよびGコード生成が許可されるかを返す。

        戻り値:
            入力検証に合格し、かつZ/A可動範囲エラーがない場合のみTrue。

        対応要求:
            REQ-VALID-002, REQ-VALID-003, REQ-LIMIT-003
        """
        # 生成を許可する条件は「最新入力が有効」「有効入力からPlanが生成済み」
        # 「Plan内にZ/A範囲超過がない」の3条件すべてを満たすこととする。
        # X/Y飽和は警告扱いなので、has_generation_errorには含めない。
        return bool(
            self._validation is not None
            and self._validation.is_valid
            and self._plan is not None
            and not self._plan.has_generation_error
        )
