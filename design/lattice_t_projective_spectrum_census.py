#!/usr/bin/env python3
"""Exact finite-spectrum secant census for the frozen lattice-T L5 walk.

The strengthened policy forbids every pair direction in the two projective
spectra

    E = {11/3, 348/275},
    J(r,y,z) = (3*y*y - y*z + 3*z*z) / (r*r).

No division is used by the census.  For e=a/b it evaluates the homogeneous
integer polynomial

    F_e(r,y,z) = b*(3*y*y - y*z + 3*z*z) - a*r*r.

The 8,268 points are ordered as in the construction store: all L5 anchors,
then connector interiors by chronological stitch and within-word slot.  The
pair scan uses increasing later point id and then increasing earlier point id.
Consequently the first zero is the exact lexicographically earliest witness
by later endpoint birth rank/id and earlier id.  A witness terminates the
experiment because it refutes the strict policy.  If there is no witness, all
34,175,778 unordered pairs are checked.

The construction checkpoint and its independent terminal audit summary are
immutable inputs.  The audit-summary pins below intentionally remain PENDING
until that audit finishes.  Census mode refuses to open the source while any
audit pin is pending.  Synthetic self-check and estimate open no large input.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import pickle
import resource
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L5-primary.json")
DEFAULT_AUDIT_SUMMARY = (
    ROOT / "design" / "lattice-T-chronological-L5-summary.json"
)
DEFAULT_CHECKPOINT = Path(
    "/tmp/lattice-T-L5-projective-spectrum-census-checkpoint.json"
)
DEFAULT_OUTPUT = (
    ROOT / "design" / "lattice-T-projective-spectrum-census-summary.json"
)
L5_STATE = ROOT / "gate2-l7-construction-L5.pkl"

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
EXPECTED_SOURCE_PRODUCER_SHA256 = (
    "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
)
EXPECTED_L5_STATE_SHA256 = (
    "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
)
EXPECTED_AUDIT_CHECKER_SHA256 = (
    "8c616ea15a7aaae3e1d70f07415dd74641c2cf4fafa22050c873d31bb1ac64e8"
)
EXPECTED_AUDIT_SUMMARY_SHA256 = (
    "88fa0f41674d71cc9cf84fc1bd4b70949ab91cd1e8d83a435bb7b6bec5fc9df5"
)
EXPECTED_AUDIT_SUMMARY_BYTES = 3_061
EXPECTED_AUDIT_RAW_SHA256 = (
    "144eb1d78a2a9c62be0747be50a2e135a8b8e91d5d2335e64398bf5af5146194"
)
EXPECTED_AUDIT_RAW_PAYLOAD_SHA256 = (
    "832e8ce9c44f2528ffd3e39996572b3622e5d4b29ed47bfa593621d8c346528b"
)

EXPECTED_POINTS = 8_268
EXPECTED_ANCHORS = 2_458
EXPECTED_GAPS = 2_457
EXPECTED_PAIRS = 34_175_778
SCHEMA_VERSION = 1
SPECTRA = (("11/3", 11, 3), ("348/275", 348, 275))
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
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
PROCESS_START_CHECKER_SHA256 = None


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def stable_hash(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


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
        raise RuntimeError("census requires thread controls=1 and nice>=15")
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
    observed = file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("projective-spectrum checker changed during run")


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


def ensure_final_audit_pins():
    pins = {
        "audit_summary": EXPECTED_AUDIT_SUMMARY_SHA256,
        "audit_raw": EXPECTED_AUDIT_RAW_SHA256,
        "audit_raw_payload": EXPECTED_AUDIT_RAW_PAYLOAD_SHA256,
    }
    if any(value == "PENDING" for value in pins.values()) or not (
        EXPECTED_AUDIT_SUMMARY_BYTES > 0
    ):
        raise RuntimeError("terminal L5 audit summary is not pinned", pins)


def apply_matrix(matrix, vector):
    return tuple(
        sum(row[index] * vector[index] for index in range(3))
        for row in matrix
    )


def add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive_direction(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise AssertionError("zero pair displacement")
    primitive = tuple(value // divisor for value in vector)
    first = next(value for value in primitive if value)
    if first < 0:
        primitive = tuple(-value for value in primitive)
    return primitive


def quadratic(direction):
    _r, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def f_values(direction):
    r, _y, _z = direction
    q = quadratic(direction)
    return {
        label: denominator * q - numerator * r * r
        for label, numerator, denominator in SPECTRA
    }


def matched_spectra(direction):
    return [label for label, value in f_values(direction).items() if value == 0]


def word_interiors(start, word):
    point = start
    interiors = []
    for child in word[:-1]:
        point = add(point, MENU[child])
        interiors.append(point)
    return tuple(interiors)


def endpoint(start, word):
    point = start
    for child in word:
        point = add(point, MENU[child])
    return point


def verify_terminal_audit_summary(path):
    ensure_final_audit_pins()
    path = Path(path)
    if path.stat().st_size != EXPECTED_AUDIT_SUMMARY_BYTES:
        raise AssertionError("terminal audit summary byte-size drift")
    observed = file_sha256(path)
    if observed != EXPECTED_AUDIT_SUMMARY_SHA256:
        raise AssertionError("terminal audit summary digest drift")
    with path.open() as handle:
        summary = json.load(handle)
    if summary["checker"]["sha256"] != EXPECTED_AUDIT_CHECKER_SHA256:
        raise AssertionError("terminal audit checker drift")
    if summary["source_checkpoint"]["sha256"] != EXPECTED_SOURCE_SHA256:
        raise AssertionError("terminal audit source drift")
    raw = summary["terminal_raw_artifact"]
    if raw["sha256"] != EXPECTED_AUDIT_RAW_SHA256 or raw[
        "payload_sha256"
    ] != EXPECTED_AUDIT_RAW_PAYLOAD_SHA256:
        raise AssertionError("terminal audit raw commitment drift")
    result = summary["result"]
    required = (
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "global_empty_yz_verified_at_every_stitch",
        "final_no_new_yz_coincidence",
        "independent_ordered_no_three_collinear_verified",
    )
    if result["points"] != EXPECTED_POINTS or result["gaps"] != EXPECTED_GAPS:
        raise AssertionError("terminal audit size drift")
    if any(not result[key] for key in required):
        raise AssertionError("terminal audit is incomplete")
    return summary, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "raw_sha256": raw["sha256"],
        "raw_payload_sha256": raw["payload_sha256"],
    }


def load_source(path):
    path = Path(path)
    if path.stat().st_size != EXPECTED_SOURCE_BYTES:
        raise AssertionError("source checkpoint byte-size drift")
    observed = file_sha256(path)
    if observed != EXPECTED_SOURCE_SHA256:
        raise AssertionError("source checkpoint digest drift")
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(source) or internal != (
        EXPECTED_SOURCE_PAYLOAD_SHA256
    ):
        raise AssertionError("source checkpoint payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source["status"] != "construction-complete-audit-pending":
        raise AssertionError("source checkpoint is not construction-complete")
    if source["next_construction_rank"] != EXPECTED_GAPS or len(
        source["selection_records"]
    ) != EXPECTED_GAPS:
        raise AssertionError("source checkpoint record count drift")
    static = source["static"]
    expected_static = {
        "checker_sha256": EXPECTED_SOURCE_PRODUCER_SHA256,
        "action_channel": "zero",
        "projection_policy": "global-empty",
        "require_digit_simple": False,
        "survivor_certificate_target": 1,
    }
    for key, expected in expected_static.items():
        if static.get(key) != expected:
            raise AssertionError("source primary-policy drift", key)
    if source["prefix"]["prefix_state_sha256"] != (
        EXPECTED_SOURCE_PREFIX_SHA256
    ) or source["prefix"]["selection_record_stream_sha256"] != (
        EXPECTED_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("source prefix commitment drift")
    if stable_hash(source["selection_records"]) != (
        EXPECTED_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("source selection stream drift")
    return source, {
        "path": str(path.resolve()),
        "sha256": observed,
        "bytes": path.stat().st_size,
        "payload_sha256": internal,
    }


def load_l5_state():
    observed = file_sha256(L5_STATE)
    if observed != EXPECTED_L5_STATE_SHA256:
        raise AssertionError("pinned L5 state drift")
    with L5_STATE.open("rb") as handle:
        state = pickle.load(handle)
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    schedule = tuple(state["order"])
    if len(parent_word) != EXPECTED_GAPS or len(anchors) != EXPECTED_ANCHORS:
        raise AssertionError("pinned L5 state size drift")
    if sorted(schedule) != list(range(EXPECTED_GAPS)):
        raise AssertionError("pinned L5 schedule is not a permutation")
    return parent_word, anchors, schedule, observed


def reconstruct_points(source):
    parent_word, anchors, schedule, state_sha = load_l5_state()
    points = list(anchors)
    provenance = [{
        "point_id": point_id,
        "birth_rank": -1,
        "birth_kind": "seed-anchor",
        "gap": None,
        "interior_slot": None,
    } for point_id in range(len(anchors))]
    point_set = set(points)
    if len(point_set) != len(points):
        raise AssertionError("pinned anchor skeleton repeats a point")
    interior_counts = []
    for rank, record in enumerate(source["selection_records"]):
        gap = schedule[rank]
        step = parent_word[gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("source schedule/step drift", rank)
        word = tuple(record["selected_word"])
        if not word or any(not 0 <= child < len(MENU) for child in word):
            raise AssertionError("source selected-word alphabet drift", rank)
        start = anchors[gap]
        if endpoint(start, word) != anchors[gap + 1]:
            raise AssertionError("source selected-word endpoint drift", rank)
        interiors = word_interiors(start, word)
        interior_counts.append(len(interiors))
        for slot, point in enumerate(interiors):
            if point in point_set:
                raise AssertionError("source selected point repeats", rank, slot)
            point_id = len(points)
            points.append(point)
            point_set.add(point)
            provenance.append({
                "point_id": point_id,
                "birth_rank": rank,
                "birth_kind": "connector-interior",
                "gap": gap,
                "interior_slot": slot,
            })
    if len(points) != EXPECTED_POINTS:
        raise AssertionError("reconstructed source point count drift")
    prefix = source["prefix"]
    if prefix["placed_point_count"] != EXPECTED_POINTS:
        raise AssertionError("source prefix point count drift")
    if point_stream_sha256(points) != prefix[
        "construction_order_point_stream_sha256"
    ]:
        raise AssertionError("source construction-order point stream drift")
    if stable_hash(sorted(points)) != prefix["point_set_sha256"]:
        raise AssertionError("source point-set commitment drift")
    return tuple(points), tuple(provenance), tuple(interior_counts), state_sha


def provenance_commitment(provenance):
    return stable_hash(provenance)


def expected_classification_counts(interior_counts):
    seed = EXPECTED_ANCHORS * (EXPECTED_ANCHORS - 1) // 2
    same = sum(count * (count - 1) // 2 for count in interior_counts)
    return {
        "seed": seed,
        "old-new": EXPECTED_PAIRS - seed - same,
        "same-word-new-new": same,
    }


def expected_later_birth_counts(interior_counts):
    counts = [EXPECTED_ANCHORS * (EXPECTED_ANCHORS - 1) // 2]
    prior = EXPECTED_ANCHORS
    for new in interior_counts:
        counts.append(new * prior + new * (new - 1) // 2)
        prior += new
    if len(counts) != EXPECTED_GAPS + 1 or sum(counts) != EXPECTED_PAIRS:
        raise AssertionError("expected later-birth count construction drift")
    return counts


def static_state(source_snapshot, audit_snapshot, points, provenance,
                 interior_counts, state_sha):
    fields = {
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_checkpoint": source_snapshot,
        "terminal_audit_summary": audit_snapshot,
        "L5_state_sha256": state_sha,
        "spectra": [{
            "label": label,
            "numerator": numerator,
            "denominator": denominator,
            "polynomial": (
                f"{denominator}*(3*y^2-y*z+3*z^2)-{numerator}*r^2"
            ),
        } for label, numerator, denominator in SPECTRA],
        "point_count": len(points),
        "pair_count": EXPECTED_PAIRS,
        "construction_order_point_stream_sha256": point_stream_sha256(points),
        "point_set_sha256": stable_hash(sorted(points)),
        "provenance_stream_sha256": provenance_commitment(provenance),
        "interior_count_stream_sha256": stable_hash(interior_counts),
        "pair_order": "increasing later point id, then increasing earlier id",
    }
    fields["static_state_sha256"] = stable_hash(fields)
    return fields


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


def initial_checkpoint(static):
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
            "same-word-new-new": 0,
        },
        "pairs_scanned_by_later_birth_rank": [0] * (EXPECTED_GAPS + 1),
        "matched_spectrum_counts": {label: 0 for label, _a, _b in SPECTRA},
        "earliest_witness": None,
        "terminal_summary": None,
        "last_run": None,
    }


def validate_cursor(checkpoint):
    later = checkpoint["next_later_point_id"]
    earlier = checkpoint["next_earlier_point_id"]
    if not 1 <= later <= EXPECTED_POINTS:
        raise AssertionError("pair cursor later-id drift")
    if later == EXPECTED_POINTS:
        if earlier != 0:
            raise AssertionError("terminal pair cursor earlier-id drift")
        implied = EXPECTED_PAIRS
    else:
        if not 0 <= earlier < later:
            raise AssertionError("pair cursor earlier-id drift")
        implied = later * (later - 1) // 2 + earlier
    if checkpoint["pairs_scanned"] != implied:
        raise AssertionError("pair cursor/count drift")


def load_checkpoint(path, static):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(checkpoint):
        raise AssertionError("spectrum checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    if checkpoint["schema_version"] != SCHEMA_VERSION or checkpoint[
        "static"
    ] != static:
        raise AssertionError("spectrum checkpoint static/schema drift")
    validate_cursor(checkpoint)
    if sum(checkpoint["classification_counts"].values()) != checkpoint[
        "pairs_scanned"
    ]:
        raise AssertionError("classification count partition drift")
    if sum(checkpoint["pairs_scanned_by_later_birth_rank"]) != checkpoint[
        "pairs_scanned"
    ]:
        raise AssertionError("later-birth count partition drift")
    matched = sum(checkpoint["matched_spectrum_counts"].values())
    if checkpoint["status"] == "partial" and matched:
        raise AssertionError("partial checkpoint already contains a match")
    if checkpoint["status"] == "refuted" and (
        matched != 1 or checkpoint["earliest_witness"] is None
    ):
        raise AssertionError("refuted checkpoint witness drift")
    if checkpoint["status"] == "complete" and (
        checkpoint["pairs_scanned"] != EXPECTED_PAIRS or matched
    ):
        raise AssertionError("complete checkpoint census drift")
    return checkpoint


def classify_pair(left, right):
    left_birth = left["birth_rank"]
    right_birth = right["birth_rank"]
    if left_birth > right_birth:
        raise AssertionError("point ids are not in birth order")
    if right_birth == -1:
        return "seed", -1
    if left_birth == right_birth:
        if left["gap"] != right["gap"]:
            raise AssertionError("same-rank interiors have different gaps")
        return "same-word-new-new", right_birth
    return "old-new", right_birth


def pair_witness(points, provenance, earlier_id, later_id, classification,
                 later_birth_rank, matches):
    earlier = points[earlier_id]
    later = points[later_id]
    raw_direction = subtract(later, earlier)
    primitive = primitive_direction(raw_direction)
    r = primitive[0]
    q = quadratic(primitive)
    j_value = None if r == 0 else Fraction(q, r * r)
    return {
        "earlier_point_id": earlier_id,
        "later_point_id": later_id,
        "earlier_point": list(earlier),
        "later_point": list(later),
        "earlier_provenance": provenance[earlier_id],
        "later_provenance": provenance[later_id],
        "later_endpoint_birth_rank": later_birth_rank,
        "classification": classification,
        "raw_direction": list(raw_direction),
        "canonical_primitive_direction": list(primitive),
        "line_moment": list(cross(earlier, primitive)),
        "quadratic_Q": q,
        "J": (
            None if j_value is None else {
                "numerator": j_value.numerator,
                "denominator": j_value.denominator,
                "label": f"{j_value.numerator}/{j_value.denominator}",
            }
        ),
        "F_values_on_raw_direction": f_values(raw_direction),
        "F_values_on_primitive_direction": f_values(primitive),
        "matched_spectra": matches,
        "earliest_order_key": [later_birth_rank, later_id, earlier_id],
    }


def terminal_payload(checkpoint, static, expected_classes,
                     expected_birth_counts, policy):
    refuted = checkpoint["status"] == "refuted"
    if not refuted:
        if checkpoint["classification_counts"] != expected_classes:
            raise AssertionError("terminal classification census drift")
        if checkpoint["pairs_scanned_by_later_birth_rank"] != (
            expected_birth_counts
        ):
            raise AssertionError("terminal later-birth census drift")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": (
            "exact earliest finite-spectrum secant witness"
            if refuted else
            "exact full-pair finite-spectrum exclusion certificate"
        ),
        "checker": {
            "path": "design/lattice_t_projective_spectrum_census.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_census": True,
        },
        "resource_policy": policy,
        "inputs": {
            "source_checkpoint": static["source_checkpoint"],
            "terminal_audit_summary": static["terminal_audit_summary"],
            "L5_state_sha256": static["L5_state_sha256"],
        },
        "scope": {
            "points": EXPECTED_POINTS,
            "unordered_pairs_total": EXPECTED_PAIRS,
            "unordered_pairs_scanned": checkpoint["pairs_scanned"],
            "all_unordered_pairs_scanned": not refuted,
            "spectra": static["spectra"],
            "pair_order": static["pair_order"],
        },
        "result": {
            "strict_policy_survives_frozen_L5": not refuted,
            "first_weaker_survivor_is_first_stronger_survivor": (
                not refuted
            ),
            "classification_counts_scanned": checkpoint[
                "classification_counts"
            ],
            "expected_full_classification_counts": expected_classes,
            "matched_spectrum_counts": checkpoint[
                "matched_spectrum_counts"
            ],
            "earliest_witness": checkpoint["earliest_witness"],
        },
        "commitments": {
            "static_state_sha256": static["static_state_sha256"],
            "construction_order_point_stream_sha256": static[
                "construction_order_point_stream_sha256"
            ],
            "point_set_sha256": static["point_set_sha256"],
            "provenance_stream_sha256": static[
                "provenance_stream_sha256"
            ],
            "later_birth_pair_count_stream_sha256": stable_hash(
                checkpoint["pairs_scanned_by_later_birth_rank"]
            ),
        },
        "proved": ([
            "the displayed pair is the earliest exact E-valued secant in construction birth/id order",
            "the strict finite-spectrum policy is already false on this frozen L5 path",
        ] if refuted else [
            "every unordered pair of the frozen audited 8268-point L5 walk was checked exactly",
            "no seed, old-new, or same-word-new-new secant has J in {11/3,348/275}",
            "the frozen L5 path is a finite witness for the strengthened finite-spectrum policy",
        ]),
        "not_proved": [
            "uniform connector availability beyond this frozen finite orbit",
            "exclusion of latent families with other projective spectra or affine moments",
            "a general far-secant tail lemma or an unconditional infinite construction",
        ],
    }
    payload["payload_sha256"] = stable_hash(payload)
    return payload


def run_chunk(args):
    started = time.monotonic()
    deadline = started + args.max_seconds
    policy = resource_policy(enforce=True)
    _audit_summary, audit_snapshot = verify_terminal_audit_summary(
        args.audit_summary
    )
    source, source_snapshot = load_source(args.source)
    points, provenance, interior_counts, state_sha = reconstruct_points(source)
    static = static_state(
        source_snapshot, audit_snapshot, points, provenance,
        interior_counts, state_sha,
    )
    expected_classes = expected_classification_counts(interior_counts)
    expected_birth_counts = expected_later_birth_counts(interior_counts)
    checkpoint = load_checkpoint(args.checkpoint, static)
    if checkpoint["status"] in {"complete", "refuted"}:
        return checkpoint, {
            "pairs_scanned_this_run": 0,
            "stop_reason": "terminal-checkpoint-already-present",
        }
    later = checkpoint["next_later_point_id"]
    earlier = checkpoint["next_earlier_point_id"]
    scanned = 0
    since_save = 0
    stop_reason = "pair-limit"
    while later < EXPECTED_POINTS:
        while earlier < later:
            if scanned % DEADLINE_CHECK_INTERVAL == 0:
                if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
                    raise MemoryError("280-MiB census resident limit exceeded")
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
            classification, later_birth_rank = classify_pair(
                provenance[earlier], provenance[later]
            )
            direction = subtract(points[later], points[earlier])
            matches = matched_spectra(direction)
            checkpoint["pairs_scanned"] += 1
            checkpoint["classification_counts"][classification] += 1
            checkpoint["pairs_scanned_by_later_birth_rank"][
                later_birth_rank + 1
            ] += 1
            scanned += 1
            since_save += 1
            earlier += 1
            if matches:
                if len(matches) != 1:
                    raise AssertionError("one direction matched both spectra")
                checkpoint["matched_spectrum_counts"][matches[0]] += 1
                checkpoint["earliest_witness"] = pair_witness(
                    points, provenance, earlier - 1, later, classification,
                    later_birth_rank, matches,
                )
                checkpoint["status"] = "refuted"
                stop_reason = "earliest-witness"
                break
            if since_save >= CHECKPOINT_PAIR_INTERVAL:
                checkpoint["next_later_point_id"] = later
                checkpoint["next_earlier_point_id"] = earlier
                save_checkpoint(args.checkpoint, checkpoint)
                since_save = 0
            if scanned >= args.max_pairs:
                stop_reason = "pair-limit"
                break
        if checkpoint["status"] == "refuted" or stop_reason == "time-limit" or (
            scanned >= args.max_pairs
        ):
            break
        if earlier == later:
            later += 1
            earlier = 0
    if later == EXPECTED_POINTS and checkpoint["status"] != "refuted":
        checkpoint["status"] = "complete"
        stop_reason = "full-census-complete"
        earlier = 0
    elif earlier == later:
        later += 1
        earlier = 0
    checkpoint["next_later_point_id"] = later
    checkpoint["next_earlier_point_id"] = earlier
    validate_cursor(checkpoint)
    if checkpoint["status"] in {"complete", "refuted"}:
        terminal = terminal_payload(
            checkpoint, static, expected_classes, expected_birth_counts, policy
        )
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
        raise RuntimeError("projective-spectrum census resource bound exceeded")
    return checkpoint, {
        "pairs_scanned_this_run": scanned,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
    }


def self_check():
    d = (3, -1, 3)
    h = (55, 34, 18)
    if matched_spectra(d) != ["11/3"]:
        raise AssertionError("11/3 witness drift")
    if matched_spectra(h) != ["348/275"]:
        raise AssertionError("348/275 witness drift")
    for direction, label in ((d, "11/3"), (h, "348/275")):
        image = apply_matrix(M_BAL3, direction)
        if matched_spectra(image) != [label]:
            raise AssertionError("M-invariant spectrum drift", label)
        raw = f_values(direction)[label]
        scaled = f_values(image)[label]
        if raw != 0 or scaled != 9 * raw:
            raise AssertionError("homogeneous M identity drift", label)
    generic = (2, 1, 4)
    generic_image = apply_matrix(M_BAL3, generic)
    for label, value in f_values(generic).items():
        if f_values(generic_image)[label] != 9 * value:
            raise AssertionError("generic homogeneous M identity drift", label)
    if matched_spectra((0, 1, 0)) or matched_spectra((1, 0, 0)):
        raise AssertionError("axis direction falsely matched a positive spectrum")
    synthetic = (
        {"birth_rank": -1, "gap": None},
        {"birth_rank": -1, "gap": None},
        {"birth_rank": 0, "gap": 4},
        {"birth_rank": 0, "gap": 4},
        {"birth_rank": 1, "gap": 2},
    )
    expected = (
        ("seed", -1),
        ("old-new", 0),
        ("same-word-new-new", 0),
        ("old-new", 1),
    )
    observed = (
        classify_pair(synthetic[0], synthetic[1]),
        classify_pair(synthetic[0], synthetic[2]),
        classify_pair(synthetic[2], synthetic[3]),
        classify_pair(synthetic[3], synthetic[4]),
    )
    if observed != expected:
        raise AssertionError("synthetic birth classification drift")
    test_checkpoint = initial_checkpoint({"synthetic": True})
    test_checkpoint["next_later_point_id"] = 10
    test_checkpoint["next_earlier_point_id"] = 7
    test_checkpoint["pairs_scanned"] = 52
    test_checkpoint["classification_counts"]["old-new"] = 52
    test_checkpoint["pairs_scanned_by_later_birth_rank"][1] = 52
    validate_cursor(test_checkpoint)
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "large_inputs_opened": False,
        "audit_pins_finalized": EXPECTED_AUDIT_SUMMARY_SHA256 != "PENDING",
        "spectra": [label for label, _a, _b in SPECTRA],
        "M_invariance_witnesses_checked": 2,
        "generic_M_polynomial_identities_checked": len(SPECTRA),
        "axis_nonmatches_checked": 2,
        "birth_classifications_checked": 4,
        "resume_cursor_checked": True,
    }


def estimate():
    return {
        "status": "no large input opened and no pair scanned",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "audit_pins_finalized": EXPECTED_AUDIT_SUMMARY_SHA256 != "PENDING",
        "points": EXPECTED_POINTS,
        "unordered_pairs": EXPECTED_PAIRS,
        "default_max_pairs_per_chunk": DEFAULT_MAX_PAIRS,
        "chunks_from_pair_cap_if_no_witness": math.ceil(
            EXPECTED_PAIRS / DEFAULT_MAX_PAIRS
        ),
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "hard_maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "terminal_behavior": "stop at earliest witness, else scan all pairs",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "run"))
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
    else:
        checkpoint, observation = run_chunk(args)
        result = {
            "status": checkpoint["status"],
            "pairs_scanned": checkpoint["pairs_scanned"],
            "pairs_total": EXPECTED_PAIRS,
            "earliest_witness": checkpoint["earliest_witness"],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": file_sha256(args.checkpoint),
            "terminal_summary": checkpoint["terminal_summary"],
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
