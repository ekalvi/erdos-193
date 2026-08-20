#!/usr/bin/env python3
"""Exact recorded-orbit source/action/successor stabilization probe.

This is deliberately a *small* experiment.  It inspects one sentinel transition
at each of L5--L8:

    L5:989, L6:8033, L7:3783, L8:65694.

Each sentinel is the middle step-122 gap of an inherited tile with ordered step
factor (123, 122, 123).  The checker reconstructs the causal inherited-tile
guard schedule, replays the exact recorded connector choices before the
sentinel, computes the complete (untruncated) secant poison mask at the source,
places the recorded source action, and computes the poison mask at the
immediately scheduled successor.

The L5--L7 successor domains contain hundreds of thousands of length-5 words.
Building their full word/atom incidence tables is outside the scope of this
small probe.  For those successors the checker stops the full-domain audit and
instead reports an exact audit of the pre-existing length-2--4 domain prefix.
L8's successor domain is small enough to audit in full.  This limitation is
part of every transition code; a short-prefix result is never labelled a
full-domain result.

The finite local observation is a translated, ordered four-inherited-tile
factor.  It retains the actual connector word for every gap already placed at
the cursor and does not invent independent address streams for unplaced gaps.
There is no rotation or reversal quotient.  L5--L6 form a frozen exact
codebook; L7--L8 are only classified as seen/unseen in that codebook.  Exact
codebook novelty is evidence about this recorded orbit, not a proof that no
coarser sound abstraction exists.

Run from the repository root on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/pipeline_transition_stabilization.py \
        --output /tmp/pipeline-transition-stabilization.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import FRAGILE_CUT, load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from salvage_gate import (  # noqa: E402
    build_domain_model,
    built_walk_with_birth,
    compute_poison,
    mask_sha256,
    midpoint,
)


SENTINELS = {5: 989, 6: 8033, 7: 3783, 8: 65694}
SOURCE_STEP = 122
EXPECTED_TILE_SIGNATURE = (123, 122, 123)
MAX_FULL_SUCCESSOR_DOMAIN = 50_000
FACTOR_TILE_OFFSETS = (-1, 0, 1, 2)

EXPECTED_INPUT_SHA256 = {
    "viz/walk3d-data.json": (
        "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
    ),
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "dstar5_fragile.pkl": (
        "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3"
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
    "gate2-l7-construction-L8.pkl": (
        "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141"
    ),
}

# These are assertions over the exact July 18 run, not proof assumptions.
# Keeping them in the checker makes accidental schedule/domain drift fail loud.
EXPECTED_HEADLINES = {
    5: {
        "source": (989, 4796, 104, 7679, 1367),
        "action": (1503, (78, 93, 101, 112)),
        "successor": (996, 69, 298775, 600, 3, 44, 556),
        "transition": (
            "6f3b39131af441831fe3d9be02681930a6f8e6dd27061ed3984c452d27f86f66"
        ),
    },
    6: {
        "source": (8033, 27253, 91, 7623, 1423),
        "action": (7220, (111, 103, 83, 87)),
        "successor": (8035, 21, 501044, 1732, 40, 1206, 526),
        "transition": (
            "0c7733aaae26596e877c81fa67310b1b29c741c60e1ec94c3b919fc19c1b16c1"
        ),
    },
    7: {
        "source": (3783, 36596, 135, 8643, 403),
        "action": (8779, (121, 108, 78, 77)),
        "successor": (3788, 114, 453015, 1505, 9, 241, 1264),
        "transition": (
            "3898c40b5f287984ee96fe735f3c10c23cdbed9b116f1907722666149b3c9f74"
        ),
    },
    8: {
        "source": (65694, 247564, 111, 7533, 1513),
        "action": (18, (112, 103, 108)),
        "successor": (65699, 123, 2570, 2570, 19, 672, 1898),
        "transition": (
            "4f1269d9a3895e742a9d2e367c415a08c934a38ddd67112d022cbc7c07ebf29c"
        ),
    },
}


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def object_sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_state(level):
    with (ROOT / f"gate2-l7-construction-L{level}.pkl").open("rb") as handle:
        return pickle.load(handle)


def translated(point, origin):
    return [point[i] - origin[i] for i in range(3)]


def pipeline_layout(state, owners, d24):
    """Return exact inherited-tile schedule, guards, ranks, and tile gaps."""
    assert len(owners) == len(state["parent_word"])
    tile_gaps = defaultdict(list)
    for gap, tile in enumerate(owners):
        tile_gaps[tile].append(gap)
    tile_gaps = {tile: tuple(gaps) for tile, gaps in sorted(tile_gaps.items())}

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
    for tile, gaps in tile_gaps.items():
        if tile + 1 in guards:
            place(guards[tile + 1])
        for gap in sorted(
            gaps,
            key=lambda item: (d24[state["parent_word"][item]], item),
        ):
            place(gap)

    assert len(order) == len(state["parent_word"])
    assert placed == set(range(len(state["parent_word"])))
    ranks = {gap: rank for rank, gap in enumerate(order)}
    return order, guards, ranks, tile_gaps


def local_ordered_factor(
    state,
    owners,
    tile_gaps,
    guards,
    ranks,
    cursor_gap,
    cursor_rank,
):
    """Translated four-tile factor with only causally placed word choices.

    Future recorded words exist in the construction pickle, but exposing them
    would give the abstract state an oracle for future choices.  They are
    therefore represented only by ``placed=False``.  Natural path order and
    the exact placed connector words are retained.
    """
    cursor_tile = owners[cursor_gap]
    origin = state["anchors"][cursor_gap]
    tiles = []
    for tile_offset in FACTOR_TILE_OFFSETS:
        tile = cursor_tile + tile_offset
        gaps = tile_gaps.get(tile, ())
        tile_record = {
            "tile_offset": tile_offset,
            "exists": bool(gaps),
            "guard_local_gap": (
                None if guards.get(tile) is None or not gaps
                else guards[tile] - gaps[0]
            ),
            "gaps": [],
        }
        for local_gap, gap in enumerate(gaps):
            rank = ranks[gap]
            placed = rank < cursor_rank
            record = {
                "local_gap": local_gap,
                "gap_offset_from_cursor": gap - cursor_gap,
                "parent_step": state["parent_word"][gap],
                "anchor_start": translated(state["anchors"][gap], origin),
                "anchor_end": translated(state["anchors"][gap + 1], origin),
                "schedule_rank_offset": rank - cursor_rank,
                "placed": placed,
                "is_cursor": gap == cursor_gap,
                "placed_word": list(state["words"][gap]) if placed else None,
            }
            tile_record["gaps"].append(record)
        tiles.append(tile_record)
    factor = {
        "normalization": (
            "translate cursor start to zero; preserve orientation and ordered "
            "path direction; tiles cursor-1 through cursor+2"
        ),
        "cursor_tile_offset": 0,
        "cursor_local_gap": cursor_gap - tile_gaps[cursor_tile][0],
        "tiles": tiles,
    }
    return factor, object_sha256(factor)


def poison_signature(model, start, end, points, births, level):
    """Compute a complete exact atom and killed-word signature."""
    info = compute_poison(
        model, start, midpoint(start, end), points, births, level
    )
    poisoned = [
        atom
        for atom, record in enumerate(info)
        if math.isfinite(record["threshold"])
    ]
    poisoned_set = set(poisoned)
    killed = [
        word_index
        for word_index, atoms in enumerate(model["word_atoms"])
        if not poisoned_set.isdisjoint(atoms)
    ]
    by_type = Counter(model["atom_desc"][atom][0] for atom in poisoned)
    poisoned_descriptors = [model["atom_desc"][atom] for atom in poisoned]
    return {
        "atom_universe_size": len(model["atom_desc"]),
        "atom_universe_sha256": object_sha256(model["atom_desc"]),
        "word_atom_incidence_sha256": object_sha256(model["word_atoms"]),
        "site_atoms": len(model["site_id"]),
        "line_atoms": len(model["line_id"]),
        "poisoned_atoms": len(poisoned),
        "poisoned_atoms_by_type": dict(sorted(by_type.items())),
        "poisoned_atom_mask_sha256": mask_sha256(
            poisoned, len(model["atom_desc"])
        ),
        "poisoned_atom_descriptors_sha256": object_sha256(
            poisoned_descriptors
        ),
        "word_universe_size": len(model["word_atoms"]),
        "killed_words": len(killed),
        "surviving_words": len(model["word_atoms"]) - len(killed),
        "killed_word_mask_sha256": mask_sha256(
            killed, len(model["word_atoms"])
        ),
        "_poisoned": poisoned_set,
        "_killed": set(killed),
    }


def public_signature(signature):
    return {key: value for key, value in signature.items() if not key.startswith("_")}


def signature_code(signature, action_space):
    return object_sha256(
        {
            "action_space": action_space,
            "signature": public_signature(signature),
        }
    )


def action_space_for_successor(step, domains, d24):
    full_domain = domains[step]
    full_size = len(full_domain)
    if full_size <= MAX_FULL_SUCCESSOR_DOMAIN:
        audited = full_domain
        kind = "full-domain"
        full_status = "enumerated"
    else:
        audited = full_domain[: d24[step]]
        assert len(audited) == d24[step]
        assert all(2 <= len(word) <= 4 for word in audited)
        kind = "exact-length-2-4-prefix"
        full_status = "stopped-as-prohibitive"
    description = {
        "kind": kind,
        "full_domain_size": full_size,
        "audited_words": len(audited),
        "omitted_words": full_size - len(audited),
        "full_domain_status": full_status,
        "full_domain_threshold": MAX_FULL_SUCCESSOR_DOMAIN,
    }
    return audited, description


def replay_transition(level, target_gap, viz, domains, d24, source_model):
    state = load_state(level)
    owners = viz["levels"][level - 1]["parents"][:-1]
    order, guards, ranks, tile_gaps = pipeline_layout(state, owners, d24)
    target_rank = ranks[target_gap]
    assert order[target_rank] == target_gap
    assert target_rank + 1 < len(order)
    successor_gap = order[target_rank + 1]

    target_tile = owners[target_gap]
    assert tuple(
        state["parent_word"][gap] for gap in tile_gaps[target_tile]
    ) == EXPECTED_TILE_SIGNATURE
    assert state["parent_word"][target_gap] == SOURCE_STEP

    parent_points, parent_births = built_walk_with_birth(level - 1)
    assert state["anchors"] == [apply(M_BAL3, point) for point in parent_points]
    points = list(state["anchors"])
    births = list(parent_births)
    for gap in order[:target_rank]:
        interiors = word_interiors(state["anchors"][gap], state["words"][gap])
        points.extend(interiors)
        births.extend([level] * len(interiors))
    assert len(points) == len(births) == len(set(points))

    source_factor, source_factor_code = local_ordered_factor(
        state, owners, tile_gaps, guards, ranks, target_gap, target_rank
    )
    source_signature = poison_signature(
        source_model,
        state["anchors"][target_gap],
        state["anchors"][target_gap + 1],
        points,
        births,
        level,
    )
    source_space = {
        "kind": "full-domain",
        "step": SOURCE_STEP,
        "audited_words": len(domains[SOURCE_STEP]),
    }
    source_poison_code = signature_code(source_signature, source_space)

    source_domain = domains[SOURCE_STEP]
    action_word = tuple(state["words"][target_gap])
    action_index = source_domain.index(action_word)
    action_atoms = set(source_model["word_atoms"][action_index])
    action_legal = source_signature["_poisoned"].isdisjoint(action_atoms)
    assert action_legal
    action = {
        "word": list(action_word),
        "normalized_interior_offsets": [
            list(point) for point in word_interiors((0, 0, 0), action_word)
        ],
    }
    action_code = object_sha256(action)
    state_action_code = object_sha256(
        {
            "source_factor_code": source_factor_code,
            "source_poison_code": source_poison_code,
            "action_code": action_code,
        }
    )

    action_interiors = word_interiors(
        state["anchors"][target_gap], action_word
    )
    points.extend(action_interiors)
    births.extend([level] * len(action_interiors))
    assert len(points) == len(births) == len(set(points))

    successor_step = state["parent_word"][successor_gap]
    successor_domain, successor_space = action_space_for_successor(
        successor_step, domains, d24
    )
    successor_space = {"step": successor_step, **successor_space}
    successor_model = build_domain_model(successor_domain)
    successor_signature = poison_signature(
        successor_model,
        state["anchors"][successor_gap],
        state["anchors"][successor_gap + 1],
        points,
        births,
        level,
    )
    successor_poison_code = signature_code(
        successor_signature, successor_space
    )
    successor_factor, successor_factor_code = local_ordered_factor(
        state,
        owners,
        tile_gaps,
        guards,
        ranks,
        successor_gap,
        target_rank + 1,
    )

    transition_code = object_sha256(
        {
            "source_factor_code": source_factor_code,
            "source_poison_code": source_poison_code,
            "action_code": action_code,
            "successor_factor_code": successor_factor_code,
            "successor_poison_code": successor_poison_code,
        }
    )
    return {
        "_source_poisoned": source_signature["_poisoned"],
        "_source_killed": source_signature["_killed"],
        "level": level,
        "source": {
            "gap": target_gap,
            "tile": target_tile,
            "pipeline_rank_zero_based": target_rank,
            "step": SOURCE_STEP,
            "placed_points": len(points) - len(action_interiors),
            "factor": source_factor,
            "factor_code": source_factor_code,
            "poison": public_signature(source_signature),
            "poison_code": source_poison_code,
        },
        "action": {
            "recorded_domain_index": action_index,
            "exactly_legal": action_legal,
            **action,
            "action_code": action_code,
        },
        "successor": {
            "gap": successor_gap,
            "tile": owners[successor_gap],
            "tile_offset_from_source": owners[successor_gap] - target_tile,
            "pipeline_rank_zero_based": target_rank + 1,
            "step": successor_step,
            "placed_points": len(points),
            "action_space": successor_space,
            "factor": successor_factor,
            "factor_code": successor_factor_code,
            "poison": public_signature(successor_signature),
            "poison_code": successor_poison_code,
        },
        "codes": {
            "source_factor": source_factor_code,
            "source_poison": source_poison_code,
            "action": action_code,
            "state_action": state_action_code,
            "successor_factor": successor_factor_code,
            "successor_poison": successor_poison_code,
            "transition": transition_code,
        },
    }


def freeze_and_classify(records):
    fields = (
        "source_factor",
        "source_poison",
        "action",
        "state_action",
        "successor_factor",
        "successor_poison",
        "transition",
    )
    training = [record for record in records if record["level"] in (5, 6)]
    codebooks = {
        field: sorted({record["codes"][field] for record in training})
        for field in fields
    }
    training_atom_union = set().union(
        *(record["_source_poisoned"] for record in training)
    )
    training_atom_intersection = set.intersection(
        *(set(record["_source_poisoned"]) for record in training)
    )
    training_word_union = set().union(
        *(record["_source_killed"] for record in training)
    )
    training_word_intersection = set.intersection(
        *(set(record["_source_killed"]) for record in training)
    )
    for record in records:
        record["frozen_L5_L6_classification"] = {
            field + "_seen": record["codes"][field] in codebooks[field]
            for field in fields
        }
        distances = []
        for trained in training:
            source_atoms = record["_source_poisoned"]
            trained_atoms = trained["_source_poisoned"]
            source_words = record["_source_killed"]
            trained_words = trained["_source_killed"]
            distances.append(
                {
                    "training_level": trained["level"],
                    "poisoned_atom_symmetric_difference": len(
                        source_atoms ^ trained_atoms
                    ),
                    "poisoned_atoms_added": len(source_atoms - trained_atoms),
                    "poisoned_atoms_removed": len(trained_atoms - source_atoms),
                    "killed_word_symmetric_difference": len(
                        source_words ^ trained_words
                    ),
                    "killed_words_added": len(source_words - trained_words),
                    "killed_words_removed": len(trained_words - source_words),
                }
            )
        record["source_mask_distance_to_training"] = distances
    for record in records:
        del record["_source_poisoned"]
        del record["_source_killed"]
    return {
        "training_levels": [5, 6],
        "sentinels_per_level": 1,
        "comparison": "exact SHA-256 code equality only",
        "source_mask_span": {
            "poisoned_atom_union": len(training_atom_union),
            "poisoned_atom_intersection": len(training_atom_intersection),
            "killed_word_union": len(training_word_union),
            "killed_word_intersection": len(training_word_intersection),
        },
        "codebooks": codebooks,
    }


def assert_expected_headline(record):
    """Pin the finite run's headline without mistaking it for a theorem."""
    source = record["source"]
    successor = record["successor"]
    expected = EXPECTED_HEADLINES[record["level"]]
    assert (
        source["gap"],
        source["placed_points"],
        source["poison"]["poisoned_atoms"],
        source["poison"]["killed_words"],
        source["poison"]["surviving_words"],
    ) == expected["source"]
    assert (
        record["action"]["recorded_domain_index"],
        tuple(record["action"]["word"]),
    ) == expected["action"]
    assert (
        successor["gap"],
        successor["step"],
        successor["action_space"]["full_domain_size"],
        successor["action_space"]["audited_words"],
        successor["poison"]["poisoned_atoms"],
        successor["poison"]["killed_words"],
        successor["poison"]["surviving_words"],
    ) == expected["successor"]
    assert record["codes"]["transition"] == expected["transition"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON here (use /tmp for experiment runs); otherwise stdout",
    )
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")

    started = time.time()
    observed_input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_input_sha256 == EXPECTED_INPUT_SHA256
    domains, d24 = load_domains()
    viz_path = ROOT / "viz/walk3d-data.json"
    viz = json.loads(viz_path.read_text())
    source_model = build_domain_model(domains[SOURCE_STEP])

    records = []
    for level, target_gap in SENTINELS.items():
        print(
            f"exact transition L{level} gap {target_gap}",
            file=sys.stderr,
            flush=True,
        )
        record = replay_transition(
            level, target_gap, viz, domains, d24, source_model
        )
        assert_expected_headline(record)
        records.append(record)

    freeze = freeze_and_classify(records)
    for record in records:
        seen = record["frozen_L5_L6_classification"]
        if record["level"] in (5, 6):
            assert all(seen.values())
        else:
            assert not any(seen.values())
    result = {
        "status": "exact four-sentinel recorded-orbit transition probe complete",
        "scope": (
            "one recorded transition per L5--L8; complete global secant scan "
            "for every audited atom; not a census, closure proof, or GFP"
        ),
        "resource_policy": {"processes": 1, "thread_cap": 1, "nice": 15},
        "sentinels": SENTINELS,
        "source_action_space": {
            "step": SOURCE_STEP,
            "kind": "full-domain",
            "words": len(domains[SOURCE_STEP]),
        },
        "successor_full_domain_policy": {
            "threshold": MAX_FULL_SUCCESSOR_DOMAIN,
            "large_domain_treatment": (
                "stop full audit and exactly audit the length-2--4 prefix; "
                "do not extrapolate to omitted length-5 words"
            ),
        },
        "normalization": {
            "tiles": list(FACTOR_TILE_OFFSETS),
            "translation": "cursor start anchor is (0,0,0)",
            "ordered_path": "natural gap order retained",
            "placed_choices": "exact recorded word retained only if causally placed",
            "quotients_not_taken": ["rotation", "reflection", "path reversal"],
        },
        "training_freeze": freeze,
        "records": records,
        "interpretation_rule": (
            "an unseen L7/L8 exact code refutes only literal stabilization of "
            "this observation/code; it does not refute a sound coarser abstraction"
        ),
        "elapsed_seconds": round(time.time() - started, 3),
        "input_sha256": {
            **observed_input_sha256,
            "checker": file_sha256(Path(__file__).resolve()),
        },
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
        print(f"wrote {args.output}", file=sys.stderr, flush=True)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
