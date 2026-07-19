#!/usr/bin/env python3
"""Fail-closed compact merger for the 65 preregistered L5 range certificates.

This verifier does not rescan secant pairs.  It verifies the immutable output
of ``lattice_t_role_first_holonomy_reachability.py`` at its actual trust
boundary: the amended frozen checker, its upstream files and dependencies,
the exact 65-leaf preregistered partition of later endpoint IDs ``[1, 8268)``,
every chunk's raw-file and internal-payload commitments, and the exact total
pair coverage.  It also independently checks record identities, elementary
integer line geometry, effect references, and the encoding and cryptographic
integrity of serialized killed-word masks.

The merged certificate is deliberately compact.  It commits to all 4,597
birth records and all raw mask bytes by SHA-256, but emits only aggregate birth
statistics, the three small effect witnesses, and mask metadata with the
``raw_hex`` fields removed.  The 65 source snapshots remain listed so every
source file is individually attributable.

The merger intentionally does not load the connector domains, enumerate the
words hit by a candidate site, or prove that the reported candidate-hit sites
are exhaustive.  It therefore does not independently recompute killed-word
membership.  Those geometric/domain semantics remain a pinned dependency on
the frozen source checker and its sealed chunks; adding the roughly 1.8-GiB
domain load would change this compact integrity verifier into a second heavy
experiment.

This is a verifier for one completed finite L5 census, not a replacement for
the source checker and not a proof of recurrence, contraction, positive
availability, or an unconditional theorem.  The L6 range partition is outside
this script's scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CHECKER = (
    ROOT / "design" / "lattice_t_role_first_holonomy_reachability.py"
)
RANGE_PLAN = ROOT / "design" / "ROLE-FIRST-RANGE-PLAN.md"
DEFAULT_INPUT_DIRECTORY = Path("/tmp")
DEFAULT_OUTPUT = Path("/tmp/lattice-T-role-first-l5-merged-v1.json")

SCHEMA_VERSION = 1
EXPECTED_SOURCE_SCHEMA_VERSION = 1
EXPECTED_SOURCE_STATUS = (
    "exact role-first primary-lineage holonomy reachability chunk; "
    "finite evidence only"
)
EXPECTED_SOURCE_DATE = "2026-07-18"
EXPECTED_SOURCE_CHECKER_SHA256 = (
    "19b95490e8f9f74cb0ae7ea89e8caed58c36c107dcd0143ef3f280c36b388f64"
)
EXPECTED_RANGE_PLAN_SHA256 = (
    "fadbd29255b939a99b9379129e28092eb9279dcbfceaedf8cacb18e18d4c0b72"
)

EXPECTED_CHUNKS = 65
EXPECTED_FIRST_LATER_ID = 1
EXPECTED_LAST_LATER_ID = 8_268
EXPECTED_STANDARD_WIDTH = 128
EXPECTED_L5_POINTS = 8_268
EXPECTED_PAIRS = 34_175_778
EXPECTED_MATCHED_BIRTHS = 4_597
EXPECTED_EFFECTS = 3
EXPECTED_MASK_RECORD_APPEARANCES = 3
EXPECTED_UNIQUE_MASKS = 3
EXPECTED_ACTUAL_MAPS = 1
EXPECTED_ACTUAL_OCCURRENCES = 4
EXPECTED_ACTUAL_GUARD_KEYS = 166

# This single digest seals the ordered list of all 65 records containing each
# filename, byte count, raw SHA-256, internal payload SHA-256, half-open range,
# pair count, birth count, effect count, and mask-record count.  Thus the
# verifier has a compact hard pin for every completed chunk without embedding
# 65 independent blocks of constants in executable code.
EXPECTED_CHUNK_MANIFEST_SHA256 = (
    "6c55ce8f989acbc4fc11d7cb03dd095c3c50ebac30ed16fa105469cac9641c95"
)
EXPECTED_PINNED_INPUTS_SHA256 = (
    "908b46823a57e22d4115142d6a9d97845b5db5f9393c83d2a89a0adcb62d1c7e"
)
EXPECTED_DEPENDENCIES_SHA256 = (
    "9ca777240feb563fc7c7e9ee03022099b3d38a2924cfbc78c5669664d0acd865"
)
EXPECTED_ROLE_FILTER_SHA256 = (
    "a0c825d5486dcfd8ffcae0afa32e74603aae9879e5c007816ec16bc279aa7661"
)
EXPECTED_RESOURCE_POLICY_SHA256 = (
    "afc79a79e33d9e41643c8bd0ae751e5ac97e5ca1f6ab0055674d255ed9fcdcf6"
)
EXPECTED_PROVED_SHA256 = (
    "0418470c69a63300c54f71384aa3942042ba931955c868d3a05d7200dc74492a"
)
EXPECTED_NOT_PROVED_SHA256 = (
    "82ca8a93049b546015b59f7233f1c91b86af600077a8ec776f7f96b747c7fea2"
)
EXPECTED_COMMON_SCOPE_SHA256 = (
    "012d6d108f2f26ffa9352602b69cfa0f6f5d04207617bd7d6e0832be5d8e8957"
)

EXPECTED_BIRTH_RECORD_STREAM_SHA256 = (
    "09ad6eb3900333d63a651a847b57a1031f89a3e7e2a0d92c318c1b296ee61126"
)
EXPECTED_LINE_ID_STREAM_SHA256 = (
    "c409f04dcb2f7e7e1e386eabb37d931d5e33d758366bf3d2f5d610d878132480"
)
EXPECTED_ENDPOINT_PAIR_STREAM_SHA256 = (
    "16c6330f097be223dbf28c6dd26b73c4dc7c50515345bb8870c2dc2f821a883d"
)
EXPECTED_CLASSIFICATION_HISTOGRAM_SHA256 = (
    "2f7e2efbbf3b1ba0dfe7ee9b3ae62f4836773d16ceb620beacf35998e08cf0ad"
)
EXPECTED_GUARD_HISTOGRAM_SHA256 = (
    "b53758775c0205aa85df03b49a675fbe0f2017c7138bf54e63123f489cf5ccb5"
)
EXPECTED_LATER_ID_HISTOGRAM_SHA256 = (
    "c03cbccf06cb2e7c14e4dfcef139bb5525c9c186cbee6896ad59a181733f2ee0"
)
EXPECTED_EFFECT_RECORD_STREAM_SHA256 = (
    "3ff25aec6b6b63616a9fa53f526f614040540756723c73313a1754f35c96140a"
)
EXPECTED_EFFECT_ID_STREAM_SHA256 = (
    "bd2c72e416409d89e8ac8591fef94dee3a173dd142f1ec7f225ada5abf47539f"
)
EXPECTED_RAW_MASK_RECORD_STREAM_SHA256 = (
    "6961bc664c33e1e1a1571c8aa8131183548f0eb0f392c05b5b29b103924f9d09"
)
EXPECTED_COMPACT_MASK_STREAM_SHA256 = (
    "6ca04e3e0de1fdfa2c5b09f213ff1430dc2a290a9770c1026158f6438a0c9326"
)

EXPECTED_CLASSIFICATION_HISTOGRAM = {
    "inherited-base-base": 1_527,
    "old-new": 2_960,
    "same-word-new-new": 110,
}

EXPECTED_DEPENDENCIES = {
    "holonomy": (
        "bd1b8308216bb47f9c83d3f2ed2a50e30011d623ea63030f6cde82203a0b536b"
    ),
    "l5_auditor": (
        "8c616ea15a7aaae3e1d70f07415dd74641c2cf4fafa22050c873d31bb1ac64e8"
    ),
    "l5_producer": (
        "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
    ),
    "l6_auditor": (
        "b9f39fd20dfad194d45420b221617cf6b1baa872aa2aa1f4a38182274dece6f5"
    ),
    "l6_producer": (
        "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
    ),
}
DEPENDENCY_PATHS = {
    "holonomy": ROOT / "design" / "lattice_t_short_return_holonomy.py",
    "l5_auditor": ROOT / "design" / "lattice_t_chronological_audit.py",
    "l5_producer": ROOT / "design" / "lattice_t_chronological_replay.py",
    "l6_auditor": ROOT / "design" / "lattice_t_l6_audit.py",
    "l6_producer": ROOT / "design" / "lattice_t_l6_continuation.py",
}

EXPECTED_INPUT_PINS = {
    "holonomy_raw": {
        "bytes": 97_258_680,
        "sha256": (
            "a1789f881fcced4abe6ac2d5aed2f001b867cae815a8c2c59dcd601aaee6d6bc"
        ),
        "payload_field": None,
    },
    "holonomy_summary": {
        "bytes": 7_690,
        "sha256": (
            "242dc1281ac84dc124844d0dc05b9f1e4f76f8b79c3973317493802c2bc4f3e8"
        ),
        "payload_field": None,
    },
    "primary_L5_source": {
        "bytes": 5_369_433,
        "sha256": (
            "9c711e396dc75042b747a1bcacb5093aa8b4c84c316a89081b2e246bdae0c2b8"
        ),
        "payload_field": "checkpoint_payload_sha256",
        "payload_sha256": (
            "4957ae7456b95d9d1c0033077eee136dfcda820e2ae4fdb9f1037490457dd71c"
        ),
    },
    "primary_L5_summary": {
        "bytes": 3_061,
        "sha256": (
            "88fa0f41674d71cc9cf84fc1bd4b70949ab91cd1e8d83a435bb7b6bec5fc9df5"
        ),
        "payload_field": None,
    },
    "primary_L5_terminal": {
        "bytes": 3_437,
        "sha256": (
            "144eb1d78a2a9c62be0747be50a2e135a8b8e91d5d2335e64398bf5af5146194"
        ),
        "payload_field": "terminal_payload_sha256",
        "payload_sha256": (
            "832e8ce9c44f2528ffd3e39996572b3622e5d4b29ed47bfa593621d8c346528b"
        ),
    },
    "terminal_primary_L6_audit": {
        "bytes": 3_497,
        "sha256": (
            "86241cb942d2a35c702dd6f8cc9a0db0c173ded7c99dd97f72c0e0123fac8b1d"
        ),
        "payload_field": "terminal_payload_sha256",
        "payload_sha256": (
            "5f8ea3468d14ee187fd4b7a7fb6ae16f2df28829d6001bd8332a2fc2ff034ff5"
        ),
    },
    "terminal_primary_L6_source": {
        "bytes": 18_699_543,
        "sha256": (
            "82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7"
        ),
        "payload_field": "checkpoint_payload_sha256",
        "payload_sha256": (
            "772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa"
        ),
    },
}

TOP_LEVEL_KEYS = {
    "schema_version", "date", "status", "checker", "resource_policy",
    "pinned_inputs", "pinned_dependencies", "scope", "role_first_filter",
    "birth_and_effect_result", "proved", "not_proved", "payload_sha256",
}
RESULT_KEYS = {
    "pairs_scanned", "matched_line_births", "effect_witnesses",
    "killed_word_masks",
}
BIRTH_KEYS = {
    "birth_layer", "classification", "earlier_point_id", "earlier_point",
    "earlier_provenance", "later_point_id", "later_point",
    "later_provenance", "birth_rank", "canonical_primitive_direction",
    "exact_Pluecker_moment", "guard_key", "polynomial",
    "actual_two_endpoint_secant", "line_id",
}
PROVENANCE_KEYS = {
    "point_id", "birth_kind", "birth_rank", "gap", "interior_slot",
    "source_point_id", "source_ordered_chain_index",
}
EFFECT_KEYS = {
    "line_id", "occurrence_id", "map_id", "guard_key",
    "guard_record_ids", "fixed_point_moment_test", "phases",
    "silent_then_returned_reveal", "effect_id",
}
PHASE_KEYS = {
    "phase", "step", "line", "present_before_stitch",
    "candidate_hit_sites", "applicable_killed_word_mask_id",
    "selected_word_killed",
}
LINE_KEYS = {
    "canonical_primitive_direction", "exact_Pluecker_moment", "guard_key",
}
MASK_KEYS = {
    "mask_id", "step", "hit_sites", "bit_order", "domain_words",
    "full_domain", "zero_envelope",
}
MASK_PAYLOAD_KEYS = {"bytes", "members", "sha256", "raw_hex"}

PROCESS_START_MERGER_SHA256 = None


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_MERGER_SHA256 = file_sha256(Path(__file__).resolve())


def assert_merger_unchanged():
    observed = file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_MERGER_SHA256:
        raise RuntimeError(
            "L5 range merger changed during execution",
            PROCESS_START_MERGER_SHA256,
            observed,
        )


def require_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise AssertionError(label + " schema drift", sorted(value), sorted(expected))


def require_integer_vector(value, label):
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise AssertionError(label + " is not an integer 3-vector", value)
    return tuple(value)


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def dot(left, right):
    return sum(left[index] * right[index] for index in range(3))


def primitive_direction(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise AssertionError("zero secant direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def guard_key(direction):
    x, y, z = direction
    quadratic = 3 * y * y - y * z + 3 * z * z
    x_squared = x * x
    divisor = math.gcd(x_squared, quadratic)
    if not divisor:
        raise AssertionError("zero guard-key divisor")
    return (x_squared // divisor, quadratic // divisor)


def parse_fraction(value, label):
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        or value[1] <= 0
    ):
        raise AssertionError(label + " fraction schema drift", value)
    result = Fraction(value[0], value[1])
    if [result.numerator, result.denominator] != value:
        raise AssertionError(label + " fraction is not canonical", value)
    return result


def parse_fraction_vector(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise AssertionError(label + " fraction-vector extent drift")
    return tuple(
        parse_fraction(item, label + f"[{index}]")
        for index, item in enumerate(value)
    )


def fraction_vector_record(value):
    return [[item.numerator, item.denominator] for item in value]


def expected_ranges():
    result = []
    for index in range(EXPECTED_CHUNKS):
        first = EXPECTED_FIRST_LATER_ID + EXPECTED_STANDARD_WIDTH * index
        last = min(first + EXPECTED_STANDARD_WIDTH, EXPECTED_LAST_LATER_ID)
        result.append((first, last))
    if result[-1] != (8_193, 8_268):
        raise AssertionError("internal expected-range construction drift")
    return tuple(result)


def expected_filename(first, last):
    return f"lattice-T-role-first-l5-{first:05d}-{last:05d}-v1.json"


def verify_static_files():
    observed_checker = file_sha256(SOURCE_CHECKER)
    observed_plan = file_sha256(RANGE_PLAN)
    if observed_checker != EXPECTED_SOURCE_CHECKER_SHA256:
        raise AssertionError("frozen role-first checker drift", observed_checker)
    if observed_plan != EXPECTED_RANGE_PLAN_SHA256:
        raise AssertionError("preregistered range plan drift", observed_plan)
    observed_dependencies = {
        name: file_sha256(path) for name, path in DEPENDENCY_PATHS.items()
    }
    if observed_dependencies != EXPECTED_DEPENDENCIES:
        raise AssertionError(
            "role-first dependency drift",
            EXPECTED_DEPENDENCIES,
            observed_dependencies,
        )
    return observed_dependencies


def verify_sealed_json(path, payload_field, expected_payload):
    with Path(path).open() as handle:
        value = json.load(handle)
    observed = value.pop(payload_field, None)
    if observed != expected_payload or stable_hash(value) != expected_payload:
        raise AssertionError("upstream JSON payload drift", str(path), observed)


def verify_upstream_files(pinned_inputs):
    if stable_hash(pinned_inputs) != EXPECTED_PINNED_INPUTS_SHA256:
        raise AssertionError("common pinned-input table drift")
    if set(pinned_inputs) != set(EXPECTED_INPUT_PINS):
        raise AssertionError("pinned-input name set drift")
    for name, expected in EXPECTED_INPUT_PINS.items():
        record = pinned_inputs[name]
        expected_keys = {"path", "bytes", "sha256"}
        if expected["payload_field"] is not None:
            expected_keys.add("payload_sha256")
        require_keys(record, expected_keys, name + " snapshot")
        if (
            record["bytes"] != expected["bytes"]
            or record["sha256"] != expected["sha256"]
            or not is_sha256(record["sha256"])
        ):
            raise AssertionError(name + " frozen pin drift")
        path = Path(record["path"])
        if path.stat().st_size != expected["bytes"]:
            raise AssertionError(name + " current byte-size drift")
        if file_sha256(path) != expected["sha256"]:
            raise AssertionError(name + " current file digest drift")
        payload_field = expected["payload_field"]
        if payload_field is not None:
            if record.get("payload_sha256") != expected["payload_sha256"]:
                raise AssertionError(name + " snapshot payload drift")
            verify_sealed_json(path, payload_field, expected["payload_sha256"])


def validate_resource_policy(policy):
    if stable_hash(policy) != EXPECTED_RESOURCE_POLICY_SHA256:
        raise AssertionError("source resource-policy commitment drift")
    threads = policy.get("thread_environment", {})
    if (
        policy.get("processes") != 1
        or policy.get("threads") != 1
        or policy.get("process_nice", -1) < 15
        or set(threads.values()) != {"1"}
        or policy.get("work_time_abort_threshold_seconds") != 120.0
        or policy.get("hard_ceiling_seconds") != 120.0
        or policy.get("maximum_later_ids_per_chunk") != 128
        or policy.get("resident_abort_threshold_bytes") != 300 * 1024 * 1024
    ):
        raise AssertionError("source resource policy is not preregistered")


def validate_role_filter(role_filter):
    if stable_hash(role_filter) != EXPECTED_ROLE_FILTER_SHA256:
        raise AssertionError("common role-first filter commitment drift")
    if (
        role_filter.get("actual_affine_map_count") != EXPECTED_ACTUAL_MAPS
        or role_filter.get("actual_occurrence_count")
        != EXPECTED_ACTUAL_OCCURRENCES
        or role_filter.get("actual_other_guard_key_count")
        != EXPECTED_ACTUAL_GUARD_KEYS
        or role_filter.get("whole_word_slot_child_gap_correlation_preserved")
        is not True
    ):
        raise AssertionError("role-first filter extent/claim drift")
    maps = role_filter.get("actual_affine_maps")
    occurrences = role_filter.get("actual_hierarchical_occurrences")
    keys = role_filter.get("actual_other_guard_keys")
    if (
        not isinstance(maps, list)
        or not isinstance(occurrences, list)
        or not isinstance(keys, list)
        or len(maps) != EXPECTED_ACTUAL_MAPS
        or len(occurrences) != EXPECTED_ACTUAL_OCCURRENCES
        or len(keys) != EXPECTED_ACTUAL_GUARD_KEYS
    ):
        raise AssertionError("role-first filter list extent drift")
    if keys != sorted(keys) or len({tuple(key) for key in keys}) != len(keys):
        raise AssertionError("role-first guard-key list is not canonical")
    map_by_id = {}
    guard_records_by_map = {}
    map_key_union = set()
    for record in maps:
        map_id = record.get("map_id")
        controls = record.get("controls")
        if map_id != stable_hash({"controls": controls}) or map_id in map_by_id:
            raise AssertionError("role-first affine-map identity drift")
        map_by_id[map_id] = record
        local_guards = {}
        local_keys = set()
        for guard in record.get("guard_records", ()):
            guard_id = guard.get("guard_record_id")
            body = {key: value for key, value in guard.items() if key != "guard_record_id"}
            if guard_id != stable_hash(body) or guard_id in local_guards:
                raise AssertionError("role-first guard-record identity drift")
            local_guards[guard_id] = guard
            local_keys.add(tuple(guard["guard_key"]))
        if record.get("other_guard_keys") != [list(key) for key in sorted(local_keys)]:
            raise AssertionError("role-first map guard-key projection drift")
        guard_records_by_map[map_id] = local_guards
        map_key_union.update(local_keys)
    occurrence_by_id = {}
    for record in occurrences:
        occurrence_id = record.get("occurrence_id")
        body = {key: value for key, value in record.items() if key != "occurrence_id"}
        if (
            occurrence_id != stable_hash(body)
            or occurrence_id in occurrence_by_id
            or record.get("map_id") not in map_by_id
            or record.get("parent_step") != 8
            or record.get("child_step") != 16
            or record.get("returned_step") != 8
        ):
            raise AssertionError("role-first occurrence identity/role drift")
        occurrence_by_id[occurrence_id] = record
    if set(map_key_union) != {tuple(key) for key in keys}:
        raise AssertionError("role-first global guard-key union drift")
    return map_by_id, occurrence_by_id, guard_records_by_map


def validate_birth(record, first, last, relevant_keys):
    require_keys(record, BIRTH_KEYS, "birth record")
    line_id = record["line_id"]
    body = {key: value for key, value in record.items() if key != "line_id"}
    if line_id != stable_hash(body):
        raise AssertionError("birth line identity drift", line_id)
    earlier_id = record["earlier_point_id"]
    later_id = record["later_point_id"]
    if (
        isinstance(earlier_id, bool)
        or isinstance(later_id, bool)
        or not isinstance(earlier_id, int)
        or not isinstance(later_id, int)
        or not 0 <= earlier_id < later_id
        or not first <= later_id < last
    ):
        raise AssertionError("birth endpoint-ID/range drift", line_id)
    earlier = require_integer_vector(record["earlier_point"], "earlier point")
    later = require_integer_vector(record["later_point"], "later point")
    direction = require_integer_vector(
        record["canonical_primitive_direction"], "birth direction"
    )
    moment = require_integer_vector(record["exact_Pluecker_moment"], "birth moment")
    if direction != primitive_direction(subtract(later, earlier)):
        raise AssertionError("birth primitive direction drift", line_id)
    if moment != cross(earlier, direction) or dot(direction, moment):
        raise AssertionError("birth Pluecker moment drift", line_id)
    key = guard_key(direction)
    if list(key) != record["guard_key"] or key not in relevant_keys:
        raise AssertionError("birth guard-key drift", line_id)
    require_keys(record["earlier_provenance"], PROVENANCE_KEYS, "earlier provenance")
    require_keys(record["later_provenance"], PROVENANCE_KEYS, "later provenance")
    if (
        record["earlier_provenance"]["point_id"] != earlier_id
        or record["later_provenance"]["point_id"] != later_id
        or record["birth_rank"] != record["later_provenance"]["birth_rank"]
        or record["birth_layer"] != "l5"
        or record["actual_two_endpoint_secant"] is not True
    ):
        raise AssertionError("birth provenance drift", line_id)
    earlier_rank = record["earlier_provenance"]["birth_rank"]
    later_rank = record["later_provenance"]["birth_rank"]
    classification = (
        "inherited-base-base"
        if later_rank == -1
        else "same-word-new-new"
        if earlier_rank == later_rank
        else "old-new"
    )
    polynomial = (
        f"{key[0]}*(3*y^2-y*z+3*z^2)-{key[1]}*r^2"
    )
    if (
        record["classification"] != classification
        or record["polynomial"] != polynomial
    ):
        raise AssertionError("birth classification/polynomial drift", line_id)


def validate_mask(record):
    require_keys(record, MASK_KEYS, "mask record")
    require_keys(record["full_domain"], MASK_PAYLOAD_KEYS, "full mask")
    require_keys(record["zero_envelope"], MASK_PAYLOAD_KEYS, "zero mask")
    if record["bit_order"] != (
        "ordinal n is bit ((n-1) mod 8) of byte floor((n-1)/8)"
    ):
        raise AssertionError("mask bit-order drift")
    words = record["domain_words"]
    if isinstance(words, bool) or not isinstance(words, int) or words <= 0:
        raise AssertionError("mask domain extent drift")
    try:
        raw = bytes.fromhex(record["full_domain"]["raw_hex"])
        zero = bytes.fromhex(record["zero_envelope"]["raw_hex"])
    except (TypeError, ValueError) as error:
        raise AssertionError("mask raw hex is malformed") from error
    byte_count = (words + 7) // 8
    if len(raw) != byte_count or len(zero) != byte_count:
        raise AssertionError("mask byte extent drift")
    for label, payload, encoded in (
        ("full", record["full_domain"], raw),
        ("zero", record["zero_envelope"], zero),
    ):
        if (
            payload["bytes"] != len(encoded)
            or payload["members"] != sum(value.bit_count() for value in encoded)
            or payload["sha256"] != hashlib.sha256(encoded).hexdigest()
        ):
            raise AssertionError(label + " mask digest/population drift")
    if any(zero[index] & ~raw[index] for index in range(byte_count)):
        raise AssertionError("zero-envelope mask is not a subset of full mask")
    used_last_bits = words % 8
    if used_last_bits:
        allowed = (1 << used_last_bits) - 1
        if raw[-1] & ~allowed or zero[-1] & ~allowed:
            raise AssertionError("mask has nonzero padding bits")
    sites = record["hit_sites"]
    if sites != sorted(sites) or len({tuple(site) for site in sites}) != len(sites):
        raise AssertionError("mask hit sites repeat or are noncanonical")
    for site in sites:
        require_integer_vector(site, "mask hit site")
    identity = {
        "step": record["step"],
        "hit_sites": sites,
        "raw_sha256": record["full_domain"]["sha256"],
        "zero_sha256": record["zero_envelope"]["sha256"],
    }
    if record["mask_id"] != stable_hash(identity):
        raise AssertionError("mask identity drift", record["mask_id"])


def validate_line_token(line, expected_key, label):
    require_keys(line, LINE_KEYS, label)
    direction = require_integer_vector(
        line["canonical_primitive_direction"], label + " direction"
    )
    moment = require_integer_vector(line["exact_Pluecker_moment"], label + " moment")
    if direction != primitive_direction(direction) or dot(direction, moment):
        raise AssertionError(label + " primitive/Pluecker drift")
    if guard_key(direction) != expected_key or line["guard_key"] != list(expected_key):
        raise AssertionError(label + " guard-key drift")
    return direction, moment


def validate_effect(
    effect, chunk_births, chunk_masks, map_by_id, occurrence_by_id,
    guard_records_by_map,
):
    require_keys(effect, EFFECT_KEYS, "effect record")
    effect_id = effect["effect_id"]
    body = {key: value for key, value in effect.items() if key != "effect_id"}
    if effect_id != stable_hash(body):
        raise AssertionError("effect identity drift", effect_id)
    birth = chunk_births.get(effect["line_id"])
    occurrence = occurrence_by_id.get(effect["occurrence_id"])
    map_record = map_by_id.get(effect["map_id"])
    if birth is None or occurrence is None or map_record is None:
        raise AssertionError("effect references an unknown birth/role/map")
    if occurrence["map_id"] != effect["map_id"]:
        raise AssertionError("effect occurrence/map correlation drift")
    key = tuple(effect["guard_key"])
    if key != tuple(birth["guard_key"]):
        raise AssertionError("effect/birth guard-key drift")
    local_guards = guard_records_by_map[effect["map_id"]]
    for guard_id in effect["guard_record_ids"]:
        guard = local_guards.get(guard_id)
        if guard is None or tuple(guard["guard_key"]) != key:
            raise AssertionError("effect guard-record reference drift")
    phases = effect["phases"]
    expected_phases = (
        ("start_8", 8),
        ("middle_16", 16),
        ("returned_8_future_L7", 8),
    )
    if not isinstance(phases, list) or len(phases) != len(expected_phases):
        raise AssertionError("L5 effect phase extent drift")
    any_applicable = False
    for phase, expected in zip(phases, expected_phases):
        require_keys(phase, PHASE_KEYS, "effect phase")
        if (phase["phase"], phase["step"]) != expected:
            raise AssertionError("L5 effect phase order/type drift")
        direction, moment = validate_line_token(phase["line"], key, phase["phase"])
        sites = phase["candidate_hit_sites"]
        if sites != sorted(sites) or len({tuple(site) for site in sites}) != len(sites):
            raise AssertionError("effect candidate sites are noncanonical")
        for site_record in sites:
            site = require_integer_vector(site_record, "effect candidate site")
            if cross(site, direction) != moment:
                raise AssertionError("effect candidate site misses its line")
        applicable = bool(sites) and phase["present_before_stitch"] is True
        any_applicable = any_applicable or applicable
        mask_id = phase["applicable_killed_word_mask_id"]
        if applicable:
            mask = chunk_masks.get(mask_id)
            if (
                mask is None
                or mask["step"] != phase["step"]
                or mask["hit_sites"] != sites
            ):
                raise AssertionError("effect phase/mask reference drift")
        elif mask_id is not None:
            raise AssertionError("inapplicable effect phase names a mask")
        if (
            phase["present_before_stitch"] is True
            and phase["selected_word_killed"] is True
        ):
            raise AssertionError("effect contradicts audited selected-word legality")
        if phase["phase"] == "returned_8_future_L7":
            if phase["selected_word_killed"] is not None:
                raise AssertionError("future returned phase claims a selected word")
        elif not isinstance(phase["selected_word_killed"], bool):
            raise AssertionError("selected-word killed flag schema drift")
    if not any_applicable:
        raise AssertionError("effect witness has no applicable candidate hit")
    expected_silent = (
        phases[0]["present_before_stitch"] is True
        and not phases[0]["candidate_hit_sites"]
        and not phases[1]["candidate_hit_sites"]
        and bool(phases[2]["candidate_hit_sites"])
    )
    if effect["silent_then_returned_reveal"] is not expected_silent:
        raise AssertionError("silent-then-returned flag drift")
    fixed_test = effect["fixed_point_moment_test"]
    expected_fraction = parse_fraction_vector(
        fixed_test["expected_p_cross_direction"], "expected fixed moment"
    )
    observed_fraction = parse_fraction_vector(
        fixed_test["observed_centered_moment"], "observed centered moment"
    )
    fixed = parse_fraction_vector(map_record["fixed_point"], "map fixed point")
    start_direction = tuple(phases[0]["line"]["canonical_primitive_direction"])
    computed_expected = cross(fixed, start_direction)
    computed_observed = tuple(
        Fraction(value) for value in phases[0]["line"]["exact_Pluecker_moment"]
    )
    if (
        fixed_test["fixed_point_phase"] != "start_8"
        or expected_fraction != computed_expected
        or observed_fraction != computed_observed
        or fixed_test["equal"] is not (expected_fraction == observed_fraction)
    ):
        raise AssertionError("effect fixed-point moment test drift")


def compact_mask(record):
    return {
        "mask_id": record["mask_id"],
        "step": record["step"],
        "hit_sites": record["hit_sites"],
        "bit_order": record["bit_order"],
        "domain_words": record["domain_words"],
        "full_domain": {
            key: value for key, value in record["full_domain"].items()
            if key != "raw_hex"
        },
        "zero_envelope": {
            key: value for key, value in record["zero_envelope"].items()
            if key != "raw_hex"
        },
    }


def common_scope(scope):
    return {
        key: value for key, value in scope.items()
        if key not in {
            "later_point_id_half_open_range", "later_endpoint_id_partition"
        }
    }


def load_and_verify_chunks(input_directory):
    input_directory = Path(input_directory).resolve()
    ranges = expected_ranges()
    expected_names = [expected_filename(first, last) for first, last in ranges]
    observed_names = sorted(
        path.name
        for path in input_directory.glob("lattice-T-role-first-l5-*-v1.json")
    )
    if observed_names != expected_names:
        missing = sorted(set(expected_names) - set(observed_names))
        extra = sorted(set(observed_names) - set(expected_names))
        raise AssertionError("L5 range-file partition drift", missing, extra)

    chunks = []
    births = []
    effects = []
    raw_masks = []
    references = None
    role_context = None
    total_pairs = 0
    total_mask_appearances = 0
    seen_line_ids = set()
    seen_effect_ids = set()

    for (first, last), name in zip(ranges, expected_names):
        path = input_directory / name
        raw_file = path.read_bytes()
        file_digest = hashlib.sha256(raw_file).hexdigest()
        value = json.loads(raw_file)
        require_keys(value, TOP_LEVEL_KEYS, name + " top level")
        payload = value.pop("payload_sha256")
        if not is_sha256(payload) or payload != stable_hash(value):
            raise AssertionError("source chunk payload seal drift", name)
        value["payload_sha256"] = payload
        if (
            value["schema_version"] != EXPECTED_SOURCE_SCHEMA_VERSION
            or value["date"] != EXPECTED_SOURCE_DATE
            or value["status"] != EXPECTED_SOURCE_STATUS
            or value["checker"] != {
                "path": "design/lattice_t_role_first_holonomy_reachability.py",
                "sha256": EXPECTED_SOURCE_CHECKER_SHA256,
                "unchanged_during_run": True,
            }
        ):
            raise AssertionError("source chunk status/checker drift", name)
        validate_resource_policy(value["resource_policy"])
        if stable_hash(value["pinned_dependencies"]) != EXPECTED_DEPENDENCIES_SHA256:
            raise AssertionError("source dependency-table drift", name)
        if value["pinned_dependencies"] != EXPECTED_DEPENDENCIES:
            raise AssertionError("source dependency pins drift", name)

        scope = value["scope"]
        partition = scope.get("later_endpoint_id_partition", {})
        if (
            scope.get("later_point_id_half_open_range") != [first, last]
            or partition != {
                "first_inclusive": first,
                "last_exclusive": last,
                "hard_maximum_partition_width": EXPECTED_STANDARD_WIDTH,
            }
            or scope.get("birth_layer") != "l5"
            or scope.get("birth_layer_points") != EXPECTED_L5_POINTS
            or scope.get("all_birth_pairs_in_range_scanned_without_cutoff")
            is not True
            or scope.get("spatial_distance_cutoff_within_id_partition") is not None
            or scope.get("endpoint_distance_cutoff_within_id_partition") is not None
            or stable_hash(common_scope(scope)) != EXPECTED_COMMON_SCOPE_SHA256
        ):
            raise AssertionError("source chunk scope/cutoff drift", name)

        result = value["birth_and_effect_result"]
        require_keys(result, RESULT_KEYS, name + " result")
        expected_pairs = (last - first) * (first + last - 1) // 2
        if result["pairs_scanned"] != expected_pairs:
            raise AssertionError("source chunk pair-count drift", name)
        total_pairs += expected_pairs
        chunk_birth_records = result["matched_line_births"]
        chunk_effect_records = result["effect_witnesses"]
        chunk_mask_records = result["killed_word_masks"]
        if (
            [record.get("line_id") for record in chunk_birth_records]
            != sorted(record.get("line_id") for record in chunk_birth_records)
            or [record.get("effect_id") for record in chunk_effect_records]
            != sorted(record.get("effect_id") for record in chunk_effect_records)
            or [record.get("mask_id") for record in chunk_mask_records]
            != sorted(record.get("mask_id") for record in chunk_mask_records)
        ):
            raise AssertionError("source chunk result streams are noncanonical", name)

        role_filter = value["role_first_filter"]
        if role_context is None:
            role_context = validate_role_filter(role_filter)
        elif stable_hash(role_filter) != EXPECTED_ROLE_FILTER_SHA256:
            raise AssertionError("role-first filter differs across chunks", name)
        map_by_id, occurrence_by_id, guard_records_by_map = role_context
        relevant_keys = {
            tuple(key) for key in role_filter["actual_other_guard_keys"]
        }
        local_births = {}
        for record in chunk_birth_records:
            validate_birth(record, first, last, relevant_keys)
            line_id = record["line_id"]
            if line_id in seen_line_ids or line_id in local_births:
                raise AssertionError("birth line repeats across partition", line_id)
            seen_line_ids.add(line_id)
            local_births[line_id] = record
        local_masks = {}
        for record in chunk_mask_records:
            validate_mask(record)
            mask_id = record["mask_id"]
            known = local_masks.get(mask_id)
            if known is not None and known != record:
                raise AssertionError("one chunk gives two bodies for a mask ID")
            local_masks[mask_id] = record
        referenced_masks = set()
        for record in chunk_effect_records:
            validate_effect(
                record, local_births, local_masks, map_by_id,
                occurrence_by_id, guard_records_by_map,
            )
            effect_id = record["effect_id"]
            if effect_id in seen_effect_ids:
                raise AssertionError("effect repeats across partition", effect_id)
            seen_effect_ids.add(effect_id)
            referenced_masks.update(
                phase["applicable_killed_word_mask_id"]
                for phase in record["phases"]
                if phase["applicable_killed_word_mask_id"] is not None
            )
        if referenced_masks != set(local_masks):
            raise AssertionError("source chunk has orphan or missing masks", name)

        source_common = {
            "pinned_inputs": value["pinned_inputs"],
            "pinned_dependencies": value["pinned_dependencies"],
            "resource_policy": value["resource_policy"],
            "role_first_filter_sha256": stable_hash(role_filter),
            "proved": value["proved"],
            "not_proved": value["not_proved"],
            "common_scope": common_scope(scope),
        }
        if references is None:
            references = source_common
        elif source_common != references:
            raise AssertionError("source chunks disagree on common evidence", name)

        chunks.append({
            "file_name": name,
            "bytes": len(raw_file),
            "file_sha256": file_digest,
            "payload_sha256": payload,
            "range": [first, last],
            "pairs_scanned": expected_pairs,
            "matched_line_births": len(chunk_birth_records),
            "effect_witnesses": len(chunk_effect_records),
            "killed_word_mask_records": len(chunk_mask_records),
        })
        births.extend(chunk_birth_records)
        effects.extend(chunk_effect_records)
        raw_masks.extend(chunk_mask_records)
        total_mask_appearances += len(chunk_mask_records)

    if stable_hash(chunks) != EXPECTED_CHUNK_MANIFEST_SHA256:
        raise AssertionError("65-file frozen chunk manifest drift")
    if total_pairs != EXPECTED_PAIRS or total_pairs != (
        EXPECTED_L5_POINTS * (EXPECTED_L5_POINTS - 1) // 2
    ):
        raise AssertionError("complete L5 unordered-pair coverage drift")
    return {
        "chunks": chunks,
        "births": births,
        "effects": effects,
        "raw_masks": raw_masks,
        "total_pairs": total_pairs,
        "mask_appearances": total_mask_appearances,
        "references": references,
        "role_context": role_context,
    }


def aggregate_verified_data(data):
    births = sorted(data["births"], key=lambda record: record["line_id"])
    effects = sorted(data["effects"], key=lambda record: record["effect_id"])
    masks_by_id = {}
    for record in data["raw_masks"]:
        mask_id = record["mask_id"]
        known = masks_by_id.get(mask_id)
        if known is not None and known != record:
            raise AssertionError("same global mask ID has two bodies")
        masks_by_id[mask_id] = record
    raw_masks = [masks_by_id[key] for key in sorted(masks_by_id)]
    compact_masks = [compact_mask(record) for record in raw_masks]

    if (
        len(births) != EXPECTED_MATCHED_BIRTHS
        or len(effects) != EXPECTED_EFFECTS
        or data["mask_appearances"] != EXPECTED_MASK_RECORD_APPEARANCES
        or len(raw_masks) != EXPECTED_UNIQUE_MASKS
    ):
        raise AssertionError("merged L5 birth/effect/mask extent drift")
    endpoint_pairs = [
        [record["earlier_point_id"], record["later_point_id"]]
        for record in births
    ]
    if len({tuple(pair) for pair in endpoint_pairs}) != len(endpoint_pairs):
        raise AssertionError("merged birth endpoint pairs repeat")
    classifications = dict(sorted(Counter(
        record["classification"] for record in births
    ).items()))
    guard_counts = Counter(tuple(record["guard_key"]) for record in births)
    guard_histogram = [
        {"guard_key": list(key), "births": guard_counts[key]}
        for key in sorted(guard_counts)
    ]
    later_counts = Counter(record["later_point_id"] for record in births)
    later_histogram = [
        [later_id, later_counts[later_id]] for later_id in sorted(later_counts)
    ]

    commitments = {
        "birth_record_stream_sha256": stable_hash(births),
        "line_id_stream_sha256": stable_hash([
            record["line_id"] for record in births
        ]),
        "endpoint_pair_stream_sha256": stable_hash(endpoint_pairs),
        "classification_histogram_sha256": stable_hash(classifications),
        "guard_histogram_sha256": stable_hash(guard_histogram),
        "later_id_histogram_sha256": stable_hash(later_histogram),
        "effect_record_stream_sha256": stable_hash(effects),
        "effect_id_stream_sha256": stable_hash([
            record["effect_id"] for record in effects
        ]),
        "raw_mask_record_stream_sha256": stable_hash(raw_masks),
        "compact_mask_stream_sha256": stable_hash(compact_masks),
    }
    expected = {
        "birth_record_stream_sha256": EXPECTED_BIRTH_RECORD_STREAM_SHA256,
        "line_id_stream_sha256": EXPECTED_LINE_ID_STREAM_SHA256,
        "endpoint_pair_stream_sha256": EXPECTED_ENDPOINT_PAIR_STREAM_SHA256,
        "classification_histogram_sha256": (
            EXPECTED_CLASSIFICATION_HISTOGRAM_SHA256
        ),
        "guard_histogram_sha256": EXPECTED_GUARD_HISTOGRAM_SHA256,
        "later_id_histogram_sha256": EXPECTED_LATER_ID_HISTOGRAM_SHA256,
        "effect_record_stream_sha256": EXPECTED_EFFECT_RECORD_STREAM_SHA256,
        "effect_id_stream_sha256": EXPECTED_EFFECT_ID_STREAM_SHA256,
        "raw_mask_record_stream_sha256": EXPECTED_RAW_MASK_RECORD_STREAM_SHA256,
        "compact_mask_stream_sha256": EXPECTED_COMPACT_MASK_STREAM_SHA256,
    }
    if commitments != expected:
        raise AssertionError("merged L5 result commitment drift", commitments)
    if classifications != EXPECTED_CLASSIFICATION_HISTOGRAM:
        raise AssertionError("merged birth classification histogram drift")
    return {
        "births": births,
        "effects": effects,
        "compact_masks": compact_masks,
        "classifications": classifications,
        "guard_histogram": guard_histogram,
        "later_histogram": later_histogram,
        "commitments": commitments,
    }


def verify_chunk_files_unchanged(input_directory, chunk_records):
    input_directory = Path(input_directory).resolve()
    for record in chunk_records:
        path = input_directory / record["file_name"]
        if (
            path.stat().st_size != record["bytes"]
            or file_sha256(path) != record["file_sha256"]
        ):
            raise RuntimeError(
                "source chunk changed during merge", record["file_name"]
            )


def build_summary(data, aggregate, dependencies):
    references = data["references"]
    pinned_inputs = references["pinned_inputs"]
    verify_upstream_files(pinned_inputs)
    if stable_hash(references["proved"]) != EXPECTED_PROVED_SHA256:
        raise AssertionError("source proved-list drift")
    if stable_hash(references["not_proved"]) != EXPECTED_NOT_PROVED_SHA256:
        raise AssertionError("source not-proved-list drift")
    map_by_id, occurrence_by_id, _guards = data["role_context"]
    effects = aggregate["effects"]
    fixed_equal = sum(
        effect["fixed_point_moment_test"]["equal"] is True
        for effect in effects
    )
    silent_return = sum(
        effect["silent_then_returned_reveal"] is True for effect in effects
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-19",
        "status": (
            "verified compact merge of the complete preregistered primary-L5 "
            "role-first later-endpoint partition; finite evidence only"
        ),
        "merger": {
            "path": "design/lattice_t_role_first_l5_range_merge.py",
            "sha256": PROCESS_START_MERGER_SHA256,
            "unchanged_during_run": True,
            "rescan_of_secant_pairs": False,
            "connector_domains_loaded": False,
            "killed_word_membership_recomputed": False,
            "candidate_hit_site_completeness_recomputed": False,
        },
        "frozen_source": {
            "checker": {
                "path": "design/lattice_t_role_first_holonomy_reachability.py",
                "sha256": EXPECTED_SOURCE_CHECKER_SHA256,
            },
            "preregistered_plan": {
                "path": "design/ROLE-FIRST-RANGE-PLAN.md",
                "sha256": EXPECTED_RANGE_PLAN_SHA256,
            },
            "pinned_inputs": pinned_inputs,
            "pinned_inputs_sha256": EXPECTED_PINNED_INPUTS_SHA256,
            "pinned_dependencies": dependencies,
            "pinned_dependencies_sha256": EXPECTED_DEPENDENCIES_SHA256,
            "source_proved_claims": references["proved"],
            "source_not_proved_claims": references["not_proved"],
        },
        "partition": {
            "birth_layer": "l5",
            "later_point_id_half_open_range": [
                EXPECTED_FIRST_LATER_ID, EXPECTED_LAST_LATER_ID,
            ],
            "birth_layer_points": EXPECTED_L5_POINTS,
            "preregistered_initial_chunks": EXPECTED_CHUNKS,
            "successful_leaf_chunks": len(data["chunks"]),
            "bisections_required": 0,
            "contiguous_exact_cover": True,
            "all_birth_pairs_scanned_without_cutoff_in_each_chunk": True,
            "spatial_distance_cutoff": None,
            "endpoint_distance_cutoff": None,
            "unordered_pairs_covered": data["total_pairs"],
            "expected_complete_unordered_pairs": EXPECTED_PAIRS,
        },
        "source_chunks": {
            "records": data["chunks"],
            "record_count": len(data["chunks"]),
            "record_stream_sha256": EXPECTED_CHUNK_MANIFEST_SHA256,
            "each_raw_file_and_internal_payload_seal_verified": True,
        },
        "resource_parameter_audit": {
            "recorded_max_seconds": 120.0,
            "recorded_processes": 1,
            "recorded_threads": 1,
            "recorded_minimum_nice_satisfied": True,
            "selected_max_births_serialized_by_source_schema": False,
            "selected_max_effects_serialized_by_source_schema": False,
            "hard_checker_max_births": 20_000,
            "hard_checker_max_effects": 20_000,
            "interpretation": (
                "the exact CLI birth/effect cap arguments cannot be recovered "
                "from these source files; successful status, exhaustive scope, "
                "and counts below the checker hard maxima prove that neither "
                "cap truncated any certified chunk"
            ),
        },
        "role_first_filter": {
            "actual_affine_maps": len(map_by_id),
            "actual_hierarchical_occurrences": len(occurrence_by_id),
            "actual_other_guard_keys": EXPECTED_ACTUAL_GUARD_KEYS,
            "map_ids": sorted(map_by_id),
            "occurrence_ids": sorted(occurrence_by_id),
            "complete_common_filter_sha256": EXPECTED_ROLE_FILTER_SHA256,
            "whole_word_slot_child_gap_correlation_preserved": True,
        },
        "merged_result": {
            "pairs_scanned": data["total_pairs"],
            "matched_line_births": len(aggregate["births"]),
            "birth_classification_histogram": aggregate["classifications"],
            "distinct_birth_guard_keys": len(aggregate["guard_histogram"]),
            "birth_guard_key_histogram": aggregate["guard_histogram"],
            "later_endpoint_ids_with_matched_births": len(
                aggregate["later_histogram"]
            ),
            "effect_witnesses": len(effects),
            "fixed_point_moment_equal_effects": fixed_equal,
            "silent_then_returned_reveal_effects": silent_return,
            "effect_records": effects,
            "raw_mask_record_appearances": data["mask_appearances"],
            "unique_killed_word_masks": len(aggregate["compact_masks"]),
            "compact_mask_records": aggregate["compact_masks"],
            "raw_mask_hex_omitted_from_merge": True,
            "commitments": aggregate["commitments"],
        },
        "verified": [
            "the amended checker and preregistered range plan match their frozen SHA-256 pins",
            "all current upstream inputs and checker dependencies match the snapshots shared by all 65 chunks",
            "the 65 immutable chunks form the exact contiguous preregistered cover [1,8268) with no bisections or omissions",
            "all 34,175,778 unordered primary-L5 point pairs belong to exactly one certified later-endpoint partition",
            "every source file has its pinned raw digest and a valid internal payload seal",
            "all reported birth IDs, elementary integer line data, and effect references were independently checked",
            "serialized raw masks were checked for byte encoding, SHA-256, population, padding, and zero-envelope subset integrity",
            "the compact result commits to every full birth, effect, and raw-mask record without reproducing raw mask hex",
        ],
        "not_proved": [
            "an independent rescan of all 34,175,778 secant pairs by this merger",
            "candidate-hit-site completeness or killed-word membership recomputed from the connector domains; those semantics remain pinned to the frozen source checker and chunks",
            "the exact --max-births and --max-effects CLI values used for each source run, because the source schema did not serialize them",
            "coverage of the separately preregistered primary-L6 later-endpoint partition",
            "that a projective guard-key match is an affine fixed-point line when the reported moment equality is false",
            "repeatability, a closed far-secant transfer state, contraction or ranking, positive connector availability, a safety greatest fixed point, or an unconditional theorem",
        ],
    }
    summary["payload_sha256"] = stable_hash(summary)
    return summary


def atomic_json_dump(value, output):
    output = Path(output).resolve()
    if output.parent != Path("/tmp").resolve():
        raise RuntimeError("merged certificate output must be directly under /tmp")
    if output.exists():
        raise FileExistsError("immutable merged output already exists", str(output))
    descriptor, temporary = tempfile.mkstemp(
        dir=output.parent, prefix=output.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        assert_merger_unchanged()
        os.link(temporary, output)
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return {
        "path": str(output),
        "bytes": output.stat().st_size,
        "sha256": file_sha256(output),
        "payload_sha256": value["payload_sha256"],
    }


def run(args):
    dependencies = verify_static_files()
    data = load_and_verify_chunks(args.input_directory)
    aggregate = aggregate_verified_data(data)
    summary = build_summary(data, aggregate, dependencies)
    verify_chunk_files_unchanged(args.input_directory, data["chunks"])
    if verify_static_files() != dependencies:
        raise RuntimeError("frozen checker/dependency files changed during merge")
    assert_merger_unchanged()
    if args.verify_only:
        return {
            "status": summary["status"],
            "write_performed": False,
            "payload_sha256": summary["payload_sha256"],
            "chunks": len(data["chunks"]),
            "pairs_scanned": data["total_pairs"],
            "matched_line_births": len(aggregate["births"]),
            "effect_witnesses": len(aggregate["effects"]),
        }
    output = Path(args.output).resolve()
    input_paths = {
        (Path(args.input_directory).resolve() / record["file_name"]).resolve()
        for record in data["chunks"]
    }
    if output in input_paths or output in {SOURCE_CHECKER.resolve(), RANGE_PLAN.resolve()}:
        raise RuntimeError("merged output aliases a protected source")
    snapshot = atomic_json_dump(summary, output)
    return {
        "status": summary["status"],
        "write_performed": True,
        "output": snapshot,
        "chunks": len(data["chunks"]),
        "pairs_scanned": data["total_pairs"],
        "matched_line_births": len(aggregate["births"]),
        "effect_witnesses": len(aggregate["effects"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-directory", default=str(DEFAULT_INPUT_DIRECTORY)
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
