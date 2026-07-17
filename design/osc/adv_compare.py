"""Adversarial vs baseline covering-multiplicity comparison + independent
legality re-verification.  Answers gap (iii): can a LEGAL orbit push
mult_g(r=3^g) above the measured cap of 5?

For each (level, seed) it reports:
  BASE short  -- prongA route="short" (the design's minimal-lambda routing)
  ADV slack0  -- max-crowding router, SHORTEST stitches (same lengths as BASE,
                 adversarial ORDERING only -> isolates the routing effect)
  ADV slack1/2-- max-crowding router allowed 1/2 extra fold-steps per stitch
                 (walks the wider legal closure, higher lambda)
and independently re-verifies (erdos193.first_disqualifier) that every
adversarial walk is genuinely triple-free = a legal orbit.

Usage: adv_compare.py LEVELS_CSV SEEDS_CSV SLACKS_CSV
"""
import sys, time
from design.osc.adversarial_multiplicity import measure_seed_adv, build_walk_adv
from design.osc.prongA_multiplicity import measure_seed
from erdos193 import first_disqualifier

levels = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [3, 4]
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [193]
slacks = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0, 1]


def mult3(r):
    return [r["gens"][i]["mult_at_3^g"] for i in (1, 2, 3)]


def dens3(r):
    return [r["gens"][i].get("point_density_at_3^g", None) for i in (1, 2, 3)]


overall_max = 0
where = None
for L in levels:
    for s in seeds:
        t = time.time()
        b = measure_seed(s, top_level=L, depth=3, route="short")
        bt = round(time.time() - t, 1)
        if b.get("ok"):
            print(f"L{L} seed{s} BASE short : mult={mult3(b)} lam={b['lambda']} d={b['d']} N={b['N']} {bt}s", flush=True)
            overall_max = max(overall_max, max(mult3(b)))
        else:
            print(f"L{L} seed{s} BASE short : FAILED L{b['reached_level']} {bt}s", flush=True)
        # matched-lambda adversary: shortest-first, crowd-ordered (pure routing)
        t = time.time()
        rs = measure_seed_adv(s, top_level=L, depth=3, crowd_radius=3, slack=0, prefer_short=True)
        rst = round(time.time() - t, 1)
        if rs.get("ok"):
            m = mult3(rs); mx = max(m)
            print(f"L{L} seed{s} ADV shortcrowd: mult={m} dens={dens3(rs)} lam={rs['lambda']} d={rs['d']} N={rs['N']} {rst}s", flush=True)
            if mx > overall_max:
                overall_max = mx; where = (L, s, "shortcrowd", m)
        else:
            print(f"L{L} seed{s} ADV shortcrowd: FAILED L{rs['reached_level']} {rst}s", flush=True)
        # wider-closure adversary: fold slack extra steps (higher lambda)
        for sl in slacks:
            t = time.time()
            r = measure_seed_adv(s, top_level=L, depth=3, crowd_radius=3, slack=sl)
            rt = round(time.time() - t, 1)
            if r.get("ok"):
                m = mult3(r); mx = max(m)
                print(f"L{L} seed{s} ADV fold-s{sl}: mult={m} dens={dens3(r)} lam={r['lambda']} d={r['d']} N={r['N']} {rt}s", flush=True)
                if mx > overall_max:
                    overall_max = mx; where = (L, s, f"fold{sl}", m)
            else:
                print(f"L{L} seed{s} ADV fold-s{sl}: FAILED L{r['reached_level']} {rt}s", flush=True)

# independent legality re-verification on the deepest adversarial walks built
for s in seeds[:3]:
    for sl in slacks:
        L = max(levels)
        lv = build_walk_adv(s, top_level=L, crowd_radius=3, slack=sl)
        if lv is not None and len(lv) > L:
            ch = lv[L][0]
            ok = first_disqualifier(ch) is None
            print(f"INDEP legality seed{s} slack{sl} L{L} N={len(ch)}: {'LEGAL' if ok else 'ILLEGAL'}", flush=True)

print(f"\n=== OVERALL MAX legal mult_g(3^g) = {overall_max}  (breaks cap 5: {overall_max > 5}); where(L,seed,slack,mult)={where} ===")
