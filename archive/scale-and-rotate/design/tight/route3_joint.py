"""
Joint (local-time m, index-span, far-return) structure over ALL balls.
Tests the emerging POTENTIAL-route theorem:
   DENSE  ==>  INDEX-LOCAL  ==>  diameter-ballistic sojourn bounds it.
   far recurrent returns (large span) contribute only SPARSE points.

For every center q (=walk point) and rho, with idxs = ball occupancy:
  m    = local time
  span = idxs[-1]-idxs[0]           (realized recurrence window at THIS ball)
  We also split occupancy by index-clustering at gap-threshold G=2*(2rho+1):
    "clumps" = maximal groups of idxs with consecutive gaps <= G.
  far_extra = m - (size of largest clump)      (points from index-distant returns)
  main_span = index span of the largest clump.

Report per (level,rho):
  max_m, and AT that center: span, n_clumps, main_clump_size, far_extra
  MAX_far_extra over ALL centers (how many points can distant returns ever add?)
  MAX_m among centers with span>4rho (can a large-span ball be dense?)
  MAX_m among centers with span<=4rho (index-local dense balls)
"""
import sys, pickle, json
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors

def build_chain(pkl):
    st = pickle.load(open(pkl,'rb'))
    anchors, words, pw = st['anchors'], st['words'], st['parent_word']
    chain=[anchors[0]]
    for i in range(len(pw)):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i+1])
    return chain

def cheb(a,b):
    return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def clumps(idxs, G):
    cl=[]; cur=[idxs[0]]
    for a in idxs[1:]:
        if a-cur[-1]<=G: cur.append(a)
        else: cl.append(cur); cur=[a]
    cl.append(cur); return cl

def analyze(level, pkl):
    chain=build_chain(pkl); N=len(chain)
    res={"level":level,"N":N,"per_rho":{}}
    for rho in range(1,11):
        cell=rho; G=2*(2*rho+1)
        grid=defaultdict(list)
        for i,p in enumerate(chain):
            grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
        max_m=0; at=None
        max_far=0; at_far=None
        max_m_largespan=0; max_m_localspan=0
        max_span_among_dense=0   # max span among centers with m>=0.7*(will fill after)
        # first pass need max_m; do two-pass lite: store per-center (m,span,far)
        recs=[]
        for qi in range(N):
            q=chain[qi]
            cx,cy,cz=q[0]//cell,q[1]//cell,q[2]//cell
            idxs=[]
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for j in grid.get((cx+dx,cy+dy,cz+dz),()):
                            if cheb(chain[j],q)<=rho: idxs.append(j)
            idxs.sort()
            m=len(idxs); span=idxs[-1]-idxs[0]
            cl=clumps(idxs,G)
            main=max(len(c) for c in cl)
            far=m-main
            if m>max_m: max_m=m; at=(m,span,len(cl),main,far,qi)
            if far>max_far: max_far=far; at_far=(m,span,far,len(cl),qi)
            if span>4*rho:
                if m>max_m_largespan: max_m_largespan=m
            else:
                if m>max_m_localspan: max_m_localspan=m
            recs.append((m,span))
        thr=0.7*max_m
        max_span_among_dense=max((s for (mm,s) in recs if mm>=thr), default=0)
        res["per_rho"][rho]={
            "max_m":max_m,
            "densest_center":{"m":at[0],"span":at[1],"n_clumps":at[2],"main_clump":at[3],"far_extra":at[4]},
            "MAX_far_extra_over_all":max_far,
            "at_max_far":{"m":at_far[0],"span":at_far[1],"far":at_far[2],"n_clumps":at_far[3]} if at_far else None,
            "max_m_with_span_gt_4rho":max_m_largespan,
            "max_m_with_span_le_4rho":max_m_localspan,
            "max_span_among_top30pct_dense":max_span_among_dense,
        }
    return res

def main():
    files=[(6,'gate2-l7-construction-L6.pkl'),(7,'gate2-l7-construction-L7.pkl'),(8,'gate2-l7-construction-L8.pkl')]
    out={"levels":{}}
    for L,pkl in files:
        print("L%d..."%L,flush=True)
        r=analyze(L,'/Users/erik/homelab/math193/'+pkl); out["levels"][L]=r
        for rho in range(1,11):
            d=r["per_rho"][rho]
            print("  rho=%2d max_m=%3d far_extra(max over all balls)=%2d | max_m[span>4rho]=%3d  max_m[span<=4rho]=%3d  span@dense<=%d"%(
                rho,d["max_m"],d["MAX_far_extra_over_all"],d["max_m_with_span_gt_4rho"],d["max_m_with_span_le_4rho"],d["max_span_among_top30pct_dense"]))
    json.dump(out,open("/Users/erik/homelab/math193/design/tight/route3_joint.json","w"),indent=2,default=int)
    print("wrote route3_joint.json")

if __name__=="__main__": main()
