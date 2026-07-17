"""C-C specific failure probes: pure imbrication (no bridge) collinearity,
coils-align, T3 aperture, T4 straddle, T5 dodges."""
from chiral_accel import *
from math import hypot
import cmath

SCREW6 = [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)]
MFIX   = [[0,0,27],[1,0,0],[0,1,0]]
MBAL3  = [[3,0,0],[0,0,-3],[0,3,-1]]
def matvec_int(M,v): return tuple(sum(M[i][j]*v[j] for j in range(3)) for i in range(3))
def matmul_int(A,B):
    return [[sum(A[i][t]*B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]

def seedwalk(menu,L):
    pts=[(0,0,0)];pset=set(pts);cur=pts[0]
    for _ in range(L):
        for s in menu:
            c=vadd(cur,s)
            if c not in pset and legal(pts,c): cur=c;pts.append(c);pset.add(c);break
    return pts

def aperture(pts):
    # min over point triples of normalized |det|/(|d1||d2|) sampled; and bounding-box thinness
    import random
    rng=random.Random(1); n=len(pts)
    if n<3: return None
    best=1e18
    for _ in range(4000):
        i,j,k=rng.sample(range(n),3)
        a,b,c=pts[i],pts[j],pts[k]
        d1=vsub(b,a); d2=vsub(c,a)
        det=(d1[0]*(d2[1])-d1[1]*(d2[0]))  # crude 2d proj; use full 3d cross norm
        cr=(d1[1]*d2[2]-d1[2]*d2[1],d1[2]*d2[0]-d1[0]*d2[2],d1[0]*d2[1]-d1[1]*d2[0])
        crn=hypot(*[float(x) for x in cr]); n1=hypot(*[float(x) for x in d1]); n2=hypot(*[float(x) for x in d2])
        if n1>0 and n2>0:
            best=min(best,crn/(n1*n2))
    return best

def straddle_count(pts):
    """count exact (v,-v) antipodal midpoint-collinear: earlier point is midpoint of two later."""
    pset=set(pts); cnt=0
    # midpoint config: p is midpoint of q,r => q+r=2p. count pairs (q,r) whose midpoint is a walk pt
    L=len(pts); mids=0; anti=0
    idx={p:i for i,p in enumerate(pts)}
    for a in range(L):
        for b in range(a+1,L):
            s=tuple(pts[a][t]+pts[b][t] for t in range(3))
            if all(x%2==0 for x in s):
                m=tuple(x//2 for x in s)
                if m in pset: mids+=1
    return mids

print("### C-C probes ###")
for name,M in [("MFIX(rational 120deg)",MFIX),("MBAL3(irrational cos=-1/6)",MBAL3)]:
    print(f"\n--- {name} ---")
    roots=durand_kerner(charpoly(M))
    print(" moduli",sorted(round(abs(z),3) for z in roots),
          "cosθ of complex pair:",[round(z.real/abs(z),4) for z in roots if abs(z.imag)>1e-6][:1])
    # T5 Niven: is cos rational allowed value?
    seed=seedwalk(SCREW6,6)
    print(" seed len",len(seed),"seed first_triple",first_triple(seed))
    # PURE IMBRICATION: union of M^k(seed) for k=0..6  (NO bridges) -> tests coils-align/self-similarity
    cloud=[]; P=[[1,0,0],[0,1,0],[0,0,1]]
    for k in range(7):
        cloud += [matvec_int(P,p) for p in seed]
        P=matmul_int(P,M)
    # dedup preserve order
    seen=set(); cl=[]
    for p in cloud:
        if p not in seen: seen.add(p); cl.append(p)
    ft=first_triple(cl)
    print(f" pure-imbrication cloud pts={len(cl)} first_triple={ft}")
    if ft:
        i,j,k=ft; print("   COLLINEAR TRIPLE:",cl[i],cl[j],cl[k])
    ap=aperture(cl)
    print(f" aperture (min normalized cross, sampled) = {ap:.5f}")
    strad=straddle_count(cl)
    print(f" midpoint-collinear (v,-v straddle) count = {strad}")
