"""設定ファイルおよびGコードファイルの入出力を担当するRepository群。"""

import csv

from models import AxisLimits, AxisRange, CalibrationSettings


class SettingsLoadError(Exception):
    """設定CSV読込時に発生する、想定内かつ非致命的な失敗。

    Presentation層は本例外を捕捉し、読込前の設定とCalibrationPlanを維持したまま、
    ユーザーへ非モーダルに通知する。

    対応要求:
        REQ-GUI-003, REQ-GUI-005
    """


class SettingsRepository:
    """スキーマバージョンを持たないCSVとして較正設定を保存・復元する。

    対応要求:
        REQ-GUI-003
    """

    _REQUIRED_KEYS = (
        "aoa_min", "aoa_max", "aos_min", "aos_max",
        "aoa_points", "aos_points", "tip_offset_x", "tip_offset_y",
        "hold_time_s", "feed_rate",
        "x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "a_min", "a_max",
        "serpentine", "output_comments",
    )

    # 対応要求: REQ-GUI-003
    def save(self, path: str, settings: CalibrationSettings) -> None:
        """すべての入力条件とオプションをCSVへ保存する。

        引数:
            path: 保存先パス。
            settings: シリアライズ対象の較正設定。

        例外:
            OSError: ファイルへ書き込めない場合。

        対応要求:
            REQ-GUI-003
        """
        # CSVは「key,value」の単純な2列形式とし、スキーマバージョンを持たせない。
        # 保存対象を明示列挙して、GUI設定の保存漏れを防ぐ。
        values = {
            "aoa_min": settings.aoa_min,
            "aoa_max": settings.aoa_max,
            "aos_min": settings.aos_min,
            "aos_max": settings.aos_max,
            "aoa_points": settings.aoa_points,
            "aos_points": settings.aos_points,
            "tip_offset_x": settings.tip_offset_x,
            "tip_offset_y": settings.tip_offset_y,
            "hold_time_s": settings.hold_time_s,
            "feed_rate": settings.feed_rate,
            "x_min": settings.axis_limits.x.minimum,
            "x_max": settings.axis_limits.x.maximum,
            "y_min": settings.axis_limits.y.minimum,
            "y_max": settings.axis_limits.y.maximum,
            "z_min": settings.axis_limits.z.minimum,
            "z_max": settings.axis_limits.z.maximum,
            "a_min": settings.axis_limits.a.minimum,
            "a_max": settings.axis_limits.a.maximum,
            "serpentine": str(settings.serpentine).lower(),
            "output_comments": str(settings.output_comments).lower(),
        }
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["key", "value"])
            for key in self._REQUIRED_KEYS:
                writer.writerow([key, values[key]])

    # 対応要求: REQ-GUI-003
    def load(self, path: str) -> CalibrationSettings:
        """CSVから設定を一括で読み込む。

        必須項目がすべて存在し、空欄でなく、構造が正しく、型変換可能であることを
        確認した後にのみCalibrationSettingsを返す。失敗時に部分的な設定を外部へ
        公開しない。

        引数:
            path: 読込対象CSVパス。

        戻り値:
            全項目の解析に成功したCalibrationSettings。

        例外:
            SettingsLoadError: 必須項目欠損、空欄、CSV構造不正、数値変換失敗、
                またはファイルI/O失敗の場合。

        対応要求:
            REQ-GUI-003
        """
        try:
            with open(path, "r", newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))
        except (OSError, UnicodeError) as exc:
            # I/O失敗もGUIで回復可能な「設定読込失敗」として統一的に通知する。
            raise SettingsLoadError(f"設定ファイルを読み込めません: {exc}") from exc

        # 一部だけ読み込んだ設定を適用しないよう、まずCSV全体の構造と全必須値を
        # ローカル辞書へ検証・変換し、最後に一度だけCalibrationSettingsを生成する。
        if not rows or rows[0] != ["key", "value"]:
            raise SettingsLoadError("設定CSVのヘッダは key,value である必要があります。")

        raw: dict[str, str] = {}
        for row in rows[1:]:
            if len(row) != 2:
                raise SettingsLoadError("設定CSVは各行2列である必要があります。")
            key, value = row
            if key in raw:
                raise SettingsLoadError(f"設定キーが重複しています: {key}")
            raw[key] = value

        for key in self._REQUIRED_KEYS:
            if key not in raw:
                raise SettingsLoadError(f"必須設定がありません: {key}")
            if raw[key].strip() == "":
                raise SettingsLoadError(f"必須設定が空欄です: {key}")

        def as_float(key: str) -> float:
            try:
                return float(raw[key])
            except ValueError as exc:
                raise SettingsLoadError(f"数値へ変換できません: {key}") from exc

        def as_int(key: str) -> int:
            try:
                # 点数は整数として保存・復元し、小数文字列を暗黙に丸めない。
                return int(raw[key])
            except ValueError as exc:
                raise SettingsLoadError(f"整数へ変換できません: {key}") from exc

        def as_bool(key: str) -> bool:
            value = raw[key].strip().lower()
            if value == "true":
                return True
            if value == "false":
                return False
            raise SettingsLoadError(f"真偽値へ変換できません: {key}")

        # ここまでに必要な全値が存在することを確認してから、全項目を型変換する。
        # 途中で失敗しても外部状態には何も適用されない。
        try:
            limits = AxisLimits(
                x=AxisRange(as_float("x_min"), as_float("x_max")),
                y=AxisRange(as_float("y_min"), as_float("y_max")),
                z=AxisRange(as_float("z_min"), as_float("z_max")),
                a=AxisRange(as_float("a_min"), as_float("a_max")),
            )
            return CalibrationSettings(
                aoa_min=as_float("aoa_min"),
                aoa_max=as_float("aoa_max"),
                aos_min=as_float("aos_min"),
                aos_max=as_float("aos_max"),
                aoa_points=as_int("aoa_points"),
                aos_points=as_int("aos_points"),
                tip_offset_x=as_float("tip_offset_x"),
                tip_offset_y=as_float("tip_offset_y"),
                hold_time_s=as_float("hold_time_s"),
                feed_rate=as_float("feed_rate"),
                axis_limits=limits,
                serpentine=as_bool("serpentine"),
                output_comments=as_bool("output_comments"),
            )
        except SettingsLoadError:
            raise
        except (TypeError, ValueError) as exc:
            raise SettingsLoadError(f"設定値を解析できません: {exc}") from exc


class InitializationGCodeRepository:
    """ユーザーが選択したファイルから初期化Gコードを読み込む。

    対応要求:
        REQ-INPUT-006
    """

    # 対応要求: REQ-INPUT-006
    def load(self, path: str) -> str:
        """初期化Gコード文字列を読み込む。

        引数:
            path: テキストファイルのパス。

        戻り値:
            行順序を保持したファイル内容。

        例外:
            OSError: ファイルを読み込めない場合。

        対応要求:
            REQ-INPUT-006
        """
        # UTF-8として全内容を一括読込し、改行を含む元のテキスト順序を保持する。
        with open(path, "r", encoding="utf-8") as file:
            return file.read()


class GCodeRepository:
    """生成済みGコード文字列を`.nc`ファイルへ保存する。

    対応要求:
        REQ-GCODE-001
    """

    # 対応要求: REQ-GCODE-001
    def save(self, path: str, text: str) -> None:
        """生成済みGコードを指定パスへ保存する。

        引数:
            path: 保存先`.nc`パス。
            text: 完全なGコード文字列。

        例外:
            OSError: ファイルへ書き込めない場合。

        対応要求:
            REQ-GCODE-001
        """
        # 呼出元が選択したパスへそのまま書き込み、存在しない親フォルダを
        # 自動生成しない。失敗時のOSErrorはGUI層で非モーダル通知する。
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
