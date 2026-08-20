"""
Per-ball path-index structure (rho in {5,10}), all levels:
  - SPAN = max_idx - min_idx of in-ball points (local-window size)
  - MAXGAP = max path-gap between consecutive in-ball indices (a big gap = a
    genuine FAR return / global recurrence; small span+small gap = pure local meander)
  - #arcs, and how many arcs are "far" (preceded by a gap > 2*L(rho)=~6*rho).
Goal: show the DENSE balls are bounded LOCAL windows (span level-uniform), and the
few genuinely-far returns are <= the spool birthspread bound.
"""
import sys, math
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
from route3_spool import load_chain, cheb, arcs_of, grid_index, u_coord, compute_colevels


def analyze(level, rhos=(5, 10)):
    colev, chain = compute_colevels(level)
    N = len(chain)
    res = {}
    for rho in rhos:
        cell = rho
        grid = grid_index(chain, cell)
        max_span = 0; span_ball = None
        max_gap = 0; gap_ball = None
        max_far_arcs = 0        # arcs separated from previous by gap > FARGAP
        FARGAP = 6 * rho        # ~2*ballistic sojourn: bigger => genuine return
        worst_A = 0
        for qi, q in enumerate(chain):
            cx, cy, cz = q[0] // cell, q[1] // cell, q[2] // cell
            idxs = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j in grid.get((cx + dx, cy + dy, cz + dz), ()):
                            if cheb(chain[j], q) <= rho:
                                idxs.append(j)
            if len(idxs) < 2:
                continue
            idxs.sort()
            span = idxs[-1] - idxs[0]
            if span > max_span:
                max_span = span; span_ball = qi
            arcs = arcs_of(idxs[:])
            if len(arcs) > worst_A:
                worst_A = len(arcs)
            # gaps between consecutive arcs
            far = 1
            for a, b in zip(arcs, arcs[1:]):
                g = b[0] - a[-1]
                if g > max_gap:
                    max_gap = g; gap_ball = qi
                if g > FARGAP:
                    far += 1
            if far > max_far_arcs:
                max_far_arcs = far
        res[rho] = {
            "max_arcs": worst_A,
            "max_local_span": max_span,
            "max_interarc_gap": max_gap,
            "FARGAP_threshold": FARGAP,
            "max_far_arcs(gap>FARGAP)": max_far_arcs,
        }
    return res


if __name__ == "__main__":
    for lv in (5, 6, 7):
        r = analyze(lv)
        print(f"L{lv}: {r}", flush=True)
