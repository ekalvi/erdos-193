"""
Dissect the DENSEST ball at each level (rho=10) to reveal what separates the
several path-arcs: spool u (log-radius), spiral angle theta, birth level, or
path-index only.  Also test whether the *unwound* spiral coordinate
  Psi = u * cos(gamma) + (theta/(2pi)) ... (a log-spiral phase)
separates arcs that share u.
"""
import sys, pickle, math
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
from route3_spool import (load_chain, u_coord, theta_coord, cheb, arcs_of,
                          grid_index, compute_colevels, Q)

ALPHA = math.acos(-1.0 / 6.0)  # irrational rotation per M in yz-plane


def dissect(level, rho=10, topballs=3):
    colev, chain = compute_colevels(level)
    N = len(chain)
    us = [u_coord(p) for p in chain]
    ths = [theta_coord(p) for p in chain]
    cell = rho
    grid = grid_index(chain, cell)

    # find densest balls by #arcs then by count
    def ball_idxs(q):
        cx, cy, cz = q[0] // cell, q[1] // cell, q[2] // cell
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((cx + dx, cy + dy, cz + dz), ()):
                        if cheb(chain[j], q) <= rho:
                            out.append(j)
        return out

    scored = []
    for qi, q in enumerate(chain):
        idxs = ball_idxs(q)
        arcs = arcs_of(idxs[:])
        scored.append((len(arcs), len(idxs), qi))
    scored.sort(reverse=True)

    print(f"\n===== L{level} rho={rho}  (top {topballs} by #arcs) =====")
    for (nA, nc, qi) in scored[:topballs]:
        q = chain[qi]
        idxs = ball_idxs(q)
        arcs = arcs_of(idxs[:])
        R = math.sqrt(Q(q))
        print(f"\n center idx {qi} q={q}  Q-radius={R:.1f}  #arcs={nA} count={nc}")
        for a, arc in enumerate(arcs):
            bl = defaultdict(int)
            for j in arc:
                bl[colev[j]] += 1
            umin = min(us[j] for j in arc); umax = max(us[j] for j in arc)
            tmin = min(ths[j] for j in arc); tmax = max(ths[j] for j in arc)
            print(f"   arc{a}: pathidx[{arc[0]}..{arc[-1]}] len={len(arc)}"
                  f" birthlevels={dict(bl)}"
                  f" u=[{umin:.3f},{umax:.3f}] theta=[{tmin:+.3f},{tmax:+.3f}]")
        # pairwise: for arcs, are they separated by u? by theta? by birthlevel?
        reps_u = [sum(us[j] for j in arc) / len(arc) for arc in arcs]
        reps_t = [sum(ths[j] for j in arc) / len(arc) for arc in arcs]
        reps_b = [max(defaultdict(int, {c: sum(1 for j in arc if colev[j] == c)
                      for c in set(colev[j] for j in arc)}).items(),
                      key=lambda kv: kv[1])[0] for arc in arcs]
        print(f"   arc u-reps:     {[round(x,3) for x in reps_u]}")
        print(f"   arc theta-reps: {[round(x,3) for x in reps_t]}")
        print(f"   arc birthlevel: {reps_b}")


if __name__ == "__main__":
    for lv in (6, 7):
        dissect(lv, rho=10, topballs=3)
