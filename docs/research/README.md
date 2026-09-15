# OT-2 motor-music research report

The report is available in both languages, with the same methods, numerical
results, figures and limitations. Version 2.0 reframes the work as a retrospective human–AI co-development case
study with single-device experiments. It is a manuscript draft, not a
peer-reviewed publication. The author is Mingzhe Chen
([cmzcswxp@gmail.com](mailto:cmzcswxp@gmail.com)).

The [architecture and role supplement](workflow-evidence.md) attributes
human-origin design decisions and describes the agent/tool boundaries. The
[supplementary experiment plan](feedback-experiment-plan.md) freezes a separate
held-out acoustic-feedback validation. It tests numerical feedback, not an
LLM-versus-conventional-calibration performance claim.

The [completed feedback supplement](feedback-validation.md) reports 0/12 versus
8/12 held-out strokes meeting the frozen ±25-cent criterion, with four uncertain
feedback estimates. All 36 calibration/test measurement rows are retained in
[`data/feedback-evidence.json`](data/feedback-evidence.json). See
[submission notes](submission-notes.md) for the remaining author declarations
and boundaries of the research claims.

| Language | Manuscript | PDF | LaTeX source |
|---|---|---|---|
| English | [Read online](ot2-motor-music-paper.en.md) | [Download PDF](pdf/ot2-motor-music-paper.en.pdf) | [Download ZIP](latex/arxiv-source-en.zip) |
| 中文 | [在线阅读](ot2-motor-music-paper.zh.md) | [下载 PDF](pdf/ot2-motor-music-paper.zh.pdf) | [下载 ZIP](latex/arxiv-source-zh.zip) |

`data/evidence.json` is the reviewed numerical supplement, including per-note
command times, class predictions, qualified harmonic measurements, anonymized experiment labels,
and SHA-256 hashes of the local source records. It excludes microphone audio,
HTTP logs, credentials and local databases. Missing detections are empty lists,
not measurements at zero frequency. The supplement supports table and figure
reconstruction; independent acoustic reanalysis requires the original recordings,
which are retained locally and are not distributed with this repository.

## Rebuild figures and manuscript sources

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
The distributed PDFs now use the LaTeX preprint layout described below. The
following older HTML export remains available for preview only; it does not
replace the distributed PDFs. After installing the frontend dependencies:

```bash
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install chromium
for lang in zh en; do
  node frontend/scripts/export-paper.mjs \
    "build/research/ot2-motor-music-paper.$lang.html" \
    "build/research/ot2-motor-music-paper.$lang.pdf"
  PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.optimize_pdf \
    "build/research/ot2-motor-music-paper.$lang.pdf" \
    "build/research/preview-paper.$lang.pdf"
done
```

The Chinese renderer uses Fontconfig and installed Noto Sans CJK fonts, converts
only the needed glyphs to a compact embedded TrueType subset, and preserves the
font's license metadata. It uses regular-weight text to avoid large synthetic
bold glyph outlines. The English renderer uses Liberation Serif or Times New
Roman. PDF stream optimization preserves searchable text and vector figures.
Both manuscripts remain readable directly on GitHub; the downloadable PDFs
include the figures and their captions.

## LaTeX preprint layout and source packages

The main PDFs use a conventional single-column LaTeX preprint layout, with a
centered title/author block, abstract, numbered sections/equations/tables, and
bibliographic citations. arXiv does not impose a single branded article template;
this is a standard `article` layout, not an official arXiv style file or an
acceptance claim. The English source is designed for PDFLaTeX with standard TeX
Live packages; the Chinese source uses `ctexart` and Fandol fonts with XeLaTeX.
Local verification used Tectonic 0.17.0 (XeTeX engine) for both languages.

Generate the self-contained source directories with the research dependencies:

```bash
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.build_latex
```

Each directory `build/research/arxiv/en/` or `zh/` contains `main.tex` and the
three included vector PDF figures. Compile `main.tex` twice with PDFLaTeX for
English or XeLaTeX for Chinese, or use `tectonic --keep-logs main.tex`. Compile
from the selected directory. Copy the reviewed `main.pdf` to the corresponding
path in `docs/research/pdf/` only after checking the output.

Source ZIPs for this draft are prepared as
`build/research/arxiv-source-en.zip` and `arxiv-source-zh.zip`; reviewed publication
copies are versioned in [`latex/`](latex/). They contain only
`main.tex` and its three PDF figures, without intermediate logs, the compiled
article, runtime records, or personal configuration. They can also be imported
into Overleaf. The source tree does not need Python, raw recordings, shell escape,
or on-the-fly SVG conversion to compile. The manuscript still needs the author's
remaining declarations and a submission decision; no arXiv submission has occurred.

When a document was authored in LaTeX, arXiv normally requires its source rather
than just the compiled PDF. See the official [TeX submission instructions](https://info.arxiv.org/help/submit_tex.html)
and [PDF policy](https://info.arxiv.org/help/submit_pdf.html). The English source
package is the intended primary submission artifact; the Chinese package is a
translation for the author's use, not an automatic second arXiv submission.

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
