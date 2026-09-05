#!/usr/bin/env python3
"""Exact audit of unit-step menu sizes for periodic signed Gaussian rules.

For a periodic sign word epsilon, the state change at n depends only on the
number k of trailing 1 bits.  The sequence of changes is itself periodic
modulo 4 after at most four sign periods, so this audit is finite and exact;
it does not infer an infinite claim from a sampled walk prefix.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
# Stijn Cambie's offsets, written as integer pairs.
OFFSETS = ((0, 0), (-1, 0), (-1, 1), (0, -1))


def patterns(period: int):
    for mask in range(1 << period):
        yield "".join("-" if mask & (1 << (period - 1 - j)) else "+" for j in range(period))


def signs(pattern: str) -> tuple[int, ...]:
    if not pattern or any(ch not in "+-" for ch in pattern):
        raise ValueError("pattern must be a nonempty +/- word")
    return tuple(1 if ch == "+" else -1 for ch in pattern)


def exact_changes(pattern: str) -> tuple[int, ...]:
    """Return every possible state change sigma(n+1)-sigma(n), modulo 4."""
    epsilon = signs(pattern)
    prefix_sum = 0
    changes: set[int] = set()
    # If E is one-period's sign sum, delta_(k+p)=delta_k-E (mod 4).
    # Four periods therefore include the complete orbit for every residue k mod p.
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


def atomic_json_write(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", type=int, default=8, help="enumerate all sign words of this period (default: 8)")
    parser.add_argument("--output", type=Path, default=Path("results/signed-gaussian-unit-step-audit.json"))
    args = parser.parse_args()
    if args.period < 1 or args.period > 20:
        parser.error("--period must be between 1 and 20")

    rows = []
    histogram: Counter[int] = Counter()
    for index, pattern in enumerate(patterns(args.period)):
        menu = step_menu(pattern)
        row = {
            "index": index,
            "pattern": pattern,
            "state_changes_mod_4": list(exact_changes(pattern)),
            "transition_pair_count": len(transition_pairs(pattern)),
            "distinct_step_count": len(menu),
        }
        rows.append(row)
        histogram[len(menu)] += 1

    minimum = min(row["distinct_step_count"] for row in rows)
    minimizers = [row for row in rows if row["distinct_step_count"] == minimum]
    for row in minimizers:
        row["menu"] = [
            {"vector": list(vector), "state_pairs": [list(pair) for pair in pairs_]}
            for vector, pairs_ in sorted(step_menu(row["pattern"]).items())
        ]

    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "exact trailing-ones state-change orbit; no sampled-prefix inference",
        "period": args.period,
        "patterns_checked": len(rows),
        "offsets": [list(c) for c in OFFSETS],
        "minimum_distinct_steps": minimum,
        "minimizers": minimizers,
        "step_count_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "code_sha256": code_hash,
    }
    atomic_json_write(args.output, payload)
    print(f"checked={len(rows)} period={args.period} minimum={minimum}")
    print("minimizers=" + ", ".join(f"g{r['index']}:{r['pattern']}" for r in minimizers))
    print(f"histogram={dict(sorted(histogram.items()))}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
