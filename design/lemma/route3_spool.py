"""
ROUTE 3 -- MONOTONE ESCAPE / TRANSIENCE via the SPOOL COORDINATE.

Spool coordinate (M-adapted log-radius):
    u(p) = 0.5 * log_3( Q(p) ),   Q(x,y,z) = x^2 + 6 y^2 - 2 y z + 6 z^2.
Exact self-similarity (verified):  Q(Mp) = 9 Q(p)  =>  u(Mp) = u(p) + 1.
So EACH application of the amplifying matrix M advances the spool by exactly one
"turn" (+1). u is the unspooling coordinate: the walk pays out thread.

Companion angular coordinate theta(p): polar angle of (y,z) in the Q_yz-orthonormal
frame; under M, theta advances by the irrational rotation alpha (cos alpha = -1/6).
Together zeta = (u, theta) is the log-spiral coordinate: M is translation by
(1, alpha) in zeta-space.

TRANSIENCE => BOUNDED RETURNS (the derivation this script tests):
  A ball B(q,r), r<=10, at Q-radius R.  Every in-ball point has u within
  Lambda(r,R) of u(q), with Lambda -> 0 as R grows (u is smooth, |grad u|~1/R).
  Because u = (colevel)*1 + u_fresh  and u advances by EXACTLY +1 per M, the
  colevels (birth levels) contributing to the ball are confined to a band of
  width <= Lambda + osc(u_fresh) =: B0  (a LEVEL-UNIFORM constant if u_fresh is
  level-uniformly bounded).  => <= B0+1 distinct birth levels meet the ball.
  Within one birth level nu, in-ball points are M^{K-nu} of "fresh" points that
  land in the pulled-back ball of radius r*3^{-(K-nu)} <= r/3 < 4; by self-similar
  reduction these form <= A_base separate arcs.
      A(q,r) <= (B0+1) * A_base = A0,  level-uniform.

This script MEASURES, at L5/L6/L7:
  (M1) exact +1 per M (sanity).
  (M2) wiggle boundedness: range of u_fresh = u - (best-fit birth offset), level-uniform?
  (M3) per-ball arc decomposition for r in 1..10:
        A0 = max #arcs; max #distinct birth levels/ball; A_base = max #arcs at one
        birth level in a ball; min inter-arc spiral separation.
  (M4) per-arc net progress of u, and amortized drift of u along the walk index.

Run:  PYTHONPATH=/Users/erik/homelab/math193 pypy3 route3_spool.py
"""
import sys, pickle, json, math
from collections import defaultdict

sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors

LOG3 = math.log(3.0)


def Q(p):
    x, y, z = p
    return x * x + 6 * y * y - 2 * y * z + 6 * z * z


def u_coord(p):
    q = Q(p)
    if q == 0:
        return 0.0  # origin only
    return 0.5 * math.log(q) / LOG3  # in units where u(Mp)=u(p)+1


# Q_yz-orthonormal frame for the angle.  Q_yz=[[6,-1],[-1,6]]=L L^T (Cholesky)
_S6 = math.sqrt(6.0)
_L11 = _S6
_L21 = -1.0 / _S6
_L22 = math.sqrt(6.0 - 1.0 / 6.0)  # sqrt(35/6)


def theta_coord(p):
    # xi = L^T (y,z); |xi|^2 = Q_yz(y,z); angle = atan2
    _, y, z = p
    xi1 = _L11 * y + _L21 * z
    xi2 = _L22 * z
    return math.atan2(xi2, xi1)


def Mmul(v):
    x, y, z = v
    return (3 * x, -3 * z, 3 * y - z)


def Minv(v):
    """M^{-1}(X,Y,Z) = (X/3, (3Z-Y)/9, -Y/3); returns None if non-integer."""
    X, Y, Z = v
    if X % 3 or Y % 3:
        return None
    yy = 3 * Z - Y
    if yy % 9:
        return None
    return (X // 3, yy // 9, -Y // 3)


def load_chain(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl", "rb"))
    a = d["anchors"]; w = d["words"]
    ch = [a[0]]
    for i in range(len(a) - 1):
        ch.extend(word_interiors(a[i], w[i]))
        ch.append(a[i + 1])
    return ch


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def compute_colevels(top_level):
    """colevel(p) = # times M^{-1} stays on the successively lower REAL chain.
    anchors_k = M*chain_{k-1}, so p in chain_k is 'inherited' iff M^{-1}p in chain_{k-1}.
    Bottom cap: below the lowest available chain (L5) fall back to M^{-1}-integer count."""
    chains = {lv: load_chain(lv) for lv in range(5, top_level + 1)}
    sets = {lv: set(chains[lv]) for lv in chains}
    lowest = 5

    memo = {}

    def colevel_at(lv, p):
        key = (lv, p)
        v = memo.get(key)
        if v is not None:
            return v
        pi = Minv(p)
        if lv > lowest:
            if pi is not None and pi in sets[lv - 1]:
                r = 1 + colevel_at(lv - 1, pi)
            else:
                r = 0
        else:
            # lowest available chain: proxy by M^{-1}-integer pullback depth.
            # GUARD: origin is an M^{-1} fixed point -> cap depth to avoid inf loop.
            r = 0
            cur = p
            while cur != (0, 0, 0) and r < 60:
                nx = Minv(cur)
                if nx is None:
                    break
                r += 1
                cur = nx
        memo[key] = r
        return r

    top = chains[top_level]
    return [colevel_at(top_level, p) for p in top], top


def arcs_of(idxs):
    idxs.sort()
    arcs = [[idxs[0]]]
    for a in idxs[1:]:
        if a == arcs[-1][-1] + 1:
            arcs[-1].append(a)
        else:
            arcs.append([a])
    return arcs


def grid_index(chain, cell):
    g = defaultdict(list)
    for i, p in enumerate(chain):
        g[(p[0] // cell, p[1] // cell, p[2] // cell)].append(i)
    return g


def analyze_level(level, want_colevels=True):
    if want_colevels:
        colev, chain = compute_colevels(level)
    else:
        chain = load_chain(level)
        colev = [0] * len(chain)
    N = len(chain)
    us = [u_coord(p) for p in chain]
    ths = [theta_coord(p) for p in chain]

    # (M2) wiggle: u_fresh = u - colevel.  Its range over the chain.
    fresh = [us[i] - colev[i] for i in range(N)]
    wiggle_min, wiggle_max = min(fresh), max(fresh)

    # (M4) amortized drift of u along index (min over i of u[i+n]-u[i])
    drift = {}
    for n in (1, 2, 5, 10, 20, 50, 100, 300, 1000):
        if n >= N:
            continue
        m = min(us[i + n] - us[i] for i in range(0, N - n, max(1, (N - n) // 4000)))
        drift[n] = round(m, 4)

    # (M3) per-ball arc decomposition
    per_rho = {}
    for rho in range(1, 11):
        cell = rho
        grid = grid_index(chain, cell)
        A0 = 0; A0_ball = None
        max_birthspread = 0
        max_arcs_one_birth = 0
        min_interarc_sep = 1e9  # min spiral separation between consecutive arcs (same ball)
        worst_c = 0
        # sample every center; N up to ~93k -> fine in pypy
        for qi, q in enumerate(chain):
            cx, cy, cz = q[0] // cell, q[1] // cell, q[2] // cell
            idxs = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j in grid.get((cx + dx, cy + dy, cz + dz), ()):
                            if cheb(chain[j], q) <= rho:
                                idxs.append(j)
            if len(idxs) > worst_c:
                worst_c = len(idxs)
            arcs = arcs_of(idxs)
            A = len(arcs)
            if A > A0:
                A0 = A; A0_ball = qi
            # birth spread: distinct colevels among in-ball points
            bl = set(colev[j] for j in idxs)
            if len(bl) > max_birthspread:
                max_birthspread = len(bl)
            # arcs sharing a birth level: an arc's birth level = colevel of its points
            # (an arc is contiguous & typically single birth level; take the mode)
            byb = defaultdict(int)
            for arc in arcs:
                # dominant birthlevel of the arc
                cnt = defaultdict(int)
                for j in arc:
                    cnt[colev[j]] += 1
                b = max(cnt, key=cnt.get)
                byb[b] += 1
            if byb:
                m = max(byb.values())
                if m > max_arcs_one_birth:
                    max_arcs_one_birth = m
            # inter-arc spiral separation: represent each arc by its centroid u
            if A >= 2:
                reps = sorted((sum(us[j] for j in arc) / len(arc)) for arc in arcs)
                for a, b in zip(reps, reps[1:]):
                    if b - a < min_interarc_sep:
                        min_interarc_sep = b - a
        per_rho[rho] = {
            "A0_max_arcs": A0,
            "max_c": worst_c,
            "max_birthlevel_spread": max_birthspread,
            "A_base_max_arcs_one_birthlevel": max_arcs_one_birth,
            "min_interarc_u_sep": None if min_interarc_sep > 1e8 else round(min_interarc_sep, 4),
        }
    return {
        "level": level, "N": N,
        "wiggle_u_fresh": [round(wiggle_min, 4), round(wiggle_max, 4),
                            round(wiggle_max - wiggle_min, 4)],
        "u_amortized_drift_min": drift,
        "per_rho": per_rho,
    }


def main():
    out = {"levels": {}}
    for lv in (5, 6, 7):
        print(f"=== analyzing L{lv} ===", flush=True)
        r = analyze_level(lv)
        out["levels"][lv] = r
        print(json.dumps(r, indent=2), flush=True)
    # cross-level uniformity
    print("\n=== LEVEL-UNIFORMITY (the crux) ===")
    print("wiggle range u_fresh:",
          {lv: out["levels"][lv]["wiggle_u_fresh"][2] for lv in (5, 6, 7)})
    print("rho | A0(5/6/7) | birthspread(5/6/7) | A_base(5/6/7)")
    for rho in range(1, 11):
        A0 = [out["levels"][lv]["per_rho"][rho]["A0_max_arcs"] for lv in (5, 6, 7)]
        bs = [out["levels"][lv]["per_rho"][rho]["max_birthlevel_spread"] for lv in (5, 6, 7)]
        ab = [out["levels"][lv]["per_rho"][rho]["A_base_max_arcs_one_birthlevel"] for lv in (5, 6, 7)]
        print(f"{rho:3d} | {A0} | {bs} | {ab}")
    with open("/Users/erik/homelab/math193/design/lemma/route3-spool-results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote route3-spool-results.json")


if __name__ == "__main__":
    main()
