#!/usr/bin/env python3
"""Exact two-cone birth audit and guarded L6 continuation prototype.

The terminal-audited lattice-T L5 walk, after the usual ``M_BAL3`` scaling,
is the grandfathered L6 base.  Secants whose two endpoints are already in
that 8,268-point base are deliberately allowed.  Every later connector
interior is a new endpoint.  This checker classifies all secants born with
that endpoint into exactly two classes:

* ``old-new``: the other endpoint existed before the selected word; and
* ``same-word-new-new``: the other endpoint is an earlier interior of the
  same selected word.

It tests only the two homogeneous projective cones

    J = 11/3 and J = 348/275,
    J(r,y,z) = (3*y*y - y*z + 3*z*z) / (r*r).

No division, floating point, distance cutoff, or endpoint truncation is used.
For ``J=a/b`` the exact test is

    b*(3*y*y-y*z+3*z*z) - a*r*r == 0.

``audit`` reads the current partial or terminal checkpoint produced by
``lattice_t_l6_continuation.py`` and extends a separate resumable pair cursor.
It reports exact counts, earliest witnesses, and chained semantic digests of
new cone births.  The source checkpoint may grow between audit runs; its
already audited selection prefix is immutable and is rechecked on every
resume.

``guard-run`` starts a separate first-survivor construction.  It retains the
original conjunction (zero-T, globally fresh yz fibres, and exact fast plus
reference legality), then rejects an otherwise legal word if any old-new or
same-word-new-new secant lies in either named cone.  Its checkpoint is not an
independent terminal audit.

``guard-l5-run`` is the smaller inductive test.  It starts from the 2,458
inherited L4 anchors used by the pinned L5 replay, enumerates and retains the
exact 246 affine cone lines already present in that base, and applies the same
no-new-cone-birth rule to every L5 connector choice.

This is a finite-spectrum CEGAR guard, not a generic far-secant lemma: every
other primitive direction and affine moment remains uncontrolled.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import mmap
import os
import sys
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import lattice_t_l6_continuation as producer  # noqa: E402


rescue = producer.rescue
l5 = producer.l5_producer
legacy = producer.legacy_l6

DEFAULT_SOURCE = producer.DEFAULT_CHECKPOINT
DEFAULT_AUDIT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L6-cone-birth-audit-v1.json"
)
DEFAULT_AUDIT_OUTPUT = (
    ROOT / "design" / "lattice-T-L6-cone-birth-audit-summary.json"
)
DEFAULT_GUARD_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L6-cone-guard-v1.json"
)
DEFAULT_L5_GUARD_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L5-cone-guard-v1.json"
)

SPECTRA = (
    {"label": "11/3", "numerator": 11, "denominator": 3},
    {"label": "348/275", "numerator": 348, "denominator": 275},
)
SCHEMA_VERSION = 1
GRANDFATHERED_POINTS = producer.EXPECTED_PARENT_POINTS
EXPECTED_L5_GRANDFATHERED_POINTS = rescue.EXPECTED_ANCHORS
EXPECTED_L5_PROMOTED_SEED_LINES = 246
PAIR_CHECK_INTERVAL = 65_536
PAIR_CHECKPOINT_INTERVAL = 1_000_000
RECONSTRUCT_CHECK_INTERVAL = 50
HARD_MAX_SECONDS = 600.0
HARD_MAX_PAIRS = 50_000_000
HARD_MAX_RANKS = 1_000
HARD_MAX_GAPS = 1_000
EMPTY_CHAIN_SHA256 = hashlib.sha256(b"").hexdigest()
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())
PROCESS_START_PRODUCER_SHA256 = rescue.file_sha256(Path(producer.__file__))
PROCESS_START_L5_PRODUCER_SHA256 = rescue.file_sha256(Path(l5.__file__))


class AuditYield(Exception):
    pass


class GuardDeadline(Exception):
    def __init__(self, pending):
        super().__init__(pending)
        self.pending = pending


class GuardNoSurvivor(Exception):
    def __init__(self, details):
        super().__init__(details)
        self.details = details


def assert_checker_unchanged():
    if rescue.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ):
        raise RuntimeError("L6 cone-birth checker changed during execution")
    if rescue.file_sha256(Path(producer.__file__)) != (
        PROCESS_START_PRODUCER_SHA256
    ):
        raise RuntimeError("L6 producer changed during cone-birth execution")
    if rescue.file_sha256(Path(l5.__file__)) != (
        PROCESS_START_L5_PRODUCER_SHA256
    ):
        raise RuntimeError("L5 producer changed during cone-birth execution")


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def chain_digest(previous, value):
    payload = canonical_bytes(value)
    digest = hashlib.sha256()
    digest.update(bytes.fromhex(previous))
    digest.update(len(payload).to_bytes(8, "little"))
    digest.update(payload)
    return digest.hexdigest()


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def primitive_direction(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise AssertionError("zero pair displacement in cone classifier")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def cone_values(direction):
    r, y, z = direction
    quadratic = 3 * y * y - y * z + 3 * z * z
    return {
        item["label"]: (
            item["denominator"] * quadratic
            - item["numerator"] * r * r
        )
        for item in SPECTRA
    }


def matched_spectra(direction):
    values = cone_values(direction)
    return tuple(label for label, value in values.items() if value == 0)


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def promoted_seed_cone_lines(points):
    """Enumerate the exact affine cone lines in the inherited anchor base."""
    records = []
    line_keys = set()
    for later_id in range(len(points)):
        later = points[later_id]
        for earlier_id in range(later_id):
            earlier = points[earlier_id]
            direction = subtract(later, earlier)
            matches = matched_spectra(direction)
            if not matches:
                continue
            primitive = primitive_direction(direction)
            moment = cross(earlier, primitive)
            line_key = (primitive, moment)
            if line_key in line_keys:
                raise AssertionError(
                    "inherited anchors contain three points on one cone line"
                )
            line_keys.add(line_key)
            records.append({
                "earlier_point_id": earlier_id,
                "later_point_id": later_id,
                "matched_spectra": list(matches),
                "canonical_primitive_direction": list(primitive),
                "exact_Pluecker_moment": list(moment),
            })
    return tuple(records)


def provenance_record(value):
    kind = value[0]
    if kind == "grandfathered-base":
        return {
            "birth_kind": kind,
            "point_id": value[1],
            "L6_birth_rank": -1,
            "gap": None,
            "interior_slot": None,
        }
    _kind, point_id, rank, gap, slot = value
    return {
        "birth_kind": kind,
        "point_id": point_id,
        "L6_birth_rank": rank,
        "gap": gap,
        "interior_slot": slot,
    }


def pair_record(
    classification, rank, gap, step, later_slot, later_id, later_point,
    earlier_id, earlier_point, earlier_provenance,
):
    direction = subtract(later_point, earlier_point)
    matches = matched_spectra(direction)
    if not matches:
        return None
    primitive = primitive_direction(direction)
    return {
        "classification": classification,
        "L6_birth_rank": rank,
        "gap": gap,
        "step": step,
        "later_interior_slot": later_slot,
        "later_point_id": later_id,
        "later_point": list(later_point),
        "earlier_point_id": earlier_id,
        "earlier_point": list(earlier_point),
        "earlier_provenance": provenance_record(earlier_provenance),
        "raw_direction": list(direction),
        "canonical_primitive_direction": list(primitive),
        "F_values_on_raw_direction": cone_values(direction),
        "F_values_on_primitive_direction": cone_values(primitive),
        "matched_spectra": list(matches),
        "birth_order_key": [rank, later_slot, earlier_id],
    }


def first_word_cone_birth(
    interiors, store, rank, gap, step,
    grandfathered_points=GRANDFATHERED_POINTS,
):
    """Return the first new cone birth in exact endpoint birth/id order."""
    base_id = len(store.pts)
    for later_slot, point in enumerate(interiors):
        later_id = base_id + later_slot
        px, py, pz = point
        for earlier_id in range(len(store.pts)):
            direction = (
                px - store.xs[earlier_id],
                py - store.ys[earlier_id],
                pz - store.zs[earlier_id],
            )
            if matched_spectra(direction):
                provenance = (
                    "grandfathered-base", earlier_id
                ) if earlier_id < grandfathered_points else (
                    "earlier-connector-interior", earlier_id, None, None, None
                )
                return pair_record(
                    "old-new", rank, gap, step, later_slot, later_id, point,
                    earlier_id, store.pts[earlier_id], provenance,
                )
        for earlier_slot in range(later_slot):
            earlier_id = base_id + earlier_slot
            direction = subtract(point, interiors[earlier_slot])
            if matched_spectra(direction):
                provenance = (
                    "same-word-interior", earlier_id, rank, gap,
                    earlier_slot,
                )
                return pair_record(
                    "same-word-new-new", rank, gap, step, later_slot,
                    later_id, point, earlier_id, interiors[earlier_slot],
                    provenance,
                )
    return None


def cone_scope_fields(grandfathered_points):
    return {
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": PROCESS_START_PRODUCER_SHA256,
        "grandfathered_base_points": grandfathered_points,
        "grandfathering_rule": (
            "base-base secants are allowed; every secant whose later endpoint "
            "is a connector interior at the guarded level is classified"
        ),
        "spectra": [
            {
                **item,
                "polynomial": (
                    f"{item['denominator']}*(3*y^2-y*z+3*z^2)-"
                    f"{item['numerator']}*r^2"
                ),
            }
            for item in SPECTRA
        ],
        "scope_warning": "only the two displayed projective cones are controlled",
    }


def common_static(context):
    return {
        **cone_scope_fields(GRANDFATHERED_POINTS),
        "base_L6_static_state_sha256": context["l6"]["static"][
            "static_state_sha256"
        ],
        "parent_terminal_sha256": producer.EXPECTED_PARENT_TERMINAL_SHA256,
    }


def load_source_snapshot(path, expected_static):
    path = Path(path)
    with path.open("rb") as handle:
        raw = handle.read()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    source = json.loads(raw)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(source):
        raise AssertionError("L6 source checkpoint payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source.get("schema_version") != producer.SCHEMA_VERSION or source.get(
        "static"
    ) != expected_static:
        raise AssertionError("L6 source checkpoint schema/static drift")
    rank = source.get("next_construction_rank")
    records = source.get("selection_records")
    if not isinstance(records, list) or rank != len(records) or not (
        0 <= rank <= expected_static["gaps"]
    ):
        raise AssertionError("L6 source rank/selection extent drift")
    if source.get("status") not in {
        "partial", "hard-jam", "construction-complete-audit-pending"
    }:
        raise AssertionError("unexpected L6 source status", source.get("status"))
    pending = source.get("pending_scan")
    if pending is not None and pending.get("construction_rank") != rank:
        raise AssertionError("L6 source pending/rank drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": source_sha256,
        "bytes": len(raw),
        "payload_sha256": internal,
        "status": source["status"],
        "selected_ranks": rank,
        "selection_prefix_sha256": rescue.stable_hash(records),
    }


def selected_geometry(context, rank, record):
    l6_state = context["l6"]
    gap = l6_state["schedule"][rank]
    step = l6_state["parent_word"][gap]
    if (record.get("construction_rank"), record.get("gap"), record.get("step")) != (
        rank, gap, step
    ):
        raise AssertionError("L6 source schedule identity drift", rank)
    block = context["blocks"][step]
    action = context["action_records"][step]
    if record.get("domain_words") != block["words"] or record.get(
        "static_action_words"
    ) != action["zero"]["set_bits"]:
        raise AssertionError("L6 source domain/action extent drift", rank)
    ordinal = record["first_survivor_ordinal_1_based"]
    if not l5.action_accepts(
        context["bitset"], action, "zero", ordinal
    ):
        raise AssertionError("L6 source selected word lost zero-T membership")
    word = producer.cache_word_at_offset(
        context["cache"], block, record["cache_record_offset"]
    )
    if list(word) != record["selected_word"]:
        raise AssertionError("L6 source selected cache bytes drift", rank)
    start = l6_state["anchors"][gap]
    target = l6_state["anchors"][gap + 1]
    interiors = tuple(rescue.word_interiors(start, word))
    if rescue.endpoint(start, word) != target:
        raise AssertionError("L6 source selected endpoint drift", rank)
    return gap, step, start, target, word, interiors


def apply_geometry(interiors, store, yz_counts):
    if not l5.global_projection_clean(interiors, yz_counts):
        raise AssertionError("L6 source or guard lost global-yz freshness")
    producer.apply_selected(interiors, store, yz_counts)


def prefix_record(store, yz_counts, records, rank):
    return producer.prefix_commitment(store, yz_counts, records, rank)


def audit_static(context, source_path):
    result = {
        **common_static(context),
        "mode": "audit-existing-L6-checkpoint",
        "source_path": str(Path(source_path).resolve()),
        "source_policy": context["l6"]["static"]["policy"],
        "pair_order": (
            "construction rank, later interior slot, then earlier point id; "
            "old-new and same-word pairs are thereby interleaved in actual "
            "later-endpoint birth order"
        ),
    }
    result["static_state_sha256"] = rescue.stable_hash(result)
    return result


def initial_audit_checkpoint(context, static):
    store = rescue.Store(context["l6"]["anchors"])
    yz_counts = Counter(point[1:] for point in context["l6"]["anchors"])
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "next_construction_rank": 0,
        "pending_pair_scan": None,
        "audited_source_selection_prefix_sha256": rescue.stable_hash([]),
        "audited_prefix": prefix_record(store, yz_counts, [], 0),
        "classification_pair_counts": {
            "old-new": 0,
            "same-word-new-new": 0,
        },
        "matched_spectrum_counts": {
            item["label"]: 0 for item in SPECTRA
        },
        "matched_classification_counts": {
            "old-new": {item["label"]: 0 for item in SPECTRA},
            "same-word-new-new": {
                item["label"]: 0 for item in SPECTRA
            },
        },
        "matched_birth_chain_sha256": EMPTY_CHAIN_SHA256,
        "matched_spectrum_chain_sha256": {
            item["label"]: EMPTY_CHAIN_SHA256 for item in SPECTRA
        },
        "earliest_new_cone_birth": None,
        "source_snapshots": [],
        "last_run": None,
    }


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


def load_audit_checkpoint(path, context, static, source):
    path = Path(path)
    if not path.exists():
        return initial_audit_checkpoint(context, static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(checkpoint):
        raise AssertionError("L6 cone audit checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != static:
        raise AssertionError("L6 cone audit checkpoint schema/static drift")
    rank = checkpoint["next_construction_rank"]
    if not 0 <= rank <= len(source["selection_records"]):
        raise AssertionError("source is shorter than audited prefix")
    expected_prefix = rescue.stable_hash(source["selection_records"][:rank])
    if checkpoint["audited_source_selection_prefix_sha256"] != expected_prefix:
        raise AssertionError("already audited L6 selection prefix changed")
    pending = checkpoint["pending_pair_scan"]
    if pending is not None and pending["construction_rank"] != rank:
        raise AssertionError("L6 cone audit pending/rank drift")
    if checkpoint["status"] == "complete" and rank != context["l6"][
        "static"
    ]["gaps"]:
        raise AssertionError("premature complete L6 cone audit")
    return checkpoint


def reconstruct_audited_prefix(context, source, checkpoint, deadline):
    rank_limit = checkpoint["next_construction_rank"]
    store = rescue.Store(context["l6"]["anchors"])
    yz_counts = Counter(point[1:] for point in context["l6"]["anchors"])
    provenance = [
        ("grandfathered-base", point_id)
        for point_id in range(len(store.pts))
    ]
    for rank in range(rank_limit):
        if rank % RECONSTRUCT_CHECK_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing cone-audited L6 prefix"
        ):
            raise AuditYield
        record = source["selection_records"][rank]
        gap, _step, _start, _target, _word, interiors = selected_geometry(
            context, rank, record
        )
        base_id = len(store.pts)
        apply_geometry(interiors, store, yz_counts)
        provenance.extend(
            ("earlier-L6-interior", base_id + slot, rank, gap, slot)
            for slot in range(len(interiors))
        )
    observed = prefix_record(
        store, yz_counts, source["selection_records"][:rank_limit], rank_limit
    )
    if observed != checkpoint["audited_prefix"]:
        raise AssertionError("L6 cone-audited prefix commitment drift")
    return store, yz_counts, provenance


def empty_pending_pair_scan(rank, gap, step, interiors, old_points):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "interior_count": len(interiors),
        "old_point_count": old_points,
        "later_slot": 0,
        "phase": "old-new",
        "earlier_cursor": 0,
        "rank_pairs_scanned": 0,
        "rank_matches": {item["label"]: 0 for item in SPECTRA},
    }


def validate_pending_pair_scan(pending, rank, gap, step, interiors, old_points):
    if (
        pending["construction_rank"], pending["gap"], pending["step"]
    ) != (rank, gap, step):
        raise AssertionError("pending cone pair identity drift")
    if pending["interior_count"] != len(interiors) or pending[
        "old_point_count"
    ] != old_points:
        raise AssertionError("pending cone pair extent drift")
    later_slot = pending["later_slot"]
    if not 0 <= later_slot <= len(interiors):
        raise AssertionError("pending cone later-slot drift")
    if pending["phase"] not in {"old-new", "same-word-new-new"}:
        raise AssertionError("pending cone phase drift")
    limit = old_points if pending["phase"] == "old-new" else later_slot
    if not 0 <= pending["earlier_cursor"] <= limit:
        raise AssertionError("pending cone earlier cursor drift")


def record_audit_match(checkpoint, record):
    if checkpoint["earliest_new_cone_birth"] is None:
        checkpoint["earliest_new_cone_birth"] = record
    checkpoint["matched_birth_chain_sha256"] = chain_digest(
        checkpoint["matched_birth_chain_sha256"], record
    )
    classification = record["classification"]
    for label in record["matched_spectra"]:
        checkpoint["matched_spectrum_counts"][label] += 1
        checkpoint["matched_classification_counts"][classification][label] += 1
        checkpoint["matched_spectrum_chain_sha256"][label] = chain_digest(
            checkpoint["matched_spectrum_chain_sha256"][label], record
        )


def scan_one_pair(
    checkpoint, pending, classification, rank, gap, step, later_slot,
    later_id, later_point, earlier_id, earlier_point, earlier_provenance,
):
    checkpoint["classification_pair_counts"][classification] += 1
    pending["rank_pairs_scanned"] += 1
    record = pair_record(
        classification, rank, gap, step, later_slot, later_id, later_point,
        earlier_id, earlier_point, earlier_provenance,
    )
    if record is not None:
        for label in record["matched_spectra"]:
            pending["rank_matches"][label] += 1
        record_audit_match(checkpoint, record)


def audit_rank_pairs(
    args, context, checkpoint, store, provenance, rank, gap, step,
    interiors, deadline, run_state,
):
    pending = checkpoint["pending_pair_scan"]
    if pending is None:
        pending = empty_pending_pair_scan(
            rank, gap, step, interiors, len(store.pts)
        )
    validate_pending_pair_scan(
        pending, rank, gap, step, interiors, len(store.pts)
    )
    checkpoint["pending_pair_scan"] = pending
    base_id = len(store.pts)
    while pending["later_slot"] < len(interiors):
        later_slot = pending["later_slot"]
        later_id = base_id + later_slot
        later_point = interiors[later_slot]
        if pending["phase"] == "old-new":
            while pending["earlier_cursor"] < len(store.pts):
                earlier_id = pending["earlier_cursor"]
                scan_one_pair(
                    checkpoint, pending, "old-new", rank, gap, step,
                    later_slot, later_id, later_point, earlier_id,
                    store.pts[earlier_id], provenance[earlier_id],
                )
                pending["earlier_cursor"] += 1
                run_state["pairs"] += 1
                run_state["since_save"] += 1
                if run_state["pairs"] % PAIR_CHECK_INTERVAL == 0:
                    if run_state["pairs"] >= args.max_pairs or (
                        rescue.enforce_runtime(deadline, "auditing L6 cone births")
                    ):
                        return False
                if run_state["since_save"] >= PAIR_CHECKPOINT_INTERVAL:
                    save_checkpoint(args.audit_checkpoint, checkpoint)
                    pending = checkpoint["pending_pair_scan"]
                    run_state["since_save"] = 0
            pending["phase"] = "same-word-new-new"
            pending["earlier_cursor"] = 0
        while pending["earlier_cursor"] < later_slot:
            earlier_slot = pending["earlier_cursor"]
            earlier_id = base_id + earlier_slot
            earlier_provenance = (
                "same-word-interior", earlier_id, rank, gap, earlier_slot
            )
            scan_one_pair(
                checkpoint, pending, "same-word-new-new", rank, gap, step,
                later_slot, later_id, later_point, earlier_id,
                interiors[earlier_slot], earlier_provenance,
            )
            pending["earlier_cursor"] += 1
            run_state["pairs"] += 1
            run_state["since_save"] += 1
            if run_state["pairs"] % PAIR_CHECK_INTERVAL == 0:
                if run_state["pairs"] >= args.max_pairs or rescue.enforce_runtime(
                    deadline, "auditing same-word L6 cone births"
                ):
                    return False
            if run_state["since_save"] >= PAIR_CHECKPOINT_INTERVAL:
                save_checkpoint(args.audit_checkpoint, checkpoint)
                pending = checkpoint["pending_pair_scan"]
                run_state["since_save"] = 0
        pending["later_slot"] += 1
        pending["phase"] = "old-new"
        pending["earlier_cursor"] = 0
    return True


def revalidate_source_prefix(args, context, loaded_source, loaded_extent):
    current, snapshot = load_source_snapshot(
        args.source, context["l6"]["static"]
    )
    if len(current["selection_records"]) < loaded_extent or current[
        "selection_records"
    ][:loaded_extent] != loaded_source["selection_records"][:loaded_extent]:
        raise AssertionError("L6 source selection prefix changed during audit")
    return snapshot


def audit_summary(checkpoint, source_snapshot, current_snapshot):
    result = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": checkpoint["status"],
        "checker": {
            "path": "design/lattice_t_l6_cone_birth_guard.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
        },
        "source_snapshot_loaded": source_snapshot,
        "source_snapshot_after_run": current_snapshot,
        "scope": {
            "grandfathered_base_points": GRANDFATHERED_POINTS,
            "base_base_secants_scanned": False,
            "new_birth_classes": ["old-new", "same-word-new-new"],
            "spectra": [dict(item) for item in SPECTRA],
            "endpoint_cutoff": None,
            "distance_cutoff": None,
            "audited_construction_ranks": checkpoint[
                "next_construction_rank"
            ],
            "pending_pair_scan": checkpoint["pending_pair_scan"],
        },
        "result": {
            "classification_pair_counts": checkpoint[
                "classification_pair_counts"
            ],
            "matched_spectrum_counts": checkpoint[
                "matched_spectrum_counts"
            ],
            "matched_classification_counts": checkpoint[
                "matched_classification_counts"
            ],
            "matched_birth_chain_sha256": checkpoint[
                "matched_birth_chain_sha256"
            ],
            "matched_spectrum_chain_sha256": checkpoint[
                "matched_spectrum_chain_sha256"
            ],
            "earliest_new_cone_birth": checkpoint[
                "earliest_new_cone_birth"
            ],
        },
        "proved": [
            "every classified pair in the audited L6 prefix was tested against both displayed homogeneous integer equations",
            "base-base secants were grandfathered and every later pair was assigned at its actual later-endpoint birth",
            "the reported earliest witness is first in rank/later-slot/earlier-id order",
        ],
        "not_proved": [
            "exclusion of any projective spectrum other than 11/3 and 348/275",
            "a bound on affine line moments inside either cone",
            "positive connector availability, a generic far-secant tail, or an unconditional theorem",
        ],
    }
    result["payload_sha256"] = rescue.stable_hash(result)
    return result


def run_audit(args, resource_policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = producer.open_context(args)
    try:
        source, source_snapshot = load_source_snapshot(
            args.source, context["l6"]["static"]
        )
        static = audit_static(context, args.source)
        checkpoint = load_audit_checkpoint(
            args.audit_checkpoint, context, static, source
        )
        try:
            store, yz_counts, provenance = reconstruct_audited_prefix(
                context, source, checkpoint, deadline
            )
        except AuditYield:
            checkpoint["last_run"] = {
                "stop_reason": "time-limit-during-prefix-reconstruction",
                "new_pairs": 0,
                "resource_policy": resource_policy,
            }
            save_checkpoint(args.audit_checkpoint, checkpoint)
            current_snapshot = revalidate_source_prefix(
                args, context, source, len(source["selection_records"])
            )
            rescue.atomic_json_dump(
                audit_summary(checkpoint, source_snapshot, current_snapshot),
                args.output,
            )
            return checkpoint
        run_state = {"pairs": 0, "since_save": 0, "ranks": 0}
        stop_reason = "caught-up-to-loaded-source"
        loaded_extent = len(source["selection_records"])
        while checkpoint["next_construction_rank"] < loaded_extent:
            if run_state["ranks"] >= args.max_ranks:
                stop_reason = "rank-limit"
                break
            if run_state["pairs"] >= args.max_pairs:
                stop_reason = "pair-limit"
                break
            if rescue.enforce_runtime(deadline, "between cone-audit ranks"):
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            record = source["selection_records"][rank]
            gap, step, _start, _target, _word, interiors = selected_geometry(
                context, rank, record
            )
            complete = audit_rank_pairs(
                args, context, checkpoint, store, provenance, rank, gap,
                step, interiors, deadline, run_state,
            )
            if not complete:
                stop_reason = (
                    "pair-limit-during-rank"
                    if run_state["pairs"] >= args.max_pairs
                    else "time-limit-during-rank"
                )
                break
            base_id = len(store.pts)
            apply_geometry(interiors, store, yz_counts)
            provenance.extend(
                ("earlier-L6-interior", base_id + slot, rank, gap, slot)
                for slot in range(len(interiors))
            )
            checkpoint["next_construction_rank"] += 1
            checkpoint["pending_pair_scan"] = None
            completed = checkpoint["next_construction_rank"]
            completed_records = source["selection_records"][:completed]
            checkpoint["audited_source_selection_prefix_sha256"] = (
                rescue.stable_hash(completed_records)
            )
            checkpoint["audited_prefix"] = prefix_record(
                store, yz_counts, completed_records, completed
            )
            run_state["ranks"] += 1
        if checkpoint["next_construction_rank"] == loaded_extent:
            if checkpoint["audited_prefix"] != source["prefix"]:
                raise AssertionError("caught-up cone audit/source prefix drift")
            if source["status"] == "construction-complete-audit-pending" and (
                loaded_extent == context["l6"]["static"]["gaps"]
            ):
                checkpoint["status"] = "complete"
                stop_reason = "complete-terminal-source-audit"
            else:
                checkpoint["status"] = "caught-up-partial-source"
        else:
            checkpoint["status"] = "partial"
        current_snapshot = revalidate_source_prefix(
            args, context, source, loaded_extent
        )
        checkpoint["source_snapshots"].append({
            "loaded": source_snapshot,
            "after_run": current_snapshot,
        })
        checkpoint["last_run"] = {
            "new_pairs": run_state["pairs"],
            "new_completed_ranks": run_state["ranks"],
            "stop_reason": stop_reason,
            "loaded_source_ranks": loaded_extent,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "maximum_resident_bytes": rescue.maximum_resident_bytes(),
            "resource_policy": resource_policy,
        }
        save_checkpoint(args.audit_checkpoint, checkpoint)
        rescue.atomic_json_dump(
            audit_summary(checkpoint, source_snapshot, current_snapshot),
            args.output,
        )
        return checkpoint
    finally:
        producer.close_context(context)


def attach_l6_guard_level(context):
    l6_state = context["l6"]
    context["guard_level"] = {
        "level": 6,
        "parent_word": l6_state["parent_word"],
        "anchors": l6_state["anchors"],
        "schedule": l6_state["schedule"],
        "gaps": l6_state["static"]["gaps"],
        "grandfathered_points": len(l6_state["anchors"]),
        "base_static_state_sha256": l6_state["static"][
            "static_state_sha256"
        ],
        "base_policy": l6_state["static"]["policy"],
        "promoted_seed_lines": None,
    }


def guard_static(context):
    level = context["guard_level"]
    base = common_static(context) if level["level"] == 6 else {
        **cone_scope_fields(level["grandfathered_points"]),
        "L5_producer_sha256": PROCESS_START_L5_PRODUCER_SHA256,
        "L5_input_sha256": level["input_sha256"],
        "base_L5_static_state_sha256": level["base_static_state_sha256"],
    }
    result = {
        **base,
        "mode": "guarded-first-survivor-construction",
        "guarded_level": level["level"],
        "base_policy": level["base_policy"],
        "grandfathered_points": level["grandfathered_points"],
        "promoted_seed_lines": level["promoted_seed_lines"],
        "strengthened_policy": (
            "zero-T AND global empty-yz AND exact fast/reference legality "
            "AND no new secant in either named projective cone"
        ),
        "selection_order": "compact-cache ordinal order",
        "stitch_order": "D2--4 fragile-first, then ordered gap index",
        "terminal_audits_required": [
            "independent ordinary firstness/no-three-collinear audit",
            "independent full new-cone-birth audit",
        ],
    }
    result["static_state_sha256"] = rescue.stable_hash(result)
    return result


def guard_selected_geometry(context, rank, record):
    level = context["guard_level"]
    gap = level["schedule"][rank]
    step = level["parent_word"][gap]
    if (record.get("construction_rank"), record.get("gap"), record.get("step")) != (
        rank, gap, step
    ):
        raise AssertionError("cone-guard schedule identity drift", rank)
    block = context["blocks"][step]
    action = context["action_records"][step]
    if record.get("domain_words") != block["words"] or record.get(
        "static_action_words"
    ) != action["zero"]["set_bits"]:
        raise AssertionError("cone-guard domain/action extent drift", rank)
    ordinal = record["first_survivor_ordinal_1_based"]
    if not l5.action_accepts(
        context["bitset"], action, "zero", ordinal
    ):
        raise AssertionError("cone-guard selected word lost zero-T membership")
    word = producer.cache_word_at_offset(
        context["cache"], block, record["cache_record_offset"]
    )
    if list(word) != record["selected_word"]:
        raise AssertionError("cone-guard selected cache bytes drift", rank)
    start = level["anchors"][gap]
    target = level["anchors"][gap + 1]
    interiors = tuple(rescue.word_interiors(start, word))
    if rescue.endpoint(start, word) != target:
        raise AssertionError("cone-guard selected endpoint drift", rank)
    return gap, step, start, target, word, interiors


def empty_guard_scan(rank, gap, step, block, static_action_count):
    scan = l5.empty_scan(rank, gap, step, block, static_action_count)
    scan.update({
        "cone_birth_rejected": 0,
        "first_cone_birth_rejection_witness": None,
    })
    return scan


def validate_guard_scan(scan, rank, gap, step, block):
    if (scan["construction_rank"], scan["gap"], scan["step"]) != (
        rank, gap, step
    ):
        raise AssertionError("pending cone-guard scan identity drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    if not 1 <= ordinal <= block["words"] + 1 or not (
        block["start"] <= cursor <= block["end"]
    ):
        raise AssertionError("pending cone-guard cursor drift")
    if scan["domain_words_scanned"] != ordinal - 1:
        raise AssertionError("pending cone-guard ordinal/count drift")
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scan["domain_words_scanned"]:
        raise AssertionError("pending cone-guard action partition drift")
    after_digit = scan["action_compatible_seen"] - scan["digit_rejected"]
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != after_digit:
        raise AssertionError("pending cone-guard projection partition drift")
    if scan["exact_legality_rejected"] + scan["cone_birth_rejected"] + len(
        scan["certified_survivors"]
    ) != scan["projection_clean_exact_tested"]:
        raise AssertionError("pending cone-guard exact partition drift")


def finalize_guard_selection(scan, block, action_record, exhaustive):
    if not scan["certified_survivors"]:
        raise GuardNoSurvivor({
            **scan,
            "domain_words": block["words"],
            "exact_full_restricted_domain_exhausted": exhaustive,
        })
    first = scan["certified_survivors"][0]
    return {
        "construction_rank": scan["construction_rank"],
        "gap": scan["gap"],
        "step": scan["step"],
        "domain_words": block["words"],
        "static_action_words": action_record["set_bits"],
        "first_survivor_ordinal_1_based": first["ordinal_1_based"],
        "cache_record_offset": first["cache_record_offset"],
        "selected_word": first["word"],
        "cone_birth_free": True,
        "certified_survivor_count": len(scan["certified_survivors"]),
        "certified_survivors": scan["certified_survivors"],
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
                "cone_birth_rejected",
            )
        },
        "first_projection_rejection_witness": scan[
            "first_projection_rejection_witness"
        ],
        "first_exact_legality_rejection_witness": scan[
            "first_exact_legality_rejection_witness"
        ],
        "first_cone_birth_rejection_witness": scan[
            "first_cone_birth_rejection_witness"
        ],
    }


def select_first_guard(
    context, rank, gap, step, start, target, store, yz_counts, pending,
    deadline,
):
    block = context["blocks"][step]
    full_action = context["action_records"][step]
    action = full_action["zero"]
    scan = copy.deepcopy(pending) if pending is not None else empty_guard_scan(
        rank, gap, step, block, action["set_bits"]
    )
    validate_guard_scan(scan, rank, gap, step, block)
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    memo = {}
    policy = producer.policy_args()
    while ordinal <= block["words"]:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "scanning cone-guarded L6 connector domain"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise GuardDeadline(scan)
        record_offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("cone-guard cache boundary drift", step, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1
        if not l5.action_accepts(
            context["bitset"], full_action, "zero", ordinal
        ):
            scan["action_incompatible_skipped"] += 1
            ordinal += 1
            continue
        scan["action_compatible_seen"] += 1
        interiors = tuple(rescue.word_interiors(start, word))
        if policy.require_digit_simple and not l5.digit_simple(start, interiors):
            scan["digit_rejected"] += 1
            ordinal += 1
            continue
        projection_passed, projection_witness = l5.projection_test(
            policy, start, target, interiors, store, yz_counts
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
        if not rescue.word_legal_fast(
            start, word, store, memo, rescue.MENU
        ):
            scan["exact_legality_rejected"] += 1
            if scan["first_exact_legality_rejection_witness"] is None:
                scan["first_exact_legality_rejection_witness"] = {
                    "ordinal_1_based": ordinal,
                    "word": list(word),
                    **rescue.exact_legality_rejection(interiors, store),
                }
            ordinal += 1
            continue
        if not rescue.word_legal(start, word, store.pts, store.pset, {}):
            raise AssertionError("cone-guard fast/reference legality disagreement")
        if rescue.endpoint(start, word) != target:
            raise AssertionError("cone-guard candidate endpoint drift")
        cone_witness = first_word_cone_birth(
            interiors, store, rank, gap, step,
            context["guard_level"]["grandfathered_points"],
        )
        if cone_witness is not None:
            scan["cone_birth_rejected"] += 1
            if scan["first_cone_birth_rejection_witness"] is None:
                scan["first_cone_birth_rejection_witness"] = {
                    "ordinal_1_based": ordinal,
                    "word": list(word),
                    "witness": cone_witness,
                }
            ordinal += 1
            continue
        scan["certified_survivors"].append({
            "ordinal_1_based": ordinal,
            "cache_record_offset": record_offset,
            "word": list(word),
            "intrinsic_projection_clean": True,
            "global_projection_clean": True,
            "zero_T_accepted": True,
            "ordered_T_accepted": l5.action_accepts(
                context["bitset"], full_action, "ordered", ordinal
            ),
            "cone_birth_free": True,
        })
        ordinal += 1
        scan["next_ordinal_1_based"] = ordinal
        scan["next_cache_cursor"] = cursor
        return finalize_guard_selection(scan, block, action, False)
    scan["next_ordinal_1_based"] = ordinal
    scan["next_cache_cursor"] = cursor
    if cursor != block["end"] or scan["action_compatible_seen"] != action[
        "set_bits"
    ]:
        raise AssertionError("exhausted cone-guard domain drift")
    return finalize_guard_selection(scan, block, action, True)


def initial_guard_checkpoint(context, static):
    level = context["guard_level"]
    store = rescue.Store(level["anchors"])
    yz_counts = Counter(point[1:] for point in level["anchors"])
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "next_construction_rank": 0,
        "selection_records": [],
        "pending_scan": None,
        "prefix": prefix_record(store, yz_counts, [], 0),
        "obstruction": None,
        "last_run": None,
    }


def load_guard_checkpoint(path, context, static):
    path = Path(path)
    if not path.exists():
        return initial_guard_checkpoint(context, static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(checkpoint):
        raise AssertionError("L6 cone-guard checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != static:
        raise AssertionError("L6 cone-guard checkpoint schema/static drift")
    rank = checkpoint["next_construction_rank"]
    if rank != len(checkpoint["selection_records"]) or not (
        0 <= rank <= context["guard_level"]["gaps"]
    ):
        raise AssertionError("L6 cone-guard rank/record drift")
    pending = checkpoint["pending_scan"]
    if pending is not None and pending["construction_rank"] != rank:
        raise AssertionError("L6 cone-guard pending/rank drift")
    return checkpoint


def reconstruct_guard_prefix(context, checkpoint, deadline):
    level = context["guard_level"]
    store = rescue.Store(level["anchors"])
    yz_counts = Counter(point[1:] for point in level["anchors"])
    for rank, record in enumerate(checkpoint["selection_records"]):
        if rank % RECONSTRUCT_CHECK_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing cone-guarded L6 prefix"
        ):
            raise GuardDeadline(checkpoint["pending_scan"])
        _gap, _step, _start, _target, _word, interiors = guard_selected_geometry(
            context, rank, record
        )
        if record.get("cone_birth_free") is not True:
            raise AssertionError("guard record lacks cone-free commitment", rank)
        apply_geometry(interiors, store, yz_counts)
    observed = prefix_record(
        store, yz_counts, checkpoint["selection_records"],
        checkpoint["next_construction_rank"],
    )
    if observed != checkpoint["prefix"]:
        raise AssertionError("L6 cone-guard prefix commitment drift")
    pending = checkpoint["pending_scan"]
    if pending is not None:
        rank = checkpoint["next_construction_rank"]
        gap = level["schedule"][rank]
        step = level["parent_word"][gap]
        validate_guard_scan(
            pending, rank, gap, step, context["blocks"][step]
        )
    return store, yz_counts


def run_guard(args, resource_policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = producer.open_context(args)
    try:
        attach_l6_guard_level(context)
        static = guard_static(context)
        checkpoint = load_guard_checkpoint(
            args.guard_checkpoint, context, static
        )
        try:
            store, yz_counts = reconstruct_guard_prefix(
                context, checkpoint, deadline
            )
        except GuardDeadline:
            checkpoint["last_run"] = {
                "new_gaps": 0,
                "stop_reason": "time-limit-during-prefix-reconstruction",
                "resource_policy": resource_policy,
            }
            save_checkpoint(args.guard_checkpoint, checkpoint)
            return checkpoint
        if checkpoint["status"] in {
            "hard-jam", "construction-complete-audit-pending"
        }:
            return checkpoint
        added = 0
        stop_reason = "new-gap-limit"
        level = context["guard_level"]
        while checkpoint["next_construction_rank"] < level["gaps"]:
            if added >= args.max_new_gaps:
                break
            if rescue.enforce_runtime(deadline, "between cone-guarded L6 stitches"):
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            gap = level["schedule"][rank]
            step = level["parent_word"][gap]
            start = level["anchors"][gap]
            target = level["anchors"][gap + 1]
            try:
                record = select_first_guard(
                    context, rank, gap, step, start, target, store,
                    yz_counts, checkpoint["pending_scan"], deadline,
                )
            except GuardDeadline as reached:
                checkpoint["pending_scan"] = reached.pending
                stop_reason = "time-limit-during-domain-scan"
                break
            except GuardNoSurvivor as failure:
                checkpoint["pending_scan"] = None
                checkpoint["status"] = "hard-jam"
                checkpoint["obstruction"] = failure.details
                stop_reason = "two-cone-guard-hard-jam"
                break
            word = tuple(record["selected_word"])
            interiors = tuple(rescue.word_interiors(start, word))
            checkpoint["selection_records"].append(record)
            apply_geometry(interiors, store, yz_counts)
            checkpoint["next_construction_rank"] += 1
            checkpoint["pending_scan"] = None
            checkpoint["prefix"] = prefix_record(
                store, yz_counts, checkpoint["selection_records"],
                checkpoint["next_construction_rank"],
            )
            added += 1
            if added % producer.CHECKPOINT_INTERVAL == 0:
                checkpoint["last_run"] = {
                    "intermediate": True,
                    "new_gaps": added,
                    "resource_policy": resource_policy,
                }
                save_checkpoint(args.guard_checkpoint, checkpoint)
        if checkpoint["next_construction_rank"] == level["gaps"]:
            checkpoint["status"] = "construction-complete-audit-pending"
            stop_reason = "construction-complete"
        checkpoint["prefix"] = prefix_record(
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
        save_checkpoint(args.guard_checkpoint, checkpoint)
        return checkpoint
    finally:
        producer.close_context(context)


def open_l5_guard_context(args):
    """Open the pinned inherited-L4 anchor skeleton used by the L5 replay."""
    input_sha256 = l5.verify_inputs(args)
    _metadata, blocks = rescue.load_metadata(args.metadata)
    parent_word, anchors, schedule = rescue.load_l5_state()
    if len(anchors) != EXPECTED_L5_GRANDFATHERED_POINTS:
        raise AssertionError("L5 inherited anchor extent drift")
    lattice_result, sidecar = l5.load_lattice_result(args.lattice_result)
    cache_handle = Path(args.cache).open("rb")
    bitset_handle = Path(args.lattice_bitsets).open("rb")
    cache = bitset = None
    try:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        bitset = mmap.mmap(
            bitset_handle.fileno(), 0, access=mmap.ACCESS_READ
        )
        if cache[:len(rescue.CACHE_MAGIC)] != rescue.CACHE_MAGIC:
            raise AssertionError("L5 cone-guard compact-cache magic drift")
        action_records = l5.parse_bitsets(bitset, sidecar, blocks)
        promoted = promoted_seed_cone_lines(anchors)
        if len(promoted) != EXPECTED_L5_PROMOTED_SEED_LINES:
            raise AssertionError(
                "L5 inherited seed-cone line count drift", len(promoted)
            )
        promoted_record = {
            "count": len(promoted),
            "line_stream_sha256": rescue.stable_hash(promoted),
            "lines": list(promoted),
            "meaning": (
                "finite exact affine Pluecker state inherited from the L4 "
                "anchor skeleton; these base-base lines are allowed"
            ),
        }
        base_fields = {
            "level": 5,
            "input_sha256": input_sha256,
            "parent_word_sha256": hashlib.sha256(
                bytes(parent_word)
            ).hexdigest(),
            "anchor_stream_sha256": rescue.stable_hash(anchors),
            "schedule_sha256": rescue.stable_hash(schedule),
            "gaps": len(parent_word),
            "anchors": len(anchors),
        }
        base_fields["static_state_sha256"] = rescue.stable_hash(base_fields)
        context = {
            "input_sha256": input_sha256,
            "lattice_result": lattice_result,
            "blocks": blocks,
            "cache_handle": cache_handle,
            "bitset_handle": bitset_handle,
            "cache": cache,
            "bitset": bitset,
            "action_records": action_records,
            "guard_level": {
                "level": 5,
                "parent_word": parent_word,
                "anchors": anchors,
                "schedule": schedule,
                "gaps": len(parent_word),
                "grandfathered_points": len(anchors),
                "base_static_state_sha256": base_fields[
                    "static_state_sha256"
                ],
                "base_policy": {
                    "action_channel": "zero",
                    "projection_policy": "global-empty",
                    "require_digit_simple": False,
                    "survivor_certificate_target": 1,
                },
                "input_sha256": input_sha256,
                "promoted_seed_lines": promoted_record,
            },
        }
        return context
    except BaseException:
        if bitset is not None:
            bitset.close()
        if cache is not None:
            cache.close()
        bitset_handle.close()
        cache_handle.close()
        raise


def close_l5_guard_context(context):
    context["bitset"].close()
    context["cache"].close()
    context["bitset_handle"].close()
    context["cache_handle"].close()


def run_l5_guard(args, resource_policy):
    """Smallest inductive guard test: inherited L4 anchors -> guarded L5."""
    started = time.monotonic()
    deadline = started + args.max_seconds
    context = open_l5_guard_context(args)
    checkpoint_path = args.l5_guard_checkpoint
    try:
        static = guard_static(context)
        checkpoint = load_guard_checkpoint(
            checkpoint_path, context, static
        )
        try:
            store, yz_counts = reconstruct_guard_prefix(
                context, checkpoint, deadline
            )
        except GuardDeadline:
            checkpoint["last_run"] = {
                "new_gaps": 0,
                "stop_reason": "time-limit-during-prefix-reconstruction",
                "resource_policy": resource_policy,
            }
            save_checkpoint(checkpoint_path, checkpoint)
            return checkpoint
        if checkpoint["status"] in {
            "hard-jam", "construction-complete-audit-pending"
        }:
            return checkpoint
        level = context["guard_level"]
        added = 0
        stop_reason = "new-gap-limit"
        while checkpoint["next_construction_rank"] < level["gaps"]:
            if added >= args.max_new_gaps:
                break
            if rescue.enforce_runtime(
                deadline, "between cone-guarded L5 stitches"
            ):
                stop_reason = "time-limit"
                break
            rank = checkpoint["next_construction_rank"]
            gap = level["schedule"][rank]
            step = level["parent_word"][gap]
            start = level["anchors"][gap]
            target = level["anchors"][gap + 1]
            try:
                record = select_first_guard(
                    context, rank, gap, step, start, target, store,
                    yz_counts, checkpoint["pending_scan"], deadline,
                )
            except GuardDeadline as reached:
                checkpoint["pending_scan"] = reached.pending
                stop_reason = "time-limit-during-domain-scan"
                break
            except GuardNoSurvivor as failure:
                checkpoint["pending_scan"] = None
                checkpoint["status"] = "hard-jam"
                checkpoint["obstruction"] = failure.details
                stop_reason = "two-cone-guard-hard-jam"
                break
            word = tuple(record["selected_word"])
            interiors = tuple(rescue.word_interiors(start, word))
            checkpoint["selection_records"].append(record)
            apply_geometry(interiors, store, yz_counts)
            checkpoint["next_construction_rank"] += 1
            checkpoint["pending_scan"] = None
            checkpoint["prefix"] = prefix_record(
                store, yz_counts, checkpoint["selection_records"],
                checkpoint["next_construction_rank"],
            )
            added += 1
            if added % l5.CHECKPOINT_INTERVAL == 0:
                checkpoint["last_run"] = {
                    "intermediate": True,
                    "new_gaps": added,
                    "resource_policy": resource_policy,
                }
                save_checkpoint(checkpoint_path, checkpoint)
        if checkpoint["next_construction_rank"] == level["gaps"]:
            checkpoint["status"] = "construction-complete-audit-pending"
            stop_reason = "construction-complete"
        checkpoint["prefix"] = prefix_record(
            store, yz_counts, checkpoint["selection_records"],
            checkpoint["next_construction_rank"],
        )
        checkpoint["last_run"] = {
            "new_gaps": added,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "maximum_resident_bytes": rescue.maximum_resident_bytes(),
            "resource_policy": resource_policy,
            "promoted_seed_cone_lines": EXPECTED_L5_PROMOTED_SEED_LINES,
        }
        save_checkpoint(checkpoint_path, checkpoint)
        return checkpoint
    finally:
        close_l5_guard_context(context)


def self_check():
    first = (3, -3, 1)
    second = (55, 34, 18)
    if matched_spectra(first) != ("11/3",):
        raise AssertionError("11/3 synthetic cone witness drift")
    if matched_spectra(second) != ("348/275",):
        raise AssertionError("348/275 synthetic cone witness drift")
    if matched_spectra((1, 0, 0)):
        raise AssertionError("non-cone direction misclassified")
    transformed_first = producer.apply(producer.M_BAL3, first)
    transformed_second = producer.apply(producer.M_BAL3, second)
    if matched_spectra(transformed_first) != ("11/3",) or matched_spectra(
        transformed_second
    ) != ("348/275",):
        raise AssertionError("projective cone lost M invariance")
    store = rescue.Store(((0, 0, 0),))
    witness = first_word_cone_birth(((3, -3, 1),), store, 0, 0, 0)
    if witness is None or witness["classification"] != "old-new":
        raise AssertionError("synthetic old-new cone birth missed")
    same_word = first_word_cone_birth(
        ((7, 4, 2), (10, 1, 3)), rescue.Store(((100, 0, 0),)),
        0, 0, 0,
    )
    if same_word is None or same_word["classification"] != (
        "same-word-new-new"
    ):
        raise AssertionError("synthetic same-word cone birth missed")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": PROCESS_START_PRODUCER_SHA256,
        "spectra": [dict(item) for item in SPECTRA],
        "grandfathered_base_points": GRANDFATHERED_POINTS,
        "old_new_tested": True,
        "same_word_new_new_tested": True,
        "M_projective_invariance_tested": True,
        "large_artifacts_opened": False,
    }


def estimate():
    return {
        "status": "prepared exact two-cone L6 birth audit/guard prototype",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "producer_sha256": PROCESS_START_PRODUCER_SHA256,
        "source": str(Path(DEFAULT_SOURCE).resolve()),
        "audit_checkpoint": str(DEFAULT_AUDIT_CHECKPOINT.resolve()),
        "guard_checkpoint": str(DEFAULT_GUARD_CHECKPOINT.resolve()),
        "L5_guard_checkpoint": str(DEFAULT_L5_GUARD_CHECKPOINT.resolve()),
        "grandfathered_base_points": GRANDFATHERED_POINTS,
        "base_base_secants_allowed": True,
        "classified_births": ["old-new", "same-word-new-new"],
        "spectra": [dict(item) for item in SPECTRA],
        "endpoint_cutoff": None,
        "distance_cutoff": None,
        "guard_base_policy_retained": (
            "zero-T AND global empty-yz AND exact fast/reference legality"
        ),
        "smallest_inductive_guard_test": {
            "transition": "inherited L4 anchors -> guarded L5 connectors",
            "grandfathered_anchor_points": EXPECTED_L5_GRANDFATHERED_POINTS,
            "expected_promoted_seed_cone_lines": (
                EXPECTED_L5_PROMOTED_SEED_LINES
            ),
            "new_birth_rule": (
                "reject every old-new or same-word-new-new secant in either "
                "named cone"
            ),
        },
        "scope_warning": "all other projective directions and affine moments remain open",
        "resumable_pair_cursor": True,
        "resumable_guard_domain_cursor": True,
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "large_artifacts_opened": False,
    }


def add_context_arguments(parser):
    parser.add_argument(
        "--parent-source", default=str(producer.DEFAULT_PARENT_SOURCE)
    )
    parser.add_argument(
        "--parent-terminal", default=str(producer.DEFAULT_PARENT_TERMINAL)
    )
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(l5.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(l5.DEFAULT_LATTICE_BITSETS)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=(
            "estimate", "self-check", "audit", "guard-run",
            "guard-l5-run",
        )
    )
    add_context_arguments(parser)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument(
        "--audit-checkpoint", default=str(DEFAULT_AUDIT_CHECKPOINT)
    )
    parser.add_argument("--output", default=str(DEFAULT_AUDIT_OUTPUT))
    parser.add_argument(
        "--guard-checkpoint", default=str(DEFAULT_GUARD_CHECKPOINT)
    )
    parser.add_argument(
        "--l5-guard-checkpoint", default=str(DEFAULT_L5_GUARD_CHECKPOINT)
    )
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-pairs", type=int, default=5_000_000)
    parser.add_argument("--max-ranks", type=int, default=500)
    parser.add_argument("--max-new-gaps", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,600]")
    if not 1 <= args.max_pairs <= HARD_MAX_PAIRS:
        raise ValueError("max-pairs outside [1,50000000]")
    if not 1 <= args.max_ranks <= HARD_MAX_RANKS:
        raise ValueError("max-ranks outside [1,1000]")
    if not 1 <= args.max_new_gaps <= HARD_MAX_GAPS:
        raise ValueError("max-new-gaps outside [1,1000]")
    resource_policy = legacy.resource_policy(
        enforce=args.mode in {"audit", "guard-run", "guard-l5-run"}
    )
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    elif args.mode == "audit":
        checkpoint = run_audit(args, resource_policy)
        result = {
            "status": checkpoint["status"],
            "audit_checkpoint": str(Path(args.audit_checkpoint).resolve()),
            "audit_checkpoint_sha256": rescue.file_sha256(
                args.audit_checkpoint
            ),
            "summary": str(Path(args.output).resolve()),
            "summary_sha256": rescue.file_sha256(args.output),
            "next_construction_rank": checkpoint[
                "next_construction_rank"
            ],
            "last_run": checkpoint["last_run"],
            "earliest_new_cone_birth": checkpoint[
                "earliest_new_cone_birth"
            ],
        }
    elif args.mode == "guard-run":
        checkpoint = run_guard(args, resource_policy)
        result = {
            "status": checkpoint["status"],
            "guard_checkpoint": str(Path(args.guard_checkpoint).resolve()),
            "guard_checkpoint_sha256": rescue.file_sha256(
                args.guard_checkpoint
            ),
            "next_construction_rank": checkpoint[
                "next_construction_rank"
            ],
            "last_run": checkpoint["last_run"],
            "obstruction": checkpoint.get("obstruction"),
        }
    else:
        checkpoint = run_l5_guard(args, resource_policy)
        result = {
            "status": checkpoint["status"],
            "guarded_level": 5,
            "promoted_seed_cone_lines": EXPECTED_L5_PROMOTED_SEED_LINES,
            "guard_checkpoint": str(
                Path(args.l5_guard_checkpoint).resolve()
            ),
            "guard_checkpoint_sha256": rescue.file_sha256(
                args.l5_guard_checkpoint
            ),
            "next_construction_rank": checkpoint[
                "next_construction_rank"
            ],
            "last_run": checkpoint["last_run"],
            "obstruction": checkpoint.get("obstruction"),
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
