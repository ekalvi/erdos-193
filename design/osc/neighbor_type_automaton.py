"""
NEIGHBOR-TYPE / STITCH-INCIDENCE AUTOMATON for the ratio-3 Q-self-similar
graph-directed system (Erdos #193 construction).  Bandt-Graf finite-type test.

Exact Q-metric: M = 3.O, O Q-orthogonal, M^T Q M = 9 Q, Q(x,y,z)=x^2+6y^2-2yz+6z^2.
Key exact identity used throughout:  Q(M.n) = n^T (M^T Q M) n = 9 Q(n).

TRANSLATION-PART neighbor automaton (the Bandt-Graf neighbor set, quotiented by
the ratio-3 similarity).  A neighbor TYPE is the relative root offset delta of a
meeting pair of cylinders, pulled back to unit (child) scale.

 * SEED: generation-1 meeting pairs.  Roots R_a = M.a, R_a' = M.a'.  Two gen-1
   cylinders can meet (their unit-scale bounding balls of Q-radius rho_c overlap,
   or the seed meeting radius R = rho_c+eta) iff Q(R_a'-R_a) <= (T*3)^2, i.e.
   pulled back delta = M.(a'-a) with Q(delta) <= (3T)^2.  Since Q(M.n)=9Q(n) this
   is Q(a'-a) <= T^2 : an EXACT integer lattice ball.

 * TRANSITION (Bandt-Graf, expanding IFS of ratio 3):
      delta  ->  M.delta + (o' - o),      o,o' in child-offset menu O,
   retain iff Q(delta_new) <= T_meet^2 (the two child cylinders still meet).
   O = interior offsets of the menu-closure connector words (union {0} = anchor
   child).  |O|=2103, distinct differences D = {o'-o}: 15,545, all Q(D)<=2116.

FINITENESS: delta_new in Z^3 (M.delta in M.Z^3 subset Z^3, o'-o in Z^3), and
Q(delta_new) <= T_meet^2 -> a bounded integer lattice ball -> FINITE ambient.
The reachable set is a subset -> FINITE TYPE (Ngai-Wang / Zerner WSC) provided the
BFS closes; it must, the ambient is finite.  Deliverable = the reachable COUNT,
the min nonzero separation (OSC vs WSC), and the max child-incidence (refill bound).

Meeting thresholds (Q-radii, from nuniform_covering_bound / dg_closure_uniform):
  rho_c = sqrt(745) = 27.2947  (proven reach-to-source, per generation)
  eta   = sqrt(15)  = 3.8730   (min-separation slack)
  R     = rho_c + eta = 31.168 ; seed pullback bound 3R  (Q^2 = 8742)
  T_meet = 2*rho_c  (two unit cylinders' bounding balls touch) ; Q^2 = 2980
"""
import json, math, ast
from collections import defaultdict, deque

M = ((3,0,0),(0,0,-3),(0,3,-1))

def Q(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def matvec(A,v):
    return tuple(A[r][0]*v[0]+A[r][1]*v[1]+A[r][2]*v[2] for r in range(3))

RHO_C2 = 745
ETA2   = 15
RHO_C  = math.sqrt(RHO_C2)
ETA    = math.sqrt(ETA2)
R      = RHO_C + ETA
# seed pullback ball:  Q(delta) <= (3R)^2  <=>  Q(a'-a) <= R^2
R2_seed  = int(math.floor((R)**2))              # 971  (a'-a lattice ball)
# recursive meeting ball for the automaton (two unit cylinders bounding-balls touch)
T_MEET   = 2*RHO_C
T2_MEET  = int(math.floor(T_MEET*T_MEET))        # ~2980

def load_offsets():
    c = json.load(open('/Users/erik/homelab/math193/collar_multiplicity4.json'))
    offs = [tuple(ast.literal_eval(k)) for k in c.keys()]
    S = set(offs) | {(0,0,0)}
    diffs = set()
    L = list(S)
    for o in L:
        for o2 in L:
            diffs.add((o2[0]-o[0], o2[1]-o[1], o2[2]-o[2]))
    return sorted(S), sorted(diffs)

def lattice_ball(R2):
    """all n in Z^3 with Q(n) <= R2."""
    out=[]
    b = int(math.isqrt(R2))+1
    for x in range(-b,b+1):
        for y in range(-b,b+1):
            for z in range(-b,b+1):
                if x*x+6*y*y-2*y*z+6*z*z <= R2:
                    out.append((x,y,z))
    return out

def main():
    print("=== NEIGHBOR-TYPE (translation part) automaton ===", flush=True)
    print(f"rho_c=sqrt(745)={RHO_C:.4f} eta=sqrt(15)={ETA:.4f} R={R:.4f}", flush=True)
    print(f"seed lattice ball Q(a'-a)<= {R2_seed}", flush=True)
    print(f"recursive meeting ball Q(delta)<= {T2_MEET} (T_meet=2*rho_c)", flush=True)

    O, D = load_offsets()
    print(f"child-offset menu |O|={len(O)} distinct diffs |D|={len(D)} maxQ(D)={max(Q(d) for d in D)}", flush=True)

    # --- SEED set: gen-1 meeting pairs, pulled back delta_seed = M.(a'-a) ---
    seed_n = lattice_ball(R2_seed)          # a'-a candidates
    print(f"seed |{{a'-a : Q<= {R2_seed}}}| = {len(seed_n)} (= N_uniform-grade count)", flush=True)
    seeds = set()
    for n in seed_n:
        if n == (0,0,0):
            continue
        d = matvec(M, n)                    # delta in M.Z^3, Q(d)=9Q(n)
        if Q(d) <= T2_MEET:
            seeds.add(d)
    print(f"seeds within recursive meeting ball: {len(seeds)}", flush=True)

    # --- BFS forward closure under delta -> M.delta + D, clipped to meeting ball ---
    # (this is the expanding Bandt-Graf neighbor recursion; finiteness = ball is finite)
    reachable = set(seeds)
    frontier = deque(seeds)
    steps = 0
    while frontier:
        delta = frontier.popleft()
        Md = matvec(M, delta)
        for dd in D:
            nd = (Md[0]+dd[0], Md[1]+dd[1], Md[2]+dd[2])
            if Q(nd) <= T2_MEET and nd not in reachable:
                reachable.add(nd)
                frontier.append(nd)
        steps += 1
        if steps % 2000 == 0:
            print(f"  BFS: expanded {steps}, reachable {len(reachable)}, frontier {len(frontier)}", flush=True)

    print(f"\nBFS CLOSED. reachable translation-types = {len(reachable)}", flush=True)

    # min nonzero separation (OSC translation-part quantum)
    nz = [Q(d) for d in reachable if d != (0,0,0)]
    has_zero = (0,0,0) in reachable
    minnz = min(nz) if nz else None
    print(f"contains delta=0 (root coincidence): {has_zero}", flush=True)
    print(f"min nonzero Q(delta) over reachable = {minnz}  -> min Q-separation of roots = {math.sqrt(minnz):.4f}", flush=True)

    # incidence / refill bound: for a single cylinder, # child sub-cylinders (arcs)
    # emitted within the incidence window = number of interior offsets in a menu word
    # PLUS the anchor child; per proven caps interiors/word<=4.  Level-uniform because
    # types are level-free.  Report the child-count spectrum from the offset menu.
    # Max stitch children within one meeting window (Q<=rho_c) around any child root:
    #   count offsets O within Q-radius that a single neighbor can donate.
    from itertools import product
    # incidence = max over reachable types of (# distinct child-arc offsets landing in
    # the shared meeting window) -- bounded by |O within a rho_c ball|; report.
    incid_window = [o for o in O if Q(o) <= RHO_C2]
    print(f"\nrefill/incidence: interior offsets within Q<=rho_c window: {len(incid_window)} "
          f"(loose); proven per-word interiors<=4, per-arc donation<=3 (measured).", flush=True)

    out = {
        "rho_c": RHO_C, "eta": ETA, "R": R,
        "R2_seed_lattice": R2_seed,
        "T2_meet": T2_MEET,
        "menu_O": len(O), "diffs_D": len(D), "maxQ_D": max(Q(d) for d in D),
        "seed_lattice_count": len(seed_n),
        "seeds_in_meeting_ball": len(seeds),
        "reachable_translation_types": len(reachable),
        "contains_zero_root_coincidence": has_zero,
        "min_nonzero_Q_delta": minnz,
        "min_Q_root_separation": math.sqrt(minnz) if minnz else None,
        "incidence_window_offsets_le_rhoc": len(incid_window),
        "finite": True,
        "note": "translation-part Bandt-Graf neighbor set; FINITE (bounded Z^3 ball). "
                "Full type = this x (78728 NP-HC side states)^2, also finite -> FINITE TYPE = WSC. "
                "min nonzero root-sep>0 rules out ROOT-coincidence overlaps, but LIMIT-ARC "
                "overlap (OSC) needs finite-depth arc-gap positivity, decided separately.",
    }
    json.dump(out, open('/Users/erik/homelab/math193/design/osc/neighbor_type_automaton_results.json','w'), indent=1)
    print("\nWROTE design/osc/neighbor_type_automaton_results.json", flush=True)

if __name__ == "__main__":
    main()
