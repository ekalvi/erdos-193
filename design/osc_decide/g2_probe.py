import pickle, json, time, sys
from collections import defaultdict
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])
STARTS=[int(x) for x in sys.argv[1].split(',')] if len(sys.argv)>1 else [0,1,2,3,4]
t0=time.time()
fwd=pickle.load(open('design/osc_decide/fwd_automaton.pkl','rb'))
into=defaultdict(lambda: defaultdict(list))
for a,edges in fwd.items():
    for (dg,ns) in edges: into[a][ns].append(dg)
outof={s1:list(edges) for s1,edges in fwd.items()}
tot=0
for a in STARTS:
    seen={}; coll=[]; npaths=0
    for s1,d1list in into[a].items():
        outs=outof.get(s1)
        if not outs: continue
        md1=[(mv(d1),d1) for d1 in d1list]
        for (d2,s2) in outs:
            b0,b1,b2=d2
            for (m,d1) in md1:
                V=(m[0]+b0,m[1]+b1,m[2]+b2); k=(V,s2); npaths+=1
                p=seen.get(k)
                if p is None: seen[k]=(d1,d2)
                elif p!=(d1,d2): coll.append((V,s2,p,(d1,d2)))
    tot+=len(coll)
    print(f"[{time.time()-t0:.1f}s] start a={a} MENU={MENU[a]} npaths={npaths} typed_overlaps={len(coll)}",flush=True)
    for (V,s2,p,q) in coll[:5]:
        print(f"     V={V} end={s2} w1=({p[0]},{p[1]}) w2=({q[0]},{q[1]})",flush=True)
print(f"TOTAL typed overlaps over starts {STARTS}: {tot}",flush=True)
