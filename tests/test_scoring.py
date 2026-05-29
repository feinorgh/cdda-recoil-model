import unittest

import scoring


BULLSEYE = {
    "type": "bullseye",
    "name": "Test Bull",
    # (score, outer_radius_cm), inner ring first
    "rings": [
        (10, 2.5), (9, 5.0), (8, 7.5), (7, 10.0),
        (6, 12.5), (5, 15.0), (4, 17.5), (3, 20.0),
        (2, 22.5), (1, 25.0),
    ],
    "x_ring_radius_cm": 1.25,
    "black_radius_cm": 10.0,
    "size_cm": 55.0,
}


class TestBullseyeScoring(unittest.TestCase):
    def test_center_hit_scores_ten_and_x(self):
        shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 10)
        self.assertEqual(result["x_count"], 1)

    def test_ring_boundaries_score_correctly(self):
        shots = [
            {"x_cm": 0.0, "y_cm": 4.0, "shot_index": 0, "time_s": 0.0},   # 9 ring
            {"x_cm": 0.0, "y_cm": 9.0, "shot_index": 1, "time_s": 0.0},   # 7 ring
            {"x_cm": 0.0, "y_cm": 24.0, "shot_index": 2, "time_s": 0.0},  # 1 ring
        ]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 9 + 7 + 1)

    def test_miss_outside_outer_ring_scores_zero(self):
        shots = [{"x_cm": 30.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 0)

    def test_reports_group_size_and_mpi(self):
        shots = [
            {"x_cm": 1.0, "y_cm": 1.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": -1.0, "y_cm": -1.0, "shot_index": 1, "time_s": 0.0},
        ]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertAlmostEqual(result["group_size_cm"], (8.0) ** 0.5, places=6)
        self.assertAlmostEqual(result["mpi_x_cm"], 0.0, places=6)
        self.assertAlmostEqual(result["mpi_y_cm"], 0.0, places=6)
