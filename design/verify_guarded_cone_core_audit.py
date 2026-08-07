#!/usr/bin/env python3
"""Independent verifier for guarded_cone_core_audit.py outputs.

The verifier does not import the producer.  It reloads the pinned parent and
terminal guarded audit, recomputes every one of the 34,407,660 pair tests,
reconstructs all 246 witness records, and independently recognizes both known
inverse direction orbits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "guarded-cone-core-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "guarded-cone-core-witness.json"
EXPECTED_SUMMARY_SCHEMA = "guarded-cone-core-audit/v1"
EXPECTED_WITNESS_SCHEMA = "guarded-cone-core-witness/v1"
EXPECTED_PARENT_SHA256 = "86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7"
EXPECTED_PARENT_PAYLOAD = "70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258"
EXPECTED_AUDIT_SHA256 = "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36"
EXPECTED_COUNTS = {"11/3": 242, "348/275": 4}
EXPECTED_DIRECTIONS = {"11/3": 38, "348/275": 4}
MATRIX_M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MATRIX_N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
SEEDS = {
    "fixed_348_macrocycle": ("348/275", (55, 34, 18)),
    "fixed_11_degenerate_cycle": ("11/3", (3, -1, 3)),
}


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def object_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def disk_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def verify_seal(value):
    body = dict(value)
    claimed = body.pop("payload_sha256", None)
    if claimed is None or object_hash(body) != claimed:
        raise AssertionError("payload seal mismatch")
    return claimed


def multiply_matrices(left, right):
    rows = []
    for row in range(3):
        values = []
        for column in range(3):
            values.append(sum(left[row][k] * right[k][column] for k in range(3)))
        rows.append(tuple(values))
    return tuple(rows)


def transpose(matrix):
    return tuple(tuple(matrix[j][i] for j in range(3)) for i in range(3))


def scaled_matrix(factor, matrix):
    return tuple(tuple(factor * value for value in row) for row in matrix)


def apply_n(vector):
    x, y, z = vector
    return 3 * x, -y + 3 * z, -3 * y


def apply_m(vector):
    x, y, z = vector
    return 3 * x, -3 * z, 3 * y - z


def normalize(vector):
    common = math.gcd(math.gcd(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    if common == 0:
        raise AssertionError("zero vector in pair scan")
    reduced = tuple(value // common for value in vector)
    orientation = next(value for value in reduced if value)
    sign = 1 if orientation > 0 else -1
    canonical = reduced if sign > 0 else tuple(-value for value in reduced)
    coefficient = sign * common
    if tuple(coefficient * value for value in canonical) != tuple(vector):
        raise AssertionError("normalization reconstruction mismatch")
    return canonical, coefficient


def classify(vector):
    x, y, z = vector
    # Expanded independently rather than calling the producer's q function.
    eleven = 9 * y * y - 3 * y * z + 9 * z * z - 11 * x * x
    three_forty_eight = (
        825 * y * y - 275 * y * z + 825 * z * z - 348 * x * x
    )
    if eleven == 0 and three_forty_eight == 0:
        raise AssertionError("distinct positive cones intersect on nonzero vector")
    if eleven == 0:
        return "11/3"
    if three_forty_eight == 0:
        return "348/275"
    return None


def cross_product(left, right):
    ax, ay, az = left
    bx, by, bz = right
    return ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx


def inverse_orbit_index(direction, seed):
    if direction[0] <= 0 or direction[0] % seed[0]:
        return None
    quotient = direction[0] // seed[0]
    exponent = 0
    while quotient > 1 and quotient % 3 == 0:
        quotient //= 3
        exponent += 1
    if quotient != 1:
        return None
    current = seed
    for _ in range(exponent):
        current = apply_n(current)
    canonical, coefficient = normalize(current)
    if coefficient != 1:
        raise AssertionError("inverse orbit is not primitive")
    return exponent if canonical == direction else None


def symbolic_checks():
    identity = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    nine_identity = scaled_matrix(9, identity)
    if multiply_matrices(MATRIX_M, MATRIX_N) != nine_identity:
        raise AssertionError("M*N != 9I")
    if multiply_matrices(MATRIX_N, MATRIX_M) != nine_identity:
        raise AssertionError("N*M != 9I")
    doubled_q = ((0, 0, 0), (0, 6, -1), (0, -1, 6))
    for matrix in (MATRIX_M, MATRIX_N):
        transported = multiply_matrices(
            multiply_matrices(transpose(matrix), doubled_q), matrix
        )
        if transported != scaled_matrix(9, doubled_q):
            raise AssertionError("quadratic transport identity failed")
    for cone, seed in SEEDS.values():
        if classify(seed) != cone or seed[1] % 3 == 0:
            raise AssertionError("family seed identity failed")


def reconstruct_records(points):
    records = []
    pair_counts = Counter()
    direction_counts = {"11/3": Counter(), "348/275": Counter()}
    for later_index in range(len(points)):
        later = points[later_index]
        for earlier_index in range(later_index):
            earlier = points[earlier_index]
            raw = tuple(later[i] - earlier[i] for i in range(3))
            cone = classify(raw)
            if cone is None:
                continue
            direction, coefficient = normalize(raw)
            if classify(direction) != cone:
                raise AssertionError("normalization changed cone")
            carried = apply_m(raw)
            carried_direction, carried_coefficient = normalize(carried)
            if classify(carried_direction) != cone:
                raise AssertionError("carriage changed cone")
            matches = []
            for name, (family_cone, seed) in SEEDS.items():
                if family_cone != cone:
                    continue
                index = inverse_orbit_index(direction, seed)
                if index is not None:
                    matches.append({"family": name, "orbit_index": index})
            records.append(
                {
                    "pair_id": f"L5:A{earlier_index}:A{later_index}",
                    "earlier_index": earlier_index,
                    "later_index": later_index,
                    "earlier_point": list(earlier),
                    "later_point": list(later),
                    "raw_chord": list(raw),
                    "canonical_direction": list(direction),
                    "signed_multiplier": coefficient,
                    "origin_moment": list(cross_product(earlier, direction)),
                    "cone": cone,
                    "carried_raw_chord": list(carried),
                    "carried_canonical_direction": list(carried_direction),
                    "carried_signed_multiplier": carried_coefficient,
                    "orbit_matches": matches,
                }
            )
            pair_counts[cone] += 1
            direction_counts[cone][direction] += 1
    if dict(pair_counts) != EXPECTED_COUNTS:
        raise AssertionError(f"pair-count mismatch: {dict(pair_counts)!r}")
    if {key: len(value) for key, value in direction_counts.items()} != EXPECTED_DIRECTIONS:
        raise AssertionError("unique-direction mismatch")
    return records, direction_counts


def verify(summary_path, witness_path):
    summary = read_json(summary_path)
    witness = read_json(witness_path)
    summary_hash = verify_seal(summary)
    witness_hash = verify_seal(witness)
    if summary.get("schema") != EXPECTED_SUMMARY_SCHEMA:
        raise AssertionError("summary schema mismatch")
    if witness.get("schema") != EXPECTED_WITNESS_SCHEMA:
        raise AssertionError("witness schema mismatch")
    if summary.get("signature") != "[OpenAI Codex]" or witness.get("signature") != "[OpenAI Codex]":
        raise AssertionError("signature mismatch")
    if summary.get("verdict") != "GUARDED_CONE_CORE_PROVED":
        raise AssertionError("verdict mismatch")
    if summary["witness"]["payload_sha256"] != witness_hash:
        raise AssertionError("summary/witness commitment mismatch")

    producer_path = ROOT / summary["producer"]["path"]
    if disk_hash(producer_path) != summary["producer"]["sha256"]:
        raise AssertionError("producer source drift")

    parent_binding = summary["source_bindings"]["parent"]
    audit_binding = summary["source_bindings"]["guarded_audit"]
    parent_path = Path(parent_binding["path"])
    audit_path = Path(audit_binding["path"])
    if disk_hash(parent_path) != EXPECTED_PARENT_SHA256:
        raise AssertionError("parent file drift")
    if disk_hash(audit_path) != EXPECTED_AUDIT_SHA256:
        raise AssertionError("guarded audit file drift")
    if parent_binding != witness["source_bindings"]["parent"]:
        raise AssertionError("parent binding differs between artifacts")
    if audit_binding != witness["source_bindings"]["guarded_audit"]:
        raise AssertionError("audit binding differs between artifacts")

    parent = read_json(parent_path)
    parent_body = dict(parent)
    parent_claim = parent_body.pop("payload_sha256", None)
    if parent_claim != EXPECTED_PARENT_PAYLOAD or object_hash(parent_body) != parent_claim:
        raise AssertionError("parent payload mismatch")
    guarded_audit = read_json(audit_path)
    if guarded_audit["canonical_guarded_L5_parent"]["sha256"] != EXPECTED_PARENT_SHA256:
        raise AssertionError("audit does not bind parent")
    if guarded_audit["result"]["guarded_cone_pair_counts_by_spectrum"] != EXPECTED_COUNTS:
        raise AssertionError("audit cone counts differ")
    invariant = guarded_audit["successor_invariant"]
    if invariant["inherited_pair_count"] != 246:
        raise AssertionError("successor inherited count mismatch")
    if not invariant["only_inherited_anchor_anchor_pairs_in_guarded_spectra"]:
        raise AssertionError("successor cone birth invariant absent")
    if set(invariant["same_guarded_spectra"]) != set(EXPECTED_COUNTS):
        raise AssertionError("successor spectra mismatch")

    symbolic_checks()
    points = tuple(tuple(point) for point in parent["points"])
    if len(points) != 8_296:
        raise AssertionError("parent point count mismatch")
    records, direction_counts = reconstruct_records(points)
    if records != witness["core_records"]:
        raise AssertionError("core record stream mismatch")

    matches = {name: [] for name in SEEDS}
    for record in records:
        for match in record["orbit_matches"]:
            matches[match["family"]].append(
                (record["pair_id"], match["orbit_index"], record["canonical_direction"])
            )
    expected_match_counts = {
        "fixed_348_macrocycle": (0, 0),
        "fixed_11_degenerate_cycle": (3, 0),
    }
    for name, (total, positive) in expected_match_counts.items():
        if len(matches[name]) != total:
            raise AssertionError(f"{name} total match drift")
        if sum(index > 0 for _pair, index, _direction in matches[name]) != positive:
            raise AssertionError(f"{name} positive-index match drift")
    if sorted(pair for pair, _index, _direction in matches["fixed_11_degenerate_cycle"]) != [
        "L5:A2592:A2609",
        "L5:A5481:A5498",
        "L5:A7055:A7072",
    ]:
        raise AssertionError("depth-zero promoted pair identities drift")

    if summary["canonical_parent"]["cone_pair_counts"] != EXPECTED_COUNTS:
        raise AssertionError("summary pair counts mismatch")
    if summary["canonical_parent"]["unique_direction_counts"] != EXPECTED_DIRECTIONS:
        raise AssertionError("summary direction counts mismatch")
    computed_histograms = {
        cone: {
            str(multiplicity): count
            for multiplicity, count in sorted(Counter(counter.values()).items())
        }
        for cone, counter in direction_counts.items()
    }
    if summary["canonical_parent"]["direction_multiplicity_histograms"] != computed_histograms:
        raise AssertionError("direction multiplicity histogram mismatch")
    if summary["canonical_parent"]["unordered_pairs_scanned"] != 34_407_660:
        raise AssertionError("pair-scan scope mismatch")
    if summary["classifications"] != {
        "all_level_guarded_cone_lineage_freeze": "PROVED",
        "canonical_parent_cone_core": "EXACT FINITE",
        "depth_zero_fixed_11_exceptions": "EXACT FINITE",
        "directions_outside_guarded_cones": "UNPROVED",
        "finite_effect_state_for_core": "UNPROVED",
        "fixed_11_positive_depth_exclusion": "PROVED",
        "fixed_348_positive_depth_exclusion": "PROVED",
        "universal_guarded_successor_availability": "UNPROVED",
    }:
        raise AssertionError("classification ledger drift")
    boundary = summary["proof_boundary"]
    if not all(
        boundary[key]
        for key in (
            "not_an_availability_certificate",
            "not_a_finite_effect_automaton",
            "not_an_exhaustive_recurrence_classification",
        )
    ):
        raise AssertionError("proof boundary weakened")

    return {
        "auditor": "OpenAI Codex",
        "status": "verified",
        "verdict": summary["verdict"],
        "parent_pairs_scanned": 34_407_660,
        "cone_pair_lineages": len(records),
        "unique_cone_directions": sum(len(counter) for counter in direction_counts.values()),
        "fixed_348_orbit_pairs": len(matches["fixed_348_macrocycle"]),
        "fixed_11_depth_zero_pairs": len(matches["fixed_11_degenerate_cycle"]),
        "positive_depth_pairs": sum(
            index > 0 for family in matches.values() for _pair, index, _direction in family
        ),
        "summary_payload_sha256": summary_hash,
        "witness_payload_sha256": witness_hash,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()
    print(json.dumps(verify(args.summary, args.witness), sort_keys=True))


if __name__ == "__main__":
    main()
