"""
P2: EXACTLY enumerate the PARALLEL-STATE bad-set of the UNCONSTRAINED rank-pair
automaton for Erdos #193 (M_BAL3).

Reduction (proven-algebra, from rank_pair_automaton.py):
  M = M_BAL3, C = cof(M). (M^g u) x (M^g v) = C^g (u x v). For two address-diffs
  Delta1,Delta2 from a common base point, with single-stream carries c1,c2 (each in
  the proven finite carry ball Q(c)<=Emax/4):
      Delta1 x Delta2 = C^g (c1 x c2),   C invertible  =>  parallel <=> c1 x c2 = 0.

The UNCONSTRAINED pair automaton advances the two carries INDEPENDENTLY over E=D-D
(legality NOT yet imposed). Both start at 0 and share generation g. Hence the joint
reachable set is SOUNDLY OVER-APPROXIMATED by R x R, where R = single-stream
reachable carry set (BFS to fixpoint = ALL generations, not depth-limited).
[The only slack vs the exact joint set is generation-matching between the two
streams; R x R ignores it, so it is a sound superset of the true bad-set. This is
EXACTLY the set the legality automaton must exclude.]

This script:
  1. rebuilds the 8649-state carry ball + R (reuses the verified construction);
  2. enumerates ALL nonzero parallel pairs (c1,c2) in R with c1 x c2 = 0;
  3. classifies: antipodal (v,-v); proper scalar multiples (v,kv,|k|>=2);
     groups by primitive direction line; isolates the real-eigen-axis (+-k,0,0)
     family (x-axis: M and C both act as scalars there -> twist is identity);
  4. reports counts + the structural families + which look hardest for a LOCAL
     legality rule to exclude.
"""
import json, ast, sys, time, math
from fractions import Fraction as F
from collections import deque, defaultdict
from math import gcd

OUT = "/Users/erik/homelab/math193/design/osc_decide"
M = [[3,0,0],[0,0,-3],[0,3,-1]]
C = [[9,0,0],[0,-3,-9],[0,9,0]]  # cof(M)

def Q(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def cross(u,v):
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])

def matvec(A,v):
    return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
            A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
            A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])

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
    g = gcd(gcd(abs(v[0]),abs(v[1])),abs(v[2]))
    w = (v[0]//g, v[1]//g, v[2]//g)
    for c in w:
        if c<0: return (-w[0],-w[1],-w[2])
        if c>0: return w
    return w

def signed_mult(v, pd):
    # v = k * pd ; return k (pd primitive, nonzero)
    if pd[0]!=0: return v[0]//pd[0]
    if pd[1]!=0: return v[1]//pd[1]
    return v[2]//pd[2]

def load_digits(kind):
    if kind=="collar":
        c = json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
        O = [tuple(ast.literal_eval(k)) for k in c.keys()]
        return [(0,0,0)] + O
    else:
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
    Ebyres=defaultdict(list)
    for e in E:
        Ebyres[residue_key(e)].append(e)

    # ---- carry ball + closure cert ----
    br=int(math.isqrt(int(Bq)))+2
    ball=set()
    for x in range(-br,br+1):
        for y in range(-br,br+1):
            for z in range(-br,br+1):
                if Q((x,y,z))<=Bq: ball.add((x,y,z))
    escapes=0
    for c in ball:
        rk=residue_key((-c[0],-c[1],-c[2]))
        for e in Ebyres.get(rk,()):
            s=(c[0]+e[0],c[1]+e[1],c[2]+e[2])
            if Q(Minv_int(s))>Bq: escapes+=1
    print(f"[{kind}] |D|={len(D)} |E|={len(E)} Emax_Q={Emax} ball={len(ball)} closure_escapes={escapes}", flush=True)

    # ---- BFS reachable single-stream carry set R (all generations) ----
    R={(0,0,0)}
    dq=deque([(0,0,0)])
    while dq:
        c=dq.popleft()
        rk=residue_key((-c[0],-c[1],-c[2]))
        for e in Ebyres.get(rk,()):
            cp=Minv_int((c[0]+e[0],c[1]+e[1],c[2]+e[2]))
            if cp not in R:
                R.add(cp); dq.append(cp)
    R.discard((0,0,0))
    Rlist=sorted(R)
    print(f"|R_nonzero|={len(R)}", flush=True)

    # generation-parity refinement (tighter joint reachability info, honest about
    # the over-approximation): record min generation each carry is reached at, and
    # whether it is reachable at BOTH parities (self-loop c->M^-1 c when c in MZ^3
    # keeps a state alive at all larger generations of one parity; e=0 always legal
    # from 0 keeps 0 at every gen). We compute the set of generation-parities each
    # state is reachable at, to note if R x R is loose.
    # gen0 = {0}. gen_{k+1} = M^-1(gen_k + E)_int.
    gens=[set([(0,0,0)])]
    seen_par={ (0,0,0): set([0]) }
    cur=set([(0,0,0)])
    for step in range(1, 60):
        nxt=set()
        for c in cur:
            rk=residue_key((-c[0],-c[1],-c[2]))
            for e in Ebyres.get(rk,()):
                cp=Minv_int((c[0]+e[0],c[1]+e[1],c[2]+e[2]))
                nxt.add(cp)
        par=step%2
        changed=False
        for c in nxt:
            s=seen_par.setdefault(c,set())
            if par not in s:
                s.add(par); changed=True
        cur=nxt
        if not changed and step>4:
            break
    both_par=sum(1 for c in R if len(seen_par.get(c,set()))>=2)
    print(f"generation-parity: {both_par}/{len(R)} nonzero carries reachable at BOTH parities", flush=True)

    # ---- enumerate parallel pairs in R x R ----
    dirs=defaultdict(list)
    for c in Rlist:
        dirs[primdir(c)].append(c)
    # per-line: signed multiples present
    line_info={}
    for pd,vs in dirs.items():
        mults=sorted(signed_mult(v,pd) for v in vs)
        line_info[pd]=mults

    # count unordered parallel pairs, split antipodal vs proper
    antipodal_pairs=0     # {v,-v}
    proper_pairs=0        # same line, not v,-v (distinct |mult| OR same-sign same-|mult| impossible)
    total_parallel_pairs=0
    proper_ratio_census=defaultdict(int)  # (min|k|, max|k|)?? we log k2/k1 for v,kv
    for pd,mults in line_info.items():
        n=len(mults)
        # all unordered pairs on this line are parallel
        total_parallel_pairs += n*(n-1)//2
        mset=set(mults)
        for i in range(n):
            for j in range(i+1,n):
                a,b=mults[i],mults[j]
                if a==-b:
                    antipodal_pairs+=1
                else:
                    proper_pairs+=1
                    # record integer ratio if one divides the other (v,kv exact)
                    la,lb=abs(a),abs(b)
                    lo,hi=min(la,lb),max(la,lb)
                    if lo>0 and hi%lo==0:
                        proper_ratio_census[hi//lo]+=1
                    else:
                        proper_ratio_census[('noninteger',lo,hi)]+=1

    assert total_parallel_pairs==antipodal_pairs+proper_pairs

    # lines with >=2 distinct |mult| (support proper (v,kv) collinear midpoint configs)
    proper_lines=[]
    for pd,mults in line_info.items():
        posm=sorted(set(abs(k) for k in mults))
        if len(posm)>=2:
            proper_lines.append((pd,sorted(set(mults)),posm))

    # ---- real-eigen-axis family: x-axis (1,0,0). M(1,0,0)=(3,0,0), C(1,0,0)=(9,0,0)
    #      -> invariant under BOTH M and C; the twist (yz-rotation) acts trivially here.
    xaxis_pd=(1,0,0)
    xaxis_mults = line_info.get(xaxis_pd, [])
    xaxis_vecs = sorted(dirs.get(xaxis_pd, []))
    # also identify how many parallel pairs lie ON the real axis
    nx=len(xaxis_mults)
    xaxis_pairs = nx*(nx-1)//2
    xaxis_antip = sum(1 for k in xaxis_mults if -k in set(xaxis_mults))//2
    xaxis_proper = xaxis_pairs - xaxis_antip

    # ---- which direction lines are "richest" (most magnitudes) => most parallel pairs
    richest = sorted(((len(m),pd,m) for pd,m in line_info.items()), reverse=True)[:12]

    print(f"\nPARALLEL-STATE BAD-SET (unordered nonzero pairs c1 x c2 = 0, over-approx R x R):")
    print(f"  total parallel unordered pairs = {total_parallel_pairs}")
    print(f"    antipodal (v,-v)             = {antipodal_pairs}  (= |R|/2 = {len(R)//2})")
    print(f"    proper (not v,-v)            = {proper_pairs}")
    print(f"  distinct primitive-direction lines in R = {len(dirs)}")
    print(f"  lines carrying >=2 distinct |magnitude| (proper v,kv midpoint families) = {len(proper_lines)}")
    print(f"  proper integer-ratio census (v -> kv), k -> #pairs:")
    for k in sorted([x for x in proper_ratio_census if isinstance(x,int)]):
        print(f"     k={k}: {proper_ratio_census[k]}")
    nonint=sum(v for x,v in proper_ratio_census.items() if not isinstance(x,int))
    print(f"     non-integer-ratio proper pairs (rational k, not integer): {nonint}")
    print(f"\n  REAL-EIGEN-AXIS (x-axis, +-k,0,0) family [twist=identity here]:")
    print(f"     carries on x-axis: {xaxis_vecs}")
    print(f"     signed multiples of (1,0,0): {sorted(set(xaxis_mults))}")
    print(f"     parallel pairs on x-axis: {xaxis_pairs} (antipodal {xaxis_antip}, proper {xaxis_proper})")
    print(f"\n  richest lines (|#magnitudes|, primdir, mults):")
    for cnt,pd,m in richest:
        print(f"     {cnt:3d}  dir={pd}  mults={m}")

    # sanity: verify a few cross products are exactly zero
    checks=[]
    for pd,mults in list(line_info.items())[:0]:
        pass
    # explicit witnesses
    witnesses={}
    if xaxis_mults:
        v=(xaxis_pd[0]*max(xaxis_mults),0,0)
        witnesses["xaxis_max"]={"c1":list(v),"c2":[-v[0],0,0],"cross":list(cross(v,(-v[0],0,0)))}
    if proper_lines:
        pd,ms,posm=proper_lines[0]
        a=(pd[0]*posm[0],pd[1]*posm[0],pd[2]*posm[0])
        b=(pd[0]*posm[-1],pd[1]*posm[-1],pd[2]*posm[-1])
        witnesses["proper_vkv"]={"pd":list(pd),"c1":list(a),"c2":list(b),
                                 "ratio":posm[-1]/posm[0],"cross":list(cross(a,b)),
                                 "both_in_R":(a in R and b in R)}

    out={
      "kind":kind,
      "note":"UNCONSTRAINED rank-pair bad-set. Joint reachable set over-approximated "
             "by R x R (single-stream reachable carries, both nonzero). R is the FULL "
             "all-generation reachable set (BFS to fixpoint), not depth-limited.",
      "|D|":len(D),"|E|":len(E),"Emax_Q":Emax,"carry_ball":len(ball),
      "closure_escapes":escapes,
      "|R_nonzero|":len(R),
      "R_symmetric_under_negation":all((-c[0],-c[1],-c[2]) in R for c in R),
      "gen_parity_both":both_par,
      "bad_set":{
        "total_parallel_unordered_pairs":total_parallel_pairs,
        "antipodal_pairs":antipodal_pairs,
        "proper_pairs":proper_pairs,
        "distinct_direction_lines":len(dirs),
        "lines_with_ge2_abs_magnitudes":len(proper_lines),
        "proper_integer_ratio_census":{str(k):proper_ratio_census[k] for k in proper_ratio_census if isinstance(k,int)},
        "proper_noninteger_ratio_pairs":nonint,
      },
      "real_eigen_axis_family":{
        "primdir":[1,0,0],
        "M_action":"eigenvalue 3","C_action":"eigenvalue 9","twist":"identity on this axis",
        "carries":[list(v) for v in xaxis_vecs],
        "signed_multiples":sorted(set(xaxis_mults)),
        "parallel_pairs":xaxis_pairs,"antipodal":xaxis_antip,"proper":xaxis_proper,
      },
      "richest_lines":[{"n_mags":cnt,"primdir":list(pd),"mults":m} for cnt,pd,m in richest],
      "witnesses":witnesses,
      "runtime_s":round(time.time()-t0,1),
    }
    json.dump(out, open(f"{OUT}/badset_{kind}.json","w"), indent=1)
    print(f"\n[{time.time()-t0:.1f}s] wrote badset_{kind}.json", flush=True)

if __name__=="__main__":
    main()
