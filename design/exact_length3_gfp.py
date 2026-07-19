#!/usr/bin/env python3
"""Exact greatest-fixed-point checker for length-three connector words.

For every radius-two step ``s``, this checker independently enumerates every
ordered three-step word ``(a,b,c)`` satisfying

    a + b + c = M s,

where ``M(x,y,z) = (3x,-3z,3y-z)``.  A word is retained exactly when its four
walk vertices are distinct and no three of them are collinear.  It then
computes the synchronous greatest fixed point

    S_{n+1} = {s in S_n : some legal word for s has all children in S_n}.

Two channels are checked: exact length three, and the union of lengths two and
three.  Each enumeration and closure is repeated with both forward and reverse
menu traversals.  The normalized semantic records must be byte-identical.
This is an independent check of the corresponding slices of
``connector_domains4.pkl``; it does not load that pickle.

Run from the repository root on one low-priority core:

    nice -n 15 python3 -B design/exact_length3_gfp.py \
        --output /tmp/exact-length3-gfp.json

The two proved conclusions are deliberately narrow: both the exact-length-
three child-step closure and the length-at-most-three closure are empty.  This
does *not* rule out a mixed-length substitution using words of length four or
five whose incidence matrix has Perron--Frobenius growth exactly three, nor
does it prove any far-secant availability or tail lemma.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Iterable


Vector = tuple[int, int, int]
Word = tuple[int, ...]

MENU: tuple[Vector, ...] = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)
MENU_INDEX = {v: i for i, v in enumerate(MENU)}

EXPECTED_BEFORE_COUNTS = (124, 104, 84, 70, 56, 36, 20, 10, 2)
EXPECTED_DROP_COUNTS = (20, 20, 14, 14, 20, 16, 10, 8, 2)
EXPECTED_TERMINAL_PAIR: tuple[Vector, ...] = ((-1, 0, 0), (1, 0, 0))

# The digests protect the exact dropped-step sets as well as these headlines.
EXPECTED_CHANNELS: dict[str, dict[str, object]] = {
    "exact_length_3": {
        "include_length_two": False,
        "total_words": 56_516,
        "internal_words": (56_516, 32_362, 15_712, 8_794, 4_120,
                           826, 72, 12, 0),
        "minimum_positive": (1, 1, 1, 3, 1, 1, 2, 6, None),
        "maximum": (3_232, 2_134, 1_176, 798, 516, 180, 22, 6, 0),
        "semantic_sha256": (
            "51b21c49e66668a95a08652e22ca88f0783b251dcf3f049b9f3f6e23666ba85c"
        ),
    },
    "lengths_2_or_3": {
        "include_length_two": True,
        "total_words": 57_068,
        "internal_words": (57_068, 32_718, 15_944, 8_922, 4_188,
                           854, 80, 12, 0),
        "minimum_positive": (1, 1, 1, 3, 1, 1, 2, 6, None),
        "maximum": (3_272, 2_164, 1_208, 822, 532, 192, 26, 6, 0),
        "semantic_sha256": (
            "523a91729d041436c646b67d06fdb674a15f3b9caf6a9bd14583ec9264b0513f"
        ),
    },
}


def add(a: Vector, b: Vector) -> Vector:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vector, b: Vector) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def apply_m(v: Vector) -> Vector:
    return (3 * v[0], -3 * v[2], 3 * v[1] - v[2])


def legal_two_word(a: Vector, b: Vector, target: Vector) -> bool:
    """Exact legality of the three connector vertices."""

    points = ((0, 0, 0), a, target)
    return (
        len(set(points)) == 3
        and cross(a, target) != (0, 0, 0)
        and add(a, b) == target
    )


def legal_three_word(a: Vector, b: Vector, c: Vector,
                     target: Vector) -> bool:
    """Exact legality of the four connector vertices."""

    p = a
    q = add(a, b)
    points = ((0, 0, 0), p, q, target)
    if len(set(points)) != 4:
        return False

    # The four triples of a four-point set.
    return all(
        cross(sub(points[j], points[i]), sub(points[k], points[i]))
        != (0, 0, 0)
        for i, j, k in ((0, 1, 2), (0, 1, 3),
                        (0, 2, 3), (1, 2, 3))
    )


def traversal(reverse: bool) -> Iterable[int]:
    order = range(len(MENU))
    return reversed(order) if reverse else order


def enumerate_hypergraph(reverse: bool,
                         include_length_two: bool) -> list[list[Word]]:
    """Enumerate the selected legal words; final children are determined."""

    edges: list[list[Word]] = [[] for _ in MENU]
    parent_order = traversal(reverse)
    for parent_index in parent_order:
        target = apply_m(MENU[parent_index])
        parent_edges = edges[parent_index]
        for a_index in traversal(reverse):
            a = MENU[a_index]
            remainder = sub(target, a)
            if include_length_two:
                b_index = MENU_INDEX.get(remainder)
                if b_index is not None:
                    b = MENU[b_index]
                    if legal_two_word(a, b, target):
                        parent_edges.append((a_index, b_index))
            for b_index in traversal(reverse):
                b = MENU[b_index]
                c = sub(remainder, b)
                c_index = MENU_INDEX.get(c)
                if c_index is None:
                    continue
                if legal_three_word(a, b, c, target):
                    parent_edges.append((a_index, b_index, c_index))
    return edges


def semantic_record(reverse: bool,
                    include_length_two: bool = False) -> dict[str, object]:
    edges = enumerate_hypergraph(reverse, include_length_two)
    alive = set(range(len(MENU)))
    rounds: list[dict[str, object]] = []

    while alive:
        witness_counts = {
            parent: sum(
                all(child in alive for child in word)
                for word in edges[parent]
            )
            for parent in sorted(alive)
        }
        dropped = sorted(parent for parent, count in witness_counts.items()
                         if count == 0)
        positive = [count for count in witness_counts.values() if count > 0]
        rounds.append(
            {
                "before_count": len(alive),
                "internal_word_count": sum(witness_counts.values()),
                "zero_witness_parent_count": len(dropped),
                "minimum_positive_witness_count": min(positive)
                if positive else None,
                "maximum_witness_count": max(positive) if positive else 0,
                "dropped_steps": [MENU[parent] for parent in dropped],
            }
        )
        if not dropped:
            break
        alive.difference_update(dropped)

    model: dict[str, object] = {
            "menu_radius": 2,
            "menu_size": len(MENU),
            "matrix": ((3, 0, 0), (0, 0, -3), (0, 3, -1)),
            "ordered_words": True,
            "exact_internal_legality": True,
    }
    if include_length_two:
        model["word_lengths"] = (2, 3)
    else:
        # Preserve the original exact-length-three semantic record and digest.
        model["word_length"] = 3

    record: dict[str, object] = {
        "model": model,
        "total_legal_words": sum(len(parent_edges)
                                 for parent_edges in edges),
        "rounds": rounds,
        "surviving_steps": [MENU[parent] for parent in sorted(alive)],
    }
    if include_length_two:
        record["legal_word_counts_by_length"] = {
            "2": sum(len(word) == 2 for parent_edges in edges
                     for word in parent_edges),
            "3": sum(len(word) == 3 for parent_edges in edges
                     for word in parent_edges),
        }
    return record


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def semantic_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def verify_expected(channel: str, record: dict[str, object],
                    digest: str) -> None:
    expected = EXPECTED_CHANNELS[channel]
    rounds = record["rounds"]
    assert isinstance(rounds, list)
    before = tuple(item["before_count"] for item in rounds)
    internal = tuple(item["internal_word_count"] for item in rounds)
    dropped = tuple(item["zero_witness_parent_count"] for item in rounds)
    minimum = tuple(item["minimum_positive_witness_count"] for item in rounds)
    maximum = tuple(item["maximum_witness_count"] for item in rounds)
    terminal = tuple(tuple(v) for v in rounds[-1]["dropped_steps"])

    checks = {
        "total legal words": (record["total_legal_words"],
                              expected["total_words"]),
        "before counts": (before, EXPECTED_BEFORE_COUNTS),
        "internal word counts": (internal, expected["internal_words"]),
        "drop counts": (dropped, EXPECTED_DROP_COUNTS),
        "minimum positive witness counts": (
            minimum, expected["minimum_positive"]
        ),
        "maximum witness counts": (maximum, expected["maximum"]),
        "terminal pair": (terminal, EXPECTED_TERMINAL_PAIR),
        "surviving steps": (record["surviving_steps"], []),
        "semantic sha256": (digest, expected["semantic_sha256"]),
    }
    failures = [f"{name}: got {got!r}, expected {expected!r}"
                for name, (got, expected) in checks.items()
                if got != expected]
    if failures:
        raise RuntimeError("certificate regression:\n  " + "\n  ".join(failures))


def nice_value() -> int | None:
    try:
        return os.getpriority(os.PRIO_PROCESS, 0)
    except (AttributeError, OSError):
        return None


def run_once(channel: str, reverse: bool,
             include_length_two: bool) -> tuple[dict[str, object],
                                                 dict[str, object]]:
    started = time.monotonic()
    record = semantic_record(reverse, include_length_two)
    run = {
        "channel": channel,
        "traversal": "reverse" if reverse else "forward",
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "maximum_resident_bytes": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "semantic_sha256": semantic_sha256(record),
    }
    return record, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="optional JSON output (atomic replacement)")
    parser.add_argument(
        "--allow-high-priority",
        action="store_true",
        help="allow execution below nice 10 (not recommended on the homelab)",
    )
    args = parser.parse_args()

    nice = nice_value()
    if not args.allow_high_priority and nice is not None and nice < 10:
        parser.error(f"refusing nice={nice}; rerun under `nice -n 15`")

    channels: dict[str, object] = {}
    for channel, expected in EXPECTED_CHANNELS.items():
        include_length_two = bool(expected["include_length_two"])
        first, first_run = run_once(
            channel, reverse=False, include_length_two=include_length_two
        )
        second, second_run = run_once(
            channel, reverse=True, include_length_two=include_length_two
        )
        if canonical_bytes(first) != canonical_bytes(second):
            raise RuntimeError(
                f"{channel}: forward and reverse semantic records differ"
            )

        digest = semantic_sha256(first)
        verify_expected(channel, first, digest)
        channels[channel] = {
            "semantic_identity": True,
            "semantic_sha256": digest,
            "runs": [first_run, second_run],
            "semantic_record": first,
        }

    output = {
        "status": (
            "both exact length-three and lengths-two-or-three child-step "
            "greatest fixed points are empty"
        ),
        "all_semantic_identities": True,
        "channels": channels,
        "resource_policy": {
            "processes": 1,
            "threads": 1,
            "nice": nice,
        },
        "theorem_boundary": {
            "proved_exact_length_three": (
                "No nonempty subset of the radius-two menu is closed under "
                "some exact legal connector word of length three for every "
                "surviving parent step."
            ),
            "proved_lengths_two_or_three": (
                "No nonempty subset of the radius-two menu is closed when "
                "each surviving parent may use any exact legal connector "
                "word of length two or three."
            ),
            "not_proved": (
                "No mixed-length substitution using length-four or "
                "length-five words has Perron--Frobenius growth three; no "
                "far-secant availability, contraction, or unconditional "
                "infinite-walk theorem follows."
            ),
        },
    }
    encoded = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(encoded)
        temporary.replace(args.output)
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
