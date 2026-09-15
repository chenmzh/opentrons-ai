"""OT-2 motor music: verify three notes, then the six-note Song of Storms motif.

Calibration applies to the tested OT-2, left p300_multi_gen2, no tips,
software 26.6.0. The selected X-axis spectral branch is not a pure tone.
"""

import math

from opentrons import protocol_api, types
from opentrons.protocol_engine.commands import SavePositionParams

metadata = {
    "protocolName": "OT-2 Song of Storms motif and pitch verification",
    "description": "Verify D4/F4/D5, then play D4 F4 D5 twice using X motion at fixed Z.",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}

CENTER_X_MM = 196.5
CENTER_Y_MM = 178.75
# Initial measured X-axis branch: approximately 79.74 Hz per mm/s.
HZ_PER_MM_S = 79.74
NOTES = (("D4", 62), ("F4", 65), ("D5", 74))


def frequency_hz(midi_note):
    return 440.0 * 2.0 ** ((midi_note - 69) / 12.0)


def note_events():
    """Long verification strokes followed by the short musical motif."""
    for name, midi in NOTES:
        for direction in (1, -1):
            yield "VERIFY", name, midi, 1.5, direction, 0.75
    for repetition in range(2):
        for index, (name, midi) in enumerate(NOTES):
            duration_s = 0.375 if index < 2 else 1.5
            direction = 1 if (repetition * 3 + index) % 2 == 0 else -1
            yield "MELODY", name, midi, duration_s, direction, 0.0


def run(protocol: protocol_api.ProtocolContext):
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
    if not math.isfinite(z_mm) or z_mm < 150.0:
        raise RuntimeError(f"Unexpected home height: {z_mm} mm")

    def move(x_mm, speed_mm_s):
        if not (146.5 <= x_mm <= 246.5 and 0 < speed_mm_s <= 30):
            raise RuntimeError("Music motion exceeds the tested region or speed")
        pipette.move_to(
            types.Location(types.Point(x_mm, CENTER_Y_MM, z_mm), None),
            force_direct=True,
            speed=speed_mm_s,
        )

    x_mm = CENTER_X_MM
    move(x_mm, 30.0)
    protocol.comment(f"MUSIC_BASELINE Z={z_mm:.5f} mm")
    protocol.delay(seconds=5)
    previous_phase = None
    for phase, name, midi, duration_s, direction, gap_s in note_events():
        if phase == "MELODY" and previous_phase != "MELODY":
            protocol.comment("SONG_OF_STORMS_MOTIF_BEGIN")
            protocol.delay(seconds=3)
        hz = frequency_hz(midi)
        speed_mm_s = hz / HZ_PER_MM_S
        x_mm += direction * speed_mm_s * duration_s
        protocol.comment(
            f"{phase} note={name} target_hz={hz:.6f} "
            f"direction={direction} speed_mm_s={speed_mm_s:.6f}"
        )
        move(x_mm, speed_mm_s)
        if gap_s:
            protocol.delay(seconds=gap_s)
        previous_phase = phase
    final = position()
    if not protocol.is_simulating() and abs(final.z - z_mm) > 0.05:
        raise RuntimeError("Z changed during music test")
    protocol.comment(f"MUSIC_COMPLETE Z={final.z:.5f} mm")
