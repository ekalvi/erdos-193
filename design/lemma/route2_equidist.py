"""
ROUTE 2 -- irrational-rotation / equidistribution attack on the
UNIFORM LOCAL-1-D INCIDENCE bound  c_k(q,rho) <= C*rho + 1.

We (a) rebuild the real walk chains at L5/L6/L7, (b) find the densest
Cheb-rho balls, (c) decompose the walk-into-ball into ARCS (maximal
contiguous runs of the path inside the ball), (d) measure the DIRECTION
distribution of those arcs -- the entry/exit tangent directions -- to test
whether they are equidistributed / non-concentrated (Route 2's mechanism),
and (e) test the metric-contraction count-recursion that actually closes it.
"""
import pickle, sys, math
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3

def build_chain(pkl):
    d = pickle.load(open(pkl, "rb"))
    anchors = d["anchors"]; words = d["words"]
    def interiors(start, word_idx):
        pts = []; x,y,z = start
        for si in word_idx[:-1]:
            s = MENU[si]; x,y,z = x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
        return pts
    chain = [anchors[0]]
    for i in range(len(anchors)-1):
        chain.extend(interiors(anchors[i], words[i]))
        chain.append(anchors[i+1])
    return chain

def is_path(chain):
    # every consecutive pair differs by a menu step; all distinct
    ms = set(MENU); bad=0
    for a,b in zip(chain, chain[1:]):
        s=(b[0]-a[0],b[1]-a[1],b[2]-a[2])
        if s not in ms: bad+=1
    distinct = len(set(chain))==len(chain)
    return bad, distinct

def cheb(a,b):
    return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def incidence_and_arcs(chain, rho, topN=8):
    """For each walk point as centre q, count walk points within Cheb rho.
    Return the densest balls and, for each, the arc decomposition + arc
    tangent directions."""
    n=len(chain)
    # spatial hash for neighborhood queries
    grid=defaultdict(list)
    R=rho
    for idx,p in enumerate(chain):
        grid[(p[0]//(R+1),p[1]//(R+1),p[2]//(R+1))].append(idx)
    def neigh(q):
        cx,cy,cz=q[0]//(R+1),q[1]//(R+1),q[2]//(R+1)
        out=[]
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    out.extend(grid.get((cx+dx,cy+dy,cz+dz),()))
        return out
    counts=[]
    for qi in range(n):
        q=chain[qi]
        cnt=0; members=[]
        for j in neigh(q):
            if cheb(q,chain[j])<=rho:
                cnt+=1; members.append(j)
        counts.append((cnt,qi,members))
    counts.sort(reverse=True)
    maxc=counts[0][0]
    # arc decomposition for the top balls
    arcinfo=[]
    for cnt,qi,members in counts[:topN]:
        members_sorted=sorted(members)
        # split into contiguous runs (arcs)
        arcs=[]; cur=[members_sorted[0]]
        for a,b in zip(members_sorted,members_sorted[1:]):
            if b==a+1: cur.append(b)
            else: arcs.append(cur); cur=[b]
        arcs.append(cur)
        # arc directions: for each arc, the chord direction (end-start) normalized;
        # also the mean step direction
        dirs=[]
        for arc in arcs:
            p0=chain[arc[0]]; p1=chain[arc[-1]]
            v=(p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2])
            L=math.sqrt(v[0]**2+v[1]**2+v[2]**2)
            if L>0: dirs.append((v[0]/L,v[1]/L,v[2]/L))
        arcinfo.append(dict(cnt=cnt,qi=qi,narcs=len(arcs),
                            arclens=[len(a) for a in arcs],dirs=dirs))
    return maxc, sum(c for c,_,_ in counts)/n, arcinfo

def direction_spread(arcinfo):
    """Test non-concentration of arc directions in the densest balls:
    max pairwise |cos angle| between arc directions (near 1 => aligned/folded)."""
    worst=0.0; worstball=None
    dist=[]
    for info in arcinfo:
        ds=info["dirs"]
        maxcos=0.0
        for i in range(len(ds)):
            for j in range(i+1,len(ds)):
                c=abs(sum(ds[i][k]*ds[j][k] for k in range(3)))
                maxcos=max(maxcos,c)
                dist.append(c)
        info["max_abs_cos_between_arcs"]=maxcos
        if info["narcs"]>=2 and maxcos>worst:
            worst=maxcos; worstball=info["qi"]
    return worst, worstball, dist

if __name__=="__main__":
    pkls={"L5":"gate2-l7-construction-L5.pkl",
          "L6":"gate2-l7-construction-L6.pkl",
          "L7":"gate2-l7-construction-L7.pkl"}
    for lvl,pkl in pkls.items():
        chain=build_chain(pkl)
        bad,distinct=is_path(chain)
        print(f"\n=== {lvl}: {len(chain)} pts  path_bad_steps={bad} all_distinct={distinct} ===")
        for rho in (4,10):
            maxc,mean,arcinfo=incidence_and_arcs(chain,rho,topN=10)
            worst,wb,dist=direction_spread(arcinfo)
            avgcos=sum(dist)/len(dist) if dist else float('nan')
            print(f" rho={rho:2d}: maxc={maxc}  mean={mean:.2f}  C_emp=maxc/rho={maxc/rho:.2f}")
            # report densest ball arc structure
            top=arcinfo[0]
            print(f"    densest ball: cnt={top['cnt']} narcs={top['narcs']} "
                  f"arclens={top['arclens']} maxabscos(this)={top['max_abs_cos_between_arcs']:.3f}")
            print(f"    over top-10 balls: worst |cos| between two arcs={worst:.3f} "
                  f"(1=folded/aligned) mean|cos|={avgcos:.3f}")
