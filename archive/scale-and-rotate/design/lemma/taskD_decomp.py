import pickle, json, sys, time
from random import Random
sys.path.insert(0,"/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2); R=10; CELL=40; D=40
def word_interiors(start,w):
    pts=[];x,y,z=start
    for si in w[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def cell_of(p): return (p[0]//CELL,p[1]//CELL,p[2]//CELL)
def line_hits_box(a1,a2,Rr):
    lo,hi=-1e18,1e18
    for j in range(3):
        d=a2[j]-a1[j];p=a1[j]
        if d==0:
            if p<-Rr or p>Rr: return False
        else:
            t0=(-Rr-p)/d;t1=(Rr-p)/d
            if t0>t1:t0,t1=t1,t0
            if t0>lo:lo=t0
            if t1<hi:hi=t1
            if lo>hi:return False
    return lo<=hi
for L in (6,7):
    d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    anchors=d['anchors'];order=d['order'];words=d['words']
    anchset=set(anchors)
    grid={}
    for p in anchors: grid.setdefault(cell_of(p),[]).append(p)
    npos=len(order);rng=Random(7)
    tg=set(rng.sample(range(npos),min(1500,npos)))
    b_tot=b_aa=0; f_tot=0; f_aa=0; n=0
    for pos,i in enumerate(order):
        if pos in tg:
            A,B=anchors[i],anchors[i+1]
            m=((A[0]+B[0])//2,(A[1]+B[1])//2,(A[2]+B[2])//2)
            cx,cy,cz=m
            c0=cell_of((cx-D,cy-D,cz-D));c1=cell_of((cx+D,cy+D,cz+D))
            nb=[]
            for gx in range(c0[0],c1[0]+1):
              for gy in range(c0[1],c1[1]+1):
                for gz in range(c0[2],c1[2]+1):
                    bb=grid.get((gx,gy,gz))
                    if bb:
                        for p in bb:
                            if abs(p[0]-cx)<=D and abs(p[1]-cy)<=D and abs(p[2]-cz)<=D: nb.append(p)
            isanc=[p in anchset for p in nb]
            sh=[(p[0]-cx,p[1]-cy,p[2]-cz) for p in nb]
            nn=len(sh)
            for x in range(nn):
                for y in range(x+1,nn):
                    if line_hits_box(sh[x],sh[y],R):
                        b_tot+=1
                        if isanc[x] and isanc[y]: b_aa+=1
            n+=1
        for p in word_interiors(anchors[i],words[i]):
            grid.setdefault(cell_of(p),[]).append(p)
    print(f"L{L}: n={n} b_mean={b_tot/n:.1f} anchor-anchor(inherited)={b_aa/n:.1f} "
          f"frac_inherited={b_aa/b_tot:.3f} frac_new={(b_tot-b_aa)/b_tot:.3f}")
