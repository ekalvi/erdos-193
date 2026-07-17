"""
MOVE-2 RANK / PARALLELISM automaton for Erdos #193.

Reduction (exact, proven-algebra):
  M = M_BAL3, C = cof(M) = [[9,0,0],[0,-3,-9],[0,9,0]], det C = 729, invertible.
  (M^g u) x (M^g v) = C^g (u x v)  [inductive from (Mu)x(Mv)=C(u x v)].
  For an address-difference Delta = sum_{j=0..g} M^j delta_j (delta in E=D-D),
  the M^{-g}-normalized carry is c_g = M^{-g} Delta  (single-stream carry automaton
  state; stays in the finite Q-ball Q(c) <= Emax/4 -- the SAME proven 8649-state
  finiteness cert as self-avoidance).
  For TWO address-differences Delta1, Delta2 (from a common base point) with carries
  c1_g, c2_g:   Delta1 x Delta2 = C^g (c1_g x c2_g).
  C invertible  =>  Delta1 x Delta2 = 0  <=>  c1_g x c2_g = 0.

So COLLINEAR (parallel Delta1,Delta2) <=> the two normalized carries are PARALLEL.
The pair automaton = product of two single-stream automata over E; the "rank" is
read off at the end as c1 x c2.  This DODGES ST2's open risk (bilinear alphabet
blow-up): no C-carry over {a x M^m b}, alphabet stays E (finite).

This script:
  1. builds E=D-D, the carry ball, verifies closure (finiteness cert);
  2. BFS the single-stream reachable carry set R from 0 (unconstrained: all e in E);
  3. tests whether R contains PARALLEL nonzero distinct vectors (=> unconstrained
     cross product CAN vanish). Reports the structure (symmetry, directions,
     nontrivial non-antipodal parallel pairs, minimal proper (v,2v) witnesses).
"""
import json, ast, sys, time, math
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

M = [[3,0,0],[0,0,-3],[0,3,-1]]
C = [[9,0,0],[0,-3,-9],[0,9,0]]  # cof(M)

def Q(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def matvec(A,v):
    return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
            A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
            A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])

def cross(u,v):
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])

def Minv_frac(v):
    return (F(v[0],3), F(-v[1],9)+F(v[2],3), F(-v[1],3))

def in_MZ(v):
    r = Minv_frac(v)
    return r[0].denominator==1 and r[1].denominator==1 and r[2].denominator==1

def Minv_int(v):
    r = Minv_frac(v)
    return (int(r[0]), int(r[1]), int(r[2]))

def residue_key(v):
    r = Minv_frac(v)
    return tuple((x - (x.numerator//x.denominator)) for x in r)

def primdir(v):
    if v==(0,0,0): return None
    g = gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    w = (v[0]//g, v[1]//g, v[2]//g)
    for c in w:
        if c<0: return (-w[0],-w[1],-w[2])
        if c>0: return w
    return w

def load_digits(kind):
    if kind=="collar":
        c = json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
        O = [tuple(ast.literal_eval(k)) for k in c.keys()]
        return [(0,0,0)] + O
    else:  # menu-diff
        from itertools import product
        menu=[v for v in product((-2,-1,0,1,2),repeat=3) if v!=(0,0,0)]
        S=set((a[0]-b[0],a[1]-b[1],a[2]-b[2]) for a in menu for b in menu)
        return sorted(S)

def main():
    kind = sys.argv[1] if len(sys.argv)>1 else "collar"
    t0=time.time()
    D = load_digits(kind)
    Eset=set()
    for a in D:
        for b in D:
            Eset.add((a[0]-b[0],a[1]-b[1],a[2]-b[2]))
    E=sorted(Eset)
    Emax=max(Q(e) for e in E)
    Bq = Emax/4.0
    print(f"[{kind}] |D|={len(D)} |E|={len(E)} Emax_Q={Emax} carry-ball Q(c)<={Bq}", flush=True)

    # group E by residue mod M Z^3
    Ebyres=defaultdict(list)
    for e in E:
        Ebyres[residue_key(e)].append(e)

    # ---- carry ball + closure cert ----
    br=int(math.isqrt(int(Bq)))+2
    ball=set()
    for x in range(-br,br+1):
        for y in range(-br,br+1):
            for z in range(-br,br+1):
                if Q((x,y,z))<=Bq:
                    ball.add((x,y,z))
    escapes=0; checked=0
    for c in ball:
        rk=residue_key((-c[0],-c[1],-c[2]))
        for e in Ebyres.get(rk,()):
            s=(c[0]+e[0],c[1]+e[1],c[2]+e[2])
            cp=Minv_int(s); checked+=1
            if Q(cp)>Bq: escapes+=1
    print(f"ball |{{Q<= {Bq}}}|={len(ball)}  closure legal-transitions={checked} escapes={escapes} "
          f"=> {'CLOSED (finiteness cert)' if escapes==0 else 'NOT CLOSED'}", flush=True)

    # ---- BFS reachable carry set R from 0 (unconstrained) ----
    R={(0,0,0)}
    dq=deque([(0,0,0)])
    while dq:
        c=dq.popleft()
        rk=residue_key((-c[0],-c[1],-c[2]))
        for e in Ebyres.get(rk,()):
            s=(c[0]+e[0],c[1]+e[1],c[2]+e[2])
            cp=Minv_int(s)
            if cp not in R:
                R.add(cp); dq.append(cp)
    R.discard((0,0,0))
    print(f"reachable nonzero carries |R|={len(R)} (of ball {len(ball)})", flush=True)

    # symmetry check
    sym = all((-c[0],-c[1],-c[2]) in R for c in R)
    print(f"R symmetric under negation: {sym}  => (v,-v) parallel pairs exist: {sym and len(R)>0}", flush=True)

    # distinct primitive directions
    dirs=defaultdict(list)
    for c in R:
        dirs[primdir(c)].append(c)
    print(f"distinct primitive directions in R: {len(dirs)}", flush=True)

    # proper parallel pairs: a direction line containing >=2 DISTINCT non-antipodal magnitudes
    # i.e. some primdir with >=2 vectors that are not just {v,-v}
    proper=[]
    for pd,vs in dirs.items():
        # vs are all parallel; distinct magnitudes ignoring sign?
        mags=set()
        for v in vs:
            # signed multiple along pd
            k = v[0]//pd[0] if pd[0]!=0 else (v[1]//pd[1] if pd[1]!=0 else v[2]//pd[2])
            mags.add(k)
        posmags=set(abs(k) for k in mags)
        if len(posmags)>=2:
            proper.append((pd,sorted(mags)))
    print(f"directions with >=2 distinct |magnitudes| (PROPER parallel, not just +/-): {len(proper)}", flush=True)
    if proper:
        pd,ms=proper[0]
        print(f"  example: dir {pd}, signed multiples present {ms[:12]}", flush=True)
        # explicit (v, w) proper parallel, w != +/-v
        a=(pd[0]*ms[0],pd[1]*ms[0],pd[2]*ms[0])
        b=(pd[0]*ms[-1],pd[1]*ms[-1],pd[2]*ms[-1])
        print(f"  witness a={a} b={b}  a x b = {cross(a,b)} (=0 confirms parallel), a!=+/-b: {abs(ms[0])!=abs(ms[-1])}", flush=True)

    out={
      "kind":kind,"|D|":len(D),"|E|":len(E),"Emax_Q":Emax,"carry_ball":len(ball),
      "closure_escapes":escapes,"|R_nonzero|":len(R),
      "R_symmetric":sym,"distinct_directions":len(dirs),
      "proper_parallel_directions":len(proper),
      "unconstrained_cross_can_vanish": bool(sym and len(R)>0),
      "runtime_s":round(time.time()-t0,1),
    }
    json.dump(out, open(f"/Users/erik/homelab/math193/design/osc_decide/rank_pair_{kind}.json","w"),indent=1)
    print(f"[{time.time()-t0:.1f}s] wrote rank_pair_{kind}.json", flush=True)

if __name__=="__main__":
    main()
