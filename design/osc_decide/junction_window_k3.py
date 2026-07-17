"""
Erdos #193 -- Round 11 FINAL SWING: junction-window coupled automaton at k=3.

Setup (proven algebra, rank_pair_automaton.py / carry_automaton.py):
  M=M_BAL3, C=cof(M), (M^g u)x(M^g v)=C^g (u x v), det C=729 invertible.
  A walk address-difference from the shared junction base q normalizes to a carry
  c_g = M^-g Delta in the finite 8649-state Q-ball; collinear(p,q,r) <=> c1_g x c2_g = 0.
  Single-stream reachable carry set R = BFS-from-0 to fixpoint (all-generation, forward
  invariant, NOT depth truncated).

JUNCTION COUPLING (the untested crack). The two arcs p<-q->r share the physical
junction vertex q. The genuine LOCAL, FINITE, depth-g-INDEPENDENT surrogate for the
single-connector menu-adjacency at q: for the first k=3 JOINT connector steps out of q,
forbid the two arcs' steps from being parallel and their partial carries from being
parallel:
     e1_j x e2_j != 0   AND   c1_{j+1} x c2_{j+1} != 0   for j < k.
After the window: free product (independent streams).  This reads ONLY the first k digits
/ partial carries (fixed k, no reference to the terminal carry c_g or depth g) => NON-CIRCULAR.

DECIDER (rigorous, all-depth):
  (1) single SCC (verified separately) + (2) non-bipartite (parity-BFS here)
      => A is a PRIMITIVE digraph: exists N s.t. every ordered (s,t) has a walk of every
         length >= N.  Hence from any nonempty window-k frontier the free-product tail
         reaches EXACTLY R x R at matched generation.
  (3) window-k=3 frontier nonempty (coupled BFS here) => coupling removes ZERO parallels.
  (4) surviving parallel bad-set recomputed directly from R (per family).
  (5) named hard witnesses shown reachable from 0 at a COMMON generation parity
      (=> jointly reachable at matched depth), with cross=0.
"""
import json, ast, sys, time
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

def cross(u,v): return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
def Minv_frac(v): return (F(v[0],3), F(-v[1],9)+F(v[2],3), F(-v[1],3))
def Minv_int(v):
    r=Minv_frac(v); return (int(r[0]),int(r[1]),int(r[2]))
def reskey(v):
    r=Minv_frac(v); return tuple((x-(x.numerator//x.denominator)) for x in r)
def primdir(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    if g==0: return None
    w=(v[0]//g,v[1]//g,v[2]//g)
    for a in w:
        if a<0: return (-w[0],-w[1],-w[2])
        if a>0: return w
    return w

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

def parity_bfs(fwd, src=(0,0,0)):
    # reach[state] = bitmask over parity {1<<0 even-len, 1<<1 odd-len}
    reach=defaultdict(int); reach[src]=1  # length 0 = even
    dq=deque([(src,0)])
    while dq:
        c,p=dq.popleft(); np=1-p; bit=1<<np
        for (cp,e) in fwd[c]:
            if not (reach[cp]&bit):
                reach[cp]|=bit; dq.append((cp,np))
    return reach

def coupled_window(fwd, k, cap, max_nxt=8000):
    layer={((0,0,0),(0,0,0))}
    sizes=[]
    for step in range(k):
        nxt=set()
        done=False
        for (c1,c2) in layer:
            o1=fwd[c1]; o2=fwd[c2]
            for (c1p,e1) in o1:
                if e1==(0,0,0): continue
                for (c2p,e2) in o2:
                    if e2==(0,0,0): continue
                    if cross(e1,e2)==(0,0,0): continue
                    if cross(c1p,c2p)==(0,0,0): continue
                    nxt.add((c1p,c2p))
                    if len(nxt)>=max_nxt: done=True; break
                if done: break
            if done: break
        sizes.append(len(nxt) if not done else f">={max_nxt}")
        layer=set(list(nxt)[:cap]) if cap else nxt
        if not layer: break
    return layer,sizes

def badset_from_R(R):
    Rn=[v for v in R if v!=(0,0,0)]
    bydir=defaultdict(list)
    for v in Rn: bydir[primdir(v)].append(v)
    total=0; antip=0; proper=0; xaxis=0; xaxis_antip=0; xaxis_proper=0
    ratio_census=defaultdict(int); noninteger=0
    for pd,vs in bydir.items():
        n=len(vs); pairs=n*(n-1)//2; total+=pairs
        vs_set=set(vs)
        is_x = (pd==(1,0,0))
        # signed multiple along pd
        def mult(v):
            for i in range(3):
                if pd[i]!=0: return v[i]//pd[i]
        for i in range(len(vs)):
            for j in range(i+1,len(vs)):
                a=vs[i]; b=vs[j]
                if (-a[0],-a[1],-a[2])==b:
                    antip+=1
                    if is_x: xaxis_antip+=1
                else:
                    proper+=1
                    if is_x: xaxis_proper+=1
                    ka=abs(mult(a)); kb=abs(mult(b))
                    hi,lo=max(ka,kb),min(ka,kb)
                    if hi%lo==0: ratio_census[hi//lo]+=1
                    else: noninteger+=1
        if is_x: xaxis+=pairs
    return {"total":total,"antipodal":antip,"proper":proper,
            "xaxis_total":xaxis,"xaxis_antipodal":xaxis_antip,"xaxis_proper":xaxis_proper,
            "proper_integer_ratio_census":dict(ratio_census),
            "proper_noninteger":noninteger,"n_direction_lines":len(bydir)}

def main():
    kind=sys.argv[1] if len(sys.argv)>1 else "collar"
    k=int(sys.argv[2]) if len(sys.argv)>2 else 3
    cap=int(sys.argv[3]) if len(sys.argv)>3 else 2000
    t0=time.time()
    R,fwd=build(kind); Rn=R-{(0,0,0)}
    print(f"[{kind} k={k}] |R_nonzero|={len(Rn)}",flush=True)

    # (2) non-bipartite check
    reach=parity_bfs(fwd,(0,0,0))
    both=sum(1 for c in Rn if reach[c]==3)
    only_even=sum(1 for c in Rn if reach[c]==1)
    only_odd=sum(1 for c in Rn if reach[c]==2)
    nonbip = both>0
    print(f"parity-BFS from 0: reachable-at-both-parities={both}/{len(Rn)} "
          f"(only-even={only_even}, only-odd={only_odd}) => non-bipartite/primitive={nonbip}",flush=True)

    # (3) coupled window frontier at k
    layer,sizes=coupled_window(fwd,k,cap)
    print(f"coupled window k={k}: per-step frontier sizes (pre-cap {cap}) = {sizes}; "
          f"final layer nonempty={len(layer)>0} (|layer|={len(layer)})",flush=True)

    # (4) surviving parallels = full badset (R x R), recomputed from R
    bs=badset_from_R(R)
    print(f"surviving parallel unordered pairs (R x R, all-depth) = {bs['total']} "
          f"[antipodal {bs['antipodal']} + proper {bs['proper']}]",flush=True)
    print(f"  x-axis eigen family (primdir (1,0,0)): {bs['xaxis_total']} pairs "
          f"(antipodal {bs['xaxis_antipodal']} + proper {bs['xaxis_proper']})",flush=True)
    print(f"  proper integer-ratio census = {bs['proper_integer_ratio_census']}, "
          f"non-integer-ratio = {bs['proper_noninteger']}; direction lines = {bs['n_direction_lines']}",flush=True)

    # (5) named witnesses: both in R, cross=0, common generation parity => matched-depth reachable
    witsets = {"collar":[((5,0,0),(-5,0,0)),((1,1,1),(5,5,5)),((-2,-2,3),(-4,-4,6))],
               "menu":[((3,0,0),(-3,0,0)),((1,1,1),(3,3,3)),((-2,-2,3),(-2,-2,3) if False else (-1,-1,1))]}
    wl = witsets.get(kind, witsets["collar"])
    print("witnesses (matched-generation joint reachability):",flush=True)
    for a,b in wl:
        ina=a in R; inb=b in R
        pa=reach.get(a,0); pb=reach.get(b,0)
        common = pa & pb
        matched = ina and inb and common!=0
        print(f"  {a}/{b}: inR={ina}/{inb} cross={cross(a,b)} parities(a)={pa:02b} parities(b)={pb:02b} "
              f"common-parity={common:02b} => jointly reachable at matched depth = {matched}",flush=True)

    # concrete: recompute a proper (v, kv) and antipodal witness present
    print(f"[{time.time()-t0:.1f}s] done",flush=True)

if __name__=="__main__": main()
