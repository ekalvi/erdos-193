"""Family #0 = F1_M3a_n3_sequence: M3(a)=[[a,0,0],[0,0,-a^2],[0,1,-1]], level k uses a_k=k+1.
Measure mu_J = min|B_J| over non-trivial telescoping brackets vs DEPTH J, EXACT Fractions.
Compare to FIXED M_BAL3 baseline (c=0). Also test resonance M_k(e) in E at each level.
Go as deep as tractable via branch-and-bound with a tail bound so we can push J past 3."""
from fractions import Fraction as Fr
from itertools import product
import time

def M3(a): return [[a,0,0],[0,0,-a*a],[0,1,-1]]
MBAL3 = [[3,0,0],[0,0,-3],[0,3,-1]]

def inv3(m):
    det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    cof=[[(m[(i+1)%3][(j+1)%3]*m[(i+2)%3][(j+2)%3]-m[(i+1)%3][(j+2)%3]*m[(i+2)%3][(j+1)%3]) for j in range(3)] for i in range(3)]
    return [[Fr(cof[j][i],det) for j in range(3)] for i in range(3)]
def mmfr(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mvfr(A,v): return tuple(sum(A[i][k]*v[k] for k in range(3)) for i in range(3))
def nrm2(v): return float(v[0])**2+float(v[1])**2+float(v[2])**2
def nrm(v): return nrm2(v)**0.5

def opnorm_bound(factor):
    # crude upper bound on ||factor||_2 via Frobenius, for tail pruning
    return sum(float(factor[i][j])**2 for i in range(3) for j in range(3))**0.5

def bracket_min(maps, E, J, prune=True):
    """maps[level] integer matrix; level J outermost. min|B_J|, delta_J != 0, delta_i in E."""
    Minvs=[inv3(maps[lv]) for lv in range(J+1)]
    I=[[Fr(int(i==j)) for j in range(3)] for i in range(3)]
    Efr=[tuple(Fr(x) for x in e) for e in E]
    maxE = max(nrm(e) for e in Efr)
    best=[float("inf")]; bestB=[None]
    zero=(0,0,0)
    def dfs(level,acc,factor):
        if level<0:
            v=nrm2(acc)
            if v<best[0]: best[0]=v; bestB[0]=acc
            return
        # tail bound: remaining levels contribute at most sum_{i<=level} ||factor*Minv^...||*maxE
        # cheap: use current factor opnorm times geometric-ish; compute exact per-step is costly, so
        # bound tail by maxE * ||factor|| * (level+1) * (contraction). We compute a safe bound:
        if prune and best[0]<float("inf"):
            fb=opnorm_bound(factor)
            # each deeper digit adds <= maxE * (opnorm of factor * prod of subsequent Minv norms).
            # Use non-increasing assumption is NOT safe generally; use loose bound maxE*fb*(level+1)*3
            tail = maxE*fb*(level+1)*2.0
            cur = nrm(acc)
            if (cur-tail)**2 > best[0] and cur>tail:
                return
        for d in Efr:
            if level==J and tuple(int(x) for x in d)==zero: continue
            add=mvfr(factor,d)
            nacc=(acc[0]+add[0],acc[1]+add[1],acc[2]+add[2])
            dfs(level-1,nacc,mmfr(factor,Minvs[level]))
    dfs(J,(Fr(0),Fr(0),Fr(0)),I)
    return best[0]**0.5,bestB[0]

def mv(A,v): return tuple(sum(A[i][k]*v[k] for k in range(len(A))) for k in [0] for _ in [0]) if False else tuple(sum(A[i][k]*v[k] for k in range(len(A))) for i in range(len(A)))

if __name__=="__main__":
    t0=time.time()
    E2=[v for v in product(range(-2,3),repeat=3)]
    E1=[v for v in product(range(-1,2),repeat=3)]

    print("=== FAMILY #0 : F1_M3a_n3_sequence  M3(a_k), a_k=k+2 (level0->a=2) ===\n")

    print("[RESONANCE depth-1 trigger]  does M_k(e) in E for nonzero e in E ?  (E={-2..2}^3)")
    Eset=set(E2)
    for lv in range(5):
        a=lv+2; A=M3(a); hits=[e for e in E2 if e!=(0,0,0) and mv(A,e) in Eset]
        ex = hits[0] if hits else None
        print(f"  level {lv} a={a}: {len(hits)} resonant pairs"+(f"  e.g. {ex}->{mv(A,ex)}" if ex else "  NON-RESONANT"))
    print()

    print("[mu_J = min|B_J| vs DEPTH]  Family #0 accel M3(a_k):")
    for (J,EE,lbl) in [(1,E2,"{-2..2}"),(2,E2,"{-2..2}"),(3,E1,"{-1..1}"),(4,E1,"{-1..1}")]:
        maps=[M3(lv+2) for lv in range(J+1)]
        val,B=bracket_min(maps,EE,J)
        print(f"  J={J} E={lbl} |E|={len(EE)}: min|B_J|={val:.6f}   arg={tuple(str(x) for x in B) if B else None}",flush=True)
    print()

    print("[BASELINE FIXED M_BAL3]  min|B_J| vs depth (expect 0 = c=0 resonance):")
    for (J,EE,lbl) in [(1,E2,"{-2..2}"),(2,E2,"{-2..2}"),(3,E1,"{-1..1}")]:
        maps=[MBAL3 for _ in range(J+1)]
        val,B=bracket_min(maps,EE,J)
        print(f"  J={J} E={lbl}: min|B_J|={val:.6f}   arg={tuple(str(x) for x in B) if B else None}",flush=True)
    print()

    print(f"[{time.time()-t0:.1f}s] done.",flush=True)
