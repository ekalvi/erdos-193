"""
PAIR-LEVEL HORIZON-CONSERVATION LEMMA -- PART 1: exact cross-cylinder Omega form.

All arithmetic is EXACT INTEGER.  No floats anywhere in a collinearity test.

Establishes, by explicit code-verified identity:
  (0) M, cof(M), det, and cof(M) = 3*N with N integral (cof(M) == 0 mod 3).
  (1) L2 inheritance:  Omega(Mp,Mq,Mr) = cof(M) . Omega(p,q,r)   (exhaustive small + random).
  (2) The DIGIT DECOMPOSITION of a cross-cylinder straddling triple:
        p in C_a  (root M^g a),  q,r in C_a' (root M^g a')
        d1 = q-p,  d2 = r-p,   Omega = d1 x d2
      With  d1 = sum_{j=0..g} M^{g-j} c1_j ,  d2 = sum_{j=0..g} M^{g-j} c2_j ,
      c1_0 = c2_0 = delta = a'-a  (shared leading digit = root offset),
      c1_j = s^q_j - s^p_j,  c2_j = s^r_j - s^p_j  (stitch-offset differences),
      the EXACT identity
        Omega = sum_{l=0..g} cof(M)^{g-l} B_l ,
        B_l = c1_l x c2_l + sum_{i<l}(M^{l-i} c1_i) x c2_l + sum_{j<l} c1_l x (M^{l-j} c2_j).
      Verified == direct Omega for random g and random bounded digits.
      Consequences: B_0 = delta x delta = 0 (identically), and
        B_1 = sigma1 x tau1 + Delta x (tau1 - sigma1),  Delta = M.delta.
  (3) The deep-tail / horizon constants: min|M^j v|_inf = 3,8,24 (j=1,2,3), reach<=4.
"""
from __future__ import annotations
import random, itertools, json

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))

def matvec(A, v):
    return tuple(A[r][0]*v[0] + A[r][1]*v[1] + A[r][2]*v[2] for r in range(3))

def matmul(A, B):
    return tuple(tuple(sum(A[r][k]*B[k][c] for k in range(3)) for c in range(3)) for r in range(3))

def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
            - A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
            + A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))

def cofactor(A):
    # C_ij = (-1)^{i+j} * minor_ij
    C = [[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            rows = [r for r in range(3) if r != i]
            cols = [c for c in range(3) if c != j]
            minor = (A[rows[0]][cols[0]]*A[rows[1]][cols[1]]
                     - A[rows[0]][cols[1]]*A[rows[1]][cols[0]])
            C[i][j] = ((-1)**(i+j)) * minor
    return tuple(tuple(row) for row in C)

def Mpow(m):
    R = ((1,0,0),(0,1,0),(0,0,1))
    for _ in range(m):
        R = matmul(R, M)
    return R

results = {}
ok = True

# ---- (0) M, cof(M), det ----------------------------------------------------
COF = cofactor(M)
detM = det3(M)
detCOF = det3(COF)
print("M       =", M)
print("cof(M)  =", COF)
print("det M   =", detM, " det cof(M) =", detCOF, " (= detM^2 =", detM*detM, ")")
assert COF == ((9,0,0),(0,-3,-9),(0,9,0)), "cof(M) mismatch!"
assert detM == 27 and detCOF == 729
# cof(M) == 0 mod 3 ?  and N = cof(M)/3 integral
allmod3 = all(COF[i][j] % 3 == 0 for i in range(3) for j in range(3))
N = tuple(tuple(COF[i][j]//3 for j in range(3)) for i in range(3))
print("cof(M) == 0 mod 3 :", allmod3, "   N = cof(M)/3 =", N, " det N =", det3(N))
assert allmod3 and det3(N) == 27
results["cofM"] = COF
results["cofM_is_3N"] = {"N": N, "detN": det3(N)}
results["detM"] = detM
results["detCOF"] = detCOF

# ---- (1) L2 inheritance  Omega(Mp,Mq,Mr) = cof(M) . Omega(p,q,r) ------------
def Omega(p, q, r):
    return cross(sub(q, p), sub(r, p))

# exhaustive small grid
cnt = 0
for p in itertools.product(range(-2, 3), repeat=3):
    for q in itertools.product(range(-2, 3), repeat=3):
        for r in itertools.product(range(-1, 2), repeat=3):
            lhs = Omega(matvec(M, p), matvec(M, q), matvec(M, r))
            rhs = matvec(COF, Omega(p, q, r))
            if lhs != rhs:
                ok = False
                print("L2 FAIL", p, q, r)
            cnt += 1
print(f"L2 inheritance exhaustive-small: {cnt} triples, all pass = {ok}")
# random large
rnd = random.Random(193)
for _ in range(200000):
    p = tuple(rnd.randint(-10**6, 10**6) for _ in range(3))
    q = tuple(rnd.randint(-10**6, 10**6) for _ in range(3))
    r = tuple(rnd.randint(-10**6, 10**6) for _ in range(3))
    if Omega(matvec(M,p),matvec(M,q),matvec(M,r)) != matvec(COF, Omega(p,q,r)):
        ok = False; print("L2 random FAIL", p,q,r); break
print("L2 inheritance random-large (2e5): pass =", ok)
results["L2_inheritance_verified"] = ok

# ---- (2) DIGIT DECOMPOSITION of cross-cylinder Omega ------------------------
COFpow = [Mpow(0)]  # cof(M)^0 = I
_c = ((1,0,0),(0,1,0),(0,0,1))
for _ in range(12):
    _c = matmul(_c, COF)
    COFpow.append(_c)
MP = [Mpow(m) for m in range(13)]

def direct_cross_omega(g, delta, c1, c2):
    """c1[j], c2[j] for j=1..g are stitch-diff digits; c1[0]=c2[0]=delta.
    d1 = sum_{j=0..g} M^{g-j} c_j.  Returns Omega=d1 x d2 (exact int)."""
    d1 = (0,0,0); d2 = (0,0,0)
    C1 = [delta]+list(c1); C2 = [delta]+list(c2)
    for j in range(g+1):
        d1 = add(d1, matvec(MP[g-j], C1[j]))
        d2 = add(d2, matvec(MP[g-j], C2[j]))
    return cross(d1, d2), d1, d2

def decomposed_omega(g, delta, c1, c2):
    C1 = [delta]+list(c1); C2 = [delta]+list(c2)
    Om = (0,0,0)
    Bs = []
    for l in range(g+1):
        B = cross(C1[l], C2[l])
        for i in range(l):
            B = add(B, cross(matvec(MP[l-i], C1[i]), C2[l]))
        for j in range(l):
            B = add(B, cross(C1[l], matvec(MP[l-j], C2[j])))
        Bs.append(B)
        Om = add(Om, matvec(COFpow[g-l], B))
    return Om, Bs

decomp_ok = True
b0_zero = True
b1_ok = True
for trial in range(20000):
    g = rnd.randint(1, 8)
    delta = tuple(rnd.randint(-6, 6) for _ in range(3))         # meeting-shell scale digit
    c1 = [tuple(rnd.randint(-8, 8) for _ in range(3)) for _ in range(g)]  # stitch diffs (reach<=4 => diff<=8)
    c2 = [tuple(rnd.randint(-8, 8) for _ in range(3)) for _ in range(g)]
    Od, d1, d2 = direct_cross_omega(g, delta, c1, c2)
    Oc, Bs = decomposed_omega(g, delta, c1, c2)
    if Od != Oc:
        decomp_ok = False; print("DECOMP FAIL", g, delta, c1, c2, Od, Oc); break
    # B_0 identically zero
    if Bs[0] != (0,0,0):
        b0_zero = False
    # B_1 = sigma1 x tau1 + Delta x (tau1 - sigma1),  Delta = M.delta
    if g >= 1:
        sig1, tau1 = c1[0], c2[0]
        Delta = matvec(M, delta)
        b1_expected = add(cross(sig1, tau1), cross(Delta, sub(tau1, sig1)))
        if Bs[1] != b1_expected:
            b1_ok = False; print("B1 FAIL", Bs[1], b1_expected)
print(f"digit-decomposition identity (2e4 random, g in 1..8): pass = {decomp_ok}")
print(f"B_0 == 0 identically: {b0_zero}    B_1 form verified: {b1_ok}")
results["decomposition_identity_verified"] = decomp_ok
results["B0_identically_zero"] = b0_zero
results["B1_form_verified"] = b1_ok
results["Omega_form"] = "Omega = sum_{l=0..g} cof(M)^(g-l) B_l ; B_l = c1_l x c2_l + sum_{i<l}(M^{l-i}c1_i)xc2_l + sum_{j<l}c1_l x(M^{l-j}c2_j); c1_0=c2_0=delta=a'-a"
results["B1_explicit"] = "B_1 = sigma1 x tau1 + Delta x (tau1 - sigma1),  Delta = M.delta"

# ---- (3) deep-tail / horizon constants -------------------------------------
def min_Mj_inf(j, bound=6):
    Mj = MP[j]
    best = None; arg = None
    for v in itertools.product(range(-bound, bound+1), repeat=3):
        if v == (0,0,0):
            continue
        w = matvec(Mj, v)
        nrm = max(abs(w[0]), abs(w[1]), abs(w[2]))
        if best is None or nrm < best:
            best = nrm; arg = v
    return best, arg
# first row of M^j is (3^j,0,0), so v0!=0 forces |.|>=3^j; the min lives in a small box -> exhaustive
sep = {}
for j in (1,2,3):
    b, arg = min_Mj_inf(j)
    sep[j] = {"min_Minf": b, "argmin": arg}
    print(f"min|M^{j} v|_inf = {b}  (attained at v={arg})")
assert sep[1]["min_Minf"] == 3 and sep[2]["min_Minf"] == 8 and sep[3]["min_Minf"] == 24
results["min_Mjv_inf"] = {str(j): sep[j] for j in sep}
results["reach_le_4"] = "PROVEN over entire menu (design/lemma/finite_menu_check.py: reach<=4, interiors/word<=4)"
results["deep_tail_packing"] = "min|M^3 v|_inf = 24 > 2*reach = 8 : any Cheb-4 ball holds <=1 point of any M^3 Z^3 coset"

results["all_pass"] = bool(ok and decomp_ok and b0_zero and b1_ok
                           and sep[1]["min_Minf"]==3 and sep[2]["min_Minf"]==8 and sep[3]["min_Minf"]==24)
print("\nALL EXACT CHECKS PASS:", results["all_pass"])
json.dump(results, open('/Users/erik/homelab/math193/design/osc/pair_horizon/omega_form_results.json','w'), indent=1)
print("wrote omega_form_results.json")
