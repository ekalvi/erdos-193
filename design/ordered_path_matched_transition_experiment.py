#!/usr/bin/env python3
"""Exact matched-transition census for the ordered-path safety programme.

This checker has two deliberately separated phases.

Phase A is a poison-blind metadata census over the pinned gate2 L5--L8
construction pickles and the terminal-audited primary lattice-T L6 lineage.
For every nonboundary stitch it retains a *contiguous ordered factor* of the
single realized path: the pending parent gap, the two preceding scheduler
actions, the complete immediate-parent connector blocks containing them, and
every actual connector already placed in that natural-path interval.  Future
connector choices remain hidden.  The current action is joined to that factor
in one canonical state-action key; Phase B replays that exact same key schema
at the actual next stitch.  Phase A never constructs a poison mask.  It emits
an immutable, deterministically ordered panel manifest rather than sampling
convenient occurrences.

Phase B independently reconstructs each manifested prefix and its actual
successor from scheduler rank zero.  It scans every prefix endpoint and every
word in the complete connector domain.  Its exact killed-word union contains
all three nonintrinsic legality channels:

* collision;
* old--old--new (a candidate interior on an old secant); and
* old--new--new (an old point on a line through two candidate interiors).

There is no distance, endpoint-age, or pair cutoff.  Witness effects are kept
in overlapping near and birth/chronological/spatial-shell masks.  Every raw
mask is fixed-width little-endian bytes tied to one explicit domain identity;
helpers refuse to compare masks from different domains.  Complete source,
action, and actual-successor records remain atomic.  A deterministic CEGAR
pass may refine repeated records by near atoms, then far-shell atoms, then a
source-observable normalized Pluecker token backtraced from the least
successor difference.  Stable endpoint IDs are evidence only and are never a
permitted refinement feature.

The output is a finite-trace diagnostic.  Even a nonvacuous pass does not
prove that the state universe is finite, cover alternate legal histories,
give universal successor closure, establish a tail contraction/rank, or
certify a greatest fixed point.

The terminal primary-L6 pins and the Phase-A manifest pins below are explicit
trust boundaries.  They intentionally remain PENDING until their immutable
artifacts have been independently reviewed.  ``estimate`` opens no pickle or
large JSON.  Heavy modes require one thread, nice>=15, and at most two shards.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import math
import os
import pickle
import resource
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402


SCHEMA_VERSION = 1
LOCAL_RADIUS = 40
SOFT_DOMAIN_WORDS = 10_000
HARD_DOMAIN_WORDS = 50_000
MIN_CLASS_OCCURRENCES = 4
MAX_PANEL_SCANS = 24
MAX_SHARDS = 2
MAX_SECONDS = 110.0
MAX_WORK_ITEMS = 10_000
CHANNELS = ("collision", "old-old-new", "old-new-new")
THREAD_ENVIRONMENT = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

GATE_LEVELS = (5, 6, 7, 8)
GATE_INPUTS = {
    5: {
        "path": "gate2-l7-construction-L5.pkl",
        "sha256": "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
        "bytes": 71_933,
        "gaps": 2_457,
    },
    6: {
        "path": "gate2-l7-construction-L6.pkl",
        "sha256": "70fa3baac057492fb8ad325eba5417bdc1e98fbd474bec37dc5f5465230f9298",
        "bytes": 242_888,
        "gaps": 8_213,
    },
    7: {
        "path": "gate2-l7-construction-L7.pkl",
        "sha256": "304e71eb74939662c0d0251864193171e74f49fd2023a98df09dc45d99fa0660",
        "bytes": 818_165,
        "gaps": 27_696,
    },
    8: {
        "path": "gate2-l7-construction-L8.pkl",
        "sha256": "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141",
        "bytes": 2_709_484,
        "gaps": 92_731,
    },
}
EXPECTED_GATE_STITCHES = 131_097
EXPECTED_PRIMARY_L6_STITCHES = 8_267

PINNED_SMALL_INPUTS = {
    "gate_run.py": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "amplify_rich.py": "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e",
    "imbricate193.py": "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb",
    "connector_domains4.pkl": "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f",
    "dstar5_fragile.pkl": "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3",
    "viz/walk3d-data.json": "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883",
}

PRIMARY_PRODUCER = ROOT / "design" / "lattice_t_l6_continuation.py"
PRIMARY_AUDITOR = ROOT / "design" / "lattice_t_l6_audit.py"
EXPECTED_PRIMARY_PRODUCER_SHA256 = (
    "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
)
EXPECTED_PRIMARY_AUDITOR_SHA256 = (
    "b9f39fd20dfad194d45420b221617cf6b1baa872aa2aa1f4a38182274dece6f5"
)
EXPECTED_PRIMARY_SOURCE_SHA256 = (
    "82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7"
)
EXPECTED_PRIMARY_SOURCE_BYTES = 18_699_543
EXPECTED_PRIMARY_SOURCE_PAYLOAD_SHA256 = (
    "772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa"
)
EXPECTED_PRIMARY_SOURCE_PREFIX_SHA256 = (
    "7626fbb39cedfeff134c064989f54054e268d0c3fd881a4cd8b0782ae2eb917d"
)
EXPECTED_PRIMARY_SOURCE_SELECTION_SHA256 = (
    "219ad3095dafea4aecba62be79e8f4d446c814285c0aa3e2a1a4282bdc99981c"
)

# Freeze these only from the independently completed L6 terminal audit.
EXPECTED_PRIMARY_TERMINAL_SHA256 = "PENDING"
EXPECTED_PRIMARY_TERMINAL_BYTES = 0
EXPECTED_PRIMARY_TERMINAL_PAYLOAD_SHA256 = "PENDING"
EXPECTED_PRIMARY_TERMINAL_ORDERED_POINT_STREAM_SHA256 = "PENDING"
EXPECTED_PRIMARY_TERMINAL_FLAT_WORD_SHA256 = "PENDING"
EXPECTED_PRIMARY_TERMINAL_POINT_SET_SHA256 = "PENDING"
EXPECTED_PRIMARY_TERMINAL_FINAL_YZ_SHA256 = "PENDING"

# Phase B is a separate reviewed experiment.  Freeze these from the write-once
# Phase-A panel manifest; never let Phase B silently select its own panel.
EXPECTED_PHASE_A_CHECKER_SHA256 = "PENDING"
EXPECTED_PANEL_MANIFEST_SHA256 = "PENDING"
EXPECTED_PANEL_MANIFEST_BYTES = 0
EXPECTED_PANEL_MANIFEST_PAYLOAD_SHA256 = "PENDING"

ABC_POLICY = Path("/tmp/l8-third-ply-cegar-canonical.json")
EXPECTED_ABC_POLICY_SHA256 = (
    "f5b197116c223fe32c5458a800b382e8a4994393439ca2ba1c8ab9cc5d2b9ccf"
)
EXPECTED_ABC_POLICY_BYTES = 4_329_036
ABC_MOTIF_STEPS = (14, 34, 48, 19, 17)
ABC_MOTIF_LEVEL = 8
ABC_MOTIF_RANK = 67_010

DEFAULT_PRIMARY_SOURCE = Path(
    "/tmp/lattice-T-chronological-L6-checkpoint-v1.json"
)
DEFAULT_PRIMARY_TERMINAL = Path(
    "/tmp/lattice-T-chronological-L6-audit-v1.json"
)
DEFAULT_PRIMARY_PARENT_SOURCE = Path(
    "/tmp/lattice-T-chronological-L5-primary.json"
)
DEFAULT_PRIMARY_PARENT_TERMINAL = Path(
    "/tmp/lattice-T-chronological-L5-audit-v2.json"
)
DEFAULT_CENSUS = Path("/tmp/ordered-path-matched-transition-census.json")
DEFAULT_MANIFEST = Path("/tmp/ordered-path-matched-transition-panel.json")
DEFAULT_CHECKPOINT = Path(
    "/tmp/ordered-path-matched-transition-scan-checkpoint.json"
)
DEFAULT_RAW = Path("/tmp/ordered-path-matched-transition-raw.json")
DEFAULT_OUTPUT = Path("/tmp/ordered-path-matched-transition-verdict.json")

PROCESS_START_CHECKER_SHA256 = None


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def assert_checker_unchanged():
    if file_sha256(Path(__file__).resolve()) != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("matched-transition checker changed during execution")


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


def immutable_json_dump(value, path):
    """Write once; an existing byte-different manifest is a hard failure."""
    assert_checker_unchanged()
    path = Path(path).resolve()
    encoded = json.dumps(value, sort_keys=True, indent=2).encode() + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError("immutable artifact already differs", str(path))
        return
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def stable_file_snapshot(path, expected_sha256, expected_bytes=None):
    path = Path(path).resolve()
    before = path.stat()
    if expected_bytes is not None and before.st_size != expected_bytes:
        raise AssertionError("pinned byte-size drift", str(path), before.st_size)
    observed = file_sha256(path)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, field) for field in fields) != tuple(
        getattr(after, field) for field in fields
    ):
        raise RuntimeError("input changed while being hashed", str(path))
    if observed != expected_sha256:
        raise AssertionError("pinned digest drift", str(path), observed)
    return {
        "path": str(path),
        "sha256": observed,
        "bytes": after.st_size,
    }


def unseal_json(path, payload_field, description):
    with Path(path).open() as handle:
        value = json.load(handle)
    internal = value.pop(payload_field, None)
    observed = stable_hash(value)
    value[payload_field] = internal
    if internal != observed:
        raise AssertionError(description + " internal payload drift")
    return value, internal


def maximum_resident_bytes():
    observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return observed if sys.platform == "darwin" else observed * 1024


def enforce_resources(mode, shard_count=1):
    if mode not in {"census", "scan", "finalize"}:
        return {
            "enforced": False,
            "processes": 1,
            "threads": 1,
            "maximum_shards": MAX_SHARDS,
        }
    if not 1 <= shard_count <= MAX_SHARDS:
        raise RuntimeError("matched-transition scan permits at most two shards")
    environment = {name: os.environ.get(name) for name in THREAD_ENVIRONMENT}
    if any(value != "1" for value in environment.values()):
        raise RuntimeError(
            "all numerical-library thread variables must equal 1",
            environment,
        )
    if os.getpriority(os.PRIO_PROCESS, 0) < 15:
        raise RuntimeError("heavy modes require nice -n 15")
    return {
        "enforced": True,
        "processes": 1,
        "threads": 1,
        "declared_shards": shard_count,
        "maximum_shards": MAX_SHARDS,
        "nice": os.getpriority(os.PRIO_PROCESS, 0),
        "thread_environment": environment,
    }


def acquire_core_lease():
    """Take one of two cooperative experiment slots for this process."""
    handles = []
    for slot in range(MAX_SHARDS):
        path = Path(f"/tmp/ordered-path-matched-transition-core-{slot}.lock")
        handle = path.open("a+")
        handles.append(handle)
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            continue
        for other in handles:
            if other is not handle:
                other.close()
        return handle, slot
    for handle in handles:
        handle.close()
    raise RuntimeError("both cooperative matched-transition core slots are busy")


def terminal_pins_finalized():
    values = (
        EXPECTED_PRIMARY_TERMINAL_SHA256,
        EXPECTED_PRIMARY_TERMINAL_PAYLOAD_SHA256,
        EXPECTED_PRIMARY_TERMINAL_ORDERED_POINT_STREAM_SHA256,
        EXPECTED_PRIMARY_TERMINAL_FLAT_WORD_SHA256,
        EXPECTED_PRIMARY_TERMINAL_POINT_SET_SHA256,
        EXPECTED_PRIMARY_TERMINAL_FINAL_YZ_SHA256,
    )
    return EXPECTED_PRIMARY_TERMINAL_BYTES > 0 and all(
        value != "PENDING" for value in values
    )


def panel_pins_finalized():
    values = (
        EXPECTED_PHASE_A_CHECKER_SHA256,
        EXPECTED_PANEL_MANIFEST_SHA256,
        EXPECTED_PANEL_MANIFEST_PAYLOAD_SHA256,
    )
    return EXPECTED_PANEL_MANIFEST_BYTES > 0 and all(
        value != "PENDING" for value in values
    )


def verify_small_inputs():
    snapshots = {}
    for relative, expected in PINNED_SMALL_INPUTS.items():
        snapshots[relative] = stable_file_snapshot(ROOT / relative, expected)
    for level, expected in GATE_INPUTS.items():
        snapshots[expected["path"]] = stable_file_snapshot(
            ROOT / expected["path"], expected["sha256"], expected["bytes"]
        )
    snapshots["primary_producer"] = stable_file_snapshot(
        PRIMARY_PRODUCER, EXPECTED_PRIMARY_PRODUCER_SHA256
    )
    snapshots["primary_auditor"] = stable_file_snapshot(
        PRIMARY_AUDITOR, EXPECTED_PRIMARY_AUDITOR_SHA256
    )
    return snapshots


def verify_primary_source(path):
    snapshot = stable_file_snapshot(
        path, EXPECTED_PRIMARY_SOURCE_SHA256, EXPECTED_PRIMARY_SOURCE_BYTES
    )
    source, internal = unseal_json(path, "checkpoint_payload_sha256", "primary L6")
    if internal != EXPECTED_PRIMARY_SOURCE_PAYLOAD_SHA256:
        raise AssertionError("primary L6 payload pin drift")
    records = source.get("selection_records", [])
    if source.get("status") != "construction-complete-audit-pending":
        raise AssertionError("primary L6 source is not construction-complete")
    if (
        source.get("next_construction_rank") != EXPECTED_PRIMARY_L6_STITCHES
        or len(records) != EXPECTED_PRIMARY_L6_STITCHES
        or source.get("pending_scan") is not None
    ):
        raise AssertionError("primary L6 source extent drift")
    if source["prefix"]["prefix_state_sha256"] != (
        EXPECTED_PRIMARY_SOURCE_PREFIX_SHA256
    ):
        raise AssertionError("primary L6 prefix pin drift")
    if stable_hash(records) != EXPECTED_PRIMARY_SOURCE_SELECTION_SHA256:
        raise AssertionError("primary L6 selection pin drift")
    snapshot["payload_sha256"] = internal
    return source, snapshot


def verify_primary_terminal(path, source, source_snapshot):
    if not terminal_pins_finalized():
        raise RuntimeError(
            "Phase A is locked until every primary-L6 terminal pin is frozen"
        )
    snapshot = stable_file_snapshot(
        path, EXPECTED_PRIMARY_TERMINAL_SHA256,
        EXPECTED_PRIMARY_TERMINAL_BYTES,
    )
    terminal, internal = unseal_json(
        path, "terminal_payload_sha256", "primary L6 terminal"
    )
    if internal != EXPECTED_PRIMARY_TERMINAL_PAYLOAD_SHA256:
        raise AssertionError("primary L6 terminal payload pin drift")
    if terminal.get("status") != "exact independent terminal finite certificate":
        raise AssertionError("primary L6 terminal status drift")
    if terminal.get("checker", {}).get("sha256") != (
        EXPECTED_PRIMARY_AUDITOR_SHA256
    ):
        raise AssertionError("primary L6 terminal auditor drift")
    if terminal.get("source_checkpoint") != source_snapshot:
        raise AssertionError("primary L6 terminal/source snapshot disagreement")
    required = (
        "construction_completed",
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "fast_reference_agreement_verified_for_every_exact_test",
        "global_empty_yz_verified_at_every_stitch",
        "final_no_new_yz_coincidence",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not terminal.get("result", {}).get(field) for field in required):
        raise AssertionError("primary L6 terminal certificate is incomplete")
    commitments = terminal.get("commitments", {})
    expected = {
        "source_prefix_state_sha256": EXPECTED_PRIMARY_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": (
            EXPECTED_PRIMARY_SOURCE_SELECTION_SHA256
        ),
        "alternate_ordered_point_stream_sha256": (
            EXPECTED_PRIMARY_TERMINAL_ORDERED_POINT_STREAM_SHA256
        ),
        "alternate_flat_step_word_sha256": (
            EXPECTED_PRIMARY_TERMINAL_FLAT_WORD_SHA256
        ),
        "final_point_set_sha256": EXPECTED_PRIMARY_TERMINAL_POINT_SET_SHA256,
        "final_yz_occupancy_sha256": (
            EXPECTED_PRIMARY_TERMINAL_FINAL_YZ_SHA256
        ),
    }
    if any(commitments.get(key) != value for key, value in expected.items()):
        raise AssertionError("primary L6 terminal commitment drift")
    snapshot["payload_sha256"] = internal
    return terminal, snapshot


def add(a, b):
    return tuple(a[index] + b[index] for index in range(3))


def sub(a, b):
    return tuple(a[index] - b[index] for index in range(3))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def primitive(vector):
    divisor = math.gcd(
        math.gcd(abs(vector[0]), abs(vector[1])), abs(vector[2])
    )
    if divisor == 0:
        return None
    result = tuple(value // divisor for value in vector)
    for value in result:
        if value < 0:
            return tuple(-entry for entry in result)
        if value > 0:
            return result
    raise AssertionError("nonzero primitive vector has no sign")


def line_key(a, b):
    direction = primitive(sub(b, a))
    if direction is None:
        raise AssertionError("candidate line has repeated points")
    return direction, cross(a, direction)


def chebyshev(a, b):
    return max(abs(a[index] - b[index]) for index in range(3))


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def endpoint(start, word):
    result = tuple(start)
    for letter in word:
        result = add(result, MENU[letter])
    return result


def step_word(points):
    index = {tuple(step): ordinal for ordinal, step in enumerate(MENU)}
    result = []
    for left, right in zip(points, points[1:]):
        delta = sub(right, left)
        if delta not in index:
            raise AssertionError("point stream uses a step outside MENU", delta)
        result.append(index[delta])
    return tuple(result)


def domain_metadata(domain):
    sites = set()
    lines = set()
    incidences = 0
    for word in domain:
        interiors = tuple(word_interiors((0, 0, 0), word))
        word_atoms = {("site", point) for point in interiors}
        for left_index, left in enumerate(interiors):
            for right in interiors[left_index + 1:]:
                word_atoms.add(("line", line_key(left, right)))
        incidences += len(word_atoms)
        sites.update(point for kind, point in word_atoms if kind == "site")
        lines.update(value for kind, value in word_atoms if kind == "line")
    directions = {record[0] for record in lines}
    return {
        "words": len(domain),
        "domain_sha256": stable_hash([list(word) for word in domain]),
        "candidate_sites": len(sites),
        "candidate_lines": len(lines),
        "candidate_line_directions": len(directions),
        "word_atom_incidences": incidences,
    }


def build_domain_catalog():
    domains, d24 = load_domains()
    domains = {
        int(step): tuple(tuple(word) for word in words)
        for step, words in domains.items()
    }
    if set(domains) != set(range(len(MENU))):
        raise AssertionError("connector domain step set drift")
    catalog = {}
    for step in range(len(MENU)):
        record = domain_metadata(domains[step])
        record["step"] = step
        record["D2_4_words"] = d24[step]
        record["domain_id"] = stable_hash({
            "step": step,
            "words": record["words"],
            "sha256": record["domain_sha256"],
        })
        catalog[step] = record
    return domains, d24, catalog


def build_viz_ancestry():
    with (ROOT / "viz" / "walk3d-data.json").open() as handle:
        viz = json.load(handle)
    levels = viz.get("levels", [])
    if len(levels) < 5:
        raise AssertionError("viz ancestry does not reach level 4")
    points = {
        level: tuple(tuple(point) for point in levels[level]["points"])
        for level in range(5)
    }
    origins = {
        0: tuple({
            "stable_id": f"viz:L0:P{index}",
            "origin_birth_level": 0,
            "origin_birth_owner": None,
            "origin_birth_rank": None,
            "origin_interior_slot": None,
            "birth_parent_endpoint_stable_ids": [],
            "generation_lineage": [{
                "level": 0,
                "kind": "base-point",
                "path_index": index,
            }],
        } for index in range(len(points[0])))
    }
    gap_roles = {
        0: tuple({
            "physical_root": f"viz:L0:G{gap}",
            "chain": [],
        } for gap in range(len(points[0]) - 1))
    }
    for level in range(1, 5):
        parents = levels[level].get("parents")
        if not isinstance(parents, list) or len(parents) != len(points[level]):
            raise AssertionError("viz parent map extent drift", level)
        anchor_indices = []
        for parent_index, prior_point in enumerate(points[level - 1]):
            target = apply(M_BAL3, prior_point)
            candidates = [
                index for index, point in enumerate(points[level])
                if point == target
            ]
            if len(candidates) != 1:
                raise AssertionError("viz scaled anchor multiplicity drift", level)
            anchor_indices.append(candidates[0])
        if anchor_indices != sorted(anchor_indices):
            raise AssertionError("viz anchors lost natural order", level)

        current_origins = [None] * len(points[level])
        for parent_index, anchor_index in enumerate(anchor_indices):
            inherited = copy.deepcopy(origins[level - 1][parent_index])
            inherited["generation_lineage"].append({
                "level": level,
                "kind": "scaled-anchor",
                "parent_path_index": parent_index,
                "path_index": anchor_index,
            })
            current_origins[anchor_index] = inherited
        current_roles = [None] * (len(points[level]) - 1)
        for owner_gap in range(len(anchor_indices) - 1):
            left = anchor_indices[owner_gap]
            right = anchor_indices[owner_gap + 1]
            word = step_word(points[level][left:right + 1])
            parent_step = step_word(points[level - 1])[owner_gap]
            if endpoint(points[level][left], word) != points[level][right]:
                raise AssertionError("viz connector endpoint drift", level)
            for slot, child_gap in enumerate(range(left, right)):
                current_roles[child_gap] = {
                    "physical_root": f"viz:L{level - 1}:G{owner_gap}",
                    "chain": [{
                        "owner_level": level - 1,
                        "parent_step": parent_step,
                        "parent_word": list(word),
                        "slot": slot,
                    }] + copy.deepcopy(gap_roles[level - 1][owner_gap]["chain"]),
                }
                if slot + 1 < len(word):
                    current_origins[child_gap + 1] = {
                        "stable_id": (
                            f"viz:L{level}:G{owner_gap}:I{slot}"
                        ),
                        "origin_birth_level": level,
                        "origin_birth_owner": owner_gap,
                        "origin_birth_rank": None,
                        "origin_interior_slot": slot,
                        "birth_parent_endpoint_stable_ids": [
                            origins[level - 1][owner_gap]["stable_id"],
                            origins[level - 1][owner_gap + 1]["stable_id"],
                        ],
                        "generation_lineage": [{
                            "level": level,
                            "kind": "connector-interior",
                            "owner_gap": owner_gap,
                            "interior_slot": slot,
                            "path_index": child_gap + 1,
                        }],
                    }
        if any(record is None for record in current_origins):
            raise AssertionError("viz ancestry left an unowned point", level)
        if any(record is None for record in current_roles):
            raise AssertionError("viz ancestry left an unowned gap", level)
        origins[level] = tuple(current_origins)
        gap_roles[level] = tuple(current_roles)
    return {
        "points": points[4],
        "origins": origins[4],
        "gap_roles": gap_roles[4],
    }


def scaled_origins(parent_origins, level):
    result = []
    for index, origin in enumerate(parent_origins):
        record = copy.deepcopy(origin)
        record["generation_lineage"].append({
            "level": level,
            "kind": "scaled-anchor",
            "parent_path_index": index,
            "path_index": None,
        })
        result.append(record)
    return tuple(result)


def complete_path(
    family, level, parent_points, parent_origins, parent_gap_roles,
    parent_word, anchors, selected_by_gap, rank_by_gap,
):
    if tuple(parent_word) != step_word(parent_points):
        raise AssertionError("trace parent word/point stream drift", family, level)
    expected_anchors = tuple(apply(M_BAL3, point) for point in parent_points)
    if tuple(anchors) != expected_anchors:
        raise AssertionError("trace anchors are not scaled parent", family, level)
    anchor_origins = scaled_origins(parent_origins, level)
    points = [anchors[0]]
    origins = [copy.deepcopy(anchor_origins[0])]
    origins[0]["generation_lineage"][-1]["path_index"] = 0
    child_roles = []
    for gap, word in enumerate(selected_by_gap):
        word = tuple(word)
        if endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("selected connector endpoint drift", family, gap)
        parent_ids = [
            anchor_origins[gap]["stable_id"],
            anchor_origins[gap + 1]["stable_id"],
        ]
        for slot, letter in enumerate(word):
            child_roles.append({
                "physical_root": f"{family}:L{level}:G{gap}",
                "chain": [{
                    "owner_level": level,
                    "parent_step": parent_word[gap],
                    "parent_word": list(word),
                    "slot": slot,
                }] + copy.deepcopy(parent_gap_roles[gap]["chain"]),
            })
            if slot + 1 < len(word):
                point = add(points[-1], MENU[letter])
                points.append(point)
                origins.append({
                    "stable_id": f"{family}:L{level}:G{gap}:I{slot}",
                    "origin_birth_level": level,
                    "origin_birth_owner": gap,
                    "origin_birth_rank": rank_by_gap[gap],
                    "origin_interior_slot": slot,
                    "birth_parent_endpoint_stable_ids": parent_ids,
                    "generation_lineage": [{
                        "level": level,
                        "kind": "connector-interior",
                        "owner_gap": gap,
                        "owner_construction_rank": rank_by_gap[gap],
                        "interior_slot": slot,
                        "path_index": len(points) - 1,
                    }],
                })
            else:
                points.append(anchors[gap + 1])
                inherited = copy.deepcopy(anchor_origins[gap + 1])
                inherited["generation_lineage"][-1]["path_index"] = (
                    len(points) - 1
                )
                origins.append(inherited)
    if len(points) != len(origins) or len(points) != len(set(points)):
        raise AssertionError("completed trace path repeats or loses provenance")
    if len(child_roles) != len(points) - 1:
        raise AssertionError("completed trace child-role extent drift")
    return {
        "points": tuple(points),
        "origins": tuple(origins),
        "gap_roles": tuple(child_roles),
        "anchor_origins": anchor_origins,
    }


def prefix_point_counts(anchors, schedule, selected_by_gap):
    """Point count immediately before each rank, plus the terminal count."""
    counts = [len(anchors)]
    for gap in schedule:
        counts.append(counts[-1] + max(0, len(selected_by_gap[gap]) - 1))
    return tuple(counts)


def load_gate_traces(viz):
    traces = {}
    parent = viz
    total = 0
    for level in GATE_LEVELS:
        expected = GATE_INPUTS[level]
        with (ROOT / expected["path"]).open("rb") as handle:
            state = pickle.load(handle)
        parent_word = tuple(state["parent_word"])
        anchors = tuple(tuple(point) for point in state["anchors"])
        schedule = tuple(state["order"])
        selected = tuple(tuple(state["words"][gap]) for gap in range(
            len(parent_word)
        ))
        rank_by_gap = [None] * len(parent_word)
        for rank, gap in enumerate(schedule):
            rank_by_gap[gap] = rank
        if len(parent_word) != expected["gaps"]:
            raise AssertionError("gate gap extent drift", level)
        if sorted(schedule) != list(range(len(parent_word))):
            raise AssertionError("gate schedule is not a permutation", level)
        completed = complete_path(
            "gate2", level,
            parent["points"], parent["origins"], parent["gap_roles"],
            parent_word, anchors, selected, tuple(rank_by_gap),
        )
        trace_id = f"gate2-L{level}"
        traces[trace_id] = {
            "trace_id": trace_id,
            "family": "gate2",
            "level": level,
            "parent_word": parent_word,
            "anchors": anchors,
            "anchor_origins": completed["anchor_origins"],
            "gap_roles": parent["gap_roles"],
            "schedule": schedule,
            "rank_by_gap": tuple(rank_by_gap),
            "selected_by_gap": selected,
            "prefix_points_by_rank": prefix_point_counts(
                anchors, schedule, selected
            ),
            "completed": completed,
        }
        parent = completed
        total += len(parent_word)
    if total != EXPECTED_GATE_STITCHES:
        raise AssertionError("gate stitch census drift", total)
    return traces


def import_primary_producer():
    import importlib.util
    specification = importlib.util.spec_from_file_location(
        "matched_transition_pinned_primary", PRIMARY_PRODUCER
    )
    if specification is None or specification.loader is None:
        raise ImportError("cannot load pinned primary producer")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if file_sha256(module.__file__) != EXPECTED_PRIMARY_PRODUCER_SHA256:
        raise AssertionError("loaded primary producer identity drift")
    return module


def load_primary_trace(args, viz, source, terminal):
    producer = import_primary_producer()
    parent_source, _source_snapshot = producer.verify_parent_source(
        args.primary_parent_source
    )
    parent_terminal, _terminal_snapshot = producer.verify_parent_terminal(
        args.primary_parent_terminal, _source_snapshot
    )
    ordered_parent = producer.reconstruct_ordered_parent(
        parent_source, parent_terminal
    )
    base_word, base_anchors, base_schedule = producer.rescue.load_l5_state()
    base_word = tuple(base_word)
    base_anchors = tuple(tuple(point) for point in base_anchors)
    base_schedule = tuple(base_schedule)
    selected_l5 = [None] * len(base_word)
    rank_l5 = [None] * len(base_word)
    for rank, record in enumerate(parent_source["selection_records"]):
        gap = base_schedule[rank]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, base_word[gap]
        ):
            raise AssertionError("primary L5 selection identity drift")
        selected_l5[gap] = tuple(record["selected_word"])
        rank_l5[gap] = rank
    primary_l5 = complete_path(
        "primary", 5,
        viz["points"], viz["origins"], viz["gap_roles"],
        base_word, base_anchors, tuple(selected_l5), tuple(rank_l5),
    )
    if primary_l5["points"] != tuple(ordered_parent["points"]):
        raise AssertionError("primary L5 provenance misses audited parent")

    parent_word = tuple(ordered_parent["word"])
    anchors = tuple(apply(M_BAL3, point) for point in ordered_parent["points"])
    selected = [None] * len(parent_word)
    schedule = []
    rank_by_gap = [None] * len(parent_word)
    for rank, record in enumerate(source["selection_records"]):
        gap = record["gap"]
        if (record["construction_rank"], record["step"]) != (
            rank, parent_word[gap]
        ):
            raise AssertionError("primary L6 selection identity drift")
        schedule.append(gap)
        rank_by_gap[gap] = rank
        selected[gap] = tuple(record["selected_word"])
    completed = complete_path(
        "primary", 6,
        primary_l5["points"], primary_l5["origins"],
        primary_l5["gap_roles"], parent_word, anchors,
        tuple(selected), tuple(rank_by_gap),
    )
    commitments = terminal["commitments"]
    if point_stream_sha256(completed["points"]) != commitments[
        "alternate_ordered_point_stream_sha256"
    ]:
        raise AssertionError("primary L6 natural path/terminal drift")
    return {
        "trace_id": "primary-L6",
        "family": "primary",
        "level": 6,
        "parent_word": parent_word,
        "anchors": anchors,
        "anchor_origins": completed["anchor_origins"],
        "gap_roles": primary_l5["gap_roles"],
        "schedule": tuple(schedule),
        "rank_by_gap": tuple(rank_by_gap),
        "selected_by_gap": tuple(selected),
        "prefix_points_by_rank": prefix_point_counts(
            anchors, tuple(schedule), tuple(selected)
        ),
        "completed": completed,
    }


def load_all_traces(args):
    snapshots = verify_small_inputs()
    source, source_snapshot = verify_primary_source(args.primary_source)
    terminal, terminal_snapshot = verify_primary_terminal(
        args.primary_terminal, source, source_snapshot
    )
    viz = build_viz_ancestry()
    traces = load_gate_traces(viz)
    primary = load_primary_trace(args, viz, source, terminal)
    traces[primary["trace_id"]] = primary
    snapshots["primary_source"] = source_snapshot
    snapshots["primary_terminal"] = terminal_snapshot
    return traces, snapshots


def relative_sign(value):
    return -1 if value < 0 else (1 if value > 0 else 0)


def scheduler_phase(trace, rank, d24):
    schedule = trace["schedule"]
    gaps = [schedule[index] for index in range(rank - 2, rank + 2)]
    steps = [trace["parent_word"][gap] for gap in gaps]
    priorities = [d24[step] for step in steps]
    current_gap = gaps[2]
    return {
        "priority_D2_4": priorities[2],
        "neighbor_priority_relations": [
            relative_sign(value - priorities[2]) for value in priorities
        ],
        "neighbor_natural_gap_relations": [
            relative_sign(gap - current_gap) for gap in gaps
        ],
        "same_priority_with_predecessor": priorities[1] == priorities[2],
        "same_priority_with_successor": priorities[3] == priorities[2],
    }


def owner_block(trace, gap):
    chain = trace["gap_roles"][gap]["chain"]
    if not chain:
        return gap, gap
    immediate = chain[0]
    slot = immediate["slot"]
    length = len(immediate["parent_word"])
    return gap - slot, gap - slot + length - 1


def canonical_role_chain(trace, gap):
    """Retain exact ancestry roles without retaining an absolute horizon."""
    result = []
    for role in trace["gap_roles"][gap]["chain"]:
        record = copy.deepcopy(role)
        owner_level = record.pop("owner_level")
        record["owner_level_age"] = trace["level"] - owner_level
        result.append(record)
    return result


def ordered_factor(trace, rank):
    schedule = trace["schedule"]
    current_gap = schedule[rank]
    causal_gaps = (schedule[rank - 2], schedule[rank - 1], current_gap)
    blocks = [owner_block(trace, gap) for gap in causal_gaps]
    lower = min(block[0] for block in blocks)
    upper = max(block[1] for block in blocks)
    if not (0 <= lower <= upper < len(trace["parent_word"])):
        raise AssertionError("ordered factor block outside parent path")
    origin = trace["anchors"][current_gap]
    records = []
    for gap in range(lower, upper + 1):
        local_rank = trace["rank_by_gap"][gap]
        if local_rank < rank:
            status = "placed"
            visible_word = list(trace["selected_by_gap"][gap])
        elif gap == current_gap:
            status = "current"
            visible_word = None
        else:
            status = "future-hidden"
            visible_word = None
        records.append({
            "natural_gap_offset": gap - current_gap,
            "scheduler_rank_offset": local_rank - rank,
            "start_relative": list(sub(trace["anchors"][gap], origin)),
            "end_relative": list(sub(trace["anchors"][gap + 1], origin)),
            "parent_step": trace["parent_word"][gap],
            "ancestry_role_chain": canonical_role_chain(trace, gap),
            "placement_status": status,
            "actual_connector_word_if_placed": visible_word,
        })
    factor = {
        "schema": "contiguous-ordered-factor-v1",
        "orientation_quotient": "none",
        "path_reversal_quotient": "none",
        "chirality_quotient": "none",
        "translation": "pending-corridor-start-to-zero",
        "causal_scheduler_offsets": [-2, -1, 0],
        "complete_parent_block_gap_offsets": [
            [left - current_gap, right - current_gap]
            for left, right in blocks
        ],
        "interval_gap_offsets": [lower - current_gap, upper - current_gap],
        "records": records,
    }
    return factor, {
        "lower": lower,
        "upper": upper,
        "current_gap": current_gap,
        "physical_root": trace["gap_roles"][current_gap]["physical_root"],
    }


def abstract_state_action(trace, rank, d24):
    factor, bounds = ordered_factor(trace, rank)
    gap = bounds["current_gap"]
    next_gap = trace["schedule"][rank + 1]
    state_action = {
        "schema": "full-ordered-factor-state-action-v1",
        "theta": {
            "current_step": trace["parent_word"][gap],
            "next_step": trace["parent_word"][next_gap],
            "scheduler_phase": scheduler_phase(trace, rank, d24),
        },
        "ordered_factor": factor,
        "actual_selected_action": list(trace["selected_by_gap"][gap]),
    }
    return state_action, bounds


def occurrence_metadata(trace, rank, d24, catalog, motif_factor_sha256):
    state_action, bounds = abstract_state_action(trace, rank, d24)
    factor = state_action["ordered_factor"]
    gap = bounds["current_gap"]
    next_gap = trace["schedule"][rank + 1]
    current_step = trace["parent_word"][gap]
    next_step = trace["parent_word"][next_gap]
    action = state_action["actual_selected_action"]
    key = state_action
    step_window = tuple(
        trace["parent_word"][trace["schedule"][rank + offset]]
        for offset in range(5)
    ) if rank + 4 < len(trace["schedule"]) else ()
    motif = (
        step_window == ABC_MOTIF_STEPS
        and stable_hash(factor) == motif_factor_sha256
    )
    current_domain = catalog[current_step]
    successor_domain = catalog[next_step]
    prefix_points = trace["prefix_points_by_rank"][rank]
    successor_points = trace["prefix_points_by_rank"][rank + 1]
    if successor_points != prefix_points + max(0, len(action) - 1):
        raise AssertionError("prefix point-count recurrence drift")
    estimated_cost = (
        prefix_points * (
            current_domain["candidate_sites"]
            + current_domain["candidate_line_directions"]
        )
        + current_domain["word_atom_incidences"]
        + successor_points * (
            successor_domain["candidate_sites"]
            + successor_domain["candidate_line_directions"]
        )
        + successor_domain["word_atom_incidences"]
    )
    occurrence_id = stable_hash({
        "trace_id": trace["trace_id"],
        "rank": rank,
        "gap": gap,
        "key_sha256": stable_hash(key),
    })
    return {
        "occurrence_id": occurrence_id,
        "trace_id": trace["trace_id"],
        "family": trace["family"],
        "level": trace["level"],
        "scheduler_rank": rank,
        "gap": gap,
        "successor_gap": next_gap,
        "key": key,
        "key_sha256": stable_hash(key),
        "ordered_factor_sha256": stable_hash(factor),
        "actual_action": action,
        "ancestry_root": bounds["physical_root"],
        "boundary": bounds["lower"] == 0 or bounds["upper"] == (
            len(trace["parent_word"]) - 1
        ),
        "current_domain_id": current_domain["domain_id"],
        "successor_domain_id": successor_domain["domain_id"],
        "current_domain_words": current_domain["words"],
        "successor_domain_words": successor_domain["words"],
        "prefix_points": prefix_points,
        "successor_prefix_points": successor_points,
        "estimated_scan_cost": estimated_cost,
        "exact_L8_ABCDE_factor_motif": motif,
    }


def class_eligibility(occurrences):
    roots = {record["ancestry_root"] for record in occurrences}
    levels = {record["level"] for record in occurrences}
    families = {record["family"] for record in occurrences}
    current_domains = {record["current_domain_id"] for record in occurrences}
    successor_domains = {
        record["successor_domain_id"] for record in occurrences
    }
    maximum_domain = max(
        max(record["current_domain_words"], record["successor_domain_words"])
        for record in occurrences
    )
    reasons = []
    if len(occurrences) < MIN_CLASS_OCCURRENCES:
        reasons.append("fewer-than-four-occurrences")
    if len(roots) < 2:
        reasons.append("fewer-than-two-ancestry-roots")
    if len(levels) < 2 and len(families) < 2:
        reasons.append("one-level-and-one-family-only")
    if len(current_domains) != 1 or len(successor_domains) != 1:
        reasons.append("domain-identity-disagreement")
    if maximum_domain > HARD_DOMAIN_WORDS:
        reasons.append("domain-above-hard-cap")
    if any(record["boundary"] for record in occurrences):
        reasons.append("contains-boundary-stitch")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "occurrences": len(occurrences),
        "ancestry_roots": len(roots),
        "levels": sorted(levels),
        "families": sorted(families),
        "maximum_domain_words": maximum_domain,
        "preferred_domain_cap_met": maximum_domain <= SOFT_DOMAIN_WORDS,
        "required_scans": 2 * len(occurrences),
    }


def class_priority(occurrences, eligibility):
    families = set(eligibility["families"])
    gate_levels = {
        record["level"] for record in occurrences
        if record["family"] == "gate2"
    }
    return (
        0 if any(record["exact_L8_ABCDE_factor_motif"] for record in occurrences) else 1,
        0 if families == {"gate2", "primary"} else 1,
        0 if len(gate_levels) >= 3 else 1,
        sum(record["estimated_scan_cost"] for record in occurrences),
        occurrences[0]["key_sha256"],
    )


def compact_occurrence(record):
    fields = (
        "occurrence_id", "trace_id", "family", "level", "scheduler_rank",
        "gap", "successor_gap", "key_sha256", "ordered_factor_sha256",
        "actual_action", "ancestry_root", "current_domain_id",
        "successor_domain_id", "current_domain_words",
        "successor_domain_words", "prefix_points", "successor_prefix_points",
        "estimated_scan_cost", "exact_L8_ABCDE_factor_motif",
    )
    return {field: record[field] for field in fields}


def phase_a_census(args, policy):
    traces, snapshots = load_all_traces(args)
    domains, d24, catalog = build_domain_catalog()
    del domains
    motif_trace = traces["gate2-L8"]
    motif_factor, motif_bounds = ordered_factor(motif_trace, ABC_MOTIF_RANK)
    if motif_bounds["current_gap"] != motif_trace["schedule"][ABC_MOTIF_RANK]:
        raise AssertionError("frozen L8 motif identity drift")
    motif_factor_sha256 = stable_hash(motif_factor)

    first_occurrence = {}
    groups = {}
    observed = 0
    for trace_id in sorted(traces):
        trace = traces[trace_id]
        for rank in range(2, len(trace["schedule"]) - 2):
            record = occurrence_metadata(
                trace, rank, d24, catalog, motif_factor_sha256
            )
            key_hash = record["key_sha256"]
            stored = {key: value for key, value in record.items() if key != "key"}
            group = groups.get(key_hash)
            if group is None and key_hash not in first_occurrence:
                # Keep only a tiny replay locator for the overwhelmingly common
                # singleton keys.  Retaining 139k full factors would make the
                # poison-blind census needlessly memory-bound.
                first_occurrence[key_hash] = (trace_id, rank)
            elif group is None:
                first_trace_id, first_rank = first_occurrence.pop(key_hash)
                first_record = occurrence_metadata(
                    traces[first_trace_id], first_rank, d24, catalog,
                    motif_factor_sha256,
                )
                if first_record["key"] != record["key"]:
                    raise AssertionError(
                        "SHA-256 collision in canonical state keys"
                    )
                groups[key_hash] = {
                    "key": record["key"],
                    "occurrences": [
                        {key: value for key, value in first_record.items()
                         if key != "key"},
                        stored,
                    ],
                }
            else:
                if group["key"] != record["key"]:
                    raise AssertionError(
                        "SHA-256 collision in canonical state keys"
                    )
                group["occurrences"].append(stored)
            observed += 1
    expected = EXPECTED_GATE_STITCHES + EXPECTED_PRIMARY_L6_STITCHES - (
        4 * (len(GATE_LEVELS) + 1)
    )
    if observed != expected:
        raise AssertionError("nonterminal metadata occurrence extent drift", observed)

    classes = []
    for key_hash, group in groups.items():
        occurrences = sorted(
            group["occurrences"], key=lambda record: record["occurrence_id"]
        )
        eligibility = class_eligibility(occurrences)
        if not eligibility["eligible"]:
            continue
        priority = class_priority(occurrences, eligibility)
        classes.append({
            "class_id": stable_hash({
                "key_sha256": key_hash,
                "occurrence_ids": [
                    record["occurrence_id"] for record in occurrences
                ],
            }),
            "key_sha256": key_hash,
            "key": group["key"],
            "eligibility": eligibility,
            "priority": list(priority),
            "occurrences": occurrences,
        })
    classes.sort(key=lambda record: tuple(record["priority"]))

    panel_classes = []
    scans = 0
    budget_blocking_class = None
    for position, record in enumerate(classes):
        required = record["eligibility"]["required_scans"]
        if scans + required > MAX_PANEL_SCANS:
            # Priority is immutable: never skip an expensive earlier class in
            # favor of a later convenient one.  The honest outcome is a panel
            # blocked by the all-members/24-scan conjunction.
            budget_blocking_class = {
                "census_class_rank": position,
                "class_id": record["class_id"],
                "required_scans": required,
                "remaining_scan_budget": MAX_PANEL_SCANS - scans,
            }
            break
        panel_classes.append({
            "panel_order": len(panel_classes),
            "census_class_rank": position,
            "class_id": record["class_id"],
            "key_sha256": record["key_sha256"],
            "key": record["key"],
            "eligibility": record["eligibility"],
            "priority": record["priority"],
            "occurrences": [
                compact_occurrence(item) for item in record["occurrences"]
            ],
        })
        scans += required
        if scans == MAX_PANEL_SCANS:
            break

    scan_units = []
    for class_record in panel_classes:
        for occurrence in class_record["occurrences"]:
            for phase in ("source", "actual-successor"):
                scan_units.append({
                    "scan_unit_id": stable_hash({
                        "class_id": class_record["class_id"],
                        "occurrence_id": occurrence["occurrence_id"],
                        "phase": phase,
                    }),
                    "class_id": class_record["class_id"],
                    "occurrence_id": occurrence["occurrence_id"],
                    "trace_id": occurrence["trace_id"],
                    "source_scheduler_rank": occurrence["scheduler_rank"],
                    "phase": phase,
                    "domain_id": (
                        occurrence["current_domain_id"] if phase == "source"
                        else occurrence["successor_domain_id"]
                    ),
                })
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "immutable poison-blind matched-transition panel; heavy masks "
            "not yet computed"
        ),
        "phase_A_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "poison_masks_consulted_for_selection": False,
        "selection_scope": {
            "gate2_levels": list(GATE_LEVELS),
            "gate2_stitches": EXPECTED_GATE_STITCHES,
            "primary_L6_stitches": EXPECTED_PRIMARY_L6_STITCHES,
            "nonboundary_candidate_occurrences": observed,
        },
        "canonical_key_schema": {
            "key": "(theta,F,actual_action)",
            "transition_target": (
                "the exact same full (theta,F,actual_action) schema replayed "
                "at scheduler rank r+1"
            ),
            "factor": (
                "translated contiguous natural-path interval containing the "
                "pending action and two scheduler predecessors, closed to "
                "complete immediate-parent connector blocks"
            ),
            "actual_words_visible": "placed only; current and future hidden in F",
            "quotients_forbidden": [
                "rotation", "reflection", "chirality", "path reversal",
                "independent address streams after a bounded prefix",
            ],
        },
        "eligibility": {
            "minimum_occurrences": MIN_CLASS_OCCURRENCES,
            "minimum_ancestry_roots": 2,
            "minimum_levels_or_families": 2,
            "identical_current_and_successor_domain_ids": True,
            "preferred_domain_words": SOFT_DOMAIN_WORDS,
            "hard_domain_words": HARD_DOMAIN_WORDS,
            "boundary_stitches_forbidden": True,
            "all_members_scanned": True,
            "maximum_source_plus_successor_scans": MAX_PANEL_SCANS,
        },
        "priority_order": [
            "exact copies of frozen L8 A-B-C-D-E scheduler/factor motif",
            "classes spanning primary L6 and gate2",
            "classes spanning at least three gate2 levels",
            "lowest estimated exact scan cost, then canonical key",
        ],
        "vacuity_policy": (
            "evaluate classes in panel order; a class with fewer than two "
            "far-positive occurrences is vacuous and the next preordered "
            "complete class is considered"
        ),
        "panel_classes": panel_classes,
        "scan_units": scan_units,
        "scan_units_sha256": stable_hash(scan_units),
        "domain_catalog": [catalog[step] for step in range(len(MENU))],
        "domain_catalog_sha256": stable_hash(
            [catalog[step] for step in range(len(MENU))]
        ),
        "frozen_L8_ABCDE_factor_sha256": motif_factor_sha256,
        "input_snapshots": snapshots,
        "census": {
            "canonical_classes": len(groups) + len(first_occurrence),
            "eligible_classes": len(classes),
            "panel_classes": len(panel_classes),
            "panel_scans": scans,
            "budget_blocking_class": budget_blocking_class,
            "no_eligible_class": not classes,
            "empty_panel": not panel_classes,
        },
        "resource_policy": policy,
    }
    manifest["manifest_payload_sha256"] = stable_hash(manifest)
    immutable_json_dump(manifest, args.manifest)
    manifest_snapshot = {
        "path": str(Path(args.manifest).resolve()),
        "sha256": file_sha256(args.manifest),
        "bytes": Path(args.manifest).stat().st_size,
        "payload_sha256": manifest["manifest_payload_sha256"],
    }
    census = {
        "schema_version": SCHEMA_VERSION,
        "status": "Phase-A poison-blind metadata census complete",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "manifest": manifest_snapshot,
        "facts": manifest["census"],
        "poison_masks_computed": False,
        "interpretation": (
            "an empty eligible class set is evidence that this exact ordered "
            "factor projection has no nontrivial repeat in the pinned traces; "
            "a nonempty panel only authorizes the separate exact Phase-B scan"
        ),
    }
    census["payload_sha256"] = stable_hash(census)
    atomic_json_dump(census, args.census_output)
    return census


def verify_panel_manifest(path):
    if not panel_pins_finalized():
        raise RuntimeError(
            "Phase B is locked until the immutable Phase-A manifest pins "
            "are reviewed and frozen"
        )
    snapshot = stable_file_snapshot(
        path, EXPECTED_PANEL_MANIFEST_SHA256,
        EXPECTED_PANEL_MANIFEST_BYTES,
    )
    manifest, internal = unseal_json(
        path, "manifest_payload_sha256", "matched-transition panel"
    )
    if internal != EXPECTED_PANEL_MANIFEST_PAYLOAD_SHA256:
        raise AssertionError("panel manifest payload pin drift")
    if manifest.get("phase_A_checker_sha256") != (
        EXPECTED_PHASE_A_CHECKER_SHA256
    ):
        raise AssertionError("panel Phase-A checker pin drift")
    if manifest.get("poison_masks_consulted_for_selection") is not False:
        raise AssertionError("panel was not certified poison-blind")
    if len(manifest.get("scan_units", [])) > MAX_PANEL_SCANS:
        raise AssertionError("panel exceeds frozen scan budget")
    if stable_hash(manifest.get("scan_units")) != manifest.get(
        "scan_units_sha256"
    ):
        raise AssertionError("panel scan-unit stream drift")
    if stable_hash(manifest.get("domain_catalog")) != manifest.get(
        "domain_catalog_sha256"
    ):
        raise AssertionError("panel domain catalog drift")
    snapshot["payload_sha256"] = internal
    return manifest, snapshot


def build_exact_domain_model(step, domain, expected_catalog):
    words = tuple(tuple(word) for word in domain)
    if stable_hash([list(word) for word in words]) != expected_catalog[
        "domain_sha256"
    ]:
        raise AssertionError("Phase-B domain bytes differ from Phase A", step)
    site_index = {}
    line_index = {}
    site_masks = []
    line_masks = []
    word_atom_records = []
    target_endpoint = tuple(apply(M_BAL3, MENU[step]))

    def site_atom(point):
        if point not in site_index:
            site_index[point] = len(site_masks)
            site_masks.append(0)
        return site_index[point]

    def line_atom(value):
        if value not in line_index:
            line_index[value] = len(line_masks)
            line_masks.append(0)
        return line_index[value]

    for ordinal, word in enumerate(words):
        if not word or any(
            isinstance(letter, bool)
            or not isinstance(letter, int)
            or not 0 <= letter < len(MENU)
            for letter in word
        ):
            raise AssertionError("domain word has an invalid MENU letter", step, ordinal)
        if endpoint((0, 0, 0), word) != target_endpoint:
            raise AssertionError(
                "domain word has the wrong expanded endpoint", step, ordinal
            )
        interiors = tuple(word_interiors((0, 0, 0), word))
        full_path = ((0, 0, 0),) + interiors + (target_endpoint,)
        if len(set(full_path)) != len(full_path):
            raise AssertionError(
                "domain word repeats a path point", step, ordinal
            )
        # This is the intrinsic three-new case omitted from the prefix scans.
        # Check it independently here rather than trusting the domain producer.
        for right_index, right in enumerate(interiors):
            seen_directions = set()
            for left in interiors[:right_index]:
                direction = primitive(sub(left, right))
                if direction in seen_directions:
                    raise AssertionError(
                        "domain word has three collinear interior points",
                        step, ordinal, direction,
                    )
                seen_directions.add(direction)
        local_sites = {site_atom(point) for point in interiors}
        local_lines = set()
        for left_index, left in enumerate(interiors):
            for right in interiors[left_index + 1:]:
                local_lines.add(line_atom(line_key(left, right)))
        bit = 1 << ordinal
        for atom in local_sites:
            site_masks[atom] |= bit
        for atom in local_lines:
            line_masks[atom] |= bit
        word_atom_records.append({
            "site_atoms": sorted(local_sites),
            "line_atoms": sorted(local_lines),
        })
    sites = [None] * len(site_index)
    for value, index in site_index.items():
        sites[index] = value
    lines = [None] * len(line_index)
    for value, index in line_index.items():
        lines[index] = value
    directions = defaultdict(dict)
    for atom, (direction, moment) in enumerate(lines):
        if moment in directions[direction]:
            raise AssertionError("candidate line atom repeated")
        directions[direction][moment] = atom
    observed = {
        "words": len(words),
        "domain_sha256": stable_hash([list(word) for word in words]),
        "candidate_sites": len(sites),
        "candidate_lines": len(lines),
        "candidate_line_directions": len(directions),
        "word_atom_incidences": sum(
            len(record["site_atoms"]) + len(record["line_atoms"])
            for record in word_atom_records
        ),
    }
    for field, value in observed.items():
        if expected_catalog.get(field) != value:
            raise AssertionError("domain-model census drift", step, field)
    atom_universe = {
        "sites": [list(point) for point in sites],
        "lines": [
            {"direction": list(direction), "moment": list(moment)}
            for direction, moment in lines
        ],
    }
    return {
        "step": step,
        "domain_id": expected_catalog["domain_id"],
        "words": words,
        "word_count": len(words),
        "width": (len(words) + 7) // 8,
        "sites": tuple(sites),
        "site_index": dict(site_index),
        "site_masks": tuple(site_masks),
        "lines": tuple(lines),
        "line_index": dict(line_index),
        "line_masks": tuple(line_masks),
        "lines_by_direction": {
            direction: dict(by_moment)
            for direction, by_moment in directions.items()
        },
        "atom_universe_sha256": stable_hash(atom_universe),
        "word_incidence_sha256": stable_hash(word_atom_records),
        "domain_sha256": observed["domain_sha256"],
        "target_endpoint": target_endpoint,
        "intrinsic_domain_certificate": {
            "words_checked": len(words),
            "every_word_ends_at_expanded_step": True,
            "every_word_path_has_distinct_points": True,
            "no_three_candidate_interiors_collinear": True,
        },
    }


def raw_mask_record(mask, model):
    if mask < 0 or mask.bit_length() > model["word_count"]:
        raise AssertionError("mask exceeds its declared domain")
    raw = mask.to_bytes(model["width"], "little")
    return {
        "domain_id": model["domain_id"],
        "step": model["step"],
        "words": model["word_count"],
        "width_bytes": model["width"],
        "bit_order": "word i is bit (i mod 8) of byte floor(i/8)",
        "little_endian_hex": raw.hex(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "population": mask.bit_count(),
    }


def decode_raw_mask(record):
    if record["width_bytes"] != (record["words"] + 7) // 8:
        raise AssertionError("raw mask width is not ceil(words/8)")
    if record.get("bit_order") != (
        "word i is bit (i mod 8) of byte floor(i/8)"
    ):
        raise AssertionError("raw mask bit-order declaration drift")
    raw = bytes.fromhex(record["little_endian_hex"])
    if raw.hex() != record["little_endian_hex"]:
        raise AssertionError("raw mask hex is not canonical lowercase encoding")
    if len(raw) != record["width_bytes"]:
        raise AssertionError("raw mask width drift")
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise AssertionError("raw mask commitment drift")
    mask = int.from_bytes(raw, "little")
    if mask.bit_count() != record["population"]:
        raise AssertionError("raw mask population drift")
    if mask.bit_length() > record["words"]:
        raise AssertionError("raw mask has a padding bit set")
    return mask


def comparable_masks(left, right):
    if (
        left["domain_id"] != right["domain_id"]
        or left["words"] != right["words"]
        or left["width_bytes"] != right["width_bytes"]
    ):
        raise AssertionError(
            "different connector domains must never be compared bitwise"
        )
    return decode_raw_mask(left), decode_raw_mask(right)


def mask_symmetric_difference(left, right):
    left_mask, right_mask = comparable_masks(left, right)
    return left_mask ^ right_mask


def activation_record(origin, kind, rank, gap=None, slot=None):
    record = copy.deepcopy(origin)
    record.update({
        "activation_kind": kind,
        "activation_rank": rank,
        "activation_gap": gap,
        "activation_interior_slot": slot,
    })
    return record


def reconstruct_prefix(trace, rank):
    points = list(trace["anchors"])
    provenance = [
        activation_record(origin, "inherited-anchor", "inherited")
        for origin in trace["anchor_origins"]
    ]
    action_trace = []
    for cursor, gap in enumerate(trace["schedule"][:rank]):
        word = trace["selected_by_gap"][gap]
        interiors = tuple(word_interiors(trace["anchors"][gap], word))
        endpoint_ids = [
            trace["anchor_origins"][gap]["stable_id"],
            trace["anchor_origins"][gap + 1]["stable_id"],
        ]
        for slot, point in enumerate(interiors):
            points.append(point)
            provenance.append({
                "stable_id": (
                    f"{trace['trace_id']}:R{cursor}:G{gap}:I{slot}"
                ),
                "origin_birth_level": trace["level"],
                "origin_birth_owner": gap,
                "origin_birth_rank": cursor,
                "origin_interior_slot": slot,
                "birth_parent_endpoint_stable_ids": endpoint_ids,
                "generation_lineage": [{
                    "level": trace["level"],
                    "kind": "connector-interior",
                    "owner_gap": gap,
                    "owner_construction_rank": cursor,
                    "interior_slot": slot,
                }],
                "activation_kind": "current-level-connector-interior",
                "activation_rank": cursor,
                "activation_gap": gap,
                "activation_interior_slot": slot,
            })
        action_trace.append({
            "rank": cursor,
            "gap": gap,
            "step": trace["parent_word"][gap],
            "selected_word": list(word),
            "interior_points": len(interiors),
        })
    if len(points) != len(provenance) or len(points) != len(set(points)):
        raise AssertionError("reconstructed prefix repeats or loses provenance")
    return {
        "points": tuple(points),
        "provenance": tuple(provenance),
        "point_index": {point: index for index, point in enumerate(points)},
        "action_trace": tuple(action_trace),
        "commitments": {
            "point_stream_sha256": point_stream_sha256(points),
            "point_set_sha256": stable_hash(sorted(points)),
            "provenance_stream_sha256": stable_hash(provenance),
            "action_trace_sha256": stable_hash(action_trace),
            "points": len(points),
        },
    }


def provenance_role(record):
    return {
        "origin_birth_level": record["origin_birth_level"],
        "origin_birth_owner_kind": (
            "none" if record.get("origin_birth_owner") is None else "connector"
        ),
        "origin_interior_slot": record.get("origin_interior_slot"),
        "activation_kind": record["activation_kind"],
        "activation_rank_class": (
            "inherited" if record["activation_rank"] == "inherited"
            else "current-level"
        ),
        "lineage_roles": [
            {
                key: value for key, value in item.items()
                if key not in {
                    "path_index", "parent_path_index", "owner_gap",
                    "owner_construction_rank",
                }
            }
            for item in record["generation_lineage"]
        ],
    }


def compact_endpoint(point, provenance):
    return {
        "stable_id": provenance["stable_id"],
        "point": list(point),
        "origin_birth_level": provenance["origin_birth_level"],
        "activation_rank": provenance["activation_rank"],
        "role": provenance_role(provenance),
    }


def corridor_distance(point, support):
    return min(chebyshev(point, candidate) for candidate in support)


def chronological_shell(endpoints, level, rank):
    active = [
        endpoint["activation_rank"] for endpoint in endpoints
        if endpoint["activation_rank"] != "inherited"
    ]
    if not active:
        return "inherited"
    delta = rank - max(active)
    if delta < 1:
        raise AssertionError("witness endpoint is not older than pending action")
    shell = 1
    while not (3 ** (shell - 1) <= delta < 3 ** shell):
        shell += 1
    return shell


def spatial_shell(endpoints):
    distance = max(endpoint["corridor_distance"] for endpoint in endpoints)
    if distance <= LOCAL_RADIUS:
        return 0
    shell = 1
    while distance > LOCAL_RADIUS * (3 ** shell):
        shell += 1
    if not LOCAL_RADIUS * (3 ** (shell - 1)) < distance <= (
        LOCAL_RADIUS * (3 ** shell)
    ):
        raise AssertionError("spatial shell boundary drift")
    return shell


def witness_descriptor(channel, endpoints, level, rank):
    ages = sorted(level - endpoint["origin_birth_level"] for endpoint in endpoints)
    chronological = chronological_shell(endpoints, level, rank)
    spatial = spatial_shell(endpoints)
    return {
        "channel": channel,
        "endpoint_age_tuple": ages,
        "obstruction_birth_level": max(
            endpoint["origin_birth_level"] for endpoint in endpoints
        ),
        "current_level_birth_rank": (
            "inherited" if chronological == "inherited"
            else max(
                endpoint["activation_rank"] for endpoint in endpoints
                if endpoint["activation_rank"] != "inherited"
            )
        ),
        "chronological_shell": chronological,
        "spatial_shell": spatial,
        "region": "near" if spatial == 0 else "far",
    }


def normalized_source_token(
    channel, atom_kind, atom_value, witness, source_frame_start,
    source_rank, current_level,
):
    endpoints = witness["old_endpoints"]
    if any(
        endpoint["activation_rank"] != "inherited"
        and endpoint["activation_rank"] > source_rank
        for endpoint in endpoints
    ):
        raise AssertionError("successor witness is not source/action observable")
    roles = [
        normalized_endpoint_role(endpoint, current_level, source_rank)
        for endpoint in endpoints
    ]
    roles.sort(key=canonical_bytes)
    token = {
        "schema": "normalized-source-observable-token-v1",
        "channel": channel,
        "atom_kind": atom_kind,
        "endpoint_birth_roles": roles,
        "uses_selected_action_birth": any(
            endpoint["activation_rank"] == source_rank
            for endpoint in endpoints
        ),
        "stable_endpoint_identity_retained": False,
    }
    if witness.get("direction") is not None:
        direction = tuple(witness["direction"])
        point = tuple(endpoints[0]["point"])
        token.update({
            "primitive_direction": list(direction),
            "moment_in_source_corridor_frame": list(
                cross(sub(point, source_frame_start), direction)
            ),
            "exact_successor_residual": witness["exact_residual"],
        })
    else:
        point = tuple(endpoints[0]["point"])
        token["collision_offset_in_source_corridor_frame"] = list(
            sub(point, source_frame_start)
        )
    if atom_kind == "site":
        token["successor_atom_offset"] = list(atom_value)
    else:
        direction, moment = atom_value
        token["successor_atom_direction"] = list(direction)
        token["successor_atom_moment"] = list(moment)
    token["token_sha256"] = stable_hash(token)
    return token


def normalized_endpoint_role(endpoint, current_level, source_rank):
    """Identity-free endpoint role used by latent-token refinements."""
    evidence_role = endpoint["role"]
    normalized_lineage = []
    for item in evidence_role["lineage_roles"]:
        normalized = dict(item)
        lineage_level = normalized.pop("level", None)
        if lineage_level is not None:
            normalized["level_age"] = current_level - lineage_level
        normalized_lineage.append(normalized)
    activation_rank = endpoint["activation_rank"]
    if activation_rank == "inherited":
        activation_age = "inherited"
    else:
        activation_age = source_rank - activation_rank
        if activation_age < 0:
            raise AssertionError("endpoint role is not source/action observable")
    return {
        "origin_age": current_level - endpoint["origin_birth_level"],
        "origin_birth_owner_kind": evidence_role["origin_birth_owner_kind"],
        "origin_interior_slot": evidence_role["origin_interior_slot"],
        "activation_kind": evidence_role["activation_kind"],
        "activation_rank_class": evidence_role["activation_rank_class"],
        "activation_age_at_source_action": activation_age,
        "lineage_roles": normalized_lineage,
    }


def empty_accumulator():
    return {
        "channel_masks": {channel: 0 for channel in CHANNELS},
        "near_masks": {channel: 0 for channel in CHANNELS},
        "far_masks": {},
        "effects": {},
        "witness_hash_chain": "00" * 32,
        "witnesses": 0,
    }


def accumulator_to_json(accumulator):
    return {
        "channel_masks": {
            key: hex(value) for key, value in accumulator["channel_masks"].items()
        },
        "near_masks": {
            key: hex(value) for key, value in accumulator["near_masks"].items()
        },
        "far_masks": {
            key: hex(value) for key, value in accumulator["far_masks"].items()
        },
        "effects": {
            key: {**value, "mask": hex(value["mask"])}
            for key, value in accumulator["effects"].items()
        },
        "witness_hash_chain": accumulator["witness_hash_chain"],
        "witnesses": accumulator["witnesses"],
    }


def accumulator_from_json(record):
    if record is None:
        return empty_accumulator()
    return {
        "channel_masks": {
            key: int(value, 16) for key, value in record["channel_masks"].items()
        },
        "near_masks": {
            key: int(value, 16) for key, value in record["near_masks"].items()
        },
        "far_masks": {
            key: int(value, 16) for key, value in record["far_masks"].items()
        },
        "effects": {
            key: {**value, "mask": int(value["mask"], 16)}
            for key, value in record["effects"].items()
        },
        "witness_hash_chain": record["witness_hash_chain"],
        "witnesses": record["witnesses"],
    }


def update_hash_chain(previous, witness):
    digest = hashlib.sha256()
    digest.update(bytes.fromhex(previous))
    digest.update(canonical_bytes(witness))
    return digest.hexdigest()


def record_witness_effect(
    accumulator, model, channel, atom_kind, atom_index, atom_value,
    endpoints, level, rank, witness, phase, source_frame_start, source_rank,
):
    descriptor = witness_descriptor(channel, endpoints, level, rank)
    atom_mask = (
        model["site_masks"][atom_index] if atom_kind == "site"
        else model["line_masks"][atom_index]
    )
    accumulator["channel_masks"][channel] |= atom_mask
    if descriptor["region"] == "near":
        accumulator["near_masks"][channel] |= atom_mask
        region_key = {
            "region": "near",
            "channel": channel,
        }
    else:
        region_key = {
            "region": "far",
            "channel": channel,
            "endpoint_age_tuple": descriptor["endpoint_age_tuple"],
            "chronological_shell": descriptor["chronological_shell"],
            "spatial_shell": descriptor["spatial_shell"],
        }
        serialized = json.dumps(region_key, sort_keys=True, separators=(",", ":"))
        accumulator["far_masks"][serialized] = (
            accumulator["far_masks"].get(serialized, 0) | atom_mask
        )
    atom_key = {
        "kind": atom_kind,
        "value": (
            list(atom_value) if atom_kind == "site" else {
                "direction": list(atom_value[0]),
                "moment": list(atom_value[1]),
            }
        ),
    }
    effect_id = stable_hash({"region": region_key, "atom": atom_key})
    complete_witness = {
        **witness,
        "descriptor": descriptor,
        "atom": atom_key,
    }
    if phase == "actual-successor":
        complete_witness["source_observable_token"] = normalized_source_token(
            channel, atom_kind, atom_value, complete_witness,
            source_frame_start, source_rank, level,
        )
    accumulator["witness_hash_chain"] = update_hash_chain(
        accumulator["witness_hash_chain"], complete_witness
    )
    accumulator["witnesses"] += 1
    candidate = {
        "effect_id": effect_id,
        "region": region_key,
        "atom": atom_key,
        "mask": atom_mask,
        "least_word_ordinal_zero_based": (
            (atom_mask & -atom_mask).bit_length() - 1
        ),
        "canonical_witness": complete_witness,
    }
    old = accumulator["effects"].get(effect_id)
    if old is None or canonical_bytes(candidate["canonical_witness"]) < (
        canonical_bytes(old["canonical_witness"])
    ):
        accumulator["effects"][effect_id] = candidate


def point_scan_metadata(prefix, support):
    result = []
    for point, provenance in zip(prefix["points"], prefix["provenance"]):
        endpoint_record = compact_endpoint(point, provenance)
        endpoint_record["corridor_distance"] = corridor_distance(point, support)
        result.append(endpoint_record)
    return tuple(result)


def prepare_scan_context(unit, occurrence, trace, domains, catalog_by_id):
    source_rank = occurrence["scheduler_rank"]
    if unit["phase"] == "source":
        rank = source_rank
    else:
        rank = source_rank + 1
    gap = trace["schedule"][rank]
    step = trace["parent_word"][gap]
    expected = catalog_by_id[unit["domain_id"]]
    if expected["step"] != step:
        raise AssertionError("scan unit/domain step mismatch")
    model = build_exact_domain_model(step, domains[step], expected)
    prefix = reconstruct_prefix(trace, rank)
    start = trace["anchors"][gap]
    end = trace["anchors"][gap + 1]
    if sub(end, start) != model["target_endpoint"]:
        raise AssertionError("connector domain endpoint/corridor displacement drift")
    support_offsets = set(model["sites"])
    support_offsets.update({(0, 0, 0), sub(end, start)})
    support = tuple(sorted(add(start, offset) for offset in support_offsets))
    point_metadata = point_scan_metadata(prefix, support)
    return {
        "rank": rank,
        "source_rank": source_rank,
        "gap": gap,
        "step": step,
        "start": start,
        "end": end,
        "source_frame_start": trace["anchors"][occurrence["gap"]],
        "actual_selected_word": tuple(trace["selected_by_gap"][gap]),
        "model": model,
        "prefix": prefix,
        "point_metadata": point_metadata,
        "support": support,
    }


def old_old_site_scan(context, site_index, accumulator, phase):
    model = context["model"]
    offset = model["sites"][site_index]
    candidate = add(context["start"], offset)
    collision_index = context["prefix"]["point_index"].get(candidate)
    if collision_index is not None:
        endpoint_record = context["point_metadata"][collision_index]
        witness = {
            "old_endpoints": [endpoint_record],
            "direction": None,
            "moment": None,
            "exact_residual": [0, 0, 0],
        }
        record_witness_effect(
            accumulator, model, "collision", "site", site_index, offset,
            [endpoint_record], context["trace_level"], context["rank"],
            witness, phase, context["source_frame_start"],
            context["source_rank"],
        )

    seen = {}
    for index, point in enumerate(context["prefix"]["points"]):
        direction = primitive(sub(point, candidate))
        if direction is None:
            continue
        previous = seen.get(direction)
        if previous is None:
            seen[direction] = index
            continue
        if isinstance(previous, tuple):
            raise AssertionError(
                "prefix contains a triple through candidate site",
                site_index, direction,
            )
        endpoints = [
            context["point_metadata"][previous],
            context["point_metadata"][index],
        ]
        line_moment = cross(
            context["prefix"]["points"][previous], direction
        )
        witness = {
            "old_endpoints": endpoints,
            "direction": list(direction),
            "moment": list(line_moment),
            "exact_residual": list(cross(
                sub(candidate, context["prefix"]["points"][previous]),
                direction,
            )),
        }
        if witness["exact_residual"] != [0, 0, 0]:
            raise AssertionError("direction bucket produced a nonincident site")
        record_witness_effect(
            accumulator, model, "old-old-new", "site", site_index, offset,
            endpoints, context["trace_level"], context["rank"], witness,
            phase, context["source_frame_start"], context["source_rank"],
        )
        seen[direction] = (previous, index)


def old_new_line_scan(context, point_index, accumulator, phase):
    model = context["model"]
    point = context["prefix"]["points"][point_index]
    endpoint_record = context["point_metadata"][point_index]
    relative = sub(point, context["start"])
    for direction, by_moment in model["lines_by_direction"].items():
        moment = cross(relative, direction)
        atom = by_moment.get(moment)
        if atom is None:
            continue
        atom_value = model["lines"][atom]
        witness = {
            "old_endpoints": [endpoint_record],
            "direction": list(direction),
            "moment": list(cross(point, direction)),
            "exact_residual": [0, 0, 0],
        }
        record_witness_effect(
            accumulator, model, "old-new-new", "line", atom, atom_value,
            [endpoint_record], context["trace_level"], context["rank"],
            witness, phase, context["source_frame_start"],
            context["source_rank"],
        )


def union_masks(records):
    result = 0
    for record in records:
        result |= record
    return result


def finalize_scan_record(unit, occurrence, trace, context, accumulator):
    model = context["model"]
    full = union_masks(accumulator["channel_masks"].values())
    decomposition = union_masks(accumulator["near_masks"].values()) | (
        union_masks(accumulator["far_masks"].values())
    )
    if full != decomposition:
        raise AssertionError("near/far overlapping masks do not OR to exact K")
    channel_records = {
        channel: raw_mask_record(accumulator["channel_masks"][channel], model)
        for channel in CHANNELS
    }
    near_records = {
        channel: raw_mask_record(accumulator["near_masks"][channel], model)
        for channel in CHANNELS
    }
    far_records = []
    for descriptor, mask in sorted(accumulator["far_masks"].items()):
        far_records.append({
            "descriptor": json.loads(descriptor),
            "mask": raw_mask_record(mask, model),
        })
    effects = []
    for effect_id, effect in sorted(accumulator["effects"].items()):
        effects.append({
            **effect,
            "mask": raw_mask_record(effect["mask"], model),
        })
    selected_word = tuple(trace["selected_by_gap"][context["gap"]])
    try:
        selected_ordinal = model["words"].index(selected_word)
    except ValueError as error:
        raise AssertionError("actual action absent from complete domain") from error
    selected_killed = bool(full & (1 << selected_ordinal))
    if selected_killed:
        raise AssertionError("recorded construction action is geometrically killed")
    return {
        "schema_version": SCHEMA_VERSION,
        "scan_unit": unit,
        "occurrence_id": occurrence["occurrence_id"],
        "class_id": unit["class_id"],
        "trace_id": trace["trace_id"],
        "family": trace["family"],
        "level": trace["level"],
        "phase": unit["phase"],
        "scheduler_rank": context["rank"],
        "gap": context["gap"],
        "step": context["step"],
        "start": list(context["start"]),
        "end": list(context["end"]),
        "domain": {
            "domain_id": model["domain_id"],
            "step": model["step"],
            "domain_sha256": model["domain_sha256"],
            "words": model["word_count"],
            "width_bytes": model["width"],
            "atom_universe_sha256": model["atom_universe_sha256"],
            "word_incidence_sha256": model["word_incidence_sha256"],
            "target_endpoint": list(model["target_endpoint"]),
            "intrinsic_domain_certificate": model[
                "intrinsic_domain_certificate"
            ],
        },
        "prefix": context["prefix"]["commitments"],
        "corridor_support": {
            "points": len(context["support"]),
            "sha256": stable_hash(context["support"]),
            "near_radius": LOCAL_RADIUS,
        },
        "exact_killed_word_mask": raw_mask_record(full, model),
        "channel_masks": channel_records,
        "overlapping_near_masks": near_records,
        "overlapping_far_masks": far_records,
        "overlap_identity_verified": True,
        "endpoint_cutoff": None,
        "distance_cutoff": None,
        "birth_age_cutoff": None,
        "witnesses": accumulator["witnesses"],
        "witness_hash_chain": accumulator["witness_hash_chain"],
        "effect_records": effects,
        "actual_selected_word": list(selected_word),
        "actual_selected_ordinal_zero_based": selected_ordinal,
        "actual_selected_word_geometrically_legal": not selected_killed,
    }


def initial_scan_checkpoint(
    manifest_snapshot, shard_index, shard_count, assigned_unit_count,
):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "complete" if assigned_unit_count == 0 else "partial",
        "phase_B_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "manifest": manifest_snapshot,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "next_assigned_unit": 0,
        "active": None,
        "completed_records": [],
        "last_run": None,
    }


def seal_checkpoint(checkpoint):
    result = copy.deepcopy(checkpoint)
    result.pop("checkpoint_payload_sha256", None)
    result["checkpoint_payload_sha256"] = stable_hash(result)
    return result


def validate_checkpoint_structure(checkpoint, units):
    status = checkpoint.get("status")
    if status not in {"partial", "complete"}:
        raise AssertionError("scan checkpoint has an invalid status")
    next_unit = checkpoint.get("next_assigned_unit")
    if (
        isinstance(next_unit, bool)
        or not isinstance(next_unit, int)
        or not 0 <= next_unit <= len(units)
    ):
        raise AssertionError("scan checkpoint cursor is outside its shard")
    completed = checkpoint.get("completed_records")
    if not isinstance(completed, list) or len(completed) != next_unit:
        raise AssertionError("scan checkpoint completed-record extent drift")
    for index, record in enumerate(completed):
        if record.get("scan_unit") != units[index]:
            raise AssertionError(
                "scan checkpoint completed-record order drift", index
            )
    active = checkpoint.get("active")
    exactly_complete = next_unit == len(units) and active is None
    if (status == "complete") != exactly_complete:
        raise AssertionError("scan checkpoint status/completeness disagreement")
    if active is not None:
        if next_unit >= len(units):
            raise AssertionError("complete shard retains an active scan")
        if active.get("scan_unit_id") != units[next_unit]["scan_unit_id"]:
            raise AssertionError("active scan is not the next assigned unit")


def load_scan_checkpoint(
    path, manifest_snapshot, shard_index, shard_count, units,
):
    path = Path(path)
    if not path.exists():
        return initial_scan_checkpoint(
            manifest_snapshot, shard_index, shard_count, len(units)
        )
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(checkpoint):
        raise AssertionError("scan checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    expected = {
        "schema_version": SCHEMA_VERSION,
        "phase_B_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "manifest": manifest_snapshot,
        "shard_index": shard_index,
        "shard_count": shard_count,
    }
    if any(checkpoint.get(key) != value for key, value in expected.items()):
        raise AssertionError("scan checkpoint static identity drift")
    validate_checkpoint_structure(checkpoint, units)
    return checkpoint


def save_scan_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def assigned_units(manifest, shard_index, shard_count):
    return tuple(
        unit for index, unit in enumerate(manifest["scan_units"])
        if index % shard_count == shard_index
    )


def manifest_occurrences(manifest):
    result = {}
    for class_record in manifest["panel_classes"]:
        for occurrence in class_record["occurrences"]:
            if occurrence["occurrence_id"] in result:
                raise AssertionError("manifest occurrence repeats")
            result[occurrence["occurrence_id"]] = occurrence
    return result


def scan_chunk(args, policy, lease_slot):
    started = time.monotonic()
    deadline = started + args.max_seconds
    manifest, manifest_snapshot = verify_panel_manifest(args.manifest)
    traces, input_snapshots = load_all_traces(args)
    domains, _d24, catalog = build_domain_catalog()
    catalog_by_id = {record["domain_id"]: record for record in catalog.values()}
    if len(catalog_by_id) != len(catalog):
        raise AssertionError("domain identity collision")
    if [catalog[step] for step in range(len(MENU))] != manifest[
        "domain_catalog"
    ]:
        raise AssertionError("current domain catalog differs from manifest")
    occurrences = manifest_occurrences(manifest)
    units = assigned_units(manifest, args.shard_index, args.shard_count)
    checkpoint = load_scan_checkpoint(
        args.checkpoint, manifest_snapshot, args.shard_index, args.shard_count,
        units,
    )
    models_by_domain = {}
    for unit in units:
        if unit["domain_id"] not in models_by_domain:
            expected = catalog_by_id[unit["domain_id"]]
            models_by_domain[unit["domain_id"]] = build_exact_domain_model(
                expected["step"], domains[expected["step"]], expected
            )
    for index, record in enumerate(checkpoint["completed_records"]):
        validate_scan_record(
            record, units[index], models_by_domain[units[index]["domain_id"]]
        )
    work = 0
    stop_reason = "work-limit"
    while checkpoint["next_assigned_unit"] < len(units):
        if work >= args.max_work_items or time.monotonic() >= deadline:
            stop_reason = (
                "time-limit" if time.monotonic() >= deadline else "work-limit"
            )
            break
        unit = units[checkpoint["next_assigned_unit"]]
        occurrence = occurrences[unit["occurrence_id"]]
        trace = traces[unit["trace_id"]]
        context = prepare_scan_context(
            unit, occurrence, trace, domains, catalog_by_id
        )
        context["trace_level"] = trace["level"]
        active = checkpoint["active"]
        if active is None:
            active = {
                "scan_unit_id": unit["scan_unit_id"],
                "stage": "site-atoms",
                "cursor": 0,
                "site_stage_complete": False,
                "accumulator": accumulator_to_json(empty_accumulator()),
            }
        accumulator = validate_active_scan_state(active, unit, context)
        if active["stage"] == "site-atoms":
            while active["cursor"] < len(context["model"]["sites"]):
                if work >= args.max_work_items or time.monotonic() >= deadline:
                    break
                old_old_site_scan(
                    context, active["cursor"], accumulator, unit["phase"]
                )
                active["cursor"] += 1
                work += 1
            if active["cursor"] == len(context["model"]["sites"]):
                active["stage"] = "old-points-for-new-lines"
                active["cursor"] = 0
                active["site_stage_complete"] = True
        if active["stage"] == "old-points-for-new-lines":
            while active["cursor"] < len(context["prefix"]["points"]):
                if work >= args.max_work_items or time.monotonic() >= deadline:
                    break
                old_new_line_scan(
                    context, active["cursor"], accumulator, unit["phase"]
                )
                active["cursor"] += 1
                work += 1
            if active["cursor"] == len(context["prefix"]["points"]):
                record = finalize_scan_record(
                    unit, occurrence, trace, context, accumulator
                )
                checkpoint["completed_records"].append(record)
                checkpoint["next_assigned_unit"] += 1
                checkpoint["active"] = None
                if checkpoint["next_assigned_unit"] == len(units):
                    checkpoint["status"] = "complete"
                save_scan_checkpoint(args.checkpoint, checkpoint)
                continue
        active["accumulator"] = accumulator_to_json(accumulator)
        checkpoint["active"] = active
        break
    if checkpoint["next_assigned_unit"] == len(units):
        checkpoint["status"] = "complete"
        stop_reason = "shard-complete"
    checkpoint["last_run"] = {
        "work_items": work,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "maximum_resident_bytes": maximum_resident_bytes(),
        "resource_policy": policy,
        "cooperative_lease_slot": lease_slot,
        "input_snapshots": input_snapshots,
    }
    save_scan_checkpoint(args.checkpoint, checkpoint)
    if checkpoint["status"] == "complete":
        raw = {
            "schema_version": SCHEMA_VERSION,
            "status": "complete exact matched-transition mask shard",
            "phase_B_checker_sha256": PROCESS_START_CHECKER_SHA256,
            "manifest": manifest_snapshot,
            "shard_index": args.shard_index,
            "shard_count": args.shard_count,
            "records": checkpoint["completed_records"],
            "record_stream_sha256": stable_hash(
                checkpoint["completed_records"]
            ),
            "resource_policy": policy,
        }
        raw["payload_sha256"] = stable_hash(raw)
        atomic_json_dump(raw, args.raw_output)
    return {
        "status": checkpoint["status"],
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_sha256": file_sha256(args.checkpoint),
        "assigned_units": len(units),
        "completed_units": checkpoint["next_assigned_unit"],
        "work_items_this_chunk": work,
        "stop_reason": stop_reason,
    }


def verify_raw_shard(path, manifest_snapshot):
    path = Path(path).resolve()
    before = path.stat()
    encoded = path.read_bytes()
    digest = hashlib.sha256(encoded).hexdigest()
    after = path.stat()
    identity_fields = (
        "st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns",
    )
    if tuple(getattr(before, key) for key in identity_fields) != tuple(
        getattr(after, key) for key in identity_fields
    ):
        raise RuntimeError("raw shard changed while being read", str(path))
    raw = json.loads(encoded)
    internal = raw.pop("payload_sha256", None)
    if internal != stable_hash(raw):
        raise AssertionError("Phase-B raw shard internal payload drift")
    raw["payload_sha256"] = internal
    if raw.get("status") != "complete exact matched-transition mask shard":
        raise AssertionError("raw shard is not complete", str(path))
    if raw.get("manifest") != manifest_snapshot:
        raise AssertionError("raw shard/manifest disagreement", str(path))
    if raw.get("phase_B_checker_sha256") != PROCESS_START_CHECKER_SHA256:
        raise AssertionError(
            "raw shard was produced by a different unreviewed Phase-B checker"
        )
    if stable_hash(raw.get("records")) != raw.get("record_stream_sha256"):
        raise AssertionError("raw shard record stream drift")
    snapshot = {
        "path": str(path),
        "sha256": digest,
        "bytes": after.st_size,
        "payload_sha256": internal,
    }
    return raw, snapshot


def validate_mask_record(record, model):
    expected = {
        "domain_id": model["domain_id"],
        "step": model["step"],
        "words": model["word_count"],
        "width_bytes": model["width"],
        "bit_order": "word i is bit (i mod 8) of byte floor(i/8)",
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise AssertionError("raw mask is not bound to its exact domain model")
    decode_raw_mask(record)
    return record


def expected_domain_record(model):
    return {
        "domain_id": model["domain_id"],
        "step": model["step"],
        "domain_sha256": model["domain_sha256"],
        "words": model["word_count"],
        "width_bytes": model["width"],
        "atom_universe_sha256": model["atom_universe_sha256"],
        "word_incidence_sha256": model["word_incidence_sha256"],
        "target_endpoint": list(model["target_endpoint"]),
        "intrinsic_domain_certificate": model[
            "intrinsic_domain_certificate"
        ],
    }


def projected_effect_region(descriptor):
    required = {
        "channel", "endpoint_age_tuple", "obstruction_birth_level",
        "current_level_birth_rank", "chronological_shell", "spatial_shell",
        "region",
    }
    if set(descriptor) != required or descriptor["channel"] not in CHANNELS:
        raise AssertionError("witness descriptor schema drift")
    if descriptor["region"] == "near":
        if descriptor["spatial_shell"] != 0:
            raise AssertionError("near descriptor has a nonzero spatial shell")
        return {"region": "near", "channel": descriptor["channel"]}
    if descriptor["region"] != "far" or not (
        isinstance(descriptor["spatial_shell"], int)
        and not isinstance(descriptor["spatial_shell"], bool)
        and descriptor["spatial_shell"] >= 1
    ):
        raise AssertionError("far descriptor has an invalid spatial shell")
    return {
        "region": "far",
        "channel": descriptor["channel"],
        "endpoint_age_tuple": descriptor["endpoint_age_tuple"],
        "chronological_shell": descriptor["chronological_shell"],
        "spatial_shell": descriptor["spatial_shell"],
    }


def validate_effect_region(region):
    if region.get("region") == "near":
        if set(region) != {"region", "channel"}:
            raise AssertionError("near effect region schema drift")
    elif region.get("region") == "far":
        required = {
            "region", "channel", "endpoint_age_tuple",
            "chronological_shell", "spatial_shell",
        }
        if set(region) != required:
            raise AssertionError("far effect region schema drift")
        ages = region["endpoint_age_tuple"]
        if (
            not isinstance(ages, list)
            or ages != sorted(ages)
            or any(
                isinstance(age, bool) or not isinstance(age, int) or age < 0
                for age in ages
            )
        ):
            raise AssertionError("far effect birth-age tuple drift")
        chronological = region["chronological_shell"]
        if chronological != "inherited" and not (
            isinstance(chronological, int)
            and not isinstance(chronological, bool)
            and chronological >= 1
        ):
            raise AssertionError("far effect chronological shell drift")
        spatial = region["spatial_shell"]
        if (
            isinstance(spatial, bool)
            or not isinstance(spatial, int)
            or spatial < 1
        ):
            raise AssertionError("far effect spatial shell drift")
    else:
        raise AssertionError("effect region is neither near nor far")
    if region.get("channel") not in CHANNELS:
        raise AssertionError("effect region has an unknown channel")


def model_atom_mask(atom, model):
    if set(atom) != {"kind", "value"}:
        raise AssertionError("effect atom schema drift")
    if atom["kind"] == "site":
        if not isinstance(atom["value"], list) or len(atom["value"]) != 3:
            raise AssertionError("site atom coordinate schema drift")
        value = tuple(atom["value"])
        if value not in model["site_index"]:
            raise AssertionError("effect names a site outside its domain model")
        return model["site_masks"][model["site_index"][value]]
    if atom["kind"] != "line" or set(atom["value"]) != {
        "direction", "moment",
    }:
        raise AssertionError("line atom schema drift")
    direction = tuple(atom["value"]["direction"])
    moment = tuple(atom["value"]["moment"])
    if len(direction) != 3 or len(moment) != 3:
        raise AssertionError("line atom coordinate schema drift")
    value = (direction, moment)
    if value not in model["line_index"]:
        raise AssertionError("effect names a line outside its domain model")
    return model["line_masks"][model["line_index"][value]]


def validate_effect_record(effect, model, mask):
    validate_effect_region(effect["region"])
    if effect["effect_id"] != stable_hash({
        "region": effect["region"], "atom": effect["atom"],
    }):
        raise AssertionError("raw effect identity drift")
    expected_mask = model_atom_mask(effect["atom"], model)
    if mask != expected_mask:
        raise AssertionError("effect mask is not its atom-incidence mask")
    least = (expected_mask & -expected_mask).bit_length() - 1
    if effect["least_word_ordinal_zero_based"] != least:
        raise AssertionError("effect least-word ordinal drift")
    witness = effect["canonical_witness"]
    if witness.get("atom") != effect["atom"] or projected_effect_region(
        witness["descriptor"]
    ) != effect["region"]:
        raise AssertionError("effect/canonical-witness semantic drift")
    return witness


def validate_scan_record(record, expected_unit, model):
    if record.get("scan_unit") != expected_unit:
        raise AssertionError("raw scan record/unit disagreement")
    if record.get("domain") != expected_domain_record(model):
        raise AssertionError("raw scan domain-model metadata drift")
    expected_identity = {
        "occurrence_id": expected_unit["occurrence_id"],
        "class_id": expected_unit["class_id"],
        "trace_id": expected_unit["trace_id"],
        "phase": expected_unit["phase"],
        "scheduler_rank": expected_unit["source_scheduler_rank"] + (
            1 if expected_unit["phase"] == "actual-successor" else 0
        ),
    }
    if any(record.get(key) != value for key, value in expected_identity.items()):
        raise AssertionError("raw scan static unit metadata drift")
    full = validate_mask_record(record["exact_killed_word_mask"], model)
    if full["domain_id"] != expected_unit["domain_id"]:
        raise AssertionError("raw scan domain/manifest disagreement")
    components = []
    for channel in CHANNELS:
        components.append(validate_mask_record(
            record["channel_masks"][channel], model
        ))
        components.append(
            validate_mask_record(
                record["overlapping_near_masks"][channel], model
            )
        )
    far_serialized = [
        json.dumps(
            component["descriptor"], sort_keys=True, separators=(",", ":")
        )
        for component in record["overlapping_far_masks"]
    ]
    if far_serialized != sorted(set(far_serialized)):
        raise AssertionError("far mask descriptors repeat or are noncanonical")
    for component in record["overlapping_far_masks"]:
        validate_effect_region(component["descriptor"])
        if component["descriptor"]["region"] != "far":
            raise AssertionError("far-mask table contains a near descriptor")
        components.append(validate_mask_record(component["mask"], model))
    effect_channel_masks = {channel: 0 for channel in CHANNELS}
    effect_near_masks = {channel: 0 for channel in CHANNELS}
    effect_far_masks = defaultdict(int)
    effect_ids = [effect["effect_id"] for effect in record["effect_records"]]
    if effect_ids != sorted(set(effect_ids)):
        raise AssertionError("effect records repeat or are noncanonical")
    for effect in record["effect_records"]:
        components.append(validate_mask_record(effect["mask"], model))
        effect_mask = decode_raw_mask(effect["mask"])
        witness = validate_effect_record(effect, model, effect_mask)
        channel = effect["region"]["channel"]
        effect_channel_masks[channel] |= effect_mask
        if effect["region"]["region"] == "near":
            effect_near_masks[channel] |= effect_mask
        else:
            descriptor = json.dumps(
                effect["region"], sort_keys=True, separators=(",", ":")
            )
            effect_far_masks[descriptor] |= effect_mask
        token = witness.get("source_observable_token")
        if record["phase"] == "actual-successor":
            if (
                token is None
                or token.get("stable_endpoint_identity_retained") is not False
            ):
                raise AssertionError("successor witness lost identity-free token")
            internal = token.get("token_sha256")
            observed = stable_hash({
                key: value for key, value in token.items()
                if key != "token_sha256"
            })
            if internal != observed:
                raise AssertionError("source-observable token commitment drift")
        elif token is not None:
            raise AssertionError("source effect unexpectedly carries successor token")
    if any(component["domain_id"] != full["domain_id"] for component in components):
        raise AssertionError("one scan record mixes connector domains")
    channel_union = union_masks(
        decode_raw_mask(record["channel_masks"][channel])
        for channel in CHANNELS
    )
    near_far_union = union_masks(
        decode_raw_mask(record["overlapping_near_masks"][channel])
        for channel in CHANNELS
    ) | union_masks(
        decode_raw_mask(component["mask"])
        for component in record["overlapping_far_masks"]
    )
    exact = decode_raw_mask(full)
    if exact != channel_union or exact != near_far_union:
        raise AssertionError("raw exact/channel/shell mask identity drift")
    for channel in CHANNELS:
        if effect_channel_masks[channel] != decode_raw_mask(
            record["channel_masks"][channel]
        ):
            raise AssertionError("effect records do not cover channel mask")
        if effect_near_masks[channel] != decode_raw_mask(
            record["overlapping_near_masks"][channel]
        ):
            raise AssertionError("effect records do not cover near mask")
    declared_far = {
        json.dumps(component["descriptor"], sort_keys=True, separators=(",", ":")):
            decode_raw_mask(component["mask"])
        for component in record["overlapping_far_masks"]
    }
    if dict(effect_far_masks) != declared_far:
        raise AssertionError("effect records do not cover far-component masks")
    ordinal = record["actual_selected_ordinal_zero_based"]
    if (
        isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or not 0 <= ordinal < model["word_count"]
        or tuple(record["actual_selected_word"]) != model["words"][ordinal]
    ):
        raise AssertionError("raw selected word/ordinal/domain binding drift")
    if exact & (1 << ordinal):
        raise AssertionError("raw selected action is killed")
    if record.get("actual_selected_word_geometrically_legal") is not True:
        raise AssertionError("raw selected action lacks an affirmative legality flag")
    witnesses = record.get("witnesses")
    chain = record.get("witness_hash_chain")
    if (
        isinstance(witnesses, bool)
        or not isinstance(witnesses, int)
        or witnesses < len(record["effect_records"])
        or not isinstance(chain, str)
        or len(chain) != 64
    ):
        raise AssertionError("raw witness count/hash-chain schema drift")
    try:
        if bytes.fromhex(chain).hex() != chain:
            raise ValueError
    except ValueError as error:
        raise AssertionError("raw witness hash chain is noncanonical") from error
    if record.get("overlap_identity_verified") is not True:
        raise AssertionError("raw overlap identity was not certified")
    if record.get("endpoint_cutoff") is not None or record.get(
        "distance_cutoff"
    ) is not None or record.get("birth_age_cutoff") is not None:
        raise AssertionError("raw scan silently truncated far endpoints")
    return record


def validate_effect_witness_against_context(effect, context, phase):
    witness = effect["canonical_witness"]
    expected_fields = {
        "old_endpoints", "direction", "moment", "exact_residual",
        "descriptor", "atom",
    }
    if phase == "actual-successor":
        expected_fields.add("source_observable_token")
    if set(witness) != expected_fields:
        raise AssertionError("canonical witness field schema drift")
    endpoints_by_id = {
        endpoint["stable_id"]: endpoint
        for endpoint in context["point_metadata"]
    }
    if len(endpoints_by_id) != len(context["point_metadata"]):
        raise AssertionError("prefix endpoint evidence has repeated stable IDs")
    endpoints = witness["old_endpoints"]
    expected_arity = 2 if effect["region"]["channel"] == "old-old-new" else 1
    if not isinstance(endpoints, list) or len(endpoints) != expected_arity:
        raise AssertionError("canonical witness endpoint arity drift")
    for endpoint_record in endpoints:
        stable_id = endpoint_record.get("stable_id")
        if endpoints_by_id.get(stable_id) != endpoint_record:
            raise AssertionError("canonical witness endpoint/provenance drift")
    descriptor = witness_descriptor(
        effect["region"]["channel"], endpoints,
        context["trace_level"], context["rank"],
    )
    if descriptor != witness["descriptor"]:
        raise AssertionError("canonical witness shell descriptor drift")

    atom = effect["atom"]
    channel = effect["region"]["channel"]
    points = [tuple(endpoint["point"]) for endpoint in endpoints]
    residual = tuple(witness["exact_residual"])
    if channel == "collision":
        if atom["kind"] != "site":
            raise AssertionError("collision effect is not a site atom")
        candidate = add(context["start"], tuple(atom["value"]))
        if (
            points[0] != candidate
            or witness["direction"] is not None
            or witness["moment"] is not None
            or residual != (0, 0, 0)
        ):
            raise AssertionError("collision witness geometry drift")
        atom_value = tuple(atom["value"])
    elif channel == "old-old-new":
        if atom["kind"] != "site" or points[0] == points[1]:
            raise AssertionError("old-old-new witness atom/endpoint drift")
        candidate = add(context["start"], tuple(atom["value"]))
        direction = primitive(sub(points[1], points[0]))
        expected_residual = cross(sub(candidate, points[0]), direction)
        if (
            tuple(witness["direction"]) != direction
            or tuple(witness["moment"]) != cross(points[0], direction)
            or residual != expected_residual
            or residual != (0, 0, 0)
        ):
            raise AssertionError("old-old-new witness geometry drift")
        atom_value = tuple(atom["value"])
    elif channel == "old-new-new":
        if atom["kind"] != "line":
            raise AssertionError("old-new-new effect is not a line atom")
        direction = tuple(atom["value"]["direction"])
        moment = tuple(atom["value"]["moment"])
        if (
            tuple(witness["direction"]) != direction
            or tuple(witness["moment"]) != cross(points[0], direction)
            or cross(sub(points[0], context["start"]), direction) != moment
            or residual != (0, 0, 0)
        ):
            raise AssertionError("old-new-new witness geometry drift")
        atom_value = (direction, moment)
    else:
        raise AssertionError("unknown canonical witness channel")

    if phase == "actual-successor":
        observed = normalized_source_token(
            channel, atom["kind"], atom_value, witness,
            context["source_frame_start"], context["source_rank"],
            context["trace_level"],
        )
        if observed != witness["source_observable_token"]:
            raise AssertionError("successor source-observable token drift")


def validate_scan_record_against_context(record, context):
    expected = {
        "scheduler_rank": context["rank"],
        "gap": context["gap"],
        "step": context["step"],
        "start": list(context["start"]),
        "end": list(context["end"]),
        "prefix": context["prefix"]["commitments"],
        "actual_selected_word": list(context["actual_selected_word"]),
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise AssertionError("raw scan/independent trace replay drift")
    expected_support = {
        "points": len(context["support"]),
        "sha256": stable_hash(context["support"]),
        "near_radius": LOCAL_RADIUS,
    }
    if record.get("corridor_support") != expected_support:
        raise AssertionError("raw corridor support commitment drift")
    for effect in record["effect_records"]:
        validate_effect_witness_against_context(
            effect, context, record["phase"]
        )


def canonical_hex_integer(value, description):
    if not isinstance(value, str):
        raise AssertionError(description + " is not hexadecimal text")
    try:
        result = int(value, 16)
    except ValueError as error:
        raise AssertionError(description + " is invalid hexadecimal") from error
    if result < 0 or hex(result) != value:
        raise AssertionError(description + " is not canonical hexadecimal")
    return result


def validate_active_scan_state(active, unit, context):
    if set(active) != {
        "scan_unit_id", "stage", "cursor", "site_stage_complete",
        "accumulator",
    } or active["scan_unit_id"] != unit["scan_unit_id"]:
        raise AssertionError("active scan/checkpoint unit schema drift")
    stage = active["stage"]
    if stage == "site-atoms":
        limit = len(context["model"]["sites"])
        if active["site_stage_complete"] is not False:
            raise AssertionError("site-stage completion marker drift")
    elif stage == "old-points-for-new-lines":
        limit = len(context["prefix"]["points"])
        if active["site_stage_complete"] is not True:
            raise AssertionError("old-point stage lacks completed-site marker")
    else:
        raise AssertionError("active scan has an unknown stage")
    cursor = active["cursor"]
    if (
        isinstance(cursor, bool)
        or not isinstance(cursor, int)
        or not 0 <= cursor <= limit
    ):
        raise AssertionError("active scan cursor drift")
    raw = active["accumulator"]
    if set(raw) != {
        "channel_masks", "near_masks", "far_masks", "effects",
        "witness_hash_chain", "witnesses",
    } or set(raw["channel_masks"]) != set(CHANNELS) or set(
        raw["near_masks"]
    ) != set(CHANNELS):
        raise AssertionError("active accumulator schema drift")
    for mapping_name in ("channel_masks", "near_masks", "far_masks"):
        for value in raw[mapping_name].values():
            mask = canonical_hex_integer(value, "checkpoint mask")
            if mask.bit_length() > context["model"]["word_count"]:
                raise AssertionError("checkpoint mask exceeds its domain")
    for effect_id, effect in raw["effects"].items():
        if effect.get("effect_id") != effect_id:
            raise AssertionError("checkpoint effect dictionary-key drift")
        canonical_hex_integer(effect["mask"], "checkpoint effect mask")
    accumulator = accumulator_from_json(raw)
    effect_channels = {channel: 0 for channel in CHANNELS}
    effect_near = {channel: 0 for channel in CHANNELS}
    effect_far = defaultdict(int)
    for effect_id, effect in accumulator["effects"].items():
        validate_effect_record(effect, context["model"], effect["mask"])
        validate_effect_witness_against_context(effect, context, unit["phase"])
        channel = effect["region"]["channel"]
        effect_channels[channel] |= effect["mask"]
        if effect["region"]["region"] == "near":
            effect_near[channel] |= effect["mask"]
        else:
            key = json.dumps(
                effect["region"], sort_keys=True, separators=(",", ":")
            )
            effect_far[key] |= effect["mask"]
    if effect_channels != accumulator["channel_masks"] or effect_near != (
        accumulator["near_masks"]
    ) or dict(effect_far) != accumulator["far_masks"]:
        raise AssertionError("checkpoint effects do not reproduce its masks")
    if stage == "site-atoms" and (
        accumulator["channel_masks"]["old-new-new"]
        or any(
            effect["atom"]["kind"] != "site"
            for effect in accumulator["effects"].values()
        )
    ):
        raise AssertionError("site-stage checkpoint contains line-stage work")
    witnesses = accumulator["witnesses"]
    chain = accumulator["witness_hash_chain"]
    if (
        isinstance(witnesses, bool)
        or not isinstance(witnesses, int)
        or witnesses < len(accumulator["effects"])
        or not isinstance(chain, str)
        or len(chain) != 64
    ):
        raise AssertionError("checkpoint witness accounting drift")
    try:
        if bytes.fromhex(chain).hex() != chain:
            raise ValueError
    except ValueError as error:
        raise AssertionError("checkpoint witness hash is noncanonical") from error
    return accumulator


def scan_record_vector(record):
    """Canonical vector; only compare after an explicit domain check."""
    vector = {
        "domain_id": record["domain"]["domain_id"],
        "exact": record["exact_killed_word_mask"]["sha256"],
        "channels": [
            [channel, record["channel_masks"][channel]["sha256"]]
            for channel in CHANNELS
        ],
        "near": [
            [channel, record["overlapping_near_masks"][channel]["sha256"]]
            for channel in CHANNELS
        ],
        "far": [
            [component["descriptor"], component["mask"]["sha256"]]
            for component in record["overlapping_far_masks"]
        ],
    }
    return vector, stable_hash(vector)


def source_effect_features(record):
    near = []
    far = []
    for effect in record["effect_records"]:
        feature = {
            "feature_kind": (
                "near-atom-word-membership"
                if effect["region"]["region"] == "near"
                else "far-shell-atom-word-membership"
            ),
            "region": effect["region"],
            "atom": effect["atom"],
            "least_word_ordinal_zero_based": effect[
                "least_word_ordinal_zero_based"
            ],
            "stable_identity_used": False,
        }
        feature["feature_id"] = stable_hash(feature)
        if effect["region"]["region"] == "near":
            near.append(feature)
        else:
            far.append(feature)
    return near, far


def successor_token_candidates(record):
    result = []
    seen = set()
    for effect in record["effect_records"]:
        token = effect["canonical_witness"].get("source_observable_token")
        if token is None:
            raise AssertionError("successor effect lacks a source-observable token")
        token_id = token["token_sha256"]
        if token_id in seen:
            continue
        seen.add(token_id)
        result.append({
            "feature_kind": "latent-source-Pluecker-or-collision-token",
            "token": token,
            "feature_id": token_id,
            "stable_identity_used": False,
        })
    return result


def chronological_order_key(value):
    return (-1 if value == "inherited" else int(value))


def feature_sort_key(feature):
    kind = feature["feature_kind"]
    if kind == "near-atom-word-membership":
        return (
            0,
            CHANNELS.index(feature["region"]["channel"]),
            canonical_bytes(feature["atom"]),
            feature["least_word_ordinal_zero_based"],
        )
    if kind == "far-shell-atom-word-membership":
        region = feature["region"]
        return (
            1,
            CHANNELS.index(region["channel"]),
            tuple(region["endpoint_age_tuple"]),
            chronological_order_key(region["chronological_shell"]),
            region["spatial_shell"],
            feature["least_word_ordinal_zero_based"],
            canonical_bytes(feature["atom"]),
        )
    return (2, canonical_bytes(feature["token"]))


def record_feature_sets(atomic):
    near, far = source_effect_features(atomic["source"])
    return {
        "near": {feature["feature_id"]: feature for feature in near},
        "far": {feature["feature_id"]: feature for feature in far},
        # Latent-token candidates are discovered from discovery successors but
        # membership is evaluated independently from each source prefix plus
        # its recorded action.  Never populate this from the same successor
        # effect record whose behavior it is supposed to predict.
        "tokens": {},
    }


def independently_evaluate_source_token(token, atomic):
    """Evaluate one frozen token without consulting this occurrence's masks."""
    context = atomic["_token_evaluation_context"]
    level = context["level"]
    source_start = tuple(context["source_frame_start"])
    successor_start = tuple(context["successor_corridor_start"])
    endpoints = []
    for point, provenance in zip(context["points"], context["provenance"]):
        endpoint = compact_endpoint(point, provenance)
        endpoint["normalized_role"] = normalized_endpoint_role(
            endpoint, level, context["source_rank"]
        )
        endpoints.append(endpoint)
    required_roles = Counter(
        stable_hash(role) for role in token["endpoint_birth_roles"]
    )

    if token["channel"] == "collision":
        if len(required_roles) != 1 or sum(required_roles.values()) != 1:
            raise AssertionError("collision token has wrong endpoint arity")
        candidate_from_source = add(
            source_start,
            tuple(token["collision_offset_in_source_corridor_frame"]),
        )
        candidate_from_successor = add(
            successor_start, tuple(token["successor_atom_offset"])
        )
        if candidate_from_source != candidate_from_successor:
            return False
        return any(
            tuple(endpoint["point"]) == candidate_from_source
            and stable_hash(endpoint["normalized_role"]) in required_roles
            for endpoint in endpoints
        )

    direction = tuple(token["primitive_direction"])
    source_moment = tuple(token["moment_in_source_corridor_frame"])
    if token["atom_kind"] == "site":
        candidate = add(successor_start, tuple(token["successor_atom_offset"]))
        if cross(sub(candidate, source_start), direction) != source_moment:
            return False
    else:
        atom_direction = tuple(token["successor_atom_direction"])
        atom_moment = tuple(token["successor_atom_moment"])
        if atom_direction != direction:
            return False
        transformed = add(
            cross(sub(successor_start, source_start), direction), atom_moment
        )
        if transformed != source_moment:
            return False

    observed_roles = Counter()
    for endpoint in endpoints:
        point = tuple(endpoint["point"])
        if cross(sub(point, source_start), direction) != source_moment:
            continue
        role_hash = stable_hash(endpoint["normalized_role"])
        if role_hash in required_roles:
            observed_roles[role_hash] += 1
    return all(
        observed_roles[role_hash] >= multiplicity
        for role_hash, multiplicity in required_roles.items()
    )


def install_discovery_token_features(atomics, discovery, cell_indices):
    """Freeze candidates on discovery; evaluate discovery and holdout at source."""
    candidates = {}
    for index in discovery:
        for feature in successor_token_candidates(atomics[index]["successor"]):
            candidates[feature["feature_id"]] = feature
    for index in cell_indices:
        features = {}
        for feature_id, feature in sorted(candidates.items()):
            if independently_evaluate_source_token(feature["token"], atomics[index]):
                features[feature_id] = feature
        atomics[index]["features"]["tokens"] = features
    return {
        "candidate_tokens_frozen_from_discovery": len(candidates),
        "holdout_successor_masks_consulted_for_token_membership": False,
        "membership_evaluator": (
            "independent source-prefix plus actual-action endpoint role, "
            "primitive direction, source-frame moment, and successor-corridor "
            "residual"
        ),
    }


def load_abc_gamma():
    stable_file_snapshot(
        ABC_POLICY, EXPECTED_ABC_POLICY_SHA256, EXPECTED_ABC_POLICY_BYTES
    )
    with ABC_POLICY.open() as handle:
        artifact = json.load(handle)
    policy = artifact.get("third_ply_CEGAR_policy_partition", {})
    if policy.get("policy_partition_sha256") != (
        "81d85f1a5e21959d5e062c6a26cc43dc77fc54fd5acb810444feece41736d78d"
    ):
        raise AssertionError("frozen ten-leaf A-B-C policy drift")
    leaves = policy.get("policy_leaf_lookup_records", [])
    if len(leaves) != 10:
        raise AssertionError("frozen A-B-C policy is not ten-leaf")
    by_action = {}
    for leaf_position, leaf in enumerate(leaves):
        for action in leaf["A_domain_indices"]:
            if action in by_action:
                raise AssertionError("A-B-C policy action appears in two leaves")
            by_action[action] = {
                "predicate_family": "frozen-ten-leaf-A-B-C",
                "policy_leaf_position": leaf_position,
                "source_class": leaf["source_class"],
                "predicate_path": leaf["predicate_path"],
                "stable_identity_used": False,
            }
    if len(by_action) != 1_997:
        raise AssertionError("A-B-C policy action coverage drift")
    return by_action


def initial_gamma_record(occurrence, source, abc_gamma):
    if not occurrence["exact_L8_ABCDE_factor_motif"]:
        return {
            "predicate_family": "empty-initial-Gamma",
            "predicate_values": [],
        }
    ordinal = source["actual_selected_ordinal_zero_based"]
    if ordinal not in abc_gamma:
        # The ten-leaf policy covered the 1,997 A actions surviving its pinned
        # prefix, not every word of D_14.  A repeated motif occurrence whose
        # actual action lies outside that finite policy has no imported leaf.
        return {
            "predicate_family": "frozen-ten-leaf-A-B-C-outside-covered-actions",
            "A_domain_ordinal_zero_based": ordinal,
            "predicate_values": [],
        }
    return {
        **abc_gamma[ordinal],
        "A_domain_ordinal_zero_based": ordinal,
    }


def target_signature(atomic):
    source_vector, source_hash = scan_record_vector(atomic["source"])
    successor_vector, successor_hash = scan_record_vector(atomic["successor"])
    successor_state = atomic["actual_successor_abstract_state_action"]
    return {
        "source_vector": source_vector,
        "source_sha256": source_hash,
        "successor_vector": successor_vector,
        "successor_sha256": successor_hash,
        "successor_ordered_factor_state_action_sha256": successor_state[
            "state_action_sha256"
        ],
    }


def choose_varying_feature(atomics, indices, tier):
    candidates = {}
    for index in indices:
        candidates.update(atomics[index]["features"][tier])
    ordered = sorted(candidates.values(), key=feature_sort_key)
    for feature in ordered:
        values = [
            feature["feature_id"] in atomics[index]["features"][tier]
            for index in indices
        ]
        if any(values) and not all(values):
            return feature
    return None


def build_discovery_cegar(atomics, discovery_indices):
    nodes = []

    def recurse(indices, path):
        node_id = len(nodes)
        nodes.append(None)
        targets = {
            (
                atomics[index]["target"]["source_sha256"],
                atomics[index]["target"]["successor_sha256"],
                atomics[index]["target"][
                    "successor_ordered_factor_state_action_sha256"
                ],
            )
            for index in indices
        }
        if len(targets) == 1:
            target = atomics[indices[0]]["target"]
            nodes[node_id] = {
                "node_id": node_id,
                "status": "congruent-discovery-leaf",
                "discovery_indices": indices,
                "occurrence_ids": [
                    atomics[index]["occurrence_id"] for index in indices
                ],
                "predicate_path": path,
                "expected_source_sha256": target["source_sha256"],
                "expected_successor_sha256": target["successor_sha256"],
                "expected_successor_ordered_factor_state_action_sha256": (
                    target["successor_ordered_factor_state_action_sha256"]
                ),
            }
            return node_id

        feature = choose_varying_feature(atomics, indices, "near")
        tier = "near"
        if feature is None:
            feature = choose_varying_feature(atomics, indices, "far")
            tier = "far"
        source_signatures = {
            atomics[index]["target"]["source_sha256"] for index in indices
        }
        if feature is None and len(source_signatures) == 1:
            feature = choose_varying_feature(atomics, indices, "tokens")
            tier = "tokens"
        if feature is None:
            nodes[node_id] = {
                "node_id": node_id,
                "status": "unresolved-noncongruence",
                "discovery_indices": indices,
                "occurrence_ids": [
                    atomics[index]["occurrence_id"] for index in indices
                ],
                "predicate_path": path,
                "distinct_source_signatures": len(source_signatures),
                "distinct_target_signatures": len(targets),
                "reason": (
                    "no permitted near, far-shell, or source-observable "
                    "latent token separates this concrete difference"
                ),
            }
            return node_id
        if feature.get("stable_identity_used"):
            raise AssertionError("CEGAR attempted an identity-based refinement")
        absent = [
            index for index in indices
            if feature["feature_id"] not in atomics[index]["features"][tier]
        ]
        present = [
            index for index in indices
            if feature["feature_id"] in atomics[index]["features"][tier]
        ]
        if not absent or not present:
            raise AssertionError("CEGAR chose a constant predicate")
        node = {
            "node_id": node_id,
            "status": "refinement",
            "discovery_indices": indices,
            "occurrence_ids": [
                atomics[index]["occurrence_id"] for index in indices
            ],
            "predicate_path": path,
            "refinement_tier": tier,
            "feature": feature,
            "feature_is_source_observable": True,
            "identity_based_refinement": False,
        }
        nodes[node_id] = node
        absent_path = path + [{
            "feature_id": feature["feature_id"],
            "present": False,
        }]
        present_path = path + [{
            "feature_id": feature["feature_id"],
            "present": True,
        }]
        node["absent_child"] = recurse(absent, absent_path)
        node["present_child"] = recurse(present, present_path)
        return node_id

    root = recurse(list(discovery_indices), [])
    return {
        "root": root,
        "nodes": nodes,
        "tree_sha256": stable_hash(nodes),
        "refinements": sum(node["status"] == "refinement" for node in nodes),
        "unresolved_nodes": sum(
            node["status"] == "unresolved-noncongruence" for node in nodes
        ),
        "identity_based_refinements": 0,
    }


def route_holdout(tree, atomic):
    node_id = tree["root"]
    while True:
        node = tree["nodes"][node_id]
        if node["status"] != "refinement":
            return node
        feature = node["feature"]
        tier = node["refinement_tier"]
        present = feature["feature_id"] in atomic["features"][tier]
        node_id = node["present_child"] if present else node["absent_child"]


def maximal_mask_antichain(atomics, phase):
    entries = []
    for atomic in atomics:
        record = atomic[phase]["exact_killed_word_mask"]
        mask = decode_raw_mask(record)
        entries.append((mask, atomic["occurrence_id"], record))
    maximal = []
    for mask, occurrence_id, record in sorted(
        entries, key=lambda item: (-item[0].bit_count(), item[1])
    ):
        if any(mask | kept[0] == kept[0] for kept in maximal):
            continue
        maximal.append((mask, occurrence_id, record))
    return {
        "scope": (
            "current availability only; discarded masks do not discard latent "
            "line tokens and this is not a future dominance relation"
        ),
        "members": [{
            "occurrence_id": occurrence_id,
            "mask_sha256": record["sha256"],
            "population": record["population"],
        } for _mask, occurrence_id, record in maximal],
    }


def scan_mask_components(record):
    result = [({"kind": "exact"}, record["exact_killed_word_mask"])]
    result.extend(
        ({"kind": "channel", "channel": channel}, record["channel_masks"][channel])
        for channel in CHANNELS
    )
    result.extend(
        (
            {"kind": "near", "channel": channel},
            record["overlapping_near_masks"][channel],
        )
        for channel in CHANNELS
    )
    result.extend(
        (
            {"kind": "far", "descriptor": component["descriptor"]},
            component["mask"],
        )
        for component in record["overlapping_far_masks"]
    )
    return result


def component_effect_matches(effect, component):
    kind = component["kind"]
    if kind == "exact":
        return True
    if kind == "channel":
        return effect["region"]["channel"] == component["channel"]
    if kind == "near":
        return (
            effect["region"]["region"] == "near"
            and effect["region"]["channel"] == component["channel"]
        )
    return effect["region"] == component["descriptor"]


def least_difference_record(left_atomic, right_atomic, phase):
    left = left_atomic[phase]
    right = right_atomic[phase]
    if left["domain"]["domain_id"] != right["domain"]["domain_id"]:
        raise AssertionError("difference requested across connector domains")
    left_components = {
        stable_hash(component): (component, mask)
        for component, mask in scan_mask_components(left)
    }
    right_components = {
        stable_hash(component): (component, mask)
        for component, mask in scan_mask_components(right)
    }
    chosen = None
    for component_id in sorted(set(left_components) | set(right_components)):
        exemplar = (left_components.get(component_id) or right_components[component_id])[0]
        left_mask_record = left_components.get(component_id, (None, None))[1]
        right_mask_record = right_components.get(component_id, (None, None))[1]
        left_mask = decode_raw_mask(left_mask_record) if left_mask_record else 0
        right_mask = decode_raw_mask(right_mask_record) if right_mask_record else 0
        difference = left_mask ^ right_mask
        if difference:
            chosen = (exemplar, left_mask, right_mask, difference)
            break
    if chosen is None:
        return None
    component, left_mask, right_mask, difference = chosen
    ordinal = (difference & -difference).bit_length() - 1

    def witness_for(record):
        candidates = []
        for effect in record["effect_records"]:
            if (
                component_effect_matches(effect, component)
                and decode_raw_mask(effect["mask"]) & (1 << ordinal)
            ):
                candidates.append(effect["canonical_witness"])
        return min(candidates, key=canonical_bytes) if candidates else None

    return {
        "phase": phase,
        "least_differing_component": component,
        "least_differing_word_ordinal_zero_based": ordinal,
        "left_occurrence_id": left_atomic["occurrence_id"],
        "right_occurrence_id": right_atomic["occurrence_id"],
        "left_component_bit": bool(left_mask & (1 << ordinal)),
        "right_component_bit": bool(right_mask & (1 << ordinal)),
        "left_exact_witness": witness_for(left),
        "right_exact_witness": witness_for(right),
    }


def least_transition_difference(left, right):
    mask_difference = least_difference_record(left, right, "successor")
    if mask_difference is not None:
        return mask_difference
    left_state = left["actual_successor_abstract_state_action"]
    right_state = right["actual_successor_abstract_state_action"]
    if left_state["state_action_sha256"] != right_state["state_action_sha256"]:
        return {
            "phase": "actual-successor-abstract-state",
            "least_differing_component": {
                "kind": "full-ordered-factor-state-action"
            },
            "left_occurrence_id": left["occurrence_id"],
            "right_occurrence_id": right["occurrence_id"],
            "left_state_action_sha256": left_state["state_action_sha256"],
            "right_state_action_sha256": right_state["state_action_sha256"],
            "left_ordered_factor_sha256": left_state[
                "ordered_factor_sha256"
            ],
            "right_ordered_factor_sha256": right_state[
                "ordered_factor_sha256"
            ],
        }
    return None


def analyze_class(class_record, atomics, abc_gamma):
    atomics = sorted(atomics, key=lambda item: item["occurrence_id"])
    domain_ids = {
        (item["source"]["domain"]["domain_id"],
         item["successor"]["domain"]["domain_id"])
        for item in atomics
    }
    if len(domain_ids) != 1:
        raise AssertionError("matched class mixes source/successor domains")
    for atomic in atomics:
        atomic["target"] = target_signature(atomic)
        atomic["features"] = record_feature_sets(atomic)
        atomic["initial_gamma"] = initial_gamma_record(
            atomic["occurrence"], atomic["source"], abc_gamma
        )
    gamma_cells = defaultdict(list)
    for index, atomic in enumerate(atomics):
        gamma_cells[stable_hash(atomic["initial_gamma"])].append(index)

    far_positive = sum(
        any(component["mask"]["population"] > 0 for component in atomic[
            "source"
        ]["overlapping_far_masks"])
        for atomic in atomics
    )
    source_union = 0
    for atomic in atomics:
        source_union |= decode_raw_mask(atomic["source"]["exact_killed_word_mask"])
    word_count = atomics[0]["source"]["domain"]["words"]
    common_legal = ((1 << word_count) - 1) & ~source_union
    actual_actions = {tuple(item["source"]["actual_selected_word"]) for item in atomics}
    if len(actual_actions) != 1:
        raise AssertionError("matched key did not retain one actual action")
    actual_ordinal = atomics[0]["source"]["actual_selected_ordinal_zero_based"]
    actual_common_legal = not bool(source_union & (1 << actual_ordinal))

    cell_results = []
    initial_refutations = []
    final_groups = []
    holdout_failures = []
    held_out_members_tested = 0
    for gamma_hash, cell_indices in sorted(gamma_cells.items()):
        ordered = sorted(cell_indices, key=lambda index: atomics[index]["occurrence_id"])
        holdout_count = max(1, len(ordered) // 3) if len(ordered) >= 4 else 0
        discovery = ordered[:-holdout_count] if holdout_count else ordered
        holdouts = ordered[-holdout_count:] if holdout_count else []
        held_out_members_tested += len(holdouts)
        if len(discovery) < 1:
            raise AssertionError("CEGAR discovery set is empty")
        token_evaluation = install_discovery_token_features(
            atomics, discovery, ordered
        )

        for left_position, left_index in enumerate(ordered):
            for right_index in ordered[left_position + 1:]:
                left = atomics[left_index]
                right = atomics[right_index]
                if left["target"]["source_sha256"] == right["target"][
                    "source_sha256"
                ] and (
                    left["target"]["successor_sha256"],
                    left["target"][
                        "successor_ordered_factor_state_action_sha256"
                    ],
                ) != (
                    right["target"]["successor_sha256"],
                    right["target"][
                        "successor_ordered_factor_state_action_sha256"
                    ],
                ):
                    initial_refutations.append(
                        least_transition_difference(left, right)
                    )
        tree = build_discovery_cegar(atomics, discovery)
        attached = defaultdict(list)
        for index in holdouts:
            leaf = route_holdout(tree, atomics[index])
            attached[leaf["node_id"]].append(index)
            if leaf["status"] != "congruent-discovery-leaf":
                holdout_failures.append({
                    "gamma_sha256": gamma_hash,
                    "occurrence_id": atomics[index]["occurrence_id"],
                    "leaf_node_id": leaf["node_id"],
                    "reason": "holdout reached unresolved discovery leaf",
                })
                continue
            target = atomics[index]["target"]
            if (
                target["source_sha256"] != leaf["expected_source_sha256"]
                or target["successor_sha256"] != leaf[
                    "expected_successor_sha256"
                ]
                or target[
                    "successor_ordered_factor_state_action_sha256"
                ] != leaf[
                    "expected_successor_ordered_factor_state_action_sha256"
                ]
            ):
                representative = atomics[leaf["discovery_indices"][0]]
                holdout_failures.append({
                    "gamma_sha256": gamma_hash,
                    "occurrence_id": atomics[index]["occurrence_id"],
                    "leaf_node_id": leaf["node_id"],
                    "reason": "held-out successor requires a new refinement",
                    "least_difference": least_transition_difference(
                        representative, atomics[index]
                    ),
                })
        for node in tree["nodes"]:
            if node["status"] not in {
                "congruent-discovery-leaf", "unresolved-noncongruence"
            }:
                continue
            members = node["discovery_indices"] + attached[node["node_id"]]
            final_groups.append({
                "gamma_sha256": gamma_hash,
                "node_id": node["node_id"],
                "status": node["status"],
                "occurrence_ids": [
                    atomics[index]["occurrence_id"] for index in members
                ],
                "members": len(members),
                "discovery_members": len(node["discovery_indices"]),
                "held_out_members": len(attached[node["node_id"]]),
                "_member_indices": members,
            })
        cell_results.append({
            "initial_gamma_sha256": gamma_hash,
            "initial_gamma": atomics[ordered[0]]["initial_gamma"],
            "members": len(ordered),
            "discovery_members": len(discovery),
            "held_out_members": len(holdouts),
            "latent_token_evaluation": token_evaluation,
            "CEGAR": tree,
        })

    effectful_final = [
        group for group in final_groups
        if any(
            any(component["mask"]["population"] > 0 for component in atomic[
                "source"
            ]["overlapping_far_masks"])
            for atomic in atomics
            if atomic["occurrence_id"] in group["occurrence_ids"]
        )
    ]
    singleton_effectful = bool(effectful_final) and all(
        group["members"] == 1 for group in effectful_final
    )
    qualifying_groups = []
    public_final_groups = []
    for group in final_groups:
        member_atomics = [atomics[index] for index in group["_member_indices"]]
        member_union = union_masks(
            decode_raw_mask(item["source"]["exact_killed_word_mask"])
            for item in member_atomics
        )
        member_common_legal = ((1 << word_count) - 1) & ~member_union
        member_far_positive = sum(
            any(component["mask"]["population"] > 0 for component in item[
                "source"
            ]["overlapping_far_masks"])
            for item in member_atomics
        )
        member_roots = {
            item["occurrence"]["ancestry_root"] for item in member_atomics
        }
        member_levels = {item["occurrence"]["level"] for item in member_atomics}
        member_families = {
            item["occurrence"]["family"] for item in member_atomics
        }
        member_actions = {
            tuple(item["source"]["actual_selected_word"])
            for item in member_atomics
        }
        member_action_ordinals = {
            item["source"]["actual_selected_ordinal_zero_based"]
            for item in member_atomics
        }
        group_holdout_failures = [
            failure for failure in holdout_failures
            if failure["gamma_sha256"] == group["gamma_sha256"]
            and failure["occurrence_id"] in group["occurrence_ids"]
        ]
        requirements = {
            "same_group_has_at_least_three_members": group["members"] >= 3,
            "same_group_has_discovery_and_holdout": (
                group["discovery_members"] >= 2
                and group["held_out_members"] >= 1
            ),
            "same_group_has_two_ancestry_roots": len(member_roots) >= 2,
            "same_group_has_two_horizons": (
                len(member_levels) >= 2 or len(member_families) >= 2
            ),
            "same_group_has_two_far_positive_members": (
                member_far_positive >= 2
            ),
            "same_group_has_common_legal_action": member_common_legal != 0,
            "recorded_state_action_key_has_one_action": len(member_actions) == 1,
            "recorded_action_ordinal_is_common": len(member_action_ordinals) == 1,
            "recorded_action_is_legal_for_same_group": not bool(
                member_union & (1 << next(iter(member_action_ordinals)))
            ),
            "same_group_successor_is_congruent": (
                group["status"] == "congruent-discovery-leaf"
            ),
            "same_group_holdout_agrees_without_refinement": (
                not group_holdout_failures
            ),
            "no_identity_based_refinement": True,
        }
        public = {
            key: value for key, value in group.items()
            if not key.startswith("_")
        }
        public.update({
            "far_positive_members": member_far_positive,
            "ancestry_roots": len(member_roots),
            "levels": sorted(member_levels),
            "families": sorted(member_families),
            "common_legal_words": member_common_legal.bit_count(),
            "holdout_failures": group_holdout_failures,
            "joint_nonvacuous_pass_requirements": requirements,
            "joint_nonvacuous_finite_pass": all(requirements.values()),
        })
        public_final_groups.append(public)
        if public["joint_nonvacuous_finite_pass"]:
            qualifying_groups.append(public)

    nonvacuous_requirements = {
        "one_same_final_group_jointly_satisfies_every_requirement": bool(
            qualifying_groups
        ),
        "effectful_classes_not_all_singletons": not singleton_effectful,
        "recorded_action_identity_is_part_of_the_frozen_state_action_key": True,
        "controller_action_selection_congruence_claimed": False,
    }
    return {
        "class_id": class_record["class_id"],
        "key_sha256": class_record["key_sha256"],
        "occurrences": len(atomics),
        "far_positive_occurrences": far_positive,
        "vacuous_for_far_stabilization": far_positive < 2,
        "componentwise_OR_uniform_legality": {
            "source_domain_id": atomics[0]["source"]["domain"]["domain_id"],
            "killed_union_population": source_union.bit_count(),
            "common_legal_words": common_legal.bit_count(),
            "least_common_legal_ordinal_zero_based": (
                (common_legal & -common_legal).bit_length() - 1
                if common_legal else None
            ),
            "actual_recorded_action_common_legal": actual_common_legal,
        },
        "maximal_mask_antichain": maximal_mask_antichain(atomics, "source"),
        "initial_projection_refutations": initial_refutations,
        "initial_projection_refuted": bool(initial_refutations),
        "CEGAR_cells": cell_results,
        "final_groups": public_final_groups,
        "jointly_qualifying_final_group_ids": [
            [group["gamma_sha256"], group["node_id"]]
            for group in qualifying_groups
        ],
        "held_out_failures": holdout_failures,
        "held_out_members_tested": held_out_members_tested,
        "effectful_classes_all_singletons": singleton_effectful,
        "nonvacuous_pass_requirements": nonvacuous_requirements,
        "nonvacuous_finite_pass": (
            bool(qualifying_groups) and not singleton_effectful
        ),
        "claim_scope": (
            "recorded state-action transition stabilization only; because the "
            "actual action is in the Phase-A key, identical recorded actions "
            "are a construction fact, not a learned controller quotient"
        ),
    }


def atomic_transition_records(
    manifest, scan_records, traces, domains, d24, catalog,
    catalog_by_id, models_by_domain,
):
    by_unit = {record["scan_unit"]["scan_unit_id"]: record for record in scan_records}
    if len(by_unit) != len(scan_records):
        raise AssertionError("duplicate scan-unit record")
    expected_units = {unit["scan_unit_id"]: unit for unit in manifest["scan_units"]}
    if set(by_unit) != set(expected_units):
        raise AssertionError("raw shards do not exactly cover the manifest")
    for unit_id, unit in expected_units.items():
        validate_scan_record(
            by_unit[unit_id], unit, models_by_domain[unit["domain_id"]]
        )
    occurrences = manifest_occurrences(manifest)
    classes = {
        record["class_id"]: record for record in manifest["panel_classes"]
    }
    result = []
    for occurrence_id, occurrence in sorted(occurrences.items()):
        records = [
            by_unit[unit["scan_unit_id"]]
            for unit in manifest["scan_units"]
            if unit["occurrence_id"] == occurrence_id
        ]
        if len(records) != 2:
            raise AssertionError("occurrence lacks exact source/successor pair")
        by_phase = {record["phase"]: record for record in records}
        if set(by_phase) != {"source", "actual-successor"}:
            raise AssertionError("occurrence phases drift")
        trace = traces[occurrence["trace_id"]]
        replayed = occurrence_metadata(
            trace, occurrence["scheduler_rank"], d24, catalog,
            manifest["frozen_L8_ABCDE_factor_sha256"],
        )
        if compact_occurrence(replayed) != occurrence:
            raise AssertionError("manifest occurrence metadata replay drift")
        class_id = records[0]["class_id"]
        if (
            any(record["class_id"] != class_id for record in records)
            or classes[class_id]["key"] != replayed["key"]
        ):
            raise AssertionError("manifest class/full ordered-factor key drift")
        source_prefix = reconstruct_prefix(trace, occurrence["scheduler_rank"])
        successor_prefix = reconstruct_prefix(
            trace, occurrence["scheduler_rank"] + 1
        )
        if source_prefix["commitments"] != by_phase["source"]["prefix"]:
            raise AssertionError("independent source-prefix replay drift")
        if successor_prefix["commitments"] != by_phase[
            "actual-successor"
        ]["prefix"]:
            raise AssertionError("independent successor-prefix replay drift")
        for phase in ("source", "actual-successor"):
            unit = by_phase[phase]["scan_unit"]
            context = prepare_scan_context(
                unit, occurrence, trace, domains, catalog_by_id
            )
            context["trace_level"] = trace["level"]
            validate_scan_record_against_context(by_phase[phase], context)
        gap = occurrence["gap"]
        action = tuple(occurrence["actual_action"])
        if tuple(by_phase["source"]["actual_selected_word"]) != action:
            raise AssertionError("source scan/manifest action disagreement")
        successor_gap = occurrence["successor_gap"]
        if tuple(by_phase["actual-successor"]["actual_selected_word"]) != tuple(
            trace["selected_by_gap"][successor_gap]
        ):
            raise AssertionError("successor scan/trace action disagreement")
        interiors = tuple(word_interiors(trace["anchors"][gap], action))
        if tuple(source_prefix["points"]) + interiors != tuple(
            successor_prefix["points"]
        ):
            raise AssertionError("P_successor != P_source union action interiors")
        source_state_action, _source_bounds = abstract_state_action(
            trace, occurrence["scheduler_rank"], d24
        )
        if source_state_action != replayed["key"]:
            raise AssertionError("source state-action/key schema mismatch")
        successor_state_action, _successor_bounds = abstract_state_action(
            trace, occurrence["scheduler_rank"] + 1, d24
        )
        successor_state_record = {
            "schema": "replayed-full-successor-state-action-v1",
            "state_action": successor_state_action,
            "state_action_sha256": stable_hash(successor_state_action),
            "ordered_factor_sha256": stable_hash(
                successor_state_action["ordered_factor"]
            ),
        }
        transition = {
            "occurrence_id": occurrence_id,
            "class_id": class_id,
            "occurrence": occurrence,
            "source": by_phase["source"],
            "actual_action": {
                "word": list(action),
                "interiors": [list(point) for point in interiors],
                "interior_stream_sha256": point_stream_sha256(interiors),
                "legal_at_source": True,
            },
            "successor": by_phase["actual-successor"],
            "actual_successor_abstract_state_action": successor_state_record,
            "transition_identity": {
                "P_successor_equals_P_source_union_action_interiors": True,
                "source_prefix_sha256": source_prefix["commitments"][
                    "point_stream_sha256"
                ],
                "successor_prefix_sha256": successor_prefix["commitments"][
                    "point_stream_sha256"
                ],
                "source_full_ordered_factor_state_action_sha256": stable_hash(
                    source_state_action
                ),
                "manifest_source_key_sha256": replayed["key_sha256"],
                "successor_full_ordered_factor_state_action_replayed": True,
            },
            "correlation": (
                "one indivisible concrete record; masks, endpoints, action, "
                "and successor are never Cartesian-recombined"
            ),
            "_token_evaluation_context": {
                # Private analysis-only data.  It is reconstructed from the
                # source and action, never taken from a successor poison mask,
                # and is removed before the terminal JSON is emitted.
                "points": tuple(successor_prefix["points"]),
                "provenance": tuple(successor_prefix["provenance"]),
                "source_frame_start": tuple(trace["anchors"][gap]),
                "successor_corridor_start": tuple(
                    trace["anchors"][occurrence["successor_gap"]]
                ),
                "level": trace["level"],
                "source_rank": occurrence["scheduler_rank"],
            },
        }
        result.append(transition)
    return result


def public_atomic_transition(record):
    fields = (
        "occurrence_id", "class_id", "occurrence", "source",
        "actual_action", "successor",
        "actual_successor_abstract_state_action", "transition_identity",
        "correlation",
    )
    return {field: record[field] for field in fields}


def finalize_experiment(args, policy, lease_slot):
    manifest, manifest_snapshot = verify_panel_manifest(args.manifest)
    if not args.raw_input:
        raise ValueError("finalize requires one or two --raw-input shards")
    raws = []
    raw_snapshots = []
    for path in args.raw_input:
        raw, snapshot = verify_raw_shard(path, manifest_snapshot)
        raws.append(raw)
        raw_snapshots.append(snapshot)
    declared = {raw["shard_count"] for raw in raws}
    indices = {raw["shard_index"] for raw in raws}
    declared_count = next(iter(declared)) if len(declared) == 1 else None
    if (
        declared_count not in {1, 2}
        or len(raws) != declared_count
        or indices != set(range(declared_count))
    ):
        raise AssertionError("raw shard set is incomplete or inconsistent")
    scan_records = [record for raw in raws for record in raw["records"]]
    traces, input_snapshots = load_all_traces(args)
    domains, d24, catalog = build_domain_catalog()
    if [catalog[step] for step in range(len(MENU))] != manifest[
        "domain_catalog"
    ]:
        raise AssertionError("finalizer domain catalog differs from manifest")
    catalog_by_id = {record["domain_id"]: record for record in catalog.values()}
    if len(catalog_by_id) != len(catalog):
        raise AssertionError("finalizer domain identity collision")
    models_by_domain = {}
    for unit in manifest["scan_units"]:
        domain_id = unit["domain_id"]
        if domain_id not in models_by_domain:
            expected = catalog_by_id[domain_id]
            models_by_domain[domain_id] = build_exact_domain_model(
                expected["step"], domains[expected["step"]], expected
            )
    transitions = atomic_transition_records(
        manifest, scan_records, traces, domains, d24, catalog,
        catalog_by_id, models_by_domain,
    )
    abc_gamma = load_abc_gamma()
    by_class = defaultdict(list)
    for transition in transitions:
        by_class[transition["class_id"]].append(transition)
    class_results = []
    first_nonvacuous = None
    for class_record in manifest["panel_classes"]:
        result = analyze_class(
            class_record, by_class[class_record["class_id"]], abc_gamma
        )
        class_results.append(result)
        if first_nonvacuous is None and not result[
            "vacuous_for_far_stabilization"
        ]:
            first_nonvacuous = result
            break
    if first_nonvacuous is None:
        verdict = "vacuous-no-preordered-class-has-two-far-positive-members"
    elif first_nonvacuous["nonvacuous_finite_pass"]:
        verdict = "nonvacuous-finite-trace-stabilization-pass"
    elif first_nonvacuous["held_out_failures"]:
        verdict = "held-out-stabilization-failure"
    elif first_nonvacuous["effectful_classes_all_singletons"]:
        verdict = "effectful-refinement-collapses-to-singletons"
    elif first_nonvacuous["initial_projection_refuted"]:
        verdict = "recorded-projection-noncongruence-found"
    else:
        verdict = "finite-panel-inconclusive-or-refuted"
    public_transitions = [
        public_atomic_transition(record) for record in transitions
    ]
    transition_stream_sha256 = stable_hash(public_transitions)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "exact finite matched-transition stabilization experiment",
        "verdict": verdict,
        "phase_B_checker_sha256": PROCESS_START_CHECKER_SHA256,
        "manifest": manifest_snapshot,
        "raw_shards": raw_snapshots,
        "atomic_transition_records": public_transitions,
        "atomic_transition_stream_sha256": transition_stream_sha256,
        "class_results_considered_in_preorder": class_results,
        "first_nonvacuous_class_id": (
            first_nonvacuous["class_id"] if first_nonvacuous else None
        ),
        "soundness": {
            "complete_illegality_cases": [
                "collision",
                "new point on an old-old secant",
                "old point on a new-new line",
                "intrinsic three-new defects excluded by certified D_s",
            ],
            "every_prefix_endpoint_scanned": True,
            "endpoint_or_distance_cutoff": None,
            "source_and_actual_successor_recomputed_independently": True,
            "actual_transition_identity_verified": True,
            "successor_full_ordered_factor_state_action_replayed": True,
            "domain_endpoint_distinctness_and_all_new_triples_rechecked": True,
            "overlapping_shell_masks_OR_to_exact_K": True,
            "different_domains_never_compared_bitwise": True,
            "occurrence_records_never_cartesian_recombined": True,
        },
        "not_proved": [
            "all reachable ordered factors map into this finite state universe",
            "universal successors under alternate legal actions and histories",
            "closure under every legal connector choice",
            "a uniform far-shell contraction or well-founded ranking",
            "a greatest-fixed-point common-action safety certificate",
            "an unconditional infinite Erdos #193 walk",
        ],
        "leading_adversarial_obstruction": (
            "two records agree on current effect masks while a silent far "
            "secant retains an unbounded affine-address phase and reactivates "
            "later; CEGAR then either finds a successor mismatch or refines "
            "every effectful repeated class to a singleton"
        ),
        "input_snapshots": input_snapshots,
        "resource_policy": policy,
        "cooperative_lease_slot": lease_slot,
    }
    result["payload_sha256"] = stable_hash(result)
    atomic_json_dump(result, args.output)
    return {
        "status": result["status"],
        "verdict": verdict,
        "output": str(Path(args.output).resolve()),
        "output_sha256": file_sha256(args.output),
        "payload_sha256": result["payload_sha256"],
        "atomic_transitions": len(transitions),
        "atomic_transition_stream_sha256": transition_stream_sha256,
    }


def estimate():
    return {
        "status": "prepared fail-closed matched-transition experiment",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "phase_A": {
            "scope": "gate2 L5-L8 plus terminal-audited primary L6",
            "poison_blind": True,
            "expected_gate_stitches": EXPECTED_GATE_STITCHES,
            "expected_primary_L6_stitches": EXPECTED_PRIMARY_L6_STITCHES,
            "terminal_pins_finalized": terminal_pins_finalized(),
            "locked": not terminal_pins_finalized(),
        },
        "phase_B": {
            "complete_exact_channels": list(CHANNELS),
            "endpoint_or_distance_cutoff": None,
            "manifest_pins_finalized": panel_pins_finalized(),
            "locked": not panel_pins_finalized(),
            "maximum_scans": MAX_PANEL_SCANS,
        },
        "resource_policy": {
            "maximum_processes": MAX_SHARDS,
            "threads_per_process": 1,
            "required_minimum_nice": 15,
            "cooperative_two_slot_lock_for_this_checker": True,
            "external_homelab_jobs_must_be_counted_separately": True,
        },
        "large_artifacts_opened": False,
    }


def normalized_shard_path(path, shard_index, shard_count):
    path = Path(path)
    if shard_count == 1:
        return path
    return path.with_name(
        path.stem + f"-shard{shard_index}-of-{shard_count}" + path.suffix
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("estimate", "census", "scan", "finalize")
    )
    parser.add_argument("--primary-source", default=str(DEFAULT_PRIMARY_SOURCE))
    parser.add_argument(
        "--primary-terminal", default=str(DEFAULT_PRIMARY_TERMINAL)
    )
    parser.add_argument(
        "--primary-parent-source", default=str(DEFAULT_PRIMARY_PARENT_SOURCE)
    )
    parser.add_argument(
        "--primary-parent-terminal", default=str(DEFAULT_PRIMARY_PARENT_TERMINAL)
    )
    parser.add_argument("--census-output", default=str(DEFAULT_CENSUS))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--raw-output", default=str(DEFAULT_RAW))
    parser.add_argument("--raw-input", action="append")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-seconds", type=float, default=MAX_SECONDS)
    parser.add_argument("--max-work-items", type=int, default=MAX_WORK_ITEMS)
    args = parser.parse_args()
    if args.mode != "estimate" and Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run heavy modes from the repository root: cd {ROOT}")
    if not 1 <= args.shard_count <= MAX_SHARDS:
        raise ValueError("shard-count must be one or two")
    if not 0 <= args.shard_index < args.shard_count:
        raise ValueError("shard-index outside declared shard-count")
    if not 0 < args.max_seconds <= MAX_SECONDS:
        raise ValueError("max-seconds outside allowed range")
    if not 1 <= args.max_work_items <= MAX_WORK_ITEMS:
        raise ValueError("max-work-items outside allowed range")
    policy = enforce_resources(args.mode, args.shard_count)
    lease = None
    lease_slot = None
    if args.mode in {"census", "scan", "finalize"}:
        lease, lease_slot = acquire_core_lease()
    try:
        if args.mode == "estimate":
            result = estimate()
        elif args.mode == "census":
            if args.shard_count != 1:
                raise ValueError("metadata census is exactly one process")
            result = phase_a_census(args, policy)
        elif args.mode == "scan":
            args.checkpoint = str(normalized_shard_path(
                args.checkpoint, args.shard_index, args.shard_count
            ))
            args.raw_output = str(normalized_shard_path(
                args.raw_output, args.shard_index, args.shard_count
            ))
            result = scan_chunk(args, policy, lease_slot)
        else:
            if args.shard_count != 1 or args.shard_index != 0:
                raise ValueError("finalize is one low-priority process")
            result = finalize_experiment(args, policy, lease_slot)
        assert_checker_unchanged()
        print(json.dumps(result, sort_keys=True, indent=2))
    finally:
        if lease is not None:
            fcntl.flock(lease.fileno(), fcntl.LOCK_UN)
            lease.close()


if __name__ == "__main__":
    main()
