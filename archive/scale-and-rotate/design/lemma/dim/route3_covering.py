"""
ROUTE 3 -- DIRECT BOX-COVERING INDUCTION for the core lemma
    c_k(q,r) <= C * r^d  on r in [1,10], uniform in k,   d = log(lambda)/log(3).

Program of this script (all EXACT integer arithmetic on the constructed walks):

(A) Global self-affine constants (rigorous inputs):
      lambda = N_{k+1}/N_k (point growth),   extent-ratio = det(M)^{1/3} = 3 EXACT
      (M elliptic, all eigenvalue moduli = 3),  d = log(lambda)/log(3).

(B) COVERING-NUMBER INDUCTION STEP, measured.
    W_{k+1} = M.W_k  (DISJOINT-UNION)  Stitch_k.
    Claim of the step: a side-r box cover of W_k pushes forward under M to a
    side-3r box cover of M.W_k with a BOUNDED-DISTORTION blow-up kappa
    (#side-3r boxes to cover M.(side-r box) <= kappa), and the stitch refills
    each anchor-edge with a BOUNDED number of extra side-3r boxes.  So
        N_{3r}(W_{k+1}) <= kappa * N_r(W_k) + refill.
    We MEASURE:
      - kappa_M := max over occupied side-r cells of #{side-3r cells covering M.cell}
        (the M box-distortion constant; should be O(1), not growing);
      - N_b(W_k) box counts and the per-3x-scale ratio N_b/N_{3b} (-> lambda if
        the cover multiplies by lambda per 3x scale => dimension d);
      - the stitch refill increment  N_{3r}(W_{k+1}) - N_{3r}(M.W_k).

(C) POINTS-PER-BOX (the covering->count conversion): max #walk points inside any
    side-1 (unit) box.  Bounded => c_k(q,r) <= (pts/box) * N_1(ball).

(D) DIRECT FIT of the target:  smallest C with c_k(q,r) <= C*r^d for r in [1,10]
    per level; the binding r; and the AVAILABILITY check at the load-bearing
    r=4.44  (integer-lattice: Cheb<=4.44 <=> Cheb<=4, so c(q,4.44)=c(q,4)).
"""
import pickle, math, json, sys
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3

def matvec(m, v):
    return (m[0][0]*v[0]+m[0][1]*v[1]+m[0][2]*v[2],
            m[1][0]*v[0]+m[1][1]*v[1]+m[1][2]*v[2],
            m[2][0]*v[0]+m[2][1]*v[1]+m[2][2]*v[2])

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

def occ_cells(pts, b):
    s = set()
    for p in pts:
        s.add((p[0]//b, p[1]//b, p[2]//b))
    return s

def boxcount(pts, b):
    return len(occ_cells(pts, b))

def local_c(chain, rho):
    """worst-case c_k(q,rho): max #chain points within Cheb-rho of ANY chain point
    (empty balls give 0; the sup is realised at/next to a chain point)."""
    grid = defaultdict(list)
    cell = rho + 1
    for idx, p in enumerate(chain):
        grid[(p[0]//cell, p[1]//cell, p[2]//cell)].append(idx)
    def neigh(p):
        cx, cy, cz = p[0]//cell, p[1]//cell, p[2]//cell
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    out.extend(grid.get((cx+dx, cy+dy, cz+dz), ()))
        return out
    maxc = 0
    for q in chain:
        cnt = sum(1 for j in neigh(q) if cheb(q, chain[j]) <= rho)
        if cnt > maxc:
            maxc = cnt
    return maxc

def pts_per_unit_box(chain):
    """max #chain points sharing one side-1 (unit) integer cell -> here trivially 1
    (distinct lattice pts each own their unit cell); the meaningful conversion const
    is max pts in a Cheb-1 BALL, = local_c(chain,1)."""
    return boxcount(chain, 1), len(chain)

if __name__ == "__main__":
    pkls = {"L5": "gate2-l7-construction-L5.pkl",
            "L6": "gate2-l7-construction-L6.pkl",
            "L7": "gate2-l7-construction-L7.pkl",
            "L8": "gate2-l7-construction-L8.pkl"}
    out = {}
    chains = {}
    order = ["L5", "L6", "L7", "L8"]
    for lvl in order:
        chains[lvl] = build_chain(pkls[lvl])

    # ---- (A) global constants ----
    A = {}
    prevN = prevE = None
    for lvl in order:
        ch = chains[lvl]
        N = len(ch); E = extent(ch)
        lam = N/prevN if prevN else None
        er = E/prevE if prevE else None
        d = math.log(lam)/math.log(3) if lam else None   # extent-ratio = 3 EXACT
        A[lvl] = dict(N=N, extent=E, lam=lam, extent_ratio=er,
                      d_from_lam=(math.log(lam)/math.log(3) if lam else None))
        prevN, prevE = N, E
    out["A_global"] = A
    # canonical d from L7->L8 lambda
    lam_final = A["L8"]["lam"]
    d = math.log(lam_final)/math.log(3)
    out["d"] = d
    print(f"[A] lambda(L7->L8)={lam_final:.5f}  d=log(lambda)/log3={d:.5f}  extent-ratio=3 (exact)")

    # ---- (B) covering-number induction step: M-distortion + per-scale ratio + refill ----
    B = {}
    for lvl in order:
        ch = chains[lvl]
        E = extent(ch)
        bc = {}
        b = 1
        while b <= E:
            bc[b] = boxcount(ch, b)
            b *= 3
        keys = sorted(bc)
        # per-3x ratio N_b / N_{3b}  (should approach lambda in the fractal regime)
        ratios = {}
        for i in range(len(keys)-1):
            ratios[keys[i]] = bc[keys[i]]/bc[keys[i+1]]
        B[lvl] = dict(boxcount={str(k): bc[k] for k in keys},
                      ratio_Nb_over_N3b={str(keys[i]): round(ratios[keys[i]], 4)
                                         for i in range(len(keys)-1)})
    out["B_boxcount"] = B

    # M-distortion kappa_M and stitch refill: transfer W_{k-1} -> W_k
    step = {}
    for prev, cur in [("L5", "L6"), ("L6", "L7"), ("L7", "L8")]:
        chp = chains[prev]; chc = chains[cur]
        MW = [matvec(M, p) for p in chp]           # M . W_{k-1}
        # kappa_M: cover each occupied side-r cell's image by side-3r cells, take max
        for r in (1, 2, 3):
            cells = defaultdict(list)
            for p in chp:
                cells[(p[0]//r, p[1]//r, p[2]//r)].append(p)
            kappa = 0
            for cell, members in cells.items():
                img = set()
                for p in members:
                    q = matvec(M, p)
                    img.add((q[0]//(3*r), q[1]//(3*r), q[2]//(3*r)))
                if len(img) > kappa:
                    kappa = len(img)
            step.setdefault(cur, {})[f"kappa_M_r{r}"] = kappa
        # refill increment at scale 3r for r=1,2,3  (side 3,6,9)
        for r in (1, 2, 3):
            n_MW = boxcount(MW, 3*r)
            n_W = boxcount(chc, 3*r)
            # verify M.W_{k-1} subset W_k (birth partition => yes as a set)
            setMW = occ_cells(MW, 3*r); setW = occ_cells(chc, 3*r)
            step[cur][f"refill_incr_side{3*r}"] = n_W - n_MW
            step[cur][f"N_side{3*r}_MW"] = n_MW
            step[cur][f"N_side{3*r}_W"] = n_W
            step[cur][f"MW_subset_W_side{3*r}"] = setMW.issubset(setW)
        # stitch point count vs anchor-edge count
        nstitch = len(chc) - len(chp)   # not exact set-diff but birth increment proxy
        step[cur]["birth_point_increment"] = nstitch
    out["B_induction_step"] = step
    print("[B] induction step (kappa_M, refill):")
    for cur in step:
        print(f"   {cur}: kappa_M_r1={step[cur]['kappa_M_r1']} r2={step[cur]['kappa_M_r2']} "
              f"r3={step[cur]['kappa_M_r3']}  refill_side3={step[cur]['refill_incr_side3']} "
              f"MWsubW={step[cur]['MW_subset_W_side3']}")

    # ---- (C) points-per-box conversion ----
    C_conv = {}
    for lvl in order:
        n1, N = pts_per_unit_box(chains[lvl])
        C_conv[lvl] = dict(unit_boxes=n1, points=N, all_distinct=(n1 == N),
                           c_at_r1=local_c(chains[lvl], 1))
    out["C_conversion"] = C_conv
    print(f"[C] all points distinct in unit cells: "
          f"{all(C_conv[l]['all_distinct'] for l in order)}; "
          f"c(q,1) (pts in Cheb-1 ball) L8={C_conv['L8']['c_at_r1']}")

    # ---- (D) direct fit c_k <= C r^d and availability at r=4.44 ----
    D = {}
    cvals = {}
    for lvl in order:
        cv = {r: local_c(chains[lvl], r) for r in range(1, 11)}
        cvals[lvl] = cv
    # per-level C = max_r c(r)/r^d, and binding r
    for lvl in order:
        cv = cvals[lvl]
        ratios = {r: cv[r]/(r**d) for r in range(1, 11)}
        Cbind = max(ratios.values())
        argr = max(range(1, 11), key=lambda r: ratios[r])
        D[lvl] = dict(c=cv, C_for_rd=Cbind, binding_r=argr,
                      c_at_4p44=cv[4],  # Cheb<=4.44 == Cheb<=4 on lattice
                      Crd_ratios={r: round(ratios[r], 3) for r in range(1, 11)})
    out["D_fit"] = D
    # availability: measured load-bearing c(4.44)=c(4); threshold 12
    c444 = {lvl: cvals[lvl][4] for lvl in order}
    # smallest C that is a VALID upper bound over ALL r in [1,10] AND all levels
    Cvalid = max(D[lvl]["C_for_rd"] for lvl in order)
    argr_valid = max(order, key=lambda l: D[l]["C_for_rd"])
    Crd_at444_with_Cvalid = Cvalid * (4.44**d)
    # smallest C that a bound needs at r=4.44 alone to cover measured c(4)
    C_needed_444 = max(c444.values()) / (4.44**d)
    out["availability"] = dict(
        d=d, threshold=12,
        measured_c_4p44_by_level=c444,
        Cvalid_over_full_range=Cvalid, binding_level=argr_valid,
        binding_r=D[argr_valid]["binding_r"],
        Crd_at_4p44_using_Cvalid=Crd_at444_with_Cvalid,
        C_needed_at_4p44_alone=C_needed_444,
        note_C2=dict(C=2.0, C2_rd_at_4p44=2.0*(4.44**d),
                     is_valid_upper_bound_at_4p44=(2.0*(4.44**d) >= max(c444.values()))))
    print(f"[D] d={d:.4f}")
    for lvl in order:
        print(f"   {lvl}: C(c<=C r^d)={D[lvl]['C_for_rd']:.3f} @r={D[lvl]['binding_r']}  "
              f"c(4.44)=c(4)={D[lvl]['c_at_4p44']}")
    print(f"[avail] measured c(4.44) by level = {c444}  (threshold 12)")
    print(f"[avail] valid C over full range = {Cvalid:.3f} (binding {argr_valid} @ r={D[argr_valid]['binding_r']})")
    print(f"[avail] C*r^d at 4.44 with that valid C = {Crd_at444_with_Cvalid:.2f}  (>=12? => over threshold)")
    print(f"[avail] C=2 gives 2*4.44^d = {2.0*(4.44**d):.2f}; valid upper bound of measured {max(c444.values())}? "
          f"{2.0*(4.44**d) >= max(c444.values())}")

    json.dump(out, open("design/lemma/dim/route3-covering-results.json", "w"), indent=1)
    print("\nwrote design/lemma/dim/route3-covering-results.json")
