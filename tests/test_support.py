"""テスト共通データ生成ヘルパー。

File: test_support.py
単体・ユースケーステストで共通利用する既定設定、軸範囲、数値許容誤差を提供する。
テストごとの差分だけを明示できるよう、正常系の基準値を一箇所に集約する。
"""

from models import AxisLimits, AxisRange, CalibrationSettings

# 数値仕様で要求される絶対誤差0.001以内をテスト側の共通許容値として使用する。
ABS_TOL = 0.001


def make_limits(**overrides):
    """標準の十分広い軸可動範囲を生成する。

    Args:
        overrides: 軸名(x/y/z/a)をキー、AxisRangeを値とする上書き指定

    Returns:
        上書き適用後のAxisLimits
    通常は範囲超過が起きない基準値を返し、各テストでは対象軸だけを上書きして異常条件を作る。
    設計根拠:
    非対象軸を常に正常範囲へ固定することで、範囲試験の失敗原因を対象軸へ限定し、テストの独立性と可読性を高める。
    """
    values = {
        "x": AxisRange(-1000.0, 1000.0),
        "y": AxisRange(-1000.0, 1000.0),
        "z": AxisRange(-180.0, 180.0),
        "a": AxisRange(-720.0, 720.0),
    }
    values.update(overrides)
    return AxisLimits(**values)


def make_settings(**overrides):
    """全入力が有効な標準CalibrationSettingsを生成する。

    Args:
        overrides: CalibrationSettingsのフィールド名をキーとする上書き指定

    Returns:
        上書き適用後のCalibrationSettings
    各テストは確認対象フィールドだけを変更し、それ以外を既知の正常値に保つために利用する。
    設計根拠:
    テストごとに大量の正常値を重複記述せず、変更点だけを明示することで、何を刺激して何を観測するテストなのかを読み取りやすくする。
    """
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
