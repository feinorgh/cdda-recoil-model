import unittest

import targets


class TestTargetDefs(unittest.TestCase):
    def test_all_three_targets_defined(self):
        self.assertIn("bullseye", targets.TARGET_DEFS)
        self.assertIn("popper", targets.TARGET_DEFS)
        self.assertIn("ipsc_silhouette", targets.TARGET_DEFS)
        for key, td in targets.TARGET_DEFS.items():
            self.assertEqual(td["type"], key)


class TestBullseyeSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["bullseye"]
        self.shots = [
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": 2.0, "y_cm": -3.0, "shot_index": 1, "time_s": 0.5},
        ]
        self.score = {
            "target": "bullseye", "total_score": 19, "x_count": 1,
            "group_size_cm": 3.6, "mpi_x_cm": 1.0, "mpi_y_cm": -1.5,
            "per_shot": [], "vertical_walk_cm": -3.0,
        }
        self.run_meta = {
            "scenario": "Test", "gun": "Glock 17", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 25, "shot_count": 2,
            "time_limit_s": 5,
        }

    def test_returns_well_formed_svg_string(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("</svg>", svg)

    def test_draws_one_marker_per_shot(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertEqual(svg.count('class="shot"'), len(self.shots))

    def test_includes_stats_panel_text(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertIn("Glock 17", svg)
        self.assertIn("Cassie", svg)


class TestPopperSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["popper"]
        self.shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.3}]
        self.run_meta = {
            "scenario": "Speed", "gun": "MP5-N", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 10, "shot_count": 1, "time_limit_s": 1.5,
        }

    def test_neutralized_popper_shows_stamp(self):
        score = {
            "target": "popper", "neutralized": True,
            "shots_to_neutralize": 1, "time_to_hit_s": 0.3, "group_size_cm": 0.0,
        }
        svg = targets.render_svg(self.target_def, self.shots, score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("NEUTRALIZED", svg)
        self.assertEqual(svg.count('class="shot"'), 1)

    def test_standing_popper_has_no_stamp(self):
        score = {
            "target": "popper", "neutralized": False,
            "shots_to_neutralize": None, "time_to_hit_s": None, "group_size_cm": 0.0,
        }
        svg = targets.render_svg(self.target_def, self.shots, score, self.run_meta)
        self.assertNotIn("NEUTRALIZED", svg)


class TestIpscSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["ipsc_silhouette"]
        self.shots = [
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": 5.0, "y_cm": -5.0, "shot_index": 1, "time_s": 0.3},
        ]
        self.score = {
            "target": "ipsc_silhouette", "total_points": 10,
            "zone_counts": {"A": 2, "C": 0, "D": 0}, "misses": 0,
            "hit_factor": 5.0, "group_size_cm": 7.1,
        }
        self.run_meta = {
            "scenario": "IPSC", "gun": "Glock 17", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 10, "shot_count": 2, "time_limit_s": 2,
        }

    def test_renders_zones_and_hit_factor(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertEqual(svg.count('class="zone"'), len(self.target_def["zones"]))
        self.assertEqual(svg.count('class="shot"'), len(self.shots))
        self.assertIn("5.00", svg)  # hit factor formatted


class TestOverlaySvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["bullseye"]

        def mk(total):
            return {
                "target": "bullseye", "total_score": total, "x_count": 0,
                "group_size_cm": 3.0, "mpi_x_cm": 0.0, "mpi_y_cm": 0.0,
                "per_shot": [], "vertical_walk_cm": 1.0,
            }

        self.series = [
            {"label": "standing", "color": "#c0392b",
             "shots": [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}],
             "score": mk(10)},
            {"label": "crouching", "color": "#2471a3",
             "shots": [
                 {"x_cm": 1.0, "y_cm": 1.0, "shot_index": 0, "time_s": 0.0},
                 {"x_cm": 2.0, "y_cm": -1.0, "shot_index": 1, "time_s": 1.0},
             ],
             "score": mk(18)},
            {"label": "prone", "color": "#1e8449",
             "shots": [{"x_cm": 0.0, "y_cm": 0.5, "shot_index": 0, "time_s": 0.0}],
             "score": mk(20)},
        ]
        self.run_meta = {
            "gun": "Glock 17", "ammo": "FMJ", "shooter": "Commando Cassie",
            "range_m": 25, "shot_count": 5, "time_limit_s": 5.0,
        }

    def test_well_formed_svg(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("</svg>", svg)

    def test_three_stance_colors_present(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        for color in ("#c0392b", "#2471a3", "#1e8449"):
            self.assertIn(color, svg)

    def test_all_shot_markers_drawn(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        total = sum(len(s["shots"]) for s in self.series)
        self.assertEqual(svg.count('class="shot"'), total)

    def test_legend_has_labels_and_range(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        for label in ("standing", "crouching", "prone"):
            self.assertIn(label, svg)
        self.assertIn("25 m", svg)
