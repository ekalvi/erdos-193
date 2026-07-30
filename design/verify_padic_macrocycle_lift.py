#!/usr/bin/env python3
"""Independently verify padic_macrocycle_lift.py's compact certificate.

This verifier intentionally does not import the explorer.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct


SCHEMA_VERSION = 1
DEFAULT_INPUT = Path("design/padic-macrocycle-lift-summary.json")
EXPLORER = Path(__file__).with_name("padic_macrocycle_lift.py")

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
CONTROL = (-4, -4, -3)
REVEAL = (-2, -2, -2)
P_NUMERATOR = (-99, -78, -62)
P_DENOMINATOR = 22
H = (55, 34, 18)
PHASE_16_DIRECTION = (165, -20, 102)


def add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def scale(factor, vector):
    return tuple(factor * coordinate for coordinate in vector)


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def determinant(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def cofactor(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return (
        (e * i - f * h, f * g - d * i, d * h - e * g),
        (c * h - b * i, a * i - c * g, b * g - a * h),
        (b * f - c * e, c * d - a * f, a * e - b * d),
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def content(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    return divisor


def canonical_primitive(vector):
    divisor = content(vector)
    if divisor == 0:
        raise AssertionError("zero direction")
    primitive = tuple(coordinate // divisor for coordinate in vector)
    if next(coordinate for coordinate in primitive if coordinate) < 0:
        primitive = scale(-1, primitive)
    return primitive


def inverse_m(vector):
    x, y, z = vector
    return (
        Fraction(x, 3),
        Fraction(3 * z - y, 9),
        Fraction(-y, 3),
    )


def stable_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def capped_v3(value, cap):
    if value == 0:
        return cap
    valuation = 0
    while valuation < cap and value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation

def exact_v3(value):
    if value == 0:
        raise ValueError("infinite 3-adic valuation")
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def lateral_q(direction):
    _, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def normalization_data():
    counts = Counter()
    digest = hashlib.sha256()
    for x in range(9):
        for y in range(9):
            for z in range(9):
                if x % 3 == y % 3 == z % 3 == 0:
                    continue
                image = matrix_vector(M, (x, y, z))
                branch = 3 ** min(capped_v3(value, 3) for value in image)
                formula_branch = (
                    1
                    if z % 3
                    else 9
                    if x % 3 == 0 and (z - 3 * y) % 9 == 0
                    else 3
                )
                if branch != formula_branch:
                    raise AssertionError("normalization formula failed", (x, y, z))
                counts[branch] += 1
                digest.update(struct.pack(">4I", x, y, z, branch))
    return {
        "primitive_residue_classes": sum(counts.values()),
        "branch_counts": {str(key): counts[key] for key in sorted(counts)},
        "assignment_sha256": digest.hexdigest(),
    }


def contact_valuation(direction, projective, k):
    return min(capped_v3(value, k) for value in cross(direction, projective))


def edge(x, z, modulus):
    middle = (-8 - 3 * z) % modulus
    inverse = pow(middle, -1, modulus)
    return 9 * x * inverse % modulus, (3 - 9 * z) * inverse % modulus


def projective_state(direction, modulus):
    if direction[1] % 3 == 0:
        raise AssertionError("latent direction left y-unit chart")
    inverse = pow(direction[1] % modulus, -1, modulus)
    return direction[0] * inverse % modulus, direction[2] * inverse % modulus


def graph_stats(edges):
    indegree = [0] * len(edges)
    for target in edges:
        indegree[target] += 1
    indegree_counts = Counter(indegree)
    work = indegree[:]
    queue = deque(index for index, degree in enumerate(work) if degree == 0)
    while queue:
        source = queue.popleft()
        target = edges[source]
        work[target] -= 1
        if work[target] == 0:
            queue.append(target)

    cycle_counts = Counter()
    visited = set()
    for start, degree in enumerate(work):
        if degree == 0 or start in visited:
            continue
        current = start
        length = 0
        while current not in visited:
            visited.add(current)
            length += 1
            current = edges[current]
        cycle_counts[length] += 1
    return (
        len(set(edges)),
        {str(key): indegree_counts[key] for key in sorted(indegree_counts)},
        {str(key): cycle_counts[key] for key in sorted(cycle_counts)},
    )


def verify_precision(record):
    k = record["k"]
    modulus = 3**k
    if record["modulus"] != modulus or record["state_count"] != modulus * modulus:
        raise AssertionError("precision dimensions drift", k)

    edges = [0] * (modulus * modulus)
    digest = hashlib.sha256()
    valuations = Counter()
    hits_8 = 0
    hits_16 = 0
    for x in range(modulus):
        for z in range(modulus):
            next_x, next_z = edge(x, z, modulus)
            index = x * modulus + z
            edges[index] = next_x * modulus + next_z
            direction = (x, 1, z)
            value_8 = contact_valuation(H, direction, k)
            value_16 = contact_valuation(PHASE_16_DIRECTION, direction, k)
            valuations[(value_8, value_16)] += 1
            hits_8 += value_8 == k
            hits_16 += value_16 == k
            digest.update(struct.pack(">7I", k, x, z, next_x, next_z, value_8, value_16))

    if digest.hexdigest() != record["state_edge_sha256"]:
        raise AssertionError("state-edge digest mismatch", k)
    expected_valuations = {
        f"{left},{right}": valuations[(left, right)]
        for left, right in sorted(valuations)
    }
    if expected_valuations != record["contact_valuation_pair_histogram"]:
        raise AssertionError("contact valuation histogram mismatch", k)
    if (hits_8, hits_16) != (
        record["phase_8_projective_contact_classes"],
        record["phase_16_projective_contact_classes"],
    ):
        raise AssertionError("contact class count mismatch", k)

    image_count, indegree_histogram, cycle_histogram = graph_stats(edges)
    if image_count != record["image_states"]:
        raise AssertionError("image count mismatch", k)
    if indegree_histogram != record["indegree_histogram"]:
        raise AssertionError("indegree histogram mismatch", k)
    if cycle_histogram != record["cycle_length_histogram"]:
        raise AssertionError("cycle histogram mismatch", k)

    fixed = [index for index, target in enumerate(edges) if index == target]
    if len(fixed) != 1:
        raise AssertionError("finite residue graph lacks unique fixed state", k)
    expected_fixed = [fixed[0] // modulus, fixed[0] % modulus]
    latent = record["latent_orbit"]
    if latent["fixed_state_xz_with_y_equal_1"] != expected_fixed:
        raise AssertionError("fixed-state record mismatch", k)

    direction = H
    states = []
    while True:
        state = list(projective_state(direction, modulus))
        states.append(state)
        if state == expected_fixed:
            break
        if len(states) > k + 3:
            raise AssertionError("latent residue orbit failed to collapse", k)
        direction = matrix_vector(N_SQUARED, direction)
    if states != latent["states_through_collapse"]:
        raise AssertionError("latent collapse path mismatch", k)
    if len(states) - 1 != latent["collapse_depth"]:
        raise AssertionError("latent collapse depth mismatch", k)


def integer_moment(direction):
    numerator = cross(P_NUMERATOR, direction)
    if any(value % P_DENOMINATOR for value in numerator):
        raise AssertionError("nonintegral latent moment")
    return tuple(value // P_DENOMINATOR for value in numerator)


def latent_record_stream(depth):
    directions = [H]
    for _ in range(depth):
        directions.append(matrix_vector(N_SQUARED, directions[-1]))
    digest = hashlib.sha256()
    records = []
    for n, direction in enumerate(directions):
        if canonical_primitive(direction) != direction:
            raise AssertionError("imprimitive latent direction", n)
        moment = integer_moment(direction)
        residual_8 = subtract(cross(REVEAL, direction), moment)
        residual_16 = cross(PHASE_16_DIRECTION, direction)
        q_value = lateral_q(direction)
        x_valuation = exact_v3(direction[0])
        q_valuation = exact_v3(q_value)
        padic_depth = min(x_valuation // 2, (q_valuation - 1) // 4)
        record = {
            "n": n,
            "direction": list(direction),
            "moment": list(moment),
            "direction_x_v3": x_valuation,
            "lateral_q": q_value,
            "lateral_q_v3": q_valuation,
            "latent_padic_depth": padic_depth,
            "phase_8_hit": residual_8 == (0, 0, 0),
            "phase_16_direction_hit": residual_16 == (0, 0, 0),
            "phase_8_residual_min_v3_capped_64": min(
                capped_v3(value, 64) for value in residual_8
            ),
            "phase_16_residual_min_v3_capped_64": min(
                capped_v3(value, 64) for value in residual_16
            ),
        }
        if record["phase_8_hit"] != (n == 0) or record["phase_16_direction_hit"]:
            raise AssertionError("latent contact record drift", n)
        if (
            x_valuation != 2 * n
            or q_valuation != 4 * n + 1
            or padic_depth != n
        ):
            raise AssertionError("latent 3-adic depth formula drift", n)
        if n:
            previous = directions[n - 1]
            image = matrix_vector(A, direction)
            divisor = content(image)
            if divisor != 81 or canonical_primitive(image) != previous:
                raise AssertionError("macro direction countdown drift", n)
            first = matrix_vector(M, direction)
            middle = canonical_primitive(first)
            if (content(first), content(matrix_vector(M, middle))) != (9, 9):
                raise AssertionError("normalization countdown drift", n)
            transported = add(
                matrix_vector(COFACTOR_A, moment),
                cross(TRANSLATION, image),
            )
            if any(value % divisor for value in transported):
                raise AssertionError("moment transport divisibility drift", n)
            normalized = tuple(value // divisor for value in transported)
            if normalized != integer_moment(previous):
                raise AssertionError("moment countdown drift", n)
        digest.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode())
        records.append(record)
    return records, digest.hexdigest()


def verify_contact_model(payload):
    if determinant(M) != 27 or determinant(N) != 27:
        raise AssertionError("base determinant drift")
    if matrix_product(M, N) != ((9, 0, 0), (0, 9, 0), (0, 0, 9)):
        raise AssertionError("base inverse identity drift")
    if matrix_product(A, N_SQUARED) != ((81, 0, 0), (0, 81, 0), (0, 0, 81)):
        raise AssertionError("macro inverse identity drift")
    if add(matrix_vector(A, P_NUMERATOR), scale(P_DENOMINATOR, TRANSLATION)) != P_NUMERATOR:
        raise AssertionError("fixed point identity drift")
    if subtract(scale(P_DENOMINATOR, REVEAL), P_NUMERATOR) != H:
        raise AssertionError("reveal direction identity drift")

    basis = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    for left in basis:
        for right in basis:
            if cross(matrix_vector(A, left), matrix_vector(A, right)) != matrix_vector(
                COFACTOR_A, cross(left, right)
            ):
                raise AssertionError("cofactor cross identity drift")

    test_vectors = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (1, 0, 1),
        (0, 1, 1),
    )
    for vector in test_vectors:
        if lateral_q(matrix_vector(N_SQUARED, vector)) != 81 * lateral_q(vector):
            raise AssertionError("lateral quadratic identity drift")

    model = payload["contact_model"]
    macro = model["macro_map"]
    if macro["A"] != [list(row) for row in A] or macro["b"] != list(TRANSLATION):
        raise AssertionError("macro map payload mismatch")
    expected_pullback = add(tuple(map(Fraction, CONTROL)), inverse_m(inverse_m(REVEAL)))
    expected_record = [[value.numerator, value.denominator] for value in expected_pullback]
    if model["phase_8_reveal_pullback"] != expected_record:
        raise AssertionError("reveal pullback mismatch")
    padic_chart = model["padic_inverse_direction_chart"]
    if padic_chart["homogeneous_polynomial"] != "q(g)=3g_y^2-g_y*g_z+3g_z^2":
        raise AssertionError("unexpected 3-adic homogeneous polynomial")


def verify(path):
    with Path(path).open() as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("unsupported schema")
    claimed_hash = payload.get("payload_sha256")
    mathematical_payload = dict(payload)
    mathematical_payload.pop("payload_sha256", None)
    if stable_hash(mathematical_payload) != claimed_hash:
        raise AssertionError("payload hash mismatch")

    if payload["explorer"]["logical_path"] != "design/padic_macrocycle_lift.py":
        raise AssertionError("unexpected explorer logical path")
    if file_sha256(EXPLORER) != payload["explorer"]["sha256"]:
        raise AssertionError("explorer source hash mismatch")

    expected_constants = {
        "M": [list(row) for row in M],
        "N": [list(row) for row in N],
        "N_squared": [list(row) for row in N_SQUARED],
        "H": list(H),
        "phase_16_direction": list(PHASE_16_DIRECTION),
    }
    if payload["constants"] != expected_constants:
        raise AssertionError("constant payload mismatch")

    estimate_payload = payload["estimate"]
    max_k = estimate_payload["max_k"]
    expected_precisions = [
        {"k": k, "modulus": 3**k, "states": 9**k}
        for k in range(1, max_k + 1)
    ]
    if estimate_payload["precisions"] != expected_precisions:
        raise AssertionError("estimate precision table mismatch")
    if estimate_payload["total_state_edges"] != sum(9**k for k in range(1, max_k + 1)):
        raise AssertionError("estimate total mismatch")

    observed_normalization = normalization_data()
    normalization = payload["normalization"]
    for key, value in observed_normalization.items():
        if normalization[key] != value:
            raise AssertionError("normalization certificate mismatch", key)

    verify_contact_model(payload)
    precisions = payload["precisions"]
    if [record["k"] for record in precisions] != list(range(1, max_k + 1)):
        raise AssertionError("precision coverage is not contiguous")
    for record in precisions:
        verify_precision(record)

    latent = payload["latent_positive_control"]
    records, digest = latent_record_stream(latent["depth"])
    if latent["record_count"] != len(records):
        raise AssertionError("latent record count mismatch")
    if latent["record_stream_sha256"] != digest:
        raise AssertionError("latent record digest mismatch")
    if latent["first_record"] != records[0] or latent["last_record"] != records[-1]:
        raise AssertionError("latent boundary record mismatch")

    return {
        "status": "verified",
        "input": str(path),
        "payload_sha256": claimed_hash,
        "precisions": len(precisions),
        "total_state_edges": estimate_payload["total_state_edges"],
        "latent_depth": latent["depth"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    print(json.dumps(verify(args.input), sort_keys=True))


A = matrix_product(M, M)
N_SQUARED = matrix_product(N, N)
COFACTOR_A = cofactor(A)
TRANSLATION = scale(-1, matrix_vector(A, CONTROL))


if __name__ == "__main__":
    main()
