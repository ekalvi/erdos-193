"""ROUTE 1 SELF-EXCLUSION TEST.
For every walk-centered Cheb-rho ball (rho<=10), extract the PASSES (maximal
contiguous walk-arcs meeting the ball). For each COEXISTING pair of passes in a
ball, measure:
  - angle theta between the two arcs' direction vectors (endpoints of the arc's
    in-ball portion; primitive lattice direction),
  - separation s = min Chebyshev distance between points of the two arcs,
  - the minimum |cross product| of any (a1a2) x (a1 b) triple with a1,a2 on arc A
    and b on arc B  (=0 would be an ACTUAL collinear triple -> forbidden).
Question: are close + near-parallel coexisting passes ABSENT (forbidden region in
(theta,s) plane)?  If they coexist freely, triple-free self-exclusion FAILS to
bound the pass count.

Also: for the densest / max-A balls, dump the full pairwise table.
"""
import sys, pickle, json, math
from collections import defaultdict
from math import gcd
sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors

def load_chain(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl","rb"))
    anchors=d["anchors"]; words=d["words"]
    chain=[anchors[0]]
    for i in range(len(anchors)-1):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i+1])
    return chain

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def norm(a): return math.sqrt(dot(a,a))
def prim(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    if g==0: return (0,0,0)
    return (v[0]//g,v[1]//g,v[2]//g)

def grid_index(chain, cell):
    g=defaultdict(list)
    for i,p in enumerate(chain):
        g[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
    return g

def arcs_of(idxs):
    idxs=sorted(idxs); arcs=[]; cur=[idxs[0]]
    for a in idxs[1:]:
        if a==cur[-1]+1: cur.append(a)
        else: arcs.append(cur); cur=[a]
    arcs.append(cur)
    return arcs

def arc_dir(chain, arc):
    # direction of the in-ball portion: last - first (fallback to +/- step if len1)
    if len(arc)>=2:
        return sub(chain[arc[-1]], chain[arc[0]])
    # single point: use adjacent chain step as tangent
    i=arc[0]
    if i+1<len(chain): return sub(chain[i+1],chain[i])
    return sub(chain[i],chain[i-1])

def angle_deg(u,v):
    nu,nv=norm(u),norm(v)
    if nu==0 or nv==0: return None
    c=dot(u,v)/(nu*nv)
    c=max(-1.0,min(1.0,c))
    return math.degrees(math.acos(abs(c)))  # undirected angle 0..90

def min_triple_cross(chain, arcA, arcB):
    """min |cross((a2-a1),(b-a1))| over a1,a2 in A (a1!=a2), b in B.
    0 would be a real collinear triple. Only meaningful if len(arcA)>=2."""
    if len(arcA)<2: return None
    best=None
    ptsA=[chain[i] for i in arcA]; ptsB=[chain[i] for i in arcB]
    for x in range(len(ptsA)):
        for y in range(len(ptsA)):
            if x==y: continue
            d=sub(ptsA[y],ptsA[x])
            for b in ptsB:
                w=sub(b,ptsA[x])
                cx=cross(d,w)
                m=abs(cx[0])+abs(cx[1])+abs(cx[2])
                if best is None or m<best: best=m
    return best

def analyze(level, dump_rhos=(2,4,6,8,10)):
    chain=load_chain(level); N=len(chain)
    print(f"=== L{level}: N={N} ===")
    summary={}
    for rho in range(1,11):
        cell=rho; grid=grid_index(chain,cell)
        # global scatter of coexisting-pair (theta,s); track forbidden-region test
        pair_records=[]   # (theta, s, mincross, nA, nB)
        maxA=0; max_ball=None
        for qi,q in enumerate(chain):
            cx,cy,cz=q[0]//cell,q[1]//cell,q[2]//cell
            idxs=[]
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for j in grid.get((cx+dx,cy+dy,cz+dz),()):
                            if cheb(chain[j],q)<=rho: idxs.append(j)
            arcs=arcs_of(idxs); A=len(arcs)
            if A>maxA:
                maxA=A; max_ball=(qi,arcs)
            if A>=2:
                for x in range(len(arcs)):
                    for y in range(x+1,len(arcs)):
                        u=arc_dir(chain,arcs[x]); v=arc_dir(chain,arcs[y])
                        th=angle_deg(u,v)
                        s=min(cheb(chain[i],chain[j]) for i in arcs[x] for j in arcs[y])
                        mc=min_triple_cross(chain,arcs[x],arcs[y])
                        mc2=min_triple_cross(chain,arcs[y],arcs[x])
                        mcs=[m for m in (mc,mc2) if m is not None]
                        mcmin=min(mcs) if mcs else None
                        pair_records.append((th,s,mcmin,len(arcs[x]),len(arcs[y])))
        # forbidden-region test: among coexisting pairs, is there any with
        # small angle AND small separation? define near-parallel theta<15deg,
        # close s<=rho. Report the closest+most-parallel coexisting pair.
        npar=[r for r in pair_records if r[0] is not None]
        n_close_par = sum(1 for (th,s,mc,a,b) in npar if th<15.0 and s<=max(1,rho//2))
        # min angle among coexisting pairs; min separation among near-parallel(<20)
        min_angle = min((r[0] for r in npar), default=None)
        # smallest cross seen (approaching 0 => near a real triple, but must be >0)
        min_cross = min((r[2] for r in npar if r[2] is not None), default=None)
        summary[rho]={
            "maxA":maxA,
            "n_coexisting_pairs":len(pair_records),
            "min_angle_deg":round(min_angle,2) if min_angle is not None else None,
            "n_close_and_near_parallel(theta<15,s<=rho/2)":n_close_par,
            "min_triple_cross_over_all_pairs":min_cross,
        }
        if rho in dump_rhos and max_ball:
            qi,arcs=max_ball
            q=chain[qi]
            tbl=[]
            for x in range(len(arcs)):
                for y in range(x+1,len(arcs)):
                    u=arc_dir(chain,arcs[x]); v=arc_dir(chain,arcs[y])
                    th=angle_deg(u,v)
                    s=min(cheb(chain[i],chain[j]) for i in arcs[x] for j in arcs[y])
                    mc=min_triple_cross(chain,arcs[x],arcs[y])
                    mc2=min_triple_cross(chain,arcs[y],arcs[x])
                    mcs=[m for m in (mc,mc2) if m is not None]
                    tbl.append({"arcs":(len(arcs[x]),len(arcs[y])),
                                "theta_deg":round(th,1) if th is not None else None,
                                "sep":s,
                                "min_triple_cross":min(mcs) if mcs else None})
            summary[rho]["densest_ball_dump"]={
                "center":list(q),"A":len(arcs),
                "arclens":[len(a) for a in arcs],"pairs":tbl}
    print(json.dumps(summary,indent=1))
    return {"level":level,"N":N,"per_rho":summary}

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [6,7]
    out={}
    for lv in levels:
        out[lv]=analyze(lv)
    json.dump(out, open("/Users/erik/homelab/math193/design/lemma/route1/selfexcl-results.json","w"),indent=1)
    # aggregate verdict
    print("\n=== SELF-EXCLUSION VERDICT ===")
    for lv in levels:
        for rho in range(1,11):
            s=out[lv]["per_rho"][rho]
            print(f"L{lv} rho={rho:2d} maxA={s['maxA']} pairs={s['n_coexisting_pairs']:4d} "
                  f"min_angle={s['min_angle_deg']} close&par={s['n_close_and_near_parallel(theta<15,s<=rho/2)']} "
                  f"min_triple_cross={s['min_triple_cross_over_all_pairs']}")
