"""Run PRONG A multiplicity measurement for ONE seed; write JSON to a file.
Usage: runner_one.py SEED BASE_LEN ROUTE OUTFILE [TOP_LEVEL]"""
import sys, json
from prongA_multiplicity import measure_seed

seed = int(sys.argv[1]); base_len = int(sys.argv[2]); route = sys.argv[3]
outfile = sys.argv[4]; top_level = int(sys.argv[5]) if len(sys.argv) > 5 else 5
res = measure_seed(seed, top_level=top_level, depth=3, base_len=base_len, route=route)
with open(outfile, "w") as f:
    json.dump(res, f)
print("WROTE", outfile, json.dumps(res), flush=True)
