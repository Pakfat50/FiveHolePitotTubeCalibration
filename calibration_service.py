"""較正計画全体を構築するアプリケーションサービス。"""

from models import CalibrationPlan, CalibrationSettings


class CalibrationService:
    """走査、座標変換、位置補正、可動範囲判定を統合する。

    生成するCalibrationPlanは、GUIの較正点マップ、シミュレーション、
    Gコード生成で共通利用する単一の計算結果とする。

    対応要求:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
        REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
        REQ-LIMIT-003
    """

    # 対応要求: REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002, REQ-LIMIT-003
    def build_plan(self, settings: CalibrationSettings) -> CalibrationPlan:
        """検証済み設定から走査順序を保持した較正計画全体を構築する。

        引数:
            settings: 入力検証に合格済みの較正設定。

        戻り値:
            全PointEvaluation、X/Y最大逸脱量、および生成禁止状態を
            集約したCalibrationPlan。

        対応要求:
            REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-002,
            REQ-TRANS-004, REQ-POS-001, REQ-LIMIT-001, REQ-LIMIT-002,
            REQ-LIMIT-003
        """
        raise NotImplementedError
