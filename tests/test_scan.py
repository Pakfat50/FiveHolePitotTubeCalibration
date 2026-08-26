import unittest

from scan import ScanPlanner
from tests.test_support import make_settings


class TestScanPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = ScanPlanner()

    # TEST-UNIT-017
    # Requirements: REQ-SCAN-001
    def test_minimum_grid_has_four_endpoints(self):
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=2))
        self.assertEqual(4, len(points))
        self.assertEqual({(-10.0, -10.0), (-10.0, 10.0), (10.0, -10.0), (10.0, 10.0)}, {(p.aoa, p.aos) for p in points})

    # TEST-UNIT-018
    # Requirements: REQ-SCAN-001
    def test_aoa_equal_spacing(self):
        points = self.planner.generate_points(make_settings(aoa_min=-10, aoa_max=10, aoa_points=5, aos_points=2))
        self.assertEqual([-10, -5, 0, 5, 10], sorted({p.aoa for p in points}))

    # TEST-UNIT-019
    # Requirements: REQ-SCAN-001
    def test_aos_equal_spacing(self):
        points = self.planner.generate_points(make_settings(aos_min=-20, aos_max=20, aos_points=5, aoa_points=2))
        self.assertEqual([-20, -10, 0, 10, 20], sorted({p.aos for p in points}))

    # TEST-UNIT-020
    # Requirements: REQ-SCAN-002
    def test_basic_scan_aoa_outer_aos_inner(self):
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=3, serpentine=False))
        self.assertEqual([(-10,-10),(-10,0),(-10,10),(10,-10),(10,0),(10,10)], [(p.aoa,p.aos) for p in points])

    # TEST-UNIT-021
    # Requirements: REQ-SCAN-003
    def test_serpentine_second_row_reversed(self):
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=3, serpentine=True))
        self.assertEqual([(-10,-10),(-10,0),(-10,10),(10,10),(10,0),(10,-10)], [(p.aoa,p.aos) for p in points])

    # TEST-UNIT-022
    # Requirements: REQ-SCAN-003
    def test_serpentine_three_rows_alternate(self):
        points = self.planner.generate_points(make_settings(aoa_points=3, aos_points=3, serpentine=True))
        rows = [[p.aos for p in points[i:i+3]] for i in range(0,9,3)]
        self.assertEqual([[-10,0,10],[10,0,-10],[-10,0,10]], rows)

    # TEST-UNIT-023
    # Requirements: REQ-SCAN-001
    def test_total_point_count(self):
        self.assertEqual(20, len(self.planner.generate_points(make_settings(aoa_points=4, aos_points=5))))

    # TEST-UNIT-024
    # Requirements: REQ-SCAN-001, REQ-SCAN-002
    def test_indices_are_unique_and_sequential(self):
        points = self.planner.generate_points(make_settings(aoa_points=3, aos_points=4))
        self.assertEqual(list(range(len(points))), [p.index for p in points])


if __name__ == "__main__": unittest.main()
