"""
ROUTE 3 core: decompose every ball's walk-points into contiguous PATH-ARCS and
bound the two separation quantities a linear cap needs, UNIFORMLY across levels.

  c(q,rho) = sum over path-arcs in B(q,rho) of (arc length).
  Linear bound:  c <= (#arcs) * (max arc length).

We measure, over ALL centers q = walk points, for each level and rho in [1,10]:
  A(rho) = max #arcs          ("return count": how many separate path-visits")
  L(rho) = max arc length     ("sojourn": longest single pass staying in the ball")
  and max_c directly, to see how loose (#arcs)*(maxarclen) is vs reality.

Also W(d) = max path-gap |i-j| over pairs with Cheb(p_i,p_j) <= d  (recurrence window),
the alternative single-quantity bound c(q,rho) <= W(2rho)+1  (shown to be loose).

All three levels, to test LEVEL-UNIFORMITY (the crux of the lemma).
Run: pypy3 route3_arcs.py
"""
import sys, pickle, json
from collections import defaultdict

sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_interiors


def load_chain(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl", "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = [anchors[0]]
    for i in range(len(anchors) - 1):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i + 1])
    return chain


def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))


def grid_index(chain, cell):
    g = defaultdict(list)
    for i, p in enumerate(chain):
        g[(p[0]//cell, p[1]//cell, p[2]//cell)].append(i)
    return g


def arcs_of(idxs):
    idxs.sort()
    arcs = []
    cur = [idxs[0]]
    for a in idxs[1:]:
        if a == cur[-1] + 1:
            cur.append(a)
        else:
            arcs.append(cur); cur = [a]
    arcs.append(cur)
    return arcs


def analyze_level(level):
    chain = load_chain(level)
    N = len(chain)
    per_rho = {}
    for rho in range(1, 11):
        cell = rho
        grid = grid_index(chain, cell)
        maxc = 0; argmaxc = None
        maxA = 0; argA = None          # max #arcs
        maxL = 0; argL = None          # max arc length
        # to bound product cleanly, also track max over centers of A*L for that center
        worst_prod = 0
        for qi, q in enumerate(chain):
            cx, cy, cz = q[0]//cell, q[1]//cell, q[2]//cell
            idxs = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j in grid.get((cx+dx, cy+dy, cz+dz), ()):
                            if cheb(chain[j], q) <= rho:
                                idxs.append(j)
            c = len(idxs)
            if c > maxc:
                maxc = c; argmaxc = qi
            arcs = arcs_of(idxs)
            A = len(arcs)
            L = max(len(a) for a in arcs)
            if A > maxA:
                maxA = A; argA = qi
            if L > maxL:
                maxL = L; argL = qi
            if A * L > worst_prod:
                worst_prod = A * L
        per_rho[rho] = {
            "max_c": maxc,
            "max_num_arcs": maxA,
            "max_arc_len": maxL,
            "max_A_times_L_over_centers": worst_prod,
            "C_direct": round((maxc - 1) / rho, 3),
        }
    return {"level": level, "N": N, "per_rho": per_rho}


def W_windows(level, dmax=20):
    """W(d)=max path-gap among pairs with Cheb<=d. cell=dmax."""
    chain = load_chain(level)
    grid = grid_index(chain, dmax)
    Wd = {d: 0 for d in range(1, dmax + 1)}
    for i, p in enumerate(chain):
        cx, cy, cz = p[0]//dmax, p[1]//dmax, p[2]//dmax
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((cx+dx, cy+dy, cz+dz), ()):
                        if j <= i:
                            continue
                        d = cheb(p, chain[j])
                        if d <= dmax:
                            g = j - i
                            if g > Wd[d]:
                                Wd[d] = g
    # make monotone (W is nondecreasing in d): W(d)=max over d'<=d
    run = 0
    Wmono = {}
    for d in range(1, dmax + 1):
        run = max(run, Wd[d])
        Wmono[d] = run
    return Wmono


def main():
    out = {"levels": {}}
    for lv in (5, 6, 7):
        print("analyzing arcs L%d ..." % lv, flush=True)
        a = analyze_level(lv)
        print("windows L%d ..." % lv, flush=True)
        a["W_recurrence_window"] = W_windows(lv)
        out["levels"][lv] = a
        print(json.dumps(a, indent=2))
    with open("/Users/erik/homelab/math193/design/lemma/route3-arcs-all.json", "w") as f:
        json.dump(out, f, indent=2)
    # cross-level uniformity summary
    print("\n=== LEVEL-UNIFORMITY SUMMARY ===")
    print("rho | maxA(5/6/7) | maxL(5/6/7) | maxc(5/6/7) | W(2rho)(5/6/7)")
    for rho in range(1, 11):
        A = [out["levels"][lv]["per_rho"][rho]["max_num_arcs"] for lv in (5, 6, 7)]
        L = [out["levels"][lv]["per_rho"][rho]["max_arc_len"] for lv in (5, 6, 7)]
        C = [out["levels"][lv]["per_rho"][rho]["max_c"] for lv in (5, 6, 7)]
        W = [out["levels"][lv]["W_recurrence_window"].get(min(2*rho,20)) for lv in (5, 6, 7)]
        print(f"{rho:3d} | {A} | {L} | {C} | {W}")


if __name__ == "__main__":
    main()
