#!/usr/bin/env python3
"""Exact reachable-entry audit for the fixed 3-adic latent family.

The audit answers one narrow question: can a translated member of the fixed
latent line family be born under the two-cone guarded policy descended from the
canonical guarded-L5 parent?  It independently replays the committed L5->L6
chronology, scans the inherited 348/275 cone core, checks every relevant
translated phase-8 line, and audits the exhaustive alternate-word census.

It does not claim successor availability or coverage of unguarded histories.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile


SCHEMA = "latent-family-reachable-entry-audit/v1"
WITNESS_SCHEMA = "latent-family-reachable-entry-witness/v1"
AUDITOR = "OpenAI Codex"
SIGNATURE = "[OpenAI Codex]"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARENT = Path("/tmp/guarded-L5-parent-canonical-v1.json")
DEFAULT_CHRONOLOGY = Path("/tmp/guarded-L5-to-L6-construction-v1.json")
DEFAULT_ALTERNATES = Path("/tmp/guarded-L5-to-L6-survivor-census-v2.json")
DEFAULT_GUARDED_AUDIT = ROOT / "design" / "guarded-L5-to-L6-audit-summary.json"
DEFAULT_ALTERNATE_SUMMARY = (
    ROOT / "design" / "guarded-L5-to-L6-survivor-census-summary.json"
)
DEFAULT_SUMMARY = ROOT / "design" / "latent-family-reachable-entry-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "latent-family-reachable-entry-witness.json"

EXPECTED_SHA256 = {
    "parent": "86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7",
    "chronology": "420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9",
    "alternates": "a69e490c544f65f51bdb178b27cd92b8ad359cb01af52de96c3b9cc796031aa2",
    "guarded_audit": "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36",
    "alternate_summary": "b49632699f6c0c3bcad43b8282d061ffc01cdbaeb013b98d8e0d9f80eaeadb77",
}
EXPECTED_PARENT_PAYLOAD = "70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258"
EXPECTED_CHRONOLOGY_PAYLOAD = "2a7043df6e2ad625527cabf4726033479d7eee53e3e10031c676961e6158570e"
EXPECTED_ALTERNATE_PAYLOAD = "197d600065a5611977fd06f9a5b58d600fb9e32d1fff848b0b7e343866df1d25"
EXPECTED_ALTERNATE_SUMMARY_PAYLOAD = (
    "42a844b40b14702a029a5b5a1125f8fe5d7c26d4eac7996fe923e958c5c340d4"
)
EXPECTED_PARENT_POINTS = 8_296
EXPECTED_GAPS = 8_295
EXPECTED_FINAL_POINTS = 28_804
EXPECTED_SOURCE_STEP_8_GAPS = 51
EXPECTED_DOMAIN_OCCURRENCES = 756_512_535
EXPECTED_SURVIVORS = 136_317_832
EXPECTED_J348_REJECTIONS = 245_555

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
H = (55, 34, 18)
P_NUMERATOR = (-99, -78, -62)
P_DENOMINATOR = 22
SOURCE_STEP = 8
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


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def seal(value):
    result = dict(value)
    result.pop("payload_sha256", None)
    result["payload_sha256"] = stable_hash(result)
    return result


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_sealed(path, field, expected_payload):
    value = load_json(path)
    claimed = value.get(field)
    payload = dict(value)
    payload.pop(field, None)
    if claimed != expected_payload or stable_hash(payload) != claimed:
        raise AssertionError("sealed input payload drift", str(path), field)
    return value


def atomic_json_dump(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
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


def primitive_with_multiplier(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    if divisor == 0:
        raise ValueError("zero displacement has no primitive direction")
    direction = tuple(coordinate // divisor for coordinate in vector)
    sign = 1
    if next(coordinate for coordinate in direction if coordinate) < 0:
        direction = tuple(-coordinate for coordinate in direction)
        sign = -1
    return direction, sign * divisor


def family_direction_by_orbit_index(index):
    if index < 0:
        raise ValueError("negative family orbit index")
    direction = H
    for _ in range(index):
        direction = matrix_vector(N, direction)
    primitive, multiplier = primitive_with_multiplier(direction)
    if multiplier != 1 or primitive != direction:
        raise AssertionError("latent orbit lost canonical primitivity", index)
    return direction


def orbit_index_candidate(direction):
    if direction[0] <= 0 or direction[0] % H[0]:
        return None
    quotient = direction[0] // H[0]
    index = 0
    while quotient > 1 and quotient % 3 == 0:
        quotient //= 3
        index += 1
    return index if quotient == 1 else None


def recognize_orbit_direction(direction):
    primitive, _multiplier = primitive_with_multiplier(direction)
    candidate = orbit_index_candidate(primitive)
    if candidate is None or family_direction_by_orbit_index(candidate) != primitive:
        return None
    if candidate % 2 == 0:
        return {
            "orbit_index": candidate,
            "phase": 8,
            "address_shell_n": candidate // 2,
            "primitive_direction": list(primitive),
        }
    return {
        "orbit_index": candidate,
        "phase": 16,
        "address_shell_n": (candidate + 1) // 2,
        "primitive_direction": list(primitive),
    }


def relative_moment(direction):
    numerator = cross(P_NUMERATOR, direction)
    if any(coordinate % P_DENOMINATOR for coordinate in numerator):
        raise AssertionError("latent relative moment is not integral", direction)
    return tuple(coordinate // P_DENOMINATOR for coordinate in numerator)


def recognize_phase8_entry(earlier, later, corridor_anchor):
    raw = subtract(later, earlier)
    direction, multiplier = primitive_with_multiplier(raw)
    orbit = recognize_orbit_direction(direction)
    if orbit is None or orbit["phase"] != 8 or orbit["address_shell_n"] < 1:
        return None
    observed = cross(subtract(earlier, corridor_anchor), direction)
    expected = relative_moment(direction)
    if observed != expected:
        return None
    return {
        **orbit,
        "raw_chord": list(raw),
        "signed_chord_multiplier": multiplier,
        "relative_moment": list(observed),
    }


def extended_gcd(left, right):
    old_r, current_r = abs(left), abs(right)
    old_s, current_s = 1, 0
    old_t, current_t = 0, 1
    while current_r:
        quotient = old_r // current_r
        old_r, current_r = current_r, old_r - quotient * current_r
        old_s, current_s = current_s, old_s - quotient * current_s
        old_t, current_t = current_t, old_t - quotient * current_t
    return (
        old_r,
        old_s if left >= 0 else -old_s,
        old_t if right >= 0 else -old_t,
    )


def integer_point_on_line(direction, moment):
    a, b, c = direction
    _u, v, w = moment
    divisor, coefficient_a, coefficient_b = extended_gcd(a, b)
    if w % divisor:
        raise AssertionError("moment is not in the saturated cross-map")
    x1 = coefficient_b * (w // divisor)
    x2 = -coefficient_a * (w // divisor)
    reduced_a = a // divisor
    rhs = -(v + c * x1)
    if rhs % reduced_a:
        raise AssertionError("integer line solve failed before reduction")
    parameter = 0 if divisor == 1 else (
        (rhs // reduced_a) * pow(c, -1, divisor) % divisor
    )
    x1 += reduced_a * parameter
    x2 += (b // divisor) * parameter
    numerator = v + c * x1
    if numerator % a:
        raise AssertionError("integer line solve failed")
    point = (x1, x2, numerator // a)
    if cross(point, direction) != moment:
        raise AssertionError("integer line point misses its Pluecker moment")
    return point


def validate_hashes(paths):
    observed = {name: file_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_SHA256.items():
        if observed[name] != expected:
            raise AssertionError("pinned input hash drift", name, observed[name], expected)
    return observed


def validate_inputs(paths):
    hashes = validate_hashes(paths)
    parent = load_sealed(paths["parent"], "payload_sha256", EXPECTED_PARENT_PAYLOAD)
    chronology = load_sealed(
        paths["chronology"],
        "checkpoint_payload_sha256",
        EXPECTED_CHRONOLOGY_PAYLOAD,
    )
    alternates = load_sealed(
        paths["alternates"], "payload_sha256", EXPECTED_ALTERNATE_PAYLOAD
    )
    guarded_audit = load_json(paths["guarded_audit"])
    alternate_summary = load_sealed(
        paths["alternate_summary"],
        "payload_sha256",
        EXPECTED_ALTERNATE_SUMMARY_PAYLOAD,
    )
    if parent.get("status") != (
        "deterministic canonical form of the independently certified guarded-L5 parent"
    ) or len(parent.get("points", [])) != EXPECTED_PARENT_POINTS:
        raise AssertionError("canonical guarded-L5 parent extent drift")
    if chronology.get("status") != "construction-complete-audit-pending" or (
        chronology.get("next_construction_rank") != EXPECTED_GAPS
        or len(chronology.get("selection_records", [])) != EXPECTED_GAPS
    ):
        raise AssertionError("guarded L5->L6 chronology is not complete")
    result = guarded_audit.get("result", {})
    if guarded_audit.get("terminal_payload_sha256") != (
        "9ccfe9b49cf545596f74d8934b762f35b6b71f88b6ab7d0ea03397b7e78af5ae"
    ) or result.get("points") != EXPECTED_FINAL_POINTS or result.get(
        "guarded_cone_pair_counts_by_spectrum"
    ) != {"11/3": 242, "348/275": 4}:
        raise AssertionError("independent guarded L6 audit drift")
    if alternate_summary["result"]["sum_surviving_connector_choices"] != (
        EXPECTED_SURVIVORS
    ):
        raise AssertionError("alternate survivor summary drift")
    return parent, chronology, alternates, guarded_audit, alternate_summary, hashes


def reconstruct_chronology(parent, chronology):
    parent_points = tuple(tuple(point) for point in parent["points"])
    parent_word = tuple(parent["flat_word"])
    if len(parent_points) != EXPECTED_PARENT_POINTS or len(parent_word) != EXPECTED_GAPS:
        raise AssertionError("guarded parent point/step extent drift")
    anchors = tuple(matrix_vector(M, point) for point in parent_points)
    if len(anchors) != len(set(anchors)):
        raise AssertionError("transported guarded anchors repeat")
    points = list(anchors)
    identities = [
        {
            "kind": "anchor",
            "stable_id": f"anchor:L6:A{index}",
            "carried_from": f"guarded-L5:natural-point:{index}",
        }
        for index in range(len(anchors))
    ]
    seen_gaps = set()
    for expected_rank, record in enumerate(chronology["selection_records"]):
        rank = record["construction_rank"]
        gap = record["gap"]
        step = record["step"]
        word = tuple(record["selected_word"])
        if rank != expected_rank or gap in seen_gaps or parent_word[gap] != step:
            raise AssertionError("guarded chronology schedule drift", expected_rank)
        seen_gaps.add(gap)
        position = anchors[gap]
        for slot, letter in enumerate(word):
            if not 0 <= letter < len(MENU):
                raise AssertionError("connector letter outside the fixed menu")
            position = add(position, MENU[letter])
            if slot + 1 < len(word):
                points.append(position)
                identities.append({
                    "kind": "connector_interior",
                    "stable_id": f"connector:L6:R{rank}:G{gap}:I{slot}",
                    "construction_rank": rank,
                    "gap": gap,
                    "interior_slot_zero_based": slot,
                })
        if position != anchors[gap + 1]:
            raise AssertionError("selected connector endpoint drift", rank, gap)
    if len(seen_gaps) != EXPECTED_GAPS or len(points) != EXPECTED_FINAL_POINTS:
        raise AssertionError("guarded chronology final extent drift")
    if len(points) != len(set(points)):
        raise AssertionError("guarded chronology repeats a point")
    points = tuple(points)
    if point_stream_sha256(points) != chronology["prefix"][
        "construction_order_point_stream_sha256"
    ] or stable_hash(sorted(points)) != chronology["prefix"]["point_set_sha256"]:
        raise AssertionError("guarded chronology point commitment drift")
    extrema = {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }
    extrema["span"] = [
        extrema["maximum"][axis] - extrema["minimum"][axis]
        for axis in range(3)
    ]
    return parent_points, parent_word, anchors, points, tuple(identities), extrema


def enumerate_base_j348_core(parent_points):
    matches = []
    for later, point in enumerate(parent_points):
        px, py, pz = point
        for earlier in range(later):
            prior = parent_points[earlier]
            x = prior[0] - px
            y = prior[1] - py
            z = prior[2] - pz
            raw = (x, y, z)
            if cone_residual(raw) != 0:
                continue
            direction, multiplier = primitive_with_multiplier(raw)
            child_raw = matrix_vector(M, raw)
            child_direction, child_multiplier = primitive_with_multiplier(child_raw)
            matches.append({
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
                    f"anchor:L6:A{earlier}",
                    f"anchor:L6:A{later}",
                ],
                "orbit_recognition_L5": recognize_orbit_direction(direction),
                "orbit_recognition_L6": recognize_orbit_direction(child_direction),
            })
    if len(matches) != 4:
        raise AssertionError("guarded-L5 348/275 core size drift", len(matches))
    return matches


def possible_phase8_directions(extrema):
    included = []
    n = 1
    while True:
        direction = family_direction_by_orbit_index(2 * n)
        if abs(direction[0]) > extrema["span"][0]:
            return included, {
                "first_excluded_n": n,
                "primitive_direction": list(direction),
                "direction_x": direction[0],
                "maximum_observed_x_separation": extrema["span"][0],
                "reason": "primitive x-spacing exceeds the exact final coordinate span",
            }
        included.append((n, direction))
        n += 1


def scan_recorded_target_lines(parent_word, anchors, points, identities, extrema):
    source_gaps = tuple(
        gap for gap, step in enumerate(parent_word) if step == SOURCE_STEP
    )
    if len(source_gaps) != EXPECTED_SOURCE_STEP_8_GAPS:
        raise AssertionError("phase-8 corridor count drift", len(source_gaps))
    included, exclusion = possible_phase8_directions(extrema)
    rows = []
    total_parallel_pairs = 0
    for n, direction in included:
        relative = relative_moment(direction)
        owners_by_moment = {}
        for gap in source_gaps:
            absolute = add(cross(anchors[gap], direction), relative)
            owners_by_moment.setdefault(absolute, []).append(gap)
        occupants = {moment: [] for moment in owners_by_moment}
        first_by_moment = {}
        parallel_pairs = []
        for point_index, point in enumerate(points):
            moment = cross(point, direction)
            if moment in occupants:
                occupants[moment].append(point_index)
            previous = first_by_moment.get(moment)
            if previous is None:
                first_by_moment[moment] = point_index
            else:
                parallel_pairs.append({
                    "earlier_point_index": previous,
                    "later_point_index": point_index,
                    "absolute_moment": list(moment),
                })
        occupancy_histogram = Counter(len(value) for value in occupants.values())
        entries = []
        for moment, point_indices in occupants.items():
            if len(point_indices) >= 2:
                entries.append({
                    "absolute_moment": list(moment),
                    "owner_gaps": owners_by_moment[moment],
                    "endpoints": [
                        {
                            "point": list(points[index]),
                            "identity": identities[index],
                        }
                        for index in point_indices[:2]
                    ],
                })
        total_parallel_pairs += len(parallel_pairs)
        rows.append({
            "address_shell_n": n,
            "primitive_direction": list(direction),
            "relative_moment": list(relative),
            "source_step_8_corridors": len(source_gaps),
            "distinct_absolute_query_lines": len(owners_by_moment),
            "query_line_occupancy_histogram": {
                str(key): occupancy_histogram[key]
                for key in sorted(occupancy_histogram)
            },
            "maximum_query_line_occupancy": max(occupancy_histogram, default=0),
            "translated_family_entries": entries,
            "all_translation_parallel_pairs": parallel_pairs[:5],
            "all_translation_parallel_pair_count": len(parallel_pairs),
        })
    if total_parallel_pairs != 0 or any(row["translated_family_entries"] for row in rows):
        raise AssertionError("recorded chronology contains a latent-family secant")
    return {
        "source_step": SOURCE_STEP,
        "source_corridor_gaps": list(source_gaps),
        "included_address_shells": [n for n, _direction in included],
        "spacing_cutoff": exclusion,
        "rows": rows,
        "verdict": "EXACT FINITE: no phase-8 latent-family entry on the recorded guarded L5->L6 chronology",
    }


def audit_alternates(alternates, alternate_summary):
    records = alternates["records"]
    if len(records) != EXPECTED_GAPS:
        raise AssertionError("alternate census stitch extent drift")
    outcomes = Counter()
    for rank, record in enumerate(records):
        if record["construction_rank"] != rank or not record["domain_exhaustive"]:
            raise AssertionError("alternate census rank/domain drift", rank)
        counts = record["outcome_counts"]
        if sum(counts.values()) != record["domain_words"]:
            raise AssertionError("alternate outcome partition drift", rank)
        if counts.get("survivor", 0) != record["surviving_connector_choices"]:
            raise AssertionError("alternate survivor count drift", rank)
        outcomes.update(counts)
    domain = sum(outcomes.values())
    survivors = outcomes["survivor"]
    j348_rejections = sum(
        count for category, count in outcomes.items() if category.endswith(":348/275")
    )
    if (domain, survivors, j348_rejections) != (
        EXPECTED_DOMAIN_OCCURRENCES,
        EXPECTED_SURVIVORS,
        EXPECTED_J348_REJECTIONS,
    ):
        raise AssertionError("alternate census aggregate drift")
    summary_result = alternate_summary["result"]
    if summary_result["sum_surviving_connector_choices"] != survivors or (
        alternate_summary["interpretation"]["proved"]
        != "all 8,295 realized prefixes have at least 71 surviving canonical guarded connectors"
    ):
        raise AssertionError("alternate summary/full artifact disagreement")
    return {
        "classification": "EXACT FINITE",
        "realized_prefixes": len(records),
        "domain_word_occurrences": domain,
        "surviving_connector_choices": survivors,
        "j348_guard_rejections": j348_rejections,
        "outcome_counts": dict(sorted(outcomes.items())),
        "scope": (
            "every connector word at each of the 8,295 recorded prefixes; "
            "not successor availability after taking an alternate word"
        ),
    }


def recognizer_self_witnesses():
    corridor_anchor = (17, -11, 5)
    direction = family_direction_by_orbit_index(2)
    relative = relative_moment(direction)
    base_relative = integer_point_on_line(direction, relative)
    earlier = add(corridor_anchor, base_relative)
    later = add(earlier, tuple(2 * coordinate for coordinate in direction))
    positive = recognize_phase8_entry(earlier, later, corridor_anchor)
    if positive is None or positive["address_shell_n"] != 1 or (
        positive["signed_chord_multiplier"] != 2
    ):
        raise AssertionError("positive family-entry self-witness failed")
    shifted = add(earlier, (1, 0, 0))
    negative = recognize_phase8_entry(
        shifted,
        add(shifted, tuple(2 * coordinate for coordinate in direction)),
        corridor_anchor,
    )
    if negative is not None:
        raise AssertionError("parallel translated nonmember passed recognizer")
    return {
        "positive": {
            "corridor_anchor": list(corridor_anchor),
            "earlier": list(earlier),
            "later": list(later),
            "recognition": positive,
        },
        "negative_parallel_translate": {
            "corridor_anchor": list(corridor_anchor),
            "earlier": list(shifted),
            "later": list(add(
                shifted, tuple(2 * coordinate for coordinate in direction)
            )),
            "recognition": negative,
        },
    }


def theorem_record(core):
    if cone_residual(H) != 0:
        raise AssertionError("latent seed left the guarded 348/275 cone")
    orbit_checks = []
    for index in range(13):
        direction = family_direction_by_orbit_index(index)
        if cone_residual(direction) != 0 or direction[0] != 55 * 3**index:
            raise AssertionError("latent orbit invariant drift", index)
        if direction[1] % 3 == 0:
            raise AssertionError("latent orbit primitivity residue drift", index)
        orbit_checks.append({
            "orbit_index": index,
            "direction": list(direction),
            "x_equals_55_times_3_to_index": True,
            "y_mod_3": direction[1] % 3,
            "cone_residual": 0,
        })
    inverse_identity = matrix_product(N, M)
    if inverse_identity != ((9, 0, 0), (0, 9, 0), (0, 0, 9)):
        raise AssertionError("N M = 9I identity drift")
    core_disjointness = []
    phase_16_seed = family_direction_by_orbit_index(1)
    for member in core:
        direction = tuple(member["canonical_L5_direction"])
        candidate = orbit_index_candidate(direction)
        if candidate != 1 or direction == phase_16_seed:
            raise AssertionError("unexpected inherited-core orbit relation")
        core_disjointness.append({
            "direction": list(direction),
            "x_forces_orbit_index": candidate,
            "N_to_index_H": list(phase_16_seed),
            "equal": False,
        })
    return {
        "classification": "PROVED",
        "guard_equation": "275*q(g)-348*g_x^2=0",
        "family_cone_membership": (
            "F(H)=0 and F(Ng)=9F(g), so every N^m H is in the 348/275 cone"
        ),
        "guard_birth_implication": (
            "the two-cone guarded predicate rejects every old-new and "
            "same-word new-new pair with F=0; therefore it rejects every "
            "latent-family birth before moment or corridor phase matters"
        ),
        "carriage_identity": "N*M=9I and F(Mg)=9F(g)",
        "orbit_primitivity": (
            "the y-coordinate of N^m H is nonzero modulo 3; primes other "
            "than 3 cannot enter the content because det(N)=27 and H is primitive"
        ),
        "orbit_checks_m0_through_m12": orbit_checks,
        "base_core_disjointness": core_disjointness,
        "all_level_policy_relative_theorem": (
            "For every finite history descended from the canonical guarded-L5 "
            "parent in which each connector word satisfies the same two-cone "
            "birth guard, no phase-8 translated latent line L_n with n>=1, "
            "and no phase-16 intermediate, is a secant at any prefix. The only "
            "348/275 pairs are four carried base lineages, and none lies in or "
            "can enter the projective N-orbit of H."
        ),
        "proof_boundary": (
            "This theorem is conditional on the guarded policy and canonical "
            "parent. It does not prove connector availability and does not "
            "cover globally triple-free histories that omit the two-cone guard."
        ),
    }


def build_payload(args):
    paths = {
        "parent": args.parent,
        "chronology": args.chronology,
        "alternates": args.alternates,
        "guarded_audit": args.guarded_audit,
        "alternate_summary": args.alternate_summary,
    }
    (
        parent,
        chronology,
        alternates,
        guarded_audit,
        alternate_summary,
        hashes,
    ) = validate_inputs(paths)
    (
        parent_points,
        parent_word,
        anchors,
        points,
        identities,
        extrema,
    ) = reconstruct_chronology(parent, chronology)
    core = enumerate_base_j348_core(parent_points)
    target_scan = scan_recorded_target_lines(
        parent_word, anchors, points, identities, extrema
    )
    alternate_scan = audit_alternates(alternates, alternate_summary)
    theorem = theorem_record(core)
    witness = {
        "schema": WITNESS_SCHEMA,
        "auditor": AUDITOR,
        "signature": SIGNATURE,
        "recognizer_self_witnesses": recognizer_self_witnesses(),
        "inherited_j348_core": core,
        "recorded_target_line_scan": target_scan,
        "theorem_checks": theorem,
    }
    witness = seal(witness)
    summary = {
        "schema": SCHEMA,
        "auditor": AUDITOR,
        "signature": SIGNATURE,
        "status": "proved guarded-policy latent-family exclusion",
        "classifications": {
            "canonical_entry_predicate": "PROVED",
            "recorded_guarded_L5_to_L6": "EXACT FINITE",
            "alternate_words_at_recorded_prefixes": "EXACT FINITE",
            "guarded_birth_exclusion": "PROVED",
            "guarded_all_level_orbit_exclusion": "PROVED",
            "unguarded_reachable_exclusion": "UNPROVED",
            "successor_availability": "UNPROVED",
        },
        "source_bindings": {
            name: {"path": str(paths[name]), "sha256": hashes[name]}
            for name in paths
        },
        "canonical_predicate": {
            "direction": (
                "canonical_primitive(b-a)=N^(2n)H for the unique n>=1 "
                "forced by the exact x-coordinate"
            ),
            "moment": "(a-r) cross g_n = (P_NUMERATOR cross g_n)/22",
            "H": list(H),
            "P_NUMERATOR": list(P_NUMERATOR),
            "P_DENOMINATOR": P_DENOMINATOR,
            "representative_independence": (
                "the chord is reduced to a canonical primitive direction; "
                "the signed integer multiplier is retained separately"
            ),
        },
        "recorded_chronology": {
            "level": "guarded L5 -> L6",
            "initial_anchors": len(anchors),
            "connector_interiors": len(points) - len(anchors),
            "final_points": len(points),
            "source_step_8_corridors": EXPECTED_SOURCE_STEP_8_GAPS,
            "coordinate_extrema": extrema,
            "included_address_shells": target_scan["included_address_shells"],
            "spacing_cutoff": target_scan["spacing_cutoff"],
            "translated_entry_count": sum(
                len(row["translated_family_entries"])
                for row in target_scan["rows"]
            ),
            "all_translation_parallel_pair_count": sum(
                row["all_translation_parallel_pair_count"]
                for row in target_scan["rows"]
            ),
            "claim": target_scan["verdict"],
        },
        "inherited_cone_core": {
            "classification": "EXACT FINITE",
            "J_348_over_275_pairs": len(core),
            "directions_L5": [
                member["canonical_L5_direction"] for member in core
            ],
            "directions_L6": [
                member["canonical_L6_direction"] for member in core
            ],
            "latent_orbit_intersections": 0,
        },
        "alternate_history_search": alternate_scan,
        "symbolic_closure": theorem,
        "verdict": {
            "code": "GUARDED_EXCLUSION_PROVED",
            "classification": "PROVED",
            "statement": theorem["all_level_policy_relative_theorem"],
            "remaining_boundary": theorem["proof_boundary"],
        },
        "witness": {
            "path": str(args.witness),
            "payload_sha256": witness["payload_sha256"],
        },
        "producer": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": file_sha256(Path(__file__).resolve()),
        },
    }
    return seal(summary), witness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--chronology", type=Path, default=DEFAULT_CHRONOLOGY)
    parser.add_argument("--alternates", type=Path, default=DEFAULT_ALTERNATES)
    parser.add_argument("--guarded-audit", type=Path, default=DEFAULT_GUARDED_AUDIT)
    parser.add_argument(
        "--alternate-summary", type=Path, default=DEFAULT_ALTERNATE_SUMMARY
    )
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()
    summary, witness = build_payload(args)
    atomic_json_dump(witness, args.witness)
    atomic_json_dump(summary, args.summary)
    print(json.dumps({
        "auditor": AUDITOR,
        "status": summary["status"],
        "verdict": summary["verdict"]["code"],
        "recorded_entries": summary["recorded_chronology"][
            "translated_entry_count"
        ],
        "alternate_survivors": summary["alternate_history_search"][
            "surviving_connector_choices"
        ],
        "inherited_core": summary["inherited_cone_core"][
            "J_348_over_275_pairs"
        ],
        "summary_payload_sha256": summary["payload_sha256"],
        "witness_payload_sha256": witness["payload_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
