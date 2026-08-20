"""
EXACT maximum cancellation defect kappa_3 over all triples of the walk
(strategy-agent recommendation, feedback round 4, section 7).

kappa_3(u, v) = c_3(U x V) where U, V are the 3-primitive parts of the two
chords from a common anchor x. Two chords have kappa_3 >= q iff their
primitive parts lie in the same projective class of P^2(Z/3^q) — so per
anchor we bucket chords by canonical projective signature mod 3, then
iteratively refine only colliding buckets at q+1. No-three-collinear
guarantees all chords from x have distinct rational projective directions,
so refinement terminates.

Outputs: exact global max kappa_3, per-q collision counts, extremal triples,
and the pigeonhole lower bound for comparison.
"""
from __future__ import annotations

import ast
import sys
from collections import defaultdict

from search193 import candidate_step_vectors
from imbricate_seam import walk_points


def strip3(v):
    """(content, primitive part) of a nonzero integer vector."""
    c = 0
    x, y, z = v
    while x % 3 == 0 and y % 3 == 0 and z % 3 == 0:
        x //= 3
        y //= 3
        z //= 3
        c += 1
    return c, (x, y, z)


def signature(U, mod):
    """Canonical projective signature of primitive U modulo `mod` (=3^q):
    chart = first coordinate that is a 3-adic unit; normalize it to 1."""
    for chart in range(3):
        if U[chart] % 3 != 0:
            inv = pow(U[chart] % mod, -1, mod)
            return (
                chart,
                (U[0] * inv) % mod,
                (U[1] * inv) % mod,
                (U[2] * inv) % mod,
            )
    raise AssertionError("non-primitive vector")


def main(path, max_extremal=6):
    word = ast.literal_eval(open(path).read())
    menu = candidate_step_vectors(2)
    points = walk_points(word, menu)
    n = len(points)
    print(f"{path}: {n} points — exact kappa_3 via projective refinement")

    global_max = 0
    extremal = []
    collisions_per_q = defaultdict(int)

    for xi in range(n):
        px, py, pz = points[xi]
        prims = []
        for yi in range(n):
            if yi == xi:
                continue
            _, U = strip3((points[yi][0] - px, points[yi][1] - py, points[yi][2] - pz))
            prims.append((yi, U))

        # q=1 bucketing, then refine only collisions
        buckets = defaultdict(list)
        for yi, U in prims:
            buckets[signature(U, 3)].append((yi, U))
        q = 1
        live = [g for g in buckets.values() if len(g) > 1]
        while live:
            collisions_per_q[q] += sum(len(g) * (len(g) - 1) // 2 for g in live)
            if q > global_max:
                global_max = q
                extremal = [
                    (xi, [m[0] for m in g][:3]) for g in live
                ][:max_extremal]
            elif q == global_max and len(extremal) < max_extremal:
                extremal.extend((xi, [m[0] for m in g][:3]) for g in live)
            q += 1
            mod = 3 ** q
            nxt = []
            for g in live:
                sub = defaultdict(list)
                for yi, U in g:
                    sub[signature(U, mod)].append((yi, U))
                nxt.extend(gg for gg in sub.values() if len(gg) > 1)
            live = nxt
        if xi % 1000 == 0:
            print(f"  anchor {xi}/{n}, running max kappa={global_max}", flush=True)

    print(f"\nEXACT global max kappa_3 = {global_max}")
    import math
    lower = 0.5 * math.log(n - 1, 3) - 0.5 * math.log(13, 3) + 1  # 13*3^(2m-2) < N-1
    print(f"pigeonhole lower bound forces kappa_3 >= "
          f"{max(m for m in range(1, 20) if 13 * 3 ** (2 * m - 2) < n - 1)}")
    print("chord-pair collisions per q:",
          dict(sorted(collisions_per_q.items())))
    print("extremal (anchor, [chord endpoints]):", extremal[:max_extremal])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "amplified-193-8292.txt")
