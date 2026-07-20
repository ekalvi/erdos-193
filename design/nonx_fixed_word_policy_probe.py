#!/usr/bin/env python3
"""Exact fixed-word restriction of the non-x degenerate-site graph.

This is deliberately narrower than a legality or availability checker.  It
chooses one whole connector word for every parent step, keeps the full-domain
candidate-site universe, and retains a direction-blind edge only when the
chosen source word avoids the carried poison site and one of that same word's
ordered slots realizes the edge.  Thus slots from different words are never
spliced at one source occurrence.

The deterministic pilot policy is the first cached word whose proper
interiors have pairwise distinct lateral (y,z) fibres and avoid both endpoint
fibres.  Endpoint fibres may coincide with each other (as they do for an
x-parallel parent edge); only new interiors are constrained.  This is an
intrinsic x-projection compatibility check, not the global empty-fibre
condition of the no-new-x-line construction.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import mmap
import os
import resource
import struct
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_NONX = Path("/tmp/nonx-degenerate-site-graph-canonical.json")
DEFAULT_OUTPUT = Path("/tmp/nonx-fixed-word-policy-probe.json")

EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_NONX_SHA256 = (
    "e0f5765fec55b25b9392333c25da037d9d073b7bc95b81680bb4e5957a0c4d92"
)
EXPECTED_NONX_CHECKER_SHA256 = (
    "4eb928bad0c0104d34b68424b07dd3b6a4939f216968bd6b2399a540b592e755"
)
EXPECTED_EFFECTIVE_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
CACHE_MAGIC = b"NOXLN001"

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def subtract(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def apply_matrix(vector):
    x, y, z = vector
    return (3 * x, -3 * z, 3 * y - z)


def word_geometry(word):
    position = (0, 0, 0)
    prefixes = []
    interiors = []
    for slot, target in enumerate(word):
        prefixes.append(position)
        position = add(position, MENU[target])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(prefixes), tuple(interiors), position


def intrinsic_x_projection_compatible(interiors, endpoint):
    endpoint_fibres = {(0, 0), endpoint[1:]}
    interior_fibres = [point[1:] for point in interiors]
    return (
        len(set(interior_fibres)) == len(interior_fibres)
        and not endpoint_fibres.intersection(interior_fibres)
    )


def verify_inputs(metadata_path, cache_path, nonx_path):
    commitments = {
        "metadata": file_sha256(metadata_path),
        "cache": file_sha256(cache_path),
        "nonx_canonical_result": file_sha256(nonx_path),
        "nonx_checker": file_sha256(
            ROOT / "design" / "nonx_degenerate_site_graph.py"
        ),
    }
    expected = {
        "metadata": EXPECTED_METADATA_SHA256,
        "cache": EXPECTED_CACHE_SHA256,
        "nonx_canonical_result": EXPECTED_NONX_SHA256,
        "nonx_checker": EXPECTED_NONX_CHECKER_SHA256,
    }
    if commitments != expected:
        raise AssertionError("pinned input drift", expected, commitments)
    return commitments


def resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError("all numerical thread controls must equal 1", observed)
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice < 15:
        raise RuntimeError("run must have nice value at least 15", nice)
    return {"thread_environment": observed, "process_nice": nice}


def canonical_two_cycle(nonx):
    witness = nonx["canonical_x_avoiding_cycle_witness"]
    if witness["cycle_length_edges"] != 2:
        raise AssertionError("canonical x-avoiding witness is not a two-cycle")
    nodes = witness["cycle_node_sequence"]
    if {node["step"] for node in nodes} != {1} or nodes[0] != nodes[-1]:
        raise AssertionError("canonical two-cycle is no longer step-1 recurrent")
    edges = []
    for record in witness["edge_records"]:
        exact = record["exact_cache_occurrence_witness"]
        edges.append({
            "source_site": tuple(record["source"]["candidate_site"]),
            "target_site": tuple(record["target"]["candidate_site"]),
            "target_step": record["target"]["step"],
            "prefix_control": tuple(record["selected_minimum_control"]),
            "canonical_witness_word_ordinal_1_based": exact[
                "word_ordinal_1_based"
            ],
        })
    return tuple(edges)


def scan_domains(metadata, cache_path, cycle_edges):
    blocks = sorted(
        metadata["compact_domain_cache"]["blocks"],
        key=lambda block: block["step"],
    )
    if len(blocks) != len(MENU):
        raise AssertionError("domain block count drift")
    candidate_sites = [set() for _ in MENU]
    chosen = [None] * len(MENU)
    chosen_ordinals = [None] * len(MENU)
    step_one = Counter()
    step_one_examples = {}
    word_count = 0
    slot_count = 0

    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("cache magic drift")
            for block in blocks:
                source = block["step"]
                cursor = block["start"]
                for ordinal in range(1, block["words"] + 1):
                    length = cache[cursor]
                    cursor += 1
                    word = tuple(cache[cursor:cursor + length])
                    cursor += length
                    prefixes, interiors, endpoint = word_geometry(word)
                    if endpoint != apply_matrix(MENU[source]):
                        raise AssertionError("cached word endpoint drift")
                    candidate_sites[source].update(interiors)
                    projection_compatible = intrinsic_x_projection_compatible(
                        interiors, endpoint
                    )
                    if chosen[source] is None and projection_compatible:
                        chosen[source] = {
                            "word": word,
                            "prefixes": prefixes,
                            "interiors": interiors,
                        }
                        chosen_ordinals[source] = ordinal

                    if source == 1:
                        interior_set = set(interiors)
                        avoids_cycle_sites = all(
                            edge["source_site"] not in interior_set
                            for edge in cycle_edges
                        )
                        realizes = tuple(
                            any(
                                target == edge["target_step"]
                                and control == edge["prefix_control"]
                                for target, control in zip(word, prefixes)
                            )
                            for edge in cycle_edges
                        )
                        step_one["words"] += 1
                        step_one["projection_compatible"] += int(
                            projection_compatible
                        )
                        step_one["avoids_both_cycle_sites"] += int(
                            avoids_cycle_sites
                        )
                        for index, realized in enumerate(realizes):
                            step_one[f"realizes_edge_{index}"] += int(realized)
                        step_one["realizes_both_edges"] += int(all(realizes))
                        robust_breaker = (
                            projection_compatible
                            and avoids_cycle_sites
                            and not any(realizes)
                        )
                        step_one["robust_breakers_realizing_neither"] += int(
                            robust_breaker
                        )
                        if robust_breaker and "robust_breaker" not in step_one_examples:
                            step_one_examples["robust_breaker"] = {
                                "ordinal_1_based": ordinal,
                                "word": list(word),
                                "interiors": [list(point) for point in interiors],
                            }
                    word_count += 1
                    slot_count += length
                if cursor != block["end"]:
                    raise AssertionError("cache block boundary drift", source)
        finally:
            cache.close()

    if word_count != EXPECTED_EFFECTIVE_WORDS:
        raise AssertionError("effective word total drift", word_count)
    if slot_count != EXPECTED_WORD_SLOTS:
        raise AssertionError("word-slot total drift", slot_count)
    if not all(chosen):
        raise AssertionError("some step has no intrinsic projection-compatible word")
    if step_one["realizes_both_edges"] != 0:
        raise AssertionError("canonical two-cycle unexpectedly has one-word support")

    return {
        "candidate_sites": tuple(tuple(sorted(sites)) for sites in candidate_sites),
        "chosen": tuple(chosen),
        "chosen_ordinals": tuple(chosen_ordinals),
        "step_one_audit": {
            **dict(sorted(step_one.items())),
            **step_one_examples,
        },
        "word_count": word_count,
        "slot_count": slot_count,
    }


def find_cycle(adjacency, residual):
    residual_set = set(residual)
    color = bytearray(len(adjacency))
    parent = [-1] * len(adjacency)
    for start in residual:
        if color[start]:
            continue
        color[start] = 1
        stack = [(start, iter(adjacency[start]))]
        while stack:
            source, successors = stack[-1]
            try:
                target = next(successors)
            except StopIteration:
                color[source] = 2
                stack.pop()
                continue
            if target not in residual_set:
                continue
            if color[target] == 0:
                parent[target] = source
                color[target] = 1
                stack.append((target, iter(adjacency[target])))
                continue
            if color[target] == 1:
                path = [source]
                while path[-1] != target:
                    path.append(parent[path[-1]])
                path.reverse()
                path.append(target)
                return tuple(path)
    raise AssertionError("nonempty Kahn residual supplied no cycle")


def build_policy_graph(candidate_sites, chosen):
    nodes = tuple(
        (step, site)
        for step, sites in enumerate(candidate_sites)
        for site in sites
    )
    node_index = {node: index for index, node in enumerate(nodes)}
    adjacency = [[] for _node in nodes]

    for source_index, (source_step, source_site) in enumerate(nodes):
        action = chosen[source_step]
        if source_site in action["interiors"]:
            continue
        for target_step, control in zip(action["word"], action["prefixes"]):
            target_site = apply_matrix(subtract(source_site, control))
            target_index = node_index.get((target_step, target_site))
            if target_index is not None:
                adjacency[source_index].append(target_index)
        adjacency[source_index] = sorted(set(adjacency[source_index]))

    indegree = [0] * len(nodes)
    edge_digest = hashlib.sha256()
    edges = 0
    for source, successors in enumerate(adjacency):
        source_step, source_site = nodes[source]
        for target in successors:
            target_step, target_site = nodes[target]
            indegree[target] += 1
            edges += 1
            edge_digest.update(struct.pack(
                "<8i",
                source_step,
                *source_site,
                target_step,
                *target_site,
            ))

    queue = [index for index, degree in enumerate(indegree) if degree == 0]
    heapq.heapify(queue)
    topological_order = []
    while queue:
        source = heapq.heappop(queue)
        topological_order.append(source)
        for target in adjacency[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(queue, target)

    if len(topological_order) != len(nodes):
        residual = tuple(
            index for index, degree in enumerate(indegree) if degree
        )
        cycle = find_cycle(adjacency, residual)
        return {
            "nodes": len(nodes),
            "edges": edges,
            "edge_stream_sha256": edge_digest.hexdigest(),
            "acyclic": False,
            "kahn_residual_vertices": len(residual),
            "cycle": [
                {"step": nodes[index][0], "candidate_site": list(nodes[index][1])}
                for index in cycle
            ],
            "strict_vertex_potential": None,
        }

    rank = [0] * len(nodes)
    for source in reversed(topological_order):
        if adjacency[source]:
            rank[source] = 1 + max(rank[target] for target in adjacency[source])
    for source, successors in enumerate(adjacency):
        if any(rank[source] <= rank[target] for target in successors):
            raise AssertionError("constructed potential is not strictly decreasing")
    rank_digest = hashlib.sha256()
    for (step, site), value in zip(nodes, rank):
        rank_digest.update(struct.pack("<5i", step, *site, value))
    return {
        "nodes": len(nodes),
        "edges": edges,
        "edge_stream_sha256": edge_digest.hexdigest(),
        "acyclic": True,
        "kahn_residual_vertices": 0,
        "cycle": None,
        "strict_vertex_potential": {
            "definition": "rank(v)=maximum number of policy edges from v to a sink",
            "maximum": max(rank, default=0),
            "strictly_decreases_on_every_edge": True,
            "stream_sha256": rank_digest.hexdigest(),
        },
    }


def atomic_json_dump(value, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=output_path.name + ".", dir=output_path.parent
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
        os.replace(temporary, output_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run(metadata_path, cache_path, nonx_path):
    started = time.monotonic()
    checker_sha256 = file_sha256(Path(__file__).resolve())
    policy = resource_policy()
    commitments = verify_inputs(metadata_path, cache_path, nonx_path)
    with Path(metadata_path).open() as handle:
        metadata = json.load(handle)
    with Path(nonx_path).open() as handle:
        nonx = json.load(handle)
    cycle_edges = canonical_two_cycle(nonx)
    scan = scan_domains(metadata, cache_path, cycle_edges)
    graph = build_policy_graph(scan["candidate_sites"], scan["chosen"])

    policy_records = []
    for step, (ordinal, action) in enumerate(
        zip(scan["chosen_ordinals"], scan["chosen"])
    ):
        policy_records.append({
            "step": step,
            "ordinal_1_based": ordinal,
            "word": list(action["word"]),
            "interiors": [list(point) for point in action["interiors"]],
        })
    if file_sha256(Path(__file__).resolve()) != checker_sha256:
        raise RuntimeError("checker changed during exact scan")

    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact fixed-word non-x degenerate-site policy probe",
        "checker": {
            "path": "design/nonx_fixed_word_policy_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "pinned_input_sha256": commitments,
        "scope": {
            "full_domain_candidate_sites": sum(
                len(sites) for sites in scan["candidate_sites"]
            ),
            "effective_words_scanned": scan["word_count"],
            "ordered_word_slots_scanned": scan["slot_count"],
            "policy": (
                "one fixed whole word per step: first cached word with "
                "pairwise-distinct interior yz fibres avoiding both endpoint fibres"
            ),
            "edge_semantics": (
                "(s,x)->(t,M(x-c)) for an ordered slot (t,c) of the one "
                "selected source word, provided that word avoids x and the "
                "target is a full-domain candidate site"
            ),
        },
        "canonical_step_one_two_cycle_audit": {
            "edge_requirements": [
                {
                    key: list(value) if isinstance(value, tuple) else value
                    for key, value in edge.items()
                }
                for edge in cycle_edges
            ],
            **scan["step_one_audit"],
            "conclusion": (
                "no single step-1 word supports both canonical directions; "
                "the first intrinsic projection-compatible word avoids both "
                "cycle sites and supports neither edge"
            ),
        },
        "fixed_policy": {
            "selected_ordinal_range": [
                min(scan["chosen_ordinals"]),
                max(scan["chosen_ordinals"]),
            ],
            "steps_whose_selected_ordinal_exceeds_one": sum(
                ordinal > 1 for ordinal in scan["chosen_ordinals"]
            ),
            "record_stream_sha256": stable_hash(policy_records),
            "records": policy_records,
        },
        "policy_graph": graph,
        "proved_by_this_probe": [
            "whole-word source correlations are retained: all active slots at one source come from its single selected word",
            "the exact full-domain candidate-site universe from the pinned cache is retained",
            "the selected word avoids every carried site from which it has an outgoing compatibility edge",
            "if emitted, the integer potential is checked to decrease strictly on every exact policy edge",
        ],
        "not_proved": [
            "global connector legality or positive availability",
            "global empty-yz-fibre compatibility; only the intrinsic endpoint-fibre condition is checked",
            "reachability of every retained poison node or a state-dependent safety policy",
            "nondegenerate selector edges, empty-effect re-entry, cursor jumps, births, or a far-secant theorem",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_set_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--nonx", default=DEFAULT_NONX)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run(args.metadata, args.cache, args.nonx)
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "policy_graph": payload["policy_graph"],
        "step_one": payload["canonical_step_one_two_cycle_audit"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_set_raw": payload["maximum_resident_set_raw"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
