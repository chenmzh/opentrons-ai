"""Offline regression checks for the no-tip motor music protocols."""

import runpy
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


def load_protocol(name):
    opentrons = ModuleType("opentrons")
    opentrons.protocol_api = SimpleNamespace(ProtocolContext=object)
    opentrons.types = SimpleNamespace(
        Point=lambda x, y, z: SimpleNamespace(x=x, y=y, z=z),
        Location=lambda point, labware: SimpleNamespace(point=point),
    )
    commands = ModuleType("opentrons.protocol_engine.commands")
    commands.SavePositionParams = lambda **kwargs: SimpleNamespace(**kwargs)
    with patch.dict(sys.modules, {
        "opentrons": opentrons,
        "opentrons.protocol_engine.commands": commands,
    }):
        return runpy.run_path(str(Path(__file__).resolve().parents[1] / "protocols" / name))


class MusicProtocolTests(unittest.TestCase):
    def context(self, z_mm):
        context = Mock()
        context.is_simulating.return_value = False
        pipette = context.load_instrument.return_value
        pipette._core._engine_client.execute_command_without_recovery.return_value = (
            SimpleNamespace(position=SimpleNamespace(z=z_mm))
        )
        return context, pipette

    def test_all_moves_preserve_actual_z_and_tested_region(self):
        for name, count in (
            ("ot2_pitch_calibration.py", 33),
            ("ot2_song_of_storms.py", 13),
            ("ot2_song_of_storms_low.py", 13),
        ):
            with self.subTest(name=name):
                protocol = load_protocol(name)
                context, pipette = self.context(189.27)
                protocol["run"](context)
                self.assertEqual(pipette.move_to.call_count, count)
                for call in pipette.move_to.call_args_list:
                    point = call.args[0].point
                    self.assertEqual(point.z, 189.27)
                    self.assertTrue(146.5 <= point.x <= 246.5)
                    self.assertTrue(128.75 <= point.y <= 228.75)
                    self.assertTrue(0 < call.kwargs["speed"] <= 30)
                    self.assertTrue(call.kwargs["force_direct"])
                pipette.aspirate.assert_not_called()
                pipette.dispense.assert_not_called()
                pipette.pick_up_tip.assert_not_called()

    def test_invalid_home_height_blocks_travel(self):
        for name in (
            "ot2_pitch_calibration.py", "ot2_song_of_storms.py", "ot2_song_of_storms_low.py"
        ):
            protocol = load_protocol(name)
            for z_mm in (0, float("nan"), float("inf")):
                with self.subTest(name=name, z_mm=z_mm):
                    context, pipette = self.context(z_mm)
                    with self.assertRaises(RuntimeError):
                        protocol["run"](context)
                    pipette.move_to.assert_not_called()

    def test_motif_notes_and_return_to_center(self):
        protocol = load_protocol("ot2_song_of_storms.py")
        events = list(protocol["note_events"]())
        melody = [event for event in events if event[0] == "MELODY"]
        self.assertEqual([event[1] for event in melody], ["D4", "F4", "D5"] * 2)
        context, pipette = self.context(189.27)
        protocol["run"](context)
        self.assertAlmostEqual(pipette.move_to.call_args.args[0].point.x, 196.5)
        self.assertAlmostEqual(protocol["frequency_hz"](69), 440)

    def test_low_register_preserves_intervals_and_returns_to_center(self):
        protocol = load_protocol("ot2_song_of_storms_low.py")
        melody = [event for event in protocol["note_events"]() if event[0] == "MELODY"]
        self.assertEqual([event[2] for event in melody], [38, 41, 50] * 2)
        context, pipette = self.context(189.27)
        protocol["run"](context)
        self.assertAlmostEqual(pipette.move_to.call_args.args[0].point.x, 196.5)


if __name__ == "__main__":
    unittest.main()
