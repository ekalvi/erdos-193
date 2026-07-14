"""
ATTACK 1 — adversarial base-walk search against the REPAIRED construction.

Mirrors gate_l7.construct exactly: anchors = M_BAL3 * parent points, segments
stitched in ascending (|D_2-4(step)|, i) order (fragile-first), choice rule =
shortest-first scan of the length-sorted full word space (2000-cap +
escalation == full ordered scan, identical chosen word), word spaces =
connector_domains4 + dstar5_fragile for the 18 fragile steps, legality =
fast_legal.word_legal_fast (validated drop-in for amplify193.legal_against /
gate_run.word_legal).

Instrumentation per segment (at its exact stitch-time state):
  * exact scan collecting legal words until 10 found (or cap): if the FULL
    domain is exhausted with 0 survivors -> HARD JAM (the win condition);
    <10 survivors after full exhaustion -> exact near-jam count.
  * the gate's own 200-word sample survivor fraction (same RNG stream
    Random(f"gate-L{level}-s{i}")) -> frac, est_abs = frac * |D*|.

Budgets (hard constraints): single process, wall stop TIME_CAP seconds for
the seed loop, global node budget NODE_CAP word-legality checks, detector
scan cap per segment, full-scan escalation only when sample frac == 0.
Progress printed per seed per level.

Run:  cd ~/homelab/math193 && pypy3 -u design/attack1_seed.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
os.chdir("/Users/erik/homelab/math193")

from gate_run import load_domains, MENU, FRAGILE_CUT, word_interiors  # noqa: E402
from erdos193 import first_disqualifier  # noqa: E402
from imbricate193 import apply  # noqa: E402
from amplify_rich import M_BAL3  # noqa: E402
from amplify193 import find_base, legal_against  # noqa: E402
from fast_legal import Store, word_legal_fast  # noqa: E402

TIME_CAP = 500.0          # seconds for the whole seed loop (after load)
NODE_CAP = 60_000_000     # global word-legality-check budget
DETECT_EXTRA = 6000       # detector: extra words scanned after first survivor
FULLSCAN_CAP = 120_000    # hard cap on any exact full scan
SAMPLE_N = 200
LEVELS = (1, 2, 3)

NODES = [0]
ULTRA = None  # set later: the 4 d24=46 corner steps


def wcheck(A, w, store, memo):
    NODES[0] += 1
    return word_legal_fast(A, w, store, memo, MENU)


def stitch_level(parent_word, parent_pts, level, doms, d24):
    """One level of the repaired constructor with instrumentation.
    Returns (new_word, chain, recs, jam)."""
    anchors = [apply(M_BAL3, p) for p in parent_pts]
    store = Store(anchors)
    order = sorted(range(len(parent_word)),
                   key=lambda i: (d24[parent_word[i]], i))
    words = {}
    recs = []
    jam = None
    for done, i in enumerate(order):
        si = parent_word[i]
        A, B = anchors[i], anchors[i + 1]
        dom = doms[si]
        memo = {}
        # --- constructor scan + count-to-10 detector (exact, ordered) ---
        surv_idx = []
        scanned = 0
        for idx in range(len(dom)):
            scanned += 1
            if wcheck(A, dom[idx], store, memo):
                surv_idx.append(idx)
                if len(surv_idx) >= 10:
                    break
            if surv_idx and scanned - surv_idx[0] > DETECT_EXTRA:
                break  # first word found long ago; availability est by sample
            if not surv_idx and scanned >= FULLSCAN_CAP:
                break  # pathological; treated below
        exhausted = scanned >= len(dom)
        if not surv_idx:
            if exhausted:
                jam = {"level": level, "i": i, "step": si, "d24": d24[si],
                       "dstar": len(dom), "scanned": scanned,
                       "survivors": 0, "hard_jam": True}
                recs.append(jam)
                return None, None, recs, jam
            # cap hit with zero survivors so far — count rest exactly
            for idx in range(scanned, len(dom)):
                if wcheck(A, dom[idx], store, memo):
                    surv_idx.append(idx)
                    if len(surv_idx) >= 10:
                        break
            exhausted = True
            if not surv_idx:
                jam = {"level": level, "i": i, "step": si, "d24": d24[si],
                       "dstar": len(dom), "scanned": len(dom),
                       "survivors": 0, "hard_jam": True}
                recs.append(jam)
                return None, None, recs, jam
        chosen = dom[surv_idx[0]]
        exact_count = len(surv_idx) if (len(surv_idx) < 10 and exhausted) else None
        # --- gate's own sample statistic (same RNG contract) ---
        rng = Random(f"gate-L{level}-s{i}")
        sample = dom if len(dom) <= SAMPLE_N else rng.sample(dom, SAMPLE_N)
        surv = sum(1 for w in sample if wcheck(A, w, store, memo))
        frac = surv / len(sample)
        est_abs = frac * len(dom)
        # escalation: sample says ~0 but detector found >=10 quickly is fine;
        # sample==0 AND detector <10-but-capped -> exact full scan (rare)
        if surv == 0 and exact_count is None and len(surv_idx) < 10:
            cnt = len(surv_idx)
            for idx in range(scanned, min(len(dom), FULLSCAN_CAP)):
                if wcheck(A, dom[idx], store, memo):
                    cnt += 1
                    if cnt >= 10:
                        break
            if cnt < 10 and min(len(dom), FULLSCAN_CAP) == len(dom):
                exact_count = cnt
        avail = exact_count if exact_count is not None else max(len(surv_idx),
                                                                est_abs)
        recs.append({"level": level, "i": i, "step": si, "d24": d24[si],
                     "dstar": len(dom), "first_idx": surv_idx[0],
                     "n10": len(surv_idx), "exact": exact_count,
                     "frac": round(frac, 4), "est_abs": round(est_abs, 1),
                     "avail": round(avail, 1),
                     "fragile": d24[si] < FRAGILE_CUT, "len": len(chosen)})
        ints = word_interiors(A, chosen)
        end = ints[-1] if ints else A
        s = MENU[chosen[-1]]
        assert (end[0] + s[0], end[1] + s[1], end[2] + s[2]) == B
        store.add_many(ints)
        words[i] = chosen
    chain = [anchors[0]]
    new_word = []
    for i in range(len(parent_word)):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i + 1])
        new_word.extend(words[i])
    assert set(chain) == store.pset
    return new_word, chain, recs, None


def crafted_base(rng, length, only_fragile=False, fragile_set=(), ultra=()):
    """Compact fragile-heavy crowd-hugging base: greedily prefer ultra-fragile
    corner steps, then fragile, then any; among those minimize Chebyshev norm
    of the new point (hug the origin); random tie-break."""
    pts = [(0, 0, 0)]
    pset = {(0, 0, 0)}
    word = []
    for _ in range(length):
        cands = []
        for si, s in enumerate(MENU):
            p = (pts[-1][0] + s[0], pts[-1][1] + s[1], pts[-1][2] + s[2])
            if not legal_against(pts, pset, p):
                continue
            pref = 0 if si in ultra else (1 if si in fragile_set else 2)
            if only_fragile and pref == 2:
                continue
            norm = max(abs(p[0]), abs(p[1]), abs(p[2]))
            cands.append((pref, norm, rng.random(), si, p))
        if not cands:
            if only_fragile:
                only_fragile = False  # fall back once stuck
                continue
            break
        cands.sort()
        _, _, _, si, p = cands[0]
        pts.append(p)
        pset.add(p)
        word.append(si)
    return word


def run_seed(tag, base_word, doms, d24, t0):
    pts = [(0, 0, 0)]
    for si in base_word:
        s = MENU[si]
        p = pts[-1]
        pts.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    assert first_disqualifier(pts) is None, f"{tag}: base not triple-free"
    word = list(base_word)
    n_frag = sum(1 for si in word if d24[si] < FRAGILE_CUT)
    summary = {"tag": tag, "base_len": len(word), "base_fragile": n_frag,
               "levels": {}, "jam": None,
               "min_frac": 1.0, "min_avail": float("inf")}
    for level in LEVELS:
        new_word, chain, recs, jam = stitch_level(word, pts, level, doms, d24)
        fr = [r["frac"] for r in recs if "frac" in r]
        av = [r["avail"] for r in recs if "avail" in r]
        lvl = {"segs": len(recs)}
        if fr:
            lvl["min_frac"] = min(fr)
            lvl["min_avail"] = min(av)
            summary["min_frac"] = min(summary["min_frac"], min(fr))
            summary["min_avail"] = min(summary["min_avail"], min(av))
        summary["levels"][level] = lvl
        worst = min((r for r in recs if "frac" in r),
                    key=lambda r: r["frac"], default=None)
        print(f"  {tag} L{level}: {len(recs)} segs, "
              f"min_frac {lvl.get('min_frac')}, min_avail {lvl.get('min_avail')}, "
              f"worst {worst and {k: worst[k] for k in ('i','step','d24','frac','n10','first_idx')}}, "
              f"nodes {NODES[0]/1e6:.1f}M, {time.time()-t0:.0f}s", flush=True)
        if jam is not None:
            summary["jam"] = jam
            print(f"  {tag} L{level}: *** HARD JAM *** {jam}", flush=True)
            return summary, recs
        word, pts = new_word, chain
        if NODES[0] > NODE_CAP or time.time() - t0 > TIME_CAP:
            summary["aborted"] = f"budget at L{level}"
            break
    return summary, recs


def main():
    t_load = time.time()
    doms, d24 = load_domains()
    print(f"domains loaded {time.time()-t_load:.0f}s", flush=True)
    fragile_set = {k for k, v in d24.items() if v < FRAGILE_CUT}
    ultra = {k for k, v in d24.items() if v == 46}

    seeds = []
    for s in (777, 193, 1, 2, 3, 4, 5, 6, 7, 8):
        seeds.append((f"fb{s}-len12", find_base(MENU, Random(s), length=12,
                                                tries=60)))
    for s in (101, 102, 103, 104):
        seeds.append((f"fb{s}-len6", find_base(MENU, Random(s), length=6,
                                               tries=60)))
    for s in (11, 12, 13, 14, 15, 16):
        seeds.append((f"hug{s}-len10",
                      crafted_base(Random(s), 10, False, fragile_set, ultra)))
    for s in (21, 22, 23, 24):
        seeds.append((f"hugF{s}-len10",
                      crafted_base(Random(s), 10, True, fragile_set, ultra)))
    for s in (31, 32):
        seeds.append((f"hug{s}-len16",
                      crafted_base(Random(s), 16, False, fragile_set, ultra)))

    t0 = time.time()
    results = []
    worst_recs = None
    for tag, bw in seeds:
        if time.time() - t0 > TIME_CAP or NODES[0] > NODE_CAP:
            print(f"BUDGET STOP before {tag} "
                  f"({time.time()-t0:.0f}s, {NODES[0]/1e6:.1f}M nodes)",
                  flush=True)
            break
        print(f"seed {tag}: base {bw}", flush=True)
        summ, recs = run_seed(tag, bw, doms, d24, t0)
        results.append(summ)
        if worst_recs is None or summ["min_frac"] <= min(
                r["min_frac"] for r in results):
            worst_recs = {"tag": summ["tag"], "recs": recs}
    results.sort(key=lambda r: r["min_frac"])
    with open("design/attack1-results.json", "w") as f:
        json.dump({"results": results, "nodes": NODES[0],
                   "elapsed_s": round(time.time() - t0),
                   "worst_seed_last_level_recs": worst_recs}, f, indent=1)
    print("\n==== RANKED (worst first) ====", flush=True)
    for r in results:
        print(f"{r['tag']}: min_frac {r['min_frac']:.3f} "
              f"min_avail {r['min_avail']:.0f} jam {r['jam'] is not None} "
              f"base_fragile {r['base_fragile']}/{r['base_len']} "
              f"{'ABORT ' + r['aborted'] if r.get('aborted') else ''}",
              flush=True)
    print(f"TOTAL nodes {NODES[0]/1e6:.1f}M, attack loop "
          f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
