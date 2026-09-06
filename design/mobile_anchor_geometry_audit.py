#!/usr/bin/env python3
"""Audit local beacon-triangle conditioning in finite signed-family prefixes.

This is a bounded exact-integer geometry audit, not a localization simulator.
For every periodic sign rule of the requested period, it inspects triples of
lifted beacon positions whose pairwise Euclidean distances are at most the
chosen lattice-unit diameter.  It reports the rule maximizing the worst
(minimum) interior angle among those local triples.

The search is intentionally capped at period 8 (256 rules and 256 beacons).
All collinearity and sine-squared comparisons use integer arithmetic; floating
point is used only to render the final angles in degrees.  The result is safely
restartable by rerunning because the bounded audit has no partial output or
external state.

This metric does not establish coverage, ranging accuracy, 2D projection
quality, obstacle feasibility, or suitability for unconstrained 3D range-only
localization.  Physical anisotropic scaling changes angles and must be audited
separately.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

Point3 = tuple[int, int, int]

DIRECTIONS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (0, 1),
    (-1, 0),
    (0, -1),
)
CORNERS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
)


@dataclass(frozen=True)
class LocalAngleResult:
    rule: int
    triangle_count: int
    sine_squared_numerator: int
    sine_squared_denominator: int
    witness: tuple[int, int, int]

    @property
    def angle_degrees(self) -> float:
        ratio = self.sine_squared_numerator / self.sine_squared_denominator
        return math.degrees(math.asin(math.sqrt(min(1.0, ratio))))

    @property
    def exact_sine_squared(self) -> str:
        value = Fraction(
            self.sine_squared_numerator,
            self.sine_squared_denominator,
        )
        return f"{value.numerator}/{value.denominator}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--period",
        type=int,
        default=8,
        choices=range(1, 9),
        metavar="P",
        help="sign-rule period P; audits all 2^P rules (default: 8, maximum: 8)",
    )
    parser.add_argument(
        "--local-diameter",
        type=int,
        default=20,
        metavar="D",
        help=(
            "maximum pairwise distance of an audited triple in native lattice "
            "units (default: 20)"
        ),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="K",
        help="number of best-conditioned rules to report (default: 10)",
    )
    args = parser.parse_args()
    if args.local_diameter <= 0:
        parser.error("--local-diameter must be positive")
    if args.top <= 0:
        parser.error("--top must be positive")
    return args


def periodic_signs(rule: int, period: int) -> tuple[int, ...]:
    """Use the same displayed-bit convention as signed_gaussian_network_audit."""

    return tuple(
        -1 if rule & (1 << (period - 1 - index)) else 1
        for index in range(period)
    )


def gaussian_state(rule: int, period: int, n: int) -> int:
    signs = periodic_signs(rule, period)
    return sum(
        signs[index % period] * ((n >> index) & 1)
        for index in range(n.bit_length())
    ) % 4


def lifted_prefix(rule: int, period: int, count: int) -> list[Point3]:
    x = 0
    y = 0
    points: list[Point3] = []
    for n in range(count):
        state = gaussian_state(rule, period, n)
        corner_x, corner_y = CORNERS[state]
        points.append((2 * x + corner_x, 2 * y + corner_y, 4 * n + state))
        direction_x, direction_y = DIRECTIONS[state]
        x += direction_x
        y += direction_y
    return points


def squared_distance(left: Point3, right: Point3) -> int:
    return sum((left[axis] - right[axis]) ** 2 for axis in range(3))


def squared_cross_norm(first: Point3, second: Point3, third: Point3) -> int:
    ax = second[0] - first[0]
    ay = second[1] - first[1]
    az = second[2] - first[2]
    bx = third[0] - first[0]
    by = third[1] - first[1]
    bz = third[2] - first[2]
    cx = ay * bz - az * by
    cy = az * bx - ax * bz
    cz = ax * by - ay * bx
    return cx * cx + cy * cy + cz * cz


def audit_rule(
    rule: int,
    period: int,
    points: Sequence[Point3],
    local_diameter: int,
) -> LocalAngleResult | None:
    diameter_squared = local_diameter * local_diameter
    best_numerator: int | None = None
    best_denominator = 1
    best_witness = (0, 0, 0)
    triangle_count = 0

    for first_index, first in enumerate(points):
        candidates: list[tuple[int, int]] = []
        for second_index in range(first_index + 1, len(points)):
            second = points[second_index]
            # Height is strictly increasing by positive integer increments.
            # Once this gap exceeds the diameter, all later points are too far.
            if second[2] - first[2] > local_diameter:
                break
            distance = squared_distance(first, second)
            if distance <= diameter_squared:
                candidates.append((second_index, distance))

        for offset, (second_index, first_second_squared) in enumerate(candidates):
            second = points[second_index]
            for third_index, first_third_squared in candidates[offset + 1 :]:
                third = points[third_index]
                second_third_squared = squared_distance(second, third)
                if second_third_squared > diameter_squared:
                    continue

                triangle_count += 1
                cross_squared = squared_cross_norm(first, second, third)
                if cross_squared == 0:
                    raise AssertionError(
                        ("collinear lifted triple", rule, first_index, second_index, third_index)
                    )

                # The doubled area is shared by all three angle formulas.  The
                # smallest angle has the smallest sine, hence the largest
                # product of its two adjacent squared side lengths.
                denominator = max(
                    first_second_squared * first_third_squared,
                    first_second_squared * second_third_squared,
                    first_third_squared * second_third_squared,
                )
                if (
                    best_numerator is None
                    or cross_squared * best_denominator
                    < best_numerator * denominator
                ):
                    best_numerator = cross_squared
                    best_denominator = denominator
                    best_witness = (first_index, second_index, third_index)

    if best_numerator is None:
        return None
    return LocalAngleResult(
        rule=rule,
        triangle_count=triangle_count,
        sine_squared_numerator=best_numerator,
        sine_squared_denominator=best_denominator,
        witness=best_witness,
    )


def render_rule(result: LocalAngleResult, period: int) -> dict[str, object]:
    return {
        "rule": result.rule,
        "sign_word": "".join(
            "+" if sign == 1 else "-"
            for sign in periodic_signs(result.rule, period)
        ),
        "local_triangle_count": result.triangle_count,
        "minimum_interior_angle_degrees": round(result.angle_degrees, 9),
        "minimum_sine_squared_exact": result.exact_sine_squared,
        "witness_indices": list(result.witness),
    }


def main() -> None:
    args = parse_args()
    count = 1 << args.period
    results: list[LocalAngleResult] = []
    for rule in range(count):
        result = audit_rule(
            rule,
            args.period,
            lifted_prefix(rule, args.period, count),
            args.local_diameter,
        )
        if result is not None:
            results.append(result)

    if not results:
        raise SystemExit(
            "no three beacon positions fit the requested local diameter; "
            "increase --local-diameter"
        )

    ordered = sorted(
        results,
        key=lambda result: Fraction(
            result.sine_squared_numerator,
            result.sine_squared_denominator,
        ),
        reverse=True,
    )
    ascending = list(reversed(ordered))
    median = ascending[len(ascending) // 2]
    rule_zero = next((result for result in results if result.rule == 0), None)

    output = {
        "status": "finite local-geometry evidence, not a localization guarantee",
        "configuration": {
            "period": args.period,
            "rules": count,
            "beacons_per_rule": count,
            "local_pairwise_diameter_lattice_units": args.local_diameter,
        },
        "rules_with_at_least_one_local_triangle": len(results),
        "best_rules": [
            render_rule(result, args.period)
            for result in ordered[: min(args.top, len(ordered))]
        ],
        "median_rule_by_worst_local_angle": render_rule(median, args.period),
        "worst_rule": render_rule(ascending[0], args.period),
        "constant_positive_rule": (
            render_rule(rule_zero, args.period) if rule_zero is not None else None
        ),
        "caveats": [
            "the distance and angle metric uses the native isotropic 3D lattice",
            "a receiver seeing three beacons requires a separate coverage test",
            "physical anisotropic scaling changes every reported angle",
            "three non-collinear anchors do not solve unconstrained 3D range-only localization",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
