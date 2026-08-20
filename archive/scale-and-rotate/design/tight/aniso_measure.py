"""
ROUTE 3 - ANISOTROPIC COUNT-RECURSION.  Empirical test of the anisotropic pull-back
vs the isotropic ||M^-1||_inf = 4/9 overcount, plus the EXACT telescoping decomposition
of crowding by BIRTH LEVEL.

Key algebraic facts (verified separately, exact fractions):
  * M eigenvalues all have modulus exactly 3 (block char poly lam^2+lam+9).
  * ||M^-j||_inf decays like ~3^-j (elliptic), NOT (4/9)^j.  S=sum_j||M^-j||=1.6769 < 9/5=1.8.

EXACT telescoping identity (from the disjoint union Walk_k = M.Walk_{k-1} + Stitch_k):
  c_k(q,rho) = sum_{j>=0} #{ Stitch_{k-j} points, mapped up by M^j, inside B(q,rho) }
             = sum_{j>=0} #{ walk_k points of BIRTH LEVEL (k-j) inside B(q,rho) }
Every walk point has a unique birth level; M just rescales, preserving birth level.
So t_j(q,rho) := #{birth-(k-j) points in B(q,rho)} and c_k = sum_j t_j EXACTLY.
This measures how fast crowding is dominated by recently-born (small-j) points -- the
per-level refill contribution in the true (thin, sheared) pulled-back regions.
"""
import pickle, sys, json
from collections import defaultdict
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)

def Mp(p):   # M . p ,  M=((3,0,0),(0,0,-3),(0,3,-1))
    return (3*p[0], -3*p[2], 3*p[1]-p[2])

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def interiors(start, wi):
    pts=[]; x,y,z=start
    for si in wi[:-1]:
        s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
    return pts

def build(L):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    A=d["anchors"]; W=d["words"]
    walk=[]
    for i in range(len(A)-1):
        walk.append(A[i]); walk.extend(interiors(A[i],W[i]))
    walk.append(A[-1])
    return walk, A, W

def build_tagged(Lmax, Lbase=5):
    """Return dict L -> (walk_pts, tags) with birth-level tags; base level all tagged Lbase."""
    out={}
    walk, A, W = build(Lbase)
    tags=[Lbase]*len(walk)
    out[Lbase]=(walk,tags)
    for L in range(Lbase+1, Lmax+1):
        d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
        A=d["anchors"]; W=d["words"]
        pw, ptags = out[L-1]
        # anchors[i] == M(pw[i]); verify + inherit tag
        assert len(A)==len(pw), (L, len(A), len(pw))
        walk=[]; tags=[]
        for i in range(len(A)-1):
            assert A[i]==Mp(pw[i])
            walk.append(A[i]); tags.append(ptags[i])          # inherited birth
            for ip in interiors(A[i],W[i]):
                walk.append(ip); tags.append(L)               # born at level L
        walk.append(A[-1]); tags.append(ptags[-1])
        out[L]=(walk,tags)
    return out

def grid_of(points, R):
    g=defaultdict(list)
    for idx,p in enumerate(points):
        g[(p[0]//R, p[1]//R, p[2]//R)].append(idx)
    return g

def max_ball(centres, points, rho):
    """max over q in centres of #{p in points: cheb<=rho}; returns (best, argq, hit_idx_list)."""
    R=rho+1; g=grid_of(points,R)
    best=0; bq=None; bhit=None
    for q in centres:
        cx,cy,cz=q[0]//R,q[1]//R,q[2]//R; hits=[]
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for idx in g.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,points[idx])<=rho: hits.append(idx)
        if len(hits)>best: best=len(hits); bq=q; bhit=hits
    return best,bq,bhit

def count_ball(q, points, rho, grid=None, R=None):
    if grid is None:
        R=rho+1; grid=grid_of(points,R)
    cx,cy,cz=q[0]//R,q[1]//R,q[2]//R; c=0
    for dx in(-1,0,1):
     for dy in(-1,0,1):
      for dz in(-1,0,1):
        for idx in grid.get((cx+dx,cy+dy,cz+dz),()):
            if cheb(q,points[idx])<=rho: c+=1
    return c

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [6,7,8]
    Lmax=max(levels)
    tagged=build_tagged(Lmax, Lbase=5)
    result={}
    for L in levels:
        walk,tags=tagged[L]
        parent_walk = tagged[L-1][0] if (L-1) in tagged else None
        anchors=[walk[i] for i in range(len(walk)) if False]  # placeholder
        # anchors = birth-tag < L points; stitch = birth==L
        anchset=[walk[i] for i in range(len(walk)) if tags[i]<L]
        stitch =[walk[i] for i in range(len(walk)) if tags[i]==L]
        print(f"\n=== L{L}: {len(walk)} pts | anchors {len(anchset)} | stitch {len(stitch)} ===",flush=True)
        # birth histogram
        bh=defaultdict(int)
        for t in tags: bh[t]+=1
        print("birth-level counts:", dict(sorted(bh.items())))
        rows=[]
        # precompute grids for walk
        for rho in range(1,11):
            R=rho+1
            gwalk=grid_of(walk,R)
            # c_k(rho): max crowding, argmax ball, birth decomposition
            c,bq,bhit=max_ball(walk, walk, rho)
            tj=defaultdict(int)
            for idx in bhit: tj[L-tags[idx]]+=1     # j = k - birth
            tj=dict(sorted(tj.items()))
            # anchor crowding a_k and stitch crowding b_k (independent maxima)
            a,aq,ahit=max_ball(anchset, anchset, rho) if anchset else (0,None,[])
            b,bqk,bhk =max_ball(stitch, stitch, rho) if stitch else (0,None,[])
            # ISOTROPIC vs ANISOTROPIC anchor overcount at the anchor argmax ball:
            # true a_k(aq,rho) = #anchors in B ; isotropic bound = #parent in B(Minv aq,(4/9)rho)
            iso=None
            if parent_walk is not None and aq is not None:
                # Minv aq : parent coords ; aq = M(parent). recover parent center = Minv(aq)
                X,Y,Z=aq
                # Minv=[[1/3,0,0],[0,-1/9,1/3],[0,-1/3,0]] -> center (X/3, -Y/9+Z/3, -Y/3) (rational)
                # isotropic ball radius (4/9)rho in parent coords, real-valued center: count parent pts p
                # with max(|p0 - X/3|,|p1-(-Y/9+Z/3)|,|p2-(-Y/3)|) <= (4/9)rho
                cx0=X/3.0; cy0=(-Y/9.0+Z/3.0); cz0=(-Y/3.0); rr=(4.0/9.0)*rho
                iso=sum(1 for p in parent_walk if abs(p[0]-cx0)<=rr and abs(p[1]-cy0)<=rr and abs(p[2]-cz0)<=rr)
            rows.append(dict(rho=rho, c=c, birth_decomp_tj=tj, a_anchor=a, b_stitch=b,
                             iso_bound_for_a=iso, overcount_ratio=(iso/a if (iso and a) else None),
                             c_over_rho=round(c/rho,3)))
            print(f" rho={rho:2d}  c={c:3d} (c/rho={c/rho:.2f})  a={a:3d} b={b:3d}  "
                  f"iso_bound(a)={iso}  overcount={ (iso/a if (iso and a) else None) }  tj={tj}",flush=True)
        result[f"L{L}"]=rows
    json.dump(result, open("design/tight/aniso_measure.json","w"), indent=1)
    print("\nwrote design/tight/aniso_measure.json")
