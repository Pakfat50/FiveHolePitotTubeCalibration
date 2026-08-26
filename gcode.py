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
        # 座標値はCalibrationPlanで一度だけ確定済みであり、Gコード生成時には
        # 再計算しない。これによりGUI表示・シミュレーションとの値の不一致を防ぐ。
        lines = self._format_header(initialization_text)
        for point_eval in plan.points:
            lines.extend(self._format_point(point_eval, settings))

        # 最終較正点に留まる仕様のため、末尾に$Hや原点復帰移動は追加しない。
        return "\n".join(lines) + "\n"

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
        lines = ["; User initialization G-code"]

        # ユーザー初期化Gコードは内容と行順を変更せず、そのままヘッダへ挿入する。
        # splitlines()で行単位に扱い、最終的な改行コードだけを生成側で統一する。
        if initialization_text:
            lines.extend(initialization_text.splitlines())

        # 初期化処理後にGRBLのホーミングを行い、その後の較正点指令を
        # mm・絶対座標・毎分送り(G94)として明示する。
        lines.extend([
            "",
            "; Homing",
            "$H",
            "",
            "G21",
            "G90",
            "G94",
        ])
        return lines

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
        lines: list[str] = []

        if settings.output_comments:
            # コメントには要求角と実際に出力する軸値を併記する。
            # XY飽和が発生した場合は、どの軸が飽和したかと逸脱量も記録する。
            saturation_parts: list[str] = []
            if point_eval.x_saturated:
                saturation_parts.append(f"X saturated deviation={point_eval.x_deviation:.6f}")
            if point_eval.y_saturated:
                saturation_parts.append(f"Y saturated deviation={point_eval.y_deviation:.6f}")
            saturation_text = "; " + ", ".join(saturation_parts) if saturation_parts else ""
            c = point_eval.command
            lines.append(
                f"; Point {point_eval.point.index + 1} AoA={point_eval.point.aoa:.6f} "
                f"AoS={point_eval.point.aos:.6f} X={c.x:.6f} Y={c.y:.6f} "
                f"Z={c.z:.6f} A={c.a:.6f}{saturation_text}"
            )

        # X/Y/Z/Aを1つのG01ブロックへ記載し、4軸同時移動としてGRBLへ渡す。
        # Feed rateはG94のprogram-unit/minとして、そのままFワードへ設定する。
        command = point_eval.command
        lines.append(
            f"G01 X{command.x:.6f} Y{command.y:.6f} Z{command.z:.6f} "
            f"A{command.a:.6f} F{settings.feed_rate:.6f}"
        )

        # 各点への移動後、指定秒数だけG04で保持する。P値も他の浮動小数値と
        # 同様に小数点以下6桁へ統一する。
        lines.append(f"G04 P{settings.hold_time_s:.6f}")
        return lines
