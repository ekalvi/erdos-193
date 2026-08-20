#!/usr/bin/env python3
"""Resumable chronological L5 consumer for lattice-T action bitsets.

The primary prepared policy intersects, in cache order:

* the exact zero-envelope (zero-T) accepted-ordinal channel;
* the evolving global empty-(y,z) invariant from the no-new-x constructor;
* exact global connector legality against every currently placed point.

Global empty-(y,z) implies intrinsic cleanliness: pairwise-distinct proper
interior fibres avoiding the two endpoint fibres.  For diagnosis,
``--projection-policy intrinsic`` applies only that weaker static predicate.
Likewise ``--action-channel ordered`` consumes the larger common-order
channel, and ``--require-digit-simple`` adds the static 3-adic digit predicate.

The first selected word and up to ``--survivor-certificate-target`` exact
survivors are retained at every stitch.  A sealed pending ordinal/cache cursor
makes both firstness and the survivor lower bound resumable across chunks.
The terminal first-survivor replay is intentionally a later audit phase.

The lattice-action result, sidecar, merger, and repository summary are pinned
to the frozen exact merge.  Run mode verifies every pin before opening the
cache.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import os
import pickle
import struct
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import potential_policy_chronological_rescue as rescue  # noqa: E402
from design.fixed_policy_chronological_replay import (  # noqa: E402
    first_projection_conflict,
)


DEFAULT_LATTICE_RESULT = Path("/tmp/nonx-lattice-envelope-action-probe.json")
DEFAULT_LATTICE_BITSETS = Path(
    "/tmp/nonx-lattice-envelope-action-probe-bitsets.bin"
)
DEFAULT_CHECKPOINT = Path("/tmp/lattice-T-chronological-L5-checkpoint.json")
EXPECTED_BASE_SHA256 = {
    "metadata": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
    "cache": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
    "L5_state": "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
    "fast_legal": "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed",
    "gate_run": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "amplify193": "f9950c4d8db2507478002841568dc0b6fef883eb0597d90db7971f87e4302ef0",
    "rescue_core": "2b1bde9e846211cd53f75b6300c540a99b92d25b706c174c137f32c9cbf19ebc",
    "fixed_replay_witness_core": (
        "474a525fce7291b00d9c8cd669fd960af742cd0109899b820ae65e2ffe341595"
    ),
}
EXPECTED_LATTICE_CHECKER_SHA256 = (
    "9056394f5529036f2e4515490de4940ca42d04165eae928c32f1b027aae36fed"
)
EXPECTED_LATTICE_RESULT_SHA256 = (
    "9ce2de5f7936349b4cc7e830dcf962f26164693dbf66da1ba3fcc9a1d73e2112"
)
EXPECTED_LATTICE_BITSET_SHA256 = (
    "f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb"
)
EXPECTED_LATTICE_BITSET_BYTES = 3_136_860
EXPECTED_LATTICE_SUMMARY_SHA256 = (
    "adad358d0878cb9e72d420b4cd15fcbac4bd31423a11b59ddfa5ce939cb30201"
)
BITSET_MAGIC = b"NTACB001"
BITSET_SCHEMA = 1
SCHEMA_VERSION = 1
MAX_SURVIVOR_TARGET = 100
CHECKPOINT_INTERVAL = 50
PRIMARY_ACTION_CHANNEL = "zero"
PRIMARY_PROJECTION_POLICY = "global-empty"


class DeadlineReached(Exception):
    def __init__(self, pending):
        super().__init__(pending)
        self.pending = pending


class NoSurvivor(Exception):
    def __init__(self, details):
        super().__init__(details)
        self.details = details


def ensure_final_pins():
    pins = {
        "checker": EXPECTED_LATTICE_CHECKER_SHA256,
        "result": EXPECTED_LATTICE_RESULT_SHA256,
        "bitset": EXPECTED_LATTICE_BITSET_SHA256,
        "summary": EXPECTED_LATTICE_SUMMARY_SHA256,
    }
    if any(value == "PENDING" for value in pins.values()) or not (
        EXPECTED_LATTICE_BITSET_BYTES > 0
    ):
        raise RuntimeError("lattice-T action artifacts are not pinned", pins)


def verify_inputs(args):
    ensure_final_pins()
    paths = {
        "metadata": Path(args.metadata),
        "cache": Path(args.cache),
        "L5_state": ROOT / "gate2-l7-construction-L5.pkl",
        "fast_legal": ROOT / "fast_legal.py",
        "gate_run": ROOT / "gate_run.py",
        "amplify193": ROOT / "amplify193.py",
        "rescue_core": (
            ROOT / "design" / "potential_policy_chronological_rescue.py"
        ),
        "fixed_replay_witness_core": (
            ROOT / "design" / "fixed_policy_chronological_replay.py"
        ),
    }
    observed = {name: rescue.file_sha256(path) for name, path in paths.items()}
    if observed != EXPECTED_BASE_SHA256:
        raise AssertionError("base input drift", EXPECTED_BASE_SHA256, observed)
    extra_paths = {
        "lattice_checker": (
            ROOT / "design" / "nonx_scc_core_action_probe.py"
        ),
        "lattice_result": Path(args.lattice_result),
        "lattice_bitset": Path(args.lattice_bitsets),
        "lattice_summary": (
            ROOT / "design" / "nonx-lattice-envelope-action-probe-summary.json"
        ),
    }
    extra = {
        name: rescue.file_sha256(path) for name, path in extra_paths.items()
    }
    expected_extra = {
        "lattice_checker": EXPECTED_LATTICE_CHECKER_SHA256,
        "lattice_result": EXPECTED_LATTICE_RESULT_SHA256,
        "lattice_bitset": EXPECTED_LATTICE_BITSET_SHA256,
        "lattice_summary": EXPECTED_LATTICE_SUMMARY_SHA256,
    }
    if extra != expected_extra:
        raise AssertionError("lattice artifact drift", expected_extra, extra)
    if Path(args.cache).stat().st_size != rescue.EXPECTED_CACHE_BYTES:
        raise AssertionError("compact cache byte-size drift")
    if Path(args.lattice_bitsets).stat().st_size != (
        EXPECTED_LATTICE_BITSET_BYTES
    ):
        raise AssertionError("lattice bitset byte-size drift")
    return {**observed, **extra}


def load_lattice_result(path):
    with Path(path).open() as handle:
        result = json.load(handle)
    if result["checker"]["sha256"] != EXPECTED_LATTICE_CHECKER_SHA256:
        raise AssertionError("lattice result/checker drift")
    sidecar = result["accepted_ordinal_bitset_sidecar"]
    if sidecar["sha256"] != EXPECTED_LATTICE_BITSET_SHA256 or sidecar[
        "bytes"
    ] != EXPECTED_LATTICE_BITSET_BYTES:
        raise AssertionError("lattice result/sidecar drift")
    return result, sidecar


def parse_bitsets(bitset, sidecar, cache_blocks):
    if bitset[:len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("lattice bitset magic drift")
    schema, block_count = struct.unpack_from("<II", bitset, len(BITSET_MAGIC))
    if schema != BITSET_SCHEMA or block_count != rescue.EXPECTED_STEPS:
        raise AssertionError("lattice bitset header drift")
    metadata = sidecar["blocks"]
    if len(metadata) != rescue.EXPECTED_STEPS:
        raise AssertionError("lattice bitset metadata count drift")
    cursor = len(BITSET_MAGIC) + 8
    zero_digest = hashlib.sha256()
    ordered_digest = hashlib.sha256()
    records = []
    for step in range(rescue.EXPECTED_STEPS):
        block_offset = cursor
        values = struct.unpack_from("<IIIII", bitset, cursor)
        cursor += 20
        observed_step, words, byte_count, zero_count, ordered_count = values
        if observed_step != step or words != cache_blocks[step]["words"]:
            raise AssertionError("lattice/cache step drift", step)
        if byte_count != (words + 7) // 8:
            raise AssertionError("lattice bitset length drift", step)
        zero_offset = cursor
        zero = bitset[cursor:cursor + byte_count]
        cursor += byte_count
        ordered_offset = cursor
        ordered = bitset[cursor:cursor + byte_count]
        cursor += byte_count
        if sum(byte.bit_count() for byte in zero) != zero_count or sum(
            byte.bit_count() for byte in ordered
        ) != ordered_count:
            raise AssertionError("lattice bitset population drift", step)
        if any(zero[index] & ~ordered[index] for index in range(byte_count)):
            raise AssertionError("zero-T bitset is not ordered-T subset", step)
        valid = words & 7
        if valid:
            padding = ~((1 << valid) - 1) & 0xFF
            if (zero[-1] | ordered[-1]) & padding:
                raise AssertionError("lattice bitset padding drift", step)
        observed_metadata = {
            "step": step,
            "words": words,
            "block_offset": block_offset,
            "block_bytes": 20 + 2 * byte_count,
            "zero_envelope": {
                "offset": zero_offset,
                "bytes": byte_count,
                "set_bits": zero_count,
                "sha256": hashlib.sha256(zero).hexdigest(),
            },
            "ordered_envelope": {
                "offset": ordered_offset,
                "bytes": byte_count,
                "set_bits": ordered_count,
                "sha256": hashlib.sha256(ordered).hexdigest(),
            },
            "unused_high_bits_in_final_byte_are_zero": True,
        }
        if metadata[step] != observed_metadata:
            raise AssertionError("lattice bitset metadata drift", step)
        zero_digest.update(struct.pack("<II", step, byte_count))
        zero_digest.update(zero)
        ordered_digest.update(struct.pack("<II", step, byte_count))
        ordered_digest.update(ordered)
        records.append({
            "step": step,
            "words": words,
            "zero": {
                "offset": zero_offset,
                "set_bits": zero_count,
            },
            "ordered": {
                "offset": ordered_offset,
                "set_bits": ordered_count,
            },
        })
    if cursor != len(bitset):
        raise AssertionError("lattice bitset trailing bytes")
    if zero_digest.hexdigest() != sidecar[
        "zero_envelope_ordinal_bitsets_sha256"
    ] or ordered_digest.hexdigest() != sidecar[
        "ordered_envelope_ordinal_bitsets_sha256"
    ]:
        raise AssertionError("lattice bitset aggregate digest drift")
    return tuple(records)


def action_accepts(bitset, record, channel, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("action ordinal outside step domain")
    selected = record[channel]
    index = ordinal - 1
    return bool(
        bitset[selected["offset"] + (index >> 3)] & (1 << (index & 7))
    )


def intrinsic_projection_clean(start, target, interiors):
    fibres = [point[1:] for point in interiors]
    return (
        len(set(fibres)) == len(fibres)
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


def digit_simple(start, interiors):
    bits = 0
    for point in interiors:
        y = point[1] - start[1]
        z = point[2] - start[2]
        digit = (y - 3 * z) % 9
        bit = 1 << digit
        if digit == 0 or bits & bit:
            return False
        bits |= bit
    return True


def apply_selected(interiors, store, yz_counts, projection_policy):
    for point in interiors:
        fibre = point[1:]
        if projection_policy == "global-empty" and yz_counts[fibre]:
            raise AssertionError("selected word reuses a global yz fibre")
        yz_counts[fibre] += 1
    store.add_many(interiors)


def prefix_commitment(store, yz_counts, records, next_rank):
    fields = {
        "next_construction_rank": next_rank,
        "selection_record_stream_sha256": rescue.stable_hash(records),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": (
            rescue.point_stream_sha256(store.pts)
        ),
        "point_set_sha256": rescue.stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": rescue.stable_hash(
            sorted(yz_counts.items())
        ),
    }
    fields["prefix_state_sha256"] = rescue.stable_hash(fields)
    return fields


def build_static(args, checker_sha256, input_sha256, parent_word, anchors, schedule):
    static = {
        "level": 5,
        "checker_sha256": checker_sha256,
        "input_sha256": input_sha256,
        "action_channel": args.action_channel,
        "projection_policy": args.projection_policy,
        "require_digit_simple": args.require_digit_simple,
        "survivor_certificate_target": args.survivor_certificate_target,
        "gaps": len(parent_word),
        "anchors": len(anchors),
        "parent_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
        "anchor_stream_sha256": rescue.stable_hash(anchors),
        "schedule_sha256": rescue.stable_hash(schedule),
        "terminal_first_survivor_audit_complete": False,
    }
    static["static_state_sha256"] = rescue.stable_hash(static)
    return static


def seal_checkpoint(checkpoint):
    payload = copy.deepcopy(checkpoint)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = rescue.stable_hash(payload)
    return payload


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    rescue.atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def load_checkpoint(path, static, initial_prefix):
    path = Path(path)
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "partial",
            "static": static,
            "next_construction_rank": 0,
            "selection_records": [],
            "pending_scan": None,
            "prefix": initial_prefix,
            "audit": {
                "first_survivor_audited_through_rank": 0,
                "terminal_audit_complete": False,
            },
        }
    with path.open() as handle:
        checkpoint = json.load(handle)
    digest = checkpoint.pop("checkpoint_payload_sha256", None)
    if digest != rescue.stable_hash(checkpoint):
        raise AssertionError("chronological checkpoint digest drift")
    checkpoint["checkpoint_payload_sha256"] = digest
    if checkpoint["schema_version"] != SCHEMA_VERSION or checkpoint[
        "static"
    ] != static:
        raise AssertionError("chronological checkpoint static/schema drift")
    if checkpoint["next_construction_rank"] != len(
        checkpoint["selection_records"]
    ):
        raise AssertionError("chronological checkpoint rank/record drift")
    pending = checkpoint["pending_scan"]
    if pending is not None and pending["construction_rank"] != checkpoint[
        "next_construction_rank"
    ]:
        raise AssertionError("chronological pending-rank drift")
    return checkpoint


def reconstruct_prefix(
    checkpoint, parent_word, anchors, schedule, cache, blocks, bitset,
    action_records, args,
):
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    for rank, record in enumerate(checkpoint["selection_records"]):
        gap = schedule[rank]
        step = parent_word[gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("stored chronological schedule drift", rank)
        word = tuple(record["selected_word"])
        offset = record["cache_record_offset"]
        length = cache[offset]
        if length != len(word) or tuple(
            cache[offset + 1:offset + 1 + length]
        ) != word:
            raise AssertionError("stored chronological cache bytes drift", rank)
        ordinal = record["first_survivor_ordinal_1_based"]
        if not action_accepts(
            bitset, action_records[step], args.action_channel, ordinal
        ):
            raise AssertionError("stored word lost lattice action membership")
        interiors = tuple(rescue.word_interiors(anchors[gap], word))
        if rescue.endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("stored chronological endpoint drift", rank)
        intrinsic = intrinsic_projection_clean(
            anchors[gap], anchors[gap + 1], interiors
        )
        if not intrinsic:
            raise AssertionError("stored word lost intrinsic projection cleanliness")
        if args.projection_policy == "global-empty" and not (
            global_projection_clean(interiors, yz_counts)
        ):
            raise AssertionError("stored word lost global projection cleanliness")
        if args.require_digit_simple and not digit_simple(
            anchors[gap], interiors
        ):
            raise AssertionError("stored word lost digit simplicity")
        apply_selected(
            interiors, store, yz_counts, args.projection_policy
        )
    observed = prefix_commitment(
        store, yz_counts, checkpoint["selection_records"],
        checkpoint["next_construction_rank"],
    )
    if observed != checkpoint["prefix"]:
        raise AssertionError("chronological prefix commitment drift")
    return store, yz_counts


def empty_scan(rank, gap, step, block, static_action_count):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "static_action_words": static_action_count,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "domain_words_scanned": 0,
        "action_incompatible_skipped": 0,
        "action_compatible_seen": 0,
        "digit_rejected": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "first_projection_rejection_witness": None,
        "first_exact_legality_rejection_witness": None,
        "certified_survivors": [],
    }


def validate_pending(scan, rank, gap, step, block):
    if (scan["construction_rank"], scan["gap"], scan["step"]) != (
        rank, gap, step
    ):
        raise AssertionError("pending chronological identity drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    if not 1 <= ordinal <= block["words"] + 1 or not (
        block["start"] <= cursor <= block["end"]
    ):
        raise AssertionError("pending chronological cursor drift")
    if scan["domain_words_scanned"] != ordinal - 1:
        raise AssertionError("pending chronological ordinal/count drift")
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scan["domain_words_scanned"]:
        raise AssertionError("pending action partition drift")
    after_digit = scan["action_compatible_seen"] - scan["digit_rejected"]
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != after_digit:
        raise AssertionError("pending projection partition drift")
    if scan["exact_legality_rejected"] + len(
        scan["certified_survivors"]
    ) != scan["projection_clean_exact_tested"]:
        raise AssertionError("pending exact-legality partition drift")


def projection_test(args, start, target, interiors, store, yz_counts):
    intrinsic = intrinsic_projection_clean(start, target, interiors)
    if args.projection_policy == "intrinsic":
        passed = intrinsic
    else:
        passed = intrinsic and global_projection_clean(interiors, yz_counts)
    witness = None
    if not passed:
        fibre_owner = {}
        for index, point in enumerate(store.pts):
            fibre_owner.setdefault(point[1:], index)
        witness = first_projection_conflict(
            interiors, store.pts, fibre_owner
        )
        if witness is None:
            witness = {
                "kind": "endpoint_fibre_or_intrinsic_projection_conflict",
                "start_fibre": list(start[1:]),
                "target_fibre": list(target[1:]),
                "interior_fibres": [list(point[1:]) for point in interiors],
            }
    return passed, witness


def finalize_selection(scan, block, action_record, exhaustive):
    survivors = scan["certified_survivors"]
    if not survivors:
        raise NoSurvivor({
            **scan,
            "domain_words": block["words"],
            "exact_full_restricted_domain_exhausted": exhaustive,
        })
    first = survivors[0]
    return {
        "construction_rank": scan["construction_rank"],
        "gap": scan["gap"],
        "step": scan["step"],
        "domain_words": block["words"],
        "static_action_words": action_record["set_bits"],
        "first_survivor_ordinal_1_based": first["ordinal_1_based"],
        "cache_record_offset": first["cache_record_offset"],
        "selected_word": first["word"],
        "certified_survivor_count": len(survivors),
        "certified_survivors": survivors,
        "survivor_census_exhaustive": exhaustive,
        "scan_counters_through_certificate": {
            key: scan[key]
            for key in (
                "domain_words_scanned",
                "action_incompatible_skipped",
                "action_compatible_seen",
                "digit_rejected",
                "projection_rejected",
                "projection_clean_exact_tested",
                "exact_legality_rejected",
            )
        },
        "first_projection_rejection_witness": scan[
            "first_projection_rejection_witness"
        ],
        "first_exact_legality_rejection_witness": scan[
            "first_exact_legality_rejection_witness"
        ],
    }


def select_first(
    cache, block, bitset, action_record, rank, gap, step, start, target,
    store, yz_counts, pending, args, deadline,
):
    channel_record = action_record[args.action_channel]
    scan = copy.deepcopy(pending) if pending is not None else empty_scan(
        rank, gap, step, block, channel_record["set_bits"]
    )
    validate_pending(scan, rank, gap, step, block)
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    memo = {}
    while ordinal <= block["words"]:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "lattice chronological domain scan"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        record_offset = cursor
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("chronological cache boundary drift", step, ordinal)
        word = tuple(cache[cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1
        if not action_accepts(
            bitset, action_record, args.action_channel, ordinal
        ):
            scan["action_incompatible_skipped"] += 1
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        interiors = tuple(rescue.word_interiors(start, word))
        if args.require_digit_simple and not digit_simple(start, interiors):
            scan["digit_rejected"] += 1
            ordinal += 1
            continue
        projection_passed, projection_witness = projection_test(
            args, start, target, interiors, store, yz_counts
        )
        if not projection_passed:
            scan["projection_rejected"] += 1
            if scan["first_projection_rejection_witness"] is None:
                scan["first_projection_rejection_witness"] = {
                    "ordinal_1_based": ordinal,
                    "word": list(word),
                    "witness": projection_witness,
                }
            ordinal += 1
            continue
        scan["projection_clean_exact_tested"] += 1
        if not rescue.word_legal_fast(start, word, store, memo, rescue.MENU):
            scan["exact_legality_rejected"] += 1
            if scan["first_exact_legality_rejection_witness"] is None:
                scan["first_exact_legality_rejection_witness"] = {
                    "ordinal_1_based": ordinal,
                    "word": list(word),
                    **rescue.exact_legality_rejection(interiors, store),
                }
            ordinal += 1
            continue
        if not rescue.word_legal(
            start, word, store.pts, store.pset, {}
        ):
            raise AssertionError("fast/reference chronological disagreement")
        if rescue.endpoint(start, word) != target:
            raise AssertionError("chronological selected endpoint drift")
        scan["certified_survivors"].append({
            "ordinal_1_based": ordinal,
            "cache_record_offset": record_offset,
            "word": list(word),
            "intrinsic_projection_clean": True,
            "global_projection_clean": global_projection_clean(
                interiors, yz_counts
            ),
            "digit_simple": digit_simple(start, interiors),
            "ordered_T_accepted": action_accepts(
                bitset, action_record, "ordered", ordinal
            ),
            "zero_T_accepted": action_accepts(
                bitset, action_record, "zero", ordinal
            ),
        })
        ordinal += 1
        if len(scan["certified_survivors"]) >= (
            args.survivor_certificate_target
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            return finalize_selection(scan, block, channel_record, False)
    scan["next_ordinal_1_based"] = ordinal
    scan["next_cache_cursor"] = cursor
    if cursor != block["end"]:
        raise AssertionError("exhausted chronological domain cursor drift")
    if scan["action_compatible_seen"] != channel_record["set_bits"]:
        raise AssertionError("exhausted lattice action population drift")
    return finalize_selection(scan, block, channel_record, True)


def run_chunk(args):
    started = time.monotonic()
    deadline = started + min(args.max_seconds, rescue.MAX_WORK_SECONDS)
    checker_path = Path(__file__).resolve()
    checker_sha256 = rescue.file_sha256(checker_path)
    policy = rescue.resource_policy()
    input_sha256 = verify_inputs(args)
    _metadata, blocks = rescue.load_metadata(args.metadata)
    parent_word, anchors, schedule = rescue.load_l5_state()
    lattice_result, sidecar = load_lattice_result(args.lattice_result)
    with Path(args.cache).open("rb") as cache_handle, Path(
        args.lattice_bitsets
    ).open("rb") as bitset_handle:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        bitset = mmap.mmap(bitset_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(rescue.CACHE_MAGIC)] != rescue.CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            action_records = parse_bitsets(bitset, sidecar, blocks)
            static = build_static(
                args, checker_sha256, input_sha256,
                parent_word, anchors, schedule,
            )
            initial_store = rescue.Store(anchors)
            initial_yz = Counter(point[1:] for point in anchors)
            initial_prefix = prefix_commitment(
                initial_store, initial_yz, [], 0
            )
            checkpoint = load_checkpoint(
                args.checkpoint, static, initial_prefix
            )
            store, yz_counts = reconstruct_prefix(
                checkpoint, parent_word, anchors, schedule,
                cache, blocks, bitset, action_records, args,
            )
            if checkpoint["status"] == "hard-jam":
                return checkpoint, {
                    "new_gaps": 0,
                    "stop_reason": "previous exact hard-jam",
                }
            added = 0
            stop_reason = "new-gap-limit"
            while checkpoint["next_construction_rank"] < len(schedule):
                if added >= args.max_new_gaps:
                    break
                if rescue.enforce_runtime(deadline, "between lattice stitches"):
                    stop_reason = "time-limit"
                    break
                rank = checkpoint["next_construction_rank"]
                gap = schedule[rank]
                step = parent_word[gap]
                try:
                    record = select_first(
                        cache, blocks[step], bitset, action_records[step],
                        rank, gap, step, anchors[gap], anchors[gap + 1],
                        store, yz_counts, checkpoint["pending_scan"],
                        args, deadline,
                    )
                except DeadlineReached as reached:
                    checkpoint["pending_scan"] = reached.pending
                    stop_reason = "time-limit-during-domain-scan"
                    break
                except NoSurvivor as failure:
                    checkpoint["pending_scan"] = None
                    checkpoint["status"] = "hard-jam"
                    checkpoint["obstruction"] = failure.details
                    stop_reason = "exact-restricted-hard-jam"
                    break
                word = tuple(record["selected_word"])
                interiors = tuple(
                    rescue.word_interiors(anchors[gap], word)
                )
                checkpoint["selection_records"].append(record)
                apply_selected(
                    interiors, store, yz_counts, args.projection_policy
                )
                checkpoint["next_construction_rank"] += 1
                checkpoint["pending_scan"] = None
                checkpoint["prefix"] = prefix_commitment(
                    store, yz_counts, checkpoint["selection_records"],
                    checkpoint["next_construction_rank"],
                )
                added += 1
                if added % CHECKPOINT_INTERVAL == 0:
                    checkpoint["last_run"] = {
                        "intermediate": True,
                        "new_gaps": added,
                        "resource_policy": policy,
                    }
                    save_checkpoint(args.checkpoint, checkpoint)
            if checkpoint["next_construction_rank"] == len(schedule):
                checkpoint["status"] = "construction-complete-audit-pending"
                stop_reason = "construction-complete"
            checkpoint["prefix"] = prefix_commitment(
                store, yz_counts, checkpoint["selection_records"],
                checkpoint["next_construction_rank"],
            )
            checkpoint["last_run"] = {
                "new_gaps": added,
                "stop_reason": stop_reason,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "maximum_resident_bytes": rescue.maximum_resident_bytes(),
                "resource_policy": policy,
            }
            save_checkpoint(args.checkpoint, checkpoint)
        finally:
            bitset.close()
            cache.close()
    if rescue.file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("lattice chronological checker changed during run")
    elapsed = time.monotonic() - started
    resident = rescue.maximum_resident_bytes()
    if elapsed > rescue.MAX_SECONDS or resident > rescue.MAX_RESIDENT_BYTES:
        raise RuntimeError("lattice chronological resource bound exceeded")
    return checkpoint, {
        "new_gaps": added,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
        "resource_policy": policy,
        "lattice_result_status": lattice_result["status"],
    }


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
        raise AssertionError("synthetic lattice bit convention drift")
    start = (10, 20, 30)
    target = (20, 25, 35)
    interiors = ((11, 21, 31), (12, 22, 32))
    if not intrinsic_projection_clean(start, target, interiors):
        raise AssertionError("synthetic intrinsic projection drift")
    if digit_simple((0, 0, 0), ((0, 1, 0), (0, 2, 0))) is not True:
        raise AssertionError("synthetic digit predicate drift")
    globally_occupied = Counter({(21, 31): 1})
    if not intrinsic_projection_clean(start, target, interiors):
        raise AssertionError("synthetic intrinsic predicate drift")
    if global_projection_clean(interiors, globally_occupied):
        raise AssertionError("synthetic global-empty predicate drift")
    if PRIMARY_ACTION_CHANNEL != "zero" or (
        PRIMARY_PROJECTION_POLICY != "global-empty"
    ):
        raise AssertionError("primary policy default drift")
    return {
        "status": "passed",
        "primary_action_channel": PRIMARY_ACTION_CHANNEL,
        "primary_projection_policy": PRIMARY_PROJECTION_POLICY,
        "weaker_intrinsic_passes_while_primary_global_empty_rejects": True,
        "ordinal_bits_tested": 10,
        "projection_modes": ["global-empty", "intrinsic"],
        "action_channels": ["zero", "ordered"],
        "mid_domain_resume_fields_present": True,
    }


def estimate():
    return {
        "status": "no artifact opened and no cache scanned",
        "primary_policy": (
            "zero-T accepted ordinal AND global empty-yz AND exact global legality"
        ),
        "diagnostic_action_channel": "ordered-T",
        "diagnostic_projection_policy": "intrinsic-only",
        "optional_digit_simple_filter": True,
        "resumable_mid_domain_firstness": True,
        "survivor_certificate_target_range": [1, MAX_SURVIVOR_TARGET],
        "maximum_work_seconds": rescue.MAX_WORK_SECONDS,
        "hard_maximum_seconds": rescue.MAX_SECONDS,
        "hard_maximum_resident_bytes": rescue.MAX_RESIDENT_BYTES,
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "lattice_artifact_pins_finalized": not (
            EXPECTED_LATTICE_RESULT_SHA256 == "PENDING"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("estimate")
    subparsers.add_parser("self-check")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--metadata", default=rescue.DEFAULT_METADATA)
    run_parser.add_argument("--cache", default=rescue.DEFAULT_CACHE)
    run_parser.add_argument("--lattice-result", default=DEFAULT_LATTICE_RESULT)
    run_parser.add_argument("--lattice-bitsets", default=DEFAULT_LATTICE_BITSETS)
    run_parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    run_parser.add_argument(
        "--action-channel", choices=("zero", "ordered"),
        default=PRIMARY_ACTION_CHANNEL,
    )
    run_parser.add_argument(
        "--projection-policy",
        choices=("global-empty", "intrinsic"),
        default=PRIMARY_PROJECTION_POLICY,
    )
    run_parser.add_argument("--require-digit-simple", action="store_true")
    run_parser.add_argument(
        "--survivor-certificate-target", type=int, default=1
    )
    run_parser.add_argument("--max-new-gaps", type=int, default=500)
    run_parser.add_argument(
        "--max-seconds", type=float, default=rescue.MAX_WORK_SECONDS
    )
    args = parser.parse_args()
    if args.mode == "estimate":
        print(json.dumps(estimate(), sort_keys=True, indent=2))
        return
    if args.mode == "self-check":
        print(json.dumps(self_check(), sort_keys=True, indent=2))
        return
    if not 1 <= args.survivor_certificate_target <= MAX_SURVIVOR_TARGET:
        raise ValueError("survivor-certificate-target outside [1,100]")
    if not 1 <= args.max_new_gaps <= rescue.EXPECTED_GAPS:
        raise ValueError("max-new-gaps outside [1,2457]")
    if not 0 < args.max_seconds <= rescue.MAX_WORK_SECONDS:
        raise ValueError("max-seconds outside (0,115]")
    checkpoint, observation = run_chunk(args)
    print(json.dumps({
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_sha256": rescue.file_sha256(args.checkpoint),
        "status": checkpoint["status"],
        "next_construction_rank": checkpoint["next_construction_rank"],
        "total_gaps": rescue.EXPECTED_GAPS,
        "pending_scan": checkpoint["pending_scan"],
        "obstruction": checkpoint.get("obstruction"),
        "last_selection_record": (
            checkpoint["selection_records"][-1]
            if checkpoint["selection_records"] else None
        ),
        "observation": observation,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
