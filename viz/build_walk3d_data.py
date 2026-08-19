#!/usr/bin/env python3
"""Pack the exact 500,000-step Hilbert artifact for the browser viewer.

The source JSONL stores one exact integer vertex per line. The browser payload
stores the first vertex, the 16 realized step vectors, and two 4-bit step IDs
per byte. Rebuilding is deterministic and writes the output atomically.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "hilbert-193-500k.jsonl"
DEFAULT_OUTPUT = ROOT / "viz" / "walk3d-data.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_vertices(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for expected, raw in enumerate(stream):
            digest.update(raw)
            row = json.loads(raw)
            if row["i"] != expected:
                raise ValueError(f"row {expected}: stored index is {row['i']}")
            yield (row["x"], row["y"], row["z"]), digest


def main() -> int:
    args = parse_args()
    rows = load_vertices(args.source)
    try:
        start, hasher = next(rows)
    except StopIteration as exc:
        raise ValueError("source artifact is empty") from exc

    steps: list[tuple[int, int, int]] = []
    previous = start
    final = start
    for point, hasher in rows:
        step = tuple(point[axis] - previous[axis] for axis in range(3))
        if step[2] <= 0:
            raise ValueError(f"height failed to increase at step {len(steps)}")
        steps.append(step)
        previous = point
        final = point

    menu = sorted(set(steps))
    if len(menu) != 16:
        raise ValueError(f"expected 16 realized vectors, found {len(menu)}")
    menu_id = {step: index for index, step in enumerate(menu)}
    packed = bytearray((len(steps) + 1) // 2)
    counts = Counter()
    for index, step in enumerate(steps):
        identifier = menu_id[step]
        counts[identifier] += 1
        if index % 2 == 0:
            packed[index // 2] = identifier << 4
        else:
            packed[index // 2] |= identifier

    payload = {
        "version": 1,
        "encoding": "two 4-bit menu indices per byte; even step in high nibble",
        "source": args.source.name,
        "sha256": hasher.hexdigest(),
        "vertices": len(steps) + 1,
        "steps": len(steps),
        "start": start,
        "end": final,
        "menu": menu,
        "counts": [counts[index] for index in range(len(menu))],
        "packed": base64.b64encode(packed).decode("ascii"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    os.replace(temporary, args.output)
    print(
        f"packed {payload['steps']:,} steps / {payload['vertices']:,} vertices; "
        f"menu={len(menu)}; payload={args.output.stat().st_size:,} bytes; "
        f"sha256={payload['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
