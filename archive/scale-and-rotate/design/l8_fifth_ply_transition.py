#!/usr/bin/env python3
"""Exact fifth-stitch transition test for the canonical L8 policy.

This checker consumes the pinned fourth-ply transition.  Its ten exact
response leaves retain all 1997 A words, fix B and C per leaf, and use the
same D word (domain index 0, word [0,3,4]) globally.  For the immediately
following scheduler stitch

    E = (pipeline rank 67014, gap 67012, step type 17),

the checker exhaustively computes

    Q_E(P,A,B,C,D)
      = BaseE(P) | UA(A) | UB(B) | UC(C) | UD(D)
                   | XAB | XAC | XAD | XBC | XBD | XCD.

``BaseE`` contains collision/P-P-E/P-E-E poison.  ``UX`` contains
collision-X-E, P-X-E, X-X-E, and X-E-E poison.  Each ``XY`` term contains
the E-site atoms hit by a secant with one endpoint in X and one in Y.  This
classification exhausts every old endpoint pair in P+A+B+C+D and every old
point on a candidate E-E line.  Candidate-internal E-E-E defects are excluded
by the certified E_17 connector domain.  All 250697 prefix points participate;
there is no distance cutoff.

If one source leaf has no common E word, an exact deterministic CEGAR tree
splits its actual A histories on genuinely A-dependent E-poison atoms outside
the fixed BaseE|UB|UC|UD|XBC|XBD|XCD mask.  Exact A indices and the already
chosen B,C,D remain attached to every transition record.  An unresolved
terminal is reported, not called game-losing: it only obstructs this selected
B,C,D policy.

Two complete ``compute_poison`` scans and independent sequential legality
checks harden the optimized union.  They do not replace the exhaustive mask
sweep and do not prove channel attribution is disjoint.

This is a finite fifth-ply transition certificate on one frozen L8 prefix.
It is not a future-state congruence, induction, or greatest fixed point.

Run from the repository root on one low-priority core::

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l8_fifth_ply_transition.py \
        --fourth-ply-certificate /tmp/l8-fourth-ply-transition-canonical.json \
        --output /tmp/l8-fifth-ply-transition.json

The checker refuses normal priority or unconstrained numerical-library thread
settings.  It is single-process and does not modify construction pickles or
the PM2 website.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import pickle
import struct
import sys
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import FRAGILE_CUT, MENU, word_interiors  # noqa: E402
from inherited_tile_lifetime import (  # noqa: E402
    build_context,
    exact_birth_levels,
    file_sha256,
    load_viz,
)
from salvage_gate import (  # noqa: E402
    add,
    build_domain_model,
    compute_poison,
    cross,
    midpoint,
    primitive,
    sub,
)
import l8_third_ply_closure as third  # noqa: E402


LEVEL = 8
A_GAP, B_GAP, C_GAP, D_GAP, E_GAP = 67009, 67011, 67008, 67013, 67012
A_STEP, B_STEP, C_STEP, D_STEP, E_STEP = 14, 34, 48, 19, 17
A_RANK, B_RANK, C_RANK, D_RANK, E_RANK = 67010, 67011, 67012, 67013, 67014

EXPECTED_FOURTH_PLY_CERTIFICATE_SHA256 = (
    "61ce7ebd1fdff96fbf7df2fd741223f447515bab6f61b1741fec132653d44e01"
)
EXPECTED_FOURTH_PLY_CERTIFICATE_BYTES = 408_307
EXPECTED_FOURTH_PLY_CHECKER_SHA256 = (
    "c69bcada5fca24352d67658b226c37260e44a6615b62b16fe3bf9dfc83b519fa"
)
EXPECTED_THIRD_PLY_HELPER_SHA256 = (
    "0b2b14b94bdf786075d3f3f5dcb70f2eb7ee5daa5ea23e9b943be7e56fc780db"
)
EXPECTED_FOURTH_PLY_TRANSITION_SHA256 = (
    "1500f0b8b686192e626be8d88aa5b586d3d7cc2677b814fecfa076e5bff76b7a"
)
EXPECTED_SOURCE_POLICY_SHA256 = (
    "81d85f1a5e21959d5e062c6a26cc43dc77fc54fd5acb810444feece41736d78d"
)
EXPECTED_POLICY_A_SHA256 = (
    "bb45f8742d6a5cdeca5edb5f26eb2daa6139d24f05bd052559a31a6f332f557e"
)

EXPECTED_DOMAIN_SIZES = {
    A_STEP: 5257,
    B_STEP: 9046,
    C_STEP: 49402,
    D_STEP: 6736,
    E_STEP: 35751,
}
EXPECTED_D_DOMAIN_SHA256 = (
    "e63b9bfef66167b664c0d8ae9545aa4da68d179b4b1c4744b10cfb7e9809ffdf"
)
EXPECTED_E_DOMAIN_SHA256 = (
    "904ecee1bce5e4bef67d2b3a94d72ab4bd71bb2e9501b44e1d3318c9d868bc04"
)
EXPECTED_E_MODEL = (264, 4579, 161, 4843)
EXPECTED_E_ATOM_DESC_SHA256 = (
    "846f5aeda28fda9a591c3fb3a496b80abbdb9f3af5949dfa4fd987c8d195e6ac"
)
EXPECTED_E_WORD_ATOMS_SHA256 = (
    "91d2ebcc5e7dbddaebc5e2e9ff28fed03bbb3a42b7ba6c21267f16ff71fad0da"
)
EXPECTED_E_START = (-71541, -1680, 13498)
EXPECTED_E_END = (-71547, -1680, 13501)
EXPECTED_A_START = (-71526, -1662, 13501)
EXPECTED_B_START = (-71538, -1674, 13503)
EXPECTED_C_START = (-71523, -1659, 13496)
EXPECTED_D_START = (-71547, -1680, 13501)
FIXED_D_DOMAIN_INDEX = 0
FIXED_D_WORD = (0, 3, 4)
RECORDED_E = (14, 21, 4)

EXPECTED_PREFIX_POINTS = third.EXPECTED_PREFIX_POINTS
EXPECTED_PREFIX_SHA256 = third.EXPECTED_PREFIX_SHA256
EXPECTED_PREFIX_BIRTH_SHA256 = third.EXPECTED_PREFIX_BIRTH_SHA256
EXPECTED_BIRTH_HISTOGRAM = third.EXPECTED_BIRTH_HISTOGRAM
THREAD_ENVIRONMENT = third.THREAD_ENVIRONMENT


stable_bytes = third.stable_bytes
stable_hash = third.stable_hash
bits_record = third.bits_record
point_set_sha256 = third.point_set_sha256
point_birth_sha256 = third.point_birth_sha256
atom_word_masks = third.atom_word_masks
atoms_to_word_bits = third.atoms_to_word_bits
poisoned_atom_bits = third.poisoned_atom_bits
union_bits = third.union_bits
iterate_set_bits = third.iterate_set_bits
direction_key = third.direction_key
atomic_write_json = third.atomic_write_json


def load_selected_domains():
    """Load only the five nonfragile D2--4 domains used by this checker."""
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        payload = pickle.load(handle)
    assert tuple(map(tuple, payload["menu"])) == tuple(MENU)
    raw_domains = payload["domains"]
    d24 = {step: len(words) for step, words in raw_domains.items()}
    selected = {}
    for step, expected in EXPECTED_DOMAIN_SIZES.items():
        assert d24[step] == expected
        assert d24[step] >= FRAGILE_CUT
        selected[step] = sorted(raw_domains[step], key=len)
    assert stable_hash(selected[D_STEP]) == EXPECTED_D_DOMAIN_SHA256
    assert stable_hash(selected[E_STEP]) == EXPECTED_E_DOMAIN_SHA256
    return selected, d24


def build_prefix(state, schedule, births7):
    """Reconstruct the exact pre-A point set, never recorded A/B/C words."""
    points = list(state["anchors"])
    births = list(births7)
    for entry in schedule[:A_RANK]:
        gap = entry["gap"]
        interiors = word_interiors(state["anchors"][gap], state["words"][gap])
        points.extend(interiors)
        births.extend([LEVEL] * len(interiors))
    assert len(points) == len(births) == len(set(points))
    return points, births


def validate_and_extract_policy(certificate_path):
    """Validate the canonical fourth transition and every exact leaf join."""
    assert certificate_path.stat().st_size == EXPECTED_FOURTH_PLY_CERTIFICATE_BYTES
    raw_sha256 = file_sha256(certificate_path)
    assert raw_sha256 == EXPECTED_FOURTH_PLY_CERTIFICATE_SHA256
    with certificate_path.open() as handle:
        certificate = json.load(handle)

    assert certificate["checker_sha256"] == EXPECTED_FOURTH_PLY_CHECKER_SHA256
    assert certificate["checker_sha256"] == file_sha256(
        ROOT / "design/l8_fourth_ply_transition.py"
    )
    assert certificate["input_sha256"] == third.EXPECTED_INPUT_SHA256
    assert certificate["third_ply_certificate"][
        "policy_partition_sha256"
    ] == EXPECTED_SOURCE_POLICY_SHA256
    assert certificate["conclusions"][
        "every_selected_exact_A_B_C_history_has_some_D"
    ] is True
    assert certificate["conclusions"][
        "exact_finite_fourth_ply_transition_for_selected_policy"
    ] is True
    assert certificate["conclusions"]["unconditional_infinite_walk_theorem"] is False

    transition = certificate["fourth_ply_transition"]
    claimed_transition_sha256 = transition["fourth_ply_transition_sha256"]
    unhashed_transition = dict(transition)
    del unhashed_transition["fourth_ply_transition_sha256"]
    assert stable_hash(unhashed_transition) == claimed_transition_sha256
    assert claimed_transition_sha256 == EXPECTED_FOURTH_PLY_TRANSITION_SHA256
    assert transition["source_policy_sha256"] == EXPECTED_SOURCE_POLICY_SHA256
    assert transition["source_policy_leaves"] == 10
    assert transition["source_A_actions"] == 1997
    assert transition["source_A_domain_indices_sha256"] == EXPECTED_POLICY_A_SHA256
    assert transition["total_D_response_leaves"] == 10
    assert transition["unresolved_terminals"] == 0
    assert transition["unresolved_A_actions"] == 0
    assert transition["terminal_partition_covers_every_source_A_exactly_once"] is True
    assert transition["D_policy_covers_every_source_A_exactly_once"] is True
    assert transition["exact_finite_fourth_ply_transition_available"] is True
    assert transition["actual_history_triples_remain_distinct"] is True
    assert transition["future_state_congruence_or_GFP_proved"] is False
    assert not transition["unresolved_terminal_records"]

    source_results = {
        record["source_policy_leaf_position"]: record
        for record in certificate["source_leaf_results"]
    }
    assert len(source_results) == 10
    covered = []
    leaves = []
    fixed_d_choices = set()
    for position, leaf in enumerate(transition["response_leaf_lookup_records"]):
        actions = leaf["A_domain_indices"]
        assert actions == sorted(set(actions))
        assert len(actions) == leaf["A_actions"]
        assert stable_hash(actions) == leaf["A_domain_indices_sha256"]
        assert leaf["common_D_response_mask"]["bits"] > 0
        assert leaf["history_triples_sha256"] == stable_hash([
            [
                a_index,
                leaf["fixed_B_domain_index"],
                leaf["fixed_C_domain_index"],
            ]
            for a_index in actions
        ])

        source_position = leaf["source_policy_leaf_position"]
        source = source_results[source_position]
        assert leaf["source_class"] == source["source_class"]
        assert leaf["fixed_B_domain_index"] == source["fixed_B_domain_index"]
        assert leaf["fixed_B_word"] == source["fixed_B_word"]
        assert leaf["fixed_C_domain_index"] == source["fixed_C_domain_index"]
        assert leaf["fixed_C_word"] == source["fixed_C_word"]
        cegar = source["D_response_CEGAR"]
        assert leaf["D_response_tree_sha256"] == cegar["tree_sha256"]
        matching_d_leaf = [
            record for record in cegar["response_compatible_leaf_records"]
            if record["node_id"] == leaf["D_response_leaf_node_id"]
        ]
        assert len(matching_d_leaf) == 1
        d_leaf = matching_d_leaf[0]
        assert d_leaf["A_domain_indices"] == actions
        assert d_leaf["predicate_path"] == leaf["D_predicate_path"]
        assert d_leaf["least_common_D_domain_index"] == leaf[
            "fixed_D_domain_index"
        ]
        assert d_leaf["least_common_D_word"] == leaf["fixed_D_word"]
        assert d_leaf["common_D_response_mask"] == leaf[
            "common_D_response_mask"
        ]
        fixed_d_choices.add((
            leaf["fixed_D_domain_index"], tuple(leaf["fixed_D_word"])
        ))

        covered.extend(actions)
        leaves.append({
            "source_transition_leaf_position": position,
            "source_policy_leaf_position": source_position,
            "source_class": leaf["source_class"],
            "source_C_response_tree_sha256": leaf[
                "source_C_response_tree_sha256"
            ],
            "source_C_response_leaf_node_id": leaf[
                "source_C_response_leaf_node_id"
            ],
            "source_predicate_path": leaf["source_predicate_path"],
            "source_D_response_tree_sha256": leaf[
                "D_response_tree_sha256"
            ],
            "source_D_response_leaf_node_id": leaf[
                "D_response_leaf_node_id"
            ],
            "source_D_predicate_path": leaf["D_predicate_path"],
            "A_domain_indices": actions,
            "A_domain_indices_sha256": leaf["A_domain_indices_sha256"],
            "fixed_B_domain_index": leaf["fixed_B_domain_index"],
            "fixed_B_word": leaf["fixed_B_word"],
            "fixed_C_domain_index": leaf["fixed_C_domain_index"],
            "fixed_C_word": leaf["fixed_C_word"],
            "fixed_D_domain_index": leaf["fixed_D_domain_index"],
            "fixed_D_word": leaf["fixed_D_word"],
        })

    assert len(leaves) == 10
    assert fixed_d_choices == {(FIXED_D_DOMAIN_INDEX, FIXED_D_WORD)}
    assert len(covered) == len(set(covered)) == 1997
    assert stable_hash(sorted(covered)) == EXPECTED_POLICY_A_SHA256
    return certificate, leaves, raw_sha256, claimed_transition_sha256


def source_to_destination_unary_transfer(
    prefix,
    prefix_set,
    source_model,
    source_start,
    destination_model,
    destination_start,
    source_label,
):
    """Map every source atom to exact unary poison in the E corridor."""
    source_atom_count = len(source_model["atom_desc"])
    channel_names = (
        f"collision-{source_label}-E",
        f"P-{source_label}-E",
        f"{source_label}-E-E",
        f"{source_label}-{source_label}-E",
    )
    channels = {name: [0] * source_atom_count for name in channel_names}
    total = [0] * source_atom_count
    destination_sites = [
        (add(destination_start, offset), atom)
        for offset, atom in destination_model["site_id"].items()
    ]
    destination_directions = list(
        destination_model["line_by_direction"].items()
    )

    source_sites = [
        (add(source_start, offset), atom)
        for offset, atom in source_model["site_id"].items()
    ]
    for position, (x, source_atom) in enumerate(source_sites, 1):
        directions = set()
        for p in prefix:
            key = direction_key(sub(p, x))
            if key is not None:
                directions.add(key)

        collision = 0
        prefix_site = 0
        for q, destination_atom in destination_sites:
            flag = 1 << destination_atom
            if q == x:
                collision |= flag
            elif q not in prefix_set and direction_key(sub(q, x)) in directions:
                prefix_site |= flag

        source_on_destination_line = 0
        relative = sub(x, destination_start)
        for direction, by_moment in destination_directions:
            destination_atom = by_moment.get(cross(relative, direction))
            if destination_atom is not None:
                source_on_destination_line |= 1 << destination_atom

        channels[f"collision-{source_label}-E"][source_atom] = collision
        channels[f"P-{source_label}-E"][source_atom] = prefix_site
        channels[f"{source_label}-E-E"][source_atom] = (
            source_on_destination_line
        )
        total[source_atom] = (
            collision | prefix_site | source_on_destination_line
        )
        del directions
        if position % 20 == 0 or position == len(source_sites):
            print(
                f"{source_label}-site to E unary transfer: "
                f"{position}/{len(source_sites)}",
                flush=True,
            )

    start_moments = {
        direction: cross(source_start, direction)
        for direction in source_model["line_by_direction"]
    }
    local_source_sites = tuple(source_model["site_id"])
    for (direction, local_moment), source_atom in source_model["line_id"].items():
        origin_moment = start_moments[direction]
        # ``line_key`` stores m=cross(local_point,u) for the canonical
        # primitive direction u.  Translation by s gives
        # cross(s+local_point,u)=cross(s,u)+m.  Verify that identity against
        # an actual local site on every source line before using the moment.
        witness_offsets = [
            offset for offset in local_source_sites
            if cross(offset, direction) == local_moment
        ]
        assert len(witness_offsets) >= 2
        absolute_moment = tuple(
            origin_moment[index] + local_moment[index] for index in range(3)
        )
        assert cross(
            add(source_start, witness_offsets[0]), direction
        ) == absolute_moment
        effect = 0
        for q, destination_atom in destination_sites:
            if q in prefix_set:
                continue
            if cross(q, direction) == absolute_moment:
                effect |= 1 << destination_atom
        channels[f"{source_label}-{source_label}-E"][source_atom] = effect
        total[source_atom] |= effect

    return {"total": total, "channels": channels}


def aggregate_source_word(source_atoms, transfer):
    channel_bits = {
        name: union_bits(values[atom] for atom in source_atoms)
        for name, values in transfer["channels"].items()
    }
    total = union_bits(transfer["total"][atom] for atom in source_atoms)
    assert total == union_bits(channel_bits.values())
    return total, channel_bits


def fixed_point_to_destination_effect(
    point,
    prefix,
    prefix_set,
    destination_start,
    destination_sites,
    destination_directions,
):
    directions = set()
    for p in prefix:
        key = direction_key(sub(p, point))
        if key is not None:
            directions.add(key)

    collision = 0
    prefix_site = 0
    for q, destination_atom in destination_sites:
        flag = 1 << destination_atom
        if q == point:
            collision |= flag
        elif q not in prefix_set and direction_key(sub(q, point)) in directions:
            prefix_site |= flag

    point_on_destination_line = 0
    relative = sub(point, destination_start)
    for direction, by_moment in destination_directions:
        destination_atom = by_moment.get(cross(relative, direction))
        if destination_atom is not None:
            point_on_destination_line |= 1 << destination_atom
    return collision, prefix_site, point_on_destination_line


def fixed_pair_to_destination_effect(
    a,
    b,
    prefix_set,
    destination_sites,
):
    assert a != b
    direction = primitive(sub(b, a))
    assert direction is not None
    moment = cross(a, direction)
    effect = 0
    for q, destination_atom in destination_sites:
        if q in prefix_set:
            continue
        if cross(q, direction) == moment:
            effect |= 1 << destination_atom
    return effect


def fixed_word_to_destination_effect(
    points,
    source_label,
    prefix,
    prefix_set,
    destination_start,
    destination_sites,
    destination_directions,
    point_cache,
    pair_cache,
):
    """Exact collision/P-X-E/X-X-E/X-E-E effect of one fixed word."""
    assert len(points) == len(set(points))
    channels = {
        f"collision-{source_label}-E": 0,
        f"P-{source_label}-E": 0,
        f"{source_label}-{source_label}-E": 0,
        f"{source_label}-E-E": 0,
    }
    for point in points:
        if point not in point_cache:
            point_cache[point] = fixed_point_to_destination_effect(
                point,
                prefix,
                prefix_set,
                destination_start,
                destination_sites,
                destination_directions,
            )
        collision, prefix_site, on_line = point_cache[point]
        channels[f"collision-{source_label}-E"] |= collision
        channels[f"P-{source_label}-E"] |= prefix_site
        channels[f"{source_label}-E-E"] |= on_line

    for position, a in enumerate(points):
        for b in points[position + 1 :]:
            key = tuple(sorted((a, b)))
            if key not in pair_cache:
                pair_cache[key] = fixed_pair_to_destination_effect(
                    a, b, prefix_set, destination_sites
                )
            channels[f"{source_label}-{source_label}-E"] |= pair_cache[key]
    return union_bits(channels.values()), channels


def source_fixed_cross_to_destination_transfer(
    source_model,
    source_start,
    fixed_points,
    prefix_set,
    destination_sites,
):
    """Return source-site-atom -> E-site masks for one mixed pair term."""
    result = [0] * len(source_model["atom_desc"])
    for offset, source_atom in source_model["site_id"].items():
        x = add(source_start, offset)
        effect = 0
        for y in fixed_points:
            if x == y:
                # An unused source atom may coincide with this fixed word,
                # but a repeated point supplies no secant direction.  Every
                # actually aggregated policy word is checked disjoint below.
                continue
            direction = primitive(sub(y, x))
            assert direction is not None
            moment = cross(x, direction)
            for q, destination_atom in destination_sites:
                if q in prefix_set:
                    continue
                if cross(q, direction) == moment:
                    effect |= 1 << destination_atom
        result[source_atom] = effect
    return result


def fixed_words_cross_to_destination_effect(
    x_points,
    y_points,
    prefix_set,
    destination_sites,
    pair_cache,
):
    effect = 0
    for x in x_points:
        for y in y_points:
            assert x != y
            key = tuple(sorted((x, y)))
            if key not in pair_cache:
                pair_cache[key] = fixed_pair_to_destination_effect(
                    x, y, prefix_set, destination_sites
                )
            effect |= pair_cache[key]
    return effect


def effect_record(atom_bits, atom_count, word_masks, word_count):
    killed = atoms_to_word_bits(atom_bits, word_masks)
    return {
        "atoms": bits_record(atom_bits, atom_count),
        "killed_E_words": bits_record(killed, word_count),
    }


def exact_e_response_cegar_partition(
    a_indices,
    final_atom_masks,
    final_killed_masks,
    fixed_atom_mask,
    e_model,
    e_domain,
):
    """Build an exact deterministic E-response tree inside one source leaf."""
    action_count = len(a_indices)
    e_word_count = len(e_domain)
    e_atom_count = len(e_model["atom_desc"])
    assert action_count == len(final_atom_masks) == len(final_killed_masks)
    assert action_count > 0
    full_actions = (1 << action_count) - 1
    full_e_words = (1 << e_word_count) - 1
    root_common_e = full_e_words & ~union_bits(final_killed_masks)

    feature_actions = [0] * e_atom_count
    for ordinal, final_atoms in enumerate(final_atom_masks):
        for atom in iterate_set_bits(final_atoms & ~fixed_atom_mask):
            feature_actions[atom] |= 1 << ordinal
    feature_items = [
        (atom, membership)
        for atom, membership in enumerate(feature_actions)
        if membership not in (0, full_actions)
    ]

    nodes = [None]
    response_leaf_ids = []
    unresolved_ids = []
    stack = [(0, full_actions, 0, [])]
    while stack:
        node_id, action_bits, depth, predicate_path = stack.pop()
        size = action_bits.bit_count()
        assert size > 0
        killed_union = union_bits(
            final_killed_masks[ordinal]
            for ordinal in iterate_set_bits(action_bits)
        )
        common_e = full_e_words & ~killed_union
        domain_indices = [
            a_indices[ordinal] for ordinal in iterate_set_bits(action_bits)
        ]
        if common_e:
            least_e = (common_e & -common_e).bit_length() - 1
            nodes[node_id] = {
                "node_id": node_id,
                "status": "response-compatible-leaf",
                "depth": depth,
                "actions": size,
                "predicate_path": predicate_path,
                "A_domain_indices": domain_indices,
                "A_domain_indices_sha256": stable_hash(domain_indices),
                "action_membership": bits_record(action_bits, action_count),
                "common_E_responses": common_e.bit_count(),
                "common_E_response_mask": bits_record(
                    common_e, e_word_count
                ),
                "least_common_E_domain_index": least_e,
                "least_common_E_word": list(e_domain[least_e]),
            }
            response_leaf_ids.append(node_id)
            continue

        best = None
        for atom, membership in feature_items:
            inside = (action_bits & membership).bit_count()
            if inside == 0 or inside == size:
                continue
            balance = min(inside, size - inside)
            candidate = (balance, -atom, atom, membership, inside)
            if best is None or candidate[:2] > best[:2]:
                best = candidate

        if best is None:
            unresolved_ordinals = list(iterate_set_bits(action_bits))
            assert all(
                final_killed_masks[ordinal] == full_e_words
                for ordinal in unresolved_ordinals
            )
            nodes[node_id] = {
                "node_id": node_id,
                "status": "unresolved-no-common-response-terminal",
                "depth": depth,
                "actions": size,
                "predicate_path": predicate_path,
                "A_domain_indices": domain_indices,
                "A_domain_indices_sha256": stable_hash(domain_indices),
                "action_membership": bits_record(action_bits, action_count),
                "reason": (
                    "no genuinely A-dependent nonfixed E-poison atom splits "
                    "this response-incompatible class; every exact history "
                    "here is fatal for the selected B,C,D, but this is not "
                    "called game-losing"
                ),
            }
            unresolved_ids.append(node_id)
            continue

        _balance, _negative_atom, atom, membership, inside = best
        absent = action_bits & ~membership
        present = action_bits & membership
        absent_id = len(nodes)
        present_id = absent_id + 1
        nodes.extend((None, None))
        description = e_model["atom_desc"][atom]
        nodes[node_id] = {
            "node_id": node_id,
            "status": "split",
            "depth": depth,
            "actions": size,
            "predicate_path": predicate_path,
            "A_domain_indices": domain_indices,
            "A_domain_indices_sha256": stable_hash(domain_indices),
            "action_membership": bits_record(action_bits, action_count),
            "feature_E_atom": atom,
            "feature_description": description,
            "feature_is_outside_fixed_BaseE_UB_UC_UD_XBC_XBD_XCD": True,
            "feature_membership_is_A_dependent_at_this_node": True,
            "feature_present": inside,
            "feature_absent": size - inside,
            "absent_child_node": absent_id,
            "present_child_node": present_id,
        }
        absent_path = predicate_path + [{
            "E_atom": atom,
            "description": description,
            "A_dependent_poison_present": False,
        }]
        present_path = predicate_path + [{
            "E_atom": atom,
            "description": description,
            "A_dependent_poison_present": True,
        }]
        stack.append((present_id, present, depth + 1, present_path))
        stack.append((absent_id, absent, depth + 1, absent_path))

    assert all(record is not None for record in nodes)
    response_records = [nodes[node_id] for node_id in response_leaf_ids]
    unresolved_records = [nodes[node_id] for node_id in unresolved_ids]
    ordinal_by_domain_index = {
        domain_index: ordinal for ordinal, domain_index in enumerate(a_indices)
    }
    assert len(ordinal_by_domain_index) == action_count
    terminal_membership = 0
    for record in response_records + unresolved_records:
        for domain_index in record["A_domain_indices"]:
            flag = 1 << ordinal_by_domain_index[domain_index]
            assert not (terminal_membership & flag)
            terminal_membership |= flag
    assert terminal_membership == full_actions
    assert sum(
        record["actions"] for record in response_records + unresolved_records
    ) == action_count
    assert all(record["common_E_responses"] > 0 for record in response_records)
    assert all(
        0 <= record["least_common_E_domain_index"] < e_word_count
        and record["least_common_E_word"]
        == list(e_domain[record["least_common_E_domain_index"]])
        for record in response_records
    )
    assert all(
        record["actions"] != 1
        or final_killed_masks[
            ordinal_by_domain_index[record["A_domain_indices"][0]]
        ] == full_e_words
        for record in unresolved_records
    )

    largest = max(
        response_records,
        key=lambda record: (
            record["actions"],
            record["common_E_responses"],
            -record["node_id"],
        ),
        default=None,
    )
    unresolved_actions = sum(record["actions"] for record in unresolved_records)
    return {
        "semantics": (
            "a response-compatible leaf has a fixed E word legal for every "
            "exact A history in it; response-incompatible nodes are greedily "
            "split on balanced A-dependent E-poison membership"
        ),
        "scope": (
            "one frozen prefix and one fourth-ply leaf with fixed B,C,D; "
            "not a future-state congruence or greatest fixed point"
        ),
        "minimality": "deterministic greedy balanced split; not claimed minimal",
        "A_domain_indices": a_indices,
        "A_domain_indices_sha256": stable_hash(a_indices),
        "fixed_BaseE_UB_UC_UD_XBC_XBD_XCD_atoms": bits_record(
            fixed_atom_mask, e_atom_count
        ),
        "root_common_E_response_mask": bits_record(
            root_common_e, e_word_count
        ),
        "genuinely_A_dependent_feature_atoms": len(feature_items),
        "root_node": 0,
        "nodes": len(nodes),
        "tree_sha256": stable_hash(nodes),
        "node_records": nodes,
        "terminal_records_cover_every_A_exactly_once": True,
        "response_compatible_leaves": len(response_records),
        "unresolved_no_common_response_terminals": len(unresolved_records),
        "unresolved_A_actions": unresolved_actions,
        "max_depth": max(record["depth"] for record in nodes),
        "leaf_depth_histogram": dict(sorted(Counter(
            record["depth"] for record in response_records
        ).items())),
        "response_compatible_leaf_records": response_records,
        "unresolved_terminal_records": unresolved_records,
        "largest_response_compatible_leaf": largest,
    }


def initialize_history_digest(source_leaf, e_atom_count, e_word_count):
    binding = {
        "schema": "l8-fifth-ply-history-stream-v1",
        "source_transition_sha256": EXPECTED_FOURTH_PLY_TRANSITION_SHA256,
        "source_transition_leaf_position": source_leaf[
            "source_transition_leaf_position"
        ],
        "source_policy_leaf_position": source_leaf[
            "source_policy_leaf_position"
        ],
        "A_domain_indices_sha256": source_leaf["A_domain_indices_sha256"],
        "fixed_B_domain_index": source_leaf["fixed_B_domain_index"],
        "fixed_C_domain_index": source_leaf["fixed_C_domain_index"],
        "fixed_D_domain_index": source_leaf["fixed_D_domain_index"],
        "E_atom_bits": e_atom_count,
        "E_word_bits": e_word_count,
    }
    digest = hashlib.sha256()
    digest.update(stable_bytes(binding))
    digest.update(b"\n")
    return digest, binding


def update_history_digest(
    digest,
    a_index,
    atom_bits,
    killed_bits,
    atom_bytes,
    word_bytes,
):
    digest.update(struct.pack("<I", a_index))
    digest.update(atom_bits.to_bytes(atom_bytes, "little"))
    digest.update(killed_bits.to_bytes(word_bytes, "little"))


def candidate_identity(candidate):
    return (
        candidate["A_domain_index"],
        candidate["B_domain_index"],
        candidate["C_domain_index"],
        candidate["D_domain_index"],
    )


def compact_candidate(candidate, e_atom_count, e_word_count):
    return {
        "source_transition_leaf_position": candidate[
            "source_transition_leaf_position"
        ],
        "source_policy_leaf_position": candidate[
            "source_policy_leaf_position"
        ],
        "A_domain_index": candidate["A_domain_index"],
        "B_domain_index": candidate["B_domain_index"],
        "C_domain_index": candidate["C_domain_index"],
        "D_domain_index": candidate["D_domain_index"],
        "E_survivors": candidate["E_survivors"],
        "least_E_survivor": candidate["least_E_survivor"],
        "incremental_pair_atoms_beyond_BaseE_and_unaries": bits_record(
            candidate["incremental_pair_atoms"], e_atom_count
        ),
        "incremental_pair_killed_E_words_beyond_BaseE_and_unaries": bits_record(
            candidate["incremental_pair_killed_words"], e_word_count
        ),
        "all_pair_term_atoms": bits_record(
            candidate["pair_atom_bits"], e_atom_count
        ),
        "final_E_atoms": bits_record(
            candidate["final_atom_bits"], e_atom_count
        ),
        "final_killed_E_words": bits_record(
            candidate["final_killed_bits"], e_word_count
        ),
    }


def direct_response_checks(
    source_leaf,
    cegar,
    prefix,
    a_domain,
    b_domain,
    c_domain,
    d_domain,
    e_domain,
    a_start,
    b_start,
    c_start,
    d_start,
    e_start,
):
    """Check first/last exact histories for every emitted common E response."""
    records = []
    prefix_set = set(prefix)
    b_index = source_leaf["fixed_B_domain_index"]
    c_index = source_leaf["fixed_C_domain_index"]
    d_index = source_leaf["fixed_D_domain_index"]
    for leaf in cegar["response_compatible_leaf_records"]:
        selected = {}
        for role, a_index in (
            ("first-A-in-E-response-leaf", leaf["A_domain_indices"][0]),
            ("last-A-in-E-response-leaf", leaf["A_domain_indices"][-1]),
        ):
            selected.setdefault(a_index, []).append(role)
        e_index = leaf["least_common_E_domain_index"]
        for a_index, roles in selected.items():
            a_points = word_interiors(a_start, a_domain[a_index])
            b_points = word_interiors(b_start, b_domain[b_index])
            c_points = word_interiors(c_start, c_domain[c_index])
            d_points = word_interiors(d_start, d_domain[d_index])
            assert not (set(a_points) & prefix_set)
            assert not (set(b_points) & (prefix_set | set(a_points)))
            assert not (
                set(c_points)
                & (prefix_set | set(a_points) | set(b_points))
            )
            assert not (
                set(d_points)
                & (
                    prefix_set | set(a_points) | set(b_points) | set(c_points)
                )
            )
            store = Store(prefix)
            assert word_legal_fast(a_start, a_domain[a_index], store, {}, MENU)
            store.add_many(a_points)
            assert word_legal_fast(b_start, b_domain[b_index], store, {}, MENU)
            store.add_many(b_points)
            assert word_legal_fast(c_start, c_domain[c_index], store, {}, MENU)
            store.add_many(c_points)
            assert word_legal_fast(d_start, d_domain[d_index], store, {}, MENU)
            store.add_many(d_points)
            assert word_legal_fast(e_start, e_domain[e_index], store, {}, MENU)
            records.append({
                "E_response_leaf_node_id": leaf["node_id"],
                "A_domain_index": a_index,
                "roles": roles,
                "B_domain_index": b_index,
                "C_domain_index": c_index,
                "D_domain_index": d_index,
                "E_domain_index": e_index,
                "A_then_B_then_C_then_D_then_E_sequential_legality": True,
            })
    return records


def sweep_policy_leaf(source_leaf, context, candidate_observer):
    a_domain = context["a_domain"]
    b_domain = context["b_domain"]
    c_domain = context["c_domain"]
    d_domain = context["d_domain"]
    e_domain = context["e_domain"]
    a_model = context["a_model"]
    e_model = context["e_model"]
    e_word_masks = context["e_word_masks"]
    e_atom_count = len(e_model["atom_desc"])
    e_word_count = len(e_domain)
    full_e_words = (1 << e_word_count) - 1
    atom_bytes = (e_atom_count + 7) // 8
    word_bytes = (e_word_count + 7) // 8
    prefix = context["prefix"]
    prefix_set = context["prefix_set"]
    a_start = context["a_start"]
    b_start = context["b_start"]
    c_start = context["c_start"]
    d_start = context["d_start"]
    e_start = context["e_start"]
    destination_sites = context["destination_sites"]

    a_indices = source_leaf["A_domain_indices"]
    b_index = source_leaf["fixed_B_domain_index"]
    c_index = source_leaf["fixed_C_domain_index"]
    d_index = source_leaf["fixed_D_domain_index"]
    assert d_index == FIXED_D_DOMAIN_INDEX
    assert list(b_domain[b_index]) == source_leaf["fixed_B_word"]
    assert list(c_domain[c_index]) == source_leaf["fixed_C_word"]
    assert list(d_domain[d_index]) == source_leaf["fixed_D_word"]
    assert tuple(d_domain[d_index]) == FIXED_D_WORD
    b_points = word_interiors(b_start, b_domain[b_index])
    c_points = word_interiors(c_start, c_domain[c_index])
    d_points = word_interiors(d_start, d_domain[d_index])
    assert not (set(b_points) & prefix_set)
    assert not (set(c_points) & (prefix_set | set(b_points)))
    assert not (
        set(d_points) & (prefix_set | set(b_points) | set(c_points))
    )

    fixed_word_cache = context["fixed_word_cache"]
    b_key = ("B", b_index)
    if b_key not in fixed_word_cache:
        fixed_word_cache[b_key] = fixed_word_to_destination_effect(
            b_points,
            "B",
            prefix,
            prefix_set,
            e_start,
            destination_sites,
            context["destination_directions"],
            context["fixed_point_cache"],
            context["fixed_pair_cache"],
        )
    c_key = ("C", c_index)
    if c_key not in fixed_word_cache:
        fixed_word_cache[c_key] = fixed_word_to_destination_effect(
            c_points,
            "C",
            prefix,
            prefix_set,
            e_start,
            destination_sites,
            context["destination_directions"],
            context["fixed_point_cache"],
            context["fixed_pair_cache"],
        )
    d_key = ("D", d_index)
    if d_key not in fixed_word_cache:
        fixed_word_cache[d_key] = fixed_word_to_destination_effect(
            d_points,
            "D",
            prefix,
            prefix_set,
            e_start,
            destination_sites,
            context["destination_directions"],
            context["fixed_point_cache"],
            context["fixed_pair_cache"],
        )
    ub_bits, ub_channels = fixed_word_cache[b_key]
    uc_bits, uc_channels = fixed_word_cache[c_key]
    ud_bits, ud_channels = fixed_word_cache[d_key]

    cross_transfer_cache = context["cross_transfer_cache"]
    if b_key not in cross_transfer_cache:
        cross_transfer_cache[b_key] = source_fixed_cross_to_destination_transfer(
            a_model,
            a_start,
            b_points,
            prefix_set,
            destination_sites,
        )
    if c_key not in cross_transfer_cache:
        cross_transfer_cache[c_key] = source_fixed_cross_to_destination_transfer(
            a_model,
            a_start,
            c_points,
            prefix_set,
            destination_sites,
        )
    if d_key not in cross_transfer_cache:
        cross_transfer_cache[d_key] = source_fixed_cross_to_destination_transfer(
            a_model,
            a_start,
            d_points,
            prefix_set,
            destination_sites,
        )
    xab_transfer = cross_transfer_cache[b_key]
    xac_transfer = cross_transfer_cache[c_key]
    xad_transfer = cross_transfer_cache[d_key]

    bc_key = (b_index, c_index)
    if bc_key not in context["xbc_cache"]:
        context["xbc_cache"][bc_key] = fixed_words_cross_to_destination_effect(
            b_points,
            c_points,
            prefix_set,
            destination_sites,
            context["fixed_pair_cache"],
        )
    xbc_bits = context["xbc_cache"][bc_key]
    bd_key = (b_index, d_index)
    if bd_key not in context["xbd_cache"]:
        context["xbd_cache"][bd_key] = fixed_words_cross_to_destination_effect(
            b_points,
            d_points,
            prefix_set,
            destination_sites,
            context["fixed_pair_cache"],
        )
    xbd_bits = context["xbd_cache"][bd_key]
    cd_key = (c_index, d_index)
    if cd_key not in context["xcd_cache"]:
        context["xcd_cache"][cd_key] = fixed_words_cross_to_destination_effect(
            c_points,
            d_points,
            prefix_set,
            destination_sites,
            context["fixed_pair_cache"],
        )
    xcd_bits = context["xcd_cache"][cd_key]
    fixed_atoms = (
        context["base_e_atoms"]
        | ub_bits | uc_bits | ud_bits
        | xbc_bits | xbd_bits | xcd_bits
    )

    final_atom_masks = []
    final_killed_masks = []
    common_e = full_e_words
    fatal_histories = 0
    survivor_histogram = Counter()
    minimum = None
    maximum = None
    component_unions = {
        "BaseE": context["base_e_atoms"],
        "UA": 0,
        "UB": ub_bits,
        "UC": uc_bits,
        "UD": ud_bits,
        "XAB": 0,
        "XAC": 0,
        "XAD": 0,
        "XBC": xbc_bits,
        "XBD": xbd_bits,
        "XCD": xcd_bits,
    }
    channel_unions = {
        **{name: 0 for name in context["a_unary_transfer"]["channels"]},
        **ub_channels,
        **uc_channels,
        **ud_channels,
        "A-B-E": 0,
        "A-C-E": 0,
        "A-D-E": 0,
        "B-C-E": xbc_bits,
        "B-D-E": xbd_bits,
        "C-D-E": xcd_bits,
    }
    digest, stream_binding = initialize_history_digest(
        source_leaf, e_atom_count, e_word_count
    )

    for ordinal, a_index in enumerate(a_indices, 1):
        if a_index not in context["ua_cache"]:
            context["ua_cache"][a_index] = aggregate_source_word(
                a_model["word_atoms"][a_index],
                context["a_unary_transfer"],
            )
        ua_bits, ua_channels = context["ua_cache"][a_index]
        a_points = word_interiors(a_start, a_domain[a_index])
        assert len(a_points) == len(set(a_points))
        assert not (set(a_points) & prefix_set)
        assert not (set(a_points) & set(b_points))
        assert not (set(a_points) & set(c_points))
        assert not (set(a_points) & set(d_points))

        xab_bits = union_bits(
            xab_transfer[atom] for atom in a_model["word_atoms"][a_index]
        )
        xac_bits = union_bits(
            xac_transfer[atom] for atom in a_model["word_atoms"][a_index]
        )
        xad_bits = union_bits(
            xad_transfer[atom] for atom in a_model["word_atoms"][a_index]
        )
        without_pairs = (
            context["base_e_atoms"] | ua_bits | ub_bits | uc_bits | ud_bits
        )
        pair_bits = (
            xab_bits | xac_bits | xad_bits
            | xbc_bits | xbd_bits | xcd_bits
        )
        final_atoms = without_pairs | pair_bits
        killed = atoms_to_word_bits(final_atoms, e_word_masks)
        without_pairs_killed = atoms_to_word_bits(
            without_pairs, e_word_masks
        )
        survivor_bits = full_e_words & ~killed
        survivors = survivor_bits.bit_count()
        least_e = None
        if survivor_bits:
            least_e = (survivor_bits & -survivor_bits).bit_length() - 1
        else:
            fatal_histories += 1

        incremental_pair_atoms = pair_bits & ~without_pairs
        incremental_pair_words = killed & ~without_pairs_killed
        final_atom_masks.append(final_atoms)
        final_killed_masks.append(killed)
        common_e &= survivor_bits
        survivor_histogram[survivors] += 1
        summary = (survivors, a_index)
        if minimum is None or summary < (
            minimum["count"], minimum["A_domain_index"]
        ):
            minimum = {"count": survivors, "A_domain_index": a_index}
        if maximum is None or summary > (
            maximum["count"], maximum["A_domain_index"]
        ):
            maximum = {"count": survivors, "A_domain_index": a_index}
        update_history_digest(
            digest,
            a_index,
            final_atoms,
            killed,
            atom_bytes,
            word_bytes,
        )

        component_unions["UA"] |= ua_bits
        component_unions["XAB"] |= xab_bits
        component_unions["XAC"] |= xac_bits
        component_unions["XAD"] |= xad_bits
        for name, bits in ua_channels.items():
            channel_unions[name] |= bits
        channel_unions["A-B-E"] |= xab_bits
        channel_unions["A-C-E"] |= xac_bits
        channel_unions["A-D-E"] |= xad_bits
        candidate_observer({
            "source_transition_leaf_position": source_leaf[
                "source_transition_leaf_position"
            ],
            "source_policy_leaf_position": source_leaf[
                "source_policy_leaf_position"
            ],
            "A_domain_index": a_index,
            "B_domain_index": b_index,
            "C_domain_index": c_index,
            "D_domain_index": d_index,
            "E_survivors": survivors,
            "least_E_survivor": least_e,
            "incremental_pair_atoms": incremental_pair_atoms,
            "incremental_pair_killed_words": incremental_pair_words,
            "pair_atom_bits": pair_bits,
            "final_atom_bits": final_atoms,
            "final_killed_bits": killed,
        })
        if ordinal % 250 == 0 or ordinal == len(a_indices):
            print(
                f"source leaf {source_leaf['source_policy_leaf_position']}: "
                f"{ordinal}/{len(a_indices)} exact A histories",
                flush=True,
            )

    cegar = exact_e_response_cegar_partition(
        a_indices,
        final_atom_masks,
        final_killed_masks,
        fixed_atoms,
        e_model,
        e_domain,
    )
    assert cegar["root_common_E_response_mask"] == bits_record(
        common_e, e_word_count
    )
    assert cegar["unresolved_A_actions"] == fatal_histories
    direct_checks = direct_response_checks(
        source_leaf,
        cegar,
        prefix,
        a_domain,
        b_domain,
        c_domain,
        d_domain,
        e_domain,
        a_start,
        b_start,
        c_start,
        d_start,
        e_start,
    )

    result = {
        "source_transition_leaf_position": source_leaf[
            "source_transition_leaf_position"
        ],
        "source_policy_leaf_position": source_leaf[
            "source_policy_leaf_position"
        ],
        "source_class": source_leaf["source_class"],
        "source_C_response_tree_sha256": source_leaf[
            "source_C_response_tree_sha256"
        ],
        "source_C_response_leaf_node_id": source_leaf[
            "source_C_response_leaf_node_id"
        ],
        "source_predicate_path": source_leaf["source_predicate_path"],
        "source_D_response_tree_sha256": source_leaf[
            "source_D_response_tree_sha256"
        ],
        "source_D_response_leaf_node_id": source_leaf[
            "source_D_response_leaf_node_id"
        ],
        "source_D_predicate_path": source_leaf[
            "source_D_predicate_path"
        ],
        "A_actions": len(a_indices),
        "A_domain_indices": a_indices,
        "A_domain_indices_sha256": source_leaf[
            "A_domain_indices_sha256"
        ],
        "fixed_B_domain_index": b_index,
        "fixed_B_word": source_leaf["fixed_B_word"],
        "fixed_C_domain_index": c_index,
        "fixed_C_word": source_leaf["fixed_C_word"],
        "fixed_D_domain_index": d_index,
        "fixed_D_word": source_leaf["fixed_D_word"],
        "actual_history_identity": (
            "each history is the exact tuple "
            "(A_domain_index, fixed B, fixed C, fixed D)"
        ),
        "history_quadruples_sha256": stable_hash([
            [a_index, b_index, c_index, d_index] for a_index in a_indices
        ]),
        "history_stream_binding": stream_binding,
        "history_stream_sha256": digest.hexdigest(),
        "fatal_histories_for_selected_B_C_D": fatal_histories,
        "forall_exact_A_exists_E": fatal_histories == 0,
        "E_survivor_count_histogram": dict(sorted(survivor_histogram.items())),
        "minimum_E_survivors": minimum,
        "maximum_E_survivors": maximum,
        "common_E": bits_record(common_e, e_word_count),
        "exists_fixed_E_forall_A_in_source_leaf": bool(common_e),
        "component_unions_over_exact_A": {
            name: effect_record(
                bits, e_atom_count, e_word_masks, e_word_count
            )
            for name, bits in component_unions.items()
        },
        "overlapping_channel_unions_over_exact_A": {
            name: effect_record(
                bits, e_atom_count, e_word_masks, e_word_count
            )
            for name, bits in channel_unions.items()
        },
        "E_response_CEGAR": cegar,
        "E_response_CEGAR_unresolved_A_equals_fatal_histories": True,
        "direct_sequential_checks_of_emitted_E_responses": direct_checks,
    }
    del final_atom_masks, final_killed_masks
    return result


def combine_fifth_ply_transition(leaf_results):
    source_actions = []
    terminal_actions = []
    response_actions = []
    response_records = []
    unresolved_records = []
    source_leaf_summaries = []
    for source in leaf_results:
        cegar = source["E_response_CEGAR"]
        source_actions.extend(source["A_domain_indices"])
        source_leaf_summaries.append({
            "source_transition_leaf_position": source[
                "source_transition_leaf_position"
            ],
            "source_policy_leaf_position": source[
                "source_policy_leaf_position"
            ],
            "source_class": source["source_class"],
            "A_actions": source["A_actions"],
            "fixed_B_domain_index": source["fixed_B_domain_index"],
            "fixed_C_domain_index": source["fixed_C_domain_index"],
            "fixed_D_domain_index": source["fixed_D_domain_index"],
            "E_response_tree_sha256": cegar["tree_sha256"],
            "E_response_leaves": cegar["response_compatible_leaves"],
            "unresolved_A_actions": cegar["unresolved_A_actions"],
        })
        for leaf in cegar["response_compatible_leaf_records"]:
            terminal_actions.extend(leaf["A_domain_indices"])
            response_actions.extend(leaf["A_domain_indices"])
            response_records.append({
                "source_transition_leaf_position": source[
                    "source_transition_leaf_position"
                ],
                "source_policy_leaf_position": source[
                    "source_policy_leaf_position"
                ],
                "source_class": source["source_class"],
                "source_C_response_tree_sha256": source[
                    "source_C_response_tree_sha256"
                ],
                "source_C_response_leaf_node_id": source[
                    "source_C_response_leaf_node_id"
                ],
                "source_predicate_path": source["source_predicate_path"],
                "source_D_response_tree_sha256": source[
                    "source_D_response_tree_sha256"
                ],
                "source_D_response_leaf_node_id": source[
                    "source_D_response_leaf_node_id"
                ],
                "source_D_predicate_path": source[
                    "source_D_predicate_path"
                ],
                "E_response_tree_sha256": cegar["tree_sha256"],
                "E_response_leaf_node_id": leaf["node_id"],
                "E_predicate_path": leaf["predicate_path"],
                "A_actions": leaf["actions"],
                "A_domain_indices": leaf["A_domain_indices"],
                "A_domain_indices_sha256": leaf[
                    "A_domain_indices_sha256"
                ],
                "fixed_B_domain_index": source["fixed_B_domain_index"],
                "fixed_B_word": source["fixed_B_word"],
                "fixed_C_domain_index": source["fixed_C_domain_index"],
                "fixed_C_word": source["fixed_C_word"],
                "fixed_D_domain_index": source["fixed_D_domain_index"],
                "fixed_D_word": source["fixed_D_word"],
                "fixed_E_domain_index": leaf[
                    "least_common_E_domain_index"
                ],
                "fixed_E_word": leaf["least_common_E_word"],
                "common_E_response_mask": leaf[
                    "common_E_response_mask"
                ],
                "history_quadruples_sha256": stable_hash([
                    [
                        a_index,
                        source["fixed_B_domain_index"],
                        source["fixed_C_domain_index"],
                        source["fixed_D_domain_index"],
                    ]
                    for a_index in leaf["A_domain_indices"]
                ]),
            })
        for terminal in cegar["unresolved_terminal_records"]:
            terminal_actions.extend(terminal["A_domain_indices"])
            unresolved_records.append({
                "source_transition_leaf_position": source[
                    "source_transition_leaf_position"
                ],
                "source_policy_leaf_position": source[
                    "source_policy_leaf_position"
                ],
                "source_class": source["source_class"],
                "fixed_B_domain_index": source["fixed_B_domain_index"],
                "fixed_C_domain_index": source["fixed_C_domain_index"],
                "fixed_D_domain_index": source["fixed_D_domain_index"],
                "E_response_tree_sha256": cegar["tree_sha256"],
                "terminal_node_id": terminal["node_id"],
                "A_actions": terminal["actions"],
                "A_domain_indices": terminal["A_domain_indices"],
                "A_domain_indices_sha256": terminal[
                    "A_domain_indices_sha256"
                ],
                "E_predicate_path": terminal["predicate_path"],
                "status": (
                    "fatal for this selected B,C,D continuation; unresolved, "
                    "not called game-losing"
                ),
            })

    assert len(source_actions) == len(set(source_actions)) == 1997
    assert stable_hash(sorted(source_actions)) == EXPECTED_POLICY_A_SHA256
    assert len(terminal_actions) == len(set(terminal_actions))
    assert sorted(terminal_actions) == sorted(source_actions)
    assert len(response_actions) == len(set(response_actions))
    full_coverage = sorted(response_actions) == sorted(source_actions)
    result = {
        "semantics": (
            "the canonical ten-leaf fourth-ply transition is refined only "
            "as needed so each emitted exact A class has fixed B,C,D,E"
        ),
        "scope": (
            "finite fifth-stitch transition on one frozen prefix; not an "
            "inductive invariant, future-state congruence, or greatest fixed point"
        ),
        "source_transition_sha256": EXPECTED_FOURTH_PLY_TRANSITION_SHA256,
        "source_policy_sha256": EXPECTED_SOURCE_POLICY_SHA256,
        "source_transition_leaves": len(leaf_results),
        "source_A_actions": len(source_actions),
        "source_A_domain_indices_sha256": stable_hash(sorted(source_actions)),
        "source_leaf_transition_summaries": source_leaf_summaries,
        "total_E_response_leaves": len(response_records),
        "unresolved_terminals": len(unresolved_records),
        "unresolved_A_actions": len(source_actions) - len(response_actions),
        "terminal_partition_covers_every_source_A_exactly_once": True,
        "E_policy_covers_every_source_A_exactly_once": full_coverage,
        "exact_finite_fifth_ply_transition_available": full_coverage,
        "actual_history_quadruples_remain_distinct": True,
        "response_leaf_lookup_records": response_records,
        "unresolved_terminal_records": unresolved_records,
        "failure_scope": (
            "an unresolved A obstructs only the selected upstream B,C,D "
            "policy; alternative legal B, C, or D choices were not swept"
        ),
        "future_state_congruence_or_GFP_proved": False,
    }
    result["fifth_ply_transition_sha256"] = stable_hash(result)
    return result


def complete_backstop(candidate, context):
    a_index = candidate["A_domain_index"]
    b_index = candidate["B_domain_index"]
    c_index = candidate["C_domain_index"]
    d_index = candidate["D_domain_index"]
    a_points = word_interiors(context["a_start"], context["a_domain"][a_index])
    b_points = word_interiors(context["b_start"], context["b_domain"][b_index])
    c_points = word_interiors(context["c_start"], context["c_domain"][c_index])
    d_points = word_interiors(context["d_start"], context["d_domain"][d_index])
    prefix_set = context["prefix_set"]
    assert not (set(a_points) & prefix_set)
    assert not (set(b_points) & (prefix_set | set(a_points)))
    assert not (
        set(c_points) & (prefix_set | set(a_points) | set(b_points))
    )
    assert not (
        set(d_points)
        & (prefix_set | set(a_points) | set(b_points) | set(c_points))
    )
    history = context["prefix"] + a_points + b_points + c_points + d_points
    history_births = context["prefix_births"] + [LEVEL] * (
        len(a_points) + len(b_points) + len(c_points) + len(d_points)
    )
    info = compute_poison(
        context["e_model"],
        context["e_start"],
        midpoint(context["e_start"], context["e_end"]),
        history,
        history_births,
        LEVEL,
    )
    full_atom_bits = poisoned_atom_bits(info)
    del info, history, history_births
    assert full_atom_bits == candidate["final_atom_bits"]
    full_killed_bits = atoms_to_word_bits(
        full_atom_bits, context["e_word_masks"]
    )
    assert full_killed_bits == candidate["final_killed_bits"]

    store = Store(context["prefix"])
    assert word_legal_fast(
        context["a_start"], context["a_domain"][a_index], store, {}, MENU
    )
    store.add_many(a_points)
    assert word_legal_fast(
        context["b_start"], context["b_domain"][b_index], store, {}, MENU
    )
    store.add_many(b_points)
    assert word_legal_fast(
        context["c_start"], context["c_domain"][c_index], store, {}, MENU
    )
    store.add_many(c_points)
    assert word_legal_fast(
        context["d_start"], context["d_domain"][d_index], store, {}, MENU
    )
    store.add_many(d_points)
    e_index = candidate["least_E_survivor"]
    if e_index is not None:
        assert word_legal_fast(
            context["e_start"], context["e_domain"][e_index], store, {}, MENU
        )

    return {
        "history": compact_candidate(
            candidate,
            len(context["e_model"]["atom_desc"]),
            len(context["e_domain"]),
        ),
        "full_compute_poison_atom_mask_matches_transfer_union": True,
        "full_killed_E_mask_matches_transfer_union": True,
        "sequential_A_then_B_then_C_then_D_legality_checked": True,
        "least_surviving_E_checked_when_present": e_index is not None,
        "backstop_scope": (
            "implementation hardening for this history; not exhaustive "
            "channel attribution or an upstream policy search"
        ),
    }


def preflight_paths(certificate_path, output_path):
    certificate_path = certificate_path.expanduser()
    output_path = output_path.expanduser()
    if not certificate_path.is_file():
        raise SystemExit(
            f"fourth-ply certificate is not a file: {certificate_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.parent.is_dir() or not os.access(
        output_path.parent, os.W_OK
    ):
        raise SystemExit(f"output parent is not writable: {output_path.parent}")
    if output_path.exists() and not output_path.is_file():
        raise SystemExit(f"output path is not a regular file: {output_path}")
    if output_path.resolve() == certificate_path.resolve():
        raise SystemExit("output path must differ from the source certificate")
    return certificate_path, output_path


def main(certificate_path, output_path):
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    current_nice = os.getpriority(os.PRIO_PROCESS, 0)
    if current_nice < 10:
        raise SystemExit(
            f"refusing normal-priority run (nice={current_nice}); prepend nice -n 15"
        )
    thread_environment = {
        name: os.environ.get(name) for name in THREAD_ENVIRONMENT
    }
    if any(value != "1" for value in thread_environment.values()):
        raise SystemExit(
            "all thread environment variables must equal '1': "
            + repr(thread_environment)
        )
    certificate_path, output_path = preflight_paths(
        certificate_path, output_path
    )
    started = time.time()

    certificate, source_leaves, raw_sha256, source_transition_sha256 = (
        validate_and_extract_policy(certificate_path)
    )
    del certificate
    input_sha256 = {
        name: file_sha256(ROOT / name)
        for name in third.EXPECTED_INPUT_SHA256
    }
    assert input_sha256 == third.EXPECTED_INPUT_SHA256
    third_helper_sha256 = file_sha256(
        ROOT / "design/l8_third_ply_closure.py"
    )
    assert third_helper_sha256 == EXPECTED_THIRD_PLY_HELPER_SHA256
    input_sha256["design/l8_third_ply_closure.py"] = third_helper_sha256
    checker_sha256 = file_sha256(Path(__file__).resolve())

    print("loading frozen L8 construction and D2--4 domains", flush=True)
    domains, d24 = load_selected_domains()
    viz = load_viz()
    births_by_level = exact_birth_levels(viz)
    state, tile_gaps, _owners, schedule, guards = build_context(
        LEVEL, viz, births_by_level, d24
    )
    schedule_by_gap = {
        entry["gap"]: (rank, entry) for rank, entry in enumerate(schedule)
    }
    assert E_RANK == D_RANK + 1
    assert tuple(
        schedule_by_gap[gap][0]
        for gap in (A_GAP, B_GAP, C_GAP, D_GAP, E_GAP)
    ) == (A_RANK, B_RANK, C_RANK, D_RANK, E_RANK)
    assert tuple(
        schedule[rank]["gap"]
        for rank in (A_RANK, B_RANK, C_RANK, D_RANK, E_RANK)
    ) == (A_GAP, B_GAP, C_GAP, D_GAP, E_GAP)
    assert schedule[D_RANK + 1]["gap"] == E_GAP
    assert schedule[E_RANK] == {
        "gap": E_GAP,
        "sweep_tile": 19960,
        "phase": "finish-current-tile",
    }
    assert tuple(
        state["parent_word"][gap]
        for gap in (A_GAP, B_GAP, C_GAP, D_GAP, E_GAP)
    ) == (A_STEP, B_STEP, C_STEP, D_STEP, E_STEP)
    assert tuple(tile_gaps[19960]) == (67012, 67013, 67014, 67015)
    assert tuple(state["parent_word"][gap] for gap in tile_gaps[19960]) == (
        17, 19, 21, 72
    )
    assert guards[19960] == 67014
    assert schedule_by_gap[67014][0] < A_RANK

    a_domain = list(domains[A_STEP])
    b_domain = list(domains[B_STEP])
    c_domain = list(domains[C_STEP])
    d_domain = list(domains[D_STEP])
    e_domain = list(domains[E_STEP])
    assert tuple(map(len, (a_domain, b_domain, c_domain, d_domain, e_domain))) == (
        5257, 9046, 49402, 6736, 35751
    )
    assert Counter(map(len, e_domain)) == {3: 151, 4: 35600}
    assert tuple(state["words"][E_GAP]) == RECORDED_E
    assert tuple(e_domain[87]) == RECORDED_E
    assert tuple(d_domain[FIXED_D_DOMAIN_INDEX]) == FIXED_D_WORD

    for source_leaf in source_leaves:
        assert all(0 <= index < len(a_domain) for index in source_leaf[
            "A_domain_indices"
        ])
        assert list(b_domain[source_leaf["fixed_B_domain_index"]]) == (
            source_leaf["fixed_B_word"]
        )
        assert list(c_domain[source_leaf["fixed_C_domain_index"]]) == (
            source_leaf["fixed_C_word"]
        )
        assert source_leaf["fixed_D_domain_index"] == FIXED_D_DOMAIN_INDEX
        assert list(d_domain[source_leaf["fixed_D_domain_index"]]) == (
            source_leaf["fixed_D_word"]
        )

    prefix, prefix_births = build_prefix(
        state, schedule, births_by_level[LEVEL - 1]
    )
    assert len(prefix) == EXPECTED_PREFIX_POINTS
    assert point_set_sha256(prefix) == EXPECTED_PREFIX_SHA256
    assert point_birth_sha256(prefix, prefix_births) == EXPECTED_PREFIX_BIRTH_SHA256
    assert dict(sorted(Counter(prefix_births).items())) == EXPECTED_BIRTH_HISTOGRAM

    a_start = state["anchors"][A_GAP]
    b_start = state["anchors"][B_GAP]
    c_start = state["anchors"][C_GAP]
    d_start = state["anchors"][D_GAP]
    e_start = state["anchors"][E_GAP]
    e_end = state["anchors"][E_GAP + 1]
    assert (a_start, b_start, c_start) == (
        EXPECTED_A_START,
        EXPECTED_B_START,
        EXPECTED_C_START,
    )
    assert d_start == EXPECTED_D_START
    assert (e_start, e_end) == (EXPECTED_E_START, EXPECTED_E_END)

    del domains, d24, viz, births_by_level, tile_gaps, schedule
    del schedule_by_gap, guards, _owners, state
    gc.collect()

    a_model = build_domain_model(a_domain)
    e_model = build_domain_model(e_domain)
    assert (
        len(a_model["site_id"]),
        len(a_model["line_id"]),
        len(a_model["line_by_direction"]),
        len(a_model["atom_desc"]),
    ) == third.EXPECTED_A_MODEL
    assert stable_hash(a_model["atom_desc"]) == third.EXPECTED_A_ATOM_DESC_SHA256
    assert stable_hash(a_model["word_atoms"]) == third.EXPECTED_A_WORD_ATOMS_SHA256
    assert (
        len(e_model["site_id"]),
        len(e_model["line_id"]),
        len(e_model["line_by_direction"]),
        len(e_model["atom_desc"]),
    ) == EXPECTED_E_MODEL
    assert stable_hash(e_model["atom_desc"]) == EXPECTED_E_ATOM_DESC_SHA256
    assert stable_hash(e_model["word_atoms"]) == EXPECTED_E_WORD_ATOMS_SHA256
    assert Counter(map(len, e_model["word_atoms"])) == {3: 151, 6: 35600}

    e_word_masks = atom_word_masks(e_model)
    prefix_set = set(prefix)
    destination_sites = [
        (add(e_start, offset), atom)
        for offset, atom in e_model["site_id"].items()
    ]
    destination_directions = list(e_model["line_by_direction"].items())

    print("computing exact full-prefix BaseE poison", flush=True)
    base_e_info = compute_poison(
        e_model,
        e_start,
        midpoint(e_start, e_end),
        prefix,
        prefix_births,
        LEVEL,
    )
    base_e_atoms = poisoned_atom_bits(base_e_info)
    base_e_killed = atoms_to_word_bits(base_e_atoms, e_word_masks)
    del base_e_info
    gc.collect()

    print("computing exact all-prefix A-atom to E unary transfer", flush=True)
    a_unary_transfer = source_to_destination_unary_transfer(
        prefix,
        prefix_set,
        a_model,
        a_start,
        e_model,
        e_start,
        "A",
    )

    context = {
        "a_domain": a_domain,
        "b_domain": b_domain,
        "c_domain": c_domain,
        "d_domain": d_domain,
        "e_domain": e_domain,
        "a_model": a_model,
        "e_model": e_model,
        "e_word_masks": e_word_masks,
        "prefix": prefix,
        "prefix_births": prefix_births,
        "prefix_set": prefix_set,
        "a_start": a_start,
        "b_start": b_start,
        "c_start": c_start,
        "d_start": d_start,
        "e_start": e_start,
        "e_end": e_end,
        "destination_sites": destination_sites,
        "destination_directions": destination_directions,
        "base_e_atoms": base_e_atoms,
        "base_e_killed": base_e_killed,
        "a_unary_transfer": a_unary_transfer,
        "ua_cache": {},
        "fixed_word_cache": {},
        "cross_transfer_cache": {},
        "xbc_cache": {},
        "xbd_cache": {},
        "xcd_cache": {},
        "fixed_point_cache": {},
        "fixed_pair_cache": {},
    }

    ordinary_candidate = None
    maximum_pair_candidate = None
    maximum_pair_distinct_from_ordinary = None

    def observe(candidate):
        nonlocal ordinary_candidate
        nonlocal maximum_pair_candidate
        nonlocal maximum_pair_distinct_from_ordinary
        if ordinary_candidate is None:
            ordinary_candidate = candidate
        score = (
            candidate["incremental_pair_killed_words"].bit_count(),
            candidate["incremental_pair_atoms"].bit_count(),
            candidate["pair_atom_bits"].bit_count(),
            candidate["source_transition_leaf_position"]
            != ordinary_candidate["source_transition_leaf_position"],
            (
                candidate["B_domain_index"],
                candidate["C_domain_index"],
                candidate["D_domain_index"],
            ) != (
                ordinary_candidate["B_domain_index"],
                ordinary_candidate["C_domain_index"],
                ordinary_candidate["D_domain_index"],
            ),
            -candidate["source_transition_leaf_position"],
            -candidate["A_domain_index"],
        )
        if maximum_pair_candidate is None or score > maximum_pair_candidate[0]:
            maximum_pair_candidate = (score, candidate)
        if candidate_identity(candidate) != candidate_identity(ordinary_candidate):
            if (
                maximum_pair_distinct_from_ordinary is None
                or score > maximum_pair_distinct_from_ordinary[0]
            ):
                maximum_pair_distinct_from_ordinary = (score, candidate)

    leaf_results = []
    for position, source_leaf in enumerate(source_leaves, 1):
        print(
            f"sweeping canonical source leaf {position}/{len(source_leaves)}",
            flush=True,
        )
        leaf_results.append(sweep_policy_leaf(source_leaf, context, observe))
        gc.collect()

    transition = combine_fifth_ply_transition(leaf_results)
    assert ordinary_candidate is not None
    assert maximum_pair_candidate is not None
    assert maximum_pair_distinct_from_ordinary is not None
    second_candidate = maximum_pair_distinct_from_ordinary[1]
    assert candidate_identity(second_candidate) != candidate_identity(
        ordinary_candidate
    )

    print("running two independent full-E history backstops", flush=True)
    backstops = []
    for role, candidate in (
        ("deterministic-first-canonical-policy-history", ordinary_candidate),
        (
            "maximum-incremental-pair-poison-history-distinct-from-first",
            second_candidate,
        ),
    ):
        record = complete_backstop(candidate, context)
        record["role"] = role
        backstops.append(record)

    e_atom_count = len(e_model["atom_desc"])
    e_word_count = len(e_domain)
    result = {
        "status": (
            "exact finite fifth-stitch transition test for the canonical "
            "ten-leaf fourth-ply transition; not a greatest fixed point"
        ),
        "checker_sha256": checker_sha256,
        "input_sha256": input_sha256,
        "fourth_ply_certificate": {
            "path": str(certificate_path),
            "raw_bytes": EXPECTED_FOURTH_PLY_CERTIFICATE_BYTES,
            "raw_file_sha256": raw_sha256,
            "raw_file_sha256_verified": True,
            "producer_checker_sha256": EXPECTED_FOURTH_PLY_CHECKER_SHA256,
            "source_policy_sha256": EXPECTED_SOURCE_POLICY_SHA256,
            "fourth_ply_transition_sha256": source_transition_sha256,
            "transition_sha256_verified_without_self_field": True,
            "transition_leaves": len(source_leaves),
            "exact_A_actions": 1997,
        },
        "resource_policy": {
            "processes": 1,
            "python_worker_threads": 1,
            "nice": current_nice,
            "thread_environment": thread_environment,
            "thread_environment_required_exactly_one": True,
            "source_leaves_processed_sequentially": True,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "scope_warning": {
            "one_frozen_prefix": True,
            "finite_fifth_stitch_only": True,
            "selected_upstream_B_C_D_policy_only": True,
            "alternative_B_C_or_D_responses_exhausted": False,
            "actual_A_histories_retained": True,
            "source_or_output_classes_are_future_state_congruences": False,
            "greatest_fixed_point_or_induction_proved": False,
        },
        "geometry": {
            "prefix_points": len(prefix),
            "prefix_point_set_sha256": EXPECTED_PREFIX_SHA256,
            "prefix_coordinate_birth_sha256": EXPECTED_PREFIX_BIRTH_SHA256,
            "ranks_are_consecutive_A_then_B_then_C_then_D_then_E": True,
            "A": {"gap": A_GAP, "step": A_STEP, "rank": A_RANK},
            "B": {"gap": B_GAP, "step": B_STEP, "rank": B_RANK},
            "C": {"gap": C_GAP, "step": C_STEP, "rank": C_RANK},
            "D": {
                "gap": D_GAP,
                "step": D_STEP,
                "rank": D_RANK,
                "start": list(d_start),
                "domain_words": len(d_domain),
                "domain_sha256": EXPECTED_D_DOMAIN_SHA256,
                "fixed_domain_index": FIXED_D_DOMAIN_INDEX,
                "fixed_word": list(FIXED_D_WORD),
            },
            "E": {
                "gap": E_GAP,
                "step": E_STEP,
                "rank": E_RANK,
                "start": list(e_start),
                "end": list(e_end),
                "domain_words": e_word_count,
                "domain_sha256": EXPECTED_E_DOMAIN_SHA256,
                "sites": len(e_model["site_id"]),
                "lines": len(e_model["line_id"]),
                "directions": len(e_model["line_by_direction"]),
                "atoms": e_atom_count,
            },
        },
        "exact_poison_identity": {
            "formula": (
                "Q_E(P,A,B,C,D) = BaseE(P) | UA(A) | UB(B) | UC(C) | "
                "UD(D) | XAB(A,B) | XAC(A,C) | XAD(A,D) | XBC(B,C) | "
                "XBD(B,D) | XCD(C,D)"
            ),
            "BaseE": "collision-P-E, P-P-E, and P-E-E",
            "UX": "collision-X-E, P-X-E, X-X-E, and X-E-E",
            "XY": "X-Y-E target-site atoms",
            "E_E_E": "excluded by the certified connector domain E_17",
            "components_overlap": True,
            "identity_is_union_not_disjoint_attribution": True,
            "distance_cutoff": None,
            "all_prefix_points_scanned": True,
        },
        "BaseE": {
            "atoms": bits_record(base_e_atoms, e_atom_count),
            "killed_E_words": bits_record(base_e_killed, e_word_count),
            "surviving_E_words": e_word_count - base_e_killed.bit_count(),
        },
        "source_leaf_results": leaf_results,
        "fifth_ply_transition": transition,
        "global_maximum_incremental_pair_poison_history": (
            compact_candidate(
                maximum_pair_candidate[1], e_atom_count, e_word_count
            )
        ),
        "global_incremental_pair_poison_nonzero": {
            "atoms_beyond_BaseE_and_unaries": bool(
                maximum_pair_candidate[1]["incremental_pair_atoms"]
            ),
            "newly_killed_E_words": bool(
                maximum_pair_candidate[1]["incremental_pair_killed_words"]
            ),
        },
        "full_E_backstops": backstops,
        "conclusions": {
            "every_selected_exact_A_B_C_D_history_has_some_E": (
                transition["unresolved_A_actions"] == 0
            ),
            "exact_finite_fifth_ply_transition_for_selected_policy": (
                transition[
                    "exact_finite_fifth_ply_transition_available"
                ]
            ),
            "unconditional_infinite_walk_theorem": False,
        },
        "memory_discipline": {
            "fragile_D5_pickle_not_materialized": True,
            "only_A_B_C_D_E_D2_to_4_domains_retained": True,
            "source_leaves_processed_sequentially": True,
            "per_A_final_masks_released_after_source_leaf_CEGAR": True,
            "fixed_word_and_pair_transfers_cached_across_leaves": True,
            "full_E_compute_poison_scans": 2,
            "JSON_contains_mask_counts_and_hashes_not_full_bitsets": True,
        },
    }
    assert len(backstops) == 2
    assert candidate_identity(backstops[0]["history"]) != candidate_identity(
        backstops[1]["history"]
    )
    atomic_write_json(output_path, result)
    print(json.dumps(result["conclusions"], indent=2, sort_keys=True), flush=True)
    print(f"wrote {output_path}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fourth-ply-certificate",
        type=Path,
        default=Path("/tmp/l8-fourth-ply-transition-canonical.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l8-fifth-ply-transition.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.fourth_ply_certificate, arguments.output)
