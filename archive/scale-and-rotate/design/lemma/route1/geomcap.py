"""Geometric capacity = #undirected primitive directions with sup-norm<=R.
This is the ONLY bound triple-free + (locally-vacuous) kappa_3 delivers:
N-1 <= #lines through anchor meeting ball = geomcap(2*rho).  Growth ~ R^3."""
from math import gcd, log
def prim(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    w=(v[0]//g,v[1]//g,v[2]//g)
    for c in w:
        if c: return w if c>0 else (-w[0],-w[1],-w[2])
def cap(R):
    S=set()
    for x in range(-R,R+1):
        for y in range(-R,R+1):
            for z in range(-R,R+1):
                if x or y or z: S.add(prim((x,y,z)))
    return len(S)//2
print("rho  2rho  geomcap(2rho)=Route1_bound(N-1)   target_C*rho+1(C=2.5)")
prev=None
for rho in [1,2,3,4,5,7,10]:
    R=2*rho; c=cap(R)
    growth=(log(c/prev[1])/log(R/prev[0])) if prev else float('nan')
    print(f"{rho:3d} {R:4d}  {c:6d}   (route1 caps N at {c+1})   target~{2.5*rho+1:.0f}   loglog_growth_exp={growth:.2f}")
    prev=(R,c)
