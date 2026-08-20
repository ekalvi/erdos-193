"""F2_M4_double_rotation_n4: min|B_J| vs DEPTH for the accelerating incommensurate
n=4 double-rotation family M4(a,b,c). Exact Fractions. Branch-and-bound with a
telescoping tail bound so we can push depth. Compare to FIXED M_BAL3 (n=3) c=0
baseline reproduced in the same harness.

M4(a,b,c)=[[0,-a^2,0,0],[1,-b,0,0],[0,0,0,-a^2],[0,0,1,-c]]
level k uses accelerating params a_k=k+3 (moduli 3,4,5,... increasing), (b,c) per level.
"""
from fractions import Fraction as Fr
from itertools import product
import time

def M4(a,b,c):
    return [[0,-a*a,0,0],[1,-b,0,0],[0,0,0,-a*a],[0,0,1,-c]]

def M_BAL3():  # fixed resonant baseline, n=3
    return [[3,0,0],[0,0,-3],[0,3,-1]]

def matinv(m):
    """Exact inverse of an n x n integer/Fraction matrix via Gauss-Jordan (Fractions)."""
    n=len(m)
    A=[[Fr(m[i][j]) for j in range(n)]+[Fr(int(i==j)) for j in range(n)] for i in range(n)]
    for col in range(n):
        piv=None
        for r in range(col,n):
            if A[r][col]!=0: piv=r; break
        if piv is None: raise ValueError("singular")
        A[col],A[piv]=A[piv],A[col]
        pv=A[col][col]
        A[col]=[x/pv for x in A[col]]
        for r in range(n):
            if r!=col and A[r][col]!=0:
                f=A[r][col]
                A[r]=[A[r][j]-f*A[col][j] for j in range(2*n)]
    return [[A[i][j+n] for j in range(n)] for i in range(n)]

def matmul(A,B):
    n=len(A); return [[sum(A[i][k]*B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def matvec(A,v):
    n=len(A); return tuple(sum(A[i][k]*v[k] for k in range(n)) for i in range(n))
def nrm(v): return sum(float(x)*float(x) for x in v)**0.5
def opnorm_rows(A):
    # crude upper bound on ||A||_2 via sqrt(max row L2 * max col L1)? use Frobenius as safe upper bound
    return sum(float(x)*float(x) for row in A for x in row)**0.5

def bracket_min(maps, E, J, use_bnb=True):
    """maps[level]=integer matrix; min euclidean |B_J| over delta_J!=0, delta_i in E.
    B = delta_J + M_J^{-1}(delta_{J-1}+ M_{J-1}^{-1}(...))  [Horner].
    DFS from outer level J down to 0. factor = product of inverses applied so far.
    tail bound: remaining levels contribute at most maxE_norm * ||factor*M^{-1}...||;
    we bound ||factor|| growth by Frobenius and geometric contraction."""
    n=len(maps[0])
    Minvs=[matinv(maps[lv]) for lv in range(J+1)]
    I=[[Fr(int(i==j)) for j in range(n)] for i in range(n)]
    Efr=[tuple(Fr(x) for x in e) for e in E]
    zero=(0,)*n
    maxEnorm=max(nrm(e) for e in Efr)
    # Frobenius norms of the successive inverse-products factor_level (for tail bound)
    best=[float("inf")]; bestB=[None]
    def dfs(level,acc,factor,factor_fro):
        if level<0:
            v=nrm(acc)
            if v<best[0]: best[0]=v; bestB[0]=tuple(acc)
            return
        if use_bnb and best[0]<float("inf"):
            # remaining levels 0..level each add factor_l * delta ; factor_l Frobenius shrinks.
            # conservative tail = maxEnorm * factor_fro / (1 - contraction). Use factor_fro * (level+1) upper bound
            # (safe: each further inverse multiply cannot increase Frobenius beyond factor_fro*||Minv||_fro,
            #  but we use simple bound maxEnorm*factor_fro*(level+1))
            tail = maxEnorm*factor_fro*(level+1)
            if nrm(acc)-tail > best[0]:
                return
        for d in Efr:
            if level==J and tuple(int(x) for x in d)==zero: continue
            add=matvec(factor,d)
            nacc=tuple(acc[i]+add[i] for i in range(n))
            nfactor=matmul(factor,Minvs[level])
            nfro=opnorm_rows(nfactor)
            dfs(level-1,nacc,nfactor,nfro)
    dfs(J,tuple(Fr(0) for _ in range(n)),I,opnorm_rows(I))
    return best[0],bestB[0]

if __name__=="__main__":
    t0=time.time()
    # accelerating incommensurate params, level 0..: a=3,4,5,6,7,... distinct (b,c), b!=c
    params=[(3,1,2),(4,2,3),(5,1,3),(6,1,4),(7,2,5),(8,1,5)]
    E2_4=[v for v in product(range(-2,3),repeat=4)]   # 625
    E1_4=[v for v in product(range(-1,2),repeat=4)]   # 81
    print("=== F2: ACCEL incommensurate M4(a_k,b_k,c_k), a_k=3,4,5,... (n=4 double rotation) ===")
    print("min|B_J| vs depth J (want bounded-below & NON-shrinking for a margin):")
    for (J,EE,lbl) in [(1,E2_4,"{-2..2}^4"),(2,E1_4,"{-1..1}^4"),(3,E1_4,"{-1..1}^4"),(4,E1_4,"{-1..1}^4")]:
        maps=[M4(*params[lv]) for lv in range(J+1)]
        val,B=bracket_min(maps,EE,J)
        bs=tuple(str(x) for x in B) if B else None
        print(f"  J={J} E={lbl} |E|={len(EE)}: min|B_J|={val:.6f}   argmin={bs}",flush=True)
    print("\n=== BASELINE: FIXED M_BAL3 (n=3) reproduced in same harness (expect 0) ===")
    E2_3=[v for v in product(range(-2,3),repeat=3)]
    E4_3=[v for v in product(range(-4,5),repeat=3)]
    for (J,EE,lbl) in [(1,E4_3,"{-4..4}^3"),(2,E2_3,"{-2..2}^3")]:
        maps=[M_BAL3() for _ in range(J+1)]
        val,B=bracket_min(maps,EE,J)
        bs=tuple(str(x) for x in B) if B else None
        print(f"  J={J} E={lbl}: min|B_J|={val:.6f}   argmin={bs}",flush=True)
    # depth-1 resonance witness for F2: is there e!=0 in E with M4(e) in E?  (M_k(menu-diff)=menu-diff)
    print("\n=== Resonance witness (M_k(menu-diff) IS a menu-diff => c=0 at depth 1) ===")
    for (a,b,c) in params[:3]:
        A=M4(a,b,c); Eset=set(E2_4); hit=None
        for e in E2_4:
            if e!=(0,0,0,0) and matvec(A,e) in Eset: hit=(e,matvec(A,e)); break
        print(f"  M4{(a,b,c)}: resonant pair e->M(e) = {hit}")
    print(f"\n[{time.time()-t0:.1f}s] done.",flush=True)
