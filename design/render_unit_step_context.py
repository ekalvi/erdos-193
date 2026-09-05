#!/usr/bin/env python3
"""Render planar g85/g170 walks and the tagged g85 lift for the 6D note."""

from __future__ import annotations

import argparse
from pathlib import Path

# Keep native numerical libraries within the repository's host limit even when
# this script is launched outside the documented command.
import os
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

DIRECTIONS = np.array(((1, 0), (0, 1), (-1, 0), (0, -1)), dtype=float)
OFFSETS = np.array(((0, 0), (-1, 0), (-1, 1), (0, -1)), dtype=float)
COLORS = np.array(("#56b4e9", "#e69f00", "#009e73", "#cc79a7"))


def states(pattern: str, count: int) -> np.ndarray:
    epsilon = np.array([1 if char == "+" else -1 for char in pattern], dtype=int)
    answer = np.zeros(count, dtype=int)
    for n in range(count):
        value = n
        place = 0
        total = 0
        while value:
            if value & 1:
                total += int(epsilon[place % len(epsilon)])
            value >>= 1
            place += 1
        answer[n] = total % 4
    return answer


def source_and_lift(pattern: str, count: int):
    sigma = states(pattern, count)
    source = np.zeros((count, 2), dtype=float)
    if count > 1:
        source[1:] = np.cumsum(DIRECTIONS[sigma[:-1]], axis=0)
    tagged = 2 * source + OFFSETS[sigma]
    height = 4 * np.arange(count) + sigma
    return sigma, source, tagged, height


def colored_trace(axis, points: np.ndarray, sigma: np.ndarray) -> None:
    segments = np.stack((points[:-1], points[1:]), axis=1)
    collection = LineCollection(segments, colors=COLORS[sigma[:-1]], linewidths=.82, alpha=.9)
    axis.add_collection(collection)
    axis.scatter(points[0, 0], points[0, 1], s=22, c="#ffffff", edgecolors="#07101d", linewidths=.8, zorder=3)
    axis.scatter(points[-1, 0], points[-1, 1], s=22, c="#ffcf66", edgecolors="#07101d", linewidths=.8, zorder=3)
    axis.autoscale()
    axis.set_aspect("equal", adjustable="datalim")


def render(count: int, pdf: Path, svg: Path, png: Path) -> None:
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.facecolor": "#080e1a",
        "figure.facecolor": "#080e1a",
        "axes.edgecolor": "#41516a",
        "axes.labelcolor": "#c6d4e7",
        "xtick.color": "#8394ad",
        "ytick.color": "#8394ad",
        "text.color": "#e8f0fb",
        "svg.hashsalt": "erdos193-unit-step-context",
    })
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.25), constrained_layout=True)
    records = []
    for axis, (rule, pattern) in zip(axes[:2], ((85, "+-+-+-+-"), (170, "-+-+-+-+"))):
        sigma, source, _, _ = source_and_lift(pattern, count)
        colored_trace(axis, source, sigma)
        axis.set_title(rf"$g_{{{rule}}}$  $\varepsilon={pattern}$", fontweight="bold", pad=7)
        axis.set_xlabel(r"$\Re z_n$")
        axis.set_ylabel(r"$\Im z_n$")
        axis.grid(color="#52637a", alpha=.18, linewidth=.5)
        records.append((sigma, source))

    sigma, _, tagged, height = source_and_lift("+-+-+-+-", count)
    # An explicit oblique projection; vertical height is compressed so planar
    # structure and monotone lifting remain visible in one static panel.
    projected = np.column_stack((tagged[:, 0] + .42 * tagged[:, 1], height / 28 + .22 * tagged[:, 1]))
    colored_trace(axes[2], projected, sigma)
    axes[2].set_aspect("auto")
    axes[2].set_title(r"tagged $g_{85}$ lift $Q_n$", fontweight="bold", pad=7)
    axes[2].set_xlabel(r"oblique planar coordinate")
    axes[2].set_ylabel(r"height $h_n/28$ (compressed)")
    axes[2].grid(color="#52637a", alpha=.18, linewidth=.5)

    fig.suptitle(
        f"Alternating signed-Gaussian rules and the valuation lift · first {count} vertices",
        fontsize=11.5,
        fontweight="bold",
    )
    pdf.parent.mkdir(parents=True, exist_ok=True)
    svg.parent.mkdir(parents=True, exist_ok=True)
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf, bbox_inches="tight", metadata={"Creator": "design/render_unit_step_context.py", "CreationDate": None})
    fig.savefig(svg, bbox_inches="tight", metadata={"Creator": "design/render_unit_step_context.py", "Date": None})
    # Matplotlib writes spaces before newlines in multiline SVG path data.
    # Normalize those generated lines so repository whitespace checks stay clean.
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    fig.savefig(png, bbox_inches="tight", dpi=180, metadata={"Software": "design/render_unit_step_context.py"})
    plt.close(fig)
    print(f"vertices={count} pdf={pdf} svg={svg} png={png}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=512)
    parser.add_argument("--pdf", type=Path, default=Path("paper/unit_step_g85_g170_context.pdf"))
    parser.add_argument("--svg", type=Path, default=Path("results/unit-step-g85-g170-context.svg"))
    parser.add_argument("--png", type=Path, default=Path("results/unit-step-g85-g170-context.png"))
    args = parser.parse_args()
    if args.count < 2:
        parser.error("--count must be at least 2")
    render(args.count, args.pdf, args.svg, args.png)


if __name__ == "__main__":
    main()
