"""
Standalone third-party verifier for an amplified walk file (recommendation E).

Usage: python3 verify_walk.py amplified-193-8292.txt

Checks, with no dependency on the constructor:
  1. every step index selects a vector from the declared menu (radius-2 ball);
  2. no vertex repeats;
  3. no three vertices are collinear (exact integer cross products, via the
     O(n^2) direction-hashing method: for each vertex, the primitive
     directions to all earlier vertices must be pairwise distinct);
  4. prints the SHA-256 of the step sequence and of the vertex sequence,
     walk length, and maximum coordinate magnitude.

The direction-hashing method is sound and complete: three points p_i, p_j,
p_k (i<j<k) are collinear iff, from p_k, the directions to p_i and p_j
coincide as unoriented primitive integer vectors.
"""
from __future__ import annotations

import ast
import hashlib
import sys
from itertools import product
from math import gcd

MENU = [v for v in product((-2, -1, 0, 1, 2), repeat=3) if v != (0, 0, 0)]


def main(path: str) -> None:
    word = ast.literal_eval(open(path).read())
    assert all(0 <= s < len(MENU) for s in word), "step index outside menu"

    points = [(0, 0, 0)]
    for s in word:
        v = MENU[s]
        p = points[-1]
        points.append((p[0] + v[0], p[1] + v[1], p[2] + v[2]))

    assert len(set(points)) == len(points), "repeated vertex"

    for k in range(len(points)):
        px, py, pz = points[k]
        seen = set()
        for i in range(k):
            vx, vy, vz = points[i][0] - px, points[i][1] - py, points[i][2] - pz
            g = gcd(gcd(abs(vx), abs(vy)), abs(vz))
            w = (vx // g, vy // g, vz // g)
            for c in w:
                if c:
                    if c < 0:
                        w = (-w[0], -w[1], -w[2])
                    break
            assert w not in seen, f"collinear triple involving vertex {k}"
            seen.add(w)

    step_sha = hashlib.sha256(",".join(map(str, word)).encode()).hexdigest()
    vert_sha = hashlib.sha256(
        ";".join(f"{x},{y},{z}" for x, y, z in points).encode()
    ).hexdigest()
    max_coord = max(abs(c) for p in points for c in p)
    print(f"VERIFIED: {len(word)} steps, {len(points)} vertices, no repeated "
          f"vertex, no 3 collinear")
    print(f"max |coordinate|: {max_coord}")
    print(f"sha256(steps):    {step_sha}")
    print(f"sha256(vertices): {vert_sha}")


if __name__ == "__main__":
    main(sys.argv[1])
