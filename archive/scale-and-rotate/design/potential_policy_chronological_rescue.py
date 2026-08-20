#!/usr/bin/env python3
"""Resumable exact L5 rescue under the common height-two non-x potential.

The accepted-ordinal sidecar is produced by
``nonx_potential_compatible_word_probe.py``.  At each pinned chronological
stitch this checker scans cache order and selects the first word satisfying:

1. its exact accepted-ordinal bit is set (all induced degenerate non-x edges
   strictly descend the common height-two potential);
2. every proper interior uses a globally empty, mutually distinct (y,z)
   fibre in the current placed state; and
3. the word is exactly legal against the complete current placed state.

A pending cache cursor is sealed into the checkpoint, so a single domain scan
can continue across 120-second chunks without losing firstness.  This checker
uses the potential-only channel.  The stricter digit-simple channel is neither
required nor consulted.

The potential-result hashes below intentionally remain PENDING until the
resumable exact producer and merger have emitted their final artifacts.  Run
and probe modes refuse to start while any pin is pending.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import os
import pickle
import resource
import struct
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, word_interiors, word_legal  # noqa: E402
from design.fixed_policy_chronological_replay import (  # noqa: E402
    first_collision,
    first_new_new_new,
    first_old_new_new,
    first_old_old_new,
)


DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_POTENTIAL = Path("/tmp/nonx-potential-compatible-word-probe.json")
DEFAULT_BITSETS = Path(
    "/tmp/nonx-potential-compatible-word-probe-bitsets.bin"
)
DEFAULT_CHECKPOINT = Path("/tmp/potential-policy-L5-checkpoint.json")
DEFAULT_PROBE_OUTPUT = Path("/tmp/potential-policy-L5-gap2-probe.json")

EXPECTED_INPUT_SHA256 = {
    "metadata": "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a",
    "cache": "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7",
    "L5_state": "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
    "fast_legal": "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed",
    "gate_run": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "amplify193": "f9950c4d8db2507478002841568dc0b6fef883eb0597d90db7971f87e4302ef0",
    "potential_summary": "de736b10b18051e61ca2060f09c8819a847a1979210d5b9c39ad2239557257ec",
    "fixed_replay_witness_core": "474a525fce7291b00d9c8cd669fd960af742cd0109899b820ae65e2ffe341595",
}
EXPECTED_POTENTIAL_CHECKER_SHA256 = (
    "21b84e6ef80c1b8184cb3c06f08d674983f10cd91759b204e1170186319b1062"
)
EXPECTED_POTENTIAL_RESULT_SHA256 = (
    "f4e809f611fc0fd18a511f95d982c8a6f5d2a2936c2d9014c3f30ef622c9b080"
)
EXPECTED_BITSET_SHA256 = (
    "dfe3d0b758663219ef2db7c205be15716927cfa91a6391f41b389335c40680e7"
)
EXPECTED_BITSET_BYTES = 3_136_860
EXPECTED_SELECTED_EDGE_SHA256 = (
    "0d42fc09d958fce8a2a9ed2fe02ae4f2cca3f3c3549c68a8bc3e5835780b70a8"
)
EXPECTED_RANK_SHA256 = (
    "79a83e18f61a95c81e24a7493e9175c034fb06719f19fa8172fa041477295056"
)
EXPECTED_STEPS = 124
EXPECTED_GAPS = 2_457
EXPECTED_ANCHORS = 2_458
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_SCHEDULE_SHA256 = (
    "031e4dc1ed31fba2ff930036dd0b1f81bb516d3d4c98818def6d9085179b4422"
)
EXPECTED_ANCHOR_STREAM_SHA256 = (
    "1baf7b206cc3cf59d41cf1b27cd29af6a5e36ad79d71bf602aa6ef87c598646a"
)
EXPECTED_PARENT_WORD_SHA256 = (
    "316c30558d05ab75ac4c556b8c985f1dce638025d75af287772eae903f531952"
)
BITSET_MAGIC = b"NPOTB001"
CACHE_MAGIC = b"NOXLN001"
SCHEMA_VERSION = 1
MAX_SECONDS = 120.0
MAX_WORK_SECONDS = 115.0
MAX_RESIDENT_BYTES = 300 * 1024 * 1024
CHECKPOINT_INTERVAL = 50
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


class DeadlineReached(Exception):
    def __init__(self, pending):
        super().__init__(pending)
        self.pending = pending


class NoSurvivor(Exception):
    def __init__(self, details):
        super().__init__(details)
        self.details = details


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


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce=True):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and nice >= 15
    if enforce and not compliant:
        raise RuntimeError("run requires thread controls=1 and nice>=15")
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": nice,
        "maximum_seconds": MAX_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


def enforce_runtime(deadline, phase):
    if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
        raise MemoryError("300-MiB resident limit exceeded", phase)
    return time.monotonic() >= deadline


def atomic_json_dump(value, path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
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


def ensure_final_pins():
    pending = {
        "potential_checker": EXPECTED_POTENTIAL_CHECKER_SHA256,
        "potential_result": EXPECTED_POTENTIAL_RESULT_SHA256,
        "bitset": EXPECTED_BITSET_SHA256,
    }
    if any(value == "PENDING" for value in pending.values()) or not (
        EXPECTED_BITSET_BYTES > 0
    ):
        raise RuntimeError("potential-filter artifacts are not pinned", pending)


def verify_inputs(metadata_path, cache_path, potential_path, bitset_path):
    ensure_final_pins()
    paths = {
        "metadata": Path(metadata_path),
        "cache": Path(cache_path),
        "L5_state": ROOT / "gate2-l7-construction-L5.pkl",
        "fast_legal": ROOT / "fast_legal.py",
        "gate_run": ROOT / "gate_run.py",
        "amplify193": ROOT / "amplify193.py",
        "potential_summary": (
            ROOT / "design" / "nonx-potential-compatible-word-probe-summary.json"
        ),
        "fixed_replay_witness_core": (
            ROOT / "design" / "fixed_policy_chronological_replay.py"
        ),
    }
    observed = {key: file_sha256(path) for key, path in paths.items()}
    if observed != EXPECTED_INPUT_SHA256:
        raise AssertionError("pinned input drift", EXPECTED_INPUT_SHA256, observed)
    if Path(cache_path).stat().st_size != EXPECTED_CACHE_BYTES:
        raise AssertionError("compact cache byte count drift")
    extra = {
        "potential_checker": file_sha256(
            ROOT / "design" / "nonx_potential_compatible_word_probe.py"
        ),
        "potential_result": file_sha256(potential_path),
        "bitset": file_sha256(bitset_path),
    }
    expected_extra = {
        "potential_checker": EXPECTED_POTENTIAL_CHECKER_SHA256,
        "potential_result": EXPECTED_POTENTIAL_RESULT_SHA256,
        "bitset": EXPECTED_BITSET_SHA256,
    }
    if extra != expected_extra:
        raise AssertionError("potential artifact drift", expected_extra, extra)
    if Path(bitset_path).stat().st_size != EXPECTED_BITSET_BYTES:
        raise AssertionError("potential bitset byte count drift")
    return {**observed, **extra}


def load_metadata(path):
    with Path(path).open() as handle:
        metadata = json.load(handle)
    blocks = {
        record["step"]: record
        for record in metadata["compact_domain_cache"]["blocks"]
    }
    if set(blocks) != set(range(EXPECTED_STEPS)):
        raise AssertionError("cache block set drift")
    return metadata, blocks


def load_l5_state():
    with (ROOT / "gate2-l7-construction-L5.pkl").open("rb") as handle:
        state = pickle.load(handle)
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    schedule = tuple(state["order"])
    if len(parent_word) != EXPECTED_GAPS or len(anchors) != EXPECTED_ANCHORS:
        raise AssertionError("pinned L5 size drift")
    if sorted(schedule) != list(range(EXPECTED_GAPS)):
        raise AssertionError("pinned L5 schedule is not a permutation")
    if stable_hash(schedule) != EXPECTED_SCHEDULE_SHA256:
        raise AssertionError("pinned schedule digest drift")
    if stable_hash(anchors) != EXPECTED_ANCHOR_STREAM_SHA256:
        raise AssertionError("pinned anchor digest drift")
    if hashlib.sha256(bytes(parent_word)).hexdigest() != (
        EXPECTED_PARENT_WORD_SHA256
    ):
        raise AssertionError("pinned parent-word digest drift")
    return parent_word, anchors, schedule


def load_potential_result(path):
    with Path(path).open() as handle:
        result = json.load(handle)
    if result["checker"]["sha256"] != EXPECTED_POTENTIAL_CHECKER_SHA256:
        raise AssertionError("potential result/checker mismatch")
    rank = result["selected_policy_rank_reconstruction"]
    if rank["edge_stream_sha256"] != EXPECTED_SELECTED_EDGE_SHA256 or (
        rank["rank_stream_sha256"] != EXPECTED_RANK_SHA256
    ):
        raise AssertionError("common potential commitment drift")
    census = result["potential_compatible_filter"]["census"]
    if census["steps_with_zero_potential_compatible_words"]:
        raise AssertionError("potential-only filter has an empty step")
    sidecar = result["accepted_ordinal_bitset_sidecar"]
    if sidecar["sha256"] != EXPECTED_BITSET_SHA256 or (
        sidecar["bytes"] != EXPECTED_BITSET_BYTES
    ):
        raise AssertionError("potential result/sidecar mismatch")
    return result, sidecar


def parse_bitsets(bitset, sidecar, cache_blocks, census):
    if bitset[:len(BITSET_MAGIC)] != BITSET_MAGIC:
        raise AssertionError("potential sidecar magic drift")
    schema, steps = struct.unpack_from("<II", bitset, len(BITSET_MAGIC))
    if schema != 1 or steps != EXPECTED_STEPS:
        raise AssertionError("potential sidecar header drift")
    cursor = len(BITSET_MAGIC) + 8
    compatible_digest = hashlib.sha256()
    records = []
    metadata_blocks = sidecar["blocks"]
    if len(metadata_blocks) != EXPECTED_STEPS:
        raise AssertionError("potential metadata block count drift")
    for step in range(EXPECTED_STEPS):
        block_offset = cursor
        values = struct.unpack_from("<IIIII", bitset, cursor)
        cursor += 20
        observed_step, words, byte_count, accepted_count, combined_count = values
        if observed_step != step or words != cache_blocks[step]["words"]:
            raise AssertionError("potential/cache step header drift", step)
        if byte_count != (words + 7) // 8:
            raise AssertionError("potential bitset length drift", step)
        accepted_offset = cursor
        accepted = bitset[cursor:cursor + byte_count]
        cursor += byte_count
        combined_offset = cursor
        combined = bitset[cursor:cursor + byte_count]
        cursor += byte_count
        if sum(byte.bit_count() for byte in accepted) != accepted_count or (
            sum(byte.bit_count() for byte in combined) != combined_count
        ):
            raise AssertionError("potential bitset population drift", step)
        valid = words & 7
        if valid:
            padding = ~((1 << valid) - 1) & 0xFF
            if accepted[-1] & padding or combined[-1] & padding:
                raise AssertionError("nonzero potential bitset padding", step)
        meta = metadata_blocks[step]
        observed_meta = {
            "step": step,
            "words": words,
            "block_offset": block_offset,
            "block_bytes": cursor - block_offset,
            "potential_compatible": {
                "offset": accepted_offset,
                "bytes": byte_count,
                "set_bits": accepted_count,
                "sha256": hashlib.sha256(accepted).hexdigest(),
            },
            "potential_compatible_digit_simple": {
                "offset": combined_offset,
                "bytes": byte_count,
                "set_bits": combined_count,
                "sha256": hashlib.sha256(combined).hexdigest(),
            },
            "unused_high_bits_in_final_byte_are_zero": True,
        }
        if meta != observed_meta:
            raise AssertionError("potential sidecar metadata drift", step)
        compatible_digest.update(struct.pack("<II", step, byte_count))
        compatible_digest.update(accepted)
        records.append({
            "step": step,
            "words": words,
            "offset": accepted_offset,
            "bytes": byte_count,
            "set_bits": accepted_count,
        })
    if cursor != len(bitset):
        raise AssertionError("potential sidecar trailing bytes")
    if compatible_digest.hexdigest() != census[
        "compatible_ordinal_bitsets_sha256"
    ]:
        raise AssertionError("compatible-ordinal aggregate digest drift")
    return tuple(records)


def potential_accepts(bitset, record, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("potential ordinal outside step block")
    index = ordinal - 1
    return bool(bitset[record["offset"] + (index >> 3)] & (1 << (index & 7)))


def endpoint(start, word):
    point = start
    for child in word:
        vector = MENU[child]
        point = tuple(point[axis] + vector[axis] for axis in range(3))
    return point


def projection_clean(interiors, yz_counts):
    local = set()
    for point in interiors:
        lateral = point[1:]
        if lateral in yz_counts or lateral in local:
            return False
        local.add(lateral)
    return True


def apply_selected(interiors, store, yz_counts):
    for point in interiors:
        lateral = point[1:]
        if yz_counts[lateral]:
            raise AssertionError("selected interior reuses yz fibre", lateral)
        yz_counts[lateral] = 1
    store.add_many(interiors)


def exact_legality_rejection(interiors, store):
    point_owner = {point: index for index, point in enumerate(store.pts)}
    witnesses = {
        "collision": first_collision(interiors, store.pts, point_owner),
        "old_old_new": first_old_old_new(interiors, store.pts),
        "old_new_new": first_old_new_new(interiors, store.pts),
        "new_new_new": first_new_new_new(interiors),
    }
    failed = [channel for channel, witness in witnesses.items() if witness]
    if not failed:
        raise AssertionError("fast legality rejected without exact witness")
    return {
        "failed_channels": failed,
        "primary_killed_channel": failed[0],
        "primary_exact_witness": witnesses[failed[0]],
        "all_channel_witnesses": witnesses,
    }


def prefix_commitment(store, yz_counts, records, next_rank):
    fields = {
        "next_construction_rank": next_rank,
        "selection_record_stream_sha256": stable_hash(records),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": point_stream_sha256(store.pts),
        "point_set_sha256": stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": stable_hash(sorted(yz_counts.items())),
    }
    fields["prefix_state_sha256"] = stable_hash(fields)
    return fields


def build_static(checker_sha256, input_sha256, sidecar, parent_word, anchors, schedule):
    static = {
        "level": 5,
        "checker_sha256": checker_sha256,
        "input_sha256": input_sha256,
        "potential_sidecar_sha256": sidecar["sha256"],
        "potential_channel": "potential_compatible (not digit-simple)",
        "common_potential_edge_stream_sha256": EXPECTED_SELECTED_EDGE_SHA256,
        "common_potential_rank_stream_sha256": EXPECTED_RANK_SHA256,
        "zero_mask_latent_reentry_controlled": False,
        "gaps": len(parent_word),
        "anchors": len(anchors),
        "parent_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
        "anchor_stream_sha256": stable_hash(anchors),
        "schedule_sha256": stable_hash(schedule),
    }
    static["static_state_sha256"] = stable_hash(static)
    return static


def seal_checkpoint(checkpoint):
    result = copy.deepcopy(checkpoint)
    result.pop("checkpoint_payload_sha256", None)
    result["checkpoint_payload_sha256"] = stable_hash(result)
    return result


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def load_checkpoint(path, static, initial_prefix):
    path = Path(path)
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "partial",
            "static": static,
            "next_construction_rank": 0,
            "selection_records": [],
            "pending_scan": None,
            "prefix": initial_prefix,
        }
    with path.open() as handle:
        checkpoint = json.load(handle)
    digest = checkpoint.pop("checkpoint_payload_sha256", None)
    if digest != stable_hash(checkpoint):
        raise AssertionError("checkpoint payload digest drift")
    checkpoint["checkpoint_payload_sha256"] = digest
    if checkpoint["schema_version"] != SCHEMA_VERSION or (
        checkpoint["static"] != static
    ):
        raise AssertionError("checkpoint static/schema drift")
    if checkpoint["next_construction_rank"] != len(
        checkpoint["selection_records"]
    ):
        raise AssertionError("checkpoint rank/record mismatch")
    pending = checkpoint["pending_scan"]
    if pending is not None and pending["construction_rank"] != checkpoint[
        "next_construction_rank"
    ]:
        raise AssertionError("checkpoint pending-rank mismatch")
    return checkpoint


def reconstruct_prefix(checkpoint, parent_word, anchors, schedule, cache, blocks, bitset, potential_records):
    store = Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    for rank, record in enumerate(checkpoint["selection_records"]):
        gap = schedule[rank]
        step = parent_word[gap]
        if record["construction_rank"] != rank or record["gap"] != gap or (
            record["step"] != step
        ):
            raise AssertionError("stored selection schedule drift", rank)
        word = tuple(record["selected_word"])
        offset = record["cache_record_offset"]
        if not blocks[step]["start"] <= offset < blocks[step]["end"]:
            raise AssertionError("stored selection cache offset drift", rank)
        length = cache[offset]
        if length != len(word) or tuple(cache[offset + 1:offset + 1 + length]) != word:
            raise AssertionError("stored selection cache bytes drift", rank)
        if not potential_accepts(
            bitset, potential_records[step],
            record["first_survivor_ordinal_1_based"],
        ):
            raise AssertionError("stored selection lost potential compatibility")
        interiors = tuple(word_interiors(anchors[gap], word))
        if endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("stored selection endpoint drift", rank)
        if not projection_clean(interiors, yz_counts):
            raise AssertionError("stored selection projection drift", rank)
        apply_selected(interiors, store, yz_counts)
    observed = prefix_commitment(
        store, yz_counts, checkpoint["selection_records"],
        checkpoint["next_construction_rank"],
    )
    if observed != checkpoint["prefix"]:
        raise AssertionError("checkpoint prefix commitment drift")
    return store, yz_counts


def empty_scan(rank, gap, step, block):
    return {
        "construction_rank": rank,
        "gap": gap,
        "step": step,
        "next_ordinal_1_based": 1,
        "next_cache_cursor": block["start"],
        "domain_words_scanned": 0,
        "potential_incompatible_skipped": 0,
        "potential_compatible_seen": 0,
        "projection_rejected": 0,
        "projection_clean_exact_tested": 0,
        "exact_legality_rejected": 0,
        "exact_legality_rejection_records": [],
    }


def validate_pending_scan(scan, rank, gap, step, block):
    if (scan["construction_rank"], scan["gap"], scan["step"]) != (
        rank, gap, step
    ):
        raise AssertionError("pending scan identity drift")
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    if not 1 <= ordinal <= block["words"] + 1:
        raise AssertionError("pending scan ordinal drift")
    if not block["start"] <= cursor <= block["end"]:
        raise AssertionError("pending scan cache cursor drift")
    scanned = scan["domain_words_scanned"]
    if scanned != ordinal - 1:
        raise AssertionError("pending scan ordinal/count drift")
    if scan["potential_incompatible_skipped"] + scan[
        "potential_compatible_seen"
    ] != scanned:
        raise AssertionError("pending scan potential partition drift")
    if scan["projection_rejected"] + scan[
        "projection_clean_exact_tested"
    ] != scan["potential_compatible_seen"]:
        raise AssertionError("pending scan projection partition drift")
    if scan["exact_legality_rejected"] != scan[
        "projection_clean_exact_tested"
    ]:
        raise AssertionError("pending scan exact-rejection partition drift")
    if len(scan["exact_legality_rejection_records"]) != scan[
        "exact_legality_rejected"
    ]:
        raise AssertionError("pending scan exact-witness count drift")


def select_first(cache, block, bitset, potential_record, rank, gap, step, start, target, store, yz_counts, pending, deadline):
    scan = copy.deepcopy(pending) if pending is not None else empty_scan(
        rank, gap, step, block
    )
    validate_pending_scan(scan, rank, gap, step, block)
    ordinal = scan["next_ordinal_1_based"]
    cursor = scan["next_cache_cursor"]
    memo = {}
    while ordinal <= block["words"]:
        if ordinal % 128 == 1 and enforce_runtime(deadline, "domain scan"):
            scan["next_ordinal_1_based"] = ordinal
            scan["next_cache_cursor"] = cursor
            raise DeadlineReached(scan)
        record_offset = cursor
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("compact cache word boundary drift", step, ordinal)
        word = tuple(cache[cursor:end])
        cursor = end
        scan["domain_words_scanned"] += 1
        if not potential_accepts(bitset, potential_record, ordinal):
            scan["potential_incompatible_skipped"] += 1
            ordinal += 1
            continue
        scan["potential_compatible_seen"] += 1
        interiors = tuple(word_interiors(start, word))
        if not projection_clean(interiors, yz_counts):
            scan["projection_rejected"] += 1
            ordinal += 1
            continue
        scan["projection_clean_exact_tested"] += 1
        if not word_legal_fast(start, word, store, memo, MENU):
            scan["exact_legality_rejected"] += 1
            scan["exact_legality_rejection_records"].append({
                "ordinal_1_based": ordinal,
                "word": list(word),
                **exact_legality_rejection(interiors, store),
            })
            ordinal += 1
            continue
        if not word_legal(start, word, store.pts, store.pset, {}):
            raise AssertionError("fast/reference selected-word disagreement", rank)
        if endpoint(start, word) != target:
            raise AssertionError("selected connector endpoint drift", rank)
        return ({
            "construction_rank": rank,
            "gap": gap,
            "step": step,
            "domain_words": block["words"],
            "potential_compatible_words_in_step": potential_record["set_bits"],
            "first_survivor_ordinal_1_based": ordinal,
            "cache_record_offset": record_offset,
            "domain_words_scanned_through_survivor": scan[
                "domain_words_scanned"
            ],
            "potential_incompatible_skipped_before_survivor": scan[
                "potential_incompatible_skipped"
            ],
            "potential_compatible_seen_through_survivor": scan[
                "potential_compatible_seen"
            ],
            "projection_rejected_before_survivor": scan[
                "projection_rejected"
            ],
            "projection_clean_exact_tested_through_survivor": scan[
                "projection_clean_exact_tested"
            ],
            "exact_legality_rejected_before_survivor": scan[
                "exact_legality_rejected"
            ],
            "exact_legality_rejection_records_before_survivor": scan[
                "exact_legality_rejection_records"
            ],
            "selected_word": list(word),
        }, interiors)
    scan["next_ordinal_1_based"] = ordinal
    scan["next_cache_cursor"] = cursor
    if cursor != block["end"]:
        raise AssertionError("exhausted domain cursor drift", step)
    if scan["potential_compatible_seen"] != potential_record["set_bits"]:
        raise AssertionError("exhausted potential population drift", step)
    raise NoSurvivor({
        **scan,
        "domain_words": block["words"],
        "potential_compatible_words_in_step": potential_record["set_bits"],
        "exact_full_restricted_domain_exhausted": True,
    })


def run_chunk(args, target_rank):
    started = time.monotonic()
    deadline = started + min(args.max_seconds, MAX_WORK_SECONDS)
    checker_sha256 = file_sha256(Path(__file__).resolve())
    policy = resource_policy()
    input_sha256 = verify_inputs(
        args.metadata, args.cache, args.potential, args.bitsets
    )
    _metadata, blocks = load_metadata(args.metadata)
    parent_word, anchors, schedule = load_l5_state()
    potential, sidecar = load_potential_result(args.potential)
    with Path(args.cache).open("rb") as cache_handle, Path(args.bitsets).open(
        "rb"
    ) as bitset_handle:
        cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
        bitset = mmap.mmap(bitset_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            potential_records = parse_bitsets(
                bitset, sidecar, blocks,
                potential["potential_compatible_filter"]["census"],
            )
            static = build_static(
                checker_sha256, input_sha256, sidecar,
                parent_word, anchors, schedule,
            )
            initial_store = Store(anchors)
            initial_yz = Counter(point[1:] for point in anchors)
            initial_prefix = prefix_commitment(initial_store, initial_yz, [], 0)
            checkpoint = load_checkpoint(
                args.checkpoint, static, initial_prefix
            )
            store, yz_counts = reconstruct_prefix(
                checkpoint, parent_word, anchors, schedule,
                cache, blocks, bitset, potential_records,
            )
            if checkpoint["status"] == "hard-jam":
                return checkpoint, {
                    "stop_reason": "previous exact hard-jam",
                    "new_gaps": 0,
                    "resource_policy": policy,
                }
            added = 0
            stop_reason = "target-rank"
            target_rank = min(target_rank, len(schedule))
            while checkpoint["next_construction_rank"] < target_rank:
                if added >= args.max_new_gaps:
                    stop_reason = "new-gap-limit"
                    break
                if enforce_runtime(deadline, "between stitches"):
                    stop_reason = "time-limit"
                    break
                rank = checkpoint["next_construction_rank"]
                gap = schedule[rank]
                step = parent_word[gap]
                try:
                    record, interiors = select_first(
                        cache, blocks[step], bitset, potential_records[step],
                        rank, gap, step, anchors[gap], anchors[gap + 1],
                        store, yz_counts, checkpoint["pending_scan"], deadline,
                    )
                except DeadlineReached as reached:
                    checkpoint["pending_scan"] = reached.pending
                    stop_reason = "time-limit-during-domain-scan"
                    break
                except NoSurvivor as failure:
                    checkpoint["pending_scan"] = None
                    checkpoint["status"] = "hard-jam"
                    checkpoint["obstruction"] = failure.details
                    stop_reason = "exact-restricted-hard-jam"
                    break
                checkpoint["selection_records"].append(record)
                apply_selected(interiors, store, yz_counts)
                checkpoint["next_construction_rank"] += 1
                checkpoint["pending_scan"] = None
                added += 1
                checkpoint["prefix"] = prefix_commitment(
                    store, yz_counts, checkpoint["selection_records"],
                    checkpoint["next_construction_rank"],
                )
                if added % CHECKPOINT_INTERVAL == 0:
                    checkpoint["last_run"] = {
                        "mode": args.command,
                        "intermediate": True,
                        "resource_policy": policy,
                    }
                    save_checkpoint(args.checkpoint, checkpoint)
            if checkpoint["next_construction_rank"] == len(schedule):
                checkpoint["status"] = "construction-complete-audit-pending"
                stop_reason = "construction-complete"
            checkpoint["prefix"] = prefix_commitment(
                store, yz_counts, checkpoint["selection_records"],
                checkpoint["next_construction_rank"],
            )
            checkpoint["last_run"] = {
                "mode": args.command,
                "new_gaps": added,
                "stop_reason": stop_reason,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "maximum_resident_bytes": maximum_resident_bytes(),
                "resource_policy": policy,
            }
            save_checkpoint(args.checkpoint, checkpoint)
        finally:
            bitset.close()
            cache.close()
    if file_sha256(Path(__file__).resolve()) != checker_sha256:
        raise RuntimeError("rescue checker changed during run")
    elapsed = time.monotonic() - started
    if elapsed > MAX_SECONDS:
        raise RuntimeError("hard 120-second process limit exceeded", elapsed)
    if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
        raise MemoryError("hard 300-MiB process limit exceeded")
    return checkpoint, {
        "stop_reason": stop_reason,
        "new_gaps": added,
        "resource_policy": policy,
        "elapsed_seconds": round(elapsed, 6),
        "maximum_resident_bytes": maximum_resident_bytes(),
    }


def gap2_payload(checkpoint, observation):
    reached = checkpoint["next_construction_rank"] >= 2
    records = checkpoint["selection_records"][:2]
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact potential-compatible gap-2 rescue witness"
            if reached
            else "potential-compatible gap-2 rescue not yet established"
        ),
        "checker": checkpoint["static"]["checker_sha256"],
        "static": checkpoint["static"],
        "completed_first_two_scheduled_stitches": reached,
        "gap_2_rescued": reached and records[1]["gap"] == 2,
        "first_two_selection_records": records,
        "obstruction": checkpoint.get("obstruction"),
        "pending_scan": checkpoint["pending_scan"],
        "checkpoint_payload_sha256": checkpoint[
            "checkpoint_payload_sha256"
        ],
        "observation": observation,
        "limitations": [
            "finite pinned L5 chronological state only",
            "common potential controls only the exact direction-blind degenerate non-x edge channel",
            "the height-two potential does not control exact-zero latent line re-entry",
            "no selector, birth, cursor-jump, or uniform far-secant theorem",
        ],
    }


def self_check():
    words = 10
    bits = bytes((0b00000101, 0b00000010))
    if not (bits[0] & 1) or not (bits[0] & 4) or not (bits[1] & 2):
        raise AssertionError("synthetic bit convention drift")
    if bits[1] & 0b11111100:
        raise AssertionError("synthetic padding drift")
    sample = {
        "words": words,
        "offset": 0,
        "set_bits": 3,
    }
    if [potential_accepts(bits, sample, ordinal) for ordinal in range(1, 11)] != [
        True, False, True, False, False, False, False, False, False, True
    ]:
        raise AssertionError("synthetic ordinal convention drift")
    return {
        "status": "passed",
        "potential_only_channel": True,
        "synthetic_ordinals": 10,
        "set_bits": 3,
    }


def estimate():
    return {
        "status": "no input opened and no cache scanned",
        "algorithm": (
            "mmap pinned cache and potential-only ordinal bitset; reconstruct "
            "the sealed prefix; scan cache order with potential, exact global "
            "yz freshness, then exact 3D legality filters"
        ),
        "hard_maximum_seconds_per_chunk": MAX_SECONDS,
        "maximum_work_deadline_seconds": MAX_WORK_SECONDS,
        "hard_maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "mid-domain_scan_resume": True,
        "potential_result_pins_finalized": not (
            EXPECTED_POTENTIAL_RESULT_SHA256 == "PENDING"
        ),
    }


def add_common_arguments(parser):
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--potential", default=DEFAULT_POTENTIAL)
    parser.add_argument("--bitsets", default=DEFAULT_BITSETS)
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--max-seconds", type=float, default=MAX_WORK_SECONDS)
    parser.add_argument("--max-new-gaps", type=int, default=500)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("estimate")
    subparsers.add_parser("self-check")
    probe = subparsers.add_parser("probe-gap2")
    add_common_arguments(probe)
    probe.add_argument("--output", default=DEFAULT_PROBE_OUTPUT)
    run_parser = subparsers.add_parser("run")
    add_common_arguments(run_parser)
    run_parser.add_argument("--target-rank", type=int, default=EXPECTED_GAPS)
    args = parser.parse_args()
    if args.command == "estimate":
        print(json.dumps(estimate(), sort_keys=True, indent=2))
        return
    if args.command == "self-check":
        print(json.dumps(self_check(), sort_keys=True, indent=2))
        return
    if not (0 < args.max_seconds <= MAX_WORK_SECONDS):
        raise ValueError("max-seconds must be in (0,115]")
    if not (1 <= args.max_new_gaps <= EXPECTED_GAPS):
        raise ValueError("max-new-gaps outside [1,2457]")
    target = 2 if args.command == "probe-gap2" else args.target_rank
    if not 1 <= target <= EXPECTED_GAPS:
        raise ValueError("target-rank outside [1,2457]")
    checkpoint, observation = run_chunk(args, target)
    if args.command == "probe-gap2":
        payload = gap2_payload(checkpoint, observation)
        atomic_json_dump(payload, args.output)
        print(json.dumps({
            "output": str(Path(args.output).resolve()),
            "output_sha256": file_sha256(args.output),
            "gap_2_rescued": payload["gap_2_rescued"],
            "records": payload["first_two_selection_records"],
            "observation": observation,
        }, sort_keys=True, indent=2))
    else:
        print(json.dumps({
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": file_sha256(args.checkpoint),
            "status": checkpoint["status"],
            "next_construction_rank": checkpoint["next_construction_rank"],
            "total_gaps": EXPECTED_GAPS,
            "pending_scan": checkpoint["pending_scan"],
            "observation": observation,
        }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
