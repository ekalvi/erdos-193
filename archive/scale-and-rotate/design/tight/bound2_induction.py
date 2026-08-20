"""
TASK B — rigorously test the BOUND2 phi<1 contraction induction.

BOUND2 (exact, proven):  b_Q^{(k)}(R) <= b_Q^{(k-1)}(R/3) + I_Q^{(k)}(R)
  - R/3 exact because M^T Q M = 9Q => d_Q(Mp,Mq)=3 d_Q(p,q) (verified elsewhere).
  - disjoint union W_k = (M.W_{k-1}) (+) Stitch_k (0 overlap).

Under ansatz b_Q(R) <= C R^d, I_Q(R) <= E R^d:  C >= 3^{-d} C + E
  => fixed point C* = E / (1 - 3^{-d}),  contraction phi = 3^{-d} < 1.

This script MEASURES on real orbits (L6,L7[,L8]):
  (1) b_Q(R) = sup_q #{walk pts in Q-ball(q,R)}   -> C_Q = sup b_Q(R)/R^d
  (2) I_Q(R) = sup_q #{fresh interiors in Q-ball(q,R)}  -> E_Q = sup I_Q(R)/R^d
  (3) VERIFY the recursion numerically: b_Q(R) <= b_Q(R/3) + I_Q(R)  (level-stable proxy)
  (4) implied fixed point C* = E_Q/(1-3^{-d}); does contraction dominate refill?
  (5) ARC-INCIDENCE: # distinct level-k connector-words with >=1 pt in Q-ball(q,R)
      vs R -> O(R) (linear/curve) or O(R^3) (cubic/packing)?  per-arc donation.
  (6) availability window: Cheb r*=4.44 -> Q-radius alpha*r*=sqrt(15)*4.44=17.2;
      pulled back /3 -> Q ~5.7.  Report b_Q and I_Q there.

Q-ball(R) subset Cheb-ball(R) since eig(Q)>=1 => Q(v)>=|v|_2^2>=|v|_inf^2.
Work in integer R^2 threshold.  Q(x,y,z)=x^2+6y^2-2yz+6z^2.
"""
import sys, pickle, math, json
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors

LAM = 3.3617                      # level-stable point growth (L8)
D   = math.log(LAM)/math.log(3)  # ~1.1036
PHI = 3.0**(-D)                  # count-contraction factor
ALPHA = math.sqrt(15.0)          # Cheb->Q distortion sup

def Qform(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def build_tagged(L):
    """ordered chain with arc-id per point. anchors tagged arc=-1; interiors tagged
    by their originating word index."""
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    anchors = d['anchors']; words = d['words']
    pts=[]; arc=[]
    pts.append(tuple(anchors[0])); arc.append(-1)
    for i in range(len(anchors)-1):
        for p in word_interiors(anchors[i], words[i]):
            pts.append(tuple(p)); arc.append(i)
        pts.append(tuple(anchors[i+1])); arc.append(-1)
    return pts, arc

def qball_max(pts, R, centres):
    """sup over given centres of #{p in pts : Q(p-q) <= R^2}."""
    R2 = R*R
    cell = max(int(math.ceil(R)),1)
    grid = defaultdict(list)
    for p in pts:
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    best=0; bestq=None
    for q in centres:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        c=0
        for dx in(-2,-1,0,1,2):
          for dy in(-2,-1,0,1,2):
            for dz in(-2,-1,0,1,2):
              for p in grid.get((gx+dx,gy+dy,gz+dz),()):
                v=(p[0]-q[0],p[1]-q[1],p[2]-q[2])
                if Qform(v)<=R2: c+=1
        if c>best: best=c; bestq=q
    return best, bestq

def qball_refill_and_arcs(pts, arc, R, centres):
    """sup over centres of #{interiors in Q-ball} (refill I_Q) and, at that
    same sup centre, the # distinct incident level-k words (arcs) & per-arc counts."""
    R2=R*R; cell=max(int(math.ceil(R)),1)
    grid=defaultdict(list)
    for idx,p in enumerate(pts):
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(idx)
    bestI=0; best_arcs=0; best_perarc=0
    for q in centres:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        cI=0; arccnt=defaultdict(int)
        for dx in(-2,-1,0,1,2):
          for dy in(-2,-1,0,1,2):
            for dz in(-2,-1,0,1,2):
              for idx in grid.get((gx+dx,gy+dy,gz+dz),()):
                p=pts[idx]; v=(p[0]-q[0],p[1]-q[1],p[2]-q[2])
                if Qform(v)<=R2:
                    a=arc[idx]
                    if a>=0:
                        cI+=1; arccnt[a]+=1
        na=len(arccnt); pa=max(arccnt.values()) if arccnt else 0
        if cI>bestI: bestI=cI
        if na>best_arcs: best_arcs=na; best_perarc=pa
    return bestI, best_arcs, best_perarc

if __name__=="__main__":
    Ls=[int(x) for x in sys.argv[1:]] or [6,7]
    # Q-radii to probe. include the availability window 17.2 and its /3 pullback 5.7
    Rs=[1,2,3,4,5,6,9,12,15,17,18,21,27]
    out={"d":D,"phi_3^-d":PHI,"alpha_sqrt15":ALPHA,"lam":LAM,
         "avail_window_Q":ALPHA*4.44,"levels":{}}
    for L in Ls:
        pts,arc=build_tagged(L)
        N=len(pts)
        # centre set: walk points; subsample for large R to stay bounded
        rec={"N":N}
        bQ={}; IQ={}; arcs={}; perarc={}
        for R in Rs:
            stride = 1 if (R<=9 or N<40000) else max(1, N// (20000 if R<=18 else 8000))
            centres = pts[::stride]
            b,_=qball_max(pts,R,centres)
            i,na,pa=qball_refill_and_arcs(pts,arc,R,centres)
            bQ[R]=b; IQ[R]=i; arcs[R]=na; perarc[R]=pa
            print(f"L{L} R={R:5} bQ={b:4} IQ={i:4} arcs={na:4} perarc={pa:3} "
                  f"bQ/R^d={b/R**D:.3f} IQ/R^d={i/R**D:.3f} arcs/R={na/R:.3f} arcs/R^3={na/R**3:.4f}",
                  flush=True)
        # constants
        C_Q = max(bQ[R]/R**D for R in Rs)
        E_Q = max(IQ[R]/R**D for R in Rs)
        C_Q_noR1 = max(bQ[R]/R**D for R in Rs if R>=2)
        E_Q_noR1 = max(IQ[R]/R**D for R in Rs if R>=2)
        # recursion check: b_Q(R) <= b_Q(floor R/3) + I_Q(R)  (level-stable proxy)
        rec_ok=True; rec_detail=[]
        for R in Rs:
            R3=R//3
            if R3<1: continue
            # b at R3: interpolate to nearest measured <=; use measured if present else recompute
            if R3 in bQ: bR3=bQ[R3]
            else:
                bR3,_=qball_max(pts,R3,pts[::max(1,N//20000)])
            lhs=bQ[R]; rhs=bR3+IQ[R]
            ok=lhs<=rhs
            rec_ok=rec_ok and ok
            rec_detail.append({"R":R,"bQ_R":lhs,"bQ_R/3":bR3,"IQ_R":IQ[R],"rhs":rhs,"holds":ok})
        # implied fixed point from measured refill slope
        Cstar_from_E = E_Q/(1-PHI)
        Cstar_from_E_noR1 = E_Q_noR1/(1-PHI)
        # arc incidence exponent (log-log fit over R in [3,27])
        import statistics
        xs=[math.log(R) for R in Rs if R>=3]
        ya=[math.log(arcs[R]) if arcs[R]>0 else 0 for R in Rs if R>=3]
        n=len(xs); mx=sum(xs)/n; my=sum(ya)/n
        slope_arc=sum((xs[i]-mx)*(ya[i]-my) for i in range(n))/sum((xs[i]-mx)**2 for i in range(n))
        rec.update({
          "bQ":bQ,"IQ":IQ,"arcs":arcs,"perarc":perarc,
          "C_Q_supRge1":round(C_Q,3),"E_Q_supRge1":round(E_Q,3),
          "C_Q_Rge2":round(C_Q_noR1,3),"E_Q_Rge2":round(E_Q_noR1,3),
          "phi":round(PHI,4),"1-phi":round(1-PHI,4),
          "Cstar_from_measured_E":round(Cstar_from_E,3),
          "Cstar_from_measured_E_Rge2":round(Cstar_from_E_noR1,3),
          "recursion_holds_all_R":rec_ok,"recursion_detail":rec_detail,
          "arc_incidence_loglog_slope":round(slope_arc,3),
          "contraction_dominates_refill": E_Q < (1-PHI)*C_Q + 1e-9,
        })
        # availability window numbers
        rec["at_Q_17 (Cheb4.44 window)"]={"bQ":bQ.get(17),"IQ":IQ.get(17),"arcs":arcs.get(17)}
        rec["at_Q_6 (pulled-back /3)"]={"bQ":bQ.get(6),"IQ":IQ.get(6),"arcs":arcs.get(6)}
        out["levels"][L]=rec
        print(json.dumps({f"L{L}_summary":{k:rec[k] for k in
              ["C_Q_supRge1","E_Q_supRge1","C_Q_Rge2","E_Q_Rge2","Cstar_from_measured_E",
               "Cstar_from_measured_E_Rge2","recursion_holds_all_R","arc_incidence_loglog_slope",
               "contraction_dominates_refill"]}}), flush=True)
    json.dump(out, open("design/tight/bound2_induction.json","w"), indent=1, default=str)
    print("WROTE design/tight/bound2_induction.json", flush=True)
