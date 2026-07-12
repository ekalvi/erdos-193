"""
Phase 2: branch-and-bound / DFS for the longest collinear-triple-free walk
with steps freely chosen from a fixed finite set S in Z^3.

Legality of a new point p against existing points P: p is illegal iff
  - p coincides with an earlier point, or
  - two earlier points have parallel directions from p
    (then p lies on the line through them).
Checking is O(|P|) per candidate extension using a direction set.
"""
from __future__ import annotations

import sys
from math import gcd
from search193 import candidate_step_vectors

Vector = tuple


def primitive_direction(v):
    g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    w = (v[0] // g, v[1] // g, v[2] // g)
    for c in w:
        if c:
            if c < 0:
                w = (-w[0], -w[1], -w[2])
            break
    return w


def legal(points, point_set, p):
    if p in point_set:
        return False
    seen = set()
    px, py, pz = p
    for (qx, qy, qz) in points:
        d = primitive_direction((qx - px, qy - py, qz - pz))
        if d in seen:
            return False
        seen.add(d)
    return True


def dfs_longest(steps, node_budget=2_000_000):
    """Iterative DFS. Returns (best_depth, best_word, budget_exhausted)."""
    best_depth = 0
    best_word = []
    nodes = 0
    points = [(0, 0, 0)]
    point_set = {(0, 0, 0)}
    word = []
    # stack of iterators over step indices to try at each depth
    stack = [iter(range(len(steps)))]

    while stack:
        if nodes >= node_budget:
            return best_depth, best_word, True
        it = stack[-1]
        advanced = False
        for si in it:
            nodes += 1
            s = steps[si]
            last = points[-1]
            p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
            if legal(points, point_set, p):
                points.append(p)
                point_set.add(p)
                word.append(si)
                if len(word) > best_depth:
                    best_depth = len(word)
                    best_word = word[:]
                stack.append(iter(range(len(steps))))
                advanced = True
                break
        if not advanced:
            stack.pop()
            if word:
                point_set.discard(points.pop())
                word.pop()

    return best_depth, best_word, False


if __name__ == "__main__":
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000

    step_sets = {
        "best-substitution-candidate": [(-1, -2, 2), (-2, 0, 1), (-1, 1, 2), (0, 2, -1)],
        "4 asymmetric radius-1": [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1)],
        "tetrahedral": [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
        "6 axis steps": [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
        "all radius-1 (26 steps)": candidate_step_vectors(1),
        "all radius-2 (124 steps)": candidate_step_vectors(2),
    }

    for name, steps in step_sets.items():
        depth, word, exhausted = dfs_longest(steps, budget)
        tag = "budget exhausted" if exhausted else "EXHAUSTIVE (true maximum)"
        print(f"{name:32s} |S|={len(steps):3d}  longest triple-free walk = {depth:4d}  [{tag}]")
        if depth <= 60:
            print(f"  word: {word}")
        sys.stdout.flush()
