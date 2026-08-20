"""TASK A - the cheap, NON-CIRCULAR, level-independent covering-multiplicity bound.

GOAL.  Assemble an EXPLICIT integer N_uniform that upper-bounds the generation-g
covering multiplicity mult_g(3^g) -- the number of gen-g cylinders whose closure
meets the fine Chebyshev ball B_inf(q, 3^g) -- for ALL g and ALL legal amplified
walks, built ONLY from constants already proven (rho_c, kappa, eta), using ZERO
measurement of any realized walk.  Finite + level-independent  ==>  OSC (Schief
1994)  ==>  Ahlfors d-regularity (Mauldin-Williams 1988).

INPUTS (already proven; see design/osc/dg_closure_uniform_results.json, CONDITIONAL-THEOREM.md):
  M   = ((3,0,0),(0,0,-3),(0,3,-1))          expansion, det 27, |eigs|=3
  Q   = ((1,0,0),(0,6,-1),(0,-1,6))           invariant PD form,  M^T Q M = 9 Q
  |v|_Q^2 = v0^2 + 6 v1^2 - 2 v1 v2 + 6 v2^2   (Q-norm^2, integer on Z^3)
  Q eigenvalues = 1, 5, 7 ; det Q = 35
  rho_c = sqrt(745)  : cylinder Q-diameter / 3^g, uniform over ALL 79,003,838
                       menu words  (diam_Q(C^(g)) <= rho_c (3^g - 1)).  [PROVEN]
  kappa = 1 EXACTLY  : ||v||_inf <= ||v||_Q  (Q - maxcoord^2 is PSD).      [PROVEN]

THE CHAIN (all rigorous, no realized-walk measurement):

(0) SELF-SIMILAR ROOT LATTICE.  Gen-g cylinders are anchored at "roots"
    M^g a, a in Z^3, i.e. on L_g = M^g Z^3.  M^T Q M = 9 Q  ==>  by induction
    (M^g)^T Q M^g = 9^g Q, i.e. |M^g w|_Q = 3^g |w|_Q for all w  (M^g = 3^g O^g,
    O^g a Q-isometry).  [verified below for g=1..4]

(1) MINIMAL Q-SEPARATION.   s = min_{v in Z^3, v!=0} |v|_Q.  Roots at level g are
    then >= 3^g * s apart in Q-metric.

(2) WINDOW RADIUS R (g-independent).  Let a gen-g cylinder C meet B_inf(q, 3^g),
    witnessed by x in C with |x-q|_inf <= 3^g.  Its root r0 = M^g a lies in C, so
        |r0 - x|_Q <= diam_Q(C) <= rho_c (3^g - 1) < rho_c * 3^g.
    Convert the fine Cheb ball to Q:  |x - q|_Q <= eta * 3^g, where
        eta = sup_{v != 0} |v|_Q / |v|_inf = sqrt(15)   (EXACT; convex max of
        v^T Q v over the cube [-1,1]^3 is attained at a vertex = 15).  [verified]
    Triangle:  |r0 - q|_Q <= (rho_c + eta) * 3^g.   ==>   R = rho_c + eta.

(3) N_uniform.  |M^g a - q|_Q <= R 3^g  <=(scale by M^-g)=>  |a - M^-g q|_Q <= R.
    So  mult_g(3^g)  <=  #{ a in Z^3 : |a - c|_Q <= R }  for the (real) centre
    c = M^-g q.  Taking c = 0 (a lattice point):
        N_uniform := #{ a in Z^3 : |a|_Q <= R }.
    For a fully rigorous worst-CENTRE bound (c arbitrary), enlarge by the lattice
    Q-covering radius mu_Q (<= sqrt(15)/2 via coordinate rounding):
        N_worst  <=  #{ a in Z^3 : |a|_Q <= R + mu_Q }.
    Both are finite, level-independent, non-circular.
"""
import sys, math, json, time
sys.path.insert(0, "/Users/erik/homelab/math193")

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
Q = ((1, 0, 0), (0, 6, -1), (0, -1, 6))

def matmul(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def transpose(A):
    return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
def qn2(v):
    return v[0]*v[0] + 6*v[1]*v[1] - 2*v[1]*v[2] + 6*v[2]*v[2]
def cheb(v):
    return max(abs(v[0]), abs(v[1]), abs(v[2]))

# ---- exact test: is integer m <= (a*sqrt(p) + b*sqrt(q))^2 ?  (a,b,p,q >=0 ints)
# RHS = a^2 p + b^2 q + 2 a b sqrt(pq).  m <= RHS  <=>  L := m - a^2 p - b^2 q <= 2ab sqrt(pq)
#   L <= 0            -> True
#   L > 0 & ab==0     -> False
#   else              -> L^2 <= 4 a^2 b^2 p q     (both sides > 0, exact)
def le_sqsum(m, a, p, b, q):
    L = m - a*a*p - b*b*q
    if L <= 0:
        return True
    if a == 0 or b == 0:
        return False
    return L * L <= 4 * a * a * b * b * p * q

def count_ball(a, p, b, q):
    """#{ v in Z^3 : |v|_Q <= a*sqrt(p) + b*sqrt(q) }, exact."""
    Rf = a*math.sqrt(p) + b*math.sqrt(q)
    B = int(Rf) + 1                     # |v|_Q^2 >= 1*|v|_2^2  => |v_i| <= |v|_2 <= R
    n = 0
    for x in range(-B, B+1):
        x2 = x*x
        for y in range(-B, B+1):
            for z in range(-B, B+1):
                if le_sqsum(x2 + 6*y*y - 2*y*z + 6*z*z, a, p, b, q):
                    n += 1
    return n

def main():
    t0 = time.time()
    out = {}
    print("=== TASK A : NON-CIRCULAR LEVEL-INDEPENDENT COVERING-MULTIPLICITY BOUND ===\n")

    # ---------- (0) exact self-similarity of the root lattice ----------
    MT = transpose(M)
    ok_ss = (matmul(matmul(MT, Q), M) == tuple(tuple(9*Q[i][j] for j in range(3)) for i in range(3)))
    print(f"(0) M^T Q M == 9 Q  : {ok_ss}")
    Mg = ((1,0,0),(0,1,0),(0,0,1)); iso = []
    for g in range(1, 5):
        Mg = matmul(Mg, M)
        MgTQMg = matmul(matmul(transpose(Mg), Q), Mg)
        want = tuple(tuple((9**g)*Q[i][j] for j in range(3)) for i in range(3))
        okg = (MgTQMg == want)
        # spot-check |M^g v|_Q = 3^g |v|_Q on some integer v
        v = (2, -1, 3); lhs = qn2(tuple(sum(Mg[i][k]*v[k] for k in range(3)) for i in range(3)))
        rhs = (9**g) * qn2(v)
        iso.append({"g": g, "MgTQMg_eq_9g_Q": okg, "norm_scales_by_3g": lhs == rhs})
        print(f"    g={g}: (M^g)^T Q M^g == 9^g Q : {okg}   |M^g v|_Q^2 == 9^g|v|_Q^2 : {lhs==rhs}")
    out["self_similar"] = {"MTQM_eq_9Q": ok_ss, "per_g": iso}
    print("    => roots live on L_g = M^g Z^3 = 3^g O^g Z^3, O^g a Q-isometry;")
    print("       #{roots in Q-ball radius R*3^g} = #{a in Z^3 : |a|_Q <= R}, INDEPENDENT of g.\n")

    # ---------- (1) minimal Q-separation s ----------
    best2 = None; arg = None
    for x in range(-3, 4):
        for y in range(-3, 4):
            for z in range(-3, 4):
                if x == y == z == 0: continue
                m = qn2((x, y, z))
                if best2 is None or m < best2: best2 = m; arg = (x, y, z)
    s = math.sqrt(best2)
    print(f"(1) minimal Q-separation  s = min_{{v!=0}} |v|_Q = sqrt({best2}) = {s:.4f}   (witness {arg})")
    print(f"    => distinct gen-g roots are >= 3^g * s = 3^g apart in the Q-metric.\n")
    out["min_sep"] = {"s2": best2, "s": s, "witness": list(arg)}

    # ---------- (2) exact Cheb->Q constant eta and kappa ----------
    # eta^2 = max_{v in [-1,1]^3} v^T Q v ; convex => attained at a vertex (+-1,+-1,+-1)
    vert_max = max(qn2(v) for v in [(sx, sy, sz) for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)])
    # brute confirm on a big integer grid that |v|_Q^2 <= eta^2 * |v|_inf^2 for all v
    eta2 = vert_max
    conf = True; wit = None
    for x in range(-30, 31):
        for y in range(-30, 31):
            for z in range(-30, 31):
                if x == y == z == 0: continue
                if qn2((x, y, z)) * 1 > eta2 * cheb((x, y, z))**2:
                    conf = False; wit = (x, y, z)
    # kappa = sup ||v||_inf/||v||_Q ; Q >= maxcoord^2 (eigs>=1) => ||v||_inf<=||v||_Q => kappa<=1, =1 at e0
    kappa = 1.0
    print(f"(2) eta = sup |v|_Q/|v|_inf = sqrt({eta2}) = {math.sqrt(eta2):.6f}   "
          f"(vertex-attained; grid-confirmed all |v|<=30: {conf})")
    print(f"    kappa = sup |v|_inf/|v|_Q = 1 EXACTLY  (Q - maxcoord^2 PSD; eigs Q = 1,5,7)\n")
    out["eta2"] = eta2; out["eta"] = math.sqrt(eta2); out["eta_grid_confirmed"] = conf
    out["kappa"] = kappa

    # ---------- rho_c from proven closure-uniformity ----------
    dg = json.load(open("/Users/erik/homelab/math193/design/osc/dg_closure_uniform_results.json"))
    rho_c = dg["rho_c_Q"]; rho_c2 = round(rho_c*rho_c)
    assert abs(rho_c2 - rho_c*rho_c) < 1e-6 and rho_c2 == 745, rho_c2
    print(f"    rho_c (proven, closure-uniform over {dg['nwords']} menu words) = sqrt(745) = {rho_c:.6f}")

    # ---------- (2) window radius R ----------
    # PRIMARY (diameter form, exactly the task's derivation): R = rho_c + eta = sqrt(745)+sqrt(15)
    R = rho_c + math.sqrt(eta2)
    R2 = R*R
    # TIGHTER (radius-from-source: root-to-farthest cyl pt <= rho_c(3^g-1)/2): R' = rho_c/2 + eta
    Rt = rho_c/2 + math.sqrt(eta2)
    print(f"\n(2) WINDOW RADIUS  R = rho_c + eta = sqrt(745) + sqrt(15) = {R:.6f}   (R^2 = {R2:.4f})")
    print(f"    [tighter radius-from-source variant  R' = rho_c/2 + eta = {Rt:.6f}]\n")
    out["rho_c2"] = rho_c2; out["rho_c"] = rho_c
    out["R_diam"] = R; out["R_diam2"] = R2
    out["R_tight_radius_from_source"] = Rt

    # ---------- (3) N_uniform (origin-centred, exact) ----------
    print("(3) enumerating N_uniform = #{a in Z^3 : |a|_Q <= R} (exact integer test) ...")
    N_uniform = count_ball(1, 745, 1, 15)                      # R = 1*sqrt(745)+1*sqrt(15)
    print(f"    N_uniform (R = sqrt745+sqrt15)                = {N_uniform}   [{time.time()-t0:.0f}s]")
    N_tight = count_ball(1, 745//1, 0, 0) if False else None   # placeholder; compute R' below
    # R' = rho_c/2 + eta = sqrt(745)/2 + sqrt(15) = sqrt(745/4)+sqrt(15) = (1/2)sqrt(745)+sqrt(15)
    # represent as a*sqrt(p)+b*sqrt(q) with rationals -> scale: use sqrt(745)/2 => a= ? handle via 2R'=sqrt(745)+2sqrt(15)
    # count |a|_Q <= R'  <=>  |2a|... no; do exact test with half: (rho_c/2)=sqrt(745/4), 745/4 not integer.
    # Use exact test via le_sqsum on m <= (sqrt(745)/2 + sqrt(15))^2 = 745/4 + 15 + sqrt(745*15)
    def le_Rt(m):  # m <= 745/4 + 15 + sqrt(11175)  <=> 4m <= 745 + 60 + 4 sqrt(11175) = 805 + 4 sqrt(11175)
        L = 4*m - 805                                          # compare L <= 4 sqrt(11175)
        if L <= 0: return True
        return L*L <= 16 * 11175
    B = int(Rt) + 1; N_tight = 0
    for x in range(-B, B+1):
        for y in range(-B, B+1):
            for z in range(-B, B+1):
                if le_Rt(x*x + 6*y*y - 2*y*z + 6*z*z): N_tight += 1
    print(f"    N_tight   (R'= sqrt745/2+sqrt15 = {Rt:.3f})   = {N_tight}")

    # ---------- worst-CENTRE rigorous upper bound ----------
    # mu_Q = Q-covering radius of Z^3 <= max_{r in [-1/2,1/2]^3} |r|_Q = sqrt(15)/2 (same vertex arg)
    mu_Q = math.sqrt(eta2) / 2
    # N_worst <= #{a : |a|_Q <= R + mu_Q}, R+mu = sqrt(745) + (3/2)sqrt(15)
    # (R+mu)^2 = 745 + (9/4)15 + 2*(3/2)sqrt(745*15) = 745 + 33.75 + 3 sqrt(11175)
    def le_Rw(m):  # m <= 745 + 135/4 + 3 sqrt(11175) <=> 4m - 3115 <= 12 sqrt(11175)
        L = 4*m - 3115
        if L <= 0: return True
        return L*L <= 144 * 11175
    Rw = R + mu_Q; B = int(Rw) + 1; N_worst = 0
    for x in range(-B, B+1):
        for y in range(-B, B+1):
            for z in range(-B, B+1):
                if le_Rw(x*x + 6*y*y - 2*y*z + 6*z*z): N_worst += 1
    print(f"    mu_Q (lattice Q-covering radius) <= sqrt(15)/2 = {mu_Q:.4f}")
    print(f"    N_worst  <= #{{|a|_Q <= R+mu_Q={Rw:.3f}}}      = {N_worst}   (rigorous worst-centre bound)\n")
    out["N_uniform"] = N_uniform
    out["N_tight_radius_from_source"] = N_tight
    out["mu_Q_upper"] = mu_Q
    out["N_worst_center_upper"] = N_worst

    # ---------- (4) validation vs proven/measured comparanda ----------
    cm = json.load(open("/Users/erik/homelab/math193/design/osc/closure_multiplicity_results.json"))
    measured = cm["measured_mult"]           # 4 / 5 / 4  at r=3^g
    packing = cm["packing_bound_P_g"]        # 315 / 480 / 612
    meas_max = max(measured.values())
    print("(4) VALIDATION")
    print(f"    measured mult_g(3^g)  (realized walk): {measured}  -> max {meas_max}")
    print(f"    prior cubic packing bound P_g        : {packing}")
    print(f"    N_uniform (this, non-circular)       : {N_uniform}")
    finite = N_uniform < math.inf
    dominates = N_uniform >= meas_max
    lvl_indep = all(it["MgTQMg_eq_9g_Q"] and it["norm_scales_by_3g"] for it in iso)
    print(f"    finite : {finite}   |   dominates measured 4/5/4 : {dominates}   |   "
          f"level-independent (self-similarity) : {lvl_indep}")
    out["validation"] = {"measured_mult": measured, "measured_max": meas_max,
                         "prior_packing": packing, "finite": finite,
                         "dominates_measured": dominates, "level_independent": lvl_indep}

    out["summary"] = {
        "s (min Q-sep, s^2)": [s, best2],
        "eta = sqrt(15)": math.sqrt(eta2),
        "kappa": 1.0,
        "rho_c = sqrt(745)": rho_c,
        "R = rho_c + eta = sqrt(745)+sqrt(15)": R,
        "N_uniform = #{a in Z^3 : |a|_Q <= R}": N_uniform,
        "N_worst_center_upper (rigorous)": N_worst,
        "R_tight = rho_c/2 + eta": Rt,
        "N_tight": N_tight,
    }
    json.dump(out, open("/Users/erik/homelab/math193/design/osc/nuniform_covering_bound_results.json", "w"),
              indent=2)
    print(f"\nwrote design/osc/nuniform_covering_bound_results.json   [{time.time()-t0:.0f}s]")
    print("\n--- HEADLINE ---")
    print(f"  s = {s:.0f} (s^2={best2}),  eta = sqrt(15) = {math.sqrt(eta2):.4f},  kappa = 1,  rho_c = sqrt(745) = {rho_c:.4f}")
    print(f"  R = sqrt(745) + sqrt(15) = {R:.4f}")
    print(f"  N_uniform = {N_uniform}    (worst-centre rigorous <= {N_worst})")

if __name__ == "__main__":
    main()
