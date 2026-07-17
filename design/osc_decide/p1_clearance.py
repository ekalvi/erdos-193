"""
P1 lean near-collinear + depth-scaling probe on the REALIZED 124-menu walk.
Tracks, per apex k, the minimum normalized cross |D1 x D2|/(|D1||D2|) over all
earlier points, using cube-face bucketing. Records:
  - global min normalized cross (sine) and the exact integer |cross|^2 achieved
  - distribution of the exact integer |cross|^2 among the closest pairs
  - min sine bucketed by apex coordinate SCALE (log3 |coord|_inf) -> depth trend
No huge histogram (that is the slow part). Exact integer cross arithmetic.

Usage: pypy3 p1_clearance.py <stepfile> [stride]
"""
import sys, ast, math
from itertools import product
from collections import defaultdict

MENU = [v for v in product((-2,-1,0,1,2), repeat=3) if v != (0,0,0)]
E2 = 0.02
INV = 1.0 / E2

def build_points(path):
    w = ast.literal_eval(open(path).read())
    pts = [(0,0,0)]; x=y=z=0
    for s in w:
        vx,vy,vz = MENU[s]; x+=vx; y+=vy; z+=vz; pts.append((x,y,z))
    return pts

def cellkey(dx,dy,dz):
    ax=dx if dx>=0 else -dx; ay=dy if dy>=0 else -dy; az=dz if dz>=0 else -dz
    if ax>=ay and ax>=az: m=ax; face=0 if dx>=0 else 1; u=dy/m; v=dz/m
    elif ay>=az: m=ay; face=2 if dy>=0 else 3; u=dx/m; v=dz/m
    else: m=az; face=4 if dz>=0 else 5; u=dx/m; v=dy/m
    cu=int((u+1.0)*INV); cv=int((v+1.0)*INV)
    return face,cu,cv

def run(path, stride):
    pts = build_points(path); n=len(pts)
    px=[p[0] for p in pts]; py=[p[1] for p in pts]; pz=[p[2] for p in pts]
    best_num=1; best_den=0; best_info=None
    cross2_at_min = defaultdict(int)     # exact |cross|^2 among per-apex closest
    scale_min = {}                       # log3(|apex|_inf) -> (num,den) min sine^2
    for k in range(1,n,stride):
        xk=px[k]; yk=py[k]; zk=pz[k]
        buckets={}; bget=buckets.get
        apex_best_num=1; apex_best_den=0; apex_c2=None
        for i in range(k):
            dx=px[i]-xk; dy=py[i]-yk; dz=pz[i]-zk
            n2=dx*dx+dy*dy+dz*dz
            face,cu,cv=cellkey(dx,dy,dz)
            for ccu in (cu-1,cu,cu+1):
                for ccv in (cv-1,cv,cv+1):
                    lst=bget((face,ccu,ccv))
                    if lst is None: continue
                    for (ex,ey,ez,en2) in lst:
                        cx=dy*ez-dz*ey; cy=dz*ex-dx*ez; cz=dx*ey-dy*ex
                        cr2=cx*cx+cy*cy+cz*cz; den=n2*en2
                        if apex_best_den==0 or cr2*apex_best_den < apex_best_num*den:
                            apex_best_num=cr2; apex_best_den=den; apex_c2=cr2
                        if best_den==0 or cr2*best_den < best_num*den:
                            best_num=cr2; best_den=den; best_info=(i,k,en2,n2,cr2)
            key=(face,cu,cv); lst=bget(key)
            if lst is None: buckets[key]=[(dx,dy,dz,n2)]
            else: lst.append((dx,dy,dz,n2))
        if apex_best_den:
            cross2_at_min[apex_c2]+=1
            mag=max(abs(xk),abs(yk),abs(zk))
            sc=int(math.log(mag,3)) if mag>0 else 0
            prev=scale_min.get(sc)
            if prev is None or apex_best_num*prev[1] < prev[0]*apex_best_den:
                scale_min[sc]=(apex_best_num,apex_best_den)
    minsine=math.sqrt(best_num/best_den) if best_den else float('nan')
    print(f"FILE {path}  n={n}  stride={stride}")
    print(f"  GLOBAL min normalized cross (sine) = {minsine:.6e}")
    if best_info:
        i,k,en2,n2,cr2=best_info
        print(f"  achieved apex k={k} pt={pts[k]} i={i} pt={pts[i]} EXACT |cross|^2={cr2}  |Di|={math.sqrt(en2):.1f} |Dk|={math.sqrt(n2):.1f}")
    print("  exact |cross|^2 of each apex's CLOSEST pair (integer-floor distribution), top:")
    for c2 in sorted(cross2_at_min)[:8]:
        print(f"     |cross|^2={c2}: {cross2_at_min[c2]} apexes")
    print("  min sine by apex coordinate SCALE  (log3 |coord|_inf):")
    for sc in sorted(scale_min):
        num,den=scale_min[sc]
        s=math.sqrt(num/den)
        print(f"     scale 3^{sc} (~{3**sc}): min sine={s:.3e}  (|cross|^2={num})")
    sys.stdout.flush()

if __name__=="__main__":
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 1)
