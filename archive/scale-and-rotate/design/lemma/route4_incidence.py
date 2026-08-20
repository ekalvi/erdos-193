"""
ROUTE 4 -- Direct induction through the recursion, for the UNIFORM LOCAL-1-D
INCIDENCE bound  c_k(q,rho) <= C*rho + 1.

We prove/measure the ingredients of the induction:

  Walk_{k+1} = M*Walk_k  (disjoint union)  Stitch_k          [exact identity]
  ||M^-1||_inf = 4/9                                           [exact]
  refill  B_local(rho) := sup_{q in R^3} #{stitch pts within Cheb rho of q}

Induction (real centres q in R^3, radius in [0,10]):
  c_{k+1}(q,rho) <= c_k(M^-1 q, (4/9) rho) + B_local(rho).

Closing condition derived in the write-up:
  small rho:  rho < 0.5  =>  count <= 1  (integer cube side < 1) -- trivial.
  rho in [0.5, 1.125):  need C >= B_local(rho)/rho
  rho in [1.125, 10]:   need C >= (9/5) B_local(rho)/rho
So  C* = max( sup_{[0.5,1.125)} B/rho , (9/5) sup_{[1.125,10]} B/rho ).

This script:
  (A) verifies the recursion identity M^-1 * anchors == parent chain (exact);
  (B) reproduces the FULL incidence c_k over lattice centres (=walk pts): the
      reported max 25 @L6, 26 @L7 for rho=10;
  (C) measures the refill B_local(rho) -- both point-centred (lower bound) and
      the TRUE real-centre max (sliding cube) -- at the L5->L6 and L6->L7
      transitions, and evaluates the closing constant C*.
"""
import json
import os
import pickle
import sys
import time
from fractions import Fraction as F

os.chdir("/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193")

import gate_run
from amplify_rich import M_BAL3

M = M_BAL3


def minv_rational():
    a = [[F(M[i][j]) for j in range(3)] for i in range(3)]
    I = [[F(1) if i == j else F(0) for j in range(3)] for i in range(3)]
    aug = [a[i] + I[i] for i in range(3)]
    for c in range(3):
        piv = next(r for r in range(c, 3) if aug[r][c] != 0)
        aug[c], aug[piv] = aug[piv], aug[c]
        p = aug[c][c]
        aug[c] = [x / p for x in aug[c]]
        for r in range(3):
            if r != c:
                f = aug[r][c]
                aug[r] = [aug[r][k] - f * aug[c][k] for k in range(6)]
    return [row[3:] for row in aug]


MINV = minv_rational()


def apply_minv(p):
    return tuple(sum(MINV[i][j] * p[j] for j in range(3)) for i in range(3))


def build(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]
    words = d["words"]
    chain = [anchors[0]]
    interiors = []
    for i in range(len(anchors) - 1):
        ints = gate_run.word_interiors(anchors[i], words[i])
        interiors.extend(ints)
        chain.extend(ints)
        chain.append(anchors[i + 1])
    return {"anchors": anchors, "interiors": interiors, "chain": chain}


# ---------- spatial hash for closed-ball lattice-centre counting ----------
def build_hash(points, cell):
    H = {}
    for p in points:
        key = (p[0] // cell, p[1] // cell, p[2] // cell)
        H.setdefault(key, []).append(p)
    return H


def count_within(H, cell, q, rho):
    # count points p (from H) with Cheb(p,q) <= rho.  q may be real.
    import math
    kx0 = int(math.floor((q[0] - rho) / cell))
    kx1 = int(math.floor((q[0] + rho) / cell))
    ky0 = int(math.floor((q[1] - rho) / cell))
    ky1 = int(math.floor((q[1] + rho) / cell))
    kz0 = int(math.floor((q[2] - rho) / cell))
    kz1 = int(math.floor((q[2] + rho) / cell))
    n = 0
    for kx in range(kx0, kx1 + 1):
        for ky in range(ky0, ky1 + 1):
            for kz in range(kz0, kz1 + 1):
                bucket = H.get((kx, ky, kz))
                if not bucket:
                    continue
                for p in bucket:
                    if (abs(p[0] - q[0]) <= rho and abs(p[1] - q[1]) <= rho
                            and abs(p[2] - q[2]) <= rho):
                        n += 1
    return n


def point_centred_max(centres, target_points, rhos):
    cell = 11
    H = build_hash(target_points, cell)
    res = {}
    for rho in rhos:
        m = 0
        for q in centres:
            c = count_within(H, cell, q, rho)
            if c > m:
                m = c
        res[rho] = m
    return res


# ---------- TRUE real-centre max: max integer pts in a cube of side W=2rho ----
def real_centre_max(points, rho):
    """Exact max over q in R^3 of #{p: Cheb(p,q) <= rho}.
    Cube side W = 2*rho.  The optimal cube can be pushed so that the point of
    minimum x within it sits on the x-min face; iterate that point a over all
    points (cx = a[0]).  Within the x-slab [a0,a0+W] solve the 2D WxW-square
    max (cy on a point's y-min face, z by two-pointer).  Pruning on `best`.
    """
    W = 2.0 * rho
    cell = int(W) + 1
    H = build_hash(points, cell)
    best = 0
    for a in points:
        a0, a1, a2 = a
        kx = a0 // cell
        ky = a1 // cell
        kz = a2 // cell
        # x-slab within Cheb W of a AND x in [a0, a0+W]  (a is x-min)
        slab = []
        for dx in (0, 1):  # x in [a0,a0+W] -> only same or +1 cell
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    b = H.get((kx + dx, ky + dy, kz + dz))
                    if b:
                        for p in b:
                            if (a0 <= p[0] <= a0 + W
                                    and abs(p[1] - a1) <= W
                                    and abs(p[2] - a2) <= W):
                                slab.append(p)
        if len(slab) <= best:
            continue
        ys = sorted(set(p[1] for p in slab))
        for cy in ys:
            ysel = [p for p in slab if cy <= p[1] <= cy + W]
            if len(ysel) <= best:
                continue
            zs = sorted(p[2] for p in ysel)
            lo = 0
            for hi in range(len(zs)):
                while zs[hi] - zs[lo] > W:
                    lo += 1
                cnt = hi - lo + 1
                if cnt > best:
                    best = cnt
    return best


def main():
    t0 = time.time()
    out = {}
    rowsums = [sum(abs(x) for x in row) for row in MINV]
    out["Minv_inf_norm"] = str(max(rowsums))
    out["Minv"] = [[str(x) for x in row] for row in MINV]

    walks = {L: build(L) for L in (5, 6, 7)}

    # (A) exact recursion identity: M^-1 * anchors(L) == chain(L-1)
    identity = {}
    for L in (6, 7):
        anc = walks[L]["anchors"]
        parent = walks[L - 1]["chain"]
        ok = len(anc) == len(parent)
        if ok:
            for i in range(len(anc)):
                if apply_minv(anc[i]) != tuple(F(v) for v in parent[i]):
                    ok = False
                    break
        identity["M^-1*anchors(L%d)==chain(L%d)" % (L, L - 1)] = ok
    out["recursion_identity"] = identity

    # (B) full incidence over lattice centres (walk points)
    rhos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    full = {}
    for L in (5, 6, 7):
        ch = walks[L]["chain"]
        res = point_centred_max(ch, ch, rhos + [4.44])
        full["L%d" % L] = {str(k): v for k, v in res.items()}
    out["full_incidence_max_lattice_centred"] = full

    # (C) refill B_local at the two transitions.
    # Stitch_{L} lives in walk L+1 as the interiors of walk L+1.
    rhos_fine = [0.5, 0.75, 1.0, 1.125, 1.25, 1.5, 2, 3, 4, 4.44, 5, 6, 7, 8, 9, 10]
    refill = {}
    for L in (6, 7):
        stitch = walks[L]["interiors"]
        # point-centred lower bound (centres = stitch pts)
        pc = point_centred_max(stitch, stitch, rhos_fine)
        refill["L%d_stitch_point_centred" % L] = {str(k): v for k, v in pc.items()}
    out["refill"] = refill

    # (C2) TRUE real-centre max for stitch pts (the quantity the proof needs)
    real_ref = {}
    for L in (6, 7):
        stitch = walks[L]["interiors"]
        d = {}
        for rho in rhos_fine:
            d[str(rho)] = real_centre_max(stitch, rho)
        real_ref["L%d_stitch_real_centre_max" % L] = d
        print("done real-centre L%d  t=%.1f" % (L, time.time() - t0), flush=True)
    out["refill_real_centre"] = real_ref

    # closing constant from real-centre B_local (use max over both transitions)
    def Bloc(rho):
        v = 0
        for L in (6, 7):
            v = max(v, real_ref["L%d_stitch_real_centre_max" % L][str(rho)])
        return v

    small = [r for r in rhos_fine if 0.5 <= r < 1.125]
    big = [r for r in rhos_fine if 1.125 <= r <= 10]
    c_small = max(Bloc(r) / r for r in small) if small else 0
    c_big = (9.0 / 5.0) * max(Bloc(r) / r for r in big) if big else 0
    out["closing"] = {
        "C_small_regime": c_small,
        "C_big_regime": c_big,
        "C_star": max(c_small, c_big),
        "binding_rho_big": max(big, key=lambda r: Bloc(r) / r),
        "B_local_over_rho_big": {str(r): Bloc(r) / r for r in big},
    }
    out["elapsed_sec"] = time.time() - t0
    json.dump(out, open("design/lemma/route4-incidence-results.json", "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
