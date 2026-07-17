"""DEEP branch-and-bound: min|B_J| vs DEPTH J for the prescaled non-resonant family
M_k = M3(a_k)^2 (family index 2, F3_prescaled_M3a_squared_MILD). Compare to fixed M_BAL3.

B_J = sum_{lev=0..J} Q_lev . delta_lev,  Q_lev = M_J^{-1} M_{J-1}^{-1} ... M_{lev+1}^{-1} (Q_J=I),
delta_lev in E, delta_J != 0. Collinearity/coincidence across seam <=> B_J = 0.
mu_J = min|B_J|. Want: bounded below by c>0 AND non-shrinking as J grows.

Branch-and-bound: exact Fraction acc, precomputed tail-norm bounds prune branches whose
best-possible completion cannot beat current best. Lets us push J far past exhaustive limit.
"""
from fractions import Fraction as Fr
from itertools import product
import time, sys

def M3(a,b=1): return [[a,0,0],[0,0,-a*a],[0,1,-b]]
def matmul(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def matpow(A,p):
    R=[[int(i==j) for j in range(3)] for i in range(3)]
    for _ in range(p): R=matmul(R,A)
    return R
def inv3(m):
    det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    cof=[[(m[(i+1)%3][(j+1)%3]*m[(i+2)%3][(j+2)%3]-m[(i+1)%3][(j+2)%3]*m[(i+2)%3][(j+1)%3]) for j in range(3)] for i in range(3)]
    return [[Fr(cof[j][i],det) for j in range(3)] for i in range(3)]
def mmfr(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mvfr(A,v): return tuple(sum(A[i][k]*v[k] for k in range(3)) for i in range(3))
def fnorm(A): return sum(float(A[i][j])**2 for i in range(3) for j in range(3))**0.5
def nrm(v): return sum(float(x)*float(x) for x in v)**0.5

def bnb_min(maps, E, J, time_budget=60.0):
    """maps[lev] integer matrix at level lev (lev=J outermost). Returns (min|B_J|, argmin, nodes, timed_out)."""
    # Q_lev = product of M^{-1} for levels J..lev+1. Q_J = I. Q_{lev-1}=Q_lev . M_lev^{-1}.
    Minv=[inv3(maps[lv]) for lv in range(J+1)]
    I=[[Fr(i==j) for j in range(3)] for i in range(3)]
    Q=[None]*(J+1)
    Q[J]=I
    for lev in range(J-1,-1,-1):
        Q[lev]=mmfr(Q[lev+1],Minv[lev+1])
    fQ=[fnorm(Q[lev]) for lev in range(J+1)]
    maxE=max(nrm(e) for e in E)
    # tailbound[level] = max possible norm contributed by levels {level, level-1, ..., 0}
    tail=[0.0]*(J+2)
    for level in range(0,J+1):
        tail[level]=sum(fQ[l] for l in range(0,level+1))*maxE
    # sort digits by norm ascending => DFS hits near-minimal completions early => strong pruning
    Efr=[tuple(Fr(x) for x in e) for e in sorted(E,key=nrm)]
    zero=(0,0,0)
    best=[float("inf")]; bestB=[None]; nodes=[0]
    t0=time.time(); timed=[False]
    # DFS from outermost level J inward. acc = partial sum of added terms.
    def dfs(level,acc):
        if timed[0]: return
        nodes[0]+=1
        if (nodes[0]&0x3FFFF)==0 and time.time()-t0>time_budget:
            timed[0]=True; return
        if level<0:
            v=nrm(acc)
            if v<best[0]: best[0]=v; bestB[0]=acc
            return
        # prune: |acc| - tail[level] > best  => cannot beat
        a=nrm(acc)
        if a-tail[level]>best[0]: return
        Ql=Q[level]
        for d in Efr:
            if level==J and tuple(int(x) for x in d)==zero: continue
            add=mvfr(Ql,d)
            nacc=(acc[0]+add[0],acc[1]+add[1],acc[2]+add[2])
            dfs(level-1,nacc)
    dfs(J,(Fr(0),Fr(0),Fr(0)))
    return best[0],bestB[0],nodes[0],timed[0]

if __name__=="__main__":
    t0=time.time()
    BOX=int(sys.argv[1]) if len(sys.argv)>1 else 2
    MAXJ=int(sys.argv[2]) if len(sys.argv)>2 else 6
    TB=float(sys.argv[3]) if len(sys.argv)>3 else 45.0
    E=[v for v in product(range(-BOX,BOX+1),repeat=3)]
    print(f"box E = {{-{BOX}..{BOX}}}^3, |E|={len(E)}, per-depth time budget {TB}s")
    print("="*70)
    print("FAMILY 2  PRESCALED accel  M_k = M3(k+2)^2  (moduli 4,9,16,25,... increasing)")
    print("  mu_J = min|B_J|  (want bounded below c>0 AND non-shrinking):")
    for J in range(1,MAXJ+1):
        maps=[matpow(M3(lv+2),2) for lv in range(J+1)]
        val,B,nd,to=bnb_min(maps,E,J,TB)
        tag=" [TIMED OUT-lower bound only]" if to else ""
        bs=tuple(str(x) for x in B) if B else None
        print(f"  J={J}: mu_J={float(val):.6f}  nodes={nd}  argmin={bs}{tag}",flush=True)
    print("-"*70)
    print("CONTROL B  FIXED prescaled  M_k = M3(3)^2  (constant, non-resonant):")
    for J in range(1,MAXJ+1):
        maps=[matpow(M3(3),2) for _ in range(J+1)]
        val,B,nd,to=bnb_min(maps,E,J,TB)
        tag=" [TIMED OUT]" if to else ""
        print(f"  J={J}: mu_J={float(val):.6f}  nodes={nd}{tag}",flush=True)
    print("-"*70)
    print("CONTROL A  RESONANT accel  M_k = M3(k+2)  (no prescale): expect 0")
    for J in range(1,min(MAXJ,4)+1):
        maps=[M3(lv+2) for lv in range(J+1)]
        val,B,nd,to=bnb_min(maps,E,J,TB)
        print(f"  J={J}: mu_J={float(val):.6f}  nodes={nd}",flush=True)
    print("-"*70)
    print("BASELINE  FIXED M_BAL3 = [[3,0,0],[0,0,-3],[0,3,-1]]  (c=0 on true closure):")
    MBAL=[[3,0,0],[0,0,-3],[0,3,-1]]
    for J in range(1,min(MAXJ,4)+1):
        maps=[MBAL for _ in range(J+1)]
        val,B,nd,to=bnb_min(maps,E,J,TB)
        bs=tuple(str(x) for x in B) if B else None
        print(f"  J={J}: mu_J={float(val):.6f}  nodes={nd}  argmin={bs}",flush=True)
    print(f"\n[{time.time()-t0:.1f}s] done.",flush=True)
