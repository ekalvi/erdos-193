"""Seed-sweeping driver for the 2D demo data (imports the machinery from gen2d)."""
import json
from random import Random

from gen2d import M, amplify, find_base


def build(seed):
    rng = Random(seed)
    base = find_base(rng)
    if base is None:
        return []
    levels = [{"points": base, "anchors": list(range(len(base))), "segments": []}]
    pts = base
    for lv in range(1, 3):
        result = amplify(pts, rng)
        if result is None:
            print(f"  level {lv} failed")
            break
        placed, anchors, segments = result
        anchor_set = set(anchors)
        levels.append(
            {
                "points": placed,
                "anchors": [i for i, p in enumerate(placed) if p in anchor_set],
                "segments": segments,
            }
        )
        pts = placed
        print(f"  level {lv}: {len(placed)} points, verified")
    return levels


if __name__ == "__main__":
    for seed in (7, 11, 42, 99, 5, 27, 193, 61):
        print(f"--- seed {seed}")
        levels = build(seed)
        if len(levels) >= 3:
            with open("viz2d-data.json", "w") as f:
                json.dump({"matrix": M, "levels": levels}, f)
            print(f"SUCCESS seed {seed}: sizes {[len(l['points']) for l in levels]}")
            break
    else:
        print("no seed succeeded")
