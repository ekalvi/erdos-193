#!/usr/bin/env python3
"""Independent structural verifier for the observed returning-line artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = ROOT / "design" / "observed-returning-line-table.json"
DEFAULT_SUMMARY = ROOT / "design" / "observed-returning-line-summary.json"
DEFAULT_WITNESSES = ROOT / "design" / "observed-returning-line-witnesses.json"
EXPECTED = {
    "cursor_lines": {"5": 37, "6": 101, "7": 315, "8": 1021},
    "carriage_lines": {"5": 0, "6": 0, "7": 4, "8": 14},
    "cursor_episodes": {"5": 77, "6": 205, "7": 635, "8": 2053},
    "carriage_episodes": {"5": 0, "6": 0, "7": 4, "8": 14},
    "cursor_types": {"5": 77, "6": 205, "7": 635, "8": 2045},
    "carriage_types": {"5": 0, "6": 0, "7": 4, "8": 14},
    "union_types": {"5": 77, "6": 205, "7": 639, "8": 2059},
    "cumulative_types": {"5": 77, "6": 282, "7": 921, "8": 2980},
}


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


def verify_seal(value):
    payload = dict(value)
    observed = payload.pop("payload_sha256")
    expected = stable_hash(payload)
    if observed != expected:
        raise AssertionError("payload seal mismatch", observed, expected)
    return observed


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def scale(factor, vector):
    return tuple(factor * value for value in vector)


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
    for value in vector:
        divisor = math.gcd(divisor, abs(value))
    return divisor


def primitive_plucker(first, second):
    chord = subtract(tuple(second), tuple(first))
    divisor = content(chord)
    if divisor == 0:
        raise AssertionError("repeated endpoints")
    direction = tuple(value // divisor for value in chord)
    flipped = next(value for value in direction if value) < 0
    if flipped:
        direction = scale(-1, direction)
    moment = cross(tuple(first), direction)
    if cross(tuple(second), direction) != moment or dot(direction, moment):
        raise AssertionError("invalid primitive Pluecker token")
    return {
        "g": list(direction),
        "mu": list(moment),
        "chord": list(chord),
        "content": divisor,
        "flipped": flipped,
    }


def verify_line(line):
    if line["endpoint_stable_ids"] != sorted(line["endpoint_stable_ids"]):
        raise AssertionError("endpoint IDs are not canonical")
    membership = line["latent_family_membership"]
    if (
        membership["member_of_exact_latent_L_n_family"]
        or membership["member_of_any_66429_y_unit_residue_graph"]
        or membership["observed_guard_cone_residual_F"] != -348
    ):
        raise AssertionError("latent-family classification drift")
    provenance = line["genealogical_provenance"]
    endpoints = provenance["birth_endpoints"]
    if len(endpoints) != 2:
        raise AssertionError("line does not have two birth endpoints")
    birth = primitive_plucker(
        endpoints[0]["coordinate_at_line_birth"],
        endpoints[1]["coordinate_at_line_birth"],
    )
    if {"g": birth["g"], "mu": birth["mu"]} != provenance[
        "birth_primitive_pluecker"
    ]:
        raise AssertionError("birth token mismatch")
    if birth["chord"] != provenance["birth_endpoint_chord"]:
        raise AssertionError("birth chord mismatch")
    normalization = provenance["birth_primitive_normalization"]
    if (
        normalization["chord_content"] != birth["content"]
        or normalization["canonical_sign_flipped"] != birth["flipped"]
    ):
        raise AssertionError("birth primitive normalization mismatch")

    level_tokens = {}
    for level_record in provenance["level_genealogy"]:
        level = level_record["level"]
        current = level_record["endpoint_coordinates"]
        token = primitive_plucker(current[0]["coordinate"], current[1]["coordinate"])
        public = {"g": token["g"], "mu": token["mu"]}
        if public != level_record["primitive_pluecker"]:
            raise AssertionError("level token mismatch", line["line_id"], level)
        if token["g"] != [1, 0, 0]:
            raise AssertionError("returning direction is not x-parallel")
        ranks = level_record["implemented_direction_and_moment_ranks"]
        if (
            ranks["padic_raw_min_depth"] != 0
            or ranks["padic_weighted_projective_candidate"] != 0
            or ranks["latent_padic_depth_R"] != 0
            or ranks["guard_cone_residual_F"] != -348
        ):
            raise AssertionError("implemented direction rank drift")
        level_tokens[level] = public
    for change in provenance["primitive_normalization_changes"]:
        if (
            change["transition"] != "carriage"
            or change["primitive_divisor"] != 3
            or change["canonical_sign_flipped"]
        ):
            raise AssertionError("carriage normalization branch drift")
        source = change["source_level"]
        target = change["target_level"]
        if target != source + 1:
            raise AssertionError("nonconsecutive carriage normalization")
        expected_source = (
            provenance["birth_primitive_pluecker"]
            if source == provenance["birth_level"]
            else level_tokens[source]
        )
        if change["source_token"] != expected_source:
            raise AssertionError("normalization source token mismatch")
        if change["target_token"] != level_tokens[target]:
            raise AssertionError("normalization target token mismatch")

    event_ids = set()
    for event in line["every_effectful_gate_phase_cursor"]:
        if event["occurrence_id"] in event_ids:
            raise AssertionError("duplicate effect occurrence")
        event_ids.add(event["occurrence_id"])
        if event["strict_word_mask"]["killed_words"] <= 0:
            raise AssertionError("effect record has an empty strict mask")
        if event["global_primitive_pluecker"] != level_tokens[event["level"]]:
            raise AssertionError("effect/global token mismatch")
        ranks = event["implemented_ranks"]
        if (
            ranks["padic_raw_min_depth"] != 0
            or ranks["padic_weighted_projective_candidate"] != 0
            or ranks["latent_padic_depth_R"] != 0
            or ranks["observed_x_bellman"]["classification"]
            not in ("core", "exterior")
        ):
            raise AssertionError("effect rank record drift")
    return level_tokens


def verify_trace(trace):
    if trace["silent_interval_length"] < 1:
        raise AssertionError("trivial interval retained as a return")
    exact = trace["exact_minimized_return_trace"]
    if exact["effect_word"] != [
        "effect", {"silent": trace["silent_interval_length"]}, "effect"
    ]:
        raise AssertionError("effect word mismatch")
    if trace["channel"] == "cursor_import":
        if (
            exact["cursor_transitions"] != trace["silent_interval_length"] + 1
            or exact["primitive_normalization"]
            != "identity at every cursor import"
            or exact["source"]["strict_killed_words"] <= 0
            or exact["target"]["strict_killed_words"] <= 0
        ):
            raise AssertionError("cursor return structure mismatch")
        interval = exact["exact_interval_reference"]
        if (
            interval["terminal_rank"] - interval["source_rank"]
            != exact["cursor_transitions"]
            or interval["last_silent_rank"] - interval["first_silent_rank"] + 1
            != trace["silent_interval_length"]
        ):
            raise AssertionError("cursor interval reference mismatch")
        type_payload = {
            "channel": "cursor_import",
            "source": exact["source"],
            "silent_interval_length": trace["silent_interval_length"],
            "net_cursor_translation": exact["net_cursor_translation"],
            "line_local_control_stream_sha256": exact[
                "line_local_control_stream_sha256"
            ],
            "target": exact["target"],
            "primitive_normalization_divisors": {
                "value": 1,
                "count": exact["cursor_transitions"],
            },
        }
        expected_trace_id = stable_hash((
            "cursor_import", trace["terminal_level"], trace["line_id"],
            trace["source_occurrence_id"], trace["terminal_occurrence_id"],
        ))
    elif trace["channel"] == "carriage":
        states = exact["states"]
        edges = exact["edges"]
        if len(states) != trace["silent_interval_length"] + 2:
            raise AssertionError("carriage state count mismatch")
        if len(edges) != len(states) - 1:
            raise AssertionError("carriage edge count mismatch")
        if states[0]["strict_killed_words"] <= 0 or states[-1][
            "strict_killed_words"
        ] <= 0:
            raise AssertionError("carriage endpoints are not effectful")
        if any(state["strict_killed_words"] for state in states[1:-1]):
            raise AssertionError("carriage interval contains an effect")
        if any(
            edge["primitive_normalization"]["primitive_divisor"] != 3
            for edge in edges
        ):
            raise AssertionError("carriage normalization is not t=3")
        if any(
            item["classification"] != "core"
            for item in exact["observed_x_bellman_profile"]
        ):
            raise AssertionError("observed carriage return left Bellman core")
        type_payload = {
            "channel": "carriage",
            "states": states,
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
            } for edge in edges],
        }
        expected_trace_id = stable_hash((
            "carriage", trace["source_occurrence_id"],
            trace["terminal_occurrence_id"],
            [edge["transition_id"] for edge in edges],
        ))
    else:
        raise AssertionError("unknown return channel")
    if stable_hash(type_payload) != trace["trace_type_id"]:
        raise AssertionError("trace-type hash mismatch")
    if expected_trace_id != trace["trace_id"]:
        raise AssertionError("trace ID mismatch")


def channel_level_sets(traces, field):
    result = {}
    for channel in ("cursor_import", "carriage"):
        result[channel] = {
            str(level): {
                trace[field]
                for trace in traces
                if trace["channel"] == channel
                and trace["terminal_level"] == level
            }
            for level in range(5, 9)
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witnesses", type=Path, default=DEFAULT_WITNESSES)
    args = parser.parse_args()
    table = load_json(args.table)
    summary = load_json(args.summary)
    witnesses = load_json(args.witnesses)
    table_seal = verify_seal(table)
    summary_seal = verify_seal(summary)
    witness_seal = verify_seal(witnesses)
    if (
        summary["table_payload_sha256"] != table_seal
        or summary["witness_payload_sha256"] != witness_seal
        or witnesses["table_payload_sha256"] != table_seal
    ):
        raise AssertionError("artifact cross-link mismatch")

    lines = table["returning_lines"]
    traces = table["return_traces"]
    types = table["trace_types"]
    if len(lines) != 1021 or len(traces) != 2988 or len(types) != 2980:
        raise AssertionError("global census drift")
    line_by_id = {}
    for line in lines:
        if line["line_id"] in line_by_id:
            raise AssertionError("duplicate returning line")
        line_by_id[line["line_id"]] = line
        verify_line(line)
    trace_by_id = {}
    trace_groups = defaultdict(list)
    trace_refs = defaultdict(lambda: {"cursor_import": [], "carriage": []})
    for trace in traces:
        if trace["trace_id"] in trace_by_id:
            raise AssertionError("duplicate return trace")
        if trace["line_id"] not in line_by_id:
            raise AssertionError("trace references an absent line")
        verify_trace(trace)
        trace_by_id[trace["trace_id"]] = trace
        trace_groups[trace["trace_type_id"]].append(trace)
        trace_refs[trace["line_id"]][trace["channel"]].append(trace["trace_id"])
    if set(trace_groups) != {record["trace_type_id"] for record in types}:
        raise AssertionError("trace-type index mismatch")
    for record in types:
        members = trace_groups[record["trace_type_id"]]
        if record["occurrences"] != len(members):
            raise AssertionError("trace-type occurrence count mismatch")
    for line_id, line in line_by_id.items():
        if sorted(trace_refs[line_id]["cursor_import"]) != sorted(
            line["cursor_import_return_trace_ids"]
        ):
            raise AssertionError("cursor trace references mismatch")
        if sorted(trace_refs[line_id]["carriage"]) != sorted(
            line["carriage_return_trace_ids"]
        ):
            raise AssertionError("carriage trace references mismatch")

    line_sets = channel_level_sets(traces, "line_id")
    episode_sets = channel_level_sets(traces, "trace_id")
    type_sets = channel_level_sets(traces, "trace_type_id")
    observed = {
        "cursor_lines": {
            level: len(values)
            for level, values in line_sets["cursor_import"].items()
        },
        "carriage_lines": {
            level: len(values)
            for level, values in line_sets["carriage"].items()
        },
        "cursor_episodes": {
            level: len(values)
            for level, values in episode_sets["cursor_import"].items()
        },
        "carriage_episodes": {
            level: len(values)
            for level, values in episode_sets["carriage"].items()
        },
        "cursor_types": {
            level: len(values)
            for level, values in type_sets["cursor_import"].items()
        },
        "carriage_types": {
            level: len(values)
            for level, values in type_sets["carriage"].items()
        },
        "union_types": {
            str(level): len({
                trace["trace_type_id"] for trace in traces
                if trace["terminal_level"] == level
            })
            for level in range(5, 9)
        },
        "cumulative_types": {
            str(level): len({
                trace["trace_type_id"] for trace in traces
                if trace["terminal_level"] <= level
            })
            for level in range(5, 9)
        },
    }
    if observed != EXPECTED:
        raise AssertionError("per-level census drift", observed)

    cursor_witness = witnesses[
        "smallest_cursor_import_return_outside_latent_family"
    ]
    carriage_witness = witnesses[
        "smallest_carriage_return_outside_latent_family"
    ]
    for witness in (cursor_witness, carriage_witness):
        trace = witness["trace"]
        if trace != trace_by_id[trace["trace_id"]]:
            raise AssertionError("witness trace is not table-exact")
        if witness["line"] != line_by_id[trace["line_id"]]:
            raise AssertionError("witness line is not table-exact")
    silent_records = cursor_witness["silent_cursor_records"]
    if len(silent_records) != cursor_witness["trace"]["silent_interval_length"]:
        raise AssertionError("minimal cursor witness silent-state count mismatch")
    if any(record["strict_word_mask"]["killed_words"] for record in silent_records):
        raise AssertionError("minimal cursor witness contains an effectful middle")
    carriage_states = carriage_witness["exact_state_records"]
    if len(carriage_states) != 3:
        raise AssertionError("minimal carriage witness state count drift")
    if carriage_states[1]["strict_word_mask"]["killed_words"] != 0:
        raise AssertionError("minimal carriage witness middle is not silent")

    answers = summary["ten_answers"]
    if (
        answers["2_distinct_minimized_trace_types"]["total"] != len(types)
        or answers["3_existing_latent_family_coverage"] != "none"
        or answers["8_existing_rank_decrease"][
            "strict_or_fixed_block_decrease_on_every_return"
        ]
        or answers["9_simple_invariant_for_g_n"]["family_value"] != 0
    ):
        raise AssertionError("summary answer drift")
    print(json.dumps({
        "status": "verified",
        "table_file_sha256": file_sha256(args.table),
        "table_payload_sha256": table_seal,
        "summary_file_sha256": file_sha256(args.summary),
        "summary_payload_sha256": summary_seal,
        "witness_file_sha256": file_sha256(args.witnesses),
        "witness_payload_sha256": witness_seal,
        "returning_lines": len(lines),
        "return_episodes": len(traces),
        "trace_types": len(types),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
