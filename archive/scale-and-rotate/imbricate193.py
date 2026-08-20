"""
Imbricated (multi-scale, self-similar) walk construction for Problem #193.

Idea: choose an expanding integer matrix M whose eigenvalues all have equal
modulus, with an irrational rotation component. For each step s in a finite
menu S, fabricate a "tile": a short triple-free walk from 0 to M.s using
steps of S. The substitution s -> tile(s) then generates a self-similar walk
whose level-(n+1) anchor skeleton is M times the level-n walk.

Why this evades the Perron-Frobenius no-go proven for abelian substitutions:
the displacement dynamics is literally M, whose spectrum has equal moduli, so
block displacements ROTATE through scales instead of collapsing onto a single
Perron direction, and (for irrational rotation) blocks at different scales
are never parallel.

M preserves collinearity, so level-n triple-freeness is inherited by the
level-(n+1) anchors; only new intra-tile points can create new triples.
This program fabricates tiles and measures how far the fixed-point walk
actually stays triple-free, compared with the ~27-46 ceilings of random
abelian substitutions.
"""
from __future__ import annotations

import sys
from itertools import combinations, product
from random import Random

from search193 import cross, fixed_point_prefix, prefix_points, sub
from erdos193 import first_disqualifier
from bnb193 import legal

# --- expansion matrices -----------------------------------------------------

# M3 = 2I: eigenvalues are the cube roots of 2 (all modulus 2^(1/3)),
# direction action periodic with period 3.
M_PERIODIC = ((0, 0, 2), (1, 0, 0), (0, 1, 0))

# Block diag(2, C) with C the companion of x^2 + x + 4: complex pair of
# modulus exactly 2, rotation angle cos(theta) = -1/4 (irrational angle).
M_IRRATIONAL = ((2, 0, 0), (0, 0, -4), (0, 1, -1))


def apply(M, v):
    return (
        M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
        M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
        M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2],
    )


# --- tile fabrication --------------------------------------------------------

def solution_multisets(steps, target, maxlen, node_budget=150_000, max_solutions=400):
    """
    Coefficient vectors c >= 0 with sum(c) <= maxlen and
    sum c_i * steps[i] = target, sorted by total length. Enumeration is
    capped: pathological menus otherwise explode combinatorially.
    """
    n = len(steps)
    out = []
    nodes = [0]

    def rec(i, remaining, residual, c):
        nodes[0] += 1
        if nodes[0] > node_budget or len(out) >= max_solutions:
            return
        if i == n:
            if residual == (0, 0, 0) and sum(c) > 0:
                out.append(tuple(c))
            return
        # Prune: remaining steps must be able to cancel the residual.
        max_step = max(
            max(abs(s[j]) for s in steps[i:]) for j in range(3)
        )
        if max(abs(r) for r in residual) > remaining * max_step:
            return
        for k in range(remaining + 1):
            c.append(k)
            rec(
                i + 1,
                remaining - k,
                (
                    residual[0] - k * steps[i][0],
                    residual[1] - k * steps[i][1],
                    residual[2] - k * steps[i][2],
                ),
                c,
            )
            c.pop()

    rec(0, maxlen, target, [])
    return sorted(set(out), key=sum)


def find_tile(steps, target, maxlen, first=None, rng=None):
    """
    Triple-free walk 0 -> target using the step menu, as a word of step
    indices. Solves the abelian (multiset) equation first, then searches for
    a triple-free ordering of each solution multiset. With rng, both the
    multiset choice (among near-shortest) and the ordering are randomized so
    repeated calls sample different tiles.
    """
    multisets = solution_multisets(steps, target, maxlen)
    if rng is not None and multisets:
        shortest = sum(multisets[0])
        near = [c for c in multisets if sum(c) <= shortest + 2]
        rng.shuffle(near)
        multisets = near + multisets[len(near):]

    for counts in multisets:
        if first is not None and counts[first] == 0:
            continue
        remaining = list(counts)

        def order(points, point_set, word):
            if not any(remaining):
                return list(word)
            last = points[-1]
            indices = list(range(len(steps)))
            if rng is not None:
                rng.shuffle(indices)
            for si in indices:
                if remaining[si] == 0:
                    continue
                if not word and first is not None and si != first:
                    continue
                s = steps[si]
                p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
                if legal(points, point_set, p):
                    remaining[si] -= 1
                    points.append(p)
                    point_set.add(p)
                    word.append(si)
                    found = order(points, point_set, word)
                    if found is not None:
                        return found
                    word.pop()
                    point_set.discard(points.pop())
                    remaining[si] += 1
            return None

        found = order([(0, 0, 0)], {(0, 0, 0)}, [])
        if found is not None:
            return found
    return None


def build_substitution(M, steps, maxlen=12, rng=None):
    """sigma[i] = tile word realizing displacement M.steps[i]; prolongable on 0."""
    sigma = {}
    for i, s in enumerate(steps):
        first = 0 if i == 0 else None
        tile = find_tile(steps, apply(M, s), maxlen, first=first, rng=rng)
        if tile is None:
            return None
        sigma[i] = tuple(tile)
    if sigma[0][0] != 0:
        return None
    return sigma


# --- step menu generation ----------------------------------------------------

def pairwise_nonparallel(steps):
    return all(
        cross(a, b) != (0, 0, 0) for a, b in combinations(steps, 2)
    )


def positively_spans(steps):
    """Approximate test that cone(steps) = R^3: every probe direction has a
    step with positive dot product."""
    probes = [p for p in product((-1, 0, 1), repeat=3) if p != (0, 0, 0)]
    return all(
        any(sum(s[i] * d[i] for i in range(3)) > 0 for s in steps)
        for d in probes
    )


def random_menu(rng, size, radius=2):
    vectors = [
        v for v in product(range(-radius, radius + 1), repeat=3)
        if v != (0, 0, 0)
    ]
    for _ in range(200):
        menu = rng.sample(vectors, size)
        if pairwise_nonparallel(menu) and positively_spans(menu):
            return menu
    return None


# --- experiment ---------------------------------------------------------------

def evaluate(M, steps, prefix_length=20000, maxlen=12, rng=None):
    sigma = build_substitution(M, steps, maxlen=maxlen, rng=rng)
    if sigma is None:
        return None
    word = fixed_point_prefix(sigma, 0, prefix_length)
    if len(word) < 2 * max(len(t) for t in sigma.values()):
        return None
    points = prefix_points(word, {i: s for i, s in enumerate(steps)})
    dq = first_disqualifier(points)
    if dq is None:
        score = len(word)
    else:
        score = (dq.k if hasattr(dq, "k") else dq.second) - 1
    return score, sigma, dq, len(word)


if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    rng = Random(193)
    matrices = {"periodic(M^3=2I)": M_PERIODIC, "irrational-rot": M_IRRATIONAL}
    best = {name: (0, None, None) for name in matrices}

    RETRIES = 8

    for trial in range(trials):
        size = rng.choice((5, 6, 7))
        menu = random_menu(rng, size)
        if menu is None:
            continue
        for name, M in matrices.items():
            maxlen = 16 if name == "irrational-rot" else 12
            for _ in range(RETRIES):
                result = evaluate(M, menu, maxlen=maxlen, rng=rng)
                if result is None:
                    break
                score, sigma, dq, wordlen = result
                if score > best[name][0]:
                    best[name] = (score, menu, sigma)
                    print(
                        f"trial={trial} {name}: NEW BEST safe prefix={score} "
                        f"(word len {wordlen}) menu={menu} sigma={sigma}",
                        flush=True,
                    )
        if trial % 200 == 0:
            print(
                f"trial={trial} bests: "
                + ", ".join(f"{n}={b[0]}" for n, b in best.items()),
                flush=True,
            )

    print("FINAL", {n: b[0] for n, b in best.items()}, flush=True)
    for name, (score, menu, sigma) in best.items():
        print(f"{name}: best={score} menu={menu} sigma={sigma}")
