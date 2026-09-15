"""Build standard single-column LaTeX preprints and self-contained source trees.

English uses article and standard TeX Live packages (PDFLaTeX compatible).
Chinese uses ctexart and Fandol fonts (XeLaTeX). No robot connection is made.
"""

import argparse
import json
import os
import re
import shutil
import zipfile
from pathlib import Path


def latex(text):
    import pypandoc

    text = re.sub(
        r"\[(\d+(?:[–,-]\d+)*)\](?!\()",
        lambda match: citation(match[1]),
        text,
    )
    text = text.replace("(../", "(https://github.com/chenmzh/opentrons-ai/blob/main/docs/")
    rendered = pypandoc.convert_text(
        text, "latex", format="markdown+raw_tex+autolink_bare_uris", extra_args=["--wrap=none"]
    ).strip()
    rendered = re.sub(
        r"\\texttt\{([A-Za-z0-9_./\\-]+)\}",
        lambda match: r"\nolinkurl{" + match[1].replace(r"\_", "_") + "}",
        rendered,
    )
    for char, replacement in {
        "♯": r"\ensuremath{\sharp}",
        "−": r"\ensuremath{-}",
        "×": r"\ensuremath{\times}",
        "±": r"\ensuremath{\pm}",
        "→": r"\ensuremath{\rightarrow}",
        "÷": r"\ensuremath{\div}",
    }.items():
        rendered = rendered.replace(char, replacement)
    return rendered


def citation(value):
    numbers = []
    for part in value.split(","):
        if "–" in part or "-" in part:
            a, b = re.split("[–-]", part)
            numbers.extend(range(int(a), int(b) + 1))
        else:
            numbers.append(int(part))
    return r"\cite{" + ",".join(f"ref{n}" for n in numbers) + "}"


def convert_manuscript(source, language):
    manuscript = source.read_text()
    abstract_heading = "## Abstract" if language == "en" else "## 摘要"
    keywords_label = "**Keywords:**" if language == "en" else "**关键词：**"
    intro_heading = "## 1 "
    reference_heading = "## References" if language == "en" else "## 参考文献"
    title = manuscript.splitlines()[0][2:]
    abstract = manuscript.split(abstract_heading + "\n\n", 1)[1].split(keywords_label)[0].strip()
    keywords = manuscript.split(keywords_label, 1)[1].split(intro_heading)[0].strip()
    body = intro_heading + manuscript.split(intro_heading, 1)[1].split(reference_heading)[0]
    body = re.sub(r"(?m)^(#{2,3}) \d+(?:\.\d+)? ", r"\1 ", body)
    body = re.sub(r"(?m)^(#{2,3}) ", lambda match: match[1][1:] + " ", body)
    figures = []
    pattern = r"<!-- FIGURE_(\w+) -->\s*\*\*(?:Figure \d+\. |图 \d+．)(.*?)\*\*(.*?)(?=\n\n)"
    for index, match in enumerate(re.finditer(pattern, body, re.S), 1):
        token, title_caption, rest = match.groups()
        filename = "workflow.pdf" if token == "ARCHITECTURE" else f"figure-{token.lower()}.pdf"
        caption = latex(title_caption + rest)
        figures.append(
            (
                match[0],
                "\n".join(
                    [
                        r"\begin{figure}[tbp]",
                        r"\centering",
                        r"\includegraphics[width=\linewidth]{" + filename + "}",
                        r"\caption{" + caption + "}",
                        r"\label{fig:" + str(index) + "}",
                        r"\end{figure}",
                    ]
                ),
            )
        )
    for original, replacement in figures:
        body = body.replace(original, replacement)
    table_captions = []

    def table_marker(match):
        table_captions.append(latex(match[1]))
        return "TABLECAPTIONPLACEHOLDER"

    body = re.sub(r"\*\*(?:Table \d+\. |表 \d+．)(.*?)\*\*", table_marker, body)
    body = body.replace(
        "`f_model (Hz) = k × v (mm/s)，k = 4.98375 Hz/(mm/s)`。",
        r"\begin{equation} f_{\mathrm{model}}=kv,\qquad k=4.98375\;\mathrm{Hz}/(\mathrm{mm}/\mathrm{s}).\end{equation}",
    )
    body = body.replace(
        "`f_target = 440 × 2^((m−69)/12)，v = f_target/k`。",
        r"\begin{equation}f_{\mathrm{target}}=440\,2^{(m-69)/12},\qquad v=f_{\mathrm{target}}/k.\end{equation}",
    )
    body = body.replace(
        "`f_model (Hz) = k × v (mm/s), where k = 4.98375 Hz/(mm/s)`.",
        r"\begin{equation} f_{\mathrm{model}}=kv,\qquad k=4.98375\;\mathrm{Hz}/(\mathrm{mm}/\mathrm{s}).\end{equation}",
    )
    body = body.replace(
        "`f_target = 440 × 2^((m−69)/12), and v = f_target/k`.",
        r"\begin{equation}f_{\mathrm{target}}=440\,2^{(m-69)/12},\qquad v=f_{\mathrm{target}}/k.\end{equation}",
    )
    converted = latex(body)
    converted = converted.replace(r"{\def\LTcaptype{none} % do not increment counter", "{")
    table_widths = [
        [0.17, 0.42, 0.41],
        [0.17, 0.46, 0.37],
        [0.08, 0.115, 0.13, 0.675],
        [0.13, 0.17, 0.22, 0.22, 0.26],
        [0.32, 0.16, 0.14, 0.16, 0.22],
    ]
    for table_index, (caption, widths) in enumerate(zip(table_captions, table_widths, strict=True)):

        def insert_caption(match, caption=caption, widths=widths, table_index=table_index):
            numeric = [set(), set(), {1, 2}, {0, 2, 3, 4}, {1, 2, 3, 4}][table_index]
            columns = []
            for index, width in enumerate(widths):
                alignment = r"\raggedleft" if index in numeric else r"\raggedright"
                columns.append(
                    ">{"
                    + alignment
                    + r"\arraybackslash}p{(\linewidth - "
                    + str(2 * (len(widths) - 1))
                    + r"\tabcolsep) * \real{"
                    + str(width)
                    + "}}"
                )
            preamble = "{\n" + r"\begin{longtable}{@{}" + "\n" + "\n".join(columns) + "@{}}\n"
            return preamble + r"\caption{" + caption + "}\\\\\n" + match[2]

        converted = re.sub(
            r"TABLECAPTIONPLACEHOLDER\s*(\{\s*\\begin\{longtable\}.*?)(\\toprule)",
            insert_caption,
            converted,
            count=1,
            flags=re.S,
        )
    if "TABLECAPTIONPLACEHOLDER" in converted or "FIGURE_" in converted:
        raise ValueError("Figure or table conversion incomplete")
    refs = manuscript.split(reference_heading, 1)[1]
    bibliography = []
    for line in refs.strip().splitlines():
        match = re.match(r"(\d+)\. (.*)", line)
        if match:
            bibliography.append(r"\bibitem{ref" + match[1] + "} " + latex(match[2]))
    if len(figures) != 3 or len(table_captions) != 5 or len(bibliography) != 11:
        raise ValueError("Unexpected manuscript figure/table/reference count")
    documentclass = (
        r"\documentclass[10pt,a4paper]{article}"
        if language == "en"
        else r"\documentclass[10pt,a4paper,fontset=fandol]{ctexart}"
    )
    fonts = (
        r"\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern}"
        if language == "en"
        else ""
    )
    return "\n".join(
        [
            "% Standard preprint layout; not an official arXiv template.",
            documentclass,
            fonts,
            r"\usepackage[margin=25mm]{geometry}",
            r"\usepackage{amsmath,amssymb,graphicx,booktabs,longtable,array,calc}",
            r"\usepackage{microtype,xurl,hyperref}",
            r"\hypersetup{hidelinks,pdfauthor={Mingzhe Chen},pdftitle={" + title + "}}",
            r"\setlength{\emergencystretch}{3em}",
            r"\setlength{\parskip}{0.25em}",
            r"\setlength{\LTpre}{0.5em}\setlength{\LTpost}{0.5em}",
            r"\renewcommand{\arraystretch}{1.12}",
            r"\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}",
            r"\title{\Large\bfseries " + latex(title) + "}",
            r"\author{Mingzhe Chen\\\small\href{mailto:cmzcswxp@gmail.com}{\texttt{cmzcswxp@gmail.com}}}",
            r"\date{\small September 15, 2026\quad |\quad Preprint draft, version 2.0}",
            r"\begin{document}",
            r"\pagestyle{plain}",
            r"\maketitle",
            r"\begin{abstract}",
            latex(abstract),
            r"\end{abstract}",
            r"\noindent\textbf{"
            + ("Keywords: " if language == "en" else "关键词：")
            + "} "
            + latex(keywords),
            converted,
            r"\begin{thebibliography}{99}",
            *bibliography,
            r"\end{thebibliography}",
            r"\end{document}",
            "",
        ]
    )


def main():
    import cairosvg
    import pikepdf

    from .build_paper import figures, validate_evidence

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/research/arxiv"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    source = root / "docs/research"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output / ".mplconfig"))
    data = json.loads((source / "data/evidence.json").read_text())
    validate_evidence(data)
    figures(data, output)
    cairosvg.svg2pdf(
        url=str(source / "figures/workflow.svg"), write_to=str(output / "workflow-cairo.pdf")
    )
    with pikepdf.open(output / "workflow-cairo.pdf") as diagram:
        diagram.save(output / "workflow.pdf", force_version="1.5")
    for language in ["en", "zh"]:
        destination = output / language
        destination.mkdir(exist_ok=True)
        for filename in ["workflow.pdf", "figure-range.pdf", "figure-rhythm.pdf"]:
            shutil.copy2(output / filename, destination / filename)
        document = convert_manuscript(source / f"ot2-motor-music-paper.{language}.md", language)
        (destination / "main.tex").write_text(document)
        archive = output.parent / f"arxiv-source-{language}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for filename in ["main.tex", "workflow.pdf", "figure-range.pdf", "figure-rhythm.pdf"]:
                package.write(destination / filename, filename)
        print(f"LaTeX source: {destination / 'main.tex'}")
        print(f"Source package: {archive}")


if __name__ == "__main__":
    main()
