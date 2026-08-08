#!/usr/bin/env python3
"""Exact finite probe of spherical lattice menus for Erdős Problem 193.

The certified construction uses the Chebyshev ball [-2, 2]^3 minus zero.
This experiment compares it with Euclidean and invariant-Q lattice balls,
checks exact short-connector reachability under M, and measures compatibility
with the recorded L8 orbit and the canonical full-menu cycle obstruction.

This is an experiment, not an unconditional proof.  Compatible interrupted
runs resume from the checkpoint at the next menu-step boundary.  The checkpoint
is rejected if the algorithm, menu specification, source inputs, or maximum
connector length changed.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import combinations, product
import json
import math
import os
from pathlib import Path
from random import Random
import signal
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amplify193 import find_base, legal_against
from erdos193 import first_disqualifier
from imbricate_seam import walk_points
from search193 import candidate_step_vectors


SCHEMA_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1
ALGORITHM_VERSION = 2
DEFAULT_OUTPUT = Path("/tmp/spherical-menu-probe-summary.json")
DEFAULT_CHECKPOINT = Path("/tmp/spherical-menu-probe-checkpoint.json")
DEFAULT_LOG = Path("/tmp/spherical-menu-probe.log.jsonl")
DEFAULT_ORBIT = ROOT / "gate2-193-L8.txt"
THREAD_ENVIRONMENT_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
Q = (
    (1, 0, 0),
    (0, 6, -1),
    (0, -1, 6),
)
MENU_SPECS = (
    ("cube-r2", "chebyshev_ball", 2),
    ("euclidean-ball-r2", "euclidean_ball", 2),
    ("euclidean-ball-r3", "euclidean_ball", 3),
    ("q-ball-t12", "q_ball", 12),
    ("q-ball-t30", "q_ball", 30),
    ("q-sphere-t70", "q_sphere", 70),
)
CANONICAL_CYCLE_INDICES = (15, 1, 20, 71)
Q_SPHERE_SMOKE_SEEDS = (1, 7, 17, 193, 8292)
Q_SPHERE_SMOKE_LEVELS = 3

STOP_REQUESTED = False


def request_stop(_signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


class RunLog:
    def __init__(self, path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event, **fields):
        record = {"timestamp": utc_now(), "event": event, **fields}
        line = canonical_json(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
        detail = " ".join(f"{key}={value}" for key, value in fields.items())
        print(f"[{record['timestamp']}] {event}{(' ' + detail) if detail else ''}", flush=True)


def transpose(matrix):
    return tuple(tuple(matrix[row][column] for row in range(3)) for column in range(3))


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


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


def euclidean_norm_squared(vector):
    return sum(coordinate * coordinate for coordinate in vector)


def q_norm_squared(vector):
    x, y, z = vector
    return x * x + 6 * y * y - 2 * y * z + 6 * z * z


def lateral_q(vector):
    _x, y, z = vector
    return 3 * y * y - y * z + 3 * z * z


def euclidean_ball(radius):
    radius_squared = radius * radius
    return [
        vector
        for vector in product(range(-radius, radius + 1), repeat=3)
        if vector != (0, 0, 0) and euclidean_norm_squared(vector) <= radius_squared
    ]


def q_ball(threshold):
    x_limit = math.isqrt(threshold)
    lateral_limit = math.isqrt(threshold // 5)
    return [
        vector
        for vector in product(
            range(-x_limit, x_limit + 1),
            range(-lateral_limit, lateral_limit + 1),
            range(-lateral_limit, lateral_limit + 1),
        )
        if vector != (0, 0, 0) and q_norm_squared(vector) <= threshold
    ]

def q_sphere(threshold):
    x_limit = math.isqrt(threshold)
    lateral_limit = math.isqrt(threshold // 5)
    return [
        vector
        for vector in product(
            range(-x_limit, x_limit + 1),
            range(-lateral_limit, lateral_limit + 1),
            range(-lateral_limit, lateral_limit + 1),
        )
        if vector != (0, 0, 0) and q_norm_squared(vector) == threshold
    ]


def build_menu(kind, parameter):
    if kind == "chebyshev_ball":
        return candidate_step_vectors(parameter)
    if kind == "euclidean_ball":
        return euclidean_ball(parameter)
    if kind == "q_ball":
        return q_ball(parameter)
    if kind == "q_sphere":
        return q_sphere(parameter)
    raise ValueError(f"unknown menu kind: {kind}")


def menu_sha256(menu):
    return sha256_bytes(canonical_json(menu).encode("utf-8"))


def legal_word(word, target):
    points = [(0, 0, 0)]
    for step in word:
        points.append(add(points[-1], step))
    if points[-1] != target or len(set(points)) != len(points):
        return False
    for first, second, third in combinations(range(len(points)), 3):
        if cross(
            subtract(points[second], points[first]),
            subtract(points[third], points[first]),
        ) == (0, 0, 0):
            return False
    return True


def first_connector(menu, target, max_length):
    """Return an exact shortest legal connector and tested-candidate counts."""
    menu_set = set(menu)
    examined = Counter()

    if max_length >= 2:
        for first in menu:
            second = subtract(target, first)
            if second in menu_set:
                examined[2] += 1
                word = (first, second)
                if legal_word(word, target):
                    return word, examined

    if max_length >= 3:
        for first in menu:
            remainder = subtract(target, first)
            for second in menu:
                third = subtract(remainder, second)
                if third in menu_set:
                    examined[3] += 1
                    word = (first, second, third)
                    if legal_word(word, target):
                        return word, examined

    if max_length >= 4:
        for first in menu:
            first_remainder = subtract(target, first)
            for second in menu:
                second_remainder = subtract(first_remainder, second)
                for third in menu:
                    fourth = subtract(second_remainder, third)
                    if fourth in menu_set:
                        examined[4] += 1
                        word = (first, second, third, fourth)
                        if legal_word(word, target):
                            return word, examined

    return None, examined

def all_legal_four_domains(menu):
    pair_words = defaultdict(list)
    for first in menu:
        for second in menu:
            pair_words[add(first, second)].append((first, second))

    domains = {}
    for step in menu:
        target = matrix_vector(M, step)
        words = []
        for pair_sum, left_words in pair_words.items():
            right_words = pair_words.get(subtract(target, pair_sum))
            if right_words is None:
                continue
            for first, second in left_words:
                for third, fourth in right_words:
                    word = (first, second, third, fourth)
                    if legal_word(word, target):
                        words.append(word)
        domains[step] = words
    return domains


def amplify_from_domains(word, menu, domains, rng, restarts=20):
    menu_index = {step: index for index, step in enumerate(menu)}
    anchors = [matrix_vector(M, point) for point in walk_points(word, menu)]

    for _restart in range(restarts):
        points = [anchors[0]]
        point_set = {anchors[0]}
        amplified = []
        failed = False

        for segment_index, old_step_index in enumerate(word):
            target = anchors[segment_index + 1]
            future = anchors[segment_index + 2 :]
            future_set = set(future)
            candidates = list(domains[menu[old_step_index]])
            rng.shuffle(candidates)
            chosen = None

            for connector in candidates:
                segment_points = []
                last = points[-1]
                valid = True
                for step in connector:
                    point = add(last, step)
                    if point != target and not legal_against(
                        points + segment_points + [target] + future,
                        point_set | set(segment_points) | {target} | future_set,
                        point,
                    ):
                        valid = False
                        break
                    segment_points.append(point)
                    last = point
                if valid and last == target:
                    chosen = (connector, segment_points)
                    break

            if chosen is None:
                failed = True
                break
            connector, segment_points = chosen
            points.extend(segment_points)
            point_set.update(segment_points)
            amplified.extend(menu_index[step] for step in connector)

        if not failed:
            if first_disqualifier(points) is not None:
                raise AssertionError("domain amplifier produced an invalid walk")
            return amplified
    return None


def validate_smoke_record(record, menu):
    completed_level = record.get("completed_level")
    lengths = record.get("lengths")
    word = record.get("word")
    if (
        type(completed_level) is not int
        or completed_level < 0
        or not isinstance(lengths, list)
        or len(lengths) != completed_level + 1
        or not isinstance(word, list)
        or any(type(index) is not int or not 0 <= index < len(menu) for index in word)
        or lengths[-1] != len(word)
    ):
        raise ValueError("corrupt Q-sphere smoke checkpoint")
    if first_disqualifier(walk_points(word, menu)) is not None:
        raise ValueError("invalid walk in Q-sphere smoke checkpoint")
    return completed_level, lengths, word


def q_sphere_smoke(
    menu,
    domains,
    checkpoint,
    checkpoint_path,
    logger,
    time_budget_seconds,
    started,
):
    smoke = checkpoint.setdefault(
        "q_sphere_smoke",
        {"menu_sha256": menu_sha256(menu), "seeds": {}},
    )
    if smoke.get("menu_sha256") != menu_sha256(menu):
        raise ValueError("Q-sphere smoke checkpoint menu mismatch")
    seed_records = smoke.get("seeds")
    if not isinstance(seed_records, dict):
        raise ValueError("corrupt Q-sphere smoke seed records")

    for seed in Q_SPHERE_SMOKE_SEEDS:
        key = str(seed)
        if key not in seed_records:
            base = find_base(menu, Random(seed), length=20, tries=200)
            if first_disqualifier(walk_points(base, menu)) is not None:
                raise AssertionError("invalid Q-sphere base walk")
            seed_records[key] = {
                "completed_level": 0,
                "lengths": [len(base)],
                "word": base,
            }
            atomic_write_json(checkpoint_path, checkpoint)

        record = seed_records[key]
        completed_level, lengths, word = validate_smoke_record(record, menu)
        while completed_level < Q_SPHERE_SMOKE_LEVELS:
            if STOP_REQUESTED or (
                time_budget_seconds is not None
                and time.monotonic() - started >= time_budget_seconds
            ):
                atomic_write_json(checkpoint_path, checkpoint)
                logger.emit(
                    "q_sphere_smoke_paused",
                    seed=seed,
                    completed_level=completed_level,
                    checkpoint=str(checkpoint_path),
                )
                return False

            next_level = completed_level + 1
            level_rng = Random(seed * 1_000_003 + next_level)
            amplified = amplify_from_domains(word, menu, domains, level_rng)
            if amplified is None:
                record["failure_level"] = next_level
                atomic_write_json(checkpoint_path, checkpoint)
                logger.emit("q_sphere_smoke_failed", seed=seed, level=next_level)
                break
            if first_disqualifier(walk_points(amplified, menu)) is not None:
                raise AssertionError("Q-sphere smoke verification failed")

            word = amplified
            completed_level = next_level
            lengths.append(len(word))
            record.update(
                {
                    "completed_level": completed_level,
                    "lengths": lengths,
                    "word": word,
                }
            )
            atomic_write_json(checkpoint_path, checkpoint)
            logger.emit(
                "q_sphere_smoke_progress",
                seed=seed,
                level=completed_level,
                steps=len(word),
                checkpoint=str(checkpoint_path),
            )
    return True


def make_config(max_length, orbit_path):
    source_paths = {
        "probe": Path(__file__).resolve(),
        "menu_provider": ROOT / "search193.py",
        "amplifier": ROOT / "amplify193.py",
        "walk_provider": ROOT / "imbricate_seam.py",
        "verifier": ROOT / "erdos193.py",
    }
    if orbit_path is not None:
        source_paths["orbit"] = orbit_path.resolve()
    source_sha256 = {
        name: sha256_file(path) for name, path in source_paths.items() if path.exists()
    }
    payload = {
        "algorithm_version": ALGORITHM_VERSION,
        "matrix": M,
        "quadratic_form": Q,
        "menu_specs": MENU_SPECS,
        "max_connector_length": max_length,
        "q_sphere_smoke_seeds": Q_SPHERE_SMOKE_SEEDS,
        "q_sphere_smoke_levels": Q_SPHERE_SMOKE_LEVELS,
        "source_sha256": source_sha256,
    }
    return payload, sha256_bytes(canonical_json(payload).encode("utf-8"))


def load_checkpoint(path, config_sha256):
    if not path.exists():
        return {
            "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
            "config_sha256": config_sha256,
            "menus": {},
        }
    try:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"corrupt checkpoint {path}: {error}") from error
    if checkpoint.get("checkpoint_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError(f"incompatible checkpoint schema in {path}")
    if checkpoint.get("config_sha256") != config_sha256:
        raise ValueError(
            f"checkpoint {path} belongs to a different configuration; "
            "choose a fresh --checkpoint path"
        )
    if not isinstance(checkpoint.get("menus"), dict):
        raise ValueError(f"corrupt checkpoint menu payload in {path}")
    return checkpoint


def validate_menu_checkpoint(menu_name, menu, record):
    if record.get("menu_sha256") != menu_sha256(menu):
        raise ValueError(f"checkpoint menu hash mismatch for {menu_name}")
    results = record.get("results")
    if not isinstance(results, list) or len(results) > len(menu):
        raise ValueError(f"checkpoint result shape mismatch for {menu_name}")
    for index, result in enumerate(results):
        if tuple(result.get("step", ())) != menu[index]:
            raise ValueError(f"checkpoint result order mismatch for {menu_name} at {index}")
        witness_payload = result.get("witness")
        if witness_payload is not None:
            witness = tuple(tuple(step) for step in witness_payload)
            if not legal_word(witness, matrix_vector(M, menu[index])):
                raise ValueError(f"invalid checkpoint witness for {menu_name} at {index}")
    return results


def connector_audit(
    menus,
    checkpoint,
    checkpoint_path,
    max_length,
    logger,
    time_budget_seconds,
    started,
):
    total = sum(len(menu) for menu in menus.values())
    initially_complete = sum(
        len(checkpoint["menus"].get(name, {}).get("results", ())) for name in menus
    )
    completed_this_run = 0

    for menu_name, menu in menus.items():
        record = checkpoint["menus"].setdefault(
            menu_name,
            {"menu_sha256": menu_sha256(menu), "results": []},
        )
        results = validate_menu_checkpoint(menu_name, menu, record)
        logger.emit(
            "menu_start",
            menu=menu_name,
            size=len(menu),
            resumed_steps=len(results),
            checkpoint=str(checkpoint_path),
        )

        for index in range(len(results), len(menu)):
            if STOP_REQUESTED or (
                time_budget_seconds is not None
                and time.monotonic() - started >= time_budget_seconds
            ):
                atomic_write_json(checkpoint_path, checkpoint)
                logger.emit(
                    "paused",
                    completed=initially_complete + completed_this_run,
                    total=total,
                    checkpoint=str(checkpoint_path),
                )
                return False

            step = menu[index]
            witness, examined = first_connector(
                menu, matrix_vector(M, step), max_length
            )
            results.append(
                {
                    "step": step,
                    "witness": witness,
                    "examined_by_length": dict(sorted(examined.items())),
                }
            )
            completed_this_run += 1
            atomic_write_json(checkpoint_path, checkpoint)

            if (index + 1) % 8 == 0 or index + 1 == len(menu):
                elapsed = max(time.monotonic() - started, 1e-9)
                rate = completed_this_run / elapsed
                complete = initially_complete + completed_this_run
                remaining = total - complete
                eta_seconds = remaining / rate if rate else None
                logger.emit(
                    "progress",
                    menu=menu_name,
                    completed=complete,
                    total=total,
                    throughput_steps_per_second=round(rate, 3),
                    elapsed_seconds=round(elapsed, 3),
                    eta_seconds=None if eta_seconds is None else round(eta_seconds, 1),
                    checkpoint=str(checkpoint_path),
                )

    return True


def norm_histogram(menu, norm_function):
    counts = Counter(norm_function(vector) for vector in menu)
    return {str(value): counts[value] for value in sorted(counts)}


def menu_summary(name, menu, checkpoint_record, cube_menu):
    results = validate_menu_checkpoint(name, menu, checkpoint_record)
    if len(results) != len(menu):
        raise ValueError(f"incomplete results for {name}")
    length_counts = Counter(
        "missing" if result["witness"] is None else str(len(result["witness"]))
        for result in results
    )
    menu_set = set(menu)
    cube_set = set(cube_menu)
    return {
        "size": len(menu),
        "menu_sha256": menu_sha256(menu),
        "coordinate_extent": [max(abs(vector[index]) for vector in menu) for index in range(3)],
        "euclidean_norm_squared_histogram": norm_histogram(menu, euclidean_norm_squared),
        "q_norm_squared_histogram": norm_histogram(menu, q_norm_squared),
        "connector_minimum_length_histogram": {
            key: length_counts.get(key, 0) for key in ("2", "3", "4", "missing")
        },
        "all_steps_reachable": length_counts.get("missing", 0) == 0,
        "overlap_with_cube_r2": len(menu_set & cube_set),
        "removed_from_cube_r2": sorted(cube_set - menu_set),
        "added_to_cube_r2": sorted(menu_set - cube_set),
        "connector_results": results,
    }


def orbit_summary(orbit_path, cube_menu, menus):
    if orbit_path is None or not orbit_path.exists():
        return None
    word = ast.literal_eval(orbit_path.read_text(encoding="utf-8"))
    if not isinstance(word, (list, tuple)):
        raise ValueError(f"orbit {orbit_path} is not a step-index sequence")
    if any(type(index) is not int or not 0 <= index < len(cube_menu) for index in word):
        raise ValueError(f"orbit {orbit_path} contains an invalid cube-menu index")
    vectors = [cube_menu[index] for index in word]
    records = {}
    for name, menu in menus.items():
        menu_set = set(menu)
        retained = sum(vector in menu_set for vector in vectors)
        records[name] = {
            "retained_step_occurrences": retained,
            "removed_step_occurrences": len(vectors) - retained,
            "retained_fraction": retained / len(vectors) if vectors else 1.0,
        }
    return {
        "path": str(orbit_path),
        "sha256": sha256_file(orbit_path),
        "step_count": len(vectors),
        "distinct_cube_vectors_used": len(set(vectors)),
        "menus": records,
    }


def mathematical_summary():
    mtqm = matrix_product(matrix_product(transpose(M), Q), M)
    nine_q = tuple(tuple(9 * value for value in row) for row in Q)
    mtm = matrix_product(transpose(M), M)
    basis = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    return {
        "m_transpose_q_m": mtqm,
        "nine_q": nine_q,
        "q_similarity_ratio_three": mtqm == nine_q,
        "m_transpose_m": mtm,
        "euclidean_similarity_ratio_three": mtm
        == ((9, 0, 0), (0, 9, 0), (0, 0, 9)),
        "lateral_q_scales_by_nine_on_basis": all(
            lateral_q(matrix_vector(M, vector)) == 9 * lateral_q(vector)
            for vector in basis
        ),
        "first_coordinate_scales_by_three": all(
            matrix_vector(M, vector)[0] == 3 * vector[0] for vector in basis
        ),
        "interpretation": (
            "In Q-spherical coordinates, radius scales by 3 and the polar ratio "
            "x^2/Q is invariant. This is the existing invariant-cone coordinate; "
            "standard Euclidean spherical coordinates are not respected by M."
        ),
    }

def determinant(first, second, third):
    return (
        first[0] * (second[1] * third[2] - second[2] * third[1])
        - first[1] * (second[0] * third[2] - second[2] * third[0])
        + first[2] * (second[0] * third[1] - second[1] * third[0])
    )


def lattice_index(menu):
    divisor = 0
    for first, second, third in combinations(menu, 3):
        divisor = math.gcd(divisor, abs(determinant(first, second, third)))
    return divisor


def q_sphere_summary(menu, domains, checkpoint):
    domain_counts = Counter(len(words) for words in domains.values())
    smoke = checkpoint["q_sphere_smoke"]["seeds"]
    return {
        "threshold": 70,
        "size": len(menu),
        "all_vectors_primitive": all(
            math.gcd(math.gcd(abs(x), abs(y)), abs(z)) == 1 for x, y, z in menu
        ),
        "unoriented_rays": len(menu) // 2,
        "generated_lattice_index": lattice_index(menu),
        "legal_four_step_domain_count": sum(len(words) for words in domains.values()),
        "legal_words_per_target_histogram": {
            str(count): multiplicity
            for count, multiplicity in sorted(domain_counts.items())
        },
        "minimum_legal_words_per_target": min(map(len, domains.values())),
        "maximum_legal_words_per_target": max(map(len, domains.values())),
        "three_step_obstruction": (
            "Every shell step has Q-length sqrt(70), while Mv has Q-length "
            "3*sqrt(70). Equality in the Q-norm triangle inequality forces any "
            "three summands to be parallel, producing a forbidden collinear connector."
        ),
        "parity_obstruction": (
            "Q(v) is congruent to v_x modulo 2. On an odd Q-shell, every step has "
            "odd x-coordinate, so no even-length word can sum to Mv."
        ),
        "dimension_exponent_for_four_step_scaling": math.log(4) / math.log(3),
        "smoke_results": {
            seed: {
                "completed_level": record["completed_level"],
                "lengths": record["lengths"],
                "failure_level": record.get("failure_level"),
            }
            for seed, record in sorted(smoke.items(), key=lambda item: int(item[0]))
        },
        "claim_boundary": (
            "These are finite globally verified walks, not a uniform connector-"
            "availability theorem or an infinite construction."
        ),
    }


def build_summary(
    config,
    config_sha256,
    menus,
    checkpoint,
    orbit_path,
    q_sphere_domains,
    started,
):
    cube_menu = menus["cube-r2"]
    summaries = {
        name: menu_summary(name, menu, checkpoint["menus"][name], cube_menu)
        for name, menu in menus.items()
    }
    cycle_vectors = [cube_menu[index] for index in CANONICAL_CYCLE_INDICES]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "EXACT FINITE PROBE; NOT AN UNCONDITIONAL PROOF",
        "generated_at": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "config_sha256": config_sha256,
        "config": config,
        "resource_settings": {
            name: os.environ.get(name) for name in THREAD_ENVIRONMENT_VARIABLES
        },
        "mathematics": mathematical_summary(),
        "menus": summaries,
        "recorded_orbit_compatibility": orbit_summary(orbit_path, cube_menu, menus),
        "q_sphere_t70": q_sphere_summary(
            menus["q-sphere-t70"], q_sphere_domains, checkpoint
        ),
        "canonical_full_menu_cycle": {
            "cube_indices": CANONICAL_CYCLE_INDICES,
            "vectors": cycle_vectors,
            "fully_present_by_menu": {
                name: all(vector in set(menu) for vector in cycle_vectors)
                for name, menu in menus.items()
            },
            "claim_boundary": (
                "Absence of this one witness destroys the canonical two-edge cycle, "
                "not every possible cycle in the rebuilt connector graph."
            ),
        },
        "claim_boundary": (
            "Short local connector closure does not prove global connector availability, "
            "an infinite walk, or Erdős Problem 193. Any non-cube menu requires a new "
            "orbit and new global certificates."
        ),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Compare cube, spherical lattice-ball, and invariant-Q shell menus "
            "exactly. Compatible interrupted runs resume automatically from the checkpoint."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--orbit", type=Path, default=DEFAULT_ORBIT)
    parser.add_argument(
        "--max-connector-length", type=int, choices=(2, 3, 4), default=4
    )
    parser.add_argument(
        "--time-budget-seconds",
        type=float,
        default=None,
        help="pause cleanly at a menu-step boundary after this many seconds",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    for variable in THREAD_ENVIRONMENT_VARIABLES:
        os.environ[variable] = "1"
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    orbit_path = args.orbit.resolve() if args.orbit is not None else None
    config, config_sha256 = make_config(args.max_connector_length, orbit_path)
    checkpoint = load_checkpoint(args.checkpoint, config_sha256)
    logger = RunLog(args.log)
    menus = {
        name: build_menu(kind, parameter) for name, kind, parameter in MENU_SPECS
    }
    started = time.monotonic()
    completed_before = sum(
        len(checkpoint["menus"].get(name, {}).get("results", ())) for name in menus
    )
    logger.emit(
        "start" if completed_before == 0 else "resume",
        config_sha256=config_sha256,
        completed_steps=completed_before,
        total_steps=sum(len(menu) for menu in menus.values()),
        max_connector_length=args.max_connector_length,
        checkpoint=str(args.checkpoint),
        output=str(args.output),
        resource_settings={name: os.environ[name] for name in THREAD_ENVIRONMENT_VARIABLES},
    )

    complete = connector_audit(
        menus,
        checkpoint,
        args.checkpoint,
        args.max_connector_length,
        logger,
        args.time_budget_seconds,
        started,
    )
    if not complete:
        return 2

    q_sphere_menu = menus["q-sphere-t70"]
    q_sphere_domains = all_legal_four_domains(q_sphere_menu)
    if any(not words for words in q_sphere_domains.values()):
        raise AssertionError("Q-sphere T=70 lost four-step closure")
    logger.emit(
        "q_sphere_domains_ready",
        menu_size=len(q_sphere_menu),
        legal_words=sum(len(words) for words in q_sphere_domains.values()),
    )
    complete = q_sphere_smoke(
        q_sphere_menu,
        q_sphere_domains,
        checkpoint,
        args.checkpoint,
        logger,
        args.time_budget_seconds,
        started,
    )
    if not complete:
        return 2

    summary = build_summary(
        config,
        config_sha256,
        menus,
        checkpoint,
        orbit_path,
        q_sphere_domains,
        started,
    )
    atomic_write_json(args.output, summary)
    logger.emit(
        "complete",
        elapsed_seconds=round(time.monotonic() - started, 3),
        output=str(args.output),
        output_sha256=sha256_file(args.output),
        checkpoint=str(args.checkpoint),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
