# Happy Birthday: precomposed phrase motion

The current script has been upgraded to full-score phrase planning. See
[the current arrangements and Python commands](ot2-music-full-arrangements.md)
for the revised structure, boundaries, and validation.

## Historical version before the full-arrangement update

The remainder of this page records the earlier source and its results.
The current protocol file differs; old protocol/run IDs refer to that earlier
version. Exact uploaded copies remain in their recorded run directories.

Run the complete classic melody once:

```bash
cd /path/to/opentrons-ai
python3 protocols/ot2_happy_birthday.py
```

The [script](../protocols/ot2_happy_birthday.py) composes the entire score and
path before homing. The host uploads the complete file once, analyzes it,
and starts one run; it does not send individual note movements over HTTP.
`--dry-run` checks composition locally; `--simulate-only` uploads and checks
robot-side analysis without motion. The shared launcher waits for existing
runs, checks the robot configuration, and never automatically retries `play`.
No microphone or host Opentrons SDK is required.

## Phrase planning

The accepted working interval is X=146.5–246.5 mm, with Y=178.75 mm. The user
confirmed a 5 mm inset within this 100 mm interval, so allowable music X is
151.5–241.5 mm. This is a margin to the chosen software interval, not a
measurement of distance from the whole pipette body to mechanical stops.
The current arrangement actually retains at least 6.071 mm from either
original X boundary.

Each note has a frequency, speed, nominal duration, sounding duration,
articulation rest, and displacement. Phrase length is the sum of each note's
`speed_mm_s * tone_s`. The planner considers whole-phrase directions and
minimizes reversals, then occupied span. It translates the complete path to
center its extrema in the working interval. Every note endpoint is checked.
If a phrase or the complete route cannot fit, composition fails before any
movement; it never reverses in the middle of a phrase to conceal the problem.

| Phrase | Direction | Start X (mm) | End X (mm) | Travel (mm) |
| --- | --- | ---: | ---: | ---: |
| 1 | → | 152.571 | 194.061 | 41.490 |
| 2 | → | 194.061 | 237.417 | 43.356 |
| 3 | ← | 237.417 | 187.082 | 50.335 |
| 4 | → | 187.082 | 240.429 | 53.347 |

There are exactly two direction changes in the melody, both at phrase
boundaries. The approach goes directly to the precomputed starting position.
The melody does not automatically return to center afterward.

The C-major melody was checked against the
[Music All the Time lead sheet](https://www.musicallthetime.com/happy-birthday-sheet-music.html).
This motor arrangement uses the classic dotted pickup, 25 notes in four
six-beat phrases, G1–G2, quarter=96. Nominal duration is 15 seconds. It retains
the accepted calibration of 4.98375 Hz/(mm/s), with note speeds 9.832–19.664
mm/s and a 30 mm/s approach. A 40 ms articulation after repeated pickup notes
and an 80 ms phrase-end breath are deducted from sounding duration so they
do not extend the nominal beat. Actual acceleration and command overhead
still extend elapsed time.

## Precomposition versus continuous buffering

The score and coordinates are fully precomputed, and the complete protocol
runs locally on the robot. Per-note comment commands have been removed; only
phrase markers are logged during the melody. Each note still uses a separate
robot-side `move_to` call.

The official OT-2
[Smoothie driver source](https://github.com/Opentrons/opentrons/blob/edge/api/src/opentrons/drivers/smoothie_drivers/driver_3_0.py)
implements ordinary movement through `_send_command`, which waits for
completion with `M400`. This upstream source inspection explains why an
uploaded score or a Python list alone does not create a continuous buffered
trajectory. It is not an inspection of the installed robot's exact source.
This implementation reduces reversals and comment overhead, but does not
claim uninterrupted velocity through notes or sample-accurate rhythm.
Raw serial streaming, firmware changes, and bypassing the position model
have not been implemented or tested.

## Validation and records

Eleven tests passed across the birthday planner and existing Jingle Bells
launcher. These cover fixed Z, phrase-only reversals, 5 mm margins, complete
score, tempo-dependent replanning, infeasible travel, the noncentral approach,
and existing upload/wait/error behavior. Ruff on changed Python files and
`git diff --check` passed.

The physical test uses the same Python entry point above, with an automatic
robot-side simulation before execution. The simulation checked all 26 direct
moves against the composed path, with Z=200 mm, and returned `ok`, no errors.

- Local artifacts: `runs/music/happy-birthday-20260914-182536-708fa4/`

Observed result on 2026-09-14: `succeeded`, all 48 commands successful, no run
errors. The melody lasted 17.49 seconds. The actual command log confirms two
melody reversals and endpoints X=152.571–240.429 mm, with a minimum margin of
6.071 mm. Initial and final position reads both reported Z=189.27000 mm;
all commanded moves used Z=189.27 mm. These are controller-reported results;
this test did not record audio or independently measure acoustic smoothness.

`composition.json` stores all note/path data before upload. The directory also
contains the exact uploaded protocol, its hash, analysis, HTTP intent/response
records, run state, and command log. Z on hardware is read after homing and
held constant; no tips, labware, aspiration, or dispensing are used.
