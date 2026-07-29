#!/usr/bin/env python3
"""Build and verify the compact certificate for the exhaustive guarded census."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import guarded_l5_l6_common as common  # noqa: E402

SCHEMA_VERSION = 1
EXPECTED_FULL_SHA256 = "a69e490c544f65f51bdb178b27cd92b8ad359cb01af52de96c3b9cc796031aa2"
EXPECTED_FULL_PAYLOAD_SHA256 = "197d600065a5611977fd06f9a5b58d600fb9e32d1fff848b0b7e343866df1d25"
EXPECTED_NORMALIZED_MERGE_SHA256 = "e4e1eb68ebe4fed4c72b66063fd8c2d78310d179ef3fbe0903e557e6faa8d6e0"
EXPECTED_CENSUS_CHECKER_SHA256 = "7762b7415c677b7a1b01d3475cb1d9e3fd23d3b8919193b5c411df76b0fef23b"
EXPECTED_AUDITOR_SHA256 = "350e63d358b65c5014d9d3c943e8aa2bc803e81d73eaeaa462505d4978de80aa"
EXPECTED_SOURCE_SHA256 = "420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9"
EXPECTED_TERMINAL_AUDIT_SHA256 = "965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36"
EXPECTED_RANKS = 8_295
EXPECTED_DOMAIN_OCCURRENCES = 756_512_535
EXPECTED_MINIMUM = 71
PROCESS_START_SHA256 = common.file_sha256(Path(__file__).resolve())


def verify_self_unchanged():
    if common.file_sha256(Path(__file__).resolve()) != PROCESS_START_SHA256:
        raise RuntimeError("compact census summarizer changed during execution")


def verify_payload_hash(document):
    claimed = document.get("payload_sha256")
    payload = copy.deepcopy(document)
    payload.pop("payload_sha256", None)
    actual = common.stable_hash(payload)
    if claimed != actual:
        raise AssertionError("JSON payload hash mismatch", claimed, actual)
    return claimed


def load_full(path):
    file_sha256 = common.file_sha256(path)
    with open(path) as handle:
        document = json.load(handle)
    payload_sha256 = verify_payload_hash(document)
    normalized = copy.deepcopy(document)
    normalized.pop("payload_sha256", None)
    for snapshot in normalized["scope"]["rank_shards"]:
        snapshot["path"] = Path(snapshot["path"]).name
    if common.stable_hash(normalized) != EXPECTED_NORMALIZED_MERGE_SHA256:
        raise AssertionError("normalized full census semantic SHA-256 mismatch")
    if file_sha256 == EXPECTED_FULL_SHA256 and payload_sha256 != (
        EXPECTED_FULL_PAYLOAD_SHA256
    ):
        raise AssertionError("reference full census payload SHA-256 mismatch")
    if document.get("checker", {}).get("sha256") != EXPECTED_CENSUS_CHECKER_SHA256:
        raise AssertionError("full census checker pin mismatch")
    if document.get("source_sha256") != EXPECTED_SOURCE_SHA256 or document.get(
        "terminal_audit_sha256"
    ) != EXPECTED_TERMINAL_AUDIT_SHA256:
        raise AssertionError("full census lineage mismatch")
    return document


def verify_shards(document):
    records = []
    cursor = 0
    snapshots = document["scope"]["rank_shards"]
    if len(snapshots) != 32:
        raise AssertionError("expected 32 census shards")
    compact_snapshots = []
    for snapshot in snapshots:
        first, last = snapshot["rank_range"]
        if first != cursor:
            raise AssertionError("shard partition gap or overlap")
        cursor = last
        path = Path(snapshot["path"])
        if common.file_sha256(path) != snapshot["sha256"]:
            raise AssertionError("shard file SHA-256 mismatch", path)
        with path.open() as handle:
            shard = common.unseal(json.load(handle))
        if shard.get("status") != "complete exact guarded transition survivor-census shard":
            raise AssertionError("incomplete shard", path)
        if shard.get("rank_range") != [first, last] or shard.get("next_rank") != last:
            raise AssertionError("shard extent mismatch", path)
        if shard.get("checker_sha256") != EXPECTED_CENSUS_CHECKER_SHA256 or shard.get(
            "auditor_sha256"
        ) != EXPECTED_AUDITOR_SHA256:
            raise AssertionError("shard implementation pin mismatch", path)
        if shard.get("source_sha256") != EXPECTED_SOURCE_SHA256 or shard.get(
            "terminal_audit_sha256"
        ) != EXPECTED_TERMINAL_AUDIT_SHA256:
            raise AssertionError("shard lineage mismatch", path)
        if common.stable_hash(shard["records"]) != shard["record_stream_sha256"]:
            raise AssertionError("shard record stream mismatch", path)
        records.extend(shard["records"])
        compact_snapshots.append(
            {
                "rank_range": [first, last],
                "bytes": snapshot["bytes"],
                "sha256": snapshot["sha256"],
                "payload_sha256": snapshot["payload_sha256"],
                "record_stream_sha256": snapshot["record_stream_sha256"],
            }
        )
    if cursor != EXPECTED_RANKS or records != document["records"]:
        raise AssertionError("shards do not exactly reproduce merged records")
    return compact_snapshots


def recompute(document):
    records = document["records"]
    if len(records) != EXPECTED_RANKS:
        raise AssertionError("merged rank count mismatch")
    outcomes = Counter()
    distribution = Counter()
    by_step = defaultdict(
        lambda: {
            "ranks": 0,
            "domain_word_occurrences": 0,
            "surviving_connector_choices": 0,
            "minimum_surviving_connector_choices": None,
            "maximum_surviving_connector_choices": 0,
        }
    )
    values = []
    domain_total = 0
    for rank, record in enumerate(records):
        if record.get("construction_rank") != rank or not record.get("domain_exhaustive"):
            raise AssertionError("merged record rank/exhaustiveness mismatch", rank)
        local_outcomes = sum(record["outcome_counts"].values())
        if local_outcomes != record["domain_words"]:
            raise AssertionError("rank outcome partition mismatch", rank)
        survivors = record["surviving_connector_choices"]
        if record["outcome_counts"].get("survivor", 0) != survivors:
            raise AssertionError("rank survivor channel mismatch", rank)
        if not 1 <= record["first_survivor_ordinal_1_based"] <= record["domain_words"]:
            raise AssertionError("rank first survivor outside domain", rank)
        outcomes.update(record["outcome_counts"])
        distribution[survivors] += 1
        values.append(survivors)
        domain_total += record["domain_words"]
        step = by_step[record["step"]]
        step["ranks"] += 1
        step["domain_word_occurrences"] += record["domain_words"]
        step["surviving_connector_choices"] += survivors
        old_minimum = step["minimum_surviving_connector_choices"]
        step["minimum_surviving_connector_choices"] = (
            survivors if old_minimum is None else min(old_minimum, survivors)
        )
        step["maximum_surviving_connector_choices"] = max(
            step["maximum_surviving_connector_choices"], survivors
        )
    if domain_total != EXPECTED_DOMAIN_OCCURRENCES or sum(outcomes.values()) != domain_total:
        raise AssertionError("global domain/outcome total mismatch")
    if outcomes["survivor"] != sum(values):
        raise AssertionError("global survivor total mismatch")
    expected_result = document["result"]
    if expected_result["minimum_surviving_connector_choices"] != min(values) or (
        expected_result["maximum_surviving_connector_choices"] != max(values)
    ) or expected_result["sum_surviving_connector_choices"] != sum(values) or (
        expected_result["outcomes_by_channel"] != dict(sorted(outcomes.items()))
    ) or expected_result["surviving_choice_distribution"] != {
        str(key): count for key, count in sorted(distribution.items())
    }:
        raise AssertionError("merged aggregate fields do not reproduce")
    if min(values) != EXPECTED_MINIMUM:
        raise AssertionError("unexpected exact minimum")
    if document["commitments"]["record_stream_sha256"] != common.stable_hash(records):
        raise AssertionError("merged record-stream commitment mismatch")
    digest_stream = common.stable_hash(
        [record["outcome_code_stream_sha256"] for record in records]
    )
    if document["commitments"]["outcome_code_digest_stream_sha256"] != digest_stream:
        raise AssertionError("merged outcome-stream commitment mismatch")
    sorted_values = sorted(values)
    quantile_indices = [0, 82, 414, 829, 2073, 4147, 6221, 7465, 7880, 8212, 8294]
    quantiles = [
        {
            "order_index_0_based": index,
            "rank_fraction": f"{index}/{EXPECTED_RANKS - 1}",
            "surviving_connector_choices": sorted_values[index],
        }
        for index in quantile_indices
    ]
    minimum_records = [
        record for record in records if record["surviving_connector_choices"] == min(values)
    ]
    return {
        "domain_total": domain_total,
        "outcomes": dict(sorted(outcomes.items())),
        "distribution": [[key, count] for key, count in sorted(distribution.items())],
        "values": values,
        "minimum_records": minimum_records,
        "quantiles": quantiles,
        "by_step": {str(key): value for key, value in sorted(by_step.items())},
    }


def build(args):
    document = load_full(args.full)
    snapshots = verify_shards(document) if not args.skip_shard_files else None
    aggregate = recompute(document)
    values = aggregate["values"]
    compact = {
        "schema_version": SCHEMA_VERSION,
        "status": "compact exact certificate for the exhaustive all-choice census on the certified guarded L5 -> L6 chronology",
        "claim_class": "CERTIFIED FINITE",
        "summarizer": {
            "path": "design/summarize_guarded_l5_l6_census.py",
            "sha256": PROCESS_START_SHA256,
        },
        "frozen_implementations": {
            "census_checker_sha256": EXPECTED_CENSUS_CHECKER_SHA256,
            "independent_terminal_auditor_sha256": EXPECTED_AUDITOR_SHA256,
        },
        "lineage": {
            "construction_checkpoint_sha256": EXPECTED_SOURCE_SHA256,
            "terminal_firstness_and_all_pairs_audit_sha256": EXPECTED_TERMINAL_AUDIT_SHA256,
        },
        "full_artifact": {
            "path_for_reproduction": "/tmp/guarded-L5-to-L6-survivor-census-v2.json",
            "bytes": Path(args.full).stat().st_size,
            "reference_file_sha256": EXPECTED_FULL_SHA256,
            "reference_payload_sha256": EXPECTED_FULL_PAYLOAD_SHA256,
            "path_normalized_semantic_sha256": EXPECTED_NORMALIZED_MERGE_SHA256,
            "all_32_shards_reloaded_and_matched": not args.skip_shard_files,
        },
        "scope": {
            "realized_chronological_prefixes": EXPECTED_RANKS,
            "all_canonical_domain_word_occurrences": aggregate["domain_total"],
            "endpoint_cutoff": None,
            "spatial_cutoff": None,
            "distance_cutoff": None,
        },
        "result": {
            "minimum_surviving_connector_choices": min(values),
            "minimum_records": aggregate["minimum_records"],
            "maximum_surviving_connector_choices": max(values),
            "sum_surviving_connector_choices": sum(values),
            "mean_surviving_connector_choices": {
                "numerator": sum(values),
                "denominator": len(values),
            },
            "median_surviving_connector_choices": statistics.median(values),
            "exact_distribution_count_to_rank_frequency": aggregate["distribution"],
            "selected_order_statistics": aggregate["quantiles"],
            "outcomes_by_first_rejection_channel": aggregate["outcomes"],
            "by_parent_step": aggregate["by_step"],
        },
        "commitments": document["commitments"],
        "domain_preflights": document["exact_atomization"],
        "shards": snapshots,
        "interpretation": {
            "proved": "all 8,295 realized prefixes have at least 71 surviving canonical guarded connectors",
            "not_proved": [
                "availability after choosing an alternate survivor",
                "availability for every reachable safe state",
                "guarded L6 -> L7 availability",
                "a universal successor theorem or an infinite construction",
            ],
        },
    }
    compact["payload_sha256"] = common.stable_hash(compact)
    common.atomic_json_dump(compact, args.output)
    verify_compact(args.output)
    return compact


def verify_compact(path):
    with open(path) as handle:
        document = json.load(handle)
    verify_payload_hash(document)
    if document.get("schema_version") != SCHEMA_VERSION or document.get(
        "claim_class"
    ) != "CERTIFIED FINITE":
        raise AssertionError("compact census schema/claim drift")
    if document.get("summarizer", {}).get("sha256") != PROCESS_START_SHA256:
        raise AssertionError("compact census summarizer pin mismatch")
    full = document["full_artifact"]
    if full["reference_file_sha256"] != EXPECTED_FULL_SHA256 or full[
        "reference_payload_sha256"
    ] != EXPECTED_FULL_PAYLOAD_SHA256 or full[
        "path_normalized_semantic_sha256"
    ] != EXPECTED_NORMALIZED_MERGE_SHA256:
        raise AssertionError("compact census full-artifact pin mismatch")
    scope = document["scope"]
    if scope["realized_chronological_prefixes"] != EXPECTED_RANKS or scope[
        "all_canonical_domain_word_occurrences"
    ] != EXPECTED_DOMAIN_OCCURRENCES:
        raise AssertionError("compact census scope mismatch")
    result = document["result"]
    distribution = result["exact_distribution_count_to_rank_frequency"]
    if sum(frequency for _value, frequency in distribution) != EXPECTED_RANKS or (
        sum(value * frequency for value, frequency in distribution)
        != result["sum_surviving_connector_choices"]
    ) or distribution[0][0] != result["minimum_surviving_connector_choices"] or (
        distribution[-1][0] != result["maximum_surviving_connector_choices"]
    ) or result["minimum_surviving_connector_choices"] != EXPECTED_MINIMUM:
        raise AssertionError("compact census distribution mismatch")
    outcomes = result["outcomes_by_first_rejection_channel"]
    if sum(outcomes.values()) != EXPECTED_DOMAIN_OCCURRENCES or outcomes[
        "survivor"
    ] != result["sum_surviving_connector_choices"]:
        raise AssertionError("compact census outcome partition mismatch")
    by_step = result["by_parent_step"]
    if sum(value["ranks"] for value in by_step.values()) != EXPECTED_RANKS or sum(
        value["domain_word_occurrences"] for value in by_step.values()
    ) != EXPECTED_DOMAIN_OCCURRENCES or sum(
        value["surviving_connector_choices"] for value in by_step.values()
    ) != result["sum_surviving_connector_choices"]:
        raise AssertionError("compact census by-step partition mismatch")
    verify_self_unchanged()
    return {
        "status": "verified",
        "path": str(Path(path).resolve()),
        "bytes": Path(path).stat().st_size,
        "sha256": common.file_sha256(path),
        "payload_sha256": document["payload_sha256"],
        "minimum_surviving_connector_choices": EXPECTED_MINIMUM,
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--full", required=True)
    build_parser.add_argument("--output", required=True)
    build_parser.add_argument("--skip-shard-files", action="store_true")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--input", required=True)
    args = parser.parse_args()
    if args.mode == "build":
        document = build(args)
        result = verify_compact(args.output)
        result["full_shards_reloaded"] = document["full_artifact"][
            "all_32_shards_reloaded_and_matched"
        ]
    else:
        result = verify_compact(args.input)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
