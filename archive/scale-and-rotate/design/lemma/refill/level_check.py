"""
ADVERSARIAL RE-CHECK of B_local level-independence across L5,L6,L7,L8.

Two measurements:
 (A) EXACT sup over ALL integer centres q of #{stitch interiors in Cheb-rho}
     for rho=1,2,3. Memory-bounded via x-slab sharding so it runs on L8.
     For integer rho the real sup is attained at an integer centre.
 (B) Fast grid walk+anchor-centred B_local(rho), rho=1..12, all levels, to see
     whether B_local(rho)/rho grows with the LEVEL (unbounded drift = fatal) or
     saturates.
Also records the per-stitch decomposition of the exact argmax ball, and the
anchor co-factor (#anchors within Cheb-(rho+4) of the winning centre).
"""
import pickle, sys, os
from collections import defaultdict
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)

def word_interiors(start, w):
    pts=[]; x,y,z=start
    for si in w[:-1]:
        s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
    return pts

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def load(L):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    a=d["anchors"]; w=d["words"]
    inter=[]; owner=[]
    for i in range(len(a)-1):
        for p in word_interiors(a[i],w[i]):
            inter.append(tuple(p)); owner.append(i)
    return [tuple(x) for x in a], inter, owner

def exact_sup_sharded(inter, owner, rho, slabW=2000):
    """Exact max over integer centres, sharded on x to bound memory.
    A centre with x=cx only sees interiors with px in [cx-rho,cx+rho].
    Shard centre-x into slabs; an interior influences centres in x-slabs it
    reaches. We assign each interior to slab of floor(px/slabW) and also the
    neighbor slab if within rho of a boundary (rho<<slabW so cheap)."""
    slabs=defaultdict(list)
    for idx,(x,y,z) in enumerate(inter):
        s=x//slabW
        slabs[s].append(idx)
        if (x - s*slabW) < rho: slabs[s-1].append(idx)
        if ((s+1)*slabW - x) <= rho: slabs[s+1].append(idx)
    best=0; bestc=None
    for s,idxs in slabs.items():
        cnt=defaultdict(int)
        for idx in idxs:
            x,y,z=inter[idx]
            for cx in range(x-rho,x+rho+1):
                if cx//slabW!=s: continue   # count each centre in exactly one slab
                for cy in range(y-rho,y+rho+1):
                    for cz in range(z-rho,z+rho+1):
                        cnt[(cx,cy,cz)]+=1
        for k,v in cnt.items():
            if v>best: best=v; bestc=k
    return best, bestc

def decompose(inter,owner,c,rho):
    o=defaultdict(int); cx,cy,cz=c
    for p,ow in zip(inter,owner):
        if abs(p[0]-cx)<=rho and abs(p[1]-cy)<=rho and abs(p[2]-cz)<=rho:
            o[ow]+=1
    hist=defaultdict(int)
    for v in o.values(): hist[v]+=1
    return len(o), dict(sorted(hist.items()))

def fast_ball_max(centres, points, rho):
    R=rho+1
    grid=defaultdict(list)
    for idx,p in enumerate(points):
        grid[(p[0]//R,p[1]//R,p[2]//R)].append(idx)
    best=0
    for q in centres:
        cx,cy,cz=q[0]//R,q[1]//R,q[2]//R; c=0
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for idx in grid.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,points[idx])<=rho: c+=1
        if c>best: best=c
    return best

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [5,6,7,8]
    mode=os.environ.get("MODE","exact")   # exact | fast
    for L in levels:
        anchors,inter,owner=load(L)
        assert len(set(inter)&set(anchors))==0
        print(f"\n=== L{L}: {len(anchors)} anchors, {len(inter)} interiors ===",flush=True)
        if mode=="exact":
            print("rho  B_exact  ratio  nstitch  hist          anch<=r+4",flush=True)
            for rho in (1,2,3):
                b,c=exact_sup_sharded(inter,owner,rho)
                ns,hist=decompose(inter,owner,c,rho)
                an=sum(1 for a in anchors if cheb(a,c)<=rho+4)
                print(f"{rho:3d}  {b:6d}  {b/rho:5.2f}  {ns:6d}  {str(hist):12s}  {an}",flush=True)
        else:
            centres=list(set(inter)|set(anchors))
            print("rho  B_fast  ratio",flush=True)
            for rho in range(1,13):
                b=fast_ball_max(centres,inter,rho)
                print(f"{rho:3d}  {b:6d}  {b/rho:5.2f}",flush=True)
