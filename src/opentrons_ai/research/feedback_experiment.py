"""Compose, validate, record, and score the prospective feedback experiment.

Hardware execution requires --execute; default commands create offline artifacts.
Local runtime artifacts may contain transport identifiers and must not be published.
"""

import argparse
import datetime
import hashlib
import json
import math
import random
import signal
import subprocess
import time
import wave
from pathlib import Path

import numpy as np

from opentrons_ai.music_runner import RobotAPI, check_hardware, controller_lock, wait_idle
from opentrons_ai.research.feedback_pitch import estimate_pitch

INITIAL_K = 4.98375 * 1.08
LEFT, RIGHT, Y_MM = 161.5, 231.5, 178.75
CAP_MM_S = 110.0


def compose(stage, fitted_k=None):
    notes = [60, 64, 67] if stage == "calibration" else [62, 65, 69]
    mappings = [("initial", INITIAL_K)]
    if stage == "test":
        if fitted_k is None or not 4 <= fitted_k <= 6:
            raise ValueError("A reviewed fitted coefficient between 4 and 6 is required")
        mappings.append(("feedback", fitted_k))
    trials = [
        dict(midi=m, direction=d, repetition=r, arm=arm, k=k)
        for m in notes
        for d in (-1, 1)
        for r in (1, 2)
        for arm, k in mappings
    ]
    random.Random(20260915 if stage == "calibration" else 20260916).shuffle(trials)
    for trial in trials:
        trial["target_hz"] = 440 * 2 ** ((trial["midi"] - 69) / 12)
        trial["speed_mm_s"] = trial["target_hz"] / trial["k"]
        trial["start_x_mm"] = LEFT if trial["direction"] == 1 else RIGHT
        trial["end_x_mm"] = RIGHT if trial["direction"] == 1 else LEFT
        if not 0 < trial["speed_mm_s"] <= CAP_MM_S:
            raise ValueError("Speed exceeds the experiment cap")
    return trials


def protocol_source(trials):
    return (
        '''"""Frozen feedback experiment; no tips; fixed post-home Y/Z."""
import math
metadata = {"protocolName": "OT-2 prospective acoustic feedback validation"}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}
TRIALS = '''
        + repr(trials)
        + """

def run(protocol):
    from opentrons import types
    from opentrons.protocol_engine.commands import SavePositionParams
    pipette = protocol.load_instrument("p300_multi_gen2", "left")
    protocol.home()
    core = pipette._core
    def position():
        return core._engine_client.execute_command_without_recovery(
            SavePositionParams(pipetteId=core._pipette_id, failOnNotHomed=True),
            command_annotations=[]).position
    measured = position()
    z_mm = 200.0 if protocol.is_simulating() else measured.z
    if not math.isfinite(z_mm) or z_mm < 150:
        raise RuntimeError("Unexpected home height")
    def move(x, speed):
        if not 151.5 <= x <= 241.5 or not 0 < speed <= 110:
            raise RuntimeError("Outside motion bounds")
        pipette.move_to(types.Location(types.Point(x, 178.75, z_mm), None),
                        force_direct=True, speed=speed)
    for index, trial in enumerate(TRIALS):
        protocol.comment("POSITION")
        move(trial["start_x_mm"], 30.0)
        protocol.delay(seconds=0.9)
        protocol.comment("MEASURE %d" % index)
        move(trial["end_x_mm"], trial["speed_mm_s"])
        protocol.delay(seconds=0.6)
    final = position()
    if not protocol.is_simulating() and abs(final.z - z_mm) > 0.05:
        raise RuntimeError("Z changed")
"""
    )


def validate(commands, trials, simulated):
    allowed = {
        "loadPipette",
        "home",
        "savePosition",
        "comment",
        "waitForDuration",
        "moveToCoordinates",
    }
    if any(c["status"] != "succeeded" or c["commandType"] not in allowed for c in commands):
        raise ValueError("Unsuccessful or unexpected command")
    moves = [c["params"] for c in commands if c["commandType"] == "moveToCoordinates"]
    expected = [(t["start_x_mm"], 30.0) for t in trials]
    expected = [
        value
        for pair, t in zip(expected, trials, strict=True)
        for value in (pair, (t["end_x_mm"], t["speed_mm_s"]))
    ]
    if len(moves) != len(expected):
        raise ValueError("Movement count mismatch")
    zs = set()
    for move, (x, speed) in zip(moves, expected, strict=True):
        point = move["coordinates"]
        if not (
            move.get("forceDirect")
            and math.isclose(point["x"], x, abs_tol=1e-6)
            and 151.5 <= point["x"] <= 241.5
            and point["y"] == Y_MM
            and math.isfinite(point["z"])
            and point["z"] >= 150
            and 0 < move["speed"] <= CAP_MM_S
            and math.isclose(move["speed"], speed, abs_tol=1e-6)
        ):
            raise ValueError("Movement violates frozen plan")
        zs.add(point["z"])
    if len(zs) != 1 or (simulated and zs != {200.0}):
        raise ValueError("Z is not fixed")
    return next(iter(zs))


def execute(directory, trials):
    api = RobotAPI(directory)
    check_hardware(api)
    wait_idle(api, 20)
    uploaded = api.upload(directory / "protocol.py")
    protocol_id = uploaded["id"]
    analysis_id = uploaded["analysisSummaries"][-1]["id"]
    deadline = time.monotonic() + 180
    while True:
        result = api.request(f"/protocols/{protocol_id}/analyses/{analysis_id}")["data"]
        if result["status"] == "completed":
            break
        if time.monotonic() > deadline:
            raise RuntimeError("Analysis timeout; no physical execution started")
        time.sleep(2)
    if result.get("result") != "ok" or result.get("errors"):
        raise RuntimeError("Robot simulation failed")
    validate(result["commands"], trials, True)
    (directory / "simulation.json").write_text(json.dumps(result))
    print("Simulation and frozen trajectory validation passed", flush=True)
    check_hardware(api)
    finished = wait_idle(api, 20)
    for run in finished:
        state = api.request(f"/runs/{run['id']}")["data"]
        if state["status"] not in {"succeeded", "failed", "stopped"}:
            raise RuntimeError("Robot became busy")
        api.request(f"/runs/{run['id']}", "PATCH", {"data": {"current": False}})
    created = api.request("/runs", "POST", {"data": {"protocolId": protocol_id}})["data"]
    run_id = created["id"]
    (directory / "run-id.txt").write_text(run_id)

    def clock_sample():
        start = time.time()
        remote = api.request("/system/time")["data"]["systemTime"]
        stop = time.time()
        epoch = datetime.datetime.fromisoformat(remote.replace("Z", "+00:00")).timestamp()
        return {"rtt_s": stop - start, "host_minus_robot_s": (start + stop) / 2 - epoch}

    timing = {"clock_before": [clock_sample() for _ in range(3)]}
    wav = directory / "recording.wav"
    recorder = subprocess.Popen(
        [
            "pw-record",
            "--rate",
            "48000",
            "--channels",
            "1",
            "--format",
            "s16",
            "--latency",
            "20ms",
            str(wav),
        ]
    )
    try:
        time.sleep(2)
        if recorder.poll() is not None or not wav.exists() or wav.stat().st_size < 16000:
            raise RuntimeError("Recording did not start; play was not sent")
        api.request(f"/runs/{run_id}/actions", "POST", {"data": {"actionType": "play"}})
        print("Recording and physical experiment started", flush=True)
        deadline = time.monotonic() + 480
        report = 0
        while True:
            state = api.request(f"/runs/{run_id}")["data"]
            (directory / "run-state.json").write_text(json.dumps(state))
            if time.monotonic() - report > 20:
                print("Experiment state:", state["status"], flush=True)
                report = time.monotonic()
            if state["status"] in {"succeeded", "failed", "stopped"}:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("Monitoring timeout; inspect known run before any replay")
            time.sleep(1)
        commands = api.request(f"/runs/{run_id}/commands?pageLength=1000")
        (directory / "commands.json").write_text(json.dumps(commands))
        if len(commands["data"]) != commands["meta"]["totalLength"]:
            raise RuntimeError("Incomplete command log")
        if state["status"] != "succeeded" or state.get("errors"):
            raise RuntimeError("Physical run did not succeed")
        z_mm = validate(commands["data"], trials, False)
        timing["clock_after"] = [clock_sample() for _ in range(3)]
        print(f"Physical run succeeded; all moves validated; fixed Z={z_mm:.2f} mm", flush=True)
        time.sleep(2)
    finally:
        timing["record_stop_signal_host"] = time.time()
        recorder.send_signal(signal.SIGINT)
        recorder.wait(timeout=10)
        with wave.open(str(wav)) as stream:
            timing["audio_duration_s"] = stream.getnframes() / stream.getframerate()
        timing["audio_start_host_estimate"] = (
            timing["record_stop_signal_host"] - timing["audio_duration_s"]
        )
        timing["audio_alignment_uncertainty_s"] = 0.15
        (directory / "timing.json").write_text(json.dumps(timing, indent=2))


def analyze(directory):
    trials = json.loads((directory / "trials.json").read_text())
    timing = json.loads((directory / "timing.json").read_text())
    samples = timing["clock_before"] + timing["clock_after"]
    offset = min(samples, key=lambda row: row["rtt_s"])["host_minus_robot_s"]
    with wave.open(str(directory / "recording.wav")) as stream:
        rate = stream.getframerate()
        audio = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2") / 32768.0
    commands = json.loads((directory / "commands.json").read_text())["data"]
    label = ""
    rows = []
    for command in commands:
        if command["commandType"] == "comment":
            label = command["params"]["message"]
        if command["commandType"] != "moveToCoordinates" or not label.startswith("MEASURE "):
            continue
        index = int(label.split()[1])
        times = [
            datetime.datetime.fromisoformat(command[key].replace("Z", "+00:00")).timestamp()
            + offset
            - timing["audio_start_host_estimate"]
            for key in ("startedAt", "completedAt")
        ]
        middle = sum(times) / 2
        window = audio[round((middle - 0.2) * rate) : round((middle + 0.2) * rate)]
        result = estimate_pitch(window, rate)
        trial = trials[index]
        row = dict(
            index=index,
            **trial,
            **result,
            command_duration_s=times[1] - times[0],
            window_start_s=middle - 0.2,
            window_end_s=middle + 0.2,
            rms_dbfs=float(20 * np.log10(np.sqrt(np.mean(window**2)) + 1e-15)),
        )
        if result["status"] == "accepted":
            row["error_cents"] = float(1200 * np.log2(result["frequency_hz"] / trial["target_hz"]))
            row["measured_k"] = result["frequency_hz"] / trial["speed_mm_s"]
        row["within_25_cents"] = abs(row.get("error_cents", float("inf"))) <= 25
        rows.append(row)
    if len(rows) != len(trials):
        raise ValueError("Missing measurement commands")
    result = {
        "rows": rows,
        "audio_sha256": hashlib.sha256((directory / "recording.wav").read_bytes()).hexdigest(),
    }
    for arm in sorted({r["arm"] for r in rows}):
        subset = [r for r in rows if r["arm"] == arm]
        errors = [abs(r["error_cents"]) for r in subset if r["status"] == "accepted"]
        result[arm] = {
            "total": len(subset),
            "accepted": len(errors),
            "within_25_cents": sum(r["within_25_cents"] for r in subset),
            "median_absolute_cents": float(np.median(errors)) if errors else None,
        }
    if {r["midi"] for r in rows} == {60, 64, 67}:
        accepted = [r for r in rows if r["status"] == "accepted"]
        valid = all(sum(r["midi"] == m for r in accepted) >= 2 for m in (60, 64, 67))
        valid = valid and {r["direction"] for r in accepted} == {-1, 1}
        result["fit_status"] = "accepted" if valid else "insufficient_evidence"
        if valid:
            result["fitted_k"] = float(np.median([r["measured_k"] for r in accepted]))
    (directory / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["calibration", "test", "analyze"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--fitted-k", type=float)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.stage == "analyze":
        analyze(args.directory)
        return
    trials = compose(args.stage, args.fitted_k)
    args.directory.mkdir(parents=True, exist_ok=False)
    (args.directory / "trials.json").write_text(json.dumps(trials, indent=2))
    (args.directory / "protocol.py").write_text(protocol_source(trials))
    root = Path(__file__).resolve().parents[3]
    frozen = [
        root / "docs/research/feedback-experiment-plan.md",
        Path(__file__),
        Path(__file__).with_name("feedback_pitch.py"),
    ]
    (args.directory / "frozen-sources.json").write_text(
        json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}, indent=2)
    )
    for path in frozen:
        (args.directory / ("frozen-" + path.name)).write_bytes(path.read_bytes())
    print(f"Prepared {len(trials)} strokes; speed cap {CAP_MM_S:g} mm/s", flush=True)
    if args.execute:
        with controller_lock(root / "runs/music/.controller.lock"):
            execute(args.directory, trials)
        analyze(args.directory)


if __name__ == "__main__":
    main()
