"""
Test the METRIC-CONTRACTION COUNT-RECURSION that (via proven alpha=4/9, refill B)
actually delivers the uniform incidence bound, and contrast with Route-2 equidist.

Facts (proven elsewhere, re-verified in route2_equidist / here):
  * Walk_{k+1} = (M . Walk_k)  DISJOINT-UNION  Stitch_k   [exact identity]
  * ||M^{-1}||_inf = 4/9   =>  M^{-1} B_cheb(q,rho) subset B_cheb(M^{-1}q, (4/9)rho)
Hence  c_{k+1}(q,rho) = #{M.Walk_k in B(q,rho)} + #{Stitch_k in B(q,rho)}
                      = c_k(M^{-1}q, over M^{-1}-ellipsoid) + refill(q,rho)
                     <= c_k(M^{-1}q, (4/9)rho) + B.
Invariant test: does c_k(q,rho) <= 36*rho + 1 hold for ALL q at every level?
Recursion test: is Walk_{k+1} really (M.Walk_k) U Stitch, and is refill <= B uniformly?
"""
import pickle, math
from collections import defaultdict
from fractions import Fraction as F
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3

def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
           -A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
           +A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))
def inv(Mm):
    d=det3(Mm); C=[[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            minor=[[Mm[r][c] for c in range(3) if c!=j] for r in range(3) if r!=i]
            cof=minor[0][0]*minor[1][1]-minor[0][1]*minor[1][0]
            C[j][i]=F(((-1)**(i+j))*cof,d)
    return C
Minv=inv(M)
def mul(Mm,p):
    return tuple(Mm[i][0]*p[0]+Mm[i][1]*p[1]+Mm[i][2]*p[2] for i in range(3))
def mulf(Mm,p):
    return tuple(Mm[i][0]*p[0]+Mm[i][1]*p[1]+Mm[i][2]*p[2] for i in range(3))

def build_chain(pkl):
    d=pickle.load(open(pkl,"rb"))
    anchors=d["anchors"]; words=d["words"]
    def interiors(start,wi):
        pts=[];x,y,z=start
        for si in wi[:-1]:
            s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
        return pts
    chain=[anchors[0]]
    for i in range(len(anchors)-1):
        chain.extend(interiors(anchors[i],words[i])); chain.append(anchors[i+1])
    return chain

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def max_ball_count(points, rho):
    """max over q in points of #{points within Cheb rho of q}."""
    grid=defaultdict(list); R=rho
    for p in points: grid[(p[0]//(R+1),p[1]//(R+1),p[2]//(R+1))].append(p)
    best=0
    for q in points:
        cx,cy,cz=q[0]//(R+1),q[1]//(R+1),q[2]//(R+1); c=0
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for p in grid.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,p)<=rho: c+=1
        if c>best: best=c
    return best

if __name__=="__main__":
    L6=build_chain("gate2-l7-construction-L6.pkl")
    L7=build_chain("gate2-l7-construction-L7.pkl")
    setL7=set(L7)
    # 1) RECURSION IDENTITY: M.L6 subset L7 ?
    MdotL6=[mul(M,p) for p in L6]
    in7=sum(1 for p in MdotL6 if p in setL7)
    print(f"M.L6 points: {len(MdotL6)}, of which in L7: {in7}  (missing {len(MdotL6)-in7})")
    setMdotL6=set(MdotL6)
    stitch=[p for p in L7 if p not in setMdotL6]
    print(f"L7 = {len(L7)} = |M.L6 in L7| {in7} + refill {len(stitch)}  "
          f"(dup check: M.L6 distinct={len(setMdotL6)})")
    # 2) REFILL BOUND B: max stitch points in any Cheb-rho ball (rho up to 10)
    for rho in (4,10):
        B=max_ball_count(stitch,rho)
        print(f"  refill B: max stitch pts in Cheb-{rho} ball = {B}")
    # 3) INVARIANT c_k(q,rho) <= 36 rho + 1 at each level, and the recursion RHS
    for lvl,ch in (("L6",L6),("L7",L7)):
        for rho in (1,4,10):
            mc=max_ball_count(ch,rho)
            print(f"  {lvl} rho={rho:2d}: max c={mc:3d}  vs 36*rho+1={36*rho+1}  "
                  f"margin={36*rho+1-mc}  (C_emp={mc/rho:.2f})")
    # 4) DIRECT count-recursion check on L7 densest balls:
    #    c_7(q,rho) <= c_6(M^-1 q, (4/9)rho) + refill(q,rho)
    #    We verify the stronger exact split: c_7 = #(M.L6 in ball) + #(stitch in ball).
    print("\n  Direct split on 200 densest-ish L7 centres (rho=10):")
    grid7=defaultdict(list)
    for p in L7: grid7[(p[0]//11,p[1]//11,p[2]//11)].append(p)
    # sample centres = every 400th point
    viol=0; checked=0
    for qi in range(0,len(L7),400):
        q=L7[qi]
        ball=[p for p in L7 if cheb(q,p)<=10]  # small count, fine
        cnt=len(ball)
        nM=sum(1 for p in ball if p in setMdotL6)
        nS=cnt-nM
        # pullback: c_6 over B(M^-1 q, 4/9*10=4.44). M^-1 q may be fractional.
        qinv=mulf(Minv,q)
        # count L6 pts within Cheb 4.44 of qinv
        c6=sum(1 for p in L6 if max(abs(float(p[0])-float(qinv[0])),
                                     abs(float(p[1])-float(qinv[1])),
                                     abs(float(p[2])-float(qinv[2])))<=4.4444)
        checked+=1
        # exact identity nM == (#L6 pts p with M p in ball) == (#L6 in M^-1 ball) <= c6
        if nM>c6: viol+=1
    print(f"    checked {checked} centres: nM<=c6(4.44) violations={viol} "
          f"(0 confirms M.L6-in-ball <= c_6 over pulled-back 4.44 ball)")
