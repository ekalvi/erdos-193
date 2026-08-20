from fractions import Fraction as F
import math
# packing bound N(rho) = g*(floor(2(rho+4)/3)+1)^3 ; also anchor-only (floor(2rho/3)+1)^3
def floor_term(rho, shift):
    # floor(2*(rho+shift)/3)+1, rho a Fraction
    val = F(2)*(rho+shift)/3
    return math.floor(val)+1
def pack(rho, g, shift=4):
    return g*(floor_term(rho,shift))**3

# bound/rho is decreasing within each constant-numerator step; numerator jumps where
# 2(rho+4)/3 hits an integer m => rho = 3m/2 - 4. Left endpoints of steps on [1,10]:
# candidate rho values: rho=1 (start) and each jump point in (1,10].
jump_pts = []
m = 3
while True:
    rho = F(3*m,2) - 4
    if rho > 10: break
    if rho >= 1: jump_pts.append(rho)
    m += 1
cands = sorted(set([F(1)] + [p for p in jump_pts if 1<=p<=10]))
print("candidate left-endpoints (rho):", [float(x) for x in cands])
for g in (3,4):
    best=F(0); arg=None
    print(f"\n=== g={g} ===")
    print("rho     floor+1   N=pack    N/rho")
    for rho in cands:
        ft=floor_term(rho,4); N=g*ft**3; r=F(N,1)/rho
        print(f"{float(rho):6.3f}  {ft:6d}   {N:7d}   {float(r):8.2f}")
        if r>best: best=r; arg=rho
    # also check right endpoint rho=10
    ft=floor_term(F(10),4); N=g*ft**3; r=F(N,1)/10
    print(f"{10.0:6.3f}  {ft:6d}   {N:7d}   {float(r):8.2f}  (rho=10 right end)")
    if r>best: best=r; arg=F(10)
    print(f"  --> smallest E (sup N/rho on [1,10]) = {float(best):.3f}  attained at rho={float(arg)}")

# anchor-only packing (for reference) at rho=1 and rho=10
print("\nanchor packing a(rho)=(floor(2rho/3)+1)^3:", (int(2*1//3)+1)**3, (int(2*10//3)+1)**3)
