#!/usr/bin/env python3
"""Translate the no-collinear-triples walk into Pauli-block commutators.

For A=P_b-P_a, define G_A=A_x X+A_y Y+A_z Z.  Then
[G_A,G_B]=2i(A cross B).sigma, so the Erdős 193 theorem gives a finite-alphabet
pulse word whose adjacent aggregate blocks never commute.  This finite-prefix
study measures the normalized and unnormalized commutator margins for equal
adjacent dyadic blocks.  Completed scales are atomically checkpointed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
STOP_REQUESTED = False


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def request_stop(_signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Logger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event, **fields):
        record = {"time": utc_now(), "event": event, **fields}
        line = json.dumps(record, sort_keys=True)
        with self.path.open("a") as handle:
            handle.write(line + "\n")
            handle.flush()
        print(line, flush=True)


def gaussian_points(count):
    corners = (0j, 1j, -1 + 1j, -1 + 0j)
    units = (1 + 0j, 1j, -1 + 0j, -1j)
    points, z = [], 0j
    for n in range(count):
        alpha = n.bit_count() & 3
        w = 2 * z + corners[alpha]
        points.append((int(w.real), int(w.imag), 4 * n + alpha))
        z += units[alpha]
    return points


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm_squared(a):
    return sum(x * x for x in a)


def quantiles(values):
    values.sort()
    count = len(values)
    def at(fraction):
        return values[min(count - 1, int(fraction * (count - 1)))]
    return {"minimum": values[0], "p01": at(0.01), "p10": at(0.10),
            "median": at(0.50), "p90": at(0.90), "p99": at(0.99),
            "maximum": values[-1]}


def analyze_scale(points, block_length):
    normalized, cross_norms = [], []
    minimum_cross_squared = None
    zero_crosses = 0
    for start in range(len(points) - 2 * block_length):
        first = subtract(points[start + block_length], points[start])
        second = subtract(points[start + 2 * block_length], points[start + block_length])
        product = cross(first, second)
        cross_squared = norm_squared(product)
        if cross_squared == 0:
            zero_crosses += 1
            continue
        minimum_cross_squared = (cross_squared if minimum_cross_squared is None
                                 else min(minimum_cross_squared, cross_squared))
        cross_norm = math.sqrt(cross_squared)
        cross_norms.append(cross_norm)
        normalized.append(cross_norm / math.sqrt(norm_squared(first) * norm_squared(second)))
    return {"block_length": block_length, "triples": len(points) - 2 * block_length,
            "zero_commutators": zero_crosses,
            "minimum_cross_squared_exact": minimum_cross_squared,
            "normalized_commutator_ratio": quantiles(normalized),
            "cross_product_norm": quantiles(cross_norms),
            "pauli_commutator_spectral_norm":
            {name: 2 * value for name, value in quantiles(cross_norms).items()}}


def fit_power(rows, field, minimum_scale):
    selected = [row for row in rows if row["block_length"] >= minimum_scale]
    coordinates = [(math.log(row["block_length"]),
                    math.log(row["normalized_commutator_ratio"][field])) for row in selected]
    xbar = sum(x for x, _ in coordinates) / len(coordinates)
    ybar = sum(y for _, y in coordinates) / len(coordinates)
    denominator = sum((x - xbar) ** 2 for x, _ in coordinates)
    exponent = sum((x - xbar) * (y - ybar) for x, y in coordinates) / denominator
    prefactor = math.exp(ybar - exponent * xbar)
    return {"statistic": field, "minimum_scale": minimum_scale,
            "exponent": exponent, "prefactor": prefactor, "fit_points": len(selected)}


def markdown_report(result):
    rows = result["scales"]
    lines = [
        "# Pauli-control consequence of no three collinear vertices", "",
        "> **Status:** the nonvanishing statement is an unconditional corollary of the",
        "> Erdős 193 construction. Numerical margins below are finite-prefix diagnostics,",
        "> not a demonstrated quantum-control application.", "",
        "For a chord `A`, define `G_A=A_x X+A_y Y+A_z Z`. The Pauli identity gives", "",
        "```text", "[G_A,G_B] = 2 i (A cross B).sigma.", "```", "",
        "For every `a<b<c`, use `A=P_b-P_a` and `B=P_c-P_b`. No three vertices are",
        "collinear, so this commutator is never zero. Moreover, `G_A`, `G_B`, and their",
        "commutator span `su(2)`. Thus each pair is Lie-algebraically universal for a",
        "single qubit if the two aggregate Hamiltonians can be independently addressed.",
        "Equivalently, the finite step word has noncommuting aggregate generators for",
        "every pair of adjacent nonempty blocks, regardless of their lengths.", "",
        f"Parameters: `{result['parameters']}`", "",
        "The normalized ratio is `|A cross B|/(|A||B|)=sin(theta)`. It is the",
        "commutator margin when both aggregate generators are normalized. The unnormalized",
        "Pauli commutator has spectral norm `2|A cross B|`.", "",
        "| equal block length | triples | min sin(theta) | median sin(theta) | min |A×B| | median |A×B| |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        n = row["normalized_commutator_ratio"]
        c = row["cross_product_norm"]
        lines.append(f"| {row['block_length']:,} | {row['triples']:,} | {n['minimum']:.8g} | "
                     f"{n['median']:.8g} | {c['minimum']:.8g} | {c['median']:.8g} |")
    lines += ["", "## Scale dependence", "",
              f"For block lengths at least {result['median_margin_fit']['minimum_scale']}, the median",
              f"normalized margin fits approximately `L^{result['median_margin_fit']['exponent']:.4f}`.",
              f"The minimum fits approximately `L^{result['minimum_margin_fit']['exponent']:.4f}`.",
              "Thus the exact all-scale noncommutation does not provide a scale-independent",
              "normalized robustness margin. Local one-step blocks are substantially better:",
              f"their minimum `sin(theta)` is {rows[0]['normalized_commutator_ratio']['minimum']:.3f}.", "",
              "## Interpretation", "",
              "This is a direct use of non-collinearity and can be read as a persistently",
              "non-Abelian finite-alphabet pulse word. Conditional on independent access to",
              "the block Hamiltonians, every adjacent block pair generates all of `su(2)`.",
              "It may be relevant to qubit-control identifiability or protocols designed to",
              "avoid commuting aggregate controls.",
              "However, large normalized blocks become nearly parallel, and unitary products",
              "depend on pulse durations and higher Magnus terms, not only vector sums. A useful",
              "application requires a robustness theorem or a finite-prefix experimental task.", ""]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=131072)
    parser.add_argument("--max-block", type=int, default=16384)
    parser.add_argument("--checkpoint", default="logs/pauli-noncommutativity.ckpt.json")
    parser.add_argument("--log", default="logs/pauli-noncommutativity.log")
    parser.add_argument("--output", default="results/pauli-noncommutativity.json")
    parser.add_argument("--report", default="physics/PAULI-NONCOMMUTATIVITY.md")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.points < 8 or args.max_block < 1 or 2 * args.max_block >= args.points:
        raise SystemExit("need points >=8 and 1 <= max-block < points/2")
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parameters = {"points": args.points, "max_block": args.max_block}
    identity = {"version": VERSION, "source_sha256": source_hash, "parameters": parameters}
    logger, checkpoint = Logger(args.log), Path(args.checkpoint)
    rows, resumed = [], False
    if checkpoint.exists():
        try:
            prior = json.loads(checkpoint.read_text())
            if prior.get("identity") == identity:
                rows, resumed = prior["completed_scales"], True
            else:
                logger.emit("checkpoint_rejected", reason="identity mismatch", checkpoint=str(checkpoint))
        except Exception as error:
            logger.emit("checkpoint_rejected", reason=str(error), checkpoint=str(checkpoint))
    logger.emit("start", parameters=parameters, source_sha256=source_hash, resumed=resumed,
                completed_scales=[row["block_length"] for row in rows], cpu_workers=1,
                checkpoint=str(checkpoint))
    points, done = gaussian_points(args.points), {row["block_length"] for row in rows}
    scale, started = 1, time.monotonic()
    while scale <= args.max_block:
        if scale not in done:
            scale_started = time.monotonic()
            row = analyze_scale(points, scale)
            rows.append(row)
            rows.sort(key=lambda item: item["block_length"])
            atomic_json(checkpoint, {"identity": identity, "completed_scales": rows})
            logger.emit("scale_complete", block_length=scale, triples=row["triples"],
                        minimum_normalized_margin=row["normalized_commutator_ratio"]["minimum"],
                        elapsed_seconds=time.monotonic() - scale_started,
                        checkpoint=str(checkpoint))
        if STOP_REQUESTED:
            logger.emit("interrupted", block_length=scale, checkpoint=str(checkpoint))
            return 130
        scale *= 2
    fit_minimum = min(64, args.max_block)
    result = {"status": "proved nonvanishing; finite computational margin diagnostics",
              "generated_at": utc_now(), "source_sha256": source_hash,
              "parameters": parameters, "scales": rows,
              "median_margin_fit": fit_power(rows, "median", fit_minimum),
              "minimum_margin_fit": fit_power(rows, "minimum", fit_minimum)}
    atomic_json(args.output, result)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(markdown_report(result))
    logger.emit("complete", elapsed_seconds=time.monotonic() - started,
                output=args.output, report=args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
