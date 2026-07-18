#!/usr/bin/env python3
"""Exact L8 -> L9 anchor-only far-secant incidence audit.

This checker does *not* construct an L9 connector walk.  It takes the completed
L8 path, applies ``M_BAL3`` to obtain the L9 anchor skeleton, and promotes the
three tagged L7 connector points from age one to age two.  Every L9 anchor is
present before any L9 stitch, so an incidence found here is a genuine legality
witness in every later L9 prefix, although it may be redundant with poison from
other points.  The audit covers, without an endpoint cutoff:

* a tagged endpoint colliding with a candidate interior site;
* a tagged endpoint lying on a line through two candidate interiors; and
* a candidate interior site lying on a secant through a tagged endpoint and
  any other L9 anchor.

The result is deliberately an under-approximation incidence audit.  It omits all L9
connector interiors, hence in particular current-age (age-zero) partners.  It
tracks stable point identities, birth ancestry, corridor endpoints, and signed
ordered-path offsets, so it does not manufacture independent address streams.
The reported witness channels overlap: a word or atom may have collision,
candidate-line, and secant witnesses simultaneously.  No channel count is an
incremental killed-word or availability contribution.

The emitted type graph is also deliberately literal.  It contains exact
age-one-to-age-two endpoint-promotion edges and exact age-two-incidence edges.
Its SCC census is a diagnostic of that witnessed one-step graph, not a finite
tail quotient.  An age-erased endpoint projection is reported separately; its
three expected self-loops merely say that physical endpoints persist and must
not be ranked away by age alone.  A proof-grade projective/Pluecker quotient,
universal Post relation, and effectful SCC-promotion closure remain explicit
TODOs rather than being inferred from this finite scan.

Run the exact audit on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l9_anchor_tail_falsifier.py run \
        --output /tmp/l9-anchor-tail-falsifier.json

A cheap structural estimate, subject to the same resource policy, is available as:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/l9_anchor_tail_falsifier.py estimate
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import IDX, MENU, load_domains  # noqa: E402
from imbricate193 import apply  # noqa: E402
from salvage_gate import add, cross, line_key, primitive, sub  # noqa: E402


SOURCE_LEVEL = 7
PARENT_LEVEL = 8
TARGET_LEVEL = 9
TAGGED_STABLE_IDS = (
    "connector:L7:G12291:I1",
    "connector:L7:G12324:I2",
    "connector:L7:G19950:I2",
)

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

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
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
    "design/salvage_gate.py": (
        "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
    ),
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def as_json(value):
    if isinstance(value, tuple):
        return [as_json(item) for item in value]
    if isinstance(value, list):
        return [as_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_json(item) for key, item in value.items()}
    return value


def stable_bytes(value):
    return json.dumps(
        as_json(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def load_viz():
    return json.loads((ROOT / "viz/walk3d-data.json").read_text())


def build_path_origins(viz):
    """Recover the exact stable birth identity of every L0--L8 point."""
    points_by_level = {
        level: [tuple(point) for point in data["points"]]
        for level, data in enumerate(viz["levels"])
    }
    origins = {
        0: [
            {
                "stable_id": f"base:L0:P{index}",
                "birth_level": 0,
                "birth_gap": None,
                "interior_ordinal": None,
                "birth_parent_endpoint_stable_ids": [],
            }
            for index in range(len(points_by_level[0]))
        ]
    }
    for level in range(1, len(viz["levels"])):
        parents = viz["levels"][level]["parents"]
        assert len(parents) == len(points_by_level[level])
        block_start = {}
        current = []
        for index, parent in enumerate(parents):
            first = index == 0 or parents[index - 1] != parent
            if first:
                block_start[parent] = index
                assert points_by_level[level][index] == apply(
                    M_BAL3, points_by_level[level - 1][parent]
                )
                current.append(dict(origins[level - 1][parent]))
            else:
                ordinal = index - block_start[parent]
                current.append({
                    "stable_id": f"connector:L{level}:G{parent}:I{ordinal}",
                    "birth_level": level,
                    "birth_gap": parent,
                    "interior_ordinal": ordinal,
                    "birth_parent_endpoint_stable_ids": [
                        origins[level - 1][parent]["stable_id"],
                        origins[level - 1][parent + 1]["stable_id"],
                    ],
                })
        stable_ids = [record["stable_id"] for record in current]
        assert len(stable_ids) == len(set(stable_ids))
        origins[level] = current
    return points_by_level, origins


def compact_domain_model(domain, step):
    """Build and endpoint-validate a domain without retaining word clauses."""
    site_id = {}
    line_id = {}
    atom_desc = []
    expected_endpoint = apply(M_BAL3, MENU[step])

    def add_site(offset):
        if offset not in site_id:
            site_id[offset] = len(atom_desc)
            atom_desc.append(("site", offset))

    def add_line(key):
        if key not in line_id:
            line_id[key] = len(atom_desc)
            atom_desc.append(("line", key))

    for word_index, word in enumerate(domain):
        position = (0, 0, 0)
        offsets = []
        for ordinal, menu_index in enumerate(word):
            position = add(position, MENU[menu_index])
            if ordinal + 1 < len(word):
                offsets.append(position)
        assert position == expected_endpoint, (
            "connector domain word has the wrong scaled endpoint",
            step,
            word_index,
            word,
            position,
            expected_endpoint,
        )
        for offset in offsets:
            add_site(offset)
        for left, first in enumerate(offsets):
            for second in offsets[left + 1 :]:
                add_line(line_key(first, second))

    line_by_direction = defaultdict(dict)
    for (direction, moment), atom in line_id.items():
        line_by_direction[direction][moment] = atom
    return {
        "site_id": site_id,
        "line_id": line_id,
        "line_by_direction": dict(line_by_direction),
        "atom_desc": atom_desc,
        "validated_domain_words": len(domain),
        "expected_scaled_endpoint": expected_endpoint,
    }


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "exact run requires all thread-cap environment variables to equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify nice level on this platform")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 15:
        raise RuntimeError(
            f"run under `nice -n 15`; observed process nice value is {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def endpoint_record(stable_id, index, point8, point9, origin):
    assert origin["stable_id"] == stable_id
    assert origin["birth_level"] == SOURCE_LEVEL
    return {
        "stable_id": stable_id,
        "l8_path_index_and_l9_anchor_index": index,
        "l8_coordinate": as_json(point8),
        "l9_coordinate": as_json(point9),
        "birth_level": origin["birth_level"],
        "age_at_l8": PARENT_LEVEL - origin["birth_level"],
        "age_at_l9": TARGET_LEVEL - origin["birth_level"],
        "birth_gap": origin["birth_gap"],
        "interior_ordinal": origin["interior_ordinal"],
        "birth_parent_endpoint_stable_ids": origin[
            "birth_parent_endpoint_stable_ids"
        ],
    }


def point_profile(index, anchors9, origins8):
    origin = origins8[index]
    return {
        "stable_id": origin["stable_id"],
        "l8_path_index_and_l9_anchor_index": index,
        "l9_coordinate": as_json(anchors9[index]),
        "birth_level": origin["birth_level"],
        "age_at_l9": TARGET_LEVEL - origin["birth_level"],
        "birth_gap": origin["birth_gap"],
        "interior_ordinal": origin["interior_ordinal"],
        "birth_parent_endpoint_stable_ids": origin[
            "birth_parent_endpoint_stable_ids"
        ],
    }


def corridor_profile(gap, step, anchors9, origins8, parents8):
    return {
        "l9_gap": gap,
        "parent_step": step,
        "l9_start": as_json(anchors9[gap]),
        "l9_end": as_json(anchors9[gap + 1]),
        "ordered_endpoint_stable_ids": [
            origins8[gap]["stable_id"], origins8[gap + 1]["stable_id"]
        ],
        "l8_connector_owner_parent_index": parents8[gap],
        "l8_parent_indices_of_ordered_endpoints": [
            parents8[gap], parents8[gap + 1]
        ],
    }


def make_occurrence(
    *,
    channel,
    atom,
    atom_desc,
    endpoint,
    partner,
    corridor,
    endpoint_relative,
    partner_relative=None,
    candidate_site=None,
    absolute_line=None,
):
    gap = corridor["l9_gap"]
    endpoint_index = endpoint["l8_path_index_and_l9_anchor_index"]
    partner_index = (
        None if partner is None
        else partner["l8_path_index_and_l9_anchor_index"]
    )
    ordered_correlation = {
        "endpoint_minus_corridor_gap": endpoint_index - gap,
        "partner_minus_corridor_gap": (
            None if partner_index is None else partner_index - gap
        ),
        "corridor_endpoint_stable_ids": corridor[
            "ordered_endpoint_stable_ids"
        ],
        "l8_connector_owner_parent_index": corridor[
            "l8_connector_owner_parent_index"
        ],
        "l8_parent_indices_of_corridor_endpoints": corridor[
            "l8_parent_indices_of_ordered_endpoints"
        ],
    }
    literal_type = {
        "schema": "literal-L9-anchor-incidence-v1",
        "channel": channel,
        "source_stable_id": endpoint["stable_id"],
        "partner_stable_id": None if partner is None else partner["stable_id"],
        "corridor_gap": gap,
        "parent_step": corridor["parent_step"],
        "atom": as_json(atom_desc),
        "endpoint_relative": as_json(endpoint_relative),
        "partner_relative": as_json(partner_relative),
        "ordered_correlation": ordered_correlation,
    }
    diagnostic_type = {
        "schema": "diagnostic-local-incidence-v1-not-a-Post-quotient",
        "channel": channel,
        "parent_step": corridor["parent_step"],
        "atom": as_json(atom_desc),
        "endpoint_birth_level": endpoint["birth_level"],
        "endpoint_age": endpoint["age_at_l9"],
        "partner_birth_level": (
            None if partner is None else partner["birth_level"]
        ),
        "partner_age": None if partner is None else partner["age_at_l9"],
        "endpoint_relative": as_json(endpoint_relative),
        "partner_relative": as_json(partner_relative),
        "signed_ordered_offsets": [
            ordered_correlation["endpoint_minus_corridor_gap"],
            ordered_correlation["partner_minus_corridor_gap"],
        ],
    }
    return {
        "channel": channel,
        "atom_id": atom,
        "atom": as_json(atom_desc),
        "endpoint": endpoint,
        "partner": partner,
        "corridor": corridor,
        "endpoint_relative": as_json(endpoint_relative),
        "partner_relative": as_json(partner_relative),
        "candidate_site_coordinate": as_json(candidate_site),
        "absolute_witness_line": as_json(absolute_line),
        "ordered_ancestry_correlation": ordered_correlation,
        "literal_type_sha256": stable_hash(literal_type),
        "literal_type": literal_type,
        "diagnostic_type_sha256": stable_hash(diagnostic_type),
        "diagnostic_type": diagnostic_type,
    }


def direction_index(endpoint, anchors9):
    index = {}
    endpoint_coordinate = tuple(endpoint["l9_coordinate"])
    digest = hashlib.sha256()
    for point_index, point in enumerate(anchors9):
        if point == endpoint_coordinate:
            continue
        direction = primitive(sub(point, endpoint_coordinate))
        assert direction is not None
        assert direction not in index, (
            "three collinear L9 anchors through tagged endpoint",
            endpoint["stable_id"],
            direction,
            index.get(direction),
            point_index,
        )
        index[direction] = point_index
    for direction, point_index in sorted(index.items()):
        digest.update(stable_bytes((direction, point_index, anchors9[point_index])))
        digest.update(b"\n")
    return index, digest.hexdigest()


def scan_endpoint_step(
    endpoint,
    directions,
    anchors9,
    origins8,
    parents8,
    gap_indices,
    step,
    model,
    progress,
):
    """Scan one endpoint on the gaps of one exact parent-step model."""
    endpoint_coordinate = tuple(endpoint["l9_coordinate"])
    endpoint_index = endpoint["l8_path_index_and_l9_anchor_index"]
    occurrences = []

    for gap in gap_indices:
        before = len(occurrences)
        start = anchors9[gap]
        relative = sub(endpoint_coordinate, start)
        corridor = corridor_profile(
            gap, step, anchors9, origins8, parents8
        )

        collision_atom = model["site_id"].get(relative)
        if collision_atom is not None:
            occurrences.append(make_occurrence(
                channel="collision",
                atom=collision_atom,
                atom_desc=model["atom_desc"][collision_atom],
                endpoint=endpoint,
                partner=None,
                corridor=corridor,
                endpoint_relative=relative,
                candidate_site=endpoint_coordinate,
            ))

        for candidate_direction, by_moment in model[
            "line_by_direction"
        ].items():
            line_atom = by_moment.get(cross(relative, candidate_direction))
            if line_atom is None:
                continue
            line_description = model["atom_desc"][line_atom]
            assert line_description[0] == "line"
            local_direction, local_moment = line_description[1]
            assert local_direction == candidate_direction
            start_moment = cross(start, local_direction)
            absolute_candidate_line = (
                local_direction,
                tuple(
                    start_moment[axis] + local_moment[axis]
                    for axis in range(3)
                ),
            )
            assert cross(endpoint_coordinate, local_direction) == (
                absolute_candidate_line[1]
            )
            occurrences.append(make_occurrence(
                channel="endpoint-on-candidate-line",
                atom=line_atom,
                atom_desc=line_description,
                endpoint=endpoint,
                partner=None,
                corridor=corridor,
                endpoint_relative=relative,
                absolute_line=absolute_candidate_line,
            ))

        for offset, site_atom in model["site_id"].items():
            query = add(start, offset)
            if query == endpoint_coordinate:
                continue
            query_direction = primitive(sub(query, endpoint_coordinate))
            assert query_direction is not None
            partner_index = directions.get(query_direction)
            if partner_index is None:
                continue
            partner_coordinate = anchors9[partner_index]
            if partner_coordinate == query:
                # This candidate site is already an anchor.  It is a collision,
                # not a distinct tagged--anchor secant witness.
                continue
            assert partner_index != endpoint_index
            assert len({endpoint_coordinate, partner_coordinate, query}) == 3
            absolute = line_key(endpoint_coordinate, partner_coordinate)
            assert cross(query, absolute[0]) == absolute[1]
            partner = point_profile(partner_index, anchors9, origins8)
            channel = (
                "tagged-tagged-anchor-secant"
                if partner["stable_id"] in TAGGED_STABLE_IDS
                else "tagged-other-anchor-secant"
            )
            occurrences.append(make_occurrence(
                channel=channel,
                atom=site_atom,
                atom_desc=model["atom_desc"][site_atom],
                endpoint=endpoint,
                partner=partner,
                corridor=corridor,
                endpoint_relative=relative,
                partner_relative=sub(partner_coordinate, start),
                candidate_site=query,
                absolute_line=absolute,
            ))

        progress["scanned"] += 1
        progress["occurrences"] += len(occurrences) - before
        if (
            progress["scanned"] % 25_000 == 0
            or progress["scanned"] == progress["total"]
        ):
            print(
                f"{endpoint['stable_id']}: scanned {progress['scanned']}/"
                f"{progress['total']} L9 anchor corridors; "
                f"occurrences {progress['occurrences']}",
                flush=True,
            )

    occurrences.sort(key=lambda record: (
        record["corridor"]["l9_gap"],
        record["channel"],
        record["atom_id"],
        "" if record["partner"] is None else record["partner"]["stable_id"],
    ))
    return occurrences


def strongly_connected_components(nodes, edges):
    adjacency = {node: set() for node in nodes}
    self_loops = set()
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set())
        if source == target:
            self_loops.add(source)

    index = 0
    indices = {}
    lowlink = {}
    stack = []
    on_stack = set()
    components = []

    def visit(node):
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in sorted(adjacency[node]):
            if successor not in indices:
                visit(successor)
                lowlink[node] = min(lowlink[node], lowlink[successor])
            elif successor in on_stack:
                lowlink[node] = min(lowlink[node], indices[successor])
        if lowlink[node] == indices[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(tuple(sorted(component)))

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)

    components.sort()
    cyclic = [
        component for component in components
        if len(component) > 1 or component[0] in self_loops
    ]
    return {
        "nodes": len(adjacency),
        "edges": len(set(edges)),
        "components": len(components),
        "cyclic_components": len(cyclic),
        "cyclic_component_records": [list(component) for component in cyclic],
        "component_stream_sha256": stable_hash(components),
    }


def build_graph_diagnostics(endpoints, occurrences):
    exact_nodes = set()
    exact_edges = set()
    projected_nodes = set()
    projected_edges = set()
    promotion_records = []
    incidence_groups = defaultdict(list)
    type_definitions = {}
    type_counts = Counter(
        record["diagnostic_type_sha256"] for record in occurrences
    )

    for endpoint in endpoints:
        stable_id = endpoint["stable_id"]
        age1 = f"endpoint:{stable_id}:age1"
        age2 = f"endpoint:{stable_id}:age2"
        exact_nodes.update((age1, age2))
        exact_edges.add((age1, age2))
        promotion_records.append({
            "source": age1,
            "target": age2,
            "kind": "exact-affine-endpoint-promotion",
            "l8_coordinate": endpoint["l8_coordinate"],
            "l9_coordinate": endpoint["l9_coordinate"],
            "matrix": as_json(M_BAL3),
        })

        frontier = f"endpoint-frontier:{stable_id}:age-erased"
        projected_nodes.add(frontier)
        projected_edges.add((frontier, frontier))

    for record in occurrences:
        stable_id = record["endpoint"]["stable_id"]
        type_node = "incidence-type:" + record["diagnostic_type_sha256"]
        type_definitions.setdefault(
            record["diagnostic_type_sha256"], record["diagnostic_type"]
        )
        assert type_definitions[record["diagnostic_type_sha256"]] == (
            record["diagnostic_type"]
        )
        incidence_groups[(stable_id, type_node)].append(record)
        exact_nodes.add(type_node)
        exact_edges.add((f"endpoint:{stable_id}:age2", type_node))
        projected_nodes.add(type_node)
        projected_edges.add((
            f"endpoint-frontier:{stable_id}:age-erased", type_node
        ))

    incidence_edge_records = []
    for (stable_id, type_node), records in sorted(incidence_groups.items()):
        incidence_edge_records.append({
            "source": f"endpoint:{stable_id}:age2",
            "target": type_node,
            "kind": "exact-observed-age2-anchor-incidence",
            "occurrences": len(records),
            "l9_gaps": sorted({
                record["corridor"]["l9_gap"] for record in records
            }),
            "literal_witness_type_stream_sha256": stable_hash(sorted(
                record["literal_type_sha256"] for record in records
            )),
        })

    return {
        "semantics": (
            "the exact witnessed graph contains only affine age1-to-age2 "
            "promotion and age2-to-observed-incidence edges; it is not a "
            "universal residual Post graph"
        ),
        "proof_grade_type_quotient": None,
        "proof_grade_residual_rank": None,
        "exact_age_specific_witness_graph": strongly_connected_components(
            exact_nodes, exact_edges
        ),
        "witnessed_promotion_edges": promotion_records,
        "witnessed_incidence_edges": incidence_edge_records,
        "witnessed_edge_stream_sha256": stable_hash(
            promotion_records + incidence_edge_records
        ),
        "diagnostic_type_definitions": [
            {
                "type_sha256": type_hash,
                "definition": definition,
            }
            for type_hash, definition in sorted(type_definitions.items())
        ],
        "age_erased_frontier_projection": {
            "warning": (
                "the three self-loops express physical endpoint persistence; "
                "they require promotion in this coarse identity quotient but "
                "are not effectful projective-incidence cycles"
            ),
            **strongly_connected_components(projected_nodes, projected_edges),
        },
        "diagnostic_incidence_types": {
            "types": len(type_counts),
            "singleton_types": sum(count == 1 for count in type_counts.values()),
            "maximum_occurrences_per_type": max(type_counts.values(), default=0),
            "size_histogram": dict(sorted(Counter(type_counts.values()).items())),
            "type_count_stream_sha256": stable_hash(sorted(type_counts.items())),
        },
        "todo_boundary": (
            "before an SCC can certify or refute the proposed tail rank, define "
            "and prove a finite point/Pluecker/address quotient, a universal "
            "concretization, and witness-compatible Post edges across every "
            "retained ordered transition; no such quotient is invented here"
        ),
    }


def structural_data(viz):
    points8 = [tuple(point) for point in viz["levels"][PARENT_LEVEL]["points"]]
    parents8 = viz["levels"][PARENT_LEVEL]["parents"]
    assert len(points8) == len(parents8) == 311_738
    steps = []
    for first, second in zip(points8, points8[1:]):
        delta = sub(second, first)
        assert delta in IDX
        steps.append(IDX[delta])
    assert len(steps) == 311_737
    return points8, parents8, steps


def estimate():
    resource_policy = enforce_resource_policy()
    viz = load_viz()
    points8, _parents8, steps = structural_data(viz)
    return {
        "status": "structural estimate only; no domains or incidences scanned",
        "resource_policy": resource_policy,
        "completed_l8_points": len(points8),
        "l9_anchor_corridors": len(steps),
        "effective_step_types": len(set(steps)),
        "tagged_endpoints": len(TAGGED_STABLE_IDS),
        "planned_direction_index_entries": len(TAGGED_STABLE_IDS) * (
            len(points8) - 1
        ),
        "scope": "L9 transformed-anchor partners only; no L9 connector interiors",
    }


def run(output_path):
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resource_policy = enforce_resource_policy()
    started = time.time()

    observed_inputs = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_inputs == EXPECTED_INPUT_SHA256

    viz = load_viz()
    points_by_level, origins = build_path_origins(viz)
    points8, parents8, step_by_gap = structural_data(viz)
    assert points_by_level[PARENT_LEVEL] == points8
    origins8 = origins[PARENT_LEVEL]
    anchors9 = [apply(M_BAL3, point) for point in points8]
    assert len(anchors9) == len(set(anchors9)) == len(points8)

    stable_to_index = {
        origin["stable_id"]: index for index, origin in enumerate(origins8)
    }
    assert len(stable_to_index) == len(origins8)
    endpoints = []
    for stable_id in TAGGED_STABLE_IDS:
        index = stable_to_index[stable_id]
        endpoint = endpoint_record(
            stable_id,
            index,
            points8[index],
            anchors9[index],
            origins8[index],
        )
        assert endpoint["age_at_l8"] == 1
        assert endpoint["age_at_l9"] == 2
        assert tuple(endpoint["l9_coordinate"]) == apply(
            M_BAL3, tuple(endpoint["l8_coordinate"])
        )
        endpoints.append(endpoint)

    completed_l8_points = len(points8)
    total_corridors = len(step_by_gap)
    gaps_by_step = defaultdict(list)
    for gap, step in enumerate(step_by_gap):
        gaps_by_step[step].append(gap)
    present_steps = sorted(gaps_by_step)

    direction_indexes = {}
    direction_summaries = []
    scan_progress = {}
    for endpoint in endpoints:
        print(f"indexing anchor directions from {endpoint['stable_id']}", flush=True)
        directions, direction_hash = direction_index(endpoint, anchors9)
        direction_indexes[endpoint["stable_id"]] = directions
        direction_summaries.append({
            "stable_id": endpoint["stable_id"],
            "directions": len(directions),
            "direction_index_sha256": direction_hash,
        })
        scan_progress[endpoint["stable_id"]] = {
            "scanned": 0,
            "total": total_corridors,
            "occurrences": 0,
        }

    # The scan needs only L8 origins, parent labels, transformed anchors, and
    # the three direction indexes.  Release all other level/viz copies before
    # materializing the much larger connector-domain collection.
    del stable_to_index, points_by_level, origins, viz, points8, step_by_gap
    gc.collect()

    domains, _d24 = load_domains()
    assert set(present_steps) == set(domains), (
        "every loaded domain must occur as an L9 parent-step type so the run "
        "validates every loaded word",
        sorted(set(domains) - set(present_steps)),
        sorted(set(present_steps) - set(domains)),
    )
    total_domain_words = sum(len(domain) for domain in domains.values())
    model_census = []
    all_occurrences = []
    for ordinal, step in enumerate(present_steps, 1):
        domain = domains.pop(step)
        print(
            f"building exact atom model {ordinal}/{len(present_steps)} "
            f"for step {step} ({len(domain)} words)",
            flush=True,
        )
        model = compact_domain_model(domain, step)
        assert model["validated_domain_words"] == len(domain)
        model_census.append({
            "step": step,
            "domain_words": len(domain),
            "all_words_end_at_scaled_parent_step": True,
            "expected_scaled_endpoint": as_json(
                model["expected_scaled_endpoint"]
            ),
            "sites": len(model["site_id"]),
            "lines": len(model["line_id"]),
            "directions": len(model["line_by_direction"]),
            "atoms": len(model["atom_desc"]),
            "atom_description_sha256": stable_hash(model["atom_desc"]),
        })

        for endpoint in endpoints:
            stable_id = endpoint["stable_id"]
            occurrences = scan_endpoint_step(
                endpoint,
                direction_indexes[stable_id],
                anchors9,
                origins8,
                parents8,
                gaps_by_step[step],
                step,
                model,
                scan_progress[stable_id],
            )
            all_occurrences.extend(occurrences)

        step_gaps = len(gaps_by_step[step])
        del model, domain
        gc.collect()
        print(
            f"completed step {ordinal}/{len(present_steps)}: step {step}, "
            f"gaps {step_gaps}, cumulative occurrences {len(all_occurrences)}",
            flush=True,
        )
    assert not domains
    assert all(
        progress["scanned"] == total_corridors
        for progress in scan_progress.values()
    )
    l9_anchor_count = len(anchors9)
    del domains, direction_indexes, scan_progress, gaps_by_step, _d24
    del anchors9, origins8, parents8
    gc.collect()

    all_occurrences.sort(key=lambda record: (
        record["endpoint"]["stable_id"],
        record["corridor"]["l9_gap"],
        record["channel"],
        record["atom_id"],
        "" if record["partner"] is None else record["partner"]["stable_id"],
    ))
    occurrence_hash = stable_hash(all_occurrences)
    channel_counts = Counter(record["channel"] for record in all_occurrences)
    incidence_gaps = sorted({
        record["corridor"]["l9_gap"] for record in all_occurrences
    })
    endpoint_counts = Counter(
        record["endpoint"]["stable_id"] for record in all_occurrences
    )
    partner_ages = Counter(
        record["partner"]["age_at_l9"]
        for record in all_occurrences if record["partner"] is not None
    )
    graph = build_graph_diagnostics(endpoints, all_occurrences)

    result = {
        "status": (
            "exact L8-to-L9 anchor-only age2 endpoint-incidence extraction; "
            "under-approximation incidence audit, not an incremental-poison "
            "test, tail theorem, or SCC rank"
        ),
        "resource_policy": {
            **resource_policy,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "input_sha256": observed_inputs,
        "scope": {
            "completed_l8_points": completed_l8_points,
            "l9_anchors": l9_anchor_count,
            "l9_anchor_corridors": total_corridors,
            "effective_step_types": len(present_steps),
            "tagged_endpoints": len(endpoints),
            "endpoint_cutoff": None,
            "distance_cutoff": None,
            "included_partners": (
                "every transformed completed-L8 point, including age1 anchors "
                "born as L8 connector interiors"
            ),
            "covered_roles": [
                "tagged endpoint collides with a candidate interior site",
                "tagged endpoint lies on a line through two candidate interiors",
                "candidate interior site lies on a tagged--other L9-anchor secant",
            ],
            "omitted": [
                "every untagged age>=2 endpoint as a source",
                "all current-age L9 connector interiors",
                "all alternate L9 connector histories",
                "word-mask union and connector availability",
                "a universal projective/Pluecker type quotient",
                "future levels after the anchor-only L9 skeleton",
            ],
            "underapproximation_logic": (
                "all L9 anchors exist before every L9 stitch, so every reported "
                "incidence is genuine but may be redundant with other poison; "
                "an absent incidence is not evidence that omitted L9 connector "
                "partners cannot reactivate the endpoint"
            ),
        },
        "promoted_endpoints": endpoints,
        "direction_indexes": direction_summaries,
        "domain_models": {
            "models": model_census,
            "model_census_sha256": stable_hash(model_census),
            "total_domain_words": total_domain_words,
            "models_built_scanned_and_released_one_step_at_a_time": True,
        },
        "exact_anchor_incidences": {
            "occurrences": len(all_occurrences),
            "incidence_gaps": len(incidence_gaps),
            "zero_incidence_gaps": total_corridors - len(incidence_gaps),
            "channel_semantics": (
                "overlapping witness-provenance channels; counts are neither "
                "disjoint nor incremental killed-word/availability effects"
            ),
            "channel_counts": dict(sorted(channel_counts.items())),
            "endpoint_counts": dict(sorted(endpoint_counts.items())),
            "partner_age_histogram": dict(sorted(partner_ages.items())),
            "incidence_gap_list": incidence_gaps,
            "occurrence_stream_sha256": occurrence_hash,
            "records": all_occurrences,
        },
        "witnessed_type_edge_scc_diagnostics": graph,
        "incidence_semantics": {
            "incidence_only_conclusion_if_nonempty": (
                "the records refute only a literal lemma declaring that these "
                "three actual endpoints have no anchor-only candidate incidence "
                "after reaching age2"
            ),
            "identity_projection_result": (
                "the age-erased endpoint self-loops are exact persistence SCCs "
                "and must be promoted in that coarse quotient"
            ),
            "not_an_incremental_poison_or_rank_falsifier": (
                "a finite age2 incidence may be redundant and does not by itself "
                "change a killed-word mask or availability, or refute a finer "
                "geometry-aware residual rank; a genuine effectful transition "
                "cycle still needs a sound quotient and compatible edges"
            ),
            "negative_result_warning": (
                "zero records would be finite negative evidence only, because "
                "this scan omits current L9 connectors"
            ),
        },
        "proof_boundary": {
            "proved_by_this_finite_checker": [
                "exact affine promotion of the three stable endpoints to age2",
                "complete all-corridor/all-domain atom-role extraction involving "
                "those endpoints and transformed completed-L8 anchor partners",
                "exact ordered ancestry and partner identity for every witness",
            ],
            "not_proved": [
                "a finite transition-congruent residual type system",
                "a sound universal Post relation over alternate histories",
                "SCC promotion closure or a strict residual rank",
                "nonfatality after all near and far poison is unioned",
                "an unconditional Erdos #193 theorem",
            ],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps({
            "output": str(output_path),
            "bytes": output_path.stat().st_size,
            "occurrences": len(all_occurrences),
            "incidence_gaps": len(incidence_gaps),
            "channels": dict(sorted(channel_counts.items())),
            "occurrence_stream_sha256": occurrence_hash,
        }, sort_keys=True),
        flush=True,
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/l9-anchor-tail-falsifier.json"),
    )
    arguments = parser.parse_args()
    if arguments.mode == "estimate":
        print(json.dumps(estimate(), indent=2, sort_keys=True))
    else:
        run(arguments.output)


if __name__ == "__main__":
    main()
