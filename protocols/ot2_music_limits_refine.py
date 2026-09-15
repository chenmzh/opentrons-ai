"""Refine musical-note range and short-note thresholds after the initial sweep.

Official gantry default/ceiling used here: 400 mm/s; no acceleration, current,
steps/mm, firmware, or axis-limit changes. Reference:
https://docs.opentrons.com/python-api/robot-position/#gantry-speed
No tips/liquids. Every post-home move preserves actual Z and remains within
X=151.5–241.5, Y=178.75 mm. External microphone recording is required for analysis.
"""

import math

metadata = {
    "protocolName": "OT-2 musical range and rhythm threshold refinement",
    "description": "Pitch targets C1 through B6, low-speed probes, and 80–125 ms notes; default acceleration.",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}
TARGET_MIDI = (24, 36, 48, 60, 72, 84, 88, 91, 93, 95)
SPEEDS_MM_S = (.125, .25, .5) + tuple(
    440.0 * 2.0 ** ((m - 69) / 12.0) / 4.98375 for m in TARGET_MIDI
)
NOTE_PERIODS_S = (1.0, .5, .125, .1, .08)
MIDI_PATTERN = (38, 41, 50, 41)
HZ_PER_MM_S = 4.98375


def test_blocks():
    blocks = []
    for speed in SPEEDS_MM_S:
        distance = min(80.0, speed * (3.0 if speed <= .5 else 1.5))
        # Both directions; extra repetitions at high speeds with short plateaus.
        repetitions = 4 if speed >= 64 else 2
        notes = [dict(x_mm=156.5 + (distance if i % 2 == 0 else 0),
                      speed_mm_s=float(speed), duration_s=distance / speed,
                      direction=1 if i % 2 == 0 else -1, gap_s=.5)
                 for i in range(repetitions)]
        blocks.append(dict(kind="RANGE", value=float(speed), start_x_mm=156.5, notes=notes))
    for period in NOTE_PERIODS_S:
        speeds = [440.0 * 2.0 ** ((m - 69) / 12.0) / HZ_PER_MM_S for m in MIDI_PATTERN]
        distance = sum(speeds) * period
        start = 196.5 - distance / 2
        x_mm = start
        notes = []
        for i in range(16):
            direction = 1 if (i // 4) % 2 == 0 else -1
            speed = speeds[i % 4]
            x_mm += direction * speed * period
            notes.append(dict(x_mm=x_mm, speed_mm_s=speed, duration_s=period,
                              midi=MIDI_PATTERN[i % 4], direction=direction, gap_s=0))
        blocks.append(dict(kind="RHYTHM", value=period, start_x_mm=start, notes=notes))
    for block in blocks:
        if not 151.5 <= block["start_x_mm"] <= 241.5:
            raise ValueError("Test approach exceeds the 5 mm inset")
        for note in block["notes"]:
            if not (151.5 <= note["x_mm"] <= 241.5
                    and 0 < note["speed_mm_s"] <= 400 and note["duration_s"] > 0):
                raise ValueError("Test note exceeds authorized coordinates or official speed")
    return blocks


def run(protocol):
    from opentrons import types
    from opentrons.protocol_engine.commands import SavePositionParams

    blocks = test_blocks()
    pipette = protocol.load_instrument("p300_multi_gen2", "left")
    protocol.home()
    core = pipette._core

    def position():
        return core._engine_client.execute_command_without_recovery(
            SavePositionParams(pipetteId=core._pipette_id, failOnNotHomed=True),
            command_annotations=[],
        ).position

    home = position()
    z_mm = 200.0 if protocol.is_simulating() else home.z
    if not math.isfinite(z_mm) or z_mm < 150:
        raise RuntimeError(f"Unexpected home Z: {z_mm}")

    def move(x_mm, speed):
        if not 151.5 <= x_mm <= 241.5 or not 0 < speed <= 400:
            raise RuntimeError("Motion exceeds the authorized test envelope")
        pipette.move_to(types.Location(types.Point(x_mm, 178.75, z_mm), None),
                        force_direct=True, speed=speed)

    protocol.comment(f"LIMITS_BASELINE Z={z_mm:.5f} mm")
    for index, block in enumerate(blocks):
        move(block["start_x_mm"], 30.0)
        protocol.delay(seconds=2)
        protocol.comment(f"BLOCK_BEGIN index={index} kind={block['kind']} value={block['value']}")
        for note in block["notes"]:
            move(note["x_mm"], note["speed_mm_s"])
            if note["gap_s"]:
                protocol.delay(seconds=note["gap_s"])
        protocol.comment(f"BLOCK_END index={index}")
    final = position()
    if not protocol.is_simulating() and (
            not math.isfinite(final.z) or abs(final.z - z_mm) > .05):
        raise RuntimeError("Z changed during music measurement")
    protocol.comment(f"LIMITS_COMPLETE Z={final.z:.5f} mm")
