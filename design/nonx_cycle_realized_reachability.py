#!/usr/bin/env python3
"""Exact finite realized-path reachability test for the canonical non-x cycle.

The arbitrary-switching graph in ``nonx_degenerate_site_graph.py`` contains
the direction-blind two-cycle

    phase A: step 1, site (-3,0,-3), word (15,1,20,71), slot 1
    phase B: step 1, site (-3,3,-2), word (20,71,1,15), slot 2.

That graph certificate does not say that the two actions occur on one
realized address chain.  This checker joins the cycle back to the pinned
gate2 L5--L8 construction pickles.  It performs three separate exact tests:

* literal selected-action occurrences of the two named words;
* macro occurrences with the same source step, prefix control, child step,
  and carried-site avoidance, allowing a different selected word; and
* chronological birth of a secant through the phase-A corridor site with
  direction ``g_n=canonprim(N^(2n)*(3,-1,3))``.

The parent-to-child join is the actual ordered factor of the realized path:
child indices are reconstructed from the selected parent words, and every
child anchor is checked against its affine parent prefix.  No address stream
is independently continued and no alternative connector is introduced.

For the chronological secant query, every level starts with all anchors
placed.  An interior point has birth time equal to its gap's position in the
constructor's ``order``.  A queried line is a live secant at a stitch exactly
when its second-earliest distinct point has birth time strictly smaller than
the stitch position.  Only moments of requested lines are retained, so the
scan is small and exact.

This does not independently repeat the repository's global triple-free
verification.  It pins the exact construction pickles, reconstructs their
coordinates and stitch chronology, and checks only the cycle reachability
question.  A zero result is a finite obstruction for this fixed cycle in
this fixed L5--L8 history, not a theorem about all possible ordered policies.

Run on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/nonx_cycle_realized_reachability.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/nonx_cycle_realized_reachability.py run \
        --output /tmp/nonx-cycle-realized-reachability.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("/tmp/nonx-cycle-realized-reachability.json")

LEVELS = (5, 6, 7, 8)
EXPECTED_INPUT_SHA256 = {
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
}
CYCLE_SOURCE_NAME = "design/nonx-cycle-invariant-certificate-summary.json"
EXPECTED_CYCLE_SOURCE_SHA256 = (
    "cdc50b48655a80731bf66ae1461116963277e4ed622b17ad1c2849dcebcfd6dd"
)

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
N = (
    (3, 0, 0),
    (0, -1, 3),
    (0, -3, 0),
)
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)

SOURCE_STEP = 1
REVEAL_DIRECTION = (3, -1, 3)
REVEAL_SITE = (-6, 1, -6)
PHASES = (
    {
        "name": "A",
        "candidate_site": (-3, 0, -3),
        "prefix_control": (-2, 1, -2),
        "target_step": 1,
        "word": (15, 1, 20, 71),
        "slot": 1,
    },
    {
        "name": "B",
        "candidate_site": (-3, 3, -2),
        "prefix_control": (-2, 4, -2),
        "target_step": 1,
        "word": (20, 71, 1, 15),
        "slot": 2,
    },
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_snapshot(path):
    path = Path(path).resolve()
    before = path.stat()
    digest = file_sha256(path)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, field) for field in fields) != tuple(
        getattr(after, field) for field in fields
    ):
        raise RuntimeError("input changed while being hashed", str(path))
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "bytes": after.st_size,
    }


def stable_json(value):
    return json.dumps(value, sort_keys=True, indent=2) + "\n"


def add(first, second):
    return tuple(a + b for a, b in zip(first, second))


def subtract(first, second):
    return tuple(a - b for a, b in zip(first, second))


def apply_matrix(matrix, vector):
    return tuple(
        sum(coefficient * value for coefficient, value in zip(row, vector))
        for row in matrix
    )


def cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def canonical_primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if divisor == 0:
        raise ValueError("zero vector has no primitive direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def inverse_cycle_direction(cycles):
    direction = REVEAL_DIRECTION
    for _ in range(2 * cycles):
        direction = apply_matrix(N, direction)
    return canonical_primitive(direction)


def word_prefixes_and_interiors(word):
    position = (0, 0, 0)
    prefixes = []
    interiors = []
    for slot, step in enumerate(word):
        prefixes.append(position)
        position = add(position, MENU[step])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(prefixes), tuple(interiors), position


def validate_cycle_constants():
    identity = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    )
    assert tuple(
        tuple(
            sum(M[row][middle] * N[middle][column] for middle in range(3))
            for column in range(3)
        )
        for row in range(3)
    ) == tuple(tuple(9 * value for value in row) for row in identity)
    assert canonical_primitive(
        subtract(REVEAL_SITE, PHASES[0]["candidate_site"])
    ) == REVEAL_DIRECTION
    for index, phase in enumerate(PHASES):
        prefixes, interiors, endpoint = word_prefixes_and_interiors(
            phase["word"]
        )
        assert phase["word"][phase["slot"]] == phase["target_step"]
        assert prefixes[phase["slot"]] == phase["prefix_control"]
        assert phase["candidate_site"] not in interiors
        assert endpoint == apply_matrix(M, MENU[SOURCE_STEP])
        successor = PHASES[(index + 1) % len(PHASES)]
        assert apply_matrix(
            M, subtract(phase["candidate_site"], phase["prefix_control"])
        ) == successor["candidate_site"]


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "every thread-cap variable must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process priority")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise RuntimeError(
            "run with nice -n 15; minimum accepted nice value is 10, "
            f"observed {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def load_and_validate_states():
    states = {}
    snapshots = {}
    for level in LEVELS:
        name = f"gate2-l7-construction-L{level}.pkl"
        snapshot = stable_snapshot(ROOT / name)
        if snapshot["sha256"] != EXPECTED_INPUT_SHA256[name]:
            raise AssertionError("pinned construction pickle drift", snapshot)
        snapshots[name] = snapshot
        with (ROOT / name).open("rb") as handle:
            state = pickle.load(handle)
        assert set(state) == {"parent_word", "order", "words", "anchors"}
        gap_count = len(state["parent_word"])
        assert len(state["anchors"]) == gap_count + 1
        assert len(state["order"]) == gap_count
        assert set(state["order"]) == set(range(gap_count))
        assert set(state["words"]) == set(range(gap_count))
        assert all(len(point) == 3 for point in state["anchors"])
        for gap in range(gap_count):
            source_step = state["parent_word"][gap]
            word = tuple(state["words"][gap])
            assert 0 <= source_step < len(MENU)
            assert 1 <= len(word) <= 5
            assert all(0 <= step < len(MENU) for step in word)
            _prefixes, _interiors, endpoint = word_prefixes_and_interiors(word)
            assert endpoint == apply_matrix(M, MENU[source_step])
            assert add(state["anchors"][gap], endpoint) == state["anchors"][gap + 1]
        states[level] = state

    child_starts = {}
    for level in LEVELS[:-1]:
        state = states[level]
        child = states[level + 1]
        flattened = tuple(
            step
            for gap in range(len(state["parent_word"]))
            for step in state["words"][gap]
        )
        assert flattened == tuple(child["parent_word"])
        starts = []
        cursor = 0
        for gap in range(len(state["parent_word"])):
            starts.append(cursor)
            word = tuple(state["words"][gap])
            prefixes, _interiors, _endpoint = word_prefixes_and_interiors(word)
            for slot, prefix in enumerate(prefixes):
                expected = apply_matrix(M, add(state["anchors"][gap], prefix))
                assert tuple(child["anchors"][cursor + slot]) == expected
            cursor += len(word)
        assert cursor == len(child["parent_word"])
        assert tuple(child["anchors"][-1]) == apply_matrix(M, state["anchors"][-1])
        child_starts[level] = tuple(starts)
    return states, child_starts, snapshots


def validate_cycle_source():
    snapshot = stable_snapshot(ROOT / CYCLE_SOURCE_NAME)
    assert snapshot["sha256"] == EXPECTED_CYCLE_SOURCE_SHA256
    payload = json.loads((ROOT / CYCLE_SOURCE_NAME).read_text(encoding="utf-8"))
    assert payload["status"] == "all-n theorem for the fixed geometric two-word cycle"
    assert payload["cycle"]["step"] == SOURCE_STEP
    assert payload["cycle"]["each_edge_is_direction_blind"] is True
    assert payload["cycle"]["fixed_words_are_exact_cache_occurrences"] is True
    assert len(payload["cycle"]["edges"]) == len(PHASES)
    for record, phase in zip(payload["cycle"]["edges"], PHASES):
        assert tuple(record["source_site"]) == phase["candidate_site"]
        assert tuple(record["prefix_control"]) == phase["prefix_control"]
        assert tuple(record["word"]) == phase["word"]
        assert record["slot_0_based"] == phase["slot"]
    implication = payload["infinite_right_language_implication"]
    assert implication["integer_primitive_family"] == (
        "g_n=canonprim(N^(2n)*(3,-1,3)), n>=0"
    )
    return snapshot


def action_slots(state, gap, phase, literal):
    if state["parent_word"][gap] != SOURCE_STEP:
        return ()
    word = tuple(state["words"][gap])
    prefixes, interiors, _endpoint = word_prefixes_and_interiors(word)
    if literal:
        slot = phase["slot"]
        if word != phase["word"]:
            return ()
        assert word[slot] == phase["target_step"]
        assert prefixes[slot] == phase["prefix_control"]
        assert phase["candidate_site"] not in interiors
        return (slot,)
    if phase["candidate_site"] in interiors:
        return ()
    return tuple(
        slot
        for slot, (target, prefix) in enumerate(zip(word, prefixes))
        if target == phase["target_step"]
        and prefix == phase["prefix_control"]
    )


def action_census(states):
    result = {}
    for level, state in states.items():
        per_phase = {}
        for phase in PHASES:
            counts = Counter({
                "source_step_gaps": 0,
                "named_word_any_source": 0,
                "named_word_at_source_step": 0,
                "literal_selected_action_slots": 0,
                "target_step_slots": 0,
                "prefix_control_slots": 0,
                "control_and_target_slots": 0,
                "x_avoiding_macro_slots": 0,
            })
            counts["named_word_any_source"] = sum(
                tuple(word) == phase["word"] for word in state["words"].values()
            )
            for gap in range(len(state["parent_word"])):
                if state["parent_word"][gap] != SOURCE_STEP:
                    continue
                counts["source_step_gaps"] += 1
                word = tuple(state["words"][gap])
                prefixes, interiors, _endpoint = word_prefixes_and_interiors(word)
                counts["target_step_slots"] += sum(
                    step == phase["target_step"] for step in word
                )
                counts["prefix_control_slots"] += sum(
                    prefix == phase["prefix_control"] for prefix in prefixes
                )
                raw = sum(
                    target == phase["target_step"]
                    and prefix == phase["prefix_control"]
                    for target, prefix in zip(word, prefixes)
                )
                counts["control_and_target_slots"] += raw
                if phase["candidate_site"] not in interiors:
                    counts["x_avoiding_macro_slots"] += raw
                if word == phase["word"]:
                    counts["named_word_at_source_step"] += 1
                    counts["literal_selected_action_slots"] += 1
            per_phase[phase["name"]] = dict(sorted(counts.items()))
        result[str(level)] = per_phase
    return result


def realized_chains(states, child_starts, literal):
    chains = []
    for start_level in LEVELS:
        for start_phase in range(2):
            state = states[start_level]
            for start_gap in range(len(state["parent_word"])):
                for start_slot in action_slots(
                    state, start_gap, PHASES[start_phase], literal
                ):
                    level = start_level
                    gap = start_gap
                    phase_index = start_phase
                    slot = start_slot
                    records = []
                    while True:
                        current = states[level]
                        prefixes, _interiors, _endpoint = (
                            word_prefixes_and_interiors(tuple(current["words"][gap]))
                        )
                        records.append({
                            "level": level,
                            "gap": gap,
                            "phase": PHASES[phase_index]["name"],
                            "slot": slot,
                            "prefix_control": list(prefixes[slot]),
                            "actual_selected_word": list(current["words"][gap]),
                            "corridor_start": list(current["anchors"][gap]),
                        })
                        if level == LEVELS[-1]:
                            break
                        child_gap = child_starts[level][gap] + slot
                        level += 1
                        gap = child_gap
                        phase_index = 1 - phase_index
                        next_slots = action_slots(
                            states[level], gap, PHASES[phase_index], literal
                        )
                        if not next_slots:
                            break
                        # A word cannot visit the same prefix twice in these
                        # pinned triple-free connector domains.  Still assert
                        # the exact uniqueness needed for a deterministic join.
                        assert len(next_slots) == 1
                        slot = next_slots[0]
                    chains.append(records)
    histogram = Counter(len(chain) for chain in chains)
    longest = max(map(len, chains), default=0)
    samples = [chain for chain in chains if len(chain) == longest][:3]
    return {
        "starting_action_occurrences": len(chains),
        "length_in_actions_histogram": {
            str(length): count for length, count in sorted(histogram.items())
        },
        "longest_correlated_chain_actions": longest,
        "longest_chain_samples": samples,
    }


def iter_placed_points(state, position_by_gap):
    for anchor_index, point in enumerate(state["anchors"]):
        yield tuple(point), -1, (0, anchor_index, -1)
    for gap in range(len(state["parent_word"])):
        point = tuple(state["anchors"][gap])
        word = tuple(state["words"][gap])
        for slot, step in enumerate(word[:-1]):
            point = add(point, MENU[step])
            yield point, position_by_gap[gap], (1, gap, slot)


def endpoint_record(record, level):
    birth, identity, point = record
    if identity[0] == 0:
        stable_id = f"anchor:L{level}:A{identity[1]}"
        kind = "anchor"
        gap = None
        slot = None
    else:
        stable_id = (
            f"connector:L{level}:G{identity[1]}:I{identity[2]}"
        )
        kind = "connector_interior"
        gap = identity[1]
        slot = identity[2]
    return {
        "stable_id": stable_id,
        "kind": kind,
        "coordinate": list(point),
        "birth_order_position": birth,
        "birth_gap": gap,
        "interior_slot_zero_based": slot,
    }


def chronological_secant_scan(states):
    all_results = []
    entry_witnesses = {}
    for level in LEVELS:
        state = states[level]
        position_by_gap = {
            gap: position for position, gap in enumerate(state["order"])
        }
        source_gaps = tuple(
            gap
            for gap, step in enumerate(state["parent_word"])
            if step == SOURCE_STEP
        )
        # L8 actions determine L9 child starts even though no selected L9
        # connectors exist.  Hence actions at levels L,...,L+2n-1 are
        # available exactly when 2n <= 9-L.
        maximum_cycles = (9 - level) // 2
        for cycles in range(maximum_cycles + 1):
            direction = inverse_cycle_direction(cycles)
            query_moment_by_gap = {
                gap: cross(
                    add(tuple(state["anchors"][gap]), PHASES[0]["candidate_site"]),
                    direction,
                )
                for gap in source_gaps
            }
            requested_moments = set(query_moment_by_gap.values())
            earliest = {moment: [] for moment in requested_moments}
            point_count = 0
            for point, birth, identity in iter_placed_points(
                state, position_by_gap
            ):
                point_count += 1
                moment = cross(point, direction)
                retained = earliest.get(moment)
                if retained is None:
                    continue
                record = (birth, identity, point)
                duplicate = next(
                    (index for index, item in enumerate(retained) if item[2] == point),
                    None,
                )
                if duplicate is not None:
                    if record < retained[duplicate]:
                        retained[duplicate] = record
                        retained.sort()
                elif len(retained) < 2:
                    retained.append(record)
                    retained.sort()
                elif record < retained[1]:
                    retained.append(record)
                    retained.sort()
                    del retained[2:]

            live = []
            for gap in source_gaps:
                endpoints = earliest[query_moment_by_gap[gap]]
                stitch_position = position_by_gap[gap]
                if len(endpoints) < 2 or endpoints[1][0] >= stitch_position:
                    continue
                query_point = add(
                    tuple(state["anchors"][gap]), PHASES[0]["candidate_site"]
                )
                assert all(
                    cross(subtract(endpoint[2], query_point), direction)
                    == (0, 0, 0)
                    for endpoint in endpoints
                )
                assert endpoints[0][2] != endpoints[1][2]
                witness = {
                    "level": level,
                    "gap": gap,
                    "stitch_order_position": stitch_position,
                    "corridor_start": list(state["anchors"][gap]),
                    "candidate_site": list(PHASES[0]["candidate_site"]),
                    "absolute_query_point": list(query_point),
                    "cycles": cycles,
                    "primitive_direction": list(direction),
                    "endpoints": [
                        endpoint_record(item, level) for item in endpoints
                    ],
                    "actual_selected_word": list(state["words"][gap]),
                    "literal_phase_A_slots": list(
                        action_slots(state, gap, PHASES[0], True)
                    ),
                    "macro_phase_A_slots": list(
                        action_slots(state, gap, PHASES[0], False)
                    ),
                }
                live.append(witness)
                entry_witnesses[(level, gap, cycles)] = witness
            all_results.append({
                "level": level,
                "cycles": cycles,
                "available_selected_action_transitions": 2 * cycles,
                "primitive_direction": list(direction),
                "source_step_corridors": len(source_gaps),
                "placed_points_scanned": point_count,
                "chronologically_live_secant_corridors": len(live),
                "witnesses": live[:5],
            })
    return all_results, entry_witnesses


def countdown_join(states, child_starts, entries, literal):
    successes = []
    tested_nontrivial_entries = 0
    for (start_level, start_gap, cycles), witness in sorted(entries.items()):
        if cycles == 0:
            continue
        tested_nontrivial_entries += 1
        level = start_level
        gap = start_gap
        path = []
        complete = True
        for edge in range(2 * cycles):
            phase_index = edge % 2
            slots = action_slots(
                states[level], gap, PHASES[phase_index], literal
            )
            if not slots:
                complete = False
                break
            assert len(slots) == 1
            slot = slots[0]
            path.append({
                "level": level,
                "gap": gap,
                "phase": PHASES[phase_index]["name"],
                "slot": slot,
                "actual_selected_word": list(states[level]["words"][gap]),
            })
            if level == 8:
                # The last L8 edge reaches a computable L9 corridor, but no L9
                # selected word is claimed or needed for a 2n-edge countdown.
                assert edge + 1 == 2 * cycles
                break
            gap = child_starts[level][gap] + slot
            level += 1
        if complete:
            successes.append({
                "entry": witness,
                "correlated_action_path": path,
            })
    return {
        "nontrivial_chronological_g_n_entries": tested_nontrivial_entries,
        "complete_correlated_countdowns": len(successes),
        "successes": successes,
    }


def build_result(resources):
    validate_cycle_constants()
    cycle_source_snapshot = validate_cycle_source()
    states, child_starts, snapshots = load_and_validate_states()
    action_counts = action_census(states)
    literal_chains = realized_chains(states, child_starts, literal=True)
    macro_chains = realized_chains(states, child_starts, literal=False)
    secants, entries = chronological_secant_scan(states)
    literal_countdowns = countdown_join(
        states, child_starts, entries, literal=True
    )
    macro_countdowns = countdown_join(
        states, child_starts, entries, literal=False
    )

    literal_total = sum(
        phase.get("literal_selected_action_slots", 0)
        for level in action_counts.values()
        for phase in level.values()
    )
    macro_total = sum(
        phase.get("x_avoiding_macro_slots", 0)
        for level in action_counts.values()
        for phase in level.values()
    )
    live_total = sum(
        item["chronologically_live_secant_corridors"] for item in secants
    )
    live_nontrivial = sum(
        item["chronologically_live_secant_corridors"]
        for item in secants
        if item["cycles"] > 0
    )

    checker_path = Path(__file__).resolve()
    return {
        "date": "2026-07-18",
        "status": "exact finite realized-path obstruction for the fixed non-x two-cycle",
        "checker": {
            "path": str(checker_path.relative_to(ROOT)),
            "sha256": file_sha256(checker_path),
        },
        "resource_policy": resources,
        "inputs": snapshots,
        "cycle_source": cycle_source_snapshot,
        "cycle": {
            "source_step": SOURCE_STEP,
            "phases": [
                {
                    key: list(value) if isinstance(value, tuple) else value
                    for key, value in phase.items()
                }
                for phase in PHASES
            ],
            "inverse_direction_family": (
                "g_n=canonprim(N^(2n)*(3,-1,3))"
            ),
            "reveal_site": list(REVEAL_SITE),
        },
        "correlated_address_validation": {
            "levels": list(LEVELS),
            "every_selected_word_endpoint_checked": True,
            "every_L5_to_L8_flattened_parent_word_checked": True,
            "every_parent_prefix_to_child_anchor_checked": True,
            "alternate_connector_histories": False,
            "independent_address_streams": False,
        },
        "selected_action_census": action_counts,
        "literal_named_word_chains": literal_chains,
        "exact_macro_chains": macro_chains,
        "chronological_secant_reachability": {
            "semantics": (
                "all anchors have birth -1; connector interiors have their "
                "gap's constructor-order position; two distinct endpoints "
                "must have birth strictly before the queried stitch"
            ),
            "queries": secants,
        },
        "literal_countdown_join": literal_countdowns,
        "macro_countdown_join": macro_countdowns,
        "decisive_result": {
            "literal_selected_cycle_actions_L5_to_L8": literal_total,
            "exact_control_target_x_avoiding_macro_actions_L5_to_L8": macro_total,
            "correlated_literal_action_chain_maximum": literal_chains[
                "longest_correlated_chain_actions"
            ],
            "correlated_macro_action_chain_maximum": macro_chains[
                "longest_correlated_chain_actions"
            ],
            "chronologically_live_g_n_entry_lines_all_queries": live_total,
            "chronologically_live_g_n_entry_lines_n_ge_1": live_nontrivial,
            "literal_complete_nontrivial_countdowns": literal_countdowns[
                "complete_correlated_countdowns"
            ],
            "macro_complete_nontrivial_countdowns": macro_countdowns[
                "complete_correlated_countdowns"
            ],
            "fixed_cycle_reachable_in_this_realized_horizon": False,
            "reason": (
                "Neither selected cycle word occurs, no selected connector "
                "realizes either exact control/target macro edge, and no "
                "chronological inverse-family entry secant with n>=1 occurs."
            ),
        },
        "scope_limitations": [
            "finite L5--L8 gate2 realized history only",
            "does not exclude the same geometric cycle under a different ordered connector policy",
            "does not exclude a different direction-blind cycle",
            "does not independently rerun the global triple-free verification",
            "the computed L9 endpoint after an L8 action has no selected L9 connector",
            "a live g_0 line is an immediate reveal, not evidence of repeatability",
        ],
    }


def atomic_write(payload, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".nonx-cycle-reachability-", suffix=".json"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(stable_json(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def estimate(resources):
    snapshots = {
        name: stable_snapshot(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert {
        name: item["sha256"] for name, item in snapshots.items()
    } == EXPECTED_INPUT_SHA256
    cycle_source = stable_snapshot(ROOT / CYCLE_SOURCE_NAME)
    assert cycle_source["sha256"] == EXPECTED_CYCLE_SOURCE_SHA256
    return {
        "mode": "estimate",
        "resource_policy": resources,
        "input_bytes": (
            sum(item["bytes"] for item in snapshots.values())
            + cycle_source["bytes"]
        ),
        "levels": list(LEVELS),
        "direction_queries_per_level": {
            str(level): (9 - level) // 2 + 1 for level in LEVELS
        },
        "implementation": (
            "one pickle at a time for moment scans; only requested line "
            "moments and two earliest endpoints are retained"
        ),
        "expected_wall_seconds": "<10",
        "expected_peak_rss_MiB": "<100",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-summary", type=Path)
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; assertions are certificate checks")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resources = enforce_resource_policy()
    if args.mode == "estimate":
        print(stable_json(estimate(resources)), end="")
        return
    result = build_result(resources)
    rendered = stable_json(result)
    if args.verify_summary is not None:
        if args.verify_summary.read_text(encoding="utf-8") != rendered:
            raise AssertionError("checked-in compact summary is stale")
    atomic_write(result, args.output)
    print(
        f"wrote {args.output.resolve()} ({args.output.stat().st_size} bytes, "
        f"sha256 {file_sha256(args.output)})",
        flush=True,
    )


if __name__ == "__main__":
    main()
