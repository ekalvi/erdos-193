"""
DECIDER (A), g=2 exact anchor-coincidence search on the menu-closure GDS.

A legal length-2 address is  root -> (digit d1, intermediate type s1) -> (digit d2)
with  d1 in RevAvail(s1)  (some forward edge (d1,s1) exists) and
      d2 in FwdAvail(s1)  (a forward edge (d2, *) exists from s1).
Anchor value  V = M.d1 + d2.
An EXACT overlap = two DISTINCT digit-pairs (d1,d2) != (d1',d2') with V = V'.
Such a pair => f_u = f_v (identical contraction) => id in Bandt-Graf neighbor set
=> OSC FAILS on the menu-closure GDS.

Sharded by residue(d2) mod M.Z^3 (collision needs same residue(V)=residue(d2)).
"""
import pickle, json, time
from collections import defaultdict
from fractions import Fraction as F

M=[[3,0,0],[0,0,-3],[0,3,-1]]
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])   # M.v
def Minv_frac(v): return (F(v[0],3), F(-v[1],9)+F(v[2],3), F(-v[1],3))
def residue(v):
    r=Minv_frac(v); return tuple((x-(x.numerator//x.denominator)) for x in r)

t0=time.time()
fwd=pickle.load(open('design/osc_decide/fwd_automaton.pkl','rb'))
# FwdAvail(s1) = digits d2 with a forward edge from s1
FwdAvail={s:sorted({dg for (dg,ns) in edges}) for s,edges in fwd.items()}
# RevAvail(s1) = digits d1 with a forward edge (d1,s1) from some state
RevAvail=defaultdict(set)
for s,edges in fwd.items():
    for (dg,ns) in edges:
        RevAvail[ns].add(dg)
RevAvail={s:sorted(v) for s,v in RevAvail.items()}
print(f"[{time.time()-t0:.1f}s] built avail; states={len(fwd)}",flush=True)

# enumerate legal (d1,d2) pairs, group value V by residue(d2)
# collision map: within a residue shard, V -> set of distinct (d1,d2) pairs
shards=defaultdict(lambda: defaultdict(set))
npairs=0
for s1 in fwd:
    rev=RevAvail.get(s1,[])
    out=FwdAvail.get(s1,[])
    if not rev or not out: continue
    Md1=[(mv(d1),d1) for d1 in rev]
    for d2 in out:
        r=residue(d2)
        sh=shards[r]
        for (md1,d1) in Md1:
            V=(md1[0]+d2[0], md1[1]+d2[1], md1[2]+d2[2])
            sh[V].add((d1,d2))
            npairs+=1
    # keep memory bounded: flush not needed if shard fits
print(f"[{time.time()-t0:.1f}s] enumerated {npairs} legal (d1,d2) pairs over {len(shards)} residue shards",flush=True)

# find collisions
collisions=[]
for r,sh in shards.items():
    for V,pairs in sh.items():
        if len(pairs)>=2:
            collisions.append((V, sorted(pairs)))
print(f"[{time.time()-t0:.1f}s] COLLISIONS (distinct-pair, same anchor V): {len(collisions)}",flush=True)

out={"npairs":npairs,"num_residue_shards":len(shards),"num_collisions":len(collisions)}
if collisions:
    # show a few, smallest V
    collisions.sort(key=lambda c:(c[0][0]**2+c[0][1]**2+c[0][2]**2))
    sample=[]
    for V,pairs in collisions[:20]:
        sample.append({"V":list(V),"pairs":[[list(a),list(b)] for (a,b) in pairs]})
    out["sample_collisions"]=sample
    print("SAMPLE COLLISIONS:",flush=True)
    for s in sample[:10]:
        print("  V=",s["V"]," pairs=",s["pairs"],flush=True)
else:
    print("NO g=2 exact overlap in menu-closure GDS.",flush=True)
out["runtime_s"]=round(time.time()-t0,1)
json.dump(out, open('design/osc_decide/g2_collision_results.json','w'), indent=1)
print(f"[{time.time()-t0:.1f}s] wrote g2_collision_results.json",flush=True)
