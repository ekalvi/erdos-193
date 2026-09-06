#!/usr/bin/env python3
"""Bounded exact audit of routing-relevant signed-Gaussian family statistics.

For all 2**p sign words and the dyadic frame n=0,...,2**p-1, this checks:

* the Walsh-Hadamard modulation identity;
* exact pairwise same/opposite-port counts;
* per-rule four-port counts and endpoint displacement;
* synchronized aggregate port loads; and
* planar vertex reuse and direct-route stretch.

The exhaustive audit is deliberately capped at p <= 8, so it is a short,
single-process check rather than a long-running calculation.  It is finite
evidence for the accompanying exact derivations, not an infinite proof.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math

DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))


def sign_word(rule: int, period: int) -> tuple[int, ...]:
    """Use the gallery convention: the high rule bit is epsilon_0."""
    return tuple(
        -1 if rule & (1 << (period - 1 - place)) else 1
        for place in range(period)
    )


def bit_dot(rule: int, n: int, period: int) -> int:
    """Return r dot b(n) over F_2 in the gallery's bit ordering."""
    return sum(
        ((rule >> (period - 1 - place)) & 1) * ((n >> place) & 1)
        for place in range(period)
    ) & 1


def states_for(rule: int, period: int) -> tuple[int, ...]:
    signs = sign_word(rule, period)
    frame = 1 << period
    return tuple(
        sum(signs[place] * ((n >> place) & 1) for place in range(period)) % 4
        for n in range(frame)
    )


def vector_key(vector: tuple[int, ...]) -> str:
    return "(" + ",".join(map(str, vector)) + ")"


def require(condition: bool, *detail: object) -> None:
    """Keep verification active even when Python is invoked with ``-O``."""
    if not condition:
        raise AssertionError(detail)


def audit(period: int) -> dict[str, object]:
    frame = 1 << period
    schedules = [states_for(rule, period) for rule in range(frame)]
    base = schedules[0]

    port_count_vectors: Counter[tuple[int, ...]] = Counter()
    unique_vertex_counts: list[int] = []
    endpoints: list[tuple[int, int]] = []

    for rule, schedule in enumerate(schedules):
        counts = Counter(schedule)
        port_vector = tuple(counts[state] for state in range(4))
        port_count_vectors[port_vector] += 1

        x = y = 0
        visited = {(x, y)}
        for n, state in enumerate(schedule):
            expected = (
                base[n]
                if bit_dot(rule, n, period) == 0
                else (base[n] + 2) % 4
            )
            require(state == expected, "Walsh modulation", rule, n, state, expected)
            dx, dy = DIRECTIONS[state]
            x += dx
            y += dy
            visited.add((x, y))

        # Product_j (1 + i**epsilon_j) has squared modulus 2**period.
        require(x * x + y * y == frame, "endpoint norm", rule, x, y)
        # State parity is popcount(n) parity, so each opposite port pair gets
        # exactly half of every complete nontrivial dyadic frame.
        require(port_vector[0] + port_vector[2] == frame // 2, "even ports", rule)
        require(port_vector[1] + port_vector[3] == frame // 2, "odd ports", rule)
        require(port_vector[0] - port_vector[2] == x, "horizontal endpoint", rule)
        require(port_vector[1] - port_vector[3] == y, "vertical endpoint", rule)
        unique_vertex_counts.append(len(visited))
        endpoints.append((x, y))

    # A pair of rules depends only on its nonzero xor mask.  Verifying that
    # every such Walsh character is balanced proves the reported relation for
    # all frame * (frame - 1) / 2 rule pairs without a quadratic pair audit.
    expected_half = frame // 2
    for mask in range(1, frame):
        positive = sum(bit_dot(mask, n, period) == 0 for n in range(frame))
        require(positive == expected_half, "unbalanced Walsh character", mask)
    pair_count = frame * (frame - 1) // 2

    aggregate_loads: Counter[tuple[int, ...]] = Counter()
    for n in range(frame):
        aggregate_loads[
            tuple(sum(schedule[n] == state for schedule in schedules) for state in range(4))
        ] += 1

    return {
        "status": "finite exact audit; not an infinite proof or routing benchmark",
        "period": period,
        "rules": frame,
        "frame_slots": frame,
        "pairwise": {
            "nontrivial_walsh_characters_checked": frame - 1,
            "pairs_implied": pair_count,
            "same_port_slots_per_distinct_pair": expected_half,
            "opposite_port_slots_per_distinct_pair": expected_half,
            "perpendicular_port_slots_per_distinct_pair": 0,
            "signed_inner_product_per_distinct_pair": 0,
        },
        "per_rule": {
            "port_count_vector_histogram": {
                vector_key(key): value for key, value in sorted(port_count_vectors.items())
            },
            "endpoint_squared_distance_values": sorted(
                {x * x + y * y for x, y in endpoints}
            ),
            "unique_planar_vertices": {
                "minimum": min(unique_vertex_counts),
                "maximum": max(unique_vertex_counts),
            },
            "euclidean_stretch_at_frame_end": math.sqrt(frame),
        },
        "all_rules_synchronized": {
            "slot_load_vector_histogram": {
                vector_key(key): value for key, value in sorted(aggregate_loads.items())
            }
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--period",
        type=int,
        default=8,
        choices=range(1, 9),
        metavar="{1,...,8}",
        help="sign-word length and log2(frame size); capped at 8 (default: 8)",
    )
    args = parser.parse_args()
    print(json.dumps(audit(args.period), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
