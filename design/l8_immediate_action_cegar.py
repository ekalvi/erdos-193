#!/usr/bin/env python3
"""Exact two-stitch action/response and CEGAR probe at L8.

The causal inherited-tile pipeline places gap 67009 (A) immediately before
gap 67011 (B).  This checker freezes the exact recorded prefix before A,
enumerates every legal A word, and computes the complete B poison mask after
each A choice.  It does not replay 5,257 global secant scans.  Instead it
constructs an exact monotone transfer from A's site/line atoms to B's
site/line atoms and validates both the source mask and selected action masks
by independent complete poison scans.

For every legal A action, the base plus transfer contains every contribution
needed to decide final B legality:

* P-P-B and P-B-B are in B's base mask;
* P-A-B and A-A-B are transferred to B site atoms;
* A-B-B is transferred to B line atoms;
* point collisions are explicit;
* B-B-B is excluded by the pre-certified connector domain.

The resulting equivalence classes are valid only for availability at this
one B cursor.  They are not future-state congruence classes: the realized A
word and its geometry remain part of any reusable ordered-path game state.

Run from the repository root on one low-priority core:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l8_immediate_action_cegar.py \
        --output /tmp/l8-immediate-action-cegar.json
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

from fast_legal import LIMIT, SHIFT, Store, word_legal_fast  # noqa: E402
from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from inherited_tile_lifetime import (  # noqa: E402
    build_context,
    distance_shell,
    exact_birth_levels,
    file_sha256,
    load_viz,
)
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    cheb,
    compute_poison,
    cross,
    midpoint,
    sub,
)


LEVEL = 8
A_GAP = 67009
B_GAP = 67011
C_GAP = 67008
A_STEP = 14
B_STEP = 34
C_STEP = 48
A_RANK = 67010
B_RANK = 67011
C_RANK = 67012
TILE = 19959
TAGGED_ANCHOR_INDEX = 66975
RECORDED_A = (0, 3, 1)
RECORDED_A_INDEX = 1
RECORDED_B = (1, 25, 50)
RECORDED_B_INDEX = 8
RECORDED_C = (18, 54, 29)
RECORDED_C_INDEX = 107
KNOWN_SITE_OFFSET = (-3, -6, -4)
KNOWN_SITE_ATOM = 81

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
    "gate2-l7-construction-L8.pkl": (
        "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141"
    ),
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "fast_legal.py": (
        "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed"
    ),
    "design/inherited_tile_lifetime.py": (
        "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4"
    ),
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
}

# Filled from an independent first exact run, then checked on every canonical
# rerun.  These are finite-computation regression assertions, not hypotheses.
EXPECTED_HEADLINES = {
    "base": (63, 1997, 46, 4137),
    "availability": (0, 2282, 4866, 3499, 0, 1977),
    "classes": (1949, 1949, 1704, 1058, 7, 4, 0),
    "stream": (
        "1556108930d80f8668bdcf8518d4b61d932d281c7be998e88c0ff8219ed58433"
    ),
    "base_masks": (
        "4e1dcf58f6e8865681a0b7779e8da1e443cebc6ae6bff5e5cf338251707ed14b",
        "ab9f5a4727cf1dac08ff72b0f82015111294ec89f21110000ec2b2be6bcc9ab0",
        "e4d81fdcdc861d06c6253068254e87f490f2fa1876bbe977e16bc9000f18865d",
    ),
    "worst": (
        4657,
        "da322ea7697e8fac7493ccd879886393df4b8a8b81bf59774263d7b53301d9aa",
    ),
    "common": (
        "bf7956a61a1512efea5b366e00014c4597c514f88a06635a2058e3481eb060d3",
        8765,
        "bc04ebb4cfe6be98eaa928679455b2c33a79e5a5a9478e7674957bc0ef46c568",
    ),
    "cegar": (
        "e079caf002fa9b2c65c50fd37a2aa1e0c78d007cf478ea8d2b346b070ca47e0c",
        "f95879cfa493566779a59fc9af4e8af813bb5d62c9ac538b198e2f99481780bd",
        "eafcd392d5aa56bc0a3ff8a908ce4c3b6bda9919cbfb278dc5befd29e2487875",
    ),
    "branch_validation": (
        (50, 4657),
        "051a4873d925a11276c40238ac8f01dbf23a37a0446c207662bd968a18b5603a",
    ),
    "third_ply_interface": (
        "c31864a8fa4bbd1214cd21a8bda1075d80ef96c12077711855746da9ec1edcdd",
        4,
        1997,
        1977,
        1,
        1241,
        4,
    ),
}


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def bits_sha256(bits, size):
    return hashlib.sha256(bits.to_bytes((size + 7) // 8, "little")).hexdigest()


def bits_record(bits, size):
    return {"bits": bits.bit_count(), "mask_sha256": bits_sha256(bits, size)}


def point_set_sha256(points):
    payload = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(payload.encode()).hexdigest()


def point_birth_sha256(points, births):
    """Hash the exact coordinate/birth correlation, independent of order."""
    digest = hashlib.sha256()
    for point, birth in sorted(zip(points, births)):
        digest.update(
            f"{point[0]},{point[1]},{point[2]}:{birth}\n".encode("ascii")
        )
    return digest.hexdigest()


def load_state():
    with (ROOT / "gate2-l7-construction-L8.pkl").open("rb") as handle:
        return pickle.load(handle)


def direction_key(delta):
    """Packed canonical primitive direction, matching fast_legal.Store.

    The radix is 2**21 and every signed primitive component has absolute
    value below 2**20.  Equality of two packed keys reduces modulo the radix
    successively, so each component difference (strictly inside one radix)
    must vanish.  The encoding is therefore injective under the asserted
    component bound.
    """
    vx, vy, vz = delta
    divisor = math.gcd(math.gcd(abs(vx), abs(vy)), abs(vz))
    if divisor == 0:
        return None
    if divisor > 1:
        vx //= divisor
        vy //= divisor
        vz //= divisor
    if vx < 0 or (vx == 0 and (vy < 0 or (vy == 0 and vz < 0))):
        vx, vy, vz = -vx, -vy, -vz
    assert max(abs(vx), abs(vy), abs(vz)) < LIMIT
    return (((vx << SHIFT) + vy) << SHIFT) + vz


def atom_word_masks(model):
    masks = [0] * len(model["atom_desc"])
    for word_index, atoms in enumerate(model["word_atoms"]):
        flag = 1 << word_index
        for atom in atoms:
            masks[atom] |= flag
    return masks


def atoms_to_word_bits(atom_bits, word_masks):
    result = 0
    while atom_bits:
        flag = atom_bits & -atom_bits
        result |= word_masks[flag.bit_length() - 1]
        atom_bits ^= flag
    return result


def poisoned_atoms(info):
    return {
        atom
        for atom, record in enumerate(info)
        if math.isfinite(record["threshold"])
    }


def set_to_bits(values):
    result = 0
    for value in values:
        result |= 1 << value
    return result


def class_statistics(counter):
    sizes = sorted(counter.values())
    return {
        "classes": len(sizes),
        "singleton_classes": sum(size == 1 for size in sizes),
        "minimum_class_size": min(sizes),
        "maximum_class_size": max(sizes),
        "class_size_histogram": dict(sorted(Counter(sizes).items())),
    }


def maximal_antichain(masks):
    """Return inclusion-maximal distinct masks, largest first."""
    ordered = sorted(set(masks), key=lambda value: (-value.bit_count(), value))
    maximal = []
    for candidate in ordered:
        if any(candidate & ~existing == 0 for existing in maximal):
            continue
        maximal.append(candidate)
    return maximal


def minimal_antichain(masks):
    """Return inclusion-minimal distinct masks, smallest first."""
    ordered = sorted(set(masks), key=lambda value: (value.bit_count(), value))
    minimal = []
    for candidate in ordered:
        if any(existing & ~candidate == 0 for existing in minimal):
            continue
        minimal.append(candidate)
    return minimal


def iterate_set_bits(bits):
    while bits:
        flag = bits & -bits
        yield flag.bit_length() - 1
        bits ^= flag


def union_for_action_class(action_bits, killed_masks):
    result = 0
    for action_ordinal in iterate_set_bits(action_bits):
        result |= killed_masks[action_ordinal]
    return result


def cegar_partition(killed_masks, effect_atom_masks, b_model, b_domain,
                    legal_actions, base_atom_bits):
    """Greedily split response-incompatible classes on added poison atoms.

    A leaf is locally response-compatible exactly when its concretization has
    a common B response.  A leaf that the present features cannot resolve is
    *not* a losing game state: a richer predicate family may still split it,
    and the controller is not required to admit every legal A action.  This
    tree is a certificate for availability at this one B cursor only.
    """
    action_count = len(killed_masks)
    b_atom_count = len(b_model["atom_desc"])
    b_word_count = len(b_domain)
    assert action_count == len(effect_atom_masks) == len(legal_actions)
    full_words = (1 << b_word_count) - 1
    feature_actions = [0] * b_atom_count
    for ordinal, effect in enumerate(effect_atom_masks):
        # A base-poisoned atom cannot distinguish final B poison states.  Keep
        # only genuinely added atoms so every predicate has final-mask meaning,
        # rather than merely remembering redundant witness provenance.
        for atom in iterate_set_bits(effect & ~base_atom_bits):
            feature_actions[atom] |= 1 << ordinal

    nodes = []
    safe_node_ids = []
    unresolved_node_ids = []

    def visit(action_bits, depth, predicate_path):
        node_id = len(nodes)
        nodes.append(None)
        size = action_bits.bit_count()
        killed_union = union_for_action_class(action_bits, killed_masks)
        common = full_words & ~killed_union
        if common:
            least_response = (common & -common).bit_length() - 1
            domain_indices = [
                legal_actions[ordinal]
                for ordinal in iterate_set_bits(action_bits)
            ]
            record = {
                "node_id": node_id,
                "status": "response-compatible",
                "depth": depth,
                "actions": size,
                "common_responses": common.bit_count(),
                "least_common_response": least_response,
                "least_common_response_word": list(b_domain[least_response]),
                "predicate_path": predicate_path,
                "A_domain_indices": domain_indices,
                "A_domain_indices_sha256": stable_hash(domain_indices),
                "action_membership": bits_record(action_bits, action_count),
                "common_response_mask": bits_record(common, b_word_count),
            }
            nodes[node_id] = record
            safe_node_ids.append(node_id)
            return node_id

        best = None
        for atom, membership in enumerate(feature_actions):
            inside = (action_bits & membership).bit_count()
            if inside == 0 or inside == size:
                continue
            score = min(inside, size - inside)
            candidate = (score, -atom, atom, membership, inside)
            if best is None or candidate[:2] > best[:2]:
                best = candidate
        if best is None:
            domain_indices = [
                legal_actions[ordinal]
                for ordinal in iterate_set_bits(action_bits)
            ]
            record = {
                "node_id": node_id,
                "status": "unresolved-no-common-response",
                "depth": depth,
                "actions": size,
                "predicate_path": predicate_path,
                "A_domain_indices": domain_indices,
                "A_domain_indices_sha256": stable_hash(domain_indices),
                "action_membership": bits_record(action_bits, action_count),
                "reason": (
                    "no genuinely added B-poison-atom predicate separates "
                    "this response-incompatible class"
                ),
            }
            nodes[node_id] = record
            unresolved_node_ids.append(node_id)
            return node_id

        _score, _negative_atom, atom, membership, inside = best
        yes = action_bits & membership
        no = action_bits & ~membership
        description = b_model["atom_desc"][atom]
        record = {
            "node_id": node_id,
            "status": "split",
            "depth": depth,
            "actions": size,
            "feature_b_atom": atom,
            "feature_description": description,
            "feature_is_genuinely_added_not_base_poisoned": True,
            "feature_present": inside,
            "feature_absent": size - inside,
        }
        nodes[node_id] = record
        absent_path = predicate_path + [{
            "B_atom": atom,
            "description": description,
            "added_poison_present": False,
        }]
        present_path = predicate_path + [{
            "B_atom": atom,
            "description": description,
            "added_poison_present": True,
        }]
        absent_child = visit(no, depth + 1, absent_path)
        present_child = visit(yes, depth + 1, present_path)
        record["absent_child_node"] = absent_child
        record["present_child_node"] = present_child
        return node_id

    root_node = visit((1 << action_count) - 1, 0, [])
    assert root_node == 0
    assert all(record is not None for record in nodes)
    safe_records = [nodes[node_id] for node_id in safe_node_ids]
    unresolved_records = [nodes[node_id] for node_id in unresolved_node_ids]
    assert sum(record["actions"] for record in safe_records + unresolved_records) == (
        action_count
    )
    action_ordinal_by_domain_index = {
        domain_index: ordinal
        for ordinal, domain_index in enumerate(legal_actions)
    }
    leaf_membership = 0
    for record in safe_records + unresolved_records:
        for domain_index in record["A_domain_indices"]:
            ordinal = action_ordinal_by_domain_index[domain_index]
            flag = 1 << ordinal
            assert not (leaf_membership & flag)
            leaf_membership |= flag
    assert leaf_membership == (1 << action_count) - 1
    largest = max(
        safe_records,
        key=lambda record: (record["actions"], record["common_responses"]),
        default=None,
    )
    return {
        "semantics": (
            "response-incompatible classes are greedily split on exact "
            "membership of one genuinely added B poison atom; every "
            "response-compatible leaf exhibits one or more B words legal "
            "for every exact A action in that leaf; unresolved does not mean "
            "game-losing"
        ),
        "scope": "one B cursor; not a future-state congruence or GFP state quotient",
        "minimality": "greedy balanced split; not claimed minimal",
        "action_membership_index_space": (
            "bit ordinal in the ascending legal_A_domain_indices array"
        ),
        "legal_A_domain_indices": legal_actions,
        "legal_A_domain_indices_sha256": stable_hash(legal_actions),
        "root_node": root_node,
        "nodes": len(nodes),
        "tree_sha256": stable_hash(nodes),
        "node_records": nodes,
        "response_compatible_leaves": len(safe_records),
        "unresolved_no_common_response_leaves": len(unresolved_records),
        "safe_leaf_depth_histogram": dict(sorted(Counter(
            record["depth"] for record in safe_records
        ).items())),
        "safe_leaf_size_histogram": dict(sorted(Counter(
            record["actions"] for record in safe_records
        ).items())),
        "unresolved_leaf_records": unresolved_records,
        "response_compatible_leaf_records": safe_records,
        "largest_response_compatible_leaf": largest,
    }


def build_prefix(state, schedule, births7):
    points = list(state["anchors"])
    births = list(births7)
    for entry in schedule[:A_RANK]:
        gap = entry["gap"]
        interiors = word_interiors(state["anchors"][gap], state["words"][gap])
        points.extend(interiors)
        births.extend([LEVEL] * len(interiors))
    assert len(points) == len(births) == len(set(points))
    return points, births


def source_base_and_transfer(
    prefix,
    prefix_births,
    a_model,
    a_start,
    b_model,
    b_start,
    b_middle,
    tagged_point,
):
    """Build exact base-A poison and A-atom -> B-atom transfer.

    Only one packed direction dictionary is retained at a time.  This avoids
    the multi-gigabyte 174-by-|P| direction table that a literal transfer
    implementation would create.  The birth/shell subtable attributes only
    the prefix endpoint of P-A-B site-secant effects; it is not a decomposition
    of base poison, A-A-B, or A-B-B channels.
    """
    a_atom_count = len(a_model["atom_desc"])
    a_to_b = [0] * a_atom_count
    channels = {
        "collision": [0] * a_atom_count,
        "prefix-action-site-secant": [0] * a_atom_count,
        "action-point-on-B-line": [0] * a_atom_count,
        "action-action-site-secant": [0] * a_atom_count,
        "tagged-age1-action-site-secant": [0] * a_atom_count,
    }
    prefix_set = set(prefix)
    b_sites = [
        (add(b_start, offset), atom, offset)
        for offset, atom in b_model["site_id"].items()
    ]
    a_sites = [
        (add(a_start, offset), atom, offset)
        for offset, atom in a_model["site_id"].items()
    ]

    metadata = [
        (LEVEL - birth, distance_shell(cheb(point, b_middle)))
        for point, birth in zip(prefix, prefix_births)
    ]
    metadata_types = sorted(set(metadata))
    metadata_index = {value: index for index, value in enumerate(metadata_types)}
    metadata_flags = [1 << metadata_index[value] for value in metadata]
    by_birth_shell = {
        value: [0] * a_atom_count for value in metadata_types
    }

    base_a = set()
    for position, (x, a_atom, _offset) in enumerate(a_sites, 1):
        directions = {}
        duplicate = False
        for point, meta_flag in zip(prefix, metadata_flags):
            key = direction_key(sub(point, x))
            if key is None:
                continue
            old = directions.get(key, 0)
            if old:
                duplicate = True
            directions[key] = old | meta_flag
        if x in prefix_set or duplicate:
            base_a.add(a_atom)

        for q, b_atom, _b_offset in b_sites:
            flag = 1 << b_atom
            if x == q:
                a_to_b[a_atom] |= flag
                channels["collision"][a_atom] |= flag
                continue
            if q in prefix_set:
                # B already has a collision.  Do not mislabel p=q as a P-A
                # secant contribution.
                continue
            witness_metadata = directions.get(direction_key(sub(q, x)), 0)
            if not witness_metadata:
                continue
            a_to_b[a_atom] |= flag
            channels["prefix-action-site-secant"][a_atom] |= flag
            for meta_index in iterate_set_bits(witness_metadata):
                by_birth_shell[metadata_types[meta_index]][a_atom] |= flag
            if direction_key(sub(tagged_point, x)) == direction_key(sub(q, x)):
                channels["tagged-age1-action-site-secant"][a_atom] |= flag

        relative = sub(x, b_start)
        for direction, by_moment in b_model["line_by_direction"].items():
            b_atom = by_moment.get(cross(relative, direction))
            if b_atom is not None:
                flag = 1 << b_atom
                a_to_b[a_atom] |= flag
                channels["action-point-on-B-line"][a_atom] |= flag

        if position % 20 == 0 or position == len(a_sites):
            print(f"source-site transfer: {position}/{len(a_sites)}", flush=True)

    # Old point on a prospective A internal line: base-A line poison.
    a_directions = list(a_model["line_by_direction"].items())
    for point in prefix:
        relative = sub(point, a_start)
        for direction, by_moment in a_directions:
            atom = by_moment.get(cross(relative, direction))
            if atom is not None:
                base_a.add(atom)

    # A-A-B: translate every possible A internal line and test B sites.
    start_moments = {
        direction: cross(a_start, direction)
        for direction in a_model["line_by_direction"]
    }
    for (direction, local_moment), a_atom in a_model["line_id"].items():
        origin_moment = start_moments[direction]
        absolute_moment = tuple(
            origin_moment[index] + local_moment[index] for index in range(3)
        )
        for q, b_atom, _offset in b_sites:
            if cross(q, direction) == absolute_moment:
                flag = 1 << b_atom
                a_to_b[a_atom] |= flag
                channels["action-action-site-secant"][a_atom] |= flag

    return {
        "base_a_atoms": base_a,
        "a_to_b_atom_bits": a_to_b,
        "channels": channels,
        "birth_shell": by_birth_shell,
        "metadata_types": metadata_types,
    }


def main(output_path):
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    started = time.time()

    input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert input_sha256 == EXPECTED_INPUT_SHA256
    checker_sha256 = file_sha256(Path(__file__).resolve())

    domains, d24 = load_domains()
    viz = load_viz()
    births_by_level = exact_birth_levels(viz)
    state, tile_gaps, _owners, schedule, guards = build_context(
        LEVEL, viz, births_by_level, d24
    )
    schedule_by_gap = {
        entry["gap"]: (rank, entry) for rank, entry in enumerate(schedule)
    }
    assert schedule_by_gap[A_GAP] == (
        A_RANK,
        {"gap": A_GAP, "sweep_tile": TILE, "phase": "finish-current-tile"},
    )
    assert schedule_by_gap[B_GAP] == (
        B_RANK,
        {"gap": B_GAP, "sweep_tile": TILE, "phase": "finish-current-tile"},
    )
    assert schedule_by_gap[C_GAP] == (
        C_RANK,
        {"gap": C_GAP, "sweep_tile": TILE, "phase": "finish-current-tile"},
    )
    assert schedule[B_RANK]["gap"] == B_GAP
    assert schedule[A_RANK + 1]["gap"] == B_GAP
    assert schedule[B_RANK + 1]["gap"] == C_GAP
    assert tuple(tile_gaps[TILE]) == (67008, 67009, 67010, 67011)
    tile_steps = tuple(state["parent_word"][gap] for gap in tile_gaps[TILE])
    tile_ranks = tuple(schedule_by_gap[gap][0] for gap in tile_gaps[TILE])
    assert tile_steps == (48, 14, 24, 34)
    assert tile_ranks == (67012, 67010, 67009, 67011)
    assert guards.get(TILE) is None

    a_domain = domains[A_STEP]
    b_domain = domains[B_STEP]
    c_domain = domains[C_STEP]
    assert state["parent_word"][A_GAP] == A_STEP
    assert state["parent_word"][B_GAP] == B_STEP
    assert state["parent_word"][C_GAP] == C_STEP
    assert len(a_domain) == d24[A_STEP] == 5257
    assert len(b_domain) == d24[B_STEP] == 9046
    assert len(c_domain) == d24[C_STEP] == 49402
    assert tuple(state["words"][A_GAP]) == RECORDED_A
    assert tuple(state["words"][B_GAP]) == RECORDED_B
    assert tuple(state["words"][C_GAP]) == RECORDED_C
    assert a_domain.index(RECORDED_A) == RECORDED_A_INDEX
    assert b_domain.index(RECORDED_B) == RECORDED_B_INDEX
    assert c_domain.index(RECORDED_C) == RECORDED_C_INDEX

    prefix, prefix_births = build_prefix(
        state, schedule, births_by_level[LEVEL - 1]
    )
    assert len(prefix) == 250697
    prefix_hash = point_set_sha256(prefix)
    assert prefix_hash == (
        "7ba05e8ced59f2fb341e2ab1487d6a6aab34123fa7b982f53ea84879d2382aae"
    )
    birth_histogram = dict(sorted(Counter(prefix_births).items()))
    assert birth_histogram == {
        0: 21, 1: 42, 2: 152, 3: 501, 4: 1742,
        5: 5756, 6: 19483, 7: 65035, 8: 157965,
    }
    prefix_point_birth_hash = point_birth_sha256(prefix, prefix_births)
    assert prefix_point_birth_hash == (
        "cdb2eab8886a3faf0f0a71c9ad04d8ecefdbc049f177b35d18742139a408811c"
    )

    a_start = state["anchors"][A_GAP]
    a_end = state["anchors"][A_GAP + 1]
    b_start = state["anchors"][B_GAP]
    b_end = state["anchors"][B_GAP + 1]
    assert (a_start, a_end) == (
        (-71526, -1662, 13501), (-71532, -1668, 13499)
    )
    assert (b_start, b_end) == (
        (-71538, -1674, 13503), (-71541, -1680, 13498)
    )
    tagged_point = state["anchors"][TAGGED_ANCHOR_INDEX]
    assert tagged_point == (-71385, -1488, 13499)
    tagged_parent_point = tuple(
        viz["levels"][7]["points"][TAGGED_ANCHOR_INDEX]
    )
    assert tagged_parent_point == (-23795, 4665, 496)
    # build_context has already asserted that every L8 anchor, including this
    # one, is the M_BAL3 image of the corresponding L7 point.
    assert births_by_level[7][TAGGED_ANCHOR_INDEX] == 7
    parents7 = viz["levels"][7]["parents"]
    assert parents7[TAGGED_ANCHOR_INDEX] == 19950
    tagged_block_start = TAGGED_ANCHOR_INDEX
    while (tagged_block_start > 0
           and parents7[tagged_block_start - 1] == 19950):
        tagged_block_start -= 1
    assert tagged_block_start == 66973
    assert TAGGED_ANCHOR_INDEX - tagged_block_start == 2

    a_model = build_domain_model(a_domain)
    b_model = build_domain_model(b_domain)
    assert (
        len(a_model["site_id"]), len(a_model["line_id"]),
        len(a_model["line_by_direction"]), len(a_model["atom_desc"]),
    ) == (140, 1356, 75, 1496)
    assert (
        len(b_model["site_id"]), len(b_model["line_id"]),
        len(b_model["line_by_direction"]), len(b_model["atom_desc"]),
    ) == (174, 1978, 94, 2152)
    assert stable_hash(a_model["atom_desc"]) == (
        "d4a73fded3821c1f02bfd5ae477d0aed4cd4b0bde6d3b7461d213dab931ebb99"
    )
    assert stable_hash(a_model["word_atoms"]) == (
        "6ee224db5c3ed34df43a480a3c7741ee65e1ebed0f17c149a811520baee43cc2"
    )
    assert stable_hash(b_model["atom_desc"]) == (
        "f15ed8576e311192ce7a6fb022031946b96aa0f03eedac90f176cb74f6413c6d"
    )
    assert stable_hash(b_model["word_atoms"]) == (
        "8de5387d753eb36f8614ec532f64f43a4d8c0393b501e196b979c7bc7821a270"
    )
    a_site_distances_from_b = [
        cheb(add(a_start, offset), midpoint(b_start, b_end))
        for offset in a_model["site_id"]
    ]
    assert (min(a_site_distances_from_b), max(a_site_distances_from_b)) == (9, 15)
    assert {distance_shell(value) for value in a_site_distances_from_b} == {0}
    b_word_masks = atom_word_masks(b_model)
    full_b_words = (1 << len(b_domain)) - 1

    print("computing exact base-B poison", flush=True)
    b_base_info = compute_poison(
        b_model, b_start, midpoint(b_start, b_end),
        prefix, prefix_births, LEVEL,
    )
    b_base_atoms = poisoned_atoms(b_base_info)
    b_base_atom_bits = set_to_bits(b_base_atoms)
    b_base_killed = atoms_to_word_bits(b_base_atom_bits, b_word_masks)

    print("computing exact A-atom to B-atom transfer", flush=True)
    transfer = source_base_and_transfer(
        prefix, prefix_births, a_model, a_start,
        b_model, b_start, midpoint(b_start, b_end), tagged_point,
    )
    base_a_atoms = transfer["base_a_atoms"]
    print("independent tuple-direction base-A validation", flush=True)
    reference_a_info = compute_poison(
        a_model, a_start, midpoint(a_start, a_end),
        prefix, prefix_births, LEVEL,
    )
    reference_a_atoms = poisoned_atoms(reference_a_info)
    assert reference_a_atoms == base_a_atoms
    legal_actions = [
        index for index, atoms in enumerate(a_model["word_atoms"])
        if base_a_atoms.isdisjoint(atoms)
    ]
    assert RECORDED_A_INDEX in legal_actions
    assert stable_hash(legal_actions) == (
        "bb45f8742d6a5cdeca5edb5f26eb2daa6139d24f05bd052559a31a6f332f557e"
    )

    # Convert each A atom's B-atom effect to a B-word effect once.
    a_to_b_words = [
        atoms_to_word_bits(bits, b_word_masks)
        for bits in transfer["a_to_b_atom_bits"]
    ]
    effect_atom_masks = []
    killed_masks = []
    survivor_counts = []
    action_records = []
    atom_class_counter = Counter()
    killed_class_counter = Counter()
    stream = hashlib.sha256()
    atom_bytes = (len(b_model["atom_desc"]) + 7) // 8
    word_bytes = (len(b_domain) + 7) // 8
    channel_action_unions = {channel: 0 for channel in transfer["channels"]}
    channel_effectful_actions = Counter()
    channel_atom_masks_by_action = {
        channel: [] for channel in transfer["channels"]
    }
    birth_shell_action_unions = {
        meta: 0 for meta in transfer["metadata_types"]
    }
    birth_shell_effectful_actions = Counter()

    for action_index in legal_actions:
        effect_atoms = 0
        effect_words = 0
        for a_atom in a_model["word_atoms"][action_index]:
            effect_atoms |= transfer["a_to_b_atom_bits"][a_atom]
            effect_words |= a_to_b_words[a_atom]
        final_atoms = b_base_atom_bits | effect_atoms
        killed = b_base_killed | effect_words
        survivors = len(b_domain) - killed.bit_count()
        effect_atom_masks.append(effect_atoms)
        killed_masks.append(killed)
        survivor_counts.append(survivors)
        atom_class_counter[final_atoms] += 1
        killed_class_counter[killed] += 1
        stream.update(action_index.to_bytes(4, "little"))
        stream.update(effect_atoms.to_bytes(atom_bytes, "little"))
        stream.update(killed.to_bytes(word_bytes, "little"))

        channel_summary = {}
        for channel, per_atom in transfer["channels"].items():
            channel_atoms = 0
            for a_atom in a_model["word_atoms"][action_index]:
                channel_atoms |= per_atom[a_atom]
            channel_atom_masks_by_action[channel].append(channel_atoms)
            channel_words = atoms_to_word_bits(channel_atoms, b_word_masks)
            channel_action_unions[channel] |= channel_words
            if channel_atoms:
                channel_effectful_actions[channel] += 1
            if action_index == RECORDED_A_INDEX:
                channel_summary[channel] = {
                    "B_atoms": bits_record(channel_atoms, len(b_model["atom_desc"])),
                    "word_membership": bits_record(channel_words, len(b_domain)),
                    "incremental_membership_after_base": bits_record(
                        channel_words & ~b_base_killed, len(b_domain)
                    ),
                }

        birth_shell_summary = {}
        for meta, per_atom in transfer["birth_shell"].items():
            contribution_atoms = 0
            for a_atom in a_model["word_atoms"][action_index]:
                contribution_atoms |= per_atom[a_atom]
            contribution_words = atoms_to_word_bits(
                contribution_atoms, b_word_masks
            )
            birth_shell_action_unions[meta] |= contribution_words
            if contribution_atoms:
                birth_shell_effectful_actions[meta] += 1
            if action_index == RECORDED_A_INDEX and contribution_atoms:
                birth_shell_summary[f"age{meta[0]}-shell{meta[1]}"] = {
                    "B_atoms": bits_record(
                        contribution_atoms, len(b_model["atom_desc"])
                    ),
                    "word_membership": bits_record(
                        contribution_words, len(b_domain)
                    ),
                }

        action_records.append({
            "action_index": action_index,
            "word": list(a_domain[action_index]),
            "B_survivors": survivors,
            "effect_B_atoms": bits_record(
                effect_atoms, len(b_model["atom_desc"])
            ),
            "killed_B_words": bits_record(killed, len(b_domain)),
            "incremental_killed_B_words": bits_record(
                killed & ~b_base_killed, len(b_domain)
            ),
            **({
                "recorded_action_channel_contributions_overlap": channel_summary,
                "recorded_action_prefix_birth_shell_contributions_overlap": (
                    birth_shell_summary
                ),
            } if action_index == RECORDED_A_INDEX else {}),
        })

    legal_action_count = len(legal_actions)
    assert len(killed_masks) == legal_action_count
    assert all(
        len(values) == legal_action_count
        for values in channel_atom_masks_by_action.values()
    )
    fatal_actions = sum(count == 0 for count in survivor_counts)
    all_killed_union = 0
    for mask in killed_masks:
        all_killed_union |= mask
    universal_common_responses = full_b_words & ~all_killed_union

    # Exact best common-response class: all actions for which one B word is
    # legal.  This is a response-defined class, not yet a reusable state type.
    killed_response_counts = [0] * len(b_domain)
    for killed in killed_masks:
        for response in iterate_set_bits(killed):
            killed_response_counts[response] += 1
    response_action_counts = [
        legal_action_count - count for count in killed_response_counts
    ]
    best_response_size = max(response_action_counts)
    best_response_index = response_action_counts.index(best_response_size)
    best_response_actions = 0
    for ordinal, killed in enumerate(killed_masks):
        if not ((killed >> best_response_index) & 1):
            best_response_actions |= 1 << ordinal
    best_class_killed_union = union_for_action_class(
        best_response_actions, killed_masks
    )
    best_class_common = full_b_words & ~best_class_killed_union

    maximal_killed_antichain = maximal_antichain(killed_masks)
    minimal_killed_antichain = minimal_antichain(killed_masks)
    cegar = cegar_partition(
        killed_masks,
        effect_atom_masks,
        b_model,
        b_domain,
        legal_actions,
        b_base_atom_bits,
    )
    minimum_ordinal = min(
        range(legal_action_count),
        key=lambda ordinal: (survivor_counts[ordinal], legal_actions[ordinal]),
    )
    maximum_ordinal = max(
        range(legal_action_count),
        key=lambda ordinal: (survivor_counts[ordinal], -legal_actions[ordinal]),
    )

    # Known mixed age-1 x age-0 witness regression.
    known_atom = b_model["site_id"][KNOWN_SITE_OFFSET]
    assert known_atom == KNOWN_SITE_ATOM
    known_word_mask = b_word_masks[known_atom]
    assert bits_record(known_word_mask, len(b_domain)) == {
        "bits": 50,
        "mask_sha256": (
            "1361827e083a4167ee51505e689da041e492c7f2f0ee71a5c862b724bac7026d"
        ),
    }
    recorded_ordinal = legal_actions.index(RECORDED_A_INDEX)
    assert (effect_atom_masks[recorded_ordinal] >> known_atom) & 1
    recorded_tagged_atoms = 0
    for a_atom in a_model["word_atoms"][RECORDED_A_INDEX]:
        recorded_tagged_atoms |= transfer["channels"][
            "tagged-age1-action-site-secant"
        ][a_atom]
    assert (recorded_tagged_atoms >> known_atom) & 1

    # Independent exact post-recorded-action recomputation.
    recorded_a_interiors = word_interiors(a_start, RECORDED_A)
    assert recorded_a_interiors == [
        (-71528, -1664, 13499), (-71530, -1666, 13500)
    ]
    post_prefix = prefix + recorded_a_interiors
    post_births = prefix_births + [LEVEL] * len(recorded_a_interiors)
    assert point_set_sha256(post_prefix) == (
        "d119ef85ffd467c805fcf638676203a2e518bd45c9252bc80435d93a021ad248"
    )
    print("independent post-recorded-action validation", flush=True)
    post_info = compute_poison(
        b_model, b_start, midpoint(b_start, b_end),
        post_prefix, post_births, LEVEL,
    )
    post_atoms = set_to_bits(poisoned_atoms(post_info))
    optimized_post_atoms = b_base_atom_bits | effect_atom_masks[recorded_ordinal]
    assert post_atoms == optimized_post_atoms
    post_killed = atoms_to_word_bits(post_atoms, b_word_masks)
    assert post_killed == killed_masks[recorded_ordinal]
    assert not ((post_killed >> RECORDED_B_INDEX) & 1)

    store = Store(prefix)
    assert word_legal_fast(a_start, RECORDED_A, store, {}, MENU)
    store.add_many(recorded_a_interiors)
    assert word_legal_fast(b_start, RECORDED_B, store, {}, MENU)

    # The recorded length-3 action has genuinely incremental P-A-B effects,
    # but its A-A-B and A-B-B contributions are already covered by base B.
    # Independently validate length-4 actions that jointly exercise both
    # missing transfer branches outside the base mask, plus the exact worst
    # action.  Use one action when possible and one per branch otherwise.
    branch_channels = (
        "action-action-site-secant",
        "action-point-on-B-line",
    )
    combined_branch_ordinal = next(
        (
            ordinal
            for ordinal, action_index in enumerate(legal_actions)
            if len(a_domain[action_index]) == 4
            and all(
                channel_atom_masks_by_action[channel][ordinal]
                & ~b_base_atom_bits
                for channel in branch_channels
            )
        ),
        None,
    )
    if combined_branch_ordinal is not None:
        branch_ordinals = {combined_branch_ordinal}
    else:
        branch_ordinals = set()
        for channel in branch_channels:
            channel_ordinal = next(
                (
                    ordinal
                    for ordinal, action_index in enumerate(legal_actions)
                    if len(a_domain[action_index]) == 4
                    and channel_atom_masks_by_action[channel][ordinal]
                    & ~b_base_atom_bits
                ),
                None,
            )
            assert channel_ordinal is not None
            branch_ordinals.add(channel_ordinal)
    validation_ordinals = sorted(branch_ordinals | {minimum_ordinal})
    independent_action_validations = []
    for ordinal in validation_ordinals:
        action_index = legal_actions[ordinal]
        action_word = a_domain[action_index]
        action_interiors = word_interiors(a_start, action_word)
        assert len(prefix) + len(action_interiors) == len(
            set(prefix + action_interiors)
        )
        print(
            f"independent post-action validation A index {action_index}",
            flush=True,
        )
        reference_info = compute_poison(
            b_model, b_start, midpoint(b_start, b_end),
            prefix + action_interiors,
            prefix_births + [LEVEL] * len(action_interiors),
            LEVEL,
        )
        reference_atoms = set_to_bits(poisoned_atoms(reference_info))
        optimized_atoms = b_base_atom_bits | effect_atom_masks[ordinal]
        assert reference_atoms == optimized_atoms
        reference_killed = atoms_to_word_bits(reference_atoms, b_word_masks)
        assert reference_killed == killed_masks[ordinal]
        direct_store = Store(prefix)
        assert word_legal_fast(a_start, action_word, direct_store, {}, MENU)
        channel_records = {}
        for channel in branch_channels:
            contribution_atoms = channel_atom_masks_by_action[channel][ordinal]
            contribution_words = atoms_to_word_bits(
                contribution_atoms, b_word_masks
            )
            channel_records[channel] = {
                "incremental_atoms_after_base": bits_record(
                    contribution_atoms & ~b_base_atom_bits,
                    len(b_model["atom_desc"]),
                ),
                "incremental_word_membership_after_base": bits_record(
                    contribution_words & ~b_base_killed,
                    len(b_domain),
                ),
            }
        exercised_incremental_channels = [
            channel for channel in branch_channels
            if channel_records[channel]["incremental_atoms_after_base"]["bits"] > 0
        ]
        independent_action_validations.append({
            "A_domain_index": action_index,
            "A_word": list(action_word),
            "is_exact_worst_A_action": ordinal == minimum_ordinal,
            "exercised_incremental_branch_channels": (
                exercised_incremental_channels
            ),
            "post_B_atoms": bits_record(
                reference_atoms, len(b_model["atom_desc"])
            ),
            "post_B_killed_words": bits_record(
                reference_killed, len(b_domain)
            ),
            "branch_channels": channel_records,
            "tuple_direction_full_recomputation_equal": True,
            "direct_A_legality_backstop": True,
        })
    branch_validations = [
        record for record in independent_action_validations
        if record["exercised_incremental_branch_channels"]
    ]
    assert set().union(*(
        set(record["exercised_incremental_branch_channels"])
        for record in branch_validations
    )) == set(branch_channels)
    recorded_survivors = survivor_counts[recorded_ordinal]

    # Explicit handoff for the independent A+B->C checker.  Keep domain
    # indices rather than only mask hashes so the next program never has to
    # infer class membership from sampled or reformatted data.
    best_response_action_ordinals = list(iterate_set_bits(best_response_actions))
    best_response_A_indices = [
        legal_actions[ordinal] for ordinal in best_response_action_ordinals
    ]
    ordinal_by_A_index = {
        domain_index: ordinal
        for ordinal, domain_index in enumerate(legal_actions)
    }
    reconstructed_best_response_actions = 0
    for domain_index in best_response_A_indices:
        reconstructed_best_response_actions |= (
            1 << ordinal_by_A_index[domain_index]
        )
    assert reconstructed_best_response_actions == best_response_actions
    assert bits_record(
        reconstructed_best_response_actions, legal_action_count
    ) == bits_record(best_response_actions, legal_action_count)
    best_class_common_B_indices = list(iterate_set_bits(best_class_common))
    assert best_class_common_B_indices == [best_response_index]
    assert all(
        not (killed_masks[ordinal] & best_class_common)
        for ordinal in best_response_action_ordinals
    )

    largest_leaf = cegar["largest_response_compatible_leaf"]
    largest_leaf_A_indices = largest_leaf["A_domain_indices"]
    largest_leaf_action_bits = 0
    for domain_index in largest_leaf_A_indices:
        largest_leaf_action_bits |= 1 << ordinal_by_A_index[domain_index]
    assert bits_record(largest_leaf_action_bits, legal_action_count) == (
        largest_leaf["action_membership"]
    )
    largest_leaf_killed_union = union_for_action_class(
        largest_leaf_action_bits, killed_masks
    )
    largest_leaf_common_B = full_b_words & ~largest_leaf_killed_union
    assert bits_record(largest_leaf_common_B, len(b_domain)) == (
        largest_leaf["common_response_mask"]
    )
    largest_leaf_common_B_indices = list(
        iterate_set_bits(largest_leaf_common_B)
    )
    assert largest_leaf_common_B_indices

    partition_membership = 0
    b_response_partition = []
    for leaf in cegar["response_compatible_leaf_records"]:
        leaf_action_bits = 0
        for domain_index in leaf["A_domain_indices"]:
            leaf_action_bits |= 1 << ordinal_by_A_index[domain_index]
        assert not (partition_membership & leaf_action_bits)
        partition_membership |= leaf_action_bits
        assert bits_record(leaf_action_bits, legal_action_count) == (
            leaf["action_membership"]
        )
        leaf_killed_union = union_for_action_class(
            leaf_action_bits, killed_masks
        )
        leaf_common_B = full_b_words & ~leaf_killed_union
        assert bits_record(leaf_common_B, len(b_domain)) == (
            leaf["common_response_mask"]
        )
        leaf_common_B_indices = list(iterate_set_bits(leaf_common_B))
        assert leaf_common_B_indices
        assert all(
            not (killed_masks[ordinal] & leaf_common_B)
            for ordinal in iterate_set_bits(leaf_action_bits)
        )
        b_response_partition.append({
            "status": "C_unchecked",
            "cegar_node_id": leaf["node_id"],
            "A_domain_indices": leaf["A_domain_indices"],
            "A_domain_indices_sha256": stable_hash(
                leaf["A_domain_indices"]
            ),
            "common_B_domain_indices": leaf_common_B_indices,
            "common_B_domain_indices_sha256": stable_hash(
                leaf_common_B_indices
            ),
            "third_ply_controller_target": (
                "exists one fixed B in common_B_domain_indices and one fixed "
                "C such that C is legal for every exact A in this leaf"
            ),
        })
    assert cegar["unresolved_no_common_response_leaves"] == 0
    assert partition_membership == (1 << legal_action_count) - 1
    assert sorted(
        domain_index
        for leaf in b_response_partition
        for domain_index in leaf["A_domain_indices"]
    ) == legal_actions

    third_ply_interface = {
        "semantics": (
            "exact domain-index partition and selected overlapping probe "
            "class from the frozen L8 prefix; input to an independent "
            "A+B-to-C closure checker, not itself a future-state invariant"
        ),
        "cursor_binding": {
            "A": {
                "gap": A_GAP, "step": A_STEP, "pipeline_rank": A_RANK,
                "domain_words": len(a_domain),
                "domain_sha256": stable_hash(a_domain),
            },
            "B": {
                "gap": B_GAP, "step": B_STEP, "pipeline_rank": B_RANK,
                "domain_words": len(b_domain),
                "domain_sha256": stable_hash(b_domain),
            },
            "C": {
                "gap": C_GAP, "step": C_STEP, "pipeline_rank": C_RANK,
                "domain_words": len(c_domain),
                "domain_sha256": stable_hash(c_domain),
            },
            "ranks_are_consecutive_A_then_B_then_C": True,
            "input_sha256": input_sha256,
        },
        "third_ply_history_contract": {
            "quantifier_order": "exists_B_exists_C_forall_A",
            "one_fixed_B_and_C_per_class": True,
            "B_choice_space": "emitted common_B_domain_indices",
            "C_choice_space": "all 49402 words in D_48",
            "prefix_before_C_in_order": [
                "P_pre_A",
                "interiors_of_exact_A",
                "interiors_of_selected_B",
            ],
            "recorded_B_or_C_not_implicitly_added": True,
        },
        "legal_A_domain_indices": legal_actions,
        "legal_A_domain_indices_sha256": stable_hash(legal_actions),
        "B_response_compatible_cegar_partition": {
            "status": "C_unchecked",
            "leaves": b_response_partition,
            "leaf_count": len(b_response_partition),
            "unresolved_leaf_count": 0,
            "covers_every_legal_A_exactly_once": True,
        },
        "selected_overlapping_probe_class": {
            "status": "C_unchecked",
            "name": "maximal-single-response-class",
            "A_domain_indices": best_response_A_indices,
            "A_domain_indices_sha256": stable_hash(best_response_A_indices),
            "common_B_domain_indices": best_class_common_B_indices,
            "common_B_domain_indices_sha256": stable_hash(
                best_class_common_B_indices
            ),
            "third_ply_controller_target": (
                "exists one fixed C such that C is legal after B=8765 for "
                "every exact A in this response-defined class"
            ),
        },
        "largest_partition_leaf_redundant_index": {
            "cegar_node_id": largest_leaf["node_id"],
            "A_domain_indices": largest_leaf_A_indices,
            "A_domain_indices_sha256": stable_hash(largest_leaf_A_indices),
            "common_B_domain_indices": largest_leaf_common_B_indices,
            "common_B_domain_indices_sha256": stable_hash(
                largest_leaf_common_B_indices
            ),
        },
    }
    third_ply_interface_sha256 = stable_hash(third_ply_interface)

    ordered_factor = {
        "tile": TILE,
        "natural_gaps": list(tile_gaps[TILE]),
        "steps": list(tile_steps),
        "pipeline_ranks": list(tile_ranks),
        "pre_A_status": ["future", "cursor-A", "placed", "future-B"],
        "placed_gap_67010_word": list(state["words"][67010]),
        "semantic_rule": (
            "after A, the exact chosen A word is retained; therefore the "
            "full ordered-factor state has one distinct record per legal word"
        ),
    }

    result = {
        "status": (
            "exact finite two-stitch action/response certificate on one "
            "recorded L8 causal prefix; not a greatest fixed point"
        ),
        "checker_sha256": checker_sha256,
        "input_sha256": input_sha256,
        "resource_policy": {
            "processes": 1,
            "thread_cap": 1,
            "nice": 15,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "causal_edge": {
            "level": LEVEL,
            "A": {
                "gap": A_GAP, "step": A_STEP, "domain_words": len(a_domain),
                "pipeline_rank": A_RANK, "recorded_word": list(RECORDED_A),
            },
            "B": {
                "gap": B_GAP, "step": B_STEP, "domain_words": len(b_domain),
                "pipeline_rank": B_RANK, "recorded_word": list(RECORDED_B),
            },
            "immediate_successor": True,
            "ordered_factor": ordered_factor,
            "ordered_factor_sha256": stable_hash(ordered_factor),
            "post_A_full_ordered_factor_classes": legal_action_count,
        },
        "third_ply_interface": third_ply_interface,
        "third_ply_interface_sha256": third_ply_interface_sha256,
        "prefix": {
            "points": len(prefix),
            "point_set_sha256": prefix_hash,
            "coordinate_birth_correlation_sha256": prefix_point_birth_hash,
            "absolute_birth_level_histogram": birth_histogram,
            "tagged_age1_endpoint": {
                "stable_id": "connector:L7:G19950:I2",
                "anchor_index": TAGGED_ANCHOR_INDEX,
                "L7_parent_coordinate": list(tagged_parent_point),
                "L8_normalized_coordinate": list(tagged_point),
                "absolute_birth_level": 7,
                "age_at_L8": 1,
                "L7_parent_gap": 19950,
                "L7_parent_block_start": tagged_block_start,
                "interior_ordinal": 2,
                "ancestry_asserted_from_viz_parents": True,
            },
        },
        "models": {
            "A": {
                "sites": len(a_model["site_id"]),
                "lines": len(a_model["line_id"]),
                "directions": len(a_model["line_by_direction"]),
                "atoms": len(a_model["atom_desc"]),
            },
            "B": {
                "sites": len(b_model["site_id"]),
                "lines": len(b_model["line_id"]),
                "directions": len(b_model["line_by_direction"]),
                "atoms": len(b_model["atom_desc"]),
            },
        },
        "base_poison": {
            "A_atoms": bits_record(set_to_bits(base_a_atoms), len(a_model["atom_desc"])),
            "A_killed_words": len(a_domain) - legal_action_count,
            "A_legal_words": legal_action_count,
            "B_atoms": bits_record(b_base_atom_bits, len(b_model["atom_desc"])),
            "B_killed_words": bits_record(b_base_killed, len(b_domain)),
            "B_survivors_before_A": len(b_domain) - b_base_killed.bit_count(),
        },
        "quantified_availability": {
            "exists_A_exists_B": legal_action_count > 0 and max(survivor_counts) > 0,
            "forall_legal_A_exists_B": fatal_actions == 0,
            "exists_B_forall_legal_A": bool(universal_common_responses),
            "legal_A_actions": legal_action_count,
            "A_actions_with_no_B_response": fatal_actions,
            "minimum_B_survivors": {
                "count": survivor_counts[minimum_ordinal],
                "A_index": legal_actions[minimum_ordinal],
                "A_word": list(a_domain[legal_actions[minimum_ordinal]]),
                "killed_mask": bits_record(
                    killed_masks[minimum_ordinal], len(b_domain)
                ),
            },
            "maximum_B_survivors": {
                "count": survivor_counts[maximum_ordinal],
                "A_index": legal_actions[maximum_ordinal],
                "A_word": list(a_domain[legal_actions[maximum_ordinal]]),
            },
            "B_survivor_count_histogram": dict(sorted(Counter(survivor_counts).items())),
            "recorded_A_B_survivors": recorded_survivors,
            "universal_common_B_responses": bits_record(
                universal_common_responses, len(b_domain)
            ),
            "best_response_defined_action_class": {
                "B_index": best_response_index,
                "B_word": list(b_domain[best_response_index]),
                "actions": best_response_size,
                "action_membership": bits_record(
                    best_response_actions, legal_action_count
                ),
                "all_common_B_responses": bits_record(
                    best_class_common, len(b_domain)
                ),
                "warning": (
                    "this class is defined by immediate response survival; "
                    "it is not yet a future-state abstraction"
                ),
            },
        },
        "mask_compression": {
            "ordered_action_stream_sha256": stream.hexdigest(),
            "final_B_atom_mask_classes": class_statistics(atom_class_counter),
            "killed_B_word_mask_classes": class_statistics(killed_class_counter),
            "inclusion_maximal_killed_masks": len(maximal_killed_antichain),
            "inclusion_maximal_mask_stream_sha256": stable_hash([
                bits_record(mask, len(b_domain))
                for mask in maximal_killed_antichain
            ]),
            "maximal_antichain_semantics": (
                "worst-case/common-response dominance frontier at this B "
                "cursor; not the complete mask family or a future quotient"
            ),
            "inclusion_minimal_killed_masks": len(minimal_killed_antichain),
            "inclusion_minimal_mask_stream_sha256": stable_hash([
                bits_record(mask, len(b_domain))
                for mask in minimal_killed_antichain
            ]),
            "minimal_antichain_semantics": (
                "controller-favorable immediate dominance frontier at this "
                "B cursor; not a future transition congruence"
            ),
            "interpretation": (
                "equal B masks are exact one-edge availability classes only; "
                "the actual A word remains distinct in the ordered factor"
            ),
        },
        "cegar_partition": cegar,
        "transfer_decomposition": {
            "semantics": (
                "memberships overlap; incremental membership means outside "
                "the base-B killed mask, not unique causation"
            ),
            "channels": {
                channel: {
                    "effectful_legal_A_actions": channel_effectful_actions[channel],
                    "union_B_word_membership": bits_record(bits, len(b_domain)),
                    "union_incremental_after_base": bits_record(
                        bits & ~b_base_killed, len(b_domain)
                    ),
                }
                for channel, bits in channel_action_unions.items()
            },
            "prefix_endpoint_age_spatial_shell_P_A_B_memberships": {
                "scope": (
                    "attributes only the prefix endpoint of P-A-B site-secant "
                    "effects; excludes base poison, A-A-B, and A-B-B; masks overlap"
                ),
                "shell_definition": (
                    "shell0: d<=40; shell j>=1: "
                    "40*3^(j-1)<d<=40*3^j, Chebyshev distance from B midpoint"
                ),
                "all_possible_A_sites_are_shell0": True,
                "A_site_distance_range": [
                    min(a_site_distances_from_b),
                    max(a_site_distances_from_b),
                ],
                "memberships": {
                f"age{meta[0]}-shell{meta[1]}": {
                    "effectful_legal_A_actions": birth_shell_effectful_actions[meta],
                    "union_B_word_membership": bits_record(bits, len(b_domain)),
                    "union_incremental_after_base": bits_record(
                        bits & ~b_base_killed, len(b_domain)
                    ),
                }
                for meta, bits in birth_shell_action_unions.items()
                if bits
                },
            },
            "known_mixed_witness": {
                "A_point": list(recorded_a_interiors[0]),
                "tagged_endpoint": list(tagged_point),
                "B_site_offset": list(KNOWN_SITE_OFFSET),
                "B_atom": known_atom,
                "atom_word_membership": bits_record(known_word_mask, len(b_domain)),
                "present_in_recorded_A_effect": True,
            },
        },
        "independent_validation": {
            "base_A_packed_mask_equals_tuple_direction_recomputation": True,
            "optimized_recorded_A_atom_mask_equals_full_recomputation": True,
            "optimized_recorded_A_word_mask_equals_full_recomputation": True,
            "recorded_A_direct_legality_backstop": True,
            "recorded_B_direct_legality_backstop": True,
            "recorded_B_survives": True,
            "tagged_endpoint_ancestry_and_age_verified": True,
            "all_possible_A_sites_shell0_verified": True,
            "nonrecorded_length4_and_worst_action_validations": (
                independent_action_validations
            ),
        },
        "scope_warning": (
            "This proves exact claims only for one incoming prefix and the "
            "immediate A-to-B edge.  A greatest-fixed-point proof still needs "
            "a sound successor state, transition closure, and a controlled "
            "deep endpoint/secant residual."
        ),
        "actions": action_records,
    }

    headlines = {
        "base": (
            len(base_a_atoms), legal_action_count,
            len(b_base_atoms), b_base_killed.bit_count(),
        ),
        "availability": (
            fatal_actions,
            min(survivor_counts),
            max(survivor_counts),
            recorded_survivors,
            universal_common_responses.bit_count(),
            best_response_size,
        ),
        "classes": (
            len(atom_class_counter), len(killed_class_counter),
            len(maximal_killed_antichain), len(minimal_killed_antichain),
            cegar["nodes"], cegar["response_compatible_leaves"],
            cegar["unresolved_no_common_response_leaves"],
        ),
        "stream": stream.hexdigest(),
        "base_masks": (
            bits_sha256(set_to_bits(base_a_atoms), len(a_model["atom_desc"])),
            bits_sha256(b_base_atom_bits, len(b_model["atom_desc"])),
            bits_sha256(b_base_killed, len(b_domain)),
        ),
        "worst": (
            legal_actions[minimum_ordinal],
            bits_sha256(killed_masks[minimum_ordinal], len(b_domain)),
        ),
        "common": (
            bits_sha256(universal_common_responses, len(b_domain)),
            best_response_index,
            bits_sha256(best_response_actions, legal_action_count),
        ),
        "cegar": (
            cegar["tree_sha256"],
            cegar["largest_response_compatible_leaf"]["action_membership"][
                "mask_sha256"
            ],
            cegar["largest_response_compatible_leaf"]["common_response_mask"][
                "mask_sha256"
            ],
        ),
        "branch_validation": (
            tuple(record["A_domain_index"] for record in branch_validations),
            stable_hash(branch_validations),
        ),
        "third_ply_interface": (
            third_ply_interface_sha256,
            len(b_response_partition),
            sum(
                len(leaf["A_domain_indices"])
                for leaf in b_response_partition
            ),
            len(best_response_A_indices),
            len(best_class_common_B_indices),
            len(largest_leaf_A_indices),
            len(largest_leaf_common_B_indices),
        ),
    }
    result["regression_headlines"] = headlines
    print(json.dumps(headlines, sort_keys=True), flush=True)
    assert headlines == EXPECTED_HEADLINES

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {output_path} ({output_path.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l8-immediate-action-cegar.json"),
    )
    arguments = parser.parse_args()
    main(arguments.output)
