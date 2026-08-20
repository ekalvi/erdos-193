#!/usr/bin/env python3
"""Exact bounded four-gap probe at the fragile L7 target segment 3783.

This program reconstructs its state from the checked-in construction and
connector-domain pickles.  It does not depend on caches or sampled menus.

Let ``B`` be the exact pre-target point set with the recorded interiors of
gaps 3782, 3784, 3786, and 3785 removed.  For a fixed choice ``A`` at 3782
and ``B'`` at 3784, define ``R(A,B')`` by subtracting from the target words
every effect of *every* unary-legal 3786 choice, including its secants with
``A`` and ``B'``.  Compatibility between those alternative 3786 choices is
deliberately ignored, so ``R`` is a sound lower bound.

The checker orders compatible ``(A,B')`` states by ``|R(A,B')|`` (not by
their raw pair-survivor count), with candidate-list indices as deterministic
tie breakers.  For each of the first twelve states it then proves

    for every unary-legal D at gap 3785 and C at gap 3786,
    if B union A union B' union C union D is triple-free, then at least one
    target connector word at gap 3783 is exactly legal.

For a D whose all-C overapproximation does not cover ``R``, a surviving word
is immediate.  Every remaining coarse-zero D core is refined over every
compatible C, with all pair and mixed-triple constraints checked exactly.

This is an exact finite computation for twelve selected A/B states.  It is
not a certificate for every compatible A/B pair, a level-uniform safety
invariant, a deterministic-selector theorem, or an unconditional proof of
Erdos #193.  Its universal C/D quantifier is an all-choice robustness result
inside this slice.  Conversely, a fatal assignment outside this slice would
refute all-choice robustness, but would not by itself refute the existence of
a winning controlled connector selector.

The implementation is single-process.  Run it with one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_four_gap_probe.py \
        > design/l7-four-gap-probe-result.json

Only a completed, assertion-checked JSON object is written to stdout.  If an
expected count changes or an unexpected jam is found, the program raises
before emitting a successful result.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    compute_poison,
    cross,
    midpoint,
    primitive,
    replay_stitch,
    sub,
)


LEVEL = 7
TARGET = 3783
# A, B, C are the three small step-123 domains.  D is the large step-20
# domain.  This is semantic order, not construction-schedule order.
GAPS = (3782, 3784, 3786, 3785)
A_GAP, B_GAP, C_GAP, D_GAP = GAPS
CENSUS_STATES = 100
CERTIFIED_STATES = 12

EXPECTED = {
    "target_schedule_rank": 16_790,
    "schedule_ranks": (8_828, 8_829, 8_830, 433),
    "actual_pre_target_points": 70_334,
    "removed_interiors": 9,
    "fixed_base_points": 70_325,
    "target_domain_size": 9_046,
    "target_base_survivors": 1_394,
    "variable_domain_sizes": (2_570, 2_570, 2_570, 47_467),
    "unary_legal": (651, 1_408, 1_802, 17_837),
    "added_site_universe": 442,
    "gap_site_universes": (76, 99, 102, 204),
    "nonzero_target_pair_masks": 6_852,
    "base_secant_bad_site_pairs": 620,
    "sound_interface": {
        "other_site_universe": 277,
        "other_pair_bits": 38_226,
        "d_site_universe": 204,
        "target_mask_classes": 10_796,
        "target_plus_cross_classes": 17_120,
        "full_classes": 17_821,
        "largest_full_class": 2,
        "singleton_full_classes": 17_805,
        "bad_single_range": (0, 35),
        "bad_pair_range": (53, 383),
    },
    "compatible_ab_pairs": 865_674,
    "minimum_all_c_residual": 53,
    "census_states_with_coarse_zero": 100,
    "census_coarse_zero_cores": 3_221,
    # residual, A list index, B list index, coarse D cores,
    # incompatible ABD cores, exact compatible-C assignments, local minimum,
    # local-minimum C list index, local-minimum D list index
    "first_twelve": (
        (53, 386, 77, 89, 31, 63_024, 26, 1677, 15710),
        (61, 405, 962, 23, 10, 11_281, 89, 561, 12125),
        (61, 412, 1100, 30, 10, 13_613, 22, 1166, 15682),
        (63, 390, 1095, 3, 0, 2_893, 62, 1415, 14838),
        (64, 386, 227, 75, 33, 31_590, 30, 1018, 941),
        (65, 386, 1036, 51, 35, 11_442, 53, 458, 15403),
        (65, 405, 1015, 6, 1, 5_174, 77, 559, 987),
        (66, 330, 1135, 21, 0, 25_311, 77, 1024, 9662),
        (67, 386, 1004, 40, 15, 21_469, 37, 1008, 9330),
        (68, 386, 297, 99, 15, 90_318, 37, 477, 6721),
        (68, 386, 602, 34, 14, 13_571, 84, 1674, 15403),
        (70, 379, 1156, 34, 7, 28_633, 31, 1293, 14852),
    ),
    "certified_coarse_zero_cores": 505,
    "certified_incompatible_abd_cores": 171,
    "certified_exact_refined_cores": 334,
    "certified_compatible_c_assignments": 318_319,
    "minimum_reachable_refined_core_survivors": 22,
    "minimum_witness_candidate_indices": (412, 1100, 1166, 15682),
    "minimum_witness_domain_indices": (1534, 1969, 1505, 41092),
    "minimum_witness_words": (
        (102, 112, 53, 102),
        (106, 59, 101, 103),
        (102, 107, 108, 52),
        (18, 24, 72, 39, 44),
    ),
}


def poisoned_atoms(info):
    return {index for index, record in enumerate(info) if math.isfinite(record["threshold"])}


def survivor_indices(model, poisoned):
    return [
        word_index
        for word_index, atoms in enumerate(model["word_atoms"])
        if not any(atom in poisoned for atom in atoms)
    ]


def collinear(a, b, c):
    return cross(sub(b, a), sub(c, a)) == (0, 0, 0)


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def point_set_sha256(points):
    serial = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def main():
    if not __debug__:
        raise SystemExit("certificate assertions require normal Python; do not use -O")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    started = time.time()
    doms, _d24 = load_domains()
    st, target_rank, actual_points, actual_births = replay_stitch(LEVEL, TARGET)
    schedule_ranks = tuple(st["order"].index(gap) for gap in GAPS)
    assert all(rank < target_rank for rank in schedule_ranks)

    removed = set()
    for gap in GAPS:
        removed.update(word_interiors(st["anchors"][gap], st["words"][gap]))
    base_pairs = [
        (point, birth)
        for point, birth in zip(actual_points, actual_births)
        if point not in removed
    ]
    base = [point for point, _birth in base_pairs]
    base_births = [birth for _point, birth in base_pairs]
    assert len(base) == len(set(base))

    target_step = st["parent_word"][TARGET]
    target_domain = doms[target_step]
    assert len(target_domain) == len(set(target_domain))
    target_model = build_domain_model(target_domain)
    target_start = st["anchors"][TARGET]
    target_info = compute_poison(
        target_model,
        target_start,
        midpoint(target_start, st["anchors"][TARGET + 1]),
        base,
        base_births,
        LEVEL,
    )
    base_survivors = survivor_indices(target_model, poisoned_atoms(target_info))
    survivor_position = {
        word_index: bit for bit, word_index in enumerate(base_survivors)
    }
    full_target_mask = (1 << len(base_survivors)) - 1

    choices = []
    gap_domains = []
    for gap in GAPS:
        domain = doms[st["parent_word"][gap]]
        assert len(domain) == len(set(domain))
        model = build_domain_model(domain)
        info = compute_poison(
            model,
            st["anchors"][gap],
            midpoint(st["anchors"][gap], st["anchors"][gap + 1]),
            base,
            base_births,
            LEVEL,
        )
        poison = poisoned_atoms(info)
        gap_choices = []
        for word_index in survivor_indices(model, poison):
            word = domain[word_index]
            gap_choices.append(
                (
                    word_index,
                    word,
                    tuple(word_interiors(st["anchors"][gap], word)),
                )
            )
        choices.append(gap_choices)
        gap_domains.append(domain)

    pool = sorted(
        {
            point
            for gap_choices in choices
            for _word_index, _word, points in gap_choices
            for point in points
        }
    )
    point_id = {point: index for index, point in enumerate(pool)}
    compact_choices = [
        [
            (word_index, word, tuple(point_id[point] for point in points))
            for word_index, word, points in gap_choices
        ]
        for gap_choices in choices
    ]
    gap_point_sets = [
        {point for _word_index, _word, points in gap_choices for point in points}
        for gap_choices in compact_choices
    ]

    # Map target legality atoms to the subset of target words that survived B.
    atom_word_mask = [0] * len(target_model["atom_desc"])
    for word_index in base_survivors:
        bit = 1 << survivor_position[word_index]
        for atom in target_model["word_atoms"][word_index]:
            atom_word_mask[atom] |= bit
    target_site_mask = {
        add(target_start, offset): atom_word_mask[atom]
        for offset, atom in target_model["site_id"].items()
    }

    # Effect of one added old point on target site/line atoms.  This includes
    # collision, incidence with a target-internal pair line, and a fixed-base
    # plus added-point secant through a target candidate site.
    unary_point_mask = [0] * len(pool)
    target_directions = list(target_model["line_by_direction"].items())
    for point_index, point in enumerate(pool):
        relative = sub(point, target_start)
        mask = target_site_mask.get(point, 0)
        for direction, by_moment in target_directions:
            atom = by_moment.get(cross(relative, direction))
            if atom is not None:
                mask |= atom_word_mask[atom]
        unary_point_mask[point_index] = mask
    for site, site_mask in target_site_mask.items():
        base_directions = {primitive(sub(point, site)) for point in base}
        for point_index, point in enumerate(pool):
            if point == site or primitive(sub(point, site)) in base_directions:
                unary_point_mask[point_index] |= site_mask

    # Effect of secants through two added sites on target candidate sites.
    pair_target_mask = {}
    target_sites = list(target_site_mask.items())
    for first, point in enumerate(pool):
        for second in range(first + 1, len(pool)):
            mask = 0
            for site, site_mask in target_sites:
                if collinear(point, pool[second], site):
                    mask |= site_mask
            if mask:
                pair_target_mask[(first, second)] = mask

    # Two added sites are incompatible when their secant already contains a
    # fixed-base point.  Collision is handled separately by pair_compatible.
    base_bad_pairs = set()
    for first, point in enumerate(pool):
        base_directions = {primitive(sub(old, point)) for old in base}
        for second in range(first + 1, len(pool)):
            if primitive(sub(pool[second], point)) in base_directions:
                base_bad_pairs.add((first, second))

    def point_pair_target_mask(first, second):
        if first == second:
            return target_site_mask.get(pool[first], 0)
        if first > second:
            first, second = second, first
        return pair_target_mask.get((first, second), 0)

    def choice_target_mask(points):
        mask = 0
        for point in points:
            mask |= unary_point_mask[point]
        for first, second in combinations(points, 2):
            mask |= point_pair_target_mask(first, second)
        return mask

    def cross_target_mask(first_points, second_points):
        mask = 0
        for first in first_points:
            for second in second_points:
                mask |= point_pair_target_mask(first, second)
        return mask

    def pair_compatible(first_points, second_points):
        if set(first_points) & set(second_points):
            return False
        for first in first_points:
            for second in second_points:
                key = (first, second) if first < second else (second, first)
                if key in base_bad_pairs:
                    return False

        joined = first_points + second_points
        split = len(first_points)
        for i, j, k in combinations(range(len(joined)), 3):
            # Skip triples wholly within one already-unary-legal choice.
            if k < split or i >= split:
                continue
            if collinear(pool[joined[i]], pool[joined[j]], pool[joined[k]]):
                return False
        return True

    def mixed_compatible(first_points, second_points, third_points):
        return not any(
            collinear(pool[first], pool[second], pool[third])
            for first in first_points
            for second in second_points
            for third in third_points
        )

    choice_masks = [
        [choice_target_mask(choice[2]) for choice in gap_choices]
        for gap_choices in compact_choices
    ]

    # A sound exact interface for D relative to arbitrary A/B/C choices.
    #
    #   target mask: D-only target poisoning;
    #   cross vector: D--q target poisoning for every other possible site q;
    #   bad singles: q collides, makes a base--D--q triple, or lies on a
    #                secant through two D interiors;
    #   bad pairs:   {q,r} whose secant contains a D interior.
    #
    # These four fields determine every target and legality interaction that
    # contains D.  Equality of full signatures is therefore a sound quotient.
    other_points = sorted(set().union(*gap_point_sets[:3]))
    other_count = len(other_points)
    d_point_universe = sorted(gap_point_sets[3])

    def other_pair_bit(first, second):
        if first > second:
            first, second = second, first
        return first * (2 * other_count - first - 1) // 2 + second - first - 1

    bad_single_by_d_point = {}
    bad_pair_by_d_point = {}
    cross_vector_by_d_point = {}
    for d_point in d_point_universe:
        bad_singles = 0
        direction_groups = defaultdict(list)
        cross_vector = {}
        for other_index, other_point in enumerate(other_points):
            if d_point == other_point:
                bad_singles |= 1 << other_index
            else:
                key = (
                    (d_point, other_point)
                    if d_point < other_point
                    else (other_point, d_point)
                )
                if key in base_bad_pairs:
                    bad_singles |= 1 << other_index
                direction_groups[
                    primitive(sub(pool[other_point], pool[d_point]))
                ].append(other_index)
            mask = point_pair_target_mask(d_point, other_point)
            if mask:
                cross_vector[other_index] = mask

        bad_pairs = 0
        for positions in direction_groups.values():
            for first, second in combinations(positions, 2):
                bad_pairs |= 1 << other_pair_bit(first, second)
        bad_single_by_d_point[d_point] = bad_singles
        bad_pair_by_d_point[d_point] = bad_pairs
        cross_vector_by_d_point[d_point] = cross_vector

    target_signature_counts = Counter()
    effect_signature_counts = Counter()
    full_signature_counts = Counter()
    bad_single_counts = []
    bad_pair_counts = []
    for d_index, d_choice in enumerate(compact_choices[3]):
        points = d_choice[2]
        bad_singles = 0
        bad_pairs = 0
        cross_keys = set()
        for point in points:
            bad_singles |= bad_single_by_d_point[point]
            bad_pairs |= bad_pair_by_d_point[point]
            cross_keys.update(cross_vector_by_d_point[point])
        for first, second in combinations(points, 2):
            for other_index, other_point in enumerate(other_points):
                if collinear(pool[first], pool[second], pool[other_point]):
                    bad_singles |= 1 << other_index

        cross_entries = []
        for other_index in sorted(cross_keys):
            mask = 0
            for point in points:
                mask |= cross_vector_by_d_point[point].get(other_index, 0)
            if mask:
                cross_entries.append((other_index, mask))
        cross_vector = tuple(cross_entries)
        target_signature = choice_masks[3][d_index]
        effect_signature = (target_signature, cross_vector)
        full_signature = (
            target_signature,
            cross_vector,
            bad_singles,
            bad_pairs,
        )
        target_signature_counts[target_signature] += 1
        effect_signature_counts[effect_signature] += 1
        full_signature_counts[full_signature] += 1
        bad_single_counts.append(bad_singles.bit_count())
        bad_pair_counts.append(bad_pairs.bit_count())

    # Sound all-C residual for each compatible A/B pair.
    all_c_unary = 0
    for mask in choice_masks[2]:
        all_c_unary |= mask

    potential_c_for_a = []
    potential_c_for_b = []
    for gap_index, output in (
        (0, potential_c_for_a),
        (1, potential_c_for_b),
    ):
        for _word_index, _word, points in compact_choices[gap_index]:
            mask = all_c_unary
            for c_choice in compact_choices[2]:
                mask |= cross_target_mask(points, c_choice[2])
            output.append(mask)

    compatible_ab = 0
    minimum_all_c_residual = len(base_survivors) + 1
    smallest_states = []
    for a_index, a_choice in enumerate(compact_choices[0]):
        for b_index, b_choice in enumerate(compact_choices[1]):
            if not pair_compatible(a_choice[2], b_choice[2]):
                continue
            compatible_ab += 1
            ab_mask = (
                choice_masks[0][a_index]
                | choice_masks[1][b_index]
                | cross_target_mask(a_choice[2], b_choice[2])
            )
            residual = full_target_mask & ~(
                ab_mask
                | potential_c_for_a[a_index]
                | potential_c_for_b[b_index]
            )
            residual_count = residual.bit_count()
            minimum_all_c_residual = min(
                minimum_all_c_residual, residual_count
            )
            record = (residual_count, a_index, b_index, residual)
            # This is deterministic because A and B indices are traversed in
            # ascending order.  At the final cardinality cutoff, the earliest
            # candidate-index ties are retained.
            if (
                len(smallest_states) < CENSUS_STATES
                or residual_count < smallest_states[-1][0]
            ):
                smallest_states.append(record)
                smallest_states.sort()
                del smallest_states[CENSUS_STATES:]

    assert len(smallest_states) == CENSUS_STATES

    # D-only plus every possible C--D target effect.  This may combine effects
    # from mutually incompatible C choices, so it is a sound overapproximation.
    c_point_universe = gap_point_sets[2]
    d_base_masks = []
    for d_index, d_choice in enumerate(compact_choices[3]):
        mask = choice_masks[3][d_index]
        for d_point in d_choice[2]:
            for c_point in c_point_universe:
                mask |= point_pair_target_mask(d_point, c_point)
        d_base_masks.append(mask)

    cores_by_state = [[] for _ in range(CENSUS_STATES)]
    for state_rank, (_count, a_index, b_index, residual) in enumerate(
        smallest_states
    ):
        a_points = compact_choices[0][a_index][2]
        b_points = compact_choices[1][b_index][2]
        for d_index, d_choice in enumerate(compact_choices[3]):
            coarse_mask = (
                d_base_masks[d_index]
                | cross_target_mask(a_points, d_choice[2])
                | cross_target_mask(b_points, d_choice[2])
            )
            if not (residual & ~coarse_mask):
                cores_by_state[state_rank].append(d_index)

    census_states_with_zero = sum(bool(cores) for cores in cores_by_state)
    census_core_count = sum(map(len, cores_by_state))

    # Refine every coarse-zero D core for the selected first twelve A/B states.
    total_incompatible_abd = 0
    total_exact_refined_cores = 0
    total_compatible_c_assignments = 0
    fatal_assignment = None
    global_minimum = len(base_survivors) + 1
    global_minimum_record = None
    state_results = []

    for state_rank in range(CERTIFIED_STATES):
        residual_count, a_index, b_index, _residual = smallest_states[state_rank]
        a_choice = compact_choices[0][a_index]
        b_choice = compact_choices[1][b_index]
        a_points = a_choice[2]
        b_points = b_choice[2]
        ab_mask = (
            choice_masks[0][a_index]
            | choice_masks[1][b_index]
            | cross_target_mask(a_points, b_points)
        )

        compatible_c = []
        for c_index, c_choice in enumerate(compact_choices[2]):
            c_points = c_choice[2]
            if not pair_compatible(a_points, c_points):
                continue
            if not pair_compatible(b_points, c_points):
                continue
            if not mixed_compatible(a_points, b_points, c_points):
                continue
            compatible_c.append(
                (
                    c_index,
                    ab_mask
                    | choice_masks[2][c_index]
                    | cross_target_mask(a_points, c_points)
                    | cross_target_mask(b_points, c_points),
                )
            )

        local_incompatible_abd = 0
        local_exact_refined_cores = 0
        local_compatible_c_assignments = 0
        local_minimum = len(base_survivors) + 1
        local_minimum_record = None

        for d_index in cores_by_state[state_rank]:
            d_choice = compact_choices[3][d_index]
            d_choice_points = d_choice[2]
            if (
                not pair_compatible(a_points, d_choice_points)
                or not pair_compatible(b_points, d_choice_points)
                or not mixed_compatible(a_points, b_points, d_choice_points)
            ):
                local_incompatible_abd += 1
                total_incompatible_abd += 1
                continue

            local_exact_refined_cores += 1
            total_exact_refined_cores += 1
            d_mask = (
                choice_masks[3][d_index]
                | cross_target_mask(a_points, d_choice_points)
                | cross_target_mask(b_points, d_choice_points)
            )
            for c_index, c_base_mask in compatible_c:
                c_points = compact_choices[2][c_index][2]
                if not pair_compatible(c_points, d_choice_points):
                    continue
                if not mixed_compatible(a_points, c_points, d_choice_points):
                    continue
                if not mixed_compatible(b_points, c_points, d_choice_points):
                    continue

                local_compatible_c_assignments += 1
                total_compatible_c_assignments += 1
                exact_mask = (
                    c_base_mask
                    | d_mask
                    | cross_target_mask(c_points, d_choice_points)
                )
                survivors = full_target_mask & ~exact_mask
                survivor_count = survivors.bit_count()
                record = (
                    survivor_count,
                    state_rank,
                    a_index,
                    b_index,
                    c_index,
                    d_index,
                    survivors,
                )
                if survivor_count < local_minimum:
                    local_minimum = survivor_count
                    local_minimum_record = record
                if survivor_count < global_minimum:
                    global_minimum = survivor_count
                    global_minimum_record = record
                if survivor_count == 0:
                    fatal_assignment = record
                    break
            if fatal_assignment is not None:
                break
        if fatal_assignment is not None:
            break

        state_results.append(
            {
                "state_rank": state_rank,
                "all_c_residual": residual_count,
                "a_candidate_index": a_index,
                "b_candidate_index": b_index,
                "a_domain_index": a_choice[0],
                "b_domain_index": b_choice[0],
                "a_word": list(a_choice[1]),
                "b_word": list(b_choice[1]),
                "coarse_zero_d_cores": len(cores_by_state[state_rank]),
                "abd_incompatible_cores": local_incompatible_abd,
                "abd_exact_refined_cores": local_exact_refined_cores,
                "compatible_c_assignments_checked": (
                    local_compatible_c_assignments
                ),
                "minimum_reachable_refined_core_survivors": local_minimum,
                "minimum_c_candidate_index": (
                    None if local_minimum_record is None else local_minimum_record[4]
                ),
                "minimum_d_candidate_index": (
                    None if local_minimum_record is None else local_minimum_record[5]
                ),
            }
        )

    # An unexpected fatal assignment or early exit is not allowed to emit a
    # successful-looking JSON result.
    assert fatal_assignment is None, fatal_assignment
    assert len(state_results) == CERTIFIED_STATES
    assert global_minimum_record is not None

    # Checked-in finite-result assertions.
    assert target_rank == EXPECTED["target_schedule_rank"]
    assert schedule_ranks == EXPECTED["schedule_ranks"]
    assert len(actual_points) == EXPECTED["actual_pre_target_points"]
    assert len(removed) == EXPECTED["removed_interiors"]
    assert len(base) == EXPECTED["fixed_base_points"]
    assert len(target_domain) == EXPECTED["target_domain_size"]
    assert len(base_survivors) == EXPECTED["target_base_survivors"]
    assert tuple(map(len, gap_domains)) == EXPECTED["variable_domain_sizes"]
    assert tuple(map(len, compact_choices)) == EXPECTED["unary_legal"]
    assert len(pool) == EXPECTED["added_site_universe"]
    assert tuple(map(len, gap_point_sets)) == EXPECTED["gap_site_universes"]
    assert len(pair_target_mask) == EXPECTED["nonzero_target_pair_masks"]
    assert len(base_bad_pairs) == EXPECTED["base_secant_bad_site_pairs"]

    expected_interface = EXPECTED["sound_interface"]
    assert other_count == expected_interface["other_site_universe"]
    assert other_count * (other_count - 1) // 2 == expected_interface["other_pair_bits"]
    assert len(d_point_universe) == expected_interface["d_site_universe"]
    assert len(target_signature_counts) == expected_interface["target_mask_classes"]
    assert len(effect_signature_counts) == expected_interface["target_plus_cross_classes"]
    assert len(full_signature_counts) == expected_interface["full_classes"]
    assert max(full_signature_counts.values()) == expected_interface["largest_full_class"]
    assert sum(count == 1 for count in full_signature_counts.values()) == expected_interface["singleton_full_classes"]
    assert (min(bad_single_counts), max(bad_single_counts)) == expected_interface["bad_single_range"]
    assert (min(bad_pair_counts), max(bad_pair_counts)) == expected_interface["bad_pair_range"]

    assert compatible_ab == EXPECTED["compatible_ab_pairs"]
    assert minimum_all_c_residual == EXPECTED["minimum_all_c_residual"]
    assert census_states_with_zero == EXPECTED["census_states_with_coarse_zero"]
    assert census_core_count == EXPECTED["census_coarse_zero_cores"]

    observed_first_twelve = tuple(
        (
            result["all_c_residual"],
            result["a_candidate_index"],
            result["b_candidate_index"],
            result["coarse_zero_d_cores"],
            result["abd_incompatible_cores"],
            result["compatible_c_assignments_checked"],
            result["minimum_reachable_refined_core_survivors"],
            result["minimum_c_candidate_index"],
            result["minimum_d_candidate_index"],
        )
        for result in state_results
    )
    assert observed_first_twelve == EXPECTED["first_twelve"]
    certified_core_count = sum(
        len(cores_by_state[state_rank])
        for state_rank in range(CERTIFIED_STATES)
    )
    assert certified_core_count == EXPECTED["certified_coarse_zero_cores"]
    assert total_incompatible_abd == EXPECTED["certified_incompatible_abd_cores"]
    assert total_exact_refined_cores == EXPECTED["certified_exact_refined_cores"]
    assert total_compatible_c_assignments == EXPECTED["certified_compatible_c_assignments"]
    assert global_minimum == EXPECTED["minimum_reachable_refined_core_survivors"]

    _, minimum_state_rank, a_index, b_index, c_index, d_index, _minimum_mask = (
        global_minimum_record
    )
    minimum_candidate_indices = (a_index, b_index, c_index, d_index)
    minimum_choices = tuple(
        compact_choices[gap_index][candidate_index]
        for gap_index, candidate_index in enumerate(minimum_candidate_indices)
    )
    minimum_domain_indices = tuple(choice[0] for choice in minimum_choices)
    minimum_words = tuple(choice[1] for choice in minimum_choices)
    assert minimum_candidate_indices == EXPECTED["minimum_witness_candidate_indices"]
    assert minimum_domain_indices == EXPECTED["minimum_witness_domain_indices"]
    assert minimum_words == EXPECTED["minimum_witness_words"]

    finished = time.time()
    result = {
        "status": (
            "exact finite first-12 four-gap non-jamming computation complete"
        ),
        "known_assertions_passed": True,
        "level": LEVEL,
        "schedule": "fragile-first",
        "target_segment": TARGET,
        "target_schedule_rank_zero_based": target_rank,
        "target_step": target_step,
        "target_domain_size": len(target_domain),
        "quantifier": (
            "for each of the selected first 12 A/B states, for every unary-legal "
            "D at 3785 and C at 3786, if the fixed base plus A,B,C,D is "
            "triple-free, at least one target word at 3783 is exactly legal"
        ),
        "selection_rule": (
            "compatible A/B states ordered by the cardinality of their sound "
            "all-C residual R(A,B), not by raw A/B pair survivors; ascending "
            "candidate-list indices deterministically break cutoff ties"
        ),
        "scope": (
            "exact for 12 selected A/B states only; not all 865674 compatible "
            "A/B states, not level-uniform, and not an unconditional theorem"
        ),
        "strategy_relation": (
            "the result is all-choice robustness in this finite slice; a fatal "
            "assignment elsewhere would not alone disprove a winning selector"
        ),
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(base),
            "target_survivors_before_replacements": len(base_survivors),
            "placed_set_sha256": point_set_sha256(base),
            "removed_interiors_sha256": point_set_sha256(removed),
        },
        "variable_gaps": [
            {
                "role": role,
                "segment": gap,
                "schedule_rank_zero_based": schedule_ranks[index],
                "step": st["parent_word"][gap],
                "domain_size": len(gap_domains[index]),
                "unary_legal_words": len(compact_choices[index]),
                "candidate_site_universe": len(gap_point_sets[index]),
            }
            for index, (role, gap) in enumerate(
                zip(("A", "B", "C", "D"), GAPS)
            )
        ],
        "target_effect_model": {
            "added_site_universe": len(pool),
            "nonzero_added_pair_target_masks": len(pair_target_mask),
            "base_secant_bad_site_pairs": len(base_bad_pairs),
        },
        "sound_d_interface_quotient": {
            "other_site_universe": other_count,
            "other_pair_bits": other_count * (other_count - 1) // 2,
            "d_site_universe": len(d_point_universe),
            "target_mask_classes": len(target_signature_counts),
            "target_plus_cross_effect_classes": len(effect_signature_counts),
            "full_sound_interface_classes": len(full_signature_counts),
            "largest_full_class": max(full_signature_counts.values()),
            "singleton_full_classes": sum(
                count == 1 for count in full_signature_counts.values()
            ),
            "bad_other_single_count_range": [
                min(bad_single_counts),
                max(bad_single_counts),
            ],
            "bad_other_pair_count_range": [
                min(bad_pair_counts),
                max(bad_pair_counts),
            ],
            "fields": [
                "D-only target-poison mask",
                "per-other-site D--q target cross-mask vector",
                "forbidden other-site set",
                "forbidden other-site-pair set",
            ],
            "conclusion": (
                "the exact quotient is finite but gives negligible compression: "
                "17837 unary-legal D words yield 17821 interfaces, comprising "
                "17805 singletons and 16 doubletons"
            ),
        },
        "all_c_residual_census": {
            "compatible_ab_pairs": compatible_ab,
            "states_retained": CENSUS_STATES,
            "minimum_residual": minimum_all_c_residual,
            "states_with_coarse_zero_d_core": census_states_with_zero,
            "coarse_zero_abd_cores": census_core_count,
            "unrefined_cores_outside_first_twelve": (
                census_core_count - certified_core_count
            ),
        },
        "first_twelve_result": {
            "states": state_results,
            "coarse_zero_abd_cores": certified_core_count,
            "abd_incompatible_cores": total_incompatible_abd,
            "abd_exact_refined_cores": total_exact_refined_cores,
            "compatible_c_assignments_checked": total_compatible_c_assignments,
            "all_coarse_zero_cores_discharged": True,
            "logic": (
                "non-core D choices retain a word under the all-C "
                "overapproximation; every core D was either ABD-incompatible "
                "or checked against every compatible C"
            ),
        },
        "minimum_reachable_refined_core": {
            "target_survivors": global_minimum,
            "state_rank": minimum_state_rank,
            "candidate_list_indices": list(minimum_candidate_indices),
            "domain_indices": list(minimum_domain_indices),
            "words": [list(word) for word in minimum_words],
        },
        "timing_seconds": round(finished - started, 3),
        "input_sha256": {
            "checker": file_sha256(Path(__file__).resolve()),
            "level4_walk_data": file_sha256(ROOT / "viz/walk3d-data.json"),
            "L5_pickle": file_sha256(ROOT / "gate2-l7-construction-L5.pkl"),
            "L6_pickle": file_sha256(ROOT / "gate2-l7-construction-L6.pkl"),
            "L7_pickle": file_sha256(ROOT / "gate2-l7-construction-L7.pkl"),
            "connector_domains4": file_sha256(ROOT / "connector_domains4.pkl"),
            "dstar5_fragile": file_sha256(ROOT / "dstar5_fragile.pkl"),
            "effective_menu": canonical_json_sha256(MENU),
            "effective_target_domain": canonical_json_sha256(target_domain),
            "effective_variable_domains": [
                canonical_json_sha256(domain) for domain in gap_domains
            ],
            "dependencies": {
                name: file_sha256(ROOT / name)
                for name in (
                    "gate_run.py",
                    "search193.py",
                    "amplify_rich.py",
                    "imbricate193.py",
                    "design/salvage_gate.py",
                )
            },
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
