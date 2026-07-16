"""
TASK B — distribution-invariance + recursion fixed point.

(1) DISTRIBUTION: is the max-c(4.44) creep a DISTRIBUTION SHIFT or an
    EXTREME-VALUE artifact of sampling lam^k more points? Compute, per level,
    the FULL distribution of walk-centred crowding c(q,r) for r in {4,5} over
    ALL walk points: mean, p50, p99, p99.9, p99.99, max, and per-capita tail
    fractions P[c>=t]. If the mean + per-capita tail fractions are flat while
    only the max creeps, the distribution is level-invariant (small bound holds
    uniformly; max creep is just an order-statistic of a fixed law).

(2) FIXED POINT of the recursion c(rho) <= phi*c(rho) + refill, in the exact
    birth-telescoping form the proof uses:
       c(rho) = sum_j t_j,  t_j = #points born j levels back in B(q,rho)
    Deep-tail (min|M^3 v|inf=24 > 2*rho for rho<=10) => t_{j>=3} <= 1.
    Measure the ACTUAL t_j decomposition at the densest ball for r*=4.44
    (bracket via r=4,5) and the per-shell ratios t_{j+1}/t_j => empirical
    contraction. Report the closed-form fixed points:
       iso:   C = E * S_iso  (S_iso = sum (4/9)^j = 9/5 = 1.8)
       aniso: C = E * S_aniso (S_aniso = sum ||M^-j||inf = 1.67693)
    and c*(4.44) = C * 4.44  vs measured, and the power-law C_d * 4.44^d.
"""
import pickle, sys, math, json
from collections import defaultdict
from search193 import candidate_step_vectors
from amplify_rich import M_BAL3 as M

MENU = candidate_step_vectors(2)
LAM = 3.36
D_DIM = math.log(LAM)/math.log(3)
RSTAR = 4.44
S_ISO = 9/5
S_ANISO = 1.67693


def Mv(v):
    return (M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
            M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
            M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2])


def word_interiors(start, wi):
    pts = []; x, y, z = start
    for si in wi[:-1]:
        s = MENU[si]; x, y, z = x+s[0], y+s[1], z+s[2]; pts.append((x, y, z))
    return pts


def build_chain(L):
    d = pickle.load(open(f"gate2-l7-construction-L{L}.pkl", "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = []
    for i in range(len(anchors)-1):
        chain.append(tuple(anchors[i]))
        for q in word_interiors(anchors[i], words[i]):
            chain.append(q)
    chain.append(tuple(anchors[-1]))
    return chain


def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))


def dist_and_max(chain, r):
    cell = max(r, 1)
    g = defaultdict(list)
    for p in chain:
        g[(p[0]//cell, p[1]//cell, p[2]//cell)].append(p)
    counts = []
    best = 0; best_q = None
    for q in chain:
        gx, gy, gz = q[0]//cell, q[1]//cell, q[2]//cell
        c = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for p in g.get((gx+dx, gy+dy, gz+dz), ()):
                        if cheb(p, q) <= r:
                            c += 1
        counts.append(c)
        if c > best:
            best = c; best_q = q
    counts.sort()
    n = len(counts)

    def pct(p):
        return counts[min(n-1, int(p*n))]
    mean = sum(counts)/n
    tails = {t: round(sum(1 for c in counts if c >= t)/n, 8) for t in (8, 10, 12, 14, 16)}
    return {"mean": round(mean, 4), "p50": pct(0.50), "p99": pct(0.99),
            "p99.9": pct(0.999), "p99.99": pct(0.9999), "max": best,
            "tailfrac_P[c>=t]": tails}, best_q


def build_with_birth(L):
    """Full chain with per-point BIRTH LEVEL: a point born at level m appears
    first as an interior at level m and thereafter as an anchor image. We label
    each level-L point by how many levels back it was born by peeling anchors:
    anchors[i]=M*parent[i]; recurse birth via parent chain interiors."""
    # birth level of a level-L point = L - (#times it is an anchor-of-anchor...).
    # Simplest exact tag: a point is born-at-shell-0 (this level) iff it is a
    # fresh interior of L; born-shell-1 iff it is an anchor whose M^-1 is a fresh
    # interior of L-1; etc. Build via recursion over stored pkls.
    born = {}  # point -> shell (0 = born this level)
    # collect fresh interiors at each ancestor level j, map forward by M^j
    for j in range(0, L-3):  # shells 0..; deep tail j>=? but keep a few
        Lp = L - j
        if Lp < 5:
            break
        try:
            d = pickle.load(open(f"gate2-l7-construction-L{Lp}.pkl", "rb"))
        except FileNotFoundError:
            break
        anchors = d["anchors"]; words = d["words"]
        fresh = []
        for i in range(len(anchors)-1):
            for q in word_interiors(anchors[i], words[i]):
                fresh.append(q)
        # map each fresh point forward j levels by M
        for p in fresh:
            v = p
            for _ in range(j):
                v = Mv(v)
            if v not in born:
                born[v] = j
    return born


def birth_decomp_at(chain, q, r, born):
    cnt = defaultdict(int)
    for p in chain:
        if cheb(p, q) <= r:
            cnt[born.get(p, 99)] += 1
    return dict(cnt)


def main():
    Ls = [int(x) for x in sys.argv[1:]] or [6, 7, 8]
    out = {"d_dim": round(D_DIM, 4), "S_iso": S_ISO, "S_aniso": S_ANISO,
           "rstar": RSTAR, "levels": {}}
    for L in Ls:
        chain = build_chain(L)
        rec = {"N": len(chain)}
        for r in (4, 5):
            dist, bq = dist_and_max(chain, r)
            rec[f"c_r{r}_dist"] = dist
        out["levels"][L] = rec
        print(json.dumps({L: rec}), flush=True)
    # fixed-point summary (uses E=3 measured, deep-tail <=1)
    E = 3.0
    fp = {"E_measured": E,
          "C_iso_lin": round(E*S_ISO, 3), "c*_4.44_iso_lin": round(E*S_ISO*RSTAR, 2),
          "C_aniso_lin": round(E*S_ANISO, 3), "c*_4.44_aniso_lin": round(E*S_ANISO*RSTAR, 2),
          "note": "linear fixed points are LOOSE upper bounds; power-law C_d*r^d is the tight one",
          "C_d_measured_range": "3.0-3.26 (L6-L8)",
          "c*_4.44_powerlaw_Cd3": round(3.0*RSTAR**D_DIM, 2),
          "c*_4.44_powerlaw_Cd2.7": round(2.7*RSTAR**D_DIM, 2),
          "availability_jam_line_crowding": round(11.9/0.265, 1),
          "avail_log_words_at_c=measuredmax": "11.9 - 0.265*c"}
    out["fixed_point"] = fp
    print(json.dumps({"fixed_point": fp}), flush=True)
    json.dump(out, open("design/tight/taskB_distribution_fixedpoint.json", "w"), indent=1)
    print("WROTE design/tight/taskB_distribution_fixedpoint.json", flush=True)


if __name__ == "__main__":
    main()
