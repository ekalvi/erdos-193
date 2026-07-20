#!/usr/bin/env python3
"""Exact finite birth scan for the two known non-x secant templates.

This checker joins three already-pinned objects without enumerating point
pairs:

* the L5--L8 realized construction pickles and their stitch chronology;
* the compact connector domains; and
* the zero-envelope and ordered-envelope accepted-word ordinal bitsets.

For each step-8 corridor it asks whether the latent line

    L_n = {x : x cross g_n = p cross g_n},
    p=(-9/2,-39/11,-31/11), g_n=N^(2n)(55,34,18),

is already a live secant when the corridor is stitched.  It also performs the
same finite scan for the older J=11/3 two-cycle family through
(-3,0,-3).  A moment hash retains at most the two points on each requested
line, so no quadratic pair enumeration occurs.

The scan is complete for each finite path: if primitive direction g occurs as
a secant of an N-point walk with Chebyshev step at most two, then
||g||_infinity <= 2(N-1).  The first family member beyond that bound is
therefore excluded without a point scan.

The reported action coefficients use a deliberately explicit experimental
model: independently and uniformly choose one accepted whole word at each
phase.  They are exact rational statistics of the frozen bitsets, not a
probability law for reachable legal histories.  The weighted sums are finite
selected-orbit evidence only; they do not prove a uniform birth envelope,
chronological availability, or Erdos #193.

Run the lightweight checks first, on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/known_template_weighted_birth_probe.py self-check

The exact L5--L8 scan is:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/known_template_weighted_birth_probe.py run \
        --output /tmp/known-template-weighted-birth-probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import pickle
import resource
import struct
import sys
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_ACTIONS = Path("/tmp/nonx-lattice-envelope-action-probe.json")
DEFAULT_BITSETS = Path("/tmp/nonx-lattice-envelope-action-probe-bitsets.bin")
DEFAULT_OUTPUT = Path("/tmp/known-template-weighted-birth-probe.json")

LEVELS = (5, 6, 7, 8)
EXPECTED_POINT_COUNTS = {5: 8_214, 6: 27_697, 7: 92_732, 8: 311_738}
EXPECTED_SHA256 = {
    "metadata": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
    "cache": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
    "actions": "9ce2de5f7936349b4cc7e830dcf962f26164693dbf66da1ba3fcc9a1d73e2112",
    "bitsets": "f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb",
    "action_checker": "9056394f5529036f2e4515490de4940ca42d04165eae928c32f1b027aae36fed",
    "gate2-l7-construction-L5.pkl": "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
    "gate2-l7-construction-L6.pkl": "70fa3baac057492fb8ad325eba5417bdc1e98fbd474bec37dc5f5465230f9298",
    "gate2-l7-construction-L7.pkl": "304e71eb74939662c0d0251864193171e74f49fd2023a98df09dc45d99fa0660",
    "gate2-l7-construction-L8.pkl": "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141",
}
EXPECTED_BYTES = {
    "metadata": 45_693,
    "cache": 68_050_680,
    "actions": 460_704,
    "bitsets": 3_136_860,
    "gate2-l7-construction-L5.pkl": 71_933,
    "gate2-l7-construction-L6.pkl": 242_888,
    "gate2-l7-construction-L7.pkl": 818_165,
    "gate2-l7-construction-L8.pkl": 2_709_484,
}

CACHE_MAGIC = b"NOXLN001"
BITSET_MAGIC = b"NTACB001"
BITSET_SCHEMA = 1
MAX_WORK_SECONDS = 115.0
MAX_RESIDENT_BYTES = 280 * 1024 * 1024
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
N_MATRIX = (
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

LATENT_SOURCE_STEP = 8
LATENT_P_NUMERATOR = (-99, -78, -62)
LATENT_P_DENOMINATOR = 22
LATENT_BASE_DIRECTION = (55, 34, 18)
LATENT_REVEAL_SITE = (-2, -2, -2)
LATENT_PHASES = (
    {
        "name": "a8",
        "step": 8,
        "control": (-4, -4, -3),
        "target_step": 16,
        "avoid_site": None,
    },
    {
        "name": "a16",
        "step": 16,
        "control": (0, 0, 0),
        "target_step": 8,
        "avoid_site": None,
    },
)
LATENT_SELECTED_WORDS = {8: (0, 1, 16), 16: (8, 23, 24)}

J_SOURCE_STEP = 1
J_BASE_DIRECTION = (3, -1, 3)
J_PHASE_A_SITE = (-3, 0, -3)
J_PHASE_B_SITE = (-3, 3, -2)
J_REVEAL_SITE = (-6, 1, -6)
J_PHASES = (
    {
        "name": "phase_A",
        "step": 1,
        "control": (-2, 1, -2),
        "target_step": 1,
        "avoid_site": J_PHASE_A_SITE,
    },
    {
        "name": "phase_B",
        "step": 1,
        "control": (-2, 4, -2),
        "target_step": 1,
        "avoid_site": J_PHASE_B_SITE,
    },
)
J_SELECTED_WORDS = ((15, 1, 20, 71), (20, 71, 1, 15))

ROLE_SPECS = LATENT_PHASES + J_PHASES
TARGET_STEPS = tuple(sorted({spec["step"] for spec in ROLE_SPECS}))


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce=True):
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in observed.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run requires every numerical thread control=1 and nice>=15",
            observed,
            nice,
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": observed,
        "process_nice": nice,
        "required_minimum_nice": 15,
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


def stable_snapshot(path, display_name=None):
    path = Path(path).resolve()
    before = path.stat()
    digest = file_sha256(path)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    identity_before = tuple(getattr(before, field) for field in fields)
    identity_after = tuple(getattr(after, field) for field in fields)
    if identity_before != identity_after:
        raise RuntimeError("input changed while being hashed", str(path))
    return {
        "name": display_name or path.name,
        "path": str(path),
        "sha256": digest,
        "bytes": after.st_size,
        "identity": list(identity_after),
    }


def verify_snapshot_unchanged(snapshot):
    path = Path(snapshot["path"])
    stat = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if [getattr(stat, field) for field in fields] != snapshot["identity"]:
        raise RuntimeError("input identity changed during exact work", str(path))
    if file_sha256(path) != snapshot["sha256"]:
        raise RuntimeError("input contents changed during exact work", str(path))


def pinned_snapshots(metadata_path, cache_path, actions_path, bitsets_path, pickles):
    paths = {
        "metadata": metadata_path,
        "cache": cache_path,
        "actions": actions_path,
        "bitsets": bitsets_path,
        "action_checker": ROOT / "design" / "nonx_scc_core_action_probe.py",
    }
    if pickles:
        paths.update({
            f"gate2-l7-construction-L{level}.pkl": (
                ROOT / f"gate2-l7-construction-L{level}.pkl"
            )
            for level in LEVELS
        })
    snapshots = {
        name: stable_snapshot(path, name) for name, path in paths.items()
    }
    for name, snapshot in snapshots.items():
        expected = EXPECTED_SHA256[name]
        if snapshot["sha256"] != expected:
            raise AssertionError("pinned input digest drift", name, snapshot, expected)
        if name in EXPECTED_BYTES and snapshot["bytes"] != EXPECTED_BYTES[name]:
            raise AssertionError("pinned input byte count drift", name, snapshot)
    return snapshots


def atomic_json_dump(value, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=output_path.parent, prefix=output_path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
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


def add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def canonical_primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if divisor == 0:
        raise ValueError("zero vector has no primitive direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def inverse_macro_direction(base, n):
    direction = base
    for _ in range(2 * n):
        direction = matrix_vector(N_MATRIX, direction)
    return canonical_primitive(direction)


def word_geometry(word):
    position = (0, 0, 0)
    prefixes = []
    interiors = []
    for slot, letter in enumerate(word):
        prefixes.append(position)
        position = add(position, MENU[letter])
        if slot + 1 < len(word):
            interiors.append(position)
    return tuple(prefixes), tuple(interiors), position


def validate_exact_constants():
    identity = tuple(
        tuple(
            sum(M[row][middle] * N_MATRIX[middle][column] for middle in range(3))
            for column in range(3)
        )
        for row in range(3)
    )
    assert identity == ((9, 0, 0), (0, 9, 0), (0, 0, 9))
    assert len(MENU) == 124
    assert canonical_primitive(
        subtract(J_REVEAL_SITE, J_PHASE_A_SITE)
    ) == J_BASE_DIRECTION
    for n in range(12):
        latent = inverse_macro_direction(LATENT_BASE_DIRECTION, n)
        moment_numerator = cross(LATENT_P_NUMERATOR, latent)
        assert all(value % LATENT_P_DENOMINATOR == 0 for value in moment_numerator)
        assert math.gcd(*(abs(value) for value in latent)) == 1
        j_direction = inverse_macro_direction(J_BASE_DIRECTION, n)
        assert math.gcd(*(abs(value) for value in j_direction)) == 1


def fraction_record(value):
    value = Fraction(value)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def load_metadata(path):
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    cache_record = payload["compact_domain_cache"]
    if cache_record["magic_ascii"] != CACHE_MAGIC.decode("ascii"):
        raise AssertionError("compact cache metadata magic drift")
    if cache_record["sha256"] != EXPECTED_SHA256["cache"]:
        raise AssertionError("embedded compact cache digest drift")
    blocks = {item["step"]: item for item in cache_record["blocks"]}
    if set(blocks) != set(range(len(MENU))):
        raise AssertionError("compact cache block census drift")
    return payload, blocks


def load_target_bitsets(actions_path, bitsets_path):
    with Path(actions_path).open(encoding="utf-8") as handle:
        actions = json.load(handle)
    if actions["schema_version"] != 1 or "not chronological availability" not in actions[
        "status"
    ]:
        raise AssertionError("action certificate status drift")
    if actions["checker"]["sha256"] != EXPECTED_SHA256["action_checker"]:
        raise AssertionError("embedded action checker digest drift")
    sidecar = actions["accepted_ordinal_bitset_sidecar"]
    if sidecar["sha256"] != EXPECTED_SHA256["bitsets"]:
        raise AssertionError("embedded bitset digest drift")
    data = Path(bitsets_path).read_bytes()
    if data[: len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("bitset sidecar magic drift")
    schema, block_count = struct.unpack_from("<II", data, len(BITSET_MAGIC))
    if schema != BITSET_SCHEMA or block_count != len(MENU):
        raise AssertionError("bitset sidecar header drift", schema, block_count)
    metadata_by_step = {item["step"]: item for item in sidecar["blocks"]}
    result = {}
    for step in TARGET_STEPS:
        expected = metadata_by_step[step]
        cursor = expected["block_offset"]
        observed = struct.unpack_from("<IIIII", data, cursor)
        source_step, words, byte_count, zero_count, ordered_count = observed
        cursor += 20
        zero = data[cursor : cursor + byte_count]
        cursor += byte_count
        ordered = data[cursor : cursor + byte_count]
        if source_step != step or words != expected["words"]:
            raise AssertionError("target bitset block identity drift", step)
        for channel, bits, count in (
            ("zero_envelope", zero, zero_count),
            ("ordered_envelope", ordered, ordered_count),
        ):
            commitment = expected[channel]
            if (
                hashlib.sha256(bits).hexdigest() != commitment["sha256"]
                or sum(byte.bit_count() for byte in bits) != count
                or count != commitment["set_bits"]
            ):
                raise AssertionError("target bitset channel drift", step, channel)
        if any(zero[index] & ~ordered[index] for index in range(byte_count)):
            raise AssertionError("zero target bitset is not ordered subset", step)
        result[step] = {
            "words": words,
            "zero_envelope": zero,
            "ordered_envelope": ordered,
            "zero_envelope_count": zero_count,
            "ordered_envelope_count": ordered_count,
        }
    return actions, result


def bit_is_set(bits, ordinal):
    return bool(bits[ordinal >> 3] & (1 << (ordinal & 7)))


def role_multiplicity(word, prefixes, interiors, spec):
    if spec["avoid_site"] is not None and spec["avoid_site"] in interiors:
        return 0
    return sum(
        letter == spec["target_step"] and prefix == spec["control"]
        for letter, prefix in zip(word, prefixes)
    )


def exact_action_statistics(metadata_blocks, cache_path, bitsets):
    per_channel = {
        channel: {
            "accepted_by_step": Counter(),
            "role_words": Counter(),
            "role_slots": Counter(),
            "latent_reveal_words": 0,
            "j_current_site_words": 0,
            "j_reveal_site_words": 0,
            "j_reveal_without_current_words": 0,
            "j_current_or_reveal_words": 0,
            "selected_word_acceptance": {},
        }
        for channel in ("zero_envelope", "ordered_envelope")
    }
    selected_words = {
        1: J_SELECTED_WORDS,
        8: (LATENT_SELECTED_WORDS[8],),
        16: (LATENT_SELECTED_WORDS[16],),
    }
    role_specs_by_step = defaultdict(list)
    for spec in ROLE_SPECS:
        role_specs_by_step[spec["step"]].append(spec)

    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[: len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for step in TARGET_STEPS:
                block = metadata_blocks[step]
                encoded = cache[block["start"] : block["end"]]
                if hashlib.sha256(encoded).hexdigest() != block["encoded_block_sha256"]:
                    raise AssertionError("target compact block digest drift", step)
                cursor = block["start"]
                observed_slots = 0
                observed_words = 0
                selected_seen = Counter()
                for ordinal in range(block["words"]):
                    length = cache[cursor]
                    cursor += 1
                    word = tuple(cache[cursor : cursor + length])
                    cursor += length
                    observed_words += 1
                    observed_slots += length
                    prefixes, interiors, endpoint = word_geometry(word)
                    if endpoint != matrix_vector(M, MENU[step]):
                        raise AssertionError("cached word endpoint drift", step, ordinal)
                    for selected in selected_words[step]:
                        if word == selected:
                            selected_seen[selected] += 1
                    multiplicities = {
                        spec["name"]: role_multiplicity(
                            word, prefixes, interiors, spec
                        )
                        for spec in role_specs_by_step[step]
                    }
                    if any(value > 1 for value in multiplicities.values()):
                        raise AssertionError(
                            "action role occurs more than once in a word",
                            step,
                            word,
                            multiplicities,
                        )
                    for channel in per_channel:
                        if not bit_is_set(bitsets[step][channel], ordinal):
                            continue
                        stats = per_channel[channel]
                        stats["accepted_by_step"][step] += 1
                        for name, multiplicity in multiplicities.items():
                            stats["role_slots"][name] += multiplicity
                            stats["role_words"][name] += bool(multiplicity)
                        if step == 8 and LATENT_REVEAL_SITE in interiors:
                            stats["latent_reveal_words"] += 1
                        if step == 1:
                            current = J_PHASE_A_SITE in interiors
                            reveal = J_REVEAL_SITE in interiors
                            stats["j_current_site_words"] += current
                            stats["j_reveal_site_words"] += reveal
                            stats["j_reveal_without_current_words"] += reveal and not current
                            stats["j_current_or_reveal_words"] += current or reveal
                        for selected in selected_words[step]:
                            if word == selected:
                                key = f"step_{step}:" + ",".join(map(str, selected))
                                stats["selected_word_acceptance"][key] = True
                if cursor != block["end"] or observed_slots != block["word_slots"]:
                    raise AssertionError("target compact block boundary drift", step)
                if observed_words != bitsets[step]["words"]:
                    raise AssertionError("cache/bitset word census drift", step)
                if set(selected_seen) != set(selected_words[step]) or any(
                    count != 1 for count in selected_seen.values()
                ):
                    raise AssertionError("selected word occurrence drift", step, selected_seen)
                for channel in per_channel:
                    expected = bitsets[step][channel + "_count"]
                    if per_channel[channel]["accepted_by_step"][step] != expected:
                        raise AssertionError("accepted target count drift", step, channel)
        finally:
            cache.close()

    result = {}
    for channel, stats in per_channel.items():
        accepted_1 = stats["accepted_by_step"][1]
        accepted_8 = stats["accepted_by_step"][8]
        accepted_16 = stats["accepted_by_step"][16]
        a8 = Fraction(stats["role_words"]["a8"], accepted_8)
        a16 = Fraction(stats["role_words"]["a16"], accepted_16)
        r8 = Fraction(stats["latent_reveal_words"], accepted_8)
        phase_a = Fraction(stats["role_words"]["phase_A"], accepted_1)
        phase_b = Fraction(stats["role_words"]["phase_B"], accepted_1)
        j_incremental = Fraction(
            stats["j_reveal_without_current_words"], accepted_1
        )
        result[channel] = {
            "accepted_words": {
                "step_1": accepted_1,
                "step_8": accepted_8,
                "step_16": accepted_16,
            },
            "latent_L_n_macro": {
                "a8_definition": (
                    "fraction of accepted step-8 whole words with the unique "
                    "target-16 slot at prefix control (-4,-4,-3)"
                ),
                "a8_qualifying_words": stats["role_words"]["a8"],
                "a8_qualifying_slots": stats["role_slots"]["a8"],
                "a8": fraction_record(a8),
                "a16_definition": (
                    "fraction of accepted step-16 whole words with the unique "
                    "target-8 slot at prefix control (0,0,0)"
                ),
                "a16_qualifying_words": stats["role_words"]["a16"],
                "a16_qualifying_slots": stats["role_slots"]["a16"],
                "a16": fraction_record(a16),
                "theta_equals_a8_times_a16": fraction_record(a8 * a16),
                "r8_definition": (
                    "fraction of accepted step-8 whole words whose proper "
                    "interiors contain (-2,-2,-2)"
                ),
                "r8_words": stats["latent_reveal_words"],
                "r8": fraction_record(r8),
            },
            "J_11_over_3_macro": {
                "phase_A_requires_avoiding": list(J_PHASE_A_SITE),
                "phase_A_qualifying_words": stats["role_words"]["phase_A"],
                "phase_A": fraction_record(phase_a),
                "phase_B_requires_avoiding": list(J_PHASE_B_SITE),
                "phase_B_qualifying_words": stats["role_words"]["phase_B"],
                "phase_B": fraction_record(phase_b),
                "theta_equals_phase_A_times_phase_B": fraction_record(
                    phase_a * phase_b
                ),
                "terminal_current_site_words": stats["j_current_site_words"],
                "terminal_reveal_site_words": stats["j_reveal_site_words"],
                "terminal_reveal_without_current_site_words": stats[
                    "j_reveal_without_current_words"
                ],
                "terminal_current_or_reveal_words": stats[
                    "j_current_or_reveal_words"
                ],
                "incremental_reveal_fraction": fraction_record(j_incremental),
                "full_terminal_union_fraction": fraction_record(Fraction(
                    stats["j_current_or_reveal_words"], accepted_1
                )),
            },
            "selected_word_acceptance": dict(sorted(
                stats["selected_word_acceptance"].items()
            )),
        }
    return result


def load_and_validate_states(snapshots):
    states = {}
    for level in LEVELS:
        name = f"gate2-l7-construction-L{level}.pkl"
        path = Path(snapshots[name]["path"])
        with path.open("rb") as handle:
            state = pickle.load(handle)
        if set(state) != {"parent_word", "order", "words", "anchors"}:
            raise AssertionError("construction pickle key drift", level)
        gap_count = len(state["parent_word"])
        if len(state["anchors"]) != gap_count + 1:
            raise AssertionError("construction anchor census drift", level)
        if len(state["order"]) != gap_count or set(state["order"]) != set(
            range(gap_count)
        ):
            raise AssertionError("construction schedule drift", level)
        if set(state["words"]) != set(range(gap_count)):
            raise AssertionError("construction selected-word key drift", level)
        point_count = len(state["anchors"])
        for gap in range(gap_count):
            source_step = state["parent_word"][gap]
            word = tuple(state["words"][gap])
            if not 1 <= len(word) <= 5:
                raise AssertionError("selected word length drift", level, gap)
            prefixes, interiors, endpoint = word_geometry(word)
            del prefixes
            point_count += len(interiors)
            if endpoint != matrix_vector(M, MENU[source_step]):
                raise AssertionError("selected endpoint drift", level, gap)
            if add(tuple(state["anchors"][gap]), endpoint) != tuple(
                state["anchors"][gap + 1]
            ):
                raise AssertionError("selected anchor join drift", level, gap)
        if point_count != EXPECTED_POINT_COUNTS[level]:
            raise AssertionError("final point census drift", level, point_count)
        states[level] = state

    for level in LEVELS[:-1]:
        parent = states[level]
        child = states[level + 1]
        flattened = tuple(
            letter
            for gap in range(len(parent["parent_word"]))
            for letter in parent["words"][gap]
        )
        if flattened != tuple(child["parent_word"]):
            raise AssertionError("parent/child ordered-factor drift", level)
        cursor = 0
        for gap in range(len(parent["parent_word"])):
            prefixes, _interiors, _endpoint = word_geometry(
                tuple(parent["words"][gap])
            )
            for slot, prefix in enumerate(prefixes):
                expected = matrix_vector(
                    M, add(tuple(parent["anchors"][gap]), prefix)
                )
                if tuple(child["anchors"][cursor + slot]) != expected:
                    raise AssertionError(
                        "parent/child affine anchor drift", level, gap, slot
                    )
            cursor += len(parent["words"][gap])
        if cursor != len(child["parent_word"]):
            raise AssertionError("parent/child cursor drift", level)
        if tuple(child["anchors"][-1]) != matrix_vector(
            M, tuple(parent["anchors"][-1])
        ):
            raise AssertionError("parent/child terminal anchor drift", level)
    return states


def build_anchor_origins(states):
    origins = {
        5: tuple((0, 4, anchor, -1) for anchor in range(len(states[5]["anchors"])))
    }
    for level in LEVELS[:-1]:
        current = origins[level]
        produced = []
        state = states[level]
        for gap in range(len(state["parent_word"])):
            produced.append(current[gap])
            for slot in range(len(state["words"][gap]) - 1):
                produced.append((1, level, gap, slot))
        produced.append(current[-1])
        if len(produced) != len(states[level + 1]["anchors"]):
            raise AssertionError("origin propagation census drift", level)
        origins[level + 1] = tuple(produced)
    return origins


def iter_placed_points(state, position_by_gap, anchor_origins, level):
    for anchor, point in enumerate(state["anchors"]):
        yield tuple(point), -1, (0, anchor, -1), anchor_origins[anchor]
    for gap in range(len(state["parent_word"])):
        point = tuple(state["anchors"][gap])
        word = tuple(state["words"][gap])
        for slot, letter in enumerate(word[:-1]):
            point = add(point, MENU[letter])
            yield (
                point,
                position_by_gap[gap],
                (1, gap, slot),
                (1, level, gap, slot),
            )


def origin_record(origin, states):
    kind, level, gap_or_anchor, slot = origin
    if kind == 0:
        return {
            "kind": "pre_L5_vertex",
            "birth_level_upper_bound": 4,
            "birth_level_exact": False,
            "pre_L5_vertex_index": gap_or_anchor,
        }
    position_by_gap = {
        gap: position for position, gap in enumerate(states[level]["order"])
    }
    return {
        "kind": "connector_interior",
        "birth_level": level,
        "birth_level_exact": True,
        "birth_gap": gap_or_anchor,
        "birth_order_position": position_by_gap[gap_or_anchor],
        "interior_slot_zero_based": slot,
        "stable_origin_id": f"L{level}:G{gap_or_anchor}:I{slot}",
    }


def endpoint_record(item, level, states):
    _sort_key, point, identity, origin = item
    kind, first, slot = identity
    if kind == 0:
        current_id = f"anchor:L{level}:A{first}"
        current_kind = "anchor"
        current_gap = None
    else:
        current_id = f"connector:L{level}:G{first}:I{slot}"
        current_kind = "connector_interior"
        current_gap = first
    return {
        "current_stable_id": current_id,
        "current_kind": current_kind,
        "current_gap": current_gap,
        "current_interior_slot_zero_based": None if kind == 0 else slot,
        "coordinate": list(point),
        "current_level_birth_order_position": _sort_key[0],
        "origin": origin_record(origin, states),
    }


def pair_birth_shell(endpoints):
    origins = [item[3] for item in endpoints]
    exact_levels = [origin[1] for origin in origins if origin[0] == 1]
    if not exact_levels:
        return "at_or_before_L4"
    return f"L{max(exact_levels)}"


def latent_relative_moment(direction):
    numerator = cross(LATENT_P_NUMERATOR, direction)
    if any(value % LATENT_P_DENOMINATOR for value in numerator):
        raise AssertionError("latent moment lost integrality", direction, numerator)
    return tuple(value // LATENT_P_DENOMINATOR for value in numerator)


def template_spec(name):
    if name == "latent_L_n":
        return {
            "name": name,
            "source_step": LATENT_SOURCE_STEP,
            "base_direction": LATENT_BASE_DIRECTION,
            "relative_moment": latent_relative_moment,
            "relative_line_description": (
                "line through p=(-9/2,-39/11,-31/11) in direction g_n"
            ),
        }
    if name == "J_11_over_3":
        return {
            "name": name,
            "source_step": J_SOURCE_STEP,
            "base_direction": J_BASE_DIRECTION,
            "relative_moment": lambda direction: cross(J_PHASE_A_SITE, direction),
            "relative_line_description": (
                "line through phase-A site (-3,0,-3) in direction g_n"
            ),
        }
    raise ValueError("unknown template", name)


def possible_n_range(point_count, base_direction):
    maximum_gap = point_count - 1
    included = []
    n = 0
    while True:
        direction = inverse_macro_direction(base_direction, n)
        norm = max(map(abs, direction))
        if norm > 2 * maximum_gap:
            return tuple(included), {
                "first_excluded_n": n,
                "primitive_direction": list(direction),
                "direction_infinity_norm": norm,
                "maximum_possible_coordinate_separation": 2 * maximum_gap,
                "reason": (
                    "primitive line spacing exceeds the maximum Chebyshev "
                    "separation of this finite two-step walk"
                ),
            }
        included.append(n)
        n += 1
        if n > 100:
            raise AssertionError("template cutoff search failed to terminate")


def retain_line_point(retained, point, birth, identity, origin):
    sort_key = (birth, identity, point)
    item = (sort_key, point, identity, origin)
    for index, old in enumerate(retained):
        if old[1] == point:
            if sort_key < old[0]:
                retained[index] = item
                retained.sort(key=lambda value: value[0])
            return
    retained.append(item)
    retained.sort(key=lambda value: value[0])
    if len(retained) > 2:
        raise AssertionError(
            "requested line contains three distinct final-path points",
            [value[1] for value in retained],
        )


def chronological_template_scan(states, anchor_origins, template_name, started):
    spec = template_spec(template_name)
    results = []
    for level in LEVELS:
        state = states[level]
        position_by_gap = {
            gap: position for position, gap in enumerate(state["order"])
        }
        source_gaps = tuple(
            gap
            for gap, step in enumerate(state["parent_word"])
            if step == spec["source_step"]
        )
        possible, exclusion = possible_n_range(
            EXPECTED_POINT_COUNTS[level], spec["base_direction"]
        )
        for n in possible:
            direction = inverse_macro_direction(spec["base_direction"], n)
            relative_moment = spec["relative_moment"](direction)
            query_by_gap = {
                gap: add(cross(tuple(state["anchors"][gap]), direction), relative_moment)
                for gap in source_gaps
            }
            retained_by_moment = {moment: [] for moment in set(query_by_gap.values())}
            scanned = 0
            for point, birth, identity, origin in iter_placed_points(
                state, position_by_gap, anchor_origins[level], level
            ):
                scanned += 1
                moment = cross(point, direction)
                retained = retained_by_moment.get(moment)
                if retained is not None:
                    retain_line_point(retained, point, birth, identity, origin)
            if scanned != EXPECTED_POINT_COUNTS[level]:
                raise AssertionError("placed-point scan census drift", level, scanned)

            status_counts = Counter()
            live_birth_shells = Counter()
            live_moments = set()
            witnesses = []
            for gap in source_gaps:
                moment = query_by_gap[gap]
                endpoints = retained_by_moment[moment]
                stitch_position = position_by_gap[gap]
                if len(endpoints) < 2:
                    status_counts["fewer_than_two_final_points"] += 1
                    continue
                second_birth = endpoints[1][0][0]
                if second_birth >= stitch_position:
                    status_counts["secant_not_live_before_stitch"] += 1
                    continue
                status_counts["chronologically_live_secant"] += 1
                live_moments.add(moment)
                shell = pair_birth_shell(endpoints)
                live_birth_shells[shell] += 1
                if len(witnesses) < 5:
                    anchor = tuple(state["anchors"][gap])
                    assert all(
                        cross(subtract(item[1], anchor), direction) == relative_moment
                        for item in endpoints
                    )
                    witnesses.append({
                        "gap": gap,
                        "stitch_order_position": stitch_position,
                        "corridor_anchor": list(anchor),
                        "absolute_line_moment": list(moment),
                        "pair_birth_shell": shell,
                        "endpoints": [
                            endpoint_record(item, level, states) for item in endpoints
                        ],
                    })
            live_count = status_counts["chronologically_live_secant"]
            results.append({
                "template": template_name,
                "level": level,
                "address_shell_n": n,
                "primitive_direction": list(direction),
                "direction_infinity_norm": max(map(abs, direction)),
                "index_gap_lower_bound": (
                    max(map(abs, direction)) + 1
                ) // 2,
                "relative_line_description": spec["relative_line_description"],
                "relative_line_moment": list(relative_moment),
                "source_step_corridors": len(source_gaps),
                "distinct_absolute_query_lines": len(retained_by_moment),
                "placed_final_points_scanned": scanned,
                "status_counts": dict(sorted(status_counts.items())),
                "chronologically_live_secant_corridors": live_count,
                "chronologically_live_distinct_lines": len(live_moments),
                "live_pair_birth_shell_counts": dict(sorted(
                    live_birth_shells.items()
                )),
                "witnesses": witnesses,
            })
            enforce_runtime(started, f"{template_name} L{level} n={n}")
        results.append({
            "template": template_name,
            "level": level,
            "spacing_cutoff": exclusion,
            "included_address_shells": list(possible),
        })
    return results


def fraction_from_record(record):
    return Fraction(record["numerator"], record["denominator"])


def weighted_profiles(scans, action_statistics):
    profiles = {}
    for channel, actions in action_statistics.items():
        channel_result = {}
        for template_name in ("latent_L_n", "J_11_over_3"):
            if template_name == "latent_L_n":
                macro = actions["latent_L_n_macro"]
                theta = fraction_from_record(macro["theta_equals_a8_times_a16"])
                terminal = fraction_from_record(macro["r8"])
                terminal_name = "r8"
            else:
                macro = actions["J_11_over_3_macro"]
                theta = fraction_from_record(
                    macro["theta_equals_phase_A_times_phase_B"]
                )
                terminal = fraction_from_record(macro["incremental_reveal_fraction"])
                terminal_name = "incremental_reveal_fraction"
            rows = []
            total_incidence = Fraction()
            total_normalized = Fraction()
            by_birth_shell = defaultdict(Fraction)
            for item in scans:
                if item.get("template") != template_name or "address_shell_n" not in item:
                    continue
                n = item["address_shell_n"]
                weight = theta**n * terminal
                live = item["chronologically_live_secant_corridors"]
                source = item["source_step_corridors"]
                incidence = live * weight
                normalized = Fraction(live, source) * weight if source else Fraction()
                total_incidence += incidence
                total_normalized += normalized
                for shell, count in item["live_pair_birth_shell_counts"].items():
                    by_birth_shell[shell] += count * weight
                rows.append({
                    "level": item["level"],
                    "address_shell_n": n,
                    "b_live_corridor_incidences": live,
                    "source_corridors": source,
                    "theta_to_n_times_terminal": fraction_record(weight),
                    "weighted_incidence": fraction_record(incidence),
                    "weighted_live_fraction": fraction_record(normalized),
                    "birth_shell_counts": item["live_pair_birth_shell_counts"],
                })
            channel_result[template_name] = {
                "model": (
                    "independent uniform selection from the frozen accepted "
                    "whole-word set at each phase"
                ),
                "theta": fraction_record(theta),
                "terminal_factor_name": terminal_name,
                "terminal_factor": fraction_record(terminal),
                "rows_by_level_and_address_shell": rows,
                "diagnostic_sum_of_weighted_incidences": fraction_record(
                    total_incidence
                ),
                "diagnostic_sum_of_per_level_live_fractions": fraction_record(
                    total_normalized
                ),
                "weighted_incidence_split_by_pair_birth_shell": {
                    shell: fraction_record(value)
                    for shell, value in sorted(by_birth_shell.items())
                },
                "warning": (
                    "Rows can overlap in corridors and endpoint pairs; this is "
                    "not an exact killed-mask union or a probability bound."
                ),
            }
        profiles[channel] = channel_result
    return profiles


def cutoff_table():
    result = {}
    for name, base in (
        ("latent_L_n", LATENT_BASE_DIRECTION),
        ("J_11_over_3", J_BASE_DIRECTION),
    ):
        result[name] = {}
        for level in LEVELS:
            included, exclusion = possible_n_range(EXPECTED_POINT_COUNTS[level], base)
            result[name][str(level)] = {
                "included_n": list(included),
                "first_exclusion": exclusion,
            }
    expected = {
        "latent_L_n": {"5": 2, "6": 3, "7": 3, "8": 4},
        "J_11_over_3": {"5": 3, "6": 4, "7": 4, "8": 5},
    }
    observed = {
        family: {level: max(record["included_n"]) for level, record in levels.items()}
        for family, levels in result.items()
    }
    if observed != expected:
        raise AssertionError("spacing cutoff drift", expected, observed)
    return result


def lightweight_result(args, resources, mode):
    started = time.monotonic()
    validate_exact_constants()
    snapshots = pinned_snapshots(
        args.metadata, args.cache, args.actions, args.bitsets, pickles=False
    )
    _metadata, blocks = load_metadata(args.metadata)
    _actions, bitsets = load_target_bitsets(args.actions, args.bitsets)
    action_statistics = exact_action_statistics(blocks, args.cache, bitsets)
    for snapshot in snapshots.values():
        verify_snapshot_unchanged(snapshot)
    return {
        "status": "lightweight exact action/bound self-check passed",
        "mode": mode,
        "resource_policy": resources,
        "elapsed_seconds": time.monotonic() - started,
        "maximum_resident_bytes": maximum_resident_bytes(),
        "pinned_inputs": snapshots,
        "target_cache_words_scanned": sum(blocks[step]["words"] for step in TARGET_STEPS),
        "target_cache_bytes_scanned": sum(
            blocks[step]["end"] - blocks[step]["start"] for step in TARGET_STEPS
        ),
        "action_statistics": action_statistics,
        "finite_spacing_cutoffs": cutoff_table(),
        "full_run_plan": {
            "pickle_bytes": sum(
                EXPECTED_BYTES[f"gate2-l7-construction-L{level}.pkl"]
                for level in LEVELS
            ),
            "moment_scans": sum(
                len(possible_n_range(EXPECTED_POINT_COUNTS[level], base)[0])
                for base in (LATENT_BASE_DIRECTION, J_BASE_DIRECTION)
                for level in LEVELS
            ),
            "pair_enumeration": False,
            "hard_limits": "one process/thread, nice>=15, 115 seconds, 280 MiB",
        },
    }


def full_result(args, resources):
    started = time.monotonic()
    validate_exact_constants()
    snapshots = pinned_snapshots(
        args.metadata, args.cache, args.actions, args.bitsets, pickles=True
    )
    _metadata, blocks = load_metadata(args.metadata)
    actions_payload, bitsets = load_target_bitsets(args.actions, args.bitsets)
    action_statistics = exact_action_statistics(blocks, args.cache, bitsets)
    enforce_runtime(started, "action statistics")
    states = load_and_validate_states(snapshots)
    origins = build_anchor_origins(states)
    latent_scans = chronological_template_scan(
        states, origins, "latent_L_n", started
    )
    j_scans = chronological_template_scan(
        states, origins, "J_11_over_3", started
    )
    scans = latent_scans + j_scans
    weighted = weighted_profiles(scans, action_statistics)
    for snapshot in snapshots.values():
        verify_snapshot_unchanged(snapshot)
    checker = stable_snapshot(Path(__file__), "checker")
    elapsed = time.monotonic() - started
    enforce_runtime(started, "completed exact scan")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact finite known-template birth/action experiment; evidence only, "
            "not a far-secant theorem"
        ),
        "checker": checker,
        "resource_policy": resources,
        "elapsed_seconds": elapsed,
        "maximum_resident_bytes": maximum_resident_bytes(),
        "pinned_inputs": snapshots,
        "action_certificate_status": actions_payload["status"],
        "theorem_used_for_finite_cutoff": {
            "statement": (
                "In an N-point ordered walk with step infinity norm at most 2, "
                "a secant with canonical primitive direction g requires index "
                "gap at least ceil(||g||_infinity/2); hence ||g||_infinity "
                "is at most 2(N-1)."
            ),
            "finite_spacing_cutoffs": cutoff_table(),
        },
        "action_statistics": action_statistics,
        "chronological_line_incidence_scans": scans,
        "weighted_selected_orbit_diagnostics": weighted,
        "proved_by_this_finite_computation": [
            "the displayed a8, a16, r8 and auxiliary J-cycle coefficients are exact rational statistics of the pinned accepted-word bitsets",
            "every requested L5--L8 line incidence up to the exact primitive-spacing cutoff was tested by moment hashing without pair enumeration",
            "a secant is called live only when two distinct endpoints predate the stitch; endpoint identities and inherited construction birth levels are retained",
            "all deeper members of each displayed family are impossible as secants of that finite level's entire final walk by the index-gap bound",
        ],
        "not_proved": [
            "the uniform accepted-word model is not a reachable chronological policy and its coefficients are not transition probabilities in the safety game",
            "the two known direction families do not cover arbitrary far secants, old-new births, deep-deep pairs, or unrelated cursor imports",
            "weighted incidence rows overlap and are not an exact union of killed connector-word masks",
            "L5--L8 stabilization is finite evidence and does not imply a level-uniform summable birth envelope",
            "positive connector availability, an inductive safety invariant, and Erdos #193 remain open",
        ],
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "run"))
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--actions", default=DEFAULT_ACTIONS)
    parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()
    resources = resource_policy(True)
    if args.mode in ("estimate", "self-check"):
        payload = lightweight_result(args, resources, args.mode)
        print(json.dumps(payload, sort_keys=True, indent=2))
        return
    payload = full_result(args, resources)
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "status": payload["status"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_bytes": payload["maximum_resident_bytes"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
