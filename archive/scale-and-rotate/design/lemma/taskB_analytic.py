"""
TASK B — analytic component (matrix / MENU geometry) for the REFILL BOUND.

Computes, exactly (integer / exact-rational arithmetic):
  - MENU = candidate_step_vectors(2) (124 nonzero steps in [-2,2]^3)
  - max Chebyshev norm of a MENU step  (bounds how far an interior point is
    from its anchor: <= (len-1) steps, each |.|_inf <= this)
  - min anchor separation g = min_{s in MENU} |M s|_inf  (and Euclidean),
    argmin step(s). Consecutive anchors are M*p, M*p' with p'-p = s in MENU.
  - M^{-1} (exact rational) and ||M^{-1}||_inf (max abs row sum) -> maps a
    Cheb radius in anchor-space to a Cheb radius in parent (pre-image) space.
  - The proven refill cap:
        every interior point lies within Cheb 2*(len-1) of BOTH anchors,
        and within Cheb 2*floor(len/2) of its NEARER anchor.
        With len<=5: nearer-anchor radius r_near = 4, far radius = 8.
        Interiors in a Cheb-R box => nearer anchor in Cheb-(R+r_near) box.
        Grouped by nearer anchor, <= r_int interiors per anchor
        (2 incident segments * up to ceil((len-1)/2) each).
        => B <= r_int * A_{R+r_near},  A = max anchors in that concentric box.
Outputs JSON to stdout.
"""
import json
from fractions import Fraction as F

# MENU
MENU = [(x, y, z)
        for x in range(-2, 3) for y in range(-2, 3) for z in range(-2, 3)
        if (x, y, z) != (0, 0, 0)]
assert len(MENU) == 124

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))


def apply(Mm, v):
    return (Mm[0][0]*v[0]+Mm[0][1]*v[1]+Mm[0][2]*v[2],
            Mm[1][0]*v[0]+Mm[1][1]*v[1]+Mm[1][2]*v[2],
            Mm[2][0]*v[0]+Mm[2][1]*v[1]+Mm[2][2]*v[2])


def cheb(v):
    return max(abs(c) for c in v)


def eucl2(v):
    return sum(c*c for c in v)


# max MENU step norm
max_menu_cheb = max(cheb(s) for s in MENU)          # = 2

# min anchor separation over MENU images
Ms = [(s, apply(M, s)) for s in MENU]
min_cheb = min(cheb(v) for _, v in Ms)
argmin_cheb = [s for s, v in Ms if cheb(v) == min_cheb]
min_e2 = min(eucl2(v) for _, v in Ms)
argmin_e2 = [s for s, v in Ms if eucl2(v) == min_e2]

# exact M^{-1} via cofactors: M^{-1} = adj(M)/det
def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
            - A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
            + A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))

det = det3(M)
# cofactor matrix
def minor(A, i, j):
    rows = [r for r in range(3) if r != i]
    cols = [c for c in range(3) if c != j]
    r0 = [A[rows[0]][cc] for cc in cols]
    r1 = [A[rows[1]][cc] for cc in cols]
    return r0[0]*r1[1] - r0[1]*r1[0]

cof = [[((-1)**(i+j))*minor(M, i, j) for j in range(3)] for i in range(3)]
adj = [[cof[j][i] for j in range(3)] for i in range(3)]   # transpose
Minv = [[F(adj[i][j], det) for j in range(3)] for i in range(3)]

# ||M^{-1}||_inf = max abs row sum
row_sums = [sum(abs(Minv[i][j]) for j in range(3)) for i in range(3)]
Minv_inf = max(row_sums)   # Fraction

# proven cap parameters (construction rule: word length <= 5)
RULE_MAXLEN = 5
r_int_rule = RULE_MAXLEN - 1          # <=4 interiors per anchor gap (word len<=5)
# each interior is within (len-1) steps of anchor_i; each step |.|_inf<=2
far_radius_rule = max_menu_cheb * (RULE_MAXLEN - 1)      # =8 : dist to start anchor
near_radius_rule = max_menu_cheb * (RULE_MAXLEN // 2)    # =4 : dist to nearer anchor
# interiors grouped by NEARER anchor: per anchor, 2 incident segments,
# each contributes at most ceil((len-1)/2) interiors nearer to that anchor
import math
per_anchor_rule = 2 * math.ceil((RULE_MAXLEN - 1) / 2)   # 2*2 = 4

# same, using MEASURED max word length (=4 in v2) for a tighter measured cap
MEAS_MAXLEN = 4
near_radius_meas = max_menu_cheb * (MEAS_MAXLEN // 2)     # =4
far_radius_meas = max_menu_cheb * (MEAS_MAXLEN - 1)       # =6
per_anchor_meas = 2 * math.ceil((MEAS_MAXLEN - 1) / 2)    # 2*2 = 4  (ceil(3/2)=2)

R = 10  # the Cheb box radius of interest
# concentric anchor-box radius (nearer-anchor argument)
anchor_box_R_rule = R + near_radius_rule    # 14
anchor_box_R_meas = R + near_radius_meas    # 14

# pre-image radius in parent space (anchors = M*parent): a Cheb-r box of anchors
# is the M-image of parent points inside M^{-1}(box); that pre-image is contained
# in a Cheb ball of radius r * ||M^{-1}||_inf about the pre-image center.
def times(fr, k):
    return fr * k

preimg_radius_rule = float(Minv_inf * anchor_box_R_rule)

out = {
    "MENU_size": len(MENU),
    "max_menu_step_cheb": max_menu_cheb,
    "min_anchor_sep_cheb": min_cheb,
    "argmin_cheb_steps": argmin_cheb,
    "min_anchor_sep_eucl": {"sq": min_e2, "val": min_e2 ** 0.5},
    "argmin_eucl_steps": argmin_e2,
    "det_M": det,
    "M_inv": [[str(Minv[i][j]) for j in range(3)] for i in range(3)],
    "M_inv_inf_norm": str(Minv_inf),
    "M_inv_inf_norm_float": float(Minv_inf),
    "proven_cap_rule_len5": {
        "max_interiors_per_segment": r_int_rule,
        "near_anchor_radius": near_radius_rule,
        "far_anchor_radius": far_radius_rule,
        "interiors_per_nearer_anchor": per_anchor_rule,
        "anchor_box_radius_for_R10": anchor_box_R_rule,
        "cap_formula": "B <= per_anchor * A_{R+near} = %d * A_14" % per_anchor_rule,
        "parent_preimage_cheb_radius": preimg_radius_rule,
    },
    "measured_rule_len4": {
        "max_interiors_per_segment": MEAS_MAXLEN - 1,
        "near_anchor_radius": near_radius_meas,
        "far_anchor_radius": far_radius_meas,
        "interiors_per_nearer_anchor": per_anchor_meas,
        "anchor_box_radius_for_R10": anchor_box_R_meas,
    },
}
print(json.dumps(out, indent=2))
