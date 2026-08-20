"""
Refine the refill sub-lemma  b_k(rho) <= E*rho  (E = menu constant).
(1) extend rho to 20 to confirm the slope-3 envelope is SET AT SMALL rho and
    only gets looser (E stays <= 3) for large rho;
(2) OFF-LATTICE sup check: recentre the densest stitch balls on the 8 half-integer
    corner shifts + the stitch centroid to make sure sup_{q in R^3} isn't >> the
    walk-point max;
(3) mechanism: distinct WORDS (gaps) and path ARCS meeting the densest balls, to
    see whether b <= 3*rho is "3 interiors per word x (words ~ rho)".
"""
import pickle, sys, os
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from search193 import candidate_step_vectors
MENU = candidate_step_vectors(2)

def build(pkl):
    d=pickle.load(open(pkl,"rb"))
    anchors=[tuple(a) for a in d["anchors"]]; words=d["words"]
    chain=[]; is_anc=[]; word_id=[]   # word_id[j]=gap index for stitch pts, -1 for anchors
    chain.append(anchors[0]); is_anc.append(1); word_id.append(-1)
    for i in range(len(anchors)-1):
        A=anchors[i]; wi=words[i]; x,y,z=A
        for si in wi[:-1]:
            s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]
            chain.append((x,y,z)); is_anc.append(0); word_id.append(i)
        chain.append(anchors[i+1]); is_anc.append(1); word_id.append(-1)
    return chain,is_anc,word_id

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

RHOS=[1,2,3,4,5,6,8,10,12,14,16,20]

def run(pkl,label):
    chain,is_anc,word_id=build(pkl); n=len(chain)
    CELL=21
    grid=defaultdict(list)
    for idx,p in enumerate(chain):
        grid[(p[0]//CELL,p[1]//CELL,p[2]//CELL)].append(idx)
    def neigh(qx,qy,qz):
        cx,cy,cz=int(qx)//CELL,int(qy)//CELL,int(qz)//CELL; out=[]
        for dx in(-2,-1,0,1,2):
         for dy in(-2,-1,0,1,2):
          for dz in(-2,-1,0,1,2):
            out.extend(grid.get((cx+dx,cy+dy,cz+dz),()))
        return out
    print(f"\n=== {label}: n={n} ===")
    print(f"{'rho':>4} {'b':>4} {'b/rho':>6} {'words':>6} {'arcs':>5} {'3*words':>8}")
    best_by_rho={}
    for rho in RHOS:
        bmax=0; bestq=None; bestmembers=None
        # center at STITCH points only (refill sup near stitch clusters)
        for qi in range(n):
            if is_anc[qi]: continue
            q=chain[qi]
            b=0; members=[]
            for j in neigh(q[0],q[1],q[2]):
                if not is_anc[j] and cheb(q,chain[j])<=rho:
                    b+=1; members.append(j)
            if b>bmax: bmax=b; bestq=qi; bestmembers=members
        # distinct words + arcs in the best ball
        wl=set(word_id[j] for j in bestmembers)
        idxs=sorted(bestmembers)
        arcs=1
        for a,bb in zip(idxs,idxs[1:]):
            if bb!=a+1: arcs+=1
        best_by_rho[rho]=(chain[bestq],bestmembers)
        print(f"{rho:>4} {bmax:>4} {bmax/rho:>6.2f} {len(wl):>6} {arcs:>5} {3*len(wl):>8}")
    # OFF-LATTICE sup check on the densest small-rho balls (rho=1,2,3,4)
    print(f"  off-lattice sup check (half-integer + centroid recentring):")
    for rho in (1,2,3,4):
        q0,members=best_by_rho[rho]
        base=bmax_offlat=0
        # gather stitch pts near q0 within rho+1
        near=[chain[j] for j in neigh(q0[0],q0[1],q0[2]) if not is_anc[j] and cheb(q0,chain[j])<=rho+1]
        # try centroid and all half-integer shifts of q0
        cands=[]
        cx=sum(p[0] for p in near)/len(near); cy=sum(p[1] for p in near)/len(near); cz=sum(p[2] for p in near)/len(near)
        cands.append((cx,cy,cz))
        for ex in (-0.5,0,0.5):
         for ey in (-0.5,0,0.5):
          for ez in (-0.5,0,0.5):
            cands.append((q0[0]+ex,q0[1]+ey,q0[2]+ez))
        best=0
        for (qx,qy,qz) in cands:
            c=sum(1 for p in near if max(abs(p[0]-qx),abs(p[1]-qy),abs(p[2]-qz))<=rho)
            if c>best: best=c
        print(f"    rho={rho}: walkpt-max={len([j for j in members])}  off-lattice-max={best}  (E*rho={3*rho})")

if __name__=="__main__":
    for L,pkl in (("L7","gate2-l7-construction-L7.pkl"),):
        run(pkl,L)
