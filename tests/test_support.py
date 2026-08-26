"""テスト共通データ生成ヘルパー。Phase 3ではproduction code未実装のため、公開API契約をここで固定する。"""

from models import AxisLimits, AxisRange, CalibrationSettings

ABS_TOL = 0.001


def make_limits(**overrides):
    values = {
        "x": AxisRange(-1000.0, 1000.0),
        "y": AxisRange(-1000.0, 1000.0),
        "z": AxisRange(-180.0, 180.0),
        "a": AxisRange(-720.0, 720.0),
    }
    values.update(overrides)
    return AxisLimits(**values)


def make_settings(**overrides):
    values = {
        "aoa_min": -10.0,
        "aoa_max": 10.0,
        "aos_min": -10.0,
        "aos_max": 10.0,
        "aoa_points": 3,
        "aos_points": 3,
        "tip_offset_x": 100.0,
        "tip_offset_y": 10.0,
        "hold_time_s": 1.0,
        "feed_rate": 100.0,
        "axis_limits": make_limits(),
        "serpentine": False,
        "output_comments": True,
    }
    values.update(overrides)
    return CalibrationSettings(**values)
