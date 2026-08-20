"""
ROUTE 2 - TRANSFER OPERATOR / RENEWAL on the exact birth-telescoping.

Goal: derive d in c_k(q,r) <= C r^d via the pressure equation, and MEASURE the
true per-shell charge kappa_j (interiors donated per birth-(k-j) anchor to a
Cheb-r ball) to test the anti-stacking (kappa ~ 1) that closes the transfer op.

Exact structure used (all verified elsewhere, re-checked here):
  Walk_L = M . Walk_{L-1}  DISJOINT-UNION  Stitch_{L-1}          (birth partition)
  interiors born at level m  ==  word-interiors of the L=m construction pkl
      (they decorate anchor-edges; anchors(m) = M.Walk_{m-1} = pkl['anchors'])
  In the Walk_K frame a birth-(K-j) interior P appears as M^j.P (M integer).
  Ball pullback is exact: P in M^{-j}B(q,r)  <=>  cheb(M^j P, q) <= r.

Measurements:
  (A) point growth lambda_L = N_L/N_{L-1}, extent ratio, d = log(lambda)/log(3).
  (B) ||M^{-j}||_inf sequence and bounded-distortion ratio ||M^{-j}||/3^{-j}.
  (C) per-shell charge kappa_j(r) = t_j / (#distinct donating anchors), avg & max
      over sampled ball centres, at K=7 and K=8, j=0..3, several r.  (anti-stacking)
  (D) telescoping amplitude S_d = sum_j ||M^{-j}||_inf^d, and C = B*S_d.
  (E) does C r^d bound measured c_K(r) on [1,10]? and the single-level refill b(r)?
"""
import pickle, math, json, random
from collections import defaultdict
from fractions import Fraction as F
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)
M = M_BAL3

def matvec(A, p):
    return (A[0][0]*p[0]+A[0][1]*p[1]+A[0][2]*p[2],
            A[1][0]*p[0]+A[1][1]*p[1]+A[1][2]*p[2],
            A[2][0]*p[0]+A[2][1]*p[1]+A[2][2]*p[2])

def matmat(A, B):
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))

def Mpow(j):
    R = ((1,0,0),(0,1,0),(0,0,1))
    for _ in range(j):
        R = matmat(R, M)
    return R

def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
           -A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
           +A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))

def inv(Mm):
    d = det3(Mm); C = [[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            minor = [[Mm[r][c] for c in range(3) if c != j] for r in range(3) if r != i]
            cof = minor[0][0]*minor[1][1]-minor[0][1]*minor[1][0]
            C[j][i] = F(((-1)**(i+j))*cof, d)
    return C

def norm_inf_frac(A):  # max row abs-sum of a rational matrix
    return max(sum(abs(A[i][j]) for j in range(3)) for i in range(3))

def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

def build(pkl):
    d = pickle.load(open(pkl, "rb"))
    return d["anchors"], d["words"]

def interiors_with_anchor(anchors, words):
    """Return list of (point, anchor_index) for every word-interior (=Stitch)."""
    out = []
    for i in range(len(anchors)-1):
        x, y, z = anchors[i]
        wi = words[i]
        for si in wi[:-1]:
            s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]
            out.append(((x, y, z), i))
    return out

def build_chain(anchors, words):
    chain = [tuple(anchors[0])]
    for i in range(len(anchors)-1):
        x, y, z = anchors[i]
        for si in words[i][:-1]:
            s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; chain.append((x, y, z))
        chain.append(tuple(anchors[i+1]))
    return chain

def extent(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; zs=[p[2] for p in pts]
    return max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

# ---------------------------------------------------------------- (A) growth
Ns = {}
chains = {}
for L in (5,6,7,8):
    a,w = build(f"gate2-l7-construction-L{L}.pkl")
    ch = build_chain(a,w)
    chains[L] = (a,w,ch)
    Ns[L] = len(ch)
growth = {}
for L in (6,7,8):
    growth[L] = {"N":Ns[L], "lambda":Ns[L]/Ns[L-1],
                 "extent_ratio": extent(chains[L][2])/extent(chains[L-1][2])}
lam = sum(growth[L]["lambda"] for L in (7,8))/2.0
d_growth = math.log(lam)/math.log(3.0)

# ---------------------------------------------------------------- (B) Minv norms
Minv = inv(M)
Mij = ((1,0,0),(0,1,0),(0,0,1))
minv_norms = []
cur = [[F(1 if i==j else 0) for j in range(3)] for i in range(3)]
curm = [[F(x) for x in row] for row in Mij]
# build M^{-j} by repeated mult
Minvf = [[Minv[i][j] for j in range(3)] for i in range(3)]
def fmatmat(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
P = [[F(1 if i==j else 0) for j in range(3)] for i in range(3)]
for j in range(9):
    minv_norms.append(float(norm_inf_frac(P)))
    P = fmatmat(P, Minvf)
distortion = [minv_norms[j]*(3.0**j) for j in range(9)]

# ---------------------------------------------------------------- pressure / S_d
def S_of_d(d):
    return sum(minv_norms[j]**d for j in range(len(minv_norms))) + \
           minv_norms[-1]**d * (3.0**(-d))/(1-3.0**(-d))  # geometric tail est

# ---------------------------------------------------------------- (C) kappa_j
def grid_bucket(points, cell):
    g = defaultdict(list)
    for idx,p in enumerate(points):
        g[(p[0]//cell, p[1]//cell, p[2]//cell)].append(idx)
    return g

def neigh(g, q, cell):
    cx,cy,cz = q[0]//cell, q[1]//cell, q[2]//cell
    out=[]
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                out.extend(g.get((cx+dx,cy+dy,cz+dz), ()))
    return out

def measure(K, radii, n_centres=1500, seed=0):
    random.seed(seed)
    # shells: j -> list of (pointInKframe, anchor_index)  for birth level K-j
    shells = {}
    for j in range(4):
        L = K-j
        if L not in chains: break
        a,w = chains[L][0], chains[L][1]
        iw = interiors_with_anchor(a,w)
        Mj = Mpow(j)
        shells[j] = [(matvec(Mj,p), ai) for (p,ai) in iw]
    chK = chains[K][2]
    centres = random.sample(chK, min(n_centres, len(chK)))
    # buckets per shell per radius cell
    res = {}
    for r in radii:
        cell = int(math.ceil(r))+1
        buckets = {j: grid_bucket([p for (p,_) in shells[j]], cell) for j in shells}
        per_r = {}
        for j in shells:
            pts = shells[j]
            g = buckets[j]
            t_sum=0; t_max=0; k_sum=0.0; k_max=0.0; ncontrib=0
            for q in centres:
                cand = neigh(g, q, cell)
                inball = [idx for idx in cand if cheb(q, pts[idx][0]) <= r]
                t = len(inball)
                if t==0:
                    continue
                anch = set(pts[idx][1] for idx in inball)
                kap = t/len(anch)
                t_sum += t; t_max = max(t_max, t)
                k_sum += kap; k_max = max(k_max, kap); ncontrib += 1
            per_r[j] = {"t_avg": t_sum/len(centres), "t_max": t_max,
                        "kappa_avg": (k_sum/ncontrib if ncontrib else 0.0),
                        "kappa_max": k_max, "frac_contrib": ncontrib/len(centres)}
        res[r] = per_r
    return res

# ---------------------------------------------------------------- (E) measured c_K(r)
def measured_c(K, radii):
    ch = chains[K][2]
    out={}
    for r in radii:
        cell=int(math.ceil(r))+1
        g=grid_bucket(ch,cell)
        mx=0
        # sup over all walk points as centres
        for i,q in enumerate(ch):
            cand=neigh(g,q,cell)
            c=sum(1 for idx in cand if cheb(q,ch[idx])<=r)
            if c>mx: mx=c
        out[r]=mx
    return out

# single-level refill b_K(r) = sup over centres of #interiors(K) in ball
def refill_b(K, radii):
    a,w=chains[K][0],chains[K][1]
    iw=[p for (p,_) in interiors_with_anchor(a,w)]
    out={}
    for r in radii:
        cell=int(math.ceil(r))+1
        g=grid_bucket(iw,cell)
        mx=0
        for q in iw:
            cand=neigh(g,q,cell)
            c=sum(1 for idx in cand if cheb(q,iw[idx])<=r)
            if c>mx: mx=c
        out[r]=mx
    return out

if __name__ == "__main__":
    RAD = [1,2,3,4,5,10]
    RADF = [1.0,2.0,4.4444,10.0]
    out = {
      "growth": growth, "lambda_avg": lam, "d_from_growth": d_growth,
      "minv_inf_norms": minv_norms, "distortion_ratio_vs_3^-j": distortion,
      "S_d": {str(d): S_of_d(d) for d in (1.0, 1.05, 1.10, 1.104, 1.15)},
      "kappa_K7": measure(7, RADF, n_centres=1500),
      "kappa_K8": measure(8, RADF, n_centres=1500),
    }
    out["measured_c_K8"] = measured_c(8, RAD)
    out["refill_b_K8"]   = refill_b(8, RAD)
    out["refill_b_K7"]   = refill_b(7, RAD)
    print(json.dumps(out, indent=1, default=str))
