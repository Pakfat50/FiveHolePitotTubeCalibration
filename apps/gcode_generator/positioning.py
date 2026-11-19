"""ピトー管先端位置のX/Y補正量を計算する。"""

import math


class PositionCompensator:
    """ピッチ回転後に必要となるX/Y並進量を算出する。

    ロール軸はピトー管長手軸上にあるため、ロール回転による先端位置変化は
    発生しないものとして扱う。

    対応要求:
        REQ-POS-001, REQ-POS-002
    """

    # 対応要求: REQ-POS-001, REQ-POS-002
    def calculate_xy(self, theta: float, lx: float, ly: float) -> tuple[float, float]:
        """ピトー管先端を風洞中心に保持するための並進指令を算出する。

        Args:
            theta: 実ピッチ角 [deg]
            lx: ピッチ中心から先端までの基準X方向距離 [mm]
            ly: ピッチ中心から先端までの基準Y方向距離 [mm]

        Returns:
            必要な``(x, y)``並進量 [mm]

        対応要求:
            REQ-POS-001, REQ-POS-002
        """
        # 基準姿勢での先端位置ベクトル(Lx, Ly)を、ピッチ角thetaだけ
        # XY平面内で回転させ、回転後の先端位置(x_tip, y_tip)を求める。
        rad = math.radians(theta)
        cos_theta = math.cos(rad)
        sin_theta = math.sin(rad)
        x_tip = lx * cos_theta - ly * sin_theta
        y_tip = lx * sin_theta + ly * cos_theta

        # 先端を基準位置(Lx, Ly)へ戻すため、基準位置と回転後位置との差を
        # 並進軸X/Yへの補正指令とする。theta=0なら差は厳密に0となる。
        x = lx - x_tip
        y = ly - y_tip

        # ロール角はAPIに含めない。ロール軸がピトー管長手軸と一致するという
        # 機構モデルにより、ロール回転は先端のX/Y位置へ影響しないためである。
        return x, y
