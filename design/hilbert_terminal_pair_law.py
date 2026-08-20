#!/usr/bin/env python3
"""Exact checks for the nested-even Hilbert terminal-state pair law.

The default run is finite and deterministic. Long runs checkpoint after each
completed exhaustive outer index and after each random progress batch. Restart
with the same arguments to resume; use --fresh to reject prior progress.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
I, X, Y, C, S, R, L, T = range(8)
NAMES = ("I", "X", "Y", "C", "S", "R", "L", "T")
# State action on a bit pair: optional swap, then xor by (bx, by).
STATE_DATA = (
    (0, 0, 0),  # I: (x,y)
    (0, 1, 0),  # X: (1-x,y)
    (0, 0, 1),  # Y: (x,1-y)
    (0, 1, 1),  # C: (1-x,1-y)
    (1, 0, 0),  # S: (y,x)
    (1, 1, 0),  # R: (1-y,x)
    (1, 0, 1),  # L: (y,1-x)
    (1, 1, 1),  # T: (1-y,1-x)
)
CHILD = ((0, 0), (0, 1), (1, 1), (1, 0))
REFINEMENT = (S, I, I, T)
EXPECTED = (
    (((0, 0), S), ((0, 1), I), ((1, 1), I), ((1, 0), T)),
    (((1, 0), R), ((1, 1), X), ((0, 1), X), ((0, 0), L)),
    (((0, 1), L), ((0, 0), Y), ((1, 0), Y), ((1, 1), R)),
    (((1, 1), T), ((1, 0), C), ((0, 0), C), ((0, 1), S)),
    (((0, 0), I), ((1, 0), S), ((1, 1), S), ((0, 1), C)),
    (((1, 0), X), ((0, 0), R), ((0, 1), R), ((1, 1), Y)),
    (((0, 1), Y), ((1, 1), L), ((1, 0), L), ((0, 0), X)),
    (((1, 1), C), ((0, 1), T), ((0, 0), T), ((1, 0), I)),
)
STOP = False


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def act(state: int, pair: tuple[int, int]) -> tuple[int, int]:
    swap, bx, by = STATE_DATA[state]
    x, y = pair
    return ((y if swap else x) ^ bx, (x if swap else y) ^ by)


def compose(g: int, h: int) -> int:
    """Return g after h."""
    target = tuple(act(g, act(h, p)) for p in ((0, 0), (0, 1), (1, 0), (1, 1)))
    for state in range(8):
        if tuple(act(state, p) for p in ((0, 0), (0, 1), (1, 0), (1, 1))) == target:
            return state
    raise AssertionError("D4 state closure failed")


OUTPUT = tuple(tuple(act(g, CHILD[q]) for q in range(4)) for g in range(8))
NEXT = tuple(tuple(compose(g, REFINEMENT[q]) for q in range(4)) for g in range(8))


def even_length(n: int) -> int:
    raw = max(1, (n.bit_length() + 1) // 2)
    return raw + (raw & 1)


def hilbert_and_state(n: int) -> tuple[int, int, int]:
    if n < 0:
        raise ValueError("index must be nonnegative")
    state = I
    x = y = 0
    for pos in range(even_length(n) - 1, -1, -1):
        q = (n >> (2 * pos)) & 3
        ox, oy = OUTPUT[state][q]
        x = (x << 1) | ox
        y = (y << 1) | oy
        state = NEXT[state][q]
    return x, y, state


def standard_d2xy(order: int, index: int) -> tuple[int, int]:
    """Independent standard finite-order Hilbert d2xy reference."""
    side = 1 << order
    x = y = 0
    t = index
    scale = 1
    while scale < side:
        rx = 1 & (t >> 1)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = scale - 1 - x
                y = scale - 1 - y
            x, y = y, x
        x += scale * rx
        y += scale * ry
        t >>= 2
        scale <<= 1
    return x, y


def v2(value: int) -> int:
    if value == 0:
        return 10**9
    value = abs(value)
    return (value & -value).bit_length() - 1


def displacement_value(dx: int, dy: int) -> int:
    vx, vy = v2(dx), v2(dy)
    p = min(vx, vy)
    if p >= 10**9:
        raise ValueError("zero displacement")
    return 2 * p + int(vx == vy)


def terminal_formula(n: int) -> int:
    zeros = threes = 0
    length = even_length(n)
    for pos in range(length):
        q = (n >> (2 * pos)) & 3
        zeros ^= q == 0
        threes ^= q == 3
    state = I
    if zeros:
        state = compose(state, S)
    if threes:
        state = compose(state, T)
    return state


def selected_index(block: int) -> int:
    correction = {I: 5, S: 1, T: 13, C: 3}  # 11, 01, 31, 03 in base 4
    prefix_state = hilbert_and_state(block)[2]
    return 16 * block + correction[prefix_state]


def deterministic_pair(seed: int, attempt: int, bits: int) -> tuple[int, int]:
    width = (bits + 7) // 8
    payload = f"{seed}:{attempt}".encode()
    raw = hashlib.shake_256(payload).digest(2 * width)
    mask = (1 << bits) - 1
    a = int.from_bytes(raw[:width], "big") & mask
    b = int.from_bytes(raw[width:], "big") & mask
    return (a, b) if a < b else (b, a)


def validate_structure() -> None:
    actual = tuple(tuple((OUTPUT[g][q], NEXT[g][q]) for q in range(4)) for g in range(8))
    assert actual == EXPECTED
    for q in range(4):
        assert len({NEXT[g][q] for g in range(8)}) == 8
    assert len({(OUTPUT[g][q], NEXT[g][q]) for g in range(8) for q in range(4)}) == 32
    for order in range(1, 7):
        for n in range(4**order):
            word_x, word_y, _ = transduce_at_length(n, order)
            assert (word_x, word_y) == standard_d2xy(order, n)
            nested_x, nested_y, _ = transduce_at_length(n, order + 2)
            assert (nested_x, nested_y) == (word_x, word_y)
    for n in range(4**6):
        assert hilbert_and_state(n)[2] == terminal_formula(n)


def transduce_at_length(n: int, length: int) -> tuple[int, int, int]:
    state = I
    x = y = 0
    for pos in range(length - 1, -1, -1):
        q = (n >> (2 * pos)) & 3
        ox, oy = OUTPUT[state][q]
        x = (x << 1) | ox
        y = (y << 1) | oy
        state = NEXT[state][q]
    return x, y, state


def metadata(args: argparse.Namespace) -> dict[str, int]:
    return {
        "version": VERSION,
        "limit": args.limit,
        "random_trials": args.random_trials,
        "random_bits": args.random_bits,
        "seed": args.seed,
    }


def save_checkpoint(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, sort_keys=True) + "\n")
    os.replace(tmp, path)


def log(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(f"{now()} {message}\n")
        handle.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=4096)
    parser.add_argument("--random-trials", type=int, default=100_000)
    parser.add_argument("--random-bits", type=int, default=160)
    parser.add_argument("--seed", type=int, default=193)
    parser.add_argument("--checkpoint", type=Path, default=Path("logs/hilbert-pair-law.ckpt.json"))
    parser.add_argument("--log", type=Path, default=Path("logs/hilbert-pair-law.log"))
    parser.add_argument("--fresh", action="store_true", help="ignore and replace an existing checkpoint")
    return parser.parse_args()


def main() -> int:
    global STOP
    args = parse_args()
    meta = metadata(args)
    state = {
        "metadata": meta,
        "phase": "exhaustive",
        "next_n": 1,
        "same_state_pairs": 0,
        "random_attempt": 0,
        "random_tested": 0,
    }
    if args.checkpoint.exists() and not args.fresh:
        loaded = json.loads(args.checkpoint.read_text())
        if loaded.get("metadata") != meta:
            raise SystemExit("checkpoint metadata mismatch; pass --fresh or use matching arguments")
        state = loaded
    log(args.log, f"start/resume metadata={meta} state={state}")

    def stop_handler(signum, _frame):
        global STOP
        STOP = True
        log(args.log, f"signal={signum}; checkpoint requested")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    validate_structure()
    points = [hilbert_and_state(n) for n in range(args.limit)]
    if state["phase"] == "exhaustive":
        for n in range(state["next_n"], args.limit):
            xn, yn, sn = points[n]
            for m in range(n):
                xm, ym, sm = points[m]
                if sm != sn:
                    continue
                state["same_state_pairs"] += 1
                got = displacement_value(xn - xm, yn - ym)
                want = v2(n - m)
                if got != want:
                    raise AssertionError(f"pair-law counterexample {(m, n, xn-xm, yn-ym, NAMES[sn], got, want)}")
            state["next_n"] = n + 1
            if n % 128 == 0 or STOP:
                save_checkpoint(args.checkpoint, state)
                log(args.log, f"exhaustive completed={n}/{args.limit-1} pairs={state['same_state_pairs']}")
            if STOP:
                return 130
        state["phase"] = "random"
        save_checkpoint(args.checkpoint, state)

    if state["phase"] == "random":
        while state["random_tested"] < args.random_trials:
            m, n = deterministic_pair(args.seed, state["random_attempt"], args.random_bits)
            state["random_attempt"] += 1
            if m == n:
                continue
            xm, ym, sm = hilbert_and_state(m)
            xn, yn, sn = hilbert_and_state(n)
            if sm != sn:
                continue
            state["random_tested"] += 1
            got = displacement_value(xn - xm, yn - ym)
            want = v2(n - m)
            if got != want:
                raise AssertionError(f"random pair-law counterexample {(m, n, xn-xm, yn-ym, NAMES[sn], got, want)}")
            if state["random_tested"] % 5000 == 0 or STOP:
                save_checkpoint(args.checkpoint, state)
                log(args.log, f"random tested={state['random_tested']}/{args.random_trials} attempts={state['random_attempt']}")
            if STOP:
                return 130
        state["phase"] = "selector"
        save_checkpoint(args.checkpoint, state)

    selected = [selected_index(a) for a in range(100_000)]
    assert {hilbert_and_state(n)[2] for n in selected} == {I}
    gaps = [b - a for a, b in zip(selected, selected[1:])]
    assert min(gaps) >= 1 and max(gaps) <= 28
    state["phase"] = "complete"
    state["selector_gap_min"] = min(gaps)
    state["selector_gap_max"] = max(gaps)
    save_checkpoint(args.checkpoint, state)
    log(args.log, f"complete pairs={state['same_state_pairs']} random={state['random_tested']} attempts={state['random_attempt']} gap=[{min(gaps)},{max(gaps)}]")
    print(
        "VERIFIED:",
        f"{state['same_state_pairs']} exhaustive same-state pairs;",
        f"{state['random_tested']} random same-state pairs;",
        f"selector gaps {min(gaps)}..{max(gaps)}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
