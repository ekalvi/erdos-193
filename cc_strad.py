from chiral_accel import *
from math import hypot
SCREW6=[(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)]
MFIX=[[0,0,27],[1,0,0],[0,1,0]]; MBAL3=[[3,0,0],[0,0,-3],[0,3,-1]]
# negation-closed control menu (achiral) same size class
NEGSYM=[(2,1,1),(-2,-1,-1),(1,-2,1),(-1,2,-1),(1,0,0),(-1,0,0)]
def mv(M,v): return tuple(sum(M[i][j]*v[j] for j in range(3)) for i in range(3))
def mm(A,B): return [[sum(A[i][t]*B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]
def seedwalk(menu,L):
    pts=[(0,0,0)];pset=set(pts);cur=pts[0]
    for _ in range(L):
        for s in menu:
            c=vadd(cur,s)
            if c not in pset and legal(pts,c): cur=c;pts.append(c);pset.add(c);break
    return pts
def cloud(menu,M,K=7,seedL=6):
    seed=seedwalk(menu,seedL); out=[]; P=[[1,0,0],[0,1,0],[0,0,1]]
    for k in range(K): out+=[mv(P,p) for p in seed]; P=mm(P,M)
    seen=set(); cl=[]
    for p in out:
        if p not in seen: seen.add(p); cl.append(p)
    return cl
def midcount(pts):
    pset=set(pts); L=len(pts); c=0
    for a in range(L):
        for b in range(a+1,L):
            s=tuple(pts[a][t]+pts[b][t] for t in range(3))
            if all(x%2==0 for x in s) and tuple(x//2 for x in s) in pset: c+=1
    return c
print("chirality check:")
for nm,S in [("SCREW6",SCREW6),("NEGSYM",NEGSYM)]:
    ch,ng,dets=is_chiral(S); print(f"  {nm}: chiral={ch} negclosed={negation_closed(S)} |Aut|={ng}")
print("\nstraddle (midpoint-collinear) counts on pure-imbrication cloud, MBAL3:")
for nm,S in [("SCREW6 chiral",SCREW6),("NEGSYM achiral neg-closed",NEGSYM)]:
    cl=cloud(S,MBAL3); print(f"  {nm}: pts={len(cl)} midpoint-straddles={midcount(cl)} first_triple={first_triple(cl)}")
