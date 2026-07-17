"""Adversarial worst-case sweep: run the max-crowding router (route="crowd")
over several seeds x (crowd_radius, slack) settings, write one JSON per config
to design/osc/results_adv/, and report the maximum legal covering multiplicity
mult_g(r=3^g) produced -- the empirical stress test of the cap-of-5.

Usage: adv_sweep.py TOP_LEVEL SEEDS_CSV
"""
import sys, os, json, time
from design.osc.adversarial_multiplicity import measure_seed_adv

OUT = "/Users/erik/homelab/math193/design/osc/results_adv"
os.makedirs(OUT, exist_ok=True)

top_level = int(sys.argv[1]) if len(sys.argv) > 1 else 5
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [193, 1, 2, 7, 42, 100, 271, 555]
# (crowd_radius, slack) adversary settings
configs = [(3, 0), (3, 1), (6, 1), (9, 2)]

overall_max = 0
overall_max_where = None
allres = []
for cr, sl in configs:
    for s in seeds:
        t = time.time()
        r = measure_seed_adv(s, top_level=top_level, depth=3, crowd_radius=cr,
                             slack=sl, verbose=False)
        r["secs"] = round(time.time() - t, 1)
        fn = f"{OUT}/adv_seed{s}_cr{cr}_sl{sl}_L{top_level}.json"
        json.dump(r, open(fn, "w"))
        allres.append(r)
        if r.get("ok"):
            mx = max(gd["mult_at_3^g"] for gd in r["gens"].values())
            mxg = max(int(g) for g, gd in r["gens"].items() if gd["mult_at_3^g"] == mx)
            if mx > overall_max:
                overall_max = mx
                overall_max_where = (s, cr, sl, mxg)
            print(f"seed {s} cr{cr} sl{sl}: N={r['N']} lam={r['lambda']} "
                  f"mult={[r['gens'][str(g)]['mult_at_3^g'] for g in (1,2,3)]} "
                  f"dens={[r['gens'][str(g)]['point_density_at_3^g'] for g in (1,2,3)]} "
                  f"({r['secs']}s)", flush=True)
        else:
            print(f"seed {s} cr{cr} sl{sl}: FAILED reached L{r['reached_level']} ({r['secs']}s)", flush=True)

print(f"\n=== OVERALL MAX legal mult_g(3^g) = {overall_max} "
      f"(seed,cr,slack,gen={overall_max_where}); cap under test = 5 ===")
json.dump({"overall_max_mult": overall_max, "where": overall_max_where,
           "top_level": top_level, "configs": configs, "seeds": seeds,
           "results": allres},
          open(f"{OUT}/SUMMARY_L{top_level}.json", "w"), indent=2)
print(f"wrote {OUT}/SUMMARY_L{top_level}.json")
