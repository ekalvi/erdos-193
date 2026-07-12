"""
Clearance spectrum of a verified triple-free walk.

For a finite-certificate argument the walk must be in 'general position at
all scales': every triple of points spanning diameter ~d should miss
collinearity by a margin growing with d. This samples random triples,
buckets them by diameter (max pairwise Chebyshev distance), and reports the
minimum triangle height per bucket.

  height = 2 * Area / longest side  (exact integer cross product, then sqrt)

Certificate-friendly signature: min height per bucket grows ~linearly with
bucket scale. Fatal signature: min height flat (or shrinking) as scale grows
— then far-apart triples get arbitrarily close to collinear and the
construction is living on luck.
"""
from __future__ import annotations

import ast
import sys
from math import sqrt
from random import Random

from search193 import candidate_step_vectors, cross, dot, sub
from imbricate_seam import walk_points


def triple_height(p, q, r):
    a = sub(q, p)
    b = sub(r, p)
    c = cross(a, b)
    area2 = sqrt(dot(c, c))  # = 2 * triangle area
    if area2 == 0:
        return 0.0
    side = max(
        sqrt(dot(a, a)),
        sqrt(dot(b, b)),
        sqrt(dot(sub(r, q), sub(r, q))),
    )
    return area2 / side


def diameter(p, q, r):
    return max(
        max(abs(p[i] - q[i]), abs(p[i] - r[i]), abs(q[i] - r[i]))
        for i in range(3)
    )


def spectrum(points, samples, rng):
    buckets = {}
    n = len(points)
    for _ in range(samples):
        i = rng.randrange(n)
        j = rng.randrange(n)
        k = rng.randrange(n)
        if i == j or j == k or i == k:
            continue
        p, q, r = points[i], points[j], points[k]
        d = diameter(p, q, r)
        b = d.bit_length()  # bucket = [2^(b-1), 2^b)
        h = triple_height(p, q, r)
        cur = buckets.get(b)
        if cur is None or h < cur[0]:
            buckets[b] = (h, d, (i, j, k))
    return buckets


if __name__ == "__main__":
    path = sys.argv[1]
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 500_000
    with open(path) as f:
        word = ast.literal_eval(f.read())
    menu = candidate_step_vectors(2)
    points = walk_points(word, menu)
    print(f"{path}: {len(points)} points, sampling {samples} triples")
    rng = Random(17)
    buckets = spectrum(points, samples, rng)
    print(f"{'scale bucket':>16} {'min height':>12} {'at diameter':>12}")
    for b in sorted(buckets):
        h, d, _ = buckets[b]
        print(f"[{2**(b-1):5d},{2**b:5d}) {h:12.3f} {d:12d}")
