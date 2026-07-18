#!/usr/bin/env python3
"""Observed x-axis Bellman-barrier experiment.

This checker asks a deliberately narrow question about the exact realized
L5--L8 x-parallel lineage graph.  For an x-parallel line, write its lateral
coordinate relative to a corridor start as ``z=(y,z)``.  The exact transport
recorded by ``x_axis_far_secant_resonance.py`` is

    z_child = B (z_parent - c),       B = [[0,-3],[3,-1]].

The quadratic form

    ||(y,z)||_S^2 = (36 y^2 - 12 y z + 36 z^2) / 35

satisfies ``B^T S B = 9 S``.  Hence a transition with prefix control ``c``
has the rigorous lower bound

    ||z_child||_S >= 3 (||z_parent||_S - ||c||_S).

On the *observed step-only coarse graph*, this program computes barriers

    D_s = max_{observed e:s->t} (||c_e||_S + D_t/3)

and the exact candidate-site threshold

    H_s = max { ||x_perp||_S : x is an interior site of an effective
                                connector-domain word for step s }.

The Bellman calculation uses exact rational squared norms.  Square roots and
the fixed point are enclosed by outward-rounded rational intervals; ordinary
binary floating point is not used in the certificate.

Scope warning
-------------

The graph is extracted from one pinned canonical realized-path artifact.  It
merges phases by source/child step and permits arbitrary switching among the
observed coarse edges.  It is neither a universal transition graph nor a
transition-congruent quotient.  A step with no observed outgoing edge is
reported as an observed terminal and assigned D_s=0 only in this finite
experiment.  The result covers only the x-parallel old-old-new site channel.

Estimate mode validates and summarizes the pinned graph without scanning the
connector-domain words.  Run mode reconstructs all 124 effective domains in
the authoritative D2--4 / fragile-D5 order and validates their word order and
site census against the pinned x-axis artifact.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_bellman_barrier.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_bellman_barrier.py run \
        --output /tmp/x-axis-bellman-barrier-canonical.json
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import pickle
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_X_ARTIFACT = Path(
    "/tmp/x-axis-far-secant-resonance-canonical.json"
)
EXPECTED_X_ARTIFACT_SHA256 = (
    "0ebbfd97194fce4453269ad1c01eb1281e9d3a5aa526f1f036e409b82ad36cc1"
)
EXPECTED_X_CHECKER_SHA256 = (
    "7a0ea121ad91fa578026225a0c892eabf564c7250d9f3acb1a6ba7bbd162dd4c"
)
EXPECTED_INPUT_SHA256 = {
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "dstar5_fragile.pkl": (
        "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3"
    ),
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "design/x_axis_far_secant_resonance.py": EXPECTED_X_CHECKER_SHA256,
}
EXPECTED_ARTIFACT_INPUT_SHA256 = {
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "design/inherited_tile_lifetime.py": (
        "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4"
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
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
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
FRAGILE_CUT = 2000
EXPECTED_MENU_SIZE = 124
EXPECTED_EFFECTIVE_DOMAIN_WORDS = 12_537_146
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
B_LATERAL = ((0, -3), (3, -1))
SQRT_DECIMAL_DIGITS = 36
BELLMAN_WIDTH_TARGET = Fraction(1, 10**28)
BELLMAN_MAX_ITERATIONS = 256


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


def menu_vectors():
    return tuple(
        (x, y, z)
        for x, y, z in product(range(-2, 3), repeat=3)
        if (x, y, z) != (0, 0, 0)
    )


MENU = menu_vectors()
if len(MENU) != EXPECTED_MENU_SIZE:
    raise AssertionError("radius-two menu cardinality drift")
IDX = {step: index for index, step in enumerate(MENU)}


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def apply_matrix(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def lateral_norm_squared(vector):
    """Exact x-line offset norm squared for vector=(y,z)."""
    y, z = vector
    return Fraction(36 * y * y - 12 * y * z + 36 * z * z, 35)


def verify_quadratic_identity():
    # Polarized form with the common denominator retained as integers.
    s = ((36, -6), (-6, 36))

    def transpose(matrix):
        return tuple(zip(*matrix))

    def multiply(first, second):
        return tuple(tuple(
            sum(first[row][k] * second[k][column] for k in range(2))
            for column in range(2)
        ) for row in range(2))

    lhs = multiply(multiply(transpose(B_LATERAL), s), B_LATERAL)
    rhs = tuple(tuple(9 * value for value in row) for row in s)
    if lhs != rhs:
        raise AssertionError("B^T S B != 9 S", lhs, rhs)
    return {
        "S_numerator_over_35": as_json(s),
        "B": as_json(B_LATERAL),
        "verified_B_transpose_S_B_equals_9S": True,
    }


def sqrt_fraction_interval(square, decimal_digits=SQRT_DECIMAL_DIGITS):
    """Return exact rational bounds enclosing sqrt(square)."""
    if square < 0:
        raise ValueError("cannot take square root of a negative rational")
    if square == 0:
        return Fraction(0), Fraction(0)
    scale = 10**decimal_digits
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
        raise AssertionError("sqrt interval is not outward enclosing")
    return lower, upper


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


def enforce_resource_policy():
    if sys_flags_optimize():
        raise RuntimeError("run without -O so certificate assertions remain active")
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "every thread-cap environment variable must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process priority on this platform")
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


def sys_flags_optimize():
    # Isolated for a trivial unit of certificate logic.
    import sys
    return sys.flags.optimize


def observed_inputs(x_artifact_path):
    if not x_artifact_path.is_file():
        raise FileNotFoundError(x_artifact_path)
    artifact_hash = file_sha256(x_artifact_path)
    if artifact_hash != EXPECTED_X_ARTIFACT_SHA256:
        raise RuntimeError(
            "pinned x-axis artifact hash drift: "
            f"{artifact_hash} != {EXPECTED_X_ARTIFACT_SHA256}"
        )
    hashes = {"x_axis_canonical_artifact": artifact_hash}
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        path = ROOT / relative
        observed = file_sha256(path)
        if observed != expected:
            raise RuntimeError(
                f"input hash drift for {relative}: {observed} != {expected}"
            )
        hashes[relative] = observed
    return hashes


def validate_artifact_and_extract_graph(path):
    with path.open() as handle:
        artifact = json.load(handle)
    if artifact.get("checker_sha256") != EXPECTED_X_CHECKER_SHA256:
        raise AssertionError("x-axis artifact checker commitment drift")
    if artifact.get("input_sha256") != EXPECTED_ARTIFACT_INPUT_SHA256:
        raise AssertionError("x-axis artifact embedded input commitments drift")
    if artifact["lateral_transport"]["B"] != as_json(B_LATERAL):
        raise AssertionError("x-axis artifact lateral matrix drift")
    if artifact["domain_models"]["effective_domain_words"] != (
        EXPECTED_EFFECTIVE_DOMAIN_WORDS
    ):
        raise AssertionError("x-axis artifact effective-domain total drift")

    model_records = artifact["domain_models"]["models"]
    if len(model_records) != len(MENU):
        raise AssertionError("x-axis artifact does not have 124 domain models")
    model_by_step = {record["step"]: record for record in model_records}
    if set(model_by_step) != set(range(len(MENU))):
        raise AssertionError("x-axis artifact model step set drift")

    graph = artifact["closed_actual_selected_lineage_graph"]
    transitions = graph["records"]
    if len(transitions) != graph["transitions"]:
        raise AssertionError("x-axis graph transition count drift")
    phase = artifact["selected_slot_phase_stabilization"]
    phase_classes = phase["classes"]
    if sum(record["occurrences"] for record in phase_classes) != len(
        transitions
    ):
        raise AssertionError("phase-class occurrence count drift")

    phase_key_counts = Counter()
    edge_occurrences = Counter()
    edge_orders = defaultdict(Counter)
    source_steps = set()
    child_steps = set()
    for record in phase_classes:
        order_name = record["stitch_order"]
        source_step = record["source_step"]
        word = tuple(record["selected_word"])
        slot = record["slot_zero_based"]
        prefix = tuple(record["prefix_control"])
        child_step = record["child_step"]
        occurrences = record["occurrences"]
        exact_key = (
            order_name, source_step, word, slot, prefix, child_step
        )
        if stable_hash(exact_key) != record["phase_key_sha256"]:
            raise AssertionError("phase key commitment mismatch")
        if not 0 <= source_step < len(MENU):
            raise AssertionError("invalid source step")
        if not 0 <= slot < len(word) or word[slot] != child_step:
            raise AssertionError("selected word/slot/child mismatch")
        expected_prefix = (0, 0, 0)
        for menu_index in word[:slot]:
            expected_prefix = add(expected_prefix, MENU[menu_index])
        if prefix != expected_prefix:
            raise AssertionError("selected prefix control mismatch")
        endpoint = (0, 0, 0)
        for menu_index in word:
            endpoint = add(endpoint, MENU[menu_index])
        if endpoint != apply_matrix(M_BAL3, MENU[source_step]):
            raise AssertionError("selected word has wrong scaled endpoint")
        record_key = (order_name, word, slot, prefix, child_step)
        phase_key_counts[record_key] += occurrences
        control = (prefix[1], prefix[2])
        coarse_edge = (source_step, child_step, control)
        edge_occurrences[coarse_edge] += occurrences
        edge_orders[coarse_edge][order_name] += occurrences
        source_steps.add(source_step)
        child_steps.add(child_step)

    graph_key_counts = Counter()
    for record in transitions:
        prefix = tuple(record["selected_prefix_control_c"])
        if tuple(record["selected_prefix_control_c_perp"]) != (
            prefix[1], prefix[2]
        ):
            raise AssertionError("graph perpendicular control mismatch")
        key = (
            record["stitch_order"],
            tuple(record["actual_selected_word"]),
            record["actual_child_slot_zero_based"],
            prefix,
            record["child_step"],
        )
        graph_key_counts[key] += 1
    if graph_key_counts != phase_key_counts:
        raise AssertionError("phase classes do not exactly cover graph records")

    edges = []
    for (source, target, control), occurrences in sorted(
        edge_occurrences.items()
    ):
        square = lateral_norm_squared(control)
        lower, upper = sqrt_fraction_interval(square)
        edges.append({
            "source_step": source,
            "target_step": target,
            "prefix_control_perp": as_json(control),
            "B_e_squared_exact": rational_record(square),
            "B_e_interval": interval_record(lower, upper),
            "observed_occurrences": occurrences,
            "observed_occurrences_by_order": dict(
                sorted(edge_orders[(source, target, control)].items())
            ),
        })

    extraction = {
        "scope": (
            "step-only coarse graph extracted from all exact closed-lineage "
            "transition records in the pinned realized L5-L8 x-axis artifact; "
            "arbitrary switching among observed edges is an overapproximation "
            "of those finite records, not a universal Post relation"
        ),
        "exact_graph_transition_records": len(transitions),
        "exact_phase_classes": len(phase_classes),
        "coarse_unique_edges": len(edges),
        "source_step_types_with_observed_outgoing_edges": len(source_steps),
        "observed_terminal_step_types_without_outgoing_edges": sorted(
            set(range(len(MENU))) - source_steps
        ),
        "child_step_types_observed": len(child_steps),
        "stitch_orders": dict(sorted(Counter(
            record["stitch_order"] for record in transitions
        ).items())),
        "materialized_latent_zero_effect_nodes": graph[
            "materialized_latent_zero_effect_nodes"
        ],
        "transition_stream_sha256": graph["transition_stream_sha256"],
        "phase_class_stream_sha256": phase["class_stream_sha256"],
        "coarse_edge_stream_sha256": stable_hash(edges),
        "edges": edges,
    }
    del artifact, transitions, phase_classes
    gc.collect()
    return extraction, model_by_step


def bellman_intervals(graph):
    outgoing = defaultdict(list)
    maximum_b_upper = Fraction(0)
    for edge in graph["edges"]:
        square_record = edge["B_e_squared_exact"]
        square = Fraction(
            square_record["numerator"], square_record["denominator"]
        )
        lower, upper = sqrt_fraction_interval(square)
        outgoing[edge["source_step"]].append((edge, lower, upper))
        maximum_b_upper = max(maximum_b_upper, upper)

    lower_values = [Fraction(0) for _ in MENU]
    global_upper = Fraction(3, 2) * maximum_b_upper
    upper_values = [global_upper for _ in MENU]

    def apply(values, endpoint):
        result = []
        for step in range(len(MENU)):
            candidates = outgoing.get(step, ())
            if not candidates:
                result.append(Fraction(0))
                continue
            result.append(max(
                (lower if endpoint == "lower" else upper)
                + values[edge["target_step"]] / 3
                for edge, lower, upper in candidates
            ))
        return result

    iterations = 0
    while iterations < BELLMAN_MAX_ITERATIONS:
        next_lower = apply(lower_values, "lower")
        next_upper = apply(upper_values, "upper")
        if any(a > b for a, b in zip(lower_values, next_lower)):
            raise AssertionError("Bellman lower iteration is not monotone")
        if any(a < b for a, b in zip(upper_values, next_upper)):
            raise AssertionError("Bellman upper iteration is not monotone")
        lower_values = next_lower
        upper_values = next_upper
        iterations += 1
        if max(
            upper - lower
            for lower, upper in zip(lower_values, upper_values)
        ) <= BELLMAN_WIDTH_TARGET:
            break
    else:
        raise RuntimeError("Bellman interval iteration did not converge")

    next_lower = apply(lower_values, "lower")
    next_upper = apply(upper_values, "upper")
    if any(lower > update for lower, update in zip(lower_values, next_lower)):
        raise AssertionError("final lower vector is not pre-fixed")
    if any(update > upper for update, upper in zip(next_upper, upper_values)):
        raise AssertionError("final upper vector is not post-fixed")

    records = []
    terminals = set(graph["observed_terminal_step_types_without_outgoing_edges"])
    for step, (lower, upper) in enumerate(zip(lower_values, upper_values)):
        records.append({
            "step": step,
            "observed_outgoing_coarse_edges": len(outgoing.get(step, ())),
            "observed_terminal_assigned_zero": step in terminals,
            "D_s_interval": interval_record(lower, upper),
        })
    return {
        "definition": (
            "D_s=max over observed coarse edges e:s->t of "
            "(sqrt(B_e_squared)+D_t/3); empty observed maximum is assigned 0"
        ),
        "status": (
            "rigorous interval for the arbitrary-switching fixed point of the "
            "finite observed step-only graph; not a universal construction barrier"
        ),
        "sqrt_decimal_digits": SQRT_DECIMAL_DIGITS,
        "target_maximum_interval_width": rational_record(
            BELLMAN_WIDTH_TARGET
        ),
        "iterations": iterations,
        "maximum_final_interval_width": rational_record(max(
            upper - lower
            for lower, upper in zip(lower_values, upper_values)
        )),
        "initial_global_postfixed_upper": rational_record(global_upper),
        "lower_vector_is_prefix_iteration_from_zero": True,
        "upper_vector_is_postfixed": True,
        "step_records": records,
        "barrier_stream_sha256": stable_hash(records),
    }


def scan_step_threshold(step, domain, layer, expected_model):
    expected_endpoint = apply_matrix(M_BAL3, MENU[step])
    word_digest = hashlib.sha256()
    sites = set()
    lateral_sites = set()
    max_square = Fraction(0)
    witnesses = set()

    for word_index, raw_word in enumerate(domain):
        word = tuple(raw_word)
        if len(word) > 255:
            raise AssertionError("word length cannot enter one digest byte")
        word_digest.update(len(word).to_bytes(1, "little"))
        position = (0, 0, 0)
        word_sites = []
        for ordinal, menu_index in enumerate(word):
            if not 0 <= menu_index < len(MENU):
                raise AssertionError("domain word has invalid menu index")
            word_digest.update(menu_index.to_bytes(1, "little"))
            position = add(position, MENU[menu_index])
            if ordinal + 1 < len(word):
                word_sites.append(position)
        if position != expected_endpoint:
            raise AssertionError(
                "connector endpoint mismatch", step, word_index,
                position, expected_endpoint,
            )
        if len(word_sites) != len(set(word_sites)):
            raise AssertionError("connector word repeats an interior site")
        for site in word_sites:
            sites.add(site)
            lateral_point = (site[1], site[2])
            lateral_sites.add(lateral_point)
            square = lateral_norm_squared(lateral_point)
            if square > max_square:
                max_square = square
                witnesses = {site}
            elif square == max_square:
                witnesses.add(site)

    observed_digest = word_digest.hexdigest()
    checks = {
        "step": step,
        "layer": layer,
        "domain_words": len(domain),
        "candidate_sites": len(sites),
        "candidate_lateral_site_classes": len(lateral_sites),
        "expected_scaled_parent_step": as_json(expected_endpoint),
        "word_order_sha256": observed_digest,
    }
    expected_checks = {
        "step": expected_model["step"],
        "layer": expected_model["effective_domain_layer"],
        "domain_words": expected_model["domain_words"],
        "candidate_sites": expected_model["candidate_sites"],
        "candidate_lateral_site_classes": expected_model[
            "candidate_lateral_site_classes"
        ],
        "expected_scaled_parent_step": expected_model[
            "expected_scaled_parent_step"
        ],
        "word_order_sha256": expected_model["word_order_sha256"],
    }
    if checks != expected_checks:
        raise AssertionError(
            "effective-domain reconstruction disagrees with pinned x-axis model",
            checks, expected_checks,
        )
    lower, upper = sqrt_fraction_interval(max_square)
    return {
        **checks,
        "H_s_squared_exact": rational_record(max_square),
        "H_s_interval": interval_record(lower, upper),
        "maximizing_site_offsets": as_json(sorted(witnesses)),
        "candidate_site_coordinate_stream_sha256": stable_hash(sorted(sites)),
    }


def stream_effective_domains(process_step):
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        d4 = pickle.load(handle)
    observed_menu = tuple(tuple(step) for step in d4.pop("menu"))
    if observed_menu != MENU:
        raise AssertionError("connector_domains4 menu drift")
    raw_domains = d4.pop("domains")
    surviving = tuple(d4.pop("surviving"))
    if d4:
        raise AssertionError("unexpected connector_domains4 fields", sorted(d4))
    if set(raw_domains) != set(range(len(MENU))):
        raise AssertionError("D2--4 step-key mismatch")
    if len(surviving) != len(set(surviving)):
        raise AssertionError("duplicate D2--4 surviving step")

    d24_sizes = {step: len(words) for step, words in raw_domains.items()}
    fragile_steps = {
        step for step, size in d24_sizes.items() if size < FRAGILE_CUT
    }
    fragile_bases = {}
    processed = []
    total_words = 0

    for step in sorted(raw_domains):
        raw_words = raw_domains.pop(step)
        if isinstance(raw_words, list):
            raw_words.sort(key=len)
            base = raw_words
        else:
            base = sorted(raw_words, key=len)
        if step in fragile_steps:
            fragile_bases[step] = base
        else:
            process_step(step, base, "D2-4-only")
            processed.append(step)
            total_words += len(base)
            del base
            gc.collect()
    if raw_domains:
        raise AssertionError("D2--4 domains were not fully released")
    del raw_domains, d4
    gc.collect()

    with (ROOT / "dstar5_fragile.pkl").open("rb") as handle:
        d5 = pickle.load(handle)
    key_by_step = {}
    for raw_step in d5:
        vector = tuple(raw_step)
        if vector not in IDX:
            raise AssertionError("D5 step outside radius-two menu")
        step = IDX[vector]
        if step in key_by_step:
            raise AssertionError("duplicate D5 step after conversion")
        key_by_step[step] = raw_step
    if set(key_by_step) != fragile_steps:
        raise AssertionError("D5 and fragile D2--4 step sets differ")

    d5_words = 0
    for step in sorted(fragile_steps):
        raw_words = d5.pop(key_by_step[step])
        if not isinstance(raw_words, list):
            raw_words = list(raw_words)
        d5_words += len(raw_words)
        for index, word in enumerate(raw_words):
            raw_words[index] = tuple(IDX[tuple(vector)] for vector in word)
        base = fragile_bases.pop(step)
        raw_words[:0] = base
        del base
        process_step(step, raw_words, "sorted-D2-4-plus-appended-D5")
        processed.append(step)
        total_words += len(raw_words)
        del raw_words
        gc.collect()
    if d5 or fragile_bases:
        raise AssertionError("fragile effective domains were not fully released")
    if set(processed) != set(range(len(MENU))) or len(processed) != len(MENU):
        raise AssertionError("effective-domain processing set drift")
    if total_words != EXPECTED_EFFECTIVE_DOMAIN_WORDS:
        raise AssertionError("effective-domain word total drift")
    return {
        "D2-4_words": sum(d24_sizes.values()),
        "D5_appended_words": d5_words,
        "effective_domain_words": total_words,
        "fragile_steps": len(fragile_steps),
        "nonfragile_steps": len(MENU) - len(fragile_steps),
        "processing_order": processed,
        "processing_order_sha256": stable_hash(processed),
        "D2-4_surviving_steps": len(surviving),
        "D2-4_surviving_step_stream_sha256": stable_hash(surviving),
    }


def join_thresholds(barrier, threshold_by_step):
    barrier_by_step = {
        record["step"]: record for record in barrier["step_records"]
    }
    records = []
    classifications = Counter()
    for step in range(len(MENU)):
        threshold = threshold_by_step[step]
        h_interval = threshold["H_s_interval"]
        d_interval = barrier_by_step[step]["D_s_interval"]
        h_lower = Fraction(**h_interval["lower"])
        h_upper = Fraction(**h_interval["upper"])
        d_lower = Fraction(**d_interval["lower"])
        d_upper = Fraction(**d_interval["upper"])
        gap_lower = h_lower - d_upper
        gap_upper = h_upper - d_lower
        if gap_lower > 0:
            classification = "proved H_s > D_s on observed coarse graph"
        elif gap_upper <= 0:
            classification = "proved H_s <= D_s on observed coarse graph"
        else:
            classification = "interval unresolved"
        classifications[classification] += 1
        records.append({
            **threshold,
            "observed_outgoing_coarse_edges": barrier_by_step[step][
                "observed_outgoing_coarse_edges"
            ],
            "observed_terminal_assigned_zero": barrier_by_step[step][
                "observed_terminal_assigned_zero"
            ],
            "D_s_interval": d_interval,
            "H_s_minus_D_s_interval": interval_record(
                gap_lower, gap_upper
            ),
            "effectful_exterior_classification": classification,
        })
    return {
        "interpretation": (
            "H_s>D_s leaves a metric exterior in which an x-parallel line "
            "could both affect a candidate site and have a strictly expanding "
            "Bellman-adjusted offset. It does not prove that any old secant "
            "realizes that annulus. H_s<=D_s places the entire candidate-site "
            "effect region inside the noncontracting Bellman core for this "
            "observed coarse graph. Neither conclusion is universal."
        ),
        "classification_counts": dict(sorted(classifications.items())),
        "steps": records,
        "step_threshold_barrier_stream_sha256": stable_hash(records),
    }


def estimate(x_artifact_path):
    started = time.time()
    resource = enforce_resource_policy()
    inputs = observed_inputs(x_artifact_path)
    quadratic = verify_quadratic_identity()
    graph, model_by_step = validate_artifact_and_extract_graph(
        x_artifact_path
    )
    barrier = bellman_intervals(graph)
    return {
        "status": (
            "exact pinned-graph estimate and rigorous observed coarse Bellman "
            "barrier; connector-domain H_s thresholds not scanned"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "quadratic_form": quadratic,
        "observed_coarse_graph": graph,
        "observed_step_only_bellman_barrier": barrier,
        "planned_domain_scan": {
            "effective_step_domains": len(model_by_step),
            "effective_domain_words": sum(
                record["domain_words"] for record in model_by_step.values()
            ),
            "effective_domain_words_expected": EXPECTED_EFFECTIVE_DOMAIN_WORDS,
            "operation": (
                "reconstruct authoritative effective word order; enumerate "
                "interior sites only; validate word digest/site census; compute "
                "max exact lateral quadratic norm per step"
            ),
        },
        "proof_boundary": {
            "proved": [
                "the pinned graph records and phase classes agree exactly",
                "every extracted actual word, slot, prefix, and child step obeys the radius-two menu recurrence",
                "the reported rational intervals enclose the fixed point for arbitrary switching on the extracted observed step-only edges",
            ],
            "not_proved": [
                "that the observed step-only graph is a universal Post relation or transition congruence",
                "that observed-terminal step types have no unobserved successors",
                "any H_s threshold, effectful exterior, line realization, connector availability, or unconditional theorem",
            ],
        },
    }


def exact_run(x_artifact_path):
    started = time.time()
    resource = enforce_resource_policy()
    inputs = observed_inputs(x_artifact_path)
    quadratic = verify_quadratic_identity()
    graph, model_by_step = validate_artifact_and_extract_graph(
        x_artifact_path
    )
    barrier = bellman_intervals(graph)
    thresholds = {}

    def process_step(step, domain, layer):
        ordinal = len(thresholds) + 1
        print(
            f"x-axis barrier domain {ordinal}/{len(MENU)}: step {step}, "
            f"{len(domain)} words",
            flush=True,
        )
        if step in thresholds:
            raise AssertionError("effective step processed twice")
        thresholds[step] = scan_step_threshold(
            step, domain, layer, model_by_step[step]
        )

    domain_stream = stream_effective_domains(process_step)
    if set(thresholds) != set(range(len(MENU))):
        raise AssertionError("threshold scan did not cover every step")
    joined = join_thresholds(barrier, thresholds)
    return {
        "status": (
            "exact finite effective-domain x-axis candidate threshold and "
            "rigorous observed/coarse step-only Bellman-barrier experiment; "
            "not a universal tail quotient, transition congruence, availability "
            "bound, or unconditional theorem"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": {
            **resource,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "quadratic_form": quadratic,
        "observed_coarse_graph": graph,
        "observed_step_only_bellman_barrier": barrier,
        "effective_domain_stream": domain_stream,
        "threshold_barrier_comparison": joined,
        "proof_boundary": {
            "proved": [
                "all 124 effective domains were reconstructed in the authoritative order and matched the pinned x-axis word and site metadata",
                "each H_s is enclosed from its exact maximum rational squared lateral norm",
                "each D_s is enclosed for arbitrary switching on the finite extracted observed step-only edge graph",
                "every reported sign of H_s-D_s follows from disjoint outward rational intervals",
            ],
            "finite_evidence_only": [
                "the classification of candidate-site effect regions relative to barriers on this one observed coarse graph",
            ],
            "not_proved": [
                "transition congruence, alternate connector histories, L9 or later transitions, or a universal phase graph",
                "that any potential exterior annulus contains a realized old secant",
                "the endpoint-on-candidate-line channel, non-x directions, near-deep joins, or Boolean union availability",
                "a finite promoted core, uniform residual rank, safety fixed point, or unconditional theorem",
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
    for command in ("estimate", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument(
            "--x-artifact", type=Path, default=DEFAULT_X_ARTIFACT
        )
        subparser.add_argument(
            "--output",
            type=Path,
            default=(
                Path("/tmp/x-axis-bellman-barrier-estimate.json")
                if command == "estimate"
                else Path("/tmp/x-axis-bellman-barrier-canonical.json")
            ),
        )
    args = parser.parse_args()
    payload = (
        estimate(args.x_artifact)
        if args.command == "estimate"
        else exact_run(args.x_artifact)
    )
    atomic_write_json(args.output, payload)
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output.resolve()),
        "output_sha256": file_sha256(args.output.resolve()),
        "checker_sha256": payload["checker_sha256"],
        "elapsed_seconds": payload["resource_policy"]["elapsed_seconds"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
