#!/usr/bin/env python3
"""Finite physics diagnostics for the Gaussian walk in the Erdős 193 proof.

The calculation is safely resumable during triple sampling. It writes an atomic
checkpoint and timestamped JSONL log; rerunning with identical parameters
continues from that checkpoint. Results are finite computational observations,
not premises or consequences beyond the proved construction.
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
STOP_REQUESTED = False
MASK64 = (1 << 64) - 1


def utc_now():
    return datetime.now(timezone.utc).isoformat()


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


def request_stop(signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def unit(n):
    return (1, 1j, -1, -1j)[n.bit_count() & 3]


def generate(n):
    points = []
    steps = []
    z_values = []
    z = 0j
    corners = (0j, 1j, -1 + 1j, -1 + 0j)
    for k in range(n):
        alpha = k.bit_count() & 3
        w = 2 * z + corners[alpha]
        points.append((int(w.real), int(w.imag), 4 * k + alpha))
        z_values.append(z)
        steps.append(unit(k))
        z += steps[-1]
    return points, z_values, steps


def dyadic_lags(n):
    values = []
    lag = 1
    while lag <= n // 8:
        values.append(lag)
        lag *= 2
    return values


def linear_fit_loglog(rows, key):
    usable = [(math.log(row["lag"]), math.log(row[key])) for row in rows if row[key] > 0]
    xbar = sum(x for x, _ in usable) / len(usable)
    ybar = sum(y for _, y in usable) / len(usable)
    denominator = sum((x - xbar) ** 2 for x, _ in usable)
    slope = sum((x - xbar) * (y - ybar) for x, y in usable) / denominator
    intercept = ybar - slope * xbar
    return {"exponent": slope, "prefactor": math.exp(intercept), "fit_points": len(usable)}


def transport(points, z_values):
    rows = []
    for lag in dyadic_lags(len(points)):
        count = len(points) - lag
        planar = 0
        spatial = 0
        for k in range(count):
            dz = z_values[k + lag] - z_values[k]
            planar += int(dz.real) ** 2 + int(dz.imag) ** 2
            a, b = points[k], points[k + lag]
            spatial += sum((b[j] - a[j]) ** 2 for j in range(3))
        rows.append({"lag": lag, "samples": count, "planar_msd": planar / count,
                     "lifted_3d_msd": spatial / count})
    return {"dyadic_lags": rows,
            "planar_fit": linear_fit_loglog(rows, "planar_msd"),
            "lifted_3d_fit": linear_fit_loglog(rows, "lifted_3d_msd")}


def autocorrelation(steps, max_lag):
    rows = []
    n = len(steps)
    for lag in range(max_lag + 1):
        total = 0j
        for k in range(n - lag):
            total += steps[k + lag] * steps[k].conjugate()
        value = total / (n - lag)
        rows.append({"lag": lag, "real": value.real, "imag": value.imag,
                     "magnitude": abs(value)})
    return rows


def fft(values):
    """In-place radix-2 FFT, returned in natural frequency order."""
    out = list(values)
    n = len(out)
    if n == 0 or n & (n - 1):
        raise ValueError("FFT length must be a power of two")
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    length = 2
    while length <= n:
        root = cmath.exp(-2j * math.pi / length)
        for start in range(0, n, length):
            factor = 1 + 0j
            half = length // 2
            for offset in range(half):
                even = out[start + offset]
                odd = out[start + offset + half] * factor
                out[start + offset] = even + odd
                out[start + offset + half] = even - odd
                factor *= root
        length *= 2
    return out


def temporal_spectrum(steps):
    n = 1 << (len(steps).bit_length() - 1)
    transformed = fft(steps[:n])
    powers = [abs(value) ** 2 / n for value in transformed]
    total = sum(powers)
    probabilities = [power / total for power in powers if power > 0]
    entropy = -sum(p * math.log(p) for p in probabilities) / math.log(n)
    top = sorted(range(n), key=powers.__getitem__, reverse=True)[:16]
    return {"fft_length": n, "normalization": "|DFT|^2/N",
            "spectral_entropy_normalized": entropy,
            "largest_bins": [{"bin": k, "cycles_per_step": k / n,
                              "power": powers[k], "fraction_of_total": powers[k] / total}
                             for k in top]}


def spatial_structure_factor(points, modulus=1024):
    """Commensurate reciprocal-line scans of S(q)=|sum exp(-iq.P)|^2/N."""
    directions = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1))
    scans = []
    for direction in directions:
        histogram = [0j] * modulus
        for point in points:
            projection = sum(a * b for a, b in zip(direction, point)) % modulus
            histogram[projection] += 1
        amplitudes = fft(histogram)
        powers = [abs(value) ** 2 / len(points) for value in amplitudes]
        # k=0 is the trivial forward-scattering peak and is reported separately.
        top = sorted(range(1, modulus), key=powers.__getitem__, reverse=True)[:12]
        scans.append({"direction": list(direction), "forward_power": powers[0],
                      "largest_nonzero_bins":
                      [{"bin": k, "q_radians": 2 * math.pi * k / modulus,
                        "power": powers[k], "power_per_particle": powers[k] / len(points)}
                       for k in top]})
    parity_counts = [0, 0]
    for x, y, h in points:
        parity_counts[(x + y + h) & 1] += 1
    return {"definition": "S(q)=|sum_j exp(-i q dot P_j)|^2/N",
            "scan_wavevectors": "q=(2*pi*k/modulus)*direction",
            "modulus": modulus, "finite_prefix_only": True,
            "coordinate_sum_parity_counts": parity_counts, "scans": scans}


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def segment_distance_squared(p1, q1, p2, q2):
    """Squared distance between two 3D segments (Ericson's clamp algorithm)."""
    u, v, w = subtract(q1, p1), subtract(q2, p2), subtract(p1, p2)
    a, b, c, d, e = dot(u, u), dot(u, v), dot(v, v), dot(u, w), dot(v, w)
    denominator = a * c - b * b
    small = 1e-15
    s_num, s_den = denominator, denominator
    t_num, t_den = denominator, denominator
    if denominator < small:
        s_num, s_den, t_num, t_den = 0.0, 1.0, float(e), float(c)
    else:
        s_num, t_num = b * e - c * d, a * e - b * d
        if s_num < 0:
            s_num, t_num, t_den = 0.0, float(e), float(c)
        elif s_num > s_den:
            s_num, t_num, t_den = s_den, float(e + b), float(c)
    if t_num < 0:
        t_num = 0.0
        if -d < 0:
            s_num, s_den = 0.0, 1.0
        elif -d > a:
            s_num, s_den = 1.0, 1.0
        else:
            s_num, s_den = float(-d), float(a)
    elif t_num > t_den:
        t_num = t_den
        if -d + b < 0:
            s_num, s_den = 0.0, 1.0
        elif -d + b > a:
            s_num, s_den = 1.0, 1.0
        else:
            s_num, s_den = float(-d + b), float(a)
    sc = 0.0 if abs(s_num) < small else s_num / s_den
    tc = 0.0 if abs(t_num) < small else t_num / t_den
    delta = tuple(wi + sc * ui - tc * vi for wi, ui, vi in zip(w, u, v))
    return dot(delta, delta)


def proximity(points, edge_gap_limit):
    vertex_best = None
    edge_best = None
    vertex_histogram = {}
    max_gap = min(edge_gap_limit, len(points) - 1)
    for gap in range(2, max_gap + 1):
        local_vertex = math.inf
        for i in range(len(points) - gap):
            distance2 = sum((points[i + gap][j] - points[i][j]) ** 2 for j in range(3))
            local_vertex = min(local_vertex, distance2)
            candidate = (distance2, i, i + gap)
            if vertex_best is None or candidate < vertex_best:
                vertex_best = candidate
        vertex_histogram[str(gap)] = local_vertex
        for i in range(len(points) - gap - 1):
            distance2 = segment_distance_squared(points[i], points[i + 1],
                                                 points[i + gap], points[i + gap + 1])
            candidate = (distance2, i, i + gap)
            if edge_best is None or candidate < edge_best:
                edge_best = candidate
    # Height rises by at least one per step. For omitted edge gaps g, vertical
    # separation is at least g-1; report this bound rather than claiming globality.
    omitted_bound = max_gap
    return {"checked_index_gaps": [2, max_gap],
            "minimum_nonconsecutive_vertex": {"distance": math.sqrt(vertex_best[0]),
                                               "indices": list(vertex_best[1:]),
                                               "global_within_prefix":
                                               vertex_best[0] < omitted_bound ** 2},
            "minimum_nonadjacent_edge": {"distance": math.sqrt(edge_best[0]),
                                         "edge_starts": list(edge_best[1:]),
                                         "global_within_prefix":
                                         edge_best[0] < omitted_bound ** 2},
            "omitted_edge_vertical_lower_bound": omitted_bound,
            "minimum_vertex_squared_by_gap": vertex_histogram}


def splitmix64(value):
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return value ^ (value >> 31)


def sampled_triple(sample_id, n, seed):
    values = []
    state = (seed + 3 * sample_id) & MASK64
    for offset in range(3):
        values.append(splitmix64(state + offset) % n)
    if len(set(values)) < 3:
        # Deterministic fallback; its tiny bias is documented in the result.
        values = [(values[0] + q) % n for q in (0, 1, 2)]
    return tuple(sorted(values))


def initial_sampling_state():
    return {"completed": 0, "bins": [0] * 12, "minimum_sine": 1.0,
            "minimum_indices": None, "minimum_angle_degrees": 90.0}


def near_collinearity(points, target, seed, state, checkpoint_path, metadata,
                      logger, checkpoint_interval):
    bounds = [10.0 ** exponent for exponent in range(-10, 1)]
    started = time.monotonic()
    resumed_at = state["completed"]
    while state["completed"] < target and not STOP_REQUESTED:
        sample_id = state["completed"]
        i, j, k = sampled_triple(sample_id, len(points), seed)
        a = subtract(points[j], points[i])
        b = subtract(points[k], points[i])
        cross = (a[1] * b[2] - a[2] * b[1],
                 a[2] * b[0] - a[0] * b[2],
                 a[0] * b[1] - a[1] * b[0])
        sine = math.sqrt(dot(cross, cross) / (dot(a, a) * dot(b, b)))
        bin_index = next((q for q, bound in enumerate(bounds) if sine < bound), len(bounds))
        state["bins"][bin_index] += 1
        if sine < state["minimum_sine"]:
            state["minimum_sine"] = sine
            state["minimum_angle_degrees"] = math.degrees(math.asin(min(1.0, sine)))
            state["minimum_indices"] = [i, j, k]
        state["completed"] += 1
        if state["completed"] % checkpoint_interval == 0:
            atomic_json(checkpoint_path, {**metadata, "sampling": state})
            elapsed = time.monotonic() - started
            done_now = state["completed"] - resumed_at
            rate = done_now / elapsed if elapsed else 0
            remaining = (target - state["completed"]) / rate if rate else None
            logger.emit("sampling_progress", completed=state["completed"], total=target,
                        throughput_per_second=rate, elapsed_seconds=elapsed,
                        estimated_remaining_seconds=remaining,
                        checkpoint=str(checkpoint_path))
    atomic_json(checkpoint_path, {**metadata, "sampling": state})
    labels = ["sin(theta)<1e-10"]
    labels += [f"1e{exponent - 1}<=sin(theta)<1e{exponent}"
               for exponent in range(-9, 1)]
    labels += ["sin(theta)>=1"]
    return {**state, "bin_definition": labels,
            "sampling": "deterministic SplitMix64 index triples; duplicate draws use three consecutive indices"}


def markdown_report(result):
    t = result["transport"]
    s = result["temporal_step_spectrum"]
    p = result["proximity"]
    a = result["near_collinearity"]
    correlation = result["step_autocorrelation"]
    selected = [correlation[q] for q in (0, 1, 2, 3, 4, 8, 16, 32, 64, 128, 256)
                if q < len(correlation)]
    lines = [
        "# Finite physics diagnostics for the Gaussian Erdős 193 walk", "",
        "> **Status:** computational observations on a finite prefix, not a physical model and not",
        "> part of the unconditional proof. “Spectrum” below means the temporal Fourier spectrum",
        "> of planar unit steps, not a spatial material diffraction measurement.", "",
        f"Parameters: `{result['parameters']}`", "",
        "## Main observations", "",
        f"- Planar ensemble MSD log-log exponent: **{t['planar_fit']['exponent']:.6f}**.",
        f"- Lifted 3D MSD exponent: **{t['lifted_3d_fit']['exponent']:.6f}** (height is ballistic).",
        f"- Normalized temporal spectral entropy: **{s['spectral_entropy_normalized']:.6f}**",
        "  (0 is one Fourier bin; 1 is flat power over all bins).",
        f"- Closest checked nonconsecutive vertices: distance **{p['minimum_nonconsecutive_vertex']['distance']:.6g}**",
        f"  at indices `{p['minimum_nonconsecutive_vertex']['indices']}`.",
        f"- Closest checked nonadjacent edges: distance **{p['minimum_nonadjacent_edge']['distance']:.6g}**",
        f"  for edges starting at `{p['minimum_nonadjacent_edge']['edge_starts']}`.",
        f"- Smallest sampled triple angle: **{a['minimum_angle_degrees']:.9g}°**",
        f"  at indices `{a['minimum_indices']}` among {a['completed']:,} sampled triples.", "",
        "## Selected step autocorrelations", "",
        "`C(l)=mean(u[n+l] conjugate(u[n]))`.", "",
        "| lag | Re C | Im C | |C| |", "|---:|---:|---:|---:|",
    ]
    lines += [f"| {r['lag']} | {r['real']:.9g} | {r['imag']:.9g} | {r['magnitude']:.9g} |"
              for r in selected]
    lines += ["", "## Strongest temporal Fourier bins", "",
              "| bin | cycles/step | power fraction |", "|---:|---:|---:|"]
    lines += [f"| {r['bin']} | {r['cycles_per_step']:.9g} | {r['fraction_of_total']:.9g} |"
              for r in s["largest_bins"][:10]]
    under_1e3 = sum(a["bins"][:8]) / a["completed"]
    under_1e2 = sum(a["bins"][:9]) / a["completed"]
    parity = result["spatial_structure_factor"]["coordinate_sum_parity_counts"]
    lines += ["", "## Angular and reciprocal-space diagnostics", "",
              f"- **{under_1e3:.3%}** of sampled triples have angle below about `0.0573°`",
              f"  (`sin(theta)<1e-3`); **{under_1e2:.3%}** are below about `0.573°`.",
              "  Thus exact non-collinearity provides very little angular clearance.",
              "- Finite-prefix scans use `S(q)=|sum_j exp(-i q·P_j)|^2/N` along x, y,",
              "  height, and (1,1,1). The forward peak is separated from nonzero bins.",
              f"- Coordinate-sum parity counts are `{parity}`: every tested point has",
              "  `x+y+h` even. Consequently the (1,1,1) scan has a fully coherent",
              "  `q=pi` peak. This is the exact parity sublattice selection rule, not",
              "  evidence by itself for novel long-range order.", "",
              "## Interpretation limits", "",
              "Exact non-collinearity does not imply robust angular separation: sampled triples can",
              "approach a line. Proximity minima apply to the reported finite prefix; the JSON flags",
              "whether the monotone-height bound makes each minimum prefix-wide. Temporal Fourier",
              "peaks characterize the symbolic time series, while the spatial scans are finite and",
              "commensurate; neither establishes an infinite-volume diffraction measure or a physical",
              "response without a specified coupling. See the JSON artifact for complete tables.", ""]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=131072, help="prefix length (default: 131072)")
    parser.add_argument("--max-correlation-lag", type=int, default=256)
    parser.add_argument("--edge-gap-limit", type=int, default=16)
    parser.add_argument("--triple-samples", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=193)
    parser.add_argument("--checkpoint-interval", type=int, default=100_000)
    parser.add_argument("--checkpoint", default="logs/physics-analysis.ckpt.json")
    parser.add_argument("--log", default="logs/physics-analysis.log")
    parser.add_argument("--output", default="results/physics-analysis.json")
    parser.add_argument("--report", default="physics/RESULTS.md")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.points < 32 or args.max_correlation_lag >= args.points:
        raise SystemExit("need --points >= 32 and correlation lag smaller than prefix")
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parameters = {"points": args.points, "max_correlation_lag": args.max_correlation_lag,
                  "edge_gap_limit": args.edge_gap_limit, "triple_samples": args.triple_samples,
                  "seed": args.seed}
    metadata = {"version": VERSION, "source_sha256": source_hash, "parameters": parameters}
    logger = Logger(args.log)
    state = initial_sampling_state()
    fixed_results = None
    checkpoint = Path(args.checkpoint)
    resumed = False
    if checkpoint.exists():
        prior = json.loads(checkpoint.read_text())
        if {k: prior.get(k) for k in metadata} == metadata:
            state = prior["sampling"]
            fixed_results = prior.get("fixed_results")
            resumed = True
        else:
            logger.emit("checkpoint_rejected", checkpoint=str(checkpoint), reason="metadata mismatch")
    logger.emit("start", parameters=parameters, source_sha256=source_hash, resumed=resumed,
                completed_samples=state["completed"], fixed_stages_resumed=fixed_results is not None,
                checkpoint=str(checkpoint), cpu_workers=1, output=args.output)
    started = time.monotonic()
    points, z_values, steps = generate(args.points)
    if fixed_results is None:
        fixed_results = {
            "transport": transport(points, z_values),
            "step_autocorrelation": autocorrelation(steps, args.max_correlation_lag),
            "temporal_step_spectrum": temporal_spectrum(steps),
            "spatial_structure_factor": spatial_structure_factor(points),
            "proximity": proximity(points, args.edge_gap_limit),
        }
        atomic_json(checkpoint, {**metadata, "fixed_results": fixed_results,
                                 "sampling": state})
        logger.emit("fixed_stages_complete", checkpoint=str(checkpoint))
    result = {"status": "finite computational observation", "generated_at": utc_now(),
              "parameters": parameters, "source_sha256": source_hash, **fixed_results}
    checkpoint_metadata = {**metadata, "fixed_results": fixed_results}
    result["near_collinearity"] = near_collinearity(
        points, args.triple_samples, args.seed, state, checkpoint, checkpoint_metadata,
        logger, args.checkpoint_interval)
    if STOP_REQUESTED:
        logger.emit("interrupted", completed_samples=state["completed"],
                    checkpoint=str(checkpoint), elapsed_seconds=time.monotonic() - started)
        return 130
    atomic_json(args.output, result)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown_report(result))
    logger.emit("complete", elapsed_seconds=time.monotonic() - started,
                output=args.output, report=args.report,
                completed_samples=state["completed"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
