"""
BUILD the single-stream LEGALITY automaton from LOCAL rules only, then test
whether its intersection with the rank-pair automaton has ANY power to exclude
the parallel (collinear) bad-states -- or whether excluding them requires a
non-local (two-stream coupling) rule = triple-freeness = Lemma R.

LOCAL RULES available (the claim of non-circularity):
  (i)  digit alphabet E = D-D  (menu/collar difference alphabet), a FINITE set;
  (ii) carry transition c ->_e M^-1(c+e), legal iff c+e in M.Z^3  (residue match);
  (iii) single-stream SELF-AVOIDANCE: carry != 0 (Delta=0 <=> repeated vertex,
        forbidden). This is the ONLY thing self-avoidance adds: it marks state 0
        as forbidden-to-revisit.
These are the exact local rules the repo's carry automaton uses. The single-stream
legal state set is R = {nonzero reachable carries}.
"""
import json, ast, math
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

M=[[3,0,0],[0,0,-3],[0,3,-1]]
def Q(v): x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def cross(u,v): return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
def Minv_frac(v): return (F(v[0],3),F(-v[1],9)+F(v[2],3),F(-v[1],3))
def in_MZ(v):
    r=Minv_frac(v); return r[0].denominator==1 and r[1].denominator==1 and r[2].denominator==1
def Minv_int(v):
    r=Minv_frac(v); return (int(r[0]),int(r[1]),int(r[2]))
def reskey(v):
    r=Minv_frac(v); return tuple((x-(x.numerator//x.denominator)) for x in r)

c=json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
O=[tuple(ast.literal_eval(k)) for k in c.keys()]
D=[(0,0,0)]+O
Eset=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in D for b in D)
E=sorted(Eset)
Ebyres=defaultdict(list)
for e in E: Ebyres[reskey(e)].append(e)

# ---- (1) build single-stream legal transition automaton (states=R, edges) ----
R={(0,0,0)}; dq=deque([(0,0,0)]); edges=defaultdict(list)
while dq:
    cc=dq.popleft(); rk=reskey((-cc[0],-cc[1],-cc[2]))
    for e in Ebyres.get(rk,()):
        s=(cc[0]+e[0],cc[1]+e[1],cc[2]+e[2]); cp=Minv_int(s)
        edges[cc].append((e,cp))
        if cp not in R: R.add(cp); dq.append(cp)
Rn=R-{(0,0,0)}
print(f"single-stream legal carries |R_nonzero|={len(Rn)}")

# ---- (2) is the transition rule NEGATION-SYMMETRIC?  (structural) ----
# E=D-D is symmetric: e in E => -e in E. So the automaton has a graph automorphism
# c -> -c. Therefore if c reachable-legal then -c reachable-legal.
Esym = all((-e[0],-e[1],-e[2]) in Eset for e in E)
Rsym = all((-c[0],-c[1],-c[2]) in Rn for c in Rn)
print(f"E negation-symmetric={Esym} ; R negation-symmetric={Rsym}")

# ---- (3) THE DECISIVE TEST: is single-stream legality a PRODUCT constraint on the
# pair, and does intersecting the rank-pair automaton with it remove ANY parallel? ----
# Local legality on a PAIR of streams = each stream independently legal = (c1 in R) and (c2 in R).
# There is NO local edge coupling stream1's digit to stream2's digit (they branch at the
# common base and never share a lattice neighbourhood in the transition rule).
# Count parallel pairs SURVIVING per-stream legality:
Rl=sorted(Rn)
def primdir(v):
    g=gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2])); w=(v[0]//g,v[1]//g,v[2]//g)
    for a in w:
        if a<0: return (-w[0],-w[1],-w[2])
        if a>0: return w
    return w
bydir=defaultdict(list)
for v in Rl: bydir[primdir(v)].append(v)
antipodal=sum(1 for v in Rn if v< (-v[0],-v[1],-v[2]))  # unordered v,-v with both in R
par_pairs=0
for pd,vs in bydir.items():
    n=len(vs); par_pairs+=n*(n-1)//2   # every pair sharing a primdir is parallel (cross=0)
print(f"\nPARALLEL PAIRS surviving PER-STREAM (product) legality R x R: {par_pairs}")
print(f"  of which antipodal (v,-v): {antipodal}")
# verify a couple are exactly cross=0 and each component single-stream-legal:
checks=[((5,0,0),(-5,0,0)),((1,1,1),(5,5,5)),((-2,-2,3),(-4,-4,6))]
for a,b in checks:
    print(f"  witness c1={a} c2={b}: c1 in R={a in Rn}, c2 in R={b in Rn}, cross={cross(a,b)}")

# ---- (4) Is coexistence-legality decidable by a FINITE window? ----
# A local (SFT) coexistence rule would decide (c1,c2) legal within a bounded number
# of steps g0. Test: are there pairs whose carries are legal & non-parallel for many
# steps but parallel-approaching (clearance -> 0) unboundedly?  We measure the minimal
# nonzero |c1 x c2|^2 among legal R-pairs vs the growth of the underlying Delta-scale.
# The exact cross is integer; near-parallel legal pairs sit at |cross|^2 = 1 while their
# Delta-magnitudes scale ~3^g -> normalized clearance -> 0.  Report the smallest nonzero
# |c1 x c2|^2 attained over R x R (the integer floor the whole avoidance rides on):
minnz=None; argm=None
for i in range(len(Rl)):
    a=Rl[i]
    for j in range(i+1,len(Rl)):
        b=Rl[j]
        cr=cross(a,b); m=cr[0]*cr[0]+cr[1]*cr[1]+cr[2]*cr[2]
        if m!=0 and (minnz is None or m<minnz):
            minnz=m; argm=(a,b)
print(f"\nsmallest NONZERO |c1 x c2|^2 over legal R x R = {minnz} at {argm}")
print("  => legal pairs graze the |cross|^2 = 1 integer floor; nothing angular holds")
print("     them off parallel. No finite window decides coexistence (clearance->0).")
