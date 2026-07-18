#!/usr/bin/env python3
"""Exact finite probe of the observed x-axis Bellman core.

The pinned x-axis artifact contains 11,154 strict-effect line nodes and
24,066 latent zero-effect descendants.  The pinned observed/coarse Bellman
barrier classifies 11,107 strict and 2,096 latent nodes as core.  This checker
collapses those occurrences by the exact geometric key

    (parent step, relative lateral coordinate z=(y,z)).

It preserves the complete combined killed-word mask, separately audits the
strict-secant/collision role decomposition, and builds action/slot-labelled
carried-line transitions.  Congruence is tested only after retaining the
actual selected connector word, ordered child slot, exact prefix control, and
child step.

The resulting object is an exact finite probe on one realized L5--L8 trace,
not a universal promotion automaton.  In particular, the source artifact
contains carried endpoint-pair lineage edges but not the singleton lateral
occupancy needed to generate every newly born x-line.  It also contains only
recorded connector choices, not all words in the effective domains.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_core_promotion_probe.py run \
        --output /tmp/x-axis-core-promotion-probe-canonical.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_X_ARTIFACT = Path(
    "/tmp/x-axis-far-secant-resonance-canonical.json"
)
DEFAULT_BARRIER_ARTIFACT = Path(
    "/tmp/x-axis-bellman-barrier-canonical.json"
)
EXPECTED_X_ARTIFACT_SHA256 = (
    "0ebbfd97194fce4453269ad1c01eb1281e9d3a5aa526f1f036e409b82ad36cc1"
)
EXPECTED_BARRIER_ARTIFACT_SHA256 = (
    "f0a30cd341548539b9e0e3ecaa7cad57727e052f873f91649c0102c00c4262a9"
)
EXPECTED_X_CHECKER_SHA256 = (
    "7a0ea121ad91fa578026225a0c892eabf564c7250d9f3acb1a6ba7bbd162dd4c"
)
EXPECTED_BARRIER_CHECKER_SHA256 = (
    "c9cd69eb345c4bfab9355570fffe5b05a809b9e64ad05d243e0aaaac39fa5582"
)
EXPECTED_CHECKER_SHA256 = {
    "design/x_axis_far_secant_resonance.py": EXPECTED_X_CHECKER_SHA256,
    "design/x_axis_bellman_barrier.py": EXPECTED_BARRIER_CHECKER_SHA256,
}
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
B_LATERAL = ((0, -3), (3, -1))


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def as_json(value):
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
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


def rational(record):
    return Fraction(record["numerator"], record["denominator"])


def rational_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def lateral_norm_squared(vector):
    y, z = vector
    return Fraction(36 * y * y - 12 * y * z + 36 * z * z, 35)


def lateral_transport(vector, control):
    displaced = vector[0] - control[0], vector[1] - control[1]
    return (
        B_LATERAL[0][0] * displaced[0]
        + B_LATERAL[0][1] * displaced[1],
        B_LATERAL[1][0] * displaced[0]
        + B_LATERAL[1][1] * displaced[1],
    )


def enforce_resource_policy():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
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


def validate_inputs(x_path, barrier_path):
    commitments = {
        "x_axis_canonical_artifact": file_sha256(x_path),
        "x_axis_bellman_barrier_canonical_artifact": file_sha256(barrier_path),
    }
    expected = {
        "x_axis_canonical_artifact": EXPECTED_X_ARTIFACT_SHA256,
        "x_axis_bellman_barrier_canonical_artifact": (
            EXPECTED_BARRIER_ARTIFACT_SHA256
        ),
    }
    for name, digest in commitments.items():
        if digest != expected[name]:
            raise RuntimeError(
                f"pinned artifact hash drift for {name}: "
                f"{digest} != {expected[name]}"
            )
    for relative, expected_digest in EXPECTED_CHECKER_SHA256.items():
        digest = file_sha256(ROOT / relative)
        if digest != expected_digest:
            raise RuntimeError(
                f"pinned checker hash drift for {relative}: "
                f"{digest} != {expected_digest}"
            )
        commitments[relative] = digest
    return commitments


def load_artifacts(x_path, barrier_path):
    with barrier_path.open() as handle:
        barrier = json.load(handle)
    if barrier["checker_sha256"] != EXPECTED_BARRIER_CHECKER_SHA256:
        raise AssertionError("barrier checker commitment drift")
    if barrier["input_sha256"]["x_axis_canonical_artifact"] != (
        EXPECTED_X_ARTIFACT_SHA256
    ):
        raise AssertionError("barrier does not pin the expected x-axis artifact")
    step_records = barrier["threshold_barrier_comparison"]["steps"]
    step_by_id = {record["step"]: record for record in step_records}
    if len(step_by_id) != 124 or set(step_by_id) != set(range(124)):
        raise AssertionError("barrier step set drift")

    with x_path.open() as handle:
        x_axis = json.load(handle)
    if x_axis["checker_sha256"] != EXPECTED_X_CHECKER_SHA256:
        raise AssertionError("x-axis checker commitment drift")
    strict = x_axis["exact_prefix_effects"]["records"]
    graph = x_axis["closed_actual_selected_lineage_graph"]
    latent = graph["latent_node_records"]
    transitions = graph["records"]
    returns = x_axis["short_actual_control_returns"]
    if stable_hash(strict) != x_axis["exact_prefix_effects"][
        "occurrence_stream_sha256"
    ]:
        raise AssertionError("strict occurrence stream commitment mismatch")
    if stable_hash(latent) != graph["latent_node_stream_sha256"]:
        raise AssertionError("latent node stream commitment mismatch")
    if stable_hash(transitions) != graph["transition_stream_sha256"]:
        raise AssertionError("transition stream commitment mismatch")
    if stable_hash(returns["exact_effect_key_return_records"]) != returns[
        "exact_effect_key_return_stream_sha256"
    ]:
        raise AssertionError("effect-return stream commitment mismatch")
    if len(strict) != 11_154 or len(latent) != 24_066:
        raise AssertionError("node population drift")
    if len(transitions) != 27_103:
        raise AssertionError("transition population drift")
    return barrier, x_axis, step_by_id


def mask_key(mask):
    return mask["killed_words"], mask["mask_sha256"]


def mask_record(key, occurrences):
    return {
        "killed_words": key[0],
        "mask_sha256": key[1],
        "occurrences": occurrences,
    }


def classify_all_nodes(x_axis, step_by_id):
    strict = x_axis["exact_prefix_effects"]["records"]
    latent = x_axis["closed_actual_selected_lineage_graph"][
        "latent_node_records"
    ]
    node_by_id = {}
    node_info = {}
    populations = Counter()
    core_groups = defaultdict(list)

    for population, records in (("strict", strict), ("latent", latent)):
        for node in records:
            node_id = node["occurrence_id"]
            if node_id in node_by_id:
                raise AssertionError("duplicate node id")
            step = node["parent_step"]
            z = tuple(node["relative_lateral_yz"])
            h_squared = lateral_norm_squared(z)
            d = step_by_id[step]["D_s_interval"]
            d_lower, d_upper = rational(d["lower"]), rational(d["upper"])
            if h_squared <= d_lower * d_lower:
                shell = "core"
            elif h_squared > d_upper * d_upper:
                shell = "exterior"
            else:
                shell = "unresolved_interval_overlap"
            if population == "strict":
                if node["latent_zero_effect"] or mask_key(
                    node["strict_x_secant_word_mask"]
                )[0] <= 0:
                    raise AssertionError("strict population role drift")
            else:
                if not node["latent_zero_effect"] or mask_key(
                    node["combined_x_line_site_word_mask"]
                )[0] != 0:
                    raise AssertionError("latent population role drift")
            info = {
                "node": node,
                "population": population,
                "shell": shell,
                "state_key": (step, z),
                "state_id": stable_hash((step, z)),
                "h_squared": h_squared,
            }
            node_by_id[node_id] = node
            node_info[node_id] = info
            populations[(population, shell)] += 1
            if shell == "core":
                core_groups[(step, z)].append(info)

    if populations[("strict", "core")] != 11_107:
        raise AssertionError("strict core census drift")
    if populations[("latent", "core")] != 2_096:
        raise AssertionError("latent core census drift")
    if populations[("strict", "unresolved_interval_overlap")] or populations[
        ("latent", "unresolved_interval_overlap")
    ]:
        raise AssertionError("node overlaps a barrier interval")
    return node_by_id, node_info, core_groups, populations


def build_core_states(core_groups, step_by_id):
    states = []
    state_by_key = {}
    diagnostics = Counter()

    for state_key in sorted(core_groups):
        step, z = state_key
        items = core_groups[state_key]
        populations = Counter(item["population"] for item in items)
        if len(populations) != 1:
            raise AssertionError("one geometric state is both strict and latent")
        combined = Counter(mask_key(
            item["node"]["combined_x_line_site_word_mask"]
        ) for item in items)
        strict = Counter(mask_key(
            item["node"]["strict_x_secant_word_mask"]
        ) for item in items)
        collision = Counter(mask_key(
            item["node"]["endpoint_collision_word_mask"]
        ) for item in items)
        if len(combined) != 1:
            raise AssertionError(
                "combined killed-word mask is not geometric-state congruent",
                state_key,
            )
        endpoint_pairs = {
            tuple(item["node"]["line_endpoint_stable_ids"])
            for item in items
        }
        selected_words = {
            tuple(item["node"]["actual_selected_word"])
            for item in items
        }
        if len(strict) > 1:
            diagnostics["states_with_multiple_strict_role_masks"] += 1
        if len(collision) > 1:
            diagnostics["states_with_multiple_collision_role_masks"] += 1
        if len(endpoint_pairs) > 1:
            diagnostics["states_with_multiple_endpoint_pairs"] += 1
        if len(selected_words) > 1:
            diagnostics["states_with_multiple_observed_selected_words"] += 1
        if populations["strict"]:
            diagnostics["strict_states"] += 1
        else:
            diagnostics["latent_states"] += 1
        combined_key, combined_occurrences = next(iter(combined.items()))
        record = {
            "state_id": stable_hash(state_key),
            "step": step,
            "relative_lateral_yz": as_json(z),
            "h_squared_exact": rational_record(items[0]["h_squared"]),
            "observed_terminal_step": step_by_id[step][
                "observed_terminal_assigned_zero"
            ],
            "population": next(iter(populations)),
            "occurrences": len(items),
            "combined_killed_word_mask": mask_record(
                combined_key, combined_occurrences
            ),
            "strict_role_mask_variants": [
                mask_record(key, count) for key, count in sorted(strict.items())
            ],
            "collision_role_mask_variants": [
                mask_record(key, count)
                for key, count in sorted(collision.items())
            ],
            "unique_endpoint_pairs": len(endpoint_pairs),
            "endpoint_pair_stream_sha256": stable_hash(sorted(endpoint_pairs)),
            "unique_observed_selected_words": len(selected_words),
            "selected_word_stream_sha256": stable_hash(sorted(selected_words)),
            "levels": sorted({item["node"]["level"] for item in items}),
            "stitch_orders": sorted({
                item["node"]["stitch_order"] for item in items
            }),
        }
        states.append(record)
        state_by_key[state_key] = record

    if len(states) != 1_312:
        raise AssertionError("observed core geometric-state census drift")
    if diagnostics["strict_states"] != 748 or diagnostics[
        "latent_states"
    ] != 564:
        raise AssertionError("strict/latent geometric-state census drift")
    if diagnostics["states_with_multiple_strict_role_masks"] != 92:
        raise AssertionError("strict role diagnostic drift")
    if diagnostics["states_with_multiple_collision_role_masks"] != 92:
        raise AssertionError("collision role diagnostic drift")
    return states, state_by_key, diagnostics


def transition_outcome(transition, target_info, state_by_key):
    target_key = target_info["state_key"]
    if target_info["shell"] == "core":
        target_state = state_by_key.get(target_key)
        if target_state is None:
            raise AssertionError("core transition target absent from state set")
        return {
            "shell": "core",
            "state_id": target_state["state_id"],
            "step": target_key[0],
            "relative_lateral_yz": as_json(target_key[1]),
            "combined_killed_word_mask": target_state[
                "combined_killed_word_mask"
            ],
        }
    if target_info["shell"] != "exterior":
        raise AssertionError("transition target has unresolved shell")
    node = target_info["node"]
    return {
        "shell": "exterior",
        "step": target_key[0],
        "relative_lateral_yz": as_json(target_key[1]),
        "combined_killed_word_mask": {
            **node["combined_x_line_site_word_mask"],
            "occurrences": 1,
        },
    }


def build_action_transitions(
    x_axis, node_info, state_by_key, core_groups
):
    transitions = x_axis["closed_actual_selected_lineage_graph"]["records"]
    incoming_ids = set()
    source_transitions = defaultdict(list)
    edge_groups = defaultdict(list)
    endpoint_pair_changes = 0
    core_source_occurrences = set()
    core_transition_class_counts = Counter()

    for transition in transitions:
        source_id = transition["source_lineage_node_id"]
        target_id = transition["target_lineage_node_id"]
        source_info = node_info[source_id]
        target_info = node_info[target_id]
        incoming_ids.add(target_id)
        source_transitions[source_id].append(transition)
        source_node = source_info["node"]
        target_node = target_info["node"]
        if tuple(source_node["line_endpoint_stable_ids"]) != tuple(
            target_node["line_endpoint_stable_ids"]
        ):
            endpoint_pair_changes += 1
        source_z = tuple(source_node["relative_lateral_yz"])
        target_z = tuple(target_node["relative_lateral_yz"])
        control = tuple(transition["selected_prefix_control_c_perp"])
        if lateral_transport(source_z, control) != target_z:
            raise AssertionError("exact lateral recurrence failed")
        if source_info["shell"] != "core":
            continue
        core_source_occurrences.add(source_id)
        word = tuple(transition["actual_selected_word"])
        slot = transition["actual_child_slot_zero_based"]
        prefix3 = tuple(transition["selected_prefix_control_c"])
        if control != (prefix3[1], prefix3[2]):
            raise AssertionError("perpendicular prefix mismatch")
        if transition["child_step"] != word[slot]:
            raise AssertionError("child step does not equal selected word slot")
        label = (
            word, slot, prefix3, control, transition["child_step"]
        )
        outcome = transition_outcome(transition, target_info, state_by_key)
        source_state = state_by_key[source_info["state_key"]]
        edge_groups[(source_state["state_id"], label)].append({
            "outcome": outcome,
            "source_occurrence": source_id,
            "transition_id": transition["transition_id"],
            "stitch_order": transition["stitch_order"],
            "source_level": source_node["level"],
        })
        core_transition_class_counts[
            "core->" + target_info["shell"]
        ] += 1

    if endpoint_pair_changes:
        raise AssertionError("carried-line edge changed endpoint pair identity")

    edge_records = []
    noncongruent = []
    for (source_state_id, label), items in sorted(edge_groups.items()):
        outcomes = {}
        for item in items:
            outcomes[stable_hash(item["outcome"])] = item["outcome"]
        if len(outcomes) != 1:
            noncongruent.append({
                "source_state_id": source_state_id,
                "label": as_json(label),
                "distinct_outcomes": len(outcomes),
            })
        outcome = next(iter(outcomes.values()))
        word, slot, prefix3, control, child_step = label
        edge_records.append({
            "source_state_id": source_state_id,
            "action_word": as_json(word),
            "child_slot_zero_based": slot,
            "prefix_control": as_json(prefix3),
            "prefix_control_perp": as_json(control),
            "child_step": child_step,
            "outcome": outcome,
            "observed_occurrences": len(items),
            "stitch_orders": sorted({item["stitch_order"] for item in items}),
            "source_levels": sorted({item["source_level"] for item in items}),
            "transition_id_stream_sha256": stable_hash(sorted(
                item["transition_id"] for item in items
            )),
        })
    if noncongruent:
        raise AssertionError("action-labelled transition noncongruence", noncongruent)

    # Test the complete ordered child tuple for each observed source/action.
    bundle_groups = defaultdict(list)
    horizon_core_nodes = 0
    for state_key, infos in core_groups.items():
        source_state = state_by_key[state_key]
        for info in infos:
            node = info["node"]
            source_id = node["occurrence_id"]
            outgoing = source_transitions.get(source_id, ())
            if not outgoing:
                if node["level"] != 8:
                    raise AssertionError("non-L8 core node lacks descendants")
                horizon_core_nodes += 1
                continue
            word = tuple(node["actual_selected_word"])
            by_slot = {edge["actual_child_slot_zero_based"]: edge for edge in outgoing}
            if set(by_slot) != set(range(len(word))):
                raise AssertionError("source action does not retain every child slot")
            ordered = []
            for slot in range(len(word)):
                edge = by_slot[slot]
                target_info = node_info[edge["target_lineage_node_id"]]
                ordered.append({
                    "slot": slot,
                    "prefix_control": edge["selected_prefix_control_c"],
                    "child_step": edge["child_step"],
                    "outcome": transition_outcome(
                        edge, target_info, state_by_key
                    ),
                })
            bundle_groups[(source_state["state_id"], word)].append({
                "source": source_id,
                "ordered_post": ordered,
            })

    bundle_bad = []
    bundle_records = []
    for (state_id, word), items in sorted(bundle_groups.items()):
        posts = {}
        for item in items:
            posts[stable_hash(item["ordered_post"])] = item["ordered_post"]
        if len(posts) != 1:
            bundle_bad.append({
                "state_id": state_id,
                "word": as_json(word),
                "distinct_ordered_posts": len(posts),
            })
        bundle_records.append({
            "state_id": state_id,
            "action_word": as_json(word),
            "ordered_post_sha256": next(iter(posts)),
            "source_occurrences": len(items),
        })
    if bundle_bad:
        raise AssertionError("whole-action transition noncongruence", bundle_bad)

    all_core_ids = {
        info["node"]["occurrence_id"]
        for infos in core_groups.values() for info in infos
    }
    no_incoming = all_core_ids - incoming_ids
    no_incoming_counts = Counter(
        node_info[node_id]["population"] for node_id in no_incoming
    )
    return {
        "edge_records": edge_records,
        "summary": {
            "core_source_transition_occurrences": sum(
                core_transition_class_counts.values()
            ),
            "core_transition_class_counts": dict(sorted(
                core_transition_class_counts.items()
            )),
            "unique_action_slot_labelled_edges": len(edge_records),
            "repeated_action_slot_edge_classes": sum(
                record["observed_occurrences"] > 1 for record in edge_records
            ),
            "action_slot_noncongruent_classes": len(noncongruent),
            "unique_whole_action_bundles": len(bundle_records),
            "whole_action_noncongruent_classes": len(bundle_bad),
            "whole_action_bundle_stream_sha256": stable_hash(bundle_records),
            "core_source_occurrences_with_descendants": len(
                core_source_occurrences
            ),
            "L8_horizon_core_occurrences_without_descendants": (
                horizon_core_nodes
            ),
            "core_occurrences_without_a_retained_incoming_lineage_edge": len(
                no_incoming
            ),
            "no_incoming_counts_by_population": dict(sorted(
                no_incoming_counts.items()
            )),
            "carried_edges_changing_endpoint_pair_identity": (
                endpoint_pair_changes
            ),
            "edge_stream_sha256": stable_hash(edge_records),
        },
    }


def map_returns(x_axis, node_info, state_by_key):
    returns = x_axis["short_actual_control_returns"][
        "exact_effect_key_return_records"
    ]
    records = []
    effect_states = set()
    action_states = set()
    for item in returns:
        source = node_info[item["source"]]
        target = node_info[item["target"]]
        if source["shell"] != "core" or target["shell"] != "core":
            raise AssertionError("return endpoint is outside observed core")
        source_state = state_by_key[source["state_key"]]
        target_state = state_by_key[target["state_key"]]
        if source_state["state_id"] != target_state["state_id"]:
            raise AssertionError("effect-key return changed geometric state")
        effect_states.add(source_state["state_id"])
        if item["selected_action_return"]:
            action_states.add(source_state["state_id"])
        records.append({
            "period": item["period"],
            "stitch_order": item["stitch_order"],
            "source_occurrence": item["source"],
            "target_occurrence": item["target"],
            "state_id": source_state["state_id"],
            "step": source_state["step"],
            "relative_lateral_yz": source_state["relative_lateral_yz"],
            "selected_action_return": item["selected_action_return"],
            "transition_ids": item["transition_ids"],
        })
    records.sort(key=lambda record: (
        record["period"], record["source_occurrence"],
        record["target_occurrence"],
    ))
    if len(records) != 36 or len(effect_states) != 15:
        raise AssertionError("effect-return state census drift")
    if sum(record["selected_action_return"] for record in records) != 6:
        raise AssertionError("selected-action return census drift")
    if len(action_states) != 3:
        raise AssertionError("selected-action return state census drift")
    return {
        "effect_key_return_occurrences": len(records),
        "unique_geometric_effect_return_states": len(effect_states),
        "effect_and_selected_action_return_occurrences": sum(
            record["selected_action_return"] for record in records
        ),
        "unique_geometric_action_return_states": len(action_states),
        "return_mapping_stream_sha256": stable_hash(records),
        "records": records,
    }


def build_result(x_path, barrier_path):
    resource = enforce_resource_policy()
    inputs = validate_inputs(x_path, barrier_path)
    barrier, x_axis, step_by_id = load_artifacts(x_path, barrier_path)
    node_by_id, node_info, core_groups, populations = classify_all_nodes(
        x_axis, step_by_id
    )
    states, state_by_key, state_diagnostics = build_core_states(
        core_groups, step_by_id
    )
    transitions = build_action_transitions(
        x_axis, node_info, state_by_key, core_groups
    )
    returns = map_returns(x_axis, node_info, state_by_key)

    if set(node_by_id) != {
        *(
            node["occurrence_id"]
            for node in x_axis["exact_prefix_effects"]["records"]
        ),
        *(
            node["occurrence_id"]
            for node in x_axis["closed_actual_selected_lineage_graph"][
                "latent_node_records"
            ]
        ),
    }:
        raise AssertionError("node lookup coverage drift")

    domain_total = barrier["effective_domain_stream"][
        "effective_domain_words"
    ]
    unique_observed_words = {
        (info["state_key"][0], tuple(info["node"]["actual_selected_word"]))
        for infos in core_groups.values() for info in infos
    }
    return {
        "status": (
            "exact finite action-labelled collapse of the pinned observed "
            "x-axis Bellman core; not a universal promotion automaton, birth "
            "closure, availability bound, or unconditional theorem"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": resource,
        "scope": {
            "levels": [5, 6, 7, 8],
            "stitch_orders": ["gate", "pipeline"],
            "core_definition": (
                "exact h_squared <= pinned observed/coarse D_lower_squared"
            ),
            "state_key": "(parent step, exact relative lateral integer pair)",
            "effect": (
                "complete combined x-line site killed-word mask; strict and "
                "endpoint-collision submasks are retained as diagnostics"
            ),
            "transition_label": (
                "actual connector word, ordered child slot, exact 3D and "
                "lateral prefix control, and child step"
            ),
            "alternate_connector_histories": False,
        },
        "occurrence_census": {
            "strict_core": populations[("strict", "core")],
            "strict_exterior": populations[("strict", "exterior")],
            "latent_core": populations[("latent", "core")],
            "latent_exterior": populations[("latent", "exterior")],
            "unresolved_interval_overlap": (
                populations[("strict", "unresolved_interval_overlap")]
                + populations[("latent", "unresolved_interval_overlap")]
            ),
        },
        "core_state_census": {
            "geometric_states": len(states),
            **dict(sorted(state_diagnostics.items())),
            "combined_mask_noncongruent_states": 0,
            "state_stream_sha256": stable_hash(states),
        },
        "observed_action_coverage": {
            "unique_step_and_selected_word_pairs_on_core_occurrences": len(
                unique_observed_words
            ),
            "full_effective_domain_words_across_steps": domain_total,
            "interpretation": (
                "the recorded selected actions are a tiny policy-specific "
                "sample; the full-domain word count is not a denominator for "
                "a statistical estimate"
            ),
        },
        "core_states": states,
        "action_labelled_transition_census": transitions["summary"],
        "action_slot_edges": transitions["edge_records"],
        "return_source_mapping": returns,
        "minimal_missing_birth_state": {
            "required": [
                "for each relevant lateral class, singleton endpoint occupancy as well as active two-endpoint line presence",
                "a truncated occupancy value 0/1/2 on legal histories; inserting a distinct point into occupancy 1 creates the x-line state",
                "exact axial endpoint/collision information, or a separately proved exact collision frontier, before treating an occupancy-1 insertion as distinct",
                "the actual ordered connector interiors for the selected word, so occupancy and new-line births are updated without an independent-address product",
                "a sound representation of which promoted line and endpoint states coexist in one realized path; unioning all finite geometric types can be availability-vacuous",
            ],
            "artifact_limit": (
                "every retained lineage edge preserves one existing endpoint "
                "pair; the artifact has no singleton-occupancy table and no "
                "edge that certifies the birth of a new x-line"
            ),
            "diagnostic_evidence": {
                "states_with_multiple_endpoint_pairs": state_diagnostics[
                    "states_with_multiple_endpoint_pairs"
                ],
                "states_with_multiple_observed_selected_words": (
                    state_diagnostics[
                        "states_with_multiple_observed_selected_words"
                    ]
                ),
                "strict_role_noncongruent_but_combined_mask_congruent_states": (
                    state_diagnostics[
                        "states_with_multiple_strict_role_masks"
                    ]
                ),
                "carried_edges_changing_endpoint_pair_identity": transitions[
                    "summary"
                ]["carried_edges_changing_endpoint_pair_identity"],
                "core_occurrences_without_a_retained_incoming_lineage_edge": (
                    transitions["summary"][
                        "core_occurrences_without_a_retained_incoming_lineage_edge"
                    ]
                ),
            },
        },
        "next_universal_test": {
            "smallest_sound_extension": (
                "scan all effective-domain words once to deduplicate every "
                "(source step, action word, slot, prefix control, child step); "
                "recompute a full-domain rather than observed Bellman barrier; "
                "enumerate its finite integer x-core; then add the exact "
                "singleton-occupancy/insertion transition before testing a BDD "
                "or antichain safety state"
            ),
            "why_the_core_is_finite_once_the_full_barrier_is_certified": (
                "the lateral quadratic form has minimum Euclidean eigenvalue "
                "6/7, so h(z)<=D bounds the integer pair z in a finite disk"
            ),
        },
        "proof_boundary": {
            "proved_by_this_finite_probe": [
                "the 13203 observed core occurrences collapse to 1312 exact geometric states",
                "the complete combined killed-word mask is congruent on every geometric state",
                "every retained carried-line transition is congruent after the actual action and ordered slot are retained",
                "all 36 effect-key returns map to 15 geometric states and all six selected-action returns map to three geometric states",
            ],
            "refuted_coarse_claims": [
                "the strict-versus-collision role decomposition is not determined by (step,z) in 92 observed states",
                "the geometric state does not determine a policy action; many states use multiple recorded selected words",
            ],
            "not_proved": [
                "transition congruence for unobserved connector words, L9, or later levels",
                "singleton endpoint occupancy, new-line birth closure, or chronological recentering between unrelated pending corridors",
                "an availability-grade coexistence state, greatest fixed point, or unconditional theorem",
            ],
        },
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
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument(
        "--x-artifact", type=Path, default=DEFAULT_X_ARTIFACT
    )
    run_parser.add_argument(
        "--barrier-artifact", type=Path, default=DEFAULT_BARRIER_ARTIFACT
    )
    run_parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/x-axis-core-promotion-probe-canonical.json"),
    )
    args = parser.parse_args()
    started = time.time()
    payload = build_result(args.x_artifact, args.barrier_artifact)
    atomic_write_json(args.output, payload)
    print(json.dumps({
        "checker_sha256": payload["checker_sha256"],
        "elapsed_seconds": round(time.time() - started, 3),
        "output": str(args.output.resolve()),
        "output_sha256": file_sha256(args.output.resolve()),
        "status": payload["status"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
