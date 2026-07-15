"""
TASK D -- ALTERNATIVE INVARIANT: bad-line count.

A "bad line" for a stitch segment is an infinite line through >=2 already-placed
walk points that passes through the Chebyshev-R tube around the segment's chord
midpoint m.  Any interior lattice site the stitch wants to occupy that lies on
such a line is FORBIDDEN (would create a collinear triple) -- so bad lines, not
raw point crowding, are the direct availability killers.

The walk is triple-free => every line carries <= 2 placed points => every bad
line corresponds to exactly ONE unordered pair of placed points.  Hence

    b_R(segment) = #{ pairs (q1,q2) of placed points :
                      infinite line(q1,q2) meets the box [m-R, m+R]^3 }.

We measure at STITCH TIME (the state the constructor actually saw): placed
points = all anchors  U  interiors of segments stitched earlier in `order`.
This mirrors exactly how the published c10 clearance ledger was produced, so
c10 and b are apples-to-apples with availability (frac / surv_abs).

Line-vs-Chebyshev-box test is EXACT: for a Chebyshev box the per-axis feasible
t-intervals of the parametric line a1 + t*(a2-a1) must share a common t.

Neighbor cutoff D: we only pair placed points within Cheb D of m.  A
convergence sweep (mode `converge`) shows b is essentially saturated by a
finite D, justifying the cutoff (far-far pairs threading a size-20 tube are
negligible).

Usage (pypy3):
  pypy3 taskD_badlines.py converge 6      # D-convergence on a subset, level 6
  pypy3 taskD_badlines.py measure 5       # full measurement, level 5
  pypy3 taskD_badlines.py measure 6
  pypy3 taskD_badlines.py measure 7 2500  # level 7, uniform sample of positions
"""
from __future__ import annotations
import json, pickle, sys, time
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)
R = 10            # tube radius (matches c10)
CELL = 40         # spatial-hash cell size


def word_interiors(start, word_idx):
    pts = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = MENU[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        pts.append((x, y, z))
    return pts


def load_state(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl", "rb"))
    return d["parent_word"], d["order"], d["words"], d["anchors"]


def cell_of(p):
    return (p[0] // CELL, p[1] // CELL, p[2] // CELL)


def line_hits_box(a1, a2, Rr):
    """Exact: does the infinite line through a1,a2 meet [-Rr,Rr]^3 ?
    (a1,a2 already shifted so the box is centred at origin.)"""
    lo, hi = -1e18, 1e18
    for j in range(3):
        d = a2[j] - a1[j]
        p = a1[j]
        if d == 0:
            if p < -Rr or p > Rr:
                return False
        else:
            t0 = (-Rr - p) / d
            t1 = (Rr - p) / d
            if t0 > t1:
                t0, t1 = t1, t0
            if t0 > lo:
                lo = t0
            if t1 < hi:
                hi = t1
            if lo > hi:
                return False
    return lo <= hi


def gather(grid, m, D):
    """placed points within Cheb D of m, via spatial hash."""
    cx, cy, cz = m
    c0 = cell_of((cx - D, cy - D, cz - D))
    c1 = cell_of((cx + D, cy + D, cz + D))
    out = []
    for gx in range(c0[0], c1[0] + 1):
        for gy in range(c0[1], c1[1] + 1):
            for gz in range(c0[2], c1[2] + 1):
                b = grid.get((gx, gy, gz))
                if b:
                    for p in b:
                        if abs(p[0] - cx) <= D and abs(p[1] - cy) <= D and abs(p[2] - cz) <= D:
                            out.append(p)
    return out


def b_and_c(nbrs, m, D):
    """given placed points within Cheb D of m, return (c10, b_at_D)."""
    cx, cy, cz = m
    # shift
    sh = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in nbrs]
    c10 = sum(1 for a in sh if abs(a[0]) <= R and abs(a[1]) <= R and abs(a[2]) <= R)
    b = 0
    n = len(sh)
    for i in range(n):
        a1 = sh[i]
        for k in range(i + 1, n):
            if line_hits_box(a1, sh[k], R):
                b += 1
    return c10, b


def midpoint(anchors, i):
    A, B = anchors[i], anchors[i + 1]
    return ((A[0] + B[0]) // 2, (A[1] + B[1]) // 2, (A[2] + B[2]) // 2)


def build_replay(level):
    parent_word, order, words, anchors = load_state(level)
    grid = {}
    for p in anchors:
        grid.setdefault(cell_of(p), []).append(p)
    return parent_word, order, words, anchors, grid


from math import gcd


def igcd3(a, b, c):
    g = gcd(abs(a), abs(b))
    g = gcd(g, abs(c))
    return g if g else 1


def forbidden_sites_from_pairs(sh, Rr):
    """given shifted placed points sh (box centred at origin), return the set of
    integer lattice sites in [-Rr,Rr]^3 that lie on a line through >=2 of them.
    Only pairs whose line meets the box contribute; we walk the integer points
    of that line inside the box.  (Union => bounded.)"""
    marked = set()
    n = len(sh)
    for i in range(n):
        a1 = sh[i]
        for k in range(i + 1, n):
            a2 = sh[k]
            dx, dy, dz = a2[0] - a1[0], a2[1] - a1[1], a2[2] - a1[2]
            g = igcd3(dx, dy, dz)
            ux, uy, uz = dx // g, dy // g, dz // g
            # integer points on the line are a1 + s*(ux,uy,uz), s integer.
            # find s-range keeping all coords within [-Rr,Rr].
            lo, hi = -10**9, 10**9
            ok = True
            for p0, u in ((a1[0], ux), (a1[1], uy), (a1[2], uz)):
                if u == 0:
                    if p0 < -Rr or p0 > Rr:
                        ok = False
                        break
                else:
                    s0 = (-Rr - p0) / u
                    s1 = (Rr - p0) / u
                    if s0 > s1:
                        s0, s1 = s1, s0
                    import math
                    lo = max(lo, math.ceil(s0))
                    hi = min(hi, math.floor(s1))
            if not ok or lo > hi:
                continue
            for s in range(lo, hi + 1):
                marked.add((a1[0] + s * ux, a1[1] + s * uy, a1[2] + s * uz))
    # exclude the placed points themselves (they are not candidate interior sites)
    placed = set(sh)
    return len(marked - placed)


def converge(level):
    """b(D) and forbidden-site f(D) for increasing D -> pick a cutoff."""
    parent_word, order, words, anchors, grid = build_replay(level)
    Ds = [20, 40, 60, 80, 120]
    rng = Random(42)
    npos = len(order)
    targets = sorted(rng.sample(range(npos), min(150, npos)))
    tset = set(targets)
    accb = {D: [] for D in Ds}
    accf = {D: [] for D in Ds}
    t0 = time.time()
    for pos, i in enumerate(order):
        if pos in tset:
            m = midpoint(anchors, i)
            nb = gather(grid, m, max(Ds))
            cx, cy, cz = m
            sh = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in nb]
            for D in Ds:
                shD = [a for a in sh if abs(a[0]) <= D and abs(a[1]) <= D and abs(a[2]) <= D]
                bb = 0
                n = len(shD)
                for x in range(n):
                    a1 = shD[x]
                    for y in range(x + 1, n):
                        if line_hits_box(a1, shD[y], R):
                            bb += 1
                accb[D].append(bb)
                accf[D].append(forbidden_sites_from_pairs(shD, R))
        for p in word_interiors(anchors[i], words[i]):
            grid.setdefault(cell_of(p), []).append(p)
    out = {"level": level, "n": len(targets), "elapsed_s": round(time.time() - t0, 1),
           "b_mean_by_D": {D: round(sum(v) / len(v), 3) for D, v in accb.items()},
           "b_max_by_D": {D: max(v) for D, v in accb.items()},
           "f_mean_by_D": {D: round(sum(v) / len(v), 3) for D, v in accf.items()},
           "f_max_by_D": {D: max(v) for D, v in accf.items()}}
    print(json.dumps(out))
    return out


def corr(pairs):
    n = len(pairs)
    mc = sum(p[0] for p in pairs) / n
    mb = sum(p[1] for p in pairs) / n
    sc = (sum((p[0] - mc) ** 2 for p in pairs) / n) ** 0.5
    sb = (sum((p[1] - mb) ** 2 for p in pairs) / n) ** 0.5
    cov = sum((p[0] - mc) * (p[1] - mb) for p in pairs) / n
    return cov / (sc * sb) if sc > 0 and sb > 0 else 0.0


def measure(level, sample=None):
    parent_word, order, words, anchors, grid = build_replay(level)
    D = 40  # fixed physical neighbourhood (cross-level scale-invariance test)
    npos = len(order)
    if sample and sample < npos:
        rng = Random(7)
        targets = set(rng.sample(range(npos), sample))
    else:
        targets = set(range(npos))
    cs, bs, fs = [], [], []
    t0 = time.time()
    for pos, i in enumerate(order):
        if pos in targets:
            m = midpoint(anchors, i)
            nb = gather(grid, m, D)
            cx, cy, cz = m
            sh = [(p[0] - cx, p[1] - cy, p[2] - cz) for p in nb]
            c10 = sum(1 for a in sh if abs(a[0]) <= R and abs(a[1]) <= R and abs(a[2]) <= R)
            b = 0
            n = len(sh)
            for x in range(n):
                a1 = sh[x]
                for y in range(x + 1, n):
                    if line_hits_box(a1, sh[y], R):
                        b += 1
            f = forbidden_sites_from_pairs(sh, R)
            cs.append(c10); bs.append(b); fs.append(f)
        for p in word_interiors(anchors[i], words[i]):
            grid.setdefault(cell_of(p), []).append(p)
    def dist(v):
        s = sorted(v)
        n = len(s)
        return {"n": n, "min": s[0], "mean": round(sum(v) / n, 3),
                "p50": s[n // 2], "p90": s[min(n - 1, int(0.9 * n))],
                "p99": s[min(n - 1, int(0.99 * n))], "max": s[-1]}
    out = {"level": level, "D": D, "R": R, "elapsed_s": round(time.time() - t0, 1),
           "c10": dist(cs), "b": dist(bs), "f": dist(fs),
           "corr_c10_b": round(corr(list(zip(cs, bs))), 4),
           "corr_c10_f": round(corr(list(zip(cs, fs))), 4),
           "b_over_c10_mean": round(sum(bs) / sum(cs), 3),
           "f_over_c10_mean": round(sum(fs) / sum(cs), 3)}
    with open(f"/Users/erik/homelab/math193/design/lemma/taskD-L{level}.json", "w") as f:
        json.dump({"summary": out, "c10": cs, "b": bs, "f": fs}, f)
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    level = int(sys.argv[2])
    if mode == "converge":
        converge(level)
    elif mode == "measure":
        sample = int(sys.argv[3]) if len(sys.argv) > 3 else None
        measure(level, sample)
