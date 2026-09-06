#!/usr/bin/env python3
"""Render the canonical problem as a monochrome email PNG and standalone LaTeX.

One small single-core atomic task, no browser/server/network. Completed outputs
are SHA-256 checked and reused from --state-dir. Incompatible or corrupt state
is rejected; use a new state directory for an intentional source/code change.
Interruption before completion simply repeats this small render on restart.
Run: uv run --with matplotlib==3.10.6 python research/unit-step/render_problem.py
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".checkpoint-unit-step-problem-image")
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.state_dir / "state.json"
    log = args.state_dir / "run.jsonl"
    source = (HERE / "PROBLEM.md").read_text()
    identity = dict(schema=1, code_sha256=sha(Path(__file__).read_bytes()),
                    source_sha256=sha(source.encode()), matplotlib=matplotlib.__version__, dpi=150)
    paths = [HERE / "unit-step-problem.png", HERE / "unit-step-problem.tex"]
    started = time.monotonic()

    def event(name, **extra):
        row = dict(time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), event=name, **extra)
        with log.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
        print(json.dumps(row, sort_keys=True), flush=True)

    try:
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            if saved["identity"] != identity:
                raise ValueError("incompatible checkpoint; use a fresh --state-dir")
            if saved["outputs"] != {p.name: sha(p.read_bytes()) for p in paths}:
                raise ValueError("corrupt output/checkpoint")
            event("resume_complete", identity=identity, completed=1, total=1, checkpoint=str(checkpoint))
            return
        event("start", identity=identity, threads=1, completed=0, total=1, eta_seconds=5, checkpoint=str(checkpoint))
        statement = source.split("\n## Exactly equivalent combinatorial problem\n", 1)[0]
        displays = [re.sub(r"\s+", " ", s).strip() for s in re.findall(r"\$\$(.*?)\$\$", statement, re.S)]
        assert len(displays) == 2 and "$P_0=0$" in source
        steps, triples = displays
        plt.rcParams.update({"font.family": "DejaVu Serif", "mathtext.fontset": "cm", "font.size": 15})
        fig = plt.figure(figsize=(10, 8), facecolor="white")
        def text(x, y, value, **options):
            value = re.sub(r"\\(ge|le|ne)(?![A-Za-z])", lambda m: "\\" + {"ge": "geq", "le": "leq", "ne": "neq"}[m[1]], value)
            return fig.text(x, y, value, color="black", **options)
        text(.07, .925, "Minimum dimension for a", fontsize=22, weight="bold")
        text(.07, .875, "no-three-collinear unit-step walk", fontsize=22, weight="bold")
        text(.07, .795, r"Find the least positive integer $d_*$ admitting an infinite sequence")
        text(.07, .755, r"$P_n\in\mathbb{Z}^{d_*}$, where $e_1,\ldots,e_{d_*}$ are the standard basis vectors.")
        text(.07, .670, "1. Start at the origin:", weight="bold")
        text(.50, .610, r"$P_0=0.$", ha="center", fontsize=21)
        text(.07, .535, "2. Take positive unit steps:", weight="bold")
        text(.50, .475, "$" + steps + "$", ha="center", fontsize=20)
        text(.07, .395, "3. No three vertices are collinear:", weight="bold")
        text(.50, .335, "$" + triples + "$", ha="center", fontsize=19)
        text(.07, .265, r"Coordinate sums equal $n$, so the last condition expresses noncollinearity.", fontsize=12.5)
        text(.07, .195, r"Goal: prove existence at $d_*$ and impossibility in every smaller dimension.", fontsize=13.5)
        text(.07, .145, "Dimensions 1–3: impossible.", fontsize=13.5)
        text(.07, .100, "Dimensions 4 and 5: unresolved.", fontsize=13.5)
        text(.07, .055, "Dimension 6: proposed construction, awaiting independent review.", fontsize=13.5)
        temporary = paths[0].with_suffix(".png.tmp")
        fig.savefig(temporary, format="png", dpi=identity["dpi"], facecolor="white", metadata={"Software": "Matplotlib " + matplotlib.__version__})
        plt.close(fig)
        temporary.replace(paths[0])
        tex = r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb}
\usepackage[margin=1in]{geometry}
\pagestyle{empty}
\begin{document}
\section*{Minimum dimension for a no-three-collinear unit-step walk}
Determine the least positive integer $d_*$ admitting an infinite sequence
$P_n\in\mathbb Z^{d_*}$, with $P_0=0$, such that
\[
""" + steps + "\n\\]\nand\n\\[\n" + triples + r"""
\]
Here $e_1,\ldots,e_{d_*}$ are the standard basis vectors. The coordinate sum
of $P_n$ is $n$, so the last condition is equivalent to noncollinearity.

Prove existence in dimension $d_*$ and impossibility in every smaller dimension.
\begin{itemize}
\item Dimensions 1--3: impossible.
\item Dimensions 4 and 5: unresolved.
\item Dimension 6: proposed construction, awaiting independent review.
\end{itemize}
\end{document}
"""
        temporary = paths[1].with_suffix(".tex.tmp")
        temporary.write_text(tex)
        temporary.replace(paths[1])
        saved = dict(identity=identity, outputs={p.name: sha(p.read_bytes()) for p in paths})
        temporary = checkpoint.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(saved, indent=2) + "\n")
        temporary.replace(checkpoint)
        event("complete", completed=1, total=1, elapsed_seconds=time.monotonic()-started, outputs=list(saved["outputs"]), checkpoint=str(checkpoint))
    except Exception as exc:
        event("error", error=str(exc), checkpoint=str(checkpoint))
        raise


if __name__ == "__main__":
    main()
