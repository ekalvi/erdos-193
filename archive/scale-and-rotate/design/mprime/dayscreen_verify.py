"""
Day-3 screen: exact-integer verification of the absorbing-separation criterion.
All algebra is exact (Python big ints / Fractions). No floats in any
collinearity / valuation / rank test.
"""
from fractions import Fraction as F
from math import gcd, acos, pi
import random

# ---------- exact 3x3 integer linear algebra ----------
def det3(M):
    a,b,c = M[0]; d,e,f = M[1]; g,h,i = M[2]
    return a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)

def cof3(M):
    # cofactor matrix C_{ij} = (-1)^{i+j} minor_{ij}; cof(M)=det(M)*M^{-T}
    a,b,c = M[0]; d,e,f = M[1]; g,h,i = M[2]
    C = [[ (e*i-f*h), -(d*i-f*g),  (d*h-e*g)],
         [-(b*i-c*h),  (a*i-c*g), -(a*h-b*g)],
         [ (b*f-c*e), -(a*f-c*d),  (a*e-b*d)]]
    return C

def matmul(A,B):
    return [[sum(A[r][k]*B[k][c] for k in range(3)) for c in range(3)] for r in range(3)]

def matvec(A,v):
    return [sum(A[r][k]*v[k] for k in range(3)) for r in range(3)]

def vp_int(n,p):
    if n==0: return 10**9
    v=0
    n=abs(n)
    while n%p==0:
        n//=p; v+=1
    return v

def vp_mat(M,p):
    return min(vp_int(M[r][c],p) for r in range(3) for c in range(3))

def vp_vec(v,p):
    return min(vp_int(x,p) for x in v)

def rank_mod_p(M,p):
    # Gaussian elimination over F_p, exact
    A=[[M[r][c]%p for c in range(3)] for r in range(3)]
    rank=0; row=0
    for col in range(3):
        piv=None
        for r in range(row,3):
            if A[r][col]%p!=0: piv=r; break
        if piv is None: continue
        A[row],A[piv]=A[piv],A[row]
        inv=pow(A[row][col],p-2,p)
        A[row]=[(x*inv)%p for x in A[row]]
        for r in range(3):
            if r!=row and A[r][col]%p!=0:
                f=A[r][col]
                A[r]=[(A[r][c]-f*A[row][c])%p for c in range(3)]
        row+=1; rank+=1
    return rank

def primitive(M,p):
    a=vp_mat(M,p)
    U=[[M[r][c]//(p**a) for c in range(3)] for r in range(3)]
    return a,U

def rot_angle(M, r):
    # O = M/r ; rotation trace = 1 + 2 cos(theta) (basis-independent trace)
    tr = F(sum(M[k][k] for k in range(3)), r)
    cos = (tr - 1)/2
    return cos  # exact Fraction

def niven_irrational(cos):
    # theta/pi irrational unless cos in {0,+-1/2,+-1}
    special = {F(0), F(1,2), F(-1,2), F(1), F(-1)}
    return cos not in special

# ---------- excess p-valuation instrument (absorbing vs decaying) ----------
def excess_valuation_slope(M, p, gens=8, trials=200, seed=0):
    """
    Collinearity vector Omega transforms as Omega(M.)=cof(M).Omega.
    After g descents: cof^g . Omega.  a = vp_mat(cof).
    Excess valuation E(g) = vp_vec(cof^g Omega) - a*g.
    Absorbing  <=> primitive part U=cof/p^a invertible mod p
               <=> E(g)=0 for all primitive Omega (separation preserved, PLATEAU).
    Decaying   <=> U rank-deficient mod p  =>  E(g) grows  (normalized sep -> 0).
    Returns max excess at final gen over random primitive Omega, and per-gen mean.
    """
    C = cof3(M)
    a = vp_mat(C,p)
    rnd = random.Random(seed)
    maxE = [0]*(gens+1)
    for _ in range(trials):
        # random primitive collinearity vector (mod p nonzero)
        while True:
            v=[rnd.randint(-20,20) for _ in range(3)]
            if vp_vec(v,p)==0: break
        w=v[:]
        for g in range(1,gens+1):
            w=matvec(C,w)
            E=vp_vec(w,p)-a*g
            if E>maxE[g]: maxE[g]=E
    return a, maxE

def report(name, M, r, p):
    print("="*70)
    print(f"{name}   M={M}   det={det3(M)}  (r={r}, ratio^2={r*r})  p={p}")
    C=cof3(M)
    print(f"  cof(M) = {C}")
    print(f"  det(cof)={det3(C)}  (= det(M)^2 = {det3(M)**2})")
    a,U=primitive(C,p)
    print(f"  cof = p^{a} * U,   U={U}")
    print(f"  a=vp(cof)={a},   2*vp_p(r)={2*vp_int(r,p)}   -> need a==2vp(r) for full rank")
    ru=rank_mod_p(U,p)
    print(f"  rank(U mod {p}) = {ru}   ({'FULL-RANK / INVERTIBLE -> ABSORBING' if ru==3 else 'DEFICIENT -> DECAYING (M_BAL3 failure)'})")
    print(f"  rank(M mod {p}) = {rank_mod_p(M,p)}  (should match primitive-cof rank: p-adic conjugacy)")
    cos=rot_angle(M,r)
    print(f"  twist: cos(theta)={cos}  irrational-angle(Niven)={niven_irrational(cos)}")
    a2,maxE=excess_valuation_slope(M,p)
    print(f"  excess-valuation E(g)=vp(cof^g Omega)-a*g  (max over 200 primitive Omega):")
    print(f"    {maxE}")
    slope = "~0 (PLATEAU, absorbing)" if maxE[-1]==0 else f">0 (DECAY, slope~{maxE[-1]/8:.2f}/gen)"
    print(f"  => normalized-separation behaviour: {slope}")
    return dict(a=a,rankU=ru,rankM=rank_mod_p(M,p),cos=str(cos),irr=niven_irrational(cos),maxE=maxE)

if __name__=="__main__":
    results={}
    # M_BAL3 baseline
    Mbal3=[[3,0,0],[0,0,-3],[0,3,-1]]
    results['M_BAL3']=report("M_BAL3 (r=3, prime-power)", Mbal3, 3, 3)

    # Candidate A: integer similarity ratio 5, irrational z-twist arctan(4/3)
    A=[[3,-4,0],[4,3,0],[0,0,5]]
    results['A_ratio5']=report("A = ratio-5 twist (screen at p=2, coprime to twist)", A, 5, 2)

    # Candidate M' = 2*A : homothety(2) x twist(ratio 5), r=10=2*5, screen at p=2
    Mp=[[6,-8,0],[8,6,0],[0,0,10]]
    results['Mprime_2A']=report("M' = 2*A (r=10=2.5), screen at p=2 (pure-homothety carrier)", Mp, 10, 2)

    # Counter-check: try to screen the SAME M' at p=5 (a prime dividing the TWIST) -> should FAIL
    results['Mprime_2A_at5']=report("M' = 2*A screened at p=5 (twist prime) -- expect FAILURE", Mp, 10, 5)

    print("\n" + "#"*70)
    print("SUMMARY (day-3 screen = rank(U mod p)==3):")
    for k,v in results.items():
        print(f"  {k:16s}: a={v['a']} rank(U)={v['rankU']} rank(M)={v['rankM']} "
              f"irr-twist={v['irr']} maxE={v['maxE'][-1]}  "
              f"{'PASS' if v['rankU']==3 else 'FAIL'}")
