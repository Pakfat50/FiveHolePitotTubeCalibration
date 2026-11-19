#include <Arduino.h>
#include <SensirionI2CSdp.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <atomic>
#include <pico/mutex.h>

constexpr uint32_t DP_MEASURE_MICROS = 10000;
constexpr uint32_t BNO_MEASURE_MICROS = 10000;
constexpr uint32_t DP_DELAY_ADJ = 2;
constexpr uint32_t BNO_DELAY_ADJ = 8;

// 元の count > 100 は、初回も含めて102ループごとの更新。
constexpr uint32_t BMP_UPDATE_INTERVAL = 102;

struct YawPitchRoll {
    float yawDeg;
    float pitchDeg;
    float rollDeg;
};

struct ImuSample {
    YawPitchRoll angles;
    imu::Vector<3> acceleration;
    imu::Vector<3> angularVelocity;
    float bmpTemperature;
    float bmpPressure;
};

enum class StartupStage : uint8_t {
    Starting,
    SerialReady,
    ImuReady
};

static std::atomic<StartupStage> startupStage{StartupStage::Starting};

static Adafruit_BNO055 bno(-1, 0x28, &Wire);
static Adafruit_BMP280 bmp;

static SensirionI2CSdp dpSensors[3];
static constexpr uint8_t dpAddresses[] = {
    SDP3X_I2C_ADDRESS_0,  // Total
    SDP3X_I2C_ADDRESS_2,  // AoA
    SDP3X_I2C_ADDRESS_1   // AoS
};

// SDKが起動時に初期化する、コア間共有用のミューテックス。
auto_init_mutex(imuSampleMutex);
static ImuSample sharedImuSample{};

bool quaternionToYawPitchRoll(const imu::Quaternion& q, YawPitchRoll& out) {
    const float w = static_cast<float>(q.w());
    const float x = static_cast<float>(q.x());
    const float y = static_cast<float>(q.y());
    const float z = static_cast<float>(q.z());

    const float ww = w * w;
    const float xx = x * x;
    const float yy = y * y;
    const float zz = z * z;
    const float normSq = ww + xx + yy + zz;

    if (!isfinite(normSq) || normSq <= 0.0f) {
        return false;
    }

    // センサーの回転行列の列を [Y, -X, Z] に組み替え、
    // 装置座標で Z-Y-X オイラー角を計算する。
    const float sinPitch = -2.0f * (w * x + y * z) / normSq;
    const float clampedSinPitch = fmaxf(-1.0f, fminf(1.0f, sinPitch));

    constexpr float radToDeg = 57.2957795f;

    out.yawDeg = atan2f(ww - xx + yy - zz,
                       2.0f * (x * y - w * z)) * radToDeg;
    out.pitchDeg = asinf(clampedSinPitch) * radToDeg;
    out.rollDeg = atan2f(2.0f * (w * y - x * z),
                        ww - xx - yy + zz) * radToDeg;

    return true;
}

static void waitRemainingMicros(uint32_t startedAt, uint32_t budget) {
    // 符号なしの差分で micros() の周回をまたいでも経過時間を求める。
    const uint32_t elapsed = micros() - startedAt;
    if (elapsed < budget) {
        delayMicroseconds(budget - elapsed);
    }
}

static void waitForStartupStage(StartupStage requiredStage) {
    while (startupStage.load(std::memory_order_acquire) < requiredStage) {
        delay(1);
    }
}

static void printTsvField(float value) {
    Serial.print(value);
    Serial.write('\t');
}

static void printTsvVector(const imu::Vector<3>& vector) {
    printTsvField(static_cast<float>(vector.x()));
    printTsvField(static_cast<float>(vector.y()));
    printTsvField(static_cast<float>(vector.z()));
}
void setup() {
    Serial.begin(115200);
    while (!Serial) {
        delay(100);
    }
    startupStage.store(StartupStage::SerialReady, std::memory_order_release);

    Wire.begin();

    if (!bmp.begin()) {
        Serial.println(F("Could not find a valid BMP280 sensor, check wiring or "
                         "try a different address!"));
        Serial.print("SensorID was: 0x");
        Serial.println(bmp.sensorID(), 16);
        Serial.print("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n");
        Serial.print("   ID of 0x56-0x58 represents a BMP 280,\n");
        Serial.print("        ID of 0x60 represents a BME 280.\n");
        Serial.print("        ID of 0x61 represents a BME 680.\n");
        while (true) {
            delay(10);
        }
    }

    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                    Adafruit_BMP280::SAMPLING_X2,
                    Adafruit_BMP280::SAMPLING_X16,
                    Adafruit_BMP280::FILTER_X16,
                    Adafruit_BMP280::STANDBY_MS_500);

    bmp.getTemperatureSensor()->printSensorDetails();

    if (!bno.begin()) {
        Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while (true) {
        }
    }

    delay(1000);

    const int8_t temp = bno.getTemp();
    Serial.print("Current Temperature: ");
    Serial.print(temp);
    Serial.println(" C");
    Serial.println();

    bno.setExtCrystalUse(true);

    Serial.println("Calibration status values: 0=uncalibrated, 3=fully calibrated");

    startupStage.store(StartupStage::ImuReady, std::memory_order_release);
}

void setup1() {
    waitForStartupStage(StartupStage::SerialReady);

    Wire1.begin();

    for (size_t i = 0; i < 3; ++i) {
        dpSensors[i].begin(Wire1, dpAddresses[i]);
    }

    // 元の順序どおり、全センサーを停止してから順に開始する。
    for (auto& sensor : dpSensors) {
        sensor.stopContinuousMeasurement();
    }
    for (auto& sensor : dpSensors) {
        sensor.startContinuousMeasurementWithDiffPressureTComp();
    }

    // 起動時の診断表示と計測ログが混ざらないようにする。
    waitForStartupStage(StartupStage::ImuReady);
}

void loop() {
    const uint32_t startedAt = micros();

    static ImuSample latest{};
    static uint32_t bmpLoopCount = 0;
    static sensors_event_t tempEvent{};
    static sensors_event_t pressureEvent{};

    // 変換に失敗した場合、元のコードと同じく直前の角度を保持する。
    quaternionToYawPitchRoll(bno.getQuat(), latest.angles);
    latest.acceleration =
        bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
    latest.angularVelocity =
        bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);

    if (++bmpLoopCount == BMP_UPDATE_INTERVAL) {
        bmp.getTemperatureSensor()->getEvent(&tempEvent);
        bmp.getPressureSensor()->getEvent(&pressureEvent);
        latest.bmpTemperature = tempEvent.temperature;
        latest.bmpPressure = pressureEvent.pressure;
        bmpLoopCount = 0;
    }

    // 取得済みの測定値をまとめて公開する。
    mutex_enter_blocking(&imuSampleMutex);
    sharedImuSample = latest;
    mutex_exit(&imuSampleMutex);

    waitRemainingMicros(startedAt, BNO_MEASURE_MICROS - BNO_DELAY_ADJ);
}

void loop1() {
    const uint32_t startedAt = micros();
    const uint32_t timestampMs = millis();

    // 読み取りエラー時の値の扱いを保つため、バッファはループ間で保持する。
    static float differentialPressure[3]{};
    static float temperature[3]{};

    for (size_t i = 0; i < 3; ++i) {
        dpSensors[i].readMeasurement(differentialPressure[i], temperature[i]);
    }

    // 1行に使うIMU・BMP値を一括コピーし、出力前にロックを解除する。
    mutex_enter_blocking(&imuSampleMutex);
    const ImuSample sample = sharedImuSample;
    mutex_exit(&imuSampleMutex);

    for (float value : differentialPressure) {
        printTsvField(value);
    }
    for (float value : temperature) {
        printTsvField(value);
    }

    printTsvField(sample.angles.yawDeg);
    printTsvField(sample.angles.pitchDeg);
    printTsvField(sample.angles.rollDeg);
    printTsvVector(sample.acceleration);
    printTsvVector(sample.angularVelocity);
    printTsvField(sample.bmpTemperature);
    printTsvField(sample.bmpPressure);
    Serial.println(timestampMs);

    waitRemainingMicros(startedAt, DP_MEASURE_MICROS - DP_DELAY_ADJ);
}
