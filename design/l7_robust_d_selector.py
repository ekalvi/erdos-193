#!/usr/bin/env python3
"""Exact fixed-D selector certificate in the frozen L7 backward cone.

The target is segment 3783 of the recorded fragile-first L7 construction.
Let ``P0`` be the exact pre-target point set after removing the recorded
interiors of gaps 3782, 3784, 3786, and 3785.  Write A, B, C for replacement
words at the first three gaps and D for a replacement at gap 3785.

This checker rebuilds every domain and mask from the pinned construction
pickles and proves the following finite statement:

    There is a unary-legal D such that, for every unary-legal A and B for
    which P0 union A union B is triple-free, at least 45 target words survive
    D and the union of the target-poisoning effects of every unary-legal C.

The all-C union deliberately ignores compatibility.  Thus the computed
quantifier is stronger than the strategy-relevant implication

    exists D, for all A,B,C,
        valid_distinct_triple_free(P0 plus A plus B plus C plus D)
        implies exists a legal target word.

All connector-interior loops are length-generic.  Target illegality is
partitioned exactly into site atoms (collision or a secant through two old
points) and line atoms (an old point on a line through two target interiors).
Effects from the fixed base, within each replacement word, and between every
pair of replacement words are all included.

Scope warning: P0 freezes every other connector placed before the target to
its recorded L7 choice, including choices made after the early D stitch.  The
fixed word below can be precommitted in this one finite cone, but this is not
an online all-history selector, a successor-state invariant, a cross-level
certificate, or an unconditional proof of Erdos #193.

The implementation is single-process.  Run it on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_robust_d_selector.py \
        > design/l7-robust-d-selector-summary.json
"""

from __future__ import annotations

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
A_GAP, B_GAP, C_GAP, D_GAP = GAPS = (3782, 3784, 3786, 3785)
FIXED_D_CANDIDATE_INDEX = 2950

EXPECTED_INPUT_SHA256 = {
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
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
    "amplify193.py": (
        "f9950c4d8db2507478002841568dc0b6fef883eb0597d90db7971f87e4302ef0"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
}

EXPECTED = {
    "target_schedule_rank": 16_790,
    "schedule_ranks": (8_828, 8_829, 8_830, 433),
    "steps": (123, 123, 123, 20),
    "target_step": 122,
    "actual_pre_target_points": 70_334,
    "removed_interiors": 9,
    "fixed_base_points": 70_325,
    "fixed_base_sha256": (
        "fd226a96108e94e80d133b644e6df463e532362209bbdd6ed826fe5873a6c757"
    ),
    "removed_sha256": (
        "b920f2f25e75d4f06e7db9bb738b739d8f18d3b5365aca9feabf67f8dd82beac"
    ),
    "target_domain_size": 9_046,
    "target_base_survivors": 1_394,
    "variable_domain_sizes": (2_570, 2_570, 2_570, 47_467),
    "unary_legal": (651, 1_408, 1_802, 17_837),
    "added_site_universe": 442,
    "gap_site_universes": (76, 99, 102, 204),
    "nonzero_target_pair_masks": 6_852,
    "base_secant_bad_site_pairs": 620,
    "effective_menu_sha256": (
        "bd5fd545baa5ff0987cd0607b6e6ca85c143541b22bf460c4815e1f0c49e3f5d"
    ),
    "effective_target_domain_sha256": (
        "664ef26059b048dfe8845dc76f00bd919044f312d9a64ec43e643b4d6275e68d"
    ),
    "effective_variable_domain_sha256": (
        "645ef82e48d325df21510adeceb1d6b501838d922cd382cfe2e8b2b77639202f",
        "645ef82e48d325df21510adeceb1d6b501838d922cd382cfe2e8b2b77639202f",
        "645ef82e48d325df21510adeceb1d6b501838d922cd382cfe2e8b2b77639202f",
        "91760e389806911292090bf3c3baea12647c8d731bbfd1b6add24da87ad833c6",
    ),
    "fixed_d_domain_index": 8_681,
    "fixed_d_word": (34, 24, 19, 22, 98),
    "fixed_d_all_c_mask_bits": 12,
    "compatible_ab_pairs": 865_674,
    "minimum_all_c_residual_before_d": 53,
    "minimum_sound_floor": 45,
    "tight_ab_candidate_indices": (388, 215),
    "tight_ab_domain_indices": (1_465, 425),
    "tight_ab_words": (
        (102, 103, 100, 63),
        (77, 82, 102, 107),
    ),
    "tight_residual_before_d": 93,
    "tight_target_domain_indices": (
        26, 415, 492, 884, 900, 934, 982, 998, 2053, 2208, 2211,
        3105, 3107, 3110, 3114, 3126, 3129, 3132, 3660, 3676, 3722,
        3731, 3733, 3734, 3743, 3745, 3758, 3759, 7100, 7101, 7113,
        7114, 7116, 8154, 8156, 8241, 8242, 8243, 8245, 8250, 8762,
        8763, 8771, 8772, 8780,
    ),
}


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


def poisoned_atoms(info):
    return {
        index
        for index, record in enumerate(info)
        if math.isfinite(record["threshold"])
    }


def survivor_indices(model, poisoned):
    return [
        word_index
        for word_index, atoms in enumerate(model["word_atoms"])
        if not any(atom in poisoned for atom in atoms)
    ]


def collinear(a, b, c):
    return cross(sub(b, a), sub(c, a)) == (0, 0, 0)


def main():
    if not __debug__:
        raise SystemExit("certificate assertions require normal Python; do not use -O")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    started = time.time()
    observed_input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_input_sha256 == EXPECTED_INPUT_SHA256

    doms, _d24 = load_domains()
    st, target_rank, actual_points, actual_births = replay_stitch(LEVEL, TARGET)
    schedule_ranks = tuple(st["order"].index(gap) for gap in GAPS)
    steps = tuple(st["parent_word"][gap] for gap in GAPS)
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
    base_survivors = survivor_indices(
        target_model, poisoned_atoms(target_info)
    )
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
        {
            point
            for _word_index, _word, points in gap_choices
            for point in points
        }
        for gap_choices in compact_choices
    ]

    # Restrict every target atom to target words that survived the fixed base.
    atom_word_mask = [0] * len(target_model["atom_desc"])
    for word_index in base_survivors:
        bit = 1 << survivor_position[word_index]
        for atom in target_model["word_atoms"][word_index]:
            atom_word_mask[atom] |= bit
    target_site_mask = {
        add(target_start, offset): atom_word_mask[atom]
        for offset, atom in target_model["site_id"].items()
    }

    # Exact target effect of one added old point.  The site part handles a
    # collision and base--point secants; the line part handles the old point
    # lying on a line through any two target interiors.
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

    # Exact target-site effect of a secant through two added old points.
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

    # A cross-choice pair is incompatible if its secant contains a base point.
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

        # The two choices may have arbitrary connector lengths.  Check every
        # triple using points from both; within-choice triples were certified
        # when the connector domains were generated.
        joined = first_points + second_points
        split = len(first_points)
        for i, j, k in combinations(range(len(joined)), 3):
            if k < split or i >= split:
                continue
            if collinear(pool[joined[i]], pool[joined[j]], pool[joined[k]]):
                return False
        return True

    def three_choice_compatible(first_points, second_points, third_points):
        """Check triples using one interior from each of three choices."""
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

    # For each A or B, union every possible C-only and A--C/B--C target
    # effect.  C compatibility is intentionally ignored, making the survivor
    # set a sound lower bound for every compatible C.
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

    fixed_d_choice = compact_choices[3][FIXED_D_CANDIDATE_INDEX]
    fixed_d_points = fixed_d_choice[2]
    fixed_d_mask = choice_masks[3][FIXED_D_CANDIDATE_INDEX]
    # Each D--C target secant depends on one D interior and one C interior.
    # Unioning the complete C site universe therefore includes every such
    # effect, without assuming a connector length.
    for d_point in fixed_d_points:
        for c_point in gap_point_sets[2]:
            fixed_d_mask |= point_pair_target_mask(d_point, c_point)

    # Non-vacuity hygiene: the pinned D has at least one complete legal
    # continuation inside this frozen cone.  The recorded A/B/C words are all
    # unary-legal against the four-removal base; pair checks cover every
    # two-from-one/one-from-another triple, while the three-choice checks cover
    # one interior from each of three choices.  Candidate membership already
    # certifies each word against the fixed base and its intrinsic constraints.
    recorded_abc = []
    for gap_index, gap in enumerate(GAPS[:3]):
        matches = [
            (candidate_index, choice)
            for candidate_index, choice in enumerate(compact_choices[gap_index])
            if tuple(choice[1]) == tuple(st["words"][gap])
        ]
        assert len(matches) == 1
        recorded_abc.append(matches[0])
    nonvacuity_groups = [fixed_d_points] + [
        choice[2] for _candidate_index, choice in recorded_abc
    ]
    assert all(
        pair_compatible(nonvacuity_groups[first], nonvacuity_groups[second])
        for first, second in combinations(range(len(nonvacuity_groups)), 2)
    )
    assert all(
        three_choice_compatible(
            nonvacuity_groups[first],
            nonvacuity_groups[second],
            nonvacuity_groups[third],
        )
        for first, second, third in combinations(
            range(len(nonvacuity_groups)), 3
        )
    )

    fixed_d_for_a = [
        cross_target_mask(choice[2], fixed_d_points)
        for choice in compact_choices[0]
    ]
    fixed_d_for_b = [
        cross_target_mask(choice[2], fixed_d_points)
        for choice in compact_choices[1]
    ]

    compatible_ab = 0
    zero_sound_cores = 0
    minimum_all_c_residual = len(base_survivors) + 1
    minimum_floor = len(base_survivors) + 1
    minimum_record = None
    for a_index, a_choice in enumerate(compact_choices[0]):
        a_points = a_choice[2]
        for b_index, b_choice in enumerate(compact_choices[1]):
            b_points = b_choice[2]
            if not pair_compatible(a_points, b_points):
                continue
            compatible_ab += 1
            all_c_residual = full_target_mask & ~(
                choice_masks[0][a_index]
                | choice_masks[1][b_index]
                | cross_target_mask(a_points, b_points)
                | potential_c_for_a[a_index]
                | potential_c_for_b[b_index]
            )
            residual_count = all_c_residual.bit_count()
            minimum_all_c_residual = min(
                minimum_all_c_residual, residual_count
            )
            sound_survivors = all_c_residual & ~(
                fixed_d_mask
                | fixed_d_for_a[a_index]
                | fixed_d_for_b[b_index]
            )
            floor = sound_survivors.bit_count()
            if floor == 0:
                zero_sound_cores += 1
            record = (
                floor,
                a_index,
                b_index,
                residual_count,
                sound_survivors,
            )
            if minimum_record is None or record[:4] < minimum_record[:4]:
                minimum_floor = floor
                minimum_record = record

    assert minimum_record is not None
    floor, tight_a_index, tight_b_index, tight_residual, tight_mask = (
        minimum_record
    )
    tight_target_indices = tuple(
        base_survivors[bit]
        for bit in range(len(base_survivors))
        if (tight_mask >> bit) & 1
    )
    tight_a_choice = compact_choices[0][tight_a_index]
    tight_b_choice = compact_choices[1][tight_b_index]

    # Pinned source and census assertions.
    assert target_rank == EXPECTED["target_schedule_rank"]
    assert schedule_ranks == EXPECTED["schedule_ranks"]
    assert steps == EXPECTED["steps"]
    assert target_step == EXPECTED["target_step"]
    assert len(actual_points) == EXPECTED["actual_pre_target_points"]
    assert len(removed) == EXPECTED["removed_interiors"]
    assert len(base) == EXPECTED["fixed_base_points"]
    assert point_set_sha256(base) == EXPECTED["fixed_base_sha256"]
    assert point_set_sha256(removed) == EXPECTED["removed_sha256"]
    assert len(target_domain) == EXPECTED["target_domain_size"]
    assert len(base_survivors) == EXPECTED["target_base_survivors"]
    assert tuple(map(len, gap_domains)) == EXPECTED["variable_domain_sizes"]
    assert tuple(map(len, compact_choices)) == EXPECTED["unary_legal"]
    assert len(pool) == EXPECTED["added_site_universe"]
    assert tuple(map(len, gap_point_sets)) == EXPECTED["gap_site_universes"]
    assert len(pair_target_mask) == EXPECTED["nonzero_target_pair_masks"]
    assert len(base_bad_pairs) == EXPECTED["base_secant_bad_site_pairs"]
    assert canonical_json_sha256(MENU) == EXPECTED["effective_menu_sha256"]
    assert canonical_json_sha256(target_domain) == EXPECTED[
        "effective_target_domain_sha256"
    ]
    assert tuple(map(canonical_json_sha256, gap_domains)) == EXPECTED[
        "effective_variable_domain_sha256"
    ]

    # The existential D witness and universal A/B certificate.
    assert fixed_d_choice[0] == EXPECTED["fixed_d_domain_index"]
    assert fixed_d_choice[1] == EXPECTED["fixed_d_word"]
    assert fixed_d_mask.bit_count() == EXPECTED["fixed_d_all_c_mask_bits"]
    assert compatible_ab == EXPECTED["compatible_ab_pairs"]
    assert minimum_all_c_residual == EXPECTED[
        "minimum_all_c_residual_before_d"
    ]
    assert zero_sound_cores == 0
    assert minimum_floor == floor == EXPECTED["minimum_sound_floor"]
    assert (tight_a_index, tight_b_index) == EXPECTED[
        "tight_ab_candidate_indices"
    ]
    assert (tight_a_choice[0], tight_b_choice[0]) == EXPECTED[
        "tight_ab_domain_indices"
    ]
    assert (tight_a_choice[1], tight_b_choice[1]) == EXPECTED[
        "tight_ab_words"
    ]
    assert tight_residual == EXPECTED["tight_residual_before_d"]
    assert tight_target_indices == EXPECTED["tight_target_domain_indices"]

    finished = time.time()
    result = {
        "status": "exact frozen-L7 robust early-D selector certificate complete",
        "known_assertions_passed": True,
        "level": LEVEL,
        "schedule": "fragile-first",
        "target_segment": TARGET,
        "target_schedule_rank_zero_based": target_rank,
        "quantifier": (
            "there exists the pinned unary-legal D; for every unary-legal "
            "base-compatible A/B pair, at least 45 target words survive D "
            "and the union of every unary-legal C effect; therefore for every "
            "jointly legal A,B,C,D state at least one target word is legal"
        ),
        "stronger_order": (
            "exists D; forall base-compatible A,B; exists >=45 W whose "
            "target atoms stay clean for every unary C; prior-state legality "
            "remains in the implication antecedent"
        ),
        "scope": (
            "exact only in the cone with every other pre-target connector "
            "frozen to its recorded L7 choice; not an online all-history "
            "selector, successor invariant, cross-level certificate, or "
            "unconditional theorem"
        ),
        "precommitment_caveat": (
            "D is scheduled before many points in the frozen base.  This "
            "finite instance may precommit the pinned word, but the search "
            "used the recorded future base and supplies no policy for other "
            "future histories."
        ),
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(base),
            "target_domain_size": len(target_domain),
            "target_survivors_before_replacements": len(base_survivors),
            "placed_set_sha256": point_set_sha256(base),
            "removed_interiors_sha256": point_set_sha256(removed),
        },
        "variable_gaps": [
            {
                "role": role,
                "segment": gap,
                "schedule_rank_zero_based": schedule_ranks[index],
                "step": steps[index],
                "domain_size": len(gap_domains[index]),
                "unary_legal_words": len(compact_choices[index]),
                "candidate_site_universe": len(gap_point_sets[index]),
            }
            for index, (role, gap) in enumerate(
                zip(("A", "B", "C", "D"), GAPS)
            )
        ],
        "fixed_d_witness": {
            "candidate_list_index": FIXED_D_CANDIDATE_INDEX,
            "domain_index": fixed_d_choice[0],
            "word": list(fixed_d_choice[1]),
            "interiors": [list(pool[index]) for index in fixed_d_points],
            "D_only_plus_all_C_cross_mask_words": fixed_d_mask.bit_count(),
        },
        "nonvacuity_witness": {
            "valid_distinct_triple_free_with_recorded_abc": True,
            "recorded_abc_candidate_indices": [
                candidate_index for candidate_index, _choice in recorded_abc
            ],
            "recorded_abc_domain_indices": [
                choice[0] for _candidate_index, choice in recorded_abc
            ],
            "recorded_abc_words": [
                list(choice[1]) for _candidate_index, choice in recorded_abc
            ],
        },
        "universal_ab_result": {
            "compatible_pairs_checked": compatible_ab,
            "zero_sound_cores": zero_sound_cores,
            "minimum_all_C_residual_before_D": minimum_all_c_residual,
            "uniform_sound_target_floor_after_D": minimum_floor,
            "all_C_compatibility_ignored": True,
        },
        "tight_state": {
            "a_candidate_index": tight_a_index,
            "b_candidate_index": tight_b_index,
            "a_domain_index": tight_a_choice[0],
            "b_domain_index": tight_b_choice[0],
            "a_word": list(tight_a_choice[1]),
            "b_word": list(tight_b_choice[1]),
            "all_C_residual_before_D": tight_residual,
            "sound_target_floor_after_D": floor,
            "surviving_target_domain_indices": list(tight_target_indices),
        },
        "soundness_partition": [
            "base poison of target site and target-pair line atoms",
            "within-choice poison including base--choice secants",
            "cross-choice secants for A--B, A--C, B--C, A--D, B--D, C--D",
            "intrinsic target-word legality inherited from the exact domains",
        ],
        "timing_seconds": round(finished - started, 3),
        "input_sha256": {
            "checker": file_sha256(Path(__file__).resolve()),
            "files": observed_input_sha256,
            "effective_menu": canonical_json_sha256(MENU),
            "effective_target_domain": canonical_json_sha256(target_domain),
            "effective_variable_domains": [
                canonical_json_sha256(domain) for domain in gap_domains
            ],
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
