#!/usr/bin/env python3
"""Exact role-first reachability filter for short-return holonomy guards.

This checker is intentionally locked until the *primary-lineage* L6
construction and its independent terminal audit have immutable pins.  It does
not accept the separate two-cone-guarded L5 construction as the parent of the
current L6 path: those artifacts contain different selected words and
different point streams.

The heavy mode performs the following operations in this order.

1. Reconstruct actual selected L5-word/slot -> selected L6-word/slot child
   pairs.  Whole words, slots, prefix controls, parent gaps, child gaps, and
   construction ranks remain correlated.
2. Generate only the exact ``8 -> 16 -> 8`` affine maps and full-candidate
   guard keys belonging to those actual hierarchical pairs.
3. Only then scan an explicit half-open range of actual secant births in the
   primary L5 or primary L6 chronology.  A Pluecker moment is materialised
   only when the primitive direction has one of the role-first guard keys.
4. Transport each retained line through its actual controls and report exact
   candidate-site effects plus raw full-domain and zero-envelope killed-word
   masks.

A guard-key match is not called a recurrent or dangerous line.  The output
separates (a) an algebraic projective key, (b) an actual two-endpoint secant,
(c) an affine fixed-point moment match, and (d) an exact candidate/word
effect.  No finite output from this script proves repeatability, a contracting
tail, positive availability, or an unconditional theorem.

The script uses one process and one thread.  Heavy mode requires nice >= 15,
all standard numerical thread variables equal to one, and a bounded range of
later endpoint ids.  Chunks are immutable independent certificates; this
file deliberately contains no automatic merge that could blur lineage or
scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import lattice_t_chronological_replay as l5_producer
from design import lattice_t_l6_continuation as l6_producer
from design import lattice_t_short_return_holonomy as holonomy


rescue = l5_producer.rescue

DEFAULT_HOLONOMY_RAW = Path(
    "/tmp/lattice-T-short-return-holonomy-zero-8-16.json"
)
DEFAULT_HOLONOMY_SUMMARY = (
    ROOT / "design" /
    "lattice-T-short-return-holonomy-zero-8-16-summary.json"
)
DEFAULT_L5_SOURCE = Path("/tmp/lattice-T-chronological-L5-primary.json")
DEFAULT_L5_TERMINAL = Path("/tmp/lattice-T-chronological-L5-audit-v2.json")
DEFAULT_L5_SUMMARY = ROOT / "design" / "lattice-T-chronological-L5-summary.json"
DEFAULT_L6_SOURCE = Path("/tmp/lattice-T-chronological-L6-checkpoint-v1.json")
DEFAULT_L6_TERMINAL = Path("/tmp/lattice-T-chronological-L6-audit-v1.json")

# Immutable holonomy and primary-L5 inputs.
EXPECTED_HOLONOMY_RAW_SHA256 = (
    "a1789f881fcced4abe6ac2d5aed2f001b867cae815a8c2c59dcd601aaee6d6bc"
)
EXPECTED_HOLONOMY_RAW_BYTES = 97_258_680
EXPECTED_HOLONOMY_SUMMARY_SHA256 = (
    "242dc1281ac84dc124844d0dc05b9f1e4f76f8b79c3973317493802c2bc4f3e8"
)
EXPECTED_HOLONOMY_SUMMARY_BYTES = 7_690
EXPECTED_HOLONOMY_CHECKER_SHA256 = (
    "bd1b8308216bb47f9c83d3f2ed2a50e30011d623ea63030f6cde82203a0b536b"
)

EXPECTED_L5_SOURCE_SHA256 = (
    "9c711e396dc75042b747a1bcacb5093aa8b4c84c316a89081b2e246bdae0c2b8"
)
EXPECTED_L5_SOURCE_BYTES = 5_369_433
EXPECTED_L5_SOURCE_PAYLOAD_SHA256 = (
    "4957ae7456b95d9d1c0033077eee136dfcda820e2ae4fdb9f1037490457dd71c"
)
EXPECTED_L5_SOURCE_PREFIX_SHA256 = (
    "5eb60096ccc3b0b51c17bb44bc782aa6c4106fb5dfa24c56952c5a4e914413a7"
)
EXPECTED_L5_SOURCE_SELECTION_SHA256 = (
    "73f8eb68b593cc268f254f30a84152b3d40887038b58f314f361fd107da066bd"
)
EXPECTED_L5_TERMINAL_SHA256 = (
    "144eb1d78a2a9c62be0747be50a2e135a8b8e91d5d2335e64398bf5af5146194"
)
EXPECTED_L5_TERMINAL_BYTES = 3_437
EXPECTED_L5_TERMINAL_PAYLOAD_SHA256 = (
    "832e8ce9c44f2528ffd3e39996572b3622e5d4b29ed47bfa593621d8c346528b"
)
EXPECTED_L5_SUMMARY_SHA256 = (
    "88fa0f41674d71cc9cf84fc1bd4b70949ab91cd1e8d83a435bb7b6bec5fc9df5"
)
EXPECTED_L5_SUMMARY_BYTES = 3_061
EXPECTED_PRIMARY_L5_ORDERED_POINT_STREAM_SHA256 = (
    "5da8880898a38de73b30f1570c1ac3de1c4c06b47c1da7eabc30d156e9123d08"
)
EXPECTED_PRIMARY_L5_FLAT_WORD_SHA256 = (
    "1429806fba4ec5703a44516863c34776cd4aa07764c687909c7bda29ef915fa7"
)
EXPECTED_PRIMARY_L5_POINT_SET_SHA256 = (
    "320ea9923f57acbf55ba6c9775b67d894b12324a8debdf0ceac85fe4147fedc4"
)
EXPECTED_PRIMARY_L5_POINTS = 8_268
EXPECTED_PRIMARY_L5_GAPS = 2_457
EXPECTED_PRIMARY_L5_STEPS = 8_267

EXPECTED_L5_PRODUCER_SHA256 = (
    "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
)
EXPECTED_L6_PRODUCER_SHA256 = (
    "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
)

# Explicitly forbidden lineage.  A tailored hard failure is emitted before a
# generic pin mismatch so this artifact can never be silently treated as the
# parent of the primary L6 continuation.
FORBIDDEN_GUARDED_L5_SOURCE_SHA256 = (
    "e22a0f71516e152f93f2d8f1c25a43fe79e6b7be384196845ebdb153bb2c0e01"
)
FORBIDDEN_GUARDED_L5_SOURCE_BYTES = 6_525_395
FORBIDDEN_GUARDED_L5_SELECTION_SHA256 = (
    "dc39dcf34f5a15458ecd42641d39c481ac856f19921f82edbd980c70518b73a6"
)
FORBIDDEN_GUARDED_L5_POINT_SET_SHA256 = (
    "1827b9595de7a95747cc290a1fcdde64cbf4214293e1603c22a5ec7a364391a9"
)
FORBIDDEN_GUARDED_L5_POINTS = 8_296

# Frozen from the completed primary L6 construction and its independently
# validated terminal audit.  Heavy mode remains locked if any required pin is
# missing or malformed.
EXPECTED_L6_SOURCE_SHA256 = (
    "82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7"
)
EXPECTED_L6_SOURCE_BYTES = 18_699_543
EXPECTED_L6_SOURCE_PAYLOAD_SHA256 = (
    "772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa"
)
EXPECTED_L6_SOURCE_PREFIX_SHA256 = (
    "7626fbb39cedfeff134c064989f54054e268d0c3fd881a4cd8b0782ae2eb917d"
)
EXPECTED_L6_SOURCE_SELECTION_SHA256 = (
    "219ad3095dafea4aecba62be79e8f4d446c814285c0aa3e2a1a4282bdc99981c"
)
EXPECTED_L6_SOURCE_MAX_FIRST_ORDINAL = 19_221
EXPECTED_L6_FINAL_POINTS = 28_665

EXPECTED_L6_AUDIT_CHECKER_SHA256 = (
    "b9f39fd20dfad194d45420b221617cf6b1baa872aa2aa1f4a38182274dece6f5"
)
EXPECTED_L6_TERMINAL_SHA256 = (
    "86241cb942d2a35c702dd6f8cc9a0db0c173ded7c99dd97f72c0e0123fac8b1d"
)
EXPECTED_L6_TERMINAL_BYTES = 3_497
EXPECTED_L6_TERMINAL_PAYLOAD_SHA256 = (
    "5f8ea3468d14ee187fd4b7a7fb6ae16f2df28829d6001bd8332a2fc2ff034ff5"
)
EXPECTED_L6_TERMINAL_ORDERED_POINT_STREAM_SHA256 = (
    "4a7906ce0b82b3f0657c5bdb2610ab8c7353adbb34a6ce799f33f07b79cedb3d"
)
EXPECTED_L6_TERMINAL_FLAT_WORD_SHA256 = (
    "fb5aa700d5b989f5cedf3855709b683cfad20a148dd3d9f22ba2f9a113f58e87"
)
EXPECTED_L6_TERMINAL_POINT_SET_SHA256 = (
    "c7d9c7bf11aa3817799733b48ab630c361e582e12100ffd4f847b5ac0ed18842"
)

EXPECTED_L6_GAPS = 8_267
EXPECTED_L6_ANCHORS = 8_268
EXPECTED_GLOBAL_OTHER_GUARD_KEYS = 47_942
EXPECTED_GLOBAL_RETURN_MAPS = 3_136
EXPECTED_FULL_MAP_REVEALS = 1_342_208
EXPECTED_CANDIDATE_SITES = {8: 214, 16: 214}

SCHEMA_VERSION = 1
MAX_LATER_IDS_PER_RUN = 128
HARD_MAX_SECONDS = 120.0
HARD_MAX_RESIDENT_BYTES = 300 * 1024 * 1024
HARD_MAX_BIRTHS = 20_000
HARD_MAX_EFFECTS = 20_000
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
PROCESS_START_CHECKER_SHA256 = rescue.file_sha256(Path(__file__).resolve())

# For M = ((3,0,0),(0,0,-3),(0,3,-1)), this is cof(M), satisfying
# (M u) cross (M v) = COFACTOR (u cross v).
COFACTOR = (
    (9, 0, 0),
    (0, -3, -9),
    (0, 9, 0),
)


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def enforce_budget(started, max_seconds, label):
    elapsed = time.monotonic() - started
    resident = rescue.maximum_resident_bytes()
    if resident > HARD_MAX_RESIDENT_BYTES:
        raise MemoryError(
            "300-MiB resident abort threshold crossed", label, resident
        )
    if elapsed > max_seconds:
        raise RuntimeError(
            "work-time abort threshold crossed", label, elapsed
        )


def file_sha256(path, budget=None):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
            if budget is not None:
                budget("file hashing")
    return digest.hexdigest()


def snapshot(path, expected_sha256, expected_bytes, label, budget=None):
    path = Path(path)
    size = path.stat().st_size
    if size != expected_bytes:
        raise AssertionError(label + " byte-size drift", size, expected_bytes)
    observed = file_sha256(path, budget=budget)
    if observed != expected_sha256:
        raise AssertionError(label + " file drift", observed, expected_sha256)
    return {
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": observed,
    }


def load_sealed_json(path, payload_field, expected_payload, label):
    with Path(path).open() as handle:
        value = json.load(handle)
    payload = value.pop(payload_field, None)
    if payload != rescue.stable_hash(value) or payload != expected_payload:
        raise AssertionError(label + " payload drift", payload)
    value[payload_field] = payload
    return value


def atomic_json_dump(value, output_path, budget):
    output = Path(output_path).resolve()
    if output.exists():
        raise FileExistsError(
            "immutable certificate output already exists", str(output)
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=output.name + ".", suffix=".tmp", dir=output.parent
    )
    digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "w") as handle:
            class BudgetedWriter:
                def __init__(self, target):
                    self.target = target
                    self.since_check = 0

                def write(self, chunk):
                    result = self.target.write(chunk)
                    digest.update(chunk.encode("utf-8"))
                    self.since_check += len(chunk)
                    if self.since_check >= 1024 * 1024:
                        budget("certificate serialization")
                        self.since_check = 0
                    return result

            writer = BudgetedWriter(handle)
            json.dump(value, writer, indent=2, sort_keys=True)
            writer.write("\n")
            budget("certificate serialization")
            handle.flush()
            os.fsync(handle.fileno())
        # A same-filesystem hard link is an atomic no-clobber commit: unlike
        # os.replace(), it fails if another certificate already owns output.
        os.link(temporary, output)
        os.unlink(temporary)
        return digest.hexdigest()
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def validate_output_target(args):
    output = Path(args.output).resolve()
    protected = {
        Path(value).resolve()
        for value in (
            args.holonomy_raw,
            args.holonomy_summary,
            args.parent_source,
            args.parent_terminal,
            args.parent_summary,
            args.l6_source,
            args.l6_terminal,
            args.metadata,
            args.cache,
            args.lattice_result,
            args.lattice_bitsets,
            Path(__file__).resolve(),
        )
    }
    if output in protected:
        raise RuntimeError(
            "certificate output aliases a protected input", str(output)
        )
    if output.exists():
        raise FileExistsError(
            "immutable certificate output already exists", str(output)
        )
    return output


def terminal_l6_pins():
    return {
        "source_file": EXPECTED_L6_SOURCE_SHA256,
        "source_payload": EXPECTED_L6_SOURCE_PAYLOAD_SHA256,
        "source_prefix": EXPECTED_L6_SOURCE_PREFIX_SHA256,
        "source_selection": EXPECTED_L6_SOURCE_SELECTION_SHA256,
        "audit_checker": EXPECTED_L6_AUDIT_CHECKER_SHA256,
        "audit_file": EXPECTED_L6_TERMINAL_SHA256,
        "audit_payload": EXPECTED_L6_TERMINAL_PAYLOAD_SHA256,
        "ordered_point_stream": (
            EXPECTED_L6_TERMINAL_ORDERED_POINT_STREAM_SHA256
        ),
        "flat_word": EXPECTED_L6_TERMINAL_FLAT_WORD_SHA256,
        "point_set": EXPECTED_L6_TERMINAL_POINT_SET_SHA256,
    }


def ensure_terminal_l6_pins():
    pins = terminal_l6_pins()
    pending = {
        key: value for key, value in pins.items()
        if not isinstance(value, str) or value.startswith("PENDING")
    }
    required_positive = {
        "source_bytes": EXPECTED_L6_SOURCE_BYTES,
        "source_max_first_ordinal": EXPECTED_L6_SOURCE_MAX_FIRST_ORDINAL,
        "final_points": EXPECTED_L6_FINAL_POINTS,
        "audit_bytes": EXPECTED_L6_TERMINAL_BYTES,
    }
    pending.update({
        key: value for key, value in required_positive.items() if value <= 0
    })
    if pending:
        raise RuntimeError(
            "role-first reachability is locked pending terminal primary L6 "
            "construction/audit pins",
            pending,
        )


def assert_checker_unchanged():
    observed = file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError(
            "role-first checker changed during execution",
            PROCESS_START_CHECKER_SHA256,
            observed,
        )


def resource_policy(selected_max_seconds):
    observed_threads = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed_threads.values()):
        raise RuntimeError(
            "all numerical thread variables must equal one", observed_threads
        )
    process_nice = os.nice(0)
    if process_nice < 15:
        raise RuntimeError("heavy mode requires process nice >= 15", process_nice)
    return {
        "processes": 1,
        "threads": 1,
        "process_nice": process_nice,
        "thread_environment": observed_threads,
        "work_time_abort_threshold_seconds": selected_max_seconds,
        "hard_ceiling_seconds": HARD_MAX_SECONDS,
        "resident_abort_threshold_bytes": HARD_MAX_RESIDENT_BYTES,
        "threshold_semantics": (
            "cooperatively checked during bounded inner loops; not an OS "
            "scheduler or address-space limit"
        ),
        "maximum_later_ids_per_chunk": MAX_LATER_IDS_PER_RUN,
    }


def verify_dependencies(budget):
    observed = {
        "holonomy": file_sha256(
            Path(holonomy.__file__).resolve(), budget=budget
        ),
        "l5_producer": file_sha256(
            Path(l5_producer.__file__).resolve(), budget=budget
        ),
        "l6_producer": file_sha256(
            Path(l6_producer.__file__).resolve(), budget=budget
        ),
    }
    expected = {
        "holonomy": EXPECTED_HOLONOMY_CHECKER_SHA256,
        "l5_producer": EXPECTED_L5_PRODUCER_SHA256,
        "l6_producer": EXPECTED_L6_PRODUCER_SHA256,
    }
    if observed != expected:
        raise AssertionError("checker dependency drift", expected, observed)
    return observed


def reject_guarded_l5(path, budget):
    path = Path(path)
    if path.stat().st_size == FORBIDDEN_GUARDED_L5_SOURCE_BYTES:
        observed = file_sha256(path, budget=budget)
        if observed == FORBIDDEN_GUARDED_L5_SOURCE_SHA256:
            raise RuntimeError(
                "forbidden lineage join: the two-cone-guarded 8,296-point "
                "L5 path is not the parent of the primary 8,268-anchor L6 path"
            )
    if "cone-guard" in path.name:
        raise RuntimeError(
            "forbidden lineage join: a cone-guarded L5 path was supplied"
        )


def verify_fixed_inputs(args, budget):
    reject_guarded_l5(args.parent_source, budget)
    snapshots = {
        "holonomy_raw": snapshot(
            args.holonomy_raw,
            EXPECTED_HOLONOMY_RAW_SHA256,
            EXPECTED_HOLONOMY_RAW_BYTES,
            "holonomy raw",
            budget,
        ),
        "holonomy_summary": snapshot(
            args.holonomy_summary,
            EXPECTED_HOLONOMY_SUMMARY_SHA256,
            EXPECTED_HOLONOMY_SUMMARY_BYTES,
            "holonomy summary",
            budget,
        ),
        "primary_L5_source": snapshot(
            args.parent_source,
            EXPECTED_L5_SOURCE_SHA256,
            EXPECTED_L5_SOURCE_BYTES,
            "primary L5 source",
            budget,
        ),
        "primary_L5_terminal": snapshot(
            args.parent_terminal,
            EXPECTED_L5_TERMINAL_SHA256,
            EXPECTED_L5_TERMINAL_BYTES,
            "primary L5 terminal",
            budget,
        ),
        "primary_L5_summary": snapshot(
            args.parent_summary,
            EXPECTED_L5_SUMMARY_SHA256,
            EXPECTED_L5_SUMMARY_BYTES,
            "primary L5 summary",
            budget,
        ),
    }
    with Path(args.holonomy_summary).open() as handle:
        holonomy_summary = json.load(handle)
    budget("holonomy summary load")
    raw_record = holonomy_summary.get("canonical_raw_result", {})
    if (
        raw_record.get("sha256") != EXPECTED_HOLONOMY_RAW_SHA256
        or raw_record.get("bytes") != EXPECTED_HOLONOMY_RAW_BYTES
        or holonomy_summary.get("checker", {}).get("sha256")
        != EXPECTED_HOLONOMY_CHECKER_SHA256
    ):
        raise AssertionError("holonomy summary/raw/checker pin disagreement")
    census = holonomy_summary.get("correlated_8_to_16_to_8_returns", {})
    spectrum = census.get("full_candidate_reveals", {})
    if (
        census.get("unique_affine_return_maps") != EXPECTED_GLOBAL_RETURN_MAPS
        or spectrum.get("unique_map_reveals") != EXPECTED_FULL_MAP_REVEALS
        or spectrum.get("guard_spectrum", {}).get("other", {}).get(
            "unique_polynomials"
        )
        != EXPECTED_GLOBAL_OTHER_GUARD_KEYS
    ):
        raise AssertionError("holonomy summary census drift")
    l5_source = load_sealed_json(
        args.parent_source,
        "checkpoint_payload_sha256",
        EXPECTED_L5_SOURCE_PAYLOAD_SHA256,
        "primary L5 source",
    )
    budget("primary L5 source load")
    snapshots["primary_L5_source"]["payload_sha256"] = (
        EXPECTED_L5_SOURCE_PAYLOAD_SHA256
    )
    if (
        l5_source.get("status") != "construction-complete-audit-pending"
        or len(l5_source.get("selection_records", ())) != EXPECTED_PRIMARY_L5_GAPS
        or l5_source.get("prefix", {}).get("prefix_state_sha256")
        != EXPECTED_L5_SOURCE_PREFIX_SHA256
        or rescue.stable_hash(l5_source["selection_records"])
        != EXPECTED_L5_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("primary L5 source extent/commitment drift")
    if (
        l5_source.get("prefix", {}).get("point_set_sha256")
        == FORBIDDEN_GUARDED_L5_POINT_SET_SHA256
        or rescue.stable_hash(l5_source["selection_records"])
        == FORBIDDEN_GUARDED_L5_SELECTION_SHA256
        or l5_source.get("prefix", {}).get("placed_point_count")
        == FORBIDDEN_GUARDED_L5_POINTS
    ):
        raise RuntimeError("forbidden guarded-L5 lineage detected in source payload")
    l5_terminal = load_sealed_json(
        args.parent_terminal,
        "terminal_payload_sha256",
        EXPECTED_L5_TERMINAL_PAYLOAD_SHA256,
        "primary L5 terminal",
    )
    budget("primary L5 terminal load")
    snapshots["primary_L5_terminal"]["payload_sha256"] = (
        EXPECTED_L5_TERMINAL_PAYLOAD_SHA256
    )
    required_terminal = (
        "construction_completed",
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not l5_terminal.get("result", {}).get(key) for key in required_terminal):
        raise AssertionError("primary L5 terminal certificate is incomplete")
    commitments = l5_terminal.get("commitments", {})
    if (
        commitments.get("selection_record_stream_sha256")
        != EXPECTED_L5_SOURCE_SELECTION_SHA256
        or commitments.get("alternate_ordered_point_stream_sha256")
        != EXPECTED_PRIMARY_L5_ORDERED_POINT_STREAM_SHA256
        or commitments.get("alternate_flat_step_word_sha256")
        != EXPECTED_PRIMARY_L5_FLAT_WORD_SHA256
        or commitments.get("final_point_set_sha256")
        != EXPECTED_PRIMARY_L5_POINT_SET_SHA256
    ):
        raise AssertionError("primary L5 terminal commitment drift")
    with Path(args.parent_summary).open() as handle:
        l5_summary = json.load(handle)
    budget("primary L5 summary load")
    if (
        l5_summary.get("source_checkpoint", {}).get("sha256")
        != EXPECTED_L5_SOURCE_SHA256
        or l5_summary.get("result", {}).get("points")
        != EXPECTED_PRIMARY_L5_POINTS
    ):
        raise AssertionError("primary L5 compact summary drift")
    return snapshots, l5_source, l5_terminal


def verify_terminal_l6(args, context, budget):
    source_snapshot = snapshot(
        args.l6_source,
        EXPECTED_L6_SOURCE_SHA256,
        EXPECTED_L6_SOURCE_BYTES,
        "terminal primary L6 source",
        budget,
    )
    source = load_sealed_json(
        args.l6_source,
        "checkpoint_payload_sha256",
        EXPECTED_L6_SOURCE_PAYLOAD_SHA256,
        "terminal primary L6 source",
    )
    budget("terminal primary L6 source load")
    source_snapshot["payload_sha256"] = EXPECTED_L6_SOURCE_PAYLOAD_SHA256
    static = source.get("static", {})
    parent_source = static.get("parent_source", {})
    if (
        parent_source.get("sha256") == FORBIDDEN_GUARDED_L5_SOURCE_SHA256
        or static.get("parent_ordered_point_stream_sha256")
        != EXPECTED_PRIMARY_L5_ORDERED_POINT_STREAM_SHA256
        or parent_source.get("sha256") != EXPECTED_L5_SOURCE_SHA256
        or static.get("anchors") != EXPECTED_L6_ANCHORS
    ):
        raise RuntimeError(
            "forbidden or non-primary L5 -> L6 lineage in terminal L6 source"
        )
    records = source.get("selection_records")
    if (
        source.get("status") != "construction-complete-audit-pending"
        or source.get("pending_scan") is not None
        or source.get("next_construction_rank") != EXPECTED_L6_GAPS
        or not isinstance(records, list)
        or len(records) != EXPECTED_L6_GAPS
        or source.get("prefix", {}).get("prefix_state_sha256")
        != EXPECTED_L6_SOURCE_PREFIX_SHA256
        or source.get("prefix", {}).get("placed_point_count")
        != EXPECTED_L6_FINAL_POINTS
        or rescue.stable_hash(records) != EXPECTED_L6_SOURCE_SELECTION_SHA256
    ):
        raise AssertionError("terminal primary L6 source extent drift")
    maximum = max(record["first_survivor_ordinal_1_based"] for record in records)
    if maximum != EXPECTED_L6_SOURCE_MAX_FIRST_ORDINAL:
        raise AssertionError("terminal primary L6 maximum ordinal drift", maximum)
    if static != context["l6"]["static"]:
        raise AssertionError("terminal L6 static state disagrees with reconstruction")
    terminal_snapshot = snapshot(
        args.l6_terminal,
        EXPECTED_L6_TERMINAL_SHA256,
        EXPECTED_L6_TERMINAL_BYTES,
        "terminal primary L6 audit",
        budget,
    )
    terminal = load_sealed_json(
        args.l6_terminal,
        "terminal_payload_sha256",
        EXPECTED_L6_TERMINAL_PAYLOAD_SHA256,
        "terminal primary L6 audit",
    )
    budget("terminal primary L6 audit load")
    terminal_snapshot["payload_sha256"] = EXPECTED_L6_TERMINAL_PAYLOAD_SHA256
    if terminal.get("checker", {}).get("sha256") != (
        EXPECTED_L6_AUDIT_CHECKER_SHA256
    ):
        raise AssertionError("terminal L6 audit checker drift")
    if terminal.get("source_checkpoint") != source_snapshot:
        raise AssertionError("terminal L6 audit/source snapshot disagreement")
    required = (
        "construction_completed",
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not terminal.get("result", {}).get(key) for key in required):
        raise AssertionError("terminal L6 audit is incomplete")
    if terminal.get("result", {}).get("points") != EXPECTED_L6_FINAL_POINTS:
        raise AssertionError("terminal L6 audited point extent drift")
    commitments = terminal.get("commitments", {})
    if (
        commitments.get("source_prefix_state_sha256")
        != EXPECTED_L6_SOURCE_PREFIX_SHA256
        or commitments.get("selection_record_stream_sha256")
        != EXPECTED_L6_SOURCE_SELECTION_SHA256
        or commitments.get("alternate_ordered_point_stream_sha256")
        != EXPECTED_L6_TERMINAL_ORDERED_POINT_STREAM_SHA256
        or commitments.get("alternate_flat_step_word_sha256")
        != EXPECTED_L6_TERMINAL_FLAT_WORD_SHA256
        or commitments.get("final_point_set_sha256")
        != EXPECTED_L6_TERMINAL_POINT_SET_SHA256
    ):
        raise AssertionError("terminal L6 audit commitment drift")
    return source, terminal, source_snapshot, terminal_snapshot


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


def primitive_direction(vector):
    divisor = math.gcd(*(abs(int(value)) for value in vector))
    if not divisor:
        raise AssertionError("zero secant displacement")
    result = tuple(int(value) // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def guard_key(direction):
    x, y, z = direction
    quadratic = 3 * y * y - y * z + 3 * z * z
    x_squared = x * x
    divisor = math.gcd(x_squared, quadratic)
    if not divisor:
        raise AssertionError("nonzero direction has zero guard gcd")
    return (x_squared // divisor, quadratic // divisor)


def key_text(key):
    return str(key[0]) + ":" + str(key[1])


def fraction_record(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def fraction_vector_record(vector):
    return [fraction_record(value) for value in vector]


def fraction_cross(left, right):
    return (
        Fraction(left[1]) * Fraction(right[2])
        - Fraction(left[2]) * Fraction(right[1]),
        Fraction(left[2]) * Fraction(right[0])
        - Fraction(left[0]) * Fraction(right[2]),
        Fraction(left[0]) * Fraction(right[1])
        - Fraction(left[1]) * Fraction(right[0]),
    )


def transport_line(direction, moment, control):
    raw_direction = matrix_vector(holonomy.M, direction)
    divisor = math.gcd(*(abs(value) for value in raw_direction))
    if not divisor:
        raise AssertionError("line transport produced zero direction")
    sign = 1
    primitive = tuple(value // divisor for value in raw_direction)
    if next(value for value in primitive if value) < 0:
        sign = -1
        primitive = tuple(-value for value in primitive)
    translated_moment = subtract(moment, cross(control, direction))
    raw_moment = matrix_vector(COFACTOR, translated_moment)
    if any(value % divisor for value in raw_moment):
        raise AssertionError("transported moment is not divisible by direction gcd")
    result_moment = tuple(sign * value // divisor for value in raw_moment)
    if sum(primitive[index] * result_moment[index] for index in range(3)):
        raise AssertionError("transported Pluecker incidence constraint drift")
    return primitive, result_moment


def line_token(direction, moment):
    return {
        "canonical_primitive_direction": list(direction),
        "exact_Pluecker_moment": list(moment),
        "guard_key": list(guard_key(direction)),
    }


def scan_step_domain(context, step, budget):
    block = context["blocks"][step]
    cache = context["cache"]
    cursor = block["start"]
    records = []
    candidate_sites = set()
    for ordinal in range(1, block["words"] + 1):
        if ordinal % 4_096 == 0:
            budget("connector-domain scan")
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if not 2 <= length <= 5 or end > block["end"]:
            raise AssertionError("connector cache record drift", step, ordinal)
        word = tuple(cache[cursor:end])
        cursor = end
        record = holonomy.word_record(ordinal, word)
        expected_endpoint = holonomy.matrix_vector(
            holonomy.M, holonomy.MENU[step]
        )
        if record["endpoint"] != expected_endpoint:
            raise AssertionError("connector endpoint drift", step, ordinal)
        records.append(record)
        candidate_sites.update(record["interiors"])
    if cursor != block["end"] or len(records) != block["words"]:
        raise AssertionError("connector block extent drift", step)
    candidate_sites = tuple(sorted(candidate_sites))
    if len(candidate_sites) != EXPECTED_CANDIDATE_SITES[step]:
        raise AssertionError("candidate-site extent drift", step)
    action = context["action_records"][step]
    byte_count = (action["words"] + 7) // 8
    zero_offset = action["zero"]["offset"]
    zero_bits = bytes(context["bitset"][zero_offset:zero_offset + byte_count])
    if sum(value.bit_count() for value in zero_bits) != action["zero"][
        "set_bits"
    ]:
        raise AssertionError("zero-envelope bitset population drift", step)
    return {
        "step": step,
        "records": tuple(records),
        "candidate_sites": candidate_sites,
        "candidate_site_sha256": stable_hash(candidate_sites),
        "zero_bits": zero_bits,
    }


def selected_by_gap(records, gaps, label):
    result = {}
    rank_by_gap = {}
    for rank, record in enumerate(records):
        if record.get("construction_rank") != rank:
            raise AssertionError(label + " construction-rank drift", rank)
        gap = record["gap"]
        if not 0 <= gap < gaps or gap in result:
            raise AssertionError(label + " gap partition drift", gap)
        result[gap] = record
        rank_by_gap[gap] = rank
    if set(result) != set(range(gaps)):
        raise AssertionError(label + " does not select every gap")
    return result, rank_by_gap


def action_accepts(context, step, ordinal):
    return l5_producer.action_accepts(
        context["bitset"], context["action_records"][step], "zero", ordinal
    )


def public_word_role(record, slot, control):
    word_record = holonomy.word_record(
        record["first_survivor_ordinal_1_based"],
        tuple(record["selected_word"]),
    )
    return {
        "ordinal_1_based": record["first_survivor_ordinal_1_based"],
        "word": list(word_record["word"]),
        "proper_interiors": [list(site) for site in word_record["interiors"]],
        "slot_zero_based": slot,
        "prefix_control": list(control),
    }


def make_map_record(controls, domains, budget):
    affine = holonomy.affine_from_controls(controls)
    fixed = affine["fixed_point"]
    public_controls = [list(control) for control in controls]
    map_id = stable_hash({"controls": public_controls})
    guard_records = {}
    for phase, sites in (
        ("start_domain", domains[8]["candidate_sites"]),
        ("middle_domain", domains[16]["candidate_sites"]),
    ):
        for site_index, site in enumerate(sites):
            if site_index % 128 == 0:
                budget("actual-map guard construction")
            adjusted = (
                tuple(Fraction(value) for value in site)
                if phase == "start_domain"
                else holonomy.pullback_site(controls[0], site)
            )
            direction = subtract(adjusted, fixed)
            guard = holonomy.guard_from_direction(direction)
            if guard.get("classification") != "other":
                continue
            key = tuple(guard["key"])
            public = {
                "phase": phase,
                "original_candidate_site": list(site),
                "phase_adjusted_site": fraction_vector_record(adjusted),
                "fixed_point": fraction_vector_record(fixed),
                "primitive_reveal_direction": list(guard["direction"]),
                "guard_key": list(key),
                "polynomial": guard["polynomial"],
            }
            public["guard_record_id"] = stable_hash(public)
            guard_records.setdefault(key, []).append(public)
    public_map = {
        "map_id": map_id,
        "controls": public_controls,
        "linear": [list(row) for row in affine["linear"]],
        "translation": list(affine["translation"]),
        "fixed_point": fraction_vector_record(fixed),
        "other_guard_keys": [
            list(key) for key in sorted(guard_records)
        ],
        "guard_records": [
            record
            for key in sorted(guard_records)
            for record in guard_records[key]
        ],
    }
    return {
        "map_id": map_id,
        "controls": tuple(tuple(value) for value in controls),
        "fixed_point": fixed,
        "guard_records": guard_records,
        "public": public_map,
    }


def build_actual_roles(context, l5_source, l6_source, domains, budget):
    base_word, base_anchors, base_schedule = rescue.load_l5_state()
    if (
        len(base_word) != EXPECTED_PRIMARY_L5_GAPS
        or len(base_anchors) != EXPECTED_PRIMARY_L5_GAPS + 1
    ):
        raise AssertionError("primary L4/L5 base extent drift")
    l5_by_gap, l5_rank = selected_by_gap(
        l5_source["selection_records"], EXPECTED_PRIMARY_L5_GAPS, "primary L5"
    )
    l6_by_gap, l6_rank = selected_by_gap(
        l6_source["selection_records"], EXPECTED_L6_GAPS, "primary L6"
    )
    flat_word = []
    child_offset = {}
    for gap in range(EXPECTED_PRIMARY_L5_GAPS):
        if gap % 256 == 0:
            budget("actual-role flattened-parent reconstruction")
        child_offset[gap] = len(flat_word)
        flat_word.extend(l5_by_gap[gap]["selected_word"])
    if (
        tuple(flat_word) != tuple(context["l6"]["parent_word"])
        or len(flat_word) != EXPECTED_PRIMARY_L5_STEPS
        or hashlib.sha256(bytes(flat_word)).hexdigest()
        != EXPECTED_PRIMARY_L5_FLAT_WORD_SHA256
    ):
        raise AssertionError("primary L5 flattened child-gap stream drift")
    maps = {}
    occurrences = []
    for parent_gap in range(EXPECTED_PRIMARY_L5_GAPS):
        if parent_gap % 64 == 0:
            budget("actual-role correlation")
        if base_word[parent_gap] != 8:
            continue
        first = l5_by_gap[parent_gap]
        if first["step"] != 8:
            raise AssertionError("actual primary L5 parent step drift", parent_gap)
        first_ordinal = first["first_survivor_ordinal_1_based"]
        if not action_accepts(context, 8, first_ordinal):
            raise AssertionError("selected primary L5 role lost zero-T membership")
        first_word = holonomy.word_record(
            first_ordinal, tuple(first["selected_word"])
        )
        for first_slot, child_step in enumerate(first_word["word"]):
            if child_step != 16:
                continue
            child_gap = child_offset[parent_gap] + first_slot
            second = l6_by_gap[child_gap]
            if second["step"] != 16 or context["l6"]["parent_word"][
                child_gap
            ] != 16:
                raise AssertionError("actual child gap is not step 16", child_gap)
            second_ordinal = second["first_survivor_ordinal_1_based"]
            if not action_accepts(context, 16, second_ordinal):
                raise AssertionError("selected primary L6 role lost zero-T membership")
            second_word = holonomy.word_record(
                second_ordinal, tuple(second["selected_word"])
            )
            for second_slot, returned_step in enumerate(second_word["word"]):
                if returned_step != 8:
                    continue
                controls = (
                    first_word["prefixes"][first_slot],
                    second_word["prefixes"][second_slot],
                )
                if controls not in maps:
                    maps[controls] = make_map_record(
                        controls, domains, budget
                    )
                map_record = maps[controls]
                public = {
                    "map_id": map_record["map_id"],
                    "parent_gap": parent_gap,
                    "parent_construction_rank": l5_rank[parent_gap],
                    "parent_step": 8,
                    "first_role": public_word_role(
                        first, first_slot, controls[0]
                    ),
                    "child_gap": child_gap,
                    "child_construction_rank": l6_rank[child_gap],
                    "child_step": 16,
                    "second_role": public_word_role(
                        second, second_slot, controls[1]
                    ),
                    "returned_step": 8,
                }
                public["occurrence_id"] = stable_hash(public)
                occurrences.append({
                    "public": public,
                    "map": map_record,
                    "parent_gap": parent_gap,
                    "parent_rank": l5_rank[parent_gap],
                    "child_gap": child_gap,
                    "child_rank": l6_rank[child_gap],
                    "first_word": first_word,
                    "second_word": second_word,
                })
    occurrences.sort(key=lambda item: item["public"]["occurrence_id"])
    role_index = {}
    for occurrence in occurrences:
        for key in occurrence["map"]["guard_records"]:
            role_index.setdefault(key, []).append(occurrence)
    return {
        "base_word": tuple(base_word),
        "base_anchors": tuple(base_anchors),
        "base_schedule": tuple(base_schedule),
        "l5_by_gap": l5_by_gap,
        "l6_by_gap": l6_by_gap,
        "maps": maps,
        "occurrences": occurrences,
        "role_index": role_index,
    }


def reconstruct_points(
    layer, context, roles, l5_source, l6_source, budget
):
    if layer == "l5":
        anchors = roles["base_anchors"]
        records = l5_source["selection_records"]
        selected = roles["l5_by_gap"]
        expected_points = EXPECTED_PRIMARY_L5_POINTS
        expected_point_set = EXPECTED_PRIMARY_L5_POINT_SET_SHA256
        label = "primary-L5"
        point_records = [
            {
                "point_id": point_id,
                "point": tuple(point),
                "birth_kind": "inherited-L4-anchor",
                "birth_rank": -1,
                "gap": None,
                "interior_slot": None,
                "source_point_id": point_id,
                "source_ordered_chain_index": None,
            }
            for point_id, point in enumerate(anchors)
        ]
    else:
        anchors = context["l6"]["anchors"]
        records = l6_source["selection_records"]
        selected = roles["l6_by_gap"]
        expected_points = EXPECTED_L6_FINAL_POINTS
        expected_point_set = EXPECTED_L6_TERMINAL_POINT_SET_SHA256
        label = "primary-L6"
        source_l5 = reconstruct_points(
            "l5", context, roles, l5_source, l6_source, budget
        )
        source_by_scaled_point = {
            matrix_vector(holonomy.M, record["point"]): record
            for record in source_l5
        }
        if len(source_by_scaled_point) != len(source_l5):
            raise AssertionError("scaled primary-L5 source map is not injective")
        point_records = []
        for ordered_index, point in enumerate(anchors):
            source = source_by_scaled_point.get(tuple(point))
            if source is None:
                raise AssertionError(
                    "L6 inherited anchor has no primary-L5 source",
                    ordered_index,
                )
            point_records.append({
                "point_id": ordered_index,
                "point": tuple(point),
                "birth_kind": "inherited-primary-L5-anchor",
                "birth_rank": -1,
                "gap": None,
                "interior_slot": None,
                "source_point_id": source["point_id"],
                "source_ordered_chain_index": ordered_index,
            })
    for rank, record in enumerate(records):
        if rank % 64 == 0:
            budget(label + " point reconstruction")
        gap = record["gap"]
        if selected[gap] is not record:
            raise AssertionError(label + " selected-record identity drift")
        start = anchors[gap]
        word = tuple(record["selected_word"])
        interiors = tuple(rescue.word_interiors(start, word))
        for slot, point in enumerate(interiors):
            point_records.append({
                "point_id": len(point_records),
                "point": tuple(point),
                "birth_kind": label + "-connector-interior",
                "birth_rank": rank,
                "gap": gap,
                "interior_slot": slot,
                "source_point_id": None,
                "source_ordered_chain_index": None,
            })
    points = tuple(record["point"] for record in point_records)
    if len(points) != expected_points or len(points) != len(set(points)):
        raise AssertionError(label + " point extent/repetition drift")
    if rescue.stable_hash(sorted(points)) != expected_point_set:
        raise AssertionError(label + " point-set commitment drift")
    return tuple(point_records)


def public_provenance(record):
    return {
        "point_id": record["point_id"],
        "birth_kind": record["birth_kind"],
        "birth_rank": record["birth_rank"],
        "gap": record["gap"],
        "interior_slot": record["interior_slot"],
        "source_point_id": record["source_point_id"],
        "source_ordered_chain_index": record.get(
            "source_ordered_chain_index"
        ),
    }


class MaskRegistry:
    def __init__(self, domains, budget):
        self.domains = domains
        self.budget = budget
        self.records = {}
        self.cache = {}

    def register(self, step, hit_sites):
        sites = tuple(sorted(set(hit_sites)))
        if not sites:
            return None
        cache_key = (step, sites)
        known = self.cache.get(cache_key)
        if known is not None:
            return known
        domain = self.domains[step]
        hits = set(sites)
        raw = bytearray((len(domain["records"]) + 7) // 8)
        for record_index, record in enumerate(domain["records"]):
            if record_index % 4_096 == 0:
                self.budget("killed-word mask construction")
            if hits.intersection(record["interiors"]):
                index = record["ordinal_1_based"] - 1
                raw[index >> 3] |= 1 << (index & 7)
        zero = bytes(
            raw[index] & domain["zero_bits"][index]
            for index in range(len(raw))
        )
        raw = bytes(raw)
        identity = {
            "step": step,
            "hit_sites": [list(site) for site in sites],
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "zero_sha256": hashlib.sha256(zero).hexdigest(),
        }
        mask_id = stable_hash(identity)
        record = {
            "mask_id": mask_id,
            "step": step,
            "hit_sites": [list(site) for site in sites],
            "bit_order": (
                "ordinal n is bit ((n-1) mod 8) of byte floor((n-1)/8)"
            ),
            "domain_words": len(domain["records"]),
            "full_domain": {
                "bytes": len(raw),
                "members": sum(value.bit_count() for value in raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "raw_hex": raw.hex(),
            },
            "zero_envelope": {
                "bytes": len(zero),
                "members": sum(value.bit_count() for value in zero),
                "sha256": hashlib.sha256(zero).hexdigest(),
                "raw_hex": zero.hex(),
            },
        }
        self.records[mask_id] = record
        self.cache[cache_key] = mask_id
        return mask_id


def candidate_hits(domain, direction, moment):
    return tuple(
        site for site in domain["candidate_sites"]
        if cross(site, direction) == moment
    )


def selected_word_is_killed(word_record, hit_sites):
    return bool(set(hit_sites).intersection(word_record["interiors"]))


def evaluate_effect(layer, birth, occurrence, domains, masks, roles, context):
    direction = tuple(birth["canonical_primitive_direction"])
    global_moment = tuple(birth["exact_Pluecker_moment"])
    key = tuple(birth["guard_key"])
    map_record = occurrence["map"]
    c0, c1 = map_record["controls"]
    phases = []
    if layer == "l5":
        anchor = roles["base_anchors"][occurrence["parent_gap"]]
        local_moment = subtract(global_moment, cross(anchor, direction))
        present0 = birth["birth_rank"] < occurrence["parent_rank"]
        phases.append({
            "phase": "start_8",
            "step": 8,
            "direction": direction,
            "moment": local_moment,
            "present_before_stitch": present0,
            "selected_word": occurrence["first_word"],
        })
        direction1, moment1 = transport_line(direction, local_moment, c0)
        expected_child_anchor = matrix_vector(
            holonomy.M,
            add(anchor, occurrence["first_word"]["prefixes"][
                occurrence["public"]["first_role"]["slot_zero_based"]
            ]),
        )
        if tuple(context["l6"]["anchors"][occurrence["child_gap"]]) != (
            expected_child_anchor
        ):
            raise AssertionError("actual parent-slot/child-gap geometry drift")
        phases.append({
            "phase": "middle_16",
            "step": 16,
            "direction": direction1,
            "moment": moment1,
            "present_before_stitch": True,
            "selected_word": occurrence["second_word"],
        })
        direction2, moment2 = transport_line(direction1, moment1, c1)
        phases.append({
            "phase": "returned_8_future_L7",
            "step": 8,
            "direction": direction2,
            "moment": moment2,
            "present_before_stitch": True,
            "selected_word": None,
        })
        fixed = map_record["fixed_point"]
        fixed_moment = fraction_cross(fixed, direction)
        observed_moment = tuple(Fraction(value) for value in local_moment)
    else:
        anchor = context["l6"]["anchors"][occurrence["child_gap"]]
        local_moment = subtract(global_moment, cross(anchor, direction))
        present1 = birth["birth_rank"] < occurrence["child_rank"]
        phases.append({
            "phase": "middle_16",
            "step": 16,
            "direction": direction,
            "moment": local_moment,
            "present_before_stitch": present1,
            "selected_word": occurrence["second_word"],
        })
        direction2, moment2 = transport_line(direction, local_moment, c1)
        phases.append({
            "phase": "returned_8_future_L7",
            "step": 8,
            "direction": direction2,
            "moment": moment2,
            "present_before_stitch": True,
            "selected_word": None,
        })
        fixed = map_record["fixed_point"]
        fixed_middle = matrix_vector(
            holonomy.M, subtract(fixed, c0)
        )
        fixed_moment = fraction_cross(fixed_middle, direction)
        observed_moment = tuple(Fraction(value) for value in local_moment)
    public_phases = []
    any_effect = False
    for phase in phases:
        if guard_key(phase["direction"]) != key:
            raise AssertionError("projective guard key changed under M")
        hits = candidate_hits(
            domains[phase["step"]], phase["direction"], phase["moment"]
        )
        applicable_hits = hits if phase["present_before_stitch"] else ()
        mask_id = masks.register(phase["step"], applicable_hits)
        killed_selected = (
            selected_word_is_killed(phase["selected_word"], hits)
            if phase["selected_word"] is not None
            else None
        )
        if (
            phase["present_before_stitch"]
            and phase["selected_word"] is not None
            and killed_selected
        ):
            raise AssertionError(
                "reachable secant kills an independently audited selected word",
                layer,
                birth["line_id"],
                occurrence["public"]["occurrence_id"],
                phase["phase"],
            )
        any_effect = any_effect or bool(applicable_hits)
        public_phases.append({
            "phase": phase["phase"],
            "step": phase["step"],
            "line": line_token(phase["direction"], phase["moment"]),
            "present_before_stitch": phase["present_before_stitch"],
            "candidate_hit_sites": [list(site) for site in hits],
            "applicable_killed_word_mask_id": mask_id,
            "selected_word_killed": killed_selected,
        })
    if not any_effect:
        return None
    guard_records = map_record["guard_records"][key]
    effect = {
        "line_id": birth["line_id"],
        "occurrence_id": occurrence["public"]["occurrence_id"],
        "map_id": map_record["map_id"],
        "guard_key": list(key),
        "guard_record_ids": [
            record["guard_record_id"] for record in guard_records
        ],
        "fixed_point_moment_test": {
            "fixed_point_phase": "start_8" if layer == "l5" else "middle_16",
            "expected_p_cross_direction": fraction_vector_record(fixed_moment),
            "observed_centered_moment": fraction_vector_record(observed_moment),
            "equal": fixed_moment == observed_moment,
            "meaning": (
                "equality is required for the exact affine-fixed-point line "
                "family; inequality does not make the secant safe from other effects"
            ),
        },
        "phases": public_phases,
    }
    effect["silent_then_returned_reveal"] = (
        layer == "l5"
        and public_phases[0]["present_before_stitch"]
        and not public_phases[0]["candidate_hit_sites"]
        and not public_phases[1]["candidate_hit_sites"]
        and bool(public_phases[2]["candidate_hit_sites"])
    )
    effect["effect_id"] = stable_hash(effect)
    return effect


def classify_birth(earlier, later):
    if later["birth_rank"] == -1:
        return "inherited-base-base"
    if earlier["birth_rank"] == later["birth_rank"]:
        return "same-word-new-new"
    return "old-new"


def scan_birth_chunk(
    args, layer, point_records, roles, domains, context, budget
):
    role_index = roles["role_index"]
    relevant_keys = set(role_index)
    masks = MaskRegistry(domains, budget)
    births = []
    effects = []
    pairs_scanned = 0
    for later_id in range(args.first_later_id, args.last_later_id):
        later = point_records[later_id]
        for earlier_id in range(later_id):
            earlier = point_records[earlier_id]
            direction = primitive_direction(
                subtract(later["point"], earlier["point"])
            )
            key = guard_key(direction)
            pairs_scanned += 1
            if pairs_scanned % 4_096 == 0:
                assert_checker_unchanged()
                budget("secant-pair scan")
            if key not in relevant_keys:
                continue
            # Exact Pluecker state is intentionally materialised only after
            # the role-first key filter above.
            moment = cross(earlier["point"], direction)
            if sum(direction[index] * moment[index] for index in range(3)):
                raise AssertionError("newborn Pluecker constraint drift")
            public = {
                "birth_layer": layer,
                "classification": classify_birth(earlier, later),
                "earlier_point_id": earlier_id,
                "earlier_point": list(earlier["point"]),
                "earlier_provenance": public_provenance(earlier),
                "later_point_id": later_id,
                "later_point": list(later["point"]),
                "later_provenance": public_provenance(later),
                "birth_rank": later["birth_rank"],
                "canonical_primitive_direction": list(direction),
                "exact_Pluecker_moment": list(moment),
                "guard_key": list(key),
                "polynomial": (
                    str(key[0]) + "*(3*y^2-y*z+3*z^2)-"
                    + str(key[1]) + "*r^2"
                ),
                "actual_two_endpoint_secant": True,
            }
            public["line_id"] = stable_hash(public)
            births.append(public)
            if len(births) > args.max_births:
                raise RuntimeError(
                    "matched-birth cap exceeded; use a smaller later-id chunk"
                )
            for occurrence_index, occurrence in enumerate(role_index[key]):
                if occurrence_index % 64 == 0:
                    budget("role-first effect fanout")
                effect = evaluate_effect(
                    layer, public, occurrence, domains, masks, roles, context
                )
                if effect is not None:
                    effects.append(effect)
                    if len(effects) > args.max_effects:
                        raise RuntimeError(
                            "effect cap exceeded; use a smaller later-id chunk"
                        )
    births.sort(key=lambda record: record["line_id"])
    effects.sort(key=lambda record: record["effect_id"])
    width = args.last_later_id - args.first_later_id
    expected_pairs = width * (
        args.first_later_id + args.last_later_id - 1
    ) // 2
    if pairs_scanned != expected_pairs:
        raise AssertionError("birth-pair range partition drift")
    return {
        "pairs_scanned": pairs_scanned,
        "matched_line_births": births,
        "effect_witnesses": effects,
        "killed_word_masks": sorted(
            masks.records.values(), key=lambda record: record["mask_id"]
        ),
    }


def run(args):
    ensure_terminal_l6_pins()
    output_path = validate_output_target(args)
    policy = resource_policy(args.max_seconds)
    started = time.monotonic()
    budget = lambda label: enforce_budget(
        started, args.max_seconds, label
    )
    dependencies = verify_dependencies(budget)
    snapshots, l5_source, l5_terminal = verify_fixed_inputs(args, budget)
    context = l6_producer.open_context(args)
    try:
        budget("L6 context reconstruction")
        l6_source, l6_terminal, l6_source_snapshot, l6_terminal_snapshot = (
            verify_terminal_l6(args, context, budget)
        )
        snapshots["terminal_primary_L6_source"] = l6_source_snapshot
        snapshots["terminal_primary_L6_audit"] = l6_terminal_snapshot
        domains = {
            step: scan_step_domain(context, step, budget)
            for step in (8, 16)
        }
        roles = build_actual_roles(
            context, l5_source, l6_source, domains, budget
        )
        if not 1 <= args.first_later_id < args.last_later_id:
            raise ValueError("later-id range must satisfy 1 <= first < last")
        if args.last_later_id - args.first_later_id > MAX_LATER_IDS_PER_RUN:
            raise ValueError("later-id chunk exceeds hard 128-id width")
        point_records = reconstruct_points(
            args.birth_layer, context, roles, l5_source, l6_source, budget
        )
        if args.last_later_id > len(point_records):
            raise ValueError("later-id range exceeds selected birth layer")
        scan = scan_birth_chunk(
            args, args.birth_layer, point_records, roles, domains,
            context, budget,
        )
        public_maps = sorted(
            (record["public"] for record in roles["maps"].values()),
            key=lambda record: record["map_id"],
        )
        public_occurrences = [
            record["public"] for record in roles["occurrences"]
        ]
        output = {
            "schema_version": SCHEMA_VERSION,
            "date": "2026-07-18",
            "status": (
                "exact role-first primary-lineage holonomy reachability "
                "chunk; finite evidence only"
            ),
            "checker": {
                "path": "design/lattice_t_role_first_holonomy_reachability.py",
                "sha256": PROCESS_START_CHECKER_SHA256,
                "unchanged_during_run": True,
            },
            "resource_policy": policy,
            "pinned_inputs": snapshots,
            "pinned_dependencies": dependencies,
            "scope": {
                "lineage": "terminal-audited primary L5 -> primary L6 only",
                "forbidden_join": (
                    "the separate two-cone-guarded 8,296-point L5 path"
                ),
                "birth_layer": args.birth_layer,
                "later_point_id_half_open_range": [
                    args.first_later_id, args.last_later_id
                ],
                "birth_layer_points": len(point_records),
                "all_birth_pairs_in_range_scanned_without_cutoff": True,
                "later_endpoint_id_partition": {
                    "first_inclusive": args.first_later_id,
                    "last_exclusive": args.last_later_id,
                    "hard_maximum_partition_width": MAX_LATER_IDS_PER_RUN,
                },
                "spatial_distance_cutoff_within_id_partition": None,
                "endpoint_distance_cutoff_within_id_partition": None,
                "global_other_guard_keys_in_algebraic_census": (
                    EXPECTED_GLOBAL_OTHER_GUARD_KEYS
                ),
            },
            "role_first_filter": {
                "actual_hierarchical_occurrences": public_occurrences,
                "actual_affine_maps": public_maps,
                "actual_affine_map_count": len(public_maps),
                "actual_occurrence_count": len(public_occurrences),
                "actual_other_guard_keys": [
                    list(key) for key in sorted(roles["role_index"])
                ],
                "actual_other_guard_key_count": len(roles["role_index"]),
                "whole_word_slot_child_gap_correlation_preserved": True,
            },
            "birth_and_effect_result": scan,
            "proved": [
                "each retained holonomy map is realized by one correlated selected L5 whole-word/slot and its actual selected L6 child whole-word/slot",
                "each retained line has two endpoints in the pinned realized chronology and exact primitive Pluecker data",
                "within the explicit later-endpoint-ID partition, every reported candidate hit and killed-word mask is computed by exact integer incidence with no spatial-distance or endpoint-distance cutoff",
                "raw killed-word masks use original compact-domain ordinals and separately report their zero-envelope intersection",
            ],
            "not_proved": [
                "that a guard-key match belongs to the affine fixed-point line family unless the separately reported moment equality holds",
                "that equality of one projective guard key implies membership in a discrete M-orbit",
                "repeatability of the two controls beyond the one selected L5/L6 descendant pair",
                "chronological legality or selected words at the returned future L7 phase",
                "a closed far-secant transfer state, contraction/ranking lemma, positive connector availability, or an unconditional theorem",
            ],
        }
        output["payload_sha256"] = stable_hash(output)
        assert_checker_unchanged()
        budget("pre-commit output")
        output_sha256 = atomic_json_dump(output, output_path, budget)
        return {
            "status": output["status"],
            "output": str(output_path),
            "output_sha256": output_sha256,
            "pairs_scanned": scan["pairs_scanned"],
            "matched_line_births": len(scan["matched_line_births"]),
            "effect_witnesses": len(scan["effect_witnesses"]),
        }
    finally:
        l6_producer.close_context(context)


def estimate():
    pins = terminal_l6_pins()
    finalized = not any(value.startswith("PENDING") for value in pins.values())
    finalized = finalized and all(value > 0 for value in (
        EXPECTED_L6_SOURCE_BYTES,
        EXPECTED_L6_SOURCE_MAX_FIRST_ORDINAL,
        EXPECTED_L6_FINAL_POINTS,
        EXPECTED_L6_TERMINAL_BYTES,
    ))
    return {
        "status": (
            "prepared exact role-first checker; heavy mode is fail-closed "
            "pending terminal primary L6 construction/audit pins"
        ),
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "terminal_L6_pins": pins,
        "terminal_L6_pins_finalized": finalized,
        "heavy_mode_locked": not finalized,
        "forbidden_guarded_L5_source_sha256": (
            FORBIDDEN_GUARDED_L5_SOURCE_SHA256
        ),
        "pinned_primary_L5_source_sha256": EXPECTED_L5_SOURCE_SHA256,
        "pinned_holonomy_raw_sha256": EXPECTED_HOLONOMY_RAW_SHA256,
        "algorithm": (
            "actual whole-word/slot/child-gap roles -> actual guard keys -> "
            "exact secant births -> Pluecker transport -> raw word masks"
        ),
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_later_ids_per_chunk": MAX_LATER_IDS_PER_RUN,
        "large_artifacts_opened": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument("--holonomy-raw", default=str(DEFAULT_HOLONOMY_RAW))
    parser.add_argument(
        "--holonomy-summary", default=str(DEFAULT_HOLONOMY_SUMMARY)
    )
    parser.add_argument(
        "--parent-source", default=str(DEFAULT_L5_SOURCE)
    )
    parser.add_argument(
        "--parent-terminal", default=str(DEFAULT_L5_TERMINAL)
    )
    parser.add_argument(
        "--parent-summary", default=str(DEFAULT_L5_SUMMARY)
    )
    parser.add_argument("--l6-source", default=str(DEFAULT_L6_SOURCE))
    parser.add_argument("--l6-terminal", default=str(DEFAULT_L6_TERMINAL))
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(l5_producer.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(l5_producer.DEFAULT_LATTICE_BITSETS)
    )
    parser.add_argument("--birth-layer", choices=("l5", "l6"), default="l5")
    parser.add_argument("--first-later-id", type=int, default=1)
    parser.add_argument("--last-later-id", type=int)
    parser.add_argument("--output")
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    parser.add_argument("--max-births", type=int, default=HARD_MAX_BIRTHS)
    parser.add_argument("--max-effects", type=int, default=HARD_MAX_EFFECTS)
    args = parser.parse_args()
    if args.mode == "estimate":
        result = estimate()
    else:
        if args.last_later_id is None or args.output is None:
            parser.error("run requires --last-later-id and --output")
        if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
            parser.error("max-seconds outside (0,120]")
        if not 1 <= args.max_births <= HARD_MAX_BIRTHS:
            parser.error("max-births outside [1,20000]")
        if not 1 <= args.max_effects <= HARD_MAX_EFFECTS:
            parser.error("max-effects outside [1,20000]")
        result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
