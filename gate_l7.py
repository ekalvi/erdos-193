"""
gate_l7.py — gate level with POST-HOC PARALLEL ledger evaluation.

The inline gate (gate_run.py) evaluates each segment's word-space ledger at
stitch time, single-threaded: cost ~ (segments x points) makes level 7 a
~10 h serial job. But the ledger is a pure FUNCTION of the stitch-time state,
and the construction is deterministic — so we can (A) construct the level
recording only the walk, then (B) replay the state evolution in N parallel
workers, each evaluating a shard of the recorded segments at their exact
stitch-time states. Same numbers, ~N x faster.

Determinism contract with gate_run.py: same domain order (length-sorted),
same choice rule (shortest-first scan, 2000-word cap, full-space escalation),
same per-segment sample seed Random(f"gate-L{level}-s{i}") — so a shard
worker reproduces exactly the sample the inline gate would have drawn.

Usage:
  pypy3 -u gate_l7.py all 6              # construct L7, 6 shard workers, merge
  pypy3 -u gate_l7.py all 4 --level 5    # dry-run validation against inline L5
  (or construct / shard K N / merge N individually, with --level)
"""
from __future__ import annotations

import json
import pickle
import subprocess
import sys
import time
from ast import literal_eval
from random import Random

from erdos193 import first_disqualifier
from imbricate193 import apply
from amplify_rich import M_BAL3
from gate_run import (
    DELTA, FRAGILE_CUT, L7_RECORD_STRIDE, MENU, SAMPLE_N,
    dfs_fallback, ks_stat, load_domains, load_level4_word, n_of_d,
    word_interiors, word_legal,
)


def get_parent(level):
    w4, p4 = load_level4_word()
    if level == 5:
        return w4, p4
    word = literal_eval(open(f"gate-193-L{level-1}.txt").read())
    start = p4[0]
    for _ in range(level - 1 - 4):
        start = apply(M_BAL3, start)
    pts = [start]
    for si in word:
        s = MENU[si]
        p = pts[-1]
        pts.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    assert len(set(pts)) == len(pts)
    return word, pts


def state_pkl(level):
    return f"gate-l7-construction-L{level}.pkl"


def construct(level, doms, d24_size):
    t0 = time.time()
    parent_word, parent_pts = get_parent(level)
    anchors = [apply(M_BAL3, p) for p in parent_pts]
    points = list(anchors)
    point_set = set(anchors)
    assert len(point_set) == len(anchors)
    order = sorted(range(len(parent_word)), key=lambda i: (d24_size[parent_word[i]], i))
    words = {}
    n_esc = n_jam = 0

    for done, i in enumerate(order):
        si = parent_word[i]
        A, B = anchors[i], anchors[i + 1]
        dom = doms[si]
        memo = {}
        chosen = None
        for w in dom[:2000]:
            if word_legal(A, w, points, point_set, memo):
                chosen = w
                break
        if chosen is None:
            n_esc += 1
            for w in dom[2000:]:
                if word_legal(A, w, points, point_set, memo):
                    chosen = w
                    break
        if chosen is None:
            n_jam += 1
            seg_word = dfs_fallback(A, B, points, point_set,
                                    Random(f"gate-L{level}-dfs-{i}"))
            if seg_word is None:
                print(f"L{level} seg {i}: HARD JAM — GATE FAILS", flush=True)
                with open(f"gate-l7-jam-L{level}.json", "w") as f:
                    json.dump({"i": i, "done": done}, f)
                return False
            chosen = tuple(seg_word)
        ints = word_interiors(A, chosen)
        end = ints[-1] if ints else A
        s = MENU[chosen[-1]]
        assert (end[0] + s[0], end[1] + s[1], end[2] + s[2]) == B
        points.extend(ints)
        point_set.update(ints)
        words[i] = tuple(chosen)
        if done % 1000 == 999:
            print(f"L{level} construct: {done+1}/{len(order)} segs, "
                  f"{time.time()-t0:.0f}s, esc {n_esc} jam {n_jam}", flush=True)

    chain = [anchors[0]]
    new_word = []
    anchors_idx = [0]
    for i in range(len(parent_word)):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i + 1])
        new_word.extend(words[i])
        anchors_idx.append(len(chain) - 1)
    assert set(chain) == point_set
    print(f"L{level}: verifying {len(chain)} points ...", flush=True)
    bad = first_disqualifier(chain)
    assert bad is None, f"L{level} VERIFY FAILED: {bad}"
    print(f"L{level}: VERIFIED triple-free ({time.time()-t0:.0f}s)", flush=True)

    stats, n81 = n_of_d(chain, anchors_idx)
    with open(state_pkl(level), "wb") as f:
        pickle.dump({"parent_word": parent_word, "order": order,
                     "words": words, "anchors": anchors}, f)
    with open(f"gate-193-L{level}.txt", "w") as f:
        f.write(repr(new_word))
    with open(f"gate-stats-L{level}.json", "w") as f:
        json.dump({"summary": {"level": level, "steps": len(new_word),
                               "points": len(chain), "escalations": n_esc,
                               "jams": n_jam, "stats": stats,
                               "construct_s": round(time.time() - t0)},
                   "n81_interior": n81}, f)
    print(f"L{level} construct done: {len(new_word)} steps, stats {stats}",
          flush=True)
    return True


def recorded_positions(level, st, d24_size):
    """Which (position-in-order, segment) pairs get a ledger record — must
    mirror gate_run.run_level exactly."""
    record_all = level < 7
    out = []
    for pos, i in enumerate(st["order"]):
        fragile = d24_size[st["parent_word"][i]] < FRAGILE_CUT
        if record_all or fragile or (pos % L7_RECORD_STRIDE == 0):
            out.append((pos, i))
    return out


def shard(level, k, n, doms, d24_size):
    t0 = time.time()
    st = pickle.load(open(state_pkl(level), "rb"))
    recs = {pos for pos, _ in recorded_positions(level, st, d24_size)}
    points = list(st["anchors"])
    point_set = set(points)
    out = []
    for pos, i in enumerate(st["order"]):
        si = st["parent_word"][i]
        if pos in recs and pos % n == k:
            dom = doms[si]
            rng = Random(f"gate-L{level}-s{i}")
            sample = dom if len(dom) <= SAMPLE_N else rng.sample(dom, SAMPLE_N)
            memo = {}
            A = st["anchors"][i]
            surv = sum(1 for w in sample
                       if word_legal(A, w, points, point_set, memo))
            frac = surv / len(sample)
            out.append({"i": i, "pos": pos, "step": si, "d24": d24_size[si],
                        "dstar": len(dom), "n": len(sample), "surv": surv,
                        "frac": round(frac, 4),
                        "surv_abs": round(frac * len(dom)),
                        "fragile": d24_size[si] < FRAGILE_CUT})
        ints = word_interiors(st["anchors"][i], st["words"][i])
        points.extend(ints)
        point_set.update(ints)
        if pos % 5000 == 4999:
            print(f"shard {k}/{n}: pos {pos+1}, {len(out)} recs, "
                  f"{time.time()-t0:.0f}s", flush=True)
    with open(f"gate-ledger-L{level}-shard{k}.json", "w") as f:
        json.dump(out, f)
    print(f"shard {k}/{n} done: {len(out)} records, {time.time()-t0:.0f}s",
          flush=True)


def merge(level, n):
    ledger = []
    for k in range(n):
        ledger.extend(json.load(open(f"gate-ledger-L{level}-shard{k}.json")))
    ledger.sort(key=lambda r: r["pos"])
    with open(f"gate-ledger-L{level}.json", "w") as f:
        json.dump(ledger, f)
    fr = [r["frac"] for r in ledger]
    stats_file = f"gate-stats-L{level}.json"
    js = json.load(open(stats_file))
    js["summary"].update({
        "recorded": len(ledger), "min_frac": min(fr),
        "mean_frac": sum(fr) / len(fr),
        "p01_frac": sorted(fr)[max(0, len(fr) // 100 - 1)],
        "below_delta": sum(1 for f_ in fr if f_ < DELTA),
        "min_surv_abs": min(r["surv_abs"] for r in ledger),
    })
    with open(stats_file, "w") as f:
        json.dump(js, f)
    print(f"L{level} MERGED SUMMARY: {json.dumps(js['summary'])}", flush=True)
    prev = f"gate-stats-L{level-1}.json"
    try:
        a = json.load(open(prev))["n81_interior"]
        b = js["n81_interior"]
        ks, crit = ks_stat(a, b)
        print(f"KS(L{level-1},L{level}) on N81: {ks:.4f} vs critical "
              f"{crit:.4f} ({'BELOW — fixed point' if ks < crit else 'ABOVE — drift'})",
              flush=True)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    mode = sys.argv[1]
    level = int(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else 7
    doms, d24_size = load_domains()
    if mode == "construct":
        construct(level, doms, d24_size)
    elif mode == "shard":
        shard(level, int(sys.argv[2]), int(sys.argv[3]), doms, d24_size)
    elif mode == "merge":
        merge(level, int(sys.argv[2]))
    elif mode == "all":
        n = int(sys.argv[2])
        if not construct(level, doms, d24_size):
            sys.exit(1)
        procs = [subprocess.Popen(
            [sys.executable, "-u", __file__, "shard", str(k), str(n),
             "--level", str(level)])
            for k in range(n)]
        assert all(p.wait() == 0 for p in procs)
        merge(level, n)
        print("GATE LEVEL COMPLETE", flush=True)
