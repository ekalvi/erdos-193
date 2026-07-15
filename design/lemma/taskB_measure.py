"""
TASK B — measurement component. Measure the REFILL BOUND on the v2 orbit.

For each level in {5,6,7}: rebuild the level-(k+1) walk from
gate2-l7-construction-L{k+1}.pkl as anchors interleaved with stitch-word
interiors; tag each point anchor vs interior; then via an integer spatial-hash
grid compute EXACTLY:

  B_meas (=P10) = max over ALL walk points p of #{interior q : |q-p|_inf <= 10}
       -> the largest number of NEW stitch points in any Cheb-10 box whose
          centre is a walk point (the box that matters: it must contain a walk
          point to be relevant to crowding).
  C20   = max over interiors q of #{interior q' : |q-q'|_inf <= 20}
       -> RIGOROUS upper bound on the true max-over-all-centres box count:
          any radius-10 box's interiors are pairwise within Cheb 20, so lie in
          the Cheb-20 neighbourhood of any one of them. Hence
                 P10 <= B_true(all centres) <= C20.
  A14   = max over ALL walk points p of #{anchor a : |a-p|_inf <= 14}
       -> feeds the proven cap  B <= 4 * A14.

Usage:  pypy3 taskB_measure.py 5      (or 6, 7)  -> JSON to stdout
Light: single process, grid keeps it ~O(N * local).
"""
import json
import pickle
import sys

MENU = [(x, y, z)
        for x in range(-2, 3) for y in range(-2, 3) for z in range(-2, 3)
        if (x, y, z) != (0, 0, 0)]


def word_interiors(start, word_idx):
    pts = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = MENU[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        pts.append((x, y, z))
    return pts


def build_chain(level):
    d = pickle.load(open(f"gate2-l7-construction-L{level}.pkl", "rb"))
    anchors = d["anchors"]
    words = d["words"]
    parent_word = d["parent_word"]
    chain = [anchors[0]]
    is_int = [0]  # anchors[0] is an anchor
    for i in range(len(parent_word)):
        w = words[i]
        for q in word_interiors(anchors[i], w):
            chain.append(q)
            is_int.append(1)
        chain.append(anchors[i + 1])
        is_int.append(0)
    return chain, is_int


def grid_of(points, cell):
    g = {}
    inv = 1  # integer floor division by cell
    for p in points:
        key = (p[0] // cell, p[1] // cell, p[2] // cell)
        g.setdefault(key, []).append(p)
    return g


NEI = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]


def max_count_around(centers, targets, radius):
    """max over centers c of #{t in targets : |t-c|_inf <= radius}.
    grid cell = radius so any t within radius is in center's cell or an
    adjacent cell (coord diff <= radius => floor-index diff in {-1,0,1})."""
    cell = radius if radius > 0 else 1
    g = grid_of(targets, cell)
    best = 0
    best_center = None
    for c in centers:
        cx, cy, cz = c[0] // cell, c[1] // cell, c[2] // cell
        cnt = 0
        for dx, dy, dz in NEI:
            bucket = g.get((cx + dx, cy + dy, cz + dz))
            if not bucket:
                continue
            for t in bucket:
                if (abs(t[0] - c[0]) <= radius and abs(t[1] - c[1]) <= radius
                        and abs(t[2] - c[2]) <= radius):
                    cnt += 1
        if cnt > best:
            best = cnt
            best_center = c
    return best, best_center


def main():
    level = int(sys.argv[1])
    chain, is_int = build_chain(level)
    interiors = [p for p, f in zip(chain, is_int) if f]
    anchors = [p for p, f in zip(chain, is_int) if not f]
    n = len(chain)

    # B_meas = P10: interiors within Cheb 10 of any walk point
    P10, c1 = max_count_around(chain, interiors, 10)
    # C20 upper bound on true max box: interiors within Cheb 20 of any interior
    C20, _ = max_count_around(interiors, interiors, 20)
    # A14: anchors within Cheb 14 of any walk point (for cap 4*A14)
    A14, _ = max_count_around(chain, anchors, 14)
    # extra: total walk-point crowding within Cheb 10 (compare to reported c10)
    C10all, _ = max_count_around(chain, chain, 10)

    out = {
        "level": level,
        "walk_points": n,
        "interiors": len(interiors),
        "anchors": len(anchors),
        "B_meas_P10": P10,          # max NEW stitch pts in a Cheb-10 box (centre = walk pt)
        "B_true_upper_C20": C20,    # rigorous upper bound on max over ALL centres
        "A14_max_anchors_in_cheb14": A14,
        "proven_cap_4A14": 4 * A14,
        "all_point_crowding_c10_max": C10all,  # sanity vs reported c10 ceiling
        "example_center_for_P10": c1,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
