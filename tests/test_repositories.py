import csv
import os
import tempfile
import unittest

from repositories import GCodeRepository, InitializationGCodeRepository, SettingsRepository, SettingsLoadError
from tests.test_support import make_settings


class TestRepositories(unittest.TestCase):
    # TEST-UNIT-076
    # Requirements: REQ-GUI-003
    def test_settings_csv_round_trip(self):
        repo = SettingsRepository()
        settings = make_settings()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "settings.csv")
            repo.save(path, settings)
            loaded = repo.load(path)
        self.assertEqual(settings, loaded)

    # TEST-UNIT-077
    # Requirements: REQ-GUI-003
    def test_options_round_trip(self):
        repo = SettingsRepository()
        for serpentine in (False, True):
            for comments in (False, True):
                with self.subTest(serpentine=serpentine, comments=comments), tempfile.TemporaryDirectory() as d:
                    s = make_settings(serpentine=serpentine, output_comments=comments)
                    p = os.path.join(d, "settings.csv"); repo.save(p, s)
                    loaded = repo.load(p)
                    self.assertEqual((serpentine, comments), (loaded.serpentine, loaded.output_comments))

    # TEST-UNIT-078
    # Requirements: REQ-GUI-003
    def test_axis_ranges_round_trip(self):
        repo = SettingsRepository(); settings = make_settings()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "settings.csv"); repo.save(p, settings); loaded = repo.load(p)
        self.assertEqual(settings.axis_limits, loaded.axis_limits)

    # TEST-UNIT-079
    # Requirements: REQ-GUI-003
    def test_structurally_invalid_csv_returns_explicit_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write("this,is,not,key,value\n")
            path = f.name
        try:
            with self.assertRaises(SettingsLoadError): SettingsRepository().load(path)
        finally: os.remove(path)

    # TEST-UNIT-080
    # Requirements: REQ-INPUT-006
    def test_initialization_gcode_utf8_multiline(self):
        content = "; 初期化\nG92 X0\nM5\n"
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write(content); path = f.name
        try: self.assertEqual(content, InitializationGCodeRepository().load(path))
        finally: os.remove(path)

    # TEST-UNIT-081
    # Requirements: REQ-INPUT-006
    def test_missing_initialization_file_raises_ioerror(self):
        with self.assertRaises(OSError): InitializationGCodeRepository().load("__missing_init__.txt")

    # TEST-UNIT-082
    # Requirements: REQ-GCODE-001
    def test_save_nc_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.nc"); GCodeRepository().save(path, "G21\n")
            with open(path, encoding="utf-8") as f: self.assertEqual("G21\n", f.read())

    # TEST-UNIT-083
    # Requirements: REQ-GCODE-001
    def test_gcode_save_failure_is_reported(self):
        with self.assertRaises(OSError): GCodeRepository().save(os.path.join("__missing_dir__", "out.nc"), "G21\n")

    # TEST-UNIT-117
    # Requirements: REQ-GUI-003
    def test_missing_required_csv_key(self):
        self._assert_bad_csv({"feed_rate": None})

    # TEST-UNIT-118
    # Requirements: REQ-GUI-003
    def test_blank_required_csv_value(self):
        self._assert_bad_csv({"feed_rate": ""}, omit_none=False)

    # TEST-UNIT-119
    # Requirements: REQ-GUI-003
    def test_non_numeric_csv_value(self):
        self._assert_bad_csv({"feed_rate": "abc"}, omit_none=False)

    # TEST-UNIT-120
    # Requirements: REQ-GUI-003
    def test_settings_io_failure_is_wrapped(self):
        with self.assertRaises(SettingsLoadError): SettingsRepository().load("__missing_settings__.csv")

    def _assert_bad_csv(self, changes, omit_none=True):
        base = {
            "aoa_min":"-10", "aoa_max":"10", "aos_min":"-10", "aos_max":"10",
            "aoa_points":"3", "aos_points":"3", "tip_offset_x":"100", "tip_offset_y":"10",
            "hold_time_s":"1", "feed_rate":"100", "x_min":"-1000", "x_max":"1000",
            "y_min":"-1000", "y_max":"1000", "z_min":"-180", "z_max":"180",
            "a_min":"-720", "a_max":"720", "serpentine":"false", "output_comments":"true"
        }
        base.update(changes)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["key","value"])
            for k,v in base.items():
                if v is None and omit_none: continue
                w.writerow([k,v]); path=f.name
        try:
            with self.assertRaises(SettingsLoadError): SettingsRepository().load(path)
        finally: os.remove(path)


if __name__ == "__main__": unittest.main()
