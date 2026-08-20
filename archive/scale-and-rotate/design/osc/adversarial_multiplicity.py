"""
GAP (iii) -- ADVERSARIAL worst-case covering multiplicity.

The prongA builder chooses stitches to be SHORT (route="short") -- it hugs the
anchor chords and produces a flat, low-crowding clearance spectrum, giving the
realized 4/5/4.  route="wiggle" steers stitches perpendicular to the chord to
spread the walk off straight lines (transversal clearance).  Neither ROUTE tries
to MAXIMIZE covering multiplicity.

This module adds an ADVERSARIAL router (route="crowd") that, on top of the SAME
verified anchor-guided builder (every placed vertex passes legal_against =
no-repeat + triple-free, and each finished level is re-verified globally by
first_disqualifier), deliberately chooses stitches to MAXIMIZE local point
crowding.  The DFS candidate ordering is scored so the walk folds as tightly
back onto its own already-placed points as legality allows.

WHY crowding is the right adversarial objective.  Prong B / gap (i) established
that mult_g(r=3^g) equals the POINT-CROWDING of the parent walk (g levels down)
inside a bounded ~6.2 Cheb window (BOUND2, self-similar).  Maximizing covering
multiplicity at every matched scale is therefore the same as maximizing the max
number of walk points inside a small Cheb ball AT EVERY LEVEL -- and by exact
self-similarity (M = 3O) that crowding compounds across levels.  So a greedy
"place each stitch point to maximize neighbours within a small Cheb radius"
router is the natural max-transversal-crowding adversary.

Legality is untouched: the adversary only REORDERS which legal continuations the
DFS tries first, and gives stitches a little extra depth-slack to reach dense
regions.  Every returned level is independently triple-free (asserted).

Usage:
  pypy3 design/osc/adversarial_multiplicity.py SEEDS TOP_LEVEL CROWD_RADIUS SLACK
e.g.
  pypy3 design/osc/adversarial_multiplicity.py 193,1,2,7,42 5 3 3
"""
import sys, math, json
from random import Random
from collections import defaultdict

from search193 import candidate_step_vectors
from imbricate_seam import walk_points
from imbricate193 import apply
from erdos193 import first_disqualifier
from amplify193 import find_base, legal_against
from amplify_rich import M_BAL3

# reuse the verified prongA measurement helpers
from design.osc.prongA_multiplicity import (
    cheb, build_ancestry, cylinders, cyl_diam, covering_multiplicity, full_diameter,
)

MENU = candidate_step_vectors(2)   # 124 radius-2 vectors, same menu as the realized walk


def _cellkey(p, c):
    return (p[0] // c, p[1] // c, p[2] // c)


def amplify_level_adv(word, steps, M, rng, seg_maxlen=16, seg_tries=4, restarts=4,
                      crowd_radius=3, slack=1, node_cap=6000, prefer_short=False):
    """One amplification level with an ADVERSARIAL max-crowding stitch router.

    Identical legality to amplify193.amplify_level (no-repeat + triple-free via
    legal_against, future anchors as obstacles, whole level re-verified).  The
    ONLY change: at each DFS node the legal continuations are ordered CROWD-FIRST
    (fold toward already-placed points), and each stitch may take `slack` extra
    steps beyond the shortest to detour into dense regions.  A cheap
    gap-feasibility prefilter (skip steps that cannot reach the anchor in the
    remaining depth) is applied BEFORE the expensive collinearity check so the
    adversary cannot blow up by steering away from the target.
    Returns the new word (over `steps`) or None.
    """
    anchors = [apply(M, p) for p in walk_points(word, steps)]
    max_step = max(max(abs(c) for c in s) for s in steps)
    best_progress = 0

    for _ in range(restarts):
        points = [anchors[0]]
        point_set = {anchors[0]}
        # spatial grid of committed points for O(1) crowding queries
        grid = defaultdict(list)
        grid[_cellkey(anchors[0], crowd_radius)].append(anchors[0])
        new_word = []
        failed = False

        for seg_index, target in enumerate(anchors[1:]):
            done = False
            future = anchors[seg_index + 2:]
            future_set = set(future)

            def crowd_score(p, seg_points):
                # #already-placed points (committed grid + this stitch) within
                # Cheb crowd_radius of p.  Higher == more local crowding.
                gx, gy, gz = _cellkey(p, crowd_radius)
                cnt = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            for q in grid.get((gx + dx, gy + dy, gz + dz), ()):
                                if cheb(q, p) <= crowd_radius:
                                    cnt += 1
                for q in seg_points:
                    if cheb(q, p) <= crowd_radius:
                        cnt += 1
                return cnt

            gap0 = max(abs(target[i] - points[-1][i]) for i in range(3))
            shortest = max(1, -(-gap0 // max_step))
            hi = min(shortest + slack, seg_maxlen)

            def run_dfs(depth_limit, mode):
                seg_points, seg_word = [], []
                nodes = [0]

                def dfs(depth):
                    nodes[0] += 1
                    if nodes[0] > node_cap:
                        return False
                    last = points[-1] if not seg_points else seg_points[-1]
                    gap = max(abs(target[i] - last[i]) for i in range(3))
                    if gap == 0:
                        return True
                    if depth == 0 or gap > depth * max_step:
                        return False
                    cands = []
                    for si in range(len(steps)):
                        s = steps[si]
                        p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
                        if p == target:
                            cands.append((1e18, si, p))  # reaching anchor: best
                            continue
                        # cheap gap-feasibility prefilter BEFORE collinearity check
                        newgap = max(abs(target[i] - p[i]) for i in range(3))
                        if newgap > (depth - 1) * max_step:
                            continue
                        if legal_against(
                            points + seg_points + [target] + future,
                            point_set | set(seg_points) | {target} | future_set,
                            p,
                        ):
                            if mode == "crowd":
                                key = crowd_score(p, seg_points) + rng.random()
                            else:  # "progress": greedy toward target (baseline-like), robust
                                key = -newgap + rng.random()
                            cands.append((key, si, p))
                    cands.sort(reverse=True)
                    for _sc, si, p in cands:
                        seg_points.append(p)
                        seg_word.append(si)
                        if dfs(depth - 1):
                            return True
                        seg_points.pop()
                        seg_word.pop()
                    return False

                if dfs(depth_limit):
                    return seg_points, seg_word
                return None

            found = False
            seg_points = seg_word = None
            # ADVERSARIAL pass: crowd-ordered candidates.  prefer_short=True
            # tries SHORTEST depth first (baseline-like lambda; isolates the pure
            # ROUTING effect at matched density) and climbs to seg_maxlen for
            # reachability; prefer_short=False tries the LONGEST allowed depth
            # first (spends slack folding into dense regions -> higher lambda).
            if prefer_short:
                depth_order = list(range(shortest, seg_maxlen + 1))
            else:
                depth_order = list(range(hi, shortest - 1, -1))
            for _ in range(seg_tries):
                for depth_limit in depth_order:
                    got = run_dfs(depth_limit, "crowd")
                    if got is not None:
                        seg_points, seg_word = got
                        found = True
                        break
                if found:
                    break
            # FALLBACK pass: progress-ordered (baseline reachability) so the
            # adversarial build never stalls where a legal stitch exists.
            if not found:
                for _ in range(seg_tries):
                    for depth_limit in range(shortest, seg_maxlen + 1):
                        got = run_dfs(depth_limit, "progress")
                        if got is not None:
                            seg_points, seg_word = got
                            found = True
                            break
                    if found:
                        break
            if found:
                for p in seg_points:
                    grid[_cellkey(p, crowd_radius)].append(p)
                points.extend(seg_points)
                point_set.update(seg_points)
                new_word.extend(seg_word)
                best_progress = max(best_progress, seg_index + 1)
            else:
                best_progress = max(best_progress, seg_index)
                failed = True
                break

        if not failed:
            assert first_disqualifier(points) is None
            return new_word
    print(f"    (adv stitcher best progress: {best_progress}/{len(anchors) - 1})", flush=True)
    return None


def build_walk_adv(seed, top_level=5, base_len=20, crowd_radius=3, slack=3,
                   seg_maxlen=16, verbose=False, prefer_short=False):
    rng = Random(seed)
    base = find_base(MENU, rng, length=base_len, tries=200)
    if base is None or len(base) < 8:
        return None
    chain = walk_points(base, MENU)
    assert first_disqualifier(chain) is None
    levels = [(chain, None)]
    word = base
    for L in range(1, top_level + 1):
        prev_chain = chain
        new = amplify_level_adv(word, MENU, M_BAL3, rng, seg_maxlen=seg_maxlen,
                                seg_tries=4, restarts=4, crowd_radius=crowd_radius,
                                slack=slack, prefer_short=prefer_short)
        if new is None:
            if verbose:
                print(f"seed {seed}: level {L} FAILED", flush=True)
            break
        word = new
        chain = walk_points(word, MENU)
        assert first_disqualifier(chain) is None, f"level {L} not triple-free"
        anchors = [apply(M_BAL3, p) for p in prev_chain]
        anchor_set = {a: i for i, a in enumerate(anchors)}
        parent = []
        cur = -1
        for p in chain:
            if p in anchor_set and anchor_set[p] == cur + 1:
                cur += 1
            parent.append(cur)
        assert cur == len(anchors) - 1, f"level {L}: not all anchors matched"
        assert parent[0] == 0
        levels.append((chain, parent))
        if verbose:
            print(f"seed {seed}: level {L} len {len(chain)} verified", flush=True)
    return levels


def max_point_density(chain, r):
    """max over walk points q of #walk POINTS within Cheb-r of q (cylinder-agnostic
    raw crowding = the BOUND2 quantity the adversary is really pushing)."""
    cell = max(r, 1)
    grid = defaultdict(list)
    for j, p in enumerate(chain):
        grid[(p[0] // cell, p[1] // cell, p[2] // cell)].append(j)
    best = 0
    for q in chain:
        gx, gy, gz = q[0] // cell, q[1] // cell, q[2] // cell
        cnt = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((gx + dx, gy + dy, gz + dz), ()):
                        if cheb(chain[j], q) <= r:
                            cnt += 1
        if cnt > best:
            best = cnt
    return best


def measure_seed_adv(seed, top_level=5, depth=3, base_len=20, crowd_radius=3, slack=3,
                     seg_maxlen=16, verbose=False, prefer_short=False):
    levels = build_walk_adv(seed, top_level=top_level, base_len=base_len,
                            crowd_radius=crowd_radius, slack=slack,
                            seg_maxlen=seg_maxlen, verbose=verbose,
                            prefer_short=prefer_short)
    if levels is None or len(levels) <= top_level:
        return {"seed": seed, "route": "crowd", "ok": False,
                "reached_level": (len(levels) - 1) if levels else -1,
                "crowd_radius": crowd_radius, "slack": slack}
    chain, anc = build_ancestry(levels, top_level, depth)
    N = len(chain)
    n_parents = len(cylinders(anc[1]))
    lam = N / n_parents
    d = math.log(lam) / math.log(3)
    diam = full_diameter(chain)
    res = {"seed": seed, "route": "crowd", "ok": True, "N": N,
           "reached_level": top_level, "lambda": round(lam, 4), "d": round(d, 4),
           "full_diameter": diam, "crowd_radius": crowd_radius, "slack": slack,
           "gens": {}}
    for g in range(1, depth + 1):
        groups = cylinders(anc[g])
        diams = sorted(cyl_diam(chain, idxs) for idxs in groups.values())
        med = diams[len(diams) // 2]; mx = diams[-1]
        r3 = 3 ** g
        mult_r3 = covering_multiplicity(chain, anc[g], r3)
        dens_r3 = max_point_density(chain, r3)
        res["gens"][g] = {
            "n_cyl": len(groups), "cyl_diam_median": med, "cyl_diam_max": mx,
            "r_3^g": r3, "mult_at_3^g": mult_r3, "point_density_at_3^g": dens_r3,
        }
    return res


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [193, 1, 2, 7, 42]
    top_level = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    crowd_radius = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    slack = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    out = []
    for s in seeds:
        r = measure_seed_adv(s, top_level=top_level, crowd_radius=crowd_radius,
                             slack=slack, verbose=True)
        out.append(r)
        print("RESULT " + json.dumps(r), flush=True)
    gmax = 0
    for r in out:
        if r.get("ok"):
            for g, gd in r["gens"].items():
                gmax = max(gmax, gd["mult_at_3^g"])
    print(f"=== MAX mult_g(3^g) over all seeds/gens = {gmax} (cap under test = 5) ===", flush=True)
    print(json.dumps(out))
