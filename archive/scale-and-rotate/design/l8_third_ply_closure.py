#!/usr/bin/env python3
"""Exact robust A+B-to-C lookup-table checker for the frozen L8 third stitch.

This is an independent consumer of ``l8_immediate_action_cegar.py``'s
``third_ply_interface``.  It tests the stronger robust per-leaf lookup-table
property

    for every leaf L, exists fixed B_L, exists fixed C_L,
    for every exact A in L,

for all four response-compatible partition leaves and for the overlapping
1977-action/B=8765 probe.  The exact C poison after an ordered history is
decomposed as

    Q_C(P, A, B) = BaseC(P) | TA(A) | TB(B) | XAB(A, B).

Here BaseC contains P-P-C and P-C-C poison, TA contains collision/P-A-C,
A-A-C, and A-C-C poison, TB contains the analogous B channels, and XAB
contains A-B-C site poison.  Thus no distance cutoff is used: every point of
the 250697-point prefix participates in BaseC and in each prefix/new-point
direction scan.  Candidate-internal C-C-C defects are excluded by the
pre-certified D_48 connector domain.

The transfer is checked against two complete ``compute_poison`` scans on
distinct A,B histories.  One is the first deterministic history.  The other
maximizes genuinely incremental XAB damage while preferring a distinct B.
Every reported winning fixed B,C pair is also checked with the independent
sequential ``word_legal_fast`` predicate on the first, last, and
minimum-survivor A actions for that B.  These direct checks harden the transfer
implementation; the exhaustive lookup-table claim still comes from the exact
mask sweep.

For each fixed B sweep, the checker also builds a deterministic exact CEGAR
tree over the realized A histories.  A response-compatible leaf has a common
C word; otherwise the tree greedily splits on balanced membership of one
genuinely A-dependent C-poison atom outside fixed BaseC|TB.  The best emitted
B for each original partition leaf is selected by a fixed complexity score,
forming a finite third-ply policy partition when all refined leaves resolve.
This refinement is a finite-prefix policy certificate only, not a future-state
quotient.

This remains a depth-three finite-prefix certificate, not an inductive
invariant or greatest fixed point.  In particular, each exact A word remains
observable while its class is swept; classes are never treated as future
state congruence classes.

Run from the repository root on one low-priority core, after producing the
pinned A-to-B certificate:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l8_third_ply_closure.py \
        --ab-certificate /tmp/l8-immediate-action-cegar-hardened-canonical.json \
        --output /tmp/l8-third-ply-closure.json

The checker is deliberately single-process and refuses to run below nice 10.
It does not modify construction pickles, walk artifacts, or the PM2 website.
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
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from fast_legal import LIMIT, SHIFT, Store, word_legal_fast  # noqa: E402
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


LEVEL = 8
A_GAP, B_GAP, C_GAP = 67009, 67011, 67008
A_STEP, B_STEP, C_STEP = 14, 34, 48
A_RANK, B_RANK, C_RANK = 67010, 67011, 67012
TILE = 19959

RECORDED_A = (0, 3, 1)
RECORDED_B = (1, 25, 50)
RECORDED_C = (18, 54, 29)

EXPECTED_THIRD_PLY_INTERFACE_SHA256 = (
    "c31864a8fa4bbd1214cd21a8bda1075d80ef96c12077711855746da9ec1edcdd"
)
EXPECTED_AB_CERTIFICATE_SHA256 = (
    "32b1518bf7ad1a80448720198932799e5e3a7aa689b3e7833c0460ce24e3b828"
)
EXPECTED_CORE_SWEEP_REGRESSION_SHA256 = (
    "51447a8e566113061c981ee00578889ec8cf07933006707455964a48f6d96fbf"
)
EXPECTED_C_RESPONSE_CEGAR_HEADLINES = {
    "combined_policy": (
        "81d85f1a5e21959d5e062c6a26cc43dc77fc54fd5acb810444feece41736d78d",
        10,
        0,
        1997,
    ),
    "overlapping_probe": (
        "342d9d10c1f28ee636913c59aa97f28c825e358063217ea07458005d7bea2829",
        8,
        0,
        1977,
    ),
    "selected_choice_stream_sha256": (
        "fa903dbc310012756c69674b0003e24e4c48599798a3c6f1d7647aa312af3e12"
    ),
    "all_tree_stream": (
        "e571715d13fe110543557043ef9613335aaa54e60abe1d3e615cd02acaa8c48c",
        49,
        243,
        15,
        4,
    ),
}
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

EXPECTED_PREFIX_POINTS = 250697
EXPECTED_PREFIX_SHA256 = (
    "7ba05e8ced59f2fb341e2ab1487d6a6aab34123fa7b982f53ea84879d2382aae"
)
EXPECTED_PREFIX_BIRTH_SHA256 = (
    "cdb2eab8886a3faf0f0a71c9ad04d8ecefdbc049f177b35d18742139a408811c"
)
EXPECTED_BIRTH_HISTOGRAM = {
    0: 21,
    1: 42,
    2: 152,
    3: 501,
    4: 1742,
    5: 5756,
    6: 19483,
    7: 65035,
    8: 157965,
}

EXPECTED_A_MODEL = (140, 1356, 75, 1496)
EXPECTED_C_MODEL = (278, 5379, 143, 5657)
EXPECTED_A_ATOM_DESC_SHA256 = (
    "d4a73fded3821c1f02bfd5ae477d0aed4cd4b0bde6d3b7461d213dab931ebb99"
)
EXPECTED_A_WORD_ATOMS_SHA256 = (
    "6ee224db5c3ed34df43a480a3c7741ee65e1ebed0f17c149a811520baee43cc2"
)
EXPECTED_C_ATOM_DESC_SHA256 = (
    "4ad22113d9491a3601876b3dbdc149d6568daab8f9666186095299853564f31f"
)
EXPECTED_C_WORD_ATOMS_SHA256 = (
    "554d29279581352c9d3000512731adb05cd3e10a06bf0f5f85d00a5f89c6afa4"
)

THREAD_ENVIRONMENT = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

CORE_REGRESSION_CLASS_NAMES = (
    "partition-leaf-0-node-1",
    "partition-leaf-1-node-4",
    "partition-leaf-2-node-5",
    "partition-leaf-3-node-6",
    "overlapping-maximal-single-response-B8765",
)
CORE_REGRESSION_CONCLUSION_KEYS = (
    "all_four_partition_leaves_have_fixed_B_and_C",
    "overlapping_1977_action_B8765_probe_has_fixed_C",
    "finite_depth_three_uniform_lookup_table_on_frozen_partition",
    "unconditional_infinite_walk_theorem",
)
CORE_REGRESSION_CANDIDATE_KEYS = (
    "class",
    "A_domain_index",
    "B_domain_index",
    "C_survivors",
    "least_C_survivor",
    "genuinely_incremental_XAB_atoms",
    "genuinely_incremental_XAB_killed_words",
    "final_C_atoms",
    "final_killed_C_words",
)


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def pick_fields(record, keys):
    return {key: record[key] for key in keys}


def core_candidate_projection(record):
    return pick_fields(record, CORE_REGRESSION_CANDIDATE_KEYS)


def core_sweep_regression_projection(result):
    """Project only the already-observed core sweep, excluding new CEGAR data."""
    matches = {
        name: [
            record
            for record in result["quantified_class_results"]
            if record["name"] == name
        ]
        for name in CORE_REGRESSION_CLASS_NAMES
    }
    assert all(len(records) == 1 for records in matches.values())
    classes = [matches[name][0] for name in CORE_REGRESSION_CLASS_NAMES]

    projected_classes = []
    for record in classes:
        projected_classes.append({
            "kind": record["kind"],
            "name": record["name"],
            "A_actions": record["A_actions"],
            "A_domain_indices_sha256": record["A_domain_indices_sha256"],
            "common_B_actions_tested": record["common_B_actions_tested"],
            "common_B_domain_indices_sha256": record[
                "common_B_domain_indices_sha256"
            ],
            "exists_fixed_B_and_C_forall_A": record[
                "exists_fixed_B_and_C_forall_A"
            ],
            "least_winning_fixed_pair": record["least_winning_fixed_pair"],
            "reported_winning_fixed_pairs": record[
                "reported_winning_fixed_pairs"
            ],
            "B_sweeps": [
                {
                    "B_domain_index": sweep["B_domain_index"],
                    "histories": sweep["histories"],
                    "history_stream_binding": pick_fields(
                        sweep["history_stream_binding"],
                        (
                            "schema",
                            "class_name",
                            "A_domain_indices_sha256",
                            "B_domain_index",
                        ),
                    ),
                    "history_stream_sha256": sweep["history_stream_sha256"],
                    "fatal_histories": sweep["fatal_histories"],
                    "forall_A_exists_C": sweep["forall_A_exists_C"],
                    "common_C": sweep["common_C"],
                    "exists_C_forall_A_for_this_fixed_B": sweep[
                        "exists_C_forall_A_for_this_fixed_B"
                    ],
                    "least_common_C_domain_index": sweep[
                        "least_common_C_domain_index"
                    ],
                }
                for sweep in record["B_sweeps"]
            ],
        })

    return {
        "schema": "l8-third-ply-core-regression-v1",
        "BaseC": pick_fields(
            result["BaseC"],
            ("atoms", "killed_C_words", "surviving_C_words"),
        ),
        "quantified_class_stream_common_C": projected_classes,
        "conclusions": pick_fields(
            result["conclusions"], CORE_REGRESSION_CONCLUSION_KEYS
        ),
        "global_largest_genuinely_incremental_XAB_history": (
            core_candidate_projection(
                result["global_largest_genuinely_incremental_XAB_history"]
            )
        ),
        "global_incremental_XAB_nonzero": pick_fields(
            result["global_incremental_XAB_nonzero"],
            ("atoms", "newly_killed_C_words"),
        ),
        "full_C_backstops": [
            {
                "role": record["role"],
                "history": core_candidate_projection(record["history"]),
                "full_compute_poison_atom_mask_matches_transfer_union": record[
                    "full_compute_poison_atom_mask_matches_transfer_union"
                ],
                "sequential_A_then_B_legality_checked_with_word_legal_fast": (
                    record[
                        "sequential_A_then_B_legality_checked_with_word_legal_fast"
                    ]
                ),
                "least_surviving_C_checked_with_word_legal_fast": record[
                    "least_surviving_C_checked_with_word_legal_fast"
                ],
            }
            for record in result["full_C_backstops"]
        ],
    }


def bits_sha256(bits, size):
    return hashlib.sha256(bits.to_bytes((size + 7) // 8, "little")).hexdigest()


def bits_record(bits, size):
    return {"bits": bits.bit_count(), "mask_sha256": bits_sha256(bits, size)}


def point_set_sha256(points):
    payload = ";".join(",".join(map(str, point)) for point in sorted(points))
    return hashlib.sha256(payload.encode()).hexdigest()


def point_birth_sha256(points, births):
    digest = hashlib.sha256()
    for point, birth in sorted(zip(points, births)):
        digest.update(
            f"{point[0]},{point[1]},{point[2]}:{birth}\n".encode("ascii")
        )
    return digest.hexdigest()


def load_state():
    with (ROOT / "gate2-l7-construction-L8.pkl").open("rb") as handle:
        return pickle.load(handle)


def load_selected_domains():
    """Load only the three nonfragile D2--4 domains used by this checker."""
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        payload = pickle.load(handle)
    assert tuple(map(tuple, payload["menu"])) == tuple(MENU)
    raw_domains = payload["domains"]
    d24 = {step: len(words) for step, words in raw_domains.items()}
    assert all(d24[step] >= FRAGILE_CUT for step in (A_STEP, B_STEP, C_STEP))
    selected = {
        step: sorted(raw_domains[step], key=len)
        for step in (A_STEP, B_STEP, C_STEP)
    }
    return selected, d24


def direction_key(delta):
    """Packed canonical primitive direction, injective in this construction."""
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


def poisoned_atom_bits(info):
    result = 0
    for atom, record in enumerate(info):
        if math.isfinite(record["threshold"]):
            result |= 1 << atom
    return result


def union_bits(values):
    result = 0
    for value in values:
        result |= value
    return result


def iterate_set_bits(bits):
    while bits:
        flag = bits & -bits
        yield flag.bit_length() - 1
        bits ^= flag


def c_response_cegar_partition(
    a_indices,
    final_atom_masks,
    final_killed_masks,
    fixed_base_tb_atoms,
    c_model,
    c_domain,
):
    """Exact deterministic C-response refinement for one fixed B sweep."""
    action_count = len(a_indices)
    c_word_count = len(c_domain)
    c_atom_count = len(c_model["atom_desc"])
    assert action_count == len(final_atom_masks) == len(final_killed_masks)
    assert action_count > 0
    full_actions = (1 << action_count) - 1
    full_c_words = (1 << c_word_count) - 1
    root_common_c = full_c_words & ~union_bits(final_killed_masks)

    feature_actions = [0] * c_atom_count
    for ordinal, final_atoms in enumerate(final_atom_masks):
        for atom in iterate_set_bits(final_atoms & ~fixed_base_tb_atoms):
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
        common_c = full_c_words & ~killed_union
        domain_indices = [
            a_indices[ordinal] for ordinal in iterate_set_bits(action_bits)
        ]
        if common_c:
            least_c = (common_c & -common_c).bit_length() - 1
            nodes[node_id] = {
                "node_id": node_id,
                "status": "response-compatible-leaf",
                "depth": depth,
                "actions": size,
                "predicate_path": predicate_path,
                "A_domain_indices": domain_indices,
                "A_domain_indices_sha256": stable_hash(domain_indices),
                "action_membership": bits_record(action_bits, action_count),
                "common_C_responses": common_c.bit_count(),
                "common_C_response_mask": bits_record(common_c, c_word_count),
                "least_common_C_domain_index": least_c,
                "least_common_C_word": list(c_domain[least_c]),
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
                final_killed_masks[ordinal] == full_c_words
                for ordinal in unresolved_ordinals
            )
            if size == 1:
                assert final_killed_masks[unresolved_ordinals[0]] == full_c_words
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
                    "every history has the full C domain killed for this "
                    "fixed B; this is fixed-B C-fatal, but is not called "
                    "source-class or game-losing because another B may work"
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
        description = c_model["atom_desc"][atom]
        nodes[node_id] = {
            "node_id": node_id,
            "status": "split",
            "depth": depth,
            "actions": size,
            "predicate_path": predicate_path,
            "A_domain_indices": domain_indices,
            "A_domain_indices_sha256": stable_hash(domain_indices),
            "action_membership": bits_record(action_bits, action_count),
            "feature_C_atom": atom,
            "feature_description": description,
            "feature_is_outside_fixed_BaseC_or_TB": True,
            "feature_membership_is_A_dependent_at_this_node": True,
            "feature_present": inside,
            "feature_absent": size - inside,
            "absent_child_node": absent_id,
            "present_child_node": present_id,
        }
        absent_path = predicate_path + [{
            "C_atom": atom,
            "description": description,
            "A_dependent_poison_present": False,
        }]
        present_path = predicate_path + [{
            "C_atom": atom,
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
    assert all(
        record["common_C_responses"] > 0 for record in response_records
    )
    assert all(
        record["actions"] != 1
        or final_killed_masks[
            ordinal_by_domain_index[record["A_domain_indices"][0]]
        ] == full_c_words
        for record in unresolved_records
    )

    largest = max(
        response_records,
        key=lambda record: (
            record["actions"],
            record["common_C_responses"],
            -record["node_id"],
        ),
        default=None,
    )
    max_depth = max(record["depth"] for record in nodes)
    unresolved_actions = sum(record["actions"] for record in unresolved_records)
    return {
        "semantics": (
            "a response-compatible leaf has one or more C words legal for "
            "every exact A history in that leaf; response-incompatible nodes "
            "are greedily split on balanced membership of one genuinely "
            "A-dependent C poison atom outside fixed BaseC|TB"
        ),
        "scope": (
            "one frozen prefix and one fixed B; exact policy refinement, not "
            "a future-state congruence or greatest fixed point"
        ),
        "minimality": "deterministic greedy balanced split; not claimed minimal",
        "action_membership_index_space": (
            "bit ordinal in this fixed-B sweep's A_domain_indices array"
        ),
        "A_domain_indices": a_indices,
        "A_domain_indices_sha256": stable_hash(a_indices),
        "fixed_BaseC_TB_atoms": bits_record(
            fixed_base_tb_atoms, c_atom_count
        ),
        "root_common_C_response_mask": bits_record(
            root_common_c, c_word_count
        ),
        "genuinely_A_dependent_feature_atoms": len(feature_items),
        "root_node": 0,
        "nodes": len(nodes),
        "tree_sha256": stable_hash(nodes),
        "node_records": nodes,
        "terminal_records_cover_every_A_exactly_once": True,
        "leaf_count": len(response_records),
        "response_compatible_leaves": len(response_records),
        "unresolved_no_common_response_terminals": len(unresolved_records),
        "unresolved_A_actions": unresolved_actions,
        "max_depth": max_depth,
        "leaf_depth_histogram": dict(sorted(Counter(
            record["depth"] for record in response_records
        ).items())),
        "response_compatible_leaf_records": response_records,
        "unresolved_terminal_records": unresolved_records,
        "largest_response_compatible_leaf": largest,
    }


def cegar_selection_score(cegar, b_index):
    largest = cegar["largest_response_compatible_leaf"]
    largest_actions = 0 if largest is None else largest["actions"]
    return (
        cegar["unresolved_A_actions"],
        cegar["leaf_count"],
        cegar["nodes"],
        cegar["max_depth"],
        -largest_actions,
        b_index,
    )


def refined_policy_partition(class_results, label):
    """Combine each class's deterministically selected fixed-B CEGAR leaves."""
    policy_leaf_records = []
    unresolved_records = []
    original_actions = []
    terminal_actions = []
    policy_actions = []
    class_choices = []
    for class_record in class_results:
        choice = class_record["best_fixed_B_for_CEGAR_policy_partition"]
        matching = [
            record for record in class_record["B_sweeps"]
            if record["B_domain_index"] == choice["B_domain_index"]
        ]
        assert len(matching) == 1
        b_record = matching[0]
        cegar = b_record["C_response_CEGAR"]
        assert cegar["tree_sha256"] == choice["tree_sha256"]
        assert tuple(choice["selection_score"]) == cegar_selection_score(
            cegar, choice["B_domain_index"]
        )
        original_actions.extend(cegar["A_domain_indices"])
        class_choices.append({
            "source_class": class_record["name"],
            "source_A_to_B_cegar_node_id": class_record.get(
                "source_A_to_B_cegar_node_id"
            ),
            "fixed_B_domain_index": choice["B_domain_index"],
            "fixed_B_word": b_record["B_word"],
            "selection_score": choice["selection_score"],
            "C_response_tree_sha256": cegar["tree_sha256"],
            "response_compatible_leaves": cegar[
                "response_compatible_leaves"
            ],
            "unresolved_A_actions": cegar["unresolved_A_actions"],
        })
        for leaf in cegar["response_compatible_leaf_records"]:
            terminal_actions.extend(leaf["A_domain_indices"])
            policy_actions.extend(leaf["A_domain_indices"])
            policy_leaf_records.append({
                "source_class": class_record["name"],
                "fixed_B_domain_index": choice["B_domain_index"],
                "C_response_tree_sha256": cegar["tree_sha256"],
                "C_response_leaf_node_id": leaf["node_id"],
                "A_actions": leaf["actions"],
                "A_domain_indices": leaf["A_domain_indices"],
                "A_domain_indices_sha256": leaf[
                    "A_domain_indices_sha256"
                ],
                "predicate_path": leaf["predicate_path"],
                "fixed_C_domain_index": leaf[
                    "least_common_C_domain_index"
                ],
                "fixed_C_word": leaf["least_common_C_word"],
                "common_C_response_mask": leaf[
                    "common_C_response_mask"
                ],
                "lookup_entry_quantifier": (
                    "fixed B and fixed C are legal for every exact A in the "
                    "referenced C-response leaf"
                ),
            })
        for terminal in cegar["unresolved_terminal_records"]:
            terminal_actions.extend(terminal["A_domain_indices"])
            unresolved_records.append({
                "source_class": class_record["name"],
                "fixed_B_domain_index": choice["B_domain_index"],
                "C_response_tree_sha256": cegar["tree_sha256"],
                "terminal_node_id": terminal["node_id"],
                "A_actions": terminal["actions"],
                "A_domain_indices": terminal["A_domain_indices"],
                "A_domain_indices_sha256": terminal[
                    "A_domain_indices_sha256"
                ],
                "predicate_path": terminal["predicate_path"],
                "status": (
                    "fixed-B C-fatal; not proved source-class or game-losing"
                ),
            })

    assert len(original_actions) == len(set(original_actions))
    assert len(terminal_actions) == len(set(terminal_actions))
    assert sorted(terminal_actions) == sorted(original_actions)
    assert len(policy_actions) == len(set(policy_actions))
    full_policy_coverage = sorted(policy_actions) == sorted(original_actions)
    result = {
        "label": label,
        "semantics": (
            "one deterministic fixed B per source class, refined into exact "
            "A leaves with one fixed common C response per leaf"
        ),
        "scope": (
            "finite depth-three policy partition on one frozen prefix; not a "
            "future-state congruence, inductive invariant, or greatest fixed point"
        ),
        "source_classes": len(class_results),
        "source_A_actions": len(original_actions),
        "source_A_domain_indices_sha256": stable_hash(sorted(original_actions)),
        "class_choices": class_choices,
        "total_refined_response_compatible_leaves": len(policy_leaf_records),
        "unresolved_terminals": len(unresolved_records),
        "unresolved_A_actions": len(original_actions) - len(policy_actions),
        "terminal_partition_covers_every_source_A_exactly_once": True,
        "policy_covers_every_source_A_exactly_once": full_policy_coverage,
        "exact_finite_policy_partition_available": full_policy_coverage,
        "policy_covered_A_domain_indices_sha256": stable_hash(
            sorted(policy_actions)
        ),
        "policy_leaf_lookup_records": policy_leaf_records,
        "unresolved_terminal_records": unresolved_records,
        "future_state_congruence_or_GFP_proved": False,
    }
    result["policy_partition_sha256"] = stable_hash(result)
    return result


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


def validate_and_extract_interface(certificate_path):
    raw_sha256 = file_sha256(certificate_path)
    assert raw_sha256 == EXPECTED_AB_CERTIFICATE_SHA256
    with certificate_path.open() as handle:
        certificate = json.load(handle)

    interface = certificate["third_ply_interface"]
    interface_sha256 = stable_hash(interface)
    assert certificate["third_ply_interface_sha256"] == interface_sha256
    assert interface_sha256 == EXPECTED_THIRD_PLY_INTERFACE_SHA256
    assert certificate["input_sha256"] == EXPECTED_INPUT_SHA256
    assert interface["cursor_binding"]["input_sha256"] == EXPECTED_INPUT_SHA256
    assert certificate["checker_sha256"] == file_sha256(
        ROOT / "design/l8_immediate_action_cegar.py"
    )

    cursor = interface["cursor_binding"]
    assert (cursor["A"]["gap"], cursor["A"]["step"], cursor["A"]["pipeline_rank"]) == (
        A_GAP,
        A_STEP,
        A_RANK,
    )
    assert (cursor["B"]["gap"], cursor["B"]["step"], cursor["B"]["pipeline_rank"]) == (
        B_GAP,
        B_STEP,
        B_RANK,
    )
    assert (cursor["C"]["gap"], cursor["C"]["step"], cursor["C"]["pipeline_rank"]) == (
        C_GAP,
        C_STEP,
        C_RANK,
    )
    assert cursor["ranks_are_consecutive_A_then_B_then_C"] is True
    history_contract = interface["third_ply_history_contract"]
    assert history_contract["quantifier_order"] == "exists_B_exists_C_forall_A"
    assert history_contract["one_fixed_B_and_C_per_class"] is True
    assert history_contract["recorded_B_or_C_not_implicitly_added"] is True

    legal_a = interface["legal_A_domain_indices"]
    assert legal_a == sorted(set(legal_a))
    assert len(legal_a) == 1997
    assert stable_hash(legal_a) == interface["legal_A_domain_indices_sha256"]

    partition = interface["B_response_compatible_cegar_partition"]
    assert partition["leaf_count"] == len(partition["leaves"]) == 4
    assert partition["unresolved_leaf_count"] == 0
    assert partition["covers_every_legal_A_exactly_once"] is True
    covered = []
    classes = []
    for position, leaf in enumerate(partition["leaves"]):
        actions = leaf["A_domain_indices"]
        responses = leaf["common_B_domain_indices"]
        assert actions == sorted(set(actions))
        assert responses == sorted(set(responses)) and responses
        assert stable_hash(actions) == leaf["A_domain_indices_sha256"]
        assert stable_hash(responses) == leaf["common_B_domain_indices_sha256"]
        covered.extend(actions)
        classes.append({
            "kind": "partition-leaf",
            "name": f"partition-leaf-{position}-node-{leaf['cegar_node_id']}",
            "cegar_node_id": leaf["cegar_node_id"],
            "A_domain_indices": actions,
            "common_B_domain_indices": responses,
        })
    assert sorted(covered) == legal_a
    assert len(covered) == len(set(covered))

    probe = interface["selected_overlapping_probe_class"]
    probe_actions = probe["A_domain_indices"]
    probe_responses = probe["common_B_domain_indices"]
    assert probe["name"] == "maximal-single-response-class"
    assert probe_actions == sorted(set(probe_actions))
    assert len(probe_actions) == 1977
    assert probe_responses == [8765]
    assert stable_hash(probe_actions) == probe["A_domain_indices_sha256"]
    assert stable_hash(probe_responses) == probe["common_B_domain_indices_sha256"]
    assert set(probe_actions) <= set(legal_a)
    classes.append({
        "kind": "overlapping-probe",
        "name": "overlapping-maximal-single-response-B8765",
        "A_domain_indices": probe_actions,
        "common_B_domain_indices": probe_responses,
    })

    largest = interface["largest_partition_leaf_redundant_index"]
    matching = [
        item
        for item in classes[:-1]
        if item["cegar_node_id"] == largest["cegar_node_id"]
    ]
    assert len(matching) == 1
    assert matching[0]["A_domain_indices"] == largest["A_domain_indices"]
    assert matching[0]["common_B_domain_indices"] == largest[
        "common_B_domain_indices"
    ]
    assert len(largest["A_domain_indices"]) == 1241
    assert len(largest["common_B_domain_indices"]) == 4

    return certificate, interface, classes, raw_sha256


def source_to_destination_transfer(
    prefix,
    prefix_set,
    source_model,
    source_start,
    destination_model,
    destination_start,
):
    """Map every A site/line atom to every C atom it can poison.

    One packed direction set is built and discarded per source site.  This is
    globally exact over ``prefix`` and intentionally has no D=40 cutoff.
    """
    source_atom_count = len(source_model["atom_desc"])
    channel_names = ("collision-A-C", "P-A-C", "A-C-C", "A-A-C")
    channels = {name: [0] * source_atom_count for name in channel_names}
    total = [0] * source_atom_count
    destination_sites = [
        (add(destination_start, offset), atom)
        for offset, atom in destination_model["site_id"].items()
    ]
    destination_directions = list(destination_model["line_by_direction"].items())

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

        channels["collision-A-C"][source_atom] = collision
        channels["P-A-C"][source_atom] = prefix_site
        channels["A-C-C"][source_atom] = source_on_destination_line
        total[source_atom] = collision | prefix_site | source_on_destination_line
        del directions
        if position % 20 == 0 or position == len(source_sites):
            print(
                f"A-site to C transfer: {position}/{len(source_sites)}",
                flush=True,
            )

    start_moments = {
        direction: cross(source_start, direction)
        for direction in source_model["line_by_direction"]
    }
    for (direction, local_moment), source_atom in source_model["line_id"].items():
        origin_moment = start_moments[direction]
        absolute_moment = tuple(
            origin_moment[index] + local_moment[index] for index in range(3)
        )
        effect = 0
        for q, destination_atom in destination_sites:
            if q in prefix_set:
                continue
            if cross(q, direction) == absolute_moment:
                effect |= 1 << destination_atom
        channels["A-A-C"][source_atom] = effect
        total[source_atom] |= effect

    return {"total": total, "channels": channels}


def aggregate_source_word(source_atoms, transfer):
    channel_bits = {
        name: union_bits(values[atom] for atom in source_atoms)
        for name, values in transfer["channels"].items()
    }
    return union_bits(transfer["total"][atom] for atom in source_atoms), channel_bits


def fixed_point_to_c_effect(
    point,
    prefix,
    prefix_set,
    c_model,
    c_start,
    c_sites,
    c_directions,
):
    directions = set()
    for p in prefix:
        key = direction_key(sub(p, point))
        if key is not None:
            directions.add(key)

    collision = 0
    prefix_site = 0
    for q, c_atom in c_sites:
        flag = 1 << c_atom
        if q == point:
            collision |= flag
        elif q not in prefix_set and direction_key(sub(q, point)) in directions:
            prefix_site |= flag

    point_on_c_line = 0
    relative = sub(point, c_start)
    for direction, by_moment in c_directions:
        c_atom = by_moment.get(cross(relative, direction))
        if c_atom is not None:
            point_on_c_line |= 1 << c_atom
    return {
        "collision-B-C": collision,
        "P-B-C": prefix_site,
        "B-C-C": point_on_c_line,
    }


def fixed_pair_to_c_effect(a, b, prefix_set, c_sites):
    direction = primitive(sub(b, a))
    assert direction is not None
    moment = cross(a, direction)
    effect = 0
    for q, c_atom in c_sites:
        if q in prefix_set:
            continue
        if cross(q, direction) == moment:
            effect |= 1 << c_atom
    return effect


def fixed_b_transfer(
    b_points,
    prefix,
    prefix_set,
    c_model,
    c_start,
    c_sites,
    c_directions,
    point_cache,
    pair_cache,
):
    channels = {
        "collision-B-C": 0,
        "P-B-C": 0,
        "B-C-C": 0,
        "B-B-C": 0,
    }
    for point in b_points:
        if point not in point_cache:
            point_cache[point] = fixed_point_to_c_effect(
                point,
                prefix,
                prefix_set,
                c_model,
                c_start,
                c_sites,
                c_directions,
            )
        for name, bits in point_cache[point].items():
            channels[name] |= bits

    for position, a in enumerate(b_points):
        for b in b_points[position + 1 :]:
            key = tuple(sorted((a, b)))
            if key not in pair_cache:
                pair_cache[key] = fixed_pair_to_c_effect(
                    a, b, prefix_set, c_sites
                )
            channels["B-B-C"] |= pair_cache[key]
    return union_bits(channels.values()), channels


def cross_a_b_to_c_transfer(
    source_model,
    source_start,
    b_points,
    prefix_set,
    c_sites,
):
    """Return A-site-atom -> C-site-atom masks for fixed B interiors."""
    result = [0] * len(source_model["atom_desc"])
    for offset, source_atom in source_model["site_id"].items():
        x = add(source_start, offset)
        effect = 0
        for y in b_points:
            if x == y:
                continue
            for q, c_atom in c_sites:
                if q == x or q == y or q in prefix_set:
                    continue
                if cross(sub(x, q), sub(y, q)) == (0, 0, 0):
                    effect |= 1 << c_atom
        result[source_atom] = effect
    return result


def effect_record(atom_bits, c_atom_count, c_word_masks, c_word_count):
    killed = atoms_to_word_bits(atom_bits, c_word_masks)
    return {
        "atoms": bits_record(atom_bits, c_atom_count),
        "killed_C_words": bits_record(killed, c_word_count),
    }


def update_history_digest(digest, a_index, atom_bits, killed_bits, atom_bytes, word_bytes):
    digest.update(struct.pack("<I", a_index))
    digest.update(atom_bits.to_bytes(atom_bytes, "little"))
    digest.update(killed_bits.to_bytes(word_bytes, "little"))


def initialize_history_digest(class_name, a_indices_sha256, b_index):
    digest = hashlib.sha256()
    binding = {
        "schema": "l8-third-ply-history-stream-v2",
        "class_name": class_name,
        "A_domain_indices_sha256": a_indices_sha256,
        "B_domain_index": b_index,
    }
    digest.update(stable_bytes(binding))
    digest.update(b"\n")
    return digest, binding


def candidate_identity(candidate):
    return candidate["A_domain_index"], candidate["B_domain_index"]


def compact_candidate(candidate, c_atom_count, c_word_count):
    return {
        "class": candidate["class"],
        "A_domain_index": candidate["A_domain_index"],
        "B_domain_index": candidate["B_domain_index"],
        "C_survivors": candidate["C_survivors"],
        "least_C_survivor": candidate["least_C_survivor"],
        "genuinely_incremental_XAB_atoms": candidate[
            "incremental_XAB_atoms"
        ].bit_count(),
        "genuinely_incremental_XAB_killed_words": candidate[
            "incremental_XAB_killed_words"
        ].bit_count(),
        "final_C_atoms": bits_record(candidate["final_atom_bits"], c_atom_count),
        "final_killed_C_words": bits_record(
            candidate["final_killed_bits"], c_word_count
        ),
    }


def complete_backstop(
    candidate,
    prefix,
    prefix_births,
    a_domain,
    b_domain,
    c_domain,
    a_start,
    b_start,
    c_start,
    c_end,
    c_model,
    c_word_count,
):
    a_index = candidate["A_domain_index"]
    b_index = candidate["B_domain_index"]
    a_points = word_interiors(a_start, a_domain[a_index])
    b_points = word_interiors(b_start, b_domain[b_index])
    history = prefix + a_points + b_points
    history_births = prefix_births + [LEVEL] * (len(a_points) + len(b_points))
    info = compute_poison(
        c_model,
        c_start,
        midpoint(c_start, c_end),
        history,
        history_births,
        LEVEL,
    )
    full_atom_bits = poisoned_atom_bits(info)
    del info, history, history_births
    assert full_atom_bits == candidate["final_atom_bits"]

    store = Store(prefix)
    assert word_legal_fast(a_start, a_domain[a_index], store, {}, MENU)
    store.add_many(a_points)
    assert word_legal_fast(b_start, b_domain[b_index], store, {}, MENU)
    store.add_many(b_points)
    c_index = candidate["least_C_survivor"]
    if c_index is not None:
        assert word_legal_fast(c_start, c_domain[c_index], store, {}, MENU)

    return {
        "history": compact_candidate(
            candidate, len(c_model["atom_desc"]), c_word_count
        ),
        "full_compute_poison_atom_mask_matches_transfer_union": True,
        "sequential_A_then_B_legality_checked_with_word_legal_fast": True,
        "least_surviving_C_checked_with_word_legal_fast": c_index is not None,
    }


def direct_winning_pair_checks(
    a_indices,
    minimum_a_index,
    b_index,
    c_index,
    prefix,
    a_domain,
    b_domain,
    c_domain,
    a_start,
    b_start,
    c_start,
):
    """Independently check a reported uniform B,C on boundary/worst A's."""
    selected = {}
    for role, a_index in (
        ("first-A-in-class", a_indices[0]),
        ("last-A-in-class", a_indices[-1]),
        ("minimum-C-survivor-A-for-this-B", minimum_a_index),
    ):
        selected.setdefault(a_index, []).append(role)

    records = []
    for a_index, roles in selected.items():
        a_points = word_interiors(a_start, a_domain[a_index])
        b_points = word_interiors(b_start, b_domain[b_index])
        store = Store(prefix)
        assert word_legal_fast(a_start, a_domain[a_index], store, {}, MENU)
        store.add_many(a_points)
        assert word_legal_fast(b_start, b_domain[b_index], store, {}, MENU)
        store.add_many(b_points)
        assert word_legal_fast(c_start, c_domain[c_index], store, {}, MENU)
        records.append({
            "A_domain_index": a_index,
            "roles": roles,
            "A_then_B_then_C_sequential_legality": True,
        })
    return records


def sweep_class(
    class_record,
    a_domain,
    b_domain,
    c_domain,
    a_model,
    a_start,
    b_start,
    base_c_atoms,
    base_c_killed,
    c_word_masks,
    c_atom_count,
    c_word_count,
    ta_cache,
    source_transfer,
    prefix,
    prefix_set,
    c_model,
    c_start,
    c_sites,
    c_directions,
    b_point_cache,
    b_pair_cache,
    candidate_observer,
):
    full_c_words = (1 << c_word_count) - 1
    atom_bytes = (c_atom_count + 7) // 8
    word_bytes = (c_word_count + 7) // 8
    a_indices = class_record["A_domain_indices"]
    a_indices_sha256 = stable_hash(a_indices)
    b_results = []
    winning_pair = None
    best_cegar_choice = None

    for response_position, b_index in enumerate(
        class_record["common_B_domain_indices"], 1
    ):
        b_points = word_interiors(b_start, b_domain[b_index])
        tb_bits, tb_channels = fixed_b_transfer(
            b_points,
            prefix,
            prefix_set,
            c_model,
            c_start,
            c_sites,
            c_directions,
            b_point_cache,
            b_pair_cache,
        )
        xab_by_a_site = cross_a_b_to_c_transfer(
            a_model, a_start, b_points, prefix_set, c_sites
        )
        tb_killed = atoms_to_word_bits(tb_bits, c_word_masks)

        common_c = full_c_words
        stream_digest, stream_binding = initialize_history_digest(
            class_record["name"], a_indices_sha256, b_index
        )
        fatal_histories = 0
        survivor_histogram = Counter()
        minimum = None
        maximum = None
        distinct_atom_masks = set()
        distinct_killed_masks = set()
        final_atom_masks = []
        final_killed_masks = []
        component_unions = {
            "BaseC": base_c_atoms,
            "TA": 0,
            "TB": tb_bits,
            "XAB": 0,
        }
        channel_unions = {
            "collision": tb_channels["collision-B-C"],
            "P-A-C": 0,
            "A-A-C": 0,
            "A-C-C": 0,
            "P-B-C": tb_channels["P-B-C"],
            "B-B-C": tb_channels["B-B-C"],
            "B-C-C": tb_channels["B-C-C"],
            "A-B-C": 0,
        }
        incremental_xab_atoms_union = 0
        incremental_xab_words_union = 0

        for ordinal, a_index in enumerate(a_indices, 1):
            if a_index not in ta_cache:
                ta_bits, ta_channels = aggregate_source_word(
                    a_model["word_atoms"][a_index], source_transfer
                )
                ta_cache[a_index] = (
                    ta_bits,
                    ta_channels,
                    atoms_to_word_bits(ta_bits, c_word_masks),
                )
            ta_bits, ta_channels, ta_killed = ta_cache[a_index]
            a_points = word_interiors(a_start, a_domain[a_index])
            assert not (set(a_points) & set(b_points))
            xab_bits = union_bits(
                xab_by_a_site[atom]
                for atom in a_model["word_atoms"][a_index]
            )
            without_xab = base_c_atoms | ta_bits | tb_bits
            final_atoms = without_xab | xab_bits
            xab_killed = atoms_to_word_bits(xab_bits, c_word_masks)
            without_xab_killed = base_c_killed | ta_killed | tb_killed
            killed = without_xab_killed | xab_killed
            if ordinal == 1:
                assert without_xab_killed == atoms_to_word_bits(
                    without_xab, c_word_masks
                )
                assert killed == atoms_to_word_bits(final_atoms, c_word_masks)
            incremental_atoms = xab_bits & ~without_xab
            incremental_words = killed & ~without_xab_killed
            survivors = c_word_count - killed.bit_count()
            least_c = None
            survivor_bits = full_c_words & ~killed
            if survivor_bits:
                least_c = (survivor_bits & -survivor_bits).bit_length() - 1
            else:
                fatal_histories += 1

            common_c &= survivor_bits
            survivor_histogram[survivors] += 1
            history_summary = (survivors, a_index)
            if minimum is None or history_summary < (minimum["count"], minimum["A_domain_index"]):
                minimum = {"count": survivors, "A_domain_index": a_index}
            if maximum is None or history_summary > (maximum["count"], maximum["A_domain_index"]):
                maximum = {"count": survivors, "A_domain_index": a_index}
            distinct_atom_masks.add(final_atoms)
            distinct_killed_masks.add(killed)
            final_atom_masks.append(final_atoms)
            final_killed_masks.append(killed)
            update_history_digest(
                stream_digest,
                a_index,
                final_atoms,
                killed,
                atom_bytes,
                word_bytes,
            )

            component_unions["TA"] |= ta_bits
            component_unions["XAB"] |= xab_bits
            channel_unions["collision"] |= ta_channels["collision-A-C"]
            channel_unions["P-A-C"] |= ta_channels["P-A-C"]
            channel_unions["A-A-C"] |= ta_channels["A-A-C"]
            channel_unions["A-C-C"] |= ta_channels["A-C-C"]
            channel_unions["A-B-C"] |= xab_bits
            incremental_xab_atoms_union |= incremental_atoms
            incremental_xab_words_union |= incremental_words

            candidate_observer({
                "class": class_record["name"],
                "A_domain_index": a_index,
                "B_domain_index": b_index,
                "C_survivors": survivors,
                "least_C_survivor": least_c,
                "incremental_XAB_atoms": incremental_atoms,
                "incremental_XAB_killed_words": incremental_words,
                "final_atom_bits": final_atoms,
                "final_killed_bits": killed,
            })
            if ordinal % 250 == 0 or ordinal == len(a_indices):
                print(
                    f"{class_record['name']} B={b_index}: "
                    f"{ordinal}/{len(a_indices)} A histories",
                    flush=True,
                )

        assert len(final_atom_masks) == len(final_killed_masks) == len(a_indices)
        cegar = c_response_cegar_partition(
            a_indices,
            final_atom_masks,
            final_killed_masks,
            base_c_atoms | tb_bits,
            c_model,
            c_domain,
        )
        assert cegar["root_common_C_response_mask"] == bits_record(
            common_c, c_word_count
        )
        assert cegar["unresolved_A_actions"] == fatal_histories
        cegar_score = cegar_selection_score(cegar, b_index)
        cegar_choice = {
            "B_domain_index": b_index,
            "selection_score_definition": [
                "unresolved_A_actions",
                "leaf_count",
                "nodes",
                "max_depth",
                "negative_largest_leaf_actions",
                "B_domain_index",
            ],
            "selection_score": list(cegar_score),
            "tree_sha256": cegar["tree_sha256"],
            "unresolved_terminals": cegar[
                "unresolved_no_common_response_terminals"
            ],
            "unresolved_A_actions": cegar["unresolved_A_actions"],
            "response_compatible_leaves": cegar[
                "response_compatible_leaves"
            ],
            "nodes": cegar["nodes"],
            "max_depth": cegar["max_depth"],
            "largest_response_compatible_leaf_actions": (
                0 if cegar["largest_response_compatible_leaf"] is None
                else cegar["largest_response_compatible_leaf"]["actions"]
            ),
        }
        if (
            best_cegar_choice is None
            or cegar_score < tuple(best_cegar_choice["selection_score"])
        ):
            best_cegar_choice = cegar_choice

        least_common_c = None
        if common_c:
            least_common_c = (common_c & -common_c).bit_length() - 1
            if winning_pair is None:
                winning_pair = {
                    "B_domain_index": b_index,
                    "C_domain_index": least_common_c,
                    "C_word": list(c_domain[least_common_c]),
                }
        direct_checks = []
        if least_common_c is not None:
            direct_checks = direct_winning_pair_checks(
                a_indices,
                minimum["A_domain_index"],
                b_index,
                least_common_c,
                prefix,
                a_domain,
                b_domain,
                c_domain,
                a_start,
                b_start,
                c_start,
            )

        b_results.append({
            "B_domain_index": b_index,
            "B_word": list(b_domain[b_index]),
            "B_interiors": [list(point) for point in b_points],
            "B_legal_for_every_A": (
                "certified by the pinned exact A-to-B interface"
            ),
            "histories": len(a_indices),
            "history_stream_format": (
                "canonical JSON binding header plus newline, then repeated "
                "<uint32 A_domain_index><5657-bit C atom mask><49402-bit "
                "killed-C-word mask>, little-endian"
            ),
            "history_stream_binding": stream_binding,
            "history_stream_sha256": stream_digest.hexdigest(),
            "C_response_CEGAR_selection_score": list(cegar_score),
            "C_response_CEGAR": cegar,
            "C_response_CEGAR_unresolved_A_equals_fatal_histories": True,
            "fatal_histories": fatal_histories,
            "forall_A_exists_C": fatal_histories == 0,
            "C_survivor_count_histogram": dict(sorted(survivor_histogram.items())),
            "minimum_C_survivors": minimum,
            "maximum_C_survivors": maximum,
            "common_C": bits_record(common_c, c_word_count),
            "exists_C_forall_A_for_this_fixed_B": bool(common_c),
            "least_common_C_domain_index": least_common_c,
            "least_common_C_word": (
                list(c_domain[least_common_c]) if least_common_c is not None else None
            ),
            "direct_sequential_checks_of_reported_winning_pair": direct_checks,
            "distinct_final_C_atom_masks": len(distinct_atom_masks),
            "distinct_final_killed_C_word_masks": len(distinct_killed_masks),
            "component_unions_over_A": {
                name: effect_record(bits, c_atom_count, c_word_masks, c_word_count)
                for name, bits in component_unions.items()
            },
            "overlapping_channel_unions_over_A": {
                name: effect_record(bits, c_atom_count, c_word_masks, c_word_count)
                for name, bits in channel_unions.items()
            },
            "genuinely_incremental_XAB": {
                "atoms_union": bits_record(
                    incremental_xab_atoms_union, c_atom_count
                ),
                "newly_killed_C_words_union": bits_record(
                    incremental_xab_words_union, c_word_count
                ),
            },
        })

        # Per-B masks are intentionally released before the next common B.
        del xab_by_a_site, distinct_atom_masks, distinct_killed_masks
        del final_atom_masks, final_killed_masks
        gc.collect()
        print(
            f"completed {class_record['name']} common B "
            f"{response_position}/{len(class_record['common_B_domain_indices'])}",
            flush=True,
        )

    winning_b_results = [
        record for record in b_results
        if record["exists_C_forall_A_for_this_fixed_B"]
    ]
    assert all(
        record["direct_sequential_checks_of_reported_winning_pair"]
        for record in winning_b_results
    )
    assert best_cegar_choice is not None
    return {
        "kind": class_record["kind"],
        "name": class_record["name"],
        "source_A_to_B_cegar_node_id": class_record.get("cegar_node_id"),
        "A_actions": len(a_indices),
        "A_domain_indices_sha256": a_indices_sha256,
        "common_B_actions_tested": len(class_record["common_B_domain_indices"]),
        "common_B_domain_indices_sha256": stable_hash(
            class_record["common_B_domain_indices"]
        ),
        "robust_lookup_table_quantifier": (
            "exists B in emitted common-B set, exists C in D_48, "
            "for every exact A in this class"
        ),
        "exists_fixed_B_and_C_forall_A": winning_pair is not None,
        "least_winning_fixed_pair": winning_pair,
        "reported_winning_fixed_pairs": len(winning_b_results),
        "direct_sequential_winning_pair_histories_checked": sum(
            len(record["direct_sequential_checks_of_reported_winning_pair"])
            for record in winning_b_results
        ),
        "best_fixed_B_for_CEGAR_policy_partition": best_cegar_choice,
        "B_sweeps": b_results,
    }


def preflight_paths(ab_certificate_path, output_path):
    ab_certificate_path = ab_certificate_path.expanduser()
    output_path = output_path.expanduser()
    if not ab_certificate_path.is_file():
        raise SystemExit(f"A-to-B certificate is not a file: {ab_certificate_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.parent.is_dir() or not os.access(output_path.parent, os.W_OK):
        raise SystemExit(f"output parent is not writable: {output_path.parent}")
    if output_path.exists() and not output_path.is_file():
        raise SystemExit(f"output path is not a regular file: {output_path}")
    if output_path.resolve() == ab_certificate_path.resolve():
        raise SystemExit("output path must differ from the A-to-B certificate")
    return ab_certificate_path, output_path


def atomic_write_json(output_path, value):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main(ab_certificate_path, output_path):
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    current_nice = os.getpriority(os.PRIO_PROCESS, 0)
    if current_nice < 10:
        raise SystemExit(
            f"refusing normal-priority run (nice={current_nice}); prepend nice -n 15"
        )
    thread_environment = {name: os.environ.get(name) for name in THREAD_ENVIRONMENT}
    if any(value != "1" for value in thread_environment.values()):
        raise SystemExit(
            "all thread environment variables must equal '1': "
            + repr(thread_environment)
        )
    ab_certificate_path, output_path = preflight_paths(
        ab_certificate_path, output_path
    )
    started = time.time()

    certificate, interface, classes, ab_raw_sha256 = validate_and_extract_interface(
        ab_certificate_path
    )
    del certificate

    input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert input_sha256 == EXPECTED_INPUT_SHA256
    checker_sha256 = file_sha256(Path(__file__).resolve())

    print("loading frozen L8 construction and selected domains", flush=True)
    domains, d24 = load_selected_domains()
    viz = load_viz()
    births_by_level = exact_birth_levels(viz)
    state, tile_gaps, _owners, schedule, guards = build_context(
        LEVEL, viz, births_by_level, d24
    )
    schedule_by_gap = {
        entry["gap"]: (rank, entry) for rank, entry in enumerate(schedule)
    }
    assert schedule_by_gap[A_GAP][0] == A_RANK
    assert schedule_by_gap[B_GAP][0] == B_RANK
    assert schedule_by_gap[C_GAP][0] == C_RANK
    assert schedule[A_RANK + 1]["gap"] == B_GAP
    assert schedule[B_RANK + 1]["gap"] == C_GAP
    assert tuple(tile_gaps[TILE]) == (67008, 67009, 67010, 67011)
    assert tuple(state["parent_word"][gap] for gap in tile_gaps[TILE]) == (
        48,
        14,
        24,
        34,
    )
    assert tuple(schedule_by_gap[gap][0] for gap in tile_gaps[TILE]) == (
        67012,
        67010,
        67009,
        67011,
    )
    assert guards.get(TILE) is None

    a_domain = list(domains[A_STEP])
    b_domain = list(domains[B_STEP])
    c_domain = list(domains[C_STEP])
    assert (len(a_domain), len(b_domain), len(c_domain)) == (5257, 9046, 49402)
    assert interface["cursor_binding"]["A"]["domain_sha256"] == stable_hash(a_domain)
    assert interface["cursor_binding"]["B"]["domain_sha256"] == stable_hash(b_domain)
    assert interface["cursor_binding"]["C"]["domain_sha256"] == stable_hash(c_domain)
    assert tuple(state["words"][A_GAP]) == RECORDED_A
    assert tuple(state["words"][B_GAP]) == RECORDED_B
    assert tuple(state["words"][C_GAP]) == RECORDED_C

    prefix, prefix_births = build_prefix(
        state, schedule, births_by_level[LEVEL - 1]
    )
    assert len(prefix) == EXPECTED_PREFIX_POINTS
    assert point_set_sha256(prefix) == EXPECTED_PREFIX_SHA256
    assert point_birth_sha256(prefix, prefix_births) == EXPECTED_PREFIX_BIRTH_SHA256
    assert dict(sorted(Counter(prefix_births).items())) == EXPECTED_BIRTH_HISTOGRAM

    a_start = state["anchors"][A_GAP]
    a_end = state["anchors"][A_GAP + 1]
    b_start = state["anchors"][B_GAP]
    b_end = state["anchors"][B_GAP + 1]
    c_start = state["anchors"][C_GAP]
    c_end = state["anchors"][C_GAP + 1]
    assert (a_start, a_end) == (
        (-71526, -1662, 13501),
        (-71532, -1668, 13499),
    )
    assert (b_start, b_end) == (
        (-71538, -1674, 13503),
        (-71541, -1680, 13498),
    )
    assert (c_start, c_end) == (
        (-71523, -1659, 13496),
        (-71526, -1662, 13501),
    )

    # Retain only objects used by the exact sweep before allocating masks.
    del domains, d24, viz, births_by_level, state, tile_gaps, schedule
    del schedule_by_gap, guards, _owners
    gc.collect()

    a_model = build_domain_model(a_domain)
    c_model = build_domain_model(c_domain)
    assert (
        len(a_model["site_id"]),
        len(a_model["line_id"]),
        len(a_model["line_by_direction"]),
        len(a_model["atom_desc"]),
    ) == EXPECTED_A_MODEL
    assert (
        len(c_model["site_id"]),
        len(c_model["line_id"]),
        len(c_model["line_by_direction"]),
        len(c_model["atom_desc"]),
    ) == EXPECTED_C_MODEL
    assert stable_hash(a_model["atom_desc"]) == EXPECTED_A_ATOM_DESC_SHA256
    assert stable_hash(a_model["word_atoms"]) == EXPECTED_A_WORD_ATOMS_SHA256
    assert stable_hash(c_model["atom_desc"]) == EXPECTED_C_ATOM_DESC_SHA256
    assert stable_hash(c_model["word_atoms"]) == EXPECTED_C_WORD_ATOMS_SHA256
    assert Counter(map(len, c_domain)) == {3: 288, 4: 49114}
    assert Counter(map(len, c_model["word_atoms"])) == {3: 288, 6: 49114}

    c_atom_count = len(c_model["atom_desc"])
    c_word_count = len(c_domain)
    c_word_masks = atom_word_masks(c_model)
    full_c_words = (1 << c_word_count) - 1
    prefix_set = set(prefix)
    c_sites = [
        (add(c_start, offset), atom)
        for offset, atom in c_model["site_id"].items()
    ]
    c_directions = list(c_model["line_by_direction"].items())

    print("computing exact full-prefix BaseC poison", flush=True)
    base_c_info = compute_poison(
        c_model,
        c_start,
        midpoint(c_start, c_end),
        prefix,
        prefix_births,
        LEVEL,
    )
    base_c_atoms = poisoned_atom_bits(base_c_info)
    base_c_killed = atoms_to_word_bits(base_c_atoms, c_word_masks)
    del base_c_info
    gc.collect()

    print("computing exact all-prefix A-atom to C transfer", flush=True)
    source_transfer = source_to_destination_transfer(
        prefix,
        prefix_set,
        a_model,
        a_start,
        c_model,
        c_start,
    )

    ta_cache = {}
    b_point_cache = {}
    b_pair_cache = {}
    ordinary_candidate = None
    maximum_incremental_candidate = None
    maximum_incremental_distinct_from_ordinary = None
    maximum_incremental_distinct_b_from_ordinary = None

    def observe(candidate):
        nonlocal ordinary_candidate
        nonlocal maximum_incremental_candidate
        nonlocal maximum_incremental_distinct_from_ordinary
        nonlocal maximum_incremental_distinct_b_from_ordinary
        if ordinary_candidate is None:
            ordinary_candidate = candidate
        score = (
            candidate["incremental_XAB_killed_words"].bit_count(),
            candidate["incremental_XAB_atoms"].bit_count(),
            -candidate["A_domain_index"],
            -candidate["B_domain_index"],
        )
        if maximum_incremental_candidate is None or score > maximum_incremental_candidate[0]:
            maximum_incremental_candidate = (score, candidate)
        if candidate_identity(candidate) != candidate_identity(ordinary_candidate):
            if (
                maximum_incremental_distinct_from_ordinary is None
                or score > maximum_incremental_distinct_from_ordinary[0]
            ):
                maximum_incremental_distinct_from_ordinary = (score, candidate)
        if candidate["B_domain_index"] != ordinary_candidate["B_domain_index"]:
            if (
                maximum_incremental_distinct_b_from_ordinary is None
                or score > maximum_incremental_distinct_b_from_ordinary[0]
            ):
                maximum_incremental_distinct_b_from_ordinary = (score, candidate)

    class_results = []
    for class_position, class_record in enumerate(classes, 1):
        print(
            f"sweeping class {class_position}/{len(classes)}: "
            f"{class_record['name']}",
            flush=True,
        )
        class_results.append(sweep_class(
            class_record,
            a_domain,
            b_domain,
            c_domain,
            a_model,
            a_start,
            b_start,
            base_c_atoms,
            base_c_killed,
            c_word_masks,
            c_atom_count,
            c_word_count,
            ta_cache,
            source_transfer,
            prefix,
            prefix_set,
            c_model,
            c_start,
            c_sites,
            c_directions,
            b_point_cache,
            b_pair_cache,
            observe,
        ))

    partition_class_results = [
        record for record in class_results
        if record["kind"] == "partition-leaf"
    ]
    probe_class_results = [
        record for record in class_results
        if record["kind"] == "overlapping-probe"
    ]
    assert len(partition_class_results) == 4
    assert len(probe_class_results) == 1
    third_ply_policy_partition = refined_policy_partition(
        partition_class_results,
        "four source B-response-compatible partition leaves",
    )
    overlapping_probe_refinement = refined_policy_partition(
        probe_class_results,
        "overlapping 1977-action B=8765 probe",
    )
    assert third_ply_policy_partition["source_A_actions"] == 1997
    assert overlapping_probe_refinement["source_A_actions"] == 1977

    assert ordinary_candidate is not None
    assert maximum_incremental_candidate is not None
    global_maximum_candidate = maximum_incremental_candidate[1]
    assert global_maximum_candidate["incremental_XAB_atoms"]
    assert global_maximum_candidate["incremental_XAB_killed_words"]
    if (
        global_maximum_candidate["B_domain_index"]
        != ordinary_candidate["B_domain_index"]
    ):
        second_backstop_candidate = global_maximum_candidate
        second_backstop_role = (
            "global-largest-genuinely-incremental-XAB-history; distinct B"
        )
    elif maximum_incremental_distinct_b_from_ordinary is not None:
        second_backstop_candidate = maximum_incremental_distinct_b_from_ordinary[1]
        second_backstop_role = (
            "largest-genuinely-incremental-XAB-history-with-B-distinct-from-ordinary"
        )
    elif candidate_identity(global_maximum_candidate) == candidate_identity(ordinary_candidate):
        assert maximum_incremental_distinct_from_ordinary is not None
        second_backstop_candidate = maximum_incremental_distinct_from_ordinary[1]
        second_backstop_role = (
            "largest-incremental-XAB-history-distinct-from-ordinary; "
            "global maximizer equals ordinary"
        )
    else:
        second_backstop_candidate = global_maximum_candidate
        second_backstop_role = "global-largest-genuinely-incremental-XAB-history"
    if maximum_incremental_distinct_b_from_ordinary is not None:
        assert (
            second_backstop_candidate["B_domain_index"]
            != ordinary_candidate["B_domain_index"]
        )

    print("running two independent full-C history backstops", flush=True)
    backstops = []
    for role, candidate in (
        ("deterministic-first-history", ordinary_candidate),
        (second_backstop_role, second_backstop_candidate),
    ):
        record = complete_backstop(
            candidate,
            prefix,
            prefix_births,
            a_domain,
            b_domain,
            c_domain,
            a_start,
            b_start,
            c_start,
            c_end,
            c_model,
            c_word_count,
        )
        record["role"] = role
        backstops.append(record)

    all_partition_classes_close = all(
        record["exists_fixed_B_and_C_forall_A"]
        for record in class_results
        if record["kind"] == "partition-leaf"
    )
    probe_closes = next(
        record["exists_fixed_B_and_C_forall_A"]
        for record in class_results
        if record["kind"] == "overlapping-probe"
    )
    result = {
        "status": (
            "exact finite A+B-to-C robust lookup and C-response policy "
            "refinement on one frozen L8 causal prefix; not a greatest fixed point"
        ),
        "checker_sha256": checker_sha256,
        "input_sha256": input_sha256,
        "A_to_B_certificate": {
            "path": str(ab_certificate_path),
            "raw_file_sha256": ab_raw_sha256,
            "raw_file_sha256_verified": True,
            "third_ply_interface_sha256": EXPECTED_THIRD_PLY_INTERFACE_SHA256,
            "local_A_to_B_checker_sha256_verified": True,
        },
        "resource_policy": {
            "processes": 1,
            "python_worker_threads": 1,
            "nice": current_nice,
            "thread_environment": thread_environment,
            "thread_environment_required_exactly_one": True,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "scope_warning": {
            "one_frozen_prefix": True,
            "depth_three_only": True,
            "greatest_fixed_point_or_induction_proved": False,
            "original_strong_property_tested_is_uniform_B_C_per_source_leaf": True,
            "refined_policy_uses_fixed_B_per_source_and_fixed_C_per_refined_leaf": True,
            "identified_as_the_actual_observation_dependent_controller_quantifier": False,
            "exact_A_word_retained_during_each_transition": True,
            "classes_are_future_state_congruences": False,
        },
        "geometry": {
            "prefix_points": len(prefix),
            "prefix_point_set_sha256": EXPECTED_PREFIX_SHA256,
            "prefix_coordinate_birth_sha256": EXPECTED_PREFIX_BIRTH_SHA256,
            "A": {"gap": A_GAP, "step": A_STEP, "rank": A_RANK},
            "B": {"gap": B_GAP, "step": B_STEP, "rank": B_RANK},
            "C": {
                "gap": C_GAP,
                "step": C_STEP,
                "rank": C_RANK,
                "start": list(c_start),
                "end": list(c_end),
                "domain_words": c_word_count,
                "sites": len(c_model["site_id"]),
                "lines": len(c_model["line_id"]),
                "directions": len(c_model["line_by_direction"]),
                "atoms": c_atom_count,
            },
        },
        "exact_poison_identity": {
            "formula": "Q_C(P,A,B) = BaseC(P) | TA(A) | TB(B) | XAB(A,B)",
            "BaseC": "collision, P-P-C, and P-C-C",
            "TA": "collision-A-C, P-A-C, A-A-C, and A-C-C",
            "TB": "collision-B-C, P-B-C, B-B-C, and B-C-C",
            "XAB": "A-B-C",
            "C_C_C": "excluded by the certified connector domain D_48",
            "distance_cutoff": None,
            "all_prefix_points_scanned": True,
        },
        "BaseC": {
            "atoms": bits_record(base_c_atoms, c_atom_count),
            "killed_C_words": bits_record(base_c_killed, c_word_count),
            "surviving_C_words": c_word_count - base_c_killed.bit_count(),
        },
        "quantified_class_results": class_results,
        "third_ply_CEGAR_policy_partition": third_ply_policy_partition,
        "overlapping_probe_CEGAR_refinement": overlapping_probe_refinement,
        "conclusions": {
            "all_four_partition_leaves_have_fixed_B_and_C": (
                all_partition_classes_close
            ),
            "overlapping_1977_action_B8765_probe_has_fixed_C": probe_closes,
            "finite_depth_three_uniform_lookup_table_on_frozen_partition": (
                all_partition_classes_close
            ),
            "exact_finite_third_ply_policy_partition_on_frozen_prefix": (
                third_ply_policy_partition[
                    "exact_finite_policy_partition_available"
                ]
            ),
            "overlapping_probe_exact_finite_policy_partition": (
                overlapping_probe_refinement[
                    "exact_finite_policy_partition_available"
                ]
            ),
            "unconditional_infinite_walk_theorem": False,
        },
        "global_largest_genuinely_incremental_XAB_history": compact_candidate(
            global_maximum_candidate, c_atom_count, c_word_count
        ),
        "global_incremental_XAB_nonzero": {
            "atoms": bool(global_maximum_candidate["incremental_XAB_atoms"]),
            "newly_killed_C_words": bool(
                global_maximum_candidate["incremental_XAB_killed_words"]
            ),
        },
        "full_C_backstops": backstops,
        "memory_discipline": {
            "unused_domain_and_visualization_data_released_before_masks": True,
            "fragile_D5_pickle_not_materialized": True,
            "only_A_B_C_D2_to_4_domains_retained": True,
            "common_B_words_processed_sequentially": True,
            "killed_word_masks_composed_distributively": True,
            "per_A_final_masks_retained_only_until_fixed_B_CEGAR_completed": True,
            "per_B_XAB_and_distinct-mask_sets_released_after_each_response": True,
            "full_C_compute_poison_scans_after_BaseC": 2,
            "full_C_backstops_use_distinct_B": (
                backstops[0]["history"]["B_domain_index"]
                != backstops[1]["history"]["B_domain_index"]
            ),
            "JSON_contains_mask_counts_and_hashes_not_full_bitsets": True,
        },
    }
    selected_choice_stream = [
        (
            record["name"],
            record["best_fixed_B_for_CEGAR_policy_partition"],
        )
        for record in class_results
    ]
    all_tree_stream = [
        (
            class_record["name"],
            b_record["B_domain_index"],
            b_record["C_response_CEGAR"]["tree_sha256"],
            b_record["C_response_CEGAR_selection_score"],
        )
        for class_record in class_results
        for b_record in class_record["B_sweeps"]
    ]
    all_cegar_trees = [
        b_record["C_response_CEGAR"]
        for class_record in class_results
        for b_record in class_record["B_sweeps"]
    ]
    cegar_headlines = {
        "combined_policy": (
            third_ply_policy_partition["policy_partition_sha256"],
            third_ply_policy_partition[
                "total_refined_response_compatible_leaves"
            ],
            third_ply_policy_partition["unresolved_A_actions"],
            third_ply_policy_partition["source_A_actions"],
        ),
        "overlapping_probe": (
            overlapping_probe_refinement["policy_partition_sha256"],
            overlapping_probe_refinement[
                "total_refined_response_compatible_leaves"
            ],
            overlapping_probe_refinement["unresolved_A_actions"],
            overlapping_probe_refinement["source_A_actions"],
        ),
        "selected_choice_stream_sha256": stable_hash(selected_choice_stream),
        "all_tree_stream": (
            stable_hash(all_tree_stream),
            len(all_cegar_trees),
            sum(tree["nodes"] for tree in all_cegar_trees),
            max(tree["nodes"] for tree in all_cegar_trees),
            max(tree["max_depth"] for tree in all_cegar_trees),
        ),
    }
    assert cegar_headlines == EXPECTED_C_RESPONSE_CEGAR_HEADLINES
    result["C_response_CEGAR_regression"] = {
        "headlines": cegar_headlines,
        "verified": True,
        "status": "pinned after the first exact C-response refinement run",
    }
    core_projection = core_sweep_regression_projection(result)
    core_projection_sha256 = stable_hash(core_projection)
    assert core_projection_sha256 == EXPECTED_CORE_SWEEP_REGRESSION_SHA256
    result["core_sweep_regression"] = {
        "source": "/tmp/l8-third-ply-closure-bootstrap.json",
        "projection_schema": core_projection["schema"],
        "projection_sha256": core_projection_sha256,
        "verified": True,
        "projection": core_projection,
        "new_CEGAR_fields_excluded_from_projection": True,
        "new_CEGAR_fields_status": "first-run finite evidence; not yet pinned",
    }
    assert full_c_words.bit_count() == c_word_count
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
        "--ab-certificate",
        type=Path,
        default=Path("/tmp/l8-immediate-action-cegar-hardened-canonical.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l8-third-ply-closure.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.ab_certificate, arguments.output)
