"""PRONG C -- bigger-twist margin + easier OSC.

For M_m = ((m,0,0),(0,0,-m),(0,m,-1))  (eigenvalue moduli m, extent-ratio exactly m,
anchor separation min|M_m v|_inf = m, irrational twist arccos(-1/2m)), build the
seed-193 amplified walk to level `depth` for m in {4,5,6} (and m=3 reference), verify
triple-free, and measure:

  (A) COVERING MULTIPLICITY mult_g(r) = max_q #distinct gen-g cylinders meeting Cheb
      ball B(q,r).  This is the OSC / Mauldin-Williams multiplicity constant.  Reported
      at the matched cylinder scale r = m^g (analog of the m=3 r=3^g), at the median
      cylinder diameter, and at the full generation-g diameter.  Bounded + g-stable =>
      OSC signature.  m=3 reference value is 4/5/4 at r=3^g.

  (B) SIBLING RELATIVE GAP rho0 (local one-generation OSC): min Cheb gap between two
      distinct child sub-cylinders of a common parent, / child scale m^{g-1}.  >0 with
      slack => local finite OSC check is clean.

  (C) AVAILABILITY proxy: the direct Ahlfors ratio C_d(r) = max_q c(q,r)/r^d over
      r in [1,10] with d = log(lambda)/log(m), the binding radius, and the max ratio.
      The m=3 construction runs at ~0 margin (c(4.44)=12 == theory bound 2*4.44^d).
      Bigger m lowers d (purer thread) and enlarges the connector word space
      (seg_maxlen = 2m+6): does the max ratio / danger-radius crowding drop?

Self-contained parent/ancestry tracking: reuses the VERIFIED amplify_level to make each
level's word, then reconstructs the gen-1 parent map by matching the M-anchor chain
(mw_osc.py convention: stitch interiors -> source parent, anchor -> its own parent).
"""
import sys, math, json, time
from random import Random
from collections import defaultdict

from search193 import candidate_step_vectors
from amplify193 import amplify_level, find_base
from erdos193 import first_disqualifier
from imbricate193 import apply
from imbricate_seam import walk_points

MENU = candidate_step_vectors(2)

def Mm(m): return ((m,0,0),(0,0,-m),(0,m,-1))

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def extent(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; zs=[p[2] for p in pts]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

def anchors_of(word, M):
    return [apply(M, p) for p in walk_points(word, MENU)]

def parent_map(word, new_word, M):
    """Reconstruct parent[j] for the new level from the anchor chain match."""
    anchors = anchors_of(word, M)
    chain = walk_points(new_word, MENU, start=anchors[0])
    parent = [0]
    ai = 0
    aset = anchors
    for j in range(1, len(chain)):
        if ai+1 < len(aset) and chain[j] == aset[ai+1]:
            ai += 1
            parent.append(ai)          # reached anchor ai -> parent ai
        else:
            parent.append(ai)          # interior of segment ai -> source parent ai
    assert ai == len(anchors)-1, f"anchor match incomplete {ai}/{len(anchors)-1}"
    return chain, parent

def compose_ancestry(parents, depth):
    """parents[L] : level-L index -> level-(L-1) index, for L=1..top.
    Returns anc[g] on the TOP chain: top index -> index in level (top-g)."""
    top = len(parents)          # top level number
    n = None
    # anc built on top chain indices
    anc = [None]*(depth+1)
    idx = list(range(len(parents[top])+1)) if False else None
    # Build directly: start identity on top chain length
    Ntop = len(parents[top])    # parents[top] length == number of points at top level
    anc[0] = list(range(Ntop))
    acc = parents[top][:]       # g=1: top index -> level top-1 index
    anc[1] = acc[:]
    for g in range(2, depth+1):
        L = top-g+1
        pmap = parents[L]       # level-L index -> level-(L-1) index
        acc = [pmap[acc[j]] for j in range(Ntop)]
        anc[g] = acc[:]
    return anc

def cylinders(anc_g):
    groups=defaultdict(list)
    for j,a in enumerate(anc_g): groups[a].append(j)
    return groups

def cyl_diam(chain, idxs):
    xs=[chain[j][0] for j in idxs]; ys=[chain[j][1] for j in idxs]; zs=[chain[j][2] for j in idxs]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

def covering_multiplicity(chain, anc_g, r):
    cell=max(r,1); grid=defaultdict(list)
    for j,p in enumerate(chain): grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(j)
    best=0
    for q in chain:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        ids=set()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(chain[j],q)<=r: ids.add(anc_g[j])
        if len(ids)>best: best=len(ids)
    return best

def sibling_gap(chain, anc_child, anc_parent):
    byparent=defaultdict(lambda: defaultdict(list))
    for j in range(len(chain)):
        byparent[anc_parent[j]][anc_child[j]].append(j)
    gmin=10**9
    for pid,children in byparent.items():
        cs=list(children.items())
        if len(cs)<2: continue
        for a in range(len(cs)):
            for b in range(a+1,len(cs)):
                pa=cs[a][1]; pb=cs[b][1]
                mm=min(cheb(chain[i],chain[k]) for i in pa for k in pb)
                if mm<gmin: gmin=mm
    return gmin

def crowd_curve(chain, radii):
    out={}
    for r in radii:
        cell=max(r,1); g2=defaultdict(list)
        for p in chain: g2[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
        best=0
        for q in chain:
            gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell; c=0
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for p in g2.get((gx+dx,gy+dy,gz+dz),()):
                            if cheb(p,q)<=r: c+=1
            if c>best: best=c
        out[r]=best
    return out

def run_m(m, depth, seed=193, base_len=20):
    rng=Random(seed)
    M=Mm(m)
    base=find_base(MENU,rng,length=base_len,tries=200)
    words=[base]                      # words[L] is the word for level L
    parents={}                        # parents[L]: level-L idx -> level-(L-1) idx
    lens=[len(walk_points(base,MENU))]
    t0=time.time()
    jam=None
    top_chain=None
    for L in range(1, depth+1):
        new=amplify_level(words[L-1], MENU, M, rng,
                          seg_maxlen=2*m+6, seg_tries=8, restarts=6, route="short")
        if new is None:
            jam=L; break
        chain, par = parent_map(words[L-1], new, M)
        assert first_disqualifier(chain) is None, f"TRIPLE at m={m} L={L}"
        words.append(new)
        parents[L]=par
        lens.append(len(chain))
        top_chain=chain
        print(f"  m={m} L={L}: {len(chain)} pts, triple-free OK ({time.time()-t0:.1f}s)", flush=True)
    if jam:
        return {"m":m,"jam":jam}
    chain=top_chain
    N=len(chain)
    anc=compose_ancestry(parents, depth)

    lam=(lens[-1]/lens[0])**(1.0/(len(lens)-1))
    ext=extent(chain)
    d=math.log(lam)/math.log(m)

    # (A) covering multiplicity per generation
    A=[]
    for g in range(1, depth+1):
        groups=cylinders(anc[g])
        diams=sorted(cyl_diam(chain,idx) for idx in groups.values())
        med=diams[len(diams)//2]; mx=diams[-1]
        rmatch=m**g
        rows={}
        for r in sorted(set([rmatch, med, mx])):
            rows[r]=covering_multiplicity(chain, anc[g], r)
        A.append({"g":g,"ncyl":len(groups),"avg_size":round(N/len(groups),2),
                  "diam_med":med,"diam_max":mx,"r_match":rmatch,
                  "mult_at_rmatch":rows.get(rmatch),
                  "mult_at_med":rows.get(med),"mult_at_maxdiam":rows.get(mx),
                  "mult_rows":{str(k):v for k,v in rows.items()}})

    # (B) sibling relative gap
    B=[]
    for g in range(1, depth):
        gmin=sibling_gap(chain, anc[g], anc[g+1])
        scale=m**(g-1)
        B.append({"g":g,"scale":scale,"min_gap":gmin,"rho0":round(gmin/scale,4)})

    # (C) availability: direct Ahlfors ratio + crowd curve
    radii=[1,2,3,4,5,6,7,8,9,10]
    crowd=crowd_curve(chain, radii)
    C_rows=[]
    C_theory=2.0                      # Q-metric Mauldin-Williams constant c(R)<=2 R^d
    worst=None
    for r in radii:
        rd=r**d; ratio=crowd[r]/rd
        thr=C_theory*rd
        margin=thr-crowd[r]           # >0 => under the MW theory bound
        row={"r":r,"c_max":crowd[r],"rd":round(rd,3),"C_d":round(ratio,3),
             "theory_bound_2rd":round(thr,2),"margin":round(margin,2)}
        C_rows.append(row)
        if worst is None or ratio>worst["C_d"]:
            worst=row
    min_margin=min(row["margin"] for row in C_rows)
    # danger radius analog of m=3's r=4.44 ~ 1.48*m (clamped to <=10)
    r_star=min(10, round(1.48*m))
    c_star=crowd[r_star]; thr_star=C_theory*(r_star**d)

    return {"m":m,"depth":depth,"N":N,"lens":lens,"lambda":round(lam,3),
            "extent":ext,
            "d":round(d,4),"seg_maxlen":2*m+6,"menu_size":len(MENU),
            "covering_multiplicity":A,
            "mult_at_match_scale":[a["mult_at_rmatch"] for a in A],
            "mult_at_maxdiam":[a["mult_at_maxdiam"] for a in A],
            "sibling_gap":B,
            "min_rho0":min((b["rho0"] for b in B), default=None),
            "availability":{"crowd_curve":crowd,"ahlfors_rows":C_rows,
                            "max_C_d":worst,"min_margin_vs_2rd":round(min_margin,2),
                            "r_star_analog":r_star,"c_at_r_star":c_star,
                            "theory_bound_at_r_star":round(thr_star,2),
                            "margin_at_r_star":round(thr_star-c_star,2)}}

if __name__=="__main__":
    ms=[int(x) for x in sys.argv[1].split(",")] if len(sys.argv)>1 else [3,4,5,6]
    depth=int(sys.argv[2]) if len(sys.argv)>2 else 4
    results={}
    for m in ms:
        print(f"=== m={m} depth={depth} ===", flush=True)
        results[m]=run_m(m, depth)
        print(json.dumps(results[m]), flush=True)
    out=f"/Users/erik/homelab/math193/design/lemma/osc/prongC-osc-results.json"
    json.dump({"depth":depth,"menu_size":len(MENU),"results":results}, open(out,"w"), indent=1)
    print("WROTE", out, flush=True)
