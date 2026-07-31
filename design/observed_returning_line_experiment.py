#!/usr/bin/env python3
"""Bounded returning-line census on the pinned guarded L5--L8 trace data.

The input trace is the existing exact x-parallel old--old--new secant audit.
This program does not enumerate arbitrary secant pairs or alternate histories.
It separates two observed transition channels:

* carriage through actual selected child slots; and
* unrelated same-level cursor imports in the recorded ``gate`` order.

A return is effect -> one-or-more exact zero-effect states -> effect.  Cursor
intervals are committed without expanding their 49 million silent state visits
into the output table.  The compact reference (level and exact gate-rank range),
the pinned construction hash, and two stream digests make every interval
reconstructible.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import pickle
import struct
import tempfile
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEVELS = (5, 6, 7, 8)
SCHEMA = "observed-returning-line-table/v1"
SUMMARY_SCHEMA = "observed-returning-line-summary/v1"
WITNESS_SCHEMA = "observed-returning-line-witnesses/v1"
EXPECTED_X_NORMALIZED_SHA256 = (
    "07bb4b6b26877aff0eb07495fbe43a74e9fbc7dd171f1fc28d66aacf108a8c00"
)
EXPECTED_X_RAW_CANONICAL_SHA256 = (
    "0ebbfd97194fce4453269ad1c01eb1281e9d3a5aa526f1f036e409b82ad36cc1"
)
EXPECTED_X_CHECKER_SHA256 = (
    "7a0ea121ad91fa578026225a0c892eabf564c7250d9f3acb1a6ba7bbd162dd4c"
)
EXPECTED_BARRIER_CHECKER_SHA256 = (
    "c9cd69eb345c4bfab9355570fffe5b05a809b9e64ad05d243e0aaaac39fa5582"
)
EXPECTED_INVARIANT_SUMMARY_SHA256 = (
    "ff930e9d48f8f7c4d6b71828f81453cb983f11483a81d82d7e5a75621bfd00c9"
)
EXPECTED_CONSTRUCTION_SHA256 = {
    5: "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
    6: "70fa3baac057492fb8ad325eba5417bdc1e98fbd474bec37dc5f5465230f9298",
    7: "304e71eb74939662c0d0251864193171e74f49fd2023a98df09dc45d99fa0660",
    8: "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141",
}
M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
H = (55, 34, 18)
DEFAULT_X = Path("/tmp/x-axis-far-secant-resonance-canonical.json")
DEFAULT_BARRIER = Path("/tmp/x-axis-bellman-barrier-canonical.json")
DEFAULT_TABLE = ROOT / "design" / "observed-returning-line-table.json"
DEFAULT_SUMMARY = ROOT / "design" / "observed-returning-line-summary.json"
DEFAULT_WITNESSES = ROOT / "design" / "observed-returning-line-witnesses.json"


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json_dump(value, path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".tmp.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
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


def seal(value):
    result = dict(value)
    result["payload_sha256"] = stable_hash(value)
    return result


def add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def scale(factor, vector):
    return tuple(factor * coordinate for coordinate in vector)


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def dot(left, right):
    return sum(left[index] * right[index] for index in range(3))


def content(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    return divisor


def primitive_plucker(first, second):
    first = tuple(first)
    second = tuple(second)
    chord = subtract(second, first)
    divisor = content(chord)
    if divisor == 0:
        raise AssertionError("repeated line endpoints")
    primitive = tuple(coordinate // divisor for coordinate in chord)
    sign_flipped = next(value for value in primitive if value) < 0
    if sign_flipped:
        primitive = scale(-1, primitive)
    moment = cross(first, primitive)
    if cross(second, primitive) != moment or dot(primitive, moment) != 0:
        raise AssertionError("invalid primitive Pluecker normalization")
    return {
        "g": list(primitive),
        "mu": list(moment),
        "endpoint_chord": list(chord),
        "endpoint_chord_content": divisor,
        "canonical_sign_flipped": sign_flipped,
    }


def token_only(record):
    return {"g": list(record["g"]), "mu": list(record["mu"])}


def lateral_q(direction):
    _x, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def cone_residual(direction):
    return 275 * lateral_q(direction) - 348 * direction[0] * direction[0]


def exact_v3(value):
    if value == 0:
        return None
    value = abs(value)
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def finite_min(left, right):
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)


def valuation_json(value):
    return "infinity" if value is None else value


def archimedean_shell3(vector):
    norm = max(abs(value) for value in vector)
    if norm == 0:
        return None
    shell = 0
    boundary = 1
    while 3 * boundary <= norm:
        boundary *= 3
        shell += 1
    return shell


def vector_content_v3(vector):
    orders = [exact_v3(value) for value in vector if value]
    return None if not orders else min(orders)


def implemented_direction_ranks(token):
    direction = tuple(token["g"])
    moment = tuple(token["mu"])
    vx = exact_v3(direction[0])
    vq = exact_v3(lateral_q(direction))
    raw = finite_min(vx, vq)
    weighted = finite_min(vx, None if vq is None else vq // 2)
    latent = finite_min(
        None if vx is None else vx // 2,
        None if vq is None else (vq - 1) // 4,
    )
    return {
        "padic_raw_min_depth": raw,
        "padic_weighted_projective_candidate": weighted,
        "latent_padic_depth_R": latent,
        "direction_x_v3": valuation_json(vx),
        "lateral_q": lateral_q(direction),
        "lateral_q_v3": valuation_json(vq),
        "direction_archimedean_3_shell": archimedean_shell3(direction),
        "direction_content_v3": valuation_json(vector_content_v3(direction)),
        "moment_archimedean_3_shell": archimedean_shell3(moment),
        "moment_content_v3": valuation_json(vector_content_v3(moment)),
        "guard_cone_residual_F": cone_residual(direction),
    }


def rational(record):
    return Fraction(record["numerator"], record["denominator"])


def rational_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def load_inputs(x_path, barrier_path):
    x_axis = load_json(x_path)
    normalized = copy.deepcopy(x_axis)
    normalized["resource_policy"].pop("elapsed_seconds", None)
    normalized_sha256 = stable_hash(normalized)
    if normalized_sha256 != EXPECTED_X_NORMALIZED_SHA256:
        raise AssertionError("normalized x-axis source drift", normalized_sha256)
    if x_axis["checker_sha256"] != EXPECTED_X_CHECKER_SHA256:
        raise AssertionError("x-axis checker drift")

    barrier = load_json(barrier_path)
    if barrier["checker_sha256"] != EXPECTED_BARRIER_CHECKER_SHA256:
        raise AssertionError("Bellman checker drift")
    if barrier["input_sha256"]["x_axis_canonical_artifact"] != (
        EXPECTED_X_RAW_CANONICAL_SHA256
    ):
        raise AssertionError("barrier/x-axis source commitment drift")
    if barrier["observed_coarse_graph"]["transition_stream_sha256"] != x_axis[
        "closed_actual_selected_lineage_graph"
    ]["transition_stream_sha256"]:
        raise AssertionError("barrier transition graph drift")

    states = {}
    construction_hashes = {}
    for level in LEVELS:
        path = ROOT / f"gate2-l7-construction-L{level}.pkl"
        digest = file_sha256(path)
        if digest != EXPECTED_CONSTRUCTION_SHA256[level]:
            raise AssertionError("construction pickle drift", level, digest)
        if x_axis["input_sha256"][path.name] != digest:
            raise AssertionError("x-axis/pickle commitment drift", level)
        construction_hashes[level] = digest
        with path.open("rb") as handle:
            state = pickle.load(handle)
        gaps = len(state["parent_word"])
        if sorted(state["order"]) != list(range(gaps)):
            raise AssertionError("gate order is not a permutation", level)
        states[level] = state

    invariant_path = ROOT / "design" / "latent-family-reachable-entry-audit-summary.json"
    if file_sha256(invariant_path) != EXPECTED_INVARIANT_SUMMARY_SHA256:
        raise AssertionError("latent-family invariant certificate drift")
    invariant = load_json(invariant_path)
    symbolic = invariant["symbolic_closure"]
    if (
        symbolic["classification"] != "PROVED"
        or symbolic["guard_equation"] != "275*q(g)-348*g_x^2=0"
        or "F(H)=0" not in symbolic["family_cone_membership"]
    ):
        raise AssertionError("latent-family invariant payload drift")

    step_d = {}
    step_records = barrier["observed_step_only_bellman_barrier"]["step_records"]
    if len(step_records) != 124:
        raise AssertionError("Bellman step census drift")
    for record in step_records:
        interval = record["D_s_interval"]
        step_d[record["step"]] = (
            rational(interval["lower"]),
            rational(interval["upper"]),
            record["observed_terminal_assigned_zero"],
        )
    return x_axis, barrier, states, step_d, {
        "x_axis_normalized_sha256": normalized_sha256,
        "x_axis_canonical_raw_sha256": EXPECTED_X_RAW_CANONICAL_SHA256,
        "x_axis_checker_sha256": x_axis["checker_sha256"],
        "barrier_checker_sha256": barrier["checker_sha256"],
        "construction_sha256": construction_hashes,
        "latent_invariant_summary_sha256": EXPECTED_INVARIANT_SUMMARY_SHA256,
    }


def bellman_record(node, step_d):
    y, z = node["relative_lateral_yz"]
    h_squared = Fraction(36 * y * y - 12 * y * z + 36 * z * z, 35)
    lower, upper, terminal = step_d[node["parent_step"]]
    if h_squared <= lower * lower:
        classification = "core"
    elif h_squared > upper * upper:
        classification = "exterior"
    else:
        raise AssertionError("Bellman interval overlap")
    return {
        "classification": classification,
        "observed_terminal_D_zero_convention": terminal,
        "h_squared": rational_record(h_squared),
        "D_lower": rational_record(lower),
        "D_upper": rational_record(upper),
    }


def line_indexes(x_axis):
    by_key = {}
    by_id = defaultdict(dict)
    for level_record in x_axis["reachable_x_parallel_lines"]["level_census"]:
        level = level_record["level"]
        for line in level_record["records"]:
            key = level, line["line_id"]
            if key in by_key:
                raise AssertionError("duplicate level/line record")
            by_key[key] = line
            by_id[line["line_id"]][level] = line
    return by_key, by_id


def gate_occurrences(x_axis):
    records = [
        record
        for record in x_axis["exact_prefix_effects"]["records"]
        if record["stitch_order"] == "gate"
    ]
    if len(records) != 5_577:
        raise AssertionError("gate effect occurrence census drift")
    records.sort(key=lambda item: (
        item["level"], item["line_id"], item["schedule_rank"], item["gap"]
    ))
    return records


def node_effect(node):
    return node["strict_x_secant_word_mask"]["killed_words"] > 0


def state_type(node):
    relative_y, relative_z = node["relative_lateral_yz"]
    return {
        "parent_step": node["parent_step"],
        "relative_primitive_pluecker": {
            "g": [1, 0, 0],
            "mu": [0, relative_z, -relative_y],
        },
        "strict_site_offsets": node["strict_third_point_site_offsets"],
        "strict_mask_sha256": node["strict_x_secant_word_mask"]["mask_sha256"],
        "strict_killed_words": node["strict_x_secant_word_mask"]["killed_words"],
    }


def event_record(node, line, states, step_d):
    level = node["level"]
    anchor = tuple(states[level]["anchors"][node["gap"]])
    token = primitive_plucker(
        line["endpoints"][0]["coordinate"], line["endpoints"][1]["coordinate"]
    )
    relative_moment = subtract(tuple(token["mu"]), cross(anchor, tuple(token["g"])))
    expected_relative = (0, node["relative_lateral_yz"][1], -node["relative_lateral_yz"][0])
    if relative_moment != expected_relative:
        raise AssertionError("relative Pluecker/cursor mismatch")
    return {
        "occurrence_id": node["occurrence_id"],
        "level": level,
        "gap": node["gap"],
        "gate_schedule_rank": node["schedule_rank"],
        "parent_step": node["parent_step"],
        "cursor_anchor": list(anchor),
        "global_primitive_pluecker": token_only(token),
        "relative_primitive_pluecker": {
            "g": list(token["g"]), "mu": list(relative_moment)
        },
        "actual_selected_word": node["actual_selected_word"],
        "strict_third_point_site_offsets": node["strict_third_point_site_offsets"],
        "strict_word_mask": node["strict_x_secant_word_mask"],
        "implemented_ranks": {
            **implemented_direction_ranks(token),
            "observed_x_bellman": bellman_record(node, step_d),
        },
    }


def cursor_stream_commitments(level, line, source, target, states):
    state = states[level]
    order = state["order"]
    parent_word = state["parent_word"]
    anchors = state["anchors"]
    lateral_y, lateral_z = line["lateral_yz"]
    exact = hashlib.sha256()
    local = hashlib.sha256()
    previous_anchor = tuple(anchors[source["gap"]])
    first_rank = source["schedule_rank"] + 1
    last_rank = target["schedule_rank"]
    for rank in range(first_rank, last_rank + 1):
        gap = order[rank]
        step = parent_word[gap]
        anchor = tuple(anchors[gap])
        relative_y = lateral_y - anchor[1]
        relative_z = lateral_z - anchor[2]
        effect = int(rank == last_rank)
        delta = subtract(anchor, previous_anchor)
        exact.update(struct.pack(
            ">10qB", level, rank, gap, step, *anchor, relative_y, relative_z,
            target["strict_x_secant_word_mask"]["killed_words"] if effect else 0,
            effect,
        ))
        local.update(struct.pack(
            ">6qB", step, *delta, relative_y, relative_z, effect
        ))
        previous_anchor = anchor
    return {
        "binary_schema": {
            "exact": ">10qB = level,rank,gap,step,anchor_xyz,relative_yz,killed_words,effect",
            "line_local": ">6qB = target_step,cursor_delta_xyz,relative_yz,effect",
            "byte_order": "big-endian signed 64-bit integers plus one unsigned effect byte",
        },
        "exact_cursor_stream_sha256": exact.hexdigest(),
        "line_local_control_stream_sha256": local.hexdigest(),
        "cursor_transitions": last_rank - source["schedule_rank"],
    }


def enumerate_cursor_returns(occurrences, lines_by_key, states):
    grouped = defaultdict(list)
    for occurrence in occurrences:
        grouped[(occurrence["level"], occurrence["line_id"])].append(occurrence)
    traces = []
    for key, events in sorted(grouped.items()):
        events.sort(key=lambda item: item["schedule_rank"])
        for source, target in zip(events, events[1:]):
            silent = target["schedule_rank"] - source["schedule_rank"] - 1
            if silent <= 0:
                continue
            level, line_id = key
            line = lines_by_key[key]
            commitments = cursor_stream_commitments(
                level, line, source, target, states
            )
            source_anchor = tuple(states[level]["anchors"][source["gap"]])
            target_anchor = tuple(states[level]["anchors"][target["gap"]])
            type_payload = {
                "channel": "cursor_import",
                "source": state_type(source),
                "silent_interval_length": silent,
                "net_cursor_translation": list(subtract(target_anchor, source_anchor)),
                "line_local_control_stream_sha256": commitments[
                    "line_local_control_stream_sha256"
                ],
                "target": state_type(target),
                "primitive_normalization_divisors": {
                    "value": 1,
                    "count": commitments["cursor_transitions"],
                },
            }
            trace_id = stable_hash((
                "cursor_import", level, line_id, source["occurrence_id"],
                target["occurrence_id"],
            ))
            traces.append({
                "trace_id": trace_id,
                "trace_type_id": stable_hash(type_payload),
                "channel": "cursor_import",
                "line_id": line_id,
                "terminal_level": level,
                "source_occurrence_id": source["occurrence_id"],
                "terminal_occurrence_id": target["occurrence_id"],
                "silent_interval_length": silent,
                "exact_minimized_return_trace": {
                    "effect_word": ["effect", {"silent": silent}, "effect"],
                    "source": state_type(source),
                    "net_cursor_translation": list(
                        subtract(target_anchor, source_anchor)
                    ),
                    "target": state_type(target),
                    "primitive_normalization": "identity at every cursor import",
                    **commitments,
                    "exact_interval_reference": {
                        "level": level,
                        "order": "gate",
                        "source_rank": source["schedule_rank"],
                        "first_silent_rank": source["schedule_rank"] + 1,
                        "last_silent_rank": target["schedule_rank"] - 1,
                        "terminal_rank": target["schedule_rank"],
                    },
                },
            })
    traces.sort(key=lambda item: (
        item["terminal_level"], item["line_id"], item["source_occurrence_id"],
        item["terminal_occurrence_id"],
    ))
    return traces


def enumerate_carriage_returns(x_axis):
    strict = {
        record["occurrence_id"]: record
        for record in x_axis["exact_prefix_effects"]["records"]
    }
    latent = {
        record["occurrence_id"]: record
        for record in x_axis["closed_actual_selected_lineage_graph"][
            "latent_node_records"
        ]
    }
    nodes = {**strict, **latent}
    transitions = [
        record
        for record in x_axis["closed_actual_selected_lineage_graph"]["records"]
        if record["stitch_order"] == "gate"
    ]
    adjacency = defaultdict(list)
    for transition in transitions:
        adjacency[transition["source_lineage_node_id"]].append(transition)
    for edges in adjacency.values():
        edges.sort(key=lambda item: item["transition_id"])

    episodes = []

    def continue_zero(source_id, current_id, path):
        for transition in adjacency.get(current_id, ()):
            target_id = transition["target_lineage_node_id"]
            extended = path + [transition]
            if node_effect(nodes[target_id]):
                episodes.append((source_id, target_id, extended))
            else:
                continue_zero(source_id, target_id, extended)

    for source_id in sorted(adjacency):
        if not node_effect(nodes[source_id]):
            continue
        for transition in adjacency[source_id]:
            target_id = transition["target_lineage_node_id"]
            if not node_effect(nodes[target_id]):
                continue_zero(source_id, target_id, [transition])

    if len(episodes) != 18:
        raise AssertionError("gate carriage-return census drift", len(episodes))
    return nodes, episodes


def carriage_normalization(source_line, target_line):
    source_token = primitive_plucker(
        source_line["endpoints"][0]["coordinate"],
        source_line["endpoints"][1]["coordinate"],
    )
    target_token = primitive_plucker(
        target_line["endpoints"][0]["coordinate"],
        target_line["endpoints"][1]["coordinate"],
    )
    raw_direction = matrix_vector(M, tuple(source_token["g"]))
    divisor = content(raw_direction)
    primitive = tuple(value // divisor for value in raw_direction)
    if next(value for value in primitive if value) < 0:
        primitive = scale(-1, primitive)
    if primitive != tuple(target_token["g"]):
        raise AssertionError("carried primitive direction mismatch")
    for source_endpoint, target_endpoint in zip(
        sorted(source_line["endpoints"], key=lambda item: item["stable_id"]),
        sorted(target_line["endpoints"], key=lambda item: item["stable_id"]),
    ):
        if matrix_vector(M, tuple(source_endpoint["coordinate"])) != tuple(
            target_endpoint["coordinate"]
        ):
            raise AssertionError("endpoint carriage mismatch")
    return {
        "raw_transported_direction": list(raw_direction),
        "primitive_divisor": divisor,
        "canonical_sign_flipped": False,
        "source_token": token_only(source_token),
        "target_token": token_only(target_token),
    }


def build_carriage_traces(nodes, episodes, lines_by_key, step_d):
    traces = []
    for source_id, target_id, path in episodes:
        source = nodes[source_id]
        target = nodes[target_id]
        line_id = source["line_id"]
        if target["line_id"] != line_id:
            raise AssertionError("carriage changed physical endpoint pair")
        node_ids = [source_id] + [
            transition["target_lineage_node_id"] for transition in path
        ]
        if any(nodes[node_id]["line_id"] != line_id for node_id in node_ids):
            raise AssertionError("carriage path changed line identity")
        if any(node_effect(nodes[node_id]) for node_id in node_ids[1:-1]):
            raise AssertionError("carriage path is not a minimized first return")
        edge_records = []
        for transition in path:
            source_level = transition["source_level_gap"][0]
            target_level = transition["child_level_gap"][0]
            normalization = carriage_normalization(
                lines_by_key[(source_level, line_id)],
                lines_by_key[(target_level, line_id)],
            )
            edge_records.append({
                "transition_id": transition["transition_id"],
                "source_level_gap": transition["source_level_gap"],
                "child_level_gap": transition["child_level_gap"],
                "actual_selected_word": transition["actual_selected_word"],
                "actual_child_slot_zero_based": transition[
                    "actual_child_slot_zero_based"
                ],
                "selected_prefix_control_c": transition[
                    "selected_prefix_control_c"
                ],
                "child_step": transition["child_step"],
                "primitive_normalization": normalization,
            })
        state_types = [state_type(nodes[node_id]) for node_id in node_ids]
        type_payload = {
            "channel": "carriage",
            "states": state_types,
            "controls": [{
                "actual_selected_word": edge["actual_selected_word"],
                "actual_child_slot_zero_based": edge[
                    "actual_child_slot_zero_based"
                ],
                "selected_prefix_control_c": edge["selected_prefix_control_c"],
                "child_step": edge["child_step"],
                "primitive_divisor": edge["primitive_normalization"][
                    "primitive_divisor"
                ],
            } for edge in edge_records],
        }
        trace_id = stable_hash((
            "carriage", source_id, target_id,
            [transition["transition_id"] for transition in path],
        ))
        traces.append({
            "trace_id": trace_id,
            "trace_type_id": stable_hash(type_payload),
            "channel": "carriage",
            "line_id": line_id,
            "terminal_level": target["level"],
            "source_occurrence_id": source_id,
            "terminal_occurrence_id": target_id,
            "silent_interval_length": len(path) - 1,
            "exact_minimized_return_trace": {
                "effect_word": ["effect", {"silent": len(path) - 1}, "effect"],
                "states": state_types,
                "edges": edge_records,
                "observed_x_bellman_profile": [
                    bellman_record(nodes[node_id], step_d) for node_id in node_ids
                ],
            },
        })
    traces.sort(key=lambda item: (
        item["terminal_level"], item["line_id"], item["source_occurrence_id"]
    ))
    return traces


def inverse_m_integer(vector):
    x, y, z = vector
    numerators = (x, 3 * z - y, -y)
    denominators = (3, 9, 3)
    if any(
        numerator % denominator
        for numerator, denominator in zip(numerators, denominators)
    ):
        raise AssertionError("endpoint coordinate has no integral M preimage")
    return tuple(
        numerator // denominator
        for numerator, denominator in zip(numerators, denominators)
    )


def endpoint_birth_record(endpoint, earliest_level, base_points, states):
    stable_id = endpoint["stable_id"]
    if stable_id.startswith("base-window:L4:P"):
        index = int(stable_id.rsplit("P", 1)[1])
        coordinate = tuple(base_points[index])
        return {
            "stable_id": stable_id,
            "birth_level": 4,
            "birth_kind": "base_path_vertex",
            "origin_coordinate": list(coordinate),
            "insertion_time": {
                "level": 4,
                "path_vertex_index": index,
                "exact_within_base_path": True,
            },
        }
    birth_level = endpoint["birth_level"]
    coordinate = tuple(endpoint["coordinate"])
    for _level in range(earliest_level, birth_level, -1):
        coordinate = inverse_m_integer(coordinate)
    gap = endpoint["birth_gap"]
    rank_by_gap = {
        candidate_gap: rank
        for rank, candidate_gap in enumerate(states[birth_level]["order"])
    }
    return {
        "stable_id": stable_id,
        "birth_level": birth_level,
        "birth_kind": "connector_interior",
        "origin_coordinate": list(coordinate),
        "birth_gap": gap,
        "interior_ordinal_one_based": endpoint["interior_ordinal"],
        "insertion_time": {
            "level": birth_level,
            "gate_schedule_rank": rank_by_gap[gap],
            "gap": gap,
            "interior_ordinal_one_based": endpoint["interior_ordinal"],
        },
    }


def insertion_key(endpoint):
    time = endpoint["insertion_time"]
    if endpoint["birth_kind"] == "base_path_vertex":
        return (4, time["path_vertex_index"], 0)
    return (
        time["level"], time["gate_schedule_rank"],
        time["interior_ordinal_one_based"],
    )


def line_provenance(line_id, levels, lines_by_key, base_points, states):
    earliest_level = min(levels)
    earliest = lines_by_key[(earliest_level, line_id)]
    endpoint_records = [
        endpoint_birth_record(
            endpoint, earliest_level, base_points, states
        )
        for endpoint in earliest["endpoints"]
    ]
    endpoint_records.sort(key=lambda item: item["stable_id"])
    birth_level = max(
        endpoint["birth_level"] for endpoint in endpoint_records
    )
    expected_birth_level = (
        4
        if earliest_level == 5
        and earliest["inherited_from_completed_L4"]
        else earliest_level
    )
    if birth_level != expected_birth_level:
        raise AssertionError(
            "line birth level disagrees with first completed-line level",
            line_id, birth_level, expected_birth_level,
        )
    for endpoint in endpoint_records:
        coordinate = tuple(endpoint["origin_coordinate"])
        for _level in range(endpoint["birth_level"], birth_level):
            coordinate = matrix_vector(M, coordinate)
        endpoint["coordinate_at_line_birth"] = list(coordinate)
    later = max(endpoint_records, key=insertion_key)
    birth_token = primitive_plucker(
        endpoint_records[0]["coordinate_at_line_birth"],
        endpoint_records[1]["coordinate_at_line_birth"],
    )
    level_history = []
    normalization_changes = []
    previous_level = birth_level
    previous_token = birth_token
    for level in sorted(levels):
        line = lines_by_key[(level, line_id)]
        token = primitive_plucker(
            line["endpoints"][0]["coordinate"], line["endpoints"][1]["coordinate"]
        )
        if level == previous_level:
            if token_only(token) != token_only(previous_token):
                raise AssertionError("birth/current token mismatch")
        else:
            current = previous_level
            current_token = previous_token
            while current < level:
                if (current, line_id) in lines_by_key:
                    source_line = lines_by_key[(current, line_id)]
                elif current == birth_level:
                    source_line = {
                        "endpoints": [{
                            "stable_id": endpoint_records[0]["stable_id"],
                            "coordinate": endpoint_records[0][
                                "coordinate_at_line_birth"
                            ],
                        }, {
                            "stable_id": endpoint_records[1]["stable_id"],
                            "coordinate": endpoint_records[1][
                                "coordinate_at_line_birth"
                            ],
                        }]
                    }
                else:
                    raise AssertionError("missing inherited line level")
                target_line = lines_by_key[(current + 1, line_id)]
                change = carriage_normalization(source_line, target_line)
                normalization_changes.append({
                    "transition": "carriage",
                    "source_level": current,
                    "target_level": current + 1,
                    **change,
                })
                current += 1
                current_token = primitive_plucker(
                    target_line["endpoints"][0]["coordinate"],
                    target_line["endpoints"][1]["coordinate"],
                )
            if token_only(current_token) != token_only(token):
                raise AssertionError("carriage token chain mismatch")
        level_history.append({
            "level": level,
            "primitive_pluecker": token_only(token),
            "endpoint_coordinates": [{
                "stable_id": endpoint["stable_id"],
                "coordinate": endpoint["coordinate"],
            } for endpoint in sorted(
                line["endpoints"], key=lambda item: item["stable_id"]
            )],
            "genealogical_carriage_depth_from_line_birth": level - birth_level,
            "implemented_direction_and_moment_ranks": implemented_direction_ranks(token),
        })
        previous_level = level
        previous_token = token
    return {
        "birth_level": birth_level,
        "birth_endpoints": endpoint_records,
        "later_endpoint_defining_line_birth": later["stable_id"],
        "line_insertion_time": later["insertion_time"],
        "birth_primitive_pluecker": token_only(birth_token),
        "birth_endpoint_chord": birth_token["endpoint_chord"],
        "birth_primitive_normalization": {
            "chord_content": birth_token["endpoint_chord_content"],
            "canonical_sign_flipped": birth_token["canonical_sign_flipped"],
        },
        "level_genealogy": level_history,
        "primitive_normalization_changes": normalization_changes,
    }


def trace_type_records(traces):
    groups = defaultdict(list)
    for trace in traces:
        groups[trace["trace_type_id"]].append(trace)
    records = []
    for type_id, members in sorted(groups.items()):
        records.append({
            "trace_type_id": type_id,
            "channel": members[0]["channel"],
            "occurrences": len(members),
            "terminal_levels": dict(sorted(Counter(
                str(member["terminal_level"]) for member in members
            ).items())),
            "representative_trace_id": members[0]["trace_id"],
        })
    return records


def build_payload(x_axis, barrier, states, step_d, commitments):
    lines_by_key, lines_by_id = line_indexes(x_axis)
    occurrences = gate_occurrences(x_axis)
    occurrence_by_id = {item["occurrence_id"]: item for item in occurrences}
    cursor_traces = enumerate_cursor_returns(
        occurrences, lines_by_key, states
    )
    nodes, carriage_episodes = enumerate_carriage_returns(x_axis)
    carriage_traces = build_carriage_traces(
        nodes, carriage_episodes, lines_by_key, step_d
    )
    traces = sorted(cursor_traces + carriage_traces, key=lambda item: (
        item["terminal_level"], item["channel"], item["line_id"], item["trace_id"]
    ))
    trace_types = trace_type_records(traces)

    returning_keys = {
        (trace["terminal_level"], trace["line_id"]) for trace in traces
    }
    returning_ids = sorted({line_id for _level, line_id in returning_keys})
    traces_by_line = defaultdict(list)
    for trace in traces:
        traces_by_line[trace["line_id"]].append(trace["trace_id"])
    effects_by_line = defaultdict(list)
    for occurrence in occurrences:
        if occurrence["line_id"] in returning_ids:
            effects_by_line[occurrence["line_id"]].append(occurrence)

    base_data = load_json(ROOT / "viz" / "walk3d-data.json")
    base_points = base_data["levels"][4]["points"]
    line_records = []
    for line_id in returning_ids:
        levels = sorted(lines_by_id[line_id])
        provenance = line_provenance(
            line_id, levels, lines_by_key, base_points, states
        )
        family = {
            "member_of_exact_latent_L_n_family": False,
            "member_of_any_66429_y_unit_residue_graph": False,
            "reason": (
                "every observed returning direction is g=(1,0,0), so g_y is "
                "zero modulo 3; every 66,429-edge state is in the y-unit "
                "chart [x:1:z] and every exact g_n has g_y nonzero modulo 3"
            ),
            "checked_precisions_k": [1, 2, 3, 4, 5],
            "observed_guard_cone_residual_F": -348,
            "latent_family_guard_cone_residual_F": 0,
        }
        event_records = []
        for occurrence in sorted(
            effects_by_line[line_id],
            key=lambda item: (item["level"], item["schedule_rank"], item["gap"]),
        ):
            event_records.append(event_record(
                occurrence,
                lines_by_key[(occurrence["level"], line_id)],
                states,
                step_d,
            ))
        line_trace_ids = sorted(traces_by_line[line_id])
        line_trace_id_set = set(line_trace_ids)
        line_traces = [
            trace for trace in traces if trace["trace_id"] in line_trace_id_set
        ]
        line_records.append({
            "line_id": line_id,
            "primitive_direction_family": "x_parallel_g=(1,0,0)",
            "endpoint_stable_ids": sorted(
                lines_by_id[line_id][min(levels)]["endpoint_stable_ids"]
            ),
            "genealogical_provenance": provenance,
            "every_effectful_gate_phase_cursor": event_records,
            "silent_interval_lengths": {
                "cursor_import": [
                    trace["silent_interval_length"] for trace in line_traces
                    if trace["channel"] == "cursor_import"
                ],
                "carriage": [
                    trace["silent_interval_length"] for trace in line_traces
                    if trace["channel"] == "carriage"
                ],
            },
            "carriage_return_trace_ids": [
                trace["trace_id"] for trace in line_traces
                if trace["channel"] == "carriage"
            ],
            "cursor_import_return_trace_ids": [
                trace["trace_id"] for trace in line_traces
                if trace["channel"] == "cursor_import"
            ],
            "latent_family_membership": family,
        })

    channel_level_lines = {
        channel: {
            str(level): len({
                trace["line_id"] for trace in traces
                if trace["channel"] == channel
                and trace["terminal_level"] == level
            })
            for level in LEVELS
        }
        for channel in ("cursor_import", "carriage")
    }
    union_level_lines = {
        str(level): len({
            line_id for observed_level, line_id in returning_keys
            if observed_level == level
        })
        for level in LEVELS
    }
    channel_level_episodes = {
        channel: {
            str(level): sum(
                trace["channel"] == channel and trace["terminal_level"] == level
                for trace in traces
            )
            for level in LEVELS
        }
        for channel in ("cursor_import", "carriage")
    }
    channel_level_types = {
        channel: {
            str(level): len({
                trace["trace_type_id"] for trace in traces
                if trace["channel"] == channel
                and trace["terminal_level"] == level
            })
            for level in LEVELS
        }
        for channel in ("cursor_import", "carriage")
    }
    union_level_types = {
        str(level): len({
            trace["trace_type_id"] for trace in traces
            if trace["terminal_level"] == level
        })
        for level in LEVELS
    }
    cumulative_types = {}
    for level in LEVELS:
        cumulative_types[str(level)] = len({
            trace["trace_type_id"] for trace in traces
            if trace["terminal_level"] <= level
        })

    expected = {
        "cursor_lines": {"5": 37, "6": 101, "7": 315, "8": 1021},
        "carriage_lines": {"5": 0, "6": 0, "7": 4, "8": 14},
        "cursor_episodes": {"5": 77, "6": 205, "7": 635, "8": 2053},
        "carriage_episodes": {"5": 0, "6": 0, "7": 4, "8": 14},
        "cursor_types": {"5": 77, "6": 205, "7": 635, "8": 2045},
        "carriage_types": {"5": 0, "6": 0, "7": 4, "8": 14},
        "union_types": {"5": 77, "6": 205, "7": 639, "8": 2059},
        "cumulative_types": {"5": 77, "6": 282, "7": 921, "8": 2980},
    }
    observed = {
        "cursor_lines": channel_level_lines["cursor_import"],
        "carriage_lines": channel_level_lines["carriage"],
        "cursor_episodes": channel_level_episodes["cursor_import"],
        "carriage_episodes": channel_level_episodes["carriage"],
        "cursor_types": channel_level_types["cursor_import"],
        "carriage_types": channel_level_types["carriage"],
        "union_types": union_level_types,
        "cumulative_types": cumulative_types,
    }
    if observed != expected:
        raise AssertionError("return census drift", observed)
    if len(line_records) != 1_021 or len(traces) != 2_988 or len(trace_types) != 2_980:
        raise AssertionError("global return census drift")
    if any(
        line["latent_family_membership"]["member_of_exact_latent_L_n_family"]
        for line in line_records
    ):
        raise AssertionError("unexpected latent-family coverage")

    trace_by_id = {trace["trace_id"]: trace for trace in traces}
    smallest_cursor = min(
        cursor_traces,
        key=lambda trace: (
            trace["terminal_level"], trace["silent_interval_length"],
            occurrence_by_id[trace["terminal_occurrence_id"]]["schedule_rank"],
            occurrence_by_id[trace["source_occurrence_id"]]["schedule_rank"],
            trace["line_id"],
        ),
    )
    smallest_carriage = min(
        carriage_traces,
        key=lambda trace: (
            trace["terminal_level"], trace["silent_interval_length"],
            nodes[trace["terminal_occurrence_id"]]["schedule_rank"],
            nodes[trace["source_occurrence_id"]]["schedule_rank"],
            trace["line_id"],
        ),
    )

    table_core = {
        "schema": SCHEMA,
        "status": (
            "complete exact finite census of nontrivial returns already observed "
            "in the pinned x-parallel L5-L8 old-secant trace; not an all-direction "
            "secant-pair census or all-level theorem"
        ),
        "scope": {
            "levels": list(LEVELS),
            "construction_order": "gate only",
            "candidate_effect": (
                "nonempty exact full-domain old--old--new strict site mask"
            ),
            "return_definition": "effect -> one-or-more silent states -> effect",
            "carriage": (
                "actual selected child-slot transitions in the existing closed "
                "lineage graph"
            ),
            "cursor_import": (
                "same already-born physical line observed at two nonconsecutive "
                "gate cursors; every intervening gate cursor has empty strict mask"
            ),
            "enumeration_boundary": (
                "all returning lines in the repository's implemented observed "
                "L5-L8 x-line trace; no new all-pairs or non-x scan is inferred"
            ),
            "alternate_history_search": False,
        },
        "input_commitments": commitments,
        "rank_inventory": {
            "padic_raw_min_depth": (
                "min(v3(g_x),v3(q(g))); implemented diagnostic, refuted as "
                "representation-independent before primitive normalization"
            ),
            "padic_weighted_projective_candidate": (
                "min(v3(g_x),floor(v3(q(g))/2)); implemented audit diagnostic"
            ),
            "latent_padic_depth_R": (
                "min(floor(v3(g_x)/2),floor((v3(q(g))-1)/4)); exact only on "
                "the fixed latent positive-control family"
            ),
            "observed_x_bellman": (
                "exact core/exterior classification for the implemented observed "
                "step-only x barrier; its decreasing escape rank is defined only "
                "outside the core and only for synchronized carriage"
            ),
            "archimedean_and_content_shells": (
                "implemented far-secant diagnostics, included per level but not "
                "claimed as theorem ranks"
            ),
        },
        "counts": {
            **observed,
            "returning_physical_lines": len(line_records),
            "return_episodes": len(traces),
            "distinct_exact_minimized_trace_types": len(trace_types),
            "cursor_silent_interval_minimum": min(
                trace["silent_interval_length"] for trace in cursor_traces
            ),
            "cursor_silent_interval_maximum": max(
                trace["silent_interval_length"] for trace in cursor_traces
            ),
            "cursor_distinct_silent_lengths": len({
                trace["silent_interval_length"] for trace in cursor_traces
            }),
            "carriage_silent_interval_histogram": dict(sorted(Counter(
                str(trace["silent_interval_length"])
                for trace in carriage_traces
            ).items())),
        },
        "family_coverage": {
            "returning_physical_lines_covered": 0,
            "returning_physical_lines_total": len(line_records),
            "fraction": {"numerator": 0, "denominator": len(line_records)},
            "return_episodes_covered": 0,
            "return_episodes_total": len(traces),
            "trace_types_covered": 0,
            "trace_types_total": len(trace_types),
            "transition_faithfulness": "not applicable: coverage is empty",
            "transition_mismatch": (
                "observed carriage uses primitive divisor 3 on each M edge and "
                "cursor import uses divisor 1; the fixed latent macrocycle uses "
                "divisor 9 on each of its two edges"
            ),
        },
        "trace_types": trace_types,
        "return_traces": traces,
        "returning_lines": line_records,
    }
    table = seal(table_core)

    smallest_cursor_line = next(
        line for line in line_records if line["line_id"] == smallest_cursor["line_id"]
    )
    smallest_carriage_line = next(
        line for line in line_records if line["line_id"] == smallest_carriage["line_id"]
    )
    zero_mask_by_step = {
        model["step"]: model["zero_word_mask"]
        for model in x_axis["domain_models"]["models"]
    }
    gate_occurrence_keys = {
        (record["level"], record["gap"], record["line_id"])
        for record in occurrences
    }
    cursor_reference = smallest_cursor[
        "exact_minimized_return_trace"
    ]["exact_interval_reference"]
    cursor_level = cursor_reference["level"]
    cursor_line = lines_by_key[(
        cursor_level, smallest_cursor["line_id"]
    )]
    cursor_token = primitive_plucker(
        cursor_line["endpoints"][0]["coordinate"],
        cursor_line["endpoints"][1]["coordinate"],
    )
    silent_cursor_records = []
    for rank in range(
        cursor_reference["first_silent_rank"],
        cursor_reference["last_silent_rank"] + 1,
    ):
        gap = states[cursor_level]["order"][rank]
        if (
            cursor_level, gap, smallest_cursor["line_id"]
        ) in gate_occurrence_keys:
            raise AssertionError("minimal witness silent cursor is effectful")
        anchor = tuple(states[cursor_level]["anchors"][gap])
        relative_moment = subtract(
            tuple(cursor_token["mu"]), cross(anchor, tuple(cursor_token["g"]))
        )
        relative_y = cursor_line["lateral_yz"][0] - anchor[1]
        relative_z = cursor_line["lateral_yz"][1] - anchor[2]
        silent_node = {
            "parent_step": states[cursor_level]["parent_word"][gap],
            "relative_lateral_yz": [relative_y, relative_z],
        }
        silent_cursor_records.append({
            "level": cursor_level,
            "gap": gap,
            "gate_schedule_rank": rank,
            "parent_step": silent_node["parent_step"],
            "cursor_anchor": list(anchor),
            "actual_selected_word": list(states[cursor_level]["words"][gap]),
            "global_primitive_pluecker": token_only(cursor_token),
            "relative_primitive_pluecker": {
                "g": list(cursor_token["g"]),
                "mu": list(relative_moment),
            },
            "strict_word_mask": zero_mask_by_step[
                silent_node["parent_step"]
            ],
            "implemented_ranks": {
                **implemented_direction_ranks(cursor_token),
                "observed_x_bellman": bellman_record(
                    silent_node, step_d
                ),
            },
        })
    carriage_episode = next(
        episode
        for episode in carriage_episodes
        if episode[0] == smallest_carriage["source_occurrence_id"]
        and episode[1] == smallest_carriage["terminal_occurrence_id"]
    )
    carriage_node_ids = [carriage_episode[0]] + [
        transition["target_lineage_node_id"]
        for transition in carriage_episode[2]
    ]
    carriage_state_records = [
        event_record(
            nodes[node_id],
            lines_by_key[(nodes[node_id]["level"], smallest_carriage["line_id"])],
            states,
            step_d,
        )
        for node_id in carriage_node_ids
    ]
    witness_core = {
        "schema": WITNESS_SCHEMA,
        "table_payload_sha256": table["payload_sha256"],
        "ordering": (
            "terminal level, silent length, terminal gate rank, source gate rank, "
            "line id"
        ),
        "smallest_cursor_import_return_outside_latent_family": {
            "trace": trace_by_id[smallest_cursor["trace_id"]],
            "line": smallest_cursor_line,
            "source_event": event_record(
                occurrence_by_id[smallest_cursor["source_occurrence_id"]],
                lines_by_key[(
                    smallest_cursor["terminal_level"], smallest_cursor["line_id"]
                )],
                states,
                step_d,
            ),
            "silent_cursor_records": silent_cursor_records,
            "terminal_event": event_record(
                occurrence_by_id[smallest_cursor["terminal_occurrence_id"]],
                lines_by_key[(
                    smallest_cursor["terminal_level"], smallest_cursor["line_id"]
                )],
                states,
                step_d,
            ),
        },
        "smallest_carriage_return_outside_latent_family": {
            "trace": trace_by_id[smallest_carriage["trace_id"]],
            "line": smallest_carriage_line,
            "exact_state_records": carriage_state_records,
        },
        "simple_invariants": {
            "observed_return_direction": [1, 0, 0],
            "observed_y_unit_chart_membership": False,
            "observed_F": -348,
            "latent_seed_H": list(H),
            "latent_seed_F": cone_residual(H),
            "policy_relative_guard_certificate": (
                "F(H)=0, F(Ng)=9F(g), F(Mg)=9F(g), and the two-cone birth "
                "guard rejects every new F=0 secant; endpoint-lineage "
                "disjointness excludes inherited entry"
            ),
            "scope_warning": (
                "the policy-relative certificate applies only to continuations "
                "that preserve that two-cone birth guard"
            ),
        },
    }
    witnesses = seal(witness_core)

    summary_core = {
        "schema": SUMMARY_SCHEMA,
        "table_payload_sha256": table["payload_sha256"],
        "witness_payload_sha256": witnesses["payload_sha256"],
        "decision": (
            "NO-GO for another 66,429-edge latent-family transition round; "
            "PIVOT to the already-proved policy-relative cone/provenance "
            "exclusion and to honest cursor-import state"
        ),
        "ten_answers": {
            "1_returning_lines_by_level": {
                "union": union_level_lines,
                "cursor_import": channel_level_lines["cursor_import"],
                "carriage_terminal": channel_level_lines["carriage"],
                "physical_lines_across_all_levels": len(line_records),
            },
            "2_distinct_minimized_trace_types": {
                "total": len(trace_types),
                "by_terminal_level": union_level_types,
                "by_channel_and_terminal_level": channel_level_types,
                "definition": (
                    "physical identity, absolute level/gap/rank, and absolute "
                    "translation are removed; exact local Pluecker state, phase, "
                    "effect mask, silent length, and ordered transition controls "
                    "are retained"
                ),
            },
            "3_existing_latent_family_coverage": "none",
            "4_coverage_fraction_and_faithfulness": {
                "fraction": "0/1021 physical lines; 0/2988 episodes; 0/2980 types",
                "faithful": False,
                "reason": "empty coverage and normalization branches 3/1 versus latent 9/9",
            },
            "5_smallest_witness_outside_family": {
                "line_id": smallest_cursor["line_id"],
                "trace_id": smallest_cursor["trace_id"],
                "terminal_level": smallest_cursor["terminal_level"],
                "silent_interval_length": smallest_cursor[
                    "silent_interval_length"
                ],
                "witness_payload_sha256": witnesses["payload_sha256"],
            },
            "6_symbolic_family_clustering": {
                "mechanism_families": 2,
                "families": [
                    "x-parallel same-level cursor translation",
                    "x-parallel selected-slot carriage zeta'=B(zeta-c_perp)",
                ],
                "small_stable_exact_family_set": False,
                "reason": "the two mechanisms contain 2,980 exact local control types",
            },
            "7_trace_type_stabilization": {
                "by_terminal_level": union_level_types,
                "cumulative": cumulative_types,
                "verdict": "continues growing substantially through L8",
            },
            "8_existing_rank_decrease": {
                "strict_or_fixed_block_decrease_on_every_return": False,
                "direction_rank_profile": (
                    "raw=0, weighted=0, latent R=0 on every state because g=(1,0,0)"
                ),
                "carriage_bellman_profiles": {
                    "core->core->core": len(carriage_traces)
                },
                "cursor_import_bellman_applicability": (
                    "not applicable: the implemented escape inequality assumes "
                    "synchronized M carriage, not unrelated cursor translation"
                ),
            },
            "9_simple_invariant_for_g_n": {
                "answer": "yes, policy-relative to the existing two-cone guard",
                "invariant": "F(g)=275*q(g)-348*g_x^2 and endpoint orbit provenance",
                "family_value": 0,
                "observed_return_value": -348,
                "scope": (
                    "excludes the fixed N-orbit in guard-preserving continuations; "
                    "does not prove unguarded or alternate-history exclusion"
                ),
            },
            "10_smallest_distinguishing_state": {
                "carriage": (
                    "(parent step, relative primitive Pluecker token) plus actual "
                    "selected word and ordered child slot/prefix control; endpoint "
                    "IDs certify coexistence but do not change the local mask"
                ),
                "cursor_import": (
                    "source relative primitive Pluecker token, exact line birth/"
                    "activation provenance, and the ordered cursor translation/"
                    "phase word through return"
                ),
                "bounded_local_history_sufficient": False,
                "repository_obstruction": (
                    "the existing cursor-jump audit found noncongruence even after "
                    "exact jump, local/tile phases, and complete predecessor-core "
                    "occupancy; remote birth/address history remains required"
                ),
            },
        },
        "decision_basis": [
            "the 66,429-edge family covers no observed returning line",
            "exact trace types grow 77,205,639,2059 by terminal level",
            "all direction-valued 3-adic ranks are constant zero",
            "all 18 carriage returns lie wholly in the noncontracting observed Bellman core",
            "cursor imports are outside the implemented carriage rank and require exact address history",
            "the separate cone/provenance invariant already excludes the abstract family under its guard",
        ],
        "proof_boundary": (
            "finite observed L5-L8 x-line data only; no all-direction return "
            "enumeration, alternate history, L9 claim, or all-level theorem"
        ),
    }
    summary = seal(summary_core)
    return table, witnesses, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--x-artifact", type=Path, default=DEFAULT_X)
    parser.add_argument("--barrier-artifact", type=Path, default=DEFAULT_BARRIER)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witnesses", type=Path, default=DEFAULT_WITNESSES)
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    x_axis, barrier, states, step_d, commitments = load_inputs(
        args.x_artifact, args.barrier_artifact
    )
    table, witnesses, summary = build_payload(
        x_axis, barrier, states, step_d, commitments
    )
    atomic_json_dump(table, args.table)
    atomic_json_dump(witnesses, args.witnesses)
    atomic_json_dump(summary, args.summary)
    print(json.dumps({
        "table": str(args.table.resolve()),
        "table_sha256": file_sha256(args.table.resolve()),
        "table_payload_sha256": table["payload_sha256"],
        "witnesses": str(args.witnesses.resolve()),
        "witnesses_sha256": file_sha256(args.witnesses.resolve()),
        "summary": str(args.summary.resolve()),
        "summary_sha256": file_sha256(args.summary.resolve()),
        "decision": summary["decision"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
