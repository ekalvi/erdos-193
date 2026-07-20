#!/usr/bin/env python3
"""Exact chronological L4 -> L5 replay of the fixed 124-word pilot policy.

The policy in ``nonx-fixed-word-policy-probe-summary.json`` was certified only
to induce an acyclic direction-blind compatibility graph.  This checker asks
the missing feasibility question on the pinned L5 stitch schedule: at every
occurrence of parent step ``s``, try exactly the policy word ``sigma_s``
against the entire currently placed state.

The first failed stitch is emitted with an exact witness for every failed
channel.  No fallback word is tried and the failed word is never committed.
If all L5 stitches pass, the checker stops after L5; deeper continuation is a
separate experiment requiring a new resource estimate.

Run from the repository root on one low-priority thread:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B \
        design/fixed_policy_chronological_replay.py \
        --output /tmp/fixed-policy-chronological-replay.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import resource
import tempfile
import time
from itertools import combinations
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "design" / "nonx-fixed-word-policy-probe-summary.json"
STATE_PATH = ROOT / "gate2-l7-construction-L5.pkl"

EXPECTED_SHA256 = {
    "design/nonx-fixed-word-policy-probe-summary.json": (
        "7a2e8c9e8c4845a5f7be7620ab7b8a12a53cae4fe24cf53f76228bd3e3fd739c"
    ),
    "design/nonx_fixed_word_policy_probe.py": (
        "531ba6ee0bfa8d5bf7485d70b13687ace4e1b100cdcdfd739b8bdcac9d8efdd3"
    ),
    "design/no_new_x_line_constructor.py": (
        "6eca827ef7b6a4dfad57554bb89156fff79c2f495e89ba33e166aebbba21fffd"
    ),
    "gate2-l7-construction-L5.pkl": (
        "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
    ),
}
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
EXPECTED_STEPS = 124
EXPECTED_GAPS = 2_457
EXPECTED_ANCHORS = 2_458

MENU = tuple(
    (x, y, z)
    for x in range(-2, 3)
    for y in range(-2, 3)
    for z in range(-2, 3)
    if (x, y, z) != (0, 0, 0)
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resource_policy():
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if any(value != "1" for value in environment.values()) or nice < 15:
        raise RuntimeError(
            "run requires numerical thread controls=1 and nice>=15",
            environment,
            nice,
        )
    return {
        "thread_environment": environment,
        "process_nice": nice,
        "processes": 1,
        "threads": 1,
    }


def verify_inputs():
    observed = {
        name: file_sha256(ROOT / name) for name in EXPECTED_SHA256
    }
    if observed != EXPECTED_SHA256:
        raise AssertionError("pinned input drift", EXPECTED_SHA256, observed)
    return observed


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def subtract(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def canonical_primitive(vector):
    x, y, z = vector
    divisor = gcd(gcd(abs(x), abs(y)), abs(z))
    if divisor:
        x, y, z = x // divisor, y // divisor, z // divisor
    if x < 0 or (x == 0 and (y < 0 or (y == 0 and z < 0))):
        x, y, z = -x, -y, -z
    return (x, y, z)


def word_points(start, word):
    point = start
    interiors = []
    for slot, step in enumerate(word):
        point = add(point, MENU[step])
        if slot + 1 < len(word):
            interiors.append(point)
    return tuple(interiors), point


def exact_collinearity_record(indices, points):
    left = subtract(points[1], points[0])
    right = subtract(points[2], points[0])
    determinant = cross(left, right)
    if determinant != (0, 0, 0):
        raise AssertionError("purported witness is not collinear")
    return {
        "indices": list(indices),
        "points": [list(point) for point in points],
        "cross_product": list(determinant),
    }


def first_projection_conflict(interiors, points, fibre_owner):
    local_owner = {}
    for interior_index, point in enumerate(interiors):
        fibre = point[1:]
        old_index = fibre_owner.get(fibre)
        if old_index is not None:
            old_point = points[old_index]
            return {
                "kind": "existing_yz_fibre",
                "interior_index": interior_index,
                "interior_point": list(point),
                "yz_fibre": list(fibre),
                "existing_point_index": old_index,
                "existing_point": list(old_point),
                "x_parallel_displacement": [
                    point[0] - old_point[0], 0, 0
                ],
            }
        earlier = local_owner.get(fibre)
        if earlier is not None:
            return {
                "kind": "repeated_yz_fibre_within_word",
                "interior_indices": [earlier, interior_index],
                "interior_points": [
                    list(interiors[earlier]), list(point)
                ],
                "yz_fibre": list(fibre),
            }
        local_owner[fibre] = interior_index
    return None


def first_collision(interiors, points, point_owner):
    local_owner = {}
    for interior_index, point in enumerate(interiors):
        old_index = point_owner.get(point)
        if old_index is not None:
            return {
                "kind": "old_new_vertex_collision",
                "interior_index": interior_index,
                "point": list(point),
                "existing_point_index": old_index,
                "existing_point": list(points[old_index]),
            }
        earlier = local_owner.get(point)
        if earlier is not None:
            return {
                "kind": "new_new_vertex_collision",
                "interior_indices": [earlier, interior_index],
                "point": list(point),
            }
        local_owner[point] = interior_index
    return None


def first_old_old_new(interiors, points):
    for interior_index, new_point in enumerate(interiors):
        direction_owner = {}
        for old_index, old_point in enumerate(points):
            direction = canonical_primitive(subtract(old_point, new_point))
            earlier = direction_owner.get(direction)
            if earlier is not None:
                return {
                    "kind": "old_old_new_collinearity",
                    "new_interior_index": interior_index,
                    "primitive_direction": list(direction),
                    **exact_collinearity_record(
                        (earlier, old_index, f"new:{interior_index}"),
                        (points[earlier], old_point, new_point),
                    ),
                }
            direction_owner[direction] = old_index
    return None


def first_old_new_new(interiors, points):
    for left, right in combinations(range(len(interiors)), 2):
        first = interiors[left]
        second = interiors[right]
        direction = subtract(second, first)
        for old_index, old_point in enumerate(points):
            if cross(direction, subtract(old_point, first)) == (0, 0, 0):
                return {
                    "kind": "old_new_new_collinearity",
                    "new_interior_indices": [left, right],
                    **exact_collinearity_record(
                        (old_index, f"new:{left}", f"new:{right}"),
                        (old_point, first, second),
                    ),
                }
    return None


def first_new_new_new(interiors):
    for triple in combinations(range(len(interiors)), 3):
        selected = tuple(interiors[index] for index in triple)
        if cross(
            subtract(selected[1], selected[0]),
            subtract(selected[2], selected[0]),
        ) == (0, 0, 0):
            return {
                "kind": "new_new_new_collinearity",
                **exact_collinearity_record(
                    tuple(f"new:{index}" for index in triple), selected
                ),
            }
    return None


def first_disqualifier(points):
    point_owner = {}
    for current_index, current in enumerate(points):
        earlier = point_owner.get(current)
        if earlier is not None:
            return {
                "kind": "repeated_vertex",
                "indices": [earlier, current_index],
                "point": list(current),
            }
        direction_owner = {}
        for old_index in range(current_index):
            direction = canonical_primitive(
                subtract(points[old_index], current)
            )
            earlier = direction_owner.get(direction)
            if earlier is not None:
                return {
                    "kind": "collinear_triple",
                    "primitive_direction": list(direction),
                    **exact_collinearity_record(
                        (earlier, old_index, current_index),
                        (points[earlier], points[old_index], current),
                    ),
                }
            direction_owner[direction] = old_index
        point_owner[current] = current_index
    return None


def channel_record(witness):
    return {"passed": witness is None, "first_witness": witness}


def load_inputs():
    with POLICY_PATH.open() as handle:
        policy = json.load(handle)
    with STATE_PATH.open("rb") as handle:
        state = pickle.load(handle)

    words = tuple(
        tuple(word) for word in policy["fixed_policy"]["selected_words_by_step"]
    )
    ordinals = tuple(
        policy["fixed_policy"]["selected_ordinals_by_step"]
    )
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    order = tuple(state["order"])
    if len(MENU) != EXPECTED_STEPS or len(words) != EXPECTED_STEPS:
        raise AssertionError("fixed policy step count drift")
    if len(ordinals) != EXPECTED_STEPS:
        raise AssertionError("fixed policy ordinal count drift")
    if len(parent_word) != EXPECTED_GAPS or len(anchors) != EXPECTED_ANCHORS:
        raise AssertionError("pinned L5 state size drift")
    if sorted(order) != list(range(EXPECTED_GAPS)):
        raise AssertionError("pinned stitch order is not a permutation")
    if any(not word for word in words):
        raise AssertionError("empty fixed policy word")
    if any(any(not 0 <= step < len(MENU) for step in word) for word in words):
        raise AssertionError("fixed policy contains invalid menu index")
    return policy, words, ordinals, parent_word, anchors, order


def run():
    started = time.monotonic()
    checker_sha256 = file_sha256(Path(__file__).resolve())
    policy_resource = resource_policy()
    input_sha256 = verify_inputs()
    policy, words, ordinals, parent_word, anchors, order = load_inputs()

    initial_disqualifier = first_disqualifier(anchors)
    if initial_disqualifier is not None:
        raise AssertionError(
            "pinned anchor state is already disqualified", initial_disqualifier
        )

    points = list(anchors)
    point_owner = {point: index for index, point in enumerate(points)}
    fibre_owner = {}
    for index, point in enumerate(points):
        fibre_owner.setdefault(point[1:], index)

    successful_records = []
    first_failure = None
    for construction_rank, gap in enumerate(order):
        parent_step = parent_word[gap]
        word = words[parent_step]
        start = anchors[gap]
        target = anchors[gap + 1]
        interiors, endpoint = word_points(start, word)

        endpoint_witness = None
        if endpoint != target:
            endpoint_witness = {
                "kind": "endpoint_mismatch",
                "computed_endpoint": list(endpoint),
                "required_endpoint": list(target),
                "difference": list(subtract(endpoint, target)),
            }
        projection_witness = first_projection_conflict(
            interiors, points, fibre_owner
        )
        collision_witness = first_collision(
            interiors, points, point_owner
        )
        old_old_new_witness = first_old_old_new(interiors, points)
        old_new_new_witness = first_old_new_new(interiors, points)
        new_new_new_witness = first_new_new_new(interiors)
        checks = {
            "endpoint": channel_record(endpoint_witness),
            "projection_freshness": channel_record(projection_witness),
            "collision": channel_record(collision_witness),
            "old_old_new": channel_record(old_old_new_witness),
            "old_new_new": channel_record(old_new_new_witness),
            "new_new_new": channel_record(new_new_new_witness),
        }
        failed_channels = [
            channel for channel, record in checks.items() if not record["passed"]
        ]
        if failed_channels:
            primary = failed_channels[0]
            prior_success = successful_records[-1] if successful_records else None
            first_failure = {
                "construction_rank_0_based": construction_rank,
                "construction_rank_1_based": construction_rank + 1,
                "gap": gap,
                "parent_step": parent_step,
                "policy_word_ordinal_1_based": ordinals[parent_step],
                "fixed_word": list(word),
                "start": list(start),
                "target": list(target),
                "proper_interiors": [list(point) for point in interiors],
                "placed_points_before_attempt": len(points),
                "failed_channels_in_check_order": failed_channels,
                "primary_killed_channel": primary,
                "primary_exact_witness": checks[primary]["first_witness"],
                "same_parent_step_and_fixed_word_as_immediately_prior_success": (
                    prior_success is not None
                    and prior_success["parent_step"] == parent_step
                    and tuple(prior_success["fixed_word"]) == word
                ),
                "checks": checks,
            }
            break

        first_index = len(points)
        for offset, point in enumerate(interiors):
            point_owner[point] = first_index + offset
            fibre_owner.setdefault(point[1:], first_index + offset)
        points.extend(interiors)
        successful_records.append({
            "construction_rank_0_based": construction_rank,
            "gap": gap,
            "parent_step": parent_step,
            "policy_word_ordinal_1_based": ordinals[parent_step],
            "fixed_word": list(word),
            "proper_interiors": [list(point) for point in interiors],
        })

    completed = first_failure is None
    if completed:
        final_disqualifier = first_disqualifier(points)
        if final_disqualifier is not None:
            raise AssertionError(
                "incremental checks passed but final verifier failed",
                final_disqualifier,
            )
    else:
        final_disqualifier = None

    if file_sha256(Path(__file__).resolve()) != checker_sha256:
        raise RuntimeError("checker changed during replay")
    return {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": (
            "exact pinned L5 fixed-policy replay completed"
            if completed
            else "exact pinned L5 fixed-policy first-failure certificate"
        ),
        "checker": {
            "path": "design/fixed_policy_chronological_replay.py",
            "sha256": checker_sha256,
            "unchanged_during_replay": True,
        },
        "input_sha256": input_sha256,
        "resource_policy": policy_resource,
        "scope": {
            "level": 5,
            "schedule": "pinned fragile-first gate order",
            "gaps": len(parent_word),
            "anchors": len(anchors),
            "all_anchors_present_before_first_stitch": True,
            "policy": policy["fixed_policy"]["definition"],
            "one_fixed_word_per_parent_step": True,
            "fallback_words_tried": 0,
            "stop_rule": "first failed attempted stitch",
        },
        "initial_state": {
            "point_count": len(anchors),
            "triple_free_and_vertex_injective": True,
            "ordered_anchor_stream_sha256": stable_hash(anchors),
            "parent_word_sha256": hashlib.sha256(bytes(parent_word)).hexdigest(),
            "schedule_sha256": stable_hash(order),
        },
        "replay": {
            "completed_L5": completed,
            "successful_stitches_before_stop": len(successful_records),
            "placed_points_at_stop": len(points),
            "successful_record_stream_sha256": stable_hash(successful_records),
            "last_successful_stitch_before_stop": (
                successful_records[-1] if successful_records else None
            ),
            "first_failure": first_failure,
            "final_global_disqualifier_if_completed": final_disqualifier,
            "deeper_continuation_attempted": False,
        },
        "interpretation": (
            "A failure is an exact finite counterexample to using this fixed "
            "124-word pilot on the pinned chronological L5 construction; it "
            "does not rule out a state-dependent word policy."
            if not completed
            else "The fixed policy passes this pinned L5 orbit only; no uniform theorem follows."
        ),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "maximum_resident_set_raw": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
    }


def atomic_json_dump(payload, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=output_path.parent,
        prefix=output_path.name + ".",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", default="/tmp/fixed-policy-chronological-replay.json"
    )
    args = parser.parse_args()
    payload = run()
    atomic_json_dump(payload, args.output)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "output_sha256": file_sha256(args.output),
        "completed_L5": payload["replay"]["completed_L5"],
        "successful_stitches_before_stop": payload["replay"][
            "successful_stitches_before_stop"
        ],
        "first_failure": payload["replay"]["first_failure"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "maximum_resident_set_raw": payload["maximum_resident_set_raw"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
