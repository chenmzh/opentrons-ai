"""Whole-phrase composition and shared launcher regression checks."""

import runpy
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from opentrons_ai.music_runner import validate_commands


class HappyBirthdayTests(unittest.TestCase):
    def setUp(self):
        self.protocol = runpy.run_path(str(Path(__file__).resolve().parents[1]
                                          / "protocols" / "ot2_happy_birthday.py"))

    def test_complete_melody_and_only_two_phrase_reversals(self):
        arrangement = self.protocol["compose"](phrases=self.protocol["PHRASES"])
        notes = arrangement["notes"]
        self.assertEqual(len(notes), 25)
        self.assertEqual(arrangement["directions"], (1, 1, -1, 1))
        self.assertEqual([e["note"] for e in notes[:6]], ["G1", "G1", "A1", "G1", "C2", "B1"])
        self.assertEqual(notes[-1]["note"], "C2")
        self.assertAlmostEqual(sum(e["duration_s"] for e in notes), 15)
        start_x = x_mm = arrangement["start_x_mm"]
        points = [x_mm]
        for event in notes:
            distance = event["x_mm"] - x_mm
            self.assertEqual(1 if distance > 0 else -1, event["direction"])
            self.assertAlmostEqual(abs(distance) / event["speed_mm_s"], event["tone_s"])
            self.assertAlmostEqual(event["tone_s"] + event["gap_after_s"], event["duration_s"])
            x_mm = event["x_mm"]
            points.append(x_mm)
        self.assertGreaterEqual(min(points), 151.5)
        self.assertLessEqual(max(points), 241.5)
        # Centering the full path, rather than starting at the center, is required.
        self.assertLess(start_x, 160)
        self.assertAlmostEqual((min(points) + max(points)) / 2, 196.5)
        turns = 0
        for previous, current in zip(notes[:-1], notes[1:], strict=True):
            if previous["direction"] != current["direction"]:
                turns += 1
                self.assertNotEqual(previous["phrase"], current["phrase"])
        self.assertEqual(turns, 2)

    def test_tempo_replans_whole_phrases_and_rejects_infeasible_travel(self):
        faster = self.protocol["compose"](120, phrases=self.protocol["PHRASES"])
        directions = faster["directions"]
        self.assertEqual(sum(directions[i] != directions[i - 1] for i in range(1, 4)), 1)
        for tempo in (0, float("nan"), float("inf"), 30):
            with self.assertRaises(ValueError):
                self.protocol["compose"](tempo)
        with self.assertRaises(ValueError):
            self.protocol["choose_phrase_path"]([91])

    def test_custom_approach_verified_by_shared_transport(self):
        arrangement = self.protocol["compose"]()
        moves = [dict(x_mm=arrangement["start_x_mm"], speed_mm_s=30), *arrangement["notes"]]
        commands = [dict(commandType="moveToCoordinates", status="succeeded", params=dict(
            forceDirect=True, speed=e["speed_mm_s"],
            coordinates=dict(x=e["x_mm"], y=178.75, z=200.0))) for e in moves]
        self.assertEqual(validate_commands(commands, arrangement["notes"], True,
                                           arrangement["start_x_mm"]), 200)
        with self.assertRaises(RuntimeError):
            validate_commands(commands, arrangement["notes"], True)

    def test_robot_uses_precomposed_path_and_fixed_z(self):
        opentrons = ModuleType("opentrons")
        opentrons.types = SimpleNamespace(
            Point=lambda x, y, z: SimpleNamespace(x=x, y=y, z=z),
            Location=lambda point, labware: SimpleNamespace(point=point))
        commands = ModuleType("opentrons.protocol_engine.commands")
        commands.SavePositionParams = lambda **kwargs: SimpleNamespace(**kwargs)
        with patch.dict(sys.modules, {"opentrons": opentrons,
                                     "opentrons.protocol_engine.commands": commands}):
            context = Mock()
            context.is_simulating.return_value = False
            pipette = context.load_instrument.return_value
            pipette._core._engine_client.execute_command_without_recovery.return_value = (
                SimpleNamespace(position=SimpleNamespace(z=189.27)))
            self.protocol["run"](context)
            self.assertEqual(pipette.move_to.call_count, 92)
            for call in pipette.move_to.call_args_list:
                self.assertEqual(call.args[0].point.z, 189.27)
                self.assertTrue(151.5 <= call.args[0].point.x <= 241.5)
            self.assertEqual(sum(c.args[0].startswith("PHRASE")
                                 for c in context.comment.call_args_list), 15)
            pipette.aspirate.assert_not_called()
            pipette.dispense.assert_not_called()
            pipette.pick_up_tip.assert_not_called()


if __name__ == "__main__":
    unittest.main()
