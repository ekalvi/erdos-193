"""
EXECUTE-MEASURE for the cross-entropy / subword-complexity wildcard.

On gate2 L6/L7/L8 we compute the three quantities requested:
 (a) SUBWORD COMPLEXITY p(n) of the walk's instruction (menu-letter) sequence.
     Linear/polynomial => curve-like; exponential => blob.
 (b) CROSS-ENTROPY / KL divergence between step-distributions of pairs of
     PATH-ARCS that co-occupy a common Cheb-ball. Is there a divergence FLOOR
     that grows with stacking (the twist-driven dissimilarity), or is it 0?
 (c) PER-BALL ARC ENTROPY vs rho: entropy of the arc-identity distribution of
     points inside B(q,rho). Slope in log rho gives the crowding exponent;
     compare to the R^0.65 arc-count slope and the O(rho)=slope-1 target.

Arcs are contiguous path-visits inside the ball (route3 convention).
Run: pypy3 design/entropy/measure_entropy.py
"""
import sys, pickle, json, math, random
from collections import defaultdict

sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_interiors

MENU = candidate_step_vectors(2)
IDX = {s: i for i, s in enumerate(MENU)}
# unit directions of each menu vector
UNIT = []
for s in MENU:
    n = math.sqrt(s[0]*s[0]+s[1]*s[1]+s[2]*s[2])
    UNIT.append((s[0]/n, s[1]/n, s[2]/n))

random.seed(193)


def load(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl", "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = [anchors[0]]
    letters = []                     # letter of each edge (outgoing step)
    for i in range(len(anchors) - 1):
        w = words[i]
        letters.extend(w)
        chain.extend(word_interiors(anchors[i], w))
        chain.append(anchors[i + 1])
    # sanity: len(letters) == len(chain)-1 and each diff is that menu vector
    return chain, letters


# ---------- (a) subword complexity ----------
def subword_complexity(letters, nmax):
    p = {}
    L = len(letters)
    for n in range(1, nmax + 1):
        seen = set()
        for i in range(0, L - n + 1):
            seen.add(tuple(letters[i:i + n]))
        p[n] = len(seen)
        if p[n] == L - n + 1:      # already all-distinct; will stay maximal
            for m in range(n + 1, nmax + 1):
                p[m] = L - m + 1
            break
    return p


# ---------- spatial hash ----------
def build_hash(chain, cell):
    H = defaultdict(list)
    for i, p in enumerate(chain):
        H[(p[0]//cell, p[1]//cell, p[2]//cell)].append(i)
    return H


def within(H, cell, q, rho):
    kx0=(q[0]-rho)//cell; kx1=(q[0]+rho)//cell
    ky0=(q[1]-rho)//cell; ky1=(q[1]+rho)//cell
    kz0=(q[2]-rho)//cell; kz1=(q[2]+rho)//cell
    out=[]
    for kx in range(kx0,kx1+1):
        for ky in range(ky0,ky1+1):
            for kz in range(kz0,kz1+1):
                b=H.get((kx,ky,kz))
                if not b: continue
                for i in b:
                    p=q  # center
                    pt=CHAIN[i]
                    if abs(pt[0]-q[0])<=rho and abs(pt[1]-q[1])<=rho and abs(pt[2]-q[2])<=rho:
                        out.append(i)
    return out


def arcs_of(idxs):
    idxs.sort()
    arcs=[]; cur=[idxs[0]]
    for a in idxs[1:]:
        if a==cur[-1]+1: cur.append(a)
        else: arcs.append(cur); cur=[a]
    arcs.append(cur)
    return arcs


def arc_stepdist(arc, letters, nlet):
    """histogram over menu letters of the edges internal to the arc, plus mean unit dir."""
    h=[0]*nlet
    mx=my=mz=0.0
    cnt=0
    for k in range(len(arc)-1):
        i=arc[k]
        le=letters[i]
        h[le]+=1
        u=UNIT[le]; mx+=u[0]; my+=u[1]; mz+=u[2]; cnt+=1
    if cnt==0:
        # singleton arc: use its outgoing edge if exists
        i=arc[0]
        if i < len(letters):
            le=letters[i]; h[le]+=1; u=UNIT[le]; mx,my,mz=u; cnt=1
    return h, (mx,my,mz), cnt


def kl(P, Q, alpha=0.5):
    """symmetric-ish: return D(P||Q) with add-alpha smoothing over the union support size."""
    # smoothing over full alphabet is too diffuse; smooth over union support
    supp=set(i for i in range(len(P)) if P[i] or Q[i])
    if not supp: return 0.0
    sp=sum(P)+alpha*len(supp); sq=sum(Q)+alpha*len(supp)
    d=0.0
    for i in supp:
        p=(P[i]+alpha)/sp; q=(Q[i]+alpha)/sq
        d+=p*math.log(p/q)
    return d


def angle(u,v):
    du=math.sqrt(u[0]**2+u[1]**2+u[2]**2); dv=math.sqrt(v[0]**2+v[1]**2+v[2]**2)
    if du==0 or dv==0: return None
    c=(u[0]*v[0]+u[1]*v[1]+u[2]*v[2])/(du*dv)
    c=max(-1.0,min(1.0,c))
    return math.degrees(math.acos(c))


def analyze_balls(chain, letters, level, n_centers=2500):
    global CHAIN
    CHAIN=chain
    nlet=len(MENU)
    N=len(chain)
    centers=random.sample(range(N), min(n_centers, N))
    rhos=list(range(1,11))
    # per-rho aggregates
    ent_max=defaultdict(float); ent_sum=defaultdict(float); ent_cnt=defaultdict(int)
    narcs_max=defaultdict(int)
    # cross-entropy floor tracking over coexisting pairs
    min_angle=defaultdict(lambda:1e9)
    min_kl=defaultdict(lambda:1e9)
    # for a fixed reference rho, collect a distribution of pair angles/kls
    pair_angles_r6=[]; pair_kls_r6=[]
    parallel_pairs=defaultdict(int); total_pairs=defaultdict(int)
    Hs={r: build_hash(chain, r) for r in rhos}
    for ci,c in enumerate(centers):
        q=chain[c]
        for rho in rhos:
            idxs=within(Hs[rho], rho, q, rho)
            if len(idxs)<2: continue
            arcs=arcs_of(idxs)
            na=len(arcs)
            if na>narcs_max[rho]: narcs_max[rho]=na
            # arc-identity entropy (weighted by arc point count)
            tot=len(idxs)
            H=0.0
            for a in arcs:
                w=len(a)/tot
                if w>0: H-=w*math.log(w)
            ent_sum[rho]+=H; ent_cnt[rho]+=1
            if H>ent_max[rho]: ent_max[rho]=H
            if na>=2:
                dists=[arc_stepdist(a, letters, nlet) for a in arcs]
                for i in range(na):
                    for j in range(i+1,na):
                        hi,mi,ci_=dists[i]; hj,mj,cj_=dists[j]
                        ang=angle(mi,mj)
                        d=kl(hi,hj)
                        total_pairs[rho]+=1
                        if ang is not None:
                            if ang<min_angle[rho]: min_angle[rho]=ang
                            if ang<1.0: parallel_pairs[rho]+=1
                        if d<min_kl[rho]: min_kl[rho]=d
                        if rho==6 and len(pair_angles_r6)<200000:
                            if ang is not None: pair_angles_r6.append(ang)
                            pair_kls_r6.append(d)
    out={"level":level,"n_centers":len(centers)}
    out["narcs_max_by_rho"]={str(r):narcs_max[r] for r in rhos}
    out["arc_entropy_max_by_rho"]={str(r):round(ent_max[r],4) for r in rhos}
    out["arc_entropy_mean_by_rho"]={str(r):round(ent_sum[r]/ent_cnt[r],4) if ent_cnt[r] else None for r in rhos}
    out["min_pair_angle_deg_by_rho"]={str(r):(round(min_angle[r],4) if min_angle[r]<1e8 else None) for r in rhos}
    out["min_pair_KL_by_rho"]={str(r):(round(min_kl[r],6) if min_kl[r]<1e8 else None) for r in rhos}
    out["parallel_pair_frac_by_rho"]={str(r):(round(parallel_pairs[r]/total_pairs[r],4) if total_pairs[r] else None) for r in rhos}
    if pair_angles_r6:
        pa=sorted(pair_angles_r6)
        out["rho6_pair_angle_pctiles"]={p:round(pa[int(len(pa)*p/100)],3) for p in (0,1,5,25,50)}
    if pair_kls_r6:
        pk=sorted(pair_kls_r6)
        out["rho6_pair_KL_pctiles"]={p:round(pk[int(len(pk)*p/100)],5) for p in (0,1,5,25,50)}
    # slope of log(narcs_max) and arc_entropy_max vs log rho over rho=2..10
    def slope(ys):
        xs=[math.log(r) for r in rhos[1:]]; ys=[ys[r] for r in rhos[1:]]
        n=len(xs); sx=sum(xs); sy=sum(ys); sxx=sum(x*x for x in xs); sxy=sum(x*y for x,y in zip(xs,ys))
        return (n*sxy-sx*sy)/(n*sxx-sx*sx)
    out["loglog_slope_narcs"]=round(slope({r:math.log(narcs_max[r]) if narcs_max[r]>0 else 0 for r in rhos}),4)
    out["loglog_slope_arc_entropy_max"]=round(slope({r:ent_max[r] for r in rhos}),4)
    return out


def main():
    results={}
    for L in (6,7,8):
        chain,letters=load(L)
        sc=subword_complexity(letters, 40)
        # fit: is p(n) linear? report p(n) and first differences
        diffs={n:sc[n]-sc[n-1] for n in sorted(sc) if n>1}
        ball=analyze_balls(chain, letters, L)
        results[f"L{L}"]={
            "chain_len":len(chain),
            "n_letters":len(letters),
            "subword_complexity_p_n":sc,
            "p_n_first_differences":diffs,
            "distinct_letters":len(set(letters)),
            "ball_analysis":ball,
        }
        print(f"=== L{L} done: chain={len(chain)} p(1)={sc[1]} p(5)={sc.get(5)} narcs_max={ball['narcs_max_by_rho']}", flush=True)
    json.dump(results, open("/Users/erik/homelab/math193/design/entropy/measure-entropy-results.json","w"), indent=2)
    print("WROTE design/entropy/measure-entropy-results.json")


if __name__=="__main__":
    main()
