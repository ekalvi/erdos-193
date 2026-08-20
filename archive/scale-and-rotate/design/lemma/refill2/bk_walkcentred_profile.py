import pickle,sys
from collections import defaultdict
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
def word_interiors(start,w):
    pts=[];x,y,z=start
    for si in w[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def load_interiors(L):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    anchors=d["anchors"];words=d["words"];inter=[]
    for i in range(len(anchors)-1):
        for p in word_interiors(anchors[i],w=words[i]): inter.append(p)
    return inter
# walk-centred (lower bound on sup): centre at each interior point, count interiors within cheb-rho
def bk_walkcentred(inter,rho):
    S=set(inter)
    # build spatial hash by cell? simple: for each centre, count via dict of coords
    from collections import defaultdict
    # bucket points
    pts=inter
    best=0
    # use grid of size (rho) not needed; do neighbor count via sorted? N up to 300k, O(N* (2rho+1)^3) too big.
    # Instead: for each centre c in pts, count pts within cheb rho using a dict keyed by coarse cell.
    cell=rho if rho>0 else 1
    grid=defaultdict(list)
    for p in pts: grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    for c in pts:
        gx,gy,gz=c[0]//cell,c[1]//cell,c[2]//cell
        cnt=0
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for p in grid.get((gx+dx,gy+dy,gz+dz),()):
                if abs(p[0]-c[0])<=rho and abs(p[1]-c[1])<=rho and abs(p[2]-c[2])<=rho: cnt+=1
        if cnt>best: best=cnt
    return best
for L in [6,7,8]:
    inter=load_interiors(L)
    row=[bk_walkcentred(inter,rho) for rho in range(1,11)]
    print(f"L{L} walk-centred b_k(rho) rho=1..10:", row, "  slopes b/rho:", [round(v/r,2) for r,v in zip(range(1,11),row)],flush=True)
