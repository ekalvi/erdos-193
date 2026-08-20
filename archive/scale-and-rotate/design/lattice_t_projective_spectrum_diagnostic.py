#!/usr/bin/env python3
"""Exact diagnostic census of the two suspect projective spectra on L5.

This is deliberately not a certificate for a stronger connector policy.  It
continues the frozen all-pair scan after the strict spectrum policy's first
counterexample and records compact exact statistics for every E-valued pair.
The frozen checker and its refutation summary are immutable pinned inputs.

For each matching pair the scan commits, in deterministic pair order, its
birth class, spectrum, primitive direction, exact Pluecker moment, later birth
rank, and endpoint ids.  Exact marginal counters are retained for birth class,
spectrum, primitive direction, and later birth rank.  The audited path has no
three collinear points, so every (primitive direction, moment) affine-line
group has multiplicity one; those groups are committed by hash chains rather
than copied pair-by-pair into the terminal artifact.

The diagnostic also distinguishes the whole J cones from the two known exact
macro inverse orbits.  For each family it includes both single-phase direction
sequences g_n and canon(M g_n), where g_n=canon(N^(2n)g_0).  The finite n range
is certified separately in each phase from its exact x-component growth and
the exact x diameter of the walk.

Finally, seed lines are joined by exact affine Pluecker data to every actual
step-1 L5 corridor and to every L6 child corridor induced by the selected L5
words.  The join preserves the actual parent gap, selected word, child slot,
prefix control, and child cursor.  It tests the known J=11/3 two-phase cycle;
direction-only or independently continued address matches do not count.

The output is diagnostic finite evidence only.  It does not prove a uniform
birth exclusion, future connector availability, or a far-secant tail lemma.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import resource
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_CHECKER = ROOT / "design" / "lattice_t_projective_spectrum_census.py"
STRICT_SUMMARY = (
    ROOT / "design" / "lattice-T-projective-spectrum-census-summary.json"
)
DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L5-primary.json")
DEFAULT_AUDIT_SUMMARY = (
    ROOT / "design" / "lattice-T-chronological-L5-summary.json"
)
DEFAULT_CHECKPOINT = Path(
    "/tmp/lattice-T-L5-projective-spectrum-diagnostic-checkpoint.json"
)
DEFAULT_OUTPUT = (
    ROOT / "design" / "lattice-T-projective-spectrum-diagnostic-summary.json"
)

EXPECTED_FROZEN_CHECKER_SHA256 = (
    "034744d9b5da4e3ffd4147bbaf0bf123cc620943bf3337bc0070a6f427edf48b"
)
EXPECTED_STRICT_SUMMARY_SHA256 = (
    "b3106b286a821337a2199dec275ca8a7630184662658c71cd7d0a847c4dfb664"
)
EXPECTED_STRICT_SUMMARY_BYTES = 4_980
EXPECTED_STRICT_SUMMARY_PAYLOAD_SHA256 = (
    "59e52ce5a55a2c42e5ecb6f0076fd5b8fd2b960084bb9b2f70aada1bc8f7d24d"
)
EXPECTED_POINTS = 8_268
EXPECTED_ANCHORS = 2_458
EXPECTED_GAPS = 2_457
EXPECTED_PAIRS = 34_175_778
SCHEMA_VERSION = 1

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)
SPECTRA = (("11/3", 11, 3), ("348/275", 348, 275))
FAMILIES = (
    {
        "name": "J_11_over_3_cycle",
        "spectrum": "11/3",
        "base_direction": (3, -1, 3),
        "phase_names": ("A", "B"),
    },
    {
        "name": "latent_348_over_275_cycle",
        "spectrum": "348/275",
        "base_direction": (55, 34, 18),
        "phase_names": ("8", "16"),
    },
)
J_PHASES = (
    {
        "name": "A",
        "site": (-3, 0, -3),
        "control": (-2, 1, -2),
        "target_step": 1,
        "literal_word": (15, 1, 20, 71),
        "literal_slot": 1,
    },
    {
        "name": "B",
        "site": (-3, 3, -2),
        "control": (-2, 4, -2),
        "target_step": 1,
        "literal_word": (20, 71, 1, 15),
        "literal_slot": 2,
    },
)

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
MAX_WORK_SECONDS = 110.0
HARD_MAX_SECONDS = 115.0
MAX_RESIDENT_BYTES = 280 * 1024 * 1024
DEFAULT_MAX_PAIRS = 5_000_000
HARD_MAX_PAIRS = 10_000_000
CHECKPOINT_PAIR_INTERVAL = 1_000_000
DEADLINE_CHECK_INTERVAL = 65_536
WITNESSES_PER_BUCKET = 3
PROCESS_START_CHECKER_SHA256 = None


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def hash_chain(previous, value):
    digest = hashlib.sha256()
    digest.update(bytes.fromhex(previous))
    digest.update(canonical_bytes(value))
    return digest.hexdigest()


def add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def subtract(left, right):
    return tuple(a - b for a, b in zip(left, right))


def apply_matrix(matrix, vector):
    return tuple(
        sum(coefficient * value for coefficient, value in zip(row, vector))
        for row in matrix
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive_direction(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise ValueError("zero vector has no primitive direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def quadratic(direction):
    _r, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def matched_spectrum(direction):
    r, _y, _z = direction
    q = quadratic(direction)
    matches = [
        label
        for label, numerator, denominator in SPECTRA
        if denominator * q == numerator * r * r
    ]
    if len(matches) > 1:
        raise AssertionError("one nonzero direction matched both spectra")
    return None if not matches else matches[0]


def word_geometry(word):
    point = (0, 0, 0)
    prefixes = []
    interiors = []
    for slot, letter in enumerate(word):
        prefixes.append(point)
        point = add(point, MENU[letter])
        if slot + 1 < len(word):
            interiors.append(point)
    return tuple(prefixes), tuple(interiors), point


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce=True):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and (
        nice >= 15
    )
    if enforce and not compliant:
        raise RuntimeError("diagnostic requires thread controls=1 and nice>=15")
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": nice,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


def assert_checker_unchanged():
    if file_sha256(Path(__file__).resolve()) != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("diagnostic checker changed during run")


def atomic_json_dump(value, path):
    assert_checker_unchanged()
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
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


def load_frozen_checker():
    observed = file_sha256(FROZEN_CHECKER)
    if observed != EXPECTED_FROZEN_CHECKER_SHA256:
        raise AssertionError("frozen spectrum checker drift")
    specification = importlib.util.spec_from_file_location(
        "frozen_lattice_t_projective_spectrum_census", FROZEN_CHECKER
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if module.PROCESS_START_CHECKER_SHA256 != observed:
        raise AssertionError("frozen checker self-hash drift")
    return module, {
        "path": str(FROZEN_CHECKER.relative_to(ROOT)),
        "sha256": observed,
        "bytes": FROZEN_CHECKER.stat().st_size,
    }


def verify_strict_summary():
    if STRICT_SUMMARY.stat().st_size != EXPECTED_STRICT_SUMMARY_BYTES:
        raise AssertionError("strict refutation summary byte-size drift")
    observed = file_sha256(STRICT_SUMMARY)
    if observed != EXPECTED_STRICT_SUMMARY_SHA256:
        raise AssertionError("strict refutation summary digest drift")
    with STRICT_SUMMARY.open() as handle:
        summary = json.load(handle)
    if summary["payload_sha256"] != EXPECTED_STRICT_SUMMARY_PAYLOAD_SHA256:
        raise AssertionError("strict refutation payload drift")
    if summary["checker"]["sha256"] != EXPECTED_FROZEN_CHECKER_SHA256:
        raise AssertionError("strict refutation checker pin drift")
    witness = summary["result"]["earliest_witness"]
    expected = {
        "earlier_point_id": 30,
        "later_point_id": 33,
        "canonical_primitive_direction": [3, -3, 1],
        "matched_spectra": ["11/3"],
        "line_moment": [198, -9, -621],
    }
    for key, value in expected.items():
        if witness[key] != value:
            raise AssertionError("strict earliest witness drift", key)
    return summary, {
        "path": str(STRICT_SUMMARY.relative_to(ROOT)),
        "sha256": observed,
        "bytes": STRICT_SUMMARY.stat().st_size,
        "payload_sha256": summary["payload_sha256"],
    }


def orbit_catalog(x_span):
    """Return both single-phase inverse-macro direction sequences.

    Every primitive pair direction has |r| at most the exact x diameter.
    Each same-phase sequence has exact factor-nine x growth from n>=1 (the
    phase-B n=0->1 normalization is exceptional and checked explicitly).
    Thus the first n above x_span is a proof-grade finite cutoff, not a
    sampled truncation.
    """
    if x_span < 0:
        raise ValueError("negative x span")
    records = []
    lookup = defaultdict(list)
    cutoffs = {}
    for family in FAMILIES:
        base = family["base_direction"]
        direction = primitive_direction(base)
        n = 0
        phase_history = {phase: [] for phase in family["phase_names"]}
        first_excluded = {}
        while True:
            if abs(direction[0]) != abs(base[0]) * (9 ** n):
                raise AssertionError("macro direction x-growth drift")
            phase_directions = (
                direction,
                primitive_direction(apply_matrix(M, direction)),
            )
            if n >= 2:
                for phase, phase_direction in zip(
                    family["phase_names"], phase_directions
                ):
                    if abs(phase_direction[0]) != 9 * phase_history[phase][-1]:
                        raise AssertionError(
                            "single-phase factor-nine x-growth drift"
                        )
            any_included = False
            for phase, phase_direction in zip(
                family["phase_names"], phase_directions
            ):
                phase_history[phase].append(abs(phase_direction[0]))
                if abs(phase_direction[0]) > x_span:
                    first_excluded.setdefault(phase, {
                        "first_excluded_n": n,
                        "first_excluded_abs_x_component": abs(
                            phase_direction[0]
                        ),
                    })
                    continue
                any_included = True
                record = {
                    "family": family["name"],
                    "spectrum": family["spectrum"],
                    "phase": phase,
                    "n": n,
                    "primitive_direction": list(phase_direction),
                }
                records.append(record)
                lookup[phase_direction].append(record)
            if not any_included:
                if set(first_excluded) != set(family["phase_names"]):
                    raise AssertionError("incomplete phase cutoff")
                break
            direction = primitive_direction(
                apply_matrix(N, apply_matrix(N, direction))
            )
            n += 1
        cutoffs[family["name"]] = {
            "phase_cutoffs": {
                phase: {
                    "included_n": [
                        record["n"] for record in records
                        if record["family"] == family["name"]
                        and record["phase"] == phase
                    ],
                    **first_excluded[phase],
                }
                for phase in family["phase_names"]
            },
            "exact_pair_x_diameter": x_span,
            "exclusion_reason": (
                "a primitive secant direction has |r| no larger than the "
                "exact x diameter; each phase's subsequent |r| grows by "
                "an exact factor nine after the checked initial normalization"
            ),
        }
    for direction, memberships in lookup.items():
        identities = {
            (item["family"], item["phase"], item["n"])
            for item in memberships
        }
        if len(identities) != len(memberships):
            raise AssertionError("duplicate orbit membership")
        spectrum = matched_spectrum(direction)
        if any(item["spectrum"] != spectrum for item in memberships):
            raise AssertionError("orbit direction left its exact spectrum")
    return tuple(records), dict(lookup), cutoffs


def selected_words_by_gap(source):
    words = [None] * EXPECTED_GAPS
    ranks = [None] * EXPECTED_GAPS
    for rank, record in enumerate(source["selection_records"]):
        gap = record["gap"]
        if words[gap] is not None:
            raise AssertionError("duplicate selected gap")
        words[gap] = tuple(record["selected_word"])
        ranks[gap] = rank
    if any(word is None for word in words) or any(
        rank is None for rank in ranks
    ):
        raise AssertionError("incomplete selected-word map")
    return tuple(words), tuple(ranks)


def actual_l6_skeleton(parent_word, anchors, words):
    child_steps = []
    child_anchors = []
    owners = []
    child_start_by_gap = []
    for gap, (step, word) in enumerate(zip(parent_word, words)):
        child_start_by_gap.append(len(child_steps))
        prefixes, _interiors, endpoint = word_geometry(word)
        if endpoint != apply_matrix(M, MENU[step]):
            raise AssertionError("selected L5 endpoint drift", gap)
        for slot, (letter, prefix) in enumerate(zip(word, prefixes)):
            child_steps.append(letter)
            child_anchor = apply_matrix(M, add(anchors[gap], prefix))
            child_anchors.append(child_anchor)
            owners.append({
                "parent_gap": gap,
                "parent_slot": slot,
                "parent_prefix": list(prefix),
            })
    child_anchors.append(apply_matrix(M, anchors[-1]))
    if len(child_anchors) != len(child_steps) + 1:
        raise AssertionError("actual L6 skeleton size drift")
    for gap, step in enumerate(child_steps):
        delta = subtract(child_anchors[gap + 1], child_anchors[gap])
        if delta != apply_matrix(M, MENU[step]):
            raise AssertionError("actual L6 child step drift", gap)
    return (
        tuple(child_steps),
        tuple(child_anchors),
        tuple(owners),
        tuple(child_start_by_gap),
    )


def phase_macro_slots(word, phase):
    prefixes, interiors, _endpoint = word_geometry(word)
    if phase["site"] in interiors:
        return ()
    return tuple(
        slot
        for slot, (letter, prefix) in enumerate(zip(word, prefixes))
        if letter == phase["target_step"] and prefix == phase["control"]
    )


def j_phase_direction_records(x_span):
    records, _lookup, _cutoffs = orbit_catalog(x_span)
    return tuple(
        record
        for record in records
        if record["family"] == "J_11_over_3_cycle"
    )


def build_j_role_index(level, parent_word, anchors, x_span, words=None,
                       ranks=None, owners=None, child_start_by_gap=None):
    """Index exact J-cycle affine lines in every actual corridor frame."""
    phase_by_name = {phase["name"]: phase for phase in J_PHASES}
    direction_records = j_phase_direction_records(x_span)
    roles = defaultdict(list)
    role_stream = []
    for gap, step in enumerate(parent_word):
        if step != 1:
            continue
        anchor = anchors[gap]
        for direction_record in direction_records:
            phase = phase_by_name[direction_record["phase"]]
            direction = tuple(direction_record["primitive_direction"])
            moment = cross(add(anchor, phase["site"]), direction)
            role = {
                "level": level,
                "gap": gap,
                "corridor_anchor": list(anchor),
                "phase": phase["name"],
                "n": direction_record["n"],
                "primitive_direction": list(direction),
                "absolute_line_moment": list(moment),
            }
            if owners is not None:
                role["actual_parent_owner"] = owners[gap]
            if words is not None:
                word = words[gap]
                slots = phase_macro_slots(word, phase)
                role.update({
                    "construction_rank": ranks[gap],
                    "actual_selected_word": list(word),
                    "macro_compatible_slots": list(slots),
                    "literal_selected_action": (
                        word == phase["literal_word"]
                        and phase["literal_slot"] in slots
                    ),
                    "child_cursors": [
                        child_start_by_gap[gap] + slot for slot in slots
                    ],
                })
            key = (direction, moment)
            roles[key].append(role)
            role_stream.append(role)
    return dict(roles), {
        "level": level,
        "step_1_corridors": sum(step == 1 for step in parent_word),
        "phase_line_roles": len(role_stream),
        "role_stream_sha256": stable_hash(role_stream),
        "actual_words_available": words is not None,
    }


def build_static_inputs(source_path, audit_path):
    frozen, frozen_snapshot = load_frozen_checker()
    _strict, strict_snapshot = verify_strict_summary()
    _audit, audit_snapshot = frozen.verify_terminal_audit_summary(audit_path)
    source, source_snapshot = frozen.load_source(source_path)
    points, provenance, interior_counts, state_sha = frozen.reconstruct_points(
        source
    )
    parent_word, anchors, schedule, repeated_state_sha = frozen.load_l5_state()
    if repeated_state_sha != state_sha:
        raise AssertionError("repeated L5 state hash drift")
    words, ranks = selected_words_by_gap(source)
    if tuple(schedule[rank] for rank in range(EXPECTED_GAPS)) != tuple(
        record["gap"] for record in source["selection_records"]
    ):
        raise AssertionError("source schedule reconstruction drift")
    child_steps, child_anchors, child_owners, child_starts = (
        actual_l6_skeleton(parent_word, anchors, words)
    )
    x_span = max(point[0] for point in points) - min(
        point[0] for point in points
    )
    anchor_x_span = max(point[0] for point in anchors) - min(
        point[0] for point in anchors
    )
    child_anchor_x_span = max(point[0] for point in child_anchors) - min(
        point[0] for point in child_anchors
    )
    orbit_records, orbit_lookup, orbit_cutoffs = orbit_catalog(x_span)
    strict_witness_orbit_memberships = orbit_lookup.get((3, -3, 1), ())
    if strict_witness_orbit_memberships:
        raise AssertionError("strict first witness unexpectedly entered orbit")
    l5_roles, l5_role_summary = build_j_role_index(
        5, parent_word, anchors, anchor_x_span,
        words=words, ranks=ranks, child_start_by_gap=child_starts,
    )
    l6_roles, l6_role_summary = build_j_role_index(
        6, child_steps, child_anchors, child_anchor_x_span,
        owners=child_owners,
    )
    expected_classes = frozen.expected_classification_counts(interior_counts)
    expected_classes = {
        ("new-new" if key == "same-word-new-new" else key): value
        for key, value in expected_classes.items()
    }
    static = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "frozen_spectrum_checker": frozen_snapshot,
        "strict_refutation_summary": strict_snapshot,
        "source_checkpoint": source_snapshot,
        "terminal_audit_summary": audit_snapshot,
        "L5_state_sha256": state_sha,
        "point_count": len(points),
        "pair_count": EXPECTED_PAIRS,
        "construction_order_point_stream_sha256": frozen.point_stream_sha256(
            points
        ),
        "provenance_stream_sha256": frozen.provenance_commitment(provenance),
        "interior_count_stream_sha256": stable_hash(interior_counts),
        "exact_x_diameter": x_span,
        "orbit_direction_records_sha256": stable_hash(orbit_records),
        "orbit_direction_record_count": len(orbit_records),
        "orbit_cutoffs": orbit_cutoffs,
        "strict_first_witness_exact_orbit_memberships": list(
            strict_witness_orbit_memberships
        ),
        "actual_L5_selected_word_stream_sha256": stable_hash(words),
        "actual_L6_parent_word_sha256": stable_hash(child_steps),
        "actual_L6_anchor_stream_sha256": stable_hash(child_anchors),
        "actual_L6_owner_stream_sha256": stable_hash(child_owners),
        "J_cycle_role_indexes": {
            "L5": l5_role_summary,
            "L6": l6_role_summary,
        },
        "expected_full_classification_counts": expected_classes,
        "pair_order": "increasing later point id, then increasing earlier id",
    }
    static["static_state_sha256"] = stable_hash(static)
    context = {
        "frozen": frozen,
        "points": points,
        "provenance": provenance,
        "child_steps": child_steps,
        "orbit_lookup": orbit_lookup,
        "l5_roles": l5_roles,
        "l6_roles": l6_roles,
    }
    return static, context


def empty_role_test():
    return {
        "counts": {
            "seed_E_pairs": 0,
            "L5_exact_phase_line_pairs": 0,
            "L5_exact_phase_line_roles": 0,
            "L5_macro_compatible_roles": 0,
            "L5_literal_selected_action_roles": 0,
            "L5_exact_selected_child_transitions": 0,
            "L5_exact_terminal_forward_exit_transitions": 0,
            "L6_exact_phase_line_pairs": 0,
            "L6_exact_phase_line_roles": 0,
        },
        "phase_n_counts": {},
        "samples": {},
    }


def initial_checkpoint(static):
    zero = "0" * 64
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "next_later_point_id": 1,
        "next_earlier_point_id": 0,
        "pairs_scanned": 0,
        "classification_counts": {
            "seed": 0,
            "old-new": 0,
            "new-new": 0,
        },
        "matched_pair_count": 0,
        "class_spectrum_counts": {},
        "later_birth_rank_counts": {},
        "primitive_direction_counts": {},
        "exact_orbit_pair_count": 0,
        "orbit_membership_counts": {},
        "match_stream_hash_chain": zero,
        "line_stream_hash_chains_by_class_spectrum": {},
        "witnesses_by_class": {},
        "orbit_witnesses": {},
        "seed_line_role_test": empty_role_test(),
        "terminal_summary": None,
        "last_run": None,
    }


def seal_checkpoint(checkpoint):
    payload = copy.deepcopy(checkpoint)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = stable_hash(payload)
    return payload


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def validate_cursor(checkpoint):
    later = checkpoint["next_later_point_id"]
    earlier = checkpoint["next_earlier_point_id"]
    if not 1 <= later <= EXPECTED_POINTS:
        raise AssertionError("diagnostic later cursor drift")
    if later == EXPECTED_POINTS:
        if earlier != 0:
            raise AssertionError("terminal earlier cursor drift")
        implied = EXPECTED_PAIRS
    else:
        if not 0 <= earlier < later:
            raise AssertionError("diagnostic earlier cursor drift")
        implied = later * (later - 1) // 2 + earlier
    if checkpoint["pairs_scanned"] != implied:
        raise AssertionError("diagnostic cursor/count drift")


def validate_counter_key_total(counter, expected, name):
    if sum(counter.values()) != expected:
        raise AssertionError(name + " count partition drift")
    if any(not isinstance(value, int) or value <= 0 for value in counter.values()):
        raise AssertionError(name + " contains a nonpositive count")


def load_checkpoint(path, static):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(checkpoint):
        raise AssertionError("diagnostic checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION or checkpoint[
        "static"
    ] != static:
        raise AssertionError("diagnostic checkpoint static/schema drift")
    validate_cursor(checkpoint)
    if sum(checkpoint["classification_counts"].values()) != checkpoint[
        "pairs_scanned"
    ]:
        raise AssertionError("diagnostic classification partition drift")
    matched = checkpoint["matched_pair_count"]
    validate_counter_key_total(
        checkpoint["class_spectrum_counts"], matched, "class/spectrum"
    ) if matched else None
    validate_counter_key_total(
        checkpoint["later_birth_rank_counts"], matched, "later-birth"
    ) if matched else None
    validate_counter_key_total(
        checkpoint["primitive_direction_counts"], matched, "direction"
    ) if matched else None
    if not 0 <= checkpoint["exact_orbit_pair_count"] <= matched:
        raise AssertionError("exact orbit pair count drift")
    if any(
        len(value) != 64
        for value in [checkpoint["match_stream_hash_chain"]]
        + list(
            checkpoint[
                "line_stream_hash_chains_by_class_spectrum"
            ].values()
        )
    ):
        raise AssertionError("diagnostic hash-chain shape drift")
    if checkpoint["status"] == "complete" and checkpoint[
        "pairs_scanned"
    ] != EXPECTED_PAIRS:
        raise AssertionError("complete diagnostic cursor drift")
    if checkpoint["status"] not in {"partial", "complete"}:
        raise AssertionError("unknown diagnostic checkpoint status")
    return checkpoint


def classify_pair(frozen, earlier, later):
    classification, birth_rank = frozen.classify_pair(earlier, later)
    if classification == "same-word-new-new":
        classification = "new-new"
    if classification not in {"seed", "old-new", "new-new"}:
        raise AssertionError("unknown pair classification")
    return classification, birth_rank


def increment(counter, key, amount=1):
    counter[key] = counter.get(key, 0) + amount


def retain_sample(buckets, key, record):
    bucket = buckets.setdefault(key, [])
    if len(bucket) < WITNESSES_PER_BUCKET:
        bucket.append(record)


def encode_direction_key(classification, spectrum, direction):
    return "|".join((
        classification,
        spectrum,
        ",".join(str(value) for value in direction),
    ))


def encode_birth_key(classification, spectrum, birth_rank):
    return "|".join((classification, spectrum, str(birth_rank)))


def class_spectrum_key(classification, spectrum):
    return classification + "|" + spectrum


def compact_witness(frozen, points, provenance, earlier_id, later_id,
                    classification, birth_rank, spectrum, direction, moment):
    witness = frozen.pair_witness(
        points,
        provenance,
        earlier_id,
        later_id,
        (
            "same-word-new-new"
            if classification == "new-new" else classification
        ),
        birth_rank,
        [spectrum],
    )
    witness["classification"] = classification
    if tuple(witness["canonical_primitive_direction"]) != direction:
        raise AssertionError("witness primitive direction drift")
    if tuple(witness["line_moment"]) != moment:
        raise AssertionError("witness line moment drift")
    return witness


def role_phase_key(role):
    return "|".join((
        "L" + str(role["level"]),
        role["phase"],
        "n=" + str(role["n"]),
    ))


def retain_role_sample(role_test, category, pair_record, role):
    record = {
        "pair": pair_record,
        "role": role,
    }
    retain_sample(role_test["samples"], category, record)


def update_seed_role_test(checkpoint, context, earlier_id, later_id,
                          direction, moment, witness):
    test = checkpoint["seed_line_role_test"]
    counts = test["counts"]
    counts["seed_E_pairs"] += 1

    pair_record = {
        "earlier_anchor_id": earlier_id,
        "later_anchor_id": later_id,
        "primitive_direction": list(direction),
        "absolute_line_moment": list(moment),
    }
    l5_matches = context["l5_roles"].get((direction, moment), ())
    if l5_matches:
        counts["L5_exact_phase_line_pairs"] += 1
    for role in l5_matches:
        counts["L5_exact_phase_line_roles"] += 1
        increment(test["phase_n_counts"], role_phase_key(role))
        retain_role_sample(test, "L5_exact_phase_line", pair_record, role)
        slots = role["macro_compatible_slots"]
        counts["L5_macro_compatible_roles"] += len(slots)
        if role["literal_selected_action"]:
            counts["L5_literal_selected_action_roles"] += 1
        for slot, child_cursor in zip(slots, role["child_cursors"]):
            phase_index = 0 if role["phase"] == "A" else 1
            next_phase = J_PHASES[1 - phase_index]["name"]
            next_n = role["n"] if role["phase"] == "A" else role["n"] - 1
            image_direction = primitive_direction(
                apply_matrix(M, direction)
            )
            image_moment = cross(
                apply_matrix(M, context["points"][earlier_id]),
                image_direction,
            )
            successor_roles = context["l6_roles"].get(
                (image_direction, image_moment), ()
            )
            exact = [
                child_role
                for child_role in successor_roles
                if child_role["gap"] == child_cursor
                and child_role["phase"] == next_phase
                and child_role["n"] == next_n
            ]
            child_anchor = apply_matrix(M, add(
                tuple(role["corridor_anchor"]),
                J_PHASES[phase_index]["control"],
            ))
            expected_successor_moment = cross(
                add(child_anchor, J_PHASES[1 - phase_index]["site"]),
                image_direction,
            )
            if expected_successor_moment != image_moment:
                raise AssertionError("macro edge lost exact affine line")
            if role["phase"] == "B" and role["n"] == 0:
                if exact:
                    raise AssertionError("terminal B,n=0 unexpectedly reentered")
                counts["L5_exact_terminal_forward_exit_transitions"] += 1
                retain_role_sample(
                    test,
                    "L5_exact_terminal_forward_exit_transition",
                    pair_record,
                    {
                        "source": role,
                        "child_gap": child_cursor,
                        "child_phase_site": list(J_PHASES[0]["site"]),
                        "child_primitive_direction": list(image_direction),
                        "child_absolute_line_moment": list(image_moment),
                        "source_slot": slot,
                    },
                )
                continue
            if len(exact) != 1:
                raise AssertionError(
                    "selected macro edge lost exact child line role",
                    earlier_id, later_id, role, slot, exact,
                )
            counts["L5_exact_selected_child_transitions"] += 1
            retain_role_sample(
                test,
                "L5_exact_selected_child_transition",
                pair_record,
                {"source": role, "target": exact[0], "source_slot": slot},
            )

    image_direction = primitive_direction(apply_matrix(M, direction))
    image_moment = cross(
        apply_matrix(M, context["points"][earlier_id]), image_direction
    )
    l6_matches = context["l6_roles"].get(
        (image_direction, image_moment), ()
    )
    if l6_matches:
        counts["L6_exact_phase_line_pairs"] += 1
    for role in l6_matches:
        counts["L6_exact_phase_line_roles"] += 1
        increment(test["phase_n_counts"], role_phase_key(role))
        retain_role_sample(test, "L6_exact_phase_line", pair_record, role)

    # The retained general witness is not duplicated into role samples, but
    # force its exact seed identity here so a future provenance drift fails.
    if witness["earlier_provenance"]["birth_rank"] != -1 or witness[
        "later_provenance"
    ]["birth_rank"] != -1:
        raise AssertionError("seed role test received a connector endpoint")


def update_match(checkpoint, context, earlier_id, later_id,
                 classification, birth_rank, spectrum, direction, moment):
    frozen = context["frozen"]
    points = context["points"]
    provenance = context["provenance"]
    witness = compact_witness(
        frozen, points, provenance, earlier_id, later_id,
        classification, birth_rank, spectrum, direction, moment,
    )
    record = {
        "earlier_point_id": earlier_id,
        "later_point_id": later_id,
        "classification": classification,
        "later_birth_rank": birth_rank,
        "spectrum": spectrum,
        "primitive_direction": list(direction),
        "exact_Pluecker_moment": list(moment),
    }
    checkpoint["matched_pair_count"] += 1
    class_key = class_spectrum_key(classification, spectrum)
    increment(checkpoint["class_spectrum_counts"], class_key)
    increment(
        checkpoint["later_birth_rank_counts"],
        encode_birth_key(classification, spectrum, birth_rank),
    )
    increment(
        checkpoint["primitive_direction_counts"],
        encode_direction_key(classification, spectrum, direction),
    )
    checkpoint["match_stream_hash_chain"] = hash_chain(
        checkpoint["match_stream_hash_chain"], record
    )
    previous = checkpoint[
        "line_stream_hash_chains_by_class_spectrum"
    ].get(class_key, "0" * 64)
    checkpoint["line_stream_hash_chains_by_class_spectrum"][class_key] = (
        hash_chain(previous, {
            "primitive_direction": list(direction),
            "exact_Pluecker_moment": list(moment),
            "later_birth_rank": birth_rank,
            "endpoint_ids": [earlier_id, later_id],
        })
    )
    retain_sample(checkpoint["witnesses_by_class"], classification, witness)

    memberships = context["orbit_lookup"].get(direction, ())
    if memberships:
        checkpoint["exact_orbit_pair_count"] += 1
    birth_cohort = "seed" if classification == "seed" else "connector-born"
    for membership in memberships:
        if membership["spectrum"] != spectrum:
            raise AssertionError("orbit/spectrum mismatch")
        orbit_key = "|".join((
            birth_cohort,
            classification,
            spectrum,
            membership["family"],
            "phase=" + membership["phase"],
            "n=" + str(membership["n"]),
        ))
        increment(checkpoint["orbit_membership_counts"], orbit_key)
        retain_sample(checkpoint["orbit_witnesses"], orbit_key, witness)

    if classification == "seed":
        update_seed_role_test(
            checkpoint, context, earlier_id, later_id,
            direction, moment, witness,
        )


def parse_direction_groups(counter):
    records = []
    for key, count in counter.items():
        classification, spectrum, encoded = key.split("|")
        direction = [int(value) for value in encoded.split(",")]
        records.append({
            "classification": classification,
            "spectrum": spectrum,
            "primitive_direction": direction,
            "pair_count": count,
        })
    records.sort(key=lambda item: (
        item["classification"], item["spectrum"],
        item["primitive_direction"],
    ))
    return records


def parse_birth_groups(counter):
    records = []
    for key, count in counter.items():
        classification, spectrum, rank = key.split("|")
        records.append({
            "classification": classification,
            "spectrum": spectrum,
            "later_birth_rank": int(rank),
            "pair_count": count,
        })
    records.sort(key=lambda item: (
        item["later_birth_rank"], item["classification"], item["spectrum"]
    ))
    return records


def direction_group_summary(counter):
    records = parse_direction_groups(counter)
    multiplicities = Counter(record["pair_count"] for record in records)
    top = sorted(
        records,
        key=lambda item: (
            -item["pair_count"], item["classification"], item["spectrum"],
            item["primitive_direction"],
        ),
    )[:20]
    return {
        "exact_group_records": records,
        "group_count": len(records),
        "group_record_stream_sha256": stable_hash(records),
        "pair_multiplicity_histogram": {
            str(value): count for value, count in sorted(multiplicities.items())
        },
        "top_20_groups": top,
    }


def birth_group_summary(counter):
    records = parse_birth_groups(counter)
    return {
        "exact_nonzero_group_records": records,
        "nonzero_group_count": len(records),
        "group_record_stream_sha256": stable_hash(records),
    }


def terminal_payload(checkpoint, policy):
    static = checkpoint["static"]
    if checkpoint["status"] != "complete" or checkpoint[
        "pairs_scanned"
    ] != EXPECTED_PAIRS:
        raise AssertionError("terminal diagnostic requested before completion")
    if checkpoint["classification_counts"] != static[
        "expected_full_classification_counts"
    ]:
        raise AssertionError("terminal classification census drift")
    matched = checkpoint["matched_pair_count"]
    direction_summary = direction_group_summary(
        checkpoint["primitive_direction_counts"]
    )
    birth_summary = birth_group_summary(
        checkpoint["later_birth_rank_counts"]
    )
    if sum(
        record["pair_count"]
        for record in direction_summary["exact_group_records"]
    ) != matched:
        raise AssertionError("terminal direction total drift")
    if sum(
        record["pair_count"]
        for record in birth_summary["exact_nonzero_group_records"]
    ) != matched:
        raise AssertionError("terminal birth total drift")
    orbit_pairs = checkpoint["exact_orbit_pair_count"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": (
            "exact finite full-pair spectrum and macro-orbit diagnostic; "
            "evidence only, not a certificate"
        ),
        "checker": {
            "path": "design/lattice_t_projective_spectrum_diagnostic.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "inputs": {
            key: static[key]
            for key in (
                "frozen_spectrum_checker",
                "strict_refutation_summary",
                "source_checkpoint",
                "terminal_audit_summary",
                "L5_state_sha256",
            )
        },
        "scope": {
            "points": static["point_count"],
            "unordered_pairs_scanned": checkpoint["pairs_scanned"],
            "all_unordered_pairs_scanned": True,
            "spectra": [label for label, _a, _b in SPECTRA],
            "pair_order": static["pair_order"],
            "exact_x_diameter": static["exact_x_diameter"],
            "macro_orbit_cutoffs": static["orbit_cutoffs"],
            "macro_direction_record_count": static[
                "orbit_direction_record_count"
            ],
            "macro_direction_record_stream_sha256": static[
                "orbit_direction_records_sha256"
            ],
        },
        "result": {
            "classification_counts_all_pairs": checkpoint[
                "classification_counts"
            ],
            "E_valued_pair_count": matched,
            "class_spectrum_counts": dict(sorted(
                checkpoint["class_spectrum_counts"].items()
            )),
            "primitive_direction_groups": direction_summary,
            "later_birth_rank_groups": birth_summary,
            "exact_affine_Pluecker_line_groups": {
                "group_count": matched,
                "multiplicity_histogram": ({"1": matched} if matched else {}),
                "reason_multiplicity_is_one": (
                    "the pinned independent audit proves no three collinear "
                    "points, so two distinct pairs cannot determine the same "
                    "exact affine line"
                ),
                "ordered_joint_match_stream_hash_chain": checkpoint[
                    "match_stream_hash_chain"
                ],
                "ordered_line_hash_chains_by_class_spectrum": dict(sorted(
                    checkpoint[
                        "line_stream_hash_chains_by_class_spectrum"
                    ].items()
                )),
            },
            "known_exact_macro_direction_orbits": {
                "distinct_matching_pairs": orbit_pairs,
                "E_cone_pairs_outside_both_exact_orbits": matched - orbit_pairs,
                "membership_counts": dict(sorted(
                    checkpoint["orbit_membership_counts"].items()
                )),
                "witnesses": checkpoint["orbit_witnesses"],
                "strict_first_witness_g_3_minus3_1_is_in_orbit": bool(
                    static["strict_first_witness_exact_orbit_memberships"]
                ),
            },
            "inherited_seed_J_cycle_affine_role_test": checkpoint[
                "seed_line_role_test"
            ],
            "witnesses_by_birth_class": checkpoint["witnesses_by_class"],
        },
        "commitments": {
            "static_state_sha256": static["static_state_sha256"],
            "construction_order_point_stream_sha256": static[
                "construction_order_point_stream_sha256"
            ],
            "provenance_stream_sha256": static[
                "provenance_stream_sha256"
            ],
            "actual_L5_selected_word_stream_sha256": static[
                "actual_L5_selected_word_stream_sha256"
            ],
            "actual_L6_parent_word_sha256": static[
                "actual_L6_parent_word_sha256"
            ],
            "actual_L6_anchor_stream_sha256": static[
                "actual_L6_anchor_stream_sha256"
            ],
            "actual_L6_owner_stream_sha256": static[
                "actual_L6_owner_stream_sha256"
            ],
            "J_cycle_role_indexes": static["J_cycle_role_indexes"],
        },
        "interpretation": {
            "proved_finite_facts": [
                "every unordered pair of the frozen audited 8268-point path is tested exactly against both spectra",
                "the exact named macro-direction membership test includes both single-phase directions and all n allowed by the finite x diameter",
                "the seed affine-role join uses exact Pluecker moments and the actual selected L5 parent-to-child cursor map",
            ],
            "diagnostic_only": [
                "frequency of E-valued pairs and exact-orbit pairs on this one frozen path",
                "absence or presence of the named seed-line cycle roles through the induced L6 skeleton",
            ],
            "not_proved": [
                "that forbidding the exact named direction orbits preserves a legal connector at every future stitch",
                "that all dangerous latent cycles are among the two named families",
                "a complete two-edge cycle join for the new policy, because selected L6 connector actions do not yet exist",
                "a level-uniform reachable-birth exclusion or far-secant tail bound",
                "an unconditional infinite construction or Erdos #193 theorem",
            ],
        },
    }
    payload["payload_sha256"] = stable_hash(payload)
    return payload


def run_chunk(args):
    started = time.monotonic()
    deadline = started + args.max_seconds
    policy = resource_policy(enforce=True)
    static, context = build_static_inputs(args.source, args.audit_summary)
    checkpoint = load_checkpoint(args.checkpoint, static)
    if checkpoint["status"] == "complete":
        return checkpoint, {
            "pairs_scanned_this_run": 0,
            "stop_reason": "terminal-checkpoint-already-present",
        }
    points = context["points"]
    provenance = context["provenance"]
    frozen = context["frozen"]
    later = checkpoint["next_later_point_id"]
    earlier = checkpoint["next_earlier_point_id"]
    scanned = 0
    since_save = 0
    stop_reason = "pair-limit"
    while later < EXPECTED_POINTS:
        while earlier < later:
            if scanned % DEADLINE_CHECK_INTERVAL == 0:
                if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
                    raise MemoryError("280-MiB diagnostic resident limit exceeded")
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
            classification, birth_rank = classify_pair(
                frozen, provenance[earlier], provenance[later]
            )
            direction_raw = subtract(points[later], points[earlier])
            spectrum = matched_spectrum(direction_raw)
            checkpoint["pairs_scanned"] += 1
            checkpoint["classification_counts"][classification] += 1
            if spectrum is not None:
                direction = primitive_direction(direction_raw)
                moment = cross(points[earlier], direction)
                update_match(
                    checkpoint, context, earlier, later,
                    classification, birth_rank, spectrum, direction, moment,
                )
            scanned += 1
            since_save += 1
            earlier += 1
            if since_save >= CHECKPOINT_PAIR_INTERVAL:
                checkpoint["next_later_point_id"] = later
                checkpoint["next_earlier_point_id"] = earlier
                save_checkpoint(args.checkpoint, checkpoint)
                since_save = 0
            if scanned >= args.max_pairs:
                stop_reason = "pair-limit"
                break
        if stop_reason == "time-limit" or scanned >= args.max_pairs:
            break
        if earlier == later:
            later += 1
            earlier = 0
    if later == EXPECTED_POINTS:
        checkpoint["status"] = "complete"
        earlier = 0
        stop_reason = "full-diagnostic-complete"
    elif earlier == later:
        later += 1
        earlier = 0
    checkpoint["next_later_point_id"] = later
    checkpoint["next_earlier_point_id"] = earlier
    validate_cursor(checkpoint)
    if checkpoint["status"] == "complete":
        terminal = terminal_payload(checkpoint, policy)
        atomic_json_dump(terminal, args.output)
        checkpoint["terminal_summary"] = {
            "path": str(Path(args.output).resolve()),
            "sha256": file_sha256(args.output),
            "bytes": Path(args.output).stat().st_size,
            "payload_sha256": terminal["payload_sha256"],
        }
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    checkpoint["last_run"] = {
        "pairs_scanned_this_run": scanned,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
        "resource_policy": policy,
    }
    save_checkpoint(args.checkpoint, checkpoint)
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > HARD_MAX_SECONDS or resident > MAX_RESIDENT_BYTES:
        raise RuntimeError("projective diagnostic resource bound exceeded")
    return checkpoint, {
        "pairs_scanned_this_run": scanned,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
    }


def self_check():
    frozen, frozen_snapshot = load_frozen_checker()
    _strict, strict_snapshot = verify_strict_summary()
    if frozen_snapshot["sha256"] != EXPECTED_FROZEN_CHECKER_SHA256:
        raise AssertionError("self-check frozen checker drift")
    if strict_snapshot["payload_sha256"] != (
        EXPECTED_STRICT_SUMMARY_PAYLOAD_SHA256
    ):
        raise AssertionError("self-check strict summary drift")

    records, lookup, cutoffs = orbit_catalog(3 * (9 ** 20))
    expected = {
        ("J_11_over_3_cycle", "A", 0): (3, -1, 3),
        ("J_11_over_3_cycle", "B", 0): (3, -3, -2),
        ("latent_348_over_275_cycle", "8", 0): (55, 34, 18),
        ("latent_348_over_275_cycle", "16", 0): (55, -18, 28),
    }
    observed = {
        (record["family"], record["phase"], record["n"]): tuple(
            record["primitive_direction"]
        )
        for record in records
        if record["n"] == 0
    }
    if observed != expected:
        raise AssertionError("single-phase orbit seed drift", observed)
    if lookup.get((3, -3, 1)):
        raise AssertionError("known strict witness falsely entered macro orbit")
    if any(
        phase["first_excluded_n"] != 21
        for phase in cutoffs["J_11_over_3_cycle"][
            "phase_cutoffs"
        ].values()
    ):
        raise AssertionError("synthetic orbit cutoff drift")
    if matched_spectrum((3, -3, 1)) != "11/3":
        raise AssertionError("strict witness left J cone")
    if matched_spectrum((55, 34, 18)) != "348/275":
        raise AssertionError("latent base left J cone")

    j_directions = {
        (record["phase"], record["n"]): tuple(
            record["primitive_direction"]
        )
        for record in records
        if record["family"] == "J_11_over_3_cycle"
    }
    for n in range(1, 20):
        if primitive_direction(apply_matrix(M, j_directions[("A", n)])) != (
            j_directions[("B", n)]
        ):
            raise AssertionError("A-to-B direction transition drift")
        if primitive_direction(apply_matrix(M, j_directions[("B", n)])) != (
            j_directions[("A", n - 1)]
        ):
            raise AssertionError("B-to-A countdown direction drift")

    for index, phase in enumerate(J_PHASES):
        prefixes, interiors, endpoint = word_geometry(phase["literal_word"])
        if endpoint != apply_matrix(M, MENU[1]):
            raise AssertionError("literal cycle endpoint drift")
        if prefixes[phase["literal_slot"]] != phase["control"]:
            raise AssertionError("literal cycle control drift")
        if phase["site"] in interiors:
            raise AssertionError("literal cycle word hits carried site")
        successor = J_PHASES[1 - index]
        if apply_matrix(M, subtract(phase["site"], phase["control"])) != (
            successor["site"]
        ):
            raise AssertionError("cycle affine site transition drift")
        if phase_macro_slots(phase["literal_word"], phase) != (
            phase["literal_slot"],
        ):
            raise AssertionError("literal macro-slot drift")

    synthetic = initial_checkpoint({"synthetic": True})
    synthetic["next_later_point_id"] = 10
    synthetic["next_earlier_point_id"] = 7
    synthetic["pairs_scanned"] = 52
    synthetic["classification_counts"]["old-new"] = 52
    validate_cursor(synthetic)
    first = hash_chain("0" * 64, {"a": 1})
    if first != hash_chain("0" * 64, {"a": 1}) or first == "0" * 64:
        raise AssertionError("hash-chain determinism drift")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "large_construction_inputs_opened": False,
        "frozen_checker_pin_verified": True,
        "strict_refutation_pin_verified": True,
        "exact_orbit_families": len(FAMILIES),
        "single_phase_sequences": sum(
            len(family["phase_names"]) for family in FAMILIES
        ),
        "strict_witness_g_3_minus3_1_in_first_21_J_macro_iterates": False,
        "cycle_affine_transitions_checked": len(J_PHASES),
        "resume_cursor_checked": True,
        "hash_chain_checked": True,
    }


def preflight(args):
    started = time.monotonic()
    policy = resource_policy(enforce=True)
    static, context = build_static_inputs(args.source, args.audit_summary)
    probe = initial_checkpoint(static)
    probe_earlier, probe_later = 30, 33
    probe_class, probe_birth = classify_pair(
        context["frozen"],
        context["provenance"][probe_earlier],
        context["provenance"][probe_later],
    )
    probe_raw = subtract(
        context["points"][probe_later], context["points"][probe_earlier]
    )
    probe_spectrum = matched_spectrum(probe_raw)
    probe_direction = primitive_direction(probe_raw)
    probe_moment = cross(context["points"][probe_earlier], probe_direction)
    update_match(
        probe, context, probe_earlier, probe_later,
        probe_class, probe_birth, probe_spectrum,
        probe_direction, probe_moment,
    )
    if probe["matched_pair_count"] != 1 or probe[
        "exact_orbit_pair_count"
    ] != 0:
        raise AssertionError("strict witness preflight classification drift")
    if Path(args.checkpoint).exists():
        checkpoint = load_checkpoint(args.checkpoint, static)
        checkpoint_status = checkpoint["status"]
        pairs_already_scanned = checkpoint["pairs_scanned"]
    else:
        checkpoint_status = "absent"
        pairs_already_scanned = 0
    if time.monotonic() - started > MAX_WORK_SECONDS:
        raise RuntimeError("preflight exceeded work-time guard")
    if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
        raise MemoryError("preflight exceeded resident-memory guard")
    return {
        "status": "ready; no unordered pair scanned",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "static_state_sha256": static["static_state_sha256"],
        "points": len(context["points"]),
        "unordered_pairs": EXPECTED_PAIRS,
        "pairs_scanned_by_preflight": 0,
        "checkpoint_status": checkpoint_status,
        "pairs_already_scanned_in_checkpoint": pairs_already_scanned,
        "exact_x_diameter": static["exact_x_diameter"],
        "orbit_cutoffs": static["orbit_cutoffs"],
        "orbit_direction_record_count": static[
            "orbit_direction_record_count"
        ],
        "strict_first_witness_probe": {
            "primitive_direction": list(probe_direction),
            "spectrum": probe_spectrum,
            "exact_macro_orbit_memberships": 0,
            "seed_J_cycle_affine_role_counts": probe[
                "seed_line_role_test"
            ]["counts"],
        },
        "J_cycle_role_indexes": static["J_cycle_role_indexes"],
        "actual_L6_child_corridors": len(context["child_steps"]),
        "resource_policy": policy,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def estimate():
    return {
        "status": "no large construction input opened and no pair scanned",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "points": EXPECTED_POINTS,
        "unordered_pairs": EXPECTED_PAIRS,
        "default_max_pairs_per_chunk": DEFAULT_MAX_PAIRS,
        "chunks_from_pair_cap": math.ceil(EXPECTED_PAIRS / DEFAULT_MAX_PAIRS),
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "hard_maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "terminal_behavior": "scan every pair; never stop at an E witness",
        "stored_data": (
            "exact marginal group counts, deterministic hash chains, and at "
            "most three witnesses per bounded class; not every matching pair"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("estimate", "self-check", "preflight", "run")
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument(
        "--audit-summary", default=str(DEFAULT_AUDIT_SUMMARY)
    )
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=float, default=MAX_WORK_SECONDS)
    parser.add_argument("--max-pairs", type=int, default=DEFAULT_MAX_PAIRS)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= MAX_WORK_SECONDS:
        raise ValueError("max-seconds outside (0,110]")
    if not 1 <= args.max_pairs <= HARD_MAX_PAIRS:
        raise ValueError("max-pairs outside [1,10000000]")
    if args.mode == "self-check":
        result = self_check()
    elif args.mode == "estimate":
        result = estimate()
    elif args.mode == "preflight":
        result = preflight(args)
    else:
        checkpoint, observation = run_chunk(args)
        result = {
            "status": checkpoint["status"],
            "pairs_scanned": checkpoint["pairs_scanned"],
            "pairs_total": EXPECTED_PAIRS,
            "E_valued_pairs_seen": checkpoint["matched_pair_count"],
            "exact_macro_orbit_pairs_seen": checkpoint[
                "exact_orbit_pair_count"
            ],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": file_sha256(args.checkpoint),
            "terminal_summary": checkpoint["terminal_summary"],
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
