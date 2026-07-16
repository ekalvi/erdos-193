"""
TASK B (independent) — measure the level-k vs level-(k-1) CROWDING RECURSION
constants directly on the v2 proof orbit (gate2 walks), and stress the targeted
small bound.

For each transition (k)->(k+1)  [k+1 in {6,7,8}]:
  * build walk_{k+1} (chain = anchors interleaved with fresh stitch interiors),
    tagging each point anchor vs interior;
  * reconstruct the PARENT walk_{k} from parent_word (verified anchors==M*parent);
  * measure, over centres q (all walk points; exact), for rho in R:
      a(q,rho)   = #anchors   in Cheb-rho ball   (the "dilated-old" term)
      ref(q,rho) = #interiors in Cheb-rho ball   (the "refill" term)
      c(q,rho)   = a+ref                          (full crowding, exact)
      D(q,rho)   = c_k(M^-1 q, (4/9)rho)          (the RHS the induction uses:
                    parent crowding in the PULLED-BACK ball; exact integer test
                    via 9-scaling since M^-1 = [[1/3,0,0],[0,-1/9,1/3],[0,-1/3,0]])
    -> TERMWISE RECURSION:  a(q,rho) <= D(q,rho)   (must hold with 0 violations;
       this is the load-bearing induction step BOUND2). Overcount = D/a measures
       how loose the isotropic 4/9 pull-back is vs the true anisotropy.
  * contraction factor (radius): the anchors in B(q,rho) pull back under M^-1;
    measure max_a ||M^-1(a-q)||_inf / rho  -> effective radius contraction phi_r
    (proven ceiling 4/9=0.444).
  * refill slope E = max_rho ref_max(rho)/rho (single-level refill lemma).
  * fixed point / uniform constant: C_lin=max c(r)/r, C_d=max c(r)/r^d, and the
    LOAD-BEARING c(4.44) (availability threshold 12).

Grid-indexed; centres exact over all walk points; parent pull-back via a hash set
+ small integer-box enumeration. Bounded.
"""
import pickle, sys, math, json
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3 as M

MENU = candidate_step_vectors(2)
LAM = 3.36
D_DIM = math.log(LAM) / math.log(3)   # ~1.104
RSTAR = 4.44                          # binding radius (availability tube pull-back)


def Mv(v):
    return (M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
            M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
            M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2])


def word_interiors(start, wi):
    pts = []; x, y, z = start
    for si in wi[:-1]:
        s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; pts.append((x, y, z))
    return pts


def build(L):
    d = pickle.load(open(f"gate2-l7-construction-L{L}.pkl", "rb"))
    anchors = d["anchors"]; words = d["words"]; pw = d["parent_word"]
    chain = []; is_anchor = []
    for i in range(len(anchors)-1):
        chain.append(tuple(anchors[i])); is_anchor.append(1)
        for q in word_interiors(anchors[i], words[i]):
            chain.append(q); is_anchor.append(0)
    chain.append(tuple(anchors[-1])); is_anchor.append(1)
    # parent walk = level L-1 walk
    parent = [(0, 0, 0)]; x = y = z = 0
    for si in pw:
        s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; parent.append((x, y, z))
    # sanity: anchors == M*parent
    assert all(Mv(parent[i]) == tuple(anchors[i]) for i in range(0, len(parent), max(1, len(parent)//50)))
    return chain, is_anchor, parent


def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))


def grid_of(pts, cell):
    g = defaultdict(list)
    for p in pts:
        g[(p[0]//cell, p[1]//cell, p[2]//cell)].append(p)
    return g


def max_count(centers, targets_grid, cell, radius):
    """max over centers of #targets within Cheb-radius. cell>=radius."""
    best = 0; best_q = None
    span = range(-((radius//cell)+1), (radius//cell)+2)
    for q in centers:
        gx, gy, gz = q[0]//cell, q[1]//cell, q[2]//cell
        c = 0
        for dx in span:
            for dy in span:
                for dz in span:
                    for p in targets_grid.get((gx+dx, gy+dy, gz+dz), ()):
                        if abs(p[0]-q[0]) <= radius and abs(p[1]-q[1]) <= radius and abs(p[2]-q[2]) <= radius:
                            c += 1
        if c > best:
            best = c; best_q = q
    return best, best_q


def parent_pullback_count(q, parent_set, rho4):
    """D = #parent p with |9p - 9 M^-1 q|_inf <= 4*rho  (exact; rho4 = 4*rho int).
    9 M^-1 q = (3qx, 3qz - qy, -3qy)."""
    w0 = 3*q[0]; w1 = 3*q[2]-q[1]; w2 = -3*q[1]
    x0 = -(-(w0-rho4)//9); x1 = (w0+rho4)//9   # ceil((w0-rho4)/9) .. floor
    y0 = -(-(w1-rho4)//9); y1 = (w1+rho4)//9
    z0 = -(-(w2-rho4)//9); z1 = (w2+rho4)//9
    c = 0
    for px in range(x0, x1+1):
        for py in range(y0, y1+1):
            for pz in range(z0, z1+1):
                if (px, py, pz) in parent_set:
                    # exact scaled check (box already exact for cheb in 9-space)
                    if abs(9*px-w0) <= rho4 and abs(9*py-w1) <= rho4 and abs(9*pz-w2) <= rho4:
                        c += 1
    return c


def measure(L, out):
    chain, is_anchor, parent = build(L)
    anchors = [p for p, a in zip(chain, is_anchor) if a]
    interiors = [p for p, a in zip(chain, is_anchor) if not a]
    parent_set = set(parent)
    N = len(chain)
    rec = {"level": L, "parent_level": L-1, "N": N,
           "n_anchor": len(anchors), "n_interior": len(interiors),
           "n_parent": len(parent)}

    # ---- walk-centre crowding c(r), a(r), ref(r); grids ----
    gA = {}; gI = {}; gC = {}
    for r in range(1, 11):
        gA[r] = grid_of(anchors, max(r, 1))
        gI[r] = grid_of(interiors, max(r, 1))
        gC[r] = grid_of(chain, max(r, 1))
    c_r = []; a_r = []; ref_r = []
    for r in range(1, 11):
        c, _ = max_count(chain, gC[r], max(r, 1), r)
        a, _ = max_count(chain, gA[r], max(r, 1), r)
        rf, _ = max_count(chain, gI[r], max(r, 1), r)
        c_r.append(c); a_r.append(a); ref_r.append(rf)
    rec["c_walkcentre_r1_10"] = c_r
    rec["anchor_a_r1_10"] = a_r
    rec["refill_ref_r1_10"] = ref_r
    rec["C_lin"] = round(max(c_r[r-1]/r for r in range(1, 11)), 3)
    rec["C_d"] = round(max(c_r[r-1]/(r**D_DIM) for r in range(1, 11)), 3)
    rec["E_refill_slope"] = round(max(ref_r[r-1]/r for r in range(1, 11)), 3)
    # load-bearing c(4.44): between c(4) and c(5)
    rec["c_4"] = c_r[3]; rec["c_5"] = c_r[4]
    rec["c_4.44_bracket"] = [c_r[3], c_r[4]]
    rec["Cd_at_4.44_from_c5"] = round(c_r[4]/(RSTAR**D_DIM), 3)

    # ---- TERMWISE RECURSION check: a(q,rho) <= D(q,rho) = c_k(M^-1 q,(4/9)rho) ----
    # sample centres (subsample for the pullback query, exact per sample)
    step = max(1, N//5000)
    samp = chain[::step]
    term = {}
    for rho in (4, 5, 8, 10):
        rho4 = 4*rho  # 9*(4/9)rho
        viol = 0; max_over = 0.0; max_D = 0; max_a = 0
        gAr = grid_of(anchors, max(rho, 1)); gIr = grid_of(interiors, max(rho, 1))
        cell = max(rho, 1); span = range(-((rho//cell)+1), (rho//cell)+2)
        max_c = 0; max_ref = 0
        for q in samp:
            gx, gy, gz = q[0]//cell, q[1]//cell, q[2]//cell
            a = 0; rf = 0
            for dx in span:
                for dy in span:
                    for dz in span:
                        for p in gAr.get((gx+dx, gy+dy, gz+dz), ()):
                            if cheb(p, q) <= rho:
                                a += 1
                        for p in gIr.get((gx+dx, gy+dy, gz+dz), ()):
                            if cheb(p, q) <= rho:
                                rf += 1
            Dv = parent_pullback_count(q, parent_set, rho4)
            if a > Dv:
                viol += 1
            if a > 0 and Dv/a > max_over:
                max_over = Dv/a
            if Dv > max_D:
                max_D = Dv
            if a > max_a:
                max_a = a
            if a+rf > max_c:
                max_c = a+rf
            if rf > max_ref:
                max_ref = rf
        term[rho] = {"termwise_violations_a_gt_D": viol,
                     "max_overcount_D_over_a": round(max_over, 3),
                     "max_D_pullback_parent": max_D,
                     "max_anchor_a": max_a,
                     "max_refill": max_ref,
                     "max_c_sampled": max_c,
                     "induction_RHS_maxD_plus_maxrefill": max_D + max_ref}
    rec["termwise_recursion"] = term

    # ---- radius contraction phi_r: max ||M^-1 (a-q)||_inf / rho over anchors in B(q,rho) ----
    # M^-1(v) = (vx/3, -vy/9 + vz/3, -vy/3); use 9-scale then /9
    def m1inf(v):
        a0 = abs(3*v[0]); a1 = abs(-v[1]+3*v[2]); a2 = abs(-3*v[1])
        return max(a0, a1, a2)/9.0
    rho = 10; cell = rho; gAr = grid_of(anchors, cell)
    worst_phi = 0.0
    for q in samp:
        gx, gy, gz = q[0]//cell, q[1]//cell, q[2]//cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for p in gAr.get((gx+dx, gy+dy, gz+dz), ()):
                        d = cheb(p, q)
                        if 0 < d <= rho:
                            phi = m1inf((p[0]-q[0], p[1]-q[1], p[2]-q[2]))/d
                            if phi > worst_phi:
                                worst_phi = phi
    rec["radius_contraction_phi_r_max"] = round(worst_phi, 4)
    rec["radius_contraction_ceiling_4/9"] = round(4/9, 4)

    out[L] = rec
    print(json.dumps({L: rec}), flush=True)


if __name__ == "__main__":
    Ls = [int(x) for x in sys.argv[1:]] or [6, 7, 8]
    out = {"d_dim": D_DIM, "lam": LAM, "Minv_inf_norm": "4/9", "rstar": RSTAR}
    lv = {}
    for L in Ls:
        measure(L, lv)
    out["levels"] = lv
    json.dump(out, open("design/tight/taskB_recursion_check.json", "w"), indent=1)
    print("WROTE design/tight/taskB_recursion_check.json", flush=True)
