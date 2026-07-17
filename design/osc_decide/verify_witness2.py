"""
Proper reconstruction: for a g=2 anchor-collision, find the COMMON intermediate
state s1 with d1 in RevAvail(s1) and d2 in FwdAvail(s1), exhibit explicit
connectors for both legs, and confirm the anchor.  Then materialize the two
cylinders' *interior point clouds* (the actual lattice points the two gen-2
cylinders contribute, descending 2 connector levels) and check per-word internal
triple-freeness (Omega cross-product).
"""
import pickle, json
from collections import defaultdict
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
M=[[3,0,0],[0,0,-3],[0,3,-1]]
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])
def cross(o,a,b):
    ux,uy,uz=a[0]-o[0],a[1]-o[1],a[2]-o[2]
    vx,vy,vz=b[0]-o[0],b[1]-o[1],b[2]-o[2]
    return (uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx)

dom=pickle.load(open('connector_domains4.pkl','rb'))['domains']

# build fwd edges with which connector realizes them: state -> list of (digit, next, connectorC, position)
def interiors_with_next(C):
    out=[((0,0,0), C[0])]
    x=y=z=0
    for t in range(1,len(C)):
        s=MENU[C[t-1]]; x+=s[0]; y+=s[1]; z+=s[2]
        out.append(((x,y,z), C[t]))
    return out

# RevAvail: for each state s1, set of d1 leading into it (+ a witness base a, connector Ca, pos)
# FwdAvail: for each state s1, set of d2 leaving it (+ witness connector)
RevWit=defaultdict(dict)   # s1 -> d1 -> (a, C)
FwdWit=defaultdict(dict)   # s1 -> d2 -> C
for a in dom:
    for C in dom[a]:
        for (off,nxt) in interiors_with_next(C):
            if off not in RevWit[nxt]:
                RevWit[nxt][off]=(a,C)
for s1 in dom:
    for C in dom[s1]:
        for (off,nxt) in interiors_with_next(C):
            if off not in FwdWit[s1]:
                FwdWit[s1][off]=C

def reconstruct(d1,d2):
    # find common s1
    for s1 in dom:
        if d1 in RevWit[s1] and d2 in FwdWit[s1]:
            a,Ca=RevWit[s1][d1]; Cp=FwdWit[s1][d2]
            return s1,a,Ca,Cp
    return None

def materialize(a,Ca,d1,Cp,d2):
    """Materialize the gen-2 cylinder interior cloud relative to root origin 0.
    Level-1: root(type a) placed at 0; its M-image structure gives level-1 points.
    We build the actual point of the chosen gen-2 node PLUS the connector interiors
    that lie within this cylinder, to test triple-freeness of the local cloud."""
    # The chosen gen-1 node has anchor A1 = d1 (relative to M*root=0).
    # Its own connector Cp (for outgoing step s1) is laid at M*A1 = M*d1, producing
    # gen-2 points M*d1 + (partial sums of Cp).  The chosen gen-2 node = M*d1 + d2.
    base=mv(d1)
    pts=[base]  # the anchor M*d1
    x,y,z=base
    for e in Cp[:-1]:
        s=MENU[e]; x+=s[0];y+=s[1];z+=s[2]; pts.append((x,y,z))
    return pts

def triplefree(pts):
    n=len(pts)
    for i in range(n):
        for j in range(i+1,n):
            for k in range(j+1,n):
                if cross(pts[i],pts[j],pts[k])==(0,0,0):
                    return False,(pts[i],pts[j],pts[k])
    return True,None

def full_check(d1,d2,label):
    r=reconstruct(d1,d2)
    print(f"[{label}] d1={d1} d2={d2}",flush=True)
    if r is None:
        print("   NO common s1 -> NOT a legal 2-word (collision was spurious in search!)",flush=True)
        return None
    s1,a,Ca,Cp=r
    anchor=(mv(d1)[0]+d2[0], mv(d1)[1]+d2[1], mv(d1)[2]+d2[2])
    print(f"   common s1={s1} MENU[s1]={MENU[s1]}",flush=True)
    print(f"   leg1: base a={a} MENU[a]={MENU[a]} connector Ca={Ca} -> interior d1 leads to s1",flush=True)
    print(f"   leg2: connector Cp={Cp} from s1 -> interior/anchor d2",flush=True)
    print(f"   gen-2 anchor = {anchor}",flush=True)
    cloud=materialize(a,Ca,d1,Cp,d2)
    tf,tri=triplefree(cloud)
    print(f"   local gen-2 cloud ({len(cloud)} pts) triple-free? {tf}",flush=True)
    if not tf: print(f"      collinear triple: {tri}",flush=True)
    return anchor,tf

print("=== WITNESS V=(0,0,0): u=((-1,0,0),(3,0,0)) vs v=((0,0,0),(0,0,0)) ===",flush=True)
ru=full_check((-1,0,0),(3,0,0),"u")
rv=full_check((0,0,0),(0,0,0),"v")
if ru and rv:
    print(f"\n>>> anchors equal: {ru[0]==rv[0]} ; both legal GDS paths: {ru is not None and rv is not None}",flush=True)
    print(f">>> both individually triple-free clouds: u={ru[1]} v={rv[1]}",flush=True)
