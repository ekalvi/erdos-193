import math
# If b_k(rho) <= P(rho) cubic packing, the crowding fixed point c*(rho)=sum_j P((4/9)^j rho).
# Show it stays cubic & finite (level-independent) — qualitative no-blow-up, but cubic.
g=4
def P(rho): return g*(math.floor(2*(rho+4)/3)+1)**3
for rho in (1,5,10,20,50):
    s=0.0; r=rho
    for j in range(200):
        s+=P(r); r*=4/9
        if r<0.01: break
    print(f"rho={rho:3d}  P(rho)={P(rho):6d}  c*(rho)~{s:9.1f}  c*/rho^3={s/rho**3:.3f}")
# ratio of geometric cubic sum: 1/(1-(4/9)^3)
print("cubic-sum amplification 1/(1-(4/9)^3) =", 1/(1-(4/9)**3))
