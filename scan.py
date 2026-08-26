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
        raise NotImplementedError
