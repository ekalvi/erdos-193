"""
Refutation hunt for Erdos #193 Move-2: find the closest-to-collinear triple in
the REAL construction walk. For each apex k (latest point), among direction
vectors to all earlier points, find the near-parallel pairs and the global
minimum normalized cross product  |D1 x D2| / (|D1| |D2|)  (= sine of the angle
at the apex).  Also count pairs below sine thresholds.  Exact integer arithmetic
for the cross product; cube-face spherical bucketing to avoid an O(n^3) all-pairs
scan (captures every pair with angle < ~cell width).

Usage: pypy3 near_collinear_hunt.py <stepfile> [apex_stride]
"""
import sys, ast, math
from itertools import product

MENU = [v for v in product((-2,-1,0,1,2), repeat=3) if v != (0,0,0)]

E2 = 0.02          # face-coordinate cell width (~0.02 rad capture radius)
INV = 1.0 / E2

def build_points(path):
    w = ast.literal_eval(open(path).read())
    pts = [(0,0,0)]
    x=y=z=0
    for s in w:
        vx,vy,vz = MENU[s]
        x+=vx; y+=vy; z+=vz
        pts.append((x,y,z))
    return pts

def cellkey(dx,dy,dz):
    ax=dx if dx>=0 else -dx
    ay=dy if dy>=0 else -dy
    az=dz if dz>=0 else -dz
    if ax>=ay and ax>=az:
        m=ax; face=0 if dx>=0 else 1; u=dy/m; v=dz/m
    elif ay>=az:
        m=ay; face=2 if dy>=0 else 3; u=dx/m; v=dz/m
    else:
        m=az; face=4 if dz>=0 else 5; u=dx/m; v=dy/m
    cu=int((u+1.0)*INV); cv=int((v+1.0)*INV)
    return face,cu,cv,u,v

def run(path, stride):
    pts = build_points(path)
    n = len(pts)
    px=[p[0] for p in pts]; py=[p[1] for p in pts]; pz=[p[2] for p in pts]
    best_num=1; best_den=0   # represents +inf (num/den); use den=0 sentinel
    best_info=None
    # thresholds for sine: count pairs below
    thr=[1e-2,1e-3,1e-4,1e-5]
    thr2=[t*t for t in thr]
    cnt=[0,0,0,0]
    apexes=range(1,n,stride)
    for k in apexes:
        xk=px[k]; yk=py[k]; zk=pz[k]
        buckets={}
        bget=buckets.get
        for i in range(k):
            dx=px[i]-xk; dy=py[i]-yk; dz=pz[i]-zk
            n2=dx*dx+dy*dy+dz*dz
            face,cu,cv,u,v=cellkey(dx,dy,dz)
            # scan 3x3 neighborhood in-face
            for ccu in (cu-1,cu,cu+1):
                base=(face,ccu)
                for ccv in (cv-1,cv,cv+1):
                    lst=bget((face,ccu,ccv))
                    if lst is None: continue
                    for (ex,ey,ez,en2) in lst:
                        cx=dy*ez-dz*ey
                        cy=dz*ex-dx*ez
                        cz=dx*ey-dy*ex
                        cr2=cx*cx+cy*cy+cz*cz
                        den=n2*en2
                        # compare to best: cr2/den < best_num/best_den
                        if best_den==0 or cr2*best_den < best_num*den:
                            best_num=cr2; best_den=den; best_info=(i,k,en2,n2,cr2)
                        # histogram (only bother if sine<1e-2)
                        if cr2*10000 < den:
                            cnt[0]+=1
                            if cr2*1000000 < den:
                                cnt[1]+=1
                                if cr2*100000000 < den:
                                    cnt[2]+=1
                                    if cr2*10000000000 < den:
                                        cnt[3]+=1
            key=(face,cu,cv)
            lst=bget(key)
            if lst is None:
                buckets[key]=[(dx,dy,dz,n2)]
            else:
                lst.append((dx,dy,dz,n2))
    minsine = math.sqrt(best_num/best_den) if best_den else float('nan')
    print(f"FILE {path}  n={n}  stride={stride}")
    print(f"  min normalized cross (sine) = {minsine:.6e}")
    if best_info:
        i,k,en2,n2,cr2=best_info
        print(f"  achieved: apex k={k} pt={pts[k]}  i={i} pt={pts[i]}  |cross|^2={cr2}")
        print(f"  |Di|={math.sqrt(en2):.3f} |Dk|={math.sqrt(n2):.3f}")
    print(f"  pairs with sine < 1e-2:{cnt[0]} 1e-3:{cnt[1]} 1e-4:{cnt[2]} 1e-5:{cnt[3]}")
    sys.stdout.flush()

if __name__=="__main__":
    path=sys.argv[1]
    stride=int(sys.argv[2]) if len(sys.argv)>2 else 1
    run(path,stride)
