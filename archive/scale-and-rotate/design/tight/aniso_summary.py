"""
ROUTE 3 anisotropic closing coefficient - consolidation.

Reads design/tight/aniso_measure.json (per-level rho-rows with c, a, b, birth-decomp tj).
Computes, per level:
  E            = single-level refill slope  = max_rho b_stitch(rho)/rho          (the LEMMA input)
  E_mid        = refill slope at load-bearing rho in [4,5]
  S            = sum_j ||M^-j||inf  = 1.67693  (EXACT, spectral rate 1/3)   [anisotropic]
  S_iso        = 9/5 = 1.8                                                   [isotropic ||M^-1||inf=4/9]
  Sprime_meas  = max_rho c(rho)/t0(rho)  = measured birth-decay sum (thin-region, <= S)
  C_meas       = max_rho c(rho)/rho
And validates the TERMWISE anisotropic bound  t_j(rho) <= E * rho * ||M^-j||inf.
"""
import json
from fractions import Fraction as F

# exact ||M^-j||inf
Minv=[[F(1,3),0,0],[0,F(-1,9),F(1,3)],[0,F(-1,3),0]]
def mm(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def inf(A): return max(sum(abs(x) for x in r) for r in A)
P=[[F(1),0,0],[0,F(1),0],[0,0,F(1)]]; NORM=[]
for j in range(40): NORM.append(inf(P)); P=mm(P,Minv)
S=float(sum(NORM))
Siso=9/5

data=json.load(open("design/tight/aniso_measure.json"))
print(f"S = sum ||M^-j||inf (anisotropic, spectral 1/3) = {S:.5f}")
print(f"S_iso = 9/5 (isotropic 4/9 per step)            = {Siso:.5f}")
print(f"||M^-j||inf j=0..4: {[round(float(x),4) for x in NORM[:5]]}\n")

summary={}
for Lk,rows in sorted(data.items()):
    E=max(r["b_stitch"]/r["rho"] for r in rows)
    Emid=max(r["b_stitch"]/r["rho"] for r in rows if 4<=r["rho"]<=5)
    Cmeas=max(r["c_over_rho"] for r in rows)
    # measured birth-decay sum S' = c / t0
    Sprime=0.0
    for r in rows:
        t0=r["birth_decomp_tj"].get("0",0)
        if t0: Sprime=max(Sprime, r["c"]/t0)
    # termwise bound check: t_j <= E*rho*||M^-j||inf  (E = ceil single-level slope = 3)
    Euse=3.0
    viol=[]
    for r in rows:
        for js,tj in r["birth_decomp_tj"].items():
            j=int(js); bound=Euse*r["rho"]*float(NORM[j])
            if tj>bound+1e-9: viol.append((r["rho"],j,tj,round(bound,2)))
    # overcount of isotropic anchor bound vs true anchor count
    oc=max((r["overcount_ratio"] or 0) for r in rows)
    C_aniso=E*S; C_iso=E*Siso
    print(f"{Lk}:  E(single-level refill slope,max)={E:.2f}  E_mid[4,5]={Emid:.2f}  "
          f"C_meas(max c/rho)={Cmeas:.2f}")
    print(f"      C_iso = E*9/5   = {C_iso:.2f}   (isotropic)")
    print(f"      C_aniso = E*S   = {C_aniso:.2f}   (anisotropic spectral, no charge blow-up)")
    print(f"      S'_meas = max c/t0 = {Sprime:.2f}  (thin-region decay, <=S)  ->  E_mid*S'_meas = {Emid*Sprime:.2f}")
    print(f"      anchor iso-overcount max = {oc:.2f}x   |  termwise t_j<=3*rho*||M^-j|| violations: {len(viol)}")
    if viol: print("        VIOL:",viol[:6])
    print()
    summary[Lk]=dict(E=E,E_mid=Emid,C_meas=Cmeas,C_iso=round(C_iso,3),
                     C_aniso=round(C_aniso,3),Sprime_meas=round(Sprime,3),
                     tight_est=round(Emid*Sprime,3),anchor_overcount=round(oc,3),
                     termwise_violations=len(viol))
summary["S_aniso_exact"]=round(S,5)
summary["S_iso"]=Siso
json.dump(summary, open("design/tight/aniso_summary.json","w"), indent=1)
print("wrote design/tight/aniso_summary.json")
