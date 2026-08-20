"""
LINE A part 2: the decisive rate comparison and grouped-bound margin.
- head-floor rate  lambda = lim g(n)^(1/n)
- tail contraction rate (spectral radius M^-1 = 1/3, i.e. 3^{tail-rate} with tail-rate=1)
- grouped self-similar margin in the EXACT Q-metric:
    base N=M^n, super-digits d in D_n = sum_{r=0}^{n-1} M^r D.
    |Delta|_Q >= 3^{nB} ( minQ_n  -  maxQ_n/(3^n - 1) )
  head floor minQ_n = 1 (achievable). If maxQ_n/(3^n-1) < 1 for some n -> CLOSES.
"""
from fractions import Fraction as F
from itertools import product
import math, random

M=[[3,0,0],[0,0,-3],[0,3,-1]]
Qm=[[1,0,0],[0,6,-1],[0,-1,6]]
def matmul(A,B):
    return [[sum(A[i][t]*B[t][j] for t in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]
def matpow(A,p):
    R=[[1 if i==j else 0 for j in range(3)] for i in range(3)]
    for _ in range(p): R=matmul(R,A)
    return R
def matvec(A,v): return [sum(A[i][t]*v[t] for t in range(3)) for i in range(3)]
def inf_norm(v): return max(abs(x) for x in v)
def Qn2(v):
    x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def Qdot(u,v):  # u^T Q v
    return (u[0]*v[0] + 6*u[1]*v[1] - u[1]*v[2] - u[2]*v[1] + 6*u[2]*v[2])

D=[v for v in product(range(-4,5),repeat=3) if v!=(0,0,0)]
print("|D nonzero| =",len(D),"  max|d|_inf=",max(inf_norm(v) for v in D),
      "  max|d|_Q=",max(Qn2(v) for v in D)**0.5)

# ---- g(n) extended, lambda = g(n)^(1/n) ----
def g_of_n(n,K):
    Mn=matpow(M,n); best=None
    for v in product(range(-K,K+1),repeat=3):
        if v==(0,0,0): continue
        val=inf_norm(matvec(Mn,v))
        if best is None or val<best: best=val
    return best
print("\nHead-floor rate:  n, g(n), g(n)/3^n, g(n)^(1/n)")
for n in range(1,12):
    g=g_of_n(n,5)
    print(f"  n={n:2d}: g={g:8d}  g/3^n={g/3**n:.5f}  g^(1/n)={g**(1.0/n):.5f}")
print("theoretical floor g(n)/3^n >= 1/sqrt(21) =",1/math.sqrt(21))

# ---- maxQ_n : achievable max Q-norm super-digit via direction sweep (lower bound on maxQ_n)
#      + rigorous triangle UPPER bound Sum 3^r sqrt(240)
def maxQ_n_achievable(n, ndir=4000):
    MrD=[]  # list over r of list of M^r delta
    for r in range(n):
        Mr=matpow(M,r)
        MrD.append([matvec(Mr,d) for d in D])
    best=0; bestp=None
    for _ in range(ndir):
        u=[random.gauss(0,1) for _ in range(3)]
        # maximize <p, Q u> = sum_r max_delta <M^r delta, Q u>
        Qu=[Qdot([1,0,0],u),Qdot([0,1,0],u),Qdot([0,0,1],u)]  # (Q u) as vector
        p=[0,0,0]
        for r in range(n):
            bd=None;bv=None
            for w in MrD[r]:
                val=w[0]*Qu[0]+w[1]*Qu[1]+w[2]*Qu[2]
                if bv is None or val>bv: bv=val; bd=w
            p=[p[0]+bd[0],p[1]+bd[1],p[2]+bd[2]]
        q=Qn2(p)
        if q>best: best=q; bestp=p
    return best**0.5, bestp
sqrt240=240**0.5
print("\nGrouped Q-margin:  n | minQ_n | maxQ_n(achv) | triangleUB | tailceil=maxQ/(3^n-1) | MARGIN=1-tailceil")
for n in range(1,8):
    mQ,pp=maxQ_n_achievable(n, 3000)
    tri=sqrt240*(3**n-1)/2
    tailceil_low=mQ/(3**n-1)          # from achievable (lower bd on true tail ceiling)
    tailceil_up =tri/(3**n-1)          # from triangle (upper bd)
    print(f"  n={n} | 1 | {mQ:9.4f} | {tri:10.4f} | in[{tailceil_low:.4f},{tailceil_up:.4f}] | MARGIN in [{1-tailceil_up:.4f},{1-tailceil_low:.4f}]")

# ---- inf-metric grouped margin using g(n) as head, ||M^-ni|| tail with super-digit max_inf
def maxinf_n(n):
    # max |sum M^r delta_r|_inf, triangle UB
    return sum(matpow(M,r) and max(inf_norm(matvec(matpow(M,r),d)) for d in D) for r in range(n))
print("\nInf-metric check (rates): 3^{tail-rate}=spectral(M)/? ; contraction spectral(M^-1)=1/3")
print("So 3^{tail-rate} = 3.  Compare lambda=lim g^(1/n) -> 3.  Equality => no scale gap.")
