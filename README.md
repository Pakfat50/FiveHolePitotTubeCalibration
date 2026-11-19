# 5孔ピトー管の較正・計測

| 用途 | アプリ | 起動方法 |
|---|---|---|
| 風洞での姿勢走査 | [Gコード生成](apps/gcode_generator/) | Pythonで `apps/gcode_generator/main.py` を実行 |
| センサー計測 | [RP2040計測スケッチ](apps/AirDataLogger/) | Arduino IDEで `AirDataLogger.ino` を開く |
| リアルタイム表示・記録 | [AirDataMonitor](apps/AirDataMonitor/) | Processing 4のJavaモードで `AirDataMonitor.pde` を開く |
| 較正係数の導出 | [AirDataCalibration](apps/AirDataCalibration/) | Pythonで `apps/AirDataCalibration/app.py` を実行 |

Gコード生成アプリで較正装置の走査を計画します。走査中はRP2040が100 Hzを目標に18列のTSVを送信し、AirDataMonitorが差圧・姿勢を表示してCSVに記録します。AirDataCalibrationにそのCSVとファイルごとの基準動圧［Pa］を入力すると、静定点一覧と迎角・横滑り角・動圧を推定する係数CSVが得られます。

[Gコード生成アプリの操作・開発手順](apps/gcode_generator/README.md) · [表示GUIの使い方](apps/AirDataMonitor/使い方.txt) · [係数導出アプリの使い方](apps/AirDataCalibration/README.txt)
