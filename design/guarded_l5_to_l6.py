#!/usr/bin/env python3
"""Exact consecutive two-cone guarded-L5 -> guarded-L6 constructor.

The sole parent is the deterministic canonical form exported by
``guarded_l5_l6_common.py`` from the independently certified guarded-L5
lineage.  In particular, this program rejects the ordinary primary L5 path
used by the previously known, unrelated guarded-L6 run.

All transformed parent points are installed as L6 anchors before the first
stitch.  Gaps are then processed in the pinned D2--4 fragile-first order.  The
complete cached connector domain is scanned in ordinal order until the first
word satisfying all of the following is found:

* the exact historical zero-envelope action bit is set;
* every proper interior has a globally unused (y,z) fibre;
* exact full-prefix legality succeeds (optimized and reference checkers agree
  on every selected word);
* no old--new or same-word new--new pair has direction in J=11/3 or J=348/275.

There is no endpoint, spatial, or secant-distance cutoff.  A mid-domain cursor,
rejection partition, semantic rejection-chain digest, and prefix commitments
make the run resumable.  A hard jam is terminal and records a complete
ordinal-to-rejection-channel run-length encoding for that stitch.

The output remains a construction artifact until the separate
``audit_guarded_l5_to_l6.py`` firstness and all-pairs passes finish.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import os
import sys
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amplify_rich import M_BAL3  # noqa: E402
from design import guarded_l5_l6_common as common  # noqa: E402
from design import potential_policy_chronological_rescue as rescue  # noqa: E402
from imbricate193 import apply  # noqa: E402


DEFAULT_CHECKPOINT = Path("/tmp/guarded-L5-to-L6-construction-v1.json")
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 25
HARD_MAX_SECONDS = 600.0
HARD_MAX_NEW_STITCHES = 1_000
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
EMPTY_CHAIN_SHA256 = hashlib.sha256(b"").hexdigest()
PROCESS_START_CHECKER_SHA256 = common.file_sha256(Path(__file__).resolve())
PROCESS_START_COMMON_SHA256 = common.file_sha256(Path(common.__file__).resolve())

EXPECTED_DEPENDENCY_SHA256 = {
    "gate2-ledger-L6.json": (
        "1d785e4a39434511603fe6f5f13955bf9946357bf3082b1ac47528d50acb4695"
    ),
    "fast_legal.py": (
        "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed"
    ),
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
}
EXPECTED_D24_PRIORITY_SHA256 = (
    "7261f8005f86b6107cbd83fbcd150010658b6e48e464e45176e16d1a31533097"
)


class DeadlineReached(Exception):
    def __init__(self, pending):
        super().__init__(pending)
        self.pending = pending


class NoSurvivor(Exception):
    def __init__(self, scan):
        super().__init__(scan)
        self.scan = scan


def assert_checker_unchanged():
    if common.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ) or common.file_sha256(Path(common.__file__).resolve()) != (
        PROCESS_START_COMMON_SHA256
    ):
        raise RuntimeError("guarded L5->L6 checker changed during execution")


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and (
        priority >= 15
    )
    if enforce and not compliant:
        raise RuntimeError(
            "run requires all numerical thread controls=1 and nice>=15",
            environment,
            priority,
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": priority,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "compliant": compliant,
    }


def verify_dependencies():
    observed = {
        name: common.file_sha256(ROOT / name)
        for name in EXPECTED_DEPENDENCY_SHA256
    }
    if observed != EXPECTED_DEPENDENCY_SHA256:
        raise AssertionError(
            "guarded L5->L6 dependency drift",
            EXPECTED_DEPENDENCY_SHA256,
            observed,
        )
    return {
        **observed,
        "guarded_l5_l6_common.py": PROCESS_START_COMMON_SHA256,
    }


def load_d24_priority():
    with (ROOT / "gate2-ledger-L6.json").open() as handle:
        records = json.load(handle)
    d24 = {}
    for record in records:
        step = record["step"]
        size = record["d24"]
        if step in d24 and d24[step] != size:
            raise AssertionError("inconsistent D2--4 priority", step)
        d24[step] = size
    if set(d24) != set(range(common.EXPECTED_MENU_SIZE)):
        raise AssertionError("D2--4 priority does not cover the menu")
    digest = common.stable_hash(sorted(d24.items()))
    if digest != EXPECTED_D24_PRIORITY_SHA256:
        raise AssertionError("D2--4 priority digest drift")
    return d24, digest


def build_level(parent_points, parent_word, parent_snapshot, dependencies):
    anchors = tuple(apply(M_BAL3, point) for point in parent_points)
    if len(anchors) != common.EXPECTED_PARENT_POINTS or len(parent_word) != (
        common.EXPECTED_PARENT_STEPS
    ):
        raise AssertionError("guarded L6 parent extent drift")
    if len(anchors) != len(set(anchors)):
        raise AssertionError("singular transport or repeated L6 anchor")
    for gap, step in enumerate(parent_word):
        if not 0 <= step < common.EXPECTED_MENU_SIZE:
            raise AssertionError("parent step outside fixed menu", gap, step)
        displacement = tuple(
            anchors[gap + 1][axis] - anchors[gap][axis]
            for axis in range(3)
        )
        if displacement != apply(M_BAL3, rescue.MENU[step]):
            raise AssertionError("transported anchor gap drift", gap)
    d24, d24_sha256 = load_d24_priority()
    schedule = tuple(sorted(
        range(len(parent_word)), key=lambda gap: (d24[parent_word[gap]], gap)
    ))
    yz_counts = Counter(point[1:] for point in anchors)
    double_fibres = sorted(
        fibre for fibre, count in yz_counts.items() if count == 2
    )
    if max(yz_counts.values(), default=0) != 2 or len(double_fibres) != 31:
        raise AssertionError("transported parent yz multiplicity drift")
    static = {
        "schema_version": SCHEMA_VERSION,
        "repository_base_commit": common.REPOSITORY_BASE_COMMIT,
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "dependency_sha256": dependencies,
        "canonical_guarded_L5_parent": parent_snapshot,
        "level": 6,
        "gaps": len(parent_word),
        "anchors": len(anchors),
        "parent_flat_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
        "anchor_point_stream_sha256": common.point_stream_sha256(anchors),
        "anchor_point_set_sha256": common.stable_hash(sorted(anchors)),
        "schedule_sha256": common.stable_hash(schedule),
        "d24_priority_sha256": d24_sha256,
        "initial_yz_occupancy_sha256": common.stable_hash(
            sorted(yz_counts.items())
        ),
        "initial_doubled_fibres": len(double_fibres),
        "initial_doubled_fibre_sha256": common.stable_hash(double_fibres),
        "connector_domain": {
            "cache_sha256": common.EXPECTED_CACHE_SHA256,
            "words": common.EXPECTED_EFFECTIVE_WORDS,
            "word_slots": common.EXPECTED_WORD_SLOTS,
            "steps": common.EXPECTED_MENU_SIZE,
            "selection_order": "compact-cache ordinal order",
        },
        "action_filter": {
            "channel": "zero-envelope",
            "bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
        },
        "stitch_order": "D2--4 fragile-first, then ordered gap index",
        "guard": {
            "spectra": [label for label, _a, _b in common.SPECTRA],
            "equations": [
                "3*(3*y^2-y*z+3*z^2)-11*r^2=0",
                "275*(3*y^2-y*z+3*z^2)-348*r^2=0",
            ],
            "grandfathered_anchor_anchor_pairs": (
                common.EXPECTED_PARENT_PROMOTED_CONE_PAIRS
            ),
            "new_pair_classes_rejected": [
                "old-new-anchor",
                "old-new-connector",
                "same-word-new-new",
            ],
            "distance_cutoff": None,
            "endpoint_cutoff": None,
        },
        "policy": (
            "zero-envelope AND global empty-yz AND exact full-prefix legality "
            "AND no connector-born pair in either guarded cone"
        ),
        "terminal_independent_audit_required": True,
    }
    static["static_state_sha256"] = common.stable_hash(static)
    return {
        "anchors": anchors,
        "parent_word": tuple(parent_word),
        "schedule": schedule,
        "initial_yz_counts": yz_counts,
        "initial_double_fibres": tuple(double_fibres),
        "static": static,
    }


def open_context(args):
    dependencies = verify_dependencies()
    _parent, parent_points, parent_word, parent_snapshot = (
        common.load_canonical_parent(args.parent)
    )
    metadata, blocks = common.load_metadata(args.metadata)
    cache_snapshot = common.verify_cache(args.cache)
    action_handle, actions, action_records = common.load_action_bitsets(
        args.action_bitsets, blocks
    )
    cache_handle = Path(args.cache).open("rb")
    cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
    try:
        if cache[:8] != common.CACHE_MAGIC:
            raise AssertionError("connector cache magic drift")
        level = build_level(
            parent_points, parent_word, parent_snapshot, dependencies
        )
    except BaseException:
        cache.close()
        cache_handle.close()
        actions.close()
        action_handle.close()
        raise
    return {
        "dependencies": dependencies,
        "metadata": metadata,
        "blocks": blocks,
        "cache_snapshot": cache_snapshot,
        "cache_handle": cache_handle,
        "cache": cache,
        "action_handle": action_handle,
        "actions": actions,
        "action_records": action_records,
        "level": level,
    }


def close_context(context):
    context["cache"].close()
    context["cache_handle"].close()
    context["actions"].close()
    context["action_handle"].close()


def chain_digest(previous, value):
    payload = common.canonical_json(value)
    digest = hashlib.sha256()
    digest.update(bytes.fromhex(previous))
    digest.update(len(payload).to_bytes(8, "little"))
    digest.update(payload)
    return digest.hexdigest()


def append_reason(scan, ordinal, category):
    record = {"ordinal_1_based": ordinal, "category": category}
    scan["rejection_chain_sha256"] = chain_digest(
        scan["rejection_chain_sha256"], record
    )
    scan["rejection_counts"][category] = (
        scan["rejection_counts"].get(category, 0) + 1
    )
    ranges = scan["rejection_channel_rle"]
    if ranges and ranges[-1][2] == category and ranges[-1][1] + 1 == ordinal:
        ranges[-1][1] = ordinal
    else:
        ranges.append([ordinal, ordinal, category])


def projection_test(interiors, yz_counts):
    local = set()
    for slot, point in enumerate(interiors):
        fibre = point[1:]
        if fibre in yz_counts:
            return False, {
                "classification": "occupied-yz-fibre",
                "interior_slot": slot,
                "point": list(point),
                "fibre": list(fibre),
                "prior_multiplicity": yz_counts[fibre],
            }
        if fibre in local:
            return False, {
                "classification": "same-word-yz-fibre",
                "interior_slot": slot,
                "point": list(point),
                "fibre": list(fibre),
            }
        local.add(fibre)
    return True, None


def cone_birth(interiors, store, anchor_count):
    for later_slot, point in enumerate(interiors):
        for earlier_id, prior in enumerate(store.pts):
            raw = common.subtract(point, prior)
            matches = common.cone_matches(raw)
            if matches:
                classification = (
                    "old-new-anchor"
                    if earlier_id < anchor_count
                    else "old-new-connector"
                )
                return {
                    "classification": classification,
                    "spectrum": matches[0],
                    "matched_spectra": list(matches),
                    "later_interior_slot": later_slot,
                    "later_point": list(point),
                    "earlier_point_id": earlier_id,
                    "earlier_point": list(prior),
                    "primitive_direction": list(common.primitive_direction(raw)),
                }
        for earlier_slot in range(later_slot):
            prior = interiors[earlier_slot]
            raw = common.subtract(point, prior)
            matches = common.cone_matches(raw)
            if matches:
                return {
                    "classification": "same-word-new-new",
                    "spectrum": matches[0],
                    "matched_spectra": list(matches),
                    "later_interior_slot": later_slot,
                    "earlier_interior_slot": earlier_slot,
                    "later_point": list(point),
                    "earlier_point": list(prior),
                    "primitive_direction": list(common.primitive_direction(raw)),
                }
    return None


def empty_scan(rank, gap, step, block, action_count):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "domain_words": block["words"],
        "static_zero_envelope_words": action_count,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "domain_words_scanned": 0,
        "action_incompatible_skipped": 0,
        "action_compatible_seen": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "cone_birth_rejected": 0,
        "rejection_counts": {},
        "rejection_chain_sha256": EMPTY_CHAIN_SHA256,
        "rejection_channel_rle": [],
        "first_rejection_witness_by_channel": {},
    }


def validate_scan(scan, rank, gap, step, block, action_count):
    if (scan["construction_rank"], scan["gap"], scan["step"]) != (
        rank, gap, step
    ) or scan["domain_words"] != block["words"] or scan[
        "static_zero_envelope_words"
    ] != action_count:
        raise AssertionError("pending guarded scan identity drift")
    ordinal = scan["next_ordinal_1_based"]
    if not 1 <= ordinal <= block["words"] + 1 or scan[
        "domain_words_scanned"
    ] != ordinal - 1 or not block["start"] <= scan[
        "next_cache_cursor"
    ] <= block["end"]:
        raise AssertionError("pending guarded scan cursor drift")
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scan["domain_words_scanned"]:
        raise AssertionError("pending guarded action partition drift")
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != scan["action_compatible_seen"]:
        raise AssertionError("pending guarded projection partition drift")
    if scan["exact_legality_rejected"] + scan[
        "cone_birth_rejected"
    ] != scan["projection_clean_exact_tested"]:
        raise AssertionError("pending guarded exact/cone partition has survivor")
    if sum(scan["rejection_counts"].values()) != scan["domain_words_scanned"]:
        raise AssertionError("pending guarded rejection reason partition drift")
    covered = sum(end - start + 1 for start, end, _category in scan[
        "rejection_channel_rle"
    ])
    if covered != scan["domain_words_scanned"]:
        raise AssertionError("pending guarded rejection RLE extent drift")


def remember_witness(scan, category, ordinal, word, witness):
    if category not in scan["first_rejection_witness_by_channel"]:
        scan["first_rejection_witness_by_channel"][category] = {
            "ordinal_1_based": ordinal,
            "word": list(word),
            "witness": witness,
        }


def scan_first_survivor(
    context, rank, gap, step, start, target, store, yz_counts, pending, deadline
):
    block = context["blocks"][step]
    action = context["action_records"][step]
    scan = copy.deepcopy(pending) if pending is not None else empty_scan(
        rank, gap, step, block, action["zero"]["set_bits"]
    )
    validate_scan(
        scan, rank, gap, step, block, action["zero"]["set_bits"]
    )
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    while ordinal <= block["words"]:
        if ordinal % 128 == 1 and time.monotonic() >= deadline:
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("connector cache boundary drift", step, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1

        if not common.action_accepts(
            context["actions"], action, "zero", ordinal
        ):
            category = "zero-envelope-incompatible"
            scan["action_incompatible_skipped"] += 1
            append_reason(scan, ordinal, category)
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        interiors = tuple(rescue.word_interiors(start, word))
        projection_clean, projection_witness = projection_test(
            interiors, yz_counts
        )
        if not projection_clean:
            category = "local-poison:" + projection_witness["classification"]
            scan["projection_rejected"] += 1
            append_reason(scan, ordinal, category)
            remember_witness(
                scan, category, ordinal, word, projection_witness
            )
            ordinal += 1
            continue
        scan["projection_clean_exact_tested"] += 1
        if not rescue.word_legal_fast(
            start, word, store, fast_memo, rescue.MENU
        ):
            category = "exact-global-legality"
            scan["exact_legality_rejected"] += 1
            append_reason(scan, ordinal, category)
            if category not in scan["first_rejection_witness_by_channel"]:
                remember_witness(
                    scan,
                    category,
                    ordinal,
                    word,
                    rescue.exact_legality_rejection(interiors, store),
                )
            ordinal += 1
            continue
        if not rescue.word_legal(start, word, store.pts, store.pset, {}):
            raise AssertionError(
                "selected-candidate fast/reference legality disagreement",
                rank,
                ordinal,
            )
        if rescue.endpoint(start, word) != target:
            raise AssertionError("eligible connector endpoint drift", rank, ordinal)
        cone_witness = cone_birth(
            interiors, store, context["level"]["static"]["anchors"]
        )
        if cone_witness is not None:
            category = "guard-cone:{}:{}".format(
                cone_witness["classification"], cone_witness["spectrum"]
            )
            scan["cone_birth_rejected"] += 1
            append_reason(scan, ordinal, category)
            remember_witness(scan, category, ordinal, word, cone_witness)
            ordinal += 1
            continue

        record = {
            "construction_rank": rank,
            "gap": gap,
            "step": step,
            "domain_words": block["words"],
            "static_zero_envelope_words": action["zero"]["set_bits"],
            "first_survivor_ordinal_1_based": ordinal,
            "cache_record_offset": offset,
            "selected_word": list(word),
            "selected_word_sha256": hashlib.sha256(bytes(word)).hexdigest(),
            "selected_predicates": {
                "zero_envelope": True,
                "global_empty_yz": True,
                "fast_legal": True,
                "reference_legal": True,
                "cone_birth_free": True,
            },
            "scan_counters_before_selection": {
                "domain_words_scanned": scan["domain_words_scanned"],
                "action_incompatible_skipped": scan[
                    "action_incompatible_skipped"
                ],
                "action_compatible_seen": scan["action_compatible_seen"],
                "projection_rejected": scan["projection_rejected"],
                "projection_clean_exact_tested": scan[
                    "projection_clean_exact_tested"
                ],
                "exact_legality_rejected": scan[
                    "exact_legality_rejected"
                ],
                "cone_birth_rejected": scan["cone_birth_rejected"],
            },
            "rejection_counts_before_selection": scan["rejection_counts"],
            "rejection_chain_sha256_before_selection": scan[
                "rejection_chain_sha256"
            ],
            "first_rejection_witness_by_channel": scan[
                "first_rejection_witness_by_channel"
            ],
            "survivor_census_exhaustive": False,
            "certified_survivors": 1,
        }
        return record, interiors

    scan["next_ordinal_1_based"] = ordinal
    scan["next_cache_cursor"] = cursor
    validate_scan(
        scan, rank, gap, step, block, action["zero"]["set_bits"]
    )
    if cursor != block["end"]:
        raise AssertionError("exhausted connector domain cursor drift")
    raise NoSurvivor(scan)


def apply_interiors(interiors, store, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts or fibre in local:
            raise AssertionError("selected connector violates global yz freshness")
        local.add(fibre)
    for point in interiors:
        yz_counts[point[1:]] += 1
    store.add_many(interiors)


def prefix_commitment(store, yz_counts, records, rank):
    fields = {
        "next_construction_rank": rank,
        "selection_record_stream_sha256": common.stable_hash(records),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": common.point_stream_sha256(
            store.pts
        ),
        "point_set_sha256": common.stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": common.stable_hash(
            sorted(yz_counts.items())
        ),
        "doubled_fibre_stream_sha256": common.stable_hash(sorted(
            fibre for fibre, count in yz_counts.items() if count == 2
        )),
    }
    fields["prefix_state_sha256"] = common.stable_hash(fields)
    return fields


def initial_checkpoint(level):
    store = rescue.Store(level["anchors"])
    yz_counts = Counter(point[1:] for point in level["anchors"])
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": level["static"],
        "next_construction_rank": 0,
        "selection_records": [],
        "pending_scan": None,
        "prefix": prefix_commitment(store, yz_counts, [], 0),
        "obstruction": None,
    }
    return common.seal(result, "checkpoint_payload_sha256")


def save_checkpoint(path, checkpoint):
    assert_checker_unchanged()
    sealed = common.seal(checkpoint, "checkpoint_payload_sha256")
    common.atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def load_checkpoint(path, level):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(level)
    with path.open() as handle:
        checkpoint = common.unseal(
            json.load(handle), "checkpoint_payload_sha256"
        )
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != level["static"]:
        raise AssertionError("guarded L5->L6 checkpoint static drift")
    rank = checkpoint["next_construction_rank"]
    if rank != len(checkpoint["selection_records"]) or not 0 <= rank <= (
        level["static"]["gaps"]
    ):
        raise AssertionError("guarded L5->L6 checkpoint extent drift")
    pending = checkpoint["pending_scan"]
    if pending is not None and pending["construction_rank"] != rank:
        raise AssertionError("guarded L5->L6 pending/rank drift")
    if checkpoint["status"] == "construction-complete-audit-pending" and (
        rank != level["static"]["gaps"] or pending is not None
    ):
        raise AssertionError("premature guarded L6 completion marker")
    if checkpoint["status"] == "hard-jam" and checkpoint["obstruction"] is None:
        raise AssertionError("guarded L6 hard jam lacks obstruction")
    return checkpoint


def reconstruct_prefix(context, checkpoint):
    level = context["level"]
    store = rescue.Store(level["anchors"])
    yz_counts = Counter(point[1:] for point in level["anchors"])
    for rank, record in enumerate(checkpoint["selection_records"]):
        gap = level["schedule"][rank]
        step = level["parent_word"][gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("stored guarded-L6 schedule drift", rank)
        word = common.decode_word(
            context["cache"], context["blocks"][step], record["cache_record_offset"]
        )
        if list(word) != record["selected_word"] or not common.action_accepts(
            context["actions"], context["action_records"][step], "zero",
            record["first_survivor_ordinal_1_based"],
        ):
            raise AssertionError("stored guarded-L6 word/action drift", rank)
        start = level["anchors"][gap]
        if rescue.endpoint(start, word) != level["anchors"][gap + 1]:
            raise AssertionError("stored guarded-L6 endpoint drift", rank)
        interiors = tuple(rescue.word_interiors(start, word))
        clean, _witness = projection_test(interiors, yz_counts)
        if not clean:
            raise AssertionError("stored guarded-L6 projection drift", rank)
        apply_interiors(interiors, store, yz_counts)
    observed = prefix_commitment(
        store,
        yz_counts,
        checkpoint["selection_records"],
        checkpoint["next_construction_rank"],
    )
    if observed != checkpoint["prefix"]:
        raise AssertionError("guarded-L6 prefix commitment drift")
    doubles = tuple(sorted(
        fibre for fibre, count in yz_counts.items() if count == 2
    ))
    if doubles != level["initial_double_fibres"]:
        raise AssertionError("guarded-L6 prefix changed inherited double fibres")
    pending = checkpoint["pending_scan"]
    if pending is not None:
        rank = checkpoint["next_construction_rank"]
        gap = level["schedule"][rank]
        step = level["parent_word"][gap]
        validate_scan(
            pending,
            rank,
            gap,
            step,
            context["blocks"][step],
            context["action_records"][step]["zero"]["set_bits"],
        )
    return store, yz_counts


def preflight(args):
    context = open_context(args)
    try:
        level = context["level"]
        frequencies = Counter(level["parent_word"])
        all_domain_occurrences = sum(
            count * context["blocks"][step]["words"]
            for step, count in frequencies.items()
        )
        return {
            "status": "pinned guarded-L5 -> guarded-L6 preflight passed",
            "repository_base_commit": common.REPOSITORY_BASE_COMMIT,
            "construction_checker_sha256": PROCESS_START_CHECKER_SHA256,
            "common_checker_sha256": PROCESS_START_COMMON_SHA256,
            "canonical_parent": level["static"]["canonical_guarded_L5_parent"],
            "historical_parent_source_sha256": (
                common.EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256
            ),
            "metadata_sha256": common.EXPECTED_METADATA_SHA256,
            "cache_sha256": common.EXPECTED_CACHE_SHA256,
            "action_bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
            "connector_order": "compact-cache ordinal order",
            "domain": {
                "menu_steps": common.EXPECTED_MENU_SIZE,
                "effective_words_across_one_copy_of_each_step": (
                    common.EXPECTED_EFFECTIVE_WORDS
                ),
                "actual_L6_gaps": level["static"]["gaps"],
                "actual_all-domain_word_occurrences": all_domain_occurrences,
                "distance_cutoff": None,
                "endpoint_cutoff": None,
            },
            "schedule_sha256": level["static"]["schedule_sha256"],
            "anchor_point_stream_sha256": level["static"][
                "anchor_point_stream_sha256"
            ],
            "guard": level["static"]["guard"],
            "checkpoint_schema": {
                "schema_version": SCHEMA_VERSION,
                "sealed_payload": True,
                "mid_domain_ordinal_and_cache_cursor": True,
                "complete_rejection_channel_RLE_on_hard_jam": True,
            },
            "resulting_static_state_sha256": level["static"][
                "static_state_sha256"
            ],
        }
    finally:
        close_context(context)


def run_chunk(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_context(args)
    try:
        checkpoint = load_checkpoint(args.checkpoint, context["level"])
        store, yz_counts = reconstruct_prefix(context, checkpoint)
        if checkpoint["status"] in {
            "hard-jam", "construction-complete-audit-pending"
        }:
            return checkpoint, {
                "new_stitches": 0,
                "stop_reason": "checkpoint-already-terminal-for-construction",
            }
        level = context["level"]
        added = 0
        stop_reason = "new-stitch-limit"
        while checkpoint["next_construction_rank"] < level["static"]["gaps"]:
            if added >= args.max_new_stitches:
                break
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            gap = level["schedule"][rank]
            step = level["parent_word"][gap]
            start = level["anchors"][gap]
            target = level["anchors"][gap + 1]
            try:
                record, interiors = scan_first_survivor(
                    context,
                    rank,
                    gap,
                    step,
                    start,
                    target,
                    store,
                    yz_counts,
                    checkpoint["pending_scan"],
                    deadline,
                )
            except DeadlineReached as reached:
                checkpoint["pending_scan"] = reached.pending
                stop_reason = "time-limit-during-domain-scan"
                break
            except NoSurvivor as failure:
                checkpoint["pending_scan"] = None
                checkpoint["status"] = "hard-jam"
                checkpoint["obstruction"] = {
                    "construction_rank": rank,
                    "gap": gap,
                    "step": step,
                    "complete_candidate_domain": context["blocks"][step],
                    "rejection_partition": failure.scan,
                    "classification_note": {
                        "zero-envelope-incompatible": "static action guard",
                        "local-poison:*": "local/global yz-fibre poison",
                        "exact-global-legality": (
                            "an existing point or secant blocks the word; a "
                            "dedicated failure audit must refine this into "
                            "birth/re-entry/import channels"
                        ),
                        "guard-cone:*": "new guarded-spectrum line birth",
                    },
                }
                stop_reason = "exact-two-cone-guard-hard-jam"
                break
            checkpoint["selection_records"].append(record)
            apply_interiors(interiors, store, yz_counts)
            checkpoint["next_construction_rank"] += 1
            checkpoint["pending_scan"] = None
            checkpoint["prefix"] = prefix_commitment(
                store,
                yz_counts,
                checkpoint["selection_records"],
                checkpoint["next_construction_rank"],
            )
            added += 1
            if added % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.checkpoint, checkpoint)
        if checkpoint["next_construction_rank"] == level["static"]["gaps"]:
            checkpoint["status"] = "construction-complete-audit-pending"
            stop_reason = "construction-complete"
        checkpoint["prefix"] = prefix_commitment(
            store,
            yz_counts,
            checkpoint["selection_records"],
            checkpoint["next_construction_rank"],
        )
        save_checkpoint(args.checkpoint, checkpoint)
        return checkpoint, {
            "new_stitches": added,
            "stop_reason": stop_reason,
            "next_construction_rank": checkpoint["next_construction_rank"],
            "total_stitches": level["static"]["gaps"],
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "placed_points": checkpoint["prefix"]["placed_point_count"],
        }
    finally:
        close_context(context)


def self_check():
    if common.cone_matches((3, -1, 3)) != ("11/3",):
        raise AssertionError("constructor cone classifier drift")
    synthetic = {
        "rejection_counts": {},
        "rejection_chain_sha256": EMPTY_CHAIN_SHA256,
        "rejection_channel_rle": [],
    }
    append_reason(synthetic, 1, "a")
    append_reason(synthetic, 2, "a")
    append_reason(synthetic, 3, "b")
    if synthetic["rejection_channel_rle"] != [[1, 2, "a"], [3, 3, "b"]]:
        raise AssertionError("rejection RLE self-check drift")
    store = rescue.Store(((0, 0, 0),))
    witness = cone_birth(((3, -1, 3),), store, 1)
    if witness is None or witness["classification"] != "old-new-anchor":
        raise AssertionError("old-new cone self-check drift")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "common_sha256": PROCESS_START_COMMON_SHA256,
        "old_new_and_rejection_RLE_checked": True,
        "large_artifacts_opened": False,
    }


def add_input_arguments(parser):
    parser.add_argument("--parent", default=common.DEFAULT_CANONICAL_PARENT)
    parser.add_argument("--metadata", default=common.DEFAULT_METADATA)
    parser.add_argument("--cache", default=common.DEFAULT_CACHE)
    parser.add_argument("--action-bitsets", default=common.DEFAULT_ACTION_BITSETS)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("self-check")
    preflight_parser = subparsers.add_parser("preflight")
    add_input_arguments(preflight_parser)
    run_parser = subparsers.add_parser("run")
    add_input_arguments(run_parser)
    run_parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    run_parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    run_parser.add_argument("--max-new-stitches", type=int, default=500)
    args = parser.parse_args()
    if args.mode == "self-check":
        result = self_check()
    elif args.mode == "preflight":
        result = preflight(args)
    else:
        if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
            raise ValueError("max-seconds outside (0,600]")
        if not 1 <= args.max_new_stitches <= HARD_MAX_NEW_STITCHES:
            raise ValueError("max-new-stitches outside [1,1000]")
        policy = resource_policy(True)
        checkpoint, observation = run_chunk(args, policy)
        result = {
            "status": checkpoint["status"],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_bytes": Path(args.checkpoint).stat().st_size,
            "checkpoint_sha256": common.file_sha256(args.checkpoint),
            "checkpoint_payload_sha256": checkpoint[
                "checkpoint_payload_sha256"
            ],
            "observation": observation,
            "obstruction": checkpoint["obstruction"],
            "resource_policy": policy,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
