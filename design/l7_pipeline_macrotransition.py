#!/usr/bin/env python3
"""Exact causal-pipeline probe around the L7 segment-3783 bottleneck.

This is deliberately different from ``l7_robust_d_selector.py``.  That
certificate freezes almost the complete fragile-first pre-target future.  The
present checker reconstructs the proposed inherited-tile pipeline order and
uses only the points that have actually been placed when its early guard D is
chosen.  Recorded connector words are used before that cursor; their completed
union is triple-free, so every such prefix is a legal replay.

The local pipeline order is

    D3785, A3782, B3784, target3783, G3788, C3786.

The checker installs the already discovered D/A/B words, computes the exact
target killed-word mask against this causal prefix, and proves the finite
two-ply statement

    for every exactly legal target word W,
    at least m short (length 2--4) words remain exactly legal at G,

where m is recomputed below.  The transfer includes collisions, old--old--new
secants, and old--new--new secants with endpoints anywhere in the complete
causal prefix; there is no distance truncation.  An independent full-domain
poison computation cross-checks the pinned target word and then verifies that
the resulting least short G choice leaves C available.

Scope: this is one exact state and one pinned D/A/B policy fragment.  It is not
uniform over incoming pipeline histories, does not prove that the same choices
work at another tile or level, and is not a greatest-fixed-point certificate.

Run on one low-priority core from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_pipeline_macrotransition.py
"""

from __future__ import annotations

import gc
import hashlib
import json
import math
import pickle
import sys
import time
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import FRAGILE_CUT, MENU, load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    built_walk_with_birth,
    compute_poison,
    cross,
    mask_sha256,
    midpoint,
    primitive,
    sub,
)


LEVEL = 7
TARGET = 3783
D_GAP, A_GAP, B_GAP, G_GAP, C_GAP = (3785, 3782, 3784, 3788, 3786)
PINNED = {
    D_GAP: (8681, (34, 24, 19, 22, 98), "D"),
    A_GAP: (1465, (102, 103, 100, 63), "A"),
    B_GAP: (425, (77, 82, 102, 107), "B"),
}
PINNED_TARGET_INDEX = 26

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
    "fast_legal.py": (
        "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed"
    ),
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
    "design/l7_robust_d_selector.py": (
        "502ce218a9b960b7efc39bfea3ad0ee41983f56c0d721d2098511c090e7cc4aa"
    ),
}

EXPECTED = {
    "local_ranks": (3782, 3783, 3784, 3785, 3786, 3787),
    "causal_base_points": 36_589,
    "causal_base_sha256": (
        "4b526480697bf324560aec75ead678686de50993fa84a62777bae4d77ebd24b7"
    ),
    "pretarget_points": 36_599,
    "pretarget_sha256": (
        "af23333a9b765e907a0449723fd324ad6f653e2a8babe1d7369f1a342dfc9ac8"
    ),
    "target_domain": 9_046,
    "target_survivors": 111,
    "target_poisoned_atoms": 164,
    "target_mask_sha256": (
        "be83fa5b1ca906421e85d4de2a28619a3507b4336f2d7ba807576f72ae92c13b"
    ),
    "guard_full_domain": 453_015,
    "guard_short_domain": 1_505,
    "guard_short_before_target": 1_264,
    "uniform_guard_floor": 1_153,
    "floor_target_indices": (3056,),
    "target_point_universe": 54,
    "target_pair_effects": 165,
    "pinned_full_guard_survivors": 350_509,
    "pinned_full_guard_poisoned_atoms": 62,
    "pinned_full_guard_mask_sha256": (
        "05028572b2f90ca808f4c59a8024b8730119769444778aa7718bef37e3ed130c"
    ),
    "pinned_short_guard_survivors": 1_263,
    "pinned_short_guard_mask_sha256": (
        "ddd74373c1fa65b5c7ad6534d790422121bbcdd1d5ae64258df2618beab2f990"
    ),
    "chosen_guard_index": 0,
    "chosen_guard_word": (123, 122, 123),
    "c_domain": 2_570,
    "c_survivors": 1_887,
    "c_poisoned_atoms": 22,
    "c_mask_sha256": (
        "4eb56678e4bc5b792370b0e8f8504a378a072f66f65bf61d7242a20f0c0b905f"
    ),
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def point_set_sha256(points):
    encoded = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def pipeline_schedule(state, owners, d24):
    """Inherited-tile guard/lookahead schedule, returned as a permutation."""
    tile_gaps = {}
    for gap, tile in enumerate(owners):
        tile_gaps.setdefault(tile, []).append(gap)

    guards = {}
    for tile, gaps in tile_gaps.items():
        fragile = [
            gap
            for gap in gaps
            if d24[state["parent_word"][gap]] < FRAGILE_CUT
        ]
        if fragile:
            guards[tile] = min(
                fragile,
                key=lambda gap: (d24[state["parent_word"][gap]], gap),
            )

    order = []
    placed = set()

    def place(gap):
        if gap not in placed:
            placed.add(gap)
            order.append(gap)

    if 0 in guards:
        place(guards[0])
    for tile in sorted(tile_gaps):
        if tile + 1 in guards:
            place(guards[tile + 1])
        for gap in sorted(
            tile_gaps[tile],
            key=lambda item: (d24[state["parent_word"][item]], item),
        ):
            place(gap)

    assert len(order) == len(state["parent_word"])
    assert placed == set(range(len(state["parent_word"])))
    return order, guards


def exact_survivors(model, start, end, points, births):
    info = compute_poison(
        model,
        start,
        midpoint(start, end),
        points,
        births,
        LEVEL,
    )
    poisoned = {
        atom
        for atom, record in enumerate(info)
        if math.isfinite(record["threshold"])
    }
    survivors = [
        word_index
        for word_index, atoms in enumerate(model["word_atoms"])
        if poisoned.isdisjoint(atoms)
    ]
    return survivors, poisoned


def atom_word_masks(model):
    masks = [0] * len(model["atom_desc"])
    for word_index, atoms in enumerate(model["word_atoms"]):
        bit = 1 << word_index
        for atom in atoms:
            masks[atom] |= bit
    return masks


def target_to_guard_transfer(
    target_domain,
    target_survivors,
    target_start,
    guard_model,
    guard_start,
    base_points,
    base_poisoned,
):
    """Exact added-target-word effect on the short G killed-word mask.

    ``base_points`` is triple-free and already includes D/A/B.  Site effects
    include target-point collisions, P--target secants, and target--target
    secants.  Line effects include a target point lying on a line through two
    prospective G interiors.  Thus every mixed triple in P + target + G is
    represented exactly.
    """
    word_masks = atom_word_masks(guard_model)
    full_guard_mask = (1 << len(guard_model["word_atoms"])) - 1
    base_killed = 0
    for atom in base_poisoned:
        base_killed |= word_masks[atom]

    guard_sites = [
        (add(guard_start, offset), atom)
        for offset, atom in guard_model["site_id"].items()
    ]
    site_base_directions = {}
    for site, _atom in guard_sites:
        site_base_directions[site] = {
            primitive(sub(point, site)) for point in base_points if point != site
        }

    target_points = sorted(
        {
            point
            for word_index in target_survivors
            for point in word_interiors(target_start, target_domain[word_index])
        }
    )
    guard_directions = list(guard_model["line_by_direction"].items())
    unary = {}
    for point in target_points:
        effect = 0
        relative = sub(point, guard_start)
        for direction, by_moment in guard_directions:
            atom = by_moment.get(cross(relative, direction))
            if atom is not None:
                effect |= word_masks[atom]
        for site, atom in guard_sites:
            if point == site or primitive(sub(point, site)) in site_base_directions[site]:
                effect |= word_masks[atom]
        unary[point] = effect

    @lru_cache(maxsize=None)
    def pair_effect(first, second):
        effect = 0
        for site, atom in guard_sites:
            if cross(sub(first, site), sub(second, site)) == (0, 0, 0):
                effect |= word_masks[atom]
        return effect

    counts = {}
    survivor_masks = {}
    for word_index in target_survivors:
        points = tuple(word_interiors(target_start, target_domain[word_index]))
        effect = 0
        for point in points:
            effect |= unary[point]
        for first_index, first in enumerate(points):
            for second in points[first_index + 1 :]:
                a, b = (second, first) if second < first else (first, second)
                effect |= pair_effect(a, b)
        survivor_mask = full_guard_mask & ~(base_killed | effect)
        survivor_masks[word_index] = survivor_mask
        counts[word_index] = survivor_mask.bit_count()

    return {
        "base_killed_mask": base_killed,
        "counts": counts,
        "survivor_masks": survivor_masks,
        "target_point_universe": len(target_points),
        "target_pair_effect_cache": pair_effect.cache_info().currsize,
    }


def main():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    started = time.time()
    observed_input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_input_sha256 == EXPECTED_INPUT_SHA256
    state_path = ROOT / f"gate2-l7-construction-L{LEVEL}.pkl"
    with state_path.open("rb") as handle:
        state = pickle.load(handle)
    data = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    owners = data["levels"][LEVEL - 1]["parents"][:-1]
    assert len(owners) == len(state["parent_word"])
    domains, d24 = load_domains()
    order, guards = pipeline_schedule(state, owners, d24)

    local_order = tuple(order.index(gap) for gap in (D_GAP, A_GAP, B_GAP, TARGET, G_GAP, C_GAP))
    assert local_order == tuple(range(local_order[0], local_order[0] + 6))
    assert local_order == EXPECTED["local_ranks"]
    d_rank = order.index(D_GAP)

    parent_points, parent_births = built_walk_with_birth(LEVEL - 1)
    assert state["anchors"] == [apply(M_BAL3, point) for point in parent_points]
    causal_points = list(state["anchors"])
    causal_births = list(parent_births)
    for gap in order[:d_rank]:
        interiors = word_interiors(state["anchors"][gap], state["words"][gap])
        causal_points.extend(interiors)
        causal_births.extend([LEVEL] * len(interiors))
    assert len(causal_points) == len(causal_births) == len(set(causal_points))
    causal_base_hash = point_set_sha256(causal_points)
    assert len(causal_points) == EXPECTED["causal_base_points"]
    assert causal_base_hash == EXPECTED["causal_base_sha256"]

    store = Store(causal_points)
    pinned_checks = []
    for gap in (D_GAP, A_GAP, B_GAP):
        domain_index, expected_word, role = PINNED[gap]
        word = tuple(domains[state["parent_word"][gap]][domain_index])
        assert word == expected_word
        legal = word_legal_fast(state["anchors"][gap], word, store, {}, MENU)
        assert legal
        interiors = word_interiors(state["anchors"][gap], word)
        pinned_checks.append(
            {
                "role": role,
                "segment": gap,
                "pipeline_rank_zero_based": order.index(gap),
                "domain_index": domain_index,
                "word": list(word),
                "interiors": len(interiors),
                "exactly_legal": legal,
            }
        )
        store.add_many(interiors)
        causal_births.extend([LEVEL] * len(interiors))
        assert len(store.pts) == len(store.pset)

    pretarget_points = list(store.pts)
    pretarget_births = list(causal_births)
    pretarget_hash = point_set_sha256(pretarget_points)
    assert len(pretarget_points) == EXPECTED["pretarget_points"]
    assert pretarget_hash == EXPECTED["pretarget_sha256"]

    target_domain = domains[state["parent_word"][TARGET]]
    target_model = build_domain_model(target_domain)
    target_survivors, target_poisoned = exact_survivors(
        target_model,
        state["anchors"][TARGET],
        state["anchors"][TARGET + 1],
        pretarget_points,
        pretarget_births,
    )
    assert PINNED_TARGET_INDEX in target_survivors
    target_mask_hash = mask_sha256(target_survivors, len(target_domain))
    assert len(target_domain) == EXPECTED["target_domain"]
    assert len(target_survivors) == EXPECTED["target_survivors"]
    assert len(target_poisoned) == EXPECTED["target_poisoned_atoms"]
    assert target_mask_hash == EXPECTED["target_mask_sha256"]
    del target_model
    gc.collect()

    guard_domain = domains[state["parent_word"][G_GAP]]
    short_guard_size = d24[state["parent_word"][G_GAP]]
    assert 0 < short_guard_size < len(guard_domain)
    short_guard_domain = guard_domain[:short_guard_size]
    guard_model = build_domain_model(short_guard_domain)
    guard_base_survivors, guard_base_poisoned = exact_survivors(
        guard_model,
        state["anchors"][G_GAP],
        state["anchors"][G_GAP + 1],
        pretarget_points,
        pretarget_births,
    )
    transfer = target_to_guard_transfer(
        target_domain,
        target_survivors,
        state["anchors"][TARGET],
        guard_model,
        state["anchors"][G_GAP],
        pretarget_points,
        guard_base_poisoned,
    )
    transfer_counts = transfer["counts"]
    minimum_guard_floor = min(transfer_counts.values())
    minimum_target_indices = sorted(
        index for index, count in transfer_counts.items() if count == minimum_guard_floor
    )
    assert minimum_guard_floor > 0
    assert len(guard_domain) == EXPECTED["guard_full_domain"]
    assert short_guard_size == EXPECTED["guard_short_domain"]
    assert len(guard_base_survivors) == EXPECTED["guard_short_before_target"]
    assert minimum_guard_floor == EXPECTED["uniform_guard_floor"]
    assert tuple(minimum_target_indices) == EXPECTED["floor_target_indices"]
    assert transfer["target_point_universe"] == EXPECTED["target_point_universe"]
    assert transfer["target_pair_effect_cache"] == EXPECTED["target_pair_effects"]

    # Independently recompute the exact short-G mask at the unique worst
    # target action.  This tests the transfer at the claimed floor, not merely
    # at the separately pinned trajectory below.
    floor_target_index = minimum_target_indices[0]
    floor_target_word = target_domain[floor_target_index]
    floor_target_interiors = word_interiors(
        state["anchors"][TARGET], floor_target_word
    )
    floor_guard_survivors, _floor_guard_poisoned = exact_survivors(
        guard_model,
        state["anchors"][G_GAP],
        state["anchors"][G_GAP + 1],
        pretarget_points + floor_target_interiors,
        pretarget_births + [LEVEL] * len(floor_target_interiors),
    )
    floor_transfer_mask = transfer["survivor_masks"][floor_target_index]
    floor_transfer_survivors = [
        index
        for index in range(short_guard_size)
        if (floor_transfer_mask >> index) & 1
    ]
    assert floor_guard_survivors == floor_transfer_survivors
    assert len(floor_guard_survivors) == minimum_guard_floor

    target_word = tuple(target_domain[PINNED_TARGET_INDEX])
    assert word_legal_fast(
        state["anchors"][TARGET], target_word, store, {}, MENU
    )
    target_interiors = word_interiors(state["anchors"][TARGET], target_word)
    store.add_many(target_interiors)
    causal_births.extend([LEVEL] * len(target_interiors))
    assert len(store.pts) == len(store.pset)

    full_guard_model = build_domain_model(guard_domain)
    full_guard_survivors, full_guard_poisoned = exact_survivors(
        full_guard_model,
        state["anchors"][G_GAP],
        state["anchors"][G_GAP + 1],
        store.pts,
        causal_births,
    )
    short_guard_survivors = [
        index for index in full_guard_survivors if index < short_guard_size
    ]
    transfer_pinned_mask = transfer["survivor_masks"][PINNED_TARGET_INDEX]
    transfer_pinned_survivors = [
        index
        for index in range(short_guard_size)
        if (transfer_pinned_mask >> index) & 1
    ]
    assert short_guard_survivors == transfer_pinned_survivors
    assert len(short_guard_survivors) == transfer_counts[PINNED_TARGET_INDEX]
    full_guard_mask_hash = mask_sha256(full_guard_survivors, len(guard_domain))
    short_guard_mask_hash = mask_sha256(short_guard_survivors, short_guard_size)
    assert len(full_guard_survivors) == EXPECTED["pinned_full_guard_survivors"]
    assert len(full_guard_poisoned) == EXPECTED["pinned_full_guard_poisoned_atoms"]
    assert full_guard_mask_hash == EXPECTED["pinned_full_guard_mask_sha256"]
    assert len(short_guard_survivors) == EXPECTED["pinned_short_guard_survivors"]
    assert short_guard_mask_hash == EXPECTED["pinned_short_guard_mask_sha256"]
    del full_guard_model
    gc.collect()

    chosen_guard_index = short_guard_survivors[0]
    chosen_guard_word = tuple(guard_domain[chosen_guard_index])
    assert chosen_guard_index == EXPECTED["chosen_guard_index"]
    assert chosen_guard_word == EXPECTED["chosen_guard_word"]
    assert word_legal_fast(
        state["anchors"][G_GAP], chosen_guard_word, store, {}, MENU
    )
    guard_interiors = word_interiors(state["anchors"][G_GAP], chosen_guard_word)
    store.add_many(guard_interiors)
    causal_births.extend([LEVEL] * len(guard_interiors))
    assert len(store.pts) == len(store.pset)

    c_domain = domains[state["parent_word"][C_GAP]]
    c_model = build_domain_model(c_domain)
    c_survivors, c_poisoned = exact_survivors(
        c_model,
        state["anchors"][C_GAP],
        state["anchors"][C_GAP + 1],
        store.pts,
        causal_births,
    )
    assert c_survivors
    c_mask_hash = mask_sha256(c_survivors, len(c_domain))
    assert len(c_domain) == EXPECTED["c_domain"]
    assert len(c_survivors) == EXPECTED["c_survivors"]
    assert len(c_poisoned) == EXPECTED["c_poisoned_atoms"]
    assert c_mask_hash == EXPECTED["c_mask_sha256"]

    result = {
        "status": "exact causal L7 pipeline macrotransition probe complete",
        "known_assertions_passed": True,
        "scope": (
            "one exact inherited-tile pipeline state with pinned D/A/B; "
            "uniform over every legal target action only; not uniform over "
            "incoming histories, tiles, or levels and not a fixed-point proof"
        ),
        "pipeline": {
            "definition": (
                "bootstrap tile-0 guard; before tile t place the guard of "
                "tile t+1; then place unplaced tile-t gaps by (d24,index)"
            ),
            "level": LEVEL,
            "segments": [D_GAP, A_GAP, B_GAP, TARGET, G_GAP, C_GAP],
            "ranks_zero_based": list(local_order),
            "tiles": [owners[gap] for gap in (D_GAP, A_GAP, B_GAP, TARGET, G_GAP, C_GAP)],
            "guard_segments": {
                str(owners[gap]): guards.get(owners[gap])
                for gap in (D_GAP, A_GAP, B_GAP, TARGET, G_GAP, C_GAP)
            },
        },
        "causal_base_before_D": {
            "points": len(causal_points),
            "placed_connector_gaps": d_rank,
            "placed_set_sha256": causal_base_hash,
            "future_connectors_included": False,
        },
        "pinned_DAB": pinned_checks,
        "pretarget_state": {
            "points": len(pretarget_points),
            "placed_set_sha256": pretarget_hash,
        },
        "target_availability": {
            "segment": TARGET,
            "domain_size": len(target_domain),
            "survivors": len(target_survivors),
            "poisoned_atoms": len(target_poisoned),
            "survivor_mask_sha256": target_mask_hash,
            "pinned_domain_index": PINNED_TARGET_INDEX,
            "pinned_word": list(target_word),
        },
        "universal_target_to_guard": {
            "quantifier": (
                "for every exactly legal target word W at the pinned causal "
                "D/A/B state, at least the stated floor of length-2--4 G "
                "words is exactly legal after W"
            ),
            "target_words_checked": len(target_survivors),
            "guard_segment": G_GAP,
            "guard_step": state["parent_word"][G_GAP],
            "guard_full_domain_size": len(guard_domain),
            "guard_short_domain_size": short_guard_size,
            "guard_short_survivors_before_target": len(guard_base_survivors),
            "uniform_short_guard_floor_after_target": minimum_guard_floor,
            "target_indices_attaining_floor": minimum_target_indices,
            "floor_attainer_independent_exact_mask_crosscheck": True,
            "target_point_universe": transfer["target_point_universe"],
            "target_pair_effects_evaluated": transfer["target_pair_effect_cache"],
            "far_endpoint_truncation": None,
            "soundness_partition": [
                "base collision and base--base secants at every G site",
                "base points on every line through two G interiors",
                "target-point collisions and base--target secants at G sites",
                "target--target secants at G sites",
                "target points on lines through two G interiors",
            ],
        },
        "pinned_target_full_guard_crosscheck": {
            "full_guard_survivors": len(full_guard_survivors),
            "full_guard_poisoned_atoms": len(full_guard_poisoned),
            "full_guard_survivor_mask_sha256": full_guard_mask_hash,
            "short_guard_survivors": len(short_guard_survivors),
            "short_guard_survivor_mask_sha256": short_guard_mask_hash,
            "transfer_mask_equals_independent_full_poison_prefix": True,
            "chosen_least_short_guard_index": chosen_guard_index,
            "chosen_least_short_guard_word": list(chosen_guard_word),
        },
        "next_C_availability": {
            "segment": C_GAP,
            "domain_size": len(c_domain),
            "survivors": len(c_survivors),
            "poisoned_atoms": len(c_poisoned),
            "survivor_mask_sha256": c_mask_hash,
        },
        "interpretation": (
            "the scale-and-rotate recorded walk supplies a legal causal prefix, "
            "and the old robust D/A/B choices do survive the pipeline reorder; "
            "the unresolved obstruction is closure over all incoming states"
        ),
        "elapsed_seconds": round(time.time() - started, 3),
        "input_sha256": {
            "checker": file_sha256(Path(__file__).resolve()),
            "files": observed_input_sha256,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
