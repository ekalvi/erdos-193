"""
First-divergence stratification of nu_3(Omega) (expert-review recommendation D).

For each sampled triple of final-level points, find r = the deepest level at
which all three share an ancestor (via provenance parent chains). Report the
nu_3(Omega) envelope per divergence depth (final_level - r) and per split type
(two points diverge together vs all three separate), instead of per Euclidean
diameter. A linear-with-bounded-corrections envelope is the signature that a
finite arithmetic certificate can exist.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from random import Random

from search193 import candidate_step_vectors, cross, sub
from imbricate_seam import walk_points


def v3(n: int) -> int:
    v = 0
    while n % 3 == 0:
        n //= 3
        v += 1
    return v


def main():
    word = ast.literal_eval(open("amplified-193-8292.txt").read())
    prov = json.load(open("provenance-8292.json"))
    parents = prov["parents"]  # parents[L][j]: level L+1 point j -> level L index
    n_levels = len(parents)
    menu = candidate_step_vectors(2)
    points = walk_points(word, menu)
    n = len(points)

    # ancestor chains: anc[j] = [level0_idx, ..., levelN_idx(=j)]
    anc = []
    for j in range(n):
        chain = [j]
        for L in range(n_levels - 1, -1, -1):
            chain.append(parents[L][chain[-1]])
        chain.reverse()
        anc.append(chain)

    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 800_000
    rng = Random(31)
    env = defaultdict(lambda: defaultdict(int))  # (depth, type) -> {v3: count}

    for _ in range(samples):
        i, j, k = rng.randrange(n), rng.randrange(n), rng.randrange(n)
        if i == j or j == k or i == k:
            continue
        a, b, c = anc[i], anc[j], anc[k]
        r = -1
        for L in range(n_levels + 1):
            if a[L] == b[L] == c[L]:
                r = L
            else:
                break
        depth = n_levels - r  # how many levels since common ancestry
        if r < n_levels:
            trio = {a[r + 1], b[r + 1], c[r + 1]}
            split = "3-way" if len(trio) == 3 else "2-way"
        else:
            split = "same"
        u = sub(points[j], points[i])
        v = sub(points[k], points[i])
        om = cross(u, v)
        c_om = min(v3(abs(x)) for x in om if x != 0)
        c_u = min(v3(abs(x)) for x in u if x != 0)
        c_v = min(v3(abs(x)) for x in v if x != 0)
        kappa = c_om - c_u - c_v  # cancellation defect kappa_3 = c3(U x V)
        env[(depth, split)][kappa] += 1

    print(f"{'depth':>6} {'split':>6} {'triples':>9} {'max kappa':>10}  kappa distribution")
    for (depth, split) in sorted(env):
        cnt = env[(depth, split)]
        total = sum(cnt.values())
        dist = " ".join(f"{v}:{cnt[v]}" for v in sorted(cnt))
        print(f"{depth:>6} {split:>6} {total:>9} {max(cnt):>10}  {dist}")


if __name__ == "__main__":
    main()
