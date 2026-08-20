"""Judge verification: tail certificate rigor + adversarial C + cross-level creep."""
import os, sys, pickle, math
os.chdir("/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3

M = [list(r) for r in M_BAL3]

def matmul(A, B):
    return [[sum(A[i][t]*B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]
def matvec(A, v):
    return tuple(sum(A[i][t]*v[t] for t in range(3)) for i in range(3))
def transpose(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]

M2 = matmul(M, M)
M3 = matmul(M2, M)
print("M3 =", M3)

# ---- (1) min |M^3 v|_inf over a lattice box, growing box ----
def min_infnorm_lattice(A, N):
    best = None; argmin = None
    for x in range(-N, N+1):
        for y in range(-N, N+1):
            for z in range(-N, N+1):
                if x==0 and y==0 and z==0: continue
                w = matvec(A, (x,y,z))
                m = max(abs(w[0]),abs(w[1]),abs(w[2]))
                if best is None or m < best:
                    best = m; argmin = (x,y,z)
    return best, argmin

for N in (4, 6, 8, 12, 16, 20):
    b, arg = min_infnorm_lattice(M3, N)
    print("min|M3 v|inf over |v|inf<=%2d : %d  at v=%s" % (N, b, arg))

# ---- (2) sigma_min(M3): smallest singular value = sqrt(min eig of M3^T M3) ----
# inverse power iteration in float
G = matmul(transpose(M3), M3)   # symmetric PD
# invert G (float)
def inv3f(m):
    a,b,c=m[0]; d,e,f=m[1]; g,h,i=m[2]
    det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    adj=[[(e*i-f*h),-(b*i-c*h),(b*f-c*e)],
         [-(d*i-f*g),(a*i-c*g),-(a*f-c*d)],
         [(d*h-e*g),-(a*h-b*g),(a*e-b*d)]]
    return [[adj[r][cc]/det for cc in range(3)] for r in range(3)]
Gi = inv3f([[float(x) for x in r] for r in G])
v=[1.0,0.3,-0.7]
for _ in range(300):
    w=matvec(Gi, v)
    n=math.sqrt(sum(c*c for c in w)); v=[c/n for c in w]
lam_max_Gi = sum(v[i]*sum(Gi[i][j]*v[j] for j in range(3)) for i in range(3))
sig_min = 1.0/math.sqrt(lam_max_Gi)
# largest eig of G -> sigma_max
v=[1.0,0.3,-0.7]
for _ in range(300):
    w=matvec([[float(x) for x in r] for r in G], v)
    n=math.sqrt(sum(c*c for c in w)); v=[c/n for c in w]
lam_max_G = sum(v[i]*sum(float(G[i][j])*v[j] for j in range(3)) for i in range(3))
sig_max = math.sqrt(lam_max_G)
print("sigma_min(M3) = %.5f   sigma_max(M3)=%.5f" % (sig_min, sig_max))
# analytic guarantee: |M3 v|inf >= |M3 v|_2/sqrt(3) >= sig_min*|v|_2/sqrt3 >= sig_min/sqrt3 for |v|>=1
print("analytic floor |M3 v|inf >= sigma_min/sqrt(3) = %.4f  (need > 2*rho=20)" % (sig_min/math.sqrt(3)))
# |v|_2 threshold so analytic bound exceeds 20:
thr = 20.0*math.sqrt(3)/sig_min
print("analytic bound > 20 once |v|_2 > %.4f  => finite check needed only for |v|_2 <= %.4f" % (thr, thr))

# ---- (3) reconfirm c_k profile + worst (c-1)/rho, cross-level creep ----
def chain_of(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors=d["anchors"]; words=d["words"]
    ch=[anchors[0]]
    for i in range(len(anchors)-1):
        ch.extend(gate_run.word_interiors(anchors[i], words[i]))
        ch.append(anchors[i+1])
    return ch

def build_hash(points, cell):
    H={}
    for p in points:
        H.setdefault((p[0]//cell,p[1]//cell,p[2]//cell),[]).append(p)
    return H
def exact_sup(points, rho):
    if not points: return 0
    W=2*int(rho); cell=int(W)+1; H=build_hash(points,cell); best=0
    for a in points:
        a0,a1,a2=a; kx=a0//cell; ky=a1//cell; kz=a2//cell; slab=[]
        for dx in (0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    bb=H.get((kx+dx,ky+dy,kz+dz))
                    if bb:
                        for p in bb:
                            if a0<=p[0]<=a0+W and abs(p[1]-a1)<=W and abs(p[2]-a2)<=W:
                                slab.append(p)
        if len(slab)<=best: continue
        ys=sorted(set(p[1] for p in slab))
        for cy in ys:
            ysel=[p for p in slab if cy<=p[1]<=cy+W]
            if len(ysel)<=best: continue
            zs=sorted(p[2] for p in ysel); lo=0
            for hi in range(len(zs)):
                while zs[hi]-zs[lo]>W: lo+=1
                cnt=hi-lo+1
                if cnt>best: best=cnt
    return best

for L in (6,7,8):
    ch=chain_of(L)
    prof=[exact_sup(ch,rho) for rho in range(1,11)]
    slopes=[round((prof[r-1]-1)/r,3) for r in range(1,11)]
    worst=max(slopes)
    print("L%d c=%s  (c-1)/rho=%s  worstC=%.3f  N=%d" % (L, prof, slopes, worst, len(ch)))
