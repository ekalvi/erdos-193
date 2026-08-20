"""
ACCELERATING-INCOMMENSURATE BRACKET MEASUREMENT (Erdos #193, well-founded induction test).

Formalization tested here
-------------------------
Imbrication W_{k+1} = M_k(W_k) |_| S_k, fixed finite menu S (bridges), E = S - S.
A first-difference at outermost level J of an address (delta_0..delta_J), delta_* in E,
gives  Delta = P_J * B  where  P_J = M_J M_{J-1} ... M_1  and the NORMALIZED bracket

    B_J = delta_J + sum_{i=1}^{J} ( M_J^{-1} M_{J-1}^{-1} ... M_{J-i+1}^{-1} ) delta_{J-i}
        = delta_J + M_J^{-1}( delta_{J-1} + M_{J-1}^{-1}( delta_{J-2} + ... ) )   [Horner]

mu_J := inf over NON-TRIVIAL addresses (delta_J != 0) of |B_J|.
Step goes through iff mu_J >= c > 0 uniformly (and non-shrinking with J).

FIXED baseline  M_k == M_BAL3 = [[3,0,0],[0,0,-3],[0,3,-1]]  is RESONANT:
M(1,0,0)=(3,0,0) in E  =>  delta_J=(-1,0,0), M^{-1}delta_{J-1}=(1,0,0) with delta_{J-1}=(3,0,0)
=> B=0 exact => mu = 0.  (c=0, refuted.)

ACCELERATING: M_k = M3(a_k), a_k strictly increasing.  M_k inflates any nonzero integer
vector by ~a_k, so for a_k large  M_k(e) leaves the fixed box E  => depth-1 resonance dies;
tail contracts by 1/a per level => mu_J -> (leading-digit floor) as J grows.

Sections:
  1. moduli + irrational-distinct-angle verification (M3(a) family, M4 double-rotation)
  2. resonance check: is M_k(e) in E for some nonzero e in E?  (the c=0 trigger)
  3. bracket min |B_J| via exact branch-and-bound, accel vs fixed baseline, vs depth.
"""
from fractions import Fraction as F
from math import gcd, hypot, cos, acos
from itertools import product
import cmath, json, time

# ---------- linear algebra ----------
def matmul(A,B):
    n=len(A); return [[sum(A[i][k]*B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def matvec(A,v):
    n=len(A); return tuple(sum(A[i][k]*v[k] for k in range(n)) for i in range(n))
def charpoly(A):
    # Faddeev-LeVerrier, exact integer/Fraction coeffs; returns [1, c1,...,cn]
    n=len(A); I=[[F(i==j) for j in range(n)] for i in range(n)]
    M=[[F(0)]*n for _ in range(n)]; c=[F(1)]; Ak=[row[:] for row in I]
    Mk=I
    for k in range(1,n+1):
        Ak=matmul([[F(x) for x in r] for r in A], Mk)
        ck=-F(1,k)*sum(Ak[i][i] for i in range(n))
        c.append(ck)
        Mk=[[Ak[i][j]+(ck if i==j else 0) for j in range(n)] for i in range(n)]
    return c
def poly_roots(coeffs):
    # Durand-Kerner on monic poly given [1,c1,...,cn] (Fraction) -> complex roots
    cs=[complex(float(x)) for x in coeffs]; n=len(cs)-1
    roots=[cmath.exp(2j*cmath.pi*k/n)*(0.4+0.9j) for k in range(n)]
    def ev(z):
        r=cs[0]
        for a in cs[1:]: r=r*z+a
        return r
    for _ in range(2000):
        new=[]
        for i in range(n):
            num=ev(roots[i]); den=1+0j
            for j in range(n):
                if j!=i: den*=(roots[i]-roots[j])
            new.append(roots[i]-num/den)
        if max(abs(new[i]-roots[i]) for i in range(n))<1e-14: roots=new; break
        roots=new
    return roots

# ---------- families ----------
def M3(a,b=1): return [[a,0,0],[0,0,-a*a],[0,1,-b]]
def M4(a,b,c): return [[0,-a*a,0,0],[1,-b,0,0],[0,0,0,-a*a],[0,0,1,-c]]

def M3inv_frac(a,b,v):
    # inverse of M3(a,b) applied to integer vector v -> tuple of Fractions
    # M3 = [[a,0,0],[0,0,-a^2],[0,1,-b]]; det = a * (0*(-b) - (-a^2)*1) = a*a^2 = a^3
    x,y,z=v
    # row-solve: a*X = x -> X=x/a ; block [[0,-a^2],[1,-b]] [Y,Z]^T=[y,z]^T
    # 0*Y -a^2 Z = y -> Z=-y/a^2 ; Y -b Z = z -> Y = z + b*Z = z - b*y/a^2
    X=F(x,a); Z=F(-y,a*a); Y=z+b*Z
    return (X,Y,Z)

def niven_irrational(cth):
    # cos in {0,+-1/2,+-1} are the only rational cos of rational-angle multiples (Niven)
    return cth not in (F(0),F(1,2),F(-1,2),F(1),F(-1))

def report_family_M3():
    print("="*70); print("FAMILY M3(a): a=2..7  M3(a)=[[a,0,0],[0,0,-a^2],[0,1,-1]]")
    rows=[]
    angles=[]
    for a in range(2,8):
        A=M3(a); cp=charpoly(A); roots=poly_roots(cp)
        mods=sorted(abs(r) for r in roots)
        # real eigen a (from axis block), complex pair modulus a
        cth=F(-1,2*a)  # companion x^2 + x + a^2: cos = -b/(2a) = -1/(2a)
        ok=niven_irrational(cth)
        angles.append(float(acos(float(cth))))
        equal_mod = max(mods)-min(mods) < 1e-9
        rows.append((a,[round(m,4) for m in mods],equal_mod,str(cth),ok))
        print(f"  a={a}: |eig|={[round(m,3) for m in mods]}  equal_moduli={equal_mod}"
              f"  cos(theta)={cth}  irrational(Niven)={ok}")
    distinct = len(set(round(x,10) for x in angles))==len(angles)
    print(f"  angles pairwise distinct across levels: {distinct}  angles={[round(x,4) for x in angles]}")
    return {"family":"M3(a) a=2..7","rows":rows,"angles_distinct":distinct}

def report_family_M4():
    print("="*70); print("FAMILY M4(a,b,c): n=4 double-rotation, per level distinct (b,c)")
    # accelerating double rotation: two 2x2 companion blocks, both modulus a, angles differ
    combos=[(2,1,1),(3,1,2),(4,2,3),(5,1,3)]
    rows=[]
    for (a,b,c) in combos:
        A=M4(a,b,c); cp=charpoly(A); roots=poly_roots(cp)
        mods=sorted(abs(r) for r in roots)
        cth1=F(-b,2*a); cth2=F(-c,2*a)
        ok1=niven_irrational(cth1); ok2=niven_irrational(cth2)
        equal_mod = max(mods)-min(mods) < 1e-9
        distinct_pair = cth1!=cth2
        rows.append((a,b,c,[round(m,4) for m in mods],equal_mod,str(cth1),str(cth2),ok1,ok2,distinct_pair))
        print(f"  (a,b,c)=({a},{b},{c}): |eig|={[round(m,3) for m in mods]} equal_mod={equal_mod}"
              f"  cos1={cth1}(irr={ok1}) cos2={cth2}(irr={ok2}) two_distinct_angles={distinct_pair}")
    return {"family":"M4 double-rotation","rows":rows}

# ---------- resonance check ----------
def resonance_check(Efn_desc, E, maps, labels):
    """For each map M_k in maps: does exist nonzero e in E with M_k(e) in E? (c=0 trigger)."""
    print("="*70); print(f"RESONANCE CHECK  M_k(e) in E ?   (E = {Efn_desc}, |E\\0|={len(E)-1})")
    Eset=set(E)
    out=[]
    for lab,Mk in zip(labels,maps):
        hits=[]
        for e in E:
            if e==(0,)*len(e): continue
            if matvec(Mk,e) in Eset:
                hits.append((e,matvec(Mk,e)))
                if len(hits)>=3: break
        res=(lab,len(hits),hits[:3])
        out.append(res)
        status = "RESONANT (c=0 possible)" if hits else "non-resonant"
        print(f"  {lab}: {status}"+(f"  e.g. {hits[0][0]}->{hits[0][1]}" if hits else ""))
    return out

# ---------- bracket min via branch and bound ----------
def bracket_min_accel(E, a_seq, J, metric="euc"):
    """
    min |B_J| over delta_J!=0, delta_{J-i} in E, using M3(a_seq[level]) per level.
    Horner:  B = delta_J + Minv_{a_J}( delta_{J-1} + Minv_{a_{J-1}}( ... delta_0 ) ).
    Exact Fractions. Branch and bound: build from the DEEPEST digit outward is awkward;
    instead enumerate outer digits with a tail-magnitude bound to prune.
    We compute an exact lower bound by full search over a REDUCED E (small box) for tractability.
    a_seq[level] is the modulus used at that level (level J outermost).
    """
    def nrm(v):
        if metric=="euc": return sum(float(x)*float(x) for x in v)**0.5
        return max(abs(float(x)) for x in v)
    # tail bound: max |Minv chain| of remaining digits. |Minv_a v|_euc <= C(a)*|v|/a with
    # condition number C; use crude C=3 upper factor to be safe for pruning (not for the value).
    maxE=max(nrm(e) for e in E)
    best=[float("inf")]; bestaddr=[None]
    # precompute per-level tail cap: sum_{i>=1} maxE / prod(a) with condition slack
    def tailcap(level):
        # levels below 'level' (i.e. level-1 .. 0), each Minv contracts by ~1/a with slack kappa
        kappa=3.0  # conservative condition-number slack per level (M3 not orthonormal)
        s=0.0; scale=1.0
        for lv in range(level-1,-1,-1):
            scale*=kappa/max(a_seq[lv],1)
            s+=maxE*scale
        return s
    # DFS from outer (level J) inward. State: current partial value as Fractions at "outer frame".
    # B = delta_J + Minv_{a_J}( X ) where X is the inner bracket at level J-1.
    # We accumulate: value(level, inner) computed by folding; easier to accumulate a linear map.
    # Represent partial as: B = acc + T(inner), where acc is fixed Fractions, T = product of Minv applied.
    # We DFS choosing delta_level for level=J..0, maintaining running value with Horner from outside:
    #   start acc=(0,0,0), factor=Identity(rational). At each level add factor*delta_level, then factor*=Minv_{a_level}.
    n=len(E[0])
    from fractions import Fraction as Fr
    def apply_Minv(a, vec):  # vec Fractions -> Fractions, M3(a,1)
        x,y,z=vec; return (x/ a, z + (-y)/(a*a), (-y)/(a*a))  # careful: recompute
    # recompute exact M3inv for Fraction vectors, b=1
    def Minv_fr(a, vec):
        x,y,z=vec
        Z=Fr(-1,a*a)*y; Y=z+Z; X=x/a
        return (X,Y,Z)
    # factor is a 3x3 rational matrix = product Minv_{a_J} ...
    I=[[Fr(i==j) for j in range(n)] for i in range(n)]
    def matmul_fr(Ai,Bi):
        return [[sum(Ai[i][k]*Bi[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    def Minv_mat(a):
        # matrix of M3(a,1)^{-1}
        return [[Fr(1,a),Fr(0),Fr(0)],[Fr(0),Fr(0),Fr(1)],[Fr(0),Fr(-1,a*a),Fr(-1,a*a)*1]]  # placeholder
    # build exact inverse numerically-safe: solve columns
    def inv3(Mm):
        # exact 3x3 inverse of integer matrix via adjugate
        m=Mm
        det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
            -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
            +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
        cof=[[ (m[(i+1)%3][(j+1)%3]*m[(i+2)%3][(j+2)%3]-m[(i+1)%3][(j+2)%3]*m[(i+2)%3][(j+1)%3]) for j in range(3)] for i in range(3)]
        adj=[[Fr(cof[j][i],det) for j in range(3)] for i in range(3)]
        return adj
    Minvs=[inv3(M3(a_seq[lv])) for lv in range(J+1)]
    def matvec_fr(Ai,v): return tuple(sum(Ai[i][k]*v[k] for k in range(n)) for i in range(n))
    Emin_nz=min(nrm(e) for e in E if e!=(0,)*n)
    def dfs(level, acc, factor):
        # choose delta_level; add factor*delta; if level==J it must be nonzero
        # lower bound on final |B|: |acc so far restricted| ... use current acc + can't easily bound; use tailcap
        if level<0:
            v=nrm(acc)
            if v<best[0]: best[0]=v; bestaddr[0]="addr"
            return
        # prune: minimal achievable from here >= |acc| - tailcap(level+... )? acc already includes chosen outer digits.
        lb=nrm(acc)-tailcap(level+1)*1.0
        # tailcap here approximates remaining factor*delta magnitudes
        # additionally the factor norm shrinks; skip aggressive prune if lb<best
        if lb-1e-12>best[0]:
            return
        for d in E:
            if level==J and d==(0,)*n: continue
            add=matvec_fr(factor,tuple(Fr(x) for x in d))
            nacc=tuple(acc[i]+add[i] for i in range(n))
            nfactor=matmul_fr(factor,Minvs[level])
            dfs(level-1,nacc,nfactor)
    dfs(J,tuple(Fr(0) for _ in range(n)),I)
    return best[0]

def bracket_min_fixed(E, M, J, metric="euc"):
    """Fixed-map baseline: same as accel but all maps = M. Returns min |B_J| (should hit 0)."""
    from fractions import Fraction as Fr
    n=len(E[0])
    def nrm(v):
        if metric=="euc": return sum(float(x)*float(x) for x in v)**0.5
        return max(abs(float(x)) for x in v)
    def inv3(Mm):
        m=Mm
        det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
        cof=[[(m[(i+1)%3][(j+1)%3]*m[(i+2)%3][(j+2)%3]-m[(i+1)%3][(j+2)%3]*m[(i+2)%3][(j+1)%3]) for j in range(3)] for i in range(3)]
        return [[Fr(cof[j][i],det) for j in range(3)] for i in range(3)]
    Minv=inv3(M)
    def matmul_fr(Ai,Bi): return [[sum(Ai[i][k]*Bi[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    def matvec_fr(Ai,v): return tuple(sum(Ai[i][k]*v[k] for k in range(n)) for i in range(n))
    I=[[Fr(i==j) for j in range(n)] for i in range(n)]
    best=[float("inf")]
    def dfs(level,acc,factor):
        if level<0:
            v=nrm(acc);
            if v<best[0]: best[0]=v
            return
        if best[0]==0.0: return
        for d in E:
            if level==J and d==(0,)*n: continue
            add=matvec_fr(factor,tuple(Fr(x) for x in d))
            nacc=tuple(acc[i]+add[i] for i in range(n))
            dfs(level-1,nacc,matmul_fr(factor,Minv))
    dfs(J,tuple(Fr(0) for _ in range(n)),I)
    return best[0]

if __name__=="__main__":
    t0=time.time()
    r3=report_family_M3()
    r4=report_family_M4()

    # small menu-difference box for tractable exact search
    E=[v for v in product(range(-2,3),repeat=3)]  # includes 0; |E|=125
    print("\nUsing exact search box E={-2..2}^3, |E|=%d (includes 0)."%len(E))

    # resonance: fixed M_BAL3 vs accelerating M3(a)
    Mbal=[[3,0,0],[0,0,-3],[0,3,-1]]
    resonance_check("{-2..2}^3", E, [Mbal, M3(2), M3(3), M3(4), M3(5)],
                    ["M_BAL3(fixed)","M3(2)","M3(3)","M3(4)","M3(5)"])

    print("="*70); print("BRACKET min |B_J| vs depth J  (metric=euclidean, exact Fractions)",flush=True)
    # fixed baseline: expect 0 at shallow depth
    for J in [1,2]:
        mb=bracket_min_fixed(E,Mbal,J)
        print(f"  FIXED M_BAL3   J={J}: min|B_J|={mb:.6f}",flush=True)
    # accelerating: a_seq[level]; outermost level J uses largest a. Use a_seq[lv]=lv+2.
    Esmall=[v for v in product(range(-1,2),repeat=3)]  # 27, for the deep J=3 pass
    for (J,EE) in [(1,E),(2,E),(3,Esmall)]:
        aseq=[lv+2 for lv in range(J+1)]  # level 0->2,1->3,...
        ma=bracket_min_accel(EE,aseq,J)
        print(f"  ACCEL M3(a)    J={J} |E|={len(EE)} a_seq(outer->in)={[aseq[J-i] for i in range(J+1)]}: min|B_J|={ma:.6f}",flush=True)
    print(f"\n[{time.time()-t0:.1f}s] done.",flush=True)
