import json
from random import Random
import gen2d
from gen2d_main import build

CONFIGS = [
    # (base_len, menu_radius, matrix, seg_maxlen, tries)
    (3, 2, ((5, -1), (1, 5)), 16, 80),
    (3, 3, ((4, -1), (1, 4)), 14, 80),
    (4, 3, ((4, -1), (1, 4)), 14, 80),
    (3, 3, ((5, -1), (1, 5)), 16, 80),
]

for base_len, radius, M, maxlen, tries in CONFIGS:
    gen2d.M = M
    gen2d.MENU = [(x, y) for x in range(-radius, radius + 1)
                  for y in range(-radius, radius + 1) if (x, y) != (0, 0)]
    gen2d.find_base.__defaults__ = (base_len, 3000)
    gen2d.amplify.__defaults__ = (maxlen, tries)
    print(f"=== base={base_len} radius={radius} M={M[0]} maxlen={maxlen}", flush=True)
    for seed in (7, 11, 42, 99):
        levels = build(seed)
        print(f"  seed {seed}: {[len(l['points']) for l in levels]}", flush=True)
        if len(levels) >= 3:
            with open("viz2d-data.json", "w") as f:
                json.dump({"matrix": M, "levels": levels}, f)
            print("SUCCESS — wrote viz2d-data.json", flush=True)
            raise SystemExit
print("no config succeeded", flush=True)
