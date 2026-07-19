#!/usr/bin/env python3
"""Fail-closed independent audit for the guarded lattice-T L6 replay.

This checker is intentionally locked until the guarded-L6 constructor reaches
``construction-complete-audit-pending`` and its source/checkpoint identities
are frozen below.  Estimate and synthetic self-check modes open no large
artifacts; audit mode refuses to start while any terminal pin is pending.

The guarded construction checkpoint is read-only.  For each fragile-order L6
stitch, this checker independently rescans compact-cache ordinals one through
the stored winner under the exact conjunction

    zero-T
    AND globally fresh (y,z) fibres
    AND optimized/reference exact legality
    AND no new secant in either named projective cone.

Fresh legality memos and a fresh cone-pair scan are used.  Constructor
rejection counters, witnesses, legality caches, and reconstructed prefixes are
not proof inputs.  An earlier guarded survivor or a fast/reference mismatch is
fatal.

After firstness, the single selected walk is reconstructed in natural gap
order.  A resumable all-pairs pass verifies ordinary no-three-collinear
legality and the two-cone condition.  Cone pairs are permitted only when both
endpoints belong to the inherited L6 anchor skeleton.  That inherited skeleton
is independently censused into exact affine Pluecker line keys; its final
count and digest must be pinned before audit mode can unlock.

The resulting certificate is finite and controls only J=11/3 and J=348/275
on one guarded L6 orbit.  It is not a uniform connector-availability theorem,
a classification of every recurrent far-secant family, or an infinite walk.
The inherited L6 anchors are the ``M_BAL3`` image of the terminal-audited
primary L5 walk opened by ``lattice_t_l6_continuation.py``.  They are not the
separately constructed two-cone-guarded L5 walk, so the two finite guarded
experiments are not consecutive levels of one realized orbit.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from collections import Counter
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import lattice_t_l6_continuation as producer  # noqa: E402


rescue = producer.rescue
l5 = producer.l5_producer
legacy = producer.legacy_l6

DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L6-cone-guard-v1.json")
DEFAULT_AUDIT_CHECKPOINT = Path(
    "/tmp/lattice-T-chronological-L6-cone-guard-audit-checkpoint-v1.json"
)
DEFAULT_OUTPUT = Path(
    "/tmp/lattice-T-chronological-L6-cone-guard-audit-v1.json"
)
DEFAULT_SUMMARY = (
    ROOT / "design" / "lattice-T-L6-cone-guard-audit-summary.json"
)
GUARD_CHECKER = ROOT / "design" / "lattice_t_l6_cone_birth_guard.py"

# Freeze every value in this block only after guarded L6 construction is
# terminal.  Keeping the constructor source pin pending prevents a later
# correction from being accidentally paired with an earlier checkpoint.
EXPECTED_GUARD_CHECKER_SHA256 = "PENDING"
EXPECTED_PRODUCER_SHA256 = "PENDING"
EXPECTED_L5_PRODUCER_SHA256 = "PENDING"
EXPECTED_RESCUE_SHA256 = "PENDING"
EXPECTED_SOURCE_SHA256 = "PENDING"
EXPECTED_SOURCE_BYTES = 0
EXPECTED_SOURCE_PAYLOAD_SHA256 = "PENDING"
EXPECTED_SOURCE_STATIC_SHA256 = "PENDING"
EXPECTED_SOURCE_PREFIX_SHA256 = "PENDING"
EXPECTED_SOURCE_SELECTION_SHA256 = "PENDING"
EXPECTED_SOURCE_MAX_FIRST_ORDINAL = 0
EXPECTED_POINTS = 0
EXPECTED_POINT_SET_SHA256 = "PENDING"
EXPECTED_FINAL_YZ_SHA256 = "PENDING"
EXPECTED_FINAL_DOUBLE_FIBRE_SHA256 = "PENDING"
EXPECTED_PROMOTED_LINES = 0
EXPECTED_PROMOTED_LINE_STREAM_SHA256 = "PENDING"

EXPECTED_GAPS = producer.EXPECTED_PARENT_STEPS
EXPECTED_ANCHORS = producer.EXPECTED_PARENT_POINTS
SPECTRA = (
    ("11/3", 11, 3),
    ("348/275", 348, 275),
)
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 25
HARD_MAX_SECONDS = 600.0
HARD_MAX_WORK_ITEMS = 2_000
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())
PRIMARY_L5_LINEAGE = (
    "the inherited L6 anchors are the M_BAL3 image of the terminal-audited "
    "primary L5 walk opened by lattice_t_l6_continuation.py, not the "
    "separately constructed two-cone-guarded L5 walk"
)


class DeadlineReached(Exception):
    def __init__(self, pending=None):
        super().__init__(pending)
        self.pending = pending


def terminal_string_pins():
    return {
        "guard_checker": EXPECTED_GUARD_CHECKER_SHA256,
        "producer": EXPECTED_PRODUCER_SHA256,
        "L5_producer": EXPECTED_L5_PRODUCER_SHA256,
        "rescue": EXPECTED_RESCUE_SHA256,
        "source_file": EXPECTED_SOURCE_SHA256,
        "source_payload": EXPECTED_SOURCE_PAYLOAD_SHA256,
        "source_static": EXPECTED_SOURCE_STATIC_SHA256,
        "source_prefix": EXPECTED_SOURCE_PREFIX_SHA256,
        "source_selection": EXPECTED_SOURCE_SELECTION_SHA256,
        "point_set": EXPECTED_POINT_SET_SHA256,
        "final_yz": EXPECTED_FINAL_YZ_SHA256,
        "final_double_fibres": EXPECTED_FINAL_DOUBLE_FIBRE_SHA256,
        "promoted_line_stream": EXPECTED_PROMOTED_LINE_STREAM_SHA256,
    }


def terminal_pins_finalized():
    return (
        all(
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
            for value in terminal_string_pins().values()
        )
        and EXPECTED_SOURCE_BYTES > 0
        and EXPECTED_SOURCE_MAX_FIRST_ORDINAL > 0
        and EXPECTED_POINTS > EXPECTED_ANCHORS
        and EXPECTED_PROMOTED_LINES > 0
    )


def ensure_terminal_pins():
    if not terminal_pins_finalized():
        raise RuntimeError(
            "guarded L6 terminal pins are not finalized; audit is locked",
            terminal_string_pins(),
        )


def source_pins():
    return {
        "file_sha256": EXPECTED_SOURCE_SHA256,
        "bytes": EXPECTED_SOURCE_BYTES,
        "payload_sha256": EXPECTED_SOURCE_PAYLOAD_SHA256,
        "static_state_sha256": EXPECTED_SOURCE_STATIC_SHA256,
        "prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
        "maximum_first_survivor_ordinal": (
            EXPECTED_SOURCE_MAX_FIRST_ORDINAL
        ),
        "placed_points": EXPECTED_POINTS,
    }


def assert_checker_unchanged():
    if rescue.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ):
        raise RuntimeError("guarded L6 auditor changed during execution")


def verify_dependencies():
    ensure_terminal_pins()
    observed = {
        "guard_checker": rescue.file_sha256(GUARD_CHECKER),
        "producer": rescue.file_sha256(Path(producer.__file__).resolve()),
        "L5_producer": rescue.file_sha256(Path(l5.__file__).resolve()),
        "rescue": rescue.file_sha256(Path(rescue.__file__).resolve()),
    }
    expected = {
        "guard_checker": EXPECTED_GUARD_CHECKER_SHA256,
        "producer": EXPECTED_PRODUCER_SHA256,
        "L5_producer": EXPECTED_L5_PRODUCER_SHA256,
        "rescue": EXPECTED_RESCUE_SHA256,
    }
    if observed != expected:
        raise AssertionError("pinned guarded-L6 dependency drift", expected, observed)
    return observed


def resolved_path(path):
    return str(Path(path).resolve())


def audit_paths(args):
    return {
        "source": resolved_path(args.source),
        "audit_checkpoint": resolved_path(args.audit_checkpoint),
        "output": resolved_path(args.output),
        "summary": resolved_path(args.summary),
    }


def ensure_audit_paths_disjoint(args):
    """Keep every writable artifact distinct from each other and all inputs."""
    writes = {
        "audit_checkpoint": resolved_path(args.audit_checkpoint),
        "output": resolved_path(args.output),
        "summary": resolved_path(args.summary),
    }
    immutable = {
        "source": resolved_path(args.source),
        "parent_source": resolved_path(args.parent_source),
        "parent_terminal": resolved_path(args.parent_terminal),
        "metadata": resolved_path(args.metadata),
        "cache": resolved_path(args.cache),
        "lattice_result": resolved_path(args.lattice_result),
        "lattice_bitsets": resolved_path(args.lattice_bitsets),
        "audit_checker": resolved_path(Path(__file__)),
        "guard_checker": resolved_path(GUARD_CHECKER),
        "producer": resolved_path(Path(producer.__file__)),
        "L5_producer": resolved_path(Path(l5.__file__)),
        "rescue": resolved_path(Path(rescue.__file__)),
    }
    owners = {}
    for name, path in writes.items():
        prior = owners.get(path)
        if prior is not None:
            raise ValueError(
                "guarded-L6 audit writable paths are not disjoint",
                prior, name, path,
            )
        owners[path] = name
    for write_name, write_path in writes.items():
        for input_name, input_path in immutable.items():
            if write_path == input_path:
                raise ValueError(
                    "guarded-L6 audit output/checkpoint aliases an input",
                    write_name, input_name, write_path,
                )
    return {
        "writable": writes,
        "immutable": immutable,
    }


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def primitive_direction(vector):
    divisor = gcd(gcd(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    if divisor == 0:
        raise AssertionError("zero displacement in guarded-L6 direction audit")
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
    """Independently enumerate exact cone lines in the inherited anchors."""
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
                    "inherited L6 anchors have three points on one cone line"
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
    """Return the first old-new or same-word-new-new target-cone pair."""
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


def verify_source(path, base_static):
    ensure_terminal_pins()
    path = Path(path)
    if path.stat().st_size != EXPECTED_SOURCE_BYTES:
        raise AssertionError("guarded L6 source byte-size drift")
    observed = rescue.file_sha256(path)
    if observed != EXPECTED_SOURCE_SHA256:
        raise AssertionError("guarded L6 source file drift", observed)
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != rescue.stable_hash(source) or internal != (
        EXPECTED_SOURCE_PAYLOAD_SHA256
    ):
        raise AssertionError("guarded L6 source payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("guarded L6 source schema drift")
    if source.get("status") != "construction-complete-audit-pending":
        raise AssertionError("guarded L6 source is not audit-ready")
    if source.get("obstruction") is not None or source.get(
        "pending_scan"
    ) is not None:
        raise AssertionError("completed guarded L6 source retains failure state")
    records = source.get("selection_records")
    if not isinstance(records, list) or len(records) != EXPECTED_GAPS or (
        source.get("next_construction_rank") != EXPECTED_GAPS
    ):
        raise AssertionError("guarded L6 source extent drift")

    static = source.get("static", {})
    static_copy = copy.deepcopy(static)
    static_hash = static_copy.pop("static_state_sha256", None)
    if static_hash != rescue.stable_hash(static_copy) or static_hash != (
        EXPECTED_SOURCE_STATIC_SHA256
    ):
        raise AssertionError("guarded L6 source static-state drift")
    required_static = {
        "checker_sha256": EXPECTED_GUARD_CHECKER_SHA256,
        "producer_sha256": EXPECTED_PRODUCER_SHA256,
        "mode": "guarded-first-survivor-construction",
        "guarded_level": 6,
        "base_policy": base_static["policy"],
        "grandfathered_points": EXPECTED_ANCHORS,
        "grandfathered_base_points": EXPECTED_ANCHORS,
        "base_L6_static_state_sha256": base_static["static_state_sha256"],
        "parent_terminal_sha256": producer.EXPECTED_PARENT_TERMINAL_SHA256,
        "promoted_seed_lines": None,
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
    for key, expected in required_static.items():
        if static.get(key) != expected:
            raise AssertionError("guarded L6 static policy drift", key)
    spectra = [{
        "label": label,
        "numerator": numerator,
        "denominator": denominator,
        "polynomial": (
            f"{denominator}*(3*y^2-y*z+3*z^2)-{numerator}*r^2"
        ),
    } for label, numerator, denominator in SPECTRA]
    if static.get("spectra") != spectra:
        raise AssertionError("guarded L6 target spectra drift")

    prefix = source.get("prefix", {})
    pinned_prefix = {
        "next_construction_rank": EXPECTED_GAPS,
        "prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
        "placed_point_count": EXPECTED_POINTS,
        "point_set_sha256": EXPECTED_POINT_SET_SHA256,
        "yz_occupancy_stream_sha256": EXPECTED_FINAL_YZ_SHA256,
        "doubled_fibre_stream_sha256": EXPECTED_FINAL_DOUBLE_FIBRE_SHA256,
    }
    for key, expected in pinned_prefix.items():
        if prefix.get(key) != expected:
            raise AssertionError("guarded L6 final-prefix drift", key)
    if rescue.stable_hash(records) != EXPECTED_SOURCE_SELECTION_SHA256:
        raise AssertionError("guarded L6 selection record stream drift")
    maximum = max(
        record["first_survivor_ordinal_1_based"] for record in records
    )
    if maximum != EXPECTED_SOURCE_MAX_FIRST_ORDINAL:
        raise AssertionError("guarded L6 maximum first ordinal drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def open_context(args):
    ensure_terminal_pins()
    dependencies = verify_dependencies()
    context = producer.open_context(args)
    try:
        l6_state = context["l6"]
        source, source_snapshot = verify_source(
            args.source, l6_state["static"]
        )
        context.update({
            "guard_source": source,
            "guard_source_snapshot": source_snapshot,
            "guard_dependencies": dependencies,
        })
        return context
    except BaseException:
        producer.close_context(context)
        raise


def cache_word_at_offset(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("guarded-L6 cache offset outside connector block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("guarded-L6 cache record boundary drift")
    return tuple(cache[offset + 1:end])


def action_accepts(bitset, record, channel, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("guarded-L6 action ordinal outside domain")
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
            raise AssertionError("audited guarded-L6 winner reuses yz fibre")
        yz_counts[fibre] += 1
    store.add_many(interiors)


def prefix_commitment(store, yz_counts, records, rank):
    """Independent copy of the guarded constructor's prefix commitment."""
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


def audit_static(context, args):
    fields = {
        "audit_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "pinned_dependencies": context["guard_dependencies"],
        "source_checkpoint": context["guard_source_snapshot"],
        "source_pins": source_pins(),
        "audit_paths": audit_paths(args),
        "base_L6_static_state_sha256": context["l6"]["static"][
            "static_state_sha256"
        ],
        "primary_L5_lineage": PRIMARY_L5_LINEAGE,
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
            "count": EXPECTED_PROMOTED_LINES,
            "line_stream_sha256": EXPECTED_PROMOTED_LINE_STREAM_SHA256,
            "verification": (
                "independently reconstructed during the resumable terminal "
                "all-pairs scan"
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


def verify_terminal_artifact(
    path, snapshot, context, checkpoint, description,
):
    """Reopen one terminal artifact and bind it to this exact audit state."""
    path = Path(path).resolve()
    if not path.is_file():
        raise AssertionError(
            "guarded-L6 terminal artifact is missing", description, str(path)
        )
    observed_snapshot = {
        "path": str(path),
        "sha256": rescue.file_sha256(path),
        "bytes": path.stat().st_size,
        "payload_sha256": snapshot.get("payload_sha256"),
    }
    if observed_snapshot != snapshot:
        raise AssertionError(
            "guarded-L6 terminal artifact snapshot drift",
            description, snapshot, observed_snapshot,
        )
    with path.open() as handle:
        terminal = json.load(handle)
    internal = terminal.pop("terminal_payload_sha256", None)
    if internal != rescue.stable_hash(terminal) or internal != snapshot.get(
        "payload_sha256"
    ):
        raise AssertionError(
            "guarded-L6 terminal artifact payload drift", description
        )
    terminal["terminal_payload_sha256"] = internal
    expected_checker = {
        "path": "design/lattice_t_l6_cone_guard_audit.py",
        "sha256": PROCESS_START_CHECKER_SHA256,
        "unchanged_during_audit": True,
    }
    if terminal.get("schema_version") != SCHEMA_VERSION or terminal.get(
        "status"
    ) != "exact independent guarded-L6 finite certificate":
        raise AssertionError(
            "guarded-L6 terminal artifact schema/status drift", description
        )
    if terminal.get("checker") != expected_checker:
        raise AssertionError(
            "guarded-L6 terminal artifact checker drift", description
        )
    expected_bindings = {
        "source_checkpoint": context["guard_source_snapshot"],
        "source_pins": source_pins(),
        "pinned_dependencies": context["guard_dependencies"],
        "static_state_sha256": checkpoint["static"]["static_state_sha256"],
    }
    for key, expected in expected_bindings.items():
        if terminal.get(key) != expected:
            raise AssertionError(
                "guarded-L6 terminal artifact provenance drift",
                description, key,
            )
    commitments = terminal.get("commitments", {})
    expected_commitments = {
        "source_prefix_state_sha256": EXPECTED_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": EXPECTED_SOURCE_SELECTION_SHA256,
        "audit_record_stream_sha256": checkpoint[
            "audit_record_stream_sha256"
        ],
        "promoted_seed_line_stream_sha256": (
            EXPECTED_PROMOTED_LINE_STREAM_SHA256
        ),
        "final_point_set_sha256": EXPECTED_POINT_SET_SHA256,
        "final_yz_occupancy_sha256": EXPECTED_FINAL_YZ_SHA256,
        "final_double_fibre_sha256": EXPECTED_FINAL_DOUBLE_FIBRE_SHA256,
    }
    for key, expected in expected_commitments.items():
        if commitments.get(key) != expected:
            raise AssertionError(
                "guarded-L6 terminal artifact commitment drift",
                description, key,
            )
    verifier = checkpoint["ordered_verifier"]
    records = context["guard_source"]["selection_records"]
    result = terminal.get("result", {})
    expected_result = {
        "construction_completed": True,
        "gaps": EXPECTED_GAPS,
        "anchors": EXPECTED_ANCHORS,
        "points": EXPECTED_POINTS,
        "first_survivor_audit_completed": True,
        "selected_reference_legality_verified_at_every_stitch": True,
        "fast_reference_agreement_verified_for_every_exact_test": True,
        "global_empty_yz_verified_at_every_stitch": True,
        "final_no_new_yz_coincidence": True,
        "independent_ordered_no_three_collinear_verified": True,
        "promoted_base_cone_lines": EXPECTED_PROMOTED_LINES,
        "new_target_cone_secants": 0,
        "target_cone_pair_matches_in_terminal_pair_scan": verifier[
            "target_cone_pair_matches"
        ],
        "ordered_pair_checks": verifier["pair_checks"],
        "maximum_first_survivor_ordinal_1_based": max(
            record["first_survivor_ordinal_1_based"] for record in records
        ),
        "sum_first_survivor_ordinals": sum(
            record["first_survivor_ordinal_1_based"] for record in records
        ),
        "independently_recounted_cone_rejections": sum(
            record["cone_birth_rejections"]
            for record in checkpoint["audit_records"]
        ),
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            raise AssertionError(
                "guarded-L6 terminal artifact result drift",
                description, key,
            )
    return terminal


def verify_terminal_artifacts(args, context, checkpoint):
    expected_paths = audit_paths(args)
    snapshots = {
        "output": checkpoint["terminal_output"],
        "summary": checkpoint["terminal_summary"],
    }
    terminals = {}
    for name in ("output", "summary"):
        snapshot = snapshots[name]
        if not isinstance(snapshot, dict) or snapshot.get("path") != (
            expected_paths[name]
        ):
            raise AssertionError(
                "guarded-L6 terminal target drift", name,
                expected_paths[name], snapshot,
            )
        terminals[name] = verify_terminal_artifact(
            expected_paths[name], snapshot, context, checkpoint, name
        )
    if terminals["output"] != terminals["summary"] or snapshots[
        "output"
    ]["sha256"] != snapshots["summary"]["sha256"]:
        raise AssertionError("guarded-L6 terminal output/summary divergence")
    return terminals["output"]


def initial_checkpoint(context, static):
    anchors = context["l6"]["anchors"]
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
            store, yz_counts,
            context["guard_source"]["selection_records"], 0,
        ),
        "ordered_verifier": {
            "next_point": 0,
            "total_points": None,
            "pair_checks": 0,
            "target_cone_pair_matches": 0,
            "promoted_line_records": [],
            "promoted_line_record_stream_sha256": rescue.stable_hash([]),
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
        raise AssertionError("guarded-L6 audit checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != static:
        raise AssertionError("guarded-L6 audit schema/static drift")
    if checkpoint.get("status") not in {"partial", "complete"}:
        raise AssertionError("guarded-L6 audit status drift")
    cursor = checkpoint["firstness_audited_through_rank"]
    if not 0 <= cursor <= EXPECTED_GAPS or len(
        checkpoint["audit_records"]
    ) != cursor:
        raise AssertionError("guarded-L6 audit firstness cursor drift")
    if checkpoint["audit_record_stream_sha256"] != rescue.stable_hash(
        checkpoint["audit_records"]
    ):
        raise AssertionError("guarded-L6 audit record stream drift")
    pending = checkpoint["pending_firstness_scan"]
    if pending is not None and pending["construction_rank"] != cursor:
        raise AssertionError("guarded-L6 audit pending/rank drift")
    verifier = checkpoint["ordered_verifier"]
    if verifier["next_point"] and cursor != EXPECTED_GAPS:
        raise AssertionError("guarded-L6 ordered scan preceded firstness")
    total = verifier["total_points"]
    if total is not None and not 0 <= verifier["next_point"] <= total:
        raise AssertionError("guarded-L6 ordered cursor drift")
    expected_pairs = verifier["next_point"] * (
        verifier["next_point"] - 1
    ) // 2
    if verifier["pair_checks"] != expected_pairs:
        raise AssertionError("guarded-L6 ordered pair-count drift")
    if len(verifier["promoted_line_records"]) != verifier[
        "target_cone_pair_matches"
    ] or verifier["promoted_line_record_stream_sha256"] != rescue.stable_hash(
        verifier["promoted_line_records"]
    ):
        raise AssertionError("guarded-L6 promoted-line record drift")
    if not 0 <= verifier["target_cone_pair_matches"] <= (
        EXPECTED_PROMOTED_LINES
    ):
        raise AssertionError("guarded-L6 promoted-line count drift")
    if verifier["complete"] and (
        total is None or verifier["next_point"] != total
    ):
        raise AssertionError("guarded-L6 ordered completion drift")
    if (checkpoint["status"] == "complete") != verifier["complete"]:
        raise AssertionError("guarded-L6 checkpoint/verifier status drift")
    if checkpoint["status"] == "complete":
        if checkpoint["terminal_output"] is None or checkpoint[
            "terminal_summary"
        ] is None:
            raise AssertionError("guarded-L6 terminal snapshot missing")
    elif checkpoint["terminal_output"] is not None or checkpoint[
        "terminal_summary"
    ] is not None:
        raise AssertionError("partial guarded-L6 audit has terminal snapshot")
    return checkpoint


def reconstruct_audited_prefix(context, checkpoint, deadline):
    source = context["guard_source"]
    records = source["selection_records"]
    l6_state = context["l6"]
    anchors = l6_state["anchors"]
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    cursor = checkpoint["firstness_audited_through_rank"]
    for rank in range(cursor):
        if rank % CHECKPOINT_INTERVAL == 0 and rescue.enforce_runtime(
            deadline, "reconstructing guarded-L6 audited prefix"
        ):
            raise DeadlineReached
        source_record = records[rank]
        audit_record = checkpoint["audit_records"][rank]
        gap = l6_state["schedule"][rank]
        step = l6_state["parent_word"][gap]
        if (
            source_record["construction_rank"], source_record["gap"],
            source_record["step"],
        ) != (rank, gap, step) or (
            audit_record["construction_rank"], audit_record["gap"],
            audit_record["step"],
        ) != (rank, gap, step):
            raise AssertionError("guarded-L6 audited schedule drift", rank)
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
                raise AssertionError(
                    "stored guarded-L6 audit-record drift", rank, key
                )
        word = cache_word_at_offset(
            context["cache"], context["blocks"][step],
            source_record["cache_record_offset"],
        )
        if list(word) != source_record["selected_word"]:
            raise AssertionError("guarded-L6 selected cache bytes drift", rank)
        ordinal = source_record["first_survivor_ordinal_1_based"]
        if not action_accepts(
            context["bitset"], context["action_records"][step], "zero",
            ordinal,
        ):
            raise AssertionError("guarded-L6 winner lost zero-T", rank)
        start, target = anchors[gap], anchors[gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        if rescue.endpoint(start, word) != target:
            raise AssertionError("guarded-L6 selected endpoint drift", rank)
        if not intrinsic_projection_clean(
            start, target, interiors
        ) or not global_projection_clean(interiors, yz_counts):
            raise AssertionError("guarded-L6 selected projection drift", rank)
        apply_selected(interiors, store, yz_counts)
    observed = prefix_commitment(store, yz_counts, records, cursor)
    if observed != checkpoint["audited_prefix"]:
        raise AssertionError("guarded-L6 audited prefix commitment drift")
    if cursor == EXPECTED_GAPS and observed != source["prefix"]:
        raise AssertionError("completed guarded-L6 prefix/source drift")
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
        raise AssertionError("pending guarded-L6 firstness identity drift")
    ordinal = scan["next_ordinal_1_based"]
    if not 1 <= ordinal <= selected_ordinal or scan[
        "domain_words_scanned"
    ] != ordinal - 1:
        raise AssertionError("pending guarded-L6 firstness ordinal drift")
    if not block["start"] <= scan["next_cache_cursor"] < block["end"]:
        raise AssertionError("pending guarded-L6 cache cursor drift")
    if scan["action_incompatible_skipped"] + scan[
        "action_compatible_seen"
    ] != scan["domain_words_scanned"]:
        raise AssertionError("pending guarded-L6 action partition drift")
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != scan["action_compatible_seen"]:
        raise AssertionError("pending guarded-L6 projection partition drift")
    if scan["exact_legality_rejected"] + scan[
        "cone_birth_rejected"
    ] != scan["projection_clean_exact_tested"]:
        raise AssertionError("pending guarded-L6 exact/cone partition has survivor")


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
            raise AssertionError("guarded-L6 selected-record drift", rank, key)
    return expected_survivor


def audit_one_stitch(context, rank, store, yz_counts, pending, deadline):
    source_record = context["guard_source"]["selection_records"][rank]
    l6_state = context["l6"]
    gap = l6_state["schedule"][rank]
    step = l6_state["parent_word"][gap]
    if (
        source_record["construction_rank"], source_record["gap"],
        source_record["step"],
    ) != (rank, gap, step):
        raise AssertionError("guarded-L6 source schedule drift", rank)
    block = context["blocks"][step]
    action_record = context["action_records"][step]
    selected_ordinal = source_record["first_survivor_ordinal_1_based"]
    if not 1 <= selected_ordinal <= block["words"]:
        raise AssertionError("guarded-L6 selected ordinal outside domain", rank)
    scan = copy.deepcopy(pending) if pending is not None else empty_pending(
        rank, gap, step, block, selected_ordinal,
        action_record["zero"]["set_bits"],
    )
    validate_pending(scan, rank, gap, step, block, selected_ordinal)
    if scan["static_zero_T_words"] != action_record["zero"]["set_bits"]:
        raise AssertionError("guarded-L6 pending zero-T population drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    fast_memo = {}
    reference_memo = {}
    start = l6_state["anchors"][gap]
    target = l6_state["anchors"][gap + 1]
    while ordinal <= selected_ordinal:
        if ordinal % 128 == 1 and rescue.enforce_runtime(
            deadline, "independent guarded-L6 firstness scan"
        ):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        offset = cursor
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("guarded-L6 cache boundary drift", rank, ordinal)
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
                "guarded-L6 fast/reference disagreement", rank, ordinal
            )
        if not reference_legal:
            scan["exact_legality_rejected"] += 1
            ordinal += 1
            continue
        if rescue.endpoint(start, word) != target:
            raise AssertionError("eligible guarded-L6 endpoint drift", rank, ordinal)
        cone_witness = first_new_cone_birth(interiors, store)
        if cone_witness is not None:
            scan["cone_birth_rejected"] += 1
            ordinal += 1
            continue
        if ordinal < selected_ordinal:
            raise AssertionError(
                "earlier guarded-L6 survivor found", rank, ordinal,
                selected_ordinal, list(word),
            )
        if list(word) != source_record["selected_word"] or offset != (
            source_record["cache_record_offset"]
        ):
            raise AssertionError("guarded-L6 winner/cache-order drift", rank)
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
    raise AssertionError("stored L6 winner is not guarded-policy legal", rank)


def ordered_chain(context):
    records = context["guard_source"]["selection_records"]
    selected = {record["gap"]: tuple(record["selected_word"])
                for record in records}
    if set(selected) != set(range(EXPECTED_GAPS)):
        raise AssertionError("guarded-L6 source does not select every gap")
    anchors = context["l6"]["anchors"]
    chain = [anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_GAPS):
        word = selected[gap]
        chain.extend(rescue.word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != EXPECTED_POINTS or len(chain) != len(set(chain)):
        raise AssertionError("guarded-L6 ordered chain extent/repetition drift")
    if rescue.stable_hash(sorted(chain)) != EXPECTED_POINT_SET_SHA256:
        raise AssertionError("guarded-L6 ordered point-set drift")
    return tuple(chain), tuple(flat_word), selected


def verify_final_yz(anchors, chain):
    initial = Counter(point[1:] for point in anchors)
    final = Counter(point[1:] for point in chain)
    for fibre, count in final.items():
        if count != initial.get(fibre, 1):
            raise AssertionError("terminal guarded-L6 no-new-yz failure", fibre)
    if rescue.stable_hash(sorted(final.items())) != EXPECTED_FINAL_YZ_SHA256:
        raise AssertionError("terminal guarded-L6 yz commitment drift")
    double_fibres = sorted(
        fibre for fibre, count in final.items() if count == 2
    )
    if rescue.stable_hash(double_fibres) != EXPECTED_FINAL_DOUBLE_FIBRE_SHA256:
        raise AssertionError("terminal guarded-L6 doubled-yz drift")
    return final, double_fibres


def verify_ordered_point(chain, cursor, anchor_ids, anchors):
    point = chain[cursor]
    owner = {}
    cone_records = []
    point_is_anchor = point in anchor_ids
    for index in range(cursor):
        prior = chain[index]
        displacement = subtract(prior, point)
        direction = primitive_direction(displacement)
        earlier = owner.get(direction)
        if earlier is not None:
            raise AssertionError(
                "ordered guarded-L6 chain contains a collinear triple",
                earlier, index, cursor,
                [list(chain[earlier]), list(prior), list(point)],
            )
        owner[direction] = index
        matches = cone_matches(displacement)
        if matches:
            if not point_is_anchor or prior not in anchor_ids:
                raise AssertionError(
                    "terminal guarded-L6 new target-cone secant",
                    index, cursor, list(prior), list(point), list(matches),
                )
            first_id = anchor_ids[prior]
            second_id = anchor_ids[point]
            earlier_id, later_id = sorted((first_id, second_id))
            direction = subtract(anchors[later_id], anchors[earlier_id])
            primitive = primitive_direction(direction)
            cone_records.append({
                "earlier_point_id": earlier_id,
                "later_point_id": later_id,
                "matched_spectra": list(cone_matches(direction)),
                "canonical_primitive_direction": list(primitive),
                "exact_Pluecker_moment": list(cross(
                    anchors[earlier_id], primitive
                )),
            })
    return cursor, cone_records


def terminal_payload(context, checkpoint, chain, flat_word, selected, policy):
    records = context["guard_source"]["selection_records"]
    ordinals = [
        record["first_survivor_ordinal_1_based"] for record in records
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": "exact independent guarded-L6 finite certificate",
        "checker": {
            "path": "design/lattice_t_l6_cone_guard_audit.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_audit": True,
        },
        "resource_policy": policy,
        "source_checkpoint": context["guard_source_snapshot"],
        "source_pins": source_pins(),
        "pinned_dependencies": context["guard_dependencies"],
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
            "the pinned two-cone-guarded L6 policy has an exact first survivor at every chronological stitch",
            "every selected word is zero-T, globally yz-fresh, reference-legal, and creates no new secant in either named cone",
            "the inherited L6 anchor skeleton contains exactly the pinned finite set of affine lines in the two named projective cones",
            "the final guarded L6 walk has no collinear triple and no target-cone secant with a connector endpoint",
        ],
        "not_proved": [
            "control of any projective direction outside J=11/3 and J=348/275",
            "positive guarded availability for every reachable state or at levels beyond this pinned L6 orbit",
            "a consecutive guarded-L5 to guarded-L6 transition: this L6 base descends from the terminal-audited primary L5 orbit, not the separate guarded-L5 experiment",
            "a finite exact-zero right congruence, contracting far-secant birth envelope, or unconditional infinite construction",
        ],
    }
    payload["terminal_payload_sha256"] = rescue.stable_hash(payload)
    return payload


def audit_chunk(args, policy):
    started = time.monotonic()
    deadline = started + args.max_seconds
    ensure_audit_paths_disjoint(args)
    context = open_context(args)
    try:
        static = audit_static(context, args)
        checkpoint = load_checkpoint(args.audit_checkpoint, context, static)
        if checkpoint["status"] == "complete":
            verify_terminal_artifacts(args, context, checkpoint)
            return checkpoint, {
                "work_items": 0,
                "stop_reason": (
                    "terminal-audit-already-complete-and-artifacts-reverified"
                ),
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
                deadline, "between guarded-L6 audit stitches"
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
                store, yz_counts,
                context["guard_source"]["selection_records"], cursor,
            )
            work += 1
            if work % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(args.audit_checkpoint, checkpoint)

        if checkpoint["firstness_audited_through_rank"] == EXPECTED_GAPS:
            if checkpoint["audited_prefix"] != context["guard_source"][
                "prefix"
            ]:
                raise AssertionError("completed guarded-L6 prefix/source drift")
            chain, flat_word, selected = ordered_chain(context)
            final_yz, double_fibres = verify_final_yz(
                context["l6"]["anchors"], chain
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
                    raise AssertionError(
                        "guarded-L6 ordered commitment drift", key
                    )
                verifier[key] = value
            verifier["final_no_new_yz_coincidence"] = True
            anchor_ids = {
                point: index for index, point in enumerate(
                    context["l6"]["anchors"]
                )
            }
            if len(anchor_ids) != EXPECTED_ANCHORS:
                raise AssertionError("inherited guarded-L6 anchors repeat")
            while verifier["next_point"] < len(chain):
                if work >= args.max_work_items:
                    stop_reason = "ordered-verifier-work-limit"
                    break
                if rescue.enforce_runtime(
                    deadline, "ordered guarded-L6 terminal verifier"
                ):
                    stop_reason = "ordered-verifier-time-limit"
                    break
                pair_checks, cone_records = verify_ordered_point(
                    chain, verifier["next_point"], anchor_ids,
                    context["l6"]["anchors"],
                )
                verifier["pair_checks"] += pair_checks
                verifier["target_cone_pair_matches"] += len(cone_records)
                verifier["promoted_line_records"].extend(cone_records)
                verifier["promoted_line_record_stream_sha256"] = (
                    rescue.stable_hash(verifier["promoted_line_records"])
                )
                verifier["next_point"] += 1
                work += 1
                if work % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(args.audit_checkpoint, checkpoint)
                    verifier = checkpoint["ordered_verifier"]
            if verifier["next_point"] == len(chain):
                expected_pairs = len(chain) * (len(chain) - 1) // 2
                if verifier["pair_checks"] != expected_pairs:
                    raise AssertionError("guarded-L6 exhaustive pair extent drift")
                if verifier["target_cone_pair_matches"] != (
                    EXPECTED_PROMOTED_LINES
                ):
                    raise AssertionError("guarded-L6 target-cone pair census drift")
                promoted = sorted(
                    verifier["promoted_line_records"],
                    key=lambda record: (
                        record["later_point_id"], record["earlier_point_id"]
                    ),
                )
                line_keys = {
                    (
                        tuple(record["canonical_primitive_direction"]),
                        tuple(record["exact_Pluecker_moment"]),
                    )
                    for record in promoted
                }
                if len(line_keys) != len(promoted):
                    raise AssertionError(
                        "inherited guarded-L6 anchors repeat a cone line"
                    )
                if rescue.stable_hash(promoted) != (
                    EXPECTED_PROMOTED_LINE_STREAM_SHA256
                ):
                    raise AssertionError(
                        "guarded-L6 promoted affine-line digest drift"
                    )
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
                verify_terminal_artifacts(args, context, checkpoint)
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
        producer.close_context(context)


def self_check():
    synthetic_paths = argparse.Namespace(
        source="/tmp/guarded-L6-source-self-check.json",
        audit_checkpoint="/tmp/guarded-L6-source-self-check.json",
        output="/tmp/guarded-L6-output-self-check.json",
        summary="/tmp/guarded-L6-summary-self-check.json",
        parent_source="/tmp/guarded-L6-parent-source-self-check.json",
        parent_terminal="/tmp/guarded-L6-parent-terminal-self-check.json",
        metadata="/tmp/guarded-L6-metadata-self-check.json",
        cache="/tmp/guarded-L6-cache-self-check.bin",
        lattice_result="/tmp/guarded-L6-lattice-self-check.json",
        lattice_bitsets="/tmp/guarded-L6-bitsets-self-check.bin",
    )
    try:
        ensure_audit_paths_disjoint(synthetic_paths)
    except ValueError as error:
        if error.args[0] != (
            "guarded-L6 audit output/checkpoint aliases an input"
        ):
            raise
    else:
        raise AssertionError("guarded-L6 source/output alias was accepted")
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
        raise AssertionError("guarded-L6 ordinal-bit convention drift")
    if cone_matches((3, -3, 1)) != ("11/3",):
        raise AssertionError("guarded-L6 11/3 witness drift")
    if cone_matches((55, 34, 18)) != ("348/275",):
        raise AssertionError("guarded-L6 348/275 witness drift")
    if cone_matches((1, 0, 0)):
        raise AssertionError("guarded-L6 non-cone direction misclassified")
    promoted = promoted_seed_cone_lines(((0, 0, 0), (3, -3, 1)))
    if len(promoted) != 1 or promoted[0]["matched_spectra"] != ["11/3"]:
        raise AssertionError("guarded-L6 synthetic promoted-line drift")
    store = rescue.Store(((0, 0, 0),))
    old_new = first_new_cone_birth(((3, -3, 1),), store)
    if old_new is None or old_new["classification"] != "old-new":
        raise AssertionError("guarded-L6 synthetic old-new birth missed")
    same_word = first_new_cone_birth(
        ((10, 0, 0), (13, -3, 1)), store
    )
    if same_word is None or same_word[
        "classification"
    ] != "same-word-new-new":
        raise AssertionError("guarded-L6 synthetic same-word birth missed")
    collinear = ((0, 0, 0), (1, 1, 1), (2, 2, 2))
    try:
        verify_ordered_point(
            collinear, 2, {(0, 0, 0): 0}, ((0, 0, 0),)
        )
    except AssertionError as error:
        if error.args[0] != (
            "ordered guarded-L6 chain contains a collinear triple"
        ):
            raise
    else:
        raise AssertionError("guarded-L6 synthetic triple was accepted")
    try:
        verify_ordered_point(
            ((0, 0, 0), (3, -3, 1)), 1, {(0, 0, 0): 0},
            ((0, 0, 0),)
        )
    except AssertionError as error:
        if error.args[0] != "terminal guarded-L6 new target-cone secant":
            raise
    else:
        raise AssertionError("guarded-L6 synthetic new cone was accepted")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "terminal_pins_finalized": terminal_pins_finalized(),
        "heavy_audit_locked_until_terminal_pins": True,
        "large_artifacts_opened": False,
        "independent_ordinal_bits_tested": 10,
        "both_target_cones_tested": True,
        "old_new_and_same_word_births_tested": True,
        "synthetic_collinear_rejection": True,
        "synthetic_new_cone_rejection": True,
        "synthetic_source_output_alias_rejection": True,
        "firstness_resume_granularity": "cache ordinal within one stitch",
    }


def estimate():
    return {
        "status": "prepared; audit is fail-closed pending guarded-L6 pins",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "terminal_pins": terminal_string_pins(),
        "terminal_pins_finalized": terminal_pins_finalized(),
        "source_checkpoint_is_read_only": True,
        "audit_checkpoint_is_separate": True,
        "all_writable_paths_are_resolved_and_disjoint": True,
        "complete_resume_reverifies_both_terminal_artifacts": True,
        "primary_L5_lineage": PRIMARY_L5_LINEAGE,
        "expected_stitches": EXPECTED_GAPS,
        "expected_anchors": EXPECTED_ANCHORS,
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
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-work-items", type=int, default=500)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,600]")
    if not 1 <= args.max_work_items <= HARD_MAX_WORK_ITEMS:
        raise ValueError("max-work-items outside [1,2000]")
    policy = legacy.resource_policy(enforce=args.mode == "audit")
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
