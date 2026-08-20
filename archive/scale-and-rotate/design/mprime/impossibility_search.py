"""
IMPOSSIBILITY THEOREM empirical seal.
Enumerate ALL integer Euclidean similarities M (M^T M = r^2 I, i.e. r*rotation,
INCLUDES axis-free 3D-mixing quaternion rotations = design family (2)).
For each with IRRATIONAL twist, verify it FAILS the day-screen at some prime|r.
Theorem: pass-all-primes <=> SNF(M)=rI <=> M/r integer <=> M/r finite-order
isometry <=> rational twist. So NO irrational-twist similarity passes all primes.
Exact integers throughout.
"""
from fractions import Fraction as F
from math import gcd, isqrt
import itertools

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
def rot_cos(M,r):
    tr=F(sum(M[k][k] for k in range(3)),r)
    return (tr-1)/2
def niven_irr(cos):
    return cos not in {F(0),F(1,2),F(-1,2),F(1),F(-1)}

def passes_all_primes(M,r):
    C=cof3(M)
    for p in prime_factors(r):
        a=vp_mat(C,p)
        U=[[C[i][j]//(p**a) for j in range(3)] for i in range(3)]
        if rank_mod_p(U,p)!=3: return False
    return True

def is_similarity(M):
    # M^T M = r^2 I  ?  columns orthonormal*r^2, equal norm
    cols=[[M[i][j] for i in range(3)] for j in range(3)]
    n0=sum(x*x for x in cols[0])
    for j in range(3):
        if sum(x*x for x in cols[j])!=n0: return None
    for a in range(3):
        for b in range(a+1,3):
            if sum(cols[a][k]*cols[b][k] for k in range(3))!=0: return None
    r2=n0; r=isqrt(r2)
    if r*r!=r2: return None
    return r

# enumerate integer similarities with small entries, all r
found_irr=0; violations=0; examples=[]
B=6
rng=range(-B,B+1)
seen=set()
# quaternion-generated rotations are dense; brute force column1 then complete is heavy.
# Instead brute-force full matrices with bounded entries but prune by column norm.
import random
rnd=random.Random(1)
# structured brute force: pick columns of equal square-norm, pairwise orthogonal
from collections import defaultdict
vecs_by_norm=defaultdict(list)
for v in itertools.product(rng,repeat=3):
    if v==(0,0,0): continue
    vecs_by_norm[sum(x*x for x in v)].append(v)

count=0
for norm,vs in vecs_by_norm.items():
    r=isqrt(norm)
    if r*r!=norm: continue
    if r<2 or r>12: continue
    if len(vs)>4000: continue  # keep it tractable
    for c0 in vs:
        for c1 in vs:
            if sum(c0[k]*c1[k] for k in range(3))!=0: continue
            # c2 must be orthogonal to both, norm=norm -> +/- cross(c0,c1)/r
            cr=(c0[1]*c1[2]-c0[2]*c1[1], c0[2]*c1[0]-c0[0]*c1[2], c0[0]*c1[1]-c0[1]*c1[0])
            # |cross| = r^2 ; need c2 = cross/r integer
            if any(x%r!=0 for x in cr): continue
            c2=tuple(x//r for x in cr)
            for sgn in (1,-1):
                cc2=tuple(sgn*x for x in c2)
                M=[[c0[i],c1[i],cc2[i]] for i in range(3)]
                if det3(M)<=0: continue
                key=tuple(map(tuple,M))
                if key in seen: continue
                seen.add(key)
                rr=is_similarity(M)
                if rr!=r: continue
                cos=rot_cos(M,r)
                if not niven_irr(cos): continue
                count+=1
                found_irr+=1
                if passes_all_primes(M,r):
                    violations+=1
                    if len(examples)<10: examples.append((M,r,str(cos)))

print(f"Enumerated integer Euclidean similarities (M^T M=r^2 I), r in 2..12, |entries|<= {B}")
print(f"  with IRRATIONAL twist: {found_irr}")
print(f"  that PASS day-screen at ALL primes dividing r: {violations}")
print(f"  (theorem predicts 0 -- any >0 would be a genuine escape)")
if examples:
    print("  EXAMPLES OF ESCAPE:")
    for M,r,cos in examples: print("   ",M,"r=",r,"cos=",cos)
else:
    print("  => NO counterexample: theorem holds across all axis-free 3D-mixing similarities searched.")

# Also confirm the converse: rational-twist similarities with SNF=rI DO pass all primes
print("\nControl: signed permutation * r (SNF=rI, rational twist) should PASS all primes:")
P=[[0,-1,0],[1,0,0],[0,0,1]]  # 90deg rotation, finite order
for r in (2,3,5,6,10):
    M=[[r*P[i][j] for j in range(3)] for i in range(3)]
    print(f"  r={r}: M/r integer, SNF=rI, passes_all_primes={passes_all_primes(M,r)}, "
          f"irr_twist={niven_irr(rot_cos(M,r))}")
