#!/usr/bin/env python3
"""Poison-blind near-state projection and right-congruence census.

This checker is deliberately separate from
``ordered_path_matched_transition_experiment.py``.  It reuses that checker's
pinned, terminal-audited trace loader, but it never constructs a connector
domain mask, secant, candidate atom, or poison set.

The projection is frozen before any census counts are observed.  A0--A4 are
cumulative diagnostics; only A4 may qualify exact listed recorded classes for
a later, separately pinned poison experiment.  Every occurrence remains one
ordered factor.  The checker compares hashes of whole projected factors and
never forms Cartesian products of ancestry prefixes, bridge summaries,
actions, or successors.

Heavy modes require one thread, nice >= 15, one process, and a cooperative
core lease shared with the matched-transition checker.  ``census`` is capped
and resumable.  ``finalize`` refuses a partial checkpoint.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design"
sys.path.insert(0, str(DESIGN))

import ordered_path_matched_transition_experiment as matched  # noqa: E402


SCHEMA_VERSION = 1
EXPECTED_MATCHED_CHECKER_SHA256 = (
    "bf21411e391e31e1b954af1a61f4bc79c175e2038757ebd453d845066d281f84"
)
EXPECTED_OCCURRENCES = 139_344
EXPECTED_A0_CLASSES = 139_344
TRACE_ORDER = (
    "gate2-L5",
    "gate2-L6",
    "gate2-L7",
    "gate2-L8",
    "primary-L6",
)
ABLATIONS = ("A0", "A1", "A2", "A3", "A4")
MIN_CLASS_OCCURRENCES = 4
MAX_SECONDS = 110.0
MAX_OCCURRENCES_PER_RUN = 10_000
THREAD_ENVIRONMENT = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
MAX_REPORTED_WITNESSES = 24

DEFAULT_CHECKPOINT = Path(
    "/tmp/ordered-path-near-state-ablation-checkpoint-v1.json"
)
DEFAULT_OUTPUT = Path(
    "/tmp/ordered-path-near-state-ablation-verdict-v1.json"
)

PROCESS_START_CHECKER_SHA256 = None


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def assert_checker_unchanged():
    if file_sha256(Path(__file__).resolve()) != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("near-state checker changed during execution")
    observed = file_sha256(matched.__file__)
    if observed != EXPECTED_MATCHED_CHECKER_SHA256:
        raise RuntimeError(
            "pinned matched-transition interface changed", observed
        )


def atomic_json_dump(value, path):
    assert_checker_unchanged()
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(
                value, handle, sort_keys=True, separators=(",", ":")
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def immutable_json_dump(value, path):
    assert_checker_unchanged()
    path = Path(path).resolve()
    encoded = json.dumps(value, sort_keys=True, indent=2).encode() + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError("immutable output already differs", str(path))
        return
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def enforce_resources(mode):
    if mode == "estimate":
        return {
            "enforced": False,
            "processes": 1,
            "threads": 1,
        }
    environment = {name: os.environ.get(name) for name in THREAD_ENVIRONMENT}
    if any(value != "1" for value in environment.values()):
        raise RuntimeError(
            "all numerical-library thread variables must equal 1", environment
        )
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice < 15:
        raise RuntimeError("heavy modes require nice -n 15")
    return {
        "enforced": True,
        "processes": 1,
        "threads": 1,
        "nice": nice,
        "thread_environment": environment,
        "cooperative_core_limit": 2,
    }


def projection_schema():
    return {
        "schema": "ordered-path-near-state-projection-v1",
        "poison_blind": True,
        "only_recorded_panel_qualifying_projection": "A4",
        "theta": "exact matched-transition theta",
        "actual_action": "exact selected connector word",
        "A0": "exact full matched-transition state-action",
        "A1": (
            "A0 with relative coordinates and redundant natural offsets "
            "removed; one full ordered record stream remains"
        ),
        "A2": (
            "A1 with exact noncausal scheduler ranks replaced by the fixed "
            "six-valued scheduler tag"
        ),
        "A3": (
            "A2 with shared laminar owner relations retained for the first two "
            "roles in immediate-to-deeper ancestry-chain order and the deeper "
            "exact suffix replaced by a contiguous shared-tail marker"
        ),
        "A4": (
            "A3 exact on the union of the three complete causal parent "
            "blocks; every intervening bridge is folded as one ordered "
            "finite two-local monoid summary"
        ),
        "causal_scheduler_offsets": [-2, -1, 0],
        "scheduler_tags": [
            "causal-r-2", "causal-r-1", "current", "next-r+1",
            "other-placed", "other-future",
        ],
        "ancestry_exact_depth": 2,
        "ancestry_role_order": (
            "retain the first two exact roles in immediate-to-deeper chain "
            "order, including their exact positive strictly increasing owner-"
            "level ages; ages need not be consecutive"
        ),
        "deeper_tail_markers": [
            "absent", "factor-start", "same-as-previous-owner",
            "new-from-previous-owner", "within-depth-zero-owner",
        ],
        "bridge_monoid": {
            "symbol": "one complete depth-zero laminar owner block",
            "length_cap": 9,
            "prefix_symbols": 2,
            "suffix_symbols": 2,
            "all_adjacent_symbol_pairs": True,
            "per_symbol_multiplicity_cap": 2,
        },
        "mandatory_floor_keys": [
            "exact-theta-action",
            "exact-causal-core",
            "causal-laminar-topology",
            "current-successor-step-pair",
        ],
        "correlation_rule": (
            "each source, action, full factor, and actual successor remains "
            "one atomic occurrence; no truncated stream is independently "
            "recombined with another occurrence"
        ),
        "holdouts": {
            "discovery": ["gate2-L5", "gate2-L6", "gate2-L7"],
            "horizon": ["gate2-L8"],
            "separate_family": ["primary-L6"],
        },
        "right_congruence": (
            "same projected source state plus exact action implies the same "
            "complete successor envelope, including projected successor state, "
            "exact recorded policy action, natural-boundary status, and source-"
            "joinability; policy functionality from the same complete recorded "
            "state context without action is reported and gated separately"
        ),
        "complete_successor_envelope": [
            "ablation identifier",
            "projected successor state-action key",
            "projected successor state key without action",
            "exact recorded policy action",
            "natural-boundary status",
            "joinability as a recorded source",
        ],
        "policy_functionality_key": [
            "ablation identifier",
            "projected state key without action",
            "natural-boundary status",
            "joinability as a recorded source",
        ],
        "authorization_scope": (
            "A4 may qualify only the exact jointly qualifying recorded source "
            "classes for a later poison follow-up; unseen holdout sources are "
            "coverage failures and no broader source coverage is authorized"
        ),
    }


PROJECTION_SCHEMA = projection_schema()
PROJECTION_SCHEMA_SHA256 = stable_hash(PROJECTION_SCHEMA)
HOLDOUT_PARTITION_SHA256 = stable_hash(PROJECTION_SCHEMA["holdouts"])
CANDIDATE_STREAM_DEFINITION = {
    "trace_order": list(TRACE_ORDER),
    "scheduler_ranks": "range(2, len(schedule)-2)",
    "source_boundary_records_retained_for_diagnostics": True,
    "successor": "actual rank r+1 factor replayed from the same trace",
}
CANDIDATE_STREAM_DEFINITION_SHA256 = stable_hash(
    CANDIDATE_STREAM_DEFINITION
)


def trace_split(trace_id):
    if trace_id in {"gate2-L5", "gate2-L6", "gate2-L7"}:
        return "discovery"
    if trace_id == "gate2-L8":
        return "horizon-holdout"
    if trace_id == "primary-L6":
        return "separate-family-holdout"
    raise AssertionError("unregistered trace split", trace_id)


def factor_layout(factor):
    records = factor["records"]
    offsets = [record["natural_gap_offset"] for record in records]
    if offsets != list(range(offsets[0], offsets[0] + len(offsets))):
        raise AssertionError("ordered factor offsets are not contiguous")
    if offsets.count(0) != 1:
        raise AssertionError("ordered factor has no unique current record")
    if factor["interval_gap_offsets"] != [offsets[0], offsets[-1]]:
        raise AssertionError("ordered factor interval header drift")
    lower = offsets[0]
    causal_offsets = factor["causal_scheduler_offsets"]
    if causal_offsets != [-2, -1, 0]:
        raise AssertionError("causal scheduler offsets drift")
    by_span = defaultdict(list)
    for causal_offset, (left, right) in zip(
        causal_offsets, factor["complete_parent_block_gap_offsets"]
    ):
        if not lower <= left <= right <= offsets[-1]:
            raise AssertionError("causal block is outside ordered factor")
        by_span[(left - lower, right - lower)].append(causal_offset)
        causal_indices = [
            index for index, record in enumerate(records)
            if record["scheduler_rank_offset"] == causal_offset
        ]
        if (
            len(causal_indices) != 1
            or not left - lower <= causal_indices[0] <= right - lower
        ):
            raise AssertionError(
                "causal scheduler record is outside its declared owner block"
            )
    blocks = []
    previous_right = -1
    for (left, right), scheduler_offsets in sorted(by_span.items()):
        if left <= previous_right:
            raise AssertionError(
                "distinct causal parent blocks overlap without being equal"
            )
        blocks.append({
            "record_interval": [left, right],
            "causal_scheduler_offsets": scheduler_offsets,
        })
        previous_right = right
    membership = []
    for index in range(len(records)):
        roles = []
        for block in blocks:
            left, right = block["record_interval"]
            if left <= index <= right:
                roles.extend(block["causal_scheduler_offsets"])
        membership.append(sorted(roles))
    if sorted({
        offset for roles in membership for offset in roles
    }) != [-2, -1, 0]:
        raise AssertionError("causal block membership lost a scheduler role")
    return {
        "current_record_index": -lower,
        "complete_parent_block_record_intervals": blocks,
        "record_count": len(records),
        "core_membership": membership,
    }


def strip_derived_geometry(factor):
    layout = factor_layout(factor)
    records = []
    for record, membership in zip(
        factor["records"], layout["core_membership"]
    ):
        status = record["placement_status"]
        visible = record["actual_connector_word_if_placed"]
        if (
            (status == "placed" and visible is None)
            or (status != "placed" and visible is not None)
        ):
            raise AssertionError("ordered factor exposes a hidden connector word")
        projected = {
            key: copy.deepcopy(value)
            for key, value in record.items()
            if key not in {
                "natural_gap_offset", "start_relative", "end_relative",
            }
        }
        projected["causal_block_membership"] = list(membership)
        records.append(projected)
    return {
        "schema": "contiguous-ordered-factor-without-derived-geometry-v1",
        "orientation_quotient": factor["orientation_quotient"],
        "path_reversal_quotient": factor["path_reversal_quotient"],
        "chirality_quotient": factor["chirality_quotient"],
        "causal_scheduler_offsets": copy.deepcopy(
            factor["causal_scheduler_offsets"]
        ),
        "current_record_index": layout["current_record_index"],
        "complete_parent_block_record_intervals": layout[
            "complete_parent_block_record_intervals"
        ],
        "records": records,
    }


def scheduler_tag(offset):
    exact = {
        -2: "causal-r-2",
        -1: "causal-r-1",
        0: "current",
        1: "next-r+1",
    }
    if offset in exact:
        return exact[offset]
    return "other-placed" if offset < 0 else "other-future"


def normalize_scheduler(factor_a1):
    result = copy.deepcopy(factor_a1)
    result["schema"] = "finite-scheduler-tagged-ordered-factor-v1"
    for record in result["records"]:
        offset = record.pop("scheduler_rank_offset")
        record["scheduler_tag"] = scheduler_tag(offset)
        status = record["placement_status"]
        if (
            (offset < 0 and status != "placed")
            or (offset == 0 and status != "current")
            or (offset > 0 and status != "future-hidden")
        ):
            raise AssertionError("scheduler tag/placement status disagreement")
    return result


def role_without_slot(role):
    result = copy.deepcopy(role)
    if set(result) != {
        "owner_level_age", "parent_step", "parent_word", "slot",
    }:
        raise AssertionError("ancestry role schema drift")
    slot = result.pop("slot")
    word = result["parent_word"]
    if (
        isinstance(slot, bool)
        or not isinstance(slot, int)
        or not isinstance(word, list)
        or not 0 <= slot < len(word)
    ):
        raise AssertionError("ancestry role slot/word extent drift")
    return result, slot


def validate_ordered_ancestry_role_chain(chain, current_parent_step):
    if not isinstance(chain, list) or len(chain) < 2:
        raise AssertionError(
            "ancestry chain does not reach two retained ordered roles"
        )
    ages = []
    child_step = current_parent_step
    for role_index, role in enumerate(chain):
        role_without_position, slot = role_without_slot(role)
        age = role_without_position["owner_level_age"]
        parent_step = role_without_position["parent_step"]
        parent_word = role_without_position["parent_word"]
        if (
            isinstance(age, bool)
            or not isinstance(age, int)
            or age <= 0
            or ages and age <= ages[-1]
        ):
            raise AssertionError(
                "ancestry owner ages are not positive and strictly increasing",
                role_index, ages, age,
            )
        if (
            isinstance(parent_step, bool)
            or not isinstance(parent_step, int)
            or parent_word[slot] != child_step
        ):
            raise AssertionError(
                "ordered ancestry role does not own its child step",
                role_index,
            )
        ages.append(age)
        child_step = parent_step
    return tuple(ages)


def synthetic_ancestry_schema_self_check():
    def chain(first_age, second_age):
        return [
            {
                "owner_level_age": first_age,
                "parent_step": 1,
                "parent_word": [0],
                "slot": 0,
            },
            {
                "owner_level_age": second_age,
                "parent_step": 2,
                "parent_word": [1],
                "slot": 0,
            },
        ]

    accepted = [
        validate_ordered_ancestry_role_chain(chain(1, 3), 0),
        validate_ordered_ancestry_role_chain(chain(2, 3), 0),
    ]
    rejected = 0
    for invalid in (
        chain(2, 2),
        [chain(1, 3)[0], dict(chain(1, 3)[1], parent_word=[0])],
    ):
        try:
            validate_ordered_ancestry_role_chain(invalid, 0)
        except AssertionError:
            rejected += 1
    if accepted != [(1, 3), (2, 3)] or rejected != 2:
        raise AssertionError("synthetic ordered ancestry schema self-check failed")
    return {
        "accepted_nonconsecutive_age_pattern": [1, 3],
        "accepted_shifted_age_pattern": [2, 3],
        "rejected_nonincreasing_age_pattern": True,
        "rejected_broken_parent_child_link": True,
    }


def exact_depth_zero_blocks(chains, records):
    candidate_spans = set()
    for index, chain in enumerate(chains):
        validate_ordered_ancestry_role_chain(
            chain, records[index]["parent_step"]
        )
        role, slot = role_without_slot(chain[0])
        length = len(role["parent_word"])
        if role["parent_word"][slot] != records[index]["parent_step"]:
            raise AssertionError(
                "depth-zero role letter/current parent step disagreement"
            )
        role_one, slot_one = role_without_slot(chain[1])
        if role_one["parent_word"][slot_one] != role["parent_step"]:
            raise AssertionError(
                "depth-one role letter/depth-zero parent step disagreement"
            )
        candidate_spans.add((index - slot, index - slot + length - 1))
    spans = sorted(candidate_spans)
    if not spans or spans[0][0] != 0 or spans[-1][1] != len(chains) - 1:
        raise AssertionError("depth-zero owner blocks are clipped")
    for left, right in zip(spans, spans[1:]):
        if left[1] + 1 != right[0]:
            raise AssertionError(
                "depth-zero owner blocks do not partition the factor"
            )
    for left, right in spans:
        reference_role, _slot = role_without_slot(chains[left][0])
        reference_tail = chains[left][1:]
        if right - left + 1 != len(reference_role["parent_word"]):
            raise AssertionError("depth-zero owner block length drift")
        for index in range(left, right + 1):
            role, slot = role_without_slot(chains[index][0])
            if (
                role != reference_role
                or slot != index - left
                or chains[index][1:] != reference_tail
            ):
                raise AssertionError(
                    "depth-zero owner block lost laminar correlation"
                )
            if role["parent_word"][slot] != records[index]["parent_step"]:
                raise AssertionError(
                    "depth-zero role letter/current step disagreement"
                )
    return spans


def exact_depth_one_intervals(chains, depth_zero_blocks):
    intervals = []
    for block_index, (left, _right) in enumerate(depth_zero_blocks):
        role, slot = role_without_slot(chains[left][1])
        length = len(role["parent_word"])
        interval = (block_index - slot, block_index - slot + length - 1)
        if not interval[0] <= block_index <= interval[1]:
            raise AssertionError("depth-one owner interval misses its child")
        intervals.append(interval)
    unique = sorted(set(intervals))
    for left, right in zip(unique, unique[1:]):
        if left[1] >= right[0]:
            raise AssertionError(
                "distinct depth-one owner intervals overlap"
            )
    for owner_left, owner_right in unique:
        clipped_left = max(0, owner_left)
        clipped_right = min(len(depth_zero_blocks) - 1, owner_right)
        reference_gap = depth_zero_blocks[clipped_left][0]
        reference_role, _slot = role_without_slot(chains[reference_gap][1])
        reference_tail = chains[reference_gap][2:]
        for block_index in range(clipped_left, clipped_right + 1):
            gap = depth_zero_blocks[block_index][0]
            role, slot = role_without_slot(chains[gap][1])
            if (
                intervals[block_index] != (owner_left, owner_right)
                or role != reference_role
                or slot != block_index - owner_left
                or chains[gap][2:] != reference_tail
            ):
                raise AssertionError(
                    "depth-one owner interval lost laminar correlation"
                )
    return intervals


def truncate_laminar_ancestry(factor_a2):
    result = copy.deepcopy(factor_a2)
    result["schema"] = "depth-two-shared-laminar-ordered-factor-v1"
    original_chains = [
        copy.deepcopy(record["ancestry_role_chain"])
        for record in factor_a2["records"]
    ]
    depth_zero_blocks = exact_depth_zero_blocks(
        original_chains, factor_a2["records"]
    )
    declared_causal_blocks = {
        tuple(block["record_interval"])
        for block in factor_a2["complete_parent_block_record_intervals"]
    }
    if not declared_causal_blocks <= set(depth_zero_blocks):
        raise AssertionError(
            "declared causal span is not one exact laminar owner block"
        )
    depth_one_intervals = exact_depth_one_intervals(
        original_chains, depth_zero_blocks
    )
    block_by_record = {}
    for block_index, (left, right) in enumerate(depth_zero_blocks):
        for index in range(left, right + 1):
            block_by_record[index] = block_index
    previous_tail = None
    for index, (record, chain) in enumerate(zip(
        result["records"], original_chains
    )):
        block_index = block_by_record[index]
        block_left, _block_right = depth_zero_blocks[block_index]
        owner_left, owner_right = depth_one_intervals[block_index]
        at_block_start = index == block_left
        if at_block_start:
            depth_zero_relation = (
                "factor-start" if index == 0
                else "new-owner-from-previous"
            )
            if index == 0:
                depth_one_relation = "factor-start"
            elif depth_one_intervals[block_index - 1] == (
                owner_left, owner_right
            ):
                depth_one_relation = "same-owner-as-previous-block"
            else:
                depth_one_relation = "new-owner-from-previous-block"
            tail = chain[2:]
            if not tail:
                tail_marker = "absent"
            elif index == 0:
                tail_marker = "factor-start"
            elif depth_one_relation == "same-owner-as-previous-block":
                tail_marker = "same-as-previous-owner"
            else:
                tail_marker = "new-from-previous-owner"
            if (
                index > 0
                and depth_one_relation == "same-owner-as-previous-block"
                and previous_tail != tail
            ):
                raise AssertionError("shared depth-one owner changed deep tail")
            previous_tail = tail
        else:
            depth_zero_relation = "same-owner-as-previous"
            depth_one_relation = "within-depth-zero-owner"
            tail_marker = "within-depth-zero-owner"
        record["ancestry_role_chain"] = [
            {
                "role": copy.deepcopy(chain[0]),
                "owner_relation_to_previous": depth_zero_relation,
            },
            {
                "role": copy.deepcopy(chain[1]),
                "owner_relation_to_previous": depth_one_relation,
                "owner_clipped_left": owner_left < 0,
                "owner_clipped_right": owner_right >= len(depth_zero_blocks),
            },
        ]
        record["deeper_shared_tail_marker"] = tail_marker
        tail_length = len(chain) - 2
        record["deeper_tail_depth_class"] = (
            tail_length if tail_length < 3 else "3+"
        )
    return result


def unique_sorted(values):
    by_bytes = {canonical_bytes(value): value for value in values}
    return [by_bytes[key] for key in sorted(by_bytes)]


def two_local_bridge_summary(symbols):
    if not symbols:
        raise AssertionError("empty bridge must not be summarized")
    counts = {}
    values = {}
    for symbol in symbols:
        encoded = canonical_bytes(symbol)
        values[encoded] = symbol
        counts[encoded] = min(2, counts.get(encoded, 0) + 1)
    multiplicities = [
        {"symbol": values[encoded], "multiplicity_capped_at_two": counts[encoded]}
        for encoded in sorted(values)
    ]
    pairs = unique_sorted([
        [left, right] for left, right in zip(symbols, symbols[1:])
    ])
    return {
        "schema": "finite-two-local-ordered-bridge-monoid-v1",
        "length_capped_at_nine": len(symbols) if len(symbols) < 9 else "9+",
        "first_two_symbols": copy.deepcopy(symbols[:2]),
        "last_two_symbols": copy.deepcopy(symbols[-2:]),
        "adjacent_symbol_pairs": pairs,
        "symbol_multiplicities": multiplicities,
    }


def causal_core_and_bridges(factor_a3):
    records = factor_a3["records"]
    owner_blocks = []
    index = 0
    while index < len(records):
        relation = records[index]["ancestry_role_chain"][0][
            "owner_relation_to_previous"
        ]
        if relation not in {"factor-start", "new-owner-from-previous"}:
            raise AssertionError("depth-zero owner block lacks a start marker")
        end = index + 1
        while end < len(records) and records[end]["ancestry_role_chain"][0][
            "owner_relation_to_previous"
        ] == "same-owner-as-previous":
            end += 1
        block_records = records[index:end]
        core_flags = [bool(record["causal_block_membership"])
                      for record in block_records]
        if any(flag != core_flags[0] for flag in core_flags):
            raise AssertionError("causal core cuts a laminar owner block")
        owner_blocks.append({
            "is_core": core_flags[0],
            "symbol": {
                "schema": "complete-depth-zero-laminar-owner-block-v1",
                "records": copy.deepcopy(block_records),
            },
        })
        index = end
    is_core = [block["is_core"] for block in owner_blocks]
    if not owner_blocks or not is_core[0] or not is_core[-1]:
        raise AssertionError("ordered factor does not begin and end in its core")
    components = []
    index = 0
    while index < len(owner_blocks):
        core = is_core[index]
        end = index + 1
        while end < len(owner_blocks) and is_core[end] == core:
            end += 1
        segment = owner_blocks[index:end]
        if core:
            components.append({
                "kind": "exact-causal-core-segment",
                "owner_blocks": [
                    copy.deepcopy(block["symbol"]) for block in segment
                ],
            })
        else:
            components.append({
                "kind": "finite-correlated-bridge-summary",
                "summary": two_local_bridge_summary([
                    block["symbol"] for block in segment
                ]),
            })
        index = end
    return {
        "schema": "exact-causal-core-with-two-local-bridges-v1",
        "orientation_quotient": factor_a3["orientation_quotient"],
        "path_reversal_quotient": factor_a3["path_reversal_quotient"],
        "chirality_quotient": factor_a3["chirality_quotient"],
        "causal_scheduler_offsets": copy.deepcopy(
            factor_a3["causal_scheduler_offsets"]
        ),
        "causal_block_overlap_pattern": [
            record["causal_block_membership"]
            for record in records if record["causal_block_membership"]
        ],
        "components": components,
    }


def state_action(theta, factor, action, schema):
    return {
        "schema": schema,
        "theta": copy.deepcopy(theta),
        "ordered_factor": factor,
        "actual_selected_action": copy.deepcopy(action),
    }


def mandatory_floor_keys(theta, action, factor_a3, factor_a4):
    core_components = [
        component for component in factor_a4["components"]
        if component["kind"] == "exact-causal-core-segment"
    ]
    topology = []
    for component in core_components:
        for owner_block in component["owner_blocks"]:
            for record in owner_block["records"]:
                topology.append({
                    "causal_block_membership": record[
                        "causal_block_membership"
                    ],
                    "owner_relations": [
                        role["owner_relation_to_previous"]
                        for role in record["ancestry_role_chain"]
                    ],
                    "deeper_shared_tail_marker": record[
                        "deeper_shared_tail_marker"
                    ],
                    "deeper_tail_depth_class": record[
                        "deeper_tail_depth_class"
                    ],
                })
    floors = {
        "exact-theta-action": stable_hash({
            "theta": theta,
            "actual_selected_action": action,
        }),
        "exact-causal-core": stable_hash(core_components),
        "causal-laminar-topology": stable_hash(topology),
        "current-successor-step-pair": stable_hash([
            theta["current_step"], theta["next_step"]
        ]),
    }
    if set(floors) != set(PROJECTION_SCHEMA["mandatory_floor_keys"]):
        raise AssertionError("mandatory floor schema drift")
    return floors


def projected_state_actions(exact):
    theta = exact["theta"]
    action = exact["actual_selected_action"]
    factor = exact["ordered_factor"]
    factor_a1 = strip_derived_geometry(factor)
    factor_a2 = normalize_scheduler(factor_a1)
    factor_a3 = truncate_laminar_ancestry(factor_a2)
    factor_a4 = causal_core_and_bridges(factor_a3)
    state_action_payloads = {
        "A0": exact,
        "A1": state_action(
            theta, factor_a1, action, "near-state-ablation-A1-v1"
        ),
        "A2": state_action(
            theta, factor_a2, action, "near-state-ablation-A2-v1"
        ),
        "A3": state_action(
            theta, factor_a3, action, "near-state-ablation-A3-v1"
        ),
        "A4": state_action(
            theta, factor_a4, action, "near-state-ablation-A4-v1"
        ),
    }
    state_payloads = {
        name: {
            "schema": "projected-ordered-path-state-without-action-v1",
            "ablation": name,
            "theta": copy.deepcopy(state_action_payloads[name]["theta"]),
            "ordered_factor": copy.deepcopy(
                state_action_payloads[name]["ordered_factor"]
            ),
        }
        for name in ABLATIONS
    }
    return {
        "keys": {
            name: stable_hash(state_action_payloads[name])
            for name in ABLATIONS
        },
        "state_keys": {
            name: stable_hash(state_payloads[name]) for name in ABLATIONS
        },
        "exact_action_sha256": stable_hash(action),
        "mandatory_floor_keys": mandatory_floor_keys(
            theta, action, factor_a3, factor_a4
        ),
        "exact_factor_sha256": stable_hash(factor),
        "actual_placed_choice_stream_sha256": stable_hash([
            [record["placement_status"],
             record["actual_connector_word_if_placed"]]
            for record in factor["records"]
        ]),
        "full_factor_records": len(factor["records"]),
        "full_factor_committed_atomically": True,
    }


def make_occurrence_record(trace, rank, d24):
    source_exact, source_bounds = matched.abstract_state_action(
        trace, rank, d24
    )
    successor_exact, _successor_bounds = matched.abstract_state_action(
        trace, rank + 1, d24
    )
    source = projected_state_actions(source_exact)
    successor = projected_state_actions(successor_exact)
    occurrence_id = stable_hash({
        "schema": "projection-independent-concrete-occurrence-v1",
        "trace_id": trace["trace_id"],
        "scheduler_rank": rank,
        "gap": source_bounds["current_gap"],
    })
    boundary = (
        source_bounds["lower"] == 0
        or source_bounds["upper"] == len(trace["parent_word"]) - 1
    )
    successor_boundary = (
        _successor_bounds["lower"] == 0
        or _successor_bounds["upper"] == len(trace["parent_word"]) - 1
    )
    return {
        "occurrence_id": occurrence_id,
        "trace_id": trace["trace_id"],
        "family": trace["family"],
        "level": trace["level"],
        "split": trace_split(trace["trace_id"]),
        "scheduler_rank": rank,
        "ancestry_root": source_bounds["physical_root"],
        "boundary": boundary,
        "source_joinable_as_source": rank < len(trace["schedule"]) - 2,
        "actual_successor_boundary": successor_boundary,
        "actual_successor_joinable_as_source": (
            rank + 1 < len(trace["schedule"]) - 2
        ),
        "domain_step_pair": [
            source_exact["theta"]["current_step"],
            source_exact["theta"]["next_step"],
        ],
        "source": source,
        "actual_successor": successor,
        "correlation": (
            "one concrete source factor, its exact action, and its actual "
            "successor; never Cartesian-recombined"
        ),
        "poison_masks_consulted": False,
    }


def checkpoint_payload(checkpoint):
    return {
        key: value for key, value in checkpoint.items()
        if key != "checkpoint_payload_sha256"
    }


def seal_checkpoint(checkpoint):
    result = checkpoint_payload(checkpoint)
    result["checkpoint_payload_sha256"] = stable_hash(result)
    return result


def empty_chunk_chain_sha256():
    return stable_hash({"schema": "empty-near-state-record-chunk-chain-v1"})


def chunk_chain_sha256(prior_chain_sha256, descriptor_payload):
    return stable_hash({
        "schema": "near-state-record-chunk-chain-link-v1",
        "prior_chain_sha256": prior_chain_sha256,
        "descriptor": descriptor_payload,
    })


def chunk_path(checkpoint_path, start_occurrence, end_occurrence):
    checkpoint_path = Path(checkpoint_path).resolve()
    directory = Path(str(checkpoint_path) + ".chunks")
    return directory / (
        f"records-{start_occurrence:09d}-{end_occurrence:09d}.json"
    )


def expected_cursor_after_count(traces, completed_occurrences):
    remaining = completed_occurrences
    for trace_index, trace_id in enumerate(TRACE_ORDER):
        count = len(traces[trace_id]["schedule"]) - 4
        if remaining < count:
            return trace_index, 2 + remaining
        remaining -= count
    if remaining:
        raise AssertionError(
            "near-state completed occurrence count exceeds candidate stream"
        )
    return len(TRACE_ORDER), 2


def initial_checkpoint(input_snapshots):
    return seal_checkpoint({
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "poison_masks_consulted": False,
        "trace_order": list(TRACE_ORDER),
        "input_snapshots": input_snapshots,
        "next_trace_index": 0,
        "next_scheduler_rank": 2,
        "completed_occurrences": 0,
        "record_chunks": [],
        "record_chunk_chain_sha256": empty_chunk_chain_sha256(),
        "last_run": None,
    })


def validate_checkpoint(checkpoint, input_snapshots, traces, checkpoint_path):
    internal = checkpoint.get("checkpoint_payload_sha256")
    if internal != stable_hash(checkpoint_payload(checkpoint)):
        raise AssertionError("near-state checkpoint payload drift")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "poison_masks_consulted": False,
        "trace_order": list(TRACE_ORDER),
        "input_snapshots": input_snapshots,
    }
    if any(checkpoint.get(key) != value for key, value in expected.items()):
        raise AssertionError("near-state checkpoint static identity drift")
    chunks = checkpoint.get("record_chunks")
    if not isinstance(chunks, list):
        raise AssertionError("near-state checkpoint chunks are not a list")
    completed = 0
    prior_chain = empty_chunk_chain_sha256()
    prior_cursor = [0, 2]
    for index, descriptor in enumerate(chunks):
        descriptor_payload = {
            key: descriptor.get(key) for key in (
                "index", "path", "sha256", "bytes", "payload_sha256",
                "records_sha256", "record_count", "start_occurrence",
                "end_occurrence_exclusive", "start_cursor", "end_cursor",
            )
        }
        count = descriptor_payload["record_count"]
        end = descriptor_payload["end_occurrence_exclusive"]
        if (
            descriptor_payload["index"] != index
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count <= 0
            or descriptor_payload["start_occurrence"] != completed
            or end != completed + count
            or descriptor_payload["start_cursor"] != prior_cursor
            or descriptor_payload["start_cursor"] != list(
                expected_cursor_after_count(traces, completed)
            )
            or descriptor_payload["end_cursor"] != list(
                expected_cursor_after_count(traces, end)
            )
            or descriptor_payload["path"] != str(
                chunk_path(checkpoint_path, completed, end)
            )
        ):
            raise AssertionError("near-state chunk descriptor extent drift", index)
        expected_chain = chunk_chain_sha256(prior_chain, descriptor_payload)
        if descriptor.get("chain_sha256") != expected_chain:
            raise AssertionError("near-state chunk descriptor chain drift", index)
        prior_chain = expected_chain
        prior_cursor = descriptor_payload["end_cursor"]
        completed = end
    if checkpoint.get("completed_occurrences") != completed:
        raise AssertionError("near-state checkpoint occurrence extent drift")
    if checkpoint.get("record_chunk_chain_sha256") != prior_chain:
        raise AssertionError("near-state checkpoint record chunk chain drift")
    trace_index = checkpoint.get("next_trace_index")
    rank = checkpoint.get("next_scheduler_rank")
    if (
        isinstance(trace_index, bool)
        or not isinstance(trace_index, int)
        or not 0 <= trace_index <= len(TRACE_ORDER)
        or isinstance(rank, bool)
        or not isinstance(rank, int)
    ):
        raise AssertionError("near-state checkpoint cursor schema drift")
    complete = trace_index == len(TRACE_ORDER)
    if (checkpoint.get("status") == "complete") != complete:
        raise AssertionError("near-state checkpoint status/cursor disagreement")
    if checkpoint.get("status") not in {"partial", "complete"}:
        raise AssertionError("near-state checkpoint status drift")
    if not complete:
        trace = traces[TRACE_ORDER[trace_index]]
        if not 2 <= rank <= len(trace["schedule"]) - 2:
            raise AssertionError("near-state checkpoint rank outside trace")
    expected_cursor = expected_cursor_after_count(traces, completed)
    if (trace_index, rank) != expected_cursor:
        raise AssertionError(
            "near-state checkpoint cursor/count disagreement",
            (trace_index, rank), expected_cursor,
        )
    if chunks and chunks[-1]["end_cursor"] != [trace_index, rank]:
        raise AssertionError("near-state final chunk/cursor disagreement")
    if not chunks and (trace_index, rank) != (0, 2):
        raise AssertionError("empty near-state checkpoint cursor drift")


def load_or_initialize_checkpoint(path, input_snapshots, traces):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(input_snapshots)
    with path.open() as handle:
        checkpoint = json.load(handle)
    validate_checkpoint(checkpoint, input_snapshots, traces, path)
    return checkpoint


def advance_cursor(checkpoint, traces):
    while checkpoint["next_trace_index"] < len(TRACE_ORDER):
        trace_id = TRACE_ORDER[checkpoint["next_trace_index"]]
        trace = traces[trace_id]
        if checkpoint["next_scheduler_rank"] < len(trace["schedule"]) - 2:
            return
        checkpoint["next_trace_index"] += 1
        checkpoint["next_scheduler_rank"] = 2
    checkpoint["status"] = "complete"


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def chunk_payload_without_hash(chunk):
    return {
        key: value for key, value in chunk.items() if key != "payload_sha256"
    }


def append_record_chunk(
    checkpoint, checkpoint_path, records, start_cursor, end_cursor,
):
    if not records:
        return
    start = checkpoint["completed_occurrences"]
    end = start + len(records)
    path = chunk_path(checkpoint_path, start, end)
    payload = {
        "schema": "ordered-path-near-state-record-chunk-v1",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "index": len(checkpoint["record_chunks"]),
        "start_occurrence": start,
        "end_occurrence_exclusive": end,
        "start_cursor": list(start_cursor),
        "end_cursor": list(end_cursor),
        "record_count": len(records),
        "records_sha256": stable_hash(records),
        "records": records,
    }
    payload["payload_sha256"] = stable_hash(payload)
    immutable_json_dump(payload, path)
    stat = path.stat()
    descriptor_payload = {
        "index": payload["index"],
        "path": str(path.resolve()),
        "sha256": file_sha256(path),
        "bytes": stat.st_size,
        "payload_sha256": payload["payload_sha256"],
        "records_sha256": payload["records_sha256"],
        "record_count": payload["record_count"],
        "start_occurrence": start,
        "end_occurrence_exclusive": end,
        "start_cursor": list(start_cursor),
        "end_cursor": list(end_cursor),
    }
    chain = chunk_chain_sha256(
        checkpoint["record_chunk_chain_sha256"], descriptor_payload
    )
    descriptor = dict(descriptor_payload)
    descriptor["chain_sha256"] = chain
    checkpoint["record_chunks"].append(descriptor)
    checkpoint["record_chunk_chain_sha256"] = chain
    checkpoint["completed_occurrences"] = end


def load_record_chunks(checkpoint):
    records = []
    snapshots = []
    prior_chain = empty_chunk_chain_sha256()
    for index, descriptor in enumerate(checkpoint["record_chunks"]):
        path = Path(descriptor["path"]).resolve()
        before = path.stat()
        encoded = path.read_bytes()
        digest = hashlib.sha256(encoded).hexdigest()
        after = path.stat()
        identity = (
            "st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns",
        )
        if tuple(getattr(before, key) for key in identity) != tuple(
            getattr(after, key) for key in identity
        ):
            raise RuntimeError("record chunk changed while being read", str(path))
        if digest != descriptor["sha256"] or after.st_size != descriptor["bytes"]:
            raise AssertionError("record chunk file identity drift", index)
        chunk = json.loads(encoded)
        internal = chunk.get("payload_sha256")
        if internal != stable_hash(chunk_payload_without_hash(chunk)):
            raise AssertionError("record chunk payload drift", index)
        expected_static = {
            "schema": "ordered-path-near-state-record-chunk-v1",
            "checker_sha256": PROCESS_START_CHECKER_SHA256,
            "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
            "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
            "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
            "candidate_stream_definition_sha256": (
                CANDIDATE_STREAM_DEFINITION_SHA256
            ),
            "index": index,
            "start_occurrence": descriptor["start_occurrence"],
            "end_occurrence_exclusive": descriptor[
                "end_occurrence_exclusive"
            ],
            "start_cursor": descriptor["start_cursor"],
            "end_cursor": descriptor["end_cursor"],
            "record_count": descriptor["record_count"],
            "records_sha256": descriptor["records_sha256"],
            "payload_sha256": descriptor["payload_sha256"],
        }
        if any(chunk.get(key) != value for key, value in expected_static.items()):
            raise AssertionError("record chunk static identity drift", index)
        chunk_records = chunk.get("records")
        if (
            not isinstance(chunk_records, list)
            or len(chunk_records) != descriptor["record_count"]
            or stable_hash(chunk_records) != descriptor["records_sha256"]
        ):
            raise AssertionError("record chunk record stream drift", index)
        descriptor_payload = {
            key: descriptor[key] for key in (
                "index", "path", "sha256", "bytes", "payload_sha256",
                "records_sha256", "record_count", "start_occurrence",
                "end_occurrence_exclusive", "start_cursor", "end_cursor",
            )
        }
        expected_chain = chunk_chain_sha256(prior_chain, descriptor_payload)
        if descriptor["chain_sha256"] != expected_chain:
            raise AssertionError("record chunk chain drift", index)
        prior_chain = expected_chain
        records.extend(chunk_records)
        snapshots.append({
            "index": index,
            "path": str(path),
            "sha256": digest,
            "bytes": after.st_size,
            "payload_sha256": internal,
            "records_sha256": descriptor["records_sha256"],
            "record_count": descriptor["record_count"],
        })
    if prior_chain != checkpoint["record_chunk_chain_sha256"]:
        raise AssertionError("loaded record chunk chain drift")
    if len(records) != checkpoint["completed_occurrences"]:
        raise AssertionError("loaded record chunk extent drift")
    return records, snapshots


def load_trace_inputs(args):
    if file_sha256(matched.__file__) != EXPECTED_MATCHED_CHECKER_SHA256:
        raise RuntimeError("matched-transition checker pin drift")
    traces, snapshots = matched.load_all_traces(args)
    if tuple(sorted(traces, key=lambda key: TRACE_ORDER.index(key))) != TRACE_ORDER:
        raise AssertionError("pinned trace universe drift")
    return traces, snapshots


def audit_trace_words_against_domains(traces, domains):
    required = defaultdict(set)
    for trace_id in TRACE_ORDER:
        trace = traces[trace_id]
        for step, word in zip(trace["parent_word"], trace["selected_by_gap"]):
            required[step].add(tuple(word))
        for gap_role in trace["gap_roles"]:
            for role in gap_role["chain"]:
                required[role["parent_step"]].add(tuple(role["parent_word"]))
    missing = {}
    maximum_lengths = {}
    for step, words in domains.items():
        remaining = set(required.get(step, set()))
        maximum = 0
        for word in words:
            canonical = tuple(word)
            maximum = max(maximum, len(canonical))
            remaining.discard(canonical)
        maximum_lengths[step] = maximum
        if remaining:
            missing[step] = sorted(remaining)
    if set(required) - set(domains) or missing:
        raise AssertionError(
            "retained trace word is outside its pinned connector domain",
            sorted(set(required) - set(domains)), missing,
        )
    stream = [
        {
            "step": step,
            "required_words": [list(word) for word in sorted(required[step])],
            "required_word_count": len(required[step]),
            "maximum_domain_word_length": maximum_lengths[step],
        }
        for step in sorted(domains)
    ]
    return {
        "schema": "pinned-trace-word-domain-membership-audit-v1",
        "all_selected_and_retained_ancestry_words_found": True,
        "steps": len(domains),
        "required_distinct_words": sum(len(words) for words in required.values()),
        "stream_sha256": stable_hash(stream),
        "maximum_word_lengths_sha256": stable_hash(maximum_lengths),
    }


def audit_trace_ancestry_role_schema(traces):
    stream = []
    total_chains = 0
    nonconsecutive_chains = 0
    for trace_id in TRACE_ORDER:
        trace = traces[trace_id]
        age_patterns = Counter()
        length_counts = Counter()
        for gap, gap_role in enumerate(trace["gap_roles"]):
            if not isinstance(gap_role, dict) or set(gap_role) != {
                "physical_root", "chain",
            }:
                raise AssertionError(
                    "trace gap-role wrapper schema drift", trace_id, gap
                )
            chain = matched.canonical_role_chain(trace, gap)
            ages = validate_ordered_ancestry_role_chain(
                chain, trace["parent_word"][gap]
            )
            age_patterns[ages] += 1
            length_counts[len(chain)] += 1
            total_chains += 1
            if any(right != left + 1 for left, right in zip(ages, ages[1:])):
                nonconsecutive_chains += 1
        stream.append({
            "trace_id": trace_id,
            "level": trace["level"],
            "chains": len(trace["gap_roles"]),
            "age_pattern_counts": [
                {"ages": list(ages), "chains": count}
                for ages, count in sorted(age_patterns.items())
            ],
            "chain_length_counts": [
                {"roles": length, "chains": count}
                for length, count in sorted(length_counts.items())
            ],
        })
    return {
        "schema": "ordered-ancestry-role-chain-audit-v1",
        "role_order": "immediate owner to successively deeper owner",
        "minimum_retained_roles": 2,
        "exact_owner_level_ages_retained": True,
        "positive_strictly_increasing_ages": True,
        "consecutive_ages_required": False,
        "parent_child_step_links_checked_for_every_role": True,
        "chains": total_chains,
        "nonconsecutive_age_chains": nonconsecutive_chains,
        "trace_reports": stream,
        "trace_reports_sha256": stable_hash(stream),
    }


def load_traces(args):
    traces, snapshots = load_trace_inputs(args)
    domains, d24 = matched.load_domains()
    snapshots["near_state_ancestry_role_schema_audit"] = (
        audit_trace_ancestry_role_schema(traces)
    )
    snapshots["near_state_domain_word_audit"] = (
        audit_trace_words_against_domains(traces, domains)
    )
    del domains
    return traces, snapshots, d24


def census_chunk(args, policy, lease_slot):
    wall_started = time.monotonic()
    traces, snapshots, d24 = load_traces(args)
    checkpoint = load_or_initialize_checkpoint(
        args.checkpoint, snapshots, traces
    )
    projection_started = time.monotonic()
    deadline = projection_started + args.max_seconds
    work = 0
    advance_cursor(checkpoint, traces)
    start_cursor = (
        checkpoint["next_trace_index"], checkpoint["next_scheduler_rank"]
    )
    new_records = []
    while checkpoint["status"] != "complete":
        if work >= args.max_occurrences or time.monotonic() >= deadline:
            break
        trace_id = TRACE_ORDER[checkpoint["next_trace_index"]]
        trace = traces[trace_id]
        rank = checkpoint["next_scheduler_rank"]
        new_records.append(make_occurrence_record(trace, rank, d24))
        checkpoint["next_scheduler_rank"] += 1
        work += 1
        advance_cursor(checkpoint, traces)
    end_cursor = (
        checkpoint["next_trace_index"], checkpoint["next_scheduler_rank"]
    )
    projection_finished = time.monotonic()
    if checkpoint["status"] == "complete":
        stop_reason = "complete"
    elif work >= args.max_occurrences:
        stop_reason = "occurrence-cap"
    else:
        stop_reason = "time-cap"
    append_record_chunk(
        checkpoint, args.checkpoint, new_records, start_cursor, end_cursor
    )
    if checkpoint["status"] == "complete" and checkpoint[
        "completed_occurrences"
    ] != (
        EXPECTED_OCCURRENCES
    ):
        raise AssertionError(
            "completed near-state census occurrence extent drift",
            checkpoint["completed_occurrences"],
        )
    checkpoint["last_run"] = {
        "occurrences": work,
        "projection_elapsed_seconds": round(
            projection_finished - projection_started, 6
        ),
        "pre_checkpoint_save_wall_elapsed_seconds": round(
            time.monotonic() - wall_started, 6
        ),
        "maximum_resident_bytes": matched.maximum_resident_bytes(),
        "resource_policy": policy,
        "cooperative_lease_slot": lease_slot,
        "stop_reason": stop_reason,
    }
    save_checkpoint(args.checkpoint, checkpoint)
    validate_checkpoint(checkpoint, snapshots, traces, args.checkpoint)
    return {
        "status": checkpoint["status"],
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_sha256": file_sha256(args.checkpoint),
        "checkpoint_payload_sha256": checkpoint[
            "checkpoint_payload_sha256"
        ],
        "completed_occurrences": checkpoint["completed_occurrences"],
        "expected_occurrences": EXPECTED_OCCURRENCES,
        "occurrences_this_run": work,
        "immutable_record_chunks": len(checkpoint["record_chunks"]),
        "record_chunk_chain_sha256": checkpoint[
            "record_chunk_chain_sha256"
        ],
        "poison_masks_consulted": False,
    }


def load_complete_checkpoint(path):
    path = Path(path).resolve()
    before = path.stat()
    encoded = path.read_bytes()
    digest = hashlib.sha256(encoded).hexdigest()
    after = path.stat()
    identity = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, key) for key in identity) != tuple(
        getattr(after, key) for key in identity
    ):
        raise RuntimeError("checkpoint changed while being read", str(path))
    checkpoint = json.loads(encoded)
    internal = checkpoint.get("checkpoint_payload_sha256")
    if internal != stable_hash(checkpoint_payload(checkpoint)):
        raise AssertionError("near-state checkpoint payload drift")
    if checkpoint.get("status") != "complete":
        raise RuntimeError("near-state checkpoint is not complete")
    static = {
        "schema_version": SCHEMA_VERSION,
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "poison_masks_consulted": False,
        "trace_order": list(TRACE_ORDER),
        "completed_occurrences": EXPECTED_OCCURRENCES,
    }
    if any(checkpoint.get(key) != value for key, value in static.items()):
        raise AssertionError("complete near-state checkpoint identity drift")
    snapshot = {
        "path": str(path),
        "sha256": digest,
        "bytes": after.st_size,
        "payload_sha256": internal,
        "record_chunks": len(checkpoint.get("record_chunks", [])),
        "record_chunk_chain_sha256": checkpoint.get(
            "record_chunk_chain_sha256"
        ),
    }
    return checkpoint, snapshot


def validate_record_prefix(
    records, traces, next_trace_index, next_rank, require_complete=False,
):
    expected = []
    for trace_index, trace_id in enumerate(TRACE_ORDER):
        trace = traces[trace_id]
        for rank in range(2, len(trace["schedule"]) - 2):
            expected.append((trace_index, trace_id, rank, trace["schedule"][rank]))
    if len(records) > len(expected):
        raise AssertionError("near-state record stream has trailing records")
    for cursor, (record, item) in enumerate(zip(records, expected)):
        _trace_index, trace_id, rank, gap = item
        expected_id = stable_hash({
            "schema": "projection-independent-concrete-occurrence-v1",
            "trace_id": trace_id,
            "scheduler_rank": rank,
            "gap": gap,
        })
        if (
            record.get("occurrence_id") != expected_id
            or record.get("trace_id") != trace_id
            or record.get("scheduler_rank") != rank
            or record.get("split") != trace_split(trace_id)
            or record.get("source_joinable_as_source") is not True
            or record.get("poison_masks_consulted") is not False
        ):
            raise AssertionError(
                "near-state record stream locator drift", cursor
            )
        for phase in ("source", "actual_successor"):
            projected = record.get(phase, {})
            if (
                set(projected.get("keys", {})) != set(ABLATIONS)
                or set(projected.get("state_keys", {})) != set(ABLATIONS)
                or set(projected.get("mandatory_floor_keys", {}))
                != set(PROJECTION_SCHEMA["mandatory_floor_keys"])
                or projected.get("full_factor_committed_atomically") is not True
            ):
                raise AssertionError(
                    "near-state projected record schema drift", cursor
                )
    if len(records) == len(expected):
        expected_cursor = (len(TRACE_ORDER), 2)
    else:
        expected_cursor = (expected[len(records)][0], expected[len(records)][2])
    if (next_trace_index, next_rank) != expected_cursor:
        raise AssertionError(
            "near-state checkpoint cursor does not follow its record prefix",
            (next_trace_index, next_rank), expected_cursor,
        )
    if require_complete and len(records) != len(expected):
        raise AssertionError("near-state complete checkpoint ends early")


def class_eligible(records):
    roots = {record["ancestry_root"] for record in records}
    levels = {record["level"] for record in records}
    families = {record["family"] for record in records}
    domain_pairs = {tuple(record["domain_step_pair"]) for record in records}
    return (
        len(records) >= MIN_CLASS_OCCURRENCES
        and len(roots) >= 2
        and (len(levels) >= 2 or len(families) >= 2)
        and len(domain_pairs) == 1
        and not any(record["boundary"] for record in records)
    )


def holdout_report(groups, split):
    total = 0
    seen = 0
    source_classes_total = 0
    source_classes_seen = 0
    agreements = 0
    next_action_agreements = 0
    mismatches = []
    next_action_mismatches = []
    unseen = []
    unseen_source_keys = []
    for source_key, records in sorted(groups.items()):
        discovery = [record for record in records if record["split"] == "discovery"]
        holdout = [record for record in records if record["split"] == split]
        total += len(holdout)
        if not holdout:
            continue
        source_classes_total += 1
        if not discovery:
            if len(unseen_source_keys) < MAX_REPORTED_WITNESSES:
                unseen_source_keys.append(source_key)
            remaining = MAX_REPORTED_WITNESSES - len(unseen)
            if remaining > 0:
                unseen.extend(
                    record["occurrence_id"] for record in holdout[:remaining]
                )
            continue
        source_classes_seen += 1
        discovery_targets = {
            record["_target_key"] for record in discovery
        }
        discovery_next_actions = {
            record["_next_action_key"] for record in discovery
        }
        for record in holdout:
            seen += 1
            if len(discovery_targets) == 1 and record[
                "_target_key"
            ] in discovery_targets:
                agreements += 1
            elif len(mismatches) < MAX_REPORTED_WITNESSES:
                mismatches.append({
                    "source_key": source_key,
                    "occurrence_id": record["occurrence_id"],
                    "discovery_complete_successor_envelope_keys": sorted(
                        discovery_targets
                    ),
                    "holdout_complete_successor_envelope_key": record[
                        "_target_key"
                    ],
                })
            if (
                len(discovery_next_actions) == 1
                and record["_next_action_key"] in discovery_next_actions
            ):
                next_action_agreements += 1
            elif len(next_action_mismatches) < MAX_REPORTED_WITNESSES:
                next_action_mismatches.append({
                    "source_key": source_key,
                    "occurrence_id": record["occurrence_id"],
                    "discovery_next_action_keys": sorted(
                        discovery_next_actions
                    ),
                    "holdout_next_action_key": record["_next_action_key"],
                })
    return {
        "split": split,
        "source_class_key_semantics": (
            "projected source state plus exact current action"
        ),
        "total_occurrences": total,
        "occurrences_with_source_class_seen_in_discovery": seen,
        "occurrence_coverage_failures": total - seen,
        "source_classes_total": source_classes_total,
        "source_classes_seen_in_discovery": source_classes_seen,
        "source_class_coverage_failures": (
            source_classes_total - source_classes_seen
        ),
        "complete_source_class_coverage": (
            source_classes_total == source_classes_seen
        ),
        "strict_complete_successor_envelope_agreements": agreements,
        "strict_complete_successor_envelope_mismatches": seen - agreements,
        "successor_action_component_agreements": next_action_agreements,
        "successor_action_component_mismatches": seen - next_action_agreements,
        "coverage_failure_source_keys_first": unseen_source_keys,
        "coverage_failure_occurrence_ids_first": unseen[
            :MAX_REPORTED_WITNESSES
        ],
        "mismatch_witnesses_first": mismatches,
        "successor_action_component_mismatch_witnesses_first": (
            next_action_mismatches
        ),
    }


def complete_successor_envelope_key(record, name):
    successor = record["actual_successor"]
    payload = {
        "schema": "complete-recorded-successor-envelope-v1",
        "ablation": name,
        "projected_successor_state_action_sha256": successor["keys"][name],
        "projected_successor_state_without_action_sha256": successor[
            "state_keys"
        ][name],
        "exact_recorded_policy_action_sha256": successor[
            "exact_action_sha256"
        ],
        "natural_boundary": record["actual_successor_boundary"],
        "joinable_as_recorded_source": record[
            "actual_successor_joinable_as_source"
        ],
    }
    return stable_hash(payload)


def policy_functionality_report(
    records, name, phases, include_boundary_joinability,
):
    groups = defaultdict(list)
    for record in records:
        for phase in phases:
            projected = record[phase]
            boundary = (
                record["boundary"] if phase == "source"
                else record["actual_successor_boundary"]
            )
            joinable = (
                record["source_joinable_as_source"] if phase == "source"
                else record["actual_successor_joinable_as_source"]
            )
            projected_state_key = projected["state_keys"][name]
            if include_boundary_joinability:
                policy_state_key = stable_hash({
                    "schema": "complete-recorded-state-without-action-v1",
                    "ablation": name,
                    "projected_state_without_action_sha256": (
                        projected_state_key
                    ),
                    "natural_boundary": boundary,
                    "joinable_as_recorded_source": joinable,
                })
            else:
                policy_state_key = projected_state_key
            groups[policy_state_key].append({
                "occurrence_id": record["occurrence_id"],
                "phase": phase,
                "projected_state_without_action_sha256": projected_state_key,
                "exact_policy_action_sha256": projected[
                    "exact_action_sha256"
                ],
                "natural_boundary": boundary,
                "joinable_as_recorded_source": joinable,
            })
    failures = []
    failure_count = 0
    for state_key, observations in sorted(groups.items()):
        actions = {
            observation["exact_policy_action_sha256"]
            for observation in observations
        }
        if len(actions) > 1:
            failure_count += 1
            if len(failures) < MAX_REPORTED_WITNESSES:
                failures.append({
                    "policy_state_without_action_key": state_key,
                    "exact_policy_action_sha256s": sorted(actions),
                    "observations_first": observations[:8],
                })
    return {
        "phases": list(phases),
        "state_key_includes_boundary_and_joinability": (
            include_boundary_joinability
        ),
        "state_key_excludes_policy_action": True,
        "observations": sum(len(group) for group in groups.values()),
        "projected_state_classes_without_action": len(groups),
        "nonfunctional_state_classes": failure_count,
        "recorded_policy_is_a_function_of_state_without_action": (
            failure_count == 0
        ),
        "nonfunctionality_witnesses_first": failures,
    }


def analyze_ablation(records, name):
    groups = defaultdict(list)
    for source in records:
        record = {
            key: source[key] for key in (
                "occurrence_id", "trace_id", "family", "level", "split",
                "scheduler_rank", "ancestry_root", "boundary",
                "actual_successor_boundary",
                "actual_successor_joinable_as_source", "domain_step_pair",
            )
        }
        record["_target_key"] = complete_successor_envelope_key(source, name)
        record["_next_action_key"] = source["actual_successor"][
            "exact_action_sha256"
        ]
        record["_floors"] = source["source"]["mandatory_floor_keys"]
        groups[source["source"]["keys"][name]].append(record)
    multiplicities = Counter(len(group) for group in groups.values())
    noncongruent = []
    discovery_noncongruent = []
    next_action_noncongruent = []
    jointly_qualifying = []
    jointly_qualifying_source_keys = []
    jointly_qualifying_count = 0
    eligible = 0
    repeated_occurrences = 0
    floor_violations = []
    for source_key, group in sorted(groups.items()):
        if len(group) >= 2:
            repeated_occurrences += len(group)
        if class_eligible(group):
            eligible += 1
        targets = {record["_target_key"] for record in group}
        if len(targets) > 1 and len(noncongruent) < MAX_REPORTED_WITNESSES:
            noncongruent.append({
                "source_key": source_key,
                "target_keys": sorted(targets),
                "occurrence_ids": [
                    record["occurrence_id"] for record in group[:8]
                ],
            })
        discovery = [record for record in group if record["split"] == "discovery"]
        discovery_targets = {record["_target_key"] for record in discovery}
        if (
            len(discovery_targets) > 1
            and len(discovery_noncongruent) < MAX_REPORTED_WITNESSES
        ):
            discovery_noncongruent.append({
                "source_key": source_key,
                "target_keys": sorted(discovery_targets),
                "occurrence_ids": [
                    record["occurrence_id"] for record in discovery[:8]
                ],
            })
        next_actions = {record["_next_action_key"] for record in group}
        if (
            len(next_actions) > 1
            and len(next_action_noncongruent) < MAX_REPORTED_WITNESSES
        ):
            next_action_noncongruent.append({
                "source_key": source_key,
                "next_action_keys": sorted(next_actions),
                "occurrence_ids": [
                    record["occurrence_id"] for record in group[:8]
                ],
            })
        if name == "A4":
            floor_tuples = {
                tuple(sorted(record["_floors"].items())) for record in group
            }
            if len(floor_tuples) > 1:
                floor_violations.append({
                    "source_key": source_key,
                    "floor_variants": len(floor_tuples),
                })
            horizon_members = [
                record for record in group
                if record["split"] == "horizon-holdout"
            ]
            separate_family_members = [
                record for record in group
                if record["split"] == "separate-family-holdout"
            ]
            roots = {record["ancestry_root"] for record in group}
            domain_pairs = {
                tuple(record["domain_step_pair"]) for record in group
            }
            next_actions = {
                record["_next_action_key"] for record in group
            }
            requirements = {
                "at_least_four_members": len(group) >= 4,
                "at_least_two_immediate_roots": len(roots) >= 2,
                "one_domain_step_pair": len(domain_pairs) == 1,
                "no_source_natural_boundary": not any(
                    record["boundary"] for record in group
                ),
                "no_successor_natural_boundary": not any(
                    record["actual_successor_boundary"] for record in group
                ),
                "every_successor_joinable_as_source": all(
                    record["actual_successor_joinable_as_source"]
                    for record in group
                ),
                "at_least_two_discovery_members": len(discovery) >= 2,
                "has_horizon_holdout_member": bool(horizon_members),
                "has_separate_family_holdout_member": bool(
                    separate_family_members
                ),
                "one_complete_successor_envelope": len(targets) == 1,
                "one_successor_action_component": len(next_actions) == 1,
                "mandatory_floor_keys_agree": len(floor_tuples) == 1,
            }
            if all(requirements.values()):
                jointly_qualifying_count += 1
                jointly_qualifying_source_keys.append(source_key)
                if len(jointly_qualifying) < MAX_REPORTED_WITNESSES:
                    jointly_qualifying.append({
                        "source_key": source_key,
                        "members": len(group),
                        "discovery_members": len(discovery),
                        "horizon_holdout_members": len(horizon_members),
                        "separate_family_holdout_members": len(
                            separate_family_members
                        ),
                        "immediate_roots": len(roots),
                        "requirements": requirements,
                    })
    if floor_violations:
        raise AssertionError(
            "A4 merged mandatory-floor keys", floor_violations[:3]
        )
    horizon = holdout_report(groups, "horizon-holdout")
    separate_family = holdout_report(groups, "separate-family-holdout")
    combined_policy_functionality = policy_functionality_report(
        records, name, ("source", "actual_successor"), True
    )
    successor_policy_functionality = policy_functionality_report(
        records, name, ("actual_successor",), True
    )
    projection_only_policy_functionality = policy_functionality_report(
        records, name, ("source", "actual_successor"), False
    )
    return {
        "ablation": name,
        "classes": len(groups),
        "multiplicity_histogram": [
            {"occurrences_per_class": size, "classes": count}
            for size, count in sorted(multiplicities.items())
        ],
        "repeated_occurrences": repeated_occurrences,
        "eligible_classes": eligible,
        "maximum_class_size": max(multiplicities) if multiplicities else 0,
        "strict_recorded_complete_successor_envelope_noncongruent_classes": sum(
            len({record["_target_key"] for record in group}) > 1
            for group in groups.values()
        ),
        "strict_discovery_complete_successor_envelope_noncongruent_classes": sum(
            len({
                record["_target_key"] for record in group
                if record["split"] == "discovery"
            }) > 1
            for group in groups.values()
        ),
        "source_action_class_successor_action_noncongruent_classes": sum(
            len({record["_next_action_key"] for record in group}) > 1
            for group in groups.values()
        ),
        "complete_successor_noncongruence_witnesses_first": noncongruent,
        "discovery_complete_successor_noncongruence_witnesses_first": (
            discovery_noncongruent
        ),
        "source_action_class_successor_action_noncongruence_witnesses_first": (
            next_action_noncongruent
        ),
        "horizon_holdout": horizon,
        "separate_family_holdout": separate_family,
        "combined_source_successor_policy_functionality": (
            combined_policy_functionality
        ),
        "successor_policy_functionality": successor_policy_functionality,
        "projection_only_policy_functionality_diagnostic": (
            projection_only_policy_functionality
        ),
        "mandatory_floor_refinement_violations": len(floor_violations),
        "jointly_qualifying_A4_classes": (
            jointly_qualifying_count if name == "A4" else None
        ),
        "jointly_qualifying_A4_classes_first": (
            jointly_qualifying if name == "A4" else []
        ),
        "jointly_qualifying_A4_source_key_set_sha256": (
            stable_hash(sorted(jointly_qualifying_source_keys))
            if name == "A4" else None
        ),
        "jointly_qualifying_A4_source_keys": (
            sorted(jointly_qualifying_source_keys) if name == "A4" else []
        ),
    }


def coarsening_reports(records):
    reports = []
    for left, right in zip(ABLATIONS, ABLATIONS[1:]):
        mapping = defaultdict(set)
        for record in records:
            mapping[record["source"]["keys"][left]].add(
                record["source"]["keys"][right]
            )
        violations = [
            key for key, targets in mapping.items() if len(targets) != 1
        ]
        if violations:
            raise AssertionError(
                "declared cumulative ablation is not a coarsening",
                left, right, violations[:3],
            )
        reports.append({
            "finer": left,
            "coarser": right,
            "finer_to_coarser_is_a_function": True,
            "mapping_sha256": stable_hash([
                [key, next(iter(mapping[key]))] for key in sorted(mapping)
            ]),
        })
    return reports


def floor_reports(records):
    names = PROJECTION_SCHEMA["mandatory_floor_keys"]
    reports = {}
    for name in names:
        values = {record["source"]["mandatory_floor_keys"][name] for record in records}
        reports[name] = {
            "classes": len(values),
            "stream_sha256": stable_hash([
                [record["occurrence_id"],
                 record["source"]["mandatory_floor_keys"][name]]
                for record in records
            ]),
        }
    return reports


def recorded_panel_qualification(a4):
    horizon = a4["horizon_holdout"]
    separate_family = a4["separate_family_holdout"]
    combined_policy = a4[
        "combined_source_successor_policy_functionality"
    ]
    successor_policy = a4["successor_policy_functionality"]
    gates = {
        "A4_has_jointly_qualifying_class": (
            a4["jointly_qualifying_A4_classes"] > 0
        ),
        "A4_strict_discovery_complete_successor_right_congruence": (
            a4["strict_discovery_complete_successor_envelope_noncongruent_classes"]
            == 0
        ),
        "A4_strict_all_recorded_complete_successor_right_congruence": (
            a4["strict_recorded_complete_successor_envelope_noncongruent_classes"]
            == 0
        ),
        "A4_recorded_policy_functional_on_all_observed_states": (
            combined_policy[
                "recorded_policy_is_a_function_of_state_without_action"
            ]
        ),
        "A4_recorded_policy_functional_on_observed_successor_states": (
            successor_policy[
                "recorded_policy_is_a_function_of_state_without_action"
            ]
        ),
        "horizon_holdout_has_discovery_covered_source_class": (
            horizon["source_classes_seen_in_discovery"] > 0
        ),
        "horizon_holdout_covered_classes_strict_complete_successor_agreement": (
            horizon[
                "strict_complete_successor_envelope_mismatches"
            ] == 0
        ),
        "separate_family_holdout_has_discovery_covered_source_class": (
            separate_family["source_classes_seen_in_discovery"] > 0
        ),
        "separate_family_holdout_covered_classes_strict_complete_successor_agreement": (
            separate_family[
                "strict_complete_successor_envelope_mismatches"
            ] == 0
        ),
        "mandatory_floor_refinement": (
            a4["mandatory_floor_refinement_violations"] == 0
        ),
    }
    qualified = all(gates.values())
    candidate_keys = a4["jointly_qualifying_A4_source_keys"]
    if len(candidate_keys) != a4["jointly_qualifying_A4_classes"]:
        raise AssertionError("jointly qualifying A4 class key extent drift")
    coverage = {
        "horizon_source_class_coverage_failures": horizon[
            "source_class_coverage_failures"
        ],
        "separate_family_source_class_coverage_failures": separate_family[
            "source_class_coverage_failures"
        ],
        "horizon_complete_source_class_coverage": horizon[
            "complete_source_class_coverage"
        ],
        "separate_family_complete_source_class_coverage": separate_family[
            "complete_source_class_coverage"
        ],
    }
    coverage["all_declared_holdout_source_classes_covered"] = (
        coverage["horizon_complete_source_class_coverage"]
        and coverage["separate_family_complete_source_class_coverage"]
    )
    return {
        "gates": gates,
        "recorded_joint_panel_poison_followup_authorized": qualified,
        "qualifying_projection": "A4",
        "other_ablation_may_qualify_a_recorded_panel": False,
        "authorized_recorded_A4_source_class_keys": (
            candidate_keys if qualified else []
        ),
        "authorized_recorded_A4_source_class_count": (
            len(candidate_keys) if qualified else 0
        ),
        "authorized_recorded_A4_source_class_key_set_sha256": (
            stable_hash(candidate_keys) if qualified else stable_hash([])
        ),
        "holdout_coverage": coverage,
        "unseen_holdout_source_classes_are_coverage_failures": True,
        "broader_source_universe_poison_followup_authorized": False,
        "scope": (
            "qualification applies only to the exact listed jointly qualifying "
            "recorded A4 source classes; it does not cover unseen L8 or primary-"
            "L6 source classes and does not establish universal coverage, far-"
            "tail contraction, availability, or a safety GFP"
        ),
    }


def finalize(args, policy, lease_slot):
    traces, snapshots, d24 = load_traces(args)
    checkpoint, snapshot = load_complete_checkpoint(args.checkpoint)
    validate_checkpoint(checkpoint, snapshots, traces, args.checkpoint)
    records, chunk_snapshots = load_record_chunks(checkpoint)
    validate_record_prefix(
        records,
        traces,
        checkpoint["next_trace_index"],
        checkpoint["next_scheduler_rank"],
        require_complete=True,
    )
    atomic_record_stream_sha256 = stable_hash(records)
    snapshot["record_chunk_snapshots"] = chunk_snapshots
    snapshot["atomic_record_stream_sha256"] = (
        atomic_record_stream_sha256
    )
    for index, record in enumerate(records):
        expected = make_occurrence_record(
            traces[record["trace_id"]], record["scheduler_rank"], d24
        )
        if expected != record:
            raise AssertionError(
                "compact projection record differs from pinned replay", index
            )
    if len({record["occurrence_id"] for record in records}) != len(records):
        raise AssertionError("near-state occurrence IDs repeat")
    if any(record.get("poison_masks_consulted") is not False for record in records):
        raise AssertionError("near-state record consulted poison")
    ablations = [analyze_ablation(records, name) for name in ABLATIONS]
    by_name = {record["ablation"]: record for record in ablations}
    if by_name["A0"]["classes"] != EXPECTED_A0_CLASSES:
        raise AssertionError(
            "A0 no longer reproduces the exact singleton census",
            by_name["A0"]["classes"],
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete poison-blind near-state ablation finite computation",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256": EXPECTED_MATCHED_CHECKER_SHA256,
        "projection_schema": PROJECTION_SCHEMA,
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition": CANDIDATE_STREAM_DEFINITION,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "poison_masks_consulted": False,
        "occurrences": len(records),
        "atomic_record_stream_sha256": atomic_record_stream_sha256,
        "checkpoint": snapshot,
        "input_snapshots": checkpoint["input_snapshots"],
        "ablations": ablations,
        "cumulative_coarsening_reports": coarsening_reports(records),
        "mandatory_floor_reports": floor_reports(records),
        "recorded_panel_qualification": recorded_panel_qualification(
            by_name["A4"]
        ),
        "soundness_scope": {
            "whole_realized_factors_committed_and_replayable_atomically": True,
            "cartesian_address_recombination": False,
            "future_connector_choices_exposed_at_source": False,
            "actual_action_retained_exactly": True,
            "actual_successor_replayed_with_same_projection": True,
            "every_compact_projection_record_replayed_at_finalize": True,
            "complete_successor_envelope_includes_action_boundary_joinability": True,
            "policy_functionality_tested_by_complete_state_context_without_action": True,
            "projection_only_policy_functionality_also_reported": True,
            "holdout_partition_frozen_before_counts": True,
            "source_factor_may_omit_the_r_plus_one_owner_block": True,
            "strict_congruence_is_a_finite_trace_rejection_gate_only": True,
            "unseen_holdout_source_classes_are_coverage_failures": True,
            "no_broader_source_coverage_is_authorized": True,
            "projected_key_equality_assumption": (
                "SHA-256 collision resistance; canonical projected objects "
                "are not serialized in the compact checkpoint"
            ),
            "primary_holdout_is_a_separate_family_not_independent_ancestry": True,
        },
        "not_proved": [
            "universal right-congruence beyond the pinned traces",
            "coverage of unseen L8 or primary-L6 source classes",
            "coverage of alternate connector histories",
            "positive connector availability",
            "a uniform far-shell transfer or rank",
            "a greatest-fixed-point safety policy",
            "an unconditional Erdos #193 theorem",
        ],
        "resource_policy": policy,
        "cooperative_lease_slot": lease_slot,
    }
    result["payload_sha256"] = stable_hash(result)
    immutable_json_dump(result, args.output)
    return {
        "status": result["status"],
        "output": str(Path(args.output).resolve()),
        "output_sha256": file_sha256(args.output),
        "payload_sha256": result["payload_sha256"],
        "recorded_joint_panel_poison_followup_authorized": result[
            "recorded_panel_qualification"
        ][
            "recorded_joint_panel_poison_followup_authorized"
        ],
    }


def estimate(ancestry_schema_self_check):
    return {
        "status": "prepared poison-blind near-state ablation checker",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "matched_checker_sha256_expected": EXPECTED_MATCHED_CHECKER_SHA256,
        "matched_checker_sha256_observed": file_sha256(matched.__file__),
        "projection_schema_sha256": PROJECTION_SCHEMA_SHA256,
        "holdout_partition_sha256": HOLDOUT_PARTITION_SHA256,
        "candidate_stream_definition_sha256": (
            CANDIDATE_STREAM_DEFINITION_SHA256
        ),
        "expected_occurrences": EXPECTED_OCCURRENCES,
        "ablations": list(ABLATIONS),
        "only_recorded_panel_qualifying_projection": "A4",
        "synthetic_ancestry_schema_self_check": ancestry_schema_self_check,
        "qualification_scope": (
            "exact jointly qualifying recorded A4 source classes only; unseen "
            "holdout source classes are reported as coverage failures"
        ),
        "resource_policy": {
            "processes": 1,
            "threads": 1,
            "required_minimum_nice": 15,
            "maximum_projection_seconds_per_census_run": MAX_SECONDS,
            "maximum_occurrences_per_census_run": (
                MAX_OCCURRENCES_PER_RUN
            ),
            "checkpoint_validation_and_atomic_save_outside_time_cap": True,
            "resumable_checkpoint": True,
            "checkpoint_format": (
                "small atomic manifest plus append-only immutable record chunks; "
                "prior chunks are fully verified once at finalize"
            ),
            "cooperative_core_limit": 2,
        },
        "large_inputs_opened": False,
        "poison_masks_consulted": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "census", "finalize"))
    parser.add_argument(
        "--primary-source", default=str(matched.DEFAULT_PRIMARY_SOURCE)
    )
    parser.add_argument(
        "--primary-terminal", default=str(matched.DEFAULT_PRIMARY_TERMINAL)
    )
    parser.add_argument(
        "--primary-parent-source",
        default=str(matched.DEFAULT_PRIMARY_PARENT_SOURCE),
    )
    parser.add_argument(
        "--primary-parent-terminal",
        default=str(matched.DEFAULT_PRIMARY_PARENT_TERMINAL),
    )
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=float, default=MAX_SECONDS)
    parser.add_argument(
        "--max-occurrences", type=int, default=MAX_OCCURRENCES_PER_RUN
    )
    args = parser.parse_args()
    if args.mode != "estimate" and Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run heavy modes from the repository root: cd {ROOT}")
    if not 0 < args.max_seconds <= MAX_SECONDS:
        raise ValueError("max-seconds outside allowed range")
    if not 1 <= args.max_occurrences <= MAX_OCCURRENCES_PER_RUN:
        raise ValueError("max-occurrences outside allowed range")
    ancestry_schema_self_check = synthetic_ancestry_schema_self_check()
    assert_checker_unchanged()
    policy = enforce_resources(args.mode)
    lease = None
    lease_slot = None
    if args.mode in {"census", "finalize"}:
        lease, lease_slot = matched.acquire_core_lease()
    try:
        if args.mode == "estimate":
            result = estimate(ancestry_schema_self_check)
        elif args.mode == "census":
            result = census_chunk(args, policy, lease_slot)
        else:
            result = finalize(args, policy, lease_slot)
        assert_checker_unchanged()
        print(json.dumps(result, sort_keys=True, indent=2))
    finally:
        if lease is not None:
            import fcntl
            fcntl.flock(lease.fileno(), fcntl.LOCK_UN)
            lease.close()


if __name__ == "__main__":
    main()
