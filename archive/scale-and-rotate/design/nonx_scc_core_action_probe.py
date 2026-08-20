#!/usr/bin/env python3
"""Exact whole-word filters from the balanced-ternary image lattice.

Every direction-blind transition has target site ``M(x-c)`` and therefore
lands in ``L=M Z^3``.  Hence every directed cycle is contained in the finite
candidate envelope ``T={(s,x): x in C_s intersect L}``.

This checker emits two arbitrary-switching-safe whole-word regions:

* zero-envelope: a word induces no edge whose source lies in T;
* ordered-envelope: every such edge follows one common topological order of
  the pinned fixed-policy graph restricted to T.

For either filter, a source covered by the same word's proper interiors is
removed before testing.  Slots and avoidance masks are never spliced across
words.

Run ``estimate`` and ``self-check`` first.  Exact scans are split into the
disjoint source-step chunks 0--60 and 61--123 and merged afterward.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import itertools
import json
import mmap
import os
import resource
import struct
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_FIXED_POLICY = Path("/tmp/nonx-fixed-word-policy-probe-v2.json")
DEFAULT_PREPARED = Path("/tmp/nonx-potential-compatible-word-prepared.json")
DEFAULT_OUTPUT = Path("/tmp/nonx-lattice-envelope-action-probe.json")
DEFAULT_BITSETS = Path("/tmp/nonx-lattice-envelope-action-probe-bitsets.bin")

EXPECTED_SHA256 = {
    "metadata": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
    "cache": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
    "fixed_policy": "e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e",
    "prepared": "5210a61f556573d39ad1ea2f3039bd5c36772b1fad4597d0920e5d6d9e6a28e1",
    "fixed_policy_checker": "531ba6ee0bfa8d5bf7485d70b13687ace4e1b100cdcdfd739b8bdcac9d8efdd3",
    "potential_checker": "21b84e6ef80c1b8184cb3c06f08d674983f10cd91759b204e1170186319b1062",
    "nonx_checker": "4eb928bad0c0104d34b68424b07dd3b6a4939f216968bd6b2399a540b592e755",
}
EXPECTED_BYTES = {
    "cache": 68_050_680,
    "prepared": 1_417_734,
    "fixed_policy": 42_537,
}
EXPECTED_WORDS = 12_537_146
EXPECTED_SLOTS = 55_513_526
EXPECTED_CANDIDATES = 34_520
EXPECTED_CANDIDATE_DIGEST = (
    "d3f5892f3edb518fcdad88457f04fddb4eb3cece48102cfbdd801353897e4e07"
)
EXPECTED_ENVELOPE_VERTICES = 780
EXPECTED_ENVELOPE_STEPS = 120
EXPECTED_ENVELOPE_RANGE = (0, 16)
EXPECTED_ENVELOPE_DIGEST = (
    "cb07c8c0f10f0de7d4032a346bd0a827d9dce554b777033b5c168108f4d3c09e"
)
EXPECTED_ENVELOPE_COUNT_DIGEST = (
    "020c60265370ea973927c7436a96d4b73e022332daec214ff619753f6f22a20e"
)
EXPECTED_ROLE_TYPES = 840_794
EXPECTED_ORDERED_PROJECTION_SIGNATURES = 291_414
EXPECTED_PROJECTION_ROLE_MASKS = 216_322
EXPECTED_DIGIT_SIMPLE_WORDS = 6_755_766
EXPECTED_LENGTH_HISTOGRAM = {2: 552, 3: 56_516, 4: 7_057_516, 5: 5_422_562}

CACHE_MAGIC = b"NOXLN001"
BITSET_MAGIC = b"NTACB001"
BITSET_SCHEMA = 1
SITE_RADIUS = 8
SITE_SIDE = 17
SITE_COUNT = SITE_SIDE**3
MENU_SIZE = 124
MAX_SECONDS = 120.0
MAX_WORK_SECONDS = 115.0
MAX_RESIDENT_BYTES = 280 * 1024 * 1024
ACTION_CHUNKS = ((0, 32), (33, 62), (63, 94), (95, 123))
DIRECT_ROLE_CHECKS_PER_STEP = 8

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
MENU_X = tuple(item[0] for item in MENU)
MENU_Y = tuple(item[1] for item in MENU)
MENU_Z = tuple(item[2] for item in MENU)
if len(MENU) != MENU_SIZE:
    raise AssertionError("menu size drift")


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def digest_integer_record(digest, values):
    for value in values:
        digest.update(int(value).to_bytes(8, "little", signed=True))


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce):
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in observed.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run requires all thread controls=1 and nice>=15", observed, nice
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": observed,
        "process_nice": nice,
        "required_minimum_nice": 15,
        "maximum_seconds": MAX_SECONDS,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


def enforce_runtime(started, phase):
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > MAX_WORK_SECONDS:
        raise RuntimeError("115-second work limit exceeded", phase, elapsed)
    if resident > MAX_RESIDENT_BYTES:
        raise MemoryError("280-MiB resident limit exceeded", phase, resident)


def file_snapshot(path):
    path = Path(path).resolve()
    stat = path.stat()
    return {
        "path": str(path),
        "sha256": file_sha256(path),
        "bytes": stat.st_size,
        "identity": [
            stat.st_dev,
            stat.st_ino,
            stat.st_size,
            stat.st_mtime_ns,
            stat.st_ctime_ns,
        ],
    }


def verify_snapshot_unchanged(snapshot):
    stat = Path(snapshot["path"]).stat()
    identity = [
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    ]
    if identity != snapshot["identity"] or file_sha256(snapshot["path"]) != (
        snapshot["sha256"]
    ):
        raise RuntimeError("input changed during exact work", snapshot["path"])


def apply_matrix(vector):
    x, y, z = vector
    return 3 * x, -3 * z, 3 * y - z


def in_image_lattice(vector):
    x, y, z = vector
    return x % 3 == 0 and y % 3 == 0 and (y - 3 * z) % 9 == 0


def exact_inverse_if_integral(vector):
    if not in_image_lattice(vector):
        return None
    x, y, z = vector
    result = x // 3, (z - y // 3) // 3, -y // 3
    if apply_matrix(result) != vector:
        raise AssertionError("image-lattice inverse drift", vector, result)
    return result


def encode_site(vector):
    x, y, z = vector
    if not all(-SITE_RADIUS <= item <= SITE_RADIUS for item in vector):
        raise ValueError("site escaped radius-eight box", vector)
    return (
        (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE
        + (y + SITE_RADIUS) * SITE_SIDE
        + z + SITE_RADIUS
    )


def maybe_encode_site(vector):
    if not all(-SITE_RADIUS <= item <= SITE_RADIUS for item in vector):
        return None
    return encode_site(vector)


def decode_site(encoded):
    if not 0 <= encoded < SITE_COUNT:
        raise ValueError("invalid site code", encoded)
    x_digit, remainder = divmod(encoded, SITE_SIDE * SITE_SIDE)
    y_digit, z_digit = divmod(remainder, SITE_SIDE)
    return x_digit - SITE_RADIUS, y_digit - SITE_RADIUS, z_digit - SITE_RADIUS


def packed_projection_signature(codes):
    if len(codes) > 4:
        raise AssertionError("too many proper lateral prefixes")
    packed = len(codes)
    for position, code in enumerate(codes):
        if not 0 <= code < SITE_SIDE * SITE_SIDE:
            raise AssertionError("lateral prefix code escaped range")
        packed |= (code + 1) << (3 + 9 * position)
    return packed


def iter_mask(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def quantiles(values):
    ordered = sorted(values)
    return {
        "minimum": ordered[0],
        "lower_quartile": ordered[len(ordered) // 4],
        "median": ordered[len(ordered) // 2],
        "upper_quartile": ordered[(3 * len(ordered)) // 4],
        "maximum": ordered[-1],
    }


def atomic_json_dump(value, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=output_path.parent, prefix=output_path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def input_snapshots(metadata_path, cache_path, fixed_policy_path, prepared_path):
    paths = {
        "metadata": Path(metadata_path),
        "cache": Path(cache_path),
        "fixed_policy": Path(fixed_policy_path),
        "prepared": Path(prepared_path),
        "fixed_policy_checker": ROOT / "design" / "nonx_fixed_word_policy_probe.py",
        "potential_checker": ROOT / "design" / "nonx_potential_compatible_word_probe.py",
        "nonx_checker": ROOT / "design" / "nonx_degenerate_site_graph.py",
    }
    snapshots = {name: file_snapshot(path) for name, path in paths.items()}
    observed = {name: item["sha256"] for name, item in snapshots.items()}
    if observed != EXPECTED_SHA256:
        raise AssertionError("pinned input drift", EXPECTED_SHA256, observed)
    for name, expected in EXPECTED_BYTES.items():
        if snapshots[name]["bytes"] != expected:
            raise AssertionError("pinned input byte-count drift", name)
    return snapshots


def load_metadata(path):
    with Path(path).open() as handle:
        payload = json.load(handle)
    blocks = sorted(
        payload["compact_domain_cache"]["blocks"], key=lambda item: item["step"]
    )
    if [item["step"] for item in blocks] != list(range(MENU_SIZE)):
        raise AssertionError("metadata block order drift")
    if sum(item["words"] for item in blocks) != EXPECTED_WORDS or sum(
        item["word_slots"] for item in blocks
    ) != EXPECTED_SLOTS:
        raise AssertionError("metadata cache census drift")
    return tuple(blocks)


def load_fixed_records(path):
    with Path(path).open() as handle:
        payload = json.load(handle)
    if payload["checker"]["sha256"] != EXPECTED_SHA256["fixed_policy_checker"]:
        raise AssertionError("fixed-policy/checker commitment drift")
    records = payload["fixed_policy"]["records"]
    if [record["step"] for record in records] != list(range(MENU_SIZE)):
        raise AssertionError("fixed-policy record order drift")
    if stable_hash(records) != payload["fixed_policy"]["record_stream_sha256"]:
        raise AssertionError("fixed-policy record digest drift")
    return tuple(records)


def load_candidates(path):
    with Path(path).open() as handle:
        payload = json.load(handle)
    if payload["checker"]["sha256"] != EXPECTED_SHA256["potential_checker"]:
        raise AssertionError("prepared/checker commitment drift")
    expected_pins = {
        name: EXPECTED_SHA256[name]
        for name in (
            "metadata", "cache", "fixed_policy", "fixed_policy_checker", "nonx_checker"
        )
    }
    if payload["pinned_input_sha256"] != expected_pins:
        raise AssertionError("prepared input commitment drift")
    rows_by_step = payload["candidate_rank_by_step"]
    if len(rows_by_step) != MENU_SIZE:
        raise AssertionError("prepared candidate step count drift")
    candidate_sites = []
    digest = hashlib.sha256()
    for step, rows in enumerate(rows_by_step):
        sites = tuple(row[0] for row in rows)
        if sites != tuple(sorted(set(sites))):
            raise AssertionError("prepared candidate order drift", step)
        if any(rank not in (0, 1, 2) for _site, rank in rows):
            raise AssertionError("prepared rank escaped height two", step)
        for site in sites:
            digest_integer_record(digest, (step, *decode_site(site)))
        candidate_sites.append(sites)
    if sum(map(len, candidate_sites)) != EXPECTED_CANDIDATES or (
        digest.hexdigest() != EXPECTED_CANDIDATE_DIGEST
    ):
        raise AssertionError("prepared candidate census/digest drift")
    return tuple(candidate_sites)


def fixed_actions(records, candidate_sets):
    actions = []
    for step, record in enumerate(records):
        word = tuple(record["word"])
        x = y = z = 0
        prefixes = []
        interiors = []
        for position, child in enumerate(word):
            prefixes.append((x, y, z))
            x += MENU_X[child]
            y += MENU_Y[child]
            z += MENU_Z[child]
            if position + 1 < len(word):
                site = encode_site((x, y, z))
                if site not in candidate_sets[step]:
                    raise AssertionError("fixed interior outside candidate set", step)
                interiors.append(site)
        if (x, y, z) != apply_matrix(MENU[step]):
            raise AssertionError("fixed word endpoint drift", step)
        if [list(decode_site(site)) for site in interiors] != record["interiors"]:
            raise AssertionError("fixed word interior record drift", step)
        actions.append({
            "word": word,
            "prefixes": tuple(prefixes),
            "interiors": frozenset(interiors),
            "ordinal": record["ordinal_1_based"],
        })
    return tuple(actions)


def build_envelope_and_order(candidate_sites, actions):
    envelope_by_step = tuple(tuple(
        site for site in sites if in_image_lattice(decode_site(site))
    ) for sites in candidate_sites)
    counts = tuple(map(len, envelope_by_step))
    digest = hashlib.sha256()
    nodes = []
    for step, sites in enumerate(envelope_by_step):
        for site in sites:
            vector = decode_site(site)
            digest_integer_record(digest, (step, *vector))
            nodes.append((step, site))
    if len(nodes) != EXPECTED_ENVELOPE_VERTICES or sum(bool(item) for item in counts) != (
        EXPECTED_ENVELOPE_STEPS
    ) or (min(counts), max(counts)) != EXPECTED_ENVELOPE_RANGE:
        raise AssertionError("lattice-envelope census drift", len(nodes), counts)
    if digest.hexdigest() != EXPECTED_ENVELOPE_DIGEST or hashlib.sha256(
        bytes(counts)
    ).hexdigest() != EXPECTED_ENVELOPE_COUNT_DIGEST:
        raise AssertionError("lattice-envelope digest drift")

    node_index = {
        step * SITE_COUNT + site: index for index, (step, site) in enumerate(nodes)
    }
    candidate_sets = tuple(frozenset(sites) for sites in candidate_sites)
    adjacency = [set() for _node in nodes]
    edge_digest = hashlib.sha256()
    for source_index, (step, site) in enumerate(nodes):
        action = actions[step]
        if site in action["interiors"]:
            continue
        source = decode_site(site)
        for target_step, control in zip(action["word"], action["prefixes"]):
            target = apply_matrix(tuple(
                source[axis] - control[axis] for axis in range(3)
            ))
            target_site = maybe_encode_site(target)
            if target_site is None or target_site not in candidate_sets[target_step]:
                continue
            if not in_image_lattice(target):
                raise AssertionError("edge target escaped image lattice")
            target_index = node_index[target_step * SITE_COUNT + target_site]
            adjacency[source_index].add(target_index)
    indegree = [0] * len(nodes)
    edges = 0
    for source, successors in enumerate(adjacency):
        for target in sorted(successors):
            indegree[target] += 1
            edges += 1
            source_step, source_site = nodes[source]
            target_step, target_site = nodes[target]
            digest_integer_record(edge_digest, (
                source_step, *decode_site(source_site),
                target_step, *decode_site(target_site),
            ))
    queue = [index for index, degree in enumerate(indegree) if degree == 0]
    heapq.heapify(queue)
    order = []
    while queue:
        source = heapq.heappop(queue)
        order.append(source)
        for target in sorted(adjacency[source]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(queue, target)
    if len(order) != len(nodes):
        raise AssertionError("fixed-policy envelope restriction is cyclic")
    position = [0] * len(nodes)
    for rank, node in enumerate(order):
        position[node] = rank
    if any(
        position[source] >= position[target]
        for source, successors in enumerate(adjacency)
        for target in successors
    ):
        raise AssertionError("topological order does not orient selected graph")
    order_digest = hashlib.sha256()
    for index, (step, site) in enumerate(nodes):
        digest_integer_record(order_digest, (step, *decode_site(site), position[index]))
    return {
        "candidate_sets": candidate_sets,
        "envelope_by_step": envelope_by_step,
        "nodes": tuple(nodes),
        "node_index": node_index,
        "position": tuple(position),
        "certificate": {
            "image_lattice": (
                "X=0 mod 3, Y=0 mod 3, and Y-3Z=0 mod 9; inverse "
                "is (X/3,(Z-Y/3)/3,-Y/3)"
            ),
            "vertices": len(nodes),
            "nonempty_steps": sum(bool(item) for item in counts),
            "per_step_range": [min(counts), max(counts)],
            "per_step_counts": list(counts),
            "count_stream_sha256": EXPECTED_ENVELOPE_COUNT_DIGEST,
            "vertex_stream_sha256": EXPECTED_ENVELOPE_DIGEST,
            "fixed_policy_restricted_edges": edges,
            "fixed_policy_restricted_edge_stream_sha256": edge_digest.hexdigest(),
            "topological_order_stream_sha256": order_digest.hexdigest(),
            "all_fixed_policy_restricted_edges_forward": True,
        },
    }


def load_structure(metadata_path, cache_path, fixed_policy_path, prepared_path):
    snapshots = input_snapshots(
        metadata_path, cache_path, fixed_policy_path, prepared_path
    )
    blocks = load_metadata(metadata_path)
    records = load_fixed_records(fixed_policy_path)
    candidate_sites = load_candidates(prepared_path)
    candidate_sets = tuple(frozenset(sites) for sites in candidate_sites)
    actions = fixed_actions(records, candidate_sets)
    structure = build_envelope_and_order(candidate_sites, actions)
    return snapshots, blocks, actions, structure


def compute_role_masks(source_step, control, target_step, structure):
    zero_mask = 0
    backward_mask = 0
    candidate_targets = structure["candidate_sets"][target_step]
    nodes = structure["nodes"]
    node_index = structure["node_index"]
    position = structure["position"]
    for local_index, source_site in enumerate(
        structure["envelope_by_step"][source_step]
    ):
        source = decode_site(source_site)
        target = apply_matrix(tuple(
            source[axis] - control[axis] for axis in range(3)
        ))
        target_site = maybe_encode_site(target)
        if target_site is None or target_site not in candidate_targets:
            continue
        if not in_image_lattice(target):
            raise AssertionError("role target escaped image lattice")
        source_index = node_index[source_step * SITE_COUNT + source_site]
        target_index = node_index[target_step * SITE_COUNT + target_site]
        if nodes[source_index] != (source_step, source_site) or nodes[
            target_index
        ] != (target_step, target_site):
            raise AssertionError("envelope node map drift")
        bit = 1 << local_index
        zero_mask |= bit
        if position[source_index] >= position[target_index]:
            backward_mask |= bit
    return zero_mask, backward_mask


def compute_role_masks_inverse(source_step, control, target_step, structure):
    """Independent target-to-source reconstruction for sampled role checks."""
    zero_mask = 0
    backward_mask = 0
    local_index = {
        site: index
        for index, site in enumerate(structure["envelope_by_step"][source_step])
    }
    node_index = structure["node_index"]
    position = structure["position"]
    for target_site in structure["candidate_sets"][target_step]:
        target = decode_site(target_site)
        difference = exact_inverse_if_integral(target)
        if difference is None:
            continue
        source = tuple(control[axis] + difference[axis] for axis in range(3))
        source_site = maybe_encode_site(source)
        source_local = None if source_site is None else local_index.get(source_site)
        if source_local is None:
            continue
        source_index = node_index[source_step * SITE_COUNT + source_site]
        target_index = node_index[target_step * SITE_COUNT + target_site]
        bit = 1 << source_local
        zero_mask |= bit
        if position[source_index] >= position[target_index]:
            backward_mask |= bit
    return zero_mask, backward_mask


def rejected_witness(
    word, source_step, interior_mask, union_mask, role_cache, structure, channel
):
    violating_mask = union_mask & ~interior_mask
    local_index = (violating_mask & -violating_mask).bit_length() - 1
    source_site = structure["envelope_by_step"][source_step][local_index]
    source = decode_site(source_site)
    x = y = z = 0
    mask_position = 0 if channel == "zero" else 1
    for slot, target_step in enumerate(word):
        control_site = encode_site((x, y, z))
        role_mask = role_cache[control_site * MENU_SIZE + target_step][mask_position]
        if role_mask & (1 << local_index):
            target = apply_matrix((source[0] - x, source[1] - y, source[2] - z))
            source_index = structure["node_index"][
                source_step * SITE_COUNT + source_site
            ]
            target_index = structure["node_index"][
                target_step * SITE_COUNT + encode_site(target)
            ]
            return {
                "word": list(word),
                "slot_zero_based": slot,
                "target_step": target_step,
                "control": [x, y, z],
                "source_site": list(source),
                "target_site": list(target),
                "source_order": structure["position"][source_index],
                "target_order": structure["position"][target_index],
                "same_word_interior_covers_source": False,
            }
        x += MENU_X[target_step]
        y += MENU_Y[target_step]
        z += MENU_Z[target_step]
    raise AssertionError("rejected word supplied no exact role witness")


def scan_action_chunk(cache_path, blocks, actions, structure, started):
    total_words = 0
    total_slots = 0
    total_roles = 0
    total_digit_simple = 0
    baseline_ordered = 0
    baseline_masks = 0
    selected_ordered = 0
    step_records = []
    bitset_blocks = []
    length_histogram = Counter()
    global_zero_role_digest = hashlib.sha256()
    global_backward_role_digest = hashlib.sha256()

    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for block in blocks:
                source_step = block["step"]
                local_envelope = structure["envelope_by_step"][source_step]
                envelope_local_index = {
                    site: index for index, site in enumerate(local_envelope)
                }
                role_cache = {}
                zero_histogram = Counter()
                backward_histogram = Counter()
                direct_checks = 0
                ordered_signatures = set()
                role_signatures = set()
                zero_signatures = set()
                ordered_safe_signatures = set()
                zero_digit_signatures = set()
                ordered_digit_signatures = set()
                zero_intrinsic_signatures = set()
                ordered_intrinsic_signatures = set()
                zero_bits = bytearray((block["words"] + 7) // 8)
                ordered_bits = bytearray((block["words"] + 7) // 8)
                zero_rejected = None
                ordered_rejected = None
                counts = Counter()
                cursor = block["start"]
                observed_slots = 0
                endpoint = apply_matrix(MENU[source_step])
                endpoint_fibres = {(0, 0), endpoint[1:]}
                selected = actions[source_step]

                for ordinal in range(1, block["words"] + 1):
                    length = cache[cursor]
                    cursor += 1
                    word_start = cursor
                    word_end = cursor + length
                    if not 2 <= length <= 5 or word_end > block["end"]:
                        raise AssertionError("invalid cached word", source_step, ordinal)
                    word = tuple(cache[word_start:word_end])
                    x = y = z = 0
                    interior_mask = 0
                    zero_union = 0
                    backward_union = 0
                    lateral_codes = []
                    lateral_fibres = []
                    digit_bits = 0
                    repeated_digit = False
                    all_digits_nonzero = True

                    for position, child in enumerate(word):
                        control_site = encode_site((x, y, z))
                        role_key = control_site * MENU_SIZE + child
                        masks = role_cache.get(role_key)
                        if masks is None:
                            masks = compute_role_masks(
                                source_step, (x, y, z), child, structure
                            )
                            role_cache[role_key] = masks
                            zero_histogram[masks[0].bit_count()] += 1
                            backward_histogram[masks[1].bit_count()] += 1
                            if direct_checks < DIRECT_ROLE_CHECKS_PER_STEP:
                                repeated = compute_role_masks_inverse(
                                    source_step, (x, y, z), child, structure
                                )
                                if repeated != masks:
                                    raise AssertionError("forward/inverse role-mask mismatch")
                                direct_checks += 1
                        zero_union |= masks[0]
                        backward_union |= masks[1]

                        x += MENU_X[child]
                        y += MENU_Y[child]
                        z += MENU_Z[child]
                        if position + 1 < length:
                            interior_site = encode_site((x, y, z))
                            local_index = envelope_local_index.get(interior_site)
                            if local_index is not None:
                                interior_mask |= 1 << local_index
                            lateral_codes.append(
                                (y + SITE_RADIUS) * SITE_SIDE + z + SITE_RADIUS
                            )
                            lateral_fibres.append((y, z))
                            digit = (y - 3 * z) % 9
                            bit = 1 << digit
                            repeated_digit = repeated_digit or bool(digit_bits & bit)
                            digit_bits |= bit
                            all_digits_nonzero = all_digits_nonzero and digit != 0

                    if (x, y, z) != endpoint:
                        raise AssertionError("cached word endpoint drift", source_step, ordinal)
                    ordered_signature = packed_projection_signature(lateral_codes)
                    role_signature = packed_projection_signature(sorted(lateral_codes))
                    ordered_signatures.add(ordered_signature)
                    role_signatures.add(role_signature)
                    digit_simple = all_digits_nonzero and not repeated_digit
                    intrinsic = (
                        len(set(lateral_fibres)) == len(lateral_fibres)
                        and not endpoint_fibres.intersection(lateral_fibres)
                    )
                    zero_safe = not (zero_union & ~interior_mask)
                    ordered_safe = not (backward_union & ~interior_mask)
                    if zero_safe and not ordered_safe:
                        raise AssertionError("zero-envelope filter is not ordered subset")

                    counts["words"] += 1
                    counts["slots"] += length
                    counts["digit_simple_words"] += int(digit_simple)
                    counts["intrinsic_fibre_clean_words"] += int(intrinsic)
                    counts["zero_envelope_words"] += int(zero_safe)
                    counts["ordered_envelope_words"] += int(ordered_safe)
                    counts["zero_envelope_digit_simple_words"] += int(
                        zero_safe and digit_simple
                    )
                    counts["ordered_envelope_digit_simple_words"] += int(
                        ordered_safe and digit_simple
                    )
                    counts["zero_envelope_intrinsic_fibre_clean_words"] += int(
                        zero_safe and intrinsic
                    )
                    counts["ordered_envelope_intrinsic_fibre_clean_words"] += int(
                        ordered_safe and intrinsic
                    )
                    counts["zero_envelope_no_envelope_role_source_words"] += int(
                        zero_safe and zero_union == 0
                    )
                    counts["zero_envelope_same_word_covered_words"] += int(
                        zero_safe and zero_union != 0
                    )
                    counts["ordered_envelope_no_backward_source_words"] += int(
                        ordered_safe and backward_union == 0
                    )
                    counts["ordered_envelope_same_word_covered_words"] += int(
                        ordered_safe and backward_union != 0
                    )
                    if zero_safe:
                        zero_bits[(ordinal - 1) >> 3] |= 1 << ((ordinal - 1) & 7)
                        zero_signatures.add(role_signature)
                        if digit_simple:
                            zero_digit_signatures.add(role_signature)
                        if intrinsic:
                            zero_intrinsic_signatures.add(role_signature)
                    elif zero_rejected is None:
                        zero_rejected = {
                            "ordinal_1_based": ordinal,
                            **rejected_witness(
                                word, source_step, interior_mask, zero_union,
                                role_cache, structure, "zero",
                            ),
                        }
                    if ordered_safe:
                        ordered_bits[(ordinal - 1) >> 3] |= 1 << ((ordinal - 1) & 7)
                        ordered_safe_signatures.add(role_signature)
                        if digit_simple:
                            ordered_digit_signatures.add(role_signature)
                        if intrinsic:
                            ordered_intrinsic_signatures.add(role_signature)
                    elif ordered_rejected is None:
                        ordered_rejected = {
                            "ordinal_1_based": ordinal,
                            **rejected_witness(
                                word, source_step, interior_mask, backward_union,
                                role_cache, structure, "ordered",
                            ),
                        }

                    if ordinal == selected["ordinal"]:
                        if word != selected["word"]:
                            raise AssertionError("selected word ordinal drift", source_step)
                        counts["selected_policy_word_zero_envelope"] = int(zero_safe)
                        counts["selected_policy_word_ordered_envelope"] = int(ordered_safe)
                        if not ordered_safe:
                            raise AssertionError(
                                "selected word fails its own topological order", source_step
                            )
                        selected_ordered += 1

                    cursor = word_end
                    observed_slots += length
                    total_words += 1
                    total_slots += length
                    length_histogram[length] += 1
                    if total_words % 500_000 == 0:
                        enforce_runtime(started, "action census")

                if cursor != block["end"] or observed_slots != block["word_slots"]:
                    raise AssertionError("cache block boundary drift", source_step)
                if direct_checks != DIRECT_ROLE_CHECKS_PER_STEP:
                    raise AssertionError("too few direct role checks", source_step)
                if not counts["ordered_envelope_words"]:
                    raise AssertionError("ordered filter emptied a step", source_step)

                step_zero_digest = hashlib.sha256()
                step_backward_digest = hashlib.sha256()
                for role_key in sorted(role_cache):
                    control_site, target_step = divmod(role_key, MENU_SIZE)
                    header = (source_step, target_step, *decode_site(control_site))
                    digest_integer_record(global_zero_role_digest, header)
                    digest_integer_record(global_backward_role_digest, header)
                    digest_integer_record(step_zero_digest, header)
                    digest_integer_record(step_backward_digest, header)
                    zero_mask, backward_mask = role_cache[role_key]
                    for local_index in iter_mask(zero_mask):
                        record = (
                            source_step,
                            *decode_site(local_envelope[local_index]),
                        )
                        digest_integer_record(global_zero_role_digest, record)
                        digest_integer_record(step_zero_digest, record)
                    for local_index in iter_mask(backward_mask):
                        record = (
                            source_step,
                            *decode_site(local_envelope[local_index]),
                        )
                        digest_integer_record(global_backward_role_digest, record)
                        digest_integer_record(step_backward_digest, record)

                total_roles += len(role_cache)
                total_digit_simple += counts["digit_simple_words"]
                baseline_ordered += len(ordered_signatures)
                baseline_masks += len(role_signatures)
                step_records.append({
                    "step": source_step,
                    "parent_step": list(MENU[source_step]),
                    "envelope_source_sites": len(local_envelope),
                    **dict(counts),
                    "ordered_projection_signatures": len(ordered_signatures),
                    "projection_role_masks": len(role_signatures),
                    "zero_envelope_projection_role_masks": len(zero_signatures),
                    "ordered_envelope_projection_role_masks": len(
                        ordered_safe_signatures
                    ),
                    "zero_envelope_digit_simple_projection_role_masks": len(
                        zero_digit_signatures
                    ),
                    "ordered_envelope_digit_simple_projection_role_masks": len(
                        ordered_digit_signatures
                    ),
                    "zero_envelope_intrinsic_projection_role_masks": len(
                        zero_intrinsic_signatures
                    ),
                    "ordered_envelope_intrinsic_projection_role_masks": len(
                        ordered_intrinsic_signatures
                    ),
                    "distinct_ordered_slot_roles": len(role_cache),
                    "zero_role_mask_stream_sha256": step_zero_digest.hexdigest(),
                    "backward_role_mask_stream_sha256": step_backward_digest.hexdigest(),
                    "zero_role_source_count_histogram": {
                        str(key): value for key, value in sorted(zero_histogram.items())
                    },
                    "backward_role_source_count_histogram": {
                        str(key): value
                        for key, value in sorted(backward_histogram.items())
                    },
                    "first_zero_envelope_rejected_witness": zero_rejected,
                    "first_ordered_envelope_rejected_witness": ordered_rejected,
                })
                bitset_blocks.append({
                    "step": source_step,
                    "words": block["words"],
                    "zero_envelope": bytes(zero_bits),
                    "zero_envelope_count": counts["zero_envelope_words"],
                    "ordered_envelope": bytes(ordered_bits),
                    "ordered_envelope_count": counts["ordered_envelope_words"],
                })
                del role_cache
                enforce_runtime(started, f"completed source step {source_step}")
        finally:
            cache.close()

    expected_words = sum(block["words"] for block in blocks)
    expected_slots = sum(block["word_slots"] for block in blocks)
    if total_words != expected_words or total_slots != expected_slots:
        raise AssertionError("chunk word/slot census drift")
    return {
        "step_records": step_records,
        "bitset_blocks": bitset_blocks,
        "census": {
            "words": total_words,
            "slots": total_slots,
            "word_length_histogram": {
                str(key): value for key, value in sorted(length_histogram.items())
            },
            "digit_simple_words": total_digit_simple,
            "distinct_ordered_slot_roles": total_roles,
            "baseline_ordered_projection_signatures": baseline_ordered,
            "baseline_projection_role_masks": baseline_masks,
            "selected_policy_words_ordered_envelope": selected_ordered,
            "zero_role_mask_stream_sha256": global_zero_role_digest.hexdigest(),
            "backward_role_mask_stream_sha256": (
                global_backward_role_digest.hexdigest()
            ),
        },
    }


def write_bitset_sidecar(blocks, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=output_path.parent, prefix=output_path.name + ".", suffix=".tmp"
    )
    metadata = []
    zero_digest = hashlib.sha256()
    ordered_digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(BITSET_MAGIC)
            handle.write(struct.pack("<II", BITSET_SCHEMA, len(blocks)))
            for block in blocks:
                step = block["step"]
                words = block["words"]
                zero = block["zero_envelope"]
                ordered = block["ordered_envelope"]
                byte_count = (words + 7) // 8
                if len(zero) != byte_count or len(ordered) != byte_count:
                    raise AssertionError("bitset block byte length drift", step)
                if sum(byte.bit_count() for byte in zero) != block[
                    "zero_envelope_count"
                ] or sum(byte.bit_count() for byte in ordered) != block[
                    "ordered_envelope_count"
                ]:
                    raise AssertionError("bitset population drift", step)
                if any(zero[index] & ~ordered[index] for index in range(byte_count)):
                    raise AssertionError("zero bitset is not ordered subset", step)
                block_offset = handle.tell()
                handle.write(struct.pack(
                    "<IIIII",
                    step,
                    words,
                    byte_count,
                    block["zero_envelope_count"],
                    block["ordered_envelope_count"],
                ))
                zero_offset = handle.tell()
                handle.write(zero)
                ordered_offset = handle.tell()
                handle.write(ordered)
                zero_digest.update(struct.pack("<II", step, byte_count))
                zero_digest.update(zero)
                ordered_digest.update(struct.pack("<II", step, byte_count))
                ordered_digest.update(ordered)
                metadata.append({
                    "step": step,
                    "words": words,
                    "block_offset": block_offset,
                    "block_bytes": 20 + 2 * byte_count,
                    "zero_envelope": {
                        "offset": zero_offset,
                        "bytes": byte_count,
                        "set_bits": block["zero_envelope_count"],
                        "sha256": hashlib.sha256(zero).hexdigest(),
                    },
                    "ordered_envelope": {
                        "offset": ordered_offset,
                        "bytes": byte_count,
                        "set_bits": block["ordered_envelope_count"],
                        "sha256": hashlib.sha256(ordered).hexdigest(),
                    },
                    "unused_high_bits_in_final_byte_are_zero": (
                        words % 8 == 0
                        or not ((zero[-1] | ordered[-1]) & ~((1 << (words % 8)) - 1))
                    ),
                })
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    snapshot = file_snapshot(output_path)
    return {
        "path": snapshot["path"],
        "sha256": snapshot["sha256"],
        "bytes": snapshot["bytes"],
        "schema": BITSET_SCHEMA,
        "blocks": metadata,
        "zero_envelope_ordinal_bitsets_sha256": zero_digest.hexdigest(),
        "ordered_envelope_ordinal_bitsets_sha256": ordered_digest.hexdigest(),
    }


def read_bitset_sidecar(metadata):
    path = Path(metadata["path"])
    if file_sha256(path) != metadata["sha256"] or path.stat().st_size != metadata[
        "bytes"
    ]:
        raise AssertionError("bitset sidecar commitment drift", path)
    data = path.read_bytes()
    if data[:len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("bitset magic drift", path)
    schema, block_count = struct.unpack_from("<II", data, len(BITSET_MAGIC))
    if schema != BITSET_SCHEMA or block_count != len(metadata["blocks"]):
        raise AssertionError("bitset header drift", path)
    cursor = len(BITSET_MAGIC) + 8
    result = []
    zero_digest = hashlib.sha256()
    ordered_digest = hashlib.sha256()
    for expected in metadata["blocks"]:
        if cursor != expected["block_offset"]:
            raise AssertionError("bitset block offset drift", path)
        step, words, byte_count, zero_count, ordered_count = struct.unpack_from(
            "<IIIII", data, cursor
        )
        cursor += 20
        zero = data[cursor:cursor + byte_count]
        zero_offset = cursor
        cursor += byte_count
        ordered = data[cursor:cursor + byte_count]
        ordered_offset = cursor
        cursor += byte_count
        if (
            step != expected["step"]
            or words != expected["words"]
            or zero_offset != expected["zero_envelope"]["offset"]
            or ordered_offset != expected["ordered_envelope"]["offset"]
            or 20 + 2 * byte_count != expected["block_bytes"]
        ):
            raise AssertionError("bitset block metadata drift", path, step)
        for channel, value, count in (
            ("zero_envelope", zero, zero_count),
            ("ordered_envelope", ordered, ordered_count),
        ):
            record = expected[channel]
            if (
                len(value) != record["bytes"]
                or hashlib.sha256(value).hexdigest() != record["sha256"]
                or sum(byte.bit_count() for byte in value) != count
                or count != record["set_bits"]
            ):
                raise AssertionError("bitset channel drift", path, step, channel)
        if any(zero[index] & ~ordered[index] for index in range(byte_count)):
            raise AssertionError("zero bitset not subset on read", path, step)
        if words % 8 and ((zero[-1] | ordered[-1]) & ~((1 << (words % 8)) - 1)):
            raise AssertionError("nonzero bitset padding", path, step)
        zero_digest.update(struct.pack("<II", step, byte_count))
        zero_digest.update(zero)
        ordered_digest.update(struct.pack("<II", step, byte_count))
        ordered_digest.update(ordered)
        result.append({
            "step": step,
            "words": words,
            "zero_envelope": zero,
            "zero_envelope_count": zero_count,
            "ordered_envelope": ordered,
            "ordered_envelope_count": ordered_count,
        })
    if cursor != len(data):
        raise AssertionError("bitset sidecar trailing bytes", path)
    if zero_digest.hexdigest() != metadata[
        "zero_envelope_ordinal_bitsets_sha256"
    ] or ordered_digest.hexdigest() != metadata[
        "ordered_envelope_ordinal_bitsets_sha256"
    ]:
        raise AssertionError("bitset aggregate digest drift", path)
    return result


def run_chunk(
    metadata_path,
    cache_path,
    fixed_policy_path,
    prepared_path,
    first_step,
    last_step,
    output_path,
    bitset_path,
):
    started = time.monotonic()
    policy = resource_policy(True)
    checker_sha256 = file_sha256(Path(__file__).resolve())
    snapshots, all_blocks, actions, structure = load_structure(
        metadata_path, cache_path, fixed_policy_path, prepared_path
    )
    if not 0 <= first_step <= last_step < MENU_SIZE:
        raise ValueError("invalid inclusive step range")
    blocks = all_blocks[first_step:last_step + 1]
    scan = scan_action_chunk(cache_path, blocks, actions, structure, started)
    sidecar = write_bitset_sidecar(scan.pop("bitset_blocks"), bitset_path)
    for snapshot in snapshots.values():
        verify_snapshot_unchanged(snapshot)
    if file_sha256(Path(__file__).resolve()) != checker_sha256:
        raise RuntimeError("checker changed during exact chunk")
    enforce_runtime(started, "chunk complete")
    payload = {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact source-step chunk of lattice-envelope whole-word filters",
        "checker": {
            "path": "design/nonx_scc_core_action_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "pinned_inputs": snapshots,
        "step_scope_inclusive": [first_step, last_step],
        "lattice_envelope_and_common_order": structure["certificate"],
        "filter_definition": {
            "zero_envelope": (
                "the union of role source masks B_T(s,t,c) is contained in "
                "the exact proper-interior mask of the same whole word"
            ),
            "ordered_envelope": (
                "the union of role source masks for backward common-order "
                "edges is contained in the exact proper-interior mask of the "
                "same whole word"
            ),
            "whole_word_correlation": True,
        },
        "action_filter": scan,
        "accepted_ordinal_bitset_sidecar": sidecar,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }
    atomic_json_dump(payload, output_path)
    return payload


def merge_chunks(chunk_paths, output_path, bitset_path):
    started = time.monotonic()
    policy = resource_policy(True)
    checker_sha256 = file_sha256(Path(__file__).resolve())
    chunks = []
    for path in chunk_paths:
        with Path(path).open() as handle:
            chunk = json.load(handle)
        if chunk["checker"]["sha256"] != checker_sha256:
            raise AssertionError("chunk checker drift", path)
        chunks.append(chunk)
    chunks.sort(key=lambda item: item["step_scope_inclusive"][0])
    scopes = [tuple(item["step_scope_inclusive"]) for item in chunks]
    next_step = 0
    for first_step, last_step in scopes:
        if first_step != next_step or not first_step <= last_step < MENU_SIZE:
            raise AssertionError("chunks are not a contiguous disjoint partition", scopes)
        next_step = last_step + 1
    if next_step != MENU_SIZE:
        raise AssertionError("chunks do not exactly partition all source steps", scopes)
    reference = chunks[0]
    for chunk in chunks[1:]:
        if chunk["pinned_inputs"] != reference["pinned_inputs"] or chunk[
            "lattice_envelope_and_common_order"
        ] != reference["lattice_envelope_and_common_order"]:
            raise AssertionError("chunk inputs or envelope order disagree")
    bitset_blocks = []
    step_records = []
    for chunk in chunks:
        bitset_blocks.extend(read_bitset_sidecar(
            chunk["accepted_ordinal_bitset_sidecar"]
        ))
        step_records.extend(chunk["action_filter"]["step_records"])
    if [item["step"] for item in step_records] != list(range(MENU_SIZE)) or [
        item["step"] for item in bitset_blocks
    ] != list(range(MENU_SIZE)):
        raise AssertionError("merged step order drift")
    sidecar = write_bitset_sidecar(bitset_blocks, bitset_path)

    def total(field):
        return sum(item[field] for item in step_records)

    baseline = {
        "words": total("words"),
        "slots": total("slots"),
        "digit_simple_words": total("digit_simple_words"),
        "distinct_ordered_slot_roles": total("distinct_ordered_slot_roles"),
        "baseline_ordered_projection_signatures": total(
            "ordered_projection_signatures"
        ),
        "baseline_projection_role_masks": total("projection_role_masks"),
    }
    expected = {
        "words": EXPECTED_WORDS,
        "slots": EXPECTED_SLOTS,
        "digit_simple_words": EXPECTED_DIGIT_SIMPLE_WORDS,
        "distinct_ordered_slot_roles": EXPECTED_ROLE_TYPES,
        "baseline_ordered_projection_signatures": (
            EXPECTED_ORDERED_PROJECTION_SIGNATURES
        ),
        "baseline_projection_role_masks": EXPECTED_PROJECTION_ROLE_MASKS,
    }
    if baseline != expected:
        raise AssertionError("merged baseline census drift", expected, baseline)
    if total("selected_policy_word_ordered_envelope") != MENU_SIZE:
        raise AssertionError("not every selected word follows common order")

    count_fields = (
        "zero_envelope_words",
        "ordered_envelope_words",
        "zero_envelope_digit_simple_words",
        "ordered_envelope_digit_simple_words",
        "zero_envelope_intrinsic_fibre_clean_words",
        "ordered_envelope_intrinsic_fibre_clean_words",
        "zero_envelope_projection_role_masks",
        "ordered_envelope_projection_role_masks",
        "zero_envelope_digit_simple_projection_role_masks",
        "ordered_envelope_digit_simple_projection_role_masks",
        "zero_envelope_intrinsic_projection_role_masks",
        "ordered_envelope_intrinsic_projection_role_masks",
    )
    totals = {field: total(field) for field in count_fields}
    empty = {
        "zero_envelope_words": [
            item["step"] for item in step_records if not item["zero_envelope_words"]
        ],
        "ordered_envelope_words": [
            item["step"]
            for item in step_records if not item["ordered_envelope_words"]
        ],
        "zero_envelope_intrinsic_fibre_clean_words": [
            item["step"] for item in step_records
            if not item["zero_envelope_intrinsic_fibre_clean_words"]
        ],
        "ordered_envelope_intrinsic_fibre_clean_words": [
            item["step"] for item in step_records
            if not item["ordered_envelope_intrinsic_fibre_clean_words"]
        ],
    }
    quantile_fields = (
        "zero_envelope_words",
        "ordered_envelope_words",
        "zero_envelope_projection_role_masks",
        "ordered_envelope_projection_role_masks",
        "zero_envelope_intrinsic_fibre_clean_words",
        "ordered_envelope_intrinsic_fibre_clean_words",
    )
    per_step_quantiles = {
        field: quantiles([item[field] for item in step_records])
        for field in quantile_fields
    }
    if file_sha256(Path(__file__).resolve()) != checker_sha256:
        raise RuntimeError("checker changed during merge")
    payload = {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact merged full-cache lattice-envelope whole-word action "
            "certificate; not chronological availability"
        ),
        "checker": {
            "path": "design/nonx_scc_core_action_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_merge": True,
        },
        "resource_policy": policy,
        "pinned_inputs": reference["pinned_inputs"],
        "chunk_runs": [{
            "step_scope_inclusive": item["step_scope_inclusive"],
            "elapsed_seconds": item["elapsed_seconds"],
            "maximum_resident_bytes": item["maximum_resident_bytes"],
            "raw_path": str(Path(path).resolve()),
            "raw_sha256": file_sha256(path),
        } for item, path in zip(chunks, sorted(chunk_paths))],
        "lattice_envelope_and_common_order": reference[
            "lattice_envelope_and_common_order"
        ],
        "action_filter": {
            "definition": reference["filter_definition"],
            "baseline_census": baseline,
            "accepted_totals": totals,
            "steps_with_zero_actions": empty,
            "per_step_count_quantiles": per_step_quantiles,
            "step_records": step_records,
        },
        "accepted_ordinal_bitset_sidecar": sidecar,
        "proved": [
            "the exact image lattice is characterized in both directions by the three displayed congruences",
            "every direction-blind cycle lies in the pinned 780-vertex candidate envelope",
            "the zero-envelope arbitrary-action union is acyclic",
            "the ordered-envelope arbitrary-action union follows one common strict order and is acyclic",
            "all slots and source-interior exceptions are taken from the same whole word",
            "the two chunks exactly partition every pinned cache word and slot",
        ],
        "not_proved": [
            "chronological legality or positive connector availability",
            "nondegenerate selector changes or latent empty-effect re-entry",
            "cursor jumps, line births, endpoint effects, or near/deep and deep/deep secants",
            "a successor-closed safety policy or an unconditional far-secant theorem",
        ],
        "merge_elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }
    atomic_json_dump(payload, output_path)
    return payload


def transitive_closure(vertices, edges):
    reach = [0] * vertices
    for source, target in edges:
        reach[source] |= 1 << target
    for pivot in range(vertices):
        for source in range(vertices):
            if reach[source] & (1 << pivot):
                reach[source] |= reach[pivot]
    return tuple(reach)


def is_acyclic(vertices, edges):
    reach = transitive_closure(vertices, edges)
    return all(not (reach[node] & (1 << node)) for node in range(vertices))


def synthetic_self_check():
    lattice_vectors = 0
    for vector in itertools.product(range(-8, 9), repeat=3):
        x, y, z = vector
        rational_inverse_integral = (
            x % 3 == 0
            and y % 3 == 0
            and (z - y // 3) % 3 == 0
        )
        inverse = exact_inverse_if_integral(vector)
        if (inverse is not None) != rational_inverse_integral:
            raise AssertionError("lattice characterization disagreement", vector)
        lattice_vectors += int(inverse is not None)
    image_pairs = 0
    for source in itertools.product(range(-2, 3), repeat=3):
        for control in itertools.product(range(-2, 3), repeat=3):
            difference = tuple(source[axis] - control[axis] for axis in range(3))
            if not in_image_lattice(apply_matrix(difference)):
                raise AssertionError("matrix image escaped exact lattice")
            image_pairs += 1

    # Exhaust every choice of envelope T on three vertices and every graph
    # whose targets lie in T but whose retained edges have sources outside T.
    envelope_cases = 0
    retained_graphs = 0
    vertices = 3
    for envelope_mask in range(1 << vertices):
        envelope = {
            node for node in range(vertices) if envelope_mask & (1 << node)
        }
        possible = tuple(
            (source, target)
            for source in range(vertices)
            for target in envelope
            if source not in envelope
        )
        envelope_cases += 1
        for edge_mask in range(1 << len(possible)):
            edges = tuple(
                edge for index, edge in enumerate(possible)
                if edge_mask & (1 << index)
            )
            if not is_acyclic(vertices, edges):
                raise AssertionError("zero-envelope theorem failed", envelope, edges)
            retained_graphs += 1

    role_masks = (0b011, 0b110)
    union = role_masks[0] | role_masks[1]
    if union & ~0b111 or not (union & ~0b010):
        raise AssertionError("same-word interior subset test drift")
    forward_batch = ((0, 1), (1, 2))
    if not is_acyclic(3, forward_batch):
        raise AssertionError("ordered fallback example is cyclic")
    return {
        "status": "passed",
        "target_box_vectors_checked": SITE_COUNT,
        "image_lattice_vectors_in_target_box": lattice_vectors,
        "matrix_image_source_control_pairs_checked": image_pairs,
        "three_vertex_envelope_choices": envelope_cases,
        "zero_envelope_retained_graphs_checked": retained_graphs,
        "same_word_full_cover_accepted": True,
        "same_word_partial_cover_rejected": True,
        "ordered_filter_strictly_more_permissive_example": True,
    }


def estimate():
    return {
        "status": "planning estimate only; no input read or output write",
        "direct_action_chunks_inclusive": [list(item) for item in ACTION_CHUNKS],
        "graph_reconstruction_required": False,
        "algebraic_envelope_vertices": EXPECTED_ENVELOPE_VERTICES,
        "algebraic_envelope_stream_sha256": EXPECTED_ENVELOPE_DIGEST,
        "resource_limits_per_process": {
            "processes": 1,
            "threads": 1,
            "minimum_nice": 15,
            "maximum_seconds": MAX_SECONDS,
            "maximum_work_seconds": MAX_WORK_SECONDS,
            "resident_abort_bytes": MAX_RESIDENT_BYTES,
        },
        "estimated_action_chunk_wall_seconds": [55, 75],
        "estimated_action_chunk_peak_resident_bytes": 100 * 1024 * 1024,
        "basis": (
            "the attempted 0--60 envelope scan completed its last source step "
            "at 115.17 seconds and about 60 MiB RSS before the hard gate; the "
            "four ranges are balanced to 11.9--14.7 million word slots each"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("estimate")
    subparsers.add_parser("self-check")

    chunk_parser = subparsers.add_parser("chunk")
    chunk_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    chunk_parser.add_argument("--cache", default=DEFAULT_CACHE)
    chunk_parser.add_argument("--fixed-policy", default=DEFAULT_FIXED_POLICY)
    chunk_parser.add_argument("--prepared", default=DEFAULT_PREPARED)
    chunk_parser.add_argument("--first-step", type=int, required=True)
    chunk_parser.add_argument("--last-step", type=int, required=True)
    chunk_parser.add_argument("--output", required=True)
    chunk_parser.add_argument("--bitsets", required=True)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--chunks", nargs="+", required=True)
    merge_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    merge_parser.add_argument("--bitsets", default=DEFAULT_BITSETS)

    args = parser.parse_args()
    if args.mode == "estimate":
        payload = estimate()
    elif args.mode == "self-check":
        payload = synthetic_self_check()
    elif args.mode == "chunk":
        payload = run_chunk(
            args.metadata,
            args.cache,
            args.fixed_policy,
            args.prepared,
            args.first_step,
            args.last_step,
            args.output,
            args.bitsets,
        )
        payload = {
            "output": str(Path(args.output).resolve()),
            "bitsets": payload["accepted_ordinal_bitset_sidecar"],
            "step_scope_inclusive": payload["step_scope_inclusive"],
            "census": payload["action_filter"]["census"],
            "elapsed_seconds": payload["elapsed_seconds"],
            "maximum_resident_bytes": payload["maximum_resident_bytes"],
        }
    else:
        payload = merge_chunks(args.chunks, args.output, args.bitsets)
        payload = {
            "output": str(Path(args.output).resolve()),
            "bitsets": payload["accepted_ordinal_bitset_sidecar"],
            "accepted_totals": payload["action_filter"]["accepted_totals"],
            "steps_with_zero_actions": payload["action_filter"][
                "steps_with_zero_actions"
            ],
            "per_step_count_quantiles": payload["action_filter"][
                "per_step_count_quantiles"
            ],
        }
    print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
