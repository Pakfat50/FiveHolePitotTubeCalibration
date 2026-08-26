"""AoA/AoS較正点マップを表示するMatplotlib View。"""

import matplotlib.pyplot as plt

from models import CalibrationPlan


class CalibrationMapView:
    """較正点を描画し、可動範囲の警告・エラー状態を視覚的に区別する。

    対応要求:
        REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
    """

    def __init__(self) -> None:
        """描画用FigureとAxesを生成する。"""
        self.figure, self.axes = plt.subplots()

    # 対応要求: REQ-GUI-002
    def render(self, plan: CalibrationPlan):
        """共有CalibrationPlanから、AoSを横軸、AoAを縦軸として描画する。

        引数:
            plan: 警告・エラー状態を含むCalibrationPlan。

        戻り値:
            MatplotlibのAxesオブジェクト。

        対応要求:
            REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
        """
        # 再描画時に古い点群を残さないようAxesを初期化する。
        self.axes.clear()
        self.axes.set_xlabel("AoS")
        self.axes.set_ylabel("AoA")

        # 状態ごとに点を分離して描画する。これにより通常点、XY飽和点、
        # Z/A範囲超過点をMatplotlib上の別collectionとして管理できる。
        normal = []
        saturated = []
        rotational_error = []
        for point_eval in plan.points:
            coordinate = (point_eval.point.aos, point_eval.point.aoa)
            if point_eval.rotational_error:
                rotational_error.append(coordinate)
            elif point_eval.x_saturated or point_eval.y_saturated:
                saturated.append(coordinate)
            else:
                normal.append(coordinate)

        self._scatter_group(normal, "通常")
        self._scatter_group(saturated, "XY飽和")
        self._scatter_group(rotational_error, "ZA範囲外")
        return self.axes

    def _scatter_group(self, points: list[tuple[float, float]], label: str) -> None:
        """同一状態の較正点を1つのscatter collectionとして描画する。"""
        if not points:
            return
        aos_values, aoa_values = zip(*points)
        self.axes.scatter(aos_values, aoa_values, label=label)
