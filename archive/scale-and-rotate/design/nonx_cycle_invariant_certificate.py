#!/usr/bin/env python3
"""Exact all-n certificate for the canonical non-x degenerate 2-cycle.

This is a lightweight algebraic verifier.  It upgrades the raw checker's
256-cycle no-alignment observation to an all-n theorem for the *fixed two
selected words and the carried line only*.  It does not assert that the
inverse-direction lines are born in the realized walk or that the two words
can be repeated in a globally legal ordered construction.

The canonical raw graph artifact remains an exact finite computation.  This
checker pins it and then verifies a symbolic projective invariant whose six
strict inequalities prove that no iterate can meet a selected-word interior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = Path("/tmp/nonx-degenerate-site-graph-canonical.json")
DEFAULT_SUMMARY = ROOT / "design/nonx-cycle-invariant-certificate-summary.json"

EXPECTED_INPUT_SHA256 = (
    "e0f5765fec55b25b9392333c25da037d9d073b7bc95b81680bb4e5957a0c4d92"
)
EXPECTED_GRAPH_CHECKER_SHA256 = (
    "4eb928bad0c0104d34b68424b07dd3b6a4939f216968bd6b2399a540b592e755"
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
B = (
    (0, -3),
    (3, -1),
)
# Twice the yz quadratic form 3*y^2-y*z+3*z^2.
H = (
    (6, -1),
    (-1, 6),
)
IDENTITY_3 = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
)

EXPECTED_NODES = (
    (1, (-3, 0, -3)),
    (1, (-3, 3, -2)),
    (1, (-3, 0, -3)),
)
EXPECTED_EDGES = (
    {
        "source": (-3, 0, -3),
        "target": (-3, 3, -2),
        "control": (-2, 1, -2),
        "word": (15, 1, 20, 71),
        "slot": 1,
        "ordinal": 2020,
        "interiors": ((-6, 1, -5), (-4, -1, -3), (-2, 1, -2)),
    },
    {
        "source": (-3, 3, -2),
        "target": (-3, 0, -3),
        "control": (-2, 4, -2),
        "word": (20, 71, 1, 15),
        "slot": 2,
        "ordinal": 4415,
        "interiors": ((-4, 2, -3), (-2, 2, -2), (-2, 4, -2)),
    },
)
EXPECTED_REVEAL_SITE = (-6, 1, -6)
EXPECTED_REVEAL_DIRECTION = (3, -1, 3)
EXPECTED_DISPLACEMENTS = (
    ((-3, 1, -2), (-1, -1, 0), (1, 1, 1)),
    ((-1, -1, -1), (1, -1, 0), (1, 1, 0)),
)
EXPECTED_J = (
    (Fraction(17, 9), Fraction(3, 1), Fraction(5, 1)),
    (Fraction(5, 1), Fraction(3, 1), Fraction(3, 1)),
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_file_snapshot(path):
    display_path = Path(path)
    resolved_path = display_path.resolve()
    before = resolved_path.stat()
    sha256 = file_sha256(resolved_path)
    after = resolved_path.stat()
    identity_fields = (
        "st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns",
    )
    if tuple(getattr(before, item) for item in identity_fields) != tuple(
        getattr(after, item) for item in identity_fields
    ):
        raise RuntimeError(
            "input changed while it was being hashed", str(resolved_path)
        )
    return {
        "path": str(display_path),
        "sha256": sha256,
        "bytes": after.st_size,
    }


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def apply_matrix(matrix, vector):
    return tuple(sum(a * b for a, b in zip(row, vector)) for row in matrix)


def transpose(matrix):
    return tuple(zip(*matrix))


def matrix_multiply(left, right):
    right_t = transpose(right)
    return tuple(
        tuple(sum(a * b for a, b in zip(row, column)) for column in right_t)
        for row in left
    )


def matrix_scale(factor, matrix):
    return tuple(tuple(factor * value for value in row) for row in matrix)


def determinant_3(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def canonical_primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if divisor == 0:
        raise ValueError("zero vector has no primitive direction")
    primitive = tuple(value // divisor for value in vector)
    first = next(value for value in primitive if value)
    if first < 0:
        primitive = tuple(-value for value in primitive)
    return primitive


def j_invariant(direction):
    r, y, z = direction
    if r == 0:
        raise ValueError("this certificate uses the finite r!=0 invariant")
    return Fraction(3 * y * y - y * z + 3 * z * z, r * r)


def fraction_record(value):
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "text": str(value),
    }


def certify(input_path):
    snapshot = stable_file_snapshot(input_path)
    assert snapshot["sha256"] == EXPECTED_INPUT_SHA256

    graph_checker = ROOT / "design/nonx_degenerate_site_graph.py"
    graph_checker_sha256 = file_sha256(graph_checker)
    assert graph_checker_sha256 == EXPECTED_GRAPH_CHECKER_SHA256

    with Path(input_path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["checker"]["sha256"] == EXPECTED_GRAPH_CHECKER_SHA256

    cycle = payload["canonical_x_avoiding_cycle_witness"]
    compatible_structure = payload["x_avoiding_compatibility_graph_structure"]
    assert compatible_structure["cyclic_components"] == 1
    assert compatible_structure["largest_cyclic_component"] == 768
    assert compatible_structure["vertices_in_cyclic_components"] == 768
    nodes = tuple(
        (record["step"], tuple(record["candidate_site"]))
        for record in cycle["cycle_node_sequence"]
    )
    assert nodes == EXPECTED_NODES
    assert cycle["cycle_length_edges"] == 2
    assert cycle["every_selected_cycle_word_avoids_its_carried_site"]

    # Universal matrix identities: J(Mg)=J(g), and N is a projective inverse.
    assert matrix_multiply(transpose(B), matrix_multiply(H, B)) == matrix_scale(9, H)
    assert matrix_multiply(M, N) == matrix_scale(9, IDENTITY_3)
    assert matrix_multiply(N, M) == matrix_scale(9, IDENTITY_3)
    assert determinant_3(N) == 27

    edge_summaries = []
    for index, (record, expected) in enumerate(zip(cycle["edge_records"], EXPECTED_EDGES)):
        witness = record["exact_cache_occurrence_witness"]
        source = tuple(record["source"]["candidate_site"])
        target = tuple(record["target"]["candidate_site"])
        control = tuple(record["selected_minimum_control"])
        interiors = tuple(tuple(site) for site in witness["interior_sites"])
        assert source == expected["source"]
        assert target == expected["target"]
        assert control == expected["control"]
        assert tuple(witness["word"]) == expected["word"]
        assert witness["slot_0_based"] == expected["slot"]
        assert witness["word_ordinal_1_based"] == expected["ordinal"]
        assert interiors == expected["interiors"]
        assert tuple(witness["carried_site"]) == source
        assert witness["interior_avoids_carried_site"]
        assert tuple(record["verified_delta"]) == (0, 0, 0)
        assert target == apply_matrix(M, subtract(source, control))

        displacements = tuple(subtract(interior, source) for interior in interiors)
        assert displacements == EXPECTED_DISPLACEMENTS[index]
        values = tuple(j_invariant(vector) for vector in displacements)
        assert values == EXPECTED_J[index]
        edge_summaries.append({
            "edge_index": index,
            "source_site": list(source),
            "target_site": list(target),
            "prefix_control": list(control),
            "word": list(expected["word"]),
            "slot_0_based": expected["slot"],
            "word_ordinal_1_based": expected["ordinal"],
            "interior_displacements": [list(item) for item in displacements],
            "interior_J_values": [fraction_record(item) for item in values],
        })

    reveal = cycle["recurrent_start_phase"]["first_non_x_delayed_reveal_witness"]
    reveal_site = tuple(reveal["site"])
    reveal_direction = tuple(reveal["primitive_direction_from_carried_site"])
    assert reveal_site == EXPECTED_REVEAL_SITE
    assert reveal_direction == EXPECTED_REVEAL_DIRECTION
    assert canonical_primitive(subtract(reveal_site, EXPECTED_NODES[0][1])) == reveal_direction
    reveal_j = j_invariant(reveal_direction)
    assert reveal_j == Fraction(11, 3)
    for values in EXPECTED_J:
        assert all(value != reveal_j for value in values)

    countdown = payload["canonical_x_avoiding_cycle_finite_countdown_test"]
    assert countdown["first_poison"] is None
    assert countdown["clean_countdown_prefix_cycles"] == 256

    # If y is nonzero modulo 3, N preserves that condition.  Together with
    # det(N)=3^3, this proves by induction that every N^j reveal_direction is
    # primitive: a common prime !=3 would pull back through N mod p, and 3
    # cannot divide the new y coordinate.
    assert reveal_direction[1] % 3 != 0
    assert apply_matrix(N, reveal_direction)[1] % 3 == (-reveal_direction[1]) % 3

    checker_path = Path(__file__).resolve()
    return {
        "date": payload["date"],
        "status": "all-n theorem for the fixed geometric two-word cycle",
        "checker": {
            "path": str(checker_path.relative_to(ROOT)),
            "sha256": file_sha256(checker_path),
        },
        "pinned_input": snapshot,
        "pinned_graph_checker": {
            "path": "design/nonx_degenerate_site_graph.py",
            "sha256": graph_checker_sha256,
        },
        "cycle": {
            "step": 1,
            "containing_exact_x_avoiding_scc_vertices": 768,
            "nodes": [
                {"step": step, "candidate_site": list(site)}
                for step, site in EXPECTED_NODES
            ],
            "edges": edge_summaries,
            "fixed_words_are_exact_cache_occurrences": True,
            "each_edge_is_direction_blind": True,
        },
        "projective_invariant": {
            "formula": "J(r,y,z)=(3*y^2-y*z+3*z^2)/r^2",
            "domain": "r != 0",
            "universal_identity": "B^T [[6,-1],[-1,6]] B = 9 [[6,-1],[-1,6]], while r maps to 3r",
            "reveal_site": list(reveal_site),
            "reveal_direction": list(reveal_direction),
            "reveal_J": fraction_record(reveal_j),
            "all_six_interior_J_values_differ_from_reveal_J": True,
        },
        "all_n_cleanliness_theorem": {
            "statement": "For every integer j, no projective iterate T^j(3,-1,3) is parallel to an interior displacement of either fixed cycle word.",
            "reason": "J is invariant under both forward and inverse projective transport, and each of the six exact displacement values differs from 11/3.",
            "fixed_label_countdown_is_carried_line_clean_for_every_cycle_count": True,
            "supersedes_finite_256_cycle_alignment_test_for_this_fixed_pair": True,
        },
        "nonperiodicity_theorem": {
            "normalized_yz_matrix": "A=B/3",
            "determinant": 1,
            "trace": "-1/3",
            "reason": "If A had a periodic nonzero real vector, an eigenvalue u would be a root of unity. Then u+u^-1=-1/3 would be a rational algebraic integer and hence an integer, contradiction.",
            "reveal_direction_has_no_nonzero_projective_period": True,
        },
        "infinite_right_language_implication": {
            "integer_primitive_family": "g_n=canonprim(N^(2n)*(3,-1,3)), n>=0",
            "line_family": "ell_n is the integer line through (-3,0,-3) with direction g_n",
            "distinguishing_query": "after k fixed two-edge cycles, query candidate site (-6,1,-6)",
            "exact_result": "ell_n hits the distinguishing site exactly when k=n",
            "fixed_geometric_cycle_has_infinitely_many_line-effect_right_languages": True,
            "actual_ordered_path_conclusion_is_conditional": "The realized-path quotient has infinite index if all ell_n are reachable carried secants at this interface and the same two connector words are globally legal, correlated, and repeatable from those histories.",
        },
        "scope_limitations": [
            "does not prove any ell_n is born from two points of the realized walk",
            "does not prove the two fixed words coexist in one globally legal repeatable ordered history",
            "checks carried-line poisoning of the two selected words, not collisions, other existing secants, endpoint-on-candidate-line effects, or near--deep births",
            "does not by itself prove infinite index for the realized ordered-path safety game",
        ],
    }


def stable_json(value):
    return json.dumps(value, sort_keys=True, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--verify-summary", type=Path)
    args = parser.parse_args()

    certificate = certify(args.input)
    rendered = stable_json(certificate)
    if args.verify_summary is not None:
        expected = args.verify_summary.read_text(encoding="utf-8")
        if rendered != expected:
            raise AssertionError("checked-in compact summary is stale")
    print(rendered, end="")


if __name__ == "__main__":
    main()
