"""
ROUTE 2 -- TWIST ANGULAR DECORRELATION measurement.

Claim under test: all passes (maximal contiguous walk-arcs) through a Cheb-r ball
(r<=10) come from <=3 adjacent BIRTH levels (deep-tail), and adjacent-level passes
CANNOT be near-parallel because M rotates the yz-plane by arccos(-1/6)=99.594 deg per
level (the x-axis is a NON-rotating eigendirection, scale 3 only).

We:
  (1) build chain_L with an exact birth-level tag per point (route4 decomposition
      Walk_L = disjoint-union_j M^j . interiors(L-j), plus deep tail).
  (2) find dense balls (all walk-point centres), decompose the path into maximal
      contiguous arcs (passes) inside B(q,r).
  (3) tag each pass with (a) its birth level(s), (b) its direction (endpoint diff,
      and PCA principal axis), (c) how x-aligned it is (|dx|/|d|).
  (4) measure pairwise angles between passes: ADJACENT-level vs SAME-level, and the
      minimum angle seen. Report whether same-level passes ever stack near-parallel
      (the event that would break single-level refill linearity).
  (5) also directly test the pure geometry claim: min angle between M^j d and
      M^{j'} d' over the realized arc-direction pool, split by x-alignment.
"""
import sys, pickle, json, math
from collections import defaultdict
sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run
from amplify_rich import M_BAL3

M = [list(r) for r in M_BAL3]


def matmul(A, B):
    return [[sum(A[i][t] * B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]


def matvec(A, v):
    return tuple(sum(A[i][t] * v[t] for t in range(3)) for i in range(3))


def interiors_of(level):
    d = pickle.load(open("/Users/erik/homelab/math193/gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    ints = []
    for i in range(len(anchors) - 1):
        ints.extend(gate_run.word_interiors(anchors[i], words[i]))
    return ints


def chain_of(level):
    d = pickle.load(open("/Users/erik/homelab/math193/gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    ch = [tuple(anchors[0])]
    for i in range(len(anchors) - 1):
        ch.extend(tuple(p) for p in gate_run.word_interiors(anchors[i], words[i]))
        ch.append(tuple(anchors[i + 1]))
    return ch


def dilate(points, j):
    if j == 0:
        return [tuple(p) for p in points]
    Mj = [[1 if a == b else 0 for b in range(3)] for a in range(3)]
    for _ in range(j):
        Mj = matmul(Mj, M)
    return [matvec(Mj, p) for p in points]


def birth_tags(L):
    """Return dict point->birth j (0=freshest at level L). Deep tail j>=jmax+1 -> jmax+1."""
    jmax = L - 5
    tag = {}
    for j in range(jmax + 1):
        m = L - j
        for p in dilate(interiors_of(m), j):
            if p not in tag:
                tag[p] = j
    return tag, jmax


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def angle_between(u, v):
    nu, nv = norm(u), norm(v)
    if nu == 0 or nv == 0:
        return None
    c = (u[0] * v[0] + u[1] * v[1] + u[2] * v[2]) / (nu * nv)
    c = max(-1.0, min(1.0, c))
    # undirected angle: fold to [0,90]
    a = math.degrees(math.acos(abs(c)))
    return a


def arc_direction(chain, arc):
    """PCA principal direction of the arc points (unsigned)."""
    pts = [chain[i] for i in arc]
    n = len(pts)
    if n < 2:
        return None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    mz = sum(p[2] for p in pts) / n
    # covariance
    cxx = cxy = cxz = cyy = cyz = czz = 0.0
    for p in pts:
        dx, dy, dz = p[0] - mx, p[1] - my, p[2] - mz
        cxx += dx * dx; cxy += dx * dy; cxz += dx * dz
        cyy += dy * dy; cyz += dy * dz; czz += dz * dz
    # power iteration for top eigenvector of symmetric 3x3
    C = [[cxx, cxy, cxz], [cxy, cyy, cyz], [cxz, cyz, czz]]
    v = [1.0, 0.7, 0.3]
    for _ in range(80):
        w = [sum(C[i][k] * v[k] for k in range(3)) for i in range(3)]
        nw = norm(w)
        if nw == 0:
            break
        v = [x / nw for x in w]
    return tuple(v)


def analyze(L, radii=(5, 10), min_passes=3):
    chain = chain_of(L)
    tag, jmax = birth_tags(L)
    tailj = jmax + 1
    N = len(chain)
    birthlevel = [tag.get(chain[i], tailj) for i in range(N)]

    out = {"L": L, "N": N, "jmax": jmax, "theta_deg": 99.594}
    per_r = {}
    for r in radii:
        cell = r
        grid = defaultdict(list)
        for i, p in enumerate(chain):
            grid[(p[0] // cell, p[1] // cell, p[2] // cell)].append(i)

        # aggregate statistics
        max_passes = 0
        max_pass_center = None
        # angle histograms
        adj_angles = []       # angles between passes of ADJACENT birth level
        same_angles = []      # angles between passes of SAME birth level
        far_angles = []       # birth-level diff >=2
        # near-parallel stacking events (same-level, angle < 15 deg, both meet ball)
        same_nearparallel = 0
        same_total_pairs = 0
        # x-alignment of passes
        xalign_by_level = defaultdict(list)
        # record the densest ball's pass table
        dense_examples = []

        seen_centers = set()
        for qi in range(N):
            q = chain[qi]
            cx, cy, cz = q[0] // cell, q[1] // cell, q[2] // cell
            key = (cx, cy, cz)
            # dedupe by cell so we don't recount identical ball contents excessively
            idxs = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j in grid.get((cx + dx, cy + dy, cz + dz), ()):
                            if cheb(chain[j], q) <= r:
                                idxs.append(j)
            idxs.sort()
            # decompose into maximal contiguous arcs
            arcs = []
            cur = [idxs[0]]
            for a in idxs[1:]:
                if a == cur[-1] + 1:
                    cur.append(a)
                else:
                    arcs.append(cur); cur = [a]
            arcs.append(cur)
            P = len(arcs)
            if P < min_passes:
                continue
            # build pass records
            passes = []
            for arc in arcs:
                d = arc_direction(chain, arc)
                # dominant birth level = mode over arc points
                cnt = defaultdict(int)
                for i in arc:
                    cnt[birthlevel[i]] += 1
                bl = max(cnt, key=cnt.get)
                xa = None
                if d is not None:
                    xa = abs(d[0]) / (norm(d) + 1e-12)
                passes.append({"len": len(arc), "dir": d, "birth": bl, "xalign": xa})
            if P > max_passes:
                max_passes = P
                max_pass_center = q
            # pairwise angles
            for a in range(len(passes)):
                for b in range(a + 1, len(passes)):
                    pa, pb = passes[a], passes[b]
                    if pa["dir"] is None or pb["dir"] is None:
                        continue
                    ang = angle_between(pa["dir"], pb["dir"])
                    if ang is None:
                        continue
                    db = abs(pa["birth"] - pb["birth"])
                    if db == 0:
                        same_angles.append(ang)
                        same_total_pairs += 1
                        if ang < 15:
                            same_nearparallel += 1
                    elif db == 1:
                        adj_angles.append(ang)
                    else:
                        far_angles.append(ang)
            for p in passes:
                if p["xalign"] is not None:
                    xalign_by_level[p["birth"]].append(p["xalign"])
            # keep a few dense examples
            if P >= max(min_passes, max_passes - 0) and len(dense_examples) < 8:
                dense_examples.append({
                    "center": list(q),
                    "n_passes": P,
                    "passes": [{"len": p["len"], "birth": p["birth"],
                                "xalign": round(p["xalign"], 3) if p["xalign"] is not None else None}
                               for p in passes],
                })

        def summ(lst):
            if not lst:
                return None
            lst2 = sorted(lst)
            return {"n": len(lst2), "min": round(lst2[0], 2),
                    "p10": round(lst2[len(lst2) // 10], 2),
                    "med": round(lst2[len(lst2) // 2], 2),
                    "mean": round(sum(lst2) / len(lst2), 2)}

        per_r[r] = {
            "max_passes": max_passes,
            "max_pass_center": list(max_pass_center) if max_pass_center else None,
            "adjacent_level_angle": summ(adj_angles),
            "same_level_angle": summ(same_angles),
            "far_level_angle": summ(far_angles),
            "same_level_nearparallel_lt15deg": same_nearparallel,
            "same_level_total_pairs": same_total_pairs,
            "xalign_mean_by_birthlevel": {str(k): round(sum(v) / len(v), 3) for k, v in sorted(xalign_by_level.items()) if v},
            "dense_examples": dense_examples[:5],
        }
    out["per_r"] = per_r
    return out


if __name__ == "__main__":
    levels = [int(x) for x in sys.argv[1:]] or [6, 7]
    result = {}
    for L in levels:
        print("analyzing L%d..." % L, flush=True)
        result["L%d" % L] = analyze(L)
        print(json.dumps(result["L%d" % L], indent=1), flush=True)
    json.dump(result, open("/Users/erik/homelab/math193/design/exclusion/route2-angular-results.json", "w"), indent=1)
    print("WROTE design/exclusion/route2-angular-results.json")
