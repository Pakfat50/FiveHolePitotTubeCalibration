"""較正点の走査順序を生成する。"""

from models import CalibrationPoint, CalibrationSettings


class ScanPlanner:
    """AoA/AoSの等間隔走査点列を生成する。

    対応要求:
        REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    """

    # 対応要求: REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
    def generate_points(self, settings: CalibrationSettings) -> list[CalibrationPoint]:
        """設定された走査順序で較正点列を生成する。

        引数:
            settings: AoA/AoS範囲、点数、蛇行走査設定を含む有効な設定。

        戻り値:
            両端を含み、AoAを外側ループ、AoSを内側ループとする較正点列。
            蛇行走査時はAoA行ごとにAoS方向を反転する。

        対応要求:
            REQ-SCAN-001, REQ-SCAN-002, REQ-SCAN-003
        """
        # 入力値はInputValidatorで検証済みであることを前提とする。
        # 両端を必ず含めるため、点数nに対して刻み幅を(max-min)/(n-1)で求める。
        aoa_step = (settings.aoa_max - settings.aoa_min) / (settings.aoa_points - 1)
        aos_step = (settings.aos_max - settings.aos_min) / (settings.aos_points - 1)

        aoa_values = [settings.aoa_min + aoa_step * i for i in range(settings.aoa_points)]
        aos_values = [settings.aos_min + aos_step * i for i in range(settings.aos_points)]

        points: list[CalibrationPoint] = []
        index = 0

        # AoAを外側ループ、AoSを内側ループとすることで仕様上の走査順序を実現する。
        # 蛇行走査が有効な場合は奇数行だけAoS順序を反転し、行末から次行先頭への
        # 不要な大移動を避ける。点集合そのものは通常走査と同一である。
        for row_index, aoa in enumerate(aoa_values):
            row_aos = aos_values
            if settings.serpentine and row_index % 2 == 1:
                row_aos = list(reversed(aos_values))

            for aos in row_aos:
                points.append(CalibrationPoint(index=index, aoa=aoa, aos=aos))
                index += 1

        return points
