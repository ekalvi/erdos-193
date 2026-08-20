"""AHLFORS d-REGULARITY residue: uniform bound c_k(q,r) <= C * r^d, r in [1,10].

Deliverables:
 (1) walk-centred AND exact-all-lattice-centre max c_k(r), r=1..10, at L6 & L7.
 (2) tight constants: C_lin = max_r c(r)/r  and  C_d = max_r c(r)/r^d,
     d = log(lam)/log 3.  A LINEAR bound c<=C_lin*r implies c<=C_lin*r^d on r>=1
     (since d>1), and also the per-scale ratio c(3r)/c(r) vs lam.
 (3) ROUTE-2 anti-stacking test: split walk into ANCHORS (M-images) and fresh
     STITCH INTERIORS.  Refill lemma claims I(q,r) := #interiors in B(q,r) <= E*r,
     level-uniform E.  Correlate per-ball crowding with the stitch word length
     actually used -> does 'shortest legal' force short words in crowded balls?

Exact all-lattice max via grid of side (2r+1): a Cheb-window of width 2r+1
overlaps <=2 cells/axis, so candidate points for any optimal integer centre lie
in a 2x2x2 block of cells; brute the small candidate set exactly.
"""
import pickle, sys, math
from collections import defaultdict
from gate_run import word_interiors

LAM = 3.37                      # box/spectral growth (boxcount er~3.0, lam~3.37)
D = math.log(LAM) / math.log(3) # ~ 1.106

def build_split(L):
    d = pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    anchors = d['anchors']; words = d['words']
    A = [tuple(anchors[0])]                 # anchor points
    I = []                                  # fresh stitch-interior points
    wl_of = {}                              # interior point -> word length (#steps)
    for i in range(len(words)):
        ints = word_interiors(anchors[i], words[i])
        for p in ints:
            I.append(p); wl_of[p] = len(words[i])
        A.append(tuple(anchors[i+1]))
    return A, I, wl_of

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def walk_centre_max(pts, r):
    cell = max(r,1)
    grid = defaultdict(list)
    for p in pts:
        grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    best = 0
    for q in pts:
        gx,gy,gz = q[0]//cell,q[1]//cell,q[2]//cell
        c = 0
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2):
                for dz in(-2,-1,0,1,2):
                    for p in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(p,q)<=r: c+=1
        if c>best: best=c
    return best

def exact_lattice_max(pts, r):
    """Exact max over ALL integer centres q of #{p: cheb(p,q)<=r}."""
    w = 2*r+1
    grid = defaultdict(list)
    for p in pts:
        grid[(p[0]//w,p[1]//w,p[2]//w)].append(p)
    best = 0
    seen = set()
    for key,cellpts in grid.items():
        gx,gy,gz = key
        # candidate points = this cell + neighbours in +/-1 (a width-w window
        # anchored anywhere touching this cell lies within these 3^3 cells;
        # 2x2x2 suffices but 3^3 is safe & still small)
        cand = []
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    cand += grid.get((gx+dx,gy+dy,gz+dz),())
        if not cand: continue
        # optimal integer centre: its window [qx-r,qx+r] can be taken with left
        # edge = some point's x (slide until a point enters). Enumerate windows
        # anchored at each candidate's coord as min corner.
        m = len(cand)
        # dedupe candidate list per anchor-cell to avoid rework
        for a in cand:
            ax = a[0]
            if ax < gx*w or ax >= (gx+1)*w:  # only anchor on points in THIS cell
                continue
            # x-window [ax, ax+2r]
            sx = [p for p in cand if ax <= p[0] <= ax+2*r]
            if len(sx) <= best: continue
            for b in sx:
                by = b[1]
                sy = [p for p in sx if by <= p[1] <= by+2*r]
                if len(sy) <= best: continue
                # z sliding window width 2r+1
                zs = sorted(p[2] for p in sy)
                j = 0
                for k in range(len(zs)):
                    while zs[k]-zs[j] > 2*r: j += 1
                    if k-j+1 > best: best = k-j+1
    return best

def refill_test(A, I, wl_of, r):
    """I(q,r)=#interiors in B(q,r); A(q,r)=#anchors; report max I/r, and the
    crowding<->word-length correlation over interior-centred balls."""
    cell = max(r,1)
    gA = defaultdict(list); gI = defaultdict(list)
    for p in A: gA[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    for p in I: gI[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    def count(grid,q):
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell; c=0
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2):
                for dz in(-2,-1,0,1,2):
                    for p in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(p,q)<=r: c+=1
        return c
    maxI=0; maxIq=None
    # correlation samples: (crowding=A+I, maxwordlen in ball) over interior centres
    samples=[]  # (total_crowd, longest_word_in_ball)
    step = max(1, len(I)//4000)   # subsample for speed
    for idx in range(0,len(I),step):
        q=I[idx]
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell
        cI=0; cA=0; longest=0
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2):
                for dz in(-2,-1,0,1,2):
                    for p in gI.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(p,q)<=r:
                            cI+=1
                            if wl_of[p]>longest: longest=wl_of[p]
                    for p in gA.get((gx+dx,gy+dy,gz+dz),()):
                        if cheb(p,q)<=r: cA+=1
        if cI>maxI: maxI=cI; maxIq=q
        samples.append((cA+cI, longest, cI))
    return maxI, samples

if __name__=='__main__':
    Ls = [int(x) for x in sys.argv[1:]] or [6,7]
    out = {'lam':LAM,'d':D,'levels':{}}
    for L in Ls:
        A,I,wl = build_split(L)
        pts = sorted(set(A)|set(I))
        # rebuild ordered full chain for centre counting (use set of all pts)
        allpts = A + I
        rec = {'N':len(allpts),'nA':len(A),'nI':len(I)}
        wc=[]; ex=[]
        for r in range(1,11):
            wc.append(walk_centre_max(allpts,r))
        rec['walk_centre_max'] = wc
        for r in range(1,11):
            ex.append(exact_lattice_max(allpts,r))
        rec['exact_lattice_max'] = ex
        rec['C_lin_walk'] = round(max(wc[r-1]/r for r in range(1,11)),3)
        rec['C_d_walk']   = round(max(wc[r-1]/(r**D) for r in range(1,11)),3)
        rec['C_lin_exact']= round(max(ex[r-1]/r for r in range(1,11)),3)
        rec['C_d_exact']  = round(max(ex[r-1]/(r**D) for r in range(1,11)),3)
        rec['ratio_c3r_over_cr_exact'] = [round(ex[3*k-1]/ex[k-1],3) for k in (1,2,3)]  # r=1->3,2->6,3->9
        # refill / route-2 at a mid radius r=6
        refills={}
        corr={}
        for r in (2,4,6,8,10):
            maxI, samples = refill_test(A,I,wl,r)
            refills[r]=maxI
            # correlation between crowding and longest-word-in-ball
            n=len(samples)
            mc=sum(s[0] for s in samples)/n; mw=sum(s[1] for s in samples)/n
            cov=sum((s[0]-mc)*(s[1]-mw) for s in samples)/n
            vc=sum((s[0]-mc)**2 for s in samples)/n; vw=sum((s[1]-mw)**2 for s in samples)/n
            rho = cov/math.sqrt(vc*vw) if vc>0 and vw>0 else 0.0
            # top-crowd deciles: avg longest word & avg interiors in the most crowded 10%
            ss=sorted(samples); k=max(1,n//10)
            top=ss[-k:]; bot=ss[:k]
            corr[r]={'pearson_crowd_vs_longestword':round(rho,3),
                     'top10pct_crowd_avg_longestword':round(sum(s[1] for s in top)/len(top),2),
                     'bot10pct_crowd_avg_longestword':round(sum(s[1] for s in bot)/len(bot),2),
                     'top10pct_crowd_avg_interiors':round(sum(s[2] for s in top)/len(top),2),
                     'bot10pct_crowd_avg_interiors':round(sum(s[2] for s in bot)/len(bot),2)}
        rec['refill_maxI_by_r']=refills
        rec['E_lin']=round(max(refills[r]/r for r in refills),3)
        rec['route2_crowd_vs_wordlen']=corr
        out['levels'][L]=rec
        import json
        print(json.dumps({L:rec}), flush=True)
    import json
    json.dump(out, open('design/lemma/ahlfors/ahlfors_ck-results.json','w'), indent=1)
    print("WROTE design/lemma/ahlfors/ahlfors_ck-results.json", flush=True)
