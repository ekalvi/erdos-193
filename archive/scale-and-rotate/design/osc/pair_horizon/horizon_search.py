"""
PAIR-LEVEL HORIZON -- PART 2: does deciding cross-collinearity need UNBOUNDED lookahead?

Exact-integer coupled cross-chord descent.  Two cross-chords
   d1 = q - p,  d2 = r - p        (p in C,  q,r in C')
evolve under one level of joint descent (into children) by
   d1' = M.d1 + e1,  d2' = M.d2 + e2,   e1 = o_q - o_p, e2 = o_r - o_p,
with (o_p,o_q,o_r) a COUPLED triple of interior offsets from the menu O (|O|=2103).
Then  Omega = d1 x d2,  and  Omega' = cof(M).Omega + birth  (verified in omega_form.py).

The automaton can decide NON-collinearity (Omega != 0) from bounded residues iff the
"excess parallelism"
   EXCESS(d1,d2) := v3(Omega) - v3(d1) - v3(d2) = v3(U1 x U2)   (U_i = primitive part)
is BOUNDED under legal descent.  EXCESS = # extra 3-adic digits through which the two
chords' primitive parts stay parallel = the lookahead depth needed to refute collinearity.
 * EXCESS bounded by H*  =>  a residue window of H* digits DECIDES it  => HOLDS (horizon H*).
 * EXCESS grows with descent depth (unboundedly)  =>  refuting Omega=0 needs arbitrarily
   deep lookahead  => FAILS.

ADVERSARIAL: beam search that MAXIMISES EXCESS (keeps the chords as parallel as possible),
seeded from the canonical meeting shell, descending many levels.  If even the adversary
cannot push EXCESS past a fixed cap regardless of depth -> bounded horizon.
"""
from __future__ import annotations
import json, ast, itertools

M = ((3,0,0),(0,0,-3),(0,3,-1))
def matvec(A,v): return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
                         A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
                         A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def Q(v): x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def v3(n):
    if n==0: return 10**9
    c=0
    while n%3==0: n//=3; c+=1
    return c
def v3vec(v):
    if v==(0,0,0): return 10**9
    return min(v3(v[0]),v3(v[1]),v3(v[2]))
def excess(d1,d2):
    Om=cross(d1,d2)
    if Om==(0,0,0): return 10**9   # exactly parallel
    return v3vec(Om)-v3vec(d1)-v3vec(d2)
def score(d1,d2):
    """beam-retention score: FINITE excess only. Exact-parallel (INF) states are the
    trivially-DECIDABLE case (Omega=0 detected at horizon) -> deprioritised (-1) so the
    adversary hunts the genuinely-hard NEAR-parallel (large finite excess) states."""
    e=excess(d1,d2)
    return -1 if e>=10**9 else e

# offset menu
c=json.load(open('/Users/erik/homelab/math193/collar_multiplicity4.json'))
O=[tuple(ast.literal_eval(k)) for k in c.keys()]
O=sorted(set(O)|{(0,0,0)})

# canonical meeting-shell delta representatives (a'-a lattice ball, small reps)
def small_shell(maxQ=40):
    reps=[]
    for x in range(-4,5):
        for y in range(-3,4):
            for z in range(-3,4):
                if (x,y,z)==(0,0,0): continue
                if Q((x,y,z))<=maxQ: reps.append((x,y,z))
    return reps

def beam_search(seeds, levels=24, beam=300, offset_sample=None, track_finite=True):
    """maximise EXCESS over coupled descent. state = (d1,d2) exact int.
    track_finite: also track the max FINITE excess (ignoring exact-parallel INF) and
    count how many INF (Omega=0 exactly) states appear -- INF = a genuine reachable
    cross-collinear pair in the (unconstrained) ambient descent."""
    Ouse = O if offset_sample is None else offset_sample
    best_by_depth=[]; best_finite_by_depth=[]; inf_by_depth=[]
    frontier=set(seeds)
    gmax=-1; garg=None; gdepth=0
    gfmax=-1; gfarg=None; gfdepth=0
    for depth in range(levels):
        cur_max=-1; cur_fmax=-1; ninf=0; carg=None; cfarg=None
        for (d1,d2) in frontier:
            e=excess(d1,d2)
            if e>=10**9:
                ninf+=1
            elif e>cur_fmax:
                cur_fmax=e; cfarg=(d1,d2)
            if e>cur_max:
                cur_max=e; carg=(d1,d2)
        best_by_depth.append('INF' if cur_max>=10**9 else cur_max)
        best_finite_by_depth.append(cur_fmax); inf_by_depth.append(ninf)
        if cur_max>gmax: gmax=cur_max; garg=carg; gdepth=depth
        if cur_fmax>gfmax: gfmax=cur_fmax; gfarg=cfarg; gfdepth=depth
        # keep top-beam by excess (finite-biased: prefer high finite, then INF)
        scored=sorted(((score(a,b),(a,b)) for (a,b) in frontier), key=lambda t:-t[0])
        keep=[s[1] for s in scored[:beam]]
        # expand with inline top-k pruning
        children={}   # (d1,d2)->excess, keep only top ~ (beam*6)
        cap=beam*8
        for (d1,d2) in keep:
            Md1=matvec(M,d1); Md2=matvec(M,d2)
            for op in Ouse:
                for oq in Ouse:
                    e1=sub(oq,op); nd1=add(Md1,e1)
                    if nd1==(0,0,0): continue
                    for orr in Ouse:
                        e2=sub(orr,op); nd2=add(Md2,e2)
                        if nd2==(0,0,0): continue
                        st=(nd1,nd2)
                        if st not in children:
                            children[st]=score(nd1,nd2)
            if len(children)>cap*4:
                items=sorted(children.items(), key=lambda t:-t[1])[:cap]
                children=dict(items)
        if not children: break
        items=sorted(children.items(), key=lambda t:-t[1])[:cap]
        frontier=set(k for k,_ in items)
    return {"gmax": ('INF' if gmax>=10**9 else gmax), "gdepth": gdepth,
            "garg": ([list(garg[0]),list(garg[1])] if garg else None),
            "gfmax_finite": gfmax, "gfdepth": gfdepth,
            "gfarg": ([list(gfarg[0]),list(gfarg[1])] if gfarg else None),
            "best_by_depth": best_by_depth, "best_finite_by_depth": best_finite_by_depth,
            "inf_count_by_depth": inf_by_depth}

if __name__=='__main__':
    import sys
    # keep offset set small for tractable coupled triple loop: use a reduced but
    # structurally-rich subset (all offsets with small cheb) -- this is an adversary
    # SUBSET; a real bound needs full O, but if EXCESS already blows up on the subset
    # that's a genuine unbounded witness (subset paths are legal descents).
    def cheb(v): return max(abs(v[0]),abs(v[1]),abs(v[2]))
    Osub=[o for o in O if cheb(o)<=1]   # 27 = full unit cube, all in menu
    print(f"|O|={len(O)}  |Osub(cheb<=1)|={len(Osub)}", flush=True)
    shell=small_shell(30)
    print(f"shell reps: {len(shell)}", flush=True)
    seeds=set()
    for delta in shell:
        for a in Osub:
            for b in Osub:
                d1=add(delta,a); d2=add(delta,b)
                if d1!=d2 and d1!=(0,0,0) and d2!=(0,0,0):
                    seeds.add((d1,d2))
    seeds=list(seeds)
    print(f"seeds: {len(seeds)}", flush=True)
    res=beam_search(seeds, levels=20, beam=300, offset_sample=Osub)
    print("MAX EXCESS (incl INF):", res["gmax"], "at depth", res["gdepth"], flush=True)
    print("MAX FINITE EXCESS:", res["gfmax_finite"], "at depth", res["gfdepth"], flush=True)
    print("best_by_depth:", res["best_by_depth"], flush=True)
    print("best_finite_by_depth:", res["best_finite_by_depth"], flush=True)
    print("inf_count_by_depth:", res["inf_count_by_depth"], flush=True)
    res["offset_subset_cheb_le1"]=len(Osub)
    res["interpretation"]=("EXCESS=v3(U1xU2)=lookahead digits of primitive-part parallelism. "
        "max FINITE excess bounded & flat across depth => bounded horizon (HOLDS). "
        "grows with depth => unbounded lookahead (FAILS). INF states = exact Omega=0 "
        "cross-collinear pairs reachable in UNCONSTRAINED ambient descent (the construction "
        "forbids these via joint legality; their reachability alone is not a FAILS).")
    json.dump(res, open('/Users/erik/homelab/math193/design/osc/pair_horizon/horizon_search_results.json','w'), indent=1)
    print("wrote horizon_search_results.json", flush=True)
