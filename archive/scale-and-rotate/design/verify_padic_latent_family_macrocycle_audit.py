#!/usr/bin/env python3
"""Independent verifier for the focused fixed latent-family audit.

This verifier does not import either macrocycle explorer or the focused auditor.

Produced and signed by [OpenAI Codex].
"""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess


AUDITOR = "OpenAI Codex"
SIGNATURE = "[OpenAI Codex]"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "padic-latent-family-macrocycle-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "padic-latent-family-macrocycle-witness.json"
EXPECTED_SCHEMA = "padic-latent-family-macrocycle-audit/v1"
EXPECTED_WITNESS_SCHEMA = "padic-latent-family-macrocycle-witness/v1"

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
N = ((3, 0, 0), (0, -1, 3), (0, -3, 0))
H = (55, 34, 18)
P_NUMERATOR = (-99, -78, -62)
P_DENOMINATOR = 22
P = tuple(Fraction(value, P_DENOMINATOR) for value in P_NUMERATOR)
CONTROL = (-4, -4, -3)
PHASE_16_CONTROL = (0, 0, 0)
PHASE_16_PULLBACK = (165, -20, 102)
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)
CACHE_MAGIC = b"NOXLN001"
SELECTED_WORDS = {8: (0, 1, 16), 16: (8, 23, 24)}
METADATA_PATH = Path("/tmp/no-new-x-line-L5-canonical.json")
CACHE_PATH = Path("/tmp/no-new-x-line-domains.bin")
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


def primitive(vector):
    divisor = content(vector)
    if not divisor:
        raise AssertionError("zero direction")
    result = tuple(int(coordinate) // divisor for coordinate in vector)
    first = next(value for value in result if value)
    if first < 0:
        result = tuple(-value for value in result)
    return result, divisor


def q(direction):
    _x, y, z = direction
    return 3 * y * y - y * z + 3 * z * z


def v3(value):
    if value == 0:
        raise AssertionError("exceptional zero entered fixed family")
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
    return min(v3(direction[0]) // 2, (v3(q(direction)) - 1) // 4)


def stable_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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
            f"git {' '.join(arguments)} failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout


def history_records(pattern, revision):
    commits = git(
        "log", revision, "--reverse", "--format=%H", "-G" + pattern
    ).splitlines()
    records = []
    for commit in commits:
        metadata = git(
            "show", "-s", "--format=%aI%x1f%s", commit
        ).rstrip("\n")
        authored_at, subject = metadata.split("\x1f", 1)
        files = sorted(set(
            line
            for line in git(
                "show", "--format=", "--name-only", "-G" + pattern,
                commit, "--"
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


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_hashed(path, schema):
    with Path(path).open() as handle:
        value = json.load(handle)
    if value.get("schema") != schema:
        raise AssertionError("schema mismatch", str(path))
    claimed = value.get("payload_sha256")
    payload = dict(value)
    payload.pop("payload_sha256", None)
    if stable_hash(payload) != claimed:
        raise AssertionError("payload hash mismatch", str(path))
    return value, payload, claimed
def inverse_m(vector):
    x, y, z = vector
    return x / 3, (z - y / 3) / 3, -y / 3


def primitive_rational(vector):
    denominator = 1
    for coordinate in vector:
        denominator = math.lcm(denominator, Fraction(coordinate).denominator)
    integers = [int(Fraction(coordinate) * denominator) for coordinate in vector]
    divisor = 0
    for coordinate in integers:
        divisor = math.gcd(divisor, abs(coordinate))
    result = tuple(coordinate // divisor for coordinate in integers)
    first = next(coordinate for coordinate in result if coordinate)
    return tuple(-coordinate for coordinate in result) if first < 0 else result


def word_geometry(word):
    position = (0, 0, 0)
    interiors = []
    for slot, letter in enumerate(word):
        position = add(position, MENU[letter])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(interiors), position


def scan_candidate_sites():
    if file_sha256(METADATA_PATH) != EXPECTED_METADATA_SHA256:
        raise AssertionError("candidate metadata hash drift")
    if file_sha256(CACHE_PATH) != EXPECTED_CACHE_SHA256:
        raise AssertionError("candidate cache hash drift")
    with METADATA_PATH.open() as handle:
        metadata = json.load(handle)
    cache = CACHE_PATH.read_bytes()
    if not cache.startswith(CACHE_MAGIC):
        raise AssertionError("candidate cache magic drift")
    blocks = {
        block["step"]: block
        for block in metadata["compact_domain_cache"]["blocks"]
    }
    payload = {}
    selected_present = {}
    domain_words = 0
    cache_bytes = 0
    for step in (8, 16):
        block = blocks[step]
        cursor = block["start"]
        sites = set()
        found = False
        for _ in range(block["words"]):
            length = cache[cursor]
            cursor += 1
            word = tuple(cache[cursor:cursor + length])
            cursor += length
            interiors, endpoint = word_geometry(word)
            if endpoint != matrix_vector(M, MENU[step]):
                raise AssertionError("cached endpoint drift", step)
            sites.update(interiors)
            found = found or word == SELECTED_WORDS[step]
        if cursor != block["end"]:
            raise AssertionError("candidate cache block boundary drift", step)
        payload[str(step)] = [list(site) for site in sorted(sites)]
        selected_present[str(step)] = found
        domain_words += block["words"]
        cache_bytes += block["end"] - block["start"]
    return payload, selected_present, domain_words, cache_bytes


def quadratic_j(direction):
    x, y, z = map(Fraction, direction)
    return (3 * y * y - y * z + 3 * z * z) / (x * x)


def verify_candidate_frontier(summary, witness):
    replay = witness["candidate_frontier_replay"]
    site_payload = replay["candidate_sites"]
    if METADATA_PATH.exists() and CACHE_PATH.exists():
        observed = scan_candidate_sites()
        if site_payload != observed[0]:
            raise AssertionError("embedded candidate sites disagree with raw cache")
        if replay["selected_words_present_in_exact_domains"] != observed[1]:
            raise AssertionError("selected-word domain membership drift")
        if replay["domain_words"] != observed[2] or replay["cache_bytes"] != observed[3]:
            raise AssertionError("candidate scan extent drift")
    if stable_hash(site_payload) != replay["candidate_site_stream_sha256"]:
        raise AssertionError("candidate-site stream hash mismatch")
    if replay["candidate_sites_by_phase"] != {
        phase: len(sites) for phase, sites in site_payload.items()
    }:
        raise AssertionError("candidate-site count drift")

    target = quadratic_j(H)
    adjusted = []
    for phase_text in ("8", "16"):
        phase = int(phase_text)
        for site in site_payload[phase_text]:
            site_q = tuple(map(Fraction, site))
            ghost = (
                site_q
                if phase == 8
                else add(CONTROL, inverse_m(site_q))
            )
            direction = subtract(ghost, P)
            if quadratic_j(direction) == target:
                adjusted.append({
                    "phase": phase,
                    "site": site,
                    "ghost_in_phase_8_frame": [
                        [value.numerator, value.denominator] for value in ghost
                    ],
                    "primitive_direction_from_p": list(
                        primitive_rational(direction)
                    ),
                })
    if adjusted != replay["equal_invariant_frontier"]:
        raise AssertionError("equal-invariant frontier drift")
    if summary["candidate_frontier_replay"] != {
        key: value for key, value in replay.items() if key != "candidate_sites"
    }:
        raise AssertionError("summary/witness candidate replay mismatch")


def verify_direction_only_collision(summary, witness):
    collision = witness["direction_only_poison_collision"]
    direction = tuple(collision["direction"])
    reveal = collision["reveal_line"]
    translated = collision["parallel_translate"]
    if cross(tuple(reveal["base_point"]), direction) != tuple(reveal["moment"]):
        raise AssertionError("reveal-line moment drift")
    if cross(tuple(translated["base_point"]), direction) != tuple(
        translated["moment"]
    ):
        raise AssertionError("translated-line moment drift")
    residual = subtract(
        cross(tuple(reveal["base_point"]), direction),
        tuple(translated["moment"]),
    )
    if residual == (0, 0, 0) or list(residual) != translated["reveal_residual"]:
        raise AssertionError("direction-only poison collision drift")
    if summary["direction_only_poison_collision"] != collision:
        raise AssertionError("summary/witness poison collision mismatch")




def exact_family(n):
    direction = H
    for _ in range(n):
        direction = matrix_vector(N_SQUARED, direction)
    if primitive(direction) != (direction, 1):
        raise AssertionError("family primitivity drift", n)
    raw_moment = cross(P_NUMERATOR, direction)
    if any(value % P_DENOMINATOR for value in raw_moment):
        raise AssertionError("family moment integrality drift", n)
    moment = tuple(value // P_DENOMINATOR for value in raw_moment)
    return direction, moment


def one_step(direction, moment, control):
    raw_direction = matrix_vector(M, direction)
    next_direction, divisor = primitive(raw_direction)
    raw_moment = matrix_vector(COFACTOR_M, subtract(moment, cross(control, direction)))
    sign = 1 if next(value for value in raw_direction if value) > 0 else -1
    raw_moment = scale(sign, raw_moment)
    if any(value % divisor for value in raw_moment):
        raise AssertionError("moment normalization drift")
    return next_direction, tuple(value // divisor for value in raw_moment), divisor


def verify_family_witness(witness):
    records = witness["family_records_n0_through_n4"]
    if len(records) != 5:
        raise AssertionError("family record count drift")
    for n, record in enumerate(records):
        direction, moment = exact_family(n)
        expected = {
            "n": n,
            "direction": list(direction),
            "moment": list(moment),
            "x_v3": 2 * n,
            "q": q(direction),
            "q_v3": 4 * n + 1,
            "rank": n,
        }
        if record != expected:
            raise AssertionError("family record drift", n)

    phase_records = witness["two_phase_transition_records_n1_through_n4"]
    if len(phase_records) != 4:
        raise AssertionError("phase record count drift")
    phase_16_fixed = matrix_vector(M, subtract(P, CONTROL))
    for n, record in enumerate(phase_records, 1):
        direction, moment = exact_family(n)
        middle_direction, middle_moment, first_divisor = one_step(direction, moment, CONTROL)
        output_direction, output_moment, second_divisor = one_step(
            middle_direction, middle_moment, PHASE_16_CONTROL
        )
        expected_output = exact_family(n - 1)
        if (first_divisor, second_divisor) != (9, 9):
            raise AssertionError("phase divisor drift", n)
        if (output_direction, output_moment) != expected_output:
            raise AssertionError("macro output drift", n)
        if middle_moment != tuple(int(value) for value in cross(phase_16_fixed, middle_direction)):
            raise AssertionError("phase-16 moment drift", n)
        first = record["phase_8_to_16"]
        second = record["phase_16_to_8"]
        if (
            first["output_direction"] != list(middle_direction)
            or first["output_moment"] != list(middle_moment)
            or first["rank_before"] != n
            or first["rank_after"] != n - 1
            or first["rank_change"] != -1
        ):
            raise AssertionError("first phase record drift", n)
        if (
            second["output_direction"] != list(output_direction)
            or second["output_moment"] != list(output_moment)
            or second["rank_before"] != n - 1
            or second["rank_after"] != n - 1
            or second["rank_change"] != 0
            or second["terminal_reveal"] != (n == 1)
        ):
            raise AssertionError("second phase record drift", n)


def projective_state(direction, modulus):
    inverse = pow(direction[1] % modulus, -1, modulus)
    return direction[0] * inverse % modulus, direction[2] * inverse % modulus


def edge(x, z, modulus):
    unit = (-8 - 3 * z) % modulus
    inverse = pow(unit, -1, modulus)
    return 9 * x * inverse % modulus, (3 - 9 * z) * inverse % modulus


def contact_valuation(direction, projective, cap):
    return min(capped_v3(value, cap) for value in cross(direction, projective))


def graph_metrics(edges):
    indegree = [0] * len(edges)
    for target in edges:
        indegree[target] += 1
    distance = [None] * len(edges)
    cycles = []
    for start in range(len(edges)):
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
            split = position[current]
            cycle = path[split:]
            cycles.append(cycle)
            for vertex in cycle:
                distance[vertex] = 0
            prefix = path[:split]
        else:
            prefix = path
        for vertex in reversed(prefix):
            distance[vertex] = distance[edges[vertex]] + 1
    indegree_histogram = Counter(indegree)
    cycle_histogram = Counter(map(len, cycles))
    return {
        "image_states": len(set(edges)),
        "indegree_histogram": {
            str(key): indegree_histogram[key] for key in sorted(indegree_histogram)
        },
        "scc_count": len(edges) - sum(map(len, cycles)) + len(cycles),
        "recurrent_scc_count": len(cycles),
        "recurrent_scc_sizes": sorted(map(len, cycles)),
        "cycle_length_histogram": {
            str(key): cycle_histogram[key] for key in sorted(cycle_histogram)
        },
        "terminal_state_count": 0,
        "maximum_tail_edges_to_recurrent_scc": max(distance),
    }


def regenerate_precision(k):
    modulus = 3**k
    state_count = modulus * modulus
    edges = [0] * state_count
    digest = hashlib.sha256()
    contact_histogram = Counter()
    for x in range(modulus):
        for z in range(modulus):
            if (-8 - 3 * z) % 3 == 0:
                raise AssertionError("nonunit edge denominator", k, x, z)
            next_x, next_z = edge(x, z, modulus)
            edges[x * modulus + z] = next_x * modulus + next_z
            value_8 = contact_valuation(H, (x, 1, z), k)
            value_16 = contact_valuation(PHASE_16_PULLBACK, (x, 1, z), k)
            contact_histogram[(value_8, value_16)] += 1
            digest.update(struct.pack(">7I", k, x, z, next_x, next_z, value_8, value_16))
    fixed = [index for index, target in enumerate(edges) if index == target]
    return {
        "k": k,
        "modulus": modulus,
        "state_count": state_count,
        "edge_count": state_count,
        "state_edge_sha256": digest.hexdigest(),
        "fixed_states_xz": [[index // modulus, index % modulus] for index in fixed],
        "contact_valuation_pair_histogram": {
            f"{left},{right}": contact_histogram[(left, right)]
            for left, right in sorted(contact_histogram)
        },
        **graph_metrics(edges),
    }


def verify_graph(summary):
    records = summary["certificate_regeneration"]["precisions"]
    if [record["k"] for record in records] != list(range(1, 6)):
        raise AssertionError("precision range drift")
    for committed in records:
        regenerated = regenerate_precision(committed["k"])
        for key, value in regenerated.items():
            if committed[key] != value:
                raise AssertionError("precision metric drift", committed["k"], key)
        if committed["invalid_source_states"] or committed["invalid_edge_domains"]:
            raise AssertionError("invalid bounded graph state")
        if committed["outdegree_histogram"] != {"1": committed["state_count"]}:
            raise AssertionError("bounded graph successor omission")
    totals = summary["certificate_regeneration"]["totals"]
    if totals != {
        "disjoint_precision_graphs": 5,
        "states": 66_429,
        "edges": 66_429,
        "sccs": 66_429,
        "recurrent_sccs": 5,
        "terminal_states": 0,
        "maximum_tail_edges_to_recurrent_residue_scc": 3,
    }:
        raise AssertionError("aggregate graph metrics drift")


def verify_collision(summary, witness):
    collision = witness["finite_state_collision"]
    members = collision["members"]
    if [member["n"] for member in members] != [3, 4]:
        raise AssertionError("collision family indices drift")
    states = [
        projective_state(tuple(member["direction"]), collision["modulus"])
        for member in members
    ]
    if states[0] != states[1] or list(states[0]) != collision[
        "projective_state_xz_with_y_equal_1"
    ]:
        raise AssertionError("finite-residue collision drift")
    if [member["rank"] for member in members] != [3, 4]:
        raise AssertionError("collision rank distinction drift")
    if summary["abstraction_collision_witness"] != collision:
        raise AssertionError("summary/witness collision mismatch")


def verify_source_boundaries(summary):
    required = {
        "design/LATENT-REENTRY-OBSTRUCTION.md": (
            "F(L_n)=L_(n-1)",
            "The all-`n` silence assertion is exact",
            "An integer lattice line is not yet a secant of the realized path",
        ),
        "design/UNCONDITIONAL-INDUCTION-PLAN.md": (
            "66,429 projective state edges",
            "The useful outcome is algebraic, not the finite depth",
            "Its output is a conjecture generator for Gate C, not a proof certificate",
        ),
        "design/padic_macrocycle_lift.py": (
            "padic_depth = min(x_valuation // 2, (q_valuation - 1) // 4)",
            "The depth is regression coverage",
            "not a reachable-birth theorem or unconditional proof",
        ),
    }
    for path, phrases in required.items():
        text = (ROOT / path).read_text()
        for phrase in phrases:
            if phrase not in text:
                raise AssertionError("source boundary phrase missing", path, phrase)
    audited_head = summary["audited_head"]
    expected_history = {
        "family_definition": history_records(
            r"55, ?34, ?18|g_n=N|L_n=\{x|latent_padic_depth",
            audited_head,
        ),
        "macrocycle_references": history_records(
            r"66,429|latent family|latent re-entry|padic_macrocycle_lift|padic-macrocycle-lift",
            audited_head,
        ),
    }
    if summary["source_inventory"]["history"] != expected_history:
        raise AssertionError("source-history inventory drift")
    if summary["stop_condition"]["number"] != 2:
        raise AssertionError("wrong stop condition")
    if summary["supported_outcome"]["code"] != "F":
        raise AssertionError("wrong supported outcome")


def verify(summary_path, witness_path):
    summary_file, summary, summary_hash = load_hashed(summary_path, EXPECTED_SCHEMA)
    witness_file, witness, witness_hash = load_hashed(witness_path, EXPECTED_WITNESS_SCHEMA)
    if summary.get("auditor") != AUDITOR or witness.get("auditor") != AUDITOR:
        raise AssertionError("auditor signpost drift")
    if summary.get("signature") != SIGNATURE or witness.get("signature") != SIGNATURE:
        raise AssertionError("signature drift")
    if summary["witness"]["payload_sha256"] != witness_hash:
        raise AssertionError("summary does not commit to witness")
    producer = ROOT / summary["producer"]["path"]
    if file_sha256(producer) != summary["producer"]["sha256"]:
        raise AssertionError("focused auditor source hash mismatch")
    verify_family_witness(witness)
    verify_candidate_frontier(summary, witness)
    verify_direction_only_collision(summary, witness)
    verify_graph(summary)
    verify_collision(summary, witness)
    verify_source_boundaries(summary)
    if summary["certificate_regeneration"]["requested_rank_metrics"]["rank_change_histogram"] is not None:
        raise AssertionError("undefined residue-graph rank was fabricated")
    return {
        "auditor": AUDITOR,
        "status": "verified",
        "stop_condition": 2,
        "outcome": "F",
        "states": 66_429,
        "edges": 66_429,
        "precisions": 5,
        "recurrent_residue_sccs": 5,
        "maximum_tail_to_recurrent_residue_scc": 3,
        "candidate_sites": 428,
        "summary_payload_sha256": summary_hash,
        "witness_payload_sha256": witness_hash,
    }


A = matrix_product(M, M)
N_SQUARED = matrix_product(N, N)
COFACTOR_M = cofactor(M)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()
    print(json.dumps(verify(args.summary, args.witness), sort_keys=True))


if __name__ == "__main__":
    main()
