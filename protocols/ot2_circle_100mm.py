"""OT-2 no-tip motion test: home, center, and one XY circle.

XY coordinates refer to the left pipette's critical point, in deck millimeters.
After homing, every motion preserves the measured home Z coordinate.
"""

import math

from opentrons import protocol_api, types
from opentrons.protocol_engine.commands import SavePositionParams

metadata = {
    "protocolName": "OT-2 home and 100 mm XY circle",
    "author": "Opentrons AI workspace",
    "description": "No-tip motion test; 30 mm/s; one circle at homed Z.",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}

# Center of the standard 3-column, 4-row slot rectangle (393 x 357.5 mm).
CENTER_X_MM = 196.5
CENTER_Y_MM = 178.75
RADIUS_MM = 50.0
SPEED_MM_S = 30.0
SEGMENTS = 180


def xy_path():
    """Visit the center, move to the perimeter, then close one CCW circle."""
    yield {"x": CENTER_X_MM, "y": CENTER_Y_MM}
    for index in range(SEGMENTS + 1):
        angle_rad = 2.0 * math.pi * index / SEGMENTS
        yield {
            "x": CENTER_X_MM + RADIUS_MM * math.cos(angle_rad),
            "y": CENTER_Y_MM + RADIUS_MM * math.sin(angle_rad),
        }


def run(protocol: protocol_api.ProtocolContext):
    pipette = protocol.load_instrument("p300_multi_gen2", "left")
    protocol.home()
    # OT-2 has no public Protocol API getter for its current coordinates.
    # This read-only engine bridge is verified on robot software 26.6.0.
    core = pipette._core

    def read_position():
        return core._engine_client.execute_command_without_recovery(
            SavePositionParams(pipetteId=core._pipette_id, failOnNotHomed=True),
            command_annotations=[],
        ).position

    home_position = read_position()
    # Robot analysis returns (0, 0, 0) for savePosition, not a homed position.
    # Use a dry-run plane for geometry analysis; hardware uses its measured Z.
    z_mm = 200.0 if protocol.is_simulating() else home_position.z
    if not math.isfinite(z_mm) or z_mm < 150.0:
        raise RuntimeError(f"Unexpected home height: {z_mm} mm")
    protocol.comment(f"Home Z = {z_mm} mm. Move to center, then one 100 mm circle.")
    for axis_map in xy_path():
        pipette.move_to(
            types.Location(types.Point(axis_map["x"], axis_map["y"], z_mm), None),
            force_direct=True,
            speed=SPEED_MM_S,
        )
    final_position = read_position()
    if not protocol.is_simulating() and abs(final_position.z - z_mm) > 0.05:
        raise RuntimeError("Final Z differs from home Z")
    protocol.comment(f"Circle complete. Final Z = {final_position.z} mm.")
