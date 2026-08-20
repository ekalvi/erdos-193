#!/usr/bin/env python3
"""Focused exact audit of the fixed 8 -> 16 -> 8 latent line family.

The audit deliberately stops at requested STOP CONDITION 2: the 66,429 edges
are five bounded projective residue graphs, not an inductive line-token or
countdown certificate.  It does not enumerate broad reachable secants.

Produced and signed by [OpenAI Codex].
"""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import tempfile


SCHEMA = "padic-latent-family-macrocycle-audit/v1"
WITNESS_SCHEMA = "padic-latent-family-macrocycle-witness/v1"
AUDITOR = "OpenAI Codex"
SIGNATURE = "[OpenAI Codex]"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "padic-latent-family-macrocycle-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "padic-latent-family-macrocycle-witness.json"
ORIGINAL_CERTIFICATE = ROOT / "design" / "padic-macrocycle-lift-summary.json"
KNOWN_TEMPLATE_CERTIFICATE = ROOT / "design" / "known-template-weighted-birth-probe-summary.json"

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
N = (
    (3, 0, 0),
    (0, -1, 3),
    (0, -3, 0),
)
H = (55, 34, 18)
P_NUMERATOR = (-99, -78, -62)
P_DENOMINATOR = 22
P = tuple(Fraction(value, P_DENOMINATOR) for value in P_NUMERATOR)
CONTROL_8_TO_16 = (-4, -4, -3)
CONTROL_16_TO_8 = (0, 0, 0)
REVEAL = (-2, -2, -2)
PULLBACK_PHASE_16_DIRECTION = (165, -20, 102)
SELECTED_WORD_8 = (0, 1, 16)
SELECTED_WORD_16 = (8, 23, 24)
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)
CACHE_MAGIC = b"NOXLN001"
POLICY_PATH = Path("/tmp/nonx-fixed-word-policy-probe-v2.json")
METADATA_PATH = Path("/tmp/no-new-x-line-L5-canonical.json")
CACHE_PATH = Path("/tmp/no-new-x-line-domains.bin")
EXPECTED_POLICY_SHA256 = "e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e"
EXPECTED_METADATA_SHA256 = "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
EXPECTED_CACHE_SHA256 = "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"


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


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def cofactor(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return (
        (e * i - f * h, f * g - d * i, d * h - e * g),
        (c * h - b * i, a * i - c * g, b * g - a * h),
        (b * f - c * e, c * d - a * f, a * e - b * d),
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def content(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(int(coordinate)))
    return divisor


def canonical_primitive_with_sign(vector):
    divisor = content(vector)
    if divisor == 0:
        raise ValueError("zero direction")
    primitive = tuple(int(coordinate) // divisor for coordinate in vector)
    first = next(coordinate for coordinate in primitive if coordinate)
    sign = -1 if first < 0 else 1
    return scale(sign, primitive), divisor, sign


def q(direction):
    _x, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def exact_v3(value):
    if value == 0:
        raise ValueError("v3(0) is infinite and excluded from this implemented rank")
    value = abs(value)
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def capped_v3(value, cap):
    if value == 0:
        return cap
    value = abs(value)
    valuation = 0
    while valuation < cap and value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def rank(direction):
    x_valuation = exact_v3(direction[0])
    q_valuation = exact_v3(q(direction))
    return min(x_valuation // 2, (q_valuation - 1) // 4)


def family_direction(n):
    if n < 0:
        raise ValueError("negative family index")
    direction = H
    for _ in range(n):
        direction = matrix_vector(N_SQUARED, direction)
    primitive, divisor, sign = canonical_primitive_with_sign(direction)
    if primitive != direction or divisor != 1 or sign != 1:
        raise AssertionError("family direction lost canonical primitivity", n)
    return direction


def moment_at(base_point, direction):
    value = cross(base_point, direction)
    if any(coordinate.denominator != 1 for coordinate in value):
        raise AssertionError("nonintegral family moment", direction, value)
    return tuple(int(coordinate) for coordinate in value)


def family_moment(n):
    return moment_at(P, family_direction(n))


def line_transition(direction, moment, control):
    raw_direction = matrix_vector(M, direction)
    primitive, divisor, sign = canonical_primitive_with_sign(raw_direction)
    raw_moment = matrix_vector(
        COFACTOR_M,
        subtract(moment, cross(control, direction)),
    )
    signed_moment = scale(sign, raw_moment)
    if any(coordinate % divisor for coordinate in signed_moment):
        raise AssertionError("Pluecker moment cannot follow primitive normalization")
    normalized_moment = tuple(coordinate // divisor for coordinate in signed_moment)
    if sum(primitive[index] * normalized_moment[index] for index in range(3)):
        raise AssertionError("normalized Pluecker orthogonality drift")
    return primitive, normalized_moment, divisor, sign, raw_direction, raw_moment


def vector_record(vector):
    result = []
    for coordinate in vector:
        coordinate = Fraction(coordinate)
        result.append([coordinate.numerator, coordinate.denominator])
    return result
def inverse_m(vector):
    x, y, z = vector
    return (
        x / 3,
        (z - y / 3) / 3,
        -y / 3,
    )


def primitive_rational(vector):
    denominator = 1
    for coordinate in vector:
        denominator = math.lcm(denominator, Fraction(coordinate).denominator)
    integers = [int(Fraction(coordinate) * denominator) for coordinate in vector]
    divisor = 0
    for coordinate in integers:
        divisor = math.gcd(divisor, abs(coordinate))
    primitive = tuple(coordinate // divisor for coordinate in integers)
    first = next(coordinate for coordinate in primitive if coordinate)
    return scale(-1, primitive) if first < 0 else primitive


def word_geometry(word):
    position = (0, 0, 0)
    interiors = []
    for slot, letter in enumerate(word):
        position = add(position, MENU[letter])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(interiors), position


def quadratic_j(direction):
    x, y, z = map(Fraction, direction)
    if x == 0:
        raise AssertionError("J requested on x=0 candidate direction")
    return (3 * y * y - y * z + 3 * z * z) / (x * x)


def candidate_frontier_replay():
    if file_sha256(METADATA_PATH) != EXPECTED_METADATA_SHA256:
        raise AssertionError("candidate metadata hash drift")
    if file_sha256(CACHE_PATH) != EXPECTED_CACHE_SHA256:
        raise AssertionError("compact candidate cache hash drift")
    with METADATA_PATH.open() as handle:
        metadata = json.load(handle)
    cache = CACHE_PATH.read_bytes()
    if not cache.startswith(CACHE_MAGIC):
        raise AssertionError("compact candidate cache magic drift")
    blocks = {
        block["step"]: block
        for block in metadata["compact_domain_cache"]["blocks"]
    }
    sites = {}
    selected_present = {}
    domain_words = 0
    cache_bytes = 0
    for step, selected_word in (
        (8, SELECTED_WORD_8),
        (16, SELECTED_WORD_16),
    ):
        block = blocks[step]
        cursor = block["start"]
        union = set()
        found = False
        for _ in range(block["words"]):
            length = cache[cursor]
            cursor += 1
            word = tuple(cache[cursor:cursor + length])
            cursor += length
            interiors, endpoint = word_geometry(word)
            if endpoint != matrix_vector(M, MENU[step]):
                raise AssertionError("cached endpoint drift", step, word)
            union.update(interiors)
            found = found or word == selected_word
        if cursor != block["end"]:
            raise AssertionError("candidate cache block boundary drift", step)
        sites[step] = tuple(sorted(union))
        selected_present[str(step)] = found
        domain_words += block["words"]
        cache_bytes += block["end"] - block["start"]
    if {step: len(values) for step, values in sites.items()} != {8: 214, 16: 214}:
        raise AssertionError("candidate-site census drift")
    if not all(selected_present.values()):
        raise AssertionError("selected macrocycle word absent from exact domain")

    site_payload = {
        str(step): [list(site) for site in sites[step]]
        for step in sorted(sites)
    }
    site_digest = stable_hash(site_payload)
    adjusted = []
    target_j = quadratic_j(H)
    for phase in (8, 16):
        for site in sites[phase]:
            site_q = tuple(map(Fraction, site))
            ghost = (
                site_q
                if phase == 8
                else add(CONTROL_8_TO_16, inverse_m(site_q))
            )
            direction = subtract(ghost, P)
            if quadratic_j(direction) == target_j:
                adjusted.append({
                    "phase": phase,
                    "site": list(site),
                    "ghost_in_phase_8_frame": vector_record(ghost),
                    "primitive_direction_from_p": list(
                        primitive_rational(direction)
                    ),
                })
    expected = [
        {
            "phase": 8,
            "site": [-2, -2, -2],
            "ghost_in_phase_8_frame": [[-2, 1], [-2, 1], [-2, 1]],
            "primitive_direction_from_p": [55, 34, 18],
        },
        {
            "phase": 16,
            "site": [-4, 1, 2],
            "ghost_in_phase_8_frame": [[-16, 3], [-31, 9], [-10, 3]],
            "primitive_direction_from_p": [165, -20, 102],
        },
    ]
    if adjusted != expected:
        raise AssertionError("equal-J candidate frontier drift", adjusted)
    return {
        "classification": "EXACT FINITE",
        "metadata_sha256": EXPECTED_METADATA_SHA256,
        "cache_sha256": EXPECTED_CACHE_SHA256,
        "expected_policy_sha256": EXPECTED_POLICY_SHA256,
        "available_policy_sha256": (
            file_sha256(POLICY_PATH) if POLICY_PATH.exists() else None
        ),
        "policy_pin_matches": (
            POLICY_PATH.exists()
            and file_sha256(POLICY_PATH) == EXPECTED_POLICY_SHA256
        ),
        "domain_words": domain_words,
        "cache_bytes": cache_bytes,
        "candidate_sites_by_phase": {
            str(step): len(sites[step]) for step in sorted(sites)
        },
        "selected_words_present_in_exact_domains": selected_present,
        "candidate_site_stream_sha256": site_digest,
        "candidate_sites": site_payload,
        "family_projective_invariant": [
            target_j.numerator,
            target_j.denominator,
        ],
        "equal_invariant_frontier": adjusted,
    }


def direction_only_poison_collision():
    direction = H
    reveal_moment = moment_at(tuple(map(Fraction, REVEAL)), direction)
    translated_base = (-1, -2, -2)
    translated_moment = moment_at(
        tuple(map(Fraction, translated_base)), direction
    )
    reveal_residual = subtract(cross(REVEAL, direction), translated_moment)
    if reveal_residual == (0, 0, 0):
        raise AssertionError("parallel translate unexpectedly hits reveal")
    return {
        "classification": "PROVED",
        "direction": list(direction),
        "reveal_line": {
            "base_point": list(REVEAL),
            "moment": list(reveal_moment),
            "hits_reveal": True,
        },
        "parallel_translate": {
            "base_point": list(translated_base),
            "moment": list(translated_moment),
            "reveal_residual": list(reveal_residual),
            "hits_reveal": False,
        },
        "conclusion": (
            "equal direction and rank do not determine affine poison effect; "
            "the Pluecker moment is required"
        ),
    }


def family_record(n):
    direction = family_direction(n)
    q_value = q(direction)
    return {
        "n": n,
        "direction": list(direction),
        "moment": list(family_moment(n)),
        "x_v3": exact_v3(direction[0]),
        "q": q_value,
        "q_v3": exact_v3(q_value),
        "rank": rank(direction),
    }


def phase_transition_record(n):
    if n < 1:
        raise ValueError("the selected phase-8 word is already killed at n=0")
    input_direction = family_direction(n)
    input_moment = family_moment(n)
    middle = line_transition(input_direction, input_moment, CONTROL_8_TO_16)
    middle_direction, middle_moment, first_divisor, first_sign, raw_first, raw_mu_first = middle
    expected_middle = H
    for _ in range(2 * n - 1):
        expected_middle = matrix_vector(N, expected_middle)
    if middle_direction != expected_middle:
        raise AssertionError("phase-16 direction formula drift", n)
    if middle_moment != moment_at(PHASE_16_FIXED_POINT, middle_direction):
        raise AssertionError("phase-16 moment formula drift", n)

    output = line_transition(middle_direction, middle_moment, CONTROL_16_TO_8)
    output_direction, output_moment, second_divisor, second_sign, raw_second, raw_mu_second = output
    if output_direction != family_direction(n - 1) or output_moment != family_moment(n - 1):
        raise AssertionError("macrocycle output drift", n)
    if (first_divisor, second_divisor, first_sign, second_sign) != (9, 9, 1, 1):
        raise AssertionError("latent normalization branch drift", n)

    terminal = n == 1
    return {
        "n": n,
        "phase_8_input": {
            "phase": 8,
            "selected_word": list(SELECTED_WORD_8),
            "slot_0_based": 2,
            "control": list(CONTROL_8_TO_16),
            "direction": list(input_direction),
            "moment": list(input_moment),
            "mask": "empty",
            "effect": "silent",
            "rank": rank(input_direction),
        },
        "phase_8_to_16": {
            "raw_direction": list(raw_first),
            "raw_moment": list(raw_mu_first),
            "primitive_divisor": first_divisor,
            "canonical_sign": first_sign,
            "output_phase": 16,
            "output_direction": list(middle_direction),
            "output_moment": list(middle_moment),
            "output_mask": "empty",
            "output_effect": "silent",
            "rank_before": rank(input_direction),
            "rank_after": rank(middle_direction),
            "rank_change": rank(middle_direction) - rank(input_direction),
        },
        "phase_16_to_8": {
            "selected_word": list(SELECTED_WORD_16),
            "slot_0_based": 0,
            "control": list(CONTROL_16_TO_8),
            "raw_direction": list(raw_second),
            "raw_moment": list(raw_mu_second),
            "primitive_divisor": second_divisor,
            "canonical_sign": second_sign,
            "output_phase": 8,
            "output_direction": list(output_direction),
            "output_moment": list(output_moment),
            "output_mask": [list(REVEAL)] if terminal else "empty",
            "output_effect": "kills selected phase-8 word" if terminal else "silent",
            "rank_before": rank(middle_direction),
            "rank_after": rank(output_direction),
            "rank_change": rank(output_direction) - rank(middle_direction),
            "terminal_reveal": terminal,
        },
    }


def projective_state(direction, modulus):
    if direction[1] % 3 == 0:
        raise ValueError("direction lies outside y-unit chart")
    inverse = pow(direction[1] % modulus, -1, modulus)
    return (
        direction[0] * inverse % modulus,
        direction[2] * inverse % modulus,
    )


def inverse_edge(x, z, modulus):
    unit = (-8 - 3 * z) % modulus
    inverse = pow(unit, -1, modulus)
    return (
        9 * x * inverse % modulus,
        (3 - 9 * z) * inverse % modulus,
    )


def contact_valuation(direction, projective, cap):
    return min(capped_v3(value, cap) for value in cross(direction, projective))


def functional_metrics(edges):
    state_count = len(edges)
    indegree = [0] * state_count
    for target in edges:
        indegree[target] += 1

    distance = [None] * state_count
    cycles = []
    for start in range(state_count):
        if distance[start] is not None:
            continue
        path = []
        position = {}
        current = start
        while distance[current] is None and current not in position:
            position[current] = len(path)
            path.append(current)
            current = edges[current]
        if current in position:
            cycle_start = position[current]
            cycle = path[cycle_start:]
            cycles.append(cycle)
            for vertex in cycle:
                distance[vertex] = 0
            prefix = path[:cycle_start]
        else:
            prefix = path
        for vertex in reversed(prefix):
            distance[vertex] = distance[edges[vertex]] + 1

    cycle_histogram = Counter(len(cycle) for cycle in cycles)
    indegree_histogram = Counter(indegree)
    scc_count = state_count - sum(map(len, cycles)) + len(cycles)
    return {
        "image_states": len(set(edges)),
        "indegree_histogram": {
            str(key): indegree_histogram[key] for key in sorted(indegree_histogram)
        },
        "scc_count": scc_count,
        "recurrent_scc_count": len(cycles),
        "recurrent_scc_sizes": sorted(map(len, cycles)),
        "cycle_length_histogram": {
            str(key): cycle_histogram[key] for key in sorted(cycle_histogram)
        },
        "terminal_state_count": 0,
        "maximum_tail_edges_to_recurrent_scc": max(distance),
    }


def precision_record(k):
    modulus = 3**k
    state_count = modulus * modulus
    edges = [0] * state_count
    digest = hashlib.sha256()
    invalid_sources = 0
    invalid_domains = 0
    contact_histogram = Counter()
    for x in range(modulus):
        for z in range(modulus):
            if math.gcd(1, modulus) != 1:
                invalid_sources += 1
            unit = (-8 - 3 * z) % modulus
            if unit % 3 == 0:
                invalid_domains += 1
            next_x, next_z = inverse_edge(x, z, modulus)
            source = x * modulus + z
            target = next_x * modulus + next_z
            edges[source] = target
            value_8 = contact_valuation(H, (x, 1, z), k)
            value_16 = contact_valuation(PULLBACK_PHASE_16_DIRECTION, (x, 1, z), k)
            contact_histogram[(value_8, value_16)] += 1
            digest.update(struct.pack(">7I", k, x, z, next_x, next_z, value_8, value_16))
    metrics = functional_metrics(edges)
    fixed = [index for index, target in enumerate(edges) if index == target]
    return {
        "k": k,
        "modulus": modulus,
        "state_schema": "(x,z) representing the projective direction [x:1:z] modulo 3^k",
        "edge_schema": "(x,z) -> (9x/u,(3-9z)/u), u=-8-3z",
        "state_count": state_count,
        "edge_count": state_count,
        "invalid_source_states": invalid_sources,
        "invalid_edge_domains": invalid_domains,
        "outdegree_histogram": {"1": state_count},
        "state_edge_sha256": digest.hexdigest(),
        "fixed_states_xz": [[index // modulus, index % modulus] for index in fixed],
        "contact_valuation_pair_histogram": {
            f"{left},{right}": contact_histogram[(left, right)]
            for left, right in sorted(contact_histogram)
        },
        **metrics,
    }


def stable_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_hashed_payload(path):
    with Path(path).open() as handle:
        value = json.load(handle)
    claimed = value.get("payload_sha256")
    mathematical = dict(value)
    mathematical.pop("payload_sha256", None)
    if stable_hash(mathematical) != claimed:
        raise AssertionError("committed payload hash mismatch", str(path))
    return value
def load_json(path):
    with Path(path).open() as handle:
        return json.load(handle)




def git(*arguments):
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(
            f"git {' '.join(arguments)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def history_records(pattern):
    commits = git("log", "--all", "--reverse", "--format=%H", "-G" + pattern).splitlines()
    records = []
    for commit in commits:
        metadata = git("show", "-s", "--format=%aI%x1f%s", commit).rstrip("\n")
        authored_at, subject = metadata.split("\x1f", 1)
        files = sorted(set(
            line
            for line in git(
                "show", "--format=", "--name-only", "-G" + pattern, commit, "--"
            ).splitlines()
            if line
        ))
        records.append({
            "commit": commit,
            "authored_at": authored_at,
            "subject": subject,
            "files": files,
        })
    return records


def source_inventory():
    return {
        "history": {
            "family_definition": history_records(
                r"55, ?34, ?18|g_n=N|L_n=\\{x|latent_padic_depth"
            ),
            "macrocycle_references": history_records(
                r"66,429|latent family|latent re-entry|padic_macrocycle_lift|padic-macrocycle-lift"
            ),
        },
        "defining_sources": [
            {
                "path": "design/LATENT-REENTRY-OBSTRUCTION.md",
                "lines": "35-99,101-203",
                "role": "line-token transition, exact all-n family, masks, scope boundary",
            },
            {
                "path": "design/nonx_latent_reentry_certificate.py",
                "lines": "265-339,349-500,526-659",
                "symbols": [
                    "selected_policy_cycle",
                    "candidate_sites",
                    "affine_cycle_and_frontier",
                    "arithmetic_certificate",
                    "run",
                ],
                "role": "primary exact all-n geometric certificate and 64-depth replay",
            },
            {
                "path": "design/nonx-latent-reentry-certificate-summary.json",
                "lines": "1-125",
                "role": "committed compact all-n certificate summary",
            },
            {
                "path": "design/padic_macrocycle_lift.py",
                "lines": "115-121,186-228,260-395,398-481,484-583,634-756",
                "symbols": [
                    "canonical_primitive",
                    "normalization_certificate",
                    "inverse_lift_edge",
                    "functional_graph_stats",
                    "compute_precision",
                    "contact_model_certificate",
                    "integer_line_moment",
                    "latent_positive_control",
                    "run",
                ],
                "classes": ["TimeBudgetExpired"],
                "role": "bounded residue explorer plus depth-16 positive-control regression",
            },
            {
                "path": "design/verify_padic_macrocycle_lift.py",
                "lines": "95-102,151-226,229-368,371-482",
                "symbols": [
                    "canonical_primitive",
                    "normalization_data",
                    "edge",
                    "graph_stats",
                    "verify_precision",
                    "latent_record_stream",
                    "verify_contact_model",
                    "verify",
                ],
                "role": "independent bounded-certificate verifier",
            },
            {
                "path": "design/padic-macrocycle-lift-summary.json",
                "lines": "1-520",
                "role": "66,429-edge bounded payload and depth-16 record commitment",
            },
        ],
        "finite_reachability_use": [
            {
                "path": "design/known_template_weighted_birth_probe.py",
                "lines": "1-31,324-338,795-969",
                "role": "complete requested-template scan on pinned L5-L8 paths",
            },
            {
                "path": "design/known-template-weighted-birth-probe-summary.json",
                "lines": "101-205",
                "role": "exact finite zero-live-family result on L5-L8",
            },
        ],
        "proof_plans_and_exposition": [
            "CONDITIONAL-THEOREM.md",
            "README.md",
            "REPORT.md",
            "design/FAR-SECANT-BIRTH-OPERATOR.md",
            "design/FAR-SECANT-RANK-LEMMA.md",
            "design/ORDERED-PATH-SAFETY-GATE.md",
            "design/UNCONDITIONAL-INDUCTION-PLAN.md",
            "design/PADIC-REACHABLE-SECANT-DEPTH-AUDIT.md",
            "design/padic_reachable_secant_depth_audit.py",
            "design/verify_padic_reachable_secant_depth_audit.py",
            "design/padic-reachable-secant-depth-audit-summary.json",
            "design/padic-reachable-secant-depth-witness.json",
        ],
        "incidental_direction_uses": [
            "design/lattice_t_projective_spectrum_census.py",
            "design/lattice_t_projective_spectrum_diagnostic.py",
            "design/lattice_t_l5_cone_guard_audit.py",
            "design/lattice_t_l6_cone_birth_guard.py",
            "design/lattice_t_l6_cone_guard_audit.py",
            "design/lattice_t_l6_cone_guard_pin_report.py",
            "design/audit_guarded_l5_to_l6.py",
            "design/guarded_l5_l6_common.py",
        ],
    }


def build_witness():
    family = [family_record(n) for n in range(5)]
    phases = [phase_transition_record(n) for n in range(1, 5)]
    modulus = 3**5
    collision_members = [family_record(3), family_record(4)]
    collision_states = [
        list(projective_state(tuple(member["direction"]), modulus))
        for member in collision_members
    ]
    if collision_states[0] != collision_states[1]:
        raise AssertionError("expected finite-residue collision disappeared")
    return {
        "schema": WITNESS_SCHEMA,
        "auditor": AUDITOR,
        "signature": SIGNATURE,
        "family_records_n0_through_n4": family,
        "two_phase_transition_records_n1_through_n4": phases,
        "candidate_frontier_replay": candidate_frontier_replay(),
        "direction_only_poison_collision": direction_only_poison_collision(),
        "finite_state_collision": {
            "classification": "PROVED",
            "k": 5,
            "modulus": modulus,
            "projective_state_xz_with_y_equal_1": collision_states[0],
            "members": collision_members,
            "conclusion": (
                "g_3 and g_4 have the same projective state modulo 3^5 but "
                "exact ranks 3 and 4, different moments, and different reveal times."
            ),
        },
    }


def build_summary(witness):
    original = load_hashed_payload(ORIGINAL_CERTIFICATE)
    known = load_json(KNOWN_TEMPLATE_CERTIFICATE)
    precisions = [precision_record(k) for k in range(1, 6)]
    total_edges = sum(record["edge_count"] for record in precisions)
    if total_edges != 66_429:
        raise AssertionError("edge total drift")
    original_by_k = {record["k"]: record for record in original["precisions"]}
    for record in precisions:
        expected = original_by_k[record["k"]]
        if record["state_edge_sha256"] != expected["state_edge_sha256"]:
            raise AssertionError("independent edge digest mismatch", record["k"])

    targeted_levels = known["finite_scan"]["latent_L_n"]["levels"]
    return {
        "schema": SCHEMA,
        "auditor": AUDITOR,
        "signature": SIGNATURE,
        "audited_head": git("rev-parse", "HEAD").strip(),
        "status": "STOP CONDITION 2",
        "source_inventory": source_inventory(),
        "family_definition": {
            "phase_8_member": (
                "for n>=0, L_n={x in Q^3:x cross g_n=mu_n}, "
                "g_n=N^(2n)H and mu_n=p cross g_n"
            ),
            "constants": {
                "H": list(H),
                "p": vector_record(P),
                "N": [list(row) for row in N],
                "phase_8_selected_word": list(SELECTED_WORD_8),
                "phase_16_selected_word": list(SELECTED_WORD_16),
            },
            "phase_16_member": (
                "for n>=1, direction d_n=N^(2n-1)H and moment "
                "nu_n=M(p-c) cross d_n after the first selected slot"
            ),
            "state_variables_required_by_fixed_cycle": {
                "phase": "8 or 16",
                "family_index": "n>=0 at phase 8; n>=1 indexes the incoming macrocycle",
                "direction": "exact canonical primitive integer g",
                "moment": "exact integer Pluecker moment in the corridor-centred frame",
                "cursor": "fixed to steps 8 and 16",
                "selected_word_and_slot": "fixed to (8,[0,1,16],slot2) and (16,[8,23,24],slot0)",
                "current_mask": "derived from phase and exact token",
                "owner_address_shell_provenance_occupancy": "not represented",
            },
            "canonicalization": (
                "divide by gcd of all direction coordinates; choose the sign "
                "whose first nonzero coordinate is positive; apply the same sign/divisor to mu"
            ),
            "moment_normalization": (
                "mu=p cross g, integral because g_n has a period-five orbit modulo 22 "
                "and P_NUMERATOR cross g_n is divisible by 22"
            ),
            "membership": {
                "mathematical_family": "exact countable orbit under the two fixed actions",
                "as_reachable_secants": "unproved underapproximation; no member is proved reachable",
                "covered_channels": ["already-born carried lines", "silent n>=1 members", "effectful terminal n=0"],
                "excluded_channels": [
                    "newborn lines",
                    "cursor imports",
                    "near-far and far-far joins",
                    "alternate connector choices",
                    "owner/address changes",
                    "whole-word and occupancy correlations",
                ],
            },
        },
        "rank_derivation": {
            "implemented_formula": "R(g)=min(v3(g_x)//2,(v3(q(g))-1)//4)",
            "base": "v3(H_x)=0 and v3(q(H))=1",
            "inverse_macro": "g_n=N^(2n)H, with x multiplied by 9 and q multiplied by 81",
            "family_valuations": "v3((g_n)_x)=2n and v3(q(g_n))=4n+1",
            "conclusion": "R(g_n)=n",
            "x_divisor_two": "one inverse macrocycle adds 2 to v3(g_x)",
            "q_offset_one": "the seed H has v3(q(H))=1",
            "q_divisor_four": "one inverse macrocycle adds 4 to v3(q)",
            "floors": (
                "they align the phase-8 parity (2n,4n+1) and intermediate phase-16 "
                "parity (2n-1,4n-1); they are not a general depth theorem"
            ),
            "domain": (
                "the implementation calls exact_v3 and is defined only when g_x and q(g) "
                "are nonzero; its asserted depth law is only the displayed orbit and intermediate phases"
            ),
            "zero_handling": "g_x=0 or q(g)=0 raises ValueError; no infinity/promotion branch exists",
            "representation": (
                "direction-only after canonical primitive normalization; not invariant under arbitrary scaling"
            ),
            "line_token_requirement": (
                "R uses only g, but mu, phase, fixed control, and mask theorem are required "
                "to infer silence or reveal time"
            ),
        },
        "macrocycle_theorem": {
            "phase_8_to_16": (
                "for n>=1, (g_n,mu_n) maps with primitive divisor 9 to "
                "(N^(2n-1)H, M(p-c) cross N^(2n-1)H); R drops from n to n-1"
            ),
            "phase_16_to_8": (
                "the intermediate token maps with primitive divisor 9 to "
                "(g_(n-1),mu_(n-1)); R remains n-1"
            ),
            "macro_rank_law": "R(next macro-boundary)=R(current)-1 for every n>=1",
            "mask_law": (
                "both phases are silent for incoming n>=1; the phase-8 output remains silent "
                "when n>1 and has the singleton reveal site (-2,-2,-2) when n=1"
            ),
            "terminal": (
                "L_0 already kills the selected phase-8 word, so the fixed legal continuation "
                "has no n=0 transition"
            ),
            "extra_operation": (
                "each M carriage multiplies the raw direction, then canonical line normalization "
                "divides direction and moment by content 9; over two slots the divisor is 81. "
                "This projective normalization, not unnormalized carriage, consumes the formula."
            ),
            "exceptions": [
                "n=0 is effectful terminal rather than a silent input",
                "tokens outside this exact orbit have no proved rank law",
                "alternate actions and imports are outside the theorem",
            ],
        },
        "certificate_regeneration": {
            "classification": "EXACT FINITE",
            "original_payload_sha256": original["payload_sha256"],
            "original_explorer_sha256": original["explorer"]["sha256"],
            "precisions": precisions,
            "totals": {
                "disjoint_precision_graphs": len(precisions),
                "states": total_edges,
                "edges": total_edges,
                "sccs": sum(record["scc_count"] for record in precisions),
                "recurrent_sccs": sum(record["recurrent_scc_count"] for record in precisions),
                "terminal_states": 0,
                "maximum_tail_edges_to_recurrent_residue_scc": max(
                    record["maximum_tail_edges_to_recurrent_scc"] for record in precisions
                ),
            },
            "per_edge_audit": {
                "source_state_validity": "all states are valid y-unit projective residues",
                "map_domain_validity": "u=-8-3z is a unit for every state",
                "exact_line_token_transition": "NOT REPRESENTED: mu is absent",
                "integer_primitive_normalization": "NOT REPRESENTED: normalization is projective y=1 modulo 3^k",
                "rank_transition": "NOT REPRESENTED: exact valuations and family index collapse",
                "poison_effect_transition": "NOT REPRESENTED",
                "terminal_or_promoted_classification": "NOT REPRESENTED",
                "successor_completeness": (
                    "complete only for the deterministic inverse projective map; no construction-channel closure claim"
                ),
            },
            "requested_rank_metrics": {
                "minimum_rank": None,
                "maximum_rank": None,
                "rank_change_histogram": None,
                "zero_decrease_edges": None,
                "increasing_edges": None,
                "minimum_countdown_slack": None,
                "maximum_path_before_termination_or_promotion": None,
                "reason": "rank, terminal, and promotion fields are absent from residue states",
                "family_inverse_orbit_rank_change": "+1 before finite-residue collapse",
            },
            "depth_16_scope": {
                "classification": "EXACT FINITE regression",
                "records": 17,
                "indices": "n=0 through n=16",
                "not_induction": True,
                "separate_all_n_result": (
                    "the all-n family theorem is symbolic in LATENT-REENTRY-OBSTRUCTION.md "
                    "and nonx_latent_reentry_certificate.py; it is not supplied by these 66,429 edges"
                ),
            },
        },
        "candidate_frontier_replay": {
            key: value
            for key, value in witness["candidate_frontier_replay"].items()
            if key != "candidate_sites"
        },
        "direction_only_poison_collision": witness[
            "direction_only_poison_collision"
        ],
        "abstraction_collision_witness": witness["finite_state_collision"],
        "existing_targeted_reachable_evidence": {
            "classification": "EXACT FINITE",
            "source": "design/known-template-weighted-birth-probe-summary.json:146-195",
            "method": known["finite_scan"]["method"],
            "levels": targeted_levels,
            "all_tested_live_secant_counts_are_zero": known["finite_scan"]["latent_L_n"][
                "all_tested_live_secant_counts_are_zero"
            ],
            "scope": (
                "complete only for requested L_n translations in pinned realized L5-L8 paths; "
                "no new guarded L5-L6 instrumentation was run after STOP CONDITION 2"
            ),
        },
        "stop_condition": {
            "number": 2,
            "classification": "PROVED",
            "statement": (
                "the 66,429-edge result is five bounded projective residue experiments, "
                "and the depth-16 stream is a finite regression, not an inductive certificate"
            ),
            "source_admission": "design/UNCONDITIONAL-INDUCTION-PLAN.md:5-30,350-363",
            "consequence": (
                "closure, promotion, targeted chronology instrumentation, and recurrent-witness "
                "search were not started"
            ),
        },
        "supported_outcome": {
            "code": "F",
            "label": "INSUFFICIENT ABSTRACTION",
            "classification": "PROVED for the proposed certificate",
            "statement": (
                "the residue direction graph cannot be a promoted safety class; exact fixed-cycle "
                "transport needs mu and phase, while reachable closure additionally needs causal "
                "owner/address, occupancy, whole-word, birth, and import state"
            ),
        },
        "next_lemma": {
            "classification": "CONJECTURED",
            "name": "reachable translated-L_n exclusion",
            "quantified_statement": (
                "For every level ell>=0, every globally legal ordered-path prefix S at level ell, "
                "every step-8 corridor anchor r in S, every integer n>=1, and every two distinct "
                "placed endpoints a,b in S, it is not the case that canonical_primitive(b-a)=g_n "
                "and (a-r) cross g_n=p cross g_n, where g_n=N^(2n)(55,34,18) and "
                "p=(-9/2,-39/11,-31/11)."
            ),
            "effect_if_proved": (
                "no translated silent member can be born or imported as a reachable secant, "
                "so this family needs exclusion rather than finite promotion"
            ),
        },
        "claim_ledger": [
            {"id": "C1", "classification": "PROVED", "claim": "The exact L_n family is an all-n integer-line orbit under two fixed actions."},
            {"id": "C2", "classification": "PROVED", "claim": "The implemented weighted valuation formula equals n on phase-8 family members."},
            {"id": "C3", "classification": "PROVED", "claim": "The two-slot primitive Pluecker macrotransition sends n to n-1 for n>=1."},
            {"id": "C4", "classification": "PROVED", "claim": "The rank drops on the first normalized slot and is unchanged on the second."},
            {"id": "C5", "classification": "EXACT FINITE", "claim": "All 66,429 projective residue edges through 3^5 were independently regenerated."},
            {"id": "C6", "classification": "REFUTED", "claim": "The 66,429 edges form an inductive line-token countdown certificate."},
            {"id": "C7", "classification": "EXACT FINITE", "claim": "The committed depth-16 check is a 17-record regression only."},
            {"id": "C8", "classification": "EXACT FINITE", "claim": "No translated L_n member is a live secant in the complete pinned L5-L8 template scan."},
            {"id": "C9", "classification": "CONJECTURED", "claim": "No translated L_n member is reachable at any level or alternate legal history."},
            {"id": "C10", "classification": "REFUTED", "claim": "Direction residue alone preserves moment, poison, terminal, rank, and whole-word behavior."},
            {"id": "C11", "classification": "MEASURED", "claim": "No new broad or targeted chronology measurement was performed after the stop condition."},
        ],
        "producer": {
            "path": "design/padic_latent_family_macrocycle_audit.py",
            "sha256": file_sha256(Path(__file__).resolve()),
        },
        "witness": {
            "path": "design/padic-latent-family-macrocycle-witness.json",
            "payload_sha256": stable_hash(witness),
        },
    }


def atomic_json_dump(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()
    witness = build_witness()
    summary = build_summary(witness)
    witness_with_hash = dict(witness)
    witness_with_hash["payload_sha256"] = stable_hash(witness)
    summary_with_hash = dict(summary)
    summary_with_hash["payload_sha256"] = stable_hash(summary)
    atomic_json_dump(witness_with_hash, args.witness)
    atomic_json_dump(summary_with_hash, args.summary)
    print(json.dumps({
        "auditor": AUDITOR,
        "status": summary["status"],
        "stop_condition": summary["stop_condition"]["number"],
        "states": summary["certificate_regeneration"]["totals"]["states"],
        "edges": summary["certificate_regeneration"]["totals"]["edges"],
        "summary": str(args.summary),
        "summary_payload_sha256": summary_with_hash["payload_sha256"],
        "witness": str(args.witness),
        "witness_payload_sha256": witness_with_hash["payload_sha256"],
    }, sort_keys=True))


A = matrix_product(M, M)
N_SQUARED = matrix_product(N, N)
COFACTOR_M = cofactor(M)
PHASE_16_FIXED_POINT = matrix_vector(M, subtract(P, CONTROL_8_TO_16))


if __name__ == "__main__":
    main()
