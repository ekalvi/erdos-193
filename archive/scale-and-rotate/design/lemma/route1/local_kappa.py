"""Test: is the proven global kappa_3<=12 EVER active inside a Cheb-rho ball (rho<=10)?
For each anchor, look at all chords to walk points within radius rho; kappa_3 of a
pair = v_3(gcd(cross(prim_a,prim_b))). Compare observed local max to the pure
MAGNITUDE ceiling floor(log_3(8*rho^2)) which holds for ANY two sup-norm<=2rho vecs."""
import pickle, sys, math
from math import gcd
from collections import defaultdict
from gate_run import word_interiors
def build_chain(L):
    d=pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    a=d['anchors']; w=d['words']; ch=[a[0]]
    for i in range(len(w)): ch+=word_interiors(a[i],w[i]); ch+=[a[i+1]]
    return ch
def prim(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    if g==0: return (0,0,0)
    w=(v[0]//g,v[1]//g,v[2]//g)
    for c in w:
        if c: return w if c>0 else (-w[0],-w[1],-w[2])
    return w
def v3(n):
    n=abs(n)
    if n==0: return 999
    c=0
    while n%3==0: n//=3; c+=1
    return c
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
L=int(sys.argv[1]); rho=10
pts=build_chain(L); n=len(pts)
cell=rho; grid=defaultdict(list)
for i,p in enumerate(pts): grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
maxk=0; kdist=defaultdict(int); maxcross=0
stride=max(1,n//4000)  # sample ~4000 anchors for speed
for ci in range(0,n,stride):
    q=pts[ci]; gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
    ball=[]
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            for dz in(-1,0,1):
                for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                    if j!=ci and cheb(pts[j],q)<=rho: ball.append(j)
    chords=[prim((pts[j][0]-q[0],pts[j][1]-q[1],pts[j][2]-q[2])) for j in ball]
    for a in range(len(chords)):
        for b in range(a+1,len(chords)):
            cx=cross(chords[a],chords[b])
            if cx==(0,0,0): continue
            g=gcd(gcd(abs(cx[0]),abs(cx[1])),abs(cx[2]))
            k=v3(g); kdist[k]+=1
            if k>maxk: maxk=k
            m=max(abs(cx[0]),abs(cx[1]),abs(cx[2]))
            if m>maxcross: maxcross=m
ceil=math.floor(math.log(8*rho*rho,3))
print(f'L{L} rho={rho}: sampled {len(range(0,n,stride))} anchors')
print(f'  observed LOCAL max kappa_3 = {maxk}   (global proven bound = 12)')
print(f'  magnitude ceiling floor(log3(8*rho^2)) = floor(log3({8*rho*rho}))={ceil}  (holds for ANY sup-norm<=2rho pair)')
print(f'  max |cross component| seen locally = {maxcross}  (3^12={3**12})')
print(f'  local kappa_3 distribution: {dict(sorted(kdist.items()))}')
