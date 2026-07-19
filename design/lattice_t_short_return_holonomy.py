#!/usr/bin/env python3
"""Exact short-return affine-holonomy census for the lattice-T channels.

The lattice-T action artifact contains two per-word channels:

* ``zero_envelope`` (the strict channel used by the chronological pilot), and
* ``ordered_envelope`` (the larger common-order channel).

This checker keeps an accepted *whole word* atomic.  For a fixed start step
``s`` and middle step ``t`` it enumerates every correlated pair

    accepted word/slot at s with child t
        x accepted word/slot at t with child s.

No slot from one word is combined with the interiors of another word at the
same parent.  The cross product is an exact two-occurrence abstract action
pair; it is deliberately not called a chronologically reachable repetition.

For each return map it computes exact rational affine data, its fixed point,
and the homogeneous direction guard associated with every selected-word
interior reveal.  The merge also computes the guard spectrum over the full
candidate domains at both phases and emits a symbolic two-loop composition
witness whenever two return maps have different fixed points.

The guard calculation proves algebra only.  This checker does NOT test:

* all-depth silence of a line family,
* existence of an integer lattice line on a returned pencil,
* birth as a secant of a placed walk,
* chronological legality or repeatability, or
* connector availability after adding any guard.

Work is resumable by disjoint ``chunk`` ranges in the ordered list of first
role occurrences.  Run ``estimate`` to obtain the exact range sizes, run one
or more chunks, and merge an exact partition.  A middle step is independent,
so all length-two returns at one start step can later be covered by running
the 124 middle steps separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import resource
import struct
import sys
import tempfile
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_ACTIONS = Path("/tmp/nonx-lattice-envelope-action-probe.json")
DEFAULT_BITSETS = Path("/tmp/nonx-lattice-envelope-action-probe-bitsets.bin")
DEFAULT_OUTPUT = Path("/tmp/lattice-T-short-return-holonomy.json")

EXPECTED_INPUTS = {
    "metadata": {
        "sha256": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
        "bytes": 45_693,
    },
    "cache": {
        "sha256": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
        "bytes": 68_050_680,
    },
    "actions": {
        "sha256": "9ce2de5f7936349b4cc7e830dcf962f26164693dbf66da1ba3fcc9a1d73e2112",
        "bytes": 460_704,
    },
    "bitsets": {
        "sha256": "f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb",
        "bytes": 3_136_860,
    },
    "action_checker": {
        "sha256": "9056394f5529036f2e4515490de4940ca42d04165eae928c32f1b027aae36fed",
    },
}

CACHE_MAGIC = b"NOXLN001"
BITSET_MAGIC = b"NTACB001"
BITSET_SCHEMA = 1
MENU_SIZE = 124
EXPECTED_WORDS = 12_537_146
EXPECTED_SLOTS = 55_513_526
EXPECTED_CANDIDATES_8_16 = {8: 214, 16: 214}

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
I3 = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
)

MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)
if len(MENU) != MENU_SIZE:
    raise AssertionError("menu size drift")

CHANNELS = ("zero_envelope", "ordered_envelope")
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
MAX_WORK_SECONDS = 110.0
MAX_RESIDENT_BYTES = 280 * 1024 * 1024
FROZEN_CHUNK_CHECKER_SHA256 = (
    "01964e05dc8fd4334bfff325b6bfede034c7c9ee2ed1ac3c85259a0d3088e23c"
)


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


def snapshot(path):
    path = Path(path).resolve()
    stat = path.stat()
    return {
        "path": str(path),
        "bytes": stat.st_size,
        "sha256": file_sha256(path),
        "identity": [
            stat.st_dev,
            stat.st_ino,
            stat.st_size,
            stat.st_mtime_ns,
            stat.st_ctime_ns,
        ],
    }


def verify_unchanged(item):
    current = snapshot(item["path"])
    if current["identity"] != item["identity"] or current["sha256"] != item[
        "sha256"
    ]:
        raise RuntimeError("input changed during exact work", item["path"])


def pin_inputs(metadata_path, cache_path, actions_path, bitsets_path):
    paths = {
        "metadata": Path(metadata_path),
        "cache": Path(cache_path),
        "actions": Path(actions_path),
        "bitsets": Path(bitsets_path),
        "action_checker": ROOT / "design" / "nonx_scc_core_action_probe.py",
    }
    result = {name: snapshot(path) for name, path in paths.items()}
    for name, expected in EXPECTED_INPUTS.items():
        observed = result[name]
        if observed["sha256"] != expected["sha256"]:
            raise AssertionError("pinned input sha256 drift", name, observed)
        if "bytes" in expected and observed["bytes"] != expected["bytes"]:
            raise AssertionError("pinned input byte-count drift", name, observed)
    return result


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    process_nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and (
        process_nice >= 15
    )
    if enforce and not compliant:
        raise RuntimeError(
            "exact run requires thread controls=1 and process nice>=15",
            environment,
            process_nice,
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": process_nice,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


def enforce_runtime(started, label):
    elapsed = time.monotonic() - started
    resident = maximum_resident_bytes()
    if elapsed > MAX_WORK_SECONDS:
        raise RuntimeError("work-time gate exceeded", label, elapsed)
    if resident > MAX_RESIDENT_BYTES:
        raise MemoryError("resident-memory gate exceeded", label, resident)


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


def add_vectors(left, right):
    return tuple(a + b for a, b in zip(left, right))


def subtract_vectors(left, right):
    return tuple(a - b for a, b in zip(left, right))


def scale_vector(scalar, vector):
    return tuple(scalar * value for value in vector)


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def matrix_multiply(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def matrix_power(matrix, exponent):
    if exponent < 0:
        raise ValueError("negative matrix exponent")
    result = I3
    base = matrix
    power = exponent
    while power:
        if power & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        power >>= 1
    return result


def solve_linear(matrix, vector):
    rows = [
        [Fraction(value) for value in matrix[row]] + [Fraction(vector[row])]
        for row in range(3)
    ]
    for column in range(3):
        pivot = next(
            (row for row in range(column, 3) if rows[row][column]), None
        )
        if pivot is None:
            raise ValueError("singular exact matrix")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(3):
            if row == column:
                continue
            factor = rows[row][column]
            if factor:
                rows[row] = [
                    rows[row][index] - factor * rows[column][index]
                    for index in range(4)
                ]
    return tuple(rows[row][3] for row in range(3))


def inverse_matrix_vector(matrix, vector):
    return solve_linear(matrix, vector)


def fraction_record(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def fraction_vector_record(vector):
    return [fraction_record(value) for value in vector]


def fraction_vector_key(vector):
    return tuple((Fraction(value).numerator, Fraction(value).denominator) for value in vector)


def fraction_vector_from_key(key):
    return tuple(Fraction(numerator, denominator) for numerator, denominator in key)


def affine_from_controls(controls):
    """Return x -> A*x+t for sequential maps x -> M*(x-c)."""
    linear = I3
    translation = (0, 0, 0)
    for control in controls:
        linear = matrix_multiply(M, linear)
        translation = subtract_vectors(
            matrix_vector(M, translation), matrix_vector(M, control)
        )
    fixed = solve_linear(
        tuple(
            tuple(I3[row][column] - linear[row][column] for column in range(3))
            for row in range(3)
        ),
        translation,
    )
    if add_vectors(matrix_vector(linear, fixed), translation) != fixed:
        raise AssertionError("affine fixed-point solve drift")
    return {
        "length": len(controls),
        "linear": linear,
        "translation": translation,
        "b": scale_vector(-1, translation),
        "fixed_point": fixed,
    }


def compose_affine(outer, inner):
    """Return outer o inner for affine pairs (A,t)."""
    outer_a, outer_t = outer
    inner_a, inner_t = inner
    return (
        matrix_multiply(outer_a, inner_a),
        add_vectors(matrix_vector(outer_a, inner_t), outer_t),
    )


def affine_power(affine, exponent):
    if exponent < 0:
        raise ValueError("negative affine exponent")
    result = (I3, (0, 0, 0))
    base = affine
    power = exponent
    while power:
        if power & 1:
            result = compose_affine(base, result)
        base = compose_affine(base, base)
        power >>= 1
    return result


def affine_fixed_point(affine):
    linear, translation = affine
    return solve_linear(
        tuple(
            tuple(I3[row][column] - linear[row][column] for column in range(3))
            for row in range(3)
        ),
        translation,
    )


def primitive_integer_direction(vector):
    fractions = tuple(Fraction(value) for value in vector)
    common_denominator = 1
    for value in fractions:
        common_denominator = math.lcm(common_denominator, value.denominator)
    integers = [
        value.numerator * (common_denominator // value.denominator)
        for value in fractions
    ]
    divisor = 0
    for value in integers:
        divisor = math.gcd(divisor, abs(value))
    if not divisor:
        return None
    integers = [value // divisor for value in integers]
    first = next(value for value in integers if value)
    if first < 0:
        integers = [-value for value in integers]
    return tuple(integers)


def q_lateral(vector):
    _x, y, z = vector
    return 3 * y * y - y * z + 3 * z * z


def guard_from_direction(vector):
    primitive = primitive_integer_direction(vector)
    if primitive is None:
        return {
            "kind": "degenerate_reveal",
            "direction": None,
            "key": None,
        }
    x, _y, _z = primitive
    q_value = q_lateral(primitive)
    x_squared = x * x
    divisor = math.gcd(x_squared, q_value)
    if not divisor:
        raise AssertionError("nonzero direction produced zero guard coefficients")
    q_coefficient = x_squared // divisor
    r_squared_coefficient = q_value // divisor
    key = (q_coefficient, r_squared_coefficient)
    if key == (3, 11):
        classification = "F11"
    elif key == (275, 348):
        classification = "F348"
    elif r_squared_coefficient == 0:
        classification = "x_axis"
    elif q_coefficient == 0:
        classification = "lateral_plane"
    else:
        classification = "other"
    return {
        "kind": "direction_guard",
        "direction": primitive,
        "key": key,
        "classification": classification,
        "polynomial": (
            f"{q_coefficient}*(3*y^2-y*z+3*z^2)"
            f"-{r_squared_coefficient}*r^2"
        ),
    }


def pullback_site(control, site):
    return add_vectors(tuple(Fraction(value) for value in control), (
        inverse_matrix_vector(M, site)
    ))


def digest_integer_record(digest, values):
    for value in values:
        digest.update(int(value).to_bytes(8, "little", signed=True))


def digest_fraction_vector(digest, vector):
    for value in vector:
        value = Fraction(value)
        digest_integer_record(digest, (value.numerator, value.denominator))


def load_blocks(metadata_path):
    with Path(metadata_path).open() as handle:
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


def load_bitsets(actions_path, bitsets_path):
    with Path(actions_path).open() as handle:
        actions = json.load(handle)
    if actions["checker"]["sha256"] != EXPECTED_INPUTS["action_checker"][
        "sha256"
    ]:
        raise AssertionError("action checker commitment drift")
    metadata = actions["accepted_ordinal_bitset_sidecar"]
    bitsets_path = Path(bitsets_path).resolve()
    if metadata["sha256"] != EXPECTED_INPUTS["bitsets"]["sha256"] or (
        metadata["bytes"] != EXPECTED_INPUTS["bitsets"]["bytes"]
    ):
        raise AssertionError("action sidecar commitment drift")
    data = bitsets_path.read_bytes()
    if data[:len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("bitset magic drift")
    schema, block_count = struct.unpack_from("<II", data, len(BITSET_MAGIC))
    if schema != BITSET_SCHEMA or block_count != MENU_SIZE:
        raise AssertionError("bitset schema/count drift")
    result = {}
    cursor = len(BITSET_MAGIC) + 8
    zero_digest = hashlib.sha256()
    ordered_digest = hashlib.sha256()
    for expected in metadata["blocks"]:
        if cursor != expected["block_offset"]:
            raise AssertionError("bitset block offset drift", expected["step"])
        step, words, byte_count, zero_count, ordered_count = struct.unpack_from(
            "<IIIII", data, cursor
        )
        cursor += 20
        zero = data[cursor:cursor + byte_count]
        cursor += byte_count
        ordered = data[cursor:cursor + byte_count]
        cursor += byte_count
        if step != expected["step"] or words != expected["words"]:
            raise AssertionError("bitset block header drift", step)
        for channel, bits, count in (
            ("zero_envelope", zero, zero_count),
            ("ordered_envelope", ordered, ordered_count),
        ):
            commitment = expected[channel]
            if (
                len(bits) != commitment["bytes"]
                or hashlib.sha256(bits).hexdigest() != commitment["sha256"]
                or sum(value.bit_count() for value in bits) != count
                or count != commitment["set_bits"]
            ):
                raise AssertionError("bitset block commitment drift", step, channel)
        if any(zero[index] & ~ordered[index] for index in range(byte_count)):
            raise AssertionError("zero channel is not ordered subset", step)
        zero_digest.update(struct.pack("<II", step, byte_count))
        zero_digest.update(zero)
        ordered_digest.update(struct.pack("<II", step, byte_count))
        ordered_digest.update(ordered)
        result[step] = {
            "words": words,
            "zero_envelope": zero,
            "ordered_envelope": ordered,
            "zero_envelope_count": zero_count,
            "ordered_envelope_count": ordered_count,
        }
    if cursor != len(data):
        raise AssertionError("bitset sidecar trailing bytes")
    if zero_digest.hexdigest() != metadata[
        "zero_envelope_ordinal_bitsets_sha256"
    ] or ordered_digest.hexdigest() != metadata[
        "ordered_envelope_ordinal_bitsets_sha256"
    ]:
        raise AssertionError("aggregate bitset digest drift")
    return result


def accepted(bits, ordinal):
    index = ordinal - 1
    return bool(bits[index >> 3] & (1 << (index & 7)))


def word_record(ordinal, word):
    prefix = (0, 0, 0)
    prefixes = []
    interiors = []
    for position, child in enumerate(word):
        prefixes.append(prefix)
        prefix = add_vectors(prefix, MENU[child])
        if position + 1 < len(word):
            interiors.append(prefix)
    return {
        "ordinal_1_based": ordinal,
        "word": tuple(word),
        "prefixes": tuple(prefixes),
        "interiors": tuple(interiors),
        "endpoint": prefix,
    }


def load_step(cache_path, block, bits_by_channel):
    candidate_sites = set()
    records_by_channel = {channel: [] for channel in CHANNELS}
    word_digest = hashlib.sha256()
    with Path(cache_path).open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("cache magic drift")
            cursor = block["start"]
            observed_slots = 0
            endpoint = matrix_vector(M, MENU[block["step"]])
            for ordinal in range(1, block["words"] + 1):
                length = cache[cursor]
                cursor += 1
                word = tuple(cache[cursor:cursor + length])
                cursor += length
                if not 2 <= length <= 5 or len(word) != length:
                    raise AssertionError("invalid cached word", block["step"], ordinal)
                record = word_record(ordinal, word)
                if record["endpoint"] != endpoint:
                    raise AssertionError("cached word endpoint drift", block["step"], ordinal)
                candidate_sites.update(record["interiors"])
                digest_integer_record(
                    word_digest,
                    (block["step"], ordinal, length, *word),
                )
                for channel in CHANNELS:
                    if accepted(bits_by_channel[channel], ordinal):
                        records_by_channel[channel].append(record)
                observed_slots += length
            if cursor != block["end"] or observed_slots != block["word_slots"]:
                raise AssertionError("cache block boundary drift", block["step"])
        finally:
            cache.close()
    for channel in CHANNELS:
        expected = sum(value.bit_count() for value in bits_by_channel[channel])
        if len(records_by_channel[channel]) != expected:
            raise AssertionError("accepted word population drift", block["step"], channel)
    candidate_sites = tuple(sorted(candidate_sites))
    if block["step"] in EXPECTED_CANDIDATES_8_16 and len(candidate_sites) != (
        EXPECTED_CANDIDATES_8_16[block["step"]]
    ):
        raise AssertionError("known candidate count drift", block["step"])
    candidate_digest = hashlib.sha256()
    for site in candidate_sites:
        digest_integer_record(candidate_digest, (block["step"], *site))
    return {
        "step": block["step"],
        "candidate_sites": candidate_sites,
        "candidate_site_sha256": candidate_digest.hexdigest(),
        "word_stream_sha256": word_digest.hexdigest(),
        "records_by_channel": records_by_channel,
    }


def role_occurrences(records, target_step):
    result = []
    digest = hashlib.sha256()
    for record in records:
        for slot, child in enumerate(record["word"]):
            if child != target_step:
                continue
            item = {
                "ordinal_1_based": record["ordinal_1_based"],
                "word": record["word"],
                "interiors": record["interiors"],
                "slot_zero_based": slot,
                "control": record["prefixes"][slot],
            }
            result.append(item)
            digest_integer_record(
                digest,
                (
                    item["ordinal_1_based"],
                    item["slot_zero_based"],
                    *item["control"],
                    len(item["word"]),
                    *item["word"],
                ),
            )
    return tuple(result), digest.hexdigest()


def public_word_role(role):
    return {
        "ordinal_1_based": role["ordinal_1_based"],
        "word": list(role["word"]),
        "proper_interiors": [list(site) for site in role["interiors"]],
        "slot_zero_based": role["slot_zero_based"],
        "prefix_control": list(role["control"]),
    }


def role_reference(role):
    return {
        "ordinal_1_based": role["ordinal_1_based"],
        "slot_zero_based": role["slot_zero_based"],
    }


def public_affine(affine):
    return {
        "length": affine["length"],
        "linear": [list(row) for row in affine["linear"]],
        "translation": list(affine["translation"]),
        "b": list(affine["b"]),
        "fixed_point": fraction_vector_record(affine["fixed_point"]),
    }


def map_key(controls):
    return tuple(tuple(value) for value in controls)


def guard_key_text(key):
    if key is None:
        return "degenerate"
    return f"{key[0]}:{key[1]}"


def guard_accumulate(table, guard, multiplicity, sample):
    key = guard_key_text(guard["key"])
    record = table.get(key)
    if record is None:
        record = {
            "kind": guard["kind"],
            "classification": guard.get("classification"),
            "q_coefficient": None if guard["key"] is None else guard["key"][0],
            "r_squared_coefficient": (
                None if guard["key"] is None else guard["key"][1]
            ),
            "polynomial": guard.get("polynomial"),
            "occurrences": 0,
            "sample": sample,
        }
        table[key] = record
    record["occurrences"] += multiplicity


def load_scope(metadata_path, cache_path, actions_path, bitsets_path, start_step, middle_step):
    blocks = load_blocks(metadata_path)
    bitsets = load_bitsets(actions_path, bitsets_path)
    needed_steps = (start_step,) if start_step == middle_step else (
        start_step,
        middle_step,
    )
    loaded = {}
    for step in needed_steps:
        loaded[step] = load_step(
            cache_path,
            blocks[step],
            {
                channel: bitsets[step][channel]
                for channel in CHANNELS
            },
        )
    return loaded


def role_scope(loaded, start_step, middle_step, channel):
    first, first_digest = role_occurrences(
        loaded[start_step]["records_by_channel"][channel], middle_step
    )
    second, second_digest = role_occurrences(
        loaded[middle_step]["records_by_channel"][channel], start_step
    )
    return first, second, first_digest, second_digest


def selected_reveals(first_role, second_role):
    for site in first_role["interiors"]:
        yield "start_word", site, tuple(Fraction(value) for value in site)
    for site in second_role["interiors"]:
        yield "middle_word", site, pullback_site(first_role["control"], site)


def map_record_key(record):
    return tuple(tuple(control) for control in record["controls"])


def run_chunk(
    metadata_path,
    cache_path,
    actions_path,
    bitsets_path,
    channel,
    start_step,
    middle_step,
    first_role_index,
    last_role_index,
    output_path,
):
    if channel not in CHANNELS:
        raise ValueError("unknown channel", channel)
    started = time.monotonic()
    policy = resource_policy(enforce=True)
    pins = pin_inputs(metadata_path, cache_path, actions_path, bitsets_path)
    checker_before = snapshot(SELF)
    loaded = load_scope(
        metadata_path, cache_path, actions_path, bitsets_path, start_step, middle_step
    )
    first_roles, second_roles, first_digest, second_digest = role_scope(
        loaded, start_step, middle_step, channel
    )
    if not 0 <= first_role_index <= last_role_index <= len(first_roles):
        raise ValueError(
            "invalid first-role half-open range",
            first_role_index,
            last_role_index,
            len(first_roles),
        )

    pair_digest = hashlib.sha256()
    reveal_digest = hashlib.sha256()
    selected_guards = {}
    maps = {}
    fixed_cache = {}
    guard_cache = {}
    pair_count = 0
    reveal_count = 0

    for local_index, first_role in enumerate(
        first_roles[first_role_index:last_role_index], start=first_role_index
    ):
        for second_role in second_roles:
            pair_count += 1
            digest_integer_record(
                pair_digest,
                (
                    start_step,
                    middle_step,
                    first_role["ordinal_1_based"],
                    first_role["slot_zero_based"],
                    second_role["ordinal_1_based"],
                    second_role["slot_zero_based"],
                ),
            )
            controls = (first_role["control"], second_role["control"])
            key = map_key(controls)
            record = maps.get(key)
            if record is None:
                affine = affine_from_controls(controls)
                witness = {
                    "first": public_word_role(first_role),
                    "second": public_word_role(second_role),
                }
                record = {
                    "controls": [list(control) for control in controls],
                    "pair_multiplicity": 0,
                    "affine": public_affine(affine),
                    "minimum_actual_pair_witness": witness,
                }
                maps[key] = record
                fixed_cache[key] = affine["fixed_point"]
            record["pair_multiplicity"] += 1

            fixed = fixed_cache[key]
            for phase, original_site, adjusted_site in selected_reveals(
                first_role, second_role
            ):
                reveal_count += 1
                guard_cache_key = (key, fraction_vector_key(adjusted_site))
                guard = guard_cache.get(guard_cache_key)
                if guard is None:
                    direction = subtract_vectors(adjusted_site, fixed)
                    guard = guard_from_direction(direction)
                    guard_cache[guard_cache_key] = guard
                digest_integer_record(
                    reveal_digest,
                    (
                        first_role["ordinal_1_based"],
                        first_role["slot_zero_based"],
                        second_role["ordinal_1_based"],
                        second_role["slot_zero_based"],
                        0 if phase == "start_word" else 1,
                        *original_site,
                    ),
                )
                digest_fraction_vector(reveal_digest, adjusted_site)
                if guard["key"] is None:
                    digest_integer_record(reveal_digest, (-1, -1))
                else:
                    digest_integer_record(reveal_digest, guard["key"])
                sample = {
                    "phase": phase,
                    "original_candidate_site": list(original_site),
                    "phase_adjusted_reveal": fraction_vector_record(adjusted_site),
                    "fixed_point": record["affine"]["fixed_point"],
                    "primitive_reveal_direction": (
                        None if guard["direction"] is None else list(guard["direction"])
                    ),
                    "actual_pair_reference": {
                        "first": role_reference(first_role),
                        "second": role_reference(second_role),
                    },
                    "controls": [list(control) for control in controls],
                }
                guard_accumulate(selected_guards, guard, 1, sample)
        if (local_index - first_role_index + 1) % 16 == 0:
            enforce_runtime(started, "actual pair/reveal enumeration")

    expected_pairs = (last_role_index - first_role_index) * len(second_roles)
    if pair_count != expected_pairs:
        raise AssertionError("pair cross-product count drift")
    if sum(item["pair_multiplicity"] for item in maps.values()) != pair_count:
        raise AssertionError("map multiplicity partition drift")
    if sum(item["occurrences"] for item in selected_guards.values()) != reveal_count:
        raise AssertionError("selected reveal guard partition drift")

    for item in pins.values():
        verify_unchanged(item)
    verify_unchanged(checker_before)
    elapsed = time.monotonic() - started
    payload = {
        "schema_version": 1,
        "status": (
            "exact resumable chunk of accepted correlated two-role return pairs; "
            "not silence, integrality, reachability, or availability"
        ),
        "checker": {
            "path": str(SELF),
            "sha256": checker_before["sha256"],
            "unchanged_during_run": True,
        },
        "pinned_inputs": pins,
        "scope": {
            "channel": channel,
            "start_step": start_step,
            "middle_step": middle_step,
            "first_role_half_open_range": [first_role_index, last_role_index],
            "total_first_role_occurrences": len(first_roles),
            "total_second_role_occurrences": len(second_roles),
            "first_role_stream_sha256": first_digest,
            "second_role_stream_sha256": second_digest,
            "start_candidate_sites": len(loaded[start_step]["candidate_sites"]),
            "middle_candidate_sites": len(loaded[middle_step]["candidate_sites"]),
            "start_candidate_stream_sha256": loaded[start_step][
                "candidate_site_sha256"
            ],
            "middle_candidate_stream_sha256": loaded[middle_step][
                "candidate_site_sha256"
            ],
        },
        "actual_correlated_pair_stream": {
            "pairs": pair_count,
            "sha256": pair_digest.hexdigest(),
            "semantics": (
                "each record is one accepted whole-word/slot occurrence at the "
                "start crossed with one accepted whole-word/slot occurrence at "
                "the middle step; word ordinals are pinned by the cache sha256"
            ),
        },
        "actual_selected_word_reveals": {
            "reveals": reveal_count,
            "stream_sha256": reveal_digest.hexdigest(),
            "guard_spectrum": sorted(
                selected_guards.values(),
                key=lambda item: (
                    item["q_coefficient"] is None,
                    item["q_coefficient"] if item["q_coefficient"] is not None else -1,
                    item["r_squared_coefficient"] if item[
                        "r_squared_coefficient"
                    ] is not None else -1,
                ),
            ),
        },
        "return_maps": sorted(
            maps.values(), key=lambda item: tuple(map(tuple, item["controls"]))
        ),
        "resource_policy": policy,
        "elapsed_seconds": elapsed,
        "maximum_resident_bytes": maximum_resident_bytes(),
        "explicitly_not_checked": [
            "all-depth candidate-mask silence",
            "integer lattice-line existence or primitive moment integrality",
            "birth as a secant of a realized placed walk",
            "chronological legality or repeatability of the two actions",
            "connector availability after imposing a guard",
        ],
    }
    atomic_json_dump(payload, output_path)
    return {
        "output": str(Path(output_path).resolve()),
        "channel": channel,
        "start_step": start_step,
        "middle_step": middle_step,
        "first_role_half_open_range": [first_role_index, last_role_index],
        "pairs": pair_count,
        "selected_reveals": reveal_count,
        "return_maps": len(maps),
        "guard_polynomials": len(selected_guards),
        "elapsed_seconds": elapsed,
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def merge_guard_tables(destination, source):
    for item in source:
        key = (
            item["q_coefficient"],
            item["r_squared_coefficient"],
        )
        record = destination.get(key)
        if record is None:
            destination[key] = item
        else:
            record["occurrences"] += item["occurrences"]


def merge_map_tables(destination, source):
    for item in source:
        key = map_record_key(item)
        record = destination.get(key)
        if record is None:
            destination[key] = item
        else:
            if record["affine"] != item["affine"]:
                raise AssertionError("identical controls changed affine map", key)
            record["pair_multiplicity"] += item["pair_multiplicity"]
            old_witness = stable_hash(record["minimum_actual_pair_witness"])
            new_witness = stable_hash(item["minimum_actual_pair_witness"])
            if new_witness < old_witness:
                record["minimum_actual_pair_witness"] = item[
                    "minimum_actual_pair_witness"
                ]


def full_candidate_spectrum(map_records, start_candidates, middle_candidates):
    table = {}
    stream = hashlib.sha256()
    total_map_reveals = 0
    total_weighted_reveals = 0
    for map_record in sorted(map_records, key=map_record_key):
        controls = tuple(tuple(control) for control in map_record["controls"])
        fixed = tuple(
            Fraction(numerator, denominator)
            for numerator, denominator in map_record["affine"]["fixed_point"]
        )
        for phase, original_site, adjusted_site in (
            [("start_domain", site, tuple(Fraction(value) for value in site))
             for site in start_candidates]
            + [("middle_domain", site, pullback_site(controls[0], site))
               for site in middle_candidates]
        ):
            total_map_reveals += 1
            total_weighted_reveals += map_record["pair_multiplicity"]
            guard = guard_from_direction(subtract_vectors(adjusted_site, fixed))
            digest_integer_record(stream, (*controls[0], *controls[1]))
            digest_fraction_vector(stream, adjusted_site)
            if guard["key"] is None:
                digest_integer_record(stream, (-1, -1))
            else:
                digest_integer_record(stream, guard["key"])
            sample = {
                "phase": phase,
                "original_candidate_site": list(original_site),
                "phase_adjusted_reveal": fraction_vector_record(adjusted_site),
                "fixed_point": map_record["affine"]["fixed_point"],
                "primitive_reveal_direction": (
                    None if guard["direction"] is None else list(guard["direction"])
                ),
                "controls": map_record["controls"],
                "actual_pair_witness_is_in_return_map_record": True,
            }
            guard_accumulate(table, guard, map_record["pair_multiplicity"], sample)
    if sum(item["occurrences"] for item in table.values()) != total_weighted_reveals:
        raise AssertionError("full-candidate guard spectrum partition drift")
    return {
        "unique_map_reveals": total_map_reveals,
        "actual_pair_weighted_reveals": total_weighted_reveals,
        "stream_sha256": stream.hexdigest(),
        "guard_spectrum": sorted(
            table.values(),
            key=lambda item: (
                item["q_coefficient"] is None,
                item["q_coefficient"] if item["q_coefficient"] is not None else -1,
                item["r_squared_coefficient"] if item[
                    "r_squared_coefficient"
                ] is not None else -1,
            ),
        ),
    }


def direct_return_census(records, start_step, candidate_sites):
    roles, role_digest = role_occurrences(records, start_step)
    maps = {}
    stream = hashlib.sha256()
    for role in roles:
        digest_integer_record(
            stream,
            (role["ordinal_1_based"], role["slot_zero_based"], *role["control"]),
        )
        key = (role["control"],)
        record = maps.get(key)
        if record is None:
            affine = affine_from_controls(key)
            record = {
                "controls": [list(role["control"])],
                "pair_multiplicity": 0,
                "affine": public_affine(affine),
                "minimum_actual_pair_witness": {
                    "direct": public_word_role(role)
                },
            }
            maps[key] = record
        record["pair_multiplicity"] += 1
    table = {}
    for record in maps.values():
        fixed = tuple(
            Fraction(numerator, denominator)
            for numerator, denominator in record["affine"]["fixed_point"]
        )
        for site in candidate_sites:
            adjusted = tuple(Fraction(value) for value in site)
            guard = guard_from_direction(subtract_vectors(adjusted, fixed))
            sample = {
                "phase": "start_domain",
                "original_candidate_site": list(site),
                "phase_adjusted_reveal": fraction_vector_record(adjusted),
                "fixed_point": record["affine"]["fixed_point"],
                "primitive_reveal_direction": (
                    None if guard["direction"] is None else list(guard["direction"])
                ),
                "controls": record["controls"],
                "actual_word_witness_is_in_return_map_record": True,
            }
            guard_accumulate(table, guard, record["pair_multiplicity"], sample)
    return {
        "actual_direct_return_role_occurrences": len(roles),
        "role_stream_sha256": role_digest,
        "direct_return_stream_sha256": stream.hexdigest(),
        "unique_affine_maps": len(maps),
        "return_maps": sorted(maps.values(), key=map_record_key),
        "full_candidate_guard_spectrum": sorted(
            table.values(),
            key=lambda item: (
                item["q_coefficient"] is None,
                item["q_coefficient"] if item["q_coefficient"] is not None else -1,
                item["r_squared_coefficient"] if item[
                    "r_squared_coefficient"
                ] is not None else -1,
            ),
        ),
    }


def composition_witness(map_records, start_candidates):
    ordered = sorted(map_records, key=map_record_key)
    first = second = None
    for index, candidate in enumerate(ordered):
        candidate_fixed = tuple(
            Fraction(numerator, denominator)
            for numerator, denominator in candidate["affine"]["fixed_point"]
        )
        for other in ordered[index + 1:]:
            other_fixed = tuple(
                Fraction(numerator, denominator)
                for numerator, denominator in other["affine"]["fixed_point"]
            )
            if candidate_fixed != other_fixed:
                first, second = candidate, other
                break
        if first is not None:
            break
    if first is None:
        return {
            "available": False,
            "reason": "fewer than two distinct affine fixed points",
        }

    def affine_pair(record):
        return (
            tuple(tuple(value for value in row) for row in record["affine"]["linear"]),
            tuple(record["affine"]["translation"]),
        )

    u = affine_pair(first)
    v = affine_pair(second)
    p_u = tuple(
        Fraction(numerator, denominator)
        for numerator, denominator in first["affine"]["fixed_point"]
    )
    p_v = tuple(
        Fraction(numerator, denominator)
        for numerator, denominator in second["affine"]["fixed_point"]
    )
    length_u = first["affine"]["length"]
    length_v = second["affine"]["length"]
    m_length_v = matrix_power(M, length_v)
    formula_numerator = matrix_vector(
        tuple(
            tuple(I3[row][column] - m_length_v[row][column] for column in range(3))
            for row in range(3)
        ),
        subtract_vectors(p_v, p_u),
    )
    if formula_numerator == (0, 0, 0):
        raise AssertionError("distinct fixed points produced zero formula numerator")

    reveal = next(
        tuple(Fraction(value) for value in site)
        for site in start_candidates
        if tuple(Fraction(value) for value in site) not in (p_u, p_v)
    )
    samples = []
    fixed_keys = set()
    for exponent in (1, 2, 3):
        product = compose_affine(v, affine_power(u, exponent))
        fixed = affine_fixed_point(product)
        formula_matrix = matrix_power(M, length_v + length_u * exponent)
        formula_delta = solve_linear(
            tuple(
                tuple(I3[row][column] - formula_matrix[row][column] for column in range(3))
                for row in range(3)
            ),
            formula_numerator,
        )
        if add_vectors(p_u, formula_delta) != fixed:
            raise AssertionError("two-loop fixed-point identity drift", exponent)
        fixed_key = fraction_vector_key(fixed)
        if fixed_key in fixed_keys:
            raise AssertionError("two-loop sample fixed points not distinct")
        fixed_keys.add(fixed_key)
        guard = guard_from_direction(subtract_vectors(reveal, fixed))
        samples.append({
            "n": exponent,
            "word": "V o U^n",
            "total_control_length": length_v + length_u * exponent,
            "fixed_point": fraction_vector_record(fixed),
            "canonical_reveal": fraction_vector_record(reveal),
            "guard": {
                "classification": guard.get("classification"),
                "q_coefficient": None if guard["key"] is None else guard["key"][0],
                "r_squared_coefficient": (
                    None if guard["key"] is None else guard["key"][1]
                ),
                "polynomial": guard.get("polynomial"),
            },
        })
    return {
        "available": True,
        "U": first,
        "V": second,
        "exact_identity": (
            "p_(V o U^n)-p_U=(I-M^(len(V)+n*len(U)))^-1"
            "*(I-M^len(V))*(p_V-p_U)"
        ),
        "nonzero_formula_numerator": fraction_vector_record(formula_numerator),
        "distinctness_proof": (
            "if two exponents gave the same nonzero delta, subtraction would "
            "give M^k*(M^j-I)*delta=0; M is invertible and every eigenvalue "
            "of M^j has modulus 3^j, so M^j-I is invertible"
        ),
        "sample_products": samples,
        "scope_warning": (
            "this is an affine-semigroup witness in the per-step action channel; "
            "it does not prove U and V repeat at one chronological safety state"
        ),
    }


def merge_chunks(
    chunk_paths,
    metadata_path,
    cache_path,
    actions_path,
    bitsets_path,
    output_path,
):
    started = time.monotonic()
    policy = resource_policy(enforce=True)
    pins = pin_inputs(metadata_path, cache_path, actions_path, bitsets_path)
    checker_before = snapshot(SELF)
    chunk_snapshots = {}
    groups = {}
    for path in chunk_paths:
        path = Path(path).resolve()
        chunk_snapshot = snapshot(path)
        with path.open() as handle:
            payload = json.load(handle)
        if payload["checker"]["sha256"] != FROZEN_CHUNK_CHECKER_SHA256:
            raise AssertionError("chunk checker revision drift", path)
        for name, pin in pins.items():
            chunk_pin = payload["pinned_inputs"][name]
            if (chunk_pin["sha256"], chunk_pin["bytes"]) != (
                pin["sha256"], pin["bytes"]
            ):
                raise AssertionError("chunk input commitment drift", path, name)
        scope = payload["scope"]
        key = (scope["channel"], scope["start_step"], scope["middle_step"])
        groups.setdefault(key, []).append((
            path,
            tuple(scope["first_role_half_open_range"]),
        ))
        chunk_snapshots[path] = chunk_snapshot
        del payload
        enforce_runtime(started, "streaming chunk metadata validation")
    if not groups:
        raise ValueError("no chunks supplied")

    final_groups = {}
    loaded_cache = {}
    for key in sorted(groups):
        channel, start_step, middle_step = key
        ordered_chunks = sorted(groups[key], key=lambda item: item[1][0])
        with ordered_chunks[0][0].open() as handle:
            first_chunk = json.load(handle)
        total_first = first_chunk["scope"]["total_first_role_occurrences"]
        total_second = first_chunk["scope"]["total_second_role_occurrences"]
        del first_chunk
        expected_start = 0
        pair_count = 0
        reveal_count = 0
        maps = {}
        selected_guards = {}
        chunk_commitments = []
        for path, recorded_range in ordered_chunks:
            verify_unchanged(chunk_snapshots[path])
            with path.open() as handle:
                chunk = json.load(handle)
            scope = chunk["scope"]
            if (
                scope["total_first_role_occurrences"] != total_first
                or scope["total_second_role_occurrences"] != total_second
            ):
                raise AssertionError("chunk role census drift", path)
            first, last = scope["first_role_half_open_range"]
            if (first, last) != recorded_range:
                raise AssertionError("chunk scope changed between streaming passes", path)
            if first != expected_start:
                raise AssertionError("chunk ranges are not an exact partition", path)
            expected_start = last
            pair_count += chunk["actual_correlated_pair_stream"]["pairs"]
            reveal_count += chunk["actual_selected_word_reveals"]["reveals"]
            merge_map_tables(maps, chunk["return_maps"])
            merge_guard_tables(
                selected_guards,
                chunk["actual_selected_word_reveals"]["guard_spectrum"],
            )
            chunk_commitments.append({
                "path": str(path),
                "sha256": chunk_snapshots[path]["sha256"],
                "range": [first, last],
                "pair_stream_sha256": chunk[
                    "actual_correlated_pair_stream"
                ]["sha256"],
                "selected_reveal_stream_sha256": chunk[
                    "actual_selected_word_reveals"
                ]["stream_sha256"],
            })
            del chunk
            enforce_runtime(started, "streaming chunk aggregation")
        if expected_start != total_first:
            raise AssertionError("chunk partition does not cover all first roles", key)
        if pair_count != total_first * total_second:
            raise AssertionError("merged pair count is not exact cross product", key)
        if sum(item["pair_multiplicity"] for item in maps.values()) != pair_count:
            raise AssertionError("merged map multiplicity drift", key)
        if sum(item["occurrences"] for item in selected_guards.values()) != reveal_count:
            raise AssertionError("merged selected guard occurrence drift", key)

        scope_key = (start_step, middle_step)
        if scope_key not in loaded_cache:
            loaded_cache[scope_key] = load_scope(
                metadata_path,
                cache_path,
                actions_path,
                bitsets_path,
                start_step,
                middle_step,
            )
        loaded = loaded_cache[scope_key]
        map_records = sorted(maps.values(), key=map_record_key)
        full_spectrum = full_candidate_spectrum(
            map_records,
            loaded[start_step]["candidate_sites"],
            loaded[middle_step]["candidate_sites"],
        )
        enforce_runtime(started, "full candidate guard spectrum")
        final_groups[f"{channel}|{start_step}|{middle_step}"] = {
            "channel": channel,
            "start_step": start_step,
            "middle_step": middle_step,
            "actual_first_role_occurrences": total_first,
            "actual_second_role_occurrences": total_second,
            "actual_correlated_pairs": pair_count,
            "actual_selected_word_reveals": reveal_count,
            "unique_affine_return_maps": len(map_records),
            "distinct_affine_fixed_points": len({
                tuple(tuple(value) for value in record["affine"]["fixed_point"])
                for record in map_records
            }),
            "chunk_commitments": chunk_commitments,
            "selected_word_guard_spectrum": sorted(
                selected_guards.values(),
                key=lambda item: (
                    item["q_coefficient"] is None,
                    item["q_coefficient"] if item[
                        "q_coefficient"
                    ] is not None else -1,
                    item["r_squared_coefficient"] if item[
                        "r_squared_coefficient"
                    ] is not None else -1,
                ),
            ),
            "full_candidate_guard_spectrum": full_spectrum,
            "return_maps": map_records,
            "two_loop_composition_witness": composition_witness(
                map_records, loaded[start_step]["candidate_sites"]
            ),
        }

    start_steps = sorted({key[1] for key in groups})
    direct = {}
    for start_step in start_steps:
        load_key = next(key for key in loaded_cache if key[0] == start_step)
        loaded = loaded_cache[load_key]
        for channel in CHANNELS:
            direct[f"{channel}|{start_step}"] = direct_return_census(
                loaded[start_step]["records_by_channel"][channel],
                start_step,
                loaded[start_step]["candidate_sites"],
            )

    channels_and_starts = {(key[0], key[1]) for key in groups}
    coverage = {}
    for channel, start_step in sorted(channels_and_starts):
        middle_steps = sorted(
            key[2] for key in groups if key[0] == channel and key[1] == start_step
        )
        coverage[f"{channel}|{start_step}"] = {
            "completed_middle_steps": middle_steps,
            "all_124_middle_steps_completed": middle_steps == list(range(MENU_SIZE)),
            "length_one_direct_returns_included": True,
            "length_at_most_two_same_phase_census_complete": (
                middle_steps == list(range(MENU_SIZE))
            ),
        }

    for item in pins.values():
        verify_unchanged(item)
    for item in chunk_snapshots.values():
        verify_unchanged(item)
    verify_unchanged(checker_before)
    payload = {
        "schema_version": 1,
        "status": (
            "exact merged short-return affine-holonomy census; algebraic/action-"
            "channel result only, not silence, integrality, reachability, or availability"
        ),
        "checker": {
            "path": str(SELF),
            "sha256": checker_before["sha256"],
            "unchanged_during_merge": True,
            "frozen_chunk_checker_sha256": FROZEN_CHUNK_CHECKER_SHA256,
            "revision_note": (
                "the frozen chunk checker produced all exact pair chunks; this "
                "merge revision changes only streaming aggregation and hard-gate "
                "checks so the seven parsed chunk trees are never retained together"
            ),
        },
        "pinned_inputs": pins,
        "semantics": {
            "whole_word_correlation": (
                "each selected role retains its actual whole word, ordinal, slot, "
                "prefix control, and all proper interiors"
            ),
            "two_occurrence_cross_product": (
                "a pair joins one accepted whole-word role at the start occurrence "
                "to one accepted whole-word role at the middle occurrence"
            ),
            "guard_formula": (
                "for h=a-p, H_h(r,y,z)=h_x^2*(3*y^2-y*z+3*z^2)-"
                "(3*h_y^2-h_y*h_z+3*h_z^2)*r^2, reduced to primitive coefficients"
            ),
            "known_guards": {
                "F11": "3*(3*y^2-y*z+3*z^2)-11*r^2",
                "F348": "275*(3*y^2-y*z+3*z^2)-348*r^2",
                "x_axis": "3*y^2-y*z+3*z^2=0",
                "lateral_plane": "r=0",
            },
        },
        "coverage": coverage,
        "length_one_direct_returns": direct,
        "length_two_return_groups": final_groups,
        "resource_policy": policy,
        "elapsed_seconds": time.monotonic() - started,
        "maximum_resident_bytes": maximum_resident_bytes(),
        "proved": [
            "every reported pair uses two exact accepted whole-word/slot occurrences",
            "every affine map, rational fixed point, phase pullback, and guard coefficient is exact",
            "F11, F348, x-axis, lateral-plane, and other guards are distinguished without floating point",
            "the displayed two-loop fixed points satisfy the exact symbolic composition identity",
        ],
        "not_proved": [
            "all-depth silence for any reported direction family",
            "integer lattice-line existence or moment integrality",
            "birth as a secant in a reachable walk",
            "chronological legality, repeatability, or successor closure",
            "that a new abstract guard polynomial must be imposed by the realized policy",
            "positive connector availability or an unconditional theorem",
        ],
    }
    atomic_json_dump(payload, output_path)
    return {
        "output": str(Path(output_path).resolve()),
        "groups": len(final_groups),
        "coverage": coverage,
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_bytes": payload["maximum_resident_bytes"],
    }


def estimate_scope(
    metadata_path,
    cache_path,
    actions_path,
    bitsets_path,
    start_step,
    middle_step,
):
    pins = pin_inputs(metadata_path, cache_path, actions_path, bitsets_path)
    loaded = load_scope(
        metadata_path, cache_path, actions_path, bitsets_path, start_step, middle_step
    )
    channels = {}
    for channel in CHANNELS:
        first, second, first_digest, second_digest = role_scope(
            loaded, start_step, middle_step, channel
        )
        direct, direct_digest = role_occurrences(
            loaded[start_step]["records_by_channel"][channel], start_step
        )
        channels[channel] = {
            "accepted_start_words": len(
                loaded[start_step]["records_by_channel"][channel]
            ),
            "accepted_middle_words": len(
                loaded[middle_step]["records_by_channel"][channel]
            ),
            "first_role_occurrences": len(first),
            "second_role_occurrences": len(second),
            "exact_correlated_pairs": len(first) * len(second),
            "direct_length_one_role_occurrences": len(direct),
            "first_role_stream_sha256": first_digest,
            "second_role_stream_sha256": second_digest,
            "direct_role_stream_sha256": direct_digest,
            "suggested_outer_role_chunk": min(64, max(1, len(first))),
        }
    return {
        "status": "exact lightweight scope estimate",
        "pinned_inputs": {
            name: {key: value for key, value in item.items() if key != "identity"}
            for name, item in pins.items()
        },
        "start_step": start_step,
        "middle_step": middle_step,
        "candidate_sites": {
            str(start_step): len(loaded[start_step]["candidate_sites"]),
            str(middle_step): len(loaded[middle_step]["candidate_sites"]),
        },
        "channels": channels,
        "resumption": (
            "partition [0,first_role_occurrences) into disjoint half-open chunk ranges"
        ),
    }


def synthetic_self_check():
    latent = affine_from_controls(((-4, -4, -3), (0, 0, 0)))
    expected_fixed = (
        Fraction(-9, 2),
        Fraction(-39, 11),
        Fraction(-31, 11),
    )
    if latent["fixed_point"] != expected_fixed:
        raise AssertionError("latent fixed point regression")
    reveal = (Fraction(-2), Fraction(-2), Fraction(-2))
    latent_guard = guard_from_direction(subtract_vectors(reveal, expected_fixed))
    if latent_guard["key"] != (275, 348):
        raise AssertionError("F348 regression", latent_guard)
    cycle_guard = guard_from_direction((3, -1, 3))
    if cycle_guard["key"] != (3, 11):
        raise AssertionError("F11 regression", cycle_guard)
    if guard_from_direction((1, 0, 0))["classification"] != "x_axis":
        raise AssertionError("x-axis classification regression")
    if guard_from_direction((0, 1, 0))["classification"] != "lateral_plane":
        raise AssertionError("lateral-plane classification regression")

    u_data = affine_from_controls(((0, 0, 0),))
    v_data = affine_from_controls(((1, 0, 0),))
    u = (u_data["linear"], u_data["translation"])
    v = (v_data["linear"], v_data["translation"])
    if u_data["fixed_point"] == v_data["fixed_point"]:
        raise AssertionError("synthetic return maps should have distinct fixed points")
    sample = compose_affine(v, affine_power(u, 2))
    fixed = affine_fixed_point(sample)
    if add_vectors(matrix_vector(sample[0], fixed), sample[1]) != fixed:
        raise AssertionError("synthetic affine composition fixed point drift")

    test_word = word_record(1, (0, 1, 16))
    if test_word["prefixes"][2] != (-4, -4, -3):
        raise AssertionError("prefix-control reconstruction drift")
    return {
        "status": "passed",
        "latent_fixed_point": fraction_vector_record(expected_fixed),
        "latent_guard": latent_guard["polynomial"],
        "canonical_cycle_guard": cycle_guard["polynomial"],
        "whole_word_prefix_control": list(test_word["prefixes"][2]),
        "exact_fraction_arithmetic": True,
        "two_loop_composition": True,
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("self-check")

    estimate_parser = subparsers.add_parser("estimate")
    estimate_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    estimate_parser.add_argument("--cache", default=DEFAULT_CACHE)
    estimate_parser.add_argument("--actions", default=DEFAULT_ACTIONS)
    estimate_parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    estimate_parser.add_argument("--start-step", type=int, default=8)
    estimate_parser.add_argument("--middle-step", type=int, default=16)

    chunk_parser = subparsers.add_parser("chunk")
    chunk_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    chunk_parser.add_argument("--cache", default=DEFAULT_CACHE)
    chunk_parser.add_argument("--actions", default=DEFAULT_ACTIONS)
    chunk_parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    chunk_parser.add_argument("--channel", choices=CHANNELS, required=True)
    chunk_parser.add_argument("--start-step", type=int, default=8)
    chunk_parser.add_argument("--middle-step", type=int, default=16)
    chunk_parser.add_argument("--first-role-index", type=int, required=True)
    chunk_parser.add_argument("--last-role-index", type=int, required=True)
    chunk_parser.add_argument("--output", required=True)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--metadata", default=DEFAULT_METADATA)
    merge_parser.add_argument("--cache", default=DEFAULT_CACHE)
    merge_parser.add_argument("--actions", default=DEFAULT_ACTIONS)
    merge_parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    merge_parser.add_argument("--chunks", nargs="+", required=True)
    merge_parser.add_argument("--output", default=DEFAULT_OUTPUT)

    args = parser.parse_args()
    if args.mode == "self-check":
        result = synthetic_self_check()
    elif args.mode == "estimate":
        if not 0 <= args.start_step < MENU_SIZE or not 0 <= args.middle_step < MENU_SIZE:
            raise ValueError("step outside menu", args.start_step, args.middle_step)
        result = estimate_scope(
            args.metadata,
            args.cache,
            args.actions,
            args.bitsets,
            args.start_step,
            args.middle_step,
        )
    elif args.mode == "chunk":
        if not 0 <= args.start_step < MENU_SIZE or not 0 <= args.middle_step < MENU_SIZE:
            raise ValueError("step outside menu", args.start_step, args.middle_step)
        result = run_chunk(
            args.metadata,
            args.cache,
            args.actions,
            args.bitsets,
            args.channel,
            args.start_step,
            args.middle_step,
            args.first_role_index,
            args.last_role_index,
            args.output,
        )
    else:
        result = merge_chunks(
            args.chunks,
            args.metadata,
            args.cache,
            args.actions,
            args.bitsets,
            args.output,
        )
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
