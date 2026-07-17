"""
LINE A: head-vs-tail via GROUPED scales.
Compute g(n) = min over nonzero v in D (and larger boxes) of |M^n v|_inf.
Test whether g(n) ~ c*lambda^n with lambda > 3^{tail-rate}, i.e. whether
grouping every n levels makes the head beat the tail UNIFORMLY in J.
All exact integer / Fraction arithmetic. No floats in the proofs; floats only for reporting.
"""
from fractions import Fraction as F
from itertools import product

M = [[3,0,0],[0,0,-3],[0,3,-1]]
# Q metric
Qm = [[1,0,0],[0,6,-1],[0,-1,6]]

def matmul(A,B):
    n=len(A); m=len(B[0]); k=len(B)
    return [[sum(A[i][t]*B[t][j] for t in range(k)) for j in range(m)] for i in range(n)]

def matpow(A,p):
    n=len(A)
    R=[[1 if i==j else 0 for j in range(n)] for i in range(n)]
    for _ in range(p):
        R=matmul(R,A)
    return R

def matvec(A,v):
    return [sum(A[i][t]*v[t] for t in range(len(v))) for i in range(len(A))]

def inf_norm(v):
    return max(abs(x) for x in v)

def Qnorm2(v):  # exact integer/Fraction v^T Q v
    x,y,z=v
    return x*x+6*y*y-2*y*z+6*z*z

# ---- verify MᵀQM = 9Q exactly ----
Mt=[[M[j][i] for j in range(3)] for i in range(3)]
MtQM=matmul(matmul(Mt,Qm),M)
NineQ=[[9*Qm[i][j] for j in range(3)] for i in range(3)]
print("MtQM == 9Q :", MtQM==NineQ, MtQM)

# ---- inf-norm of M^n and M^{-n} ----
def rowabs_sum_inf_norm(A):
    return max(sum(abs(x) for x in row) for row in A)

# M^{-1} exact via Fraction
def inv3(A):
    # general 3x3 inverse with Fractions
    a=[[F(A[i][j]) for j in range(3)] for i in range(3)]
    det=(a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
        -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
        +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
    cof=[[0]*3 for _ in range(3)]
    cof[0][0]= (a[1][1]*a[2][2]-a[1][2]*a[2][1])
    cof[0][1]=-(a[1][0]*a[2][2]-a[1][2]*a[2][0])
    cof[0][2]= (a[1][0]*a[2][1]-a[1][1]*a[2][0])
    cof[1][0]=-(a[0][1]*a[2][2]-a[0][2]*a[2][1])
    cof[1][1]= (a[0][0]*a[2][2]-a[0][2]*a[2][0])
    cof[1][2]=-(a[0][0]*a[2][1]-a[0][1]*a[2][0])
    cof[2][0]= (a[0][1]*a[1][2]-a[0][2]*a[1][1])
    cof[2][1]=-(a[0][0]*a[1][2]-a[0][2]*a[1][0])
    cof[2][2]= (a[0][0]*a[1][1]-a[0][1]*a[1][0])
    adj=[[cof[j][i] for j in range(3)] for i in range(3)]
    return [[adj[i][j]/det for j in range(3)] for i in range(3)]

Minv=inv3(M)
print("Minv=",Minv,"  ||Minv||_inf=",rowabs_sum_inf_norm(Minv))

def matpowF(A,p):
    n=len(A); R=[[F(1) if i==j else F(0) for j in range(n)] for i in range(n)]
    Af=[[F(x) for x in row] for row in A]
    for _ in range(p):
        R=matmul(R,Af)
    return R

print("\n n |  ||M^n||_inf   ||M^-n||_inf(exact)   (as float)")
Minf=[]; Mninf=[]
for n in range(1,13):
    Mn=matpow(M,n)
    Mninv=matpowF(Minv,n)
    a=rowabs_sum_inf_norm(Mn)
    b=rowabs_sum_inf_norm(Mninv)
    Minf.append(a); Mninf.append(b)
    print(f"{n:2d} | {a:12d}   {str(b):>16}   {float(b):.6f}")

# telescope S = sum_{j>=0} ||M^-j||_inf
S=F(1)
for n in range(1,60):
    S+=rowabs_sum_inf_norm(matpowF(Minv,n))
print("\nS = sum ||M^-j||_inf =", float(S))
print("S-1 (tail multiplier, inf) =", float(S-1))

# ---- g(n) = min nonzero |M^n v|_inf over box ----
def g_of_n(n, K):
    Mn=matpow(M,n)
    best=None; argb=None
    R=range(-K,K+1)
    for v in product(R,R,R):
        if v==(0,0,0): continue
        w=matvec(Mn,v)
        val=inf_norm(w)
        if best is None or val<best:
            best=val; argb=v
    return best,argb

print("\n n |  g(n)=min|M^n v|_inf  arg v   g(n)/3^n   g(n)^(1/n)   (over box K)")
gs=[]
import math
# check stability across K
for n in range(1,9):
    # search increasing K until min stabilizes
    prev=None; stable=None; Kused=None
    for K in (3,4,5,6,7):
        val,arg=g_of_n(n,K)
        if prev is not None and val==prev:
            stable=val; Kused=K-1; argstab=argprev; break
        prev=val; argprev=arg
    if stable is None:
        stable=val; Kused=7; argstab=arg
    gs.append(stable)
    r=stable/3**n
    print(f"{n:2d} | {stable:10d}          {str(argstab):12s} {r:.6f}   {stable**(1.0/n):.5f}   Kstable<={Kused}")

# ---- g(n) also restricted to D = {-4..4}^3 exactly (the digit set) ----
print("\ng(n) restricted to D={-4..4}^3 (nonzero):")
for n in range(1,9):
    val,arg=g_of_n(n,4)  # box exactly D
    print(f"  n={n}: min|M^n delta|_inf over D = {val}  at {arg}   /3^n={val/3**n:.6f}")

# ---- Q-norm min of M^n v: exact, must be 3^n (since |v|_Q>=1) ----
print("\nSanity Q: min|M^n v|_Q^2 over box K=4 (should be 9^n):")
for n in range(1,6):
    Mn=matpow(M,n); best=None
    for v in product(range(-4,5),repeat=3):
        if v==(0,0,0): continue
        best=min(best, Qnorm2(matvec(Mn,v))) if best is not None else Qnorm2(matvec(Mn,v))
    print(f"  n={n}: min|M^n v|_Q^2={best}  9^n={9**n}  ratio={best/9**n:.6f}")
