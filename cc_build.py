"""
CANDIDATE C-C: isolate CHIRALITY.
 Menu  = SCREW6 (chiral, gen Z^3).
 Matrix= FIXED all-moduli-3 map applied EVERY level (stationary, NOT accelerating).
   Primary: Mfix = companion(x^3-27) = [[0,0,27],[1,0,0],[0,1,0]]  (all |eig|=3,
            complex pair angle +-120deg, cos=-1/2 RATIONAL -> Niven-periodic).
   Also test: M_BAL3 = [[3,0,0],[0,0,-3],[0,3,-1]] (all |eig|=3, cos=-1/6 IRRATIONAL).
Run full battery T1-T5, brutally honest.
"""
from chiral_accel import *
from math import hypot, pi, cos, sin, degrees
import cmath
def cmath_phase(z): return degrees(cmath.phase(z))

SCREW6 = [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)]
MFIX   = [[0,0,27],[1,0,0],[0,1,0]]          # companion x^3-27
MBAL3  = [[3,0,0],[0,0,-3],[0,3,-1]]         # irrational-twist fixed all-moduli-3

def matvec_int(M,v):
    return tuple(sum(M[i][j]*v[j] for j in range(len(v))) for i in range(len(M)))
def matmul_int(A,B):
    n=len(A);m=len(B[0]);k=len(B)
    return [[sum(A[i][t]*B[t][j] for t in range(k)) for j in range(m)] for i in range(n)]

def frame(g):
    glen=hypot(*[float(x) for x in g]); ax=[x/glen for x in g]
    e=[1.0,0,0]
    if abs(dot(e,ax))>0.9: e=[0,1.0,0]
    u=[e[i]-dot(e,ax)*ax[i] for i in range(3)]; un=hypot(*u); u=[x/un for x in u]
    w=[ax[1]*u[2]-ax[2]*u[1],ax[2]*u[0]-ax[0]*u[2],ax[0]*u[1]-ax[1]*u[0]]
    return ax,u,w,glen

def bridge_exact(start,target,menu,points,pset,radius,turns,node_budget=80000):
    g=vsub(target,start)
    if g==(0,0,0): return True,0
    ax,u,w,glen=frame(g)
    def ideal(t):
        ang=2*pi*turns*t; rad=radius*sin(pi*t)
        return [start[i]+t*g[i]+rad*(cos(ang)*u[i]+sin(ang)*w[i]) for i in range(3)]
    cur=start; added=0
    avg=sum(hypot(*[float(x) for x in s]) for s in menu)/len(menu)
    L=max(8,int((glen+2*pi*turns*radius)/avg))
    for step in range(3*L):
        if vsub(target,cur)==(0,0,0): break
        if hypot(*[float(x) for x in vsub(target,cur)])<3.0*avg: break
        t=min(0.90,(step+1)/L); tg=ideal(t); best=None
        for s in menu:
            cand=vadd(cur,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            d=sum((cand[i]-tg[i])**2 for i in range(3))
            if best is None or d<best[0]: best=(d,cand)
        if best is None: return False,added
        cur=best[1]; points.append(cur); pset.add(cur); added+=1
    nodes=[0]; maxstep=max(hypot(*[float(x) for x in s]) for s in menu)
    def dfs(node,depth):
        if node==tuple(target): return True
        if depth<=0 or nodes[0]>node_budget: return False
        nodes[0]+=1
        remlen=hypot(*[float(x) for x in vsub(target,node)])
        if remlen>depth*maxstep+1e-9: return False
        order=sorted(menu,key=lambda s: sum((node[i]+s[i]-target[i])**2 for i in range(3)))
        for s in order:
            cand=vadd(node,s)
            if cand in pset: continue
            if not legal(points,cand): continue
            points.append(cand); pset.add(cand)
            if dfs(cand,depth-1): return True
            points.pop(); pset.discard(cand)
        return False
    for dcap in (6,9,12,16,22,30):
        nodes[0]=0
        if dfs(cur,dcap): return True,added
    return False,added

def build(menu, Mfix, Kmax=6, seed_word_len=4, prescale_pow=2, radiusfrac=0.10):
    pts=[(0,0,0)]; pset=set(pts); cur=pts[0]
    for _ in range(seed_word_len):
        for s in menu:
            cand=vadd(cur,s)
            if cand not in pset and legal(pts,cand):
                cur=cand; pts.append(cur); pset.add(cur); break
    # pre-enlarge so gaps start large (bridge's design regime)
    P=[[1,0,0],[0,1,0],[0,0,1]]
    for _ in range(prescale_pow): P=matmul_int(P,Mfix)
    pts=[matvec_int(P,p) for p in pts]; pset=set(pts)
    anchors=pts[:]; log=[]
    log.append(("L0","pts",len(pts),"first_triple",first_triple(pts)))
    bridge_lens=[]
    for k in range(Kmax):
        scaled=[matvec_int(Mfix,p) for p in anchors]   # SAME fixed map each level
        newpts=[scaled[0]]; newpset={scaled[0]}; ok=True
        gaps=[]
        for i in range(len(scaled)-1):
            if scaled[i] not in newpset:
                newpts.append(scaled[i]); newpset.add(scaled[i])
            gaplen=hypot(*[float(x) for x in vsub(scaled[i+1],scaled[i])])
            gaps.append(gaplen)
            rad=max(5,int(radiusfrac*gaplen)); tn=max(2,int(gaplen/40))
            okb,added=bridge_exact(scaled[i],scaled[i+1],menu,newpts,newpset,rad,tn)
            bridge_lens.append(added)
            if not okb:
                ok=False
                log.append((f"L{k+1}","BRIDGE-FAIL seg",i,"gaplen",round(gaplen,1),
                            "pts_so_far",len(newpts)))
                break
            if scaled[i+1] not in newpset:
                newpts.append(scaled[i+1]); newpset.add(scaled[i+1])
        ft=first_triple(newpts)
        log.append((f"L{k+1}","pts",len(newpts),"gaps~",[round(g,1) for g in gaps[:3]],
                    "bridged_ok",ok,"first_triple",ft))
        if not ok or ft is not None:
            return log,newpts,bridge_lens,False
        anchors=newpts; pts=newpts; pset=newpset
    return log,anchors,bridge_lens,True

if __name__=="__main__":
    import sys
    which=sys.argv[1] if len(sys.argv)>1 else "MFIX"
    M = MFIX if which=="MFIX" else MBAL3
    print(f"=== C-C build with {which} = {M} ===")
    print("charpoly(lo->hi):",charpoly(M))
    roots=durand_kerner(charpoly(M))
    print("eig moduli:",sorted(round(abs(z),4) for z in roots))
    print("eig angles(deg):",sorted(round(cmath_phase(z),2) for z in roots))
    log,pts,blens,ok=build(SCREW6,M,Kmax=6,seed_word_len=4,prescale_pow=2)
    for row in log: print("   ",row)
    print("FINAL pts:",len(pts),"first_triple:",first_triple(pts),"6-level-ok:",ok)
    if blens: print("bridge lens:",blens[:12],"...max",max(blens))
