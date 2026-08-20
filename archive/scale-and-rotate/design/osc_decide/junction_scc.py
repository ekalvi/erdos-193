"""
Junction-window coupling decider for Erdos #193, Round 11.
Single-stream carry automaton R, then SCC / forward-reachability, which decides
whether ANY finite junction window can sever parallels.
"""
import json, ast, sys, math, time
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

M=[[3,0,0],[0,0,-3],[0,3,-1]]
def Q(v): x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def cross(u,v): return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
def Minv_frac(v): return (F(v[0],3),F(-v[1],9)+F(v[2],3),F(-v[1],3))
def in_MZ(v):
    r=Minv_frac(v); return r[0].denominator==1 and r[1].denominator==1 and r[2].denominator==1
def Minv_int(v):
    r=Minv_frac(v); return (int(r[0]),int(r[1]),int(r[2]))
def reskey(v):
    r=Minv_frac(v); return tuple((x-(x.numerator//x.denominator)) for x in r)

def load_digits(kind):
    if kind=="collar":
        c=json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
        O=[tuple(ast.literal_eval(k)) for k in c.keys()]
        return [(0,0,0)]+O
    else:
        from itertools import product
        menu=[v for v in product((-2,-1,0,1,2),repeat=3) if v!=(0,0,0)]
        S=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in menu for b in menu)
        return sorted(S)

def build(kind):
    D=load_digits(kind)
    Eset=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in D for b in D)
    E=sorted(Eset)
    Ebyres=defaultdict(list)
    for e in E: Ebyres[reskey(e)].append(e)
    # forward edges from each carry: c ->(e) c'=Minv(c+e), legal iff residue matches
    R={(0,0,0)}; dq=deque([(0,0,0)]); fwd=defaultdict(list)
    while dq:
        cc=dq.popleft(); rk=reskey((-cc[0],-cc[1],-cc[2]))
        for e in Ebyres.get(rk,()):
            s=(cc[0]+e[0],cc[1]+e[1],cc[2]+e[2]); cp=Minv_int(s)
            fwd[cc].append((cp,e))
            if cp not in R: R.add(cp); dq.append(cp)
    return D,E,R,fwd

def tarjan_scc(nodes, succ):
    index={}; low={}; onst={}; st=[]; idx=[0]; sccs=[]
    import sys as _s; _s.setrecursionlimit(1000000)
    def strong(v):
        # iterative Tarjan
        work=[(v,0)]
        while work:
            node,pi=work[-1]
            if pi==0:
                index[node]=low[node]=idx[0]; idx[0]+=1; st.append(node); onst[node]=True
            recurse=False
            children=succ[node]
            i=pi
            while i<len(children):
                w=children[i][0]
                if w not in index:
                    work.append((w,0)); work[-2]=(node,i+1); recurse=True; break
                elif onst.get(w):
                    low[node]=min(low[node],index[w])
                i+=1
            if recurse: continue
            if low[node]==index[node]:
                comp=[]
                while True:
                    w=st.pop(); onst[w]=False; comp.append(w)
                    if w==node: break
                sccs.append(comp)
            work.pop()
            if work:
                parent,_=work[-1]
                low[parent]=min(low[parent],low[node])
    for v in nodes:
        if v not in index: strong(v)
    return sccs

def main():
    kind=sys.argv[1] if len(sys.argv)>1 else "menu"
    t0=time.time()
    D,E,R,fwd=build(kind)
    Rn=R-{(0,0,0)}
    print(f"[{kind}] |D|={len(D)} |E|={len(E)} |R|={len(R)} |R_nonzero|={len(Rn)}",flush=True)
    # SCC of the FULL automaton (including 0)
    nodes=list(R)
    sccs=tarjan_scc(nodes, fwd)
    sizes=sorted((len(c) for c in sccs),reverse=True)
    print(f"#SCCs={len(sccs)} top sizes={sizes[:6]}",flush=True)
    # which SCC contains 0? is there one giant SCC = all nonzero?
    big=max(sccs,key=len); bigset=set(big)
    print(f"largest SCC size={len(big)}; contains 0: {(0,0,0) in bigset}; covers all nonzero: {Rn<=bigset or Rn==bigset-{(0,0,0)}}",flush=True)
    # forward reachable set from an arbitrary nonzero state
    def fclose(s):
        seen={s}; dq=deque([s])
        while dq:
            c=dq.popleft()
            for (cp,e) in fwd[c]:
                if cp not in seen: seen.add(cp); dq.append(cp)
        return seen
    import random
    sample=random.sample(list(Rn), min(20,len(Rn)))
    allR=set(R)
    full=0
    for s in sample:
        fc=fclose(s)
        if fc>=allR: full+=1
    print(f"forward-closure test: {full}/{len(sample)} sampled nonzero states reach ALL of R (incl 0)",flush=True)
    # antipodal reachability: from a nonzero v, can we reach -v?
    antip_ok=0
    for s in sample:
        nv=(-s[0],-s[1],-s[2])
        fc=fclose(s)
        if nv in fc: antip_ok+=1
    print(f"antipodal test: {antip_ok}/{len(sample)} nonzero v can forward-reach -v",flush=True)
    print(f"[{time.time()-t0:.1f}s] done",flush=True)

if __name__=="__main__": main()
