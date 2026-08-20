"""
CANDIDATE C-A (isolate ACCELERATION): accelerating equal-moduli matrix M3(a)
+ SYMMETRIC (achiral) menu SQ4.  Full T1..T5 battery, brutally honest.

SQ4 = {(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1)}  (achiral, |Aut|=8, generates index-10 sublattice)
M_k = M3(k+1) = [[k+1,0,0],[0,0,-(k+1)^2],[0,1,-1]]  (all |eig|=k+1, cos th=-1/(2(k+1)) irrational)
"""
from chiral_accel import (M3, first_triple, collinear, legal, vsub, vadd, dot,
                          is_chiral, negation_closed, minors_gcd, handedness_chi,
                          matpow_scaled_norm)
from multi_level import build, matvec_int, bridge_exact, frame
from math import hypot, sqrt
from fractions import Fraction as F

SQ4 = [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1)]        # C-A achiral menu
SCREW6 = [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)]  # for contrast
M_BAL3 = [[3,0,0],[0,0,-3],[0,3,-1]]

def hr(t): print("\n"+"="*70+"\n"+t+"\n"+"="*70)

# ---------------- T1 FINITENESS ----------------
def T1():
    hr("T1 FINITENESS  (menu SQ4, fixed finite, reused every level)")
    ch, ng, dets = is_chiral(SQ4)
    print(f"  |SQ4|={len(SQ4)}  chiral={ch}  |Aut|={ng}  improper={any(d==-1 for d in dets)}")
    print(f"  negation_closed={negation_closed(SQ4)}  minors_gcd={minors_gcd(SQ4)} "
          f"(==1 iff generates Z^3)")
    print(f"  handedness chi(SQ4)={handedness_chi(SQ4)}")
    print("  VERDICT: fixed finite integer menu -> T1 PASS (finiteness).")
    print("           NOTE: achiral + generates only an index-10 sublattice (not Z^3).")

# ---------------- T2 STITCH-NO-COLLINEAR (CRUX) ----------------
def T2():
    hr("T2 STITCH-NO-COLLINEAR [CRUX] : C-A SQ4, >=6 levels, prescaled large gaps")
    # prescale = M3(7)^2 so even level-1 gaps are large (bridge design regime)
    P=M3(7); P=[[sum(P[i][k]*P[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    log,pts=build(SQ4,Kmax=8,seed_word_len=4,prescale=P)
    for row in log: print("  ",row)
    ft=first_triple(pts)
    print(f"  FINAL points={len(pts)}  first_triple={ft}")
    return log,pts

def T2_gapgrowth():
    hr("T2 gap-growth & bridge-length diagnostics (per level)")
    P=M3(7); P=[[sum(P[i][k]*P[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    # seed
    pts=[(0,0,0)]; pset=set(pts); cur=pts[0]
    for _ in range(4):
        for s in SQ4:
            cand=vadd(cur,s)
            if cand not in pset and legal(pts,cand):
                cur=cand; pts.append(cur); pset.add(cur); break
    pts=[matvec_int(P,p) for p in pts]
    anchors=pts[:]
    avals=[2,3,4,5,6,7,8,9]
    for k in range(6):
        a=avals[k]; M=M3(a)
        scaled=[matvec_int(M,p) for p in anchors]
        gaps=[hypot(*[float(x) for x in vsub(scaled[i+1],scaled[i])]) for i in range(len(scaled)-1)]
        # try to bridge one representative gap and report bridge length
        newpts=[scaled[0]]; newpset={scaled[0]}
        bridged=0; brlens=[]; failat=None
        for i in range(len(scaled)-1):
            if scaled[i] not in newpset: newpts.append(scaled[i]); newpset.add(scaled[i])
            gl=hypot(*[float(x) for x in vsub(scaled[i+1],scaled[i])])
            rad=max(5,int(0.10*gl)); tn=max(2,int(gl/40))
            before=len(newpts)
            if bridge_exact(scaled[i],scaled[i+1],SQ4,newpts,newpset,rad,tn):
                bridged+=1; brlens.append(len(newpts)-before)
            else:
                failat=i; break
            if scaled[i+1] not in newpset: newpts.append(scaled[i+1]); newpset.add(scaled[i+1])
        avgg=sum(gaps)/len(gaps) if gaps else 0
        print(f"  L{k+1}: a={a} anchors={len(anchors)} avg_gap={avgg:.0f} "
              f"max_gap={max(gaps):.0f} seams={len(scaled)-1} bridged_ok={bridged} "
              f"bridge_lens={brlens[:4]}{'...' if len(brlens)>4 else ''} "
              f"failseam={failat} first_triple={first_triple(newpts)}")
        if failat is not None:
            print("     -> STALLED (SQ4 straight bridge could not close this seam).")
            break
        anchors=newpts

# ---------------- T3 FLATTEN ----------------
def T3(pts):
    hr("T3 FLATTEN : cumulative-product power-boundedness + cloud aperture")
    # per-level semisimple power bound (already known) -- recompute cumulative product
    Cum=[[1,0,0],[0,1,0],[0,0,1]]
    for a in [2,3,4,5,6,7]:
        M=M3(a)
        Cum=[[sum(M[i][k]*Cum[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    # cumulative radius r = prod a = 2*3*4*5*6*7 = 5040
    rprod=1
    for a in [2,3,4,5,6,7]: rprod*=a
    pb=matpow_scaled_norm(Cum,rprod,1)
    print(f"  cumulative prod M_k (a=2..7), radius={rprod}, (Cum/r) maxentry={pb:.4f}")
    # aperture of realized cloud: min normalized |det(D1,D2,D3)| over displacement triples
    if pts and len(pts)>=8:
        aperture_stat(pts)

def aperture_stat(pts, sample=1500):
    import random
    rng=random.Random(1)
    P=pts if len(pts)<=400 else rng.sample(pts,400)
    o=P[0]
    D=[vsub(p,o) for p in P[1:]]
    D=[d for d in D if any(d)]
    best=0.0; worst=1e18; count=0
    for _ in range(sample):
        a,b,c=rng.sample(D,3)
        det=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))
        na=hypot(*[float(x) for x in a]); nb=hypot(*[float(x) for x in b]); nc=hypot(*[float(x) for x in c])
        if na*nb*nc==0: continue
        norm=abs(det)/(na*nb*nc)
        best=max(best,norm); worst=min(worst,norm); count+=1
    print(f"  cloud aperture over {count} displacement triples: "
          f"max normdet={best:.4f} min normdet={worst:.2e}")
    print("  (bounded-below max => not collapsed to a line; min~0 is normal for coplanar triples)")

# ---------------- T4 STRADDLE SUPPRESSION ----------------
def antipodal_and_midpoint_stats(pts, label):
    """Count (i) exact (v,-v) antipodal collinear straddle triples: p is midpoint
    of q,r with q-p = -(r-p).  (ii) fraction of pairs whose midpoint is a walk pt."""
    ptset=set(pts)
    P=pts
    m=len(P)
    # (i) midpoint-collinear: p_j is midpoint of p_i,p_k  <=> p_i+p_k=2 p_j
    # count triples (i,j,k) i<k with (p_i+p_k)/2 = some walk point p_j
    mid_hits=0; pair_ct=0
    # limit cost
    import random
    rng=random.Random(2)
    idx=list(range(m))
    if m>500: idx=rng.sample(idx,500)
    for ai in range(len(idx)):
        for bi in range(ai+1,len(idx)):
            i=idx[ai]; k=idx[bi]
            pi=P[i]; pk=P[k]
            s=tuple(pi[t]+pk[t] for t in range(3))
            pair_ct+=1
            if all(c%2==0 for c in s):
                mp=tuple(c//2 for c in s)
                if mp in ptset:
                    mid_hits+=1
    frac=mid_hits/pair_ct if pair_ct else 0
    print(f"  [{label}] pts={m} sampled_pairs={pair_ct} midpoint-is-walkpoint hits={mid_hits} "
          f"frac={frac:.3e}")
    return mid_hits, frac

def baseline_MBAL3(nlv=6):
    """Build an M_BAL3 stationary imbrication-style anchor cloud for baseline.
    Just iterate M_BAL3 on a small triple-free seed (no bridges) to get the
    self-similar cloud whose straddle survivors we compare against."""
    seed=[(0,0,0),(1,0,0),(0,1,0),(1,1,1),(2,1,0),(0,2,1),(1,0,2)]
    # keep only triple-free prefix
    tf=[]
    for p in seed:
        if legal(tf,p) and p not in set(tf): tf.append(p)
    pts=tf[:]
    cur=tf[:]
    for _ in range(nlv):
        cur=[matvec_int(M_BAL3,p) for p in cur]
        pts=pts+cur
    # dedup
    seen=set(); out=[]
    for p in pts:
        if p not in seen: seen.add(p); out.append(p)
    return out

def T4(ca_pts):
    hr("T4 STRADDLE-SUPPRESSION : C-A (achiral SQ4) vs M_BAL3 baseline")
    base=baseline_MBAL3(6)
    bh,bf=antipodal_and_midpoint_stats(base,"M_BAL3 baseline")
    if ca_pts and len(ca_pts)>6:
        ch,cf=antipodal_and_midpoint_stats(ca_pts,"C-A SQ4 realized")
        if bf>0:
            print(f"  ratio C-A/baseline midpoint-frac = {cf/bf:.3f}  "
                  f"(chiral menu claims ~0; SYMMETRIC menu expected NOT suppressed)")
    else:
        print("  C-A realized walk too small (T2 stalled) -> cannot measure suppression.")
    # Also: is the achiral menu itself negation-generating straddles?
    print("  NOTE: SQ4 is mirror-symmetric (improper Aut) -> no handed drift -> "
          "monotone-escape argument does NOT apply; straddles NOT geometrically excluded.")

# ---------------- T5 DODGES ----------------
def T5():
    hr("T5 DODGES : which fixed-map/similarity/straddle obstructions C-A escapes")
    from chiral_accel import charpoly, durand_kerner
    maps=[M3(a) for a in [2,3,4,5,6,7]]
    coss=[F(-1,2*a) for a in [2,3,4,5,6,7]]
    print(f"  (a) maps pairwise distinct: {len(set(map(str,maps)))==len(maps)}  "
          f"cos th distinct & irrational (Niven): {coss}")
    rs=[2,3,4,5,6,7]
    print(f"  (b) r_k strictly increasing (no fixed global similarity): "
          f"{all(rs[i]<rs[i+1] for i in range(len(rs)-1))}")
    print(f"  (c) angles cos in Q\\{{0,+-1/2,+-1}} (Niven irrational, non-repeating): "
          f"{all(c not in (F(0),F(1,2),F(-1,2),F(1),F(-1)) for c in coss)}")
    print("  => C-A DODGES: Niven(distinct ratios), fixed-map primitivity(non-stationary),")
    print("     ESS self-similar degeneracy(no single similarity).")
    print("  => C-A DOES NOT DODGE: (v,-v) straddle family -- menu is mirror-symmetric,")
    print("     drift is NOT handed, so no monotone-escape exclusion of midpoints.")
    print("  (This is the WHOLE POINT of the C-A control: acceleration alone, no chirality.)")

if __name__=="__main__":
    T1()
    log,pts=T2()
    T2_gapgrowth()
    T3(pts)
    T4(pts)
    T5()
