"""Offline checks for the complete fixed-height motor melody."""

import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from test_music_protocol import load_protocol


class FullMusicTests(unittest.TestCase):
    def setUp(self):
        opentrons = ModuleType("opentrons")
        opentrons.types = SimpleNamespace(
            Point=lambda x, y, z: SimpleNamespace(x=x, y=y, z=z),
            Location=lambda point, labware: SimpleNamespace(point=point))
        commands = ModuleType("opentrons.protocol_engine.commands")
        commands.SavePositionParams = lambda **kwargs: SimpleNamespace(**kwargs)
        mock_imports = patch.dict(sys.modules, {"opentrons": opentrons,
                                 "opentrons.protocol_engine.commands": commands})
        mock_imports.start()
        self.addCleanup(mock_imports.stop)
        self.protocol = load_protocol("ot2_song_of_storms_full.py")

    def test_complete_score_and_relative_pitch(self):
        arrangement = self.protocol["compose"]()
        plan = arrangement["notes"]
        self.assertEqual(len(plan), 86)
        self.assertEqual([row["note"] for row in plan[:3]], ["D2", "F2", "D3"])
        self.assertEqual(plan[-1]["note"], "D2")
        self.assertEqual([e["note"] for e in plan[:43]], [e["note"] for e in plan[43:]])
        self.assertAlmostEqual(plan[2]["speed_mm_s"] / plan[0]["speed_mm_s"], 2)
        self.assertAlmostEqual(sum(row["duration_s"] for row in plan), 90 * 60 / 132)
        x_mm = arrangement["start_x_mm"]
        for event in plan:
            target_x, speed = event["x_mm"], event["speed_mm_s"]
            self.assertTrue(151.5 <= target_x <= 241.5)
            self.assertTrue(0 < speed <= 36)
            self.assertAlmostEqual(abs(target_x - x_mm) / speed, event["tone_s"])
            x_mm = target_x

    def context(self, *z_positions):
        context = Mock()
        context.is_simulating.return_value = False
        pipette = context.load_instrument.return_value
        pipette._core._engine_client.execute_command_without_recovery.side_effect = [
            SimpleNamespace(position=SimpleNamespace(z=z)) for z in z_positions
        ]
        return context, pipette

    def test_fixed_z_and_no_liquid_handling(self):
        context, pipette = self.context(189.27, 189.27)
        self.protocol["run"](context)
        self.assertEqual(pipette.move_to.call_count, 87)
        for call in pipette.move_to.call_args_list:
            self.assertEqual(call.args[0].point.z, 189.27)
            self.assertEqual(call.args[0].point.y, 178.75)
            self.assertTrue(call.kwargs["force_direct"])
        pipette.pick_up_tip.assert_not_called()
        pipette.aspirate.assert_not_called()
        pipette.dispense.assert_not_called()

    def test_invalid_height_prevents_travel_and_drift_is_reported(self):
        for z_mm in (0, float("nan"), float("inf")):
            context, pipette = self.context(z_mm)
            with self.assertRaises(RuntimeError):
                self.protocol["run"](context)
            pipette.move_to.assert_not_called()
        context, _ = self.context(189.27, 189.4)
        with self.assertRaisesRegex(RuntimeError, "Z changed"):
            self.protocol["run"](context)


if __name__ == "__main__":
    unittest.main()
