"""ピトー管先端位置のX/Y補正量を計算する。"""


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

        引数:
            theta: 実ピッチ角 [deg]。
            lx: ピッチ中心から先端までの基準X方向距離 [mm]。
            ly: ピッチ中心から先端までの基準Y方向距離 [mm]。

        戻り値:
            必要な``(x, y)``並進量 [mm]。

        対応要求:
            REQ-POS-001, REQ-POS-002
        """
        raise NotImplementedError
