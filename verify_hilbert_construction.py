#!/usr/bin/env python3
"""Independently verify a terminal-steered Hilbert-walk artifact.

This verifier does not import the constructor.  It recomputes selected indices
from digit parities, planar coordinates with the standard iterative d2xy
algorithm, every consecutive step, and the fixed 16-vector menu.  The Lean
module Hilbert193.Construction proves no collinear triple for this exact vertex
function; this program checks that every artifact row is that function.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
STOP = False
MENU = {
    (-5,-1,26),(-4,0,16),(-3,3,14),(-3,5,18),(-2,0,28),(-1,1,18),
    (0,-4,16),(0,4,16),(0,6,20),(1,-3,6),(2,-6,24),(2,0,4),
    (2,2,8),(3,-5,14),(4,-2,12),(4,0,16),
}
CORRECTION = {(0,0): 5, (1,0): 1, (0,1): 13, (1,1): 3}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parity(block: int) -> tuple[int,int]:
    p0 = p3 = 0
    length = max(1, (block.bit_length() + 1) // 2)
    length += length & 1
    for pos in range(length):
        digit = (block >> (2 * pos)) & 3
        p0 ^= digit == 0
        p3 ^= digit == 3
    return p0, p3


def selected_index(block: int) -> int:
    return 16 * block + CORRECTION[parity(block)]


def d2xy(order: int, index: int) -> tuple[int,int]:
    side = 1 << order
    x = y = 0
    t = index
    scale = 1
    while scale < side:
        rx = 1 & (t >> 1)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x, y = scale - 1 - x, scale - 1 - y
            x, y = y, x
        x += scale * rx
        y += scale * ry
        t >>= 2
        scale <<= 1
    return x, y


def expected(block: int) -> tuple[int,int,int]:
    z = selected_index(block)
    raw = max(1, (z.bit_length() + 1) // 2)
    order = raw + (raw & 1)
    x, y = d2xy(order, z)
    return x, y, z


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True) + "\n")
    os.replace(tmp, path)


def log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(f"{now()} {text}\n")
        f.flush()


def main() -> int:
    global STOP
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", nargs="?", type=Path, default=Path("hilbert-193-500k.jsonl"))
    p.add_argument("--steps", type=int, default=500_000)
    p.add_argument("--checkpoint", type=Path, default=Path("logs/hilbert-193-500k.verify.ckpt.json"))
    p.add_argument("--log", type=Path, default=Path("logs/hilbert-193-500k.verify.log"))
    p.add_argument("--progress", type=int, default=25_000)
    p.add_argument("--fresh", action="store_true")
    args = p.parse_args()
    if args.steps < 1 or args.progress < 1:
        p.error("--steps and --progress must be positive")
    artifact = args.artifact.open("rb")
    hasher = hashlib.sha256()
    for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
        hasher.update(chunk)
    digest = hasher.hexdigest()
    artifact.seek(0)
    meta = {"version": VERSION, "steps": args.steps, "artifact": str(args.artifact), "sha256": digest}
    state = {"metadata": meta, "next": 0, "seen_steps": [], "previous": None}
    if args.fresh:
        args.checkpoint.unlink(missing_ok=True)
    elif args.checkpoint.exists():
        state = json.loads(args.checkpoint.read_text())
        if state.get("metadata") != meta:
            raise SystemExit("checkpoint metadata mismatch; pass --fresh")

    def stop(signum, _frame):
        global STOP
        STOP = True
        log(args.log, f"signal={signum}; stopping at next progress boundary")
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    start = time.monotonic()
    seen = {tuple(step) for step in state["seen_steps"]}
    previous = tuple(state["previous"]) if state["previous"] is not None else None
    log(args.log, f"start/resume metadata={meta} next={state['next']} workers=1")
    with artifact as f:
        for line_no, line in enumerate(f):
            if line_no < state["next"]:
                continue
            if line_no > args.steps:
                raise AssertionError(f"extra vertex at line {line_no+1}")
            row = json.loads(line)
            if set(row) != {"i","x","y","z"}:
                raise AssertionError(f"invalid fields at line {line_no+1}")
            got = (row["x"], row["y"], row["z"])
            want = expected(line_no)
            if row["i"] != line_no or got != want:
                raise AssertionError(f"vertex mismatch line={line_no+1} got={row} want={(line_no,*want)}")
            if previous is not None:
                step = tuple(got[d] - previous[d] for d in range(3))
                if step not in MENU:
                    raise AssertionError(f"step outside fixed menu at index {line_no}: {step}")
                seen.add(step)
            previous = got
            state["next"] = line_no + 1
            if state["next"] % args.progress == 0 or STOP:
                state["seen_steps"] = sorted(seen)
                state["previous"] = previous
                atomic_json(args.checkpoint, state)
                elapsed = time.monotonic() - start
                rate = state["next"] / elapsed if elapsed else 0.0
                remaining = (args.steps + 1 - state["next"]) / rate if rate else 0.0
                log(args.log, f"completed={state['next']}/{args.steps+1} rate={rate:.0f}/s elapsed={elapsed:.2f}s eta={remaining:.2f}s checkpoint={args.checkpoint}")
                if STOP:
                    return 130
    if state["next"] != args.steps + 1:
        raise AssertionError(f"artifact ended at {state['next']} vertices; expected {args.steps+1}")
    if seen != MENU:
        raise AssertionError(f"artifact realizes {len(seen)} menu vectors, expected all {len(MENU)}")
    elapsed = time.monotonic() - start
    state.update({"complete": True, "seen_steps": sorted(seen), "previous": previous, "elapsed_seconds": elapsed})
    atomic_json(args.checkpoint, state)
    log(args.log, f"complete vertices={state['next']} menu={len(seen)} sha256={digest} elapsed={elapsed:.2f}s")
    print(f"VERIFIED exact construction: {args.steps} steps; {args.steps+1} vertices; menu={len(seen)}; sha256={digest}; elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
