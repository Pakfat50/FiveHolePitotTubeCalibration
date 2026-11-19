# RP2040計測スケッチ

Arduino IDEで同じフォルダの `AirDataLogger.ino` を開き、Arduino-Picoコアの **Adafruit QT Py RP2040** を選びます。スケッチは Sensirion I2C SDP、Adafruit Unified Sensor、Adafruit BMP280 Library、Adafruit BNO055 を使用します。

| バス | 接続先 |
|---|---|
| Wire | BNO055（0x28）、BMP280 |
| Wire1 | SDP3x 3台。Total・AoA・AoSの順にアドレス設定0・2・1 |

USBシリアルを115200で開くと初期化を開始します。起動診断に続いて、各行に以下の18列をタブ区切りで送信します。最後の時刻は差圧を読み取る直前の `millis()` です。

1. Total・AoA・AoSの差圧3列
2. 同じ順の差圧計温度3列
3. Yaw・Pitch・Rollの3列
4. 加速度XYZ、角速度XYZの6列
5. BMP温度、BMP気圧、時刻の3列

記録と表示には [AirDataMonitor](../AirDataMonitor/) を使用します。
