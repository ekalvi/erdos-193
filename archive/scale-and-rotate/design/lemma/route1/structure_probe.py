"""For the densest Cheb-rho balls, dissect what bounds the point count:
 - triple-free => chords from any in-ball point have DISTINCT primitive directions
 - geometric capacity = # primitive dirs with sup-norm <= 2rho (the O(rho^2) room)
 - kappa_3 = 3-adic valuation of cross products of in-ball chords (max over pairs)
 - arc structure: is the ball's point set one contiguous path-arc or several?
"""
import pickle, sys
from math import gcd
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

def prim(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    if g==0: return (0,0,0)
    w=(v[0]//g,v[1]//g,v[2]//g)
    for c in w:
        if c!=0:
            return w if c>0 else (-w[0],-w[1],-w[2])
    return w

def v3(n):
    n=abs(n)
    if n==0: return 999
    c=0
    while n%3==0: n//=3; c+=1
    return c

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

# count primitive directions with sup-norm<=R (geometric capacity, half-space dedup)
def prim_dir_capacity(R):
    S=set()
    for x in range(-R,R+1):
        for y in range(-R,R+1):
            for z in range(-R,R+1):
                if x==0 and y==0 and z==0: continue
                S.add(prim((x,y,z)))
    return len(S)//2  # antipodal pairs -> undirected lines

def analyze(L, rhos):
    pts=build_chain(L)
    idx={p:i for i,p in enumerate(pts)}
    # grid for neighbor queries
    print(f'=== L{L}: {len(pts)} pts ===')
    for rho in rhos:
        cell=max(rho,1)
        grid=defaultdict(list)
        for i,p in enumerate(pts):
            grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
        best=-1; bestinfo=None
        for ci,q in enumerate(pts):
            gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
            ball=[]
            for dx in(-2,-1,0,1,2):
                for dy in(-2,-1,0,1,2):
                    for dz in(-2,-1,0,1,2):
                        for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                            if cheb(pts[j],q)<=rho: ball.append(j)
            if len(ball)>best:
                best=len(ball); bestinfo=(ci,ball)
        ci,ball=bestinfo
        q=pts[ci]
        # anchor at q (a walk point). chords to others:
        dirs=[prim((pts[j][0]-q[0],pts[j][1]-q[1],pts[j][2]-q[2])) for j in ball if j!=ci]
        distinct=len(set(dirs))
        # kappa_3 max over pairs of chords (raw, not primitive-stripped cross)
        chords=[(pts[j][0]-q[0],pts[j][1]-q[1],pts[j][2]-q[2]) for j in ball if j!=ci]
        maxk=0
        for a in range(len(chords)):
            for b in range(a+1,len(chords)):
                cx=cross(prim(chords[a]),prim(chords[b]))
                if cx==(0,0,0): continue
                k=min(v3(cx[0]) if cx[0] else 999, v3(cx[1]) if cx[1] else 999, v3(cx[2]) if cx[2] else 999)
                # v3 of gcd of components:
                g=gcd(gcd(abs(cx[0]),abs(cx[1])),abs(cx[2]))
                k=v3(g)
                if k>maxk: maxk=k
        # arc structure: sort ball indices, count runs
        s=sorted(ball); runs=1
        for a in range(1,len(s)):
            if s[a]!=s[a-1]+1: runs+=1
        cap=prim_dir_capacity(2*rho)
        print(f' rho={rho:2d} N={best:3d} distinct_dirs={distinct} (=N-1? {distinct==best-1}) '
              f'geomcap(2rho)={cap} maxkappa3={maxk} pathruns={runs} N/rho={best/rho:.2f}')

if __name__=='__main__':
    L=int(sys.argv[1])
    analyze(L, [2,3,4,5,7,10])
