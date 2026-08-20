"""
Sharded, staged, checkpointed search for long collinear-triple-free
substitution walks in Z^3 (Problem #193 programme).

Improvements over search193.py per review feedback:
  - staged prefix filtering (most candidates die on the 50-prefix check,
    and the word is only generated to full length for survivors);
  - repeated vertices reported as RepeatedVertex, not a fake collinear triple
    (both still disqualify a walk);
  - independent verification of every reported collision, plus the cubic
    oracle on short prefixes for survivors;
  - richer survivor records: seed/trial, return ranks R_m, max determinants
    Delta_m, normalized determinant delta_m, word hash;
  - atomic JSON checkpoints every CHECKPOINT_EVERY trials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from itertools import combinations
from random import Random
from typing import Dict, List, Optional, Sequence, Tuple, Union

from search193 import (
    Collision,
    Substitution,
    Symbol,
    Vector,
    analyse_marker,
    candidate_step_vectors,
    cross,
    first_collinear_triple_slow,
    fixed_point_prefix,
    is_primitive,
    prefix_points,
    primitive_direction,
    random_prolongable_substitution,
    sub,
    vector_rank,
)

STAGES = (50, 100, 250, 500, 1000, 2500, 5000)
CHECKPOINT_EVERY = 10_000


@dataclass(frozen=True)
class RepeatedVertex:
    first: int
    second: int
    point: Vector


Disqualifier = Union[Collision, RepeatedVertex]


def first_disqualifier(points: Sequence[Vector]) -> Optional[Disqualifier]:
    """
    Like search193.first_collinear_triple, but reports a repeated vertex
    honestly instead of fabricating an i == j 'triple'.
    """
    seen_points: Dict[Vector, int] = {}

    for k, p in enumerate(points):
        if p in seen_points:
            return RepeatedVertex(seen_points[p], k, p)

        direction_owner: Dict[Vector, int] = {}
        for i in range(k):
            d = primitive_direction(sub(points[i], p))
            if d in direction_owner:
                j = direction_owner[d]
                return Collision(j, i, k, points[j], points[i], points[k])
            direction_owner[d] = i

        seen_points[p] = k

    return None


def verify_collision(points: Sequence[Vector], collision: Collision) -> bool:
    i, j, k = collision.i, collision.j, collision.k
    if not (0 <= i < j < k < len(points)):
        return False
    return cross(sub(points[j], points[i]), sub(points[k], points[i])) == (0, 0, 0)


def word_hash(word: Sequence[int]) -> str:
    payload = ",".join(map(str, word)).encode()
    return hashlib.sha256(payload).hexdigest()


def norm(v: Vector) -> float:
    return (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) ** 0.5


def normalized_max_det(displacements: Sequence[Vector]) -> float:
    from search193 import det

    best = 0.0
    for a, b, c in combinations(displacements, 3):
        denominator = norm(a) * norm(b) * norm(c)
        if denominator:
            best = max(best, abs(det(a, b, c)) / denominator)
    return best


def atomic_json_dump(data, path: str) -> None:
    directory = os.path.dirname(path) or "."
    fd, temporary_path = tempfile.mkstemp(
        dir=directory, prefix=".checkpoint-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary_path, path)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise


def disqualifier_record(d: Optional[Disqualifier]):
    if d is None:
        return None
    if isinstance(d, RepeatedVertex):
        return {
            "kind": "repeated_vertex",
            "first": d.first,
            "second": d.second,
            "point": list(d.point),
        }
    return {
        "kind": "collinear_triple",
        "i": d.i,
        "j": d.j,
        "k": d.k,
        "points": [list(d.point_i), list(d.point_j), list(d.point_k)],
    }


def candidate_record(
    trial: int,
    seed: int,
    score: int,
    sigma: Substitution,
    step: Dict[Symbol, Vector],
    disqualifier: Optional[Disqualifier],
    word: Sequence[Symbol],
    profiles,
) -> dict:
    return {
        "seed": seed,
        "trial": trial,
        "score": score,
        "substitution": {str(a): list(sigma[a]) for a in sorted(sigma)},
        "step": {str(a): list(step[a]) for a in sorted(step)},
        "disqualifier": disqualifier_record(disqualifier),
        "prefix_length_tested": len(word),
        "word_hash_sha256": word_hash(word),
        "return_profiles": [
            {
                "marker": list(p.marker),
                "returns": len(p.words),
                "return_lengths": sorted(len(w) for w in p.words),
                "rank": p.rank,
                "max_det": p.maximum_determinant,
                "normalized_max_det": normalized_max_det(p.displacements),
            }
            for p in profiles
        ],
    }


def search_shard(
    seed: int,
    trials: int,
    output: str,
    alphabet_size: int = 4,
    vector_radius: int = 2,
    keep: int = 100,
) -> None:
    rng = Random(seed)
    alphabet = list(range(alphabet_size))
    vectors = candidate_step_vectors(vector_radius)
    maximum_prefix = max(STAGES)

    best: List[dict] = []
    started = time.time()
    tested = 0

    parameters = {
        "seed": seed,
        "trials": trials,
        "alphabet_size": alphabet_size,
        "vector_radius": vector_radius,
        "stages": list(STAGES),
        "keep": keep,
    }

    def checkpoint(trial: int, finished: bool) -> None:
        atomic_json_dump(
            {
                "parameters": parameters,
                "trials_completed": trial,
                "candidates_tested": tested,
                "elapsed_seconds": round(time.time() - started, 1),
                "finished": finished,
                "best": best,
            },
            output,
        )

    for trial in range(trials):
        if trial and trial % CHECKPOINT_EVERY == 0:
            checkpoint(trial, finished=False)
            print(
                f"seed={seed} trial={trial} tested={tested} "
                f"best={best[0]['score'] if best else 0} "
                f"({trial / (time.time() - started):.0f} trials/s)",
                flush=True,
            )

        sigma = random_prolongable_substitution(rng, alphabet_size)
        if not is_primitive(sigma, alphabet):
            continue

        chosen = rng.sample(vectors, alphabet_size)
        step = dict(zip(alphabet, chosen))
        if vector_rank(chosen) < 3:
            continue

        # Stage 0: cheap 50-symbol prefix; only survivors are extended.
        word = fixed_point_prefix(sigma, seed=0, target_length=STAGES[0])
        if len(word) < STAGES[0]:
            continue

        tested += 1
        disqualifier = None
        score = 0

        for stage in STAGES:
            if len(word) < stage:
                word = fixed_point_prefix(sigma, seed=0, target_length=stage)
                if len(word) < stage:
                    break
            points = prefix_points(word[:stage], step)
            disqualifier = first_disqualifier(points)
            if disqualifier is not None:
                score = (
                    disqualifier.k - 1
                    if isinstance(disqualifier, Collision)
                    else disqualifier.second - 1
                )
                break
            score = stage

        if best and len(best) >= keep and score <= best[-1]["score"]:
            continue

        # Independent verification for anything worth keeping.
        points = prefix_points(word[: min(len(word), maximum_prefix)], step)
        if isinstance(disqualifier, Collision):
            assert verify_collision(points, disqualifier), (
                seed,
                trial,
                disqualifier,
            )
        if score >= 250:
            oracle_points = points[: min(len(points), 400)]
            fast = first_disqualifier(oracle_points)
            slow = first_collinear_triple_slow(oracle_points)
            assert (fast is None) == (slow is None), (seed, trial)

        profiles = []
        if score >= 250:
            analysed_word = word[: min(len(word), maximum_prefix)]
            for marker_length in range(1, 13):
                data = analyse_marker(
                    analysed_word, analysed_word[:marker_length], step
                )
                if len(data.words) >= 2:
                    profiles.append(data)

        best.append(
            candidate_record(
                trial, seed, score, sigma, step, disqualifier, word, profiles
            )
        )
        best.sort(key=lambda r: r["score"], reverse=True)
        del best[keep:]

    checkpoint(trials, finished=True)
    print(
        f"seed={seed} DONE trials={trials} tested={tested} "
        f"best={best[0]['score'] if best else 0} "
        f"elapsed={time.time() - started:.0f}s",
        flush=True,
    )


def run_controls() -> None:
    """Scientific controls; raises AssertionError on any failure."""
    from search193 import add, safe_prefix_length

    # 1. Constant word: immediate collision.
    step = {0: (1, 0, 0)}
    assert safe_prefix_length([0] * 10, step) <= 2

    # 2. Tribonacci with standard basis: early collision (contains 00).
    trib = {0: (0, 1), 1: (0, 2), 2: (0,)}
    w = fixed_point_prefix(trib, 0, 200)
    assert (
        safe_prefix_length(w, {0: (1, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1)}) < 20
    )

    # 3. Gerver-Ramsey-style word beginning i,j,i,i,k,... has an early triple.
    gr_prefix = [0, 1, 0, 0, 2, 0, 0, 1]
    assert (
        safe_prefix_length(gr_prefix, {0: (1, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1)})
        < 8
    )

    # 4. Fast and cubic checkers agree on random short walks.
    rng = Random(7)
    vectors = candidate_step_vectors(2)
    for _ in range(300):
        points = [(0, 0, 0)]
        for _ in range(14):
            points.append(add(points[-1], rng.choice(vectors)))
        fast = first_disqualifier(points)
        slow = first_collinear_triple_slow(points)
        assert (fast is None) == (slow is None)

    # 5. Collision indices invariant under translation and unimodular maps.
    unimodular = ((1, 1, 0), (0, 1, 1), (0, 0, 1))  # det = 1

    def apply_map(p):
        return (
            unimodular[0][0] * p[0] + unimodular[0][1] * p[1] + unimodular[0][2] * p[2] + 5,
            unimodular[1][0] * p[0] + unimodular[1][1] * p[1] + unimodular[1][2] * p[2] - 3,
            unimodular[2][0] * p[0] + unimodular[2][1] * p[1] + unimodular[2][2] * p[2] + 1,
        )

    for trial_seed in range(40):
        rng2 = Random(trial_seed)
        points = [(0, 0, 0)]
        for _ in range(20):
            points.append(add(points[-1], rng2.choice(vectors)))
        a = first_disqualifier(points)
        b = first_disqualifier([apply_map(p) for p in points])
        if a is None or b is None:
            assert a is None and b is None
        else:
            ka = a.k if isinstance(a, Collision) else a.second
            kb = b.k if isinstance(b, Collision) else b.second
            assert ka == kb

    print("all controls passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trials", type=int, default=1_000_000)
    parser.add_argument("--output")
    parser.add_argument("--alphabet-size", type=int, default=4)
    parser.add_argument("--vector-radius", type=int, default=2)
    parser.add_argument("--controls", action="store_true")
    args = parser.parse_args()

    if args.controls:
        run_controls()
    else:
        if args.seed is None or not args.output:
            parser.error("--seed and --output are required for a search run")
        search_shard(
            seed=args.seed,
            trials=args.trials,
            output=args.output,
            alphabet_size=args.alphabet_size,
            vector_radius=args.vector_radius,
        )
