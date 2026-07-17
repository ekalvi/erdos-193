"""
C-H candidate (formal.candidates[3]): higher-n accelerating double-rotation
matrix M4(a,b,c) + chiral n=4 menu twist4.  Full T2 crux build in n=4.

Double-helix bridge: M4 has two invariant rotation planes P1=span(e0,e1),
P2=span(e2,e3).  A bridge from start->target circulates in BOTH planes while
drifting to the target, with a spindle taper sin(pi t) so radius->0 at both
endpoints (exact landing possible).  Greedy helix-follow + iterative-deepening
DFS endgame, keeping the WHOLE accumulated point set triple-free (legal()).
"""
from chiral_accel import *
from math import hypot, pi, cos, sin
import sys

twist4 = [(2,1,0,0),(-1,2,0,0),(0,0,2,1),(0,0,-1,2),(1,0,0,1),(0,1,1,0)]

def matvec_int(M,v):
    return tuple(sum(M[i][j]*v[j] for j in range(len(v))) for i in range(len(M)))

def flen(v): return hypot(*[float(x) for x in v])

def bridge_double_helix(start, target, menu, points, pset, R1, R2, T1, T2,
                        node_budget=200000, endgame_caps=(6,9,12,16,22,30)):
    """Greedy double-helix follow start->target, then DFS to land EXACTLY.
    Mutates points/pset on success. Returns (ok, n_added)."""
    g = vsub(target, start)
    if all(x==0 for x in g): return True, 0
    n = len(g)
    def ideal(t):
        sp = sin(pi*t)              # spindle taper -> 0 at t=0,1
        a1 = 2*pi*T1*t; a2 = 2*pi*T2*t
        base = [start[i]+t*g[i] for i in range(n)]
        base[0]+=R1*sp*cos(a1); base[1]+=R1*sp*sin(a1)
        base[2]+=R2*sp*cos(a2); base[3]+=R2*sp*sin(a2)
        return base
    cur = start
    added = []
    avg = sum(flen(s) for s in menu)/len(menu)
    glen = flen(g)
    L = max(8, int((glen + 2*pi*(T1*R1+T2*R2))/avg))
    for step in range(4*L):
        if all(x==0 for x in vsub(target,cur)): break
        if flen(vsub(target,cur)) < 3.0*avg: break
        t = min(0.92,(step+1)/L)
        tg = ideal(t)
        best=None
        for s in menu:
            cand=vadd(cur,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            d=sum((cand[i]-tg[i])**2 for i in range(n))
            if best is None or d<best[0]: best=(d,cand)
        if best is None:
            return False, len(added)
        cur=best[1]; points.append(cur); pset.add(cur); added.append(cur)
    # DFS endgame -> hit target exactly
    nodes=[0]
    maxstep=max(flen(s) for s in menu)
    def dfs(node, depth):
        if node==tuple(target): return True
        if depth<=0 or nodes[0]>node_budget: return False
        nodes[0]+=1
        if flen(vsub(target,node)) > depth*maxstep+1e-9: return False
        order=sorted(menu,key=lambda s: sum((node[i]+s[i]-target[i])**2 for i in range(len(node))))
        for s in order:
            cand=vadd(node,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            points.append(cand); pset.add(cand)
            if dfs(cand,depth-1): return True
            points.pop(); pset.discard(cand)
        return False
    for dcap in endgame_caps:
        nodes[0]=0
        if dfs(cur, dcap):
            return True, len(added)
    return False, len(added)

def seed_walk(menu, wlen):
    pts=[tuple(0 for _ in menu[0])]; pset=set(pts); cur=pts[0]
    for _ in range(wlen):
        placed=False
        for s in menu:
            cand=vadd(cur,s)
            if cand not in pset and legal(pts,cand):
                cur=cand; pts.append(cur); pset.add(cur); placed=True; break
        if not placed: break
    return pts

def build(menu, Kmax=6, avals=None, bcs=None, seed_word_len=4, prescale=None,
          rad_frac=0.10, verbose=True):
    if avals is None: avals=[2,3,4,5,6,7]
    if bcs is None: bcs=[(1,3),(1,2),(1,3),(1,2),(1,3),(1,2)]
    pts=seed_walk(menu, seed_word_len)
    if prescale is not None:
        pts=[matvec_int(prescale,p) for p in pts]
    anchors=pts[:]
    log=[("L0","pts",len(pts),"ft",first_triple(pts))]
    gap_stats=[]
    for k in range(Kmax):
        a=avals[k]; b,c=bcs[k]
        M=M4(a,b,c)
        scaled=[matvec_int(M,p) for p in anchors]
        newpts=[scaled[0]]; newpset={scaled[0]}
        ok=True; bridge_lens=[]; gaplens=[]
        for i in range(len(scaled)-1):
            if scaled[i] not in newpset:
                newpts.append(scaled[i]); newpset.add(scaled[i])
            g=vsub(scaled[i+1],scaled[i]); gl=flen(g); gaplens.append(gl)
            R1=max(4,int(rad_frac*gl)); R2=max(4,int(rad_frac*gl))
            T1=max(2,int(gl/50)); T2=max(2,int(gl/60))
            before=len(newpts)
            bok,nadd=bridge_double_helix(scaled[i],scaled[i+1],menu,newpts,newpset,R1,R2,T1,T2)
            bridge_lens.append(len(newpts)-before)
            if not bok:
                ok=False
                log.append((f"L{k+1}","BRIDGE-FAIL","seg",i,"gaplen",round(gl,1),
                            "added_before_stall",nadd))
                break
            if scaled[i+1] not in newpset:
                newpts.append(scaled[i+1]); newpset.add(scaled[i+1])
        ft=first_triple(newpts)
        maxgap=max(gaplens) if gaplens else 0
        gap_stats.append((k+1,round(maxgap,1)))
        log.append((f"L{k+1}","pts",len(newpts),"maxgap",round(maxgap,1),
                    "bridge_lens",bridge_lens,"bridged_ok",ok,"first_triple",ft))
        if not ok or ft is not None:
            return log, newpts, gap_stats
        anchors=newpts
    return log, anchors, gap_stats

if __name__=="__main__":
    menu=twist4
    # pre-enlarge so gaps start LARGE (helical bridge design regime)
    P=M4(7,1,2)
    P=[[sum(P[i][k]*P[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
    print("C-H: n=4 double-rotation M4 + chiral twist4 menu")
    print("Building >=6 levels...")
    log,pts,gs=build(menu,Kmax=6,seed_word_len=4,prescale=P)
    for row in log: print("  ",row)
    print("GAP GROWTH (level,maxgap):",gs)
    print("FINAL pts:",len(pts),"first_triple:",first_triple(pts))
