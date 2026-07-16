"""
ROUTE 3 -- DIRECT BOUNDED-DISTORTION COVERING in the Q-METRIC.

Target: level-independent C with  c_k(q,r) := #{walk pts within Chebyshev r of q}
        <= C * r^d  on r in [1,10],  d = log(lambda)/log(3) ~ 1.10.

The new move: work in the invariant Q-metric where M is an EXACT similarity of
ratio 3 (M^T Q M = 9 Q), so the anisotropic self-affine mess becomes an exact
self-SIMILAR covering.  In the isotropic (Chebyshev) route the box-distortion
kappa_M grows with scale (1,2,3) because ||M||_inf = 4 > 3 = det(M)^{1/3}; the
claim is that in the Q-metric kappa is SCALE-STABLE (a fixed constant), which is
exactly what a clean self-similar Ahlfors bound needs.

Q = [[1,0,0],[0,6,-1],[0,-1,6]],  Q(x,y,z) = x^2 + 6y^2 - 2yz + 6z^2,  M^T Q M = 9Q.

TESTS (all EXACT integer arithmetic on the constructed walks; float only for the
Q-Cholesky embedding u = L^T p, |u|^2 = Q(p), in which M acts as A = 3*O, O orth):

 (T1) EXACTNESS of the metric self-similarity:  Q(M v) = 9 Q(v) for all integer v
      (integer identity, sampled + proven) => d_Q(Mp,Mq) = 3 d_Q(p,q) EXACTLY.
      Hence covering/packing numbers are metric invariants that scale by exactly 3.
 (T2) SCALE-STABILITY of the covering distortion:  in u-space M = 3*O; measure
      kappa_Q(s) = max over occupied side-s u-cells of #{side-3s u-cells covering
      A.cell}.  Compare to the isotropic kappa_M(r) = 1,2,3 (which GREW).  If
      kappa_Q(s) is flat in s, the induction carries the lambda multiplier with a
      UNIFORM constant (the thing the isotropic route could not do).
 (T3) SELF-SIMILAR per-3x covering ratio N_s / N_{3s} in the Q-metric -> lambda,
      and its scale-stability on the availability window.
 (T4) LOCAL Q-BALL count b_Q(R) = max_q #{walk pts in Q-ball radius R}; fit
      b_Q(R) <= C_Q * R^d.  This is the direct Ahlfors upper bound in the metric
      where it is clean.
 (T5) CONVERSION to the Chebyshev target:  Cheb-r ball  subset  Q-ball(alpha*r)
      with alpha = sup_{|p|_inf<=1}|p|_Q ; and Q-ball(R) subset Cheb(beta*R).
      Deliver C with c_k(q,r) <= C r^d on [1,10], report the binding level/r, and
      the load-bearing availability count c(q,4)=c(q,4.44).
"""
import pickle, math, json
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3
Q = ((1,0,0),(0,6,-1),(0,-1,6))
D_EXPONENT = None  # set from measured lambda below

def matvec(m, v):
    return (m[0][0]*v[0]+m[0][1]*v[1]+m[0][2]*v[2],
            m[1][0]*v[0]+m[1][1]*v[1]+m[1][2]*v[2],
            m[2][0]*v[0]+m[2][1]*v[1]+m[2][2]*v[2])

def qform(v):
    x,y,z = v
    return x*x + 6*y*y - 2*y*z + 6*z*z

def build_chain(pkl):
    d = pickle.load(open(pkl, "rb"))
    anchors = d["anchors"]; words = d["words"]
    def interiors(start, wi):
        pts = []; x, y, z = start
        for si in wi[:-1]:
            s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; pts.append((x, y, z))
        return pts
    chain = [tuple(anchors[0])]
    for i in range(len(anchors)-1):
        chain.extend(interiors(anchors[i], words[i]))
        chain.append(tuple(anchors[i+1]))
    return chain

def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

# ---- Q-Cholesky embedding: u = L^T p, |u|^2 = Q(p).  L^T upper triangular. ----
# Q = [[1,0,0],[0,6,-1],[0,-1,6]] -> u0 = x ; u1 = sqrt6*y - z/sqrt6 ; u2 = sqrt(35/6)*z
S6 = math.sqrt(6.0)
S356 = math.sqrt(35.0/6.0)
def embed(p):
    x,y,z = p
    return (float(x), S6*y - z/S6, S356*z)

def A_matrix():
    """A = L^T M L^{-T}; the action of M in u-space; should equal 3*O, O orthogonal."""
    # columns are embed(M . e_i) after inverse embed of e_i; easier: A u = embed(M p)
    # where u = embed(p). Build A by applying to the three u-basis preimages.
    # preimage of u-basis: p = (L^T)^{-1} e_j. Compute numerically.
    # L^T = [[1,0,0],[0,S6,-1/S6],[0,0,S356]]
    LT = [[1.0,0.0,0.0],[0.0,S6,-1.0/S6],[0.0,0.0,S356]]
    # invert LT (upper triangular)
    a=LT[0][0]; # =1
    e=LT[1][1]; f=LT[1][2]; i=LT[2][2]
    LTinv = [[1.0,0.0,0.0],
             [0.0,1.0/e,-f/(e*i)],
             [0.0,0.0,1.0/i]]
    cols=[]
    for j in range(3):
        uj = [0.0,0.0,0.0]; uj[j]=1.0
        # p = LTinv @ uj
        p = tuple(sum(LTinv[r][c]*uj[c] for c in range(3)) for r in range(3))
        Mp = matvec(M, p)
        col = embed(Mp)
        cols.append(col)
    # A has these as columns
    A = [[cols[c][r] for c in range(3)] for r in range(3)]
    return A

def occ_cells_u(upts, s):
    st = set()
    inv = 1.0/s
    for u in upts:
        st.add((math.floor(u[0]*inv), math.floor(u[1]*inv), math.floor(u[2]*inv)))
    return st

def boxcount_u(upts, s):
    return len(occ_cells_u(upts, s))

def local_c_cheb(chain, rho):
    grid = defaultdict(list); cell = rho + 1
    for idx, p in enumerate(chain):
        grid[(p[0]//cell, p[1]//cell, p[2]//cell)].append(idx)
    def neigh(p):
        cx,cy,cz = p[0]//cell, p[1]//cell, p[2]//cell; out=[]
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    out.extend(grid.get((cx+dx,cy+dy,cz+dz),()))
        return out
    maxc=0
    for q in chain:
        cnt = sum(1 for j in neigh(q) if cheb(q,chain[j])<=rho)
        if cnt>maxc: maxc=cnt
    return maxc

def local_b_qball(chain, R):
    """max over walk pts q of #{walk pts p : sqrt(Q(p-q)) <= R}.
    Use a Cheb pre-filter: Q(v) >= min-eig * |v|_2^2 >= 1*|v|_inf^2, and
    Q(v) <= 7*|v|_2^2 <= 21*|v|_inf^2.  So Q(p-q)<=R^2 forces |v|_inf <= R (since
    Q>=|v|_inf^2 when the min structure... use safe filter |v|_inf <= R)."""
    R2 = R*R
    # candidates within Cheb radius ceil(R) (since Q(v) >= |v|_inf^2? check: Q>= lambda_min|v|_2^2
    #  = 1*|v|_2^2 >= |v|_inf^2). So Q(v)<=R^2 => |v|_inf<=R.)
    rad = int(math.floor(R))
    grid = defaultdict(list); cell = rad + 1
    for idx,p in enumerate(chain):
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(idx)
    def neigh(p):
        cx,cy,cz=p[0]//cell,p[1]//cell,p[2]//cell; out=[]
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    out.extend(grid.get((cx+dx,cy+dy,cz+dz),()))
        return out
    maxb=0; argq=None
    for q in chain:
        cnt=0
        qx,qy,qz=q
        for j in neigh(q):
            p=chain[j]
            v=(p[0]-qx,p[1]-qy,p[2]-qz)
            if qform(v)<=R2: cnt+=1
        if cnt>maxb: maxb=cnt; argq=q
    return maxb

if __name__ == "__main__":
    pkls = {"L5":"gate2-l7-construction-L5.pkl","L6":"gate2-l7-construction-L6.pkl",
            "L7":"gate2-l7-construction-L7.pkl","L8":"gate2-l7-construction-L8.pkl"}
    order=["L5","L6","L7","L8"]
    chains={l:build_chain(pkls[l]) for l in order}
    out={}

    # ---- (T1) exact metric self-similarity ----
    import random
    rng=random.Random(1)
    ok=True; worst=0
    for _ in range(200000):
        v=(rng.randint(-50,50),rng.randint(-50,50),rng.randint(-50,50))
        if qform(matvec(M,v)) != 9*qform(v):
            ok=False; break
    out["T1_metric_selfsimilar_exact"]=dict(Q_M_v_eq_9_Q_v=ok,
        statement="Q(Mv)=9Q(v) integer identity => d_Q(Mp,Mq)=3 d_Q(p,q) EXACT; covering/packing numbers scale by exactly 3.")
    print(f"[T1] Q(Mv)=9Q(v) exact on 2e5 random integer v: {ok}")

    # A = 3*O check
    A=A_matrix()
    AtA=[[sum(A[k][i]*A[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    ata_is_9I=all(abs(AtA[i][j]-(9.0 if i==j else 0.0))<1e-9 for i in range(3) for j in range(3))
    out["T1_A_is_3O"]=dict(AtA=[[round(AtA[i][j],6) for j in range(3)] for i in range(3)],
                           AtA_eq_9I=ata_is_9I)
    print(f"[T1] u-space action A satisfies A^T A = 9 I (M = 3*O, O orthogonal): {ata_is_9I}")

    # ---- global lambda, d ----
    Nk={l:len(chains[l]) for l in order}
    lam=Nk["L8"]/Nk["L7"]
    d=math.log(lam)/math.log(3.0)
    out["global"]=dict(N=Nk, lambda_L7_L8=lam, d=d,
                       extent_ratio="3 exact = det(M)^{1/3} (M elliptic, all eig moduli 3)")
    print(f"[global] lambda={lam:.5f}  d=log(lambda)/log3={d:.5f}")

    # embed all chains
    uchains={l:[embed(p) for p in chains[l]] for l in order}

    # ---- (T2) scale-stability of covering distortion in Q vs isotropic ----
    # isotropic kappa_M(r): reuse the known growth by measuring here for reference
    T2={}
    for lvl in ["L6","L7"]:
        ch=chains[lvl]
        iso={}
        for r in (1,2,3,4,6,9):
            cells=defaultdict(list)
            for p in ch: cells[(p[0]//r,p[1]//r,p[2]//r)].append(p)
            k=0
            for cell,mem in cells.items():
                img=set()
                for p in mem:
                    qv=matvec(M,p); img.add((qv[0]//(3*r),qv[1]//(3*r),qv[2]//(3*r)))
                if len(img)>k: k=len(img)
            iso[r]=k
        # Q-space kappa_Q(s): in u-space, image cells under A at side 3s vs source side s
        uc=uchains[lvl]
        qd={}
        for s in (1.0,2.0,3.0,6.0,9.0,18.0):
            cells=defaultdict(list)
            invs=1.0/s
            for u in uc: cells[(math.floor(u[0]*invs),math.floor(u[1]*invs),math.floor(u[2]*invs))].append(u)
            inv3=1.0/(3*s); k=0
            for cell,mem in cells.items():
                img=set()
                for u in mem:
                    au=(A[0][0]*u[0]+A[0][1]*u[1]+A[0][2]*u[2],
                        A[1][0]*u[0]+A[1][1]*u[1]+A[1][2]*u[2],
                        A[2][0]*u[0]+A[2][1]*u[1]+A[2][2]*u[2])
                    img.add((math.floor(au[0]*inv3),math.floor(au[1]*inv3),math.floor(au[2]*inv3)))
                if len(img)>k: k=len(img)
            qd[s]=k
        T2[lvl]=dict(kappa_iso_by_r={str(k):v for k,v in iso.items()},
                     kappa_Q_by_s={str(k):v for k,v in qd.items()})
    out["T2_distortion"]=T2
    print("[T2] isotropic kappa_M(r) vs Q-metric kappa_Q(s):")
    for lvl in ["L6","L7"]:
        print(f"   {lvl} iso: {T2[lvl]['kappa_iso_by_r']}")
        print(f"   {lvl} Q  : {T2[lvl]['kappa_Q_by_s']}")

    # ---- (T3) per-3x Q covering ratio -> lambda ----
    T3={}
    for lvl in order:
        uc=uchains[lvl]
        # extent in u
        ex=max(max(abs(u[c]) for u in uc) for c in range(3))
        bc={}; s=1.0
        while s<=ex:
            bc[s]=boxcount_u(uc,s); s*=3.0
        ks=sorted(bc)
        ratios={ks[i]:bc[ks[i]]/bc[ks[i+1]] for i in range(len(ks)-1)}
        T3[lvl]=dict(boxcount_u={str(round(k,2)):bc[k] for k in ks},
                     ratio_Ns_over_N3s={str(round(ks[i],2)):round(ratios[ks[i]],4) for i in range(len(ks)-1)})
    out["T3_Qcovering_ratio"]=T3
    print("[T3] Q-metric per-3x covering ratio N_s/N_3s (-> lambda in fractal regime):")
    for lvl in order:
        print(f"   {lvl}: {T3[lvl]['ratio_Ns_over_N3s']}")

    # ---- (T4) local Q-ball count b_Q(R) and fit <= C_Q R^d ----
    T4={}
    Rlist=[1.0,1.5,2.0,3.0,4.0,5.0,7.0,10.0,14.0,20.0,30.0]
    for lvl in ["L6","L7","L8"]:
        ch=chains[lvl]
        bvals={R:local_b_qball(ch,R) for R in Rlist}
        CQ=max(bvals[R]/(R**d) for R in Rlist)
        argR=max(Rlist,key=lambda R:bvals[R]/(R**d))
        T4[lvl]=dict(b_Q={str(R):bvals[R] for R in Rlist}, C_Q_for_Rd=CQ, binding_R=argR,
                     ratios={str(R):round(bvals[R]/(R**d),3) for R in Rlist})
    out["T4_Qball_fit"]=T4
    print("[T4] local Q-ball count b_Q(R) fit  b_Q <= C_Q R^d:")
    for lvl in ["L6","L7","L8"]:
        print(f"   {lvl}: C_Q={T4[lvl]['C_Q_for_Rd']:.3f} @R={T4[lvl]['binding_R']}  b_Q={T4[lvl]['b_Q']}")

    # ---- (T5) conversion to Chebyshev target ----
    # alpha = sup_{|p|_inf<=1} |p|_Q  (Q-radius of a Cheb-unit ball); beta similar reverse.
    # sup over the 27 sign/coord extreme lattice pts of the cube [-1,1]^3 (Q convex => vertices)
    verts=[(a,b,c) for a in (-1,0,1) for b in (-1,0,1) for c in (-1,0,1)]
    alpha=max(math.sqrt(qform(v)) for v in verts)  # Cheb-1 ball subset Q-ball(alpha)
    out_alpha=alpha
    # so Cheb-r ball subset Q-ball(alpha*r); c_k(q,r) <= b_Q(alpha*r) <= C_Q (alpha r)^d = C_Q alpha^d r^d
    # direct Cheb fit:
    T5={}
    cvals={}
    for lvl in order:
        cv={r:local_c_cheb(chains[lvl],r) for r in range(1,11)}
        cvals[lvl]=cv
        C=max(cv[r]/(r**d) for r in range(1,11))
        argr=max(range(1,11),key=lambda r:cv[r]/(r**d))
        T5[lvl]=dict(c=cv,C_for_rd=C,binding_r=argr,c_at_4=cv[4],
                     ratios={str(r):round(cv[r]/(r**d),3) for r in range(1,11)})
    Cvalid=max(T5[l]["C_for_rd"] for l in order)
    bind_lvl=max(order,key=lambda l:T5[l]["C_for_rd"])
    # conversion-predicted C from the metric route: C_conv = C_Q(worst level) * alpha^d
    CQ_worst=max(T4[l]["C_Q_for_Rd"] for l in ["L6","L7","L8"])
    C_conv=CQ_worst*(alpha**d)
    out["T5_cheb_conversion"]=dict(
        alpha_ChebUnit_to_Q=alpha,
        direct_C_valid_over_range=Cvalid, binding_level=bind_lvl,
        binding_r=T5[bind_lvl]["binding_r"],
        c_at_4p44_by_level={l:cvals[l][4] for l in order},
        C_from_metric_conversion=C_conv,
        Crd_at_4p44_direct=Cvalid*(4.44**d),
        per_level=T5)
    out["global"]["d"]=d
    print(f"[T5] alpha (Cheb-1 -> Q-radius) = {alpha:.4f}")
    print(f"[T5] DIRECT valid C over [1,10] all levels: {Cvalid:.4f}  (binds {bind_lvl} @ r={T5[bind_lvl]['binding_r']})  => C*r^d at 4.44 = {Cvalid*(4.44**d):.3f}")
    print(f"[T5] metric-conversion C = C_Q*alpha^d = {CQ_worst:.3f}*{alpha**d:.3f} = {C_conv:.3f}")
    print(f"[T5] load-bearing c(q,4)=c(q,4.44) by level: {out['T5_cheb_conversion']['c_at_4p44_by_level']} (threshold 12)")

    json.dump(out, open("design/lemma/ahlfors/route3-qmetric-results.json","w"), indent=1)
    print("\nwrote design/lemma/ahlfors/route3-qmetric-results.json")
