"""設定ファイルおよびGコードファイルの入出力を担当するRepository群。"""

from models import CalibrationSettings


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
        raise NotImplementedError

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
        raise NotImplementedError


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
        raise NotImplementedError


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
        raise NotImplementedError
