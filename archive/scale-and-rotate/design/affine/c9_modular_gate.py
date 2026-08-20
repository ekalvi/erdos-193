#!/usr/bin/env python3
"""Independent exact audit of the coefficient-nine modular certificate gate.

This checker deliberately does not import ``affine_recurrence.py``.  Starting
only from Lidbetter's seven-uniform morphism, it reconstructs the 12-state
mod-27 and 360-state mod-243 correction quotients, checks their formulas against
a directly generated walk, and decides the natural mod-27 SCC gate.

The optional staged graph has 787,320 states.  Keep the run to one low-priority
core, for example:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/affine/c9_modular_gate.py --staged

The result is an obstruction to a fixed-modulus SCC proof, not an
unconditional triple-freeness theorem for the C=9 walk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path


MU = (
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


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(coefficient, vector):
    return tuple(coefficient * x for x in vector)


def delta(symbol):
    out = [-1, -1, -1]
    out[symbol % 3] = 2
    return tuple(out)


def g(symbol, digit):
    out = (0, 0, 0)
    for child in MU[symbol][:digit]:
        out = add(out, delta(child))
    return out


def h27(state, digit):
    # 9*g_2 = -18*d*1 (mod 27), while 81*g_5 vanishes.
    return tuple((x - 18 * digit) % 27 for x in g(state, digit))


def transition27(state, digit):
    return MU[state][digit]


def g2(state, digit):
    # state = (lambda_t, lambda_(2t), lambda_(2t+1)).
    _, b0, b1 = state
    pair = (b0, b1)
    quotient, remainder = divmod(2 * digit, 7)
    shift = (0, 0, 0)
    for offset in range(quotient):
        shift = add(shift, delta(pair[offset]))
    return add(scale(4, shift), g(pair[quotient], remainder))


def h243(state, digit):
    # 81*g_5 = -405*d*1 = -162*d*1 (mod 243).
    return tuple(
        (x + 9 * y - 162 * digit) % 243
        for x, y in zip(g(state[0], digit), g2(state, digit))
    )


def transition243(state, digit):
    a, b0, b1 = state
    pair = (b0, b1)

    def child(offset):
        quotient, remainder = divmod(2 * digit + offset, 7)
        return MU[pair[quotient]][remainder]

    return MU[a][digit], child(0), child(1)


def reachable(start, transition):
    states = [start]
    ids = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for digit in range(7):
            child = transition(state, digit)
            if child not in ids:
                ids[child] = len(states)
                states.append(child)
                queue.append(child)
    return states, ids


def correction_table(modulus, states, ids, transition, correction):
    transitions = []
    corrections = []
    for state in states:
        transitions.append([ids[transition(state, digit)] for digit in range(7)])
        corrections.append([correction(state, digit) for digit in range(7)])
    output_rows = {tuple(row) for row in corrections}
    assert len(output_rows) == len(states)
    return {
        "modulus": modulus,
        "states": states,
        "transitions": transitions,
        "corrections": corrections,
        "reachable_states": len(states),
        "distinct_output_rows": len(output_rows),
        "distinct_correction_vectors": len(
            {value for row in corrections for value in row}
        ),
        "minimality_witness": "every state has a distinct seven-output row",
    }


def fixed_prefix(length):
    word = [0]
    while len(word) < length:
        word = [child for symbol in word for child in MU[symbol]]
    return word[:length]


def direct_walk(max_index):
    symbols = fixed_prefix(5 * max_index + 2)
    walk = [(0, 0, 0)]
    for symbol in symbols:
        point = list(walk[-1])
        point[symbol % 3] += 1
        walk.append(tuple(point))

    def v(index):
        return tuple(3 * coordinate - index for coordinate in walk[index])

    def z(index):
        blocks = v(index), v(2 * index), v(5 * index)
        return tuple(
            blocks[0][coordinate]
            + 9 * blocks[1][coordinate]
            + 81 * blocks[2][coordinate]
            for coordinate in range(3)
        )

    return symbols, z


def direct_cross_check(limit, ids27, ids243):
    symbols, z = direct_walk(7 * limit + 6)
    for index in range(limit + 1):
        state27 = symbols[index]
        state243 = symbols[index], symbols[2 * index], symbols[2 * index + 1]
        assert state27 in ids27
        assert state243 in ids243
        for digit in range(7):
            raw = tuple(
                z(7 * index + digit)[coordinate] - 4 * z(index)[coordinate]
                for coordinate in range(3)
            )
            assert tuple(value % 27 for value in raw) == h27(state27, digit)
            assert tuple(value % 243 for value in raw) == h243(state243, digit)
    return 7 * (limit + 1)


def defect(z, indices):
    x, y, end = indices
    left_gap = y - x
    right_gap = end - y
    return tuple(
        right_gap * (z(y)[coordinate] - z(x)[coordinate])
        - left_gap * (z(end)[coordinate] - z(y)[coordinate])
        for coordinate in range(3)
    )


def modular_witnesses():
    _symbols, z = direct_walk(36)
    cases = []
    for modulus, indices, parents, expected in (
        (27, (2, 3, 4), None, (-486, 459, 27)),
        (27, (0, 7, 36), (0, 1, 5), None),
        (243, (4, 10, 22), (0, 1, 3), (21384, -25272, 3888)),
    ):
        value = defect(z, indices)
        if expected is not None:
            assert value == expected
        assert all(coordinate % modulus == 0 for coordinate in value)
        record = {
            "modulus": modulus,
            "indices": list(indices),
            "defect": list(value),
        }
        if parents is not None:
            parent_value = defect(z, parents)
            assert any(coordinate % modulus for coordinate in parent_value)
            record["base7_parents"] = list(parents)
            record["parent_defect"] = list(parent_value)
            record["zero_not_prefix_closed"] = True
        cases.append(record)
    return cases


def graph_digest(states, rows):
    digest = hashlib.sha256()
    for state, row in zip(states, rows):
        digest.update(repr((state, tuple(row))).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def strongly_connected_lift(start, transition):
    states, ids = reachable(start, transition)
    rows = []
    reverse = [[] for _ in states]
    for state_id, state in enumerate(states):
        row = []
        for digit in range(7):
            child = ids[transition(state, digit)]
            row.append(child)
            reverse[child].append(state_id)
        rows.append(row)

    coaccessible = {0}
    queue = [0]
    while queue:
        child = queue.pop()
        for parent in reverse[child]:
            if parent not in coaccessible:
                coaccessible.add(parent)
                queue.append(parent)
    assert len(coaccessible) == len(states)
    assert transition(start, 0) == start
    return {
        "states": len(states),
        "edges": 7 * len(states),
        "strongly_connected": True,
        "start_has_digit_zero_self_loop": True,
        "primitive": True,
        "state_edge_sha256": graph_digest(states, rows),
    }


def mod27_lift():
    start = (0, 0, (0, 0, 0))

    def transition(state, digit):
        residue, symbol, value = state
        return (
            (7 * residue + digit) % 27,
            transition27(symbol, digit),
            tuple(
                (4 * value[coordinate] + h27(symbol, digit)[coordinate]) % 27
                for coordinate in range(3)
            ),
        )

    result = strongly_connected_lift(start, transition)
    result["state"] = "(t mod 27, lambda_t, Z_t mod 27)"
    result["product_consequence"] = (
        "the independent three-endpoint product has no SCC-only modular-zero separator"
    )
    return result


def staged_mod27_lift():
    start = (0, (0, 0, 4), (0, 0, 0))

    def transition(state, digit):
        residue, quotient_state, value = state
        correction = h27(quotient_state[0], digit)
        return (
            (7 * residue + digit) % 27,
            transition243(quotient_state, digit),
            tuple(
                (4 * value[coordinate] + correction[coordinate]) % 27
                for coordinate in range(3)
            ),
        )

    result = strongly_connected_lift(start, transition)
    result["state"] = "(t mod 27, q_243(t), Z_t mod 27)"
    result["interpretation"] = (
        "all 360 future-correction classes still create no SCC invariant before values lift"
    )
    return result


def mod243_depth_profile(depth):
    start = (0, (0, 0, 4), (0, 0, 0))

    def transition(state, digit):
        residue, quotient_state, value = state
        correction = h243(quotient_state, digit)
        return (
            (7 * residue + digit) % 243,
            transition243(quotient_state, digit),
            tuple(
                (4 * value[coordinate] + correction[coordinate]) % 243
                for coordinate in range(3)
            ),
        )

    layer = {start}
    counts = []
    for _ in range(depth):
        layer = {
            transition(state, digit)
            for state in layer
            for digit in range(7)
        }
        counts.append(len(layer))
    return {
        "depth": depth,
        "reachable_layer_counts": counts,
        "full_word_counts": [7 ** exponent for exponent in range(1, depth + 1)],
        "interpretation": "prefix lift is near-injective; no eventual SCC claim",
    }


def compact(table):
    return {
        key: value
        for key, value in table.items()
        if key not in {"states", "transitions", "corrections"}
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-prefix", type=int, default=1000)
    parser.add_argument(
        "--staged", action="store_true", help="also check the 787,320-state staged lift"
    )
    parser.add_argument(
        "--mod243-depth", type=int, default=0, help="optional exact prefix-depth profile"
    )
    parser.add_argument("--full-tables", action="store_true")
    args = parser.parse_args()
    if not __debug__:
        raise SystemExit("certificate assertions require normal Python; do not use -O")
    if args.mod243_depth < 0:
        raise SystemExit("--mod243-depth must be nonnegative")

    states27, ids27 = reachable(0, transition27)
    states243, ids243 = reachable((0, 0, 4), transition243)
    table27 = correction_table(27, states27, ids27, transition27, h27)
    table243 = correction_table(243, states243, ids243, transition243, h243)
    assert len(states27) == 12
    assert len(states243) == 360
    assert table27["distinct_correction_vectors"] == 31
    assert table243["distinct_correction_vectors"] == 325

    payload = {
        "status": "exact modular quotients; fixed-modulus SCC gate refuted",
        "checker_sha256": hashlib.sha256(
            Path(__file__).resolve().read_bytes()
        ).hexdigest(),
        "coefficient": 9,
        "base": 7,
        "mod27": table27 if args.full_tables else compact(table27),
        "mod243": table243 if args.full_tables else compact(table243),
        "direct_recurrence_checks": direct_cross_check(
            args.verify_prefix, ids27, ids243
        ),
        "modular_witnesses": modular_witnesses(),
        "mod27_single_index_lift": mod27_lift(),
        "staged_mod27_lift": staged_mod27_lift() if args.staged else "not requested",
        "mod243_depth_profile": (
            mod243_depth_profile(args.mod243_depth)
            if args.mod243_depth
            else "not requested"
        ),
        "soundness_warning": (
            "modular zero is not prefix-closed; quotients are filters, not a zero-language invariant"
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["canonical_payload_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
