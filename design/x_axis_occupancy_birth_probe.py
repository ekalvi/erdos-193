#!/usr/bin/env python3
"""Exact finite x-parallel occupancy/birth smoke probe.

This checker targets the 42 realized L7 parent corridors and their 146
realized L8 child corridors retained by ``far_secant_future_trace.py``.  It
reconstructs prefix-active point populations independently from the L7/L8
construction pickles under three finite schedules:

* the recorded gate order;
* the inherited-tile pipeline order; and
* a counterfactual left-to-right replay of the same recorded words.

At a pending anchor ``a``, an x-parallel line is indexed by its relative
lateral coordinate ``zeta=(y-a_y,z-a_z)``.  The probe retains every integer
cell in the universal length-five core

    h(zeta)^2 = (36 y^2 - 12 y z + 36 z^2) / 35 <= 1728/5.

For each cell it records the exact prefix-active occupancy in ``{0,1,2}``.
It then replays the selected connector word point by point, separately checks
collisions, and records every singleton-to-line birth.  For each actual
L7-to-L8 child edge it decomposes target occupancy into four exact sources:

1. transport of the source prefix;
2. the source connector action;
3. completion of the rest of L7 after the source cursor; and
4. L8 connector insertions preceding the child cursor.

Finally it tests a small CEGAR ladder whose state consists of step, the two
occupancy bitplanes, a correlated ancestral suffix, and a causal contiguous
path window.  Current connector choice is an action label, not hidden in the
pre-choice state.  No address streams are multiplied independently.

The result is exact finite evidence for one fixed set of recorded words.  It
is not a universal Post quotient, does not cover non-x secants, and does not
make the state Markov across arbitrary same-level corridor jumps.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_occupancy_birth_probe.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_occupancy_birth_probe.py run \
        --output /tmp/x-axis-occupancy-birth-probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import MENU  # noqa: E402
from imbricate193 import apply  # noqa: E402
from inherited_tile_lifetime import (  # noqa: E402
    pipeline_schedule,
    tile_layout,
)


DEFAULT_TRACE = Path("/tmp/far-secant-future-trace-canonical.json")
EXPECTED_TRACE_SHA256 = (
    "611bf74be1d42bd15d311964603daa573f8ff39a0f3bcb9542f4063341919b87"
)
EXPECTED_TRACE_CHECKER_SHA256 = (
    "6f286cb118166c1375eb777ec6e24bcdc58766b98538099c604eb97b5c3dd430"
)
EXPECTED_INPUT_SHA256 = {
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "design/far_secant_future_trace.py": EXPECTED_TRACE_CHECKER_SHA256,
    "design/inherited_tile_lifetime.py": (
        "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4"
    ),
    "gate2-ledger-L6.json": (
        "1d785e4a39434511603fe6f5f13955bf9946357bf3082b1ac47528d50acb4695"
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
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
    ),
}
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
SCHEDULES = ("gate", "pipeline", "left_to_right")
B_LATERAL = ((0, -3), (3, -1))
MAX_WORD_LENGTH = 5
CORE_H_SQUARED_NUMERATOR = 1728
CORE_H_SQUARED_DENOMINATOR = 5
CEGAR_DEPTHS = (0, 1, 2)
CEGAR_RADII = (0, 1, 2, 3)
CEGAR_OCCUPANCY_MODES = (
    "active_lines_only_diagnostic",
    "full_counts",
    "full_counts_with_provenance",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
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


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def sub2(first, second):
    return first[0] - second[0], first[1] - second[1]


def lateral(point):
    return point[1], point[2]


def lateral_transport(vector, control):
    displaced = vector[0] - control[0], vector[1] - control[1]
    return (
        B_LATERAL[0][0] * displaced[0]
        + B_LATERAL[0][1] * displaced[1],
        B_LATERAL[1][0] * displaced[0]
        + B_LATERAL[1][1] * displaced[1],
    )


def h_squared_numerator(vector):
    y, z = vector
    return 36 * y * y - 12 * y * z + 36 * z * z


def in_universal_core(vector):
    # h^2 = numerator/35 and D_5^2 = 1728/5.
    return (
        CORE_H_SQUARED_DENOMINATOR * h_squared_numerator(vector)
        <= 35 * CORE_H_SQUARED_NUMERATOR
    )


def build_core_cells():
    # lambda_min(S)=6/7 gives |coordinate|<=20 for D_5.
    cells = tuple(
        (y, z)
        for y in range(-20, 21)
        for z in range(-20, 21)
        if in_universal_core((y, z))
    )
    if not cells or (0, 0) not in cells:
        raise AssertionError("universal x core is malformed")
    if any(max(abs(y), abs(z)) > 20 for y, z in cells):
        raise AssertionError("universal x core escaped its proved square")
    return cells, {cell: index for index, cell in enumerate(cells)}


CORE_CELLS, CORE_INDEX = build_core_cells()
CORE_MASK_BYTES = (len(CORE_CELLS) + 7) // 8


def mask_profile(mask):
    raw = mask.to_bytes(CORE_MASK_BYTES, "little")
    if len(CORE_CELLS) % 8:
        if raw[-1] >> (len(CORE_CELLS) % 8):
            raise AssertionError("occupancy mask has bits outside the core")
    return {
        "set_bits": mask.bit_count(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def count_masks(counts):
    one = 0
    two = 0
    for index, count in counts.items():
        if count == 1:
            one |= 1 << index
        elif count == 2:
            two |= 1 << index
        elif count:
            raise AssertionError("lateral occupancy exceeds two", index, count)
    if one & two:
        raise AssertionError("occupancy bitplanes overlap")
    return one, two


def enforce_resource_policy():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "estimate/run requires every thread-cap variable to equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    try:
        nice_value = os.getpriority(os.PRIO_PROCESS, 0)
    except (AttributeError, OSError):
        nice_value = None
    if nice_value is not None and nice_value < 10:
        raise RuntimeError(
            f"estimate/run requires process nice >=10, observed {nice_value}"
        )
    return {
        "processes": 1,
        "thread_cap": 1,
        "minimum_nice": 10,
        "observed_nice": nice_value,
    }


def validate_inputs(trace_path):
    observed = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    if observed != EXPECTED_INPUT_SHA256:
        raise AssertionError(
            "pinned input drift",
            {name: observed[name] for name in observed
             if observed[name] != EXPECTED_INPUT_SHA256[name]},
        )
    trace_hash = file_sha256(trace_path)
    if trace_hash != EXPECTED_TRACE_SHA256:
        raise AssertionError("far trace artifact drift", trace_hash)
    return {**observed, "far_trace_artifact": trace_hash}


def load_trace(trace_path):
    with Path(trace_path).open() as handle:
        trace = json.load(handle)
    if trace["checker_sha256"] != EXPECTED_TRACE_CHECKER_SHA256:
        raise AssertionError("far trace checker commitment drift")
    parents = trace["parent_states"]
    children = trace["child_states"]
    if len(parents) != 42 or len(children) != 146:
        raise AssertionError("42/146 target horizon drift")
    parent_by_gap = {item["l7_parent_gap"]: item for item in parents}
    child_by_gap = {item["l8_gap"]: item for item in children}
    if len(parent_by_gap) != 42 or len(child_by_gap) != 146:
        raise AssertionError("target gaps are not unique")
    listed_children = []
    for parent in parents:
        ordered = parent["ordered_l8_children"]
        if [item["slot"] for item in ordered] != list(range(len(ordered))):
            raise AssertionError("parent child slots are not contiguous")
        for child in ordered:
            gap = child["l8_gap"]
            if gap not in child_by_gap:
                raise AssertionError("parent names an absent child gap")
            if child_by_gap[gap]["l7_parent_gap"] != parent["l7_parent_gap"]:
                raise AssertionError("parent/child gap link drift")
            listed_children.append(gap)
    if sorted(listed_children) != sorted(child_by_gap):
        raise AssertionError("parent ordered lists do not partition children")
    return trace, parent_by_gap, child_by_gap


def load_d24():
    with (ROOT / "gate2-ledger-L6.json").open() as handle:
        ledger = json.load(handle)
    values = defaultdict(set)
    for record in ledger:
        if "step" in record and "d24" in record:
            values[int(record["step"])].add(int(record["d24"]))
    if set(values) != set(range(len(MENU))):
        raise AssertionError("L6 ledger does not cover every menu step")
    if any(len(items) != 1 for items in values.values()):
        raise AssertionError("L6 ledger gives inconsistent D2-4 sizes")
    result = {step: next(iter(values[step])) for step in range(len(MENU))}
    return result, stable_hash(tuple(result[step] for step in range(len(MENU))))


def load_states():
    states = {}
    for level in range(5, 9):
        path = ROOT / f"gate2-l7-construction-L{level}.pkl"
        with path.open("rb") as handle:
            state = pickle.load(handle)
        state["anchors"] = [tuple(point) for point in state["anchors"]]
        state["parent_word"] = tuple(state["parent_word"])
        state["words"] = {
            int(gap): tuple(word) for gap, word in state["words"].items()
        }
        state["order"] = tuple(state["order"])
        gaps = len(state["parent_word"])
        if set(state["words"]) != set(range(gaps)):
            raise AssertionError(f"L{level} word map is incomplete")
        if sorted(state["order"]) != list(range(gaps)):
            raise AssertionError(f"L{level} recorded order is not a permutation")
        if len(state["anchors"]) != gaps + 1:
            raise AssertionError(f"L{level} anchor count mismatch")
        maximum = max(map(len, state["words"].values()), default=0)
        if maximum > MAX_WORD_LENGTH:
            raise AssertionError(
                f"L{level} selected word exceeds length-five core", maximum
            )
        states[level] = state
    return states


def build_child_maps(states):
    child_maps = {}
    commitments = {}
    for parent_level in range(5, 8):
        parent = states[parent_level]
        child = states[parent_level + 1]
        mapping = {}
        child_word = []
        child_gap = 0
        for parent_gap in range(len(parent["parent_word"])):
            prefix = (0, 0, 0)
            word = parent["words"][parent_gap]
            for slot, step in enumerate(word):
                mapping[child_gap] = {
                    "parent_gap": parent_gap,
                    "slot": slot,
                    "prefix": prefix,
                    "step": step,
                }
                child_word.append(step)
                prefix = add(prefix, MENU[step])
                child_gap += 1
            expected = apply(M_BAL3, MENU[parent["parent_word"][parent_gap]])
            if prefix != expected:
                raise AssertionError(
                    "selected word endpoint mismatch", parent_level, parent_gap
                )
        if tuple(child_word) != child["parent_word"]:
            raise AssertionError(
                f"L{parent_level} words do not form the L{parent_level + 1} parent word"
            )
        child_maps[parent_level + 1] = mapping
        commitments[str(parent_level + 1)] = stable_hash(tuple(
            (
                gap,
                item["parent_gap"],
                item["slot"],
                item["prefix"],
                item["step"],
            )
            for gap, item in sorted(mapping.items())
        ))
    return child_maps, commitments


def load_viz_parent_shell():
    with (ROOT / "viz/walk3d-data.json").open() as handle:
        full = json.load(handle)
    viz = {"levels": [{} for _item in full["levels"]]}
    for level in (7, 8):
        viz["levels"][level - 1] = {
            "parents": full["levels"][level - 1]["parents"]
        }
    return viz


def schedules_for_level(level, state, viz, d24):
    gaps = len(state["parent_word"])
    orders = {
        "gate": tuple(state["order"]),
        "left_to_right": tuple(range(gaps)),
    }
    tile_gaps, _owners = tile_layout(level, state, viz)
    entries, guards = pipeline_schedule(state, tile_gaps, d24)
    orders["pipeline"] = tuple(item["gap"] for item in entries)
    ranks = {}
    for name, order in orders.items():
        if sorted(order) != list(range(gaps)):
            raise AssertionError(level, name, "schedule is not a permutation")
        ranks[name] = {gap: rank for rank, gap in enumerate(order)}
    phases = {
        "gate": {gap: "recorded-gate" for gap in range(gaps)},
        "left_to_right": {
            gap: "counterfactual-left-to-right" for gap in range(gaps)
        },
        "pipeline": {item["gap"]: item["phase"] for item in entries},
    }
    summary = {
        "gate_order_sha256": stable_hash(orders["gate"]),
        "pipeline_entry_stream_sha256": stable_hash(entries),
        "pipeline_guard_map_sha256": stable_hash(guards),
        "left_to_right_order_sha256": stable_hash(orders["left_to_right"]),
        "pipeline_guards": len(guards),
    }
    return ranks, phases, summary


def word_interiors(start, word):
    position = tuple(start)
    interiors = []
    for ordinal, step in enumerate(word):
        position = add(position, MENU[step])
        if ordinal + 1 < len(word):
            interiors.append(position)
    return interiors, position


def point_record(
    stable_id,
    coordinate,
    role,
    rank_by_schedule,
    birth_gap=None,
    interior_ordinal=None,
    parent_record=None,
):
    return {
        "stable_id": stable_id,
        "coordinate": tuple(coordinate),
        "lateral": lateral(coordinate),
        "role": role,
        "rank_by_schedule": dict(rank_by_schedule),
        "birth_gap": birth_gap,
        "interior_ordinal": interior_ordinal,
        "parent_record": parent_record,
    }


def build_level_data(level, state, ranks, parent_records=None):
    gaps = len(state["parent_word"])
    if parent_records is None:
        anchors = [
            point_record(
                f"anchor:L{level}:P{index}",
                coordinate,
                "anchor",
                {name: -1 for name in SCHEDULES},
            )
            for index, coordinate in enumerate(state["anchors"])
        ]
    else:
        if len(parent_records) != len(state["anchors"]):
            raise AssertionError("parent path/child anchor length mismatch")
        anchors = []
        for index, (parent, coordinate) in enumerate(
            zip(parent_records, state["anchors"])
        ):
            expected = apply(M_BAL3, parent["coordinate"])
            if coordinate != expected:
                raise AssertionError(
                    "child anchor is not the parent point image", level, index
                )
            anchors.append(point_record(
                parent["stable_id"],
                coordinate,
                "anchor",
                {name: -1 for name in SCHEDULES},
                parent_record=parent,
            ))

    interiors_by_gap = {}
    construction_records = list(anchors)
    completed = [anchors[0]]
    for gap in range(gaps):
        word = state["words"][gap]
        interiors, endpoint = word_interiors(state["anchors"][gap], word)
        if endpoint != state["anchors"][gap + 1]:
            raise AssertionError("selected connector endpoint drift", level, gap)
        records = []
        for ordinal, coordinate in enumerate(interiors, 1):
            record = point_record(
                f"connector:L{level}:G{gap}:I{ordinal}",
                coordinate,
                "connector-interior",
                {name: ranks[name][gap] for name in SCHEDULES},
                birth_gap=gap,
                interior_ordinal=ordinal,
            )
            records.append(record)
        interiors_by_gap[gap] = tuple(records)
        construction_records.extend(records)
        completed.extend(records)
        completed.append(anchors[gap + 1])

    coordinates = [record["coordinate"] for record in completed]
    if len(coordinates) != len(set(coordinates)):
        raise AssertionError(f"L{level} completed path repeats a point")
    if len(completed) != len(construction_records):
        raise AssertionError(f"L{level} construction/path population drift")
    fibers = defaultdict(list)
    coordinate_map = {}
    for record in construction_records:
        if record["coordinate"] in coordinate_map:
            raise AssertionError(f"L{level} construction repeats a coordinate")
        coordinate_map[record["coordinate"]] = record
        fibers[record["lateral"]].append(record)
    if max(map(len, fibers.values()), default=0) > 2:
        raise AssertionError(f"L{level} has three completed points on an x-line")
    return {
        "level": level,
        "state": state,
        "anchors": anchors,
        "interiors_by_gap": interiors_by_gap,
        "construction_records": construction_records,
        "completed": completed,
        "fibers": dict(fibers),
        "coordinate_map": coordinate_map,
    }


def is_active(record, schedule, cursor_rank):
    return record["rank_by_schedule"][schedule] < cursor_rank


def occupancy_observation(level_data, gap, schedule, ranks):
    state = level_data["state"]
    anchor = state["anchors"][gap]
    anchor_lateral = lateral(anchor)
    cursor_rank = ranks[schedule][gap]
    counts = {}
    active_by_index = {}
    anchor_counts = {}
    inserted_counts = {}
    for index, cell in enumerate(CORE_CELLS):
        absolute = (
            anchor_lateral[0] + cell[0],
            anchor_lateral[1] + cell[1],
        )
        active = tuple(
            record
            for record in level_data["fibers"].get(absolute, ())
            if is_active(record, schedule, cursor_rank)
        )
        if not active:
            continue
        if len(active) > 2:
            raise AssertionError("prefix-active x fiber exceeds two")
        active_by_index[index] = active
        counts[index] = len(active)
        anchors = sum(record["role"] == "anchor" for record in active)
        insertions = len(active) - anchors
        if anchors:
            anchor_counts[index] = anchors
        if insertions:
            inserted_counts[index] = insertions
    one, two = count_masks(counts)
    anchor_one, anchor_two = count_masks(anchor_counts)
    inserted_one, inserted_two = count_masks(inserted_counts)
    return {
        "level": level_data["level"],
        "gap": gap,
        "schedule": schedule,
        "cursor_rank": cursor_rank,
        "step": state["parent_word"][gap],
        "one_mask": one,
        "two_mask": two,
        "anchor_one_mask": anchor_one,
        "anchor_two_mask": anchor_two,
        "inserted_one_mask": inserted_one,
        "inserted_two_mask": inserted_two,
        "counts": counts,
        "active_by_index": active_by_index,
    }


def occupancy_public(observation):
    return {
        "level": observation["level"],
        "gap": observation["gap"],
        "schedule": observation["schedule"],
        "cursor_rank": observation["cursor_rank"],
        "step": observation["step"],
        "one": mask_profile(observation["one_mask"]),
        "two": mask_profile(observation["two_mask"]),
        "anchor_one": mask_profile(observation["anchor_one_mask"]),
        "anchor_two": mask_profile(observation["anchor_two_mask"]),
        "inserted_one": mask_profile(observation["inserted_one_mask"]),
        "inserted_two": mask_profile(observation["inserted_two_mask"]),
    }


def replay_selected_action(level_data, observation, schedule, ranks):
    gap = observation["gap"]
    state = level_data["state"]
    word = state["words"][gap]
    anchor = state["anchors"][gap]
    cursor_rank = ranks[schedule][gap]
    counts = dict(observation["counts"])
    occupants = {
        index: list(records)
        for index, records in observation["active_by_index"].items()
    }
    temporary_coordinates = set()
    position = (0, 0, 0)
    births = []
    insertions = []
    for ordinal, step in enumerate(word):
        position = add(position, MENU[step])
        if ordinal + 1 == len(word):
            continue
        cell = lateral(position)
        index = CORE_INDEX.get(cell)
        if index is None:
            raise AssertionError("selected interior lies outside universal core")
        absolute = add(anchor, position)
        final_record = level_data["coordinate_map"].get(absolute)
        if final_record is None:
            raise AssertionError("selected interior absent from completed path")
        collision = (
            is_active(final_record, schedule, cursor_rank)
            or absolute in temporary_coordinates
        )
        if collision:
            raise AssertionError(
                "recorded selected word has a prefix collision",
                level_data["level"], gap, schedule, ordinal,
            )
        before = counts.get(index, 0)
        if before >= 2:
            raise AssertionError(
                "recorded selected word hits an active x-secant",
                level_data["level"], gap, schedule, ordinal, cell,
            )
        previous = occupants.get(index, [])
        if before == 1:
            if len(previous) != 1:
                raise AssertionError("singleton provenance is not unique")
            earlier = previous[0]
            if isinstance(earlier, dict):
                if earlier["role"] == "anchor":
                    birth_type = "anchor+selected-interior"
                else:
                    birth_type = "prior-interior+selected-interior"
                earlier_id = earlier["stable_id"]
            else:
                birth_type = "selected-interior+selected-interior"
                earlier_id = earlier
            births.append((ordinal + 1, cell, birth_type, earlier_id))
        selected_id = (
            f"selected:L{level_data['level']}:G{gap}:I{ordinal + 1}"
        )
        occupants.setdefault(index, []).append(selected_id)
        counts[index] = before + 1
        temporary_coordinates.add(absolute)
        insertions.append((ordinal + 1, cell, before, before + 1))
    if add(anchor, position) != state["anchors"][gap + 1]:
        raise AssertionError("selected action endpoint mismatch")
    post_one, post_two = count_masks(counts)
    record = {
        "level": level_data["level"],
        "gap": gap,
        "schedule": schedule,
        "step": state["parent_word"][gap],
        "selected_word": word,
        "pre_one_sha256": mask_profile(observation["one_mask"])["sha256"],
        "pre_two_sha256": mask_profile(observation["two_mask"])["sha256"],
        "post_one_sha256": mask_profile(post_one)["sha256"],
        "post_two_sha256": mask_profile(post_two)["sha256"],
        "insertions": tuple(insertions),
        "births": tuple(births),
    }
    return record


def masks_for_category_counts(counts):
    one, two = count_masks(counts)
    return one, two


def target_decomposition(
    source_gap,
    child_gap,
    slot,
    schedule,
    level7,
    level8,
    observations,
    ranks7,
    ranks8,
):
    source = observations[(7, source_gap, schedule)]
    target = observations[(8, child_gap, schedule)]
    word = level7["state"]["words"][source_gap]
    prefix = (0, 0, 0)
    for step in word[:slot]:
        prefix = add(prefix, MENU[step])
    if slot >= len(word):
        raise AssertionError("child slot outside source word")
    expected_child = None
    running_gap = 0
    for gap in range(source_gap):
        running_gap += len(level7["state"]["words"][gap])
    expected_child = running_gap + slot
    if expected_child != child_gap:
        raise AssertionError("source/child block link mismatch")

    categories = {
        "transported_source_prefix": {},
        "source_action": {},
        "late_parent_completion": {},
        "child_prior_insertions": {},
    }
    source_rank = ranks7[schedule][source_gap]
    target_rank = ranks8[schedule][child_gap]
    for index, active in target["active_by_index"].items():
        for record in active:
            if record["role"] == "anchor":
                parent = record["parent_record"]
                if parent is None:
                    raise AssertionError("L8 anchor lacks its L7 parent record")
                if is_active(parent, schedule, source_rank):
                    category = "transported_source_prefix"
                elif (
                    parent["role"] == "connector-interior"
                    and parent["birth_gap"] == source_gap
                ):
                    category = "source_action"
                else:
                    if (
                        parent["role"] != "connector-interior"
                        or parent["rank_by_schedule"][schedule] <= source_rank
                    ):
                        raise AssertionError(
                            "uncategorized L7 completion point", source_gap,
                            child_gap, schedule, parent["stable_id"],
                        )
                    category = "late_parent_completion"
            else:
                if not is_active(record, schedule, target_rank):
                    raise AssertionError("inactive L8 point entered target occupancy")
                category = "child_prior_insertions"
            categories[category][index] = categories[category].get(index, 0) + 1

    total = defaultdict(int)
    for counts in categories.values():
        for index, count in counts.items():
            total[index] += count
    if dict(total) != target["counts"]:
        raise AssertionError("four-way occupancy decomposition is not exact")

    predicted_transport = defaultdict(int)
    control = lateral(prefix)
    for index, count in source["counts"].items():
        target_cell = lateral_transport(CORE_CELLS[index], control)
        target_index = CORE_INDEX.get(target_cell)
        if target_index is not None:
            predicted_transport[target_index] += count
    if dict(predicted_transport) != categories["transported_source_prefix"]:
        raise AssertionError(
            "source-prefix occupancy transport mismatch",
            source_gap, child_gap, slot, schedule,
        )

    profiles = {}
    for name, counts in categories.items():
        one, two = masks_for_category_counts(counts)
        profiles[name] = {
            "points": sum(counts.values()),
            "occupied_cells": len(counts),
            "one": mask_profile(one),
            "two": mask_profile(two),
        }
    return {
        "source_gap": source_gap,
        "child_gap": child_gap,
        "slot": slot,
        "schedule": schedule,
        "prefix_control": prefix,
        "source_step": source["step"],
        "child_step": target["step"],
        "categories": profiles,
        "target_one_sha256": mask_profile(target["one_mask"])["sha256"],
        "target_two_sha256": mask_profile(target["two_mask"])["sha256"],
    }


def ancestry_suffix(level, gap, depth, states, child_maps):
    suffix = []
    current_level = level
    current_gap = gap
    for _index in range(depth):
        mapping = child_maps.get(current_level)
        if mapping is None:
            suffix.append(("ancestry-boundary", current_level, current_gap))
            break
        edge = mapping[current_gap]
        parent_level = current_level - 1
        parent_gap = edge["parent_gap"]
        parent_state = states[parent_level]
        suffix.append((
            parent_level,
            parent_state["parent_word"][parent_gap],
            parent_state["words"][parent_gap],
            edge["slot"],
            edge["prefix"],
            states[current_level]["parent_word"][current_gap],
        ))
        current_level = parent_level
        current_gap = parent_gap
    return tuple(suffix)


def ordered_window(level, gap, schedule, radius, states, ranks, phases):
    state = states[level]
    current_rank = ranks[level][schedule][gap]
    items = []
    for offset in range(-radius, radius + 1):
        other = gap + offset
        if not 0 <= other < len(state["parent_word"]):
            items.append((offset, "path-boundary"))
            continue
        other_rank = ranks[level][schedule][other]
        if other == gap:
            status = "cursor"
            chosen = None
        elif other_rank < current_rank:
            status = "placed"
            chosen = state["words"][other]
        else:
            status = "unplaced"
            chosen = None
        items.append((
            offset,
            state["parent_word"][other],
            status,
            chosen,
        ))
    return (
        phases[level][schedule][gap],
        tuple(items),
    )


def state_key(
    level,
    gap,
    schedule,
    depth,
    radius,
    occupancy_mode,
    observations,
    states,
    child_maps,
    ranks,
    phases,
):
    observation = observations[(level, gap, schedule)]
    if occupancy_mode == "active_lines_only_diagnostic":
        occupancy = (observation["two_mask"],)
    elif occupancy_mode == "full_counts":
        occupancy = (
            observation["one_mask"],
            observation["two_mask"],
        )
    elif occupancy_mode == "full_counts_with_provenance":
        occupancy = (
            observation["one_mask"],
            observation["two_mask"],
        )
        occupancy += (
            observation["anchor_one_mask"],
            observation["anchor_two_mask"],
            observation["inserted_one_mask"],
            observation["inserted_two_mask"],
        )
    else:
        raise AssertionError("unknown CEGAR occupancy mode", occupancy_mode)
    return (
        schedule,
        observation["step"],
        occupancy,
        ancestry_suffix(level, gap, depth, states, child_maps),
        ordered_window(
            level, gap, schedule, radius, states, ranks, phases
        ),
    )


def partition_profile(groups):
    sizes = Counter(len(items) for items in groups.values())
    return {
        "classes": len(groups),
        "nodes": sum(sizes[size] * size for size in sizes),
        "merged_classes": sum(count for size, count in sizes.items() if size > 1),
        "singleton_classes": sizes.get(1, 0),
        "largest_class": max(sizes, default=0),
        "class_size_histogram": dict(sorted(sizes.items())),
    }


def cegar_ladder(
    parent_by_gap,
    observations,
    states,
    child_maps,
    ranks,
    phases,
):
    records = []
    for depth in CEGAR_DEPTHS:
        for radius in CEGAR_RADII:
            for occupancy_mode in CEGAR_OCCUPANCY_MODES:
                state_groups = defaultdict(list)
                action_groups = defaultdict(list)
                class_stream = []
                for source_gap, parent in sorted(parent_by_gap.items()):
                    word = states[7]["words"][source_gap]
                    ordered_children = sorted(
                        parent["ordered_l8_children"],
                        key=lambda item: item["slot"],
                    )
                    for schedule in SCHEDULES:
                        source_key = state_key(
                            7, source_gap, schedule, depth, radius,
                            occupancy_mode, observations, states, child_maps,
                            ranks, phases,
                        )
                        post = []
                        prefix = (0, 0, 0)
                        for child in ordered_children:
                            slot = child["slot"]
                            if slot >= len(word):
                                raise AssertionError("trace child slot outside word")
                            if slot:
                                expected_prefix = (0, 0, 0)
                                for step in word[:slot]:
                                    expected_prefix = add(expected_prefix, MENU[step])
                                if prefix != expected_prefix:
                                    raise AssertionError("post prefix drift")
                            child_gap = child["l8_gap"]
                            child_key = state_key(
                                8, child_gap, schedule, depth, radius,
                                occupancy_mode, observations, states,
                                child_maps, ranks, phases,
                            )
                            post.append((slot, prefix, word[slot], child_key))
                            prefix = add(prefix, MENU[word[slot]])
                        node = (schedule, source_gap)
                        state_groups[source_key].append(node)
                        action_groups[(source_key, word)].append((node, tuple(post)))
                        class_stream.append((
                            node,
                            stable_hash(source_key),
                            stable_hash(word),
                            stable_hash(tuple(post)),
                        ))

                noncongruent = []
                for action_key, items in action_groups.items():
                    posts = defaultdict(list)
                    for node, post in items:
                        posts[stable_hash(post)].append(node)
                    if len(posts) > 1:
                        noncongruent.append({
                            "state_action_sha256": stable_hash(action_key),
                            "class_nodes": len(items),
                            "distinct_posts": len(posts),
                            "witnesses": [
                                {"post_sha256": digest, "nodes": nodes[:3]}
                                for digest, nodes in sorted(posts.items())[:3]
                            ],
                        })
                profile = partition_profile(state_groups)
                action_profile = partition_profile(action_groups)
                records.append({
                    "ancestry_depth": depth,
                    "path_window_radius": radius,
                    "occupancy_mode": occupancy_mode,
                    "state_partition": profile,
                    "state_action_partition": action_profile,
                    "state_action_classes_with_multiple_observed_posts": len(
                        noncongruent
                    ),
                    "counterexamples": noncongruent[:5],
                    "class_stream_sha256": stable_hash(sorted(class_stream)),
                    "interpretation": (
                        "a repeated class with multiple posts is refuted on "
                        "this finite recorded orbit; a class with one observed "
                        "post is only finite non-falsification"
                    ),
                })
    return records


def estimate_payload(trace_path):
    started = time.time()
    resource = enforce_resource_policy()
    inputs = validate_inputs(trace_path)
    _trace, parent_by_gap, child_by_gap = load_trace(trace_path)
    d24, d24_hash = load_d24()
    if len(d24) != 124:
        raise AssertionError("D2-4 vector length drift")
    return {
        "status": (
            "structural estimate for the exact finite 42-parent/146-child "
            "x-parallel occupancy/birth smoke probe; no construction pickle "
            "was loaded and no occupancy claim is made"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "target_horizon": {
            "L7_parent_gaps": len(parent_by_gap),
            "L8_child_gaps": len(child_by_gap),
            "schedules": list(SCHEDULES),
            "cursor_observations": (
                len(SCHEDULES) * (len(parent_by_gap) + len(child_by_gap))
            ),
        },
        "universal_length_five_core": {
            "definition": "(36*y^2-12*y*z+36*z^2)/35 <= 1728/5",
            "cells": len(CORE_CELLS),
            "proved_square_upper_bound": 1681,
            "cell_stream_sha256": stable_hash(CORE_CELLS),
        },
        "pipeline_d24_vector_sha256": d24_hash,
        "cegar_ladder": {
            "ancestry_depths": list(CEGAR_DEPTHS),
            "causal_path_window_radii": list(CEGAR_RADII),
            "occupancy_modes": list(CEGAR_OCCUPANCY_MODES),
            "experiments": (
                len(CEGAR_DEPTHS)
                * len(CEGAR_RADII)
                * len(CEGAR_OCCUPANCY_MODES)
            ),
        },
        "proof_boundary": {
            "proved_by_estimate": [
                "the pinned far trace contains exactly 42 unique L7 parent gaps and 146 unique L8 child gaps",
                "the universal length-five integer core and CEGAR parameter grid are finite and deterministic",
            ],
            "not_run": [
                "construction-prefix occupancy reconstruction",
                "selected-word insertion and x-line births",
                "four-way target decomposition and CEGAR post tests",
            ],
        },
    }


def exact_payload(trace_path):
    started = time.time()
    resource = enforce_resource_policy()
    inputs = validate_inputs(trace_path)
    _trace, parent_by_gap, child_by_gap = load_trace(trace_path)
    d24, d24_hash = load_d24()
    states = load_states()
    child_maps, child_map_hashes = build_child_maps(states)
    viz = load_viz_parent_shell()

    ranks = {}
    phases = {}
    schedule_summaries = {}
    for level in (7, 8):
        level_ranks, level_phases, summary = schedules_for_level(
            level, states[level], viz, d24
        )
        ranks[level] = level_ranks
        phases[level] = level_phases
        schedule_summaries[str(level)] = summary

    level7 = build_level_data(7, states[7], ranks[7])
    level8 = build_level_data(
        8, states[8], ranks[8], parent_records=level7["completed"]
    )
    level_data = {7: level7, 8: level8}

    for gap, record in parent_by_gap.items():
        if tuple(record["actual_corridor_start_coordinate"]) != states[7][
            "anchors"
        ][gap]:
            raise AssertionError("far trace L7 start coordinate drift")
        if record["step"] != states[7]["parent_word"][gap]:
            raise AssertionError("far trace L7 step drift")
        if tuple(record["actual_selected_connector_word"]) != states[7][
            "words"
        ][gap]:
            raise AssertionError("far trace L7 selected word drift")
    for gap, record in child_by_gap.items():
        if tuple(record["actual_corridor_start_coordinate"]) != states[8][
            "anchors"
        ][gap]:
            raise AssertionError("far trace L8 start coordinate drift")
        if record["step"] != states[8]["parent_word"][gap]:
            raise AssertionError("far trace L8 step drift")
        if tuple(record["actual_selected_connector_word"]) != states[8][
            "words"
        ][gap]:
            raise AssertionError("far trace L8 selected word drift")
        edge = child_maps[8][gap]
        if edge["parent_gap"] != record["l7_parent_gap"]:
            raise AssertionError("far trace child ancestry drift")
        if edge["slot"] != record[
            "actual_parent_connector_step_slot_zero_based"
        ]:
            raise AssertionError("far trace child slot drift")
        if tuple(record["l7_parent_connector_prefix_vector"]) != edge["prefix"]:
            raise AssertionError("far trace child prefix drift")

    observations = {}
    occupancy_stream = []
    action_stream = []
    target_gaps = {7: sorted(parent_by_gap), 8: sorted(child_by_gap)}
    for level in (7, 8):
        for gap in target_gaps[level]:
            for schedule in SCHEDULES:
                observation = occupancy_observation(
                    level_data[level], gap, schedule, ranks[level]
                )
                observations[(level, gap, schedule)] = observation
                occupancy_stream.append(occupancy_public(observation))
                action_stream.append(replay_selected_action(
                    level_data[level], observation, schedule, ranks[level]
                ))

    decomposition_stream = []
    for source_gap, parent in sorted(parent_by_gap.items()):
        for child in sorted(
            parent["ordered_l8_children"], key=lambda item: item["slot"]
        ):
            for schedule in SCHEDULES:
                decomposition_stream.append(target_decomposition(
                    source_gap,
                    child["l8_gap"],
                    child["slot"],
                    schedule,
                    level7,
                    level8,
                    observations,
                    ranks[7],
                    ranks[8],
                ))

    cegar = cegar_ladder(
        parent_by_gap,
        observations,
        states,
        child_maps,
        ranks,
        phases,
    )

    occupancy_census = {}
    for level in (7, 8):
        occupancy_census[str(level)] = {}
        for schedule in SCHEDULES:
            selected = [
                item for item in occupancy_stream
                if item["level"] == level and item["schedule"] == schedule
            ]
            occupancy_census[str(level)][schedule] = {
                "corridors": len(selected),
                "distinct_one_masks": len({
                    item["one"]["sha256"] for item in selected
                }),
                "distinct_two_masks": len({
                    item["two"]["sha256"] for item in selected
                }),
                "maximum_singleton_cells": max(
                    (item["one"]["set_bits"] for item in selected), default=0
                ),
                "maximum_active_line_cells": max(
                    (item["two"]["set_bits"] for item in selected), default=0
                ),
            }

    birth_histogram = Counter(
        birth[2]
        for action in action_stream
        for birth in action["births"]
    )
    birth_histogram_by_schedule = {
        schedule: dict(sorted(Counter(
            birth[2]
            for action in action_stream
            if action["schedule"] == schedule
            for birth in action["births"]
        ).items()))
        for schedule in SCHEDULES
    }
    category_points = Counter()
    records_with_category = Counter()
    category_points_by_schedule = {
        schedule: Counter() for schedule in SCHEDULES
    }
    records_with_category_by_schedule = {
        schedule: Counter() for schedule in SCHEDULES
    }
    for record in decomposition_stream:
        for name, profile in record["categories"].items():
            category_points[name] += profile["points"]
            category_points_by_schedule[record["schedule"]][name] += profile[
                "points"
            ]
            if profile["points"]:
                records_with_category[name] += 1
                records_with_category_by_schedule[record["schedule"]][name] += 1

    return {
        "status": (
            "exact finite realized-word x-parallel occupancy, birth, and "
            "L7-to-L8 target-decomposition smoke probe; not a universal Post "
            "quotient, global stitch-state closure, availability bound, or "
            "unconditional theorem"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "scope": {
            "levels": [7, 8],
            "L7_parent_gaps": len(parent_by_gap),
            "L8_child_gaps": len(child_by_gap),
            "schedules": list(SCHEDULES),
            "left_to_right_semantics": (
                "counterfactual replay of the same pinned selected words with "
                "gap rank equal to path order; not a constructed alternate path"
            ),
            "alternate_connector_words": False,
            "covered_channel": (
                "prefix occupancy and births of x-parallel secants, with exact "
                "selected-point collision assertions"
            ),
        },
        "universal_length_five_core": {
            "definition": "(36*y^2-12*y*z+36*z^2)/35 <= 1728/5",
            "cells": len(CORE_CELLS),
            "proved_square_upper_bound": 1681,
            "cell_stream_sha256": stable_hash(CORE_CELLS),
        },
        "construction_checks": {
            "L7_completed_points": len(level7["completed"]),
            "L8_completed_points": len(level8["completed"]),
            "maximum_selected_word_length": max(
                len(word)
                for level in states.values()
                for word in level["words"].values()
            ),
            "pipeline_d24_vector_sha256": d24_hash,
            "child_map_sha256_by_level": child_map_hashes,
            "schedule_summaries": schedule_summaries,
        },
        "prefix_occupancy": {
            "observations": len(occupancy_stream),
            "census": occupancy_census,
            "stream_sha256": stable_hash(occupancy_stream),
        },
        "sequential_selected_actions": {
            "actions": len(action_stream),
            "collision_failures": 0,
            "active_x_line_hit_failures": 0,
            "birth_type_histogram": dict(sorted(birth_histogram.items())),
            "birth_type_histogram_by_schedule": birth_histogram_by_schedule,
            "stream_sha256": stable_hash(action_stream),
        },
        "four_way_target_decomposition": {
            "edge_schedule_records": len(decomposition_stream),
            "exact_total_mismatches": 0,
            "source_prefix_transport_mismatches": 0,
            "category_point_occurrences": dict(sorted(category_points.items())),
            "category_point_occurrences_by_schedule": {
                schedule: dict(sorted(counts.items()))
                for schedule, counts in category_points_by_schedule.items()
            },
            "records_with_nonzero_category": dict(
                sorted(records_with_category.items())
            ),
            "records_with_nonzero_category_by_schedule": {
                schedule: dict(sorted(counts.items()))
                for schedule, counts in records_with_category_by_schedule.items()
            },
            "stream_sha256": stable_hash(decomposition_stream),
        },
        "cegar_ladder": cegar,
        "proof_boundary": {
            "proved_by_this_finite_replay": [
                "the reported occupancies are exact for the pinned 42 L7 and 146 L8 corridors under each named finite schedule",
                "every pinned selected word passes sequential collision and active-x-line checks, and every reported x-line birth is an exact 1-to-2 lateral occupancy transition",
                "every target occupancy is the exact union of transported source prefix, source action, late L7 completion, and prior L8 insertion components",
                "every CEGAR counterexample is an exact differing post among equal tested finite state/action keys",
            ],
            "finite_evidence_only": [
                "the number of repeated occupancy/ordered states and their observed posts on this one realized L7-to-L8 horizon",
                "the left-to-right replay uses recorded words chosen under another schedule and is only a finite schedule-order diagnostic",
            ],
            "not_proved": [
                "transition congruence for alternate legal connector choices or L9 and later",
                "a Markov update across arbitrary same-level corridor recenterings",
                "control of non-x secants, endpoint-on-candidate-line defects, or the Boolean union of poison channels",
                "positive connector availability, a safety greatest fixed point, or an unconditional theorem",
            ],
        },
    }


def atomic_write_json(path, payload):
    path = Path(path).resolve()
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
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("estimate", "run"):
        child = subparsers.add_parser(command)
        child.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
        child.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "estimate":
        payload = estimate_payload(args.trace)
    else:
        payload = exact_payload(args.trace)
    if args.output is None:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        atomic_write_json(args.output, payload)


if __name__ == "__main__":
    main()
