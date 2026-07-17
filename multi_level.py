"""
T2 CRUX: build a genuine multi-level accelerating+chiral walk and check the
WHOLE point set for triple-freeness across >=6 levels.

Level 0: short triple-free menu walk (anchors).
Level k->k+1: scale entire current path by M_k (preserves collinearity), then
insert a helical chiral bridge between each consecutive scaled point pair,
landing EXACTLY on the next anchor (DFS endgame) while staying legal.
"""
from chiral_accel import *
from math import hypot, pi, cos, sin

def frame(g, n=3):
    glen = hypot(*[float(x) for x in g])
    ax = [x/glen for x in g]
    e = [1.0,0,0]
    if abs(dot(e,ax))>0.9: e=[0,1.0,0]
    u=[e[i]-dot(e,ax)*ax[i] for i in range(3)]; un=hypot(*u); u=[x/un for x in u]
    w=[ax[1]*u[2]-ax[2]*u[1],ax[2]*u[0]-ax[0]*u[2],ax[0]*u[1]-ax[1]*u[0]]
    return ax,u,w,glen

def bridge_exact(start, target, menu, points, pset, radius, turns,
                 node_budget=60000):
    """
    Helical greedy from start toward target, then DFS endgame to land EXACTLY,
    keeping the GLOBAL point set (points/pset) triple-free.  Mutates points/pset
    on success. Returns True/False.
    """
    g = vsub(target, start)
    if g == tuple(0 for _ in g): return True
    ax,u,w,glen = frame(g)
    def ideal(t):
        ang=2*pi*turns*t
        rad=radius*sin(pi*t)         # spindle: 0 at both ends -> exact endpoints
        return [start[i]+t*g[i]+rad*(cos(ang)*u[i]+sin(ang)*w[i]) for i in range(3)]
    # phase 1: greedy helix follow until close to target
    cur=start
    added=[]
    avg=sum(hypot(*[float(x) for x in s]) for s in menu)/len(menu)
    L=max(8,int((glen+2*pi*turns*radius)/avg))
    for step in range(3*L):
        if vsub(target,cur)==tuple(0 for _ in g): break
        # once within endgame range, stop greedy and DFS
        if hypot(*[float(x) for x in vsub(target,cur)]) < 3.0*avg: break
        t=min(0.90,(step+1)/L)
        tg=ideal(t)
        best=None
        for s in menu:
            cand=vadd(cur,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            d=sum((cand[i]-tg[i])**2 for i in range(3))
            if best is None or d<best[0]: best=(d,cand)
        if best is None:
            return False
        cur=best[1]; points.append(cur); pset.add(cur); added.append(cur)
    # phase 2: DFS endgame -> hit target exactly (deeper, mild admissible prune)
    nodes=[0]
    maxstep=max(hypot(*[float(x) for x in s]) for s in menu)
    def dfs(node, depth):
        if node==tuple(target): return True
        if depth<=0 or nodes[0]>node_budget: return False
        nodes[0]+=1
        remlen=hypot(*[float(x) for x in vsub(target,node)])
        if remlen > depth*maxstep + 1e-9: return False   # admissible: unreachable
        order=sorted(menu,key=lambda s: sum((node[i]+s[i]-target[i])**2 for i in range(3)))
        for s in order:
            cand=vadd(node,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            points.append(cand); pset.add(cand)
            if dfs(cand,depth-1): return True
            points.pop(); pset.discard(cand)
        return False
    for dcap in (6,9,12,16,22):
        nodes[0]=0
        if dfs(cur, dcap):
            return True
    return False

def build(menu, Kmax=6, avals=None, radius=6, turns=3, seed_word_len=5,
          prescale=None):
    if avals is None: avals=[2,3,4,5,6,7]
    # level-0 seed: a triple-free greedy menu walk
    pts=[tuple(0 for _ in menu[0])]; pset=set(pts)
    cur=pts[0]
    for _ in range(seed_word_len):
        for s in menu:
            cand=vadd(cur,s)
            if cand not in pset and legal(pts,cand):
                cur=cand; pts.append(cur); pset.add(cur); break
    # optional pre-enlargement so gaps start LARGE (bridge's intended regime)
    if prescale is not None:
        pts=[matvec_int(prescale,p) for p in pts]
        pset=set(pts)
    anchors=pts[:]                      # current-level anchor sequence
    log=[]
    log.append(("L0", len(pts), first_triple(pts)))
    for k in range(Kmax):
        a=avals[k]
        M=M3(a)
        scaled=[tuple(matvec_int(M,p) for p in [p])[0] for p in anchors]
        scaled=[matvec_int(M,p) for p in anchors]
        # rebuild full path: scaled[0], bridge, scaled[1], bridge, ...
        newpts=[scaled[0]]
        newpset={scaled[0]}
        ok=True
        for i in range(len(scaled)-1):
            # ensure current anchor in global set
            if scaled[i] not in newpset:
                newpts.append(scaled[i]); newpset.add(scaled[i])
            gaplen=hypot(*[float(x) for x in vsub(scaled[i+1],scaled[i])])
            rad=max(5,int(0.10*gaplen))
            tn=max(2,int(gaplen/40))     # gentle: many steps per turn
            if not bridge_exact(scaled[i],scaled[i+1],menu,newpts,newpset,rad,tn):
                ok=False
                log.append((f"L{k+1}", "BRIDGE-FAIL seg", i, "gaplen", round(gaplen,1)))
                break
            if scaled[i+1] not in newpset:
                newpts.append(scaled[i+1]); newpset.add(scaled[i+1])
        ft=first_triple(newpts)
        log.append((f"L{k+1}", "pts", len(newpts), "bridged_ok", ok,
                    "first_triple", ft))
        if not ok or ft is not None:
            return log, newpts
        anchors=newpts
        pts=newpts; pset=newpset
    return log, anchors

def matvec_int(M,v):
    return tuple(sum(M[i][j]*v[j] for j in range(len(v))) for i in range(len(M)))

if __name__=="__main__":
    menu=[(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)]  # SCREW6 chiral
    # pre-enlarge seed so even level-1 gaps are large (bridge's design regime)
    P=M3(7); P=[[sum(P[i][k]*P[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    print("menu SCREW6 chiral, LARGE-GAP multi-level accelerating walk...")
    log,pts=build(menu,Kmax=6,seed_word_len=4,prescale=P)
    for row in log: print("  ",row)
    print("FINAL points:",len(pts),"first_triple:",first_triple(pts))
