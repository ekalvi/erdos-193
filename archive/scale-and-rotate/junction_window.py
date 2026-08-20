"""
Junction-window COUPLED joint automaton BFS (Round 11 swing).
Coupling: for the first k joint steps (the connector digits at/near the shared
junction vertex q), impose the LOCAL finite-window non-collinearity:
   cross(e1_j, e2_j) != 0     (the two arcs' j-th connector steps non-parallel), AND
   cross(c1_{j+1}, c2_{j+1}) != 0  (partial carries non-parallel through step j).
After k steps: free product (no coupling). This is the STRONGEST honest
finite-window local rule (window k fixed, depth-g independent => NON-circular).
Decide: does any parallel terminal (c1 x c2 = 0, both nonzero) remain reachable?
"""
import json, ast, sys, time
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

def Q(v): x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def cross(u,v): return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
def Minv_frac(v): return (F(v[0],3),F(-v[1],9)+F(v[2],3),F(-v[1],3))
def Minv_int(v):
    r=Minv_frac(v); return (int(r[0]),int(r[1]),int(r[2]))
def reskey(v):
    r=Minv_frac(v); return tuple((x-(x.numerator//x.denominator)) for x in r)

def load_digits(kind):
    if kind=="collar":
        c=json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
        O=[tuple(ast.literal_eval(k)) for k in c.keys()]
        return [(0,0,0)]+O
    from itertools import product
    menu=[v for v in product((-2,-1,0,1,2),repeat=3) if v!=(0,0,0)]
    S=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in menu for b in menu)
    return sorted(S)

def build(kind):
    D=load_digits(kind)
    Eset=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in D for b in D)
    Ebyres=defaultdict(list)
    for e in Eset: Ebyres[reskey(e)].append(e)
    R={(0,0,0)}; dq=deque([(0,0,0)]); fwd=defaultdict(list)
    while dq:
        cc=dq.popleft(); rk=reskey((-cc[0],-cc[1],-cc[2]))
        for e in Ebyres.get(rk,()):
            s=(cc[0]+e[0],cc[1]+e[1],cc[2]+e[2]); cp=Minv_int(s)
            fwd[cc].append((cp,e))
            if cp not in R: R.add(cp); dq.append(cp)
    return R,fwd

def fclose(fwd,s):
    seen={s}; dq=deque([s])
    while dq:
        c=dq.popleft()
        for (cp,e) in fwd[c]:
            if cp not in seen: seen.add(cp); dq.append(cp)
    return seen

def main():
    kind=sys.argv[1] if len(sys.argv)>1 else "menu"
    k=int(sys.argv[2]) if len(sys.argv)>2 else 3
    t0=time.time()
    R,fwd=build(kind); Rn=R-{(0,0,0)}
    print(f"[{kind} k={k}] |R_nonzero|={len(Rn)}",flush=True)
    # windowed BFS: layer = set of (c1,c2) reachable at each gen with coupling on
    layer={((0,0,0),(0,0,0))}
    for step in range(k):
        nxt=set()
        for (c1,c2) in layer:
            for (c1p,e1) in fwd[c1]:
                if e1==(0,0,0): continue  # a nonzero connector step at the junction
                cr_e=cross(e1,(0,0,0))
                for (c2p,e2) in fwd[c2]:
                    if e2==(0,0,0): continue
                    if cross(e1,e2)==(0,0,0): continue          # steps parallel -> forbidden
                    if cross(c1p,c2p)==(0,0,0): continue        # partial carries parallel -> forbidden
                    nxt.add((c1p,c2p))
        layer=set(list(nxt)[:1200])
        print(f"  after coupled step {step+1}: |frontier(nonzero,non-parallel)|={len(layer)}",flush=True)
        if not layer: break
    # Phase B: free product from the window-k frontier. Single stream strongly connected
    # => forward-closure of any state = R. Confirm and enumerate reachable parallels.
    if not layer:
        print("  window prefix EMPTY -> coupling severed everything at this k (unexpected).",flush=True)
        return
    # pick a frontier state, compute forward closures
    reach1=set(); reach2=set()
    # union of forward closures over frontier coords (sound: these are reachable)
    for (a,b) in list(layer)[:50]:
        reach1|=fclose(fwd,a); reach2|=fclose(fwd,b)
        if reach1>=R and reach2>=R: break
    print(f"  Phase B forward closures: stream1 reaches {len(reach1)}/{len(R)}, stream2 reaches {len(reach2)}/{len(R)} of R",flush=True)
    # count parallel pairs (v,w) with v in reach1, w in reach2, cross=0, both nonzero
    # (this is the surviving parallel bad-set under the junction coupling)
    r1=[v for v in reach1 if v!=(0,0,0)]; r2set=set(w for w in reach2 if w!=(0,0,0))
    def primdir(v):
        g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2])); w=(v[0]//g,v[1]//g,v[2]//g)
        for a in w:
            if a<0: return (-w[0],-w[1],-w[2])
            if a>0: return w
        return w
    # count unordered parallel pairs both reachable (v in R, both in reach), matches badset
    bydir=defaultdict(list)
    for v in (reach1&reach2)-{(0,0,0)}: bydir[primdir(v)].append(v)
    survive=0; antip=0
    for pd,vs in bydir.items():
        n=len(vs); survive+=n*(n-1)//2
        for v in vs:
            if (-v[0],-v[1],-v[2]) in set(vs) and v<(-v[0],-v[1],-v[2]): antip+=1
    print(f"  SURVIVING parallel unordered pairs (both coords reachable post-window): {survive} (antipodal {antip})",flush=True)
    # explicit hard witnesses reachable?
    hard=[((5,0,0),(-5,0,0)),((1,1,1),(5,5,5)),((-2,-2,3),(-4,-4,6))] if kind=="collar" else \
         [((3,0,0),(-3,0,0)),((1,1,1),(3,3,3))]
    for a,b in hard:
        print(f"    witness {a}/{b}: reachable stream1={a in reach1}, stream2={b in reach2}, cross={cross(a,b)}",flush=True)
    print(f"[{time.time()-t0:.1f}s] done",flush=True)

if __name__=="__main__": main()
