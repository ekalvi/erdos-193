"""Measure c_k(q,rho) = # walk points within Chebyshev distance rho of centre q.
Centres considered: (A) every walk point, (B) exact max over ALL integer lattice
centres (found via a sliding-window over candidate box positions).
Reports max_q c_k and implied C = (max-1)/rho for rho=1..10."""
import pickle, sys
from collections import defaultdict
from gate_run import word_interiors

def build_chain(L):
    d = pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    anchors=d['anchors']; words=d['words']
    chain=[anchors[0]]
    for i in range(len(words)):
        chain += word_interiors(anchors[i], words[i])
        chain += [anchors[i+1]]
    return chain

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def measure_walk_centres(pts, rho):
    # grid bucket of side rho+1 so neighbours are in 3x3x3 blocks... use side=rho
    cell = rho if rho>0 else 1
    grid=defaultdict(list)
    for p in pts:
        grid[(p[0]//(cell), p[1]//(cell), p[2]//(cell))].append(p)
    best=0; argp=None
    for q in pts:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        c=0
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2):
                for dz in(-2,-1,0,1,2):
                    for p in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(p,q)<=rho: c+=1
        if c>best: best=c; argp=q
    return best, argp

if __name__=='__main__':
    L=int(sys.argv[1])
    pts=build_chain(L)
    print(f'L{L}: {len(pts)} points')
    for rho in range(1,11):
        b,ap=measure_walk_centres(pts,rho)
        C=(b-1)/rho
        print(f'  rho={rho:2d}  max c_k(walk-centre)={b:3d}  C=(max-1)/rho={C:.3f}')
