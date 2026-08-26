"""AoA/AoS較正点マップを表示するMatplotlib View。"""

import matplotlib.pyplot as plt

from models import CalibrationPlan


class CalibrationMapView:
    """較正点を描画し、可動範囲の警告・エラー状態を視覚的に区別する。

    色はX/Y飽和状態の識別だけに使用し、Z/A可動範囲超過は
    マーカー形状で生成禁止エラーとして識別する。

    対応要求:
        REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003
    """

    NORMAL_COLOR = "tab:blue"
    SATURATED_COLOR = "tab:orange"
    NORMAL_MARKER = "o"
    ROTATIONAL_ERROR_MARKER = "x"

    def __init__(self) -> None:
        """描画用FigureとAxesを生成する。"""
        self.figure, self.axes = plt.subplots()

    # 対応要求: REQ-GUI-002
    def render(self, plan: CalibrationPlan):
        """共有CalibrationPlanから、AoSを横軸、AoAを縦軸として描画する。

        色は「X/Y非飽和」「X/Y飽和」の2色のみとする。
        Z/A可動範囲超過点は同じ色分類を維持したまま×マーカーで表示し、
        凡例で生成禁止エラーであることを明示する。

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

        # 色はX/Y飽和の有無だけで決める。Z/A範囲超過は色を増やさず、
        # マーカー形状で独立に表現する。これにより色分類は常に2種類となる。
        normal = []
        saturated = []
        normal_rotational_error = []
        saturated_rotational_error = []

        for point_eval in plan.points:
            coordinate = (point_eval.point.aos, point_eval.point.aoa)
            is_saturated = point_eval.x_saturated or point_eval.y_saturated
            if point_eval.rotational_error:
                if is_saturated:
                    saturated_rotational_error.append(coordinate)
                else:
                    normal_rotational_error.append(coordinate)
            elif is_saturated:
                saturated.append(coordinate)
            else:
                normal.append(coordinate)

        self._scatter_group(
            normal,
            "非飽和",
            color=self.NORMAL_COLOR,
            marker=self.NORMAL_MARKER,
        )
        self._scatter_group(
            saturated,
            "X/Y飽和",
            color=self.SATURATED_COLOR,
            marker=self.NORMAL_MARKER,
        )
        self._scatter_group(
            normal_rotational_error,
            "非飽和・Z/A範囲外（生成禁止）",
            color=self.NORMAL_COLOR,
            marker=self.ROTATIONAL_ERROR_MARKER,
        )
        self._scatter_group(
            saturated_rotational_error,
            "X/Y飽和・Z/A範囲外（生成禁止）",
            color=self.SATURATED_COLOR,
            marker=self.ROTATIONAL_ERROR_MARKER,
        )

        if self.axes.collections:
            self.axes.legend()
        return self.axes

    def _scatter_group(
        self,
        points: list[tuple[float, float]],
        label: str,
        *,
        color: str,
        marker: str,
    ) -> None:
        """同じ飽和状態・回転軸状態の較正点を1つのscatterとして描画する。"""
        if not points:
            return
        aos_values, aoa_values = zip(*points)
        self.axes.scatter(aos_values, aoa_values, label=label, color=color, marker=marker)
