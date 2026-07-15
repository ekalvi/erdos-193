"""
DECISIVE: does the RETURN count A(rho) SATURATE (bounded => product A*L linear)
or GROW with rho (=> A*L superlinear, combined decomposition breaks)?
Measure max_A(rho) over ALL walk-point centers, rho up to 40, levels L6,L7,L8.
Also report the actual max_c and c/rho to get the honest combined C, and check
whether A and the sojourn L co-occur in the SAME ball (product tightness).
"""
import sys, pickle, json
sys.path.insert(0,"/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from collections import defaultdict
MENU=candidate_step_vectors(2)
def interiors(start,wi):
    pts=[];x,y,z=start
    for si in wi[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def build(L):
    d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    A=d["anchors"];W=d["words"];walk=[]
    for i in range(len(A)-1):
        walk.append(A[i]);walk.extend(interiors(A[i],W[i]))
    walk.append(A[-1]);return walk
def cheb(a,b):return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
def grid_of(points,R):
    g=defaultdict(list)
    for idx,p in enumerate(points):g[(p[0]//R,p[1]//R,p[2]//R)].append(idx)
    return g
def arcs(sidx):
    if not sidx:return 0,[]
    a=1;L=[1]
    for x,y in zip(sidx,sidx[1:]):
        if y==x+1:L[-1]+=1
        else:a+=1;L.append(1)
    return a,L
def scan(ch,rho):
    N=len(ch);R=rho+1;g=grid_of(ch,R)
    maxc=0;maxc_arcs=None;maxc_L=None
    maxA=0;maxA_c=None;maxA_L=None
    maxprod=0
    for qi in range(N):
        q=ch[qi];cx,cy,cz=q[0]//R,q[1]//R,q[2]//R;hits=[]
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for idx in g.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,ch[idx])<=rho:hits.append(idx)
        hits.sort();A,Ls=arcs(hits);c=len(hits);mL=max(Ls) if Ls else 0
        if c>maxc:maxc=c;maxc_arcs=A;maxc_L=mL
        if A>maxA:maxA=A;maxA_c=c;maxA_L=mL
        p=A*mL
        if p>maxprod:maxprod=p
    return dict(rho=rho,max_c=maxc,at_maxc_A=maxc_arcs,at_maxc_sojourn=maxc_L,
                max_A=maxA,at_maxA_c=maxA_c,at_maxA_sojourn=maxA_L,
                max_AxL_product=maxprod,c_over_rho=round(maxc/rho,3))
if __name__=="__main__":
    levels=[int(x) for x in sys.argv[1:]] or [7,8]
    rhos=[4,5,8,10,15,20,30,40]
    out={}
    for L in levels:
        ch=build(L);print(f"L{L} N={len(ch)}",flush=True);rows=[]
        for rho in rhos:
            r=scan(ch,rho);rows.append(r)
            print(f" L{L} rho={rho:2d}: c={r['max_c']:3d} c/rho={r['c_over_rho']:.2f} | "
                  f"maxA={r['max_A']} (ball c={r['at_maxA_c']},soj={r['at_maxA_sojourn']}) | "
                  f"at densest ball: A={r['at_maxc_A']} sojourn={r['at_maxc_sojourn']} | maxAxL={r['max_AxL_product']}",flush=True)
        out[f"L{L}"]=rows
    json.dump(out,open("/Users/erik/homelab/math193/design/tight/adversary_returns.json","w"),indent=1)
    print("WROTE",flush=True)
