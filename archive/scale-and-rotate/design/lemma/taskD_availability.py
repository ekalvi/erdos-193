# Does bad-line/forbidden-site count predict availability (frac) better than c10?
# Correlate c10, b, f at stitch time against the recorded surviving-word fraction
# (clearance-L7v2.json, the v2 proof orbit) on matching segments.
import pickle, json, sys
from random import Random
sys.path.insert(0,"/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2); R=10; CELL=40; D=40
from math import gcd, ceil, floor
def word_interiors(start,w):
    pts=[];x,y,z=start
    for si in w[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def cell_of(p): return (p[0]//CELL,p[1]//CELL,p[2]//CELL)
def line_hits_box(a1,a2,Rr):
    lo,hi=-1e18,1e18
    for j in range(3):
        d=a2[j]-a1[j];p=a1[j]
        if d==0:
            if p<-Rr or p>Rr: return False
        else:
            t0=(-Rr-p)/d;t1=(Rr-p)/d
            if t0>t1:t0,t1=t1,t0
            lo=max(lo,t0);hi=min(hi,t1)
            if lo>hi:return False
    return lo<=hi
def igcd3(a,b,c):
    g=gcd(abs(a),abs(b));g=gcd(g,abs(c));return g or 1
def fsites(sh,Rr):
    marked=set()
    n=len(sh)
    for i in range(n):
        a1=sh[i]
        for k in range(i+1,n):
            a2=sh[k]
            dx,dy,dz=a2[0]-a1[0],a2[1]-a1[1],a2[2]-a1[2]
            g=igcd3(dx,dy,dz);ux,uy,uz=dx//g,dy//g,dz//g
            lo,hi=-10**9,10**9;ok=True
            for p0,u in ((a1[0],ux),(a1[1],uy),(a1[2],uz)):
                if u==0:
                    if p0<-Rr or p0>Rr: ok=False;break
                else:
                    s0=(-Rr-p0)/u;s1=(Rr-p0)/u
                    if s0>s1:s0,s1=s1,s0
                    lo=max(lo,ceil(s0));hi=min(hi,floor(s1))
            if not ok or lo>hi: continue
            for s in range(lo,hi+1):
                marked.add((a1[0]+s*ux,a1[1]+s*uy,a1[2]+s*uz))
    return len(marked-set(sh))
def corr(pairs):
    n=len(pairs);mx=sum(p[0] for p in pairs)/n;my=sum(p[1] for p in pairs)/n
    sx=(sum((p[0]-mx)**2 for p in pairs)/n)**.5;sy=(sum((p[1]-my)**2 for p in pairs)/n)**.5
    return sum((p[0]-mx)*(p[1]-my) for p in pairs)/n/(sx*sy) if sx>0 and sy>0 else 0.0
L=7
frac={r['i']:r['frac'] for r in json.load(open(f'/Users/erik/homelab/math193/clearance-L{L}v2.json')) if 'frac' in r}
d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
anchors=d['anchors'];order=d['order'];words=d['words']
grid={}
for p in anchors: grid.setdefault(cell_of(p),[]).append(p)
rng=Random(3); tg=set(rng.sample(range(len(order)),3000))
CF=[];BF=[];FF=[]
for pos,i in enumerate(order):
    if pos in tg and i in frac:
        A,B=anchors[i],anchors[i+1]
        cx,cy,cz=(A[0]+B[0])//2,(A[1]+B[1])//2,(A[2]+B[2])//2
        c0=cell_of((cx-D,cy-D,cz-D));c1=cell_of((cx+D,cy+D,cz+D));nb=[]
        for gx in range(c0[0],c1[0]+1):
          for gy in range(c0[1],c1[1]+1):
            for gz in range(c0[2],c1[2]+1):
                bb=grid.get((gx,gy,gz))
                if bb:
                    for p in bb:
                        if abs(p[0]-cx)<=D and abs(p[1]-cy)<=D and abs(p[2]-cz)<=D: nb.append(p)
        sh=[(p[0]-cx,p[1]-cy,p[2]-cz) for p in nb]
        c10=sum(1 for a in sh if abs(a[0])<=R and abs(a[1])<=R and abs(a[2])<=R)
        b=0;nn=len(sh)
        for x in range(nn):
            for y in range(x+1,nn):
                if line_hits_box(sh[x],sh[y],R): b+=1
        f=fsites(sh,R)
        fr=frac[i]
        CF.append((c10,fr));BF.append((b,fr));FF.append((f,fr))
    for p in word_interiors(anchors[i],words[i]):
        grid.setdefault(cell_of(p),[]).append(p)
print(json.dumps({"level":L,"n":len(CF),
    "corr_c10_frac":round(corr(CF),4),
    "corr_b_frac":round(corr(BF),4),
    "corr_f_frac":round(corr(FF),4)}))
