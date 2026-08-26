"""事前計算済みCalibrationPlanからGコード文字列を生成する。"""

from models import CalibrationPlan, CalibrationSettings, PointEvaluation


class GCodeGenerator:
    """軸値を再計算せず、GRBL互換の較正Gコードを生成する。

    対応要求:
        REQ-INPUT-004, REQ-INPUT-006, REQ-INPUT-007, REQ-GCODE-002,
        REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
    """

    # 対応要求: REQ-GCODE-002, REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
    def generate(self, plan: CalibrationPlan, settings: CalibrationSettings, initialization_text: str) -> str:
        """共有された較正計画から完全なGコード文字列を生成する。

        引数:
            plan: すべての出力経路で共有する事前計算済み較正計画。
            settings: Feed rate、保持時間、コメント出力設定を含む設定。
            initialization_text: ユーザーが読み込んだ初期化Gコード。

        戻り値:
            完全な`.nc`文字列。X/Y/Z/A/F/Pの浮動小数点値は
            小数点以下6桁とし、原点復帰指令は末尾に付加しない。

        対応要求:
            REQ-GCODE-002, REQ-GCODE-003, REQ-GCODE-004, REQ-GCODE-005
        """
        raise NotImplementedError

    # 対応要求: REQ-GCODE-002
    def _format_header(self, initialization_text: str) -> list[str]:
        """初期化コード、原点復帰、G21、G90、G94のヘッダ行を整形する。

        引数:
            initialization_text: ユーザーが読み込んだ初期化Gコード。

        戻り値:
            要求された順序のヘッダ行。

        対応要求:
            REQ-INPUT-006, REQ-GCODE-002
        """
        raise NotImplementedError

    # 対応要求: REQ-INPUT-004, REQ-GCODE-003, REQ-GCODE-004
    def _format_point(self, point_eval: PointEvaluation, settings: CalibrationSettings) -> list[str]:
        """1較正点分の同時移動、保持、任意コメントを整形する。

        引数:
            point_eval: ``command``が実際の出力値となる評価済み較正点。
            settings: Feed rate、保持時間、コメント出力設定。

        戻り値:
            1較正点分のGコード行。

        対応要求:
            REQ-INPUT-004, REQ-INPUT-007, REQ-GCODE-003, REQ-GCODE-004
        """
        raise NotImplementedError
