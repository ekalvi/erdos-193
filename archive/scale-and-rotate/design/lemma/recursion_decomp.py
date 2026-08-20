"""
TASK A - EXACT RECURSION + stitch-time crowding decomposition verifier.

SET-LEVEL RECURSION (exact identity of point sets):
    Walk_{k+1}  =  (M . Walk_k)   \\sqcup   Stitch_k          (disjoint union)
where
    M . Walk_k = { M p : p in Walk_k }  =  the ANCHORS  (dilated-old points),
                 injective since det M = 27 != 0;
    Stitch_k   = \\bigsqcup_i interior(word_i)  =  the NEW refill points,
    interior(word_i) = the len(word_i)-1 lattice points a stitch visits strictly
                       between anchor_i and anchor_{i+1}.
The union is disjoint (the construction asserts set(chain) size = |anchors| + |interiors|).

CROWDING DECOMPOSITION.  The measured clearance c_R is the *stitch-time* tube
crowding: segments are placed in fragile-first order `order`, all anchors present
from the start (store = Store(anchors)), and when segment i is stitched the placed
set is
    P_i = anchors  \\cup  { interior(word_j) : pos(j) < pos(i) in `order` }.
For q = chord midpoint of segment i (floor-div midpoint of anchor_i, anchor_{i+1}),
    c_R(i) = #{ p in P_i : ||p-q||_inf <= R }
           = #{ a in anchors : ||a-q||_inf <= R }            <- DILATED-OLD (all)
           + #{ s in earlier stitches : ||s-q||_inf <= R }.  <- REFILL (stitch-time)
Both terms are computed here and summed; the sum must equal the measured c5/c10
EXACTLY (it is a true set identity if the crowding is stitch-time).

Usage:  pypy3 recursion_decomp.py <pkl> <clearance.json> <out.json>
"""
from __future__ import annotations
import json, pickle, sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from search193 import candidate_step_vectors

MENU = candidate_step_vectors(2)
CELL = 21  # > 2*R for R<=10: radius-R neighbours live in the 27-cell block


def word_interiors(start, word_idx):
    pts = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = MENU[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        pts.append((x, y, z))
    return pts


def add_grid(grid, p):
    grid.setdefault((p[0] // CELL, p[1] // CELL, p[2] // CELL), []).append(p)


def count_within(grid, q, R):
    qx, qy, qz = q
    cx, cy, cz = qx // CELL, qy // CELL, qz // CELL
    n = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                b = grid.get((cx + dx, cy + dy, cz + dz))
                if not b:
                    continue
                for (x, y, z) in b:
                    ax = x - qx if x >= qx else qx - x
                    if ax > R:
                        continue
                    ay = y - qy if y >= qy else qy - y
                    if ay > R:
                        continue
                    az = z - qz if z >= qz else qz - z
                    if az > R:
                        continue
                    n += 1
    return n


def main():
    pkl, cl_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    t0 = time.time()
    d = pickle.load(open(pkl, "rb"))
    anchors = [tuple(a) for a in d["anchors"]]
    words = d["words"]
    order = d["order"]
    parent_word = d["parent_word"]
    nseg = len(parent_word)

    # disjoint-union sanity: reconstruct full walk, confirm |walk| = |anchors|+|stitch|
    all_stitch = 0
    for i in range(nseg):
        all_stitch += len(words[i]) - 1
    assert all_stitch == sum(len(word_interiors(anchors[i], words[i])) for i in range(nseg))

    # static grid of ALL anchors = M . Walk_k  (present from stitch time 0)
    g_anch = {}
    for a in anchors:
        add_grid(g_anch, a)

    clearance = {r["i"]: r for r in json.load(open(cl_path))}
    has_c5 = "c5" in next(iter(clearance.values()))

    g_stitch = {}          # grows in fragile-first `order`
    rows = []
    mm10 = mm5 = 0
    for pos, i in enumerate(order):
        if i in clearance:
            A, B = anchors[i], anchors[i + 1]
            mid = ((A[0] + B[0]) // 2, (A[1] + B[1]) // 2, (A[2] + B[2]) // 2)
            old10 = count_within(g_anch, mid, 10)
            new10 = count_within(g_stitch, mid, 10)
            tot10 = old10 + new10
            meas10 = clearance[i]["c10"]
            row = {"i": i, "old10": old10, "new10": new10,
                   "tot10": tot10, "meas10": meas10}
            if tot10 != meas10:
                mm10 += 1
            if has_c5:
                old5 = count_within(g_anch, mid, 5)
                new5 = count_within(g_stitch, mid, 5)
                tot5 = old5 + new5
                meas5 = clearance[i]["c5"]
                row.update({"old5": old5, "new5": new5, "tot5": tot5, "meas5": meas5})
                if tot5 != meas5:
                    mm5 += 1
            rows.append(row)
        # place this segment's interiors AFTER measuring (stitch-time semantics)
        for p in word_interiors(anchors[i], words[i]):
            add_grid(g_stitch, p)

    n = len(rows)
    def stat(key):
        v = [x[key] for x in rows]
        return {"mean": round(sum(v) / n, 4), "max": max(v), "min": min(v)}

    summary = {
        "pkl": pkl, "clearance": cl_path, "n_checked": n,
        "anchors": len(anchors), "stitch_interiors_total": all_stitch,
        "mismatches_c10": mm10, "identity_c10_exact": mm10 == 0,
        "c10_total": stat("tot10"),
        "c10_dilated_old": stat("old10"),
        "c10_refill_new": stat("new10"),
        "c10_frac_dilated_old": round(stat("old10")["mean"] / stat("tot10")["mean"], 4),
        "c10_frac_refill": round(stat("new10")["mean"] / stat("tot10")["mean"], 4),
    }
    if has_c5:
        summary.update({
            "mismatches_c5": mm5, "identity_c5_exact": mm5 == 0,
            "c5_total": stat("tot5"),
            "c5_dilated_old": stat("old5"),
            "c5_refill_new": stat("new5"),
        })
    # show a few mismatches if any
    if mm10:
        summary["sample_c10_mismatches"] = [
            r for r in rows if r["tot10"] != r["meas10"]][:8]

    json.dump({"summary": summary, "rows_head": rows[:5]}, open(out_path, "w"), indent=2)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"[{time.time()-t0:.1f}s] DONE", flush=True)


if __name__ == "__main__":
    main()
