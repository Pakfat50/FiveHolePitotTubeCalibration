"""5孔ピトー管較正GUIアプリケーションのエントリポイント。"""


def main() -> None:
    """アプリケーション依存関係を構築し、GUIを起動する。

    依存関係の構成はアーキテクチャで定義した
    Presentation -> Application -> Domain/Core の方向に従い、
    ファイルI/OはInfrastructure層へ分離する。

    対応要求:
        REQ-GUI-004
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
