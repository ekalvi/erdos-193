#!/usr/bin/env python3
"""Independent verifier for the guarded latent-family reachable-entry audit.

This file does not import the producer or the guarded construction modules.
It reloads the pinned mathematical inputs, reconstructs the chronology, scans
the inherited cone core, checks translated-line occupancy, and re-aggregates
the exhaustive alternate-word certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


AUDITOR = "OpenAI Codex"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "latent-family-reachable-entry-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "latent-family-reachable-entry-witness.json"
EXPECTED_SCHEMA = "latent-family-reachable-entry-audit/v1"
EXPECTED_WITNESS_SCHEMA = "latent-family-reachable-entry-witness/v1"

PARENT = Path("/tmp/guarded-L5-parent-canonical-v1.json")
CHRONOLOGY = Path("/tmp/guarded-L5-to-L6-construction-v1.json")
ALTERNATES = Path("/tmp/guarded-L5-to-L6-survivor-census-v2.json")
GUARDED_AUDIT = ROOT / "design" / "guarded-L5-to-L6-audit-summary.json"
ALTERNATE_SUMMARY = ROOT / "design" / "guarded-L5-to-L6-survivor-census-summary.json"
EXPECTED_SHA256 = {
    PARENT: "86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7",
    CHRONOLOGY: "420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9",
    ALTERNATES: "a69e490c544f65f51bdb178b27cd92b8ad359cb01af52de96c3b9cc796031aa2",
    GUARDED_AUDIT: "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36",
    ALTERNATE_SUMMARY: "b49632699f6c0c3bcad43b8282d061ffc01cdbaeb013b98d8e0d9f80eaeadb77",
}
EXPECTED_PARENT_PAYLOAD = "70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258"
EXPECTED_CHRONOLOGY_PAYLOAD = "2a7043df6e2ad625527cabf4726033479d7eee53e3e10031c676961e6158570e"
EXPECTED_ALTERNATE_PAYLOAD = "197d600065a5611977fd06f9a5b58d600fb9e32d1fff848b0b7e343866df1d25"
EXPECTED_ALT_SUMMARY_PAYLOAD = "42a844b40b14702a029a5b5a1125f8fe5d7c26d4eac7996fe923e958c5c340d4"

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
H = (55, 34, 18)
P_NUMERATOR = (-99, -78, -62)
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def stable_hash(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_sealed(path, field="payload_sha256", schema=None, expected=None):
    value = load_json(path)
    if schema is not None and value.get("schema") != schema:
        raise AssertionError("schema drift", str(path))
    claimed = value.get(field)
    payload = dict(value)
    payload.pop(field, None)
    if stable_hash(payload) != claimed or (expected is not None and claimed != expected):
        raise AssertionError("payload seal drift", str(path))
    return value, claimed


def add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


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


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def q(direction):
    _x, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def cone_residual(direction):
    return 275 * q(direction) - 348 * direction[0] * direction[0]


def primitive(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    if divisor == 0:
        raise AssertionError("zero direction")
    result = tuple(coordinate // divisor for coordinate in vector)
    sign = 1
    if next(coordinate for coordinate in result if coordinate) < 0:
        result = tuple(-coordinate for coordinate in result)
        sign = -1
    return result, sign * divisor


def family_direction(index):
    direction = H
    for _ in range(index):
        direction = matrix_vector(N, direction)
    normalized, multiplier = primitive(direction)
    if normalized != direction or multiplier != 1:
        raise AssertionError("family primitivity drift", index)
    return direction


def orbit_candidate(direction):
    if direction[0] <= 0 or direction[0] % 55:
        return None
    quotient = direction[0] // 55
    index = 0
    while quotient > 1 and quotient % 3 == 0:
        quotient //= 3
        index += 1
    return index if quotient == 1 else None


def recognize(direction):
    direction, _multiplier = primitive(direction)
    index = orbit_candidate(direction)
    if index is None or family_direction(index) != direction:
        return None
    return {
        "orbit_index": index,
        "phase": 8 if index % 2 == 0 else 16,
        "address_shell_n": index // 2 if index % 2 == 0 else (index + 1) // 2,
        "primitive_direction": list(direction),
    }


def relative_moment(direction):
    raw = cross(P_NUMERATOR, direction)
    if any(value % 22 for value in raw):
        raise AssertionError("nonintegral latent moment")
    return tuple(value // 22 for value in raw)


def verify_raw_inputs():
    for path, expected in EXPECTED_SHA256.items():
        observed = file_sha256(path)
        if observed != expected:
            raise AssertionError("raw input hash drift", str(path), observed)
    parent, _ = load_sealed(PARENT, expected=EXPECTED_PARENT_PAYLOAD)
    chronology, _ = load_sealed(
        CHRONOLOGY,
        field="checkpoint_payload_sha256",
        expected=EXPECTED_CHRONOLOGY_PAYLOAD,
    )
    alternates, _ = load_sealed(ALTERNATES, expected=EXPECTED_ALTERNATE_PAYLOAD)
    alternate_summary, _ = load_sealed(
        ALTERNATE_SUMMARY, expected=EXPECTED_ALT_SUMMARY_PAYLOAD
    )
    guarded_audit = load_json(GUARDED_AUDIT)
    if guarded_audit["result"]["guarded_cone_pair_counts_by_spectrum"] != {
        "11/3": 242,
        "348/275": 4,
    }:
        raise AssertionError("guarded audit cone count drift")
    return parent, chronology, alternates, alternate_summary


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def reconstruct(parent, chronology):
    parent_points = tuple(tuple(point) for point in parent["points"])
    parent_word = tuple(parent["flat_word"])
    if len(parent_points) != 8296 or len(parent_word) != 8295:
        raise AssertionError("parent extent drift")
    anchors = tuple(matrix_vector(M, point) for point in parent_points)
    points = list(anchors)
    identities = [
        {
            "kind": "anchor",
            "stable_id": f"anchor:L6:A{index}",
            "carried_from": f"guarded-L5:natural-point:{index}",
        }
        for index in range(len(anchors))
    ]
    seen = set()
    for rank, record in enumerate(chronology["selection_records"]):
        gap = record["gap"]
        if record["construction_rank"] != rank or gap in seen or (
            record["step"] != parent_word[gap]
        ):
            raise AssertionError("chronology order drift", rank)
        seen.add(gap)
        position = anchors[gap]
        for slot, letter in enumerate(record["selected_word"]):
            position = add(position, MENU[letter])
            if slot + 1 < len(record["selected_word"]):
                points.append(position)
                identities.append({
                    "kind": "connector_interior",
                    "stable_id": f"connector:L6:R{rank}:G{gap}:I{slot}",
                    "construction_rank": rank,
                    "gap": gap,
                    "interior_slot_zero_based": slot,
                })
        if position != anchors[gap + 1]:
            raise AssertionError("connector endpoint drift", rank)
    points = tuple(points)
    if len(seen) != 8295 or len(points) != 28804 or len(points) != len(set(points)):
        raise AssertionError("chronology final extent/repetition drift")
    if point_stream_sha256(points) != chronology["prefix"][
        "construction_order_point_stream_sha256"
    ] or stable_hash(sorted(points)) != chronology["prefix"]["point_set_sha256"]:
        raise AssertionError("chronology point commitment drift")
    extrema = {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }
    extrema["span"] = [
        extrema["maximum"][axis] - extrema["minimum"][axis]
        for axis in range(3)
    ]
    return parent_points, parent_word, anchors, points, tuple(identities), extrema


def enumerate_core(parent_points):
    records = []
    for later, point in enumerate(parent_points):
        px, py, pz = point
        for earlier in range(later):
            prior = parent_points[earlier]
            raw = (prior[0] - px, prior[1] - py, prior[2] - pz)
            if cone_residual(raw):
                continue
            direction, multiplier = primitive(raw)
            child_raw = matrix_vector(M, raw)
            child_direction, child_multiplier = primitive(child_raw)
            records.append({
                "earlier_natural_point_index": earlier,
                "later_natural_point_index": later,
                "earlier_L5_point": list(prior),
                "later_L5_point": list(point),
                "raw_L5_chord": list(raw),
                "canonical_L5_direction": list(direction),
                "signed_L5_multiplier": multiplier,
                "raw_L6_chord": list(child_raw),
                "canonical_L6_direction": list(child_direction),
                "signed_L6_multiplier": child_multiplier,
                "L6_endpoint_ids": [
                    f"anchor:L6:A{earlier}", f"anchor:L6:A{later}"
                ],
                "orbit_recognition_L5": recognize(direction),
                "orbit_recognition_L6": recognize(child_direction),
            })
    if len(records) != 4:
        raise AssertionError("independent 348/275 core count drift")
    return records


def scan_targets(parent_word, anchors, points, extrema):
    source_gaps = [gap for gap, step in enumerate(parent_word) if step == 8]
    if len(source_gaps) != 51:
        raise AssertionError("phase-8 source corridor count drift")
    included = []
    n = 1
    while True:
        direction = family_direction(2 * n)
        if direction[0] > extrema["span"][0]:
            exclusion = {
                "first_excluded_n": n,
                "primitive_direction": list(direction),
                "direction_x": direction[0],
                "maximum_observed_x_separation": extrema["span"][0],
                "reason": "primitive x-spacing exceeds the exact final coordinate span",
            }
            break
        included.append((n, direction))
        n += 1
    rows = []
    for n, direction in included:
        rel = relative_moment(direction)
        owners = {}
        for gap in source_gaps:
            moment = add(cross(anchors[gap], direction), rel)
            owners.setdefault(moment, []).append(gap)
        occupancy = Counter()
        first = {}
        parallel_pairs = []
        for point_index, point in enumerate(points):
            moment = cross(point, direction)
            if moment in owners:
                occupancy[moment] += 1
            if moment in first:
                parallel_pairs.append({
                    "earlier_point_index": first[moment],
                    "later_point_index": point_index,
                    "absolute_moment": list(moment),
                })
            else:
                first[moment] = point_index
        histogram = Counter(occupancy.get(moment, 0) for moment in owners)
        entries = []
        for moment in owners:
            if occupancy.get(moment, 0) >= 2:
                entries.append(list(moment))
        rows.append({
            "address_shell_n": n,
            "primitive_direction": list(direction),
            "relative_moment": list(rel),
            "source_step_8_corridors": len(source_gaps),
            "distinct_absolute_query_lines": len(owners),
            "query_line_occupancy_histogram": {
                str(key): histogram[key] for key in sorted(histogram)
            },
            "maximum_query_line_occupancy": max(histogram, default=0),
            "translated_family_entries": entries,
            "all_translation_parallel_pairs": parallel_pairs[:5],
            "all_translation_parallel_pair_count": len(parallel_pairs),
        })
    return source_gaps, included, exclusion, rows


def aggregate_alternates(alternates, alternate_summary):
    outcomes = Counter()
    for rank, record in enumerate(alternates["records"]):
        if record["construction_rank"] != rank or not record["domain_exhaustive"]:
            raise AssertionError("alternate record drift", rank)
        counts = record["outcome_counts"]
        if sum(counts.values()) != record["domain_words"] or counts.get(
            "survivor", 0
        ) != record["surviving_connector_choices"]:
            raise AssertionError("alternate partition drift", rank)
        outcomes.update(counts)
    domain = sum(outcomes.values())
    survivors = outcomes["survivor"]
    j348 = sum(
        count for category, count in outcomes.items() if category.endswith(":348/275")
    )
    if (len(alternates["records"]), domain, survivors, j348) != (
        8295,
        756_512_535,
        136_317_832,
        245_555,
    ):
        raise AssertionError("alternate aggregate drift")
    if alternate_summary["result"]["sum_surviving_connector_choices"] != survivors:
        raise AssertionError("alternate summary disagreement")
    return outcomes, domain, survivors, j348


def verify_recognizer_witness(witness):
    records = witness["recognizer_self_witnesses"]
    positive = records["positive"]
    earlier = tuple(positive["earlier"])
    later = tuple(positive["later"])
    anchor = tuple(positive["corridor_anchor"])
    direction, multiplier = primitive(subtract(later, earlier))
    recognition = recognize(direction)
    if recognition is None or recognition["phase"] != 8 or (
        cross(subtract(earlier, anchor), direction) != relative_moment(direction)
    ) or multiplier != 2:
        raise AssertionError("positive recognizer witness drift")
    negative = records["negative_parallel_translate"]
    negative_direction, _ = primitive(subtract(
        tuple(negative["later"]), tuple(negative["earlier"])
    ))
    if cross(
        subtract(tuple(negative["earlier"]), tuple(negative["corridor_anchor"])),
        negative_direction,
    ) == relative_moment(negative_direction):
        raise AssertionError("negative recognizer witness became a member")


def verify_theorem(summary, witness, core):
    if matrix_product(N, M) != ((9, 0, 0), (0, 9, 0), (0, 0, 9)):
        raise AssertionError("N M identity drift")
    checks = []
    for index in range(13):
        direction = family_direction(index)
        if direction[0] != 55 * 3**index or cone_residual(direction) != 0 or (
            direction[1] % 3 == 0
        ):
            raise AssertionError("family invariant drift", index)
        checks.append({
            "orbit_index": index,
            "direction": list(direction),
            "x_equals_55_times_3_to_index": True,
            "y_mod_3": direction[1] % 3,
            "cone_residual": 0,
        })
    theorem = witness["theorem_checks"]
    if checks != theorem["orbit_checks_m0_through_m12"]:
        raise AssertionError("theorem orbit check stream drift")
    phase16_seed = family_direction(1)
    for member in core:
        direction = tuple(member["canonical_L5_direction"])
        if orbit_candidate(direction) != 1 or direction == phase16_seed:
            raise AssertionError("base core intersects family orbit")
    if summary["verdict"]["code"] != "GUARDED_EXCLUSION_PROVED" or (
        summary["classifications"]["unguarded_reachable_exclusion"] != "UNPROVED"
    ) or summary["classifications"]["successor_availability"] != "UNPROVED":
        raise AssertionError("proof boundary classification drift")


def verify(summary_path, witness_path):
    summary, summary_hash = load_sealed(summary_path, schema=EXPECTED_SCHEMA)
    witness, witness_hash = load_sealed(
        witness_path, schema=EXPECTED_WITNESS_SCHEMA
    )
    if summary.get("auditor") != AUDITOR or witness.get("auditor") != AUDITOR:
        raise AssertionError("auditor signpost drift")
    if summary["witness"]["payload_sha256"] != witness_hash:
        raise AssertionError("summary does not commit to witness")
    producer = ROOT / summary["producer"]["path"]
    if file_sha256(producer) != summary["producer"]["sha256"]:
        raise AssertionError("producer source hash drift")

    parent, chronology, alternates, alternate_summary = verify_raw_inputs()
    parent_points, parent_word, anchors, points, _identities, extrema = reconstruct(
        parent, chronology
    )
    if extrema != summary["recorded_chronology"]["coordinate_extrema"]:
        raise AssertionError("coordinate extrema drift")

    core = enumerate_core(parent_points)
    if core != witness["inherited_j348_core"]:
        raise AssertionError("inherited core witness drift")
    if [record["canonical_L5_direction"] for record in core] != summary[
        "inherited_cone_core"
    ]["directions_L5"] or [
        record["canonical_L6_direction"] for record in core
    ] != summary["inherited_cone_core"]["directions_L6"]:
        raise AssertionError("summary inherited core drift")

    source_gaps, included, exclusion, rows = scan_targets(
        parent_word, anchors, points, extrema
    )
    target = witness["recorded_target_line_scan"]
    if source_gaps != target["source_corridor_gaps"] or [
        n for n, _direction in included
    ] != target["included_address_shells"] or exclusion != target[
        "spacing_cutoff"
    ] or rows != target["rows"]:
        raise AssertionError("recorded target-line replay drift")
    if any(row["translated_family_entries"] for row in rows) or any(
        row["all_translation_parallel_pair_count"] for row in rows
    ):
        raise AssertionError("latent secant unexpectedly found")

    outcomes, domain, survivors, j348 = aggregate_alternates(
        alternates, alternate_summary
    )
    alternate_record = summary["alternate_history_search"]
    if alternate_record["outcome_counts"] != dict(sorted(outcomes.items())) or (
        alternate_record["domain_word_occurrences"],
        alternate_record["surviving_connector_choices"],
        alternate_record["j348_guard_rejections"],
    ) != (domain, survivors, j348):
        raise AssertionError("summary alternate census drift")

    verify_recognizer_witness(witness)
    verify_theorem(summary, witness, core)
    return {
        "auditor": AUDITOR,
        "status": "verified",
        "verdict": "GUARDED_EXCLUSION_PROVED",
        "recorded_entries": 0,
        "inherited_j348_core": len(core),
        "alternate_prefixes": len(alternates["records"]),
        "alternate_domain_word_occurrences": domain,
        "alternate_survivors": survivors,
        "j348_guard_rejections": j348,
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
