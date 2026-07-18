#!/usr/bin/env python3
"""Exact two-gap backward-cone certificate at the L7 bottleneck.

The target is L7 segment 3783 under the constructor's fragile-first schedule.
The only variable earlier connectors are its two realized path neighbours 3782
and 3784; every other point already present at the target stitch is frozen.  The
script removes the two recorded connector interiors, recomputes legality
against that fixed base, and exhausts every pair of unary-legal replacements.

No radius truncation or sampled connector menu is used.  Pair compatibility
checks every new bad-triple class, and target availability is represented by
exact site/line poison bitsets.  The implementation is single-process.  Run it
at low priority, for example:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_backward_cone.py

This is a bounded finite certificate, not a level-uniform safety invariant.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    cheb,
    compute_poison,
    cross,
    exact_cover_distance,
    midpoint,
    mask_sha256,
    primitive,
    replay_stitch,
    sub,
)


LEVEL = 7
TARGET = 3783
VARIABLE_GAPS = (3782, 3784)
EXPECTED = {
    "fixed_base_points": 70_330,
    "target_base_survivors": 1_251,
    "unary_legal": (649, 1_250),
    "raw_pairs": 811_250,
    "globally_legal_pairs": 767_711,
    "minimum_target_survivors": 59,
    "minimum_pair_indices": (1534, 1969),
    "minimum_pair_words": (
        (102, 112, 53, 102),
        (106, 59, 101, 103),
    ),
    "actual_pair_indices": (0, 1),
    "actual_pair_target_survivors": 262,
    "minimum_placed_points": 70_336,
    "minimum_residual_atom_cover": 9,
    "minimum_placed_set_sha256": (
        "8ed6459f1b4ff3caea4e4a4a2a3fdc322331b2824829b89a9fd51147a3c8201d"
    ),
}


def poisoned_atoms(info):
    return {j for j, record in enumerate(info) if math.isfinite(record["threshold"])}


def survivor_indices(model, poisoned):
    return [
        wi
        for wi, atoms in enumerate(model["word_atoms"])
        if not any(atom in poisoned for atom in atoms)
    ]


def atom_mask(indices):
    out = 0
    for index in indices:
        out |= 1 << index
    return out


def indices_from_mask(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def coverage_from_atom_mask(mask, atom_coverage):
    out = 0
    while mask:
        bit = mask & -mask
        out |= atom_coverage[bit.bit_length() - 1]
        mask ^= bit
    return out


def is_collinear(a, b, c):
    return cross(sub(b, a), sub(c, a)) == (0, 0, 0)


def placed_set_sha256(points):
    serial = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def word_atom_mask(model, word_index):
    return atom_mask(model["word_atoms"][word_index])


def point_target_atom_mask(
    point,
    base_points,
    target_start,
    target_model,
    target_sites,
):
    """Atoms newly poisoned by adding one old point to the target state."""
    out = 0

    # The new old point may lie on a line through two target interiors.
    relative = sub(point, target_start)
    for direction, by_moment in target_model["line_by_direction"].items():
        atom = by_moment.get(cross(relative, direction))
        if atom is not None:
            out |= 1 << atom

    # For every target site q, adding point p poisons q on collision or when
    # the line p--q already contains a fixed-base point.  Build one temporary
    # direction set per p, rather than retaining 174 large sets at once.
    base_directions = {primitive(sub(old, point)) for old in base_points}
    for site, atom in target_sites:
        if site == point:
            out |= 1 << atom
            continue
        if primitive(sub(site, point)) in base_directions:
            out |= 1 << atom
    return out


def pair_target_atom_mask(a, b, target_sites):
    """Target site atoms poisoned by the secant through two new old points."""
    if a == b:
        return 0
    out = 0
    for site, atom in target_sites:
        if is_collinear(a, b, site):
            out |= 1 << atom
    return out


def build_unary_choices(st, gap, base_points, base_births, doms):
    step = st["parent_word"][gap]
    domain = doms[step]
    assert len(domain) == len(set(domain))
    model = build_domain_model(domain)
    start = st["anchors"][gap]
    end = st["anchors"][gap + 1]
    info = compute_poison(
        model, start, midpoint(start, end), base_points, base_births, LEVEL
    )
    poisoned = poisoned_atoms(info)
    choices = []
    for word_index in survivor_indices(model, poisoned):
        points = tuple(word_interiors(start, domain[word_index]))
        choices.append(
            {
                "word_index": word_index,
                "word": domain[word_index],
                "points": points,
            }
        )
    return {
        "gap": gap,
        "step": step,
        "start": start,
        "end": end,
        "domain": domain,
        "domain_model": model,
        "poisoned_atoms": poisoned,
        "choices": choices,
    }


def quantiles_from_histogram(histogram, total):
    requests = (("p00", 0), ("p10", 10), ("p50", 50), ("p90", 90), ("p100", 100))
    answer = {}
    cumulative = 0
    pending = list(requests)
    for value in sorted(histogram):
        cumulative += histogram[value]
        while pending:
            label, percentile = pending[0]
            rank = 1 if percentile == 0 else (percentile * total + 99) // 100
            if cumulative < rank:
                break
            answer[label] = value
            pending.pop(0)
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-production-check",
        action="store_true",
        help="skip the independent fast_legal scan of all 9,046 target words",
    )
    parser.add_argument(
        "--no-known-assertions",
        action="store_true",
        help="report results without asserting the checked-in expected certificate",
    )
    args = parser.parse_args()

    started = time.time()
    if not __debug__:
        raise SystemExit("certificate assertions require normal Python; do not use -O")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    doms, _d24 = load_domains()
    st, target_rank, actual_points, actual_births = replay_stitch(LEVEL, TARGET)
    target_start = st["anchors"][TARGET]
    target_end = st["anchors"][TARGET + 1]

    schedule_ranks = {gap: st["order"].index(gap) for gap in VARIABLE_GAPS}
    assert all(rank < target_rank for rank in schedule_ranks.values())
    assert schedule_ranks[VARIABLE_GAPS[0]] < schedule_ranks[VARIABLE_GAPS[1]]

    removed = set()
    for gap in VARIABLE_GAPS:
        interiors = word_interiors(st["anchors"][gap], st["words"][gap])
        assert all(point in actual_points for point in interiors)
        removed.update(interiors)
    assert len(removed) == 4

    base_points = []
    base_births = []
    for point, birth in zip(actual_points, actual_births):
        if point not in removed:
            base_points.append(point)
            base_births.append(birth)
    assert len(base_points) == len(set(base_points))

    target_step = st["parent_word"][TARGET]
    target_domain = doms[target_step]
    assert len(target_domain) == len(set(target_domain))
    target_model = build_domain_model(target_domain)
    target_info = compute_poison(
        target_model,
        target_start,
        midpoint(target_start, target_end),
        base_points,
        base_births,
        LEVEL,
    )
    target_base_poisoned = poisoned_atoms(target_info)
    target_base_survivors = survivor_indices(target_model, target_base_poisoned)
    survivor_bit_by_word = {
        word_index: bit for bit, word_index in enumerate(target_base_survivors)
    }
    full_survivor_mask = (1 << len(target_base_survivors)) - 1

    atom_coverage = [0] * len(target_model["atom_desc"])
    for bit, word_index in enumerate(target_base_survivors):
        for atom in target_model["word_atoms"][word_index]:
            atom_coverage[atom] |= 1 << bit

    target_sites = [
        (add(target_start, offset), atom)
        for offset, atom in target_model["site_id"].items()
    ]

    gap_data = [
        build_unary_choices(st, gap, base_points, base_births, doms)
        for gap in VARIABLE_GAPS
    ]
    left, right = gap_data

    left_points = sorted(
        {point for choice in left["choices"] for point in choice["points"]}
    )
    right_points = sorted(
        {point for choice in right["choices"] for point in choice["points"]}
    )
    left_point_id = {point: index for index, point in enumerate(left_points)}
    right_point_id = {point: index for index, point in enumerate(right_points)}

    # Per-point target effects.  This is the expensive but finite global-secant
    # preprocessing; every fixed-base endpoint is included.
    point_atom_masks = {}
    for point in left_points + right_points:
        if point not in point_atom_masks:
            point_atom_masks[point] = point_target_atom_mask(
                point,
                base_points,
                target_start,
                target_model,
                target_sites,
            )

    # Does the cross-connector line x--y contain a fixed-base point?  Retain
    # only a 76x93 Boolean table; each large direction set is discarded after
    # its row is constructed.
    base_cross_hit = []
    for point in left_points:
        directions = {primitive(sub(old, point)) for old in base_points}
        row = []
        for other in right_points:
            row.append(
                other == point or primitive(sub(other, point)) in directions
            )
        base_cross_hit.append(row)

    pair_target_atoms = []
    pair_target_bits = []
    for point in left_points:
        atom_row = []
        bit_row = []
        for other in right_points:
            atoms = pair_target_atom_mask(point, other, target_sites)
            atom_row.append(atoms)
            bit_row.append(coverage_from_atom_mask(atoms, atom_coverage))
        pair_target_atoms.append(atom_row)
        pair_target_bits.append(bit_row)

    same_word_pair_cache = {}

    def decorate_choices(data, point_ids):
        decorated = []
        for choice in data["choices"]:
            atoms = 0
            for point in choice["points"]:
                atoms |= point_atom_masks[point]
            for a, b in combinations(choice["points"], 2):
                key = (a, b) if a <= b else (b, a)
                effect = same_word_pair_cache.get(key)
                if effect is None:
                    effect = pair_target_atom_mask(a, b, target_sites)
                    same_word_pair_cache[key] = effect
                atoms |= effect
            decorated.append(
                (
                    choice["word_index"],
                    choice["word"],
                    choice["points"],
                    tuple(point_ids[point] for point in choice["points"]),
                    atoms,
                    coverage_from_atom_mask(atoms, atom_coverage),
                )
            )
        return decorated

    left_choices = decorate_choices(left, left_point_id)
    right_choices = decorate_choices(right, right_point_id)

    def pair_compatible(left_choice, right_choice):
        left_concrete = left_choice[2]
        right_concrete = right_choice[2]
        left_ids = left_choice[3]
        right_ids = right_choice[3]

        # One fixed-base point and one point from each replacement, including
        # cross collisions as the degenerate case.
        for left_id in left_ids:
            row = base_cross_hit[left_id]
            for right_id in right_ids:
                if row[right_id]:
                    return False

        # Two interiors from one replacement and one from the other.
        for a, b in combinations(left_concrete, 2):
            for c in right_concrete:
                if is_collinear(a, b, c):
                    return False
        for a in left_concrete:
            for b, c in combinations(right_concrete, 2):
                if is_collinear(a, b, c):
                    return False
        return True

    preprocessing_finished = time.time()
    raw_pairs = len(left_choices) * len(right_choices)
    compatible_pair_mask = bytearray((raw_pairs + 7) // 8)
    legal_survivor_stream = hashlib.sha256()
    globally_legal_pairs = 0
    survivor_sum = 0
    survivor_histogram = Counter()
    minimum_survivors = len(target_base_survivors) + 1
    minimum_pairs = []
    minimum_mask = None
    minimum_atom_mask = None
    actual_pair_survivors = None

    actual_indices = []
    for data, gap in zip(gap_data, VARIABLE_GAPS):
        actual_indices.append(data["domain"].index(st["words"][gap]))
    actual_indices = tuple(actual_indices)

    for left_position, left_choice in enumerate(left_choices):
        left_word_index = left_choice[0]
        for right_position, right_choice in enumerate(right_choices):
            if not pair_compatible(left_choice, right_choice):
                continue
            pair_position = left_position * len(right_choices) + right_position
            compatible_pair_mask[pair_position >> 3] |= 1 << (pair_position & 7)
            globally_legal_pairs += 1

            cross_atoms = 0
            cross_bits = 0
            for left_id in left_choice[3]:
                atom_row = pair_target_atoms[left_id]
                bit_row = pair_target_bits[left_id]
                for right_id in right_choice[3]:
                    cross_atoms |= atom_row[right_id]
                    cross_bits |= bit_row[right_id]

            killed = left_choice[5] | right_choice[5] | cross_bits
            survivors = full_survivor_mask & ~killed
            count = survivors.bit_count()
            legal_survivor_stream.update(count.to_bytes(2, "little"))
            survivor_sum += count
            survivor_histogram[count] += 1

            pair_indices = (left_word_index, right_choice[0])
            if pair_indices == actual_indices:
                actual_pair_survivors = count
            if count < minimum_survivors:
                minimum_survivors = count
                minimum_pairs = [pair_indices]
                minimum_mask = survivors
                minimum_atom_mask = (
                    atom_mask(target_base_poisoned)
                    | left_choice[4]
                    | right_choice[4]
                    | cross_atoms
                )
            elif count == minimum_survivors:
                minimum_pairs.append(pair_indices)

    enumeration_finished = time.time()
    assert minimum_mask is not None and minimum_atom_mask is not None
    minimum_pair = minimum_pairs[0]
    minimum_words = (
        left["domain"][minimum_pair[0]],
        right["domain"][minimum_pair[1]],
    )
    minimum_points = (
        base_points
        + word_interiors(left["start"], minimum_words[0])
        + word_interiors(right["start"], minimum_words[1])
    )
    minimum_hash = placed_set_sha256(minimum_points)
    minimum_target_indices = [
        target_base_survivors[bit] for bit in indices_from_mask(minimum_mask)
    ]

    # Exact distance of the minimum state from arbitrary atom fatality.
    minimum_poisoned = set(indices_from_mask(minimum_atom_mask))
    residual_cover = exact_cover_distance(
        [target_model["word_atoms"][wi] for wi in minimum_target_indices],
        minimum_poisoned,
        30.0,
    )

    production = {"skipped": args.skip_production_check}
    if not args.skip_production_check:
        store = Store(base_points)
        left_min_points = word_interiors(left["start"], minimum_words[0])
        right_min_points = word_interiors(right["start"], minimum_words[1])
        left_ok = word_legal_fast(
            left["start"], minimum_words[0], store, {}, MENU
        )
        assert left_ok
        store.add_many(left_min_points)
        right_ok = word_legal_fast(
            right["start"], minimum_words[1], store, {}, MENU
        )
        assert right_ok
        store.add_many(right_min_points)

        memo = {}
        production_survivors = []
        for wi, word in enumerate(target_domain):
            if word_legal_fast(target_start, word, store, memo, MENU):
                production_survivors.append(wi)
        assert production_survivors == minimum_target_indices
        production = {
            "skipped": False,
            "replacement_words_sequentially_legal": True,
            "target_words_checked": len(target_domain),
            "target_survivors": len(production_survivors),
            "survivor_indices_match_atom_model": True,
        }

    finished = time.time()
    known_assertions = not args.no_known_assertions
    if known_assertions:
        assert len(base_points) == EXPECTED["fixed_base_points"]
        assert len(target_base_survivors) == EXPECTED["target_base_survivors"]
        assert tuple(len(data["choices"]) for data in gap_data) == EXPECTED["unary_legal"]
        assert raw_pairs == EXPECTED["raw_pairs"]
        assert globally_legal_pairs == EXPECTED["globally_legal_pairs"]
        assert minimum_survivors == EXPECTED["minimum_target_survivors"]
        assert minimum_pair == EXPECTED["minimum_pair_indices"]
        assert minimum_words == EXPECTED["minimum_pair_words"]
        assert actual_indices == EXPECTED["actual_pair_indices"]
        assert actual_pair_survivors == EXPECTED["actual_pair_target_survivors"]
        assert len(minimum_points) == EXPECTED["minimum_placed_points"]
        assert len(minimum_points) == len(set(minimum_points))
        assert minimum_hash == EXPECTED["minimum_placed_set_sha256"]
        assert residual_cover["status"] == "exact"
        assert residual_cover["minimum_or_upper"] == EXPECTED["minimum_residual_atom_cover"]
        if not args.skip_production_check:
            assert production["target_survivors"] == EXPECTED["minimum_target_survivors"]

    result = {
        "status": (
            "exact finite fragile-first two-gap certificate; "
            "not a uniform safety proof"
        ),
        "known_assertions_passed": known_assertions,
        "level": LEVEL,
        "target_segment": TARGET,
        "target_step": target_step,
        "target_schedule_rank_zero_based": target_rank,
        "schedule": "fragile-first",
        "target_domain_size": len(target_domain),
        "variable_gaps": [
            {
                "segment": data["gap"],
                "step": data["step"],
                "schedule_rank_zero_based": schedule_ranks[data["gap"]],
                "domain_size": len(data["domain"]),
                "unary_legal_words": len(data["choices"]),
                "unique_candidate_interior_sites": (
                    len(left_points) if index == 0 else len(right_points)
                ),
                "actual_word_index": actual_indices[index],
            }
            for index, data in enumerate(gap_data)
        ],
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(base_points),
            "target_survivors_before_replacements": len(target_base_survivors),
            "placed_set_sha256": placed_set_sha256(base_points),
            "removed_interiors_sha256": placed_set_sha256(removed),
            "target_base_survivor_mask_sha256": mask_sha256(
                target_base_survivors, len(target_domain)
            ),
        },
        "pair_exhaustion": {
            "raw_unary_legal_pairs": raw_pairs,
            "globally_triple_free_pairs": globally_legal_pairs,
            "globally_illegal_pairs": raw_pairs - globally_legal_pairs,
            "fatal_target_pairs": survivor_histogram.get(0, 0),
            "target_survivor_sum": survivor_sum,
            "compatible_pair_relation_sha256": hashlib.sha256(
                compatible_pair_mask
            ).hexdigest(),
            "legal_pair_survivor_count_stream_sha256": (
                legal_survivor_stream.hexdigest()
            ),
            "target_survivor_quantiles": quantiles_from_histogram(
                survivor_histogram, globally_legal_pairs
            ),
        },
        "actual_pair": {
            "domain_indices": list(actual_indices),
            "target_survivors": actual_pair_survivors,
        },
        "minimum_pair": {
            "target_survivors": minimum_survivors,
            "number_of_minimizing_pairs": len(minimum_pairs),
            "domain_indices": list(minimum_pair),
            "words": [list(word) for word in minimum_words],
            "target_survivor_indices": minimum_target_indices,
            "target_survivor_mask_sha256": mask_sha256(
                minimum_target_indices, len(target_domain)
            ),
            "placed_set_sha256": minimum_hash,
            "placed_points": len(minimum_points),
            "residual_arbitrary_atom_cover": residual_cover,
        },
        "independent_production_crosscheck": production,
        "soundness_partition": [
            "unary: collision or two fixed-base endpoints with one new point",
            "unary: one fixed-base point with two interiors of one connector",
            "cross: collision between the two connector interiors",
            "cross: one fixed-base point and one interior from each connector",
            "cross: two interiors from one connector and one from the other",
            "target: fixed-base poison plus unary and cross new-point effects",
        ],
        "reachability_scope": (
            "reachable in the legal-choice game by replacing these two early "
            "connectors and retaining every other frozen pre-target choice; "
            "not claimed to follow the constructor's deterministic selector"
        ),
        "timing_seconds": {
            "preprocessing": round(preprocessing_finished - started, 3),
            "pair_enumeration": round(enumeration_finished - preprocessing_finished, 3),
            "postchecks": round(finished - enumeration_finished, 3),
            "total": round(finished - started, 3),
        },
        "input_sha256": {
            "checker": file_sha256(Path(__file__).resolve()),
            "L7_pickle": file_sha256(ROOT / "gate2-l7-construction-L7.pkl"),
            "connector_domains4": file_sha256(ROOT / "connector_domains4.pkl"),
            "dstar5_fragile": file_sha256(ROOT / "dstar5_fragile.pkl"),
            "effective_menu": canonical_json_sha256(MENU),
            "effective_target_domain": canonical_json_sha256(target_domain),
            "effective_variable_domains": [
                canonical_json_sha256(data["domain"]) for data in gap_data
            ],
            "dependencies": {
                name: file_sha256(ROOT / name)
                for name in (
                    "gate_run.py",
                    "fast_legal.py",
                    "search193.py",
                    "design/salvage_gate.py",
                )
            },
        },
        "unary_legal_mask_sha256": [
            mask_sha256(
                [choice["word_index"] for choice in data["choices"]],
                len(data["domain"]),
            )
            for data in gap_data
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
