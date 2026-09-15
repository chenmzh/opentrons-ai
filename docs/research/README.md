# OT-2 motor-music research report

Read the [Chinese research manuscript](ot2-motor-music-paper.zh.md) for the
question, methods, results, discussion, limitations and references. It is an
exploratory report on one robot, not a peer-reviewed publication. The English
title is provided for indexing; the full text is Chinese.

`data/evidence.json` is the reviewed numerical supplement, including per-note
command times, class predictions, qualified harmonic measurements, anonymized experiment labels,
and SHA-256 hashes of the local source records. It excludes microphone audio,
HTTP logs, credentials and local databases. Missing detections are empty lists,
not measurements at zero frequency. The supplement supports table and figure
reconstruction; independent acoustic reanalysis requires the original recordings,
which are retained locally and are not distributed with this repository.

## Rebuild figures and the printable article

From the repository root, with Python 3.12 or later:

```bash
python3 -m venv .venv-research
.venv-research/bin/python -m pip install -r requirements-research.txt
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.build_paper
```

The builder reconciles timing denominators and classification counts, then writes
SVG, PDF and PNG figures plus a self-contained HTML article to `build/research/`.
Open the HTML in a browser to read or print. Generated exports are ignored by Git.
For an automated article PDF after installing the frontend dependencies:

```bash
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install chromium
node frontend/scripts/export-paper.mjs \
  build/research/ot2-motor-music-paper.zh.html \
  build/research/ot2-motor-music-paper.zh.pdf
```

Install a Chinese font such as Noto Serif CJK for Chinese PDF rendering.
The manuscript remains readable directly on GitHub, with numerical tables and
figure captions; figures are embedded in the generated HTML/PDF.

## Reanalyse a local original recording

Each recording directory must contain `recording.wav` (mono 16-bit PCM),
`commands.json` (robot command response envelope) and `timing.json` (host/robot
clock samples and estimated recording start). Run these stages in order:

```bash
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.analyze_recording runs/music/limits-refine-20260914
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.classify_notes runs/music/limits-refine-20260914
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.track_harmonics runs/music/limits-refine-20260914
```

These offline scripts reproduce the experiment's analysis, including the
reference-note-based timing adjustment and target-conditioned harmonic search.
They write derived JSON alongside the recording. The fixed three-note classifier
is specific to these protocols, not a general MIDI transcription system.
`analyze_recording` also emits exploratory central-window spectral peaks; the
paper's range claims use `track_harmonics` results instead.

## Hardware protocols

[Initial sweep](../../protocols/ot2_music_limits.py) and
[refinement](../../protocols/ot2_music_limits_refine.py) are the actual executed
robot-side protocol sources. Ordinary Python execution of these two files does
not launch the robot. They require current-state verification, robot-side analysis
and explicit execution through the Opentrons workflow. The existing
[song launchers](../ot2-music-full-arrangements.md) provide separate direct-Python
entry points for the three arrangements.
