"""
3-adic valuation structure of triple determinants in an amplified walk.

The proposed arithmetic certificate needs: v_3(det(q-p, r-p)) bounded by a
function of the triple's scale band. The modulus-3 matrix multiplies anchor
determinants by det(M) = 27 per level (v_3 += 3), so IF stitches contribute
bounded valuation, triples in scale band k should show v_3 <= 3k + O(1).
This samples triples, buckets by diameter in powers of 3 (the natural grading
for |lambda| = 3), and reports the v_3 distribution per band.
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from random import Random

from search193 import candidate_step_vectors, cross, dot, sub
from imbricate_seam import walk_points


def v3(n: int) -> int:
    if n == 0:
        return 99  # sentinel: infinite valuation (never happens: verified walks)
    v = 0
    while n % 3 == 0:
        n //= 3
        v += 1
    return v


def band(d: int) -> int:
    """Scale band k: 3^k <= d < 3^(k+1)."""
    k = 0
    while d >= 3 ** (k + 1):
        k += 1
    return k


if __name__ == "__main__":
    path = sys.argv[1]
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 600_000
    word = ast.literal_eval(open(path).read())
    menu = candidate_step_vectors(2)
    points = walk_points(word, menu)
    n = len(points)
    print(f"{path}: {n} points, {samples} sampled triples")

    rng = Random(23)
    bands: dict[int, Counter] = {}
    for _ in range(samples):
        i, j, k = rng.randrange(n), rng.randrange(n), rng.randrange(n)
        if i == j or j == k or i == k:
            continue
        p, q, r = points[i], points[j], points[k]
        # det of the 3x3 built from two difference vectors and their cross —
        # for collinearity in Z^3 the invariant is the cross product vector;
        # use v_3 of its gcd-like content: min over nonzero components is the
        # right "how divisible by 3" measure of near-degeneracy.
        c = cross(sub(q, p), sub(r, p))
        val = min(v3(abs(x)) for x in c if x != 0) if c != (0, 0, 0) else 99
        d = max(
            max(abs(p[t] - q[t]), abs(p[t] - r[t]), abs(q[t] - r[t]))
            for t in range(3)
        )
        bands.setdefault(band(d), Counter())[val] += 1

    print(f"{'band':>5} {'diam range':>16} {'triples':>9} {'max v3':>7}  v3 distribution (v: count)")
    for k in sorted(bands):
        c = bands[k]
        total = sum(c.values())
        mx = max(c)
        dist = " ".join(f"{v}:{c[v]}" for v in sorted(c))
        print(f"{k:>5} [{3**k:>6},{3**(k+1):>6}) {total:>9} {mx:>7}  {dist}")
