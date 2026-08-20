"""
INDEPENDENT ALGEBRAIC ANGLE (cross-check of the search agent).
Key question the design flagged in risk (2) but never resolved:
the day-screen must PASS AT EVERY PRIME DIVIDING r.
Test each candidate at ALL primes p|r, and test the Smith-Normal-Form
impossibility theorem. Exact integer arithmetic only.
"""
from fractions import Fraction as F
from math import gcd

def det3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
def cof3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return [[ (e*i-f*h), -(d*i-f*g),  (d*h-e*g)],
            [-(b*i-c*h),  (a*i-c*g), -(a*h-b*g)],
            [ (b*f-c*e), -(a*f-c*d),  (a*e-b*d)]]
def vp_int(n,p):
    if n==0: return 10**9
    v=0; n=abs(n)
    while n%p==0: n//=p; v+=1
    return v
def vp_mat(M,p): return min(vp_int(M[r][c],p) for r in range(3) for c in range(3))
def rank_mod_p(M,p):
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
                fac=A[r][col]; A[r]=[(A[r][c]-fac*A[row][c])%p for c in range(3)]
        row+=1; rank+=1
    return rank
def prime_factors(n):
    n=abs(n); fs=set(); d=2
    while d*d<=n:
        while n%d==0: fs.add(d); n//=d
        d+=1
    if n>1: fs.add(n)
    return sorted(fs)

def smith_normal_form(M):
    # exact integer SNF diagonal (invariant factors) of 3x3
    A=[[M[r][c] for c in range(3)] for r in range(3)]
    n=3
    def minor_gcds(A):
        # gcd of all k-minors gives product of first k invariant factors
        import itertools
        d=[0]*(n+1); d[0]=1
        # 1-minors
        g=0
        for r in range(n):
            for c in range(n):
                g=gcd(g,A[r][c])
        d[1]=g
        # 2-minors
        g=0
        rows=[0,1,2]
        import itertools as it
        for rs in it.combinations(range(n),2):
            for cs in it.combinations(range(n),2):
                m=A[rs[0]][cs[0]]*A[rs[1]][cs[1]]-A[rs[0]][cs[1]]*A[rs[1]][cs[0]]
                g=gcd(g,m)
        d[2]=g
        d[3]=abs(det3(A))
        return d
    d=minor_gcds(A)
    s=[0,0,0]
    s[0]=d[1]
    s[1]=d[2]//d[1] if d[1]!=0 else 0
    s[2]=d[3]//d[2] if d[2]!=0 else 0
    return s

def rot_cos(M,r):
    tr=F(sum(M[k][k] for k in range(3)),r)
    return (tr-1)/2
def niven_irr(cos):
    return cos not in {F(0),F(1,2),F(-1,2),F(1),F(-1)}

def screen_all_primes(name, M, r):
    print("="*72)
    print(f"{name}")
    print(f"  M={M}  det={det3(M)}  r={r}")
    C=cof3(M)
    cos=rot_cos(M,r)
    print(f"  twist cos={cos}  irrational(Niven)={niven_irr(cos)}")
    snf=smith_normal_form(M)
    print(f"  SNF invariant factors of M = {snf}   (r*I would be [{r},{r},{r}])")
    is_rI = snf==[r,r,r]
    primes=prime_factors(r)
    print(f"  primes dividing r: {primes}")
    overall=True
    for p in primes:
        k=vp_int(r,p)
        a=vp_mat(C,p)
        Up=[[C[i][j]//(p**a) for j in range(3)] for i in range(3)]
        ru=rank_mod_p(Up,p)
        ok = (ru==3)
        overall = overall and ok
        print(f"    p={p} (k={k}): a=vp(cof)={a} (need 2k={2*k}), rank(U mod {p})={ru} -> {'PASS' if ok else 'FAIL'}")
    print(f"  ==> DAY-SCREEN AT ALL PRIMES: {'PASS' if overall else 'FAIL'};  SNF==rI: {is_rI}")
    # theorem cross-check: overall-pass <=> SNF==rI <=> M/r integer
    Mr_integer = all((M[i][j]%r==0) for i in range(3) for j in range(3))
    print(f"  M/r integer? {Mr_integer}   (theorem: allpass <=> SNF=rI <=> M/r integer isometry -> finite order twist)")
    return overall, is_rI, niven_irr(cos)

print("\n########## CROSS-CHECK: screen candidates at ALL primes dividing r ##########")
# M_BAL3
screen_all_primes("M_BAL3  (r=3 prime)", [[3,0,0],[0,0,-3],[0,3,-1]], 3)
# the search agent's headline escape:
screen_all_primes("M'=2A (r=10=2.5) -- search agent's PASS claim (single prime p=2 only)",
                  [[6,-8,0],[8,6,0],[0,0,10]], 10)
# Pure homothety times bare Pythagorean, other members
screen_all_primes("A ratio5 (r=5 prime) bare", [[3,-4,0],[4,3,0],[0,0,5]], 5)
screen_all_primes("3A (r=15=3.5)", [[9,-12,0],[12,9,0],[0,0,15]], 15)
screen_all_primes("M'=2*(5,12,13) (r=26=2.13)", [[10,-24,0],[24,10,0],[0,0,26]], 26)
