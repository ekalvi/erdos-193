#!/usr/bin/env python3
"""Exact L7 -> L8 transport audit for the two shell-5 poison atoms.

The inherited-tile lifetime experiment found two atoms whose first witness
requires spatial shell 5.  This program enriches those two records with exact
placed-point identities and follows their *actual* affine images into L8.

This is deliberately a source-transport experiment, not a tail-contraction
certificate.  Both attaining witnesses are made from points born at L7.  They
are age zero at the source and age one after applying ``M_BAL3``.  With data
only through L8, they never enter an age-at-least-two residual state.

The audit has two successor scopes:

* ``actual_child_block`` scans every L8 corridor in the realized connector
  that replaced the source L7 gap; these are the exact causal child addresses.
* ``global_same_domain`` scans every realized L8 corridor of step type 122.
  This detects same-domain recurrences anywhere on the recorded orbit, but is
  not a substitute for scanning all 124 successor domains.

Every incidence calculation is exact integer arithmetic.  There is no
endpoint or distance cutoff.  Run single-threaded and at low priority:

    env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/deep_incidence_lineage.py run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from inherited_tile_lifetime import (  # noqa: E402
    EXPECTED_INPUT_SHA256,
    bits_count_hash,
    build_context,
    distance_shell,
    exact_birth_levels,
    exact_witness_scan,
    file_sha256,
    load_viz,
    pareto_spans,
)
from salvage_gate import (  # noqa: E402
    build_domain_model,
    cheb,
    cross,
    line_key,
    midpoint,
    primitive,
    sub,
)


LEVEL = 7
STEP = 122
TARGETS = {
    13171: {
        "atom_id": 905,
        "atom_desc": ("site", (3, 0, 4)),
        "witness_type": "old-old-secant",
        "expected_stream_sha256": (
            "b8c8d6d127b7cdde004efbd139a278e4220ce296df1c092e0f118999f9cedaeb"
        ),
        "expected_atom_word_count": 154,
        "expected_atom_word_mask_sha256": (
            "d2abd53fcdf66a9f11b519a01b6a139090dc8d2b04eab14129e4dbe85d068594"
        ),
        "expected_first_shell_word_count": 56,
        "expected_first_shell_word_mask_sha256": (
            "51fae9aa4965bcb0e866eb1affcb454e5cc48b8f5a785f608fb2a6b853f6fbc9"
        ),
    },
    21115: {
        "atom_id": 611,
        "atom_desc": ("line", ((2, 1, 1), (-4, 1, 7))),
        "witness_type": "old-new-new-line",
        "expected_stream_sha256": (
            "e5e1c77bb2e83af6956af0c7c7efcb8fd5c315cdba94c8a0753673a816bd0107"
        ),
        "expected_atom_word_count": 18,
        "expected_atom_word_mask_sha256": (
            "1c212c13f571c08847ffb4dd937d543eecbd5235a4fcd97efb339cd532565237"
        ),
        "expected_first_shell_word_count": 9,
        "expected_first_shell_word_mask_sha256": (
            "cbc8c345b46f680f9354bf3991d52c7798da7656d12d4b22f41b9ba6170d9e9a"
        ),
    },
}

USED_INPUTS = (
    "viz/walk3d-data.json",
    "connector_domains4.pkl",
    "dstar5_fragile.pkl",
    "gate2-l7-construction-L7.pkl",
    "gate2-l7-construction-L8.pkl",
    "gate_run.py",
    "design/inherited_tile_lifetime.py",
    "design/salvage_gate.py",
    "amplify_rich.py",
    "imbricate193.py",
    "search193.py",
)

EXTRA_INPUT_SHA256 = {
    "design/inherited_tile_lifetime.py": (
        "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4"
    ),
}

PRIMARY_CHANNELS = (
    "collision",
    "tagged-tagged-old-old",
    "tagged-other-old-old",
    "endpoint-old-new-new",
)

EXPECTED_ALL_DOMAIN = {
    "direction_index_sha256": {
        "connector:L7:G12291:I1": (
            "6604171eb1f59288f23e5cdeb2878b582f9cccbed044f108c5501d1f4ab623d6"
        ),
        "connector:L7:G12324:I2": (
            "3d16e86ff1cee95b2754169dc2fe19ae2e81f38f158d7fb6ead815fc65e2aa3d"
        ),
        "connector:L7:G19950:I2": (
            "d320614c89d9b331c8c7babcc1ae1018aca912442d8e4af373b07ae42dcb2f64"
        ),
    },
    "model_census_sha256": (
        "bff91ea1ae23aee38c0fab868e704fa83e739f95a80cd00f2b7d98f3cc94d3e9"
    ),
    "combined": {
        "effectful_gaps": 64,
        "zero_effect_gaps": 92667,
        "maximum_killed_words": 131472,
        "minimum_source_only_survivors": 2397,
        "minimum_source_only_survivors_gap": 41265,
        "minimum_domain_words": 2570,
        "maximum_killed_fraction": {
            "gap": 41266,
            "killed_words": 131472,
            "domain_words": 501044,
            "reduced_numerator": 32868,
            "reduced_denominator": 125261
        },
        "occurrence_stream_sha256": (
            "5bc8602fb0abf4552bd46d5679cdd458841947afac6e81f706fdd03c748ee5e9"
        ),
        "gap_vector_sha256": (
            "70cd9be63f2b7bb3101542adb80b86778fac8181c18f86db8144b48eda769908"
        ),
    },
    "sources": {
        13171: {
            "effectful_gaps": 40,
            "zero_effect_gaps": 92691,
            "effect_atom_occurrences": 111,
            "maximum_killed_words": 131472,
            "survivors_at_maximum_killed_words_record": 369572,
            "minimum_source_only_survivors": 2397,
            "minimum_source_only_survivors_gap": 41265,
            "minimum_domain_words": 2570,
            "maximum_killed_fraction": {
                "gap": 41266,
                "killed_words": 131472,
                "domain_words": 501044,
                "reduced_numerator": 32868,
                "reduced_denominator": 125261
            },
            "worst_gap": 41266,
            "channel_effectful_gap_counts": {
                "collision": 0,
                "tagged-tagged-old-old": 0,
                "tagged-other-old-old": 39,
                "endpoint-old-new-new": 6,
            },
            "gap_vector_sha256": (
                "9da41182b2a4c33d0ea046c16e1efaf490409fb9af823f12adc8a7d6a9adefbf"
            ),
            "occurrence_stream_sha256": (
                "af874f391f48f99c24e33df403a95bbd0eb8ef151cfadba7abc2a0b20d1f5990"
            ),
            "worst_mask": {
                "words": 131472,
                "mask_sha256": (
                    "c0f8e97558602073824b5a2e4f3afad3f9b3538c52f70063cedab73fca6a103a"
                ),
            },
            "direct_transport_gaps": [41155, 41158, 41161, 41263, 41267, 41268],
            "original_same_mode_gaps": [],
        },
        21115: {
            "effectful_gaps": 24,
            "zero_effect_gaps": 92707,
            "effect_atom_occurrences": 45,
            "maximum_killed_words": 11453,
            "survivors_at_maximum_killed_words_record": 489591,
            "minimum_source_only_survivors": 2475,
            "minimum_source_only_survivors_gap": 66955,
            "minimum_domain_words": 2570,
            "maximum_killed_fraction": {
                "gap": 66977,
                "killed_words": 3452,
                "domain_words": 38022,
                "reduced_numerator": 1726,
                "reduced_denominator": 19011
            },
            "worst_gap": 66997,
            "channel_effectful_gap_counts": {
                "collision": 0,
                "tagged-tagged-old-old": 0,
                "tagged-other-old-old": 22,
                "endpoint-old-new-new": 6,
            },
            "gap_vector_sha256": (
                "8c22482f5f8f8357f7e82759acdc8c791eaa4ceb62a952b80aaa834a6d46d04e"
            ),
            "occurrence_stream_sha256": (
                "46cb1d6bdf929cf925a552e7baa8d3545ee46be0a814d1b4534fcb45bc97f42d"
            ),
            "worst_mask": {
                "words": 11453,
                "mask_sha256": (
                    "727d9413614697dc26f884ad45b2cc86caf059bb1a374c7bbda1ad1db207a230"
                ),
            },
            "direct_transport_gaps": [66972, 66976, 66977, 66978, 66979, 66980],
            "original_same_mode_gaps": [66972, 66976, 66977, 66978, 66979, 66980],
        },
    },
}


def load_state(level):
    with (ROOT / f"gate2-l7-construction-L{level}.pkl").open("rb") as handle:
        return pickle.load(handle)


def as_list(value):
    if isinstance(value, tuple):
        return [as_list(item) for item in value]
    if isinstance(value, list):
        return [as_list(item) for item in value]
    return value


def stable_json_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_path_origins(viz):
    """Recover a stable birth identity for every point on every path level."""
    points_by_level = {
        level: [tuple(point) for point in data["points"]]
        for level, data in enumerate(viz["levels"])
    }
    origins = {
        0: [
            {
                "stable_id": f"base:L0:P{index}",
                "birth_level": 0,
                "birth_gap": None,
                "interior_ordinal": None,
                "birth_parent_endpoint_stable_ids": [],
            }
            for index in range(len(points_by_level[0]))
        ]
    }
    for level in range(1, len(viz["levels"])):
        parents = viz["levels"][level]["parents"]
        assert len(parents) == len(points_by_level[level])
        current = []
        block_start = {}
        for index, parent in enumerate(parents):
            first = index == 0 or parents[index - 1] != parent
            if first:
                block_start[parent] = index
                assert points_by_level[level][index] == apply(
                    M_BAL3, points_by_level[level - 1][parent]
                )
                current.append(dict(origins[level - 1][parent]))
            else:
                ordinal = index - block_start[parent]
                current.append({
                    "stable_id": f"connector:L{level}:G{parent}:I{ordinal}",
                    "birth_level": level,
                    "birth_gap": parent,
                    "interior_ordinal": ordinal,
                    "birth_parent_endpoint_stable_ids": [
                        origins[level - 1][parent]["stable_id"],
                        origins[level - 1][parent + 1]["stable_id"],
                    ],
                })
        stable_ids = [origin["stable_id"] for origin in current]
        assert len(stable_ids) == len(set(stable_ids))
        origins[level] = current
    return points_by_level, origins


def replay_target_prefixes(viz, births_by_level, d24, path_origins):
    """Replay L7 once and snapshot the two exact pre-stitch point sets."""
    state, tile_gaps, anchor_owners, schedule, guards = build_context(
        LEVEL, viz, births_by_level, d24
    )
    final_points = [tuple(point) for point in viz["levels"][LEVEL]["points"]]
    final_index = {point: index for index, point in enumerate(final_points)}
    assert len(final_index) == len(final_points)

    points = list(state["anchors"])
    births = list(births_by_level[LEVEL - 1])
    activation_actions = [-1] * len(points)
    activation_sweeps = [None] * len(points)
    owner_options = list(anchor_owners)
    path_indices = [final_index[point] for point in points]
    gap_tile = {gap: tile for tile, gaps in tile_gaps.items() for gap in gaps}
    snapshots = {}

    for rank, entry in enumerate(schedule):
        gap = entry["gap"]
        if gap in TARGETS:
            snapshots[gap] = {
                "state": state,
                "tile_gaps": tile_gaps,
                "guards": guards,
                "entry": entry,
                "rank": rank,
                "points": list(points),
                "births": list(births),
                "activation_actions": list(activation_actions),
                "activation_sweeps": list(activation_sweeps),
                "owner_options": list(owner_options),
                "path_indices": list(path_indices),
            }
        interiors = word_interiors(state["anchors"][gap], state["words"][gap])
        tile = gap_tile[gap]
        for ordinal, point in enumerate(interiors, 1):
            path_index = final_index[point]
            origin = path_origins[LEVEL][path_index]
            assert origin == {
                "stable_id": f"connector:L{LEVEL}:G{gap}:I{ordinal}",
                "birth_level": LEVEL,
                "birth_gap": gap,
                "interior_ordinal": ordinal,
                "birth_parent_endpoint_stable_ids": [
                    path_origins[LEVEL - 1][gap]["stable_id"],
                    path_origins[LEVEL - 1][gap + 1]["stable_id"],
                ],
            }
            points.append(point)
            births.append(LEVEL)
            activation_actions.append(rank)
            activation_sweeps.append(entry["sweep_tile"])
            owner_options.append((tile,))
            path_indices.append(path_index)

    assert set(snapshots) == set(TARGETS)
    assert len(points) == len(set(points)) == len(final_points)
    assert set(points) == set(final_points)
    return snapshots


def endpoint_record(snapshot, index, corridor_midpoint, path_origins):
    path_index = snapshot["path_indices"][index]
    origin = path_origins[LEVEL][path_index]
    assert origin["birth_level"] == snapshot["births"][index]
    point = snapshot["points"][index]
    distance = cheb(point, corridor_midpoint)
    return {
        "pipeline_index": index,
        "level7_path_index": path_index,
        "coordinate": as_list(point),
        "stable_id": origin["stable_id"],
        "birth_level": snapshot["births"][index],
        "age": LEVEL - snapshot["births"][index],
        "birth_gap": origin["birth_gap"],
        "interior_ordinal": origin["interior_ordinal"],
        "birth_parent_endpoint_stable_ids": origin[
            "birth_parent_endpoint_stable_ids"
        ],
        "activation_action": snapshot["activation_actions"][index],
        "activation_sweep_tile": snapshot["activation_sweeps"][index],
        "owner_options": list(snapshot["owner_options"][index]),
        "corridor_midpoint_chebyshev_distance": distance,
        "spatial_shell": distance_shell(distance),
    }


def witness_activation(snapshot, endpoint_indices):
    actions = snapshot["activation_actions"]
    sweeps = snapshot["activation_sweeps"]
    activation = max(actions[index] for index in endpoint_indices)
    if activation < 0:
        return activation, None
    latest = max(endpoint_indices, key=lambda index: actions[index])
    return activation, sweeps[latest]


def enumerate_target_witnesses(gap, snapshot, atom_desc, path_origins):
    """Enumerate every exact placed-point witness for one fixed atom."""
    state = snapshot["state"]
    start = state["anchors"][gap]
    middle = midpoint(start, state["anchors"][gap + 1])
    points = snapshot["points"]
    raw = []

    if atom_desc[0] == "site":
        offset = atom_desc[1]
        query = tuple(start[axis] + offset[axis] for axis in range(3))
        point_index = {point: index for index, point in enumerate(points)}
        if query in point_index:
            raw.append(("collision", (point_index[query],)))
        seen = {}
        for index, point in enumerate(points):
            if point == query:
                continue
            direction = primitive(sub(point, query))
            previous = seen.get(direction)
            if previous is None:
                seen[direction] = index
            else:
                assert not isinstance(previous, tuple)
                seen[direction] = (previous, index)
                raw.append(("old-old-secant", (previous, index)))
    else:
        direction, relative_moment = atom_desc[1]
        absolute_moment = tuple(
            cross(start, direction)[axis] + relative_moment[axis]
            for axis in range(3)
        )
        for index, point in enumerate(points):
            if cross(point, direction) == absolute_moment:
                raw.append(("old-new-new-line", (index,)))

    records = []
    for witness_type, indices in raw:
        endpoints = [
            endpoint_record(snapshot, index, middle, path_origins)
            for index in indices
        ]
        activation, sweep = witness_activation(snapshot, indices)
        spans = pareto_spans(
            tuple(tuple(endpoint["owner_options"]) for endpoint in endpoints),
            next(
                tile for tile, gaps in snapshot["tile_gaps"].items() if gap in gaps
            ),
        )
        records.append({
            "witness_type": witness_type,
            "placed_endpoints": endpoints,
            "maximum_endpoint_shell": max(
                endpoint["spatial_shell"] for endpoint in endpoints
            ),
            "maximum_endpoint_distance": max(
                endpoint["corridor_midpoint_chebyshev_distance"]
                for endpoint in endpoints
            ),
            "activation_action": activation,
            "activation_sweep_tile": sweep,
            "owner_pareto_spans": [list(span) for span in spans],
            "minimum_owner_radius": min(max(span) for span in spans),
        })
    records.sort(key=lambda record: stable_json_hash(record))
    return records


def atom_realizations(domain, atom_desc):
    """List every word/ordinal realization of the fixed local atom."""
    records = []
    for word_index, word in enumerate(domain):
        interiors = word_interiors((0, 0, 0), word)
        if atom_desc[0] == "site":
            for ordinal, point in enumerate(interiors, 1):
                if point == atom_desc[1]:
                    records.append({
                        "word_index": word_index,
                        "interior_ordinal": ordinal,
                        "site_offset": as_list(point),
                    })
        else:
            for left, a in enumerate(interiors):
                for right in range(left + 1, len(interiors)):
                    b = interiors[right]
                    if line_key(a, b) == atom_desc[1]:
                        records.append({
                            "word_index": word_index,
                            "interior_ordinals": [left + 1, right + 1],
                            "site_offsets": [as_list(a), as_list(b)],
                        })
    return records


def transform_absolute_line(a, b):
    return line_key(apply(M_BAL3, a), apply(M_BAL3, b))


def point_on_line(point, key):
    direction, moment = key
    return cross(point, direction) == moment


def local_line_absolute(start, key):
    direction, relative_moment = key
    start_moment = cross(start, direction)
    return direction, tuple(
        start_moment[axis] + relative_moment[axis] for axis in range(3)
    )


def scan_child_effect(domain, start, mode, carried, direct_image,
                      transported_endpoint_coordinates):
    """Exact word mask induced by one transported source on one corridor."""
    killed_bits = 0
    direct_bits = 0
    local_atoms = set()
    direct_atoms = set()
    for word_index, word in enumerate(domain):
        offsets = word_interiors((0, 0, 0), word)
        word_atoms = set()
        word_direct = set()
        if mode == "old-old-secant":
            for offset in offsets:
                point = tuple(start[axis] + offset[axis] for axis in range(3))
                if (point not in transported_endpoint_coordinates
                        and point_on_line(point, carried)):
                    word_atoms.add(("site", offset))
                if point == direct_image:
                    word_direct.add(("site", offset))
        else:
            for left, a in enumerate(offsets):
                for b in offsets[left + 1:]:
                    relative_key = line_key(a, b)
                    absolute_key = local_line_absolute(start, relative_key)
                    if point_on_line(carried, absolute_key):
                        word_atoms.add(("line", relative_key))
                    if absolute_key == direct_image:
                        word_direct.add(("line", relative_key))
        if word_atoms:
            killed_bits |= 1 << word_index
            local_atoms.update(word_atoms)
        if word_direct:
            direct_bits |= 1 << word_index
            direct_atoms.update(word_direct)
    return {
        "killed": bits_count_hash(killed_bits, len(domain)),
        "local_atoms": [as_list(atom) for atom in sorted(local_atoms)],
        "direct_image_killed": bits_count_hash(direct_bits, len(domain)),
        "direct_image_local_atoms": [
            as_list(atom) for atom in sorted(direct_atoms)
        ],
        "_killed_bits": killed_bits,
    }


def block_starts(parents):
    starts = {}
    for index, parent in enumerate(parents):
        if index == 0 or parents[index - 1] != parent:
            starts[parent] = index
    return starts


def l8_address(gap, viz, state7, state8, starts7):
    parents7 = viz["levels"][7]["parents"]
    parent_gap = parents7[gap]
    slot = gap - starts7[parent_gap]
    assert state7["words"][parent_gap][slot] == state8["parent_word"][gap]
    return {
        "l7_parent_gap": parent_gap,
        "actual_connector_step_slot_zero_based": slot,
        "actual_connector_word": list(state7["words"][parent_gap]),
    }


def child_transport(source, doms, viz, d24, state7, state8):
    parents7 = viz["levels"][7]["parents"]
    starts7 = block_starts(parents7)
    child_gaps = [
        gap for gap in range(len(state8["parent_word"]))
        if parents7[gap] == source["gap"]
    ]
    assert child_gaps == list(range(child_gaps[0], child_gaps[-1] + 1))
    assert [state8["parent_word"][gap] for gap in child_gaps] == list(
        state7["words"][source["gap"]]
    )

    _state, tile_gaps, _owners, schedule, _guards = build_context(
        8, viz, exact_birth_levels(viz), d24
    )
    schedule_by_gap = {
        entry["gap"]: (rank, entry) for rank, entry in enumerate(schedule)
    }
    results = []
    for lineage in source["transported_lineages"]:
        mode = lineage["witness_type"]
        carried = lineage["carried_geometry"]
        direct = lineage["direct_image_geometry"]
        lineage_results = []
        for gap in child_gaps:
            step = state8["parent_word"][gap]
            domain = doms[step]
            start = state8["anchors"][gap]
            effect = scan_child_effect(
                domain,
                start,
                mode,
                tuple(tuple(x) if isinstance(x, list) else x for x in carried)
                if mode == "old-old-secant" else tuple(carried),
                tuple(tuple(x) if isinstance(x, list) else x for x in direct)
                if mode == "old-new-new-line" else tuple(direct),
                {
                    tuple(endpoint["l8_coordinate"])
                    for endpoint in lineage["transported_endpoints"]
                },
            )
            chosen_index = domain.index(state8["words"][gap])
            assert not ((effect["_killed_bits"] >> chosen_index) & 1)
            rank, entry = schedule_by_gap[gap]
            tile = next(tile for tile, gaps in tile_gaps.items() if gap in gaps)
            effect.pop("_killed_bits")
            lineage_results.append({
                "l8_gap": gap,
                "l8_step": step,
                "address": l8_address(gap, viz, state7, state8, starts7),
                "pipeline_action_rank": rank,
                "pipeline_sweep_tile": entry["sweep_tile"],
                "pipeline_tile": tile,
                "domain_size": len(domain),
                "chosen_word_index": chosen_index,
                "chosen_word_avoids_transported_source": True,
                **effect,
            })
        results.append({
            "lineage_index": lineage["lineage_index"],
            "witness_type": mode,
            "corridors": lineage_results,
        })
    return {
        "source_gap": source["gap"],
        "child_gaps": child_gaps,
        "actual_child_steps": [state8["parent_word"][gap] for gap in child_gaps],
        "lineages": results,
    }


def atom_word_bits(model, domain_size):
    bits = [0] * len(model["atom_desc"])
    for word_index, atoms in enumerate(model["word_atoms"]):
        flag = 1 << word_index
        for atom in atoms:
            bits[atom] |= flag
    assert all(value < (1 << domain_size) for value in bits)
    return bits


def global_same_domain_transport(source, model, bits_by_atom, domain, viz,
                                 state7, state8):
    """Scan all L8 step-122 corridors for each transported source lineage."""
    parents7 = viz["levels"][7]["parents"]
    starts7 = block_starts(parents7)
    step_gaps = [
        gap for gap, step in enumerate(state8["parent_word"]) if step == STEP
    ]
    word_index = {tuple(word): index for index, word in enumerate(domain)}
    output = []
    for lineage in source["transported_lineages"]:
        mode = lineage["witness_type"]
        if mode == "old-old-secant":
            direction, moment = (
                tuple(lineage["carried_geometry"][0]),
                tuple(lineage["carried_geometry"][1]),
            )
            carried = (direction, moment)
            direct_point = tuple(lineage["direct_image_geometry"])
            endpoint_coordinates = {
                tuple(endpoint["l8_coordinate"])
                for endpoint in lineage["transported_endpoints"]
            }
        else:
            carried = tuple(lineage["carried_geometry"])
            direct_line = (
                tuple(lineage["direct_image_geometry"][0]),
                tuple(lineage["direct_image_geometry"][1]),
            )
        occurrences = []
        direct_occurrences = []
        exact_self = []
        for gap in step_gaps:
            start = state8["anchors"][gap]
            atoms = []
            direct_atoms = []
            if mode == "old-old-secant":
                for offset, atom in model["site_id"].items():
                    point = tuple(start[axis] + offset[axis] for axis in range(3))
                    if (point not in endpoint_coordinates
                            and point_on_line(point, carried)):
                        atoms.append(atom)
                    if point == direct_point:
                        direct_atoms.append(atom)
            else:
                relative = sub(carried, start)
                for direction, by_moment in model["line_by_direction"].items():
                    atom = by_moment.get(cross(relative, direction))
                    if atom is not None:
                        atoms.append(atom)
                transformed_relative = (
                    direct_line[0],
                    tuple(
                        direct_line[1][axis] - cross(start, direct_line[0])[axis]
                        for axis in range(3)
                    ),
                )
                atom = model["line_id"].get(transformed_relative)
                if atom is not None:
                    direct_atoms.append(atom)
            if not atoms and not direct_atoms:
                continue
            killed = 0
            for atom in atoms:
                killed |= bits_by_atom[atom]
            direct_killed = 0
            for atom in direct_atoms:
                direct_killed |= bits_by_atom[atom]
            chosen = word_index[tuple(state8["words"][gap])]
            assert not ((killed >> chosen) & 1)
            record = {
                "l8_gap": gap,
                "address": l8_address(gap, viz, state7, state8, starts7),
                "effect_atom_ids": sorted(atoms),
                "effect_atom_descriptions": [
                    as_list(model["atom_desc"][atom]) for atom in sorted(atoms)
                ],
                "killed": bits_count_hash(killed, len(domain)),
                "chosen_word_index": chosen,
                "chosen_word_avoids_transported_source": True,
                "direct_image_atom_ids": sorted(direct_atoms),
                "direct_image_killed": bits_count_hash(direct_killed, len(domain)),
            }
            occurrences.append(record)
            if direct_atoms:
                direct_occurrences.append(record)

            source_atom = source["atom_id"]
            if source_atom in atoms:
                original_vectors = source["lineages"][lineage["lineage_index"]][
                    "source_relative_endpoint_vectors"
                ]
                successor_vectors = [
                    list(sub(tuple(endpoint["l8_coordinate"]), start))
                    for endpoint in lineage["transported_endpoints"]
                ]
                if mode == "old-old-secant":
                    same_vectors = sorted(original_vectors) == sorted(successor_vectors)
                else:
                    same_vectors = original_vectors == successor_vectors
                if same_vectors:
                    exact_self.append(gap)
        output.append({
            "lineage_index": lineage["lineage_index"],
            "witness_type": mode,
            "scanned_step_122_gaps": len(step_gaps),
            "effectful_occurrences": len(occurrences),
            "occurrence_stream_sha256": stable_json_hash(occurrences),
            "occurrences": occurrences,
            "direct_image_occurrences": len(direct_occurrences),
            "direct_image_gaps": [record["l8_gap"] for record in direct_occurrences],
            "exact_same_atom_and_relative_endpoint_self_loops": exact_self,
        })
    return {
        "source_gap": source["gap"],
        "scope": "all recorded L8 corridors whose step/domain is exactly 122",
        "lineages": output,
    }


def compact_domain_model(domain):
    """Build the exact atom universe without retaining every word's atom tuple."""
    site_id = {}
    line_id = {}
    atom_desc = []

    def get_site(offset):
        if offset not in site_id:
            site_id[offset] = len(atom_desc)
            atom_desc.append(("site", offset))

    def get_line(key):
        if key not in line_id:
            line_id[key] = len(atom_desc)
            atom_desc.append(("line", key))

    for word in domain:
        offsets = word_interiors((0, 0, 0), word)
        for offset in offsets:
            get_site(offset)
        for left, a in enumerate(offsets):
            for b in offsets[left + 1:]:
                get_line(line_key(a, b))
    by_direction = defaultdict(dict)
    for (direction, moment), atom in line_id.items():
        by_direction[direction][moment] = atom
    return {
        "site_id": site_id,
        "line_id": line_id,
        "line_by_direction": dict(by_direction),
        "atom_desc": atom_desc,
    }


def build_l8_catalog(state8, viz, births_by_level, path_origins, d24):
    """Return every final L8 point with its exact pipeline activation."""
    _state, tile_gaps, anchor_owners, schedule, _guards = build_context(
        8, viz, births_by_level, d24
    )
    assert _state["anchors"] == state8["anchors"]
    tile_by_gap = {gap: tile for tile, gaps in tile_gaps.items() for gap in gaps}
    schedule_by_gap = {
        entry["gap"]: (rank, entry) for rank, entry in enumerate(schedule)
    }
    catalog = []
    for anchor_index, point in enumerate(state8["anchors"]):
        origin = path_origins[7][anchor_index]
        catalog.append({
            "coordinate": point,
            "stable_id": origin["stable_id"],
            "birth_level": births_by_level[7][anchor_index],
            "age": 8 - births_by_level[7][anchor_index],
            "activation_action": -1,
            "activation_sweep_tile": None,
            "owner_options": anchor_owners[anchor_index],
            "kind": "inherited-anchor",
            "l7_anchor_index": anchor_index,
            "birth_gap": origin["birth_gap"],
            "interior_ordinal": origin["interior_ordinal"],
        })
    for rank, entry in enumerate(schedule):
        gap = entry["gap"]
        tile = tile_by_gap[gap]
        interiors = word_interiors(state8["anchors"][gap], state8["words"][gap])
        for ordinal, point in enumerate(interiors, 1):
            catalog.append({
                "coordinate": point,
                "stable_id": f"connector:L8:G{gap}:I{ordinal}",
                "birth_level": 8,
                "age": 0,
                "activation_action": rank,
                "activation_sweep_tile": entry["sweep_tile"],
                "owner_options": (tile,),
                "kind": "connector-interior",
                "l7_anchor_index": None,
                "birth_gap": gap,
                "interior_ordinal": ordinal,
            })
    coordinates = [record["coordinate"] for record in catalog]
    stable_ids = [record["stable_id"] for record in catalog]
    activation_counts = Counter(record["activation_action"] for record in catalog)
    assert activation_counts[-1] == len(state8["anchors"])
    for rank, entry in enumerate(schedule):
        assert activation_counts[rank] == len(state8["words"][entry["gap"]]) - 1
    assert len(coordinates) == len(set(coordinates)) == 311738
    assert len(stable_ids) == len(set(stable_ids))
    final_points = {tuple(point) for point in viz["levels"][8]["points"]}
    assert set(coordinates) == final_points
    final_origin_by_coordinate = {
        tuple(point): origin
        for point, origin in zip(viz["levels"][8]["points"], path_origins[8])
    }
    for record in catalog:
        assert final_origin_by_coordinate[record["coordinate"]]["stable_id"] == (
            record["stable_id"]
        )
    return {
        "points": catalog,
        "schedule": schedule,
        "schedule_by_gap": schedule_by_gap,
        "tile_gaps": tile_gaps,
        "tile_by_gap": tile_by_gap,
        "coordinate_index": {
            record["coordinate"]: index for index, record in enumerate(catalog)
        },
    }


def build_source_frontiers(sources, catalog):
    """Materialize the three age-one endpoints and their exact line sources."""
    definitions = {}
    all_endpoints = {}
    for source in sources:
        endpoints = {}
        lines = []
        direct_lines = []
        for lineage in source["transported_lineages"]:
            for endpoint in lineage["transported_endpoints"]:
                coordinate = tuple(endpoint["l8_coordinate"])
                index = catalog["coordinate_index"][coordinate]
                point = catalog["points"][index]
                assert point["stable_id"] == endpoint["stable_id"]
                assert point["activation_action"] == -1
                assert point["age"] == endpoint["l8_age"] == 1
                assert point["l7_anchor_index"] == endpoint["l8_anchor_index"]
                endpoints[point["stable_id"]] = {
                    "catalog_index": index,
                    "stable_id": point["stable_id"],
                    "coordinate": coordinate,
                    "source_lineage_index": lineage["lineage_index"],
                }
                all_endpoints[point["stable_id"]] = endpoints[point["stable_id"]]
            if lineage["witness_type"] == "old-old-secant":
                lines.append({
                    "lineage_index": lineage["lineage_index"],
                    "key": (
                        tuple(lineage["carried_geometry"][0]),
                        tuple(lineage["carried_geometry"][1]),
                    ),
                    "endpoint_stable_ids": [
                        endpoint["stable_id"]
                        for endpoint in lineage["transported_endpoints"]
                    ],
                    "direct_image_point": tuple(lineage["direct_image_geometry"]),
                })
            else:
                direct_lines.append({
                    "lineage_index": lineage["lineage_index"],
                    "key": (
                        tuple(lineage["direct_image_geometry"][0]),
                        tuple(lineage["direct_image_geometry"][1]),
                    ),
                    "endpoint_stable_id": lineage["transported_endpoints"][0][
                        "stable_id"
                    ],
                })
        definitions[source["gap"]] = {
            "source": source,
            "endpoints": list(endpoints.values()),
            "carried_lines": lines,
            "direct_image_lines": direct_lines,
        }
    assert len(all_endpoints) == 3
    return definitions, all_endpoints


def direction_index_sha256(index, catalog):
    digest = hashlib.sha256()
    for direction, point_index in sorted(index.items()):
        point = catalog["points"][point_index]
        payload = (
            direction,
            point["stable_id"],
            point["activation_action"],
            point["coordinate"],
        )
        digest.update(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_direction_indexes(all_endpoints, catalog):
    """Index every final point by direction from each tagged endpoint."""
    indexes = {}
    summaries = []
    for stable_id, endpoint in sorted(all_endpoints.items()):
        origin = endpoint["coordinate"]
        index = {}
        for point_index, point in enumerate(catalog["points"]):
            if point["coordinate"] == origin:
                continue
            direction = primitive(sub(point["coordinate"], origin))
            assert direction not in index, (stable_id, direction)
            index[direction] = point_index
        assert len(index) == len(catalog["points"]) - 1
        indexes[stable_id] = index
        summaries.append({
            "stable_id": stable_id,
            "directions": len(index),
            "sha256": direction_index_sha256(index, catalog),
        })
    return indexes, summaries


def point_profile(point, corridor_midpoint):
    distance = cheb(point["coordinate"], corridor_midpoint)
    return {
        "stable_id": point["stable_id"],
        "coordinate": as_list(point["coordinate"]),
        "age": point["age"],
        "birth_level": point["birth_level"],
        "birth_gap": point["birth_gap"],
        "interior_ordinal": point["interior_ordinal"],
        "activation_action": point["activation_action"],
        "activation_sweep_tile": point["activation_sweep_tile"],
        "owner_options": list(point["owner_options"]),
        "corridor_midpoint_chebyshev_distance": distance,
        "spatial_shell": distance_shell(distance),
    }


def source_witness(channel, endpoint, partner, corridor_midpoint,
                   completion_tile, **extra):
    endpoint_profile = point_profile(endpoint, corridor_midpoint)
    profiles = [endpoint_profile]
    if partner is not None:
        profiles.append(point_profile(partner, corridor_midpoint))
    spans = pareto_spans(
        tuple(tuple(profile["owner_options"]) for profile in profiles),
        completion_tile,
    )
    if partner is None:
        descriptor = (
            f"{channel}:age{endpoint_profile['age']}@"
            f"shell{endpoint_profile['spatial_shell']}"
        )
    else:
        descriptor = (
            f"{channel}:tagged-age{endpoint_profile['age']}@"
            f"shell{endpoint_profile['spatial_shell']},"
            f"partner-age{profiles[1]['age']}@shell{profiles[1]['spatial_shell']}"
        )
    record = {
        "channel": channel,
        "correlated_birth_shell_descriptor": descriptor,
        "tagged_endpoint": endpoint_profile,
        "partner": profiles[1] if partner is not None else None,
        "owner_pareto_spans": [list(span) for span in spans],
        "minimum_owner_radius": min(max(span) for span in spans),
    }
    record.update(extra)
    return record


def add_atom_witness(witnesses, atom, record):
    encoded = stable_json_hash(record)
    known = {stable_json_hash(value) for value in witnesses[atom]}
    if encoded not in known:
        witnesses[atom].append(record)


def evaluate_endpoint_closure(gap, rank, start, midpoint_value, completion_tile,
                              model, definition, all_tagged_ids,
                              direction_indexes, catalog, chosen_word):
    """Exact poison atoms involving one of this source's tagged endpoints."""
    witnesses = defaultdict(list)
    endpoint_points = {}
    for endpoint in definition["endpoints"]:
        point = catalog["points"][endpoint["catalog_index"]]
        endpoint_points[endpoint["stable_id"]] = point

        collision_offset = sub(point["coordinate"], start)
        collision_atom = model["site_id"].get(collision_offset)
        if collision_atom is not None:
            add_atom_witness(
                witnesses,
                collision_atom,
                source_witness(
                    "collision", point, None, midpoint_value, completion_tile,
                    source_lineage_index=endpoint["source_lineage_index"],
                    candidate_site_offset=as_list(collision_offset),
                    candidate_site_coordinate=as_list(point["coordinate"]),
                ),
            )

        relative = sub(point["coordinate"], start)
        for direction, by_moment in model["line_by_direction"].items():
            atom = by_moment.get(cross(relative, direction))
            if atom is not None:
                relative_key = model["atom_desc"][atom][1]
                absolute_key = local_line_absolute(start, relative_key)
                assert point_on_line(point["coordinate"], absolute_key)
                add_atom_witness(
                    witnesses,
                    atom,
                    source_witness(
                        "endpoint-old-new-new", point, None, midpoint_value,
                        completion_tile,
                        source_lineage_index=endpoint["source_lineage_index"],
                        candidate_line_relative=as_list(relative_key),
                        candidate_line_absolute=as_list(absolute_key),
                    ),
                )

        direction_index = direction_indexes[endpoint["stable_id"]]
        for offset, atom in model["site_id"].items():
            query = tuple(start[axis] + offset[axis] for axis in range(3))
            if query == point["coordinate"]:
                continue
            direction = primitive(sub(query, point["coordinate"]))
            partner_index = direction_index.get(direction)
            if partner_index is None:
                continue
            partner = catalog["points"][partner_index]
            if partner["activation_action"] >= rank:
                continue
            if partner["coordinate"] == query:
                continue
            assert len({point["coordinate"], partner["coordinate"], query}) == 3
            assert primitive(sub(query, point["coordinate"])) == primitive(
                sub(partner["coordinate"], point["coordinate"])
            )
            channel = (
                "tagged-tagged-old-old"
                if partner["stable_id"] in all_tagged_ids
                else "tagged-other-old-old"
            )
            add_atom_witness(
                witnesses,
                atom,
                source_witness(
                    channel, point, partner, midpoint_value, completion_tile,
                    source_lineage_index=endpoint["source_lineage_index"],
                    candidate_site_offset=as_list(offset),
                    candidate_site_coordinate=as_list(query),
                ),
            )

    carried_atoms = set()
    direct_image_atoms = set()
    for line in definition["carried_lines"]:
        line_endpoints = {
            endpoint_points[stable_id]["coordinate"]
            for stable_id in line["endpoint_stable_ids"]
        }
        for offset, atom in model["site_id"].items():
            query = tuple(start[axis] + offset[axis] for axis in range(3))
            if query in line_endpoints or not point_on_line(query, line["key"]):
                continue
            carried_atoms.add(atom)
            line_profiles = [
                endpoint_points[stable_id]
                for stable_id in line["endpoint_stable_ids"]
            ]
            add_atom_witness(
                witnesses,
                atom,
                source_witness(
                    "carried-line-audit", line_profiles[0], line_profiles[1],
                    midpoint_value, completion_tile,
                    source_lineage_index=line["lineage_index"],
                    candidate_site_offset=as_list(offset),
                    candidate_site_coordinate=as_list(query),
                    carried_line_absolute=as_list(line["key"]),
                ),
            )
        direct_offset = sub(line["direct_image_point"], start)
        atom = model["site_id"].get(direct_offset)
        if atom is not None:
            direct_image_atoms.add(atom)
            assert atom in carried_atoms

    for direct in definition["direct_image_lines"]:
        direction, absolute_moment = direct["key"]
        relative_key = (
            direction,
            tuple(
                absolute_moment[axis] - cross(start, direction)[axis]
                for axis in range(3)
            ),
        )
        atom = model["line_id"].get(relative_key)
        if atom is not None:
            direct_image_atoms.add(atom)
            assert atom in witnesses

    for atom in carried_atoms:
        channels = {record["channel"] for record in witnesses[atom]}
        assert "tagged-tagged-old-old" in channels
        assert "carried-line-audit" in channels

    chosen_atoms = set()
    chosen_offsets = word_interiors((0, 0, 0), chosen_word)
    for offset in chosen_offsets:
        chosen_atoms.add(model["site_id"][offset])
    for left, a in enumerate(chosen_offsets):
        for b in chosen_offsets[left + 1:]:
            chosen_atoms.add(model["line_id"][line_key(a, b)])
    assert chosen_atoms.isdisjoint(witnesses)

    primary_atoms = {
        atom for atom, records in witnesses.items()
        if any(record["channel"] in PRIMARY_CHANNELS for record in records)
    }
    assert primary_atoms == set(witnesses)
    direct_transport_atoms = {
        atom for atom, records in witnesses.items()
        if any(record["channel"] in (
            "carried-line-audit", "endpoint-old-new-new"
        ) for record in records)
    }
    source_witness_type = definition["source"]["transported_lineages"][0][
        "witness_type"
    ]
    same_mode_atoms = (
        carried_atoms
        if source_witness_type == "old-old-secant"
        else {
            atom for atom, records in witnesses.items()
            if any(record["channel"] == "endpoint-old-new-new"
                   for record in records)
        }
    )
    return {
        "atom_witnesses": dict(witnesses),
        "direct_transport_atoms": direct_transport_atoms,
        "same_mode_atoms": same_mode_atoms,
        "direct_image_atoms": direct_image_atoms,
        "chosen_word_atom_count": len(chosen_atoms),
        "chosen_word_avoids_endpoint_closure": True,
    }


def requested_atom_word_bits(domain, model, requested):
    bits = {atom: 0 for atom in requested}
    for word_index, word in enumerate(domain):
        offsets = word_interiors((0, 0, 0), word)
        present = set()
        for offset in offsets:
            atom = model["site_id"][offset]
            if atom in requested:
                present.add(atom)
        for left, a in enumerate(offsets):
            for b in offsets[left + 1:]:
                atom = model["line_id"][line_key(a, b)]
                if atom in requested:
                    present.add(atom)
        flag = 1 << word_index
        for atom in present:
            bits[atom] |= flag
    return bits


def finalize_closure_occurrence(record, domain, model, bits_by_atom):
    atom_witnesses = record.pop("atom_witnesses")
    all_atoms = set(atom_witnesses)
    union_bits = 0
    for atom in all_atoms:
        union_bits |= bits_by_atom[atom]
    chosen_index = domain.index(record.pop("chosen_word"))
    assert not ((union_bits >> chosen_index) & 1)

    channel_atoms = {channel: set() for channel in PRIMARY_CHANNELS}
    descriptor_atoms = defaultdict(set)
    atom_records = []
    for atom in sorted(all_atoms):
        records = sorted(atom_witnesses[atom], key=stable_json_hash)
        for witness in records:
            channel = witness["channel"]
            if channel in channel_atoms:
                channel_atoms[channel].add(atom)
                descriptor_atoms[
                    witness["correlated_birth_shell_descriptor"]
                ].add(atom)
        atom_records.append({
            "atom_id": atom,
            "atom_description": as_list(model["atom_desc"][atom]),
            "word_membership": bits_count_hash(bits_by_atom[atom], len(domain)),
            "witnesses": records,
        })

    channel_bits = {}
    for channel, atoms in channel_atoms.items():
        value = 0
        for atom in atoms:
            value |= bits_by_atom[atom]
        channel_bits[channel] = value
    partition = {}
    cumulative = {}
    assigned = 0
    for channel in PRIMARY_CHANNELS:
        disjoint = channel_bits[channel] & ~assigned
        assigned |= channel_bits[channel]
        partition[channel] = bits_count_hash(disjoint, len(domain))
        cumulative[channel] = bits_count_hash(assigned, len(domain))
    assert assigned == union_bits

    def atoms_value(atoms):
        value = 0
        for atom in atoms:
            value |= bits_by_atom[atom]
        return value

    direct_transport_bits = atoms_value(record.pop("direct_transport_atoms"))
    same_mode_bits = atoms_value(record.pop("same_mode_atoms"))
    direct_image_bits = atoms_value(record.pop("direct_image_atoms"))
    assert same_mode_bits & ~direct_transport_bits == 0
    assert direct_transport_bits & ~union_bits == 0
    assert direct_image_bits & ~same_mode_bits == 0
    direct_transport = bits_count_hash(direct_transport_bits, len(domain))
    same_mode = bits_count_hash(same_mode_bits, len(domain))
    direct_image = bits_count_hash(direct_image_bits, len(domain))

    record.update({
        "chosen_word_index": chosen_index,
        "endpoint_closure": bits_count_hash(union_bits, len(domain)),
        "direct_transport": direct_transport,
        "original_same_mode_transport": same_mode,
        "direct_image_transport": direct_image,
        "primary_channel_membership_masks_overlap": {
            channel: bits_count_hash(value, len(domain))
            for channel, value in channel_bits.items()
        },
        "priority_disjoint_word_partition": {
            "priority": list(PRIMARY_CHANNELS),
            "masks": partition,
            "cumulative_masks": cumulative,
        },
        "correlated_birth_shell_action_masks_overlap": {
            descriptor: bits_count_hash(atoms_value(atoms), len(domain))
            for descriptor, atoms in sorted(descriptor_atoms.items())
        },
        "atoms": atom_records,
    })
    return record, union_bits


def closure_summary(occurrences, total_gaps, minimum_domain_words):
    if not occurrences:
        return {
            "scanned_gaps": total_gaps,
            "effectful_gaps": 0,
            "zero_effect_gaps": total_gaps,
            "occurrence_stream_sha256": stable_json_hash([]),
            "maximum_killed_words": 0,
            "survivors_at_maximum_killed_words_record": None,
            "minimum_source_only_survivors": minimum_domain_words,
            "minimum_source_only_survivors_gap": None,
            "minimum_domain_words": minimum_domain_words,
            "maximum_killed_fraction": None,
            "worst_gap": None,
            "channel_effectful_gap_counts": {channel: 0 for channel in PRIMARY_CHANNELS},
        }
    channel_counts = Counter()
    for record in occurrences:
        for channel, mask in record[
            "primary_channel_membership_masks_overlap"
        ].items():
            if mask["words"]:
                channel_counts[channel] += 1
    maximum_count = max(
        occurrences,
        key=lambda record: (record["endpoint_closure"]["words"], -record["l8_gap"]),
    )
    minimum_survivors = min(
        occurrences,
        key=lambda record: (
            record["domain_size"] - record["endpoint_closure"]["words"],
            record["l8_gap"],
        ),
    )
    maximum_fraction = max(
        occurrences,
        key=lambda record: (
            Fraction(record["endpoint_closure"]["words"], record["domain_size"]),
            -record["l8_gap"],
        ),
    )
    fraction_words = maximum_fraction["endpoint_closure"]["words"]
    fraction_domain = maximum_fraction["domain_size"]
    effect_minimum_survivors = (
        minimum_survivors["domain_size"]
        - minimum_survivors["endpoint_closure"]["words"]
    )
    all_gap_minimum = min(effect_minimum_survivors, minimum_domain_words)
    return {
        "scanned_gaps": total_gaps,
        "effectful_gaps": len(occurrences),
        "zero_effect_gaps": total_gaps - len(occurrences),
        "occurrence_stream_sha256": stable_json_hash(occurrences),
        "maximum_killed_words": maximum_count["endpoint_closure"]["words"],
        "survivors_at_maximum_killed_words_record": (
            maximum_count["domain_size"] - maximum_count["endpoint_closure"]["words"]
        ),
        "minimum_source_only_survivors": (
            all_gap_minimum
        ),
        "minimum_source_only_survivors_gap": (
            minimum_survivors["l8_gap"]
            if effect_minimum_survivors <= minimum_domain_words else None
        ),
        "minimum_domain_words": minimum_domain_words,
        "maximum_killed_fraction": {
            "gap": maximum_fraction["l8_gap"],
            "killed_words": fraction_words,
            "domain_words": fraction_domain,
            "reduced_numerator": Fraction(fraction_words, fraction_domain).numerator,
            "reduced_denominator": Fraction(fraction_words, fraction_domain).denominator,
        },
        "worst_gap": maximum_count["l8_gap"],
        "channel_effectful_gap_counts": {
            channel: channel_counts[channel] for channel in PRIMARY_CHANNELS
        },
    }


def all_domain_endpoint_closure(sources, doms, d24, viz, births_by_level,
                                path_origins, state7, state8, reference_model):
    """Complete recorded-orbit L8 poison closure involving the tagged endpoints."""
    catalog = build_l8_catalog(
        state8, viz, births_by_level, path_origins, d24
    )
    definitions, all_endpoints = build_source_frontiers(sources, catalog)
    direction_indexes, direction_summaries = build_direction_indexes(
        all_endpoints, catalog
    )
    tagged_ids = set(all_endpoints)
    starts7 = block_starts(viz["levels"][7]["parents"])
    step_gaps = defaultdict(list)
    for gap, step in enumerate(state8["parent_word"]):
        step_gaps[step].append(gap)
    assert set(step_gaps) == set(doms)
    minimum_domain_words = min(len(doms[step]) for step in step_gaps)
    assert minimum_domain_words == 2570

    occurrences_by_source = {source["gap"]: [] for source in sources}
    combined_occurrences = []
    model_census = []
    total_effect_atoms = Counter()
    for position, step in enumerate(sorted(step_gaps), 1):
        domain = doms[step]
        assert len(domain) == len(set(map(tuple, domain)))
        model = compact_domain_model(domain)
        if step == STEP:
            assert model["atom_desc"] == reference_model["atom_desc"]
        pending = []
        requested = set()
        for gap in step_gaps[step]:
            rank, entry = catalog["schedule_by_gap"][gap]
            start = state8["anchors"][gap]
            middle = midpoint(start, state8["anchors"][gap + 1])
            completion_tile = catalog["tile_by_gap"][gap]
            for source_gap, definition in definitions.items():
                evaluated = evaluate_endpoint_closure(
                    gap, rank, start, middle, completion_tile, model,
                    definition, tagged_ids, direction_indexes, catalog,
                    state8["words"][gap],
                )
                if not evaluated["atom_witnesses"]:
                    continue
                requested.update(evaluated["atom_witnesses"])
                pending.append({
                    "source_gap": source_gap,
                    "l8_gap": gap,
                    "l8_step": step,
                    "domain_size": len(domain),
                    "pipeline_action_rank": rank,
                    "pipeline_sweep_tile": entry["sweep_tile"],
                    "pipeline_tile": completion_tile,
                    "address": l8_address(gap, viz, state7, state8, starts7),
                    "chosen_word": tuple(state8["words"][gap]),
                    **evaluated,
                })
        if requested:
            bits_by_atom = requested_atom_word_bits(domain, model, requested)
            finalized_for_gap = defaultdict(list)
            for record in pending:
                finalized, union_bits = finalize_closure_occurrence(
                    record, domain, model, bits_by_atom
                )
                occurrences_by_source[finalized["source_gap"]].append(finalized)
                finalized_for_gap[finalized["l8_gap"]].append((finalized, union_bits))
                total_effect_atoms[finalized["source_gap"]] += len(finalized["atoms"])
            for gap, records in finalized_for_gap.items():
                combined_bits = 0
                source_masks = []
                for finalized, union_bits in records:
                    combined_bits |= union_bits
                    source_masks.append({
                        "source_gap": finalized["source_gap"],
                        "mask": finalized["endpoint_closure"],
                    })
                chosen_index = domain.index(tuple(state8["words"][gap]))
                assert not ((combined_bits >> chosen_index) & 1)
                combined_occurrences.append({
                    "l8_gap": gap,
                    "l8_step": step,
                    "domain_size": len(domain),
                    "chosen_word_index": chosen_index,
                    "chosen_word_avoids_all_three_tagged_endpoints": True,
                    "source_masks": sorted(source_masks, key=lambda item: item["source_gap"]),
                    "combined_endpoint_closure": bits_count_hash(
                        combined_bits, len(domain)
                    ),
                })
        model_census.append({
            "step": step,
            "gaps": len(step_gaps[step]),
            "domain_words": len(domain),
            "site_atoms": len(model["site_id"]),
            "line_atoms": len(model["line_id"]),
            "line_directions": len(model["line_by_direction"]),
            "requested_effect_atoms": len(requested),
            "effect_records": len(pending),
        })
        if position % 8 == 0 or position == len(step_gaps):
            print(
                f"all-domain endpoint closure: {position}/{len(step_gaps)} steps",
                flush=True,
            )

    for records in occurrences_by_source.values():
        records.sort(key=lambda record: (record["l8_gap"], record["source_gap"]))
    combined_occurrences.sort(key=lambda record: record["l8_gap"])
    per_source = []
    for source in sources:
        records = occurrences_by_source[source["gap"]]
        same_atom_gaps = [
            record["l8_gap"] for record in records
            if record["l8_step"] == STEP
            and any(atom["atom_id"] == source["atom_id"] for atom in record["atoms"])
        ]
        per_source.append({
            "source_gap": source["gap"],
            "summary": closure_summary(
                records, len(state8["parent_word"]), minimum_domain_words
            ),
            "effect_atom_occurrences": total_effect_atoms[source["gap"]],
            "coarse_same_step_same_atom_gaps": same_atom_gaps,
            "occurrences": records,
        })
    combined_minimum_survivors = min(
        combined_occurrences,
        key=lambda record: (
            record["domain_size"] - record["combined_endpoint_closure"]["words"],
            record["l8_gap"],
        ),
    )
    combined_maximum_fraction = max(
        combined_occurrences,
        key=lambda record: (
            Fraction(
                record["combined_endpoint_closure"]["words"],
                record["domain_size"],
            ),
            -record["l8_gap"],
        ),
    )
    combined_fraction = Fraction(
        combined_maximum_fraction["combined_endpoint_closure"]["words"],
        combined_maximum_fraction["domain_size"],
    )
    combined_effect_minimum = (
        combined_minimum_survivors["domain_size"]
        - combined_minimum_survivors["combined_endpoint_closure"]["words"]
    )
    combined_summary = {
        "scanned_gaps": len(state8["parent_word"]),
        "effectful_gaps": len(combined_occurrences),
        "zero_effect_gaps": len(state8["parent_word"]) - len(combined_occurrences),
        "occurrence_stream_sha256": stable_json_hash(combined_occurrences),
        "maximum_killed_words": max(
            (record["combined_endpoint_closure"]["words"]
             for record in combined_occurrences),
            default=0,
        ),
        "minimum_source_only_survivors": (
            min(combined_effect_minimum, minimum_domain_words)
        ),
        "minimum_source_only_survivors_gap": (
            combined_minimum_survivors["l8_gap"]
            if combined_effect_minimum <= minimum_domain_words else None
        ),
        "minimum_domain_words": minimum_domain_words,
        "maximum_killed_fraction": {
            "gap": combined_maximum_fraction["l8_gap"],
            "killed_words": combined_maximum_fraction[
                "combined_endpoint_closure"
            ]["words"],
            "domain_words": combined_maximum_fraction["domain_size"],
            "reduced_numerator": combined_fraction.numerator,
            "reduced_denominator": combined_fraction.denominator,
        },
    }
    return {
        "status": (
            "exact prefix-aware L8 closure for every forbidden triple involving "
            "one of the three tagged age-one endpoints"
        ),
        "scope": {
            "recorded_l8_stitches": len(state8["parent_word"]),
            "effective_step_domains": len(step_gaps),
            "final_l8_points_indexed": len(catalog["points"]),
            "minimum_domain_words": minimum_domain_words,
            "alternate_histories": False,
            "other_l7_endpoints": False,
            "age_at_least_2": False,
        },
        "direction_indexes": direction_summaries,
        "model_census": model_census,
        "model_census_sha256": stable_json_hash(model_census),
        "per_source": per_source,
        "combined_three_endpoint_summary": combined_summary,
        "combined_occurrences": combined_occurrences,
    }


def assert_narrow_transport_reproduced(all_domain, child, same_domain, doms):
    """Tie the all-topology closure to both earlier same-mode scans."""
    closure_by_source = {
        item["source_gap"]: {
            record["l8_gap"]: record for record in item["occurrences"]
        }
        for item in all_domain["per_source"]
    }
    child_checks = 0
    for block in child:
        source_records = closure_by_source[block["source_gap"]]
        for lineage in block["lineages"]:
            for corridor in lineage["corridors"]:
                record = source_records.get(corridor["l8_gap"])
                actual_same = (
                    record["original_same_mode_transport"]
                    if record is not None
                    else bits_count_hash(0, corridor["domain_size"])
                )
                actual_direct = (
                    record["direct_image_transport"]
                    if record is not None
                    else bits_count_hash(0, corridor["domain_size"])
                )
                assert actual_same == corridor["killed"]
                assert actual_direct == corridor["direct_image_killed"]
                child_checks += 1

    same_domain_checks = 0
    for old_scan in same_domain:
        source_records = closure_by_source[old_scan["source_gap"]]
        old_by_gap = {
            record["l8_gap"]: record
            for lineage in old_scan["lineages"]
            for record in lineage["occurrences"]
            if record["killed"]["words"] or record["direct_image_killed"]["words"]
        }
        new_by_gap = {
            gap: record for gap, record in source_records.items()
            if record["l8_step"] == STEP
            and (record["original_same_mode_transport"]["words"]
                 or record["direct_image_transport"]["words"])
        }
        assert set(old_by_gap) == set(new_by_gap)
        for gap in old_by_gap:
            assert old_by_gap[gap]["killed"] == new_by_gap[gap][
                "original_same_mode_transport"
            ]
            assert old_by_gap[gap]["direct_image_killed"] == new_by_gap[gap][
                "direct_image_transport"
            ]
            same_domain_checks += 1
        assert all(
            lineage["scanned_step_122_gaps"] == 838
            for lineage in old_scan["lineages"]
        )
    return {
        "actual_child_corridors_checked": child_checks,
        "global_step_122_effectful_corridors_checked": same_domain_checks,
        "all_empty_same_mode_masks_reproduced": True,
        "semantics": (
            "the original carried-line/endpoint-line modes and direct affine "
            "images are exact submasks of the all-topology endpoint closure"
        ),
    }


def assert_expected_all_domain(all_domain):
    """Pin the canonical complete recorded-orbit endpoint-closure result."""
    assert all_domain["scope"] == {
        "recorded_l8_stitches": 92731,
        "effective_step_domains": 124,
        "final_l8_points_indexed": 311738,
        "minimum_domain_words": 2570,
        "alternate_histories": False,
        "other_l7_endpoints": False,
        "age_at_least_2": False,
    }
    observed_directions = {
        row["stable_id"]: row["sha256"]
        for row in all_domain["direction_indexes"]
    }
    assert observed_directions == EXPECTED_ALL_DOMAIN["direction_index_sha256"]
    assert all(row["directions"] == 311737
               for row in all_domain["direction_indexes"])
    assert len(all_domain["model_census"]) == 124
    assert sum(row["domain_words"] for row in all_domain["model_census"]) == 12537146
    assert sum(row["gaps"] for row in all_domain["model_census"]) == 92731
    assert sum(row["requested_effect_atoms"]
               for row in all_domain["model_census"]) == 151
    assert sum(row["effect_records"] for row in all_domain["model_census"]) == 64
    assert all_domain["model_census_sha256"] == EXPECTED_ALL_DOMAIN[
        "model_census_sha256"
    ]

    combined = all_domain["combined_three_endpoint_summary"]
    expected_combined = EXPECTED_ALL_DOMAIN["combined"]
    assert combined["scanned_gaps"] == 92731
    for key in (
        "effectful_gaps", "zero_effect_gaps", "maximum_killed_words",
        "minimum_source_only_survivors", "minimum_source_only_survivors_gap",
        "minimum_domain_words", "maximum_killed_fraction",
        "occurrence_stream_sha256",
    ):
        assert combined[key] == expected_combined[key]
    assert stable_json_hash([
        record["l8_gap"] for record in all_domain["combined_occurrences"]
    ]) == expected_combined["gap_vector_sha256"]

    child_gaps = {44081, 44082, 44083, 70880, 70881, 70882}
    for item in all_domain["per_source"]:
        source_gap = item["source_gap"]
        expected = EXPECTED_ALL_DOMAIN["sources"][source_gap]
        summary = item["summary"]
        assert summary["scanned_gaps"] == 92731
        for key in (
            "effectful_gaps", "zero_effect_gaps", "maximum_killed_words",
            "survivors_at_maximum_killed_words_record",
            "minimum_source_only_survivors",
            "minimum_source_only_survivors_gap", "minimum_domain_words",
            "maximum_killed_fraction",
            "worst_gap", "occurrence_stream_sha256",
            "channel_effectful_gap_counts",
        ):
            assert summary[key] == expected[key]
        assert item["effect_atom_occurrences"] == expected[
            "effect_atom_occurrences"
        ]
        assert item["coarse_same_step_same_atom_gaps"] == []
        assert stable_json_hash([
            record["l8_gap"] for record in item["occurrences"]
        ]) == expected["gap_vector_sha256"]
        assert child_gaps.isdisjoint(
            record["l8_gap"] for record in item["occurrences"]
        )
        worst = next(
            record for record in item["occurrences"]
            if record["l8_gap"] == expected["worst_gap"]
        )
        assert worst["endpoint_closure"] == expected["worst_mask"]
        assert [
            record["l8_gap"] for record in item["occurrences"]
            if record["direct_transport"]["words"]
        ] == expected["direct_transport_gaps"]
        assert [
            record["l8_gap"] for record in item["occurrences"]
            if record["original_same_mode_transport"]["words"]
        ] == expected["original_same_mode_gaps"]
        assert all(
            record["direct_image_transport"]["words"] == 0
            for record in item["occurrences"]
        )


def build_source(gap, snapshot, model, domain, path_origins, state8):
    target = TARGETS[gap]
    atom = target["atom_id"]
    assert model["atom_desc"][atom] == target["atom_desc"]
    state = snapshot["state"]
    start = state["anchors"][gap]
    middle = midpoint(start, state["anchors"][gap + 1])
    info, _count, stream_hash = exact_witness_scan(
        model,
        start,
        middle,
        snapshot["points"],
        snapshot["births"],
        snapshot["activation_actions"],
        snapshot["activation_sweeps"],
        snapshot["owner_options"],
        LEVEL,
        next(tile for tile, gaps in snapshot["tile_gaps"].items() if gap in gaps),
    )
    assert stream_hash == target["expected_stream_sha256"]
    assert info[atom]["first_visible_max_shell"] == 5
    assert {
        value for value, record in enumerate(info)
        if record["first_visible_max_shell"] == 5
    } == {atom}

    membership_bits = 0
    for word_index, atoms in enumerate(model["word_atoms"]):
        if atom in atoms:
            membership_bits |= 1 << word_index
    assert membership_bits.bit_count() == target["expected_atom_word_count"]
    membership = bits_count_hash(membership_bits, len(domain))
    assert membership == {
        "words": target["expected_atom_word_count"],
        "mask_sha256": target["expected_atom_word_mask_sha256"],
    }
    word_first_shell = []
    for atoms in model["word_atoms"]:
        word_first_shell.append(min(
            (info[value]["first_visible_max_shell"] for value in atoms),
            default=math.inf,
        ))
    exact_shell_bits = sum(
        1 << index for index, shell in enumerate(word_first_shell) if shell == 5
    )
    assert exact_shell_bits.bit_count() == target["expected_first_shell_word_count"]
    assert exact_shell_bits & ~membership_bits == 0
    first_shell = bits_count_hash(exact_shell_bits, len(domain))
    assert first_shell == {
        "words": target["expected_first_shell_word_count"],
        "mask_sha256": target["expected_first_shell_word_mask_sha256"],
    }

    witnesses = enumerate_target_witnesses(
        gap, snapshot, target["atom_desc"], path_origins
    )
    attaining = [
        record for record in witnesses if record["maximum_endpoint_shell"] == 5
    ]
    assert attaining
    assert all(record["witness_type"] == target["witness_type"] for record in attaining)
    assert all(endpoint["age"] == 0 for record in attaining
               for endpoint in record["placed_endpoints"])

    realizations = atom_realizations(domain, target["atom_desc"])
    assert len({record["word_index"] for record in realizations}) == (
        target["expected_atom_word_count"]
    )

    source = {
        "gap": gap,
        "step": STEP,
        "atom_id": atom,
        "atom_description": as_list(target["atom_desc"]),
        "placed_points_at_stitch": len(snapshot["points"]),
        "pipeline_action_rank": snapshot["rank"],
        "pipeline_sweep_tile": snapshot["entry"]["sweep_tile"],
        "witness_stream_sha256": stream_hash,
        "all_target_atom_witnesses": witnesses,
        "first_shell_5_attaining_witnesses": attaining,
        "atom_word_membership": membership,
        "first_visible_shell_5_word_contribution": first_shell,
        "candidate_atom_realizations": realizations,
        "lineages": [],
        "transported_lineages": [],
    }

    for lineage_index, record in enumerate(attaining):
        endpoints = record["placed_endpoints"]
        relative_vectors = [
            list(sub(tuple(endpoint["coordinate"]), start)) for endpoint in endpoints
        ]
        source["lineages"].append({
            "lineage_index": lineage_index,
            "source_relative_endpoint_vectors": relative_vectors,
            "source_endpoint_stable_ids": [endpoint["stable_id"] for endpoint in endpoints],
        })
        transported_endpoints = []
        for endpoint in endpoints:
            coordinate = apply(M_BAL3, tuple(endpoint["coordinate"]))
            anchor_index = endpoint["level7_path_index"]
            assert state8["anchors"][anchor_index] == coordinate
            transported_endpoints.append({
                "stable_id": endpoint["stable_id"],
                "l8_coordinate": as_list(coordinate),
                "l8_age": 1,
                "l8_anchor_index": anchor_index,
            })
        if record["witness_type"] == "old-old-secant":
            carried = transform_absolute_line(
                tuple(endpoints[0]["coordinate"]),
                tuple(endpoints[1]["coordinate"]),
            )
            offset = target["atom_desc"][1]
            source_query = tuple(start[axis] + offset[axis] for axis in range(3))
            direct = apply(M_BAL3, source_query)
            assert point_on_line(direct, carried)
            assert all(
                point_on_line(tuple(endpoint["l8_coordinate"]), carried)
                for endpoint in transported_endpoints
            )
        else:
            carried = apply(M_BAL3, tuple(endpoints[0]["coordinate"]))
            representative = realizations[0]["site_offsets"]
            a = tuple(start[axis] + representative[0][axis] for axis in range(3))
            b = tuple(start[axis] + representative[1][axis] for axis in range(3))
            direct = transform_absolute_line(a, b)
            for realization in realizations[1:]:
                a2 = tuple(start[axis] + realization["site_offsets"][0][axis]
                           for axis in range(3))
                b2 = tuple(start[axis] + realization["site_offsets"][1][axis]
                           for axis in range(3))
                assert transform_absolute_line(a2, b2) == direct
            assert point_on_line(carried, direct)
        source["transported_lineages"].append({
            "lineage_index": lineage_index,
            "witness_type": record["witness_type"],
            "transported_endpoints": transported_endpoints,
            "carried_geometry": as_list(carried),
            "direct_image_geometry": as_list(direct),
        })
    return source


def run():
    observed_inputs = {name: file_sha256(ROOT / name) for name in USED_INPUTS}
    expected_inputs = {
        name: EXTRA_INPUT_SHA256.get(name, EXPECTED_INPUT_SHA256.get(name))
        for name in USED_INPUTS
    }
    assert all(expected_inputs.values())
    assert observed_inputs == expected_inputs

    doms, d24 = load_domains()
    domain = doms[STEP]
    assert len(domain) == len(set(map(tuple, domain)))
    model = build_domain_model(domain)
    assert len(domain) == 9046
    assert len(model["site_id"]) == 174
    assert len(model["line_id"]) == 1978
    assert len(model["atom_desc"]) == 2152

    viz = load_viz()
    births_by_level = exact_birth_levels(viz)
    _points_by_level, path_origins = build_path_origins(viz)
    snapshots = replay_target_prefixes(viz, births_by_level, d24, path_origins)
    state7 = load_state(7)
    state8 = load_state(8)

    sources = [
        build_source(gap, snapshots[gap], model, domain, path_origins, state8)
        for gap in TARGETS
    ]
    bits_by_atom = atom_word_bits(model, len(domain))
    child = [
        child_transport(source, doms, viz, d24, state7, state8)
        for source in sources
    ]
    same_domain = [
        global_same_domain_transport(
            source, model, bits_by_atom, domain, viz, state7, state8
        )
        for source in sources
    ]
    all_domain = all_domain_endpoint_closure(
        sources, doms, d24, viz, births_by_level, path_origins,
        state7, state8, model,
    )
    assert_expected_all_domain(all_domain)
    narrow_crosscheck = assert_narrow_transport_reproduced(
        all_domain, child, same_domain, doms
    )

    result = {
        "status": (
            "exact finite L7-to-L8 source-transport audit; no endpoint cutoff; "
            "complete for triples involving the three tagged endpoints on the "
            "recorded L8 prefixes, but not an age>=2 or alternate-history proof"
        ),
        "resource_policy": {"processes": 1, "thread_cap": 1, "nice": 15},
        "classification": {
            "source_ages": [0],
            "successor_ages": [1],
            "residual_age_threshold": 2,
            "age_at_least_2_testable_from_L5_L8": False,
            "reason": (
                "both shell-5 attaining witnesses are born at L7 and become "
                "only age one in the final available level L8"
            ),
        },
        "scope": {
            "exact_child_blocks": True,
            "global_step_122_corridors": True,
            "all_124_L8_domains": True,
            "all_92731_recorded_L8_prefixes": True,
            "all_poison_topologies_involving_the_three_tagged_endpoints": True,
            "alternate_connector_histories": False,
            "future_levels_beyond_L8": False,
        },
        "sources": sources,
        "actual_child_block_transport": child,
        "global_same_domain_transport": same_domain,
        "all_domain_endpoint_incidence_closure": all_domain,
        "narrow_transport_submask_crosscheck": narrow_crosscheck,
        "input_sha256": observed_inputs,
        "checker_sha256": file_sha256(Path(__file__).resolve()),
    }
    return result


def estimate(viz):
    state8 = load_state(8)
    parents7 = viz["levels"][7]["parents"]
    child_gaps = sum(
        1 for gap in range(len(state8["parent_word"]))
        if parents7[gap] in TARGETS
    )
    return {
        "status": "structural estimate; no poison geometry scanned",
        "source_probes": len(TARGETS),
        "tagged_age_one_endpoints": 3,
        "actual_child_corridors": child_gaps,
        "global_step_122_corridors": Counter(state8["parent_word"])[STEP],
        "all_recorded_l8_stitches": len(state8["parent_word"]),
        "effective_step_types_present": len(set(state8["parent_word"])),
        "final_l8_points_for_direction_indexes": 311738,
        "step_122_domain_words": 9046,
        "resource_policy": {"processes": 1, "thread_cap": 1, "nice": 15},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/deep-incidence-lineage.json")
    )
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    if args.mode == "estimate":
        result = estimate(load_viz())
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    result = run()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload)
    print(f"wrote {args.output} ({len(payload)} bytes)", flush=True)


if __name__ == "__main__":
    main()
