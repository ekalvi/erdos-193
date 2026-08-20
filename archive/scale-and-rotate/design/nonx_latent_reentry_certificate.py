#!/usr/bin/env python3
"""Exact latent re-entry obstruction for the height-two fixed-word policy.

This checker reads only two compact-domain blocks (steps 8 and 16).  It
certifies an infinite family of integer lattice lines which has empty direct
candidate-site mask for an arbitrarily long traversal of one repeatable phase
cycle, and then hits an interior of the selected step-8 word exactly at the
prescribed return.  The result is about the geometric carried-line channel.
It does not prove that the lines are born as secants in reachable globally
legal ordered-path histories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import resource
import tempfile
import time
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = Path("/tmp/nonx-fixed-word-policy-probe-v2.json")
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_OUTPUT = Path("/tmp/nonx-latent-reentry-certificate.json")

EXPECTED_POLICY_SHA256 = (
    "e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e"
)
EXPECTED_POLICY_CHECKER_SHA256 = (
    "531ba6ee0bfa8d5bf7485d70b13687ace4e1b100cdcdfd739b8bdcac9d8efdd3"
)
EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
CACHE_MAGIC = b"NOXLN001"

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

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
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add(left, right):
    return tuple(left[i] + right[i] for i in range(3))


def subtract(left, right):
    return tuple(left[i] - right[i] for i in range(3))


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
            sum(left[row][k] * right[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def transpose(matrix):
    return tuple(tuple(matrix[j][i] for j in range(len(matrix))) for i in range(len(matrix[0])))


def determinant_3(matrix):
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


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
        denominator = math.lcm(denominator, coordinate.denominator)
    integers = [int(coordinate * denominator) for coordinate in vector]
    divisor = 0
    for coordinate in integers:
        divisor = math.gcd(divisor, abs(coordinate))
    primitive = tuple(coordinate // divisor for coordinate in integers)
    first = next(coordinate for coordinate in primitive if coordinate)
    if first < 0:
        primitive = scale(-1, primitive)
    return primitive


def extended_gcd(left, right):
    """Return (g,s,t) with g>0 and s*left+t*right=g."""
    old_r, r = abs(left), abs(right)
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return (
        old_r,
        old_s if left >= 0 else -old_s,
        old_t if right >= 0 else -old_t,
    )


def integer_point_on_line(direction, moment):
    """Construct x in Z^3 with x cross direction=moment.

    The implementation uses that the first coordinate is nonzero and that a
    primitive direction makes gcd(g_x,g_y) coprime to g_z.  This is also an
    independent finite-run check of the saturated-cross-map argument.
    """
    a, b, c = direction
    u, v, w = moment
    if a == 0 or any(not isinstance(value, int) for value in moment):
        raise AssertionError("integer-point constructor precondition failed")
    divisor, coefficient_a, coefficient_b = extended_gcd(a, b)
    if w % divisor:
        raise AssertionError("third moment coordinate is not divisible by gcd(a,b)")
    x1 = coefficient_b * (w // divisor)
    x2 = -coefficient_a * (w // divisor)
    reduced_a = a // divisor
    rhs = -(v + c * x1)
    if rhs % reduced_a:
        raise AssertionError("orthogonality congruence failed before reduction")
    if divisor == 1:
        parameter = 0
    else:
        parameter = (rhs // reduced_a) * pow(c, -1, divisor) % divisor
    x1 += reduced_a * parameter
    x2 += (b // divisor) * parameter
    numerator = v + c * x1
    if numerator % a:
        raise AssertionError("integer-point congruence solve failed")
    x3 = numerator // a
    point = (x1, x2, x3)
    if cross(point, direction) != moment:
        raise AssertionError("constructed point misses the line", point, direction, moment)
    return point


def fraction_record(value):
    return [value.numerator, value.denominator]


def vector_record(vector):
    return [fraction_record(coordinate) for coordinate in vector]


def resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError("all numerical thread controls must equal one", observed)
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice < 15:
        raise RuntimeError("process nice value must be at least 15", nice)
    return {"thread_environment": observed, "process_nice": nice}


def verify_inputs(policy_path, metadata_path, cache_path):
    observed = {
        "fixed_policy_artifact": file_sha256(policy_path),
        "fixed_policy_checker": file_sha256(
            ROOT / "design" / "nonx_fixed_word_policy_probe.py"
        ),
        "metadata": file_sha256(metadata_path),
        "compact_domain_cache": file_sha256(cache_path),
    }
    expected = {
        "fixed_policy_artifact": EXPECTED_POLICY_SHA256,
        "fixed_policy_checker": EXPECTED_POLICY_CHECKER_SHA256,
        "metadata": EXPECTED_METADATA_SHA256,
        "compact_domain_cache": EXPECTED_CACHE_SHA256,
    }
    if observed != expected:
        raise AssertionError("pinned input drift", expected, observed)
    return observed


def word_geometry(word):
    position = (0, 0, 0)
    prefixes = []
    interiors = []
    for slot, letter in enumerate(word):
        prefixes.append(position)
        position = add(position, MENU[letter])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(prefixes), tuple(interiors), position


def selected_policy_cycle(policy):
    if policy["checker"]["sha256"] != EXPECTED_POLICY_CHECKER_SHA256:
        raise AssertionError("embedded fixed-policy checker digest drift")
    graph = policy["policy_graph"]
    potential = graph["strict_vertex_potential"]
    if not graph["acyclic"] or potential["maximum"] != 2:
        raise AssertionError("fixed policy no longer has its height-two potential")
    if not potential["strictly_decreases_on_every_edge"]:
        raise AssertionError("fixed-policy potential is not strict")

    records = {record["step"]: record for record in policy["fixed_policy"]["records"]}
    result = {}
    for step, expected_word in ((8, (0, 1, 16)), (16, (8, 23, 24))):
        record = records[step]
        word = tuple(record["word"])
        if word != expected_word:
            raise AssertionError("selected cycle word drift", step, word)
        prefixes, interiors, endpoint = word_geometry(word)
        if endpoint != matrix_vector(M, MENU[step]):
            raise AssertionError("selected word endpoint drift", step)
        if tuple(map(tuple, record["interiors"])) != interiors:
            raise AssertionError("stored selected interiors drift", step)
        result[step] = {
            "word": word,
            "prefixes": prefixes,
            "interiors": interiors,
        }

    first = result[8]
    second = result[16]
    if first["word"][2] != 16 or second["word"][0] != 8:
        raise AssertionError("phase cycle labels drift")
    c_first = first["prefixes"][2]
    c_second = second["prefixes"][0]
    if c_first != (-4, -4, -3) or c_second != (0, 0, 0):
        raise AssertionError("phase cycle controls drift", c_first, c_second)
    return result, c_first, c_second, potential


def candidate_sites(metadata, cache_path, steps=(8, 16)):
    blocks = {
        block["step"]: block
        for block in metadata["compact_domain_cache"]["blocks"]
    }
    sites = {}
    scanned_words = 0
    scanned_bytes = 0
    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact-domain cache magic drift")
            for step in steps:
                block = blocks[step]
                cursor = block["start"]
                union = set()
                for _ in range(block["words"]):
                    length = cache[cursor]
                    cursor += 1
                    word = tuple(cache[cursor:cursor + length])
                    cursor += length
                    _, interiors, endpoint = word_geometry(word)
                    if endpoint != matrix_vector(M, MENU[step]):
                        raise AssertionError("cached endpoint drift", step)
                    union.update(interiors)
                if cursor != block["end"]:
                    raise AssertionError("cache block boundary drift", step)
                sites[step] = tuple(sorted(union))
                scanned_words += block["words"]
                scanned_bytes += block["end"] - block["start"]
        finally:
            cache.close()
    if {step: len(values) for step, values in sites.items()} != {8: 214, 16: 214}:
        raise AssertionError("candidate-site census drift")
    return sites, scanned_words, scanned_bytes


def quadratic_j(direction):
    r, y, z = direction
    if r == 0:
        raise AssertionError("J requested on axial-zero direction")
    return Fraction(3 * y * y - y * z + 3 * z * z) / Fraction(r * r)


def affine_cycle_and_frontier(policy_cycle, control, sites):
    a_matrix = matrix_product(M, M)
    b = scale(-1, matrix_vector(a_matrix, control))
    p = (Fraction(-9, 2), Fraction(-39, 11), Fraction(-31, 11))
    if add(matrix_vector(a_matrix, p), b) != p:
        raise AssertionError("claimed affine-cycle fixed point drift")

    reveal = tuple(map(Fraction, policy_cycle[8]["interiors"][0]))
    h_fractional = scale(22, subtract(reveal, p))
    if any(coordinate.denominator != 1 for coordinate in h_fractional):
        raise AssertionError("reveal direction did not clear at denominator 22")
    h = tuple(int(coordinate) for coordinate in h_fractional)
    if h != (55, 34, 18) or math.gcd(math.gcd(*map(abs, h[:2])), abs(h[2])) != 1:
        raise AssertionError("primitive reveal direction drift", h)
    target_j = quadratic_j(h)
    if target_j != Fraction(348, 275):
        raise AssertionError("reveal invariant drift", target_j)

    adjusted = []
    for phase in (8, 16):
        for site in sites[phase]:
            site_q = tuple(map(Fraction, site))
            ghost = site_q if phase == 8 else add(control, inverse_m(site_q))
            direction = subtract(ghost, p)
            if direction[0] == 0:
                raise AssertionError("unexpected r=0 phase-adjusted candidate", phase, site)
            invariant = quadratic_j(direction)
            if invariant == target_j:
                adjusted.append({
                    "phase": phase,
                    "site": list(site),
                    "ghost_in_step_8_frame": vector_record(ghost),
                    "primitive_direction_from_p": list(primitive_rational(direction)),
                })

    expected = [
        {
            "phase": 8,
            "site": [-2, -2, -2],
            "ghost_in_step_8_frame": [[-2, 1], [-2, 1], [-2, 1]],
            "primitive_direction_from_p": [55, 34, 18],
        },
        {
            "phase": 16,
            "site": [-4, 1, 2],
            "ghost_in_step_8_frame": [[-16, 3], [-31, 9], [-10, 3]],
            "primitive_direction_from_p": [165, -20, 102],
        },
    ]
    if adjusted != expected:
        raise AssertionError("equal-J frontier drift", adjusted)

    return {
        "A": a_matrix,
        "b": b,
        "p": p,
        "reveal": reveal,
        "h": h,
        "J": target_j,
        "equal_j_frontier": adjusted,
    }


def arithmetic_certificate(frontier, sites, control):
    n2 = matrix_product(N, N)
    if determinant_3(N) != 27:
        raise AssertionError("det(N) drift")
    if matrix_product(matrix_product(M, M), n2) != (
        (81, 0, 0),
        (0, 81, 0),
        (0, 0, 81),
    ):
        raise AssertionError("M^2 N^2 identity drift")

    # This is the exact quadratic identity behind J invariance.
    lateral_b = ((0, -3), (3, -1))
    lateral_h = ((6, -1), (-1, 6))
    if matrix_product_2(
        matrix_product_2(transpose(lateral_b), lateral_h), lateral_b
    ) != scale_matrix_2(9, lateral_h):
        raise AssertionError("lateral quadratic identity drift")

    p = frontier["p"]
    p_numerator = tuple(int(22 * coordinate) for coordinate in p)
    h = frontier["h"]
    if p_numerator != (-99, -78, -62):
        raise AssertionError("fixed point numerator drift")
    if h[1] % 3 == 0:
        raise AssertionError("primitive induction seed lost")

    # N^2 has a period-five orbit on h modulo 22.  Every residue has
    # P cross g == 0 mod 22, so p cross g_n is integral for all n.
    expected_residues = (
        (11, 12, 18),
        (11, 4, 6),
        (11, 16, 2),
        (11, 20, 8),
        (11, 14, 10),
    )
    residues = []
    residue = tuple(coordinate % 22 for coordinate in h)
    while residue not in residues:
        residues.append(residue)
        residue = tuple(coordinate % 22 for coordinate in matrix_vector(n2, residue))
    if tuple(residues) != expected_residues or residue != expected_residues[0]:
        raise AssertionError("mod-22 direction orbit drift", residues, residue)
    for residue in residues:
        if any(coordinate % 22 for coordinate in cross(p_numerator, residue)):
            raise AssertionError("nonintegral Pluecker residue", residue)

    # Independent direct arithmetic replay.  It is a cross-check, not the
    # source of the all-n conclusion, which follows from J and the x-coordinate.
    phase_ghosts = {}
    for phase in (8, 16):
        phase_ghosts[phase] = tuple(
            tuple(map(Fraction, site))
            if phase == 8
            else add(control, inverse_m(tuple(map(Fraction, site))))
            for site in sites[phase]
        )
    g_previous = h
    for n in range(1, 65):
        g = matrix_vector(n2, g_previous)
        if g[0] != 55 * 9**n:
            raise AssertionError("x-coordinate formula drift", n)
        if math.gcd(math.gcd(abs(g[0]), abs(g[1])), abs(g[2])) != 1:
            raise AssertionError("direction unexpectedly imprimitive", n)
        moment = cross(p, g)
        if any(coordinate.denominator != 1 for coordinate in moment):
            raise AssertionError("nonintegral moment", n, moment)
        integer_moment = tuple(int(coordinate) for coordinate in moment)
        integer_point_on_line(g, integer_moment)
        if matrix_vector(frontier["A"], g) != scale(81, g_previous):
            raise AssertionError("line countdown transport drift", n)
        for phase, ghosts in phase_ghosts.items():
            hits = [
                index
                for index, ghost in enumerate(ghosts)
                if cross(subtract(ghost, p), g) == (0, 0, 0)
            ]
            if hits:
                raise AssertionError("finite replay found a latent hit", n, phase, hits)
        g_previous = g

    if cross(subtract(frontier["reveal"], p), h) != (0, 0, 0):
        raise AssertionError("L_0 does not hit the reveal interior")
    return {
        "N_squared": n2,
        "p_numerator_over_22": p_numerator,
        "direction_residues_mod_22": residues,
        "direct_zero_mask_replay_depth": 64,
    }


def matrix_product_2(left, right):
    return tuple(
        tuple(sum(left[i][k] * right[k][j] for k in range(2)) for j in range(2))
        for i in range(2)
    )


def scale_matrix_2(factor, matrix):
    return tuple(tuple(factor * value for value in row) for row in matrix)


def atomic_json_dump(payload, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=output_path.parent, prefix=output_path.name + ".", delete=False
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
    os.replace(temporary, output_path)


def run(policy_path, metadata_path, cache_path):
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = file_sha256(checker_path)
    resources = resource_policy()
    inputs = verify_inputs(policy_path, metadata_path, cache_path)
    with Path(policy_path).open() as handle:
        policy = json.load(handle)
    with Path(metadata_path).open() as handle:
        metadata = json.load(handle)

    cycle, c_first, c_second, potential = selected_policy_cycle(policy)
    sites, scanned_words, scanned_bytes = candidate_sites(metadata, cache_path)
    frontier = affine_cycle_and_frontier(cycle, c_first, sites)
    arithmetic = arithmetic_certificate(frontier, sites, c_first)
    if c_second != (0, 0, 0):
        raise AssertionError("second cycle control is no longer zero")
    if file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("checker changed during run")

    site_payload = {
        str(step): [list(site) for site in sites[step]]
        for step in sorted(sites)
    }
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact geometric latent-reentry obstruction under the pinned "
            "height-two fixed-word policy; not a reachable-history theorem"
        ),
        "checker": {
            "path": "design/nonx_latent_reentry_certificate.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": resources,
        "pinned_inputs": inputs,
        "scan_scope": {
            "steps": [8, 16],
            "domain_words": scanned_words,
            "cache_bytes": scanned_bytes,
            "candidate_sites_by_step": {
                str(step): len(sites[step]) for step in sorted(sites)
            },
            "candidate_site_stream_sha256": stable_hash(site_payload),
        },
        "fixed_policy_cycle": {
            "height_two_potential": {
                "maximum": potential["maximum"],
                "strictly_decreases_on_every_continuous_degenerate_edge": potential[
                    "strictly_decreases_on_every_edge"
                ],
                "stream_sha256": potential["stream_sha256"],
            },
            "edges": [
                {
                    "source_step": 8,
                    "selected_word": list(cycle[8]["word"]),
                    "slot_0_based": 2,
                    "target_step": 16,
                    "prefix_control": list(c_first),
                },
                {
                    "source_step": 16,
                    "selected_word": list(cycle[16]["word"]),
                    "slot_0_based": 0,
                    "target_step": 8,
                    "prefix_control": list(c_second),
                },
            ],
            "macro_map": {
                "definition": "F(x)=M^2(x-c), c=(-4,-4,-3)",
                "linear_part": [list(row) for row in frontier["A"]],
                "translation": list(frontier["b"]),
                "fixed_point": vector_record(frontier["p"]),
            },
        },
        "infinite_line_family": {
            "definition": "g_n=N^(2n)h and L_n={x:x cross g_n=p cross g_n}",
            "h": list(frontier["h"]),
            "p_numerator_over_22": list(arithmetic["p_numerator_over_22"]),
            "primitive_for_every_n": (
                "h is primitive and h_y is nonzero mod 3; N preserves that "
                "nonzero residue and is invertible modulo every prime other than 3"
            ),
            "integer_lattice_line_for_every_n": (
                "the period-five mod-22 orbit makes p cross g_n integral; for "
                "primitive g_n, the integer cross-product map is saturated"
            ),
            "direction_residues_mod_22": [
                list(residue) for residue in arithmetic["direction_residues_mod_22"]
            ],
            "x_coordinate": "(g_n)_x=55*9^n",
            "transport": "F(L_n)=L_(n-1) for n>=1",
        },
        "all_n_silence_and_reveal": {
            "projective_invariant": "J(r,y,z)=(3y^2-yz+3z^2)/r^2",
            "family_value": fraction_record(frontier["J"]),
            "phase_adjustment": (
                "step-8 sites use z=x; step-16 sites use the exact parent ghost "
                "z=c+M^(-1)x"
            ),
            "equal_invariant_frontier": frontier["equal_j_frontier"],
            "exclusion": (
                "the step-8 equal-J direction is g_0; the other primitive "
                "x-coordinate is 165, unequal to 55*9^n for every integer n>=1"
            ),
            "theorem": (
                "for every n>=1, L_n has empty full candidate-site masks at "
                "both phases for n traversals, then F^n(L_n)=L_0 hits the "
                "selected step-8 interior (-2,-2,-2)"
            ),
            "independent_direct_replay_depth": arithmetic[
                "direct_zero_mask_replay_depth"
            ],
        },
        "conclusion": {
            "proved": [
                "the pinned common height-two potential does not bound zero-mask lifetime",
                "the direct carried-line channel has infinitely many geometric right languages under the pinned fixed actions",
                "candidate-to-candidate degenerate rank and latent first-return rank are distinct obligations",
            ],
            "not_proved": [
                "that any L_n is born from two endpoints in a reachable globally legal ordered-path history",
                "that the two selected connector words remain globally legal for such a history",
                "closure of endpoint, near-deep, deep-deep, collision, or same-level cursor-jump channels",
                "failure of every finite quotient on the reachable safety-game state space",
                "an unconditional far-secant lemma or Erdős #193 theorem",
            ],
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_set_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run(args.policy, args.metadata, args.cache)
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "status": payload["status"],
        "scan_scope": payload["scan_scope"],
        "all_n_silence_and_reveal": payload["all_n_silence_and_reveal"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_set_raw": payload["maximum_resident_set_raw"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
