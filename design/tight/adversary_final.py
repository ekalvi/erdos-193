"""
(1) LOAD-BEARING drift: max_c at rho=4 (=c(4.44)) across L5..L8 -- does it exceed 12?
(2) Route-3 SINGLE-LEVEL refill slope E: crowding of STITCH-ONLY (birth==L) points,
    b_k(rho)=max ball over stitch set; E=max b_k/rho. Level-stable? drift?
(3) product-bound looseness: ratio (max_A * max_sojourn)/max_c per rho (should blow up
    if A,L anti-correlate => returns*sojourn is NOT the right linear decomposition).
"""
import sys, pickle, json
sys.path.insert(0,"/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from collections import defaultdict
MENU=candidate_step_vectors(2)
def Mp(p):return (3*p[0],-3*p[2],3*p[1]-p[2])
def interiors(start,wi):
    pts=[];x,y,z=start
    for si in wi[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def build(L):
    d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    A=d["anchors"];W=d["words"];walk=[]
    for i in range(len(A)-1):
        walk.append(A[i]);walk.extend(interiors(A[i],W[i]))
    walk.append(A[-1]);return walk
def build_tagged(Lmax,Lbase=5):
    out={};walk=build(Lbase);tags=[Lbase]*len(walk);out[Lbase]=(walk,tags)
    for L in range(Lbase+1,Lmax+1):
        d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
        A=d["anchors"];W=d["words"];pw,pt=out[L-1]
        walk=[];tags=[]
        for i in range(len(A)-1):
            walk.append(A[i]);tags.append(pt[i])
            for ip in interiors(A[i],W[i]):walk.append(ip);tags.append(L)
        walk.append(A[-1]);tags.append(pt[-1]);out[L]=(walk,tags)
    return out
def cheb(a,b):return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def grid_of(points,R):
    g=defaultdict(list)
    for idx,p in enumerate(points):g[(p[0]//R,p[1]//R,p[2]//R)].append(idx)
    return g
def maxball(centres,points,rho):
    R=rho+1;g=grid_of(points,R);best=0
    for q in centres:
        cx,cy,cz=q[0]//R,q[1]//R,q[2]//R;c=0
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for idx in g.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,points[idx])<=rho:c+=1
        if c>best:best=c
    return best
if __name__=="__main__":
    Lmax=8;tagged=build_tagged(Lmax,5)
    res={"load_bearing_c4":{},"single_level_refill_E":{}}
    # (1) c(4) drift + a few rho
    for L in range(5,Lmax+1):
        walk,tags=tagged[L]
        row={}
        for rho in (2,4,5):
            row[rho]=maxball(walk,walk,rho)
        res["load_bearing_c4"][f"L{L}"]=row
        print(f"L{L} c(2)={row[2]} c(4)={row[4]} c(5)={row[5]}  [target c(4)<=12]",flush=True)
    # (2) single-level refill slope: stitch-only crowding b_k(rho)=max over stitch centres of #stitch in ball
    for L in range(6,Lmax+1):
        walk,tags=tagged[L]
        stitch=[walk[i] for i in range(len(walk)) if tags[i]==L]
        row={}
        for rho in (1,2,4,5,8,10):
            b=maxball(stitch,stitch,rho);row[rho]=(b,round(b/rho,3))
        res["single_level_refill_E"][f"L{L}"]=row
        Emax=max(v[1] for v in row.values())
        print(f"L{L} stitch-refill b_k/rho: "+" ".join(f"r{r}:{row[r][0]}({row[r][1]})" for r in row)+f"  Emax={Emax}",flush=True)
    json.dump(res,open("/Users/erik/homelab/math193/design/tight/adversary_final.json","w"),indent=1)
    print("WROTE",flush=True)
