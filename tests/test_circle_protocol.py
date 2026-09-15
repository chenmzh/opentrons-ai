"""Offline motion-contract tests; no Opentrons SDK or robot connection needed."""

import math
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class CircleProtocolTests(unittest.TestCase):
    def setUp(self):
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
            self.protocol = runpy.run_path(
                str(Path(__file__).resolve().parents[1] / "protocols/ot2_circle_100mm.py")
            )

    def context(self, home_z=189.27, final_z=189.27):
        context = Mock()
        context.is_simulating.return_value = False
        pipette = context.load_instrument.return_value
        pipette._core._engine_client.execute_command_without_recovery.side_effect = [
            SimpleNamespace(position=SimpleNamespace(z=z)) for z in (home_z, final_z)
        ]
        return context, pipette

    def test_circle_is_closed_and_has_100_mm_diameter(self):
        path = list(self.protocol["xy_path"]())
        self.assertEqual(len(path), 182)
        self.assertEqual(path[0], {"x": 196.5, "y": 178.75})
        for point in path[1:]:
            self.assertAlmostEqual(math.hypot(point["x"] - 196.5, point["y"] - 178.75), 50)
        self.assertAlmostEqual(path[1]["x"], path[-1]["x"])
        self.assertAlmostEqual(path[1]["y"], path[-1]["y"])

    def test_motion_keeps_measured_home_height_and_requested_speed(self):
        context, pipette = self.context()
        self.protocol["run"](context)
        self.assertEqual(pipette.move_to.call_count, 182)
        for call in pipette.move_to.call_args_list:
            self.assertEqual(call.args[0].point.z, 189.27)
            self.assertEqual(call.kwargs, {"force_direct": True, "speed": 30.0})
        context.home.assert_called_once()
        context.load_instrument.assert_called_once_with("p300_multi_gen2", "left")

    def test_invalid_home_height_prevents_xy_motion(self):
        for z in (0.0, 149.9, float("nan"), float("inf")):
            with self.subTest(z=z):
                context, pipette = self.context(home_z=z)
                with self.assertRaises(RuntimeError):
                    self.protocol["run"](context)
                pipette.move_to.assert_not_called()

    def test_final_height_discrepancy_is_reported(self):
        context, _ = self.context(final_z=188.0)
        with self.assertRaisesRegex(RuntimeError, "Final Z"):
            self.protocol["run"](context)


if __name__ == "__main__":
    unittest.main()
