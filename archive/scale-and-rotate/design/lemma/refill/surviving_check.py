"""
SURVIVING-ARGUMENT verification.

CLAIM (non-circular, level-independent, PROVES qualitative boundedness):
  (P1) Anchors A_k = M.W_{k-1} are 3-separated: min over ALL nonzero integer v of
       |M v|_inf = 3.  => #anchors in any Cheb-rho ball <= (floor(2rho/3)+1)^3
       (packing), independent of k and of the walk.
  (P2) Every stitch interior is within Cheb-4 of its NEARER anchor (structural:
       word <=4 steps, each step Cheb<=2, nearer anchor <=2 steps away).
  (P3) Each anchor is NEARER-anchor of <= g interiors (g measured; structural cap 4).
  (P4) interiors per word <= 3.
  => c_k(q,rho) = a_k + b_k <= (floor(2rho/3)+1)^3 + g*(floor(2(rho+4)/3)+1)^3,
     LEVEL-INDEPENDENT, no induction, no circularity.  (Cubic, not linear.)

We verify P1 exhaustively over a v-box, and P2/P3/P4 as STRUCTURAL caps that hold
for EVERY word actually present in L5..L8 (evidence they are not exceeded), and we
check the measured anchor-crowding never exceeds the packing bound.
"""
import pickle, sys, os
from collections import defaultdict
from search193 import candidate_step_vectors
MENU = candidate_step_vectors(2)
M = ((3,0,0),(0,0,-3),(0,3,-1))
def mul(m,p): return (m[0][0]*p[0]+m[0][1]*p[1]+m[0][2]*p[2],
                       m[1][0]*p[0]+m[1][1]*p[1]+m[1][2]*p[2],
                       m[2][0]*p[0]+m[2][1]*p[1]+m[2][2]*p[2])
def cheb(a,b=None):
    if b is None: return max(abs(a[0]),abs(a[1]),abs(a[2]))
    return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

# P1: min |M v|_inf over nonzero v in a box
def check_separation(R=6):
    best=10**9; arg=None
    for a in range(-R,R+1):
     for b in range(-R,R+1):
      for c in range(-R,R+1):
        if a==0 and b==0 and c==0: continue
        v=cheb(mul(M,(a,b,c)))
        if v<best: best=v; arg=(a,b,c)
    return best,arg

def word_interiors(start,w):
    pts=[];x,y,z=start
    for si in w[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts

def load(L):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    return [tuple(a) for a in d["anchors"]], d["words"]

def structural_checks(L):
    anchors,words=load(L)
    n=len(anchors)
    max_reach_near=0; max_reach_start=0; max_int=0; max_step=0
    charge=defaultdict(int)   # anchor index -> # interiors having it as nearer
    for i in range(n-1):
        w=words[i]; L_steps=len(w)
        ints=word_interiors(anchors[i],w)
        max_int=max(max_int,len(ints))
        # steps cheb
        x,y,z=anchors[i]
        for si in w[:-1]:
            s=MENU[si]; max_step=max(max_step,cheb(s))
        for t,p in enumerate(ints):
            steps_start=t+1
            steps_end=(L_steps)-steps_start
            near = i if steps_start<=steps_end else i+1
            na=anchors[near]
            max_reach_near=max(max_reach_near,cheb(p,na))
            max_reach_start=max(max_reach_start,cheb(p,anchors[i]))
            charge[near]+=1
    g=max(charge.values()) if charge else 0
    return dict(max_int=max_int,max_step=max_step,
                max_reach_near=max_reach_near,max_reach_start=max_reach_start,g=g)

def packing_bound(rho):
    return (int(2*rho//3)+1)**3

def measure_anchor_crowding(L, rhos):
    anchors,_=load(L)
    R=lambda rho: rho+1
    out={}
    for rho in rhos:
        cell=rho+1
        grid=defaultdict(list)
        for a in anchors:
            grid[(a[0]//cell,a[1]//cell,a[2]//cell)].append(a)
        best=0
        for a in anchors:
            cx,cy,cz=a[0]//cell,a[1]//cell,a[2]//cell; c=0
            for dx in(-1,0,1):
             for dy in(-1,0,1):
              for dz in(-1,0,1):
                for b in grid.get((cx+dx,cy+dy,cz+dz),()):
                    if cheb(a,b)<=rho: c+=1
            if c>best: best=c
        out[rho]=best
    return out

if __name__=="__main__":
    print("=== P1: anchor separation  min|M v|_inf over nonzero v in box ===",flush=True)
    for R in (4,6,8):
        b,arg=check_separation(R)
        print(f"  box +/-{R}: min={b} at v={arg}",flush=True)
    print("\n=== P2/P3/P4 structural caps per level (must be <=4 reach, <=3 int, <=2 step, g<=4) ===",flush=True)
    for L in (5,6,7,8):
        s=structural_checks(L)
        print(f"  L{L}: {s}",flush=True)
    print("\n=== packing bound vs measured anchor-crowding a_k(rho) ===",flush=True)
    rhos=[1,2,3,4,6,8,10]
    print("  rho  packing(2rho/3+1)^3   a_L5 a_L6 a_L7 a_L8",flush=True)
    meas={L:measure_anchor_crowding(L,rhos) for L in (5,6,7,8)}
    for rho in rhos:
        pb=packing_bound(rho)
        print(f"  {rho:3d}  {pb:6d}              "
              f"{meas[5][rho]:4d} {meas[6][rho]:4d} {meas[7][rho]:4d} {meas[8][rho]:4d}",flush=True)
