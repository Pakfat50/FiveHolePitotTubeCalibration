"""較正点走査計画の単体テスト。

File: test_scan.py
ScanPlanner の等間隔格子、走査順、蛇行、点番号を検証する。
Details:
    docs/test_specification.md の TEST-UNIT-017..024 に対応する。
"""

import unittest

from scan import ScanPlanner
from tests.test_support import make_settings


class TestScanPlanner(unittest.TestCase):
    """@brief ScanPlanner が要求された較正点集合と走査順を生成することを確認する。"""

    def setUp(self):
        """@brief 各テストで独立した ScanPlanner を生成する。"""
        self.planner = ScanPlanner()

    # TEST-UNIT-017
    # Requirements: REQ-SCAN-001
    def test_minimum_grid_has_four_endpoints(self):
        """@brief 最小2×2格子が4端点をすべて含むことを確認する。

        Test:
            TEST-UNIT-017: AoA/AoS各2点では両端の直積4点を生成すること。
        Details:
            生成点数とAoA/AoS座標集合を同時に比較する。
        Verification rationale:
            点数だけでなく4つの端点座標そのものを照合するため、両端を含む格子生成を直接確認できる。
        See Also:
            REQ-SCAN-001
        """
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=2))
        self.assertEqual(4, len(points))
        self.assertEqual({(-10.0, -10.0), (-10.0, 10.0), (10.0, -10.0), (10.0, 10.0)}, {(p.aoa, p.aos) for p in points})

    # TEST-UNIT-018
    # Requirements: REQ-SCAN-001
    def test_aoa_equal_spacing(self):
        """@brief AoA方向が両端を含む等間隔になることを確認する。

        Test:
            TEST-UNIT-018: -10～10度を5点指定した場合、AoAが[-10,-5,0,5,10]となること。
        Details:
            生成点からAoAの一意値を抽出し、理論上の等間隔列と比較する。
        Verification rationale:
            実際のAoA座標列を期待値と完全一致比較するため、間隔と端点包含を同時に確認できる。
        See Also:
            REQ-SCAN-001
        """
        points = self.planner.generate_points(make_settings(aoa_min=-10, aoa_max=10, aoa_points=5, aos_points=2))
        self.assertEqual([-10, -5, 0, 5, 10], sorted({p.aoa for p in points}))

    # TEST-UNIT-019
    # Requirements: REQ-SCAN-001
    def test_aos_equal_spacing(self):
        """@brief AoS方向が両端を含む等間隔になることを確認する。

        Test:
            TEST-UNIT-019: -20～20度を5点指定した場合、AoSが[-20,-10,0,10,20]となること。
        Details:
            生成点からAoSの一意値を抽出し、期待する等間隔列と比較する。
        Verification rationale:
            実座標を全点比較するため、AoSの端点・点数・等間隔性を直接検証できる。
        See Also:
            REQ-SCAN-001
        """
        points = self.planner.generate_points(make_settings(aos_min=-20, aos_max=20, aos_points=5, aoa_points=2))
        self.assertEqual([-20, -10, 0, 10, 20], sorted({p.aos for p in points}))

    # TEST-UNIT-020
    # Requirements: REQ-SCAN-002
    def test_basic_scan_aoa_outer_aos_inner(self):
        """@brief 通常走査でAoAが外側、AoSが内側ループになることを確認する。

        Test:
            TEST-UNIT-020: serpentine=Falseでは同一AoA行内でAoSを走査し、完了後に次AoAへ移ること。
        Details:
            2×3格子の生成順を期待する6点列と完全一致比較する。
        Verification rationale:
            集合ではなく順序付き座標列を比較するため、ループの入れ子順序まで確認できる。
        See Also:
            REQ-SCAN-002
        """
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=3, serpentine=False))
        self.assertEqual([(-10,-10),(-10,0),(-10,10),(10,-10),(10,0),(10,10)], [(p.aoa,p.aos) for p in points])

    # TEST-UNIT-021
    # Requirements: REQ-SCAN-003
    def test_serpentine_second_row_reversed(self):
        """@brief 蛇行走査で2行目のAoS方向が反転することを確認する。

        Test:
            TEST-UNIT-021: serpentine=Trueでは隣接AoA行ごとにAoS走査方向を反転すること。
        Details:
            2×3格子の全走査順を期待列と比較する。
        Verification rationale:
            1行目の昇順と2行目の降順を同時に観測するため、蛇行反転動作を直接確認できる。
        See Also:
            REQ-SCAN-003
        """
        points = self.planner.generate_points(make_settings(aoa_points=2, aos_points=3, serpentine=True))
        self.assertEqual([(-10,-10),(-10,0),(-10,10),(10,10),(10,0),(10,-10)], [(p.aoa,p.aos) for p in points])

    # TEST-UNIT-022
    # Requirements: REQ-SCAN-003
    def test_serpentine_three_rows_alternate(self):
        """@brief 3行以上でも蛇行方向が交互に切り替わることを確認する。

        Test:
            TEST-UNIT-022: 3行のAoS方向が昇順→降順→昇順となること。
        Details:
            3×3格子をAoA行ごとに分割し、各行のAoS配列を比較する。
        Verification rationale:
            2行だけでなく3行目で元方向へ戻ることを確認するため、単発反転ではなく交互反転ロジックを検証できる。
        See Also:
            REQ-SCAN-003
        """
        points = self.planner.generate_points(make_settings(aoa_points=3, aos_points=3, serpentine=True))
        rows = [[p.aos for p in points[i:i+3]] for i in range(0,9,3)]
        self.assertEqual([[-10,0,10],[10,0,-10],[-10,0,10]], rows)

    # TEST-UNIT-023
    # Requirements: REQ-SCAN-001
    def test_total_point_count(self):
        """@brief 総較正点数がAoA点数×AoS点数になることを確認する。

        Test:
            TEST-UNIT-023: 4×5指定では20点を生成すること。
        Details:
            生成リスト長を点数の直積と比較する。
        Verification rationale:
            直積格子の総数を直接観測するため、点の欠落・重複による件数不整合を検出できる。
        See Also:
            REQ-SCAN-001
        """
        self.assertEqual(20, len(self.planner.generate_points(make_settings(aoa_points=4, aos_points=5))))

    # TEST-UNIT-024
    # Requirements: REQ-SCAN-001, REQ-SCAN-002
    def test_indices_are_unique_and_sequential(self):
        """@brief 較正点indexが走査順に0から連番で付与されることを確認する。

        Test:
            TEST-UNIT-024: 全点のindexが重複なく0..N-1であること。
        Details:
            生成順のindex列をrange(N)と完全一致比較する。
        Verification rationale:
            順序付きindex列を直接比較するため、重複、欠番、走査順との不一致を同時に検出できる。
        See Also:
            REQ-SCAN-001, REQ-SCAN-002
        """
        points = self.planner.generate_points(make_settings(aoa_points=3, aos_points=4))
        self.assertEqual(list(range(len(points))), [p.index for p in points])


if __name__ == "__main__":
    unittest.main()
