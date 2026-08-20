#!/usr/bin/env python3
"""Version-2 fast-resume runner for the exact no-new-x-line L6 orbit.

Version 1 deliberately rechecked the full 3D legality of every stored selected
word on every resume.  That is exact but quadratic across invocations and, by
rank 3,500, consumed most of the 600-second chunk allowance before new work
began.  This runner migrates one precisely pinned v1 checkpoint to schema v2.

Migration verifies the v1 checker, external checkpoint file, internal payload,
static state, record stream, and prefix commitments.  Records are copied
without semantic or canonical-byte changes.  The v2 fast-resume path rebuilds
the point store from anchors and cached selected words and rechecks, for every
stored word, schedule identity, cache ordinal and bytes, endpoint, global
``(y,z)`` freshness, point-set commitment, occupancy commitment, and complete
prefix-state commitment.  It does not repeatedly redo old reference-legality
or first-survivor scans.  Those facts were checked when each transition was
created and remain subject to the mandatory resumable terminal audit.

New transitions are unchanged: they scan from domain ordinal one and require
both ``word_legal_fast`` and reference ``gate_run.word_legal`` plus globally
fresh, mutually distinct ``(y,z)`` fibres.  ``--full-resume-revalidation``
retains the v1 all-selected-word legality replay as an optional diagnostic.

The checker enforces the same one-thread/nice and 600-second/1,000-item caps as
v1, pins its own source at process start/end, and writes atomic checkpoints at
least every 100 completed items.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import os
import resource
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import no_new_x_line_l6_continuation as v1  # noqa: E402


DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_V1_CHECKPOINT = Path("/tmp/no-new-x-line-L6-checkpoint.json")
DEFAULT_V2_CHECKPOINT = Path("/tmp/no-new-x-line-L6-checkpoint-v2.json")
DEFAULT_OUTPUT = Path("/tmp/no-new-x-line-L6-certificate-v2.json")

V1_CHECKER_SHA256 = (
    "eb5281e08a04ba78285b083341fbaa36eea6e05f3bdbaa352394794d0cbfdee5"
)
V1_CHECKPOINT_FILE_SHA256 = (
    "573685ff70c2027e765cfb76790024309ed27e9dece9d268c420516bffaea847"
)
V1_CHECKPOINT_PAYLOAD_SHA256 = (
    "b0f8947828f2664ddded94be2508b89795b639ac52056717ebb533ed8e81a466"
)
V1_STATIC_STATE_SHA256 = (
    "ad59ad492d0c33117a6a75a3e7d5f0aa5fdb46b2610bba16d61d353d1743e809"
)
V1_PREFIX_STATE_SHA256 = (
    "5f0535cff0613e49854475ace9c307fa5c9d0918293d7bf04d6e6d3f44551f0b"
)
V1_SELECTION_RECORD_STREAM_SHA256 = (
    "b1dd956d04d5a127c54b0ad53f19070f95700d2140e12a6557bd97d91991dc1e"
)
V1_RECORDS_CANONICAL_BYTES_SHA256 = (
    "b1dd956d04d5a127c54b0ad53f19070f95700d2140e12a6557bd97d91991dc1e"
)
V1_RECORD_COUNT = 3_500
V1_PLACED_POINTS = 18_210
SCHEMA_VERSION = 2
CHECKPOINT_INTERVAL = 100
HARD_MAX_SECONDS = 600
HARD_MAX_ITEMS = 1_000
PROCESS_START_CHECKER_SHA256 = v1.file_sha256(Path(__file__).resolve())


def assert_checker_unchanged():
    observed = v1.file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError(
            "v2 continuation checker changed during this process",
            PROCESS_START_CHECKER_SHA256,
            observed,
        )


def canonical_bytes_sha(value):
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def atomic_json_dump(payload, path):
    assert_checker_unchanged()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".no-new-x-line-L6-v2-", suffix=".json"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
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


def seal_checkpoint(checkpoint):
    payload = copy.deepcopy(checkpoint)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = v1.stable_hash(payload)
    return payload


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def verify_v1_source_and_checkpoint(path):
    source_digest = v1.file_sha256(Path(v1.__file__).resolve())
    if source_digest != V1_CHECKER_SHA256:
        raise AssertionError("v1 checker drift", source_digest)
    path = Path(path)
    file_digest = v1.file_sha256(path)
    if file_digest != V1_CHECKPOINT_FILE_SHA256:
        raise AssertionError("v1 checkpoint file drift", file_digest)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != V1_CHECKPOINT_PAYLOAD_SHA256:
        raise AssertionError("v1 checkpoint pinned payload drift", internal)
    if internal != v1.stable_hash(checkpoint):
        raise AssertionError("v1 checkpoint internal commitment failure")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != 1:
        raise AssertionError("v1 checkpoint schema drift")
    if checkpoint["static"]["continuation_checker_sha256"] != V1_CHECKER_SHA256:
        raise AssertionError("v1 checkpoint checker/static mismatch")
    if checkpoint["static"]["static_state_sha256"] != V1_STATIC_STATE_SHA256:
        raise AssertionError("v1 checkpoint static-state drift")
    if checkpoint["next_construction_rank"] != V1_RECORD_COUNT:
        raise AssertionError("v1 checkpoint record-count drift")
    if checkpoint["prefix"]["prefix_state_sha256"] != V1_PREFIX_STATE_SHA256:
        raise AssertionError("v1 checkpoint prefix-state drift")
    if checkpoint["prefix"][
        "selection_record_stream_sha256"
    ] != V1_SELECTION_RECORD_STREAM_SHA256:
        raise AssertionError("v1 checkpoint selection-record drift")
    if canonical_bytes_sha(
        checkpoint["selection_records"]
    ) != V1_RECORDS_CANONICAL_BYTES_SHA256:
        raise AssertionError("v1 checkpoint canonical record-byte drift")
    if checkpoint["prefix"]["placed_point_count"] != V1_PLACED_POINTS:
        raise AssertionError("v1 checkpoint placed-point drift")
    return checkpoint


def build_v2_static(l6_v1):
    static = copy.deepcopy(l6_v1["static"])
    if static["continuation_checker_sha256"] != V1_CHECKER_SHA256:
        raise AssertionError("replayed v1 static checker mismatch")
    if static["static_state_sha256"] != V1_STATIC_STATE_SHA256:
        raise AssertionError("replayed v1 static-state mismatch")
    static.pop("static_state_sha256")
    static["continuation_checker_sha256"] = PROCESS_START_CHECKER_SHA256
    static["checkpoint_schema_version"] = SCHEMA_VERSION
    static["migration_origin"] = {
        "v1_checker_sha256": V1_CHECKER_SHA256,
        "v1_checkpoint_file_sha256": V1_CHECKPOINT_FILE_SHA256,
        "v1_checkpoint_payload_sha256": V1_CHECKPOINT_PAYLOAD_SHA256,
        "v1_static_state_sha256": V1_STATIC_STATE_SHA256,
        "v1_prefix_state_sha256": V1_PREFIX_STATE_SHA256,
        "v1_selection_record_stream_sha256": (
            V1_SELECTION_RECORD_STREAM_SHA256
        ),
        "v1_record_count": V1_RECORD_COUNT,
    }
    static["static_state_sha256"] = v1.stable_hash(static)
    result = dict(l6_v1)
    result["static"] = static
    return result


def load_context(args, deadline):
    observed, metadata, blocks = v1.verify_frozen_inputs(
        args.metadata, args.cache
    )
    d24, d24_commitment = v1.load_d24_priority()
    handle = Path(args.cache).open("rb")
    cache = None
    try:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        if cache[:len(v1.CACHE_MAGIC)] != v1.CACHE_MAGIC:
            raise AssertionError("compact cache magic drift")
        l5 = v1.replay_frozen_l5(cache, blocks, deadline=deadline)
        l6_v1 = v1.build_l6_static(l5, d24, d24_commitment)
        l6 = build_v2_static(l6_v1)
    except BaseException:
        if cache is not None:
            cache.close()
        handle.close()
        raise
    return {
        "observed": observed,
        "metadata": metadata,
        "blocks": blocks,
        "d24": d24,
        "d24_commitment": d24_commitment,
        "handle": handle,
        "cache": cache,
        "l6_v1": l6_v1,
        "l6": l6,
    }


def close_context(context):
    context["cache"].close()
    context["handle"].close()


def quick_reconstruct(cache, blocks, l6, checkpoint, deadline=None):
    anchors = l6["anchors"]
    parent_word = l6["parent_word"]
    schedule = l6["schedule"]
    store = v1.Store(anchors)
    yz_counts = Counter((point[1], point[2]) for point in anchors)
    records = checkpoint["selection_records"]
    for rank, record in enumerate(records):
        if (
            deadline is not None
            and rank % CHECKPOINT_INTERVAL == 0
            and time.monotonic() >= deadline
        ):
            raise v1.DeadlineReached
        gap = schedule[rank]
        step = parent_word[gap]
        if record["construction_rank"] != rank:
            raise AssertionError("v2 record rank drift")
        if record["gap"] != gap or record["step"] != step:
            raise AssertionError("v2 record schedule/step drift")
        block = blocks[step]
        if record["domain_words"] != block["words"]:
            raise AssertionError("v2 record domain-size drift")
        word = v1.cached_word(
            cache, block, record["first_survivor_ordinal_1_based"]
        )
        if list(word) != record["selected_word"]:
            raise AssertionError("v2 record cached bytes drift")
        interiors = v1.word_interiors(anchors[gap], word)
        if not v1.projection_clean(interiors, yz_counts):
            raise AssertionError("v2 stored word projection drift", rank)
        if v1.endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("v2 stored word endpoint drift", rank)
        v1.apply_selected(interiors, store, yz_counts)
    observed_prefix = v1.prefix_commitment(
        store, yz_counts, records, len(records)
    )
    if observed_prefix != checkpoint["prefix"]:
        raise AssertionError("v2 quick-resume prefix commitment mismatch")
    doubled = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if doubled != l6["initial_double_fibres"]:
        raise AssertionError("v2 quick-resume doubled-fibre drift")
    return store, yz_counts


def full_reconstruct(cache, blocks, l6, checkpoint, deadline=None):
    # v1's routine depends only on records/prefix and the supplied L6 geometry;
    # it does not inspect the checkpoint schema or static record.
    return v1.reconstruct_l6_prefix(
        cache, blocks, l6, checkpoint, deadline=deadline
    )[:2]


def refresh_checkpoint(checkpoint, store, yz_counts):
    records = checkpoint["selection_records"]
    checkpoint["next_construction_rank"] = len(records)
    checkpoint["generation_first_survivor_scanned_through_rank"] = len(records)
    checkpoint["prefix"] = v1.prefix_commitment(
        store, yz_counts, records, len(records)
    )
    if checkpoint.get("status") == "hard-jam":
        return
    if checkpoint["audit"]["terminal_audit_complete"]:
        checkpoint["status"] = "complete"
    elif len(records) == checkpoint["static"]["gaps"]:
        checkpoint["status"] = "construction-complete-audit-pending"
    else:
        checkpoint["status"] = "partial"


def validate_v2_checkpoint(checkpoint, expected_static):
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != v1.stable_hash(checkpoint):
        raise AssertionError("v2 checkpoint payload commitment mismatch")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION:
        raise AssertionError("v2 checkpoint schema drift")
    if checkpoint["static"] != expected_static:
        raise AssertionError("v2 checkpoint static-state mismatch")
    if len(checkpoint["selection_records"]) != checkpoint[
        "next_construction_rank"
    ]:
        raise AssertionError("v2 checkpoint record/rank mismatch")
    if checkpoint["next_construction_rank"] < V1_RECORD_COUNT:
        raise AssertionError("v2 checkpoint precedes its migration origin")
    if checkpoint[
        "generation_first_survivor_scanned_through_rank"
    ] != checkpoint["next_construction_rank"]:
        raise AssertionError("v2 generation scan cursor drift")
    migration = checkpoint["migration"]
    expected_migration_fields = {
        "v1_checker_sha256": V1_CHECKER_SHA256,
        "v1_checkpoint_file_sha256": V1_CHECKPOINT_FILE_SHA256,
        "v1_checkpoint_payload_sha256": V1_CHECKPOINT_PAYLOAD_SHA256,
        "v1_static_state_sha256": V1_STATIC_STATE_SHA256,
        "v1_prefix_state_sha256": V1_PREFIX_STATE_SHA256,
        "v1_selection_record_stream_sha256": (
            V1_SELECTION_RECORD_STREAM_SHA256
        ),
        "v1_record_count": V1_RECORD_COUNT,
        "records_canonical_bytes_sha256": (
            V1_RECORDS_CANONICAL_BYTES_SHA256
        ),
        "prefix_copied_unchanged": True,
        "quick_state_reconstruction_passed": True,
        "repeated_old_legality_deferred_to_terminal_audit": True,
    }
    for key, expected in expected_migration_fields.items():
        if migration.get(key) != expected:
            raise AssertionError("v2 migration commitment drift", key)
    migrated_prefix = checkpoint["selection_records"][:V1_RECORD_COUNT]
    if canonical_bytes_sha(
        migrated_prefix
    ) != V1_RECORDS_CANONICAL_BYTES_SHA256:
        raise AssertionError("v2 migrated canonical record bytes changed")
    if v1.stable_hash(migrated_prefix) != V1_SELECTION_RECORD_STREAM_SHA256:
        raise AssertionError("v2 migrated record stream changed")
    records = checkpoint["selection_records"]
    prefix = checkpoint["prefix"]
    if prefix["next_construction_rank"] != len(records):
        raise AssertionError("v2 prefix/rank mismatch")
    if prefix["selection_record_stream_sha256"] != v1.stable_hash(records):
        raise AssertionError("v2 prefix/record-stream mismatch")
    audit = checkpoint["audit"]
    cursor = audit["first_survivor_audited_through_rank"]
    if not 0 <= cursor <= len(records):
        raise AssertionError("v2 first-survivor audit cursor drift")
    verifier = audit["ordered_verifier_next_point"]
    total = audit["ordered_verifier_total_points"]
    if verifier < 0 or (total is not None and not 0 <= verifier <= total):
        raise AssertionError("v2 ordered-verifier cursor drift")
    if verifier > 0 and cursor != len(records):
        raise AssertionError("v2 ordered verifier advanced before firstness")
    if audit["terminal_audit_complete"] and (
        total is None or verifier != total or cursor != len(records)
    ):
        raise AssertionError("v2 terminal-audit flag/cursor mismatch")
    return checkpoint


def load_v2_checkpoint(path, expected_static):
    with Path(path).open() as handle:
        checkpoint = json.load(handle)
    return validate_v2_checkpoint(checkpoint, expected_static)


def migrate(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    source = verify_v1_source_and_checkpoint(args.v1_checkpoint)
    context = load_context(args, deadline)
    try:
        # This also verifies that the pinned checkpoint static record agrees
        # with an independent frozen-L5 replay under the v1 checker.
        source_checked = v1.load_checkpoint(
            args.v1_checkpoint, context["l6_v1"]["static"]
        )
        if source_checked != source:
            raise AssertionError("v1 checkpoint dual loader disagreement")
        store, yz_counts = quick_reconstruct(
            context["cache"], context["blocks"], context["l6_v1"],
            source, deadline=deadline,
        )
        records_bytes_sha = canonical_bytes_sha(source["selection_records"])
        if records_bytes_sha != V1_RECORDS_CANONICAL_BYTES_SHA256:
            raise AssertionError("pinned v1 canonical record bytes mismatch")
        checkpoint = {
            "schema_version": SCHEMA_VERSION,
            "status": source["status"],
            "static": context["l6"]["static"],
            "next_construction_rank": source["next_construction_rank"],
            "selection_records": copy.deepcopy(source["selection_records"]),
            "generation_first_survivor_scanned_through_rank": source[
                "generation_first_survivor_scanned_through_rank"
            ],
            "resume_revalidation": (
                "schema v2 fast resume checks cached bytes, endpoint, global yz "
                "freshness, and exact prefix commitments; old reference legality "
                "and firstness are deferred to terminal audit"
            ),
            "audit": copy.deepcopy(source["audit"]),
            "prefix": copy.deepcopy(source["prefix"]),
            "migration": {
                "v1_checker_sha256": V1_CHECKER_SHA256,
                "v1_checkpoint_file_sha256": V1_CHECKPOINT_FILE_SHA256,
                "v1_checkpoint_payload_sha256": V1_CHECKPOINT_PAYLOAD_SHA256,
                "v1_static_state_sha256": V1_STATIC_STATE_SHA256,
                "v1_prefix_state_sha256": V1_PREFIX_STATE_SHA256,
                "v1_selection_record_stream_sha256": (
                    V1_SELECTION_RECORD_STREAM_SHA256
                ),
                "v1_record_count": V1_RECORD_COUNT,
                "records_canonical_bytes_sha256": records_bytes_sha,
                "prefix_copied_unchanged": True,
                "quick_state_reconstruction_passed": True,
                "repeated_old_legality_deferred_to_terminal_audit": True,
            },
            "last_run": {
                "mode": "migrate",
                "resource_policy": policy,
            },
        }
        # Exact migration assertions before writing.
        if checkpoint["selection_records"] != source["selection_records"]:
            raise AssertionError("migration changed a record")
        if canonical_bytes_sha(checkpoint["selection_records"]) != records_bytes_sha:
            raise AssertionError("migration changed canonical record bytes")
        if checkpoint["prefix"] != source["prefix"]:
            raise AssertionError("migration changed the prefix commitment")
        refresh_checkpoint(checkpoint, store, yz_counts)
        if checkpoint["prefix"] != source["prefix"]:
            raise AssertionError("reconstructed v2 prefix differs from v1")
        save_checkpoint(args.checkpoint, checkpoint)

        # Read-after-write migration self-test.
        reread = load_v2_checkpoint(args.checkpoint, context["l6"]["static"])
        if reread["selection_records"] != source["selection_records"]:
            raise AssertionError("migration readback record mismatch")
        if reread["prefix"] != source["prefix"]:
            raise AssertionError("migration readback prefix mismatch")
        quick_reconstruct(
            context["cache"], context["blocks"], context["l6"], reread,
            deadline=deadline,
        )
        return {
            "mode": "migrate",
            "records": len(reread["selection_records"]),
            "prefix_state_sha256": reread["prefix"]["prefix_state_sha256"],
            "records_canonical_bytes_sha256": records_bytes_sha,
            "migration_self_test_passed": True,
        }
    finally:
        close_context(context)


def run_chunk(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = load_context(args, deadline)
    try:
        checkpoint = load_v2_checkpoint(
            args.checkpoint, context["l6"]["static"]
        )
        if args.full_resume_revalidation:
            store, yz_counts = full_reconstruct(
                context["cache"], context["blocks"], context["l6"],
                checkpoint, deadline=deadline,
            )
            resume_mode = "full-selected-word-legality-revalidation"
        else:
            store, yz_counts = quick_reconstruct(
                context["cache"], context["blocks"], context["l6"],
                checkpoint, deadline=deadline,
            )
            resume_mode = "committed-fast-resume"
        if checkpoint.get("status") == "hard-jam":
            return {
                "mode": "run",
                "new_gaps": 0,
                "stop_reason": "previously-certified-exact-hard-jam",
                "obstruction": checkpoint.get("obstruction"),
            }
        added = 0
        stop_reason = "chunk-limit"
        while checkpoint["next_construction_rank"] < context["l6"]["static"][
            "gaps"
        ]:
            if added >= args.max_new_gaps:
                break
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            gap = context["l6"]["schedule"][rank]
            step = context["l6"]["parent_word"][gap]
            try:
                record, interiors = v1.select_first(
                    context["cache"], context["blocks"][step], rank, gap, step,
                    context["l6"]["anchors"][gap],
                    context["l6"]["anchors"][gap + 1],
                    store, yz_counts, deadline=deadline,
                )
            except v1.DeadlineReached:
                stop_reason = "time-limit-during-domain-scan"
                break
            except v1.NoSurvivor as failure:
                checkpoint["status"] = "hard-jam"
                checkpoint["obstruction"] = failure.details
                stop_reason = "exact-hard-jam"
                break
            checkpoint["selection_records"].append(record)
            v1.apply_selected(interiors, store, yz_counts)
            checkpoint["next_construction_rank"] += 1
            added += 1
            if added % CHECKPOINT_INTERVAL == 0:
                refresh_checkpoint(checkpoint, store, yz_counts)
                save_checkpoint(args.checkpoint, checkpoint)
        refresh_checkpoint(checkpoint, store, yz_counts)
        if checkpoint["next_construction_rank"] == context["l6"]["static"][
            "gaps"
        ]:
            stop_reason = "construction-complete"
        checkpoint["last_run"] = {
            "mode": "run",
            "new_gaps": added,
            "stop_reason": stop_reason,
            "resume_mode": resume_mode,
            "resource_policy": policy,
        }
        save_checkpoint(args.checkpoint, checkpoint)
        return {
            "mode": "run",
            "resume_mode": resume_mode,
            "new_gaps": added,
            "next_construction_rank": checkpoint["next_construction_rank"],
            "total_gaps": context["l6"]["static"]["gaps"],
            "stop_reason": stop_reason,
        }
    finally:
        close_context(context)


def ordered_chain(l6, records):
    return v1.ordered_chain(l6, records)


def audit_chunk(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = load_context(args, deadline)
    try:
        checkpoint = load_v2_checkpoint(
            args.checkpoint, context["l6"]["static"]
        )
        if checkpoint["next_construction_rank"] != context["l6"]["static"][
            "gaps"
        ]:
            raise RuntimeError("audit requires construction-complete checkpoint")
        store = v1.Store(context["l6"]["anchors"])
        yz_counts = Counter(
            (point[1], point[2]) for point in context["l6"]["anchors"]
        )
        cursor = checkpoint["audit"]["first_survivor_audited_through_rank"]
        records = checkpoint["selection_records"]
        # Previously audited transitions need only committed quick replay.
        for rank in range(cursor):
            if rank % CHECKPOINT_INTERVAL == 0 and time.monotonic() >= deadline:
                raise v1.DeadlineReached
            record = records[rank]
            gap = context["l6"]["schedule"][rank]
            step = context["l6"]["parent_word"][gap]
            word = v1.cached_word(
                context["cache"], context["blocks"][step],
                record["first_survivor_ordinal_1_based"],
            )
            interiors = v1.word_interiors(context["l6"]["anchors"][gap], word)
            if list(word) != record["selected_word"]:
                raise AssertionError("audited v2 record byte drift")
            if not v1.projection_clean(interiors, yz_counts):
                raise AssertionError("audited v2 projection drift")
            if v1.endpoint(context["l6"]["anchors"][gap], word) != context[
                "l6"
            ]["anchors"][gap + 1]:
                raise AssertionError("audited v2 endpoint drift")
            v1.apply_selected(interiors, store, yz_counts)
        work = 0
        stop_reason = "work-limit"
        while cursor < len(records) and work < args.max_work_items:
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            stored = records[cursor]
            gap = context["l6"]["schedule"][cursor]
            step = context["l6"]["parent_word"][gap]
            try:
                observed, interiors = v1.select_first(
                    context["cache"], context["blocks"][step], cursor, gap,
                    step, context["l6"]["anchors"][gap],
                    context["l6"]["anchors"][gap + 1], store, yz_counts,
                    deadline=deadline,
                )
            except v1.DeadlineReached:
                stop_reason = "time-limit-during-domain-scan"
                break
            if observed != stored:
                raise AssertionError("v2 terminal firstness audit mismatch", cursor)
            v1.apply_selected(interiors, store, yz_counts)
            cursor += 1
            work += 1
            checkpoint["audit"]["first_survivor_audited_through_rank"] = cursor
            if work % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.checkpoint, checkpoint)
        if cursor == len(records):
            chain, flat_word, selected = ordered_chain(context["l6"], records)
            checkpoint["audit"]["ordered_verifier_total_points"] = len(chain)
            verifier = checkpoint["audit"]["ordered_verifier_next_point"]
            remaining = args.max_work_items - work
            if remaining > 0 and time.monotonic() < deadline:
                verifier = v1.verify_point_range(
                    chain, verifier, remaining, deadline
                )
                checkpoint["audit"]["ordered_verifier_next_point"] = verifier
            if verifier == len(chain):
                checkpoint["audit"]["terminal_audit_complete"] = True
                checkpoint["status"] = "complete"
                stop_reason = "terminal-audit-complete"
                atomic_json_dump(
                    terminal_payload(
                        policy, checkpoint, context["l6"], chain,
                        flat_word, selected,
                    ),
                    args.output,
                )
            elif stop_reason not in {
                "time-limit", "time-limit-during-domain-scan"
            }:
                stop_reason = "ordered-verifier-partial"
        checkpoint["last_run"] = {
            "mode": "audit",
            "work_items": work,
            "stop_reason": stop_reason,
            "resource_policy": policy,
        }
        save_checkpoint(args.checkpoint, checkpoint)
        return {
            "mode": "audit",
            "first_survivor_audited_through_rank": checkpoint["audit"][
                "first_survivor_audited_through_rank"
            ],
            "ordered_verifier_next_point": checkpoint["audit"][
                "ordered_verifier_next_point"
            ],
            "terminal_audit_complete": checkpoint["audit"][
                "terminal_audit_complete"
            ],
            "stop_reason": stop_reason,
        }
    finally:
        close_context(context)


def terminal_payload(policy, checkpoint, l6, chain, flat_word, selected):
    yz_counts = Counter((point[1], point[2]) for point in chain)
    doubled = {lateral for lateral, count in yz_counts.items() if count == 2}
    if doubled != l6["initial_double_fibres"]:
        raise AssertionError("v2 terminal doubled-fibre drift")
    records = checkpoint["selection_records"]
    return {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": "exact finite certificate",
        "checker": {
            "path": "design/no_new_x_line_l6_continuation_v2.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
        },
        "resource_policy": policy,
        "migration": copy.deepcopy(checkpoint["migration"]),
        "static": l6["static"],
        "result": {
            "construction_completed": True,
            "first_survivor_audit_completed": True,
            "independent_ordered_verifier_completed": True,
            "gaps": len(records),
            "points": len(chain),
            "steps": len(flat_word),
            "initial_doubled_yz_fibres": v1.EXPECTED_DOUBLE_FIBRES,
            "final_doubled_yz_fibres": len(doubled),
            "new_doubled_yz_fibres": 0,
            "minimum_joint_survivors_certified_per_stitch": 1,
            "survivor_counts_exhaustive": False,
            "maximum_first_survivor_ordinal_1_based": max(
                record["first_survivor_ordinal_1_based"] for record in records
            ),
        },
        "commitments": {
            "selection_record_stream_sha256": v1.stable_hash(records),
            "alternate_words_by_gap_sha256": v1.word_map_sha256(selected),
            "alternate_flat_step_word_sha256": hashlib.sha256(
                bytes(flat_word)
            ).hexdigest(),
            "alternate_ordered_point_stream_sha256": v1.point_stream_sha256(
                chain
            ),
            "final_point_set_sha256": v1.stable_hash(sorted(chain)),
            "final_doubled_fibre_stream_sha256": v1.stable_hash(
                sorted(doubled)
            ),
        },
    }


def self_check(args, policy):
    if v1.file_sha256(Path(v1.__file__).resolve()) != V1_CHECKER_SHA256:
        raise AssertionError("pinned v1 checker missing")
    source = verify_v1_source_and_checkpoint(args.v1_checkpoint)
    observed, _metadata, blocks = v1.verify_frozen_inputs(
        args.metadata, args.cache
    )
    d24, d24_commitment = v1.load_d24_priority()
    checkpoint = "absent"
    if Path(args.checkpoint).exists():
        with Path(args.checkpoint).open() as handle:
            raw = json.load(handle)
        internal = raw.pop("checkpoint_payload_sha256", None)
        if internal != v1.stable_hash(raw):
            raise AssertionError("v2 self-check checkpoint commitment failure")
        checkpoint = {
            "status": raw["status"],
            "rank": raw["next_construction_rank"],
            "schema_version": raw["schema_version"],
        }
    return {
        "mode": "self-check",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "v1_checker_sha256": V1_CHECKER_SHA256,
        "frozen_inputs": observed,
        "cache_blocks": len(blocks),
        "priority_steps": len(d24),
        "priority_map_sha256": d24_commitment,
        "v1_checkpoint": {
            "file_sha256": V1_CHECKPOINT_FILE_SHA256,
            "payload_sha256": source["checkpoint_payload_sha256"],
            "records": len(source["selection_records"]),
            "records_canonical_bytes_sha256": canonical_bytes_sha(
                source["selection_records"]
            ),
            "prefix_state_sha256": source["prefix"][
                "prefix_state_sha256"
            ],
        },
        "checkpoint": checkpoint,
        "resource_policy": policy,
        "heavy_construction_run": False,
    }


def estimate(policy):
    return {
        "mode": "estimate",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "schema_version": SCHEMA_VERSION,
        "pinned_v1": {
            "checker_sha256": V1_CHECKER_SHA256,
            "checkpoint_file_sha256": V1_CHECKPOINT_FILE_SHA256,
            "checkpoint_payload_sha256": V1_CHECKPOINT_PAYLOAD_SHA256,
            "records": V1_RECORD_COUNT,
            "prefix_state_sha256": V1_PREFIX_STATE_SHA256,
        },
        "resume_modes": {
            "default": "committed fast resume",
            "optional": "--full-resume-revalidation",
            "terminal": "mandatory full firstness and ordered-chain audit",
        },
        "hard_limits": {
            "seconds": HARD_MAX_SECONDS,
            "items": HARD_MAX_ITEMS,
            "checkpoint_interval": CHECKPOINT_INTERVAL,
        },
        "resource_policy": policy,
        "heavy_construction_run": False,
    }


def bounded(value, name):
    if not 1 <= value <= HARD_MAX_ITEMS:
        raise ValueError(f"{name} must lie in [1,{HARD_MAX_ITEMS}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("estimate", "self-check", "migrate", "run", "audit")
    )
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--v1-checkpoint", default=str(DEFAULT_V1_CHECKPOINT))
    parser.add_argument("--checkpoint", default=str(DEFAULT_V2_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=int, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-new-gaps", type=int, default=1_000)
    parser.add_argument("--max-work-items", type=int, default=500)
    parser.add_argument("--full-resume-revalidation", action="store_true")
    args = parser.parse_args()
    policy = v1.resource_policy(enforce=args.mode in {"migrate", "run", "audit"})
    if args.mode == "estimate":
        assert_checker_unchanged()
        print(json.dumps(estimate(policy), sort_keys=True, indent=2))
        return
    if not 1 <= args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError(f"max-seconds must lie in [1,{HARD_MAX_SECONDS}]")
    bounded(args.max_new_gaps, "max-new-gaps")
    bounded(args.max_work_items, "max-work-items")
    try:
        if args.mode == "self-check":
            result = self_check(args, policy)
        elif args.mode == "migrate":
            if Path(args.checkpoint).exists():
                raise FileExistsError(
                    "refusing to overwrite an existing v2 checkpoint",
                    args.checkpoint,
                )
            result = migrate(args, policy)
        elif args.mode == "run":
            result = run_chunk(args, policy)
        else:
            result = audit_chunk(args, policy)
    except v1.DeadlineReached:
        result = {
            "mode": args.mode,
            "stop_reason": "time-limit-during-frozen-parent-or-state-replay",
        }
    assert_checker_unchanged()
    checkpoint_path = Path(args.checkpoint)
    result["checkpoint"] = str(checkpoint_path.resolve())
    result["checkpoint_sha256"] = (
        v1.file_sha256(checkpoint_path) if checkpoint_path.exists() else None
    )
    result["maximum_resident_set_raw"] = resource.getrusage(
        resource.RUSAGE_SELF
    ).ru_maxrss
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
