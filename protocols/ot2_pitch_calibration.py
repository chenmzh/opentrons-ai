"""Record X/Y speed sweeps with an external microphone; no tips or liquids."""

import math

from opentrons import protocol_api, types
from opentrons.protocol_engine.commands import SavePositionParams

metadata = {
    "protocolName": "OT-2 motor pitch calibration",
    "description": "X/Y sweeps at measured home Z; external microphone required.",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}

CENTER_X_MM = 196.5
CENTER_Y_MM = 178.75
SPEEDS_MM_S = (2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0)
TONE_DURATION_S = 1.5
GAP_S = 0.75


def calibration_moves():
    """Each speed gets an outward stroke and a return stroke at the same speed."""
    for axis in ("x", "y"):
        for speed_mm_s in SPEEDS_MM_S:
            distance_mm = speed_mm_s * TONE_DURATION_S
            for direction in (1, -1):
                x_mm, y_mm = CENTER_X_MM, CENTER_Y_MM
                if direction == 1:
                    if axis == "x":
                        x_mm += distance_mm
                    else:
                        y_mm += distance_mm
                yield axis, direction, speed_mm_s, x_mm, y_mm


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

    def move(x_mm, y_mm, speed_mm_s):
        if not (146.5 <= x_mm <= 246.5 and 128.75 <= y_mm <= 228.75):
            raise RuntimeError("Pitch calibration exceeds the tested XY region")
        if not (0 < speed_mm_s <= 30):
            raise RuntimeError("Invalid calibration speed")
        pipette.move_to(
            types.Location(types.Point(x_mm, y_mm, z_mm), None),
            force_direct=True,
            speed=speed_mm_s,
        )

    move(CENTER_X_MM, CENTER_Y_MM, 30.0)
    protocol.comment(f"CALIBRATION_BASELINE Z={z_mm:.5f} mm")
    protocol.delay(seconds=5)
    for index, (axis, direction, speed, x_mm, y_mm) in enumerate(calibration_moves()):
        protocol.comment(
            f"TONE {index:02d} axis={axis} direction={direction} speed_mm_s={speed}"
        )
        move(x_mm, y_mm, speed)
        protocol.comment(f"TONE_END {index:02d}")
        protocol.delay(seconds=GAP_S)
    final = position()
    if not protocol.is_simulating() and abs(final.z - z_mm) > 0.05:
        raise RuntimeError("Z changed during pitch calibration")
    protocol.comment(f"CALIBRATION_COMPLETE Z={final.z:.5f} mm")
