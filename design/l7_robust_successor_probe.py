#!/usr/bin/env python3
"""Exact L7 successor probe aligned with the robust early-D certificate.

The source is the frozen pre-target cone at segment 3783 under the recorded
fragile-first schedule.  This checker installs the robust-D witness and the
tight A/B pair from ``l7_robust_d_selector.py``, then makes two deterministic
choices:

1. C is the least effective-domain index exactly legal against the complete
   frozen base plus D, A, and B.
2. The target action is the first, in the certified 45-index order, that is
   exactly legal against the resulting state.

It then computes the complete global killed-word mask at the actual next
scheduled stitch, segment 3806.  No endpoint-radius truncation is used.

The replacements are tested in their true schedule order against the complete
fixed pre-target base.  That base includes recorded connectors scheduled after
the early D/A/B choices, so this is stronger than testing only chronological
prefixes.  Once the full union is triple-free, every chronological prefix is
triple-free and the recorded intervening actions give a legal arbitrary-choice
replay.

Exact scope: this certifies one concrete reachable transition in the frozen L7
cone.  The successor count is not a uniform lower bound over all C or target
actions, and the rank-433 D choice was found using the recorded future base.
This is not an online all-history selector, transition quotient, greatest-fixed
point, cross-level invariant, deterministic first-legal construction result,
or unconditional theorem.

Run on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l7_robust_successor_probe.py
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
A_GAP = 3782
B_GAP = 3784
C_GAP = 3786
D_GAP = 3785

# Values are (effective-domain index, word, role).  The checker sorts these by
# actual schedule rank before insertion.
PINNED_CHOICES = {
    D_GAP: (8681, (34, 24, 19, 22, 98), "D"),
    A_GAP: (1465, (102, 103, 100, 63), "A"),
    B_GAP: (425, (77, 82, 102, 107), "B"),
}

CERTIFIED_TARGET_INDICES = (
    26,
    415,
    492,
    884,
    900,
    934,
    982,
    998,
    2053,
    2208,
    2211,
    3105,
    3107,
    3110,
    3114,
    3126,
    3129,
    3132,
    3660,
    3676,
    3722,
    3731,
    3733,
    3734,
    3743,
    3745,
    3758,
    3759,
    7100,
    7101,
    7113,
    7114,
    7116,
    8154,
    8156,
    8241,
    8242,
    8243,
    8245,
    8250,
    8762,
    8763,
    8771,
    8772,
    8780,
)

EXPECTED = {
    "target_schedule_rank": 16_790,
    "successor_schedule_rank": 16_791,
    "schedule_order": (D_GAP, A_GAP, B_GAP),
    "schedule_ranks": (433, 8_828, 8_829),
    "pinned_interiors": (4, 3, 3),
    "c_schedule_rank": 8_830,
    "actual_pre_target_points": 70_334,
    "removed_actual_interiors": 9,
    "fixed_base_points": 70_325,
    "fixed_base_sha256": (
        "fd226a96108e94e80d133b644e6df463e532362209bbdd6ed826fe5873a6c757"
    ),
    "c_domain_index": 0,
    "c_word": (102, 103, 102),
    "c_interiors": 2,
    "pretarget_points": 70_337,
    "pretarget_sha256": (
        "555b9f67d287c03a3b61cddbcd6d6eb0ea8d922ea58d262527d5b2d72f39f6ff"
    ),
    "certified_target_count": 45,
    "target_domain_index": 26,
    "target_word": (51, 103, 108, 123),
    "target_interiors": 3,
    "target_indices_tested": ((26, True),),
    "successor_state_points": 70_340,
    "successor_state_sha256": (
        "036479527b9f4ef742b56db70786ccfd566bf7cc9c7abb6d7a120baed5bdbae3"
    ),
    "successor_domain_size": 9_046,
    "successor_survivors": 2_747,
    "successor_survivor_mask_sha256": (
        "5efdf9263ce992cbde50b484a546f04d692eeff0e86b6bc7bc3a6f60c6edf4cd"
    ),
    "successor_poisoned_atoms": 78,
    "successor_production_sample": 24,
    "recorded_successor_domain_index": 15,
    "recorded_successor_word": (108, 107, 108),
    "corridor_start_translation": (102, -54, 75),
    "corridor_start_chebyshev_distance": 102,
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
    "design/l7_robust_d_selector.py": (
        "502ce218a9b960b7efc39bfea3ad0ee41983f56c0d721d2098511c090e7cc4aa"
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
    assert target_rank == EXPECTED["target_schedule_rank"]
    assert state["order"][target_rank + 1] == SUCCESSOR
    successor_rank = state["order"].index(SUCCESSOR)
    assert successor_rank == EXPECTED["successor_schedule_rank"]
    assert state["parent_word"][TARGET] == state["parent_word"][SUCCESSOR] == 122
    assert len(actual_points) == EXPECTED["actual_pre_target_points"]

    corridor_translation = tuple(
        state["anchors"][SUCCESSOR][axis] - state["anchors"][TARGET][axis]
        for axis in range(3)
    )
    corridor_distance = max(map(abs, corridor_translation))
    assert corridor_translation == EXPECTED["corridor_start_translation"]
    assert corridor_distance == EXPECTED["corridor_start_chebyshev_distance"]

    removed = {
        point
        for gap in (A_GAP, B_GAP, C_GAP, D_GAP)
        for point in word_interiors(state["anchors"][gap], state["words"][gap])
    }
    assert len(removed) == EXPECTED["removed_actual_interiors"]
    assert removed.issubset(set(actual_points))

    fixed_base = []
    births = []
    for point, birth in zip(actual_points, actual_births):
        if point not in removed:
            fixed_base.append(point)
            births.append(birth)
    assert len(fixed_base) == EXPECTED["fixed_base_points"]
    assert point_set_sha256(fixed_base) == EXPECTED["fixed_base_sha256"]

    store = Store(fixed_base)
    pinned_checks = []
    schedule_order = tuple(sorted(PINNED_CHOICES, key=state["order"].index))
    assert schedule_order == EXPECTED["schedule_order"]

    for gap in schedule_order:
        domain_index, expected_word, role = PINNED_CHOICES[gap]
        word = tuple(domains[state["parent_word"][gap]][domain_index])
        assert word == expected_word
        rank = state["order"].index(gap)
        interiors = word_interiors(state["anchors"][gap], word)
        legal = word_legal_fast(state["anchors"][gap], word, store, {}, MENU)
        assert legal
        store.add_many(interiors)
        births.extend([LEVEL] * len(interiors))
        pinned_checks.append(
            {
                "role": role,
                "segment": gap,
                "schedule_rank_zero_based": rank,
                "domain_index": domain_index,
                "word": list(word),
                "interiors": len(interiors),
                "legal_against_full_fixed_base_and_prior_replacements": legal,
            }
        )

    assert tuple(item["schedule_rank_zero_based"] for item in pinned_checks) == (
        EXPECTED["schedule_ranks"]
    )
    assert tuple(item["interiors"] for item in pinned_checks) == EXPECTED[
        "pinned_interiors"
    ]

    # Deterministic C selector: the first word in effective-domain order that
    # is exactly legal against the full frozen base and the pinned D/A/B.
    c_domain = domains[state["parent_word"][C_GAP]]
    c_memo = {}
    c_domain_index = None
    c_word = None
    for word_index, word in enumerate(c_domain):
        if word_legal_fast(state["anchors"][C_GAP], word, store, c_memo, MENU):
            c_domain_index = word_index
            c_word = tuple(word)
            break
    assert c_domain_index == EXPECTED["c_domain_index"]
    assert c_word == EXPECTED["c_word"]
    assert state["order"].index(C_GAP) == EXPECTED["c_schedule_rank"]
    c_interiors = word_interiors(state["anchors"][C_GAP], c_word)
    assert len(c_interiors) == EXPECTED["c_interiors"]
    store.add_many(c_interiors)
    births.extend([LEVEL] * len(c_interiors))

    assert len(store.pts) == len(births) == EXPECTED["pretarget_points"]
    pretarget_hash = point_set_sha256(store.pts)
    assert pretarget_hash == EXPECTED["pretarget_sha256"]

    # Deterministic target selector restricted to the certified robust-D set.
    target_domain = domains[state["parent_word"][TARGET]]
    assert len(target_domain) == EXPECTED["successor_domain_size"]
    assert len(target_domain) == len(set(target_domain))
    assert len(CERTIFIED_TARGET_INDICES) == EXPECTED["certified_target_count"]

    target_domain_index = None
    target_word = None
    target_tests = []
    for word_index in CERTIFIED_TARGET_INDICES:
        word = tuple(target_domain[word_index])
        legal = word_legal_fast(state["anchors"][TARGET], word, store, {}, MENU)
        target_tests.append((word_index, legal))
        if legal:
            target_domain_index = word_index
            target_word = word
            break
    assert tuple(target_tests) == EXPECTED["target_indices_tested"]
    assert target_domain_index == EXPECTED["target_domain_index"]
    assert target_word == EXPECTED["target_word"]

    target_interiors = word_interiors(state["anchors"][TARGET], target_word)
    assert len(target_interiors) == EXPECTED["target_interiors"]
    store.add_many(target_interiors)
    births.extend([LEVEL] * len(target_interiors))
    assert len(store.pts) == len(births) == EXPECTED["successor_state_points"]
    assert point_set_sha256(store.pts) == EXPECTED["successor_state_sha256"]

    successor_model = build_domain_model(target_domain)
    successor_survivors, successor_poisoned = exact_survivors(
        successor_model,
        state["anchors"][SUCCESSOR],
        state["anchors"][SUCCESSOR + 1],
        store.pts,
        births,
    )
    successor_mask_hash = mask_sha256(successor_survivors, len(target_domain))
    assert len(successor_survivors) == EXPECTED["successor_survivors"]
    assert successor_mask_hash == EXPECTED["successor_survivor_mask_sha256"]
    assert len(successor_poisoned) == EXPECTED["successor_poisoned_atoms"]

    recorded_successor_word = tuple(state["words"][SUCCESSOR])
    recorded_successor_index = target_domain.index(recorded_successor_word)
    assert recorded_successor_index == EXPECTED["recorded_successor_domain_index"]
    assert recorded_successor_word == EXPECTED["recorded_successor_word"]
    assert recorded_successor_index in successor_survivors
    sample_size = production_sample(
        state["anchors"][SUCCESSOR],
        target_domain,
        store,
        successor_survivors,
        (recorded_successor_index,),
    )
    assert sample_size == EXPECTED["successor_production_sample"]

    result = {
        "status": "exact frozen-L7 robust-D one-edge successor certificate complete",
        "known_assertions_passed": True,
        "level": LEVEL,
        "schedule": "fragile-first",
        "quantifier": (
            "for the pinned robust D and tight A/B, choose the least-domain "
            "exactly legal C and then the first exactly legal member of the "
            "certified 45-word target set; that concrete successor at segment "
            "3806 retains 2747 exactly legal words"
        ),
        "scope": (
            "one concrete frozen-cone history only; the successor count is not "
            "uniform over C/target actions or abstract histories, and this is "
            "not an online selector, fixed point, cross-level invariant, "
            "deterministic first-legal theorem, or unconditional proof"
        ),
        "precommitment_caveat": (
            "D is chosen at rank 433 using a frozen base containing recorded "
            "future connectors; the computation supplies no D policy for "
            "other possible future histories"
        ),
        "cursor": {
            "source_segment": TARGET,
            "source_schedule_rank_zero_based": target_rank,
            "successor_segment": SUCCESSOR,
            "successor_schedule_rank_zero_based": successor_rank,
            "step": 122,
            "corridor_start_translation": list(corridor_translation),
            "corridor_start_chebyshev_distance": corridor_distance,
        },
        "fixed_base": {
            "actual_pre_target_points": len(actual_points),
            "removed_actual_interiors": len(removed),
            "points": len(fixed_base),
            "placed_set_sha256": point_set_sha256(fixed_base),
        },
        "pinned_choice_checks": pinned_checks,
        "deterministic_c": {
            "criterion": (
                "least effective-domain index exactly legal against the full "
                "frozen base plus D,A,B"
            ),
            "segment": C_GAP,
            "schedule_rank_zero_based": state["order"].index(C_GAP),
            "domain_index": c_domain_index,
            "word": list(c_word),
            "interiors": len(c_interiors),
        },
        "pretarget_state": {
            "points": EXPECTED["pretarget_points"],
            "placed_set_sha256": pretarget_hash,
        },
        "deterministic_target": {
            "criterion": "first exactly legal index in the certified 45-index order",
            "certified_set_size": len(CERTIFIED_TARGET_INDICES),
            "indices_tested": [list(item) for item in target_tests],
            "domain_index": target_domain_index,
            "word": list(target_word),
            "interiors": len(target_interiors),
        },
        "successor_state": {
            "points": len(store.pts),
            "placed_set_sha256": point_set_sha256(store.pts),
        },
        "successor_availability": {
            "segment": SUCCESSOR,
            "domain_size": len(target_domain),
            "survivors": len(successor_survivors),
            "survivor_mask_sha256": successor_mask_hash,
            "poisoned_atoms": len(successor_poisoned),
            "production_sample_words": sample_size,
            "recorded_word_domain_index": recorded_successor_index,
            "recorded_word": list(recorded_successor_word),
            "recorded_word_legal": recorded_successor_index in successor_survivors,
            "interpretation": "exact concrete count, not a uniform successor floor",
        },
        "elapsed_seconds": round(time.time() - started, 3),
        "input_sha256": {
            **observed_input_hashes,
            "checker": file_sha256(Path(__file__).resolve()),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
