#!/usr/bin/env python3
"""Pre-registered hybrid cube+spherical-direction gate for Erdős #193.

The experiment first selects one 24-move spherical layer using menu geometry
only, before constructing a walk.  It then checks exact length-at-most-five
connector closure—the shortest bound that the matched cube control itself
requires—and runs the same resumable Level-0--Level-3 constructor used
by spherical_menu_comparison.py.

Commands:

    python3 -B design/hybrid_spherical_menu_experiment.py screen
    python3 -B design/hybrid_spherical_menu_experiment.py run
    python3 -B design/hybrid_spherical_menu_experiment.py compare

Working logs/checkpoints default to /tmp/hybrid-spherical-menu/.  The detailed
result and compact comparison default to design/.  Interrupted closure resumes
at the next source step; interrupted amplification resumes at the next parent
gap.  All construction and collinearity checks use exact integer arithmetic.
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
from itertools import combinations, product
from pathlib import Path
from random import Random
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design"
if str(DESIGN) not in sys.path:
    sys.path.insert(0, str(DESIGN))

import spherical_menu_comparison as base

SCHEMA = "hybrid-spherical-menu-gate-v1"
RUN_DIR = Path("/tmp/hybrid-spherical-menu")
DEFAULT_SCREEN = DESIGN / "hybrid-spherical-menu-screen.json"
DEFAULT_RESULT = DESIGN / "hybrid-spherical-menu-result.json"
DEFAULT_SUMMARY = DESIGN / "hybrid-spherical-menu-summary.json"
BASELINE_RESULT = DESIGN / "spherical-menu-cube-result.json"
LAYER_SIZE = 24
SCREEN_PROBES = 20_000
GREEDY_PROBES = 5_000
MAX_CLOSURE_LENGTH = 5

GATES = {
    "all_steps_connector_closed_through_length": MAX_CLOSURE_LENGTH,
    "maximum_L3_nodes_per_gap_over_cube": 2.0,
    "maximum_L3_cumulative_effective_dimension": 1.12,
    "maximum_L3_normalized_Q_radius4_crowding": 16,
    "maximum_L3_parallel_probability_over_cube": 1.0 / 3.0,
}


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


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class Log:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **fields: Any) -> None:
        record = {"at": now(), "event": event, **fields}
        with self.path.open("a") as handle:
            handle.write(stable_json(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        print(f"[{record['at']}] {event} " + " ".join(f"{key}={value}" for key, value in fields.items()), flush=True)


def shell(norm_squared: int) -> list[tuple[int, int, int]]:
    radius = math.isqrt(norm_squared)
    if radius * radius < norm_squared:
        radius += 1
    return [
        vector
        for vector in product(range(-radius, radius + 1), repeat=3)
        if vector != (0, 0, 0) and base.dot(vector, vector) == norm_squared
    ]


def fibonacci_probes(count: int) -> list[tuple[float, float, float]]:
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    probes = []
    for index in range(count):
        z = 1.0 - 2.0 * (index + 0.5) / count
        radial = math.sqrt(max(0.0, 1.0 - z * z))
        probes.append((radial * math.cos(index * golden_angle), radial * math.sin(index * golden_angle), z))
    return probes


def unit(vector: Sequence[int]) -> tuple[float, float, float]:
    length = math.sqrt(base.dot(vector, vector))
    return tuple(coordinate / length for coordinate in vector)  # type: ignore[return-value]


def axis_key(vector: Sequence[int]) -> tuple[int, int, int]:
    return base.primitive_unoriented(vector)


def greedy_shell14_layer() -> list[tuple[int, int, int]]:
    cube = base.menu_vectors("cube")
    candidates = sorted({axis_key(vector) for vector in shell(14)})
    assert len(candidates) == 24
    probes = fibonacci_probes(GREEDY_PROBES)
    cube_units = [unit(vector) for vector in sorted(set(base.primitive_oriented(step) for step in cube))]
    current = [max(sum(probe[i] * direction[i] for i in range(3)) for direction in cube_units) for probe in probes]
    selected: list[tuple[int, int, int]] = []

    for _ in range(12):
        best_axis = None
        best_floor = -2.0
        best_mean = -2.0
        for axis in candidates:
            if axis in selected:
                continue
            direction = unit(axis)
            updated = [max(old, abs(sum(probe[i] * direction[i] for i in range(3)))) for old, probe in zip(current, probes)]
            floor = min(updated)
            mean = statistics.fmean(updated)
            key = (floor, mean)
            if key > (best_floor, best_mean):
                best_floor, best_mean = key
                best_axis = axis
        if best_axis is None:
            raise AssertionError("greedy angular layer exhausted")
        selected.append(best_axis)
        direction = unit(best_axis)
        current = [max(old, abs(sum(probe[i] * direction[i] for i in range(3)))) for old, probe in zip(current, probes)]

    layer = sorted(selected + [tuple(-coordinate for coordinate in axis) for axis in selected])
    assert len(layer) == LAYER_SIZE
    assert all(base.dot(vector, vector) == 14 for vector in layer)
    return layer


def candidate_layers() -> dict[str, list[tuple[int, int, int]]]:
    layers = {
        "shell10-full": shell(10),
        "shell11-full": shell(11),
        "shell13-full": shell(13),
        "shell14-greedy-half": greedy_shell14_layer(),
    }
    assert all(len(layer) == LAYER_SIZE for layer in layers.values())
    return layers


def angular_metrics(menu: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    directions = sorted(set(base.primitive_oriented(step) for step in menu))
    units = [unit(direction) for direction in directions]
    nearest = []
    for index, direction in enumerate(units):
        best = max(
            sum(direction[axis] * other[axis] for axis in range(3))
            for other_index, other in enumerate(units)
            if index != other_index
        )
        nearest.append(math.degrees(math.acos(max(-1.0, min(1.0, best)))))
    probe_angles = []
    for probe in fibonacci_probes(SCREEN_PROBES):
        best = max(sum(probe[axis] * direction[axis] for axis in range(3)) for direction in units)
        probe_angles.append(math.degrees(math.acos(max(-1.0, min(1.0, best)))))
    return {
        "menu_size": len(menu),
        "oriented_projective_directions": len(directions),
        "minimum_direction_separation_degrees": min(nearest),
        "sampled_covering_radius_degrees": max(probe_angles),
        "sampled_mean_nearest_probe_angle_degrees": statistics.fmean(probe_angles),
        "probes": SCREEN_PROBES,
    }


def screen_payload() -> dict[str, Any]:
    cube = base.menu_vectors("cube")
    cube_set = set(cube)
    records = {}
    layers = candidate_layers()
    for name, layer in layers.items():
        if cube_set.intersection(layer):
            raise AssertionError(f"layer overlaps cube moves: {name}")
        menu = sorted(cube_set.union(layer))
        records[name] = {
            "layer": [list(vector) for vector in layer],
            "layer_sha256": stable_hash(layer),
            "menu_sha256": stable_hash(menu),
            "angular": angular_metrics(menu),
        }
    selected = min(
        records,
        key=lambda name: (
            records[name]["angular"]["sampled_covering_radius_degrees"],
            records[name]["angular"]["sampled_mean_nearest_probe_angle_degrees"],
            name,
        ),
    )
    return {
        "schema": SCHEMA,
        "created_at": now(),
        "selection_rule": "minimum 20,000-probe covering radius; mean nearest angle then name break ties; no walk constructed before selection",
        "cube_angular": angular_metrics(cube),
        "candidates": records,
        "selected": selected,
        "selected_layer": records[selected]["layer"],
        "selected_menu_sha256": records[selected]["menu_sha256"],
    }


def command_screen(args: argparse.Namespace) -> int:
    payload = screen_payload()
    atomic_json(Path(args.output), payload)
    print(json.dumps({"selected": payload["selected"], "cube": payload["cube_angular"], "candidates": {name: record["angular"] for name, record in payload["candidates"].items()}}, indent=2))
    print(f"wrote {args.output}")
    return 0


def selected_menu(screen: dict[str, Any]) -> list[tuple[int, int, int]]:
    cube = set(base.menu_vectors("cube"))
    layer = {tuple(vector) for vector in screen["selected_layer"]}
    menu = sorted(cube | layer)
    if len(menu) != 148 or stable_hash(menu) != screen["selected_menu_sha256"]:
        raise RuntimeError("selected menu reconstruction mismatch")
    return menu


def legal_word(word: Sequence[tuple[int, int, int]], target: tuple[int, int, int]) -> bool:
    points = [(0, 0, 0)]
    for step in word:
        points.append(base.add(points[-1], step))
    if points[-1] != target or len(points) != len(set(points)):
        return False
    for first, second, third in combinations(range(len(points)), 3):
        if base.cross(base.sub(points[second], points[first]), base.sub(points[third], points[first])) == (0, 0, 0):
            return False
    return True


def pair_word_index(
    menu: Sequence[tuple[int, int, int]],
) -> dict[tuple[int, int, int], list[tuple[tuple[int, int, int], tuple[int, int, int]]]]:
    result: dict[tuple[int, int, int], list[tuple[tuple[int, int, int], tuple[int, int, int]]]] = {}
    for first in menu:
        for second in menu:
            result.setdefault(base.add(first, second), []).append((first, second))
    return result


def first_connector(
    menu: Sequence[tuple[int, int, int]],
    target: tuple[int, int, int],
    pair_words: dict[tuple[int, int, int], list[tuple[tuple[int, int, int], tuple[int, int, int]]]],
) -> tuple[tuple[tuple[int, int, int], ...] | None, dict[int, int]]:
    menu_set = set(menu)
    examined: Counter[int] = Counter()
    for first in menu:
        second = base.sub(target, first)
        if second in menu_set:
            examined[2] += 1
            word = (first, second)
            if legal_word(word, target):
                return word, dict(examined)
    for first in menu:
        remainder = base.sub(target, first)
        for second in menu:
            third = base.sub(remainder, second)
            if third in menu_set:
                examined[3] += 1
                word = (first, second, third)
                if legal_word(word, target):
                    return word, dict(examined)
    for first in menu:
        remainder1 = base.sub(target, first)
        for second in menu:
            remainder2 = base.sub(remainder1, second)
            for third in menu:
                fourth = base.sub(remainder2, third)
                if fourth in menu_set:
                    examined[4] += 1
                    word = (first, second, third, fourth)
                    if legal_word(word, target):
                        return word, dict(examined)
    for first in menu:
        remainder1 = base.sub(target, first)
        for second in menu:
            remainder2 = base.sub(remainder1, second)
            for third in menu:
                remainder_pair = base.sub(remainder2, third)
                for fourth, fifth in pair_words.get(remainder_pair, ()):
                    examined[5] += 1
                    word = (first, second, third, fourth, fifth)
                    if legal_word(word, target):
                        return word, dict(examined)
    return None, dict(examined)


def identity(screen: dict[str, Any], menu: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    config = {
        "schema": SCHEMA,
        "selected_candidate": screen["selected"],
        "screen_sha256": stable_hash(screen),
        "menu_sha256": stable_hash(menu),
        "matrix": base.M,
        "Q": base.Q,
        "seed": base.SEED,
        "base_length": base.BASE_LENGTH,
        "target_levels": base.TARGET_LEVELS,
        "segment_max_length": base.SEGMENT_MAX_LENGTH,
        "segment_tries": base.SEGMENT_TRIES,
        "level_restarts": base.LEVEL_RESTARTS,
        "dfs_node_budget": base.DFS_NODE_BUDGET,
        "closure_max_length": MAX_CLOSURE_LENGTH,
        "experiment_code_sha256": file_hash(Path(__file__).resolve()),
        "constructor_code_sha256": file_hash(Path(base.__file__).resolve()),
    }
    return {"variant": f"hybrid-{screen['selected']}", **config, "identity_sha256": stable_hash(config)}


def closure_run(menu: Sequence[tuple[int, int, int]], ident: dict[str, Any], checkpoint: Path, log: Log, force: bool) -> list[dict[str, Any]]:
    if force:
        checkpoint.unlink(missing_ok=True)
    records: list[dict[str, Any]] = []
    if checkpoint.exists():
        payload = json.loads(checkpoint.read_text())
        if payload.get("identity") != ident["identity_sha256"]:
            raise RuntimeError("closure checkpoint identity mismatch")
        records = payload["records"]
        log.emit("closure_resume", completed=len(records), total=len(menu), checkpoint=str(checkpoint))
    started = time.monotonic()
    pair_words = pair_word_index(menu)
    for index in range(len(records), len(menu)):
        if base._STOP_REQUESTED:
            raise InterruptedError("stop requested")
        target = base.apply_matrix(base.M, menu[index])
        word, examined = first_connector(menu, target, pair_words)
        record = {
            "step_index": index,
            "step": list(menu[index]),
            "connector": None if word is None else [list(vector) for vector in word],
            "length": None if word is None else len(word),
            "examined_by_length": {str(key): value for key, value in examined.items()},
        }
        records.append(record)
        atomic_json(checkpoint, {"schema": SCHEMA, "identity": ident["identity_sha256"], "records": records, "saved_at": now()})
        if (index + 1) % 10 == 0 or index + 1 == len(menu):
            elapsed = time.monotonic() - started
            throughput = (index + 1) / elapsed if elapsed else 0.0
            eta = (len(menu) - index - 1) / throughput if throughput else None
            log.emit("closure_progress", completed=index + 1, total=len(menu), elapsed_s=round(elapsed, 3), eta_s=None if eta is None else round(eta, 3), checkpoint=str(checkpoint))
    return records


def run_hybrid(args: argparse.Namespace) -> int:
    screen_path = Path(args.screen)
    if not screen_path.exists() or args.force:
        atomic_json(screen_path, screen_payload())
    screen = json.loads(screen_path.read_text())
    menu = selected_menu(screen)
    ident = identity(screen, menu)
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    closure_checkpoint = run_dir / "closure-checkpoint.json"
    amplification_checkpoint = run_dir / "amplification-checkpoint.json"
    log = Log(run_dir / "run.jsonl")
    result_path = Path(args.result)

    signal.signal(signal.SIGINT, base.request_stop)
    signal.signal(signal.SIGTERM, base.request_stop)

    if result_path.exists() and not args.force:
        result = json.loads(result_path.read_text())
        if result.get("identity", {}).get("identity_sha256") != ident["identity_sha256"]:
            raise RuntimeError("existing hybrid result identity mismatch")
        print(f"validated existing result: {result_path}")
        return 0
    if args.force:
        result_path.unlink(missing_ok=True)
        amplification_checkpoint.unlink(missing_ok=True)

    try:
        closure = closure_run(menu, ident, closure_checkpoint, log, args.force)
        missing = [record for record in closure if record["connector"] is None]
        if missing:
            result = {
                "schema": SCHEMA,
                "status": "closure-failed",
                "created_at": now(),
                "identity": ident,
                "screen": screen,
                "menu": [list(vector) for vector in menu],
                "closure": closure,
                "missing_steps": missing,
            }
            atomic_json(result_path, result)
            log.emit("closure_failed", missing=len(missing), result=str(result_path))
            return 2
        log.emit("closure_complete", steps=len(menu), minimum=min(record["length"] for record in closure), maximum=max(record["length"] for record in closure))

        rng = Random(base.SEED)
        completed: list[dict[str, Any]]
        if amplification_checkpoint.exists() and not args.force:
            payload = json.loads(amplification_checkpoint.read_text())
            if payload.get("identity", {}).get("identity_sha256") != ident["identity_sha256"]:
                raise RuntimeError("amplification checkpoint identity mismatch")
            completed = payload["completed_levels"]
            state = payload["state"]
            state["started_monotonic"] = time.monotonic()
            rng.setstate(base.tupleify(state["rng_state"]))
            log.emit("amplification_resume", level=state["level"], next_segment=state["next_segment"])
        else:
            word = base.find_base(menu, rng)
            if len(word) != base.BASE_LENGTH:
                raise RuntimeError("failed to construct hybrid Level 0")
            points = base.walk_points(word, menu)
            completed = [{
                "level": 0,
                "word": word,
                "word_sha256": base.word_sha256(word),
                "points": [list(point) for point in points],
                "routing": None,
                "verification": base.verify_points(points),
            }]
            state = base.new_level_state(1, word, points, rng)
            base.save_checkpoint(amplification_checkpoint, ident, completed, state, rng)
            log.emit("amplification_start", base_steps=len(word), target_levels=base.TARGET_LEVELS, checkpoint=str(amplification_checkpoint))

        while int(state["level"]) <= base.TARGET_LEVELS:
            outcome = base.amplify_resumable(menu, rng, ident, completed, state, amplification_checkpoint, log)
            if outcome is None:
                raise RuntimeError(f"hybrid jammed at level {state['level']}")
            word, points, details = outcome
            completed.append({
                "level": int(state["level"]),
                "word": word,
                "word_sha256": base.word_sha256(word),
                "points": [list(point) for point in points],
                **details,
            })
            next_level = int(state["level"]) + 1
            if next_level > base.TARGET_LEVELS:
                break
            state = base.new_level_state(next_level, word, points, rng)
            base.save_checkpoint(amplification_checkpoint, ident, completed, state, rng)

    except InterruptedError:
        log.emit("interrupted", closure_checkpoint=str(closure_checkpoint), amplification_checkpoint=str(amplification_checkpoint))
        return 130

    levels = []
    for record in completed:
        points = [tuple(point) for point in record["points"]]
        levels.append({
            "level": record["level"],
            "word": record["word"],
            "word_sha256": record["word_sha256"],
            "routing": record["routing"],
            "metrics": base.point_metrics(points, menu, record["level"], len(completed[0]["word"])),
        })
    result = {
        "schema": SCHEMA,
        "status": "complete",
        "created_at": now(),
        "identity": ident,
        "screen": screen,
        "menu": [list(vector) for vector in menu],
        "menu_metrics": base.menu_metrics(menu),
        "closure": closure,
        "levels": levels,
        "claim_boundary": "one statically selected hybrid layer, one seed, and three finite levels; not successor closure or an infinite proof",
    }
    atomic_json(result_path, result)
    closure_checkpoint.unlink(missing_ok=True)
    amplification_checkpoint.unlink(missing_ok=True)
    log.emit("run_complete", result=str(result_path), sha256=file_hash(result_path))
    return 0


def compare(args: argparse.Namespace) -> int:
    baseline = base.load_complete(Path(args.baseline))
    hybrid_path = Path(args.result)
    hybrid = json.loads(hybrid_path.read_text())
    if hybrid.get("schema") != SCHEMA or hybrid.get("status") != "complete":
        raise RuntimeError("hybrid result is not complete")
    screen = hybrid["screen"]
    menu = [tuple(vector) for vector in hybrid["menu"]]
    expected = identity(screen, menu)
    if hybrid["identity"]["identity_sha256"] != expected["identity_sha256"]:
        raise RuntimeError("hybrid result identity mismatch")
    for level in hybrid["levels"]:
        points = base.walk_points(level["word"], menu)
        base.verify_points(points)
        if base.word_sha256(level["word"]) != level["word_sha256"]:
            raise RuntimeError("hybrid word hash mismatch")

    cube_l3 = baseline["levels"][3]
    hybrid_l3 = hybrid["levels"][3]
    cube_metrics = cube_l3["metrics"]
    hybrid_metrics = hybrid_l3["metrics"]
    cube_nodes = cube_l3["routing"]["nodes_per_parent_gap"]
    hybrid_nodes = hybrid_l3["routing"]["nodes_per_parent_gap"]
    cube_parallel = cube_metrics["secants"]["parallel_collision_probability"]
    hybrid_parallel = hybrid_metrics["secants"]["parallel_collision_probability"]
    checks = {
        "exact_connector_closure_length_at_most_5": {
            "passed": all(record["connector"] is not None and record["length"] <= MAX_CLOSURE_LENGTH for record in hybrid["closure"]),
            "maximum_observed_length": max(record["length"] for record in hybrid["closure"]),
        },
        "L3_nodes_per_gap_at_most_2x_cube": {
            "passed": hybrid_nodes <= GATES["maximum_L3_nodes_per_gap_over_cube"] * cube_nodes,
            "cube": cube_nodes,
            "hybrid": hybrid_nodes,
            "ratio": hybrid_nodes / cube_nodes,
        },
        "L3_effective_dimension_at_most_1_12": {
            "passed": hybrid_metrics["cumulative_effective_dimension_log_growth_over_log3"] <= GATES["maximum_L3_cumulative_effective_dimension"],
            "cube": cube_metrics["cumulative_effective_dimension_log_growth_over_log3"],
            "hybrid": hybrid_metrics["cumulative_effective_dimension_log_growth_over_log3"],
        },
        "L3_normalized_Q_crowding_at_most_cube": {
            "passed": hybrid_metrics["normalized_Q_crowding"]["4"]["maximum_neighbors"] <= GATES["maximum_L3_normalized_Q_radius4_crowding"],
            "cube": cube_metrics["normalized_Q_crowding"]["4"]["maximum_neighbors"],
            "hybrid": hybrid_metrics["normalized_Q_crowding"]["4"]["maximum_neighbors"],
        },
        "L3_parallel_probability_at_most_one_third_cube": {
            "passed": hybrid_parallel <= GATES["maximum_L3_parallel_probability_over_cube"] * cube_parallel,
            "cube": cube_parallel,
            "hybrid": hybrid_parallel,
            "ratio": hybrid_parallel / cube_parallel,
        },
    }
    overall = all(check["passed"] for check in checks.values())
    summary = {
        "schema": SCHEMA,
        "created_at": now(),
        "selected_candidate": screen["selected"],
        "selection_rule": screen["selection_rule"],
        "pre_registered_gates": GATES,
        "checks": checks,
        "overall_passed": overall,
        "decision": "retain hybrid as a live construction candidate" if overall else "retire this pre-registered hybrid candidate; do not pivot the main proof route",
        "source_results": {
            "cube": {"path": str(Path(args.baseline)), "sha256": file_hash(Path(args.baseline))},
            "hybrid": {"path": str(hybrid_path), "sha256": file_hash(hybrid_path)},
        },
        "claim_boundary": hybrid["claim_boundary"],
    }
    atomic_json(Path(args.output), summary)
    print(json.dumps(summary, indent=2))
    return 0 if overall else 3


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = result.add_subparsers(dest="command", required=True)
    screen = commands.add_parser("screen")
    screen.add_argument("--output", default=str(DEFAULT_SCREEN))
    run = commands.add_parser("run")
    run.add_argument("--screen", default=str(DEFAULT_SCREEN))
    run.add_argument("--result", default=str(DEFAULT_RESULT))
    run.add_argument("--run-dir", default=str(RUN_DIR))
    run.add_argument("--force", action="store_true")
    compare_parser = commands.add_parser("compare")
    compare_parser.add_argument("--baseline", default=str(BASELINE_RESULT))
    compare_parser.add_argument("--result", default=str(DEFAULT_RESULT))
    compare_parser.add_argument("--output", default=str(DEFAULT_SUMMARY))
    return result


def self_test() -> None:
    layers = candidate_layers()
    assert set(layers) == {"shell10-full", "shell11-full", "shell13-full", "shell14-greedy-half"}
    assert all(len(layer) == LAYER_SIZE and len(layer) == len(set(layer)) for layer in layers.values())
    assert all(set(layer).isdisjoint(base.menu_vectors("cube")) for layer in layers.values())
    baseline = json.loads(BASELINE_RESULT.read_text())
    assert baseline["status"] == "complete" and baseline["levels"][3]["metrics"]["steps"] == 145


def main() -> int:
    self_test()
    args = parser().parse_args()
    if args.command == "screen":
        return command_screen(args)
    if args.command == "run":
        return run_hybrid(args)
    return compare(args)


if __name__ == "__main__":
    raise SystemExit(main())
