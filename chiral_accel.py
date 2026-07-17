"""
ERDOS #193 -- ACCELERATING (equal-moduli) MATRIX + CHIRAL MENU.
Concrete integer candidates + pypy sanity checks.

Sections:
  A. geometry primitives (exact integer collinearity, general n)
  B. rigorous chirality test (orthogonal-automorphism group of a vector set)
  C. lattice-span / generation test (gcd of maximal minors)
  D. accelerating equal-moduli matrices: char poly (Faddeev-LeVerrier, exact),
     roots (Durand-Kerner), moduli, power-boundedness (non-flattening)
  E. helical bridge builder + triple-free check (T2 proof-of-concept)
  F. accelerating spiral vs constant-radius helix (why acceleration is required)
"""
from __future__ import annotations
from fractions import Fraction as F
from math import gcd, cos, sin, hypot, pi
from itertools import combinations, permutations
import cmath, random

# ---------------------------------------------------------------- A. geometry
def vsub(a, b): return tuple(x - y for x, y in zip(a, b))
def vadd(a, b): return tuple(x + y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))

def collinear(a, b, c):
    """Exact: are points a,b,c collinear in Z^n?  (rank[b-a, c-a] <= 1)."""
    u, v = vsub(b, a), vsub(c, a)
    n = len(a)
    for i in range(n):
        for j in range(i + 1, n):
            if u[i] * v[j] - u[j] * v[i] != 0:
                return False
    return True

def prim_dir(v):
    g = 0
    for c in v: g = gcd(g, abs(c))
    if g == 0: return v
    w = tuple(c // g for c in v)
    for c in w:
        if c:
            if c < 0: w = tuple(-x for x in w)
            break
    return w

def legal(points, p):
    """p legal against existing points iff no earlier pair is collinear with p."""
    seen = set()
    for q in points:
        d = prim_dir(vsub(q, p))
        if d in seen: return False
        seen.add(d)
    return True

def first_triple(points):
    """Return first (i,j,k) collinear triple or None. O(m^2) incremental."""
    for k in range(len(points)):
        seen = {}
        for j in range(k):
            d = prim_dir(vsub(points[j], points[k]))
            if d in seen:
                return (seen[d], j, k)
            seen[d] = j
    return None

# --------------------------------------------------- B. rigorous chirality
def orthogonal_automorphisms(S):
    """
    All linear isometries O (over Q) with O(S)=S, for a spanning finite set
    S subset Z^n.  Returns list of (matrix-as-tuple-of-rows-of-Fraction, det).
    Method: O is determined by images of an independent spanning subset B;
    each image must lie in S with matching Gram data; solve O exactly, then
    verify O(S)=S set-equality and O^T O = I.
    """
    n = len(S[0])
    Svec = [tuple(F(x) for x in s) for s in S]
    Sset = set(S)
    # pick independent subset B (indices)
    B = []
    basis_rows = []
    for i, s in enumerate(Svec):
        cand = basis_rows + [s]
        if rank_frac(cand) == len(cand):
            B.append(i); basis_rows.append(s)
            if len(B) == n: break
    if len(B) != n:
        raise ValueError("S does not span R^n")
    Bmat = [Svec[i] for i in B]                       # rows = basis vectors
    Binv = mat_inv(Bmat)                              # (B as columns)^-1 ... careful
    gramB = [[dot(S[i], S[j]) for j in B] for i in B]
    autos = []
    # choose images: ordered n-tuple of distinct S-vectors matching gramB
    def compatible(images):
        m = len(images)
        for a in range(m):
            for b in range(m):
                if dot(S[images[a]], S[images[b]]) != gramB[a][b]:
                    return False
        return True
    def rec(images):
        if len(images) == n:
            # O maps basis vector B[t] -> S[images[t]].
            # Build O: columns? We have O * Bmat_col = Img_col  => O = Img * Bmat^{-1}
            O = build_map([Svec[B[t]] for t in range(n)],
                          [Svec[images[t]] for t in range(n)])
            if O is None: return
            # verify O(S)=S
            ok = True
            for s in S:
                im = matvec(O, tuple(F(x) for x in s))
                imt = tuple(int(x) if x.denominator == 1 else None for x in im)
                if None in imt or imt not in Sset:
                    ok = False; break
            if ok:
                autos.append((O, det_frac(O)))
            return
        t = len(images)
        for i in range(len(S)):
            images.append(i)
            if compatible(images):
                rec(images)
            images.pop()
    rec([])
    # dedup by matrix
    uniq = {}
    for O, d in autos:
        key = tuple(tuple(x for x in row) for row in O)
        uniq[key] = d
    return list(uniq.items())

def rank_frac(rows):
    rows = [list(r) for r in rows]
    rows = [[F(x) for x in r] for r in rows]
    n = len(rows);
    if n == 0: return 0
    m = len(rows[0]); rank = 0; col = 0
    r = 0
    while r < n and col < m:
        piv = None
        for i in range(r, n):
            if rows[i][col] != 0: piv = i; break
        if piv is None: col += 1; continue
        rows[r], rows[piv] = rows[piv], rows[r]
        pv = rows[r][col]
        rows[r] = [x / pv for x in rows[r]]
        for i in range(n):
            if i != r and rows[i][col] != 0:
                f = rows[i][col]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        r += 1; col += 1; rank += 1
    return rank

def build_map(src, dst):
    """Return linear O (rows of Fraction) with O*src[t] = dst[t] for all t.
    src are n independent column vectors."""
    n = len(src)
    # Solve O: O = D * S^{-1} where S has src as columns, D has dst as columns.
    Scol = [[src[t][i] for t in range(n)] for i in range(n)]  # matrix, entry [i][t]
    Sinv = mat_inv(Scol)
    if Sinv is None: return None
    Dcol = [[dst[t][i] for t in range(n)] for i in range(n)]
    O = matmul(Dcol, Sinv)
    return O

def mat_inv(M):
    n = len(M)
    A = [[F(M[i][j]) for j in range(n)] + [F(1) if i == j else F(0) for j in range(n)]
         for i in range(n)]
    for col in range(n):
        piv = None
        for i in range(col, n):
            if A[i][col] != 0: piv = i; break
        if piv is None: return None
        A[col], A[piv] = A[piv], A[col]
        pv = A[col][col]
        A[col] = [x / pv for x in A[col]]
        for i in range(n):
            if i != col and A[i][col] != 0:
                f = A[i][col]
                A[i] = [a - f * b for a, b in zip(A[i], A[col])]
    return [row[n:] for row in A]

def matmul(A, B):
    n = len(A); m = len(B[0]); k = len(B)
    return [[sum(F(A[i][t]) * F(B[t][j]) for t in range(k)) for j in range(m)]
            for i in range(n)]

def matvec(M, v):
    return tuple(sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M)))

def det_frac(M):
    n = len(M); A = [[F(x) for x in row] for row in M]; det = F(1)
    for col in range(n):
        piv = None
        for i in range(col, n):
            if A[i][col] != 0: piv = i; break
        if piv is None: return F(0)
        if piv != col: A[col], A[piv] = A[piv], A[col]; det = -det
        det *= A[col][col]
        inv = A[col][col]
        A[col] = [x / inv for x in A[col]]
        for i in range(col + 1, n):
            if A[i][col] != 0:
                f = A[i][col]
                A[i] = [a - f * b for a, b in zip(A[i], A[col])]
    return det

def is_chiral(S):
    autos = orthogonal_automorphisms(S)
    dets = [d for _, d in autos]
    has_improper = any(d == -1 for d in dets)
    return (not has_improper), len(autos), dets

def negation_closed(S):
    Sset = set(S)
    return all(tuple(-x for x in s) in Sset for s in S)

def handedness_chi(S):
    """Ordered signed sum of 3x3 dets (n=3): nonzero => not coplanar + a sign."""
    tot = 0
    for a, b, c in combinations(S, 3):
        tot += (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0])
                + a[2]*(b[0]*c[1]-b[1]*c[0]))
    return tot

# --------------------------------------------------- C. lattice generation
def minors_gcd(S):
    """gcd of all n x n minors of the matrix whose rows are S; ==1 iff S
    generates Z^n as a group."""
    n = len(S[0]); g = 0
    for combo in combinations(S, n):
        g = gcd(g, abs(int(det_frac([list(r) for r in combo]))))
    return g

# --------------------------------------------------- D. matrices
def charpoly(M):
    """Faddeev-LeVerrier: integer char poly coeffs [c0..cn], p(x)=sum c_i x^i."""
    n = len(M)
    Mf = [[F(M[i][j]) for j in range(n)] for i in range(n)]
    I = [[F(1) if i == j else F(0) for j in range(n)] for i in range(n)]
    Mk = [row[:] for row in I]  # M^0
    c = [F(0)] * (n + 1)
    c[n] = F(1)
    Mprev = I
    for k in range(1, n + 1):
        Mk = matmul(Mf, Mprev)
        tr = sum(Mk[i][i] for i in range(n))
        ck = -tr / k
        c[n - k] = ck
        Mprev = [[Mk[i][j] + (ck if i == j else 0) for j in range(n)] for i in range(n)]
    return [int(x) for x in c]  # x^0 .. x^n

def durand_kerner(coeffs):
    """Roots of poly given low->high coeffs. Returns complex roots."""
    # normalize monic, high->low
    c = coeffs[:]
    while len(c) > 1 and c[-1] == 0: c.pop()
    deg = len(c) - 1
    lead = c[-1]
    a = [ci / lead for ci in c]  # low->high monic
    def p(x):
        r = 0j
        for ci in reversed(a): r = r * x + ci
        return r
    roots = [cmath.exp(2j * pi * k / deg) * (0.4 + 0.9j) for k in range(deg)]
    for _ in range(500):
        new = []
        for i in range(deg):
            num = p(roots[i])
            den = 1 + 0j
            for j in range(deg):
                if j != i: den *= (roots[i] - roots[j])
            new.append(roots[i] - num / den)
        if max(abs(new[i] - roots[i]) for i in range(deg)) < 1e-14:
            roots = new; break
        roots = new
    return roots

def matpow_scaled_norm(M, r, T):
    """max abs entry of (M/r)^t for t=1..T (float). Bounded => semisimple/no-flatten."""
    n = len(M)
    A = [[M[i][j] / r for j in range(n)] for i in range(n)]
    cur = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    mx = 0.0
    for t in range(1, T + 1):
        cur = [[sum(A[i][k] * cur[k][j] for k in range(n)) for j in range(n)]
               for i in range(n)]
        mx = max(mx, max(abs(cur[i][j]) for i in range(n) for j in range(n)))
    return mx

# accelerating n=3 family (block: axis a_k ; rotation modulus a_k, irrational angle)
def M3(a, b=1):
    return [[a, 0, 0], [0, 0, -a * a], [0, 1, -b]]

# coupled (non-block) version via unimodular conjugation
U3 = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
U3inv = [[1, -1, 1], [0, 1, -1], [0, 0, 1]]
def M3_coupled(a, b=1):
    Mf = matmul(matmul(U3, M3(a, b)), U3inv)
    return [[int(x) for x in row] for row in Mf]

# accelerating n=4 double-rotation (two irrational angles, no invariant line)
def M4(a, b, c):
    return [[0, -a * a, 0, 0], [1, -b, 0, 0], [0, 0, 0, -a * a], [0, 0, 1, -c]]

def block2_angle_ok(a, b):
    """companion x^2+bx+a^2: complex (disc<0) and irrational angle (Niven)."""
    if b * b - 4 * a * a >= 0: return False
    cth = F(-b, 2 * a)
    return cth not in (F(0), F(1, 2), F(-1, 2), F(1), F(-1))

# --------------------------------------------------- E. helical bridge (T2)
def helical_bridge(g, menu, radius, turns, seed=0, node_budget=400000):
    """
    Build a triple-free lattice path 0 -> g whose shape tracks an ideal helix
    with axis g, given radius and number of turns, using ONLY menu steps.
    Greedy (pick menu step closest to ideal helix tangent that stays legal),
    with limited backtracking. Returns (points, ok, reached_g).
    """
    n = len(g)
    glen = hypot(*[float(x) for x in g])
    ax = [x / glen for x in g]
    # orthonormal frame u,w perpendicular to axis
    e = [1.0] + [0.0] * (n - 1)
    if abs(dot(e, ax)) > 0.9: e = [0.0, 1.0] + [0.0] * (n - 2)
    u = [e[i] - dot(e, ax) * ax[i] for i in range(n)]
    un = hypot(*u); u = [x / un for x in u]
    # w = axis x u  (n=3); for n>3 use Gram-Schmidt on another e
    if n == 3:
        w = [ax[1]*u[2]-ax[2]*u[1], ax[2]*u[0]-ax[0]*u[2], ax[0]*u[1]-ax[1]*u[0]]
    else:
        e2 = [0.0, 0.0, 1.0] + [0.0]*(n-3)
        w = [e2[i]-dot(e2,ax)*ax[i]-dot(e2,u)*u[i] for i in range(n)]
        wn = hypot(*w); w = [x/wn for x in w]
    def ideal(t):  # t in [0,1]
        ang = 2 * pi * turns * t
        rad = radius
        return [t * g[i] + rad * (cos(ang) * u[i] + sin(ang) * w[i]) for i in range(n)]
    points = [tuple(0 for _ in range(n))]
    pset = {points[0]}
    # estimate steps: total path length ~ sqrt(glen^2 + (2pi turns radius)^2)
    est = int((glen + 2 * pi * turns * radius) / (sum(hypot(*[float(x) for x in s]) for s in menu) / len(menu)))
    est = max(est, 8)
    rng = random.Random(seed)
    stack = [(points[0], 0)]
    nodes = 0
    L = est
    cur = points[0]
    for step_i in range(L * 3):
        nodes += 1
        if nodes > node_budget: break
        t = min(1.0, (step_i + 1) / L)
        target = ideal(t)
        # rank menu steps by how well cur+step approaches target + drift to g
        scored = []
        for s in menu:
            cand = vadd(cur, s)
            d = sum((cand[i] - target[i]) ** 2 for i in range(n))
            scored.append((d, s, cand))
        scored.sort(key=lambda z: z[0])
        placed = False
        for d, s, cand in scored[:len(menu)]:
            if cand in pset: continue
            if legal(points, cand):
                points.append(cand); pset.add(cand); cur = cand; placed = True; break
        if not placed:
            break
        if cur == tuple(g):
            break
    reached = (cur == tuple(g))
    ok = first_triple(points) is None
    return points, ok, reached

# --------------------------------------------------- F. spiral vs helix demo
def spiral_points(turns_pts, radius0, growth, pitch, angstep):
    """Integer-rounded accelerating spiral (radius grows) vs constant helix."""
    pts = []
    r = radius0
    for k in range(turns_pts):
        ang = angstep * k
        z = pitch * k
        p = (round(r * cos(ang)), round(r * sin(ang)), round(z))
        pts.append(p)
        r *= growth
    return pts
