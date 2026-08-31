#!/usr/bin/env python3
"""Build the browser payload for the all-index Hilbert lift.

The builder evaluates the exact construction from ``hilbert_walk_demo.py`` and
packs two 4-bit realized-step identifiers per byte. Work is checkpointed every
``--checkpoint-every`` vertices. A compatible checkpoint resumes automatically;
``--fresh`` discards it. Result and checkpoint writes are atomic.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

from hilbert_walk_demo import H, state_corner, λ

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "viz" / "walk3d-data.json"
DEFAULT_CHECKPOINT = ROOT / "logs" / "walk3d-build.ckpt.json"
DEFAULT_LOG = ROOT / "logs" / "walk3d-build.log"
FORMAT_VERSION = 2
CONSTRUCTION = "hilbert-lift-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vertices", type=int, default=500_001)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--checkpoint-every", type=int, default=25_000)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="discard a compatible or incompatible checkpoint and rebuild",
    )
    return parser.parse_args()


def lifted_point(n: int) -> tuple[int, int, int]:
    """Evaluate P_n while decoding the Hilbert word only once."""
    (x, y), state = H(n)
    corner_x, corner_y = state_corner(state)
    label = λ(state)
    return 2 * x + corner_x, 2 * y + corner_y, 4 * n + label


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, separators=(",", ":")) + "\n")
    os.replace(temporary, path)


def build_identity(vertices: int) -> str:
    digest = hashlib.sha256()
    digest.update(f"{FORMAT_VERSION}:{CONSTRUCTION}:{vertices}".encode())
    for path in (Path(__file__), Path(__file__).with_name("hilbert_walk_demo.py")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def logger(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    def emit(event: str, **fields: object) -> None:
        record = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            **fields,
        }
        line = json.dumps(record, separators=(",", ":"))
        with path.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
            stream.flush()
        print(line, flush=True)

    return emit


def checkpoint_payload(
    identity: str,
    vertices: int,
    next_n: int,
    start: tuple[int, int, int],
    previous: tuple[int, int, int],
    menu: list[tuple[int, int, int]],
    counts: list[int],
    packed: bytearray,
) -> dict[str, object]:
    return {
        "version": FORMAT_VERSION,
        "construction": CONSTRUCTION,
        "identity": identity,
        "vertices": vertices,
        "next_n": next_n,
        "start": start,
        "previous": previous,
        "menu": menu,
        "counts": counts,
        "packed": base64.b64encode(packed).decode("ascii"),
    }


def main() -> int:
    args = parse_args()
    if args.vertices < 2:
        raise ValueError("--vertices must be at least 2")
    if args.checkpoint_every < 1:
        raise ValueError("--checkpoint-every must be positive")

    emit = logger(args.log)
    identity = build_identity(args.vertices)
    stop_requested = False

    def request_stop(signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True
        emit("signal", signal=signum)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    if args.fresh and args.checkpoint.exists():
        args.checkpoint.unlink()

    start_time = time.monotonic()
    if args.checkpoint.exists():
        saved = json.loads(args.checkpoint.read_text())
        if (
            saved.get("identity") != identity
            or saved.get("version") != FORMAT_VERSION
            or saved.get("construction") != CONSTRUCTION
            or saved.get("vertices") != args.vertices
        ):
            raise ValueError(
                f"incompatible checkpoint {args.checkpoint}; pass --fresh to discard it"
            )
        next_n = int(saved["next_n"])
        start = tuple(saved["start"])
        previous = tuple(saved["previous"])
        menu = [tuple(step) for step in saved["menu"]]
        counts = [int(count) for count in saved["counts"]]
        packed = bytearray(base64.b64decode(saved["packed"]))
        emit(
            "resume",
            identity=identity,
            completed=next_n,
            total=args.vertices,
            checkpoint=str(args.checkpoint),
            workers=1,
        )
    else:
        next_n = 1
        start = lifted_point(0)
        previous = start
        menu: list[tuple[int, int, int]] = []
        counts: list[int] = []
        packed = bytearray()
        emit(
            "start",
            identity=identity,
            completed=1,
            total=args.vertices,
            checkpoint=str(args.checkpoint),
            workers=1,
            thread_settings={
                key: os.environ.get(key, "unset")
                for key in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            },
        )

    menu_id = {step: index for index, step in enumerate(menu)}

    def save_checkpoint() -> None:
        atomic_json(
            args.checkpoint,
            checkpoint_payload(
                identity,
                args.vertices,
                next_n,
                start,
                previous,
                menu,
                counts,
                packed,
            ),
        )

    while next_n < args.vertices:
        point = lifted_point(next_n)
        step = tuple(point[axis] - previous[axis] for axis in range(3))
        if not (
            abs(step[0]) <= 3
            and abs(step[1]) <= 3
            and 1 <= step[2] <= 7
        ):
            raise ValueError(f"step {next_n - 1} violates the walk bounds: {step}")

        identifier = menu_id.get(step)
        if identifier is None:
            identifier = len(menu)
            if identifier >= 16:
                raise ValueError("construction realized more than 16 vectors")
            menu_id[step] = identifier
            menu.append(step)
            counts.append(0)
        counts[identifier] += 1

        step_index = next_n - 1
        if step_index % 2 == 0:
            packed.append(identifier << 4)
        else:
            packed[-1] |= identifier

        previous = point
        next_n += 1

        if next_n % args.checkpoint_every == 0 or stop_requested:
            save_checkpoint()
            elapsed = max(time.monotonic() - start_time, 1e-9)
            processed = next_n
            throughput = processed / elapsed
            remaining = (args.vertices - next_n) / throughput
            emit(
                "progress",
                identity=identity,
                completed=next_n,
                total=args.vertices,
                throughput_vertices_per_second=round(throughput, 2),
                elapsed_seconds=round(elapsed, 2),
                estimated_remaining_seconds=round(remaining, 2),
                checkpoint=str(args.checkpoint),
                menu_size=len(menu),
            )
            if stop_requested:
                emit("stopped", checkpoint=str(args.checkpoint))
                return 130

    if len(menu) != 16:
        raise ValueError(f"expected 16 realized vectors, found {len(menu)}")

    core = {
        "start": start,
        "end": previous,
        "menu": menu,
        "counts": counts,
        "packed": base64.b64encode(packed).decode("ascii"),
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload = {
        "version": FORMAT_VERSION,
        "construction": CONSTRUCTION,
        "encoding": "two 4-bit menu indices per byte; even step in high nibble",
        "source": "hilbert_walk_demo.py",
        "sha256": digest,
        "vertices": args.vertices,
        "steps": args.vertices - 1,
        **core,
    }
    atomic_json(args.output, payload)
    if args.checkpoint.exists():
        args.checkpoint.unlink()
    elapsed = time.monotonic() - start_time
    emit(
        "complete",
        identity=identity,
        completed=args.vertices,
        total=args.vertices,
        elapsed_seconds=round(elapsed, 2),
        menu_size=len(menu),
        output=str(args.output),
        output_bytes=args.output.stat().st_size,
        sha256=digest,
    )
    print(
        f"packed {payload['steps']:,} steps / {payload['vertices']:,} vertices; "
        f"menu={len(menu)}; payload={args.output.stat().st_size:,} bytes; "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
