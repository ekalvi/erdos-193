#!/usr/bin/env python3
"""Independent exact audit for the consecutive guarded-L5 -> guarded-L6 run.

The constructor checkpoint is immutable input.  This checker independently
rebuilds the guarded-L5 parent transport and fragile-first schedule, rescans
every cache ordinal through each stored winner with fresh optimized/reference
legality memos, reconstructs the natural L6 walk, and finally checks every
unordered point pair.  A guarded-cone pair is accepted only when both endpoints
are transformed parent anchors; exactly 246 such inherited pairs must remain.

``census`` is a stronger optional phase.  It scans the *entire* connector
domain at every realized prefix (756,512,535 word occurrences for this parent)
and records the exact number and distribution of surviving choices.  It is
separate because firstness plus terminal geometry already certify the finite
transition, while the all-choice census is much more expensive.

No constructor rejection memo, cone witness, prefix reconstruction, endpoint
cutoff, spatial cutoff, or secant-distance cutoff is trusted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import os
import struct
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


DEFAULT_SOURCE = Path("/tmp/guarded-L5-to-L6-construction-v1.json")
DEFAULT_AUDIT_CHECKPOINT = Path("/tmp/guarded-L5-to-L6-audit-checkpoint-v1.json")
DEFAULT_OUTPUT = Path("/tmp/guarded-L5-to-L6-audit-v1.json")
DEFAULT_WALK_OUTPUT = Path("/tmp/guarded-L5-to-L6-walk-v1.txt")
DEFAULT_CENSUS_OUTPUT = Path("/tmp/guarded-L5-to-L6-survivor-census-v1.json")
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 25
HARD_MAX_SECONDS = 600.0
HARD_MAX_WORK_ITEMS = 2_000
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
CONSTRUCTOR = ROOT / "design" / "guarded_l5_to_l6.py"
PROCESS_START_CONSTRUCTOR_SHA256 = common.file_sha256(CONSTRUCTOR)
EXPECTED_LEDGER_SHA256 = (
    "1d785e4a39434511603fe6f5f13955bf9946357bf3082b1ac47528d50acb4695"
)
EXPECTED_D24_PRIORITY_SHA256 = (
    "7261f8005f86b6107cbd83fbcd150010658b6e48e464e45176e16d1a31533097"
)


class DeadlineReached(Exception):
    def __init__(self, pending=None):
        super().__init__(pending)
        self.pending = pending


def assert_checker_unchanged():
    observed = {
        "auditor": common.file_sha256(Path(__file__).resolve()),
        "common": common.file_sha256(Path(common.__file__).resolve()),
        "constructor": common.file_sha256(CONSTRUCTOR),
    }
    expected = {
        "auditor": PROCESS_START_CHECKER_SHA256,
        "common": PROCESS_START_COMMON_SHA256,
        "constructor": PROCESS_START_CONSTRUCTOR_SHA256,
    }
    if observed != expected:
        raise RuntimeError("guarded transition audit code changed during execution")


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and (
        priority >= 15
    )
    if enforce and not compliant:
        raise RuntimeError(
            "audit requires all numerical thread controls=1 and nice>=15",
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


def load_d24_priority_independent():
    path = ROOT / "gate2-ledger-L6.json"
    if common.file_sha256(path) != EXPECTED_LEDGER_SHA256:
        raise AssertionError("audit priority ledger drift")
    with path.open() as handle:
        rows = json.load(handle)
    result = {}
    for row in rows:
        step, size = row["step"], row["d24"]
        if step in result and result[step] != size:
            raise AssertionError("audit inconsistent D2--4 priority", step)
        result[step] = size
    if set(result) != set(range(common.EXPECTED_MENU_SIZE)) or common.stable_hash(
        sorted(result.items())
    ) != EXPECTED_D24_PRIORITY_SHA256:
        raise AssertionError("audit D2--4 priority coverage/digest drift")
    return result


def verify_source(path, expected_sha256):
    path = Path(path)
    observed = common.file_sha256(path)
    if observed != expected_sha256:
        raise AssertionError("guarded transition source file drift", observed)
    with path.open() as handle:
        source = common.unseal(
            json.load(handle), "checkpoint_payload_sha256"
        )
    if source.get("schema_version") != SCHEMA_VERSION or source.get(
        "status"
    ) != "construction-complete-audit-pending" or source.get(
        "pending_scan"
    ) is not None or source.get("obstruction") is not None:
        raise AssertionError("guarded transition source is not audit-ready")
    return source, {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": observed,
        "payload_sha256": source["checkpoint_payload_sha256"],
    }


def open_context(args):
    parent, parent_points, parent_word, parent_snapshot = (
        common.load_canonical_parent(args.parent)
    )
    _metadata, blocks = common.load_metadata(args.metadata)
    common.verify_cache(args.cache)
    action_handle, actions, action_records = common.load_action_bitsets(
        args.action_bitsets, blocks
    )
    cache_handle = Path(args.cache).open("rb")
    cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
    try:
        source, source_snapshot = verify_source(
            args.source, args.expected_source_sha256
        )
        anchors = tuple(apply(M_BAL3, point) for point in parent_points)
        d24 = load_d24_priority_independent()
        schedule = tuple(sorted(
            range(len(parent_word)),
            key=lambda gap: (d24[parent_word[gap]], gap),
        ))
        if len(anchors) != common.EXPECTED_PARENT_POINTS or len(parent_word) != (
            common.EXPECTED_PARENT_STEPS
        ) or len(schedule) != len(parent_word):
            raise AssertionError("audit guarded-L6 extent drift")
        static = source.get("static", {})
        static_copy = copy.deepcopy(static)
        internal_static = static_copy.pop("static_state_sha256", None)
        if internal_static != common.stable_hash(static_copy):
            raise AssertionError("constructor static-state payload drift")
        required_static = {
            "repository_base_commit": common.REPOSITORY_BASE_COMMIT,
            "checker_sha256": PROCESS_START_CONSTRUCTOR_SHA256,
            "canonical_guarded_L5_parent": parent_snapshot,
            "level": 6,
            "gaps": len(parent_word),
            "anchors": len(anchors),
            "parent_flat_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
            "anchor_point_stream_sha256": common.point_stream_sha256(anchors),
            "anchor_point_set_sha256": common.stable_hash(sorted(anchors)),
            "schedule_sha256": common.stable_hash(schedule),
            "d24_priority_sha256": EXPECTED_D24_PRIORITY_SHA256,
            "terminal_independent_audit_required": True,
        }
        for key, expected in required_static.items():
            if static.get(key) != expected:
                raise AssertionError("constructor static policy drift", key)
        connector_domain = static.get("connector_domain", {})
        if connector_domain != {
            "cache_sha256": common.EXPECTED_CACHE_SHA256,
            "words": common.EXPECTED_EFFECTIVE_WORDS,
            "word_slots": common.EXPECTED_WORD_SLOTS,
            "steps": common.EXPECTED_MENU_SIZE,
            "selection_order": "compact-cache ordinal order",
        } or static.get("action_filter") != {
            "channel": "zero-envelope",
            "bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
        } or static.get("stitch_order") != (
            "D2--4 fragile-first, then ordered gap index"
        ) or static.get("dependency_sha256", {}).get(
            "guarded_l5_l6_common.py"
        ) != PROCESS_START_COMMON_SHA256:
            raise AssertionError("constructor domain/action/dependency policy drift")
        guard = static.get("guard", {})
        if guard.get("spectra") != [label for label, _a, _b in common.SPECTRA] or (
            guard.get("grandfathered_anchor_anchor_pairs")
            != common.EXPECTED_PARENT_PROMOTED_CONE_PAIRS
        ) or guard.get("new_pair_classes_rejected") != [
            "old-new-anchor", "old-new-connector", "same-word-new-new"
        ] or guard.get("distance_cutoff") is not None or guard.get(
            "endpoint_cutoff"
        ) is not None:
            raise AssertionError("constructor guarded-spectrum scope drift")
        records = source.get("selection_records")
        if len(records) != len(parent_word) or source.get(
            "next_construction_rank"
        ) != len(parent_word):
            raise AssertionError("constructor selection extent drift")
        return {
            "parent": parent,
            "parent_snapshot": parent_snapshot,
            "parent_points": parent_points,
            "parent_word": tuple(parent_word),
            "anchors": anchors,
            "schedule": schedule,
            "blocks": blocks,
            "cache_handle": cache_handle,
            "cache": cache,
            "action_handle": action_handle,
            "actions": actions,
            "action_records": action_records,
            "source": source,
            "source_snapshot": source_snapshot,
        }
    except BaseException:
        cache.close()
        cache_handle.close()
        actions.close()
        action_handle.close()
        raise


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


def projection_test_independent(interiors, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts:
            return False, "local-poison:occupied-yz-fibre"
        if fibre in local:
            return False, "local-poison:same-word-yz-fibre"
        local.add(fibre)
    return True, None


def cone_birth_independent(interiors, store, anchor_count):
    for later_slot, point in enumerate(interiors):
        for earlier_id, prior in enumerate(store.pts):
            matches = common.cone_matches(common.subtract(point, prior))
            if matches:
                classification = (
                    "old-new-anchor"
                    if earlier_id < anchor_count
                    else "old-new-connector"
                )
                return classification, matches[0]
        for earlier_slot in range(later_slot):
            prior = interiors[earlier_slot]
            matches = common.cone_matches(common.subtract(point, prior))
            if matches:
                return "same-word-new-new", matches[0]
    return None


def apply_selected_independent(interiors, store, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts or fibre in local:
            raise AssertionError("audit selected connector repeats a yz fibre")
        local.add(fibre)
    for point in interiors:
        yz_counts[point[1:]] += 1
    store.add_many(interiors)


def selected_geometry(context, rank, record):
    gap = context["schedule"][rank]
    step = context["parent_word"][gap]
    if (record.get("construction_rank"), record.get("gap"), record.get("step")) != (
        rank, gap, step
    ):
        raise AssertionError("audit source schedule identity drift", rank)
    block = context["blocks"][step]
    ordinal = record["first_survivor_ordinal_1_based"]
    if not 1 <= ordinal <= block["words"]:
        raise AssertionError("audit selected ordinal outside domain", rank)
    word = common.decode_word(
        context["cache"], block, record["cache_record_offset"]
    )
    if list(word) != record["selected_word"] or hashlib.sha256(
        bytes(word)
    ).hexdigest() != record["selected_word_sha256"]:
        raise AssertionError("audit selected cache word drift", rank)
    start = context["anchors"][gap]
    target = context["anchors"][gap + 1]
    if rescue.endpoint(start, word) != target:
        raise AssertionError("audit selected endpoint drift", rank)
    interiors = tuple(rescue.word_interiors(start, word))
    return gap, step, block, ordinal, word, start, target, interiors


def prefix_commitment_independent(store, yz_counts, records, rank):
    fields = {
        "next_construction_rank": rank,
        "selection_record_stream_sha256": common.stable_hash(records[:rank]),
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


def reconstruct_prefix(context, rank):
    store = rescue.Store(context["anchors"])
    yz_counts = Counter(point[1:] for point in context["anchors"])
    records = context["source"]["selection_records"]
    for cursor in range(rank):
        _gap, _step, _block, ordinal, word, _start, _target, interiors = (
            selected_geometry(context, cursor, records[cursor])
        )
        if not common.action_accepts(
            context["actions"], context["action_records"][_step], "zero", ordinal
        ):
            raise AssertionError("audit selected action bit drift", cursor)
        clean, _category = projection_test_independent(interiors, yz_counts)
        if not clean:
            raise AssertionError("audit selected projection drift", cursor)
        apply_selected_independent(interiors, store, yz_counts)
    expected = prefix_commitment_independent(store, yz_counts, records, rank)
    if rank == len(records) and expected != context["source"]["prefix"]:
        raise AssertionError("audit terminal source prefix drift")
    return store, yz_counts, expected


def empty_firstness_scan(rank, gap, step, block, ordinal, action_count):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "selected_ordinal_1_based": ordinal,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "action_incompatible_skipped": 0,
        "action_compatible_seen": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "cone_birth_rejected": 0,
        "rejection_counts": {},
        "rejection_chain_sha256": EMPTY_CHAIN_SHA256,
    }


def validate_firstness_scan(scan, rank, gap, step, block, selected_ordinal):
    if (
        scan["construction_rank"], scan["gap"], scan["step"],
        scan["selected_ordinal_1_based"],
    ) != (rank, gap, step, selected_ordinal):
        raise AssertionError("audit pending firstness identity drift")
    ordinal = scan["next_ordinal_1_based"]
    if not 1 <= ordinal <= selected_ordinal or not block["start"] <= scan[
        "next_cache_cursor"
    ] < block["end"]:
        raise AssertionError("audit pending firstness cursor drift")
    scanned = ordinal - 1
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scanned or scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != scan["action_compatible_seen"] or scan[
        "exact_legality_rejected"
    ] + scan["cone_birth_rejected"] != scan[
        "projection_clean_exact_tested"
    ] or sum(scan["rejection_counts"].values()) != scanned:
        raise AssertionError("audit pending firstness partition drift")


def record_rejection(scan, ordinal, category):
    scan["rejection_counts"][category] = scan["rejection_counts"].get(
        category, 0
    ) + 1
    scan["rejection_chain_sha256"] = chain_digest(
        scan["rejection_chain_sha256"],
        {"ordinal_1_based": ordinal, "category": category},
    )


def audit_one_firstness(context, rank, store, yz_counts, pending, deadline):
    source_record = context["source"]["selection_records"][rank]
    gap, step, block, selected_ordinal, selected_word, start, target, _interiors = (
        selected_geometry(context, rank, source_record)
    )
    action = context["action_records"][step]
    scan = copy.deepcopy(pending) if pending is not None else empty_firstness_scan(
        rank,
        gap,
        step,
        block,
        selected_ordinal,
        action["zero"]["set_bits"],
    )
    validate_firstness_scan(
        scan, rank, gap, step, block, selected_ordinal
    )
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    reference_memo = {}
    while ordinal <= selected_ordinal:
        if ordinal % 128 == 1 and time.monotonic() >= deadline:
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("audit connector cache boundary drift", rank, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        if not common.action_accepts(
            context["actions"], action, "zero", ordinal
        ):
            scan["action_incompatible_skipped"] += 1
            record_rejection(scan, ordinal, "zero-envelope-incompatible")
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        interiors = tuple(rescue.word_interiors(start, word))
        projection_clean, category = projection_test_independent(
            interiors, yz_counts
        )
        if not projection_clean:
            scan["projection_rejected"] += 1
            record_rejection(scan, ordinal, category)
            ordinal += 1
            continue
        scan["projection_clean_exact_tested"] += 1
        fast = rescue.word_legal_fast(
            start, word, store, fast_memo, rescue.MENU
        )
        reference = rescue.word_legal(
            start, word, store.pts, store.pset, reference_memo
        )
        if fast != reference:
            raise AssertionError(
                "audit fast/reference legality disagreement", rank, ordinal
            )
        if not reference:
            scan["exact_legality_rejected"] += 1
            record_rejection(scan, ordinal, "exact-global-legality")
            ordinal += 1
            continue
        cone = cone_birth_independent(interiors, store, len(context["anchors"]))
        if cone is not None:
            scan["cone_birth_rejected"] += 1
            category = "guard-cone:{}:{}".format(*cone)
            record_rejection(scan, ordinal, category)
            ordinal += 1
            continue
        if ordinal != selected_ordinal:
            raise AssertionError(
                "audit found an earlier guarded-L6 survivor",
                rank,
                ordinal,
                selected_ordinal,
                list(word),
            )
        if word != selected_word or offset != source_record[
            "cache_record_offset"
        ]:
            raise AssertionError("audit stored winner/cache order drift", rank)
        expected_counters = {
            "domain_words_scanned": ordinal,
            "action_incompatible_skipped": scan[
                "action_incompatible_skipped"
            ],
            "action_compatible_seen": scan["action_compatible_seen"],
            "projection_rejected": scan["projection_rejected"],
            "projection_clean_exact_tested": scan[
                "projection_clean_exact_tested"
            ],
            "exact_legality_rejected": scan["exact_legality_rejected"],
            "cone_birth_rejected": scan["cone_birth_rejected"],
        }
        if source_record.get("scan_counters_before_selection") != expected_counters or (
            source_record.get("rejection_counts_before_selection")
            != scan["rejection_counts"]
        ) or source_record.get(
            "rejection_chain_sha256_before_selection"
        ) != scan["rejection_chain_sha256"]:
            raise AssertionError("audit constructor rejection record drift", rank)
        audit_record = {
            "construction_rank": rank,
            "gap": gap,
            "step": step,
            "selected_ordinal_1_based": ordinal,
            "selected_word_sha256": hashlib.sha256(bytes(word)).hexdigest(),
            "ordinals_rescanned": ordinal,
            "rejection_counts": dict(sorted(scan["rejection_counts"].items())),
            "rejection_chain_sha256": scan["rejection_chain_sha256"],
            "fast_reference_agreement_for_every_exact_test": True,
            "earlier_survivors": 0,
            "selected_reference_legal": True,
            "selected_cone_birth_free": True,
        }
        return audit_record, interiors
    raise AssertionError("audit stored winner is not a survivor", rank)


def natural_chain(context):
    selected = {}
    for rank, record in enumerate(context["source"]["selection_records"]):
        gap, _step, _block, _ordinal, word, _start, _target, _interiors = (
            selected_geometry(context, rank, record)
        )
        if gap in selected:
            raise AssertionError("audit selected a natural gap twice", gap)
        selected[gap] = word
    if set(selected) != set(range(len(context["parent_word"]))):
        raise AssertionError("audit selected natural gap cover drift")
    chain = [context["anchors"][0]]
    flat_word = []
    for gap in range(len(context["parent_word"])):
        word = selected[gap]
        start = context["anchors"][gap]
        if rescue.endpoint(start, word) != context["anchors"][gap + 1]:
            raise AssertionError("audit natural connector endpoint drift", gap)
        chain.extend(rescue.word_interiors(start, word))
        chain.append(context["anchors"][gap + 1])
        flat_word.extend(word)
    chain = tuple(chain)
    flat_word = tuple(flat_word)
    if len(chain) != len(flat_word) + 1 or len(chain) != len(set(chain)):
        raise AssertionError("audit natural chain extent/repetition failure")
    store, yz_counts, terminal_prefix = reconstruct_prefix(
        context, len(context["source"]["selection_records"])
    )
    if set(chain) != store.pset:
        raise AssertionError("audit natural/construction point-set disagreement")
    natural_yz = Counter(point[1:] for point in chain)
    if natural_yz != yz_counts:
        raise AssertionError("audit natural/construction yz disagreement")
    return chain, flat_word, selected, natural_yz, terminal_prefix


def write_walk(points, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as handle:
        for point in points:
            handle.write("{} {} {}\n".format(*point))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": common.file_sha256(path),
        "format": "one exact integer x y z point per line, natural walk order",
    }


def initial_checkpoint(context):
    static = {
        "schema_version": SCHEMA_VERSION,
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "common_checker_sha256": PROCESS_START_COMMON_SHA256,
        "constructor_checker_sha256": PROCESS_START_CONSTRUCTOR_SHA256,
        "source_checkpoint": context["source_snapshot"],
        "canonical_parent": context["parent_snapshot"],
        "metadata_sha256": common.EXPECTED_METADATA_SHA256,
        "cache_sha256": common.EXPECTED_CACHE_SHA256,
        "action_bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
        "firstness_policy": (
            "zero-envelope AND global empty-yz AND exact fast/reference "
            "full-prefix legality AND no new pair in either guarded cone"
        ),
        "pair_scan_order": "natural later point, then every earlier point",
        "distance_cutoff": None,
        "endpoint_cutoff": None,
    }
    static["static_state_sha256"] = common.stable_hash(static)
    checkpoint = {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "firstness_audited_through_rank": 0,
        "audit_records": [],
        "audit_record_stream_sha256": common.stable_hash([]),
        "pending_firstness_scan": None,
        "audited_prefix": prefix_commitment_independent(
            rescue.Store(context["anchors"]),
            Counter(point[1:] for point in context["anchors"]),
            context["source"]["selection_records"],
            0,
        ),
        "ordered_verifier": {
            "next_point": 0,
            "total_points": None,
            "pair_checks": 0,
            "target_cone_pair_matches": 0,
            "target_cone_pair_counts_by_spectrum": {},
            "natural_point_stream_sha256": None,
            "natural_point_set_sha256": None,
            "flat_word_sha256": None,
            "final_yz_sha256": None,
            "final_double_fibre_sha256": None,
            "complete": False,
        },
        "terminal_output": None,
        "walk_output": None,
        "survivor_census": {
            "status": "not-started",
            "next_rank": 0,
            "records": [],
            "record_stream_sha256": common.stable_hash([]),
            "pending_scan": None,
            "output": None,
        },
    }
    return common.seal(checkpoint, "checkpoint_payload_sha256")


def save_checkpoint(path, checkpoint):
    assert_checker_unchanged()
    sealed = common.seal(checkpoint, "checkpoint_payload_sha256")
    common.atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def load_checkpoint(path, context):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(context)
    with path.open() as handle:
        checkpoint = common.unseal(
            json.load(handle), "checkpoint_payload_sha256"
        )
    fresh = initial_checkpoint(context)
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != fresh["static"]:
        raise AssertionError("audit checkpoint static drift")
    cursor = checkpoint["firstness_audited_through_rank"]
    if not 0 <= cursor <= len(context["source"]["selection_records"]) or len(
        checkpoint["audit_records"]
    ) != cursor or checkpoint["audit_record_stream_sha256"] != common.stable_hash(
        checkpoint["audit_records"]
    ):
        raise AssertionError("audit firstness cursor/record drift")
    pending = checkpoint["pending_firstness_scan"]
    if pending is not None and pending["construction_rank"] != cursor:
        raise AssertionError("audit pending firstness/rank drift")
    verifier = checkpoint["ordered_verifier"]
    if verifier["next_point"] and cursor != len(context["source"]["selection_records"]):
        raise AssertionError("audit ordered scan preceded firstness")
    expected_pairs = verifier["next_point"] * (verifier["next_point"] - 1) // 2
    if verifier["pair_checks"] != expected_pairs:
        raise AssertionError("audit ordered pair cursor drift")
    census = checkpoint["survivor_census"]
    if census["next_rank"] != len(census["records"]) or census[
        "record_stream_sha256"
    ] != common.stable_hash(census["records"]):
        raise AssertionError("audit survivor-census cursor drift")
    return checkpoint


def verify_one_ordered_point(chain, cursor, anchor_set):
    point = chain[cursor]
    directions = {}
    cone_counts = Counter()
    point_is_anchor = point in anchor_set
    for earlier, prior in enumerate(chain[:cursor]):
        raw = common.subtract(prior, point)
        direction = common.primitive_direction(raw)
        previous = directions.get(direction)
        if previous is not None:
            raise AssertionError(
                "terminal guarded-L6 walk contains a collinear triple",
                previous,
                earlier,
                cursor,
                [list(chain[previous]), list(prior), list(point)],
            )
        directions[direction] = earlier
        matches = common.cone_matches(raw)
        if matches:
            if not point_is_anchor or prior not in anchor_set:
                raise AssertionError(
                    "terminal guarded-L6 walk has a connector-born guarded-cone pair",
                    earlier,
                    cursor,
                    list(matches),
                )
            cone_counts.update(matches)
    return cursor, cone_counts


def aggregate_firstness(checkpoint):
    rejection_counts = Counter()
    ordinals = []
    for record in checkpoint["audit_records"]:
        ordinals.append(record["selected_ordinal_1_based"])
        rejection_counts.update(record["rejection_counts"])
    return {
        "selected_ordinal_minimum": min(ordinals),
        "selected_ordinal_maximum": max(ordinals),
        "selected_ordinal_sum": sum(ordinals),
        "selected_ordinal_distribution": {
            str(key): value for key, value in sorted(Counter(ordinals).items())
        },
        "rejections_before_selected_words_by_channel": dict(
            sorted(rejection_counts.items())
        ),
    }


def terminal_payload(context, checkpoint, chain, flat_word, natural_yz, walk):
    verifier = checkpoint["ordered_verifier"]
    firstness = aggregate_firstness(checkpoint)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "exact independent finite certificate for the consecutive guarded-L5 -> guarded-L6 transition",
        "repository_base_commit": common.REPOSITORY_BASE_COMMIT,
        "checker": {
            "path": "design/audit_guarded_l5_to_l6.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_audit": True,
        },
        "constructor": {
            "path": "design/guarded_l5_to_l6.py",
            "sha256": PROCESS_START_CONSTRUCTOR_SHA256,
        },
        "common": {
            "path": "design/guarded_l5_l6_common.py",
            "sha256": PROCESS_START_COMMON_SHA256,
        },
        "source_checkpoint": context["source_snapshot"],
        "canonical_guarded_L5_parent": context["parent_snapshot"],
        "deterministic_inputs": {
            "metadata_sha256": common.EXPECTED_METADATA_SHA256,
            "cache_sha256": common.EXPECTED_CACHE_SHA256,
            "action_bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
        },
        "result": {
            "construction_completed": True,
            "gaps": len(context["parent_word"]),
            "anchors": len(context["anchors"]),
            "points": len(chain),
            "steps": len(flat_word),
            "first_survivor_audit_completed": True,
            "fast_reference_agreement_verified_for_every_exact_test_through_winners": True,
            "selected_reference_legality_verified_at_every_stitch": True,
            "global_empty_yz_verified_at_every_stitch": True,
            "no_repeated_points": True,
            "independent_ordered_no_three_collinear_verified": True,
            "ordered_pair_checks": verifier["pair_checks"],
            "inherited_guarded_cone_pairs": verifier[
                "target_cone_pair_matches"
            ],
            "guarded_cone_pair_counts_by_spectrum": verifier[
                "target_cone_pair_counts_by_spectrum"
            ],
            "connector_born_guarded_cone_pairs": 0,
            "survivor_census_exhaustive": checkpoint[
                "survivor_census"
            ]["status"] == "complete",
            **firstness,
        },
        "commitments": {
            "source_selection_record_stream_sha256": common.stable_hash(
                context["source"]["selection_records"]
            ),
            "audit_record_stream_sha256": checkpoint[
                "audit_record_stream_sha256"
            ],
            "natural_point_stream_sha256": common.point_stream_sha256(chain),
            "natural_point_set_sha256": common.stable_hash(sorted(chain)),
            "flat_word_sha256": hashlib.sha256(bytes(flat_word)).hexdigest(),
            "final_yz_occupancy_sha256": common.stable_hash(
                sorted(natural_yz.items())
            ),
            "final_double_fibre_sha256": common.stable_hash(sorted(
                fibre for fibre, count in natural_yz.items() if count == 2
            )),
            "walk_artifact": walk,
        },
        "successor_invariant": {
            "same_guarded_spectra": [
                label for label, _a, _b in common.SPECTRA
            ],
            "only_inherited_anchor_anchor_pairs_in_guarded_spectra": True,
            "inherited_pair_count": common.EXPECTED_PARENT_PROMOTED_CONE_PAIRS,
            "global_empty_yz_for_every_connector_interior": True,
            "all_selected_words_zero_envelope": True,
            "M_projective_invariance_identity": (
                "Q(-3z,3y-z)=9Q(y,z) and (3r)^2=9r^2"
            ),
            "sufficient_to_initialize_the_same_guarded_L7_selector": True,
        },
        "proved": [
            "this one pinned guarded-L5 parent has a legal guarded-L6 first-survivor transition at every stitch",
            "the resulting natural L6 walk has no repeated point and no collinear triple",
            "the resulting L6 state has exactly the same two-cone no-new-pair invariant needed to initialize guarded L7",
        ],
        "not_proved": [
            "that every reachable guarded state has a successor",
            "control of projective directions outside the two guarded spectra",
            "an all-level induction or unconditional infinite walk",
        ],
    }
    payload["terminal_payload_sha256"] = common.stable_hash(payload)
    return payload


def run_audit(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_context(args)
    try:
        checkpoint = load_checkpoint(args.audit_checkpoint, context)
        if checkpoint["status"] == "complete":
            return checkpoint, {
                "work_items": 0,
                "stop_reason": "terminal-audit-already-complete",
            }
        cursor = checkpoint["firstness_audited_through_rank"]
        store, yz_counts, observed_prefix = reconstruct_prefix(context, cursor)
        if observed_prefix != checkpoint["audited_prefix"]:
            raise AssertionError("audit reconstructed prefix commitment drift")
        work = 0
        stop_reason = "work-item-limit"
        total_ranks = len(context["source"]["selection_records"])
        while checkpoint["firstness_audited_through_rank"] < total_ranks:
            if work >= args.max_work_items:
                break
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            rank = checkpoint["firstness_audited_through_rank"]
            try:
                audit_record, interiors = audit_one_firstness(
                    context,
                    rank,
                    store,
                    yz_counts,
                    checkpoint["pending_firstness_scan"],
                    deadline,
                )
            except DeadlineReached as reached:
                checkpoint["pending_firstness_scan"] = reached.pending
                stop_reason = "time-limit-during-firstness-domain-scan"
                break
            checkpoint["audit_records"].append(audit_record)
            checkpoint["audit_record_stream_sha256"] = common.stable_hash(
                checkpoint["audit_records"]
            )
            apply_selected_independent(interiors, store, yz_counts)
            checkpoint["firstness_audited_through_rank"] += 1
            checkpoint["pending_firstness_scan"] = None
            checkpoint["audited_prefix"] = prefix_commitment_independent(
                store,
                yz_counts,
                context["source"]["selection_records"],
                checkpoint["firstness_audited_through_rank"],
            )
            work += 1
            if work % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.audit_checkpoint, checkpoint)
        if checkpoint["firstness_audited_through_rank"] == total_ranks:
            if checkpoint["audited_prefix"] != context["source"]["prefix"]:
                raise AssertionError("audit complete firstness prefix/source drift")
            chain, flat_word, _selected, natural_yz, _terminal_prefix = natural_chain(
                context
            )
            verifier = checkpoint["ordered_verifier"]
            expected_commitments = {
                "total_points": len(chain),
                "natural_point_stream_sha256": common.point_stream_sha256(chain),
                "natural_point_set_sha256": common.stable_hash(sorted(chain)),
                "flat_word_sha256": hashlib.sha256(bytes(flat_word)).hexdigest(),
                "final_yz_sha256": common.stable_hash(sorted(natural_yz.items())),
                "final_double_fibre_sha256": common.stable_hash(sorted(
                    fibre for fibre, count in natural_yz.items() if count == 2
                )),
            }
            for key, value in expected_commitments.items():
                if verifier[key] is not None and verifier[key] != value:
                    raise AssertionError("audit natural commitment drift", key)
                verifier[key] = value
            anchor_set = set(context["anchors"])
            while verifier["next_point"] < len(chain):
                if work >= args.max_work_items:
                    stop_reason = "ordered-verifier-work-limit"
                    break
                if time.monotonic() >= deadline:
                    stop_reason = "ordered-verifier-time-limit"
                    break
                pair_checks, cone_counts = verify_one_ordered_point(
                    chain, verifier["next_point"], anchor_set
                )
                verifier["pair_checks"] += pair_checks
                verifier["target_cone_pair_matches"] += sum(cone_counts.values())
                cumulative = Counter(
                    verifier["target_cone_pair_counts_by_spectrum"]
                )
                cumulative.update(cone_counts)
                verifier["target_cone_pair_counts_by_spectrum"] = dict(
                    sorted(cumulative.items())
                )
                verifier["next_point"] += 1
                work += 1
                if work % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(args.audit_checkpoint, checkpoint)
                    verifier = checkpoint["ordered_verifier"]
            if verifier["next_point"] == len(chain):
                expected_pairs = len(chain) * (len(chain) - 1) // 2
                if verifier["pair_checks"] != expected_pairs or verifier[
                    "target_cone_pair_matches"
                ] != common.EXPECTED_PARENT_PROMOTED_CONE_PAIRS:
                    raise AssertionError("audit terminal pair census drift")
                verifier["complete"] = True
                checkpoint["status"] = "complete"
                walk = write_walk(chain, args.walk_output)
                terminal = terminal_payload(
                    context, checkpoint, chain, flat_word, natural_yz, walk
                )
                common.atomic_json_dump(terminal, args.output)
                checkpoint["terminal_output"] = {
                    "path": str(Path(args.output).resolve()),
                    "bytes": Path(args.output).stat().st_size,
                    "sha256": common.file_sha256(args.output),
                    "payload_sha256": terminal["terminal_payload_sha256"],
                }
                checkpoint["walk_output"] = walk
                stop_reason = "terminal-audit-complete"
        save_checkpoint(args.audit_checkpoint, checkpoint)
        return checkpoint, {
            "work_items": work,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "firstness_audited_through_rank": checkpoint[
                "firstness_audited_through_rank"
            ],
            "ordered_verifier_next_point": checkpoint["ordered_verifier"][
                "next_point"
            ],
            "ordered_verifier_total_points": checkpoint["ordered_verifier"][
                "total_points"
            ],
            "ordered_pair_checks": checkpoint["ordered_verifier"]["pair_checks"],
        }
    finally:
        close_context(context)


def empty_census_scan(rank, gap, step, block):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "outcome_counts": {},
        "outcome_chain_sha256": EMPTY_CHAIN_SHA256,
        "survivors": 0,
        "first_survivor_ordinal_1_based": None,
    }


def census_record_outcome(scan, ordinal, category):
    scan["outcome_counts"][category] = scan["outcome_counts"].get(category, 0) + 1
    scan["outcome_chain_sha256"] = chain_digest(
        scan["outcome_chain_sha256"],
        {"ordinal_1_based": ordinal, "category": category},
    )
    if category == "survivor":
        scan["survivors"] += 1
        if scan["first_survivor_ordinal_1_based"] is None:
            scan["first_survivor_ordinal_1_based"] = ordinal


def census_one_domain(context, rank, store, yz_counts, pending, deadline):
    source_record = context["source"]["selection_records"][rank]
    gap, step, block, selected_ordinal, _selected_word, start, target, _interiors = (
        selected_geometry(context, rank, source_record)
    )
    action = context["action_records"][step]
    scan = copy.deepcopy(pending) if pending is not None else empty_census_scan(
        rank, gap, step, block
    )
    if (scan["construction_rank"], scan["gap"], scan["step"]) != (
        rank, gap, step
    ) or not 1 <= scan["next_ordinal_1_based"] <= block["words"] + 1:
        raise AssertionError("survivor census pending identity/cursor drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    if sum(scan["outcome_counts"].values()) != ordinal - 1:
        raise AssertionError("survivor census pending partition drift")
    fast_memo = {}
    reference_memo = {}
    while ordinal <= block["words"]:
        if ordinal % 128 == 1 and time.monotonic() >= deadline:
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("survivor census cache boundary drift", rank, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        if not common.action_accepts(
            context["actions"], action, "zero", ordinal
        ):
            category = "zero-envelope-incompatible"
        else:
            interiors = tuple(rescue.word_interiors(start, word))
            clean, category = projection_test_independent(interiors, yz_counts)
            if clean:
                fast = rescue.word_legal_fast(
                    start, word, store, fast_memo, rescue.MENU
                )
                reference = rescue.word_legal(
                    start, word, store.pts, store.pset, reference_memo
                )
                if fast != reference:
                    raise AssertionError(
                        "survivor census fast/reference disagreement", rank, ordinal
                    )
                if not reference:
                    category = "exact-global-legality"
                else:
                    if rescue.endpoint(start, word) != target:
                        raise AssertionError("survivor census endpoint drift")
                    cone = cone_birth_independent(
                        interiors, store, len(context["anchors"])
                    )
                    category = (
                        "survivor"
                        if cone is None
                        else "guard-cone:{}:{}".format(*cone)
                    )
        census_record_outcome(scan, ordinal, category)
        ordinal += 1
    scan["next_ordinal_1_based"] = ordinal
    scan["next_cache_cursor"] = cursor
    if cursor != block["end"] or sum(scan["outcome_counts"].values()) != block[
        "words"
    ] or scan["first_survivor_ordinal_1_based"] != selected_ordinal:
        raise AssertionError("survivor census complete-domain/firstness drift", rank)
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "domain_words": block["words"],
        "surviving_connector_choices": scan["survivors"],
        "first_survivor_ordinal_1_based": scan[
            "first_survivor_ordinal_1_based"
        ],
        "outcome_counts": dict(sorted(scan["outcome_counts"].items())),
        "outcome_chain_sha256": scan["outcome_chain_sha256"],
        "domain_exhaustive": True,
    }


def census_payload(context, checkpoint):
    records = checkpoint["survivor_census"]["records"]
    survivors = [record["surviving_connector_choices"] for record in records]
    outcome_counts = Counter()
    for record in records:
        outcome_counts.update(record["outcome_counts"])
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "exact exhaustive surviving-connector census on the certified consecutive guarded-L6 chronology",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_checkpoint": context["source_snapshot"],
        "scope": {
            "stitches": len(records),
            "all_domain_word_occurrences": sum(
                record["domain_words"] for record in records
            ),
            "connector_order": "all compact-cache ordinals at every realized prefix",
            "distance_cutoff": None,
            "endpoint_cutoff": None,
        },
        "result": {
            "minimum_surviving_connector_choices": min(survivors),
            "maximum_surviving_connector_choices": max(survivors),
            "sum_surviving_connector_choices": sum(survivors),
            "surviving_choice_distribution": {
                str(key): value
                for key, value in sorted(Counter(survivors).items())
            },
            "outcomes_by_channel": dict(sorted(outcome_counts.items())),
            "every_record_first_survivor_matches_constructor": True,
        },
        "commitments": {
            "record_stream_sha256": checkpoint["survivor_census"][
                "record_stream_sha256"
            ],
        },
        "records": records,
        "not_proved": [
            "availability on any alternate reachable state",
            "successor closure at L7 or beyond",
            "an all-level induction",
        ],
    }
    payload["payload_sha256"] = common.stable_hash(payload)
    return payload


def run_census(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_context(args)
    try:
        checkpoint = load_checkpoint(args.audit_checkpoint, context)
        if checkpoint["status"] != "complete":
            raise RuntimeError("survivor census is locked until terminal audit")
        census = checkpoint["survivor_census"]
        if census["status"] == "complete":
            return checkpoint, {
                "new_stitches": 0,
                "stop_reason": "survivor-census-already-complete",
            }
        rank = census["next_rank"]
        store, yz_counts, _prefix = reconstruct_prefix(context, rank)
        added = 0
        stop_reason = "work-item-limit"
        total = len(context["source"]["selection_records"])
        census["status"] = "partial"
        while rank < total:
            if added >= args.max_work_items:
                break
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            try:
                record = census_one_domain(
                    context,
                    rank,
                    store,
                    yz_counts,
                    census["pending_scan"],
                    deadline,
                )
            except DeadlineReached as reached:
                census["pending_scan"] = reached.pending
                stop_reason = "time-limit-during-complete-domain-scan"
                break
            census["records"].append(record)
            census["record_stream_sha256"] = common.stable_hash(census["records"])
            census["next_rank"] += 1
            census["pending_scan"] = None
            source_record = context["source"]["selection_records"][rank]
            _gap, _step, _block, _ordinal, _word, _start, _target, interiors = (
                selected_geometry(context, rank, source_record)
            )
            apply_selected_independent(interiors, store, yz_counts)
            rank += 1
            added += 1
            if added % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.audit_checkpoint, checkpoint)
                census = checkpoint["survivor_census"]
        if rank == total:
            census["status"] = "complete"
            payload = census_payload(context, checkpoint)
            common.atomic_json_dump(payload, args.census_output)
            census["output"] = {
                "path": str(Path(args.census_output).resolve()),
                "bytes": Path(args.census_output).stat().st_size,
                "sha256": common.file_sha256(args.census_output),
                "payload_sha256": payload["payload_sha256"],
            }
            stop_reason = "survivor-census-complete"
        save_checkpoint(args.audit_checkpoint, checkpoint)
        return checkpoint, {
            "new_stitches": added,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "next_rank": census["next_rank"],
            "total_ranks": total,
        }
    finally:
        close_context(context)


def preflight(args):
    context = open_context(args)
    try:
        all_domain = sum(
            context["blocks"][step]["words"]
            for step in context["parent_word"]
        )
        return {
            "status": "independent guarded transition audit preflight passed",
            "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
            "constructor_checker_sha256": PROCESS_START_CONSTRUCTOR_SHA256,
            "common_checker_sha256": PROCESS_START_COMMON_SHA256,
            "source_checkpoint": context["source_snapshot"],
            "canonical_parent": context["parent_snapshot"],
            "independent_inputs": {
                "metadata_sha256": common.EXPECTED_METADATA_SHA256,
                "cache_sha256": common.EXPECTED_CACHE_SHA256,
                "action_bitset_sha256": common.EXPECTED_ACTION_BITSET_SHA256,
                "priority_ledger_sha256": EXPECTED_LEDGER_SHA256,
            },
            "firstness_domain": {
                "stitches": len(context["parent_word"]),
                "each_ordinal_through_stored_winner": True,
                "fresh_fast_and_reference_memos": True,
            },
            "terminal_domain": {
                "natural_walk_all_unordered_pairs": True,
                "expected_inherited_guarded_cone_pairs": (
                    common.EXPECTED_PARENT_PROMOTED_CONE_PAIRS
                ),
                "distance_cutoff": None,
                "endpoint_cutoff": None,
            },
            "optional_complete_survivor_census": {
                "all_word_occurrences": all_domain,
                "stitches": len(context["parent_word"]),
            },
        }
    finally:
        close_context(context)


def self_check():
    if common.cone_matches((3, -1, 3)) != ("11/3",) or common.cone_matches(
        (55, 34, 18)
    ) != ("348/275",):
        raise AssertionError("audit cone classifier self-check drift")
    store = rescue.Store(((0, 0, 0),))
    if cone_birth_independent(((3, -1, 3),), store, 1) != (
        "old-new-anchor", "11/3"
    ):
        raise AssertionError("audit cone-birth self-check drift")
    try:
        verify_one_ordered_point(
            ((0, 0, 0), (1, 1, 1), (2, 2, 2)), 2, {(0, 0, 0)}
        )
    except AssertionError as error:
        if error.args[0] != "terminal guarded-L6 walk contains a collinear triple":
            raise
    else:
        raise AssertionError("audit synthetic collinearity was accepted")
    return {
        "status": "passed",
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "constructor_checker_sha256": PROCESS_START_CONSTRUCTOR_SHA256,
        "common_checker_sha256": PROCESS_START_COMMON_SHA256,
        "synthetic_cone_and_collinearity_rejections": True,
        "large_artifacts_opened": False,
    }


def add_inputs(parser):
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--parent", default=common.DEFAULT_CANONICAL_PARENT)
    parser.add_argument("--metadata", default=common.DEFAULT_METADATA)
    parser.add_argument("--cache", default=common.DEFAULT_CACHE)
    parser.add_argument("--action-bitsets", default=common.DEFAULT_ACTION_BITSETS)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("self-check")
    preflight_parser = subparsers.add_parser("preflight")
    add_inputs(preflight_parser)
    audit_parser = subparsers.add_parser("audit")
    add_inputs(audit_parser)
    audit_parser.add_argument("--audit-checkpoint", default=DEFAULT_AUDIT_CHECKPOINT)
    audit_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    audit_parser.add_argument("--walk-output", default=DEFAULT_WALK_OUTPUT)
    audit_parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    audit_parser.add_argument("--max-work-items", type=int, default=500)
    census_parser = subparsers.add_parser("census")
    add_inputs(census_parser)
    census_parser.add_argument("--audit-checkpoint", default=DEFAULT_AUDIT_CHECKPOINT)
    census_parser.add_argument("--census-output", default=DEFAULT_CENSUS_OUTPUT)
    census_parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    census_parser.add_argument("--max-work-items", type=int, default=25)
    args = parser.parse_args()
    if args.mode == "self-check":
        result = self_check()
    elif args.mode == "preflight":
        result = preflight(args)
    else:
        if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
            raise ValueError("max-seconds outside (0,600]")
        if not 1 <= args.max_work_items <= HARD_MAX_WORK_ITEMS:
            raise ValueError("max-work-items outside [1,2000]")
        policy = resource_policy(True)
        if args.mode == "audit":
            checkpoint, observation = run_audit(args, policy)
        else:
            checkpoint, observation = run_census(args, policy)
        result = {
            "status": checkpoint["status"],
            "audit_checkpoint": str(Path(args.audit_checkpoint).resolve()),
            "audit_checkpoint_sha256": common.file_sha256(args.audit_checkpoint),
            "audit_checkpoint_payload_sha256": checkpoint[
                "checkpoint_payload_sha256"
            ],
            "terminal_output": checkpoint["terminal_output"],
            "walk_output": checkpoint["walk_output"],
            "survivor_census": checkpoint["survivor_census"],
            "observation": observation,
            "resource_policy": policy,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
