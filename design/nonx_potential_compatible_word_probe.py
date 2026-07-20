#!/usr/bin/env python3
"""Exact whole-word filter for the fixed non-x height-two potential.

For the full candidate-site sets C_s and the exact rank r(s,x) emitted by
``nonx_fixed_word_policy_probe.py``, define the bad source-site mask of one
ordered slot role (s,t,c) by

    B(s,t,c) = {x in C_s : M(x-c) in C_t and
                             r(s,x) <= r(t,M(x-c))}.

A whole connector word w is potential-compatible exactly when the union of
the bad masks of all of its ordered slots is contained in the proper-interior
set I_s(w).  This is an if-and-only-if check for strict descent of the frozen
rank on every direction-blind edge induced by that one word.  Interiors and
slots are never spliced between different words.

This remains a conditional non-x lifetime filter, not connector availability:
when a carried poison site belongs to I_s(w), the word is unavailable in that
state even though the corresponding edge is absent from its compatibility
graph.  The checker also does not cover selector edges, births, cursor jumps,
or exact chronological legality.

Run on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/nonx_potential_compatible_word_probe.py prepare \
        --metadata /tmp/no-new-x-line-L5-canonical.json \
        --cache /tmp/no-new-x-line-domains.bin \
        --fixed-policy /tmp/nonx-fixed-word-policy-probe-v2.json \
        --output /tmp/nonx-potential-compatible-word-prepared.json

Then run the disjoint inclusive source-step chunks 0--60 and 61--123, one at
a time, with the ``chunk`` subcommand, and combine their JSON/NPOTB001 files
with ``merge``.  The split keeps every low-priority process below the hard
two-minute limit while scanning every word exactly once in the filter pass.
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
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_FIXED_POLICY = Path("/tmp/nonx-fixed-word-policy-probe-v2.json")
DEFAULT_OUTPUT = Path("/tmp/nonx-potential-compatible-word-probe.json")
DEFAULT_BITSETS = Path("/tmp/nonx-potential-compatible-word-probe-bitsets.bin")
DEFAULT_PREPARED = Path("/tmp/nonx-potential-compatible-word-prepared.json")

EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_FIXED_POLICY_SHA256 = (
    "e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e"
)
EXPECTED_FIXED_POLICY_CHECKER_SHA256 = (
    "531ba6ee0bfa8d5bf7485d70b13687ace4e1b100cdcdfd739b8bdcac9d8efdd3"
)
EXPECTED_NONX_CHECKER_SHA256 = (
    "4eb928bad0c0104d34b68424b07dd3b6a4939f216968bd6b2399a540b592e755"
)
EXPECTED_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_CANDIDATE_SITES = 34_520
EXPECTED_CANDIDATE_RANGE = (122, 520)
EXPECTED_CANDIDATE_DIGEST = (
    "d3f5892f3edb518fcdad88457f04fddb4eb3cece48102cfbdd801353897e4e07"
)
EXPECTED_SELECTED_EDGES = 1_321
EXPECTED_SELECTED_EDGE_DIGEST = (
    "0d42fc09d958fce8a2a9ed2fe02ae4f2cca3f3c3549c68a8bc3e5835780b70a8"
)
EXPECTED_RANK_DIGEST = (
    "79a83e18f61a95c81e24a7493e9175c034fb06719f19fa8172fa041477295056"
)
EXPECTED_MAXIMUM_RANK = 2
EXPECTED_ROLE_TYPES = 840_794
EXPECTED_ORDERED_PROJECTION_SIGNATURES = 291_414
EXPECTED_PROJECTION_ROLE_MASKS = 216_322
EXPECTED_DIGIT_SIMPLE_WORDS = 6_755_766
EXPECTED_LENGTH_HISTOGRAM = {2: 552, 3: 56_516, 4: 7_057_516, 5: 5_422_562}
CACHE_MAGIC = b"NOXLN001"
BITSET_MAGIC = b"NPOTB001"
SITE_RADIUS = 8
SITE_SIDE = 17
SITE_COUNT = SITE_SIDE**3
MAX_SECONDS = 120.0
MAX_RESIDENT_BYTES = 300 * 1024 * 1024
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
MENU_X = tuple(step[0] for step in MENU)
MENU_Y = tuple(step[1] for step in MENU)
MENU_Z = tuple(step[2] for step in MENU)


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


def digest_integer_record(digest, values):
    for value in values:
        digest.update(int(value).to_bytes(8, "little", signed=True))


def apply_matrix(vector):
    x, y, z = vector
    return 3 * x, -3 * z, 3 * y - z


def inverse_image(vector):
    """Return d with M d=vector, or None when vector is outside M Z^3."""
    x, y, z = vector
    if x % 3 or y % 3:
        return None
    dx = x // 3
    dz = -y // 3
    numerator = z + dz
    if numerator % 3:
        return None
    result = dx, numerator // 3, dz
    if apply_matrix(result) != vector:
        raise AssertionError("exact M inverse failed", vector, result)
    return result


def encode_site(vector):
    x, y, z = vector
    if not (
        -SITE_RADIUS <= x <= SITE_RADIUS
        and -SITE_RADIUS <= y <= SITE_RADIUS
        and -SITE_RADIUS <= z <= SITE_RADIUS
    ):
        raise ValueError("candidate site escaped radius-eight box", vector)
    return (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE + (
        y + SITE_RADIUS
    ) * SITE_SIDE + z + SITE_RADIUS


def maybe_encode_site(vector):
    x, y, z = vector
    if not (
        -SITE_RADIUS <= x <= SITE_RADIUS
        and -SITE_RADIUS <= y <= SITE_RADIUS
        and -SITE_RADIUS <= z <= SITE_RADIUS
    ):
        return None
    return (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE + (
        y + SITE_RADIUS
    ) * SITE_SIDE + z + SITE_RADIUS


def decode_site(encoded):
    if not 0 <= encoded < SITE_COUNT:
        raise ValueError("invalid encoded candidate site", encoded)
    x_digit, remainder = divmod(encoded, SITE_SIDE * SITE_SIDE)
    y_digit, z_digit = divmod(remainder, SITE_SIDE)
    return (
        x_digit - SITE_RADIUS,
        y_digit - SITE_RADIUS,
        z_digit - SITE_RADIUS,
    )


def packed_projection_signature(codes):
    if len(codes) > 4:
        raise AssertionError("too many connector interiors")
    packed = len(codes)
    for position, code in enumerate(codes):
        if not 0 <= code < SITE_SIDE * SITE_SIDE:
            raise AssertionError("lateral prefix code escaped range", code)
        packed |= (code + 1) << (3 + 9 * position)
    return packed


def iter_mask(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def enforce_runtime(started, phase):
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > MAX_SECONDS:
        raise RuntimeError("120-second run limit exceeded", phase, elapsed)
    if resident > MAX_RESIDENT_BYTES:
        raise MemoryError("300-MiB resident limit exceeded", phase, resident)


def resource_policy(enforce):
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in observed.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run requires one numerical thread and nice >=15", observed, nice
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": observed,
        "process_nice": nice,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "maximum_seconds": MAX_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


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
    if identity != snapshot["identity"]:
        raise RuntimeError("input changed during exact scan", snapshot["path"])


def load_inputs(metadata_path, cache_path, fixed_policy_path):
    snapshots = {
        "metadata": file_snapshot(metadata_path),
        "cache": file_snapshot(cache_path),
        "fixed_policy": file_snapshot(fixed_policy_path),
        "fixed_policy_checker": file_snapshot(
            ROOT / "design" / "nonx_fixed_word_policy_probe.py"
        ),
        "nonx_checker": file_snapshot(
            ROOT / "design" / "nonx_degenerate_site_graph.py"
        ),
    }
    expected = {
        "metadata": EXPECTED_METADATA_SHA256,
        "cache": EXPECTED_CACHE_SHA256,
        "fixed_policy": EXPECTED_FIXED_POLICY_SHA256,
        "fixed_policy_checker": EXPECTED_FIXED_POLICY_CHECKER_SHA256,
        "nonx_checker": EXPECTED_NONX_CHECKER_SHA256,
    }
    observed = {key: value["sha256"] for key, value in snapshots.items()}
    if observed != expected:
        raise AssertionError("pinned input drift", expected, observed)
    if snapshots["cache"]["bytes"] != EXPECTED_CACHE_BYTES:
        raise AssertionError("compact cache byte count drift")

    with Path(metadata_path).open() as handle:
        metadata = json.load(handle)
    blocks = sorted(
        metadata["compact_domain_cache"]["blocks"], key=lambda item: item["step"]
    )
    if len(blocks) != len(MENU) or [b["step"] for b in blocks] != list(
        range(len(MENU))
    ):
        raise AssertionError("cache block table step drift")
    if sum(block["words"] for block in blocks) != EXPECTED_WORDS:
        raise AssertionError("cache block word count drift")
    if sum(block["word_slots"] for block in blocks) != EXPECTED_WORD_SLOTS:
        raise AssertionError("cache block slot count drift")

    with Path(fixed_policy_path).open() as handle:
        fixed_policy = json.load(handle)
    if fixed_policy["checker"]["sha256"] != EXPECTED_FIXED_POLICY_CHECKER_SHA256:
        raise AssertionError("fixed-policy checker commitment drift")
    if fixed_policy["policy_graph"]["edge_stream_sha256"] != (
        EXPECTED_SELECTED_EDGE_DIGEST
    ):
        raise AssertionError("fixed-policy graph commitment drift")
    records = fixed_policy["fixed_policy"]["records"]
    if len(records) != len(MENU) or [record["step"] for record in records] != list(
        range(len(MENU))
    ):
        raise AssertionError("fixed-policy step record drift")
    if stable_hash(records) != fixed_policy["fixed_policy"][
        "record_stream_sha256"
    ]:
        raise AssertionError("fixed-policy record hash drift")
    return snapshots, blocks, records


def scan_candidate_sites(cache_path, blocks, started):
    candidate_sites = [set() for _step in MENU]
    words = 0
    slots = 0
    length_histogram = Counter()
    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[: len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for block in blocks:
                source = block["step"]
                endpoint = apply_matrix(MENU[source])
                cursor = block["start"]
                observed_slots = 0
                for ordinal in range(1, block["words"] + 1):
                    length = cache[cursor]
                    cursor += 1
                    end = cursor + length
                    if not 2 <= length <= 5 or end > block["end"]:
                        raise AssertionError(
                            "invalid compact word", source, ordinal, length
                        )
                    x = y = z = 0
                    for position in range(length):
                        child = cache[cursor + position]
                        if child >= len(MENU):
                            raise AssertionError("child step escaped menu")
                        x += MENU_X[child]
                        y += MENU_Y[child]
                        z += MENU_Z[child]
                        if position + 1 < length:
                            if not (
                                -SITE_RADIUS <= x <= SITE_RADIUS
                                and -SITE_RADIUS <= y <= SITE_RADIUS
                                and -SITE_RADIUS <= z <= SITE_RADIUS
                            ):
                                raise AssertionError("proper prefix escaped box")
                            candidate_sites[source].add(
                                (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE
                                + (y + SITE_RADIUS) * SITE_SIDE
                                + z
                                + SITE_RADIUS
                            )
                    if (x, y, z) != endpoint:
                        raise AssertionError(
                            "cached word endpoint drift", source, ordinal
                        )
                    cursor = end
                    words += 1
                    slots += length
                    observed_slots += length
                    length_histogram[length] += 1
                    if words % 500_000 == 0:
                        enforce_runtime(started, "candidate-site pass")
                if cursor != block["end"] or observed_slots != block["word_slots"]:
                    raise AssertionError("cache block boundary drift", source)
        finally:
            cache.close()

    if words != EXPECTED_WORDS or slots != EXPECTED_WORD_SLOTS:
        raise AssertionError("candidate pass census drift", words, slots)
    if dict(length_histogram) != EXPECTED_LENGTH_HISTOGRAM:
        raise AssertionError("word-length histogram drift", length_histogram)
    counts = [len(sites) for sites in candidate_sites]
    if sum(counts) != EXPECTED_CANDIDATE_SITES or (
        min(counts), max(counts)
    ) != EXPECTED_CANDIDATE_RANGE:
        raise AssertionError("candidate-site count drift", sum(counts), counts)
    digest = hashlib.sha256()
    for step, sites in enumerate(candidate_sites):
        for site in sorted(sites):
            digest_integer_record(digest, (step, *decode_site(site)))
    if digest.hexdigest() != EXPECTED_CANDIDATE_DIGEST:
        raise AssertionError("candidate-site stream digest drift", digest.hexdigest())
    return tuple(tuple(sorted(sites)) for sites in candidate_sites), {
        "words": words,
        "slots": slots,
        "word_length_histogram": {
            str(length): count for length, count in sorted(length_histogram.items())
        },
        "candidate_sites": sum(counts),
        "candidate_sites_per_step_range": [min(counts), max(counts)],
        "candidate_site_stream_sha256": digest.hexdigest(),
    }


def selected_actions(records, candidate_sites):
    actions = []
    for expected_step, record in enumerate(records):
        if record["step"] != expected_step:
            raise AssertionError("selected policy record order drift")
        word = tuple(record["word"])
        position = (0, 0, 0)
        prefixes = []
        interiors = []
        for slot, child in enumerate(word):
            prefixes.append(position)
            position = tuple(
                position[axis] + MENU[child][axis] for axis in range(3)
            )
            if slot + 1 < len(word):
                interiors.append(position)
        if position != apply_matrix(MENU[expected_step]):
            raise AssertionError("selected word endpoint drift", expected_step)
        if [list(point) for point in interiors] != record["interiors"]:
            raise AssertionError("selected word interior record drift", expected_step)
        interior_codes = tuple(encode_site(point) for point in interiors)
        if not set(interior_codes) <= set(candidate_sites[expected_step]):
            raise AssertionError("selected interior outside candidate set")
        actions.append({
            "word": word,
            "prefixes": tuple(prefixes),
            "interiors": interior_codes,
            "ordinal": record["ordinal_1_based"],
        })
    return tuple(actions)


def reconstruct_rank(candidate_sites, actions):
    nodes = tuple(
        (step, site)
        for step, sites in enumerate(candidate_sites)
        for site in sites
    )
    node_index = {
        step * SITE_COUNT + site: index
        for index, (step, site) in enumerate(nodes)
    }
    adjacency = [[] for _node in nodes]
    for source_index, (source_step, source_site) in enumerate(nodes):
        action = actions[source_step]
        if source_site in action["interiors"]:
            continue
        source_vector = decode_site(source_site)
        for target_step, control in zip(action["word"], action["prefixes"]):
            target_vector = apply_matrix(tuple(
                source_vector[axis] - control[axis] for axis in range(3)
            ))
            target_site = maybe_encode_site(target_vector)
            if target_site is None:
                continue
            target_index = node_index.get(target_step * SITE_COUNT + target_site)
            if target_index is not None:
                adjacency[source_index].append(target_index)
        adjacency[source_index] = sorted(set(adjacency[source_index]))

    indegree = [0] * len(nodes)
    edge_digest = hashlib.sha256()
    edges = 0
    for source, successors in enumerate(adjacency):
        source_step, source_site = nodes[source]
        source_vector = decode_site(source_site)
        for target in successors:
            target_step, target_site = nodes[target]
            target_vector = decode_site(target_site)
            indegree[target] += 1
            edges += 1
            edge_digest.update(struct.pack(
                "<8i",
                source_step,
                *source_vector,
                target_step,
                *target_vector,
            ))
    if edges != EXPECTED_SELECTED_EDGES or edge_digest.hexdigest() != (
        EXPECTED_SELECTED_EDGE_DIGEST
    ):
        raise AssertionError(
            "selected graph reproduction drift", edges, edge_digest.hexdigest()
        )

    queue = [index for index, degree in enumerate(indegree) if degree == 0]
    heapq.heapify(queue)
    order = []
    while queue:
        source = heapq.heappop(queue)
        order.append(source)
        for target in adjacency[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(queue, target)
    if len(order) != len(nodes):
        raise AssertionError("selected policy graph is no longer acyclic")
    rank = [0] * len(nodes)
    for source in reversed(order):
        if adjacency[source]:
            rank[source] = 1 + max(rank[target] for target in adjacency[source])
    if max(rank) != EXPECTED_MAXIMUM_RANK:
        raise AssertionError("selected graph rank height drift", max(rank))
    rank_digest = hashlib.sha256()
    rank_by_step = [dict() for _step in MENU]
    for (step, site), value in zip(nodes, rank):
        rank_by_step[step][site] = value
        rank_digest.update(struct.pack("<5i", step, *decode_site(site), value))
    if rank_digest.hexdigest() != EXPECTED_RANK_DIGEST:
        raise AssertionError("selected rank stream digest drift", rank_digest.hexdigest())
    return tuple(rank_by_step), {
        "vertices": len(nodes),
        "edges": edges,
        "edge_stream_sha256": edge_digest.hexdigest(),
        "maximum_rank": max(rank),
        "rank_stream_sha256": rank_digest.hexdigest(),
        "strictly_decreases_on_selected_edges": all(
            rank[source] > rank[target]
            for source, successors in enumerate(adjacency)
            for target in successors
        ),
    }


def target_preimages(candidate_sites, rank_by_step):
    result = []
    for step, sites in enumerate(candidate_sites):
        records = []
        for site in sites:
            vector = decode_site(site)
            preimage = inverse_image(vector)
            if preimage is not None:
                records.append((*preimage, site, rank_by_step[step][site]))
        result.append(tuple(records))
    return tuple(result)


def compute_bad_role_sparse(
    control_vector, target_step, source_info, preimages, pair_counts=None
):
    bad = 0
    cx, cy, cz = control_vector
    for dx, dy, dz, _target_site, target_rank in preimages[target_step]:
        x = cx + dx
        y = cy + dy
        z = cz + dz
        if not (
            -SITE_RADIUS <= x <= SITE_RADIUS
            and -SITE_RADIUS <= y <= SITE_RADIUS
            and -SITE_RADIUS <= z <= SITE_RADIUS
        ):
            continue
        source = source_info.get(
            (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE
            + (y + SITE_RADIUS) * SITE_SIDE
            + z
            + SITE_RADIUS
        )
        if source is None:
            continue
        source_index, source_rank = source
        if pair_counts is not None:
            pair_counts[source_rank * 3 + target_rank] += 1
        if source_rank <= target_rank:
            bad |= 1 << source_index
    return bad


def compute_bad_role_direct(
    control_vector, target_step, source_sites, source_rank, rank_by_step
):
    bad = 0
    target_rank = rank_by_step[target_step]
    for source_index, source_site in enumerate(source_sites):
        source_vector = decode_site(source_site)
        image = apply_matrix(tuple(
            source_vector[axis] - control_vector[axis] for axis in range(3)
        ))
        image_site = maybe_encode_site(image)
        if image_site is None:
            continue
        image_rank = target_rank.get(image_site)
        if image_rank is not None and source_rank[source_site] <= image_rank:
            bad |= 1 << source_index
    return bad


def rejected_witness(
    cache, word_start, length, source_step, source_sites, source_rank,
    rank_by_step, role_cache, violating_index
):
    source_site = source_sites[violating_index]
    source_vector = decode_site(source_site)
    position = (0, 0, 0)
    word = tuple(cache[word_start:word_start + length])
    for slot, target_step in enumerate(word):
        control_site = encode_site(position)
        bad = role_cache[control_site * len(MENU) + target_step]
        if bad & (1 << violating_index):
            target_vector = apply_matrix(tuple(
                source_vector[axis] - position[axis] for axis in range(3)
            ))
            target_site = encode_site(target_vector)
            return {
                "word": list(word),
                "slot_zero_based": slot,
                "target_step": target_step,
                "control": list(position),
                "source_site": list(source_vector),
                "target_site": list(target_vector),
                "source_rank": source_rank[source_site],
                "target_rank": rank_by_step[target_step][target_site],
            }
        child = MENU[target_step]
        position = tuple(position[axis] + child[axis] for axis in range(3))
    raise AssertionError("rejected word supplied no concrete bad role witness")


def quantiles(values):
    ordered = sorted(values)
    return {
        "minimum": ordered[0],
        "lower_quartile": ordered[len(ordered) // 4],
        "median": ordered[len(ordered) // 2],
        "upper_quartile": ordered[(3 * len(ordered)) // 4],
        "maximum": ordered[-1],
    }


def scan_compatible_words(
    cache_path, blocks, candidate_sites, rank_by_step, actions, started
):
    preimages = target_preimages(candidate_sites, rank_by_step)
    total_words = 0
    total_slots = 0
    total_roles = 0
    total_digit_simple = 0
    total_compatible = 0
    total_compatible_digit_simple = 0
    total_compatible_intrinsic = 0
    total_zero_bad = 0
    pair_counts = [0] * 9
    role_digest = hashlib.sha256()
    compatible_ordinal_digest = hashlib.sha256()
    combined_ordinal_digest = hashlib.sha256()
    step_records = []
    baseline_ordered_total = 0
    baseline_role_total = 0
    selected_acceptances = 0
    bitset_blocks = []

    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for block in blocks:
                source_step = block["step"]
                source_sites = candidate_sites[source_step]
                source_rank = rank_by_step[source_step]
                source_info = {
                    site: (index, source_rank[site])
                    for index, site in enumerate(source_sites)
                }
                role_cache = {}
                role_bad_histogram = Counter()
                direct_checks = 0
                ordered_masks = set()
                role_masks = set()
                compatible_masks = set()
                compatible_digit_masks = set()
                compatible_intrinsic_masks = set()
                accepted_bits = bytearray((block["words"] + 7) // 8)
                combined_bits = bytearray((block["words"] + 7) // 8)
                rejected_example = None
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
                    x = y = z = 0
                    interior_mask = 0
                    bad_union = 0
                    lateral_codes = []
                    lateral_fibres = []
                    digit_bits = 0
                    repeated_digit = False
                    all_digits_nonzero = True

                    for position in range(length):
                        child = cache[cursor + position]
                        control_site = (
                            (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE
                            + (y + SITE_RADIUS) * SITE_SIDE
                            + z
                            + SITE_RADIUS
                        )
                        role_key = control_site * len(MENU) + child
                        bad = role_cache.get(role_key)
                        if bad is None:
                            bad = compute_bad_role_sparse(
                                (x, y, z), child, source_info, preimages,
                                pair_counts,
                            )
                            role_cache[role_key] = bad
                            role_bad_histogram[bad.bit_count()] += 1
                            if direct_checks < DIRECT_ROLE_CHECKS_PER_STEP:
                                direct = compute_bad_role_direct(
                                    (x, y, z),
                                    child,
                                    source_sites,
                                    source_rank,
                                    rank_by_step,
                                )
                                if direct != bad:
                                    raise AssertionError(
                                        "sparse/direct role mask mismatch",
                                        source_step,
                                        child,
                                        (x, y, z),
                                    )
                                direct_checks += 1
                        bad_union |= bad

                        x += MENU_X[child]
                        y += MENU_Y[child]
                        z += MENU_Z[child]
                        if position + 1 < length:
                            interior_site = (
                                (x + SITE_RADIUS) * SITE_SIDE * SITE_SIDE
                                + (y + SITE_RADIUS) * SITE_SIDE
                                + z
                                + SITE_RADIUS
                            )
                            interior_mask |= 1 << source_info[interior_site][0]
                            lateral_codes.append(
                                (y + SITE_RADIUS) * SITE_SIDE + z + SITE_RADIUS
                            )
                            lateral_fibres.append((y, z))
                            digit = (y - 3 * z) % 9
                            bit = 1 << digit
                            repeated_digit = repeated_digit or bool(
                                digit_bits & bit
                            )
                            digit_bits |= bit
                            all_digits_nonzero = (
                                all_digits_nonzero and digit != 0
                            )

                    if (x, y, z) != endpoint:
                        raise AssertionError(
                            "second-pass endpoint drift", source_step, ordinal
                        )
                    ordered_signature = packed_projection_signature(lateral_codes)
                    role_signature = packed_projection_signature(
                        sorted(lateral_codes)
                    )
                    ordered_masks.add(ordered_signature)
                    role_masks.add(role_signature)
                    digit_simple = all_digits_nonzero and not repeated_digit
                    intrinsic = (
                        len(set(lateral_fibres)) == len(lateral_fibres)
                        and not endpoint_fibres.intersection(lateral_fibres)
                    )
                    compatible = not (bad_union & ~interior_mask)

                    counts["words"] += 1
                    counts["slots"] += length
                    counts["digit_simple_words"] += int(digit_simple)
                    counts["intrinsic_fibre_clean_words"] += int(intrinsic)
                    counts["potential_compatible_words"] += int(compatible)
                    counts["potential_compatible_digit_simple_words"] += int(
                        compatible and digit_simple
                    )
                    counts["potential_compatible_intrinsic_fibre_clean_words"] += int(
                        compatible and intrinsic
                    )
                    counts["zero_bad_words"] += int(compatible and bad_union == 0)
                    counts["nonzero_bad_covered_words"] += int(
                        compatible and bad_union != 0
                    )
                    if compatible:
                        accepted_bits[(ordinal - 1) >> 3] |= 1 << (
                            (ordinal - 1) & 7
                        )
                        compatible_masks.add(role_signature)
                        if digit_simple:
                            combined_bits[(ordinal - 1) >> 3] |= 1 << (
                                (ordinal - 1) & 7
                            )
                            compatible_digit_masks.add(role_signature)
                        if intrinsic:
                            compatible_intrinsic_masks.add(role_signature)
                    elif rejected_example is None:
                        violating = (bad_union & ~interior_mask & -(
                            bad_union & ~interior_mask
                        )).bit_length() - 1
                        rejected_example = {
                            "ordinal_1_based": ordinal,
                            **rejected_witness(
                                cache,
                                word_start,
                                length,
                                source_step,
                                source_sites,
                                source_rank,
                                rank_by_step,
                                role_cache,
                                violating,
                            ),
                        }

                    if ordinal == selected["ordinal"]:
                        observed_word = tuple(cache[word_start:word_end])
                        if observed_word != selected["word"]:
                            raise AssertionError("selected policy ordinal drift")
                        if not compatible or not intrinsic:
                            raise AssertionError(
                                "selected policy word fails repaired filter",
                                source_step,
                            )
                        selected_acceptances += 1

                    cursor = word_end
                    observed_slots += length
                    total_words += 1
                    total_slots += length
                    if total_words % 500_000 == 0:
                        enforce_runtime(started, "potential-compatible pass")

                if cursor != block["end"] or observed_slots != block["word_slots"]:
                    raise AssertionError("second-pass block boundary drift", source_step)
                if direct_checks != DIRECT_ROLE_CHECKS_PER_STEP:
                    raise AssertionError("too few direct role checks", source_step)
                if not counts["potential_compatible_words"]:
                    raise AssertionError("step retained no potential-compatible action")

                step_role_digest = hashlib.sha256()
                for role_key in sorted(role_cache):
                    control_site, target_step = divmod(role_key, len(MENU))
                    role_header = (
                        source_step,
                        target_step,
                        *decode_site(control_site),
                    )
                    digest_integer_record(role_digest, role_header)
                    digest_integer_record(step_role_digest, role_header)
                    bad = role_cache[role_key]
                    for source_index in iter_mask(bad):
                        role_source = (
                            source_step,
                            *decode_site(source_sites[source_index]),
                        )
                        digest_integer_record(role_digest, role_source)
                        digest_integer_record(step_role_digest, role_source)
                compatible_ordinal_digest.update(struct.pack("<II", source_step, len(accepted_bits)))
                compatible_ordinal_digest.update(accepted_bits)
                combined_ordinal_digest.update(struct.pack("<II", source_step, len(combined_bits)))
                combined_ordinal_digest.update(combined_bits)
                bitset_blocks.append({
                    "step": source_step,
                    "words": block["words"],
                    "potential_compatible": bytes(accepted_bits),
                    "potential_compatible_count": counts[
                        "potential_compatible_words"
                    ],
                    "potential_compatible_digit_simple": bytes(combined_bits),
                    "potential_compatible_digit_simple_count": counts[
                        "potential_compatible_digit_simple_words"
                    ],
                })

                total_roles += len(role_cache)
                total_digit_simple += counts["digit_simple_words"]
                total_compatible += counts["potential_compatible_words"]
                total_compatible_digit_simple += counts[
                    "potential_compatible_digit_simple_words"
                ]
                total_compatible_intrinsic += counts[
                    "potential_compatible_intrinsic_fibre_clean_words"
                ]
                total_zero_bad += counts["zero_bad_words"]
                baseline_ordered_total += len(ordered_masks)
                baseline_role_total += len(role_masks)
                step_records.append({
                    "step": source_step,
                    "parent_step": list(MENU[source_step]),
                    **dict(counts),
                    "ordered_projection_signatures": len(ordered_masks),
                    "projection_role_masks": len(role_masks),
                    "potential_compatible_projection_role_masks": len(
                        compatible_masks
                    ),
                    "potential_compatible_digit_simple_projection_role_masks": len(
                        compatible_digit_masks
                    ),
                    "potential_compatible_intrinsic_fibre_clean_projection_role_masks": len(
                        compatible_intrinsic_masks
                    ),
                    "distinct_ordered_slot_roles": len(role_cache),
                    "bad_role_stream_sha256": step_role_digest.hexdigest(),
                    "selected_policy_word_accepted": True,
                    "role_bad_source_count_histogram": {
                        str(key): value
                        for key, value in sorted(role_bad_histogram.items())
                    },
                    "first_rejected_exact_witness": rejected_example,
                })
                del role_cache, source_info
                enforce_runtime(started, f"completed source step {source_step}")
        finally:
            cache.close()

    expected_words = sum(block["words"] for block in blocks)
    expected_slots = sum(block["word_slots"] for block in blocks)
    if total_words != expected_words or total_slots != expected_slots:
        raise AssertionError("second-pass total drift")
    full_scan = (
        len(blocks) == len(MENU)
        and [block["step"] for block in blocks] == list(range(len(MENU)))
    )
    if full_scan:
        if total_roles != EXPECTED_ROLE_TYPES:
            raise AssertionError("ordered slot-role census drift", total_roles)
        if baseline_ordered_total != EXPECTED_ORDERED_PROJECTION_SIGNATURES:
            raise AssertionError("ordered projection signature census drift")
        if baseline_role_total != EXPECTED_PROJECTION_ROLE_MASKS:
            raise AssertionError("projection role-mask census drift")
        if total_digit_simple != EXPECTED_DIGIT_SIMPLE_WORDS:
            raise AssertionError("digit-simple word census drift", total_digit_simple)
    if selected_acceptances != len(blocks):
        raise AssertionError("not every selected policy word was recovered")

    compatible_counts = [
        record["potential_compatible_words"] for record in step_records
    ]
    combined_counts = [
        record["potential_compatible_digit_simple_words"]
        for record in step_records
    ]
    compatible_masks = [
        record["potential_compatible_projection_role_masks"]
        for record in step_records
    ]
    combined_masks = [
        record["potential_compatible_digit_simple_projection_role_masks"]
        for record in step_records
    ]
    result = {
        "step_scope": [blocks[0]["step"], blocks[-1]["step"]],
        "definition": {
            "bad_slot_mask": (
                "B(s,t,c)={x in C_s: M(x-c) in C_t and "
                "r(s,x)<=r(t,M(x-c))}"
            ),
            "whole_word_acceptance": (
                "union of the exact bad masks of all ordered slots of w is "
                "a subset of that same word's exact proper-interior set I_s(w)"
            ),
            "digit_simple": (
                "all proper lateral-prefix digits q(y,z)=y-3z mod 9 are "
                "nonzero and pairwise distinct"
            ),
            "intrinsic_fibre_clean": (
                "proper (y,z) fibres are pairwise distinct and avoid both "
                "endpoint fibres"
            ),
            "projection_role_mask": (
                "unordered multiset of exact proper lateral-prefix offsets; "
                "multiplicity retained"
            ),
        },
        "census": {
            "words": total_words,
            "slots": total_slots,
            "distinct_ordered_slot_roles": total_roles,
            "rank_pair_edge_counts": {
                f"{source_rank}->{target_rank}": pair_counts[
                    source_rank * 3 + target_rank
                ]
                for source_rank in range(3)
                for target_rank in range(3)
            },
            "bad_role_stream_sha256": role_digest.hexdigest(),
            "digit_simple_words": total_digit_simple,
            "potential_compatible_words": total_compatible,
            "potential_compatible_digit_simple_words": (
                total_compatible_digit_simple
            ),
            "potential_compatible_intrinsic_fibre_clean_words": (
                total_compatible_intrinsic
            ),
            "zero_bad_potential_compatible_words": total_zero_bad,
            "nonzero_bad_covered_potential_compatible_words": (
                total_compatible - total_zero_bad
            ),
            "baseline_ordered_projection_signatures": baseline_ordered_total,
            "baseline_projection_role_masks": baseline_role_total,
            "compatible_ordinal_bitsets_sha256": (
                compatible_ordinal_digest.hexdigest()
            ),
            "compatible_digit_simple_ordinal_bitsets_sha256": (
                combined_ordinal_digest.hexdigest()
            ),
            "all_124_selected_policy_words_accepted": True,
            "steps_with_zero_potential_compatible_words": [
                record["step"]
                for record in step_records
                if record["potential_compatible_words"] == 0
            ],
            "steps_with_zero_potential_compatible_digit_simple_words": [
                record["step"]
                for record in step_records
                if record["potential_compatible_digit_simple_words"] == 0
            ],
            "steps_with_zero_potential_compatible_intrinsic_fibre_clean_words": [
                record["step"]
                for record in step_records
                if record[
                    "potential_compatible_intrinsic_fibre_clean_words"
                ] == 0
            ],
        },
        "per_step_action_count_quantiles": {
            "potential_compatible_words": quantiles(compatible_counts),
            "potential_compatible_digit_simple_words": quantiles(combined_counts),
            "potential_compatible_projection_role_masks": quantiles(
                compatible_masks
            ),
            "potential_compatible_digit_simple_projection_role_masks": quantiles(
                combined_masks
            ),
        },
        "step_records": step_records,
    }
    return result, tuple(bitset_blocks)


def synthetic_self_check():
    for x in range(-SITE_RADIUS, SITE_RADIUS + 1):
        for y in range(-SITE_RADIUS, SITE_RADIUS + 1):
            for z in range(-SITE_RADIUS, SITE_RADIUS + 1):
                vector = x, y, z
                preimage = inverse_image(vector)
                if (preimage is not None) != (
                    x % 3 == 0 and y % 3 == 0 and (z - y // 3) % 3 == 0
                ):
                    raise AssertionError("inverse-image lattice predicate drift")

    candidate_sites = (
        tuple(sorted(map(encode_site, ((0, 0, 0), (1, 0, 0), (2, 0, 0))))),
        tuple(sorted(map(encode_site, ((0, 0, 0), (3, 0, 0), (6, 0, 0))))),
    )
    ranks = (
        {
            encode_site((0, 0, 0)): 0,
            encode_site((1, 0, 0)): 1,
            encode_site((2, 0, 0)): 2,
        },
        {
            encode_site((0, 0, 0)): 0,
            encode_site((3, 0, 0)): 1,
            encode_site((6, 0, 0)): 2,
        },
    )
    preimages = target_preimages(candidate_sites, ranks)
    source_info = {
        site: (index, ranks[0][site])
        for index, site in enumerate(candidate_sites[0])
    }
    comparisons = 0
    for control in ((0, 0, 0), (1, 0, 0), (-1, 0, 0)):
        for target in range(2):
            sparse = compute_bad_role_sparse(
                control, target, source_info, preimages
            )
            direct = compute_bad_role_direct(
                control, target, candidate_sites[0], ranks[0], ranks
            )
            if sparse != direct:
                raise AssertionError("synthetic sparse/direct mismatch")
            comparisons += 1
    # A word-level subset test: one bad bit is accepted only when that exact
    # source site belongs to the same word's interior mask.
    bad = 1 << 1
    if bad & ~(1 << 1) or not (bad & ~(1 << 0)):
        raise AssertionError("whole-word subset predicate drift")
    sidecar_blocks = (
        {
            "step": 0,
            "words": 3,
            "potential_compatible": bytes((0b00000101,)),
            "potential_compatible_count": 2,
            "potential_compatible_digit_simple": bytes((0b00000001,)),
            "potential_compatible_digit_simple_count": 1,
        },
        {
            "step": 1,
            "words": 9,
            "potential_compatible": bytes((0b11111111, 0b00000001)),
            "potential_compatible_count": 9,
            "potential_compatible_digit_simple": bytes((0b01010101, 0)),
            "potential_compatible_digit_simple_count": 4,
        },
    )
    with tempfile.TemporaryDirectory(prefix="nonx-potential-self-check-") as directory:
        sidecar_metadata = write_bitset_sidecar(
            sidecar_blocks, Path(directory) / "tiny.bin"
        )
        decoded = read_bitset_sidecar(sidecar_metadata)
        if decoded != sidecar_blocks:
            raise AssertionError("bitset sidecar roundtrip drift")
    return {
        "status": "passed",
        "exact_inverse_vectors_tested": SITE_COUNT,
        "sparse_direct_role_comparisons": comparisons,
        "whole_word_subset_cases": 2,
        "bitset_sidecar_roundtrip_blocks": len(sidecar_blocks),
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
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_bitset_sidecar(blocks, output_path):
    """Atomically emit exact cache-ordinal membership for two filters."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=output_path.name + ".", dir=output_path.parent
    )
    records = []
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(BITSET_MAGIC)
            handle.write(struct.pack("<II", 1, len(blocks)))
            prior_step = -1
            for block in blocks:
                expected_step = block["step"]
                if not prior_step < expected_step < len(MENU):
                    raise AssertionError("bitset block step order drift")
                prior_step = expected_step
                words = block["words"]
                byte_count = (words + 7) // 8
                first = block["potential_compatible"]
                second = block["potential_compatible_digit_simple"]
                if len(first) != byte_count or len(second) != byte_count:
                    raise AssertionError("bitset byte length drift", expected_step)
                valid_last_bits = words & 7
                if valid_last_bits:
                    padding_mask = ~((1 << valid_last_bits) - 1) & 0xFF
                    if first[-1] & padding_mask or second[-1] & padding_mask:
                        raise AssertionError("nonzero bitset padding", expected_step)
                first_count = sum(byte.bit_count() for byte in first)
                second_count = sum(byte.bit_count() for byte in second)
                if first_count != block["potential_compatible_count"] or (
                    second_count
                    != block["potential_compatible_digit_simple_count"]
                ):
                    raise AssertionError("bitset population count drift")

                block_offset = handle.tell()
                handle.write(struct.pack(
                    "<IIIII",
                    expected_step,
                    words,
                    byte_count,
                    first_count,
                    second_count,
                ))
                first_offset = handle.tell()
                handle.write(first)
                second_offset = handle.tell()
                handle.write(second)
                block_end = handle.tell()
                records.append({
                    "step": expected_step,
                    "words": words,
                    "block_offset": block_offset,
                    "block_bytes": block_end - block_offset,
                    "potential_compatible": {
                        "offset": first_offset,
                        "bytes": byte_count,
                        "set_bits": first_count,
                        "sha256": hashlib.sha256(first).hexdigest(),
                    },
                    "potential_compatible_digit_simple": {
                        "offset": second_offset,
                        "bytes": byte_count,
                        "set_bits": second_count,
                        "sha256": hashlib.sha256(second).hexdigest(),
                    },
                    "unused_high_bits_in_final_byte_are_zero": True,
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
    return {
        "path": str(output_path),
        "sha256": file_sha256(output_path),
        "bytes": output_path.stat().st_size,
        "format": (
            "8-byte NPOTB001 magic; uint32 schema=1; uint32 steps; then per "
            "step <uint32 step,words,bytes,potential_count,combined_count> "
            "followed by potential and potential+digit-simple ordinal bitsets"
        ),
        "ordinal_convention": (
            "bit k of a step channel is cache ordinal k+1; least-significant "
            "bit first within each byte"
        ),
        "blocks": records,
    }


def prepare_candidate_rank(metadata_path, cache_path, fixed_policy_path):
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = file_sha256(checker_path)
    policy = resource_policy(enforce=True)
    self_check = synthetic_self_check()
    snapshots, blocks, fixed_records = load_inputs(
        metadata_path, cache_path, fixed_policy_path
    )
    candidate_sites, candidate_census = scan_candidate_sites(
        cache_path, blocks, started
    )
    actions = selected_actions(fixed_records, candidate_sites)
    rank_by_step, rank_census = reconstruct_rank(candidate_sites, actions)
    for snapshot in snapshots.values():
        verify_snapshot_unchanged(snapshot)
    if file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("checker changed during candidate/rank preparation")
    enforce_runtime(started, "candidate/rank preparation completed")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact prepared candidate-site and selected-potential table",
        "checker": {
            "path": "design/nonx_potential_compatible_word_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "pinned_input_sha256": {
            key: snapshot["sha256"] for key, snapshot in snapshots.items()
        },
        "synthetic_self_check": self_check,
        "candidate_site_reconstruction": candidate_census,
        "selected_policy_rank_reconstruction": rank_census,
        "candidate_rank_by_step": [
            [[site, rank_by_step[step][site]] for site in sites]
            for step, sites in enumerate(candidate_sites)
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def load_prepared(path, checker_sha256, snapshots, fixed_records):
    snapshot = file_snapshot(path)
    with Path(path).open() as handle:
        payload = json.load(handle)
    if payload["checker"]["sha256"] != checker_sha256:
        raise AssertionError("prepared table checker drift")
    expected_inputs = {
        key: item["sha256"] for key, item in snapshots.items()
    }
    if payload["pinned_input_sha256"] != expected_inputs:
        raise AssertionError("prepared table input commitment drift")
    raw = payload["candidate_rank_by_step"]
    if len(raw) != len(MENU):
        raise AssertionError("prepared table step count drift")
    candidate_sites = tuple(
        tuple(record[0] for record in step_records)
        for step_records in raw
    )
    stored_rank = tuple(
        {record[0]: record[1] for record in step_records}
        for step_records in raw
    )
    if any(tuple(sorted(sites)) != sites for sites in candidate_sites):
        raise AssertionError("prepared candidate order drift")
    actions = selected_actions(fixed_records, candidate_sites)
    reconstructed_rank, rank_census = reconstruct_rank(candidate_sites, actions)
    if reconstructed_rank != stored_rank:
        raise AssertionError("prepared rank table drift")
    if rank_census != payload["selected_policy_rank_reconstruction"]:
        raise AssertionError("prepared rank census drift")
    counts = [len(sites) for sites in candidate_sites]
    if sum(counts) != EXPECTED_CANDIDATE_SITES or (
        min(counts), max(counts)
    ) != EXPECTED_CANDIDATE_RANGE:
        raise AssertionError("prepared candidate census drift")
    digest = hashlib.sha256()
    for step, sites in enumerate(candidate_sites):
        for site in sites:
            digest_integer_record(digest, (step, *decode_site(site)))
    if digest.hexdigest() != EXPECTED_CANDIDATE_DIGEST:
        raise AssertionError("prepared candidate digest drift")
    return snapshot, candidate_sites, reconstructed_rank, actions, payload


def run_chunk(
    metadata_path,
    cache_path,
    fixed_policy_path,
    prepared_path,
    first_step,
    last_step,
    bitset_path,
):
    if not 0 <= first_step <= last_step < len(MENU):
        raise ValueError("invalid inclusive step range", first_step, last_step)
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = file_sha256(checker_path)
    policy = resource_policy(enforce=True)
    self_check = synthetic_self_check()
    snapshots, all_blocks, fixed_records = load_inputs(
        metadata_path, cache_path, fixed_policy_path
    )
    (
        prepared_snapshot,
        candidate_sites,
        rank_by_step,
        actions,
        prepared_payload,
    ) = load_prepared(
        prepared_path, checker_sha256, snapshots, fixed_records
    )
    blocks = all_blocks[first_step:last_step + 1]
    compatible, bitset_blocks = scan_compatible_words(
        cache_path,
        blocks,
        candidate_sites,
        rank_by_step,
        actions,
        started,
    )
    bitset_sidecar = write_bitset_sidecar(bitset_blocks, bitset_path)
    for snapshot in (*snapshots.values(), prepared_snapshot):
        verify_snapshot_unchanged(snapshot)
    if file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("checker changed during exact chunk scan")
    enforce_runtime(started, "chunk completed")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact source-step chunk of the full-cache whole-word potential "
            "filter; must be merged across all 124 steps"
        ),
        "checker": {
            "path": "design/nonx_potential_compatible_word_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "synthetic_self_check": self_check,
        "pinned_inputs": {
            key: {
                field: value
                for field, value in snapshot.items()
                if field != "identity"
            }
            for key, snapshot in snapshots.items()
        },
        "prepared_candidate_rank": {
            "path": prepared_snapshot["path"],
            "sha256": prepared_snapshot["sha256"],
            "bytes": prepared_snapshot["bytes"],
            "candidate_site_reconstruction": prepared_payload[
                "candidate_site_reconstruction"
            ],
            "selected_policy_rank_reconstruction": prepared_payload[
                "selected_policy_rank_reconstruction"
            ],
        },
        "step_scope_inclusive": [first_step, last_step],
        "potential_compatible_filter": compatible,
        "accepted_ordinal_bitset_sidecar": bitset_sidecar,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def read_bitset_sidecar(metadata):
    path = Path(metadata["path"])
    if file_sha256(path) != metadata["sha256"] or path.stat().st_size != metadata[
        "bytes"
    ]:
        raise AssertionError("chunk bitset sidecar commitment drift", path)
    data = path.read_bytes()
    if data[: len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("chunk bitset magic drift", path)
    version, blocks = struct.unpack_from("<II", data, len(BITSET_MAGIC))
    if version != 1 or blocks != len(metadata["blocks"]):
        raise AssertionError("chunk bitset header drift", path)
    result = []
    prior_end = len(BITSET_MAGIC) + 8
    for record in metadata["blocks"]:
        if record["block_offset"] != prior_end:
            raise AssertionError("chunk bitset block is not contiguous", path)
        header = struct.unpack_from("<IIIII", data, record["block_offset"])
        step, words, byte_count, first_count, second_count = header
        if (
            step != record["step"]
            or words != record["words"]
            or byte_count != record["potential_compatible"]["bytes"]
            or byte_count
            != record["potential_compatible_digit_simple"]["bytes"]
            or first_count != record["potential_compatible"]["set_bits"]
            or second_count
            != record["potential_compatible_digit_simple"]["set_bits"]
        ):
            raise AssertionError("chunk bitset block header drift", path, step)
        first_meta = record["potential_compatible"]
        second_meta = record["potential_compatible_digit_simple"]
        first = data[first_meta["offset"]:first_meta["offset"] + byte_count]
        second = data[second_meta["offset"]:second_meta["offset"] + byte_count]
        if hashlib.sha256(first).hexdigest() != first_meta["sha256"] or (
            hashlib.sha256(second).hexdigest() != second_meta["sha256"]
        ):
            raise AssertionError("chunk channel digest drift", path, step)
        if sum(byte.bit_count() for byte in first) != first_count or sum(
            byte.bit_count() for byte in second
        ) != second_count:
            raise AssertionError("chunk channel population drift", path, step)
        if words & 7:
            padding = ~((1 << (words & 7)) - 1) & 0xFF
            if first[-1] & padding or second[-1] & padding:
                raise AssertionError("chunk channel nonzero padding", path, step)
        prior_end = record["block_offset"] + record["block_bytes"]
        result.append({
            "step": step,
            "words": words,
            "potential_compatible": first,
            "potential_compatible_count": first_count,
            "potential_compatible_digit_simple": second,
            "potential_compatible_digit_simple_count": second_count,
        })
    if prior_end != len(data):
        raise AssertionError("chunk bitset trailing bytes", path)
    return tuple(result)


def aggregate_filters(filters, bitset_blocks):
    step_records = sorted(
        (
            record
            for result in filters
            for record in result["step_records"]
        ),
        key=lambda record: record["step"],
    )
    if [record["step"] for record in step_records] != list(range(len(MENU))):
        raise AssertionError("merged filter chunks do not partition all steps")
    if [block["step"] for block in bitset_blocks] != list(range(len(MENU))):
        raise AssertionError("merged bitset chunks do not partition all steps")
    for record, block in zip(step_records, bitset_blocks):
        if record["words"] != block["words"] or record[
            "potential_compatible_words"
        ] != block["potential_compatible_count"] or record[
            "potential_compatible_digit_simple_words"
        ] != block["potential_compatible_digit_simple_count"]:
            raise AssertionError("merged filter/bitset population mismatch")

    def total(field):
        return sum(record[field] for record in step_records)

    pair_counts = {
        f"{source_rank}->{target_rank}": sum(
            result["census"]["rank_pair_edge_counts"][
                f"{source_rank}->{target_rank}"
            ]
            for result in filters
        )
        for source_rank in range(3)
        for target_rank in range(3)
    }
    role_digest = hashlib.sha256()
    compatible_digest = hashlib.sha256()
    combined_digest = hashlib.sha256()
    for record, block in zip(step_records, bitset_blocks):
        role_digest.update(struct.pack("<I", record["step"]))
        role_digest.update(bytes.fromhex(record["bad_role_stream_sha256"]))
        first = block["potential_compatible"]
        second = block["potential_compatible_digit_simple"]
        compatible_digest.update(struct.pack("<II", record["step"], len(first)))
        compatible_digest.update(first)
        combined_digest.update(struct.pack("<II", record["step"], len(second)))
        combined_digest.update(second)

    words = total("words")
    slots = total("slots")
    roles = total("distinct_ordered_slot_roles")
    digit_simple = total("digit_simple_words")
    baseline_ordered = total("ordered_projection_signatures")
    baseline_masks = total("projection_role_masks")
    if (
        words != EXPECTED_WORDS
        or slots != EXPECTED_WORD_SLOTS
        or roles != EXPECTED_ROLE_TYPES
        or digit_simple != EXPECTED_DIGIT_SIMPLE_WORDS
        or baseline_ordered != EXPECTED_ORDERED_PROJECTION_SIGNATURES
        or baseline_masks != EXPECTED_PROJECTION_ROLE_MASKS
    ):
        raise AssertionError(
            "merged global census drift",
            words,
            slots,
            roles,
            digit_simple,
            baseline_ordered,
            baseline_masks,
        )
    compatible_counts = [
        record["potential_compatible_words"] for record in step_records
    ]
    combined_counts = [
        record["potential_compatible_digit_simple_words"]
        for record in step_records
    ]
    compatible_masks = [
        record["potential_compatible_projection_role_masks"]
        for record in step_records
    ]
    combined_masks = [
        record["potential_compatible_digit_simple_projection_role_masks"]
        for record in step_records
    ]
    return {
        "step_scope": [0, len(MENU) - 1],
        "definition": filters[0]["definition"],
        "census": {
            "words": words,
            "slots": slots,
            "distinct_ordered_slot_roles": roles,
            "rank_pair_edge_counts": pair_counts,
            "bad_role_per_step_digest_stream_sha256": role_digest.hexdigest(),
            "bad_role_per_step_digest_stream_definition": (
                "SHA-256 of concatenated <uint32 step,32-byte exact "
                "per-step bad-role-stream digest> records"
            ),
            "digit_simple_words": digit_simple,
            "potential_compatible_words": total("potential_compatible_words"),
            "potential_compatible_digit_simple_words": total(
                "potential_compatible_digit_simple_words"
            ),
            "potential_compatible_intrinsic_fibre_clean_words": total(
                "potential_compatible_intrinsic_fibre_clean_words"
            ),
            "zero_bad_potential_compatible_words": total("zero_bad_words"),
            "nonzero_bad_covered_potential_compatible_words": total(
                "nonzero_bad_covered_words"
            ),
            "baseline_ordered_projection_signatures": baseline_ordered,
            "baseline_projection_role_masks": baseline_masks,
            "compatible_ordinal_bitsets_sha256": compatible_digest.hexdigest(),
            "compatible_digit_simple_ordinal_bitsets_sha256": (
                combined_digest.hexdigest()
            ),
            "all_124_selected_policy_words_accepted": all(
                record["selected_policy_word_accepted"]
                for record in step_records
            ),
            "steps_with_zero_potential_compatible_words": [
                record["step"]
                for record in step_records
                if record["potential_compatible_words"] == 0
            ],
            "steps_with_zero_potential_compatible_digit_simple_words": [
                record["step"]
                for record in step_records
                if record["potential_compatible_digit_simple_words"] == 0
            ],
            "steps_with_zero_potential_compatible_intrinsic_fibre_clean_words": [
                record["step"]
                for record in step_records
                if record[
                    "potential_compatible_intrinsic_fibre_clean_words"
                ] == 0
            ],
        },
        "per_step_action_count_quantiles": {
            "potential_compatible_words": quantiles(compatible_counts),
            "potential_compatible_digit_simple_words": quantiles(combined_counts),
            "potential_compatible_projection_role_masks": quantiles(
                compatible_masks
            ),
            "potential_compatible_digit_simple_projection_role_masks": quantiles(
                combined_masks
            ),
        },
        "step_records": step_records,
    }


def merge_chunks(chunk_paths, output_bitset_path):
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = file_sha256(checker_path)
    chunks = []
    chunk_records = []
    for raw_path in chunk_paths:
        snapshot = file_snapshot(raw_path)
        with Path(raw_path).open() as handle:
            chunk = json.load(handle)
        if chunk["checker"]["sha256"] != checker_sha256:
            raise AssertionError("chunk checker drift", raw_path)
        chunks.append(chunk)
        chunk_records.append({
            "path": snapshot["path"],
            "sha256": snapshot["sha256"],
            "bytes": snapshot["bytes"],
            "step_scope_inclusive": chunk["step_scope_inclusive"],
            "elapsed_seconds": chunk["elapsed_seconds"],
            "maximum_resident_bytes": chunk["maximum_resident_bytes"],
        })
    chunks.sort(key=lambda chunk: chunk["step_scope_inclusive"][0])
    scopes = [chunk["step_scope_inclusive"] for chunk in chunks]
    expected_first = 0
    for first, last in scopes:
        if first != expected_first or last < first:
            raise AssertionError("chunk scopes are not a partition", scopes)
        expected_first = last + 1
    if expected_first != len(MENU):
        raise AssertionError("chunk scopes do not reach final step", scopes)
    reference = chunks[0]
    for chunk in chunks[1:]:
        if chunk["pinned_inputs"] != reference["pinned_inputs"] or chunk[
            "prepared_candidate_rank"
        ] != reference["prepared_candidate_rank"]:
            raise AssertionError("chunk input/prepared commitments disagree")
    bitset_blocks = tuple(
        block
        for chunk in chunks
        for block in read_bitset_sidecar(
            chunk["accepted_ordinal_bitset_sidecar"]
        )
    )
    filters = [chunk["potential_compatible_filter"] for chunk in chunks]
    compatible = aggregate_filters(filters, bitset_blocks)
    bitset_sidecar = write_bitset_sidecar(bitset_blocks, output_bitset_path)
    if file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("checker changed during chunk merge")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact merged full-cache whole-word filter under the pinned "
            "height-two non-x potential; not an availability theorem"
        ),
        "checker": {
            "path": "design/nonx_potential_compatible_word_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_merge": True,
        },
        "chunk_runs": chunk_records,
        "pinned_inputs": reference["pinned_inputs"],
        "candidate_site_reconstruction": reference[
            "prepared_candidate_rank"
        ]["candidate_site_reconstruction"],
        "selected_policy_rank_reconstruction": reference[
            "prepared_candidate_rank"
        ]["selected_policy_rank_reconstruction"],
        "prepared_candidate_rank": {
            key: value
            for key, value in reference["prepared_candidate_rank"].items()
            if key not in {
                "candidate_site_reconstruction",
                "selected_policy_rank_reconstruction",
            }
        },
        "potential_compatible_filter": compatible,
        "accepted_ordinal_bitset_sidecar": bitset_sidecar,
        "proved_by_this_probe": [
            "the pinned selected-policy graph and its exact height-two rank are reproduced by their published edge and rank digests",
            "every retained whole word induces only direction-blind degenerate edges that strictly descend that same rank",
            "the conclusion is closed under arbitrary whole-word switching among retained actions because all retained actions share the rank",
            "the source-step chunks exactly partition all 12,537,146 cache words and 55,513,526 ordered slots",
        ],
        "not_proved": [
            "that any retained word is legal or survives in every chronological ordered-path state",
            "positive connector availability after current near/far poison and evolving x-projection occupancy are imposed",
            "control of nondegenerate selector edges, births, empty-effect re-entry, cursor jumps, or endpoint/deep-deep secants",
            "a state-dependent greatest fixed point, a uniform far-secant lemma, or Erdős #193",
        ],
        "merge_elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def run(metadata_path, cache_path, fixed_policy_path, bitset_path):
    started = time.monotonic()
    checker_path = Path(__file__).resolve()
    checker_sha256 = file_sha256(checker_path)
    policy = resource_policy(enforce=True)
    self_check = synthetic_self_check()
    snapshots, blocks, fixed_records = load_inputs(
        metadata_path, cache_path, fixed_policy_path
    )
    candidate_sites, candidate_census = scan_candidate_sites(
        cache_path, blocks, started
    )
    actions = selected_actions(fixed_records, candidate_sites)
    rank_by_step, rank_census = reconstruct_rank(candidate_sites, actions)
    compatible, bitset_blocks = scan_compatible_words(
        cache_path,
        blocks,
        candidate_sites,
        rank_by_step,
        actions,
        started,
    )
    bitset_sidecar = write_bitset_sidecar(bitset_blocks, bitset_path)
    for snapshot in snapshots.values():
        verify_snapshot_unchanged(snapshot)
    if file_sha256(checker_path) != checker_sha256:
        raise RuntimeError("checker changed during exact scan")
    enforce_runtime(started, "completed")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact finite full-cache whole-word filter under the pinned "
            "height-two non-x potential; not an availability theorem"
        ),
        "checker": {
            "path": "design/nonx_potential_compatible_word_probe.py",
            "sha256": checker_sha256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "pinned_inputs": {
            key: {
                field: value
                for field, value in snapshot.items()
                if field != "identity"
            }
            for key, snapshot in snapshots.items()
        },
        "synthetic_self_check": self_check,
        "candidate_site_reconstruction": candidate_census,
        "selected_policy_rank_reconstruction": rank_census,
        "potential_compatible_filter": compatible,
        "accepted_ordinal_bitset_sidecar": bitset_sidecar,
        "proved_by_this_probe": [
            "the pinned selected-policy graph and its exact height-two rank are reproduced byte-for-byte by their published edge and rank digests",
            "a retained whole word induces only direction-blind degenerate edges that strictly descend that same rank",
            "the conclusion is closed under arbitrary whole-word switching among retained words because every retained action shares the rank",
            "all full-cache words, slots, exact interiors, and ordered roles are scanned without combining data from different words",
            "the exact per-step action and projection-role-mask counts show whether either the potential-only or stronger digit-simple intersection is empty",
        ],
        "not_proved": [
            "that any retained word is legal or survives in every chronological ordered-path state",
            "positive connector availability after current near/far poison and evolving x-projection occupancy are imposed",
            "control of nondegenerate selector edges, births, empty-effect re-entry, cursor jumps, or endpoint/deep-deep secants",
            "a state-dependent greatest fixed point, a uniform far-secant lemma, or Erdős #193",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def estimate():
    return {
        "status": "no input files opened and no cache scanned",
        "algorithm": (
            "one prepare pass for candidate sites/rank, two disjoint source-step "
            "filter chunks using sparse exact M-inverse role masks, then a "
            "subsecond exact merge"
        ),
        "expected_total_cache_bytes_read": 2 * EXPECTED_CACHE_BYTES,
        "expected_prepare_words": EXPECTED_WORDS,
        "expected_filter_words_partitioned_across_chunks": EXPECTED_WORDS,
        "expected_filter_slots_partitioned_across_chunks": EXPECTED_WORD_SLOTS,
        "suggested_chunk_step_ranges_inclusive": [[0, 60], [61, 123]],
        "expected_prepare_wall_seconds_range": [25, 40],
        "expected_each_chunk_wall_seconds_range": [45, 85],
        "hard_wall_seconds_per_process": MAX_SECONDS,
        "expected_maximum_resident_bytes": 160 * 1024 * 1024,
        "hard_maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "simultaneous_processes": 1,
        "required_threads": 1,
        "required_minimum_nice": 15,
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("estimate")
    subparsers.add_parser("self-check")
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    prepare_parser.add_argument("--cache", default=DEFAULT_CACHE)
    prepare_parser.add_argument("--fixed-policy", default=DEFAULT_FIXED_POLICY)
    prepare_parser.add_argument("--output", default=DEFAULT_PREPARED)
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
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    run_parser.add_argument("--cache", default=DEFAULT_CACHE)
    run_parser.add_argument("--fixed-policy", default=DEFAULT_FIXED_POLICY)
    run_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    run_parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    args = parser.parse_args()
    if args.command == "estimate":
        print(json.dumps(estimate(), sort_keys=True, indent=2))
        return
    if args.command == "self-check":
        print(json.dumps(synthetic_self_check(), sort_keys=True, indent=2))
        return
    if args.command == "prepare":
        payload = prepare_candidate_rank(
            args.metadata, args.cache, args.fixed_policy
        )
        atomic_json_dump(payload, args.output)
        print(json.dumps({
            "output": str(Path(args.output).resolve()),
            "checker": payload["checker"],
            "candidate_site_reconstruction": payload[
                "candidate_site_reconstruction"
            ],
            "selected_policy_rank_reconstruction": payload[
                "selected_policy_rank_reconstruction"
            ],
            "elapsed_seconds": payload["elapsed_seconds"],
            "maximum_resident_bytes": payload["maximum_resident_bytes"],
        }, sort_keys=True, indent=2))
        return
    if args.command == "chunk":
        payload = run_chunk(
            args.metadata,
            args.cache,
            args.fixed_policy,
            args.prepared,
            args.first_step,
            args.last_step,
            args.bitsets,
        )
        atomic_json_dump(payload, args.output)
        print(json.dumps({
            "output": str(Path(args.output).resolve()),
            "step_scope_inclusive": payload["step_scope_inclusive"],
            "census": payload["potential_compatible_filter"]["census"],
            "quantiles": payload["potential_compatible_filter"][
                "per_step_action_count_quantiles"
            ],
            "accepted_ordinal_bitset_sidecar": {
                key: value
                for key, value in payload[
                    "accepted_ordinal_bitset_sidecar"
                ].items()
                if key != "blocks"
            },
            "elapsed_seconds": payload["elapsed_seconds"],
            "maximum_resident_bytes": payload["maximum_resident_bytes"],
        }, sort_keys=True, indent=2))
        return
    if args.command == "merge":
        payload = merge_chunks(args.chunks, args.bitsets)
        atomic_json_dump(payload, args.output)
        print(json.dumps({
            "output": str(Path(args.output).resolve()),
            "checker": payload["checker"],
            "census": payload["potential_compatible_filter"]["census"],
            "quantiles": payload["potential_compatible_filter"][
                "per_step_action_count_quantiles"
            ],
            "accepted_ordinal_bitset_sidecar": {
                key: value
                for key, value in payload[
                    "accepted_ordinal_bitset_sidecar"
                ].items()
                if key != "blocks"
            },
            "merge_elapsed_seconds": payload["merge_elapsed_seconds"],
            "maximum_resident_bytes": payload["maximum_resident_bytes"],
        }, sort_keys=True, indent=2))
        return
    payload = run(args.metadata, args.cache, args.fixed_policy, args.bitsets)
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "checker": payload["checker"],
        "accepted_ordinal_bitset_sidecar": {
            key: value
            for key, value in payload[
                "accepted_ordinal_bitset_sidecar"
            ].items()
            if key != "blocks"
        },
        "census": payload["potential_compatible_filter"]["census"],
        "quantiles": payload["potential_compatible_filter"][
            "per_step_action_count_quantiles"
        ],
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_bytes": payload["maximum_resident_bytes"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
