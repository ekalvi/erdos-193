"""
Anchor-guided amplification with a RICH menu: all radius-2 vectors (124
steps) under the balanced modulus-2 irrational-rotation matrix M_BAL.
The maximal-closed-set computation shows every M.s decomposes into 2-3 menu
steps, so stitches are short; walk length grows ~2-3x per level while volume
grows |det M| = 8x, so density falls with depth.
"""
from __future__ import annotations

import sys
from random import Random

from erdos193 import first_disqualifier
from search193 import candidate_step_vectors
from design_menu import M_BAL

# Modulus-3 sibling: diag(3, companion-balanced of x^2+x+9); all eigenvalue
# moduli 3, irrational rotation (cos t = -1/6). Volume x27 per level.
M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
from amplify193 import amplify_level, find_base
from imbricate_seam import walk_points


def measure_density(word, steps):
    pts = walk_points(word, steps)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    vol = max(
        1,
        (max(xs) - min(xs)) * (max(ys) - min(ys)) * (max(zs) - min(zs)),
    )
    return len(pts) / vol


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 193
    base_len = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
    modulus = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    route = sys.argv[5] if len(sys.argv) > 5 else "short"
    M = M_BAL if modulus == 2 else M_BAL3
    seg_maxlen = (8 if modulus == 2 else 12) + (4 if route == "wiggle" else 0)

    rng = Random(seed)
    menu = candidate_step_vectors(2)  # all 124 radius-2 vectors
    base = find_base(menu, rng, length=base_len, tries=200)
    print(f"base: length {len(base)} (matrix modulus {modulus}, route {route})", flush=True)

    word = base
    level = 0
    while len(word) <= cap:
        level += 1
        new = amplify_level(
            word, menu, M, rng, seg_maxlen=seg_maxlen, seg_tries=8, restarts=6,
            route=route,
        )
        if new is None:
            print(f"level {level}: FAILED", flush=True)
            break
        word = new
        pts = walk_points(word, menu)
        assert first_disqualifier(pts) is None
        print(
            f"level {level}: length {len(word)} VERIFIED triple-free, "
            f"density {measure_density(word, menu):.5f}",
            flush=True,
        )
    print(f"final length: {len(word)}", flush=True)
    with open(f"amplified-{seed}-{len(word)}.txt", "w") as f:
        f.write(repr(word))
