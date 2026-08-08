#!/usr/bin/env python3
"""Exact, resumable cube-versus-sphere menu comparison for Erdős #193.

The controlled comparison uses one common construction:

* cube124: every nonzero vector in [-2,2]^3;
* sphere120: every integer vector on x^2+y^2+z^2 = 74;
* the same expansion M, greedy Level-0 length, random seed, DFS limits,
  future-anchor semantics, and exact no-three-collinear verifier.

Run one independently resumable variant:

    python3 -B design/spherical_menu_comparison.py run --variant cube
    python3 -B design/spherical_menu_comparison.py run --variant sphere

By default, checkpoints, logs, and detailed run results are written below
/tmp/spherical-menu-comparison/.  A valid checkpoint is resumed automatically;
identity mismatches fail closed.  SIGINT/SIGTERM preserve the last completed
anchor gap, so at most one gap is recomputed.

After both runs complete, make the compact comparison artifact:

    python3 -B design/spherical_menu_comparison.py compare \
      --output design/spherical-menu-comparison-summary.json

The program is stdlib-only, single-process, and uses exact integer arithmetic
for construction, incidence, and verification.  Floating point is used only
for explicitly labelled angular and dimension diagnostics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from itertools import product
from math import gcd
from pathlib import Path
from random import Random
from typing import Any, Iterable, Sequence

SCHEMA = "spherical-menu-apples-to-apples-v1"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIR = Path("/tmp/spherical-menu-comparison")
DEFAULT_SUMMARY = ROOT / "design" / "spherical-menu-comparison-summary.json"

M = ((3, 0, 0), (0, 0, -3), (0, 3, -2))
Q = ((1, 0, 0), (0, 6, -2), (0, -2, 6))
SEED = 193
BASE_LENGTH = 4
TARGET_LEVELS = 3
BASE_TRIES = 500
SEGMENT_MAX_LENGTH = 12
SEGMENT_TRIES = 6
LEVEL_RESTARTS = 4
DFS_NODE_BUDGET = 30_000
COVERING_PROBES = 20_000

_STOP_REQUESTED = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class DurableLog:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **fields: Any) -> None:
        record = {"at": utc_now(), "event": event, **fields}
        line = stable_json(record)
        with self.path.open("a") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        printable = " ".join(f"{key}={value}" for key, value in fields.items())
        print(f"[{record['at']}] {event} {printable}".rstrip(), flush=True)


def request_stop(_signum: int, _frame: Any) -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True


def check_stop() -> None:
    if _STOP_REQUESTED:
        raise InterruptedError("stop requested")


def menu_vectors(variant: str) -> list[tuple[int, int, int]]:
    if variant == "cube":
        menu = [
            (x, y, z)
            for x, y, z in product(range(-2, 3), repeat=3)
            if (x, y, z) != (0, 0, 0)
        ]
        assert len(menu) == 124
        return menu
    if variant == "sphere":
        menu = [
            (x, y, z)
            for x, y, z in product(range(-8, 9), repeat=3)
            if x * x + y * y + z * z == 74
        ]
        assert len(menu) == 120
        assert all(gcd(gcd(abs(x), abs(y)), abs(z)) == 1 for x, y, z in menu)
        return menu
    raise ValueError(f"unknown variant: {variant}")


def apply_matrix(matrix: Sequence[Sequence[int]], vector: Sequence[int]) -> tuple[int, int, int]:
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def add(left: Sequence[int], right: Sequence[int]) -> tuple[int, int, int]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def sub(left: Sequence[int], right: Sequence[int]) -> tuple[int, int, int]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def cross(left: Sequence[int], right: Sequence[int]) -> tuple[int, int, int]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def dot(left: Sequence[int], right: Sequence[int]) -> int:
    return sum(left[i] * right[i] for i in range(3))


def primitive_oriented(vector: Sequence[int]) -> tuple[int, int, int]:
    divisor = gcd(gcd(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    if divisor == 0:
        return (0, 0, 0)
    return (vector[0] // divisor, vector[1] // divisor, vector[2] // divisor)


def primitive_unoriented(vector: Sequence[int]) -> tuple[int, int, int]:
    value = primitive_oriented(vector)
    for coordinate in value:
        if coordinate:
            return value if coordinate > 0 else (-value[0], -value[1], -value[2])
    return value


def qnorm2(vector: Sequence[int]) -> int:
    return sum(vector[i] * Q[i][j] * vector[j] for i in range(3) for j in range(3))


def legal_against(
    points: Sequence[tuple[int, int, int]],
    point_set: set[tuple[int, int, int]],
    candidate: tuple[int, int, int],
) -> bool:
    if candidate in point_set:
        return False
    seen: set[tuple[int, int, int]] = set()
    for old in points:
        direction = primitive_unoriented(sub(old, candidate))
        if direction in seen:
            return False
        seen.add(direction)
    return True


def verify_points(points: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    seen_points: set[tuple[int, int, int]] = set()
    checked_directions = 0
    for terminal, point in enumerate(points):
        if point in seen_points:
            raise AssertionError(f"repeated point at index {terminal}: {point}")
        directions: set[tuple[int, int, int]] = set()
        for old in points[:terminal]:
            direction = primitive_unoriented(sub(old, point))
            checked_directions += 1
            if direction in directions:
                raise AssertionError(f"collinear triple ending at index {terminal}")
            directions.add(direction)
        seen_points.add(point)
    return {
        "verified": True,
        "points": len(points),
        "unordered_pairs_checked": checked_directions,
    }


def walk_points(word: Sequence[int], menu: Sequence[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    points = [(0, 0, 0)]
    for index in word:
        points.append(add(points[-1], menu[index]))
    return points


def find_base(menu: Sequence[tuple[int, int, int]], rng: Random) -> list[int]:
    best: list[int] = []
    for _ in range(BASE_TRIES):
        points = [(0, 0, 0)]
        point_set = {(0, 0, 0)}
        word: list[int] = []
        for _position in range(BASE_LENGTH):
            indices = list(range(len(menu)))
            rng.shuffle(indices)
            for index in indices:
                candidate = add(points[-1], menu[index])
                if legal_against(points, point_set, candidate):
                    points.append(candidate)
                    point_set.add(candidate)
                    word.append(index)
                    break
            else:
                break
        if len(word) > len(best):
            best = word
        if len(best) == BASE_LENGTH:
            return best
    return best


def listify(value: Any) -> Any:
    if isinstance(value, tuple):
        return [listify(item) for item in value]
    if isinstance(value, list):
        return [listify(item) for item in value]
    return value


def tupleify(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(tupleify(item) for item in value)
    return value


def code_identity(variant: str, menu: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    config = {
        "schema": SCHEMA,
        "variant": variant,
        "menu_sha256": stable_hash(menu),
        "matrix": M,
        "quadratic_form": Q,
        "seed": SEED,
        "base_length": BASE_LENGTH,
        "target_levels": TARGET_LEVELS,
        "base_tries": BASE_TRIES,
        "segment_max_length": SEGMENT_MAX_LENGTH,
        "segment_tries": SEGMENT_TRIES,
        "level_restarts": LEVEL_RESTARTS,
        "dfs_node_budget": DFS_NODE_BUDGET,
        "covering_probes": COVERING_PROBES,
        "code_sha256": file_sha256(Path(__file__).resolve()),
    }
    return {**config, "identity_sha256": stable_hash(config)}


def new_level_state(
    level: int,
    parent_word: Sequence[int],
    parent_points: Sequence[tuple[int, int, int]],
    rng: Random,
) -> dict[str, Any]:
    return {
        "level": level,
        "parent_word": list(parent_word),
        "parent_points": [list(point) for point in parent_points],
        "restart": 0,
        "next_segment": 0,
        "points": [list(apply_matrix(M, parent_points[0]))],
        "new_word": [],
        "segment_records": [],
        "total_dfs_nodes": 0,
        "started_monotonic": time.monotonic(),
        "elapsed_before_resume_s": 0.0,
        "rng_state": listify(rng.getstate()),
    }


def checkpoint_payload(identity: dict[str, Any], completed: Sequence[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    serializable = dict(state)
    serializable.pop("started_monotonic", None)
    serializable["saved_at"] = utc_now()
    return {
        "schema": SCHEMA,
        "identity": identity,
        "completed_levels": list(completed),
        "state": serializable,
    }


def save_checkpoint(
    path: Path,
    identity: dict[str, Any],
    completed: Sequence[dict[str, Any]],
    state: dict[str, Any],
    rng: Random,
) -> None:
    state["rng_state"] = listify(rng.getstate())
    atomic_json(path, checkpoint_payload(identity, completed, state))


def level_elapsed(state: dict[str, Any]) -> float:
    return float(state.get("elapsed_before_resume_s", 0.0)) + time.monotonic() - float(state["started_monotonic"])


def amplify_resumable(
    menu: Sequence[tuple[int, int, int]],
    rng: Random,
    identity: dict[str, Any],
    completed: list[dict[str, Any]],
    state: dict[str, Any],
    checkpoint_path: Path,
    log: DurableLog,
) -> tuple[list[int], list[tuple[int, int, int]], dict[str, Any]] | None:
    parent_word = [int(value) for value in state["parent_word"]]
    parent_points = [tuple(point) for point in state["parent_points"]]
    anchors = [apply_matrix(M, point) for point in parent_points]
    max_step = max(max(abs(coordinate) for coordinate in step) for step in menu)
    level = int(state["level"])

    while int(state["restart"]) < LEVEL_RESTARTS:
        points = [tuple(point) for point in state["points"]]
        point_set = set(points)
        new_word = [int(value) for value in state["new_word"]]
        next_segment = int(state["next_segment"])
        failed = False

        for segment_index in range(next_segment, len(parent_word)):
            check_stop()
            target = anchors[segment_index + 1]
            future = anchors[segment_index + 2 :]
            segment_points: list[tuple[int, int, int]] = []
            segment_word: list[int] = []
            success = False
            segment_nodes = 0
            successful_depth = None
            successful_try = None

            for attempt in range(SEGMENT_TRIES):
                order = list(range(len(menu)))
                nodes = [0]

                def dfs(depth: int) -> bool:
                    nonlocal segment_nodes
                    nodes[0] += 1
                    segment_nodes += 1
                    if nodes[0] % 256 == 0:
                        check_stop()
                    if nodes[0] > DFS_NODE_BUDGET:
                        return False
                    last = points[-1] if not segment_points else segment_points[-1]
                    gap = max(abs(target[axis] - last[axis]) for axis in range(3))
                    if gap == 0:
                        return True
                    if depth == 0 or gap > depth * max_step:
                        return False
                    rng.shuffle(order)
                    for step_index in list(order):
                        candidate = add(last, menu[step_index])
                        if candidate == target or legal_against(
                            points + segment_points + [target] + future,
                            point_set | set(segment_points) | {target} | set(future),
                            candidate,
                        ):
                            segment_points.append(candidate)
                            segment_word.append(step_index)
                            if dfs(depth - 1):
                                return True
                            segment_points.pop()
                            segment_word.pop()
                    return False

                initial_gap = max(abs(target[axis] - points[-1][axis]) for axis in range(3))
                minimum_depth = max(1, -(-initial_gap // max_step))
                for depth_limit in range(minimum_depth, SEGMENT_MAX_LENGTH + 1):
                    nodes[0] = 0
                    if dfs(depth_limit):
                        success = True
                        successful_depth = depth_limit
                        successful_try = attempt
                        break
                    segment_points.clear()
                    segment_word.clear()
                if success:
                    break

            state["total_dfs_nodes"] = int(state["total_dfs_nodes"]) + segment_nodes
            if not success:
                failed = True
                log.emit(
                    "level_restart",
                    variant=identity["variant"],
                    level=level,
                    restart=int(state["restart"]),
                    failed_segment=segment_index,
                    completed_segments=segment_index,
                    dfs_nodes=state["total_dfs_nodes"],
                )
                break

            points.extend(segment_points)
            point_set.update(segment_points)
            new_word.extend(segment_word)
            record = {
                "segment": segment_index,
                "parent_step": parent_word[segment_index],
                "word_length": len(segment_word),
                "dfs_nodes": segment_nodes,
                "attempt": successful_try,
                "depth_limit": successful_depth,
            }
            state["segment_records"].append(record)
            state["points"] = [list(point) for point in points]
            state["new_word"] = new_word
            state["next_segment"] = segment_index + 1
            save_checkpoint(checkpoint_path, identity, completed, state, rng)

            completed_count = segment_index + 1
            if completed_count == len(parent_word) or completed_count % max(10, len(parent_word) // 10) == 0:
                elapsed = level_elapsed(state)
                throughput = completed_count / elapsed if elapsed else 0.0
                remaining = (len(parent_word) - completed_count) / throughput if throughput else None
                log.emit(
                    "level_progress",
                    variant=identity["variant"],
                    level=level,
                    completed=completed_count,
                    total=len(parent_word),
                    points=len(points),
                    dfs_nodes=state["total_dfs_nodes"],
                    elapsed_s=round(elapsed, 3),
                    eta_s=None if remaining is None else round(remaining, 3),
                    checkpoint=str(checkpoint_path),
                )

        if not failed:
            verification = verify_points(points)
            if len(new_word) + 1 != len(points):
                raise AssertionError("word/point count mismatch")
            elapsed = level_elapsed(state)
            routing = {
                "elapsed_s": round(elapsed, 6),
                "total_dfs_nodes": int(state["total_dfs_nodes"]),
                "nodes_per_parent_gap": int(state["total_dfs_nodes"]) / len(parent_word),
                "maximum_segment_nodes": max(record["dfs_nodes"] for record in state["segment_records"]),
                "connector_length_histogram": dict(sorted(Counter(record["word_length"] for record in state["segment_records"]).items())),
                "maximum_connector_length": max(record["word_length"] for record in state["segment_records"]),
                "restarts_used": int(state["restart"]),
            }
            log.emit(
                "level_complete",
                variant=identity["variant"],
                level=level,
                steps=len(new_word),
                points=len(points),
                dfs_nodes=state["total_dfs_nodes"],
                elapsed_s=round(elapsed, 3),
            )
            return new_word, points, {"routing": routing, "verification": verification}

        state["restart"] = int(state["restart"]) + 1
        state["next_segment"] = 0
        state["points"] = [list(anchors[0])]
        state["new_word"] = []
        state["segment_records"] = []
        state["total_dfs_nodes"] = 0
        state["elapsed_before_resume_s"] = level_elapsed(state)
        state["started_monotonic"] = time.monotonic()
        save_checkpoint(checkpoint_path, identity, completed, state, rng)

    return None


def fraction_record(value: Fraction) -> dict[str, Any]:
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def menu_metrics(menu: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    euclidean_norms = Counter(dot(step, step) for step in menu)
    qnorms = Counter(qnorm2(step) for step in menu)
    oriented = sorted(set(primitive_oriented(step) for step in menu))
    unoriented = sorted(set(primitive_unoriented(step) for step in menu))

    moment = [[Fraction(0) for _ in range(3)] for _ in range(3)]
    for step in menu:
        norm = dot(step, step)
        for row in range(3):
            for column in range(3):
                moment[row][column] += Fraction(step[row] * step[column], norm * len(menu))

    unit = []
    for step in oriented:
        length = math.sqrt(dot(step, step))
        unit.append(tuple(coordinate / length for coordinate in step))
    nearest_angles = []
    for index, vector in enumerate(unit):
        best = max(
            sum(vector[axis] * other[axis] for axis in range(3))
            for other_index, other in enumerate(unit)
            if other_index != index
        )
        nearest_angles.append(math.degrees(math.acos(max(-1.0, min(1.0, best)))))

    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    covering_distances = []
    for index in range(COVERING_PROBES):
        z = 1.0 - 2.0 * (index + 0.5) / COVERING_PROBES
        radial = math.sqrt(max(0.0, 1.0 - z * z))
        probe = (radial * math.cos(index * golden_angle), radial * math.sin(index * golden_angle), z)
        best = max(sum(probe[axis] * vector[axis] for axis in range(3)) for vector in unit)
        covering_distances.append(math.degrees(math.acos(max(-1.0, min(1.0, best)))))

    mean_qnorm = Fraction(sum(qnorm2(step) for step in menu), len(menu))
    return {
        "menu_size": len(menu),
        "menu_sha256": stable_hash(menu),
        "unique_oriented_projective_directions": len(oriented),
        "unique_unoriented_projective_directions": len(unoriented),
        "radial_duplicate_moves": len(menu) - len(oriented),
        "euclidean_squared_norm_histogram": {str(key): value for key, value in sorted(euclidean_norms.items())},
        "Q_squared_norm_histogram": {str(key): value for key, value in sorted(qnorms.items())},
        "mean_Q_squared_norm": fraction_record(mean_qnorm),
        "normalized_direction_second_moment": [[fraction_record(value) for value in row] for row in moment],
        "minimum_nearest_direction_angle_degrees": min(nearest_angles),
        "median_nearest_direction_angle_degrees": statistics.median(nearest_angles),
        "sampled_spherical_covering_radius_degrees": max(covering_distances),
        "sampled_mean_nearest_probe_angle_degrees": statistics.fmean(covering_distances),
        "covering_probe_count": COVERING_PROBES,
    }


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("empty percentile")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(probability * len(ordered)) - 1))
    return ordered[index]


def point_metrics(
    points: Sequence[tuple[int, int, int]],
    menu: Sequence[tuple[int, int, int]],
    level: int,
    base_steps: int,
) -> dict[str, Any]:
    verify = verify_points(points)
    pair_directions: Counter[tuple[int, int, int]] = Counter()
    for right in range(len(points)):
        for left in range(right):
            pair_directions[primitive_unoriented(sub(points[right], points[left]))] += 1
    pair_count = len(points) * (len(points) - 1) // 2
    parallel_collisions = sum(count * (count - 1) // 2 for count in pair_directions.values())
    possible_pair_pairs = pair_count * (pair_count - 1) // 2

    mean_qnorm = Fraction(sum(qnorm2(step) for step in menu), len(menu))
    crowding: dict[str, Any] = {}
    for multiplier in (2, 4):
        threshold = multiplier * multiplier * mean_qnorm
        counts = []
        for point in points:
            count = 0
            for other in points:
                if other != point and Fraction(qnorm2(sub(other, point)), 1) <= threshold:
                    count += 1
            counts.append(count)
        crowding[str(multiplier)] = {
            "threshold_Q_squared_over_mean_step_Q_squared": multiplier * multiplier,
            "maximum_neighbors": max(counts, default=0),
            "mean_neighbors": statistics.fmean(counts) if counts else 0.0,
        }

    legal_counts = []
    prefix: list[tuple[int, int, int]] = []
    prefix_set: set[tuple[int, int, int]] = set()
    for point in points:
        prefix.append(point)
        prefix_set.add(point)
        legal_counts.append(sum(legal_against(prefix, prefix_set, add(point, step)) for step in menu))

    steps = len(points) - 1
    cumulative_growth = steps / base_steps
    effective_dimension = 0.0 if level == 0 else math.log(cumulative_growth) / (level * math.log(3.0))
    return {
        "level": level,
        "steps": steps,
        "points": len(points),
        "verification": verify,
        "cumulative_growth_from_level0": cumulative_growth,
        "cumulative_effective_dimension_log_growth_over_log3": effective_dimension,
        "normalized_Q_crowding": crowding,
        "secants": {
            "unordered_pairs": pair_count,
            "unique_unoriented_directions": len(pair_directions),
            "unique_direction_fraction": len(pair_directions) / pair_count if pair_count else 1.0,
            "maximum_parallel_multiplicity": max(pair_directions.values(), default=0),
            "parallel_secant_pair_collisions": parallel_collisions,
            "parallel_collision_probability": parallel_collisions / possible_pair_pairs if possible_pair_pairs else 0.0,
        },
        "immediate_legal_menu_moves": {
            "minimum": min(legal_counts),
            "p10": percentile([float(value) for value in legal_counts], 0.10),
            "median": statistics.median(legal_counts),
            "mean": statistics.fmean(legal_counts),
            "minimum_fraction": min(legal_counts) / len(menu),
        },
    }


def word_sha256(word: Sequence[int]) -> str:
    return hashlib.sha256(stable_json(list(word)).encode()).hexdigest()


def run_variant(args: argparse.Namespace) -> int:
    variant = args.variant
    menu = menu_vectors(variant)
    identity = code_identity(variant, menu)
    run_dir = Path(args.run_dir)
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else run_dir / f"{variant}-checkpoint.json"
    result_path = Path(args.result) if args.result else run_dir / f"{variant}-result.json"
    log_path = Path(args.log) if args.log else run_dir / f"{variant}.jsonl"
    log = DurableLog(log_path)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    completed: list[dict[str, Any]] = []
    rng = Random(SEED)
    state: dict[str, Any]

    if result_path.exists() and not args.force:
        result = json.loads(result_path.read_text())
        if result.get("identity", {}).get("identity_sha256") != identity["identity_sha256"]:
            raise RuntimeError(f"existing result identity mismatch: {result_path}")
        print(f"validated existing result: {result_path}")
        return 0

    if checkpoint_path.exists() and not args.force:
        payload = json.loads(checkpoint_path.read_text())
        if payload.get("schema") != SCHEMA:
            raise RuntimeError("checkpoint schema mismatch")
        pinned = payload.get("identity", {})
        if pinned.get("identity_sha256") != identity["identity_sha256"]:
            raise RuntimeError("checkpoint identity mismatch; remove it or use --force")
        completed = payload["completed_levels"]
        state = payload["state"]
        state["started_monotonic"] = time.monotonic()
        rng.setstate(tupleify(state["rng_state"]))
        log.emit(
            "resume",
            variant=variant,
            level=state["level"],
            next_segment=state["next_segment"],
            completed_levels=len(completed) - 1,
            checkpoint=str(checkpoint_path),
        )
    else:
        if args.force:
            checkpoint_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)
        base_word = find_base(menu, rng)
        if len(base_word) != BASE_LENGTH:
            raise RuntimeError(f"failed to create Level-0 seed: got {len(base_word)} steps")
        base_points = walk_points(base_word, menu)
        base_verification = verify_points(base_points)
        completed = [{
            "level": 0,
            "word": base_word,
            "word_sha256": word_sha256(base_word),
            "points": [list(point) for point in base_points],
            "routing": None,
            "verification": base_verification,
        }]
        state = new_level_state(1, base_word, base_points, rng)
        save_checkpoint(checkpoint_path, identity, completed, state, rng)
        log.emit(
            "start",
            variant=variant,
            menu_size=len(menu),
            base_steps=len(base_word),
            target_levels=TARGET_LEVELS,
            checkpoint=str(checkpoint_path),
            log=str(log_path),
            identity=identity["identity_sha256"],
            resource_threads=1,
        )

    try:
        while int(state["level"]) <= TARGET_LEVELS:
            outcome = amplify_resumable(menu, rng, identity, completed, state, checkpoint_path, log)
            if outcome is None:
                log.emit(
                    "terminal_jam",
                    variant=variant,
                    level=state["level"],
                    restarts=LEVEL_RESTARTS,
                )
                result = {
                    "schema": SCHEMA,
                    "status": "jam",
                    "identity": identity,
                    "menu": [list(step) for step in menu],
                    "completed_levels": completed,
                    "failed_level": state["level"],
                    "checkpoint": str(checkpoint_path),
                    "log": str(log_path),
                }
                atomic_json(result_path, result)
                return 2
            word, points, details = outcome
            completed.append({
                "level": int(state["level"]),
                "word": word,
                "word_sha256": word_sha256(word),
                "points": [list(point) for point in points],
                **details,
            })
            next_level = int(state["level"]) + 1
            if next_level > TARGET_LEVELS:
                break
            state = new_level_state(next_level, word, points, rng)
            save_checkpoint(checkpoint_path, identity, completed, state, rng)

    except InterruptedError:
        log.emit(
            "interrupted",
            variant=variant,
            level=state["level"],
            last_completed_segment=state["next_segment"],
            checkpoint=str(checkpoint_path),
        )
        return 130

    detailed_levels = []
    base_steps = len(completed[0]["word"])
    for record in completed:
        points = [tuple(point) for point in record["points"]]
        detailed_levels.append({
            "level": record["level"],
            "word": record["word"],
            "word_sha256": record["word_sha256"],
            "routing": record["routing"],
            "metrics": point_metrics(points, menu, record["level"], base_steps),
        })
    result = {
        "schema": SCHEMA,
        "status": "complete",
        "created_at": utc_now(),
        "identity": identity,
        "menu": [list(step) for step in menu],
        "menu_metrics": menu_metrics(menu),
        "levels": detailed_levels,
        "checkpoint": str(checkpoint_path),
        "log": str(log_path),
        "scope": "exact finite comparison through the configured target level; not an infinite construction or availability theorem",
    }
    atomic_json(result_path, result)
    checkpoint_path.unlink(missing_ok=True)
    log.emit("run_complete", variant=variant, result=str(result_path), levels=TARGET_LEVELS)
    return 0


def load_complete(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA or data.get("status") != "complete":
        raise RuntimeError(f"not a complete {SCHEMA} result: {path}")
    variant = data["identity"]["variant"]
    menu = [tuple(step) for step in data["menu"]]
    expected = code_identity(variant, menu)
    if data["identity"]["identity_sha256"] != expected["identity_sha256"]:
        raise RuntimeError(f"result identity/code mismatch: {path}")
    for level in data["levels"]:
        points = walk_points(level["word"], menu)
        verify_points(points)
        if word_sha256(level["word"]) != level["word_sha256"]:
            raise RuntimeError(f"word hash mismatch in {path}, level {level['level']}")
    return data


def selected_comparison(cube: dict[str, Any], sphere: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {"menu": {}, "levels": {}}
    for name, data in (("cube", cube), ("sphere", sphere)):
        menu = data["menu_metrics"]
        output["menu"][name] = {
            "size": menu["menu_size"],
            "oriented_directions": menu["unique_oriented_projective_directions"],
            "radial_duplicate_moves": menu["radial_duplicate_moves"],
            "euclidean_squared_norm_histogram": menu["euclidean_squared_norm_histogram"],
            "minimum_direction_separation_degrees": menu["minimum_nearest_direction_angle_degrees"],
            "sampled_covering_radius_degrees": menu["sampled_spherical_covering_radius_degrees"],
        }
    for index in range(TARGET_LEVELS + 1):
        output["levels"][str(index)] = {}
        for name, data in (("cube", cube), ("sphere", sphere)):
            level = data["levels"][index]
            metrics = level["metrics"]
            output["levels"][str(index)][name] = {
                "steps": metrics["steps"],
                "effective_dimension": metrics["cumulative_effective_dimension_log_growth_over_log3"],
                "Q_crowding_radius4_max": metrics["normalized_Q_crowding"]["4"]["maximum_neighbors"],
                "parallel_collision_probability": metrics["secants"]["parallel_collision_probability"],
                "maximum_parallel_secant_multiplicity": metrics["secants"]["maximum_parallel_multiplicity"],
                "immediate_legal_move_minimum_fraction": metrics["immediate_legal_menu_moves"]["minimum_fraction"],
                "routing": level["routing"],
            }
    return output


def compare_runs(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    cube_path = Path(args.cube_result) if args.cube_result else run_dir / "cube-result.json"
    sphere_path = Path(args.sphere_result) if args.sphere_result else run_dir / "sphere-result.json"
    cube = load_complete(cube_path)
    sphere = load_complete(sphere_path)
    selected = selected_comparison(cube, sphere)

    cube_l3 = selected["levels"][str(TARGET_LEVELS)]["cube"]
    sphere_l3 = selected["levels"][str(TARGET_LEVELS)]["sphere"]
    cube_nodes = sum(
        level["routing"]["total_dfs_nodes"] for level in cube["levels"][1:]
    )
    sphere_nodes = sum(
        level["routing"]["total_dfs_nodes"] for level in sphere["levels"][1:]
    )
    verdict = {
        "primary_routing_work": {
            "lower_is_better": True,
            "cube_total_dfs_nodes_L1_through_L3": cube_nodes,
            "sphere_total_dfs_nodes_L1_through_L3": sphere_nodes,
            "sphere_over_cube": sphere_nodes / cube_nodes,
            "winner": "cube" if cube_nodes < sphere_nodes else "sphere",
        },
        "cumulative_growth_dimension_L3": {
            "lower_is_better_for_dilution": True,
            "cube": cube_l3["effective_dimension"],
            "sphere": sphere_l3["effective_dimension"],
            "winner": "cube" if cube_l3["effective_dimension"] < sphere_l3["effective_dimension"] else "sphere",
        },
        "normalized_Q_crowding_L3_radius4": {
            "lower_is_better": True,
            "cube": cube_l3["Q_crowding_radius4_max"],
            "sphere": sphere_l3["Q_crowding_radius4_max"],
            "winner": "cube" if cube_l3["Q_crowding_radius4_max"] < sphere_l3["Q_crowding_radius4_max"] else "sphere" if sphere_l3["Q_crowding_radius4_max"] < cube_l3["Q_crowding_radius4_max"] else "tie",
        },
        "parallel_secant_collision_probability_L3": {
            "lower_is_better": True,
            "cube": cube_l3["parallel_collision_probability"],
            "sphere": sphere_l3["parallel_collision_probability"],
            "winner": "cube" if cube_l3["parallel_collision_probability"] < sphere_l3["parallel_collision_probability"] else "sphere",
        },
        "interpretation": (
            "No scalar score is formed. Routing work and growth dimension are preregistered primary diagnostics; "
            "crowding, secant concentration, immediate availability, and angular coverage are separate diagnostics."
        ),
    }
    output = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "source_results": {
            "cube": {"path": str(cube_path), "sha256": file_sha256(cube_path)},
            "sphere": {"path": str(sphere_path), "sha256": file_sha256(sphere_path)},
        },
        "controlled_design": {
            "common_matrix": M,
            "common_quadratic_form": Q,
            "matrix_Q_conformality": "M^T Q M = 9 Q (checked by self-test)",
            "seed": SEED,
            "base_length": BASE_LENGTH,
            "target_levels": TARGET_LEVELS,
            "segment_max_length": SEGMENT_MAX_LENGTH,
            "segment_tries": SEGMENT_TRIES,
            "level_restarts": LEVEL_RESTARTS,
            "dfs_node_budget": DFS_NODE_BUDGET,
            "cube_definition": "Z^3 intersection [-2,2]^3 minus zero (124 moves)",
            "sphere_definition": "integer Euclidean shell x^2+y^2+z^2=74 (120 primitive equal-length moves)",
        },
        "selected_metrics": selected,
        "verdict": verdict,
        "claim_boundary": (
            "Exact finite evidence for one deterministic seed and three amplification levels. "
            "It neither proves infinite continuation nor compares every seed or routing policy."
        ),
    }
    output_path = Path(args.output)
    atomic_json(output_path, output)
    print(json.dumps(verdict, indent=2))
    print(f"wrote {output_path}")
    return 0


def matrix_multiply(left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(sum(left[i][k] * right[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def transpose(matrix: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(matrix[j][i] for j in range(3)) for i in range(3))


def self_test() -> None:
    assert matrix_multiply(matrix_multiply(transpose(M), Q), M) == tuple(tuple(9 * value for value in row) for row in Q)
    for variant, expected in (("cube", 124), ("sphere", 120)):
        menu = menu_vectors(variant)
        assert len(menu) == expected
        assert len(menu) == len(set(menu))
        assert all(tuple(-value for value in step) in set(menu) for step in menu)
    points = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 1)]
    verify_points(points)
    try:
        verify_points([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    except AssertionError:
        pass
    else:
        raise AssertionError("collinearity self-test failed")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = result.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run/resume one controlled variant")
    run.add_argument("--variant", choices=("cube", "sphere"), required=True)
    run.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    run.add_argument("--checkpoint")
    run.add_argument("--result")
    run.add_argument("--log")
    run.add_argument("--force", action="store_true", help="discard matching-path prior progress and rerun")
    compare = subparsers.add_parser("compare", help="validate both detailed results and write compact summary")
    compare.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    compare.add_argument("--cube-result")
    compare.add_argument("--sphere-result")
    compare.add_argument("--output", default=str(DEFAULT_SUMMARY))
    return result


def main() -> int:
    self_test()
    args = parser().parse_args()
    if args.command == "run":
        return run_variant(args)
    return compare_runs(args)


if __name__ == "__main__":
    raise SystemExit(main())
