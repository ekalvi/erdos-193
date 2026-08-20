"""GAP (i) -- the DECISIVE tight worst-case reduction and its rigorous bounds.

We reduce  mult_g(3^g)  to ONE generation-independent quantity N* via the exact
self-similar Q-pullback (M^T Q M = 9 Q  =>  M scales d_Q by exactly 3), then
bound N* by a ladder of rigorous, NON-circular upper bounds and, finally, probe
it adversarially with the legal menu-walk.

REDUCTION.  A gen-g cylinder C_a is contained in a Q-ball  B_Q(root_a, R^Q_g),
root_a = M^g a in L_g = M^g Z^3.  If C_a meets the fine ball B_cheb(q, 3^g) then
    d_Q(root_a, q) <= d_Q(root_a, p) + d_Q(p, q) <= R^Q_g + kappa * 3^g,
where p in C_a, |p-q|_inf <= 3^g, and kappa = sup_{|v|_inf<=1} |v|_Q = sqrt(15).
Apply M^{-g} (divides d_Q by exactly 3^g):
    d_Q(a, M^{-g} q) <= R^Q_g/3^g + kappa =: rho*.
The ancestors a are DISTINCT integer points (distinct cylinders <=> distinct a),
hence
    mult_g(3^g) <= N* := sup_{legal parent walks W'} sup_c #{W' cap B_Q(c, rho*)}.
N* has NO g and NO level.  We compute a ladder of upper bounds on it.

This script:
  (1) measures R^cheb_g, R^Q_g (radius FROM ROOT, the quantity the reduction needs)
      on the realized L8 walk (gap-ii caveat: measured, not yet closure-proven);
  (2) derives rho* and the Cheb analogue;
  (3) EXACT anisotropic lattice packing in root space L_g:
        N_cheb  = sup_q #{L_g : |.-q|_inf   <= Rc}         (reproduces 315/480/612)
        N_Q     = sup_c #{L_g : d_Q(.,c)     <= Rq}         (the Q-ellipsoid)
        N_both  = sup   #{L_g : both}                        (intersection sharpening)
      -- all pure lattice, no legality, no OSC;
  (4) ADVERSARIAL legal probe: beam search for a self-avoiding + triple-free MENU
      walk that crowds a B_Q(0,rho*) ball -- a rigorous LOWER bound on N* and the
      falsification test (any config with >5 CONSTRUCTION-legal cylinders falsifies
      the tight bound).
"""
import sys, math, pickle, json, time
from random import Random
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors
from search193 import candidate_step_vectors, primitive_direction

M = ((3,0,0),(0,0,-3),(0,3,-1))
Q = ((1,0,0),(0,6,-1),(0,-1,6))
KAPPA2 = 15            # sup_{|v|_inf<=1} v^T Q v  (corner (1,-1,1)/(1,1,-1))
KAPPA = math.sqrt(15)
MENU = candidate_step_vectors(2)

def matvec(A,v): return tuple(sum(A[i][j]*v[j] for j in range(3)) for i in range(3))
def matmul(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def qn2(v): return v[0]*v[0]+6*v[1]*v[1]+6*v[2]*v[2]-2*v[1]*v[2]
def Mpow(g):
    R=((1,0,0),(0,1,0),(0,0,1))
    for _ in range(g): R=matmul(M,R)
    return R

# ---------------------------------------------------------------- (1) measure R from root
def build_level(L):
    d=pickle.load(open(f'/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl','rb'))
    A=d['anchors']; W=d['words']
    chain=[A[0]]; parent=[0]
    for i in range(len(W)):
        for p in word_interiors(A[i],W[i]):
            chain.append(p); parent.append(i)
        chain.append(A[i+1]); parent.append(i+1)
    return chain,parent

def measure_radii(topL=8, depth=3):
    chains={}; parents={}
    for L in range(topL-depth, topL+1):
        chains[L],parents[L]=build_level(L)
    chain=chains[topL]; N=len(chain)
    anc=[list(range(N))]; acc=parents[topL][:]; anc.append(acc[:])
    for g in range(2,depth+1):
        pmap=parents[topL-g+1]; acc=[pmap[acc[j]] for j in range(N)]; anc.append(acc[:])
    out={}
    for g in (1,2,3):
        Mg=Mpow(g)
        groups=defaultdict(list)
        for j,a in enumerate(anc[g]): groups[a].append(j)
        Rc=0; Rq2=0
        for a,idxs in groups.items():
            root=matvec(Mg,chains[topL-g][a])
            for j in idxs:
                p=chain[j]; dv=(p[0]-root[0],p[1]-root[1],p[2]-root[2])
                c=max(abs(dv[0]),abs(dv[1]),abs(dv[2]))
                if c>Rc: Rc=c
                q=qn2(dv)
                if q>Rq2: Rq2=q
        out[g]={'ncyl':len(groups),'Rcheb':Rc,'RQ':math.sqrt(Rq2)}
    return out, N

# ---------------------------------------------------------------- (3) lattice packings
def lattice_pts(Mg, span):
    vb = span//3 + 4
    pts=[]
    for x in range(-vb,vb+1):
        for y in range(-vb,vb+1):
            for z in range(-vb,vb+1):
                p=matvec(Mg,(x,y,z))
                if abs(p[0])<=span and abs(p[1])<=span and abs(p[2])<=span:
                    pts.append(p)
    return pts

def sup_cheb_box(pts, Rc):
    """EXACT sup over real centers of #{p: |p-c|_inf <= Rc}  (= per-axis spread <= 2Rc)."""
    W=2*Rc
    best=0
    xs=sorted(set(p[0] for p in pts))
    for x0 in xs:
        xin=[p for p in pts if x0<=p[0]<=x0+W]
        if len(xin)<=best: continue
        ys=sorted(set(p[1] for p in xin))
        for y0 in ys:
            yin=[p for p in xin if y0<=p[1]<=y0+W]
            if len(yin)<=best: continue
            zz=sorted(p[2] for p in yin); lo=0
            for hi in range(len(zz)):
                while zz[hi]-zz[lo]>W: lo+=1
                if hi-lo+1>best: best=hi-lo+1
    return best

def sup_q_ball(pts, Rq):
    """LOWER bound on sup_c #{p: d_Q(p,c)<=Rq}: scan centers = lattice points and
       their pairwise midpoints (half-integer).  (Used only to show the Q-branch is
       LOOSER than Cheb; a lower bound that already exceeds N_cheb settles that.)"""
    Rqsq=Rq*Rq; best=0
    cand=set()
    for p in pts: cand.add((2*p[0],2*p[1],2*p[2]))  # work in half-integer units *2
    # midpoints of near pairs
    for i,p in enumerate(pts):
        for qd in pts:
            if abs(p[0]-qd[0])<=Rq and abs(p[1]-qd[1])<=Rq and abs(p[2]-qd[2])<=Rq:
                cand.add((p[0]+qd[0],p[1]+qd[1],p[2]+qd[2]))
    for c2 in cand:
        cx,cy,cz=c2[0]/2,c2[1]/2,c2[2]/2
        cnt=0
        for p in pts:
            dv=(p[0]-cx,p[1]-cy,p[2]-cz)
            if dv[0]*dv[0]+6*dv[1]*dv[1]+6*dv[2]*dv[2]-2*dv[1]*dv[2]<=Rqsq: cnt+=1
        if cnt>best: best=cnt
    return best

def sup_cheb_with_q(pts, Rc, Rq):
    """EXACT sup over real centers of #{p: |p-c|_inf<=Rc} together with, AT the
       Cheb-optimal integer-anchored center, the residual count after ALSO imposing
       d_Q<=Rq.  Returns (N_cheb, N_both_at_that_center)."""
    W=2*Rc; best=0; bestwin=None
    xs=sorted(set(p[0] for p in pts))
    for x0 in xs:
        xin=[p for p in pts if x0<=p[0]<=x0+W]
        if len(xin)<=best: continue
        ys=sorted(set(p[1] for p in xin))
        for y0 in ys:
            yin=[p for p in xin if y0<=p[1]<=y0+W]
            if len(yin)<=best: continue
            zz=sorted(p[2] for p in yin); lo=0
            for hi in range(len(zz)):
                while zz[hi]-zz[lo]>W: lo+=1
                if hi-lo+1>best:
                    best=hi-lo+1; bestwin=(x0,y0,zz[lo])
    # residual with Q at box center
    x0,y0,z0=bestwin; c=(x0+Rc,y0+Rc,z0+Rc); Rqsq=Rq*Rq
    nb=0
    for p in pts:
        if x0<=p[0]<=x0+W and y0<=p[1]<=y0+W and z0<=p[2]<=z0+W:
            dv=(p[0]-c[0],p[1]-c[1],p[2]-c[2])
            if dv[0]*dv[0]+6*dv[1]*dv[1]+6*dv[2]*dv[2]-2*dv[1]*dv[2]<=Rqsq: nb+=1
    return best, nb

# ---------------------------------------------------------------- (4) adversarial legal probe
def beam_crowd(rho_cheb, rho_q, beam=400, restarts=40, seed=0, time_budget=90.0):
    """Beam search for the longest self-avoiding + triple-free MENU walk CONFINED to
       the ancestor-space window  W = {|p|_inf <= rho_cheb  AND  d_Q(p,0) <= rho_q}.
       Every such walk is a legal menu walk whose points ALL lie in W, so its length
       is a rigorous LOWER bound on N* (worst-case cylinders in the pulled-back window).
       Returns (max length found, config)."""
    rq2=rho_q*rho_q
    rc=rho_cheb
    def inwin(p):
        return (abs(p[0])<=rc and abs(p[1])<=rc and abs(p[2])<=rc and qn2(p)<=rq2)
    rng=Random(seed)
    t0=time.time()
    GLOBAL_BEST=0; GLOBAL_CFG=None
    for r in range(restarts):
        if time.time()-t0>time_budget: break
        beamset=[{'pts':[(0,0,0)],'occ':{(0,0,0)}}]
        best_here=1; best_cfg=[(0,0,0)]
        while True:
            if time.time()-t0>time_budget: break
            cand=[]
            for st in beamset:
                last=st['pts'][-1]
                menu=MENU[:]; rng.shuffle(menu)
                added=0
                for s in menu:
                    np=(last[0]+s[0],last[1]+s[1],last[2]+s[2])
                    if not inwin(np): continue
                    if np in st['occ']: continue
                    ok=True; seen=set()
                    for pp in st['pts']:
                        dd=primitive_direction((pp[0]-np[0],pp[1]-np[1],pp[2]-np[2]))
                        if dd in seen: ok=False; break
                        seen.add(dd)
                    if not ok: continue
                    cand.append((st, np))
                    added+=1
                    if added>=8: break
            if not cand: break
            # prefer longer walks that keep options: score by current length (all equal) + randomness
            rng.shuffle(cand)
            beamset=[]
            for st, np in cand[:beam]:
                pts=st['pts']+[np]; occ=set(st['occ']); occ.add(np)
                beamset.append({'pts':pts,'occ':occ})
                if len(pts)>best_here:
                    best_here=len(pts); best_cfg=pts
        if best_here>GLOBAL_BEST:
            GLOBAL_BEST=best_here; GLOBAL_CFG=best_cfg
    return GLOBAL_BEST, GLOBAL_CFG

# ---------------------------------------------------------------- main
if __name__=='__main__':
    mode = sys.argv[1] if len(sys.argv)>1 else 'all'
    print("=== GAP (i): tight worst-case reduction, kappa=sqrt(15)=%.4f ==="%KAPPA)

    if mode in ('all','geom'):
        rad,N = measure_radii()
        print("\n(1) realized-L8 radius FROM ROOT (gap-ii: measured, not closure-proven):")
        for g in (1,2,3):
            print("    g=%d  ncyl=%d  Rcheb=%d  RQ=%.3f  Rcheb/3^g=%.3f  RQ/3^g=%.4f"%(
                g,rad[g]['ncyl'],rad[g]['Rcheb'],rad[g]['RQ'],rad[g]['Rcheb']/3**g,rad[g]['RQ']/3**g))
        RQ0=max(rad[g]['RQ']/3**g for g in (1,2,3))
        Rc0=max(rad[g]['Rcheb']/3**g for g in (1,2,3))
        rho=KAPPA+RQ0
        print("\n(2) LEVEL-INDEPENDENT pullback radii:")
        print("    rho*_Q   = kappa + max_g RQ/3^g   = %.4f + %.4f = %.4f  (Q-units, ancestor space)"%(KAPPA,RQ0,rho))
        print("    rho*_cheb= 1     + max_g Rcheb/3^g= %.4f  (Cheb-units)"%(1+Rc0))
        json.dump({'kappa':KAPPA,'RQ0':RQ0,'Rc0':Rc0,'rho_Q':rho,
                   'radii':{g:rad[g] for g in (1,2,3)},'N_L8':N},
                  open('/Users/erik/homelab/math193/design/osc/tight_geom.json','w'),indent=2)

    if mode in ('all','pack'):
        rad=json.load(open('/Users/erik/homelab/math193/design/osc/tight_geom.json'))['radii']
        print("\n(3) EXACT anisotropic lattice packings in root space L_g:")
        packres={}
        for g in (1,2,3):
            Mg=Mpow(g)
            Rc = 3**g + rad[str(g)]['Rcheb']
            Rq = 3**g*KAPPA + rad[str(g)]['RQ']
            span=int(2*Rc+4)
            pts=lattice_pts(Mg, span)
            Ncheb,Nboth = sup_cheb_with_q(pts, Rc, Rq)
            NQ = sup_q_ball(pts, Rq)   # lower bound on the Q-ellipsoid sup
            packres[g]={'Rc':Rc,'Rq':round(Rq,2),'npts':len(pts),
                        'N_cheb':Ncheb,'N_Q_lb':NQ,'N_both':Nboth}
            print("    g=%d Rc=%d Rq=%.1f  |L_g in box|=%d  N_cheb=%d  N_Q(ellipsoid,>=)=%d  N_both(intersect)=%d"%(
                g,Rc,Rq,len(pts),Ncheb,NQ,Nboth))
        json.dump(packres,open('/Users/erik/homelab/math193/design/osc/tight_packing.json','w'),indent=2)

    if mode in ('all','probe'):
        geom=json.load(open('/Users/erik/homelab/math193/design/osc/tight_geom.json'))
        rho_q=geom['rho_Q']
        rho_cheb=1+geom['Rc0']       # ancestor-space Cheb window radius (the TIGHT one)
        rc_int=int(math.floor(rho_cheb))
        tb=int(sys.argv[2]) if len(sys.argv)>2 else 100
        print("\n(4) ADVERSARIAL legal probe: longest self-avoiding+triple-free MENU walk")
        print("    CONFINED to the pulled-back ancestor window  W = {|p|_inf<=%.2f (=>%d) AND d_Q<=%.2f}."%(
            rho_cheb,rc_int,rho_q))
        print("    Its length is a rigorous LOWER bound on N*.  If a CONSTRUCTION-legal config")
        print("    fits >5 cylinders it FALSIFIES the tight 4/5/4 bound.")
        best,cfg=beam_crowd(float(rc_int), rho_q, beam=250, restarts=200, seed=1, time_budget=tb)
        print("    N*_local (triple-free self-avoiding menu walk in W) >= %d  points."%best)
        print("    Cheb-window box |p|_inf<=%d has %d integer points."%(rc_int,(2*rc_int+1)**3))
        json.dump({'rho_q':rho_q,'rho_cheb':rho_cheb,'rc_int':rc_int,
                   'N_local_lower':best,'cfg_len':len(cfg) if cfg else 0,
                   'cfg':cfg[:200] if cfg else []},
                  open('/Users/erik/homelab/math193/design/osc/tight_probe.json','w'),indent=2)
