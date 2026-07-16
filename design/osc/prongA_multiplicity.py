"""
PRONG A -- Multiplicity robustness across seeds.

Build fresh triple-free walks for many independent base seeds under the SAME
self-similar system used by the realized seed-193 walk (matrix M_BAL3, m=3, the
rich radius-2 menu), amplify each to level 5 with find_base + amplify_level, and
measure the graph-directed covering multiplicity mult_g(r) = max_q #{gen-g
cylinders meeting Cheb-ball B(q,r)} at matched scales r = 3^g and at full
diameter.  This is exactly the OSC/Ahlfors multiplicity constant that
Mauldin-Williams needs bounded uniformly on the MENU CLOSURE, not just on one
realized orbit.  If it is uniformly bounded and stable across many independent
adaptive orbits, that is strong evidence the bound is a property of the
construction rules (=> holds on the closure).  If some orbit blows it up,
adaptivity is essential and the MW frame is at risk.

We reconstruct the cylinder ancestry directly from the amplification structure:
level-L anchors = M . chain_{L-1}, and the level-L chain visits those anchors in
order with self-avoiding stitch interiors between them.  parent[j] = index (in
chain_{L-1}) of the anchor segment that chain-point j belongs to -- identical to
the convention in design/lemma/route1/mw_osc.py.  Parent maps compose down
generations exactly as there.
"""
import sys, math, json
from random import Random
from collections import defaultdict

from search193 import candidate_step_vectors
from imbricate_seam import walk_points
from imbricate193 import apply
from erdos193 import first_disqualifier
from amplify193 import amplify_level, find_base
from amplify_rich import M_BAL3

MENU = candidate_step_vectors(2)   # 124 radius-2 vectors: same menu as the realized walk


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def build_walk(seed, top_level=5, base_len=20, route="short", verbose=False):
    """find_base + amplify_level to `top_level`.  Returns list of (chain_L, parent_L)
    where parent_L[j] = index in chain_{L-1} of the anchor-segment of chain_L point j.
    parent_0 is None.  All levels independently verified triple-free."""
    rng = Random(seed)
    base = find_base(MENU, rng, length=base_len, tries=200)
    if base is None or len(base) < 8:
        return None
    chain = walk_points(base, MENU)
    assert first_disqualifier(chain) is None, "base not triple-free"
    levels = [(chain, None)]
    seg_maxlen = 12 + (4 if route == "wiggle" else 0)
    word = base
    for L in range(1, top_level + 1):
        prev_chain = chain
        new = amplify_level(word, MENU, M_BAL3, rng, seg_maxlen=seg_maxlen,
                            seg_tries=8, restarts=6, route=route)
        if new is None:
            if verbose:
                print(f"seed {seed}: level {L} FAILED", flush=True)
            break
        word = new
        chain = walk_points(word, MENU)
        # independent triple-free verification of the whole level
        assert first_disqualifier(chain) is None, f"level {L} not triple-free"
        # anchors of this level, in order = M . prev_chain
        anchors = [apply(M_BAL3, p) for p in prev_chain]
        anchor_set = {a: i for i, a in enumerate(anchors)}
        # parent[j] = index of anchor-segment.  Walk chain in order; every time we
        # hit an anchor, advance the parent pointer.  All points are distinct
        # (self-avoiding), so equality-matching is unambiguous.
        parent = []
        cur = -1
        for p in chain:
            if p in anchor_set and anchor_set[p] == cur + 1:
                cur += 1
            parent.append(cur)
        assert cur == len(anchors) - 1, f"level {L}: not all {len(anchors)} anchors matched (got {cur+1})"
        assert parent[0] == 0
        levels.append((chain, parent))
        if verbose:
            print(f"seed {seed}: level {L} len {len(chain)} verified", flush=True)
    return levels


def build_ancestry(levels, top_level, depth):
    """chain at top_level plus anc[g][j] = ancestor index in chain_{top_level-g}."""
    chain = levels[top_level][0]
    N = len(chain)
    anc = [list(range(N))]                      # g=0: itself
    acc = levels[top_level][1][:]               # g=1: parent in chain_{top_level-1}
    anc.append(acc[:])
    for g in range(2, depth + 1):
        pmap = levels[top_level - g + 1][1]     # chain_{top_level-g+1} -> chain_{top_level-g}
        acc = [pmap[acc[j]] for j in range(N)]
        anc.append(acc[:])
    return chain, anc


def cylinders(anc_g):
    groups = defaultdict(list)
    for j, a in enumerate(anc_g):
        groups[a].append(j)
    return groups


def cyl_diam(chain, idxs):
    xs = [chain[j][0] for j in idxs]; ys = [chain[j][1] for j in idxs]; zs = [chain[j][2] for j in idxs]
    return max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def covering_multiplicity(chain, anc_g, r):
    """max over walk points q of #distinct gen-g cylinder ids within Cheb-r of q."""
    cell = max(r, 1)
    grid = defaultdict(list)
    for j, p in enumerate(chain):
        grid[(p[0] // cell, p[1] // cell, p[2] // cell)].append(j)
    best = 0
    for q in chain:
        gx, gy, gz = q[0] // cell, q[1] // cell, q[2] // cell
        ids = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((gx + dx, gy + dy, gz + dz), ()):
                        if cheb(chain[j], q) <= r:
                            ids.add(anc_g[j])
        if len(ids) > best:
            best = len(ids)
    return best


def full_diameter(chain):
    xs = [p[0] for p in chain]; ys = [p[1] for p in chain]; zs = [p[2] for p in chain]
    return max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def measure_seed(seed, top_level=5, depth=3, base_len=20, route="short"):
    levels = build_walk(seed, top_level=top_level, base_len=base_len, route=route)
    if levels is None or len(levels) <= top_level:
        return {"seed": seed, "route": route, "ok": False,
                "reached_level": (len(levels) - 1) if levels else -1}
    chain, anc = build_ancestry(levels, top_level, depth)
    N = len(chain)
    n_parents = len(cylinders(anc[1]))
    lam = N / n_parents
    d = math.log(lam) / math.log(3)
    diam = full_diameter(chain)
    res = {"seed": seed, "route": route, "ok": True, "N": N,
           "reached_level": top_level, "lambda": round(lam, 4), "d": round(d, 4),
           "full_diameter": diam, "gens": {}}
    for g in range(1, depth + 1):
        groups = cylinders(anc[g])
        diams = sorted(cyl_diam(chain, idxs) for idxs in groups.values())
        med = diams[len(diams) // 2]; mx = diams[-1]
        r3 = 3 ** g
        mult_r3 = covering_multiplicity(chain, anc[g], r3)
        mult_diam = covering_multiplicity(chain, anc[g], diam)
        res["gens"][g] = {
            "n_cyl": len(groups), "cyl_diam_median": med, "cyl_diam_max": mx,
            "r_3^g": r3, "mult_at_3^g": mult_r3,
            "mult_at_full_diameter": mult_diam,
        }
    return res


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [193, 1, 2, 7, 42, 100, 271, 555]
    top_level = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    route = sys.argv[3] if len(sys.argv) > 3 else "short"
    out = []
    for s in seeds:
        r = measure_seed(s, top_level=top_level, route=route)
        out.append(r)
        print(json.dumps(r), flush=True)
    print("=== SUMMARY ===")
    print(json.dumps(out, indent=2))
