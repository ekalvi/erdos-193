"""
Phase 2: CONTACT-INTERFACE dimension + shared-sub-cylinder (overlap) test.

For each generation g, take every pair of DISTINCT gen-g cylinders whose clouds achieve
the pinned min Q-clearance = 1 (difference vector (1,0,0)).  For each such pair (u,v):

  (a) INTERFACE SIZE  I_r(u,v) = #{ (p in cloud_u, q in cloud_v) : Cheb(p,q) <= r }.
      Touch  => I_r bounded / O(1) (0-dim contact).
      Overlap => I_r grows like the sub-cylinder size (a full shared sub-cylinder).

  (b) SHARED-SUB-CYLINDER test.  The two clouds are related near contact by the integer
      translation w = (1,0,0).  Overlap in positive H^d-measure requires a common open
      sub-attractor, i.e. cloud_u + w shares a LARGE (sub-cylinder-sized) subset with
      cloud_v (a deeper Delta=0 identity).  We compute
          ov(w) = |(cloud_u + w) ∩ cloud_v|   for w over the small offset ball,
      and report max over w and per contact.  A whole shared sub-cylinder shows up as
      ov growing with cylinder size; a boundary touch keeps ov = O(1).

We report the SCALING of the interface with cylinder size across g -> the interface
(contact) dimension.  Interface bounded while cylinders grow ~3^g  =>  contact dim 0
=> H^d-measure-zero touch.
"""
import importlib.util, sys, math
from collections import defaultdict

MW_PATH = '/Users/erik/homelab/math193/design/lemma/route1/mw_osc.py'
spec = importlib.util.spec_from_file_location('mw', MW_PATH)
mw = importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

def Q(v):
    x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z
def Qd(a,b): return Q((a[0]-b[0],a[1]-b[1],a[2]-b[2]))
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

def run(topL, depth):
    print("="*80); print(f"CONTACT INTERFACE  topL={topL} depth={depth}"); print("="*80)
    chain, anc = mw.build_ancestry(topL, depth)
    N=len(chain); pset=set(chain)
    cloudpts = {}  # (g, ancid) -> list of points
    for g in range(1, depth+1):
        groups=defaultdict(list)
        for j,a in enumerate(anc[g]):
            groups[a].append(chain[j])
        cloudpts[g]=groups

    OFFB=[(dx,dy,dz) for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)]  # Cheb-1 ball
    for g in range(1, depth+1):
        anc_g=anc[g]; groups=cloudpts[g]
        cell=max(2, min(3**g,64))
        grid=defaultdict(list)
        for j,p in enumerate(chain):
            grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(j)
        # find pinned contacts (Q-clearance == 1)
        contacts=set()
        for j in range(N):
            p=chain[j]; gj=anc_g[j]
            gx,gy,gz=p[0]//cell,p[1]//cell,p[2]//cell
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    for dz in(-1,0,1):
                        for k in grid.get((gx+dx,gy+dy,gz+dz),()):
                            if k==j: continue
                            if anc_g[k]==gj: continue
                            if Qd(p,chain[k])==1:
                                pair=(min(gj,anc_g[k]),max(gj,anc_g[k]))
                                contacts.add(pair)
        # cylinder sizes
        sizes=[len(v) for v in groups.values()]; sizes.sort()
        medsize=sizes[len(sizes)//2]; maxsize=sizes[-1]
        # analyze each pinned contact pair
        Irs=defaultdict(list); ovs=[]; nshared=[]
        for (a,b) in contacts:
            ca=groups[a]; cb=groups[b]; sb=set(cb)
            # interface size I_r
            for r in (1,2,3,4):
                cnt=0
                for p in ca:
                    for q in cb:
                        if cheb(p,q)<=r: cnt+=1
                Irs[r].append(cnt)
            # shared-sub-cylinder / overlap test: max over Cheb-1 translations w of
            #  |(ca + w) ∩ cb|  (excluding trivial w=0 which is 0 by self-avoidance)
            best_ov=0; best_w=None
            for w in OFFB:
                ov=sum(1 for p in ca if (p[0]+w[0],p[1]+w[1],p[2]+w[2]) in sb)
                if ov>best_ov: best_ov=ov; best_w=w
            ovs.append(best_ov); nshared.append((best_ov,best_w,len(ca),len(cb)))
        def stats(lst): return (min(lst),sum(lst)/len(lst),max(lst)) if lst else (0,0,0)
        print(f"\n g={g}: #pinned-contact-pairs={len(contacts)}  cyl size med={medsize} max={maxsize} (3^g={3**g})")
        for r in (1,2,3,4):
            mn,av,mx=stats(Irs[r])
            print(f"    interface I_{r}: min={mn} avg={av:.2f} max={mx}   (max/cyl_med={mx/max(1,medsize):.3f})")
        mn,av,mx=stats(ovs)
        print(f"    SHARED-translate overlap max|(cloud_u+w)∩cloud_v|: min={mn} avg={av:.2f} MAX={mx}"
              f"   (MAX/cyl_med={mx/max(1,medsize):.3f})")
        # show the worst (largest overlap) contact
        nshared.sort(reverse=True)
        print(f"    worst-overlap contacts (ov,w,|u|,|v|): {nshared[:3]}")

if __name__=='__main__':
    topL=int(sys.argv[1]) if len(sys.argv)>1 else 8
    depth=int(sys.argv[2]) if len(sys.argv)>2 else 4
    run(topL, depth)
