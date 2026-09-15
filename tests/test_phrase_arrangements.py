"""Cross-song invariants for the complete phrase-based arrangements."""

import runpy
import unittest
from pathlib import Path

from opentrons_ai.music_runner import validate_commands


class PhraseArrangementTests(unittest.TestCase):
    def test_all_songs_preserve_margin_and_only_turn_at_phrase_boundaries(self):
        for name, count, turns in (("ot2_happy_birthday.py", 91, 12),
                                   ("ot2_jingle_bells.py", 99, 15),
                                   ("ot2_song_of_storms_full.py", 86, 13)):
            with self.subTest(song=name):
                source = runpy.run_path(str(Path(__file__).resolve().parents[1] / "protocols" / name))
                arrangement = source["compose"]()
                notes = arrangement["notes"]
                self.assertEqual(len(notes), count)
                previous = None
                x_mm = arrangement["start_x_mm"]
                reversals = 0
                self.assertTrue(151.5 <= x_mm <= 241.5)
                for event in notes:
                    self.assertTrue(151.5 <= event["x_mm"] <= 241.5)
                    self.assertAlmostEqual(abs(event["x_mm"] - x_mm),
                                           event["tone_s"] * event["speed_mm_s"])
                    self.assertEqual(1 if event["x_mm"] > x_mm else -1, event["direction"])
                    if previous and event["direction"] != previous["direction"]:
                        self.assertNotEqual(event["phrase"], previous["phrase"])
                        reversals += 1
                    previous, x_mm = event, event["x_mm"]
                self.assertEqual(reversals, turns)

    def test_birthday_full_arrangement_contains_three_complete_themes(self):
        source = runpy.run_path(str(Path(__file__).resolve().parents[1]
                                   / "protocols" / "ot2_happy_birthday.py"))
        score = source["score_phrases"]()
        self.assertEqual(score[1:5], source["PHRASES"])
        self.assertEqual(score[6:10], source["PHRASES"])
        self.assertEqual(score[10:14], source["PHRASES"])
        self.assertEqual(score[0], source["INTRO"])
        self.assertEqual(score[-1], source["CODA"])
        self.assertAlmostEqual(sum(e["duration_s"] for e in source["compose"]()["notes"]), 56.25)

    def test_transport_enforces_inset_and_song_specific_speed_limit(self):
        event = dict(x_mm=200.0, speed_mm_s=35.0)
        commands = [dict(commandType="moveToCoordinates", status="succeeded", params=dict(
            coordinates=dict(x=x, y=178.75, z=200.0), speed=speed, forceDirect=True))
            for x, speed in ((196.5, 30), (200.0, 35))]
        with self.assertRaises(RuntimeError):
            validate_commands(commands, [event], True)
        self.assertEqual(validate_commands(commands, [event], True, max_speed_mm_s=36), 200)
        commands[1]["params"]["coordinates"]["x"] = event["x_mm"] = 149
        with self.assertRaises(RuntimeError):
            validate_commands(commands, [event], True, max_speed_mm_s=36)
        with self.assertRaises(RuntimeError):
            validate_commands(commands, [event], True, max_speed_mm_s=40)


if __name__ == "__main__":
    unittest.main()
