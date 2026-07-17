"""
CRUX SEPARATION & REDUCTION TEST (2026-07-16).

Question (from the parent task): does restricting Lemma R to the SPARSE REALIZED
orbit (self-avoidance, single connector per gap) provably cap the incident-arc
count / give a level-uniform single-level refill slope E where the CLOSURE
(all legal connectors per gap) cannot -- or is self-avoidance IRRELEVANT to E
(the linear-vs-cubic slope), only removing the per-gap menu multiplicity constant?

We measure on the realized gate2 L6/L7/L8 chains:
  a(rho)  = anchor crowding      (= c_{k-1}, the recursion one level down)
  b(rho)  = interior refill      (the E quantity: # stitch interiors in a ball)
  I(rho)  = arc-incidence        (# distinct connector-arcs/gaps meeting a ball)
and the ratios b/a, I/a plus the log-log slope of each in rho.

Then we quantify the CLOSURE over-approximation: per gap, the domain of ALL legal
connector words (connector_domains4.pkl). Closure refill = a(rho+4) x (corridor
box size); closure arc-incidence = I_real(rho) x (domain size). We sample domain
corridor sizes to pin the closure multiplicity constant.

Centres: lattice/point-centred sup (the standard lower bound used throughout;
matches route4 / ahlfors_ck). rho = 1..10.
"""
import json, os, pickle, sys, time, math
os.chdir("/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3

MENU = gate_run.MENU

def build(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]; parent = d["parent_word"]
    ng = len(anchors) - 1
    # chain with gap-id per point. anchor j -> touches gaps j-1,j. interior of gap i -> gap i.
    pt_gaps = {}   # point -> set of gap ids
    interiors = [] # list of (point, gapid)
    chain = []
    def touch(p, g):
        pt_gaps.setdefault(p, set()).add(g)
    a0 = anchors[0]; chain.append(a0); touch(a0, 0)
    for i in range(ng):
        ints = gate_run.word_interiors(anchors[i], words[i])
        for p in ints:
            interiors.append((p, i)); chain.append(p); touch(p, i)
        ap = anchors[i+1]; chain.append(ap); touch(ap, i);
        if i+1 <= ng-1: touch(ap, i+1)
    anchors_pts = list(anchors)
    interior_pts = [p for (p,_) in interiors]
    return dict(anchors=anchors_pts, interior_pts=interior_pts,
                pt_gaps=pt_gaps, chain=chain, parent=parent, ng=ng)

def build_hash(points, cell):
    H = {}
    for p in points:
        H.setdefault((p[0]//cell, p[1]//cell, p[2]//cell), []).append(p)
    return H

def ball_points(H, cell, q, rho):
    res = []
    kx0=(q[0]-rho)//cell; kx1=(q[0]+rho)//cell
    ky0=(q[1]-rho)//cell; ky1=(q[1]+rho)//cell
    kz0=(q[2]-rho)//cell; kz1=(q[2]+rho)//cell
    for kx in range(kx0,kx1+1):
        for ky in range(ky0,ky1+1):
            for kz in range(kz0,kz1+1):
                b=H.get((kx,ky,kz))
                if not b: continue
                for p in b:
                    if abs(p[0]-q[0])<=rho and abs(p[1]-q[1])<=rho and abs(p[2]-q[2])<=rho:
                        res.append(p)
    return res

def sup_count(centres, target_pts, rhos, cell=11):
    H = build_hash(target_pts, cell)
    out={}
    for rho in rhos:
        m=0
        for q in centres:
            c=len(ball_points(H,cell,q,rho))
            if c>m: m=c
        out[rho]=m
    return out

def sup_arc_incidence(centres, chain, pt_gaps, rhos, cell=11):
    H = build_hash(chain, cell)
    out={}
    for rho in rhos:
        m=0
        for q in centres:
            pts=ball_points(H,cell,q,rho)
            gaps=set()
            for p in pts:
                gaps |= pt_gaps.get(p,())
            if len(gaps)>m: m=len(gaps)
        out[rho]=m
    return out

def loglog_slope(rhos, vals):
    xs=[math.log(r) for r in rhos]; ys=[math.log(v) for v in vals]
    n=len(xs); sx=sum(xs); sy=sum(ys); sxx=sum(x*x for x in xs); sxy=sum(x*y for x,y in zip(xs,ys))
    return (n*sxy-sx*sy)/(n*sxx-sx*sx)

def main():
    t0=time.time()
    rhos=[1,2,3,4,5,6,7,8,9,10]
    out={"rhos":rhos, "levels":{}}
    for L in (6,7,8):
        W=build(L)
        # subsample centres for speed at L8 (densest-first not needed for lower bound; use stride)
        chain=W["chain"]
        stride = 1 if L<=6 else (3 if L==7 else 9)
        centres = chain[::stride]
        a = sup_count(centres, W["anchors"], rhos)
        b = sup_count(centres, W["interior_pts"], rhos)
        I = sup_arc_incidence(centres, chain, W["pt_gaps"], rhos)
        av=[a[r] for r in rhos]; bv=[b[r] for r in rhos]; Iv=[I[r] for r in rhos]
        out["levels"][str(L)]={
            "nA":len(W["anchors"]),"nI":len(W["interior_pts"]),"ngaps":W["ng"],
            "centres_used":len(centres),
            "a_anchor_crowd":av, "b_interior_refill":bv, "I_arc_incidence":Iv,
            "ratio_b_over_a":[round(bv[i]/av[i],3) for i in range(len(rhos))],
            "ratio_I_over_a":[round(Iv[i]/av[i],3) for i in range(len(rhos))],
            "slope_a":round(loglog_slope(rhos,av),3),
            "slope_b":round(loglog_slope(rhos,bv),3),
            "slope_I":round(loglog_slope(rhos,Iv),3),
            "E_b_over_rho_max":round(max(bv[i]/rhos[i] for i in range(len(rhos))),3),
            "E_I_over_rho_max":round(max(Iv[i]/rhos[i] for i in range(len(rhos))),3),
        }
        print("done L%d t=%.1f a=%s b=%s I=%s"%(L,time.time()-t0,av,bv,Iv),flush=True)

    # CLOSURE multiplicity: sample domain corridor sizes per gap on L6.
    d4=pickle.load(open("connector_domains4.pkl","rb"))
    doms=d4["domains"]
    W6=build(6); anchors=W6["anchors"]; parent=W6["parent"]
    import random; random.seed(1)
    gaps=random.sample(range(W6["ng"]), 200)
    dom_sizes=[]; corridor_sizes=[]
    for i in gaps:
        p=parent[i]
        words=doms.get(p, doms.get(str(p)))
        if words is None: continue
        dom_sizes.append(len(words))
        # union of interiors over ALL domain words anchored at anchors[i]
        u=set()
        for w in words:
            for pt in gate_run.word_interiors(anchors[i], w):
                u.add(pt)
        corridor_sizes.append(len(u))
    def stats(x):
        x=sorted(x); n=len(x)
        return {"n":n,"min":x[0],"median":x[n//2],"mean":round(sum(x)/n,1),"max":x[-1]}
    out["closure_multiplicity_L6_sample"]={
        "domain_size_per_gap": stats(dom_sizes),
        "corridor_distinct_interior_pts_per_gap": stats(corridor_sizes),
        "note":"realized fills a gap with <=4 interior pts; closure (all legal connectors) fills the whole corridor box (median corridor size below); both anchored on the SAME skeleton -> same rho-scaling, different constant."
    }
    out["elapsed_sec"]=round(time.time()-t0,1)
    json.dump(out, open("design/lemma/realized_sep_reduction-results.json","w"), indent=2)
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
