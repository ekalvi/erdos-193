"""
Final comparison table. Separation instrument = excess p-valuation
E(g)=vp(cof^g.Omega)-a*g over 300 random primitive Omega, at EVERY prime|r.
E(g)==0 => normalized separation PLATEAU (absorbing). E(g)>0 => DECAY (M_BAL3 failure).
The candidate's TRUE behaviour = the WORST prime dividing r.
"""
from fractions import Fraction as F
from math import gcd
import random
def cof3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return [[ (e*i-f*h), -(d*i-f*g),  (d*h-e*g)],
            [-(b*i-c*h),  (a*i-c*g), -(a*h-b*g)],
            [ (b*f-c*e), -(a*f-c*d),  (a*e-b*d)]]
def det3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
def matvec(A,v): return [sum(A[r][k]*v[k] for k in range(3)) for r in range(3)]
def vp_int(n,p):
    if n==0: return 10**9
    v=0; n=abs(n)
    while n%p==0: n//=p; v+=1
    return v
def vp_mat(M,p): return min(vp_int(M[r][c],p) for r in range(3) for c in range(3))
def vp_vec(v,p): return min(vp_int(x,p) for x in v)
def rank_mod_p(M,p):
    A=[[M[r][c]%p for c in range(3)] for r in range(3)]
    rank=0;row=0
    for col in range(3):
        piv=None
        for r in range(row,3):
            if A[r][col]%p!=0: piv=r;break
        if piv is None: continue
        A[row],A[piv]=A[piv],A[row]
        inv=pow(A[row][col],p-2,p)
        A[row]=[(x*inv)%p for x in A[row]]
        for r in range(3):
            if r!=row and A[r][col]%p!=0:
                fac=A[r][col];A[r]=[(A[r][c]-fac*A[row][c])%p for c in range(3)]
        row+=1;rank+=1
    return rank
def prime_factors(n):
    n=abs(n);fs=set();d=2
    while d*d<=n:
        while n%d==0: fs.add(d);n//=d
        d+=1
    if n>1: fs.add(n)
    return sorted(fs)
def rot_cos(M,r):
    tr=F(sum(M[k][k] for k in range(3)),r);return (tr-1)/2
def niven_irr(cos): return cos not in {F(0),F(1,2),F(-1,2),F(1),F(-1)}

def Eg(M,p,gens=6,trials=300,seed=0):
    C=cof3(M);a=vp_mat(C,p);rnd=random.Random(seed);maxE=[0]*(gens+1)
    for _ in range(trials):
        while True:
            v=[rnd.randint(-30,30) for _ in range(3)]
            if vp_vec(v,p)==0: break
        w=v[:]
        for g in range(1,gens+1):
            w=matvec(C,w);E=vp_vec(w,p)-a*g
            if E>maxE[g]: maxE[g]=E
    return a,maxE

def row(name,M,r):
    cos=rot_cos(M,r);primes=prime_factors(r)
    perprime=[]
    worst_decay=False
    for p in primes:
        a,mE=Eg(M,p)
        ru=rank_mod_p([[cof3(M)[i][j]//(p**vp_mat(cof3(M),p)) for j in range(3)] for i in range(3)],p)
        dec = mE[-1]>0
        worst_decay=worst_decay or dec
        perprime.append((p,ru,a,mE[-1],'DECAY' if dec else 'plateau'))
    dim="n/a"
    print(f"\n{name}")
    print(f"  M={M} det={det3(M)} r={r}  twist cos={cos} irr={niven_irr(cos)}")
    for p,ru,a,me,tag in perprime:
        print(f"    p={p}: rank(U mod p)={ru}  a={a}  E(g=6)={me}  -> {tag}")
    print(f"  OVERALL (worst prime): {'DECAY = same failure as M_BAL3' if worst_decay else 'PLATEAU absorbing'}")
    return worst_decay

print("#### COMPARISON TABLE: separation instrument at ALL primes dividing r ####")
row("M_BAL3 baseline", [[3,0,0],[0,0,-3],[0,3,-1]], 3)
row("M'=2A  (search agent headline 'escape', r=10)", [[6,-8,0],[8,6,0],[0,0,10]], 10)
row("A ratio5 bare (r=5)", [[3,-4,0],[4,3,0],[0,0,5]], 5)
row("2*(5,12,13) (r=26)", [[10,-24,0],[24,10,0],[0,0,26]], 26)
row("CONTROL rational-twist 3*(90deg rot) SNF=rI (r=3)", [[0,-3,0],[3,0,0],[0,0,3]], 3)
