"""DECISIVE: min|B_J| vs DEPTH for the NON-RESONANT prescaled family M_k = M3(a_k)^2.
Does the separation margin stay bounded below (>=c>0, non-shrinking) or drift to 0
(deferred resonance)?  Exact Fractions, full DFS on {-2..2}^3 (J<=2) and {-1..1}^3 (J=3)."""
from fractions import Fraction as Fr
from itertools import product
import time
def M3(a,b=1): return [[a,0,0],[0,0,-a*a],[0,1,-b]]
def mm(A,B):
    n=len(A); return [[sum(A[i][k]*B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def mp(A,p):
    R=[[int(i==j) for j in range(3)] for i in range(3)]
    for _ in range(p): R=mm(R,A)
    return R
def inv3(m):
    det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    cof=[[(m[(i+1)%3][(j+1)%3]*m[(i+2)%3][(j+2)%3]-m[(i+1)%3][(j+2)%3]*m[(i+2)%3][(j+1)%3]) for j in range(3)] for i in range(3)]
    return [[Fr(cof[j][i],det) for j in range(3)] for i in range(3)]
def mmfr(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mvfr(A,v): return tuple(sum(A[i][k]*v[k] for k in range(3)) for i in range(3))
def nrm(v): return sum(float(x)*float(x) for x in v)**0.5

def bracket_min(maps, E, J):
    """maps[level] = integer matrix at that level (level J outermost). min|B_J|, delta_J!=0."""
    Minvs=[inv3(maps[lv]) for lv in range(J+1)]
    I=[[Fr(i==j) for j in range(3)] for i in range(3)]
    best=[float("inf")]; bestB=[None]
    Efr=[tuple(Fr(x) for x in e) for e in E]; zero=(0,0,0)
    def dfs(level,acc,factor):
        if level<0:
            v=nrm(acc)
            if v<best[0]: best[0]=v; bestB[0]=acc
            return
        for d in Efr:
            if level==J and tuple(int(x) for x in d)==zero: continue
            add=mvfr(factor,d)
            nacc=(acc[0]+add[0],acc[1]+add[1],acc[2]+add[2])
            dfs(level-1,nacc,mmfr(factor,Minvs[level]))
    dfs(J,(Fr(0),Fr(0),Fr(0)),I)
    return best[0],bestB[0]

if __name__=="__main__":
    t0=time.time()
    E2=[v for v in product(range(-2,3),repeat=3)]
    E1=[v for v in product(range(-1,2),repeat=3)]
    print("PRESCALED non-resonant family: M_k = M3(k+2)^2  (level 0->M3(2)^2, 1->M3(3)^2,...)")
    print("min|B_J| vs depth J  (want: bounded below, NON-shrinking):")
    for (J,EE) in [(1,E2),(2,E2),(3,E1)]:
        maps=[mp(M3(lv+2),2) for lv in range(J+1)]
        val,B=bracket_min(maps,EE,J)
        print(f"  J={J} |E|={len(EE)}: min|B_J|={val:.6f}   argmin B={tuple(str(x) for x in B)}",flush=True)
    print("\nControl A - RESONANT accel M_k=M3(k+2) (no prescale): expect 0")
    for (J,EE) in [(1,E2),(2,E2)]:
        maps=[M3(lv+2) for lv in range(J+1)]
        val,_=bracket_min(maps,EE,J)
        print(f"  J={J}: min|B_J|={val:.6f}",flush=True)
    print("\nControl B - FIXED prescaled M_k=M3(3)^2 (constant, non-resonant): margin vs depth")
    for (J,EE) in [(1,E2),(2,E2),(3,E1)]:
        maps=[mp(M3(3),2) for _ in range(J+1)]
        val,_=bracket_min(maps,EE,J)
        print(f"  J={J}: min|B_J|={val:.6f}",flush=True)
    print(f"\n[{time.time()-t0:.1f}s] done.",flush=True)
