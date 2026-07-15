"""
ROUTE 2 joint-induction update matrix + closing condition, and the measured
joint envelope trajectory (C_k, E_k) at L6/L7/L8.

Two competing models for the refill row of the 2x2 update on (C_k, E_k),
c_k(rho) <= C_k rho + 1,  b_k(rho) <= E_k rho :

 (A) PESSIMISTIC (per-anchor / per-word counting, PROVABLE but does NOT close):
     refill slope proportional to crowding, E_k = a*(4/9)*C_k with a = max
     interiors-per-word x shell factor (measured effective a ~ 3.5).
       U_A = [[4/9, 1],[16a/81, 4a/9]],  det U_A = 0,  rho(U_A) = (4/9)(1+a).
     Closes iff a < 5/4.  Measured a ~ 3.5  =>  rho(U_A) ~ (4/9)(4.5) = 2.0 > 1. FAILS.

 (B) MENU-SOURCE (refill slope an EXOGENOUS menu constant E, the sub-lemma):
     E_{k+1} = E_max (level-independent),  independent of C_k.
       U_B = [[4/9, 1],[0, 0]],  eigenvalues {4/9, 0},  rho(U_B) = 4/9 < 1.
     Source term E_max.  CLOSES: C* = E_max/(1-4/9) = (9/5) E_max.
     With measured E_max = 3  =>  C* = 27/5 = 5.4.

Data adjudicates A vs B: E_k measured flat at 3.0 while C_k rises 2.5->3->3;
proportional model (A) would force E_k up to (4/9)*a*C_k ~ rising. It doesn't.
"""
import json, os
from fractions import Fraction as F

# ---- measured joint envelope (from joint_measure.py / refill_envelope.py) ----
# C_k = max_rho (c_k(rho)-1)/rho ; E_k = max_rho b_k(rho)/rho over rho in [0.5,10]
CK = {"L6": 2.5, "L7": 3.0, "L8": 3.0}
EK = {"L6": 3.0, "L7": 3.0, "L8": 3.0}

alpha = F(4, 9)          # ||M^-1||_inf, exact
Emax  = 3                # measured level-independent refill slope
Cstar = Emax / (1 - alpha)   # fixed point of C_{k+1}=alpha C_k + Emax

def eig2(m):
    (a,b),(c,d) = m
    tr = a+d; det = a*d-b*c
    disc = tr*tr - 4*det
    # exact/float sqrt
    import math
    s = math.sqrt(float(disc)) if disc>=0 else 0.0
    return (float(tr)/2 + s/2, float(tr)/2 - s/2), float(tr), float(det)

# model B update matrix
UB = [[alpha, F(1)], [F(0), F(0)]]
(l1B,l2B), trB, detB = eig2(UB)

# model A (pessimistic) with measured effective a
def modelA(a):
    a = F(a).limit_denominator(1000)
    UA = [[alpha, F(1)], [F(16)*a/81, F(4)*a/9]]
    (l1,l2), tr, det = eig2(UA)
    return dict(a=float(a), UA=[[str(x) for x in r] for r in UA],
                spectral_radius=(4/9)*(1+float(a)), det=det,
                closes=(4/9)*(1+float(a))<1)

# closure check of the measured trajectory under model B: C_{k+1} <= alpha C_k + Emax
traj = []
levels = ["L6","L7","L8"]
for i in range(len(levels)-1):
    k, kp = levels[i], levels[i+1]
    rhs = float(alpha)*CK[k] + EK[k]
    traj.append(dict(step=f"{k}->{kp}", Ck=CK[k], Ek=EK[k],
                     rhs_alphaCk_plus_Ek=round(rhs,4),
                     Ckp_measured=CK[kp], holds=CK[kp] <= rhs + 1e-9))

out = {
  "matrix_M": [[3,0,0],[0,0,-3],[0,3,-1]],
  "alpha_Minv_inf": "4/9",
  "singular_values_M": [2.5414, 3.0000, 3.5414],
  "model_B_menu_source": {
     "update_matrix_UB": [[str(alpha),"1"],["0","0"]],
     "eigenvalues": [round(l1B,6), round(l2B,6)],
     "spectral_radius": round(max(abs(l1B),abs(l2B)),6),
     "source_term_Emax": Emax,
     "fixed_point_Cstar": str(Cstar) + f" = {float(Cstar)}",
     "closes": max(abs(l1B),abs(l2B))<1,
     "refill_sublemma": "b_k(rho) <= Emax*rho, Emax=3, level-independent (THE finite check)"
  },
  "model_A_pessimistic_effective_a": {a: modelA(a) for a in (1.25, 3.5)},
  "measured_joint_envelope": {"C_k": CK, "E_k": EK,
     "C_k_note": "rises 2.5->3->3 then flat, all <= C*=5.4",
     "E_k_note": "flat 3.0 at every level => menu-source model (B), NOT proportional (A)"},
  "trajectory_closure_check_modelB": traj,
  "verdict": "Joint system CLOSES under model B (spectral radius 4/9<1, C*=27/5=5.4) "
             "iff the refill slope E_max is level-independent. Measured flat at 3.0 "
             "across L6/L7/L8, off-lattice-robust, holds to rho=20. Model A (the "
             "PROVABLE per-anchor bound) has spectral radius (4/9)(1+a)>1 for a>=5/4 "
             "and does NOT close; the gap between A and B IS the refill sub-lemma."
}
p = os.path.join(os.path.dirname(__file__), "joint_update.json")
json.dump(out, open(p,"w"), indent=2)
print(json.dumps(out, indent=2))
