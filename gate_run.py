"""
THE GATE (2026-07-14): repaired construction, levels 5-7, exact word-union ledger.

Repairs implemented (L3' spec, PROOF-SKELETON.md):
  R1  length-5 connector layer on fragile steps (|D_2-4| < 2000)  [dstar5_fragile.pkl]
  R2  fragile-first stitch order: segments stitched in ascending |D_2-4| of their
      parent step, NOT left-to-right (anchors are fixed by M, so segments are
      position-independent; the chain is reassembled in order afterwards)
  R3  ledger recorded at stitch time: fraction of the segment's word space killed
      by the walk-so-far (per-word exact legality against all placed points)

Gate criteria (pre-registered, design/overnight-lemma-attack.json):
  (a) pointwise survivor fraction >= delta = 0.15 at every recorded stitch
  (b) zero hard jams
  (c) N81(L7) = 112.6 +/- 0.7 with the canonical midpoint/Chebyshev/interior
      statistic; KS(L6, L7) below critical

Run:  pypy3 -u gate_run.py > logs/gate-run.log 2>&1
"""
from __future__ import annotations

import json
import pickle
import time
from math import gcd
from random import Random

from erdos193 import first_disqualifier
from search193 import candidate_step_vectors, cross
from amplify193 import legal_against
from amplify_rich import M_BAL3
from imbricate193 import apply

MENU = candidate_step_vectors(2)
IDX = {s: i for i, s in enumerate(MENU)}
FRAGILE_CUT = 2000
SAMPLE_N = 200
DELTA = 0.15
L7_RECORD_STRIDE = 5  # at level 7, record fragile segments + every 5th other


def load_domains():
    d4 = pickle.load(open("connector_domains4.pkl", "rb"))
    doms = {si: sorted(ws, key=len) for si, ws in d4["domains"].items()}
    d24_size = {si: len(ws) for si, ws in doms.items()}
    d5 = pickle.load(open("dstar5_fragile.pkl", "rb"))
    for step, words in d5.items():
        si = IDX[step]
        assert d24_size[si] < FRAGILE_CUT
        doms[si] = doms[si] + [tuple(IDX[v] for v in w) for w in words]
    return doms, d24_size


def load_level4_word():
    data = json.load(open("viz/walk3d-data.json"))
    pts = [tuple(p) for p in data["levels"][4]["points"]]
    word = []
    for a, b in zip(pts, pts[1:]):
        word.append(IDX[(b[0] - a[0], b[1] - a[1], b[2] - a[2])])
    assert first_disqualifier(pts) is None
    return word, pts


def word_interiors(start, word_idx):
    pts = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = MENU[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        pts.append((x, y, z))
    return pts


def word_legal(start, word_idx, points, point_set, memo):
    """Exact: every interior point legal against all placed points, and no
    placed point lies on a line through two interiors of this word.
    (Interior-only triples and interiors-vs-endpoints are pre-certified in
    the domain construction; the final first_disqualifier is the backstop.)"""
    ints = word_interiors(start, word_idx)
    for p in ints:
        v = memo.get(p)
        if v is None:
            v = legal_against(points, point_set, p)
            memo[p] = v
        if not v:
            return False
    if len(ints) >= 2:
        pairs = [
            (a, (b[0] - a[0], b[1] - a[1], b[2] - a[2]))
            for k, a in enumerate(ints)
            for b in ints[k + 1 :]
        ]
        for q in points:
            for (a, d) in pairs:
                w = (q[0] - a[0], q[1] - a[1], q[2] - a[2])
                if (
                    w[1] * d[2] - w[2] * d[1] == 0
                    and w[2] * d[0] - w[0] * d[2] == 0
                    and w[0] * d[1] - w[1] * d[0] == 0
                ):
                    return False
    return True


def dfs_fallback(start, target, points, point_set, rng, maxlen=8):
    """Original iterative-deepening stitcher, any word up to maxlen."""
    for depth_limit in range(2, maxlen + 1):
        seg_pts, seg_word = [], []
        nodes = [0]

        def dfs(depth):
            nodes[0] += 1
            if nodes[0] > 200_000:
                return False
            last = seg_pts[-1] if seg_pts else start
            gap = max(abs(target[i] - last[i]) for i in range(3))
            if gap > depth * 2:
                return False
            order = list(range(len(MENU)))
            rng.shuffle(order)
            for si in order:
                s = MENU[si]
                p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
                if p == target:
                    if depth == 1:
                        seg_word.append(si)
                        return True
                    continue
                if depth > 1 and legal_against(
                    points + seg_pts, point_set | set(seg_pts), p
                ):
                    seg_pts.append(p)
                    seg_word.append(si)
                    if dfs(depth - 1):
                        return True
                    seg_pts.pop()
                    seg_word.pop()
            return False

        if dfs(depth_limit):
            return seg_word
    return None


def n_of_d(points, anchors_idx, ds=(3, 9, 27, 81)):
    """Canonical local-law statistic: per segment midpoint, count walk points
    within Chebyshev distance d; report interior-midpoint means + N81 dist."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    bb = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    dmax = max(ds)
    mids = []
    for a, b in zip(anchors_idx, anchors_idx[1:]):
        A, B = points[a], points[b]
        mids.append(((A[0] + B[0]) // 2, (A[1] + B[1]) // 2, (A[2] + B[2]) // 2))
    out = {d: [] for d in ds}
    n81_interior = []
    for c in mids:
        cx, cy, cz = c
        cnt = {d: 0 for d in ds}
        for (x, y, z) in points:
            dx = x - cx
            if dx < 0:
                dx = -dx
            if dx > dmax:
                continue
            dy = y - cy
            if dy < 0:
                dy = -dy
            if dy > dmax:
                continue
            dz = z - cz
            if dz < 0:
                dz = -dz
            m = dx if dx > dy else dy
            if dz > m:
                m = dz
            for d in ds:
                if m <= d:
                    cnt[d] += 1
        for d in ds:
            if (
                c[0] - d >= bb[0]
                and c[0] + d <= bb[1]
                and c[1] - d >= bb[2]
                and c[1] + d <= bb[3]
                and c[2] - d >= bb[4]
                and c[2] + d <= bb[5]
            ):
                out[d].append(cnt[d])
                if d == 81:
                    n81_interior.append(cnt[81])
    stats = {}
    for d in ds:
        v = out[d]
        if v:
            m = sum(v) / len(v)
            var = sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)
            stats[f"N{d}"] = round(m, 3)
            stats[f"N{d}_se"] = round((var / len(v)) ** 0.5, 3)
            stats[f"N{d}_n"] = len(v)
    return stats, n81_interior


def run_level(level, parent_word, parent_pts, doms, d24_size):
    t0 = time.time()
    anchors = [apply(M_BAL3, p) for p in parent_pts]
    points = list(anchors)
    point_set = set(anchors)
    assert len(point_set) == len(anchors)

    order = sorted(range(len(parent_word)), key=lambda i: (d24_size[parent_word[i]], i))
    record_all = level < 7
    ledger = []
    words = {}
    n_jam = n_esc = 0

    for done, i in enumerate(order):
        si = parent_word[i]
        A, B = anchors[i], anchors[i + 1]
        dom = doms[si]
        fragile = d24_size[si] < FRAGILE_CUT
        record = record_all or fragile or (done % L7_RECORD_STRIDE == 0)
        rng = Random(f"gate-L{level}-s{i}")
        memo = {}

        if record:
            sample = dom if len(dom) <= SAMPLE_N else rng.sample(dom, SAMPLE_N)
            surv = [w for w in sample if word_legal(A, w, points, point_set, memo)]
            frac = len(surv) / len(sample)
            rec = {
                "i": i, "step": si, "d24": d24_size[si], "dstar": len(dom),
                "n": len(sample), "surv": len(surv), "frac": round(frac, 4),
                "fragile": fragile,
            }
            chosen = min(surv, key=len) if surv else None
        else:
            chosen, rec, frac = None, None, None
            scan = dom if len(dom) <= SAMPLE_N else rng.sample(dom, len(dom))
            for w in scan:
                if word_legal(A, w, points, point_set, memo):
                    chosen = w
                    break

        if chosen is None:
            n_esc += 1
            for w in dom:  # full-space shortest-first scan
                if word_legal(A, w, points, point_set, memo):
                    chosen = w
                    break
            if rec is not None:
                rec["escalated"] = True
        if chosen is None:
            n_jam += 1
            seg_word = dfs_fallback(A, B, points, point_set, rng)
            if rec is not None:
                rec["dfs"] = seg_word is not None
            if seg_word is None:
                print(f"L{level} seg {i}: HARD JAM — GATE FAILS HERE", flush=True)
                ledger.append(rec or {"i": i, "hard_jam": True})
                json.dump(ledger, open(f"gate-ledger-L{level}.json", "w"))
                return None, None
            chosen = tuple(seg_word)

        ints = word_interiors(A, chosen)
        assert word_interiors(A, chosen) and True  # keep pypy honest
        end = ints[-1] if ints else A
        s = MENU[chosen[-1]]
        assert (end[0] + s[0], end[1] + s[1], end[2] + s[2]) == B
        points.extend(ints)
        point_set.update(ints)
        words[i] = chosen
        if rec is not None:
            rec["len"] = len(chosen)
            ledger.append(rec)

        if done % 250 == 249:
            el = time.time() - t0
            fr = [r["frac"] for r in ledger]
            print(
                f"L{level}: {done+1}/{len(order)} segs, {el:.0f}s, "
                f"minfrac {min(fr):.3f} meanfrac {sum(fr)/len(fr):.3f}, "
                f"esc {n_esc} jam {n_jam}",
                flush=True,
            )
        if done % 2000 == 1999:
            json.dump(ledger, open(f"gate-ledger-L{level}.json", "w"))

    # reassemble chain, verify globally
    chain = [anchors[0]]
    new_word = []
    anchors_idx = [0]
    for i in range(len(parent_word)):
        w = words[i]
        chain.extend(word_interiors(anchors[i], w))
        chain.append(anchors[i + 1])
        new_word.extend(w)
        anchors_idx.append(len(chain) - 1)
    assert set(chain) == point_set
    print(f"L{level}: verifying {len(chain)} points ...", flush=True)
    bad = first_disqualifier(chain)
    assert bad is None, f"L{level} VERIFY FAILED: {bad}"

    stats, n81 = n_of_d(chain, anchors_idx)
    fr = [r["frac"] for r in ledger]
    summary = {
        "level": level, "steps": len(new_word), "points": len(chain),
        "recorded": len(ledger), "min_frac": min(fr), "mean_frac": sum(fr) / len(fr),
        "p01_frac": sorted(fr)[max(0, len(fr) // 100 - 1)],
        "below_delta": sum(1 for f in fr if f < DELTA),
        "escalations": n_esc, "jams": n_jam, "stats": stats,
        "elapsed_s": round(time.time() - t0),
    }
    json.dump(ledger, open(f"gate-ledger-L{level}.json", "w"))
    json.dump(
        {"summary": summary, "n81_interior": n81},
        open(f"gate-stats-L{level}.json", "w"),
    )
    with open(f"gate-193-L{level}.txt", "w") as f:
        f.write(repr(new_word))
    print(f"L{level} SUMMARY: {json.dumps(summary)}", flush=True)
    return new_word, chain


def ks_stat(a, b):
    sa, sb = sorted(a), sorted(b)
    vals = sorted(set(sa) | set(sb))
    import bisect

    ks = 0.0
    for v in vals:
        fa = bisect.bisect_right(sa, v) / len(sa)
        fb = bisect.bisect_right(sb, v) / len(sb)
        ks = max(ks, abs(fa - fb))
    crit = 1.358 * (1 / len(a) + 1 / len(b)) ** 0.5
    return ks, crit


if __name__ == "__main__":
    doms, d24_size = load_domains()
    print(
        f"domains loaded: {len(doms)} steps, fragile "
        f"{sum(1 for v in d24_size.values() if v < FRAGILE_CUT)}",
        flush=True,
    )
    word, pts = load_level4_word()
    print(f"level 4 seed: {len(word)} steps VERIFIED", flush=True)
    n81_by_level = {}
    for level in (5, 6, 7):
        word, pts = run_level(level, word, pts, doms, d24_size)
        if word is None:
            print("GATE: FAILED", flush=True)
            break
        n81_by_level[level] = json.load(open(f"gate-stats-L{level}.json"))[
            "n81_interior"
        ]
    if 6 in n81_by_level and 7 in n81_by_level:
        ks, crit = ks_stat(n81_by_level[6], n81_by_level[7])
        print(f"KS(L6,L7) on N81: {ks:.4f} vs critical {crit:.4f} "
              f"({'BELOW — fixed point' if ks < crit else 'ABOVE — drift'})",
              flush=True)
    print("GATE RUN COMPLETE", flush=True)
