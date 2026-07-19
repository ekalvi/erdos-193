#!/usr/bin/env python3
"""Independent terminal-pin report for the guarded lattice-T L6 source.

This is a narrow promotion tool, not the guarded-L6 terminal auditor.  It
opens the pinned primary-L5/L6 inputs read-only, reconstructs every selected
guarded-L6 connector, and emits candidate values for the 17 ``EXPECTED_*``
constants in ``lattice_t_l6_cone_guard_audit.py``.

The inherited L6 anchor skeleton is also censused in two deliberately
separate ways:

1. directly, from transformed L6 anchor differences; and
2. from primary-L5 differences, transporting the endpoints through M_BAL3.

Both formulations must produce the same 758 affine Pluecker records in the
auditor's exact pair order and schema.  No promoted-line enumerator from the
constructor or auditor is imported or called.

Run mode is fail-closed: all thread controls must equal one, process niceness
must be at least 15, the source and dependencies must remain unchanged, and
the only writable path is one atomic JSON report directly under /tmp.
Estimate and synthetic self-check modes open no large artifacts.

This report does *not* independently rescan rejected words, establish
first-survivor minimality, rerun exact no-three-collinear legality, or audit
new cone births.  Those remain duties of the separately pinned terminal
auditor after a human has reviewed and frozen the candidate constants.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from design import lattice_t_l6_continuation as producer  # noqa: E402


rescue = producer.rescue
l5 = producer.l5_producer
legacy = producer.legacy_l6

DEFAULT_SOURCE = Path("/tmp/lattice-T-chronological-L6-cone-guard-v1.json")
DEFAULT_OUTPUT = Path("/tmp/lattice-T-L6-cone-guard-pin-report-v1.json")
GUARD_CHECKER = ROOT / "design" / "lattice_t_l6_cone_birth_guard.py"

EXPECTED_DEPENDENCY_SHA256 = {
    "guard_checker": (
        "0a3041a77fffd954bd7ff2478427d1c7f6ea6f6951b9f8465c0a0966b6b3d376"
    ),
    "producer": (
        "048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906"
    ),
    "L5_producer": (
        "6310c6e23f03e26507005744985676388fba308cf08096a21abab017b6b90e51"
    ),
    "rescue": (
        "2b1bde9e846211cd53f75b6300c540a99b92d25b706c174c137f32c9cbf19ebc"
    ),
    "legacy_L6_helpers": (
        "eb5281e08a04ba78285b083341fbaa36eea6e05f3bdbaa352394794d0cbfdee5"
    ),
    "M_BAL3_provider": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "integer_matrix_apply_provider": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
}
EXPECTED_BASE_L6_STATIC_SHA256 = (
    "719ae1f97d8cf5cc87e37b849f4fe91a4e92e509a9129fbe48af5ef6fc77229d"
)
EXPECTED_GUARD_STATIC_SHA256 = (
    "e49ade10eb2fb82eef88f4469d1a2c5ac2acdb93ebba619170a86d8e3909dc60"
)
EXPECTED_GAPS = producer.EXPECTED_PARENT_STEPS
EXPECTED_ANCHORS = producer.EXPECTED_PARENT_POINTS
EXPECTED_PROMOTED_LINES = 758
EXPECTED_PAIR_CHECKS_PER_FORMULATION = EXPECTED_ANCHORS * (
    EXPECTED_ANCHORS - 1
) // 2
SPECTRA = (
    ("11/3", 11, 3),
    ("348/275", 348, 275),
)
SCHEMA_VERSION = 1
HARD_MAX_SECONDS = 900.0
HARD_MAX_RESIDENT_BYTES = 512 * 1024 * 1024
PAIR_CHECK_INTERVAL = 65_536
RECONSTRUCT_CHECK_INTERVAL = 100
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

SOURCE_TOP_LEVEL_KEYS = {
    "schema_version",
    "status",
    "static",
    "next_construction_rank",
    "selection_records",
    "pending_scan",
    "prefix",
    "obstruction",
    "last_run",
    "checkpoint_payload_sha256",
}
PREFIX_KEYS = {
    "next_construction_rank",
    "selection_record_stream_sha256",
    "placed_point_count",
    "construction_order_point_stream_sha256",
    "point_set_sha256",
    "yz_occupancy_stream_sha256",
    "doubled_fibre_stream_sha256",
    "prefix_state_sha256",
}
SELECTION_RECORD_KEYS = {
    "construction_rank",
    "gap",
    "step",
    "domain_words",
    "static_action_words",
    "first_survivor_ordinal_1_based",
    "cache_record_offset",
    "selected_word",
    "cone_birth_free",
    "certified_survivor_count",
    "certified_survivors",
    "survivor_census_exhaustive",
    "scan_counters_through_certificate",
    "first_projection_rejection_witness",
    "first_exact_legality_rejection_witness",
    "first_cone_birth_rejection_witness",
}
SURVIVOR_KEYS = {
    "ordinal_1_based",
    "cache_record_offset",
    "word",
    "intrinsic_projection_clean",
    "global_projection_clean",
    "zero_T_accepted",
    "ordered_T_accepted",
    "cone_birth_free",
}
COUNTER_KEYS = {
    "domain_words_scanned",
    "action_incompatible_skipped",
    "action_compatible_seen",
    "digit_rejected",
    "projection_rejected",
    "projection_clean_exact_tested",
    "exact_legality_rejected",
    "cone_birth_rejected",
}
AUDITOR_PIN_NAMES = (
    "EXPECTED_GUARD_CHECKER_SHA256",
    "EXPECTED_PRODUCER_SHA256",
    "EXPECTED_L5_PRODUCER_SHA256",
    "EXPECTED_RESCUE_SHA256",
    "EXPECTED_SOURCE_SHA256",
    "EXPECTED_SOURCE_BYTES",
    "EXPECTED_SOURCE_PAYLOAD_SHA256",
    "EXPECTED_SOURCE_STATIC_SHA256",
    "EXPECTED_SOURCE_PREFIX_SHA256",
    "EXPECTED_SOURCE_SELECTION_SHA256",
    "EXPECTED_SOURCE_MAX_FIRST_ORDINAL",
    "EXPECTED_POINTS",
    "EXPECTED_POINT_SET_SHA256",
    "EXPECTED_FINAL_YZ_SHA256",
    "EXPECTED_FINAL_DOUBLE_FIBRE_SHA256",
    "EXPECTED_PROMOTED_LINES",
    "EXPECTED_PROMOTED_LINE_STREAM_SHA256",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def exact_json_equal(left, right):
    return canonical_json(left) == canonical_json(right)


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


PROCESS_START_REPORT_SHA256 = file_sha256(Path(__file__).resolve())


def is_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def assert_report_unchanged():
    observed = file_sha256(Path(__file__).resolve())
    if observed != PROCESS_START_REPORT_SHA256:
        raise RuntimeError(
            "guarded-L6 pin reporter changed during execution",
            PROCESS_START_REPORT_SHA256,
            observed,
        )


def dependency_paths():
    return {
        "guard_checker": GUARD_CHECKER,
        "producer": Path(producer.__file__).resolve(),
        "L5_producer": Path(l5.__file__).resolve(),
        "rescue": Path(rescue.__file__).resolve(),
        "legacy_L6_helpers": Path(legacy.__file__).resolve(),
        "M_BAL3_provider": ROOT / "amplify_rich.py",
        "integer_matrix_apply_provider": ROOT / "imbricate193.py",
    }


def verify_dependencies():
    observed = {
        name: file_sha256(path)
        for name, path in dependency_paths().items()
    }
    if observed != EXPECTED_DEPENDENCY_SHA256:
        raise AssertionError(
            "guarded-L6 pin-report dependency drift",
            EXPECTED_DEPENDENCY_SHA256,
            observed,
        )
    return observed


def verify_producer_inputs_unchanged(
    args, expected_input_sha256, expected_parent_source,
    expected_parent_terminal, expected_d24_sha256,
):
    input_args = argparse.Namespace(
        metadata=args.metadata,
        cache=args.cache,
        lattice_result=args.lattice_result,
        lattice_bitsets=args.lattice_bitsets,
    )
    observed_input = l5.verify_inputs(input_args)
    if observed_input != expected_input_sha256:
        raise RuntimeError(
            "pinned L5/L6 input changed during pin extraction",
            expected_input_sha256,
            observed_input,
        )
    _source, source_snapshot = producer.verify_parent_source(
        args.parent_source
    )
    _terminal, terminal_snapshot = producer.verify_parent_terminal(
        args.parent_terminal, source_snapshot
    )
    if source_snapshot != expected_parent_source or terminal_snapshot != (
        expected_parent_terminal
    ):
        raise RuntimeError("pinned primary-L5 parent changed during extraction")
    _d24, d24_sha256 = legacy.load_d24_priority()
    ledger_sha256 = file_sha256(ROOT / "gate2-ledger-L6.json")
    expected_ledger_sha256 = legacy.EXPECTED_FROZEN_INPUT_SHA256[
        "gate2-ledger-L6.json"
    ]
    if d24_sha256 != expected_d24_sha256 or ledger_sha256 != (
        expected_ledger_sha256
    ):
        raise RuntimeError(
            "pinned D2--4 priority ledger changed during extraction",
            d24_sha256,
            ledger_sha256,
        )
    return observed_input


def maximum_resident_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    active_threads = threading.active_count()
    compliant = (
        all(value == "1" for value in environment.values())
        and nice >= 15
        and active_threads == 1
    )
    if enforce and not compliant:
        raise RuntimeError(
            "run requires every thread control=1, one active Python thread, "
            "and nice>=15",
            environment,
            active_threads,
            nice,
        )
    return {
        "processes": 1,
        "threads": 1,
        "active_python_threads_at_start": active_threads,
        "thread_environment": environment,
        "process_nice": nice,
        "required_minimum_nice": 15,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "hard_maximum_resident_bytes": HARD_MAX_RESIDENT_BYTES,
        "compliant": compliant,
    }


def guard_runtime(deadline, phase):
    if threading.active_count() != 1:
        raise RuntimeError("unexpected Python thread during " + phase)
    resident = maximum_resident_bytes()
    if resident > HARD_MAX_RESIDENT_BYTES:
        raise MemoryError(
            "guarded-L6 pin report exceeded resident-memory cap",
            phase,
            resident,
        )
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("guarded-L6 pin report reached time cap", phase)


def resolved(path):
    return Path(path).resolve()


def ensure_output_disjoint(args):
    output = resolved(args.output)
    temporary_root = Path("/tmp").resolve()
    if output.parent != temporary_root:
        raise ValueError(
            "pin report must be written directly under /tmp", str(output)
        )
    immutable = {
        "source": resolved(args.source),
        "parent_source": resolved(args.parent_source),
        "parent_terminal": resolved(args.parent_terminal),
        "metadata": resolved(args.metadata),
        "cache": resolved(args.cache),
        "lattice_result": resolved(args.lattice_result),
        "lattice_bitsets": resolved(args.lattice_bitsets),
        "pin_reporter": resolved(Path(__file__)),
        **{
            name: resolved(path)
            for name, path in dependency_paths().items()
        },
    }
    aliases = [name for name, path in immutable.items() if path == output]
    if aliases:
        raise ValueError(
            "pin-report output aliases immutable input", aliases, str(output)
        )
    return {
        "output": str(output),
        "immutable": {name: str(path) for name, path in immutable.items()},
    }


def stat_token(path):
    status = Path(path).stat()
    return {
        "device": status.st_dev,
        "inode": status.st_ino,
        "bytes": status.st_size,
        "mtime_ns": status.st_mtime_ns,
    }


def read_guard_source(path):
    path = resolved(path)
    before = stat_token(path)
    raw = path.read_bytes()
    after = stat_token(path)
    if before != after or len(raw) != before["bytes"]:
        raise RuntimeError("guarded-L6 source changed while being read")
    source = json.loads(raw.decode("utf-8"))
    if not isinstance(source, dict):
        raise AssertionError("guarded-L6 source is not a JSON object")
    payload = dict(source)
    internal = payload.pop("checkpoint_payload_sha256", None)
    observed_payload = stable_hash(payload)
    if internal != observed_payload or not is_sha256(internal):
        raise AssertionError(
            "guarded-L6 source payload seal drift", internal, observed_payload
        )
    snapshot = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "payload_sha256": internal,
    }
    return source, snapshot, before


def assert_source_unchanged(path, snapshot, token):
    path = resolved(path)
    observed_token = stat_token(path)
    observed_sha256 = file_sha256(path)
    if observed_token != token or observed_sha256 != snapshot["sha256"]:
        raise RuntimeError(
            "guarded-L6 source changed during pin extraction",
            token,
            observed_token,
            snapshot["sha256"],
            observed_sha256,
        )


def atomic_json_dump(value, path, pre_replace_check):
    path = resolved(path)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        pre_replace_check()
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def expected_guard_static(context):
    base_static = context["l6"]["static"]
    if base_static.get("static_state_sha256") != (
        EXPECTED_BASE_L6_STATIC_SHA256
    ):
        raise AssertionError(
            "base L6 static-state pin drift",
            base_static.get("static_state_sha256"),
        )
    result = {
        "checker_sha256": EXPECTED_DEPENDENCY_SHA256["guard_checker"],
        "producer_sha256": EXPECTED_DEPENDENCY_SHA256["producer"],
        "grandfathered_base_points": EXPECTED_ANCHORS,
        "grandfathering_rule": (
            "base-base secants are allowed; every secant whose later endpoint "
            "is a connector interior at the guarded level is classified"
        ),
        "spectra": [
            {
                "label": label,
                "numerator": numerator,
                "denominator": denominator,
                "polynomial": (
                    f"{denominator}*(3*y^2-y*z+3*z^2)-"
                    f"{numerator}*r^2"
                ),
            }
            for label, numerator, denominator in SPECTRA
        ],
        "scope_warning": "only the two displayed projective cones are controlled",
        "base_L6_static_state_sha256": EXPECTED_BASE_L6_STATIC_SHA256,
        "parent_terminal_sha256": producer.EXPECTED_PARENT_TERMINAL_SHA256,
        "mode": "guarded-first-survivor-construction",
        "guarded_level": 6,
        "base_policy": base_static["policy"],
        "grandfathered_points": EXPECTED_ANCHORS,
        "promoted_seed_lines": None,
        "strengthened_policy": (
            "zero-T AND global empty-yz AND exact fast/reference legality "
            "AND no new secant in either named projective cone"
        ),
        "selection_order": "compact-cache ordinal order",
        "stitch_order": "D2--4 fragile-first, then ordered gap index",
        "terminal_audits_required": [
            "independent ordinary firstness/no-three-collinear audit",
            "independent full new-cone-birth audit",
        ],
    }
    result["static_state_sha256"] = stable_hash(result)
    if result["static_state_sha256"] != EXPECTED_GUARD_STATIC_SHA256:
        raise AssertionError(
            "locally rebuilt guarded-L6 static pin drift",
            result["static_state_sha256"],
        )
    return result


def validate_source_envelope(source, expected_static):
    if set(source) != SOURCE_TOP_LEVEL_KEYS:
        raise AssertionError(
            "guarded-L6 source top-level schema drift",
            sorted(SOURCE_TOP_LEVEL_KEYS),
            sorted(source),
        )
    if type(source["schema_version"]) is not int or source[
        "schema_version"
    ] != SCHEMA_VERSION:
        raise AssertionError("guarded-L6 source schema-version drift")
    if source["status"] != "construction-complete-audit-pending":
        raise AssertionError("guarded-L6 source is not terminal/audit-pending")
    if source["pending_scan"] is not None or source["obstruction"] is not None:
        raise AssertionError("terminal guarded-L6 source retains failure state")
    if not exact_json_equal(source["static"], expected_static):
        raise AssertionError("guarded-L6 source static object drift")
    static_without_hash = dict(source["static"])
    internal_static = static_without_hash.pop("static_state_sha256", None)
    if internal_static != stable_hash(static_without_hash) or internal_static != (
        EXPECTED_GUARD_STATIC_SHA256
    ):
        raise AssertionError("guarded-L6 source static seal drift")

    records = source["selection_records"]
    if not isinstance(records, list) or len(records) != EXPECTED_GAPS:
        raise AssertionError("guarded-L6 source selection extent drift")
    if type(source["next_construction_rank"]) is not int or source[
        "next_construction_rank"
    ] != EXPECTED_GAPS:
        raise AssertionError("guarded-L6 source rank is not complete")
    prefix = source["prefix"]
    if not isinstance(prefix, dict) or set(prefix) != PREFIX_KEYS:
        raise AssertionError("guarded-L6 source prefix schema drift")
    prefix_without_hash = dict(prefix)
    internal_prefix = prefix_without_hash.pop("prefix_state_sha256", None)
    if not is_sha256(internal_prefix) or internal_prefix != stable_hash(
        prefix_without_hash
    ):
        raise AssertionError("guarded-L6 source prefix seal drift")
    selection_sha256 = stable_hash(records)
    if prefix["selection_record_stream_sha256"] != selection_sha256:
        raise AssertionError("guarded-L6 source selection digest drift")
    if type(prefix["next_construction_rank"]) is not int or prefix[
        "next_construction_rank"
    ] != EXPECTED_GAPS:
        raise AssertionError("guarded-L6 prefix rank drift")
    for key in ("placed_point_count",):
        require_plain_int(prefix[key], "guarded-L6 prefix integer drift", 1)
    for key in (
        "selection_record_stream_sha256",
        "construction_order_point_stream_sha256",
        "point_set_sha256",
        "yz_occupancy_stream_sha256",
        "doubled_fibre_stream_sha256",
        "prefix_state_sha256",
    ):
        if not is_sha256(prefix[key]):
            raise AssertionError("guarded-L6 prefix digest schema drift", key)

    last_run = source["last_run"]
    if not isinstance(last_run, dict) or last_run.get("stop_reason") != (
        "construction-complete"
    ):
        raise AssertionError("guarded-L6 terminal last-run marker drift")
    return {
        "selection_record_stream_sha256": selection_sha256,
        "prefix_state_sha256": internal_prefix,
        "static_state_sha256": internal_static,
    }


def require_plain_int(value, description, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        raise AssertionError(description, value)
    return value


def cache_word_at_offset(cache, block, offset):
    require_plain_int(offset, "cache record offset is not an integer", 0)
    if not block["start"] <= offset < block["end"]:
        raise AssertionError("cache record offset outside connector block")
    length = cache[offset]
    end = offset + 1 + length
    if not 1 <= length <= 255 or end > block["end"]:
        raise AssertionError("compact-cache record boundary drift")
    return tuple(cache[offset + 1:end])


def action_accepts(bitset, action_record, channel, ordinal):
    if not 1 <= ordinal <= action_record["words"]:
        raise AssertionError("action ordinal outside connector domain")
    selected = action_record[channel]
    index = ordinal - 1
    return bool(
        bitset[selected["offset"] + (index >> 3)] & (1 << (index & 7))
    )


def intrinsic_projection_clean(start, target, interiors):
    fibres = [point[1:] for point in interiors]
    return (
        len(fibres) == len(set(fibres))
        and not {start[1:], target[1:]}.intersection(fibres)
    )


def global_projection_clean(interiors, yz_counts):
    local = set()
    for point in interiors:
        fibre = point[1:]
        if fibre in yz_counts or fibre in local:
            return False
        local.add(fibre)
    return True


def expected_selected_offsets(context, records, deadline):
    requested = defaultdict(set)
    schedule = context["l6"]["schedule"]
    parent_word = context["l6"]["parent_word"]
    for rank, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != SELECTION_RECORD_KEYS:
            raise AssertionError("selection-record schema drift", rank)
        gap = schedule[rank]
        step = parent_word[gap]
        identity = tuple(require_plain_int(
            record.get(key), "selection identity is not an integer", 0
        ) for key in ("construction_rank", "gap", "step"))
        if identity != (rank, gap, step):
            raise AssertionError("selection-record schedule drift", rank, identity)
        ordinal = require_plain_int(
            record.get("first_survivor_ordinal_1_based"),
            "selected ordinal is not a positive integer",
            1,
        )
        block = context["blocks"][step]
        if ordinal > block["words"]:
            raise AssertionError("selected ordinal outside domain", rank, ordinal)
        requested[step].add(ordinal)

    result = {}
    for step in sorted(requested):
        block = context["blocks"][step]
        wanted = requested[step]
        maximum = max(wanted)
        cursor = block["start"]
        for ordinal in range(1, maximum + 1):
            if ordinal % PAIR_CHECK_INTERVAL == 1:
                guard_runtime(deadline, "mapping selected cache ordinals")
            offset = cursor
            if not block["start"] <= cursor < block["end"]:
                raise AssertionError("compact-cache ordinal cursor drift", step)
            length = context["cache"][cursor]
            cursor += 1 + length
            if not 1 <= length <= 255 or cursor > block["end"]:
                raise AssertionError("compact-cache ordinal boundary drift", step)
            if ordinal in wanted:
                result[(step, ordinal)] = offset
        if len([key for key in result if key[0] == step]) != len(wanted):
            raise AssertionError("failed to map every selected cache ordinal", step)
    return result


def validate_scan_counters(counters, ordinal, rank):
    if not isinstance(counters, dict) or set(counters) != COUNTER_KEYS:
        raise AssertionError("selection scan-counter schema drift", rank)
    for key, value in counters.items():
        require_plain_int(value, "selection counter is not nonnegative", 0)
    if counters["domain_words_scanned"] != ordinal:
        raise AssertionError("selection scan did not stop at recorded ordinal", rank)
    if counters["action_incompatible_skipped"] + counters[
        "action_compatible_seen"
    ] != ordinal:
        raise AssertionError("selection action partition drift", rank)
    if counters["digit_rejected"] != 0:
        raise AssertionError("guarded L6 unexpectedly used a digit filter", rank)
    if counters["projection_rejected"] + counters[
        "projection_clean_exact_tested"
    ] != counters["action_compatible_seen"]:
        raise AssertionError("selection projection partition drift", rank)
    if counters["exact_legality_rejected"] + counters[
        "cone_birth_rejected"
    ] + 1 != counters["projection_clean_exact_tested"]:
        raise AssertionError("selection exact/cone partition drift", rank)


def prefix_commitment(store, yz_counts, records, rank):
    fields = {
        "next_construction_rank": rank,
        "selection_record_stream_sha256": stable_hash(records),
        "placed_point_count": len(store.pts),
        "construction_order_point_stream_sha256": point_stream_sha256(
            store.pts
        ),
        "point_set_sha256": stable_hash(sorted(store.pset)),
        "yz_occupancy_stream_sha256": stable_hash(sorted(yz_counts.items())),
        "doubled_fibre_stream_sha256": stable_hash(sorted(
            fibre for fibre, count in yz_counts.items() if count == 2
        )),
    }
    fields["prefix_state_sha256"] = stable_hash(fields)
    return fields


def reconstruct_selection(context, source, deadline):
    records = source["selection_records"]
    l6_state = context["l6"]
    anchors = l6_state["anchors"]
    if len(anchors) != EXPECTED_ANCHORS:
        raise AssertionError("guarded-L6 anchor extent drift")
    offsets = expected_selected_offsets(context, records, deadline)
    store = rescue.Store(anchors)
    yz_counts = Counter(point[1:] for point in anchors)
    selected_by_gap = {}
    ordinals = []
    total_interiors = 0

    for rank, record in enumerate(records):
        if rank % RECONSTRUCT_CHECK_INTERVAL == 0:
            guard_runtime(deadline, "reconstructing selected guarded-L6 geometry")
        gap = l6_state["schedule"][rank]
        step = l6_state["parent_word"][gap]
        block = context["blocks"][step]
        action_record = context["action_records"][step]
        domain_words = require_plain_int(
            record["domain_words"], "selection domain extent is not positive", 1
        )
        static_action_words = require_plain_int(
            record["static_action_words"],
            "selection action extent is not nonnegative",
            0,
        )
        if domain_words != block["words"] or static_action_words != (
            action_record["zero"]["set_bits"]
        ):
            raise AssertionError("selection domain/action extent drift", rank)

        ordinal = record["first_survivor_ordinal_1_based"]
        recorded_offset = require_plain_int(
            record["cache_record_offset"],
            "selected cache offset is not a nonnegative integer",
            0,
        )
        if recorded_offset != offsets[(step, ordinal)]:
            raise AssertionError(
                "selected cache offset does not match its ordinal", rank
            )
        word = cache_word_at_offset(context["cache"], block, recorded_offset)
        if not isinstance(record["selected_word"], list) or not exact_json_equal(
            record["selected_word"], list(word)
        ):
            raise AssertionError("selected cache word drift", rank)
        if not action_accepts(
            context["bitset"], action_record, "zero", ordinal
        ):
            raise AssertionError("selected word lost zero-T membership", rank)

        start = anchors[gap]
        target = anchors[gap + 1]
        interiors = tuple(rescue.word_interiors(start, word))
        if rescue.endpoint(start, word) != target:
            raise AssertionError("selected connector endpoint drift", rank)
        intrinsic = intrinsic_projection_clean(start, target, interiors)
        global_clean = global_projection_clean(interiors, yz_counts)
        if not intrinsic or not global_clean:
            raise AssertionError("selected connector projection drift", rank)
        if len(interiors) != len(set(interiors)) or any(
            point in store.pset for point in interiors
        ):
            raise AssertionError("selected connector repeats a point", rank)

        expected_survivor = {
            "ordinal_1_based": ordinal,
            "cache_record_offset": recorded_offset,
            "word": list(word),
            "intrinsic_projection_clean": True,
            "global_projection_clean": True,
            "zero_T_accepted": True,
            "ordered_T_accepted": action_accepts(
                context["bitset"], action_record, "ordered", ordinal
            ),
            "cone_birth_free": True,
        }
        survivors = record["certified_survivors"]
        if (
            record["cone_birth_free"] is not True
            or type(record["certified_survivor_count"]) is not int
            or record["certified_survivor_count"] != 1
            or record["survivor_census_exhaustive"] is not False
            or not isinstance(survivors, list)
            or len(survivors) != 1
            or not isinstance(survivors[0], dict)
            or set(survivors[0]) != SURVIVOR_KEYS
            or not exact_json_equal(survivors[0], expected_survivor)
        ):
            raise AssertionError("selected survivor certificate drift", rank)
        validate_scan_counters(
            record["scan_counters_through_certificate"], ordinal, rank
        )
        witness_counters = {
            "first_projection_rejection_witness": "projection_rejected",
            "first_exact_legality_rejection_witness": (
                "exact_legality_rejected"
            ),
            "first_cone_birth_rejection_witness": "cone_birth_rejected",
        }
        counters = record["scan_counters_through_certificate"]
        for witness_key, counter_key in witness_counters.items():
            witness = record[witness_key]
            if witness is not None and not isinstance(witness, dict):
                raise AssertionError("selection witness schema drift", rank)
            if (witness is None) != (counters[counter_key] == 0):
                raise AssertionError("selection witness/count drift", rank)

        for point in interiors:
            yz_counts[point[1:]] += 1
        store.add_many(interiors)
        if gap in selected_by_gap:
            raise AssertionError("guarded-L6 gap selected twice", gap)
        selected_by_gap[gap] = (word, interiors)
        ordinals.append(ordinal)
        total_interiors += len(interiors)

    if set(selected_by_gap) != set(range(EXPECTED_GAPS)):
        raise AssertionError("guarded-L6 selection does not cover every gap")
    observed_prefix = prefix_commitment(
        store, yz_counts, records, EXPECTED_GAPS
    )
    if not exact_json_equal(observed_prefix, source["prefix"]):
        raise AssertionError("reconstructed guarded-L6 prefix drift")

    doubled = {
        fibre for fibre, count in yz_counts.items() if count == 2
    }
    if doubled != l6_state["initial_double_fibres"] or max(
        yz_counts.values(), default=0
    ) != 2:
        raise AssertionError("selected geometry changed inherited double fibres")

    chain = [anchors[0]]
    flat_word = []
    for gap in range(EXPECTED_GAPS):
        if chain[-1] != anchors[gap]:
            raise AssertionError("natural guarded-L6 chain lost its anchor")
        word, interiors = selected_by_gap[gap]
        chain.extend(interiors)
        chain.append(anchors[gap + 1])
        flat_word.extend(word)
    if len(chain) != len(set(chain)):
        raise AssertionError("natural guarded-L6 chain repeats a point")
    if len(chain) != len(store.pts) or set(chain) != store.pset:
        raise AssertionError("natural and construction-order point sets differ")
    natural_yz = Counter(point[1:] for point in chain)
    if natural_yz != yz_counts:
        raise AssertionError("natural and construction-order yz states differ")

    return {
        "gaps": EXPECTED_GAPS,
        "anchors": EXPECTED_ANCHORS,
        "points": len(chain),
        "selected_interiors": total_interiors,
        "maximum_first_survivor_ordinal_1_based": max(ordinals),
        "sum_first_survivor_ordinals": sum(ordinals),
        "selection_record_stream_sha256": stable_hash(records),
        "construction_order_point_stream_sha256": (
            observed_prefix["construction_order_point_stream_sha256"]
        ),
        "natural_ordered_point_stream_sha256": point_stream_sha256(chain),
        "natural_flat_step_word_sha256": hashlib.sha256(
            bytes(flat_word)
        ).hexdigest(),
        "point_set_sha256": stable_hash(sorted(chain)),
        "final_yz_occupancy_sha256": stable_hash(sorted(natural_yz.items())),
        "final_double_fibre_sha256": stable_hash(sorted(doubled)),
        "final_double_fibres": len(doubled),
        "prefix": observed_prefix,
    }


def load_primary_l5_preimage(args, context):
    source, source_snapshot = producer.verify_parent_source(args.parent_source)
    terminal, terminal_snapshot = producer.verify_parent_terminal(
        args.parent_terminal, source_snapshot
    )
    if source_snapshot != context["source_snapshot"] or terminal_snapshot != (
        context["terminal_snapshot"]
    ):
        raise AssertionError("primary-L5 preimage snapshots disagree with L6")
    parent = producer.reconstruct_ordered_parent(source, terminal)
    points = tuple(parent["points"])
    transported = tuple(producer.apply(producer.M_BAL3, point) for point in points)
    if len(points) != EXPECTED_ANCHORS or transported != context["l6"][
        "anchors"
    ]:
        raise AssertionError("primary-L5 preimage does not transport to L6 anchors")
    return points, {
        "source": source_snapshot,
        "terminal": terminal_snapshot,
        "ordered_point_stream_sha256": point_stream_sha256(points),
        "transported_anchor_stream_sha256": point_stream_sha256(transported),
    }


def direct_matches(direction):
    r, y, z = direction
    quadratic = 3 * y * y - y * z + 3 * z * z
    return tuple(
        label
        for label, numerator, denominator in SPECTRA
        if denominator * quadratic - numerator * r * r == 0
    )


def direct_primitive(vector):
    divisor = gcd(gcd(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    if divisor == 0:
        raise AssertionError("zero displacement in direct anchor census")
    primitive = tuple(value // divisor for value in vector)
    if next(value for value in primitive if value) < 0:
        primitive = tuple(-value for value in primitive)
    return primitive


def direct_cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def enumerate_direct_transformed_anchors(points, deadline):
    records = []
    line_keys = set()
    pair_checks = 0
    for later_id, later in enumerate(points):
        for earlier_id in range(later_id):
            pair_checks += 1
            if pair_checks % PAIR_CHECK_INTERVAL == 0:
                guard_runtime(deadline, "direct transformed-anchor cone census")
            earlier = points[earlier_id]
            direction = tuple(
                later[axis] - earlier[axis] for axis in range(3)
            )
            matches = direct_matches(direction)
            if not matches:
                continue
            primitive = direct_primitive(direction)
            moment = direct_cross(earlier, primitive)
            key = (primitive, moment)
            if key in line_keys:
                raise AssertionError(
                    "direct census found three anchors on one promoted line"
                )
            line_keys.add(key)
            records.append({
                "earlier_point_id": earlier_id,
                "later_point_id": later_id,
                "matched_spectra": list(matches),
                "canonical_primitive_direction": list(primitive),
                "exact_Pluecker_moment": list(moment),
            })
    return tuple(records), pair_checks


def transport_primitive(vector):
    common = gcd(abs(vector[0]), abs(vector[1]))
    common = gcd(common, abs(vector[2]))
    if not common:
        raise AssertionError("zero displacement in preimage transport census")
    normalized = (
        vector[0] // common,
        vector[1] // common,
        vector[2] // common,
    )
    first = normalized[0] or normalized[1] or normalized[2]
    if first < 0:
        normalized = (-normalized[0], -normalized[1], -normalized[2])
    return normalized


def transport_cross(anchor, direction):
    ax, ay, az = anchor
    dx, dy, dz = direction
    return (
        ay * dz - az * dy,
        az * dx - ax * dz,
        ax * dy - ay * dx,
    )


def enumerate_primary_preimage_transport(primary_points, expected_anchors, deadline):
    transported_points = tuple(
        producer.apply(producer.M_BAL3, point) for point in primary_points
    )
    if transported_points != tuple(expected_anchors):
        raise AssertionError("preimage transport missed the expected L6 anchors")
    records = []
    line_keys = set()
    pair_checks = 0
    for later_id in range(len(primary_points)):
        primary_later = primary_points[later_id]
        transported_later = transported_points[later_id]
        for earlier_id in range(later_id):
            pair_checks += 1
            if pair_checks % PAIR_CHECK_INTERVAL == 0:
                guard_runtime(deadline, "primary-L5 preimage transport census")
            primary_earlier = primary_points[earlier_id]
            pr = primary_later[0] - primary_earlier[0]
            py = primary_later[1] - primary_earlier[1]
            pz = primary_later[2] - primary_earlier[2]
            primary_quadratic = 3 * py * py - py * pz + 3 * pz * pz

            transported_earlier = transported_points[earlier_id]
            tr = transported_later[0] - transported_earlier[0]
            ty = transported_later[1] - transported_earlier[1]
            tz = transported_later[2] - transported_earlier[2]
            transported_quadratic = 3 * ty * ty - ty * tz + 3 * tz * tz

            matches = []
            for label, numerator, denominator in SPECTRA:
                primary_residual = (
                    denominator * primary_quadratic - numerator * pr * pr
                )
                transported_residual = (
                    denominator * transported_quadratic - numerator * tr * tr
                )
                if transported_residual != 9 * primary_residual:
                    raise AssertionError(
                        "M_BAL3 cone-residual transfer identity drift",
                        earlier_id,
                        later_id,
                        label,
                    )
                if primary_residual == 0:
                    matches.append(label)
            if not matches:
                continue
            transported_direction = (tr, ty, tz)
            primitive = transport_primitive(transported_direction)
            moment = transport_cross(transported_earlier, primitive)
            key = (primitive, moment)
            if key in line_keys:
                raise AssertionError(
                    "preimage census found three anchors on one promoted line"
                )
            line_keys.add(key)
            records.append({
                "earlier_point_id": earlier_id,
                "later_point_id": later_id,
                "matched_spectra": matches,
                "canonical_primitive_direction": list(primitive),
                "exact_Pluecker_moment": list(moment),
            })
    return tuple(records), pair_checks


def validate_auditor_pin_candidates(candidates):
    if tuple(candidates) != AUDITOR_PIN_NAMES:
        raise AssertionError("auditor pin-candidate order/schema drift")
    hash_names = {
        name for name in AUDITOR_PIN_NAMES if name.endswith("SHA256")
    }
    for name in hash_names:
        if not is_sha256(candidates[name]):
            raise AssertionError("invalid SHA-256 candidate", name)
    integer_names = set(AUDITOR_PIN_NAMES) - hash_names
    for name in integer_names:
        require_plain_int(candidates[name], "invalid integer pin candidate", 1)


def build_report(
    args, resource_record, path_record, dependencies, source_snapshot,
    source_commitments, producer_input_sha256, reconstruction,
    primary_snapshot, direct_records, direct_pairs, transport_records,
    transport_pairs, elapsed,
):
    if direct_pairs != EXPECTED_PAIR_CHECKS_PER_FORMULATION or transport_pairs != (
        EXPECTED_PAIR_CHECKS_PER_FORMULATION
    ):
        raise AssertionError("promoted-line pair census extent drift")
    if direct_records != transport_records:
        raise AssertionError(
            "direct and primary-preimage promoted-line records disagree"
        )
    if len(direct_records) != EXPECTED_PROMOTED_LINES:
        raise AssertionError(
            "promoted-line count drift", len(direct_records),
            EXPECTED_PROMOTED_LINES,
        )
    direct_digest = stable_hash(direct_records)
    transport_digest = stable_hash(transport_records)
    if direct_digest != transport_digest:
        raise AssertionError("promoted-line formulation digest disagreement")

    candidates = {
        "EXPECTED_GUARD_CHECKER_SHA256": dependencies["guard_checker"],
        "EXPECTED_PRODUCER_SHA256": dependencies["producer"],
        "EXPECTED_L5_PRODUCER_SHA256": dependencies["L5_producer"],
        "EXPECTED_RESCUE_SHA256": dependencies["rescue"],
        "EXPECTED_SOURCE_SHA256": source_snapshot["sha256"],
        "EXPECTED_SOURCE_BYTES": source_snapshot["bytes"],
        "EXPECTED_SOURCE_PAYLOAD_SHA256": source_snapshot["payload_sha256"],
        "EXPECTED_SOURCE_STATIC_SHA256": source_commitments[
            "static_state_sha256"
        ],
        "EXPECTED_SOURCE_PREFIX_SHA256": reconstruction["prefix"][
            "prefix_state_sha256"
        ],
        "EXPECTED_SOURCE_SELECTION_SHA256": reconstruction[
            "selection_record_stream_sha256"
        ],
        "EXPECTED_SOURCE_MAX_FIRST_ORDINAL": reconstruction[
            "maximum_first_survivor_ordinal_1_based"
        ],
        "EXPECTED_POINTS": reconstruction["points"],
        "EXPECTED_POINT_SET_SHA256": reconstruction["point_set_sha256"],
        "EXPECTED_FINAL_YZ_SHA256": reconstruction[
            "final_yz_occupancy_sha256"
        ],
        "EXPECTED_FINAL_DOUBLE_FIBRE_SHA256": reconstruction[
            "final_double_fibre_sha256"
        ],
        "EXPECTED_PROMOTED_LINES": len(direct_records),
        "EXPECTED_PROMOTED_LINE_STREAM_SHA256": direct_digest,
    }
    validate_auditor_pin_candidates(candidates)

    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete pin candidates; not a terminal audit",
        "reporter": {
            "path": "design/lattice_t_l6_cone_guard_pin_report.py",
            "sha256": PROCESS_START_REPORT_SHA256,
            "unchanged_before_atomic_promotion": True,
        },
        "source_checkpoint": source_snapshot,
        "pinned_dependencies": dependencies,
        "pinned_producer_inputs": producer_input_sha256,
        "paths": path_record,
        "resource_policy": resource_record,
        "elapsed_seconds_before_atomic_write": round(elapsed, 6),
        "source_verification": {
            "terminal_status": "construction-complete-audit-pending",
            "top_level_schema_exact": True,
            "payload_seal_recomputed": True,
            "static_object_rebuilt_exactly": True,
            "static_state_sha256": source_commitments[
                "static_state_sha256"
            ],
            "prefix_seal_recomputed": True,
            "prefix_state_sha256": source_commitments[
                "prefix_state_sha256"
            ],
            "selection_stream_rehashed": True,
            "selection_record_stream_sha256": source_commitments[
                "selection_record_stream_sha256"
            ],
            "source_opened_read_only": True,
        },
        "selected_geometry_reconstruction": reconstruction,
        "primary_L5_preimage": primary_snapshot,
        "promoted_base_cone_lines": {
            "count": len(direct_records),
            "line_stream_sha256": direct_digest,
            "pair_order": "later anchor id, then earlier anchor id",
            "record_schema": (
                "auditor earlier/later ids, matched spectra, canonical "
                "primitive direction, exact Pluecker moment"
            ),
            "direct_transformed_anchor_formulation": {
                "pair_checks": direct_pairs,
                "count": len(direct_records),
                "line_stream_sha256": direct_digest,
            },
            "primary_L5_preimage_transport_formulation": {
                "pair_checks": transport_pairs,
                "count": len(transport_records),
                "line_stream_sha256": transport_digest,
                "M_BAL3_residual_identity_checked_for_every_pair_and_spectrum": True,
            },
            "formulations_agree_record_for_record": True,
            "records": list(direct_records),
        },
        "auditor_pin_candidates": candidates,
        "proved_by_this_report": [
            "the terminal source has the exact guarded-L6 schema, payload seal, policy static state, and complete extent",
            "every selected word is the cache word at its recorded ordinal and retains the pinned zero-T and projection properties",
            "the selected finite geometry reproduces the source prefix, point-set, yz, and doubled-fibre commitments",
            "two separate exact formulations produce the same 758 inherited anchor cone-line records",
        ],
        "not_proved_by_this_report": [
            "that no earlier connector word survives the complete guarded policy",
            "reference/fast exact legality or ordinary no-three-collinear legality of the selected L6 walk",
            "absence of new target-cone secants involving connector interiors",
            "positive connector availability beyond this finite L6 construction",
            "a generic far-secant tail lemma or an unconditional infinite theorem",
        ],
        "promotion_warning": (
            "review these candidates before freezing the guarded-L6 auditor; "
            "this report is not a substitute for running that auditor"
        ),
    }
    report["report_payload_sha256"] = stable_hash(report)
    return report


def run_report(args, resource_record, path_record):
    started = time.monotonic()
    deadline = started + args.max_seconds
    dependencies = verify_dependencies()
    source, source_snapshot, source_token = read_guard_source(args.source)
    context = producer.open_context(args)
    try:
        producer_input_sha256 = dict(context["input_sha256"])
        parent_source_snapshot = dict(context["source_snapshot"])
        parent_terminal_snapshot = dict(context["terminal_snapshot"])
        d24_sha256 = context["l6"]["static"]["d24_priority_map_sha256"]
        expected_static = expected_guard_static(context)
        source_commitments = validate_source_envelope(source, expected_static)
        reconstruction = reconstruct_selection(context, source, deadline)
        primary_points, primary_snapshot = load_primary_l5_preimage(
            args, context
        )
        direct_records, direct_pairs = enumerate_direct_transformed_anchors(
            context["l6"]["anchors"], deadline
        )
        transport_records, transport_pairs = (
            enumerate_primary_preimage_transport(
                primary_points, context["l6"]["anchors"], deadline
            )
        )
        guard_runtime(deadline, "finalizing guarded-L6 pin report")
        report = build_report(
            args,
            resource_record,
            path_record,
            dependencies,
            source_snapshot,
            source_commitments,
            producer_input_sha256,
            reconstruction,
            primary_snapshot,
            direct_records,
            direct_pairs,
            transport_records,
            transport_pairs,
            time.monotonic() - started,
        )
    finally:
        producer.close_context(context)

    def pre_replace_check():
        assert_report_unchanged()
        if verify_dependencies() != dependencies:
            raise RuntimeError("dependency changed before pin-report promotion")
        assert_source_unchanged(args.source, source_snapshot, source_token)
        observed_input = verify_producer_inputs_unchanged(
            args,
            producer_input_sha256,
            parent_source_snapshot,
            parent_terminal_snapshot,
            d24_sha256,
        )
        if observed_input != producer_input_sha256:
            raise RuntimeError("producer input changed before report promotion")
        guard_runtime(deadline, "revalidating inputs before report promotion")
        resource_policy(enforce=True)

    atomic_json_dump(report, args.output, pre_replace_check)
    assert_report_unchanged()
    return {
        "status": report["status"],
        "output": str(resolved(args.output)),
        "output_sha256": file_sha256(args.output),
        "report_payload_sha256": report["report_payload_sha256"],
        "auditor_pin_candidates": report["auditor_pin_candidates"],
    }


def estimate():
    return {
        "status": "prepared independent guarded-L6 terminal-pin report",
        "reporter_sha256": PROCESS_START_REPORT_SHA256,
        "expected_gaps": EXPECTED_GAPS,
        "expected_anchors": EXPECTED_ANCHORS,
        "expected_promoted_lines": EXPECTED_PROMOTED_LINES,
        "pair_checks_per_formulation": EXPECTED_PAIR_CHECKS_PER_FORMULATION,
        "total_promoted_line_pair_checks": (
            2 * EXPECTED_PAIR_CHECKS_PER_FORMULATION
        ),
        "promoted_line_formulations": [
            "direct transformed L6 anchors",
            "primary-L5 preimage with exact M_BAL3 transport",
        ],
        "processes": 1,
        "threads": 1,
        "required_minimum_nice": 15,
        "hard_maximum_seconds": HARD_MAX_SECONDS,
        "large_artifacts_opened": False,
        "source_writes": 0,
        "output": str(DEFAULT_OUTPUT),
    }


def self_check():
    if direct_matches((3, -3, 1)) != ("11/3",):
        raise AssertionError("synthetic 11/3 cone witness drift")
    if direct_matches((55, 34, 18)) != ("348/275",):
        raise AssertionError("synthetic 348/275 cone witness drift")
    if direct_matches((1, 0, 0)):
        raise AssertionError("synthetic non-cone direction misclassified")
    if direct_primitive((-2, -4, 6)) != (1, 2, -3):
        raise AssertionError("direct primitive sign normalization drift")
    if transport_primitive((2, 4, -6)) != (1, 2, -3):
        raise AssertionError("transport primitive normalization drift")

    primary = ((0, 0, 0), (3, -3, 1), (55, 34, 18))
    transformed = tuple(
        producer.apply(producer.M_BAL3, point) for point in primary
    )
    direct, direct_pairs = enumerate_direct_transformed_anchors(
        transformed, None
    )
    transported, transport_pairs = enumerate_primary_preimage_transport(
        primary, transformed, None
    )
    if direct != transported or direct_pairs != 3 or transport_pairs != 3:
        raise AssertionError("synthetic two-formulation census disagreement")
    if {label for record in direct for label in record["matched_spectra"]} != {
        "11/3", "348/275"
    }:
        raise AssertionError("synthetic two-spectrum census drift")
    return {
        "status": "synthetic self-check passed",
        "reporter_sha256": PROCESS_START_REPORT_SHA256,
        "synthetic_pair_checks_per_formulation": 3,
        "synthetic_promoted_records": len(direct),
        "two_formulations_agree": True,
        "large_artifacts_opened": False,
        "source_writes": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "self-check", "run"))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument(
        "--parent-source", default=str(producer.DEFAULT_PARENT_SOURCE)
    )
    parser.add_argument(
        "--parent-terminal", default=str(producer.DEFAULT_PARENT_TERMINAL)
    )
    parser.add_argument("--metadata", default=str(rescue.DEFAULT_METADATA))
    parser.add_argument("--cache", default=str(rescue.DEFAULT_CACHE))
    parser.add_argument(
        "--lattice-result", default=str(l5.DEFAULT_LATTICE_RESULT)
    )
    parser.add_argument(
        "--lattice-bitsets", default=str(l5.DEFAULT_LATTICE_BITSETS)
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-seconds", type=float, default=HARD_MAX_SECONDS)
    args = parser.parse_args()
    if not 0 < args.max_seconds <= HARD_MAX_SECONDS:
        raise ValueError("max-seconds outside (0,900]")

    resource_record = resource_policy(enforce=args.mode == "run")
    if args.mode == "estimate":
        result = estimate()
    elif args.mode == "self-check":
        result = self_check()
    else:
        path_record = ensure_output_disjoint(args)
        result = run_report(args, resource_record, path_record)
    assert_report_unchanged()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
