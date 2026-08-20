"""
ATTACK 1, wave 2 — target the observed choke point: non-fragile steps with
d24 in [2570, 16000] (no length-5 layer, stitched mid-order). Bases:
  A. band-only: every base step from the vulnerable band (compact greedy)
  B. alternator: ultra-fragile corner / band steps alternating, so corner
     segments (stitched FIRST) dump interiors at the band segments' anchors
  C. all-fragile length-20 (extends wave-1 worst family hug*-len16)
Reuses stitch_level / crafted_base machinery from attack1_seed.
"""
from __future__ import annotations

import json
import time
from random import Random

import sys
sys.path.insert(0, "/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193/design")

from attack1_seed import (  # noqa: E402  (does chdir)
    MENU, FRAGILE_CUT, NODES, TIME_CAP, NODE_CAP, run_seed, crafted_base,
)
from gate_run import load_domains  # noqa: E402
from amplify193 import legal_against  # noqa: E402
from erdos193 import first_disqualifier  # noqa: E402


def crafted_band(rng, length, band, ultra, alternate=False):
    """Compact greedy base preferring band steps (or alternating ultra/band)."""
    pts = [(0, 0, 0)]
    pset = {(0, 0, 0)}
    word = []
    relax = False
    while len(word) < length:
        want_ultra = alternate and (len(word) % 2 == 0)
        cands = []
        for si, s in enumerate(MENU):
            p = (pts[-1][0] + s[0], pts[-1][1] + s[1], pts[-1][2] + s[2])
            if not legal_against(pts, pset, p):
                continue
            if want_ultra:
                pref = 0 if si in ultra else (1 if si in band else 2)
            else:
                pref = 0 if si in band else (1 if si in ultra else 2)
            if not relax and pref == 2:
                continue
            norm = max(abs(p[0]), abs(p[1]), abs(p[2]))
            cands.append((pref, norm, rng.random(), si, p))
        if not cands:
            if not relax:
                relax = True
                continue
            break
        relax = False
        cands.sort()
        _, _, _, si, p = cands[0]
        pts.append(p)
        pset.add(p)
        word.append(si)
    return word


def main():
    t_load = time.time()
    doms, d24 = load_domains()
    print(f"domains loaded {time.time()-t_load:.0f}s", flush=True)
    fragile_set = {k for k, v in d24.items() if v < FRAGILE_CUT}
    ultra = {k for k, v in d24.items() if v == 46}
    band = {k for k, v in d24.items() if 2000 <= v <= 16000}
    print(f"band steps: {len(band)}", flush=True)

    seeds = []
    for s in (41, 42, 43, 44, 45):
        seeds.append((f"band{s}-len12",
                      crafted_band(Random(s), 12, band, ultra, False)))
    for s in (51, 52, 53, 54, 55):
        seeds.append((f"alt{s}-len12",
                      crafted_band(Random(s), 12, band, ultra, True)))
    for s in (61, 62, 63):
        seeds.append((f"hug{s}-len20",
                      crafted_base(Random(s), 20, False, fragile_set, ultra)))
    for s in (71, 72):
        seeds.append((f"band{s}-len18",
                      crafted_band(Random(s), 18, band, ultra, False)))
    for s in (81, 82):
        seeds.append((f"alt{s}-len18",
                      crafted_band(Random(s), 18, band, ultra, True)))

    t0 = time.time()
    results = []
    worst_recs = None
    for tag, bw in seeds:
        if time.time() - t0 > TIME_CAP or NODES[0] > NODE_CAP:
            print(f"BUDGET STOP before {tag}", flush=True)
            break
        nb = sum(1 for si in bw if si in band)
        print(f"seed {tag}: base {bw} (band {nb}/{len(bw)})", flush=True)
        summ, recs = run_seed(tag, bw, doms, d24, t0)
        summ["base_band"] = nb
        results.append(summ)
        if worst_recs is None or summ["min_frac"] <= min(
                r["min_frac"] for r in results):
            worst_recs = {"tag": summ["tag"], "recs": recs}
    results.sort(key=lambda r: r["min_frac"])
    with open("design/attack1-wave2-results.json", "w") as f:
        json.dump({"results": results, "nodes": NODES[0],
                   "elapsed_s": round(time.time() - t0),
                   "worst_seed_recs": worst_recs}, f, indent=1)
    print("\n==== WAVE2 RANKED (worst first) ====", flush=True)
    for r in results:
        print(f"{r['tag']}: min_frac {r['min_frac']:.3f} "
              f"min_avail {r['min_avail']:.0f} jam {r['jam'] is not None} "
              f"band {r.get('base_band')}/{r['base_len']}", flush=True)
    print(f"TOTAL nodes {NODES[0]/1e6:.1f}M, loop {time.time()-t0:.0f}s",
          flush=True)


if __name__ == "__main__":
    main()
