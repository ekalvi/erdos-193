#!/usr/bin/env python3
"""Exact guarded-cone lineage core and latent-orbit closure audit.

This audit performs the all-pairs scan of the canonical guarded-L5 parent,
classifies every secant in either guarded invariant cone, and proves the
policy-relative induction that no additional cone secant can be born.  It
also checks the two explicit infinite delayed-return direction families
against the complete inherited core.

The result is deliberately narrower than an availability certificate: finite
lineage identity does not by itself give a finite effect/moment automaton for
all corridors, and directions outside the two cones remain uncontrolled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path


SCHEMA = "guarded-cone-core-audit/v1"
WITNESS_SCHEMA = "guarded-cone-core-witness/v1"
AUDITOR = "OpenAI Codex"
SIGNATURE = "[OpenAI Codex]"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARENT = Path("/tmp/guarded-L5-parent-canonical-v1.json")
DEFAULT_GUARDED_AUDIT = ROOT / "design" / "guarded-L5-to-L6-audit-summary.json"
DEFAULT_SUMMARY = ROOT / "design" / "guarded-cone-core-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "guarded-cone-core-witness.json"

EXPECTED_PARENT_SHA256 = "86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7"
EXPECTED_PARENT_PAYLOAD = "70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258"
EXPECTED_GUARDED_AUDIT_SHA256 = "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36"
EXPECTED_PARENT_POINTS = 8_296
EXPECTED_PAIR_COUNTS = {"11/3": 242, "348/275": 4}
EXPECTED_UNIQUE_DIRECTION_COUNTS = {"11/3": 38, "348/275": 4}

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

FAMILIES = (
    {
        "name": "fixed_348_macrocycle",
        "cone": "348/275",
        "seed": (55, 34, 18),
        "source": "phase-8/phase-16 latent 8 -> 16 -> 8 family",
        "same_phase_directions": "N^(2n)*(55,34,18)",
    },
    {
        "name": "fixed_11_degenerate_cycle",
        "cone": "11/3",
        "seed": (3, -1, 3),
        "source": "step-1 two-edge degenerate-cycle family",
        "same_phase_directions": "N^(2n)*(3,-1,3)",
    },
)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def seal(value):
    result = dict(value)
    result.pop("payload_sha256", None)
    result["payload_sha256"] = stable_hash(result)
    return result


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json_dump(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][middle] * right[middle][column] for middle in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def scale_matrix(factor, matrix):
    return tuple(tuple(factor * entry for entry in row) for row in matrix)


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def quadratic(direction):
    _x, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def cone_residuals(direction):
    x = direction[0]
    value = quadratic(direction)
    return {
        "11/3": 3 * value - 11 * x * x,
        "348/275": 275 * value - 348 * x * x,
    }


def cone_label(direction):
    zeroes = [name for name, residual in cone_residuals(direction).items() if residual == 0]
    if len(zeroes) > 1:
        raise AssertionError("nonzero direction lies in both distinct cones")
    return zeroes[0] if zeroes else None


def primitive_with_multiplier(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    if divisor == 0:
        raise ValueError("zero chord")
    direction = tuple(coordinate // divisor for coordinate in vector)
    first = next(coordinate for coordinate in direction if coordinate)
    sign = 1 if first > 0 else -1
    if sign < 0:
        direction = tuple(-coordinate for coordinate in direction)
    multiplier = sign * divisor
    if tuple(multiplier * coordinate for coordinate in direction) != tuple(vector):
        raise AssertionError("primitive multiplier reconstruction failed")
    return direction, multiplier


def power_of_three(value):
    if value < 1:
        return None
    exponent = 0
    while value % 3 == 0:
        value //= 3
        exponent += 1
    return exponent if value == 1 else None


def orbit_direction(seed, index):
    direction = tuple(seed)
    for _ in range(index):
        direction = matrix_vector(N, direction)
    primitive, multiplier = primitive_with_multiplier(direction)
    if multiplier != 1:
        raise AssertionError("declared inverse family lost primitivity")
    return primitive


def recognize_orbit(direction, seed):
    if direction[0] <= 0 or direction[0] % seed[0]:
        return None
    index = power_of_three(direction[0] // seed[0])
    if index is None:
        return None
    return index if orbit_direction(seed, index) == tuple(direction) else None


def validate_inputs(parent_path, guarded_audit_path):
    hashes = {
        "parent": file_sha256(parent_path),
        "guarded_audit": file_sha256(guarded_audit_path),
    }
    expected = {
        "parent": EXPECTED_PARENT_SHA256,
        "guarded_audit": EXPECTED_GUARDED_AUDIT_SHA256,
    }
    if hashes != expected:
        raise AssertionError(f"input hash drift: {hashes!r}")

    parent = load_json(parent_path)
    parent_payload = dict(parent)
    claimed_parent_payload = parent_payload.pop("payload_sha256", None)
    if claimed_parent_payload != EXPECTED_PARENT_PAYLOAD:
        raise AssertionError("parent payload commitment drift")
    if stable_hash(parent_payload) != claimed_parent_payload:
        raise AssertionError("parent payload seal mismatch")
    if len(parent["points"]) != EXPECTED_PARENT_POINTS:
        raise AssertionError("parent point count drift")

    guarded_audit = load_json(guarded_audit_path)
    if guarded_audit["canonical_guarded_L5_parent"]["sha256"] != hashes["parent"]:
        raise AssertionError("guarded audit does not bind the loaded parent")
    if guarded_audit["canonical_guarded_L5_parent"]["payload_sha256"] != claimed_parent_payload:
        raise AssertionError("guarded audit parent payload drift")
    if guarded_audit["result"]["guarded_cone_pair_counts_by_spectrum"] != EXPECTED_PAIR_COUNTS:
        raise AssertionError("guarded audit cone-count drift")
    if not guarded_audit["result"]["independent_ordered_no_three_collinear_verified"]:
        raise AssertionError("parent lineage lacks the certified triple-free successor")
    return parent, guarded_audit, hashes


def enumerate_core(points):
    records = []
    direction_counts = {name: Counter() for name in EXPECTED_PAIR_COUNTS}
    pair_counts = Counter()
    for later_index, later in enumerate(points):
        for earlier_index in range(later_index):
            earlier = points[earlier_index]
            raw = subtract(later, earlier)
            label = cone_label(raw)
            if label is None:
                continue
            direction, multiplier = primitive_with_multiplier(raw)
            if cone_label(direction) != label:
                raise AssertionError("cone predicate changed under primitive normalization")
            raw_child = matrix_vector(M, raw)
            child_direction, child_multiplier = primitive_with_multiplier(raw_child)
            if cone_label(child_direction) != label:
                raise AssertionError("cone predicate changed under carriage")
            orbit_matches = []
            for family in FAMILIES:
                if family["cone"] != label:
                    continue
                orbit_index = recognize_orbit(direction, family["seed"])
                if orbit_index is not None:
                    orbit_matches.append(
                        {"family": family["name"], "orbit_index": orbit_index}
                    )
            record = {
                "pair_id": f"L5:A{earlier_index}:A{later_index}",
                "earlier_index": earlier_index,
                "later_index": later_index,
                "earlier_point": list(earlier),
                "later_point": list(later),
                "raw_chord": list(raw),
                "canonical_direction": list(direction),
                "signed_multiplier": multiplier,
                "origin_moment": list(cross(earlier, direction)),
                "cone": label,
                "carried_raw_chord": list(raw_child),
                "carried_canonical_direction": list(child_direction),
                "carried_signed_multiplier": child_multiplier,
                "orbit_matches": orbit_matches,
            }
            records.append(record)
            pair_counts[label] += 1
            direction_counts[label][direction] += 1

    observed_pair_counts = dict(sorted(pair_counts.items()))
    if observed_pair_counts != EXPECTED_PAIR_COUNTS:
        raise AssertionError(f"parent cone-pair census drift: {observed_pair_counts!r}")
    observed_direction_counts = {
        label: len(counter) for label, counter in sorted(direction_counts.items())
    }
    if observed_direction_counts != EXPECTED_UNIQUE_DIRECTION_COUNTS:
        raise AssertionError(
            f"parent unique-direction census drift: {observed_direction_counts!r}"
        )
    return records, direction_counts


def family_records(core):
    results = []
    for family in FAMILIES:
        matches = []
        for record in core:
            for match in record["orbit_matches"]:
                if match["family"] == family["name"]:
                    matches.append(
                        {
                            "pair_id": record["pair_id"],
                            "orbit_index": match["orbit_index"],
                            "canonical_direction": record["canonical_direction"],
                            "origin_moment": record["origin_moment"],
                        }
                    )
        positive = [match for match in matches if match["orbit_index"] > 0]
        depth_zero = [match for match in matches if match["orbit_index"] == 0]
        if positive:
            raise AssertionError(f"positive-depth inherited family member: {positive!r}")
        expected_depth_zero = 0 if family["name"] == "fixed_348_macrocycle" else 3
        if len(depth_zero) != expected_depth_zero:
            raise AssertionError("depth-zero exception count drift")
        results.append(
            {
                "name": family["name"],
                "cone": family["cone"],
                "seed": list(family["seed"]),
                "source": family["source"],
                "same_phase_directions": family["same_phase_directions"],
                "inherited_orbit_pair_count": len(matches),
                "positive_orbit_index_pair_count": len(positive),
                "depth_zero_pair_count": len(depth_zero),
                "matches": matches,
                "policy_relative_conclusion": (
                    "No positive-index member can occur in any guarded continuation. "
                    "A future member would either be a forbidden new cone birth or the "
                    "carriage of a base direction at a still larger inverse-orbit index."
                ),
            }
        )
    return results


def multiplicity_histogram(counter):
    return {
        str(multiplicity): count
        for multiplicity, count in sorted(Counter(counter.values()).items())
    }


def prove_symbolic_identities():
    if matrix_product(N, M) != scale_matrix(9, IDENTITY):
        raise AssertionError("N*M identity failed")
    if matrix_product(M, N) != scale_matrix(9, IDENTITY):
        raise AssertionError("M*N identity failed")

    # Twice the yz quadratic q: v^T Q2 v = 2q(v).
    q2 = ((0, 0, 0), (0, 6, -1), (0, -1, 6))
    mt = tuple(tuple(M[column][row] for column in range(3)) for row in range(3))
    nt = tuple(tuple(N[column][row] for column in range(3)) for row in range(3))
    if matrix_product(matrix_product(mt, q2), M) != scale_matrix(9, q2):
        raise AssertionError("q(Mg)=9q(g) matrix identity failed")
    if matrix_product(matrix_product(nt, q2), N) != scale_matrix(9, q2):
        raise AssertionError("q(Ng)=9q(g) matrix identity failed")
    for family in FAMILIES:
        if cone_label(family["seed"]) != family["cone"]:
            raise AssertionError("family seed cone drift")
        if family["seed"][1] % 3 == 0:
            raise AssertionError("family primitivity induction precondition failed")
    return {
        "N_times_M": "9I",
        "M_times_N": "9I",
        "q_M_g": "9*q(g)",
        "q_N_g": "9*q(g)",
        "cone_invariance": "F_j(Mg)=9F_j(g) and F_j(Ng)=9F_j(g)",
        "orbit_primitivity": (
            "each seed has y nonzero modulo 3; N sends y to -y modulo 3, "
            "and det(N)=27 makes N invertible modulo every prime other than 3"
        ),
    }


def build_payload(args):
    parent, guarded_audit, hashes = validate_inputs(args.parent, args.guarded_audit)
    identities = prove_symbolic_identities()
    points = tuple(tuple(point) for point in parent["points"])
    core, direction_counts = enumerate_core(points)
    families = family_records(core)

    producer_hash = file_sha256(Path(__file__))
    witness = seal(
        {
            "schema": WITNESS_SCHEMA,
            "auditor": AUDITOR,
            "signature": SIGNATURE,
            "source_bindings": {
                "parent": {
                    "path": str(Path(args.parent).resolve()),
                    "sha256": hashes["parent"],
                    "payload_sha256": EXPECTED_PARENT_PAYLOAD,
                },
                "guarded_audit": {
                    "path": str(Path(args.guarded_audit).resolve()),
                    "sha256": hashes["guarded_audit"],
                    "terminal_payload_sha256": guarded_audit["terminal_payload_sha256"],
                },
            },
            "symbolic_identities": identities,
            "core_records": core,
            "family_records": families,
        }
    )

    family_summary = []
    for record in families:
        family_summary.append(
            {
                key: value
                for key, value in record.items()
                if key != "matches"
            }
        )

    summary = seal(
        {
            "schema": SCHEMA,
            "auditor": AUDITOR,
            "signature": SIGNATURE,
            "status": "proved guarded two-cone lineage freeze and known latent-orbit closure",
            "producer": {
                "path": "design/guarded_cone_core_audit.py",
                "sha256": producer_hash,
            },
            "source_bindings": witness["source_bindings"],
            "classifications": {
                "canonical_parent_cone_core": "EXACT FINITE",
                "all_level_guarded_cone_lineage_freeze": "PROVED",
                "fixed_348_positive_depth_exclusion": "PROVED",
                "fixed_11_positive_depth_exclusion": "PROVED",
                "depth_zero_fixed_11_exceptions": "EXACT FINITE",
                "finite_effect_state_for_core": "UNPROVED",
                "universal_guarded_successor_availability": "UNPROVED",
                "directions_outside_guarded_cones": "UNPROVED",
            },
            "canonical_parent": {
                "points": len(points),
                "unordered_pairs_scanned": len(points) * (len(points) - 1) // 2,
                "cone_pair_counts": EXPECTED_PAIR_COUNTS,
                "unique_direction_counts": EXPECTED_UNIQUE_DIRECTION_COUNTS,
                "direction_multiplicity_histograms": {
                    label: multiplicity_histogram(counter)
                    for label, counter in sorted(direction_counts.items())
                },
                "total_cone_pair_lineages": len(core),
            },
            "known_latent_families": family_summary,
            "theorem": {
                "classification": "PROVED",
                "guarded_lineage_freeze": (
                    "For every finite history descended from the canonical guarded-L5 "
                    "parent in which every connector word satisfies the same two-cone "
                    "birth guard, every 11/3 or 348/275 secant is the image under a "
                    "common power of M of exactly one of the 246 inherited parent pairs."
                ),
                "known_family_corollary": (
                    "No positive inverse-orbit-index member of either explicit delayed-return "
                    "family can be a secant in such a history. The 348/275 family has no "
                    "inherited member. The 11/3 family has exactly three inherited index-zero "
                    "pairs and no positive-index member; those three endpoint-pair lineages "
                    "are the complete promoted exceptions for that fixed family."
                ),
                "proof": [
                    "M is injective and preserves both cone predicates, so inherited anchor-anchor pairs carry bijectively.",
                    "The guarded insertion predicate rejects every old-new and same-word new-new pair in either cone.",
                    "Every physical pair is either inherited anchor-anchor or is tested once when its later connector endpoint is inserted.",
                    "If M^k*d is projectively N^m*h, then d is projectively N^(m+k)*h because N*M=9I; the complete base-orbit scan therefore proves the family corollary.",
                ],
            },
            "proof_boundary": {
                "not_an_availability_certificate": True,
                "not_a_finite_effect_automaton": True,
                "not_an_exhaustive_recurrence_classification": True,
                "statement": (
                    "Finite endpoint-pair lineage identity does not yet encode every centred "
                    "Pluecker moment, corridor import, current poison effect, or direction "
                    "outside the two guarded cones. Connector availability remains open."
                ),
            },
            "verdict": "GUARDED_CONE_CORE_PROVED",
            "witness": {
                "path": str(Path(args.witness).resolve()),
                "payload_sha256": witness["payload_sha256"],
            },
        }
    )
    return summary, witness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--guarded-audit", type=Path, default=DEFAULT_GUARDED_AUDIT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()

    summary, witness = build_payload(args)
    atomic_json_dump(witness, args.witness)
    atomic_json_dump(summary, args.summary)
    print(
        json.dumps(
            {
                "auditor": AUDITOR,
                "status": summary["status"],
                "verdict": summary["verdict"],
                "cone_pair_lineages": summary["canonical_parent"]["total_cone_pair_lineages"],
                "fixed_348_orbit_pairs": summary["known_latent_families"][0]["inherited_orbit_pair_count"],
                "fixed_11_depth_zero_pairs": summary["known_latent_families"][1]["depth_zero_pair_count"],
                "positive_depth_pairs": sum(
                    family["positive_orbit_index_pair_count"]
                    for family in summary["known_latent_families"]
                ),
                "summary_payload_sha256": summary["payload_sha256"],
                "witness_payload_sha256": witness["payload_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
