"""
TASK C -- measure the DILATED-OLD fraction of c10 on the real L6 orbit.
Level-(k+1) points split into:
  - anchors  = M*(level-k walk points)   -> "dilated-old" points
  - interiors= new stitch interior points -> "new/refill" points
For a sample of level-6 points p, count neighbors within Chebyshev-10 and split
into anchor-neighbors vs interior-neighbors. dilated-old fraction = anchorNbr/total.
Compare to derived alpha from taskC_geometry.py.
Pure python; light (grid-bucketed neighbor search, sampled sources, node budget).
"""
import pickle, sys, json, random

MENU = None
def load_menu():
    sys.path.insert(0,'/Users/erik/homelab/math193')
    from search193 import candidate_step_vectors
    return candidate_step_vectors(2)

def word_interiors(start, word_idx, MENU):
    pts=[]; x,y,z=start
    for si in word_idx[:-1]:
        s=MENU[si]; x,y,z=x+s[0],y+s[1],z+s[2]; pts.append((x,y,z))
    return pts

def build_chain(pkl_path, MENU):
    d=pickle.load(open(pkl_path,'rb'))
    anchors=d['anchors']; words=d['words']
    chain=[anchors[0]]; is_anchor=[True]
    for i in range(len(words)):
        ints=word_interiors(anchors[i], words[i], MENU)
        for q in ints: chain.append(q); is_anchor.append(False)
        chain.append(anchors[i+1]); is_anchor.append(True)
    return chain, is_anchor

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def main():
    MENU=load_menu()
    path='/Users/erik/homelab/math193/gate2-l7-construction-L6.pkl'
    chain,is_anchor=build_chain(path,MENU)
    N=len(chain)
    nanch=sum(is_anchor)
    # grid bucket by cell size 11 (Chebyshev): neighbors within 10 lie in +-1 cells
    CELL=11; R=10
    grid={}
    for idx,p in enumerate(chain):
        key=(p[0]//CELL,p[1]//CELL,p[2]//CELL)
        grid.setdefault(key,[]).append(idx)
    rng=random.Random(193)
    # sample sources across the whole chain
    SAMPLE=1200
    src=rng.sample(range(N), min(SAMPLE,N))
    tot_c10=0; tot_anchNbr=0; tot_intNbr=0
    per=[]
    for i in src:
        p=chain[i]
        gx,gy,gz=p[0]//CELL,p[1]//CELL,p[2]//CELL
        c10=0; anum=0; inum=0
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if j==i: continue
                        if cheb(p,chain[j])<=R:
                            c10+=1
                            if is_anchor[j]: anum+=1
                            else: inum+=1
        tot_c10+=c10; tot_anchNbr+=anum; tot_intNbr+=inum
        per.append((c10,anum,inum))
    frac_anchor = tot_anchNbr/tot_c10 if tot_c10 else 0
    # also restrict to ANCHOR sources only (the recursion is really about how anchor
    # crowding at level k+1 relates to crowding at level k):
    a_c10=0; a_anch=0
    a_src=[i for i in src if is_anchor[i]]
    for i in a_src:
        p=chain[i]; gx,gy,gz=p[0]//CELL,p[1]//CELL,p[2]//CELL
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    for j in grid.get((gx+dx,gy+dy,gz+dz),()):
                        if j==i: continue
                        if cheb(p,chain[j])<=R:
                            a_c10+=1
                            if is_anchor[j]: a_anch+=1
    out={
     "level":"L6 (built from L5 parent)",
     "N_points":N, "N_anchors":nanch, "N_interiors":N-nanch,
     "anchor_fraction_global": nanch/N,
     "sample_sources":len(src),
     "mean_c10": tot_c10/len(src),
     "mean_anchor_neighbors": tot_anchNbr/len(src),
     "mean_interior_neighbors": tot_intNbr/len(src),
     "DILATED_OLD_FRACTION_of_c10 (measured)": frac_anchor,
     "among_anchor_sources": {
        "n_anchor_sources":len(a_src),
        "mean_c10": a_c10/len(a_src) if a_src else 0,
        "dilated_old_frac_within_anchor_crowd": a_anch/a_c10 if a_c10 else 0,
     },
    }
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
