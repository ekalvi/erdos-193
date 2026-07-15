"""
BOUND-2 follow-up: (A) exact FULL-walk crowding c_L(4.44) (the real target), and
(B) the arc/returns anatomy that decides circularity.

Non-circular linear-per-arc bound:  along ONE monotone arc, consecutive anchors are
Cheb->=3 apart, so a window of Cheb-diameter D=2(r+4) holds <= floor(D/3)+1 anchors
per arc.  Total anchors-in-window <= (#arcs) * (floor(2(r+4)/3)+1).  #arcs = returns+1
is the ONLY circular ingredient (needs parent geometry).  We measure returns directly
and test whether a single monotone run already saturates the per-arc packing.
"""
import json, os, pickle, sys, time
os.chdir("/Users/erik/homelab/math193"); sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3
M = [list(r) for r in M_BAL3]
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def load(L):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl"%L,"rb"))
    anchors, words = d["anchors"], d["words"]
    chain=[anchors[0]]
    for i in range(len(anchors)-1):
        chain.extend(gate_run.word_interiors(anchors[i], words[i])); chain.append(anchors[i+1])
    return anchors, chain

def build_hash(P,c):
    H={}
    for p in P: H.setdefault((p[0]//c,p[1]//c,p[2]//c),[]).append(p)
    return H

def exact_sup(points, rho, want_arg=True):
    if not points: return 0, None
    W=2*int(rho)
    if 2*rho-W>=1: W+=1
    cell=int(W)+1; H=build_hash(points,cell); best=0; arg=None
    for a in points:
        a0,a1,a2=a; kx,ky,kz=a0//cell,a1//cell,a2//cell; slab=[]
        for dx in(0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    b=H.get((kx+dx,ky+dy,kz+dz))
                    if b:
                        for p in b:
                            if a0<=p[0]<=a0+W and abs(p[1]-a1)<=W and abs(p[2]-a2)<=W: slab.append(p)
        if len(slab)<=best: continue
        for cy in sorted(set(p[1] for p in slab)):
            ysel=[p for p in slab if cy<=p[1]<=cy+W]
            if len(ysel)<=best: continue
            zs=sorted(p[2] for p in ysel); lo=0
            for hi in range(len(zs)):
                while zs[hi]-zs[lo]>W: lo+=1
                if hi-lo+1>best: best=hi-lo+1; arg=(a0,cy,zs[lo])
    return best, arg

def main():
    import math
    t0=time.time(); out={}
    load_r=40.0/9.0
    for L in (6,7,8):
        anchors, chain = load(L)
        anch_index={p:i for i,p in enumerate(anchors)}
        res={}
        for r in (load_r, 4.0, 10.0):
            c, arg = exact_sup(chain, r)
            # the exact_sup arg is a box corner; use box centre for window analysis
            W=2*int(r);
            if 2*r-W>=1: W+=1
            q=(arg[0]+W/2.0, arg[1]+W/2.0, arg[2]+W/2.0)
            # anchors within Cheb-(r+4) of q
            rwin=r+4
            win=[anch_index[p] for p in anchors if cheb(p,q)<=rwin]
            win.sort()
            arcs=1 if win else 0
            for u,v in zip(win,win[1:]):
                if v!=u+1: arcs+=1
            # per-arc max run length
            runs=[]; cur=1
            for u,v in zip(win,win[1:]):
                if v==u+1: cur+=1
                else: runs.append(cur); cur=1
            if win: runs.append(cur)
            res["r=%.4f"%r]={
                "true_c_full": c,
                "nanch_in_window_r+4": len(win),
                "arcs_returns+1": arcs,
                "max_arc_len": max(runs) if runs else 0,
                "per_arc_packing_floor(2(r+4)/3)+1": math.floor(2*rin/3)+1 if (rin:=r+4) else 0,
            }
        out["L%d"%L]=res
        print("L%d"%L, json.dumps(res), "t=%.1f"%(time.time()-t0), flush=True)
    json.dump(out, open("design/lemma/automaton/bound2_direct_results.json","w"), indent=2)

if __name__=="__main__": main()
