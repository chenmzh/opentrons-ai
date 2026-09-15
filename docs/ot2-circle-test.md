# OT-2 100 mm circle motion test

[Protocol](../protocols/ot2_circle_100mm.py), physically executed on 2026-09-14
on the tested OT-2, robot software 26.6.0, with the left p300_multi_gen2.
The saved file is byte-for-byte identical to the successful uploaded protocol.

This is a no-tip motion test, authorized directly by the operator. It does not
load labware or perform liquid handling. It does not implement the planned
experiment automation application.

## Motion

- Home, move to XY (196.5, 178.75) mm, then move to the circle's rightmost point.
- Draw one counterclockwise circle of radius 50 mm, viewed from above.
- Request 30 mm/s for each move. The 180 straight segments approximate the
  circle with less than 0.008 mm radial deviation; acceleration and command
  overhead make the effective speed lower than the requested travel speed.
- Read the left pipette's home Z and use that same coordinate for all 182
  direct moves, including the center and perimeter approach. No additional
  home is requested by the script after the circle.

The XY reference is the left pipette's critical point, not the midpoint of all
eight nozzles. The center is derived from the standard deck's 393 by 357.5 mm
slot rectangle. See the [official deck definition](https://github.com/Opentrons/opentrons/blob/v8.8.2/shared-data/deck/definitions/3/ot2_standard.json)
and [direct-movement documentation](https://docs.opentrons.com/python-api/robot-position/).

The read-only `savePosition` bridge uses internal engine interfaces because
the OT-2 public Python API has no current-position getter. Compatibility was
verified on software 26.6.0; rerun analysis after software changes. Analysis
returns a placeholder position of (0, 0, 0), so the simulation uses Z=200 mm
to inspect geometry. Physical execution instead reads the actual homed Z and
rejects nonfinite heights or heights below 150 mm before moving in XY. It
checks the final reported Z against the initial Z with a 0.05 mm tolerance.
Simulation does not measure physical clearance or positioning accuracy.

## Verification and local records

Robot-side analysis completed with `result: ok`, no errors. The physical run completed with `status: succeeded`,
no errors, and all 189 commands succeeded. The command list contains 182
direct moves at 30 mm/s, all at Z=189.27 mm. Position reads before and after
the circle both reported Z=189.27 mm. The engine inserts an initial home,
in addition to the script's explicit home. Reported run duration was about
89 seconds, including homing and positioning.

Analysis, run status, and command records are in the ignored local directory
`runs/circle-test/`. Robot timestamps lagged the host date; do not treat them
as host UTC. Verification uses controller responses, not camera images.

## Reuse

No host SDK installation is required to import the Python file into the
Opentrons App. Connect to the robot, import the protocol, let analysis finish,
and start a new run through the App for another authorized no-tip test.
Each invocation performs one circle. The tested hardware is the left
`p300_multi_gen2`; ensure the high-level travel region is clear before reuse.

For robot-side simulation without starting motion, upload the file:

```bash
: "${OT2_URL:?Set OT2_URL locally before connecting}"
curl --noproxy '*' --fail-with-body --silent --show-error --max-time 30 \
  -H 'Opentrons-Version: 2' \
  -F 'files=@protocols/ot2_circle_100mm.py' \
  "$OT2_URL/protocols"
```

Use the returned protocol ID and analysis summary ID to read
`GET /protocols/{protocolId}/analyses/{analysisId}` with the same version
header; wait for `status: completed`, `result: ok`, and no errors before
execution. Uploading alone does not move the robot. When controlling via
HTTP, create a fresh run with the analyzed protocol ID, persist its run ID,
then issue `play` once and monitor that run. After an ambiguous response,
inspect run state rather than issuing `play` again.

Offline regression tests need only Python 3:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```
