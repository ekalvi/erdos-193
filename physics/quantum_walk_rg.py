#!/usr/bin/env python3
"""Dyadic renormalization study of the Gaussian-phase coined quantum walk.

For alpha_t=popcount(t) mod 4, offset block propagators obey
B[r+1,a] = B[r,a+1] B[r,a].  Differentiating this recursion in momentum
allows Monte Carlo integration of exact momentum-space moment formulas at
very large dyadic times without simulating every position.  Sampling is
finite and statistical; durable checkpoints make the run safely resumable.
"""

from __future__ import annotations

import argparse
import cmath
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
MASK64 = (1 << 64) - 1
Q = 1 / math.sqrt(2)
UNITS = (1 + 0j, 1j, -1 + 0j, -1j)
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


def splitmix64(value):
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return value ^ (value >> 31)


def matrix_multiply(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return (a * e + b * g, a * f + b * h,
            c * e + d * g, c * f + d * h)


def matrix_add(x, y):
    return tuple(a + b for a, b in zip(x, y))


def matrix_apply(matrix, vector):
    a, b, c, d = matrix
    x, y = vector
    return a * x + b * y, c * x + d * y


def base_matrices(momentum):
    left_phase = cmath.exp(-1j * momentum)
    right_phase = left_phase.conjugate()
    blocks, derivatives = [], []
    for unit in UNITS:
        block = (Q * left_phase, Q * left_phase,
                 Q * right_phase * unit, -Q * right_phase * unit)
        derivative = (-1j * block[0], -1j * block[1],
                      1j * block[2], 1j * block[3])
        blocks.append(block)
        derivatives.append(derivative)
    return blocks, derivatives


def unitarity_error(matrix):
    a, b, c, d = matrix
    return max(abs(abs(a) ** 2 + abs(c) ** 2 - 1),
               abs(abs(b) ** 2 + abs(d) ** 2 - 1),
               abs(a.conjugate() * b + c.conjugate() * d))


def sample_levels(sample_id, seed, max_level):
    random_bits = splitmix64(seed + sample_id)
    momentum = 2 * math.pi * ((random_bits + 0.5) / (1 << 64))
    blocks, derivatives = base_matrices(momentum)
    initial = (Q + 0j, 1j * Q)
    values = []
    maximum_unitarity_error = 0.0
    for level in range(max_level + 1):
        state = matrix_apply(blocks[0], initial)
        derivative_state = matrix_apply(derivatives[0], initial)
        inner = state[0].conjugate() * derivative_state[0] + state[1].conjugate() * derivative_state[1]
        mean_integrand = (-1j * inner).real
        second_integrand = abs(derivative_state[0]) ** 2 + abs(derivative_state[1]) ** 2
        values.append((mean_integrand, second_integrand))
        maximum_unitarity_error = max(maximum_unitarity_error, unitarity_error(blocks[0]))
        if level == max_level:
            break
        old_blocks, old_derivatives = blocks, derivatives
        blocks, derivatives = [], []
        for offset in range(4):
            upper = (offset + 1) & 3
            blocks.append(matrix_multiply(old_blocks[upper], old_blocks[offset]))
            derivatives.append(matrix_add(
                matrix_multiply(old_derivatives[upper], old_blocks[offset]),
                matrix_multiply(old_blocks[upper], old_derivatives[offset])))
    return values, maximum_unitarity_error


def empty_sums(count):
    return {"mean": [0.0] * count, "mean2": [0.0] * count,
            "second": [0.0] * count, "second2": [0.0] * count,
            "maximum_unitarity_error": 0.0}


def add_sample(sums, values, unitary_error):
    for level, (mean, second) in enumerate(values):
        sums["mean"][level] += mean
        sums["mean2"][level] += mean * mean
        sums["second"][level] += second
        sums["second2"][level] += second * second
    sums["maximum_unitarity_error"] = max(sums["maximum_unitarity_error"], unitary_error)


def standard_error(total, total2, count):
    if count < 2:
        return None
    variance = max(0.0, (total2 - total * total / count) / (count - 1))
    return math.sqrt(variance / count)


def records_from_sums(sums, count):
    records = []
    for level in range(len(sums["mean"])):
        mean = sums["mean"][level] / count
        second = sums["second"][level] / count
        mean_se = standard_error(sums["mean"][level], sums["mean2"][level], count)
        second_se = standard_error(sums["second"][level], sums["second2"][level], count)
        variance = second - mean * mean
        conservative_se = second_se + 2 * abs(mean) * mean_se
        records.append({"level": level, "time": 1 << level, "mean": mean,
                        "mean_standard_error": mean_se, "second_moment": second,
                        "second_moment_standard_error": second_se, "variance": variance,
                        "variance_conservative_standard_error": conservative_se,
                        "relative_variance_standard_error": conservative_se / variance if variance else None})
    return records


def fit_loglog(records, levels):
    chosen = [row for row in records if row["level"] >= levels]
    coordinates = [(math.log(row["time"]), math.log(row["variance"])) for row in chosen]
    xbar = sum(x for x, _ in coordinates) / len(coordinates)
    ybar = sum(y for _, y in coordinates) / len(coordinates)
    denominator = sum((x - xbar) ** 2 for x, _ in coordinates)
    slope = sum((x - xbar) * (y - ybar) for x, y in coordinates) / denominator
    intercept = ybar - slope * xbar
    return {"exponent": slope, "prefactor": math.exp(intercept),
            "minimum_level": levels, "fit_points": len(chosen)}


def local_exponents(records):
    rows = []
    for left, right in zip(records, records[1:]):
        rows.append({"ending_level": right["level"], "ending_time": right["time"],
                     "exponent": math.log(right["variance"] / left["variance"], 2)})
    return rows


def markdown_report(result):
    selected = [row for row in result["records"] if row["level"] <= 12 or row["level"] % 2 == 0]
    lines = [
        "# Dyadic renormalization of the Gaussian-phase quantum walk", "",
        "> **Status:** finite Monte Carlo integration of exact momentum-space recursions.",
        "> This supports a quantum-walk research direction, not a quantum application of the",
        "> Erdős 193 theorem and not an asymptotic theorem.", "",
        "## Exact recursion", "",
        "For a block beginning with phase offset `a`, the digit-sum word splits into an",
        "unshifted half followed by a half with offset `a+1 (mod 4)`. With chronological",
        "operators multiplying right-to-left,", "",
        "```text", "B[r+1,a](k) = B[r,a+1](k) B[r,a](k).", "```", "",
        "The same product rule is differentiated in momentum. Parseval's identities give",
        "the first position moment from `-i psi† dpsi/dk` and the second from",
        "`||dpsi/dk||²`. Momentum integration is estimated by deterministic pseudorandom",
        "uniform samples.", "",
        f"Parameters: `{result['parameters']}`", "",
        f"Late-level variance exponent: **{result['late_variance_fit']['exponent']:.6f}**",
        f"(levels {result['late_variance_fit']['minimum_level']}–{result['parameters']['max_level']}).", "",
        "| level | time | variance | conservative MC relative SE | local beta |", "|---:|---:|---:|---:|---:|",
    ]
    local = {row["ending_level"]: row["exponent"] for row in result["local_exponents"]}
    for row in selected:
        beta = local.get(row["level"])
        beta_text = "—" if beta is None else f"{beta:.6f}"
        lines.append(f"| {row['level']} | {row['time']:,} | {row['variance']:.9g} | "
                     f"{row['relative_variance_standard_error']:.3%} | {beta_text} |")
    lines += ["", "## Reading", "",
              "A stable asymptotic power law would make the local exponents settle. Persistent",
              "level-to-level motion instead indicates discrete-scale oscillation or multifractal",
              "transport. Statistical error bars quantify only momentum quadrature, not finite-level",
              "bias. Direct position-space simulation supplies an independent check through level 12.", ""]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-level", type=int, default=24,
                        help="largest time is 2^max-level (default: 24)")
    parser.add_argument("--samples", type=int, default=65536)
    parser.add_argument("--seed", type=int, default=193)
    parser.add_argument("--checkpoint-interval", type=int, default=1024)
    parser.add_argument("--checkpoint", default="logs/quantum-walk-rg.ckpt.json")
    parser.add_argument("--log", default="logs/quantum-walk-rg.log")
    parser.add_argument("--output", default="results/quantum-walk-rg.json")
    parser.add_argument("--report", default="physics/QUANTUM-WALK-RG-RESULTS.md")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_level < 4 or args.samples < 2 or args.checkpoint_interval < 1:
        raise SystemExit("need max level >=4, samples >=2, and checkpoint interval >=1")
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parameters = {"max_level": args.max_level, "samples": args.samples, "seed": args.seed,
                  "checkpoint_interval": args.checkpoint_interval}
    identity = {"version": VERSION, "source_sha256": source_hash, "parameters": parameters}
    checkpoint = Path(args.checkpoint)
    logger = Logger(args.log)
    completed, sums, resumed = 0, empty_sums(args.max_level + 1), False
    if checkpoint.exists():
        try:
            prior = json.loads(checkpoint.read_text())
            if prior.get("identity") == identity:
                completed, sums, resumed = prior["completed_samples"], prior["sums"], True
            else:
                logger.emit("checkpoint_rejected", checkpoint=str(checkpoint), reason="identity mismatch")
        except Exception as error:
            logger.emit("checkpoint_rejected", checkpoint=str(checkpoint), reason=str(error))
    logger.emit("start", parameters=parameters, source_sha256=source_hash, resumed=resumed,
                completed_samples=completed, cpu_workers=1, checkpoint=str(checkpoint))
    started, resumed_at = time.monotonic(), completed
    while completed < args.samples and not STOP_REQUESTED:
        values, error = sample_levels(completed, args.seed, args.max_level)
        add_sample(sums, values, error)
        completed += 1
        if completed % args.checkpoint_interval == 0:
            atomic_json(checkpoint, {"identity": identity, "completed_samples": completed, "sums": sums})
            elapsed = time.monotonic() - started
            rate = (completed - resumed_at) / elapsed if elapsed else 0.0
            logger.emit("progress", completed_samples=completed, total_samples=args.samples,
                        sample_rate=rate, elapsed_seconds=elapsed,
                        estimated_remaining_seconds=(args.samples - completed) / rate if rate else None,
                        checkpoint=str(checkpoint))
    atomic_json(checkpoint, {"identity": identity, "completed_samples": completed, "sums": sums})
    if STOP_REQUESTED:
        logger.emit("interrupted", completed_samples=completed, checkpoint=str(checkpoint))
        return 130
    records = records_from_sums(sums, completed)
    fit_start = max(8, args.max_level - 7)
    result = {"status": "finite Monte Carlo integration of exact dyadic recursion",
              "generated_at": utc_now(), "source_sha256": source_hash, "parameters": parameters,
              "recursion": "B[r+1,a]=B[r,a+1 mod 4] B[r,a]",
              "records": records, "local_exponents": local_exponents(records),
              "late_variance_fit": fit_loglog(records, fit_start),
              "maximum_sampled_unitarity_error": sums["maximum_unitarity_error"]}
    atomic_json(args.output, result)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(markdown_report(result))
    logger.emit("complete", elapsed_seconds=time.monotonic() - started, output=args.output,
                report=args.report, maximum_unitarity_error=sums["maximum_unitarity_error"],
                late_variance_exponent=result["late_variance_fit"]["exponent"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
