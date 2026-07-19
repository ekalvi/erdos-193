#!/usr/bin/env python3
"""Exact realized cursor-jump injection probe for the universal x-core.

The full-domain Bellman certificate proves exterior invariance only while one
x-parallel line is transported synchronously from a parent corridor to one of
its ordered children.  The chronological stitch cursor instead jumps between
unrelated corridor anchors.  If consecutive anchors have lateral difference
``delta``, then the same absolute x-line changes relative coordinate by the
translation

    z_successor = z_predecessor - delta,

with no factor-three expansion.  This checker measures that missing channel
exactly on the pinned L5--L8 realized constructions.

For each of the recorded gate order, inherited-tile pipeline order, and
left-to-right gap order, anchors are initially present.  At a transition from
cursor r to r+1 the complete recorded connector at r is inserted, and the
placed inventory is projected onto cursor r+1's exact promoted universal
integer core.  The checker records:

* exact lateral cursor translation and base-three distance shell;
* absolute overlap of the predecessor and successor universal cores;
* capped point occupancy and active x-lines in the two cores;
* points and active x-lines in the successor core but geometrically outside
  the predecessor core;
* anchor/current-interior, birth/activation age, inherited-tile owner radius,
  and base-three address-shell decompositions of those injections.

Exact congruence tables test whether bounded ordered/tile phase, optionally
augmented by the complete predecessor-core occupancy, determines the injected
mask.  A strongest observed key also retains the exact cursor translation.
Noncongruence refutes that key on the finite sample; congruence does not prove
future closure.  Singleton classes provide no transition evidence.

This is an x-parallel, realized-path diagnostic.  It does not prove a global
tail lemma, non-x closure, collision closure, connector availability, or an
unconditional theorem.

Low-priority single-thread commands from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_cursor_jump_injection.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_cursor_jump_injection.py sample \
        --sample-level 8 --sample-transitions 2000 \
        --output /tmp/x-axis-cursor-jump-sample.json

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_cursor_jump_injection.py run \
        --output /tmp/x-axis-cursor-jump-injection-canonical.json
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import pickle
import sys
import tempfile
import time
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEVELS = tuple(range(5, 9))
ORDER_NAMES = ("gate", "pipeline", "left-to-right")
FRAGILE_CUT = 2000
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MENU = tuple(
    (x, y, z)
    for x, y, z in product(range(-2, 3), repeat=3)
    if (x, y, z) != (0, 0, 0)
)
EXPECTED_GAPS = {5: 2457, 6: 8213, 7: 27696, 8: 92731}
EXPECTED_UNIVERSAL_RAW = Path(
    "/tmp/x-axis-universal-bellman-canonical.json"
)
EXPECTED_UNIVERSAL_RAW_SHA256 = (
    "9028a2872e5e0530d329e983652eec8c6d2f3391c8f24bd99e81b1708da69275"
)
EXPECTED_UNIVERSAL_CHECKER_SHA256 = (
    "cd16f5600747b168a3deeb7c6d74164e9463fed6889054f5a39227a42b731bb7"
)
EXPECTED_INPUT_SHA256 = {
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
    ),
    "gate2-l7-construction-L5.pkl": (
        "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
    ),
    "gate2-l7-construction-L6.pkl": (
        "70fa3baac057492fb8ad325eba5417bdc1e98fbd474bec37dc5f5465230f9298"
    ),
    "gate2-l7-construction-L7.pkl": (
        "304e71eb74939662c0d0251864193171e74f49fd2023a98df09dc45d99fa0660"
    ),
    "gate2-l7-construction-L8.pkl": (
        "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141"
    ),
    "gate2-ledger-L5.json": (
        "c8ccd4ff6716eba29d58f2de0541e6f5a43d27badf6fcdb1aaf0954069858bc8"
    ),
}
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
PHASE_ADDRESS_MODULI = (1, 9, 81)
EXAMPLE_LIMIT = 12


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def as_json(value):
    if isinstance(value, tuple):
        return [as_json(item) for item in value]
    if isinstance(value, list):
        return [as_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_json(item) for key, item in value.items()}
    return value


def stable_bytes(value):
    return json.dumps(
        as_json(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def apply_matrix(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def sub(first, second):
    return tuple(first[axis] - second[axis] for axis in range(3))


def lateral(point):
    return point[1], point[2]


def add2(first, second):
    return first[0] + second[0], first[1] + second[1]


def sub2(first, second):
    return first[0] - second[0], first[1] - second[1]


def cheb2(vector):
    return max(abs(vector[0]), abs(vector[1]))


def base3_shell(distance):
    """0 for zero; j>=1 is the least j with distance <= 3^(j-1)."""
    if distance < 0:
        raise ValueError("negative distance")
    if distance == 0:
        return 0
    shell = 1
    ceiling = 1
    while distance > ceiling:
        shell += 1
        ceiling *= 3
    return shell


def clipped_signed(value, cutoff=2):
    if value < -cutoff:
        return "far-left"
    if value > cutoff:
        return "far-right"
    return value


def clipped_base3_shell(distance, cutoff=6):
    shell = base3_shell(distance)
    return shell if shell < cutoff else f"{cutoff}+"


def integer_mask_sha256(value, bits):
    if value < 0:
        raise ValueError("negative bit mask")
    size = (bits + 7) // 8
    raw = value.to_bytes(size, "little")
    if bits % 8 and raw and raw[-1] >> (bits % 8):
        raise AssertionError("mask exceeds declared bit width")
    return hashlib.sha256(raw).hexdigest()


def hist(counter):
    return dict(sorted(
        ((str(key), value) for key, value in counter.items()),
        key=lambda item: item[0],
    ))


def deep_size_bytes(root):
    """Exact reachable Python heap size for the small sample tracker graph."""
    seen = set()
    stack = [root]
    total = 0
    while stack:
        value = stack.pop()
        identity = id(value)
        if identity in seen:
            continue
        seen.add(identity)
        total += sys.getsizeof(value)
        if isinstance(value, dict):
            stack.extend(value.keys())
            stack.extend(value.values())
        elif isinstance(value, (list, tuple, set, frozenset)):
            stack.extend(value)
        elif hasattr(value, "__dict__"):
            stack.append(value.__dict__)
    return total


def enforce_resource_policy():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so checker assertions remain active")
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "every thread-cap environment variable must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process priority")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise RuntimeError(
            "run at low priority with nice -n 15 (minimum accepted nice is 10)"
        )
    return {
        "processes": 1,
        "thread_cap": 1,
        "minimum_nice": 10,
        "observed_nice": priority,
    }


def validate_inputs(universal_path):
    commitments = {}
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        digest = file_sha256(ROOT / relative)
        if digest != expected:
            raise RuntimeError(
                f"input hash drift for {relative}: {digest} != {expected}"
            )
        commitments[relative] = digest
    digest = file_sha256(universal_path)
    if digest != EXPECTED_UNIVERSAL_RAW_SHA256:
        raise RuntimeError(
            "universal Bellman raw artifact hash drift: "
            f"{digest} != {EXPECTED_UNIVERSAL_RAW_SHA256}"
        )
    commitments["universal_bellman_raw"] = digest
    checker = file_sha256(ROOT / "design/x_axis_universal_bellman.py")
    if checker != EXPECTED_UNIVERSAL_CHECKER_SHA256:
        raise RuntimeError("universal Bellman checker hash drift")
    commitments["design/x_axis_universal_bellman.py"] = checker
    return commitments


def load_universal_core(universal_path):
    with universal_path.open() as handle:
        raw = json.load(handle)
    if raw["checker_sha256"] != EXPECTED_UNIVERSAL_CHECKER_SHA256:
        raise AssertionError("universal raw/checker commitment mismatch")
    records = raw["finite_integer_core"]["step_records"]
    if len(records) != len(MENU):
        raise AssertionError("universal core does not cover every step")
    core_by_step = {}
    index_by_step = {}
    for record in records:
        step = record["step"]
        core = tuple(
            tuple(offset)
            for offset in (
                record["inner_core_integer_yz"]
                + record["bellman_interval_fringe_integer_yz"]
            )
        )
        if len(core) != record["outer_promoted_core_count"]:
            raise AssertionError("promoted core cardinality drift", step)
        if len(core) != len(set(core)):
            raise AssertionError("duplicate promoted core offset", step)
        core_by_step[step] = core
        index_by_step[step] = {offset: index for index, offset in enumerate(core)}
    if set(core_by_step) != set(range(len(MENU))):
        raise AssertionError("universal core step set drift")
    scans = {record["step"]: record for record in raw["domain_step_scans"]}
    if set(scans) != set(core_by_step):
        raise AssertionError("universal domain scan step set drift")
    return raw, core_by_step, index_by_step, scans


def reconstruct_d24_sizes(scans):
    """Recover D2--4 sizes without unpickling the 74 MB domain menu.

    The small pinned L5 ledger covers 118/124 steps, including every fragile
    step.  Nonfragile effective domains equal D2--4.  Missing ledger steps are
    required to have the universal artifact's D2-4-only layer.
    """
    with (ROOT / "gate2-ledger-L5.json").open() as handle:
        ledger = json.load(handle)
    observed = defaultdict(set)
    observed_effective = defaultdict(set)
    for record in ledger:
        observed[record["step"]].add(record["d24"])
        observed_effective[record["step"]].add(record["dstar"])
    if any(len(values) != 1 for values in observed.values()):
        raise AssertionError("ledger has noncongruent D2--4 sizes by step")
    if any(len(values) != 1 for values in observed_effective.values()):
        raise AssertionError("ledger has noncongruent effective sizes by step")

    d24 = {}
    for step, scan in scans.items():
        effective = scan["domain_words"]
        if step in observed:
            size = next(iter(observed[step]))
            if next(iter(observed_effective[step])) != effective:
                raise AssertionError("ledger/universal effective-size drift", step)
        else:
            if scan["layer"] != "D2-4-only":
                raise AssertionError("missing ledger step is fragile", step)
            size = effective
        if size >= FRAGILE_CUT:
            if scan["layer"] != "D2-4-only" or size != effective:
                raise AssertionError("nonfragile domain layer drift", step)
        else:
            if scan["layer"] != "sorted-D2-4-plus-appended-D5":
                raise AssertionError("fragile domain layer drift", step)
            if not size < effective:
                raise AssertionError("fragile domain did not gain D5 words", step)
        d24[step] = size
    if set(d24) != set(range(len(MENU))):
        raise AssertionError("D2--4 size reconstruction is incomplete")
    fragile = {step for step, size in d24.items() if size < FRAGILE_CUT}
    if len(fragile) != 18 or not fragile <= set(observed):
        raise AssertionError("fragile D2--4 step census drift")
    return d24, {
        "ledger_steps": len(observed),
        "universal_only_nonfragile_steps": len(MENU) - len(observed),
        "fragile_steps": len(fragile),
        "d24_size_stream_sha256": stable_hash(sorted(d24.items())),
    }


def load_state(level):
    with (ROOT / f"gate2-l7-construction-L{level}.pkl").open("rb") as handle:
        state = pickle.load(handle)
    if len(state["parent_word"]) != EXPECTED_GAPS[level]:
        raise AssertionError("construction gap count drift", level)
    return state


def exact_births_through_level4(viz):
    births = [0] * len(viz["levels"][0]["points"])
    for level in range(1, 5):
        parents = viz["levels"][level]["parents"]
        points = [tuple(point) for point in viz["levels"][level]["points"]]
        old_points = [
            tuple(point) for point in viz["levels"][level - 1]["points"]
        ]
        next_births = []
        for index, parent in enumerate(parents):
            first = index == 0 or parents[index - 1] != parent
            if first:
                if points[index] != apply_matrix(M_BAL3, old_points[parent]):
                    raise AssertionError("viz anchor ancestry drift", level, index)
                next_births.append(births[parent])
            else:
                next_births.append(level)
        births = next_births
    return births


def tile_layout(level, state, viz):
    parents = viz["levels"][level - 1]["parents"]
    if len(parents) != len(state["anchors"]):
        raise AssertionError("tile parent/anchor count drift", level)
    if len(state["parent_word"]) + 1 != len(parents):
        raise AssertionError("tile gap/anchor count drift", level)
    if any(first > second for first, second in zip(parents, parents[1:])):
        raise AssertionError("tile parents are not monotone", level)

    tile_gaps = defaultdict(list)
    for gap in range(len(state["parent_word"])):
        tile_gaps[parents[gap]].append(gap)
    tile_gaps = {
        tile: tuple(gaps) for tile, gaps in sorted(tile_gaps.items())
    }
    if tuple(tile_gaps) != tuple(range(len(tile_gaps))):
        raise AssertionError("inherited tile indices are not contiguous")
    for gaps in tile_gaps.values():
        if tuple(range(gaps[0], gaps[-1] + 1)) != gaps:
            raise AssertionError("inherited tile gaps are not contiguous")

    last_tile = len(tile_gaps) - 1
    anchor_owners = []
    for index, tile in enumerate(parents):
        boundary = index == 0 or parents[index - 1] != tile
        if boundary:
            choices = {tile}
            if tile > 0:
                choices.add(tile - 1)
            choices = {owner for owner in choices if 0 <= owner <= last_tile}
        else:
            choices = {min(tile, last_tile)}
        anchor_owners.append(tuple(sorted(choices)))
    return tile_gaps, anchor_owners


def pipeline_schedule(state, tile_gaps, d24):
    guards = {}
    for tile, gaps in tile_gaps.items():
        fragile = [
            gap for gap in gaps
            if d24[state["parent_word"][gap]] < FRAGILE_CUT
        ]
        if fragile:
            guards[tile] = min(
                fragile,
                key=lambda gap: (d24[state["parent_word"][gap]], gap),
            )
    entries = []
    placed = set()

    def place(gap, sweep_tile, phase):
        if gap in placed:
            return
        entries.append({
            "gap": gap,
            "sweep_tile": sweep_tile,
            "phase": phase,
        })
        placed.add(gap)

    if 0 in guards:
        place(guards[0], 0, "bootstrap-guard")
    for tile, gaps in tile_gaps.items():
        if tile + 1 in guards:
            place(guards[tile + 1], tile, "next-tile-guard")
        for gap in sorted(
            gaps,
            key=lambda item: (d24[state["parent_word"][item]], item),
        ):
            place(gap, tile, "finish-current-tile")
    if len(entries) != len(state["parent_word"]):
        raise AssertionError("pipeline schedule length drift")
    if placed != set(range(len(state["parent_word"]))):
        raise AssertionError("pipeline schedule is not a permutation")
    return entries, guards


def connector_interiors(start, word):
    position = start
    interiors = []
    for ordinal, step in enumerate(word):
        if not 0 <= step < len(MENU):
            raise AssertionError("connector word has invalid step")
        position = add(position, MENU[step])
        if ordinal + 1 < len(word):
            interiors.append(position)
    return interiors, position


def build_level(level, parent_points, state, viz, d24):
    gaps = len(state["parent_word"])
    if set(state["words"]) != set(range(gaps)):
        raise AssertionError("construction lacks one word per gap", level)
    if sorted(state["order"]) != list(range(gaps)):
        raise AssertionError("gate order is not a permutation", level)
    expected_anchors = [
        apply_matrix(M_BAL3, point[0]) for point in parent_points
    ]
    if expected_anchors != [tuple(anchor) for anchor in state["anchors"]]:
        raise AssertionError("construction anchor/parent drift", level)

    tile_gaps, anchor_owners = tile_layout(level, state, viz)
    tile_of_gap = {
        gap: tile for tile, tile_members in tile_gaps.items()
        for gap in tile_members
    }
    gap_position = {
        gap: position for tile_members in tile_gaps.values()
        for position, gap in enumerate(tile_members)
    }
    records = []
    anchor_indices = []
    for index, ((coordinate, birth_level), owners) in enumerate(
        zip(zip(expected_anchors, (point[1] for point in parent_points)),
            anchor_owners)
    ):
        record_index = len(records)
        records.append({
            "coordinate": coordinate,
            "birth_level": birth_level,
            "current_birth_gap": None,
            "current_role": "anchor",
            "owner_options": owners,
            "anchor_index": index,
        })
        anchor_indices.append(record_index)

    interior_indices_by_gap = {}
    corridors = []
    completed_indices = [anchor_indices[0]]
    for gap in range(gaps):
        word = tuple(state["words"][gap])
        interiors, endpoint = connector_interiors(expected_anchors[gap], word)
        if endpoint != expected_anchors[gap + 1]:
            raise AssertionError("recorded connector endpoint drift", level, gap)
        expected_displacement = apply_matrix(
            M_BAL3, MENU[state["parent_word"][gap]]
        )
        if sub(endpoint, expected_anchors[gap]) != expected_displacement:
            raise AssertionError("corridor displacement drift", level, gap)
        indices = []
        tile = tile_of_gap[gap]
        for coordinate in interiors:
            record_index = len(records)
            records.append({
                "coordinate": coordinate,
                "birth_level": level,
                "current_birth_gap": gap,
                "current_role": "connector-interior",
                "owner_options": (tile,),
                "anchor_index": None,
            })
            indices.append(record_index)
        interior_indices_by_gap[gap] = tuple(indices)
        completed_indices.extend(indices)
        completed_indices.append(anchor_indices[gap + 1])
        tile_members = tile_gaps[tile]
        corridors.append({
            "level": level,
            "gap": gap,
            "step": state["parent_word"][gap],
            "anchor": expected_anchors[gap],
            "anchor_lateral": lateral(expected_anchors[gap]),
            "tile": tile,
            "gap_position_in_tile": gap_position[gap],
            "tile_size": len(tile_members),
            "tile_signature": tuple(
                state["parent_word"][item] for item in tile_members
            ),
            "d24_size": d24[state["parent_word"][gap]],
        })

    completed_coordinates = [records[index]["coordinate"] for index in completed_indices]
    if len(completed_coordinates) != len(set(completed_coordinates)):
        raise AssertionError("completed realized path repeats a point", level)
    viz_points = [tuple(point) for point in viz["levels"][level]["points"]]
    if completed_coordinates != viz_points:
        raise AssertionError("construction/viz completed path drift", level)
    completed_parent_points = [
        (records[index]["coordinate"], records[index]["birth_level"])
        for index in completed_indices
    ]
    pipeline_entries, guards = pipeline_schedule(state, tile_gaps, d24)
    return {
        "level": level,
        "records": records,
        "anchor_indices": tuple(anchor_indices),
        "interior_indices_by_gap": interior_indices_by_gap,
        "corridors": corridors,
        "tile_gaps": tile_gaps,
        "tile_of_gap": tile_of_gap,
        "pipeline_entries": pipeline_entries,
        "guards": guards,
        "gate_order": tuple(state["order"]),
        "completed_parent_points": completed_parent_points,
        "completed_points": len(completed_parent_points),
    }


def schedule_entries(order_name, level_data):
    gaps = len(level_data["corridors"])
    if order_name == "gate":
        raw_entries = [
            {"gap": gap, "sweep_tile": level_data["tile_of_gap"][gap],
             "phase": "gate-recorded"}
            for gap in level_data["gate_order"]
        ]
    elif order_name == "pipeline":
        raw_entries = level_data["pipeline_entries"]
    elif order_name == "left-to-right":
        raw_entries = [
            {"gap": gap, "sweep_tile": level_data["tile_of_gap"][gap],
             "phase": "left-to-right"}
            for gap in range(gaps)
        ]
    else:
        raise ValueError(order_name)
    order = [entry["gap"] for entry in raw_entries]
    if sorted(order) != list(range(gaps)):
        raise AssertionError("schedule is not a permutation", order_name)
    rank_by_gap = {gap: rank for rank, gap in enumerate(order)}
    local_seen = Counter()
    entries = []
    for rank, raw in enumerate(raw_entries):
        gap = raw["gap"]
        corridor = level_data["corridors"][gap]
        tile = corridor["tile"]
        entry = {
            **corridor,
            "rank": rank,
            "phase": raw["phase"],
            "sweep_tile": raw["sweep_tile"],
            "tile_action_ordinal": local_seen[tile],
            "is_tile_guard": level_data["guards"].get(tile) == gap,
        }
        local_seen[tile] += 1
        entries.append(entry)
    return entries, rank_by_gap


def owner_radius_and_side(owner_options, target_tile):
    distances = [(abs(owner - target_tile), owner - target_tile)
                 for owner in owner_options]
    radius = min(distance for distance, _signed in distances)
    signs = {
        0 if signed == 0 else 1 if signed > 0 else -1
        for distance, signed in distances if distance == radius
    }
    if signs == {0}:
        side = "same"
    elif signs == {-1}:
        side = "left"
    elif signs == {1}:
        side = "right"
    else:
        side = "boundary-tie"
    return radius, side


def joint_owner_radius(records, indices, target_tile):
    possibilities = [records[index]["owner_options"] for index in indices]
    best = None
    for assignment in product(*possibilities):
        radius = max(abs(owner - target_tile) for owner in assignment)
        best = radius if best is None else min(best, radius)
    if best is None:
        raise AssertionError("empty endpoint owner assignment")
    return best


def point_role(record, rank_by_gap, predecessor_rank):
    if record["current_role"] == "anchor":
        return "anchor"
    birth_rank = rank_by_gap[record["current_birth_gap"]]
    if birth_rank == predecessor_rank:
        return "just-inserted-current-interior"
    if birth_rank < predecessor_rank:
        return "older-current-interior"
    raise AssertionError("unplaced point appears in occupancy")


def local_phase_descriptor(entry):
    return (
        entry["step"], entry["phase"], entry["tile_signature"],
        entry["gap_position_in_tile"], entry["tile_size"],
        entry["tile_action_ordinal"], entry["is_tile_guard"],
        entry["d24_size"] < FRAGILE_CUT,
    )


def transition_code(level, predecessor_gap, successor_gap):
    if predecessor_gap >= (1 << 20) or successor_gap >= (1 << 20):
        raise AssertionError("transition code bit budget exceeded")
    return (level << 40) | (predecessor_gap << 20) | successor_gap


def decode_transition_code(code):
    return {
        "level": code >> 40,
        "predecessor_gap": (code >> 20) & ((1 << 20) - 1),
        "successor_gap": code & ((1 << 20) - 1),
    }


def target_fingerprint(target, successor_core_size):
    geometry, point_occupancy, active_lines = target
    return {
        "newly_exposed_geometry_sha256": integer_mask_sha256(
            geometry, successor_core_size
        ),
        "injected_capped_point_occupancy_sha256": integer_mask_sha256(
            point_occupancy, 2 * successor_core_size
        ),
        "injected_active_x_line_sha256": integer_mask_sha256(
            active_lines, successor_core_size
        ),
    }


class CongruenceTracker:
    """Exact state-key and target equality; hashes are output commitments."""

    def __init__(self, name):
        self.name = name
        self.entries = {}
        self.examples = []

    def update(self, key, target, level, code, successor_core_size):
        entry = self.entries.get(key)
        level_bit = 1 << (level - LEVELS[0])
        if entry is None:
            # count, first target, first-target levels, target map or None,
            # first transition code, all levels, successor core size.
            self.entries[key] = [
                1, target, level_bit, None, code, level_bit,
                successor_core_size,
            ]
            return
        entry[0] += 1
        entry[5] |= level_bit
        if target == entry[1]:
            entry[2] |= level_bit
            if entry[3] is not None:
                entry[3][target] |= level_bit
            return
        if entry[3] is None:
            entry[3] = {
                entry[1]: entry[2],
                target: level_bit,
            }
            if len(self.examples) < EXAMPLE_LIMIT:
                self.examples.append({
                    "first": decode_transition_code(entry[4]),
                    "different": decode_transition_code(code),
                    "first_target": target_fingerprint(
                        entry[1], entry[6]
                    ),
                    "different_target": target_fingerprint(
                        target, successor_core_size
                    ),
                })
        else:
            entry[3][target] = (
                entry[3].get(target, 0) | level_bit
            )

    @staticmethod
    def cross_level_noncongruent(target_levels):
        items = list(target_levels.items())
        for first_index, (_first_target, first_levels) in enumerate(items):
            for _second_target, second_levels in items[first_index + 1:]:
                for first_level in range(len(LEVELS)):
                    if not (first_levels >> first_level) & 1:
                        continue
                    if second_levels & ~(1 << first_level):
                        return True
                for second_level in range(len(LEVELS)):
                    if not (second_levels >> second_level) & 1:
                        continue
                    if first_levels & ~(1 << second_level):
                        return True
        return False

    def summarize(self):
        counts = Counter()
        class_stream = hashlib.sha256()
        maximum_targets = 1
        for key, entry in self.entries.items():
            repeated = entry[0] > 1
            noncongruent = entry[3] is not None
            target_count = (
                len(entry[3]) if noncongruent else 1
            )
            maximum_targets = max(maximum_targets, target_count)
            counts["classes"] += 1
            counts["occurrences"] += entry[0]
            counts["singleton_classes"] += not repeated
            counts["repeated_classes"] += repeated
            counts["congruent_repeated_classes"] += repeated and not noncongruent
            counts["noncongruent_classes"] += noncongruent
            counts["occurrences_in_noncongruent_classes"] += (
                entry[0] if noncongruent else 0
            )
            multi_level = entry[5].bit_count() > 1
            counts["multi_level_classes"] += multi_level
            counts["multi_level_congruent_classes"] += (
                multi_level and not noncongruent
            )
            cross_noncongruent = (
                noncongruent
                and self.cross_level_noncongruent(entry[3])
            )
            counts["cross_level_noncongruent_classes"] += cross_noncongruent
            compact = (
                stable_hash(key), entry[0], entry[5],
                target_count, noncongruent, cross_noncongruent,
            )
            class_stream.update(stable_bytes(compact))
            class_stream.update(b"\n")
        return {
            "representation": self.name,
            **dict(counts),
            "maximum_distinct_targets_in_one_class": maximum_targets,
            "class_stream_sha256": class_stream.hexdigest(),
            "class_stream_order": "first occurrence of each exact key",
            "first_noncongruence_examples": self.examples,
            "interpretation": (
                "noncongruence refutes this exact state key on L5--L8; "
                "congruence is finite evidence only; singleton classes have "
                "no repeated-transition evidence"
            ),
        }


def phase_key(predecessor, successor, jump, modulus, descriptors=None):
    tile_delta = successor["tile"] - predecessor["tile"]
    if descriptors is None:
        descriptors = (
            local_phase_descriptor(predecessor),
            local_phase_descriptor(successor),
        )
    return (
        "phase-only", modulus,
        descriptors[0], descriptors[1],
        clipped_signed(tile_delta),
        clipped_base3_shell(cheb2(jump)),
        predecessor["tile"] % modulus,
        successor["tile"] % modulus,
        predecessor["rank"] % modulus,
    )


def phase_occupancy_key(
    predecessor, successor, jump, modulus, prior_occupancy,
    descriptors=None,
):
    return (
        "phase-plus-prior-occupancy", modulus,
        phase_key(
            predecessor, successor, jump, modulus, descriptors
        ),
        prior_occupancy,
    )


def exact_jump_occupancy_key(
    predecessor, successor, jump, prior_occupancy, descriptors=None
):
    if descriptors is None:
        descriptors = (
            local_phase_descriptor(predecessor),
            local_phase_descriptor(successor),
        )
    return (
        "exact-jump-plus-prior-occupancy",
        descriptors[0], descriptors[1],
        jump,
        successor["tile"] - predecessor["tile"],
        prior_occupancy,
    )


def update_extreme(current, value, compact, prefer_max=True):
    if current is None:
        return {"value": value, "transition": compact}
    better = value > current["value"] if prefer_max else value < current["value"]
    return {"value": value, "transition": compact} if better else current


def analyze_order_level(
    order_name,
    level_data,
    core_by_step,
    index_by_step,
    trackers,
    transition_limit=None,
):
    level = level_data["level"]
    records = level_data["records"]
    entries, rank_by_gap = schedule_entries(order_name, level_data)
    occupancy = defaultdict(list)
    activation_rank = {}

    def insert(record_index, rank):
        cell = lateral(records[record_index]["coordinate"])
        bucket = occupancy[cell]
        if len(bucket) >= 2:
            raise AssertionError("three placed points on one x-line", level, cell)
        bucket.append(record_index)
        if len(bucket) == 2:
            activation_rank[cell] = rank

    for record_index in level_data["anchor_indices"]:
        insert(record_index, -1)

    first = entries[0]
    prior_counts = tuple(
        len(occupancy.get(add2(first["anchor_lateral"], offset), ()))
        for offset in core_by_step[first["step"]]
    )
    if any(count > 2 for count in prior_counts):
        raise AssertionError("initial core occupancy exceeds two")
    prior_occupancy = sum(
        count << (2 * index) for index, count in enumerate(prior_counts)
    )

    aggregate = Counter()
    jump_shells = Counter()
    tile_jump_shells = Counter()
    core_overlap_histogram = Counter()
    point_roles = Counter()
    point_birth_levels = Counter()
    point_birth_ages = Counter()
    point_action_ages = Counter()
    point_owner_shells = Counter()
    point_owner_sides = Counter()
    line_roles = Counter()
    line_birth_levels = Counter()
    line_birth_ages = Counter()
    line_activation_ages = Counter()
    line_owner_shells = Counter()
    jump_set = set()
    event_stream = hashlib.sha256()
    extremes = {
        "maximum_jump_chebyshev": None,
        "minimum_absolute_core_overlap": None,
        "maximum_injected_point_records": None,
        "maximum_injected_active_x_lines": None,
    }

    available = len(entries) - 1
    transitions = available if transition_limit is None else min(
        available, transition_limit
    )
    for predecessor_rank in range(transitions):
        predecessor = entries[predecessor_rank]
        successor = entries[predecessor_rank + 1]
        for record_index in level_data["interior_indices_by_gap"][
            predecessor["gap"]
        ]:
            insert(record_index, predecessor_rank)

        jump = sub2(successor["anchor_lateral"], predecessor["anchor_lateral"])
        jump_distance = cheb2(jump)
        tile_delta = successor["tile"] - predecessor["tile"]
        jump_set.add(jump)
        jump_shells[base3_shell(jump_distance)] += 1
        tile_jump_shells[base3_shell(abs(tile_delta))] += 1

        successor_core = core_by_step[successor["step"]]
        predecessor_index = index_by_step[predecessor["step"]]
        current_counts = []
        geometry_mask = 0
        injected_point_mask = 0
        injected_line_mask = 0
        overlap = 0
        occupied_overlap_from_prior = 0
        prior_point_records_in_overlap = 0
        current_occupied_cells = 0
        current_point_records = 0
        current_active_lines = 0
        injected_cells = 0
        injected_point_records = 0
        injected_lines = 0
        just_born_inside_overlap = 0

        for index, offset in enumerate(successor_core):
            absolute_cell = add2(successor["anchor_lateral"], offset)
            predecessor_relative = add2(offset, jump)
            predecessor_core_index = predecessor_index.get(predecessor_relative)
            inside_predecessor = predecessor_core_index is not None
            if inside_predecessor:
                overlap += 1
                prior_count = prior_counts[predecessor_core_index]
                if prior_count:
                    occupied_overlap_from_prior += 1
                    prior_point_records_in_overlap += prior_count
            else:
                geometry_mask |= 1 << index

            bucket = occupancy.get(absolute_cell, ())
            count = len(bucket)
            if count > 2:
                raise AssertionError("successor core occupancy exceeds two")
            current_counts.append(count)
            if count:
                current_occupied_cells += 1
                current_point_records += count
            if count == 2:
                current_active_lines += 1

            if inside_predecessor:
                for record_index in bucket:
                    record = records[record_index]
                    if (
                        record["current_role"] == "connector-interior"
                        and rank_by_gap[record["current_birth_gap"]]
                        == predecessor_rank
                    ):
                        just_born_inside_overlap += 1
                continue

            if count:
                injected_cells += 1
                injected_point_records += count
                injected_point_mask |= count << (2 * index)
                for record_index in bucket:
                    record = records[record_index]
                    role = point_role(record, rank_by_gap, predecessor_rank)
                    point_roles[role] += 1
                    point_birth_levels[record["birth_level"]] += 1
                    point_birth_ages[level - record["birth_level"]] += 1
                    if role == "anchor":
                        point_action_ages["initial"] += 1
                    else:
                        action_age = predecessor_rank - rank_by_gap[
                            record["current_birth_gap"]
                        ]
                        point_action_ages[action_age] += 1
                    radius, side = owner_radius_and_side(
                        record["owner_options"], successor["tile"]
                    )
                    point_owner_shells[base3_shell(radius)] += 1
                    point_owner_sides[side] += 1
            if count == 2:
                injected_lines += 1
                injected_line_mask |= 1 << index
                roles = tuple(sorted(
                    point_role(records[item], rank_by_gap, predecessor_rank)
                    for item in bucket
                ))
                line_roles[roles] += 1
                line_birth_level = max(
                    records[item]["birth_level"] for item in bucket
                )
                line_birth_levels[line_birth_level] += 1
                line_birth_ages[level - line_birth_level] += 1
                activation = activation_rank[absolute_cell]
                if activation < 0:
                    line_activation_ages["initial"] += 1
                else:
                    line_activation_ages[predecessor_rank - activation] += 1
                radius = joint_owner_radius(
                    records, bucket, successor["tile"]
                )
                line_owner_shells[base3_shell(radius)] += 1

        core_overlap_histogram[overlap] += 1
        current_occupancy = sum(
            count << (2 * index) for index, count in enumerate(current_counts)
        )
        target = (geometry_mask, injected_point_mask, injected_line_mask)
        code = transition_code(
            level, predecessor["gap"], successor["gap"]
        )
        descriptors = (
            local_phase_descriptor(predecessor),
            local_phase_descriptor(successor),
        )
        phase_only = phase_key(
            predecessor, successor, jump, 1, descriptors
        )
        trackers["phase-only-mod1"].update(
            phase_only, target, level, code, len(successor_core)
        )
        for modulus in (9, 81):
            tracker_name = f"phase-prior-occupancy-mod{modulus}"
            trackers[tracker_name].update(
                phase_occupancy_key(
                    predecessor, successor, jump, modulus,
                    prior_occupancy, descriptors,
                ),
                target, level, code, len(successor_core),
            )
        trackers["exact-jump-prior-occupancy"].update(
            exact_jump_occupancy_key(
                predecessor, successor, jump, prior_occupancy,
                descriptors,
            ),
            target, level, code, len(successor_core),
        )

        compact_transition = {
            "level": level,
            "predecessor_gap": predecessor["gap"],
            "successor_gap": successor["gap"],
            "predecessor_step": predecessor["step"],
            "successor_step": successor["step"],
            "lateral_cursor_jump": list(jump),
            "jump_chebyshev": jump_distance,
            "jump_base3_shell": base3_shell(jump_distance),
            "signed_tile_jump": tile_delta,
            "absolute_core_overlap": overlap,
            "successor_cells_outside_predecessor_core": (
                len(successor_core) - overlap
            ),
            "predecessor_core_size": len(core_by_step[predecessor["step"]]),
            "successor_core_size": len(successor_core),
            "prior_occupied_overlap_cells": occupied_overlap_from_prior,
            "prior_point_records_in_overlap": prior_point_records_in_overlap,
            "current_occupied_cells": current_occupied_cells,
            "current_point_records": current_point_records,
            "current_active_x_lines": current_active_lines,
            "injected_occupied_cells": injected_cells,
            "injected_point_records": injected_point_records,
            "injected_active_x_lines": injected_lines,
            "just_born_points_inside_core_overlap": just_born_inside_overlap,
            "target_masks": target_fingerprint(target, len(successor_core)),
        }
        event_stream.update(stable_bytes(compact_transition))
        event_stream.update(b"\n")

        aggregate["transitions"] += 1
        aggregate["successor_core_cells_scanned"] += len(successor_core)
        aggregate["absolute_core_overlap"] += overlap
        aggregate["successor_cells_outside_predecessor_core"] += (
            len(successor_core) - overlap
        )
        aggregate["prior_occupied_overlap_cells"] += occupied_overlap_from_prior
        aggregate["prior_point_records_in_overlap"] += prior_point_records_in_overlap
        aggregate["current_occupied_cells"] += current_occupied_cells
        aggregate["current_point_records"] += current_point_records
        aggregate["current_active_x_lines"] += current_active_lines
        aggregate["injected_occupied_cells"] += injected_cells
        aggregate["injected_point_records"] += injected_point_records
        aggregate["injected_active_x_lines"] += injected_lines
        aggregate["just_born_points_inside_core_overlap"] += just_born_inside_overlap
        aggregate["transitions_with_injected_points"] += injected_point_records > 0
        aggregate["transitions_with_injected_lines"] += injected_lines > 0
        aggregate["zero_lateral_cursor_jumps"] += jump == (0, 0)

        extremes["maximum_jump_chebyshev"] = update_extreme(
            extremes["maximum_jump_chebyshev"], jump_distance,
            compact_transition, True,
        )
        extremes["minimum_absolute_core_overlap"] = update_extreme(
            extremes["minimum_absolute_core_overlap"], overlap,
            compact_transition, False,
        )
        extremes["maximum_injected_point_records"] = update_extreme(
            extremes["maximum_injected_point_records"], injected_point_records,
            compact_transition, True,
        )
        extremes["maximum_injected_active_x_lines"] = update_extreme(
            extremes["maximum_injected_active_x_lines"], injected_lines,
            compact_transition, True,
        )
        prior_counts = tuple(current_counts)
        prior_occupancy = current_occupancy

    if transition_limit is None:
        last_rank = len(entries) - 1
        for record_index in level_data["interior_indices_by_gap"][
            entries[-1]["gap"]
        ]:
            insert(record_index, last_rank)
        if sum(len(bucket) for bucket in occupancy.values()) != len(records):
            raise AssertionError("schedule did not place every point", order_name, level)
        if max(map(len, occupancy.values()), default=0) > 2:
            raise AssertionError("completed x-line occupancy exceeds two")

    return {
        "level": level,
        "order": order_name,
        "gaps": len(entries),
        "transitions_available": available,
        "transitions_scanned": transitions,
        "completed_points": level_data["completed_points"],
        "aggregate": dict(aggregate),
        "jump": {
            "distinct_exact_lateral_translations": len(jump_set),
            "base3_chebyshev_shell_histogram": hist(jump_shells),
            "base3_absolute_tile_jump_shell_histogram": hist(tile_jump_shells),
        },
        "core_overlap_histogram": hist(core_overlap_histogram),
        "injected_point_decomposition": {
            "current_role": hist(point_roles),
            "birth_level": hist(point_birth_levels),
            "birth_age_levels": hist(point_birth_ages),
            "placement_action_age": hist(point_action_ages),
            "minimum_owner_base3_address_shell": hist(point_owner_shells),
            "nearest_owner_side": hist(point_owner_sides),
        },
        "injected_active_x_line_decomposition": {
            "endpoint_current_roles": hist(line_roles),
            "birth_level": hist(line_birth_levels),
            "birth_age_levels": hist(line_birth_ages),
            "activation_action_age": hist(line_activation_ages),
            "minimum_joint_owner_base3_address_shell": hist(line_owner_shells),
        },
        "extremes": extremes,
        "transition_event_stream_sha256": event_stream.hexdigest(),
    }


def merge_histograms(records, path):
    merged = Counter()
    for record in records:
        value = record
        for key in path:
            value = value[key]
        merged.update({key: count for key, count in value.items()})
    return dict(sorted(merged.items(), key=lambda item: item[0]))


def summarize_order(order_name, level_records, trackers):
    aggregate = Counter()
    for record in level_records:
        aggregate.update(record["aggregate"])
    return {
        "order": order_name,
        "levels": level_records,
        "aggregate": dict(aggregate),
        "injected_point_decomposition_all_levels": {
            "current_role": merge_histograms(
                level_records, ("injected_point_decomposition", "current_role")
            ),
            "birth_age_levels": merge_histograms(
                level_records, ("injected_point_decomposition", "birth_age_levels")
            ),
            "birth_level": merge_histograms(
                level_records, ("injected_point_decomposition", "birth_level")
            ),
            "placement_action_age": merge_histograms(
                level_records, ("injected_point_decomposition", "placement_action_age")
            ),
            "minimum_owner_base3_address_shell": merge_histograms(
                level_records,
                ("injected_point_decomposition", "minimum_owner_base3_address_shell"),
            ),
        },
        "injected_active_x_line_decomposition_all_levels": {
            "endpoint_current_roles": merge_histograms(
                level_records,
                ("injected_active_x_line_decomposition", "endpoint_current_roles"),
            ),
            "birth_age_levels": merge_histograms(
                level_records,
                ("injected_active_x_line_decomposition", "birth_age_levels"),
            ),
            "birth_level": merge_histograms(
                level_records,
                ("injected_active_x_line_decomposition", "birth_level"),
            ),
            "activation_action_age": merge_histograms(
                level_records,
                ("injected_active_x_line_decomposition", "activation_action_age"),
            ),
            "minimum_joint_owner_base3_address_shell": merge_histograms(
                level_records,
                ("injected_active_x_line_decomposition", "minimum_joint_owner_base3_address_shell"),
            ),
        },
        "state_representation_tests": {
            name: tracker.summarize() for name, tracker in trackers.items()
        },
    }


def new_trackers():
    names = [
        "phase-only-mod1",
        "phase-prior-occupancy-mod9",
        "phase-prior-occupancy-mod81",
        "exact-jump-prior-occupancy",
    ]
    return {name: CongruenceTracker(name) for name in names}


def base_parent_points(viz):
    births = exact_births_through_level4(viz)
    points = [tuple(point) for point in viz["levels"][4]["points"]]
    if len(points) != len(births):
        raise AssertionError("L4 birth vector length drift")
    return list(zip(points, births))


def exact_probe(
    universal_path,
    sample_level=None,
    sample_transitions=None,
):
    resource = enforce_resource_policy()
    inputs = validate_inputs(universal_path)
    started = time.time()
    raw, core_by_step, index_by_step, scans = load_universal_core(
        universal_path
    )
    d24, d24_audit = reconstruct_d24_sizes(scans)

    order_results = []
    for order_name in ORDER_NAMES:
        order_started = time.perf_counter()
        build_seconds = 0.0
        scan_seconds = 0.0
        with (ROOT / "viz/walk3d-data.json").open() as handle:
            viz = json.load(handle)
        trackers = new_trackers()
        parent_points = base_parent_points(viz)
        # Coordinates are now carried by exact point records.  Future tile
        # layouts use parent arrays, not these large viz point arrays.
        for old_level in range(5):
            viz["levels"][old_level]["points"] = None
        level_results = []
        planned_full_transitions = 0
        planned_full_successor_cells = 0
        for level in LEVELS:
            build_started = time.perf_counter()
            state = load_state(level)
            level_data = build_level(
                level, parent_points, state, viz, d24
            )
            del state
            build_seconds += time.perf_counter() - build_started
            parent_points = level_data["completed_parent_points"]
            viz["levels"][level]["points"] = None
            viz["levels"][level - 1]["parents"] = None
            planning_entries, _planning_rank = schedule_entries(
                order_name, level_data
            )
            planned_full_transitions += len(planning_entries) - 1
            planned_full_successor_cells += sum(
                len(core_by_step[entry["step"]])
                for entry in planning_entries[1:]
            )
            del planning_entries, _planning_rank
            if sample_level is None or sample_level == level:
                limit = sample_transitions if sample_level is not None else None
                print(
                    f"cursor-jump {order_name} L{level}: "
                    f"{min(EXPECTED_GAPS[level] - 1, limit) if limit is not None else EXPECTED_GAPS[level] - 1} transitions",
                    flush=True,
                )
                scan_started = time.perf_counter()
                level_result = analyze_order_level(
                    order_name, level_data, core_by_step, index_by_step,
                    trackers, limit,
                )
                level_scan_seconds = time.perf_counter() - scan_started
                scan_seconds += level_scan_seconds
                level_result["scan_elapsed_seconds"] = round(
                    level_scan_seconds, 6
                )
                level_results.append(level_result)
            del level_data
            gc.collect()
        tracker_classes = sum(
            len(tracker.entries) for tracker in trackers.values()
        )
        tracker_deep_size = (
            deep_size_bytes(trackers) if sample_level is not None else None
        )
        summary_started = time.perf_counter()
        order_result = summarize_order(
            order_name, level_results, trackers
        )
        summary_seconds = time.perf_counter() - summary_started
        order_result["timing"] = {
            "construction_and_validation_seconds": round(build_seconds, 6),
            "transition_scan_seconds": round(scan_seconds, 6),
            "congruence_summary_seconds": round(summary_seconds, 6),
            "total_order_seconds": round(
                time.perf_counter() - order_started, 6
            ),
        }
        order_result["tracker_memory_audit"] = {
            "exact_classes_retained": tracker_classes,
            "reachable_deep_size_bytes": tracker_deep_size,
            "sample_only_measurement": sample_level is not None,
        }
        order_result["planned_full_order_work"] = {
            "transitions": planned_full_transitions,
            "exact_successor_core_cells": planned_full_successor_cells,
        }
        order_results.append(order_result)
        del trackers, parent_points, viz
        gc.collect()

    transitions = sum(
        result["aggregate"].get("transitions", 0)
        for result in order_results
    )
    if sample_level is None:
        expected = len(ORDER_NAMES) * sum(
            gaps - 1 for gaps in EXPECTED_GAPS.values()
        )
        if transitions != expected:
            raise AssertionError("full transition census drift", transitions, expected)
    return {
        "status": (
            "exact realized L5--L8 universal x-core cursor-jump injection "
            "probe; not a global tail lemma, availability bound, or "
            "unconditional theorem"
        ),
        "mode": "sample" if sample_level is not None else "run",
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "universal_core_commitment": {
            "fixed_direction_statement": raw["proved_carried_line_theorem"],
            "total_promoted_integer_states": raw["finite_integer_core"][
                "total_outer_promoted_integer_states"
            ],
            "promoted_state_stream_sha256": raw["finite_integer_core"][
                "integer_core_stream_sha256"
            ],
        },
        "D2-4_size_reconstruction": d24_audit,
        "semantics": {
            "orders": list(ORDER_NAMES),
            "transition": (
                "anchors initially placed; insert the complete recorded word "
                "at predecessor cursor r; then inspect successor cursor r+1 "
                "before inserting its word"
            ),
            "injection": (
                "a placed point or active two-point x-line lies in the "
                "successor promoted core at an absolute lateral cell outside "
                "the predecessor promoted core"
            ),
            "base3_shell": (
                "shell 0 is distance 0; shell j>=1 is the least j with "
                "distance <= 3^(j-1)"
            ),
            "hash_role": (
                "state keys and injection targets are compared as exact Python "
                "tuples/integers; SHA-256 values are output commitments only"
            ),
        },
        "sample_scope": (
            None if sample_level is None else {
                "level": sample_level,
                "maximum_transitions_per_order": sample_transitions,
            }
        ),
        "orders": order_results,
        "proof_boundary": {
            "finite_computation": [
                "exact cursor translations in three pinned realized orders",
                "exact promoted-core overlap and capped x-line occupancy",
                "exact remote injection masks and stated birth/tile decompositions",
                "exact congruence or noncongruence on the scanned L5--L8 transitions",
            ],
            "not_proved": [
                "that any tested finite key stabilizes beyond L8",
                "a uniform bound on unrelated-anchor injection",
                "non-x secant or exact collision closure",
                "positive connector availability or a greatest safety fixed point",
                "an unconditional theorem",
            ],
        },
    }


def structural_estimate(universal_path):
    resource = enforce_resource_policy()
    inputs = validate_inputs(universal_path)
    started = time.time()
    _raw, core_by_step, _index_by_step, scans = load_universal_core(
        universal_path
    )
    _d24, d24_audit = reconstruct_d24_sizes(scans)
    gaps = {}
    for level in LEVELS:
        state = load_state(level)
        gaps[level] = len(state["parent_word"])
        del state
    transitions_per_order = sum(value - 1 for value in gaps.values())
    maximum_core = max(len(core) for core in core_by_step.values())
    average_core = sum(map(len, core_by_step.values())) / len(core_by_step)
    return {
        "status": (
            "pinned structural estimate; no realized points, schedules, "
            "occupancy, cursor transitions, or congruence classes scanned"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "D2-4_size_reconstruction": d24_audit,
        "levels": [
            {"level": level, "gaps": gaps[level],
             "transitions_per_order": gaps[level] - 1}
            for level in LEVELS
        ],
        "orders": list(ORDER_NAMES),
        "transitions_per_order": transitions_per_order,
        "planned_total_transitions": len(ORDER_NAMES) * transitions_per_order,
        "universal_promoted_core_size": {
            "minimum": min(len(core) for core in core_by_step.values()),
            "maximum": maximum_core,
            "unweighted_mean": average_core,
        },
        "conservative_successor_cell_scans": (
            len(ORDER_NAMES) * transitions_per_order * maximum_core
        ),
        "planned_representations_per_order": 4,
        "recommended_sample": (
            "sample L8 with 2000 transitions/order before the canonical run; "
            "scale successor-cell throughput and peak RSS; stop if projected "
            "runtime exceeds 15 minutes or RSS exceeds 1.2 GB"
        ),
    }


def atomic_write_json(path, payload):
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".tmp.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("estimate", "sample", "run"))
    parser.add_argument(
        "--universal-artifact", type=Path,
        default=EXPECTED_UNIVERSAL_RAW,
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--sample-level", type=int, choices=LEVELS, default=8,
    )
    parser.add_argument(
        "--sample-transitions", type=int, default=2000,
    )
    arguments = parser.parse_args()
    if arguments.sample_transitions <= 0:
        parser.error("--sample-transitions must be positive")
    if arguments.mode in ("sample", "run") and arguments.output is None:
        parser.error("sample/run requires --output")

    started = time.time()
    if arguments.mode == "estimate":
        payload = structural_estimate(arguments.universal_artifact)
    elif arguments.mode == "sample":
        payload = exact_probe(
            arguments.universal_artifact,
            sample_level=arguments.sample_level,
            sample_transitions=arguments.sample_transitions,
        )
    else:
        payload = exact_probe(arguments.universal_artifact)
    if arguments.output is not None:
        atomic_write_json(arguments.output, payload)
    print(json.dumps({
        "status": payload["status"],
        "mode": arguments.mode,
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "elapsed_seconds": round(time.time() - started, 3),
        "output": (
            str(arguments.output.resolve()) if arguments.output else None
        ),
        "output_sha256": (
            file_sha256(arguments.output.resolve())
            if arguments.output is not None else None
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
