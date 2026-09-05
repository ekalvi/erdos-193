#!/usr/bin/env python3
"""Exact, resumable audit of periodic signed-Gaussian unit-step menus.

For a periodic sign word epsilon, the state change at n depends only on the
number k of trailing 1 bits. The change sequence is periodic modulo 4 after at
most four sign periods, so the calculation is exact rather than a sampled-walk
extrapolation. Large runs stream rows, checkpoint progress, and append a JSONL
run log. A compatible checkpoint is resumed automatically.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time

DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
OFFSETS = ((0, 0), (-1, 0), (-1, 1), (0, -1))
SCHEMA_VERSION = 2
STOP_REQUESTED = False


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pattern_for(mask: int, period: int) -> str:
    return "".join("-" if mask & (1 << (period - 1 - j)) else "+" for j in range(period))


def signs(pattern: str) -> tuple[int, ...]:
    if not pattern or any(ch not in "+-" for ch in pattern):
        raise ValueError("pattern must be a nonempty +/- word")
    return tuple(1 if ch == "+" else -1 for ch in pattern)


def exact_changes(pattern: str) -> tuple[int, ...]:
    """Return every possible state change sigma(n+1)-sigma(n), modulo 4."""
    epsilon = signs(pattern)
    prefix_sum = 0
    changes: set[int] = set()
    # If E is one period's sign sum, delta_(k+p)=delta_k-E (mod 4).
    # Four periods include the complete orbit for every residue k mod p.
    for k in range(4 * len(epsilon)):
        changes.add((epsilon[k % len(epsilon)] - prefix_sum) % 4)
        prefix_sum += epsilon[k % len(epsilon)]
    return tuple(sorted(changes))


def transition_pairs(pattern: str) -> tuple[tuple[int, int], ...]:
    return tuple(
        (state, (state + change) % 4)
        for change in exact_changes(pattern)
        for state in range(4)
    )


def step_menu(pattern: str) -> dict[tuple[int, int, int], list[tuple[int, int]]]:
    menu: dict[tuple[int, int, int], list[tuple[int, int]]] = {}
    for start, end in transition_pairs(pattern):
        dx = 2 * DIRECTIONS[start][0] + OFFSETS[end][0] - OFFSETS[start][0]
        dy = 2 * DIRECTIONS[start][1] + OFFSETS[end][1] - OFFSETS[start][1]
        vector = (dx, dy, 4 + end - start)
        menu.setdefault(vector, []).append((start, end))
    return menu


def row_for(index: int, period: int) -> dict:
    pattern = pattern_for(index, period)
    pairs = transition_pairs(pattern)
    return {
        "index": index,
        "pattern": pattern,
        "state_changes_mod_4": list(exact_changes(pattern)),
        "transition_pair_count": len(pairs),
        "distinct_step_count": len(step_menu(pattern)),
    }


def atomic_json_write(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def append_log(path: Path, event: str, **fields: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": now(), "event": event, **fields}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def checkpoint_payload(*, code_hash: str, period: int, total: int, phase: str,
                       next_index: int, histogram: dict[int, int], minimum: int | None,
                       minimizers: list[dict], started_at: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "code_sha256": code_hash,
        "period": period,
        "total": total,
        "offsets": [list(c) for c in OFFSETS],
        "phase": phase,
        "next_index": next_index,
        "histogram": {str(k): v for k, v in sorted(histogram.items())},
        "minimum": minimum,
        "minimizers": minimizers,
        "started_at": started_at,
        "updated_at": now(),
    }


def handle_signal(_signum, _frame) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", type=int, default=8, help="sign-word period (default: 8)")
    parser.add_argument("--output", type=Path, default=Path("results/signed-gaussian-unit-step-audit.json"))
    parser.add_argument("--checkpoint", type=Path, help="checkpoint path (default: logs/...period-P.checkpoint.json)")
    parser.add_argument("--log", type=Path, help="JSONL log path (default: logs/...period-P.log)")
    parser.add_argument("--progress-every", type=int, default=10_000, help="checkpoint/log interval")
    args = parser.parse_args()
    if args.period < 1 or args.period > 20:
        parser.error("--period must be between 1 and 20")
    if args.progress_every < 1:
        parser.error("--progress-every must be positive")

    total = 1 << args.period
    checkpoint = args.checkpoint or Path(f"logs/signed-gaussian-unit-step-period-{args.period}.checkpoint.json")
    log = args.log or Path(f"logs/signed-gaussian-unit-step-period-{args.period}.log")
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    started_at = now()
    phase = "measure"
    next_index = 0
    histogram: dict[int, int] = {}
    minimum: int | None = None
    minimizers: list[dict] = []

    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
        identity = (saved.get("schema_version"), saved.get("code_sha256"), saved.get("period"),
                    saved.get("total"), saved.get("offsets"))
        expected = (SCHEMA_VERSION, code_hash, args.period, total, [list(c) for c in OFFSETS])
        if identity != expected:
            raise SystemExit(f"incompatible checkpoint: {checkpoint}")
        phase = saved["phase"]
        next_index = saved["next_index"]
        histogram = {int(k): v for k, v in saved["histogram"].items()}
        minimum = saved["minimum"]
        minimizers = saved["minimizers"]
        started_at = saved["started_at"]
        append_log(log, "resume", period=args.period, phase=phase, completed=next_index,
                   total=total, checkpoint=str(checkpoint), code_sha256=code_hash)
    else:
        append_log(log, "start", period=args.period, total=total, checkpoint=str(checkpoint),
                   output=str(args.output), progress_every=args.progress_every, code_sha256=code_hash,
                   resource_threads=1)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    run_started = time.monotonic()
    run_initial = next_index

    while phase != "complete":
        for index in range(next_index, total):
            row = row_for(index, args.period)
            count = row["distinct_step_count"]
            if phase == "measure":
                histogram[count] = histogram.get(count, 0) + 1
                minimum = count if minimum is None else min(minimum, count)
            elif count == minimum:
                minimizers.append(row)
            next_index = index + 1

            if next_index % args.progress_every == 0 or STOP_REQUESTED:
                elapsed = max(time.monotonic() - run_started, 1e-9)
                throughput = (next_index - run_initial) / elapsed
                remaining = total - next_index
                eta = remaining / throughput if throughput > 0 else None
                state = checkpoint_payload(
                    code_hash=code_hash, period=args.period, total=total, phase=phase,
                    next_index=next_index, histogram=histogram, minimum=minimum,
                    minimizers=minimizers, started_at=started_at,
                )
                atomic_json_write(checkpoint, state)
                append_log(log, "progress", phase=phase, completed=next_index, total=total,
                           throughput_per_second=throughput, elapsed_seconds=elapsed,
                           eta_seconds=eta, checkpoint=str(checkpoint))
            if STOP_REQUESTED:
                append_log(log, "interrupted", phase=phase, completed=next_index, total=total)
                print(f"interrupted phase={phase} completed={next_index}/{total} checkpoint={checkpoint}", flush=True)
                return 130

        if phase == "measure":
            phase = "collect"
            next_index = 0
            run_started = time.monotonic()
            run_initial = 0
        else:
            phase = "complete"
        atomic_json_write(checkpoint, checkpoint_payload(
            code_hash=code_hash, period=args.period, total=total, phase=phase,
            next_index=next_index, histogram=histogram, minimum=minimum,
            minimizers=minimizers, started_at=started_at,
        ))
        append_log(log, "phase", phase=phase, completed=next_index, total=total,
                   checkpoint=str(checkpoint))

    for row in minimizers:
        row["menu"] = [
            {"vector": list(vector), "state_pairs": [list(pair) for pair in pairs_]}
            for vector, pairs_ in sorted(step_menu(row["pattern"]).items())
        ]
    payload = {
        "schema_version": 1,
        "generated_at": now(),
        "method": "exact trailing-ones state-change orbit; no sampled-prefix inference",
        "period": args.period,
        "patterns_checked": total,
        "offsets": [list(c) for c in OFFSETS],
        "minimum_distinct_steps": minimum,
        "minimizers": minimizers,
        "step_count_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "code_sha256": code_hash,
    }
    atomic_json_write(args.output, payload)
    append_log(log, "complete", period=args.period, total=total, minimum=minimum,
               minimizer_count=len(minimizers), output=str(args.output), checkpoint=str(checkpoint))
    print(f"checked={total} period={args.period} minimum={minimum}")
    print("minimizers=" + ", ".join(f"g{r['index']}:{r['pattern']}" for r in minimizers))
    print(f"histogram={dict(sorted(histogram.items()))}")
    print(f"output={args.output} checkpoint={checkpoint} log={log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
