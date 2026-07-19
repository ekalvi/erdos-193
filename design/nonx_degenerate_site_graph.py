#!/usr/bin/env python3
"""Exact non-x consecutive-effect graph from the compact connector cache.

For a source candidate site ``x``, a selected child slot with prefix control
``c``, and a successor candidate site ``x'``, Lemmas 3.4--3.6 give the exact
consecutive-hit equation

    (x' - M (x-c)) cross (M g) = 0.

If the bracketed displacement is zero, every line direction through ``x`` is
carried through ``x'``.  These direction-blind transitions form the finite
degenerate-site graph checked here.  If it is nonzero, the successor primitive
direction is forced to ``canonprim(x' - M (x-c))``.  The checker also computes
the exact finite union of these selector directions.

The input is the compact effective-domain cache emitted by
``no_new_x_line_constructor.py`` and the companion canonical JSON containing
its block table.  This checker never loads either connector-domain pickle.

Run the lightweight estimate first:

    python3 -B design/nonx_degenerate_site_graph.py estimate

Run the exact scan on one low-priority thread only after approval:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/nonx_degenerate_site_graph.py run \
        --metadata /tmp/no-new-x-line-L5-canonical.json \
        --cache /tmp/no-new-x-line-domains.bin \
        --output /tmp/nonx-degenerate-site-graph-canonical.json

An acyclic result supplies a uniform bound only for a carried line that hits a
candidate site at every synchronized stitch.  A cycle refutes a purely
height/direction-based escape argument for the full connector menu, but it is
not by itself a realizable infinite ordered walk: global legality, the
history-dependent no-new-x-line filter, cursor jumps, births, and latent
effectless re-entry are outside this finite graph.

The checker now emits a second, strictly refined compatibility graph.  It
keeps a labelled degenerate arc only when some exact cache word/slot realizes
the transition and that word's full interior avoids the carried poison site.
This removes the most immediate self-poison defect, but not poisoning at a
different interior point or compatibility with the rest of a realized path.

The selector union has the identical arbitrary-switching semantics as the
legacy nested pair loop.  Identical bases and successor-site sets are merged,
then exact 16-bit-lane integer polynomial multiplication computes difference
support.  A reduced legacy-loop equivalence test is mandatory on every run.

Graph arcs are deduplicated only within one source phase, then written as
strictly sorted 12-byte records.  The original and x-avoiding graphs are
memory-mapped and analyzed sequentially with one compact reverse CSR, so no
global Python edge set or duplicate pair of adjacency dictionaries survives.
"""

from __future__ import annotations

import argparse
import array
import gc
import hashlib
import heapq
import json
import math
import mmap
import os
import resource
import struct
import sys
import tempfile
import time
from collections import Counter, defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_OUTPUT = Path("/tmp/nonx-degenerate-site-graph-canonical.json")

EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_CACHE_BUILDER_SHA256 = (
    "6eca827ef7b6a4dfad57554bb89156fff79c2f495e89ba33e166aebbba21fffd"
)
EXPECTED_UNIVERSAL_SCANNER_SHA256 = (
    "cd16f5600747b168a3deeb7c6d74164e9463fed6889054f5a39227a42b731bb7"
)
EXPECTED_BLOCK_METADATA_SHA256 = (
    "838cbe6fc0205d293191c4f656fb9c7181074849d8cfdaaed83107da2d0ebc0e"
)
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_EFFECTIVE_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
EXPECTED_D24_WORDS = 7_114_584
EXPECTED_D5_WORDS = 5_422_562
EXPECTED_FRAGILE_STEPS = 18
EXPECTED_MENU_SIZE = 124
EXPECTED_MAXIMUM_WORD_LENGTH = 5
CACHE_MAGIC = b"NOXLN001"

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

M_BAL3 = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
# N=9*M^{-1}; projectively, canonical_primitive(Ng)=T^{-1}(g).
N_BAL3 = (
    (3, 0, 0),
    (0, -1, 3),
    (0, -3, 0),
)
MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)

# Every proper prefix of a length-at-most-five radius-two word is in this box.
SITE_RADIUS = 2 * (EXPECTED_MAXIMUM_WORD_LENGTH - 1)
SITE_SIDE = 2 * SITE_RADIUS + 1
SITE_COUNT = SITE_SIDE**3
NODE_COUNT = EXPECTED_MENU_SIZE * SITE_COUNT
NODE_BITS = (NODE_COUNT - 1).bit_length()
NODE_MASK = (1 << NODE_BITS) - 1
ARC_RECORD = struct.Struct("<QHH")
if NODE_BITS * 2 > 64:
    raise AssertionError("packed graph arc does not fit in uint64")

# If x,x',c are candidate/control prefixes, Delta=x'-M(x-c) is in this box.
SELECTOR_RADIUS = (56, 56, 72)
SELECTOR_SIDE = tuple(2 * radius + 1 for radius in SELECTOR_RADIUS)
SELECTOR_BOX_SIZE = math.prod(SELECTOR_SIDE)

# Carried bases are M(x-c), with x,c in the radius-eight candidate/control
# box. Reflection puts -M(x-c) in these nonnegative convolution boxes.
BASE_RADIUS = (48, 48, 64)
BASE_SIDE = tuple(2 * radius + 1 for radius in BASE_RADIUS)
BASE_BOX_SIZE = math.prod(BASE_SIDE)

# A coefficient counts (base, successor-site) pairs and is at most 4913, so
# exact integer polynomial multiplication cannot carry across 16-bit lanes.
CONVOLUTION_LANE_BITS = 16
CONVOLUTION_LANE_BYTES = CONVOLUTION_LANE_BITS // 8
if SITE_COUNT >= 1 << CONVOLUTION_LANE_BITS:
    raise AssertionError("convolution coefficient lane is too narrow")

COUNTDOWN_TEST_LIMIT = 256
COUNTDOWN_TRANSFORM_BUDGET = 10_000
PACKED_BENCHMARK_VERTICES = 100_000
PACKED_BENCHMARK_OUTDEGREE = 20
PACKED_BENCHMARK_SOURCE_ARCS = 500_000


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_file_snapshot(path):
    """Hash a file while proving its filesystem identity stayed unchanged."""
    path = Path(path).resolve()
    before = path.stat()
    sha256 = file_sha256(path)
    after = path.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    before_identity = tuple(getattr(before, field) for field in fields)
    after_identity = tuple(getattr(after, field) for field in fields)
    if before_identity != after_identity:
        raise RuntimeError("file changed while it was being committed", str(path))
    return {
        "path": str(path),
        "sha256": sha256,
        "bytes": after.st_size,
        "device": after.st_dev,
        "inode": after.st_ino,
        "mtime_ns": after.st_mtime_ns,
        "ctime_ns": after.st_ctime_ns,
    }


def verify_file_snapshot(expected, label):
    observed = stable_file_snapshot(expected["path"])
    if observed != expected:
        raise RuntimeError(
            f"{label} changed during certificate run", expected, observed
        )
    return observed


def stable_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def atomic_json_dump(payload, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".nonx-degenerate-site-", suffix=".json"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
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


def resource_policy(enforce):
    if enforce and sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = (
        all(value == "1" for value in environment.values())
        and priority >= 15
    )
    if enforce and not compliant:
        raise RuntimeError(
            "run requires every thread variable set to 1 and nice >= 15",
            environment,
            priority,
        )
    return {
        "thread_environment": environment,
        "process_nice": priority,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "compliant": compliant,
    }


def add(first, second):
    return tuple(first[axis] + second[axis] for axis in range(3))


def subtract(first, second):
    return tuple(first[axis] - second[axis] for axis in range(3))


def apply_matrix(vector):
    return tuple(
        sum(M_BAL3[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def apply_inverse_projective_matrix(vector):
    return tuple(
        sum(N_BAL3[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def forward_direction(direction):
    return canonical_primitive(apply_matrix(direction))


def inverse_direction(direction):
    predecessor = canonical_primitive(
        apply_inverse_projective_matrix(direction)
    )
    if forward_direction(predecessor) != canonical_primitive(direction):
        raise AssertionError("projective inverse-direction identity failed")
    return predecessor


def parallel(first, second):
    return (
        first[1] * second[2] - first[2] * second[1] == 0
        and first[2] * second[0] - first[0] * second[2] == 0
        and first[0] * second[1] - first[1] * second[0] == 0
    )


def encode_site(vector):
    if any(abs(coordinate) > SITE_RADIUS for coordinate in vector):
        raise ValueError("vector outside candidate-site box", vector)
    encoded = 0
    for coordinate in vector:
        encoded = encoded * SITE_SIDE + coordinate + SITE_RADIUS
    return encoded


def maybe_encode_site(vector):
    if any(abs(coordinate) > SITE_RADIUS for coordinate in vector):
        return None
    return encode_site(vector)


def decode_site(encoded):
    coordinates = []
    for _axis in range(3):
        encoded, digit = divmod(encoded, SITE_SIDE)
        coordinates.append(digit - SITE_RADIUS)
    if encoded:
        raise ValueError("invalid encoded candidate site")
    return tuple(reversed(coordinates))


def encode_base(vector):
    if any(
        abs(vector[axis]) > BASE_RADIUS[axis] for axis in range(3)
    ):
        raise ValueError("carried base outside proved box", vector)
    encoded = 0
    for axis in range(3):
        encoded = (
            encoded * BASE_SIDE[axis]
            + vector[axis]
            + BASE_RADIUS[axis]
        )
    return encoded


def decode_base(encoded):
    coordinates = []
    for axis in reversed(range(3)):
        encoded, digit = divmod(encoded, BASE_SIDE[axis])
        coordinates.append(digit - BASE_RADIUS[axis])
    if encoded:
        raise ValueError("invalid encoded carried base")
    return tuple(reversed(coordinates))


def flatten_selector_coordinate(coordinates):
    encoded = 0
    for axis in range(3):
        coordinate = coordinates[axis]
        if not 0 <= coordinate < SELECTOR_SIDE[axis]:
            raise ValueError("selector-grid coordinate outside box", coordinates)
        encoded = encoded * SELECTOR_SIDE[axis] + coordinate
    return encoded


def decode_selector_grid(encoded):
    coordinates = []
    for axis in reversed(range(3)):
        encoded, digit = divmod(encoded, SELECTOR_SIDE[axis])
        coordinates.append(digit - SELECTOR_RADIUS[axis])
    if encoded:
        raise ValueError("invalid selector-grid coordinate")
    return tuple(reversed(coordinates))


def encode_node(step, site):
    return step * SITE_COUNT + site


def decode_node(node):
    step, site = divmod(node, SITE_COUNT)
    if not 0 <= step < EXPECTED_MENU_SIZE:
        raise ValueError("invalid encoded graph node")
    return step, site


def pack_arc(source_node, target_node):
    if not (
        0 <= source_node < NODE_COUNT and 0 <= target_node < NODE_COUNT
    ):
        raise ValueError("graph node outside packed range")
    return (source_node << NODE_BITS) | target_node


def unpack_arc(packed):
    return packed >> NODE_BITS, packed & NODE_MASK


def canonical_primitive(vector):
    divisor = math.gcd(*(abs(coordinate) for coordinate in vector))
    if divisor == 0:
        raise ValueError("zero vector has no primitive direction")
    primitive = tuple(coordinate // divisor for coordinate in vector)
    first = next(coordinate for coordinate in primitive if coordinate)
    if first < 0:
        primitive = tuple(-coordinate for coordinate in primitive)
    return primitive


def encode_selector(direction):
    if any(
        abs(direction[axis]) > SELECTOR_RADIUS[axis]
        for axis in range(3)
    ):
        raise ValueError("primitive selector outside proved box", direction)
    encoded = 0
    for axis in range(3):
        encoded = (
            encoded * SELECTOR_SIDE[axis]
            + direction[axis]
            + SELECTOR_RADIUS[axis]
        )
    return encoded


def decode_selector(encoded):
    coordinates = []
    for axis in reversed(range(3)):
        encoded, digit = divmod(encoded, SELECTOR_SIDE[axis])
        coordinates.append(digit - SELECTOR_RADIUS[axis])
    if encoded:
        raise ValueError("invalid encoded selector direction")
    return tuple(reversed(coordinates))


def iter_mask(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def digest_integer_record(digest, values):
    for value in values:
        digest.update(int(value).to_bytes(8, "little", signed=True))


def load_and_verify_metadata(metadata_path, cache_path):
    metadata_path = Path(metadata_path)
    cache_path = Path(cache_path)
    observed_metadata_sha256 = file_sha256(metadata_path)
    if observed_metadata_sha256 != EXPECTED_METADATA_SHA256:
        raise AssertionError(
            "pinned cache-metadata JSON drift",
            observed_metadata_sha256,
            EXPECTED_METADATA_SHA256,
        )
    observed_cache_sha256 = file_sha256(cache_path)
    if observed_cache_sha256 != EXPECTED_CACHE_SHA256:
        raise AssertionError(
            "pinned compact cache drift",
            observed_cache_sha256,
            EXPECTED_CACHE_SHA256,
        )
    with metadata_path.open() as handle:
        payload = json.load(handle)
    cache = payload["compact_domain_cache"]
    expected_scalars = {
        "bytes": EXPECTED_CACHE_BYTES,
        "sha256": EXPECTED_CACHE_SHA256,
        "effective_words": EXPECTED_EFFECTIVE_WORDS,
        "word_slots": EXPECTED_WORD_SLOTS,
        "D2-4_words": EXPECTED_D24_WORDS,
        "D5_appended_words": EXPECTED_D5_WORDS,
        "fragile_steps": EXPECTED_FRAGILE_STEPS,
        "magic_ascii": CACHE_MAGIC.decode("ascii"),
        "block_metadata_sha256": EXPECTED_BLOCK_METADATA_SHA256,
    }
    observed_scalars = {key: cache[key] for key in expected_scalars}
    if observed_scalars != expected_scalars:
        raise AssertionError(
            "compact-cache metadata drift", observed_scalars, expected_scalars
        )
    if payload["checker"] != {
        "path": "design/no_new_x_line_constructor.py",
        "sha256": EXPECTED_CACHE_BUILDER_SHA256,
    }:
        raise AssertionError("cache-builder commitment drift", payload["checker"])
    if (
        payload["input_sha256"]["design/x_axis_universal_bellman.py"]
        != EXPECTED_UNIVERSAL_SCANNER_SHA256
    ):
        raise AssertionError("universal scanner commitment drift")
    if cache_path.stat().st_size != EXPECTED_CACHE_BYTES:
        raise AssertionError("cache byte size drift", cache_path.stat().st_size)

    blocks = cache["blocks"]
    if len(blocks) != EXPECTED_MENU_SIZE:
        raise AssertionError("cache block count drift", len(blocks))
    if {block["step"] for block in blocks} != set(range(EXPECTED_MENU_SIZE)):
        raise AssertionError("cache block step set drift")
    if stable_hash(blocks) != EXPECTED_BLOCK_METADATA_SHA256:
        raise AssertionError("cache block-table hash drift")
    intervals = sorted((block["start"], block["end"]) for block in blocks)
    cursor = len(CACHE_MAGIC)
    for start, end in intervals:
        if start != cursor or end <= start:
            raise AssertionError("cache block intervals are not a partition")
        cursor = end
    if cursor != EXPECTED_CACHE_BYTES:
        raise AssertionError("cache block partition does not cover file")
    if sum(block["words"] for block in blocks) != EXPECTED_EFFECTIVE_WORDS:
        raise AssertionError("block word total drift")
    if sum(block["word_slots"] for block in blocks) != EXPECTED_WORD_SLOTS:
        raise AssertionError("block slot total drift")
    if max(block["maximum_word_length"] for block in blocks) != 5:
        raise AssertionError("maximum word length drift")
    return {
        "metadata_sha256": observed_metadata_sha256,
        "cache_sha256": observed_cache_sha256,
        "cache_builder_sha256": EXPECTED_CACHE_BUILDER_SHA256,
        "universal_scanner_sha256": EXPECTED_UNIVERSAL_SCANNER_SHA256,
        "block_metadata_sha256": EXPECTED_BLOCK_METADATA_SHA256,
        "blocks": sorted(blocks, key=lambda block: block["step"]),
    }


def scan_cache(cache_path, blocks):
    zero_site = encode_site((0, 0, 0))
    expected_endpoints = tuple(apply_matrix(step) for step in MENU)
    candidate_sites = [set() for _step in MENU]
    target_masks = [dict() for _step in MENU]
    # For each observed (source, control, target), retain the intersection of
    # witness-word interiors after removing the compulsory nonzero control
    # site. Every word using a nonzero proper-prefix control contains that site,
    # so it is restored algebraically below. Empty residual intersections are
    # recorded compactly in a target-step bit mask.
    forced_transition_interiors = [dict() for _step in MENU]
    zero_forced_target_masks = [dict() for _step in MENU]
    word_count = 0
    slot_count = 0
    word_length_histogram = Counter()
    candidate_digest = hashlib.sha256()
    transition_occurrence_digest = hashlib.sha256()
    transition_occurrences = 0

    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for block in blocks:
                step = block["step"]
                encoded_block = cache[block["start"]:block["end"]]
                if hashlib.sha256(encoded_block).hexdigest() != block[
                    "encoded_block_sha256"
                ]:
                    raise AssertionError("encoded cache block hash drift", step)
                cursor = block["start"]
                observed_slots = 0
                for ordinal in range(1, block["words"] + 1):
                    if cursor >= block["end"]:
                        raise AssertionError("truncated cache block", step, ordinal)
                    length = cache[cursor]
                    cursor += 1
                    if not 1 <= length <= EXPECTED_MAXIMUM_WORD_LENGTH:
                        raise AssertionError("invalid cached word length", step, ordinal)
                    word_end = cursor + length
                    if word_end > block["end"]:
                        raise AssertionError("truncated cached word", step, ordinal)
                    word = cache[cursor:word_end]
                    cursor = word_end
                    position = (0, 0, 0)
                    positions = []
                    local_interiors = set()
                    for slot, child_step in enumerate(word):
                        if not 0 <= child_step < EXPECTED_MENU_SIZE:
                            raise AssertionError("invalid cached child step")
                        positions.append(position)
                        position = add(position, MENU[child_step])
                        if slot + 1 < length:
                            site = encode_site(position)
                            if site in local_interiors:
                                raise AssertionError(
                                    "connector word repeats an interior site",
                                    step,
                                    ordinal,
                                )
                            local_interiors.add(site)
                            candidate_sites[step].add(site)
                    interior_mask = 0
                    for site in local_interiors:
                        interior_mask |= 1 << site
                    for slot, (child_step, prefix) in enumerate(
                        zip(word, positions)
                    ):
                        control = encode_site(prefix)
                        target_bit = 1 << child_step
                        prior = target_masks[step].get(control, 0)
                        target_masks[step][control] = prior | target_bit
                        digest_integer_record(
                            transition_occurrence_digest,
                            (step, ordinal, slot, child_step, *prefix),
                        )
                        transition_occurrences += 1

                        if (
                            control != zero_site
                            and control not in local_interiors
                        ):
                            raise AssertionError(
                                "nonzero prefix control is not a proper interior",
                                step,
                                ordinal,
                                slot,
                            )

                        zero_mask = zero_forced_target_masks[step].get(
                            control, 0
                        )
                        if zero_mask & target_bit:
                            continue
                        by_target = forced_transition_interiors[step].get(
                            control
                        )
                        prior_forced = (
                            None if by_target is None
                            else by_target.get(child_step)
                        )
                        compulsory_control = (
                            0 if control == zero_site
                            else 1 << control
                        )
                        residual_interior = (
                            interior_mask & ~compulsory_control
                        )
                        forced = (
                            residual_interior if prior_forced is None
                            else prior_forced & residual_interior
                        )
                        if forced:
                            if by_target is None:
                                by_target = {}
                                forced_transition_interiors[step][control] = (
                                    by_target
                                )
                            by_target[child_step] = forced
                        else:
                            if by_target is not None:
                                by_target.pop(child_step, None)
                                if not by_target:
                                    del forced_transition_interiors[step][control]
                            zero_forced_target_masks[step][control] = (
                                zero_mask | target_bit
                            )
                    expected_endpoint = expected_endpoints[step]
                    if position != expected_endpoint:
                        raise AssertionError(
                            "connector endpoint drift",
                            step,
                            ordinal,
                            position,
                            expected_endpoint,
                        )
                    observed_slots += length
                    slot_count += length
                    word_count += 1
                    word_length_histogram[length] += 1
                if cursor != block["end"]:
                    raise AssertionError("cache block has trailing bytes", step)
                if observed_slots != block["word_slots"]:
                    raise AssertionError("cache block slot total drift", step)
        finally:
            cache.close()

    if word_count != EXPECTED_EFFECTIVE_WORDS:
        raise AssertionError("effective word count drift", word_count)
    if slot_count != EXPECTED_WORD_SLOTS:
        raise AssertionError("word-slot count drift", slot_count)
    if transition_occurrences != slot_count:
        raise AssertionError("transition occurrence count drift")

    unique_transition_count = 0
    nonempty_forced_transition_count = 0
    nonempty_residual_forced_transition_count = 0
    compulsory_control_forced_transition_count = 0
    permanently_forced_site_triples = 0
    transition_digest = hashlib.sha256()
    forced_digest = hashlib.sha256()
    for step in range(EXPECTED_MENU_SIZE):
        allowed_controls = candidate_sites[step] | {encode_site((0, 0, 0))}
        if not set(target_masks[step]) <= allowed_controls:
            raise AssertionError("prefix control is not zero or a candidate site", step)
        for site in sorted(candidate_sites[step]):
            digest_integer_record(candidate_digest, (step, *decode_site(site)))
        for control, mask in sorted(target_masks[step].items()):
            forced_by_target = forced_transition_interiors[step].get(
                control, {}
            )
            nonempty_residual_forced_transition_count += len(forced_by_target)
            forced_targets = sum(1 << target for target in forced_by_target)
            zero_targets = zero_forced_target_masks[step].get(control, 0)
            if forced_targets & zero_targets or (
                forced_targets | zero_targets
            ) != mask:
                raise AssertionError(
                    "forced-interior transition partition drift",
                    step,
                    control,
                )
            for target in iter_mask(mask):
                digest_integer_record(
                    transition_digest,
                    (step, target, *decode_site(control)),
                )
                unique_transition_count += 1
                forced = forced_by_target.get(target, 0)
                if control != zero_site:
                    forced |= 1 << control
                    compulsory_control_forced_transition_count += 1
                if forced:
                    nonempty_forced_transition_count += 1
                    for site in iter_mask(forced):
                        digest_integer_record(
                            forced_digest,
                            (step, target, *decode_site(control), *decode_site(site)),
                        )
                        permanently_forced_site_triples += 1

    return {
        "candidate_sites": candidate_sites,
        "target_masks": target_masks,
        "residual_forced_transition_interiors": forced_transition_interiors,
        "census": {
            "effective_words": word_count,
            "word_slots_and_transition_occurrences": slot_count,
            "word_length_histogram": {
                str(length): count
                for length, count in sorted(word_length_histogram.items())
            },
            "candidate_sites_total": sum(map(len, candidate_sites)),
            "candidate_sites_per_step_range": [
                min(map(len, candidate_sites)),
                max(map(len, candidate_sites)),
            ],
            "source_control_pairs": sum(map(len, target_masks)),
            "unique_full_3d_source_target_control_transitions": (
                unique_transition_count
            ),
            "candidate_site_stream_sha256": candidate_digest.hexdigest(),
            "transition_occurrence_stream_sha256": (
                transition_occurrence_digest.hexdigest()
            ),
            "unique_transition_stream_sha256": transition_digest.hexdigest(),
            "source_control_target_transitions_with_nonempty_forced_word_intersection": (
                nonempty_forced_transition_count
            ),
            "transitions_with_nonempty_residual_after_compulsory_control_removed": (
                nonempty_residual_forced_transition_count
            ),
            "transitions_with_compulsory_nonzero_control_site": (
                compulsory_control_forced_transition_count
            ),
            "permanently_forced_source_control_target_site_triples": (
                permanently_forced_site_triples
            ),
            "forced_transition_interior_stream_sha256": (
                forced_digest.hexdigest()
            ),
        },
    }


def build_site_phase_masks(candidate_sites):
    masks = [0] * SITE_COUNT
    for step, sites in enumerate(candidate_sites):
        bit = 1 << step
        for site in sites:
            masks[site] |= bit
    return masks


def build_candidate_site_bitsets(candidate_sites):
    return tuple(
        sum(1 << site for site in sites) for sites in candidate_sites
    )


def target_site_bitset(target_mask, candidate_site_bitsets, cache):
    cached = cache.get(target_mask)
    if cached is not None:
        return cached
    result = 0
    for target in iter_mask(target_mask):
        result |= candidate_site_bitsets[target]
    cache[target_mask] = result
    return result


def collect_selector_base_groups(candidate_sites, target_masks):
    """Preserve the old relation, then quotient only existential duplicates.

    The legacy semantics is a union over source, exact target-step mask,
    carried base, and a candidate site in one of those target steps.  OR-ing
    target masks for the same carried base, even across source phases, is exact
    for that final existential union.  Grouping equal successor-site bitsets is
    another exact quotient; no target site is introduced.
    """
    candidate_site_bitsets = build_candidate_site_bitsets(candidate_sites)
    target_site_cache = {}
    global_base_target_masks = {}
    distinct_source_mask_base_states = 0
    legacy_base_site_pairs = 0

    for source in range(len(candidate_sites)):
        source_sites = tuple(sorted(candidate_sites[source]))
        bases_by_target_mask = defaultdict(set)
        for control, target_mask in sorted(target_masks[source].items()):
            c = decode_site(control)
            for source_site in source_sites:
                x = decode_site(source_site)
                base = encode_base(apply_matrix(subtract(x, c)))
                bases_by_target_mask[target_mask].add(base)
        for target_mask, bases in bases_by_target_mask.items():
            successor_sites = target_site_bitset(
                target_mask, candidate_site_bitsets, target_site_cache
            )
            site_count = successor_sites.bit_count()
            distinct_source_mask_base_states += len(bases)
            legacy_base_site_pairs += len(bases) * site_count
            for base in bases:
                global_base_target_masks[base] = (
                    global_base_target_masks.get(base, 0) | target_mask
                )

    groups = defaultdict(list)
    for base, target_mask in global_base_target_masks.items():
        successor_sites = target_site_bitset(
            target_mask, candidate_site_bitsets, target_site_cache
        )
        if successor_sites:
            groups[successor_sites].append(base)
    return {
        "groups": {
            sites: tuple(sorted(bases)) for sites, bases in groups.items()
        },
        "distinct_source_mask_base_states": (
            distinct_source_mask_base_states
        ),
        "legacy_base_site_pairs": legacy_base_site_pairs,
        "globally_merged_base_states": len(global_base_target_masks),
        "exact_successor_site_equivalence_classes": len(groups),
        "target_step_mask_site_union_cache_entries": len(target_site_cache),
    }


_LANE_COLLAPSE_MASKS = None


def lane_collapse_masks():
    global _LANE_COLLAPSE_MASKS
    if _LANE_COLLAPSE_MASKS is None:
        masks = []
        for low_byte in (0xFF, 0x0F, 0x03, 0x01):
            packed = bytes((low_byte, 0)) * SELECTOR_BOX_SIZE
            masks.append(int.from_bytes(packed, "little"))
        _LANE_COLLAPSE_MASKS = tuple(masks)
    return _LANE_COLLAPSE_MASKS


def lane_polynomial(indices):
    indices = tuple(sorted(indices))
    if not indices or len(indices) != len(set(indices)):
        raise AssertionError("lane polynomial requires distinct nonempty indices")
    minimum = indices[0]
    maximum = indices[-1]
    packed = bytearray(
        CONVOLUTION_LANE_BYTES * (maximum - minimum + 1)
    )
    for index in indices:
        packed[CONVOLUTION_LANE_BYTES * (index - minimum)] = 1
    return int.from_bytes(packed, "little"), minimum, maximum


def reflected_base_convolution_index(encoded_base):
    base = decode_base(encoded_base)
    return flatten_selector_coordinate(
        tuple(BASE_RADIUS[axis] - base[axis] for axis in range(3))
    )


def collapse_product_lanes(product):
    low8, low4, low2, low1 = lane_collapse_masks()
    support = (product | (product >> 8)) & low8
    support = (support | (support >> 4)) & low4
    support = (support | (support >> 2)) & low2
    support = (support | (support >> 1)) & low1
    return support


def selector_flags_from_groups(groups):
    lane_support = 0
    multiplication_groups = 0
    group_records = sorted(
        groups.items(),
        key=lambda item: (
            -(len(item[1]) * item[0].bit_count()),
            item[0],
        ),
    )
    exact_quotient_pairs = sum(
        len(encoded_bases) * site_mask.bit_count()
        for site_mask, encoded_bases in group_records
    )
    maximum_group_bases = max(
        (len(encoded_bases) for _site_mask, encoded_bases in group_records),
        default=0,
    )
    maximum_group_sites = max(
        (site_mask.bit_count() for site_mask, _bases in group_records),
        default=0,
    )
    full_lane_support = lane_collapse_masks()[-1]

    for site_mask, encoded_bases in group_records:
        if lane_support == full_lane_support:
            break
        sites = tuple(iter_mask(site_mask))
        site_indices = tuple(
            flatten_selector_coordinate(
                tuple(
                    coordinate + SITE_RADIUS
                    for coordinate in decode_site(site)
                )
            )
            for site in sites
        )
        reflected_base_indices = tuple(
            reflected_base_convolution_index(base)
            for base in encoded_bases
        )
        base_polynomial, base_minimum, _base_maximum = lane_polynomial(
            reflected_base_indices
        )
        site_polynomial, site_minimum, _site_maximum = lane_polynomial(
            site_indices
        )
        product = base_polynomial * site_polynomial
        local_support = collapse_product_lanes(product)
        lane_support |= local_support << (
            CONVOLUTION_LANE_BITS * (base_minimum + site_minimum)
        )
        multiplication_groups += 1

    zero = encode_selector((0, 0, 0))
    lane_support &= ~(1 << (CONVOLUTION_LANE_BITS * zero))
    low1 = lane_collapse_masks()[-1]
    if lane_support & ~low1:
        raise AssertionError("convolution support escaped lane low bits")
    packed = lane_support.to_bytes(
        CONVOLUTION_LANE_BYTES * SELECTOR_BOX_SIZE, "little"
    )
    selector_flags = bytearray(SELECTOR_BOX_SIZE)
    nonzero_difference_vectors = 0
    for encoded, present in enumerate(packed[::CONVOLUTION_LANE_BYTES]):
        if not present:
            continue
        delta = decode_selector_grid(encoded)
        direction = canonical_primitive(delta)
        selector_flags[encode_selector(direction)] = 1
        nonzero_difference_vectors += 1
    return selector_flags, {
        "carry_safe_integer_multiplication_groups": multiplication_groups,
        "total_exact_successor_site_groups_before_safe_saturation_shortcut": (
            len(group_records)
        ),
        "groups_skipped_only_after_full_difference_box_saturation": (
            len(group_records) - multiplication_groups
        ),
        "distinct_pairs_after_exact_global_quotient": exact_quotient_pairs,
        "nonzero_difference_vectors_before_primitive_quotient": (
            nonzero_difference_vectors
        ),
        "maximum_bases_in_one_convolution_group": maximum_group_bases,
        "maximum_sites_in_one_convolution_group": maximum_group_sites,
        "coefficient_lane_bits": CONVOLUTION_LANE_BITS,
        "proved_maximum_coefficient": SITE_COUNT,
    }


def legacy_selector_flags(candidate_sites, target_masks):
    flags = bytearray(SELECTOR_BOX_SIZE)
    for source in range(len(candidate_sites)):
        bases_by_target_mask = defaultdict(set)
        for control, target_mask in target_masks[source].items():
            c = decode_site(control)
            for source_site in candidate_sites[source]:
                x = decode_site(source_site)
                bases_by_target_mask[target_mask].add(
                    apply_matrix(subtract(x, c))
                )
        for target_mask, bases in bases_by_target_mask.items():
            successor_sites = set()
            for target in iter_mask(target_mask):
                successor_sites.update(candidate_sites[target])
            for base in bases:
                for successor_site in successor_sites:
                    delta = subtract(decode_site(successor_site), base)
                    if delta != (0, 0, 0):
                        flags[encode_selector(canonical_primitive(delta))] = 1
    return flags


def selector_equivalence_self_test():
    points = (
        ((1, 0, 0), (0, 1, 0), (1, 1, -1)),
        ((-1, 0, 1), (0, -1, 0), (2, 0, 0)),
        ((0, 0, 1), (1, -1, 0), (-1, 1, 1)),
        ((0, 1, -1), (-2, 0, 0), (1, 0, 1)),
    )
    candidate_sites = [set(map(encode_site, phase)) for phase in points]
    zero = encode_site((0, 0, 0))
    target_masks = [
        {
            zero: 0b0011,
            encode_site(points[0][0]): 0b1100,
        },
        {
            zero: 0b0101,
            encode_site(points[1][1]): 0b1010,
        },
        {zero: 0b1111},
        {
            zero: 0b1001,
            encode_site(points[3][0]): 0b0110,
        },
    ]
    legacy = legacy_selector_flags(candidate_sites, target_masks)
    quotient = collect_selector_base_groups(candidate_sites, target_masks)
    optimized, convolution = selector_flags_from_groups(quotient["groups"])
    if optimized != legacy:
        missing = [
            index for index in range(SELECTOR_BOX_SIZE)
            if legacy[index] and not optimized[index]
        ]
        extra = [
            index for index in range(SELECTOR_BOX_SIZE)
            if optimized[index] and not legacy[index]
        ]
        raise AssertionError(
            "selector convolution is not legacy-equivalent",
            missing[:10],
            extra[:10],
        )
    return {
        "status": "passed exact reduced legacy-pair-loop equivalence",
        "source_phases": len(candidate_sites),
        "candidate_sites": sum(map(len, candidate_sites)),
        "selector_directions": sum(legacy),
        "selector_flag_sha256": hashlib.sha256(legacy).hexdigest(),
        "quotient_groups": len(quotient["groups"]),
        "convolution_groups": convolution[
            "carry_safe_integer_multiplication_groups"
        ],
    }


def graph_and_selector_census(
    candidate_sites,
    target_masks,
    residual_forced_transition_interiors,
    spool_directory,
):
    """Write sorted unique arcs to disk; retain no global Python edge set."""
    zero_site = encode_site((0, 0, 0))
    site_phase_masks = build_site_phase_masks(candidate_sites)
    candidate_site_bitsets = build_candidate_site_bitsets(candidate_sites)
    target_site_cache = {}
    global_base_target_masks = {}
    distinct_source_mask_base_states = 0
    legacy_base_site_pairs = 0

    spool_directory = Path(spool_directory)
    original_path = spool_directory / "original-arcs.bin"
    compatible_path = spool_directory / "compatible-arcs.bin"
    original_arc_digest = hashlib.sha256()
    compatible_arc_digest = hashlib.sha256()
    labeled_edge_digest = hashlib.sha256()
    compatible_labeled_edge_digest = hashlib.sha256()
    labeled_edges = 0
    compatible_labeled_edges = 0
    original_arc_count = 0
    compatible_arc_count = 0
    maximum_controls = 0
    maximum_compatible_controls = 0
    spooled_label_total = 0
    spooled_compatible_label_total = 0
    original_outgoing = bytearray(NODE_COUNT)
    compatible_outgoing = bytearray(NODE_COUNT)
    previous_original_arc = -1
    previous_compatible_arc = -1

    with original_path.open("wb") as original_handle, compatible_path.open(
        "wb"
    ) as compatible_handle:
        for source in range(EXPECTED_MENU_SIZE):
            source_site_records = tuple(
                (site, vector, apply_matrix(vector))
                for site in sorted(candidate_sites[source])
                for vector in (decode_site(site),)
            )
            bases_by_target_mask = defaultdict(set)
            # Bits 0:15 original count, 16:31 original minimum control,
            # 32:47 compatible count, 48:63 compatible minimum control.
            source_arc_metadata = {}
            for control, target_mask in sorted(target_masks[source].items()):
                c = decode_site(control)
                mapped_control = apply_matrix(c)
                forced_by_target = residual_forced_transition_interiors[
                    source
                ].get(control, {})
                for source_site, x, mapped_x in source_site_records:
                    base = subtract(mapped_x, mapped_control)
                    bases_by_target_mask[target_mask].add(encode_base(base))

                    successor_site = maybe_encode_site(base)
                    if successor_site is None:
                        continue
                    valid_targets = target_mask & site_phase_masks[successor_site]
                    for target in iter_mask(valid_targets):
                        u = encode_node(source, source_site)
                        v = encode_node(target, successor_site)
                        arc = pack_arc(u, v)
                        metadata = source_arc_metadata.get(arc)
                        if metadata is None:
                            metadata = 1 | (control << 16)
                        else:
                            if (metadata & 0xFFFF) == 0xFFFF:
                                raise AssertionError("original arc label overflow")
                            metadata += 1
                        digest_integer_record(
                            labeled_edge_digest,
                            (source, *x, target, *base, *c),
                        )
                        labeled_edges += 1

                        forced = forced_by_target.get(target, 0)
                        if control != zero_site:
                            forced |= 1 << control
                        if not forced & (1 << source_site):
                            compatible_count = (metadata >> 32) & 0xFFFF
                            if compatible_count == 0:
                                metadata |= (1 << 32) | (control << 48)
                            else:
                                if compatible_count == 0xFFFF:
                                    raise AssertionError(
                                        "compatible arc label overflow"
                                    )
                                metadata += 1 << 32
                            digest_integer_record(
                                compatible_labeled_edge_digest,
                                (source, *x, target, *base, *c),
                            )
                            compatible_labeled_edges += 1
                        source_arc_metadata[arc] = metadata

            for arc in sorted(source_arc_metadata):
                metadata = source_arc_metadata[arc]
                count = metadata & 0xFFFF
                minimum_control = (metadata >> 16) & 0xFFFF
                compatible_count = (metadata >> 32) & 0xFFFF
                compatible_minimum = (metadata >> 48) & 0xFFFF
                u, v = unpack_arc(arc)
                if arc <= previous_original_arc:
                    raise AssertionError("original packed arc stream is not sorted")
                previous_original_arc = arc
                original_handle.write(
                    ARC_RECORD.pack(arc, minimum_control, count)
                )
                digest_integer_record(original_arc_digest, (u, v))
                original_outgoing[u] = 1
                original_arc_count += 1
                spooled_label_total += count
                maximum_controls = max(maximum_controls, count)
                if compatible_count:
                    if arc <= previous_compatible_arc:
                        raise AssertionError(
                            "compatible packed arc stream is not sorted"
                        )
                    previous_compatible_arc = arc
                    compatible_handle.write(
                        ARC_RECORD.pack(
                            arc, compatible_minimum, compatible_count
                        )
                    )
                    digest_integer_record(compatible_arc_digest, (u, v))
                    compatible_outgoing[u] = 1
                    compatible_arc_count += 1
                    spooled_compatible_label_total += compatible_count
                    maximum_compatible_controls = max(
                        maximum_compatible_controls, compatible_count
                    )

            for target_mask, bases in bases_by_target_mask.items():
                successor_sites = target_site_bitset(
                    target_mask, candidate_site_bitsets, target_site_cache
                )
                distinct_source_mask_base_states += len(bases)
                legacy_base_site_pairs += (
                    len(bases) * successor_sites.bit_count()
                )
                for encoded_base in bases:
                    global_base_target_masks[encoded_base] = (
                        global_base_target_masks.get(encoded_base, 0)
                        | target_mask
                    )
            del source_arc_metadata
            del bases_by_target_mask
            del source_site_records

    expected_original_bytes = original_arc_count * ARC_RECORD.size
    expected_compatible_bytes = compatible_arc_count * ARC_RECORD.size
    if original_path.stat().st_size != expected_original_bytes:
        raise AssertionError("original arc spool byte count drift")
    if compatible_path.stat().st_size != expected_compatible_bytes:
        raise AssertionError("compatible arc spool byte count drift")
    original_spool_sha256 = file_sha256(original_path)
    compatible_spool_sha256 = file_sha256(compatible_path)
    if compatible_arc_count > original_arc_count:
        raise AssertionError("compatible graph is not a packed subgraph")
    if spooled_label_total != labeled_edges:
        raise AssertionError("original packed label total drift")
    if spooled_compatible_label_total != compatible_labeled_edges:
        raise AssertionError("compatible packed label total drift")
    original_outgoing_count = sum(original_outgoing)
    compatible_outgoing_count = sum(compatible_outgoing)
    del original_outgoing
    del compatible_outgoing

    # Every graph label has now been committed to the sorted spools and every
    # selector base to the merged base dictionary.  Drop the large scan maps
    # before grouping bases or invoking integer convolution.
    target_masks.clear()
    residual_forced_transition_interiors.clear()
    gc.collect()

    selector_groups = defaultdict(lambda: array.array("I"))
    for encoded_base, target_mask in global_base_target_masks.items():
        successor_sites = target_site_bitset(
            target_mask, candidate_site_bitsets, target_site_cache
        )
        if successor_sites:
            selector_groups[successor_sites].append(encoded_base)
    globally_merged_base_states = len(global_base_target_masks)
    del global_base_target_masks
    selector_equivalence_classes = len(selector_groups)
    target_site_cache_entries = len(target_site_cache)
    del target_site_cache
    del candidate_site_bitsets
    del site_phase_masks
    gc.collect()
    selector_flags, convolution_census = selector_flags_from_groups(
        selector_groups
    )

    direction_digest = hashlib.sha256()
    selector_count = 0
    non_x_selector_count = 0
    x_direction_present = False
    maximum_direction_coordinate = 0
    for encoded, present in enumerate(selector_flags):
        if not present:
            continue
        direction = decode_selector(encoded)
        if canonical_primitive(direction) != direction:
            raise AssertionError("selector flag is not canonical primitive")
        digest_integer_record(direction_digest, direction)
        selector_count += 1
        maximum_direction_coordinate = max(
            maximum_direction_coordinate, *(abs(value) for value in direction)
        )
        if direction[1:] == (0, 0):
            x_direction_present = True
        else:
            non_x_selector_count += 1

    del selector_flags
    del selector_groups
    gc.collect()

    all_nodes = array.array(
        "I",
        (
            encode_node(step, site)
            for step, sites in enumerate(candidate_sites)
            for site in sorted(sites)
        ),
    )
    return {
        "nodes": all_nodes,
        "original_spool": {
            "path": original_path,
            "records": original_arc_count,
        },
        "compatible_spool": {
            "path": compatible_path,
            "records": compatible_arc_count,
        },
        "census": {
            "candidate_vertices": len(all_nodes),
            "vertices_with_outgoing_degenerate_arcs": original_outgoing_count,
            "unique_unlabelled_degenerate_arcs": original_arc_count,
            "full_3d_control_labelled_degenerate_edges": labeled_edges,
            "maximum_controls_for_one_unlabelled_arc": maximum_controls,
            "unlabelled_arc_stream_sha256": original_arc_digest.hexdigest(),
            "labelled_edge_stream_sha256": labeled_edge_digest.hexdigest(),
            "x_avoiding_compatible_vertices_with_outgoing_arcs": (
                compatible_outgoing_count
            ),
            "x_avoiding_compatible_unique_unlabelled_degenerate_arcs": (
                compatible_arc_count
            ),
            "x_avoiding_compatible_control_labelled_degenerate_edges": (
                compatible_labeled_edges
            ),
            "maximum_compatible_controls_for_one_unlabelled_arc": (
                maximum_compatible_controls
            ),
            "x_avoiding_compatible_unlabelled_arc_stream_sha256": (
                compatible_arc_digest.hexdigest()
            ),
            "x_avoiding_compatible_labelled_edge_stream_sha256": (
                compatible_labeled_edge_digest.hexdigest()
            ),
            "packed_arc_spool_record_bytes": ARC_RECORD.size,
            "original_packed_arc_spool_sha256": original_spool_sha256,
            "compatible_packed_arc_spool_sha256": compatible_spool_sha256,
            "peak_python_arc_deduplication_scope": "one source step",
            "packed_graph_memory_schedule": (
                "write original and compatible sorted spools together; release "
                "scan poison maps before convolution; then mmap and analyze "
                "original and compatible graphs one at a time with one uint32 "
                "reverse-source array per active graph"
            ),
            "selector_census_method": (
                "preserve every source/exact-target-mask carried-base relation; "
                "OR target masks only for identical carried bases in the final "
                "existential union; group identical exact successor-site sets; "
                "then take carry-safe 16-bit-lane integer difference convolutions"
            ),
            "distinct_source_mask_carried_base_states": (
                distinct_source_mask_base_states
            ),
            "distinct_carried_base_target_site_pairs_tested": (
                legacy_base_site_pairs
            ),
            "globally_merged_carried_base_states": globally_merged_base_states,
            "exact_successor_site_equivalence_classes": (
                selector_equivalence_classes
            ),
            "target_step_mask_site_union_cache_entries": (
                target_site_cache_entries
            ),
            **convolution_census,
            "selector_primitive_directions": selector_count,
            "non_x_selector_primitive_directions": non_x_selector_count,
            "x_selector_direction_present": x_direction_present,
            "maximum_selector_primitive_coordinate": maximum_direction_coordinate,
            "selector_direction_stream_sha256": direction_digest.hexdigest(),
            "proved_selector_coordinate_box": [
                [-SELECTOR_RADIUS[0], SELECTOR_RADIUS[0]],
                [-SELECTOR_RADIUS[1], SELECTOR_RADIUS[1]],
                [-SELECTOR_RADIUS[2], SELECTOR_RADIUS[2]],
            ],
            "ambient_nonzero_vector_bound_before_primitive_deduplication": (
                SELECTOR_BOX_SIZE - 1
            ),
        },
    }


class PackedNeighborRange:
    __slots__ = ("graph", "node", "reverse")

    def __init__(self, graph, node, reverse):
        self.graph = graph
        self.node = node
        self.reverse = reverse

    def __len__(self):
        offsets = (
            self.graph.reverse_offsets
            if self.reverse else self.graph.forward_offsets
        )
        return offsets[self.node + 1] - offsets[self.node]

    def __iter__(self):
        if self.reverse:
            start = self.graph.reverse_offsets[self.node]
            end = self.graph.reverse_offsets[self.node + 1]
            for index in range(start, end):
                yield self.graph.reverse_sources[index]
            return
        start = self.graph.forward_offsets[self.node]
        end = self.graph.forward_offsets[self.node + 1]
        for index in range(start, end):
            packed, _minimum, _count = ARC_RECORD.unpack_from(
                self.graph.mapping, index * ARC_RECORD.size
            )
            yield packed & NODE_MASK

    def __contains__(self, target):
        if self.reverse:
            values = self.graph.reverse_sources
            low = self.graph.reverse_offsets[self.node]
            high = self.graph.reverse_offsets[self.node + 1]
            while low < high:
                middle = (low + high) // 2
                value = values[middle]
                if value < target:
                    low = middle + 1
                else:
                    high = middle
            return low < self.graph.reverse_offsets[self.node + 1] and (
                values[low] == target
            )
        return self.graph.find_arc_record(self.node, target) is not None


class PackedAdjacencyView:
    __slots__ = ("graph", "reverse")

    def __init__(self, graph, reverse):
        self.graph = graph
        self.reverse = reverse

    def __getitem__(self, node):
        return PackedNeighborRange(self.graph, node, self.reverse)

    def items(self):
        for node in self.graph.nodes:
            yield node, self[node]


class PackedArcMetadataView:
    __slots__ = ("graph", "field")

    def __init__(self, graph, field):
        self.graph = graph
        self.field = field

    def __getitem__(self, arc):
        record = self.graph.find_arc_record(*arc)
        if record is None:
            raise KeyError(arc)
        return record[self.field]


class PackedArcGraph:
    """Forward mmap plus one compact in-memory reverse CSR."""

    def __init__(self, spool, nodes):
        self.path = Path(spool["path"])
        self.record_count = spool["records"]
        self.nodes = nodes
        self.handle = self.path.open("rb")
        expected_bytes = self.record_count * ARC_RECORD.size
        if self.path.stat().st_size != expected_bytes:
            raise AssertionError("packed graph spool byte count drift")
        self.mapping = (
            mmap.mmap(self.handle.fileno(), 0, access=mmap.ACCESS_READ)
            if expected_bytes else None
        )
        active = bytearray(NODE_COUNT)
        for node in nodes:
            active[node] = 1
        outgoing_counts = array.array("Q", [0]) * NODE_COUNT
        incoming_counts = array.array("Q", [0]) * NODE_COUNT
        previous = -1
        for index in range(self.record_count):
            packed, minimum, count = ARC_RECORD.unpack_from(
                self.mapping, index * ARC_RECORD.size
            )
            if packed <= previous:
                raise AssertionError("packed graph records are not strictly sorted")
            previous = packed
            u, v = unpack_arc(packed)
            if not active[u] or not active[v]:
                raise AssertionError("packed arc endpoint is not a candidate node")
            if not 0 <= minimum < SITE_COUNT or count == 0:
                raise AssertionError("invalid packed arc metadata")
            outgoing_counts[u] += 1
            incoming_counts[v] += 1

        self.forward_offsets = array.array("Q", [0]) * (NODE_COUNT + 1)
        self.reverse_offsets = array.array("Q", [0]) * (NODE_COUNT + 1)
        forward_total = 0
        reverse_total = 0
        for node in range(NODE_COUNT):
            self.forward_offsets[node] = forward_total
            self.reverse_offsets[node] = reverse_total
            forward_total += outgoing_counts[node]
            reverse_total += incoming_counts[node]
        self.forward_offsets[NODE_COUNT] = forward_total
        self.reverse_offsets[NODE_COUNT] = reverse_total
        if forward_total != self.record_count or reverse_total != self.record_count:
            raise AssertionError("packed CSR edge total drift")
        del outgoing_counts
        del active

        self.reverse_sources = array.array("I", [0]) * self.record_count
        cursors = array.array("Q", self.reverse_offsets[:-1])
        for index in range(self.record_count):
            packed, _minimum, _count = ARC_RECORD.unpack_from(
                self.mapping, index * ARC_RECORD.size
            )
            u, v = unpack_arc(packed)
            destination = cursors[v]
            self.reverse_sources[destination] = u
            cursors[v] += 1
        del cursors
        del incoming_counts

        self.adjacency = PackedAdjacencyView(self, reverse=False)
        self.reverse = PackedAdjacencyView(self, reverse=True)
        self.arc_min_control = PackedArcMetadataView(self, field=1)
        self.arc_label_counts = PackedArcMetadataView(self, field=2)

    def find_arc_record(self, source, target):
        packed_target = pack_arc(source, target)
        low = self.forward_offsets[source]
        high = self.forward_offsets[source + 1]
        while low < high:
            middle = (low + high) // 2
            packed, minimum, count = ARC_RECORD.unpack_from(
                self.mapping, middle * ARC_RECORD.size
            )
            if packed < packed_target:
                low = middle + 1
            else:
                high = middle
        if low >= self.forward_offsets[source + 1]:
            return None
        record = ARC_RECORD.unpack_from(self.mapping, low * ARC_RECORD.size)
        return record if record[0] == packed_target else None

    def as_graph_mapping(self):
        return {
            "nodes": self.nodes,
            "adjacency": self.adjacency,
            "reverse": self.reverse,
            "arc_min_control": self.arc_min_control,
            "arc_label_counts": self.arc_label_counts,
        }

    def close(self):
        self.adjacency = None
        self.reverse = None
        self.arc_min_control = None
        self.arc_label_counts = None
        self.reverse_sources = None
        self.forward_offsets = None
        self.reverse_offsets = None
        if self.mapping is not None:
            self.mapping.close()
            self.mapping = None
        self.handle.close()


def packed_graph_equivalence_self_test():
    records = (
        (pack_arc(0, 1), 3, 2),
        (pack_arc(1, 1), 4, 1),
        (pack_arc(1, 2), 5, 3),
        (pack_arc(2, 0), 6, 1),
    )
    with tempfile.TemporaryDirectory(prefix="packed-graph-self-test-") as folder:
        path = Path(folder) / "arcs.bin"
        with path.open("wb") as handle:
            for record in records:
                handle.write(ARC_RECORD.pack(*record))
        nodes = array.array("I", (0, 1, 2))
        graph = PackedArcGraph(
            {"path": path, "records": len(records)}, nodes
        )
        expected_forward = {0: (1,), 1: (1, 2), 2: (0,)}
        expected_reverse = {0: (2,), 1: (0, 1), 2: (1,)}
        observed_forward = {
            node: tuple(graph.adjacency[node]) for node in nodes
        }
        observed_reverse = {
            node: tuple(graph.reverse[node]) for node in nodes
        }
        if observed_forward != expected_forward:
            raise AssertionError("packed forward adjacency self-test failed")
        if observed_reverse != expected_reverse:
            raise AssertionError("packed reverse adjacency self-test failed")
        for packed, minimum, count in records:
            arc = unpack_arc(packed)
            if graph.arc_min_control[arc] != minimum:
                raise AssertionError("packed minimum-control self-test failed")
            if graph.arc_label_counts[arc] != count:
                raise AssertionError("packed label-count self-test failed")
        structure = graph_structure(graph.as_graph_mapping())
        if structure["result"]["strongly_connected_components"] != 1:
            raise AssertionError("packed SCC self-test failed")
        graph.close()
    return {
        "status": "passed fixed-record forward/reverse/metadata/SCC test",
        "vertices": len(nodes),
        "arcs": len(records),
        "record_bytes": ARC_RECORD.size,
    }


def strongly_connected_components(nodes, adjacency, reverse):
    visited = bytearray(NODE_COUNT)
    visited_count = 0
    finish = array.array("I")
    for start in nodes:
        if visited[start]:
            continue
        visited[start] = 1
        visited_count += 1
        stack = [(start, iter(adjacency[start]))]
        while stack:
            node, successors = stack[-1]
            try:
                successor = next(successors)
            except StopIteration:
                finish.append(node)
                stack.pop()
                continue
            if not visited[successor]:
                visited[successor] = 1
                visited_count += 1
                stack.append((successor, iter(adjacency[successor])))
    if visited_count != len(nodes) or len(finish) != len(nodes):
        raise AssertionError("forward SCC traversal lost a vertex")

    component_of = array.array("i", [-1]) * NODE_COUNT
    assigned = 0
    components = []
    for start in reversed(finish):
        if component_of[start] != -1:
            continue
        component_index = len(components)
        component = []
        component_of[start] = component_index
        assigned += 1
        stack = [start]
        while stack:
            node = stack.pop()
            component.append(node)
            for predecessor in reverse[node]:
                if component_of[predecessor] == -1:
                    component_of[predecessor] = component_index
                    assigned += 1
                    stack.append(predecessor)
        component.sort()
        components.append(tuple(component))
    if assigned != len(nodes):
        raise AssertionError("reverse SCC traversal lost a vertex")
    return component_of, components


def dag_longest_path(nodes, adjacency):
    indegree = {node: 0 for node in nodes}
    for node in nodes:
        for successor in adjacency[node]:
            indegree[successor] += 1
    queue = [node for node in nodes if indegree[node] == 0]
    heapq.heapify(queue)
    distance = {node: 0 for node in nodes}
    processed = 0
    maximum = 0
    while queue:
        node = heapq.heappop(queue)
        processed += 1
        maximum = max(maximum, distance[node])
        for successor in adjacency[node]:
            distance[successor] = max(distance[successor], distance[node] + 1)
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(queue, successor)
    if processed != len(nodes):
        return None
    return maximum


def condensation_longest_path(components, component_of, adjacency):
    count = len(components)
    indegree = array.array("I", [0]) * count
    offsets = array.array("Q", [0]) * (count + 1)
    targets = array.array("I")
    digest = hashlib.sha256()
    edge_count = 0
    for source_component, component in enumerate(components):
        offsets[source_component] = len(targets)
        local_targets = set()
        for node in component:
            for successor in adjacency[node]:
                target_component = component_of[successor]
                if source_component != target_component:
                    local_targets.add(target_component)
        for target_component in sorted(local_targets):
            targets.append(target_component)
            indegree[target_component] += 1
            digest_integer_record(
                digest, (source_component, target_component)
            )
            edge_count += 1
    offsets[count] = len(targets)

    queue = [index for index, degree in enumerate(indegree) if degree == 0]
    heapq.heapify(queue)
    distance = array.array("I", [0]) * count
    processed = 0
    maximum = 0
    while queue:
        component = heapq.heappop(queue)
        processed += 1
        maximum = max(maximum, distance[component])
        for edge_index in range(offsets[component], offsets[component + 1]):
            successor = targets[edge_index]
            distance[successor] = max(
                distance[successor], distance[component] + 1
            )
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(queue, successor)
    if processed != count:
        raise AssertionError("SCC condensation is cyclic")
    return maximum, edge_count, digest.hexdigest()


def canonical_cycle(components, component_of, adjacency):
    cyclic_components = []
    for component_index, component in enumerate(components):
        if len(component) > 1 or (
            len(component) == 1 and component[0] in adjacency[component[0]]
        ):
            cyclic_components.append((component_index, component))
    if not cyclic_components:
        return None, []
    component_index, component = min(
        cyclic_components, key=lambda value: (min(value[1]), value[1])
    )
    for source in component:
        for target in adjacency[source]:
            if component_of[target] != component_index:
                continue
            if source == target:
                return (source, source), [
                    item[1] for item in cyclic_components
                ]
            predecessor = {target: None}
            queue = deque([target])
            while queue and source not in predecessor:
                node = queue.popleft()
                for successor in adjacency[node]:
                    if (
                        component_of[successor] == component_index
                        and successor not in predecessor
                    ):
                        predecessor[successor] = node
                        queue.append(successor)
            if source not in predecessor:
                raise AssertionError("SCC edge has no return path")
            path = [source]
            while path[-1] != target:
                path.append(predecessor[path[-1]])
            path.reverse()
            return tuple([source, *path]), [
                item[1] for item in cyclic_components
            ]
    raise AssertionError("cyclic SCC supplied no internal edge")


def graph_structure(graph):
    nodes = graph["nodes"]
    adjacency = graph["adjacency"]
    reverse = graph["reverse"]
    component_of, components = strongly_connected_components(
        nodes, adjacency, reverse
    )
    cycle, cyclic_components = canonical_cycle(
        components, component_of, adjacency
    )
    component_histogram = Counter(map(len, components))
    condensation_length, condensation_edges, condensation_hash = (
        condensation_longest_path(components, component_of, adjacency)
    )
    longest_path = condensation_length if cycle is None else None
    if cyclic_components:
        cyclic_vertices = sum(map(len, cyclic_components))
        largest_cyclic = max(map(len, cyclic_components))
    else:
        cyclic_vertices = 0
        largest_cyclic = 0
    return {
        "cycle": cycle,
        "result": {
            "strongly_connected_components": len(components),
            "component_size_histogram": {
                str(size): count
                for size, count in sorted(component_histogram.items())
            },
            "cyclic_components": len(cyclic_components),
            "vertices_in_cyclic_components": cyclic_vertices,
            "largest_cyclic_component": largest_cyclic,
            "degenerate_site_graph_is_acyclic": cycle is None,
            "longest_degenerate_path_edges_if_acyclic": longest_path,
            "condensation_edges": condensation_edges,
            "condensation_longest_path_edges": condensation_length,
            "condensation_edge_stream_sha256": condensation_hash,
        },
    }


def find_transition_witnesses(cache_path, blocks, required):
    if not required:
        return {}
    required_by_source = defaultdict(set)
    for transition in required:
        required_by_source[transition[0]].add(transition)
    witnesses = {}
    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for block in blocks:
                source = block["step"]
                remaining = required_by_source.get(source)
                if not remaining:
                    continue
                cursor = block["start"]
                for ordinal in range(1, block["words"] + 1):
                    length = cache[cursor]
                    cursor += 1
                    word = tuple(cache[cursor:cursor + length])
                    cursor += length
                    position = (0, 0, 0)
                    for slot, target in enumerate(word):
                        transition = (source, target, encode_site(position))
                        if transition in remaining and transition not in witnesses:
                            witnesses[transition] = {
                                "source_step": source,
                                "target_step": target,
                                "prefix_control": list(position),
                                "word_ordinal_1_based": ordinal,
                                "slot_0_based": slot,
                                "word": list(word),
                            }
                        position = add(position, MENU[target])
                    if all(item in witnesses for item in remaining):
                        break
        finally:
            cache.close()
    if set(witnesses) != set(required):
        raise AssertionError(
            "failed to recover every cycle transition witness",
            sorted(set(required) - set(witnesses)),
        )
    return witnesses


def find_compatible_transition_witnesses(cache_path, blocks, required):
    """Recover a word/slot witness whose full interior avoids carried x."""
    if not required:
        return {}
    required_by_source_transition = defaultdict(set)
    required_by_source = defaultdict(set)
    for item in required:
        source, target, control, _source_site = item
        transition = (source, target, control)
        required_by_source_transition[transition].add(item)
        required_by_source[source].add(item)
    witnesses = {}
    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for block in blocks:
                source = block["step"]
                source_required = required_by_source.get(source)
                if not source_required:
                    continue
                cursor = block["start"]
                for ordinal in range(1, block["words"] + 1):
                    length = cache[cursor]
                    cursor += 1
                    word = tuple(cache[cursor:cursor + length])
                    cursor += length
                    positions = []
                    position = (0, 0, 0)
                    interiors = set()
                    for slot, target in enumerate(word):
                        positions.append(position)
                        position = add(position, MENU[target])
                        if slot + 1 < length:
                            interiors.add(encode_site(position))
                    for slot, (target, prefix) in enumerate(
                        zip(word, positions)
                    ):
                        control = encode_site(prefix)
                        transition = (source, target, control)
                        for item in required_by_source_transition.get(
                            transition, ()
                        ):
                            source_site = item[3]
                            if item in witnesses or source_site in interiors:
                                continue
                            witnesses[item] = {
                                "source_step": source,
                                "target_step": target,
                                "prefix_control": list(prefix),
                                "word_ordinal_1_based": ordinal,
                                "slot_0_based": slot,
                                "word": list(word),
                                "interior_sites": [
                                    list(decode_site(site))
                                    for site in sorted(interiors)
                                ],
                                "carried_site": list(
                                    decode_site(source_site)
                                ),
                                "interior_avoids_carried_site": True,
                            }
                    if all(item in witnesses for item in source_required):
                        break
        finally:
            cache.close()
    if set(witnesses) != set(required):
        raise AssertionError(
            "failed to recover every x-avoiding cycle witness",
            sorted(set(required) - set(witnesses)),
        )
    return witnesses


def cycle_certificate(
    cycle,
    graph,
    cache_path,
    blocks,
    candidate_sites,
    require_source_site_avoidance=False,
):
    if cycle is None:
        return None
    arc_min_control = graph["arc_min_control"]
    transitions = []
    for source_node, target_node in zip(cycle, cycle[1:]):
        source_step, source_site = decode_node(source_node)
        target_step, target_site = decode_node(target_node)
        control = arc_min_control[(source_node, target_node)]
        transition = (source_step, target_step, control)
        if require_source_site_avoidance:
            transition += (source_site,)
        transitions.append(transition)
    if require_source_site_avoidance:
        witnesses = find_compatible_transition_witnesses(
            cache_path, blocks, set(transitions)
        )
    else:
        witnesses = find_transition_witnesses(
            cache_path, blocks, set(transitions)
        )

    records = []
    for index, (source_node, target_node) in enumerate(zip(cycle, cycle[1:])):
        source_step, source_site = decode_node(source_node)
        target_step, target_site = decode_node(target_node)
        control = arc_min_control[(source_node, target_node)]
        x = decode_site(source_site)
        x_prime = decode_site(target_site)
        c = decode_site(control)
        delta = subtract(x_prime, apply_matrix(subtract(x, c)))
        if delta != (0, 0, 0):
            raise AssertionError("cycle edge is not direction-blind")
        transition = (source_step, target_step, control)
        if require_source_site_avoidance:
            transition += (source_site,)
        records.append({
            "cycle_edge_index": index,
            "source": {"step": source_step, "candidate_site": list(x)},
            "target": {"step": target_step, "candidate_site": list(x_prime)},
            "control_label_multiplicity_for_this_unlabelled_arc": (
                graph["arc_label_counts"][(source_node, target_node)]
            ),
            "selected_minimum_control": list(c),
            "verified_delta": list(delta),
            "exact_cache_occurrence_witness": witnesses[transition],
        })

    first_step, first_site_encoded = decode_node(cycle[0])
    first_site = decode_site(first_site_encoded)
    non_x_reveal_sites = []
    x_reveal_sites = []
    for other_encoded in sorted(candidate_sites[first_step]):
        if other_encoded == first_site_encoded:
            continue
        other = decode_site(other_encoded)
        direction = canonical_primitive(subtract(other, first_site))
        record = {
            "site": list(other),
            "primitive_direction_from_carried_site": list(direction),
        }
        if direction[1:] == (0, 0):
            x_reveal_sites.append(record)
        else:
            non_x_reveal_sites.append(record)

    return {
        "cycle_length_edges": len(cycle) - 1,
        "cycle_node_sequence": [
            {
                "step": decode_node(node)[0],
                "candidate_site": list(decode_site(decode_node(node)[1])),
            }
            for node in cycle
        ],
        "edge_records": records,
        "word_slot_witnesses_are_exact_cache_occurrences": True,
        "every_selected_cycle_word_avoids_its_carried_site": (
            require_source_site_avoidance
        ),
        "recurrent_start_phase": {
            "step": first_step,
            "carried_site": list(first_site),
            "non_x_delayed_reveal_site_count": len(non_x_reveal_sites),
            "x_parallel_reveal_site_count": len(x_reveal_sites),
            "first_non_x_delayed_reveal_witness": (
                non_x_reveal_sites[0] if non_x_reveal_sites else None
            ),
        },
        "implication": (
            (
                "Each selected exact word avoids the carried site, so the "
                "permanent self-poison objection is removed on this cycle. "
                "Other interior alignments along a countdown are tested "
                "separately; no infinite compatible repetition or globally "
                "legal ordered policy is asserted."
            )
            if require_source_site_avoidance
            else (
                "Repeating these geometric controls carries every line through "
                "the listed sites in the arbitrary-switching candidate graph. "
                "A word realizing a selected slot may contain the carried site, "
                "and global ordered-path realizability is not asserted."
            )
        ),
    }


def cycle_countdown_compatibility(certificate):
    if certificate is None:
        return {
            "status": "not tested because the x-avoiding graph is acyclic"
        }
    reveal = certificate["recurrent_start_phase"][
        "first_non_x_delayed_reveal_witness"
    ]
    if reveal is None:
        return {
            "status": "not tested because no non-x reveal site exists"
        }
    length = certificate["cycle_length_edges"]
    if length <= 0:
        raise AssertionError("cycle has no edges")
    limit = min(
        COUNTDOWN_TEST_LIMIT,
        max(1, COUNTDOWN_TRANSFORM_BUDGET // length),
    )
    reveal_direction = tuple(reveal["primitive_direction_from_carried_site"])
    start_direction = reveal_direction
    first_poison = None
    tested = 0
    for residual in range(1, limit + 1):
        previous_start = start_direction
        for _edge in range(length):
            start_direction = inverse_direction(start_direction)
        phase_direction = start_direction
        residual_poison = None
        for edge in certificate["edge_records"]:
            source_site = tuple(edge["source"]["candidate_site"])
            witness = edge["exact_cache_occurrence_witness"]
            if not witness.get("interior_avoids_carried_site"):
                raise AssertionError("countdown word does not avoid carried site")
            for interior in witness["interior_sites"]:
                displacement = subtract(tuple(interior), source_site)
                if displacement == (0, 0, 0):
                    raise AssertionError("self-poison survived x-avoidance filter")
                if parallel(displacement, phase_direction):
                    residual_poison = {
                        "residual_cycles": residual,
                        "cycle_edge_index": edge["cycle_edge_index"],
                        "carried_site": list(source_site),
                        "poisoned_interior_site": interior,
                        "line_direction": list(phase_direction),
                        "word_ordinal_1_based": witness[
                            "word_ordinal_1_based"
                        ],
                        "word": witness["word"],
                    }
                    break
            if residual_poison is not None:
                break
            phase_direction = forward_direction(phase_direction)
        # Every edge advances the projective direction once.  Recompute this
        # invariant independently of whether the poison scan stopped early.
        check_direction = start_direction
        for _edge in range(length):
            check_direction = forward_direction(check_direction)
        if check_direction != previous_start:
            raise AssertionError("countdown cycle direction transport drift")
        tested = residual
        if residual_poison is not None:
            first_poison = residual_poison
            break

    if first_poison is None:
        status = (
            "no alignment found through the finite cap; this is not an "
            "infinite compatibility proof"
        )
        clean_prefix = tested
    else:
        status = (
            "the first poisoned residual blocks this fixed-label countdown "
            "at that length and every longer length that traverses it"
        )
        clean_prefix = first_poison["residual_cycles"] - 1
    return {
        "status": status,
        "tested_residual_cycles": tested,
        "configured_limit": COUNTDOWN_TEST_LIMIT,
        "transform_budget": COUNTDOWN_TRANSFORM_BUDGET,
        "cycle_length_edges": length,
        "clean_countdown_prefix_cycles": clean_prefix,
        "first_poison": first_poison,
        "scope": (
            "the canonical x-avoiding cycle with its fixed selected witness "
            "word on each edge; adaptive label choices are not searched"
        ),
    }


def run(metadata_path, cache_path):
    started = time.monotonic()
    metadata_path = Path(metadata_path).resolve()
    cache_path = Path(cache_path).resolve()
    start_snapshots = {
        "checker": stable_file_snapshot(Path(__file__).resolve()),
        "metadata": stable_file_snapshot(metadata_path),
        "cache": stable_file_snapshot(cache_path),
    }
    inputs = load_and_verify_metadata(metadata_path, cache_path)
    self_test = selector_equivalence_self_test()
    packed_graph_self_test = packed_graph_equivalence_self_test()
    scan = scan_cache(cache_path, inputs["blocks"])
    candidate_sites = scan["candidate_sites"]
    domain_scan_census = scan["census"]
    with tempfile.TemporaryDirectory(
        prefix="nonx-degenerate-packed-"
    ) as spool_directory:
        graph_build = graph_and_selector_census(
            candidate_sites,
            scan["target_masks"],
            scan["residual_forced_transition_interiors"],
            spool_directory,
        )
        del scan
        gc.collect()

        original_graph = PackedArcGraph(
            graph_build["original_spool"], graph_build["nodes"]
        )
        original_mapping = original_graph.as_graph_mapping()
        structure = graph_structure(original_mapping)
        cycle = cycle_certificate(
            structure["cycle"],
            original_mapping,
            cache_path,
            inputs["blocks"],
            candidate_sites,
        )
        original_graph.close()
        del original_mapping
        del original_graph
        gc.collect()

        compatible_graph = PackedArcGraph(
            graph_build["compatible_spool"], graph_build["nodes"]
        )
        compatible_mapping = compatible_graph.as_graph_mapping()
        compatible_structure = graph_structure(compatible_mapping)
        compatible_cycle = cycle_certificate(
            compatible_structure["cycle"],
            compatible_mapping,
            cache_path,
            inputs["blocks"],
            candidate_sites,
            require_source_site_avoidance=True,
        )
        compatible_graph.close()
        del compatible_mapping
        del compatible_graph
        gc.collect()
    countdown = cycle_countdown_compatibility(compatible_cycle)

    result = structure["result"]
    selector_count = graph_build["census"][
        "non_x_selector_primitive_directions"
    ]
    longest = result["longest_degenerate_path_edges_if_acyclic"]
    if longest is None:
        continuous_effect_bound = None
    else:
        continuous_effect_bound = selector_count + (selector_count + 1) * longest

    end_snapshots = {
        label: verify_file_snapshot(snapshot, label)
        for label, snapshot in start_snapshots.items()
    }

    return {
        "schema_version": 2,
        "date": "2026-07-18",
        "status": "exact finite synchronized candidate-site graph certificate",
        "checker": {
            "path": "design/nonx_degenerate_site_graph.py",
            "sha256": start_snapshots["checker"]["sha256"],
        },
        "execution_file_commitments": {
            "captured_before_scan": start_snapshots,
            "captured_after_all_proof_work": end_snapshots,
            "start_and_end_are_byte_and_identity_identical": True,
        },
        "selector_optimization_self_test": self_test,
        "packed_graph_self_test": packed_graph_self_test,
        "pinned_inputs": {
            key: value for key, value in inputs.items() if key != "blocks"
        },
        "domain_scan": domain_scan_census,
        "degenerate_graph_and_selector_census": graph_build["census"],
        "graph_structure": result,
        "canonical_cycle_witness": cycle,
        "x_avoiding_compatibility_graph_structure": compatible_structure[
            "result"
        ],
        "canonical_x_avoiding_cycle_witness": compatible_cycle,
        "canonical_x_avoiding_cycle_finite_countdown_test": countdown,
        "conditional_continuous_non_x_effect_bound": {
            "formula_if_acyclic": "|V_nonx| + (|V_nonx|+1)*L",
            "selector_direction_count_V_nonx": selector_count,
            "longest_degenerate_path_L": longest,
            "bound_in_edges": continuous_effect_bound,
            "scope": (
                "one already-existing non-x line which hits at least one "
                "candidate site at every synchronized parent-to-child stitch"
            ),
        },
        "proved_by_this_finite_scan": [
            "Every word and ordered slot in the pinned compact effective-domain cache is parsed and endpoint-checked without loading a domain pickle.",
            "Every full-3D candidate site and source-target-prefix transition is retained before finite deduplication.",
            "Original and x-avoiding labelled arcs are deduplicated exactly within their unique source phase, committed as strictly sorted fixed-width records, and independently reconstructed as forward and reverse packed graphs.",
            "The direction-blind graph contains exactly the transitions x'=M(x-c) between candidate-site phases in this full-domain arbitrary-switching geometry.",
            "The separate compatibility graph retains exactly those direction-blind labelled arcs for which some exact witness word and slot has the required c,target transition and the word's entire interior avoids the carried site x.",
            "Every nonzero consecutive-hit displacement contributes its exact canonical primitive selector direction.",
            "The selector union is unchanged by the globally merged-base quotient and carry-safe integer convolution, as proved algebraically and gated by a reduced legacy-enumeration equivalence self-test.",
            "The SCC, cycle, and DAG/longest-path conclusions are exact for that finite graph.",
        ],
        "proof_boundary_not_proved": [
            "In the original arbitrary-switching graph, the word witnessing a slot may itself contain the carried poison site x; its cycles are therefore not word-compatible certificates.",
            "The x-avoiding graph removes that permanent self-poison only. It does not prove that its witness word avoids other points of the carried line, other existing secants, collisions, or all exact-legality constraints.",
            "A compatibility-graph cycle's action labels coexist in one globally legal realized ordered path or survive the history-dependent no-new-x-line policy.",
            "A finite clean countdown prefix is not extrapolated. One poisoned residual contaminates every longer fixed-label countdown that traverses it; an infinite claim needs no positive orbit hit or an adaptive compatible-label proof.",
            "Acyclicity controls a line across intervals in which its candidate poison mask is empty; latent effectless re-entry remains open.",
            "Unrelated chronological cursor jumps, newly born near-deep or deep-deep non-x lines, endpoint-on-candidate-line poison, or collision provenance.",
            "Connector availability, a greatest safety fixed point, or an unconditional theorem.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_set_raw": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
    }


def estimate_payload(policy):
    return {
        "mode": "estimate",
        "status": (
            "no metadata/cache hash scan, mmap domain scan, pickle load, or "
            "output write performed"
        ),
        "resource_policy": policy,
        "pinned_inputs": {
            "metadata": str(DEFAULT_METADATA),
            "metadata_sha256": EXPECTED_METADATA_SHA256,
            "cache": str(DEFAULT_CACHE),
            "cache_sha256": EXPECTED_CACHE_SHA256,
            "cache_bytes": EXPECTED_CACHE_BYTES,
            "block_metadata_sha256": EXPECTED_BLOCK_METADATA_SHA256,
        },
        "expected_exact_scope": {
            "effective_words": EXPECTED_EFFECTIVE_WORDS,
            "ordered_word_slots": EXPECTED_WORD_SLOTS,
            "source_steps": EXPECTED_MENU_SIZE,
            "candidate_site_box": [
                [-SITE_RADIUS, SITE_RADIUS],
                [-SITE_RADIUS, SITE_RADIUS],
                [-SITE_RADIUS, SITE_RADIUS],
            ],
            "ambient_selector_vector_bound": SELECTOR_BOX_SIZE - 1,
        },
        "algorithm": [
            "one mmap pass builds exact full-3D candidate-site sets, source/control target-step masks, and exact intersections of witness-word interiors",
            "one source/control/site join deduplicates arcs only within one source step and writes separate globally sorted 12-byte original and x-avoiding arc spools",
            "scan poison maps are released before convolution; original and compatible graphs are mmaped and analyzed one at a time with a compact uint32 reverse CSR",
            "identical bases and identical exact successor-site sets are quotient-deduplicated before carry-safe 16-bit-lane integer difference convolutions",
            "a reduced legacy nested-pair enumeration must exactly match the optimized selector flags before the pinned scan starts",
            "iterative Kosaraju plus Kahn/condensation passes certify SCCs, cycles, and longest paths",
            "if cyclic, targeted cache passes recover exact word/slot witnesses for canonical cycles, including an x-avoiding word on every refined-cycle edge",
            "checker, metadata, and cache hashes plus filesystem identities are captured at start and verified unchanged at end",
        ],
        "estimated_resources": {
            "processes": 1,
            "threads": 1,
            "nice": 15,
            "peak_resident_memory_MiB": "target below 700; a 100,000-vertex, 1,999,790-arc DAG benchmark used 147.6 MiB RSS",
            "spooling_dictionary_benchmark_MiB": "204.8 with all 1,213,761 possible merged bases plus 500,000 unique arcs in one source-step dictionary",
            "resident_memory_design_target_MiB": 700,
            "emergency_stop_MiB": 900,
            "wall_seconds": "180--600 target; stop and profile rather than exceed the ten-minute trial cap",
            "output_MiB": "less than 5 expected",
            "temporary_disk": "12 bytes per unique original arc plus 12 bytes per unique x-avoiding arc; deleted after staged analysis",
        },
        "run_requires_separate_approval": True,
    }


def packed_graph_memory_benchmark(policy):
    """Reproducible acyclic stress case; no project cache is read."""
    started = time.monotonic()
    vertices = PACKED_BENCHMARK_VERTICES
    degree = PACKED_BENCHMARK_OUTDEGREE
    # Reproduce the largest simultaneous dictionaries in the spooling stage:
    # the complete proved base box and a substantial single-source arc table.
    merged_bases = {
        base: 1 << (base % EXPECTED_MENU_SIZE)
        for base in range(BASE_BOX_SIZE)
    }
    source_arc_metadata = {
        arc: 1 | ((arc % SITE_COUNT) << 16)
        for arc in range(PACKED_BENCHMARK_SOURCE_ARCS)
    }
    if len(merged_bases) != BASE_BOX_SIZE or len(source_arc_metadata) != (
        PACKED_BENCHMARK_SOURCE_ARCS
    ):
        raise AssertionError("packed dictionary benchmark construction drift")
    del source_arc_metadata
    del merged_bases
    gc.collect()

    records = 0
    with tempfile.TemporaryDirectory(
        prefix="nonx-packed-memory-benchmark-"
    ) as folder:
        path = Path(folder) / "dag-arcs.bin"
        with path.open("wb") as handle:
            for source in range(vertices):
                for target in range(
                    source + 1, min(vertices, source + degree + 1)
                ):
                    handle.write(
                        ARC_RECORD.pack(pack_arc(source, target), 0, 1)
                    )
                    records += 1
        nodes = array.array("I", range(vertices))
        graph = PackedArcGraph(
            {"path": path, "records": records}, nodes
        )
        structure = graph_structure(graph.as_graph_mapping())
        graph.close()
    result = structure["result"]
    if not result["degenerate_site_graph_is_acyclic"]:
        raise AssertionError("packed memory benchmark DAG became cyclic")
    if result["strongly_connected_components"] != vertices:
        raise AssertionError("packed memory benchmark SCC count drift")
    return {
        "mode": "benchmark",
        "status": "completed packed DAG memory benchmark",
        "resource_policy": policy,
        "vertices": vertices,
        "arcs": records,
        "nominal_outdegree": degree,
        "simulated_merged_base_states": BASE_BOX_SIZE,
        "simulated_unique_arcs_in_one_source_step": (
            PACKED_BENCHMARK_SOURCE_ARCS
        ),
        "arc_record_bytes": ARC_RECORD.size,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_set_raw": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "scope": (
            "stresses the full merged-base box plus a 500,000-arc source-local "
            "dedup table, then sorted-spool mmap, reverse CSR, singleton SCCs, "
            "and a nearly two-million-edge condensation DAG; it does not "
            "predict the cache scan's exact peak"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "benchmark", "run"))
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    policy = resource_policy(enforce=args.mode in ("benchmark", "run"))
    if args.mode == "estimate":
        print(json.dumps(estimate_payload(policy), sort_keys=True, indent=2))
        return
    if args.mode == "benchmark":
        print(
            json.dumps(
                packed_graph_memory_benchmark(policy),
                sort_keys=True,
                indent=2,
            )
        )
        return

    payload = run(args.metadata, args.cache)
    payload["resource_policy"] = policy
    atomic_json_dump(payload, args.output)
    observation = {
        "output": str(args.output.resolve()),
        "output_sha256": file_sha256(args.output),
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_set_raw": payload["maximum_resident_set_raw"],
    }
    print(json.dumps(observation, sort_keys=True))


if __name__ == "__main__":
    main()
