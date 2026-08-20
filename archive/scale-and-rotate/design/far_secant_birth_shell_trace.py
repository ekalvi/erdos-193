#!/usr/bin/env python3
"""Exact finite birth/shell mask expressions on the realized L7 -> L8 trace.

This is a small consumer of the pinned ``deep_incidence_lineage.py`` result
and ``far_secant_future_trace.py`` construction.  It does not rescan connector
domains.  For each retained realized L8 child it keeps:

* the exact direct mask commitment;
* the exact aggregate tagged-other-point mask commitment;
* the exact disjoint direct-only remainder supplied by the deep priority
  partition; and
* the exact correlated birth/spatial-shell mask commitments, split into
  inherited partners (birth level < 8) and current-level partners (birth
  level 8).

The deep JSON stores a mask hash and word count for every correlated
descriptor, but it does not store the raw bitsets or the aggregate OR of all
inherited descriptors and all current-level descriptors separately.  Those
two pieces are therefore represented here as canonical monotone OR
expressions over exact descriptor-mask commitments.  Such an expression is
an exact symbolic representation of its mask, but two different expressions
can denote the same bitset.  The program never adds descriptor word counts or
claims a disjoint inherited/current split.

The exact two-piece identity that *is* available in the artifact is

    full = tagged-other-partner mask  disjoint-union  direct-only remainder.

The inherited/current expressions form an overlapping cover of the first
piece.  Direct poisoning can also overlap the partner mask before the deep
priority partition is applied.

The quotient checks retain the actual selected connector word.  The enriched
parent tests retain the ordered contiguous child block and every actual child
connector choice; one separately labelled diagnostic parent key omits those
child fields.  They are finite falsification/non-falsification tests on one
recorded orbit only: there is no L9 observation, alternate history, Post
closure, contraction, positive availability bound, or infinite-walk theorem
here.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/far_secant_birth_shell_trace.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/far_secant_birth_shell_trace.py run \
        --output /tmp/far-secant-birth-shell-trace.json

The run is expected to take a few seconds, not the hours needed to regenerate
the deep artifact: it loads pinned JSON/pickles and replays the small
146-child future trace, but never loads the connector-domain pickles.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

import far_secant_future_trace as future  # noqa: E402


TARGET_LEVEL = 8
EXPECTED_FUTURE_CHECKER_SHA256 = (
    "6f286cb118166c1375eb777ec6e24bcdc58766b98538099c604eb97b5c3dd430"
)
EXPECTED_CORE_CENSUS = {
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
PRIMARY_CHANNELS = (
    "collision",
    "tagged-tagged-old-old",
    "tagged-other-old-old",
    "endpoint-old-new-new",
)


def stable_hash(value):
    return future.stable_hash(value)


def zero_mask(size):
    return future.zero_mask(size)


def mask_term_key(term):
    return {
        "descriptor": term["descriptor"],
        "mask": term["mask"],
    }


def term_shape_key(term):
    return {
        "descriptor": term["descriptor"],
        "tagged_birth_levels": term["tagged_birth_levels"],
        "tagged_spatial_shells": term["tagged_spatial_shells"],
        "partner_birth_levels": term["partner_birth_levels"],
        "partner_ages": term["partner_ages"],
        "partner_spatial_shells": term["partner_spatial_shells"],
    }


def term_count_key(term):
    return {
        **term_shape_key(term),
        "killed_words": term["mask"]["words"],
    }


def mask_family(terms, empty_mask):
    exact_terms = [mask_term_key(term) for term in terms]
    unique_masks = {}
    for term in exact_terms:
        unique_masks[stable_hash(term["mask"])] = term["mask"]
    if not unique_masks:
        aggregate = empty_mask
        status = "empty exact mask"
    elif len(unique_masks) == 1:
        aggregate = next(iter(unique_masks.values()))
        status = "aggregate equals the sole distinct exact OR term"
    else:
        aggregate = None
        status = (
            "raw aggregate bitset/hash absent from the pinned deep artifact; "
            "the canonical monotone OR expression is exact but may be "
            "non-minimal"
        )
    return {
        "representation": "canonical monotone OR of exact mask commitments",
        "terms": terms,
        "or_expression_sha256": stable_hash(exact_terms),
        "aggregate_mask_commitment_if_directly_available": aggregate,
        "aggregate_status": status,
    }


def descriptor_category(witness):
    channel = witness["channel"]
    if channel == "endpoint-old-new-new":
        assert witness["partner"] is None
        return "direct"
    if channel == "tagged-other-old-old":
        partner = witness["partner"]
        assert partner is not None
        birth_level = partner["birth_level"]
        assert birth_level <= TARGET_LEVEL
        return "current" if birth_level == TARGET_LEVEL else "inherited"
    if channel in ("collision", "tagged-tagged-old-old"):
        return "unsupported-primary-channel"
    raise AssertionError(f"not a primary descriptor witness: {channel}")


def exact_descriptor_terms(record):
    correlated = record["correlated_birth_shell_action_masks_overlap"]
    descriptor_atoms = defaultdict(set)
    descriptor_categories = defaultdict(set)
    descriptor_tagged_births = defaultdict(set)
    descriptor_tagged_shells = defaultdict(set)
    descriptor_partner_births = defaultdict(set)
    descriptor_partner_ages = defaultdict(set)
    descriptor_partner_shells = defaultdict(set)
    direct_atoms = set()
    inherited_atoms = set()
    current_atoms = set()
    all_atom_ids = set()

    for atom in record["atoms"]:
        atom_id = atom["atom_id"]
        assert atom_id not in all_atom_ids
        all_atom_ids.add(atom_id)
        atom_partner_categories = set()
        atom_primary_categories = set()
        assert atom["witnesses"]
        for witness in atom["witnesses"]:
            channel = witness["channel"]
            if channel not in PRIMARY_CHANNELS:
                continue
            descriptor = witness["correlated_birth_shell_descriptor"]
            assert descriptor in correlated
            category = descriptor_category(witness)
            descriptor_atoms[descriptor].add(atom_id)
            descriptor_categories[descriptor].add(category)
            tagged = witness["tagged_endpoint"]
            descriptor_tagged_births[descriptor].add(tagged["birth_level"])
            descriptor_tagged_shells[descriptor].add(tagged["spatial_shell"])
            atom_primary_categories.add(category)
            if witness["partner"] is not None:
                partner = witness["partner"]
                descriptor_partner_births[descriptor].add(
                    partner["birth_level"]
                )
                descriptor_partner_ages[descriptor].add(partner["age"])
                descriptor_partner_shells[descriptor].add(
                    partner["spatial_shell"]
                )
                atom_partner_categories.add(category)

        # The pinned data has no atom witnessed by both an inherited and a
        # current-level partner.  This makes the symbolic atom split clean;
        # killed-word masks may still overlap because a word can contain two
        # different atoms.
        assert not ({"inherited", "current"} <= atom_partner_categories)
        if "direct" in atom_primary_categories:
            direct_atoms.add(atom_id)
        if "inherited" in atom_primary_categories:
            inherited_atoms.add(atom_id)
        if "current" in atom_primary_categories:
            current_atoms.add(atom_id)
        assert "unsupported-primary-channel" not in atom_primary_categories

    assert set(correlated) == set(descriptor_atoms)
    assert inherited_atoms.isdisjoint(current_atoms)
    assert all_atom_ids == direct_atoms | inherited_atoms | current_atoms

    groups = {"direct": [], "inherited": [], "current": []}
    for descriptor, mask in sorted(correlated.items()):
        categories = descriptor_categories[descriptor]
        assert len(categories) == 1
        category = next(iter(categories))
        assert category in groups
        term = {
            "descriptor": descriptor,
            "mask": mask,
            "atom_ids": sorted(descriptor_atoms[descriptor]),
            "tagged_birth_levels": sorted(
                descriptor_tagged_births[descriptor]
            ),
            "tagged_spatial_shells": sorted(
                descriptor_tagged_shells[descriptor]
            ),
            "partner_birth_levels": sorted(
                descriptor_partner_births[descriptor]
            ),
            "partner_ages": sorted(descriptor_partner_ages[descriptor]),
            "partner_spatial_shells": sorted(
                descriptor_partner_shells[descriptor]
            ),
        }
        groups[category].append(term)

    return groups, {
        "all_effect_atom_ids": sorted(all_atom_ids),
        "direct_atom_ids": sorted(direct_atoms),
        "inherited_partner_atom_ids": sorted(inherited_atoms),
        "current_partner_atom_ids": sorted(current_atoms),
    }


def empty_decomposition(child, domain_size):
    empty = zero_mask(domain_size)
    observation = child["observation"]
    assert observation["endpoint_closure"] == empty
    assert observation["direct_endpoint_or_carried_line_submask"] == empty
    assert observation["deep_record_effectful"] is False
    assert observation["deep_domain_word_index_if_effectful"] is None
    family = mask_family([], empty)
    return {
        "full_killed_word_mask": empty,
        "direct_mask_before_priority": empty,
        "tagged_other_partner_mask": empty,
        "direct_only_remainder_after_partner_priority": empty,
        "direct_partner_word_overlap_count": 0,
        "direct_birth_shell_terms": family,
        "inherited_partner_birth_shell_terms": family,
        "current_level_partner_birth_shell_terms": family,
        "symbolic_atom_cover": {
            "all_effect_atom_ids": [],
            "direct_atom_ids": [],
            "inherited_partner_atom_ids": [],
            "current_partner_atom_ids": [],
        },
        "exact_cover_status": (
            "empty mask; every component and monotone OR expression is empty"
        ),
    }


def effect_decomposition(record, child, state7):
    observation = child["observation"]
    domain_size = record["domain_size"]
    empty = zero_mask(domain_size)
    assert record["source_gap"] == child["source_gap"]
    assert record["l8_gap"] == child["l8_gap"]
    assert record["l8_step"] == child["step"]
    assert observation["endpoint_closure"] == record["endpoint_closure"]
    assert observation["direct_endpoint_or_carried_line_submask"] == record[
        "direct_transport"
    ]
    assert observation["deep_domain_word_index_if_effectful"] == record[
        "chosen_word_index"
    ]
    assert record["chosen_word_avoids_endpoint_closure"] is True

    # Harden the source+gap join by checking the address that was stored by
    # the deep producer, rather than trusting the dictionary lookup alone.
    address = record["address"]
    parent_gap = child["l7_parent_gap"]
    assert address["l7_parent_gap"] == parent_gap
    assert address["actual_connector_step_slot_zero_based"] == child[
        "actual_parent_connector_step_slot_zero_based"
    ]
    assert address["actual_connector_word"] == list(state7["words"][parent_gap])

    primary = record["primary_channel_membership_masks_overlap"]
    priority = record["priority_disjoint_word_partition"]
    assert priority["priority"] == list(PRIMARY_CHANNELS)
    for channel in ("collision", "tagged-tagged-old-old"):
        assert primary[channel] == empty
        assert priority["masks"][channel] == empty
    direct = record["direct_transport"]
    partner = primary["tagged-other-old-old"]
    full = record["endpoint_closure"]
    direct_only = priority["masks"]["endpoint-old-new-new"]
    assert primary["endpoint-old-new-new"] == direct
    assert priority["masks"]["tagged-other-old-old"] == partner
    assert priority["cumulative_masks"]["tagged-other-old-old"] == partner
    assert priority["cumulative_masks"]["endpoint-old-new-new"] == full
    assert partner["words"] + direct_only["words"] == full["words"]
    overlap_count = direct["words"] + partner["words"] - full["words"]
    assert 0 <= overlap_count <= min(direct["words"], partner["words"])

    groups, atom_cover = exact_descriptor_terms(record)
    direct_family = mask_family(groups["direct"], empty)
    inherited_family = mask_family(groups["inherited"], empty)
    current_family = mask_family(groups["current"], empty)
    # On this pinned data the direct descriptor mask is exactly the direct
    # transport mask.  The partner aggregate is exact, while its inherited /
    # current subdivision remains a symbolic OR expression when it has more
    # than one distinct term.
    assert direct_family[
        "aggregate_mask_commitment_if_directly_available"
    ] == direct

    return {
        "full_killed_word_mask": full,
        "direct_mask_before_priority": direct,
        "tagged_other_partner_mask": partner,
        "direct_only_remainder_after_partner_priority": direct_only,
        "direct_partner_word_overlap_count": overlap_count,
        "direct_birth_shell_terms": direct_family,
        "inherited_partner_birth_shell_terms": inherited_family,
        "current_level_partner_birth_shell_terms": current_family,
        "symbolic_atom_cover": atom_cover,
        "exact_cover_status": (
            "full is the exact disjoint union of tagged_other_partner_mask "
            "and direct_only_remainder_after_partner_priority; the partner "
            "mask is the exact monotone OR of the inherited and current-level "
            "descriptor expressions, which may overlap at word level"
        ),
    }


def component_payload(child, decomposition):
    inherited = decomposition["inherited_partner_birth_shell_terms"]["terms"]
    current = decomposition["current_level_partner_birth_shell_terms"]["terms"]
    direct_terms = decomposition["direct_birth_shell_terms"]["terms"]
    base = {
        "witness_type": child["centered_geometry"]["witness_type"],
        "step": child["step"],
        "actual_selected_connector_word": child[
            "actual_selected_connector_word"
        ],
    }
    exact_term_key = {
        **base,
        "direct_mask": decomposition["direct_mask_before_priority"],
        "direct_terms": [mask_term_key(term) for term in direct_terms],
        "inherited_terms": [mask_term_key(term) for term in inherited],
        "current_terms": [mask_term_key(term) for term in current],
    }
    count_key = {
        **base,
        "direct_killed_words": decomposition[
            "direct_mask_before_priority"
        ]["words"],
        "direct_terms": [term_count_key(term) for term in direct_terms],
        "inherited_terms": [term_count_key(term) for term in inherited],
        "current_terms": [term_count_key(term) for term in current],
    }
    presence_key = {
        **base,
        "direct_nonempty": bool(
            decomposition["direct_mask_before_priority"]["words"]
        ),
        "direct_terms": [term_shape_key(term) for term in direct_terms],
        "inherited_terms": [term_shape_key(term) for term in inherited],
        "current_terms": [term_shape_key(term) for term in current],
    }
    exact_payload = {
        "schema": "exact-symbolic-birth-shell-sig-0-v1",
        **exact_term_key,
        "full_killed_word_mask": decomposition["full_killed_word_mask"],
    }
    return exact_payload, {
        "exact_descriptor_mask_terms": stable_hash(exact_term_key),
        "birth_shell_descriptor_counts": stable_hash(count_key),
        "birth_shell_descriptor_presence": stable_hash(presence_key),
    }


def quotient_test(records, name, key_name, outcome_name):
    classes = defaultdict(list)
    for record in records:
        classes[record["coarse_key_sha256"][key_name]].append(record)
    merged = [items for items in classes.values() if len(items) > 1]
    bad = []
    for key, items in classes.items():
        outcomes = {record[outcome_name] for record in items}
        if len(outcomes) <= 1:
            continue
        bad.append({
            "coarse_key_sha256": key,
            "class_nodes": len(items),
            "distinct_outcomes": len(outcomes),
            "witnesses": [
                {
                    "source_gap": record["source_gap"],
                    "l8_gap": record["l8_gap"],
                    "full_killed_word_mask": record["decomposition"][
                        "full_killed_word_mask"
                    ],
                    "decomposition_sig_0_sha256": record[
                        "decomposition_sig_0_sha256"
                    ],
                }
                for record in sorted(
                    items, key=lambda value: (value["source_gap"], value["l8_gap"])
                )[:6]
            ],
        })
    merged_nonzero = [
        items for items in merged
        if any(
            record["decomposition"]["full_killed_word_mask"]["words"]
            for record in items
        )
    ]
    return {
        "name": name,
        "nodes": len(records),
        "classes": len(classes),
        "merged_classes": len(merged),
        "nodes_in_merged_classes": sum(map(len, merged)),
        "merged_classes_with_a_nonzero_full_mask": len(merged_nonzero),
        "noncongruent_classes": len(bad),
        "largest_noncongruent_class": max(
            (item["class_nodes"] for item in bad), default=0
        ),
        "refuted_on_this_finite_trace": bool(bad),
        "counterexamples": bad[:4],
    }


def parent_quotient_test(records, name, key_name):
    classes = defaultdict(list)
    for record in records:
        classes[record["coarse_key_sha256"][key_name]].append(record)
    merged = [items for items in classes.values() if len(items) > 1]
    bad = []
    for key, items in classes.items():
        outcomes = {record["decomposition_sig_1_sha256"] for record in items}
        if len(outcomes) <= 1:
            continue
        bad.append({
            "coarse_key_sha256": key,
            "class_nodes": len(items),
            "distinct_sig_1_outcomes": len(outcomes),
            "witnesses": [
                {
                    "source_gap": record["source_gap"],
                    "l7_parent_gap": record["l7_parent_gap"],
                    "decomposition_sig_1_sha256": record[
                        "decomposition_sig_1_sha256"
                    ],
                }
                for record in sorted(
                    items,
                    key=lambda value: (
                        value["source_gap"], value["l7_parent_gap"]
                    ),
                )[:6]
            ],
        })
    return {
        "name": name,
        "nodes": len(records),
        "classes": len(classes),
        "merged_classes": len(merged),
        "nodes_in_merged_classes": sum(map(len, merged)),
        "noncongruent_classes_for_sig_1": len(bad),
        "largest_noncongruent_class": max(
            (item["class_nodes"] for item in bad), default=0
        ),
        "refuted_on_this_finite_trace": bool(bad),
        "counterexamples": bad[:4],
    }


def block_starts_with_uniqueness(parents, state7):
    starts = {}
    lengths = {}
    index = 0
    while index < len(parents):
        parent = parents[index]
        assert parent not in starts
        start = index
        while index < len(parents) and parents[index] == parent:
            index += 1
        starts[parent] = start
        lengths[parent] = index - start
    assert index == len(parents)
    for parent in range(len(state7["parent_word"])):
        assert lengths[parent] == len(state7["words"][parent])
    assert set(starts) == set(range(len(state7["words"]) + 1))
    assert lengths[len(state7["words"])] == 1
    return starts


def build_result(deep, trace, state7, state8, viz):
    parents7 = viz["levels"][7]["parents"]
    starts = block_starts_with_uniqueness(parents7, state7)
    closure = deep["all_domain_endpoint_incidence_closure"]
    domain_sizes = {
        row["step"]: row["domain_words"] for row in closure["model_census"]
    }
    occurrences = {}
    occurrence_gaps_by_source = {}
    for source in closure["per_source"]:
        source_gap = source["source_gap"]
        gaps = [record["l8_gap"] for record in source["occurrences"]]
        assert len(gaps) == len(set(gaps))
        occurrence_gaps_by_source[source_gap] = set(gaps)
        for record in source["occurrences"]:
            key = (source_gap, record["l8_gap"])
            assert key not in occurrences
            occurrences[key] = record

    parent_map = {}
    for parent in trace["parent_states"]:
        key = (parent["source_gap"], parent["l7_parent_gap"])
        assert key not in parent_map
        parent_map[key] = parent
    raw_children = {}
    for child in trace["child_states"]:
        key = (child["source_gap"], child["l8_gap"])
        assert key not in raw_children
        raw_children[key] = child

    child_records = []
    descriptor_counter = Counter()
    unique_descriptors = set()
    records_with_categories = Counter()
    mixed_partner_age_records = 0
    strict_residual = 0
    partner_metadata = {}
    for key, child in sorted(raw_children.items()):
        source_gap, gap = key
        assert parents7[gap] == child["l7_parent_gap"]
        parent_gap = child["l7_parent_gap"]
        slot = gap - starts[parent_gap]
        assert slot == child["actual_parent_connector_step_slot_zero_based"]
        assert state7["words"][parent_gap][slot] == child["step"]
        assert state8["parent_word"][gap] == child["step"]
        assert list(state8["words"][gap]) == child[
            "actual_selected_connector_word"
        ]
        record = occurrences.get(key)
        if record is None:
            decomposition = empty_decomposition(
                child, domain_sizes[child["step"]]
            )
        else:
            decomposition = effect_decomposition(record, child, state7)
            categories = set()
            for category, field in (
                ("direct", "direct_birth_shell_terms"),
                ("inherited", "inherited_partner_birth_shell_terms"),
                ("current", "current_level_partner_birth_shell_terms"),
            ):
                terms = decomposition[field]["terms"]
                descriptor_counter[category] += len(terms)
                unique_descriptors.update(term["descriptor"] for term in terms)
                if terms:
                    categories.add(category)
                    records_with_categories[category] += 1
            if {"inherited", "current"} <= categories:
                mixed_partner_age_records += 1
            if decomposition["full_killed_word_mask"] != decomposition[
                "direct_mask_before_priority"
            ]:
                assert decomposition["full_killed_word_mask"]["words"] > (
                    decomposition["direct_mask_before_priority"]["words"]
                )
                strict_residual += 1

        for profile in child["observation"]["joined_partner_profiles"]:
            invariant = {
                name: value for name, value in profile.items()
                if name != "centered_vector"
            }
            previous = partner_metadata.setdefault(profile["stable_id"], invariant)
            assert previous == invariant

        exact_payload, coarse_keys = component_payload(child, decomposition)
        child_records.append({
            "schema": "realized-L8-birth-shell-mask-state-v1",
            "source_gap": source_gap,
            "l8_gap": gap,
            "l7_parent_gap": parent_gap,
            "actual_parent_connector_step_slot_zero_based": slot,
            "witness_type": child["centered_geometry"]["witness_type"],
            "step": child["step"],
            "actual_selected_connector_word": child[
                "actual_selected_connector_word"
            ],
            "deep_record_effectful": record is not None,
            "decomposition": decomposition,
            "decomposition_sig_0_sha256": stable_hash(exact_payload),
            "full_mask_outcome_sha256": stable_hash(
                decomposition["full_killed_word_mask"]
            ),
            "coarse_key_sha256": coarse_keys,
        })

    child_map = {
        (record["source_gap"], record["l8_gap"]): record
        for record in child_records
    }
    assert len(child_map) == len(child_records)
    assert set(occurrences) <= set(child_map)
    # No retained parent block for one source happens to contain an effect of
    # the other source in the pinned orbit.  Assert this finite fact so a zero
    # source-specific observation is not presented as an all-source mask.
    for source_gap in occurrence_gaps_by_source:
        retained = {
            gap for source, gap in child_map if source == source_gap
        }
        other_effects = set().union(*(
            gaps for source, gaps in occurrence_gaps_by_source.items()
            if source != source_gap
        ))
        assert retained.isdisjoint(other_effects)

    parent_records = []
    for key, parent in sorted(parent_map.items()):
        source_gap, parent_gap = key
        word = list(state7["words"][parent_gap])
        begin = starts[parent_gap]
        children = [
            child_map[(source_gap, begin + slot)]
            for slot in range(len(word))
        ]
        assert [child["step"] for child in children] == word
        assert parent["actual_selected_connector_word"] == word
        ordered_exact = [
            {
                "slot": slot,
                "step": child["step"],
                "actual_selected_connector_word": child[
                    "actual_selected_connector_word"
                ],
                "decomposition_sig_0_sha256": child[
                    "decomposition_sig_0_sha256"
                ],
            }
            for slot, child in enumerate(children)
        ]
        exact_sig1_payload = {
            "schema": "realized-ordered-birth-shell-sig-1-v1",
            "witness_type": parent["centered_geometry"]["witness_type"],
            "parent_step": parent["step"],
            "actual_selected_parent_connector_word": word,
            "ordered_children": ordered_exact,
        }
        base_key = stable_hash({
            "witness_type": parent["centered_geometry"]["witness_type"],
            "parent_step": parent["step"],
            "actual_selected_parent_connector_word": word,
        })
        ordered_keys = {}
        for coarse_name in (
            "exact_descriptor_mask_terms",
            "birth_shell_descriptor_counts",
            "birth_shell_descriptor_presence",
        ):
            ordered_keys[coarse_name] = stable_hash({
                "witness_type": parent["centered_geometry"]["witness_type"],
                "parent_step": parent["step"],
                "actual_selected_parent_connector_word": word,
                "ordered_actual_children": [
                    {
                        "slot": slot,
                        "step": child["step"],
                        "actual_selected_connector_word": child[
                            "actual_selected_connector_word"
                        ],
                        "child_coarse_key_sha256": child[
                            "coarse_key_sha256"
                        ][coarse_name],
                    }
                    for slot, child in enumerate(children)
                ],
            })
        parent_records.append({
            "schema": "realized-L7-birth-shell-transition-state-v1",
            "source_gap": source_gap,
            "l7_parent_gap": parent_gap,
            "witness_type": parent["centered_geometry"]["witness_type"],
            "step": parent["step"],
            "actual_selected_connector_word": word,
            "ordered_l8_child_gaps": [child["l8_gap"] for child in children],
            "decomposition_sig_1_sha256": stable_hash(exact_sig1_payload),
            "coarse_key_sha256": {
                "parent_mode_step_actual_choice_only": base_key,
                **ordered_keys,
            },
        })

    core_census = {
        "parent_states": len(parent_records),
        "child_states": len(child_records),
        "effect_records": len(occurrences),
        "strict_join_residual_states": strict_residual,
        "correlated_descriptor_terms": sum(descriptor_counter.values()),
        "unique_correlated_descriptors": len(unique_descriptors),
        "inherited_descriptor_terms": descriptor_counter["inherited"],
        "current_descriptor_terms": descriptor_counter["current"],
        "direct_descriptor_terms": descriptor_counter["direct"],
        "records_with_inherited_partner_terms": records_with_categories[
            "inherited"
        ],
        "records_with_current_partner_terms": records_with_categories[
            "current"
        ],
        "records_with_both_partner_ages": mixed_partner_age_records,
    }
    assert core_census == EXPECTED_CORE_CENSUS

    child_tests = {
        name: quotient_test(
            child_records,
            description,
            name,
            "full_mask_outcome_sha256",
        )
        for name, description in (
            (
                "exact_descriptor_mask_terms",
                "mode + step + actual choice + direct mask + exact inherited/current descriptor-mask OR terms",
            ),
            (
                "birth_shell_descriptor_counts",
                "mode + step + actual choice + descriptor birth/shell labels and killed-word counts",
            ),
            (
                "birth_shell_descriptor_presence",
                "mode + step + actual choice + descriptor birth/shell labels without mask hashes or counts",
            ),
        )
    }
    parent_tests = {
        "parent_mode_step_actual_choice_only": parent_quotient_test(
            parent_records,
            "diagnostic parent key omitting child poison states and child connector choices",
            "parent_mode_step_actual_choice_only",
        )
    }
    for name in (
        "exact_descriptor_mask_terms",
        "birth_shell_descriptor_counts",
        "birth_shell_descriptor_presence",
    ):
        parent_tests[name] = parent_quotient_test(
            parent_records,
            "parent mode + step + actual choice + ordered actual child "
            + name,
            name,
        )

    return {
        "status": (
            "exact finite realized-path birth/shell mask-expression and "
            "one-generation transition experiment"
        ),
        "scope": {
            "levels": [7, 8],
            "alternate_connector_histories": False,
            "endpoint_or_distance_cutoff": None,
            "raw_connector_domain_masks_reconstructed": False,
            "actual_connector_choices_retained": True,
            "ordered_parent_child_blocks_retained": True,
            "sig_2_or_L9_available": False,
        },
        "artifact_information_limit": {
            "exact_aggregate_masks_available": [
                "full tagged-endpoint closure",
                "direct transport",
                "tagged-other partner total",
                "direct-only remainder after partner-first priority",
            ],
            "exact_symbolic_masks_available": [
                "inherited-partner birth/shell monotone OR expression",
                "current-level-partner birth/shell monotone OR expression",
            ],
            "not_available_without_domain_rescan": [
                "aggregate bitset/hash and union cardinality for all inherited terms when multiple terms occur",
                "aggregate bitset/hash and union cardinality for all current-level terms when multiple terms occur",
                "disjoint inherited-versus-current word partition",
                "local re-derivation of the selected connector word from the stored deep domain index",
            ],
        },
        "core_census": core_census,
        "stable_partner_profiles_checked": len(partner_metadata),
        "child_quotient_tests": child_tests,
        "parent_transition_tests": parent_tests,
        "stabilization_claim_scope": (
            "A noncongruent class is a finite counterexample.  A congruent "
            "class is only a repeat on this orbit.  Singleton nonzero states "
            "and singleton parent classes provide no stabilization evidence, "
            "finite-state theorem, or future transition rule."
        ),
        "parent_states": parent_records,
        "child_states": child_records,
    }


def estimate(deep):
    closure = deep["all_domain_endpoint_incidence_closure"]
    occurrences = [
        record
        for source in closure["per_source"]
        for record in source["occurrences"]
    ]
    descriptor_entries = sum(
        len(record["correlated_birth_shell_action_masks_overlap"])
        for record in occurrences
    )
    return {
        "status": "static artifact estimate; no future trace built",
        "effect_records": len(occurrences),
        "correlated_descriptor_mask_entries": descriptor_entries,
        "expected_realized_child_states": EXPECTED_CORE_CENSUS["child_states"],
        "expected_realized_parent_states": EXPECTED_CORE_CENSUS["parent_states"],
        "connector_domain_pickles_needed": False,
        "expected_run_time": "a few seconds on one low-priority core",
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
    return len(payload), future.file_sha256(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument(
        "--deep-result", type=Path, default=future.DEFAULT_DEEP_RESULT
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/far-secant-birth-shell-trace.json"),
    )
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; certificate assertions must remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    observed_future_hash = future.file_sha256(Path(future.__file__).resolve())
    if observed_future_hash != EXPECTED_FUTURE_CHECKER_SHA256:
        raise RuntimeError(
            "far_secant_future_trace.py changed: observed "
            f"{observed_future_hash}, expected {EXPECTED_FUTURE_CHECKER_SHA256}"
        )
    resources = future.enforce_resource_policy()
    deep, input_hashes, deep_hash = future.validate_inputs(
        args.deep_result.resolve()
    )
    if args.mode == "estimate":
        result = estimate(deep)
        result["resource_policy"] = resources
        result["deep_result_sha256"] = deep_hash
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    viz = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    state7 = future.load_pickle("gate2-l7-construction-L7.pkl")
    state8 = future.load_pickle("gate2-l7-construction-L8.pkl")
    trace = future.build_experiment(deep, state7, state8, viz)
    result = build_result(deep, trace, state7, state8, viz)
    result["resource_policy"] = resources
    result["input_sha256"] = input_hashes
    result["deep_result_sha256"] = deep_hash
    result["future_trace_checker_sha256"] = observed_future_hash
    result["checker_sha256"] = future.file_sha256(Path(__file__).resolve())
    size, digest = atomic_write_json(args.output, result)
    print(
        f"wrote {args.output.resolve()} ({size} bytes, sha256 {digest})",
        flush=True,
    )


if __name__ == "__main__":
    main()
