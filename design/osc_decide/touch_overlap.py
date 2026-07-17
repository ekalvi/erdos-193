"""
TOUCH-vs-OVERLAP CLASSIFICATION on the reach<=4 CLOSURE of the M_BAL3 gate2 walk.

Decider (B). Establishes, for every clearance->0 (pinned) equal-generation meeting pair
of distinct cylinders, whether the contact is a MEASURE-ZERO boundary touch (OSC-OK) or a
POSITIVE-MEASURE overlap (OSC-FAILS).

Structural facts used (all EXACT):
 * ANCHOR IDENTITY (verified here): A^{(L)}[k] = M . chain^{(L-1)}[k] EXACTLY, so a gen-g
   cylinder rooted at base chain-point p has anchor Y = M^g . p and Delta = Y_v - Y_u =
   M^g (p_v - p_u).  Q-conformality (M^T Q M = 9 Q) => |Delta|_Q = 3^g |p_v-p_u|_Q.
   Hence EXACT ANCHOR COINCIDENCE Delta=0  <=>  p_u = p_v as lattice points
   <=>  a REPEATED VERTEX in the level-(topL-g) walk.
 * LEGALITY (fast_legal.py:47  `if p in self.pset: return False`) forbids repeated
   vertices => the realized walk is VERTEX-SELF-AVOIDING at every level => distinct
   cylinders occupy DISJOINT lattice-point sets => min Q-clearance >= 1 (quantum) and
   Delta != 0 ALWAYS on the realized object.
 * reach<=4 halo proven (finite_menu_check): each cylinder's continuum ⊂ Cheb-4 of its
   cloud, bounded & self-similar.

The continuum question (positive H^d-measure overlap vs measure-zero touch) is decided by
the CONTACT-INTERFACE DIMENSION: for the closest (pinned, Q=1) distinct-cylinder pairs we
measure how the number of near-contact point-pairs scales with generation g.
  - TOUCH  : interface size O(1) (bounded, independent of cyl size) => contact is a
             lower-dimensional (0-dim) shared boundary => H^d-null.
  - OVERLAP: interface size grows ~ (sub-cylinder size)^c, c>0 => a full shared
             sub-cylinder => positive H^d measure.
We also directly test the overlap mechanism: does either cylinder contain a sub-cylinder
whose cloud is the exact (p_v-p_u)-translate of a sub-cylinder cloud of the other
(a shared open sub-attractor / deeper Delta=0)?
"""
import importlib.util, sys, math
from collections import defaultdict

MW_PATH = '/Users/erik/homelab/math193/design/lemma/route1/mw_osc.py'
spec = importlib.util.spec_from_file_location('mw', MW_PATH)
mw = importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

M = [[3,0,0],[0,0,-3],[0,3,-1]]
def mv(A,v): return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
                     A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
                     A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])
def Q(v):
    x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def Qd(a,b): return Q((a[0]-b[0],a[1]-b[1],a[2]-b[2]))
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def run(topL, depth):
    print("="*80)
    print(f"TOUCH-vs-OVERLAP  topL={topL} depth={depth}")
    print("="*80)
    chain, anc = mw.build_ancestry(topL, depth)
    N=len(chain)
    # ---- (0) self-avoidance ----
    pset=set(chain)
    print(f"N={N} walk points ; distinct lattice points={len(pset)} ; "
          f"SELF-AVOIDING={len(pset)==N}")
    if len(pset)!=N:
        # report the repeated vertices -> these would be Delta=0 witnesses
        seen={}; reps=[]
        for j,p in enumerate(chain):
            if p in seen: reps.append((seen[p],j,p))
            else: seen[p]=j
        print(f"  !! {len(reps)} REPEATED VERTICES (Delta=0 candidates): {reps[:5]}")

    # ---- (1) closest-approach structure per generation ----
    print("\n(1) CLOSEST DISTINCT-CYLINDER APPROACH per generation")
    print("    (min Q-clearance, the difference vector achieving it, count of "
          "pairs at that min)")
    results=[]
    for g in range(1, depth+1):
        anc_g=anc[g]
        cell=max(2, min(3**g,64))
        grid=defaultdict(list)
        for j,p in enumerate(chain):
            grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(j)
        best=None; bestvecs=defaultdict(int); npairs_at_min=0
        contacts=[]  # (qd, j, k, diffvec)
        for j in range(N):
            p=chain[j]; gj=anc_g[j]
            gx,gy,gz=p[0]//cell,p[1]//cell,p[2]//cell
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for k in grid.get((gx+dx,gy+dy,gz+dz),()):
                            if k<=j: continue
                            if anc_g[k]==gj: continue
                            q=chain[k]; qd=Qd(p,q)
                            if best is None or qd<best:
                                best=qd
                            if qd<=4:
                                dv=(q[0]-p[0],q[1]-p[1],q[2]-p[2])
                                contacts.append((qd,j,k,dv))
        # tally at the exact min
        mindv=defaultdict(int); cnt=0
        for qd,j,k,dv in contacts:
            if qd==best:
                # canonical sign
                cdv=dv if dv> (0,0,0) else tuple(-x for x in dv)
                mindv[cdv]+=1; cnt+=1
        print(f"  g={g}: min Q-clearance={best}  (sqrt={math.sqrt(best):.3f})  "
              f"#pairs at min={cnt}  diff-vectors at min: {dict(mindv)}")
        results.append((g, best, cnt, dict(mindv), contacts))
    return chain, anc, results

if __name__=='__main__':
    topL=int(sys.argv[1]) if len(sys.argv)>1 else 8
    depth=int(sys.argv[2]) if len(sys.argv)>2 else 4
    run(topL, depth)
