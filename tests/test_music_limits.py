"""Geometry and speed-ceiling checks for the explicitly authorized range test."""

import runpy
import unittest
from pathlib import Path


class MusicLimitsTests(unittest.TestCase):
    def setUp(self):
        self.protocol = runpy.run_path(str(Path(__file__).resolve().parents[1]
                                          / "protocols" / "ot2_music_limits.py"))

    def test_sweeps_cover_ceiling_both_directions_and_stay_inset(self):
        blocks = self.protocol["test_blocks"]()
        sweeps = [b for b in blocks if b["kind"] == "RANGE"]
        self.assertEqual([b["value"] for b in sweeps], list(self.protocol["SPEEDS_MM_S"]))
        self.assertEqual(sweeps[-1]["value"], 400)
        for block in blocks:
            x_mm = block["start_x_mm"]
            for note in block["notes"]:
                self.assertTrue(151.5 <= x_mm <= 241.5)
                self.assertTrue(151.5 <= note["x_mm"] <= 241.5)
                self.assertTrue(0 < note["speed_mm_s"] <= 400)
                self.assertAlmostEqual(abs(note["x_mm"] - x_mm) / note["speed_mm_s"],
                                       note["duration_s"])
                x_mm = note["x_mm"]
            self.assertAlmostEqual(x_mm, block["start_x_mm"])
        for block in sweeps:
            self.assertEqual({n["direction"] for n in block["notes"]}, {-1, 1})

    def test_tempo_blocks_change_duration_without_changing_pitch(self):
        rhythm = [b for b in self.protocol["test_blocks"]() if b["kind"] == "RHYTHM"]
        self.assertEqual(len(rhythm), 7)
        for block in rhythm:
            self.assertEqual([n["midi"] for n in block["notes"]], [38, 41, 50, 41] * 4)
            self.assertEqual([n["speed_mm_s"] for n in block["notes"]],
                             [n["speed_mm_s"] for n in rhythm[0]["notes"]])
            self.assertTrue(all(n["gap_s"] == 0 for n in block["notes"]))

    def test_refinement_stays_inset_and_changes_direction_at_phrase_boundaries(self):
        protocol = runpy.run_path(str(Path(__file__).resolve().parents[1]
                                     / "protocols" / "ot2_music_limits_refine.py"))
        blocks = protocol["test_blocks"]()
        self.assertLess(max(protocol["SPEEDS_MM_S"]), 400)
        self.assertEqual(len(blocks), 18)
        for block in blocks:
            x_mm = block["start_x_mm"]
            for note in block["notes"]:
                self.assertTrue(151.5 <= x_mm <= 241.5)
                self.assertTrue(151.5 <= note["x_mm"] <= 241.5)
                self.assertTrue(0 < note["speed_mm_s"] <= 400)
                self.assertAlmostEqual(abs(note["x_mm"] - x_mm) / note["speed_mm_s"],
                                       note["duration_s"])
                x_mm = note["x_mm"]
            self.assertAlmostEqual(x_mm, block["start_x_mm"])
            if block["kind"] == "RHYTHM":
                self.assertEqual([n["direction"] for n in block["notes"]],
                                 [1] * 4 + [-1] * 4 + [1] * 4 + [-1] * 4)


if __name__ == "__main__":
    unittest.main()
