"""
Dependency-structure measurement for the Stage-4 viability game / LLL route.

One stitch choice perturbs every chord with an endpoint among its segment's
points. The worry (agent round 5, section 9) is that one stitch touches too
many simultaneous unresolved constraints. Shallow agreements (j=1) are dense
(~10% of triples) so their count per stitch grows with the walk — but they
separate under ~92% of routings and need no coordination. The constraints
that could require coordination are the DEEP ones. This measures, per
final-level segment of the verified walk: how many sampled unresolved triples
at depth j>=2 / j>=3 touch it, scaled to census totals.

Output: distribution of per-segment touching-constraint counts by depth —
the dependency degrees an LLL/game formalization must handle.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from random import Random

from search193 import candidate_step_vectors, cross, sub
from imbricate_seam import walk_points
from router_synthesis import agreement_depth


def main(samples=4_000_000):
    word = ast.literal_eval(open("amplified-193-8292.txt").read())
    points = walk_points(word, candidate_step_vectors(2))
    prov = json.load(open("provenance-8292.json"))
    parents = prov["parents"][-1]  # final-level point -> previous-level parent
    n = len(points)

    # segment id of a final-level point = its parent index (points created
    # in the stitch between prev anchors i and i+1 have parent i or i+1;
    # grouping by parent approximates the per-stitch decision unit)
    seg_of = parents
    n_segments = max(parents) + 1

    rng = Random(53)
    touch = {2: defaultdict(int), 3: defaultdict(int)}
    counts = defaultdict(int)
    for _ in range(samples):
        x, y, z = rng.randrange(n), rng.randrange(n), rng.randrange(n)
        if len({x, y, z}) < 3:
            continue
        u = sub(points[y], points[x])
        v = sub(points[z], points[x])
        j = agreement_depth(u, v)
        counts[j] += 1
        for depth in (2, 3):
            if j >= depth:
                for p in (x, y, z):
                    touch[depth][seg_of[p]] += 1

    total = sum(counts.values())
    print(f"sampled {total} triples; depth histogram: {dict(sorted(counts.items()))}")
    scale = (n * (n - 1) * (n - 2)) / max(1, total)  # sample -> full-walk factor
    for depth in (2, 3):
        per_seg = touch[depth]
        if not per_seg:
            print(f"j>={depth}: no touches sampled")
            continue
        values = sorted(per_seg.values())
        est_max = values[-1] * scale
        est_med = values[len(values) // 2] * scale
        print(
            f"j>={depth}: segments touched {len(per_seg)}/{n_segments}; "
            f"per-segment touching constraints (scaled to full walk): "
            f"median ~{est_med:.0f}, max ~{est_max:.0f}"
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4_000_000)
