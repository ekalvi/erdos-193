#!/usr/bin/env python3
"""Exact base-7 recurrence generator for P_n=(W_n,W_2n,W_5n).

The projected Lidbetter walk satisfies V(7t+r)=4V(t)+g(lambda[t],r),
where V(t)=3W(t)-t(1,1,1).  Multipliers two and five require only the joint
automatic symbol state

    lambda[t], lambda[2t:2t+2], lambda[5t:5t+5].

This program constructs every reachable joint state, its digit transitions,
and the exact correction h in Q(7t+r)=4Q(t)+h(state(t),r).  It also projects
that correction to the dimension-correct weighted merge

    Z_C(t) = V(t) + C V(2t) + C^2 V(5t).

It can emit the finite table used by a future rational defect-CEGAR
certificate.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
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

ZERO3 = (0, 0, 0)


def add3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale3(c, a):
    return (c * a[0], c * a[1], c * a[2])


def delta(symbol):
    """V(n+1)-V(n) for projected symbol lambda[n]."""
    out = [-1, -1, -1]
    out[symbol % 3] = 2
    return tuple(out)


def prefix_correction(symbol, remainder):
    """g(symbol,r) in V(7t+r)=4V(t)+g(lambda[t],r)."""
    out = [0, 0, 0]
    for child in MORPHISM[symbol][:remainder]:
        out = list(add3(out, delta(child)))
    return tuple(out)


def fixed_point_prefix(length):
    symbols = [0]
    while len(symbols) < length:
        symbols = [child for symbol in symbols for child in MORPHISM[symbol]]
    return symbols[:length]


def state_symbol(state, multiplier, offset):
    if multiplier == 1:
        assert offset == 0
        return state[0]
    if multiplier == 2:
        assert 0 <= offset <= 1
        return state[1 + offset]
    if multiplier == 5:
        assert 0 <= offset <= 4
        return state[3 + offset]
    raise ValueError(multiplier)


def child_symbol(state, multiplier, digit, offset):
    quotient, remainder = divmod(multiplier * digit + offset, 7)
    parent = state_symbol(state, multiplier, quotient)
    return MORPHISM[parent][remainder]


def transition(state, digit):
    return (
        child_symbol(state, 1, digit, 0),
        child_symbol(state, 2, digit, 0),
        child_symbol(state, 2, digit, 1),
        child_symbol(state, 5, digit, 0),
        child_symbol(state, 5, digit, 1),
        child_symbol(state, 5, digit, 2),
        child_symbol(state, 5, digit, 3),
        child_symbol(state, 5, digit, 4),
    )


def block_correction(state, multiplier, digit):
    quotient, remainder = divmod(multiplier * digit, 7)
    shift = ZERO3
    for offset in range(quotient):
        shift = add3(shift, delta(state_symbol(state, multiplier, offset)))
    symbol = state_symbol(state, multiplier, quotient)
    return add3(scale3(4, shift), prefix_correction(symbol, remainder))


def q_correction(state, digit):
    return (
        *block_correction(state, 1, digit),
        *block_correction(state, 2, digit),
        *block_correction(state, 5, digit),
    )


def weighted_correction(correction, coefficient):
    coefficient_squared = coefficient * coefficient
    return tuple(
        correction[coordinate]
        + coefficient * correction[3 + coordinate]
        + coefficient_squared * correction[6 + coordinate]
        for coordinate in range(3)
    )


def enumerate_automatic_states():
    prefix = fixed_point_prefix(5)
    start = (prefix[0], prefix[0], prefix[1], *prefix[:5])
    states = [start]
    ids = {start: 0}
    queue = deque([start])
    transitions = []
    corrections = []
    while queue:
        state = queue.popleft()
        row = []
        hrow = []
        for digit in range(7):
            child = transition(state, digit)
            if child not in ids:
                ids[child] = len(states)
                states.append(child)
                queue.append(child)
            row.append(ids[child])
            hrow.append(q_correction(state, digit))
        transitions.append(row)
        corrections.append(hrow)
    return states, transitions, corrections


def minimize_mealy(transitions, corrections):
    """Partition refinement for the digit-labelled correction transducer."""
    block_by_output = {}
    blocks = []
    for row in corrections:
        key = tuple(row)
        if key not in block_by_output:
            block_by_output[key] = len(block_by_output)
        blocks.append(block_by_output[key])

    rounds = 0
    while True:
        signatures = {}
        refined = []
        for state, row in enumerate(corrections):
            signature = (
                tuple(row),
                tuple(blocks[child] for child in transitions[state]),
            )
            if signature not in signatures:
                signatures[signature] = len(signatures)
            refined.append(signatures[signature])
        rounds += 1
        if refined == blocks:
            return blocks, rounds
        blocks = refined


def walk_prefix(symbols):
    walk = [(0, 0, 0)]
    for symbol in symbols:
        point = list(walk[-1])
        point[symbol % 3] += 1
        walk.append(tuple(point))
    return walk


def v(point, index):
    return tuple(3 * coordinate - index for coordinate in point)


def verify_prefix(limit, states, transitions, corrections):
    symbols = fixed_point_prefix(5 * (7 * limit + 7) + 5)
    walk = walk_prefix(symbols)

    id_by_state = {state: i for i, state in enumerate(states)}
    state_ids = []
    for t in range(limit + 1):
        state = (
            symbols[t], symbols[2 * t], symbols[2 * t + 1],
            symbols[5 * t], symbols[5 * t + 1], symbols[5 * t + 2],
            symbols[5 * t + 3], symbols[5 * t + 4],
        )
        state_ids.append(id_by_state[state])

    checked = 0
    max_abs_correction = 0
    for t in range(limit + 1):
        q_t = (*v(walk[t], t), *v(walk[2 * t], 2 * t),
               *v(walk[5 * t], 5 * t))
        for digit in range(7):
            child_t = 7 * t + digit
            q_child = (
                *v(walk[child_t], child_t),
                *v(walk[2 * child_t], 2 * child_t),
                *v(walk[5 * child_t], 5 * child_t),
            )
            correction = corrections[state_ids[t]][digit]
            expected = tuple(4 * coordinate + h for coordinate, h in zip(q_t, correction))
            assert q_child == expected
            expected_state = transitions[state_ids[t]][digit]
            actual_state = (
                symbols[child_t], symbols[2 * child_t], symbols[2 * child_t + 1],
                symbols[5 * child_t], symbols[5 * child_t + 1],
                symbols[5 * child_t + 2], symbols[5 * child_t + 3],
                symbols[5 * child_t + 4],
            )
            assert states[expected_state] == actual_state
            max_abs_correction = max(max_abs_correction, *(abs(x) for x in correction))
            checked += 1
    return {
        "parent_indices": limit + 1,
        "digit_transitions": checked,
        "max_abs_q_correction": max_abs_correction,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-prefix", type=int, default=10_000)
    parser.add_argument("--merge-coefficient", type=int, default=9)
    parser.add_argument("--emit-table", type=Path)
    args = parser.parse_args()

    states, transitions, corrections = enumerate_automatic_states()
    quotient_blocks, refinement_rounds = minimize_mealy(
        transitions, corrections
    )
    verification = verify_prefix(
        args.verify_prefix, states, transitions, corrections
    )
    distinct_corrections = {
        correction for row in corrections for correction in row
    }
    weighted_corrections = [
        [
            weighted_correction(correction, args.merge_coefficient)
            for correction in row
        ]
        for row in corrections
    ]
    weighted_blocks, weighted_refinement_rounds = minimize_mealy(
        transitions, weighted_corrections
    )
    distinct_weighted_corrections = {
        correction for row in weighted_corrections for correction in row
    }
    summary = {
        "status": "exact finite recurrence table constructed",
        "base": 7,
        "q_scaling": 4,
        "defect_scaling_for_all_indices_times_7": 28,
        "joint_symbol_state_width": 8,
        "reachable_joint_states": len(states),
        "minimal_correction_transducer_states": len(set(quotient_blocks)),
        "partition_refinement_rounds": refinement_rounds,
        "distinct_q_corrections": len(distinct_corrections),
        "weighted_merge": {
            "coefficient": args.merge_coefficient,
            "step_coordinate_sum": (
                1
                + 2 * args.merge_coefficient
                + 5 * args.merge_coefficient * args.merge_coefficient
            ),
            "distinct_corrections": len(distinct_weighted_corrections),
            "minimal_correction_transducer_states": len(set(weighted_blocks)),
            "partition_refinement_rounds": weighted_refinement_rounds,
            "interpretation": (
                "exact projected recurrence for the Z^3 weighted merge; "
                "does not prove projected defect zero-exclusion"
            ),
        },
        "verification": verification,
        "interpretation": (
            "proves the Q recurrence; does not prove that the bilinear "
            "three-index defect avoids zero"
        ),
    }
    if args.emit_table:
        table = {
            **summary,
            "states": states,
            "transitions": transitions,
            "corrections": corrections,
            "minimal_quotient_block": quotient_blocks,
            "weighted_corrections": weighted_corrections,
            "weighted_minimal_quotient_block": weighted_blocks,
        }
        args.emit_table.write_text(json.dumps(table, indent=2) + "\n")
        summary["table_written"] = str(args.emit_table)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
