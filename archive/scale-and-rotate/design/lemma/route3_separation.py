"""
ROUTE 3 -- CLEARANCE / SEPARATION analysis for the uniform local-1-D incidence bound.

Goal inequality:  c_k(q,rho) = #{walk pts within Cheb rho of q} <= C*rho + 1, uniform in k.

This script tests, on the REAL seed-193 orbit walks (L5/L6/L7), every sub-claim a
separation/packing route could rest on:

  (S0) global minimum inter-point Chebyshev separation (all pairs).
  (S1) PACKING baselines in the densest ball:
        - trivial Cheb-1 packing: (2rho+1)^3   (useless, cubic)
        - no-3-in-line packing (triple-free): points-per-line <=2   (quadratic-ish)
  (S2) PATH-ARC structure of the densest balls: how many maximal contiguous
        path-arcs make up the points in B(q,rho), and each arc's length.
        -> linear bound = (#arcs) x (max arc length). Test both factors.
  (S3) PATH-DISTANCE vs SPACE-DISTANCE separation (the key sub-lemma for linear):
        for pairs at path-distance |i-j| >= T, what is the min Chebyshev distance?
        A "return gap" g(T) that grows means the path cannot re-approach itself
        except path-locally -> then a ball holds ~ (arcs) each path-local -> linear.
  (S4) directly: max_q c_k(q,rho) and the induced C = max_rho (c-1)/rho.

Run:  pypy3 route3_separation.py L6   (or L5/L7)
"""
import sys, pickle, json
from collections import defaultdict

sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_interiors

MENU = candidate_step_vectors(2)


def load_chain(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl", "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = [anchors[0]]
    anchors_idx = [0]
    for i in range(len(anchors) - 1):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i + 1])
        anchors_idx.append(len(chain) - 1)
    return chain, set(anchors_idx)


def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))


def grid_index(chain, cell):
    """Bucket points into cells of side `cell` for neighbor queries."""
    g = defaultdict(list)
    for i, p in enumerate(chain):
        g[(p[0]//cell, p[1]//cell, p[2]//cell)].append(i)
    return g


def count_ball(chain, grid, cell, q, rho):
    """indices of chain points within Cheb rho of q, using grid of side `cell`>=rho."""
    assert cell >= rho
    cx, cy, cz = q[0]//cell, q[1]//cell, q[2]//cell
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for i in grid.get((cx+dx, cy+dy, cz+dz), ()):
                    if cheb(chain[i], q) <= rho:
                        out.append(i)
    return out


def s0_min_separation(chain):
    """Global min all-pairs Cheb separation via grid (cell=1 -> exact for sep>=1)."""
    # min sep is >=1 (distinct lattice pts). Find actual min and its multiplicity,
    # and the min sep among NON-CONSECUTIVE path points.
    g = grid_index(chain, 1)  # cell 1: neighbors within Cheb 1 are in 27 adjacent cells
    n = len(chain)
    min_all = 99
    min_nonadj = 99
    pair_all = pair_nonadj = None
    for i, p in enumerate(chain):
        cx, cy, cz = p
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in g.get((cx+dx, cy+dy, cz+dz), ()):
                        if j <= i:
                            continue
                        d = cheb(p, chain[j])
                        if d < min_all:
                            min_all = d; pair_all = (i, j)
                        if abs(i-j) > 1 and d < min_nonadj:
                            min_nonadj = d; pair_nonadj = (i, j)
    return {"min_sep_all": min_all, "min_sep_nonadjacent": min_nonadj,
            "pair_all": pair_all, "pair_nonadj": pair_nonadj}


def densest_balls(chain, rho, topk=5):
    """max_q c(q,rho) taking q ranging over walk points (worst case is near a pt)."""
    cell = rho if rho >= 1 else 1
    grid = grid_index(chain, cell)
    best = []
    seen = {}
    for i, q in enumerate(chain):
        idxs = count_ball(chain, grid, cell, q, rho)
        c = len(idxs)
        seen[i] = c
    # top centres
    order = sorted(seen, key=lambda i: -seen[i])[:topk]
    for i in order:
        idxs = count_ball(chain, grid, cell, chain[i], rho)
        best.append((seen[i], i, sorted(idxs)))
    maxc = max(seen.values())
    return maxc, best


def arc_structure(idxs):
    """Given sorted chain-indices inside a ball, split into maximal consecutive arcs."""
    arcs = []
    cur = [idxs[0]]
    for a in idxs[1:]:
        if a == cur[-1] + 1:
            cur.append(a)
        else:
            arcs.append(cur); cur = [a]
    arcs.append(cur)
    return arcs


def s3_return_gap(chain, Ts):
    """For each threshold T, min Cheb dist over pairs with |i-j|>=T.
    Uses grid at cell=1 for close pairs (Cheb<=some cap). We seek the SMALLEST
    space-distance achievable at each path-gap, so scan close pairs (Cheb<=6)."""
    CAP = 8
    g = grid_index(chain, CAP)
    # collect all pairs with Cheb<=CAP and record (space_cheb, path_gap)
    pairs = []
    n = len(chain)
    seen = set()
    for i, p in enumerate(chain):
        cx, cy, cz = p[0]//CAP, p[1]//CAP, p[2]//CAP
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in g.get((cx+dx, cy+dy, cz+dz), ()):
                        if j <= i:
                            continue
                        d = cheb(p, chain[j])
                        if d <= CAP:
                            pairs.append((d, abs(i-j)))
    out = {}
    for T in Ts:
        m = min((d for d, gap in pairs if gap >= T), default=None)
        out[T] = m
    # inverse view: for each space-distance d, the MIN path-gap seen (are close
    # points always path-close?) and count of "far-in-path but near-in-space" pairs
    close_far = defaultdict(int)  # space d -> #pairs with path-gap>=50
    for d, gap in pairs:
        if gap >= 50:
            close_far[d] += 1
    return {"min_space_given_pathgap>=T": out,
            "num_pairs_pathgap>=50_by_space_cheb": dict(sorted(close_far.items()))}


def main():
    level = sys.argv[1] if len(sys.argv) > 1 else "6"
    lv = int(level)
    chain, anchor_set = load_chain(lv)
    N = len(chain)
    res = {"level": lv, "N": N}

    res["S0_separation"] = s0_min_separation(chain)

    # S4 / S1 / S2 over rho
    rho_report = {}
    for rho in range(1, 11):
        maxc, best = densest_balls(chain, rho, topk=3)
        # analyse the densest ball
        c, ci, idxs = best[0]
        arcs = arc_structure(idxs)
        arclens = sorted((len(a) for a in arcs), reverse=True)
        # packing baselines
        trivial = (2*rho+1)**3
        # no-3-in-line count within these points: lines occupied
        rho_report[rho] = {
            "max_c": maxc,
            "C_est_(c-1)/rho": round((maxc-1)/rho, 3),
            "densest_num_arcs": len(arcs),
            "densest_arc_lengths": arclens,
            "densest_max_arc": arclens[0],
            "trivial_cheb1_packing": trivial,
        }
    res["S4_incidence_and_arcs"] = rho_report

    res["S3_return_gap"] = s3_return_gap(chain, [1, 2, 3, 5, 10, 20, 50, 100, 500])

    out = f"/Users/erik/homelab/math193/design/lemma/route3-sep-L{lv}.json"
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    print("WROTE", out)


if __name__ == "__main__":
    main()
