"""
BOUND-2: LOW-SHELL charge via a LOCAL-CONFIG AUTOMATON.

Single-level refill  b_L(r) = sup_q #{ level-L stitch interiors in Cheb-r(q) }.
Via birth-telescoping the load-bearing crowding bound is
    c_k(4.44) <= b(4.44) + b(4*4.44/9) + b(4*4.44/27) + 1
             =  tau_0(4.44) + tau_1(4.44) + tau_2(4.44) + 1
with tau_0(r)=b(r), tau_1(r)=b(4r/9), tau_2(r)=b(4r/27)  (||M^-1||=4/9, ||M^-2||=4/27).

THE AUTOMATON.  Every level-L interior sits within Cheb-4 of the NEARER of the two
anchors of its parent-segment (finite-menu fact: reach<=4, interiors/word<=4, PROVEN
over the whole menu).  Anchors = M.(parent chain point).  So the interiors in a ball
B(q,r) are DETERMINED by the LOCAL ANCHOR CONFIG:
    LC(q,r) = { anchors A=M.p in Cheb-(r+4) of q } + their incident parent-steps
              + the chosen connector words, all translated to q.

FINITENESS (non-circular).  Anchors are 3-SEPARATED (min_{v!=0}|M.v|_inf = 3, exact,
proven) and M is injective, so
    #{ anchors in Cheb-(r+4) }  <=  P(r+4) := (floor(2(r+4)/3)+1)^3
a PURE PACKING NUMBER, level-independent, needing NO crowding hypothesis.  Hence the
config alphabet is finite and level-uniform.  b_L(r) <= max over configs of #interiors.

This script MEASURES, at L6/L7/L8:
 (1) b_L(r) exact (single-level t_0) at r in {1..10, 4.44, 1.97, 0.66} -> level-uniformity
     of tau_0, tau_1, tau_2 and the load-bearing sum.
 (2) For crowding-achieving centres: #anchors-in-window vs packing P(r+4); #arcs
     (returns+1 = maximal consecutive parent-index runs in window); #interiors.
     -> does the config look like an ARC (linear) or a BLOB (cubic packing)?
 (3) distinct canonical anchor-configs (reachable-config count) + its level growth,
     to estimate whether the reachable set is genuinely finite/tractable.
"""
import json, os, pickle, sys, time
from fractions import Fraction as F
from collections import defaultdict

os.chdir("/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3

M = [list(r) for r in M_BAL3]
def matvec(A, v): return tuple(sum(A[i][t]*v[t] for t in range(3)) for i in range(3))
def cheb(a, b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))


def load_level(L):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % L, "rb"))
    anchors = d["anchors"]; words = d["words"]
    # fresh interiors of level L, and the parent-anchor index each belongs to,
    # tagged with the NEARER anchor.
    interiors = []
    int_anchor = []   # index of nearer anchor for each interior
    for i in range(len(anchors) - 1):
        A, B = anchors[i], anchors[i + 1]
        segints = gate_run.word_interiors(A, words[i])
        for p in segints:
            interiors.append(p)
            int_anchor.append(i if cheb(p, A) <= cheb(p, B) else i + 1)
    return anchors, words, interiors, int_anchor


# ---------- exact real-centre sup of #integer pts in Cheb-r box -------------
def build_hash(points, cell):
    H = {}
    for p in points:
        H.setdefault((p[0] // cell, p[1] // cell, p[2] // cell), []).append(p)
    return H

def exact_sup(points, rho):
    """Exact max over q in R^3 of #{p: Cheb(p,q)<=rho}.  W=2*floor(rho) side box
    (integer pts at Cheb<=rho from a real centre <=> coord-spread <= floor(2*rho);
    we use the standard W=2*int(rho) used across this codebase for consistency)."""
    if not points: return 0
    W = 2 * int(rho)
    if 2 * rho - W >= 1:  # fractional radius wide enough for one more integer
        W += 1
    cell = int(W) + 1
    H = build_hash(points, cell)
    best = 0; argc = None
    for a in points:
        a0, a1, a2 = a
        kx, ky, kz = a0 // cell, a1 // cell, a2 // cell
        slab = []
        for dx in (0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    b = H.get((kx + dx, ky + dy, kz + dz))
                    if b:
                        for p in b:
                            if a0 <= p[0] <= a0 + W and abs(p[1]-a1) <= W and abs(p[2]-a2) <= W:
                                slab.append(p)
        if len(slab) <= best: continue
        ys = sorted(set(p[1] for p in slab))
        for cy in ys:
            ysel = [p for p in slab if cy <= p[1] <= cy + W]
            if len(ysel) <= best: continue
            zs = sorted(p[2] for p in ysel)
            lo = 0
            for hi in range(len(zs)):
                while zs[hi] - zs[lo] > W: lo += 1
                cnt = hi - lo + 1
                if cnt > best:
                    best = cnt; argc = (a0, cy, zs[lo])
    return best, argc


def packing(r):
    """(floor(2r/3)+1)^3 : anchors are Cheb-3-separated."""
    import math
    n = math.floor(2 * r / 3) + 1
    return n * n * n


def analyze_configs(anchors, interiors, int_anchor, r, centres, rwin=None):
    """For each candidate integer centre q, extract the local anchor config:
    anchors within Cheb-(r+4); count them; count arcs (maximal consecutive-index
    runs); count interiors within Cheb-r; canonical signature of the anchor
    arrangement (translated, sorted)."""
    if rwin is None:
        rwin = r + 4
    W = int(rwin) + 1
    Hanch = build_hash(anchors, W + 1)
    Hint = build_hash(interiors, int(r) + 2)
    cellA = W + 1
    cellI = int(r) + 2
    max_int = 0; best_rec = None
    sig_count = defaultdict(int)
    recs = []
    for q in centres:
        # interiors in Cheb-r(q)
        kx, ky, kz = q[0]//cellI, q[1]//cellI, q[2]//cellI
        nint = 0
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    b = Hint.get((kx+dx, ky+dy, kz+dz))
                    if b:
                        for p in b:
                            if cheb(p, q) <= r: nint += 1
        # anchors in Cheb-(r+4)(q), with their global indices
        ax, ay, az = q[0]//cellA, q[1]//cellA, q[2]//cellA
        win_idx = []
        win_pts = []
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    b = Hanch.get((ax+dx, ay+dy, az+dz))
                    if b:
                        for p in b:
                            if cheb(p, q) <= rwin:
                                win_pts.append(p)
        # need global indices -> build index map once outside; here recompute via dict
        # (anchors unique)
        idxs = sorted(anch_index[p] for p in win_pts)
        # arcs = maximal consecutive runs of anchor indices
        arcs = 1 if idxs else 0
        for u, v in zip(idxs, idxs[1:]):
            if v != u + 1: arcs += 1
        nanch = len(idxs)
        # canonical signature: translate anchors by min corner, sort
        if win_pts:
            mnx = min(p[0] for p in win_pts); mny = min(p[1] for p in win_pts); mnz = min(p[2] for p in win_pts)
            sig = tuple(sorted((p[0]-mnx, p[1]-mny, p[2]-mnz) for p in win_pts))
        else:
            sig = ()
        sig_count[sig] += 1
        rec = {"nint": nint, "nanch": nanch, "arcs": arcs}
        recs.append(rec)
        if nint > max_int:
            max_int = nint; best_rec = dict(rec, q=q)
    return max_int, best_rec, sig_count, recs


anch_index = {}

def main():
    t0 = time.time()
    RHOS_PROFILE = [1,2,3,4,5,6,7,8,9,10]
    FRAC = {"4.44": F(40,9)/1, "r=4.44": None}
    # exact load-bearing radii: 4.44 and its shells
    load_r = F(40, 9)          # 4.4444...  (this is (4/9)*10)
    shell1 = F(4,9) * load_r   # tau_1 radius
    shell2 = F(4,27) * load_r  # tau_2 radius
    out = {"M": M, "note": "b_L(r)=single-level t_0 sup; anchors 3-separated (min|M.s|=3)"}
    out["packing_P(r+4)"] = {str(r): packing(r+4) for r in RHOS_PROFILE + [4.44]}

    b_by_level = {}
    for L in (6, 7, 8):
        anchors, words, interiors, int_anchor = load_level(L)
        global anch_index
        anch_index = {p: i for i, p in enumerate(anchors)}
        print("L%d loaded: %d anchors %d interiors  t=%.1f" % (L, len(anchors), len(interiors), time.time()-t0), flush=True)

        # (1) exact single-level b_L(r)
        prof = {}
        for r in RHOS_PROFILE:
            v, _ = exact_sup(interiors, r)
            prof[str(r)] = v
        # fractional load-bearing radii (exact rational -> float for box)
        for name, rr in (("4.4444", float(load_r)), ("shell1_1.9753", float(shell1)), ("shell2_0.6584", float(shell2))):
            v, _ = exact_sup(interiors, rr)
            prof[name] = v
        b_by_level["L%d" % L] = prof
        print("   b_L profile:", prof, flush=True)

        # (2)+(3) config analysis at load-bearing r=4.44 (window r+4=8.44) and r=10
        cfg = {}
        for r in (float(load_r), 4.0, 10.0):
            centres = interiors  # centre balls at interior points (representative)
            mx, best, sig_count, recs = analyze_configs(anchors, interiors, int_anchor, r, centres)
            # summary of window occupancy vs packing
            import statistics as st
            nanch_list = [rr["nanch"] for rr in recs]
            arcs_list = [rr["arcs"] for rr in recs]
            nint_list = [rr["nint"] for rr in recs]
            # among the top-crowding centres, what are nanch/arcs?
            recs_sorted = sorted(recs, key=lambda z: -z["nint"])[:50]
            cfg["r=%.4f" % r] = {
                "window_r+4": r + 4,
                "packing_P(r+4)": packing(r + 4),
                "max_interiors_at_int_centre": mx,
                "distinct_anchor_configs": len(sig_count),
                "n_centres": len(centres),
                "max_nanch_in_window": max(nanch_list),
                "mean_nanch_in_window": round(sum(nanch_list)/len(nanch_list), 2),
                "max_arcs": max(arcs_list),
                "mean_arcs": round(sum(arcs_list)/len(arcs_list), 2),
                "top50_by_interiors": [
                    {"nint": z["nint"], "nanch": z["nanch"], "arcs": z["arcs"]} for z in recs_sorted[:15]
                ],
            }
            print("   r=%.4f config: maxint=%d distinct_cfg=%d max_nanch=%d(pack %d) max_arcs=%d  t=%.1f"
                  % (r, mx, len(sig_count), max(nanch_list), packing(r+4), max(arcs_list), time.time()-t0), flush=True)
        out.setdefault("config_analysis", {})["L%d" % L] = cfg

    out["b_by_level"] = b_by_level
    # load-bearing telescoped sum per level using tau_0=b(4.44), tau_1=b(1.975), tau_2=b(0.658)
    lb = {}
    for L in (6,7,8):
        p = b_by_level["L%d" % L]
        s = p["4.4444"] + p["shell1_1.9753"] + p["shell2_0.6584"] + 1
        lb["L%d" % L] = {"tau0_b(4.44)": p["4.4444"], "tau1_b(1.975)": p["shell1_1.9753"],
                          "tau2_b(0.658)": p["shell2_0.6584"], "deep_tail": 1,
                          "telescoped_sum_c(4.44)_bound": s}
    out["load_bearing_c(4.44)"] = lb
    out["elapsed_sec"] = round(time.time() - t0, 1)
    json.dump(out, open("design/lemma/automaton/bound2_results.json", "w"), indent=2)
    print("\nLOAD-BEARING:", json.dumps(lb, indent=2))
    print("DONE t=%.1f" % (time.time()-t0))


if __name__ == "__main__":
    main()
