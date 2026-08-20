import math
from random import Random
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify193 import amplify_level, find_base
from erdos193 import first_disqualifier
from imbricate_seam import walk_points

MENU = candidate_step_vectors(2)
def Mm(m): return ((m,0,0),(0,0,-m),(0,m,-1))   # eigenvalue moduli m, irrational twist arccos(-1/2m)

def extent(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; zs=[p[2] for p in pts]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

def crowd_max(pts, r):
    C=max(1,r); grid=defaultdict(list)
    for p in pts: grid[(p[0]//C,p[1]//C,p[2]//C)].append(p)
    mx=0
    for p in pts:
        cx,cy,cz=p; cnt=0; gx,gy,gz=cx//C,cy//C,cz//C
        for bx in range(gx-1,gx+2):
            for by in range(gy-1,gy+2):
                for bz in range(gz-1,gz+2):
                    for (x,y,z) in grid.get((bx,by,bz),()):
                        if 0<max(abs(x-cx),abs(y-cy),abs(z-cz))<=r: cnt+=1
        if cnt>mx: mx=cnt
    return mx

print("m | jam? | lam(pts/lvl) | extent-ratio | DIM=logλ/logext | crowd@r=m | provable-packing@r=m", flush=True)
for m in (3,4,5,6):
    M=Mm(m); rng=Random(193)
    base=find_base(MENU,rng,length=20,tries=200)
    word=base; pts=walk_points(word,MENU); lens=[len(pts)]; exts=[extent(pts)]
    jam=None
    for level in range(1,4):
        new=amplify_level(word,MENU,M,rng,seg_maxlen=2*m+6,seg_tries=8,restarts=6,route="short")
        if new is None:
            jam=level; break
        word=new; pts=walk_points(word,MENU)
        assert first_disqualifier(pts) is None
        lens.append(len(pts)); exts.append(extent(pts))
    if jam:
        print(f"{m} | JAM@L{jam} | -- | -- | -- | -- | --", flush=True); continue
    lam=(lens[-1]/lens[0])**(1.0/(len(lens)-1))
    extr=(exts[-1]/exts[1])**(1.0/(len(exts)-2)) if len(exts)>2 else exts[-1]/exts[1]
    dim=math.log(lam)/math.log(extr)
    cr=crowd_max(pts, m)                       # crowding at the SCALING radius r=m
    sep=m                                      # proven min anchor separation min|M_m v|inf = m
    prov=(2*m//sep+1)**3 * 4                   # provable packing bound at r=m, g<=4
    print(f"{m} | none | {lam:.2f} | {extr:.2f} | {dim:.3f} | {cr} | {prov}", flush=True)
