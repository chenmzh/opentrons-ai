# Jingle Bells from Python

The current script has been upgraded to full-score phrase planning. See
[the current arrangements and Python commands](ot2-music-full-arrangements.md)
for the revised structure, boundaries, and validation.

## Historical version before the full-arrangement update

The remainder of this page records the earlier source and its results.
The current protocol file differs; old protocol/run IDs refer to that earlier
version. Exact uploaded copies remain in their recorded run directories.

From this Linux host, run:

```bash
cd /path/to/opentrons-ai
python3 protocols/ot2_jingle_bells.py
```

The [script](../protocols/ot2_jingle_bells.py) is both the Python entry point
and an uploadable OT-2 protocol. The entry point uses the repository's standard
library [host transport](../src/opentrons_ai/music_runner.py); keep it in this
repository. No host Opentrons SDK, virtual environment, microphone, or protocol
ID arguments are required. Set `OT2_URL` and `OT2_EXPECTED_NAME` locally before connecting.

Default execution uploads the current file, waits for successful robot-side
analysis, checks the simulated moves against the local melody, and then homes
and plays the robot. Maintain the confirmed configuration: left
`p300_multi_gen2`, right mount empty, no tips, and the same unobstructed travel
area. The calibrated robot identity and firmware 26.6.0 are checked each time.
After homing, all music travel uses the actual saved Z position.

If another run is active, the script polls without pausing or stopping it.
It waits before uploading and checks again before creating its own run.
The default wait limit is 15 minutes; an idle or paused run also blocks new
execution until the operator finishes it. A local file lock prevents two
instances of this launcher running together. Other controllers should not
start a new run during playback.

Optional checks:

```bash
# Offline note and motion preflight; no robot connection.
python3 protocols/ot2_jingle_bells.py --dry-run

# Upload and simulate on the robot, without physical motion.
python3 protocols/ot2_jingle_bells.py --simulate-only

# Exit immediately if a previous run has not finished.
python3 protocols/ot2_jingle_bells.py --wait-timeout 0
```

Every invocation saves the exact uploaded source, its SHA-256, simulation,
HTTP intentions/responses, run ID, final state, and successful command log in
a new `runs/music/jingle-bells-<timestamp>-<suffix>/` directory. This directory
is ignored by Git. The launcher does not record audio.

Requests that change robot state are never automatically retried. If a network
error, monitoring timeout, or Ctrl+C interrupts the launcher after creating a
run, its exit does not stop the robot. Inspect the printed run ID in the app or
through `GET /runs/<run-id>` before starting again. The saved request intentions
also help recover an ambiguous run-creation response.

## Arrangement and validation

The arrangement contains the complete verse followed by the complete chorus:
32 bars, 99 notes, in C major, ending on C2. The public-domain melody by James
Lord Pierpont was checked against
[the mfiles melody sheet](https://www.mfiles.co.uk/scores/jingle-bells-main.pdf).
Its 2/4 note values are doubled to express the same proportions in 4/4 here.
The motor arrangement uses quarter=132 and does not repeat the verse/chorus.

The nominal note duration totals 58.18 seconds. Firmware acceleration and
command overhead add time, as do homing and approach. Relative pitches retain
the earlier measured factor of 4.98375 Hz/(mm/s). Motor harmonics remain audible;
this run does not independently recalibrate each note.

- Register: G1–A2; note speeds 9.832–22.072 mm/s; approach speed 30 mm/s.
- Planned note endpoints: X=168.698–224.818 mm, Y=178.75 mm.
- Runtime bounds: X=146.5–246.5 mm, speed <=30 mm/s, post-home Z >=150 mm.
- No labware definitions, tip pickup, aspiration, or dispensing.
- Robot simulation checks all 100 direct moves, at simulated Z=200 mm.
- Seven offline tests cover the full score, bounded travel, actual-Z handling,
  rejection of altered/unsafe simulated commands, waiting for prior runs,
  failed analysis, ambiguous request handling, and exclusive controller locking.

Test command:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p test_jingle_bells.py -v
```

The first physical test used the same plain Python command shown above, after
the preceding Song of Storms run had ended.
Artifacts: `runs/music/jingle-bells-20260914-181328-6b4c95/`.

Observed result on 2026-09-14: `succeeded`, no run errors, all 209 commands
successful. The music itself lasted 68.93 seconds; the whole run including
homing and cleanup lasted 127.76 seconds. Initial and final saved height
readings were both Z=189.27000 mm, and all 100 direct moves used Z=189.27 mm.
The preceding run was already `succeeded`
at this launcher's first state check. Seven offline tests, Ruff on the new
files, and `git diff --check` passed.
