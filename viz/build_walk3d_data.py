#!/usr/bin/env python3
"""
Rebuild viz/walk3d-data.json with the gate walks: levels 0-4 unchanged
(original record run), levels 5-7 from gate-193-L{k}.txt (same recursion
lineage — gate L5 stitches the M-image of the same L4 walk — so the viewer's
enlarge-twist-stitch morph stays exact).

parents[j] = index of the parent-level point whose segment point j belongs to;
anchors are the first point of each value (the viewer marks anchors where the
value increases).

Run after a gate level verifies:  python3 viz/build_walk3d_data.py
"""
import json
import os
import sys
from ast import literal_eval
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from search193 import candidate_step_vectors  # noqa: E402

MENU = candidate_step_vectors(2)
ROOT = Path(__file__).parent.parent
OUT = Path(__file__).parent / "walk3d-data.json"

data = json.load(open(OUT))
M = data["M"]


def apply_M(p):
    return tuple(sum(M[r][c] * p[c] for c in range(3)) for r in range(3))


def build_level(parent_pts, word):
    anchors = [apply_M(tuple(p)) for p in parent_pts]
    aset = {a: i for i, a in enumerate(anchors)}
    pts = [anchors[0]]
    parents = [0]
    seg = 0
    pos = anchors[0]
    for si in word:
        s = MENU[si]
        pos = (pos[0] + s[0], pos[1] + s[1], pos[2] + s[2])
        if pos == anchors[seg + 1]:
            seg += 1
            parents.append(seg)
        else:
            parents.append(seg)
        pts.append(pos)
    assert seg == len(anchors) - 1, f"chain ended at anchor {seg}/{len(anchors)-1}"
    assert pts[-1] == anchors[-1]
    return pts, parents


levels = data["levels"][:5]
parent = [tuple(p) for p in levels[4]["points"]]
for k in (5, 6, 7):
    f = ROOT / f"{os.environ.get('WALK_PREFIX', 'gate')}-193-L{k}.txt"
    if not f.exists():
        print(f"level {k}: {f.name} not present yet — stopping here")
        break
    word = literal_eval(f.read_text())
    pts, parents = build_level(parent, word)
    levels.append({"points": [list(p) for p in pts], "parents": parents})
    print(f"level {k}: {len(pts)} points, {max(parents)+1} parent segments OK")
    parent = pts

data["levels"] = levels
json.dump(data, open(OUT, "w"))
print(f"wrote {OUT} with {len(levels)} levels "
      f"({sum(len(l['points']) for l in levels)} total points)")

# bump the fetch cache-buster so Cloudflare serves the new data
import re

html_path = Path(__file__).parent / "walk3d.html"
html = html_path.read_text()
new_html, n = re.subn(
    r"walk3d-data\.json\?v=(\d+)",
    lambda m: f"walk3d-data.json?v={int(m.group(1)) + 1}",
    html,
)
assert n == 1, "cache-buster fetch line not found in walk3d.html"
html_path.write_text(new_html)
print(f"bumped data cache-buster in walk3d.html")
