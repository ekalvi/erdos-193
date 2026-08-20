#!/usr/bin/env python3
"""Join realized x-line nodes to the pinned observed Bellman barrier.

This is a compact, read-only finite replay.  It consumes the canonical
``x_axis_far_secant_resonance`` and ``x_axis_bellman_barrier`` JSON artifacts;
it does not rebuild connector domains or modify either frozen checker.

For every strict-effect and latent zero-effect lineage node, the checker
compares the exact squared x-line offset

    h^2(y,z) = (36 y^2 - 12 y z + 36 z^2) / 35

with the outward rational interval for the observed/coarse step barrier D_s.
A node is certified core if ``h <= D_lower`` and certified exterior if
``h > D_upper``.  Any overlap is reported as unresolved rather than rounded
to either side.

For every recorded transition whose source is certified exterior, the
checker independently verifies the exact lateral recurrence and the outward
interval inequality

    (h_target - D_target) - 3 (h_source - D_source) >= 0.

The result remains finite observed-path evidence.  The step-only barrier is
not a universal Post relation, and nodes on a step with no observed outgoing
edge use the barrier experiment's terminal convention D_s=0.  Their exterior
classification is explicitly labelled terminal-vacuous.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_barrier_node_join.py run \
        --output /tmp/x-axis-barrier-node-join-canonical.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
SQRT_DECIMAL_DIGITS = 36


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


def scaled_decimal(integer, places):
    sign = "-" if integer < 0 else ""
    digits = str(abs(integer)).rjust(places + 1, "0")
    if places == 0:
        return sign + digits
    return sign + digits[:-places] + "." + digits[-places:]


def decimal_interval(lower, upper, places=15):
    scale = 10**places
    lower_scaled = (lower.numerator * scale) // lower.denominator
    upper_scaled = -((-upper.numerator * scale) // upper.denominator)
    return {
        "places": places,
        "lower_rounded_down": scaled_decimal(lower_scaled, places),
        "upper_rounded_up": scaled_decimal(upper_scaled, places),
    }


def interval_record(lower, upper):
    if lower > upper:
        raise AssertionError("reversed interval")
    return {
        "lower": rational_record(lower),
        "upper": rational_record(upper),
        "width": rational_record(upper - lower),
        "decimal_outward_enclosure": decimal_interval(lower, upper),
    }


def sqrt_fraction_interval(square):
    if square < 0:
        raise ValueError("negative squared norm")
    if square == 0:
        return Fraction(0), Fraction(0)
    scale = 10**SQRT_DECIMAL_DIGITS
    scaled_floor = (square.numerator * scale * scale) // square.denominator
    lower_integer = math.isqrt(scaled_floor)
    lower = Fraction(lower_integer, scale)
    if (
        lower_integer * lower_integer * square.denominator
        == square.numerator * scale * scale
    ):
        upper = lower
    else:
        upper = Fraction(lower_integer + 1, scale)
    if lower * lower > square or upper * upper < square:
        raise AssertionError("square-root interval is not outward")
    return lower, upper


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


def load_and_validate_artifacts(x_path, barrier_path):
    with barrier_path.open() as handle:
        barrier = json.load(handle)
    if barrier["checker_sha256"] != EXPECTED_BARRIER_CHECKER_SHA256:
        raise AssertionError("barrier artifact checker commitment drift")
    if barrier["input_sha256"]["x_axis_canonical_artifact"] != (
        EXPECTED_X_ARTIFACT_SHA256
    ):
        raise AssertionError("barrier artifact does not pin the expected x artifact")
    steps = barrier["threshold_barrier_comparison"]["steps"]
    if len(steps) != 124:
        raise AssertionError("barrier artifact step count drift")
    step_by_id = {record["step"]: record for record in steps}
    if set(step_by_id) != set(range(124)):
        raise AssertionError("barrier step identifiers drift")
    terminal_steps = {
        step for step, record in step_by_id.items()
        if record["observed_terminal_assigned_zero"]
    }
    if terminal_steps != {57, 65, 67, 80, 81, 86}:
        raise AssertionError("observed terminal step set drift")

    with x_path.open() as handle:
        x_axis = json.load(handle)
    if x_axis["checker_sha256"] != EXPECTED_X_CHECKER_SHA256:
        raise AssertionError("x-axis artifact checker commitment drift")
    graph = x_axis["closed_actual_selected_lineage_graph"]
    strict = x_axis["exact_prefix_effects"]["records"]
    latent = graph["latent_node_records"]
    transitions = graph["records"]
    returns = x_axis["short_actual_control_returns"]
    if stable_hash(strict) != x_axis["exact_prefix_effects"][
        "occurrence_stream_sha256"
    ]:
        raise AssertionError("strict-node stream commitment mismatch")
    if stable_hash(latent) != graph["latent_node_stream_sha256"]:
        raise AssertionError("latent-node stream commitment mismatch")
    if stable_hash(transitions) != graph["transition_stream_sha256"]:
        raise AssertionError("transition stream commitment mismatch")
    if stable_hash(returns["exact_effect_key_return_records"]) != returns[
        "exact_effect_key_return_stream_sha256"
    ]:
        raise AssertionError("effect-return stream commitment mismatch")
    if stable_hash(returns["exact_lateral_return_records"]) != returns[
        "exact_lateral_return_stream_sha256"
    ]:
        raise AssertionError("lateral-return stream commitment mismatch")
    if len(strict) != 11_154 or len(latent) != 24_066:
        raise AssertionError("realized node population drift")
    if len(transitions) != 27_103:
        raise AssertionError("realized transition population drift")
    return barrier, x_axis, step_by_id, terminal_steps


def classify_nodes(x_axis, step_by_id, terminal_steps):
    strict = x_axis["exact_prefix_effects"]["records"]
    latent = x_axis["closed_actual_selected_lineage_graph"][
        "latent_node_records"
    ]
    node_by_id = {}
    classification = {}
    totals = defaultdict(Counter)
    by_step = {
        step: {
            "strict": Counter(),
            "latent": Counter(),
        }
        for step in range(124)
    }
    by_level = defaultdict(Counter)
    by_order = defaultdict(Counter)
    stream_records = []

    for population, records in (("strict", strict), ("latent", latent)):
        for node in records:
            node_id = node["occurrence_id"]
            if node_id in node_by_id:
                raise AssertionError("duplicate lineage node id")
            if population == "strict":
                if node["latent_zero_effect"] or node[
                    "strict_x_secant_word_mask"
                ]["killed_words"] <= 0:
                    raise AssertionError("strict population contains a latent node")
            else:
                if not node["latent_zero_effect"] or node[
                    "strict_x_secant_word_mask"
                ]["killed_words"] != 0:
                    raise AssertionError("latent population contains an effect node")
            step = node["parent_step"]
            z = tuple(node["relative_lateral_yz"])
            h_squared = lateral_norm_squared(z)
            d_interval = step_by_id[step]["D_s_interval"]
            d_lower = rational(d_interval["lower"])
            d_upper = rational(d_interval["upper"])
            if d_lower < 0 or d_upper < d_lower:
                raise AssertionError("invalid barrier interval")
            if h_squared <= d_lower * d_lower:
                label = "core"
            elif h_squared > d_upper * d_upper:
                label = "exterior"
            else:
                label = "unresolved_interval_overlap"
            terminal = step in terminal_steps
            h_interval = sqrt_fraction_interval(h_squared)
            item = {
                "node": node,
                "population": population,
                "classification": label,
                "terminal_vacuous": terminal,
                "h_squared": h_squared,
                "h_interval": h_interval,
            }
            node_by_id[node_id] = node
            classification[node_id] = item
            totals[population][label] += 1
            totals[population]["total"] += 1
            totals["combined"][label] += 1
            totals["combined"]["total"] += 1
            if terminal:
                totals[population]["terminal_vacuous_" + label] += 1
                totals["combined"]["terminal_vacuous_" + label] += 1
                totals[population]["terminal_vacuous_total"] += 1
                totals["combined"]["terminal_vacuous_total"] += 1
            by_step[step][population][label] += 1
            by_step[step][population]["total"] += 1
            by_level[(population, node["level"])][label] += 1
            by_level[(population, node["level"])]["total"] += 1
            by_order[(population, node["stitch_order"])][label] += 1
            by_order[(population, node["stitch_order"])]["total"] += 1
            stream_records.append((
                node_id,
                population,
                step,
                h_squared.numerator,
                h_squared.denominator,
                label,
                terminal,
            ))

    graph = x_axis["closed_actual_selected_lineage_graph"]
    if len(node_by_id) != graph["lineage_nodes"]:
        raise AssertionError("classified node union does not equal lineage graph")
    if stable_hash(sorted(node_by_id)) != graph[
        "lineage_node_id_stream_sha256"
    ]:
        raise AssertionError("lineage node-id stream commitment mismatch")
    if totals["strict"]["unresolved_interval_overlap"] or totals[
        "latent"
    ]["unresolved_interval_overlap"]:
        raise AssertionError("a node classification overlaps its D interval")

    stream_records.sort()
    step_records = []
    for step in range(124):
        barrier_record = step_by_id[step]
        step_records.append({
            "step": step,
            "observed_terminal_assigned_zero": step in terminal_steps,
            "observed_outgoing_coarse_edges": barrier_record[
                "observed_outgoing_coarse_edges"
            ],
            "H_s_vs_D_s": barrier_record[
                "effectful_exterior_classification"
            ],
            "strict": dict(sorted(by_step[step]["strict"].items())),
            "latent": dict(sorted(by_step[step]["latent"].items())),
        })
    return {
        "node_by_id": node_by_id,
        "classification": classification,
        "summary": {
            "definition": (
                "core means exact h^2 <= D_lower^2; exterior means exact "
                "h^2 > D_upper^2; interval overlap would remain unresolved"
            ),
            "population_counts": {
                population: dict(sorted(counter.items()))
                for population, counter in sorted(totals.items())
            },
            "by_level": [
                {
                    "population": population,
                    "level": level,
                    **dict(sorted(counter.items())),
                }
                for (population, level), counter in sorted(by_level.items())
            ],
            "by_stitch_order": [
                {
                    "population": population,
                    "stitch_order": order,
                    **dict(sorted(counter.items())),
                }
                for (population, order), counter in sorted(by_order.items())
            ],
            "per_step": step_records,
            "classification_stream_sha256": stable_hash(stream_records),
        },
    }


def verify_exterior_transitions(x_axis, classified, terminal_steps):
    transitions = x_axis["closed_actual_selected_lineage_graph"]["records"]
    node_by_id = classified["node_by_id"]
    classification = classified["classification"]
    transition_classes = Counter()
    exterior_source_ids = set()
    interval_digest = hashlib.sha256()
    minimum_lower = None
    minimum_record = None
    tested = 0

    for transition in transitions:
        source_id = transition["source_lineage_node_id"]
        target_id = transition["target_lineage_node_id"]
        source = node_by_id[source_id]
        target = node_by_id[target_id]
        source_class = classification[source_id]["classification"]
        target_class = classification[target_id]["classification"]
        transition_classes[source_class + "->" + target_class] += 1
        if transition["source_has_strict_x_secant_effect"] != (
            classification[source_id]["population"] == "strict"
        ):
            raise AssertionError("transition source effect flag drift")
        if transition["target_has_strict_x_secant_effect"] != (
            classification[target_id]["population"] == "strict"
        ):
            raise AssertionError("transition target effect flag drift")
        if transition["child_step"] != target["parent_step"]:
            raise AssertionError("transition child/target step mismatch")
        source_z = tuple(source["relative_lateral_yz"])
        target_z = tuple(target["relative_lateral_yz"])
        control = tuple(transition["selected_prefix_control_c_perp"])
        if lateral_transport(source_z, control) != target_z:
            raise AssertionError("exact lateral recurrence failed")

        if source_class != "exterior":
            continue
        tested += 1
        exterior_source_ids.add(source_id)
        if source["parent_step"] in terminal_steps:
            raise AssertionError(
                "observed-terminal source unexpectedly has a transition"
            )
        if target_class != "exterior":
            raise AssertionError("certified exterior transition re-entered core")

        source_item = classification[source_id]
        target_item = classification[target_id]
        source_h_lower, source_h_upper = source_item["h_interval"]
        target_h_lower, target_h_upper = target_item["h_interval"]
        source_d = source_item["node"]["parent_step"]
        target_d = target_item["node"]["parent_step"]
        # D intervals are retrieved from the cached classification records.
        # The exact values are attached below before this routine is called.
        source_d_lower, source_d_upper = source_item["D_interval"]
        target_d_lower, target_d_upper = target_item["D_interval"]
        delta_lower = (
            target_h_lower - target_d_upper
            - 3 * (source_h_upper - source_d_lower)
        )
        delta_upper = (
            target_h_upper - target_d_lower
            - 3 * (source_h_lower - source_d_upper)
        )
        if delta_lower < 0:
            raise AssertionError(
                "exterior transition delta expansion not interval-certified",
                transition["transition_id"], delta_lower, delta_upper,
            )
        compact = (
            transition["transition_id"],
            source_d,
            target_d,
            delta_lower.numerator,
            delta_lower.denominator,
            delta_upper.numerator,
            delta_upper.denominator,
        )
        interval_digest.update(stable_bytes(compact))
        interval_digest.update(b"\n")
        if minimum_lower is None or delta_lower < minimum_lower:
            minimum_lower = delta_lower
            minimum_record = {
                "transition_id": transition["transition_id"],
                "source_node": source_id,
                "target_node": target_id,
                "source_step": source_d,
                "target_step": target_d,
                "delta_expansion_interval": interval_record(
                    delta_lower, delta_upper
                ),
            }

    if tested == 0 or minimum_lower is None:
        raise AssertionError("no exterior-source transition was tested")
    return {
        "all_transition_class_counts": dict(sorted(transition_classes.items())),
        "exterior_source_transitions_tested": tested,
        "distinct_exterior_source_nodes_with_a_transition": len(
            exterior_source_ids
        ),
        "terminal_vacuous_exterior_source_transitions": 0,
        "exact_lateral_recurrence_failures": 0,
        "exterior_to_nonexterior_transitions": 0,
        "negative_delta_expansion_lower_bounds": 0,
        "minimum_delta_expansion_lower_bound": rational_record(minimum_lower),
        "minimum_delta_expansion_witness": minimum_record,
        "exterior_transition_interval_stream_sha256": interval_digest.hexdigest(),
        "interpretation": (
            "for each recorded transition with a certified exterior source, "
            "the displayed outward interval proves delta_target >= 3 delta_source; "
            "this is a replay on the finite observed/coarse barrier graph only"
        ),
    }


def classify_returns(x_axis, classified):
    records = x_axis["short_actual_control_returns"][
        "exact_effect_key_return_records"
    ]
    classification = classified["classification"]
    effect_counts = Counter()
    action_counts = Counter()
    compact = []
    seen_sources = set()
    for record in records:
        source_id = record["source"]
        if source_id in seen_sources:
            raise AssertionError("effect-key return source repeated")
        seen_sources.add(source_id)
        item = classification[source_id]
        if item["population"] != "strict":
            raise AssertionError("effect-key return source is not strict-effect")
        label = item["classification"]
        effect_counts[label] += 1
        if record["selected_action_return"]:
            action_counts[label] += 1
        compact.append({
            "source": source_id,
            "step": item["node"]["parent_step"],
            "classification": label,
            "period": record["period"],
            "stitch_order": record["stitch_order"],
            "selected_action_return": record["selected_action_return"],
        })
    if len(records) != 36 or sum(action_counts.values()) != 6:
        raise AssertionError("effect/action-return census drift")
    compact.sort(key=lambda item: item["source"])
    return {
        "effect_key_return_sources": len(records),
        "effect_key_return_source_classification": dict(sorted(
            effect_counts.items()
        )),
        "effect_and_selected_action_return_sources": sum(
            action_counts.values()
        ),
        "effect_and_selected_action_source_classification": dict(sorted(
            action_counts.items()
        )),
        "source_classification_stream_sha256": stable_hash(compact),
        "action_return_sources": [
            item for item in compact if item["selected_action_return"]
        ],
        "interpretation": (
            "all classifications concern finite realized return sources; an "
            "effect/action return is not a transition-congruent policy cycle"
        ),
    }


def build_result(x_path, barrier_path):
    resource = enforce_resource_policy()
    inputs = validate_inputs(x_path, barrier_path)
    barrier, x_axis, step_by_id, terminal_steps = (
        load_and_validate_artifacts(x_path, barrier_path)
    )
    classified = classify_nodes(x_axis, step_by_id, terminal_steps)
    for item in classified["classification"].values():
        d = step_by_id[item["node"]["parent_step"]]["D_s_interval"]
        item["D_interval"] = rational(d["lower"]), rational(d["upper"])
    transition_result = verify_exterior_transitions(
        x_axis, classified, terminal_steps
    )
    return_result = classify_returns(x_axis, classified)
    barrier_counts = barrier["threshold_barrier_comparison"][
        "classification_counts"
    ]
    if barrier_counts != {
        "proved H_s <= D_s on observed coarse graph": 77,
        "proved H_s > D_s on observed coarse graph": 47,
    }:
        raise AssertionError("barrier H/D census drift")
    nonterminal_exterior_steps = sum(
        record["effectful_exterior_classification"]
        == "proved H_s > D_s on observed coarse graph"
        and not record["observed_terminal_assigned_zero"]
        for record in step_by_id.values()
    )
    if nonterminal_exterior_steps != 41:
        raise AssertionError("nonterminal H>D step census drift")
    return {
        "status": (
            "exact finite realized-node join to the pinned observed/coarse "
            "x-axis Bellman barrier; not a universal transition quotient, "
            "tail lemma, availability bound, or unconditional theorem"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": resource,
        "scope": {
            "levels": [5, 6, 7, 8],
            "stitch_orders": ["gate", "pipeline"],
            "channel": "x-parallel old--old--new candidate-site secants",
            "strict_effect_nodes": 11_154,
            "latent_zero_effect_nodes": 24_066,
            "recorded_selected-child_transitions": 27_103,
            "barrier_phase_graph": (
                "step-only arbitrary-switching merge of exact edges observed "
                "in the pinned realized L5-L8 closed lineage graph"
            ),
            "observed_terminal_steps_D_equals_zero_by_convention": sorted(
                terminal_steps
            ),
        },
        "barrier_step_census": {
            **barrier_counts,
            "proved H_s > D_s and nonterminal": nonterminal_exterior_steps,
            "proved H_s > D_s but observed-terminal": 47
            - nonterminal_exterior_steps,
        },
        "realized_node_classification": classified["summary"],
        "exterior_transition_delta_expansion": transition_result,
        "return_source_classification": return_result,
        "proof_boundary": {
            "proved_by_this_finite_replay": [
                "all 35,220 pinned lineage nodes are separated from their step's outward D interval with no unresolved overlap",
                "all recorded transitions from certified exterior nodes satisfy the exact lateral recurrence and a nonnegative outward interval for delta_target-3*delta_source",
                "all 36 exact effect-key return sources and all six selected-action-return sources lie in the observed Bellman core",
            ],
            "finite_observed_evidence_only": [
                "the core/exterior populations and return placement on one realized L5-L8 path under two recorded stitch orders",
            ],
            "not_proved": [
                "that the step-only graph contains alternate connector histories or any L9/later transition",
                "that observed-terminal steps have no unobserved successors",
                "transition congruence, a finite promoted core, a uniform residual rank, non-x channels, endpoint-on-candidate-line poisoning, or join closure",
                "positive connector availability, a safety fixed point, or an unconditional theorem",
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
        default=Path("/tmp/x-axis-barrier-node-join-canonical.json"),
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
