#!/usr/bin/env python3
"""Exact quotient/address census for the no-new-x-line connector domains.

For the lateral block

    B = ((0, -3), (3, -1)),

the checker verifies the quotient coordinate q(y,z)=y-3z (mod 9), the
canonical carry decomposition

    (y,z) = B*c + (q,0),

and streams the pinned compact length-at-most-five connector cache.  It
records the exact finite role masks seen by the x-parallel projection.  A
role mask is the multiset of lateral prefix offsets of one connector word;
equivalently it is the multiset of its (carry,digit) pairs.

This is a projection-only checker.  It does not test non-x secants, connector
availability, reachability of arbitrary local occupancy patterns, or a
greatest safety fixed point.  Alternative words in one domain are actions;
they are never treated as simultaneously realized points.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_projection_coset_address.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/x_projection_coset_address.py run \
        --cache /tmp/no-new-x-line-domains.bin \
        --metadata /tmp/no-new-x-line-L5-canonical.json \
        --output /tmp/x-projection-coset-address-canonical.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import sys
import tempfile
from collections import Counter
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gate_run import MENU  # noqa: E402


B = ((0, -3), (3, -1))
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
CACHE_MAGIC = b"NOXLN001"
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_OUTPUT = Path("/tmp/x-projection-coset-address-canonical.json")

EXPECTED_INPUT_SHA256 = {
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
}
EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_METADATA_CHECKER_SHA256 = (
    "6eca827ef7b6a4dfad57554bb89156fff79c2f495e89ba33e166aebbba21fffd"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_STEPS = 124
EXPECTED_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
EXPECTED_PREFIX_OCCURRENCES = 42_976_380
EXPECTED_DISTINCT_PREFIX_OFFSETS = 217
EXPECTED_DISTINCT_CARRIES = 39
EXPECTED_ORDERED_SIGNATURES = 291_414
EXPECTED_ROLE_MASKS = 216_322
EXPECTED_MINIMUM_MASKS_PER_STEP = 201
EXPECTED_MAXIMUM_MASKS_PER_STEP = 8_059
EXPECTED_NONZERO_DIGIT_WORDS = 9_687_350
EXPECTED_DIGIT_SIMPLE_WORDS = 6_755_766
EXPECTED_SHARP_INTERACTION_RADIUS = 5
ANALYTIC_INTERACTION_RADIUS = 7
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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
        dir=path.parent, prefix=".x-projection-coset-", suffix=".json"
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


def apply_matrix(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def apply_b(vector):
    y, z = vector
    return -3 * z, 3 * y - z


def digit(vector):
    y, z = vector
    return (y - 3 * z) % 9


def carry(vector):
    y, z = vector
    residue = digit(vector)
    first_numerator = residue - y + 3 * z
    second_numerator = residue - y
    if first_numerator % 9 or second_numerator % 3:
        raise AssertionError("nonintegral quotient carry", vector, residue)
    result = first_numerator // 9, second_numerator // 3
    rebuilt = apply_b(result)
    if (rebuilt[0] + residue, rebuilt[1]) != vector:
        raise AssertionError("quotient carry roundtrip failed", vector, result)
    return result


def packed_signature(codes):
    # Four fixed nine-bit slots plus a three-bit length field.
    if len(codes) > 4:
        raise AssertionError("too many interior prefixes", len(codes))
    packed = len(codes)
    for position, code in enumerate(codes):
        if not 0 <= code < 289:
            raise AssertionError("prefix code out of range", code)
        packed |= (code + 1) << (3 + 9 * position)
    return packed


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and priority >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run requires thread variables equal to 1 and nice priority >= 15",
            environment,
            priority,
        )
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": priority,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "compliant": compliant,
    }


def verify_repository_inputs():
    observed = {}
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        digest = file_sha256(ROOT / relative)
        if digest != expected:
            raise AssertionError("pinned repository input drift", relative, digest)
        observed[relative] = digest
    if len(MENU) != EXPECTED_STEPS:
        raise AssertionError("menu size drift", len(MENU))
    return observed


def verify_algebra():
    if B[0][0] * B[1][1] - B[0][1] * B[1][0] != 9:
        raise AssertionError("lateral determinant drift")
    for vector in product(range(-20, 21), repeat=2):
        residue = digit(vector)
        coarse = carry(vector)
        if digit(apply_b(vector)) != 0:
            raise AssertionError("B image escaped quotient kernel", vector)
        if not 0 <= residue < 9:
            raise AssertionError("digit representative escaped range")
        if (apply_b(coarse)[0] + residue, apply_b(coarse)[1]) != vector:
            raise AssertionError("address decomposition failed", vector)
    image_residues = {digit((y, 0)) for y in range(9)}
    if image_residues != set(range(9)):
        raise AssertionError("quotient coordinate is not surjective")
    return {
        "matrix": [list(row) for row in B],
        "determinant": 9,
        "smith_normal_form": [1, 9],
        "quotient": "Z/9Z",
        "digit": "q(y,z)=y-3z mod 9, represented in {0,...,8}",
        "kernel_identity": "ker(q)=B Z^2",
        "carry": "c=((q-y+3z)/9,(q-y)/3)",
        "address_bijection": "(a,r) -> B a + (r,0)",
        "finite_box_roundtrip": "verified exactly on [-20,20]^2",
    }


def load_metadata(path):
    path = Path(path)
    digest = file_sha256(path)
    if digest != EXPECTED_METADATA_SHA256:
        raise AssertionError("pinned metadata drift", digest)
    with path.open() as handle:
        metadata = json.load(handle)
    if metadata["checker"]["sha256"] != EXPECTED_METADATA_CHECKER_SHA256:
        raise AssertionError("metadata checker commitment drift")
    cache_metadata = metadata["compact_domain_cache"]
    if cache_metadata["sha256"] != EXPECTED_CACHE_SHA256:
        raise AssertionError("metadata cache commitment drift")
    blocks = cache_metadata["blocks"]
    if len(blocks) != EXPECTED_STEPS:
        raise AssertionError("metadata block count drift", len(blocks))
    if {block["step"] for block in blocks} != set(range(EXPECTED_STEPS)):
        raise AssertionError("metadata step coverage drift")
    intervals = sorted((block["start"], block["end"]) for block in blocks)
    if intervals[0][0] != len(CACHE_MAGIC):
        raise AssertionError("metadata does not begin after cache magic")
    for first, second in zip(intervals, intervals[1:]):
        if first[1] != second[0]:
            raise AssertionError("metadata cache intervals are not contiguous")
    if intervals[-1][1] != EXPECTED_CACHE_BYTES:
        raise AssertionError("metadata cache extent drift")
    return digest, cache_metadata, sorted(blocks, key=lambda item: item["step"])


def scan_cache(cache_path, blocks):
    cache_path = Path(cache_path)
    if cache_path.stat().st_size != EXPECTED_CACHE_BYTES:
        raise AssertionError("compact cache byte count drift")
    cache_digest = file_sha256(cache_path)
    if cache_digest != EXPECTED_CACHE_SHA256:
        raise AssertionError("compact cache digest drift", cache_digest)

    all_offsets = set()
    first_projections = set()
    length_histogram = Counter()
    step_records = []
    role_digest = hashlib.sha256()
    total_words = 0
    total_slots = 0
    total_nonzero = 0
    total_digit_simple = 0
    total_lateral_simple = 0

    with cache_path.open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for block in blocks:
                step = block["step"]
                cursor = block["start"]
                endpoint = apply_matrix(M_BAL3, MENU[step])
                ordered_signatures = set()
                role_masks = set()
                step_length_histogram = Counter()
                block_role_bytes = bytearray()
                step_words = 0
                step_slots = 0
                step_nonzero = 0
                step_digit_simple = 0
                step_lateral_simple = 0

                while cursor < block["end"]:
                    length = cache[cursor]
                    cursor += 1
                    if not 2 <= length <= 5:
                        raise AssertionError("connector length drift", step, length)
                    word_end = cursor + length
                    if word_end > block["end"]:
                        raise AssertionError("truncated connector word", step)

                    x = y = z = 0
                    codes = []
                    digit_bits = 0
                    repeated_digit = False
                    repeated_lateral = False
                    for position in range(length):
                        menu_index = cache[cursor + position]
                        if menu_index >= len(MENU):
                            raise AssertionError("menu index escaped range")
                        dx, dy, dz = MENU[menu_index]
                        x += dx
                        y += dy
                        z += dz
                        if position < length - 1:
                            if not (-8 <= y <= 8 and -8 <= z <= 8):
                                raise AssertionError(
                                    "length-five prefix escaped proved square",
                                    (y, z),
                                )
                            offset = y, z
                            code = (y + 8) * 17 + (z + 8)
                            repeated_lateral = repeated_lateral or code in codes
                            codes.append(code)
                            residue = (y - 3 * z) % 9
                            bit = 1 << residue
                            repeated_digit = repeated_digit or bool(digit_bits & bit)
                            digit_bits |= bit
                            all_offsets.add(offset)
                            if position == 0:
                                first_projections.add(offset)
                    cursor = word_end
                    point = x, y, z
                    if point != endpoint:
                        raise AssertionError(
                            "connector endpoint drift", step, step_words, point, endpoint
                        )

                    ordered = packed_signature(codes)
                    mask = packed_signature(sorted(codes))
                    ordered_signatures.add(ordered)
                    role_masks.add(mask)
                    block_role_bytes.append(step)
                    block_role_bytes.append(length)
                    block_role_bytes.extend(ordered.to_bytes(5, "little"))

                    nonzero = not bool(digit_bits & 1)
                    digit_simple = nonzero and not repeated_digit
                    lateral_simple = not repeated_lateral
                    step_nonzero += int(nonzero)
                    step_digit_simple += int(digit_simple)
                    step_lateral_simple += int(lateral_simple)
                    total_nonzero += int(nonzero)
                    total_digit_simple += int(digit_simple)
                    total_lateral_simple += int(lateral_simple)
                    step_words += 1
                    step_slots += length
                    total_words += 1
                    total_slots += length
                    step_length_histogram[length] += 1
                    length_histogram[length] += 1

                if cursor != block["end"]:
                    raise AssertionError("cache block endpoint drift", step)
                role_digest.update(block_role_bytes)
                if step_words != block["words"] or step_slots != block["word_slots"]:
                    raise AssertionError("metadata/cache census mismatch", step)
                if step_digit_simple == 0:
                    raise AssertionError("step has no digit-simple word", step)
                step_records.append({
                    "step": step,
                    "parent_step": list(MENU[step]),
                    "words": step_words,
                    "word_slots": step_slots,
                    "word_length_histogram": {
                        str(key): value
                        for key, value in sorted(step_length_histogram.items())
                    },
                    "ordered_lateral_prefix_signatures": len(ordered_signatures),
                    "unordered_projection_role_masks": len(role_masks),
                    "all_prefix_digits_nonzero_words": step_nonzero,
                    "digit_simple_words": step_digit_simple,
                    "lateral_simple_words": step_lateral_simple,
                })
        finally:
            cache.close()

    if total_words != EXPECTED_WORDS:
        raise AssertionError("effective word count drift", total_words)
    if total_slots != EXPECTED_WORD_SLOTS:
        raise AssertionError("word-slot count drift", total_slots)
    if total_slots - total_words != EXPECTED_PREFIX_OCCURRENCES:
        raise AssertionError("prefix occurrence count drift")
    if len(all_offsets) != EXPECTED_DISTINCT_PREFIX_OFFSETS:
        raise AssertionError("distinct prefix-offset count drift", len(all_offsets))
    carries_by_digit = {residue: set() for residue in range(9)}
    for offset in all_offsets:
        carries_by_digit[digit(offset)].add(carry(offset))
    all_carries = set().union(*carries_by_digit.values())
    if len(all_carries) != EXPECTED_DISTINCT_CARRIES:
        raise AssertionError("distinct carry count drift", len(all_carries))
    if set(residue for residue, values in carries_by_digit.items() if values) != set(range(9)):
        raise AssertionError("not all quotient digits occur")
    ordered_total = sum(
        record["ordered_lateral_prefix_signatures"] for record in step_records
    )
    masks_total = sum(
        record["unordered_projection_role_masks"] for record in step_records
    )
    mask_counts = [
        record["unordered_projection_role_masks"] for record in step_records
    ]
    if ordered_total != EXPECTED_ORDERED_SIGNATURES:
        raise AssertionError("ordered signature count drift", ordered_total)
    if masks_total != EXPECTED_ROLE_MASKS:
        raise AssertionError("role-mask count drift", masks_total)
    if min(mask_counts) != EXPECTED_MINIMUM_MASKS_PER_STEP:
        raise AssertionError("minimum role-mask count drift", min(mask_counts))
    if max(mask_counts) != EXPECTED_MAXIMUM_MASKS_PER_STEP:
        raise AssertionError("maximum role-mask count drift", max(mask_counts))
    if total_nonzero != EXPECTED_NONZERO_DIGIT_WORDS:
        raise AssertionError("nonzero-digit word count drift", total_nonzero)
    if total_digit_simple != EXPECTED_DIGIT_SIMPLE_WORDS:
        raise AssertionError("digit-simple word count drift", total_digit_simple)

    same_digit_radius = 0
    for values in carries_by_digit.values():
        for first in values:
            for second in values:
                same_digit_radius = max(
                    same_digit_radius,
                    abs(first[0] - second[0]),
                    abs(first[1] - second[1]),
                )
    if same_digit_radius != EXPECTED_SHARP_INTERACTION_RADIUS:
        raise AssertionError("sharp interaction radius drift", same_digit_radius)

    expected_cage = set(product(range(-2, 3), repeat=2))
    menu_projections = {(vector[1], vector[2]) for vector in MENU}
    if first_projections != expected_cage or menu_projections != expected_cage:
        raise AssertionError("first-prefix cage projection drift")

    offset_stream = [list(offset) for offset in sorted(all_offsets)]
    carry_stream = {
        str(residue): [list(value) for value in sorted(carries_by_digit[residue])]
        for residue in range(9)
    }
    return {
        "cache_sha256": cache_digest,
        "effective_words": total_words,
        "word_slots": total_slots,
        "interior_prefix_occurrences": total_slots - total_words,
        "word_length_histogram": {
            str(key): value for key, value in sorted(length_histogram.items())
        },
        "distinct_lateral_prefix_offsets": len(all_offsets),
        "distinct_carries": len(all_carries),
        "digits_present": list(range(9)),
        "step_specific_ordered_lateral_prefix_signatures": ordered_total,
        "step_specific_unordered_projection_role_masks": masks_total,
        "minimum_role_masks_per_step": min(mask_counts),
        "maximum_role_masks_per_step": max(mask_counts),
        "all_prefix_digits_nonzero_words": total_nonzero,
        "digit_simple_words": total_digit_simple,
        "lateral_simple_words": total_lateral_simple,
        "steps_with_a_digit_simple_word": sum(
            record["digit_simple_words"] > 0 for record in step_records
        ),
        "analytic_same_digit_interaction_radius": ANALYTIC_INTERACTION_RADIUS,
        "pinned_cache_sharp_same_digit_interaction_radius": same_digit_radius,
        "first_prefix_lateral_projections": len(first_projections),
        "offset_stream_sha256": stable_hash(offset_stream),
        "carries_by_digit_sha256": stable_hash(carry_stream),
        "role_occurrence_stream_sha256": role_digest.hexdigest(),
        "step_census_sha256": stable_hash(step_records),
        "steps": step_records,
    }


def estimate_payload(policy, repository_inputs, algebra):
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "estimate only; no metadata or compact cache opened",
        "checker": {
            "path": "design/x_projection_coset_address.py",
            "sha256": file_sha256(Path(__file__)),
        },
        "repository_inputs": repository_inputs,
        "resource_policy": policy,
        "algebra": algebra,
        "expected_run": {
            "cache_bytes": EXPECTED_CACHE_BYTES,
            "words": EXPECTED_WORDS,
            "word_slots": EXPECTED_WORD_SLOTS,
            "single_streaming_process": True,
            "ordinary_python_sets_are_released_after_each_step_block": True,
            "resource_bound": "intended for less than 2 minutes and 300 MiB",
        },
    }


def run_payload(args, policy, repository_inputs, algebra):
    metadata_digest, cache_metadata, blocks = load_metadata(args.metadata)
    census = scan_cache(args.cache, blocks)
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact finite quotient/address and pinned connector-mask census; "
            "projection-only, not availability or an unconditional theorem"
        ),
        "checker": {
            "path": "design/x_projection_coset_address.py",
            "sha256": file_sha256(Path(__file__)),
        },
        "repository_inputs": repository_inputs,
        "pinned_artifacts": {
            "metadata_path": str(Path(args.metadata)),
            "metadata_sha256": metadata_digest,
            "metadata_checker_sha256": EXPECTED_METADATA_CHECKER_SHA256,
            "cache_path": str(Path(args.cache)),
            "cache_bytes": EXPECTED_CACHE_BYTES,
            "cache_sha256": census.pop("cache_sha256"),
            "block_metadata_sha256": cache_metadata["block_metadata_sha256"],
        },
        "resource_policy": policy,
        "algebra": algebra,
        "exact_cache_census": census,
        "projection_locality": {
            "address_of_child_interior": (
                "for parent lateral gap start a and prefix u, "
                "address=(a+c(u),q(u))"
            ),
            "collision_criterion": "two child yz coordinates agree iff their addresses agree",
            "analytic_radius_proof": (
                "same digit gives delta_c=((-delta_y+3*delta_z)/9,"
                "-delta_y/3); prefix coordinates lie in [-8,8], hence "
                "||delta_c||_infinity<=7"
            ),
            "analytic_radius": ANALYTIC_INTERACTION_RADIUS,
            "pinned_cache_sharp_radius": EXPECTED_SHARP_INTERACTION_RADIUS,
            "parent_fibre_multiplicity_two_neighbor_cap_at_radius_7": 450,
            "realized_choice_semantics": (
                "one selected role mask is translated at each gap; unchosen "
                "alternative masks are actions, not simultaneous points"
            ),
        },
        "static_25_fibre_cage": {
            "lateral_offsets": "[-2,2]^2",
            "fibres": 25,
            "central_fibre_already_contains_start_anchor": True,
            "additional_fibres_in_this_sufficient_cage": 24,
            "effect": (
                "every length-at-least-two connector has a first interior in "
                "one of these fibres, so every word is projection-killed"
            ),
            "triple_free_lift": (
                "a finite point set with one point per cage fibre can be made "
                "triple-free by choosing integer x coordinates successively "
                "outside finitely many forbidden values"
            ),
            "reachability_caveat": (
                "not proved reachable as a contiguous ordered MENU walk or "
                "under the no-new-x selector"
            ),
        },
        "proved": [
            "Z^2/BZ^2 is cyclic of order 9 with quotient q(y,z)=y-3z mod 9",
            "the carry/digit address is exact and unique",
            (
                "x-projection conflicts of length-at-most-five connectors are "
                "parent-local within analytic radius 7"
            ),
            "the named pinned-cache counts and sharp radius are exact finite computations",
            (
                "the 25-fibre cage refutes availability from triple-freeness "
                "plus fibre multiplicity alone"
            ),
        ],
        "not_proved": [
            "reachability of the static cage in the ordered construction",
            "positive connector availability in every reachable state",
            "a finite global online strategy or greatest safety fixed point",
            "control of non-x-parallel local or far secants",
            "an unconditional theorem for Erdos problem 193",
        ],
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-test", "run"))
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()
    policy = resource_policy(enforce=args.mode == "run")
    repository_inputs = verify_repository_inputs()
    algebra = verify_algebra()
    if args.mode == "estimate":
        payload = estimate_payload(policy, repository_inputs, algebra)
    elif args.mode == "self-test":
        payload = {
            "schema_version": 1,
            "date": "2026-07-18",
            "status": "algebra and structural cage self-test passed; cache not opened",
            "checker": {
                "path": "design/x_projection_coset_address.py",
                "sha256": file_sha256(Path(__file__)),
            },
            "repository_inputs": repository_inputs,
            "resource_policy": policy,
            "algebra": algebra,
            "menu_lateral_projections": len({(v[1], v[2]) for v in MENU}),
        }
        if payload["menu_lateral_projections"] != 25:
            raise AssertionError("MENU does not induce the 25-fibre cage")
    else:
        payload = run_payload(args, policy, repository_inputs, algebra)
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "mode": args.mode,
        "output": str(Path(args.output)),
        "bytes": Path(args.output).stat().st_size,
        "sha256": file_sha256(args.output),
        "status": payload["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
