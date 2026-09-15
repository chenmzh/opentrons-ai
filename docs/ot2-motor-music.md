# Motor music: calibration and playback

For the current full versions of all three songs, see
[complete motor music arrangements](ot2-music-full-arrangements.md).
Their whole scores/paths are precomposed, with reversals at phrase boundaries
and at least 5 mm inset in the 100 mm range.

For the second song, see [Jingle Bells from Python](ot2-jingle-bells.md):
`python3 protocols/ot2_jingle_bells.py` uploads, simulates, waits for the robot
to be free, and plays the verse and chorus without requiring a microphone.

Status on 2026-09-14: **microphone capture restored; speed sweeps, two
six-note trials, and the complete Song of Storms melody completed**.
The [complete performance report](ot2-song-of-storms-full.md) links the
86-note script and 50.77-second recording. See the
[measured results and listening clips](ot2-pitch-calibration-results.md).
The user authorized microphone capture, X/Y motor pitch calibration, and a
Song of Storms trial. The no-tip, high-Z configuration follows the earlier
circle test. Pitch is estimated from measured spectral components; motor
harmonics and background noise prevent treating this as a pure-tone instrument.

## Audio diagnosis

Host: Dell Precision 3460, Linux. Initial sandbox and host-level checks found
no capture hardware; this section records that diagnosis before recovery.
PipeWire and ALSA recording tools are installed. The `snd_hda_intel` driver
is loaded, but `lspci` and `/proc/asound/cards` show only NVIDIA HDMI/DP audio.
`arecord -l` lists no capture hardware; PipeWire lists no audio sources.
USB enumeration shows no USB audio device. The operator says the headset is
connected directly to the Linux host. Kernel journal access was unavailable.

An integrated audio controller disabled in firmware is a plausible cause,
not a confirmed diagnosis. Dell documents the BIOS option
**Integrated Devices → Audio → Enable Audio** in the
[Precision 3460 service manual](https://www.dell.com/support/manuals/en-us/precision-3460-workstation/prec_3460_sff_sm/system-setup-options?guid=guid-3f577fdd-5e02-4303-b34c-ea88677be495&lang=en-us).
No BIOS changes, reboots, system package installation, or driver reloads were
performed by the agent. After the operator's reboot/configuration change,
ALC3246 Analog appeared as capture card 1, and PipeWire exposed an input source.
An initial recording clipped, so microphone boost was disabled and gain was
adjusted. Final verification recordings used PipeWire input volume 0.35;
steady analysis windows were free of clipping. Startup transients were excluded.

## Prepared calibration

[ot2_pitch_calibration.py](../protocols/ot2_pitch_calibration.py) homes, reads
the actual left-pipette Z, and centers at (196.5, 178.75) mm. Each of X and Y
gets outward and return strokes at 2, 3, 4, 6, 8, 12, 16, and 24 mm/s. The
nominal constant-speed stroke duration is 1.5 seconds, with 0.75-second gaps.
Each stroke is <=36 mm; all XY points lie inside the earlier circle test's
bounding box. Command comments identify axis, speed, direction, and tone ID.

Robot-side analysis completed with `result: ok`, no errors, and 33 direct
movement commands. All were checked for fixed simulated Z=200 mm, speed
<=30 mm/s, and XY bounds. Physical Z will come from a home-position reading,
using the same verified internal read-only bridge as the circle test.
Simulation does not establish physical clearance or acoustic pitch.

Local upload and analysis records: `runs/music/` (ignored by Git).

## Analysis tools

An isolated environment at `runs/music/.venv` contains NumPy 2.2.6. Recreate it:

```bash
python3 -m venv runs/music/.venv
runs/music/.venv/bin/python -m pip install 'numpy==2.2.6'
```

The analysis module accepts a mono 16-bit PCM WAV and an explicit steady-tone
window. Example, after obtaining an actual recording at the given path:

```bash
PYTHONPATH=src runs/music/.venv/bin/python -m opentrons_ai.motor_pitch \
  runs/music/recording.wav --start-s 10 --duration-s 1
```

It reports up to five strong spectral components from 60–3000 Hz, their nearest
equal-tempered notes (A4=440 Hz), and cents errors. Positive cents means sharp;
negative means flat. Silence and substantial clipping are rejected. These
components are **not automatically labeled as the perceived fundamental**:
motor harmonics, fans, and room noise can dominate. For calibration, compare
against the quiet baseline, both movement directions, and multiple speeds;
exclude acceleration/deceleration and require a consistent frequency branch.
Keep command timestamps synchronized with recording timestamps before
attributing any peak to a given speed. Robot clock lag must be accounted for.

Four synthetic-signal tests passed, including known frequencies, cents,
strong harmonics, silence, and clipping. Run them with:

```bash
PYTHONPATH=src runs/music/.venv/bin/python -m unittest discover \
  -s tests -p test_motor_pitch.py -v
```

The measured speed-to-frequency map and separate note verification are in the
[results report](ot2-pitch-calibration-results.md), including commanded speeds,
measured Hz, cents errors, harmonic ambiguity, and run identifiers.
The opening D4, F4, D5 targets are 293.665, 349.228, 587.330 Hz; these are
theoretical reference frequencies, **not measurements from this robot**.

Prior art: [midi2gcode](https://github.com/nescio007/midi2gcode) and
[Musical Marlin](https://github.com/Toglefritz/Musical_Marlin). Their printer
calibration constants and firmware commands have not been applied to the OT-2.

The subsequent [range and rhythm measurements](ot2-music-limits.md) cover
0.125–400 mm/s X-axis tests, recorded note separation, short high-note plateaus,
and the distinction between command throughput and usable musical tempo.
