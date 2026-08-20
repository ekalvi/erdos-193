"""
ROUTE 4 -- BIRTH-TELESCOPING with bounded-range curve control.

Exact identity (birth telescoping):  every point of Walk_L has a unique BIRTH
LEVEL m<=L; born as a Stitch_{m-1} interior, it appears in Walk_L dilated by
M^{L-m}.  With j := L-m,

     c_L(q,rho) = sum_{j>=0} t_j(q,rho),
     t_j(q,rho) = #{ M^j . interiors(L-j)  within Cheb-rho of q },

where interiors(m) = the level-m stitch interiors (the `interiors` of the
gate2 L(m) construction).  Since  M^j.interiors(L-j) in B(q,rho)  <=>
interiors(L-j) in M^{-j}B(q,rho),  a ball of radius rho*||M^{-j}||_inf, the
per-birth-level count t_j is a SINGLE birth level's crowding in a ball that
SHRINKS by ||M^{-j}||_inf ~ (4/9)^j.  On rho<=10 the radius drops below the
lattice packing threshold for small j -> only O(1) terms contribute.

This script:
  (T1) computes ||M^{-j}||_inf and the shrinking radii rho*||M^{-j}||_inf, rho=10.
  (T2) verifies the birth decomposition is exact: the dilated interior sets are
       pairwise disjoint and (with the deep tail) reconstruct chain(L).
  (T3) measures t_j(rho) = EXACT sup over integer centres, rho=1..10, per j,
       at L=7 and L=8; reports how many j contribute >1 and whether each is
       linear (slope t_j/rho).
  (T4) compares sum_j max_q t_j  (birth-telescoped bound) to the true crowding
       max_q c_L(q,rho), and fits C in c_L <= C*rho + 1.
"""
import json, os, pickle, sys, time
from fractions import Fraction as F
from collections import defaultdict

os.chdir("/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3

M = [list(r) for r in M_BAL3]


def matmul(A, B):
    return [[sum(A[i][t] * B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]


def matvec(A, v):
    return tuple(sum(A[i][t] * v[t] for t in range(3)) for i in range(3))


def inv3(m):
    m = [[F(x) for x in r] for r in m]
    a, b, c = m[0]; d, e, f = m[1]; g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    adj = [[(e * i - f * h), -(b * i - c * h), (b * f - c * e)],
           [-(d * i - f * g), (a * i - c * g), -(a * f - c * d)],
           [(d * h - e * g), -(a * h - b * g), (a * e - b * d)]]
    return [[adj[r][col] / det for col in range(3)] for r in range(3)]


def infnorm(A):
    return max(sum(abs(x) for x in r) for r in A)


Minv = inv3(M)
ALPHA = infnorm(Minv)  # 4/9


def interiors_of(level):
    """Level-`level` stitch interiors in level-`level` coordinates."""
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    ints = []
    for i in range(len(anchors) - 1):
        ints.extend(gate_run.word_interiors(anchors[i], words[i]))
    return ints


def chain_of(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    ch = [anchors[0]]
    for i in range(len(anchors) - 1):
        ch.extend(gate_run.word_interiors(anchors[i], words[i]))
        ch.append(anchors[i + 1])
    return ch


def dilate(points, j):
    """Apply M^j to a list of integer points."""
    if j == 0:
        return [tuple(p) for p in points]
    Mj = [[1 if a == b else 0 for b in range(3)] for a in range(3)]
    for _ in range(j):
        Mj = matmul(Mj, M)
    return [matvec(Mj, p) for p in points]


# ---- exact real-centre sup of #{points in closed Cheb-rho box} -------------
def build_hash(points, cell):
    H = {}
    for p in points:
        H.setdefault((p[0] // cell, p[1] // cell, p[2] // cell), []).append(p)
    return H


def exact_sup_integer_centre(points, rho):
    """Exact max over q in R^3 of #{p: Cheb(p,q) <= rho} (box side W=2rho).
    Spatial-hash + prune-on-best sweep (from route4_incidence.real_centre_max):
    the optimal box may be pushed so its x-min face touches a point a; iterate a,
    restrict to the x-slab [a0,a0+W], then 2D WxW-square max on (y,z)."""
    if not points:
        return 0
    W = 2 * int(rho)
    cell = int(W) + 1
    H = build_hash(points, cell)
    best = 0
    for a in points:
        a0, a1, a2 = a
        kx = a0 // cell; ky = a1 // cell; kz = a2 // cell
        slab = []
        for dx in (0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    b = H.get((kx + dx, ky + dy, kz + dz))
                    if b:
                        for p in b:
                            if (a0 <= p[0] <= a0 + W and abs(p[1] - a1) <= W
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
    out["M"] = M
    out["Minv_inf_norm"] = str(ALPHA)

    # (T1) shrinking radii
    P = [[1 if a == b else 0 for b in range(3)] for a in range(3)]
    norms = []
    for j in range(9):
        norms.append(infnorm(P))
        P = matmul(P, Minv)
    S = sum(norms)  # note: infinite tail; j>=9 negligible
    out["Minv_j_inf_norm"] = [str(x) for x in norms]
    out["Minv_j_inf_norm_float"] = [float(x) for x in norms]
    out["S_sum_norms"] = float(S)
    out["radius_rho10_times_norm"] = {("j=%d" % j): float(10 * norms[j]) for j in range(9)}
    # packing threshold: radius < 1/2 => <=1 lattice point
    out["j_where_rho10_radius_below_half"] = next(j for j in range(9) if 10 * norms[j] < F(1, 2))

    results = {}
    for L in (7, 8):
        # birth decomposition: t_j uses interiors(L-j) dilated by M^j
        jmax = L - 5  # we have pkls down to L5
        birth_sets = {}
        for j in range(jmax + 1):
            m = L - j
            ints = interiors_of(m)
            birth_sets[j] = dilate(ints, j)
        # deep tail = chain(L) minus union of birth sets
        full = chain_of(L)
        fullset = set(full)
        union = set()
        overlap = 0
        for j in birth_sets:
            s = set(birth_sets[j])
            overlap += len(union & s)
            union |= s
        tail = [p for p in full if p not in union]
        # sanity: union subset of full?
        union_in_full = union <= fullset

        rhos = list(range(1, 11))
        tj_profile = {}
        for j in range(jmax + 1):
            row = {}
            for rho in rhos:
                row[rho] = exact_sup_integer_centre(birth_sets[j], rho)
            tj_profile[j] = row
            print("L%d t_%d done  t=%.1f" % (L, j, time.time() - t0), flush=True)
        tail_profile = {}
        for rho in rhos:
            tail_profile[rho] = exact_sup_integer_centre(tail, rho)
        print("L%d tail done  t=%.1f" % (L, time.time() - t0), flush=True)

        # true crowding of the full walk
        true_c = {}
        for rho in rhos:
            true_c[rho] = exact_sup_integer_centre(full, rho)
        print("L%d full done  t=%.1f" % (L, time.time() - t0), flush=True)

        # birth-telescoped bound: sum_j max t_j + max tail
        tele_bound = {}
        for rho in rhos:
            s = sum(tj_profile[j][rho] for j in range(jmax + 1)) + tail_profile[rho]
            tele_bound[rho] = s

        results["L%d" % L] = {
            "jmax_measured": jmax,
            "birth_disjoint_overlap": overlap,
            "union_subset_of_chain": union_in_full,
            "tail_size": len(tail),
            "birth_set_sizes": {("j=%d" % j): len(birth_sets[j]) for j in range(jmax + 1)},
            "t_j_sup": {("j=%d" % j): {str(r): tj_profile[j][r] for r in rhos} for j in range(jmax + 1)},
            "t_j_slope": {("j=%d" % j): {str(r): round(tj_profile[j][r] / r, 3) for r in rhos} for j in range(jmax + 1)},
            "tail_sup": {str(r): tail_profile[r] for r in rhos},
            "true_crowding_c": {str(r): true_c[r] for r in rhos},
            "telescoped_bound_sum": {str(r): tele_bound[r] for r in rhos},
            "true_C_slope_(c-1)/rho": {str(r): round((true_c[r] - 1) / r, 3) for r in rhos},
            "tele_C_slope_(b-1)/rho": {str(r): round((tele_bound[r] - 1) / r, 3) for r in rhos},
        }
    out["results"] = results
    out["elapsed_sec"] = time.time() - t0
    json.dump(out, open("design/lemma/route4-birth-telescope-results.json", "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
