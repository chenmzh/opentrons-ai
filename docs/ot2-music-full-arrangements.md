# Complete motor music arrangements

All three current scripts precompose the entire score, articulation, starting
position, and path before homing. They use the accepted X-axis pitch calibration,
preserve post-home Z, and retain at least 5 mm within the previously tested
100 mm interval. Reversals occur only at the declared musical phrase edges.

Set `OT2_URL` and `OT2_EXPECTED_NAME` in your local environment (see
[configuration](../README.md#local-robot-configuration)). Dry runs need no robot configuration.

Run one chosen song from the repository root:

```bash
cd /path/to/opentrons-ai

python3 protocols/ot2_happy_birthday.py
python3 protocols/ot2_song_of_storms_full.py
python3 protocols/ot2_jingle_bells.py
```

Each command uploads its current script, simulates, waits for robot availability,
and plays once. The three commands above are separate choices; running all three
in a shell executes the songs sequentially. No protocol IDs, host Opentrons SDK,
or microphone are needed. Keep the confirmed left `p300_multi_gen2`, empty right
mount, no-tip configuration and unobstructed motion area.

Append `--dry-run` to check locally without connecting to the robot, or
`--simulate-only` for robot-side analysis without physical movement.

## Arrangements

| Song | Structure | Notes | Planned musical duration | Reversals |
| --- | ---: | ---: | ---: |
| Happy Birthday | Intro, complete theme, interlude, theme twice more, final cadence | 91 | 56.25 s | 12 |
| Song of Storms | Complete 15-bar lead melody twice | 86 | 40.91 s | 13 |
| Jingle Bells | Complete verse followed by complete chorus | 99 | 58.18 s | 15 |

The original 25-note birthday trial already contained the complete traditional
tune. This expanded performance adds an original motor arrangement around
three intact passes through that tune. Its register and quarter=96 tempo are
retained. The two other songs keep their previous pitches, beat values, tempo
(quarter=132), and repetition structure.

For Song of Storms and Jingle Bells, two-bar musical subphrases are the permitted
turning units; Song of Storms also has its final single-bar cadence in each pass.
The longer phrases of the complete songs would not all fit in the available
travel. These boundaries are chosen before execution, not inserted mid-note
when an edge is reached.

| Song | X endpoints including approach (mm) | Minimum inset from 146.5/246.5 (mm) | Note speed (mm/s) |
| --- | ---: | ---: |
| Happy Birthday | 151.943–241.057 | 5.443 | 9.832–19.664 |
| Song of Storms | 152.384–240.616 | 5.884 | 14.731–35.037 |
| Jingle Bells | 160.757–232.243 | 14.257 | 9.832–22.072 |

Y stays at 178.75 mm. Approach speed is 30 mm/s; the birthday and Jingle Bells
scripts cap speed at 30 mm/s, while Song of Storms retains its tested 36 mm/s
cap for the high notes. The host validator checks the song-specific speed cap,
all note coordinates, and X=151.5–241.5 mm before execution. The 5 mm margin is
to this chosen working rectangle, not a measurement to the robot's hard stops.

## Composition and playback

The planner computes each phrase's total displacement, searches its possible
directions, minimizes reversals and then occupied span, and centers the entire
path envelope. It checks every note endpoint and rejects an infeasible score
before motion. Each script embeds the planner to remain independently uploadable
as an OT-2 protocol. No other module is required on the robot.

Only phrase comments are emitted during music. Repeated notes receive a 40 ms
articulation; phrase endings have an 80 ms breath. These gaps are deducted from
the note's sounding duration to preserve nominal beat length. Driver overhead
and acceleration still increase actual elapsed time. The accepted calibration
is 4.98375 Hz/(mm/s); these revisions do not recalibrate acoustic pitch.

Complete protocols are uploaded once and run locally on the robot. Execution
still uses separate robot-side `move_to` segments; this is the same mechanism
as the birthday trial the operator found fluent, rather than firmware-buffered
continuous motion. No raw serial streaming or firmware modification is used.

## Checks and records

Seventeen offline tests (plus three song subtests), Ruff on all changed Python
files, and `git diff --check` passed. Tests cover complete melodies, repeated
themes, phrase boundaries, direction counts, inset geometry, duration accounting,
fixed Z, invalid plans, song-specific speed caps, and existing transport behavior.
Direct comparison with the preceding saved protocol sources also confirmed
that all 86 Song of Storms and 99 Jingle Bells pitches and nominal beat durations
are unchanged.

Every invocation creates `runs/music/<song>-<timestamp>-<suffix>/`, containing
the full `composition.json`, exact uploaded source/hash, simulation, request
intentions/responses, run ID, final state, and command log. Older protocol IDs
still identify the older versions; use the Python entries above to upload the
updated source. The launcher never automatically resends a state-changing request.
Exiting its monitor does not stop the robot; inspect the known run before replaying.

The earlier single-pass birthday and per-note-direction versions are recorded
in the historical song reports. Their old success records should not be read
as validation of the revised source.

## Physical validation of these revisions — 2026-09-14

All three new scripts were simulated and then executed sequentially through
their Python entry points. Every run returned `succeeded` with no run errors;
every recorded command succeeded. All movement commands used Z=189.27 mm,
and each script's initial and final position reads reported Z=189.27000 mm.
Command logs confirmed the direction counts and margins listed above.

| Song | Successful commands | Music time |
| --- | ---: | ---: |
| Happy Birthday | 144 | 65.36 s |
| Song of Storms | 131 | 49.70 s |
| Jingle Bells | 176 | 68.40 s |

Run artifacts and `summary.json` are in:

- `runs/music/happy-birthday-20260914-183328-97349e/`
- `runs/music/song-of-storms-full-20260914-183619-ef4e6a/`
- `runs/music/jingle-bells-20260914-183847-9374a5/`

Music time excludes homing, approach, and cleanup. No audio was recorded in
these runs; acoustic smoothness and per-note pitch were not independently
remeasured. The runs validate completed movement and the reported positions.
