#!/usr/bin/env python3
"""Independent terminal audit for ``lattice_t_l6_continuation.py``.

The construction checkpoint is read-only.  For each fragile-order stitch this
checker independently rescans compact-cache ordinals one through the stored
winner and checks the exact primary conjunction: zero-T action membership,
global empty-(y,z), and exact legality against the complete prefix.  Both the
optimized and reference legality routines are evaluated for every candidate
that reaches the exact test; disagreement or an earlier survivor is fatal.

After firstness is complete, the checker reassembles the single realized walk
in natural gap order.  It independently verifies the final no-new-yz invariant
and then checks every point against the directions to every earlier point.
Both phases have separate resumable cursors and a separate sealed audit
checkpoint.  A terminal artifact is emitted only after both phases complete.

The construction-checkpoint pins intentionally remain PENDING until the L6
construction finishes.  Audit mode is therefore fail-closed at present;
``estimate`` and synthetic ``self-check`` open no large artifacts.
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

from design import lattice_t_l6_continuation as producer  # noqa: E402


rescue = producer.rescue

DEFAULT_SOURCE = Path(
    "/tmp/lattice-T-chronological-L6-checkpoint-v1.json"
)
DEFAULT_AUDIT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L6-audit-checkpoint-v1.json"
)
DEFAULT_OUTPUT = Path(
    "/tmp/lattice-T-chronological-L6-audit-v1.json"
)

# Freeze this source identity together with the completed construction pins.
# It remains pending so a last pre-launch correction cannot accidentally make
# a future source checkpoint appear to belong to a different checker.
EXPECTED_PRODUCER_SHA256 = (
    "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
)
EXPECTED_SOURCE_SHA256 = (
    "82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7"
)
EXPECTED_SOURCE_BYTES = 18_699_543
EXPECTED_SOURCE_PAYLOAD_SHA256 = (
    "772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa"
)
EXPECTED_SOURCE_PREFIX_SHA256 = (
    "7626fbb39cedfeff134c064989f54054e268d0c3fd881a4cd8b0782ae2eb917d"
)
EXPECTED_SOURCE_SELECTION_SHA256 = (
    "219ad3095dafea4aecba62be79e8f4d446c814285c0aa3e2a1a4282bdc99981c"
)
EXPECTED_SOURCE_MAX_FIRST_ORDINAL = 19_221

EXPECTED_GAPS = producer.EXPECTED_PARENT_STEPS
EXPECTED_ANCHORS = producer.EXPECTED_PARENT_POINTS
EXPECTED_INHERITED_DOUBLE_FIBRES = (
    producer.EXPECTED_INHERITED_DOUBLE_FIBRES
)
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 25
HARD_MAX_SECONDS = 600.0
HARD_MAX_ITEMS = 1_000
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())


class DeadlineReached(Exception):
    def __init__(self, pending=None):
        super().__init__(pending)
        self.pending = pending


def assert_checker_unchanged():
    if rescue.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ):
        raise RuntimeError("lattice-T L6 audit checker changed during execution")


def source_pins():
    return {
        "producer": EXPECTED_PRODUCER_SHA256,
        "source_file": EXPECTED_SOURCE_SHA256,
        "source_payload": EXPECTED_SOURCE_PAYLOAD_SHA256,
        "source_prefix": EXPECTED_SOURCE_PREFIX_SHA256,
        "source_selection": EXPECTED_SOURCE_SELECTION_SHA256,
    }


def ensure_source_pins():
    pins = source_pins()
    if any(value == "PENDING" for value in pins.values()) or not (
        EXPECTED_SOURCE_BYTES > 0 and EXPECTED_SOURCE_MAX_FIRST_ORDINAL > 0
    ):
        raise RuntimeError(
            "completed L6 construction pins are not finalized; audit is locked",
            pins,
        )


def verify_producer():
    observed = rescue.file_sha256(Path(producer.__file__))
    if observed != EXPECTED_PRODUCER_SHA256:
        raise AssertionError("L6 producer source drift", observed)
    return observed


def verify_source(path, expected_static):
    ensure_source_pins()
    path = Path(path)
    if path.stat().st_size != EXPECTED_SOURCE_BYTES:
        raise AssertionError("L6 source byte-size drift", path.stat().st_size)
    observed = rescue.file_sha256(path)
    if observed != EXPECTED_SOURCE_SHA256:
        raise AssertionError("L6 source file drift", observed)
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(source) or internal != (
        EXPECTED_SOURCE_PAYLOAD_SHA256
    ):
        raise AssertionError("L6 source payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source["schema_version"] != producer.SCHEMA_VERSION:
        raise AssertionError("L6 source schema drift")
    if source["static"] != expected_static:
        raise AssertionError("L6 source static-state drift")
    if source["status"] != "construction-complete-audit-pending":
        raise AssertionError("L6 source construction is not audit-ready")
    if source["next_construction_rank"] != EXPECTED_GAPS or len(
        source["selection_records"]
    ) != EXPECTED_GAPS or source["pending_scan"] is not None:
        raise AssertionError("L6 source construction extent drift")
    if source["prefix"]["prefix_state_sha256"] != (
        EXPECTED_SOURCE_PREFIX_SHA256
    ):
        raise AssertionError("L6 source prefix pin drift")
    if rescue.stable_hash(source["selection_records"]) != (
        EXPECTED_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("L6 source selection pin drift")
    maximum = max(
        record["first_survivor_ordinal_1_based"]
        for record in source["selection_records"]
    )
    if maximum != EXPECTED_SOURCE_MAX_FIRST_ORDINAL:
        raise AssertionError("L6 source maximum first ordinal drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def open_context(args):
    ensure_source_pins()
    producer_sha256 = verify_producer()
    base = producer.open_context(args)
    try:
        source, source_snapshot = verify_source(
            args.source, base["l6"]["static"]
        )
    except BaseException:
        producer.close_context(base)
        raise
    base.update({
        "source": source,
        "source_snapshot": source_snapshot,
        "producer_sha256": producer_sha256,
    })
    return base


def audit_static(context):
    fields = {
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": context["producer_sha256"],
        "source_checkpoint": context["source_snapshot"],
        "source_prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "source_selection_record_stream_sha256": (
            EXPECTED_SOURCE_SELECTION_SHA256
        ),
        "policy": {
            "action_channel": "zero",
            "projection_policy": "global-empty",
            "require_digit_simple": False,
            "selection_order": "compact-cache ordinal order",
            "stitch_order": "D2--4 fragile-first, then ordered gap index",
        },
        "gaps": EXPECTED_GAPS,
        "anchors": EXPECTED_ANCHORS,
        "parent_terminal_sha256": (
            producer.EXPECTED_PARENT_TERMINAL_SHA256
        ),
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
    store = rescue.Store(context["l6"]["anchors"])
    yz_counts = Counter(point[1:] for point in context["l6"]["anchors"])
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "firstness_audited_through_rank": 0,
        "pending_firstness_scan": None,
        "audit_records": [],
        "audit_record_stream_sha256": rescue.stable_hash([]),
        "audited_prefix": producer.prefix_commitment(
            store, yz_counts, [], 0
        ),
        "ordered_verifier": {
            "next_point": 0,
            "total_points": None,
            "ordered_point_stream_sha256": None,
            "ordered_point_set_sha256": None,
            "final_yz_occupancy_sha256": None,
            "final_no_new_yz_coincidence": False,
            "complete": False,
        },
        "terminal_output": None,
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
        raise AssertionError("L6 audit checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION or checkpoint[
        "static"
    ] != static:
        raise AssertionError("L6 audit checkpoint schema/static drift")
    cursor = checkpoint["firstness_audited_through_rank"]
    if not 0 <= cursor <= EXPECTED_GAPS or len(
        checkpoint["audit_records"]
    ) != cursor:
        raise AssertionError("L6 audit firstness cursor drift")
    if checkpoint["audit_record_stream_sha256"] != rescue.stable_hash(
        checkpoint["audit_records"]
    ):
        raise AssertionError("L6 audit record stream drift")
    pending = checkpoint["pending_firstness_scan"]
    if pending is not None and pending["construction_rank"] != cursor:
        raise AssertionError("L6 audit pending/rank drift")
    verifier = checkpoint["ordered_verifier"]
    if verifier["next_point"] and cursor != EXPECTED_GAPS:
        raise AssertionError("ordered verification preceded firstness")
    total = verifier["total_points"]
    if total is not None and not 0 <= verifier["next_point"] <= total:
        raise AssertionError("L6 ordered-verifier cursor drift")
    if verifier["complete"] and (
        total is None or verifier["next_point"] != total
    ):
        raise AssertionError("L6 ordered-verifier completion drift")
    return checkpoint


def cache_word_at_offset(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("audit cache offset outside step block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("audit cache record boundary drift")
    return tuple(cache[offset + 1:end])


def action_accepts(bitset, record, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("audit action ordinal outside domain")
    index = ordinal - 1
    channel = record["zero"]
    return bool(
        bitset[channel["offset"] + (index >> 3)] & (1 << (index & 7))
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


def digit_simple(start, interiors):
    digits = set()
    for point in interiors:
        digit = (
            point[1] - start[1] - 3 * (point[2] - start[2])
        ) % 9
        if digit == 0 or digit in digits:
            return False
        digits.add(digit)
    return True


def apply_selected(interiors, store, yz_counts):
    for point in interiors:
        fibre = point[1:]
        if yz_counts[fibre]:
            raise AssertionError("audit selected word reuses a yz fibre")
        yz_counts[fibre] += 1
    store.add_many(interiors)


def reconstruct_audited_prefix(context, checkpoint, deadline):
    l6 = context["l6"]
    records = context["source"]["selection_records"]
    store = rescue.Store(l6["anchors"])
    yz_counts = Counter(point[1:] for point in l6["anchors"])
    cursor = checkpoint["firstness_audited_through_rank"]
    for rank in range(cursor):
        if rank % CHECKPOINT_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing audited L6 prefix"
        ):
            raise DeadlineReached
        source_record = records[rank]
        audit_record = checkpoint["audit_records"][rank]
        gap = l6["schedule"][rank]
        step = l6["parent_word"][gap]
        identity = (rank, gap, step)
        if (
            source_record["construction_rank"], source_record["gap"],
            source_record["step"],
        ) != identity or (
            audit_record["construction_rank"], audit_record["gap"],
            audit_record["step"],
        ) != identity:
            raise AssertionError("audited L6 schedule identity drift", rank)
        expected_audit_fields = {
            "selected_ordinal_1_based": source_record[
                "first_survivor_ordinal_1_based"
            ],
            "cache_record_offset": source_record["cache_record_offset"],
            "selected_word_sha256": hashlib.sha256(
                bytes(source_record["selected_word"])
            ).hexdigest(),
            "earlier_exact_survivors": 0,
            "selected_fast_reference_agreement": True,
            "selected_reference_legal": True,
        }
        for field, expected in expected_audit_fields.items():
            if audit_record.get(field) != expected:
                raise AssertionError("stored L6 audit-record drift", rank, field)
        word = cache_word_at_offset(
            context["cache"], context["blocks"][step],
            source_record["cache_record_offset"],
        )
        if list(word) != source_record["selected_word"]:
            raise AssertionError("audited L6 cache bytes drift", rank)
        ordinal = source_record["first_survivor_ordinal_1_based"]
        if not action_accepts(
            context["bitset"], context["action_records"][step], ordinal
        ):
            raise AssertionError("audited L6 word lost zero-T bit", rank)
        start, target = l6["anchors"][gap], l6["anchors"][gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        if rescue.endpoint(start, word) != target:
            raise AssertionError("audited L6 endpoint drift", rank)
        if not intrinsic_projection_clean(
            start, target, interiors
        ) or not global_projection_clean(interiors, yz_counts):
            raise AssertionError("audited L6 global-yz drift", rank)
        apply_selected(interiors, store, yz_counts)
    observed = producer.prefix_commitment(
        store, yz_counts, records[:cursor], cursor
    )
    if observed != checkpoint["audited_prefix"]:
        raise AssertionError("audited L6 prefix commitment drift")
    if cursor == EXPECTED_GAPS and observed != context["source"]["prefix"]:
        raise AssertionError("audited final L6 prefix/source drift")
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
        "static_zero_T_words": action_count,
    }


def validate_pending(pending, rank, gap, step, block, selected_ordinal):
    identity = (
        pending["construction_rank"], pending["gap"], pending["step"],
        pending["selected_ordinal_1_based"],
    )
    if identity != (rank, gap, step, selected_ordinal):
        raise AssertionError("L6 audit pending identity drift")
    ordinal = pending["next_ordinal_1_based"]
    if not 1 <= ordinal <= selected_ordinal or pending[
        "domain_words_scanned"
    ] != ordinal - 1:
        raise AssertionError("L6 audit pending ordinal/count drift")
    if not block["start"] <= pending["next_cache_cursor"] < block["end"]:
        raise AssertionError("L6 audit pending cache cursor drift")
    if pending["action_incompatible_skipped"] + pending[
        "action_compatible_seen"
    ] != pending["domain_words_scanned"]:
        raise AssertionError("L6 audit pending action partition drift")
    if pending["projection_rejected"] + pending[
        "projection_clean_exact_tested"
    ] != pending["action_compatible_seen"]:
        raise AssertionError("L6 audit pending projection partition drift")
    if pending["exact_legality_rejected"] != pending[
        "projection_clean_exact_tested"
    ]:
        raise AssertionError("L6 audit pending exact partition has survivor")


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
        "digit_simple": digit_simple(context["l6"]["anchors"][gap], interiors),
        "ordered_T_accepted": l5_ordered_accepts(
            context["bitset"], action_record, ordinal
        ),
        "zero_T_accepted": True,
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
        "certified_survivor_count": 1,
        "certified_survivors": [expected_survivor],
        # The producer returns as soon as its one-survivor target is met, even
        # when that winner happens to be the final domain ordinal.
        "survivor_census_exhaustive": False,
        "scan_counters_through_certificate": counters,
    }
    for field, value in expected.items():
        if source_record.get(field) != value:
            raise AssertionError("L6 source selected-record drift", rank, field)
    return expected_survivor


def l5_ordered_accepts(bitset, record, ordinal):
    index = ordinal - 1
    channel = record["ordered"]
    return bool(
        bitset[channel["offset"] + (index >> 3)] & (1 << (index & 7))
    )


def audit_one_stitch(context, rank, store, yz_counts, pending, deadline):
    l6 = context["l6"]
    source_record = context["source"]["selection_records"][rank]
    gap = l6["schedule"][rank]
    step = l6["parent_word"][gap]
    block = context["blocks"][step]
    action_record = context["action_records"][step]
    selected_ordinal = source_record["first_survivor_ordinal_1_based"]
    if not 1 <= selected_ordinal <= block["words"]:
        raise AssertionError("L6 selected ordinal outside domain", rank)
    scan = copy.deepcopy(pending) if pending is not None else empty_pending(
        rank, gap, step, block, selected_ordinal,
        action_record["zero"]["set_bits"],
    )
    validate_pending(scan, rank, gap, step, block, selected_ordinal)
    if scan["static_zero_T_words"] != action_record["zero"]["set_bits"]:
        raise AssertionError("L6 audit pending zero-T population drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    reference_memo = {}
    while ordinal <= selected_ordinal:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "independent L6 firstness domain scan"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("L6 audit cache boundary drift", rank, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1
        if not action_accepts(context["bitset"], action_record, ordinal):
            scan["action_incompatible_skipped"] += 1
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        start, target = l6["anchors"][gap], l6["anchors"][gap + 1]
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
                "L6 fast/reference legality disagreement", rank, ordinal
            )
        if not reference_legal:
            scan["exact_legality_rejected"] += 1
            ordinal += 1
            continue
        if rescue.endpoint(start, word) != target:
            raise AssertionError("eligible L6 word endpoint drift", rank, ordinal)
        if ordinal < selected_ordinal:
            raise AssertionError(
                "earlier L6 primary-policy survivor found", rank, ordinal,
                selected_ordinal, list(word),
            )
        if list(word) != source_record["selected_word"] or offset != (
            source_record["cache_record_offset"]
        ):
            raise AssertionError("stored L6 winner/cache-order drift", rank)
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
            "earlier_exact_survivors": 0,
            "selected_fast_reference_agreement": True,
            "selected_reference_legal": True,
            "selected_static_channels": survivor,
        }
        return audit_record, interiors
    raise AssertionError("stored L6 winner is not a primary-policy survivor")


def ordered_chain(context):
    records = context["source"]["selection_records"]
    selected = {record["gap"]: tuple(record["selected_word"])
                for record in records}
    if set(selected) != set(range(EXPECTED_GAPS)):
        raise AssertionError("L6 source does not select every ordered gap")
    anchors = context["l6"]["anchors"]
    chain = [anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_GAPS):
        word = selected[gap]
        chain.extend(rescue.word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != len(set(chain)):
        raise AssertionError("realized L6 ordered chain repeats a point")
    if len(chain) != context["source"]["prefix"]["placed_point_count"]:
        raise AssertionError("L6 ordered chain/source point extent drift")
    if rescue.stable_hash(sorted(chain)) != context["source"]["prefix"][
        "point_set_sha256"
    ]:
        raise AssertionError("L6 ordered chain/source point-set drift")
    return tuple(chain), tuple(flat_word), selected


def verify_final_yz(anchors, chain):
    initial = Counter(point[1:] for point in anchors)
    final = Counter(point[1:] for point in chain)
    for fibre, count in final.items():
        if count != initial.get(fibre, 1):
            raise AssertionError("terminal L6 no-new-yz failure", fibre)
    doubles = {fibre for fibre, count in final.items() if count == 2}
    initial_doubles = {
        fibre for fibre, count in initial.items() if count == 2
    }
    if doubles != initial_doubles or len(doubles) != (
        EXPECTED_INHERITED_DOUBLE_FIBRES
    ):
        raise AssertionError("terminal L6 doubled-yz set drift")
    return final


def primitive_direction(vector):
    x, y, z = vector
    divisor = gcd(gcd(abs(x), abs(y)), abs(z))
    if divisor == 0:
        raise AssertionError("zero displacement in ordered L6 verifier")
    x, y, z = x // divisor, y // divisor, z // divisor
    if x < 0 or (x == 0 and (y < 0 or (y == 0 and z < 0))):
        x, y, z = -x, -y, -z
    return (x, y, z)


def verify_ordered_point(chain, cursor):
    point = chain[cursor]
    owner = {}
    for index in range(cursor):
        prior = chain[index]
        direction = primitive_direction(tuple(
            prior[axis] - point[axis] for axis in range(3)
        ))
        earlier = owner.get(direction)
        if earlier is not None:
            raise AssertionError(
                "ordered L6 chain contains a collinear triple",
                earlier, index, cursor,
                [list(chain[earlier]), list(prior), list(point)],
            )
        owner[direction] = index


def terminal_payload(context, checkpoint, chain, flat_word, selected, policy):
    records = context["source"]["selection_records"]
    ordinals = [
        record["first_survivor_ordinal_1_based"] for record in records
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": "exact independent terminal finite certificate",
        "checker": {
            "path": "design/lattice_t_l6_audit.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_audit": True,
        },
        "resource_policy": policy,
        "source_checkpoint": context["source_snapshot"],
        "source_producer_sha256": context["producer_sha256"],
        "parent_L5_terminal_sha256": (
            producer.EXPECTED_PARENT_TERMINAL_SHA256
        ),
        "static_state_sha256": checkpoint["static"]["static_state_sha256"],
        "result": {
            "construction_completed": True,
            "gaps": EXPECTED_GAPS,
            "points": len(chain),
            "steps": len(flat_word),
            "first_survivor_audit_completed": True,
            "selected_reference_legality_verified_at_every_stitch": True,
            "fast_reference_agreement_verified_for_every_exact_test": True,
            "global_empty_yz_verified_at_every_stitch": True,
            "final_no_new_yz_coincidence": True,
            "independent_ordered_no_three_collinear_verified": True,
            "minimum_primary_survivors_certified_per_stitch": 1,
            "survivor_counts_exhaustive": False,
            "maximum_first_survivor_ordinal_1_based": max(ordinals),
            "sum_first_survivor_ordinals": sum(ordinals),
            "zero_T_projection_clean_exact_tests": sum(
                record["projection_clean_exact_tested"]
                for record in checkpoint["audit_records"]
            ),
        },
        "commitments": {
            "source_prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
            "selection_record_stream_sha256": (
                EXPECTED_SOURCE_SELECTION_SHA256
            ),
            "audit_record_stream_sha256": checkpoint[
                "audit_record_stream_sha256"
            ],
            "alternate_words_by_gap_sha256": rescue.stable_hash(
                [[gap, list(selected[gap])] for gap in range(EXPECTED_GAPS)]
            ),
            "alternate_flat_step_word_sha256": hashlib.sha256(
                bytes(flat_word)
            ).hexdigest(),
            "alternate_ordered_point_stream_sha256": (
                rescue.point_stream_sha256(chain)
            ),
            "final_point_set_sha256": rescue.stable_hash(sorted(chain)),
            "final_yz_occupancy_sha256": checkpoint["ordered_verifier"][
                "final_yz_occupancy_sha256"
            ],
        },
        "proved": [
            "the pinned lattice-T L6 policy has an exact first survivor at every fragile-order stitch",
            "each winner is zero-T, globally yz-fresh, and reference-legal against its complete prefix",
            "the final realized L6 chain creates no new yz-fibre coincidence",
            "an independent ordered-pair direction scan finds no collinear triple in the realized L6 chain",
        ],
        "not_proved": [
            "positive availability for every reachable safe state or at levels beyond this pinned L6 orbit",
            "a summable or contracting bound on latent far-secant births and re-entry",
            "an unconditional infinite construction",
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
            if rescue.enforce_runtime(deadline, "between L6 audit stitches"):
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
            checkpoint["audited_prefix"] = producer.prefix_commitment(
                store, yz_counts,
                context["source"]["selection_records"][:cursor], cursor,
            )
            work += 1
            if work % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.audit_checkpoint, checkpoint)

        if checkpoint["firstness_audited_through_rank"] == EXPECTED_GAPS:
            if checkpoint["audited_prefix"] != context["source"]["prefix"]:
                raise AssertionError("completed L6 audit prefix/source drift")
            chain, flat_word, selected = ordered_chain(context)
            final_yz = verify_final_yz(context["l6"]["anchors"], chain)
            verifier = checkpoint["ordered_verifier"]
            expected = {
                "total_points": len(chain),
                "ordered_point_stream_sha256": rescue.point_stream_sha256(
                    chain
                ),
                "ordered_point_set_sha256": rescue.stable_hash(sorted(chain)),
                "final_yz_occupancy_sha256": rescue.stable_hash(
                    sorted(final_yz.items())
                ),
            }
            for field, value in expected.items():
                if verifier[field] is not None and verifier[field] != value:
                    raise AssertionError("L6 ordered commitment drift", field)
                verifier[field] = value
            verifier["final_no_new_yz_coincidence"] = True
            while verifier["next_point"] < len(chain):
                if work >= args.max_work_items:
                    stop_reason = "ordered-verifier-work-limit"
                    break
                if rescue.enforce_runtime(deadline, "ordered L6 verifier"):
                    stop_reason = "ordered-verifier-time-limit"
                    break
                verify_ordered_point(chain, verifier["next_point"])
                verifier["next_point"] += 1
                work += 1
                if work % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(args.audit_checkpoint, checkpoint)
                    verifier = checkpoint["ordered_verifier"]
            if verifier["next_point"] == len(chain):
                verifier["complete"] = True
                checkpoint["status"] = "complete"
                stop_reason = "terminal-audit-complete"
                terminal = terminal_payload(
                    context, checkpoint, chain, flat_word, selected, policy
                )
                rescue.atomic_json_dump(terminal, args.output)
                checkpoint["terminal_output"] = {
                    "path": str(Path(args.output).resolve()),
                    "sha256": rescue.file_sha256(args.output),
                    "bytes": Path(args.output).stat().st_size,
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
        }
    finally:
        producer.close_context(context)


def self_check():
    bits = bytes((0b00000101, 0b00000010))
    record = {
        "words": 10,
        "zero": {"offset": 0, "set_bits": 3},
        "ordered": {"offset": 0, "set_bits": 3},
    }
    observed = [action_accepts(bits, record, n) for n in range(1, 11)]
    if observed != [
        True, False, True, False, False,
        False, False, False, False, True,
    ]:
        raise AssertionError("L6 audit ordinal-bit convention drift")
    start, target = (10, 20, 30), (20, 25, 35)
    interiors = ((11, 21, 31), (12, 22, 32))
    if not intrinsic_projection_clean(start, target, interiors):
        raise AssertionError("L6 audit intrinsic projection drift")
    if global_projection_clean(interiors, Counter({(21, 31): 1})):
        raise AssertionError("L6 audit global projection drift")
    if primitive_direction((-2, -4, -6)) != (1, 2, 3):
        raise AssertionError("L6 audit primitive-direction drift")
    collinear = ((0, 0, 0), (1, 1, 1), (2, 2, 2))
    try:
        verify_ordered_point(collinear, 2)
    except AssertionError as error:
        if error.args[0] != "ordered L6 chain contains a collinear triple":
            raise
    else:
        raise AssertionError("L6 audit failed to reject collinear triple")
    clean = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    for cursor in range(len(clean)):
        verify_ordered_point(clean, cursor)
    pins = source_pins()
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_pins_finalized": not any(
            value == "PENDING" for value in pins.values()
        ) and EXPECTED_SOURCE_BYTES > 0,
        "heavy_audit_locked_until_source_pins": True,
        "large_artifacts_opened": False,
        "expected_stitches": EXPECTED_GAPS,
        "independent_ordinal_bits_tested": 10,
        "independent_projection_predicates_tested": True,
        "synthetic_collinear_rejection": True,
        "synthetic_general_position_acceptance": True,
        "firstness_resume_granularity": "cache ordinal within one stitch",
    }


def estimate():
    pins = source_pins()
    return {
        "status": "prepared; audit is fail-closed pending L6 source pins",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_pins": pins,
        "source_pins_finalized": not any(
            value == "PENDING" for value in pins.values()
        ) and EXPECTED_SOURCE_BYTES > 0,
        "source_checkpoint_is_read_only": True,
        "audit_checkpoint_is_separate": True,
        "expected_stitches": EXPECTED_GAPS,
        "firstness_policy": (
            "zero-T AND global empty-yz AND exact fast/reference legality"
        ),
        "firstness_resume_granularity": "cache ordinal within one stitch",
        "terminal_verifier": (
            "ordered chain; each point checked against all prior directions"
        ),
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_seconds_per_chunk": HARD_MAX_SECONDS,
        "maximum_work_items_per_chunk": HARD_MAX_ITEMS,
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
    parser.add_argument(
        "--parent-source", default=str(producer.DEFAULT_PARENT_SOURCE)
    )
    parser.add_argument(
        "--parent-terminal", default=str(producer.DEFAULT_PARENT_TERMINAL)
    )
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(producer.l5_producer.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(producer.l5_producer.DEFAULT_LATTICE_BITSETS)
    )
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-work-items", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,600]")
    if not 1 <= args.max_work_items <= HARD_MAX_ITEMS:
        raise ValueError("max-work-items outside [1,1000]")
    policy = producer.legacy_l6.resource_policy(
        enforce=args.mode == "audit"
    )
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
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
