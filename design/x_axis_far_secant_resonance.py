#!/usr/bin/env python3
"""Exact realized-path x-axis far-secant and short-return audit.

The only rational periodic projective direction of ``M_BAL3`` is the x-axis.
An x-parallel line is therefore represented by its lateral coordinate
``z = (y, z)``.  Under the common affine scaling map its lateral coordinate is
transported by

    B = [[0, -3], [3, -1]].

This checker uses only the connector choices actually recorded in the L5--L8
construction pickles.  It separately replays the original gate stitch order
and the later inherited-tile pipeline order.  At every cursor in each order it
enumerates every old x-parallel secant (two already placed points with equal
y,z), projects that line onto the pending connector's exact site atoms, and
computes the exact killed-word mask.  There is no endpoint or distance cutoff.

The recorded word in a level-L corridor also gives exact child slots at level
L+1.  If ``c`` is the selected word prefix before one such slot and ``z`` is
the line coordinate relative to the parent corridor start, the inherited line
has exact child-relative coordinate

    z' = B (z - c_perp).

Starting at every strict x-secant effect, the checker closes those jointly
realized lineage edges through every selected descendant slot to L8.  It
materializes intermediate states even when their exact strict effect mask is
zero, then solves the period-r equations whenever the terminal state is again
effectful,

    (B^r - I) z0 = sum_{i=0}^{r-1} B^(r-i) c_i,    r = 1,2,3.

An exact return of the projected ``(step, z, atoms, killed-word mask)`` key is
a witnessed cycle in that coarse projection and must be promoted or refined.
It is *not* an infinite policy cycle: the pickles do not prove that equal
finite keys have congruent future selected continuations.  Period four cannot
be tested from L5--L8 because it needs an actual selected L9 construction.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_far_secant_resonance.py run \
        --output /tmp/x-axis-far-secant-resonance.json

A lightweight exact structural estimate (no connector domains scanned) is:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_far_secant_resonance.py estimate
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import pickle
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import FRAGILE_CUT, IDX, MENU, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from inherited_tile_lifetime import pipeline_schedule, tile_layout  # noqa: E402


LEVELS = tuple(range(5, 9))
B_LATERAL = ((0, -3), (3, -1))
TARGET_L8_BLOCK = {
    "A": 67_009,
    "B": 67_011,
    "C": 67_008,
    "D": 67_013,
}
TARGET_L8_GAPS = frozenset(TARGET_L8_BLOCK.values())
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

EXPECTED_INPUT_SHA256 = {
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
    ),
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "dstar5_fragile.pkl": (
        "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3"
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
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
    "design/inherited_tile_lifetime.py": (
        "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4"
    ),
}

# These are planning expectations only in estimate mode.  Run mode recomputes
# and asserts the first value from the pinned domain artifacts.
EXPECTED_EFFECTIVE_DOMAIN_WORDS = 12_537_146


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


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def sub(first, second):
    return tuple(first[axis] - second[axis] for axis in range(3))


def cross3(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def lateral(point):
    return point[1], point[2]


def add2(first, second):
    return first[0] + second[0], first[1] + second[1]


def sub2(first, second):
    return first[0] - second[0], first[1] - second[1]


def mat2_vector(matrix, vector):
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def mat2_product(first, second):
    return tuple(tuple(
        sum(first[row][inner] * second[inner][column] for inner in range(2))
        for column in range(2)
    ) for row in range(2))


def mat2_power(matrix, exponent):
    result = ((1, 0), (0, 1))
    base = matrix
    while exponent:
        if exponent & 1:
            result = mat2_product(result, base)
        base = mat2_product(base, base)
        exponent >>= 1
    return result


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "estimate/run requires every thread-cap variable to equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process priority on this platform")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise RuntimeError(
            "run under at least `nice -n 10` (recommended: 15); "
            f"observed nice value is {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "minimum_nice": 10,
            "observed_nice": priority}


def observed_inputs():
    observed = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    if observed != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "pinned input drift:\n" + json.dumps({
                "expected": EXPECTED_INPUT_SHA256,
                "observed": observed,
            }, sort_keys=True, indent=2)
        )
    return observed


def load_state(level):
    with (ROOT / f"gate2-l7-construction-L{level}.pkl").open("rb") as handle:
        return pickle.load(handle)


def base_level4_records():
    data = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    points = [tuple(point) for point in data["levels"][4]["points"]]
    assert len(points) == len(set(points))
    return [{
        "stable_id": f"base-window:L4:P{index}",
        "coordinate": point,
        "birth_level": 4,
        "birth_gap": None,
        "interior_ordinal": None,
    } for index, point in enumerate(points)]


def completed_x_lines(records):
    groups = defaultdict(list)
    for record in records:
        groups[lateral(record["coordinate"])].append(record)
    histogram = Counter(len(group) for group in groups.values())
    if max(histogram, default=0) > 2:
        raise AssertionError(
            "completed realized path contains three points on an x-line",
            dict(sorted(histogram.items())),
        )
    by_pair = {}
    for line_lateral, endpoints in groups.items():
        if len(endpoints) != 2:
            continue
        ordered = tuple(sorted(endpoints, key=lambda item: (
            item["coordinate"][0], item["stable_id"]
        )))
        pair = tuple(sorted(endpoint["stable_id"] for endpoint in ordered))
        by_pair[pair] = {
            "pair": pair,
            "lateral": line_lateral,
            "endpoints": ordered,
        }
    return by_pair, dict(sorted(histogram.items()))


def build_realized_levels():
    """Build exact construction-prefix availability and child-slot maps."""
    parent_records = base_level4_records()
    parent_lines, _base_histogram = completed_x_lines(parent_records)
    levels = {}

    for level in LEVELS:
        state = load_state(level)
        gaps = len(state["parent_word"])
        if set(state["words"]) != set(range(gaps)):
            raise AssertionError(f"L{level} does not record one word per gap")
        if sorted(state["order"]) != list(range(gaps)):
            raise AssertionError(f"L{level} stitch order is not a permutation")
        rank = {gap: position for position, gap in enumerate(state["order"])}

        expected_anchors = [
            apply(M_BAL3, record["coordinate"]) for record in parent_records
        ]
        if expected_anchors != state["anchors"]:
            raise AssertionError(f"L{level} anchor/parent mismatch")
        anchors = []
        for record, coordinate in zip(parent_records, expected_anchors):
            transformed = dict(record)
            transformed["coordinate"] = coordinate
            transformed["availability_rank"] = -1
            transformed["availability_rank_by_order"] = {"gate": -1}
            transformed["construction_role"] = "anchor"
            anchors.append(transformed)

        completed = [anchors[0]]
        construction_records = list(anchors)
        block_start = {}
        corridors = []
        for gap in range(gaps):
            block_start[gap] = len(completed) - 1
            word = tuple(state["words"][gap])
            interiors = word_interiors(state["anchors"][gap], word)
            interior_records = []
            for ordinal, coordinate in enumerate(interiors, 1):
                record = {
                    "stable_id": f"connector:L{level}:G{gap}:I{ordinal}",
                    "coordinate": coordinate,
                    "birth_level": level,
                    "birth_gap": gap,
                    "interior_ordinal": ordinal,
                    "availability_rank": rank[gap],
                    "availability_rank_by_order": {"gate": rank[gap]},
                    "construction_role": "connector-interior",
                }
                interior_records.append(record)
            construction_records.extend(interior_records)
            completed.extend(interior_records)
            completed.append(anchors[gap + 1])
            step = state["parent_word"][gap]
            expected_displacement = apply(M_BAL3, MENU[step])
            observed_displacement = sub(
                state["anchors"][gap + 1], state["anchors"][gap]
            )
            if observed_displacement != expected_displacement:
                raise AssertionError(
                    "corridor displacement is not M_BAL3(parent step)",
                    level, gap, step, observed_displacement,
                    expected_displacement,
                )
            corridors.append({
                "level": level,
                "gap": gap,
                "schedule_rank_by_order": {"gate": rank[gap]},
                "step": step,
                "start": state["anchors"][gap],
                "end": state["anchors"][gap + 1],
                "actual_word": word,
                "block_start": block_start[gap],
            })

        completed_coordinates = [record["coordinate"] for record in completed]
        if len(completed_coordinates) != len(set(completed_coordinates)):
            raise AssertionError(f"L{level} completed path repeats a point")
        if len(construction_records) != len(completed):
            raise AssertionError(f"L{level} construction/completed size mismatch")

        groups = defaultdict(list)
        for record in construction_records:
            groups[lateral(record["coordinate"])].append(record)
        group_histogram = Counter(len(group) for group in groups.values())
        if max(group_histogram, default=0) > 2:
            raise AssertionError(
                f"L{level} has three completed points on one x-line",
                dict(sorted(group_histogram.items())),
            )

        line_by_lateral = {}
        line_by_pair = {}
        line_records = []
        for line_lateral, endpoints in sorted(groups.items()):
            if len(endpoints) != 2:
                continue
            ordered = tuple(sorted(endpoints, key=lambda item: (
                item["coordinate"][0], item["stable_id"]
            )))
            pair = tuple(sorted(endpoint["stable_id"] for endpoint in ordered))
            activation = max(
                endpoint["availability_rank"] for endpoint in ordered
            )
            inherited = parent_lines.get(pair)
            if inherited is not None:
                predicted = mat2_vector(B_LATERAL, inherited["lateral"])
                if predicted != line_lateral:
                    raise AssertionError(
                        "inherited x-line violates exact B transport",
                        level, pair, inherited["lateral"], predicted,
                        line_lateral,
                    )
                if activation != -1:
                    raise AssertionError("inherited line endpoints must be anchors")
            elif all(endpoint["construction_role"] == "anchor"
                     for endpoint in ordered):
                raise AssertionError("new x-line cannot be made by two anchors")

            line_id = stable_hash(pair)
            public_endpoints = [{
                "stable_id": endpoint["stable_id"],
                "coordinate": as_json(endpoint["coordinate"]),
                "birth_level": endpoint["birth_level"],
                "birth_gap": endpoint["birth_gap"],
                "interior_ordinal": endpoint["interior_ordinal"],
                "availability_rank_by_order": dict(
                    endpoint["availability_rank_by_order"]
                ),
                "construction_role": endpoint["construction_role"],
            } for endpoint in ordered]
            line = {
                "level": level,
                "line_id": line_id,
                "endpoint_stable_ids": list(pair),
                "lateral_yz": as_json(line_lateral),
                "endpoint_x_coordinates": [
                    endpoint["coordinate"][0] for endpoint in ordered
                ],
                "activation_rank_by_order": {"gate": activation},
                "active_before_stitches_by_order": {
                    "gate": gaps - activation - 1
                },
                "inherited_from_completed_L" + str(level - 1): (
                    inherited is not None
                ),
                "endpoints": public_endpoints,
            }
            line_records.append(line)
            internal = {
                **line,
                "pair": pair,
                "lateral": line_lateral,
                "endpoint_coordinates": tuple(
                    endpoint["coordinate"] for endpoint in ordered
                ),
                "endpoint_records": ordered,
            }
            line_by_lateral[line_lateral] = internal
            line_by_pair[pair] = internal

        if len(line_by_lateral) != len(line_records):
            raise AssertionError("two distinct x-lines share a lateral coordinate")

        level_record = {
            "level": level,
            "state": state,
            "gaps": gaps,
            "corridors": corridors,
            "corridor_by_gap": {item["gap"]: item for item in corridors},
            "completed_points": len(completed),
            "line_by_lateral": line_by_lateral,
            "line_by_pair": line_by_pair,
            "line_records": line_records,
            "point_lateral_multiplicity_histogram": dict(
                sorted(group_histogram.items())
            ),
        }
        levels[level] = level_record

        parent_records = completed
        parent_lines = {
            pair: {
                "pair": pair,
                "lateral": line["lateral"],
            }
            for pair, line in line_by_pair.items()
        }

    return levels


def install_pipeline_orders(levels, d24):
    """Add exact inherited-tile pipeline ranks without changing geometry."""
    full_viz = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    viz = {"levels": [{} for _level in full_viz["levels"]]}
    for level in LEVELS:
        viz["levels"][level - 1] = {
            "parents": full_viz["levels"][level - 1]["parents"]
        }
    del full_viz
    gc.collect()
    for level in LEVELS:
        data = levels[level]
        state = data["state"]
        tile_gaps, _anchor_owners = tile_layout(level, state, viz)
        del _anchor_owners
        entries, guards = pipeline_schedule(state, tile_gaps, d24)
        order = [entry["gap"] for entry in entries]
        if sorted(order) != list(range(data["gaps"])):
            raise AssertionError(f"L{level} pipeline is not a permutation")
        rank = {gap: position for position, gap in enumerate(order)}
        data["pipeline_entry_by_gap"] = {
            entry["gap"]: dict(entry)
            for entry in entries
            if level == 8 and entry["gap"] in TARGET_L8_GAPS
        }
        data["schedule_summaries"] = {
            "gate": {
                "order_sha256": stable_hash(state["order"]),
                "different_from_other_order": state["order"] != order,
            },
            "pipeline": {
                "entry_stream_sha256": stable_hash(entries),
                "guard_map_sha256": stable_hash(guards),
                "guards": len(guards),
                "different_from_other_order": state["order"] != order,
            },
        }

        for corridor in data["corridors"]:
            corridor["schedule_rank_by_order"]["pipeline"] = rank[
                corridor["gap"]
            ]

        public_by_id = {
            line["line_id"]: line for line in data["line_records"]
        }
        for internal in data["line_by_pair"].values():
            endpoint_ranks = []
            for endpoint in internal["endpoint_records"]:
                if endpoint["construction_role"] == "anchor":
                    endpoint_rank = -1
                else:
                    if endpoint["birth_level"] != level:
                        raise AssertionError(
                            "non-anchor endpoint must be born at current level"
                        )
                    endpoint_rank = rank[endpoint["birth_gap"]]
                endpoint["availability_rank_by_order"]["pipeline"] = (
                    endpoint_rank
                )
                endpoint_ranks.append(endpoint_rank)
            activation = max(endpoint_ranks)
            internal["activation_rank_by_order"]["pipeline"] = activation
            internal["active_before_stitches_by_order"]["pipeline"] = (
                data["gaps"] - activation - 1
            )

            public = public_by_id[internal["line_id"]]
            public["activation_rank_by_order"]["pipeline"] = activation
            public["active_before_stitches_by_order"]["pipeline"] = (
                data["gaps"] - activation - 1
            )
            for public_endpoint, endpoint_rank in zip(
                public["endpoints"], endpoint_ranks
            ):
                public_endpoint["availability_rank_by_order"]["pipeline"] = (
                    endpoint_rank
                )

        if level == 8:
            # Independent pin for the schedule used by the frozen-prefix work.
            if rank[TARGET_L8_BLOCK["A"]] != 67_010:
                raise AssertionError(
                    "pipeline schedule drift at the A cursor",
                    rank[TARGET_L8_BLOCK["A"]],
                )
        del data["state"]

    return levels


def mask_profile(mask, domain_words):
    byte_length = (domain_words + 7) // 8
    raw = mask.to_bytes(byte_length, "little")
    if domain_words % 8:
        assert raw[-1] >> (domain_words % 8) == 0
    return {
        "killed_words": mask.bit_count(),
        "mask_sha256": hashlib.sha256(raw).hexdigest(),
    }


def model_mask_profile(model, mask):
    """Avoid re-hashing the all-zero domain mask at every corridor."""
    if mask == 0:
        return model["zero_mask_profile"]
    return mask_profile(mask, model["domain_words"])


def build_lateral_domain_model(domain, step, needed_words):
    """Build exact site-to-word masks; x-lines never target line atoms."""
    expected_endpoint = apply(M_BAL3, MENU[step])
    byte_length = (len(domain) + 7) // 8
    site_bytes = {}
    word_order_digest = hashlib.sha256()
    needed_indices = defaultdict(list)

    for word_index, raw_word in enumerate(domain):
        word = tuple(raw_word)
        word_order_digest.update(len(word).to_bytes(1, "little"))
        for menu_index in word:
            word_order_digest.update(menu_index.to_bytes(1, "little"))
        if word in needed_words:
            needed_indices[word].append(word_index)

        position = (0, 0, 0)
        sites = []
        for ordinal, menu_index in enumerate(word):
            position = add(position, MENU[menu_index])
            if ordinal + 1 < len(word):
                sites.append(position)
        if position != expected_endpoint:
            raise AssertionError(
                "connector word endpoint mismatch", step, word_index,
                position, expected_endpoint,
            )
        if len(sites) != len(set(sites)):
            raise AssertionError("domain word repeats an interior site")
        for site in sites:
            bits = site_bytes.get(site)
            if bits is None:
                bits = bytearray(byte_length)
                site_bytes[site] = bits
            bits[word_index >> 3] |= 1 << (word_index & 7)

    missing = sorted(needed_words - set(needed_indices))
    if missing:
        raise AssertionError("recorded selected words absent from domain", step,
                             missing[:5], len(missing))

    site_masks = {}
    for site in list(site_bytes):
        bits = site_bytes.pop(site)
        site_masks[site] = int.from_bytes(bits, "little")
        del bits
    del site_bytes
    lateral_sites = defaultdict(list)
    for site in site_masks:
        lateral_sites[lateral(site)].append(site)
    lateral_sites = {
        key: tuple(sorted(sites)) for key, sites in lateral_sites.items()
    }

    site_mask_digest = hashlib.sha256()
    for site in sorted(site_masks):
        profile = mask_profile(site_masks[site], len(domain))
        site_mask_digest.update(stable_bytes((
            site, profile["killed_words"], profile["mask_sha256"]
        )))
        site_mask_digest.update(b"\n")

    return {
        "step": step,
        "domain_words": len(domain),
        "expected_endpoint": expected_endpoint,
        "site_masks": site_masks,
        "lateral_sites": lateral_sites,
        "needed_indices": dict(needed_indices),
        "sites": len(site_masks),
        "lateral_site_classes": len(lateral_sites),
        "word_order_sha256": word_order_digest.hexdigest(),
        "site_word_mask_stream_sha256": site_mask_digest.hexdigest(),
        "zero_mask_profile": mask_profile(0, len(domain)),
    }


def occurrence_id(order_name, level, gap, line_id):
    return f"{order_name}:L{level}:G{gap}:X{line_id}"


def scan_corridor(corridor, level_data, model, order_name):
    start = corridor["start"]
    active_occurrences = []
    strict_union = 0
    collision_union = 0
    line_equation_checks = 0
    selected_indices = model["needed_indices"][corridor["actual_word"]]
    selected_index_mask = sum(1 << index for index in selected_indices)

    for relative_lateral, sites in model["lateral_sites"].items():
        absolute_lateral = add2(lateral(start), relative_lateral)
        line = level_data["line_by_lateral"].get(absolute_lateral)
        if (
            line is None
            or line["activation_rank_by_order"][order_name]
            >= corridor["schedule_rank_by_order"][order_name]
        ):
            continue

        endpoint_set = set(line["endpoint_coordinates"])
        strict_sites = []
        collision_sites = []
        strict_mask = 0
        collision_mask = 0
        for site in sites:
            absolute_site = add(start, site)
            if absolute_site in endpoint_set:
                collision_sites.append(site)
                collision_mask |= model["site_masks"][site]
            else:
                # Equal y,z and a distinct x coordinate gives three distinct
                # collinear points on this exact old x-parallel secant.
                if lateral(absolute_site) != line["lateral"]:
                    raise AssertionError("lateral lookup inconsistency")
                first, second = line["endpoint_coordinates"]
                if absolute_site in (first, second):
                    raise AssertionError("strict site is an endpoint")
                if cross3(sub(second, first), sub(absolute_site, first)) != (
                    0, 0, 0
                ):
                    raise AssertionError(
                        "strict lateral effect fails independent line equation",
                        first, second, absolute_site,
                    )
                line_equation_checks += 1
                strict_sites.append(site)
                strict_mask |= model["site_masks"][site]

        combined_mask = strict_mask | collision_mask
        if not combined_mask:
            raise AssertionError("matched lateral class has an empty word mask")
        if combined_mask & selected_index_mask:
            raise AssertionError(
                "recorded connector is killed by a prefix-active x-line",
                corridor["level"], corridor["gap"], line["line_id"],
                selected_indices,
            )

        strict_profile = model_mask_profile(model, strict_mask)
        collision_profile = model_mask_profile(model, collision_mask)
        if combined_mask == strict_mask:
            combined_profile = strict_profile
        elif combined_mask == collision_mask:
            combined_profile = collision_profile
        else:
            combined_profile = model_mask_profile(model, combined_mask)
        strict_atom_key = tuple(strict_sites)
        effect_key = (
            corridor["step"], relative_lateral, strict_atom_key,
            strict_profile["mask_sha256"],
        )
        record = {
            "occurrence_id": occurrence_id(
                order_name, corridor["level"], corridor["gap"],
                line["line_id"]
            ),
            "stitch_order": order_name,
            "level": corridor["level"],
            "gap": corridor["gap"],
            "schedule_rank": corridor["schedule_rank_by_order"][order_name],
            "parent_step": corridor["step"],
            "domain_words": model["domain_words"],
            "actual_selected_word": as_json(corridor["actual_word"]),
            "actual_selected_word_indices": selected_indices,
            "line_id": line["line_id"],
            "line_endpoint_stable_ids": line["endpoint_stable_ids"],
            "line_activation_rank": line["activation_rank_by_order"][
                order_name
            ],
            "line_lateral_yz": as_json(line["lateral"]),
            "relative_lateral_yz": as_json(relative_lateral),
            "strict_third_point_site_offsets": as_json(strict_sites),
            "collision_site_offsets": as_json(collision_sites),
            "strict_x_secant_word_mask": strict_profile,
            "endpoint_collision_word_mask": collision_profile,
            "combined_x_line_site_word_mask": combined_profile,
            "recorded_word_survives_this_line": True,
            "line_meets_candidate_site_lateral_class": True,
            "latent_zero_effect": False,
            "effect_key_sha256": stable_hash(effect_key),
        }
        active_occurrences.append(record)
        strict_union |= strict_mask
        collision_union |= collision_mask

    active_occurrences.sort(key=lambda item: item["occurrence_id"])
    if (strict_union | collision_union) & selected_index_mask:
        raise AssertionError("recorded word is killed by union of active x-lines")
    strict_union_profile = model_mask_profile(model, strict_union)
    collision_union_profile = model_mask_profile(model, collision_union)
    combined_union_mask = strict_union | collision_union
    if combined_union_mask == strict_union:
        combined_union_profile = strict_union_profile
    elif combined_union_mask == collision_union:
        combined_union_profile = collision_union_profile
    else:
        combined_union_profile = model_mask_profile(model, combined_union_mask)
    return active_occurrences, {
        "active_x_lines_meeting_candidate_sites": len(active_occurrences),
        "strict_effectful_x_lines": sum(
            item["strict_x_secant_word_mask"]["killed_words"] > 0
            for item in active_occurrences
        ),
        "strict_union": strict_union_profile,
        "collision_union": collision_union_profile,
        "combined_union": combined_union_profile,
        "recorded_word_survives_union": True,
        "strict_site_line_equation_checks": line_equation_checks,
    }


def exact_fixed_point(controls):
    """Solve (B^r-I)z = sum B^(r-i)c_i over Q exactly."""
    period = len(controls)
    power = mat2_power(B_LATERAL, period)
    matrix = (
        (power[0][0] - 1, power[0][1]),
        (power[1][0], power[1][1] - 1),
    )
    rhs = (0, 0)
    for control in controls:
        rhs = mat2_vector(B_LATERAL, add2(rhs, control))
    determinant = matrix[0][0] * matrix[1][1] - (
        matrix[0][1] * matrix[1][0]
    )
    if determinant == 0:
        raise AssertionError("B^r-I unexpectedly singular", period)
    solution = (
        Fraction(
            rhs[0] * matrix[1][1] - matrix[0][1] * rhs[1],
            determinant,
        ),
        Fraction(
            matrix[0][0] * rhs[1] - rhs[0] * matrix[1][0],
            determinant,
        ),
    )
    check = (
        matrix[0][0] * solution[0] + matrix[0][1] * solution[1],
        matrix[1][0] * solution[0] + matrix[1][1] * solution[1],
    )
    if check != rhs:
        raise AssertionError("exact cycle equation solver failed")
    return {
        "period": period,
        "matrix_Br_minus_I": as_json(matrix),
        "rhs": as_json(rhs),
        "determinant": determinant,
        "solution": [
            {"numerator": value.numerator, "denominator": value.denominator}
            for value in solution
        ],
        "integral": all(value.denominator == 1 for value in solution),
        "integral_value": (
            [int(value) for value in solution]
            if all(value.denominator == 1 for value in solution) else None
        ),
    }


def build_closed_lineage_graph(
    levels, occurrences, occurrence_by_key, zero_profile_by_step
):
    """Close every strict-effect line through all realized slots to L8.

    A line remains a concrete jointly realized endpoint pair even when it has
    no effect on an intermediate connector domain.  Such intermediate states
    are materialized with an exact zero strict mask, so effect--latent--effect
    paths are not silently dropped.
    """
    nodes = {}
    latent_nodes = []
    queue = []
    expanded = set()

    def add_node(node):
        node_id = node["occurrence_id"]
        previous = nodes.get(node_id)
        if previous is not None:
            if previous != node:
                raise AssertionError("lineage node id has two definitions")
            return previous
        nodes[node_id] = node
        queue.append(node_id)
        if node["latent_zero_effect"]:
            latent_nodes.append(node)
        return node

    strict_seeds = sorted(
        (
            occurrence for occurrence in occurrences
            if occurrence["strict_x_secant_word_mask"]["killed_words"] > 0
        ),
        key=lambda item: item["occurrence_id"],
    )
    for seed in strict_seeds:
        add_node(seed)

    def materialize_target(order_name, level, gap, line):
        key = (order_name, level, gap, line["line_id"])
        existing = occurrence_by_key.get(key)
        if existing is not None:
            return add_node(existing)

        corridor = levels[level]["corridor_by_gap"][gap]
        relative = sub2(line["lateral"], lateral(corridor["start"]))
        zero_profile = zero_profile_by_step[corridor["step"]]
        effect_key = (
            corridor["step"], relative, tuple(),
            zero_profile["mask_sha256"],
        )
        node = {
            "occurrence_id": occurrence_id(
                order_name, level, gap, line["line_id"]
            ),
            "stitch_order": order_name,
            "level": level,
            "gap": gap,
            "schedule_rank": corridor["schedule_rank_by_order"][order_name],
            "parent_step": corridor["step"],
            "domain_words": zero_profile_by_step[corridor["step"]][
                "domain_words"
            ],
            "actual_selected_word": as_json(corridor["actual_word"]),
            "actual_selected_word_indices": None,
            "line_id": line["line_id"],
            "line_endpoint_stable_ids": line["endpoint_stable_ids"],
            "line_activation_rank": line["activation_rank_by_order"][
                order_name
            ],
            "line_lateral_yz": as_json(line["lateral"]),
            "relative_lateral_yz": as_json(relative),
            "strict_third_point_site_offsets": [],
            "collision_site_offsets": [],
            "strict_x_secant_word_mask": {
                "killed_words": zero_profile["killed_words"],
                "mask_sha256": zero_profile["mask_sha256"],
            },
            "endpoint_collision_word_mask": {
                "killed_words": zero_profile["killed_words"],
                "mask_sha256": zero_profile["mask_sha256"],
            },
            "combined_x_line_site_word_mask": {
                "killed_words": zero_profile["killed_words"],
                "mask_sha256": zero_profile["mask_sha256"],
            },
            "recorded_word_survives_this_line": True,
            "line_meets_candidate_site_lateral_class": False,
            "latent_zero_effect": True,
            "effect_key_sha256": stable_hash(effect_key),
        }
        if node["strict_x_secant_word_mask"]["killed_words"] != 0:
            raise AssertionError("latent lineage node must have zero effect")
        return add_node(node)

    transitions = []
    while queue:
        source_id = queue.pop()
        if source_id in expanded:
            continue
        expanded.add(source_id)
        source = nodes[source_id]
        level = source["level"]
        order_name = source["stitch_order"]
        if level == LEVELS[-1]:
            continue
        source_level = levels[level]
        child_level = levels[level + 1]
        corridor = source_level["corridor_by_gap"][source["gap"]]
        word = corridor["actual_word"]
        prefix = (0, 0, 0)
        pair = tuple(source["line_endpoint_stable_ids"])
        source_line = source_level["line_by_pair"].get(pair)
        if source_line is None:
            raise AssertionError("lineage source line identity is absent")
        source_relative = sub2(
            source_line["lateral"], lateral(corridor["start"])
        )
        if source_relative != tuple(source["relative_lateral_yz"]):
            raise AssertionError("lineage source relative offset drift")
        child_line = child_level["line_by_pair"].get(pair)
        if child_line is None:
            raise AssertionError(
                "completed source x-line did not inherit", level,
                source["line_id"],
            )
        if not child_line["inherited_from_completed_L" + str(level)]:
            raise AssertionError("lineage target not marked inherited")
        if any(
            child_line["activation_rank_by_order"][name] != -1
            for name in ("gate", "pipeline")
        ):
            raise AssertionError("inherited lineage line must be initially old")

        for slot, menu_index in enumerate(word):
            child_gap = corridor["block_start"] + slot
            child_corridor = child_level["corridor_by_gap"][child_gap]
            if child_corridor["step"] != menu_index:
                raise AssertionError("actual child slot/step mismatch")
            predicted = mat2_vector(
                B_LATERAL,
                sub2(tuple(source["relative_lateral_yz"]), lateral(prefix)),
            )
            actual = sub2(
                child_line["lateral"], lateral(child_corridor["start"])
            )
            if predicted != actual:
                raise AssertionError(
                    "selected-control lateral recurrence failed", source,
                    slot, prefix, predicted, actual,
                )
            target = materialize_target(
                order_name, level + 1, child_gap, child_line
            )
            transition = {
                "transition_id": stable_hash((
                    source_id, target["occurrence_id"], slot, prefix,
                )),
                "source_lineage_node_id": source_id,
                "target_lineage_node_id": target["occurrence_id"],
                "stitch_order": order_name,
                "source_effect_key_sha256": source["effect_key_sha256"],
                "source_has_strict_x_secant_effect": (
                    source["strict_x_secant_word_mask"]["killed_words"] > 0
                ),
                "source_is_latent_zero_effect": source["latent_zero_effect"],
                "source_level_gap": [level, source["gap"]],
                "actual_selected_word": as_json(word),
                "actual_child_slot_zero_based": slot,
                "selected_prefix_control_c": as_json(prefix),
                "selected_prefix_control_c_perp": as_json(lateral(prefix)),
                "child_level_gap": [level + 1, child_gap],
                "child_step": child_corridor["step"],
                "predicted_and_actual_child_relative_lateral_yz": as_json(
                    actual
                ),
                "target_meets_candidate_site_lateral_class": target[
                    "line_meets_candidate_site_lateral_class"
                ],
                "target_has_strict_x_secant_effect": (
                    target["strict_x_secant_word_mask"]["killed_words"] > 0
                ),
                "target_is_latent_zero_effect": target["latent_zero_effect"],
                "target_effect_key_sha256": target["effect_key_sha256"],
            }
            transitions.append(transition)
            prefix = add(prefix, MENU[menu_index])
        if add(corridor["start"], prefix) != corridor["end"]:
            raise AssertionError("recorded word endpoint failed in transition")

    transitions.sort(key=lambda item: (
        item["stitch_order"], item["source_lineage_node_id"],
        item["actual_child_slot_zero_based"], item["target_lineage_node_id"],
    ))
    latent_nodes.sort(key=lambda item: item["occurrence_id"])
    return {
        "nodes_by_id": nodes,
        "strict_seed_ids": [item["occurrence_id"] for item in strict_seeds],
        "latent_nodes": latent_nodes,
        "transitions": transitions,
    }


def analyze_short_returns(nodes_by_id, transitions, strict_seed_ids):
    """Test effectful endpoints of every depth<=3 closed-lineage path."""
    adjacency = defaultdict(list)
    for transition in transitions:
        source_id = transition["source_lineage_node_id"]
        target_id = transition["target_lineage_node_id"]
        if source_id not in nodes_by_id or target_id not in nodes_by_id:
            raise AssertionError("closed lineage transition has a missing node")
        adjacency[source_id].append(transition)
    for source_id in adjacency:
        adjacency[source_id].sort(key=lambda item: item["transition_id"])

    counts = {period: Counter() for period in (1, 2, 3)}
    path_digests = {period: hashlib.sha256() for period in (1, 2, 3)}
    all_path_digests = {period: hashlib.sha256() for period in (1, 2, 3)}
    order_counts = {
        order_name: {period: Counter() for period in (1, 2, 3)}
        for order_name in ("gate", "pipeline")
    }
    order_digests = {
        order_name: {period: hashlib.sha256() for period in (1, 2, 3)}
        for order_name in ("gate", "pipeline")
    }
    order_all_path_digests = {
        order_name: {period: hashlib.sha256() for period in (1, 2, 3)}
        for order_name in ("gate", "pipeline")
    }
    lateral_returns = []
    effect_key_returns = []

    def visit(source_id, current_id, path, maximum):
        if path:
            period = len(path)
            source = nodes_by_id[source_id]
            target = nodes_by_id[current_id]
            order_name = source["stitch_order"]
            if target["stitch_order"] != order_name:
                raise AssertionError("lineage path crossed stitch orders")
            path_key = (
                source_id, current_id,
                tuple(edge["transition_id"] for edge in path),
            )
            counts[period]["all_paths_from_effect_source"] += 1
            order_counts[order_name][period][
                "all_paths_from_effect_source"
            ] += 1
            all_path_digests[period].update(stable_bytes(path_key))
            all_path_digests[period].update(b"\n")
            order_all_path_digests[order_name][period].update(
                stable_bytes(path_key)
            )
            order_all_path_digests[order_name][period].update(b"\n")

            target_effectful = (
                target["strict_x_secant_word_mask"]["killed_words"] > 0
            )
            if target_effectful:
                controls = [
                    tuple(edge["selected_prefix_control_c_perp"])
                    for edge in path
                ]
                solved = exact_fixed_point(controls)
                source_z = tuple(source["relative_lateral_yz"])
                target_z = tuple(target["relative_lateral_yz"])
                source_matches = (
                    solved["integral"]
                    and tuple(solved["integral_value"]) == source_z
                )
                lateral_return = source_z == target_z
                if source_matches != lateral_return:
                    raise AssertionError(
                        "cycle equation disagrees with exact recurrence",
                        source_id, current_id, controls, solved,
                    )
                source_components = (
                    source["parent_step"], source_z,
                    tuple(tuple(site) for site in source[
                        "strict_third_point_site_offsets"
                    ]),
                )
                target_components = (
                    target["parent_step"], target_z,
                    tuple(tuple(site) for site in target[
                        "strict_third_point_site_offsets"
                    ]),
                )
                effect_return = (
                    lateral_return and source_components == target_components
                )
                if effect_return and (
                    source["strict_x_secant_word_mask"]
                    != target["strict_x_secant_word_mask"]
                    or source["effect_key_sha256"]
                    != target["effect_key_sha256"]
                ):
                    raise AssertionError(
                        "equal exact step/lateral/site atoms have unequal masks"
                    )
                action_return = (
                    source["actual_selected_word"]
                    == target["actual_selected_word"]
                )
                latent_intermediates = sum(
                    nodes_by_id[edge["target_lineage_node_id"]][
                        "strict_x_secant_word_mask"
                    ]["killed_words"] == 0
                    for edge in path[:-1]
                )
                data = counts[period]
                data["paths_with_effectful_terminal"] += 1
                data["paths_with_zero_effect_intermediate"] += int(
                    latent_intermediates > 0
                )
                data["integral_formal_fixed_points"] += int(solved["integral"])
                data["reachable_lateral_returns"] += int(lateral_return)
                data["exact_effect_key_returns"] += int(effect_return)
                data["effect_and_selected_action_returns"] += int(
                    effect_return and action_return
                )
                per_order = order_counts[order_name][period]
                per_order["paths_with_effectful_terminal"] += 1
                per_order["paths_with_zero_effect_intermediate"] += int(
                    latent_intermediates > 0
                )
                per_order["integral_formal_fixed_points"] += int(
                    solved["integral"]
                )
                per_order["reachable_lateral_returns"] += int(lateral_return)
                per_order["exact_effect_key_returns"] += int(effect_return)
                per_order["effect_and_selected_action_returns"] += int(
                    effect_return and action_return
                )
                compact = {
                    "period": period,
                    "stitch_order": order_name,
                    "source": source_id,
                    "target": current_id,
                    "transition_ids": [
                        edge["transition_id"] for edge in path
                    ],
                    "controls": as_json(controls),
                    "zero_effect_intermediate_nodes": latent_intermediates,
                    "formal_solution": solved["solution"],
                    "integral": solved["integral"],
                    "lateral_return": lateral_return,
                    "effect_key_return": effect_return,
                    "selected_action_return": action_return,
                }
                path_digests[period].update(stable_bytes(compact))
                path_digests[period].update(b"\n")
                order_digests[order_name][period].update(stable_bytes(compact))
                order_digests[order_name][period].update(b"\n")
                if lateral_return:
                    record = {
                        **compact,
                        "source_effect_key_sha256": source[
                            "effect_key_sha256"
                        ],
                        "target_effect_key_sha256": target[
                            "effect_key_sha256"
                        ],
                        "exact_cycle_equation": solved,
                        "interpretation": (
                            "an exact finite realized lateral return, allowing "
                            "zero-effect intermediate lineage states; it is a "
                            "cycle only in the stated coarse projection"
                        ),
                    }
                    lateral_returns.append(record)
                    if effect_return:
                        effect_key_returns.append(record)
        if len(path) == maximum:
            return
        for edge in adjacency.get(current_id, ()):
            visit(
                source_id,
                edge["target_lineage_node_id"],
                path + [edge],
                maximum,
            )

    for source_id in sorted(strict_seed_ids):
        source = nodes_by_id[source_id]
        if source["strict_x_secant_word_mask"]["killed_words"] == 0:
            raise AssertionError("short-return seed is not effectful")
        visit(source_id, source_id, [], 3)

    def period_record(data, effect_digest, all_digest):
        return {
            "all_lineage_paths_from_effect_source": data[
                "all_paths_from_effect_source"
            ],
            "paths_with_effectful_terminal": data[
                "paths_with_effectful_terminal"
            ],
            "paths_with_zero_effect_intermediate": data[
                "paths_with_zero_effect_intermediate"
            ],
            "integral_formal_fixed_points": data[
                "integral_formal_fixed_points"
            ],
            "reachable_lateral_returns": data["reachable_lateral_returns"],
            "exact_effect_key_returns": data["exact_effect_key_returns"],
            "effect_and_selected_action_returns": data[
                "effect_and_selected_action_returns"
            ],
            "all_path_stream_sha256": all_digest.hexdigest(),
            "effect_endpoint_path_solution_stream_sha256": (
                effect_digest.hexdigest()
            ),
        }

    period_records = {
        str(period): period_record(
            counts[period], path_digests[period], all_path_digests[period]
        )
        for period in (1, 2, 3)
    }
    by_order = {
        order_name: {
            str(period): period_record(
                order_counts[order_name][period],
                order_digests[order_name][period],
                order_all_path_digests[order_name][period],
            )
            for period in (1, 2, 3)
        }
        for order_name in ("gate", "pipeline")
    }
    lateral_returns.sort(key=lambda item: (
        item["period"], item["source"], item["target"], item["transition_ids"]
    ))
    effect_key_returns.sort(key=lambda item: (
        item["period"], item["source"], item["target"], item["transition_ids"]
    ))
    return {
        "path_scope": (
            "all depth-1..3 actual selected descendant paths from every strict "
            "effect seed; intermediate lineage nodes may have zero effect; "
            "return equations are evaluated when the terminal is effectful"
        ),
        "periods_1_through_3": period_records,
        "periods_by_stitch_order": by_order,
        "exact_lateral_return_records": lateral_returns,
        "exact_lateral_return_stream_sha256": stable_hash(lateral_returns),
        "exact_effect_key_return_records": effect_key_returns,
        "exact_effect_key_return_stream_sha256": stable_hash(
            effect_key_returns
        ),
        "period_4": {
            "status": "not instantiated",
            "reason": (
                "four transitions beginning at L5 require actual L9 choices, "
                "which are absent from the pinned artifacts"
            ),
        },
        "policy_cycle_join": {
            "certified": False,
            "missing_obligation": (
                "equal finite effect keys and actions are not proved to "
                "determine congruent future ordered-path states"
            ),
            "consequence_of_a_reported_effect_key_return": (
                "a strict rank on exactly this coarse key must refine or "
                "promote the witnessed cycle; infinite recurrence does not follow"
            ),
        },
    }


def phase_stabilization(transitions, nodes_by_id):
    classes = defaultdict(list)
    for transition in transitions:
        source = nodes_by_id[transition["source_lineage_node_id"]]
        key = (
            transition["stitch_order"],
            source["parent_step"],
            tuple(source["actual_selected_word"]),
            transition["actual_child_slot_zero_based"],
            tuple(transition["selected_prefix_control_c"]),
            transition["child_step"],
        )
        post = (
            transition["target_has_strict_x_secant_effect"],
            transition["target_effect_key_sha256"],
        )
        classes[key].append((source["occurrence_id"], post))

    class_records = []
    ambiguous = 0
    repeated = 0
    for key, members in sorted(classes.items()):
        posts = sorted(set(post for _source, post in members))
        repeated += len(members) > 1
        ambiguous += len(posts) > 1
        class_records.append({
            "phase_key_sha256": stable_hash(key),
            "stitch_order": key[0],
            "source_step": key[1],
            "selected_word": as_json(key[2]),
            "slot_zero_based": key[3],
            "prefix_control": as_json(key[4]),
            "child_step": key[5],
            "occurrences": len(members),
            "distinct_effect_posts": len(posts),
            "effect_posts": as_json(posts),
        })
    return {
        "scope": (
            "closed realized descendants of every strict x-line effect seed, "
            "including zero-effect intermediate lineage nodes"
        ),
        "phase_classes": len(class_records),
        "repeated_phase_classes": repeated,
        "phase_classes_with_multiple_effect_posts": ambiguous,
        "class_stream_sha256": stable_hash(class_records),
        "classes": class_records,
        "interpretation": (
            "these are exact finite selected-word/slot observations; repeated "
            "classes with one observed post are not universal transition "
            "congruence, and ambiguous classes refute this phase key outright"
        ),
    }


def structural_estimate():
    resource = enforce_resource_policy()
    inputs = observed_inputs()
    started = time.time()
    levels = build_realized_levels()
    level_records = []
    for level in LEVELS:
        data = levels[level]
        inherited = sum(
            line["inherited_from_completed_L" + str(level - 1)]
            for line in data["line_records"]
        )
        level_records.append({
            "level": level,
            "construction_points": data["completed_points"],
            "corridors": data["gaps"],
            "x_parallel_lines_in_completed_path": len(data["line_records"]),
            "inherited_x_parallel_lines": inherited,
            "new_x_parallel_lines": len(data["line_records"]) - inherited,
            "point_lateral_multiplicity_histogram": (
                data["point_lateral_multiplicity_histogram"]
            ),
        })
    return {
        "status": (
            "exact realized-path structural estimate; x-line identities and "
            "gate-order activation ranks built; connector domains, pipeline "
            "ranks, and word masks not scanned"
        ),
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "levels": level_records,
        "total_corridors": sum(record["corridors"] for record in level_records),
        "total_level_line_records": sum(
            record["x_parallel_lines_in_completed_path"]
            for record in level_records
        ),
        "planned_effective_domain_words": EXPECTED_EFFECTIVE_DOMAIN_WORDS,
        "planned_run_work": (
            "build one exact site-to-word bitset model for each of 124 step "
            "domains, install and separately scan gate/pipeline prefixes, then "
            "release each model"
        ),
    }


def stream_effective_domains(on_d24, process_step):
    """Process effective domains without retaining both D2--4 and D5.

    Ordering is byte-for-byte the ordering rule in ``gate_run.load_domains``:
    stable sort each D2--4 collection by word length, then append converted D5
    words for precisely the fragile steps.  The callback consumes a domain
    before the next large effective list is formed.
    """
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        d4 = pickle.load(handle)
    observed_menu = tuple(tuple(step) for step in d4.pop("menu"))
    if observed_menu != tuple(MENU):
        raise AssertionError("connector_domains4 menu drift")
    raw_domains = d4.pop("domains")
    surviving = tuple(d4.pop("surviving"))
    if d4:
        raise AssertionError("unexpected connector_domains4 fields", sorted(d4))
    if len(surviving) != len(set(surviving)):
        raise AssertionError("duplicate surviving step index in D2--4 artifact")
    if not set(surviving) <= set(range(len(MENU))):
        raise AssertionError("invalid surviving step index in D2--4 artifact")
    if set(raw_domains) != set(range(len(MENU))):
        raise AssertionError("D2--4 step-key mismatch")

    d24 = {step: len(words) for step, words in raw_domains.items()}
    fragile_steps = {
        step for step, size in d24.items() if size < FRAGILE_CUT
    }
    nonfragile_steps = set(d24) - fragile_steps
    on_d24(d24)

    processed = []
    total_words = 0
    d24_words = sum(d24.values())
    fragile_bases = {}
    for step in sorted(d24):
        raw_words = raw_domains.pop(step)
        if isinstance(raw_words, list):
            raw_words.sort(key=len)
            base = raw_words
        else:
            base = sorted(raw_words, key=len)
        del raw_words
        if step in fragile_steps:
            fragile_bases[step] = base
        else:
            process_step(step, base, "D2-4-only")
            total_words += len(base)
            processed.append(step)
            del base
            gc.collect()
    if raw_domains:
        raise AssertionError("D2--4 domains not fully released")
    del raw_domains, d4
    gc.collect()

    with (ROOT / "dstar5_fragile.pkl").open("rb") as handle:
        d5 = pickle.load(handle)
    key_by_step = {}
    for raw_step in d5:
        step_vector = tuple(raw_step)
        if step_vector not in IDX:
            raise AssertionError("D5 has a step outside MENU", step_vector)
        step = IDX[step_vector]
        if step in key_by_step:
            raise AssertionError("duplicate D5 step after MENU conversion", step)
        key_by_step[step] = raw_step
    if set(key_by_step) != fragile_steps:
        raise AssertionError(
            "D5/fragile-step mismatch",
            sorted(set(key_by_step) - fragile_steps),
            sorted(fragile_steps - set(key_by_step)),
        )

    d5_words = 0
    for step in sorted(fragile_steps):
        raw_words = d5.pop(key_by_step[step])
        if not isinstance(raw_words, list):
            raw_words = list(raw_words)
        d5_words += len(raw_words)
        for word_index, word in enumerate(raw_words):
            raw_words[word_index] = tuple(
                IDX[tuple(vector)] for vector in word
            )
        base = fragile_bases.pop(step)
        raw_words[:0] = base
        del base
        effective = raw_words
        del raw_words
        process_step(step, effective, "sorted-D2-4-plus-appended-D5")
        total_words += len(effective)
        processed.append(step)
        del effective
        gc.collect()
    if d5 or fragile_bases:
        raise AssertionError("fragile effective domains not fully released")
    del d5, fragile_bases, key_by_step
    gc.collect()

    if set(processed) != set(range(len(MENU))):
        raise AssertionError("not all 124 effective steps were processed")
    if len(processed) != len(set(processed)):
        raise AssertionError("an effective step was processed twice")
    if total_words != EXPECTED_EFFECTIVE_DOMAIN_WORDS:
        raise AssertionError(
            "effective domain size drift", total_words,
            EXPECTED_EFFECTIVE_DOMAIN_WORDS,
        )
    return {
        "D2-4_words": d24_words,
        "D2-4_surviving_steps": len(surviving),
        "D2-4_surviving_step_stream_sha256": stable_hash(surviving),
        "D5_appended_words": d5_words,
        "effective_domain_words": total_words,
        "fragile_steps": len(fragile_steps),
        "nonfragile_steps": len(nonfragile_steps),
        "processing_order": processed,
        "processing_order_sha256": stable_hash(processed),
        "memory_discipline": (
            "all nonfragile D2-4 domains are consumed before loading D5; only "
            "the <FRAGILE_CUT sorted D2-4 bases survive that boundary; each "
            "D5 word list is converted in place, prefixed by its small base, "
            "processed, and released separately"
        ),
    }


def exact_run():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    resource = enforce_resource_policy()
    inputs = observed_inputs()
    started = time.time()
    levels = build_realized_levels()

    corridors_by_step = defaultdict(list)
    needed_words_by_step = defaultdict(set)
    for level in LEVELS:
        for corridor in levels[level]["corridors"]:
            corridors_by_step[corridor["step"]].append(corridor)
            needed_words_by_step[corridor["step"]].add(
                corridor["actual_word"]
            )
    for step in corridors_by_step:
        corridors_by_step[step].sort(key=lambda item: (
            item["level"], item["gap"]
        ))

    occurrences = []
    occurrence_by_key = {}
    target_corridor_effects = {}
    prefix_stats = {
        order_name: Counter() for order_name in ("gate", "pipeline")
    }
    model_records = []
    schedule_installed = [False]

    def on_d24(d24):
        if set(d24) != set(corridors_by_step):
            raise AssertionError(
                "loaded/effective step mismatch",
                sorted(set(d24) - set(corridors_by_step)),
                sorted(set(corridors_by_step) - set(d24)),
            )
        install_pipeline_orders(levels, d24)
        schedule_installed[0] = True

    def process_step(step, domain, domain_layer):
        if not schedule_installed[0]:
            raise AssertionError("pipeline ranks must precede domain scans")
        ordinal = len(model_records) + 1
        print(
            f"x-axis model {ordinal}/{len(MENU)}: step {step}, "
            f"{len(domain)} words, {len(corridors_by_step[step])} corridors",
            flush=True,
        )
        model = build_lateral_domain_model(
            domain, step, needed_words_by_step[step]
        )
        model_records.append({
            "step": step,
            "effective_domain_layer": domain_layer,
            "domain_words": model["domain_words"],
            "candidate_sites": model["sites"],
            "candidate_lateral_site_classes": model[
                "lateral_site_classes"
            ],
            "expected_scaled_parent_step": as_json(
                model["expected_endpoint"]
            ),
            "word_order_stream_schema": (
                "one unsigned length byte followed by one unsigned menu-index "
                "byte per word, in effective-domain order"
            ),
            "word_order_sha256": model["word_order_sha256"],
            "site_word_mask_stream_sha256": model[
                "site_word_mask_stream_sha256"
            ],
            "zero_word_mask": model["zero_mask_profile"],
        })

        for order_name in ("gate", "pipeline"):
            for corridor in corridors_by_step[step]:
                found, union = scan_corridor(
                    corridor, levels[corridor["level"]], model, order_name
                )
                prefix_stats[order_name]["corridors"] += 1
                prefix_stats[order_name]["strict_effectful_corridors"] += int(
                    union["strict_union"]["killed_words"] > 0
                )
                prefix_stats[order_name]["strict_site_line_equation_checks"] += (
                    union["strict_site_line_equation_checks"]
                )
                if (
                    corridor["level"] == 8
                    and corridor["gap"] in TARGET_L8_GAPS
                ):
                    target_corridor_effects[
                        (order_name, corridor["gap"])
                    ] = union
                for occurrence in found:
                    key = (
                        order_name, occurrence["level"], occurrence["gap"],
                        occurrence["line_id"],
                    )
                    if key in occurrence_by_key:
                        raise AssertionError(
                            "duplicate x-line occurrence key", key
                        )
                    occurrence_by_key[key] = occurrence
                    occurrences.append(occurrence)

        del model
        gc.collect()

    domain_stream = stream_effective_domains(on_d24, process_step)
    if not schedule_installed[0]:
        raise AssertionError("pipeline schedule installation was skipped")
    expected_targets = {
        (order_name, gap)
        for order_name in ("gate", "pipeline")
        for gap in TARGET_L8_GAPS
    }
    if set(target_corridor_effects) != expected_targets:
        raise AssertionError("target gap/order effects were not all retained")
    model_records.sort(key=lambda item: item["step"])
    total_domain_words = domain_stream["effective_domain_words"]

    occurrences.sort(key=lambda item: (
        item["stitch_order"], item["level"], item["gap"], item["line_id"]
    ))
    if len({item["occurrence_id"] for item in occurrences}) != len(occurrences):
        raise AssertionError("duplicate occurrence id")

    zero_profile_by_step = {
        record["step"]: {
            "domain_words": record["domain_words"],
            **record["zero_word_mask"],
        }
        for record in model_records
    }
    if set(zero_profile_by_step) != set(range(len(MENU))):
        raise AssertionError("zero-mask profiles do not cover every step")
    lineage = build_closed_lineage_graph(
        levels, occurrences, occurrence_by_key, zero_profile_by_step
    )
    lineage_nodes = lineage["nodes_by_id"]
    transitions = lineage["transitions"]
    short_returns = analyze_short_returns(
        lineage_nodes, transitions, lineage["strict_seed_ids"]
    )
    phase = phase_stabilization(transitions, lineage_nodes)

    line_census = []
    for level in LEVELS:
        data = levels[level]
        inherited = sum(
            line["inherited_from_completed_L" + str(level - 1)]
            for line in data["line_records"]
        )
        line_census.append({
            "level": level,
            "completed_points": data["completed_points"],
            "construction_corridors": data["gaps"],
            "x_parallel_lines": len(data["line_records"]),
            "inherited_x_parallel_lines": inherited,
            "new_x_parallel_lines": len(data["line_records"]) - inherited,
            "point_lateral_multiplicity_histogram": (
                data["point_lateral_multiplicity_histogram"]
            ),
            "stitch_orders": data["schedule_summaries"],
            "line_record_stream_sha256": stable_hash(data["line_records"]),
            "records": data["line_records"],
        })

    targeted_block = {}
    for label, gap in TARGET_L8_BLOCK.items():
        corridor = levels[8]["corridor_by_gap"][gap]
        targeted_block[label] = {
            "gap": gap,
            "step": corridor["step"],
            "actual_selected_word": as_json(corridor["actual_word"]),
            "recorded_word_replay_by_stitch_order": {
                order_name: {
                    "schedule_rank": corridor["schedule_rank_by_order"][
                        order_name
                    ],
                    "pipeline_schedule_entry": (
                        levels[8]["pipeline_entry_by_gap"][gap]
                        if order_name == "pipeline" else None
                    ),
                    "x_axis_effect": target_corridor_effects[
                        (order_name, gap)
                    ],
                    "occurrence_ids": [
                        item["occurrence_id"] for item in occurrences
                        if item["stitch_order"] == order_name
                        and item["level"] == 8 and item["gap"] == gap
                    ],
                }
                for order_name in ("gate", "pipeline")
            },
        }

    strict_occurrences = [
        item for item in occurrences
        if item["strict_x_secant_word_mask"]["killed_words"] > 0
    ]
    collision_only = [
        item for item in occurrences
        if item["strict_x_secant_word_mask"]["killed_words"] == 0
    ]
    effectful_corridors_by_order = {
        order_name: prefix_stats[order_name]["strict_effectful_corridors"]
        for order_name in ("gate", "pipeline")
    }
    all_corridors = sum(levels[level]["gaps"] for level in LEVELS)
    if any(
        prefix_stats[order_name]["corridors"] != all_corridors
        for order_name in ("gate", "pipeline")
    ):
        raise AssertionError("not every corridor was scanned in both orders")

    return {
        "status": (
            "exact finite realized L5-L8 x-axis old-secant/site-word audit "
            "and actual selected-child recurrence census; not a universal "
            "tail quotient, policy cycle, contraction lemma, or availability proof"
        ),
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "scope": {
            "levels": list(LEVELS),
            "construction_corridors": all_corridors,
            "stitch_orders_replayed_separately": ["gate", "pipeline"],
            "prefix_cursors_scanned_across_both_orders": 2 * all_corridors,
            "endpoint_cutoff": None,
            "distance_cutoff": None,
            "secants": (
                "all pairs of actual completed-level points with identical "
                "y,z; activation rank makes the pair old at each exact cursor"
            ),
            "candidate_effect": (
                "all exact connector-domain interior site atoms on each active "
                "x-line, with exact effective-domain word masks"
            ),
            "selected_controls": (
                "only recorded connector words and their actual child slots; "
                "no full-menu alternative or independent address stream"
            ),
            "schedule_semantics": (
                "gate is state['order']; pipeline is the exact inherited-tile "
                "guard schedule. Geometry and child-slot controls are common, "
                "but old-line activation and poison records remain separate. "
                "The pipeline replay reuses recorded final connector words and "
                "this checker revalidates only their x-line channel, not their "
                "complete legality under that reordered prefix."
            ),
            "covered_poison_role": "old--old--new candidate-site secants",
            "separately_labelled_degeneracy": (
                "a candidate site equal to a line endpoint is collision poison, "
                "not a three-distinct-point secant witness"
            ),
            "omitted": [
                "non-x-parallel secants",
                "old points on candidate-internal lines",
                "all alternate connector choices",
                "L9 and later selected constructions",
                "a proof that a finite phase/effect key determines future policy",
                "union with every other local and far poison source",
            ],
        },
        "lateral_transport": {
            "B": as_json(B_LATERAL),
            "exact_rule": "z_child = B * (z_parent - c_perp)",
            "cycle_equation": (
                "(B^r-I)z0 = sum_{i=0}^{r-1} B^(r-i)c_i"
            ),
            "effect_return_key": (
                "exact parent step, relative lateral coordinate, and ordered "
                "strict site-offset tuple; equal components deterministically "
                "reuse the same step-domain word mask, whose count/hash is "
                "asserted equal independently"
            ),
        },
        "domain_models": {
            "effective_domain_words": total_domain_words,
            "sequential_artifact_processing": domain_stream,
            "models": model_records,
            "model_stream_sha256": stable_hash(model_records),
            "bit_order": (
                "word i is bit (i mod 8) of byte floor(i/8), little-endian "
                "within each byte"
            ),
            "built_and_released_one_step_at_a_time": True,
        },
        "reachable_x_parallel_lines": {
            "level_census": line_census,
            "all_level_line_stream_sha256": stable_hash(line_census),
        },
        "exact_prefix_effects": {
            "physical_corridors_per_order": all_corridors,
            "prefix_cursors_across_both_orders": 2 * all_corridors,
            "strict_effectful_corridors_by_order": effectful_corridors_by_order,
            "zero_strict_effect_corridors_by_order": {
                order_name: all_corridors - effectful_corridors_by_order[
                    order_name
                ]
                for order_name in ("gate", "pipeline")
            },
            "line_lateral_occurrences": len(occurrences),
            "line_lateral_occurrences_by_order": dict(sorted(Counter(
                item["stitch_order"] for item in occurrences
            ).items())),
            "strict_x_secant_occurrences": len(strict_occurrences),
            "strict_x_secant_occurrences_by_order": dict(sorted(Counter(
                item["stitch_order"] for item in strict_occurrences
            ).items())),
            "collision_only_occurrences": len(collision_only),
            "strict_site_line_equation_checks": sum(
                prefix_stats[order_name]["strict_site_line_equation_checks"]
                for order_name in ("gate", "pipeline")
            ),
            "strict_site_line_equation_checks_by_order": {
                order_name: prefix_stats[order_name][
                    "strict_site_line_equation_checks"
                ]
                for order_name in ("gate", "pipeline")
            },
            "maximum_strict_words_killed_by_one_line": max((
                item["strict_x_secant_word_mask"]["killed_words"]
                for item in strict_occurrences
            ), default=0),
            "occurrence_stream_sha256": stable_hash(occurrences),
            "records": occurrences,
            "recorded_selected_words_killed_by_x_line_union": 0,
        },
        "closed_actual_selected_lineage_graph": {
            "closure_rule": (
                "seed every strict-effect occurrence, then retain every actual "
                "selected child slot through L8 even when intermediate strict "
                "effect is zero"
            ),
            "strict_effect_seeds": len(lineage["strict_seed_ids"]),
            "strict_effect_seed_stream_sha256": stable_hash(
                lineage["strict_seed_ids"]
            ),
            "lineage_nodes": len(lineage_nodes),
            "lineage_node_id_stream_sha256": stable_hash(
                sorted(lineage_nodes)
            ),
            "zero_strict_effect_lineage_nodes": sum(
                node["strict_x_secant_word_mask"]["killed_words"] == 0
                for node in lineage_nodes.values()
            ),
            "materialized_latent_zero_effect_nodes": len(
                lineage["latent_nodes"]
            ),
            "observed_lateral_class_zero_effect_nodes": sum(
                node["strict_x_secant_word_mask"]["killed_words"] == 0
                and not node["latent_zero_effect"]
                for node in lineage_nodes.values()
            ),
            "latent_node_stream_sha256": stable_hash(
                lineage["latent_nodes"]
            ),
            "latent_node_records": lineage["latent_nodes"],
            "transitions": len(transitions),
            "transitions_by_order": dict(sorted(Counter(
                item["stitch_order"] for item in transitions
            ).items())),
            "effectful_to_effectful_transitions": sum(
                item["target_has_strict_x_secant_effect"]
                for item in transitions
                if item["source_has_strict_x_secant_effect"]
            ),
            "effectful_to_effectful_transitions_by_order": {
                order_name: sum(
                    item["target_has_strict_x_secant_effect"]
                    for item in transitions
                    if item["stitch_order"] == order_name
                    and item["source_has_strict_x_secant_effect"]
                )
                for order_name in ("gate", "pipeline")
            },
            "effect_transition_class_histogram": dict(sorted(Counter(
                ("effect" if item["source_has_strict_x_secant_effect"]
                 else "zero")
                + "->"
                + ("effect" if item["target_has_strict_x_secant_effect"]
                   else "zero")
                for item in transitions
            ).items())),
            "transition_stream_sha256": stable_hash(transitions),
            "records": transitions,
        },
        "short_actual_control_returns": short_returns,
        "selected_slot_phase_stabilization": phase,
        "recorded_word_replay_at_frozen_certificate_gap_ids": {
            "warning": (
                "these are the pickles' single recorded words under each named "
                "prefix order, not the A/B/C/D alternative-history policy "
                "partition or its poison masks"
            ),
            "gaps": targeted_block,
        },
        "proof_boundary": {
            "proved_by_a_successful_run": (
                "the reported x-lines, prefix activations, site atoms, killed "
                "word masks, common-affine inheritance, selected slot controls, "
                "and length-at-most-three recurrence paths—including paths "
                "through zero-effect intermediate lineage states—are exhaustive "
                "in both named orders for the pinned realized L5-L8 artifacts"
            ),
            "not_proved": (
                "finite observations do not join source and target as the same "
                "future policy state; no universal Post relation, period-four "
                "test, far-tail envelope, or connector-survivor theorem follows"
            ),
        },
    }


def atomic_write_json(path, value):
    path = path.resolve()
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if temporary.exists():
        raise RuntimeError(f"refusing to overwrite stale temporary {temporary}")
    try:
        with temporary.open("x") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    result = (
        structural_estimate() if arguments.mode == "estimate" else exact_run()
    )
    if arguments.output is not None:
        atomic_write_json(arguments.output, result)
        print(
            json.dumps({
                "mode": arguments.mode,
                "output": str(arguments.output.resolve()),
                "output_sha256": file_sha256(arguments.output.resolve()),
            }, sort_keys=True),
            flush=True,
        )
    else:
        print(json.dumps(result, sort_keys=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
