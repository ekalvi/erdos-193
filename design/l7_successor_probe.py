#!/usr/bin/env python3
"""Exact one-edge successor probe for the chosen L7 four-gap state.

The source stitch is segment 3783 under the fragile-first schedule.  This
checker installs one exactly compatible four-gap assignment, chooses target
word 493 from the 22-word minimum four-gap witness, and computes the complete
global killed-word mask at the *actual* next scheduled stitch, segment 3806.
It also computes the recorded-history mask at the same cursor as a baseline.

The four replacements are checked against the complete fixed pre-target base
in their true schedule order.  That base contains all other fixed pre-target
connectors, including connectors that occur later than a replacement.  Thus
the checks are stronger than chronological-prefix checks: the resulting full
union is triple-free, and every chronological prefix is triple-free as well.

The exact quantifier certified here is only

    for this concrete compatible earlier assignment, target word 493 is legal
    and its concrete successor at segment 3806 has a nonempty legal domain.

This is an exact finite reachable transition in the arbitrary-legal-choice
safety game.  It is not an all-history abstract transition, a deterministic
first-legal-selector result, a greatest-fixed-point certificate, or a
level-uniform theorem.

The implementation is single-process.  Run it on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_successor_probe.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from salvage_gate import (  # noqa: E402
    build_domain_model,
    compute_poison,
    mask_sha256,
    midpoint,
    replay_stitch,
)


LEVEL = 7
TARGET = 3783
SUCCESSOR = 3806
TARGET_DOMAIN_INDEX = 493
TARGET_WORD = (59, 102, 103, 121)

# Mapping values are (effective-domain index, connector word).  Iteration in
# the checker is by stitch rank, not by this semantic/path-neighbour ordering.
REPLACEMENTS = {
    3782: (1534, (102, 112, 53, 102)),
    3784: (1969, (106, 59, 101, 103)),
    3786: (1505, (102, 107, 108, 52)),
    3785: (41092, (18, 24, 72, 39, 44)),
}

EXPECTED = {
    "target_rank": 16_790,
    "successor_rank": 16_791,
    "corridor_start_translation": (102, -54, 75),
    "corridor_start_chebyshev_distance": 102,
    "schedule_order": (3785, 3782, 3784, 3786),
    "schedule_ranks": (433, 8_828, 8_829, 8_830),
    "replacement_interiors": (4, 3, 3, 3),
    "actual_pre_target_points": 70_334,
    "removed_actual_interiors": 9,
    "fixed_base_points": 70_325,
    "fixed_base_sha256": (
        "fd226a96108e94e80d133b644e6df463e532362209bbdd6ed826fe5873a6c757"
    ),
    "source_points": 70_338,
    "source_sha256": (
        "86e44cac71928d967eebc74fa37676bc3d9c90be200a73780cc169a3c505f9e2"
    ),
    "successor_points": 70_341,
    "successor_sha256": (
        "81e8039d20f2a7b290956f2fbb0fa79698c95e7507e3b4ed413f1de407372009"
    ),
    "domain_size": 9_046,
    "altered_survivors": 3_082,
    "altered_survivor_mask_sha256": (
        "4565d52c74070225f52cf1cbb352390dd9f74f93c6f36256018eb2889ea01750"
    ),
    "altered_killed_atoms": 75,
    "actual_pre_successor_points": 70_337,
    "actual_pre_successor_sha256": (
        "57b89380f3abd5a161a6bb49cee3563cdfbdc588b78a37d26395b67553c3fe3b"
    ),
    "actual_survivors": 3_142,
    "actual_survivor_mask_sha256": (
        "3c484de2ebdaa0cd655379930f8fdbf0ff096eb8a7ac4dd1e026a0c168cb77d2"
    ),
    "actual_killed_atoms": 73,
    "recorded_successor_domain_index": 15,
    "recorded_successor_word": (108, 107, 108),
    "survivor_intersection": 3_082,
    "survivor_union": 3_142,
    "survivor_symmetric_difference": 60,
    "production_sample_size": 24,
}

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
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def point_set_sha256(points):
    serial = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


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


def production_sample(start, domain, store, survivors, extra_indices=()):
    expected = set(survivors)
    indices = set(extra_indices)
    stride = max(1, len(domain) // 16)
    indices.update(range(0, len(domain), stride))
    indices.update(survivors[:3])
    indices.update(survivors[-3:])

    memo = {}
    mismatches = []
    for word_index in sorted(indices):
        legal = word_legal_fast(start, domain[word_index], store, memo, MENU)
        if legal != (word_index in expected):
            mismatches.append((word_index, legal, word_index in expected))
    assert not mismatches
    return len(indices)


def main():
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")

    started = time.time()
    observed_input_hashes = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_input_hashes == EXPECTED_INPUT_SHA256

    domains, _d24 = load_domains()
    state, target_rank, actual_points, actual_births = replay_stitch(LEVEL, TARGET)
    assert target_rank == EXPECTED["target_rank"]
    assert state["order"][target_rank + 1] == SUCCESSOR
    assert state["parent_word"][TARGET] == state["parent_word"][SUCCESSOR] == 122
    assert len(actual_points) == EXPECTED["actual_pre_target_points"]
    corridor_translation = tuple(
        state["anchors"][SUCCESSOR][axis] - state["anchors"][TARGET][axis]
        for axis in range(3)
    )
    assert corridor_translation == EXPECTED["corridor_start_translation"]
    corridor_distance = max(map(abs, corridor_translation))
    assert corridor_distance == EXPECTED["corridor_start_chebyshev_distance"]

    domain = domains[122]
    assert len(domain) == EXPECTED["domain_size"]
    assert len(domain) == len(set(domain))
    assert tuple(domain[TARGET_DOMAIN_INDEX]) == TARGET_WORD
    model = build_domain_model(domain)

    removed = {
        point
        for gap in REPLACEMENTS
        for point in word_interiors(state["anchors"][gap], state["words"][gap])
    }
    assert len(removed) == EXPECTED["removed_actual_interiors"]
    assert removed.issubset(set(actual_points))

    fixed_base = []
    fixed_births = []
    for point, birth in zip(actual_points, actual_births):
        if point not in removed:
            fixed_base.append(point)
            fixed_births.append(birth)
    assert len(fixed_base) == EXPECTED["fixed_base_points"]
    assert point_set_sha256(fixed_base) == EXPECTED["fixed_base_sha256"]

    store = Store(fixed_base)
    births = list(fixed_births)
    replacement_checks = []
    schedule_order = tuple(sorted(REPLACEMENTS, key=state["order"].index))
    assert schedule_order == EXPECTED["schedule_order"]

    for gap in schedule_order:
        domain_index, expected_word = REPLACEMENTS[gap]
        word = tuple(domains[state["parent_word"][gap]][domain_index])
        assert word == expected_word
        rank = state["order"].index(gap)
        interiors = word_interiors(state["anchors"][gap], word)
        legal = word_legal_fast(state["anchors"][gap], word, store, {}, MENU)
        assert legal
        store.add_many(interiors)
        births.extend([LEVEL] * len(interiors))
        replacement_checks.append(
            {
                "segment": gap,
                "schedule_rank_zero_based": rank,
                "domain_index": domain_index,
                "word": list(word),
                "interiors": len(interiors),
                "legal_against_full_fixed_base_and_prior_replacements": legal,
            }
        )

    assert tuple(item["schedule_rank_zero_based"] for item in replacement_checks) == (
        EXPECTED["schedule_ranks"]
    )
    assert tuple(item["interiors"] for item in replacement_checks) == (
        EXPECTED["replacement_interiors"]
    )
    assert len(store.pts) == len(births) == EXPECTED["source_points"]
    assert point_set_sha256(store.pts) == EXPECTED["source_sha256"]

    target_legal = word_legal_fast(
        state["anchors"][TARGET], TARGET_WORD, store, {}, MENU
    )
    assert target_legal
    target_interiors = word_interiors(state["anchors"][TARGET], TARGET_WORD)
    store.add_many(target_interiors)
    births.extend([LEVEL] * len(target_interiors))
    assert len(store.pts) == len(births) == EXPECTED["successor_points"]
    assert point_set_sha256(store.pts) == EXPECTED["successor_sha256"]

    altered_survivors, altered_poisoned = exact_survivors(
        model,
        state["anchors"][SUCCESSOR],
        state["anchors"][SUCCESSOR + 1],
        store.pts,
        births,
    )
    altered_mask_hash = mask_sha256(altered_survivors, len(domain))
    assert len(altered_survivors) == EXPECTED["altered_survivors"]
    assert altered_mask_hash == EXPECTED["altered_survivor_mask_sha256"]
    assert len(altered_poisoned) == EXPECTED["altered_killed_atoms"]

    recorded_successor_word = tuple(state["words"][SUCCESSOR])
    recorded_successor_index = domain.index(recorded_successor_word)
    assert recorded_successor_index == EXPECTED["recorded_successor_domain_index"]
    assert recorded_successor_word == EXPECTED["recorded_successor_word"]
    assert recorded_successor_index in altered_survivors
    altered_sample_size = production_sample(
        state["anchors"][SUCCESSOR],
        domain,
        store,
        altered_survivors,
        (recorded_successor_index,),
    )
    assert altered_sample_size == EXPECTED["production_sample_size"]

    same_state, successor_rank, baseline_points, baseline_births = replay_stitch(
        LEVEL, SUCCESSOR
    )
    assert same_state is state
    assert successor_rank == EXPECTED["successor_rank"]
    assert len(baseline_points) == EXPECTED["actual_pre_successor_points"]
    assert point_set_sha256(baseline_points) == EXPECTED["actual_pre_successor_sha256"]

    actual_survivors, actual_poisoned = exact_survivors(
        model,
        state["anchors"][SUCCESSOR],
        state["anchors"][SUCCESSOR + 1],
        baseline_points,
        baseline_births,
    )
    actual_mask_hash = mask_sha256(actual_survivors, len(domain))
    assert len(actual_survivors) == EXPECTED["actual_survivors"]
    assert actual_mask_hash == EXPECTED["actual_survivor_mask_sha256"]
    assert len(actual_poisoned) == EXPECTED["actual_killed_atoms"]
    assert recorded_successor_index in actual_survivors
    actual_sample_size = production_sample(
        state["anchors"][SUCCESSOR],
        domain,
        Store(baseline_points),
        actual_survivors,
        (recorded_successor_index,),
    )
    assert actual_sample_size == EXPECTED["production_sample_size"]

    altered_set = set(altered_survivors)
    actual_set = set(actual_survivors)
    comparison = {
        "intersection": len(altered_set & actual_set),
        "union": len(altered_set | actual_set),
        "symmetric_difference": len(altered_set ^ actual_set),
        "altered_is_subset_of_actual": altered_set <= actual_set,
    }
    assert comparison["intersection"] == EXPECTED["survivor_intersection"]
    assert comparison["union"] == EXPECTED["survivor_union"]
    assert comparison["symmetric_difference"] == EXPECTED[
        "survivor_symmetric_difference"
    ]
    assert comparison["altered_is_subset_of_actual"]

    result = {
        "status": "exact finite L7 one-edge successor certificate complete",
        "known_assertions_passed": True,
        "level": LEVEL,
        "schedule": "fragile-first",
        "quantifier": (
            "for the stated concrete compatible four-gap assignment, target "
            "word 493 is legal and its concrete successor at segment 3806 "
            "retains at least one exactly legal word"
        ),
        "scope": (
            "one concrete reachable transition only; not an all-history "
            "abstract transition, deterministic-selector result, greatest "
            "fixed point, level-uniform certificate, or unconditional theorem"
        ),
        "cursor": {
            "source_segment": TARGET,
            "source_schedule_rank_zero_based": target_rank,
            "successor_segment": SUCCESSOR,
            "successor_schedule_rank_zero_based": successor_rank,
            "step": 122,
            "domain_size": len(domain),
            "corridor_start_translation": list(corridor_translation),
            "corridor_start_chebyshev_distance": corridor_distance,
        },
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(fixed_base),
            "placed_set_sha256": point_set_sha256(fixed_base),
        },
        "replacement_checks": replacement_checks,
        "chosen_target": {
            "domain_index": TARGET_DOMAIN_INDEX,
            "word": list(TARGET_WORD),
            "legal": target_legal,
            "interiors": len(target_interiors),
        },
        "altered_successor": {
            "points": len(store.pts),
            "placed_set_sha256": point_set_sha256(store.pts),
            "survivors": len(altered_survivors),
            "survivor_mask_sha256": altered_mask_hash,
            "poisoned_atoms": len(altered_poisoned),
            "production_sample_words": altered_sample_size,
            "recorded_successor_word_legal": (
                recorded_successor_index in altered_survivors
            ),
        },
        "recorded_history_baseline": {
            "points": len(baseline_points),
            "placed_set_sha256": point_set_sha256(baseline_points),
            "survivors": len(actual_survivors),
            "survivor_mask_sha256": actual_mask_hash,
            "poisoned_atoms": len(actual_poisoned),
            "production_sample_words": actual_sample_size,
        },
        "recorded_successor_action": {
            "domain_index": recorded_successor_index,
            "word": list(recorded_successor_word),
            "legal_in_altered_state": recorded_successor_index in altered_survivors,
            "legal_in_recorded_state": recorded_successor_index in actual_survivors,
        },
        "mask_comparison": comparison,
        "elapsed_seconds": round(time.time() - started, 3),
        "input_sha256": {
            **observed_input_hashes,
            "checker": file_sha256(Path(__file__).resolve()),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
