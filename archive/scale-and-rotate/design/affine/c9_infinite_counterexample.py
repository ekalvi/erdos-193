#!/usr/bin/env python3
"""Exact certificate for an infinite family of C=9 affine counterexamples.

The all-k proof is the base-7 digit-cycle argument documented in
C9-INFINITE-COUNTEREXAMPLE.md.  ``--depth`` is a finite regression of the
closed formulas and O(log n) prefix-Parikh evaluator, not the universal proof.
This checker is independent of affine_recurrence.py and the prefix C++ checker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path


MORPHISM = (
    (0, 4, 9, 0, 8, 9, 0),
    (1, 5, 10, 1, 6, 10, 1),
    (2, 3, 11, 2, 7, 11, 2),
    (3, 2, 6, 3, 10, 6, 3),
    (4, 0, 7, 4, 11, 7, 4),
    (5, 1, 8, 5, 9, 8, 5),
    (6, 3, 2, 6, 3, 10, 6),
    (7, 4, 0, 7, 4, 11, 7),
    (8, 5, 1, 8, 5, 9, 8),
    (9, 0, 4, 9, 0, 8, 9),
    (10, 1, 5, 10, 1, 6, 10),
    (11, 2, 3, 11, 2, 7, 11),
)
COEFFICIENT = 9
I0 = 191_649
SCALE = 2_401
TRANSLATION = 74_000
OFFSETS = (0, 28, 36)
BASE7_PREFIX = (1, 4, 2)
BASE7_SUFFIX = (1, 3)


def digits_base7(value):
    if value == 0:
        return (0,)
    digits = []
    while value:
        value, digit = divmod(value, 7)
        digits.append(digit)
    return tuple(reversed(digits))


def value_base7(digits):
    value = 0
    for digit in digits:
        if not 0 <= digit < 7:
            raise ValueError("non-base-7 digit")
        value = 7 * value + digit
    return value


def transition(symbol, digits):
    for digit in digits:
        symbol = MORPHISM[symbol][digit]
    return symbol


@lru_cache(maxsize=None)
def symbol(index):
    """Automatic fixed-point symbol lambda[index] in O(log index)."""
    return transition(0, digits_base7(index))


@lru_cache(maxsize=None)
def walk(index):
    """Projected Parikh prefix W_index in O(log index)."""
    if index == 0:
        return (0, 0, 0)
    quotient, remainder = divmod(index, 7)
    parent = walk(quotient)
    result = [4 * coordinate + quotient for coordinate in parent]
    parent_symbol = symbol(quotient)
    for child in MORPHISM[parent_symbol][:remainder]:
        result[child % 3] += 1
    return tuple(result)


def add(*vectors):
    return tuple(sum(vector[axis] for vector in vectors) for axis in range(3))


def scale(coefficient, vector):
    return tuple(coefficient * value for value in vector)


def subtract(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def merged(index):
    return add(
        walk(index),
        scale(COEFFICIENT, walk(2 * index)),
        scale(COEFFICIENT**2, walk(5 * index)),
    )


def index_at(depth):
    index = I0
    for _ in range(depth):
        index = SCALE * index + TRANSLATION
    return index


def expected_index_digits(depth):
    return (*BASE7_PREFIX, *(5 for _ in range(4 * depth + 2)), *BASE7_SUFFIX)


def factor(multiplier, index, length):
    return tuple(symbol(multiplier * index + offset) for offset in range(length))


def canonical_json(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def verify_morphism_parikh_identity():
    for parent, image in enumerate(MORPHISM):
        counts = [0, 0, 0]
        for child in image:
            counts[child % 3] += 1
        expected = [1, 1, 1]
        expected[parent % 3] += 4
        if counts != expected:
            raise AssertionError("projected morphism Parikh identity drift", parent)


def direct_base_prefix_check():
    limit = 5 * (I0 + OFFSETS[-1])
    symbols = [0]
    while len(symbols) < limit:
        target = min(limit, 7 * len(symbols))
        parent_count = (target + 6) // 7
        symbols = [
            child
            for parent in symbols[:parent_count]
            for child in MORPHISM[parent]
        ][:target]
    counts = [0, 0, 0]
    requested = {
        multiplier * (I0 + offset)
        for multiplier in (1, 2, 5)
        for offset in OFFSETS
    }
    direct = {0: (0, 0, 0)}
    for index, parent in enumerate(symbols, start=1):
        counts[parent % 3] += 1
        if index in requested:
            direct[index] = tuple(counts)
    for index in requested:
        if direct[index] != walk(index):
            raise AssertionError("direct base prefix/evaluator disagreement", index)
    return {
        "symbols_expanded": limit,
        "prefix_queries_checked": len(requested),
        "direct_prefix_agrees_with_logarithmic_evaluator": True,
    }


def verify_digit_cycles():
    records = []
    specifications = (
        {
            "multiplier": 1,
            "prefix": (1, 4, 2),
            "repeated_digit": 5,
            "initial_repetitions": 2,
            "suffix_digits": 2,
            "suffix_min": value_base7((1, 3)),
            "suffix_max": value_base7((1, 3)) + 35,
        },
        {
            "multiplier": 2,
            "prefix": (3, 1, 5),
            "repeated_digit": 4,
            "initial_repetitions": 1,
            "suffix_digits": 3,
            "suffix_min": value_base7((3, 2, 6)),
            "suffix_max": value_base7((3, 2, 6)) + 71,
        },
        {
            "multiplier": 5,
            "prefix": (1, 1, 1, 0),
            "repeated_digit": 1,
            "initial_repetitions": 0,
            "suffix_digits": 4,
            "suffix_min": value_base7((0, 5, 0, 1)),
            "suffix_max": value_base7((0, 5, 0, 1)) + 179,
        },
    )
    for specification in specifications:
        state_after_prefix = transition(0, specification["prefix"])
        base_state = transition(
            state_after_prefix,
            (specification["repeated_digit"],)
            * specification["initial_repetitions"],
        )
        cycled_state = transition(
            base_state, (specification["repeated_digit"],) * 4
        )
        if cycled_state != base_state:
            raise AssertionError("four-digit automaton cycle drift", specification)
        if specification["suffix_max"] >= 7 ** specification["suffix_digits"]:
            raise AssertionError("offset carry enters repeated digit run")
        records.append({
            **specification,
            "prefix": list(specification["prefix"]),
            "state_after_prefix": state_after_prefix,
            "state_before_suffix": base_state,
            "state_after_four_more_repeated_digits": cycled_state,
            "four_digit_cycle_verified": True,
            "offsets_do_not_carry_into_repeated_run": True,
        })
    return records


def run(depth):
    if depth < 1:
        raise ValueError("depth must be positive")
    verify_morphism_parikh_identity()
    direct_check = direct_base_prefix_check()
    cycles = verify_digit_cycles()

    base_index = index_at(0)
    base_factors = {
        multiplier: factor(multiplier, base_index, 36 * multiplier)
        for multiplier in (1, 2, 5)
    }
    indices = []
    point_records = []
    for k in range(depth):
        index = index_at(k)
        if digits_base7(index) != expected_index_digits(k):
            raise AssertionError("closed base-7 index form drift", k)
        if digits_base7(2 * index) != (
            3, 1, 5, *(4 for _ in range(4 * k + 1)), 3, 2, 6
        ) or digits_base7(5 * index) != (
            1, 1, 1, 0, *(1 for _ in range(4 * k)), 0, 5, 0, 1
        ):
            raise AssertionError("multiplied base-7 closed form drift", k)
        if k and index != SCALE * indices[-1] + TRANSLATION:
            raise AssertionError("index recurrence drift", k)
        indices.append(index)
        for multiplier in (1, 2, 5):
            if factor(multiplier, index, 36 * multiplier) != base_factors[
                multiplier
            ]:
                raise AssertionError("local morphic factor cycle drift", k, multiplier)
        points = tuple(merged(index + offset) for offset in OFFSETS)
        first = subtract(points[1], points[0])
        second = subtract(points[2], points[1])
        if tuple(2 * value for value in first) != tuple(
            7 * value for value in second
        ):
            raise AssertionError("reported affine triple is not collinear", k)
        if first != (3_759, 5_306, 2_807) or second != (
            1_074, 1_516, 802
        ):
            raise AssertionError("local chord vector drift", k)
        if k == 0 and points != (
            (27_958_563, 26_840_581, 26_460_032),
            (27_962_322, 26_845_887, 26_462_839),
            (27_963_396, 26_847_403, 26_463_641),
        ):
            raise AssertionError("base counterexample coordinate drift")
        point_records.append({
            "depth": k,
            "index": index,
            "indices": [index + offset for offset in OFFSETS],
            "first_chord": list(first),
            "second_chord": list(second),
        })

    return {
        "status": "exact finite regression for a proved infinite C=9 counterexample family",
        "coefficient": COEFFICIENT,
        "index_recurrence": {
            "initial": I0,
            "scale": SCALE,
            "translation": TRANSLATION,
            "base7_closed_form": "142 + 5^(4k+2) + 13 (digit concatenation)",
        },
        "triple_offsets": list(OFFSETS),
        "base_points": [list(merged(I0 + offset)) for offset in OFFSETS],
        "first_chord": [3_759, 5_306, 2_807],
        "second_chord": [1_074, 1_516, 802],
        "collinearity_identity": "2*first_chord = 7*second_chord",
        "projected_morphism_parikh_identity_verified_for_all_symbols": True,
        "direct_base_prefix_check": direct_check,
        "four_digit_automatic_cycles": cycles,
        "depth_checked": depth,
        "checked_index_stream_sha256": hashlib.sha256(
            canonical_json(indices)
        ).hexdigest(),
        "checked_record_stream_sha256": hashlib.sha256(
            canonical_json(point_records)
        ).hexdigest(),
        "proof_boundary": (
            "all-depth result follows from the exact base-7 closed form, "
            "no-carry suffix ranges, and four-digit symbol-state cycles; "
            "depth is only a regression parameter"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=64)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run(args.depth)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
