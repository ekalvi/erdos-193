"""
Design step menus closed under short M-decomposition: for every s in S,
M.s must be a sum of 2-3 members of S (not all parallel). Short stitches
mean the amplified walk grows 2-3x per level while volume grows |det M| = 8x,
so point density falls and stitching gets easier with depth.

M_BAL = diag(2, [[0,-2],[2,-1]]): same spectrum as M_IRRATIONAL (real 2 and
complex pair of modulus 2 with irrational rotation cos t = -1/4) but with
balanced entries so images stay near the search radius.
"""
from __future__ import annotations

import sys
from itertools import product
from random import Random

from search193 import cross

M_BAL = ((2, 0, 0), (0, 0, -2), (0, 2, -1))


def apply(M, v):
    return (
        M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
        M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
        M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2],
    )


def decompositions(target, members, vset, max_parts=3):
    """Ways to write target as a sum of 2 or 3 distinct-ish members of vset,
    at least two parts non-parallel."""
    out = []
    mem = list(members)
    for a in mem:
        b = (target[0] - a[0], target[1] - a[1], target[2] - a[2])
        if b in vset and b != a and cross(a, b) != (0, 0, 0):
            out.append((a, b))
    if max_parts >= 3:
        for a in mem:
            r = (target[0] - a[0], target[1] - a[1], target[2] - a[2])
            for b in mem:
                c = (r[0] - b[0], r[1] - b[1], r[2] - b[2])
                if c in vset and (
                    cross(a, b) != (0, 0, 0)
                    or cross(b, c) != (0, 0, 0)
                ):
                    out.append((a, b, c))
    return out


def closed_menus(M, radius, attempts, rng, max_size=9):
    vecs = [
        v
        for v in product(range(-radius, radius + 1), repeat=3)
        if v != (0, 0, 0)
    ]
    vset = set(vecs)
    found = []
    for attempt in range(attempts):
        S = set(rng.sample(vecs, 2))
        dead = False
        for _ in range(40):
            missing = [
                s for s in S if not decompositions(apply(M, s), S, S)
            ]
            if not missing:
                break
            s = missing[0]
            t = apply(M, s)
            cands = decompositions(t, vecs, vset)
            cands = [d for d in cands if all(abs(c) <= radius for p in d for c in p)]
            if not cands:
                dead = True
                break
            cands.sort(key=lambda d: -sum(p in S for p in d))
            pick = cands[0] if rng.random() < 0.7 else rng.choice(cands[: 8])
            S.update(pick)
            if len(S) > max_size:
                dead = True
                break
        if dead:
            continue
        if all(decompositions(apply(M, s), S, S) for s in S):
            menu = tuple(sorted(S))
            if menu not in [f[1] for f in found]:
                found.append((len(menu), menu))
                print(f"attempt {attempt}: closed menu size {len(menu)}: {list(menu)}", flush=True)
    found.sort()
    return found


if __name__ == "__main__":
    attempts = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    rng = Random(193)
    found = closed_menus(M_BAL, radius=3, attempts=attempts, rng=rng)
    print(f"total distinct closed menus: {len(found)}")
    for size, menu in found[:5]:
        print(size, list(menu))
