#!/usr/bin/env python3
"""Resumable exact L6 continuation of the frozen no-new-x-line L5 orbit.

The parent walk is not accepted as an opaque file.  Every invocation replays
the deterministic L5 selector from the pinned compact domain cache and asserts
all frozen word, point, schedule, selection-record, and doubled-fibre
commitments.  The resulting 8,260 points are mapped by ``M_BAL3`` to the L6
anchors.  The all-124-step D2--4 priority map is recovered from the pinned L6
ledger, and the L6 gaps are processed in exact fragile-first order.

At every new L6 stitch, the selected word is the first effective-domain word
whose interior points

* are exactly legal against the alternate prefix, according to both
  ``word_legal_fast`` and the slower reference ``gate_run.word_legal``; and
* have globally fresh and mutually distinct ``(y,z)`` coordinates.

The latter condition prevents every new x-parallel secant birth.  The 31
doubled fibres already inherited from L4 remain and are required to remain the
same set throughout L6.

Checkpoint semantics
--------------------

Every resume reconstructs the exact point store from anchors and stored words,
rechecks each stored word's cache ordinal, endpoint, global projection
freshness, fast legality, and reference legality, and recomputes a prefix-state
commitment.  It does *not* repeatedly rescan all candidates rejected before an
old stored word.  New transitions always scan from domain ordinal one.

``audit`` performs the deferred proof pass: it replays every rejected candidate
once to certify all first-survivor ordinals, then advances a resumable
point-by-point implementation of the independent ordered-chain direction test.
Only after both audit cursors reach the end is a terminal certificate written.

The run and audit modes enforce one-thread environment variables, nice >= 15,
at most 1,000 new work items, and at most 600 wall seconds per invocation.
Checkpoints are atomic and are refreshed at least every 100 completed items.

Examples, from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/no_new_x_line_l6_continuation.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/no_new_x_line_l6_continuation.py run \
        --max-new-gaps 500 --max-seconds 600

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/no_new_x_line_l6_continuation.py audit \
        --max-work-items 500 --max-seconds 600
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import pickle
import resource
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amplify_rich import M_BAL3  # noqa: E402
from design.no_new_x_line_constructor import (  # noqa: E402
    CACHE_MAGIC,
    file_sha256,
    iter_block_words,
    point_stream_sha256,
    stable_hash,
    word_map_sha256,
)
from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, word_interiors, word_legal  # noqa: E402
from imbricate193 import apply  # noqa: E402
from search193 import primitive_direction, sub  # noqa: E402


DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_CHECKPOINT = Path("/tmp/no-new-x-line-L6-checkpoint.json")
DEFAULT_OUTPUT = Path("/tmp/no-new-x-line-L6-certificate.json")

EXPECTED_FROZEN_INPUT_SHA256 = {
    "design/no_new_x_line_constructor.py": (
        "6eca827ef7b6a4dfad57554bb89156fff79c2f495e89ba33e166aebbba21fffd"
    ),
    "design/no-new-x-line-constructor-summary.json": (
        "0c19b8176df195fd1079170a53cc27e5162a26d7eaf769c078ee6b1aa20e3681"
    ),
    "gate2-ledger-L6.json": (
        "1d785e4a39434511603fe6f5f13955bf9946357bf3082b1ac47528d50acb4695"
    ),
    "gate2-l7-construction-L5.pkl": (
        "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
    ),
    "fast_legal.py": (
        "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed"
    ),
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
}
EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_L5_COMMITMENTS = {
    "pinned_schedule_sha256": (
        "031e4dc1ed31fba2ff930036dd0b1f81bb516d3d4c98818def6d9085179b4422"
    ),
    "selection_record_stream_sha256": (
        "1979af1139a707304147d4fb3e7a9d97af46a92c4ec1a783d567ca966b79531c"
    ),
    "alternate_words_by_gap_sha256": (
        "32d5c762c15ce574c87427ee198b22e758fe4b714989cba52a9d9d54c71a02a7"
    ),
    "alternate_flat_step_word_sha256": (
        "8f94471be8be8bfe8c790470e392fa7ac40d5834db86aa5f594c0aa500e741b9"
    ),
    "alternate_ordered_point_stream_sha256": (
        "a9522b6403c869016dc77ba00646af5240b416c06a57e8434fadea519b7fb5e5"
    ),
    "final_point_set_sha256": (
        "9dfdb584080c4ed05c37578660c6ec3a7567fd09637bcc22374bc57ca34b357e"
    ),
    "inherited_doubled_fibre_stream_sha256": (
        "d697a3b3feee953fb8cc3794f7c8f7a8108c98c70bce2d29466e62f590f0fd8f"
    ),
}
EXPECTED_L5_POINTS = 8_260
EXPECTED_L5_STEPS = 8_259
EXPECTED_DOUBLE_FIBRES = 31
EXPECTED_MENU_SIZE = 124
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
CHECKPOINT_INTERVAL = 100
HARD_MAX_SECONDS = 600
HARD_MAX_ITEMS = 1_000
PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


class DeadlineReached(Exception):
    pass


class NoSurvivor(Exception):
    def __init__(self, details):
        super().__init__(details)
        self.details = details


def assert_checker_unchanged():
    observed = file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError(
            "continuation checker changed during this process",
            PROCESS_START_CHECKER_SHA256,
            observed,
        )


def atomic_json_dump(payload, path):
    assert_checker_unchanged()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".no-new-x-line-L6-", suffix=".json"
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


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and priority >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run/audit requires all thread variables=1 and nice>=15",
            environment,
            priority,
        )
    return {
        "thread_environment": environment,
        "process_nice": priority,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "compliant": compliant,
    }


def verify_frozen_inputs(metadata_path, cache_path):
    observed = {}
    for name, expected in EXPECTED_FROZEN_INPUT_SHA256.items():
        digest = file_sha256(ROOT / name)
        if digest != expected:
            raise AssertionError("frozen input drift", name, digest, expected)
        observed[name] = digest
    metadata_path = Path(metadata_path)
    cache_path = Path(cache_path)
    metadata_digest = file_sha256(metadata_path)
    if metadata_digest != EXPECTED_METADATA_SHA256:
        raise AssertionError("frozen L5 metadata drift", metadata_digest)
    if cache_path.stat().st_size != EXPECTED_CACHE_BYTES:
        raise AssertionError("compact cache byte-size drift", cache_path.stat().st_size)
    cache_digest = file_sha256(cache_path)
    if cache_digest != EXPECTED_CACHE_SHA256:
        raise AssertionError("compact cache digest drift", cache_digest)
    with metadata_path.open() as handle:
        metadata = json.load(handle)
    if metadata["compact_domain_cache"]["sha256"] != cache_digest:
        raise AssertionError("metadata/cache commitment disagreement")
    blocks = {
        block["step"]: block
        for block in metadata["compact_domain_cache"]["blocks"]
    }
    if set(blocks) != set(range(EXPECTED_MENU_SIZE)):
        raise AssertionError("compact cache block set drift")
    return observed, metadata, blocks


def load_d24_priority():
    with (ROOT / "gate2-ledger-L6.json").open() as handle:
        records = json.load(handle)
    d24 = {}
    for record in records:
        step = record["step"]
        size = record["d24"]
        if step in d24 and d24[step] != size:
            raise AssertionError("inconsistent ledger D2--4 size", step)
        d24[step] = size
    if set(d24) != set(range(EXPECTED_MENU_SIZE)):
        raise AssertionError("ledger does not cover all menu steps", sorted(d24))
    return d24, stable_hash(sorted(d24.items()))


def cached_word(cache, block, target_ordinal):
    if not 1 <= target_ordinal <= block["words"]:
        raise AssertionError("cached word ordinal outside block")
    for ordinal, word in iter_block_words(cache, block):
        if ordinal == target_ordinal:
            return word
    raise AssertionError("cached word ordinal not found")


def projection_clean(interiors, yz_counts):
    local = set()
    for point in interiors:
        lateral = (point[1], point[2])
        if lateral in yz_counts or lateral in local:
            return False
        local.add(lateral)
    return True


def endpoint(start, word):
    point = start
    for child in word:
        vector = MENU[child]
        point = (
            point[0] + vector[0],
            point[1] + vector[1],
            point[2] + vector[2],
        )
    return point


def apply_selected(interiors, store, yz_counts):
    for point in interiors:
        lateral = (point[1], point[2])
        if yz_counts[lateral] != 0:
            raise AssertionError("selected word creates doubled yz fibre", lateral)
        yz_counts[lateral] = 1
    store.add_many(interiors)


def check_selected_word(start, target, word, store, yz_counts):
    interiors = word_interiors(start, word)
    if not projection_clean(interiors, yz_counts):
        raise AssertionError("stored selected word is not projection-clean")
    if not word_legal_fast(start, word, store, {}, MENU):
        raise AssertionError("stored selected word fails fast legality")
    if not word_legal(start, word, store.pts, store.pset, {}):
        raise AssertionError("stored selected word fails reference legality")
    if endpoint(start, word) != target:
        raise AssertionError("stored selected word endpoint drift")
    return interiors


def select_first(
    cache,
    block,
    construction_rank,
    gap,
    step,
    start,
    target,
    store,
    yz_counts,
    deadline=None,
):
    memo = {}
    projection_rejected = 0
    exact_tested = 0
    for ordinal, word in iter_block_words(cache, block):
        if deadline is not None and ordinal % 128 == 0 and time.monotonic() >= deadline:
            raise DeadlineReached
        interiors = word_interiors(start, word)
        if not projection_clean(interiors, yz_counts):
            projection_rejected += 1
            continue
        exact_tested += 1
        if not word_legal_fast(start, word, store, memo, MENU):
            continue
        if not word_legal(start, word, store.pts, store.pset, {}):
            raise AssertionError(
                "fast/reference legality disagreement",
                construction_rank,
                gap,
                step,
                ordinal,
            )
        if endpoint(start, word) != target:
            raise AssertionError("selected connector endpoint drift")
        return ({
            "construction_rank": construction_rank,
            "gap": gap,
            "step": step,
            "domain_words": block["words"],
            "first_survivor_ordinal_1_based": ordinal,
            "projection_rejected_before_survivor": projection_rejected,
            "projection_clean_exact_tested_through_survivor": exact_tested,
            "selected_word": list(word),
        }, interiors)
    raise NoSurvivor({
        "construction_rank": construction_rank,
        "gap": gap,
        "step": step,
        "domain_words": block["words"],
        "projection_rejected": projection_rejected,
        "projection_clean_exact_tested": exact_tested,
    })


def replay_frozen_l5(cache, blocks, deadline=None):
    """Reproduce raw L5 words/points and assert every frozen commitment."""
    with (ROOT / "gate2-l7-construction-L5.pkl").open("rb") as handle:
        state = pickle.load(handle)
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    order = tuple(state["order"])
    if stable_hash(order) != EXPECTED_L5_COMMITMENTS["pinned_schedule_sha256"]:
        raise AssertionError("frozen L5 schedule drift")
    store = Store(anchors)
    yz_counts = Counter((point[1], point[2]) for point in anchors)
    initial_double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    selected = {}
    selection_records = []
    for construction_rank, gap in enumerate(order):
        step = parent_word[gap]
        record, interiors = select_first(
            cache,
            blocks[step],
            construction_rank,
            gap,
            step,
            anchors[gap],
            anchors[gap + 1],
            store,
            yz_counts,
            deadline=deadline,
        )
        word = tuple(record["selected_word"])
        selected[gap] = word
        selection_records.append(record)
        apply_selected(interiors, store, yz_counts)

    chain = [anchors[0]]
    flat_word = []
    for gap in range(len(parent_word)):
        word = selected[gap]
        chain.extend(word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != EXPECTED_L5_POINTS or len(flat_word) != EXPECTED_L5_STEPS:
        raise AssertionError("frozen alternate L5 size drift")
    if set(chain) != store.pset or len(chain) != len(store.pts):
        raise AssertionError("frozen alternate L5 store/path mismatch")
    final_double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if final_double_fibres != initial_double_fibres:
        raise AssertionError("frozen alternate L5 doubled-fibre drift")

    observed = {
        "pinned_schedule_sha256": stable_hash(order),
        "selection_record_stream_sha256": stable_hash(selection_records),
        "alternate_words_by_gap_sha256": word_map_sha256(selected),
        "alternate_flat_step_word_sha256": hashlib.sha256(
            bytes(flat_word)
        ).hexdigest(),
        "alternate_ordered_point_stream_sha256": point_stream_sha256(chain),
        "final_point_set_sha256": stable_hash(sorted(store.pset)),
        "inherited_doubled_fibre_stream_sha256": stable_hash(
            sorted(initial_double_fibres)
        ),
    }
    if observed != EXPECTED_L5_COMMITMENTS:
        raise AssertionError("frozen L5 commitment replay failed", observed)
    return {
        "points": tuple(chain),
        "word": tuple(flat_word),
        "commitments": observed,
        "doubled_fibres": initial_double_fibres,
    }


def build_l6_static(l5, d24, d24_commitment):
    parent_word = l5["word"]
    anchors = tuple(apply(M_BAL3, point) for point in l5["points"])
    if len(parent_word) + 1 != len(anchors):
        raise AssertionError("alternate L5 word/point mismatch")
    for gap, step in enumerate(parent_word):
        if sub(anchors[gap + 1], anchors[gap]) != apply(M_BAL3, MENU[step]):
            raise AssertionError("L6 anchor gap is not scaled parent step", gap)
    schedule = tuple(sorted(
        range(len(parent_word)), key=lambda gap: (d24[parent_word[gap]], gap)
    ))
    yz_counts = Counter((point[1], point[2]) for point in anchors)
    double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if len(double_fibres) != EXPECTED_DOUBLE_FIBRES:
        raise AssertionError("L6 inherited doubled-fibre count drift")
    if max(yz_counts.values(), default=0) != 2:
        raise AssertionError("L6 anchor fibre multiplicity exceeds two")
    static = {
        "level": 6,
        "continuation_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "frozen_L5_metadata_sha256": EXPECTED_METADATA_SHA256,
        "compact_cache_sha256": EXPECTED_CACHE_SHA256,
        "priority_ledger_sha256": EXPECTED_FROZEN_INPUT_SHA256[
            "gate2-ledger-L6.json"
        ],
        "gaps": len(parent_word),
        "anchors": len(anchors),
        "parent_flat_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
        "anchor_point_stream_sha256": point_stream_sha256(anchors),
        "anchor_point_set_sha256": stable_hash(sorted(anchors)),
        "schedule_sha256": stable_hash(schedule),
        "d24_priority_map_sha256": d24_commitment,
        "initial_doubled_fibres": len(double_fibres),
        "initial_doubled_fibre_stream_sha256": stable_hash(sorted(double_fibres)),
        "frozen_L5_commitments": l5["commitments"],
    }
    static["static_state_sha256"] = stable_hash(static)
    return {
        "parent_word": parent_word,
        "anchors": anchors,
        "schedule": schedule,
        "initial_double_fibres": double_fibres,
        "static": static,
    }


def prefix_commitment(store, yz_counts, selection_records, next_rank):
    fields = {
        "next_construction_rank": next_rank,
        "selection_record_stream_sha256": stable_hash(selection_records),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": point_stream_sha256(store.pts),
        "point_set_sha256": stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": stable_hash(sorted(yz_counts.items())),
        "doubled_fibre_stream_sha256": stable_hash(sorted(
            lateral for lateral, count in yz_counts.items() if count == 2
        )),
    }
    fields["prefix_state_sha256"] = stable_hash(fields)
    return fields


def seal_checkpoint(payload):
    payload = dict(payload)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = stable_hash(payload)
    return payload


def save_checkpoint(path, payload):
    sealed = seal_checkpoint(payload)
    atomic_json_dump(sealed, path)
    payload.clear()
    payload.update(sealed)


def load_checkpoint(path, expected_static):
    path = Path(path)
    if not path.exists():
        return {
            "schema_version": 1,
            "status": "partial",
            "static": expected_static,
            "next_construction_rank": 0,
            "selection_records": [],
            "generation_first_survivor_scanned_through_rank": 0,
            "resume_revalidation": (
                "stored selected words and exact state are rechecked; old rejected "
                "candidates are deferred to the audit cursor"
            ),
            "audit": {
                "first_survivor_audited_through_rank": 0,
                "ordered_verifier_next_point": 0,
                "ordered_verifier_total_points": None,
                "terminal_audit_complete": False,
            },
            "prefix": None,
        }
    with path.open() as handle:
        payload = json.load(handle)
    digest = payload.pop("checkpoint_payload_sha256", None)
    if digest != stable_hash(payload):
        raise AssertionError("checkpoint payload commitment mismatch")
    payload["checkpoint_payload_sha256"] = digest
    if payload["schema_version"] != 1:
        raise AssertionError("checkpoint schema drift")
    if payload["static"] != expected_static:
        raise AssertionError("checkpoint static-state mismatch")
    if payload["next_construction_rank"] != len(payload["selection_records"]):
        raise AssertionError("checkpoint rank/record count mismatch")
    audit = payload["audit"]
    if not 0 <= audit["first_survivor_audited_through_rank"] <= payload[
        "next_construction_rank"
    ]:
        raise AssertionError("checkpoint first-survivor audit cursor drift")
    if audit["ordered_verifier_next_point"] < 0:
        raise AssertionError("checkpoint ordered-verifier cursor is negative")
    if (
        audit["ordered_verifier_next_point"] > 0
        and audit["first_survivor_audited_through_rank"]
        != payload["next_construction_rank"]
    ):
        raise AssertionError(
            "ordered verifier advanced before first-survivor audit"
        )
    total_points = audit["ordered_verifier_total_points"]
    if total_points is not None and not (
        0 <= audit["ordered_verifier_next_point"] <= total_points
    ):
        raise AssertionError("checkpoint ordered-verifier extent drift")
    if audit["terminal_audit_complete"] and (
        total_points is None
        or audit["ordered_verifier_next_point"] != total_points
    ):
        raise AssertionError("terminal audit flag/cursor mismatch")
    return payload


def reconstruct_l6_prefix(cache, blocks, l6, checkpoint, deadline=None):
    anchors = l6["anchors"]
    parent_word = l6["parent_word"]
    schedule = l6["schedule"]
    store = Store(anchors)
    yz_counts = Counter((point[1], point[2]) for point in anchors)
    records = checkpoint["selection_records"]
    for construction_rank, record in enumerate(records):
        if (
            deadline is not None
            and construction_rank % CHECKPOINT_INTERVAL == 0
            and time.monotonic() >= deadline
        ):
            raise DeadlineReached
        gap = schedule[construction_rank]
        step = parent_word[gap]
        if record["construction_rank"] != construction_rank:
            raise AssertionError("checkpoint construction-rank drift")
        if record["gap"] != gap or record["step"] != step:
            raise AssertionError("checkpoint schedule/step drift")
        block = blocks[step]
        if record["domain_words"] != block["words"]:
            raise AssertionError("checkpoint domain-size drift")
        word = cached_word(
            cache, block, record["first_survivor_ordinal_1_based"]
        )
        if list(word) != record["selected_word"]:
            raise AssertionError("checkpoint cached-word drift")
        interiors = check_selected_word(
            anchors[gap], anchors[gap + 1], word, store, yz_counts
        )
        apply_selected(interiors, store, yz_counts)
    observed_prefix = prefix_commitment(
        store, yz_counts, records, len(records)
    )
    if checkpoint["prefix"] is not None and checkpoint["prefix"] != observed_prefix:
        raise AssertionError("checkpoint prefix-state commitment mismatch")
    double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if double_fibres != l6["initial_double_fibres"]:
        raise AssertionError("resume changed inherited doubled-fibre set")
    return store, yz_counts, observed_prefix


def refresh_checkpoint(checkpoint, store, yz_counts):
    records = checkpoint["selection_records"]
    checkpoint["next_construction_rank"] = len(records)
    checkpoint["generation_first_survivor_scanned_through_rank"] = len(records)
    checkpoint["prefix"] = prefix_commitment(
        store, yz_counts, records, len(records)
    )
    if checkpoint.get("status") == "hard-jam":
        return
    if checkpoint["audit"]["terminal_audit_complete"]:
        checkpoint["status"] = "complete"
        return
    if checkpoint["next_construction_rank"] == checkpoint["static"]["gaps"]:
        checkpoint["status"] = "construction-complete-audit-pending"
    else:
        checkpoint["status"] = "partial"


def run_chunk(args, policy, metadata, blocks, d24, d24_commitment):
    started = time.monotonic()
    deadline = started + args.max_seconds
    cache_path = Path(args.cache)
    with cache_path.open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            l5 = replay_frozen_l5(cache, blocks, deadline=deadline)
            l6 = build_l6_static(l5, d24, d24_commitment)
            checkpoint = load_checkpoint(args.checkpoint, l6["static"])
            try:
                store, yz_counts, _prefix = reconstruct_l6_prefix(
                    cache, blocks, l6, checkpoint, deadline=deadline
                )
            except DeadlineReached:
                return checkpoint, {
                    "mode": "run",
                    "new_gaps": 0,
                    "next_construction_rank": checkpoint[
                        "next_construction_rank"
                    ],
                    "total_gaps": l6["static"]["gaps"],
                    "stop_reason": "time-limit-during-resume-revalidation",
                }
            if checkpoint.get("status") == "hard-jam":
                return checkpoint, {
                    "mode": "run",
                    "new_gaps": 0,
                    "next_construction_rank": checkpoint[
                        "next_construction_rank"
                    ],
                    "total_gaps": l6["static"]["gaps"],
                    "stop_reason": "previously-certified-exact-hard-jam",
                    "obstruction": checkpoint.get("obstruction"),
                }
            added = 0
            stop_reason = "chunk-limit"
            while checkpoint["next_construction_rank"] < l6["static"]["gaps"]:
                if added >= args.max_new_gaps:
                    stop_reason = "chunk-limit"
                    break
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
                construction_rank = checkpoint["next_construction_rank"]
                gap = l6["schedule"][construction_rank]
                step = l6["parent_word"][gap]
                try:
                    record, interiors = select_first(
                        cache,
                        blocks[step],
                        construction_rank,
                        gap,
                        step,
                        l6["anchors"][gap],
                        l6["anchors"][gap + 1],
                        store,
                        yz_counts,
                        deadline=deadline,
                    )
                except DeadlineReached:
                    stop_reason = "time-limit-during-domain-scan"
                    break
                except NoSurvivor as failure:
                    checkpoint["status"] = "hard-jam"
                    checkpoint["obstruction"] = failure.details
                    stop_reason = "exact-hard-jam"
                    break
                checkpoint["selection_records"].append(record)
                apply_selected(interiors, store, yz_counts)
                checkpoint["next_construction_rank"] += 1
                added += 1
                if added % CHECKPOINT_INTERVAL == 0:
                    refresh_checkpoint(checkpoint, store, yz_counts)
                    save_checkpoint(args.checkpoint, checkpoint)
            refresh_checkpoint(checkpoint, store, yz_counts)
            if checkpoint["next_construction_rank"] == l6["static"]["gaps"]:
                stop_reason = "construction-complete"
            checkpoint["last_run"] = {
                "mode": "run",
                "new_gaps": added,
                "stop_reason": stop_reason,
                "resource_policy": policy,
            }
            save_checkpoint(args.checkpoint, checkpoint)
            return checkpoint, {
                "mode": "run",
                "new_gaps": added,
                "next_construction_rank": checkpoint["next_construction_rank"],
                "total_gaps": l6["static"]["gaps"],
                "stop_reason": stop_reason,
            }
        finally:
            cache.close()


def ordered_chain(l6, selection_records):
    selected = {record["gap"]: tuple(record["selected_word"])
                for record in selection_records}
    if set(selected) != set(range(len(l6["parent_word"]))):
        raise AssertionError("cannot assemble incomplete ordered L6 chain")
    chain = [l6["anchors"][0]]
    flat_word = []
    for gap in range(len(l6["parent_word"])):
        word = selected[gap]
        chain.extend(word_interiors(l6["anchors"][gap], word))
        chain.append(l6["anchors"][gap + 1])
        flat_word.extend(word)
    if len(chain) != len(set(chain)):
        raise AssertionError("completed ordered L6 chain repeats a vertex")
    return tuple(chain), tuple(flat_word), selected


def verify_point_range(points, start, limit, deadline):
    finish = min(len(points), start + limit)
    seen_points = set(points[:start])
    if len(seen_points) != start:
        raise AssertionError("ordered verifier prefix repeats a vertex")
    cursor = start
    while cursor < finish:
        if time.monotonic() >= deadline:
            break
        point = points[cursor]
        if point in seen_points:
            raise AssertionError("ordered chain repeated vertex", cursor, point)
        direction_owner = {}
        for index in range(cursor):
            direction = primitive_direction(sub(points[index], point))
            if direction in direction_owner:
                raise AssertionError(
                    "ordered chain collinear triple",
                    direction_owner[direction],
                    index,
                    cursor,
                )
            direction_owner[direction] = index
        seen_points.add(point)
        cursor += 1
    return cursor


def audit_chunk(args, policy, metadata, blocks, d24, d24_commitment):
    started = time.monotonic()
    deadline = started + args.max_seconds
    with Path(args.cache).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            l5 = replay_frozen_l5(cache, blocks, deadline=deadline)
            l6 = build_l6_static(l5, d24, d24_commitment)
            checkpoint = load_checkpoint(args.checkpoint, l6["static"])
            if checkpoint["next_construction_rank"] != l6["static"]["gaps"]:
                raise RuntimeError("audit requires a construction-complete checkpoint")

            store = Store(l6["anchors"])
            yz_counts = Counter((point[1], point[2]) for point in l6["anchors"])
            audit_cursor = checkpoint["audit"][
                "first_survivor_audited_through_rank"
            ]
            records = checkpoint["selection_records"]
            # Reconstruct the already-audited prefix without rescanning rejects.
            for rank in range(audit_cursor):
                if (
                    rank % CHECKPOINT_INTERVAL == 0
                    and time.monotonic() >= deadline
                ):
                    raise DeadlineReached
                record = records[rank]
                gap = l6["schedule"][rank]
                step = l6["parent_word"][gap]
                word = cached_word(
                    cache,
                    blocks[step],
                    record["first_survivor_ordinal_1_based"],
                )
                if list(word) != record["selected_word"]:
                    raise AssertionError("audited-prefix cached-word drift")
                interiors = check_selected_word(
                    l6["anchors"][gap],
                    l6["anchors"][gap + 1],
                    word,
                    store,
                    yz_counts,
                )
                apply_selected(interiors, store, yz_counts)

            work = 0
            stop_reason = "work-limit"
            while audit_cursor < len(records) and work < args.max_work_items:
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
                stored = records[audit_cursor]
                gap = l6["schedule"][audit_cursor]
                step = l6["parent_word"][gap]
                try:
                    observed, interiors = select_first(
                        cache,
                        blocks[step],
                        audit_cursor,
                        gap,
                        step,
                        l6["anchors"][gap],
                        l6["anchors"][gap + 1],
                        store,
                        yz_counts,
                        deadline=deadline,
                    )
                except DeadlineReached:
                    stop_reason = "time-limit-during-domain-scan"
                    break
                if observed != stored:
                    raise AssertionError(
                        "terminal first-survivor audit mismatch",
                        audit_cursor,
                        observed,
                        stored,
                    )
                apply_selected(interiors, store, yz_counts)
                audit_cursor += 1
                work += 1
                checkpoint["audit"][
                    "first_survivor_audited_through_rank"
                ] = audit_cursor
                if work % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(args.checkpoint, checkpoint)

            if audit_cursor == len(records):
                chain, flat_word, selected = ordered_chain(l6, records)
                checkpoint["audit"]["ordered_verifier_total_points"] = len(chain)
                verifier_cursor = checkpoint["audit"]["ordered_verifier_next_point"]
                remaining_work = args.max_work_items - work
                if remaining_work > 0 and time.monotonic() < deadline:
                    verifier_cursor = verify_point_range(
                        chain, verifier_cursor, remaining_work, deadline
                    )
                    checkpoint["audit"][
                        "ordered_verifier_next_point"
                    ] = verifier_cursor
                if verifier_cursor == len(chain):
                    stop_reason = "terminal-audit-complete"
                    checkpoint["audit"]["terminal_audit_complete"] = True
                    checkpoint["status"] = "complete"
                    output = terminal_payload(
                        args, policy, metadata, checkpoint, l6,
                        chain, flat_word, selected,
                    )
                    atomic_json_dump(output, args.output)
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
            return checkpoint, {
                "mode": "audit",
                "first_survivor_audited_through_rank": checkpoint["audit"][
                    "first_survivor_audited_through_rank"
                ],
                "ordered_verifier_next_point": checkpoint["audit"][
                    "ordered_verifier_next_point"
                ],
                "stop_reason": stop_reason,
                "terminal_audit_complete": checkpoint["audit"][
                    "terminal_audit_complete"
                ],
            }
        finally:
            cache.close()


def terminal_payload(args, policy, metadata, checkpoint, l6,
                     chain, flat_word, selected):
    yz_counts = Counter((point[1], point[2]) for point in chain)
    final_double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if final_double_fibres != l6["initial_double_fibres"]:
        raise AssertionError("terminal doubled-fibre set drift")
    records = checkpoint["selection_records"]
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact finite certificate",
        "checker": {
            "path": "design/no_new_x_line_l6_continuation.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
        },
        "resource_policy": policy,
        "frozen_L5_metadata_sha256": EXPECTED_METADATA_SHA256,
        "compact_cache_sha256": EXPECTED_CACHE_SHA256,
        "static": l6["static"],
        "result": {
            "construction_completed": True,
            "first_survivor_audit_completed": True,
            "independent_ordered_verifier_completed": True,
            "gaps": len(records),
            "points": len(chain),
            "steps": len(flat_word),
            "initial_doubled_yz_fibres": EXPECTED_DOUBLE_FIBRES,
            "final_doubled_yz_fibres": len(final_double_fibres),
            "new_doubled_yz_fibres": 0,
            "minimum_joint_survivors_certified_per_stitch": 1,
            "survivor_counts_exhaustive": False,
            "maximum_first_survivor_ordinal_1_based": max(
                record["first_survivor_ordinal_1_based"] for record in records
            ),
        },
        "commitments": {
            "selection_record_stream_sha256": stable_hash(records),
            "alternate_words_by_gap_sha256": word_map_sha256(selected),
            "alternate_flat_step_word_sha256": hashlib.sha256(
                bytes(flat_word)
            ).hexdigest(),
            "alternate_ordered_point_stream_sha256": point_stream_sha256(chain),
            "final_point_set_sha256": stable_hash(sorted(chain)),
            "final_doubled_fibre_stream_sha256": stable_hash(
                sorted(final_double_fibres)
            ),
        },
        "limitations": [
            "finite certificate for one pinned alternate L5-to-L6 orbit",
            "the 31 x-parallel lines inherited from L4 remain",
            "survivor counts beyond the selected witness are not exhaustive",
            "no uniform all-level availability theorem",
            "no special elimination of non-x-parallel far secants",
        ],
    }


def self_check(args, policy, observed, blocks, d24, d24_commitment):
    checkpoint_status = "absent"
    if Path(args.checkpoint).exists():
        with Path(args.checkpoint).open() as handle:
            checkpoint = json.load(handle)
        digest = checkpoint.pop("checkpoint_payload_sha256", None)
        if digest != stable_hash(checkpoint):
            raise AssertionError("checkpoint self-check commitment mismatch")
        static = checkpoint["static"]
        expected_static_fields = {
            "continuation_checker_sha256": PROCESS_START_CHECKER_SHA256,
            "frozen_L5_metadata_sha256": EXPECTED_METADATA_SHA256,
            "compact_cache_sha256": EXPECTED_CACHE_SHA256,
            "priority_ledger_sha256": EXPECTED_FROZEN_INPUT_SHA256[
                "gate2-ledger-L6.json"
            ],
            "d24_priority_map_sha256": d24_commitment,
            "gaps": EXPECTED_L5_STEPS,
            "anchors": EXPECTED_L5_POINTS,
        }
        for key, expected in expected_static_fields.items():
            if static.get(key) != expected:
                raise AssertionError("checkpoint static self-check drift", key)
        checkpoint_status = {
            "status": checkpoint["status"],
            "next_construction_rank": checkpoint["next_construction_rank"],
            "first_survivor_audited_through_rank": checkpoint["audit"][
                "first_survivor_audited_through_rank"
            ],
            "ordered_verifier_next_point": checkpoint["audit"][
                "ordered_verifier_next_point"
            ],
        }
    return {
        "mode": "self-check",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "resource_policy": policy,
        "frozen_inputs": observed,
        "metadata_sha256": EXPECTED_METADATA_SHA256,
        "cache_sha256": EXPECTED_CACHE_SHA256,
        "cache_blocks": len(blocks),
        "d24_priority_steps": len(d24),
        "d24_priority_map_sha256": d24_commitment,
        "checkpoint": checkpoint_status,
        "heavy_construction_run": False,
    }


def estimate_payload(policy):
    return {
        "mode": "estimate",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "status": "no pickle, cache, metadata, ledger, or checkpoint loaded",
        "resource_policy": policy,
        "scope": {
            "L6_anchors": EXPECTED_L5_POINTS,
            "L6_gaps": EXPECTED_L5_STEPS,
            "inherited_doubled_yz_fibres": EXPECTED_DOUBLE_FIBRES,
            "cache_reused_bytes": EXPECTED_CACHE_BYTES,
        },
        "hard_limits_per_invocation": {
            "wall_seconds": HARD_MAX_SECONDS,
            "new_or_audit_items": HARD_MAX_ITEMS,
            "atomic_checkpoint_interval_items": CHECKPOINT_INTERVAL,
        },
        "estimated_resources": {
            "peak_resident_memory_MiB": "100--250",
            "construction_wall_minutes_total_if_L5-like": "10--25",
            "terminal_audit_wall_minutes_total": "10--25",
            "warning": "deep survivor ranks can increase construction time substantially",
            "processes": 1,
            "threads": 1,
            "nice": 15,
        },
        "checkpoint_semantics": {
            "resume": (
                "recheck stored chosen words and exact reconstructed state; do "
                "not repeatedly rescan old rejected candidates"
            ),
            "terminal_audit": (
                "rescan all rejected candidates once, then independently verify "
                "the ordered point chain in resumable point ranges"
            ),
        },
    }


def bounded(value, name, upper):
    if not 1 <= value <= upper:
        raise ValueError(f"{name} must lie in [1,{upper}]")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "run", "audit"))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=int, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-new-gaps", type=int, default=500)
    parser.add_argument("--max-work-items", type=int, default=500)
    args = parser.parse_args()

    policy = resource_policy(enforce=args.mode in {"run", "audit"})
    if args.mode == "estimate":
        assert_checker_unchanged()
        print(json.dumps(estimate_payload(policy), sort_keys=True, indent=2))
        return
    if args.mode in {"run", "audit"}:
        bounded(args.max_seconds, "max-seconds", HARD_MAX_SECONDS)
        bounded(args.max_new_gaps, "max-new-gaps", HARD_MAX_ITEMS)
        bounded(args.max_work_items, "max-work-items", HARD_MAX_ITEMS)

    observed, metadata, blocks = verify_frozen_inputs(args.metadata, args.cache)
    d24, d24_commitment = load_d24_priority()
    if args.mode == "self-check":
        result = self_check(
            args, policy, observed, blocks, d24, d24_commitment
        )
        assert_checker_unchanged()
        print(json.dumps(result, sort_keys=True, indent=2))
        return
    try:
        if args.mode == "run":
            checkpoint, result = run_chunk(
                args, policy, metadata, blocks, d24, d24_commitment
            )
        else:
            checkpoint, result = audit_chunk(
                args, policy, metadata, blocks, d24, d24_commitment
            )
    except DeadlineReached:
        result = {
            "mode": args.mode,
            "stop_reason": "time-limit-during-frozen-parent-or-audit-replay",
        }
    assert_checker_unchanged()
    checkpoint_path = Path(args.checkpoint)
    result["checkpoint"] = str(checkpoint_path.resolve())
    result["checkpoint_sha256"] = (
        file_sha256(checkpoint_path) if checkpoint_path.exists() else None
    )
    result["maximum_resident_set_raw"] = resource.getrusage(
        resource.RUSAGE_SELF
    ).ru_maxrss
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
