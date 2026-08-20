#!/usr/bin/env python3
"""Direct positive-mask backstop for the canonical L9 age-2 precursor.

The main precursor's two pre-registered direct word backstops happened to be
zero-effect corridors.  This independent checker targets the positive record
at L9 gap 138809 (step 120).  It reconstructs the authoritative effective
step-120 domain and all 311,738 initial L9 anchors, then scans every raw word
directly.  It does not construct or use the main checker's site/line atoms.

For each word it tests the four tagged-endpoint channels literally:

* collision with a source tagged endpoint;
* a source tagged endpoint on a line through two distinct word interiors;
* a word interior on a secant through two tagged anchors; and
* a word interior on a secant through a source endpoint and any other anchor.

The resulting four bitsets and their union must equal decoded fixed-length
payloads from the pinned canonical precursor artifact.  Every payload
referenced by the target record is also decoded and checked for byte length,
SHA-256, padding, and popcount consistency.

The exact scan is deliberately held behind ``run``.  A lightweight estimate
validates pins and target metadata without loading either domain pickle:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/l9_anchor_age2_positive_mask_verifier.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/l9_anchor_age2_positive_mask_verifier.py run \
        --output /tmp/l9-anchor-age2-positive-mask-verifier.json
"""

from __future__ import annotations

import argparse
import base64
import gc
import hashlib
import json
import math
import os
import pickle
import sys
import tempfile
import time
import zlib
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_CHECKER = ROOT / "design/l9_anchor_age2_precursor.py"
DEFAULT_CANONICAL = Path("/tmp/l9-anchor-age2-precursor-canonical.json")

EXPECTED_MAIN_CHECKER_SHA256 = (
    "66f776e7ae4eff4c35d004d870d82458582a4c2b6516f20257149a08e5535b90"
)
EXPECTED_CANONICAL_SHA256 = (
    "961f9e5f0772d9df508ab0aefaa7405e3cc21637d59560cdda95c4edf61d809f"
)
EXPECTED_CANONICAL_BYTES = 3_312_472

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
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
}

M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MENU = tuple(
    (x, y, z)
    for x, y, z in product(range(-2, 3), repeat=3)
    if (x, y, z) != (0, 0, 0)
)
IDX = {step: index for index, step in enumerate(MENU)}
FRAGILE_CUT = 2_000

TARGET_GAP = 138_809
TARGET_STEP = 120
TARGET_SOURCE_GAP = 13_171
TARGET_L8_GAP = 41_265
TARGET_L7_PARENT_GAP = 12_324
TARGET_SLOT = 2
TARGET_DOMAIN_WORDS = 501_044
TARGET_KILLED_WORDS = 113_998
TARGET_UNION_SHA256 = (
    "9340a4cba9d0608b66b611d4f009d2ed45ab49c873d49c621cee12b534fb5afd"
)
TARGET_ZERO_SHA256 = (
    "1ce4436ba04def21268ffe0e6e7d4afd3d2bafd8a3c5a4663e694157c2af1909"
)
TARGET_START = (-68_496, -42_582, 95_420)
TARGET_END = (-68_490, -42_579, 95_427)
TARGET_SELECTED_L8_WORD = (120, 119, 120)
TARGET_SOURCE_ENDPOINTS = (
    "connector:L7:G12291:I1",
    "connector:L7:G12324:I2",
)
CHANNELS = (
    "collision",
    "endpoint-old-new-new",
    "tagged-tagged-old-old",
    "tagged-other-anchor-old-old",
)
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


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


def apply(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def sub(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive(vector):
    divisor = math.gcd(
        math.gcd(abs(vector[0]), abs(vector[1])), abs(vector[2])
    )
    if divisor == 0:
        return None
    result = tuple(coordinate // divisor for coordinate in vector)
    for coordinate in result:
        if coordinate < 0:
            return tuple(-value for value in result)
        if coordinate > 0:
            return result
    raise AssertionError("nonzero primitive direction lost its sign")


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "all thread-cap environment variables must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("cannot verify process nice level on this platform")
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 15:
        raise RuntimeError(
            f"run under `nice -n 15`; observed process nice value is {priority}"
        )
    return {"processes": 1, "thread_cap": 1, "nice": priority}


def target_record(canonical):
    records = canonical["exact_corridor_masks"]["records"]
    matches = [record for record in records if record["l9_gap"] == TARGET_GAP]
    assert len(matches) == 1
    record = matches[0]
    assert record["schema"] == "realized-L9-descendant-corridor-v1"
    assert record["source_gap"] == TARGET_SOURCE_GAP
    assert record["l8_gap"] == TARGET_L8_GAP
    assert record["l7_parent_gap"] == TARGET_L7_PARENT_GAP
    assert record["actual_l8_connector_step_slot_zero_based"] == TARGET_SLOT
    assert tuple(record["actual_selected_l8_connector_word"]) == (
        TARGET_SELECTED_L8_WORD
    )
    assert record["step"] == TARGET_STEP
    assert record["domain_words"] == TARGET_DOMAIN_WORDS
    assert tuple(record["l9_corridor_start"]) == TARGET_START
    assert tuple(record["l9_corridor_end"]) == TARGET_END
    assert tuple(record["source_tagged_endpoint_stable_ids"]) == (
        TARGET_SOURCE_ENDPOINTS
    )
    assert record["selected_l9_connector_word"] is None
    union = record["exact_tagged_age2_anchor_component_mask"]
    assert union["killed_words"] == TARGET_KILLED_WORDS
    assert union["mask_sha256"] == TARGET_UNION_SHA256
    channels = record["exact_overlapping_channel_masks"]
    assert set(channels) == set(CHANNELS)
    assert channels["tagged-other-anchor-old-old"] == union
    for channel in CHANNELS[:-1]:
        assert channels[channel]["killed_words"] == 0
        assert channels[channel]["mask_sha256"] == TARGET_ZERO_SHA256
    return record


def validate_pins(canonical_path):
    canonical_path = canonical_path.resolve()
    observed_inputs = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_inputs == EXPECTED_INPUT_SHA256
    assert file_sha256(MAIN_CHECKER) == EXPECTED_MAIN_CHECKER_SHA256
    assert canonical_path.stat().st_size == EXPECTED_CANONICAL_BYTES
    assert file_sha256(canonical_path) == EXPECTED_CANONICAL_SHA256
    canonical = json.loads(canonical_path.read_text())
    assert canonical["checker_sha256"] == EXPECTED_MAIN_CHECKER_SHA256
    for name, digest in EXPECTED_INPUT_SHA256.items():
        if name in canonical["input_sha256"]:
            assert canonical["input_sha256"][name] == digest
    record = target_record(canonical)
    return canonical, record, observed_inputs


def decode_mask_record(mask, payloads, cache):
    domain_words = mask["domain_words"]
    digest = mask["mask_sha256"]
    reference = mask["exact_payload_ref"]
    assert reference == f"{domain_words}:{digest}"
    if reference not in cache:
        payload = payloads[reference]
        assert payload["domain_words"] == domain_words
        raw_size = (domain_words + 7) // 8
        assert payload["uncompressed_bytes"] == raw_size
        compressed = base64.b64decode(payload["payload_base64"], validate=True)
        assert len(compressed) == payload["zlib_bytes"]
        raw = zlib.decompress(compressed)
        assert len(raw) == raw_size
        assert hashlib.sha256(raw).hexdigest() == digest
        bits = int.from_bytes(raw, "little")
        assert bits >> domain_words == 0
        cache[reference] = bits
    bits = cache[reference]
    assert bits.bit_count() == mask["killed_words"]
    return bits


def validate_all_target_payloads(record, canonical):
    payloads = canonical["exact_mask_store"]["payloads"]
    cache = {}
    mask_records = []

    def visit(value):
        if isinstance(value, dict):
            if "exact_payload_ref" in value:
                assert {
                    "domain_words", "killed_words", "mask_sha256",
                    "exact_payload_ref",
                } <= set(value)
                mask_records.append(value)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(record)
    for mask in mask_records:
        decode_mask_record(mask, payloads, cache)
    return cache, {
        "mask_records_decoded": len(mask_records),
        "unique_payloads_decoded": len(cache),
        "payload_reference_stream_sha256": hashlib.sha256(stable_bytes(sorted(
            cache
        ))).hexdigest(),
    }


def load_step_domain():
    with (ROOT / "connector_domains4.pkl").open("rb") as handle:
        base = pickle.load(handle)
    assert tuple(map(tuple, base["menu"])) == MENU
    assert set(base["domains"]) == set(range(len(MENU)))
    base_sizes = {
        int(step): len(words) for step, words in base["domains"].items()
    }
    base_words = sorted(base["domains"][TARGET_STEP], key=len)
    del base
    gc.collect()

    fragile_steps = {
        step for step, size in base_sizes.items() if size < FRAGILE_CUT
    }
    assert TARGET_STEP in fragile_steps
    with (ROOT / "dstar5_fragile.pkl").open("rb") as handle:
        d5 = pickle.load(handle)
    step_by_vector = {tuple(vector): IDX[tuple(vector)] for vector in d5}
    assert set(step_by_vector.values()) == fragile_steps
    raw_words = d5.pop(MENU[TARGET_STEP])
    del d5
    gc.collect()
    if not isinstance(raw_words, list):
        raw_words = list(raw_words)
    for index, word in enumerate(raw_words):
        raw_words[index] = tuple(IDX[tuple(vector)] for vector in word)
    domain = base_words + raw_words
    del base_words, raw_words
    assert len(domain) == TARGET_DOMAIN_WORDS
    return domain, {
        "base_D2_D4_words": base_sizes[TARGET_STEP],
        "appended_D5_words": TARGET_DOMAIN_WORDS - base_sizes[TARGET_STEP],
        "effective_domain_words": len(domain),
        "ordering": (
            "stable length sort of pinned D2-D4 words followed by pinned D5 "
            "words converted in artifact order"
        ),
    }


def load_initial_l9_anchors(canonical, record):
    viz = json.loads((ROOT / "viz/walk3d-data.json").read_text())
    points8 = [tuple(point) for point in viz["levels"][8]["points"]]
    del viz
    anchors = [apply(M_BAL3, point) for point in points8]
    del points8
    assert len(anchors) == 311_738
    assert len(set(anchors)) == len(anchors)
    assert anchors[TARGET_GAP] == TARGET_START
    assert anchors[TARGET_GAP + 1] == TARGET_END
    assert sub(TARGET_END, TARGET_START) == apply(
        M_BAL3, MENU[TARGET_STEP]
    )

    endpoint_profiles = {
        profile["stable_id"]: profile
        for profile in canonical["anchor_skeleton"]["tagged_endpoint_profiles"]
    }
    assert set(endpoint_profiles) == {
        "connector:L7:G12291:I1",
        "connector:L7:G12324:I2",
        "connector:L7:G19950:I2",
    }
    tagged_indexes = set()
    for stable_id, profile in endpoint_profiles.items():
        index = profile["l8_path_index_and_l9_anchor_index"]
        assert anchors[index] == tuple(profile["l9_coordinate"])
        assert profile["birth_level"] == 7
        assert profile["age_at_l9"] == 2
        tagged_indexes.add(index)
    source_endpoints = {
        stable_id: tuple(endpoint_profiles[stable_id]["l9_coordinate"])
        for stable_id in record["source_tagged_endpoint_stable_ids"]
    }
    return anchors, source_endpoints, tagged_indexes


def build_direction_indexes(anchors, source_endpoints, canonical):
    expected_summaries = {
        record["tagged_endpoint_stable_id"]: record
        for record in canonical["direction_indexes"]
    }
    indexes = {}
    summaries = []
    for stable_id in TARGET_SOURCE_ENDPOINTS:
        endpoint = source_endpoints[stable_id]
        index = {}
        endpoint_index = None
        for partner_index, partner in enumerate(anchors):
            if partner == endpoint:
                assert endpoint_index is None
                endpoint_index = partner_index
                continue
            direction = primitive(sub(partner, endpoint))
            assert direction is not None
            assert direction not in index, (
                "three inherited anchors collinear through source endpoint",
                stable_id, direction, index.get(direction), partner_index,
            )
            index[direction] = partner_index
        assert endpoint_index is not None
        assert len(index) == len(anchors) - 1
        digest = hashlib.sha256()
        for direction, partner_index in sorted(index.items()):
            digest.update(stable_bytes((
                direction, partner_index, anchors[partner_index]
            )))
            digest.update(b"\n")
        summary = expected_summaries[stable_id]
        assert summary["directions"] == len(index)
        assert summary["endpoint_cutoff"] is None
        assert summary["distance_cutoff"] is None
        assert summary["direction_index_sha256"] == digest.hexdigest()
        indexes[stable_id] = index
        summaries.append({
            "tagged_endpoint_stable_id": stable_id,
            "endpoint_anchor_index": endpoint_index,
            "directions": len(index),
            "direction_index_sha256": digest.hexdigest(),
        })
    return indexes, summaries


def direct_raw_word_masks(domain, anchors, source_endpoints, tagged_indexes,
                          direction_indexes):
    bits = {channel: 0 for channel in CHANNELS}
    start = anchors[TARGET_GAP]
    end = anchors[TARGET_GAP + 1]
    for word_index, word in enumerate(domain):
        position = start
        candidates = []
        for ordinal, menu_index in enumerate(word):
            assert 0 <= menu_index < len(MENU)
            position = add(position, MENU[menu_index])
            if ordinal + 1 < len(word):
                candidates.append(position)
        assert position == end
        assert len({start, *candidates, end}) == len(candidates) + 2

        present = set()
        for stable_id in TARGET_SOURCE_ENDPOINTS:
            endpoint = source_endpoints[stable_id]
            if endpoint in candidates:
                present.add("collision")

            for left, first in enumerate(candidates):
                if first == endpoint:
                    continue
                for second in candidates[left + 1:]:
                    if second == endpoint:
                        continue
                    assert first != second
                    if cross(
                        sub(first, endpoint), sub(second, endpoint)
                    ) == (0, 0, 0):
                        present.add("endpoint-old-new-new")

            direction_index = direction_indexes[stable_id]
            for candidate in candidates:
                if candidate == endpoint:
                    continue
                direction = primitive(sub(candidate, endpoint))
                assert direction is not None
                partner_index = direction_index.get(direction)
                if partner_index is None:
                    continue
                partner = anchors[partner_index]
                if partner == candidate:
                    # Collision with a non-source anchor is outside this tagged
                    # source component.  A source-endpoint collision was caught
                    # above when that endpoint was iterated.
                    continue
                assert len({endpoint, partner, candidate}) == 3
                assert cross(
                    sub(partner, endpoint), sub(candidate, endpoint)
                ) == (0, 0, 0)
                present.add(
                    "tagged-tagged-old-old"
                    if partner_index in tagged_indexes
                    else "tagged-other-anchor-old-old"
                )

        flag = 1 << word_index
        for channel in present:
            bits[channel] |= flag
    return bits


def mask_profile(bits, domain_words):
    raw = bits.to_bytes((domain_words + 7) // 8, "little")
    return {
        "domain_words": domain_words,
        "killed_words": bits.bit_count(),
        "mask_sha256": hashlib.sha256(raw).hexdigest(),
    }


def estimate_result(canonical_path, resource_policy):
    canonical, record, observed_inputs = validate_pins(canonical_path)
    payload_references = set()

    def visit(value):
        if isinstance(value, dict):
            if "exact_payload_ref" in value:
                payload_references.add(value["exact_payload_ref"])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(record)
    return {
        "status": (
            "pinned positive-mask verifier estimate only; no domain pickle, "
            "initial-anchor list, direction index, payload, or raw word scanned"
        ),
        "resource_policy": resource_policy,
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "pinned_main_checker_sha256": EXPECTED_MAIN_CHECKER_SHA256,
        "pinned_canonical": {
            "path": str(canonical_path.resolve()),
            "bytes": EXPECTED_CANONICAL_BYTES,
            "sha256": EXPECTED_CANONICAL_SHA256,
        },
        "input_sha256": observed_inputs,
        "target": {
            "l9_gap": TARGET_GAP,
            "step": TARGET_STEP,
            "source_gap": TARGET_SOURCE_GAP,
            "domain_words": TARGET_DOMAIN_WORDS,
            "canonical_union_killed_words": TARGET_KILLED_WORDS,
            "canonical_union_mask_sha256": TARGET_UNION_SHA256,
            "source_tagged_endpoints": len(TARGET_SOURCE_ENDPOINTS),
            "initial_l9_anchors": canonical["anchor_skeleton"][
                "complete_initial_l9_anchors"
            ],
            "maximum_candidate_interiors_per_raw_word": 4,
            "maximum_candidate_interior_pairs_per_raw_word": 6,
            "referenced_canonical_payloads": len(payload_references),
        },
        "planned_exact_run": {
            "raw_domain_words": TARGET_DOMAIN_WORDS,
            "all_four_channels_per_word": True,
            "atom_composition_used": False,
            "direction_index_entries": (
                len(TARGET_SOURCE_ENDPOINTS)
                * (canonical["anchor_skeleton"]["complete_initial_l9_anchors"] - 1)
            ),
            "decode_every_payload_referenced_by_target_record": True,
            "assert_channel_and_union_bitset_equality": True,
        },
        "scope": (
            "one positive canonical corridor backstop; not a second precursor "
            "census, L9 legality computation, or availability result"
        ),
    }


def run_result(canonical_path, resource_policy):
    started = time.time()
    canonical, record, observed_inputs = validate_pins(canonical_path)
    decoded, decode_summary = validate_all_target_payloads(record, canonical)
    domain, domain_summary = load_step_domain()
    anchors, source_endpoints, tagged_indexes = load_initial_l9_anchors(
        canonical, record
    )
    direction_indexes, direction_summaries = build_direction_indexes(
        anchors, source_endpoints, canonical
    )
    direct_bits = direct_raw_word_masks(
        domain, anchors, source_endpoints, tagged_indexes, direction_indexes
    )

    canonical_channel_bits = {
        channel: decode_mask_record(
            record["exact_overlapping_channel_masks"][channel],
            canonical["exact_mask_store"]["payloads"], decoded,
        )
        for channel in CHANNELS
    }
    assert direct_bits == canonical_channel_bits
    direct_union = 0
    for channel in CHANNELS:
        direct_union |= direct_bits[channel]
    canonical_union = decode_mask_record(
        record["exact_tagged_age2_anchor_component_mask"],
        canonical["exact_mask_store"]["payloads"], decoded,
    )
    assert direct_union == canonical_union
    assert direct_union.bit_count() == TARGET_KILLED_WORDS
    direct_union_profile = mask_profile(direct_union, len(domain))
    assert direct_union_profile["mask_sha256"] == TARGET_UNION_SHA256
    direct_channel_profiles = {
        channel: mask_profile(direct_bits[channel], len(domain))
        for channel in CHANNELS
    }
    assert direct_channel_profiles["tagged-other-anchor-old-old"] == (
        direct_union_profile
    )
    for channel in CHANNELS[:-1]:
        assert direct_channel_profiles[channel]["killed_words"] == 0
        assert direct_channel_profiles[channel]["mask_sha256"] == (
            TARGET_ZERO_SHA256
        )

    return {
        "status": (
            "exact direct raw-word positive-mask verification passed for pinned "
            "L9 gap 138809; no atom composition used"
        ),
        "resource_policy": {
            **resource_policy,
            "elapsed_seconds": round(time.time() - started, 3),
        },
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "pinned_main_checker_sha256": EXPECTED_MAIN_CHECKER_SHA256,
        "pinned_canonical": {
            "path": str(canonical_path.resolve()),
            "bytes": EXPECTED_CANONICAL_BYTES,
            "sha256": EXPECTED_CANONICAL_SHA256,
        },
        "input_sha256": observed_inputs,
        "target": {
            "l9_gap": TARGET_GAP,
            "step": TARGET_STEP,
            "source_gap": TARGET_SOURCE_GAP,
            "l8_gap": TARGET_L8_GAP,
            "domain": domain_summary,
            "source_tagged_endpoint_stable_ids": list(TARGET_SOURCE_ENDPOINTS),
        },
        "initial_l9_anchor_reconstruction": {
            "anchors": len(anchors),
            "source_direction_indexes": direction_summaries,
            "endpoint_cutoff": None,
            "distance_cutoff": None,
        },
        "canonical_payload_reconstruction": decode_summary,
        "direct_raw_word_geometry": {
            "raw_words_scanned": len(domain),
            "atom_composition_used": False,
            "three_distinct_point_assertions_active": True,
            "channel_masks": direct_channel_profiles,
            "union_mask": direct_union_profile,
            "channel_bitsets_equal_decoded_canonical_payloads": True,
            "union_bitset_equals_decoded_canonical_payload": True,
        },
        "scope": (
            "one positive tagged age-2 initial-anchor component mask; not full "
            "L9 poison, legality, connector availability, or a theorem"
        ),
    }


def atomic_write_json(output, result):
    output = output.resolve()
    if not output.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {output.parent}")
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(payload), file_sha256(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument(
        "--canonical", type=Path, default=DEFAULT_CANONICAL
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("/tmp/l9-anchor-age2-positive-mask-verifier.json"),
    )
    arguments = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; verifier assertions must remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resource_policy = enforce_resource_policy()
    if arguments.mode == "estimate":
        result = estimate_result(arguments.canonical, resource_policy)
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    result = run_result(arguments.canonical, resource_policy)
    byte_count, output_hash = atomic_write_json(arguments.output, result)
    print(json.dumps({
        "output": str(arguments.output.resolve()),
        "bytes": byte_count,
        "sha256": output_hash,
        "verified_gap": TARGET_GAP,
        "direct_union_killed_words": TARGET_KILLED_WORDS,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
