"""AoA/AoS較正点マップを表示するMatplotlib View。"""

from models import CalibrationPlan


class CalibrationMapView:
    """較正点を描画し、可動範囲の警告・エラー状態を視覚的に区別する。

    対応要求:
        REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
    """

    # 対応要求: REQ-GUI-002
    def render(self, plan: CalibrationPlan):
        """共有CalibrationPlanから、AoSを横軸、AoAを縦軸として描画する。

        引数:
            plan: 警告・エラー状態を含むCalibrationPlan。

        戻り値:
            View固有の描画結果。必要がない場合は戻り値を持たなくてもよい。

        対応要求:
            REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
        """
        raise NotImplementedError
