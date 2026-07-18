#!/usr/bin/env python3
"""Exact inherited-anchor age-2 precursor on the 42 -> 146 -> 488 trace.

This checker advances the three tagged L7 endpoints one more affine level and
computes their exact killed-word masks on precisely the 488 completed-L8 path
corridors descended from the pinned 42-parent/146-child realized trace.  It is
purposefully narrower than an L9 construction:

* the complete initial L9 anchor set is ``M_BAL3`` applied to every point of
  the completed L8 path (311,738 anchors);
* there is no selected L9 connector word and no L9 connector-interior point;
* all secants from a tagged endpoint to every initial L9 anchor are joined,
  with no endpoint, path-index, spatial, or distance cutoff; and
* the exact word masks cover only failures involving one of the source's
  tagged endpoints.  They are not the full L9 poison mask or an availability
  certificate.

For each source/corridor, the overlapping channels are:

``collision``
    A candidate interior equals a tagged endpoint.
``endpoint-old-new-new``
    A tagged endpoint lies on a line through two candidate interiors.
``tagged-tagged-old-old``
    A candidate interior lies on a secant from a source endpoint to another
    one of the three tagged endpoints.
``tagged-other-anchor-old-old``
    A candidate interior lies on a secant from a source endpoint to any other
    transformed completed-L8 anchor.

The output contains reconstructible, fixed-length little-endian word bitsets,
deduplicated and compressed with zlib.  Mask hashes are SHA-256 hashes of the
uncompressed fixed-length bytes.  Domain models are built, scanned, and
released one step type at a time.  Direction indexes make the all-anchor join
exact without a corridor-by-anchor probe loop.

Run from the repository root on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l9_anchor_age2_precursor.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l9_anchor_age2_precursor.py run \
        --output /tmp/l9-anchor-age2-precursor.json

The exact run is intentionally not an L9 walk generator.  In particular, a
word surviving the masks here can still be killed by an untagged-anchor
failure or by earlier L9 connector interiors in any eventual stitch schedule.
"""

from __future__ import annotations

import argparse
import base64
import gc
import hashlib
import json
import math
import os
import pickle
import sys
import tempfile
import time
import zlib
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_LEVEL = 7
PARENT_LEVEL = 8
TARGET_LEVEL = 9
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MENU = tuple(
    (x, y, z)
    for x, y, z in product(range(-2, 3), repeat=3)
    if (x, y, z) != (0, 0, 0)
)
IDX = {step: index for index, step in enumerate(MENU)}
FRAGILE_CUT = 2_000

DEFAULT_TRACE = Path("/tmp/far-secant-birth-shell-trace-canonical.json")
EXPECTED_TRACE_SHA256 = (
    "5c525ef4cc0c77ed96a2f67238e785d0382ead806f96479854a691498de99488"
)
EXPECTED_TRACE_CHECKER_SHA256 = (
    "dd35f8ac5459d6df05d8b960f82b709f69380268ed144ac5c0e6789d178c35b9"
)
EXPECTED_FUTURE_CHECKER_SHA256 = (
    "6f286cb118166c1375eb777ec6e24bcdc58766b98538099c604eb97b5c3dd430"
)
EXPECTED_DEEP_RESULT_SHA256 = (
    "7195c4d72a71c0b819da1c2d9ba16165ea2aa1c71ffdfd61ae980fc7975388ab"
)
EXPECTED_DEEP_CHECKER_SHA256 = (
    "cde329fafc79ec95ea0f3d8d8a060219af45633f6414f7f3fb8426fad4888be7"
)

# These are the repository inputs directly consumed here, plus the pinned
# authoritative implementations whose geometry/domain semantics are copied
# below.  Standard-library modules are the only imports.
EXPECTED_REPOSITORY_INPUT_SHA256 = {
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
    ),
    "gate2-l7-construction-L8.pkl": (
        "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141"
    ),
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "dstar5_fragile.pkl": (
        "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3"
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
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
    "design/deep_incidence_lineage.py": EXPECTED_DEEP_CHECKER_SHA256,
    "design/far_secant_future_trace.py": EXPECTED_FUTURE_CHECKER_SHA256,
    "design/far_secant_birth_shell_trace.py": EXPECTED_TRACE_CHECKER_SHA256,
}

EXPECTED_CORE_CENSUS = {
    "parent_states": 42,
    "child_states": 146,
    "effect_records": 64,
    "strict_join_residual_states": 61,
    "correlated_descriptor_terms": 94,
    "unique_correlated_descriptors": 32,
    "inherited_descriptor_terms": 53,
    "current_descriptor_terms": 29,
    "direct_descriptor_terms": 12,
    "records_with_inherited_partner_terms": 43,
    "records_with_current_partner_terms": 28,
    "records_with_both_partner_ages": 10,
}

EXPECTED_PARENT_IDENTITY_STREAM_SHA256 = (
    "58cd87a92f28dbc1c16df8193bfba19695f50063c122c34d376365dc21bc7df3"
)
EXPECTED_CHILD_IDENTITY_STREAM_SHA256 = (
    "fa061a23af382b3e8b005f848c86983b0817bec9b476e1bd3426674df22bcf9a"
)
EXPECTED_DESCENDANT_IDENTITY_STREAM_SHA256 = (
    "25f2ed5965c68a3ed91175a040bb68940899a548cf2637c5e2f4746dd7d90361"
)
EXPECTED_DESCENDANT_GAP_STREAM_SHA256 = (
    "c983ad2a8af899460beeb91c3a6fae0b790e5c7251bec1f586fc6322fff355a9"
)

SOURCE_DEFINITIONS = {
    13171: {
        "witness_type": "old-old-secant",
        "tagged_endpoint_stable_ids": (
            "connector:L7:G12291:I1",
            "connector:L7:G12324:I2",
        ),
        "expected_parent_states": 27,
        "expected_child_states": 89,
        "expected_descendant_corridors": 305,
    },
    21115: {
        "witness_type": "old-new-new-line",
        "tagged_endpoint_stable_ids": (
            "connector:L7:G19950:I2",
        ),
        "expected_parent_states": 15,
        "expected_child_states": 57,
        "expected_descendant_corridors": 183,
    },
}
ALL_TAGGED_STABLE_IDS = tuple(
    stable_id
    for source in SOURCE_DEFINITIONS.values()
    for stable_id in source["tagged_endpoint_stable_ids"]
)
EXPECTED_TAGGED_L8_PATH_INDEX = {
    "connector:L7:G12291:I1": 138424,
    "connector:L7:G12324:I2": 138810,
    "connector:L7:G19950:I2": 224864,
}

CHANNELS = (
    "collision",
    "endpoint-old-new-new",
    "tagged-tagged-old-old",
    "tagged-other-anchor-old-old",
)
PRIORITY_CHANNELS = CHANNELS

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

# Run-time model totals are asserted after the 90 domains are built.  They
# were independently audited from the pinned canonical L8 domain census.
EXPECTED_OPERATION_CENSUS = {
    "effective_domains": 90,
    "distinct_domain_words": 8_530_195,
    "corridor_weighted_domain_words": 50_221_944,
    "endpoint_corridor_weighted_domain_words": 81_133_048,
    "distinct_site_atoms": 23_484,
    "corridor_weighted_site_atoms": 117_408,
    "endpoint_corridor_weighted_site_atoms": 189_830,
    "distinct_line_atoms": 453_212,
    "corridor_weighted_line_atoms": 2_212_551,
    "endpoint_corridor_weighted_line_atoms": 3_568_897,
    "distinct_line_directions": 13_440,
    "corridor_weighted_line_directions": 66_802,
    "endpoint_corridor_weighted_line_directions": 107_789,
}


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


def apply(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def sub(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive(vector):
    divisor = math.gcd(
        math.gcd(abs(vector[0]), abs(vector[1])), abs(vector[2])
    )
    if divisor == 0:
        return None
    result = tuple(coordinate // divisor for coordinate in vector)
    for coordinate in result:
        if coordinate < 0:
            return tuple(-value for value in result)
        if coordinate > 0:
            return result
    raise AssertionError("nonzero primitive direction lost its sign")


def line_key(first, second):
    direction = primitive(sub(second, first))
    if direction is None:
        raise ValueError("line through a repeated point")
    return direction, cross(first, direction)


def word_offsets(word):
    position = (0, 0, 0)
    offsets = []
    for step in word[:-1]:
        position = add(position, MENU[step])
        offsets.append(position)
    return offsets


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "all thread-cap environment variables must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process nice level on this platform")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 15:
        raise RuntimeError(
            f"run under `nice -n 15`; observed process nice value is {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def validate_inputs(trace_path):
    observed = {
        name: file_sha256(ROOT / name)
        for name in EXPECTED_REPOSITORY_INPUT_SHA256
    }
    assert observed == EXPECTED_REPOSITORY_INPUT_SHA256
    trace_path = trace_path.resolve()
    trace_hash = file_sha256(trace_path)
    if trace_hash != EXPECTED_TRACE_SHA256:
        raise RuntimeError(
            f"upstream trace hash {trace_hash}, expected {EXPECTED_TRACE_SHA256}"
        )
    trace = json.loads(trace_path.read_text())
    assert trace["checker_sha256"] == EXPECTED_TRACE_CHECKER_SHA256
    assert trace["future_trace_checker_sha256"] == EXPECTED_FUTURE_CHECKER_SHA256
    assert trace["deep_result_sha256"] == EXPECTED_DEEP_RESULT_SHA256
    assert trace["input_sha256"]["design/deep_incidence_lineage.py"] == (
        EXPECTED_DEEP_CHECKER_SHA256
    )
    assert trace["input_sha256"]["gate2-l7-construction-L8.pkl"] == (
        EXPECTED_REPOSITORY_INPUT_SHA256["gate2-l7-construction-L8.pkl"]
    )
    assert trace["input_sha256"]["viz/walk3d-data.json"] == (
        EXPECTED_REPOSITORY_INPUT_SHA256["viz/walk3d-data.json"]
    )
    assert trace["core_census"] == EXPECTED_CORE_CENSUS
    assert trace["scope"] == {
        "actual_connector_choices_retained": True,
        "alternate_connector_histories": False,
        "endpoint_or_distance_cutoff": None,
        "levels": [7, 8],
        "ordered_parent_child_blocks_retained": True,
        "raw_connector_domain_masks_reconstructed": False,
        "sig_2_or_L9_available": False,
    }
    return trace, observed, trace_hash


def load_structural_inputs():
    viz = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    with (ROOT / "gate2-l7-construction-L8.pkl").open("rb") as handle:
        state8 = pickle.load(handle)
    return viz, state8


def load_domains():
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        base = pickle.load(handle)
    assert tuple(map(tuple, base["menu"])) == MENU
    domains = {
        int(step): sorted(words, key=len)
        for step, words in base["domains"].items()
    }
    base_sizes = {step: len(words) for step, words in domains.items()}
    with (ROOT / "dstar5_fragile.pkl").open("rb") as handle:
        fragile = pickle.load(handle)
    for vector, words in fragile.items():
        step = IDX[tuple(vector)]
        assert base_sizes[step] < FRAGILE_CUT
        domains[step] = domains[step] + [
            tuple(IDX[tuple(menu_step)] for menu_step in word)
            for word in words
        ]
    return domains


def build_path_origins(viz):
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
    for level in range(1, PARENT_LEVEL + 1):
        parents = viz["levels"][level]["parents"]
        assert len(parents) == len(points_by_level[level])
        block_start = {}
        current = []
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
        stable_ids = [record["stable_id"] for record in current]
        assert len(stable_ids) == len(set(stable_ids))
        origins[level] = current
    return points_by_level, origins


def reconstruct_completed_l8(viz, state8):
    anchors = [tuple(point) for point in state8["anchors"]]
    assert len(anchors) == 92_732
    assert len(state8["parent_word"]) == len(state8["order"]) == 92_731
    assert set(state8["words"]) == set(range(92_731))
    points = [anchors[0]]
    block_start = {}
    words = {}
    for gap in range(len(anchors) - 1):
        assert points[-1] == anchors[gap]
        block_start[gap] = len(points) - 1
        word = tuple(state8["words"][gap])
        assert 2 <= len(word) <= 5
        words[gap] = word
        position = anchors[gap]
        for step in word:
            assert 0 <= step < len(MENU)
            position = add(position, MENU[step])
            points.append(position)
        assert position == anchors[gap + 1]

    points8 = [tuple(point) for point in viz["levels"][PARENT_LEVEL]["points"]]
    parents8 = list(viz["levels"][PARENT_LEVEL]["parents"])
    assert points == points8
    assert len(points8) == len(parents8) == 311_738
    for gap, start in block_start.items():
        stop = start + len(words[gap])
        assert parents8[start:stop] == [gap] * len(words[gap])
        assert parents8[stop] == gap + 1
    return points8, parents8, block_start, words


def derive_lineage(trace, block_start, words):
    parent_identities = []
    for record in trace["parent_states"]:
        parent_identities.append([
            record["source_gap"],
            record["l7_parent_gap"],
            record["step"],
            record["actual_selected_connector_word"],
            record["ordered_l8_child_gaps"],
        ])
    parent_identities.sort()
    assert len(parent_identities) == len(set(map(stable_hash, parent_identities))) == 42
    assert stable_hash(parent_identities) == EXPECTED_PARENT_IDENTITY_STREAM_SHA256

    child_identities = []
    descendants = []
    for child in trace["child_states"]:
        source_gap = child["source_gap"]
        assert source_gap in SOURCE_DEFINITIONS
        assert child["witness_type"] == SOURCE_DEFINITIONS[source_gap][
            "witness_type"
        ]
        l8_gap = child["l8_gap"]
        word = words[l8_gap]
        assert list(word) == child["actual_selected_connector_word"]
        child_identities.append([
            source_gap,
            child["l7_parent_gap"],
            l8_gap,
            child["step"],
            list(word),
            child["actual_parent_connector_step_slot_zero_based"],
        ])
        for slot, step in enumerate(word):
            descendants.append({
                "schema": "realized-L9-descendant-corridor-v1",
                "source_gap": source_gap,
                "source_witness_type": child["witness_type"],
                "l7_parent_gap": child["l7_parent_gap"],
                "l8_gap": l8_gap,
                "l8_child_state_sha256": stable_hash(child),
                "actual_selected_l8_connector_word": list(word),
                "l9_gap": block_start[l8_gap] + slot,
                "actual_l8_connector_step_slot_zero_based": slot,
                "step": step,
                "selected_l9_connector_word": None,
            })
    child_identities.sort()
    assert len(child_identities) == len(set(map(stable_hash, child_identities))) == 146
    assert stable_hash(child_identities) == EXPECTED_CHILD_IDENTITY_STREAM_SHA256

    descendants.sort(key=lambda record: (
        record["source_gap"], record["l8_gap"],
        record["actual_l8_connector_step_slot_zero_based"],
    ))
    descendant_identities = [
        [
            record["source_gap"],
            record["l7_parent_gap"],
            record["l8_gap"],
            record["l9_gap"],
            record["actual_l8_connector_step_slot_zero_based"],
            record["step"],
            record["actual_selected_l8_connector_word"],
        ]
        for record in descendants
    ]
    assert len(descendants) == len({record["l9_gap"] for record in descendants})
    assert len(descendants) == 488
    assert stable_hash(descendant_identities) == (
        EXPECTED_DESCENDANT_IDENTITY_STREAM_SHA256
    )
    gaps = sorted(record["l9_gap"] for record in descendants)
    assert stable_hash(gaps) == EXPECTED_DESCENDANT_GAP_STREAM_SHA256
    assert (min(gaps), max(gaps)) == (138_338, 230_558)
    assert len({record["step"] for record in descendants}) == 90

    parent_counts = Counter(record[0] for record in parent_identities)
    child_counts = Counter(record[0] for record in child_identities)
    descendant_counts = Counter(record["source_gap"] for record in descendants)
    for source_gap, definition in SOURCE_DEFINITIONS.items():
        assert parent_counts[source_gap] == definition["expected_parent_states"]
        assert child_counts[source_gap] == definition["expected_child_states"]
        assert descendant_counts[source_gap] == (
            definition["expected_descendant_corridors"]
        )
    return descendants, {
        "parent_states": len(parent_identities),
        "parent_identity_stream_sha256": stable_hash(parent_identities),
        "child_states": len(child_identities),
        "child_identity_stream_sha256": stable_hash(child_identities),
        "descendant_corridors": len(descendants),
        "descendant_identity_stream_sha256": stable_hash(descendant_identities),
        "descendant_gap_stream_sha256": stable_hash(gaps),
        "descendant_gap_range": [min(gaps), max(gaps)],
        "effective_step_domains": len({record["step"] for record in descendants}),
        "per_source": {
            str(source_gap): {
                "parent_states": parent_counts[source_gap],
                "child_states": child_counts[source_gap],
                "descendant_corridors": descendant_counts[source_gap],
            }
            for source_gap in sorted(SOURCE_DEFINITIONS)
        },
    }


def point_profile(index, anchors9, origins8):
    origin = origins8[index]
    return {
        "stable_id": origin["stable_id"],
        "l8_path_index_and_l9_anchor_index": index,
        "l9_coordinate": as_json(anchors9[index]),
        "birth_level": origin["birth_level"],
        "age_at_l9": TARGET_LEVEL - origin["birth_level"],
        "birth_gap": origin["birth_gap"],
        "interior_ordinal": origin["interior_ordinal"],
        "birth_parent_endpoint_stable_ids": origin[
            "birth_parent_endpoint_stable_ids"
        ],
    }


def build_anchor_skeleton(points8, origins8):
    anchors9 = [apply(M_BAL3, point) for point in points8]
    assert len(anchors9) == len(set(anchors9)) == 311_738
    assert len(origins8) == len(anchors9)
    stable_to_index = {
        origin["stable_id"]: index for index, origin in enumerate(origins8)
    }
    assert len(stable_to_index) == len(origins8)
    endpoints = {}
    for stable_id in ALL_TAGGED_STABLE_IDS:
        index = stable_to_index[stable_id]
        assert index == EXPECTED_TAGGED_L8_PATH_INDEX[stable_id]
        profile = point_profile(index, anchors9, origins8)
        assert profile["birth_level"] == SOURCE_LEVEL
        assert profile["age_at_l9"] == 2
        profile["l8_coordinate"] = as_json(points8[index])
        assert tuple(profile["l9_coordinate"]) == apply(
            M_BAL3, tuple(profile["l8_coordinate"])
        )
        endpoints[stable_id] = profile

    digest = hashlib.sha256()
    for index, (point, origin) in enumerate(zip(anchors9, origins8)):
        digest.update(stable_bytes((
            index, point, origin["stable_id"], origin["birth_level"],
            origin["birth_gap"], origin["interior_ordinal"],
        )))
        digest.update(b"\n")
    spans = [
        max(point[axis] for point in anchors9)
        - min(point[axis] for point in anchors9)
        for axis in range(3)
    ]
    return anchors9, endpoints, {
        "completed_l8_points": len(points8),
        "complete_initial_l9_anchors": len(anchors9),
        "anchor_identity_coordinate_stream_sha256": digest.hexdigest(),
        "coordinate_spans": spans,
        "tagged_endpoint_profiles": [
            endpoints[stable_id] for stable_id in ALL_TAGGED_STABLE_IDS
        ],
        "omitted_current_l9_connector_interiors": True,
    }


def build_direction_indexes(endpoints, anchors9):
    indexes = {}
    summaries = []
    for stable_id in ALL_TAGGED_STABLE_IDS:
        endpoint = endpoints[stable_id]
        coordinate = tuple(endpoint["l9_coordinate"])
        index = {}
        digest = hashlib.sha256()
        for partner_index, partner in enumerate(anchors9):
            if partner == coordinate:
                assert partner_index == endpoint[
                    "l8_path_index_and_l9_anchor_index"
                ]
                continue
            direction = primitive(sub(partner, coordinate))
            assert direction is not None
            assert direction not in index, (
                "three collinear inherited L9 anchors through tagged endpoint",
                stable_id, direction, index.get(direction), partner_index,
            )
            index[direction] = partner_index
        for direction, partner_index in sorted(index.items()):
            digest.update(stable_bytes((
                direction, partner_index, anchors9[partner_index]
            )))
            digest.update(b"\n")
        assert len(index) == len(anchors9) - 1
        indexes[stable_id] = index
        summaries.append({
            "tagged_endpoint_stable_id": stable_id,
            "directions": len(index),
            "direction_index_sha256": digest.hexdigest(),
            "endpoint_cutoff": None,
            "distance_cutoff": None,
        })
    return indexes, summaries


def compact_domain_model(domain, step):
    site_id = {}
    line_id = {}
    atom_desc = []
    expected_endpoint = apply(M_BAL3, MENU[step])

    def add_site(offset):
        if offset not in site_id:
            site_id[offset] = len(atom_desc)
            atom_desc.append(("site", offset))

    def add_line(key):
        if key not in line_id:
            line_id[key] = len(atom_desc)
            atom_desc.append(("line", key))

    for word_index, word in enumerate(domain):
        position = (0, 0, 0)
        offsets = []
        for ordinal, menu_index in enumerate(word):
            position = add(position, MENU[menu_index])
            if ordinal + 1 < len(word):
                offsets.append(position)
        assert position == expected_endpoint, (
            "connector word has wrong endpoint", step, word_index, word,
            position, expected_endpoint,
        )
        for offset in offsets:
            add_site(offset)
        for left, first in enumerate(offsets):
            for second in offsets[left + 1:]:
                add_line(line_key(first, second))

    line_by_direction = defaultdict(dict)
    for (direction, moment), atom in line_id.items():
        line_by_direction[direction][moment] = atom
    return {
        "site_id": site_id,
        "line_id": line_id,
        "line_by_direction": dict(line_by_direction),
        "atom_desc": atom_desc,
        "expected_endpoint": expected_endpoint,
    }


def add_witness(witnesses, atom, witness):
    encoded = stable_hash(witness)
    known = {stable_hash(record) for record in witnesses[atom]}
    if encoded not in known:
        witnesses[atom].append(witness)


def evaluate_corridor(
    target, model, anchors9, origins8, endpoints, direction_indexes,
    partner_profiles,
):
    source_gap = target["source_gap"]
    source = SOURCE_DEFINITIONS[source_gap]
    gap = target["l9_gap"]
    step = target["step"]
    start = anchors9[gap]
    end = anchors9[gap + 1]
    assert sub(end, start) == model["expected_endpoint"] == apply(
        M_BAL3, MENU[step]
    )
    witnesses = defaultdict(list)

    for stable_id in source["tagged_endpoint_stable_ids"]:
        endpoint = endpoints[stable_id]
        endpoint_coordinate = tuple(endpoint["l9_coordinate"])
        endpoint_relative = sub(endpoint_coordinate, start)
        direction_index = direction_indexes[stable_id]

        collision_atom = model["site_id"].get(endpoint_relative)
        if collision_atom is not None:
            add_witness(witnesses, collision_atom, {
                "channel": "collision",
                "tagged_endpoint_stable_id": stable_id,
                "tagged_endpoint_birth_level": endpoint["birth_level"],
                "tagged_endpoint_age_at_l9": endpoint["age_at_l9"],
                "tagged_endpoint_relative_to_corridor_start": as_json(
                    endpoint_relative
                ),
                "candidate_site_coordinate": as_json(endpoint_coordinate),
                "partner_stable_id": None,
            })

        for direction, by_moment in model["line_by_direction"].items():
            atom = by_moment.get(cross(endpoint_relative, direction))
            if atom is None:
                continue
            description = model["atom_desc"][atom]
            assert description[0] == "line"
            local_direction, local_moment = description[1]
            absolute_moment = add(cross(start, local_direction), local_moment)
            assert cross(endpoint_coordinate, local_direction) == absolute_moment
            add_witness(witnesses, atom, {
                "channel": "endpoint-old-new-new",
                "tagged_endpoint_stable_id": stable_id,
                "tagged_endpoint_birth_level": endpoint["birth_level"],
                "tagged_endpoint_age_at_l9": endpoint["age_at_l9"],
                "tagged_endpoint_relative_to_corridor_start": as_json(
                    endpoint_relative
                ),
                "absolute_candidate_line": as_json((
                    local_direction, absolute_moment
                )),
                "partner_stable_id": None,
            })

        for offset, atom in model["site_id"].items():
            query = add(start, offset)
            if query == endpoint_coordinate:
                continue
            direction = primitive(sub(query, endpoint_coordinate))
            assert direction is not None
            partner_index = direction_index.get(direction)
            if partner_index is None:
                continue
            partner_coordinate = anchors9[partner_index]
            if partner_coordinate == query:
                # This is an existing-anchor collision, not a secant through
                # three distinct points.  Untagged collisions are outside the
                # tagged-endpoint component; a tagged collision is found when
                # that endpoint belongs to the source endpoint set.
                continue
            assert len({endpoint_coordinate, partner_coordinate, query}) == 3
            absolute_line = line_key(endpoint_coordinate, partner_coordinate)
            assert cross(query, absolute_line[0]) == absolute_line[1]
            partner = point_profile(partner_index, anchors9, origins8)
            partner_profiles[partner["stable_id"]] = partner
            channel = (
                "tagged-tagged-old-old"
                if partner["stable_id"] in ALL_TAGGED_STABLE_IDS
                else "tagged-other-anchor-old-old"
            )
            add_witness(witnesses, atom, {
                "channel": channel,
                "tagged_endpoint_stable_id": stable_id,
                "tagged_endpoint_birth_level": endpoint["birth_level"],
                "tagged_endpoint_age_at_l9": endpoint["age_at_l9"],
                "tagged_endpoint_relative_to_corridor_start": as_json(
                    endpoint_relative
                ),
                "partner_stable_id": partner["stable_id"],
                "partner_birth_level": partner["birth_level"],
                "partner_age_at_l9": partner["age_at_l9"],
                "partner_relative_to_corridor_start": as_json(
                    sub(partner_coordinate, start)
                ),
                "candidate_site_coordinate": as_json(query),
                "absolute_witness_line": as_json(absolute_line),
            })

    return {
        **target,
        "l9_corridor_start": as_json(start),
        "l9_corridor_end": as_json(end),
        "ordered_corridor_endpoint_stable_ids": [
            origins8[gap]["stable_id"], origins8[gap + 1]["stable_id"]
        ],
        "source_tagged_endpoint_stable_ids": list(
            source["tagged_endpoint_stable_ids"]
        ),
        "domain_words": None,
        "atom_witnesses": dict(witnesses),
    }


def requested_atom_word_bits(
    domain, model, requested, endpoint_line_terms,
):
    bits = {atom: 0 for atom in requested}
    endpoint_line_bits = {term: 0 for term in endpoint_line_terms}
    line_terms_by_atom = defaultdict(set)
    for atom, endpoint_relative in endpoint_line_terms:
        line_terms_by_atom[atom].add(endpoint_relative)
    if not requested and not endpoint_line_terms:
        return bits, endpoint_line_bits
    for word_index, word in enumerate(domain):
        offsets = word_offsets(word)
        present = set()
        present_endpoint_line_terms = set()
        for offset in offsets:
            atom = model["site_id"][offset]
            if atom in requested:
                present.add(atom)
        for left, first in enumerate(offsets):
            for second in offsets[left + 1:]:
                atom = model["line_id"][line_key(first, second)]
                if atom in requested:
                    present.add(atom)
                # The endpoint lies on this line by construction of each
                # requested term.  It is a genuine old-new-new witness only
                # when the two candidate interiors in this particular word
                # are both distinct from that endpoint.  This retains a line
                # witness when a colliding word also has another valid pair;
                # a blanket subtraction of the collision mask would not.
                for endpoint_relative in line_terms_by_atom.get(atom, ()):
                    if first != endpoint_relative and second != endpoint_relative:
                        present_endpoint_line_terms.add((
                            atom, endpoint_relative
                        ))
        flag = 1 << word_index
        for atom in present:
            bits[atom] |= flag
        for term in present_endpoint_line_terms:
            endpoint_line_bits[term] |= flag
    return bits, endpoint_line_bits


def exact_mask_record(bits, domain_words, payload_store):
    raw_size = (domain_words + 7) // 8
    raw = bits.to_bytes(raw_size, "little")
    digest = hashlib.sha256(raw).hexdigest()
    reference = f"{domain_words}:{digest}"
    if reference not in payload_store:
        compressed = zlib.compress(raw, level=9)
        payload_store[reference] = {
            "domain_words": domain_words,
            "uncompressed_bytes": raw_size,
            "encoding": (
                "zlib+base64 of fixed-length little-endian word-membership "
                "bitset; bit i is domain word i"
            ),
            "zlib_bytes": len(compressed),
            "payload_base64": base64.b64encode(compressed).decode("ascii"),
        }
    return {
        "domain_words": domain_words,
        "killed_words": bits.bit_count(),
        "mask_sha256": digest,
        "exact_payload_ref": reference,
    }


def finalize_corridor(
    record, model, bits_by_atom, endpoint_line_bits, domain_words,
    payload_store,
):
    atom_witnesses = record.pop("atom_witnesses")
    record["domain_words"] = domain_words
    channel_bits = {channel: 0 for channel in CHANNELS}
    endpoint_bits = {
        stable_id: 0
        for stable_id in record["source_tagged_endpoint_stable_ids"]
    }
    partner_bits = defaultdict(int)
    partner_birth_bits = defaultdict(int)
    atom_records = []
    positive_effect_atoms = 0
    for atom in sorted(atom_witnesses):
        witnesses = sorted(atom_witnesses[atom], key=stable_hash)
        atom_contribution = 0
        for witness in witnesses:
            channel = witness["channel"]
            assert channel in channel_bits
            if channel == "endpoint-old-new-new":
                term = (
                    atom,
                    tuple(witness[
                        "tagged_endpoint_relative_to_corridor_start"
                    ]),
                )
                contribution = endpoint_line_bits[term]
            else:
                contribution = bits_by_atom[atom]
            atom_contribution |= contribution
            channel_bits[channel] |= contribution
            endpoint_bits[witness["tagged_endpoint_stable_id"]] |= contribution
            partner_stable_id = witness.get("partner_stable_id")
            if partner_stable_id is not None:
                partner_bits[partner_stable_id] |= contribution
                partner_birth_bits[witness["partner_birth_level"]] |= contribution
        if atom_contribution:
            positive_effect_atoms += 1
        atom_records.append({
            "atom_id": atom,
            "atom": as_json(model["atom_desc"][atom]),
            "witnesses": witnesses,
            "exact_witness_union_mask": exact_mask_record(
                atom_contribution, domain_words, payload_store
            ),
        })

    all_bits = 0
    for bits in channel_bits.values():
        all_bits |= bits
    record["exact_overlapping_channel_masks"] = {
        channel: exact_mask_record(bits, domain_words, payload_store)
        for channel, bits in channel_bits.items()
    }
    record["exact_tagged_age2_anchor_component_mask"] = exact_mask_record(
        all_bits, domain_words, payload_store
    )
    record["tagged_component_survivors_not_full_legality"] = (
        domain_words - all_bits.bit_count()
    )

    claimed = 0
    priority_partition = {}
    for channel in PRIORITY_CHANNELS:
        disjoint = channel_bits[channel] & ~claimed
        priority_partition[channel] = exact_mask_record(
            disjoint, domain_words, payload_store
        )
        claimed |= channel_bits[channel]
    assert claimed == all_bits
    record["exact_disjoint_priority_partition"] = {
        "priority": list(PRIORITY_CHANNELS),
        "semantic_warning": (
            "priority makes reporting disjoint; it does not assign a unique "
            "geometric cause to words having multiple witnesses"
        ),
        "masks": priority_partition,
    }
    record["exact_endpoint_masks_overlap"] = {
        stable_id: exact_mask_record(
            bits, domain_words, payload_store
        )
        for stable_id, bits in sorted(endpoint_bits.items())
    }
    record["exact_partner_masks_overlap"] = {
        stable_id: exact_mask_record(
            bits, domain_words, payload_store
        )
        for stable_id, bits in sorted(partner_bits.items())
    }
    record["exact_partner_birth_level_masks_overlap"] = {
        str(level): exact_mask_record(
            bits, domain_words, payload_store
        )
        for level, bits in sorted(partner_birth_bits.items())
    }
    record["atoms"] = atom_records
    record["witness_atoms"] = len(atom_records)
    record["positive_effect_atoms"] = positive_effect_atoms
    record["effectful"] = bool(all_bits)
    record["abstract_observation_sha256"] = stable_hash({
        "source_gap": record["source_gap"],
        "step": record["step"],
        "actual_selected_l8_connector_word": record[
            "actual_selected_l8_connector_word"
        ],
        "slot": record["actual_l8_connector_step_slot_zero_based"],
        "ordered_corridor_endpoint_stable_ids": record[
            "ordered_corridor_endpoint_stable_ids"
        ],
        "source_tagged_endpoint_stable_ids": record[
            "source_tagged_endpoint_stable_ids"
        ],
        "channel_masks": record["exact_overlapping_channel_masks"],
        "partner_profiles": sorted(partner_bits),
        "partner_birth_levels": sorted(partner_birth_bits),
    })
    return record, channel_bits


def direct_word_geometry_backstop(
    record, domain, anchors9, origins8, endpoints, direction_indexes,
):
    """Recompute all four masks directly, without the atom composition."""
    source = SOURCE_DEFINITIONS[record["source_gap"]]
    start = anchors9[record["l9_gap"]]
    channel_bits = {channel: 0 for channel in CHANNELS}
    for word_index, word in enumerate(domain):
        candidates = [add(start, offset) for offset in word_offsets(word)]
        present = set()
        for stable_id in source["tagged_endpoint_stable_ids"]:
            endpoint_coordinate = tuple(endpoints[stable_id]["l9_coordinate"])
            if endpoint_coordinate in candidates:
                present.add("collision")

            for left, first in enumerate(candidates):
                if first == endpoint_coordinate:
                    continue
                for second in candidates[left + 1:]:
                    if second == endpoint_coordinate:
                        continue
                    if cross(
                        sub(first, endpoint_coordinate),
                        sub(second, endpoint_coordinate),
                    ) == (0, 0, 0):
                        present.add("endpoint-old-new-new")

            direction_index = direction_indexes[stable_id]
            for candidate in candidates:
                if candidate == endpoint_coordinate:
                    continue
                direction = primitive(sub(candidate, endpoint_coordinate))
                assert direction is not None
                partner_index = direction_index.get(direction)
                if partner_index is None:
                    continue
                partner_coordinate = anchors9[partner_index]
                if partner_coordinate == candidate:
                    continue
                assert len({
                    endpoint_coordinate, partner_coordinate, candidate
                }) == 3
                absolute_line = line_key(
                    endpoint_coordinate, partner_coordinate
                )
                assert cross(
                    candidate, absolute_line[0]
                ) == absolute_line[1]
                partner_stable_id = origins8[partner_index]["stable_id"]
                present.add(
                    "tagged-tagged-old-old"
                    if partner_stable_id in ALL_TAGGED_STABLE_IDS
                    else "tagged-other-anchor-old-old"
                )

        flag = 1 << word_index
        for channel in present:
            channel_bits[channel] |= flag
    return channel_bits


def operation_census(model_census, targets):
    count_by_step = Counter(record["step"] for record in targets)
    endpoint_count_by_step = Counter()
    for record in targets:
        endpoint_count_by_step[record["step"]] += len(
            SOURCE_DEFINITIONS[record["source_gap"]][
                "tagged_endpoint_stable_ids"
            ]
        )
    models = {record["step"]: record for record in model_census}
    census = {
        "effective_domains": len(models),
        "distinct_domain_words": sum(
            record["domain_words"] for record in model_census
        ),
        "corridor_weighted_domain_words": sum(
            count_by_step[step] * models[step]["domain_words"] for step in models
        ),
        "endpoint_corridor_weighted_domain_words": sum(
            endpoint_count_by_step[step] * models[step]["domain_words"]
            for step in models
        ),
        "distinct_site_atoms": sum(
            record["site_atoms"] for record in model_census
        ),
        "corridor_weighted_site_atoms": sum(
            count_by_step[step] * models[step]["site_atoms"] for step in models
        ),
        "endpoint_corridor_weighted_site_atoms": sum(
            endpoint_count_by_step[step] * models[step]["site_atoms"]
            for step in models
        ),
        "distinct_line_atoms": sum(
            record["line_atoms"] for record in model_census
        ),
        "corridor_weighted_line_atoms": sum(
            count_by_step[step] * models[step]["line_atoms"] for step in models
        ),
        "endpoint_corridor_weighted_line_atoms": sum(
            endpoint_count_by_step[step] * models[step]["line_atoms"]
            for step in models
        ),
        "distinct_line_directions": sum(
            record["line_directions"] for record in model_census
        ),
        "corridor_weighted_line_directions": sum(
            count_by_step[step] * models[step]["line_directions"]
            for step in models
        ),
        "endpoint_corridor_weighted_line_directions": sum(
            endpoint_count_by_step[step] * models[step]["line_directions"]
            for step in models
        ),
    }
    assert census == EXPECTED_OPERATION_CENSUS
    return census


def structural_context(trace):
    viz, state8 = load_structural_inputs()
    points_by_level, origins = build_path_origins(viz)
    points8, parents8, block_start, words = reconstruct_completed_l8(viz, state8)
    assert points_by_level[PARENT_LEVEL] == points8
    targets, lineage = derive_lineage(trace, block_start, words)
    anchors9, endpoints, anchor_summary = build_anchor_skeleton(
        points8, origins[PARENT_LEVEL]
    )
    for target in targets:
        gap = target["l9_gap"]
        assert sub(points8[gap + 1], points8[gap]) == MENU[target["step"]]
        assert parents8[gap] == target["l8_gap"]
    return {
        "viz": viz,
        "state8": state8,
        "points_by_level": points_by_level,
        "origins": origins,
        "points8": points8,
        "parents8": parents8,
        "targets": targets,
        "lineage": lineage,
        "anchors9": anchors9,
        "endpoints": endpoints,
        "anchor_summary": anchor_summary,
    }


def estimate_result(trace, trace_hash, observed_inputs, resource_policy):
    context = structural_context(trace)
    targets = context["targets"]
    endpoint_corridors = sum(
        len(SOURCE_DEFINITIONS[record["source_gap"]][
            "tagged_endpoint_stable_ids"
        ])
        for record in targets
    )
    anchors = len(context["anchors9"])
    result = {
        "status": (
            "structural estimate only; connector domains, direction indexes, "
            "incidences, and killed-word masks were not scanned"
        ),
        "resource_policy": resource_policy,
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": observed_inputs,
        "upstream_trace_sha256": trace_hash,
        "lineage": context["lineage"],
        "anchor_skeleton": context["anchor_summary"],
        "planned_exact_run": {
            **EXPECTED_OPERATION_CENSUS,
            "source_endpoint_corridor_pairs": endpoint_corridors,
            "one_time_direction_index_entries": len(ALL_TAGGED_STABLE_IDS) * (
                anchors - 1
            ),
            "exact_source_scope_corridor_times_anchor_probes_avoided": (
                endpoint_corridors * anchors
            ),
            "join_plan": (
                "one all-anchor primitive-direction index per tagged endpoint; "
                "then exact candidate-site direction lookups and exact "
                "candidate-line direction/moment joins"
            ),
            "quoted_348m_note": (
                "the earlier approximately 348m broad naive estimate is not "
                "used; exact source ownership gives 247,208,234 direct "
                "corridor-endpoint-anchor probes, all avoided here"
            ),
        },
        "scope_boundary": {
            "complete_transformed_l8_initial_anchor_set": True,
            "l9_connector_choices": False,
            "current_l9_connector_interior_partners": False,
            "full_sig2": False,
            "full_l9_poison_or_legality": False,
            "availability_theorem": False,
        },
    }
    # Release the large structural copies before returning to an interactive
    # caller.  Estimate deliberately never loads either domain pickle.
    del context
    gc.collect()
    return result


def run_result(trace, trace_hash, observed_inputs, resource_policy):
    started = time.time()
    context = structural_context(trace)
    targets = context["targets"]
    anchors9 = context["anchors9"]
    origins8 = context["origins"][PARENT_LEVEL]
    endpoints = context["endpoints"]
    lineage = context["lineage"]
    anchor_summary = context["anchor_summary"]
    # Do not retain the viz object, state pickle, L0--L7 origin tables, or the
    # duplicate completed-L8 coordinate list while loading 8.53m domain words.
    del context
    gc.collect()

    print("building three complete inherited-anchor direction indexes", flush=True)
    direction_indexes, direction_summaries = build_direction_indexes(
        endpoints, anchors9
    )

    targets_by_step = defaultdict(list)
    for target in targets:
        targets_by_step[target["step"]].append(target)
    assert len(targets_by_step) == EXPECTED_OPERATION_CENSUS["effective_domains"]

    # Loading is necessarily monolithic because the canonical inputs are two
    # pickles, but all non-target domains are immediately released and the 90
    # retained domains are modeled/scanned/released strictly sequentially.
    domains = load_domains()
    assert set(targets_by_step) <= set(domains)
    for step in list(domains):
        if step not in targets_by_step:
            del domains[step]
    assert len(domains) == 90
    gc.collect()

    model_census = []
    finalized = []
    partner_profiles = {}
    payload_store = {}
    steps = sorted(targets_by_step)
    stable_target_order = sorted(targets, key=lambda record: record["l9_gap"])
    backstop_roles = {
        stable_target_order[0]["l9_gap"]: "first-target-by-l9-gap",
        stable_target_order[-1]["l9_gap"]: "last-target-by-l9-gap",
    }
    assert tuple(sorted(backstop_roles)) == (138_338, 230_558)
    for ordinal, step in enumerate(steps, 1):
        domain = domains.pop(step)
        print(
            f"domain {ordinal}/90 step {step}: {len(domain)} words, "
            f"{len(targets_by_step[step])} target corridors",
            flush=True,
        )
        model = compact_domain_model(domain, step)
        records = [
            evaluate_corridor(
                target, model, anchors9, origins8, endpoints,
                direction_indexes, partner_profiles,
            )
            for target in targets_by_step[step]
        ]
        requested = set()
        endpoint_line_terms = set()
        for record in records:
            requested.update(record["atom_witnesses"])
            for atom, witnesses in record["atom_witnesses"].items():
                for witness in witnesses:
                    if witness["channel"] == "endpoint-old-new-new":
                        endpoint_line_terms.add((
                            atom,
                            tuple(witness[
                                "tagged_endpoint_relative_to_corridor_start"
                            ]),
                        ))
        bits_by_atom, endpoint_line_bits = requested_atom_word_bits(
            domain, model, requested, endpoint_line_terms
        )
        for record in records:
            final_record, composed_channel_bits = finalize_corridor(
                record, model, bits_by_atom, endpoint_line_bits, len(domain),
                payload_store,
            )
            gap = final_record["l9_gap"]
            if gap in backstop_roles:
                direct_channel_bits = direct_word_geometry_backstop(
                    final_record, domain, anchors9, origins8, endpoints,
                    direction_indexes,
                )
                assert direct_channel_bits == composed_channel_bits
                final_record["direct_full_domain_word_geometry_backstop"] = {
                    "stable_order_role": backstop_roles[gap],
                    "domain_words_recomputed": len(domain),
                    "atom_composition_used": False,
                    "all_four_channel_bitsets_equal_composed_masks": True,
                    "exact_channel_masks": {
                        channel: exact_mask_record(
                            bits, len(domain), payload_store
                        )
                        for channel, bits in direct_channel_bits.items()
                    },
                }
            finalized.append(final_record)
        model_census.append({
            "step": step,
            "domain_words": len(domain),
            "site_atoms": len(model["site_id"]),
            "line_atoms": len(model["line_id"]),
            "line_directions": len(model["line_by_direction"]),
            "requested_witness_atoms": len(requested),
            "target_corridors": len(records),
            "endpoint_corridor_pairs": sum(
                len(SOURCE_DEFINITIONS[record["source_gap"]][
                    "tagged_endpoint_stable_ids"
                ])
                for record in records
            ),
            "expected_scaled_endpoint": as_json(model["expected_endpoint"]),
            "atom_description_sha256": stable_hash(model["atom_desc"]),
            "direct_word_backstop_l9_gaps": sorted(
                record["l9_gap"]
                for record in records
                if record["l9_gap"] in backstop_roles
            ),
        })
        del domain, model, records, requested, endpoint_line_terms
        del bits_by_atom, endpoint_line_bits
        gc.collect()
    assert not domains

    operation_summary = operation_census(model_census, targets)
    finalized.sort(key=lambda record: record["l9_gap"])
    assert len(finalized) == 488
    assert [record["l9_gap"] for record in finalized] == sorted(
        record["l9_gap"] for record in targets
    )
    channel_effectful = Counter()
    channel_killed_sum = Counter()
    for record in finalized:
        for channel, mask in record["exact_overlapping_channel_masks"].items():
            if mask["killed_words"]:
                channel_effectful[channel] += 1
            channel_killed_sum[channel] += mask["killed_words"]
    effectful = [record for record in finalized if record["effectful"]]
    minimum_survivors = min(
        record["tagged_component_survivors_not_full_legality"]
        for record in finalized
    )

    result = {
        "status": (
            "exact 42-to-146-to-488 inherited-anchor age2 tagged-endpoint "
            "precursor; not a full L9 poison, legality, sig2, or availability "
            "certificate"
        ),
        "resource_policy": {
            **resource_policy,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": observed_inputs,
        "upstream_trace": {
            "sha256": trace_hash,
            "checker_sha256": trace["checker_sha256"],
            "future_trace_checker_sha256": trace[
                "future_trace_checker_sha256"
            ],
            "deep_result_sha256": trace["deep_result_sha256"],
        },
        "lineage": lineage,
        "anchor_skeleton": anchor_summary,
        "direction_indexes": direction_summaries,
        "domain_models": {
            "models": model_census,
            "model_census_sha256": stable_hash(model_census),
            "processed_scanned_and_released_sequentially": True,
            "operation_census": operation_summary,
            "direct_full_domain_word_geometry_backstops": [
                {
                    "l9_gap": record["l9_gap"],
                    **record["direct_full_domain_word_geometry_backstop"],
                }
                for record in finalized
                if "direct_full_domain_word_geometry_backstop" in record
            ],
        },
        "exact_mask_store": {
            "semantics": (
                "every referenced payload reconstructs the exact domain-word "
                "bitset; hashes cover uncompressed fixed-length bytes"
            ),
            "unique_payloads": len(payload_store),
            "payloads": dict(sorted(payload_store.items())),
        },
        "partner_profiles": {
            "profiles": [
                partner_profiles[stable_id]
                for stable_id in sorted(partner_profiles)
            ],
            "profile_count": len(partner_profiles),
            "profile_stream_sha256": stable_hash([
                partner_profiles[stable_id]
                for stable_id in sorted(partner_profiles)
            ]),
        },
        "exact_corridor_masks": {
            "records": finalized,
            "record_stream_sha256": stable_hash(finalized),
            "effectful_corridors": len(effectful),
            "zero_effect_corridors": len(finalized) - len(effectful),
            "channel_effectful_corridors": dict(sorted(channel_effectful.items())),
            "channel_killed_word_sum_across_distinct_corridors": dict(
                sorted(channel_killed_sum.items())
            ),
            "minimum_tagged_component_survivors": minimum_survivors,
            "survivor_warning": (
                "survivors avoid only this tagged age2 inherited-anchor "
                "component; they are not legal L9 choices"
            ),
        },
        "scope": {
            "included": [
                "complete transformed completed-L8 path as initial L9 anchors",
                "the three tagged L7 endpoints at age two",
                "tagged endpoint collision with candidate interiors",
                "tagged endpoint on candidate-interior pair lines",
                "tagged-to-tagged and tagged-to-every-other-anchor secants",
                "exact source/corridor/channel/endpoint/partner/birth masks",
            ],
            "endpoint_cutoff": None,
            "distance_cutoff": None,
            "omitted": [
                "all selected L9 connector words (none exists in the inputs)",
                "all current-L9 connector-interior points and partners",
                "poisoning unrelated to the source's tagged endpoints",
                "alternate connector histories and a universal Post relation",
                "full sig2, full L9 legality, positive availability, and an "
                "unconditional Erdos #193 theorem",
            ],
            "soundness_boundary": (
                "every emitted killed bit has an exact tagged endpoint and "
                "initial-anchor/candidate witness.  Omitting L9 connector "
                "interiors makes the mask an under-approximation, so zero or "
                "surviving bits cannot certify complete L9 legality."
            ),
        },
    }
    return result


def atomic_write_json(output, result):
    output = output.resolve()
    if not output.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {output.parent}")
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(payload), file_sha256(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument("--trace-result", type=Path, default=DEFAULT_TRACE)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l9-anchor-age2-precursor.json"),
    )
    arguments = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; certificate assertions must remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resource_policy = enforce_resource_policy()
    trace, observed_inputs, trace_hash = validate_inputs(
        arguments.trace_result
    )
    if arguments.mode == "estimate":
        result = estimate_result(
            trace, trace_hash, observed_inputs, resource_policy
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    result = run_result(trace, trace_hash, observed_inputs, resource_policy)
    byte_count, output_hash = atomic_write_json(arguments.output, result)
    print(json.dumps({
        "output": str(arguments.output.resolve()),
        "bytes": byte_count,
        "sha256": output_hash,
        "effectful_corridors": result["exact_corridor_masks"][
            "effectful_corridors"
        ],
        "minimum_tagged_component_survivors_not_full_legality": result[
            "exact_corridor_masks"
        ]["minimum_tagged_component_survivors"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
