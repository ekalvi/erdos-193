"""Decisive: does NORMALIZED sibling separation PLATEAU or DECAY?
Distinguishes TWO separations at each generation g on the realized L8 orbit:
  (1) ROOT (map) separation  = min |root_a - root_b| over sibling gen-g cyls
      (root = M^g * ancestor = the anchor image; this is the Bandt-Graf
      neighbor-MAP quantity that decides OSC / id-in-closure).
  (2) POINT-SET gap = min point-set Cheb distance over sibling gen-g cyls
      (closest twig/refill approach; boundary-touching, OSC-permitted).
Normalizes each by the gen-g cylinder diameter. Also computes the pure lattice
floor min|M^g v|_inf and the isotropic 3^g for reference.
"""
import pickle, math
from collections import defaultdict
from gate_run import word_interiors

M=[[3,0,0],[0,0,-3],[0,3,-1]]
def mul(M,v): return (M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
                       M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
                       M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2])
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def ninf(v): return max(abs(v[0]),abs(v[1]),abs(v[2]))

# (0) pure lattice floor min|M^g v|_inf over 0<|v|<=B
def minMg(g,B=3):
    Mg=[[1,0,0],[0,1,0],[0,0,1]]
    for _ in range(g):
        Mg=[[sum(M[i][k]*Mg[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    best=10**9
    for a in range(-B,B+1):
      for b in range(-B,B+1):
        for c in range(-B,B+1):
          if a==0 and b==0 and c==0: continue
          v=mul(Mg,(a,b,c))
          n=ninf(v)
          if n<best: best=n
    return best
print("g : min|M^g v|_inf (v in [-3,3]^3\\0)   3^g   ratio/3^g")
for g in range(1,7):
    m=minMg(g); print(f"{g} : {m:6d}   {3**g:6d}   {m/3**g:.4f}")

# realized ancestry (reuse mw_osc builders)
import importlib.util
spec=importlib.util.spec_from_file_location("mw","/Users/erik/homelab/math193/design/lemma/route1/mw_osc.py")
mw=importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

topL=8; depth=5
# need L4 construction too for depth5; fall back to depth4 if missing
import os
while depth>1 and not os.path.exists(f'/Users/erik/homelab/math193/gate2-l7-construction-L{topL-depth+1}.pkl'):
    depth-=1
print(f"\nrealized topL={topL} depth={depth}")
chain,anc=mw.build_ancestry(topL,depth)
N=len(chain)

# roots: for gen-g cylinder id = ancestor index a in W_{topL-g}; root = M^g * (that ancestor point).
# Get ancestor POINTS at each level.
levelpts={}
for L in range(topL-depth+1, topL+1):
    ch,_=mw.build_level(L); levelpts[L]=ch
# W_{topL} chain we already have; ancestor points:
def Mg_apply(v,g):
    r=v
    for _ in range(g): r=mul(M,r)
    return r

print("\ng | #sibpairs | ROOTsep(min) | PTgap(min) | diam(med/max) | ROOTsep/diam | PTgap/diam")
for g in range(1,depth):
    # siblings: group by parent anc[g+1], children distinct anc[g]
    byparent=defaultdict(lambda: defaultdict(list))
    for j in range(N):
        byparent[anc[g+1][j]][anc[g][j]].append(j)
    # roots per child id: ancestor point in W_{topL-g}, times M^g
    ancL=levelpts[topL-g]
    rootmin=10**9; ptmin=10**9
    diams=[]
    # diam per gen-g cyl
    groups=defaultdict(list)
    for j in range(N): groups[anc[g][j]].append(j)
    for idxs in groups.values(): diams.append(mw.cyl_diam(chain,idxs))
    diams.sort(); med=diams[len(diams)//2]; mx=diams[-1]
    for pid,children in byparent.items():
        cs=list(children.items())
        if len(cs)<2: continue
        for x in range(len(cs)):
          for y in range(x+1,len(cs)):
            ida,idb=cs[x][0],cs[y][0]
            ra=Mg_apply(ancL[ida],g); rb=Mg_apply(ancL[idb],g)
            rs=cheb(ra,rb)
            if rs<rootmin: rootmin=rs
            pa=cs[x][1]; pb=cs[y][1]
            pm=min(cheb(chain[i],chain[k]) for i in pa for k in pb)
            if pm<ptmin: ptmin=pm
    print(f"{g} | {'':9}| {rootmin:6d}       | {ptmin:6d}     | {med:4d}/{mx:4d}     | {rootmin/mx:.4f}      | {ptmin/mx:.4f}")
