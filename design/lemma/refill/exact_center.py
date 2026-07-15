"""Exact sup over ALL integer centres q of #{stitch interiors within Cheb-rho}.
For integer rho the sup over real q is attained at an integer centre (a closed
interval of length 2*rho contains <= 2*rho+1 integers, max when endpoints integer).
Lean: accumulate a plain integer count per candidate centre; take the max.  Then
re-scan the (few) interiors near the winning centre to decompose per-stitch."""
import pickle, sys
from collections import defaultdict
from search193 import candidate_step_vectors
MENU = candidate_step_vectors(2)
def word_interiors(start, wi):
    pts=[];x,y,z=start
    for si in wi[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def load_interiors(L):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    anchors=d["anchors"];words=d["words"];inter=[];owner=[]
    for i in range(len(anchors)-1):
        for p in word_interiors(anchors[i],words[i]):
            inter.append(p);owner.append(i)
    return inter,owner

def exact_max(inter, rho):
    cnt=defaultdict(int)
    for (x,y,z) in inter:
        for cx in range(x-rho,x+rho+1):
         for cy in range(y-rho,y+rho+1):
          for cz in range(z-rho,z+rho+1):
            cnt[(cx,cy,cz)]+=1
    best=0;bk=None
    for k,v in cnt.items():
        if v>best: best=v;bk=k
    return best,bk

def decompose(inter,owner,center,rho):
    owners=defaultdict(int)
    cx,cy,cz=center
    for p,ow in zip(inter,owner):
        if abs(p[0]-cx)<=rho and abs(p[1]-cy)<=rho and abs(p[2]-cz)<=rho:
            owners[ow]+=1
    hist=defaultdict(int)
    for v in owners.values(): hist[v]+=1
    return len(owners),dict(sorted(hist.items()))

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [6,7,8]
    rhos=[1,2,3,4]
    C=6.0
    for L in levels:
        inter,owner=load_interiors(L)
        print(f"\n=== L{L}: {len(inter)} interiors, EXACT lattice-centre sup ===",flush=True)
        print("rho  B_local(exact)  target3.333r  ratio  n_stitch  int/stitch-hist",flush=True)
        for rho in rhos:
            b,bk=exact_max(inter,rho)
            ns,hist=decompose(inter,owner,bk,rho)
            print(f"{rho:3d}  {b:13d}  {(5/9)*C*rho:11.2f}  {b/rho:5.2f}  {ns:7d}  {hist}",flush=True)
