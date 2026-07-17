"""T3 (flatten/aperture), T4 (straddle suppression vs neg-closed baseline),
T5 (dodges) for the C-H candidate (n=4 M4 + twist4)."""
from chiral_accel import *
from build_ch import twist4, matvec_int, flen, seed_walk, bridge_double_helix
from math import hypot

# ---------- SVD-free aperture via Gram eigenvalue ratio (power iteration) ----
def gram(points):
    n=len(points[0]); m=len(points)
    mean=[sum(p[i] for p in points)/m for i in range(n)]
    C=[[0.0]*n for _ in range(n)]
    for p in points:
        d=[p[i]-mean[i] for i in range(n)]
        for i in range(n):
            for j in range(n):
                C[i][j]+=d[i]*d[j]
    return C

def eig_extremes(C, iters=2000):
    n=len(C)
    import random
    rng=random.Random(1)
    def mv(v): return [sum(C[i][j]*v[j] for j in range(n)) for i in range(n)]
    def norm(v): return hypot(*v)
    # largest via power iteration
    v=[rng.random() for _ in range(n)]
    for _ in range(iters):
        v=mv(v); nv=norm(v);
        if nv==0: break
        v=[x/nv for x in v]
    lam_max=norm(mv(v))
    # smallest via inverse-shift: use (lam_max*I - C) power iteration -> lam_max-lam_min
    def mv2(x): return [lam_max*x[i]-sum(C[i][j]*x[j] for j in range(n)) for i in range(n)]
    w=[rng.random() for _ in range(n)]
    for _ in range(iters):
        w=mv2(w); nw=norm(w)
        if nw==0: break
        w=[x/nw for x in w]
    shift=norm(mv2(w))
    lam_min=lam_max-shift
    return lam_max, lam_min

def aperture(points):
    C=gram(points)
    lmax,lmin=eig_extremes(C)
    if lmax<=0: return 0.0
    # ratio of stddev extremes = sqrt(lmin/lmax)
    r=lmin/lmax
    return (r**0.5) if r>0 else 0.0

# ---------- T3: cumulative-product flattening of the composed map ----------
def matmul_int(A,B):
    n=len(A); k=len(B); m=len(B[0])
    return [[sum(A[i][t]*B[t][j] for t in range(k)) for j in range(m)] for i in range(n)]

def cumulative_map_aperture(avals,bcs):
    P=[[1 if i==j else 0 for j in range(4)] for i in range(4)]
    rows=[]
    Rprod=1.0
    for k in range(len(avals)):
        M=M4(avals[k],bcs[k][0],bcs[k][1])
        P=matmul_int(M,P)
        Rprod*=avals[k]
        # normalized map columns as "point cloud" -> aperture of P/Rprod
        cols=[[P[i][j]/Rprod for i in range(4)] for j in range(4)]
        ap=aperture(cols+[[0,0,0,0]])   # include origin
        rows.append((k+1,avals[k],round(ap,4),round(Rprod,1)))
    return rows

print("="*70); print("T3 FLATTEN: aperture of normalized cumulative product prod M_k / prod r_k")
print("(bounded away from 0 => no flattening; ->0 => collapses to line)"); print("="*70)
avals=[2,3,4,5,6,7]; bcs=[(1,3),(1,2),(1,3),(1,2),(1,3),(1,2)]
for row in cumulative_map_aperture(avals,bcs):
    print("  level",row[0],"a=",row[1],"aperture(min/max stddev)=",row[2],"prod_r=",row[3])

# aperture of an actual triple-free interior bridge cloud
print()
menu=twist4
start=(0,0,0,0); target=(90,30,-40,50)
pts=[start]; pset={start}
ok,nadd=bridge_double_helix(start,target,menu,pts,pset,8,8,3,3,node_budget=200000)
print("interior bridge cloud: pts=",len(pts),"triple_free=",first_triple(pts) is None,
      "aperture=",round(aperture(pts),4),"closed_exact=",ok)

# ---------- T4: straddle suppression, chiral vs neg-closed baseline ----------
print(); print("="*70)
print("T4 STRADDLE-SUPPRESSION: (v,-v) antipodal step pairs + midpoint-is-a-point")
print("="*70)
def antipodal_pairs(menu):
    s=set(menu); c=0
    for v in menu:
        if tuple(-x for x in v) in s: c+=1
    return c//2
def midpoint_fraction(points, cap=1500):
    pset=set(points); pts=points[:cap]; m=len(pts); hit=0; tot=0
    for i in range(m):
        for j in range(i+1,m):
            a=pts[i]; b=pts[j]
            s=tuple(a[t]+b[t] for t in range(len(a)))
            tot+=1
            if all(x%2==0 for x in s) and tuple(x//2 for x in s) in pset:
                hit+=1
    return hit,tot

# chiral menu walk
wch=seed_walk(twist4, 4000)
# neg-closed baseline menu (achiral, straddle-heavy): twist4 U -twist4
base_menu=twist4+[tuple(-x for x in v) for v in twist4]
wbase=seed_walk(base_menu, 4000)
print("chiral twist4:   |walk|=",len(wch),"antipodal_step_pairs=",antipodal_pairs(twist4),
      "triple_free=",first_triple(wch) is None)
h1,t1=midpoint_fraction(wch); print("   midpoint-is-a-point:",h1,"/",t1)
print("neg-closed base: |walk|=",len(wbase),"antipodal_step_pairs=",antipodal_pairs(base_menu),
      "triple_free=",first_triple(wbase) is None)
h2,t2=midpoint_fraction(wbase); print("   midpoint-is-a-point:",h2,"/",t2)

# ---------- T5: dodges (maps distinct, r increasing, angles irrational) ------
print(); print("="*70); print("T5 DODGES"); print("="*70)
mats=[M4(avals[k],bcs[k][0],bcs[k][1]) for k in range(6)]
alldistinct=len({tuple(map(tuple,M)) for M in mats})==len(mats)
rincr=all(avals[k]<avals[k+1] for k in range(5))
angles_irr=all(block2_angle_ok(avals[k],bcs[k][0]) and block2_angle_ok(avals[k],bcs[k][1]) for k in range(6))
print("maps pairwise distinct (no fixed-map automaton):",alldistinct)
print("r_k strictly increasing (no fixed similarity/ESS):",rincr)
print("all angles irrational per Niven (no recurrence):",angles_irr)
print("menu chiral & S!=-S (no forced antipodal survivors):",is_chiral(twist4)[0], not negation_closed(twist4))
