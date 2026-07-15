"""
ADVERSARIAL ATTACK on the combined tight-linear law:
   c_k(q,rho) <= C*rho + 1,  via  c = A(rho) * L(rho)  (returns x sojourn).

(a) DIAMETER-ballistic S(n)=min_i cheb-diam(W[i..i+n]);  ratio S(n)/n level-uniform?
    Also ENDPOINT-ballistic min|W(i+n)-W(i)|inf/n (should -> 0, confirming diameter is the right one).
    Push n high, ALL levels L5..L8, find worst-case (min-ratio) arc.
(b) RETURN count A(rho): for the DENSEST ball at each rho, split the in-ball hits into
    maximal contiguous path-arcs; A = number of arcs. Track max A over ALL balls (adversarial).
    Does A creep with level?
(c) direct combined C = max_rho c(rho)/rho ; and product bound A_max * L vs actual c.
"""
import sys, pickle, json
sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from collections import defaultdict
MENU = candidate_step_vectors(2)

def interiors(start, wi):
    pts=[]; x,y,z=start
    for si in wi[:-1]:
        s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
    return pts

def build(L):
    d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    A=d["anchors"]; W=d["words"]
    walk=[]
    for i in range(len(A)-1):
        walk.append(A[i]); walk.extend(interiors(A[i],W[i]))
    walk.append(A[-1])
    return walk

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def diam_ballistic(chain, Nmax):
    N=len(chain); S=[10**9]*(Nmax+1)
    argn=[None]*(Nmax+1)
    for i in range(N):
        x0=x1=chain[i][0]; y0=y1=chain[i][1]; z0=z1=chain[i][2]
        jmax=min(i+Nmax, N-1)
        for n in range(1, jmax-i+1):
            p=chain[i+n]
            if p[0]<x0:x0=p[0]
            elif p[0]>x1:x1=p[0]
            if p[1]<y0:y0=p[1]
            elif p[1]>y1:y1=p[1]
            if p[2]<z0:z0=p[2]
            elif p[2]>z1:z1=p[2]
            dm=x1-x0
            t=y1-y0; dm=t if t>dm else dm
            t=z1-z0; dm=t if t>dm else dm
            if dm<S[n]:
                S[n]=dm; argn[n]=i
    return S, argn

def endpoint_ballistic_min(chain, Nmax, step=1):
    N=len(chain); G=[10**9]*(Nmax+1)
    for i in range(N):
        jmax=min(i+Nmax,N-1)
        for n in range(1,jmax-i+1):
            d=cheb(chain[i],chain[i+n])
            if d<G[n]: G[n]=d
    return G

def grid_of(points, R):
    g=defaultdict(list)
    for idx,p in enumerate(points):
        g[(p[0]//R,p[1]//R,p[2]//R)].append(idx)
    return g

def ball_hits(q, points, rho, grid, R):
    cx,cy,cz=q[0]//R,q[1]//R,q[2]//R; hits=[]
    for dx in(-1,0,1):
     for dy in(-1,0,1):
      for dz in(-1,0,1):
        for idx in grid.get((cx+dx,cy+dy,cz+dz),()):
            if cheb(q,points[idx])<=rho: hits.append(idx)
    return hits

def arcs_of(sorted_idx):
    """given sorted path-indices in a ball, count maximal contiguous runs (return count A)."""
    if not sorted_idx: return 0, []
    arcs=1; lengths=[1]
    for a,b in zip(sorted_idx, sorted_idx[1:]):
        if b==a+1:
            lengths[-1]+=1
        else:
            arcs+=1; lengths.append(1)
    return arcs, lengths

def analyze_returns(chain, rho, sample_stride=1):
    """For EVERY walk point as center q, compute c, A(#arcs), maxarc(sojourn). Return maxima."""
    N=len(chain); R=rho+1; grid=grid_of(chain,R)
    best_c=0; best_c_q=None
    max_A=0; max_A_q=None; max_A_c=None
    max_L=0
    # to bound cost, iterate all centers (walk points) but reuse grid
    for qi in range(0,N,sample_stride):
        q=chain[qi]
        hits=ball_hits(q,chain,rho,grid,R)
        hits.sort()
        A, lengths = arcs_of(hits)
        c=len(hits); mL=max(lengths) if lengths else 0
        if c>best_c: best_c=c; best_c_q=qi
        if A>max_A: max_A=A; max_A_q=qi; max_A_c=c
        if mL>max_L: max_L=mL
    return dict(max_c=best_c, max_c_qi=best_c_q, max_A=max_A, max_A_at_qi=max_A_q,
               max_A_ball_c=max_A_c, max_sojourn_arc=max_L)

if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [5,6,7,8]
    Nmax=int(__import__("os").environ.get("NMAX","150"))
    rho_list=[1,2,4,5,10]
    out={"Nmax":Nmax,"levels":{}}
    chains={}
    for L in levels:
        chains[L]=build(L)
        print(f"L{L} built N={len(chains[L])}",flush=True)
    # (a) ballistic
    for L in levels:
        ch=chains[L]
        S,argn=diam_ballistic(ch,min(Nmax,len(ch)-1))
        nn=[n for n in range(1,min(Nmax,len(ch)-1)+1)]
        ratios={n:S[n]/n for n in nn}
        cmin=min(ratios.values()); cmin_n=min(ratios,key=lambda n:ratios[n])
        # endpoint (cheaper: cap Nmax at 200)
        G=endpoint_ballistic_min(ch,min(200,len(ch)-1))
        eratios={n:G[n]/n for n in range(1,min(200,len(ch)-1)+1)}
        emin=min(eratios.values()); emin_n=min(eratios,key=lambda n:eratios[n])
        rec={"N":len(ch),
             "diam_c_min":round(cmin,4),"diam_c_min_at_n":cmin_n,
             "diam_ratio_tail":{n:round(ratios[n],4) for n in nn if n%10==0 or n<=5},
             "worst_arc_start_i":argn[cmin_n],
             "endpoint_min_ratio":round(emin,4),"endpoint_min_at_n":emin_n}
        out["levels"].setdefault(L,{})["ballistic"]=rec
        print(f"L{L} DIAM c_min={cmin:.4f}@n={cmin_n}  ENDPT min={emin:.4f}@n={emin_n}",flush=True)
    # (b)(c) returns + combined C
    for L in levels:
        ch=chains[L]
        rr={}
        for rho in rho_list:
            r=analyze_returns(ch,rho)
            r["c_over_rho"]=round(r["max_c"]/rho,3)
            rr[rho]=r
            print(f"L{L} rho={rho}: max_c={r['max_c']} (c/rho={r['c_over_rho']}) "
                  f"max_A={r['max_A']}(at ball c={r['max_A_ball_c']}) max_sojourn={r['max_sojourn_arc']}",flush=True)
        out["levels"].setdefault(L,{})["returns"]=rr
        out["levels"][L]["C_combined"]=max(rr[rho]["c_over_rho"] for rho in rho_list)
    json.dump(out, open("/Users/erik/homelab/math193/design/tight/adversary_combined.json","w"),indent=1)
    print("WROTE adversary_combined.json",flush=True)
