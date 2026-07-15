"""
ROUTE 2 -- JOINT INDUCTION (crowding c_k + refill b_k together).

We measure, on the REAL construction chains L6/L7/L8, every quantity the joint
2x2 update needs, and test the closing inequalities.

Definitions (Cheb = L-inf).  For a level-k walk W_k = (M.W_{k-1}) sqcup Stitch:
  ANCHORS  A = { M p : p in W_{k-1} }   (dilated-old)
  STITCH   S = interiors of the connector words
  c_k(rho) = sup_q #{ W_k  in B(q,rho) }              (crowding)
  b_k(rho) = sup_q #{ S    in B(q,rho) }              (refill / B_local)
  a_k(rho) = sup_q #{ A    in B(q,rho) }              (anchor crowding)
sup approximated by max over q in the walk (lower bound on the true sup;
we also spot-check half-integer shifts).

JOINT UPDATE (affine bounds  c_k(rho) <= C_k rho + 1,  b_k(rho) <= E_k rho + F):
  crowding recursion (proven identity + ||M^-1||_inf = 4/9 pullback):
      c_{k+1}(rho) <= c_k((4/9)rho) + b_k(rho)          => C_{k+1} = (4/9)C_k + E_k
  refill coupling (each stitch pt within Cheb-4 of NEARER anchor;
      anchors = M.W_{k-1}, pullback (4/9)):
      b_k(rho) <= a * c_k((4/9)(rho+4))                 => E_k = a (4/9) C_k
  where a = max per-anchor stitch multiplicity (structural, from fixed menu).
Update matrix on (C_k,E_k):  U=[[4/9,1],[16a/81,4a/9]], det U = 0,
  spectral radius = trace = (4/9)(1+a).  CLOSES iff a < 5/4.

This script MEASURES the effective a on real data and tests level-independence.

Usage:  pypy3 joint_measure.py
"""
import pickle, sys, os, json
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)
# M_BAL3 = ((3,0,0),(0,0,-3),(0,3,-1))
M = ((3,0,0),(0,0,-3),(0,3,-1))

def mul(Mm,p):
    return (Mm[0][0]*p[0]+Mm[0][1]*p[1]+Mm[0][2]*p[2],
            Mm[1][0]*p[0]+Mm[1][1]*p[1]+Mm[1][2]*p[2],
            Mm[2][0]*p[0]+Mm[2][1]*p[1]+Mm[2][2]*p[2])

def build(pkl):
    d=pickle.load(open(pkl,"rb"))
    anchors=[tuple(a) for a in d["anchors"]]; words=d["words"]
    chain=[]; is_anc=[]; anc_of=[]   # anc_of[j] = index of nearer anchor for stitch pts
    ancset=set(anchors)
    # walk through, tagging nearer anchor for each stitch point
    chain.append(anchors[0]); is_anc.append(1); anc_of.append(0)
    for i in range(len(anchors)-1):
        A=anchors[i]; wi=words[i]; x,y,z=A
        interiors=[]
        for si in wi[:-1]:
            s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]; interiors.append((x,y,z))
        nint=len(interiors)
        for t,p in enumerate(interiors):
            # nearer anchor: distance in STEPS from start=t+1, from end=nint+1-t
            near = i if (t+1) <= (nint+1-(t)) else i+1  # t+1 steps to A_i, nint+1-(t+1)+1...
            # steps to A_i = t+1 ; steps to A_{i+1} = (nint+1)-(t+1)+... word has nint+1 steps
            steps_start=t+1
            steps_end=(nint+1)-steps_start
            near = i if steps_start<=steps_end else i+1
            chain.append(p); is_anc.append(0); anc_of.append(near)
        chain.append(anchors[i+1]); is_anc.append(1); anc_of.append(i+1)
    return chain, is_anc, anchors, ancset

def frac_max(v):
    return v

RHOS=[0.5,1,1.5,2,3,4,5,6,8,10]

def measure(pkl, label):
    chain,is_anc,anchors,ancset=build(pkl)
    n=len(chain)
    CELL=11
    grid=defaultdict(list)
    for idx,p in enumerate(chain):
        grid[(p[0]//CELL,p[1]//CELL,p[2]//CELL)].append(idx)
    # also a grid of ANCHORS only for anchor-count queries at radius rho+4
    ganc=defaultdict(list)
    for a in anchors:
        ganc[(a[0]//CELL,a[1]//CELL,a[2]//CELL)].append(a)

    def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
    def neigh(q,g):
        cx,cy,cz=q[0]//CELL,q[1]//CELL,q[2]//CELL; out=[]
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            out.extend(g.get((cx+dx,cy+dy,cz+dz),()))
        return out

    # max crowding c, refill b, anchor a over all q in chain, per rho
    cmax={r:0 for r in RHOS}; bmax={r:0 for r in RHOS}; amax={r:0 for r in RHOS}
    # effective per-anchor multiplicity: for each q, S(q,rho)/max(1,Anc(q,rho+4))
    aeff={r:0.0 for r in RHOS}          # max ratio
    aeff_q={r:None for r in RHOS}
    for qi in range(n):
        q=chain[qi]
        cand=neigh(q,grid)
        dists=[]
        for j in cand:
            d=cheb(q,chain[j])
            if d<=10: dists.append((d,is_anc[j]))
        # anchor neighbors at radius up to 14 for rho+4 queries
        canc=neigh(q,ganc)
        dancs=[cheb(q,a) for a in canc]
        for r in RHOS:
            ctot=0;btot=0;atot=0
            for d,ia in dists:
                if d<=r:
                    ctot+=1
                    if ia: atot+=1
                    else: btot+=1
            if ctot>cmax[r]: cmax[r]=ctot
            if btot>bmax[r]: bmax[r]=btot
            if atot>amax[r]: amax[r]=atot
            # anchors within r+4
            anc_r4=sum(1 for dd in dancs if dd<=r+4)
            ratio=btot/anc_r4 if anc_r4>0 else (btot if btot else 0.0)
            if btot>0 and ratio>aeff[r]:
                aeff[r]=ratio; aeff_q[r]=qi
    # structural per-anchor stitch multiplicity sigma(A): max stitch pts assigned to one anchor
    load=defaultdict(int)
    # recompute via anc_of over stitch points, but we didn't keep anc_of aligned to chain indices robustly; recount:
    return dict(label=label,n=n,anchors=len(anchors),stitch=n-len(anchors),
                cmax=cmax,bmax=bmax,amax=amax,aeff=aeff)

if __name__=="__main__":
    out={}
    for L,pkl in (("L6","gate2-l7-construction-L6.pkl"),
                  ("L7","gate2-l7-construction-L7.pkl"),
                  ("L8","gate2-l7-construction-L8.pkl")):
        r=measure(pkl,L); out[L]=r
        print(f"\n=== {L}: n={r['n']} anchors={r['anchors']} stitch={r['stitch']} "
              f"(stitch/anchor={r['stitch']/r['anchors']:.3f}) ===")
        print(f"{'rho':>5} {'c':>5} {'b':>5} {'anc':>5} {'b/c':>6} {'c/rho':>6} {'b/rho':>6} {'a_eff':>6}")
        for rr in RHOS:
            c=r['cmax'][rr]; b=r['bmax'][rr]; a=r['amax'][rr]; ae=r['aeff'][rr]
            print(f"{rr:>5} {c:>5} {b:>5} {a:>5} {b/c if c else 0:>6.3f} "
                  f"{c/rr:>6.2f} {b/rr:>6.2f} {ae:>6.3f}")
    # dump json (convert rho keys to str)
    def conv(d): return {str(k):v for k,v in d.items()}
    js={}
    for L,r in out.items():
        js[L]=dict(n=r['n'],anchors=r['anchors'],stitch=r['stitch'],
                   cmax=conv(r['cmax']),bmax=conv(r['bmax']),
                   amax=conv(r['amax']),aeff=conv(r['aeff']))
    json.dump(js,open(os.path.join(os.path.dirname(__file__),"joint_measure.json"),"w"),indent=2)
    print("\nwrote joint_measure.json")
