#!/usr/bin/env python3
"""Exact non-jamming certificate for the three-gap L7 backward cone.

Under the fragile-first schedule, vary gaps 3782, 3784 and 3786 while freezing
every other point present before target segment 3783.  A direct product has
1,444,455,936 unary-legal assignments.  This checker avoids that enumeration by
unioning *all* possible third-gap poison effects.  Even that sound
overapproximation leaves at least six target words for every compatible choice
of the first two gaps.

Run with one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_three_gap_gate.py

This is an exact finite cone certificate, not a level-uniform safety game.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from l7_backward_cone import (  # noqa: E402
    canonical_json_sha256,
    file_sha256,
    placed_set_sha256,
    poisoned_atoms,
    survivor_indices,
)
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    compute_poison,
    mask_sha256,
    midpoint,
    primitive,
    replay_stitch,
    sub,
)


LEVEL = 7
TARGET = 3783
GAPS = (3782, 3784, 3786)
EXPECTED = {
    "base_points": 70_328,
    "removed_interiors": 6,
    "base_survivors": 1_324,
    "unary_legal": (649, 1_288, 1_728),
    "added_sites": 267,
    "raw_ab_pairs": 835_912,
    "compatible_ab_pairs": 789_797,
    "raw_triples": 1_444_455_936,
    "base_bad_site_pairs": 456,
    "nonzero_target_pair_masks": 3_725,
    "minimum_pair_survivors": 76,
    "uniform_immune_lower_bound": 6,
    "tight_pair_domain_indices": (1386, 2029),
    "tight_pair_words": ((102, 80, 108, 78), (106, 108, 52, 103)),
    "immune_target_indices": (1220, 2177, 2508, 8241, 8242, 8771),
    "actual_candidate_list_indices": (0, 0, 1),
    "actual_target_survivors": 262,
}


def collinear(a, b, c):
    x = sub(b, a)
    y = sub(c, a)
    return (
        x[1] * y[2] == x[2] * y[1]
        and x[2] * y[0] == x[0] * y[2]
        and x[0] * y[1] == x[1] * y[0]
    )


def fixed_width_mask_bytes(mask, width):
    return mask.to_bytes((width + 7) // 8, "little")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-known-assertions", action="store_true")
    args = parser.parse_args()
    if not __debug__:
        raise SystemExit("certificate assertions require normal Python; do not use -O")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    started = time.time()
    doms, _d24 = load_domains()
    st, target_rank, actual_points, actual_births = replay_stitch(LEVEL, TARGET)
    schedule_ranks = {gap: st["order"].index(gap) for gap in GAPS}
    assert list(schedule_ranks.values()) == sorted(schedule_ranks.values())
    assert all(rank < target_rank for rank in schedule_ranks.values())

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
    target_base_poisoned = poisoned_atoms(target_info)
    base_survivors = survivor_indices(target_model, target_base_poisoned)
    survivor_position = {
        word_index: bit for bit, word_index in enumerate(base_survivors)
    }
    full = (1 << len(base_survivors)) - 1

    candidates = []
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
        choices = []
        for word_index in survivor_indices(model, poison):
            choices.append(
                (
                    word_index,
                    domain[word_index],
                    tuple(word_interiors(st["anchors"][gap], domain[word_index])),
                )
            )
        candidates.append(choices)
        gap_domains.append(domain)

    pool = sorted(
        {point for choices in candidates for _wi, _word, points in choices for point in points}
    )
    point_id = {point: index for index, point in enumerate(pool)}
    compact_choices = [
        [
            (wi, word, tuple(point_id[point] for point in points))
            for wi, word, points in choices
        ]
        for choices in candidates
    ]

    # Atom-to-word coverage on target words surviving the fixed base.
    atom_word_mask = [0] * len(target_model["atom_desc"])
    for word_index in base_survivors:
        bit = 1 << survivor_position[word_index]
        for atom in target_model["word_atoms"][word_index]:
            atom_word_mask[atom] |= bit

    target_site_mask = {
        add(target_start, offset): atom_word_mask[atom]
        for offset, atom in target_model["site_id"].items()
    }

    # U_x point effects: target-line incidence, collision, and a fixed-base/new
    # secant through a target candidate site.
    unary_point_mask = [0] * len(pool)
    directions = list(target_model["line_by_direction"].items())
    for point_index, point in enumerate(pool):
        relative = sub(point, target_start)
        mask = target_site_mask.get(point, 0)
        for direction, by_moment in directions:
            moment = (
                relative[1] * direction[2] - relative[2] * direction[1],
                relative[2] * direction[0] - relative[0] * direction[2],
                relative[0] * direction[1] - relative[1] * direction[0],
            )
            atom = by_moment.get(moment)
            if atom is not None:
                mask |= atom_word_mask[atom]
        unary_point_mask[point_index] = mask

    for site, site_mask in target_site_mask.items():
        base_directions = {primitive(sub(point, site)) for point in base}
        for point_index, point in enumerate(pool):
            if point == site or primitive(sub(point, site)) in base_directions:
                unary_point_mask[point_index] |= site_mask

    # Q_xy: target candidate sites on secants through two added sites.
    pair_target = {}
    target_sites = list(target_site_mask.items())
    for first, point in enumerate(pool):
        for second in range(first + 1, len(pool)):
            other = pool[second]
            mask = 0
            for site, site_mask in target_sites:
                if collinear(point, other, site):
                    mask |= site_mask
            if mask:
                pair_target[(first, second)] = mask

    # Cross choices are globally incompatible if two added sites collide or
    # their line already contains a fixed-base point.
    base_bad = set()
    for first, point in enumerate(pool):
        base_directions = {primitive(sub(old, point)) for old in base}
        for second in range(first + 1, len(pool)):
            if primitive(sub(pool[second], point)) in base_directions:
                base_bad.add((first, second))

    def point_pair_mask(first, second):
        if first == second:
            return target_site_mask.get(pool[first], 0)
        if first > second:
            first, second = second, first
        return pair_target.get((first, second), 0)

    def choice_unary(points):
        mask = 0
        for point in points:
            mask |= unary_point_mask[point]
        for first, second in combinations(points, 2):
            mask |= point_pair_mask(first, second)
        return mask

    choice_masks = [
        [choice_unary(choice[2]) for choice in choices]
        for choices in compact_choices
    ]

    def cross_mask(first_points, second_points):
        mask = 0
        for first in first_points:
            for second in second_points:
                mask |= point_pair_mask(first, second)
        return mask

    def pair_compatible(first_points, second_points):
        if set(first_points) & set(second_points):
            return False
        for first in first_points:
            for second in second_points:
                key = (first, second) if first < second else (second, first)
                if key in base_bad:
                    return False

        joined = first_points + second_points
        split = len(first_points)
        for i, j, k in combinations(range(len(joined)), 3):
            if k < split or i >= split:
                continue
            if collinear(pool[joined[i]], pool[joined[j]], pool[joined[k]]):
                return False
        return True

    def triple_mixed_compatible(first_points, second_points, third_points):
        return not any(
            collinear(pool[first], pool[second], pool[third])
            for first in first_points
            for second in second_points
            for third in third_points
        )

    # Independent exact decomposition check on the three recorded choices.
    original_list_indices = []
    for gap_index, gap in enumerate(GAPS):
        matches = [
            index
            for index, choice in enumerate(compact_choices[gap_index])
            if choice[1] == st["words"][gap]
        ]
        assert len(matches) == 1
        original_list_indices.append(matches[0])
    original_points = [
        compact_choices[index][choice_index][2]
        for index, choice_index in enumerate(original_list_indices)
    ]
    assert all(
        pair_compatible(original_points[i], original_points[j])
        for i, j in combinations(range(3), 2)
    )
    assert triple_mixed_compatible(*original_points)
    original_mask = 0
    for gap_index, choice_index in enumerate(original_list_indices):
        original_mask |= choice_masks[gap_index][choice_index]
    for i, j in combinations(range(3), 2):
        original_mask |= cross_mask(original_points[i], original_points[j])

    direct_info = compute_poison(
        target_model,
        target_start,
        midpoint(target_start, st["anchors"][TARGET + 1]),
        actual_points,
        actual_births,
        LEVEL,
    )
    direct_poisoned = poisoned_atoms(direct_info)
    direct_survivors = set(survivor_indices(target_model, direct_poisoned))
    decomposed_survivors = {
        word_index
        for bit, word_index in enumerate(base_survivors)
        if not ((original_mask >> bit) & 1)
    }
    assert direct_survivors == decomposed_survivors

    # All possible C effects, factored by A and by B.  The two unions may use
    # different C choices and include globally incompatible C choices, so their
    # union is intentionally an overapproximation of every actual third choice.
    all_third_unary = 0
    for mask in choice_masks[2]:
        all_third_unary |= mask

    potential_a = []
    for first_choice in compact_choices[0]:
        mask = all_third_unary
        for third_choice in compact_choices[2]:
            mask |= cross_mask(first_choice[2], third_choice[2])
        potential_a.append(mask)

    potential_b = []
    for second_choice in compact_choices[1]:
        mask = all_third_unary
        for third_choice in compact_choices[2]:
            mask |= cross_mask(second_choice[2], third_choice[2])
        potential_b.append(mask)

    raw_ab_pairs = len(compact_choices[0]) * len(compact_choices[1])
    compatible_relation = bytearray((raw_ab_pairs + 7) // 8)
    immune_count_stream = hashlib.sha256()
    compatible_ab = 0
    minimum_pair_survivors = len(base_survivors) + 1
    minimum_immune = len(base_survivors) + 1
    tight_record = None

    for first_index, first_choice in enumerate(compact_choices[0]):
        first_points = first_choice[2]
        first_unary = choice_masks[0][first_index]
        for second_index, second_choice in enumerate(compact_choices[1]):
            second_points = second_choice[2]
            if not pair_compatible(first_points, second_points):
                continue
            position = first_index * len(compact_choices[1]) + second_index
            compatible_relation[position >> 3] |= 1 << (position & 7)
            compatible_ab += 1
            pair_mask = (
                first_unary
                | choice_masks[1][second_index]
                | cross_mask(first_points, second_points)
            )
            pair_survivors = full & ~pair_mask
            minimum_pair_survivors = min(
                minimum_pair_survivors, pair_survivors.bit_count()
            )
            immune = pair_survivors & ~(
                potential_a[first_index] | potential_b[second_index]
            )
            immune_count = immune.bit_count()
            immune_count_stream.update(immune_count.to_bytes(2, "little"))
            if immune_count < minimum_immune:
                minimum_immune = immune_count
                tight_record = (first_index, second_index, immune)

    assert tight_record is not None
    tight_first, tight_second, tight_mask = tight_record
    tight_first_choice = compact_choices[0][tight_first]
    tight_second_choice = compact_choices[1][tight_second]
    immune_target_indices = tuple(
        base_survivors[bit]
        for bit in range(len(base_survivors))
        if (tight_mask >> bit) & 1
    )
    raw_triples = math.prod(len(choices) for choices in compact_choices)
    finished = time.time()

    known_assertions = not args.no_known_assertions
    if known_assertions:
        assert len(base) == EXPECTED["base_points"]
        assert len(removed) == EXPECTED["removed_interiors"]
        assert len(base_survivors) == EXPECTED["base_survivors"]
        assert tuple(map(len, compact_choices)) == EXPECTED["unary_legal"]
        assert len(pool) == EXPECTED["added_sites"]
        assert raw_ab_pairs == EXPECTED["raw_ab_pairs"]
        assert compatible_ab == EXPECTED["compatible_ab_pairs"]
        assert raw_triples == EXPECTED["raw_triples"]
        assert len(base_bad) == EXPECTED["base_bad_site_pairs"]
        assert len(pair_target) == EXPECTED["nonzero_target_pair_masks"]
        assert minimum_pair_survivors == EXPECTED["minimum_pair_survivors"]
        assert minimum_immune == EXPECTED["uniform_immune_lower_bound"]
        assert (
            tight_first_choice[0], tight_second_choice[0]
        ) == EXPECTED["tight_pair_domain_indices"]
        assert (
            tight_first_choice[1], tight_second_choice[1]
        ) == EXPECTED["tight_pair_words"]
        assert immune_target_indices == EXPECTED["immune_target_indices"]
        assert tuple(original_list_indices) == EXPECTED["actual_candidate_list_indices"]
        assert len(direct_survivors) == EXPECTED["actual_target_survivors"]

    width = len(base_survivors)
    potential_a_digest = hashlib.sha256(
        b"".join(fixed_width_mask_bytes(mask, width) for mask in potential_a)
    ).hexdigest()
    potential_b_digest = hashlib.sha256(
        b"".join(fixed_width_mask_bytes(mask, width) for mask in potential_b)
    ).hexdigest()
    result = {
        "status": (
            "exact finite fragile-first three-gap certificate: "
            "uniform target-survivor lower bound six"
        ),
        "known_assertions_passed": known_assertions,
        "level": LEVEL,
        "schedule": "fragile-first",
        "target_segment": TARGET,
        "target_schedule_rank_zero_based": target_rank,
        "target_step": target_step,
        "target_domain_size": len(target_domain),
        "variable_gaps": [
            {
                "segment": gap,
                "schedule_rank_zero_based": schedule_ranks[gap],
                "step": st["parent_word"][gap],
                "domain_size": len(gap_domains[index]),
                "unary_legal_words": len(compact_choices[index]),
            }
            for index, gap in enumerate(GAPS)
        ],
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(base),
            "target_survivors_before_replacements": len(base_survivors),
            "placed_set_sha256": placed_set_sha256(base),
            "removed_interiors_sha256": placed_set_sha256(removed),
            "target_base_survivor_mask_sha256": mask_sha256(
                base_survivors, len(target_domain)
            ),
        },
        "choice_model": {
            "added_site_universe": len(pool),
            "base_secant_bad_site_pairs": len(base_bad),
            "nonzero_added_pair_target_masks": len(pair_target),
            "raw_ab_pairs": raw_ab_pairs,
            "compatible_ab_pairs": compatible_ab,
            "raw_three_gap_assignments_avoided": raw_triples,
            "minimum_ab_pair_survivors": minimum_pair_survivors,
            "compatible_ab_relation_sha256": hashlib.sha256(
                compatible_relation
            ).hexdigest(),
            "compatible_ab_immune_count_stream_sha256": (
                immune_count_stream.hexdigest()
            ),
            "potential_a_mask_stream_sha256": potential_a_digest,
            "potential_b_mask_stream_sha256": potential_b_digest,
        },
        "uniform_certificate": {
            "target_survivor_lower_bound": minimum_immune,
            "tight_pair_candidate_list_indices": [tight_first, tight_second],
            "tight_pair_domain_indices": [
                tight_first_choice[0], tight_second_choice[0]
            ],
            "tight_pair_words": [
                list(tight_first_choice[1]), list(tight_second_choice[1])
            ],
            "immune_target_domain_indices": list(immune_target_indices),
            "immune_target_mask_sha256": mask_sha256(
                immune_target_indices, len(target_domain)
            ),
            "logic": (
                "for each compatible (a,b), union every unary-legal c effect "
                "and every a-c/b-c target secant; this overapproximates every "
                "actual third choice and still leaves at least six words"
            ),
        },
        "actual_choice_decomposition_crosscheck": {
            "candidate_list_indices": original_list_indices,
            "direct_survivors": len(direct_survivors),
            "decomposed_survivors": len(decomposed_survivors),
            "survivor_sets_equal": True,
        },
        "scope": (
            "frozen three-gap cone in the legal-choice game; not a deterministic-selector "
            "claim, a cross-level fixed point, or an all-history availability theorem"
        ),
        "timing_seconds": round(finished - started, 3),
        "input_sha256": {
            "checker": file_sha256(Path(__file__).resolve()),
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
                    "fast_legal.py",
                    "search193.py",
                    "design/salvage_gate.py",
                    "design/l7_backward_cone.py",
                )
            },
        },
        "unary_legal_mask_sha256": [
            mask_sha256(
                [choice[0] for choice in choices], len(gap_domains[index])
            )
            for index, choices in enumerate(compact_choices)
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
