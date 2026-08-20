#!/usr/bin/env python3
"""Fail-closed five-corridor chronological birth/shell mask census.

This is the exact finite-diagnostic successor to
``lattice_t_birth_shell_mask_experiment.py``.  The v1 checker and its result
are immutable inputs: this file neither imports their conclusions as proof nor
rewrites either artifact.  V2 waits for a completed, independently audited L6
construction, independently replays the exact chronological L5 prefix at one
poison-blind owner, and then revisits the four L6 corridors actually descended
from its selected word.  Each L6 corridor is evaluated immediately before and
immediately after its true inverse-schedule action in the single realized
chronological L6 construction.

For each complete connector domain, the output stores fixed-width raw word
masks for the five predicates which the construction actually intersects:

* zero-envelope (zero-T) action membership;
* intrinsic connector validity and intrinsic (y,z)-projection cleanliness;
* global (y,z)-fibre freshness against the exact prefix;
* exact geometric legality against every placed point; and
* their combined policy survivor set.

The geometric mask is split into collision, old--old--new, and old--new--new
channels, and into overlapping D=40/3-adic spatial and chronological birth
shells.  Every witness record retains stable endpoint identities, recursive
birth ancestry, exact coordinates, primitive direction, and integer moment.
No endpoint or distance truncation is used.  Masks are little-endian bytes
encoded as fixed-width hexadecimal strings, so memberships can be recovered
from the JSON rather than inferred from populations or hashes.

The chronological replay also seals the adjacent action records around each
target rank.  It never splices independent address streams: L5 owner, actual
selected L5 word, slot, prefix, L6 natural gap, inverse-schedule rank, exact
L6 selected action, and the adjacent schedule actions remain joined.  For each
L6 corridor, the before/after masks share the same corridor and domain, so their
bitwise comparison is meaningful.  Raw masks belonging to different steps or
domains are deliberately *not* compared.  The parent-to-child record contains
only exact populations, rational normalized populations, semantic descriptor
summaries, and commitments; no canonical cross-step projection is assumed.

This is still a narrow finite census, not a transition-system closure test.
It does not identify repeated abstract states, establish that the post-state of
one corridor is the pre-state of another comparable corridor, justify a
cross-step mask projection, prove a uniform tail or greatest-fixed-point
invariant, or produce an infinite Erdos #193 construction.

Full execution is deliberately locked by explicit ``PENDING`` L6 construction
and terminal-audit pins below.  Fill those constants only from the immutable
completed files, in one reviewed pin-only change.  ``estimate`` and
``self-check`` open no large construction artifacts; ``preflight`` and ``run``
refuse to proceed while any terminal pin remains pending.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.util
import json
import math
import mmap
import os
import resource
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1_CHECKER = ROOT / "design" / "lattice_t_birth_shell_mask_experiment.py"
V1_RESULT = ROOT / "design" / "lattice-T-L5-L6-birth-shell-mask-summary.json"
L6_PRODUCER = ROOT / "design" / "lattice_t_l6_continuation.py"
L6_AUDITOR = ROOT / "design" / "lattice_t_l6_audit.py"
SALVAGE_GATE = ROOT / "design" / "salvage_gate.py"
VIZ_PATH = ROOT / "viz" / "walk3d-data.json"

DEFAULT_L6_SOURCE = Path("/tmp/lattice-T-chronological-L6-checkpoint-v1.json")
DEFAULT_L6_TERMINAL = Path("/tmp/lattice-T-chronological-L6-audit-v1.json")
DEFAULT_CHECKPOINT = Path(
    "/tmp/lattice-T-birth-shell-transition-v2-checkpoint.json"
)
DEFAULT_OUTPUT = (
    ROOT / "design" / "lattice-T-birth-shell-transition-v2-summary.json"
)

# Frozen predecessor evidence.  V2 does not edit or silently regenerate it.
EXPECTED_V1_CHECKER_SHA256 = (
    "44eb4e6a93eef4218bc089cf2c2addea062a69433f3c3368c5e51c2baf08bcf0"
)
EXPECTED_V1_RESULT_SHA256 = (
    "70b0c0086c5e36da5ddb649aa3d53568a83165bbc39184facbfd65d4471cdb6b"
)
EXPECTED_SALVAGE_GATE_SHA256 = (
    "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95"
)
EXPECTED_VIZ_SHA256 = (
    "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883"
)

# -------------------------------------------------------------------------
# TERMINAL L6 PIN BLOCK.  Frozen from the completed construction and its
# independently validated terminal audit.  Every string and byte count here is
# intentionally explicit and came from sealed artifacts, not a live checkpoint.
# -------------------------------------------------------------------------
EXPECTED_L6_PRODUCER_SHA256 = (
    "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
)
EXPECTED_L6_SOURCE_SHA256 = (
    "82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7"
)
EXPECTED_L6_SOURCE_BYTES = 18_699_543
EXPECTED_L6_SOURCE_PAYLOAD_SHA256 = (
    "772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa"
)
EXPECTED_L6_SOURCE_STATIC_SHA256 = (
    "719ae1f97d8cf5cc87e37b849f4fe91a4e92e509a9129fbe48af5ef6fc77229d"
)
EXPECTED_L6_SOURCE_PREFIX_SHA256 = (
    "7626fbb39cedfeff134c064989f54054e268d0c3fd881a4cd8b0782ae2eb917d"
)
EXPECTED_L6_SOURCE_SELECTION_SHA256 = (
    "219ad3095dafea4aecba62be79e8f4d446c814285c0aa3e2a1a4282bdc99981c"
)

EXPECTED_L6_AUDITOR_SHA256 = (
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
EXPECTED_L6_TERMINAL_FINAL_YZ_SHA256 = (
    "8ce7f58ffbeebaed1b4acc6ca961a45ccb116499a53b66ab16f629192313c119"
)

EXPECTED_L6_GAPS = 8_267
EXPECTED_L6_ANCHORS = 8_268
EXPECTED_MENU_SIZE = 124
OWNER_L5_GAP = 93
OWNER_L5_RANK = 1_934
OWNER_L5_STEP = 70
OWNER_L5_WORD = (8, 19, 123, 118)
OWNER_L5_ORDINAL = 162
OWNER_L6_GAPS = (314, 315, 316, 317)

SCHEMA_VERSION = 3
LOCAL_RADIUS = 40
CHANNELS = ("collision", "old-old-new", "old-new-new")
PREDICATES = ("zero_T", "intrinsic", "global_yz", "geometric", "combined")
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
MAX_WORK_SECONDS = 110.0
HARD_MAX_SECONDS = 115.0
MAX_RESIDENT_BYTES = 320 * 1024 * 1024
DEFAULT_MAX_UNITS = 10_000
HARD_MAX_UNITS = 20_000
SAVE_UNIT_INTERVAL = 32
PROCESS_START_CHECKER_SHA256 = None


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


PROCESS_START_CHECKER_SHA256 = file_sha256(Path(__file__).resolve())


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def stable_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def hash_chain(previous, value):
    digest = hashlib.sha256()
    digest.update(bytes.fromhex(previous))
    digest.update(canonical_bytes(value))
    return digest.hexdigest()


def assert_checker_unchanged():
    if file_sha256(Path(__file__).resolve()) != PROCESS_START_CHECKER_SHA256:
        raise RuntimeError("v2 checker changed during execution")


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce=True):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and (
        nice >= 15
    )
    if enforce and not compliant:
        raise RuntimeError("run requires thread controls=1 and nice>=15")
    return {
        "processes": 1,
        "threads": 1,
        "thread_environment": environment,
        "process_nice": nice,
        "required_minimum_nice": 15,
        "maximum_work_seconds": MAX_WORK_SECONDS,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
        "cooperative_input_replay_deadline_and_RSS_checks": True,
        "compliant": compliant,
    }


class CooperativeLimitReached(RuntimeError):
    """A deterministic replay reached the caller's advertised chunk limit."""


def enforce_cooperative_limits(deadline, description):
    resident = maximum_resident_bytes()
    if resident > MAX_RESIDENT_BYTES:
        raise MemoryError(
            f"v2 resident-memory limit exceeded while {description}: "
            f"{resident}>{MAX_RESIDENT_BYTES}"
        )
    if deadline is not None and time.monotonic() >= deadline:
        raise CooperativeLimitReached(
            f"v2 cooperative deadline reached while {description}"
        )


def atomic_json_dump(value, path):
    assert_checker_unchanged()
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


def stable_file_snapshot(path, expected_sha256, expected_bytes=None):
    path = Path(path).resolve()
    before = path.stat()
    if expected_bytes is not None and before.st_size != expected_bytes:
        raise AssertionError("pinned byte-size drift", str(path), before.st_size)
    observed = file_sha256(path)
    after = path.stat()
    identity = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, key) for key in identity) != tuple(
        getattr(after, key) for key in identity
    ):
        raise RuntimeError("input changed while being hashed", str(path))
    if observed != expected_sha256:
        raise AssertionError("pinned digest drift", str(path), observed)
    return {
        "path": str(path),
        "sha256": observed,
        "bytes": after.st_size,
    }


def load_python_module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ImportError("cannot load pinned module", str(path))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def terminal_pin_block():
    return {
        "L6_producer": EXPECTED_L6_PRODUCER_SHA256,
        "L6_source_file": EXPECTED_L6_SOURCE_SHA256,
        "L6_source_bytes": EXPECTED_L6_SOURCE_BYTES,
        "L6_source_payload": EXPECTED_L6_SOURCE_PAYLOAD_SHA256,
        "L6_source_static": EXPECTED_L6_SOURCE_STATIC_SHA256,
        "L6_source_prefix": EXPECTED_L6_SOURCE_PREFIX_SHA256,
        "L6_source_selection": EXPECTED_L6_SOURCE_SELECTION_SHA256,
        "L6_auditor": EXPECTED_L6_AUDITOR_SHA256,
        "L6_terminal_file": EXPECTED_L6_TERMINAL_SHA256,
        "L6_terminal_bytes": EXPECTED_L6_TERMINAL_BYTES,
        "L6_terminal_payload": EXPECTED_L6_TERMINAL_PAYLOAD_SHA256,
        "L6_terminal_ordered_points": (
            EXPECTED_L6_TERMINAL_ORDERED_POINT_STREAM_SHA256
        ),
        "L6_terminal_flat_word": EXPECTED_L6_TERMINAL_FLAT_WORD_SHA256,
        "L6_terminal_point_set": EXPECTED_L6_TERMINAL_POINT_SET_SHA256,
        "L6_terminal_final_yz": EXPECTED_L6_TERMINAL_FINAL_YZ_SHA256,
    }


def terminal_pins_finalized():
    pins = terminal_pin_block()
    strings = [value for value in pins.values() if isinstance(value, str)]
    return (
        all(value != "PENDING" for value in strings)
        and EXPECTED_L6_SOURCE_BYTES > 0
        and EXPECTED_L6_TERMINAL_BYTES > 0
    )


def ensure_terminal_pins():
    if not terminal_pins_finalized():
        raise RuntimeError(
            "v2 full execution is locked pending immutable L6 construction "
            "and independent terminal-audit pins",
            terminal_pin_block(),
        )


def unseal_json(path, payload_field, description):
    with Path(path).open() as handle:
        value = json.load(handle)
    internal = value.pop(payload_field, None)
    observed = stable_hash(value)
    value[payload_field] = internal
    if internal != observed:
        raise AssertionError(description + " internal payload drift")
    return value, internal


def add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def subtract(left, right):
    return tuple(a - b for a, b in zip(left, right))


def apply_matrix(matrix, vector):
    return tuple(
        sum(coefficient * value for coefficient, value in zip(row, vector))
        for row in matrix
    )


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive(vector):
    divisor = math.gcd(*(abs(value) for value in vector))
    if not divisor:
        raise ValueError("zero vector has no primitive direction")
    result = tuple(value // divisor for value in vector)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def line_key(first, second):
    direction = primitive(subtract(second, first))
    return direction, cross(first, direction)


def chebyshev(left, right):
    return max(abs(a - b) for a, b in zip(left, right))


def midpoint(left, right):
    return tuple((a + b) // 2 for a, b in zip(left, right))


def spatial_shell(distance):
    if distance <= LOCAL_RADIUS:
        return 0
    shell = 1
    ceiling = LOCAL_RADIUS * 3
    while distance > ceiling:
        shell += 1
        ceiling *= 3
    return shell


def rank_shell(distance):
    if distance < 0:
        raise ValueError("negative chronological distance")
    if distance == 0:
        return 0
    shell = 1
    ceiling = 3
    while distance >= ceiling:
        shell += 1
        ceiling *= 3
    return shell


def full_mask(bit_count):
    return (1 << bit_count) - 1 if bit_count else 0


def raw_mask(bits, bit_count):
    if bit_count < 0 or bits < 0 or bits & ~full_mask(bit_count):
        raise AssertionError("mask outside declared bit width")
    byte_count = (bit_count + 7) // 8
    encoded = bits.to_bytes(byte_count, "little")
    return {
        "encoding": "fixed-width-little-endian-byte-hex",
        "bit_count": bit_count,
        "byte_count": byte_count,
        "data_hex": encoded.hex(),
        "members": bits.bit_count(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bit_semantics": "ordinal i+1 is bit i; low bit first in each byte",
        "unused_high_bits_in_final_byte_are_zero": True,
    }


def decode_raw_mask(record, expected_bit_count):
    if record.get("encoding") != "fixed-width-little-endian-byte-hex":
        raise AssertionError("mask encoding drift")
    if record.get("bit_count") != expected_bit_count:
        raise AssertionError("mask bit-width drift")
    byte_count = (expected_bit_count + 7) // 8
    if record.get("byte_count") != byte_count:
        raise AssertionError("mask byte-width drift")
    encoded_hex = record.get("data_hex")
    if not isinstance(encoded_hex, str) or len(encoded_hex) != 2 * byte_count:
        raise AssertionError("mask is not fixed width")
    if encoded_hex != encoded_hex.lower() or any(
        character not in "0123456789abcdef" for character in encoded_hex
    ):
        raise AssertionError("mask hex is not canonical lowercase hexadecimal")
    encoded = bytes.fromhex(encoded_hex)
    if len(encoded) != byte_count or encoded.hex() != encoded_hex:
        raise AssertionError("mask decoded byte width/canonical form drift")
    bits = int.from_bytes(encoded, "little")
    if bits & ~full_mask(expected_bit_count):
        raise AssertionError("mask padding bits are nonzero")
    if record.get("members") != bits.bit_count() or record.get("sha256") != (
        hashlib.sha256(encoded).hexdigest()
    ):
        raise AssertionError("mask commitment drift")
    return bits


def allowed_killed_pair(allowed, bit_count):
    universe = full_mask(bit_count)
    return {
        "allowed": raw_mask(allowed, bit_count),
        "killed": raw_mask(universe & ~allowed, bit_count),
        "allowed_OR_killed_is_full_domain": True,
        "allowed_AND_killed_is_empty": True,
    }


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def verify_l6_source(path, producer, l6_static):
    snapshot = stable_file_snapshot(
        path, EXPECTED_L6_SOURCE_SHA256, EXPECTED_L6_SOURCE_BYTES
    )
    source, internal = unseal_json(path, "checkpoint_payload_sha256", "L6 source")
    if internal != EXPECTED_L6_SOURCE_PAYLOAD_SHA256:
        raise AssertionError("L6 source payload pin drift")
    if source.get("schema_version") != producer.SCHEMA_VERSION:
        raise AssertionError("L6 source schema drift")
    if source.get("static") != l6_static or source["static"].get(
        "static_state_sha256"
    ) != EXPECTED_L6_SOURCE_STATIC_SHA256:
        raise AssertionError("L6 source static-state drift")
    if source.get("status") != "construction-complete-audit-pending":
        raise AssertionError("L6 source is not construction-complete")
    records = source.get("selection_records")
    if (
        source.get("next_construction_rank") != EXPECTED_L6_GAPS
        or not isinstance(records, list)
        or len(records) != EXPECTED_L6_GAPS
        or source.get("pending_scan") is not None
    ):
        raise AssertionError("L6 source extent drift")
    if source["prefix"].get("prefix_state_sha256") != (
        EXPECTED_L6_SOURCE_PREFIX_SHA256
    ):
        raise AssertionError("L6 source prefix pin drift")
    if stable_hash(records) != EXPECTED_L6_SOURCE_SELECTION_SHA256:
        raise AssertionError("L6 source selection pin drift")
    snapshot["payload_sha256"] = internal
    return source, snapshot


def verify_l6_terminal(path, source, source_snapshot):
    snapshot = stable_file_snapshot(
        path, EXPECTED_L6_TERMINAL_SHA256, EXPECTED_L6_TERMINAL_BYTES
    )
    terminal, internal = unseal_json(
        path, "terminal_payload_sha256", "L6 terminal audit"
    )
    if internal != EXPECTED_L6_TERMINAL_PAYLOAD_SHA256:
        raise AssertionError("L6 terminal payload pin drift")
    if terminal.get("status") != "exact independent terminal finite certificate":
        raise AssertionError("L6 terminal status drift")
    if terminal.get("checker", {}).get("sha256") != EXPECTED_L6_AUDITOR_SHA256:
        raise AssertionError("L6 terminal auditor pin drift")
    if terminal.get("source_checkpoint") != source_snapshot:
        raise AssertionError("L6 terminal/source snapshot disagreement")
    if terminal.get("source_producer_sha256") != EXPECTED_L6_PRODUCER_SHA256:
        raise AssertionError("L6 terminal producer pin drift")
    required = (
        "construction_completed",
        "first_survivor_audit_completed",
        "selected_reference_legality_verified_at_every_stitch",
        "fast_reference_agreement_verified_for_every_exact_test",
        "global_empty_yz_verified_at_every_stitch",
        "final_no_new_yz_coincidence",
        "independent_ordered_no_three_collinear_verified",
    )
    if any(not terminal.get("result", {}).get(key) for key in required):
        raise AssertionError("L6 terminal certificate is incomplete")
    if terminal["result"].get("gaps") != EXPECTED_L6_GAPS:
        raise AssertionError("L6 terminal gap extent drift")
    commitments = terminal.get("commitments", {})
    expected = {
        "source_prefix_state_sha256": EXPECTED_L6_SOURCE_PREFIX_SHA256,
        "selection_record_stream_sha256": (
            EXPECTED_L6_SOURCE_SELECTION_SHA256
        ),
        "alternate_ordered_point_stream_sha256": (
            EXPECTED_L6_TERMINAL_ORDERED_POINT_STREAM_SHA256
        ),
        "alternate_flat_step_word_sha256": (
            EXPECTED_L6_TERMINAL_FLAT_WORD_SHA256
        ),
        "final_point_set_sha256": EXPECTED_L6_TERMINAL_POINT_SET_SHA256,
        "final_yz_occupancy_sha256": EXPECTED_L6_TERMINAL_FINAL_YZ_SHA256,
    }
    if any(commitments.get(key) != value for key, value in expected.items()):
        raise AssertionError("L6 terminal commitment drift")
    if stable_hash(source["selection_records"]) != commitments[
        "selection_record_stream_sha256"
    ]:
        raise AssertionError("L6 source/terminal selection drift")
    snapshot["payload_sha256"] = internal
    return terminal, snapshot


def verify_frozen_v1_result():
    result, internal = unseal_json(
        V1_RESULT, "payload_sha256", "frozen v1 result"
    )
    if result.get("checker", {}).get("sha256") != EXPECTED_V1_CHECKER_SHA256:
        raise AssertionError("frozen v1 result/checker drift")
    if result.get("status") != (
        "exact finite realized-path L5-to-induced-L6 birth/shell mask "
        "panel; evidence only"
    ):
        raise AssertionError("frozen v1 result status drift")
    probes = result.get("probe_results")
    if not isinstance(probes, list) or len(probes) != 5:
        raise AssertionError("frozen v1 probe census drift")
    parent = probes[0]
    parent_probe = parent.get("probe", {})
    if (
        parent_probe.get("level"),
        parent_probe.get("parent_gap"),
        parent_probe.get("parent_rank"),
        parent_probe.get("step"),
        parent_probe.get("domain_words"),
    ) != (5, OWNER_L5_GAP, OWNER_L5_RANK, OWNER_L5_STEP, 16_392):
        raise AssertionError("frozen v1 L5 parent identity drift")
    def v1_mask_snapshot(record):
        return {
            "members": record["members"],
            "sha256": record["mask_sha256"],
        }
    near_far = parent["near_far_overlap_aware_OR"]
    return {
        "payload_sha256": internal,
        "static_state_sha256": result["commitments"]["static_state_sha256"],
        "probe_result_stream_sha256": result["commitments"][
            "probe_result_stream_sha256"
        ],
        "L5_parent_geometry_regression_authority": {
            "probe_id": parent_probe["probe_id"],
            "domain_words": parent_probe["domain_words"],
            "domain_block_sha256": parent_probe["domain_block_sha256"],
            "exact_full_killed": v1_mask_snapshot(
                parent["exact_full_killed_word_mask"]
            ),
            "near_membership": v1_mask_snapshot(
                near_far["near_membership"]
            ),
            "far_membership": v1_mask_snapshot(
                near_far["far_membership"]
            ),
        },
    }


def load_authorities(args, deadline=None):
    ensure_terminal_pins()
    enforce_cooperative_limits(deadline, "starting pinned-input verification")
    snapshots = {
        "v1_checker": stable_file_snapshot(
            V1_CHECKER, EXPECTED_V1_CHECKER_SHA256
        ),
        "v1_result": stable_file_snapshot(V1_RESULT, EXPECTED_V1_RESULT_SHA256),
        "L6_producer": stable_file_snapshot(
            L6_PRODUCER, EXPECTED_L6_PRODUCER_SHA256
        ),
        "L6_auditor": stable_file_snapshot(
            L6_AUDITOR, EXPECTED_L6_AUDITOR_SHA256
        ),
        "salvage_gate": stable_file_snapshot(
            SALVAGE_GATE, EXPECTED_SALVAGE_GATE_SHA256
        ),
        "viz": stable_file_snapshot(VIZ_PATH, EXPECTED_VIZ_SHA256),
    }
    snapshots["v1_verified_payload"] = verify_frozen_v1_result()
    enforce_cooperative_limits(deadline, "verifying frozen v1 evidence")
    producer = load_python_module(
        L6_PRODUCER, "pinned_lattice_t_l6_continuation_for_transition_v2"
    )
    salvage = load_python_module(
        SALVAGE_GATE, "pinned_salvage_gate_for_transition_v2"
    )
    if file_sha256(Path(producer.__file__).resolve()) != (
        EXPECTED_L6_PRODUCER_SHA256
    ):
        raise AssertionError("loaded L6 producer identity drift")
    producer_context = producer.open_context(args)
    try:
        enforce_cooperative_limits(deadline, "opening the pinned L6 context")
        source, source_snapshot = verify_l6_source(
            args.l6_source, producer, producer_context["l6"]["static"]
        )
        terminal, terminal_snapshot = verify_l6_terminal(
            args.l6_terminal, source, source_snapshot
        )
        enforce_cooperative_limits(deadline, "verifying terminal L6 evidence")
    except BaseException:
        producer.close_context(producer_context)
        raise
    snapshots["L6_source"] = source_snapshot
    snapshots["L6_terminal"] = terminal_snapshot
    return producer, salvage, producer_context, source, terminal, snapshots


def build_viz_origins(viz, matrix):
    """Recover every stable birth identity through the complete viz ancestry."""
    levels = viz.get("levels")
    if not isinstance(levels, list) or len(levels) < 5:
        raise AssertionError("viz ancestry does not reach L4")
    # L5's anchors descend from viz L4.  Later viz levels belong to a different
    # realized continuation and must not be imported into this alternate path.
    points_by_level = {
        level: tuple(tuple(point) for point in data["points"])
        for level, data in enumerate(levels[:5])
    }
    origins = {
        0: tuple({
            "stable_id": f"base:L0:P{index}",
            "origin_birth_level": 0,
            "origin_birth_gap": None,
            "origin_birth_rank": None,
            "origin_interior_slot": None,
            "birth_parent_endpoint_stable_ids": [],
            "generation_lineage": [{
                "level": 0,
                "kind": "base-point",
                "path_index": index,
            }],
        } for index in range(len(points_by_level[0])))
    }
    for level in range(1, 5):
        parents = levels[level].get("parents")
        points = points_by_level[level]
        previous_points = points_by_level[level - 1]
        previous_origins = origins[level - 1]
        if not isinstance(parents, list) or len(parents) != len(points):
            raise AssertionError("viz parent-map extent drift", level)
        block_start = {}
        current = []
        for index, parent in enumerate(parents):
            if not 0 <= parent < len(previous_points):
                raise AssertionError("viz parent index outside prior level", level)
            first = index == 0 or parents[index - 1] != parent
            if first:
                block_start[parent] = index
                if points[index] != apply_matrix(matrix, previous_points[parent]):
                    raise AssertionError("viz inherited-anchor geometry drift", level)
                record = copy.deepcopy(previous_origins[parent])
                record["generation_lineage"].append({
                    "level": level,
                    "kind": "scaled-anchor",
                    "parent_path_index": parent,
                    "path_index": index,
                })
            else:
                if parent + 1 >= len(previous_origins):
                    raise AssertionError("viz connector has no right endpoint", level)
                ordinal = index - block_start[parent]
                record = {
                    "stable_id": f"connector:L{level}:G{parent}:I{ordinal}",
                    "origin_birth_level": level,
                    "origin_birth_gap": parent,
                    "origin_birth_rank": None,
                    "origin_interior_slot": ordinal,
                    "birth_parent_endpoint_stable_ids": [
                        previous_origins[parent]["stable_id"],
                        previous_origins[parent + 1]["stable_id"],
                    ],
                    "generation_lineage": [{
                        "level": level,
                        "kind": "connector-interior",
                        "owner_gap": parent,
                        "interior_ordinal": ordinal,
                        "path_index": index,
                    }],
                }
            current.append(record)
        stable_ids = [record["stable_id"] for record in current]
        if len(stable_ids) != len(set(stable_ids)):
            raise AssertionError("viz stable identities repeat", level)
        origins[level] = tuple(current)
    return points_by_level, origins


def selected_by_gap(records, gap_count, schedule, parent_word):
    selected = [None] * gap_count
    ranks = [None] * gap_count
    by_gap = [None] * gap_count
    for rank, record in enumerate(records):
        gap = schedule[rank]
        step = parent_word[gap]
        if (record.get("construction_rank"), record.get("gap"), record.get("step")) != (
            rank, gap, step
        ):
            raise AssertionError("selection schedule identity drift", rank)
        if selected[gap] is not None:
            raise AssertionError("gap selected twice", gap)
        selected[gap] = tuple(record["selected_word"])
        ranks[gap] = rank
        by_gap[gap] = record
    if any(word is None for word in selected):
        raise AssertionError("selection stream does not cover every gap")
    return tuple(selected), tuple(ranks), tuple(by_gap)


def replay_l5_owner_prefix(
    producer, context, source, parent_word, anchors, schedule, anchor_origins,
    deadline=None,
):
    """Replay the exact placed L5 state immediately before the owner action."""
    records = source["selection_records"]
    store = producer.rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    provenance = []
    for index, inherited in enumerate(anchor_origins):
        record = copy.deepcopy(inherited)
        record.update({
            "activation_kind": "preplaced-L5-anchor",
            "activation_rank": -1,
            "activation_anchor_index": index,
            "activation_gap": None,
            "activation_interior_slot": None,
        })
        provenance.append(record)

    for rank, selection in enumerate(records[:OWNER_L5_RANK]):
        if rank % 32 == 0:
            enforce_cooperative_limits(
                deadline, "replaying the chronological L5 owner prefix"
            )
        gap = schedule[rank]
        step = parent_word[gap]
        if (
            selection["construction_rank"],
            selection["gap"],
            selection["step"],
        ) != (rank, gap, step):
            raise AssertionError("L5 owner-prefix schedule drift", rank)
        block = context["blocks"][step]
        action_record = context["action_records"][step]
        ordinal = selection["first_survivor_ordinal_1_based"]
        if selection["domain_words"] != block["words"] or selection[
            "static_action_words"
        ] != action_record["zero"]["set_bits"]:
            raise AssertionError("L5 owner-prefix domain/action drift", rank)
        if not producer.l5_producer.action_accepts(
            context["bitset"], action_record, "zero", ordinal
        ):
            raise AssertionError("L5 owner-prefix winner lost zero-T", rank)
        word = producer.cache_word_at_offset(
            context["cache"], block, selection["cache_record_offset"]
        )
        if list(word) != selection["selected_word"]:
            raise AssertionError("L5 owner-prefix cache/selection drift", rank)
        start, target = anchors[gap], anchors[gap + 1]
        interiors = tuple(producer.rescue.word_interiors(start, word))
        if producer.rescue.endpoint(start, word) != target:
            raise AssertionError("L5 owner-prefix endpoint drift", rank)
        if not producer.l5_producer.intrinsic_projection_clean(
            start, target, interiors
        ) or not producer.l5_producer.global_projection_clean(
            interiors, yz_counts
        ):
            raise AssertionError("L5 owner-prefix projection drift", rank)
        if not producer.rescue.word_legal_fast(
            start, word, store, {}, producer.rescue.MENU
        ) or not producer.rescue.word_legal(
            start, word, store.pts, store.pset, {}
        ):
            raise AssertionError("L5 owner-prefix exact legality drift", rank)
        endpoint_ids = [
            anchor_origins[gap]["stable_id"],
            anchor_origins[gap + 1]["stable_id"],
        ]
        for slot, point in enumerate(interiors):
            provenance.append({
                "stable_id": f"alternate:L5:G{gap}:I{slot}",
                "origin_birth_level": 5,
                "origin_birth_gap": gap,
                "origin_birth_rank": rank,
                "origin_interior_slot": slot,
                "birth_parent_endpoint_stable_ids": endpoint_ids,
                "generation_lineage": [{
                    "level": 5,
                    "kind": "connector-interior",
                    "owner_gap": gap,
                    "owner_construction_rank": rank,
                    "interior_slot": slot,
                    "construction_order_index": len(provenance),
                }],
                "activation_kind": "L5-connector-interior",
                "activation_rank": rank,
                "activation_anchor_index": None,
                "activation_gap": gap,
                "activation_interior_slot": slot,
            })
            fibre = point[1:]
            if yz_counts[fibre]:
                raise AssertionError("L5 owner-prefix reuses yz fibre", rank)
            yz_counts[fibre] += 1
        store.add_many(interiors)
        if len(store.pts) != len(provenance):
            raise AssertionError("L5 owner-prefix provenance extent drift", rank)

    commitment = producer.l5_producer.prefix_commitment(
        store, yz_counts, records[:OWNER_L5_RANK], OWNER_L5_RANK
    )
    commitment = {
        **commitment,
        "level": 5,
        "point_provenance_stream_sha256": stable_hash(provenance),
        "recursive_origin_birth_histogram": {
            str(level): count for level, count in sorted(Counter(
                record["origin_birth_level"] for record in provenance
            ).items())
        },
    }
    return {
        "points": tuple(store.pts),
        "provenance": tuple(provenance),
        "yz_counts": Counter(yz_counts),
        "commitment": commitment,
    }


def build_l5_natural_ancestry(
    producer, context, args, l6_anchors, deadline=None,
):
    """Join recursive L0--L4 origins to the audited alternate L5 path."""
    with VIZ_PATH.open() as handle:
        viz = json.load(handle)
    points_by_level, origins = build_viz_origins(viz, producer.M_BAL3)
    enforce_cooperative_limits(deadline, "recovering recursive L0--L4 ancestry")
    base_word, base_anchors, base_schedule = producer.rescue.load_l5_state()
    base_word = tuple(base_word)
    base_anchors = tuple(tuple(point) for point in base_anchors)
    base_schedule = tuple(base_schedule)
    l4_points = points_by_level[4]
    l4_origins = origins[4]
    expected_l5_anchors = tuple(
        apply_matrix(producer.M_BAL3, point) for point in l4_points
    )
    if expected_l5_anchors != base_anchors or len(l4_origins) != len(base_anchors):
        raise AssertionError("recursive viz ancestry does not join L5 anchors")

    l5_source, l5_source_snapshot = producer.verify_parent_source(
        args.parent_source
    )
    l5_terminal, l5_terminal_snapshot = producer.verify_parent_terminal(
        args.parent_terminal, l5_source_snapshot
    )
    audited_parent = producer.reconstruct_ordered_parent(
        l5_source, l5_terminal
    )
    selected, ranks, records = selected_by_gap(
        l5_source["selection_records"], len(base_word), base_schedule, base_word
    )
    owner = records[OWNER_L5_GAP]
    if (
        ranks[OWNER_L5_GAP] != OWNER_L5_RANK
        or base_word[OWNER_L5_GAP] != OWNER_L5_STEP
        or selected[OWNER_L5_GAP] != OWNER_L5_WORD
        or owner["first_survivor_ordinal_1_based"] != OWNER_L5_ORDINAL
    ):
        raise AssertionError("frozen poison-blind L5 owner identity drift")

    anchor_origins = []
    for index, inherited in enumerate(l4_origins):
        record = copy.deepcopy(inherited)
        record["generation_lineage"].append({
            "level": 5,
            "kind": "scaled-anchor",
            "parent_path_index": index,
            "path_index": None,
        })
        anchor_origins.append(record)

    owner_prefix = replay_l5_owner_prefix(
        producer,
        context,
        l5_source,
        base_word,
        base_anchors,
        base_schedule,
        tuple(anchor_origins),
        deadline,
    )

    points = [base_anchors[0]]
    point_origins = [copy.deepcopy(anchor_origins[0])]
    point_origins[0]["generation_lineage"][-1]["path_index"] = 0
    gap_ancestry = []
    menu = tuple(producer.rescue.MENU)
    for gap, word in enumerate(selected):
        if gap % 64 == 0:
            enforce_cooperative_limits(
                deadline, "joining the audited natural L5 path to L6"
            )
        prefix = (0, 0, 0)
        owner_endpoint_ids = [
            anchor_origins[gap]["stable_id"],
            anchor_origins[gap + 1]["stable_id"],
        ]
        for slot, letter in enumerate(word):
            child_gap = len(points) - 1
            start = points[-1]
            next_prefix = add(prefix, menu[letter])
            end = add(base_anchors[gap], next_prefix)
            if slot + 1 < len(word):
                origin = {
                    "stable_id": f"alternate:L5:G{gap}:I{slot}",
                    "origin_birth_level": 5,
                    "origin_birth_gap": gap,
                    "origin_birth_rank": ranks[gap],
                    "origin_interior_slot": slot,
                    "birth_parent_endpoint_stable_ids": owner_endpoint_ids,
                    "generation_lineage": [{
                        "level": 5,
                        "kind": "connector-interior",
                        "owner_gap": gap,
                        "owner_construction_rank": ranks[gap],
                        "interior_slot": slot,
                        "path_index": len(points),
                    }],
                }
            else:
                if end != base_anchors[gap + 1]:
                    raise AssertionError("alternate L5 connector endpoint drift", gap)
                origin = copy.deepcopy(anchor_origins[gap + 1])
                origin["generation_lineage"][-1]["path_index"] = len(points)
            gap_ancestry.append({
                "L6_natural_gap": child_gap,
                "L5_owner_gap": gap,
                "L5_owner_construction_rank": ranks[gap],
                "L5_owner_step": base_word[gap],
                "actual_L5_selected_word": list(word),
                "actual_L5_selected_ordinal_1_based": records[gap][
                    "first_survivor_ordinal_1_based"
                ],
                "owner_slot": slot,
                "owner_prefix_before_slot": list(prefix),
                "child_step": letter,
                "start_stable_id": point_origins[-1]["stable_id"],
                "end_stable_id": origin["stable_id"],
                "start": list(start),
                "end": list(end),
            })
            points.append(end)
            point_origins.append(origin)
            prefix = next_prefix
    points = tuple(points)
    point_origins = tuple(point_origins)
    gap_ancestry = tuple(gap_ancestry)
    if points != tuple(audited_parent["points"]):
        raise AssertionError("recursive L5 natural path misses audited parent")
    expected_l6 = tuple(
        apply_matrix(producer.M_BAL3, point) for point in points
    )
    if expected_l6 != tuple(l6_anchors):
        raise AssertionError("recursive L5 path misses chronological L6 anchors")
    if len(gap_ancestry) != EXPECTED_L6_GAPS:
        raise AssertionError("L5-to-L6 natural gap ancestry extent drift")
    return {
        "L5_points": points,
        "L5_point_origins": point_origins,
        "L6_gap_ancestry": gap_ancestry,
        "L5_source_snapshot": l5_source_snapshot,
        "L5_terminal_snapshot": l5_terminal_snapshot,
        "recursive_origin_commitment": stable_hash(point_origins),
        "gap_ancestry_commitment": stable_hash(gap_ancestry),
        "L5_owner_prefix": owner_prefix,
        "L5_owner_selection": compact_selection_record(owner),
        "L5_owner_start": list(base_anchors[OWNER_L5_GAP]),
        "L5_owner_end": list(base_anchors[OWNER_L5_GAP + 1]),
        "viz_levels_recovered": len(points_by_level),
        "viz_oldest_birth_level": 0,
    }


def verify_final_l6_chain(producer, l6, source, terminal, deadline=None):
    schedule = tuple(l6["schedule"])
    parent_word = tuple(l6["parent_word"])
    selected, _ranks, _records = selected_by_gap(
        source["selection_records"], EXPECTED_L6_GAPS, schedule, parent_word
    )
    anchors = tuple(l6["anchors"])
    chain = [anchors[0]]
    flat_word = []
    for gap, word in enumerate(selected):
        if gap % 128 == 0:
            enforce_cooperative_limits(
                deadline, "reconstructing the terminal ordered L6 chain"
            )
        if producer.rescue.endpoint(anchors[gap], word) != anchors[gap + 1]:
            raise AssertionError("terminal L6 selected endpoint drift", gap)
        chain.extend(producer.rescue.word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != len(set(chain)):
        raise AssertionError("terminal L6 natural chain repeats a point")
    commitments = {
        "alternate_ordered_point_stream_sha256": point_stream_sha256(chain),
        "alternate_flat_step_word_sha256": hashlib.sha256(
            bytes(flat_word)
        ).hexdigest(),
        "final_point_set_sha256": stable_hash(sorted(chain)),
        "final_yz_occupancy_sha256": stable_hash(
            sorted(Counter(point[1:] for point in chain).items())
        ),
    }
    if commitments != {
        key: terminal["commitments"][key] for key in commitments
    }:
        raise AssertionError("reconstructed final L6/terminal commitment drift")
    if len(chain) != terminal["result"]["points"] or len(flat_word) != terminal[
        "result"
    ]["steps"]:
        raise AssertionError("reconstructed final L6 terminal extent drift")
    return {
        "points": len(chain),
        "steps": len(flat_word),
        **commitments,
    }


def prefix_commitment(producer, store, yz_counts, records, rank, provenance):
    commitment = producer.prefix_commitment(store, yz_counts, records, rank)
    return {
        **commitment,
        "point_provenance_stream_sha256": stable_hash(provenance),
        "recursive_origin_birth_histogram": {
            str(level): count for level, count in sorted(Counter(
                record["origin_birth_level"] for record in provenance
            ).items())
        },
    }


def replay_prefix_panel(
    producer, context, source, ancestry, target_ranks, deadline=None,
):
    l6 = context["l6"]
    anchors = tuple(l6["anchors"])
    schedule = tuple(l6["schedule"])
    parent_word = tuple(l6["parent_word"])
    records = source["selection_records"]
    geometry_boundaries = set(target_ranks)
    geometry_boundaries.update(rank + 1 for rank in target_ranks)
    requested_boundaries = {0, *geometry_boundaries}
    for rank in target_ranks:
        requested_boundaries.update(
            value for value in (rank - 1, rank, rank + 1, rank + 2)
            if 0 <= value <= EXPECTED_L6_GAPS
        )
    maximum_boundary = max(requested_boundaries)

    l6_anchor_provenance = []
    for index, inherited in enumerate(ancestry["L5_point_origins"]):
        record = copy.deepcopy(inherited)
        record["generation_lineage"].append({
            "level": 6,
            "kind": "scaled-anchor",
            "parent_path_index": index,
            "path_index": index,
        })
        record.update({
            "activation_kind": "preplaced-L6-anchor",
            "activation_rank": -1,
            "activation_anchor_index": index,
            "activation_gap": None,
            "activation_interior_slot": None,
        })
        l6_anchor_provenance.append(record)

    store = producer.rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    provenance = list(l6_anchor_provenance)
    snapshots = {}
    boundaries = {}

    def capture(rank):
        enforce_cooperative_limits(
            deadline, "capturing an exact chronological L6 boundary"
        )
        if rank not in requested_boundaries:
            raise AssertionError("unrequested L6 boundary capture")
        commitment = prefix_commitment(
            producer, store, yz_counts, records[:rank], rank, provenance
        )
        boundaries[rank] = commitment
        if rank in geometry_boundaries:
            snapshots[rank] = {
                "points": tuple(store.pts),
                # Provenance records are append-only and never mutated after
                # insertion.  Boundary tuples can therefore share the immutable
                # record objects instead of multiplying the full recursive
                # ancestry seven times in resident memory.
                "provenance": tuple(provenance),
                "yz_counts": Counter(yz_counts),
                "commitment": commitment,
            }

    for rank in range(maximum_boundary + 1):
        if rank % 32 == 0:
            enforce_cooperative_limits(
                deadline, "replaying the chronological L6 prefix panel"
            )
        if rank in requested_boundaries:
            capture(rank)
        if rank == maximum_boundary:
            break
        record = records[rank]
        gap = schedule[rank]
        step = parent_word[gap]
        if (record["construction_rank"], record["gap"], record["step"]) != (
            rank, gap, step
        ):
            raise AssertionError("L6 prefix schedule drift", rank)
        block = context["blocks"][step]
        action_record = context["action_records"][step]
        ordinal = record["first_survivor_ordinal_1_based"]
        if record["domain_words"] != block["words"] or record[
            "static_action_words"
        ] != action_record["zero"]["set_bits"]:
            raise AssertionError("L6 prefix domain/action extent drift", rank)
        if not producer.l5_producer.action_accepts(
            context["bitset"], action_record, "zero", ordinal
        ):
            raise AssertionError("L6 prefix winner lost zero-T membership", rank)
        word = producer.cache_word_at_offset(
            context["cache"], block, record["cache_record_offset"]
        )
        if list(word) != record["selected_word"]:
            raise AssertionError("L6 prefix winner/cache drift", rank)
        start, target = anchors[gap], anchors[gap + 1]
        interiors = tuple(producer.rescue.word_interiors(start, word))
        if producer.rescue.endpoint(start, word) != target:
            raise AssertionError("L6 prefix winner endpoint drift", rank)
        if not producer.l5_producer.intrinsic_projection_clean(
            start, target, interiors
        ) or not producer.l5_producer.global_projection_clean(
            interiors, yz_counts
        ):
            raise AssertionError("L6 prefix winner projection drift", rank)
        memo = {}
        if not producer.rescue.word_legal_fast(
            start, word, store, memo, producer.rescue.MENU
        ) or not producer.rescue.word_legal(
            start, word, store.pts, store.pset, {}
        ):
            raise AssertionError("L6 prefix winner exact legality drift", rank)
        endpoint_ids = [
            l6_anchor_provenance[gap]["stable_id"],
            l6_anchor_provenance[gap + 1]["stable_id"],
        ]
        for slot, point in enumerate(interiors):
            provenance.append({
                "stable_id": f"alternate:L6:G{gap}:I{slot}",
                "origin_birth_level": 6,
                "origin_birth_gap": gap,
                "origin_birth_rank": rank,
                "origin_interior_slot": slot,
                "birth_parent_endpoint_stable_ids": endpoint_ids,
                "generation_lineage": [{
                    "level": 6,
                    "kind": "connector-interior",
                    "owner_gap": gap,
                    "owner_construction_rank": rank,
                    "interior_slot": slot,
                    "construction_order_index": len(provenance),
                }],
                "activation_kind": "L6-connector-interior",
                "activation_rank": rank,
                "activation_anchor_index": None,
                "activation_gap": gap,
                "activation_interior_slot": slot,
            })
            fibre = point[1:]
            if yz_counts[fibre]:
                raise AssertionError("L6 prefix replay reuses yz fibre", rank)
            yz_counts[fibre] += 1
        store.add_many(interiors)
        if len(store.pts) != len(provenance):
            raise AssertionError("L6 prefix point/provenance extent drift", rank)

    if set(snapshots) != geometry_boundaries:
        raise AssertionError("failed to capture every L6 pre/post prefix")
    return snapshots, boundaries, tuple(l6_anchor_provenance)


def compact_selection_record(record):
    keys = (
        "construction_rank",
        "gap",
        "step",
        "domain_words",
        "static_action_words",
        "first_survivor_ordinal_1_based",
        "cache_record_offset",
        "selected_word",
    )
    result = {key: record[key] for key in keys}
    result["source_record_sha256"] = stable_hash(record)
    result["selected_word_sha256"] = hashlib.sha256(
        bytes(record["selected_word"])
    ).hexdigest()
    return result


def build_probe_panel(producer, context, source, ancestry, deadline=None):
    l6 = context["l6"]
    schedule = tuple(l6["schedule"])
    inverse = [None] * len(schedule)
    for rank, gap in enumerate(schedule):
        if inverse[gap] is not None:
            raise AssertionError("L6 schedule is not a permutation")
        inverse[gap] = rank
    if any(rank is None for rank in inverse):
        raise AssertionError("L6 inverse schedule is incomplete")
    target_ranks = tuple(inverse[gap] for gap in OWNER_L6_GAPS)
    snapshots, boundaries, anchor_provenance = replay_prefix_panel(
        producer, context, source, ancestry, target_ranks, deadline
    )

    parent_block = context["blocks"][OWNER_L5_STEP]
    if parent_block["words"] > 50_000:
        raise AssertionError("L5 owner domain cap drift")
    parent_probe_id = (
        f"chronological-L5-G{OWNER_L5_GAP}-R{OWNER_L5_RANK}-parent-pre"
    )
    parent_probe = {
        "probe_id": parent_probe_id,
        "level": 5,
        "natural_gap": OWNER_L5_GAP,
        "target_action_rank": OWNER_L5_RANK,
        "observation_boundary_rank": OWNER_L5_RANK,
        "construction_rank": OWNER_L5_RANK,
        "prefix_position": "before-target-action",
        "same_corridor_comparison_role": "L5-parent-only",
        "selection_check": "audited-first-survivor",
        "step": OWNER_L5_STEP,
        "start": ancestry["L5_owner_start"],
        "end": ancestry["L5_owner_end"],
        "domain_words": parent_block["words"],
        "domain_block_sha256": parent_block["encoded_block_sha256"],
        "owner_ancestry": {
            "L5_owner_gap": OWNER_L5_GAP,
            "L5_owner_construction_rank": OWNER_L5_RANK,
            "L5_owner_step": OWNER_L5_STEP,
            "actual_L5_selected_word": list(OWNER_L5_WORD),
        },
        "actual_selection": ancestry["L5_owner_selection"],
        "prefix_commitment": ancestry["L5_owner_prefix"]["commitment"],
    }
    probes = [parent_probe]
    point_sets = {parent_probe_id: ancestry["L5_owner_prefix"]}
    same_corridor_pairs = []
    adjacent_action_contexts = []
    gap_ancestry = ancestry["L6_gap_ancestry"]
    for owner_slot, (gap, rank) in enumerate(zip(OWNER_L6_GAPS, target_ranks)):
        owner = gap_ancestry[gap]
        if (
            owner["L5_owner_gap"] != OWNER_L5_GAP
            or owner["L5_owner_construction_rank"] != OWNER_L5_RANK
            or tuple(owner["actual_L5_selected_word"]) != OWNER_L5_WORD
            or owner["owner_slot"] != owner_slot
            or owner["child_step"] != OWNER_L5_WORD[owner_slot]
        ):
            raise AssertionError("owner-descendant ancestry drift", owner_slot)
        selected = source["selection_records"][rank]
        block = context["blocks"][owner["child_step"]]
        if block["words"] > 50_000:
            raise AssertionError("owner-descendant domain cap drift", gap)
        base_id = f"chronological-L6-G{gap}-R{rank}-S{owner_slot}"
        pre_probe = {
            "probe_id": base_id + "-pre",
            "level": 6,
            "natural_gap": gap,
            "target_action_rank": rank,
            "observation_boundary_rank": rank,
            "construction_rank": rank,
            "prefix_position": "before-target-action",
            "same_corridor_comparison_role": "pre",
            "selection_check": "audited-first-survivor",
            "step": owner["child_step"],
            "start": list(l6["anchors"][gap]),
            "end": list(l6["anchors"][gap + 1]),
            "domain_words": block["words"],
            "domain_block_sha256": block["encoded_block_sha256"],
            "owner_ancestry": owner,
            "actual_selection": compact_selection_record(selected),
            "prefix_commitment": snapshots[rank]["commitment"],
        }
        post_probe = {
            **pre_probe,
            "probe_id": base_id + "-post",
            "observation_boundary_rank": rank + 1,
            "construction_rank": rank + 1,
            "prefix_position": "after-target-action",
            "same_corridor_comparison_role": "post",
            "selection_check": "selected-word-killed-after-placement",
            "prefix_commitment": snapshots[rank + 1]["commitment"],
        }
        probes.extend((pre_probe, post_probe))
        point_sets[pre_probe["probe_id"]] = snapshots[rank]
        point_sets[post_probe["probe_id"]] = snapshots[rank + 1]
        same_corridor_pairs.append({
            "pair_id": base_id,
            "pre_probe_id": pre_probe["probe_id"],
            "post_probe_id": post_probe["probe_id"],
            "target_rank": rank,
            "target_natural_gap": gap,
            "step": owner["child_step"],
            "domain_words": block["words"],
            "domain_block_sha256": block["encoded_block_sha256"],
            "same_corridor_and_raw_ordinal_domain": True,
            "prefix_before": boundaries[rank],
            "prefix_after": boundaries[rank + 1],
            "target_action": compact_selection_record(selected),
        })
        adjacent = []
        for action_rank, role in (
            (rank - 1, "incoming-predecessor"),
            (rank, "target-action"),
            (rank + 1, "outgoing-successor"),
        ):
            if not 0 <= action_rank < EXPECTED_L6_GAPS:
                continue
            record = source["selection_records"][action_rank]
            adjacent_gap = schedule[action_rank]
            adjacent.append({
                "role": role,
                "action": compact_selection_record(record),
                "gap_ancestry": gap_ancestry[adjacent_gap],
                "prefix_before": boundaries[action_rank],
                "prefix_after": boundaries[action_rank + 1],
            })
        adjacent_action_contexts.append({
            "pair_id": base_id,
            "target_rank": rank,
            "target_natural_gap": gap,
            "rank_adjacency_is_literal_in_single_L6_schedule": True,
            "adjacent_actions": adjacent,
            "adjacent_action_context_sha256": stable_hash(adjacent),
        })
    for pair in same_corridor_pairs:
        pair["pair_record_sha256"] = stable_hash(pair)
    point_set_commitments = {
        probe_id: snapshot["commitment"]
        for probe_id, snapshot in point_sets.items()
    }
    return (
        tuple(probes),
        point_sets,
        tuple(same_corridor_pairs),
        tuple(adjacent_action_contexts),
        point_set_commitments,
        anchor_provenance,
    )


def build_inputs(args, deadline=None):
    producer = salvage = producer_context = None
    try:
        (
            producer,
            salvage,
            producer_context,
            source,
            terminal,
            snapshots,
        ) = load_authorities(args, deadline)
        enforce_cooperative_limits(deadline, "loading pinned authorities")
        final_l6 = verify_final_l6_chain(
            producer, producer_context["l6"], source, terminal, deadline
        )
        ancestry = build_l5_natural_ancestry(
            producer,
            producer_context,
            args,
            producer_context["l6"]["anchors"],
            deadline,
        )
        (
            probes,
            point_sets,
            same_corridor_pairs,
            adjacent_action_contexts,
            point_set_commitments,
            anchor_provenance,
        ) = build_probe_panel(
            producer, producer_context, source, ancestry, deadline
        )
        enforce_cooperative_limits(deadline, "sealing the v2 probe panel")
        static = {
            "schema_version": SCHEMA_VERSION,
            "checker_sha256": PROCESS_START_CHECKER_SHA256,
            "terminal_pin_block": terminal_pin_block(),
            "inputs": snapshots,
            "producer_verified_input_sha256": producer_context[
                "input_sha256"
            ],
            "L6_static_state": producer_context["l6"]["static"],
            "L6_terminal_result_commitments": final_l6,
            "L5_source_snapshot": ancestry["L5_source_snapshot"],
            "L5_terminal_snapshot": ancestry["L5_terminal_snapshot"],
            "recursive_ancestry": {
                "oldest_exact_birth_level": ancestry[
                    "viz_oldest_birth_level"
                ],
                "viz_levels_recovered": ancestry["viz_levels_recovered"],
                "L5_point_origin_stream_sha256": ancestry[
                    "recursive_origin_commitment"
                ],
                "L5_to_L6_gap_ancestry_stream_sha256": ancestry[
                    "gap_ancestry_commitment"
                ],
                "L6_anchor_provenance_stream_sha256": stable_hash(
                    anchor_provenance
                ),
            },
            "probe_selection": {
                "rule": (
                    "the immutable v1 poison-blind owner G93/R1934, followed "
                    "only through its four actual selected-word slots; the "
                    "L5 parent is recomputed at its exact chronological prefix, "
                    "and each L6 corridor is scanned immediately before and "
                    "after its actual action"
                ),
                "poison_results_consulted": False,
                "owner_L5_gap": OWNER_L5_GAP,
                "owner_L5_rank": OWNER_L5_RANK,
                "owner_L5_step": OWNER_L5_STEP,
                "owner_L5_word": list(OWNER_L5_WORD),
                "owner_L6_natural_gaps": list(OWNER_L6_GAPS),
            },
            "probe_records": list(probes),
            "probe_record_stream_sha256": stable_hash(probes),
            "same_corridor_pre_post_records": list(same_corridor_pairs),
            "same_corridor_pre_post_record_stream_sha256": stable_hash(
                same_corridor_pairs
            ),
            "adjacent_action_context_records": list(adjacent_action_contexts),
            "adjacent_action_context_stream_sha256": stable_hash(
                adjacent_action_contexts
            ),
            "point_set_commitments": point_set_commitments,
            "word_mask_encoding": {
                "encoding": "fixed-width-little-endian-byte-hex",
                "ordinal_rule": "domain ordinal i+1 is bit i",
                "raw_bytes_in_terminal_artifact": True,
                "populations_or_hashes_used_as_mask_substitutes": False,
            },
            "cross_probe_comparability_policy": {
                "bitwise_raw_mask_comparison_permitted_only_for": (
                    "the pre/post pair of one identical L6 corridor with the "
                    "same step, cache block, domain size, and ordinal semantics"
                ),
                "parent_to_child_raw_mask_projection": None,
                "reason": (
                    "different step domains have no proved canonical map between "
                    "connector words or ordinal bits"
                ),
                "parent_to_child_comparison": (
                    "exact populations, rational normalized populations, "
                    "semantic descriptor spectra, and commitments only"
                ),
            },
            "local_radius": LOCAL_RADIUS,
            "spatial_shell_definition": (
                "shell 0 is Chebyshev distance<=40 from the integer corridor "
                "midpoint; shell j>=1 has 40*3^(j-1)<d<=40*3^j"
            ),
            "chronological_birth_shell_definition": (
                "preplaced anchors are cohort inherited at the observed level; "
                "a placed same-level interior at rank b has shell of "
                "observation_boundary_rank-b in powers of 3"
            ),
            "channels": list(CHANNELS),
            "explicit_scope_limitations": [
                "five corridors only: one L5 parent and four actual L6 children",
                "only the four L6 same-corridor pre/post pairs have comparable raw masks",
                "adjacent action context is chronology metadata, not an abstract-state transition relation",
                "no repeated-state quotient, closure test, contraction, or tail theorem is asserted",
                "preplaced inherited endpoints have recursive origin levels but no within-level activation rank",
            ],
        }
        static["static_state_sha256"] = stable_hash(static)
        return static, {
            "producer": producer,
            "salvage": salvage,
            "producer_context": producer_context,
            "source": source,
            "terminal": terminal,
            "probes": probes,
            "point_sets": point_sets,
            "same_corridor_pairs": same_corridor_pairs,
            "adjacent_action_contexts": adjacent_action_contexts,
        }
    except BaseException:
        if producer_context is not None and producer is not None:
            producer.close_context(producer_context)
        raise


def close_inputs(context):
    context["producer"].close_context(context["producer_context"])


def load_domain(cache, block):
    cursor = block["start"]
    digest = hashlib.sha256()
    words = []
    for ordinal in range(1, block["words"] + 1):
        if cursor >= block["end"]:
            raise AssertionError("truncated compact domain", block["step"], ordinal)
        length = cache[cursor]
        end = cursor + 1 + length
        if not 1 <= length <= 255 or end > block["end"]:
            raise AssertionError("compact domain word boundary drift")
        encoded = bytes(cache[cursor:end])
        digest.update(encoded)
        words.append(tuple(encoded[1:]))
        cursor = end
    if cursor != block["end"] or digest.hexdigest() != block[
        "encoded_block_sha256"
    ]:
        raise AssertionError("compact domain block commitment drift", block["step"])
    return tuple(words)


def general_position(points):
    if len(points) != len(set(points)):
        return False
    for cursor, point in enumerate(points):
        directions = set()
        for prior in points[:cursor]:
            direction = primitive(subtract(prior, point))
            if direction in directions:
                return False
            directions.add(direction)
    return True


def intrinsic_domain_recheck(producer, domain, model, probe):
    """Recheck endpoint, self-geometry, projection, and atom incidence."""
    start = tuple(probe["start"])
    target = tuple(probe["end"])
    origin = (0, 0, 0)
    expected_displacement = subtract(target, start)
    intrinsic_bits = 0
    length_histogram = Counter()
    for word_index, word in enumerate(domain):
        if any(not 0 <= letter < EXPECTED_MENU_SIZE for letter in word):
            raise AssertionError("domain word has invalid menu letter", word_index)
        if subtract(producer.rescue.endpoint(start, word), start) != (
            expected_displacement
        ):
            raise AssertionError("domain word endpoint drift", word_index)
        interiors = tuple(producer.rescue.word_interiors(start, word))
        if not general_position((start, *interiors, target)):
            raise AssertionError("domain word has intrinsic collinearity", word_index)
        offsets = tuple(producer.rescue.word_interiors(origin, word))
        expected_atoms = set()
        for offset in offsets:
            if offset not in model["site_id"]:
                raise AssertionError("domain site atom missing", word_index)
            expected_atoms.add(model["site_id"][offset])
        for left, first in enumerate(offsets):
            for second in offsets[left + 1:]:
                key = line_key(first, second)
                if key not in model["line_id"]:
                    raise AssertionError("domain line atom missing", word_index)
                expected_atoms.add(model["line_id"][key])
        if tuple(sorted(expected_atoms)) != tuple(model["word_atoms"][word_index]):
            raise AssertionError("domain atom incidence drift", word_index)
        if producer.l5_producer.intrinsic_projection_clean(
            start, target, interiors
        ):
            intrinsic_bits |= 1 << word_index
        length_histogram[len(word)] += 1
    return intrinsic_bits, {
        "words_rechecked": len(domain),
        "every_endpoint_exact": True,
        "every_word_internally_general_position": True,
        "every_word_atom_incidence_reconstructed": True,
        "intrinsic_projection_clean_words": intrinsic_bits.bit_count(),
        "word_length_histogram": {
            str(length): count for length, count in sorted(length_histogram.items())
        },
    }


def load_probe_domain_model(context, probe):
    producer_context = context["producer_context"]
    block = producer_context["blocks"][probe["step"]]
    domain = load_domain(producer_context["cache"], block)
    if len(domain) != probe["domain_words"]:
        raise AssertionError("probe domain extent drift")
    model = context["salvage"].build_domain_model(domain)
    intrinsic_bits, recheck = intrinsic_domain_recheck(
        context["producer"], domain, model, probe
    )
    return domain, model, intrinsic_bits, recheck


def endpoint_profile(provenance, point, point_index, target_rank, distance):
    activation_rank = provenance["activation_rank"]
    if activation_rank == -1:
        relation = "preplaced-inherited-anchor-at-observed-level"
        delta = None
        shell = "inherited"
    else:
        if not 0 <= activation_rank < target_rank:
            raise AssertionError("prefix contains a nonpast activation")
        relation = "earlier-same-level-connector"
        delta = target_rank - activation_rank
        shell = rank_shell(delta)
    return {
        "point_index": point_index,
        "coordinate": list(point),
        "stable_id": provenance["stable_id"],
        "activation_kind": provenance["activation_kind"],
        "activation_rank": activation_rank,
        "activation_anchor_index": provenance["activation_anchor_index"],
        "activation_gap": provenance["activation_gap"],
        "activation_interior_slot": provenance["activation_interior_slot"],
        "observation_boundary_rank_distance": delta,
        "observation_boundary_rank": target_rank,
        "chronological_birth_shell": shell,
        "origin_birth_level": provenance["origin_birth_level"],
        "origin_birth_gap": provenance["origin_birth_gap"],
        "origin_birth_rank": provenance["origin_birth_rank"],
        "origin_interior_slot": provenance["origin_interior_slot"],
        "birth_parent_endpoint_stable_ids": provenance[
            "birth_parent_endpoint_stable_ids"
        ],
        "generation_lineage": provenance["generation_lineage"],
        "recursive_provenance_sha256": stable_hash(provenance),
        "exact_spatial_distance": distance,
        "spatial_shell": spatial_shell(distance),
    }


def point_profiles(points, provenance, target_rank, center):
    if len(points) != len(provenance):
        raise AssertionError("point/provenance extent drift")
    distances = tuple(chebyshev(point, center) for point in points)
    profiles = tuple(
        endpoint_profile(record, point, index, target_rank, distance)
        for index, (point, record, distance) in enumerate(
            zip(points, provenance, distances)
        )
    )
    return distances, profiles


def witness_descriptor(channel, profiles):
    maximum_spatial = max(profile["spatial_shell"] for profile in profiles)
    latest_activation = max(profile["activation_rank"] for profile in profiles)
    target_ranks = {
        profile["observation_boundary_rank"] for profile in profiles
    }
    if len(target_ranks) != 1:
        raise AssertionError("witness endpoint target-rank disagreement")
    target_rank = next(iter(target_ranks))
    if latest_activation == -1:
        birth_relation = "inherited-before-observed-level-construction"
        birth_shell = "inherited"
    else:
        birth_relation = "same-level-connector-born-secant-or-obstruction"
        birth_shell = rank_shell(target_rank - latest_activation)
    return {
        "channel": channel,
        "locality": "near/local" if maximum_spatial == 0 else "far-involved",
        "maximum_spatial_shell": maximum_spatial,
        "obstruction_birth_relation": birth_relation,
        "obstruction_birth_rank_shell": birth_shell,
        "endpoint_origin_birth_levels": sorted({
            profile["origin_birth_level"] for profile in profiles
        }),
        "endpoint_activation_relations": sorted({
            profile["activation_kind"] for profile in profiles
        }),
    }


def initial_accumulator():
    return {
        "full_atom_mask": 0,
        "near_atom_mask": 0,
        "far_atom_mask": 0,
        "channel_atom_masks": {channel: 0 for channel in CHANNELS},
        "birth_descriptor_atom_masks": {},
        "birth_descriptor_records": {},
        "witness_records": [],
        "witness_hash_chain": "0" * 64,
    }


def record_witness(accumulator, atom, descriptor, witness):
    descriptor_key = json.dumps(
        descriptor, sort_keys=True, separators=(",", ":")
    )
    bit = 1 << atom
    accumulator["full_atom_mask"] |= bit
    accumulator["channel_atom_masks"][descriptor["channel"]] |= bit
    if descriptor["locality"] == "near/local":
        accumulator["near_atom_mask"] |= bit
    else:
        accumulator["far_atom_mask"] |= bit
    accumulator["birth_descriptor_atom_masks"][descriptor_key] = (
        accumulator["birth_descriptor_atom_masks"].get(descriptor_key, 0) | bit
    )
    previous = accumulator["birth_descriptor_records"].setdefault(
        descriptor_key, descriptor
    )
    if previous != descriptor:
        raise AssertionError("birth descriptor key collision")
    record = {
        "witness_sequence_0_based": len(accumulator["witness_records"]),
        "poisoned_atom_id": atom,
        "birth_shell_descriptor_sha256": hashlib.sha256(
            descriptor_key.encode("utf-8")
        ).hexdigest(),
        **witness,
    }
    record["witness_record_sha256"] = stable_hash(record)
    accumulator["witness_records"].append(record)
    accumulator["witness_hash_chain"] = hash_chain(
        accumulator["witness_hash_chain"], record
    )


def scan_site_unit(start, points, profiles, site_record, accumulator):
    offset, atom = site_record
    candidate = add(start, offset)
    seen = {}
    for point_index, point in enumerate(points):
        if point == candidate:
            endpoint = profiles[point_index]
            descriptor = witness_descriptor("collision", (endpoint,))
            record_witness(accumulator, atom, descriptor, {
                "channel": "collision",
                "candidate_site": list(candidate),
                "candidate_offset": list(offset),
                "old_endpoints": [endpoint],
                "exact_line": None,
            })
            continue
        direction = primitive(subtract(point, candidate))
        previous = seen.get(direction)
        if previous is None:
            seen[direction] = point_index
            continue
        if isinstance(previous, tuple):
            raise AssertionError("placed prefix contains three collinear points")
        seen[direction] = (previous, point_index)
        endpoint_profiles = (profiles[previous], profiles[point_index])
        moment = cross(candidate, direction)
        if cross(points[previous], direction) != moment or cross(
            points[point_index], direction
        ) != moment:
            raise AssertionError("old-old secant moment reconstruction drift")
        descriptor = witness_descriptor("old-old-new", endpoint_profiles)
        record_witness(accumulator, atom, descriptor, {
            "channel": "old-old-new",
            "candidate_site": list(candidate),
            "candidate_offset": list(offset),
            "old_endpoints": list(endpoint_profiles),
            "exact_line": {
                "primitive_direction": list(direction),
                "integer_moment_cross_point_direction": list(moment),
            },
        })


def scan_old_point_unit(start, points, profiles, point_index, directions,
                        accumulator):
    point = points[point_index]
    relative = subtract(point, start)
    endpoint = profiles[point_index]
    for direction, by_moment in directions:
        relative_moment = cross(relative, direction)
        atom = by_moment.get(relative_moment)
        if atom is None:
            continue
        absolute_moment = cross(point, direction)
        translated = add(cross(start, direction), relative_moment)
        if absolute_moment != translated:
            raise AssertionError("candidate line moment translation drift")
        descriptor = witness_descriptor("old-new-new", (endpoint,))
        record_witness(accumulator, atom, descriptor, {
            "channel": "old-new-new",
            "candidate_site": None,
            "candidate_offset": None,
            "old_endpoints": [endpoint],
            "exact_line": {
                "primitive_direction": list(direction),
                "relative_integer_moment": list(relative_moment),
                "absolute_integer_moment_cross_point_direction": list(
                    absolute_moment
                ),
                "corridor_start": list(start),
            },
        })


def build_atom_word_bits(model, domain_size):
    if len(model["word_atoms"]) != domain_size:
        raise AssertionError("domain/model word census drift")
    result = [0] * len(model["atom_desc"])
    for word_index, atoms in enumerate(model["word_atoms"]):
        bit = 1 << word_index
        for atom in atoms:
            if not 0 <= atom < len(result):
                raise AssertionError("word references atom outside universe")
            result[atom] |= bit
    return tuple(result)


def atom_mask_to_word_mask(atom_mask, atom_word_bits):
    result = 0
    remaining = atom_mask
    while remaining:
        lowest = remaining & -remaining
        atom = lowest.bit_length() - 1
        if not 0 <= atom < len(atom_word_bits):
            raise AssertionError("poison mask has atom outside universe")
        result |= atom_word_bits[atom]
        remaining ^= lowest
    return result


def zero_t_word_mask(context, probe, domain_size):
    action = context["producer_context"]["action_records"][probe["step"]]
    record = action["zero"]
    byte_count = (domain_size + 7) // 8
    start = record["offset"]
    encoded = bytes(
        context["producer_context"]["bitset"][start:start + byte_count]
    )
    bits = int.from_bytes(encoded, "little")
    if bits & ~full_mask(domain_size):
        raise AssertionError("zero-T bitset has nonzero padding")
    if bits.bit_count() != record["set_bits"]:
        raise AssertionError("zero-T bitset population drift")
    return bits


def global_yz_word_mask(producer, domain, probe, yz_counts):
    start = tuple(probe["start"])
    result = 0
    for word_index, word in enumerate(domain):
        interiors = tuple(producer.rescue.word_interiors(start, word))
        if producer.l5_producer.global_projection_clean(interiors, yz_counts):
            result |= 1 << word_index
    return result


def first_member_ordinal(bits):
    if not bits:
        return None
    return (bits & -bits).bit_length()


def mask_vector_hash(records):
    return stable_hash([
        {
            "name": name,
            "sha256": record["sha256"],
            "bit_count": record["bit_count"],
            "members": record["members"],
        }
        for name, record in records
    ])


def finalize_probe(context, probe, domain, model, intrinsic_bits,
                   domain_recheck, points, provenance, yz_counts, distances,
                   accumulator):
    producer = context["producer"]
    domain_size = len(domain)
    atom_count = len(model["atom_desc"])
    atom_word_bits = build_atom_word_bits(model, domain_size)
    universe = full_mask(domain_size)

    full_atom = accumulator["full_atom_mask"]
    full_word = atom_mask_to_word_mask(full_atom, atom_word_bits)
    near_word = atom_mask_to_word_mask(
        accumulator["near_atom_mask"], atom_word_bits
    )
    far_word = atom_mask_to_word_mask(
        accumulator["far_atom_mask"], atom_word_bits
    )
    if near_word | far_word != full_word:
        raise AssertionError("near/far word OR does not equal geometric poison")

    channel_words = {
        channel: atom_mask_to_word_mask(
            accumulator["channel_atom_masks"][channel], atom_word_bits
        )
        for channel in CHANNELS
    }
    channel_union = 0
    for channel in CHANNELS:
        channel_union |= channel_words[channel]
    if channel_union != full_word:
        raise AssertionError("channel OR does not equal geometric poison")

    descriptor_records = []
    descriptor_atom_union = 0
    descriptor_word_union = 0
    for key in sorted(accumulator["birth_descriptor_atom_masks"]):
        atom_bits = accumulator["birth_descriptor_atom_masks"][key]
        word_bits = atom_mask_to_word_mask(atom_bits, atom_word_bits)
        descriptor_atom_union |= atom_bits
        descriptor_word_union |= word_bits
        descriptor_records.append({
            "descriptor": accumulator["birth_descriptor_records"][key],
            "descriptor_sha256": hashlib.sha256(
                key.encode("utf-8")
            ).hexdigest(),
            "poisoned_atom_mask": raw_mask(atom_bits, atom_count),
            "killed_word_mask": raw_mask(word_bits, domain_size),
        })
    if descriptor_atom_union != full_atom or descriptor_word_union != full_word:
        raise AssertionError("birth descriptor OR misses geometric poison")

    zero_bits = zero_t_word_mask(context, probe, domain_size)
    global_yz_bits = global_yz_word_mask(
        producer, domain, probe, yz_counts
    )
    if global_yz_bits & ~intrinsic_bits:
        raise AssertionError("global-yz clean mask is not intrinsic subset")
    geometric_bits = universe & ~full_word
    combined_bits = zero_bits & intrinsic_bits & global_yz_bits & geometric_bits

    selected = probe["actual_selection"]
    ordinal = selected["first_survivor_ordinal_1_based"]
    if not 1 <= ordinal <= domain_size:
        raise AssertionError("stored target-action ordinal outside domain")
    selected_bit = 1 << (ordinal - 1)
    if domain[ordinal - 1] != tuple(selected["selected_word"]):
        raise AssertionError("stored target-action/domain ordinal drift")
    predicate_memberships = {
        "zero_T": bool(zero_bits & selected_bit),
        "intrinsic": bool(intrinsic_bits & selected_bit),
        "global_yz": bool(global_yz_bits & selected_bit),
        "geometric": bool(geometric_bits & selected_bit),
        "combined": bool(combined_bits & selected_bit),
    }
    first_combined = first_member_ordinal(combined_bits)
    store = producer.rescue.Store(points)
    selected_word = tuple(selected["selected_word"])
    fast_legal = producer.rescue.word_legal_fast(
        tuple(probe["start"]), selected_word, store, {}, producer.rescue.MENU
    )
    reference_legal = producer.rescue.word_legal(
        tuple(probe["start"]), selected_word, store.pts, store.pset, {}
    )
    if fast_legal != reference_legal:
        raise AssertionError("v2 fast/reference target-action disagreement")
    selection_check = probe["selection_check"]
    if selection_check == "audited-first-survivor":
        if not all(predicate_memberships.values()) or not fast_legal:
            raise AssertionError(
                "audited target action is absent from a pre-state predicate"
            )
        if first_combined != ordinal:
            raise AssertionError(
                "v2 exact pre-state mask disagrees with audited first survivor",
                first_combined,
                ordinal,
            )
        selection_assertion = {
            "kind": selection_check,
            "is_first_member_of_exact_combined_mask": True,
            "expected_geometric_legality": True,
        }
    elif selection_check == "selected-word-killed-after-placement":
        if len(selected_word) < 2:
            raise AssertionError("post-state target action has no interior")
        expected = {
            "zero_T": True,
            "intrinsic": True,
            "global_yz": False,
            "geometric": False,
            "combined": False,
        }
        if predicate_memberships != expected or fast_legal:
            raise AssertionError(
                "placed target action is not exactly killed in its post-state",
                predicate_memberships,
            )
        selection_assertion = {
            "kind": selection_check,
            "is_first_member_of_exact_combined_mask": False,
            "first_combined_ordinal_1_based": first_combined,
            "expected_geometric_legality": False,
        }
    else:
        raise AssertionError("unknown target-action selection check")

    predicate_pairs = {
        "zero_T": allowed_killed_pair(zero_bits, domain_size),
        "intrinsic": allowed_killed_pair(intrinsic_bits, domain_size),
        "global_yz": allowed_killed_pair(global_yz_bits, domain_size),
        "geometric": allowed_killed_pair(geometric_bits, domain_size),
        "combined": allowed_killed_pair(combined_bits, domain_size),
    }
    reason_masks = {
        "zero_T_incompatible": raw_mask(universe & ~zero_bits, domain_size),
        "intrinsic_invalid": raw_mask(universe & ~intrinsic_bits, domain_size),
        "global_yz_conflict": raw_mask(universe & ~global_yz_bits, domain_size),
        "geometric_illegal": raw_mask(full_word, domain_size),
    }
    reason_union = (
        (universe & ~zero_bits)
        | (universe & ~intrinsic_bits)
        | (universe & ~global_yz_bits)
        | full_word
    )
    if reason_union != (universe & ~combined_bits):
        raise AssertionError("combined killed-reason OR drift")

    priority = []
    cumulative = 0
    for channel in CHANNELS:
        membership = channel_words[channel]
        remainder = membership & ~cumulative
        cumulative |= membership
        priority.append({
            "channel": channel,
            "overlapping_killed_word_mask": raw_mask(
                membership, domain_size
            ),
            "priority_only_remainder_mask": raw_mask(
                remainder, domain_size
            ),
            "cumulative_OR_mask": raw_mask(cumulative, domain_size),
        })

    predicate_vector = [
        (name + ".allowed", pair["allowed"])
        for name, pair in predicate_pairs.items()
    ] + [
        (name + ".killed", pair["killed"])
        for name, pair in predicate_pairs.items()
    ]
    return {
        "probe": probe,
        "exact_prefix": {
            "placed_points": len(points),
            "construction_order_point_stream_sha256": point_stream_sha256(points),
            "point_set_sha256": stable_hash(sorted(points)),
            "point_provenance_stream_sha256": stable_hash(provenance),
            "yz_occupancy_sha256": stable_hash(sorted(yz_counts.items())),
            "all_placed_points_scanned": True,
            "endpoint_or_distance_cutoff": None,
        },
        "domain": {
            "words": domain_size,
            "encoded_block_sha256": probe["domain_block_sha256"],
            "candidate_site_atoms": len(model["site_id"]),
            "candidate_line_atoms": len(model["line_id"]),
            "atom_universe": atom_count,
            "atom_universe_sha256": stable_hash(model["atom_desc"]),
            "word_atom_incidence_sha256": stable_hash(model["word_atoms"]),
            "intrinsic_recheck": domain_recheck,
        },
        "exact_predicate_word_masks": predicate_pairs,
        "predicate_definitions": {
            "zero_T": (
                "raw zero-envelope accepted-ordinal bit from the pinned "
                "lattice action sidecar"
            ),
            "intrinsic": (
                "endpoint and internal general-position checks are mandatory "
                "domain assertions; this mask records pairwise-distinct "
                "interior yz fibres avoiding both endpoint fibres"
            ),
            "global_yz": (
                "every proper interior yz fibre is absent from the complete "
                "chronological prefix and distinct within the word"
            ),
            "geometric": (
                "no collision, old-old-new, or old-new-new atom is poisoned "
                "by any point of the complete chronological prefix"
            ),
            "combined": "bitwise intersection of the four allowed masks",
        },
        "combined_killed_reason_masks_overlap": {
            "semantics": (
                "reason memberships overlap; only their bitwise OR is the "
                "combined killed mask"
            ),
            "reason_masks": reason_masks,
            "reason_OR": raw_mask(reason_union, domain_size),
            "reason_OR_equals_combined_killed_mask": True,
        },
        "geometric_poison_decomposition": {
            "exact_full_killed_word_mask": raw_mask(full_word, domain_size),
            "near_membership": raw_mask(near_word, domain_size),
            "far_membership": raw_mask(far_word, domain_size),
            "near_AND_far": raw_mask(near_word & far_word, domain_size),
            "near_only": raw_mask(near_word & ~far_word, domain_size),
            "far_only": raw_mask(far_word & ~near_word, domain_size),
            "near_OR_far": raw_mask(near_word | far_word, domain_size),
            "channel_priority_partition": priority,
            "birth_shell_descriptor_masks": descriptor_records,
            "descriptor_OR_equals_full_geometric_poison": True,
        },
        "referenced_target_action": {
            **selected,
            "predicate_memberships": predicate_memberships,
            "selection_assertion": selection_assertion,
            "fast_reference_agreement": True,
            "reference_geometric_legality": reference_legal,
        },
        "exact_combined_survivors": combined_bits.bit_count(),
        "raw_predicate_mask_vector_sha256": mask_vector_hash(predicate_vector),
        "exact_witness_provenance": {
            "records": accumulator["witness_records"],
            "record_count": len(accumulator["witness_records"]),
            "ordered_hash_chain_sha256": accumulator["witness_hash_chain"],
            "exact_direction_and_moment_stored_for_every_line_witness": True,
            "recursive_endpoint_ancestry_stored": True,
        },
    }


def encode_accumulator(accumulator, atom_count):
    return {
        "atom_count": atom_count,
        "full_atom_mask": raw_mask(accumulator["full_atom_mask"], atom_count),
        "near_atom_mask": raw_mask(accumulator["near_atom_mask"], atom_count),
        "far_atom_mask": raw_mask(accumulator["far_atom_mask"], atom_count),
        "channel_atom_masks": {
            channel: raw_mask(bits, atom_count)
            for channel, bits in accumulator["channel_atom_masks"].items()
        },
        "birth_descriptor_atom_masks": {
            key: raw_mask(bits, atom_count)
            for key, bits in accumulator[
                "birth_descriptor_atom_masks"
            ].items()
        },
        "birth_descriptor_records": accumulator["birth_descriptor_records"],
        "witness_records": accumulator["witness_records"],
        "witness_hash_chain": accumulator["witness_hash_chain"],
    }


def decode_accumulator(stored, expected_atom_count):
    if stored.get("atom_count") != expected_atom_count:
        raise AssertionError("active atom universe extent drift")
    accumulator = {
        "full_atom_mask": decode_raw_mask(
            stored["full_atom_mask"], expected_atom_count
        ),
        "near_atom_mask": decode_raw_mask(
            stored["near_atom_mask"], expected_atom_count
        ),
        "far_atom_mask": decode_raw_mask(
            stored["far_atom_mask"], expected_atom_count
        ),
        "channel_atom_masks": {
            channel: decode_raw_mask(record, expected_atom_count)
            for channel, record in stored["channel_atom_masks"].items()
        },
        "birth_descriptor_atom_masks": {
            key: decode_raw_mask(record, expected_atom_count)
            for key, record in stored["birth_descriptor_atom_masks"].items()
        },
        "birth_descriptor_records": stored["birth_descriptor_records"],
        "witness_records": stored["witness_records"],
        "witness_hash_chain": stored["witness_hash_chain"],
    }
    validate_accumulator(accumulator, expected_atom_count)
    return accumulator


def validate_accumulator(accumulator, atom_count):
    if set(accumulator["channel_atom_masks"]) != set(CHANNELS):
        raise AssertionError("active channel key drift")
    if set(accumulator["birth_descriptor_atom_masks"]) != set(
        accumulator["birth_descriptor_records"]
    ):
        raise AssertionError("active descriptor key drift")
    full_atoms = near_atoms = far_atoms = 0
    channel_atoms = {channel: 0 for channel in CHANNELS}
    descriptor_atoms = defaultdict(int)
    descriptor_by_sha = {}
    for key, descriptor in accumulator["birth_descriptor_records"].items():
        if json.dumps(descriptor, sort_keys=True, separators=(",", ":")) != key:
            raise AssertionError("noncanonical active descriptor key")
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in descriptor_by_sha:
            raise AssertionError("active descriptor SHA-256 collision")
        descriptor_by_sha[digest] = (key, descriptor)
    chain = "0" * 64
    for sequence, record in enumerate(accumulator["witness_records"]):
        if record.get("witness_sequence_0_based") != sequence:
            raise AssertionError("active witness sequence drift")
        internal = record.get("witness_record_sha256")
        unhashed = dict(record)
        unhashed.pop("witness_record_sha256", None)
        if internal != stable_hash(unhashed):
            raise AssertionError("active witness record digest drift")
        atom = record["poisoned_atom_id"]
        if not 0 <= atom < atom_count:
            raise AssertionError("active witness atom outside universe")
        descriptor_entry = descriptor_by_sha.get(
            record["birth_shell_descriptor_sha256"]
        )
        if descriptor_entry is None:
            raise AssertionError("active witness descriptor is absent")
        key, descriptor = descriptor_entry
        bit = 1 << atom
        full_atoms |= bit
        channel_atoms[descriptor["channel"]] |= bit
        if descriptor["locality"] == "near/local":
            near_atoms |= bit
        else:
            far_atoms |= bit
        descriptor_atoms[key] |= bit
        chain = hash_chain(chain, record)
    if (
        full_atoms != accumulator["full_atom_mask"]
        or near_atoms != accumulator["near_atom_mask"]
        or far_atoms != accumulator["far_atom_mask"]
        or channel_atoms != accumulator["channel_atom_masks"]
        or dict(descriptor_atoms) != accumulator["birth_descriptor_atom_masks"]
        or chain != accumulator["witness_hash_chain"]
    ):
        raise AssertionError("active witness/mask reconstruction drift")


def seal_checkpoint(checkpoint):
    payload = copy.deepcopy(checkpoint)
    payload.pop("checkpoint_payload_sha256", None)
    payload["checkpoint_payload_sha256"] = stable_hash(payload)
    return payload


def save_checkpoint(path, checkpoint):
    sealed = seal_checkpoint(checkpoint)
    atomic_json_dump(sealed, path)
    checkpoint.clear()
    checkpoint.update(sealed)


def initial_checkpoint(static):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial",
        "static": static,
        "next_probe_index": 0,
        "active_probe": None,
        "completed_probe_results": [],
        "terminal_summary": None,
        "last_run": None,
    }


def initialize_active_probe(probe_index, probe, model):
    atom_count = len(model["atom_desc"])
    return {
        "probe_index": probe_index,
        "probe_id": probe["probe_id"],
        "phase": "site-atoms",
        "next_unit_index": 0,
        "atom_count": atom_count,
        "atom_universe_sha256": stable_hash(model["atom_desc"]),
        "word_atom_incidence_sha256": stable_hash(model["word_atoms"]),
        "accumulator": encode_accumulator(initial_accumulator(), atom_count),
    }


def decode_mask_partition(pair, bit_count, label):
    allowed = decode_raw_mask(pair["allowed"], bit_count)
    killed = decode_raw_mask(pair["killed"], bit_count)
    if allowed & killed or allowed | killed != full_mask(bit_count):
        raise AssertionError(label + " mask partition drift")
    if pair.get("allowed_OR_killed_is_full_domain") is not True or pair.get(
        "allowed_AND_killed_is_empty"
    ) is not True:
        raise AssertionError(label + " mask-partition assertion drift")
    return allowed, killed


def validate_completed_probe_result(result, expected_probe, context, deadline=None):
    """Decode and cross-check every committed mask and witness relation.

    This is deliberately stronger than checking the outer checkpoint digest.
    It rebuilds the pinned domain model, checks the raw atom-to-word projection,
    and verifies each stored witness against the exact chronological snapshot.
    It does not rerun the full all-point witness search and therefore remains a
    semantic integrity check on the completed census, not a second census.
    """
    if result.get("probe") != expected_probe:
        raise AssertionError("completed probe/result identity drift")
    result_digest = stable_hash(result)
    cache = context.setdefault("_validated_probe_result_sha256", {})
    if cache.get(expected_probe["probe_id"]) == result_digest:
        return
    enforce_cooperative_limits(deadline, "validating a completed probe result")

    domain, model, intrinsic_expected, domain_recheck = load_probe_domain_model(
        context, expected_probe
    )
    domain_words = len(domain)
    atom_count = len(model["atom_desc"])
    universe = full_mask(domain_words)
    atom_word_bits = build_atom_word_bits(model, domain_words)
    if domain_words != expected_probe["domain_words"]:
        raise AssertionError("completed probe domain extent drift")

    snapshot = context["point_sets"][expected_probe["probe_id"]]
    points = snapshot["points"]
    provenance = snapshot["provenance"]
    yz_counts = snapshot["yz_counts"]
    exact_prefix = result.get("exact_prefix", {})
    expected_prefix = {
        "placed_points": len(points),
        "construction_order_point_stream_sha256": point_stream_sha256(points),
        "point_set_sha256": stable_hash(sorted(points)),
        "point_provenance_stream_sha256": stable_hash(provenance),
        "yz_occupancy_sha256": stable_hash(sorted(yz_counts.items())),
        "all_placed_points_scanned": True,
        "endpoint_or_distance_cutoff": None,
    }
    if exact_prefix != expected_prefix:
        raise AssertionError("completed probe exact-prefix commitment drift")

    domain_record = result.get("domain", {})
    expected_domain = {
        "words": domain_words,
        "encoded_block_sha256": expected_probe["domain_block_sha256"],
        "candidate_site_atoms": len(model["site_id"]),
        "candidate_line_atoms": len(model["line_id"]),
        "atom_universe": atom_count,
        "atom_universe_sha256": stable_hash(model["atom_desc"]),
        "word_atom_incidence_sha256": stable_hash(model["word_atoms"]),
        "intrinsic_recheck": domain_recheck,
    }
    if domain_record != expected_domain:
        raise AssertionError("completed probe domain/model commitment drift")

    predicate_records = result.get("exact_predicate_word_masks", {})
    if tuple(predicate_records) != PREDICATES and set(predicate_records) != set(
        PREDICATES
    ):
        raise AssertionError("completed predicate-mask key drift")
    predicate_allowed = {}
    predicate_killed = {}
    for name in PREDICATES:
        allowed, killed = decode_mask_partition(
            predicate_records[name], domain_words, name
        )
        predicate_allowed[name] = allowed
        predicate_killed[name] = killed

    poison = result.get("geometric_poison_decomposition", {})
    poison_masks = {
        name: decode_raw_mask(poison[name], domain_words)
        for name in (
            "exact_full_killed_word_mask",
            "near_membership",
            "far_membership",
            "near_AND_far",
            "near_only",
            "far_only",
            "near_OR_far",
        )
    }
    full_word = poison_masks["exact_full_killed_word_mask"]
    near_word = poison_masks["near_membership"]
    far_word = poison_masks["far_membership"]
    if (
        poison_masks["near_AND_far"] != near_word & far_word
        or poison_masks["near_only"] != near_word & ~far_word & universe
        or poison_masks["far_only"] != far_word & ~near_word & universe
        or poison_masks["near_OR_far"] != near_word | far_word
        or near_word | far_word != full_word
        or poison.get("descriptor_OR_equals_full_geometric_poison") is not True
    ):
        raise AssertionError("completed near/far geometric decomposition drift")

    descriptor_records = poison.get("birth_shell_descriptor_masks")
    if not isinstance(descriptor_records, list):
        raise AssertionError("completed birth-descriptor census is absent")
    descriptor_by_sha = {}
    descriptor_keys = []
    for record in descriptor_records:
        descriptor = record["descriptor"]
        key = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if record.get("descriptor_sha256") != digest or digest in descriptor_by_sha:
            raise AssertionError("completed descriptor identity drift")
        atom_bits = decode_raw_mask(record["poisoned_atom_mask"], atom_count)
        word_bits = decode_raw_mask(record["killed_word_mask"], domain_words)
        descriptor_by_sha[digest] = {
            "descriptor": descriptor,
            "atom_bits": atom_bits,
            "word_bits": word_bits,
        }
        descriptor_keys.append(key)
    if descriptor_keys != sorted(descriptor_keys):
        raise AssertionError("completed descriptor order is noncanonical")

    witness_block = result.get("exact_witness_provenance", {})
    witness_records = witness_block.get("records")
    if not isinstance(witness_records, list) or witness_block.get(
        "record_count"
    ) != len(witness_records):
        raise AssertionError("completed witness-stream extent drift")
    center = midpoint(tuple(expected_probe["start"]), tuple(expected_probe["end"]))
    witness_chain = "0" * 64
    reconstructed_full_atom = 0
    reconstructed_near_atom = 0
    reconstructed_far_atom = 0
    reconstructed_channel_atoms = {channel: 0 for channel in CHANNELS}
    reconstructed_descriptor_atoms = defaultdict(int)
    start = tuple(expected_probe["start"])
    for sequence, record in enumerate(witness_records):
        if sequence % 32 == 0:
            enforce_cooperative_limits(deadline, "validating witness provenance")
        if record.get("witness_sequence_0_based") != sequence:
            raise AssertionError("completed witness sequence drift")
        unhashed = dict(record)
        internal = unhashed.pop("witness_record_sha256", None)
        if internal != stable_hash(unhashed):
            raise AssertionError("completed witness record digest drift")
        atom = record.get("poisoned_atom_id")
        if not isinstance(atom, int) or not 0 <= atom < atom_count:
            raise AssertionError("completed witness atom outside universe")
        descriptor_entry = descriptor_by_sha.get(
            record.get("birth_shell_descriptor_sha256")
        )
        if descriptor_entry is None:
            raise AssertionError("completed witness descriptor is absent")
        channel = record.get("channel")
        if channel not in CHANNELS or channel != descriptor_entry[
            "descriptor"
        ].get("channel"):
            raise AssertionError("completed witness channel drift")
        endpoints = record.get("old_endpoints")
        expected_endpoint_count = {
            "collision": 1,
            "old-old-new": 2,
            "old-new-new": 1,
        }[channel]
        if not isinstance(endpoints, list) or len(endpoints) != (
            expected_endpoint_count
        ):
            raise AssertionError("completed witness endpoint extent drift")
        for endpoint in endpoints:
            index = endpoint.get("point_index")
            if not isinstance(index, int) or not 0 <= index < len(points):
                raise AssertionError("completed witness endpoint index drift")
            distance = chebyshev(points[index], center)
            expected_profile = endpoint_profile(
                provenance[index],
                points[index],
                index,
                expected_probe["observation_boundary_rank"],
                distance,
            )
            if endpoint != expected_profile:
                raise AssertionError("completed witness endpoint profile drift")
        expected_descriptor = witness_descriptor(channel, tuple(endpoints))
        if expected_descriptor != descriptor_entry["descriptor"]:
            raise AssertionError("completed witness/descriptor semantic drift")

        atom_kind, atom_geometry = model["atom_desc"][atom]
        if channel in {"collision", "old-old-new"}:
            if atom_kind != "site":
                raise AssertionError("site witness references a line atom")
            offset = tuple(record.get("candidate_offset") or ())
            candidate = tuple(record.get("candidate_site") or ())
            if offset != tuple(atom_geometry) or candidate != add(start, offset):
                raise AssertionError("completed site-witness geometry drift")
            if channel == "collision":
                if record.get("exact_line") is not None or tuple(
                    endpoints[0]["coordinate"]
                ) != candidate:
                    raise AssertionError("completed collision witness drift")
            else:
                line = record.get("exact_line") or {}
                direction = tuple(line.get("primitive_direction") or ())
                moment = tuple(
                    line.get("integer_moment_cross_point_direction") or ()
                )
                if len(direction) != 3 or primitive(direction) != direction or (
                    moment != cross(candidate, direction)
                ):
                    raise AssertionError("completed old-old line encoding drift")
                for endpoint in endpoints:
                    coordinate = tuple(endpoint["coordinate"])
                    if (
                        primitive(subtract(coordinate, candidate)) != direction
                        or cross(coordinate, direction) != moment
                    ):
                        raise AssertionError("completed old-old secant drift")
        else:
            if atom_kind != "line" or record.get("candidate_site") is not None or (
                record.get("candidate_offset") is not None
            ):
                raise AssertionError("old-new-new witness atom-kind drift")
            local_direction, local_moment = atom_geometry
            line = record.get("exact_line") or {}
            direction = tuple(line.get("primitive_direction") or ())
            relative_moment = tuple(line.get("relative_integer_moment") or ())
            absolute_moment = tuple(
                line.get("absolute_integer_moment_cross_point_direction") or ()
            )
            coordinate = tuple(endpoints[0]["coordinate"])
            relative = subtract(coordinate, start)
            if (
                direction != tuple(local_direction)
                or relative_moment != tuple(local_moment)
                or relative_moment != cross(relative, direction)
                or absolute_moment != cross(coordinate, direction)
                or tuple(line.get("corridor_start") or ()) != start
            ):
                raise AssertionError("completed old-new-new line drift")

        bit = 1 << atom
        reconstructed_full_atom |= bit
        reconstructed_channel_atoms[channel] |= bit
        if expected_descriptor["locality"] == "near/local":
            reconstructed_near_atom |= bit
        else:
            reconstructed_far_atom |= bit
        reconstructed_descriptor_atoms[
            record["birth_shell_descriptor_sha256"]
        ] |= bit
        witness_chain = hash_chain(witness_chain, record)

    if (
        witness_chain != witness_block.get("ordered_hash_chain_sha256")
        or witness_block.get(
            "exact_direction_and_moment_stored_for_every_line_witness"
        ) is not True
        or witness_block.get("recursive_endpoint_ancestry_stored") is not True
    ):
        raise AssertionError("completed witness-stream commitment drift")
    if set(reconstructed_descriptor_atoms) != set(descriptor_by_sha):
        raise AssertionError("completed witness/descriptor census drift")
    for digest, entry in descriptor_by_sha.items():
        atom_bits = reconstructed_descriptor_atoms[digest]
        if atom_bits != entry["atom_bits"] or atom_mask_to_word_mask(
            atom_bits, atom_word_bits
        ) != entry["word_bits"]:
            raise AssertionError("completed descriptor atom/word mask drift")

    reconstructed_full_word = atom_mask_to_word_mask(
        reconstructed_full_atom, atom_word_bits
    )
    reconstructed_near_word = atom_mask_to_word_mask(
        reconstructed_near_atom, atom_word_bits
    )
    reconstructed_far_word = atom_mask_to_word_mask(
        reconstructed_far_atom, atom_word_bits
    )
    if (
        reconstructed_full_word != full_word
        or reconstructed_near_word != near_word
        or reconstructed_far_word != far_word
    ):
        raise AssertionError("completed witness-to-word poison drift")

    priority = poison.get("channel_priority_partition")
    if not isinstance(priority, list) or len(priority) != len(CHANNELS):
        raise AssertionError("completed channel-priority census drift")
    cumulative = 0
    for channel, record in zip(CHANNELS, priority):
        if record.get("channel") != channel:
            raise AssertionError("completed channel-priority order drift")
        membership = atom_mask_to_word_mask(
            reconstructed_channel_atoms[channel], atom_word_bits
        )
        remainder = membership & ~cumulative & universe
        cumulative |= membership
        if (
            decode_raw_mask(
                record["overlapping_killed_word_mask"], domain_words
            ) != membership
            or decode_raw_mask(
                record["priority_only_remainder_mask"], domain_words
            ) != remainder
            or decode_raw_mask(record["cumulative_OR_mask"], domain_words)
            != cumulative
        ):
            raise AssertionError("completed channel-priority mask drift")
    if cumulative != full_word:
        raise AssertionError("completed channel OR misses geometric poison")

    zero_expected = zero_t_word_mask(context, expected_probe, domain_words)
    global_yz_expected = global_yz_word_mask(
        context["producer"], domain, expected_probe, yz_counts
    )
    geometric_expected = universe & ~full_word
    combined_expected = (
        zero_expected
        & intrinsic_expected
        & global_yz_expected
        & geometric_expected
    )
    expected_allowed = {
        "zero_T": zero_expected,
        "intrinsic": intrinsic_expected,
        "global_yz": global_yz_expected,
        "geometric": geometric_expected,
        "combined": combined_expected,
    }
    if predicate_allowed != expected_allowed or any(
        predicate_killed[name] != universe & ~expected_allowed[name]
        for name in PREDICATES
    ):
        raise AssertionError("completed predicate semantics drift")
    if global_yz_expected & ~intrinsic_expected:
        raise AssertionError("completed global-yz/intrinsic subset drift")

    reasons = result.get("combined_killed_reason_masks_overlap", {})
    reason_records = reasons.get("reason_masks", {})
    expected_reasons = {
        "zero_T_incompatible": universe & ~zero_expected,
        "intrinsic_invalid": universe & ~intrinsic_expected,
        "global_yz_conflict": universe & ~global_yz_expected,
        "geometric_illegal": full_word,
    }
    if set(reason_records) != set(expected_reasons):
        raise AssertionError("completed killed-reason key drift")
    reason_union = 0
    for name, expected_bits in expected_reasons.items():
        observed = decode_raw_mask(reason_records[name], domain_words)
        if observed != expected_bits:
            raise AssertionError("completed killed-reason mask drift", name)
        reason_union |= observed
    if (
        decode_raw_mask(reasons["reason_OR"], domain_words) != reason_union
        or reason_union != predicate_killed["combined"]
        or reasons.get("reason_OR_equals_combined_killed_mask") is not True
    ):
        raise AssertionError("completed killed-reason OR drift")

    referenced = result.get("referenced_target_action", {})
    selected = expected_probe["actual_selection"]
    if any(referenced.get(key) != value for key, value in selected.items()):
        raise AssertionError("completed referenced target action drift")
    ordinal = selected["first_survivor_ordinal_1_based"]
    if not 1 <= ordinal <= domain_words or domain[ordinal - 1] != tuple(
        selected["selected_word"]
    ):
        raise AssertionError("completed target ordinal/domain drift")
    selected_bit = 1 << (ordinal - 1)
    memberships = {
        name: bool(expected_allowed[name] & selected_bit) for name in PREDICATES
    }
    if referenced.get("predicate_memberships") != memberships:
        raise AssertionError("completed target predicate-membership drift")
    selected_word = tuple(selected["selected_word"])
    store = context["producer"].rescue.Store(points)
    fast_legal = context["producer"].rescue.word_legal_fast(
        tuple(expected_probe["start"]),
        selected_word,
        store,
        {},
        context["producer"].rescue.MENU,
    )
    reference_legal = context["producer"].rescue.word_legal(
        tuple(expected_probe["start"]),
        selected_word,
        store.pts,
        store.pset,
        {},
    )
    if fast_legal != reference_legal or referenced.get(
        "fast_reference_agreement"
    ) is not True or referenced.get("reference_geometric_legality") != (
        reference_legal
    ) or reference_legal != memberships["geometric"]:
        raise AssertionError("completed target exact-legality drift")
    first_combined = first_member_ordinal(combined_expected)
    selection_check = expected_probe["selection_check"]
    if selection_check == "audited-first-survivor":
        expected_assertion = {
            "kind": selection_check,
            "is_first_member_of_exact_combined_mask": True,
            "expected_geometric_legality": True,
        }
        if not all(memberships.values()) or first_combined != ordinal:
            raise AssertionError("completed pre-state first-survivor drift")
    elif selection_check == "selected-word-killed-after-placement":
        expected_assertion = {
            "kind": selection_check,
            "is_first_member_of_exact_combined_mask": False,
            "first_combined_ordinal_1_based": first_combined,
            "expected_geometric_legality": False,
        }
        expected_memberships = {
            "zero_T": True,
            "intrinsic": True,
            "global_yz": False,
            "geometric": False,
            "combined": False,
        }
        if memberships != expected_memberships or reference_legal:
            raise AssertionError("completed post-state target-kill drift")
    else:
        raise AssertionError("completed target selection-check drift")
    if referenced.get("selection_assertion") != expected_assertion:
        raise AssertionError("completed target selection assertion drift")

    predicate_vector = [
        (name + ".allowed", predicate_records[name]["allowed"])
        for name in PREDICATES
    ] + [
        (name + ".killed", predicate_records[name]["killed"])
        for name in PREDICATES
    ]
    if (
        result.get("exact_combined_survivors")
        != combined_expected.bit_count()
        or result.get("raw_predicate_mask_vector_sha256")
        != mask_vector_hash(predicate_vector)
    ):
        raise AssertionError("completed predicate summary commitment drift")

    cache[expected_probe["probe_id"]] = result_digest
    enforce_cooperative_limits(deadline, "finishing completed-result validation")


def validate_checkpoint(checkpoint, static, context, deadline=None):
    if checkpoint.get("schema_version") != SCHEMA_VERSION or checkpoint.get(
        "static"
    ) != static:
        raise AssertionError("checkpoint static/schema drift")
    probes = static["probe_records"]
    next_probe = checkpoint.get("next_probe_index")
    results = checkpoint.get("completed_probe_results")
    if (
        not isinstance(next_probe, int)
        or not 0 <= next_probe <= len(probes)
        or not isinstance(results, list)
        or len(results) != next_probe
    ):
        raise AssertionError("checkpoint probe cursor drift")
    for index, result in enumerate(results):
        if result.get("probe") != probes[index]:
            raise AssertionError("checkpoint result/probe order drift")
        validate_completed_probe_result(
            result, probes[index], context, deadline
        )
        normalized_probe_signature(result)
    active = checkpoint.get("active_probe")
    if active is not None:
        if next_probe == len(probes):
            raise AssertionError("terminal checkpoint retains active probe")
        if (
            active.get("probe_index") != next_probe
            or active.get("probe_id") != probes[next_probe]["probe_id"]
            or active.get("phase") not in {"site-atoms", "old-new-new"}
            or not isinstance(active.get("next_unit_index"), int)
            or active["next_unit_index"] < 0
            or not isinstance(active.get("atom_count"), int)
            or active["atom_count"] < 0
        ):
            raise AssertionError("active probe identity/cursor drift")
        decode_accumulator(active["accumulator"], active["atom_count"])
    status = checkpoint.get("status")
    if status == "complete":
        terminal_summary = checkpoint.get("terminal_summary")
        if (
            next_probe != len(probes)
            or active is not None
            or not isinstance(terminal_summary, dict)
            or terminal_summary.get("probe_result_stream_sha256")
            != stable_hash(results)
        ):
            raise AssertionError("complete checkpoint terminal-state drift")
    elif status == "partial":
        if checkpoint.get("terminal_summary") is not None:
            raise AssertionError("partial checkpoint claims terminal output")
    else:
        raise AssertionError("unknown checkpoint status")


def load_checkpoint(path, static, context, deadline=None):
    path = Path(path)
    if not path.exists():
        return initial_checkpoint(static)
    before = path.stat()
    with path.open() as handle:
        checkpoint = json.load(handle)
    after = path.stat()
    identity = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, key) for key in identity) != tuple(
        getattr(after, key) for key in identity
    ):
        raise RuntimeError("checkpoint changed while being loaded")
    internal = checkpoint.pop("checkpoint_payload_sha256", None)
    if internal != stable_hash(checkpoint):
        raise AssertionError("checkpoint payload drift")
    checkpoint["checkpoint_payload_sha256"] = internal
    validate_checkpoint(checkpoint, static, context, deadline)
    return checkpoint


def observed_file_snapshot(path):
    path = Path(path).resolve()
    before = path.stat()
    digest = file_sha256(path)
    after = path.stat()
    identity = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if tuple(getattr(before, key) for key in identity) != tuple(
        getattr(after, key) for key in identity
    ):
        raise RuntimeError("terminal artifact changed while being hashed")
    return {"path": str(path), "sha256": digest, "bytes": after.st_size}


def rational_population(members, domain_words):
    return {
        "members": members,
        "domain_words": domain_words,
        "exact_fraction": {
            "numerator": members,
            "denominator": domain_words,
        },
    }


def normalized_probe_signature(result):
    """Canonical scalar/semantic summary; never a cross-domain bit map."""
    domain_words = result["domain"]["words"]
    predicates = {}
    for name, pair in result["exact_predicate_word_masks"].items():
        predicates[name] = {
            "allowed": rational_population(
                pair["allowed"]["members"], domain_words
            ),
            "killed": rational_population(
                pair["killed"]["members"], domain_words
            ),
            "allowed_mask_sha256": pair["allowed"]["sha256"],
            "killed_mask_sha256": pair["killed"]["sha256"],
        }
    poison = result["geometric_poison_decomposition"]
    geometric_classes = {}
    for name in (
        "exact_full_killed_word_mask",
        "near_membership",
        "far_membership",
        "near_AND_far",
        "near_only",
        "far_only",
    ):
        mask = poison[name]
        geometric_classes[name] = {
            **rational_population(mask["members"], domain_words),
            "mask_sha256": mask["sha256"],
        }
    channel_populations = {}
    for record in poison["channel_priority_partition"]:
        mask = record["overlapping_killed_word_mask"]
        channel_populations[record["channel"]] = {
            **rational_population(mask["members"], domain_words),
            "overlapping_killed_word_mask_sha256": mask["sha256"],
        }
    descriptors = []
    for record in poison["birth_shell_descriptor_masks"]:
        word_mask = record["killed_word_mask"]
        atom_mask = record["poisoned_atom_mask"]
        descriptors.append({
            "descriptor": record["descriptor"],
            "descriptor_sha256": record["descriptor_sha256"],
            "poisoned_atoms": atom_mask["members"],
            "poisoned_atom_mask_sha256": atom_mask["sha256"],
            "killed_words": rational_population(
                word_mask["members"], domain_words
            ),
            "killed_word_mask_sha256": word_mask["sha256"],
        })
    signature = {
        "probe_id": result["probe"]["probe_id"],
        "level": result["probe"]["level"],
        "step": result["probe"]["step"],
        "prefix_position": result["probe"]["prefix_position"],
        "observation_boundary_rank": result["probe"][
            "observation_boundary_rank"
        ],
        "domain_words": domain_words,
        "domain_block_sha256": result["probe"]["domain_block_sha256"],
        "predicate_populations": predicates,
        "geometric_class_populations": geometric_classes,
        "overlapping_channel_populations": channel_populations,
        "birth_shell_descriptor_spectrum": descriptors,
        "birth_shell_descriptor_spectrum_sha256": stable_hash(descriptors),
        "raw_predicate_mask_vector_sha256": result[
            "raw_predicate_mask_vector_sha256"
        ],
        "cross_domain_word_correspondence_asserted": False,
    }
    signature["normalized_probe_signature_sha256"] = stable_hash(signature)
    return signature


def same_corridor_pre_post_observations(static, results):
    by_probe = {result["probe"]["probe_id"]: result for result in results}
    observations = []
    for pair in static["same_corridor_pre_post_records"]:
        pre = by_probe[pair["pre_probe_id"]]
        post = by_probe[pair["post_probe_id"]]
        domain_words = pair["domain_words"]
        if (
            pre["domain"]["words"] != domain_words
            or post["domain"]["words"] != domain_words
            or pre["probe"]["domain_block_sha256"]
            != pair["domain_block_sha256"]
            or post["probe"]["domain_block_sha256"]
            != pair["domain_block_sha256"]
        ):
            raise AssertionError("same-corridor pre/post domain drift")
        predicate_deltas = {}
        for name in ("zero_T", "intrinsic", "global_yz", "geometric", "combined"):
            pre_allowed = decode_raw_mask(
                pre["exact_predicate_word_masks"][name]["allowed"],
                domain_words,
            )
            post_allowed = decode_raw_mask(
                post["exact_predicate_word_masks"][name]["allowed"],
                domain_words,
            )
            gained = post_allowed & ~pre_allowed
            lost = pre_allowed & ~post_allowed
            if name in {"zero_T", "intrinsic"}:
                if pre_allowed != post_allowed:
                    raise AssertionError("static predicate changed across action", name)
            elif gained:
                raise AssertionError(
                    "monotone placed-prefix predicate gained an allowed word",
                    name,
                )
            predicate_deltas[name] = {
                "pre_allowed": raw_mask(pre_allowed, domain_words),
                "post_allowed": raw_mask(post_allowed, domain_words),
                "lost_allowed": raw_mask(lost, domain_words),
                "gained_allowed": raw_mask(gained, domain_words),
                "post_allowed_subset_of_pre_allowed": not bool(gained),
            }
        selected_ordinal = pair["target_action"][
            "first_survivor_ordinal_1_based"
        ]
        selected_bit = 1 << (selected_ordinal - 1)
        lost_combined = decode_raw_mask(
            predicate_deltas["combined"]["lost_allowed"], domain_words
        )
        if not lost_combined & selected_bit:
            raise AssertionError("placed target word did not leave combined mask")
        observation = {
            **pair,
            "comparison_scope": (
                "one literal construction action on one unchanged corridor and "
                "one unchanged connector-word ordinal domain"
            ),
            "predicate_allowed_mask_deltas": predicate_deltas,
            "target_selected_word_is_in_combined_lost_mask": True,
            "pre_normalized_signature": normalized_probe_signature(pre),
            "post_normalized_signature": normalized_probe_signature(post),
            "abstract_state_transition_or_recurrence_claimed": False,
        }
        observation["same_corridor_pre_post_observation_sha256"] = stable_hash(
            observation
        )
        observations.append(observation)
    return observations


def parent_child_comparison(static, results):
    parent = [
        result for result in results
        if result["probe"]["same_corridor_comparison_role"] == "L5-parent-only"
    ]
    children = [
        result for result in results
        if result["probe"]["level"] == 6
        and result["probe"]["same_corridor_comparison_role"] == "pre"
    ]
    if len(parent) != 1 or len(children) != len(OWNER_L6_GAPS):
        raise AssertionError("parent/four-child result census drift")
    signatures = {
        "parent": normalized_probe_signature(parent[0]),
        "children_in_owner_slot_order": [
            normalized_probe_signature(result) for result in children
        ],
    }
    v1_authority = static["inputs"]["v1_verified_payload"][
        "L5_parent_geometry_regression_authority"
    ]
    parent_geometry = signatures["parent"]["geometric_class_populations"]
    observed_v1_fields = {
        "domain_words": signatures["parent"]["domain_words"],
        "domain_block_sha256": signatures["parent"]["domain_block_sha256"],
        "exact_full_killed": {
            "members": parent_geometry["exact_full_killed_word_mask"][
                "members"
            ],
            "sha256": parent_geometry["exact_full_killed_word_mask"][
                "mask_sha256"
            ],
        },
        "near_membership": {
            "members": parent_geometry["near_membership"]["members"],
            "sha256": parent_geometry["near_membership"]["mask_sha256"],
        },
        "far_membership": {
            "members": parent_geometry["far_membership"]["members"],
            "sha256": parent_geometry["far_membership"]["mask_sha256"],
        },
    }
    expected_v1_fields = {
        key: value for key, value in v1_authority.items() if key != "probe_id"
    }
    if observed_v1_fields != expected_v1_fields:
        raise AssertionError("recomputed L5 parent geometry disagrees with v1")
    comparison = {
        "scope": "one exact L5 chronological parent and its four actual L6 child corridors",
        "parent_probe_id": parent[0]["probe"]["probe_id"],
        "child_probe_ids": [result["probe"]["probe_id"] for result in children],
        "normalized_signatures": signatures,
        "normalized_signature_vector_sha256": stable_hash(signatures),
        "recomputed_L5_parent_matches_frozen_v1_geometry": {
            "matched": True,
            "frozen_v1_probe_id": v1_authority["probe_id"],
            "exact_compared_fields": observed_v1_fields,
            "comparison_sha256": stable_hash(observed_v1_fields),
        },
        "raw_mask_cross_step_comparison_performed": False,
        "canonical_cross_step_word_or_ordinal_projection": None,
        "reason_raw_masks_are_incomparable": static[
            "cross_probe_comparability_policy"
        ]["reason"],
        "allowed_comparison_semantics": static[
            "cross_probe_comparability_policy"
        ]["parent_to_child_comparison"],
        "transfer_contraction_or_state_recurrence_claimed": False,
    }
    comparison["parent_four_child_comparison_sha256"] = stable_hash(comparison)
    return comparison


def terminal_payload(checkpoint, policy):
    static = checkpoint["static"]
    results = checkpoint["completed_probe_results"]
    if checkpoint["status"] != "complete" or len(results) != len(
        static["probe_records"]
    ):
        raise AssertionError("terminal payload requested before completion")
    pre_post = same_corridor_pre_post_observations(static, results)
    parent_children = parent_child_comparison(static, results)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "date": "2026-07-18",
        "status": (
            "exact finite five-corridor chronological birth/shell mask census "
            "with four same-corridor L6 pre/post pairs; evidence only"
        ),
        "checker": {
            "path": "design/lattice_t_birth_shell_transition_v2.py",
            "sha256": PROCESS_START_CHECKER_SHA256,
            "unchanged_during_scan": True,
        },
        "resource_policy": policy,
        "inputs": static["inputs"],
        "terminal_pin_block": static["terminal_pin_block"],
        "scope": {
            "probe_selection": static["probe_selection"],
            "probe_records": static["probe_records"],
            "point_set_commitments": static["point_set_commitments"],
            "recursive_ancestry": static["recursive_ancestry"],
            "all_probe_domains_complete": True,
            "all_exact_chronological_prefix_points_scanned": True,
            "endpoint_or_distance_cutoff": None,
            "raw_fixed_width_word_masks_stored": True,
            "cross_probe_comparability_policy": static[
                "cross_probe_comparability_policy"
            ],
            "explicit_limitations": static["explicit_scope_limitations"],
            "channels": list(CHANNELS),
        },
        "probe_results": results,
        "same_corridor_L6_pre_post_observations": pre_post,
        "parent_to_four_child_normalized_comparison": parent_children,
        "adjacent_L6_action_context_only": static[
            "adjacent_action_context_records"
        ],
        "commitments": {
            "static_state_sha256": static["static_state_sha256"],
            "probe_record_stream_sha256": static[
                "probe_record_stream_sha256"
            ],
            "probe_result_stream_sha256": stable_hash(results),
            "same_corridor_pre_post_record_stream_sha256": static[
                "same_corridor_pre_post_record_stream_sha256"
            ],
            "same_corridor_pre_post_observation_stream_sha256": stable_hash(
                pre_post
            ),
            "adjacent_action_context_stream_sha256": static[
                "adjacent_action_context_stream_sha256"
            ],
            "parent_four_child_comparison_sha256": parent_children[
                "parent_four_child_comparison_sha256"
            ],
        },
        "interpretation": {
            "proved_finite_facts_if_checker_completes": [
                "the L5 parent uses an independently replayed exact chronological prefix and its audited first survivor",
                "the recomputed L5 full, near, and far geometric word masks match the frozen v1 commitments exactly",
                "each L6 child uses its exact audited chronological prefix at the literal inverse-schedule rank",
                "each L6 post-state uses the exact prefix after placing that target action on the same corridor and domain",
                "each raw predicate mask is reconstructable ordinal by ordinal from fixed-width bytes",
                "the combined mask is exactly zero-T AND intrinsic AND global-yz AND geometric",
                "every geometric witness uses the complete prefix and stores exact line direction, moment, and recursive endpoint provenance",
                "the audited selected action is the first member of each exact pre-state combined mask and is killed in each corresponding L6 post-state",
                "same-corridor L6 allowed masks are monotone across the literal target action",
            ],
            "not_proved": [
                "availability at any untested stitch or any level beyond this pinned L6 orbit",
                "a canonical projection or bitwise comparison between different step domains",
                "that the four literal pre/post observations form a repeated, finite, or closed safety-game state space",
                "stabilization of normalized parent/child descriptor spectra",
                "a contracting or summable far-secant shell transfer operator",
                "an unconditional infinite construction or solution of Erdos #193",
            ],
        },
    }
    payload["terminal_payload_sha256"] = stable_hash(payload)
    return payload


def verify_terminal_output(
    path, expected_summary, static, context, deadline=None,
):
    snapshot = observed_file_snapshot(path)
    if snapshot != {
        key: expected_summary[key] for key in ("path", "sha256", "bytes")
    }:
        raise AssertionError("terminal file snapshot drift")
    terminal, internal = unseal_json(
        path, "terminal_payload_sha256", "v2 terminal output"
    )
    if internal != expected_summary["payload_sha256"]:
        raise AssertionError("v2 terminal payload pin drift")
    results = terminal.get("probe_results")
    if (
        terminal.get("schema_version") != SCHEMA_VERSION
        or terminal.get("status")
        != (
            "exact finite five-corridor chronological birth/shell mask census "
            "with four same-corridor L6 pre/post pairs; evidence only"
        )
        or not isinstance(results, list)
        or len(results) != len(static["probe_records"])
    ):
        raise AssertionError("v2 terminal schema/status/result extent drift")
    result_stream_sha256 = stable_hash(results)
    if expected_summary.get("probe_result_stream_sha256") != (
        result_stream_sha256
    ):
        raise AssertionError("v2 terminal/checkpoint result-stream drift")
    for result, probe in zip(results, static["probe_records"]):
        validate_completed_probe_result(result, probe, context, deadline)
    expected_pre_post = same_corridor_pre_post_observations(static, results)
    expected_parent_children = parent_child_comparison(static, results)
    expected_commitments = {
        "static_state_sha256": static["static_state_sha256"],
        "probe_record_stream_sha256": static["probe_record_stream_sha256"],
        "probe_result_stream_sha256": result_stream_sha256,
        "same_corridor_pre_post_record_stream_sha256": static[
            "same_corridor_pre_post_record_stream_sha256"
        ],
        "same_corridor_pre_post_observation_stream_sha256": stable_hash(
            expected_pre_post
        ),
        "adjacent_action_context_stream_sha256": static[
            "adjacent_action_context_stream_sha256"
        ],
        "parent_four_child_comparison_sha256": expected_parent_children[
            "parent_four_child_comparison_sha256"
        ],
    }
    if (
        terminal.get("checker", {}).get("sha256")
        != PROCESS_START_CHECKER_SHA256
        or terminal.get("commitments") != expected_commitments
        or terminal.get("same_corridor_L6_pre_post_observations")
        != expected_pre_post
        or terminal.get("parent_to_four_child_normalized_comparison")
        != expected_parent_children
        or terminal.get("adjacent_L6_action_context_only")
        != static["adjacent_action_context_records"]
    ):
        raise AssertionError("v2 terminal semantic verification drift")
    return terminal


def write_verified_terminal(
    checkpoint, policy, output, context, deadline=None,
):
    terminal = terminal_payload(checkpoint, policy)
    atomic_json_dump(terminal, output)
    snapshot = observed_file_snapshot(output)
    summary = {
        **snapshot,
        "payload_sha256": terminal["terminal_payload_sha256"],
        "probe_result_stream_sha256": stable_hash(
            checkpoint["completed_probe_results"]
        ),
    }
    verify_terminal_output(
        output, summary, checkpoint["static"], context, deadline
    )
    return summary


def active_probe_geometry(context, probe):
    snapshot = context["point_sets"][probe["probe_id"]]
    points = snapshot["points"]
    provenance = snapshot["provenance"]
    center = midpoint(tuple(probe["start"]), tuple(probe["end"]))
    distances, profiles = point_profiles(
        points, provenance, probe["observation_boundary_rank"], center
    )
    return (
        points,
        provenance,
        snapshot["yz_counts"],
        distances,
        profiles,
    )


def synchronize_active(checkpoint, accumulator, atom_count):
    checkpoint["active_probe"]["accumulator"] = encode_accumulator(
        accumulator, atom_count
    )


def run_chunk(args):
    started = time.monotonic()
    deadline = started + args.max_seconds
    hard_deadline = started + HARD_MAX_SECONDS
    policy = resource_policy(enforce=True)
    static, context = build_inputs(args, deadline)
    try:
        checkpoint = load_checkpoint(
            args.checkpoint, static, context, deadline
        )
        if checkpoint["status"] == "complete":
            verify_terminal_output(
                args.output,
                checkpoint["terminal_summary"],
                static,
                context,
                hard_deadline,
            )
            return checkpoint, {
                "units_processed_this_run": 0,
                "probes_completed_this_run": 0,
                "stop_reason": "verified-terminal-checkpoint-already-present",
            }
        units = 0
        units_since_save = 0
        completed_this_run = 0
        stop_reason = "unit-limit"
        while checkpoint["next_probe_index"] < len(context["probes"]):
            if time.monotonic() >= deadline:
                stop_reason = "time-limit"
                break
            probe_index = checkpoint["next_probe_index"]
            probe = context["probes"][probe_index]
            domain, model, intrinsic_bits, domain_recheck = (
                load_probe_domain_model(context, probe)
            )
            atom_count = len(model["atom_desc"])
            if checkpoint["active_probe"] is None:
                checkpoint["active_probe"] = initialize_active_probe(
                    probe_index, probe, model
                )
            active = checkpoint["active_probe"]
            if (
                active["atom_count"] != atom_count
                or active["atom_universe_sha256"] != stable_hash(
                    model["atom_desc"]
                )
                or active["word_atom_incidence_sha256"] != stable_hash(
                    model["word_atoms"]
                )
            ):
                raise AssertionError("resumed active domain model drift")
            accumulator = decode_accumulator(
                active["accumulator"], atom_count
            )
            (
                points,
                provenance,
                yz_counts,
                distances,
                profiles,
            ) = active_probe_geometry(context, probe)
            site_records = tuple(sorted(model["site_id"].items()))
            directions = tuple(sorted(model["line_by_direction"].items()))
            if (
                active["phase"] == "site-atoms"
                and active["next_unit_index"] > len(site_records)
            ) or (
                active["phase"] == "old-new-new"
                and active["next_unit_index"] > len(points)
            ):
                raise AssertionError("resumed active unit cursor outside phase")
            while units < args.max_units:
                if maximum_resident_bytes() > MAX_RESIDENT_BYTES:
                    raise MemoryError("v2 resident-memory limit exceeded")
                if time.monotonic() >= deadline:
                    stop_reason = "time-limit"
                    break
                if active["phase"] == "site-atoms":
                    cursor = active["next_unit_index"]
                    if cursor == len(site_records):
                        active["phase"] = "old-new-new"
                        active["next_unit_index"] = 0
                        continue
                    if cursor > len(site_records):
                        raise AssertionError("active site-unit cursor drift")
                    scan_site_unit(
                        tuple(probe["start"]), points, profiles,
                        site_records[cursor], accumulator,
                    )
                    active["next_unit_index"] += 1
                else:
                    cursor = active["next_unit_index"]
                    if cursor == len(points):
                        break
                    if cursor > len(points):
                        raise AssertionError("active old-point cursor drift")
                    scan_old_point_unit(
                        tuple(probe["start"]), points, profiles, cursor,
                        directions, accumulator,
                    )
                    active["next_unit_index"] += 1
                units += 1
                units_since_save += 1
                if units_since_save >= SAVE_UNIT_INTERVAL:
                    synchronize_active(checkpoint, accumulator, atom_count)
                    save_checkpoint(args.checkpoint, checkpoint)
                    active = checkpoint["active_probe"]
                    units_since_save = 0
            probe_complete = (
                active["phase"] == "old-new-new"
                and active["next_unit_index"] == len(points)
            )
            if probe_complete:
                result = finalize_probe(
                    context, probe, domain, model, intrinsic_bits,
                    domain_recheck, points, provenance, yz_counts, distances,
                    accumulator,
                )
                checkpoint["completed_probe_results"].append(result)
                checkpoint["next_probe_index"] += 1
                checkpoint["active_probe"] = None
                completed_this_run += 1
                save_checkpoint(args.checkpoint, checkpoint)
                units_since_save = 0
                del result
            else:
                synchronize_active(checkpoint, accumulator, atom_count)
            del (
                accumulator, domain, model, intrinsic_bits, domain_recheck,
                points, provenance, yz_counts, distances, profiles,
            )
            gc.collect()
            if stop_reason == "time-limit" or units >= args.max_units:
                break

        if checkpoint["next_probe_index"] == len(context["probes"]):
            checkpoint["status"] = "complete"
            checkpoint["active_probe"] = None
            stop_reason = "full-panel-complete"
            checkpoint["terminal_summary"] = write_verified_terminal(
                checkpoint, policy, args.output, context, hard_deadline
            )
        elapsed = time.monotonic() - started
        resident = maximum_resident_bytes()
        checkpoint["last_run"] = {
            "units_processed_this_run": units,
            "probes_completed_this_run": completed_this_run,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(elapsed, 6),
            "maximum_resident_bytes": resident,
            "resource_policy": policy,
        }
        validate_checkpoint(checkpoint, static, context, hard_deadline)
        save_checkpoint(args.checkpoint, checkpoint)
        elapsed = time.monotonic() - started
        resident = maximum_resident_bytes()
        if elapsed > HARD_MAX_SECONDS or resident > MAX_RESIDENT_BYTES:
            raise RuntimeError("v2 resource bound exceeded")
        return checkpoint, {
            "units_processed_this_run": units,
            "probes_completed_this_run": completed_this_run,
            "stop_reason": stop_reason,
            "elapsed_seconds": round(elapsed, 6),
            "maximum_resident_bytes": resident,
        }
    finally:
        close_inputs(context)


def self_check():
    sample_bits = (1 << 0) | (1 << 7) | (1 << 9)
    encoded = raw_mask(sample_bits, 10)
    if encoded["data_hex"] != "8102" or decode_raw_mask(encoded, 10) != (
        sample_bits
    ):
        raise AssertionError("fixed-width little-endian mask codec drift")
    noncanonical = dict(encoded)
    noncanonical.update({
        "data_hex": "81  ",
        "members": 2,
        "sha256": hashlib.sha256(bytes.fromhex("81  ")).hexdigest(),
    })
    try:
        decode_raw_mask(noncanonical, 10)
    except AssertionError:
        pass
    else:
        raise AssertionError("noncanonical short decoded mask was accepted")
    pair = allowed_killed_pair(sample_bits, 10)
    allowed = decode_raw_mask(pair["allowed"], 10)
    killed = decode_raw_mask(pair["killed"], 10)
    if allowed & killed or allowed | killed != full_mask(10):
        raise AssertionError("allowed/killed mask partition drift")
    if primitive((-2, -4, -6)) != (1, 2, 3):
        raise AssertionError("primitive direction convention drift")
    direction, moment = line_key((1, 2, 3), (3, 6, 9))
    if cross((1, 2, 3), direction) != moment or cross(
        (3, 6, 9), direction
    ) != moment:
        raise AssertionError("direction/moment reconstruction drift")
    if general_position(((0, 0, 0), (1, 1, 1), (2, 2, 2))):
        raise AssertionError("synthetic collinear triple accepted")
    if not general_position(
        ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    ):
        raise AssertionError("synthetic general-position set rejected")

    accumulator = initial_accumulator()
    descriptor = {
        "channel": "old-new-new",
        "locality": "far-involved",
        "maximum_spatial_shell": 2,
        "obstruction_birth_relation": "synthetic",
        "obstruction_birth_rank_shell": 1,
        "endpoint_origin_birth_levels": [0],
        "endpoint_activation_relations": ["synthetic"],
    }
    record_witness(accumulator, 3, descriptor, {
        "channel": "old-new-new",
        "candidate_site": None,
        "candidate_offset": None,
        "old_endpoints": [],
        "exact_line": {
            "primitive_direction": [1, 0, 0],
            "relative_integer_moment": [0, 0, 0],
        },
    })
    stored = encode_accumulator(accumulator, 7)
    if decode_accumulator(stored, 7) != accumulator:
        raise AssertionError("hardened accumulator codec drift")
    if not terminal_pins_finalized():
        try:
            ensure_terminal_pins()
        except RuntimeError:
            fail_closed = True
        else:
            raise AssertionError("pending terminal pins did not lock execution")
    else:
        fail_closed = False
    return {
        "status": "passed",
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "large_artifacts_opened": False,
        "terminal_pins_finalized": terminal_pins_finalized(),
        "pending_pin_fail_closed_path_checked": fail_closed,
        "fixed_width_mask_bits_checked": 10,
        "noncanonical_short_hex_rejected": True,
        "direction_moment_geometry_checked": True,
        "synthetic_general_position_checked": True,
        "witness_to_mask_resume_reconstruction_checked": True,
    }


def preflight(args):
    started = time.monotonic()
    deadline = started + args.max_seconds
    policy = resource_policy(enforce=True)
    static, context = build_inputs(args, deadline)
    try:
        checkpoint = load_checkpoint(
            args.checkpoint, static, context, deadline
        )
        census = []
        total_units = 0
        total_site_endpoint_tests = 0
        total_old_new_moment_lookups = 0
        for probe in context["probes"]:
            enforce_cooperative_limits(deadline, "preflighting a probe domain")
            domain, model, intrinsic_bits, recheck = load_probe_domain_model(
                context, probe
            )
            points = context["point_sets"][probe["probe_id"]]["points"]
            site_atoms = len(model["site_id"])
            directions = len(model["line_by_direction"])
            units = site_atoms + len(points)
            total_units += units
            total_site_endpoint_tests += site_atoms * len(points)
            total_old_new_moment_lookups += directions * len(points)
            census.append({
                "probe_id": probe["probe_id"],
                "target_action_rank": probe["target_action_rank"],
                "observation_boundary_rank": probe[
                    "observation_boundary_rank"
                ],
                "prefix_position": probe["prefix_position"],
                "natural_gap": probe["natural_gap"],
                "step": probe["step"],
                "domain_words": len(domain),
                "intrinsic_words": intrinsic_bits.bit_count(),
                "placed_prefix_points": len(points),
                "site_atoms": site_atoms,
                "line_atoms": len(model["line_id"]),
                "line_directions": directions,
                "atom_universe": len(model["atom_desc"]),
                "atom_universe_sha256": stable_hash(model["atom_desc"]),
                "word_atom_incidence_sha256": stable_hash(
                    model["word_atoms"]
                ),
                "intrinsic_domain_recheck": recheck,
                "checkpoint_units": units,
            })
            del domain, model
            gc.collect()
        elapsed = time.monotonic() - started
        resident = maximum_resident_bytes()
        if elapsed > MAX_WORK_SECONDS or resident > MAX_RESIDENT_BYTES:
            raise RuntimeError("v2 preflight resource bound exceeded")
        return {
            "status": (
                "ready; terminal L6 construction/audit verified, exact "
                "chronological prefixes replayed, zero witness units scanned"
            ),
            "checker_sha256": PROCESS_START_CHECKER_SHA256,
            "static_state_sha256": static["static_state_sha256"],
            "terminal_pin_block": terminal_pin_block(),
            "probe_census": census,
            "same_corridor_pre_post_records": static[
                "same_corridor_pre_post_records"
            ],
            "adjacent_action_context_records": static[
                "adjacent_action_context_records"
            ],
            "work_estimate": {
                "checkpoint_units": total_units,
                "minimum_unit_cap_chunks": math.ceil(
                    total_units / DEFAULT_MAX_UNITS
                ),
                "site_endpoint_direction_tests": total_site_endpoint_tests,
                "old_new_new_moment_lookups": (
                    total_old_new_moment_lookups
                ),
                "warning": (
                    "prefix reconstruction and final raw-mask projection are "
                    "additional deterministic work; wall time may require "
                    "more chunks"
                ),
            },
            "checkpoint_status": checkpoint["status"],
            "completed_probes_in_checkpoint": checkpoint[
                "next_probe_index"
            ],
            "witness_units_scanned_by_preflight": 0,
            "resource_policy": policy,
            "elapsed_seconds": round(elapsed, 6),
            "maximum_resident_bytes": resident,
        }
    finally:
        close_inputs(context)


def estimate():
    return {
        "status": (
            "prepared and fail-closed pending immutable terminal L6 pins"
            if not terminal_pins_finalized()
            else "terminal pins filled; preflight is the next permitted phase"
        ),
        "checker_sha256": PROCESS_START_CHECKER_SHA256,
        "terminal_pin_block": terminal_pin_block(),
        "terminal_pins_finalized": terminal_pins_finalized(),
        "large_artifacts_opened": False,
        "files_written": False,
        "full_execution_locked_until_terminal_pins": True,
        "scope": {
            "L5_owner_gap": OWNER_L5_GAP,
            "L5_owner_rank": OWNER_L5_RANK,
            "actual_L5_word": list(OWNER_L5_WORD),
            "actual_L6_natural_gaps": list(OWNER_L6_GAPS),
            "exact_inverse_schedule_ranks": (
                "computed only after sealed L6 source/audit verification"
            ),
            "corridor_count": 1 + len(OWNER_L6_GAPS),
            "mask_probe_count": 1 + 2 * len(OWNER_L6_GAPS),
            "L5_parent_prefix_recomputed": True,
            "L6_same_corridor_pre_post_pairs": len(OWNER_L6_GAPS),
            "cross_step_raw_mask_projection": None,
        },
        "predicate_masks": [
            "zero-T",
            "intrinsic",
            "global-yz",
            "geometric",
            "combined",
        ],
        "mask_encoding": "fixed-width-little-endian-byte-hex",
        "resume_granularity": "one candidate-site atom or one old prefix point",
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "maximum_work_seconds_per_chunk": MAX_WORK_SECONDS,
        "hard_maximum_seconds_per_chunk": HARD_MAX_SECONDS,
        "maximum_resident_bytes": MAX_RESIDENT_BYTES,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("estimate", "self-check", "preflight", "run")
    )
    parser.add_argument(
        "--parent-source",
        default="/tmp/lattice-T-chronological-L5-primary.json",
    )
    parser.add_argument(
        "--parent-terminal",
        default="/tmp/lattice-T-chronological-L5-audit-v2.json",
    )
    parser.add_argument(
        "--metadata", default="/tmp/no-new-x-line-L5-canonical.json"
    )
    parser.add_argument(
        "--cache", default="/tmp/no-new-x-line-domains.bin"
    )
    parser.add_argument(
        "--lattice-result",
        default="/tmp/nonx-lattice-envelope-action-probe.json",
    )
    parser.add_argument(
        "--lattice-bitsets",
        default="/tmp/nonx-lattice-envelope-action-probe-bitsets.bin",
    )
    parser.add_argument("--l6-source", default=str(DEFAULT_L6_SOURCE))
    parser.add_argument("--l6-terminal", default=str(DEFAULT_L6_TERMINAL))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=float, default=MAX_WORK_SECONDS)
    parser.add_argument("--max-units", type=int, default=DEFAULT_MAX_UNITS)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= MAX_WORK_SECONDS:
        raise ValueError("max-seconds outside (0,110]")
    if not 1 <= args.max_units <= HARD_MAX_UNITS:
        raise ValueError("max-units outside [1,20000]")
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    elif args.mode == "preflight":
        result = preflight(args)
    else:
        checkpoint, observation = run_chunk(args)
        result = {
            "status": checkpoint["status"],
            "completed_probes": checkpoint["next_probe_index"],
            "total_probes": len(checkpoint["static"]["probe_records"]),
            "active_probe": checkpoint["active_probe"],
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "checkpoint_sha256": file_sha256(args.checkpoint),
            "terminal_summary": checkpoint["terminal_summary"],
            "observation": observation,
        }
    assert_checker_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
