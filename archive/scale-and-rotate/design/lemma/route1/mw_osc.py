"""ROUTE 1 (Mauldin-Williams) OSC / covering-multiplicity test.

Frames the walk as a graph-directed self-similar system (ratio 1/3 in the Q-metric,
bounded distortion kappa=1.323 already proven).  A generation-g CYLINDER = the set of
level-k walk points descended from one common ancestor in W_{k-g}.  Cylinders are
contiguous walk-arcs, diameter ~3^g.

We measure the two quantities that decide whether the Mauldin-Williams theorem closes
Ahlfors d-regularity c_k(q,r) <= C r^d:

 (A) COVERING MULTIPLICITY  mult_g(r) = max_q #{distinct gen-g cylinders meeting Cheb-ball
     B(q,r)}.  This is the empirical OSC/Ahlfors multiplicity constant that MW's volume
     argument bounds.  Reported for r = median cyl diameter and r = 3^g.

 (B) SIBLING RELATIVE GAP  rho0 = min over parents of (min Cheb gap between two distinct
     child sub-cylinders) / (child scale 3^{g-1}).  This is the LOCAL, finite-alphabet
     one-generation OSC quantity: if bounded below >0 uniformly, the local OSC finite
     check passes and MW's bootstrap (sibling disjoint => all-generation disjoint =>
     bounded multiplicity) applies.

 (C) direct Ahlfors ratio  max_q c_k(q,r)/r^d, d = log(lambda)/log 3.
"""
import pickle, sys, math
from collections import defaultdict
from gate_run import word_interiors

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def build_level(L):
    """Return (chain, parent) where parent[j] = index in W_{L-1} of chain point j."""
    d = pickle.load(open(f'/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl','rb'))
    A=d['anchors']; W=d['words']
    chain=[A[0]]; parent=[0]
    for i in range(len(W)):
        for p in word_interiors(A[i],W[i]):
            chain.append(p); parent.append(i)      # stitch interiors -> source parent i
        chain.append(A[i+1]); parent.append(i+1)   # anchor A[i+1] = M*W_{L-1}[i+1]
    return chain, parent

def build_ancestry(topL, depth):
    """chains[topL] plus parent maps composing down 'depth' levels.
    Returns chain7 and a list anc[g] : position-in-chain(topL) -> ancestor index in W_{topL-g}."""
    chains={}; parents={}
    for L in range(topL-depth+1, topL+1):
        chains[L], parents[L] = build_level(L)
    chain = chains[topL]
    anc = [list(range(len(chain)))]      # g=0 : itself
    cur = list(range(len(chain)))
    # anc[g][j] = ancestor index of chain point j in W_{topL-g}
    prevmap = list(range(len(chain)))
    # g=1: parent in W_{topL-1}
    acc = parents[topL][:]                # position j -> parent index in W_{topL-1}
    anc.append(acc[:])
    for g in range(2, depth+1):
        L = topL-g+1                      # we need parents of W_{topL-g+1} to go one more up
        pmap = parents[L]                 # index in W_{topL-g+1} -> index in W_{topL-g}
        acc = [pmap[acc[j]] for j in range(len(chain))]
        anc.append(acc[:])
    return chain, anc

def cylinders(chain, anc_g):
    """group chain-point indices by ancestor id -> dict id->list of point indices."""
    groups=defaultdict(list)
    for j,a in enumerate(anc_g):
        groups[a].append(j)
    return groups

def cyl_diam(chain, idxs):
    xs=[chain[j][0] for j in idxs]; ys=[chain[j][1] for j in idxs]; zs=[chain[j][2] for j in idxs]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

def covering_multiplicity(chain, anc_g, r):
    """max over walk points q of #distinct gen-g cylinder ids within Cheb-r of q."""
    cell=max(r,1)
    grid=defaultdict(list)
    for j,p in enumerate(chain):
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(j)
    best=0
    for q in chain:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        ids=set()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(chain[j],q)<=r:
                            ids.add(anc_g[j])
        if len(ids)>best: best=len(ids)
    return best

def sibling_gap(chain, anc_child, anc_parent):
    """For each parent (anc_parent id), among its child sub-cylinders (grouped by anc_child),
    min Cheb gap between two DISTINCT child cylinders (point-set distance).  Returns global min."""
    # group points by parent, then by child within
    byparent=defaultdict(lambda: defaultdict(list))
    for j in range(len(chain)):
        byparent[anc_parent[j]][anc_child[j]].append(j)
    gmin=10**9; worst=None
    for pid,children in byparent.items():
        cs=list(children.items())
        if len(cs)<2: continue
        # brute pairwise point-set Cheb gap (children are small)
        for a in range(len(cs)):
            for b in range(a+1,len(cs)):
                pa=cs[a][1]; pb=cs[b][1]
                m=min(cheb(chain[i],chain[k]) for i in pa for k in pb)
                if m<gmin: gmin=m; worst=(pid,cs[a][0],cs[b][0])
    return gmin, worst

if __name__=='__main__':
    topL=int(sys.argv[1]); depth=int(sys.argv[2]) if len(sys.argv)>2 else 3
    chain, anc = build_ancestry(topL, depth)
    N=len(chain)
    print(f'=== L{topL}: {N} walk points, ancestry depth {depth} ===')
    n_parents = len(cylinders(chain, anc[1]))   # = |W_{topL-1}|
    lam = N / n_parents
    d = math.log(lam)/math.log(3)
    print(f'per-level growth lambda = N/|W_(k-1)| = {N}/{n_parents} = {lam:.4f}  => d=log(lam)/log3 = {d:.4f}')

    # (A) covering multiplicity per generation
    print('\n(A) COVERING MULTIPLICITY  mult_g(r) = max_q #distinct gen-g cylinders in Cheb-r')
    for g in range(1, depth+1):
        groups=cylinders(chain, anc[g])
        diams=[cyl_diam(chain,idxs) for idxs in groups.values()]
        diams.sort()
        med=diams[len(diams)//2]; mx=diams[-1]
        ncyl=len(groups); avgsz=N/ncyl
        print(f'  gen {g}: #cyl={ncyl} avg_size={avgsz:.2f} pts  diam median={med} max={mx}  (3^g={3**g})')
        for r in sorted(set([med, 3**g, mx])):
            m=covering_multiplicity(chain, anc[g], r)
            print(f'        r={r:4d}: mult={m}')

    # (B) sibling relative gap (local one-generation OSC)
    print('\n(B) SIBLING GAP  min Cheb gap between distinct child sub-cylinders of a common parent')
    for g in range(1, depth):
        gmin,worst = sibling_gap(chain, anc[g], anc[g+1])
        scale=3**(g-1)
        print(f'  children at gen {g} (scale 3^{g-1}={scale}) under gen-{g+1} parents: '
              f'min_gap={gmin}  rel_gap rho0={gmin/scale:.4f}  worst_parent={worst}')

    # (C) direct Ahlfors ratio
    print('\n(C) DIRECT AHLFORS  max_q c_k(q,r)/r^d')
    cell=1
    grid=defaultdict(list)
    for p in chain: grid[p].append(1)
    # reuse a coarse grid per r
    for r in [1,2,3,4,5,8,10]:
        cellr=max(r,1)
        g2=defaultdict(list)
        for p in chain: g2[(p[0]//cellr,p[1]//cellr,p[2]//cellr)].append(p)
        best=0
        for q in chain:
            gx,gy,gz=q[0]//cellr,q[1]//cellr,q[2]//cellr
            c=0
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for p in g2.get((gx+dx,gy+dy,gz+dz),()):
                            if cheb(p,q)<=r: c+=1
            if c>best: best=c
        rd = r**d
        print(f'  r={r:3d}: max c_k={best:4d}  r^d={rd:6.2f}  C_d=c/r^d={best/rd:.3f}')
