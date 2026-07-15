"""Exact max_q c_k over all integer lattice centres, rho=1..RMAX, using a
memory-lean grid: only enumerate box centres per point, dict count."""
import pickle, sys
from collections import defaultdict
from gate_run import word_interiors
def build_chain(L):
    d=pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    a=d['anchors']; w=d['words']; ch=[a[0]]
    for i in range(len(w)): ch+=word_interiors(a[i],w[i]); ch+=[a[i+1]]
    return ch
def exact_max(pts,rho):
    cnt=defaultdict(int); R=range(-rho,rho+1)
    for (x,y,z) in pts:
        for dx in R:
            xx=x+dx
            for dy in R:
                yy=y+dy
                for dz in R:
                    cnt[(xx,yy,z+dz)]+=1
    return max(cnt.values())
L=int(sys.argv[1]); rmax=int(sys.argv[2])
pts=build_chain(L)
for rho in range(1,rmax+1):
    b=exact_max(pts,rho)
    print(f'L{L} rho={rho} EXACTmax={b} C=(b-1)/rho={(b-1)/rho:.3f}',flush=True)
