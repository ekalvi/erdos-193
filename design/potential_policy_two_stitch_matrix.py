#!/usr/bin/env python3
"""Exact correlated 8-by-8 lookahead matrix for the first two L5 stitches.

The common height-two potential retains eight words for parent step 20.  This
checker tries each retained word at scheduled gap 0 against all 2,458 anchors.
When that first action is projection-clean and exactly legal, its proper
interiors are committed to a fresh row-specific state and all eight retained
words are tested at scheduled gap 2.  Rows never share committed interiors.

Every zero entry records its exact projection and/or global-collinearity
witness.  The experiment is finite and pinned; it tests two-stitch lookahead,
not closure of a policy over the full construction.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import time
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import potential_policy_chronological_rescue as rescue
from design.fixed_policy_chronological_replay import first_projection_conflict


DEFAULT_OUTPUT = Path("/tmp/potential-policy-two-stitch-matrix.json")
EXPECTED_RESCUE_CHECKER_SHA256 = (
    "2b1bde9e846211cd53f75b6300c540a99b92d25b706c174c137f32c9cbf19ebc"
)
EXPECTED_RESCUE_SUMMARY_SHA256 = (
    "8f975dc8dad64f70a1a7b759a25e2cfaccd6e0261079bbd0235332d6b8c99582"
)
EXPECTED_ORDINALS = (1, 3513, 3530, 3585, 5479, 12492, 17775, 46804)
EXPECTED_FIRST_GAPS = (0, 2)


def verify_local_inputs():
    observed = {
        "rescue_checker": rescue.file_sha256(
            ROOT / "design" / "potential_policy_chronological_rescue.py"
        ),
        "rescue_summary": rescue.file_sha256(
            ROOT / "design" / "potential-policy-chronological-rescue-summary.json"
        ),
    }
    expected = {
        "rescue_checker": EXPECTED_RESCUE_CHECKER_SHA256,
        "rescue_summary": EXPECTED_RESCUE_SUMMARY_SHA256,
    }
    if observed != expected:
        raise AssertionError("two-stitch local input drift", expected, observed)
    return observed


def accepted_step_words(cache, block, bitset, potential_record):
    records = []
    cursor = block["start"]
    for ordinal in range(1, block["words"] + 1):
        record_offset = cursor
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if end > block["end"]:
            raise AssertionError("step-20 compact-cache boundary drift")
        if rescue.potential_accepts(bitset, potential_record, ordinal):
            records.append({
                "ordinal_1_based": ordinal,
                "cache_record_offset": record_offset,
                "word": tuple(cache[cursor:end]),
            })
        cursor = end
    if cursor != block["end"]:
        raise AssertionError("step-20 compact-cache end drift")
    if tuple(record["ordinal_1_based"] for record in records) != (
        EXPECTED_ORDINALS
    ):
        raise AssertionError("step-20 accepted ordinal drift", records)
    if len(records) != potential_record["set_bits"]:
        raise AssertionError("step-20 potential population drift")
    return tuple(records)


def evaluate(start, target, word, store, yz_counts):
    interiors = tuple(rescue.word_interiors(start, word))
    endpoint_value = rescue.endpoint(start, word)
    endpoint_witness = None
    if endpoint_value != target:
        endpoint_witness = {
            "computed": list(endpoint_value),
            "required": list(target),
        }
    fibre_owner = {}
    for index, point in enumerate(store.pts):
        fibre_owner.setdefault(point[1:], index)
    projection_witness = first_projection_conflict(
        interiors, store.pts, fibre_owner
    )
    fast_legal = rescue.word_legal_fast(
        start, word, store, {}, rescue.MENU
    )
    if fast_legal:
        if not rescue.word_legal(
            start, word, store.pts, store.pset, {}
        ):
            raise AssertionError("fast/reference matrix legality disagreement")
        exact_rejection = None
    else:
        exact_rejection = rescue.exact_legality_rejection(interiors, store)
    passed = (
        endpoint_witness is None
        and projection_witness is None
        and exact_rejection is None
    )
    return {
        "passed": passed,
        "proper_interiors": [list(point) for point in interiors],
        "endpoint_passed": endpoint_witness is None,
        "endpoint_witness": endpoint_witness,
        "projection_freshness_passed": projection_witness is None,
        "projection_witness": projection_witness,
        "exact_global_legality_passed": exact_rejection is None,
        "exact_legality_rejection": exact_rejection,
    }, interiors


def matrix_run(args):
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = rescue.file_sha256(checker_path)
    policy = rescue.resource_policy()
    local_inputs = verify_local_inputs()
    external_inputs = rescue.verify_inputs(
        args.metadata, args.cache, args.potential, args.bitsets
    )
    _metadata, blocks = rescue.load_metadata(args.metadata)
    parent_word, anchors, schedule = rescue.load_l5_state()
    if tuple(schedule[:2]) != EXPECTED_FIRST_GAPS:
        raise AssertionError("first two scheduled gaps drift", schedule[:2])
    if parent_word[0] != 20 or parent_word[2] != 20:
        raise AssertionError("first two scheduled parent steps drift")
    potential, sidecar = rescue.load_potential_result(args.potential)

    with Path(args.cache).open("rb") as cache_handle, Path(args.bitsets).open(
        "rb"
    ) as bitset_handle:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        bitset = mmap.mmap(bitset_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            potential_records = rescue.parse_bitsets(
                bitset,
                sidecar,
                blocks,
                potential["potential_compatible_filter"]["census"],
            )
            actions = accepted_step_words(
                cache, blocks[20], bitset, potential_records[20]
            )
            rows = []
            legal_pairs = []
            initial_yz = Counter(point[1:] for point in anchors)
            for first_index, first_action in enumerate(actions):
                first_store = rescue.Store(anchors)
                first_yz = copy.copy(initial_yz)
                first_evaluation, first_interiors = evaluate(
                    anchors[0], anchors[1], first_action["word"],
                    first_store, first_yz,
                )
                row = {
                    "first_action_index_0_based": first_index,
                    "first_ordinal_1_based": first_action["ordinal_1_based"],
                    "first_word": list(first_action["word"]),
                    "first_action_evaluation": first_evaluation,
                    "first_action_committed": first_evaluation["passed"],
                    "response_mask_lsb_is_first_ordinal": 0,
                    "legal_response_count": 0,
                    "legal_response_ordinals_1_based": [],
                    "responses": [],
                }
                if first_evaluation["passed"]:
                    rescue.apply_selected(
                        first_interiors, first_store, first_yz
                    )
                    for second_index, second_action in enumerate(actions):
                        evaluation, _interiors = evaluate(
                            anchors[2], anchors[3], second_action["word"],
                            first_store, first_yz,
                        )
                        response = {
                            "second_action_index_0_based": second_index,
                            "second_ordinal_1_based": second_action[
                                "ordinal_1_based"
                            ],
                            "second_word": list(second_action["word"]),
                            **evaluation,
                        }
                        row["responses"].append(response)
                        if evaluation["passed"]:
                            row["response_mask_lsb_is_first_ordinal"] |= (
                                1 << second_index
                            )
                            row["legal_response_ordinals_1_based"].append(
                                second_action["ordinal_1_based"]
                            )
                            legal_pairs.append([
                                first_action["ordinal_1_based"],
                                second_action["ordinal_1_based"],
                            ])
                    row["legal_response_count"] = len(
                        row["legal_response_ordinals_1_based"]
                    )
                rows.append(row)
        finally:
            bitset.close()
            cache.close()

    if rescue.file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("two-stitch checker changed during exact matrix")
    elapsed = time.monotonic() - started
    resident = rescue.maximum_resident_bytes()
    if elapsed > rescue.MAX_SECONDS or resident > rescue.MAX_RESIDENT_BYTES:
        raise RuntimeError("two-stitch resource bound exceeded", elapsed, resident)
    valid_first_actions = [
        row["first_ordinal_1_based"]
        for row in rows
        if row["first_action_committed"]
    ]
    responding_first_actions = [
        row["first_ordinal_1_based"]
        for row in rows
        if row["legal_response_count"]
    ]
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact pinned two-stitch common-potential safety matrix",
        "checker": {
            "path": "design/potential_policy_two_stitch_matrix.py",
            "sha256": checker_sha256,
            "unchanged_during_run": True,
        },
        "resource_policy": policy,
        "input_sha256": {**external_inputs, **local_inputs},
        "scope": {
            "level": 5,
            "scheduled_gaps": [0, 2],
            "parent_step": 20,
            "anchors_present_before_first_action": len(anchors),
            "potential_compatible_ordinals_1_based": list(EXPECTED_ORDINALS),
            "matrix_shape": [8, 8],
            "row_state_correlation": (
                "each row commits only its own exactly legal gap-0 interiors"
            ),
        },
        "result": {
            "valid_first_action_count": len(valid_first_actions),
            "valid_first_action_ordinals_1_based": valid_first_actions,
            "first_actions_with_legal_response_count": len(
                responding_first_actions
            ),
            "first_actions_with_legal_response_ordinals_1_based": (
                responding_first_actions
            ),
            "legal_ordered_pair_count": len(legal_pairs),
            "legal_ordered_pairs_ordinal_1_based": legal_pairs,
            "two_stitch_safety_choice_exists": bool(legal_pairs),
            "rows": rows,
        },
        "proved_by_this_matrix": [
            "every retained gap-0 action is tested against the full pinned anchor state",
            "every gap-2 response is tested only after committing its own row's gap-0 interiors",
            "every zero has exact projection and/or global-collinearity evidence",
        ],
        "not_proved": [
            "closure beyond the first two stitches",
            "a full state-dependent greatest fixed point",
            "control of exact-zero latent re-entry, births, cursor jumps, or all far secants",
        ],
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": resident,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default=rescue.DEFAULT_METADATA)
    parser.add_argument("--cache", default=rescue.DEFAULT_CACHE)
    parser.add_argument("--potential", default=rescue.DEFAULT_POTENTIAL)
    parser.add_argument("--bitsets", default=rescue.DEFAULT_BITSETS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = matrix_run(args)
    rescue.atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "output_sha256": rescue.file_sha256(args.output),
        "result": {
            key: value
            for key, value in payload["result"].items()
            if key != "rows"
        },
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_bytes": payload["maximum_resident_bytes"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
