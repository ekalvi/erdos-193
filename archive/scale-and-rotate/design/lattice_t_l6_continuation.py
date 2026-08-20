#!/usr/bin/env python3
"""Prepared exact L6 continuation of the audited lattice-T L5 path.

The parent is the *ordered point stream* certified by the independent
``lattice_t_chronological_audit.py`` terminal artifact.  It is not the older
8,260-point no-new-x-line path, nor is the construction-order point stream in
the L5 producer checkpoint accepted as an ordered walk.  The sealed L5 source
checkpoint supplies the selected connector words; the terminal audit supplies
the independent firstness and ordered no-three-collinear certificate.

After applying ``M_BAL3`` to the 8,268 audited L5 points, this checker processes
the resulting 8,267 gaps in the exact D2--4 fragile-first order.  At every gap
it scans the compact connector domain in ordinal order and selects the first
word satisfying all three primary predicates:

* its zero-envelope (zero-T) action bit is set;
* every proper interior has a globally unused, mutually distinct (y,z) fibre;
* it is exactly legal against the complete placed prefix, according to both
  the optimized and reference legality implementations.

Mid-domain ordinal/cache cursors are sealed in the checkpoint.  Resume replay
rechecks cache bytes, action membership, endpoints, global-yz freshness, and
the complete prefix commitment, but deliberately defers old rejected-word and
reference-legality replay to ``lattice_t_l6_audit.py``.  That independent
audit is mandatory before the finite L6 result is called a certificate.

The L5 terminal-audit pins were frozen only after that audit completed.  Until
then ``run`` was fail-closed.  ``estimate`` and synthetic ``self-check`` never
open the large parent or connector artifacts.
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
from design import lattice_t_chronological_replay as l5_producer  # noqa: E402
from design import no_new_x_line_l6_continuation as legacy_l6  # noqa: E402
from imbricate193 import apply  # noqa: E402


rescue = l5_producer.rescue

DEFAULT_PARENT_SOURCE = Path(
    "/tmp/lattice-T-chronological-L5-primary.json"
)
DEFAULT_PARENT_TERMINAL = Path(
    "/tmp/lattice-T-chronological-L5-audit-v2.json"
)
DEFAULT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L6-checkpoint-v1.json"
)

EXPECTED_L5_PRODUCER_SHA256 = (
    "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
)
EXPECTED_LEGACY_L6_HELPERS_SHA256 = (
    "eb5281e08a04ba78285b083341fbaa36eea6e05f3bdbaa352394794d0cbfdee5"
)

# The completed construction checkpoint is already immutable.  It is not by
# itself accepted as proof that the ordered parent path is legal; that role is
# reserved for the still-running independent terminal audit below.
EXPECTED_PARENT_SOURCE_SHA256 = (
    "9c711e396dc75042b747a1bcacb5093aa8b4c84c316a89081b2e246bdae0c2b8"
)
EXPECTED_PARENT_SOURCE_BYTES = 5_369_433
EXPECTED_PARENT_SOURCE_PAYLOAD_SHA256 = (
    "4957ae7456b95d9d1c0033077eee136dfcda820e2ae4fdb9f1037490457dd71c"
)
EXPECTED_PARENT_SOURCE_PREFIX_SHA256 = (
    "5eb60096ccc3b0b51c17bb44bc782aa6c4106fb5dfa24c56952c5a4e914413a7"
)
EXPECTED_PARENT_SOURCE_SELECTION_SHA256 = (
    "73f8eb68b593cc268f254f30a84152b3d40887038b58f314f361fd107da066bd"
)

# Frozen only from the sealed independent L5 terminal artifact.  None of these
# commitments was promoted solely from the producer checkpoint.
EXPECTED_PARENT_AUDIT_CHECKER_SHA256 = (
    "8c616ea15a7aaae3e1d70f07415dd74641c2cf4fafa22050c873d31bb1ac64e8"
)
EXPECTED_PARENT_TERMINAL_SHA256 = (
    "144eb1d78a2a9c62be0747be50a2e135a8b8e91d5d2335e64398bf5af5146194"
)
EXPECTED_PARENT_TERMINAL_BYTES = 3_437
EXPECTED_PARENT_TERMINAL_PAYLOAD_SHA256 = (
    "832e8ce9c44f2528ffd3e39996572b3622e5d4b29ed47bfa593621d8c346528b"
)
EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256 = (
    "5da8880898a38de73b30b1570c1ac3de1c4c06b47c1da7eabc30d156e9123d08"
)
EXPECTED_PARENT_FLAT_WORD_SHA256 = (
    "1429806fba4ec5703a44516863c34776cd4aa07764c687909c7bda29ef915fa7"
)
EXPECTED_PARENT_POINT_SET_SHA256 = (
    "320ea9923f57acbf55ba6c9775b67d894b12324a8debdf0ceac85fe4147fedc4"
)
EXPECTED_PARENT_FINAL_YZ_SHA256 = (
    "a27701eccdfe87c1a393e37a7cae69ae07b22aa3502e5c0e0d53b25ae1d118a5"
)

EXPECTED_PARENT_POINTS = 8_268
EXPECTED_PARENT_STEPS = 8_267
EXPECTED_PARENT_CONSTRUCTION_GAPS = 2_457
EXPECTED_INHERITED_DOUBLE_FIBRES = 31
EXPECTED_L6_ANCHOR_STREAM_SHA256 = (
    "336b3104799b9ae46bb4332d4706152b983c097bdae1e399d1ac0979c2830a55"
)
EXPECTED_L6_SCHEDULE_SHA256 = (
    "33ff8d998bcd753d8587498d8ed99bd59e9c6d7c590602c2b0b3fde7cf351f52"
)

SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 50
HARD_MAX_SECONDS = 600.0
HARD_MAX_ITEMS = 1_000
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())


def assert_checker_unchanged():
    observed = rescue.file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError(
            "lattice-T L6 checker changed during execution",
            PROCESS_START_CHECKER_SHA256,
            observed,
        )


def dependency_hashes():
    observed = {
        "l5_producer": rescue.file_sha256(Path(l5_producer.__file__)),
        "legacy_l6_helpers": rescue.file_sha256(Path(legacy_l6.__file__)),
    }
    expected = {
        "l5_producer": EXPECTED_L5_PRODUCER_SHA256,
        "legacy_l6_helpers": EXPECTED_LEGACY_L6_HELPERS_SHA256,
    }
    if observed != expected:
        raise AssertionError("prepared L6 dependency drift", expected, observed)
    return observed


def terminal_pins():
    return {
        "audit_checker": EXPECTED_PARENT_AUDIT_CHECKER_SHA256,
        "terminal_file": EXPECTED_PARENT_TERMINAL_SHA256,
        "terminal_payload": EXPECTED_PARENT_TERMINAL_PAYLOAD_SHA256,
        "ordered_point_stream": EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256,
        "flat_word": EXPECTED_PARENT_FLAT_WORD_SHA256,
        "point_set": EXPECTED_PARENT_POINT_SET_SHA256,
        "final_yz": EXPECTED_PARENT_FINAL_YZ_SHA256,
    }


def ensure_parent_terminal_pins():
    pins = terminal_pins()
    if any(value == "PENDING" for value in pins.values()) or not (
        EXPECTED_PARENT_TERMINAL_BYTES > 0
    ):
        raise RuntimeError(
            "audited L5 parent pins are not finalized; L6 run is locked", pins
        )


def unseal_json(path, payload_field, description):
    with Path(path).open() as handle:
        value = json.load(handle)
    internal = value.pop(payload_field, None)
    observed = rescue.stable_hash(value)
    value[payload_field] = internal
    if internal != observed:
        raise AssertionError(description + " internal payload drift")
    return value, internal


def verify_parent_source(path):
    path = Path(path)
    if path.stat().st_size != EXPECTED_PARENT_SOURCE_BYTES:
        raise AssertionError("L5 source byte-size drift", path.stat().st_size)
    observed = rescue.file_sha256(path)
    if observed != EXPECTED_PARENT_SOURCE_SHA256:
        raise AssertionError("L5 source file drift", observed)
    source, internal = unseal_json(
        path, "checkpoint_payload_sha256", "L5 source"
    )
    if internal != EXPECTED_PARENT_SOURCE_PAYLOAD_SHA256:
        raise AssertionError("L5 source payload pin drift", internal)
    if source["status"] != "construction-complete-audit-pending":
        raise AssertionError("L5 source is not construction-complete")
    if source["next_construction_rank"] != (
        EXPECTED_PARENT_CONSTRUCTION_GAPS
    ) or len(source["selection_records"]) != (
        EXPECTED_PARENT_CONSTRUCTION_GAPS
    ):
        raise AssertionError("L5 source construction extent drift")
    if source["pending_scan"] is not None:
        raise AssertionError("completed L5 source retains a pending scan")
    if source["prefix"]["prefix_state_sha256"] != (
        EXPECTED_PARENT_SOURCE_PREFIX_SHA256
    ):
        raise AssertionError("L5 source prefix pin drift")
    if rescue.stable_hash(source["selection_records"]) != (
        EXPECTED_PARENT_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("L5 source selection pin drift")
    if source["static"]["checker_sha256"] != EXPECTED_L5_PRODUCER_SHA256:
        raise AssertionError("L5 source producer pin drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def verify_parent_terminal(path, source_snapshot):
    path = Path(path)
    if path.stat().st_size != EXPECTED_PARENT_TERMINAL_BYTES:
        raise AssertionError("L5 terminal byte-size drift", path.stat().st_size)
    observed = rescue.file_sha256(path)
    if observed != EXPECTED_PARENT_TERMINAL_SHA256:
        raise AssertionError("L5 terminal file drift", observed)
    terminal, internal = unseal_json(
        path, "terminal_payload_sha256", "L5 terminal"
    )
    if internal != EXPECTED_PARENT_TERMINAL_PAYLOAD_SHA256:
        raise AssertionError("L5 terminal payload pin drift", internal)
    if terminal["checker"]["sha256"] != (
        EXPECTED_PARENT_AUDIT_CHECKER_SHA256
    ):
        raise AssertionError("L5 terminal audit-checker drift")
    if terminal["source_checkpoint"] != source_snapshot:
        raise AssertionError("L5 terminal/source snapshot disagreement")
    required = (
        "construction_completed",
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "fast_reference_agreement_verified_for_every_exact_test",
        "global_empty_yz_verified_at_every_stitch",
        "final_no_new_yz_coincidence",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not terminal["result"].get(field) for field in required):
        raise AssertionError("L5 terminal certificate is incomplete")
    expected_extent = {
        "gaps": EXPECTED_PARENT_CONSTRUCTION_GAPS,
        "points": EXPECTED_PARENT_POINTS,
        "steps": EXPECTED_PARENT_STEPS,
    }
    for field, expected in expected_extent.items():
        if terminal["result"].get(field) != expected:
            raise AssertionError("L5 terminal extent drift", field)
    pinned_commitments = {
        "alternate_ordered_point_stream_sha256": (
            EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256
        ),
        "alternate_flat_step_word_sha256": (
            EXPECTED_PARENT_FLAT_WORD_SHA256
        ),
        "final_point_set_sha256": EXPECTED_PARENT_POINT_SET_SHA256,
        "final_yz_occupancy_sha256": EXPECTED_PARENT_FINAL_YZ_SHA256,
    }
    for field, expected in pinned_commitments.items():
        if terminal["commitments"].get(field) != expected:
            raise AssertionError("L5 terminal commitment drift", field)
    return terminal, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def reconstruct_ordered_parent(source, terminal):
    base_word, base_anchors, base_schedule = rescue.load_l5_state()
    if len(base_word) != EXPECTED_PARENT_CONSTRUCTION_GAPS:
        raise AssertionError("base L5 gap extent drift")
    selected = {}
    for rank, record in enumerate(source["selection_records"]):
        gap = base_schedule[rank]
        step = base_word[gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("L5 source schedule identity drift", rank)
        if gap in selected:
            raise AssertionError("L5 source selects a gap twice", gap)
        selected[gap] = tuple(record["selected_word"])
    if set(selected) != set(range(EXPECTED_PARENT_CONSTRUCTION_GAPS)):
        raise AssertionError("L5 source does not choose every ordered gap")

    chain = [base_anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_PARENT_CONSTRUCTION_GAPS):
        word = selected[gap]
        if rescue.endpoint(base_anchors[gap], word) != base_anchors[gap + 1]:
            raise AssertionError("L5 source connector endpoint drift", gap)
        chain.extend(rescue.word_interiors(base_anchors[gap], word))
        chain.append(base_anchors[gap + 1])
        flat_word.extend(word)
    chain = tuple(chain)
    flat_word = tuple(flat_word)
    if len(chain) != EXPECTED_PARENT_POINTS or len(flat_word) != (
        EXPECTED_PARENT_STEPS
    ):
        raise AssertionError("ordered audited parent extent drift")
    if len(chain) != len(set(chain)):
        raise AssertionError("ordered audited parent repeats a point")

    commitments = {
        "alternate_ordered_point_stream_sha256": (
            rescue.point_stream_sha256(chain)
        ),
        "alternate_flat_step_word_sha256": hashlib.sha256(
            bytes(flat_word)
        ).hexdigest(),
        "final_point_set_sha256": rescue.stable_hash(sorted(chain)),
    }
    for field, observed in commitments.items():
        if terminal["commitments"].get(field) != observed:
            raise AssertionError("reconstructed parent/terminal drift", field)
    if commitments["alternate_ordered_point_stream_sha256"] != (
        EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256
    ) or commitments["alternate_flat_step_word_sha256"] != (
        EXPECTED_PARENT_FLAT_WORD_SHA256
    ) or commitments["final_point_set_sha256"] != (
        EXPECTED_PARENT_POINT_SET_SHA256
    ):
        raise AssertionError("reconstructed parent misses immutable pin")
    if source["prefix"]["point_set_sha256"] != commitments[
        "final_point_set_sha256"
    ]:
        raise AssertionError("source and ordered parent point sets disagree")

    initial_yz = Counter(point[1:] for point in base_anchors)
    final_yz = Counter(point[1:] for point in chain)
    for fibre, count in final_yz.items():
        if count != initial_yz.get(fibre, 1):
            raise AssertionError("ordered parent creates a new yz coincidence")
    if rescue.stable_hash(sorted(final_yz.items())) != (
        EXPECTED_PARENT_FINAL_YZ_SHA256
    ):
        raise AssertionError("ordered parent final-yz pin drift")
    double_fibres = {
        fibre for fibre, count in final_yz.items() if count == 2
    }
    if len(double_fibres) != EXPECTED_INHERITED_DOUBLE_FIBRES or max(
        final_yz.values(), default=0
    ) != 2:
        raise AssertionError("ordered parent inherited-yz multiplicity drift")
    return {
        "points": chain,
        "word": flat_word,
        "double_fibres": double_fibres,
        "commitments": commitments,
    }


def policy_args():
    return argparse.Namespace(
        action_channel="zero",
        projection_policy="global-empty",
        require_digit_simple=False,
        survivor_certificate_target=1,
    )


def build_l6(parent, d24, d24_sha256, input_sha256, snapshots):
    parent_word = parent["word"]
    anchors = tuple(apply(M_BAL3, point) for point in parent["points"])
    if len(anchors) != EXPECTED_PARENT_POINTS or len(parent_word) != (
        EXPECTED_PARENT_STEPS
    ):
        raise AssertionError("L6 parent extent drift")
    for gap, step in enumerate(parent_word):
        displacement = tuple(
            anchors[gap + 1][axis] - anchors[gap][axis]
            for axis in range(3)
        )
        if displacement != apply(M_BAL3, rescue.MENU[step]):
            raise AssertionError("L6 anchor gap is not a scaled parent step", gap)
    schedule = tuple(sorted(
        range(len(parent_word)), key=lambda gap: (d24[parent_word[gap]], gap)
    ))
    anchor_stream_sha256 = rescue.point_stream_sha256(anchors)
    schedule_sha256 = rescue.stable_hash(schedule)
    if anchor_stream_sha256 != EXPECTED_L6_ANCHOR_STREAM_SHA256:
        raise AssertionError("pinned L6 anchor stream drift")
    if schedule_sha256 != EXPECTED_L6_SCHEDULE_SHA256:
        raise AssertionError("pinned L6 fragile schedule drift")
    yz_counts = Counter(point[1:] for point in anchors)
    double_fibres = {
        fibre for fibre, count in yz_counts.items() if count == 2
    }
    # The yz block of M_BAL3 has determinant nine and is injective over Z^2,
    # so equality of parent yz fibres is preserved exactly by scaling.
    if len(double_fibres) != EXPECTED_INHERITED_DOUBLE_FIBRES or max(
        yz_counts.values(), default=0
    ) != 2:
        raise AssertionError("scaled L6 anchor yz multiplicity drift")
    static = {
        "level": 6,
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "dependency_sha256": dependency_hashes(),
        "parent_source": snapshots["source"],
        "parent_terminal": snapshots["terminal"],
        "parent_terminal_audit_checker_sha256": (
            EXPECTED_PARENT_AUDIT_CHECKER_SHA256
        ),
        "parent_ordered_point_stream_sha256": (
            EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256
        ),
        "parent_terminal_flat_word_sha256": EXPECTED_PARENT_FLAT_WORD_SHA256,
        "artifact_sha256": input_sha256,
        "priority_ledger_sha256": legacy_l6.EXPECTED_FROZEN_INPUT_SHA256[
            "gate2-ledger-L6.json"
        ],
        "d24_priority_map_sha256": d24_sha256,
        "policy": {
            "action_channel": "zero",
            "projection_policy": "global-empty",
            "require_digit_simple": False,
            "survivor_certificate_target": 1,
            "selection_order": "compact-cache ordinal order",
            "stitch_order": "D2--4 fragile-first, then ordered gap index",
        },
        "gaps": len(parent_word),
        "anchors": len(anchors),
        "parent_flat_word_sha256": hashlib.sha256(
            bytes(parent_word)
        ).hexdigest(),
        "anchor_point_stream_sha256": anchor_stream_sha256,
        "anchor_point_set_sha256": rescue.stable_hash(sorted(anchors)),
        "schedule_sha256": schedule_sha256,
        "initial_doubled_fibres": len(double_fibres),
        "initial_doubled_fibre_stream_sha256": rescue.stable_hash(
            sorted(double_fibres)
        ),
        "terminal_audit_required": True,
    }
    static["static_state_sha256"] = rescue.stable_hash(static)
    return {
        "parent_word": parent_word,
        "anchors": anchors,
        "schedule": schedule,
        "initial_double_fibres": double_fibres,
        "static": static,
    }


def prefix_commitment(store, yz_counts, records, rank):
    fields = {
        "next_construction_rank": rank,
        "selection_record_stream_sha256": rescue.stable_hash(records),
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


def initial_checkpoint(l6):
    store = rescue.Store(l6["anchors"])
    yz_counts = Counter(point[1:] for point in l6["anchors"])
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": l6["static"],
        "next_construction_rank": 0,
        "selection_records": [],
        "pending_scan": None,
        "prefix": prefix_commitment(store, yz_counts, [], 0),
        "resume_revalidation": (
            "cache bytes, zero-T membership, endpoint, global-yz state, and "
            "prefix commitments; terminal audit replays firstness and legality"
        ),
        "last_run": None,
    }


def load_checkpoint(path, l6):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(l6)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(checkpoint):
        raise AssertionError("L6 checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION:
        raise AssertionError("L6 checkpoint schema drift")
    if checkpoint["static"] != l6["static"]:
        raise AssertionError("L6 checkpoint static-state drift")
    rank = checkpoint["next_construction_rank"]
    if rank != len(checkpoint["selection_records"]) or not (
        0 <= rank <= l6["static"]["gaps"]
    ):
        raise AssertionError("L6 checkpoint rank/record drift")
    pending = checkpoint["pending_scan"]
    if pending is not None and pending["construction_rank"] != rank:
        raise AssertionError("L6 pending scan/rank drift")
    if checkpoint["status"] == "construction-complete-audit-pending" and (
        rank != l6["static"]["gaps"] or pending is not None
    ):
        raise AssertionError("L6 completed checkpoint extent drift")
    return checkpoint


def cache_word_at_offset(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("L6 cache offset outside step block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("L6 cache record boundary drift")
    return tuple(cache[offset + 1:end])


def apply_selected(interiors, store, yz_counts):
    for point in interiors:
        fibre = point[1:]
        if yz_counts[fibre]:
            raise AssertionError("L6 selected word reuses a yz fibre")
        yz_counts[fibre] += 1
    store.add_many(interiors)


def reconstruct_prefix(context, checkpoint, deadline):
    l6 = context["l6"]
    store = rescue.Store(l6["anchors"])
    yz_counts = Counter(point[1:] for point in l6["anchors"])
    args = policy_args()
    for rank, record in enumerate(checkpoint["selection_records"]):
        if rank % CHECKPOINT_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing committed L6 prefix"
        ):
            raise l5_producer.DeadlineReached(None)
        gap = l6["schedule"][rank]
        step = l6["parent_word"][gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("L6 stored schedule identity drift", rank)
        block = context["blocks"][step]
        action_record = context["action_records"][step]
        if record["domain_words"] != block["words"] or record[
            "static_action_words"
        ] != action_record["zero"]["set_bits"]:
            raise AssertionError("L6 stored domain/action extent drift", rank)
        ordinal = record["first_survivor_ordinal_1_based"]
        if not l5_producer.action_accepts(
            context["bitset"], action_record, "zero", ordinal
        ):
            raise AssertionError("L6 stored word lost zero-T membership", rank)
        word = cache_word_at_offset(
            context["cache"], block, record["cache_record_offset"]
        )
        if list(word) != record["selected_word"]:
            raise AssertionError("L6 stored cache bytes drift", rank)
        start, target = l6["anchors"][gap], l6["anchors"][gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        if rescue.endpoint(start, word) != target:
            raise AssertionError("L6 stored connector endpoint drift", rank)
        if not l5_producer.intrinsic_projection_clean(
            start, target, interiors
        ) or not l5_producer.global_projection_clean(interiors, yz_counts):
            raise AssertionError("L6 stored global-yz drift", rank)
        if args.require_digit_simple:
            raise AssertionError("primary L6 replay unexpectedly uses digit filter")
        apply_selected(interiors, store, yz_counts)
    observed = prefix_commitment(
        store, yz_counts, checkpoint["selection_records"],
        checkpoint["next_construction_rank"],
    )
    if observed != checkpoint["prefix"]:
        raise AssertionError("L6 prefix commitment drift")
    doubles = {
        fibre for fibre, count in yz_counts.items() if count == 2
    }
    if doubles != l6["initial_double_fibres"]:
        raise AssertionError("L6 resume changed inherited double fibres")
    pending = checkpoint["pending_scan"]
    if pending is not None:
        rank = checkpoint["next_construction_rank"]
        gap = l6["schedule"][rank]
        step = l6["parent_word"][gap]
        block = context["blocks"][step]
        l5_producer.validate_pending(pending, rank, gap, step, block)
        expected_count = context["action_records"][step]["zero"]["set_bits"]
        if pending["static_action_words"] != expected_count:
            raise AssertionError("L6 pending zero-T population drift")
    return store, yz_counts


def input_args(args):
    return argparse.Namespace(
        metadata=args.metadata,
        cache=args.cache,
        lattice_result=args.lattice_result,
        lattice_bitsets=args.lattice_bitsets,
    )


def open_context(args):
    ensure_parent_terminal_pins()
    dependencies = dependency_hashes()
    input_sha256 = l5_producer.verify_inputs(input_args(args))
    _metadata, blocks = rescue.load_metadata(args.metadata)
    source, source_snapshot = verify_parent_source(args.parent_source)
    terminal, terminal_snapshot = verify_parent_terminal(
        args.parent_terminal, source_snapshot
    )
    parent = reconstruct_ordered_parent(source, terminal)
    d24, d24_sha256 = legacy_l6.load_d24_priority()
    snapshots = {"source": source_snapshot, "terminal": terminal_snapshot}
    l6 = build_l6(parent, d24, d24_sha256, input_sha256, snapshots)

    lattice_result, sidecar = l5_producer.load_lattice_result(
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
            raise AssertionError("L6 compact-cache magic drift")
        action_records = l5_producer.parse_bitsets(
            bitset, sidecar, blocks
        )
    except BaseException:
        if bitset is not None:
            bitset.close()
        if cache is not None:
            cache.close()
        bitset_handle.close()
        cache_handle.close()
        raise
    return {
        "dependencies": dependencies,
        "input_sha256": input_sha256,
        "source_snapshot": source_snapshot,
        "terminal_snapshot": terminal_snapshot,
        "lattice_result": lattice_result,
        "blocks": blocks,
        "l6": l6,
        "cache_handle": cache_handle,
        "bitset_handle": bitset_handle,
        "cache": cache,
        "bitset": bitset,
        "action_records": action_records,
    }


def close_context(context):
    context["bitset"].close()
    context["cache"].close()
    context["bitset_handle"].close()
    context["cache_handle"].close()


def run_chunk(args, resource_policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_context(args)
    try:
        checkpoint = load_checkpoint(args.checkpoint, context["l6"])
        try:
            store, yz_counts = reconstruct_prefix(
                context, checkpoint, deadline
            )
        except l5_producer.DeadlineReached:
            return checkpoint, {
                "new_gaps": 0,
                "stop_reason": "time-limit-during-prefix-reconstruction",
            }
        if checkpoint["status"] in {
            "hard-jam", "construction-complete-audit-pending"
        }:
            return checkpoint, {
                "new_gaps": 0,
                "stop_reason": "checkpoint-already-terminal-for-construction",
            }
        added = 0
        stop_reason = "new-gap-limit"
        policy = policy_args()
        while checkpoint["next_construction_rank"] < context["l6"][
            "static"
        ]["gaps"]:
            if added >= args.max_new_gaps:
                break
            if rescue.enforce_runtime(deadline, "between lattice-T L6 stitches"):
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            gap = context["l6"]["schedule"][rank]
            step = context["l6"]["parent_word"][gap]
            start = context["l6"]["anchors"][gap]
            target = context["l6"]["anchors"][gap + 1]
            try:
                record = l5_producer.select_first(
                    context["cache"], context["blocks"][step],
                    context["bitset"], context["action_records"][step],
                    rank, gap, step, start, target, store, yz_counts,
                    checkpoint["pending_scan"], policy, deadline,
                )
            except l5_producer.DeadlineReached as reached:
                checkpoint["pending_scan"] = reached.pending
                stop_reason = "time-limit-during-domain-scan"
                break
            except l5_producer.NoSurvivor as failure:
                checkpoint["pending_scan"] = None
                checkpoint["status"] = "hard-jam"
                checkpoint["obstruction"] = failure.details
                stop_reason = "exact-primary-policy-hard-jam"
                break
            word = tuple(record["selected_word"])
            interiors = tuple(rescue.word_interiors(start, word))
            checkpoint["selection_records"].append(record)
            apply_selected(interiors, store, yz_counts)
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
                    "resource_policy": resource_policy,
                }
                save_checkpoint(args.checkpoint, checkpoint)
        if checkpoint["next_construction_rank"] == context["l6"]["static"][
            "gaps"
        ]:
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
            "resource_policy": resource_policy,
        }
        save_checkpoint(args.checkpoint, checkpoint)
        return checkpoint, {
            "new_gaps": added,
            "stop_reason": stop_reason,
            "next_construction_rank": checkpoint["next_construction_rank"],
            "total_gaps": context["l6"]["static"]["gaps"],
        }
    finally:
        close_context(context)


def self_check():
    dependencies = dependency_hashes()
    producer_check = l5_producer.self_check()
    if producer_check["status"] != "passed":
        raise AssertionError("lattice-T producer synthetic checks failed")
    determinant_yz = (
        M_BAL3[1][1] * M_BAL3[2][2]
        - M_BAL3[1][2] * M_BAL3[2][1]
    )
    if determinant_yz != 9:
        raise AssertionError("M_BAL3 yz block lost injectivity")
    synthetic_word = (0, 1, 0, 2, 1)
    synthetic_d24 = {0: 4, 1: 2, 2: 2}
    schedule = tuple(sorted(
        range(len(synthetic_word)),
        key=lambda gap: (synthetic_d24[synthetic_word[gap]], gap),
    ))
    if schedule != (1, 3, 4, 0, 2):
        raise AssertionError("fragile-first schedule convention drift")
    block = {"start": 100, "end": 200, "words": 10}
    pending = l5_producer.empty_scan(0, 7, 3, block, 6)
    l5_producer.validate_pending(pending, 0, 7, 3, block)
    if EXPECTED_PARENT_POINTS - 1 != EXPECTED_PARENT_STEPS:
        raise AssertionError("parent ordered path extent is inconsistent")
    pins_finalized = not any(
        value == "PENDING" for value in terminal_pins().values()
    ) and EXPECTED_PARENT_TERMINAL_BYTES > 0
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "dependency_sha256": dependencies,
        "terminal_pins_finalized": pins_finalized,
        "heavy_run_locked_until_terminal_pins": not pins_finalized,
        "large_artifacts_opened": False,
        "expected_L6_starting_anchors": EXPECTED_PARENT_POINTS,
        "expected_L6_stitches": EXPECTED_PARENT_STEPS,
        "expected_inherited_double_yz_fibres": (
            EXPECTED_INHERITED_DOUBLE_FIBRES
        ),
        "M_BAL3_yz_determinant": determinant_yz,
        "fragile_schedule_tie_break_tested": True,
        "mid_domain_pending_scan_tested": True,
        "primary_policy": (
            "zero-T AND global empty-yz AND exact fast/reference legality"
        ),
    }


def estimate():
    pins = terminal_pins()
    pins_finalized = not any(
        value == "PENDING" for value in pins.values()
    ) and EXPECTED_PARENT_TERMINAL_BYTES > 0
    return {
        "status": "prepared and pinned; construction has not been launched",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "expected_L6_starting_anchors": EXPECTED_PARENT_POINTS,
        "expected_L6_stitches": EXPECTED_PARENT_STEPS,
        "possible_L6_ordered_point_range": [
            2 * EXPECTED_PARENT_STEPS + 1,
            5 * EXPECTED_PARENT_STEPS + 1,
        ],
        "expected_inherited_double_yz_fibres": (
            EXPECTED_INHERITED_DOUBLE_FIBRES
        ),
        "parent": (
            "terminal-audited 8,268-point lattice-T L5 ordered stream"
        ),
        "primary_policy": (
            "zero-envelope AND global empty-yz AND exact legality"
        ),
        "schedule": "actual D2--4 fragile-first order, stable by gap index",
        "resumable_mid_domain_ordinal_scans": True,
        "terminal_audit": "separate mandatory lattice_t_l6_audit.py phase",
        "terminal_pins": pins,
        "terminal_pins_finalized": pins_finalized,
        "heavy_run_locked": not pins_finalized,
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_seconds_per_chunk": HARD_MAX_SECONDS,
        "maximum_new_stitches_per_chunk": HARD_MAX_ITEMS,
        "large_artifacts_opened": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "run"))
    parser.add_argument("--parent-source", default=str(DEFAULT_PARENT_SOURCE))
    parser.add_argument(
        "--parent-terminal", default=str(DEFAULT_PARENT_TERMINAL)
    )
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(l5_producer.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(l5_producer.DEFAULT_LATTICE_BITSETS)
    )
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-new-gaps", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,600]")
    if not 1 <= args.max_new_gaps <= HARD_MAX_ITEMS:
        raise ValueError("max-new-gaps outside [1,1000]")
    resource_policy = legacy_l6.resource_policy(enforce=args.mode == "run")
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    else:
        checkpoint, observation = run_chunk(args, resource_policy)
        result = {
            "status": checkpoint["status"],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": rescue.file_sha256(args.checkpoint),
            "observation": observation,
            "obstruction": checkpoint.get("obstruction"),
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
