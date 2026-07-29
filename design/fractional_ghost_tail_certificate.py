#!/usr/bin/env python3
"""Exact regression checks for FRACTIONAL-GHOST-TAIL.md.

The all-depth claims are algebraic proofs in the note.  ``--depth`` checks a
finite initial segment, including the pairwise lattice-line incidence matrix;
it must not be reported as the proof of the universal statement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
N = (
    (3, 0, 0),
    (0, -1, 3),
    (0, -3, 0),
)
M_INV = (
    (Fraction(1, 3), 0, 0),
    (0, Fraction(-1, 9), Fraction(1, 3)),
    (0, Fraction(-1, 3), 0),
)
H = (0, 1, 0)


def mat_vec(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def is_zero(vector):
    return all(value == 0 for value in vector)


def is_integral(vector):
    return all(Fraction(value).denominator == 1 for value in vector)


def canonical_json(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def run(depth):
    if depth < 2:
        raise ValueError("depth must be at least 2")

    # Exact inverse and norm identities.
    for basis in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        if mat_vec(M, mat_vec(M_INV, basis)) != basis:
            raise AssertionError("displayed M inverse is not exact")
        if mat_vec(M, mat_vec(N, basis)) != tuple(9 * x for x in basis):
            raise AssertionError("M*N != 9I")
    row_sums = tuple(sum(abs(value) for value in row) for row in M_INV)
    infinity_norm = max(row_sums)
    if infinity_norm != Fraction(4, 9):
        raise AssertionError("inverse infinity norm drift")
    control_radius = 8
    invariant_radius = Fraction(control_radius, 1) / (1 - infinity_norm)
    if invariant_radius != Fraction(72, 5):
        raise AssertionError("backward invariant radius drift")
    integral_sites = (2 * math.floor(invariant_radius) + 1) ** 3
    if integral_sites != 24_389:
        raise AssertionError("bounded integral-site count drift")

    # A minimal nonintegral ghost lying on an integer lattice line.
    elementary = mat_vec(M_INV, (1, 0, 0))
    if elementary != (Fraction(1, 3), 0, 0) or not is_zero(
        cross(elementary, (1, 0, 0))
    ):
        raise AssertionError("elementary fractional incidence drift")

    vectors = []
    ghosts = []
    vector = H
    ghost = tuple(Fraction(value) for value in H)
    for n in range(1, depth + 1):
        vector = mat_vec(N, vector)
        ghost = mat_vec(M_INV, ghost)
        expected = tuple(Fraction(value, 9**n) for value in vector)
        if ghost != expected:
            raise AssertionError("N^n/9^n ghost identity drift", n)
        if is_zero(ghost) or is_integral(ghost):
            raise AssertionError("fractional tail became zero/integral", n)
        if max(abs(value) for value in ghost) >= 1:
            raise AssertionError("fractional tail left the open unit cube", n)
        if not is_zero(cross(ghost, vector)):
            raise AssertionError("ghost missed its integer lattice line", n)
        vectors.append(vector)
        ghosts.append(ghost)

    incidence_rows = []
    for n, direction in enumerate(vectors):
        row = []
        for m, ghost_point in enumerate(ghosts):
            hit = is_zero(cross(ghost_point, direction))
            if hit != (m == n):
                raise AssertionError(
                    "finite incidence matrix is not the identity", n + 1, m + 1
                )
            row.append(int(hit))
        incidence_rows.append(row)

    trace = -1
    determinant = 9
    root_ratio_trace = Fraction(trace * trace - 2 * determinant, determinant)
    if root_ratio_trace != Fraction(-17, 9) or root_ratio_trace.denominator == 1:
        raise AssertionError("root-of-unity obstruction arithmetic drift")

    vector_digest = hashlib.sha256(canonical_json(vectors)).hexdigest()
    ghost_records = [
        [[value.numerator, value.denominator] for value in ghost_point]
        for ghost_point in ghosts
    ]
    ghost_digest = hashlib.sha256(canonical_json(ghost_records)).hexdigest()
    incidence_digest = hashlib.sha256(canonical_json(incidence_rows)).hexdigest()
    return {
        "status": "exact finite regression for an all-depth algebraic theorem",
        "depth_checked": depth,
        "matrix": [list(row) for row in M],
        "nine_times_inverse": [list(row) for row in N],
        "inverse_infinity_norm": [
            infinity_norm.numerator,
            infinity_norm.denominator,
        ],
        "control_radius": control_radius,
        "backward_invariant_radius": [
            invariant_radius.numerator,
            invariant_radius.denominator,
        ],
        "bounded_integral_spatial_sites": integral_sites,
        "root_ratio_u_plus_inverse": [
            root_ratio_trace.numerator,
            root_ratio_trace.denominator,
        ],
        "all_tested_ghosts_nonzero_nonintegral_and_in_open_unit_cube": True,
        "finite_lattice_line_incidence_matrix_is_identity": True,
        "direction_stream_sha256": vector_digest,
        "ghost_stream_sha256": ghost_digest,
        "incidence_matrix_sha256": incidence_digest,
        "proof_boundary": (
            "finite regression only; all-depth nonperiodicity follows from "
            "the rational non-algebraic-integer value -17/9"
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
