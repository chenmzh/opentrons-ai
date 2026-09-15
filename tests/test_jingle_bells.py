"""Regression checks for the dual host/robot script and execution boundaries."""

import copy
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from opentrons_ai import music_runner as runner

PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "protocols" / "ot2_jingle_bells.py"


class JingleBellsTests(unittest.TestCase):
    def setUp(self):
        configuration = patch.dict("os.environ", {"OT2_URL": "http://robot.invalid:31950"})
        configuration.start()
        self.addCleanup(configuration.stop)
        self.protocol = runpy.run_path(str(PROTOCOL_PATH))
        self.arrangement = self.protocol["compose"]()
        self.plan = self.arrangement["notes"]
        self.start_x_mm = self.arrangement["start_x_mm"]

    def commands(self):
        return [dict(commandType="moveToCoordinates", status="succeeded", params=dict(
            forceDirect=True, speed=e["speed_mm_s"],
            coordinates=dict(x=e["x_mm"], y=178.75, z=200.0)))
            for e in [dict(x_mm=self.start_x_mm, speed_mm_s=30.0), *self.plan]]

    def test_score_and_bounded_durations(self):
        self.assertEqual(len(self.plan), 99)
        self.assertAlmostEqual(sum(e["duration_s"] for e in self.plan), 128 * 60 / 132)
        chorus = [e for e in self.plan if e["phrase"] > 8]
        self.assertEqual([e["note"] for e in chorus[:7]], ["E2"] * 7)
        self.assertEqual(chorus[-1]["note"], "C2")
        self.assertEqual({e["phrase"] for e in chorus}, set(range(9, 17)))
        x_mm = self.start_x_mm
        for event in self.plan:
            self.assertTrue(146.5 <= event["x_mm"] <= 246.5)
            self.assertTrue(0 < event["speed_mm_s"] <= 30)
            self.assertAlmostEqual(abs(event["x_mm"] - x_mm) / event["speed_mm_s"],
                                   event["tone_s"])
            x_mm = event["x_mm"]

    def test_robot_preserves_actual_z_and_rejects_invalid_height(self):
        opentrons = ModuleType("opentrons")
        opentrons.types = SimpleNamespace(
            Point=lambda x, y, z: SimpleNamespace(x=x, y=y, z=z),
            Location=lambda point, labware: SimpleNamespace(point=point))
        commands = ModuleType("opentrons.protocol_engine.commands")
        commands.SavePositionParams = lambda **kwargs: SimpleNamespace(**kwargs)
        with patch.dict(sys.modules, {"opentrons": opentrons,
                                     "opentrons.protocol_engine.commands": commands}):
            for z_mm in (189.27, 0, float("nan")):
                context = Mock()
                context.is_simulating.return_value = False
                pipette = context.load_instrument.return_value
                pipette._core._engine_client.execute_command_without_recovery.return_value = (
                    SimpleNamespace(position=SimpleNamespace(z=z_mm)))
                if z_mm != 189.27:
                    with self.assertRaises(RuntimeError):
                        self.protocol["run"](context)
                    pipette.move_to.assert_not_called()
                    continue
                self.protocol["run"](context)
                self.assertEqual(pipette.move_to.call_count, 100)
                for call in pipette.move_to.call_args_list:
                    self.assertEqual(call.args[0].point.z, z_mm)
                pipette.aspirate.assert_not_called()
                pipette.dispense.assert_not_called()
                pipette.pick_up_tip.assert_not_called()

    def test_analysis_rejects_liquid_handling_changed_notes_and_z(self):
        commands = self.commands()
        self.assertEqual(runner.validate_commands(commands, self.plan, True, self.start_x_mm), 200.0)
        bad_sets = [commands + [dict(commandType="aspirate", status="succeeded")], commands[:-1]]
        for key, value in (("z", 201), ("x", 300)):
            changed = copy.deepcopy(commands)
            changed[1]["params"]["coordinates"][key] = value
            bad_sets.append(changed)
        changed = copy.deepcopy(commands)
        changed[1]["params"]["speed"] *= 1.01
        bad_sets.append(changed)
        for bad in bad_sets:
            with self.assertRaises(RuntimeError):
                runner.validate_commands(bad, self.plan, True, self.start_x_mm)

    def test_waiting_never_stops_or_releases_active_run(self):
        api = Mock()
        api.request.side_effect = [dict(data=[dict(id="old", status=s, current=True)])
                                   for s in ("running", "paused", "finishing", "succeeded")]
        with patch.object(runner.time, "sleep"):
            result = runner.wait_idle(api, 60)
        self.assertEqual(result[0]["status"], "succeeded")
        self.assertTrue(all(c.args == ("/runs",) for c in api.request.call_args_list))
        api.request.side_effect = None
        api.request.return_value = dict(data=[dict(id="old", status="running", current=True)])
        with self.assertRaisesRegex(RuntimeError, "等待超时"):
            runner.wait_idle(api, 0)

    def test_failed_analysis_prevents_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            api = Mock(directory=Path(directory))
            api.upload.return_value = dict(id="p", analysisSummaries=[dict(id="a")])
            api.request.return_value = dict(data=dict(status="completed", result="not-ok",
                                                      errors=["simulation failed"]))
            with self.assertRaisesRegex(RuntimeError, "模拟未通过"):
                runner.prepare(api, PROTOCOL_PATH, self.plan)
            self.assertEqual(api.request.call_args.args, ("/protocols/p/analyses/a",))

    def test_ambiguous_play_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            api = runner.RobotAPI(Path(directory))
            api.opener = Mock()
            api.opener.open.side_effect = TimeoutError("test timeout")
            with self.assertRaisesRegex(RuntimeError, "不会自动重发"):
                api.request("/runs/known/actions", "POST", {"data": {"actionType": "play"}})
            self.assertEqual(api.opener.open.call_count, 1)
            intent = json.loads((Path(directory) / "0001-intent.json").read_text())
            self.assertEqual(intent["path"], "/runs/known/actions")

    def test_upload_uses_exact_source_and_controller_lock_excludes_second_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            api = runner.RobotAPI(root)
            api.request = Mock(return_value=dict(data=dict(id="uploaded")))
            api.upload(PROTOCOL_PATH)
            self.assertIn(PROTOCOL_PATH.read_bytes(), api.request.call_args.kwargs["body"])
            self.assertEqual((root / "uploaded-protocol.py").read_bytes(), PROTOCOL_PATH.read_bytes())
            with runner.controller_lock(root / "lock"):
                with self.assertRaisesRegex(RuntimeError, "另一个音乐启动器"):
                    with runner.controller_lock(root / "lock"):
                        self.fail("Second controller acquired the lock")


if __name__ == "__main__":
    unittest.main()
