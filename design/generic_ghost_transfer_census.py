#!/usr/bin/env python3
"""Exact generic role-transfer census for the lattice-T action channels.

This checker keeps connector words atomic.  Its marginal role kernel is used
only for a prescribed descendant address or for a first-moment branching
calculation; a digest of every accepted word's complete ordered and unordered
role tuple, together with target-step sibling moments, records the correlation
which those marginals discard.

The expensive scan is resumable by disjoint source-step intervals.  Merge
requires a complete partition of the 124 source steps and computes:

* exact accepted length means and the 124 by 124 first-moment kernel B;
* the algebraic certificate ``B*1 >= 2*1``, hence ``rho(B) >= 2``;
* exact prescribed-role marginals, without claiming an unnecessary tight
  maximum cycle mean;
* the exact avoid-source kernel on the 780 lattice-T states.

It is not a chronological probability model.  In particular it has no line
birth operator, unrelated-cursor import, or conditioning on global legality.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import mmap
import os
import resource
import struct
import sys
import tempfile
import time
from array import array
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design"
ACTION_MODULE_PATH = DESIGN / "nonx_scc_core_action_probe.py"
DEFAULT_ACTIONS = Path("/tmp/nonx-lattice-envelope-action-probe.json")
DEFAULT_BITSETS = Path("/tmp/nonx-lattice-envelope-action-probe-bitsets.bin")
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_FIXED = Path("/tmp/nonx-fixed-word-policy-probe-v2.json")
DEFAULT_PREPARED = Path("/tmp/nonx-potential-compatible-word-prepared.json")
DEFAULT_OUTPUT = Path("/tmp/generic-ghost-transfer-census.json")
DEFAULT_SUMMARY = DESIGN / "generic-ghost-transfer-census-summary.json"

EXPECTED_SHA256 = {
    "action_checker": "9056394f5529036f2e4515490de4940ca42d04165eae928c32f1b027aae36fed",
    "actions": "9ce2de5f7936349b4cc7e830dcf962f26164693dbf66da1ba3fcc9a1d73e2112",
    "bitsets": "f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb",
    "metadata": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
    "cache": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
    "fixed": "e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e",
    "prepared": "5210a61f556573d39ad1ea2f3039bd5c36772b1fad4597d0920e5d6d9e6a28e1",
}
EXPECTED_BYTES = {
    "cache": 68_050_680,
    "bitsets": 3_136_860,
}
# Seven completed scan chunks were produced by this exact checker revision.
# Merge accepts that pinned revision so the expensive cache scan never has to
# be repeated merely because the compact merge/report code is improved.
LEGACY_CHUNK_CHECKER_SHA256 = (
    "777c1d836bba6be946b7ed972d91046764be69f3b1d747d0641475e78dd0b047"
)
CHANNELS = ("zero_envelope", "ordered_envelope")
MENU_SIZE = 124
MAX_WORK_SECONDS = 115.0
MAX_RESIDENT_BYTES = 280 * 1024 * 1024
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def load_action_module():
    spec = importlib.util.spec_from_file_location("lattice_action_probe", ACTION_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


A = load_action_module()
MENU = A.MENU


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def maximum_resident_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def resource_policy(enforce=True):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError("requires one numerical thread and nice >= 15", environment, nice)
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": nice,
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


def atomic_json_dump(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
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


def fraction_record(value):
    value = Fraction(value)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def role_code(control, target):
    return A.encode_site(control) * MENU_SIZE + target


def decode_role(code):
    control_site, target = divmod(code, MENU_SIZE)
    return A.decode_site(control_site), target


def bit_is_set(bits, ordinal_zero_based):
    return bool(bits[ordinal_zero_based >> 3] & (1 << (ordinal_zero_based & 7)))


def digest_integer(digest, value, width=8, signed=True):
    digest.update(int(value).to_bytes(width, "little", signed=signed))


def semantic_role_count_digest(source_step, role_counts):
    digest = hashlib.sha256()
    for code, count in sorted(role_counts.items()):
        control, target = decode_role(code)
        for value in (source_step, *control, target, count):
            digest_integer(digest, value)
    return digest.hexdigest()


def semantic_pair_moment_digest(source_step, values):
    digest = hashlib.sha256()
    for first in range(MENU_SIZE):
        for second in range(MENU_SIZE):
            count = values[first * MENU_SIZE + second]
            for value in (source_step, first, second, count):
                digest_integer(digest, value)
    return digest.hexdigest()


def validate_inputs(actions_path, bitsets_path, metadata_path, cache_path,
                    fixed_path, prepared_path):
    paths = {
        "action_checker": ACTION_MODULE_PATH,
        "actions": Path(actions_path),
        "bitsets": Path(bitsets_path),
        "metadata": Path(metadata_path),
        "cache": Path(cache_path),
        "fixed": Path(fixed_path),
        "prepared": Path(prepared_path),
    }
    snapshots = {}
    for name, path in paths.items():
        stat = path.stat()
        digest = file_sha256(path)
        if digest != EXPECTED_SHA256[name]:
            raise AssertionError("pinned input digest drift", name, digest)
        if name in EXPECTED_BYTES and stat.st_size != EXPECTED_BYTES[name]:
            raise AssertionError("pinned input byte count drift", name, stat.st_size)
        snapshots[name] = {
            "path": str(path.resolve()),
            "sha256": digest,
            "bytes": stat.st_size,
            "identity": [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns],
        }
    with Path(actions_path).open(encoding="utf-8") as handle:
        actions = json.load(handle)
    if actions["checker"]["sha256"] != EXPECTED_SHA256["action_checker"]:
        raise AssertionError("action/checker commitment drift")
    sidecar = dict(actions["accepted_ordinal_bitset_sidecar"])
    sidecar["path"] = str(Path(bitsets_path).resolve())
    bitset_blocks = A.read_bitset_sidecar(sidecar)
    blocks = A.load_metadata(metadata_path)
    if [item["step"] for item in bitset_blocks] != list(range(MENU_SIZE)):
        raise AssertionError("bitset block order drift")
    if [item["step"] for item in blocks] != list(range(MENU_SIZE)):
        raise AssertionError("cache block order drift")
    _, repeated_blocks, _, structure = A.load_structure(
        metadata_path, cache_path, fixed_path, prepared_path
    )
    if blocks != repeated_blocks:
        raise AssertionError("independent metadata load drift")
    return snapshots, blocks, bitset_blocks, structure


def word_roles(word):
    x = y = z = 0
    roles = []
    interiors = []
    for index, target in enumerate(word):
        control = (x, y, z)
        roles.append(role_code(control, target))
        dx, dy, dz = MENU[target]
        x += dx
        y += dy
        z += dz
        if index + 1 < len(word):
            interiors.append((x, y, z))
    return tuple(roles), tuple(interiors), (x, y, z)


def role_edges(source_step, code, structure, cache):
    key = source_step, code
    if key in cache:
        return cache[key]
    control, target_step = decode_role(code)
    mask, _backward = A.compute_role_masks(source_step, control, target_step, structure)
    result = []
    local_sites = structure["envelope_by_step"][source_step]
    for local_index in A.iter_mask(mask):
        source_site = local_sites[local_index]
        source = A.decode_site(source_site)
        target = A.apply_matrix(tuple(source[axis] - control[axis] for axis in range(3)))
        target_site = A.encode_site(target)
        source_node = structure["node_index"][source_step * A.SITE_COUNT + source_site]
        target_node = structure["node_index"][target_step * A.SITE_COUNT + target_site]
        result.append((local_index, source_node, target_node))
    result = tuple(result)
    cache[key] = result
    return result


def scan_step(block, bitsets, cache, structure, started):
    source_step = block["step"]
    endpoint = A.apply_matrix(MENU[source_step])
    envelope_index = {
        site: index for index, site in enumerate(structure["envelope_by_step"][source_step])
    }
    role_edge_cache = {}
    accumulators = {}
    for channel in CHANNELS:
        accumulators[channel] = {
            "accepted": 0,
            "slots": 0,
            "lengths": {2: 0, 3: 0, 4: 0, 5: 0},
            "targets": [0] * MENU_SIZE,
            "roles": {},
            "pairs": array("Q", [0]) * (MENU_SIZE * MENU_SIZE),
            "joint_ordered": hashlib.sha256(),
            "joint_unordered": hashlib.sha256(),
            "sibling_pairs": 0,
            "repeated_role_words": 0,
        }
    ordered_t_edges = {}
    cursor = block["start"]
    observed_slots = 0
    for ordinal in range(block["words"]):
        length = cache[cursor]
        cursor += 1
        word = tuple(cache[cursor:cursor + length])
        cursor += length
        observed_slots += length
        roles, interiors, observed_endpoint = word_roles(word)
        if observed_endpoint != endpoint:
            raise AssertionError("word endpoint drift", source_step, ordinal)
        repeated_role = len(set(roles)) != len(roles)
        interior_mask = 0
        for point in interiors:
            encoded = A.encode_site(point)
            local = envelope_index.get(encoded)
            if local is not None:
                interior_mask |= 1 << local
        accepted_channels = [
            channel for channel in CHANNELS if bit_is_set(bitsets[channel], ordinal)
        ]
        for channel in accepted_channels:
            item = accumulators[channel]
            item["accepted"] += 1
            item["slots"] += length
            item["lengths"][length] += 1
            item["sibling_pairs"] += length * (length - 1)
            item["repeated_role_words"] += repeated_role
            targets = [code % MENU_SIZE for code in roles]
            for code, target in zip(roles, targets):
                item["targets"][target] += 1
                item["roles"][code] = item["roles"].get(code, 0) + 1
            for first_index, first in enumerate(targets):
                base = first * MENU_SIZE
                for second_index, second in enumerate(targets):
                    if first_index != second_index:
                        item["pairs"][base + second] += 1
            header = struct.pack("<BIB", source_step, ordinal, length)
            ordered_payload = bytearray(header)
            for code in roles:
                ordered_payload.extend(struct.pack("<I", code))
            item["joint_ordered"].update(ordered_payload)
            unordered_payload = bytearray(header)
            for code in sorted(roles):
                unordered_payload.extend(struct.pack("<I", code))
            item["joint_unordered"].update(unordered_payload)

        if "ordered_envelope" in accepted_channels:
            for code in roles:
                for local, source_node, target_node in role_edges(
                    source_step, code, structure, role_edge_cache
                ):
                    if interior_mask & (1 << local):
                        continue
                    if structure["position"][source_node] >= structure["position"][target_node]:
                        raise AssertionError("ordered T edge is not forward", source_node, target_node)
                    key = source_node, target_node
                    ordered_t_edges[key] = ordered_t_edges.get(key, 0) + 1
        if "zero_envelope" in accepted_channels:
            for code in roles:
                for local, _source_node, _target_node in role_edges(
                    source_step, code, structure, role_edge_cache
                ):
                    if not (interior_mask & (1 << local)):
                        raise AssertionError("zero-envelope live T edge", source_step, ordinal)
        if (ordinal + 1) % 250_000 == 0:
            enforce_runtime(started, f"step {source_step} word {ordinal + 1}")
    if cursor != block["end"] or observed_slots != block["word_slots"]:
        raise AssertionError("cache block boundary drift", source_step)

    channel_records = {}
    for channel, item in accumulators.items():
        expected = bitsets[channel + "_count"]
        if item["accepted"] != expected:
            raise AssertionError("accepted count drift", source_step, channel)
        if item["accepted"] <= 0 or sum(item["lengths"].values()) != item["accepted"]:
            raise AssertionError("accepted length census drift", source_step, channel)
        if sum(item["targets"]) != item["slots"]:
            raise AssertionError("target slot census drift", source_step, channel)
        if item["repeated_role_words"]:
            raise AssertionError("an exact (control,target) role repeated in a word")
        maxima = []
        by_target = {}
        for code, count in item["roles"].items():
            control, target = decode_role(code)
            previous = by_target.get(target)
            candidate = count, control
            if previous is None or candidate > previous:
                by_target[target] = candidate
        for target in range(MENU_SIZE):
            count, control = by_target.get(target, (0, None))
            maxima.append({
                "target_step": target,
                "count": count,
                "control": None if control is None else list(control),
            })
        channel_records[channel] = {
            "accepted_words": item["accepted"],
            "accepted_slots": item["slots"],
            "accepted_length_histogram": {
                str(length): item["lengths"][length] for length in range(2, 6)
            },
            "accepted_mean_length": fraction_record(Fraction(
                item["slots"], item["accepted"]
            )),
            "target_slot_counts": item["targets"],
            "maximum_role_count_by_target": maxima,
            "distinct_exact_roles": len(item["roles"]),
            "exact_role_count_stream_sha256": semantic_role_count_digest(
                source_step, item["roles"]
            ),
            "complete_ordered_whole_word_role_stream_sha256": (
                item["joint_ordered"].hexdigest()
            ),
            "complete_unordered_whole_word_role_stream_sha256": (
                item["joint_unordered"].hexdigest()
            ),
            "ordered_sibling_role_pairs": item["sibling_pairs"],
            "target_step_ordered_sibling_moment_sha256": (
                semantic_pair_moment_digest(source_step, item["pairs"])
            ),
            "exact_role_multiplicity_maximum": 1,
        }
    return {
        "step": source_step,
        "parent_step": list(MENU[source_step]),
        "channels": channel_records,
        "T_avoid_source_kernel": {
            "zero_envelope_nonzero_edges": 0,
            "ordered_envelope_edges": [
                [source, target, count]
                for (source, target), count in sorted(ordered_t_edges.items())
            ],
        },
    }


def run_chunk(args):
    started = time.monotonic()
    policy = resource_policy(True)
    checker_sha = file_sha256(Path(__file__).resolve())
    snapshots, blocks, bitsets, structure = validate_inputs(
        args.actions, args.bitsets, args.metadata, args.cache, args.fixed, args.prepared
    )
    if not 0 <= args.first_step <= args.last_step < MENU_SIZE:
        raise ValueError("invalid inclusive source-step interval")
    selected = blocks[args.first_step:args.last_step + 1]
    records = []
    with Path(args.cache).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(A.CACHE_MAGIC)] != A.CACHE_MAGIC:
                raise AssertionError("cache magic drift")
            for block in selected:
                records.append(scan_step(block, bitsets[block["step"]], cache, structure, started))
                enforce_runtime(started, f"finished step {block['step']}")
        finally:
            cache.close()
    if file_sha256(Path(__file__).resolve()) != checker_sha:
        raise RuntimeError("checker changed during chunk")
    payload = {
        "schema_version": 1,
        "status": "exact generic whole-word ghost-role transfer chunk; not a probability model for chronological legality",
        "checker": {"path": "design/generic_ghost_transfer_census.py", "sha256": checker_sha},
        "resource_policy": policy,
        "pinned_inputs": snapshots,
        "step_scope_inclusive": [args.first_step, args.last_step],
        "steps": records,
        "lattice_T": {
            "vertices": len(structure["nodes"]),
            "vertex_stream_sha256": A.EXPECTED_ENVELOPE_DIGEST,
            "common_order_stream_sha256": structure["certificate"]["topological_order_stream_sha256"],
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }
    atomic_json_dump(payload, args.output)
    return payload


def collatz_interval(count_matrix, denominators):
    floating = [
        [count_matrix[source][target] / denominators[source] for target in range(MENU_SIZE)]
        for source in range(MENU_SIZE)
    ]
    vector = [1.0] * MENU_SIZE
    scale = 1.0
    for _ in range(1000):
        updated = [
            sum(floating[source][target] * vector[target] for target in range(MENU_SIZE))
            for source in range(MENU_SIZE)
        ]
        scale = max(updated)
        if not math.isfinite(scale) or scale <= 0:
            raise AssertionError("invalid Perron iteration")
        updated = [max(value / scale, 1e-100) for value in updated]
        if max(abs(updated[index] - vector[index]) for index in range(MENU_SIZE)) < 1e-15:
            vector = updated
            break
        vector = updated
    integer_vector = [max(1, round(value * 10**15)) for value in vector]
    ratios = []
    for source in range(MENU_SIZE):
        numerator = sum(
            count_matrix[source][target] * integer_vector[target]
            for target in range(MENU_SIZE)
        )
        ratios.append(Fraction(
            numerator, denominators[source] * integer_vector[source]
        ))
    lower = min(ratios)
    upper = max(ratios)
    if not lower <= scale <= upper:
        raise AssertionError("floating Perron estimate escaped exact Collatz interval")
    return {
        "theorem": "for the displayed positive integer vector v, min_s (Bv)_s/v_s <= spectral_radius(B) <= max_s (Bv)_s/v_s",
        "positive_integer_vector": integer_vector,
        "lower": fraction_record(lower),
        "upper": fraction_record(upper),
        "floating_power_iteration_estimate": scale,
        "strictly_above_one": lower > 1,
    }


def root_compare(first, second):
    """Compare positive roots (fraction, degree) exactly."""
    first_value, first_degree = first
    second_value, second_degree = second
    left = first_value ** second_degree
    right = second_value ** first_degree
    return (left > right) - (left < right)


def root_decimal_bracket(value, degree, digits=15):
    scale = 10**digits
    low = 0
    high = scale
    target = value.numerator * (scale ** degree)
    denominator = value.denominator
    while low < high:
        middle = (low + high + 1) // 2
        if (middle ** degree) * denominator <= target:
            low = middle
        else:
            high = middle - 1
    lower = Fraction(low, scale)
    if lower ** degree == value:
        upper = lower
    else:
        upper = Fraction(low + 1, scale)
    return fraction_record(lower), fraction_record(upper)


def karp_maximum_cycle_mean(max_role_counts, denominators):
    probabilities = [[Fraction() for _ in range(MENU_SIZE)] for _ in range(MENU_SIZE)]
    controls = [[None for _ in range(MENU_SIZE)] for _ in range(MENU_SIZE)]
    incoming = [[] for _ in range(MENU_SIZE)]
    edge_count = 0
    for source in range(MENU_SIZE):
        for target in range(MENU_SIZE):
            item = max_role_counts[source][target]
            if item["count"]:
                probability = Fraction(item["count"], denominators[source])
                probabilities[source][target] = probability
                controls[source][target] = item["control"]
                incoming[target].append((source, probability))
                edge_count += 1
    products = [[Fraction(1) for _ in range(MENU_SIZE)]]
    predecessors = []
    for length in range(1, MENU_SIZE + 1):
        previous = products[-1]
        current = [Fraction() for _ in range(MENU_SIZE)]
        predecessor = [-1] * MENU_SIZE
        for target in range(MENU_SIZE):
            best = Fraction()
            best_source = -1
            for source, probability in incoming[target]:
                candidate = previous[source] * probability
                if candidate > best:
                    best = candidate
                    best_source = source
            current[target] = best
            predecessor[target] = best_source
        if not all(current):
            raise AssertionError("role graph is not reachable from the super-source", length)
        products.append(current)
        predecessors.append(predecessor)

    per_vertex = []
    final = products[MENU_SIZE]
    for vertex in range(MENU_SIZE):
        candidates = []
        for length in range(MENU_SIZE):
            if products[length][vertex]:
                candidates.append((
                    final[vertex] / products[length][vertex],
                    MENU_SIZE - length,
                    length,
                ))
        best = candidates[0]
        for candidate in candidates[1:]:
            if root_compare(candidate[:2], best[:2]) < 0:
                best = candidate
        per_vertex.append((best[0], best[1], vertex, best[2]))
    optimum = per_vertex[0]
    for candidate in per_vertex[1:]:
        if root_compare(candidate[:2], optimum[:2]) > 0:
            optimum = candidate
    ratio, degree, vertex, prefix_length = optimum
    decimal_lower, decimal_upper = root_decimal_bracket(ratio, degree)
    global_max = max(
        probabilities[source][target]
        for source in range(MENU_SIZE) for target in range(MENU_SIZE)
    )
    return {
        "theorem": "multiplicative Karp theorem applied to P_st=max_control Pr[(control,t) occurs]",
        "nonzero_step_edges": edge_count,
        "exact_expression": {
            "radicand": fraction_record(ratio),
            "root_degree": degree,
            "Karp_terminal_vertex": vertex,
            "Karp_prefix_length": prefix_length,
        },
        "certified_decimal_lower": decimal_lower,
        "certified_decimal_upper": decimal_upper,
        "global_single_role_probability_upper_bound": fraction_record(global_max),
        "strictly_below_one": global_max < 1,
        "scope": "maximum asymptotic coefficient along one prescribed role ancestry; it is not the all-branches first moment",
    }


def semantic_matrix_digest(matrix, denominators, label):
    digest = hashlib.sha256(label.encode("ascii"))
    for source in range(MENU_SIZE):
        for target in range(MENU_SIZE):
            for value in (source, target, matrix[source][target], denominators[source]):
                digest_integer(digest, value)
    return digest.hexdigest()


def merge_chunks(args):
    started = time.monotonic()
    policy = resource_policy(True)
    checker_sha = file_sha256(Path(__file__).resolve())
    chunks = []
    observed_chunk_checkers = set()
    for path in args.chunks:
        with Path(path).open(encoding="utf-8") as handle:
            item = json.load(handle)
        chunk_checker = item["checker"]["sha256"]
        if chunk_checker not in (checker_sha, LEGACY_CHUNK_CHECKER_SHA256):
            raise AssertionError("chunk checker drift", path)
        observed_chunk_checkers.add(chunk_checker)
        chunks.append((item, Path(path)))
    if len(observed_chunk_checkers) != 1:
        raise AssertionError("chunks mix checker revisions", observed_chunk_checkers)
    chunk_checker_sha = next(iter(observed_chunk_checkers))
    chunks.sort(key=lambda pair: pair[0]["step_scope_inclusive"][0])
    next_step = 0
    records = []
    reference = chunks[0][0]
    for item, _path in chunks:
        first, last = item["step_scope_inclusive"]
        if first != next_step or not first <= last < MENU_SIZE:
            raise AssertionError("chunks do not form a disjoint contiguous partition")
        next_step = last + 1
        if item["pinned_inputs"] != reference["pinned_inputs"] or item["lattice_T"] != reference["lattice_T"]:
            raise AssertionError("chunk pins or lattice T drift")
        records.extend(item["steps"])
    if next_step != MENU_SIZE or [item["step"] for item in records] != list(range(MENU_SIZE)):
        raise AssertionError("chunks do not cover all 124 source steps")

    channel_results = {}
    for channel in CHANNELS:
        denominators = [item["channels"][channel]["accepted_words"] for item in records]
        matrix = [item["channels"][channel]["target_slot_counts"] for item in records]
        accepted = sum(denominators)
        slots = sum(item["channels"][channel]["accepted_slots"] for item in records)
        histogram = {
            str(length): sum(
                item["channels"][channel]["accepted_length_histogram"][str(length)]
                for item in records
            )
            for length in range(2, 6)
        }
        if sum(histogram.values()) != accepted:
            raise AssertionError("accepted length histogram drift", channel)
        if sum(int(length) * count for length, count in histogram.items()) != slots:
            raise AssertionError("accepted slot/length identity drift", channel)
        for source, item in enumerate(records):
            source_channel = item["channels"][channel]
            if sum(matrix[source]) != source_channel["accepted_slots"]:
                raise AssertionError("first-moment row-sum drift", channel, source)
            if not 2 * denominators[source] <= sum(matrix[source]) <= (
                5 * denominators[source]
            ):
                raise AssertionError("connector length escaped [2,5]", channel, source)
        channel_results[channel] = {
            "accepted_words": accepted,
            "accepted_slots": slots,
            "accepted_length_histogram": histogram,
            "aggregate_word_weighted_mean_length": fraction_record(Fraction(slots, accepted)),
            "per_source_step_mean_length_range": {
                "minimum": fraction_record(min(Fraction(
                    item["channels"][channel]["accepted_slots"],
                    item["channels"][channel]["accepted_words"],
                ) for item in records)),
                "maximum": fraction_record(max(Fraction(
                    item["channels"][channel]["accepted_slots"],
                    item["channels"][channel]["accepted_words"],
                ) for item in records)),
            },
            "first_moment_step_kernel": {
                "definition": "B_st=(1/|A_s|) sum_{w in A_s} multiplicity of target step t in w",
                "exact_count_denominator_stream_sha256": semantic_matrix_digest(
                    matrix, denominators, channel
                ),
                "row_sum_identity": "sum_t B_st is the accepted mean connector length at source step s and lies in [2,5]",
                "spectral_radius_certificate": {
                    "exact_inequalities": [
                        "B*1 >= 2*1",
                        "B*1 <= 5*1"
                    ],
                    "conclusion": "2 <= spectral_radius(B) <= 5",
                    "lower_bound_proof": "B^n*1 >= 2^n*1 for every n, so the Gelfand growth rate is at least 2",
                    "upper_bound_proof": "the infinity operator norm is at most the maximum row sum, which is at most 5",
                    "common_weighted_contraction_below_one_impossible": True,
                    "tight_value_computed": False,
                },
            },
            "prescribed_exact_role_kernel": {
                "status": "exact marginal counts and maximizing controls are sealed in the chunks; no tight cycle mean is claimed",
                "reason_omitted": "a tight prescribed-role cycle value is unnecessary for the rigorous all-branches obstruction and the earlier exact-radical merge was intentionally abandoned",
                "scope": "a fixed-address product, even if contracting, does not override spectral_radius(B)>=2 for all descendant branches",
                "maximum_role_count_by_target_step_digests": [
                    hashlib.sha256(json.dumps(
                        item["channels"][channel]["maximum_role_count_by_target"],
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()).hexdigest()
                    for item in records
                ],
            },
            "whole_word_correlation": {
                "ordered_role_stream_step_digests": [
                    item["channels"][channel]["complete_ordered_whole_word_role_stream_sha256"]
                    for item in records
                ],
                "unordered_role_stream_step_digests": [
                    item["channels"][channel]["complete_unordered_whole_word_role_stream_sha256"]
                    for item in records
                ],
                "target_sibling_moment_step_digests": [
                    item["channels"][channel]["target_step_ordered_sibling_moment_sha256"]
                    for item in records
                ],
                "ordered_sibling_role_pairs": sum(
                    item["channels"][channel]["ordered_sibling_role_pairs"]
                    for item in records
                ),
                "exact_role_multiplicity_maximum": 1,
                "joint_event_rule": "at one parent, require all sibling roles in the same accepted whole word and divide that joint word count by |A_s|; do not multiply sibling marginals",
            },
        }
        enforce_runtime(started, f"merged channel {channel}")

    ordered_edges = {}
    for item in records:
        for source, target, count in item["T_avoid_source_kernel"]["ordered_envelope_edges"]:
            key = source, target
            ordered_edges[key] = ordered_edges.get(key, 0) + count
    if any(item["T_avoid_source_kernel"]["zero_envelope_nonzero_edges"] for item in records):
        raise AssertionError("zero T kernel acquired an edge")
    if any(source >= 780 or target >= 780 for source, target in ordered_edges):
        raise AssertionError("T edge escaped node range")
    longest = [0] * 780
    adjacency = [[] for _ in range(780)]
    for source, target in ordered_edges:
        adjacency[source].append(target)
    # Node indices are not topological ranks, so use the pinned position array.
    _, _, _, structure = A.load_structure(
        args.metadata, args.cache, args.fixed, args.prepared
    )
    if any(
        structure["position"][source] >= structure["position"][target]
        for source, target in ordered_edges
    ):
        raise AssertionError("merged ordered-T edge violates the pinned strict order")
    order = sorted(range(780), key=lambda node: structure["position"][node], reverse=True)
    for source in order:
        if adjacency[source]:
            longest[source] = 1 + max(longest[target] for target in adjacency[source])
    edge_digest = hashlib.sha256()
    for (source, target), count in sorted(ordered_edges.items()):
        for value in (source, target, count):
            digest_integer(edge_digest, value)

    payload = {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact uniform-action generic role-transfer census; proves finite-T contraction but not chronological far-birth availability",
        "checker": {"path": "design/generic_ghost_transfer_census.py", "sha256": checker_sha},
        "chunk_checker_sha256": chunk_checker_sha,
        "artifact": {"path": str(Path(args.output).resolve())},
        "resource_policy": policy,
        "pinned_inputs": reference["pinned_inputs"],
        "chunk_runs": [
            {
                "scope": item["step_scope_inclusive"],
                "path": str(path.resolve()),
                "sha256": file_sha256(path),
                "elapsed_seconds": item["elapsed_seconds"],
                "maximum_resident_bytes": item["maximum_resident_bytes"],
            }
            for item, path in chunks
        ],
        "probability_space": {
            "model": "independently and uniformly select one frozen accepted whole word at every distinct visited parent gap",
            "fixed_address_formula": "for roles r_j=(s_j,c_j,t_j) at distinct parent gaps, Pr[address]=product_j count_{A_sj}(r_j)/|A_sj|",
            "same_parent_formula": "multiple sibling requirements use one joint whole-word count, not a product of role marginals",
            "conditional_legality_warning": "after conditioning on exact chronological legality the available set is history-dependent; an unconditional role probability can increase to one",
        },
        "channels": channel_results,
        "lattice_T_avoid_source_kernel": {
            "vertices": 780,
            "zero_envelope": {
                "nonzero_edges": 0,
                "spectral_radius": 0,
                "reason": "every T-source role edge is covered by a proper interior of that same accepted whole word",
            },
            "ordered_envelope": {
                "nonzero_edges": len(ordered_edges),
                "weighted_transition_occurrences": sum(ordered_edges.values()),
                "edge_count_stream_sha256": edge_digest.hexdigest(),
                "longest_directed_path_edges": max(longest),
                "nilpotence_exponent_upper_bound": max(longest) + 1,
                "nilpotent": True,
                "spectral_radius": 0,
                "reason": "every live edge follows the pinned common strict T order",
            },
        },
        "proved": [
            "the exact fixed-address product under the displayed independent uniform whole-word model",
            "all exact role multiplicities, accepted length means, first moments, and whole-word role-stream commitments for both frozen channels",
            "the algebraic bounds 2 <= spectral_radius(B) <= 5 for each all-descendant first-moment branching kernel",
            "zero and nilpotent avoid-source kernels on the finite lattice T for the zero and ordered channels respectively",
        ],
        "not_proved": [
            "that independent uniform accepted actions are globally legal or define a chronological safety policy",
            "an upper bound after conditioning on the history-dependent legal subset",
            "transport of silent Pluecker ghosts outside T, line births, endpoint pairs, or deep-deep closure",
            "unrelated same-level cursor imports, whose exact reframe has no accepted-role probability factor",
            "a summable reachable-birth moment, LLL dependency bound, connector survivor, or unconditional theorem",
            "a tight Perron root or maximum prescribed-role cycle mean",
        ],
        "interpretation": {
            "fixed_address": "strict contraction along one prescribed role ancestry is real in the artificial model",
            "branching": "the role-only all-descendant operator expands because every accepted connector has length at least two; no common positive weighted norm can make its spectral radius below one",
            "cubic_growth": "a cubic local point count supplies no orientation-sensitive reduction; multiplying by any additional birth or shell growth only worsens the already expansive branching bound",
            "cursor_import": "a same-level cursor change can expose a retained token without any connector-role occurrence, so it contributes a coefficient-one import outside these kernels",
            "LLL_boundary": "the census can parameterize a proposed product measure, but the unary old-old-new events, quadratic pair births, global dependencies, and legality conditioning still require a separate reachable-birth/local-dependency theorem",
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }
    atomic_json_dump(payload, args.output)
    payload["artifact"]["bytes"] = Path(args.output).stat().st_size
    payload["artifact"]["sha256"] = file_sha256(args.output)
    atomic_json_dump(payload, args.summary)
    return payload


def synthetic_self_check():
    if len(MENU) != MENU_SIZE:
        raise AssertionError("menu size drift")
    examples = (
        (Fraction(1, 4), 2, Fraction(1, 8), 3),
        (Fraction(9, 16), 2, Fraction(3, 4), 1),
        (Fraction(1, 3), 1, Fraction(1, 9), 2),
    )
    for first, d1, second, d2 in examples:
        observed = root_compare((first, d1), (second, d2))
        left = float(first) ** (1 / d1)
        right = float(second) ** (1 / d2)
        expected = (left > right) - (left < right)
        if observed != expected:
            raise AssertionError("exact root comparison drift")
    for value, degree in ((Fraction(1, 2), 1), (Fraction(1, 4), 2), (Fraction(7, 19), 5)):
        lower, upper = root_decimal_bracket(value, degree, digits=9)
        low = Fraction(lower["numerator"], lower["denominator"])
        high = Fraction(upper["numerator"], upper["denominator"])
        if not low ** degree <= value <= high ** degree:
            raise AssertionError("root bracket drift")
    # Two-node multiplicative Karp identity, checked directly.
    cycle = (Fraction(1, 3) * Fraction(3, 5), 2)
    if root_compare(cycle, (Fraction(1, 5), 2)) != 0:
        raise AssertionError("cycle root identity drift")
    return {
        "status": "passed",
        "exact_root_comparisons": len(examples),
        "certified_root_brackets": 3,
        "same_whole_word_rule": "joint sibling requirements are one event",
    }


def parser():
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    check = sub.add_parser("self-check")
    scan = sub.add_parser("scan")
    scan.add_argument("--first-step", type=int, required=True)
    scan.add_argument("--last-step", type=int, required=True)
    scan.add_argument("--output", type=Path, required=True)
    merge = sub.add_parser("merge")
    merge.add_argument("--chunks", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    merge.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    for item in (scan, merge):
        item.add_argument("--actions", type=Path, default=DEFAULT_ACTIONS)
        item.add_argument("--bitsets", type=Path, default=DEFAULT_BITSETS)
        item.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
        item.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
        item.add_argument("--fixed", type=Path, default=DEFAULT_FIXED)
        item.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    return result


def main():
    args = parser().parse_args()
    if args.command == "self-check":
        print(json.dumps(synthetic_self_check(), sort_keys=True, indent=2))
    elif args.command == "scan":
        print(json.dumps(run_chunk(args), sort_keys=True, indent=2))
    elif args.command == "merge":
        print(json.dumps(merge_chunks(args), sort_keys=True, indent=2))
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
