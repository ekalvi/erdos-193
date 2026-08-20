#!/usr/bin/env python3
"""Exact finite future-trace experiment for the three tagged L7 endpoints.

This is a deliberately small follow-up to ``deep_incidence_lineage.py``.  It
does not rescan all connector domains.  Instead it consumes that checker's
pinned, exact L8 endpoint-closure artifact and joins it back to the realized
L7 -> L8 ordered path in the construction pickles.

For every L8 effect of either shell-5 source, the experiment retains the L7
parent corridor that actually generated the L8 corridor.  It then closes the
parent under *all and only* the consecutive segments of the connector word
actually selected at that parent.  A literal state contains:

* stable endpoint identities;
* exact endpoint vectors centered at the corridor start;
* primitive Plucker line data for a carried two-endpoint secant;
* the centered affine image of the original source atom;
* the corridor step and the actual selected connector word; and
* its exact ordered address in the single realized path.

The exact L8 observation is the killed-word mask from the complete tagged
endpoint closure in the deep audit.  Its direct endpoint/carried-line submask
is retained separately.  Therefore the experiment can falsify a quotient
that forgets the tagged-endpoint--other-point join, without pretending to
have recomputed that global join.

The available horizon is only one generation:

``sig_0``
    Exact L8 killed-word observation on a concrete child corridor.

``sig_1``
    Exact ordered list of ``sig_0`` values reached from a concrete L7 parent
    through the connector word actually chosen there.

There is no ``sig_2``.  These endpoints are born in L7, so L5--L6 cannot be
used as predecessor observations; and the repository has no realized L9
connector choices or L9 prefix join closure.  Stabilization of this finite
trace is consequently evidence neither for a universal Post quotient nor for
a contraction lemma.

Run from the repository root on one low-priority thread.  The default deep
artifact is the existing canonical temporary result; regenerate it with the
pinned deep checker if it is absent.

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/far_secant_future_trace.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/far_secant_future_trace.py run \
        --output /tmp/far-secant-future-trace.json

The JSON write is atomic.  No random sampling, endpoint cutoff, distance
cutoff, independent address stream, or alternate connector history is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from imbricate193 import apply  # noqa: E402
from salvage_gate import cross, line_key, primitive, sub  # noqa: E402


SOURCE_LEVEL = 7
TARGET_LEVEL = 8
DEFAULT_DEEP_RESULT = Path(
    "/tmp/deep-incidence-lineage-final-canonical.json"
)
EXPECTED_DEEP_RESULT_SHA256 = (
    "7195c4d72a71c0b819da1c2d9ba16165ea2aa1c71ffdfd61ae980fc7975388ab"
)
EXPECTED_DEEP_CHECKER_SHA256 = (
    "cde329fafc79ec95ea0f3d8d8a060219af45633f6414f7f3fb8426fad4888be7"
)

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
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
    "design/deep_incidence_lineage.py": EXPECTED_DEEP_CHECKER_SHA256,
}

EXPECTED_CLOSURE = {
    "scope": {
        "recorded_l8_stitches": 92731,
        "effective_step_domains": 124,
        "final_l8_points_indexed": 311738,
        "minimum_domain_words": 2570,
        "alternate_histories": False,
        "other_l7_endpoints": False,
        "age_at_least_2": False,
    },
    "model_census_sha256": (
        "bff91ea1ae23aee38c0fab868e704fa83e739f95a80cd00f2b7d98f3cc94d3e9"
    ),
    "combined_occurrence_stream_sha256": (
        "5bc8602fb0abf4552bd46d5679cdd458841947afac6e81f706fdd03c748ee5e9"
    ),
    "source_occurrence_stream_sha256": {
        13171: (
            "af874f391f48f99c24e33df403a95bbd0eb8ef151cfadba7abc2a0b20d1f5990"
        ),
        21115: (
            "46cb1d6bdf929cf925a552e7baa8d3545ee46be0a814d1b4534fcb45bc97f42d"
        ),
    },
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


def bits_sha256(bits, size):
    return hashlib.sha256(
        bits.to_bytes((size + 7) // 8, "little")
    ).hexdigest()


def zero_mask(size):
    return {"words": 0, "mask_sha256": bits_sha256(0, size)}


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def archimedean_shell3(vector):
    """Return k with 3**k <= ||vector||_infinity < 3**(k+1)."""
    norm = max(abs(value) for value in vector)
    if norm == 0:
        return None
    shell = 0
    boundary = 1
    while boundary * 3 <= norm:
        boundary *= 3
        shell += 1
    assert boundary <= norm < 3 * boundary
    return shell


def valuation3_integer(value):
    if value == 0:
        return None
    value = abs(value)
    order = 0
    while value % 3 == 0:
        value //= 3
        order += 1
    return order


def content_valuation3(vector):
    orders = [valuation3_integer(value) for value in vector if value]
    return None if not orders else min(orders)


def vector_profile(vector):
    vector = tuple(vector)
    return {
        "vector": as_json(vector),
        "primitive_direction": as_json(primitive(vector)),
        "chebyshev_norm": max(abs(value) for value in vector),
        "archimedean_3_shell": archimedean_shell3(vector),
        "content_3_adic_valuation": content_valuation3(vector),
    }


def relative_line(absolute_key, start):
    direction, moment = absolute_key
    start_moment = cross(start, direction)
    return direction, tuple(
        moment[axis] - start_moment[axis] for axis in range(3)
    )


def line_profile(key):
    direction, moment = key
    return {
        "primitive_direction": as_json(direction),
        "relative_moment": as_json(moment),
        "moment_chebyshev_norm": max(abs(value) for value in moment),
        "moment_archimedean_3_shell": archimedean_shell3(moment),
        "moment_content_3_adic_valuation": content_valuation3(moment),
    }


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "run requires every thread-cap variable to equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process priority on this platform")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise RuntimeError(
            "run at low priority with `nice -n 15` (minimum accepted nice "
            f"value is 10; observed {priority})"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def load_pickle(name):
    with (ROOT / name).open("rb") as handle:
        return pickle.load(handle)


def validate_inputs(deep_path):
    observed = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed == EXPECTED_INPUT_SHA256
    if not deep_path.is_file():
        raise FileNotFoundError(
            f"missing pinned deep result {deep_path}; regenerate it with "
            "design/deep_incidence_lineage.py"
        )
    deep_hash = file_sha256(deep_path)
    if deep_hash != EXPECTED_DEEP_RESULT_SHA256:
        raise RuntimeError(
            "deep result is not the pinned canonical artifact: "
            f"observed {deep_hash}, expected {EXPECTED_DEEP_RESULT_SHA256}"
        )
    deep = json.loads(deep_path.read_text())
    assert deep["checker_sha256"] == EXPECTED_DEEP_CHECKER_SHA256
    closure = deep["all_domain_endpoint_incidence_closure"]
    assert closure["scope"] == EXPECTED_CLOSURE["scope"]
    assert closure["model_census_sha256"] == EXPECTED_CLOSURE[
        "model_census_sha256"
    ]
    assert closure["combined_three_endpoint_summary"][
        "occurrence_stream_sha256"
    ] == EXPECTED_CLOSURE["combined_occurrence_stream_sha256"]
    for source in closure["per_source"]:
        source_gap = source["source_gap"]
        assert source["summary"]["occurrence_stream_sha256"] == (
            EXPECTED_CLOSURE["source_occurrence_stream_sha256"][source_gap]
        )
    return deep, observed, deep_hash


def block_starts(parents):
    starts = {}
    for index, parent in enumerate(parents):
        if index == 0 or parents[index - 1] != parent:
            assert parent not in starts, (
                "parent blocks must be contiguous and occur exactly once",
                parent,
            )
            starts[parent] = index
    assert len(starts) == len(set(parents))
    return starts


def source_definition(source, state7, state8):
    assert len(source["lineages"]) == 1
    assert len(source["transported_lineages"]) == 1
    lineage = source["lineages"][0]
    transported = source["transported_lineages"][0]
    assert lineage["lineage_index"] == transported["lineage_index"] == 0

    witness_endpoints = {}
    for witness in source["first_shell_5_attaining_witnesses"]:
        for endpoint in witness["placed_endpoints"]:
            stable_id = endpoint["stable_id"]
            coordinate = tuple(endpoint["coordinate"])
            previous = witness_endpoints.setdefault(stable_id, coordinate)
            assert previous == coordinate
    stable_ids = tuple(lineage["source_endpoint_stable_ids"])
    assert set(stable_ids) == set(witness_endpoints)
    source_points = tuple(witness_endpoints[stable_id] for stable_id in stable_ids)

    transported_by_id = {
        endpoint["stable_id"]: endpoint
        for endpoint in transported["transported_endpoints"]
    }
    assert set(transported_by_id) == set(stable_ids)
    target_points = []
    for stable_id, point7 in zip(stable_ids, source_points):
        record = transported_by_id[stable_id]
        point8 = tuple(record["l8_coordinate"])
        assert point8 == apply(M_BAL3, point7)
        assert tuple(state8["anchors"][record["l8_anchor_index"]]) == point8
        target_points.append(point8)

    source_start = tuple(state7["anchors"][source["gap"]])
    atom = source["atom_description"]
    if atom[0] == "site":
        source_image_kind = "point"
        source_image_absolute = add(source_start, tuple(atom[1]))
        target_image_absolute = tuple(transported["direct_image_geometry"])
        assert target_image_absolute == apply(M_BAL3, source_image_absolute)
    else:
        source_image_kind = "line"
        direction = tuple(atom[1][0])
        relative_moment = tuple(atom[1][1])
        source_image_absolute = (
            direction,
            add(cross(source_start, direction), relative_moment),
        )
        target_image_absolute = (
            tuple(transported["direct_image_geometry"][0]),
            tuple(transported["direct_image_geometry"][1]),
        )
        assert primitive(apply(M_BAL3, direction)) == target_image_absolute[0]
        assert all(
            cross(point, direction) == source_image_absolute[1]
            for point in source_points
        )
        assert all(
            cross(point, target_image_absolute[0]) == target_image_absolute[1]
            for point in target_points
        )

    mode = transported["witness_type"]
    if mode == "old-old-secant":
        assert len(source_points) == len(target_points) == 2
        carried = line_key(target_points[0], target_points[1])
        expected = (
            tuple(transported["carried_geometry"][0]),
            tuple(transported["carried_geometry"][1]),
        )
        assert carried == expected
    else:
        assert mode == "old-new-new-line"
        assert len(source_points) == len(target_points) == 1
        assert tuple(transported["carried_geometry"]) == target_points[0]

    return {
        "source_gap": source["gap"],
        "source_atom_id": source["atom_id"],
        "witness_type": mode,
        "stable_ids": stable_ids,
        "source_points": source_points,
        "target_points": tuple(target_points),
        "source_image_kind": source_image_kind,
        "source_image_absolute": source_image_absolute,
        "target_image_absolute": target_image_absolute,
    }


def centered_geometry(definition, level, start):
    if level == SOURCE_LEVEL:
        points = definition["source_points"]
        image_absolute = definition["source_image_absolute"]
    else:
        assert level == TARGET_LEVEL
        points = definition["target_points"]
        image_absolute = definition["target_image_absolute"]

    endpoint_profiles = []
    centered_vectors = []
    for stable_id, point in zip(definition["stable_ids"], points):
        vector = sub(point, start)
        centered_vectors.append(vector)
        endpoint_profiles.append({
            "stable_id": stable_id,
            **vector_profile(vector),
        })

    carried_lines = []
    if definition["witness_type"] == "old-old-secant":
        assert len(centered_vectors) == 2
        key = line_key(centered_vectors[0], centered_vectors[1])
        carried_lines.append({
            "endpoint_stable_ids": list(definition["stable_ids"]),
            **line_profile(key),
        })

    if definition["source_image_kind"] == "point":
        source_image = {
            "kind": "point",
            **vector_profile(sub(image_absolute, start)),
        }
    else:
        source_image = {
            "kind": "line",
            **line_profile(relative_line(image_absolute, start)),
        }

    literal_key = {
        "schema": "literal-centered-tagged-frontier-v1",
        "source_gap": definition["source_gap"],
        "witness_type": definition["witness_type"],
        "endpoints": endpoint_profiles,
        "carried_two_endpoint_secants": carried_lines,
        "transported_source_atom_image": source_image,
    }
    shell_key = {
        "schema": "diagnostic-shell-projection-v1-not-a-Post-quotient",
        "witness_type": definition["witness_type"],
        "endpoint_shells": [
            (
                item["archimedean_3_shell"],
                item["content_3_adic_valuation"],
            )
            for item in endpoint_profiles
        ],
        "line_moment_shells": [
            (
                item["moment_archimedean_3_shell"],
                item["moment_content_3_adic_valuation"],
            )
            for item in carried_lines
        ],
    }
    return {
        **literal_key,
        "literal_centered_geometry_sha256": stable_hash(literal_key),
        "diagnostic_shell_projection": shell_key,
        "diagnostic_shell_projection_sha256": stable_hash(shell_key),
        "_centered_vectors": centered_vectors,
    }


def exact_observation(
    record,
    domain_size,
    step,
    selected_word,
    corridor_start,
    parent_gap,
    parent_slot,
    parent_word,
):
    zero = zero_mask(domain_size)
    if record is None:
        closure = direct = same_mode = direct_image = zero
        atom_hash = stable_hash([])
        atom_count = 0
        partner_ids = []
        partner_profiles = []
        channels = []
        chosen_index = None
        effectful = False
    else:
        assert record["domain_size"] == domain_size
        assert record["l8_step"] == step
        assert record["chosen_word_avoids_endpoint_closure"] is True
        assert record["address"] == {
            "l7_parent_gap": parent_gap,
            "actual_connector_step_slot_zero_based": parent_slot,
            "actual_connector_word": list(parent_word),
        }
        closure = record["endpoint_closure"]
        direct = record["direct_transport"]
        assert direct["words"] <= closure["words"]
        if direct["words"] == closure["words"]:
            assert direct["mask_sha256"] == closure["mask_sha256"]
        same_mode = record["original_same_mode_transport"]
        direct_image = record["direct_image_transport"]
        atom_hash = stable_hash(record["atoms"])
        atom_count = len(record["atoms"])
        partners = {}
        for atom in record["atoms"]:
            for witness in atom["witnesses"]:
                partner = witness["partner"]
                if partner is None:
                    continue
                stable_id = partner["stable_id"]
                previous = partners.setdefault(stable_id, partner)
                assert previous == partner
        partner_ids = sorted(partners)
        partner_profiles = []
        for stable_id in partner_ids:
            partner = partners[stable_id]
            coordinate = tuple(partner["coordinate"])
            partner_profiles.append({
                "stable_id": stable_id,
                "centered_vector": as_json(sub(coordinate, corridor_start)),
                "coordinate": as_json(coordinate),
                "birth_level": partner["birth_level"],
                "age": partner["age"],
                "birth_gap": partner["birth_gap"],
                "interior_ordinal": partner["interior_ordinal"],
                "activation_action": partner["activation_action"],
                "activation_sweep_tile": partner["activation_sweep_tile"],
                "owner_options": partner["owner_options"],
            })
        channels = sorted({
            witness["channel"]
            for atom in record["atoms"]
            for witness in atom["witnesses"]
        })
        chosen_index = record["chosen_word_index"]
        effectful = True

    observation = {
        "schema": "exact-recorded-L8-tagged-endpoint-action-v1",
        "step": step,
        "domain_size": domain_size,
        "actual_selected_connector_word": list(selected_word),
        "deep_domain_word_index_if_effectful": chosen_index,
        "actual_selected_word_avoids_endpoint_closure": True,
        "endpoint_closure": closure,
        "direct_endpoint_or_carried_line_submask": direct,
        "original_same_mode_submask": same_mode,
        "direct_affine_image_submask": direct_image,
        "deep_atom_witness_stream_sha256": atom_hash,
        "deep_effect_atom_count": atom_count,
        "joined_partner_stable_ids": partner_ids,
        "joined_partner_profiles": partner_profiles,
        "witness_channels": channels,
        "deep_record_effectful": effectful,
        "join_residual_present": closure != direct,
        "direct_subset_of_closure_source": (
            "asserted by the pinned deep producer; this consumer also checks "
            "count monotonicity and equal-count mask equality"
        ),
    }
    behavior_key = {
        "schema": "killed-word-behavior-sig-0-v1",
        "step": step,
        "domain_size": domain_size,
        "actual_selected_connector_word": list(selected_word),
        "endpoint_closure": closure,
    }
    return observation, behavior_key


def partition_summary(records, key_function):
    classes = defaultdict(list)
    for record in records:
        classes[key_function(record)].append(record)
    sizes = Counter(len(items) for items in classes.values())
    return {
        "nodes": len(records),
        "classes": len(classes),
        "class_size_histogram": dict(sorted(sizes.items())),
        "largest_class": max(sizes, default=0),
        "singleton_classes": sizes[1],
    }


def quotient_test(records, name, key_function):
    classes = defaultdict(list)
    for record in records:
        classes[key_function(record)].append(record)
    bad = []
    for key, items in classes.items():
        outcomes = {
            stable_hash(item["observation"]["endpoint_closure"])
            for item in items
        }
        if len(outcomes) <= 1:
            continue
        sample = sorted(items, key=lambda item: item["l8_gap"])[:6]
        bad.append({
            "projection_key_sha256": stable_hash(key),
            "class_nodes": len(items),
            "distinct_full_killed_masks": len(outcomes),
            "witnesses": [
                {
                    "source_gap": item["source_gap"],
                    "l8_gap": item["l8_gap"],
                    "step": item["step"],
                    "actual_selected_connector_word": item[
                        "actual_selected_connector_word"
                    ],
                    "direct_mask": item["observation"][
                        "direct_endpoint_or_carried_line_submask"
                    ],
                    "full_mask": item["observation"]["endpoint_closure"],
                    "joined_partner_stable_ids": item["observation"][
                        "joined_partner_stable_ids"
                    ],
                }
                for item in sample
            ],
        })
    merged = [items for items in classes.values() if len(items) > 1]
    return {
        "name": name,
        "nodes": len(records),
        "classes": len(classes),
        "merged_classes": len(merged),
        "nodes_in_merged_classes": sum(map(len, merged)),
        "noncongruent_classes_for_full_killed_mask": len(bad),
        "largest_noncongruent_class": max(
            (item["class_nodes"] for item in bad), default=0
        ),
        "refuted_on_this_finite_trace": bool(bad),
        "counterexamples": bad[:4],
    }


def compact_child_for_behavior_trace(child):
    return {
        "slot": child["actual_parent_connector_step_slot_zero_based"],
        "actual_parent_connector_step": child["step"],
        "sig_0_sha256": child["sig_0_sha256"],
    }


def compact_child_literal_address(child):
    return {
        **compact_child_for_behavior_trace(child),
        "l8_gap": child["l8_gap"],
    }


def parent_trace_quotient_test(records, name, key_function):
    classes = defaultdict(list)
    for record in records:
        classes[key_function(record)].append(record)
    bad = []
    for key, items in classes.items():
        outcomes = {item["sig_1_sha256"] for item in items}
        if len(outcomes) <= 1:
            continue
        sample = sorted(
            items, key=lambda item: (item["source_gap"], item["l7_parent_gap"])
        )[:6]
        bad.append({
            "projection_key_sha256": stable_hash(key),
            "class_nodes": len(items),
            "distinct_sig_1_traces": len(outcomes),
            "witnesses": [
                {
                    "source_gap": item["source_gap"],
                    "l7_parent_gap": item["l7_parent_gap"],
                    "step": item["step"],
                    "actual_selected_connector_word": item[
                        "actual_selected_connector_word"
                    ],
                    "diagnostic_shell_projection": item["centered_geometry"][
                        "diagnostic_shell_projection"
                    ],
                    "sig_1_sha256": item["sig_1_sha256"],
                }
                for item in sample
            ],
        })
    merged = [items for items in classes.values() if len(items) > 1]
    return {
        "name": name,
        "nodes": len(records),
        "classes": len(classes),
        "merged_classes": len(merged),
        "nodes_in_merged_classes": sum(map(len, merged)),
        "noncongruent_classes_for_sig_1": len(bad),
        "largest_noncongruent_class": max(
            (item["class_nodes"] for item in bad), default=0
        ),
        "refuted_on_this_finite_trace": bool(bad),
        "counterexamples": bad[:4],
    }


def build_experiment(deep, state7, state8, viz):
    parents7 = viz["levels"][7]["parents"]
    points7 = [tuple(point) for point in viz["levels"][7]["points"]]
    starts = block_starts(parents7)
    assert len(points7) == len(state8["anchors"]) == len(parents7)
    assert len(state7["anchors"]) == len(state7["parent_word"]) + 1
    assert len(state8["anchors"]) == len(state8["parent_word"]) + 1

    closure = deep["all_domain_endpoint_incidence_closure"]
    domain_sizes = {
        row["step"]: row["domain_words"] for row in closure["model_census"]
    }
    assert len(domain_sizes) == 124
    raw_sources = {source["gap"]: source for source in deep["sources"]}
    raw_closures = {
        source["source_gap"]: source for source in closure["per_source"]
    }
    assert set(raw_sources) == set(raw_closures) == {13171, 21115}

    parent_records = []
    child_records = []
    edge_shell_deltas = []
    source_summaries = []
    for source_gap in sorted(raw_sources):
        definition = source_definition(raw_sources[source_gap], state7, state8)
        occurrences = raw_closures[source_gap]["occurrences"]
        occurrence_by_gap = {
            record["l8_gap"]: record
            for record in occurrences
        }
        assert len(occurrence_by_gap) == len(occurrences)
        effect_parent_gaps = sorted({
            parents7[gap] for gap in occurrence_by_gap
        })
        source_children = []

        for parent_gap in effect_parent_gaps:
            parent_word = tuple(state7["words"][parent_gap])
            parent_step = state7["parent_word"][parent_gap]
            block_start = starts[parent_gap]
            parent_start = tuple(state7["anchors"][parent_gap])
            parent_geometry = centered_geometry(
                definition, SOURCE_LEVEL, parent_start
            )
            parent_vectors = parent_geometry.pop("_centered_vectors")
            children = []

            for slot, connector_step in enumerate(parent_word):
                child_gap = block_start + slot
                assert parents7[child_gap] == parent_gap
                assert state8["parent_word"][child_gap] == connector_step
                child_start7 = points7[child_gap]
                child_start8 = tuple(state8["anchors"][child_gap])
                assert child_start8 == apply(M_BAL3, child_start7)
                prefix = sub(child_start7, parent_start)

                child_geometry = centered_geometry(
                    definition, TARGET_LEVEL, child_start8
                )
                child_vectors = child_geometry.pop("_centered_vectors")
                assert len(parent_vectors) == len(child_vectors)
                for endpoint_index, (
                    parent_vector, child_vector, point7
                ) in enumerate(zip(
                    parent_vectors, child_vectors, definition["source_points"]
                )):
                    assert child_vector == apply(
                        M_BAL3, sub(point7, child_start7)
                    )
                    assert child_vector == sub(
                        apply(M_BAL3, parent_vector), apply(M_BAL3, prefix)
                    )
                    edge_shell_deltas.append({
                        "source_gap": source_gap,
                        "l7_parent_gap": parent_gap,
                        "l8_child_gap": child_gap,
                        "endpoint_stable_id": definition["stable_ids"][
                            endpoint_index
                        ],
                        "parent_shell": archimedean_shell3(parent_vector),
                        "child_shell": archimedean_shell3(child_vector),
                        "shell_delta": (
                            None if archimedean_shell3(parent_vector) is None
                            or archimedean_shell3(child_vector) is None
                            else archimedean_shell3(child_vector)
                            - archimedean_shell3(parent_vector)
                        ),
                    })

                selected_word = tuple(state8["words"][child_gap])
                observation, behavior_key = exact_observation(
                    occurrence_by_gap.get(child_gap),
                    domain_sizes[connector_step],
                    connector_step,
                    selected_word,
                    child_start8,
                    parent_gap,
                    slot,
                    parent_word,
                )
                literal_state = {
                    "schema": "literal-realized-L8-far-frontier-state-v1",
                    "source_gap": source_gap,
                    "l8_gap": child_gap,
                    "l7_parent_gap": parent_gap,
                    "actual_parent_connector_step_slot_zero_based": slot,
                    "l7_parent_connector_prefix_vector": as_json(prefix),
                    "actual_corridor_start_coordinate": as_json(child_start8),
                    "step": connector_step,
                    "actual_selected_connector_word": list(selected_word),
                    "centered_geometry": child_geometry,
                    "observation": observation,
                }
                sig0 = stable_hash(behavior_key)
                literal_sig0 = stable_hash(literal_state)
                child = {
                    **literal_state,
                    "sig_0_schema": (
                        "step + actual selected connector word + exact full "
                        "tagged-endpoint killed-word mask"
                    ),
                    "sig_0_sha256": sig0,
                    "literal_sig_0_sha256": literal_sig0,
                }
                children.append(child)
                source_children.append(child)
                child_records.append(child)

            assert len(children) == len(parent_word)
            trace_payload = {
                "schema": "realized-ordered-future-trace-sig-1-v1",
                "l7_parent_step": parent_step,
                "actual_selected_l7_connector_word": list(parent_word),
                "ordered_children": [
                    compact_child_for_behavior_trace(child)
                    for child in children
                ],
            }
            literal_parent = {
                "schema": "literal-realized-L7-far-frontier-state-v1",
                "source_gap": source_gap,
                "l7_parent_gap": parent_gap,
                "actual_corridor_start_coordinate": as_json(parent_start),
                "step": parent_step,
                "actual_selected_connector_word": list(parent_word),
                "centered_geometry": parent_geometry,
                "ordered_l8_children": [
                    compact_child_literal_address(child) for child in children
                ],
            }
            parent_records.append({
                **literal_parent,
                "sig_1_schema": (
                    "exact ordered sig_0 list along the actual selected L7 "
                    "connector, retaining each actual L8 connector choice"
                ),
                "sig_1_sha256": stable_hash(trace_payload),
                "literal_sig_1_sha256": stable_hash({
                    "parent": literal_parent,
                    "child_literal_sig_0": [
                        child["literal_sig_0_sha256"] for child in children
                    ],
                }),
            })

        source_summaries.append({
            "source_gap": source_gap,
            "witness_type": definition["witness_type"],
            "tagged_endpoint_stable_ids": list(definition["stable_ids"]),
            "effectful_l8_observations": len(occurrence_by_gap),
            "effect_parent_l7_states": len(effect_parent_gaps),
            "actual_child_states_closed_under_those_parents": len(source_children),
            "direct_effectful_child_states": sum(
                child["observation"][
                    "direct_endpoint_or_carried_line_submask"
                ]["words"] > 0
                for child in source_children
            ),
            "full_effectful_child_states": sum(
                child["observation"]["endpoint_closure"]["words"] > 0
                for child in source_children
            ),
            "states_with_nonempty_join_residual": sum(
                child["observation"]["join_residual_present"]
                for child in source_children
            ),
        })

    child_records.sort(key=lambda item: (item["source_gap"], item["l8_gap"]))
    parent_records.sort(
        key=lambda item: (item["source_gap"], item["l7_parent_gap"])
    )

    direct_no_choice = quotient_test(
        child_records,
        "mode + step + direct-frontier mask; actual connector choice omitted",
        lambda item: stable_hash((
            item["centered_geometry"]["witness_type"],
            item["step"],
            item["observation"]["direct_endpoint_or_carried_line_submask"],
        )),
    )
    direct_with_choice = quotient_test(
        child_records,
        "mode + step + actual connector choice + direct-frontier mask",
        lambda item: stable_hash((
            item["centered_geometry"]["witness_type"],
            item["step"],
            item["actual_selected_connector_word"],
            item["observation"]["direct_endpoint_or_carried_line_submask"],
        )),
    )
    centered_with_choice = quotient_test(
        child_records,
        "exact centered stable-identity geometry + step + actual choice",
        lambda item: stable_hash((
            item["centered_geometry"][
                "literal_centered_geometry_sha256"
            ],
            item["step"],
            item["actual_selected_connector_word"],
        )),
    )
    shell_with_choice = quotient_test(
        child_records,
        "diagnostic centered 3-shells + mode + step + actual choice + direct mask",
        lambda item: stable_hash((
            item["centered_geometry"]["witness_type"],
            item["centered_geometry"][
                "diagnostic_shell_projection_sha256"
            ],
            item["step"],
            item["actual_selected_connector_word"],
            item["observation"]["direct_endpoint_or_carried_line_submask"],
        )),
    )
    parent_shell_trace = parent_trace_quotient_test(
        parent_records,
        "diagnostic centered 3-shells + mode + step + actual parent choice",
        lambda item: stable_hash((
            item["centered_geometry"]["witness_type"],
            item["centered_geometry"][
                "diagnostic_shell_projection_sha256"
            ],
            item["step"],
            item["actual_selected_connector_word"],
        )),
    )
    parent_exact_trace = parent_trace_quotient_test(
        parent_records,
        "exact centered stable-identity geometry + step + actual parent choice",
        lambda item: stable_hash((
            item["centered_geometry"][
                "literal_centered_geometry_sha256"
            ],
            item["step"],
            item["actual_selected_connector_word"],
        )),
    )

    shell_delta_histogram = Counter(
        record["shell_delta"] for record in edge_shell_deltas
    )
    partner_birth_levels = {}
    partner_static_profiles = {}
    partner_profile_occurrences = 0
    for child in child_records:
        for partner in child["observation"]["joined_partner_profiles"]:
            stable_id = partner["stable_id"]
            birth_level = partner["birth_level"]
            previous = partner_birth_levels.setdefault(stable_id, birth_level)
            assert previous == birth_level
            static_profile = {
                key: value for key, value in partner.items()
                if key != "centered_vector"
            }
            previous_profile = partner_static_profiles.setdefault(
                stable_id, static_profile
            )
            assert previous_profile == static_profile
            partner_profile_occurrences += 1
    partner_birth_histogram = Counter(partner_birth_levels.values())
    return {
        "status": (
            "exact finite realized-path sig_0/sig_1 experiment; not a "
            "universal Post quotient, far-tail rank, or availability proof"
        ),
        "scope": {
            "source_levels_present_in_pickles": [5, 6, 7, 8],
            "tagged_endpoint_birth_level": 7,
            "exact_effect_observation_level": 8,
            "alternate_connector_histories": False,
            "endpoint_or_distance_cutoff": None,
            "address_semantics": (
                "single realized ordered path; parent and child connector "
                "choices are retained and no independent stream product is "
                "formed"
            ),
        },
        "horizon_coverage": {
            "sig_0": {
                "available": True,
                "nodes": len(child_records),
                "semantics": "exact recorded L8 tagged-endpoint killed-word action",
            },
            "sig_1": {
                "available": True,
                "nodes": len(parent_records),
                "semantics": (
                    "ordered actual L7 connector block of exact sig_0 children"
                ),
            },
            "sig_2": {
                "available": False,
                "nodes": 0,
                "missing_data": [
                    "no gate2-l7-construction-L9.pkl with selected connector words",
                    "no L9 prefix activation order for connector-born partners",
                    "no exact L9 tagged-endpoint--other-point join closure",
                ],
            },
            "why_L5_L6_do_not_extend_the_past_horizon": (
                "all three stable endpoints are connector points born at L7"
            ),
        },
        "source_summaries": source_summaries,
        "missing_join_census": {
            "child_states_with_full_mask_strictly_larger_than_direct_frontier_mask": sum(
                child["observation"]["join_residual_present"]
                for child in child_records
            ),
            "joined_partner_profile_occurrences": partner_profile_occurrences,
            "unique_joined_partner_stable_ids": len(partner_birth_levels),
            "unique_partner_birth_level_histogram": {
                str(level): count
                for level, count in sorted(partner_birth_histogram.items())
            },
            "unique_current_L8_connector_partners": partner_birth_histogram[
                TARGET_LEVEL
            ],
            "interpretation": (
                "these are the concrete endpoint--other-point joins absent "
                "from the direct endpoint/carried-line state; current-L8 "
                "partners depend on the realized prefix and can depend on "
                "alternate connector choices, which were not computed here"
            ),
        },
        "partitions": {
            "L8_behavior_sig_0": partition_summary(
                child_records, lambda item: item["sig_0_sha256"]
            ),
            "L8_literal_sig_0": partition_summary(
                child_records, lambda item: item["literal_sig_0_sha256"]
            ),
            "L7_behavior_sig_1": partition_summary(
                parent_records, lambda item: item["sig_1_sha256"]
            ),
            "L7_literal_sig_1": partition_summary(
                parent_records, lambda item: item["literal_sig_1_sha256"]
            ),
        },
        "quotient_falsifiers": {
            "direct_frontier_without_choice": direct_no_choice,
            "direct_frontier_with_actual_choice": direct_with_choice,
            "diagnostic_shell_with_actual_choice": shell_with_choice,
            "exact_centered_geometry_with_actual_choice": centered_with_choice,
            "parent_shell_projection_to_sig_1": parent_shell_trace,
            "parent_exact_centered_projection_to_sig_1": parent_exact_trace,
            "interpretation": (
                "a refuted projection is unsound even on the one recorded "
                "orbit.  A projection not refuted here is only a finite "
                "non-falsification; singleton or nearly singleton classes "
                "supply no finite-state or transition-congruence theorem"
            ),
        },
        "diagnostic_shell_transfer": {
            "endpoint_edges": len(edge_shell_deltas),
            "archimedean_3_shell_delta_histogram": {
                str(key): value
                for key, value in sorted(
                    shell_delta_histogram.items(),
                    key=lambda item: (-999 if item[0] is None else item[0]),
                )
            },
            "edges": edge_shell_deltas,
            "proof_status": (
                "exact observations only; no common contraction, switched "
                "envelope, or rank decrease is inferred"
            ),
        },
        "parent_states": parent_records,
        "child_states": child_records,
        "referee_interpretation": {
            "proved_by_finite_computation": [
                "the concrete L7 parent addresses and all their realized L8 child slots are joined without an address cross-product",
                "sig_0 is the pinned exact killed-word action of the full tagged-endpoint closure on every retained L8 child",
                "sig_1 is the exact ordered one-generation trace through the actual selected connector words",
                "centered endpoint vectors and carried primitive lines obey the exact M_BAL3 transport identities on every retained edge",
            ],
            "finite_falsification": [
                "the reported two noncongruent classes prove that the tested "
                "(mode, step, actual connector choice, direct-frontier mask) "
                "projection does not determine full poisoning on this "
                "recorded trace"
            ],
            "not_proved": [
                "a finite exact centered-state quotient (the literal states may all be singletons)",
                "congruence under alternate legal connector choices",
                "a finite rule that generates the observed inherited and current-level partner joins from a bounded frontier",
                "any sig_2 stabilization or age-at-least-two recurrence",
                "a uniform far-secant contraction/ranking inequality",
                "positive connector availability or an unconditional infinite walk",
            ],
        },
    }


def estimate(deep, state7, viz):
    parents7 = viz["levels"][7]["parents"]
    starts = block_starts(parents7)
    closure = deep["all_domain_endpoint_incidence_closure"]
    sources = []
    total_parents = 0
    total_children = 0
    for item in sorted(closure["per_source"], key=lambda value: value["source_gap"]):
        parent_gaps = sorted({
            parents7[record["l8_gap"]] for record in item["occurrences"]
        })
        children = sum(len(state7["words"][gap]) for gap in parent_gaps)
        for gap in parent_gaps:
            begin = starts[gap]
            assert all(
                parents7[begin + slot] == gap
                for slot in range(len(state7["words"][gap]))
            )
        total_parents += len(parent_gaps)
        total_children += children
        sources.append({
            "source_gap": item["source_gap"],
            "effectful_L8_records": len(item["occurrences"]),
            "L7_effect_parent_states": len(parent_gaps),
            "actual_L8_children_in_closed_parent_blocks": children,
        })
    return {
        "status": "structural estimate; no geometry or signature construction",
        "sources": sources,
        "total_L7_parent_states": total_parents,
        "total_L8_child_states": total_children,
        "expected_horizons": [0, 1],
        "unavailable_horizon": 2,
    }


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
    parser.add_argument(
        "--deep-result", type=Path, default=DEFAULT_DEEP_RESULT
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/far-secant-future-trace.json"),
    )
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; certificate assertions must remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    resources = enforce_resource_policy()
    deep_path = args.deep_result.resolve()
    deep, input_hashes, deep_hash = validate_inputs(deep_path)
    viz = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    state7 = load_pickle("gate2-l7-construction-L7.pkl")

    if args.mode == "estimate":
        result = estimate(deep, state7, viz)
        result["resource_policy"] = resources
        result["deep_result_sha256"] = deep_hash
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    state8 = load_pickle("gate2-l7-construction-L8.pkl")
    result = build_experiment(deep, state7, state8, viz)
    result["resource_policy"] = resources
    result["input_sha256"] = input_hashes
    result["deep_result"] = {
        "path": str(deep_path),
        "sha256": deep_hash,
        "checker_sha256": deep["checker_sha256"],
    }
    result["checker_sha256"] = file_sha256(Path(__file__).resolve())
    size, digest = atomic_write_json(args.output, result)
    print(
        f"wrote {args.output.resolve()} ({size} bytes, sha256 {digest})",
        flush=True,
    )


if __name__ == "__main__":
    main()
