#!/usr/bin/env python3
"""Generate faithful SVG sprite paths for the trilemma scorecard.
Every curve is REAL geometry: Hilbert & Koch by their exact recursions,
the moment curve by sampling (t,t^2,t^3), our walk by PCA-projecting an
actual contiguous segment of the record construction (walk3d-data.json)."""
import json, math

VB_W, VB_H, PAD = 88.0, 52.0, 6.0

def normalize(pts, W=VB_W, H=VB_H, pad=PAD, flip=True):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys)
    dx=(maxx-minx) or 1.0; dy=(maxy-miny) or 1.0
    s=min((W-2*pad)/dx,(H-2*pad)/dy)
    ox=(W-s*dx)/2.0; oy=(H-s*dy)/2.0
    out=[]
    for x,y in pts:
        X=ox+s*(x-minx)
        Y=(H-(oy+s*(y-miny))) if flip else (oy+s*(y-miny))
        out.append((X,Y))
    return out

def path_d(pts, prec=1):
    p=pts[0]; d=f"M{p[0]:.{prec}f},{p[1]:.{prec}f}"
    for x,y in pts[1:]:
        d+=f" L{x:.{prec}f},{y:.{prec}f}"
    return d

# ---- PCA to 2D (top-2 principal axes; power iteration) ----
def pca2d(pts3):
    n=len(pts3)
    c=[sum(p[i] for p in pts3)/n for i in range(3)]
    C=[[0.0]*3 for _ in range(3)]
    for p in pts3:
        v=[p[i]-c[i] for i in range(3)]
        for a in range(3):
            for b in range(3):
                C[a][b]+=v[a]*v[b]
    def mv(M,v): return [sum(M[i][j]*v[j] for j in range(3)) for i in range(3)]
    def nrm(v):
        m=math.sqrt(sum(x*x for x in v)); return [x/m for x in v] if m>1e-12 else v
    def pit(M,excl=None,it=300,seed=(1.0,0.41,-0.27)):
        v=list(seed)
        for _ in range(it):
            v=mv(M,v)
            if excl:
                d=sum(v[i]*excl[i] for i in range(3)); v=[v[i]-d*excl[i] for i in range(3)]
            v=nrm(v)
        return v
    e1=pit(C); e2=pit(C,excl=e1)
    out=[]
    for p in pts3:
        v=[p[i]-c[i] for i in range(3)]
        out.append((sum(v[i]*e1[i] for i in range(3)), sum(v[i]*e2[i] for i in range(3))))
    return out

# ---- Hilbert space-filling curve, order k ----
def hilbert(order):
    n=1<<order
    def d2xy(d):
        rx=ry=0; x=y=0; t=d; s=1
        while s<n:
            rx=1&(t>>1); ry=1&(t^rx)
            if ry==0:
                if rx==1: x=s-1-x; y=s-1-y
                x,y=y,x
            x+=s*rx; y+=s*ry
            t>>=2; s<<=1
        return (x,y)
    return [d2xy(i) for i in range(n*n)]

# ---- Koch curve, given recursion depth ----
def koch(level):
    pts=[(0.0,0.0),(1.0,0.0)]
    ang=-math.pi/3.0; ca,sa=math.cos(ang),math.sin(ang)
    for _ in range(level):
        new=[]
        for i in range(len(pts)-1):
            (x1,y1),(x2,y2)=pts[i],pts[i+1]
            dx=(x2-x1)/3.0; dy=(y2-y1)/3.0
            ax,ay=x1+dx,y1+dy; bx,by=x1+2*dx,y1+2*dy
            ux,uy=bx-ax,by-ay
            px=ax+ux*ca-uy*sa; py=ay+ux*sa+uy*ca
            new+=[(x1,y1),(ax,ay),(px,py),(bx,by)]
        new.append(pts[-1]); pts=new
    return pts

# ---- moment curve: the strictly-convex arc (t, t^2) — the textbook
# smooth curve with no three points collinear; drawn as a clean parabola ----
def moment(N=90):
    p=[]
    for i in range(N+1):
        t=-1.05+2.10*i/N
        p.append((t, t*t))
    return p

# ---- our walk: real contiguous segment, projected ----
def walk_segment(level, start, count):
    lv=json.load(open('viz/walk3d-data.json'))['levels']
    seg=[tuple(map(float,q)) for q in lv[level]['points'][start:start+count]]
    return pca2d(seg)

sprites={
    'straight': [(0.0,0.0),(1.0,1.0)],
    'moment'  : moment(),
    'koch'    : koch(3),
    'hilbert' : hilbert(3),
    'walk'    : walk_segment(5, 2000, 350),
}

paths={k:path_d(normalize(v)) for k,v in sprites.items()}
json.dump(paths, open('viz/sprite_paths.json','w'), indent=0)

# contact sheet at TRUE sprite size (76x45) alongside a 3x zoom
cells=""
for k,dstr in paths.items():
    col = 'hsl(217 91% 50%)' if k=='walk' else 'hsl(215 16% 47%)'
    cells += f'''<figure style="margin:0;text-align:center">
      <svg viewBox="0 0 {VB_W:.0f} {VB_H:.0f}" width="76" height="45" style="background:#fff">
        <path d="{dstr}" fill="none" stroke="{col}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
      &nbsp;&nbsp;
      <svg viewBox="0 0 {VB_W:.0f} {VB_H:.0f}" width="228" height="135" style="border:1px solid #eee;background:#fff">
        <path d="{dstr}" fill="none" stroke="{col}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <figcaption style="font:12px sans-serif;color:#333">{k}</figcaption></figure>'''
open('viz/_contact.html','w').write(
  f'<!doctype html><meta charset=utf8><body style="font-family:sans-serif">'
  f'<div style="display:grid;grid-template-columns:1fr;gap:12px;padding:16px">{cells}</div>')
print("wrote sprite_paths.json (%d) and _contact.html"%len(paths))
for k in paths: print("  ",k, "len", len(sprites[k]))
