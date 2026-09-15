"""Render the research manuscript and figures from reviewed, versioned evidence.

This offline command never connects to a robot. Generated files go to build/.
"""

import argparse
import base64
import json
import os
import re
from pathlib import Path


def validate_evidence(data):
    """Reconcile published counts and timing against the retained observations."""
    import numpy as np

    if len(data["runs"]) != 2:
        raise ValueError("Expected both experimental runs")
    if sum(r["moves"] for r in data["runs"]) != 311:
        raise ValueError("Movement count differs from the verified record")
    for run in data["runs"]:
        if run["status"] != "succeeded" or run["z_mm"] != 189.27:
            raise ValueError("Run verification mismatch")
        for row in run["rhythm"]:
            moves = row["move_times_s"]
            expected = [38, 41, 50, 41] * 4
            predictions = row["predictions_midi"]
            if len(moves) != 16 or len(predictions) != 16 or row["total"] != 16:
                raise ValueError("A rhythm block must contain 16 notes")
            correct = sum(a == b for a, b in zip(expected, predictions, strict=True))
            interval = float(np.median(np.diff([m[0] for m in moves])))
            duration = row["block_end_s"] - row["block_start_s"]
            if correct != row["correct"]:
                raise ValueError("Classification count does not match predictions")
            if not np.isclose(interval, row["median_onset_interval_s"], atol=1e-9):
                raise ValueError("Median interval differs from command timestamps")
            if not np.isclose(16 / duration, row["notes_per_s"], atol=1e-9):
                raise ValueError("Throughput denominator mismatch")


def figures(data, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
    palette = ["#22577a", "#b85435"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.6), layout="constrained")
    for run, color, marker, label in zip(
        data["runs"], palette, ["o", "s"], ["Initial run", "Refinement"], strict=True
    ):
        rows = run["rhythm"]
        axes[0].scatter(
            [r["nominal_period_s"] * 1000 for r in rows],
            [r["median_onset_interval_s"] * 1000 for r in rows],
            color=color,
            marker=marker,
            label=label,
        )
        tested = [r for r in rows if r["nominal_period_s"] < 0.5]
        axes[1].scatter(
            [r["notes_per_s"] for r in tested],
            [100 * r["correct"] / r["total"] for r in tested],
            color=color,
            marker=marker,
            label=label,
        )
    axes[0].plot([10, 1200], [10, 1200], "--", color="0.5", label="Nominal = actual")
    axes[0].set(
        xscale="log",
        yscale="log",
        xlabel="Nominal note duration (ms)",
        ylabel="Median command onset interval (ms)",
        title="A  Execution timing",
    )
    axes[1].axhline(50, ls="--", color="0.5", label="Majority-class baseline")
    axes[1].set(
        xlabel="Block throughput (notes/s)",
        ylabel="Template agreement (%)",
        ylim=(0, 105),
        title="B  Three-note separability",
    )
    for ax in axes:
        ax.grid(alpha=0.15)
        ax.legend(fontsize=8, loc="best")
    for suffix in ["svg", "pdf", "png"]:
        fig.savefig(output / f"figure-rhythm.{suffix}", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.6), layout="constrained")
    rows = [r for r in data["runs"][1]["range"] if r["speed_mm_s"] > 100]
    labels = ["C5", "C6", "E6", "G6", "A6", "B6"]
    for i, row in enumerate(rows):
        axes[0].plot([i - 0.22, i + 0.22], [row["expected_base_hz"]] * 2, color="0.6", lw=2)
        for j, matches in enumerate(row["moves"]):
            first = next((m for m in matches if m["harmonic"] == 1), None)
            if first:
                x = i + (j - 1.5) * 0.075
                axes[0].scatter(x, first["component_hz"], color=palette[j % 2], s=22)
                axes[1].scatter(x, first["frame_center_span_s"] * 1000, color=palette[j % 2], s=22)
        if not any(any(m["harmonic"] == 1 for m in rep) for rep in row["moves"]):
            for ax in axes:
                ax.text(
                    i,
                    0.45,
                    "Not\ndetected",
                    ha="center",
                    va="center",
                    fontsize=8,
                    transform=ax.get_xaxis_transform(),
                    color=palette[1],
                )
    for ax in axes:
        ax.set_xticks(np.arange(len(labels)), labels)
        ax.set_xlim(-0.5, len(labels) - 0.5)
        ax.set_xlabel("Target note (four strokes each)")
        ax.grid(axis="y", alpha=0.15)
    axes[0].set(ylabel="Detected target component (Hz)", title="A  Frequency evidence")
    axes[1].set(
        ylabel="Qualified frame-center span (ms)", ylim=(0, 800), title="B  Temporal persistence"
    )
    for suffix in ["svg", "pdf", "png"]:
        fig.savefig(output / f"figure-range.{suffix}", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/research"))
    parser.add_argument("--language", choices=["zh", "en", "all"], default="all")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    source = root / "docs/research"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output / ".mplconfig"))
    data = json.loads((source / "data/evidence.json").read_text())
    validate_evidence(data)
    figures(data, output)
    languages = ["zh", "en"] if args.language == "all" else [args.language]
    for language in languages:
        render_article(source, output, language)


def render_article(source, output, language):
    """Render a complete manuscript with its figures and attached captions."""

    import markdown

    manuscript = (source / f"ot2-motor-music-paper.{language}.md").read_text()
    architecture = base64.b64encode((source / "figures/workflow.svg").read_bytes()).decode()
    manuscript = manuscript.replace(
        "<!-- FIGURE_ARCHITECTURE -->",
        f'<figure><img alt="Human–AI acoustic feedback architecture" '
        f'src="data:image/svg+xml;base64,{architecture}"></figure>',
    )
    for token, filename in [("RANGE", "range"), ("RHYTHM", "rhythm")]:
        encoded = base64.b64encode((output / f"figure-{filename}.svg").read_bytes()).decode()
        manuscript = manuscript.replace(
            f"<!-- FIGURE_{token} -->",
            f'<figure><img alt="{filename}" src="data:image/svg+xml;base64,{encoded}"></figure>',
        )
    body = markdown.markdown(manuscript, extensions=["tables", "fenced_code"])
    body = re.sub(
        r"</figure>\s*<p>(<strong>(?:图 \d+．|Figure \d+\. ).*?</p>)",
        r"<figcaption><p>\1</figcaption></figure>",
        body,
        flags=re.S,
    )
    # Resolve repository references for a standalone exported document.
    body = body.replace(
        'href="../', 'href="https://github.com/chenmzh/opentrons-ai/blob/main/docs/'
    )
    css = """
    @page { size: A4; margin: 19mm 17mm 20mm; }
    body { max-width: 850px; margin: 32px auto; padding: 0 20px; color: #18212a;
      font: 11pt/1.7 'Noto Serif CJK SC', 'Noto Serif CJK JP', serif; }
    h1 { font-size: 23pt; line-height: 1.35; margin-bottom: 16px; }
    h2 { font-size: 16pt; border-bottom: 1px solid #ccd3da; padding-bottom: 5px; }
    h3 { font-size: 12pt; }
    h1,h2,h3 { break-after: avoid; }
    p { text-align: justify; orphans: 3; widows: 3; }
    table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 16px 0; }
    thead { display: table-header-group; }
    td,th { border-bottom: 1px solid #d8dfe5; padding: 6px; text-align: left; }
    th { background: #eef3f6; }
    tr { break-inside: avoid; }
    figure { margin: 18px 0; break-inside: avoid; }
    img { width: 100%; }
    code { font-size: 9pt; overflow-wrap: anywhere; }
    a { color: #22577a; text-decoration: none; overflow-wrap: anywhere; }
    @media print { body { max-width: none; padding: 0; margin: 0; font-size: 10pt; } }
    """
    if language == "zh":
        from .report_fonts import chinese_font_css

        css += chinese_font_css(manuscript, output)
    if language == "en":
        css += "body { font-family: 'Liberation Serif', 'Times New Roman', serif; }"
    locale = "zh-CN" if language == "zh" else "en"
    html = f'<!doctype html><html lang="{locale}"><meta charset="utf-8"><title>OT-2 motor music study ({language})</title><style>{css}</style><body>{body}</body></html>'
    destination = output / f"ot2-motor-music-paper.{language}.html"
    destination.write_text(html)
    print(f"Evidence verified; report: {destination}")


if __name__ == "__main__":
    main()
