#!/usr/bin/env python3
"""Build a compact finite prefix of the proposed Hilbert walk.

The default artifact contains 400,000 retained vertices, enough to exceed the
repository's current 311,738-vertex finite record.  The output is a byte-coded
step word plus a JSON manifest.  Generation is deterministic, exact, atomic,
and idempotent: an existing compatible artifact is validated and reused unless
``--force`` is supplied.

This script constructs a candidate witness; it does not certify the all-length
Hilbert valuation lemma or absence of collinear triples.  Use
``verify_hilbert_record.py structural`` for an independent linear audit and
``verify_hilbert_record.py run`` for the resumable exhaustive direction audit.

Examples:

    python3 -B hilbert_record.py
    python3 -B hilbert_record.py --count 400000
    python3 -B hilbert_record.py --output-dir /tmp/hilbert-smoke --count 4096
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_COUNT = 400_000
SCHEMA = "hilbert-193-record-v1"
_STOP_REQUESTED = False

# Standard infinite quadrant Hilbert traversal, matching Math::PlanePath.
_NEXT_STATE = (
    4, 0, 0, 12,
    0, 4, 4, 8,
    12, 8, 8, 4,
    8, 12, 12, 0,
)
_DIGIT_X = (
    0, 1, 1, 0,
    0, 0, 1, 1,
    1, 0, 0, 1,
    1, 1, 0, 0,
)
_DIGIT_Y = (
    0, 0, 1, 1,
    0, 1, 1, 0,
    1, 1, 0, 0,
    1, 0, 0, 1,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode()).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, payload: Any) -> None:
    atomic_bytes(path, (stable_json(payload) + "\n").encode())


class Log:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **fields: Any) -> None:
        record = {"at": now(), "event": event, **fields}
        line = (stable_json(record) + "\n").encode()
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(descriptor, line)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        print(
            f"[{record['at']}] {event} "
            + " ".join(f"{key}={value}" for key, value in fields.items()),
            flush=True,
        )


def request_stop(_signum: int, _frame: object) -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True


def digits4_low(number: int) -> list[int]:
    if number == 0:
        return [0]
    digits: list[int] = []
    while number:
        digits.append(number & 3)
        number >>= 2
    return digits


def hilbert_xy(number: int) -> tuple[int, int]:
    digits = digits4_low(number)
    last = len(digits) - 1
    state = 4 if last & 1 else 0
    x_bits = [0] * len(digits)
    y_bits = [0] * len(digits)
    for index in range(last, -1, -1):
        table_index = state + digits[index]
        x_bits[index] = _DIGIT_X[table_index]
        y_bits[index] = _DIGIT_Y[table_index]
        state = _NEXT_STATE[table_index]
    x = sum(bit << index for index, bit in enumerate(x_bits))
    y = sum(bit << index for index, bit in enumerate(y_bits))
    return x, y


def colour(number: int) -> tuple[int, int]:
    count_12 = 0
    count_3 = 0
    for digit in digits4_low(number):
        if digit in (1, 2):
            count_12 ^= 1
        elif digit == 3:
            count_3 ^= 1
    return count_12, count_3


def artifact_paths(output_dir: Path, count: int) -> tuple[Path, Path, Path]:
    stem = f"hilbert-193-{count}"
    default_output_dir = ROOT / "viz"
    log_dir = ROOT / "logs" if output_dir.resolve() == default_output_dir.resolve() else output_dir
    return (
        output_dir / f"{stem}.steps.bin",
        output_dir / f"{stem}-manifest.json",
        log_dir / f"{stem}-build.jsonl",
    )


def validate_existing(step_path: Path, manifest_path: Path, count: int) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != SCHEMA:
        raise RuntimeError("existing manifest schema mismatch")
    if manifest.get("vertex_count") != count:
        raise RuntimeError("existing manifest vertex-count mismatch")
    artifact = manifest.get("artifact", {})
    if artifact.get("bytes") != count - 1 or step_path.stat().st_size != count - 1:
        raise RuntimeError("existing step artifact size mismatch")
    observed = file_hash(step_path)
    if artifact.get("sha256") != observed:
        raise RuntimeError("existing step artifact hash mismatch")
    return manifest


def build(count: int, output_dir: Path, force: bool) -> dict[str, Any]:
    if count < 3:
        raise ValueError("--count must be at least 3")
    step_path, manifest_path, log_path = artifact_paths(output_dir, count)
    log = Log(log_path)
    code_sha256 = file_hash(Path(__file__).resolve())
    parameters = {
        "schema": SCHEMA,
        "vertex_count": count,
        "hilbert_variant": "standard-infinite-quadrant-four-state",
        "index_origin": 0,
        "lift": ["hilbert_x", "hilbert_y", "index"],
        "retained_colour": [0, 0],
        "colour_rule": ["parity(count digits 1 or 2)", "parity(count digit 3)"],
        "generator_code_sha256": code_sha256,
    }
    identity_sha256 = stable_hash(parameters)
    log.emit(
        "build_start",
        parameters=parameters,
        identity_sha256=identity_sha256,
        output=str(step_path),
        resource_policy={"processes": 1, "thread_cap": 1},
        resume="existing compatible final artifact is validated and reused",
    )

    if step_path.exists() or manifest_path.exists():
        if not (step_path.exists() and manifest_path.exists()):
            if not force:
                raise RuntimeError("partial existing artifact; pass --force to replace it")
        elif not force:
            manifest = validate_existing(step_path, manifest_path, count)
            log.emit(
                "build_reused",
                vertices=count,
                steps=count - 1,
                artifact_sha256=manifest["artifact"]["sha256"],
                manifest=str(manifest_path),
            )
            return manifest
    if force:
        step_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)

    started = time.monotonic()
    vertex_hasher = hashlib.sha256()
    index_hasher = hashlib.sha256()
    pack_vertex = struct.Struct("<qqq").pack
    pack_index = struct.Struct("<Q").pack
    word = bytearray()
    menu: list[tuple[int, int, int]] = []
    menu_index: dict[tuple[int, int, int], int] = {}
    bounds_min = [0, 0, 0]
    bounds_max = [0, 0, 0]
    max_gap = 0
    scan_index = 0
    retained = 0
    previous: tuple[int, int, int] | None = None

    while retained < count:
        if _STOP_REQUESTED:
            log.emit(
                "build_interrupted",
                completed=retained,
                total=count,
                elapsed_s=round(time.monotonic() - started, 3),
                restart="deterministic rebuild from zero; expected runtime is seconds",
            )
            raise InterruptedError("stop requested")
        if colour(scan_index) == (0, 0):
            x, y = hilbert_xy(scan_index)
            vertex = (x, y, scan_index)
            vertex_hasher.update(pack_vertex(*vertex))
            index_hasher.update(pack_index(scan_index))
            for coordinate in range(3):
                bounds_min[coordinate] = min(bounds_min[coordinate], vertex[coordinate])
                bounds_max[coordinate] = max(bounds_max[coordinate], vertex[coordinate])
            if previous is not None:
                step = tuple(vertex[i] - previous[i] for i in range(3))
                if not (1 <= step[2] <= 31):
                    raise AssertionError(f"gap bound failed at retained vertex {retained}: {step}")
                if abs(step[0]) + abs(step[1]) > step[2]:
                    raise AssertionError(f"unit-walk displacement bound failed: {step}")
                code = menu_index.get(step)
                if code is None:
                    code = len(menu)
                    if code >= 256:
                        raise AssertionError("byte menu overflow")
                    menu_index[step] = code
                    menu.append(step)
                word.append(code)
                max_gap = max(max_gap, step[2])
            previous = vertex
            retained += 1
            if retained % 100_000 == 0 or retained == count:
                elapsed = time.monotonic() - started
                rate = retained / elapsed if elapsed else 0.0
                eta = (count - retained) / rate if rate else None
                log.emit(
                    "build_progress",
                    completed=retained,
                    total=count,
                    indices_scanned=scan_index + 1,
                    menu_size=len(menu),
                    elapsed_s=round(elapsed, 3),
                    throughput_vertices_s=round(rate, 1),
                    eta_s=None if eta is None else round(eta, 3),
                )
        scan_index += 1

    atomic_bytes(step_path, bytes(word))
    artifact_sha256 = file_hash(step_path)
    elapsed = time.monotonic() - started
    manifest = {
        "schema": SCHEMA,
        "status": "constructed-exhaustive-verification-pending",
        "created_at": now(),
        "identity_sha256": identity_sha256,
        "parameters": parameters,
        "vertex_count": count,
        "step_count": count - 1,
        "indices_scanned": scan_index,
        "first_vertex": [0, 0, 0],
        "last_vertex": list(previous or (0, 0, 0)),
        "coordinate_bounds": {"minimum": bounds_min, "maximum": bounds_max},
        "menu": [list(step) for step in menu],
        "menu_size": len(menu),
        "maximum_observed_index_gap": max_gap,
        "proven_conservative_index_gap": 31,
        "artifact": {
            "path": step_path.name,
            "encoding": "one unsigned byte per step; value indexes manifest.menu",
            "bytes": len(word),
            "sha256": artifact_sha256,
        },
        "hashes": {
            "vertices_int64_le_sha256": vertex_hasher.hexdigest(),
            "retained_indices_uint64_le_sha256": index_hasher.hexdigest(),
        },
        "construction_elapsed_s": round(elapsed, 6),
        "claim_scope": {
            "constructed": True,
            "structurally_verified": False,
            "exhaustively_triple_free_verified": False,
            "infinite_claim": "candidate Hilbert valuation lemma; not certified by this artifact",
        },
    }
    atomic_json(manifest_path, manifest)
    log.emit(
        "build_complete",
        vertices=count,
        steps=count - 1,
        indices_scanned=scan_index,
        menu_size=len(menu),
        maximum_gap=max_gap,
        elapsed_s=round(elapsed, 3),
        artifact=str(step_path),
        artifact_sha256=artifact_sha256,
        manifest=str(manifest_path),
        checkpoint="not required: deterministic full rebuild completed in seconds",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="retained vertex count (default: %(default)s)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "viz",
        help="artifact directory (default: %(default)s)",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing or partial artifact")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    try:
        manifest = build(args.count, args.output_dir, args.force)
    except InterruptedError:
        return 130
    print(stable_json({
        "status": manifest["status"],
        "vertices": manifest["vertex_count"],
        "menu_size": manifest["menu_size"],
        "artifact_sha256": manifest["artifact"]["sha256"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
