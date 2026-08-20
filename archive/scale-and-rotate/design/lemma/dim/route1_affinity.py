"""
ROUTE 1 -- AFFINITY DIMENSION / SINGULAR-VALUE FUNCTION (Falconer).

Goal: derive the box-counting dimension d of the walk from M's singular value
function, prove d = log(lambda)/log 3 via BOUNDED DISTORTION (M elliptic), and
test the local-count law c_k(q,r) <= C r^d on r in [1,10], uniform in k.

Two parts:
  A) LINEAR ALGEBRA on M (hand-rolled, no numpy):
     - eigenvalues (all modulus 3 => elliptic), diagonalizability
     - invariant positive-definite form Q with M^T Q M = 9 Q  => bounded distortion
       constant kappa; singular values of M^j confined to [3^j/kappa, 3^j*kappa]
     - affinity dimension via the pressure equation (collapses to log lambda/log 3)
     - the ANISOTROPIC singular-value pullback contraction factor vs isotropic 4/9
  B) MEASUREMENT on the real construction chains L6/L7/L8:
     - point growth lambda, Cheb-extent growth, box-count slopes
     - worst-case local count c_k(q,r), fit c ~ C r^d
     - arc-incidence: #arcs meeting a Cheb-r ball ~ r^{d-1}
"""
import pickle, math, json, sys
from collections import defaultdict
from gate_run import word_interiors

M = ((3,0,0),(0,0,-3),(0,3,-1))

# ---------- tiny linear algebra ----------
def matmul(A,B):
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def transpose(A):
    return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
def ident():
    return tuple(tuple(1.0 if i==j else 0.0 for j in range(3)) for i in range(3))

def jacobi_eig(Ain):
    """symmetric 3x3 -> sorted eigenvalues (desc). cyclic Jacobi."""
    A=[list(r) for r in Ain]
    for _ in range(100):
        off=sum(A[i][j]**2 for i in range(3) for j in range(3) if i<j)
        if off<1e-30: break
        for p in range(3):
            for q in range(p+1,3):
                if abs(A[p][q])<1e-300: continue
                theta=(A[q][q]-A[p][p])/(2*A[p][q])
                t=(1 if theta>=0 else -1)/(abs(theta)+math.sqrt(theta*theta+1))
                c=1/math.sqrt(t*t+1); s=t*c
                for k in range(3):
                    akp=A[k][p]; akq=A[k][q]
                    A[k][p]=c*akp-s*akq; A[k][q]=s*akp+c*akq
                for k in range(3):
                    apk=A[p][k]; aqk=A[q][k]
                    A[p][k]=c*apk-s*aqk; A[q][k]=s*apk+c*aqk
    ev=sorted([A[i][i] for i in range(3)],reverse=True)
    return ev

def singular_values(A):
    ATA=matmul(transpose(A),A)
    ev=jacobi_eig(ATA)
    return [math.sqrt(max(0.0,x)) for x in ev]

def matpow(A,n):
    R=tuple(tuple(1 if i==j else 0 for j in range(3)) for i in range(3))
    for _ in range(n): R=matmul(R,A)
    return R

# ---------- invariant form Q: M^T Q M = 9 Q ----------
def invariant_form():
    """solve for symmetric Q (6 dof) with M^T Q M - 9 Q = 0, pick PD null vector."""
    Mt=transpose(M)
    # basis of symmetric matrices
    idx=[(0,0),(1,1),(2,2),(0,1),(0,2),(1,2)]
    def sym(v):
        Q=[[0.0]*3 for _ in range(3)]
        Q[0][0]=v[0];Q[1][1]=v[1];Q[2][2]=v[2]
        Q[0][1]=Q[1][0]=v[3];Q[0][2]=Q[2][0]=v[4];Q[1][2]=Q[2][1]=v[5]
        return Q
    def unsym(Q):  # map symmetric matrix to 6-vector in same basis (using upper entries)
        return [Q[0][0],Q[1][1],Q[2][2],Q[0][1],Q[0][2],Q[1][2]]
    # build 6x6 operator L(v) = unsym( M^T sym(v) M - 9 sym(v) )
    L=[]
    for b in range(6):
        e=[0.0]*6; e[b]=1.0
        Q=sym(e)
        MQM=matmul(matmul(Mt,Q),M)
        R=[[MQM[i][j]-9*Q[i][j] for j in range(3)] for i in range(3)]
        L.append(unsym(R))
    # L is columns; we want null space of the matrix whose columns are L[b]
    # Build A (6x6) with A[:,b]=L[b]
    A=[[L[b][r] for b in range(6)] for r in range(6)]
    # gaussian elimination null space
    Aw=[row[:] for row in A]; n=6
    piv=[]; r=0
    for col in range(n):
        # find pivot
        sel=-1; best=1e-9
        for i in range(r,n):
            if abs(Aw[i][col])>best: best=abs(Aw[i][col]); sel=i
        if sel<0: continue
        Aw[r],Aw[sel]=Aw[sel],Aw[r]
        pv=Aw[r][col]
        Aw[r]=[x/pv for x in Aw[r]]
        for i in range(n):
            if i!=r and abs(Aw[i][col])>1e-12:
                f=Aw[i][col]; Aw[i]=[Aw[i][j]-f*Aw[r][j] for j in range(n)]
        piv.append(col); r+=1
        if r==n: break
    free=[c for c in range(n) if c not in piv]
    if not free: return None
    # build a basis of the null space (one vector per free column)
    basis=[]
    for fc in free:
        v=[0.0]*n; v[fc]=1.0
        for ri,col in enumerate(piv):
            v[col]=-Aw[ri][fc]
        basis.append(v)
    # search combinations for a positive-definite representative
    import itertools
    best=None; bestcond=1e18
    coeffs=[-2,-1,-0.5,0.5,1,2]
    combos=itertools.product(coeffs,repeat=len(basis)) if len(basis)<=3 else [tuple([1]+[0]*(len(basis)-1))]
    for cc in combos:
        v=[sum(cc[b]*basis[b][i] for b in range(len(basis))) for i in range(n)]
        Q=sym(v); ev=jacobi_eig(Q)
        if ev[0]<0: ev=[-e for e in ev][::-1]; Q=[[-x for x in row] for row in Q]
        if ev[-1]>1e-9:  # PD
            cond=ev[0]/ev[-1]
            if cond<bestcond: bestcond=cond; best=(Q,sorted(ev))
    return best

# ---------- chain building ----------
def build_chain(L):
    d=pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    anchors=d['anchors']; words=d['words']
    chain=[tuple(anchors[0])]
    for i in range(len(words)):
        chain += [tuple(p) for p in word_interiors(anchors[i], words[i])]
        chain += [tuple(anchors[i+1])]
    return chain

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def extent(ch):
    xs=[p[0] for p in ch]; ys=[p[1] for p in ch]; zs=[p[2] for p in ch]
    return max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
def boxcount(ch,b):
    return len({(p[0]//b,p[1]//b,p[2]//b) for p in ch})

def local_ck(ch,rho):
    """exact sup over walk-point centres of #pts in Cheb-rho; also #arcs at argmax."""
    cell=rho if rho>0 else 1
    grid=defaultdict(list)
    for idx,p in enumerate(ch):
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(idx)
    best=0; best_arcs=0; maxarcs=0
    for qi in range(len(ch)):
        q=ch[qi]; gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        mem=[]
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2):
                for dz in(-2,-1,0,1,2):
                    for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(ch[j],q)<=rho: mem.append(j)
        mem.sort()
        arcs=1
        for a,b in zip(mem,mem[1:]):
            if b!=a+1: arcs+=1
        if arcs>maxarcs: maxarcs=arcs
        if len(mem)>best: best=len(mem); best_arcs=arcs
    return best,best_arcs,maxarcs

if __name__=='__main__':
    out={}
    print("="*70)
    print("PART A -- LINEAR ALGEBRA on M (affinity dimension foundation)")
    print("="*70)
    # eigenvalues: 3 (from decoupled coord 0) and roots of t^2+t+9 (block [[0,-3],[3,-1]])
    disc=1-36
    print(f"M = {M}, det = 27")
    print("eigenvalues: 3 ; (-1 +- i*sqrt(35))/2  -> moduli 3, 3, 3 (all = 27^(1/3))")
    print(f"  2x2 block [[0,-3],[3,-1]]: trace -1, det 9 => |eig|=sqrt(9)=3. ELLIPTIC.")
    # singular values of M^j
    print("\nBounded distortion: singular values of M^j vs 3^j")
    Qres=invariant_form()
    band_hi=0; band_lo=99
    sv_table={}
    for j in range(1,11):
        Mj=matpow(M,j)
        sv=singular_values(Mj)
        ratios=[s/3**j for s in sv]
        band_hi=max(band_hi,max(ratios)); band_lo=min(band_lo,min(ratios))
        sv_table[j]=[round(r,4) for r in ratios]
        if j<=6:
            print(f"  j={j}: sv/3^j = [{ratios[0]:.4f}, {ratios[1]:.4f}, {ratios[2]:.4f}]")
    print(f"  => sv(M^j)/3^j stays in [{band_lo:.4f}, {band_hi:.4f}] for j=1..10 (BOUNDED)")
    kappa_emp=band_hi/band_lo
    print(f"  empirical distortion kappa (hi/lo band) = {kappa_emp:.4f}")
    if Qres:
        Q,qev=Qres
        kappaQ=math.sqrt(qev[-1]/qev[0]) if qev[0]>1e-12 else None
        print(f"  invariant form Q solved: eig(Q)={[round(e,4) for e in qev]}, "
              f"cond^(1/2)=kappa={kappaQ:.4f}  (M = 3*O in Q-metric)")
    else:
        kappaQ=None; print("  invariant form: no null vector found")
    # singular values of M and M^-1 (single step)
    svM=singular_values(M)
    svMi=[1/s for s in svM]  # sv(M^-1) = 1/sv(M) reversed
    svMi_sorted=sorted(svMi,reverse=True)
    print(f"\n  sv(M) = [{svM[0]:.4f}, {svM[1]:.4f}, {svM[2]:.4f}]")
    print(f"  sv(M^-1) sorted desc = [{svMi_sorted[0]:.4f}, {svMi_sorted[1]:.4f}, {svMi_sorted[2]:.4f}]")
    out['linalg']=dict(sv_M=svM, sv_Minv=svMi_sorted, sv_over_3j=sv_table,
                       distortion_band=[band_lo,band_hi], kappa_emp=kappa_emp,
                       kappaQ=kappaQ)

    print("\n"+"="*70)
    print("PART B -- MEASUREMENT on construction chains")
    print("="*70)
    levels=[6,7,8]
    chains={}; prevN=None; prevE=None
    lam_meas={}
    for L in levels:
        ch=build_chain(L); chains[L]=ch
        N=len(ch); E=extent(ch)
        lam=N/prevN if prevN else float('nan')
        er=E/prevE if prevE else float('nan')
        d_ratio=math.log(lam)/math.log(er) if prevN and er>1 else float('nan')
        if prevN: lam_meas[L]=lam
        bc={}; b=1
        while b<=E: bc[b]=boxcount(ch,b); b*=3
        keys=sorted(bc)
        slopes=[round((math.log(bc[keys[i]])-math.log(bc[keys[i+1]]))/
                      (math.log(keys[i+1])-math.log(keys[i])),3) for i in range(len(keys)-1)]
        print(f"L{L}: N={N} extent={E} lambda={lam:.4f} extent_ratio={er:.4f} d=logL/logE={d_ratio:.4f}")
        print(f"     box-dim slopes(log3) = {slopes}")
        out[f'L{L}']=dict(N=N,extent=E,lam=lam,er=er,d_ratio=d_ratio,box_slopes=slopes)
        prevN=N; prevE=E

    # affinity dimension from measured lambda + structural cap
    lam_avg=sum(lam_meas.values())/len(lam_meas)
    d_meas=math.log(lam_avg)/math.log(3)
    d_cap=math.log(5)/math.log(3)   # lambda<=5 structural (<=4 interiors/edge)
    print(f"\nAFFINITY DIMENSION (pressure eqn collapses to log lambda/log 3 by bounded distortion):")
    print(f"  measured lambda_avg = {lam_avg:.4f}  =>  d = {d_meas:.4f}")
    print(f"  structural cap lambda<=5 =>  d <= {d_cap:.4f}  (rigorous but loose)")
    out['dimension']=dict(lam_avg=lam_avg,d_measured=d_meas,d_rigorous_cap=d_cap)

    # anisotropic vs isotropic pullback contraction (the Route-1 payoff)
    a1=svMi_sorted[0]; a2=svMi_sorted[1]  # semiaxes of M^-1 B per unit r
    for dtest in [d_meas,1.10]:
        aniso=a1*(a2**(dtest-1))
        iso=(4/9)  # linear framing used ||M^-1||=4/9 on r^1
        print(f"  d={dtest:.4f}: ANISOTROPIC pullback factor phi = sv1*sv2^(d-1) = "
              f"{aniso:.4f}  (<1 => recursion CONTRACTS)  vs isotropic 4/9 on r^d = {(4/9):.4f}")
    out['contraction']=dict(aniso_factor=svMi_sorted[0]*svMi_sorted[1]**(d_meas-1),
                            aniso_at_1p10=svMi_sorted[0]*svMi_sorted[1]**0.10,
                            isotropic_linear_coeff_prev="(4/9)(1+g)=20/9>1 DIVERGED")

    # worst-case local count c_k(q,r), fit, arc-incidence
    print("\nWorst-case local count c_k(q,r) and arc-incidence:")
    for L in levels:
        ch=chains[L]
        cs={}; arcs_at={}
        print(f"-- L{L} --  r:  c  arcs(argmax)  maxarcs   c/r^1.10")
        for rho in range(1,11):
            c,arcs,maxarcs=local_ck(ch,rho)
            cs[rho]=c; arcs_at[rho]=(arcs,maxarcs)
            print(f"     {rho:3d}: {c:3d}   {arcs:3d}         {maxarcs:3d}      {c/rho**1.10:.3f}")
        out[f'ck_L{L}']=dict(c={r:cs[r] for r in cs},
                             arcs={r:arcs_at[r][1] for r in arcs_at})
        # power fit
        xs=[math.log(r) for r in range(1,11)]; ys=[math.log(cs[r]) for r in range(1,11)]
        mx=sum(xs)/10; my=sum(ys)/10
        dfit=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
        Cfit=math.exp(my-dfit*mx)
        Csup=max(cs[r]/r**1.10 for r in range(1,11)); argC=max(range(1,11),key=lambda r:cs[r]/r**1.10)
        # arc exponent fit
        aa=[math.log(arcs_at[r][1]) for r in range(1,11)]
        may=sum(aa)/10
        adfit=sum((x-mx)*(y-may) for x,y in zip(xs,aa))/sum((x-mx)**2 for x in xs)
        print(f"   FIT L{L}: c ~ {Cfit:.3f}*r^{dfit:.4f} ; sup c/r^1.10 = {Csup:.3f} (r={argC}); "
              f"maxarcs ~ r^{adfit:.3f}")
        out[f'fit_L{L}']=dict(C=Cfit,d=dfit,C_for_d110=Csup,argC=argC,arc_exponent=adfit)

    # availability grade check at r=4.44 and r=10 using best fit constants
    print("\nAVAILABILITY GRADE CHECK (C=2, d=1.10):")
    for r in [4.44,10]:
        v=2*r**1.10
        print(f"  2*{r}^1.10 = {v:.3f}")
    json.dump(out,open('design/lemma/dim/route1_affinity_results.json','w'),indent=1)
    print("\nwrote design/lemma/dim/route1_affinity_results.json")
