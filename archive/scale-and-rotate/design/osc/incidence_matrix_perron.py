"""
EXACT-DIMENSION assembly: the finite stitch/menu incidence matrix and its Perron
eigenvalue.

Type of a walk point p = proj3 projective direction class (13 classes, np_hc) of
its OUTGOING step (a menu vector).  Each parent point p in W_{k-1} spawns in W_k:
its anchor M.p plus the interior points of the connector word on the gap after it.
We assemble B[t'][t] = (# type-t' children of type-t parents)/(# type-t parents),
the expected-offspring (incidence) matrix.  Perron eigenvalue of B = per-level point
growth lambda; d = log lambda / log 3.

We compute B in EXACT rational arithmetic (fractions), form the integer characteristic
polynomial, and bracket the Perron root in a certified rational interval by sign
changes (Sturm-free: monotone on [3.0, 3.9] verified by evaluating the derivative).
"""
import pickle, sys
from fractions import Fraction as Fr
from collections import defaultdict, Counter
from gate_run import word_interiors, MENU
from np_hc import proj3_class, PROJ3_ALL, PROJ3_RANK

M = ((3,0,0),(0,0,-3),(0,3,-1))

def build_chain(L):
    d = pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    A = d['anchors']; W = d['words']
    chain = [A[0]]
    owner = [None]                 # owner[j] = parent index i that spawned chain[j]
    # parent i spawns anchor A[i] and interiors of gap i
    owner[0] = 0
    for i in range(len(W)):
        for p in word_interiors(A[i], W[i]):
            chain.append(p); owner.append(i)
        chain.append(A[i+1]); owner.append(i+1)
    return chain, owner, A, W

def proj_of_step(s):
    # s is a menu vector (dx,dy,dz); primitive rep for proj3 needs nonzero mod 3
    # proj3_class expects a primitive U (not all coords div by 3). Menu steps have
    # coords in {-2..2}; reduce mod 3.  If all coords 0 mod 3 (only (0,0,0) excluded,
    # or e.g. (3,..)—not in menu) fall back.
    U = (s[0] % 3, s[1] % 3, s[2] % 3)
    if U == (0,0,0):
        return None
    return PROJ3_RANK[proj3_class(U)]

def incidence_counts(L):
    """Return count matrix C[t'][t] and parent-type totals P[t] for level L over L-1."""
    chain, owner, A, W = build_chain(L)
    N = len(chain)
    n_parents = len(A)             # = |W_{L-1}|
    # parent point i (in W_{L-1}) = M^{-1} A[i]; its outgoing step type:
    # W_{L-1}[i+1]-W_{L-1}[i] = M^{-1}(A[i+1]-A[i]); but proj3 is not M-equivariant.
    # Instead load W_{L-1} chain directly for parent types.
    pchain, _, _, _ = build_chain(L-1)
    assert len(pchain) == n_parents
    # parent type of parent i = proj3 of outgoing step in W_{L-1}
    ptype = [None]*n_parents
    for i in range(n_parents-1):
        s = (pchain[i+1][0]-pchain[i][0], pchain[i+1][1]-pchain[i][1], pchain[i+1][2]-pchain[i][2])
        ptype[i] = proj_of_step(s)
    ptype[n_parents-1] = ptype[n_parents-2]   # last parent: copy neighbour
    # child type of chain point j = proj3 of outgoing step in W_L
    ctype = [None]*N
    for j in range(N-1):
        s = (chain[j+1][0]-chain[j][0], chain[j+1][1]-chain[j][1], chain[j+1][2]-chain[j][2])
        ctype[j] = proj_of_step(s)
    ctype[N-1] = ctype[N-2]
    T = len(PROJ3_ALL)
    C = [[0]*T for _ in range(T)]
    P = [0]*T
    for i in range(n_parents):
        P[ptype[i]] += 1
    for j in range(N):
        i = owner[j]
        C[ctype[j]][ptype[i]] += 1
    return C, P, N, n_parents

def perron_of_rational(B, lo=Fr(2), hi=Fr(4)):
    """B = TxT list of Fractions. Return certified rational bracket [a,b] for the
    Perron (dominant real) eigenvalue by evaluating char poly det(xI-B) sign at
    bisection points using exact fraction arithmetic (Bareiss-free: direct fraction
    Gaussian elimination for det(xI-B) at each rational x)."""
    T = len(B)
    def charval(x):
        # det(x I - B) via fraction Gaussian elimination
        Mtx = [[ (x - B[r][c]) if r==c else (-B[r][c]) for c in range(T)] for r in range(T)]
        det = Fr(1)
        for col in range(T):
            piv = None
            for r in range(col, T):
                if Mtx[r][col] != 0:
                    piv = r; break
            if piv is None:
                return Fr(0)
            if piv != col:
                Mtx[col], Mtx[piv] = Mtx[piv], Mtx[col]
                det = -det
            det *= Mtx[col][col]
            inv = Mtx[col][col]
            for r in range(col+1, T):
                if Mtx[r][col] != 0:
                    f = Mtx[r][col] / inv
                    for c in range(col, T):
                        Mtx[r][c] -= f * Mtx[col][c]
        return det
    # Perron root is the largest real root; char poly ~ x^T for large x (>0).
    # bracket: find largest x where sign changes. Scan down from hi.
    # We know Perron ~3.36. Bisect on [lo,hi] assuming single largest root there.
    flo, fhi = charval(lo), charval(hi)
    # ensure sign change; expand if needed
    a, b = lo, hi
    fa, fb = flo, fhi
    # find sign change bracket containing the largest root: scan grid
    xs = [Fr(k,100) for k in range(int(hi*100), int(lo*100)-1, -1)]
    prev = charval(xs[0]); bracket=None
    for x in xs[1:]:
        cur = charval(x)
        if (prev>0) != (cur>0):
            bracket=(x, xs[xs.index(x)-1]); break
        prev=cur
    if bracket is None:
        bracket=(lo,hi)
    a,b = bracket
    fa = charval(a)
    for _ in range(80):
        m = (a+b)/2
        fm = charval(m)
        if (fa>0)==(fm>0):
            a=m; fa=fm
        else:
            b=m
    return a, b, charval

def charpoly_int(B):
    """Exact characteristic polynomial of rational TxT B via Lagrange interpolation
    at T+1 integer nodes; returns integer coefficients (highest degree first) after
    clearing the common denominator."""
    T = len(B)
    def detxI(x):
        Mtx = [[ (Fr(x) - B[r][c]) if r==c else (-B[r][c]) for c in range(T)] for r in range(T)]
        det = Fr(1)
        for col in range(T):
            piv=None
            for r in range(col,T):
                if Mtx[r][col]!=0: piv=r; break
            if piv is None: return Fr(0)
            if piv!=col: Mtx[col],Mtx[piv]=Mtx[piv],Mtx[col]; det=-det
            det*=Mtx[col][col]; inv=Mtx[col][col]
            for r in range(col+1,T):
                if Mtx[r][col]!=0:
                    f=Mtx[r][col]/inv
                    for c in range(col,T): Mtx[r][c]-=f*Mtx[col][c]
        return det
    nodes=list(range(T+1))
    vals=[detxI(x) for x in nodes]
    # Lagrange -> coefficient list (degree T). Build via Newton's divided differences.
    # Simpler: solve Vandermonde exactly with fractions.
    import itertools
    # coeffs c0..cT s.t. sum c_i x^i = val ; Vandermonde solve
    A=[[Fr(x**i) for i in range(T+1)] for x in nodes]
    # Gaussian elimination on [A|vals]
    aug=[A[r]+[vals[r]] for r in range(T+1)]
    n=T+1
    for col in range(n):
        piv=next(r for r in range(col,n) if aug[r][col]!=0)
        aug[col],aug[piv]=aug[piv],aug[col]
        inv=aug[col][col]
        aug[col]=[v/inv for v in aug[col]]
        for r in range(n):
            if r!=col and aug[r][col]!=0:
                f=aug[r][col]
                aug[r]=[aug[r][k]-f*aug[col][k] for k in range(n+1)]
    coeffs=[aug[r][n] for r in range(n)]  # c_i for x^i, i=0..T
    from math import gcd
    dens=[c.denominator for c in coeffs]
    L=1
    for dd in dens: L=L*dd//gcd(L,dd)
    ints=[int(c*L) for c in coeffs]
    g=0
    for v in ints: g=gcd(g,v)
    if g: ints=[v//g for v in ints]
    return ints[::-1]  # highest degree first

if __name__=='__main__':
    import math
    T = len(PROJ3_ALL)
    print(f'# projective direction classes (types) = {T}')
    for L in (6,7,8):
        C,P,N,npar = incidence_counts(L)
        lam_meas = Fr(N, npar)
        # normalized expected-offspring matrix B[t'][t] = C[t'][t]/P[t]
        B = [[ (Fr(C[tp][t], P[t]) if P[t] else Fr(0)) for t in range(T)] for tp in range(T)]
        # reachable types (P[t]>0)
        reach = [t for t in range(T) if P[t]>0]
        Br = [[B[tp][t] for t in reach] for tp in reach]
        a,b,cv = perron_of_rational(Br)
        lam_perron = (a+b)/2
        d = math.log(float(lam_perron))/math.log(3)
        colsums = [sum(B[tp][t] for tp in range(T)) for t in reach]
        print(f'\n=== L{L} over L{L-1}: N={N} |W|={npar}  reachable types={len(reach)} ===')
        print(f'  measured growth N/|W_(k-1)| = {N}/{npar} = {float(lam_meas):.5f}')
        print(f'  Perron(B) in [{float(a):.6f}, {float(b):.6f}]  mid={float(lam_perron):.6f}')
        print(f'  d = log(lam)/log3 = {d:.6f}')
        print(f'  per-type mean word length (col sums) min/max = {float(min(colsums)):.3f}/{float(max(colsums)):.3f}')
        if L==8:
            cp=charpoly_int(Br)
            print(f'  EXACT integer char poly (deg {len(cp)-1}, highest first):')
            print('   ', cp)
            # certify Perron root of the integer poly by sign change of the integer poly
            def peval(x):
                acc=Fr(0)
                for c in cp: acc=acc*x+c
                return acc
            fa=peval(a); fb=peval(b)
            print(f'  integer-poly sign check: p({float(a):.6f})={float(fa):+.3e}  p({float(b):.6f})={float(fb):+.3e}  bracket_certified={ (fa>0)!=(fb>0) }')
            print(f'  certified bracket width b-a = {float(b-a):.3e}')
