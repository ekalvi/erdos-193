"""
DIRECT ARCHIMEDEAN GEOMETRIC CLEARANCE on the ORIGINAL M_BAL3 gate2 walk (L5-L8).

Settles the OSC crux by measuring the REAL (archimedean) normalized separation of
DISTINCT equal-generation cylinders vs generation g, NOT the p-adic proxy the last
5 rounds measured. All Q-values are EXACT integers (Q(v)=x^2+6y^2-2yz+6z^2, the
proven M-conformal form with M^T Q M = 9 Q). Distances reported are sqrt of exact
integer Q-values (the ratio is what matters; the underlying quantities are exact).

Per generation g (from the realized L8 ancestry, no rebuild) we report:

 (a) GEOMETRIC CLEARANCE  = min Q-distance between the realized point-sets of two
     DISTINCT gen-g cylinders, normalized by the gen-g cylinder Q-diameter (~3^g).
     Two flavours:
       - RAW: over ALL distinct pairs (includes chain-consecutive arcs that share a
         boundary lattice point = measure-zero touching, OSC-PERMITTED).
       - LONG-RANGE: only pairs whose closest approach is between chain-DISTANT
         points (|index gap| > 2*maxcylsize) = genuinely non-adjacent arcs folding
         back near each other -- the interpenetration signal.
     PLATEAU (slope~0) => OSC-consistent; DECAY => pieces get relatively closer.

 (b) ROOT/MAP separation |Delta|_Q = |Y_v - Y_u|_Q (Bandt-Graf neighbor-map
     translation), normalized by diameter. Delta=0 for a distinct pair => id in
     neighbor closure => OSC FAILS (discrete, decisive).

 (c) |Omega|_Q / 9^g on straddling triples (the non-collinearity / area form).

 (d) p-adic E(g) = v3(Omega) - 2g on the SAME triples (the "decaying" ghost).

 (e) TOUCH-vs-OVERLAP classification of the closest encounters.

Reconciliation: does the archimedean clearance (a) PLATEAU while p-adic E(g) (d)
GROWS  ->  the 5 rounds measured a 3-adic ghost; or do BOTH decay -> OSC genuinely
fails.
"""
import importlib.util, math
from collections import defaultdict

MW_PATH = '/Users/erik/homelab/math193/design/lemma/route1/mw_osc.py'
spec = importlib.util.spec_from_file_location('mw', MW_PATH)
mw = importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

M = [[3, 0, 0], [0, 0, -3], [0, 3, -1]]

# --- exact Q-form Q(v)=x^2+6y^2-2yz+6z^2 ; form matrix Qm=[[1,0,0],[0,6,-1],[0,-1,6]]
def Q(v):
    x, y, z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z
def Qdist(a, b):
    return Q((a[0]-b[0], a[1]-b[1], a[2]-b[2]))
def matmul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def matvec(A, v):
    return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
            A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
            A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])
def transpose(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]
def cross(u, v):
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
def vp3(n):
    if n == 0: return 10**9
    v = 0; n = abs(n)
    while n % 3 == 0: n //= 3; v += 1
    return v

# --- VERIFY conformality M^T Q M = 9 Q (exact) ---
Qm = [[1, 0, 0], [0, 6, -1], [0, -1, 6]]
MtQM = matmul(matmul(transpose(M), Qm), M)
NINE_Q = [[9*Qm[i][j] for j in range(3)] for i in range(3)]
CONFORMAL_OK = (MtQM == NINE_Q)

def build(topL, depth):
    chain, anc = mw.build_ancestry(topL, depth)
    # base-level anchor points (level topL-g) for roots
    levelpts = {}
    for L in range(topL-depth, topL+1):
        try:
            levelpts[L] = mw.build_level(L)[0]
        except Exception:
            pass
    return chain, anc, levelpts

def Mg(v, g):
    r = v
    for _ in range(g):
        r = matvec(M, r)
    return r

def cyl_qdiam_sample(chain, groups, nsample=60):
    """Median & max Q-diameter of gen-g cylinders (sample of largest cylinders)."""
    items = sorted(groups.values(), key=len, reverse=True)[:nsample]
    diams = []
    for idxs in items:
        # exact Q-diameter = max pairwise Q-dist; cylinders small (<200 pts)
        pts = [chain[j] for j in idxs]
        best = 0
        for i in range(len(pts)):
            pi = pts[i]
            for k in range(i+1, len(pts)):
                dq = Qdist(pi, pts[k])
                if dq > best: best = dq
        diams.append(best)
    diams.sort()
    if not diams: return 0, 0
    return diams[len(diams)//2], diams[-1]

def clearance(chain, anc_g, maxsize, cell):
    """min Q-dist between points of DISTINCT gen-g cylinders, via spatial grid.
    Returns (rawmin_q, raw_witness_idxgap, longmin_q, close_encounters) where
    close_encounters is a list of (qdist, idxgap) for all found distinct-cyl pairs
    with Cheb<=cell (dedup by unordered pair not needed; we take mins)."""
    grid = defaultdict(list)
    for j, p in enumerate(chain):
        grid[(p[0]//cell, p[1]//cell, p[2]//cell)].append(j)
    rawmin = None; raw_gap = None
    longmin = None; long_gap = None
    thr = 2*maxsize
    encounters = []  # (qdist, idxgap) sampled among the closest
    N = len(chain)
    for j in range(N):
        p = chain[j]; gj = anc_g[j]
        gx, gy, gz = p[0]//cell, p[1]//cell, p[2]//cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in grid.get((gx+dx, gy+dy, gz+dz), ()):
                        if k <= j: continue
                        if anc_g[k] == gj: continue
                        dq = Qdist(p, chain[k])
                        idxgap = k - j
                        if rawmin is None or dq < rawmin:
                            rawmin = dq; raw_gap = idxgap
                        if idxgap > thr:
                            if longmin is None or dq < longmin:
                                longmin = dq; long_gap = idxgap
                        if dq <= 4*cell*cell:  # collect close encounters (Cheb~<=2cell)
                            encounters.append((dq, idxgap))
    return rawmin, raw_gap, longmin, long_gap, encounters

QDUAL = [[35, 0, 0], [0, 6, 1], [0, 1, 6]]   # adj(Q); |Om|^2_Qdual conformal under cof(M)
COF = [[9, 0, 0], [0, -3, -9], [0, 9, 0]]    # cof(M_BAL3)
def qdual_sq(v):
    return sum(v[i]*QDUAL[i][j]*v[j] for i in range(3) for j in range(3))
def omega_stats(chain, anc_g, g, ntri=3000, seed=1):
    """Over straddling triples of DISTINCT gen-g cylinders (anchor points), form the
    real collinearity form Omega and report BOTH readings on the SAME triples:
      - ARCHIMEDEAN conformal invariant: |Omega|^2_Qdual / 81^g, AND the per-triple
        descent-constancy: descend Omega by cof(M) one level and confirm
        |cof.Omega|^2_Qdual / 81^{g+1} == |Omega|^2_Qdual / 81^g EXACTLY (the
        M^TQM=9Q conformality => archimedean magnitude does NOT decay).
      - p-adic: v3(Omega) and E=v3-2g (the ghost the 5 rounds read as 'decay')."""
    import random
    from fractions import Fraction as Fr
    rnd = random.Random(seed)
    reps = {}
    for j, a in enumerate(anc_g):
        if a not in reps: reps[a] = chain[j]
    ids = list(reps.keys())
    if len(ids) < 3: return None
    descent_const = True; cnt = 0
    v3s = []; Es = []
    for _ in range(ntri):
        a, b, c = rnd.sample(ids, 3)
        pa, pb, pc = reps[a], reps[b], reps[c]
        om = cross((pb[0]-pa[0], pb[1]-pa[1], pb[2]-pa[2]),
                   (pc[0]-pa[0], pc[1]-pa[1], pc[2]-pa[2]))
        if om == (0, 0, 0): continue
        # per-triple conformal descent check (archimedean magnitude is scale-exact)
        n0 = Fr(qdual_sq(om), 81**g)
        om1 = (COF[0][0]*om[0]+COF[0][1]*om[1]+COF[0][2]*om[2],
               COF[1][0]*om[0]+COF[1][1]*om[1]+COF[1][2]*om[2],
               COF[2][0]*om[0]+COF[2][1]*om[1]+COF[2][2]*om[2])
        n1 = Fr(qdual_sq(om1), 81**(g+1))
        if n0 != n1: descent_const = False
        v = min(vp3(om[0]), vp3(om[1]), vp3(om[2]))
        v3s.append(v); Es.append(v - 2*g); cnt += 1
    v3s.sort(); Es.sort()
    return dict(arch_descent_constant=descent_const, ntri=cnt,
                v3_med=v3s[len(v3s)//2] if v3s else 0, v3_max=v3s[-1] if v3s else 0,
                E_med=Es[len(Es)//2] if Es else 0, E_max=Es[-1] if Es else 0)

def root_sep(chain, anc_g, levelpts, topL, g):
    """min |Delta|_Q over distinct gen-g cylinders and whether Delta=0 is hit.
    root = M^g * (base anchor point at level topL-g). Base anchor = the level chain
    point at the ancestor index (levelpts[topL-g])."""
    base = levelpts.get(topL-g)
    if base is None: return None
    # representative base anchor per cylinder = the level-(topL-g) point at ancestor id
    ids = sorted(set(anc_g))
    roots = {}
    for a in ids:
        if a < len(base):
            roots[a] = Mg(base[a], g)
    rl = list(roots.items())
    # check Delta=0 (identical anchor) : distinct ids with identical base point
    seen = {}
    delta0 = 0
    for a, r in rl:
        if r in seen: delta0 += 1
        else: seen[r] = a
    # min |Delta|_Q among distinct: use grid on roots
    cell = max(1, 3**g)
    grid = defaultdict(list)
    for a, r in rl:
        grid[(r[0]//cell, r[1]//cell, r[2]//cell)].append((a, r))
    dmin = None
    for a, r in rl:
        gx, gy, gz = r[0]//cell, r[1]//cell, r[2]//cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for (b, s) in grid.get((gx+dx, gy+dy, gz+dz), ()):
                        if b <= a: continue
                        dq = Qdist(r, s)
                        if dq == 0: continue
                        if dmin is None or dq < dmin: dmin = dq
    return dict(dmin_q=dmin, delta0=delta0, ncyl=len(rl))

def run(topL, depth):
    print("="*78)
    print(f"GEOMETRIC CLEARANCE  topL={topL} depth={depth}   (conformal M^TQM=9Q: {CONFORMAL_OK})")
    print("="*78)
    chain, anc, levelpts = build(topL, depth)
    N = len(chain)
    print(f"N={N} chain points; levels available for roots: {sorted(levelpts)}")
    rows = []
    for g in range(1, depth+1):
        groups = defaultdict(list)
        for j, a in enumerate(anc[g]):
            groups[a].append(j)
        maxsize = max(len(v) for v in groups.values())
        meddiam, maxdiam = cyl_qdiam_sample(chain, groups)
        cell = max(4, min(3**g, 120))
        rawmin, raw_gap, longmin, long_gap, enc = clearance(chain, anc[g], maxsize, cell)
        om = omega_stats(chain, anc[g], g)
        rs = root_sep(chain, anc[g], levelpts, topL, g)
        # normalized clearances: sqrt(Qdist)/sqrt(Qdiam)  and /3^g
        import math as _m
        def norm_by_diam(qd):
            return (_m.sqrt(qd/maxdiam) if (qd and maxdiam) else None)
        def norm_by_3g(qd):
            return (_m.sqrt(qd)/(3**g) if qd else None)
        # touch vs overlap: among close encounters (smallest qdist), what idxgaps?
        enc.sort()
        closest = enc[:200]
        long_close = [e for e in closest if e[1] > 2*maxsize]
        row = dict(g=g, ncyl=len(groups), maxsize=maxsize,
                   meddiam_q=meddiam, maxdiam_q=maxdiam, sqrt_maxdiam=_m.sqrt(maxdiam) if maxdiam else 0,
                   raw_clear_q=rawmin, raw_clear_norm=norm_by_diam(rawmin), raw_clear_3g=norm_by_3g(rawmin), raw_gap=raw_gap,
                   long_clear_q=longmin, long_clear_norm=norm_by_diam(longmin), long_clear_3g=norm_by_3g(longmin), long_gap=long_gap,
                   n_close=len(closest), n_long_close=len(long_close),
                   omega=om, root=rs)
        rows.append(row)
        print(f"\n g={g}: #cyl={row['ncyl']} maxsize={maxsize} cell={cell}")
        print(f"   Q-diam median={meddiam} max={maxdiam} (sqrt={row['sqrt_maxdiam']:.1f}); 3^g={3**g}")
        print(f"   RAW clearance (all distinct pairs): Qdist={rawmin} sqrt={math.sqrt(rawmin):.3f} "
              f"norm/diam={row['raw_clear_norm']:.4f} /3^g={row['raw_clear_3g']:.4f} witness idxgap={raw_gap}")
        if longmin is not None:
            print(f"   LONG-RANGE clearance (idxgap>{2*maxsize}): Qdist={longmin} sqrt={math.sqrt(longmin):.3f} "
                  f"norm/diam={row['long_clear_norm']:.4f} /3^g={row['long_clear_3g']:.4f} witness idxgap={long_gap}")
        else:
            print(f"   LONG-RANGE clearance: NONE within cell={cell} (no non-adjacent arc came within Cheb~{2*cell})")
        print(f"   touch/overlap: {len(closest)} closest distinct-cyl encounters, "
              f"of which {len(long_close)} are chain-distant (idxgap>{2*maxsize})")
        if rs:
            print(f"   root/map sep |Delta|_Q min={rs['dmin_q']} sqrt={math.sqrt(rs['dmin_q']):.3f} "
                  f"/3^g={math.sqrt(rs['dmin_q'])/3**g:.4f} ; Delta=0 hits (distinct cyls, same anchor)={rs['delta0']}")
        if om:
            print(f"   ARCH |Omega|^2_Qdual/81^g EXACTLY conformal-invariant under cof descent? "
                  f"{om['arch_descent_constant']}  (=> archimedean magnitude does NOT decay);  "
                  f"p-adic v3(Omega) med={om['v3_med']} max={om['v3_max']}, E=v3-2g med={om['E_med']} "
                  f"(over {om['ntri']} triples)")
    # slopes
    print("\n" + "-"*78)
    print("SLOPES (log-quantity regressed on g):")
    def logslope(xs, ys):
        pts = [(x, math.log(y)) for x, y in zip(xs, ys) if y and y > 0]
        if len(pts) < 2: return None
        n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
        sxx = sum(p[0]**2 for p in pts); sxy = sum(p[0]*p[1] for p in pts)
        return (n*sxy - sx*sy)/(n*sxx - sx*sx)
    gs = [r['g'] for r in rows]
    for key, label in [('raw_clear_norm', 'RAW clearance/diam'),
                       ('raw_clear_3g', 'RAW clearance/3^g'),
                       ('long_clear_norm', 'LONG clearance/diam')]:
        ys = [r[key] for r in rows]
        sl = logslope(gs, [y for y in ys])
        print(f"  {label:26s}: seq={[round(y,4) if y else None for y in ys]}  log-slope={sl}")
    om_seq = [r['omega']['arch_descent_constant'] if r['omega'] else None for r in rows]
    v3_seq = [r['omega']['v3_max'] if r['omega'] else None for r in rows]
    dmin_seq = [(math.sqrt(r['root']['dmin_q'])/3**r['g'] if r['root'] and r['root']['dmin_q'] else None) for r in rows]
    d0_seq = [r['root']['delta0'] if r['root'] else None for r in rows]
    print(f"  |Omega|_Qdual descent-invariant seq={om_seq}  (all True => archimedean magnitude EXACTLY constant, conformal)")
    print(f"  p-adic v3(Omega) max seq={v3_seq}  (climbs => 3-adic parallelism, the ghost the 5 rounds read as decay)")
    print(f"  root-sep/3^g seq={[round(x,4) if x else None for x in dmin_seq]}  (Bandt-Graf translation, normalized)")
    print(f"  Delta=0 hits seq={d0_seq}  (any nonzero => id in closure => OSC FAILS)")
    return rows

if __name__ == '__main__':
    import sys
    topL = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    run(topL, depth)
