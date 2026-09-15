# OT-2 motor-music research report

The report is available in both languages, with the same methods, numerical
results, figures and limitations. It is an exploratory single-device study,
not a peer-reviewed publication.

| Language | Manuscript | PDF |
|---|---|---|
| English | [Read online](ot2-motor-music-paper.en.md) | [Download PDF](pdf/ot2-motor-music-paper.en.pdf) |
| 中文 | [在线阅读](ot2-motor-music-paper.zh.md) | [下载 PDF](pdf/ot2-motor-music-paper.zh.pdf) |

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
SVG, PDF and PNG figures plus self-contained Chinese and English HTML articles to `build/research/`.
Open either HTML file in a browser to read or print. Intermediate exports are
ignored by Git; the two reviewed article PDFs in `pdf/` are versioned publication
artifacts explicitly requested by the maintainer. Use `--language en` or
`--language zh` to render only one language.
For an automated article PDF after installing the frontend dependencies:

```bash
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install chromium
for lang in zh en; do
  node frontend/scripts/export-paper.mjs \
    "build/research/ot2-motor-music-paper.$lang.html" \
    "build/research/ot2-motor-music-paper.$lang.pdf"
  PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.optimize_pdf \
    "build/research/ot2-motor-music-paper.$lang.pdf" \
    "docs/research/pdf/ot2-motor-music-paper.$lang.pdf"
done
```

The Chinese renderer uses Fontconfig and installed Noto Sans CJK fonts, converts
only the needed glyphs to a compact embedded TrueType subset, and preserves the
font's license metadata. It uses regular-weight text to avoid large synthetic
bold glyph outlines. The English renderer uses Liberation Serif or Times New
Roman. PDF stream optimization preserves searchable text and vector figures.
Both manuscripts remain readable directly on GitHub; the downloadable PDFs
include the figures and their captions.

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
