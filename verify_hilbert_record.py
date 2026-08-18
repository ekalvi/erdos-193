#!/usr/bin/env python3
"""Independently verify a compact Hilbert-walk record.

Two verification layers are deliberately separated:

``structural``
    Linear exact audit of the byte witness, hashes, declared menu, retained
    colour, absence of skipped retained indices, and inverse Hilbert address.
    It also checks every local case in the four-state Gray-code valuation table.

``run``
    First performs the structural audit, then starts 1--4 exact direction-hash
    workers.  Worker ``k mod W`` checks every primitive direction from vertex k
    to all earlier vertices.  This is O(n^2), sound and complete for detecting
    collinear triples, and does not assume the proposed Hilbert lemma.

The exhaustive run is safely resumable.  Each worker atomically checkpoints its
next vertex, cumulative direction count, elapsed time, record identity, worker
layout, and verifier-code hash.  SIGINT/SIGTERM finishes the current checkpoint
boundary (or abandons and later recomputes the interrupted vertex).  JSONL logs
record parameters, throughput, elapsed time, ETA, checkpoints, and outcomes.

Examples:

    python3 -B verify_hilbert_record.py structural
    python3 -B verify_hilbert_record.py run --workers 4
    python3 -B verify_hilbert_record.py status --workers 4

A checkpoint identity mismatch is fatal rather than silently reusing work from
a different witness, code revision, or worker partition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import signal
import struct
import subprocess
import sys
import time
from array import array
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_COUNT = 400_000
DEFAULT_STEM = f"hilbert-193-{DEFAULT_COUNT}"
DEFAULT_MANIFEST = ROOT / "viz" / f"{DEFAULT_STEM}-manifest.json"
DEFAULT_CHECKPOINT_DIR = ROOT / f".checkpoint-{DEFAULT_STEM}-verify"
DEFAULT_LOG = ROOT / "logs" / f"{DEFAULT_STEM}-verify.jsonl"
DEFAULT_STRUCTURAL_RESULT = ROOT / f"{DEFAULT_STEM}-structural-verification.json"
DEFAULT_RESULT = ROOT / f"{DEFAULT_STEM}-verification.json"
DEFAULT_PUBLIC_STATUS = ROOT / "viz" / f"{DEFAULT_STEM}-status.json"
RECORD_SCHEMA = "hilbert-193-record-v1"
CHECKPOINT_SCHEMA = "hilbert-193-direction-checkpoint-v1"
RESULT_SCHEMA = "hilbert-193-verification-v1"
_STOP_REQUESTED = False
_CHILDREN: list[subprocess.Popen[Any]] = []

# Independent inverse table for the same standard Hilbert convention.
_NEXT_STATE = (
    4, 0, 0, 12,
    0, 4, 4, 8,
    12, 8, 8, 4,
    8, 12, 12, 0,
)
_YX_TO_DIGIT = (
    0, 1, 3, 2,
    0, 3, 1, 2,
    2, 3, 1, 0,
    2, 1, 3, 0,
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
_STATE_XOR_BY_DIGIT = (1, 0, 0, 3)


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


def atomic_json(path: Path, value: Any) -> None:
    atomic_bytes(path, (stable_json(value) + "\n").encode())


class Log:
    """Single-write O_APPEND JSONL logger, safe across worker processes."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **fields: Any) -> None:
        record = {"at": now(), "event": event, **fields}
        payload = (stable_json(record) + "\n").encode()
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(descriptor, payload)
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


def install_signal_handlers() -> None:
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)


def v2(number: int) -> int:
    number = abs(number)
    if number == 0:
        raise ValueError("v2(0) is not used in the local digit audit")
    return (number & -number).bit_length() - 1


def digits4_low(number: int) -> list[int]:
    if number == 0:
        return [0]
    digits: list[int] = []
    while number:
        digits.append(number & 3)
        number >>= 2
    return digits


def colour(number: int) -> tuple[int, int]:
    first = 0
    second = 0
    for digit in digits4_low(number):
        if digit in (1, 2):
            first ^= 1
        elif digit == 3:
            second ^= 1
    return first, second


def xy_to_hilbert_index(x: int, y: int) -> int:
    """Inverse state-table implementation, independent of the constructor."""
    if x < 0 or y < 0:
        raise ValueError("standard quadrant Hilbert coordinates must be nonnegative")
    top_bit = max(x.bit_length(), y.bit_length()) - 1
    if top_bit < 0:
        top_bit = 0
    state = 4 if top_bit & 1 else 0
    number = 0
    for bit in range(top_bit, -1, -1):
        x_bit = (x >> bit) & 1
        y_bit = (y >> bit) & 1
        digit = _YX_TO_DIGIT[state + 2 * y_bit + x_bit]
        number = 4 * number + digit
        state = _NEXT_STATE[state + digit]
    return number


def audit_local_hilbert_table() -> dict[str, int]:
    transition_cases = 0
    pair_cases = 0
    for state in range(4):
        for digit in range(4):
            table_index = 4 * state + digit
            outgoing = _NEXT_STATE[table_index] // 4
            expected = state ^ _STATE_XOR_BY_DIGIT[digit]
            if outgoing != expected:
                raise AssertionError(("state transition mismatch", state, digit, outgoing, expected))
            outgoing_index = 4 * outgoing + digit
            if (_DIGIT_X[table_index], _DIGIT_Y[table_index]) != (
                _DIGIT_X[outgoing_index], _DIGIT_Y[outgoing_index]
            ):
                raise AssertionError(("reverse output mismatch", state, digit))
            transition_cases += 1
        row = [(_DIGIT_X[4 * state + digit], _DIGIT_Y[4 * state + digit]) for digit in range(4)]
        for left in range(4):
            for right in range(left + 1, 4):
                hamming = int(row[left][0] != row[right][0]) + int(row[left][1] != row[right][1])
                if hamming != 1 + v2(right - left):
                    raise AssertionError(("Gray distance mismatch", state, left, right, hamming))
                pair_cases += 1
    return {"transition_cases": transition_cases, "digit_pair_cases": pair_cases}


def load_manifest(path: Path) -> tuple[dict[str, Any], Path, bytes]:
    manifest = json.loads(path.read_text())
    if manifest.get("schema") != RECORD_SCHEMA:
        raise RuntimeError("record manifest schema mismatch")
    artifact = manifest.get("artifact", {})
    step_path = path.parent / artifact.get("path", "")
    if not step_path.is_file():
        raise RuntimeError(f"step artifact missing: {step_path}")
    steps = step_path.read_bytes()
    if len(steps) != manifest.get("step_count") or len(steps) != artifact.get("bytes"):
        raise RuntimeError("step artifact size mismatch")
    observed_hash = hashlib.sha256(steps).hexdigest()
    if observed_hash != artifact.get("sha256"):
        raise RuntimeError("step artifact SHA-256 mismatch")
    return manifest, step_path, steps


def reconstruct_arrays(manifest: dict[str, Any], steps: bytes) -> tuple[array[int], array[int], array[int]]:
    menu = [tuple(int(value) for value in step) for step in manifest["menu"]]
    if len(menu) > 256:
        raise RuntimeError("manifest menu does not fit byte encoding")
    first = tuple(int(value) for value in manifest["first_vertex"])
    xs = array("q", [first[0]])
    ys = array("q", [first[1]])
    zs = array("q", [first[2]])
    x, y, z = first
    for rank, code in enumerate(steps, 1):
        if code >= len(menu):
            raise RuntimeError(f"step {rank} uses menu code {code} outside menu")
        dx, dy, dz = menu[code]
        x += dx
        y += dy
        z += dz
        xs.append(x)
        ys.append(y)
        zs.append(z)
    if len(xs) != manifest["vertex_count"]:
        raise RuntimeError("reconstructed vertex count mismatch")
    return xs, ys, zs


def structural_audit(
    manifest_path: Path,
    result_path: Path,
    log: Log,
) -> dict[str, Any]:
    started = time.monotonic()
    manifest, step_path, steps = load_manifest(manifest_path)
    table = audit_local_hilbert_table()
    xs, ys, zs = reconstruct_arrays(manifest, steps)
    pack_vertex = struct.Struct("<qqq").pack
    pack_index = struct.Struct("<Q").pack
    vertex_hasher = hashlib.sha256()
    index_hasher = hashlib.sha256()
    seen: set[tuple[int, int, int]] = set()
    previous_index = -1
    bounds_min = [xs[0], ys[0], zs[0]]
    bounds_max = [xs[0], ys[0], zs[0]]
    maximum_gap = 0
    log.emit(
        "structural_start",
        manifest=str(manifest_path),
        artifact=str(step_path),
        vertices=len(xs),
        artifact_sha256=manifest["artifact"]["sha256"],
        resource_policy={"processes": 1, "thread_cap": 1},
    )
    for rank, (x, y, index) in enumerate(zip(xs, ys, zs)):
        point = (x, y, index)
        if point in seen:
            raise AssertionError(f"repeated vertex at rank {rank}: {point}")
        seen.add(point)
        if colour(index) != (0, 0):
            raise AssertionError(f"retained-colour mismatch at rank {rank}, index {index}")
        for skipped in range(previous_index + 1, index):
            if colour(skipped) == (0, 0):
                raise AssertionError(f"retained index {skipped} skipped before rank {rank}")
        if xy_to_hilbert_index(x, y) != index:
            raise AssertionError(f"inverse Hilbert mismatch at rank {rank}: {(x, y, index)}")
        if previous_index >= 0:
            maximum_gap = max(maximum_gap, index - previous_index)
        previous_index = index
        vertex_hasher.update(pack_vertex(x, y, index))
        index_hasher.update(pack_index(index))
        for coordinate, value in enumerate(point):
            bounds_min[coordinate] = min(bounds_min[coordinate], value)
            bounds_max[coordinate] = max(bounds_max[coordinate], value)
        if (rank + 1) % 100_000 == 0 or rank + 1 == len(xs):
            elapsed = time.monotonic() - started
            rate = (rank + 1) / elapsed if elapsed else 0.0
            eta = (len(xs) - rank - 1) / rate if rate else None
            log.emit(
                "structural_progress",
                completed=rank + 1,
                total=len(xs),
                elapsed_s=round(elapsed, 3),
                throughput_vertices_s=round(rate, 1),
                eta_s=None if eta is None else round(eta, 3),
            )
    expected_hashes = manifest["hashes"]
    if vertex_hasher.hexdigest() != expected_hashes["vertices_int64_le_sha256"]:
        raise AssertionError("vertex stream hash mismatch")
    if index_hasher.hexdigest() != expected_hashes["retained_indices_uint64_le_sha256"]:
        raise AssertionError("retained-index stream hash mismatch")
    if bounds_min != manifest["coordinate_bounds"]["minimum"] or bounds_max != manifest["coordinate_bounds"]["maximum"]:
        raise AssertionError("coordinate bounds mismatch")
    if list((xs[-1], ys[-1], zs[-1])) != manifest["last_vertex"]:
        raise AssertionError("last vertex mismatch")
    if maximum_gap != manifest["maximum_observed_index_gap"]:
        raise AssertionError("maximum observed gap mismatch")
    elapsed = time.monotonic() - started
    result = {
        "schema": RESULT_SCHEMA,
        "status": "structural-passed-exhaustive-pending",
        "verified_at": now(),
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": file_hash(manifest_path),
        "artifact": str(step_path.resolve()),
        "artifact_sha256": manifest["artifact"]["sha256"],
        "vertices": len(xs),
        "steps": len(steps),
        "menu_size": len(manifest["menu"]),
        "maximum_gap": maximum_gap,
        "coordinate_bounds": {"minimum": bounds_min, "maximum": bounds_max},
        "hashes": expected_hashes,
        "local_hilbert_table_audit": table,
        "checks": [
            "artifact size and SHA-256",
            "menu-code range and exact reconstruction",
            "no repeated vertex",
            "every retained index has colour even/even",
            "no retained even/even index skipped",
            "independent inverse Hilbert address at every vertex",
            "coordinate bounds, terminal vertex, and canonical stream hashes",
            "all four-state transition and Gray-code digit-pair cases",
        ],
        "elapsed_s": round(elapsed, 6),
        "exhaustive_direction_check": "pending",
    }
    atomic_json(result_path, result)
    log.emit(
        "structural_passed",
        vertices=len(xs),
        steps=len(steps),
        menu_size=len(manifest["menu"]),
        maximum_gap=maximum_gap,
        elapsed_s=round(elapsed, 3),
        result=str(result_path),
    )
    return result


def verification_identity(manifest_path: Path, manifest: dict[str, Any], workers: int) -> dict[str, Any]:
    config = {
        "schema": CHECKPOINT_SCHEMA,
        "record_artifact_sha256": manifest["artifact"]["sha256"],
        "record_manifest_sha256": file_hash(manifest_path),
        "vertex_count": manifest["vertex_count"],
        "workers": workers,
        "partition": "vertex rank k modulo workers",
        "direction": "primitive oriented (dx,dy,dz), dz positive to earlier vertex",
        "verifier_code_sha256": file_hash(Path(__file__).resolve()),
    }
    return {**config, "identity_sha256": stable_hash(config)}


def stripe_total_directions(first: int, workers: int, vertices: int) -> int:
    if first >= vertices:
        return 0
    terms = (vertices - 1 - first) // workers + 1
    return terms * (2 * first + (terms - 1) * workers) // 2


def checkpoint_path(directory: Path, worker: int) -> Path:
    return directory / f"worker-{worker}.json"


def initial_checkpoint(identity: dict[str, Any], worker: int, workers: int) -> dict[str, Any]:
    return {
        "schema": CHECKPOINT_SCHEMA,
        "identity_sha256": identity["identity_sha256"],
        "worker": worker,
        "workers": workers,
        "next_k": worker,
        "vertices_completed": 0,
        "directions_checked": 0,
        "elapsed_s": 0.0,
        "status": "running",
        "saved_at": now(),
    }


def load_checkpoint(path: Path, identity: dict[str, Any], worker: int, workers: int) -> dict[str, Any]:
    if not path.exists():
        return initial_checkpoint(identity, worker, workers)
    checkpoint = json.loads(path.read_text())
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise RuntimeError(f"checkpoint schema mismatch: {path}")
    if checkpoint.get("identity_sha256") != identity["identity_sha256"]:
        raise RuntimeError(f"checkpoint identity mismatch: {path}")
    if checkpoint.get("worker") != worker or checkpoint.get("workers") != workers:
        raise RuntimeError(f"checkpoint worker layout mismatch: {path}")
    if checkpoint.get("next_k", worker) % workers != worker:
        raise RuntimeError(f"checkpoint next_k partition mismatch: {path}")
    return checkpoint


def zigzag(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def packed_direction(
    vx: int,
    vy: int,
    vz: int,
    shift_y: int,
    shift_x: int,
) -> int:
    divisor = math.gcd(math.gcd(abs(vx), abs(vy)), vz)
    if divisor == 0:
        raise AssertionError("repeated vertex reached direction worker")
    if divisor > 1:
        vx //= divisor
        vy //= divisor
        vz //= divisor
    return (zigzag(vx) << shift_x) | (zigzag(vy) << shift_y) | vz


def run_worker(args: argparse.Namespace) -> int:
    install_signal_handlers()
    manifest_path = args.manifest.resolve()
    manifest, _step_path, steps = load_manifest(manifest_path)
    workers = args.workers
    worker = args.worker_index
    if not (0 <= worker < workers <= 4):
        raise ValueError("worker layout must satisfy 0 <= worker < workers <= 4")
    identity = verification_identity(manifest_path, manifest, workers)
    path = checkpoint_path(args.checkpoint_dir, worker)
    checkpoint = load_checkpoint(path, identity, worker, workers)
    log = Log(args.log)
    if checkpoint["status"] == "passed":
        log.emit("worker_reused_complete", worker=worker, checkpoint=str(path))
        return 0
    if checkpoint["status"] == "counterexample":
        log.emit("worker_reused_counterexample", worker=worker, checkpoint=str(path))
        return 2

    xs, ys, zs = reconstruct_arrays(manifest, steps)
    vertices = len(xs)
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    span_z = max(zs) - min(zs)
    bits_y = max(1, (2 * span_y).bit_length())
    bits_z = max(1, span_z.bit_length())
    shift_y = bits_z
    shift_x = bits_y + bits_z
    if shift_x + max(1, (2 * span_x).bit_length()) > 63:
        raise RuntimeError("packed primitive direction exceeds 63 bits")

    total_directions = stripe_total_directions(worker, workers, vertices)
    base_elapsed = float(checkpoint.get("elapsed_s", 0.0))
    run_started = time.monotonic()
    next_k = int(checkpoint["next_k"])
    completed_vertices = int(checkpoint.get("vertices_completed", 0))
    completed_directions = int(checkpoint.get("directions_checked", 0))
    log.emit(
        "worker_resume" if path.exists() else "worker_start",
        worker=worker,
        workers=workers,
        next_k=next_k,
        vertices=vertices,
        completed_directions=completed_directions,
        total_directions=total_directions,
        checkpoint=str(path),
        identity_sha256=identity["identity_sha256"],
        verifier_code_sha256=identity["verifier_code_sha256"],
        python=sys.version.split()[0],
        host=platform.node(),
        resource_policy={"processes": workers, "worker_threads": 1},
    )

    gcd = math.gcd
    checkpoint_stride = args.checkpoint_stride
    k = next_k
    while k < vertices:
        px, py, pz = xs[k], ys[k], zs[k]
        seen: set[int] = set()
        add = seen.add
        duplicate_key: int | None = None
        duplicate_i = -1
        interrupted = False
        for i in range(k):
            if (i & 0xFFFF) == 0 and _STOP_REQUESTED:
                interrupted = True
                break
            vx = px - xs[i]
            vy = py - ys[i]
            vz = pz - zs[i]
            divisor = gcd(gcd(abs(vx), abs(vy)), vz)
            if divisor == 0:
                raise AssertionError(f"repeated vertex at ranks {i}, {k}")
            if divisor > 1:
                vx //= divisor
                vy //= divisor
                vz //= divisor
            key = (zigzag(vx) << shift_x) | (zigzag(vy) << shift_y) | vz
            if key in seen:
                duplicate_key = key
                duplicate_i = i
                break
            add(key)
        if interrupted:
            elapsed = base_elapsed + time.monotonic() - run_started
            checkpoint.update({
                "next_k": k,
                "vertices_completed": completed_vertices,
                "directions_checked": completed_directions,
                "elapsed_s": elapsed,
                "status": "interrupted",
                "saved_at": now(),
            })
            atomic_json(path, checkpoint)
            log.emit(
                "worker_interrupted",
                worker=worker,
                next_k=k,
                completed_directions=completed_directions,
                total_directions=total_directions,
                elapsed_s=round(elapsed, 3),
                checkpoint=str(path),
            )
            return 130
        if duplicate_key is not None:
            first_i = -1
            for candidate in range(duplicate_i):
                key = packed_direction(
                    px - xs[candidate],
                    py - ys[candidate],
                    pz - zs[candidate],
                    shift_y,
                    shift_x,
                )
                if key == duplicate_key:
                    first_i = candidate
                    break
            elapsed = base_elapsed + time.monotonic() - run_started
            checkpoint.update({
                "next_k": k,
                "vertices_completed": completed_vertices,
                "directions_checked": completed_directions,
                "elapsed_s": elapsed,
                "status": "counterexample",
                "counterexample": {
                    "ranks": [first_i, duplicate_i, k],
                    "points": [
                        [xs[first_i], ys[first_i], zs[first_i]],
                        [xs[duplicate_i], ys[duplicate_i], zs[duplicate_i]],
                        [px, py, pz],
                    ],
                    "packed_primitive_direction": duplicate_key,
                },
                "saved_at": now(),
            })
            atomic_json(path, checkpoint)
            log.emit(
                "worker_counterexample",
                worker=worker,
                ranks=[first_i, duplicate_i, k],
                elapsed_s=round(elapsed, 3),
                checkpoint=str(path),
            )
            return 2

        completed_vertices += 1
        completed_directions += k
        k += workers
        if completed_vertices % checkpoint_stride == 0 or k >= vertices:
            elapsed = base_elapsed + time.monotonic() - run_started
            rate = completed_directions / elapsed if elapsed else 0.0
            eta = (total_directions - completed_directions) / rate if rate else None
            checkpoint.update({
                "next_k": k,
                "vertices_completed": completed_vertices,
                "directions_checked": completed_directions,
                "elapsed_s": elapsed,
                "status": "passed" if k >= vertices else "running",
                "saved_at": now(),
            })
            atomic_json(path, checkpoint)
            log.emit(
                "worker_passed" if k >= vertices else "worker_progress",
                worker=worker,
                next_k=k,
                completed_vertices=completed_vertices,
                total_vertices=(vertices - 1 - worker) // workers + 1,
                completed_directions=completed_directions,
                total_directions=total_directions,
                percent=round(100 * completed_directions / total_directions, 4) if total_directions else 100.0,
                throughput_directions_s=round(rate, 1),
                elapsed_s=round(elapsed, 3),
                eta_s=None if eta is None else round(eta, 3),
                checkpoint=str(path),
            )
    return 0


def write_public_status(
    path: Path,
    manifest: dict[str, Any],
    identity: dict[str, Any],
    status: str,
    **fields: Any,
) -> None:
    atomic_json(path, {
        "schema": "hilbert-193-public-status-v1",
        "status": status,
        "updated_at": now(),
        "vertices": manifest["vertex_count"],
        "steps": manifest["step_count"],
        "menu_size": manifest["menu_size"],
        "artifact_sha256": manifest["artifact"]["sha256"],
        "identity_sha256": identity["identity_sha256"],
        **fields,
    })


def run_controller(args: argparse.Namespace) -> int:
    global _CHILDREN
    install_signal_handlers()
    if not (1 <= args.workers <= 4):
        raise ValueError("--workers must be between 1 and 4")
    manifest_path = args.manifest.resolve()
    manifest, step_path, _steps = load_manifest(manifest_path)
    log = Log(args.log)
    structural = structural_audit(manifest_path, args.structural_result, log)
    identity = verification_identity(manifest_path, manifest, args.workers)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    direction_checks = manifest["vertex_count"] * (manifest["vertex_count"] - 1) // 2
    write_public_status(
        args.public_status,
        manifest,
        identity,
        "exhaustive-running",
        structural_status=structural["status"],
        workers=args.workers,
        direction_checks=direction_checks,
        checkpoint_dir=str(args.checkpoint_dir),
        log=str(args.log),
    )
    log.emit(
        "exhaustive_start",
        manifest=str(manifest_path),
        artifact=str(step_path),
        vertices=manifest["vertex_count"],
        direction_checks=direction_checks,
        workers=args.workers,
        checkpoint_dir=str(args.checkpoint_dir),
        log=str(args.log),
        identity_sha256=identity["identity_sha256"],
        code_sha256=identity["verifier_code_sha256"],
        resource_policy={
            "active_workers": args.workers,
            "maximum_aggregate_cpu_cores": 4,
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", "1"),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS", "1"),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS", "1"),
            "NUMEXPR_NUM_THREADS": os.environ.get("NUMEXPR_NUM_THREADS", "1"),
        },
        resume="validated per-worker atomic checkpoints",
    )
    common = [
        sys.executable,
        "-B",
        str(Path(__file__).resolve()),
        "worker",
        "--manifest",
        str(manifest_path),
        "--workers",
        str(args.workers),
        "--checkpoint-dir",
        str(args.checkpoint_dir),
        "--checkpoint-stride",
        str(args.checkpoint_stride),
        "--log",
        str(args.log),
    ]
    environment = os.environ.copy()
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[variable] = "1"
    _CHILDREN = [
        subprocess.Popen(common + ["--worker-index", str(worker)], env=environment)
        for worker in range(args.workers)
    ]
    while any(process.poll() is None for process in _CHILDREN):
        if _STOP_REQUESTED:
            log.emit("controller_stop_requested", active=sum(process.poll() is None for process in _CHILDREN))
            for process in _CHILDREN:
                if process.poll() is None:
                    process.terminate()
            break
        time.sleep(1)
    codes = [process.wait() for process in _CHILDREN]
    _CHILDREN = []
    if _STOP_REQUESTED:
        log.emit("exhaustive_interrupted", worker_exit_codes=codes, checkpoint_dir=str(args.checkpoint_dir))
        write_public_status(
            args.public_status,
            manifest,
            identity,
            "exhaustive-interrupted",
            structural_status=structural["status"],
            workers=args.workers,
            direction_checks=direction_checks,
            checkpoint_dir=str(args.checkpoint_dir),
            log=str(args.log),
        )
        return 130
    if any(code != 0 for code in codes):
        log.emit("exhaustive_failed", worker_exit_codes=codes, checkpoint_dir=str(args.checkpoint_dir))
        write_public_status(
            args.public_status,
            manifest,
            identity,
            "exhaustive-failed",
            structural_status=structural["status"],
            workers=args.workers,
            direction_checks=direction_checks,
            worker_exit_codes=codes,
            checkpoint_dir=str(args.checkpoint_dir),
            log=str(args.log),
        )
        return 2

    checkpoints = [
        load_checkpoint(checkpoint_path(args.checkpoint_dir, worker), identity, worker, args.workers)
        for worker in range(args.workers)
    ]
    if any(checkpoint["status"] != "passed" for checkpoint in checkpoints):
        raise RuntimeError("workers exited successfully without passed checkpoints")
    total_directions = sum(int(checkpoint["directions_checked"]) for checkpoint in checkpoints)
    expected_directions = manifest["vertex_count"] * (manifest["vertex_count"] - 1) // 2
    if total_directions != expected_directions:
        raise AssertionError("direction-check total mismatch")
    result = {
        "schema": RESULT_SCHEMA,
        "status": "exhaustive-passed",
        "verified_at": now(),
        "manifest": str(manifest_path),
        "manifest_sha256": file_hash(manifest_path),
        "artifact": str(step_path),
        "artifact_sha256": manifest["artifact"]["sha256"],
        "vertices": manifest["vertex_count"],
        "steps": manifest["step_count"],
        "menu_size": manifest["menu_size"],
        "workers": args.workers,
        "direction_checks": total_directions,
        "worker_elapsed_s": [round(float(checkpoint["elapsed_s"]), 6) for checkpoint in checkpoints],
        "identity": identity,
        "structural_result": str(args.structural_result.resolve()),
        "structural_result_sha256": file_hash(args.structural_result),
        "claim": "no repeated vertex and no three vertices collinear; exact integer exhaustive audit",
    }
    atomic_json(args.result, result)
    log.emit(
        "exhaustive_passed",
        vertices=manifest["vertex_count"],
        direction_checks=total_directions,
        worker_elapsed_s=result["worker_elapsed_s"],
        result=str(args.result),
        result_sha256=file_hash(args.result),
    )
    write_public_status(
        args.public_status,
        manifest,
        identity,
        "exhaustive-passed",
        structural_status=structural["status"],
        workers=args.workers,
        direction_checks=total_directions,
        result=str(args.result),
        result_sha256=file_hash(args.result),
    )
    return 0


def show_status(args: argparse.Namespace) -> int:
    manifest, _step_path, _steps = load_manifest(args.manifest.resolve())
    identity = verification_identity(args.manifest.resolve(), manifest, args.workers)
    rows = []
    for worker in range(args.workers):
        path = checkpoint_path(args.checkpoint_dir, worker)
        checkpoint = load_checkpoint(path, identity, worker, args.workers)
        rows.append({
            "worker": worker,
            "status": checkpoint["status"],
            "next_k": checkpoint["next_k"],
            "directions_checked": checkpoint["directions_checked"],
            "elapsed_s": round(float(checkpoint["elapsed_s"]), 3),
            "checkpoint": str(path),
        })
    print(json.dumps({"identity_sha256": identity["identity_sha256"], "workers": rows}, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("structural", "run", "worker", "status"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--worker-index", type=int, default=-1, help=argparse.SUPPRESS)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    parser.add_argument("--checkpoint-stride", type=int, default=100)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--structural-result", type=Path, default=DEFAULT_STRUCTURAL_RESULT)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--public-status", type=Path, default=DEFAULT_PUBLIC_STATUS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.checkpoint_stride < 1:
        raise ValueError("--checkpoint-stride must be positive")
    if args.command == "structural":
        install_signal_handlers()
        structural_audit(args.manifest.resolve(), args.structural_result, Log(args.log))
        return 0
    if args.command == "worker":
        return run_worker(args)
    if args.command == "run":
        return run_controller(args)
    return show_status(args)


if __name__ == "__main__":
    sys.exit(main())
