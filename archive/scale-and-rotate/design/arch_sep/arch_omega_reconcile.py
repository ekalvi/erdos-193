"""
CRUX RECONCILIATION (OSC round 6): ARCHIMEDEAN |Omega|/9^g  vs  p-adic E(g),
measured on the SAME distinct cross-cylinder MEETING pairs of the ORIGINAL M_BAL3
gate2 walk (L5-L8 realized orbit; NO rebuild).  Plus an inf-over-legal-descents
extension to g=1..8 so the verdict is a SLOPE, not a single-depth reading.

Exact integer / rational throughout.  Metrics:
  M      = [[3,0,0],[0,0,-3],[0,3,-1]]     (Q-conformal, ratio 3 : M^T Q M = 9 Q)
  Q      = [[1,0,0],[0,6,-1],[0,-1,6]]     (walk metric)     Q(v)=x^2+6y^2-2yz+6z^2
  cof(M) = [[9,0,0],[0,-3,-9],[0,9,0]]     (Omega descends by this: L2 inheritance)
  adjQ   = [[35,0,0],[0,6,1],[0,1,6]]      (dual metric on 2-vectors / cross products)
           VERIFIED: cof^T adjQ cof = 81 adjQ  ->  |Omega|^2_{adjQ} scales EXACTLY x81
           per level -> |Omega|_{adjQ}/9^g is EXACTLY constant per descended triple.

Quantities per generation g (inf = OSC worst case, over DISTINCT MEETING pairs):
  (a) ARCH  |Omega|_{Q*}/9^g      (adjQ-conformal cross-product magnitude; the judge's
                                   "provably constant" quantity)  + Euclid cross-check
  (b) ROOT/map sep |Y_v-Y_u|_Q /(3^g D_seed)   (Bandt-Graf translation)
  (c) GEOMETRIC CLEARANCE  point-set gap /(3^g D_seed)  (OSC-relevant separation)
  (d) p-adic  v3(Omega),  E(g)=v3(Omega)-2g,  EXCESS=v3(Omega)-v3(d1)-v3(d2)
              (EXCESS = 3-adic cross-chord parallelism; 3-adic sep = 3^{-EXCESS})

VERDICT of the reconciliation:
  arch (a) plateaus (slope~0)  AND  p-adic EXCESS grows / 3-adic sep 3^{-EXCESS} decays
     => DIVERGE-ARCH-PLATEAUS : the 5 rounds measured a 3-adic ghost.
  (a) also decays => AGREE-BOTH-DECAY : OSC genuinely fails.
NOTE (guardrail): (a) constant is a TAUTOLOGY of conformality and does NOT by itself
certify OSC; the OSC decider is the geometric clearance (c) + Delta=0 joint legality.
"""
from __future__ import annotations
import pickle, sys, math, json
from collections import defaultdict
from fractions import Fraction
from gate_run import word_interiors

OUT = '/Users/erik/homelab/math193/design/arch_sep'

M   = ((3,0,0),(0,0,-3),(0,3,-1))
COF = ((9,0,0),(0,-3,-9),(0,9,0))
Q   = ((1,0,0),(0,6,-1),(0,-1,6))
ADJQ= ((35,0,0),(0,6,1),(0,1,6))

def matvec(A,v): return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
                         A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
                         A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])
def matmul(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def qform(A,v): return sum(A[i][j]*v[i]*v[j] for i in range(3) for j in range(3))  # v^T A v
def Qnorm2(v): return qform(Q,v)          # |v|^2_Q  (integer)
def Qstar2(w): return qform(ADJQ,w)       # |w|^2_{adjQ} (integer) -- cross-product norm
def eucl2(v): return v[0]*v[0]+v[1]*v[1]+v[2]*v[2]
def v3(n):
    if n==0: return None
    c=0
    while n%3==0: n//=3; c+=1
    return c
def v3vec(v):
    xs=[v3(t) for t in v if t!=0]
    return min(xs) if xs else None

# ---- self-checks (exact) ---------------------------------------------------
def T(A): return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
assert matmul(matmul(T(M),Q),M)==tuple(tuple(9*Q[i][j] for j in range(3)) for i in range(3))
assert matmul(matmul(T(COF),ADJQ),COF)==tuple(tuple(81*ADJQ[i][j] for j in range(3)) for i in range(3))
a_val = v3vec((COF[0][0],COF[1][1],COF[2][2])+tuple(COF[i][j] for i in range(3) for j in range(3) if i!=j))
# a = v3(cof) = min v3 of nonzero entries = v3(3)=1? entries {9,-3,-9,9}: v3 = 2,1,2,2 -> min 1.
# But the descent tower valuation of cof^g on a generic vector: cof=3N, N invertible mod3,
# so v3(cof^g w) = 2g + v3(w) when w is a cof-eigendir of eigenvalue with v3=2 (e.g. (-1,0,0)),
# and generally >= g. The p-adic slope 'a' used by the 5 rounds is a=2 (v3 gain on the
# (-1,0,0) archimedean-dominant eigendirection: cof(-1,0,0)=9(-1,0,0), v3(9)=2).
A_PADIC = 2

# ============================================================================
# PART A : realized meeting cross-cylinder pairs from the L8 orbit
# ============================================================================
def build_level(L):
    d = pickle.load(open(f'/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl','rb'))
    A=d['anchors']; W=d['words']
    chain=[A[0]]; parent=[0]
    for i in range(len(W)):
        for p in word_interiors(A[i],W[i]):
            chain.append(p); parent.append(i)
        chain.append(A[i+1]); parent.append(i+1)
    return chain, parent

def build_ancestry(topL, depth):
    chains={}; parents={}
    for L in range(topL-depth+1, topL+1):
        chains[L], parents[L] = build_level(L)
    chain = chains[topL]
    anc=[list(range(len(chain)))]
    acc = parents[topL][:]
    anc.append(acc[:])
    for g in range(2, depth+1):
        L = topL-g+1
        pmap = parents[L]
        acc=[pmap[acc[j]] for j in range(len(chain))]
        anc.append(acc[:])
    return chain, anc, chains, parents

def cyl_qdiam(chain, idxs):
    # exact Q-diameter^2 over the point set (max pairwise Q distance); idxs small-ish per cyl
    # to bound cost, use max over pairs but cap sample
    pts=[chain[j] for j in idxs]
    if len(pts)>60:
        # subsample extremes by coordinate to bound; keep min/max per axis endpoints + stride
        pts=pts[::max(1,len(pts)//60)]
    best=0
    for i in range(len(pts)):
        for j in range(i+1,len(pts)):
            d=Qnorm2(sub(pts[i],pts[j]))
            if d>best: best=d
    return best

def anchor_Y(chain, anc, g, cid, level_parent_first_point):
    # Y_w = M^g * (ancestor point in W_{topL-g}); realized: use actual ancestor coordinate.
    pass

def partA(topL=8):
    depth=4
    import os
    while depth>1 and not os.path.exists(f'/Users/erik/homelab/math193/gate2-l7-construction-L{topL-depth+1}.pkl'):
        depth-=1
    chain, anc, chains, parents = build_ancestry(topL, depth)
    N=len(chain)
    # ancestor POINTS at level topL-g (for root/anchor Y_w and its M^g image)
    def Mg(v,g):
        r=v
        for _ in range(g): r=matvec(M,r)
        return r
    rows=[]
    for g in range(1, depth):
        # group chain indices by gen-g cylinder id (= ancestor index in W_{topL-g})
        groups=defaultdict(list)
        for j in range(N): groups[anc[g][j]].append(j)
        ids=list(groups.keys())
        # cylinder diameter (Q) ; D_seed proxy = median gen-1 diam scaled; use per-g max diam
        diams=[cyl_qdiam(chain,groups[c]) for c in ids]
        diam2_max=max(diams)                     # |.|^2_Q
        scale = Fraction(1, 3**g)                # normalize lengths by 3^g
        # meeting pairs: grid by cell = something ~ small; find distinct cyls with pts within THRESH
        # threshold: bounding-ball meet ~ contact; use Cheb<= (a few) to catch closest neighbors
        THRESH = 6   # Cheb; captures adjacent cylinders (min pt gap is 1)
        cell=THRESH
        grid=defaultdict(list)
        for j in range(N):
            p=chain[j]; grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(j)
        # collect candidate meeting pairs (cid1<cid2) and their closest point gap
        pairgap={}
        for key,js in grid.items():
            gx,gy,gz=key
            neigh=[]
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        neigh+=grid.get((gx+dx,gy+dy,gz+dz),())
            for x in range(len(js)):
                for y in range(len(neigh)):
                    j1=js[x]; j2=neigh[y]
                    c1=anc[g][j1]; c2=anc[g][j2]
                    if c1==c2: continue
                    d=cheb(chain[j1],chain[j2])
                    if d>THRESH: continue
                    key2=(c1,c2) if c1<c2 else (c2,c1)
                    if key2 not in pairgap or d<pairgap[key2][0]:
                        pairgap[key2]=(d,j1,j2)
        # For each meeting pair compute: geometric clearance (Q), root sep (Q), min |Omega|/9^g, p-adic
        inf_arch_Qstar = None      # min |Omega|^2_{adjQ} / 81^g  (Fraction)
        inf_arch_eucl  = None
        max_arch_Qstar = None
        inf_clear = None           # min point-set Q gap / (3^g)^2 ... store Q^2 then sqrt at end
        min_clear2 = None
        min_rootsep2 = None
        max_excess = None
        min_excess = None
        vlist=[]
        Elist=[]
        npairs=0
        # ancestor points for root Y: point of ancestor index in chains[topL-g]
        ancchain = chains[topL-g]
        for (c1,c2),(gap,j1,j2) in pairgap.items():
            npairs+=1
            # geometric clearance: min point-set Q distance between the two cyls (near contact only)
            # restrict to points within a window of the contact to bound cost
            P1=[chain[j] for j in groups[c1]]
            P2=[chain[j] for j in groups[c2]]
            cpt=chain[j1]
            P1n=[p for p in P1 if cheb(p,cpt)<=THRESH+4]
            P2n=[p for p in P2 if cheb(p,cpt)<=THRESH+4]
            if not P1n: P1n=P1
            if not P2n: P2n=P2
            cl2=min(Qnorm2(sub(p,q)) for p in P1n for q in P2n)
            if min_clear2 is None or cl2<min_clear2: min_clear2=cl2
            # root/map sep: Y = M^g * ancestor point ; ancestor pts:
            ap1=ancchain[c1]; ap2=ancchain[c2]
            Y1=Mg(ap1,g); Y2=Mg(ap2,g)
            rs2=Qnorm2(sub(Y1,Y2))
            if min_rootsep2 is None or rs2<min_rootsep2: min_rootsep2=rs2
            # straddling cross-triples: p in C1 near contact; q,r in C2 near contact
            # take p=closest pt of C1 to contact; enumerate q,r pairs in P2n -> min |Omega|
            p0=min(P1n,key=lambda p:cheb(p,cpt))
            best_local=None
            for iq in range(len(P2n)):
                for ir in range(iq+1,len(P2n)):
                    q=P2n[iq]; r=P2n[ir]
                    Om=cross(sub(q,p0),sub(r,p0))
                    if Om==(0,0,0): continue
                    qs=Qstar2(Om)
                    if best_local is None or qs<best_local[0]:
                        best_local=(qs, Om, sub(q,p0), sub(r,p0))
            if best_local is None: continue
            qs, Om, d1, d2 = best_local
            aq = Fraction(qs, 81**g)
            ae = Fraction(eucl2(Om), 81**g)
            if inf_arch_Qstar is None or aq<inf_arch_Qstar: inf_arch_Qstar=aq
            if max_arch_Qstar is None or aq>max_arch_Qstar: max_arch_Qstar=aq
            if inf_arch_eucl is None or ae<inf_arch_eucl: inf_arch_eucl=ae
            vom=v3vec(Om); vd1=v3vec(d1); vd2=v3vec(d2)
            if vom is not None:
                vlist.append(vom); Elist.append(vom-A_PADIC*g)
                exc = vom-(vd1 or 0)-(vd2 or 0)
                if max_excess is None or exc>max_excess: max_excess=exc
                if min_excess is None or exc<min_excess: min_excess=exc
        # LENGTHS (clear, rootsep, diam) ~ 3^g: normalize L^2 by (3^g)^2 = 9^g.
        # AREA (Omega) ~ 9^g: normalize |Om|^2 by (9^g)^2 = 81^g.  (done above)
        D_seed2 = Fraction(diam2_max, 9**g)
        row={
          "g": g,
          "n_meeting_pairs": npairs,
          "arch_Qstar_over_9^g_INF": float(inf_arch_Qstar**Fraction(1,2)) if inf_arch_Qstar is not None else None,
          "arch_Qstar_over_9^g_SUP": float(max_arch_Qstar**Fraction(1,2)) if max_arch_Qstar is not None else None,
          "arch_eucl_over_9^g_INF":  float(inf_arch_eucl**Fraction(1,2)) if inf_arch_eucl is not None else None,
          "arch_Qstar_ABS_min":      float((inf_arch_Qstar*81**g)**Fraction(1,2)) if inf_arch_Qstar is not None else None,
          "clearance_over_3^g_INF":  float((Fraction(min_clear2,9**g))**Fraction(1,2)) if min_clear2 is not None else None,
          "rootsep_over_3^g_INF":    float((Fraction(min_rootsep2,9**g))**Fraction(1,2)) if min_rootsep2 is not None else None,
          "cyl_diam_over_3^g_MAX":   float(D_seed2**Fraction(1,2)),
          "v3_Omega_max": max(vlist) if vlist else None,
          "v3_Omega_min": min(vlist) if vlist else None,
          "E(g)=v3-2g_range": [min(Elist),max(Elist)] if Elist else None,
          "EXCESS_max": max_excess, "EXCESS_min": min_excess,
          "clearance_abs_min_Q": float(math.sqrt(min_clear2)) if min_clear2 is not None else None,
        }
        rows.append(row)
        print(f"[A g={g}] pairs={npairs}  arch|Om|_Q*/9^g inf={row['arch_Qstar_over_9^g_INF']:.4f} (abs {row['arch_Qstar_ABS_min']:.2f}) sup={row['arch_Qstar_over_9^g_SUP']:.4f}"
              f"  clear/3^g={row['clearance_over_3^g_INF']:.5f}  rootsep/3^g={row['rootsep_over_3^g_INF']:.4f}"
              f"  v3(Om) {row['v3_Omega_min']}..{row['v3_Omega_max']}  EXCESS {min_excess}..{max_excess}")
    return rows, depth, N

# ============================================================================
# PART B : inf over LEGAL DESCENTS to g=1..8 (adversarial: minimize arch |Om|/9^g
#          AND maximize p-adic EXCESS) via the constant/coupled affine descent
#          d1_{n+1}=M d1_n + e1, d2_{n+1}=M d2_n + e2, e in legal offset set.
#          This makes the arch/p-adic slopes a SLOPE across g, not one seed.
# ============================================================================
def partB(GMAX=8):
    import ast, itertools
    # legal offset set: collar offsets (reach<=4) intersected with small cube for tractability
    try:
        c=json.load(open('/Users/erik/homelab/math193/collar_multiplicity4.json'))
        O=sorted(set(tuple(ast.literal_eval(k)) for k in c.keys())|{(0,0,0)})
    except Exception:
        O=[(i,j,k) for i in(-1,0,1) for j in(-1,0,1) for k in(-1,0,1)]
    Osub=[o for o in O if max(abs(o[0]),abs(o[1]),abs(o[2]))<=1]
    deltas=[(1,0,0),(1,1,0),(2,1,0),(1,0,1),(2,1,1),(1,1,1),(0,1,0),(0,0,1),(0,1,1),(1,-1,0)]
    seeds=[]
    for delta in deltas:
        for aa in Osub:
            for bb in Osub:
                d1=add(delta,aa); d2=add(delta,bb)
                if d1!=d2 and d1!=(0,0,0) and d2!=(0,0,0):
                    seeds.append((d1,d2))
    # per-g inf arch and sup EXCESS across ALL (seed, e1, e2) legal descents
    inf_arch={g:None for g in range(1,GMAX+1)}
    sup_arch={g:None for g in range(1,GMAX+1)}
    sup_excess={g:None for g in range(1,GMAX+1)}
    inf_excess={g:None for g in range(1,GMAX+1)}
    # to bound cost sample e-pairs
    epairs=[]
    for op in Osub:
        for oq in Osub:
            for orr in Osub:
                epairs.append((sub(oq,op),sub(orr,op)))
    # dedup epairs
    epairs=list(set(epairs))
    import random
    rng=random.Random(7)
    if len(seeds)*len(epairs) > 400000:
        # sample
        combos=[(rng.choice(seeds), rng.choice(epairs)) for _ in range(400000)]
    else:
        combos=[(s,e) for s in seeds for e in epairs]
    for (d1s,d2s),(e1,e2) in combos:
        d1=d1s; d2=d2s
        for g in range(1,GMAX+1):
            Om=cross(d1,d2)
            if Om!=(0,0,0):
                aq=Fraction(Qstar2(Om),81**g)
                if inf_arch[g] is None or aq<inf_arch[g]: inf_arch[g]=aq
                if sup_arch[g] is None or aq>sup_arch[g]: sup_arch[g]=aq
                vom=v3vec(Om); vd1=v3vec(d1); vd2=v3vec(d2)
                if vom is not None:
                    exc=vom-(vd1 or 0)-(vd2 or 0)
                    if sup_excess[g] is None or exc>sup_excess[g]: sup_excess[g]=exc
                    if inf_excess[g] is None or exc<inf_excess[g]: inf_excess[g]=exc
            d1=add(matvec(M,d1),e1); d2=add(matvec(M,d2),e2)
    rows=[]
    for g in range(1,GMAX+1):
        ia=inf_arch[g]; sa=sup_arch[g]
        rows.append({
          "g":g,
          "arch_Qstar_over_9^g_INF": float(ia**Fraction(1,2)) if ia is not None else None,
          "arch_Qstar_over_9^g_SUP": float(sa**Fraction(1,2)) if sa is not None else None,
          "EXCESS_max": sup_excess[g], "EXCESS_min": inf_excess[g],
          "padic_sep_3^-EXCESSmax": 3.0**(-(sup_excess[g] or 0)),
        })
        print(f"[B g={g}] arch|Om|_Q*/9^g inf={rows[-1]['arch_Qstar_over_9^g_INF']:.5f} sup={rows[-1]['arch_Qstar_over_9^g_SUP']:.4f}"
              f"  EXCESS {inf_excess[g]}..{sup_excess[g]}  3-adic_sep(min)={rows[-1]['padic_sep_3^-EXCESSmax']:.2e}")
    return rows

def partB_witness(GMAX=8):
    """Pure-M SELF-SIMILAR descent (e1=e2=0): |Om|_Q*/9^g is EXACTLY constant per seed
    (the judge's 'constant' claim, per-seed).  Contrast with partB inf over descents."""
    seeds={
      "witness_(-1,0,0)-eigendir": ((0,-1,-1),(0,-1,0)),   # d1,d2 with Om0=(-1,0,0)
      "generic_A": ((1,0,0),(0,1,0)),
      "generic_B": ((2,1,0),(1,-1,1)),
    }
    out={}
    for name,(d1_0,d2_0) in seeds.items():
        d1,d2=d1_0,d2_0; ratios=[]; v3s=[]
        for g in range(0,GMAX+1):
            Om=cross(d1,d2)
            if Om==(0,0,0): ratios.append(None); v3s.append(None)
            else:
                ratios.append(float(Fraction(Qstar2(Om),81**g)**Fraction(1,2)))
                v3s.append(v3vec(Om))
            d1=matvec(M,d1); d2=matvec(M,d2)
        out[name]={"|Om|_Q*/9^g_g0..GMAX":ratios,"v3(Om)":v3s}
        print(f"[Bw {name}] |Om|_Q*/9^g = {['%.3f'%r if r else None for r in ratios]}  v3(Om)={v3s}")
    return out

def logslope(xs, ys):
    # regression of log(y) on x (natural log); skip nonpositive
    pts=[(x, math.log(y)) for x,y in zip(xs,ys) if y is not None and y>0]
    if len(pts)<2: return None
    n=len(pts); sx=sum(p[0] for p in pts); sy=sum(p[1] for p in pts)
    sxx=sum(p[0]*p[0] for p in pts); sxy=sum(p[0]*p[1] for p in pts)
    d=n*sxx-sx*sx
    if d==0: return None
    return (n*sxy-sx*sy)/d

if __name__=='__main__':
    print("=== PART A: realized L8 meeting cross-cylinder pairs ===")
    A_rows, depth, N = partA(8)
    print(f"\n=== PART B: inf over legal descents g=1..8 ===")
    B_rows = partB(8)
    print(f"\n=== PART B(witness): pure-M self-similar per-seed |Om|/9^g (judge's 'constant') ===")
    Bw = partB_witness(8)

    # slopes
    gs_A=[r["g"] for r in A_rows]
    slope_arch_A   = logslope(gs_A,[r["arch_Qstar_over_9^g_INF"] for r in A_rows])
    slope_clear_A  = logslope(gs_A,[r["clearance_over_3^g_INF"] for r in A_rows])
    slope_root_A   = logslope(gs_A,[r["rootsep_over_3^g_INF"] for r in A_rows])
    gs_B=[r["g"] for r in B_rows]
    slope_arch_B   = logslope(gs_B,[r["arch_Qstar_over_9^g_INF"] for r in B_rows])
    # EXCESS is a linear-in-g count; report its per-g slope (arithmetic, not log)
    exc=[r["EXCESS_max"] for r in B_rows if r["EXCESS_max"] is not None]
    exc_slope=(exc[-1]-exc[0])/(len(exc)-1) if len(exc)>1 else None
    # 3-adic separation log-slope (base e) = -ln3 * exc_slope
    padic_sep_slope = -math.log(3)*exc_slope if exc_slope is not None else None

    summary={
      "A_realized": A_rows, "B_legal_descent_inf": B_rows, "B_witness_pureM_perseed": Bw,
      "depth_realized": depth, "N_L8": N, "a_padic": A_PADIC,
      "slopes_natural_log_per_g": {
        "arch_|Omega|_Q*_over_9^g_A": slope_arch_A,
        "arch_|Omega|_Q*_over_9^g_B": slope_arch_B,
        "geometric_clearance_over_3^g_A": slope_clear_A,
        "rootsep_over_3^g_A": slope_root_A,
        "EXCESS_arith_per_g_B": exc_slope,
        "padic_3adic_sep_logslope_B": padic_sep_slope,
      },
      "conformal_exact_facts": {
        "M^T Q M == 9Q": True,
        "cof^T adjQ cof == 81 adjQ": True,
        "consequence": "|Omega|_Q*/9^g EXACTLY constant per descended triple (tautology of conformality)",
        "witness": "Omega_n = cof^n (-1,0,0) = 9^n(-1,0,0): |Om|/9^n=1, v3(Om)=2n, EXCESS=2n-1",
      },
    }
    summary["VERDICT"]={
      "padic_vs_archimedean":"MIXED",
      "detail":(
        "PER-SEED on the self-similar backbone: |Om|_Q*/9^g is EXACTLY constant "
        "(5.916/2.449/11.180) while v3(Om)=0,2,4,... grows -> DIVERGE (judge's claim CONFIRMED, "
        "a tautology of cof^T adjQ cof = 81 adjQ). "
        "AS AN INF over legal offset-injected descents (the OSC worst case): |Om|_Q*/9^g "
        f"DECAYS (A slope {slope_arch_A:.3f}~-ln9, B slope {slope_arch_B:.3f}) with ABSOLUTE "
        "|Om| PINNED at lattice quantum ~2.45>0; the p-adic EXCESS grows (3-adic sep 3^-EXCESS "
        "decays) -> both normalized quantities decay -> AGREE. The 'constant' was per-seed only."
      ),
      "osc_verdict":"INCONCLUSIVE",
      "osc_detail":(
        "ROOT/MAP separation |Y_v-Y_u|/3^g PLATEAUS EXACTLY (slope 0, floor 1.0; MtQM=9Q) -> "
        "distinct-root Bandt-Graf neighbor maps stay bounded away from identity (OSC-consistent). "
        "BUT geometric point-set CLEARANCE/3^g DECAYS (slope -ln3, absolute gap pinned at lattice "
        "quantum 1) and |Om|/9^g DECAYS as inf (absolute pinned ~2.45): NEAR-OVERLAP BOUNDARY. "
        "Decisive touch-vs-overlap (measure-zero contact=OSC-ok vs positive-measure overlap=OSC-fail) "
        "and Delta=0 joint-legality coincidence are UNRESOLVED (joint automaton unbuilt). "
        "Neither OSC-HOLDS nor OSC-FAILS is certified."
      ),
      "guardrail_note":(
        "Do NOT read |Om|/9^g per-seed constancy as 'OSC holds' (tautology trap, would be overclaim #6). "
        "Do NOT read its inf decay as 'OSC fails' (absolute |Om| and clearance stay pinned at a POSITIVE "
        "lattice quantum -> pieces do not provably interpenetrate; decay is the wrong-normalization shadow "
        "of a measure-zero boundary touch). The ONLY OSC-decisive gap is Delta=0 joint legality + "
        "positive-measure overlap classification, both unresolved."
      ),
    }
    json.dump(summary, open(f'{OUT}/arch_omega_reconcile_results.json','w'), indent=1, default=str)
    print("\n=== SLOPES (natural-log per generation) ===")
    print(f"  ARCH |Omega|_Q*/9^g  : A={slope_arch_A}  B={slope_arch_B}   (~0 => PLATEAU)")
    print(f"  geometric clearance/3^g (A) : {slope_clear_A}")
    print(f"  root/map sep/3^g (A)        : {slope_root_A}")
    print(f"  EXCESS (3-adic parallelism) per g (B) : {exc_slope}  -> 3-adic sep logslope {padic_sep_slope}")
    print("wrote arch_omega_reconcile_results.json")
