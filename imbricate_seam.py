"""
Seam-aware imbricated construction for Problem #193.

Upgrade over imbricate193.py: tiles are not accepted greedily. For each
letter we fabricate a POOL of distinct candidate tiles (same displacement
M.s, different shapes), precompute a seam-compatibility matrix (tile_a
followed by tile_b must be jointly triple-free as a walk), then backtrack
over one-tile-per-letter assignments requiring EVERY ordered letter pair
(a,b) — including a==b — to be seam-safe. Only assignments passing all
seam checks are evaluated on the full fixed-point walk.

Also reports a clearance diagnostic for the best candidate: the minimum
distance from any walk point to the line through any two other points, at
successive prefix scales. Growing clearance across levels is the signature
the finite-certificate argument needs.
"""
from __future__ import annotations

import sys
from itertools import combinations
from random import Random

from search193 import fixed_point_prefix, prefix_points, sub, cross, dot
from erdos193 import first_disqualifier
from imbricate193 import (
    M_IRRATIONAL,
    M_PERIODIC,
    apply,
    find_tile,
    random_menu,
)


def tile_pool(steps, target, maxlen, pool_size, attempts, rng, first=None):
    tiles = []
    seen = set()
    for _ in range(attempts):
        t = find_tile(steps, target, maxlen, first=first, rng=rng)
        if t is None:
            continue
        key = tuple(t)
        if key not in seen:
            seen.add(key)
            tiles.append(key)
            if len(tiles) >= pool_size:
                break
    return tiles


def walk_points(word, steps, start=(0, 0, 0)):
    points = [start]
    for si in word:
        s = steps[si]
        p = points[-1]
        points.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    return points


def seam_ok(tile_a, tile_b, steps):
    """Concatenated walk tile_a + tile_b must be triple-free."""
    return first_disqualifier(walk_points(list(tile_a) + list(tile_b), steps)) is None


def tile_clearance(tile, steps):
    """Minimum point-to-line clearance (squared) among the tile's own points.
    Higher-clearance tiles are geometrically 'curled' and seam better."""
    pts = walk_points(tile, steps)
    best = None
    for (i, p), (j, q) in combinations(enumerate(pts), 2):
        pq = sub(q, p)
        pq2 = dot(pq, pq)
        for k, r in enumerate(pts):
            if k in (i, j):
                continue
            c = cross(pq, sub(r, p))
            d2 = dot(c, c) / pq2
            if best is None or d2 < best:
                best = d2
    return best if best is not None else 0.0


def occurring_pairs(sigma, start=0):
    """
    Adjacent letter pairs occurring in the fixed point of sigma, computed as
    a closure: internal pairs of images of reachable letters, plus boundary
    pairs (last of sigma[x], first of sigma[y]) for each occurring pair (x,y).
    NOTE: a pair (a, a) in the closure is fatal — adjacent identical tiles
    give collinear anchors 0, D, 2D unconditionally.
    """
    letters = {start}
    while True:
        new = set(letters)
        for a in letters:
            new.update(sigma[a])
        if new == letters:
            break
        letters = new

    pairs = set()
    for a in letters:
        img = sigma[a]
        for x, y in zip(img, img[1:]):
            pairs.add((x, y))
    while True:
        boundary = {
            (sigma[x][-1], sigma[y][0]) for (x, y) in pairs
        }
        new = pairs | boundary
        if new == pairs:
            break
        pairs = new
    return pairs


def find_assignment(pools, steps, rng, samples=300):
    """
    One tile per letter such that every letter pair actually occurring in
    the resulting substitution's fixed point is seam-safe. The occurring-pair
    set depends on the assignment itself, so we sample assignments (biased
    toward high-clearance tiles) and verify the closure per sample.
    """
    n = len(pools)
    ranked = [
        sorted(pool, key=lambda t: -tile_clearance(t, steps))
        for pool in pools
    ]
    cache = {}

    def ok(ta, tb):
        key = (ta, tb)
        if key not in cache:
            cache[key] = seam_ok(ta, tb, steps)
        return cache[key]

    for attempt in range(samples):
        if attempt == 0:
            assignment = [pool[0] for pool in ranked]
        else:
            assignment = [
                pool[min(int(rng.expovariate(1.0)), len(pool) - 1)]
                for pool in ranked
            ]
        sigma = {i: t for i, t in enumerate(assignment)}
        pairs = occurring_pairs(sigma)
        if any(a == b for a, b in pairs):
            continue
        if all(ok(assignment[a], assignment[b]) for a, b in pairs):
            return list(assignment)
    return None


def evaluate_sigma(sigma, steps, prefix_length=50000):
    word = fixed_point_prefix(sigma, 0, prefix_length)
    points = prefix_points(word, {i: s for i, s in enumerate(steps)})
    dq = first_disqualifier(points)
    if dq is None:
        return len(word), None
    k = dq.k if hasattr(dq, "k") else dq.second
    return k - 1, dq


def clearance_profile(word, steps, scales=(20, 40, 80, 160, 320)):
    """
    Minimum point-to-line clearance among the first n points, for growing n.
    Clearance of point r from line through p,q = |PQ x PR| / |PQ|.
    Reported squared-normalized to stay exact-ish: min over triples of
    |PQ x PR|^2 / |PQ|^2 (squared distance).
    """
    points = walk_points(word[: max(scales)], steps)
    out = []
    for n in scales:
        pts = points[: n + 1]
        if len(pts) < 3:
            continue
        best = None
        for (i, p), (j, q) in combinations(enumerate(pts), 2):
            pq = sub(q, p)
            pq2 = dot(pq, pq)
            for k, r in enumerate(pts):
                if k == i or k == j:
                    continue
                c = cross(pq, sub(r, p))
                d2 = dot(c, c) / pq2
                if best is None or d2 < best:
                    best = d2
        out.append((n, round(best ** 0.5, 3)))
    return out


def search(trials, seed=193):
    rng = Random(seed)
    matrices = {"periodic(M^3=2I)": M_PERIODIC, "irrational-rot": M_IRRATIONAL}
    best = {name: (0, None, None) for name in matrices}

    for trial in range(trials):
        size = rng.choice((5, 6, 7))
        menu = random_menu(rng, size)
        if menu is None:
            continue
        for name, M in matrices.items():
            maxlen = 16 if name == "irrational-rot" else 12
            pools = []
            complete = True
            for i, s in enumerate(menu):
                pool = tile_pool(
                    menu,
                    apply(M, s),
                    maxlen,
                    pool_size=8,
                    attempts=24,
                    rng=rng,
                    first=0 if i == 0 else None,
                )
                if not pool:
                    complete = False
                    break
                pools.append(pool)
            if not complete:
                continue

            assignment = find_assignment(pools, menu, rng)
            if assignment is None:
                continue

            sigma = {i: t for i, t in enumerate(assignment)}
            score, dq = evaluate_sigma(sigma, menu)
            if score > best[name][0]:
                best[name] = (score, menu, sigma)
                print(
                    f"trial={trial} {name}: NEW BEST safe prefix={score} "
                    f"menu={menu} sigma={sigma}",
                    flush=True,
                )
        if trial % 50 == 0:
            print(
                f"trial={trial} bests: "
                + ", ".join(f"{n}={b[0]}" for n, b in best.items()),
                flush=True,
            )

    print("FINAL", {n: b[0] for n, b in best.items()}, flush=True)
    for name, (score, menu, sigma) in best.items():
        print(f"\n{name}: best={score}\n  menu={menu}\n  sigma={sigma}")
        if sigma:
            word = fixed_point_prefix(sigma, 0, 400)
            print("  clearance profile:", clearance_profile(word, menu))
    return best


if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    search(trials)
