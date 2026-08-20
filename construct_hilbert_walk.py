#!/usr/bin/env python3
"""Construct the terminal-steered Hilbert lift used by Hilbert193.Construction.

The output contains one JSON object per vertex. Generation is resumable through
an append-only .part file and an atomic checkpoint. On completion the .part
file is atomically renamed to --output. Restarting from a completed checkpoint
validates and reuses the final artifact without rewriting it.
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_completed_output(path: Path, meta: dict, expected_digest: str | None) -> str:
    if not path.exists():
        raise SystemExit("completed checkpoint exists but final artifact is missing")
    digest = hashlib.sha256()
    lines = 0
    try:
        with path.open("rb") as artifact:
            for block, line in enumerate(artifact):
                digest.update(line)
                x, y, z = selected(block)
                expected = {"i": block, "x": x, "y": y, "z": z}
                if json.loads(line) != expected:
                    raise SystemExit(f"final artifact mismatch at line {block + 1}")
                lines = block + 1
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SystemExit(f"invalid final artifact: {error}") from error
    if lines != meta["vertices"]:
        raise SystemExit(f"final artifact has {lines} lines; expected {meta['vertices']}")
    actual_digest = digest.hexdigest()
    if expected_digest is not None and actual_digest != expected_digest:
        raise SystemExit(
            f"final artifact digest {actual_digest} does not match checkpoint {expected_digest}"
        )
    return actual_digest


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
        next_block = state.get("next")
        if not isinstance(next_block, int) or not 0 <= next_block <= meta["vertices"]:
            raise SystemExit("checkpoint has invalid next offset")
        if state.get("complete"):
            if part.exists():
                raise SystemExit("completed checkpoint still has a partial artifact; pass --fresh")
            if next_block != meta["vertices"]:
                raise SystemExit("completed checkpoint has an incomplete next offset")
            expected_digest = state.get("sha256")
            if not isinstance(expected_digest, str):
                raise SystemExit("completed checkpoint has no artifact digest")
            digest = validate_completed_output(args.output, meta, expected_digest)
            log(args.log, f"reuse validated output={args.output} sha256={digest}")
            print(
                f"REUSED {args.steps} steps; {args.steps+1} validated vertices; "
                f"sha256={digest}"
            )
            return 0
        if args.output.exists():
            if next_block == meta["vertices"] and not part.exists():
                digest = validate_completed_output(args.output, meta, None)
                state.update({"complete": True, "sha256": digest, "recovered": True})
                atomic_json(args.checkpoint, state)
                log(args.log, f"recovered completed output={args.output} sha256={digest}")
                print(
                    f"RECOVERED {args.steps} steps; {args.steps+1} validated vertices; "
                    f"sha256={digest}"
                )
                return 0
            raise SystemExit("final artifact exists for an incomplete checkpoint; pass --fresh")
        if not part.exists() and next_block != 0:
            raise SystemExit("checkpoint exists but partial artifact is missing")
        if part.exists():
            with part.open("rb") as artifact:
                lines = sum(1 for _ in artifact)
            if lines != next_block:
                raise SystemExit(
                    f"partial artifact has {lines} lines; checkpoint expects {next_block}"
                )
    elif part.exists() or args.output.exists():
        raise SystemExit("artifact exists without checkpoint; pass --fresh")

    def stop(signum, _frame):
        global STOP
        STOP = True
        log(args.log, f"signal={signum}; stopping after current chunk")
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    resume_start = state["next"]
    start = time.monotonic()
    log(
        args.log,
        f"start/resume metadata={meta} next={resume_start} chunk={args.chunk} workers=1",
    )
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
            run_completed = end - resume_start
            rate = (run_completed / elapsed) if elapsed else 0.0
            remaining = (args.steps + 1 - end) / rate if rate else 0.0
            log(
                args.log,
                f"completed={end}/{args.steps+1} run_completed={run_completed} "
                f"rate={rate:.0f}/s elapsed={elapsed:.2f}s eta={remaining:.2f}s "
                f"checkpoint={args.checkpoint}",
            )
            if STOP:
                return 130
    os.replace(part, args.output)
    digest = sha256_file(args.output)
    elapsed = time.monotonic() - start
    state.update({"complete": True, "sha256": digest, "elapsed_seconds": elapsed})
    atomic_json(args.checkpoint, state)
    log(args.log, f"complete output={args.output} sha256={digest} elapsed={elapsed:.2f}s")
    print(f"CONSTRUCTED {args.steps} steps; {args.steps+1} vertices; sha256={digest}; elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
