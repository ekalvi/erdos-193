#!/usr/bin/env python3
"""Exact finite obstructions to small standard-basis encodings.

The default finite run exhausts ternary eight-letter words up to alphabet
permutation, then tests every surjective coding of the eight g85 transitions
onto four or five letters. A collision is an exact counterexample; survival is
ONLY finite evidence. No positive infinite claim is inferred from a prefix.

Runs use one core, save an atomic checkpoint after each task, and append flushed
JSONL progress. Repeating an identical command resumes validated completed tasks.
SIGINT/SIGTERM stop at the next completed task. Logs/checkpoints are separate
from the final JSON artifact; --state-dir defaults to an ignored directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import reduce
import hashlib
import itertools
import json
from math import gcd
import os
from pathlib import Path
import signal
import time

PAIRS = ((0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3), (2, 0), (3, 1))
STOP = False


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def log_event(path, event, **values):
    line = json.dumps(dict(timestamp=now(), event=event, **values), sort_keys=True)
    with path.open("a") as stream:
        stream.write(line + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    if event != "task":
        print(line, flush=True)


def partitions(n, k):
    """All restricted-growth strings using exactly k nonempty classes."""
    def visit(prefix, maximum):
        if len(prefix) == n:
            if maximum == k - 1:
                yield tuple(prefix)
            return
        for value in range(min(k - 1, maximum + 1) + 1):
            yield from visit(prefix + [value], max(value, maximum))
    yield from visit([0], 0)


def alternating_word(count):
    def state(n):
        total, place = 0, 0
        while n:
            total += (1 if place % 2 == 0 else -1) * (n & 1)
            n >>= 1
            place += 1
        return total % 4
    states = [state(n) for n in range(count + 1)]
    return [PAIRS.index(pair) for pair in zip(states, states[1:])]


def prefix_counts(word, alphabet):
    points = [[0] * alphabet]
    for letter in word:
        point = points[-1].copy()
        point[letter] += 1
        points.append(point)
    return points


def witness(points, a, b, c):
    left = [y - x for x, y in zip(points[a], points[b])]
    right = [y - x for x, y in zip(points[b], points[c])]
    assert all((c - b) * x == (b - a) * y for x, y in zip(left, right))
    return dict(indices=[a, b, c], left_counts=left, right_counts=right,
                left_length=b - a, right_length=c - b)


def first_collision(word, alphabet):
    points = prefix_counts(word, alphabet)
    # Cheap adjacent equal-length check before the all-length geometric check.
    for half in range(1, min(len(word) // 2, 16) + 1):
        for a in range(len(word) - 2 * half + 1):
            b, c = a + half, a + 2 * half
            if all(x + z == 2 * y for x, y, z in zip(points[a], points[b], points[c])):
                return witness(points, a, b, c)
    for a in range(len(word) - 1):
        directions = {}
        for c in range(a + 1, len(word) + 1):
            displacement = tuple(y - x for x, y in zip(points[a], points[c]))
            divisor = reduce(gcd, displacement)
            direction = tuple(x // divisor for x in displacement)
            if direction in directions:
                return witness(points, a, directions[direction], c)
            directions[direction] = c
    return None


def lower_bound():
    # Exhaust the extension tree after quotienting only by alphabet permutations.
    frontier = [(0,)]
    sizes = [1]
    for length in range(2, 9):
        next_frontier = []
        for prefix in frontier:
            for letter in range(min(2, max(prefix) + 1) + 1):
                word = prefix + (letter,)
                if first_collision(word, 3) is None:
                    next_frontier.append(word)
        frontier = next_frontier
        sizes.append(len(frontier))
        if length == 7:
            longest = [list(w) for w in frontier]
    assert not frontier
    # Independent unquotiented check of all 3^8 words.
    histogram = {}
    for word in itertools.product(range(3), repeat=8):
        hit = first_collision(word, 3)
        assert hit is not None
        key = str(hit["left_length"])
        histogram[key] = histogram.get(key, 0) + 1
    return dict(kind="exhaustive_lower_bound", alphabet=3, steps=8,
                words_checked=3 ** 8, canonical_survivors_by_length=sizes,
                canonical_seven_step_examples=longest,
                witness_half_length_histogram=histogram)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=256, help="finite g85 step prefix")
    parser.add_argument("--state-dir", type=Path, default=Path(".checkpoint-unit-step-dimensions"))
    parser.add_argument("--output", type=Path, default=Path("results/unit-step-dimension-probe.json"))
    args = parser.parse_args()
    if not 8 <= args.steps <= 4096:
        parser.error("--steps must be between 8 and 4096 (bounded quadratic probe)")
    args.state_dir.mkdir(parents=True, exist_ok=True)
    checkpoint, log = args.state_dir / "state.json", args.state_dir / "run.jsonl"
    identity = dict(schema=1, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    steps=args.steps, pairs=PAIRS)
    identity = json.loads(json.dumps(identity))
    jobs = [(k, coding) for k in (4, 5) for coding in partitions(8, k)]
    total = 1 + len(jobs)
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        if saved.get("identity") != identity:
            parser.error(f"incompatible checkpoint: {checkpoint}")
        rows = saved["rows"]
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
        if saved.get("rows_sha256") != digest or not 0 <= len(rows) <= total:
            parser.error(f"corrupt checkpoint: {checkpoint}")
    else:
        rows = []

    def save():
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
        atomic_json(checkpoint, dict(identity=identity, rows=rows, rows_sha256=digest))

    def stop(_signum, _frame):
        global STOP
        STOP = True
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, stop)
    initial = len(rows)
    started = time.monotonic()
    log_event(log, "resume" if rows else "start", identity=identity, completed=initial,
              total=total, threads=1, checkpoint=str(checkpoint))
    source = alternating_word(args.steps)
    assert first_collision([ (0, 1, 2, 3, 4, 4, 5, 5)[x] for x in source], 6) is None
    try:
        if not rows:
            rows.append(lower_bound())
            save()
        for k, coding in jobs[len(rows) - 1:]:
            if STOP:
                log_event(log, "interrupted", completed=len(rows), total=total)
                return 130
            hit = first_collision([coding[x] for x in source], k)
            rows.append(dict(alphabet=k, coding=coding, collision=hit))
            save()
            elapsed = max(time.monotonic() - started, 1e-9)
            rate = (len(rows) - initial) / elapsed
            log_event(log, "progress" if len(rows) % 100 == 0 else "task",
                      completed=len(rows), total=total, elapsed_seconds=elapsed,
                      tasks_per_second=rate, eta_seconds=(total - len(rows)) / rate)
        summary = {}
        for k in (4, 5):
            group = [r for r in rows[1:] if r["alphabet"] == k]
            failures = [r for r in group if r["collision"] is not None]
            summary[str(k)] = dict(tested=len(group), refuted=len(failures),
                finite_survivors=[r["coding"] for r in group if r["collision"] is None],
                largest_witness_endpoint=max((r["collision"]["indices"][2] for r in failures), default=None))
        atomic_json(args.output, dict(identity=identity, generated_at=now(),
            lower_bound=rows[0], summary=summary, codings=rows[1:],
            scope="Finite witnesses refute these fixed transition codings, not arbitrary constructions."))
        log_event(log, "complete", completed=total, total=total, summary=summary, output=str(args.output))
    except Exception as exc:
        log_event(log, "error", completed=len(rows), error=repr(exc))
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
