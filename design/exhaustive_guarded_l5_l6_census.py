#!/usr/bin/env python3
"""Exact exhaustive survivor census for the certified guarded L5->L6 path.

The literal auditor evaluates global legality and cone incidence afresh for
every word.  That is exact but needlessly repeats predicates depending only on
one candidate point or one candidate-internal line.  This checker uses exact
atomization:

* point legality is memoized by the absolute candidate point;
* old-point incidence with an interior-pair line is queried by the exact moment
  key ``p cross primitive(b-a)``;
* old-new guarded-cone incidence is memoized by the candidate point;
* action, yz, same-word, and endpoint predicates remain per whole word.

These are identities, not spatial cutoffs or approximations.  Shards are
disjoint rank intervals on one immutable certified chronology.  Each shard is
resumable between ranks and deterministic.  ``merge`` accepts only an exact
cover of all 8,295 ranks and verifies all 756,512,535 domain occurrences.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import audit_guarded_l5_to_l6 as audit  # noqa: E402
from design import guarded_l5_l6_common as common  # noqa: E402
from design import potential_policy_chronological_rescue as rescue  # noqa: E402


SOURCE_SHA256 = "420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9"
TERMINAL_AUDIT_SHA256 = "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36"
TERMINAL_AUDIT_PATH = ROOT / "design" / "guarded-L5-to-L6-audit-summary.json"
EXPECTED_RANKS = 8_295
EXPECTED_DOMAIN_OCCURRENCES = 756_512_535
SCHEMA_VERSION = 1
CHECKPOINT_INTERVAL = 5
PROCESS_START_CHECKER_SHA256 = common.file_sha256(Path(__file__).resolve())
PROCESS_START_AUDITOR_SHA256 = common.file_sha256(Path(audit.__file__).resolve())

CATEGORY_NAMES = (
    "zero-envelope-incompatible",
    "local-poison:occupied-yz-fibre",
    "local-poison:same-word-yz-fibre",
    "exact-global-legality",
    "guard-cone:old-new-anchor:11/3",
    "guard-cone:old-new-anchor:348/275",
    "guard-cone:old-new-connector:11/3",
    "guard-cone:old-new-connector:348/275",
    "guard-cone:same-word-new-new:11/3",
    "guard-cone:same-word-new-new:348/275",
    "survivor",
)
CATEGORY_ID = {name: index for index, name in enumerate(CATEGORY_NAMES)}


def assert_checker_unchanged():
    if common.file_sha256(Path(__file__).resolve()) != (
        PROCESS_START_CHECKER_SHA256
    ) or common.file_sha256(Path(audit.__file__).resolve()) != (
        PROCESS_START_AUDITOR_SHA256
    ):
        raise RuntimeError("exhaustive census code changed during execution")


def verify_terminal_certificate():
    if common.file_sha256(TERMINAL_AUDIT_PATH) != TERMINAL_AUDIT_SHA256:
        raise AssertionError("committed terminal transition certificate drift")
    with TERMINAL_AUDIT_PATH.open() as handle:
        terminal = json.load(handle)
    if terminal.get("status") != (
        "exact independent finite certificate for the consecutive guarded-L5 -> guarded-L6 transition"
    ) or terminal["source_checkpoint"]["sha256"] != SOURCE_SHA256 or not terminal[
        "result"
    ]["first_survivor_audit_completed"]:
        raise AssertionError("terminal transition certificate is incomplete")
    return terminal


def context_args(args):
    return argparse.Namespace(
        source=args.source,
        expected_source_sha256=SOURCE_SHA256,
        parent=args.parent,
        metadata=args.metadata,
        cache=args.cache,
        action_bitsets=args.action_bitsets,
    )


def primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if divisor == 0:
        raise AssertionError("zero interior-pair direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def line_clear(first, second, store, line_indexes):
    direction = primitive(common.subtract(second, first))
    moments = line_indexes.get(direction)
    if moments is None:
        moments = {cross(point, direction) for point in store.pts}
        line_indexes[direction] = moments
    return cross(first, direction) not in moments


def exact_word_legal(interiors, store, point_legality, line_indexes):
    for point in interiors:
        value = point_legality.get(point)
        if value is None:
            value = store.legal(point)
            point_legality[point] = value
        if not value:
            return False
    return all(
        line_clear(first, second, store, line_indexes)
        for index, first in enumerate(interiors)
        for second in interiors[index + 1:]
    )


def old_cone_incidence(point, store, anchor_count, memo):
    if point in memo:
        return memo[point]
    result = None
    for earlier_id, earlier in enumerate(store.pts):
        matches = common.cone_matches(common.subtract(point, earlier))
        if matches:
            classification = (
                "old-new-anchor"
                if earlier_id < anchor_count
                else "old-new-connector"
            )
            result = classification, matches[0]
            break
    memo[point] = result
    return result


def cone_incidence(interiors, store, anchor_count, old_cone_memo):
    for later_slot, point in enumerate(interiors):
        old = old_cone_incidence(
            point, store, anchor_count, old_cone_memo
        )
        if old is not None:
            return old
        for earlier in interiors[:later_slot]:
            matches = common.cone_matches(common.subtract(point, earlier))
            if matches:
                return "same-word-new-new", matches[0]
    return None


def projection_category(interiors, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts:
            return "local-poison:occupied-yz-fibre"
        if fibre in local:
            return "local-poison:same-word-yz-fibre"
        local.add(fibre)
    return None


def verify_packed_direction_bound(context):
    minima = [min(point[axis] for point in context["anchors"]) for axis in range(3)]
    maxima = [max(point[axis] for point in context["anchors"]) for axis in range(3)]
    for rank, record in enumerate(context["source"]["selection_records"]):
        _gap, _step, _block, _ordinal, _word, _start, _target, interiors = (
            audit.selected_geometry(context, rank, record)
        )
        for point in interiors:
            for axis in range(3):
                minima[axis] = min(minima[axis], point[axis])
                maxima[axis] = max(maxima[axis], point[axis])
    spans = [maxima[axis] - minima[axis] for axis in range(3)]
    # Every candidate lies within eight of its anchor.  This makes each raw
    # displacement, and hence each primitive component, strictly smaller than
    # fast_legal's signed 21-bit packing lane.
    if max(spans) + 16 >= 1 << 20:
        raise AssertionError("census packed direction lane is not injective")
    return {
        "final_coordinate_minima": minima,
        "final_coordinate_maxima": maxima,
        "final_coordinate_spans": spans,
        "candidate_margin": 8,
        "signed_packing_lane_bound": 1 << 20,
        "packing_is_injective_on_every_point_legality_query": True,
    }


def verify_complete_domain_endpoints(context):
    words_checked = 0
    word_slots_checked = 0
    digest = hashlib.sha256()
    for step in range(common.EXPECTED_MENU_SIZE):
        block = context["blocks"][step]
        cursor = block["start"]
        expected = audit.apply(audit.M_BAL3, rescue.MENU[step])
        for ordinal in range(1, block["words"] + 1):
            length = context["cache"][cursor]
            cursor += 1
            end = cursor + length
            if not 1 <= length <= 255 or end > block["end"]:
                raise AssertionError("domain endpoint preflight cache drift", step, ordinal)
            word = context["cache"][cursor:end]
            cursor = end
            displacement = [0, 0, 0]
            for child in word:
                vector = rescue.MENU[child]
                for axis in range(3):
                    displacement[axis] += vector[axis]
            if tuple(displacement) != expected:
                raise AssertionError("domain endpoint preflight failed", step, ordinal)
            digest.update(bytes((step, length)))
            digest.update(word)
            words_checked += 1
            word_slots_checked += length
        if cursor != block["end"]:
            raise AssertionError("domain endpoint preflight trailing bytes", step)
    if words_checked != common.EXPECTED_EFFECTIVE_WORDS or word_slots_checked != (
        common.EXPECTED_WORD_SLOTS
    ):
        raise AssertionError("domain endpoint preflight census drift")
    return {
        "words_checked": words_checked,
        "word_slots_checked": word_slots_checked,
        "step_word_stream_sha256": digest.hexdigest(),
        "every_word_has_the_exact_scaled_parent_step_endpoint": True,
    }


def scan_rank(context, rank, store, yz_counts):
    source_record = context["source"]["selection_records"][rank]
    gap, step, block, selected_ordinal, _selected_word, start, target, _selected_interiors = (
        audit.selected_geometry(context, rank, source_record)
    )
    action = context["action_records"][step]
    cursor = block["start"]
    counts = [0] * len(CATEGORY_NAMES)
    outcome_codes = bytearray(block["words"])
    point_legality = {}
    old_cone_memo = {}
    line_indexes = {}
    first_survivor = None
    survivor_count = 0
    anchor_count = len(context["anchors"])

    for ordinal in range(1, block["words"] + 1):
        length = context["cache"][cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("census cache boundary drift", rank, ordinal)
        word = tuple(context["cache"][cursor:end])
        cursor = end

        if not common.action_accepts(
            context["actions"], action, "zero", ordinal
        ):
            category = "zero-envelope-incompatible"
        else:
            interiors = tuple(rescue.word_interiors(start, word))
            category = projection_category(interiors, yz_counts)
            if category is None:
                if not exact_word_legal(
                    interiors, store, point_legality, line_indexes
                ):
                    category = "exact-global-legality"
                else:
                    cone = cone_incidence(
                        interiors, store, anchor_count, old_cone_memo
                    )
                    category = (
                        "survivor"
                        if cone is None
                        else "guard-cone:{}:{}".format(*cone)
                    )
        category_id = CATEGORY_ID[category]
        outcome_codes[ordinal - 1] = category_id
        counts[category_id] += 1
        if category == "survivor":
            survivor_count += 1
            if first_survivor is None:
                first_survivor = ordinal

    if cursor != block["end"] or sum(counts) != block["words"]:
        raise AssertionError("census complete-domain extent drift", rank)
    if first_survivor != selected_ordinal:
        raise AssertionError(
            "census first survivor disagrees with independent terminal audit",
            rank,
            first_survivor,
            selected_ordinal,
        )
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "domain_words": block["words"],
        "surviving_connector_choices": survivor_count,
        "first_survivor_ordinal_1_based": first_survivor,
        "outcome_counts": {
            CATEGORY_NAMES[index]: count
            for index, count in enumerate(counts)
            if count
        },
        "outcome_code_stream_sha256": hashlib.sha256(outcome_codes).hexdigest(),
        "distinct_point_legality_queries": len(point_legality),
        "distinct_old_cone_queries": len(old_cone_memo),
        "distinct_interior_pair_directions": len(line_indexes),
        "domain_exhaustive": True,
    }


def initial_shard(first_rank, last_rank):
    value = {
        "schema_version": SCHEMA_VERSION,
        "status": "partial exact guarded transition survivor-census shard",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "auditor_sha256": PROCESS_START_AUDITOR_SHA256,
        "source_sha256": SOURCE_SHA256,
        "terminal_audit_sha256": TERMINAL_AUDIT_SHA256,
        "rank_range": [first_rank, last_rank],
        "next_rank": first_rank,
        "records": [],
        "record_stream_sha256": common.stable_hash([]),
    }
    return common.seal(value)


def load_shard(path, first_rank, last_rank):
    path = Path(path)
    if not path.exists():
        return initial_shard(first_rank, last_rank)
    with path.open() as handle:
        shard = common.unseal(json.load(handle))
    expected = initial_shard(first_rank, last_rank)
    for key in (
        "schema_version", "checker_sha256", "auditor_sha256", "source_sha256",
        "terminal_audit_sha256", "rank_range",
    ):
        if shard.get(key) != expected[key]:
            raise AssertionError("survivor-census shard static drift", key)
    if shard["next_rank"] != first_rank + len(shard["records"]) or not (
        first_rank <= shard["next_rank"] <= last_rank
    ) or shard["record_stream_sha256"] != common.stable_hash(shard["records"]):
        raise AssertionError("survivor-census shard cursor/record drift")
    return shard


def save_shard(path, shard):
    assert_checker_unchanged()
    common.atomic_json_dump(common.seal(shard), path)


def run_shard(args):
    if not 0 <= args.first_rank < args.last_rank <= EXPECTED_RANKS:
        raise ValueError("rank range must lie in [0,8295]")
    verify_terminal_certificate()
    context = audit.open_context(context_args(args))
    try:
        endpoint_preflight = verify_complete_domain_endpoints(context)
        packing_preflight = verify_packed_direction_bound(context)
        shard = load_shard(args.output, args.first_rank, args.last_rank)
        if "domain_endpoint_preflight" in shard and shard[
            "domain_endpoint_preflight"
        ] != endpoint_preflight:
            raise AssertionError("survivor-census endpoint preflight drift")
        shard["domain_endpoint_preflight"] = endpoint_preflight
        if "direction_packing_preflight" in shard and shard[
            "direction_packing_preflight"
        ] != packing_preflight:
            raise AssertionError("survivor-census packing preflight drift")
        shard["direction_packing_preflight"] = packing_preflight
        rank = shard["next_rank"]
        store, yz_counts, _prefix = audit.reconstruct_prefix(context, rank)
        completed_this_run = 0
        while rank < args.last_rank:
            record = scan_rank(context, rank, store, yz_counts)
            shard["records"].append(record)
            shard["record_stream_sha256"] = common.stable_hash(shard["records"])
            shard["next_rank"] += 1
            source_record = context["source"]["selection_records"][rank]
            _gap, _step, _block, _ordinal, _word, _start, _target, interiors = (
                audit.selected_geometry(context, rank, source_record)
            )
            audit.apply_selected_independent(interiors, store, yz_counts)
            rank += 1
            completed_this_run += 1
            if completed_this_run % CHECKPOINT_INTERVAL == 0:
                save_shard(args.output, shard)
        shard["status"] = "complete exact guarded transition survivor-census shard"
        save_shard(args.output, shard)
        return {
            "status": shard["status"],
            "output": str(Path(args.output).resolve()),
            "bytes": Path(args.output).stat().st_size,
            "sha256": common.file_sha256(args.output),
            "payload_sha256": json.load(open(args.output))["payload_sha256"],
            "rank_range": shard["rank_range"],
            "records": len(shard["records"]),
            "record_stream_sha256": shard["record_stream_sha256"],
            "domain_endpoint_preflight": endpoint_preflight,
            "direction_packing_preflight": packing_preflight,
        }
    finally:
        audit.close_context(context)


def load_complete_shard(path):
    path = Path(path)
    with path.open() as handle:
        shard = common.unseal(json.load(handle))
    if shard.get("status") != "complete exact guarded transition survivor-census shard" or (
        shard.get("checker_sha256") != PROCESS_START_CHECKER_SHA256
    ) or shard.get("auditor_sha256") != PROCESS_START_AUDITOR_SHA256 or shard.get(
        "source_sha256"
    ) != SOURCE_SHA256 or shard.get("terminal_audit_sha256") != TERMINAL_AUDIT_SHA256:
        raise AssertionError("incomplete or foreign survivor-census shard", path)
    first, last = shard["rank_range"]
    if shard["next_rank"] != last or len(shard["records"]) != last - first or (
        shard["record_stream_sha256"] != common.stable_hash(shard["records"])
    ):
        raise AssertionError("complete survivor-census shard extent drift", path)
    return shard, {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": common.file_sha256(path),
        "payload_sha256": shard["payload_sha256"],
        "rank_range": shard["rank_range"],
        "record_stream_sha256": shard["record_stream_sha256"],
    }


def merge(args):
    verify_terminal_certificate()
    loaded = [load_complete_shard(path) for path in args.chunks]
    loaded.sort(key=lambda item: item[0]["rank_range"][0])
    ranges = [item[0]["rank_range"] for item in loaded]
    cursor = 0
    records = []
    snapshots = []
    endpoint_preflight = loaded[0][0].get("domain_endpoint_preflight")
    packing_preflight = loaded[0][0].get("direction_packing_preflight")
    for (shard, snapshot), (first, last) in zip(loaded, ranges):
        if first != cursor:
            raise AssertionError("survivor-census shards do not form a partition", ranges)
        cursor = last
        if shard.get("domain_endpoint_preflight") != endpoint_preflight or shard.get(
            "direction_packing_preflight"
        ) != packing_preflight:
            raise AssertionError("survivor-census shard preflight disagreement")
        records.extend(shard["records"])
        snapshots.append(snapshot)
    if cursor != EXPECTED_RANKS or len(records) != EXPECTED_RANKS:
        raise AssertionError("survivor-census partition does not cover all ranks")
    for rank, record in enumerate(records):
        if record["construction_rank"] != rank or not record["domain_exhaustive"]:
            raise AssertionError("survivor-census merged rank drift", rank)
    domain_occurrences = sum(record["domain_words"] for record in records)
    if domain_occurrences != EXPECTED_DOMAIN_OCCURRENCES:
        raise AssertionError("survivor-census complete domain total drift")
    survivors = [record["surviving_connector_choices"] for record in records]
    outcomes = Counter()
    for record in records:
        outcomes.update(record["outcome_counts"])
    if sum(outcomes.values()) != EXPECTED_DOMAIN_OCCURRENCES or outcomes[
        "survivor"
    ] != sum(survivors):
        raise AssertionError("survivor-census outcome partition drift")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "exact exhaustive surviving-connector census on the certified consecutive guarded-L6 chronology",
        "checker": {
            "path": "design/exhaustive_guarded_l5_l6_census.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
        },
        "source_sha256": SOURCE_SHA256,
        "terminal_audit_sha256": TERMINAL_AUDIT_SHA256,
        "scope": {
            "stitches": EXPECTED_RANKS,
            "all_domain_word_occurrences": domain_occurrences,
            "connector_order": "every compact-cache ordinal at every realized prefix",
            "distance_cutoff": None,
            "endpoint_cutoff": None,
            "rank_shards": snapshots,
        },
        "exact_atomization": {
            "point_legality": "memoized exact canonical-direction duplicate test",
            "interior_pair_line": "exact primitive-direction affine moment membership",
            "old_new_guarded_cone": "memoized exact homogeneous cone equations",
            "whole_word_correlation_preserved": True,
            "first_survivor_matches_independent_terminal_audit_at_every_stitch": True,
            "complete_domain_endpoint_preflight": endpoint_preflight,
            "direction_packing_preflight": packing_preflight,
        },
        "result": {
            "minimum_surviving_connector_choices": min(survivors),
            "maximum_surviving_connector_choices": max(survivors),
            "sum_surviving_connector_choices": sum(survivors),
            "surviving_choice_distribution": {
                str(key): value
                for key, value in sorted(Counter(survivors).items())
            },
            "outcomes_by_channel": dict(sorted(outcomes.items())),
        },
        "commitments": {
            "record_stream_sha256": common.stable_hash(records),
            "outcome_code_digest_stream_sha256": common.stable_hash([
                record["outcome_code_stream_sha256"] for record in records
            ]),
        },
        "records": records,
        "not_proved": [
            "availability on an alternate reachable state",
            "guarded L6->L7 availability",
            "a universal successor theorem or infinite construction",
        ],
    }
    payload["payload_sha256"] = common.stable_hash(payload)
    common.atomic_json_dump(payload, args.output)
    return {
        "status": payload["status"],
        "output": str(Path(args.output).resolve()),
        "bytes": Path(args.output).stat().st_size,
        "sha256": common.file_sha256(args.output),
        "payload_sha256": payload["payload_sha256"],
        "minimum_surviving_connector_choices": min(survivors),
        "distribution": payload["result"]["surviving_choice_distribution"],
    }


def self_check():
    direction = primitive((6, -4, -6))
    if direction != (3, -2, -3):
        raise AssertionError("census primitive direction drift")
    first = (2, 3, 5)
    second = (5, 1, 4)
    d = primitive(common.subtract(second, first))
    moment = cross(first, d)
    translated = tuple(first[axis] + 7 * d[axis] for axis in range(3))
    if cross(translated, d) != moment:
        raise AssertionError("census affine moment identity drift")
    if set(CATEGORY_NAMES) != set(CATEGORY_ID) or len(CATEGORY_NAMES) > 256:
        raise AssertionError("census category encoding drift")
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "auditor_sha256": PROCESS_START_AUDITOR_SHA256,
        "terminal_audit_sha256": TERMINAL_AUDIT_SHA256,
        "point_line_atomization_identity_checked": True,
        "large_artifacts_opened": False,
    }


def add_inputs(parser):
    parser.add_argument("--source", default=audit.DEFAULT_SOURCE)
    parser.add_argument("--parent", default=common.DEFAULT_CANONICAL_PARENT)
    parser.add_argument("--metadata", default=common.DEFAULT_METADATA)
    parser.add_argument("--cache", default=common.DEFAULT_CACHE)
    parser.add_argument("--action-bitsets", default=common.DEFAULT_ACTION_BITSETS)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("self-check")
    shard_parser = subparsers.add_parser("shard")
    add_inputs(shard_parser)
    shard_parser.add_argument("--first-rank", type=int, required=True)
    shard_parser.add_argument("--last-rank", type=int, required=True)
    shard_parser.add_argument("--output", required=True)
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--chunks", nargs="+", required=True)
    merge_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.mode == "self-check":
        result = self_check()
    elif args.mode == "shard":
        result = run_shard(args)
    else:
        result = merge(args)
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
