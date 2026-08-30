# 5孔ピトー管較正Gコード生成

5孔ピトー管の較正条件から、GRBL対応の4軸（X/Y/Z/A）Gコードを生成するGUIアプリケーションです。AoA/AoSの較正点を作成し、装置の実軸可動範囲、軸変換、蛇行走査、保持時間、Feed rateを考慮した較正計画を生成します。

## 主な機能

- AoA/AoSの範囲・点数を指定した較正点生成
- Pitch/RollおよびX/Y補正を含む実軸指令への変換
- 実軸可動範囲の検証と逸脱・生成禁止状態の表示
- 較正点マップによる走査順序の確認
- シミュレーションによる姿勢・較正点の再生確認
- 初期化Gコードの読込とGRBL向けGコードの生成
- 設定のCSV保存・読込
- 日本語GUIと要求・設計・テスト・APIのトレーサビリティ

## まず試す

~~~bash
python -m pip install numpy matplotlib
python main.py
~~~

GUI起動から条件入力、シミュレーション、Gコード生成までの実画面操作は、[取扱説明書](https://pakfat50.github.io/FiveHolePitotTubeCalibration/user-manual/)の冒頭に掲載しています。

![操作の流れ](docs/media/getting-started.gif)

## ドキュメント

- [取扱説明書（GitHub Pages）](https://pakfat50.github.io/FiveHolePitotTubeCalibration/user-manual/)
- [要求仕様書](https://pakfat50.github.io/FiveHolePitotTubeCalibration/requirements/)
- [アーキテクチャ設計書](https://pakfat50.github.io/FiveHolePitotTubeCalibration/architecture/)
- [テスト仕様書](https://pakfat50.github.io/FiveHolePitotTubeCalibration/test-specification/)
- [製品コードAPI](https://pakfat50.github.io/FiveHolePitotTubeCalibration/api/)
- [テストコードAPI](https://pakfat50.github.io/FiveHolePitotTubeCalibration/test-api/)
- [開発プロセスルール](https://pakfat50.github.io/FiveHolePitotTubeCalibration/development-process-guideline/)
- [トレーサビリティ運用ルール](https://pakfat50.github.io/FiveHolePitotTubeCalibration/traceability-rules/)

## 開発者向け

~~~bash
python tools/check_artifacts.py
python -m unittest discover -s tests -v
~~~

## ライセンス

[MIT License](LICENSE)
