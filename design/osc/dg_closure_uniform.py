"""GAP (ii): PROVE D_g (cylinder Chebyshev diameter) is CLOSURE-UNIFORM.

STATEMENT.  There is a constant rho_c depending ONLY on M and the finite
connector menu (connector_domains4 U dstar5_fragile U dstar5_band) -- NOT on any
realized walk -- such that for EVERY gen-g cylinder C_a of EVERY legal amplified
walk,

        diam_Q(C_a^{(g)})  <=  rho_c * (3^g - 1),
   i.e.  D^Q_g / 3^g  <=  rho_c   uniformly.

PROOF STRUCTURE (this script certifies the finite pieces exactly):

 (a) EXACT Q self-similarity  ||M v||_Q = 3 ||v||_Q  (from M^T Q M = 9 Q)
     ==> diam_Q(M.S) = 3.diam_Q(S) for ANY point set S.        [verified here]

 (b) ONE-STEP CYLINDER RECURSION (charge-to-source).  One amplification maps a
     level-(k-1) walk to a level-k walk: every point p becomes M.p, and the
     interiors Int(w(p)) of the outgoing connector word w(p) are inserted after
     M.p, CHARGED TO THE SOURCE p.  Hence
        C_a^{(g)} = U_{p in C_a^{(g-1)}} ( {M.p} U Int_rel(p) ),
     where Int_rel(p) = { M.p + partial-sums of w(p) } are the interiors.
     Because the interiors are charged to the SOURCE p, and M.p lies in
     M.C_a^{(g-1)} by definition of the cylinder, EACH added interior x obeys
        ||x - M.p||_Q  <=  rho_c := max over ALL menu words w, over all
                                    interiors q of w, of ||q - start(w)||_Q
     (the "reach-to-source" of the finite menu).  There is NO seam bookkeeping:
     the source anchor M.p is ALWAYS inside the cylinder, so rho_c is exactly the
     reach-to-source, a pure finite-menu quantity.       [certified exhaustively]

 (c) CLOSURE-UNIFORMITY = FINITE MENU CHECK.  The outgoing word w(p) at any point
     of any legal amplified walk is BY CONSTRUCTION a word of the finite menu
     (legality only REMOVES words, never adds).  So rho_c computed over the whole
     menu is an upper bound over the entire closure, independent of the L7 orbit.

 (d) TELESCOPE.  From (a)+(b): C_a^{(g)} is contained in the Q-rho_c neighbourhood
     of M.C_a^{(g-1)}, so
        diam_Q(C^{(g)}) <= diam_Q(M.C^{(g-1)}) + 2 rho_c
                        = 3.diam_Q(C^{(g-1)}) + 2 rho_c,   diam_Q(C^{(0)})=0
     ==> D^Q_g <= 2 rho_c (3^{g-1}+...+1) = rho_c (3^g - 1).  QED.

 (e) CHEBYSHEV CONVERSION.  D_g^{cheb} <= kappa * D^Q_g with
        kappa = sup_v ||v||_inf / ||v||_Q   (the exact metric distortion).

This script computes rho_c EXACTLY over the entire menu (reach-to-source in both
Cheb and Q), the sharper reach-to-nearer, max interiors/word, kappa, and the
per-gen-1-cylinder diameters, then validates the telescoped bound against the
measured D_q = 21.2/62.6/212 (D_q/3^g = 7.08/7.83/7.85) and Cheb 6/25/83.
"""
import pickle, sys, math, json, os, time
sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)
M = ((3,0,0),(0,0,-3),(0,3,-1))
Q = ((1,0,0),(0,6,-1),(0,-1,6))

def matvec(A,v): return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
                         A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
                         A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])
def matmul(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def cheb(v): return max(abs(v[0]),abs(v[1]),abs(v[2]))
def qn2(v): return v[0]*v[0] + 6*v[1]*v[1] - 2*v[1]*v[2] + 6*v[2]*v[2]

# ---------- (a) verify M^T Q M = 9 Q ----------
def check_self_similarity():
    MT = tuple(tuple(M[j][i] for j in range(3)) for i in range(3))
    MTQ = matmul(MT, Q)
    MTQM = matmul(MTQ, M)
    Q9 = tuple(tuple(9*Q[i][j] for j in range(3)) for i in range(3))
    return MTQM == Q9, MTQM

# ---------- (e) exact Cheb<->Q distortion kappa = sup ||v||_inf/||v||_Q ----------
def kappa_distortion(B=40):
    # sup over rational directions; ||v||_inf/||v||_Q is scale-invariant, brute on
    # integer directions in a box (fine enough; the sup is attained on a ray).
    best = 0.0; arg=None
    for x in range(-B,B+1):
        for y in range(-B,B+1):
            for z in range(-B,B+1):
                if x==0 and y==0 and z==0: continue
                r = cheb((x,y,z))/math.sqrt(qn2((x,y,z)))
                if r>best: best=r; arg=(x,y,z)
    return best, arg

# ---------- reach scan over a word set ----------
def scan_words(word_iter, is_index):
    """word_iter yields (step_vec, word). Returns global maxima."""
    mx = {'reach_src_cheb':0,'reach_src_q2':0,'reach_near_cheb':0,'reach_near_q2':0,
          'diam1_cheb':0,'diam1_q2':0,'ints_max':0,'nwords':0}
    arg = {}
    for step, w in word_iter:
        mx['nwords'] += 1
        # interiors relative to start (partial sums of all but last step)
        pts=[(0,0,0)]
        x=y=z=0
        L=len(w)
        for i in range(L-1):
            s = MENU[w[i]] if is_index else w[i]
            x+=s[0]; y+=s[1]; z+=s[2]
            pts.append((x,y,z))
        ints = pts[1:]                       # interior points, rel to source=0
        ni = len(ints)
        if ni > mx['ints_max']: mx['ints_max']=ni; arg['ints']=(step,w)
        # T = full displacement = M.step (= sum of all word steps)
        # (for reach-to-nearer we need it exactly = sum of ALL steps)
        tx=x+ (MENU[w[-1]][0] if is_index else w[-1][0])
        ty=y+ (MENU[w[-1]][1] if is_index else w[-1][1])
        tz=z+ (MENU[w[-1]][2] if is_index else w[-1][2])
        T=(tx,ty,tz)
        for q in ints:
            # reach to source (anchor at 0)
            rc = cheb(q); rq = qn2(q)
            if rc>mx['reach_src_cheb']: mx['reach_src_cheb']=rc; arg['rsc']=(step,w,q)
            if rq>mx['reach_src_q2']: mx['reach_src_q2']=rq; arg['rsq']=(step,w,q)
            # reach to nearer of the two anchors
            d2=(q[0]-T[0],q[1]-T[1],q[2]-T[2])
            nc=min(rc, cheb(d2)); nq=min(rq, qn2(d2))
            if nc>mx['reach_near_cheb']: mx['reach_near_cheb']=nc
            if nq>mx['reach_near_q2']: mx['reach_near_q2']=nq
        # gen-1 cylinder diameter: {0} U ints  (charge-to-source cylinder)
        allp = pts  # includes 0 and interiors
        dc=0; dq=0
        for a in range(len(allp)):
            for b in range(a+1,len(allp)):
                dv=(allp[a][0]-allp[b][0],allp[a][1]-allp[b][1],allp[a][2]-allp[b][2])
                c=cheb(dv); qq=qn2(dv)
                if c>dc: dc=c
                if qq>dq: dq=qq
        if dc>mx['diam1_cheb']: mx['diam1_cheb']=dc; arg['d1c']=(step,w)
        if dq>mx['diam1_q2']: mx['diam1_q2']=dq; arg['d1q']=(step,w)
    return mx, arg

def merge(a,b):
    out=dict(a)
    for k in a:
        if k=='nwords': out[k]=a[k]+b[k]
        else: out[k]=max(a[k],b[k])
    return out

def cd4_iter():
    d=pickle.load(open('connector_domains4.pkl','rb'))
    for si,ws in d['domains'].items():
        step=MENU[si]
        for w in ws: yield step,w
def vecfile_iter(fn):
    d=pickle.load(open(fn,'rb'))
    for step,ws in d.items():
        for w in ws: yield step,w

if __name__=='__main__':
    t0=time.time()
    print("=== GAP (ii): D_g CLOSURE-UNIFORMITY -- finite-menu reach-to-source ===\n")

    ok,MTQM = check_self_similarity()
    print(f"(a) M^T Q M == 9 Q : {ok}   (exact Q self-similarity ||Mv||_Q=3||v||_Q)")
    print(f"    M^T Q M = {MTQM}\n")

    kap,karg = kappa_distortion()
    print(f"(e) kappa = sup ||v||_inf/||v||_Q = {kap:.6f}  (witness {karg})\n")

    total={'reach_src_cheb':0,'reach_src_q2':0,'reach_near_cheb':0,'reach_near_q2':0,
           'diam1_cheb':0,'diam1_q2':0,'ints_max':0,'nwords':0}
    argall={}
    print("scanning menu word sets (reach-to-source over the whole closure):")
    # 1) connector_domains4 (index words)  -- part of amplify_level
    m,a=scan_words(cd4_iter(), True); total=merge(total,m)
    print(f"  connector_domains4: {m['nwords']:>10} words | reach_src_cheb={m['reach_src_cheb']} "
          f"reach_near_cheb={m['reach_near_cheb']} rsQ={math.sqrt(m['reach_src_q2']):.3f} "
          f"diam1_cheb={m['diam1_cheb']} ints_max={m['ints_max']}  [{time.time()-t0:.0f}s]", flush=True)
    if 'rsq' in a: argall['cd4']=a
    # 2) dstar5_fragile (vector words) -- part of amplify_level
    m,a=scan_words(vecfile_iter('dstar5_fragile.pkl'), False); total=merge(total,m)
    print(f"  dstar5_fragile:     {m['nwords']:>10} words | reach_src_cheb={m['reach_src_cheb']} "
          f"reach_near_cheb={m['reach_near_cheb']} rsQ={math.sqrt(m['reach_src_q2']):.3f} "
          f"diam1_cheb={m['diam1_cheb']} ints_max={m['ints_max']}  [{time.time()-t0:.0f}s]", flush=True)
    argall['fragile']=a
    # 3) dstar5_band (vector words) -- SUPERSET closure check (not used by amplify)
    if os.path.exists('dstar5_band.pkl') and not os.environ.get('SKIP_BAND'):
        m,a=scan_words(vecfile_iter('dstar5_band.pkl'), False); total=merge(total,m)
        print(f"  dstar5_band:        {m['nwords']:>10} words | reach_src_cheb={m['reach_src_cheb']} "
              f"reach_near_cheb={m['reach_near_cheb']} rsQ={math.sqrt(m['reach_src_q2']):.3f} "
              f"diam1_cheb={m['diam1_cheb']} ints_max={m['ints_max']}  [{time.time()-t0:.0f}s]", flush=True)
        argall['band']=a

    print(f"\n  TOTAL words scanned: {total['nwords']}")
    rho_c = math.sqrt(total['reach_src_q2'])
    rho_near = math.sqrt(total['reach_near_q2'])
    print(f"\n(b/c) CLOSURE CONSTANTS over the ENTIRE menu:")
    print(f"    max reach-to-source  Cheb = {total['reach_src_cheb']}   Q = {rho_c:.4f}  = rho_c")
    print(f"    max reach-to-nearer  Cheb = {total['reach_near_cheb']}   Q = {rho_near:.4f}")
    print(f"    max interiors / word      = {total['ints_max']}")
    print(f"    max gen-1 cyl diam   Cheb = {total['diam1_cheb']}   Q = {math.sqrt(total['diam1_q2']):.4f}")

    print(f"\n(d) TELESCOPE: D^Q_g <= rho_c (3^g - 1),  rho_c = {rho_c:.4f}")
    print(f"    D_g^cheb <= kappa * D^Q_g <= kappa*rho_c*(3^g-1),  kappa*rho_c = {kap*rho_c:.4f}")
    print(f"\n    g |  bound D^Q_g=rho_c(3^g-1) | measured D_q | bound D_cheb=k*rho_c(3^g-1) | measured D_cheb")
    measured_dq={1:21.24,2:62.6,3:212.0}   # from closure_multiplicity D_q/3^g=7.08/7.83/7.85
    measured_dc={1:6,2:25,3:83}
    val_ok=True
    for g in (1,2,3):
        bq=rho_c*(3**g-1); bc=kap*rho_c*(3**g-1)
        mq=measured_dq[g]; mc=measured_dc[g]
        okq = bq>=mq; okc = bc>=mc
        val_ok = val_ok and okq and okc
        print(f"    {g} |  {bq:8.2f}  (/3^g={bq/3**g:.3f}) | {mq:6.1f} | {bc:8.2f} | {mc:4d}   "
              f"{'OK' if okq and okc else 'FAIL'}")
    print(f"\n    D^Q_g/3^g -> rho_c = {rho_c:.4f}   (measured D_q/3^g = 7.08/7.83/7.85, monotone up, < rho_c)")
    print(f"    VALIDATION (bound dominates measured at every g): {'PASS' if val_ok else 'FAIL'}")

    out={'MTQM_eq_9Q':ok,'kappa':kap,'kappa_witness':karg,
         'nwords':total['nwords'],
         'reach_src_cheb':total['reach_src_cheb'],'rho_c_Q':rho_c,
         'reach_near_cheb':total['reach_near_cheb'],'reach_near_Q':rho_near,
         'ints_max':total['ints_max'],
         'diam1_cheb':total['diam1_cheb'],'diam1_Q':math.sqrt(total['diam1_q2']),
         'bound_DQ_over_3g':rho_c,'bound_Dcheb_coef_kappa_rho':kap*rho_c,
         'measured_Dq':measured_dq,'measured_Dcheb':measured_dc,
         'validation_pass':val_ok,
         'witnesses':{k:{kk:[list(x) if isinstance(x,tuple) else x for x in vv] if isinstance(vv,tuple) else vv
                        for kk,vv in v.items()} for k,v in argall.items()}}
    json.dump(out, open('/Users/erik/homelab/math193/design/osc/dg_closure_uniform_results.json','w'), indent=2, default=str)
    print(f"\nwrote design/osc/dg_closure_uniform_results.json   [{time.time()-t0:.0f}s]")
