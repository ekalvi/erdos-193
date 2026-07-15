"""
ROUTE 1 — refill sub-lemma measurement.

For each level L, decompose Walk_L = anchors (M.parent) DISJOINT-UNION stitch-interiors.
Measure:
  (1) B_local(rho) := max over ball-centres q of #{stitch interiors within Cheb-rho of q}.
      Centres: all interior points AND all anchors (union), for rho=1..10.
      Compare to target (5/9)*C*rho with C=6  ->  3.3333*rho.
  (2) The per-stitch footprint f_word(rho) := max over a SINGLE word and offset of
      #interiors of that word inside a Cheb-rho ball. LEVEL-INDEPENDENT (menu-fixed).
  (3) For the argmax refill ball at each rho: how many distinct STITCHES contribute,
      and the histogram of interiors-per-contributing-stitch (tests the "few per stitch").
  (4) Anchor-crowding co-factor: in the argmax refill ball, #anchors within Cheb-(rho+6).
"""
import pickle, sys
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)

def word_interiors(start, wi):
    pts = []; x,y,z = start
    for si in wi[:-1]:
        s = MENU[si]; x,y,z = x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
    return pts

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def load(L):
    d = pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    anchors = d["anchors"]; words = d["words"]
    # stitch interiors, tagged by owning stitch index i
    inter = []          # list of interior points
    inter_owner = []    # owning stitch index (== start-anchor index i)
    for i in range(len(anchors)-1):
        w = words[i]
        for p in word_interiors(anchors[i], w):
            inter.append(p); inter_owner.append(i)
    return anchors, words, inter, inter_owner

def max_ball(centres, points, rho, want_argmax=False):
    """max over q in centres of #{p in points : cheb(q,p)<=rho}. Grid-accelerated."""
    R = rho+1
    grid = defaultdict(list)
    for idx,p in enumerate(points):
        grid[(p[0]//R,p[1]//R,p[2]//R)].append(idx)
    best = 0; bestq = None; bestset = None
    for q in centres:
        cx,cy,cz = q[0]//R,q[1]//R,q[2]//R
        hits=[]
        for dx in(-1,0,1):
         for dy in(-1,0,1):
          for dz in(-1,0,1):
            for idx in grid.get((cx+dx,cy+dy,cz+dz),()):
                if cheb(q,points[idx])<=rho: hits.append(idx)
        if len(hits)>best:
            best=len(hits); bestq=q
            if want_argmax: bestset=hits
    return best, bestq, bestset

def per_stitch_footprint(words, anchors, rho):
    """LEVEL-INDEPENDENT finite check: max #interiors of a single word inside a
    Cheb-rho ball, over all words present and all integer ball positions.
    Since <=3 interiors, we just check every window: the max #interiors whose
    pairwise Cheb-diameter <= 2*rho (necessary) — but we test the true max over
    optimal centre by brute force over the interior points as candidate anchors."""
    best=0
    seen=set()
    for i in range(len(anchors)-1):
        w=words[i]
        ints=word_interiors(anchors[i],w)
        n=len(ints)
        if n==0: continue
        # translate to canonical (subtract first interior) to dedup word-shapes
        base=ints[0]
        shape=tuple((p[0]-base[0],p[1]-base[1],p[2]-base[2]) for p in ints)
        if shape in seen:
            pass  # still may want max footprint but shape determines it
        seen.add(shape)
        # max interiors inside a cheb-rho ball: try centre = each interior, also
        # any lattice centre in bounding box is dominated; brute over interiors as
        # centre gives >= true only if optimum centre is at an interior. To be safe
        # brute over all lattice centres in bbox of the interiors.
        xs=[p[0] for p in ints]; ys=[p[1] for p in ints]; zs=[p[2] for p in ints]
        cnt=0
        for cx in range(min(xs),max(xs)+1):
         for cy in range(min(ys),max(ys)+1):
          for cz in range(min(zs),max(zs)+1):
            c=sum(1 for p in ints if abs(p[0]-cx)<=rho and abs(p[1]-cy)<=rho and abs(p[2]-cz)<=rho)
            if c>cnt: cnt=c
        if cnt>best: best=cnt
    return best, len(seen)

if __name__=="__main__":
    levels = [int(x) for x in sys.argv[1:]] or [6,7]
    C=6.0
    for L in levels:
        anchors,words,inter,owner = load(L)
        print(f"\n=== L{L}: {len(anchors)} anchors, {len(inter)} stitch interiors ===",flush=True)
        setinter=set(inter); setanch=set(anchors)
        assert len(setinter & setanch)==0, "interiors overlap anchors!"
        centres = list(set(inter) | set(anchors))
        # sample centres for L8 to stay light
        if L>=8:
            centres = inter + anchors[:len(anchors)//1]  # keep all; grid makes it ok-ish
        print("rho  B_local(int)  target(3.333r)  margin   f_word  ncontrib  int/stitch-hist  anch_in(r+6)")
        for rho in range(1,11):
            B,bq,bset = max_ball(inter, inter, rho, want_argmax=True)
            # also allow anchor centres
            Ba,bqa,bseta = max_ball(anchors, inter, rho, want_argmax=True)
            if Ba>B: B,bq,bset = Ba,bqa,bseta
            tgt = (5/9)*C*rho
            fw,nshapes = per_stitch_footprint(words,anchors,rho)
            # decompose argmax ball
            owners_here = defaultdict(int)
            for idx in bset: owners_here[owner[idx]]+=1
            ncontrib=len(owners_here)
            hist=defaultdict(int)
            for v in owners_here.values(): hist[v]+=1
            hist=dict(sorted(hist.items()))
            # anchor cofactor: #anchors within cheb (rho+6) of bq
            anch_near=sum(1 for a in anchors if cheb(a,bq)<=rho+6)
            print(f"{rho:3d}  {B:11d}  {tgt:12.2f}  {tgt-B:6.1f}  {fw:5d}  {ncontrib:7d}  {str(hist):18s}  {anch_near}",flush=True)
