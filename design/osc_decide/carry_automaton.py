"""
DECIDER (A) - Delta=0 EXACT ANCHOR-COINCIDENCE search for the M_BAL3 ratio-3
self-similar walk (Erdos #193 OSC).

SETUP.  M = ((3,0,0),(0,0,-3),(0,3,-1)), det 27, M^T Q M = 9 Q,
Q(x,y,z)=x^2+6y^2-2yz+6z^2 (so |M v|_Q = 3|v|_Q exactly).

For two equal-generation words u!=v (|u|=|v|=g) the Bandt-Graf neighbor map
h_{u,v}=f_u^{-1} o f_v is the PURE TRANSLATION x -> x + Delta with
   Delta = Y_v - Y_u,   Y_w = sum_{j=1..g} M^{g-j} d_{w_j},  d in digit set D.
Delta is an INTEGER lattice vector; equal-gen OSC-failure <=> some distinct legal
meeting pair has Delta = 0 EXACTLY (exact anchor coincidence / exact overlap).

DIGIT SET.  A level-(k+1) point is  M.p + d  with d in D = {0} U O, O = the set of
connector INTERIOR offsets (collar), |O|=2102, maxQ(O)=529.  (Verified from
collar_multiplicity4.json + the anchor recursion A_{iw}=M A_w + d_i.)

CARRY AUTOMATON (decides Delta=0 for ALL g at once).
Write Delta = sum_{k=0..g-1} M^k f_k = 0 with f_k = e_{g-k}, e in E=D-D.
Process low-to-high: c_0=0, c_{k+1}=M^{-1}(c_k+f_k) legal iff c_k+f_k in M Z^3
(exact-integer divisibility).  c_g=0 <=> sum M^k f_k = 0.
Since |c_{k+1}|_Q = (1/3)|c_k+f_k|_Q <= (1/3)(|c_k|_Q+Emax_Q), every reachable
carry obeys  Q(c) <= Emax_Q/4  (EXACT constant bound), a FINITE state set.
A nontrivial Delta=0 witness  <=>  a closed walk 0->0 using >=1 nonzero digit e.

This script (phase 1):
  - pins D, E exactly; residue (mod M Z^3) census of the digits;
  - builds the carry-state ball, VERIFIES the Q(c)<=Emax/4 bound is closed under
    transitions (rigorous finiteness certificate);
  - finds whether the UNCONSTRAINED automaton has a nontrivial 0->0 cycle
    (expected YES per prior rounds -> lattice/norm alone does NOT close Delta=0);
  - reports the minimal unconstrained witness and its digit differences.
Legality intersection is phase 2 (carry_legal.py).
"""
import json, ast, pickle, sys, os, time
from fractions import Fraction as F
from collections import deque, defaultdict

OUT = "/Users/erik/homelab/math193/design/osc_decide"
M = [[3,0,0],[0,0,-3],[0,3,-1]]

def Q(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def matvec(A,v):
    return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
            A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
            A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])

# exact M^-1 = [[1/3,0,0],[0,-1/9,1/3],[0,-1/3,0]]
def Minv_frac(v):
    return (F(v[0],3), F(-v[1],9)+F(v[2],3), F(-v[1],3))

def in_MZ(v):
    r = Minv_frac(v)
    return all(x.denominator==1 for x in r)

def Minv_int(v):
    # assumes v in M Z^3
    r = Minv_frac(v)
    return (int(r[0]), int(r[1]), int(r[2]))

def residue_key(v):
    # coset of v mod M Z^3 : frac(M^-1 v) in (Q/Z)^3 -- exact canonical key
    r = Minv_frac(v)
    return tuple((x - (x.numerator//x.denominator)) for x in r)

def load_digits():
    c = json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
    O = [tuple(ast.literal_eval(k)) for k in c.keys()]
    assert (0,0,0) not in O
    D = [(0,0,0)] + O
    return D, O

def main():
    t0=time.time()
    D, O = load_digits()
    print(f"|O|={len(O)}  |D|={len(D)}  maxQ(O)={max(Q(o) for o in O)}", flush=True)

    # E = D - D
    Eset = set()
    for a in D:
        for b in D:
            Eset.add((a[0]-b[0], a[1]-b[1], a[2]-b[2]))
    E = sorted(Eset)
    Emax = max(Q(e) for e in E)
    print(f"|E=D-D|={len(E)}  Emax_Q=max Q(e)={Emax}  => carry bound Q(c)<={Emax//4} (Emax/4={Emax/4})", flush=True)

    # ---- residue census of the digits ----
    res = defaultdict(list)
    for d in D:
        res[residue_key(d)].append(d)
    print(f"\nRESIDUE CENSUS mod M.Z^3 (27 cosets):", flush=True)
    print(f"  #distinct residues occupied by D = {len(res)} (of 27)", flush=True)
    sizes = sorted((len(v) for v in res.values()), reverse=True)
    print(f"  coset occupancy sizes (top): {sizes[:10]} ...", flush=True)
    print(f"  #cosets with >=2 digits (residue-collision cosets) = {sum(1 for v in res.values() if len(v)>=2)}", flush=True)
    # this is why the clean 'distinct-residue' one-line proof fails for full D:
    # many digits share a residue -> low-digit cancellation e_g in M Z^3 is possible.

    # ---- build carry-state ball  {c : Q(c) <= Emax/4} ----
    bound = Emax // 4        # integer bound (Q integer-valued); Q(c)<=Emax/4
    # Q integer valued so Q(c)<=Emax/4 == Q(c) <= floor(Emax/4) since 4|... check:
    # Emax may not be divisible by 4; the true bound is Q(c) <= Emax/4 (real). Q integer
    # so Q(c) <= floor(Emax/4).
    import math
    Bq = Emax/4.0
    # enumerate integer ball Q(c) <= Bq
    br = int(math.isqrt(int(Bq))) + 2
    states = []
    for x in range(-br,br+1):
        for y in range(-br,br+1):
            for z in range(-br,br+1):
                if Q((x,y,z)) <= Bq:
                    states.append((x,y,z))
    states = set(states)
    print(f"\ncarry ball |{{Q(c)<={Bq}}}| = {len(states)} states", flush=True)

    # ---- verify closure: every legal transition from an in-ball state lands in-ball ----
    # transition c ->_e c' = M^-1(c+e) when c+e in M Z^3
    # We assert Q(c') <= Emax/4 for ALL c in ball, e in E with c+e in MZ.  This certifies
    # the reachable carry set never leaves the ball (finiteness cert).
    Eset_t = Eset
    escapes = 0
    checked = 0
    # only need to check reachable ones, but full closure check over ball x E is the cert:
    for c in states:
        for e in E:
            s = (c[0]+e[0], c[1]+e[1], c[2]+e[2])
            if in_MZ(s):
                cp = Minv_int(s)
                checked += 1
                if Q(cp) > Bq:
                    escapes += 1
    print(f"closure check: {checked} legal transitions from ball; escapes(Q>bound)={escapes}", flush=True)
    print(f"  => carry bound {'CLOSED (rigorous finiteness cert)' if escapes==0 else 'NOT closed!!'}", flush=True)

    # ---- UNCONSTRAINED reachability: is there a nontrivial 0->0 cycle? ----
    # Forward BFS from 0 over ALL e in E (nonzero e allowed). We want to know if 0 is
    # revisited via a path with >=1 nonzero digit -> nontrivial Delta=0 exists.
    # Build successor structure lazily.
    def succ(c):
        out=[]
        for e in E:
            s=(c[0]+e[0],c[1]+e[1],c[2]+e[2])
            if in_MZ(s):
                out.append((Minv_int(s), e))
        return out

    # BFS shortest nontrivial cycle 0->0 : BFS from each successor of 0 (via nonzero e0),
    # find shortest path back to 0. Simpler: BFS from 0 but forbid the trivial empty path.
    # shortest closed walk length using >=1 edge with nonzero e.
    # Do BFS: start states = {(succ_state, [e0]) for e0!=0 out of 0}; find first reach 0.
    print("\nUNCONSTRAINED: searching shortest nontrivial 0->0 cycle...", flush=True)
    start_edges = [(sc, e) for (sc,e) in succ((0,0,0)) if e!=(0,0,0)]
    print(f"  nonzero-digit edges out of carry 0: {len(start_edges)}", flush=True)
    # BFS
    dist = {(0,0,0):0}
    parent = {}
    dq = deque()
    found=None
    for (sc,e) in start_edges:
        if sc==(0,0,0):
            found=([e],1); break
        if sc not in dist:
            dist[sc]=1; parent[sc]=((0,0,0),e); dq.append(sc)
    if not found:
        while dq and not found:
            c=dq.popleft()
            for (sc,e) in succ(c):
                if sc==(0,0,0):
                    # reconstruct
                    path=[e]; cur=c
                    while cur!=(0,0,0):
                        pc,pe=parent[cur]; path.append(pe); cur=pc
                    path.reverse()
                    found=(path, dist[c]+1); break
                if sc not in dist:
                    dist[sc]=dist[c]+1; parent[sc]=(c,e); dq.append(sc)
    if found:
        path,ln=found
        print(f"  NONTRIVIAL 0->0 CYCLE FOUND, length {ln}; digit-diffs e_k = {path}", flush=True)
        # verify: sum_{k} M^k e_k == 0
        acc=(0,0,0); Mp=[[1,0,0],[0,1,0],[0,0,1]]
        tot=(0,0,0)
        cur=(0,0,0)
        # sum_{k=0}^{ln-1} M^k path[k]
        Mpow=[[1,0,0],[0,1,0],[0,0,1]]
        def matmul(A,B):
            return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        S=(0,0,0); P=[[1,0,0],[0,1,0],[0,0,1]]
        for k in range(ln):
            term=matvec(P,path[k]); S=(S[0]+term[0],S[1]+term[1],S[2]+term[2])
            P=matmul(M,P)
        print(f"  VERIFY sum M^k e_k = {S}  (should be 0): {'OK' if S==(0,0,0) else 'FAIL'}", flush=True)
        uncon_cycle = {"length":ln, "e_k":[list(e) for e in path], "verify_sum":list(S)}
    else:
        print("  NO nontrivial 0->0 cycle in unconstrained automaton (unexpected!)", flush=True)
        uncon_cycle = None

    out = {
        "digits": {"O":len(O),"D":len(D),"maxQ_O":max(Q(o) for o in O)},
        "E": {"size":len(E),"Emax_Q":Emax,"carry_bound_Qc_le":Emax/4},
        "residue_census": {
            "distinct_residues_occupied": len(res),
            "of_27": 27,
            "cosets_with_ge2_digits": sum(1 for v in res.values() if len(v)>=2),
            "top_occupancy_sizes": sizes[:10],
            "note":"D has 2103 digits over <=27 cosets -> the clean distinct-residue "
                   "one-line no-coincidence proof FAILS; low-digit cancellation possible.",
        },
        "carry_ball": {"Q_bound":Emax/4,"num_states":len(states),
                       "closure_escapes":escapes,
                       "bound_closed":escapes==0},
        "unconstrained_cycle": uncon_cycle,
        "runtime_s": round(time.time()-t0,1),
    }
    json.dump(out, open(f"{OUT}/carry_automaton_results.json","w"), indent=1)
    print(f"\n[{time.time()-t0:.1f}s] wrote carry_automaton_results.json", flush=True)

if __name__=="__main__":
    main()
