"""Exact max_q c_k(q,rho) over ALL integer lattice centres q, via box-coverage.
Every centre with c>=1 lies in some walk point's (2rho+1)^3 box; count coverage."""
import pickle, sys
from collections import defaultdict, Counter
from gate_run import word_interiors

def build_chain(L):
    d = pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    anchors=d['anchors']; words=d['words']
    chain=[anchors[0]]
    for i in range(len(words)):
        chain += word_interiors(anchors[i], words[i])
        chain += [anchors[i+1]]
    return chain

def exact_max(pts, rho):
    cnt=Counter()
    R=range(-rho,rho+1)
    for (x,y,z) in pts:
        for dx in R:
            xx=x+dx
            for dy in R:
                yy=y+dy
                for dz in R:
                    cnt[(xx,yy,zz:=z+dz)]+=1
    best=max(cnt.values())
    # also how many centres achieve it, and split by walk vs non-walk centre
    ptset=set(pts)
    args=[q for q,c in cnt.items() if c==best]
    on_walk=any(q in ptset for q in args)
    return best, len(args), on_walk

if __name__=='__main__':
    L=int(sys.argv[1]); rmax=int(sys.argv[2]) if len(sys.argv)>2 else 4
    pts=build_chain(L)
    print(f'L{L}: {len(pts)} points  (exact lattice-centre max)')
    for rho in range(1,rmax+1):
        b,na,ow=exact_max(pts,rho)
        print(f'  rho={rho:2d}  EXACT max c_k={b:3d}  C=(max-1)/rho={(b-1)/rho:.3f}  #argmax={na} on_walk={ow}')
