from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from math import gcd
from random import Random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

Symbol = int
Vector = Tuple[int, int, int]
Substitution = Dict[Symbol, Tuple[Symbol, ...]]


# ------------------------------------------------------------
# Integer vector operations
# ------------------------------------------------------------

def add(a: Vector, b: Vector) -> Vector:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vector, b: Vector) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: Vector, b: Vector) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def det(a: Vector, b: Vector, c: Vector) -> int:
    return dot(a, cross(b, c))


def parallel(a: Vector, b: Vector) -> bool:
    return cross(a, b) == (0, 0, 0)


def primitive_direction(v: Vector) -> Vector:
    """
    Canonical representative of the unoriented rational direction of v.
    """
    if v == (0, 0, 0):
        return v

    g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    w = (v[0] // g, v[1] // g, v[2] // g)

    # Identify w and -w.
    for coordinate in w:
        if coordinate:
            if coordinate < 0:
                w = (-w[0], -w[1], -w[2])
            break

    return w


# ------------------------------------------------------------
# Words, substitutions, and walks
# ------------------------------------------------------------

def substitute(word: Sequence[Symbol],
               sigma: Substitution) -> List[Symbol]:
    out: List[Symbol] = []
    for a in word:
        out.extend(sigma[a])
    return out


def fixed_point_prefix(
    sigma: Substitution,
    seed: Symbol,
    target_length: int,
    max_iterations: int = 100,
) -> List[Symbol]:
    """
    Intended for a prolongable substitution: sigma[seed] starts with seed.
    """
    word = [seed]

    for _ in range(max_iterations):
        if len(word) >= target_length:
            return word[:target_length]

        new_word = substitute(word, sigma)

        if new_word == word:
            break

        word = new_word

    return word[:target_length]


def prefix_points(
    word: Sequence[Symbol],
    step: Dict[Symbol, Vector],
) -> List[Vector]:
    points: List[Vector] = [(0, 0, 0)]

    for a in word:
        points.append(add(points[-1], step[a]))

    return points


def block_displacement(
    word: Sequence[Symbol],
    step: Dict[Symbol, Vector],
) -> Vector:
    v = (0, 0, 0)

    for a in word:
        v = add(v, step[a])

    return v


# ------------------------------------------------------------
# Collinearity checking
# ------------------------------------------------------------

@dataclass(frozen=True)
class Collision:
    i: int
    j: int
    k: int
    point_i: Vector
    point_j: Vector
    point_k: Vector


def first_collinear_triple_slow(
    points: Sequence[Vector],
) -> Optional[Collision]:
    """
    O(n^3), useful as a verification oracle.
    """
    for i, j, k in combinations(range(len(points)), 3):
        u = sub(points[j], points[i])
        v = sub(points[k], points[j])

        if parallel(u, v):
            return Collision(
                i, j, k,
                points[i], points[j], points[k]
            )

    return None


def first_collinear_triple(
    points: Sequence[Vector],
) -> Optional[Collision]:
    """
    O(n^2) expected time.

    At each newest point p_k, group all earlier points by the
    unoriented rational direction from p_k. Two earlier points
    in the same direction class are collinear with p_k.
    """
    seen_points: Dict[Vector, int] = {}

    for k, p in enumerate(points):
        # Repeated vertices are tracked separately. A repeated point
        # should generally disqualify a candidate walk, although it is
        # not by itself a triple of distinct collinear points.
        if p in seen_points:
            return Collision(
                seen_points[p], seen_points[p], k,
                p, p, p
            )

        direction_owner: Dict[Vector, int] = {}

        for i in range(k):
            d = primitive_direction(sub(points[i], p))

            if d in direction_owner:
                j = direction_owner[d]
                return Collision(
                    j, i, k,
                    points[j], points[i], points[k]
                )

            direction_owner[d] = i

        seen_points[p] = k

    return None


def safe_prefix_length(
    word: Sequence[Symbol],
    step: Dict[Symbol, Vector],
) -> int:
    """
    Number of steps preceding the first detected collision.
    """
    points = prefix_points(word, step)
    collision = first_collinear_triple(points)

    if collision is None:
        return len(word)

    return collision.k - 1


# ------------------------------------------------------------
# Return words
# ------------------------------------------------------------

def occurrences(
    word: Sequence[Symbol],
    marker: Sequence[Symbol],
) -> List[int]:
    m = len(marker)

    return [
        i for i in range(len(word) - m + 1)
        if tuple(word[i:i + m]) == tuple(marker)
    ]


def return_words(
    word: Sequence[Symbol],
    marker: Sequence[Symbol],
) -> List[Tuple[Symbol, ...]]:
    """
    A return word begins at one occurrence of marker and ends
    immediately before the next occurrence.
    """
    starts = occurrences(word, marker)
    result = set()

    for a, b in zip(starts, starts[1:]):
        result.add(tuple(word[a:b]))

    return sorted(result, key=lambda w: (len(w), w))


def vector_rank(vectors: Iterable[Vector]) -> int:
    """
    Rank over Q, specialized to vectors in Q^3.
    """
    vectors = [v for v in vectors if v != (0, 0, 0)]

    if not vectors:
        return 0

    a = vectors[0]

    if all(parallel(a, b) for b in vectors[1:]):
        return 1

    b = next(b for b in vectors[1:] if not parallel(a, b))

    if all(det(a, b, c) == 0 for c in vectors):
        return 2

    return 3


@dataclass
class ReturnData:
    marker: Tuple[Symbol, ...]
    words: List[Tuple[Symbol, ...]]
    displacements: List[Vector]
    rank: int
    maximum_determinant: int


def analyse_marker(
    word: Sequence[Symbol],
    marker: Sequence[Symbol],
    step: Dict[Symbol, Vector],
) -> ReturnData:
    words = return_words(word, marker)
    displacements = [
        block_displacement(return_word, step)
        for return_word in words
    ]

    determinants = [
        abs(det(a, b, c))
        for a, b, c in combinations(displacements, 3)
    ]

    return ReturnData(
        marker=tuple(marker),
        words=words,
        displacements=displacements,
        rank=vector_rank(displacements),
        maximum_determinant=max(determinants, default=0),
    )


# ------------------------------------------------------------
# Primitive-substitution testing
# ------------------------------------------------------------

def is_primitive(
    sigma: Substitution,
    alphabet: Sequence[Symbol],
) -> bool:
    """
    For an m-letter alphabet, it suffices here to iterate supports
    until they stabilize. Primitivity means some common power sends
    every letter to a word containing every letter.
    """
    full = set(alphabet)
    supports = {a: set(sigma[a]) for a in alphabet}

    for _ in range(len(alphabet) ** 2 + 1):
        if all(supports[a] == full for a in alphabet):
            return True

        new_supports = {}

        for a in alphabet:
            expanded = set()
            for b in supports[a]:
                expanded.update(supports[b])
            new_supports[a] = expanded

        if new_supports == supports:
            break

        supports = new_supports

    return all(supports[a] == full for a in alphabet)


def random_prolongable_substitution(
    rng: Random,
    alphabet_size: int,
    minimum_image_length: int = 2,
    maximum_image_length: int = 4,
) -> Substitution:
    alphabet = list(range(alphabet_size))
    sigma: Substitution = {}

    for a in alphabet:
        length = rng.randint(
            minimum_image_length,
            maximum_image_length
        )
        sigma[a] = tuple(
            rng.randrange(alphabet_size)
            for _ in range(length)
        )

    # Make the substitution prolongable on 0.
    sigma[0] = (0,) + sigma[0][1:]

    return sigma


def candidate_step_vectors(
    radius: int = 1,
) -> List[Vector]:
    return [
        (x, y, z)
        for x, y, z in product(
            range(-radius, radius + 1),
            repeat=3
        )
        if (x, y, z) != (0, 0, 0)
    ]


@dataclass
class Candidate:
    score: int
    sigma: Substitution
    step: Dict[Symbol, Vector]
    collision: Optional[Collision]
    return_profiles: List[ReturnData]


def search(
    trials: int = 100_000,
    alphabet_size: int = 4,
    prefix_length: int = 1_000,
    vector_radius: int = 2,
    seed: int = 193,
    keep: int = 20,
) -> List[Candidate]:
    rng = Random(seed)
    alphabet = list(range(alphabet_size))
    vectors = candidate_step_vectors(vector_radius)
    best: List[Candidate] = []

    for trial in range(trials):
        sigma = random_prolongable_substitution(
            rng,
            alphabet_size
        )

        if not is_primitive(sigma, alphabet):
            continue

        chosen = rng.sample(vectors, alphabet_size)
        step = dict(zip(alphabet, chosen))

        # Require the individual step vectors to span R^3.
        if vector_rank(chosen) < 3:
            continue

        word = fixed_point_prefix(
            sigma,
            seed=0,
            target_length=prefix_length
        )

        if len(word) < prefix_length:
            continue

        points = prefix_points(word, step)
        collision = first_collinear_triple(points)

        score = (
            prefix_length
            if collision is None
            else collision.k - 1
        )

        # Return-word diagnostics for prefixes of lengths 1 through 6.
        profiles = []
        for marker_length in range(1, 7):
            marker = word[:marker_length]
            data = analyse_marker(word, marker, step)

            # Demand enough observed returns to make the statistic useful.
            if len(data.words) >= 2:
                profiles.append(data)

        candidate = Candidate(
            score=score,
            sigma=sigma,
            step=step,
            collision=collision,
            return_profiles=profiles,
        )

        best.append(candidate)
        best.sort(key=lambda c: c.score, reverse=True)
        del best[keep:]

        if trial % 1_000 == 0 and best:
            print(
                f"trial={trial:8d} "
                f"best safe prefix={best[0].score}"
            )

    return best


def print_candidate(candidate: Candidate) -> None:
    print("\nSafe prefix:", candidate.score)
    print("Substitution:")
    for a in sorted(candidate.sigma):
        image = "".join(map(str, candidate.sigma[a]))
        print(f"  {a} -> {image}")

    print("Step vectors:")
    for a in sorted(candidate.step):
        print(f"  {a} -> {candidate.step[a]}")

    print("First collision:", candidate.collision)

    print("Return-word profiles:")
    for data in candidate.return_profiles:
        marker = "".join(map(str, data.marker))
        print(
            f"  marker={marker!r}, "
            f"returns={len(data.words)}, "
            f"rank={data.rank}, "
            f"max |det|={data.maximum_determinant}"
        )


if __name__ == "__main__":
    results = search(
        trials=100_000,
        alphabet_size=4,
        prefix_length=1_000,
        vector_radius=2,
        seed=193,
        keep=20,
    )

    for candidate in results[:10]:
        print_candidate(candidate)
