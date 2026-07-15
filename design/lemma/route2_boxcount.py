"""
ROUTE 2 — SELF-AFFINE BOX-COUNTING measurement for the uniform local incidence
lemma  c_k(q,rho) <= C*rho + 1  on rho in [1,10].

Measures, at L5/L6/L7/L8:
  (1) level-stable per-level growth lambda (point ratio) and Cheb-extent ratio,
      hence the box-counting exponent d = log(lambda)/log(extent-ratio).
  (2) direct box-counting: cover the walk by side-b boxes, count occupied N(b),
      slope of log N(b) vs log(1/b) = box dimension.
  (3) the WORST-CASE LOCAL count c_k(rho) = sup over integer centres, rho=1..10,
      and the arc/return decomposition:  R(rho) = max #maximal contiguous arcs of
      the path inside a Cheb-rho ball;  L(rho) = max single-arc length (sojourn).
      Tests c_k(rho) <= R(rho)*L(rho) and whether R,L,c grow ~rho (linear) vs cube.
  (4) fits c_k(rho) ~ A*rho^d and reports the C with c_k <= C*rho+1 on [1,10].
"""
import pickle, math, json
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3

def build_chain(pkl):
    d = pickle.load(open(pkl, "rb"))
    anchors = d["anchors"]; words = d["words"]
    def interiors(start, wi):
        pts = []; x, y, z = start
        for si in wi[:-1]:
            s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; pts.append((x, y, z))
        return pts
    chain = [tuple(anchors[0])]
    for i in range(len(anchors)-1):
        chain.extend(interiors(anchors[i], words[i]))
        chain.append(tuple(anchors[i+1]))
    return chain

def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

def extent(chain):
    xs = [p[0] for p in chain]; ys = [p[1] for p in chain]; zs = [p[2] for p in chain]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

def boxcount(chain, b):
    occ = set()
    for p in chain:
        occ.add((p[0]//b, p[1]//b, p[2]//b))
    return len(occ)

def local_stats(chain, rho):
    """sup over integer centres near the walk of:
       c = #walk pts in Cheb-rho ball; also the arc decomposition (R arcs, max arc len).
    Centres = every walk point (worst case is realised at/next to a walk point since
    empty balls give 0). We report max c, and for the arg-max ball its R and arcs; plus
    global max R and max arc-length over all such balls."""
    n = len(chain)
    R = rho
    grid = defaultdict(list)
    cell = R+1
    for idx, p in enumerate(chain):
        grid[(p[0]//cell, p[1]//cell, p[2]//cell)].append(idx)
    def neigh_idx(p):
        cx, cy, cz = p[0]//cell, p[1]//cell, p[2]//cell
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    out.extend(grid.get((cx+dx, cy+dy, cz+dz), ()))
        return out
    maxc = 0; maxR = 0; maxarc = 0; argc_R = 0; argc_arcs = None
    for qi in range(n):
        q = chain[qi]
        members = [j for j in neigh_idx(q) if cheb(q, chain[j]) <= rho]
        cnt = len(members)
        members.sort()
        # arcs = contiguous index runs
        arcs = []; cur = [members[0]]
        for a, b2 in zip(members, members[1:]):
            if b2 == a+1:
                cur.append(b2)
            else:
                arcs.append(cur); cur = [b2]
        arcs.append(cur)
        r = len(arcs)
        la = max(len(a) for a in arcs)
        if r > maxR: maxR = r
        if la > maxarc: maxarc = la
        if cnt > maxc:
            maxc = cnt; argc_R = r; argc_arcs = [len(a) for a in arcs]
    return maxc, maxR, maxarc, argc_R, argc_arcs

if __name__ == "__main__":
    import sys
    pkls = {"L5": "gate2-l7-construction-L5.pkl",
            "L6": "gate2-l7-construction-L6.pkl",
            "L7": "gate2-l7-construction-L7.pkl",
            "L8": "gate2-l7-construction-L8.pkl"}
    do_L8 = "--l8" in sys.argv
    if not do_L8:
        pkls.pop("L8")
    out = {}
    chains = {}
    prevN = None; prevE = None
    print("=== GROWTH / EXTENT / BOX DIMENSION ===")
    for lvl, pkl in pkls.items():
        ch = build_chain(pkl); chains[lvl] = ch
        N = len(ch); E = extent(ch)
        lam = N/prevN if prevN else float('nan')
        er = E/prevE if prevE else float('nan')
        d_from_ratio = math.log(lam)/math.log(er) if prevN and er > 1 else float('nan')
        # box counting across scales
        bc = {}
        b = 1
        while b <= E:
            bc[b] = boxcount(ch, b)
            b *= 3
        # box dim slope between successive scales (log3)
        keys = sorted(bc)
        slopes = []
        for i in range(len(keys)-1):
            b1, b2 = keys[i], keys[i+1]
            s = (math.log(bc[b1])-math.log(bc[b2]))/(math.log(b2)-math.log(b1))
            slopes.append(round(s, 3))
        print(f"{lvl}: N={N} extent={E} lambda={lam:.4f} extent_ratio={er:.4f} "
              f"d=log(lam)/log(er)={d_from_ratio:.4f}")
        print(f"     boxcount(side b)={ {k:bc[k] for k in keys} }")
        print(f"     box-dim local slopes (log3 successive)={slopes}")
        out[lvl] = dict(N=N, extent=E, lam=lam, er=er, d_ratio=d_from_ratio,
                        boxcount=bc, box_slopes=slopes)
        prevN = N; prevE = E

    print("\n=== WORST-CASE LOCAL COUNT c_k(rho), ARCS R(rho), SOJOURN L(rho) ===")
    for lvl in pkls:
        ch = chains[lvl]
        row = {}
        print(f"-- {lvl} (N={len(ch)}) --")
        print("  rho :  c    R  maxarc   c/rho  (c-1)/rho   argmax-arcs")
        for rho in range(1, 11):
            maxc, maxR, maxarc, aR, aarcs = local_stats(ch, rho)
            row[rho] = dict(c=maxc, R=maxR, maxarc=maxarc)
            print(f"  {rho:3d} : {maxc:3d}  {maxR:3d}   {maxarc:3d}   "
                  f"{maxc/rho:5.2f}   {(maxc-1)/rho:6.2f}    R@argc={aR} arcs={aarcs}")
        out.setdefault("local", {})[lvl] = row

    # fit exponent on L7 (or L8) worst-case c vs rho, and C for c<=C*rho+1
    fitlvl = "L8" if do_L8 else "L7"
    loc = out["local"][fitlvl]
    import statistics
    xs = [math.log(r) for r in range(1, 11)]
    ys = [math.log(loc[r]["c"]) for r in range(1, 11)]
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
    dfit = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/sum((x-mx)**2 for x in xs)
    Afit = math.exp(my - dfit*mx)
    Cplus1 = max((loc[r]["c"]-1)/r for r in range(1, 11))
    argC = max(range(1, 11), key=lambda r: (loc[r]["c"]-1)/r)
    print(f"\nFIT on {fitlvl}: c ~ {Afit:.3f}*rho^{dfit:.4f}")
    print(f"  power-law exponent d_fit={dfit:.4f}  (box-dim prediction ~1.10)")
    print(f"  C for c<=C*rho+1 on [1,10]:  C={Cplus1:.4f}  (binding at rho={argC})")
    print(f"  bounded-range: rho^{dfit:.3f} <= 10^{dfit-1:.3f}*rho = {10**(dfit-1):.3f}*rho")
    out["fit"] = dict(level=fitlvl, A=Afit, d=dfit, C_plus1=Cplus1, argC=argC,
                      rho_d_bound=10**(dfit-1))
    json.dump(out, open("design/lemma/route2-boxcount-results.json", "w"), indent=1)
    print("\nwrote design/lemma/route2-boxcount-results.json")
