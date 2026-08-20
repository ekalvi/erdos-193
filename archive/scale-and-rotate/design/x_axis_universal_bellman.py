#!/usr/bin/env python3
"""Full-domain x-axis Bellman barrier and finite integer-core certificate.

For every word in all 124 effective connector domains and every ordered child
slot, this checker retains the exact coarse transport edge

    (source step, child step, lateral prefix control).

Edges are deduplicated only after the complete authoritative domain stream has
been scanned.  On this finite all-action edge graph it computes outward
rational intervals for

    D_s = max_(s -> t, c) (||c||_S + D_t/3),

where

    ||(y,z)||_S^2 = (36 y^2 - 12 y z + 36 z^2) / 35.

The upper Bellman vector U is independently checked to be postfixed.  Hence
for every retained edge and every x-line offset h>U_s,

    h_child - U_t >= 3 (h_parent - U_s) > 0.

This is a universal statement over every connector word in the pinned finite
domains for the fixed x-parallel carried-line channel.  It is deliberately an
arbitrary-switching step-only overapproximation: it does not assert that edge
choices from different words or slots can be combined into one realized
ordered path.

Because the minimum Euclidean eigenvalue of S is 6/7, each integer core

    {(y,z) in Z^2 : ||(y,z)||_S <= U_s}

is finite.  The checker enumerates it exactly, together with the Bellman
interval fringe and all candidate-site lateral classes.  This finite carried-
line theorem does not supply singleton endpoint occupancy, new-line births,
collision provenance, coexistence, connector availability, or transport between
unrelated chronological connector anchors.  Its offset transport is only the
synchronized parent-to-child transport of one carried line.

Run on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_universal_bellman.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_axis_universal_bellman.py run \
        --output /tmp/x-axis-universal-bellman-canonical.json
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import pickle
import sys
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BARRIER_ARTIFACT = Path(
    "/tmp/x-axis-bellman-barrier-canonical.json"
)
EXPECTED_BARRIER_ARTIFACT_SHA256 = (
    "f0a30cd341548539b9e0e3ecaa7cad57727e052f873f91649c0102c00c4262a9"
)
EXPECTED_BARRIER_CHECKER_SHA256 = (
    "c9cd69eb345c4bfab9355570fffe5b05a809b9e64ad05d243e0aaaac39fa5582"
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
    "design/x_axis_bellman_barrier.py": EXPECTED_BARRIER_CHECKER_SHA256,
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


def validate_inputs(barrier_path):
    commitments = {
        "observed_bellman_canonical_artifact": file_sha256(barrier_path)
    }
    if commitments["observed_bellman_canonical_artifact"] != (
        EXPECTED_BARRIER_ARTIFACT_SHA256
    ):
        raise RuntimeError("pinned observed Bellman artifact hash drift")
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        digest = file_sha256(ROOT / relative)
        if digest != expected:
            raise RuntimeError(
                f"input hash drift for {relative}: {digest} != {expected}"
            )
        commitments[relative] = digest
    return commitments


def load_reference_models(barrier_path):
    with barrier_path.open() as handle:
        barrier = json.load(handle)
    if barrier["checker_sha256"] != EXPECTED_BARRIER_CHECKER_SHA256:
        raise AssertionError("observed Bellman checker commitment drift")
    if barrier["effective_domain_stream"]["effective_domain_words"] != (
        EXPECTED_EFFECTIVE_DOMAIN_WORDS
    ):
        raise AssertionError("reference effective-domain total drift")
    models = barrier["threshold_barrier_comparison"]["steps"]
    model_by_step = {record["step"]: record for record in models}
    if len(model_by_step) != len(MENU) or set(model_by_step) != set(
        range(len(MENU))
    ):
        raise AssertionError("reference domain-model step set drift")
    return barrier, model_by_step


def scan_step(step, domain, layer, reference):
    expected_endpoint = apply_matrix(M_BAL3, MENU[step])
    word_digest = hashlib.sha256()
    edge_counts = Counter()
    sites = set()
    lateral_sites = set()
    maximum_word_length = 0
    slot_occurrences = 0

    for word_index, raw_word in enumerate(domain):
        word = tuple(raw_word)
        if not word or len(word) > 255:
            raise AssertionError("invalid connector word length")
        maximum_word_length = max(maximum_word_length, len(word))
        word_digest.update(len(word).to_bytes(1, "little"))
        position = (0, 0, 0)
        word_sites = []
        for slot, child_step in enumerate(word):
            if not 0 <= child_step < len(MENU):
                raise AssertionError("invalid menu index in connector word")
            word_digest.update(child_step.to_bytes(1, "little"))
            control = (position[1], position[2])
            edge_counts[(child_step, control[0], control[1])] += 1
            slot_occurrences += 1
            position = add(position, MENU[child_step])
            if slot + 1 < len(word):
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
            lateral_sites.add((site[1], site[2]))

    observed = {
        "step": step,
        "layer": layer,
        "domain_words": len(domain),
        "candidate_sites": len(sites),
        "candidate_lateral_site_classes": len(lateral_sites),
        "expected_scaled_parent_step": as_json(expected_endpoint),
        "word_order_sha256": word_digest.hexdigest(),
    }
    expected = {
        "step": reference["step"],
        "layer": reference["layer"],
        "domain_words": reference["domain_words"],
        "candidate_sites": reference["candidate_sites"],
        "candidate_lateral_site_classes": reference[
            "candidate_lateral_site_classes"
        ],
        "expected_scaled_parent_step": reference[
            "expected_scaled_parent_step"
        ],
        "word_order_sha256": reference["word_order_sha256"],
    }
    if observed != expected:
        raise AssertionError(
            "effective-domain reconstruction disagrees with pinned reference",
            observed, expected,
        )
    maximum_h_squared = max(
        (lateral_norm_squared(site) for site in lateral_sites),
        default=Fraction(0),
    )
    reference_h = reference["H_s_squared_exact"]
    if maximum_h_squared != rational(reference_h):
        raise AssertionError("candidate lateral threshold drift")
    edge_controls = {(y, z) for _target, y, z in edge_counts}
    if not lateral_sites <= edge_controls:
        raise AssertionError(
            "candidate site is not a next-slot prefix control",
            step, sorted(lateral_sites - edge_controls),
        )
    edges = [
        [step, target, y, z, occurrences]
        for (target, y, z), occurrences in sorted(edge_counts.items())
    ]
    return {
        **observed,
        "maximum_word_length": maximum_word_length,
        "slot_occurrences_before_deduplication": slot_occurrences,
        "unique_full_domain_edges": len(edges),
        "candidate_lateral_sites_are_edge_controls": True,
        "candidate_lateral_yz": as_json(sorted(lateral_sites)),
        "candidate_lateral_stream_sha256": stable_hash(sorted(lateral_sites)),
        "H_s_squared_exact": rational_record(maximum_h_squared),
        "edges": edges,
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


def solve_bellman(edges):
    outgoing = defaultdict(list)
    norm_intervals = {}
    maximum_b_upper = Fraction(0)
    for source, target, y, z, occurrences in edges:
        control = (y, z)
        if control not in norm_intervals:
            square = lateral_norm_squared(control)
            norm_intervals[control] = (
                square, *sqrt_fraction_interval(square)
            )
        square, lower, upper = norm_intervals[control]
        maximum_b_upper = max(maximum_b_upper, upper)
        outgoing[source].append({
            "target": target,
            "control": control,
            "occurrences": occurrences,
            "B_squared": square,
            "B_lower": lower,
            "B_upper": upper,
        })
    if set(outgoing) != set(range(len(MENU))):
        raise AssertionError("full-domain edge graph has a terminal step")

    lower_values = [Fraction(0) for _ in MENU]
    global_upper = Fraction(3, 2) * maximum_b_upper
    upper_values = [global_upper for _ in MENU]

    def apply(values, endpoint):
        result = []
        for step in range(len(MENU)):
            result.append(max(
                edge["B_lower" if endpoint == "lower" else "B_upper"]
                + values[edge["target"]] / 3
                for edge in outgoing[step]
            ))
        return result

    iterations = 0
    while iterations < BELLMAN_MAX_ITERATIONS:
        next_lower = apply(lower_values, "lower")
        next_upper = apply(upper_values, "upper")
        if any(a > b for a, b in zip(lower_values, next_lower)):
            raise AssertionError("lower Bellman iteration is not monotone")
        if any(a < b for a, b in zip(upper_values, next_upper)):
            raise AssertionError("upper Bellman iteration is not monotone")
        lower_values, upper_values = next_lower, next_upper
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
        raise AssertionError("lower vector is not pre-fixed")
    if any(update > upper for update, upper in zip(next_upper, upper_values)):
        raise AssertionError("upper vector is not postfixed")

    slack_digest = hashlib.sha256()
    minimum_slack = None
    minimum_slack_edge = None
    zero_slack_edges = 0
    for source in range(len(MENU)):
        for edge in outgoing[source]:
            slack = (
                upper_values[source] - edge["B_upper"]
                - upper_values[edge["target"]] / 3
            )
            if slack < 0:
                raise AssertionError("postfixed edge slack is negative")
            zero_slack_edges += slack == 0
            compact = (
                source, edge["target"], edge["control"],
                slack.numerator, slack.denominator,
            )
            slack_digest.update(stable_bytes(compact))
            slack_digest.update(b"\n")
            if minimum_slack is None or slack < minimum_slack:
                minimum_slack = slack
                minimum_slack_edge = {
                    "source_step": source,
                    "target_step": edge["target"],
                    "prefix_lateral_control": as_json(edge["control"]),
                    "postfixed_slack": rational_record(slack),
                }
    if minimum_slack is None:
        raise AssertionError("full-domain graph has no edge")

    step_records = []
    for step in range(len(MENU)):
        step_records.append({
            "step": step,
            "outgoing_unique_edges": len(outgoing[step]),
            "D_interval": interval_record(
                lower_values[step], upper_values[step]
            ),
            "certified_postfixed_upper_U": rational_record(
                upper_values[step]
            ),
        })
    norm_records = []
    for control, (square, lower, upper) in sorted(norm_intervals.items()):
        norm_records.append({
            "prefix_lateral_control": as_json(control),
            "norm_squared_exact": rational_record(square),
            "norm_interval": interval_record(lower, upper),
        })
    return {
        "outgoing": outgoing,
        "lower_values": lower_values,
        "upper_values": upper_values,
        "public": {
            "definition": (
                "D_s=max over every deduplicated full-domain step/slot edge "
                "(sqrt(B_squared)+D_target/3)"
            ),
            "arbitrary_switching_scope": (
                "all edges occur in at least one pinned effective-domain word; "
                "the graph does not preserve which edges belong to one word"
            ),
            "iterations": iterations,
            "sqrt_decimal_digits": SQRT_DECIMAL_DIGITS,
            "target_maximum_interval_width": rational_record(
                BELLMAN_WIDTH_TARGET
            ),
            "maximum_final_interval_width": rational_record(max(
                upper - lower
                for lower, upper in zip(lower_values, upper_values)
            )),
            "initial_global_postfixed_upper": rational_record(global_upper),
            "step_records": step_records,
            "barrier_stream_sha256": stable_hash(step_records),
            "unique_prefix_lateral_norms": len(norm_records),
            "prefix_lateral_norms": norm_records,
            "postfixed_edge_slack_stream_sha256": slack_digest.hexdigest(),
            "minimum_postfixed_edge_slack": rational_record(minimum_slack),
            "minimum_postfixed_edge_slack_witness": minimum_slack_edge,
            "zero_postfixed_slack_edges": zero_slack_edges,
            "all_edges_postfixed": True,
        },
    }


def enumerate_integer_cores(step_scans, bellman):
    lower_values = bellman["lower_values"]
    upper_values = bellman["upper_values"]
    outgoing = bellman["outgoing"]
    step_records = []
    total_inner = 0
    total_fringe = 0
    total_effectful = 0
    total_effectful_fringe = 0
    total_effectful_exterior = 0
    effect_transition_counts = Counter()
    maximum_coordinate_bound = 0

    for step in range(len(MENU)):
        lower = lower_values[step]
        upper = upper_values[step]
        radius_squared = Fraction(7, 6) * upper * upper
        coordinate_bound = math.isqrt(
            radius_squared.numerator // radius_squared.denominator
        )
        maximum_coordinate_bound = max(
            maximum_coordinate_bound, coordinate_bound
        )
        inner = []
        fringe = []
        for y in range(-coordinate_bound, coordinate_bound + 1):
            for z in range(-coordinate_bound, coordinate_bound + 1):
                square = lateral_norm_squared((y, z))
                if square <= lower * lower:
                    inner.append((y, z))
                elif square <= upper * upper:
                    fringe.append((y, z))
        outer = set(inner) | set(fringe)
        candidate_sites = {
            tuple(site) for site in step_scans[step]["candidate_lateral_yz"]
        }
        effect_inner = sorted(candidate_sites & set(inner))
        effect_fringe = sorted(candidate_sites & set(fringe))
        effect_exterior = sorted(candidate_sites - outer)
        if not candidate_sites <= {
            (edge["control"][0], edge["control"][1])
            for edge in outgoing[step]
        }:
            raise AssertionError("candidate site/control coverage drift")

        # Classify every full-domain edge on every finite effectful offset.
        per_step_transitions = Counter()
        for source_z in sorted(candidate_sites):
            source_shell = (
                "inner" if source_z in set(inner)
                else "fringe" if source_z in set(fringe)
                else "exterior"
            )
            for edge in outgoing[step]:
                target_z = lateral_transport(source_z, edge["control"])
                target = edge["target"]
                target_square = lateral_norm_squared(target_z)
                if target_square <= lower_values[target] ** 2:
                    target_shell = "inner"
                elif target_square <= upper_values[target] ** 2:
                    target_shell = "fringe"
                else:
                    target_shell = "exterior"
                per_step_transitions[
                    source_shell + "->" + target_shell
                ] += 1
        effect_transition_counts.update(per_step_transitions)

        total_inner += len(inner)
        total_fringe += len(fringe)
        total_effectful += len(candidate_sites)
        total_effectful_fringe += len(effect_fringe)
        total_effectful_exterior += len(effect_exterior)
        step_records.append({
            "step": step,
            "coordinate_box_bound": coordinate_bound,
            "inner_core_integer_yz": as_json(inner),
            "bellman_interval_fringe_integer_yz": as_json(fringe),
            "outer_promoted_core_count": len(inner) + len(fringe),
            "candidate_effectful_lateral_classes": len(candidate_sites),
            "effectful_inner_core_yz": as_json(effect_inner),
            "effectful_bellman_fringe_yz": as_json(effect_fringe),
            "effectful_exterior_yz": as_json(effect_exterior),
            "effectful_state_edge_transition_counts": dict(sorted(
                per_step_transitions.items()
            )),
        })
    return {
        "quadratic_finiteness_theorem": (
            "S has minimum Euclidean eigenvalue 6/7; therefore h(z)<=U "
            "implies y^2+z^2<=(7/6)U^2 and the integer core is finite"
        ),
        "core_definition": (
            "inner uses the Bellman lower interval endpoint; the promoted "
            "outer core adds every integer point up to the certified postfixed "
            "upper endpoint; their difference is the interval fringe"
        ),
        "total_inner_core_integer_states": total_inner,
        "total_bellman_interval_fringe_integer_states": total_fringe,
        "total_outer_promoted_integer_states": total_inner + total_fringe,
        "maximum_coordinate_box_bound": maximum_coordinate_bound,
        "total_candidate_effectful_lateral_classes": total_effectful,
        "total_effectful_bellman_fringe_states": total_effectful_fringe,
        "total_effectful_exterior_states": total_effectful_exterior,
        "effectful_state_edge_transition_counts": dict(sorted(
            effect_transition_counts.items()
        )),
        "step_records": step_records,
        "integer_core_stream_sha256": stable_hash(step_records),
    }


def estimate(barrier_path):
    resource = enforce_resource_policy()
    inputs = validate_inputs(barrier_path)
    barrier, model_by_step = load_reference_models(barrier_path)
    total_words = sum(record["domain_words"] for record in model_by_step.values())
    if total_words != EXPECTED_EFFECTIVE_DOMAIN_WORDS:
        raise AssertionError("reference model word total drift")
    return {
        "status": (
            "pinned structural estimate for the full-domain x-axis Bellman "
            "scan; no connector words or universal edges scanned"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": resource,
        "planned_scan": {
            "effective_step_domains": len(model_by_step),
            "effective_domain_words": total_words,
            "per_step_memory": (
                "one effective word list, one deduplicated edge Counter, and "
                "finite candidate-site sets; released before the next step"
            ),
            "edge_schema": (
                "source step, child step, exact lateral prefix control, and "
                "number of word/slot occurrences"
            ),
            "post_scan": (
                "rigorous interval Bellman solve, exact integer-core "
                "enumeration, and candidate-effect transition classification"
            ),
        },
        "proof_boundary": {
            "not_yet_computed": [
                "the full-domain edge set, universal barrier, integer core, or effectful exterior/fringe"
            ]
        },
        "reference_observed_barrier_raw_sha256": (
            EXPECTED_BARRIER_ARTIFACT_SHA256
        ),
        "reference_observed_barrier_status": barrier["status"],
    }


def exact_run(barrier_path):
    resource = enforce_resource_policy()
    inputs = validate_inputs(barrier_path)
    _barrier, model_by_step = load_reference_models(barrier_path)
    step_scans = {}
    all_edges = []

    def process_step(step, domain, layer):
        ordinal = len(step_scans) + 1
        print(
            f"universal x-axis domain {ordinal}/{len(MENU)}: step {step}, "
            f"{len(domain)} words",
            flush=True,
        )
        if step in step_scans:
            raise AssertionError("effective step processed twice")
        record = scan_step(step, domain, layer, model_by_step[step])
        all_edges.extend(record.pop("edges"))
        step_scans[step] = record

    domain_stream = stream_effective_domains(process_step)
    if set(step_scans) != set(range(len(MENU))):
        raise AssertionError("domain scan did not cover every step")
    all_edges.sort()
    if len(all_edges) != len({tuple(edge[:4]) for edge in all_edges}):
        raise AssertionError("full-domain edge deduplication failed")
    if sum(record["domain_words"] for record in step_scans.values()) != (
        EXPECTED_EFFECTIVE_DOMAIN_WORDS
    ):
        raise AssertionError("scanned domain word total drift")

    bellman = solve_bellman(all_edges)
    integer_core = enumerate_integer_cores(step_scans, bellman)
    scan_records = [step_scans[step] for step in range(len(MENU))]
    if integer_core["total_effectful_exterior_states"] != 0:
        raise AssertionError(
            "a candidate effect lies outside the universal postfixed core"
        )
    return {
        "status": (
            "exact full-effective-domain arbitrary-switching x-axis Bellman "
            "barrier and finite integer carried-line core; not singleton "
            "occupancy, birth/coexistence closure, connector availability, or "
            "an unconditional theorem"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": inputs,
        "resource_policy": resource,
        "scope": {
            "effective_domain_words_scanned": EXPECTED_EFFECTIVE_DOMAIN_WORDS,
            "source_steps": len(MENU),
            "edge": (
                "one source step, one child step, and the exact lateral prefix "
                "control before that ordered child slot"
            ),
            "switching": (
                "arbitrary switching among every deduplicated edge witnessed "
                "by at least one full effective-domain word"
            ),
            "channel": "carried x-parallel old--old--new candidate-site line",
        },
        "effective_domain_stream": domain_stream,
        "domain_step_scans": scan_records,
        "domain_scan_stream_sha256": stable_hash(scan_records),
        "full_domain_edge_census": {
            "unique_edges": len(all_edges),
            "word_slot_occurrences_before_deduplication": sum(
                record["slot_occurrences_before_deduplication"]
                for record in scan_records
            ),
            "maximum_connector_word_length": max(
                record["maximum_word_length"] for record in scan_records
            ),
            "edge_record_schema": [
                "source_step", "child_step", "prefix_y", "prefix_z",
                "word_slot_occurrences",
            ],
            "edge_stream_sha256": stable_hash(all_edges),
            "edges": all_edges,
        },
        "universal_step_only_bellman": bellman["public"],
        "finite_integer_core": integer_core,
        "proved_carried_line_theorem": {
            "statement": (
                "for every pinned effective-domain connector word, every "
                "ordered child slot, and every integer x-line offset exterior "
                "to the certified postfixed core, the child offset remains "
                "exterior and its Bellman-adjusted distance expands by at least 3"
            ),
            "ingredients": [
                "B^T S B = 9S",
                "every full-domain word/slot prefix edge is retained",
                "the reported rational upper vector is postfixed on every edge",
                "the fixed-direction integer core is finite by the 6/7 eigenvalue bound",
            ],
        },
        "missing_for_a_universal_safety_automaton": [
            "singleton endpoint occupancy and exact insertion-driven x-line births",
            "axial collision data or a separately exact collision frontier",
            "action-level correlation tying all child slots to one selected connector word",
            "honest coexistence of promoted endpoint and line states on one realized ordered path",
            "chronological transfer between unrelated connector anchors; the checked "
            "transport follows one synchronized carried line only",
            "non-x secants, endpoint-on-candidate-line poison, availability, and a greatest safety fixed point",
        ],
        "proof_boundary": {
            "proved": [
                "the complete finite effective-domain edge graph and its exact edge-occurrence census",
                "a rigorous postfixed Bellman barrier for arbitrary switching on that graph",
                "universal exterior invariance for the carried x-line channel",
                "exact finiteness and enumeration of the postfixed integer x-core",
                "the exact candidate-effectful core/fringe/exterior census",
            ],
            "not_proved": [
                "that arbitrary edge switching preserves one connector word or one realized path",
                "new-line birth closure, endpoint occupancy, or availability-grade coexistence",
                "control of a far line when the realized stitch cursor jumps to an unrelated anchor",
                "a complete far-secant tail lemma or unconditional theorem",
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
            "--barrier-artifact", type=Path,
            default=DEFAULT_BARRIER_ARTIFACT,
        )
        subparser.add_argument(
            "--output", type=Path,
            default=(
                Path("/tmp/x-axis-universal-bellman-estimate.json")
                if command == "estimate"
                else Path("/tmp/x-axis-universal-bellman-canonical.json")
            ),
        )
    args = parser.parse_args()
    started = time.time()
    payload = (
        estimate(args.barrier_artifact)
        if args.command == "estimate"
        else exact_run(args.barrier_artifact)
    )
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
