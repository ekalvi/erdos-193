"""Probe: for a single fresh bridge (empty global set + the two endpoints),
what is the largest gap the double-helix bridge can close EXACTLY & triple-free?
This isolates the T2 stitching ceiling from multi-level interactions."""
from build_ch import *
from chiral_accel import *

def try_gap(g, menu, R1,R2,T1,T2):
    start=tuple(0 for _ in g); target=tuple(g)
    points=[start]; pset={start}
    ok,nadd=bridge_double_helix(start,target,menu,points,pset,R1,R2,T1,T2,
                                node_budget=400000)
    ft=first_triple(points)
    return ok, len(points), (ft is None)

menu=twist4
# gaps along generic direction (mix of both planes), increasing magnitude
import itertools
print("gap-magnitude | closed_exact | pts | triple_free  (best over params)")
for scale in [1,2,3,5,8,12,20,30,50]:
    g=(3*scale,1*scale,-2*scale,2*scale)   # generic 4D direction
    gl=flen(g)
    best=None
    for R in (4,6,10,int(0.1*gl)+2):
        for T in (2,3,4):
            ok,npts,tf=try_gap(g,menu,R,R,T,T)
            if ok and tf:
                if best is None or npts<best[1]:
                    best=(ok,npts,tf,R,T)
    if best:
        print(f"gl={gl:7.1f} g={g}  CLOSED  pts={best[1]:4d} tf={best[2]} (R={best[3]},T={best[4]})")
    else:
        # report best triple-free reach even if not closed
        maxreach=0; closed_any=False
        for R in (4,6,10,int(0.1*gl)+2):
            for T in (2,3,4):
                ok,npts,tf=try_gap(g,menu,R,R,T,T)
                if tf: maxreach=max(maxreach,npts)
                if ok: closed_any=True
        print(f"gl={gl:7.1f} g={g}  NOT-CLOSED (closed_any={closed_any}) max_tf_reach={maxreach}")
