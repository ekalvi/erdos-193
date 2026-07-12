"""
Randomized probes of the longest triple-free walk for fixed step menus,
to test whether the DFS record (224 on the 'good' 4-step menu) reflects a
real ceiling or just depth-first ordering bias.

Two independent methods per menu:
  1. Beam search: keep a population of B partial walks; at each level extend
     every walk by every legal step, then randomly downsample to B survivors.
     Random sampling (not scoring) avoids the lexicographic bias of DFS.
  2. Randomized-restart DFS: many short DFS runs, each with independently
     shuffled step order at every node.

Legality is the same exact-integer predicate as everywhere else: a new point
is illegal if it repeats an earlier point or is collinear with two of them.
"""
from __future__ import annotations

import sys
from random import Random

from bnb193 import legal


def legal_children(points, point_set, steps):
    out = []
    last = points[-1]
    for s in steps:
        p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
        if legal(points, point_set, p):
            out.append(p)
    return out


def beam_search(steps, rng, beam_width=200, depth_cap=3000):
    beams = [([(0, 0, 0)], {(0, 0, 0)})]
    depth = 0
    while beams and depth < depth_cap:
        children = []
        for points, point_set in beams:
            for p in legal_children(points, point_set, steps):
                children.append((points, point_set, p))
        if not children:
            break
        if len(children) > beam_width:
            children = rng.sample(children, beam_width)
        beams = []
        for points, point_set, p in children:
            new_points = points + [p]
            new_set = set(point_set)
            new_set.add(p)
            beams.append((new_points, new_set))
        depth += 1
    return depth


def randomized_dfs(steps, rng, node_budget=300_000):
    best = 0
    nodes = 0
    points = [(0, 0, 0)]
    point_set = {(0, 0, 0)}
    order = list(range(len(steps)))

    def descend():
        nonlocal best, nodes
        if nodes >= node_budget:
            return
        rng.shuffle(order)
        last = points[-1]
        for si in list(order):
            if nodes >= node_budget:
                return
            nodes += 1
            s = steps[si]
            p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
            if legal(points, point_set, p):
                points.append(p)
                point_set.add(p)
                if len(points) - 1 > best:
                    best = len(points) - 1
                descend()
                point_set.discard(points.pop())

    sys.setrecursionlimit(100_000)
    descend()
    return best


MENUS = {
    "good-4 (deepDFS 224)": [(-1, -2, 2), (-2, 0, 1), (-1, 1, 2), (0, 2, -1)],
    "main-a4r2 winner": [(2, 1, -2), (-1, 2, 0), (-1, -2, 0), (1, 2, 1)],
    "wide-a4r3 winner": [(-1, 3, -2), (-1, -1, 3), (0, 3, -1), (3, -3, -3)],
    "alpha5 winner (5 steps)": [(1, 1, 1), (-2, 2, -2), (-1, 2, -1), (2, -2, 0), (1, -2, -2)],
    "alpha6 mix (6 steps)": [(-1, -2, 2), (-2, 0, 1), (-1, 1, 2), (0, 2, -1), (2, 1, -2), (1, -2, -1)],
}


if __name__ == "__main__":
    beam_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    dfs_restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    for name, steps in MENUS.items():
        rng = Random(hash(name) & 0xFFFFFFFF)
        beam_best = 0
        for run in range(beam_runs):
            beam_best = max(beam_best, beam_search(steps, rng))
            print(f"  {name}: beam run {run + 1}/{beam_runs} best so far {beam_best}", flush=True)
        dfs_best = 0
        for run in range(dfs_restarts):
            dfs_best = max(dfs_best, randomized_dfs(steps, rng))
        print(
            f"RESULT {name:28s} |S|={len(steps)}  "
            f"beam best={beam_best}  randomized-DFS best={dfs_best}",
            flush=True,
        )
