#!/usr/bin/env python3
"""Finite stabilization tests for the canonical L9 age-2 precursor.

This read-only analyzer joins the 146 realized L8 child states in the pinned
birth/shell trace to all 488 exact L9 descendant-corridor records in the pinned
inherited-anchor precursor.  It tests four nested candidate state keys:

``a_context``
    source mode + current step + actual parent connector word + actual slot;
``b_direct``
    ``a`` plus the exact endpoint-old-new-new mask;
``c_partner_birth``
    ``b`` plus the exact partner-birth-level mask vector; and
``d_partner_identity``
    ``c`` plus stable partner identities and exact per-partner masks.

A class is noncongruent when one candidate key has multiple exact full-mask
outcomes on this finite trace.  A repeated congruent class is only a finite
repeat.  Singleton classes are explicitly counted as inconclusive and never
reported as stabilization evidence.

Two ordered transition layers are also tested:

* each of 146 L8 states -> its actual ordered L9 descendants; and
* each of 42 L7 parents -> its actual ordered L8 children enriched by those
  L9 vectors.

No L9 connector choice, current-L9 connector point, alternate history,
universal Post relation, full sig2, or availability theorem is introduced.

Run on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/l9_age2_transition_stabilization.py run \
        --output /tmp/l9-age2-transition-stabilization.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_UPSTREAM = Path(
    "/tmp/far-secant-birth-shell-trace-canonical.json"
)
DEFAULT_PRECURSOR = Path(
    "/tmp/l9-anchor-age2-precursor-canonical.json"
)

EXPECTED_UPSTREAM_SHA256 = (
    "5c525ef4cc0c77ed96a2f67238e785d0382ead806f96479854a691498de99488"
)
EXPECTED_UPSTREAM_CHECKER_SHA256 = (
    "dd35f8ac5459d6df05d8b960f82b709f69380268ed144ac5c0e6789d178c35b9"
)
EXPECTED_PRECURSOR_SHA256 = (
    "961f9e5f0772d9df508ab0aefaa7405e3cc21637d59560cdda95c4edf61d809f"
)
EXPECTED_PRECURSOR_CHECKER_SHA256 = (
    "66f776e7ae4eff4c35d004d870d82458582a4c2b6516f20257149a08e5535b90"
)
EXPECTED_CHECKER_INPUT_SHA256 = {
    "design/far_secant_birth_shell_trace.py": (
        EXPECTED_UPSTREAM_CHECKER_SHA256
    ),
    "design/l9_anchor_age2_precursor.py": (
        EXPECTED_PRECURSOR_CHECKER_SHA256
    ),
}

EXPECTED_LINEAGE = {
    "parent_states": 42,
    "parent_identity_stream_sha256": (
        "58cd87a92f28dbc1c16df8193bfba19695f50063c122c34d376365dc21bc7df3"
    ),
    "child_states": 146,
    "child_identity_stream_sha256": (
        "fa061a23af382b3e8b005f848c86983b0817bec9b476e1bd3426674df22bcf9a"
    ),
    "descendant_corridors": 488,
    "descendant_identity_stream_sha256": (
        "25f2ed5965c68a3ed91175a040bb68940899a548cf2637c5e2f4746dd7d90361"
    ),
    "descendant_gap_stream_sha256": (
        "c983ad2a8af899460beeb91c3a6fae0b790e5c7251bec1f586fc6322fff355a9"
    ),
    "descendant_gap_range": [138338, 230558],
    "effective_step_domains": 90,
    "per_source": {
        "13171": {
            "parent_states": 27,
            "child_states": 89,
            "descendant_corridors": 305,
        },
        "21115": {
            "parent_states": 15,
            "child_states": 57,
            "descendant_corridors": 183,
        },
    },
}

EXPECTED_UPSTREAM_CORE = {
    "parent_states": 42,
    "child_states": 146,
    "effect_records": 64,
    "strict_join_residual_states": 61,
    "correlated_descriptor_terms": 94,
    "unique_correlated_descriptors": 32,
    "inherited_descriptor_terms": 53,
    "current_descriptor_terms": 29,
    "direct_descriptor_terms": 12,
    "records_with_inherited_partner_terms": 43,
    "records_with_current_partner_terms": 28,
    "records_with_both_partner_ages": 10,
}

LEVELS = (
    "a_context",
    "b_direct",
    "c_partner_birth",
    "d_partner_identity",
)
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "all thread-cap environment variables must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process nice level")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 15:
        raise RuntimeError(
            f"run under `nice -n 15`; observed nice value is {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def mask_identity(mask, expected_domain_words=None):
    required = {
        "domain_words", "killed_words", "mask_sha256", "exact_payload_ref"
    }
    assert required <= set(mask)
    domain_words = mask["domain_words"]
    if expected_domain_words is not None:
        assert domain_words == expected_domain_words
    assert 0 <= mask["killed_words"] <= domain_words
    assert mask["exact_payload_ref"] == (
        f"{domain_words}:{mask['mask_sha256']}"
    )
    return {
        "domain_words": domain_words,
        "killed_words": mask["killed_words"],
        "mask_sha256": mask["mask_sha256"],
    }


def validate_inputs(upstream_path, precursor_path):
    observed_checkers = {
        name: file_sha256(ROOT / name)
        for name in EXPECTED_CHECKER_INPUT_SHA256
    }
    assert observed_checkers == EXPECTED_CHECKER_INPUT_SHA256

    upstream_path = upstream_path.resolve()
    precursor_path = precursor_path.resolve()
    upstream_hash = file_sha256(upstream_path)
    precursor_hash = file_sha256(precursor_path)
    if upstream_hash != EXPECTED_UPSTREAM_SHA256:
        raise RuntimeError(
            f"upstream SHA {upstream_hash}, expected {EXPECTED_UPSTREAM_SHA256}"
        )
    if precursor_hash != EXPECTED_PRECURSOR_SHA256:
        raise RuntimeError(
            f"precursor SHA {precursor_hash}, expected {EXPECTED_PRECURSOR_SHA256}"
        )

    upstream = json.loads(upstream_path.read_text())
    precursor = json.loads(precursor_path.read_text())
    assert upstream["checker_sha256"] == EXPECTED_UPSTREAM_CHECKER_SHA256
    assert upstream["core_census"] == EXPECTED_UPSTREAM_CORE
    assert len(upstream["parent_states"]) == 42
    assert len(upstream["child_states"]) == 146

    assert precursor["checker_sha256"] == EXPECTED_PRECURSOR_CHECKER_SHA256
    assert precursor["upstream_trace"]["sha256"] == EXPECTED_UPSTREAM_SHA256
    assert precursor["upstream_trace"]["checker_sha256"] == (
        EXPECTED_UPSTREAM_CHECKER_SHA256
    )
    assert precursor["lineage"] == EXPECTED_LINEAGE
    closure = precursor["exact_corridor_masks"]
    assert len(closure["records"]) == 488
    assert closure["effectful_corridors"] == 58
    assert closure["zero_effect_corridors"] == 430
    assert closure["minimum_tagged_component_survivors"] == 2413
    assert precursor["scope"]["endpoint_cutoff"] is None
    assert precursor["scope"]["distance_cutoff"] is None
    assert precursor["anchor_skeleton"]["omitted_current_l9_connector_interiors"]
    assert len(precursor["domain_models"][
        "direct_full_domain_word_geometry_backstops"
    ]) == 2
    assert all(
        record["all_four_channel_bitsets_equal_composed_masks"]
        for record in precursor["domain_models"][
            "direct_full_domain_word_geometry_backstops"
        ]
    )
    return upstream, precursor, {
        "upstream_raw_sha256": upstream_hash,
        "precursor_raw_sha256": precursor_hash,
        "checker_sha256": observed_checkers,
    }


def validate_precursor_masks(precursor):
    payloads = precursor["exact_mask_store"]["payloads"]
    partner_profiles = {
        record["stable_id"]: record
        for record in precursor["partner_profiles"]["profiles"]
    }
    assert len(partner_profiles) == precursor["partner_profiles"][
        "profile_count"
    ]
    records = precursor["exact_corridor_masks"]["records"]
    effectful = 0
    for record in records:
        domain_words = record["domain_words"]
        masks = [record["exact_tagged_age2_anchor_component_mask"]]
        masks.extend(record["exact_overlapping_channel_masks"].values())
        masks.extend(record["exact_endpoint_masks_overlap"].values())
        masks.extend(record["exact_partner_birth_level_masks_overlap"].values())
        masks.extend(record["exact_partner_masks_overlap"].values())
        for mask in masks:
            identity = mask_identity(mask, domain_words)
            reference = mask["exact_payload_ref"]
            assert reference in payloads
            assert payloads[reference]["domain_words"] == identity["domain_words"]
        full = mask_identity(
            record["exact_tagged_age2_anchor_component_mask"], domain_words
        )
        assert record["effectful"] == bool(full["killed_words"])
        assert record["tagged_component_survivors_not_full_legality"] == (
            domain_words - full["killed_words"]
        )
        effectful += bool(full["killed_words"])
        for stable_id in record["exact_partner_masks_overlap"]:
            assert stable_id in partner_profiles
    assert effectful == 58
    return partner_profiles


def build_join(upstream, precursor):
    parents = {}
    for parent in upstream["parent_states"]:
        key = (parent["source_gap"], parent["l7_parent_gap"])
        assert key not in parents
        parents[key] = parent
    children = {}
    for child in upstream["child_states"]:
        key = (child["source_gap"], child["l8_gap"])
        assert key not in children
        children[key] = child

    descendants = defaultdict(list)
    l9_gaps = set()
    for record in precursor["exact_corridor_masks"]["records"]:
        key = (record["source_gap"], record["l8_gap"])
        assert key in children
        assert record["l9_gap"] not in l9_gaps
        l9_gaps.add(record["l9_gap"])
        descendants[key].append(record)
    assert len(l9_gaps) == 488
    assert set(descendants) == set(children)

    for key, child in children.items():
        source_gap, l8_gap = key
        parent_key = (source_gap, child["l7_parent_gap"])
        assert parent_key in parents
        parent = parents[parent_key]
        parent_slot = child["actual_parent_connector_step_slot_zero_based"]
        assert parent["ordered_l8_child_gaps"][parent_slot] == l8_gap
        assert parent["actual_selected_connector_word"][parent_slot] == (
            child["step"]
        )

        records = sorted(
            descendants[key],
            key=lambda record: record[
                "actual_l8_connector_step_slot_zero_based"
            ],
        )
        word = child["actual_selected_connector_word"]
        assert len(records) == len(word)
        assert [
            record["actual_l8_connector_step_slot_zero_based"]
            for record in records
        ] == list(range(len(word)))
        for slot, record in enumerate(records):
            assert record["l8_child_state_sha256"] == stable_hash(child)
            assert record["l7_parent_gap"] == child["l7_parent_gap"]
            assert record["source_witness_type"] == child["witness_type"]
            assert record["actual_selected_l8_connector_word"] == word
            assert record["step"] == word[slot]
            assert record["selected_l9_connector_word"] is None
    return parents, children, descendants


def source_mode(record):
    return {
        "source_gap": record["source_gap"],
        "witness_type": record["source_witness_type"],
        "tagged_endpoint_stable_ids": record[
            "source_tagged_endpoint_stable_ids"
        ],
    }


def build_l9_nodes(descendants, partner_profiles):
    nodes = []
    for key in sorted(descendants):
        for record in sorted(
            descendants[key], key=lambda value: value["l9_gap"]
        ):
            domain_words = record["domain_words"]
            base = {
                "schema": "l9-age2-context-key-v1",
                "source_mode": source_mode(record),
                "step": record["step"],
                "actual_parent_connector_word": record[
                    "actual_selected_l8_connector_word"
                ],
                "actual_parent_word_slot_zero_based": record[
                    "actual_l8_connector_step_slot_zero_based"
                ],
            }
            direct = mask_identity(
                record["exact_overlapping_channel_masks"][
                    "endpoint-old-new-new"
                ],
                domain_words,
            )
            birth_vector = [
                [int(level), mask_identity(mask, domain_words)]
                for level, mask in sorted(
                    record[
                        "exact_partner_birth_level_masks_overlap"
                    ].items(),
                    key=lambda item: int(item[0]),
                )
            ]
            partner_vector = []
            for stable_id, mask in sorted(
                record["exact_partner_masks_overlap"].items()
            ):
                profile = partner_profiles[stable_id]
                partner_vector.append([
                    stable_id,
                    profile["birth_level"],
                    profile["age_at_l9"],
                    mask_identity(mask, domain_words),
                ])

            keys = {
                "a_context": base,
                "b_direct": {**base, "direct_endpoint_line_mask": direct},
            }
            keys["c_partner_birth"] = {
                **keys["b_direct"],
                "partner_birth_level_mask_vector": birth_vector,
            }
            keys["d_partner_identity"] = {
                **keys["c_partner_birth"],
                "partner_identity_mask_vector": partner_vector,
            }
            key_hashes = {
                level: stable_hash(keys[level]) for level in LEVELS
            }
            full = mask_identity(
                record["exact_tagged_age2_anchor_component_mask"],
                domain_words,
            )
            channel_vector = [
                [channel, mask_identity(mask, domain_words)]
                for channel, mask in sorted(
                    record["exact_overlapping_channel_masks"].items()
                )
            ]
            nodes.append({
                "address": {
                    "source_gap": record["source_gap"],
                    "l7_parent_gap": record["l7_parent_gap"],
                    "l8_gap": record["l8_gap"],
                    "l9_gap": record["l9_gap"],
                    "slot": record[
                        "actual_l8_connector_step_slot_zero_based"
                    ],
                    "step": record["step"],
                },
                "key_hashes": key_hashes,
                "full_mask": full,
                "full_mask_outcome_sha256": stable_hash(full),
                "exact_channel_vector_sha256": stable_hash(channel_vector),
                "nonzero": bool(full["killed_words"]),
            })
    assert len(nodes) == 488
    assert sum(node["nonzero"] for node in nodes) == 58
    return nodes


def class_kind(items):
    statuses = {item["nonzero"] for item in items}
    if statuses == {False}:
        return "all-zero"
    if statuses == {True}:
        return "all-nonzero"
    return "mixed-zero-nonzero"


def quotient_report(nodes, key_field, outcome_field, name):
    classes = defaultdict(list)
    for node in nodes:
        classes[node[key_field]].append(node)
    singleton = [items for items in classes.values() if len(items) == 1]
    repeated = [items for items in classes.values() if len(items) > 1]
    repeated_kinds = Counter(class_kind(items) for items in repeated)
    bad = []
    congruent_repeated = []
    for key_hash, items in classes.items():
        outcomes = {item[outcome_field] for item in items}
        if len(items) > 1 and len(outcomes) == 1:
            congruent_repeated.append(items)
        if len(outcomes) <= 1:
            continue
        bad.append({
            "candidate_key_sha256": key_hash,
            "class_nodes": len(items),
            "class_kind": class_kind(items),
            "distinct_outcomes": len(outcomes),
            "witnesses": [
                {
                    "address": item["address"],
                    "nonzero": item["nonzero"],
                    "outcome_sha256": item[outcome_field],
                    "full_mask": item.get("full_mask"),
                }
                for item in sorted(
                    items, key=lambda value: stable_bytes(value["address"])
                )[:6]
            ],
        })
    bad.sort(key=lambda record: (
        -record["class_nodes"], record["candidate_key_sha256"]
    ))
    congruent_kinds = Counter(
        class_kind(items) for items in congruent_repeated
    )
    return {
        "name": name,
        "nodes": len(nodes),
        "classes": len(classes),
        "singleton_classes_inconclusive": len(singleton),
        "singleton_zero_nodes": sum(not items[0]["nonzero"] for items in singleton),
        "singleton_nonzero_nodes": sum(items[0]["nonzero"] for items in singleton),
        "repeated_classes": len(repeated),
        "nodes_in_repeated_classes": sum(len(items) for items in repeated),
        "largest_repeated_class": max(map(len, repeated), default=0),
        "repeated_class_kind_census": dict(sorted(repeated_kinds.items())),
        "finite_congruent_repeated_classes": len(congruent_repeated),
        "finite_congruent_repeated_kind_census": dict(
            sorted(congruent_kinds.items())
        ),
        "noncongruent_classes": len(bad),
        "largest_noncongruent_class": max(
            (record["class_nodes"] for record in bad), default=0
        ),
        "refuted_on_this_finite_trace": bool(bad),
        "stabilization_proved": False,
        "counterexamples": bad[:4],
        "interpretation": (
            "noncongruence is a finite counterexample; a congruent repeat is "
            "finite evidence only; singleton classes are inconclusive"
        ),
    }


def build_l8_transition_nodes(
    parents, children, descendants, l9_nodes,
):
    l9_by_gap = {node["address"]["l9_gap"]: node for node in l9_nodes}
    nodes = []
    for key in sorted(children):
        child = children[key]
        parent = parents[(child["source_gap"], child["l7_parent_gap"])]
        parent_slot = child["actual_parent_connector_step_slot_zero_based"]
        input_key = {
            "schema": "realized-L8-parent-context-v1",
            "source_mode": {
                "source_gap": child["source_gap"],
                "witness_type": child["witness_type"],
            },
            "step": child["step"],
            "actual_parent_connector_word": parent[
                "actual_selected_connector_word"
            ],
            "actual_parent_word_slot_zero_based": parent_slot,
            "actual_selected_connector_word": child[
                "actual_selected_connector_word"
            ],
        }
        records = sorted(
            descendants[key],
            key=lambda record: record[
                "actual_l8_connector_step_slot_zero_based"
            ],
        )
        outcome_vectors = {}
        for level in LEVELS:
            vector = []
            for record in records:
                l9_node = l9_by_gap[record["l9_gap"]]
                vector.append({
                    "slot": record[
                        "actual_l8_connector_step_slot_zero_based"
                    ],
                    "step": record["step"],
                    "child_state_key_sha256": l9_node["key_hashes"][level],
                    "child_full_mask_outcome_sha256": l9_node[
                        "full_mask_outcome_sha256"
                    ],
                })
            outcome_vectors[level] = stable_hash(vector)
        nodes.append({
            "address": {
                "source_gap": child["source_gap"],
                "l7_parent_gap": child["l7_parent_gap"],
                "l8_gap": child["l8_gap"],
                "parent_slot": parent_slot,
                "step": child["step"],
            },
            "parent_context_key_sha256": stable_hash(input_key),
            "ordered_l9_outcome_vector_sha256": outcome_vectors,
            "nonzero": any(
                l9_by_gap[record["l9_gap"]]["nonzero"] for record in records
            ),
        })
    assert len(nodes) == 146
    return nodes


def build_l7_transition_nodes(parents, children, l8_nodes):
    l8_by_key = {
        (node["address"]["source_gap"], node["address"]["l8_gap"]): node
        for node in l8_nodes
    }
    nodes = []
    for key in sorted(parents):
        parent = parents[key]
        input_key = {
            "schema": "realized-L7-parent-context-v1",
            "source_gap": parent["source_gap"],
            "witness_type": parent["witness_type"],
            "step": parent["step"],
            "actual_selected_connector_word": parent[
                "actual_selected_connector_word"
            ],
        }
        ordered_children = []
        for slot, l8_gap in enumerate(parent["ordered_l8_child_gaps"]):
            child_key = (parent["source_gap"], l8_gap)
            assert child_key in children
            child = children[child_key]
            assert child["actual_parent_connector_step_slot_zero_based"] == slot
            ordered_children.append((child, l8_by_key[child_key]))
        outcome_vectors = {}
        for level in LEVELS:
            vector = [
                {
                    "slot": slot,
                    "step": child["step"],
                    "l8_parent_context_key_sha256": node[
                        "parent_context_key_sha256"
                    ],
                    "ordered_l9_outcome_vector_sha256": node[
                        "ordered_l9_outcome_vector_sha256"
                    ][level],
                }
                for slot, (child, node) in enumerate(ordered_children)
            ]
            outcome_vectors[level] = stable_hash(vector)
        nodes.append({
            "address": {
                "source_gap": parent["source_gap"],
                "l7_parent_gap": parent["l7_parent_gap"],
                "step": parent["step"],
            },
            "parent_context_key_sha256": stable_hash(input_key),
            "enriched_ordered_l8_outcome_vector_sha256": outcome_vectors,
            "nonzero": any(node["nonzero"] for _child, node in ordered_children),
        })
    assert len(nodes) == 42
    return nodes


def build_result(upstream, precursor, input_hashes, resource_policy):
    partner_profiles = validate_precursor_masks(precursor)
    parents, children, descendants = build_join(upstream, precursor)
    l9_nodes = build_l9_nodes(descendants, partner_profiles)

    l9_tests = {}
    for level in LEVELS:
        projected = [
            {
                **node,
                "candidate_key_sha256": node["key_hashes"][level],
            }
            for node in l9_nodes
        ]
        l9_tests[level] = quotient_report(
            projected,
            "candidate_key_sha256",
            "full_mask_outcome_sha256",
            f"L9 exact full-mask outcome under {level}",
        )

    l8_nodes = build_l8_transition_nodes(
        parents, children, descendants, l9_nodes
    )
    l8_tests = {}
    for level in LEVELS:
        projected = [
            {
                **node,
                "transition_outcome_sha256": node[
                    "ordered_l9_outcome_vector_sha256"
                ][level],
            }
            for node in l8_nodes
        ]
        l8_tests[level] = quotient_report(
            projected,
            "parent_context_key_sha256",
            "transition_outcome_sha256",
            f"L8 parent to ordered L9 {level} outcome vector",
        )

    l7_nodes = build_l7_transition_nodes(parents, children, l8_nodes)
    l7_tests = {}
    for level in LEVELS:
        projected = [
            {
                **node,
                "transition_outcome_sha256": node[
                    "enriched_ordered_l8_outcome_vector_sha256"
                ][level],
            }
            for node in l7_nodes
        ]
        l7_tests[level] = quotient_report(
            projected,
            "parent_context_key_sha256",
            "transition_outcome_sha256",
            f"L7 parent to enriched ordered L8/L9 {level} outcome vector",
        )

    return {
        "status": (
            "exact finite realized-path L8-to-L9 age2 state and ordered-"
            "transition stabilization diagnostic"
        ),
        "resource_policy": resource_policy,
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": input_hashes,
        "scope": {
            "upstream_l7_parent_states": 42,
            "upstream_l8_states": 146,
            "l9_descendant_states": 488,
            "l9_nonzero_tagged_component_states": 58,
            "l9_zero_tagged_component_states": 430,
            "actual_parent_words_and_slots_retained": True,
            "alternate_histories": False,
            "l9_connector_choices": False,
            "current_l9_connector_partners": False,
            "full_sig2_or_availability_theorem": False,
        },
        "candidate_key_definitions": {
            "a_context": (
                "source mode + L9 step + actual selected L8 parent word + "
                "actual slot in that word"
            ),
            "b_direct": "a + exact endpoint-old-new-new mask",
            "c_partner_birth": (
                "b + sparse exact partner-birth-level mask vector; absent "
                "levels mean the exact zero mask for the fixed step domain"
            ),
            "d_partner_identity": (
                "c + stable partner identity/birth/age and exact per-partner "
                "mask vector"
            ),
            "state_outcome": "exact full tagged age2 anchor-component mask",
        },
        "ordered_transition_key_definitions": {
            "l8_parent": (
                "source mode + L8 step + actual L7 parent word/slot + the "
                "actual selected L8 connector word; retaining the selected "
                "word prevents different realized actions from being called "
                "transition noncongruence"
            ),
            "l8_outcome": (
                "ordered vector of L9 slot, step, candidate state-key hash, "
                "and exact full-mask outcome hash"
            ),
            "l7_parent": (
                "source mode + L7 step + actual selected L7 connector word"
            ),
            "l7_outcome": (
                "ordered vector of enriched L8 parent/action keys and their "
                "ordered L9 outcome-vector hashes"
            ),
        },
        "joined_census": {
            "parents": len(parents),
            "children": len(children),
            "descendants": sum(map(len, descendants.values())),
            "children_with_complete_ordered_descendants": len(descendants),
            "l9_node_stream_sha256": stable_hash(l9_nodes),
            "l8_transition_node_stream_sha256": stable_hash(l8_nodes),
            "l7_transition_node_stream_sha256": stable_hash(l7_nodes),
        },
        "l9_candidate_state_tests": l9_tests,
        "l8_to_ordered_l9_transition_tests": l8_tests,
        "l7_to_enriched_ordered_l8_transition_tests": l7_tests,
        "headline_assessment": {
            "l9_noncongruent_classes_by_key": {
                level: l9_tests[level]["noncongruent_classes"]
                for level in LEVELS
            },
            "birth_and_identity_resolution_warning": (
                "c and d have no finite noncongruence, but every one of the "
                "58 nonzero L9 states is a singleton; their only repeated "
                "classes are all-zero, so this is not effectful-state "
                "stabilization evidence"
            ),
            "l8_transition_warning": (
                "after retaining the actual selected L8 connector action, "
                "all 146 L8 parent classes are singletons; the transition "
                "test is therefore wholly inconclusive"
            ),
            "enriched_l7_noncongruent_classes_by_key": {
                level: l7_tests[level]["noncongruent_classes"]
                for level in LEVELS
            },
        },
        "referee_boundary": {
            "finite_counterexample_rule": (
                "a noncongruent repeated class refutes that candidate key on "
                "this realized trace"
            ),
            "nonproof_rule": (
                "a congruent repeated class is finite evidence only; a "
                "singleton class supplies no stabilization evidence"
            ),
            "unavailable_claims": [
                "universal transition congruence over alternate legal choices",
                "poison from current-L9 connector interiors",
                "positive complete connector availability",
                "an unconditional Erdos #193 theorem",
            ],
        },
    }


def atomic_write_json(output, result):
    output = output.resolve()
    if not output.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {output.parent}")
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(payload), file_sha256(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run",))
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--precursor", type=Path, default=DEFAULT_PRECURSOR)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l9-age2-transition-stabilization.json"),
    )
    arguments = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; certificate assertions must remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resource_policy = enforce_resource_policy()
    upstream, precursor, input_hashes = validate_inputs(
        arguments.upstream, arguments.precursor
    )
    result = build_result(
        upstream, precursor, input_hashes, resource_policy
    )
    byte_count, output_hash = atomic_write_json(arguments.output, result)
    print(json.dumps({
        "output": str(arguments.output.resolve()),
        "bytes": byte_count,
        "sha256": output_hash,
        "l9_noncongruent_classes": {
            level: result["l9_candidate_state_tests"][level][
                "noncongruent_classes"
            ]
            for level in LEVELS
        },
        "l8_transition_noncongruent_classes": {
            level: result["l8_to_ordered_l9_transition_tests"][level][
                "noncongruent_classes"
            ]
            for level in LEVELS
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
