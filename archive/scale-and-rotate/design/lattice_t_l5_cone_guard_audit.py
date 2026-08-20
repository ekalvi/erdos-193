#!/usr/bin/env python3
"""Fail-closed independent audit of the guarded lattice-T L5 replay.

The construction checkpoint is read-only and fully pinned.  This checker
uses it only for the chosen cache ordinal/word at each stitch.  It rebuilds
the inherited L4 anchor state from the pinned L5 inputs and independently
rescans every compact-cache ordinal through the stored winner.  A candidate
survives exactly when it is zero-T, globally fresh in the (y,z) projection,
exactly legal against the complete chronological prefix, and creates no
secant in either of the two named projective cones.

The checker does not trust the constructor's rejection counters, legality
memo, cone witnesses, or prefix reconstruction.  Fresh optimized and
reference legality memos are used for each audited stitch and disagreement is
fatal.  An earlier guarded survivor is fatal.

After firstness, a second pass assembles the one realized walk in natural gap
order.  It verifies the terminal projection invariant and scans every point
against every earlier point.  That scan simultaneously proves ordinary
no-three-collinear legality and rejects any target-cone secant having a
connector interior as an endpoint.  A separate exact census of the inherited
anchors must contain exactly the pinned 246 affine cone lines.

This is a finite certificate for two named cones on one L5 orbit.  It is not a
uniform far-secant lemma or an infinite construction.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import sys
import time
from collections import Counter
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import lattice_t_chronological_replay as producer  # noqa: E402
from design import potential_policy_chronological_rescue as rescue  # noqa: E402


DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L5-cone-guard-v1.json")
DEFAULT_AUDIT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L5-cone-guard-audit-checkpoint-v1.json"
)
DEFAULT_OUTPUT = Path(
    "/tmp/lattice-T-chronological-L5-cone-guard-audit-v1.json"
)
DEFAULT_SUMMARY = (
    ROOT / "design" / "lattice-T-L5-cone-guard-audit-summary.json"
)
GUARD_CHECKER = ROOT / "design" / "lattice_t_l6_cone_birth_guard.py"

EXPECTED_GUARD_CHECKER_SHA256 = (
    "0a3041a77fffd954bd7ff2478427d1c7f6ea6f6951b9f8465c0a0966b6b3d376"
)
EXPECTED_PRODUCER_SHA256 = (
    "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
)
EXPECTED_RESCUE_SHA256 = (
    "2b1bde9e846211cd53f75b6300c540a99b92d25b706c174c137f32c9cbf19ebc"
)
EXPECTED_SOURCE_SHA256 = (
    "e22a0f71516e152f93f2d8f1c25a43fe79e6b7be384196845ebdb153bb2c0e01"
)
EXPECTED_SOURCE_BYTES = 6_525_395
EXPECTED_SOURCE_PAYLOAD_SHA256 = (
    "19c70eafa7b8c076764b711e8e8c77167d3f90c2e4509ce2432aab4cf04d946d"
)
EXPECTED_SOURCE_STATIC_SHA256 = (
    "4c696ebe6f9bc153843bb566e50faed05649aedef1db1d79a4986f59fcee3759"
)
EXPECTED_SOURCE_PREFIX_SHA256 = (
    "6d4f45fbf7f4d606fb36e8b1c37b77f6148ff0b3851580a98e34497259635680"
)
EXPECTED_SOURCE_SELECTION_SHA256 = (
    "dc39dcf34f5a15458ecd42641d39c481ac856f19921f82edbd980c70518b73a6"
)
EXPECTED_PROMOTED_LINE_STREAM_SHA256 = (
    "fde18771786475d9a79d19634cd0d0ef908b8cd92f734a1212d4f9049a485d81"
)
EXPECTED_POINT_SET_SHA256 = (
    "1827b9595de7a95747cc290a1fcdde64cbf4214293e1603c22a5ec7a364391a9"
)
EXPECTED_FINAL_YZ_SHA256 = (
    "899f963392893cf9035a63470eaa96a1401e04d9d55a97c7bceb3a9e6706f470"
)
EXPECTED_FINAL_DOUBLE_FIBRE_SHA256 = (
    "d697a3b3feee953fb8cc3794f7c8f7a8108c98c70bce2d29466e62f590f0fd8f"
)
EXPECTED_GAPS = 2_457
EXPECTED_ANCHORS = 2_458
EXPECTED_POINTS = 8_296
EXPECTED_MAX_FIRST_ORDINAL = 3_417
EXPECTED_PROMOTED_LINES = 246

SPECTRA = (
    ("11/3", 11, 3),
    ("348/275", 348, 275),
)
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 25
HARD_MAX_SECONDS = 600.0
HARD_MAX_WORK_ITEMS = 2_000
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())


class DeadlineReached(Exception):
    def __init__(self, pending=None):
        super().__init__(pending)
        self.pending = pending


def assert_checker_unchanged():
    if rescue.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ):
        raise RuntimeError("L5 cone-guard auditor changed during execution")


def verify_dependencies():
    observed = {
        "guard_checker": rescue.file_sha256(GUARD_CHECKER),
        "L5_producer": rescue.file_sha256(Path(producer.__file__).resolve()),
        "rescue_geometry": rescue.file_sha256(Path(rescue.__file__).resolve()),
    }
    expected = {
        "guard_checker": EXPECTED_GUARD_CHECKER_SHA256,
        "L5_producer": EXPECTED_PRODUCER_SHA256,
        "rescue_geometry": EXPECTED_RESCUE_SHA256,
    }
    if observed != expected:
        raise AssertionError("pinned audit dependency drift", expected, observed)
    return observed


def source_pins():
    return {
        "file_sha256": EXPECTED_SOURCE_SHA256,
        "bytes": EXPECTED_SOURCE_BYTES,
        "payload_sha256": EXPECTED_SOURCE_PAYLOAD_SHA256,
        "static_state_sha256": EXPECTED_SOURCE_STATIC_SHA256,
        "prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
    }


def verify_source(path):
    path = Path(path)
    if path.stat().st_size != EXPECTED_SOURCE_BYTES:
        raise AssertionError("guarded L5 source byte-size drift")
    observed = rescue.file_sha256(path)
    if observed != EXPECTED_SOURCE_SHA256:
        raise AssertionError("guarded L5 source file drift", observed)
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(source) or internal != (
        EXPECTED_SOURCE_PAYLOAD_SHA256
    ):
        raise AssertionError("guarded L5 source payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("guarded L5 source schema drift")
    if source.get("status") != "construction-complete-audit-pending":
        raise AssertionError("guarded L5 source is not audit-ready")
    if source.get("obstruction") is not None or source.get(
        "pending_scan"
    ) is not None:
        raise AssertionError("completed guarded source retains failure state")
    records = source.get("selection_records")
    if not isinstance(records, list) or len(records) != EXPECTED_GAPS or (
        source.get("next_construction_rank") != EXPECTED_GAPS
    ):
        raise AssertionError("guarded L5 source extent drift")
    static = source.get("static", {})
    static_copy = copy.deepcopy(static)
    static_hash = static_copy.pop("static_state_sha256", None)
    if static_hash != rescue.stable_hash(static_copy) or static_hash != (
        EXPECTED_SOURCE_STATIC_SHA256
    ):
        raise AssertionError("guarded L5 source static-state drift")
    required_static = {
        "checker_sha256": EXPECTED_GUARD_CHECKER_SHA256,
        "L5_producer_sha256": EXPECTED_PRODUCER_SHA256,
        "guarded_level": 5,
        "grandfathered_points": EXPECTED_ANCHORS,
        "selection_order": "compact-cache ordinal order",
        "stitch_order": "D2--4 fragile-first, then ordered gap index",
    }
    for key, expected in required_static.items():
        if static.get(key) != expected:
            raise AssertionError("guarded L5 static policy drift", key)
    promoted = static.get("promoted_seed_lines", {})
    if promoted.get("count") != EXPECTED_PROMOTED_LINES or promoted.get(
        "line_stream_sha256"
    ) != EXPECTED_PROMOTED_LINE_STREAM_SHA256:
        raise AssertionError("guarded L5 promoted-line commitment drift")
    prefix = source.get("prefix", {})
    pinned_prefix = {
        "prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
        "placed_point_count": EXPECTED_POINTS,
        "point_set_sha256": EXPECTED_POINT_SET_SHA256,
        "yz_occupancy_stream_sha256": EXPECTED_FINAL_YZ_SHA256,
        "doubled_fibre_stream_sha256": EXPECTED_FINAL_DOUBLE_FIBRE_SHA256,
    }
    for key, expected in pinned_prefix.items():
        if prefix.get(key) != expected:
            raise AssertionError("guarded L5 final-prefix drift", key)
    if rescue.stable_hash(records) != EXPECTED_SOURCE_SELECTION_SHA256:
        raise AssertionError("guarded L5 selection record stream drift")
    maximum = max(
        record["first_survivor_ordinal_1_based"] for record in records
    )
    if maximum != EXPECTED_MAX_FIRST_ORDINAL:
        raise AssertionError("guarded L5 maximum first ordinal drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def artifact_args(args):
    return argparse.Namespace(
        metadata=args.metadata,
        cache=args.cache,
        lattice_result=args.lattice_result,
        lattice_bitsets=args.lattice_bitsets,
    )


def open_context(args):
    dependencies = verify_dependencies()
    source, source_snapshot = verify_source(args.source)
    artifact_sha256 = producer.verify_inputs(artifact_args(args))
    _metadata, blocks = rescue.load_metadata(args.metadata)
    parent_word, anchors, schedule = rescue.load_l5_state()
    if len(parent_word) != EXPECTED_GAPS or len(anchors) != EXPECTED_ANCHORS:
        raise AssertionError("pinned inherited L4/L5 extent drift")
    _lattice_result, sidecar = producer.load_lattice_result(
        args.lattice_result
    )
    cache_handle = Path(args.cache).open("rb")
    bitset_handle = Path(args.lattice_bitsets).open("rb")
    cache = bitset = None
    try:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        bitset = mmap.mmap(
            bitset_handle.fileno(), 0, access=mmap.ACCESS_READ
        )
        if cache[:len(rescue.CACHE_MAGIC)] != rescue.CACHE_MAGIC:
            raise AssertionError("compact connector cache magic drift")
        action_records = producer.parse_bitsets(bitset, sidecar, blocks)
    except BaseException:
        if bitset is not None:
            bitset.close()
        if cache is not None:
            cache.close()
        bitset_handle.close()
        cache_handle.close()
        raise
    context = {
        "source": source,
        "source_snapshot": source_snapshot,
        "dependencies": dependencies,
        "artifact_sha256": artifact_sha256,
        "blocks": blocks,
        "parent_word": parent_word,
        "anchors": anchors,
        "schedule": schedule,
        "cache_handle": cache_handle,
        "bitset_handle": bitset_handle,
        "cache": cache,
        "bitset": bitset,
        "action_records": action_records,
    }
    promoted = promoted_seed_cone_lines(anchors)
    if len(promoted) != EXPECTED_PROMOTED_LINES or rescue.stable_hash(
        promoted
    ) != EXPECTED_PROMOTED_LINE_STREAM_SHA256:
        close_context(context)
        raise AssertionError("independent promoted seed-line census drift")
    if list(promoted) != source["static"]["promoted_seed_lines"]["lines"]:
        close_context(context)
        raise AssertionError("constructor/independent promoted-line list drift")
    context["promoted_seed_lines"] = promoted
    return context


def close_context(context):
    context["bitset"].close()
    context["cache"].close()
    context["bitset_handle"].close()
    context["cache_handle"].close()


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def primitive_direction(vector):
    divisor = gcd(gcd(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    if divisor == 0:
        raise AssertionError("zero displacement in exact direction audit")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def cone_matches(direction):
    r, y, z = direction
    quadratic = 3 * y * y - y * z + 3 * z * z
    return tuple(
        label for label, numerator, denominator in SPECTRA
        if denominator * quadratic - numerator * r * r == 0
    )


def promoted_seed_cone_lines(points):
    records = []
    line_keys = set()
    for later_id, later in enumerate(points):
        for earlier_id in range(later_id):
            earlier = points[earlier_id]
            direction = subtract(later, earlier)
            matches = cone_matches(direction)
            if not matches:
                continue
            primitive = primitive_direction(direction)
            moment = cross(earlier, primitive)
            key = (primitive, moment)
            if key in line_keys:
                raise AssertionError(
                    "inherited anchors contain three points on one cone line"
                )
            line_keys.add(key)
            records.append({
                "earlier_point_id": earlier_id,
                "later_point_id": later_id,
                "matched_spectra": list(matches),
                "canonical_primitive_direction": list(primitive),
                "exact_Pluecker_moment": list(moment),
            })
    return tuple(records)


def first_new_cone_birth(interiors, store):
    base_id = len(store.pts)
    for later_slot, point in enumerate(interiors):
        px, py, pz = point
        for earlier_id in range(len(store.pts)):
            direction = (
                px - store.xs[earlier_id],
                py - store.ys[earlier_id],
                pz - store.zs[earlier_id],
            )
            matches = cone_matches(direction)
            if matches:
                return {
                    "classification": "old-new",
                    "later_slot": later_slot,
                    "later_point_id": base_id + later_slot,
                    "earlier_point_id": earlier_id,
                    "matched_spectra": list(matches),
                    "primitive_direction": list(
                        primitive_direction(direction)
                    ),
                }
        for earlier_slot in range(later_slot):
            direction = subtract(point, interiors[earlier_slot])
            matches = cone_matches(direction)
            if matches:
                return {
                    "classification": "same-word-new-new",
                    "later_slot": later_slot,
                    "later_point_id": base_id + later_slot,
                    "earlier_point_id": base_id + earlier_slot,
                    "matched_spectra": list(matches),
                    "primitive_direction": list(
                        primitive_direction(direction)
                    ),
                }
    return None


def cache_word_at_offset(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("stored cache offset outside connector block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("stored cache record boundary drift")
    return tuple(cache[offset + 1:end])


def action_accepts(bitset, record, channel, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("action ordinal outside connector domain")
    index = ordinal - 1
    selected = record[channel]
    return bool(
        bitset[selected["offset"] + (index >> 3)] & (1 << (index & 7))
    )


def intrinsic_projection_clean(start, target, interiors):
    fibres = [point[1:] for point in interiors]
    return (
        len(fibres) == len(set(fibres))
        and not {start[1:], target[1:]}.intersection(fibres)
    )


def global_projection_clean(interiors, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts or fibre in local:
            return False
        local.add(fibre)
    return True


def apply_selected(interiors, store, yz_counts):
    for point in interiors:
        fibre = point[1:]
        if yz_counts[fibre]:
            raise AssertionError("audited winner reuses a global yz fibre")
        yz_counts[fibre] += 1
    store.add_many(interiors)


def prefix_commitment(store, yz_counts, records, rank):
    fields = {
        "next_construction_rank": rank,
        "selection_record_stream_sha256": rescue.stable_hash(records[:rank]),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": (
            rescue.point_stream_sha256(store.pts)
        ),
        "point_set_sha256": rescue.stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": rescue.stable_hash(
            sorted(yz_counts.items())
        ),
        "doubled_fibre_stream_sha256": rescue.stable_hash(sorted(
            fibre for fibre, count in yz_counts.items() if count == 2
        )),
    }
    fields["prefix_state_sha256"] = rescue.stable_hash(fields)
    return fields


def audit_static(context):
    fields = {
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "pinned_dependencies": context["dependencies"],
        "source_checkpoint": context["source_snapshot"],
        "source_pins": source_pins(),
        "artifact_sha256": context["artifact_sha256"],
        "policy": {
            "action_channel": "zero",
            "projection_policy": "global-empty",
            "require_digit_simple": False,
            "cone_spectra": [label for label, _a, _b in SPECTRA],
            "selection_order": "compact-cache ordinal order",
            "stitch_order": "D2--4 fragile-first, then ordered gap index",
        },
        "gaps": EXPECTED_GAPS,
        "anchors": EXPECTED_ANCHORS,
        "points": EXPECTED_POINTS,
        "promoted_seed_cone_lines": {
            "count": len(context["promoted_seed_lines"]),
            "line_stream_sha256": rescue.stable_hash(
                context["promoted_seed_lines"]
            ),
        },
    }
    fields["static_state_sha256"] = rescue.stable_hash(fields)
    return fields


def seal(value):
    result = copy.deepcopy(value)
    result.pop("checkpoint_payload_sha256", None)
    result["checkpoint_payload_sha256"] = rescue.stable_hash(result)
    return result


def save_checkpoint(path, checkpoint):
    assert_checker_unchanged()
    sealed = seal(checkpoint)
    rescue.atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def initial_checkpoint(context, static):
    store = rescue.Store(context["anchors"])
    yz_counts = Counter(point[1:] for point in context["anchors"])
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "firstness_audited_through_rank": 0,
        "pending_firstness_scan": None,
        "audit_records": [],
        "audit_record_stream_sha256": rescue.stable_hash([]),
        "audited_prefix": prefix_commitment(
            store, yz_counts, context["source"]["selection_records"], 0
        ),
        "ordered_verifier": {
            "next_point": 0,
            "total_points": None,
            "pair_checks": 0,
            "target_cone_pair_matches": 0,
            "ordered_point_stream_sha256": None,
            "ordered_point_set_sha256": None,
            "final_yz_occupancy_sha256": None,
            "final_double_fibre_sha256": None,
            "final_no_new_yz_coincidence": False,
            "complete": False,
        },
        "terminal_output": None,
        "terminal_summary": None,
        "last_run": None,
    }


def load_checkpoint(path, context, static):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(context, static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(checkpoint):
        raise AssertionError("L5 cone-guard audit checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != static:
        raise AssertionError("L5 cone-guard audit schema/static drift")
    cursor = checkpoint["firstness_audited_through_rank"]
    if not 0 <= cursor <= EXPECTED_GAPS or len(
        checkpoint["audit_records"]
    ) != cursor:
        raise AssertionError("L5 cone-guard audit firstness cursor drift")
    if checkpoint["audit_record_stream_sha256"] != rescue.stable_hash(
        checkpoint["audit_records"]
    ):
        raise AssertionError("L5 cone-guard audit record stream drift")
    pending = checkpoint["pending_firstness_scan"]
    if pending is not None and pending["construction_rank"] != cursor:
        raise AssertionError("L5 cone-guard audit pending/rank drift")
    verifier = checkpoint["ordered_verifier"]
    if verifier["next_point"] and cursor != EXPECTED_GAPS:
        raise AssertionError("ordered verification preceded firstness")
    total = verifier["total_points"]
    if total is not None and not 0 <= verifier["next_point"] <= total:
        raise AssertionError("ordered verifier cursor drift")
    expected_pairs = verifier["next_point"] * (
        verifier["next_point"] - 1
    ) // 2
    if verifier["pair_checks"] != expected_pairs:
        raise AssertionError("ordered verifier pair-count drift")
    if verifier["complete"] and (
        total is None or verifier["next_point"] != total
    ):
        raise AssertionError("ordered verifier completion drift")
    return checkpoint


def reconstruct_audited_prefix(context, checkpoint, deadline):
    records = context["source"]["selection_records"]
    anchors = context["anchors"]
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    cursor = checkpoint["firstness_audited_through_rank"]
    for rank in range(cursor):
        if rank % CHECKPOINT_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing cone-guard-audited L5 prefix"
        ):
            raise DeadlineReached
        source_record = records[rank]
        audit_record = checkpoint["audit_records"][rank]
        gap = context["schedule"][rank]
        step = context["parent_word"][gap]
        if (
            source_record["construction_rank"], source_record["gap"],
            source_record["step"],
        ) != (rank, gap, step) or (
            audit_record["construction_rank"], audit_record["gap"],
            audit_record["step"],
        ) != (rank, gap, step):
            raise AssertionError("audited L5 schedule identity drift", rank)
        expected_audit = {
            "selected_ordinal_1_based": source_record[
                "first_survivor_ordinal_1_based"
            ],
            "cache_record_offset": source_record["cache_record_offset"],
            "selected_word_sha256": hashlib.sha256(
                bytes(source_record["selected_word"])
            ).hexdigest(),
            "earlier_guarded_survivors": 0,
            "selected_fast_reference_agreement": True,
            "selected_reference_legal": True,
            "selected_cone_birth_free": True,
        }
        for key, expected in expected_audit.items():
            if audit_record.get(key) != expected:
                raise AssertionError("stored L5 cone audit-record drift", rank, key)
        word = cache_word_at_offset(
            context["cache"], context["blocks"][step],
            source_record["cache_record_offset"],
        )
        if list(word) != source_record["selected_word"]:
            raise AssertionError("audited selected cache bytes drift", rank)
        ordinal = source_record["first_survivor_ordinal_1_based"]
        if not action_accepts(
            context["bitset"], context["action_records"][step], "zero",
            ordinal,
        ):
            raise AssertionError("audited selected word lost zero-T", rank)
        start, target = anchors[gap], anchors[gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        if rescue.endpoint(start, word) != target:
            raise AssertionError("audited selected endpoint drift", rank)
        if not intrinsic_projection_clean(
            start, target, interiors
        ) or not global_projection_clean(interiors, yz_counts):
            raise AssertionError("audited selected projection drift", rank)
        apply_selected(interiors, store, yz_counts)
    observed = prefix_commitment(store, yz_counts, records, cursor)
    if observed != checkpoint["audited_prefix"]:
        raise AssertionError("audited L5 prefix commitment drift")
    if cursor == EXPECTED_GAPS and observed != context["source"]["prefix"]:
        raise AssertionError("completed independent prefix/source drift")
    return store, yz_counts


def empty_pending(rank, gap, step, block, selected_ordinal, action_count):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "selected_ordinal_1_based": selected_ordinal,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "domain_words_scanned": 0,
        "action_incompatible_skipped": 0,
        "action_compatible_seen": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "cone_birth_rejected": 0,
        "static_zero_T_words": action_count,
    }


def validate_pending(scan, rank, gap, step, block, selected_ordinal):
    if (
        scan["construction_rank"], scan["gap"], scan["step"],
        scan["selected_ordinal_1_based"],
    ) != (rank, gap, step, selected_ordinal):
        raise AssertionError("pending cone-audit firstness identity drift")
    ordinal = scan["next_ordinal_1_based"]
    if not 1 <= ordinal <= selected_ordinal or scan[
        "domain_words_scanned"
    ] != ordinal - 1:
        raise AssertionError("pending cone-audit firstness ordinal drift")
    if not block["start"] <= scan["next_cache_cursor"] < block["end"]:
        raise AssertionError("pending cone-audit cache cursor drift")
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scan["domain_words_scanned"]:
        raise AssertionError("pending cone-audit action partition drift")
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != scan["action_compatible_seen"]:
        raise AssertionError("pending cone-audit projection partition drift")
    if scan["exact_legality_rejected"] + scan[
        "cone_birth_rejected"
    ] != scan["projection_clean_exact_tested"]:
        raise AssertionError("pending cone-audit exact/cone partition has survivor")


def verify_source_record(
    context, source_record, rank, gap, step, ordinal, offset, word,
    interiors, counters,
):
    action_record = context["action_records"][step]
    expected_survivor = {
        "ordinal_1_based": ordinal,
        "cache_record_offset": offset,
        "word": list(word),
        "intrinsic_projection_clean": True,
        "global_projection_clean": True,
        "zero_T_accepted": True,
        "ordered_T_accepted": action_accepts(
            context["bitset"], action_record, "ordered", ordinal
        ),
        "cone_birth_free": True,
    }
    expected = {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "domain_words": context["blocks"][step]["words"],
        "static_action_words": action_record["zero"]["set_bits"],
        "first_survivor_ordinal_1_based": ordinal,
        "cache_record_offset": offset,
        "selected_word": list(word),
        "cone_birth_free": True,
        "certified_survivor_count": 1,
        "certified_survivors": [expected_survivor],
        "survivor_census_exhaustive": False,
        "scan_counters_through_certificate": counters,
    }
    for key, value in expected.items():
        if source_record.get(key) != value:
            raise AssertionError("guarded source selected-record drift", rank, key)
    return expected_survivor


def audit_one_stitch(context, rank, store, yz_counts, pending, deadline):
    source_record = context["source"]["selection_records"][rank]
    gap = context["schedule"][rank]
    step = context["parent_word"][gap]
    if (
        source_record["construction_rank"], source_record["gap"],
        source_record["step"],
    ) != (rank, gap, step):
        raise AssertionError("guarded source schedule drift", rank)
    block = context["blocks"][step]
    action_record = context["action_records"][step]
    selected_ordinal = source_record["first_survivor_ordinal_1_based"]
    if not 1 <= selected_ordinal <= block["words"]:
        raise AssertionError("guarded selected ordinal outside domain", rank)
    scan = copy.deepcopy(pending) if pending is not None else empty_pending(
        rank, gap, step, block, selected_ordinal,
        action_record["zero"]["set_bits"],
    )
    validate_pending(scan, rank, gap, step, block, selected_ordinal)
    if scan["static_zero_T_words"] != action_record["zero"]["set_bits"]:
        raise AssertionError("pending zero-T population drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    reference_memo = {}
    start, target = context["anchors"][gap], context["anchors"][gap + 1]
    while ordinal <= selected_ordinal:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "independent guarded-L5 firstness scan"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("independent cache boundary drift", rank, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1
        if not action_accepts(
            context["bitset"], action_record, "zero", ordinal
        ):
            scan["action_incompatible_skipped"] += 1
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        interiors = tuple(rescue.word_interiors(start, word))
        if not intrinsic_projection_clean(
            start, target, interiors
        ) or not global_projection_clean(interiors, yz_counts):
            scan["projection_rejected"] += 1
            ordinal += 1
            continue
        scan["projection_clean_exact_tested"] += 1
        fast_legal = rescue.word_legal_fast(
            start, word, store, fast_memo, rescue.MENU
        )
        reference_legal = rescue.word_legal(
            start, word, store.pts, store.pset, reference_memo
        )
        if fast_legal != reference_legal:
            raise AssertionError(
                "guarded audit fast/reference disagreement", rank, ordinal
            )
        if not reference_legal:
            scan["exact_legality_rejected"] += 1
            ordinal += 1
            continue
        if rescue.endpoint(start, word) != target:
            raise AssertionError("eligible guarded word endpoint drift", rank, ordinal)
        cone_witness = first_new_cone_birth(interiors, store)
        if cone_witness is not None:
            scan["cone_birth_rejected"] += 1
            ordinal += 1
            continue
        if ordinal < selected_ordinal:
            raise AssertionError(
                "earlier guarded-policy survivor found", rank, ordinal,
                selected_ordinal, list(word),
            )
        if list(word) != source_record["selected_word"] or offset != (
            source_record["cache_record_offset"]
        ):
            raise AssertionError("guarded winner/cache-order drift", rank)
        counters = {
            "domain_words_scanned": scan["domain_words_scanned"],
            "action_incompatible_skipped": scan[
                "action_incompatible_skipped"
            ],
            "action_compatible_seen": scan["action_compatible_seen"],
            "digit_rejected": 0,
            "projection_rejected": scan["projection_rejected"],
            "projection_clean_exact_tested": scan[
                "projection_clean_exact_tested"
            ],
            "exact_legality_rejected": scan["exact_legality_rejected"],
            "cone_birth_rejected": scan["cone_birth_rejected"],
        }
        survivor = verify_source_record(
            context, source_record, rank, gap, step, ordinal, offset, word,
            interiors, counters,
        )
        audit_record = {
            "construction_rank": rank,
            "gap": gap,
            "step": step,
            "selected_ordinal_1_based": ordinal,
            "cache_record_offset": offset,
            "selected_word_sha256": hashlib.sha256(bytes(word)).hexdigest(),
            "ordinals_rescanned": ordinal,
            "zero_T_compatible_seen": scan["action_compatible_seen"],
            "projection_clean_exact_tested": scan[
                "projection_clean_exact_tested"
            ],
            "cone_birth_rejections": scan["cone_birth_rejected"],
            "earlier_guarded_survivors": 0,
            "selected_fast_reference_agreement": True,
            "selected_reference_legal": True,
            "selected_cone_birth_free": True,
            "selected_static_channels": survivor,
        }
        return audit_record, interiors
    raise AssertionError("stored winner is not a guarded-policy survivor", rank)


def ordered_chain(context):
    records = context["source"]["selection_records"]
    selected = {record["gap"]: tuple(record["selected_word"])
                for record in records}
    if set(selected) != set(range(EXPECTED_GAPS)):
        raise AssertionError("guarded source does not select every gap")
    anchors = context["anchors"]
    chain = [anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_GAPS):
        word = selected[gap]
        chain.extend(rescue.word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != EXPECTED_POINTS or len(chain) != len(set(chain)):
        raise AssertionError("realized guarded L5 chain extent/repetition drift")
    if rescue.stable_hash(sorted(chain)) != EXPECTED_POINT_SET_SHA256:
        raise AssertionError("realized guarded L5 point set drift")
    return tuple(chain), tuple(flat_word), selected


def verify_final_yz(anchors, chain):
    initial = Counter(point[1:] for point in anchors)
    final = Counter(point[1:] for point in chain)
    for fibre, count in final.items():
        if count != initial.get(fibre, 1):
            raise AssertionError("terminal guarded L5 no-new-yz failure", fibre)
    if rescue.stable_hash(sorted(final.items())) != EXPECTED_FINAL_YZ_SHA256:
        raise AssertionError("terminal guarded L5 yz commitment drift")
    double_fibres = sorted(
        fibre for fibre, count in final.items() if count == 2
    )
    if rescue.stable_hash(double_fibres) != EXPECTED_FINAL_DOUBLE_FIBRE_SHA256:
        raise AssertionError("terminal guarded L5 doubled-yz drift")
    return final, double_fibres


def verify_ordered_point(chain, cursor, anchor_ids):
    point = chain[cursor]
    owner = {}
    cone_pairs = 0
    point_is_anchor = point in anchor_ids
    for index in range(cursor):
        prior = chain[index]
        displacement = subtract(prior, point)
        direction = primitive_direction(displacement)
        earlier = owner.get(direction)
        if earlier is not None:
            raise AssertionError(
                "ordered guarded L5 chain contains a collinear triple",
                earlier, index, cursor,
                [list(chain[earlier]), list(prior), list(point)],
            )
        owner[direction] = index
        matches = cone_matches(displacement)
        if matches:
            if not point_is_anchor or prior not in anchor_ids:
                raise AssertionError(
                    "terminal new target-cone secant",
                    index, cursor, list(prior), list(point), list(matches),
                )
            cone_pairs += 1
    return cursor, cone_pairs


def terminal_payload(context, checkpoint, chain, flat_word, selected, policy):
    records = context["source"]["selection_records"]
    ordinals = [
        record["first_survivor_ordinal_1_based"] for record in records
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": "exact independent guarded-L5 finite certificate",
        "checker": {
            "path": "design/lattice_t_l5_cone_guard_audit.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_audit": True,
        },
        "resource_policy": policy,
        "source_checkpoint": context["source_snapshot"],
        "source_pins": source_pins(),
        "pinned_dependencies": context["dependencies"],
        "static_state_sha256": checkpoint["static"][
            "static_state_sha256"
        ],
        "result": {
            "construction_completed": True,
            "gaps": EXPECTED_GAPS,
            "anchors": EXPECTED_ANCHORS,
            "points": len(chain),
            "steps": len(flat_word),
            "first_survivor_audit_completed": True,
            "selected_reference_legality_verified_at_every_stitch": True,
            "fast_reference_agreement_verified_for_every_exact_test": True,
            "global_empty_yz_verified_at_every_stitch": True,
            "final_no_new_yz_coincidence": True,
            "independent_ordered_no_three_collinear_verified": True,
            "promoted_base_cone_lines": EXPECTED_PROMOTED_LINES,
            "new_target_cone_secants": 0,
            "target_cone_pair_matches_in_terminal_pair_scan": (
                checkpoint["ordered_verifier"]["target_cone_pair_matches"]
            ),
            "ordered_pair_checks": checkpoint["ordered_verifier"][
                "pair_checks"
            ],
            "maximum_first_survivor_ordinal_1_based": max(ordinals),
            "sum_first_survivor_ordinals": sum(ordinals),
            "independently_recounted_cone_rejections": sum(
                record["cone_birth_rejections"]
                for record in checkpoint["audit_records"]
            ),
        },
        "commitments": {
            "source_prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
            "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
            "audit_record_stream_sha256": checkpoint[
                "audit_record_stream_sha256"
            ],
            "promoted_seed_line_stream_sha256": (
                EXPECTED_PROMOTED_LINE_STREAM_SHA256
            ),
            "alternate_words_by_gap_sha256": rescue.stable_hash(
                [[gap, list(selected[gap])] for gap in range(EXPECTED_GAPS)]
            ),
            "alternate_flat_step_word_sha256": hashlib.sha256(
                bytes(flat_word)
            ).hexdigest(),
            "alternate_ordered_point_stream_sha256": (
                rescue.point_stream_sha256(chain)
            ),
            "final_point_set_sha256": EXPECTED_POINT_SET_SHA256,
            "final_yz_occupancy_sha256": EXPECTED_FINAL_YZ_SHA256,
            "final_double_fibre_sha256": EXPECTED_FINAL_DOUBLE_FIBRE_SHA256,
        },
        "proved": [
            "the pinned two-cone-guarded L5 policy has an exact first survivor at every chronological stitch",
            "every selected word is zero-T, globally yz-fresh, reference-legal, and creates no new secant in either named cone",
            "the inherited anchor skeleton contains exactly 246 affine lines in the two named projective cones",
            "the final realized walk has no collinear triple and no target-cone secant with a connector endpoint",
        ],
        "not_proved": [
            "control of any projective direction outside J=11/3 and J=348/275",
            "positive guarded availability for every reachable state or at levels beyond this pinned L5 orbit",
            "a contracting far-secant tail bound or an unconditional infinite construction",
        ],
    }
    payload["terminal_payload_sha256"] = rescue.stable_hash(payload)
    return payload


def audit_chunk(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_context(args)
    try:
        static = audit_static(context)
        checkpoint = load_checkpoint(args.audit_checkpoint, context, static)
        if checkpoint["status"] == "complete":
            return checkpoint, {
                "work_items": 0,
                "stop_reason": "terminal-audit-already-complete",
            }
        try:
            store, yz_counts = reconstruct_audited_prefix(
                context, checkpoint, deadline
            )
        except DeadlineReached:
            return checkpoint, {
                "work_items": 0,
                "stop_reason": "time-limit-during-prefix-reconstruction",
            }
        work = 0
        stop_reason = "work-limit"
        while checkpoint["firstness_audited_through_rank"] < EXPECTED_GAPS:
            if work >= args.max_work_items:
                break
            if rescue.enforce_runtime(
                deadline, "between guarded-L5 audit stitches"
            ):
                stop_reason = "time-limit"
                break
            rank = checkpoint["firstness_audited_through_rank"]
            try:
                audit_record, interiors = audit_one_stitch(
                    context, rank, store, yz_counts,
                    checkpoint["pending_firstness_scan"], deadline,
                )
            except DeadlineReached as reached:
                checkpoint["pending_firstness_scan"] = reached.pending
                stop_reason = "time-limit-during-firstness-domain-scan"
                break
            checkpoint["audit_records"].append(audit_record)
            apply_selected(interiors, store, yz_counts)
            checkpoint["firstness_audited_through_rank"] += 1
            checkpoint["pending_firstness_scan"] = None
            checkpoint["audit_record_stream_sha256"] = rescue.stable_hash(
                checkpoint["audit_records"]
            )
            cursor = checkpoint["firstness_audited_through_rank"]
            checkpoint["audited_prefix"] = prefix_commitment(
                store, yz_counts, context["source"]["selection_records"],
                cursor,
            )
            work += 1
            if work % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.audit_checkpoint, checkpoint)
        if checkpoint["firstness_audited_through_rank"] == EXPECTED_GAPS:
            if checkpoint["audited_prefix"] != context["source"]["prefix"]:
                raise AssertionError("completed guarded audit prefix/source drift")
            chain, flat_word, selected = ordered_chain(context)
            final_yz, double_fibres = verify_final_yz(
                context["anchors"], chain
            )
            verifier = checkpoint["ordered_verifier"]
            expected = {
                "total_points": len(chain),
                "ordered_point_stream_sha256": rescue.point_stream_sha256(chain),
                "ordered_point_set_sha256": rescue.stable_hash(sorted(chain)),
                "final_yz_occupancy_sha256": rescue.stable_hash(
                    sorted(final_yz.items())
                ),
                "final_double_fibre_sha256": rescue.stable_hash(double_fibres),
            }
            for key, value in expected.items():
                if verifier[key] is not None and verifier[key] != value:
                    raise AssertionError("ordered verifier commitment drift", key)
                verifier[key] = value
            verifier["final_no_new_yz_coincidence"] = True
            anchor_ids = {point: index for index, point in enumerate(
                context["anchors"]
            )}
            while verifier["next_point"] < len(chain):
                if work >= args.max_work_items:
                    stop_reason = "ordered-verifier-work-limit"
                    break
                if rescue.enforce_runtime(
                    deadline, "ordered guarded-L5 terminal verifier"
                ):
                    stop_reason = "ordered-verifier-time-limit"
                    break
                pair_checks, cone_pairs = verify_ordered_point(
                    chain, verifier["next_point"], anchor_ids
                )
                verifier["pair_checks"] += pair_checks
                verifier["target_cone_pair_matches"] += cone_pairs
                verifier["next_point"] += 1
                work += 1
                if work % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(args.audit_checkpoint, checkpoint)
                    verifier = checkpoint["ordered_verifier"]
            if verifier["next_point"] == len(chain):
                expected_pairs = len(chain) * (len(chain) - 1) // 2
                if verifier["pair_checks"] != expected_pairs:
                    raise AssertionError("terminal exhaustive pair extent drift")
                if verifier["target_cone_pair_matches"] != (
                    EXPECTED_PROMOTED_LINES
                ):
                    raise AssertionError("terminal target-cone pair census drift")
                verifier["complete"] = True
                checkpoint["status"] = "complete"
                stop_reason = "terminal-audit-complete"
                terminal = terminal_payload(
                    context, checkpoint, chain, flat_word, selected, policy
                )
                rescue.atomic_json_dump(terminal, args.output)
                rescue.atomic_json_dump(terminal, args.summary)
                checkpoint["terminal_output"] = {
                    "path": str(Path(args.output).resolve()),
                    "sha256": rescue.file_sha256(args.output),
                    "bytes": Path(args.output).stat().st_size,
                    "payload_sha256": terminal["terminal_payload_sha256"],
                }
                checkpoint["terminal_summary"] = {
                    "path": str(Path(args.summary).resolve()),
                    "sha256": rescue.file_sha256(args.summary),
                    "bytes": Path(args.summary).stat().st_size,
                    "payload_sha256": terminal["terminal_payload_sha256"],
                }
        checkpoint["last_run"] = {
            "work_items": work,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "maximum_resident_bytes": rescue.maximum_resident_bytes(),
            "resource_policy": policy,
        }
        save_checkpoint(args.audit_checkpoint, checkpoint)
        return checkpoint, {
            "work_items": work,
            "stop_reason": stop_reason,
            "firstness_audited_through_rank": checkpoint[
                "firstness_audited_through_rank"
            ],
            "ordered_verifier_next_point": checkpoint["ordered_verifier"][
                "next_point"
            ],
            "ordered_verifier_total_points": checkpoint["ordered_verifier"][
                "total_points"
            ],
            "ordered_pair_checks": checkpoint["ordered_verifier"][
                "pair_checks"
            ],
        }
    finally:
        close_context(context)


def self_check():
    bits = bytes((0b00000101, 0b00000010))
    record = {
        "words": 10,
        "zero": {"offset": 0, "set_bits": 3},
        "ordered": {"offset": 0, "set_bits": 3},
    }
    observed = [
        action_accepts(bits, record, "zero", ordinal)
        for ordinal in range(1, 11)
    ]
    if observed != [
        True, False, True, False, False,
        False, False, False, False, True,
    ]:
        raise AssertionError("cone-guard audit ordinal-bit convention drift")
    if cone_matches((3, -3, 1)) != ("11/3",):
        raise AssertionError("11/3 synthetic cone witness drift")
    if cone_matches((55, 34, 18)) != ("348/275",):
        raise AssertionError("348/275 synthetic cone witness drift")
    if cone_matches((1, 0, 0)):
        raise AssertionError("non-cone direction misclassified")
    promoted = promoted_seed_cone_lines(((0, 0, 0), (3, -3, 1)))
    if len(promoted) != 1 or promoted[0]["matched_spectra"] != ["11/3"]:
        raise AssertionError("synthetic promoted-line census drift")
    store = rescue.Store(((0, 0, 0),))
    if first_new_cone_birth(((3, -3, 1),), store)[
        "classification"
    ] != "old-new":
        raise AssertionError("synthetic old-new cone birth missed")
    same = first_new_cone_birth(((10, 0, 0), (13, -3, 1)), store)
    if same is None or same["classification"] != "same-word-new-new":
        raise AssertionError("synthetic same-word cone birth missed")
    collinear = ((0, 0, 0), (1, 1, 1), (2, 2, 2))
    try:
        verify_ordered_point(collinear, 2, {(0, 0, 0): 0})
    except AssertionError as error:
        if error.args[0] != (
            "ordered guarded L5 chain contains a collinear triple"
        ):
            raise
    else:
        raise AssertionError("synthetic collinear triple was not rejected")
    try:
        verify_ordered_point(
            ((0, 0, 0), (3, -3, 1)), 1, {(0, 0, 0): 0}
        )
    except AssertionError as error:
        if error.args[0] != "terminal new target-cone secant":
            raise
    else:
        raise AssertionError("synthetic new target-cone secant was accepted")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_pins": source_pins(),
        "large_artifacts_opened": False,
        "independent_ordinal_bits_tested": 10,
        "both_target_cones_tested": True,
        "old_new_and_same_word_births_tested": True,
        "synthetic_collinear_rejection": True,
        "synthetic_new_cone_rejection": True,
        "firstness_resume_granularity": "cache ordinal within one stitch",
    }


def estimate():
    return {
        "status": "prepared fail-closed guarded-L5 terminal audit",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_pins": source_pins(),
        "source_checkpoint_is_read_only": True,
        "audit_checkpoint_is_separate": True,
        "expected_stitches": EXPECTED_GAPS,
        "expected_points": EXPECTED_POINTS,
        "expected_promoted_seed_cone_lines": EXPECTED_PROMOTED_LINES,
        "firstness_policy": (
            "zero-T AND global empty-yz AND exact fast/reference legality "
            "AND no new secant in J=11/3 or J=348/275"
        ),
        "terminal_verifier": (
            "natural ordered chain; exhaustive prior-direction and target-cone scan"
        ),
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_seconds_per_chunk": HARD_MAX_SECONDS,
        "maximum_work_items_per_chunk": HARD_MAX_WORK_ITEMS,
        "large_artifacts_opened": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "audit"))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument(
        "--audit-checkpoint", default=str(DEFAULT_AUDIT_CHECKPOINT)
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(producer.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(producer.DEFAULT_LATTICE_BITSETS)
    )
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-work-items", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,600]")
    if not 1 <= args.max_work_items <= HARD_MAX_WORK_ITEMS:
        raise ValueError("max-work-items outside [1,2000]")
    policy = rescue.resource_policy(enforce=args.mode == "audit")
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    else:
        checkpoint, observation = audit_chunk(args, policy)
        result = {
            "status": checkpoint["status"],
            "audit_checkpoint": str(Path(args.audit_checkpoint).resolve()),
            "audit_checkpoint_sha256": rescue.file_sha256(
                args.audit_checkpoint
            ),
            "terminal_output": checkpoint["terminal_output"],
            "terminal_summary": checkpoint["terminal_summary"],
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
