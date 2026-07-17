"""Worst-case covering multiplicity over seeds, in three regimes:
  base        -- prongA route="short" (design routing, minimal lambda)
  shortcrowd  -- adversarial max-crowding router at MATCHED lambda (shortest-
                 first, crowd-ordered) => isolates pure routing at design density
  fold-sK     -- adversarial router allowed K extra fold-steps per stitch
                 => walks the wider legal menu-closure (higher lambda / d)

Reports, per regime, the max mult_g(3^g) over all (seed, g) and where it occurs,
plus the lambda/d range spanned.  Writes design/osc/results_adv/worstcase_L{L}.json.

Usage: adv_worstcase.py LEVEL SEEDS_CSV FOLD_SLACKS_CSV
"""
import sys, os, json, time
from design.osc.adversarial_multiplicity import measure_seed_adv
from design.osc.prongA_multiplicity import measure_seed

OUT = "/Users/erik/homelab/math193/design/osc/results_adv"
os.makedirs(OUT, exist_ok=True)

L = int(sys.argv[1]) if len(sys.argv) > 1 else 3
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [193, 1, 2, 7, 42, 100, 271, 555]
folds = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2]


def mult3(r):
    return [r["gens"][i]["mult_at_3^g"] for i in (1, 2, 3)]


regimes = {}


def record(name, seed, r):
    if not r.get("ok"):
        print(f"  {name} seed{seed}: FAILED L{r['reached_level']}", flush=True)
        return
    m = mult3(r); mx = max(m); g = 1 + m.index(mx)
    d = regimes.setdefault(name, {"max": 0, "where": None, "lams": [], "rows": []})
    d["lams"].append(r["lambda"])
    d["rows"].append({"seed": seed, "mult": m, "lambda": r["lambda"], "d": r["d"], "N": r["N"]})
    if mx > d["max"]:
        d["max"] = mx; d["where"] = {"seed": seed, "gen": g, "mult": m, "lambda": r["lambda"], "d": r["d"]}
    print(f"  {name} seed{seed}: mult={m} lam={r['lambda']} d={r['d']} N={r['N']}", flush=True)


for s in seeds:
    t = time.time()
    record("base", s, measure_seed(s, top_level=L, depth=3, route="short"))
    record("shortcrowd", s, measure_seed_adv(s, top_level=L, depth=3, crowd_radius=3, slack=0, prefer_short=True))
    for k in folds:
        record(f"fold-s{k}", s, measure_seed_adv(s, top_level=L, depth=3, crowd_radius=3, slack=k))
    print(f"  (seed {s} done, {round(time.time()-t,1)}s)", flush=True)

print("\n=== WORST-CASE mult_g(3^g) per regime (level {}) ===".format(L))
summary = {}
for name, d in regimes.items():
    lo, hi = min(d["lams"]), max(d["lams"])
    print(f"  {name:12s}: MAX mult = {d['max']}  lam in [{lo},{hi}]  at {d['where']}")
    summary[name] = {"max_mult": d["max"], "lam_range": [lo, hi], "where": d["where"], "rows": d["rows"]}
allmax = max(d["max"] for d in regimes.values())
matched_max = max(regimes["base"]["max"], regimes.get("shortcrowd", {"max": 0})["max"])
print(f"\n  OVERALL MAX (any regime) = {allmax}  (breaks cap 5: {allmax > 5})")
print(f"  MATCHED-DENSITY MAX (base + shortcrowd, lam~design) = {matched_max}")
json.dump({"level": L, "seeds": seeds, "overall_max": allmax, "matched_density_max": matched_max,
           "regimes": summary}, open(f"{OUT}/worstcase_L{L}.json", "w"), indent=2)
print(f"wrote {OUT}/worstcase_L{L}.json")
