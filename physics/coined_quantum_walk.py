#!/usr/bin/env python3
"""Explore Gaussian digit-sum phases in a one-dimensional coined quantum walk.

This is an exploratory finite simulation, not a consequence of the Erdős 193
no-collinearity theorem.  The default run compares several embeddings and
controls through 4096 unitary time steps.  Runs use one process, write durable
JSONL progress, checkpoint completed models atomically, and checkpoint an
in-progress wavefunction with pickle.  Only load checkpoints you generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import signal
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
SQRT2_INV = 1 / math.sqrt(2)
UNITS = (1 + 0j, 1j, -1 + 0j, -1j)
MASK64 = (1 << 64) - 1
STOP_REQUESTED = False

MODELS = (
    "homogeneous",
    "gaussian_time_phase",
    "periodic_time_phase",
    "thue_morse_time_phase",
    "random_time_phase",
    "gaussian_time_axis",
    "gaussian_space_phase",
    "gaussian_space_shifted_phase",
    "periodic_space_phase",
    "thue_morse_space_phase",
    "random_space_phase",
    "gaussian_spacetime_phase",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def request_stop(_signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def atomic_bytes(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


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


def zigzag(x):
    return 2 * x if x >= 0 else -2 * x - 1


def phase_alpha(model, t, x, seed):
    if model in ("homogeneous", "gaussian_time_axis"):
        return 0 if model == "homogeneous" else t.bit_count() & 3
    if model == "gaussian_time_phase":
        return t.bit_count() & 3
    if model == "periodic_time_phase":
        return t & 3
    if model == "thue_morse_time_phase":
        return 2 * (t.bit_count() & 1)
    if model == "random_time_phase":
        return splitmix64(seed + t) & 3
    spatial_index = zigzag(x)
    spatial = spatial_index.bit_count() & 3
    if model == "gaussian_space_phase":
        return spatial
    if model == "gaussian_space_shifted_phase":
        return (spatial_index + seed).bit_count() & 3
    if model == "periodic_space_phase":
        return spatial_index & 3
    if model == "thue_morse_space_phase":
        return 2 * (spatial_index.bit_count() & 1)
    if model == "random_space_phase":
        return splitmix64(seed + spatial_index) & 3
    if model == "gaussian_spacetime_phase":
        return (spatial + t.bit_count()) & 3
    raise ValueError(f"unknown model {model}")


def observation_times(steps):
    values = {0, 1, 2, 4, 8, 16, 32, 64}
    power = 128
    while power <= steps:
        values.add(power)
        power *= 2
    # Additional late-time points make scaling fits less dependent on powers of two.
    stride = max(1, steps // 16)
    values.update(range(stride, steps + 1, stride))
    values.add(steps)
    return values


def metrics(left, right, center, t):
    lo, hi = center - t, center + t
    norm = mean = second = ipr = entropy = 0.0
    rho_ll = rho_rr = 0.0
    rho_lr = 0j
    return_probability = 0.0
    peak_probability = -1.0
    peak_position = 0
    distribution = []
    for index in range(lo, hi + 1, 2):
        l, r = left[index], right[index]
        probability = abs(l) ** 2 + abs(r) ** 2
        x = index - center
        norm += probability
        mean += x * probability
        second += x * x * probability
        ipr += probability * probability
        if probability > 0:
            entropy -= probability * math.log(probability)
        rho_ll += abs(l) ** 2
        rho_rr += abs(r) ** 2
        rho_lr += l * r.conjugate()
        if x == 0:
            return_probability = probability
        if probability > peak_probability:
            peak_probability, peak_position = probability, x
        if t > 0 and probability > 1e-15:
            distribution.append([x, probability])
    mean /= norm
    variance = second / norm - mean * mean
    discriminant = math.sqrt(max(0.0, (rho_ll - rho_rr) ** 2 + 4 * abs(rho_lr) ** 2)) / norm
    eigenvalues = ((1 + discriminant) / 2, (1 - discriminant) / 2)
    entanglement = -sum(value * math.log(value, 2) for value in eigenvalues if value > 0)
    return {"time": t, "norm": norm, "mean": mean, "variance": variance,
            "standard_deviation": math.sqrt(max(0.0, variance)),
            "variance_over_t2": variance / (t * t) if t else None,
            "ipr": ipr / (norm * norm), "participation_ratio": norm * norm / ipr,
            "spatial_entropy_nats": entropy / norm + math.log(norm),
            "coin_position_entanglement_bits": entanglement,
            "return_probability": return_probability / norm,
            "peak_position": peak_position, "peak_probability": peak_probability / norm,
            "distribution": distribution if t > 0 else [[0, 1.0]]}


def fit_loglog(records, key, minimum_time):
    points = [(math.log(row["time"]), math.log(row[key])) for row in records
              if row["time"] >= minimum_time and row[key] > 0]
    if len(points) < 2:
        return {"exponent": None, "fit_points": len(points)}
    xbar = sum(x for x, _ in points) / len(points)
    ybar = sum(y for _, y in points) / len(points)
    denominator = sum((x - xbar) ** 2 for x, _ in points)
    slope = sum((x - xbar) * (y - ybar) for x, y in points) / denominator
    intercept = ybar - slope * xbar
    return {"exponent": slope, "prefactor": math.exp(intercept), "fit_points": len(points),
            "minimum_time": minimum_time}


def checkpoint_wavefunction(path, identity, model, t, left, right, records):
    state = {"identity": identity, "model": model, "time": t, "left": left,
             "right": right, "records": records}
    atomic_bytes(path, pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))


def load_wavefunction(path, identity, model):
    path = Path(path)
    if not path.exists():
        return None
    try:
        with path.open("rb") as handle:
            state = pickle.load(handle)
    except Exception:
        return None
    if state.get("identity") != identity or state.get("model") != model:
        return None
    return state


def simulate_model(model, args, identity, logger):
    size = 2 * args.steps + 3
    center = args.steps + 1
    wave_path = Path(args.wave_checkpoint)
    state = load_wavefunction(wave_path, identity, model)
    if state:
        left, right = state["left"], state["right"]
        records, start_t = state["records"], state["time"]
        logger.emit("model_resume", model=model, completed_steps=start_t,
                    wave_checkpoint=str(wave_path))
    else:
        left, right = [0j] * size, [0j] * size
        # This coin state makes the homogeneous Hadamard walk reflection symmetric.
        left[center] = SQRT2_INV
        right[center] = 1j * SQRT2_INV
        records, start_t = [metrics(left, right, center, 0)], 0
    next_left, next_right = [0j] * size, [0j] * size
    observe = observation_times(args.steps)
    started = time.monotonic()
    resumed_at = start_t
    for t in range(start_t, args.steps):
        lo, hi = center - t, center + t
        next_left[hi + 1] = 0j
        next_right[lo - 1] = 0j
        temporal_alpha = phase_alpha(model, t, 0, args.seed) if "space" not in model else None
        for index in range(lo, hi + 1, 2):
            l, r = left[index], right[index]
            x = index - center
            alpha = temporal_alpha if temporal_alpha is not None else phase_alpha(model, t, x, args.seed)
            u = UNITS[alpha]
            if model == "gaussian_time_axis":
                # D(u) H D(conj(u)): rotate the Hadamard reflection axis.
                out_l = (l + u.conjugate() * r) * SQRT2_INV
                out_r = (u * l - r) * SQRT2_INV
            else:
                # D(u) H: u is a relative, not global, phase.
                out_l = (l + r) * SQRT2_INV
                out_r = u * (l - r) * SQRT2_INV
            next_left[index - 1] = out_l
            next_right[index + 1] = out_r
        left, next_left = next_left, left
        right, next_right = next_right, right
        completed = t + 1
        if completed in observe:
            records.append(metrics(left, right, center, completed))
        if completed % args.checkpoint_interval == 0 or STOP_REQUESTED:
            checkpoint_wavefunction(wave_path, identity, model, completed, left, right, records)
            elapsed = time.monotonic() - started
            done = completed - resumed_at
            rate = done / elapsed if elapsed else 0.0
            remaining = (args.steps - completed) / rate if rate else None
            logger.emit("model_progress", model=model, completed_steps=completed,
                        total_steps=args.steps, elapsed_seconds=elapsed,
                        step_rate=rate, estimated_remaining_seconds=remaining,
                        wave_checkpoint=str(wave_path))
        if STOP_REQUESTED:
            return None
    final = records[-1]
    if final["time"] != args.steps:
        final = metrics(left, right, center, args.steps)
        records.append(final)
    maximum_norm_error = max(abs(row["norm"] - 1) for row in records)
    compact_records = []
    for row in records:
        compact = dict(row)
        if row["time"] != args.steps:
            compact.pop("distribution")
        compact_records.append(compact)
    minimum_fit_time = max(64, args.steps // 8)
    result = {"model": model, "coin_convention":
              "D(i^alpha) H" if model != "gaussian_time_axis" else "D(i^alpha) H D(i^-alpha)",
              "records": compact_records,
              "variance_fit": fit_loglog(records, "variance", minimum_fit_time),
              "participation_fit": fit_loglog(records, "participation_ratio", minimum_fit_time),
              "maximum_observed_norm_error": maximum_norm_error}
    if wave_path.exists():
        wave_path.unlink()
    logger.emit("model_complete", model=model,
                elapsed_seconds=time.monotonic() - started,
                variance_exponent=result["variance_fit"]["exponent"],
                final_variance=final["variance"],
                final_return_probability=final["return_probability"],
                maximum_norm_error=maximum_norm_error)
    return result


def distribution_dict(model_result):
    return dict(model_result["records"][-1]["distribution"])


def jensen_shannon(left, right):
    keys = set(left) | set(right)
    divergence = 0.0
    for key in keys:
        p, q = left.get(key, 0.0), right.get(key, 0.0)
        midpoint = (p + q) / 2
        if p:
            divergence += 0.5 * p * math.log(p / midpoint, 2)
        if q:
            divergence += 0.5 * q * math.log(q / midpoint, 2)
    return divergence


def comparisons(results):
    by_name = {result["model"]: result for result in results}
    target = distribution_dict(by_name["gaussian_time_phase"])
    rows = []
    for name, result in by_name.items():
        rows.append({"model": name,
                     "final_distribution_js_divergence_from_gaussian_time_bits":
                     jensen_shannon(target, distribution_dict(result))})
    return rows


def markdown_report(artifact):
    rows = []
    for model in artifact["models"]:
        final = model["records"][-1]
        rows.append((model["model"], model["variance_fit"]["exponent"],
                     final["variance_over_t2"], final["participation_ratio"],
                     final["return_probability"], final["coin_position_entanglement_bits"]))
    lines = [
        "# Coined quantum-walk experiment with Gaussian digit-sum phases", "",
        "> **Status:** exploratory finite simulation. This is one chosen quantum embedding; it is",
        "> not implied uniquely by the Erdős 193 theorem and establishes no quantum advantage.", "",
        "## Model", "",
        "At time `t`, a Hadamard coin is given relative phase",
        "`u_t=i^popcount(t)` and then the left/right components shift by one lattice site.",
        "Controls replace this sequence with homogeneous, period-four, binary Thue–Morse,",
        "or seeded random phases. Additional variants rotate the coin axis or put the phase",
        "in space and space–time. Spatial sequences use the two-sided index",
        "`zigzag(x)=2x` for `x>=0` and `-2x-1` otherwise; one control shifts that index by",
        "the seed. The initial state is `(L+iR)/sqrt(2)` at the origin.", "",
        f"Run parameters: `{artifact['parameters']}`", "",
        "## Results", "",
        "The exponent `beta` is fitted from `variance ~ time^beta` over the final eighth of",
        "the run onward. Ballistic, diffusive, and localized reference values are 2, 1, and 0.", "",
        "| model | beta | variance/t² | participation | P(origin) | coin-position entanglement |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, beta, ballisticity, participation, return_p, entanglement in rows:
        lines.append(f"| `{name}` | {beta:.6f} | {ballisticity:.6g} | {participation:.6g} | "
                     f"{return_p:.6g} | {entanglement:.6f} |")
    target = next(row for row in rows if row[0] == "gaussian_time_phase")
    baseline = next(row for row in rows if row[0] == "homogeneous")
    spatial = next(row for row in rows if row[0] == "gaussian_space_phase")
    lines += ["", "## Automated reading", "",
              f"- Gaussian time modulation has `beta={target[1]:.4f}`, versus",
              f"  `beta={baseline[1]:.4f}` for the homogeneous walk.",
              f"- Its final ballistic coefficient `variance/t²={target[2]:.6g}` should be",
              "  checked across larger powers of two before assigning an asymptotic regime.",
              f"- The spatial digit-sum phase has `beta={spatial[1]:.4f}`. A value well below",
              "  two would identify deterministic suppression of ballistic transport, but finite",
              "  runs alone cannot distinguish localization from a long crossover.", "",
              "## Interpretation limits", "",
              "A time-only coin remains translation invariant and is not a disordered material.",
              "The random control is one deterministic seed, and fitted exponents are effective",
              "finite-time slopes. A promising signal requires size scaling, multiple random",
              "controls, spectral analysis of the unitary operator, and preferably an analytic",
              "renormalization argument. Full dyadic records and final distributions are in JSON.", ""]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=193)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--checkpoint-interval", type=int, default=256,
                        help="wavefunction checkpoint interval within each model")
    parser.add_argument("--checkpoint", default="logs/coined-quantum-walk.ckpt.json")
    parser.add_argument("--wave-checkpoint", default="logs/coined-quantum-walk.wave.pkl")
    parser.add_argument("--log", default="logs/coined-quantum-walk.log")
    parser.add_argument("--output", default="results/coined-quantum-walk.json")
    parser.add_argument("--report", default="physics/QUANTUM-WALK-RESULTS.md")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.steps < 64 or args.checkpoint_interval < 1:
        raise SystemExit("need --steps >= 64 and --checkpoint-interval >= 1")
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parameters = {"steps": args.steps, "seed": args.seed, "models": args.models,
                  "checkpoint_interval": args.checkpoint_interval}
    identity = {"version": VERSION, "source_sha256": source_hash, "parameters": parameters}
    logger = Logger(args.log)
    checkpoint_path = Path(args.checkpoint)
    completed = []
    if checkpoint_path.exists():
        try:
            prior = json.loads(checkpoint_path.read_text())
            if prior.get("identity") == identity:
                completed = prior["completed_models"]
            else:
                logger.emit("checkpoint_rejected", checkpoint=str(checkpoint_path),
                            reason="identity mismatch")
        except Exception as error:
            logger.emit("checkpoint_rejected", checkpoint=str(checkpoint_path), reason=str(error))
    done_names = {row["model"] for row in completed}
    logger.emit("start", parameters=parameters, source_sha256=source_hash,
                completed_models=sorted(done_names), cpu_workers=1,
                checkpoint=str(checkpoint_path), wave_checkpoint=args.wave_checkpoint)
    started = time.monotonic()
    for number, model in enumerate(args.models, 1):
        if model in done_names:
            logger.emit("model_skipped", model=model, reason="validated completed checkpoint")
            continue
        logger.emit("model_start", model=model, model_number=number, total_models=len(args.models))
        result = simulate_model(model, args, identity, logger)
        if result is None:
            logger.emit("interrupted", model=model, elapsed_seconds=time.monotonic() - started,
                        checkpoint=str(checkpoint_path), wave_checkpoint=args.wave_checkpoint)
            return 130
        completed.append(result)
        done_names.add(model)
        atomic_json(checkpoint_path, {"identity": identity, "completed_models": completed})
    ordered = [next(row for row in completed if row["model"] == name) for name in args.models]
    artifact = {"status": "exploratory finite quantum simulation", "generated_at": utc_now(),
                "source_sha256": source_hash, "parameters": parameters, "models": ordered,
                "comparisons": comparisons(ordered)}
    atomic_json(args.output, artifact)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown_report(artifact))
    logger.emit("complete", elapsed_seconds=time.monotonic() - started,
                output=args.output, report=args.report, models=len(ordered))
    return 0


if __name__ == "__main__":
    sys.exit(main())
