#!/usr/bin/env python3
"""Construct the terminal-steered Hilbert lift used by Hilbert193.Construction.

The output contains one JSON object per vertex.  Generation is resumable through
an append-only .part file and an atomic checkpoint.  On completion the .part
file is atomically renamed to --output.
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
I, S, T, C = 0, 4, 7, 3
STATE_DATA = ((0,0,0),(0,1,0),(0,0,1),(0,1,1),(1,0,0),(1,1,0),(1,0,1),(1,1,1))
CHILD = ((0,0),(0,1),(1,1),(1,0))
REFINEMENT = (S,I,I,T)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def act(state: int, pair: tuple[int,int]) -> tuple[int,int]:
    swap, bx, by = STATE_DATA[state]
    x, y = pair
    return ((y if swap else x) ^ bx, (x if swap else y) ^ by)


def compose(g: int, h: int) -> int:
    target = tuple(act(g, act(h, p)) for p in CHILD)
    return next(s for s in range(8) if tuple(act(s, p) for p in CHILD) == target)


OUTPUT = tuple(tuple(act(g, CHILD[q]) for q in range(4)) for g in range(8))
NEXT = tuple(tuple(compose(g, REFINEMENT[q]) for q in range(4)) for g in range(8))
CORRECTION = (5, None, None, 3, 1, None, None, 13)


def even_length(n: int) -> int:
    raw = max(1, (n.bit_length() + 1) // 2)
    return raw + (raw & 1)


def hilbert(n: int) -> tuple[int,int,int]:
    state = I
    x = y = 0
    for pos in range(even_length(n) - 1, -1, -1):
        q = (n >> (2 * pos)) & 3
        ox, oy = OUTPUT[state][q]
        x, y, state = (x << 1) | ox, (y << 1) | oy, NEXT[state][q]
    return x, y, state


def selected(block: int) -> tuple[int,int,int]:
    prefix_state = hilbert(block)[2]
    correction = CORRECTION[prefix_state]
    if correction is None:
        raise AssertionError(f"unreachable prefix state {prefix_state}")
    z = 16 * block + correction
    x, y, terminal = hilbert(z)
    if terminal != I:
        raise AssertionError(f"terminal steering failed at block {block}")
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
    p.add_argument("--steps", type=int, default=500_000)
    p.add_argument("--output", type=Path, default=Path("hilbert-193-500k.jsonl"))
    p.add_argument("--checkpoint", type=Path, default=Path("logs/hilbert-193-500k.ckpt.json"))
    p.add_argument("--log", type=Path, default=Path("logs/hilbert-193-500k.construct.log"))
    p.add_argument("--chunk", type=int, default=10_000)
    p.add_argument("--fresh", action="store_true")
    args = p.parse_args()
    if args.steps < 1 or args.chunk < 1:
        p.error("--steps and --chunk must be positive")
    part = Path(str(args.output) + ".part")
    meta = {"version": VERSION, "steps": args.steps, "vertices": args.steps + 1}
    state = {"metadata": meta, "next": 0}
    if args.fresh:
        for path in (part, args.checkpoint, args.output):
            path.unlink(missing_ok=True)
    elif args.checkpoint.exists():
        state = json.loads(args.checkpoint.read_text())
        if state.get("metadata") != meta:
            raise SystemExit("checkpoint metadata mismatch; pass --fresh")
        if not part.exists() and state["next"] != 0:
            raise SystemExit("checkpoint exists but partial artifact is missing")
        with part.open("rb") as f:
            lines = sum(1 for _ in f)
        if lines != state["next"]:
            raise SystemExit(f"partial artifact has {lines} lines; checkpoint expects {state['next']}")
    elif part.exists():
        raise SystemExit("partial artifact exists without checkpoint; pass --fresh")

    def stop(signum, _frame):
        global STOP
        STOP = True
        log(args.log, f"signal={signum}; stopping after current chunk")
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    start = time.monotonic()
    log(args.log, f"start/resume metadata={meta} next={state['next']} chunk={args.chunk} workers=1")
    part.parent.mkdir(parents=True, exist_ok=True)
    with part.open("a", buffering=1024 * 1024) as out:
        while state["next"] <= args.steps:
            end = min(args.steps + 1, state["next"] + args.chunk)
            for block in range(state["next"], end):
                x, y, z = selected(block)
                out.write(json.dumps({"i": block, "x": x, "y": y, "z": z}, separators=(",", ":")) + "\n")
            out.flush()
            os.fsync(out.fileno())
            state["next"] = end
            atomic_json(args.checkpoint, state)
            elapsed = time.monotonic() - start
            rate = (end / elapsed) if elapsed else 0.0
            remaining = (args.steps + 1 - end) / rate if rate else 0.0
            log(args.log, f"completed={end}/{args.steps+1} rate={rate:.0f}/s elapsed={elapsed:.2f}s eta={remaining:.2f}s checkpoint={args.checkpoint}")
            if STOP:
                return 130
    os.replace(part, args.output)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    elapsed = time.monotonic() - start
    state.update({"complete": True, "sha256": digest, "elapsed_seconds": elapsed})
    atomic_json(args.checkpoint, state)
    log(args.log, f"complete output={args.output} sha256={digest} elapsed={elapsed:.2f}s")
    print(f"CONSTRUCTED {args.steps} steps; {args.steps+1} vertices; sha256={digest}; elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
