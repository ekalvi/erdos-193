"""
2D analog of anchor-guided amplification, for the visual explainer.
M = [[2,-1],[1,2]] is multiplication by the Gaussian integer 2+i:
scale sqrt(5), irrational rotation atan(1/2). Menu: all 24 radius-2
2D vectors. Emits JSON with real per-level data: points, which points
are anchors, and the stitch segments.
"""
from __future__ import annotations

import json
from math import gcd
from random import Random

M = ((4, -1), (1, 4))
MENU = [
    (x, y)
    for x in range(-2, 3)
    for y in range(-2, 3)
    if (x, y) != (0, 0)
]


def apply(v):
    return (M[0][0] * v[0] + M[0][1] * v[1], M[1][0] * v[0] + M[1][1] * v[1])


def pdir(v):
    g = gcd(abs(v[0]), abs(v[1]))
    w = (v[0] // g, v[1] // g)
    if w[0] < 0 or (w[0] == 0 and w[1] < 0):
        w = (-w[0], -w[1])
    return w


def legal(points, pset, p):
    if p in pset:
        return False
    seen = set()
    for q in points:
        d = pdir((q[0] - p[0], q[1] - p[1]))
        if d in seen:
            return False
        seen.add(d)
    return True


def verify(points):
    for k, p in enumerate(points):
        if not legal(points[:k], set(points[:k]), p):
            return False
    return True


def find_base(rng, length=4, tries=3000):
    for _ in range(tries):
        pts = [(0, 0)]
        pset = {(0, 0)}
        word = []
        ok = True
        for _ in range(length):
            sis = list(range(len(MENU)))
            rng.shuffle(sis)
            for si in sis:
                s = MENU[si]
                p = (pts[-1][0] + s[0], pts[-1][1] + s[1])
                if legal(pts, pset, p):
                    pts.append(p)
                    pset.add(p)
                    word.append(si)
                    break
            else:
                ok = False
                break
        if ok:
            return pts
    return None


def amplify(points, rng, seg_maxlen=14, tries=300):
    anchors = [apply(p) for p in points]
    for _ in range(tries):
        placed = [anchors[0]]
        pset = {anchors[0]}
        segments = []
        failed = False
        for i, target in enumerate(anchors[1:]):
            future = []
            seg = None
            for _try in range(8):
                path = route(placed, pset, target, future, rng, seg_maxlen)
                if path is not None:
                    seg = path
                    break
            if seg is None:
                failed = True
                break
            placed.extend(seg)
            pset.update(seg)
            segments.append(seg)
        if not failed and verify(placed):
            return placed, anchors, segments
    return None


def route(placed, pset, target, future, rng, maxlen):
    obstacles_extra = [target] + future
    start = placed[-1]
    gap0 = max(abs(target[0] - start[0]), abs(target[1] - start[1]))
    for depth in range(max(1, -(-gap0 // 2)), maxlen + 1):
        seg = []
        nodes = [0]
        if dfs(placed, pset, seg, target, obstacles_extra, depth, rng, nodes):
            return seg
    return None


def dfs(placed, pset, seg, target, extra, depth, rng, nodes):
    nodes[0] += 1
    if nodes[0] > 15_000:
        return False
    last = seg[-1] if seg else placed[-1]
    gap = max(abs(target[0] - last[0]), abs(target[1] - last[1]))
    if gap == 0:
        return True
    if depth == 0 or gap > depth * 2:
        return False
    order = list(MENU)
    rng.shuffle(order)
    for s in order:
        p = (last[0] + s[0], last[1] + s[1])
        allpts = placed + seg + extra
        allset = pset | set(seg) | set(extra)
        if p == target or legal(allpts, allset, p):
            seg.append(p)
            if dfs(placed, pset, seg, target, extra, depth - 1, rng, nodes):
                return True
            seg.pop()
    return False



if False and __name__ == "__main__":
    for seed in (7, 11, 42, 99, 5, 27, 193, 61):
        print(f"--- seed {seed}")
        levels = build(seed)
        if len(levels) >= 3:
            with open("viz2d-data.json", "w") as f:
                json.dump({"matrix": M, "levels": levels}, f)
            print(f"SUCCESS with seed {seed}: sizes {[len(l['points']) for l in levels]}")
            break
