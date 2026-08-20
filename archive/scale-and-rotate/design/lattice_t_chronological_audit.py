#!/usr/bin/env python3
"""Independent terminal audit of the lattice-T chronological L5 replay.

This checker consumes, but never mutates, the frozen construction checkpoint
written by ``lattice_t_chronological_replay.py``.  For every chronological
stitch it independently scans cache ordinals 1 through the stored winner and
checks the exact primary conjunction:

* the zero-envelope (zero-T) accepted-ordinal bit is set;
* every proper interior has a globally unused, mutually distinct (y,z) fibre
  (and hence is intrinsically fibre-clean); and
* the word is exactly legal against the complete placed prefix.

Every projection-clean zero-T candidate is checked by both the optimized and
reference legality implementations.  An earlier legal candidate is fatal;
the stored candidate must be the first and must pass reference legality.

After firstness is audited at every stitch, a second pass assembles the one
realized walk in natural gap order, verifies that no new (y,z) coincidence was
created, and checks every point against all earlier point pairs for an exact
collinear triple.  Firstness and the ordered verifier have separate resumable
cursors in an audit-only checkpoint.  A terminal raw certificate is written
only after both cursors finish; ``freeze-summary`` then writes a compact
repository summary from that sealed terminal artifact.

The source-checkpoint pins intentionally remain PENDING until construction
finishes.  Audit and summary modes refuse to run while any source pin is
pending.  Estimate and synthetic self-check modes open no large artifact.
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


DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L5-primary.json")
DEFAULT_AUDIT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L5-audit-checkpoint-v2.json"
)
DEFAULT_OUTPUT = Path("/tmp/lattice-T-chronological-L5-audit-v2.json")
DEFAULT_SUMMARY = ROOT / "design" / "lattice-T-chronological-L5-summary.json"

EXPECTED_PRODUCER_SHA256 = (
    "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
)
EXPECTED_SOURCE_SHA256 = (
    "9c711e396dc75042b747a1bcacb5093aa8b4c84c316a89081b2e246bdae0c2b8"
)
EXPECTED_SOURCE_BYTES = 5_369_433
EXPECTED_SOURCE_PAYLOAD_SHA256 = (
    "4957ae7456b95d9d1c0033077eee136dfcda820e2ae4fdb9f1037490457dd71c"
)
EXPECTED_SOURCE_PREFIX_SHA256 = (
    "5eb60096ccc3b0b51c17bb44bc782aa6c4106fb5dfa24c56952c5a4e914413a7"
)
EXPECTED_SOURCE_SELECTION_SHA256 = (
    "73f8eb68b593cc268f254f30a84152b3d40887038b58f314f361fd107da066bd"
)
EXPECTED_SOURCE_RECORDS_CANONICAL_SHA256 = (
    "73f8eb68b593cc268f254f30a84152b3d40887038b58f314f361fd107da066bd"
)
EXPECTED_SOURCE_MAX_FIRST_ORDINAL = 2_455

SCHEMA_VERSION = 1
EXPECTED_GAPS = rescue.EXPECTED_GAPS
CHECKPOINT_INTERVAL = 25
MAX_WORK_ITEMS = 5_000
MAX_WORK_SECONDS = rescue.MAX_WORK_SECONDS
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())


class DeadlineReached(Exception):
    def __init__(self, pending=None):
        super().__init__(pending)
        self.pending = pending


def canonical_bytes_sha(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ensure_source_pins():
    pins = {
        "source_file": EXPECTED_SOURCE_SHA256,
        "source_payload": EXPECTED_SOURCE_PAYLOAD_SHA256,
        "source_prefix": EXPECTED_SOURCE_PREFIX_SHA256,
        "source_selection": EXPECTED_SOURCE_SELECTION_SHA256,
        "source_records_canonical": EXPECTED_SOURCE_RECORDS_CANONICAL_SHA256,
    }
    if any(value == "PENDING" for value in pins.values()) or not (
        EXPECTED_SOURCE_BYTES > 0
        and EXPECTED_SOURCE_MAX_FIRST_ORDINAL > 0
    ):
        raise RuntimeError("construction checkpoint is not pinned", pins)


def assert_checker_unchanged():
    observed = rescue.file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("terminal audit checker changed during execution")


def verify_producer():
    observed = rescue.file_sha256(Path(producer.__file__).resolve())
    if observed != EXPECTED_PRODUCER_SHA256:
        raise AssertionError(
            "chronological producer drift", EXPECTED_PRODUCER_SHA256, observed
        )
    return observed


def verify_source(path):
    ensure_source_pins()
    path = Path(path)
    if path.stat().st_size != EXPECTED_SOURCE_BYTES:
        raise AssertionError("construction checkpoint byte-size drift")
    observed_file = rescue.file_sha256(path)
    if observed_file != EXPECTED_SOURCE_SHA256:
        raise AssertionError(
            "construction checkpoint file drift",
            EXPECTED_SOURCE_SHA256,
            observed_file,
        )
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    observed_internal = rescue.stable_hash(source)
    source["checkpoint_payload_sha256"] = internal
    if internal != EXPECTED_SOURCE_PAYLOAD_SHA256 or internal != observed_internal:
        raise AssertionError("construction checkpoint payload drift")
    if source["schema_version"] != producer.SCHEMA_VERSION:
        raise AssertionError("construction checkpoint schema drift")
    if source["status"] != "construction-complete-audit-pending":
        raise AssertionError("source construction is not audit-ready")
    if source["next_construction_rank"] != EXPECTED_GAPS or len(
        source["selection_records"]
    ) != EXPECTED_GAPS:
        raise AssertionError("source construction is incomplete")
    if source["pending_scan"] is not None:
        raise AssertionError("completed source retains a pending domain scan")
    static = source["static"]
    expected_policy = {
        "checker_sha256": EXPECTED_PRODUCER_SHA256,
        "action_channel": producer.PRIMARY_ACTION_CHANNEL,
        "projection_policy": producer.PRIMARY_PROJECTION_POLICY,
        "require_digit_simple": False,
        "survivor_certificate_target": 1,
        "gaps": EXPECTED_GAPS,
        "terminal_first_survivor_audit_complete": False,
    }
    for key, expected in expected_policy.items():
        if static.get(key) != expected:
            raise AssertionError("source primary-policy drift", key)
    if producer.PRIMARY_ACTION_CHANNEL != "zero" or (
        producer.PRIMARY_PROJECTION_POLICY != "global-empty"
    ):
        raise AssertionError("producer primary constants drift")
    prefix = source["prefix"]
    if prefix["prefix_state_sha256"] != EXPECTED_SOURCE_PREFIX_SHA256:
        raise AssertionError("source final-prefix drift")
    if prefix["selection_record_stream_sha256"] != (
        EXPECTED_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("source selection-stream drift")
    if rescue.stable_hash(source["selection_records"]) != (
        EXPECTED_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("source selection records/hash disagree")
    if canonical_bytes_sha(source["selection_records"]) != (
        EXPECTED_SOURCE_RECORDS_CANONICAL_SHA256
    ):
        raise AssertionError("source canonical selection bytes drift")
    maximum = max(
        record["first_survivor_ordinal_1_based"]
        for record in source["selection_records"]
    )
    if maximum != EXPECTED_SOURCE_MAX_FIRST_ORDINAL:
        raise AssertionError("source maximum first ordinal drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed_file,
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
    producer_sha = verify_producer()
    source, source_snapshot = verify_source(args.source)
    artifact_sha = producer.verify_inputs(artifact_args(args))
    _metadata, blocks = rescue.load_metadata(args.metadata)
    parent_word, anchors, schedule = rescue.load_l5_state()
    lattice_result, sidecar = producer.load_lattice_result(
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
            raise AssertionError("compact cache magic drift")
        action_records = producer.parse_bitsets(bitset, sidecar, blocks)
    except BaseException:
        if bitset is not None:
            bitset.close()
        if cache is not None:
            cache.close()
        bitset_handle.close()
        cache_handle.close()
        raise
    return {
        "source": source,
        "source_snapshot": source_snapshot,
        "artifact_sha256": artifact_sha,
        "producer_sha256": producer_sha,
        "blocks": blocks,
        "parent_word": parent_word,
        "anchors": anchors,
        "schedule": schedule,
        "lattice_result": lattice_result,
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


def audit_static(context):
    fields = {
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": context["producer_sha256"],
        "source_checkpoint": context["source_snapshot"],
        "source_prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "source_selection_record_stream_sha256": (
            EXPECTED_SOURCE_SELECTION_SHA256
        ),
        "artifact_sha256": context["artifact_sha256"],
        "policy": {
            "action_channel": "zero",
            "projection_policy": "global-empty",
            "require_digit_simple": False,
            "selection_order": "compact-cache ordinal order",
        },
        "gaps": EXPECTED_GAPS,
    }
    fields["static_state_sha256"] = rescue.stable_hash(fields)
    return fields


def seal(value):
    payload = copy.deepcopy(value)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = rescue.stable_hash(payload)
    return payload


def save_audit_checkpoint(path, checkpoint):
    sealed = seal(checkpoint)
    rescue.atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def prefix_commitment(store, yz_counts, records, rank):
    return producer.prefix_commitment(store, yz_counts, records[:rank], rank)


def initial_audit_checkpoint(static, source, anchors):
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "firstness_audited_through_rank": 0,
        "pending_firstness_scan": None,
        "audit_records": [],
        "audit_record_stream_sha256": rescue.stable_hash([]),
        "audited_prefix": prefix_commitment(
            store, yz_counts, source["selection_records"], 0
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


def load_audit_checkpoint(path, static, source, anchors):
    path = Path(path)
    if not path.exists():
        return initial_audit_checkpoint(static, source, anchors)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(checkpoint):
        raise AssertionError("audit checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION:
        raise AssertionError("audit checkpoint schema drift")
    if checkpoint["static"] != static:
        raise AssertionError("audit checkpoint static-state drift")
    cursor = checkpoint["firstness_audited_through_rank"]
    if not 0 <= cursor <= EXPECTED_GAPS:
        raise AssertionError("firstness audit cursor drift")
    if len(checkpoint["audit_records"]) != cursor:
        raise AssertionError("audit record/cursor drift")
    if checkpoint["audit_record_stream_sha256"] != rescue.stable_hash(
        checkpoint["audit_records"]
    ):
        raise AssertionError("audit record stream drift")
    pending = checkpoint["pending_firstness_scan"]
    if pending is not None and pending["construction_rank"] != cursor:
        raise AssertionError("pending firstness rank drift")
    verifier = checkpoint["ordered_verifier"]
    if verifier["next_point"] and cursor != EXPECTED_GAPS:
        raise AssertionError("ordered verifier advanced before firstness")
    total = verifier["total_points"]
    if total is not None and not 0 <= verifier["next_point"] <= total:
        raise AssertionError("ordered verifier cursor drift")
    if verifier["complete"] and (
        total is None or verifier["next_point"] != total
    ):
        raise AssertionError("ordered verifier completion drift")
    if checkpoint["status"] == "complete" and not verifier["complete"]:
        raise AssertionError("complete audit lacks ordered verification")
    return checkpoint


def cache_word_at_offset(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("stored cache offset outside step block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("stored cache record boundary drift")
    return tuple(cache[offset + 1:end])


def action_accepts(bitset, record, channel, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("audit action ordinal outside step domain")
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
    source = context["source"]
    records = source["selection_records"]
    anchors = context["anchors"]
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    cursor = checkpoint["firstness_audited_through_rank"]
    for rank in range(cursor):
        if rank % CHECKPOINT_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing audited L5 prefix"
        ):
            raise DeadlineReached
        record = records[rank]
        gap = context["schedule"][rank]
        step = context["parent_word"][gap]
        audit_record = checkpoint["audit_records"][rank]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("source schedule record drift", rank)
        if (
            audit_record["construction_rank"],
            audit_record["gap"],
            audit_record["step"],
        ) != (rank, gap, step):
            raise AssertionError("audit schedule record drift", rank)
        word = cache_word_at_offset(
            context["cache"], context["blocks"][step],
            record["cache_record_offset"],
        )
        if list(word) != record["selected_word"]:
            raise AssertionError("audited source word bytes drift", rank)
        ordinal = record["first_survivor_ordinal_1_based"]
        if not action_accepts(
            context["bitset"], context["action_records"][step], "zero", ordinal
        ):
            raise AssertionError("audited source word lost zero-T bit", rank)
        interiors = tuple(rescue.word_interiors(anchors[gap], word))
        if rescue.endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("audited source endpoint drift", rank)
        if not intrinsic_projection_clean(
            anchors[gap], anchors[gap + 1], interiors
        ) or not global_projection_clean(interiors, yz_counts):
            raise AssertionError("audited source global-yz drift", rank)
        apply_selected(interiors, store, yz_counts)
    observed = prefix_commitment(store, yz_counts, records, cursor)
    if observed != checkpoint["audited_prefix"]:
        raise AssertionError("audited-prefix commitment drift")
    if cursor == EXPECTED_GAPS and observed != source["prefix"]:
        raise AssertionError("audited final prefix differs from source")
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
        "digit_rejected": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "static_zero_T_words": action_count,
    }


def validate_pending(pending, rank, gap, step, block, selected_ordinal):
    if (
        pending["construction_rank"], pending["gap"], pending["step"],
        pending["selected_ordinal_1_based"],
    ) != (rank, gap, step, selected_ordinal):
        raise AssertionError("pending firstness identity drift")
    ordinal = pending["next_ordinal_1_based"]
    if not 1 <= ordinal <= selected_ordinal:
        raise AssertionError("pending firstness ordinal drift")
    if pending["domain_words_scanned"] != ordinal - 1:
        raise AssertionError("pending firstness scan-count drift")
    cursor = pending["next_cache_cursor"]
    if not block["start"] <= cursor < block["end"]:
        raise AssertionError("pending firstness cache cursor drift")
    if pending["action_incompatible_skipped"] + pending[
        "action_compatible_seen"
    ] != pending["domain_words_scanned"]:
        raise AssertionError("pending action partition drift")
    if pending["digit_rejected"] != 0:
        raise AssertionError("primary audit unexpectedly applied a digit filter")
    if pending["projection_rejected"] + pending[
        "projection_clean_exact_tested"
    ] != pending["action_compatible_seen"]:
        raise AssertionError("pending projection partition drift")
    if pending["exact_legality_rejected"] != pending[
        "projection_clean_exact_tested"
    ]:
        raise AssertionError("pending exact partition contains a survivor")


def selected_static_record(
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
        "digit_simple": digit_simple(
            context["anchors"][gap], interiors
        ),
        "ordered_T_accepted": action_accepts(
            context["bitset"], action_record, "ordered", ordinal
        ),
        "zero_T_accepted": True,
    }
    identity = {
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
        "survivor_census_exhaustive": False,
        "scan_counters_through_certificate": counters,
    }
    for key, expected in identity.items():
        if source_record.get(key) != expected:
            raise AssertionError("source selected-record audit drift", rank, key)
    return expected_survivor


def audit_one_stitch(context, rank, store, yz_counts, pending, deadline):
    source_record = context["source"]["selection_records"][rank]
    gap = context["schedule"][rank]
    step = context["parent_word"][gap]
    block = context["blocks"][step]
    action_record = context["action_records"][step]
    selected_ordinal = source_record["first_survivor_ordinal_1_based"]
    if not 1 <= selected_ordinal <= block["words"]:
        raise AssertionError("stored selected ordinal outside domain", rank)
    scan = copy.deepcopy(pending) if pending is not None else empty_pending(
        rank, gap, step, block, selected_ordinal,
        action_record["zero"]["set_bits"],
    )
    validate_pending(
        scan, rank, gap, step, block, selected_ordinal
    )
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    reference_memo = {}
    while ordinal <= selected_ordinal:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "independent firstness domain scan"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("audit cache boundary drift", rank, ordinal)
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
        start = context["anchors"][gap]
        target = context["anchors"][gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        intrinsic = intrinsic_projection_clean(
            start, target, interiors
        )
        global_empty = global_projection_clean(
            interiors, yz_counts
        )
        if not intrinsic or not global_empty:
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
                "fast/reference legality disagreement", rank, ordinal
            )
        if not reference_legal:
            scan["exact_legality_rejected"] += 1
            ordinal += 1
            continue
        if rescue.endpoint(start, word) != target:
            raise AssertionError("eligible audit word endpoint drift", rank, ordinal)
        if ordinal < selected_ordinal:
            raise AssertionError(
                "earlier primary-policy survivor found", rank, ordinal,
                selected_ordinal, list(word),
            )
        if list(word) != source_record["selected_word"] or offset != (
            source_record["cache_record_offset"]
        ):
            raise AssertionError("stored winner/cache-order drift", rank)
        counters = {
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
        }
        survivor = selected_static_record(
            context, source_record, rank, gap, step, ordinal, offset,
            word, interiors, counters,
        )
        record = {
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
        return record, interiors
    raise AssertionError("stored winner was not a primary-policy survivor", rank)


def primitive_direction(vector):
    x, y, z = vector
    divisor = gcd(gcd(abs(x), abs(y)), abs(z))
    if divisor == 0:
        raise AssertionError("zero displacement in ordered verifier")
    x, y, z = x // divisor, y // divisor, z // divisor
    if x < 0 or (x == 0 and (y < 0 or (y == 0 and z < 0))):
        x, y, z = -x, -y, -z
    return (x, y, z)


def ordered_chain(context):
    records = context["source"]["selection_records"]
    selected = {record["gap"]: tuple(record["selected_word"])
                for record in records}
    if set(selected) != set(range(EXPECTED_GAPS)):
        raise AssertionError("source does not choose one word per gap")
    anchors = context["anchors"]
    chain = [anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_GAPS):
        word = selected[gap]
        chain.extend(rescue.word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != len(set(chain)):
        raise AssertionError("realized ordered chain repeats a point")
    if len(chain) != context["source"]["prefix"]["placed_point_count"]:
        raise AssertionError("ordered chain/source point count drift")
    if rescue.stable_hash(sorted(chain)) != context["source"]["prefix"][
        "point_set_sha256"
    ]:
        raise AssertionError("ordered chain/source point set drift")
    return tuple(chain), tuple(flat_word), selected


def verify_final_yz(anchors, chain):
    initial = Counter(point[1:] for point in anchors)
    final = Counter(point[1:] for point in chain)
    for fibre, count in final.items():
        expected = initial.get(fibre, 1)
        if count != expected:
            raise AssertionError(
                "terminal no-new-yz invariant failed", fibre, count, expected
            )
    if any(fibre not in final for fibre in initial):
        raise AssertionError("terminal chain lost an anchor yz fibre")
    return final


def verify_ordered_point(chain, cursor):
    point = chain[cursor]
    direction_owner = {}
    for index in range(cursor):
        prior = chain[index]
        direction = primitive_direction(tuple(
            prior[axis] - point[axis] for axis in range(3)
        ))
        earlier = direction_owner.get(direction)
        if earlier is not None:
            raise AssertionError(
                "ordered chain contains a collinear triple",
                earlier, index, cursor,
                [list(chain[earlier]), list(prior), list(point)],
            )
        direction_owner[direction] = index


def terminal_payload(context, checkpoint, chain, flat_word, selected, policy):
    records = context["source"]["selection_records"]
    audit_records = checkpoint["audit_records"]
    ordinals = [
        record["first_survivor_ordinal_1_based"] for record in records
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": "exact independent terminal finite certificate",
        "checker": {
            "path": "design/lattice_t_chronological_audit.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_audit": True,
        },
        "resource_policy": policy,
        "source_checkpoint": context["source_snapshot"],
        "source_producer_sha256": context["producer_sha256"],
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
                item["projection_clean_exact_tested"]
                for item in audit_records
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
            "the pinned L5 primary policy has an exact first survivor at every chronological stitch",
            "each winner is zero-T, globally yz-fresh, and reference-legal against its complete prefix",
            "the final realized chain creates no new yz-fibre coincidence",
            "an independent ordered-pair direction scan finds no collinear triple in the realized chain",
        ],
        "not_proved": [
            "positive availability for every safe state or at levels beyond this pinned L5 orbit",
            "control of latent zero-mask re-entry, births, cursor injection, or arbitrary far secants",
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
        checkpoint = load_audit_checkpoint(
            args.audit_checkpoint, static, context["source"],
            context["anchors"],
        )
        if checkpoint["status"] == "complete":
            return checkpoint, {
                "stop_reason": "terminal-audit-already-complete",
                "work_items": 0,
            }
        try:
            store, yz_counts = reconstruct_audited_prefix(
                context, checkpoint, deadline
            )
        except DeadlineReached:
            return checkpoint, {
                "stop_reason": "time-limit-during-prefix-reconstruction",
                "work_items": 0,
            }
        work = 0
        stop_reason = "work-limit"
        while checkpoint["firstness_audited_through_rank"] < EXPECTED_GAPS:
            if work >= args.max_work_items:
                break
            if rescue.enforce_runtime(deadline, "between firstness stitches"):
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
            checkpoint["audited_prefix"] = prefix_commitment(
                store, yz_counts, context["source"]["selection_records"],
                checkpoint["firstness_audited_through_rank"],
            )
            work += 1
            if work % CHECKPOINT_INTERVAL == 0:
                save_audit_checkpoint(args.audit_checkpoint, checkpoint)

        if checkpoint["firstness_audited_through_rank"] == EXPECTED_GAPS:
            if checkpoint["audited_prefix"] != context["source"]["prefix"]:
                raise AssertionError("completed audit prefix/source drift")
            chain, flat_word, selected = ordered_chain(context)
            final_yz = verify_final_yz(context["anchors"], chain)
            verifier = checkpoint["ordered_verifier"]
            point_sha = rescue.point_stream_sha256(chain)
            point_set_sha = rescue.stable_hash(sorted(chain))
            yz_sha = rescue.stable_hash(sorted(final_yz.items()))
            expected_verifier = {
                "total_points": len(chain),
                "ordered_point_stream_sha256": point_sha,
                "ordered_point_set_sha256": point_set_sha,
                "final_yz_occupancy_sha256": yz_sha,
            }
            for key, value in expected_verifier.items():
                current = verifier[key]
                if current is not None and current != value:
                    raise AssertionError("ordered verifier commitment drift", key)
                verifier[key] = value
            verifier["final_no_new_yz_coincidence"] = True
            while verifier["next_point"] < len(chain):
                if work >= args.max_work_items:
                    stop_reason = "ordered-verifier-work-limit"
                    break
                if rescue.enforce_runtime(deadline, "ordered point verifier"):
                    stop_reason = "ordered-verifier-time-limit"
                    break
                verify_ordered_point(chain, verifier["next_point"])
                verifier["next_point"] += 1
                work += 1
                if work % CHECKPOINT_INTERVAL == 0:
                    save_audit_checkpoint(args.audit_checkpoint, checkpoint)
                    # save_audit_checkpoint replaces the checkpoint's nested
                    # dictionaries with the sealed deep copy.  Refresh this
                    # local reference so subsequent increments are committed
                    # to that live copy rather than to the pre-save object.
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
            "mode": "audit",
            "work_items": work,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "maximum_resident_bytes": rescue.maximum_resident_bytes(),
            "resource_policy": policy,
        }
        save_audit_checkpoint(args.audit_checkpoint, checkpoint)
        observation = {
            "stop_reason": stop_reason,
            "work_items": work,
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
        elapsed = time.monotonic() - started
        resident = rescue.maximum_resident_bytes()
        if elapsed > rescue.MAX_SECONDS or resident > rescue.MAX_RESIDENT_BYTES:
            raise RuntimeError("terminal audit resource bound exceeded")
        observation["elapsed_seconds"] = round(elapsed, 6)
        observation["maximum_resident_bytes"] = resident
        return checkpoint, observation
    finally:
        close_context(context)


def verify_terminal(path):
    with Path(path).open() as handle:
        terminal = json.load(handle)
    internal = terminal.pop("terminal_payload_sha256", None)
    if internal != rescue.stable_hash(terminal):
        raise AssertionError("terminal payload commitment drift")
    terminal["terminal_payload_sha256"] = internal
    if terminal["checker"]["sha256"] != PROCESS_START_CHECKER_SHA256:
        raise AssertionError("terminal checker identity drift")
    if terminal["source_checkpoint"]["sha256"] != EXPECTED_SOURCE_SHA256:
        raise AssertionError("terminal source checkpoint drift")
    required = (
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "global_empty_yz_verified_at_every_stitch",
        "final_no_new_yz_coincidence",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not terminal["result"][key] for key in required):
        raise AssertionError("terminal result is incomplete")
    return terminal


def freeze_summary(args):
    ensure_source_pins()
    verify_producer()
    terminal = verify_terminal(args.output)
    raw = {
        "path": str(Path(args.output).resolve()),
        "sha256": rescue.file_sha256(args.output),
        "bytes": Path(args.output).stat().st_size,
        "payload_sha256": terminal["terminal_payload_sha256"],
    }
    summary = {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": terminal["status"],
        "checker": terminal["checker"],
        "source_checkpoint": terminal["source_checkpoint"],
        "terminal_raw_artifact": raw,
        "result": terminal["result"],
        "commitments": terminal["commitments"],
        "proved": terminal["proved"],
        "not_proved": terminal["not_proved"],
    }
    rescue.atomic_json_dump(summary, args.summary)
    return {
        "summary": str(Path(args.summary).resolve()),
        "summary_sha256": rescue.file_sha256(args.summary),
        "summary_bytes": Path(args.summary).stat().st_size,
        "terminal_raw_artifact": raw,
    }


def self_check():
    producer_sha = verify_producer()
    bits = bytes((0b00000101, 0b00000010))
    action_record = {
        "words": 10,
        "zero": {"offset": 0, "set_bits": 3},
        "ordered": {"offset": 0, "set_bits": 3},
    }
    observed = [
        action_accepts(bits, action_record, "zero", ordinal)
        for ordinal in range(1, 11)
    ]
    if observed != [
        True, False, True, False, False,
        False, False, False, False, True,
    ]:
        raise AssertionError("independent ordinal bit convention drift")
    start = (10, 20, 30)
    target = (20, 25, 35)
    interiors = ((11, 21, 31), (12, 22, 32))
    if not intrinsic_projection_clean(start, target, interiors):
        raise AssertionError("independent intrinsic projection drift")
    if global_projection_clean(interiors, Counter({(21, 31): 1})):
        raise AssertionError("independent global projection drift")
    if primitive_direction((-2, -4, -6)) != (1, 2, 3):
        raise AssertionError("primitive-direction normalization drift")
    collinear = ((0, 0, 0), (1, 1, 1), (2, 2, 2))
    try:
        verify_ordered_point(collinear, 2)
    except AssertionError as error:
        if not error.args or error.args[0] != (
            "ordered chain contains a collinear triple"
        ):
            raise
    else:
        raise AssertionError("synthetic collinear triple was not rejected")
    clean = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    for cursor in range(len(clean)):
        verify_ordered_point(clean, cursor)
    checkpoint = {"ordered_verifier": {"next_point": 0}}
    stale_verifier = checkpoint["ordered_verifier"]
    sealed = seal(checkpoint)
    checkpoint.clear()
    checkpoint.update(sealed)
    stale_verifier["next_point"] += 1
    if checkpoint["ordered_verifier"]["next_point"] != 0:
        raise AssertionError("checkpoint replacement did not detach nesting")
    refreshed_verifier = checkpoint["ordered_verifier"]
    refreshed_verifier["next_point"] += 1
    if checkpoint["ordered_verifier"]["next_point"] != 1:
        raise AssertionError("refreshed verifier cursor was not committed")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": producer_sha,
        "source_pins_finalized": EXPECTED_SOURCE_SHA256 != "PENDING",
        "large_artifacts_opened": False,
        "independent_ordinal_bits_tested": 10,
        "independent_projection_predicates_tested": True,
        "synthetic_collinear_rejection": True,
        "synthetic_general_position_acceptance": True,
        "checkpoint_nested_cursor_refresh_tested": True,
    }


def estimate():
    return {
        "status": "no large artifact opened",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": EXPECTED_PRODUCER_SHA256,
        "source_pins_finalized": EXPECTED_SOURCE_SHA256 != "PENDING",
        "source_checkpoint_is_read_only": True,
        "audit_checkpoint_is_separate": True,
        "firstness_policy": (
            "zero-T AND global empty-yz AND exact reference legality"
        ),
        "firstness_resume_granularity": "cache ordinal within one stitch",
        "terminal_verifier": (
            "ordered chain; each point checked against directions to all prior points"
        ),
        "summary_mode": "freeze-summary after sealed terminal audit",
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": rescue.MAX_SECONDS,
        "hard_maximum_resident_bytes": rescue.MAX_RESIDENT_BYTES,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("estimate", "self-check", "audit", "freeze-summary")
    )
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
    parser.add_argument("--max-seconds", type=float, default=MAX_WORK_SECONDS)
    parser.add_argument("--max-work-items", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= MAX_WORK_SECONDS:
        raise ValueError("max-seconds outside (0,115]")
    if not 1 <= args.max_work_items <= MAX_WORK_ITEMS:
        raise ValueError("max-work-items outside [1,5000]")
    policy = rescue.resource_policy(
        enforce=args.mode in {"audit", "freeze-summary"}
    )
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    elif args.mode == "freeze-summary":
        result = freeze_summary(args)
    else:
        checkpoint, observation = audit_chunk(args, policy)
        result = {
            "status": checkpoint["status"],
            "audit_checkpoint": str(
                Path(args.audit_checkpoint).resolve()
            ),
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
