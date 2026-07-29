#!/usr/bin/env python3
"""Pinned exact inputs and geometry for the guarded-L5 -> guarded-L6 gate.

This module deliberately does not accept the volatile raw JSON identity of the
lattice-envelope action report.  That report embeds elapsed time, RSS, inode,
and timestamp fields.  Its deterministic binary sidecar *is* accepted, but
only at the SHA-256 committed on main.  The guarded-L5 source is handled in the
same way: its selected-record digest and every terminal geometric commitment
must match the independently audited certificate committed on main.

The ``export-parent`` command turns that evidence into a deterministic compact
parent artifact.  It independently reconstructs the natural guarded-L5 walk,
checks all unordered pairs, and records only stable mathematical data.  The L6
constructor consumes that artifact as its sole parent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import pickle
import struct
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amplify_rich import M_BAL3  # noqa: E402
from design import potential_policy_chronological_rescue as rescue  # noqa: E402
from imbricate193 import apply  # noqa: E402


REPOSITORY_BASE_COMMIT = "e73a9cd1f7e775a98f8d4809eb18ed557c7a216f"
DEFAULT_METADATA = Path("/tmp/no-new-x-line-L5-canonical.json")
DEFAULT_CACHE = Path("/tmp/no-new-x-line-domains.bin")
DEFAULT_ACTION_BITSETS = Path(
    "/tmp/nonx-lattice-envelope-action-probe-bitsets.bin"
)
DEFAULT_GUARDED_L5_SOURCE = Path(
    "/tmp/lattice-T-chronological-L5-cone-guard-reproduced.json"
)
DEFAULT_CANONICAL_PARENT = Path("/tmp/guarded-L5-parent-canonical-v1.json")

EXPECTED_CANONICAL_PARENT_SHA256 = (
    "86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7"
)
EXPECTED_CANONICAL_PARENT_PAYLOAD_SHA256 = (
    "70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258"
)
EXPECTED_CANONICAL_PARENT_BYTES = 458_159
EXPECTED_METADATA_SHA256 = (
    "5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a"
)
EXPECTED_CACHE_SHA256 = (
    "da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7"
)
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_EFFECTIVE_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
EXPECTED_ACTION_BITSET_SHA256 = (
    "f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb"
)
EXPECTED_ACTION_BITSET_BYTES = 3_136_860
EXPECTED_ACTION_SUMMARY_SHA256 = (
    "adad358d0878cb9e72d420b4cd15fcbac4bd31423a11b59ddfa5ce939cb30201"
)
EXPECTED_ACTION_CHECKER_SHA256 = (
    "9056394f5529036f2e4515490de4940ca42d04165eae928c32f1b027aae36fed"
)
EXPECTED_GUARD_CHECKER_SHA256 = (
    "0a3041a77fffd954bd7ff2478427d1c7f6ea6f6951b9f8465c0a0966b6b3d376"
)
EXPECTED_PARENT_AUDITOR_SHA256 = (
    "b5d6b841fb8bcdfb606666dd653f05ce0e4af303a9f9840f83d0ae902c978e87"
)
EXPECTED_PARENT_SUMMARY_SHA256 = (
    "35ff40afbe13aa95a374285ab98994f4ed335b65d012f772a441a64789f3baf2"
)
EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256 = (
    "e22a0f71516e152f93f2d8f1c25a43fe79e6b7be384196845ebdb153bb2c0e01"
)
EXPECTED_HISTORICAL_PARENT_SOURCE_BYTES = 6_525_395
EXPECTED_HISTORICAL_PARENT_SOURCE_PAYLOAD_SHA256 = (
    "19c70eafa7b8c076764b711e8e8c77167d3f90c2e4509ce2432aab4cf04d946d"
)
EXPECTED_PARENT_SELECTION_SHA256 = (
    "dc39dcf34f5a15458ecd42641d39c481ac856f19921f82edbd980c70518b73a6"
)
EXPECTED_PARENT_PREFIX_SHA256 = (
    "6d4f45fbf7f4d606fb36e8b1c37b77f6148ff0b3851580a98e34497259635680"
)
EXPECTED_PARENT_WORDS_BY_GAP_SHA256 = (
    "c8fdcf6e6fd561e0b92c2501e979c612bbde669521aa9a07cdf44b0f747f07a0"
)
EXPECTED_PARENT_FLAT_WORD_SHA256 = (
    "24e60da88d787b78697673a1734f1ccc4b8e4bfacdefbf06544e25766ffe6619"
)
EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256 = (
    "2b3d99c21e062e3e76c6037ad042f4be21591b8b53714c617d41f9968e2117fd"
)
EXPECTED_PARENT_POINT_SET_SHA256 = (
    "1827b9595de7a95747cc290a1fcdde64cbf4214293e1603c22a5ec7a364391a9"
)
EXPECTED_PARENT_FINAL_YZ_SHA256 = (
    "899f963392893cf9035a63470eaa96a1401e04d9d55a97c7bceb3a9e6706f470"
)
EXPECTED_PARENT_FINAL_DOUBLE_FIBRE_SHA256 = (
    "d697a3b3feee953fb8cc3794f7c8f7a8108c98c70bce2d29466e62f590f0fd8f"
)
EXPECTED_PARENT_GAPS = 2_457
EXPECTED_PARENT_BASE_ANCHORS = 2_458
EXPECTED_PARENT_POINTS = 8_296
EXPECTED_PARENT_STEPS = 8_295
EXPECTED_PARENT_PROMOTED_CONE_PAIRS = 246
EXPECTED_PARENT_MAX_FIRST_ORDINAL = 3_417
EXPECTED_PARENT_SUM_FIRST_ORDINALS = 126_015
EXPECTED_PARENT_CONE_REJECTIONS = 4_211
EXPECTED_MENU_SIZE = 124

CACHE_MAGIC = b"NOXLN001"
BITSET_MAGIC = b"NTACB001"
BITSET_SCHEMA = 1
SPECTRA = (
    ("11/3", 11, 3),
    ("348/275", 348, 275),
)


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def point_stream_sha256(points) -> str:
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def atomic_json_dump(value, path: Path | str) -> None:
    path = Path(path)
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


def seal(value, field="payload_sha256"):
    result = dict(value)
    result.pop(field, None)
    result[field] = stable_hash(result)
    return result


def unseal(value, field="payload_sha256"):
    result = dict(value)
    internal = result.pop(field, None)
    if internal != stable_hash(result):
        raise AssertionError("JSON payload seal drift", field)
    result[field] = internal
    return result


def primitive_direction(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if divisor == 0:
        raise AssertionError("zero displacement")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def cone_matches(vector):
    r, y, z = vector
    quadratic = 3 * y * y - y * z + 3 * z * z
    return tuple(
        label
        for label, numerator, denominator in SPECTRA
        if denominator * quadratic - numerator * r * r == 0
    )


def subtract(left, right):
    return tuple(left[index] - right[index] for index in range(3))


def verify_projective_invariance():
    # Q(-3z,3y-z)=9Q(y,z), while (3r)^2=9r^2.
    probes = ((3, -1, 3), (55, 34, 18), (7, -11, 5), (1, 0, 0))
    for vector in probes:
        if cone_matches(vector) != cone_matches(apply(M_BAL3, vector)):
            raise AssertionError("M_BAL3 cone invariance drift", vector)
    determinant = (
        M_BAL3[0][0]
        * (M_BAL3[1][1] * M_BAL3[2][2]
           - M_BAL3[1][2] * M_BAL3[2][1])
    )
    if determinant == 0:
        raise AssertionError("M_BAL3 became singular")
    return determinant


def load_metadata(path=DEFAULT_METADATA):
    path = Path(path)
    if file_sha256(path) != EXPECTED_METADATA_SHA256:
        raise AssertionError("canonical connector metadata drift")
    with path.open() as handle:
        metadata = json.load(handle)
    cache_record = metadata.get("compact_domain_cache", {})
    if cache_record.get("sha256") != EXPECTED_CACHE_SHA256 or cache_record.get(
        "bytes"
    ) != EXPECTED_CACHE_BYTES:
        raise AssertionError("metadata/cache pin drift")
    blocks = {record["step"]: record for record in cache_record.get("blocks", [])}
    if set(blocks) != set(range(EXPECTED_MENU_SIZE)):
        raise AssertionError("connector block domain is not all 124 steps")
    if sum(record["words"] for record in blocks.values()) != (
        EXPECTED_EFFECTIVE_WORDS
    ) or sum(record["word_slots"] for record in blocks.values()) != (
        EXPECTED_WORD_SLOTS
    ):
        raise AssertionError("connector domain census drift")
    return metadata, blocks


def verify_cache(path=DEFAULT_CACHE):
    path = Path(path)
    if path.stat().st_size != EXPECTED_CACHE_BYTES or file_sha256(path) != (
        EXPECTED_CACHE_SHA256
    ):
        raise AssertionError("canonical connector cache drift")
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": EXPECTED_CACHE_SHA256,
    }


def decode_word(cache, block, offset):
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("cache record offset outside step block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("cache record boundary drift")
    return tuple(cache[offset + 1:end])


def iter_block_words(cache, block, ordinal=1, cursor=None):
    if cursor is None:
        cursor = block["start"]
        for _ in range(1, ordinal):
            length = cache[cursor]
            cursor += 1 + length
    while ordinal <= block["words"]:
        offset = cursor
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("cache block boundary drift", block["step"], ordinal)
        yield ordinal, offset, tuple(cache[cursor:end]), end
        cursor = end
        ordinal += 1
    if cursor != block["end"]:
        raise AssertionError("cache block has trailing bytes", block["step"])


def load_action_bitsets(path=DEFAULT_ACTION_BITSETS, cache_blocks=None):
    path = Path(path)
    if path.stat().st_size != EXPECTED_ACTION_BITSET_BYTES or file_sha256(path) != (
        EXPECTED_ACTION_BITSET_SHA256
    ):
        raise AssertionError("deterministic lattice action bitset drift")
    summary_path = ROOT / "design" / "nonx-lattice-envelope-action-probe-summary.json"
    if file_sha256(summary_path) != EXPECTED_ACTION_SUMMARY_SHA256:
        raise AssertionError("committed action summary drift")
    with summary_path.open() as handle:
        summary = json.load(handle)
    canonical = summary["canonical_artifacts"]["accepted_ordinal_bitsets"]
    if canonical["sha256"] != EXPECTED_ACTION_BITSET_SHA256 or canonical[
        "bytes"
    ] != EXPECTED_ACTION_BITSET_BYTES or summary["checker"]["sha256"] != (
        EXPECTED_ACTION_CHECKER_SHA256
    ):
        raise AssertionError("action summary does not bind pinned sidecar")

    handle = path.open("rb")
    mapping = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
    if mapping[:8] != BITSET_MAGIC:
        mapping.close()
        handle.close()
        raise AssertionError("action bitset magic drift")
    schema, count = struct.unpack_from("<II", mapping, 8)
    if schema != BITSET_SCHEMA or count != EXPECTED_MENU_SIZE:
        mapping.close()
        handle.close()
        raise AssertionError("action bitset header drift")
    cursor = 16
    records = {}
    zero_digest = hashlib.sha256()
    ordered_digest = hashlib.sha256()
    for expected_step in range(EXPECTED_MENU_SIZE):
        step, words, byte_count, zero_count, ordered_count = struct.unpack_from(
            "<IIIII", mapping, cursor
        )
        cursor += 20
        if step != expected_step or byte_count != (words + 7) // 8:
            raise AssertionError("action bitset block header drift", expected_step)
        if cache_blocks is not None and words != cache_blocks[step]["words"]:
            raise AssertionError("action/cache domain disagreement", step)
        zero_offset = cursor
        zero = mapping[cursor:cursor + byte_count]
        cursor += byte_count
        ordered_offset = cursor
        ordered = mapping[cursor:cursor + byte_count]
        cursor += byte_count
        if sum(byte.bit_count() for byte in zero) != zero_count or sum(
            byte.bit_count() for byte in ordered
        ) != ordered_count:
            raise AssertionError("action bitset population drift", step)
        if any(zero[index] & ~ordered[index] for index in range(byte_count)):
            raise AssertionError("zero action is not an ordered-action subset", step)
        if words % 8:
            unused = ~((1 << (words % 8)) - 1) & 0xFF
            if zero[-1] & unused or ordered[-1] & unused:
                raise AssertionError("nonzero action padding", step)
        zero_digest.update(struct.pack("<II", step, byte_count))
        zero_digest.update(zero)
        ordered_digest.update(struct.pack("<II", step, byte_count))
        ordered_digest.update(ordered)
        records[step] = {
            "step": step,
            "words": words,
            "bytes": byte_count,
            "zero": {"offset": zero_offset, "set_bits": zero_count},
            "ordered": {"offset": ordered_offset, "set_bits": ordered_count},
        }
    if cursor != len(mapping):
        raise AssertionError("action bitset trailing bytes")
    if zero_digest.hexdigest() != canonical[
        "zero_envelope_channel_sha256"
    ] or ordered_digest.hexdigest() != canonical[
        "ordered_envelope_channel_sha256"
    ]:
        raise AssertionError("action channel stream digest drift")
    return handle, mapping, records


def action_accepts(mapping, record, channel, ordinal):
    if not 1 <= ordinal <= record["words"]:
        raise AssertionError("action ordinal outside complete domain")
    offset = record[channel]["offset"] + (ordinal - 1) // 8
    return bool(mapping[offset] & (1 << ((ordinal - 1) % 8)))


def load_l5_base_state():
    with (ROOT / "gate2-l7-construction-L5.pkl").open("rb") as handle:
        state = pickle.load(handle)
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    schedule = tuple(state["order"])
    if len(parent_word) != EXPECTED_PARENT_GAPS or len(anchors) != (
        EXPECTED_PARENT_BASE_ANCHORS
    ) or sorted(schedule) != list(range(EXPECTED_PARENT_GAPS)):
        raise AssertionError("pinned L4-to-L5 base state drift")
    return parent_word, anchors, schedule


def verify_parent_summary():
    path = ROOT / "design" / "lattice-T-L5-cone-guard-audit-summary.json"
    if file_sha256(path) != EXPECTED_PARENT_SUMMARY_SHA256:
        raise AssertionError("guarded-L5 terminal summary drift")
    with path.open() as handle:
        summary = json.load(handle)
    if summary.get("status") != "exact independent guarded-L5 finite certificate":
        raise AssertionError("guarded-L5 summary is not terminal")
    if summary["checker"]["sha256"] != EXPECTED_PARENT_AUDITOR_SHA256:
        raise AssertionError("guarded-L5 auditor pin drift")
    source = summary["source_checkpoint"]
    if source != {
        "bytes": EXPECTED_HISTORICAL_PARENT_SOURCE_BYTES,
        "path": "/private/tmp/lattice-T-chronological-L5-cone-guard-v1.json",
        "payload_sha256": EXPECTED_HISTORICAL_PARENT_SOURCE_PAYLOAD_SHA256,
        "sha256": EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256,
    }:
        raise AssertionError("historical guarded-L5 source identity drift")
    required = {
        "construction_completed": True,
        "first_survivor_audit_completed": True,
        "independent_ordered_no_three_collinear_verified": True,
        "new_target_cone_secants": 0,
        "points": EXPECTED_PARENT_POINTS,
        "steps": EXPECTED_PARENT_STEPS,
        "promoted_base_cone_lines": EXPECTED_PARENT_PROMOTED_CONE_PAIRS,
        "target_cone_pair_matches_in_terminal_pair_scan": (
            EXPECTED_PARENT_PROMOTED_CONE_PAIRS
        ),
        "maximum_first_survivor_ordinal_1_based": (
            EXPECTED_PARENT_MAX_FIRST_ORDINAL
        ),
        "sum_first_survivor_ordinals": EXPECTED_PARENT_SUM_FIRST_ORDINALS,
        "independently_recounted_cone_rejections": EXPECTED_PARENT_CONE_REJECTIONS,
    }
    for key, expected in required.items():
        if summary["result"].get(key) != expected:
            raise AssertionError("guarded-L5 certified result drift", key)
    return summary, path


def load_reproduced_parent_source(path=DEFAULT_GUARDED_L5_SOURCE):
    path = Path(path)
    with path.open() as handle:
        source = json.load(handle)
    internal = source.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(source):
        raise AssertionError("reproduced guarded-L5 source payload drift")
    source["checkpoint_payload_sha256"] = internal
    if source.get("status") != "construction-complete-audit-pending" or source.get(
        "next_construction_rank"
    ) != EXPECTED_PARENT_GAPS or source.get("pending_scan") is not None or source.get(
        "obstruction"
    ) is not None:
        raise AssertionError("reproduced guarded-L5 source is not complete")
    records = source.get("selection_records")
    if len(records) != EXPECTED_PARENT_GAPS or stable_hash(records) != (
        EXPECTED_PARENT_SELECTION_SHA256
    ):
        raise AssertionError("reproduced guarded-L5 selection identity drift")
    if source["prefix"]["prefix_state_sha256"] != EXPECTED_PARENT_PREFIX_SHA256:
        raise AssertionError("reproduced guarded-L5 prefix identity drift")
    return source, {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": file_sha256(path),
        "payload_sha256": internal,
    }


def reconstruct_parent(source, metadata_path=DEFAULT_METADATA, cache_path=DEFAULT_CACHE,
                       action_path=DEFAULT_ACTION_BITSETS):
    _metadata, blocks = load_metadata(metadata_path)
    verify_cache(cache_path)
    action_handle, actions, action_records = load_action_bitsets(
        action_path, blocks
    )
    cache_handle = Path(cache_path).open("rb")
    cache = mmap.mmap(cache_handle.fileno(), 0, access=mmap.ACCESS_READ)
    try:
        if cache[:8] != CACHE_MAGIC:
            raise AssertionError("connector cache magic drift")
        parent_word, anchors, schedule = load_l5_base_state()
        selected = {}
        ordinals = []
        cone_rejections = 0
        for rank, record in enumerate(source["selection_records"]):
            gap = schedule[rank]
            step = parent_word[gap]
            if (record.get("construction_rank"), record.get("gap"), record.get("step")) != (
                rank, gap, step
            ):
                raise AssertionError("guarded-L5 selection schedule drift", rank)
            ordinal = record["first_survivor_ordinal_1_based"]
            if not action_accepts(actions, action_records[step], "zero", ordinal):
                raise AssertionError("guarded-L5 selected action bit drift", rank)
            word = decode_word(cache, blocks[step], record["cache_record_offset"])
            if list(word) != record["selected_word"]:
                raise AssertionError("guarded-L5 selected cache word drift", rank)
            if rescue.endpoint(anchors[gap], word) != anchors[gap + 1]:
                raise AssertionError("guarded-L5 selected endpoint drift", rank)
            selected[gap] = word
            ordinals.append(ordinal)
            cone_rejections += record["scan_counters_through_certificate"][
                "cone_birth_rejected"
            ]
        if set(selected) != set(range(EXPECTED_PARENT_GAPS)):
            raise AssertionError("guarded-L5 selected gap cover drift")
        chain = [anchors[0]]
        flat_word = []
        for gap in range(EXPECTED_PARENT_GAPS):
            word = selected[gap]
            chain.extend(rescue.word_interiors(anchors[gap], word))
            chain.append(anchors[gap + 1])
            flat_word.extend(word)
        chain = tuple(chain)
        flat_word = tuple(flat_word)
        if len(chain) != EXPECTED_PARENT_POINTS or len(flat_word) != (
            EXPECTED_PARENT_STEPS
        ) or len(chain) != len(set(chain)):
            raise AssertionError("guarded-L5 natural chain extent/repetition drift")
        commitments = {
            "selection_record_stream_sha256": stable_hash(
                source["selection_records"]
            ),
            "words_by_gap_sha256": stable_hash(
                [[gap, list(selected[gap])] for gap in range(EXPECTED_PARENT_GAPS)]
            ),
            "flat_step_word_sha256": hashlib.sha256(bytes(flat_word)).hexdigest(),
            "ordered_point_stream_sha256": point_stream_sha256(chain),
            "point_set_sha256": stable_hash(sorted(chain)),
        }
        expected_commitments = {
            "selection_record_stream_sha256": EXPECTED_PARENT_SELECTION_SHA256,
            "words_by_gap_sha256": EXPECTED_PARENT_WORDS_BY_GAP_SHA256,
            "flat_step_word_sha256": EXPECTED_PARENT_FLAT_WORD_SHA256,
            "ordered_point_stream_sha256": (
                EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256
            ),
            "point_set_sha256": EXPECTED_PARENT_POINT_SET_SHA256,
        }
        if commitments != expected_commitments:
            raise AssertionError(
                "reconstructed guarded-L5 commitment drift",
                expected_commitments,
                commitments,
            )
        initial_yz = Counter(point[1:] for point in anchors)
        final_yz = Counter(point[1:] for point in chain)
        for fibre, count in final_yz.items():
            if count != initial_yz.get(fibre, 1):
                raise AssertionError("guarded-L5 creates a new yz coincidence")
        doubles = sorted(fibre for fibre, count in final_yz.items() if count == 2)
        if stable_hash(sorted(final_yz.items())) != EXPECTED_PARENT_FINAL_YZ_SHA256 or (
            stable_hash(doubles) != EXPECTED_PARENT_FINAL_DOUBLE_FIBRE_SHA256
        ):
            raise AssertionError("guarded-L5 terminal yz commitment drift")
        if max(ordinals) != EXPECTED_PARENT_MAX_FIRST_ORDINAL or sum(ordinals) != (
            EXPECTED_PARENT_SUM_FIRST_ORDINALS
        ) or cone_rejections != EXPECTED_PARENT_CONE_REJECTIONS:
            raise AssertionError("guarded-L5 selection census drift")
        return {
            "points": chain,
            "flat_word": flat_word,
            "base_anchors": anchors,
            "selected": selected,
            "commitments": commitments,
            "maximum_first_survivor_ordinal": max(ordinals),
            "sum_first_survivor_ordinals": sum(ordinals),
            "cone_rejections_through_winners": cone_rejections,
            "final_yz_sha256": stable_hash(sorted(final_yz.items())),
            "final_double_fibre_sha256": stable_hash(doubles),
        }
    finally:
        cache.close()
        cache_handle.close()
        actions.close()
        action_handle.close()


def independent_parent_pair_audit(points, base_anchors):
    base_set = set(base_anchors)
    pair_checks = 0
    cone_pairs = 0
    spectrum_counts = Counter()
    for cursor, point in enumerate(points):
        directions = {}
        point_is_base = point in base_set
        for earlier in range(cursor):
            prior = points[earlier]
            raw = subtract(prior, point)
            direction = primitive_direction(raw)
            previous = directions.get(direction)
            if previous is not None:
                raise AssertionError(
                    "guarded-L5 parent contains a collinear triple",
                    previous,
                    earlier,
                    cursor,
                    [list(points[previous]), list(prior), list(point)],
                )
            directions[direction] = earlier
            matches = cone_matches(raw)
            if matches:
                if not point_is_base or prior not in base_set:
                    raise AssertionError(
                        "guarded-L5 parent has connector-born guarded-cone pair",
                        earlier,
                        cursor,
                        list(matches),
                    )
                cone_pairs += 1
                spectrum_counts.update(matches)
            pair_checks += 1
    expected_pairs = len(points) * (len(points) - 1) // 2
    if pair_checks != expected_pairs or cone_pairs != (
        EXPECTED_PARENT_PROMOTED_CONE_PAIRS
    ):
        raise AssertionError("guarded-L5 independent pair census drift")
    return {
        "pair_checks": pair_checks,
        "guarded_cone_pairs": cone_pairs,
        "guarded_cone_pairs_by_spectrum": dict(sorted(spectrum_counts.items())),
        "no_repeated_points": len(points) == len(set(points)),
        "no_collinear_triple": True,
        "all_guarded_cone_pairs_are_inherited_base_pairs": True,
    }


def export_parent(args):
    verify_projective_invariance()
    summary, summary_path = verify_parent_summary()
    source, source_snapshot = load_reproduced_parent_source(args.source)
    parent = reconstruct_parent(
        source, args.metadata, args.cache, args.action_bitsets
    )
    pair_audit = independent_parent_pair_audit(
        parent["points"], parent["base_anchors"]
    )
    payload = {
        "schema_version": 1,
        "status": "deterministic canonical form of the independently certified guarded-L5 parent",
        "repository_base_commit": REPOSITORY_BASE_COMMIT,
        "historical_certificate": {
            "source_checkpoint_sha256": EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256,
            "source_checkpoint_bytes": EXPECTED_HISTORICAL_PARENT_SOURCE_BYTES,
            "source_payload_sha256": (
                EXPECTED_HISTORICAL_PARENT_SOURCE_PAYLOAD_SHA256
            ),
            "terminal_summary_path": str(summary_path.relative_to(ROOT)),
            "terminal_summary_sha256": EXPECTED_PARENT_SUMMARY_SHA256,
            "terminal_payload_sha256": summary["terminal_payload_sha256"],
            "independent_auditor_sha256": EXPECTED_PARENT_AUDITOR_SHA256,
            "constructor_sha256": EXPECTED_GUARD_CHECKER_SHA256,
        },
        "reproduced_source_binding": {
            "selection_record_stream_sha256": EXPECTED_PARENT_SELECTION_SHA256,
            "prefix_state_sha256": EXPECTED_PARENT_PREFIX_SHA256,
            "raw_file_identity_excluded": (
                "the source embeds chunk timing/RSS provenance; its observed "
                "raw identity is reported by the command but is not part of "
                "this canonical mathematical parent"
            ),
        },
        "deterministic_inputs": {
            "metadata_sha256": EXPECTED_METADATA_SHA256,
            "cache_sha256": EXPECTED_CACHE_SHA256,
            "action_bitset_sha256": EXPECTED_ACTION_BITSET_SHA256,
            "action_summary_sha256": EXPECTED_ACTION_SUMMARY_SHA256,
        },
        "scope": {
            "level": 5,
            "base_anchors": EXPECTED_PARENT_BASE_ANCHORS,
            "construction_gaps": EXPECTED_PARENT_GAPS,
            "points": EXPECTED_PARENT_POINTS,
            "steps": EXPECTED_PARENT_STEPS,
            "connector_order": "compact-cache ordinal order",
            "stitch_order": "D2--4 fragile-first, then ordered gap index",
            "guarded_spectra": [label for label, _a, _b in SPECTRA],
        },
        "commitments": {
            **parent["commitments"],
            "final_yz_occupancy_sha256": parent["final_yz_sha256"],
            "final_double_fibre_sha256": parent[
                "final_double_fibre_sha256"
            ],
        },
        "selection_census": {
            "maximum_first_survivor_ordinal_1_based": parent[
                "maximum_first_survivor_ordinal"
            ],
            "sum_first_survivor_ordinals": parent[
                "sum_first_survivor_ordinals"
            ],
            "cone_rejections_through_winners": parent[
                "cone_rejections_through_winners"
            ],
        },
        "independent_pair_audit": pair_audit,
        "points": [list(point) for point in parent["points"]],
        "flat_word": list(parent["flat_word"]),
    }
    payload = seal(payload)
    atomic_json_dump(payload, args.output)
    output_sha256 = file_sha256(args.output)
    if Path(args.output).stat().st_size != EXPECTED_CANONICAL_PARENT_BYTES or (
        output_sha256 != EXPECTED_CANONICAL_PARENT_SHA256
    ) or payload["payload_sha256"] != EXPECTED_CANONICAL_PARENT_PAYLOAD_SHA256:
        raise AssertionError("canonical guarded-L5 parent byte identity drift")
    return {
        "status": payload["status"],
        "output": str(Path(args.output).resolve()),
        "bytes": Path(args.output).stat().st_size,
        "sha256": output_sha256,
        "payload_sha256": payload["payload_sha256"],
        "observed_reproduced_source_sha256": source_snapshot["sha256"],
        "points": len(parent["points"]),
        "steps": len(parent["flat_word"]),
        "pair_checks": pair_audit["pair_checks"],
        "guarded_cone_pairs": pair_audit["guarded_cone_pairs"],
    }


def load_canonical_parent(path, expected_sha256=EXPECTED_CANONICAL_PARENT_SHA256):
    path = Path(path)
    observed = file_sha256(path)
    if expected_sha256 is not None and observed != expected_sha256:
        raise AssertionError("canonical guarded-L5 parent file drift", observed)
    if path.stat().st_size != EXPECTED_CANONICAL_PARENT_BYTES:
        raise AssertionError("canonical guarded-L5 parent byte-size drift")
    with path.open() as handle:
        parent = unseal(json.load(handle))
    if parent["payload_sha256"] != EXPECTED_CANONICAL_PARENT_PAYLOAD_SHA256:
        raise AssertionError("canonical guarded-L5 parent payload pin drift")
    if parent.get("repository_base_commit") != REPOSITORY_BASE_COMMIT or parent.get(
        "status"
    ) != "deterministic canonical form of the independently certified guarded-L5 parent":
        raise AssertionError("canonical guarded-L5 parent schema/status drift")
    historical = parent["historical_certificate"]
    if historical["source_checkpoint_sha256"] != (
        EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256
    ) or historical["terminal_summary_sha256"] != EXPECTED_PARENT_SUMMARY_SHA256:
        raise AssertionError("canonical parent historical binding drift")
    commitments = parent["commitments"]
    expected = {
        "selection_record_stream_sha256": EXPECTED_PARENT_SELECTION_SHA256,
        "words_by_gap_sha256": EXPECTED_PARENT_WORDS_BY_GAP_SHA256,
        "flat_step_word_sha256": EXPECTED_PARENT_FLAT_WORD_SHA256,
        "ordered_point_stream_sha256": EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256,
        "point_set_sha256": EXPECTED_PARENT_POINT_SET_SHA256,
        "final_yz_occupancy_sha256": EXPECTED_PARENT_FINAL_YZ_SHA256,
        "final_double_fibre_sha256": EXPECTED_PARENT_FINAL_DOUBLE_FIBRE_SHA256,
    }
    if commitments != expected:
        raise AssertionError("canonical guarded-L5 parent commitment drift")
    points = tuple(tuple(point) for point in parent["points"])
    flat_word = tuple(parent["flat_word"])
    if len(points) != EXPECTED_PARENT_POINTS or len(flat_word) != (
        EXPECTED_PARENT_STEPS
    ) or point_stream_sha256(points) != EXPECTED_PARENT_ORDERED_POINT_STREAM_SHA256 or (
        hashlib.sha256(bytes(flat_word)).hexdigest()
        != EXPECTED_PARENT_FLAT_WORD_SHA256
    ):
        raise AssertionError("canonical guarded-L5 parent payload drift")
    pair_audit = parent["independent_pair_audit"]
    if pair_audit.get("pair_checks") != EXPECTED_PARENT_POINTS * (
        EXPECTED_PARENT_POINTS - 1
    ) // 2 or pair_audit.get("guarded_cone_pairs") != (
        EXPECTED_PARENT_PROMOTED_CONE_PAIRS
    ) or not pair_audit.get("no_collinear_triple"):
        raise AssertionError("canonical parent pair-audit commitment drift")
    return parent, points, flat_word, {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": observed,
        "payload_sha256": parent["payload_sha256"],
    }


def self_check():
    determinant = verify_projective_invariance()
    if cone_matches((3, -1, 3)) != ("11/3",):
        raise AssertionError("11/3 cone self-check drift")
    if cone_matches((55, 34, 18)) != ("348/275",):
        raise AssertionError("348/275 cone self-check drift")
    if primitive_direction((-6, 4, 6)) != (3, -2, -3):
        raise AssertionError("primitive-direction self-check drift")
    return {
        "status": "passed",
        "M_BAL3_determinant": determinant,
        "projective_cone_invariance_checked": True,
        "guarded_spectra": [label for label, _a, _b in SPECTRA],
        "historical_parent_source_sha256": (
            EXPECTED_HISTORICAL_PARENT_SOURCE_SHA256
        ),
        "deterministic_action_bitset_sha256": EXPECTED_ACTION_BITSET_SHA256,
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("self-check")
    export = subparsers.add_parser("export-parent")
    export.add_argument("--source", default=DEFAULT_GUARDED_L5_SOURCE)
    export.add_argument("--metadata", default=DEFAULT_METADATA)
    export.add_argument("--cache", default=DEFAULT_CACHE)
    export.add_argument("--action-bitsets", default=DEFAULT_ACTION_BITSETS)
    export.add_argument("--output", default=DEFAULT_CANONICAL_PARENT)
    args = parser.parse_args()
    result = self_check() if args.mode == "self-check" else export_parent(args)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
