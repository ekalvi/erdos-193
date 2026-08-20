"""
DECIDER (A), g=2, GDS-CORRECT (same start type, same anchor, same end type).
A legal 2-word: a --(d1)--> s1 --(d2)--> s2.  Cylinder = f_{d1}f_{d2}(K_{s2}) subset K_a.
GENUINE EXACT OVERLAP (identical cylinder, OSC FAILS) iff two distinct (d1,d2)
share  start a, anchor V=M.d1+d2, end type s2.
"""
import pickle, json, time
from collections import defaultdict
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])

t0=time.time()
fwd=pickle.load(open('design/osc_decide/fwd_automaton.pkl','rb'))
# into[a][s1] = list of d1 (edges a->(d1,s1)); outof[s1] = list of (d2,s2)
into=defaultdict(lambda: defaultdict(list))
for a,edges in fwd.items():
    for (dg,ns) in edges:
        into[a][ns].append(dg)
outof={s1:list(edges) for s1,edges in fwd.items()}
print(f"[{time.time()-t0:.1f}s] indexed",flush=True)

typed_coll=[]
npaths=0
for a in fwd:
    seen={}   # (V,s2) -> (d1,d2)  first witness
    inta=into[a]
    for s1, d1list in inta.items():
        outs=outof.get(s1)
        if not outs: continue
        md1=[(mv(d1),d1) for d1 in d1list]
        for (d2,s2) in outs:
            d2x,d2y,d2z=d2
            for (m,d1) in md1:
                V=(m[0]+d2x, m[1]+d2y, m[2]+d2z)
                k=(V,s2)
                npaths+=1
                prev=seen.get(k)
                if prev is None:
                    seen[k]=(d1,d2)
                elif prev!=(d1,d2):
                    typed_coll.append((a,V,s2,prev,(d1,d2)))
    if a%20==0:
        print(f"[{time.time()-t0:.1f}s] start a={a} done; npaths={npaths} coll={len(typed_coll)}",flush=True)

print(f"[{time.time()-t0:.1f}s] DONE npaths={npaths}",flush=True)
print(f"GDS-CORRECT g=2 exact overlaps (same start,anchor,end): {len(typed_coll)}",flush=True)
out={"npaths":npaths,"gds_exact_overlaps_g2":len(typed_coll)}
if typed_coll:
    typed_coll.sort(key=lambda c:(c[1][0]**2+c[1][1]**2+c[1][2]**2))
    out["sample"]=[{"start_a":a,"V":list(V),"end_s2":s2,
                    "pair1":[list(p[0]),list(p[1])],"pair2":[list(q[0]),list(q[1])]}
                   for (a,V,s2,p,q) in typed_coll[:20]]
    for s in out["sample"][:12]:
        print(f"  start={s['start_a']} V={s['V']} end={s['end_s2']} w1={s['pair1']} w2={s['pair2']}",flush=True)
else:
    print("NO GDS-correct exact overlap at g=2 -> type constraint KILLS the anchor-flood.",flush=True)
out["runtime_s"]=round(time.time()-t0,1)
json.dump(out, open('design/osc_decide/g2_typed_results.json','w'), indent=1)
print(f"[{time.time()-t0:.1f}s] wrote",flush=True)
