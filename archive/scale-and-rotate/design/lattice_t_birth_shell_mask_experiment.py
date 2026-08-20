#!/usr/bin/env python3
"""Exact realized-path birth/shell mask panel for lattice-T L5 -> L6.

This finite experiment consumes the independently audited lattice-T L5 path.
It chooses one parent stitch by a poison-blind rule fixed in this checker, then
examines that pending L5 corridor and every actual L6 child corridor induced
by the parent's selected connector word.  The child address is never formed
from an independent stream: parent gap, selected word, slot, exact prefix,
child step, and child cursor stay correlated.

For every probe the checker scans the complete relevant placed set, with no
endpoint or distance cutoff, against the complete pinned effective connector
domain.  It covers all three external legality channels:

* collision at a proposed interior site;
* old--old--new, where two placed points determine a secant through a proposed
  interior; and
* old--new--new, where a placed point lies on a line through two proposed
  interiors.

Every genuine witness is attributed to an exact D=40/3-adic spatial shell and
to a birth cohort/rank shell relative to the chosen L5 parent.  Descriptor
masks are exact overlapping memberships.  The output reports actual bitwise
OR masks, intersections, and priority-only remainders; it never adds witness
counts or descriptor mask sizes as though they were disjoint.

The induced L6 state contains all M-images of the completed L5 natural path as
anchors and no L6 connector interiors.  Thus it is an exact owner-descendant
frame test, but not an L6 chronological construction or a safety-game closure
test.  A successful finite panel is evidence only: it proves no level-uniform
tail, positive availability theorem, or unconditional solution of Erdos #193.

The scan is resumable inside a corridor.  Site atoms and old points are the
checkpoint units.  Run on one low-priority thread only.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.util
import json
import math
import mmap
import os
import resource
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_CENSUS = ROOT / "design" / "lattice_t_projective_spectrum_census.py"
SALVAGE_GATE = ROOT / "design" / "salvage_gate.py"
DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L5-primary.json")
DEFAULT_AUDIT_SUMMARY = ROOT / "design" / "lattice-T-chronological-L5-summary.json"
DEFAULT_DOMAIN_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_DOMAIN_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_CHECKPOINT = Path("/tmp/lattice-T-L5-L6-birth-shell-mask-checkpoint.json")
DEFAULT_OUTPUT = ROOT / "design" / "lattice-T-L5-L6-birth-shell-mask-summary.json"
L5_STATE = ROOT / "gate2-l7-construction-L5.pkl"

EXPECTED_FROZEN_CENSUS_SHA256 = (
    "034744d9b5da4e3ffd4147bbaf0bf123cc620943bf3337bc0070a6f427edf48b"
)
EXPECTED_SALVAGE_GATE_SHA256 = (
    "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
)
EXPECTED_DEPENDENCY_SHA256 = {
    "gate_run.py": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "fast_legal.py": "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed",
    "search193.py": "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc",
    "amplify_rich.py": "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e",
    "imbricate193.py": "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb",
}
EXPECTED_SOURCE_SHA256 = (
    "9c711e396dc75042b747a1bcacb5093aa8b4c84c316a89081b2e246bdae0c2b8"
)
EXPECTED_SOURCE_BYTES = 5_369_433
EXPECTED_AUDIT_SUMMARY_SHA256 = (
    "88fa0f41674d71cc9cf84fc1bd4b70949ab91cd1e8d83a435bb7b6bec5fc9df5"
)
EXPECTED_AUDIT_SUMMARY_BYTES = 3_061
EXPECTED_L5_STATE_SHA256 = (
    "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
)
EXPECTED_DOMAIN_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_DOMAIN_METADATA_BYTES = 45_693
EXPECTED_DOMAIN_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_DOMAIN_CACHE_BYTES = 68_050_680
EXPECTED_CACHE_MAGIC = b"NOXLN001"

EXPECTED_POINTS = 8_268
EXPECTED_ANCHORS = 2_458
EXPECTED_GAPS = 2_457
SCHEMA_VERSION = 1
M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
LOCAL_RADIUS = 40
MAX_PROBE_DOMAIN_WORDS = 50_000
LATEST_QUARTER_FIRST_RANK = 3 * EXPECTED_GAPS // 4
MIN_SELECTED_WORD_LENGTH = 4
CHANNEL_PRIORITY = ("collision", "old-old-new", "old-new-new")
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
DEFAULT_MAX_UNITS = 10_000
HARD_MAX_UNITS = 20_000
SAVE_UNIT_INTERVAL = 64
PROCESS_START_CHECKER_SHA256 = None


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise ValueError("zero vector has no primitive direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def chebyshev(left, right):
    return max(abs(a - b) for a, b in zip(left, right))


def midpoint(left, right):
    return tuple((a + b) // 2 for a, b in zip(left, right))


def spatial_shell(distance):
    """D40 shell: 0 for d<=40, then ceilings 120,360,... ."""
    if distance <= LOCAL_RADIUS:
        return 0
    shell = 1
    ceiling = 3 * LOCAL_RADIUS
    while distance > ceiling:
        shell += 1
        ceiling *= 3
    return shell


def rank_shell(distance):
    """Rank shell 0 for distance 0; j>=1 for 3^(j-1)<=d<3^j."""
    if distance < 0:
        raise ValueError("negative rank distance")
    if distance == 0:
        return 0
    shell = 1
    ceiling = 3
    while distance >= ceiling:
        shell += 1
        ceiling *= 3
    return shell


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce=True):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError("run requires thread controls=1 and nice>=15")
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
        raise RuntimeError("birth/shell checker changed during run")


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


def stable_file_snapshot(path, expected_sha256, expected_bytes=None):
    path = Path(path).resolve()
    before = path.stat()
    if expected_bytes is not None and before.st_size != expected_bytes:
        raise AssertionError("pinned file byte-size drift", str(path))
    observed = file_sha256(path)
    after = path.stat()
    identity_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, field) for field in identity_fields) != tuple(
        getattr(after, field) for field in identity_fields
    ):
        raise RuntimeError("input changed while being hashed", str(path))
    if observed != expected_sha256:
        raise AssertionError("pinned file digest drift", str(path), observed)
    return {
        "path": str(path),
        "sha256": observed,
        "bytes": after.st_size,
    }


def load_python_module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_authoritative_modules():
    snapshots = {
        "frozen_census": stable_file_snapshot(
            FROZEN_CENSUS, EXPECTED_FROZEN_CENSUS_SHA256
        ),
        "salvage_gate": stable_file_snapshot(
            SALVAGE_GATE, EXPECTED_SALVAGE_GATE_SHA256
        ),
    }
    for relative, expected in EXPECTED_DEPENDENCY_SHA256.items():
        snapshots[relative] = stable_file_snapshot(ROOT / relative, expected)
    frozen = load_python_module(
        FROZEN_CENSUS, "frozen_lattice_t_projective_spectrum_census"
    )
    if frozen.PROCESS_START_CHECKER_SHA256 != EXPECTED_FROZEN_CENSUS_SHA256:
        raise AssertionError("frozen census self-hash drift")
    salvage = load_python_module(SALVAGE_GATE, "pinned_salvage_gate")
    return frozen, salvage, snapshots


def verify_domain_inputs(metadata_path, cache_path):
    metadata_snapshot = stable_file_snapshot(
        metadata_path,
        EXPECTED_DOMAIN_METADATA_SHA256,
        EXPECTED_DOMAIN_METADATA_BYTES,
    )
    cache_snapshot = stable_file_snapshot(
        cache_path, EXPECTED_DOMAIN_CACHE_SHA256, EXPECTED_DOMAIN_CACHE_BYTES
    )
    with Path(metadata_path).open() as handle:
        metadata = json.load(handle)
    if metadata["checker"]["sha256"] != (
        "6eca827ef7b6a4dfad57554bb89156fff79c2f495e89ba33e166aebbba21fffd"
    ):
        raise AssertionError("domain metadata producer drift")
    compact = metadata["compact_domain_cache"]
    if compact["sha256"] != EXPECTED_DOMAIN_CACHE_SHA256 or compact[
        "bytes"
    ] != EXPECTED_DOMAIN_CACHE_BYTES:
        raise AssertionError("domain metadata/cache join drift")
    blocks = {record["step"]: record for record in compact["blocks"]}
    if set(blocks) != set(range(124)):
        raise AssertionError("domain cache block census drift")
    if stable_hash([blocks[step] for step in sorted(blocks)]) != compact[
        "block_metadata_sha256"
    ]:
        raise AssertionError("domain block metadata commitment drift")
    with Path(cache_path).open("rb") as handle:
        if handle.read(len(EXPECTED_CACHE_MAGIC)) != EXPECTED_CACHE_MAGIC:
            raise AssertionError("domain cache magic drift")
    return blocks, metadata_snapshot, cache_snapshot


def load_domain(cache, block):
    cursor = block["start"]
    end = block["end"]
    digest = hashlib.sha256()
    words = []
    for ordinal in range(1, block["words"] + 1):
        if cursor >= end:
            raise AssertionError("truncated domain block", block["step"], ordinal)
        length = cache[cursor]
        record_end = cursor + 1 + length
        if record_end > end:
            raise AssertionError("truncated domain word", block["step"], ordinal)
        encoded = bytes(cache[cursor:record_end])
        digest.update(encoded)
        word = tuple(encoded[1:])
        if len(word) != length or not word:
            raise AssertionError("domain word encoding drift")
        words.append(word)
        cursor = record_end
    if cursor != end or digest.hexdigest() != block["encoded_block_sha256"]:
        raise AssertionError("domain block commitment drift", block["step"])
    return tuple(words)


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def selected_words_by_gap(source):
    words = [None] * EXPECTED_GAPS
    ranks = [None] * EXPECTED_GAPS
    records = [None] * EXPECTED_GAPS
    for rank, record in enumerate(source["selection_records"]):
        gap = record["gap"]
        if words[gap] is not None or record["construction_rank"] != rank:
            raise AssertionError("selection record order/gap drift")
        words[gap] = tuple(record["selected_word"])
        ranks[gap] = rank
        records[gap] = record
    if any(word is None for word in words):
        raise AssertionError("incomplete selected-word map")
    return tuple(words), tuple(ranks), tuple(records)


def natural_l5_path(frozen, anchors, words, ranks):
    points = [anchors[0]]
    provenance = [{
        "stable_id": "L5:A0",
        "birth_kind": "seed-anchor",
        "birth_rank": -1,
        "birth_gap": None,
        "interior_slot": None,
        "natural_path_index": 0,
    }]
    child_start_by_gap = []
    for gap, word in enumerate(words):
        child_start_by_gap.append(len(points) - 1)
        interiors = frozen.word_interiors(anchors[gap], word)
        for slot, point in enumerate(interiors):
            points.append(point)
            provenance.append({
                "stable_id": f"L5:G{gap}:I{slot}",
                "birth_kind": "connector-interior",
                "birth_rank": ranks[gap],
                "birth_gap": gap,
                "interior_slot": slot,
                "natural_path_index": len(points) - 1,
            })
        points.append(anchors[gap + 1])
        provenance.append({
            "stable_id": f"L5:A{gap + 1}",
            "birth_kind": "seed-anchor",
            "birth_rank": -1,
            "birth_gap": None,
            "interior_slot": None,
            "natural_path_index": len(points) - 1,
        })
    if len(points) != EXPECTED_POINTS or len(points) != len(set(points)):
        raise AssertionError("natural L5 path point census drift")
    return tuple(points), tuple(provenance), tuple(child_start_by_gap)


def choose_parent_probe(source, words, records, blocks):
    candidates = []
    for rank, chronological in enumerate(source["selection_records"]):
        if rank < LATEST_QUARTER_FIRST_RANK:
            continue
        gap = chronological["gap"]
        word = words[gap]
        if len(word) < MIN_SELECTED_WORD_LENGTH:
            continue
        steps = (chronological["step"], *word)
        sizes = tuple(blocks[step]["words"] for step in steps)
        if max(sizes) > MAX_PROBE_DOMAIN_WORDS:
            continue
        if chronological["domain_words"] != sizes[0]:
            raise AssertionError("source/domain metadata size drift", gap)
        candidates.append({
            "rank": rank,
            "gap": gap,
            "word": list(word),
            "source_step": chronological["step"],
            "domain_sizes_source_then_slots": list(sizes),
            "maximum_domain_size": max(sizes),
        })
    if not candidates:
        raise AssertionError("poison-blind probe rule selected no parent")
    winner = min(candidates, key=lambda item: (
        -len(item["word"]),
        item["maximum_domain_size"],
        -item["rank"],
        item["gap"],
    ))
    return winner, {
        "rule": (
            "among L5 ranks in the latest quarter with selected length>=4 "
            "and source/every-child domain<=50000, maximize selected length, "
            "then minimize the maximum domain, then maximize construction rank, "
            "then minimize gap"
        ),
        "candidate_count": len(candidates),
        "poison_results_consulted": False,
        "winner": winner,
    }


def l5_prefix_points(frozen, anchors, source, parent_rank):
    points = list(anchors)
    provenance = [{
        "stable_id": f"L5:A{index}",
        "birth_kind": "seed-anchor",
        "birth_rank": -1,
        "birth_gap": None,
        "interior_slot": None,
    } for index in range(len(anchors))]
    for rank, record in enumerate(source["selection_records"][:parent_rank]):
        for slot, point in enumerate(frozen.word_interiors(
            anchors[record["gap"]], tuple(record["selected_word"])
        )):
            points.append(point)
            provenance.append({
                "stable_id": f"L5:G{record['gap']}:I{slot}",
                "birth_kind": "connector-interior",
                "birth_rank": rank,
                "birth_gap": record["gap"],
                "interior_slot": slot,
            })
    if len(points) != len(provenance) or len(points) != len(set(points)):
        raise AssertionError("L5 prefix point-set drift")
    return tuple(points), tuple(provenance)


def build_probe_panel(frozen, source, blocks):
    parent_word, anchors, schedule, state_sha = frozen.load_l5_state()
    if state_sha != EXPECTED_L5_STATE_SHA256:
        raise AssertionError("L5 state pin drift")
    words, ranks, records = selected_words_by_gap(source)
    natural_points, natural_provenance, child_starts = natural_l5_path(
        frozen, anchors, words, ranks
    )
    parent, selection_rule = choose_parent_probe(source, words, records, blocks)
    gap = parent["gap"]
    rank = parent["rank"]
    if schedule[rank] != gap or parent_word[gap] != parent["source_step"]:
        raise AssertionError("chosen parent schedule/step drift")
    l5_points, l5_provenance = l5_prefix_points(
        frozen, anchors, source, rank
    )
    l6_points = tuple(apply_matrix(M, point) for point in natural_points)
    if len(l6_points) != len(set(l6_points)):
        raise AssertionError("induced L6 anchors repeat")
    l6_provenance = tuple({
        **record,
        "stable_id": "inherited:" + record["stable_id"],
        "induced_current_kind": "L6-anchor-from-completed-L5-point",
    } for record in natural_provenance)

    probes = [{
        "probe_id": f"L5-parent-G{gap}-R{rank}",
        "level": 5,
        "kind": "chronological-L5-parent-prefix",
        "step": parent_word[gap],
        "start": list(anchors[gap]),
        "end": list(anchors[gap + 1]),
        "point_set": "L5-prefix",
        "parent_gap": gap,
        "parent_rank": rank,
        "actual_selected_parent_word": list(words[gap]),
        "selected_parent_ordinal_1_based": records[gap][
            "first_survivor_ordinal_1_based"
        ],
        "parent_slot": None,
        "parent_prefix": None,
        "child_cursor": None,
    }]
    prefix = (0, 0, 0)
    for slot, letter in enumerate(words[gap]):
        start = apply_matrix(M, add(anchors[gap], prefix))
        next_prefix = add(prefix, frozen.MENU[letter])
        end = apply_matrix(M, add(anchors[gap], next_prefix))
        probes.append({
            "probe_id": f"L6-child-of-G{gap}-S{slot}",
            "level": 6,
            "kind": "induced-L6-owner-descendant-frame",
            "step": letter,
            "start": list(start),
            "end": list(end),
            "point_set": "induced-L6-anchors",
            "parent_gap": gap,
            "parent_rank": rank,
            "actual_selected_parent_word": list(words[gap]),
            "selected_parent_ordinal_1_based": records[gap][
                "first_survivor_ordinal_1_based"
            ],
            "parent_slot": slot,
            "parent_prefix": list(prefix),
            "child_cursor": child_starts[gap] + slot,
        })
        prefix = next_prefix
    if add(anchors[gap], prefix) != anchors[gap + 1]:
        raise AssertionError("selected parent word endpoint drift")

    for probe in probes:
        if blocks[probe["step"]]["words"] > MAX_PROBE_DOMAIN_WORDS:
            raise AssertionError("probe domain cap drift")
        probe["domain_words"] = blocks[probe["step"]]["words"]
        probe["domain_block_sha256"] = blocks[probe["step"]][
            "encoded_block_sha256"
        ]
    point_sets = {
        "L5-prefix": (l5_points, l5_provenance),
        "induced-L6-anchors": (l6_points, l6_provenance),
    }
    point_set_commitments = {
        name: {
            "points": len(points),
            "point_stream_sha256": point_stream_sha256(points),
            "provenance_stream_sha256": stable_hash(provenance),
        }
        for name, (points, provenance) in point_sets.items()
    }
    return tuple(probes), point_sets, selection_rule, point_set_commitments


def build_inputs(args):
    frozen, salvage, module_snapshots = load_authoritative_modules()
    source_file_snapshot = stable_file_snapshot(
        args.source, EXPECTED_SOURCE_SHA256, EXPECTED_SOURCE_BYTES
    )
    audit_file_snapshot = stable_file_snapshot(
        args.audit_summary,
        EXPECTED_AUDIT_SUMMARY_SHA256,
        EXPECTED_AUDIT_SUMMARY_BYTES,
    )
    _audit, audit_snapshot = frozen.verify_terminal_audit_summary(
        args.audit_summary
    )
    source, source_snapshot = frozen.load_source(args.source)
    if source_snapshot["sha256"] != source_file_snapshot["sha256"]:
        raise AssertionError("source double-snapshot drift")
    reconstructed, provenance, interior_counts, state_sha = (
        frozen.reconstruct_points(source)
    )
    if len(reconstructed) != EXPECTED_POINTS or state_sha != (
        EXPECTED_L5_STATE_SHA256
    ):
        raise AssertionError("audited path reconstruction drift")
    blocks, metadata_snapshot, cache_snapshot = verify_domain_inputs(
        args.domain_metadata, args.domain_cache
    )
    probes, point_sets, selection_rule, point_set_commitments = (
        build_probe_panel(frozen, source, blocks)
    )
    static = {
        "schema_version": SCHEMA_VERSION,
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "authoritative_modules": module_snapshots,
        "source_checkpoint": source_snapshot,
        "source_file_snapshot": source_file_snapshot,
        "terminal_audit_summary": audit_snapshot,
        "terminal_audit_file_snapshot": audit_file_snapshot,
        "domain_metadata": metadata_snapshot,
        "domain_cache": cache_snapshot,
        "L5_state_sha256": state_sha,
        "construction_order_point_stream_sha256": frozen.point_stream_sha256(
            reconstructed
        ),
        "construction_order_provenance_sha256": frozen.provenance_commitment(
            provenance
        ),
        "interior_count_stream_sha256": stable_hash(interior_counts),
        "probe_selection": selection_rule,
        "probe_records": list(probes),
        "probe_record_stream_sha256": stable_hash(probes),
        "point_sets": point_set_commitments,
        "local_radius": LOCAL_RADIUS,
        "spatial_shell_definition": (
            "shell 0 is Chebyshev distance<=40 from the integer corridor "
            "midpoint; shell j>=1 has 40*3^(j-1)<distance<=40*3^j"
        ),
        "birth_rank_shell_definition": (
            "shell 0 is rank distance 0; shell j>=1 has "
            "3^(j-1)<=rank distance<3^j"
        ),
        "channel_priority": list(CHANNEL_PRIORITY),
    }
    static["static_state_sha256"] = stable_hash(static)
    return static, {
        "frozen": frozen,
        "salvage": salvage,
        "blocks": blocks,
        "probes": probes,
        "point_sets": point_sets,
        "domain_cache": Path(args.domain_cache),
    }


def mask_hash(bits, size):
    return hashlib.sha256(
        bits.to_bytes((size + 7) // 8, "little")
    ).hexdigest()


def mask_commitment(bits, size):
    return {
        "members": bits.bit_count(),
        "mask_sha256": mask_hash(bits, size),
        "bit_order": "index i is bit (i mod 8) of byte floor(i/8)",
    }


def hex_mask(bits):
    return format(bits, "x")


def unhex_mask(encoded):
    return int(encoded, 16) if encoded else 0


def endpoint_birth_profile(provenance, parent_rank, distance):
    birth_rank = provenance["birth_rank"]
    if birth_rank == -1:
        relation = "seed-anchor"
        delta = None
        shell = "seed"
    elif birth_rank < parent_rank:
        relation = "L5-before-owner"
        delta = parent_rank - birth_rank
        shell = rank_shell(delta)
    elif birth_rank == parent_rank:
        relation = "L5-owner-word"
        delta = 0
        shell = 0
    else:
        relation = "L5-after-owner"
        delta = birth_rank - parent_rank
        shell = rank_shell(delta)
    return {
        "stable_id": provenance["stable_id"],
        "birth_kind": provenance["birth_kind"],
        "birth_rank": birth_rank,
        "birth_gap": provenance["birth_gap"],
        "interior_slot": provenance["interior_slot"],
        "owner_relation": relation,
        "owner_rank_distance": delta,
        "birth_rank_shell": shell,
        "exact_spatial_distance": distance,
        "spatial_shell": spatial_shell(distance),
    }


def descriptor_endpoint(profile):
    return {
        "owner_relation": profile["owner_relation"],
        "birth_rank_shell": profile["birth_rank_shell"],
        "spatial_shell": profile["spatial_shell"],
    }


def descriptor_and_witness(channel, atom, profiles, exact_geometry):
    profiles = tuple(sorted(profiles, key=lambda item: item["stable_id"]))
    endpoint_descriptors = sorted(
        (descriptor_endpoint(profile) for profile in profiles),
        key=canonical_bytes,
    )
    maximum_shell = max(profile["spatial_shell"] for profile in profiles)
    descriptor = {
        "channel": channel,
        "locality": "near/local" if maximum_shell == 0 else "far-involved",
        "maximum_spatial_shell": maximum_shell,
        "endpoint_birth_shell_profiles": endpoint_descriptors,
    }
    if channel == "old-old-new":
        latest = max(profile["birth_rank"] for profile in profiles)
        latest_profiles = [
            profile for profile in profiles if profile["birth_rank"] == latest
        ]
        descriptor["secant_birth_cohorts"] = sorted({
            profile["owner_relation"] for profile in latest_profiles
        })
        descriptor["secant_birth_rank_shells"] = sorted(
            {profile["birth_rank_shell"] for profile in latest_profiles},
            key=str,
        )
    key = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
    witness = {
        "channel": channel,
        "atom_id": atom,
        "descriptor_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
        "endpoints": profiles,
        "exact_geometry": exact_geometry,
    }
    return key, descriptor, witness


def initial_accumulator():
    return {
        "full_atom_mask": 0,
        "near_atom_mask": 0,
        "far_atom_mask": 0,
        "channel_atom_masks": {channel: 0 for channel in CHANNEL_PRIORITY},
        "descriptor_atom_masks": {},
        "descriptor_records": {},
        "witness_count": 0,
        "witness_hash_chain": "0" * 64,
    }


def decode_accumulator(active):
    stored = active["accumulator"]
    return {
        "full_atom_mask": unhex_mask(stored["full_atom_mask"]),
        "near_atom_mask": unhex_mask(stored["near_atom_mask"]),
        "far_atom_mask": unhex_mask(stored["far_atom_mask"]),
        "channel_atom_masks": {
            key: unhex_mask(value)
            for key, value in stored["channel_atom_masks"].items()
        },
        "descriptor_atom_masks": {
            key: unhex_mask(value)
            for key, value in stored["descriptor_atom_masks"].items()
        },
        "descriptor_records": stored["descriptor_records"],
        "witness_count": stored["witness_count"],
        "witness_hash_chain": stored["witness_hash_chain"],
    }


def encode_accumulator(accumulator):
    return {
        "full_atom_mask": hex_mask(accumulator["full_atom_mask"]),
        "near_atom_mask": hex_mask(accumulator["near_atom_mask"]),
        "far_atom_mask": hex_mask(accumulator["far_atom_mask"]),
        "channel_atom_masks": {
            key: hex_mask(value)
            for key, value in accumulator["channel_atom_masks"].items()
        },
        "descriptor_atom_masks": {
            key: hex_mask(value)
            for key, value in accumulator["descriptor_atom_masks"].items()
        },
        "descriptor_records": accumulator["descriptor_records"],
        "witness_count": accumulator["witness_count"],
        "witness_hash_chain": accumulator["witness_hash_chain"],
    }


def record_witness(accumulator, atom, descriptor_key, descriptor, witness):
    bit = 1 << atom
    accumulator["full_atom_mask"] |= bit
    channel = descriptor["channel"]
    accumulator["channel_atom_masks"][channel] |= bit
    if descriptor["locality"] == "near/local":
        accumulator["near_atom_mask"] |= bit
    else:
        accumulator["far_atom_mask"] |= bit
    accumulator["descriptor_atom_masks"][descriptor_key] = (
        accumulator["descriptor_atom_masks"].get(descriptor_key, 0) | bit
    )
    previous = accumulator["descriptor_records"].setdefault(
        descriptor_key, descriptor
    )
    if previous != descriptor:
        raise AssertionError("descriptor key collision")
    accumulator["witness_count"] += 1
    accumulator["witness_hash_chain"] = hash_chain(
        accumulator["witness_hash_chain"], witness
    )


def point_profiles(points, provenance, parent_rank, corridor_midpoint):
    if len(points) != len(provenance):
        raise AssertionError("point/provenance length drift")
    distances = [chebyshev(point, corridor_midpoint) for point in points]
    profiles = [
        endpoint_birth_profile(record, parent_rank, distance)
        for record, distance in zip(provenance, distances)
    ]
    return tuple(distances), tuple(profiles)


def scan_site_unit(model, start, points, profiles, site_record, accumulator):
    offset, atom = site_record
    candidate = add(start, offset)
    seen = {}
    for point_index, point in enumerate(points):
        if point == candidate:
            key, descriptor, witness = descriptor_and_witness(
                "collision", atom, (profiles[point_index],), {
                    "candidate_site": list(candidate),
                    "candidate_offset": list(offset),
                    "old_point_id": point_index,
                },
            )
            record_witness(accumulator, atom, key, descriptor, witness)
            continue
        direction = primitive(subtract(point, candidate))
        previous = seen.get(direction)
        if previous is None:
            seen[direction] = point_index
            continue
        if isinstance(previous, tuple):
            raise AssertionError("placed point set contains three collinear points")
        seen[direction] = (previous, point_index)
        key, descriptor, witness = descriptor_and_witness(
            "old-old-new", atom,
            (profiles[previous], profiles[point_index]), {
                "candidate_site": list(candidate),
                "candidate_offset": list(offset),
                "old_point_ids": [previous, point_index],
                "primitive_secant_direction": list(direction),
            },
        )
        record_witness(accumulator, atom, key, descriptor, witness)


def scan_old_point_unit(model, start, points, profiles, point_index,
                        directions, accumulator):
    relative = subtract(points[point_index], start)
    for direction, by_moment in directions:
        moment = cross(relative, direction)
        atom = by_moment.get(moment)
        if atom is None:
            continue
        key, descriptor, witness = descriptor_and_witness(
            "old-new-new", atom, (profiles[point_index],), {
                "old_point_id": point_index,
                "old_point_relative_to_corridor": list(relative),
                "candidate_line_primitive_direction": list(direction),
                "candidate_line_moment": list(moment),
            },
        )
        record_witness(accumulator, atom, key, descriptor, witness)


def atom_mask_to_word_mask(atom_mask, atom_word_bits):
    result = 0
    remaining = atom_mask
    while remaining:
        lowest = remaining & -remaining
        atom = lowest.bit_length() - 1
        result |= atom_word_bits[atom]
        remaining ^= lowest
    return result


def build_atom_word_bits(model, domain_size):
    result = [0] * len(model["atom_desc"])
    for word_index, atoms in enumerate(model["word_atoms"]):
        bit = 1 << word_index
        for atom in atoms:
            result[atom] |= bit
    if len(model["word_atoms"]) != domain_size:
        raise AssertionError("domain/model word census drift")
    return result


def mask_pair_record(left, right, size):
    return {
        "left_and_right": mask_commitment(left & right, size),
        "left_only": mask_commitment(left & ~right, size),
        "right_only": mask_commitment(right & ~left, size),
        "left_or_right": mask_commitment(left | right, size),
    }


def provenance_histogram(provenance, parent_rank, distances):
    counts = defaultdict(int)
    for record, distance in zip(provenance, distances):
        profile = endpoint_birth_profile(record, parent_rank, distance)
        key = json.dumps({
            "owner_relation": profile["owner_relation"],
            "birth_rank_shell": profile["birth_rank_shell"],
            "spatial_shell": profile["spatial_shell"],
        }, sort_keys=True, separators=(",", ":"))
        counts[key] += 1
    return [
        {"profile": json.loads(key), "placed_points": count}
        for key, count in sorted(counts.items())
    ]


def finalize_probe(probe, model, domain, points, provenance, distances,
                   accumulator):
    atom_count = len(model["atom_desc"])
    domain_size = len(domain)
    atom_word_bits = build_atom_word_bits(model, domain_size)
    descriptor_records = []
    descriptor_atom_union = 0
    descriptor_word_union = 0
    for key in sorted(accumulator["descriptor_atom_masks"]):
        atom_bits = accumulator["descriptor_atom_masks"][key]
        word_bits = atom_mask_to_word_mask(atom_bits, atom_word_bits)
        descriptor_atom_union |= atom_bits
        descriptor_word_union |= word_bits
        descriptor = accumulator["descriptor_records"][key]
        descriptor_records.append({
            "descriptor": descriptor,
            "descriptor_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
            "poisoned_atom_membership": mask_commitment(atom_bits, atom_count),
            "killed_word_membership": mask_commitment(word_bits, domain_size),
        })
    full_atom = accumulator["full_atom_mask"]
    if descriptor_atom_union != full_atom:
        raise AssertionError("descriptor atom OR does not equal full poison")
    full_word = atom_mask_to_word_mask(full_atom, atom_word_bits)
    if descriptor_word_union != full_word:
        raise AssertionError("descriptor word OR does not equal full poison")

    near_atom = accumulator["near_atom_mask"]
    far_atom = accumulator["far_atom_mask"]
    if near_atom | far_atom != full_atom:
        raise AssertionError("near/far atom OR does not equal full poison")
    near_word = atom_mask_to_word_mask(near_atom, atom_word_bits)
    far_word = atom_mask_to_word_mask(far_atom, atom_word_bits)
    if near_word | far_word != full_word:
        raise AssertionError("near/far word OR does not equal full poison")

    channel_words = {
        channel: atom_mask_to_word_mask(
            accumulator["channel_atom_masks"][channel], atom_word_bits
        )
        for channel in CHANNEL_PRIORITY
    }
    channel_union = 0
    priority_records = []
    for channel in CHANNEL_PRIORITY:
        membership = channel_words[channel]
        exclusive = membership & ~channel_union
        channel_union |= membership
        priority_records.append({
            "channel": channel,
            "overlapping_membership": mask_commitment(membership, domain_size),
            "priority_only_remainder": mask_commitment(exclusive, domain_size),
            "cumulative_OR": mask_commitment(channel_union, domain_size),
        })
    if channel_union != full_word:
        raise AssertionError("channel OR does not equal full poison")
    channel_intersections = []
    for left_index, left in enumerate(CHANNEL_PRIORITY):
        for right in CHANNEL_PRIORITY[left_index + 1:]:
            channel_intersections.append({
                "channels": [left, right],
                **mask_pair_record(
                    channel_words[left], channel_words[right], domain_size
                ),
            })

    selected = None
    if probe["level"] == 5:
        ordinal = probe["selected_parent_ordinal_1_based"]
        expected_word = tuple(probe["actual_selected_parent_word"])
        if not 1 <= ordinal <= domain_size or domain[ordinal - 1] != expected_word:
            raise AssertionError("selected source ordinal/domain drift")
        selected = {
            "ordinal_1_based": ordinal,
            "word": list(expected_word),
            "killed_by_exact_full_mask": bool(full_word & (1 << (ordinal - 1))),
        }
        if selected["killed_by_exact_full_mask"]:
            raise AssertionError("audited selected L5 word is killed")

    descriptor_expression = [
        {
            "descriptor_sha256": record["descriptor_sha256"],
            "poisoned_atom_membership": record["poisoned_atom_membership"],
            "killed_word_membership": record["killed_word_membership"],
        }
        for record in descriptor_records
    ]
    return {
        "probe": probe,
        "placed_points": len(points),
        "placed_point_birth_shell_spatial_shell_histogram": (
            provenance_histogram(provenance, probe["parent_rank"], distances)
        ),
        "domain": {
            "words": domain_size,
            "candidate_site_atoms": len(model["site_id"]),
            "candidate_line_atoms": len(model["line_id"]),
            "atom_universe": atom_count,
            "atom_universe_sha256": stable_hash(model["atom_desc"]),
            "word_atom_incidence_sha256": stable_hash(model["word_atoms"]),
        },
        "exact_full_killed_word_mask": mask_commitment(full_word, domain_size),
        "exact_surviving_words": domain_size - full_word.bit_count(),
        "selected_L5_action": selected,
        "near_far_overlap_aware_OR": {
            "semantics": (
                "near and far are overlapping any-witness memberships; "
                "near-only and far-only are exact bitwise remainders"
            ),
            "near_membership": mask_commitment(near_word, domain_size),
            "far_membership": mask_commitment(far_word, domain_size),
            "near_and_far": mask_commitment(near_word & far_word, domain_size),
            "near_only": mask_commitment(near_word & ~far_word, domain_size),
            "far_only": mask_commitment(far_word & ~near_word, domain_size),
            "near_OR_far": mask_commitment(near_word | far_word, domain_size),
        },
        "channel_overlap_aware_OR": {
            "priority_order": list(CHANNEL_PRIORITY),
            "priority_partition": priority_records,
            "pairwise_intersections_and_remainders": channel_intersections,
        },
        "correlated_birth_shell_descriptor_masks": {
            "overlap_semantics": (
                "each descriptor is an exact membership mask; descriptors "
                "may share atoms and words, and only their bitwise OR equals "
                "the full mask"
            ),
            "descriptor_count": len(descriptor_records),
            "descriptor_records": descriptor_records,
            "canonical_OR_expression_sha256": stable_hash(
                descriptor_expression
            ),
            "OR_equals_full_atom_mask": True,
            "OR_equals_full_killed_word_mask": True,
        },
        "exact_witness_stream": {
            "witness_records": accumulator["witness_count"],
            "ordered_hash_chain_sha256": accumulator["witness_hash_chain"],
            "records_stored_individually": False,
        },
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


def initial_checkpoint(static):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "next_probe_index": 0,
        "active_probe": None,
        "completed_probe_results": [],
        "terminal_summary": None,
        "last_run": None,
    }


def initialize_active_probe(probe_index, probe):
    return {
        "probe_index": probe_index,
        "probe_id": probe["probe_id"],
        "phase": "sites",
        "next_unit_index": 0,
        "accumulator": encode_accumulator(initial_accumulator()),
    }


def validate_checkpoint(checkpoint, static):
    if checkpoint["schema_version"] != SCHEMA_VERSION or checkpoint[
        "static"
    ] != static:
        raise AssertionError("checkpoint static/schema drift")
    next_probe = checkpoint["next_probe_index"]
    results = checkpoint["completed_probe_results"]
    probes = static["probe_records"]
    if not 0 <= next_probe <= len(probes) or len(results) != next_probe:
        raise AssertionError("checkpoint probe cursor drift")
    for index, result in enumerate(results):
        if result["probe"]["probe_id"] != probes[index]["probe_id"]:
            raise AssertionError("checkpoint result/probe order drift")
    active = checkpoint["active_probe"]
    if active is not None:
        if next_probe == len(probes):
            raise AssertionError("terminal checkpoint has active probe")
        if active["probe_index"] != next_probe or active["probe_id"] != (
            probes[next_probe]["probe_id"]
        ):
            raise AssertionError("active probe identity drift")
        if active["phase"] not in {"sites", "old-new-new"}:
            raise AssertionError("active probe phase drift")
        if active["next_unit_index"] < 0:
            raise AssertionError("negative active unit cursor")
        decoded = decode_accumulator(active)
        if set(decoded["channel_atom_masks"]) != set(CHANNEL_PRIORITY):
            raise AssertionError("active channel mask key drift")
        if set(decoded["descriptor_atom_masks"]) != set(
            decoded["descriptor_records"]
        ):
            raise AssertionError("active descriptor map drift")
    if checkpoint["status"] == "complete":
        if next_probe != len(probes) or active is not None:
            raise AssertionError("complete checkpoint cursor drift")
    elif checkpoint["status"] != "partial":
        raise AssertionError("unknown checkpoint status")


def load_checkpoint(path, static):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(static)
    with path.open() as handle:
        checkpoint = json.load(handle)
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(checkpoint):
        raise AssertionError("checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    validate_checkpoint(checkpoint, static)
    return checkpoint


def terminal_payload(checkpoint, policy):
    static = checkpoint["static"]
    results = checkpoint["completed_probe_results"]
    if checkpoint["status"] != "complete" or len(results) != len(
        static["probe_records"]
    ):
        raise AssertionError("terminal payload requested before completion")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": (
            "exact finite realized-path L5-to-induced-L6 birth/shell mask "
            "panel; evidence only"
        ),
        "checker": {
            "path": "design/lattice_t_birth_shell_mask_experiment.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "inputs": {
            key: static[key]
            for key in (
                "authoritative_modules",
                "source_checkpoint",
                "terminal_audit_summary",
                "domain_metadata",
                "domain_cache",
                "L5_state_sha256",
            )
        },
        "scope": {
            "probe_selection": static["probe_selection"],
            "probe_records": static["probe_records"],
            "point_sets": static["point_sets"],
            "local_radius": static["local_radius"],
            "spatial_shell_definition": static["spatial_shell_definition"],
            "birth_rank_shell_definition": static[
                "birth_rank_shell_definition"
            ],
            "channels": list(CHANNEL_PRIORITY),
            "all_probe_domains_complete": True,
            "all_relevant_placed_points_scanned": True,
            "endpoint_or_distance_cutoff": None,
        },
        "probe_results": results,
        "commitments": {
            "static_state_sha256": static["static_state_sha256"],
            "probe_result_stream_sha256": stable_hash(results),
            "probe_record_stream_sha256": static[
                "probe_record_stream_sha256"
            ],
            "construction_order_point_stream_sha256": static[
                "construction_order_point_stream_sha256"
            ],
        },
        "interpretation": {
            "proved_finite_facts": [
                "every reported mask is an exact bitwise OR over complete collision, old-old-new, and old-new-new witness scans",
                "birth/shell descriptor masks are overlapping memberships and are never summed as disjoint contributions",
                "every L6 frame is the actual child cursor determined by the audited selected L5 word, slot, and prefix",
            ],
            "not_proved": [
                "availability for any untested L5 corridor or any chronological L6 prefix",
                "that the selected L5 word would be chosen by a greatest-fixed-point policy",
                "stabilization of masks or transitions beyond this one finite parent/child panel",
                "a uniform far-secant tail, contraction, or positive connector-survivor lemma",
                "an unconditional infinite construction or Erdos #193 theorem",
            ],
        },
    }
    payload["payload_sha256"] = stable_hash(payload)
    return payload


def load_probe_domain_and_model(cache, context, probe):
    block = context["blocks"][probe["step"]]
    domain = load_domain(cache, block)
    if len(domain) != probe["domain_words"]:
        raise AssertionError("probe domain size drift")
    model = context["salvage"].build_domain_model(domain)
    return domain, model


def active_probe_geometry(context, probe):
    points, provenance = context["point_sets"][probe["point_set"]]
    center = midpoint(tuple(probe["start"]), tuple(probe["end"]))
    distances, profiles = point_profiles(
        points, provenance, probe["parent_rank"], center
    )
    return points, provenance, distances, profiles


def synchronize_active_accumulator(checkpoint, accumulator):
    checkpoint["active_probe"]["accumulator"] = encode_accumulator(accumulator)


def run_chunk(args):
    started = time.monotonic()
    deadline = started + args.max_seconds
    policy = resource_policy(enforce=True)
    static, context = build_inputs(args)
    checkpoint = load_checkpoint(args.checkpoint, static)
    if checkpoint["status"] == "complete":
        return checkpoint, {
            "units_processed_this_run": 0,
            "stop_reason": "terminal-checkpoint-already-present",
        }
    units = 0
    units_since_save = 0
    completed_this_run = 0
    stop_reason = "unit-limit"
    with context["domain_cache"].open("rb") as cache_handle:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            while checkpoint["next_probe_index"] < len(context["probes"]):
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
                probe_index = checkpoint["next_probe_index"]
                probe = context["probes"][probe_index]
                if checkpoint["active_probe"] is None:
                    checkpoint["active_probe"] = initialize_active_probe(
                        probe_index, probe
                    )
                active = checkpoint["active_probe"]
                accumulator = decode_accumulator(active)
                domain, model = load_probe_domain_and_model(
                    cache, context, probe
                )
                points, provenance, distances, profiles = (
                    active_probe_geometry(context, probe)
                )
                site_records = tuple(sorted(model["site_id"].items()))
                directions = tuple(sorted(model["line_by_direction"].items()))
                while units < args.max_units:
                    if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
                        raise MemoryError("280-MiB birth/shell resident limit exceeded")
                    if time.monotonic() >= deadline:
                        stop_reason = "time-limit"
                        break
                    if active["phase"] == "sites":
                        cursor = active["next_unit_index"]
                        if cursor == len(site_records):
                            active["phase"] = "old-new-new"
                            active["next_unit_index"] = 0
                            continue
                        if cursor > len(site_records):
                            raise AssertionError("site unit cursor drift")
                        scan_site_unit(
                            model, tuple(probe["start"]), points, profiles,
                            site_records[cursor], accumulator,
                        )
                        active["next_unit_index"] += 1
                    else:
                        cursor = active["next_unit_index"]
                        if cursor == len(points):
                            break
                        if cursor > len(points):
                            raise AssertionError("old-point unit cursor drift")
                        scan_old_point_unit(
                            model, tuple(probe["start"]), points, profiles,
                            cursor, directions, accumulator,
                        )
                        active["next_unit_index"] += 1
                    units += 1
                    units_since_save += 1
                    if units_since_save >= SAVE_UNIT_INTERVAL:
                        synchronize_active_accumulator(checkpoint, accumulator)
                        save_checkpoint(args.checkpoint, checkpoint)
                        active = checkpoint["active_probe"]
                        units_since_save = 0
                probe_complete = (
                    active["phase"] == "old-new-new"
                    and active["next_unit_index"] == len(points)
                )
                if probe_complete:
                    result = finalize_probe(
                        probe, model, domain, points, provenance, distances,
                        accumulator,
                    )
                    checkpoint["completed_probe_results"].append(result)
                    checkpoint["next_probe_index"] += 1
                    checkpoint["active_probe"] = None
                    completed_this_run += 1
                    save_checkpoint(args.checkpoint, checkpoint)
                    units_since_save = 0
                    del result
                else:
                    synchronize_active_accumulator(checkpoint, accumulator)
                del accumulator, domain, model, points, provenance, distances, profiles
                gc.collect()
                if stop_reason == "time-limit" or units >= args.max_units:
                    break
            if checkpoint["next_probe_index"] == len(context["probes"]):
                checkpoint["status"] = "complete"
                stop_reason = "full-panel-complete"
        finally:
            cache.close()
    validate_checkpoint(checkpoint, static)
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
        "units_processed_this_run": units,
        "probes_completed_this_run": completed_this_run,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
        "resource_policy": policy,
    }
    save_checkpoint(args.checkpoint, checkpoint)
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > HARD_MAX_SECONDS or resident > MAX_RESIDENT_BYTES:
        raise RuntimeError("birth/shell experiment resource bound exceeded")
    return checkpoint, {
        "units_processed_this_run": units,
        "probes_completed_this_run": completed_this_run,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
    }


def self_check():
    frozen, salvage, snapshots = load_authoritative_modules()
    if spatial_shell(40) != 0 or spatial_shell(41) != 1:
        raise AssertionError("D40 shell boundary drift")
    if spatial_shell(120) != 1 or spatial_shell(121) != 2:
        raise AssertionError("3-adic spatial shell boundary drift")
    expected_rank_shells = {0: 0, 1: 1, 2: 1, 3: 2, 8: 2, 9: 3}
    if {value: rank_shell(value) for value in expected_rank_shells} != (
        expected_rank_shells
    ):
        raise AssertionError("birth-rank shell boundary drift")
    vectors = ((3, -6, 9), (-3, 6, -9), (0, 4, 2))
    for vector in vectors:
        if primitive(vector) != salvage.primitive(vector):
            raise AssertionError("primitive direction disagrees with authority")
    if cross((1, 2, 3), (4, 5, 6)) != salvage.cross(
        (1, 2, 3), (4, 5, 6)
    ):
        raise AssertionError("cross product disagrees with authority")
    synthetic_domain = ((0, 1, 2), (0, 2, 1), (3, 4, 5, 6))
    model = salvage.build_domain_model(synthetic_domain)
    if len(model["word_atoms"]) != len(synthetic_domain):
        raise AssertionError("synthetic domain model drift")
    atom_word_bits = build_atom_word_bits(model, len(synthetic_domain))
    all_atoms = (1 << len(model["atom_desc"])) - 1
    if atom_mask_to_word_mask(all_atoms, atom_word_bits) != (
        (1 << len(synthetic_domain)) - 1
    ):
        raise AssertionError("synthetic atom-to-word OR drift")
    accumulator = initial_accumulator()
    encoded = encode_accumulator(accumulator)
    active = {"accumulator": encoded}
    if decode_accumulator(active) != accumulator:
        raise AssertionError("accumulator codec drift")
    if frozen.MENU != tuple(salvage.MENU):
        raise AssertionError("authoritative menu drift")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "large_inputs_opened": False,
        "authoritative_module_pins_verified": len(snapshots),
        "spatial_shell_boundaries_checked": 4,
        "birth_rank_shell_boundaries_checked": len(expected_rank_shells),
        "primitive_cross_geometry_crosschecked": True,
        "synthetic_overlap_OR_checked": True,
        "checkpoint_accumulator_codec_checked": True,
    }


def preflight(args):
    started = time.monotonic()
    policy = resource_policy(enforce=True)
    static, context = build_inputs(args)
    checkpoint = load_checkpoint(args.checkpoint, static)
    model_census = {}
    with context["domain_cache"].open("rb") as cache_handle:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for step in sorted({probe["step"] for probe in context["probes"]}):
                synthetic_probe = next(
                    probe for probe in context["probes"] if probe["step"] == step
                )
                domain, model = load_probe_domain_and_model(
                    cache, context, synthetic_probe
                )
                model_census[str(step)] = {
                    "domain_words": len(domain),
                    "site_atoms": len(model["site_id"]),
                    "line_atoms": len(model["line_id"]),
                    "line_directions": len(model["line_by_direction"]),
                    "atom_universe": len(model["atom_desc"]),
                    "atom_universe_sha256": stable_hash(model["atom_desc"]),
                    "word_atom_incidence_sha256": stable_hash(
                        model["word_atoms"]
                    ),
                }
                del domain, model
                gc.collect()
        finally:
            cache.close()
    work = []
    total_units = 0
    total_site_endpoint_tests = 0
    total_oldnew_moment_lookups = 0
    for probe in context["probes"]:
        census = model_census[str(probe["step"])]
        point_count = static["point_sets"][probe["point_set"]]["points"]
        units = census["site_atoms"] + point_count
        site_tests = census["site_atoms"] * point_count
        line_lookups = census["line_directions"] * point_count
        total_units += units
        total_site_endpoint_tests += site_tests
        total_oldnew_moment_lookups += line_lookups
        work.append({
            "probe_id": probe["probe_id"],
            "step": probe["step"],
            "placed_points": point_count,
            "checkpoint_units": units,
            "site_endpoint_direction_tests": site_tests,
            "old_new_new_moment_lookups": line_lookups,
        })
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > MAX_WORK_SECONDS or resident > MAX_RESIDENT_BYTES:
        raise RuntimeError("preflight resource bound exceeded")
    return {
        "status": "ready; exact domains modeled and zero witness units scanned",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "source_sha256": static["source_checkpoint"]["sha256"],
        "terminal_audit_sha256": static["terminal_audit_summary"]["sha256"],
        "static_state_sha256": static["static_state_sha256"],
        "scope": {
            "probe_selection": static["probe_selection"],
            "probe_records": static["probe_records"],
            "point_sets": static["point_sets"],
            "model_census_by_step": model_census,
        },
        "work_estimate": {
            "per_probe": work,
            "checkpoint_units": total_units,
            "unit_cap_chunks": math.ceil(total_units / DEFAULT_MAX_UNITS),
            "site_endpoint_direction_tests": total_site_endpoint_tests,
            "old_new_new_moment_lookups": total_oldnew_moment_lookups,
            "warning": (
                "wall-time may split into more chunks; this estimate counts "
                "exact loop operations, not calibrated seconds"
            ),
        },
        "checkpoint_status": checkpoint["status"],
        "completed_probes_in_checkpoint": checkpoint["next_probe_index"],
        "witness_units_scanned_by_preflight": 0,
        "resource_policy": policy,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
    }


def estimate():
    return {
        "status": "no source, cache, construction pickle, or checkpoint opened",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "selection_scope": (
            "one poison-blind late L5 parent plus every actual selected-word "
            "slot as an induced L6 owner-descendant corridor"
        ),
        "maximum_domain_words_per_probe": MAX_PROBE_DOMAIN_WORDS,
        "default_max_checkpoint_units_per_run": DEFAULT_MAX_UNITS,
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "hard_maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "full_scan_launched": False,
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
    parser.add_argument(
        "--domain-metadata", default=str(DEFAULT_DOMAIN_METADATA)
    )
    parser.add_argument("--domain-cache", default=str(DEFAULT_DOMAIN_CACHE))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=float, default=MAX_WORK_SECONDS)
    parser.add_argument("--max-units", type=int, default=DEFAULT_MAX_UNITS)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= MAX_WORK_SECONDS:
        raise ValueError("max-seconds outside (0,110]")
    if not 1 <= args.max_units <= HARD_MAX_UNITS:
        raise ValueError("max-units outside [1,20000]")
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
            "completed_probes": checkpoint["next_probe_index"],
            "total_probes": len(checkpoint["static"]["probe_records"]),
            "active_probe": checkpoint["active_probe"],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": file_sha256(args.checkpoint),
            "terminal_summary": checkpoint["terminal_summary"],
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
