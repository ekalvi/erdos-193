"""
ATTACK 1 — certification of the band72-len18 hard jam.

Replays the repaired constructor (fragile-first order, shortest-first choice,
full word spaces) on the crafted-but-legal base walk crafted_band(Random(72),
18, band, ultra, False) at level 1 up to the jam segment, then:
  1. exhaustively re-verifies 0/15920 surviving words with the REFERENCE
     legality path (gate_run.word_legal on plain point lists, which wraps
     amplify193.legal_against) — independent of fast_legal;
  2. runs gate_run.dfs_fallback exactly as gate_run.run_level and
     gate_l7.construct would (both rng conventions, maxlen 8) — the
     constructor's last resort;
  3. runs an exhaustive iterative-deepening DFS (deterministic order, node
     budget NB, progress printed) certifying no legal stitch word of ANY
     length <= MAXDEPTH exists;
  4. re-verifies the base walk is triple-free and that every constructor
     choice up to the jam followed the exact gate choice rule.
Also certifies band71-len18 L1 exact 2-word availability with the reference
path. Prints JSON summary at the end.
"""
from __future__ import annotations

import json
import sys
import time
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193/design")

from attack1_seed import MENU, FRAGILE_CUT  # noqa: E402  (does chdir)
from attack1_wave2 import crafted_band  # noqa: E402
from gate_run import (  # noqa: E402
    load_domains, word_interiors, word_legal, dfs_fallback,
)
from fast_legal import Store, word_legal_fast  # noqa: E402
from amplify193 import legal_against  # noqa: E402
from erdos193 import first_disqualifier  # noqa: E402
from imbricate193 import apply  # noqa: E402
from amplify_rich import M_BAL3  # noqa: E402

MAXDEPTH = 6
NB = 4_000_000


def exhaustive_iddfs(A, B, points, point_set, maxdepth, budget):
    """Deterministic exhaustive stitch search A -> B, all word lengths up to
    maxdepth. Returns (found_word_or_None, nodes, complete_up_to_depth)."""
    nodes = [0]
    complete = 0
    for depth_limit in range(2, maxdepth + 1):
        seg_pts, seg_word = [], []
        aborted = [False]

        def dfs(depth):
            nodes[0] += 1
            if nodes[0] > budget:
                aborted[0] = True
                return False
            last = seg_pts[-1] if seg_pts else A
            gap = max(abs(B[k] - last[k]) for k in range(3))
            if gap > depth * 2:
                return False
            for si in range(len(MENU)):
                s = MENU[si]
                p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
                if p == B:
                    if depth == 1:
                        seg_word.append(si)
                        return True
                    continue
                if depth > 1 and legal_against(
                        points + seg_pts, point_set | set(seg_pts), p):
                    seg_pts.append(p)
                    seg_word.append(si)
                    if dfs(depth - 1):
                        return True
                    seg_pts.pop()
                    seg_word.pop()
            return False

        if dfs(depth_limit):
            return seg_word, nodes[0], complete
        if aborted[0]:
            print(f"  depth {depth_limit}: BUDGET ABORT at {nodes[0]} nodes",
                  flush=True)
            return None, nodes[0], complete
        complete = depth_limit
        print(f"  depth {depth_limit}: exhausted, no stitch "
              f"({nodes[0]} cumulative nodes)", flush=True)
    return None, nodes[0], complete


def replay_to_segment(base_word, doms, d24, target_i, level=1):
    pts = [(0, 0, 0)]
    for si in base_word:
        s = MENU[si]
        p = pts[-1]
        pts.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    assert first_disqualifier(pts) is None, "base not triple-free"
    anchors = [apply(M_BAL3, p) for p in pts]
    store = Store(anchors)
    points = list(anchors)
    point_set = set(anchors)
    order = sorted(range(len(base_word)),
                   key=lambda i: (d24[base_word[i]], i))
    for i in order:
        si = base_word[i]
        A, B = anchors[i], anchors[i + 1]
        if i == target_i:
            return A, B, si, points, point_set, store, len(points)
        dom = doms[si]
        memo = {}
        chosen = None
        for w in dom:
            if word_legal_fast(A, w, store, memo, MENU):
                chosen = w
                break
        assert chosen is not None, f"unexpected jam at seg {i}"
        # cross-check the chosen word against the reference legality
        memo2 = {}
        assert word_legal(A, chosen, points, point_set, memo2), \
            f"impl divergence at seg {i}"
        ints = word_interiors(A, chosen)
        store.add_many(ints)
        points.extend(ints)
        point_set.update(ints)
    raise AssertionError("target segment not reached")


def main():
    t0 = time.time()
    doms, d24 = load_domains()
    print(f"domains loaded {time.time()-t0:.0f}s", flush=True)
    ultra = {k for k, v in d24.items() if v == 46}
    band = {k for k, v in d24.items() if 2000 <= v <= 16000}
    out = {}

    # ---- band72 jam ----
    bw = crafted_band(Random(72), 18, band, ultra, False)
    print(f"band72 base ({len(bw)} steps): {bw}", flush=True)
    A, B, si, points, point_set, store, npts = replay_to_segment(
        bw, doms, d24, target_i=9)
    print(f"jam state: seg i=9, step {si} {MENU[si]}, A={A}, B={B}, "
          f"{npts} points placed", flush=True)
    dom = doms[si]
    t = time.time()
    surv_ref = 0
    memo = {}
    for w in dom:
        if word_legal(A, w, points, point_set, memo):
            surv_ref += 1
    print(f"REFERENCE exhaustive scan: {surv_ref}/{len(dom)} survivors "
          f"({time.time()-t:.0f}s)", flush=True)
    surv_fast = 0
    memo = {}
    for w in dom:
        if word_legal_fast(A, w, store, memo, MENU):
            surv_fast += 1
    print(f"fast_legal exhaustive scan: {surv_fast}/{len(dom)} survivors",
          flush=True)
    out["jam"] = {
        "base_word": bw, "level": 1, "seg_i": 9, "step": list(MENU[si]),
        "step_idx": si, "d24": d24[si], "dstar": len(dom),
        "survivors_reference": surv_ref, "survivors_fast": surv_fast,
        "points_placed": npts, "A": list(A), "B": list(B),
    }

    # constructor's own last resort, both rng conventions
    for tag, rngkey in (("gate_run", "gate-L1-s9"), ("gate_l7", "gate-L1-dfs-9")):
        t = time.time()
        w = dfs_fallback(A, B, points, point_set, Random(rngkey), maxlen=8)
        print(f"dfs_fallback[{tag}] (maxlen 8, 200k nodes/depth): "
              f"{'FOUND ' + str(w) if w else 'NO STITCH'} "
              f"({time.time()-t:.0f}s)", flush=True)
        out["jam"][f"dfs_fallback_{tag}"] = w

    # exhaustive certification
    print(f"exhaustive ID-DFS to depth {MAXDEPTH}, budget {NB} nodes:",
          flush=True)
    w, nodes, complete = exhaustive_iddfs(A, B, points, point_set,
                                          MAXDEPTH, NB)
    out["jam"]["exhaustive"] = {"found": w, "nodes": nodes,
                                "complete_to_depth": complete}
    print(f"exhaustive result: found={w}, certified none up to length "
          f"{complete}, {nodes} nodes", flush=True)

    # ---- band71 near-jam (exact 2 survivors) reference check ----
    bw71 = crafted_band(Random(71), 18, band, ultra, False)
    st = None
    # find its worst L1 segment by exact reference scan of all its segments
    pts = [(0, 0, 0)]
    for s_i in bw71:
        s = MENU[s_i]
        p = pts[-1]
        pts.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    anchors = [apply(M_BAL3, p) for p in pts]
    points = list(anchors)
    point_set = set(anchors)
    order = sorted(range(len(bw71)), key=lambda i: (d24[bw71[i]], i))
    worst = None
    for i in order:
        s_i = bw71[i]
        A, B = anchors[i], anchors[i + 1]
        dom = doms[s_i]
        memo = {}
        surv = 0
        first = None
        for w_ in dom:
            if word_legal(A, w_, points, point_set, memo):
                if first is None:
                    first = w_
                surv += 1
        assert first is not None
        if worst is None or surv < worst[0]:
            worst = (surv, i, s_i, len(dom))
        ints = word_interiors(A, first)
        points.extend(ints)
        point_set.update(ints)
    out["band71_L1_worst_exact"] = {
        "survivors": worst[0], "seg_i": worst[1], "step_idx": worst[2],
        "step": list(MENU[worst[2]]), "dstar": worst[3], "base_word": bw71}
    print(f"band71 L1 worst (reference, exact over full domains): "
          f"{worst[0]} survivors at seg {worst[1]} step {MENU[worst[2]]} "
          f"of {worst[3]} words", flush=True)

    with open("design/attack1-certify.json", "w") as f:
        json.dump(out, f, indent=1)
    print("CERTIFY DONE", flush=True)
    print(json.dumps({k: (v if k != "jam" else {kk: vv for kk, vv in v.items()
                     if kk != "base_word"}) for k, v in out.items()},
                     default=str)[:1500], flush=True)


if __name__ == "__main__":
    main()
