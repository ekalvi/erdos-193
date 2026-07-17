"""Follow-up: pin the resonance structurally. Is the M3(a) resonance a-INDEPENDENT?
Baseline M_BAL3 on a box big enough to contain (3,0,0). M4 resonance. And the
structural reason: integer + equal-moduli + irrational-angle => non-normal => O(1)
shear entries => a-independent resonance channel M_k(e) in E."""
from itertools import product
def M3(a,b=1): return [[a,0,0],[0,0,-a*a],[0,1,-b]]
def M4(a,b,c): return [[0,-a*a,0,0],[1,-b,0,0],[0,0,0,-a*a],[0,0,1,-c]]
def mv(A,v):
    n=len(A); return tuple(sum(A[i][k]*v[k] for k in range(n)) for i in range(n))

def res(A,E,name):
    Eset=set(E); n=len(E[0]); hits=[]
    for e in E:
        if e==(0,)*n: continue
        if mv(A,e) in Eset: hits.append((e,mv(A,e)))
    print(f"  {name}: {len(hits)} resonant pairs"+(f"  e.g. {hits[0]}" if hits else "  NON-RESONANT"))
    return len(hits)

print("baseline M_BAL3 on {-4..4}^3 (must contain (1,0,0)->(3,0,0)):")
E3big=[v for v in product(range(-4,5),repeat=3)]
res([[3,0,0],[0,0,-3],[0,3,-1]],E3big,"M_BAL3")
print("  M_BAL3 sends (1,0,0) ->",mv([[3,0,0],[0,0,-3],[0,3,-1]],(1,0,0)))

print("\nM3(a) resonance count vs a on {-2..2}^3 (is it a-INDEPENDENT? persists for all a?):")
E3=[v for v in product(range(-2,3),repeat=3)]
for a in [2,3,4,5,7,10,20,50]:
    res(M3(a),E3,f"M3({a})")

print("\n  The a-independent channel: M3(a) sends (0,-1,0) ->",mv(M3(9),(0,-1,0)),
      " and (0,-2,0)->",mv(M3(99),(0,-2,0))," (last two coords a-independent: (0, y, ...)-> z-shear).")

print("\nM4 double-rotation resonance on {-2..2}^4:")
E4=[v for v in product(range(-2,3),repeat=4)]
for (a,b,c) in [(3,1,2),(4,2,3),(5,1,3)]:
    res(M4(a,b,c),E4,f"M4({a},{b},{c})")

print("\nMILDLY-accelerating variant M3(a) with a=2,2,3,3,4,... resonance persists too:")
for a in [2,3]:
    res(M3(a),E3,f"M3({a}) (mild)")
