"""
Two deliverables the earlier panels left open:

(A) FORCING SEARCH / crystallographic impossibility.
    Broad exact search over integer Euclidean similarities (Q=I): homothety x
    axis-twist Pythagorean AND homothety x integer-SO(3) (signed perms and
    quaternion rotations). Screen at EVERY prime dividing r. Report every
    all-prime passer and its twist. Claim under test:
      all-prime PASS  <=>  SNF(M)=r*I  <=>  M/r in GL_3(Z) & isometry
                       <=>  O'=M/r finite order (crystallographic: order in
                            {1,2,3,4,6}) <=> twist cos in {0,+-1/2,+-1} (RATIONAL).
    => irrational twist is INCOMPATIBLE with passing at all primes of r.

(B) THE WALK INSTRUMENT (task's explicit ask). Build a real menu-driven walk
    (levels 1-4), take triples of DISTINCT equal-generation cylinders, form the
    exact-integer collinearity vector Omega, and MEASURE the normalized
    cross-chord separation as a function of generation g via the PROVEN descent
    law Omega(M.)=cof(M).Omega. Report the excess-valuation slope
      E(g)=v_p(cof^g . Omega)-a*g
    over REAL cylinder triples (not random vectors). slope 0 = PLATEAU
    (absorbing, OSC-consistent); slope > 0 = DECAY (M_BAL3 failure). Also report
    the archimedean normalized separation to show it does NOT discriminate
    (the p-adic reading is the load-bearing one).

Exact integer everywhere. No floats in any valuation / collinearity test.
"""
from fractions import Fraction as F
from math import gcd
import itertools, random

# ---------- exact 3x3 integer linear algebra ----------
def det3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
def cof3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return [[ (e*i-f*h), -(d*i-f*g),  (d*h-e*g)],
            [-(b*i-c*h),  (a*i-c*g), -(a*h-b*g)],
            [ (b*f-c*e), -(a*f-c*d),  (a*e-b*d)]]
def matmul(A,B): return [[sum(A[r][k]*B[k][c] for k in range(3)) for c in range(3)] for r in range(3)]
def matvec(A,v): return [sum(A[r][k]*v[k] for k in range(3)) for r in range(3)]
def transpose(A): return [[A[c][r] for c in range(3)] for r in range(3)]
def cross(u,v): return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
def sub(a,b): return [a[0]-b[0],a[1]-b[1],a[2]-b[2]]
def Omega(p,q,r): return cross(sub(q,p),sub(r,p))
def vp_int(n,p):
    if n==0: return 10**9
    v=0; n=abs(n)
    while n%p==0: n//=p; v+=1
    return v
def vp_vec(v,p): return min(vp_int(x,p) for x in v)
def vp_mat(M,p): return min(vp_int(M[r][c],p) for r in range(3) for c in range(3))
def rank_mod_p(M,p):
    A=[[M[r][c]%p for c in range(3)] for r in range(3)]
    rank=0; row=0
    for col in range(3):
        piv=None
        for r in range(row,3):
            if A[r][col]%p!=0: piv=r; break
        if piv is None: continue
        A[row],A[piv]=A[piv],A[row]
        inv=pow(A[row][col],p-2,p)
        A[row]=[(x*inv)%p for x in A[row]]
        for r in range(3):
            if r!=row and A[r][col]%p!=0:
                fac=A[r][col]; A[r]=[(A[r][c]-fac*A[row][c])%p for c in range(3)]
        row+=1; rank+=1
    return rank
def prime_factors(n):
    n=abs(n); fs=set(); d=2
    while d*d<=n:
        while n%d==0: fs.add(d); n//=d
        d+=1
    if n>1: fs.add(n)
    return sorted(fs)
def rot_cos(M,r): return (F(sum(M[k][k] for k in range(3)),r)-1)/2
def niven_irr(cos): return cos not in {F(0),F(1,2),F(-1,2),F(1),F(-1)}
def is_similarity(M):
    G=matmul(transpose(M),M)
    for i in range(3):
        for j in range(3):
            if i!=j and G[i][j]!=0: return None
    d0=G[0][0]
    if G[1][1]!=d0 or G[2][2]!=d0: return None
    r=int(round(d0**0.5))
    return r if r*r==d0 else None
def matrix_order(O,cap=100):
    I=[[1,0,0],[0,1,0],[0,0,1]]; P=[row[:] for row in O]
    for n in range(1,cap+1):
        if P==I: return n
        P=matmul(P,O)
    return None

# ---------- (A) forcing search ----------
def screen_all_primes(M):
    r=is_similarity(M)
    if r is None or r<2: return None
    C=cof3(M); overall=True; per={}
    for p in prime_factors(r):
        k=vp_int(r,p); a=vp_mat(C,p)
        U=[[C[i][j]//p**a for j in range(3)] for i in range(3)]
        ru=rank_mod_p(U,p); ok=(ru==3 and a==2*k)
        per[p]=(k,a,ru,ok); overall=overall and ok
    return dict(r=r,per=per,overall=overall,cos=rot_cos(M,r),irr=niven_irr(rot_cos(M,r)))

def lipschitz_so3():
    """Integer SO(3) rotation matrices from Lipschitz quaternions (a,b,c,d),
    R = (1/N)[[a^2+b^2-c^2-d^2, 2(bc-ad), 2(bd+ac)],...] scaled by N=a^2+b^2+c^2+d^2
    gives an integer matrix of ratio N (a similarity), the classic integer-rotation
    construction. Enumerate small quaternions."""
    out=[]
    R=range(-3,4)
    for a in R:
        for b in R:
            for c in R:
                for d in R:
                    N=a*a+b*b+c*c+d*d
                    if N<2: continue
                    M=[[a*a+b*b-c*c-d*d, 2*(b*c-a*d),     2*(b*d+a*c)],
                       [2*(b*c+a*d),      a*a-b*b+c*c-d*d, 2*(c*d-a*b)],
                       [2*(b*d-a*c),      2*(c*d+a*b),     a*a-b*b-c*c+d*d]]
                    if is_similarity(M)==N:   # ratio N similarity (integer)
                        out.append((M,N,(a,b,c,d)))
    return out

def run_forcing_search():
    print("="*74)
    print("(A) FORCING SEARCH: all-prime passers among integer similarities")
    print("="*74)
    seen=set(); passers=[]; total=0
    # Family 1: homothety h * Pythagorean axis-twist
    def prim_pyth(lim):
        out=[]
        for m in range(2,lim):
            for a in range(1,m):
                b2=m*m-a*a; b=int(round(b2**0.5))
                if b>0 and b*b==b2 and gcd(gcd(a,b),m)==1: out.append((a,b,m))
        return out
    for (aa,bb,mm) in prim_pyth(40):
        for h in range(1,7):
            M=[[h*aa,-h*bb,0],[h*bb,h*aa,0],[0,0,h*mm]]
            key=tuple(map(tuple,M))
            if key in seen: continue
            seen.add(key); total+=1
            res=screen_all_primes(M)
            if res and res['overall']: passers.append((M,res))
    # Family 2: homothety h * integer SO(3) (Lipschitz) -- fully 3D-mixing twists
    for (O,N,q) in lipschitz_so3():
        # O has ratio N; also test h*O and, to get UNIT-ratio twist O/sqrt? skip.
        for h in range(1,5):
            M=[[h*O[i][j] for j in range(3)] for i in range(3)]
            key=tuple(map(tuple,M))
            if key in seen: continue
            seen.add(key); total+=1
            res=screen_all_primes(M)
            if res and res['overall']: passers.append((M,res))
    # Family 3: homothety h * signed-permutation (finite-order twist, control)
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product([1,-1],repeat=3):
            O=[[0,0,0],[0,0,0],[0,0,0]]
            for i in range(3): O[i][perm[i]]=signs[i]
            if det3(O)!=1: continue
            for h in range(2,8):
                M=[[h*O[i][j] for j in range(3)] for i in range(3)]
                key=tuple(map(tuple,M))
                if key in seen: continue
                seen.add(key); total+=1
                res=screen_all_primes(M)
                if res and res['overall']: passers.append((M,res))
    print(f"screened {total} integer similarities; ALL-PRIME passers: {len(passers)}")
    irr=[x for x in passers if x[1]['irr']]
    print(f"  of which IRRATIONAL-twist: {len(irr)}")
    print("\n  sample of all-prime passers (M, r, cos twist, irrational?, O'=M/r order):")
    for (M,res) in passers[:25]:
        r=res['r']; O=[[M[i][j]//r for j in range(3)] for i in range(3)] if all(M[i][j]%r==0 for i in range(3) for j in range(3)) else None
        order=matrix_order(O) if O else None
        print(f"    r={r:3d} cos={str(res['cos']):>5} irr={res['irr']!s:5} "
              f"M/r-integer={O is not None} O'-order={order}  M={M}")
    print("\n  VERDICT:", "NO irrational-twist all-prime passer exists in the search"
          if len(irr)==0 else "found irrational passer -- investigate!")
    return passers,irr

# ---------- (B) walk instrument ----------
def build_walk_points(M, menu, depth):
    """Expanding-integer cylinder anchor points.
    IFS f_i(x)=M^{-1}(x+d_i). Real gen-g anchor of word w=(i1..ig):
       P_real = sum_j M^{-j} d_{i_j}.  Expanding integer coord:
       Y_w = M^g P_real = sum_j M^{g-j} d_{i_j}  in Z^3.
    Returns dict g -> list of (word, Y_w)."""
    Mpow=[[[1,0,0],[0,1,0],[0,0,1]]]  # M^0
    for _ in range(depth): Mpow.append(matmul(Mpow[-1],M))
    out={}
    for g in range(1,depth+1):
        pts=[]
        for w in itertools.product(range(len(menu)),repeat=g):
            Y=[0,0,0]
            for j in range(1,g+1):
                # term M^{g-j} d_{w[j-1]}
                Mp=Mpow[g-j]; d=menu[w[j-1]]
                dv=matvec(Mp,d)
                Y=[Y[0]+dv[0],Y[1]+dv[1],Y[2]+dv[2]]
            pts.append((w,Y))
        out[g]=pts
    return out

# archimedean magnitude of the collinearity form Omega (an AREA): |Omega|^2 in a
# quadratic form G. Omega descends by cof(M); its archimedean magnitude, normalized
# by scale^2 per generation (r^{2g} in length => r^{4g} for the squared magnitude),
# is EXACTLY CONSTANT when G is the M-conformal DUAL form (M^T Q M = r^2 Q).
# For M_BAL3, Q=[[1,0,0],[0,6,-1],[0,-1,6]] and the dual (adjugate) form that makes
# the cross-product magnitude conformal is Qdual = adj(Q) = [[35,0,0],[0,6,1],[0,1,6]]
# (|Omega|^2_Qdual = 35x^2+6y^2+2yz+6z^2). Euclidean (G=I) is NOT M-conformal and
# oscillates -- a pure metric artifact, not geometry.
QDUAL_BAL3=[[35,0,0],[0,6,1],[0,1,6]]
def qform_sq(v,G): return sum(v[i]*G[i][j]*v[j] for i in range(3) for j in range(3))

def walk_separation(name, M, r, p, menu, depth=4, gens=8, max_triples=4000, seed=1, Qform=None):
    """Take triples of DISTINCT equal-generation cylinders, form primitive Omega_0,
    push through the descent cof(M)^g, measure BOTH: (p-adic) excess valuation
    E(g)=v_p(cof^g.Omega)-a*g, AND (ARCHIMEDEAN, the OSC-relevant quantity) the
    normalized magnitude arch(g)=|cof^g.Omega|^2_G / r^{4g}. The two DIVERGE: E(g)
    climbs (3-adic parallelism) while arch(g) is CONSTANT (conformal, plateau)."""
    print("-"*74)
    print(f"WALK {name}: M={M} r={r} p={p} menu={menu} depth={depth}")
    G = Qform if Qform is not None else [[1,0,0],[0,1,0],[0,0,1]]
    C=cof3(M); a=vp_mat(C,p)
    print(f"   cof={C}  a=vp_p(cof)={a}  2*vp_p(r)={2*vp_int(r,p)}  "
          f"rank(U mod {p})={rank_mod_p([[C[i][j]//p**a for j in range(3)] for i in range(3)],p)}")
    pts_by_g=build_walk_points(M,menu,depth)
    rnd=random.Random(seed)
    # collect real primitive Omega_0 from DISTINCT equal-generation cylinders
    # use the deepest built generation for genuine distinct cylinders
    gg=depth
    pts=pts_by_g[gg]
    seeds=[]
    tries=0
    while len(seeds)<400 and tries<20000:
        tries+=1
        ta,tb,tc=rnd.sample(pts,3)
        wa,Ya=ta; wb,Yb=tb; wc,Yc=tc
        if wa==wb or wb==wc or wa==wc: continue
        om=Omega(Ya,Yb,Yc)
        if all(x==0 for x in om): continue          # collinear -> skip
        vp0=vp_vec(om,p)
        prim=[x//p**vp0 for x in om]                # strip existing p-part -> primitive
        seeds.append(prim)
    if not seeds:
        print("   (could not form non-collinear distinct-cylinder triples)"); return None
    # descend: E(g)=vp(cof^g . prim)-a*g  AND  arch(g)=|cof^g.prim|^2_G / r^{4g}
    maxE=[0]*(gens+1); meanE=[0.0]*(gens+1)
    # ARCHIMEDEAN array (was dead): normalized squared magnitude, min & mean over seeds.
    r4=r**4
    arch_min=[None]*(gens+1); arch_mean=[0.0]*(gens+1)
    arch_const=True; arch_ref={}
    for prim in seeds:
        w=prim[:]
        base=qform_sq(prim,G)                        # g=0 magnitude of this Omega
        for g in range(1,gens+1):
            w=matvec(C,w)
            E=vp_vec(w,p)-a*g
            if E>maxE[g]: maxE[g]=E
            meanE[g]+=E
            # archimedean: |cof^g.Omega|^2_G / r^{4g}, expected == base (conformal)
            amag = qform_sq(w,G)
            norm = F(amag, r4**g)                     # exact rational normalized magnitude
            if arch_min[g] is None or norm<arch_min[g]: arch_min[g]=norm
            arch_mean[g]+=float(norm)
            # constancy check: normalized magnitude should equal the g=0 base exactly
            if norm != base: arch_const=False
    n=len(seeds)
    meanE=[x/n for x in meanE]; arch_mean=[x/n for x in arch_mean[:]]
    print(f"   {n} DISTINCT-cylinder real triples.")
    print(f"   [p-adic]  E(g)=v_{p}(cof^g.Omega)-a*g   (the quantity the 5 rounds read):")
    print(f"     max  E(g) : {maxE}")
    print(f"     mean E(g) : {[round(x,2) for x in meanE]}")
    print(f"   [ARCHIMEDEAN, OSC-relevant]  |cof^g.Omega|^2_G / r^{{4g}}   (G={'Qdual' if Qform else 'Euclid'}):")
    print(f"     mean arch(g): {[round(x,3) for x in arch_mean[1:]]}")
    print(f"     min  arch(g): {[str(x) for x in arch_min[1:]]}")
    print(f"     EXACTLY CONSTANT across g (== g=0 magnitude)?  {arch_const}")
    slope_max=(maxE[-1]-maxE[1])/(gens-1) if gens>1 else 0
    slope_mean=(meanE[-1]-meanE[1])/(gens-1) if gens>1 else 0
    epadic=("PLATEAU (E=0, absorbing)" if maxE[-1]==0
             else f"E slope~{slope_mean:.2f}/gen (3-adic parallelism)")
    archv=("CONSTANT (conformal plateau => archimedean separation does NOT decay)"
           if arch_const else "NOT constant (metric artifact -- use conformal G)")
    print(f"   => p-adic reading: {epadic}")
    print(f"   => archimedean reading: {archv}")
    print(f"   => DIVERGENCE: p-adic E moves while archimedean magnitude is fixed"
          if (not arch_const)==False and slope_mean!=0 else
          f"   => (compare the two columns above)")
    return dict(a=a,maxE=maxE,meanE=meanE,slope_mean=slope_mean,plateau=(maxE[-1]==0),
                arch_const=arch_const,arch_mean=arch_mean)

def run_walk():
    print("\n"+"="*74)
    print("(B) WALK INSTRUMENT: real menu-driven distinct-cylinder separation")
    print("="*74)
    res={}
    # menu: small non-degenerate integer offsets giving non-collinear triples
    menu=[[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1]]
    # M_BAL3 baseline (its metric Q!=I but the descent law Omega->cof.Omega is
    # basis-free; screen at its prime p=3)
    Mbal3=[[3,0,0],[0,0,-3],[0,3,-1]]
    res['M_BAL3_p3']=walk_separation("M_BAL3 (baseline)",Mbal3,3,3,menu,depth=4,Qform=QDUAL_BAL3)
    # M'=2A at p=2 (its 'good' homothety prime)
    Mp=[[6,-8,0],[8,6,0],[0,0,10]]
    res['Mprime2A_p2']=walk_separation("M'=2A at p=2 (homothety prime)",Mp,10,2,menu,depth=4)
    # M'=2A at p=5 (the OTHER prime of r=10 -- MUST also be absorbing for OSC)
    res['Mprime2A_p5']=walk_separation("M'=2A at p=5 (twist prime -- also divides r!)",Mp,10,5,menu,depth=4)
    # control: a genuine all-prime passer with RATIONAL twist (homothety*rotation)
    #   e.g. M=2*O with O an order-4 integer rotation: r=2, only prime 2, SNF=2I.
    Mrot=[[0,-2,0],[2,0,0],[0,0,2]]   # 2 * 90deg rotation about z (finite order twist)
    res['control_2rot_p2']=walk_separation("control 2*Rot90z (all-prime PASS, RATIONAL twist)",Mrot,2,2,menu,depth=4)
    return res

if __name__=="__main__":
    passers,irr=run_forcing_search()
    walk=run_walk()
    print("\n"+"#"*74)
    print("SUMMARY")
    print("#"*74)
    print("(A) All-prime passers found:", len(passers),
          "| irrational-twist among them:", len(irr),
          "->", "IMPOSSIBILITY CONFIRMED" if len(irr)==0 else "COUNTEREXAMPLE")
    print("(B) Walk excess-valuation slopes (0=absorbing plateau, >0=decay):")
    for k,v in walk.items():
        if v: print(f"    {k:22s}: a={v['a']} E(g)_max={v['maxE'][-1]} "
                     f"slope_mean={v['slope_mean']:.2f} "
                     f"{'PLATEAU/absorbing' if v['plateau'] else 'DECAY'}")
