#!/usr/bin/env python3
"""Bounded 3-adic lift graph for the latent 8 -> 16 -> 8 macrocycle.

This is a conjecture generator and regression certificate.  It checks exact
line transport, the primitive-normalization split, and finite projective
residue graphs.  It does not prove reachable line birth, finite index, or an
unconditional result for Erdos #193.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time


SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path("/tmp/padic-macrocycle-lift-summary.json")
DEFAULT_CHECKPOINT = Path("/tmp/padic-macrocycle-lift-checkpoint.json")
DEFAULT_STATE_BUDGET = 1_000_000

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
CONTROL = (-4, -4, -3)
REVEAL = (-2, -2, -2)
P_NUMERATOR = (-99, -78, -62)
P_DENOMINATOR = 22
H = (55, 34, 18)
PHASE_16_DIRECTION = (165, -20, 102)


class TimeBudgetExpired(RuntimeError):
    """The current precision was discarded at a deterministic boundary."""


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
        raise ValueError("zero vector has no primitive direction")
    primitive = tuple(coordinate // divisor for coordinate in vector)
    first = next(coordinate for coordinate in primitive if coordinate)
    return scale(-1, primitive) if first < 0 else primitive


def inverse_m(vector):
    x, y, z = vector
    return (
        Fraction(x, 3),
        Fraction(3 * z - y, 9),
        Fraction(-y, 3),
    )


def fraction_vector_record(vector):
    return [[coordinate.numerator, coordinate.denominator] for coordinate in vector]


def stable_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json_dump(payload, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, prefix=path.name + ".", delete=False
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def estimate(max_k, state_budget):
    if max_k < 1:
        raise ValueError("max-k must be positive")
    precisions = []
    for k in range(1, max_k + 1):
        modulus = 3**k
        precisions.append({
            "k": k,
            "modulus": modulus,
            "states": modulus * modulus,
        })
    maximum_states = precisions[-1]["states"]
    return {
        "max_k": max_k,
        "precisions": precisions,
        "total_state_edges": sum(item["states"] for item in precisions),
        "maximum_single_precision_states": maximum_states,
        "state_budget": state_budget,
        "within_budget": maximum_states <= state_budget,
    }


def normalization_certificate():
    branch_counts = Counter()
    digest = hashlib.sha256()
    modulus = 9
    for x in range(modulus):
        for y in range(modulus):
            for z in range(modulus):
                if x % 3 == 0 and y % 3 == 0 and z % 3 == 0:
                    continue
                image = matrix_vector(M, (x, y, z))
                valuation = min(capped_v3(value, 3) for value in image)
                branch = 3**valuation
                if branch not in (1, 3, 9):
                    raise AssertionError("unexpected normalization branch", (x, y, z), branch)
                expected = (
                    1
                    if z % 3
                    else 9
                    if x % 3 == 0 and (z - 3 * y) % 9 == 0
                    else 3
                )
                if branch != expected:
                    raise AssertionError("normalization residue formula drift")
                branch_counts[branch] += 1
                digest.update(struct.pack(">4I", x, y, z, branch))
    if sum(branch_counts.values()) != 9**3 - 3**3:
        raise AssertionError("primitive residue count drift")
    return {
        "residue_modulus": modulus,
        "primitive_residue_classes": 9**3 - 3**3,
        "branch_counts": {str(key): branch_counts[key] for key in sorted(branch_counts)},
        "assignment_sha256": digest.hexdigest(),
        "branch_formula": {
            "t=1": "z is nonzero modulo 3",
            "t=9": "x=0 modulo 3 and z=3y modulo 9",
            "t=3": "z=0 modulo 3 and the t=9 condition fails",
        },
        "all_integer_proof": (
            "For primitive g, gcd(Mg) divides det(M)=27 by the adjugate identity. "
            "Divisibility by 27 would force 9|g_x, 9|g_z, and 3|g_y, "
            "contradicting primitivity; the residue formula distinguishes 1,3,9."
        ),
    }


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
        raise ValueError("the 3-adic valuation of zero is infinite")
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def lateral_q(direction):
    _, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def contact_valuation(direction, projective, k):
    residual = cross(direction, projective)
    return min(capped_v3(coordinate, k) for coordinate in residual)


def projective_y_state(direction, modulus):
    if direction[1] % 3 == 0:
        raise ValueError("the y-coordinate is not a 3-adic unit")
    inverse = pow(direction[1] % modulus, -1, modulus)
    return (
        direction[0] * inverse % modulus,
        direction[2] * inverse % modulus,
    )


def inverse_lift_edge(x, z, modulus):
    # N^2(x,1,z) = (9x,-8-3z,3-9z).  The middle coordinate is a unit.
    middle = (-8 - 3 * z) % modulus
    inverse = pow(middle, -1, modulus)
    return (
        9 * x * inverse % modulus,
        (3 - 9 * z) * inverse % modulus,
    )


def functional_graph_stats(edges):
    indegree = [0] * len(edges)
    for target in edges:
        indegree[target] += 1
    indegree_histogram = Counter(indegree)

    remaining_indegree = indegree[:]
    queue = deque(index for index, degree in enumerate(remaining_indegree) if degree == 0)
    while queue:
        source = queue.popleft()
        target = edges[source]
        remaining_indegree[target] -= 1
        if remaining_indegree[target] == 0:
            queue.append(target)

    cycle_histogram = Counter()
    visited = set()
    for start, degree in enumerate(remaining_indegree):
        if degree == 0 or start in visited:
            continue
        length = 0
        current = start
        while current not in visited:
            visited.add(current)
            length += 1
            current = edges[current]
        cycle_histogram[length] += 1

    return {
        "image_states": len(set(edges)),
        "indegree_histogram": {
            str(key): indegree_histogram[key] for key in sorted(indegree_histogram)
        },
        "cycle_length_histogram": {
            str(key): cycle_histogram[key] for key in sorted(cycle_histogram)
        },
    }


def latent_collapse_record(k, modulus, edges):
    fixed_indices = [index for index, target in enumerate(edges) if index == target]
    if len(fixed_indices) != 1:
        raise AssertionError("expected one finite-modulus fixed state", k, fixed_indices)
    fixed_index = fixed_indices[0]
    fixed_state = [fixed_index // modulus, fixed_index % modulus]

    direction = H
    states = []
    for depth in range(k + 3):
        state = projective_y_state(direction, modulus)
        states.append(list(state))
        if state == tuple(fixed_state):
            break
        direction = matrix_vector(N_SQUARED, direction)
    else:
        raise AssertionError("latent orbit did not reach the finite-modulus fixed state", k)

    for left, right in zip(states, states[1:]):
        source = left[0] * modulus + left[1]
        target = edges[source]
        if target != right[0] * modulus + right[1]:
            raise AssertionError("latent orbit disagrees with the residue graph", k)

    return {
        "fixed_state_xz_with_y_equal_1": fixed_state,
        "collapse_depth": len(states) - 1,
        "states_through_collapse": states,
    }


def compute_precision(k, stop_requested, progress):
    modulus = 3**k
    state_count = modulus * modulus
    edges = [0] * state_count
    valuation_histogram = Counter()
    digest = hashlib.sha256()
    phase_8_hits = 0
    phase_16_hits = 0

    for x in range(modulus):
        for z in range(modulus):
            next_x, next_z = inverse_lift_edge(x, z, modulus)
            index = x * modulus + z
            edges[index] = next_x * modulus + next_z
            projective = (x, 1, z)
            value_8 = contact_valuation(H, projective, k)
            value_16 = contact_valuation(PHASE_16_DIRECTION, projective, k)
            valuation_histogram[(value_8, value_16)] += 1
            phase_8_hits += value_8 == k
            phase_16_hits += value_16 == k
            digest.update(struct.pack(">7I", k, x, z, next_x, next_z, value_8, value_16))
        progress(modulus)
        if stop_requested():
            raise TimeBudgetExpired

    if phase_8_hits != 1 or phase_16_hits != 1:
        raise AssertionError("projective contact class count drift", k)
    graph_stats = functional_graph_stats(edges)
    latent = latent_collapse_record(k, modulus, edges)
    return {
        "k": k,
        "modulus": modulus,
        "state_count": state_count,
        "edge_count": state_count,
        "state_order": "x major, then z, representing [x:1:z] modulo 3^k",
        "edge_formula": "[g] maps to [N^2 g], normalized to y=1",
        "state_edge_sha256": digest.hexdigest(),
        "contact_valuation_pair_histogram": {
            f"{left},{right}": valuation_histogram[(left, right)]
            for left, right in sorted(valuation_histogram)
        },
        "phase_8_projective_contact_classes": phase_8_hits,
        "phase_16_projective_contact_classes": phase_16_hits,
        **graph_stats,
        "latent_orbit": latent,
    }


def contact_model_certificate():
    if matrix_product(M, N) != ((9, 0, 0), (0, 9, 0), (0, 0, 9)):
        raise AssertionError("MN=9I identity drift")
    if determinant(M) != 27 or determinant(N) != 27:
        raise AssertionError("matrix determinant drift")
    if matrix_product(A, N_SQUARED) != (
        (81, 0, 0),
        (0, 81, 0),
        (0, 0, 81),
    ):
        raise AssertionError("macro inverse identity drift")

    if add(matrix_vector(A, P_NUMERATOR), scale(P_DENOMINATOR, TRANSLATION)) != P_NUMERATOR:
        raise AssertionError("affine fixed point drift")
    reveal_from_fixed_point = subtract(scale(P_DENOMINATOR, REVEAL), P_NUMERATOR)
    if reveal_from_fixed_point != H:
        raise AssertionError("reveal direction drift")

    # Checking the cross identity on basis pairs proves it by bilinearity.
    basis = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    for left in basis:
        for right in basis:
            if cross(matrix_vector(A, left), matrix_vector(A, right)) != matrix_vector(
                COFACTOR_A, cross(left, right)
            ):
                raise AssertionError("cofactor cross identity drift")

    pullback_reveal = add(tuple(map(Fraction, CONTROL)), inverse_m(inverse_m(REVEAL)))
    quadratic_test_vectors = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (1, 0, 1),
        (0, 1, 1),
    )
    for vector in quadratic_test_vectors:
        if lateral_q(matrix_vector(N_SQUARED, vector)) != 81 * lateral_q(vector):
            raise AssertionError("lateral quadratic transport identity drift")

    return {
        "line_equation": "x cross g = mu, with primitive canonical g and g dot mu = 0",
        "macro_map": {
            "definition": "F(x)=M^2(x-c)=A x+b",
            "A": [list(row) for row in A],
            "b": list(TRANSLATION),
            "control_c": list(CONTROL),
            "fixed_point_numerator": list(P_NUMERATOR),
            "fixed_point_denominator": P_DENOMINATOR,
        },
        "unnormalized_line_transport": (
            "(g,mu) maps to (A g, cof(A) mu + b cross (A g))"
        ),
        "contact_residual": "R_x(g,mu)=x cross g-mu",
        "residual_identity": (
            "R_(F(x))(A g,cof(A)mu+b cross A g)=cof(A)R_x(g,mu)"
        ),
        "phase_8_reveal": list(REVEAL),
        "phase_8_reveal_pullback": fraction_vector_record(pullback_reveal),
        "phase_contact_directions_from_fixed_point": {
            "8": list(H),
            "16": list(PHASE_16_DIRECTION),
        },
        "padic_inverse_direction_chart": {
            "domain": "g_y is a 3-adic unit; normalize [g]=[x:1:z]",
            "map": "(x,z) maps to (9x/u,(3-9z)/u), where u=-8-3z is a unit",
            "fixed_point": (
                "(0,z_*) with 3z_*^2-z_*+3=0 and z_*=0 mod 3; "
                "Hensel uniqueness follows because 6z_*-1 is a unit"
            ),
            "difference_identity": (
                "phi(z)-phi(w)=81(z-w)/((-8-3z)(-8-3w))"
            ),
            "contraction": (
                "v3(x')=v3(x)+2 and v3(phi(z)-phi(w))=v3(z-w)+4"
            ),
            "homogeneous_polynomial": "q(g)=3g_y^2-g_y*g_z+3g_z^2",
            "homogeneous_transport": "q(N^2 g)=81q(g)",
            "reachable_birth_target": (
                "bound simultaneous 3-adic proximity to g_x=0 and q(g)=0 "
                "for every policy-reachable newborn secant"
            ),
        },
    }


def integer_line_moment(direction):
    numerator = cross(P_NUMERATOR, direction)
    if any(coordinate % P_DENOMINATOR for coordinate in numerator):
        raise AssertionError("latent line moment is not integral", direction, numerator)
    return tuple(coordinate // P_DENOMINATOR for coordinate in numerator)


def latent_positive_control(depth):
    if depth < 1:
        raise ValueError("latent-depth must be positive")
    records = []
    digest = hashlib.sha256()
    directions = [H]
    for _ in range(depth):
        directions.append(matrix_vector(N_SQUARED, directions[-1]))

    for n, direction in enumerate(directions):
        if canonical_primitive(direction) != direction:
            raise AssertionError("latent direction lost primitivity/canonical sign", n)
        moment = integer_line_moment(direction)
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
            raise AssertionError("latent direct-contact positive control drift", n)
        if (
            x_valuation != 2 * n
            or q_valuation != 4 * n + 1
            or padic_depth != n
        ):
            raise AssertionError("latent 3-adic depth formula drift", n)

        if n:
            previous_direction = directions[n - 1]
            image = matrix_vector(A, direction)
            divisor = content(image)
            if divisor != 81 or canonical_primitive(image) != previous_direction:
                raise AssertionError("latent direction countdown drift", n)

            first_image = matrix_vector(M, direction)
            first_divisor = content(first_image)
            middle = canonical_primitive(first_image)
            second_divisor = content(matrix_vector(M, middle))
            if (first_divisor, second_divisor) != (9, 9):
                raise AssertionError("latent t=9 normalization branches drift", n)

            transported_moment = add(
                matrix_vector(COFACTOR_A, moment),
                cross(TRANSLATION, image),
            )
            if any(coordinate % divisor for coordinate in transported_moment):
                raise AssertionError("transported moment normalization is not integral", n)
            normalized_moment = tuple(
                coordinate // divisor for coordinate in transported_moment
            )
            if normalized_moment != integer_line_moment(previous_direction):
                raise AssertionError("affine line moment countdown drift", n)

        digest.update(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
        )
        records.append(record)

    return {
        "depth": depth,
        "record_count": len(records),
        "record_stream_sha256": digest.hexdigest(),
        "first_record": records[0],
        "last_record": records[-1],
        "checks": [
            "g_n=N^(2n)h remains primitive and has an integral affine moment",
            "each forward macrocycle uses t=9 twice and maps L_n to L_(n-1)",
            "only L_0 hits the phase-8 reveal direction in this finite regression",
            "the phase-16 equal-J direction is never parallel to a checked g_n",
        ],
        "proof_boundary": (
            "The depth is regression coverage.  The all-n latent-family theorem is "
            "proved separately in LATENT-REENTRY-OBSTRUCTION.md."
        ),
    }


def constants_payload():
    return {
        "M": [list(row) for row in M],
        "N": [list(row) for row in N],
        "N_squared": [list(row) for row in N_SQUARED],
        "H": list(H),
        "phase_16_direction": list(PHASE_16_DIRECTION),
    }


def checkpoint_fingerprint(max_k, latent_depth, source_sha256):
    return stable_hash({
        "schema_version": SCHEMA_VERSION,
        "max_k": max_k,
        "latent_depth": latent_depth,
        "source_sha256": source_sha256,
        "constants": constants_payload(),
    })


def load_checkpoint(path, fingerprint):
    path = Path(path)
    if not path.exists():
        return []
    with path.open() as handle:
        checkpoint = json.load(handle)
    if checkpoint.get("fingerprint") != fingerprint:
        raise RuntimeError("checkpoint fingerprint mismatch")
    completed = checkpoint.get("completed_precisions")
    if not isinstance(completed, list):
        raise RuntimeError("checkpoint completed-precision payload is malformed")
    if [record.get("k") for record in completed] != list(range(1, len(completed) + 1)):
        raise RuntimeError("checkpoint precision frontier is not contiguous")
    return completed


def write_checkpoint(path, fingerprint, max_k, completed, status):
    atomic_json_dump({
        "schema_version": SCHEMA_VERSION,
        "fingerprint": fingerprint,
        "max_k": max_k,
        "status": status,
        "next_precision": len(completed) + 1,
        "completed_state_edges": sum(record["state_count"] for record in completed),
        "completed_precisions": completed,
    }, path)


def run(args):
    source_path = Path(__file__)
    source_sha256 = file_sha256(source_path)
    estimate_record = estimate(args.max_k, args.state_budget)
    if not estimate_record["within_budget"]:
        raise RuntimeError(
            "state budget exceeded: "
            f"precision {args.max_k} needs {estimate_record['maximum_single_precision_states']} "
            f"states, budget is {args.state_budget}; run estimate and raise the budget explicitly"
        )

    fingerprint = checkpoint_fingerprint(args.max_k, args.latent_depth, source_sha256)
    completed = load_checkpoint(args.checkpoint, fingerprint) if args.resume else []
    if not args.resume and Path(args.checkpoint).exists():
        raise RuntimeError("checkpoint exists; pass --resume or choose a new checkpoint path")

    total = estimate_record["total_state_edges"]
    completed_work = sum(record["state_count"] for record in completed)
    started = time.monotonic()
    last_report = started
    precision_progress = 0

    def report(increment):
        nonlocal precision_progress, last_report
        precision_progress += increment
        now = time.monotonic()
        if args.progress_seconds > 0 and now - last_report >= args.progress_seconds:
            done = completed_work + precision_progress
            elapsed = max(now - started, 1e-9)
            rate = precision_progress / elapsed
            eta = (total - done) / rate if rate else None
            print(json.dumps({
                "status": "running",
                "done": done,
                "total": total,
                "rate_states_per_second": round(rate, 1),
                "eta_seconds": None if eta is None else round(eta, 1),
                "checkpoint": str(args.checkpoint),
            }, sort_keys=True), file=sys.stderr, flush=True)
            last_report = now

    def stop_requested():
        return args.max_seconds > 0 and time.monotonic() - started >= args.max_seconds

    for k in range(len(completed) + 1, args.max_k + 1):
        precision_progress = 0
        precision_started = time.monotonic()
        try:
            record = compute_precision(k, stop_requested, report)
        except TimeBudgetExpired:
            write_checkpoint(args.checkpoint, fingerprint, args.max_k, completed, "paused")
            print(json.dumps({
                "status": "paused",
                "next_precision": k,
                "completed_precisions": len(completed),
                "checkpoint": str(args.checkpoint),
            }, sort_keys=True))
            return None
        record["elapsed_seconds_observed"] = round(time.monotonic() - precision_started, 6)
        completed.append(record)
        completed_work += record["state_count"]
        write_checkpoint(args.checkpoint, fingerprint, args.max_k, completed, "running")

    if file_sha256(source_path) != source_sha256:
        raise RuntimeError("explorer changed during run")

    mathematical_payload = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "exact bounded 3-adic residue exploration for one fixed macrocycle; "
            "not a reachable-birth theorem or unconditional proof"
        ),
        "proof_boundary": {
            "proved_by_exact_algebra": [
                "primitive normalization has only t=1,3,9 branches",
                "the displayed affine Pluecker and contact-residual transport identities",
                "the y-unit inverse chart contracts by 3^2 and 3^4 toward its unique 3-adic projective fixed point",
                "q(N^2 g)=81q(g), giving v3(g_n,x)=2n and v3(q(g_n))=4n+1 for the latent family",
            ],
            "certified_finite": [
                f"all [x:1:z] residue states through modulus 3^{args.max_k}",
                f"the latent-family arithmetic regression through depth {args.latent_depth}",
            ],
            "not_proved": [
                "birth of a latent line from a reachable legal endpoint pair",
                "finite index of the reachable contact language",
                "a universal connector survivor or all-level induction",
            ],
        },
        "explorer": {
            "logical_path": "design/padic_macrocycle_lift.py",
            "sha256": source_sha256,
        },
        "constants": constants_payload(),
        "estimate": estimate_record,
        "normalization": normalization_certificate(),
        "contact_model": contact_model_certificate(),
        "precisions": [
            {key: value for key, value in record.items() if key != "elapsed_seconds_observed"}
            for record in completed
        ],
        "latent_positive_control": latent_positive_control(args.latent_depth),
        "finite_modulus_warning": (
            "The exact y-unit chart has a unique 3-adic attracting direction: "
            "x contracts by 3^2 and z contracts by 3^4.  At every fixed precision, "
            "the inverse latent orbit therefore reaches one fixed projective residue. "
            "Bounded residue state cannot encode the unbounded exact reveal countdown; "
            "a positive proof must bound how closely reachable newborn secants approach "
            "the simultaneous 3-adic locus g_x=0 and q(g)=0."
        ),
    }
    payload = dict(mathematical_payload)
    payload["payload_sha256"] = stable_hash(mathematical_payload)
    atomic_json_dump(payload, args.output)
    write_checkpoint(args.checkpoint, fingerprint, args.max_k, completed, "complete")
    print(json.dumps({
        "status": "complete",
        "output": str(args.output),
        "payload_sha256": payload["payload_sha256"],
        "precisions": len(completed),
        "total_state_edges": total,
    }, sort_keys=True))
    return payload


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    estimate_parser = subparsers.add_parser("estimate")
    estimate_parser.add_argument("--max-k", type=int, default=5)
    estimate_parser.add_argument("--state-budget", type=int, default=DEFAULT_STATE_BUDGET)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--max-k", type=int, default=5)
    run_parser.add_argument("--latent-depth", type=int, default=16)
    run_parser.add_argument("--state-budget", type=int, default=DEFAULT_STATE_BUDGET)
    run_parser.add_argument("--max-seconds", type=float, default=300.0)
    run_parser.add_argument("--progress-seconds", type=float, default=5.0)
    run_parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    run_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run_parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


A = matrix_product(M, M)
N_SQUARED = matrix_product(N, N)
COFACTOR_A = cofactor(A)
TRANSLATION = scale(-1, matrix_vector(A, CONTROL))


def main():
    args = parse_args()
    if args.command == "estimate":
        print(json.dumps(estimate(args.max_k, args.state_budget), sort_keys=True, indent=2))
        return
    run(args)


if __name__ == "__main__":
    main()
