"""
Stage 2-3 driver: transition census over realized unresolved chord pairs.

Samples chord pairs (u, v) from a common anchor of the verified 8,292-step
walk with agreement depth j0 >= 1 (genuinely unresolved at modulus 3), and
asks, for every possible next-level routing (Mu + d1, Mv + d2) over the exact
perturbation set Delta: what fraction separates (j'=0), decreases rank, stays,
or deepens? The ranked-automaton certificate needs separation/decrease to be
available essentially always; the Stage-4 viability game additionally needs
them to be simultaneously choosable across pairs (not tested here).
"""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from random import Random

from search193 import candidate_step_vectors, sub
from imbricate_seam import walk_points
from router_synthesis import (
    MENU,
    Q,
    agreement_depth,
    connectors,
    apply_M,
    delta_set,
    offset_collar,
    transition_census,
)


def main(samples=400):
    word = ast.literal_eval(open("amplified-193-8292.txt").read())
    points = walk_points(word, candidate_step_vectors(2))
    n = len(points)

    total_connectors = sum(len(connectors(apply_M(s))) for s in MENU)
    O = offset_collar()
    deltas = delta_set(O)
    print(f"menu {len(MENU)} steps; connectors total {total_connectors}; "
          f"collar |O|={len(O)}; exact |Delta|={len(deltas)}; Q={Q}")

    rng = Random(41)
    stats = defaultdict(lambda: {
        "pairs": 0, "sep_available": 0, "progress_available": 0,
        "sep_frac_sum": 0.0, "worst_sep_frac": 1.0, "worst_pair": None,
    })
    tried = 0
    kept = 0
    while kept < samples and tried < 500_000:
        tried += 1
        x, y, z = rng.randrange(n), rng.randrange(n), rng.randrange(n)
        if len({x, y, z}) < 3:
            continue
        u = sub(points[y], points[x])
        v = sub(points[z], points[x])
        j0 = agreement_depth(u, v)
        if j0 < 1 or j0 > Q:
            continue
        kept += 1
        j0c, counts = transition_census(u, v, deltas)
        total = sum(counts.values())
        s = stats[j0c]
        s["pairs"] += 1
        sep_frac = counts["separated"] / total
        s["sep_frac_sum"] += sep_frac
        if counts["separated"]:
            s["sep_available"] += 1
        if counts["separated"] or counts["down"]:
            s["progress_available"] += 1
        if sep_frac < s["worst_sep_frac"]:
            s["worst_sep_frac"] = sep_frac
            s["worst_pair"] = (points[x], points[y], points[z], counts)

    print(f"sampled {kept} unresolved pairs (from {tried} random triples)")
    for j0 in sorted(stats):
        s = stats[j0]
        print(f"\nj0={j0}: pairs={s['pairs']}")
        print(f"  separation available:    {s['sep_available']}/{s['pairs']}")
        print(f"  progress (sep or down):  {s['progress_available']}/{s['pairs']}")
        print(f"  mean separated fraction: {s['sep_frac_sum']/max(1,s['pairs']):.4f}")
        print(f"  worst separated fraction:{s['worst_sep_frac']:.4f}")
        if s["worst_pair"]:
            print(f"  worst-case counts: {s['worst_pair'][3]}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400)
