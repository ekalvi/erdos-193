"""Route-1 returns+sojourn measurement at L8 (and re-confirm L6/L7).
Exact max return-count A(rho) and max sojourn L(rho) over ALL walk-centered balls,
rho=1..10. Also max_c direct. Confirms level-stability of A0."""
import sys, pickle, json
from collections import defaultdict
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

def grid_index(chain, cell):
    g=defaultdict(list)
    for i,p in enumerate(chain):
        g[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
    return g

def arcs_of(idxs):
    idxs.sort()
    arcs=[]; cur=[idxs[0]]
    for a in idxs[1:]:
        if a==cur[-1]+1: cur.append(a)
        else: arcs.append(cur); cur=[a]
    arcs.append(cur)
    return arcs

def analyze(level):
    chain=load_chain(level); N=len(chain)
    per={}
    for rho in range(1,11):
        cell=rho; grid=grid_index(chain,cell)
        maxc=0; maxA=0; maxL=0; worst_prod=0
        # record the center achieving max A, and its arc-length multiset
        bestA_arclens=None
        for qi,q in enumerate(chain):
            cx,cy,cz=q[0]//cell,q[1]//cell,q[2]//cell
            idxs=[]
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for j in grid.get((cx+dx,cy+dy,cz+dz),()):
                            if cheb(chain[j],q)<=rho: idxs.append(j)
            c=len(idxs)
            if c>maxc: maxc=c
            arcs=arcs_of(idxs); A=len(arcs); L=max(len(a) for a in arcs)
            if A>maxA: maxA=A; bestA_arclens=sorted((len(a) for a in arcs),reverse=True)
            if L>maxL: maxL=L
            if A*L>worst_prod: worst_prod=A*L
        per[rho]={"max_c":maxc,"max_A":maxA,"max_L":maxL,
                  "max_AL_percenter":worst_prod,"bestA_arclens":bestA_arclens}
    return {"level":level,"N":N,"per_rho":per}

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [8]
    out={}
    for lv in levels:
        print("L%d..."%lv,flush=True)
        out[lv]=analyze(lv)
        print(json.dumps(out[lv]["per_rho"]))
    json.dump(out, open("/Users/erik/homelab/math193/design/lemma/route1/L8_arcs.json","w"),indent=1)
    print("=== A0 (max return count) per level, per rho ===")
    for rho in range(1,11):
        row=[out[lv]["per_rho"][rho]["max_A"] for lv in levels]
        print("rho",rho,"A=",row)
