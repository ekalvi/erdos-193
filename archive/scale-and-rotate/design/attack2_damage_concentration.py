"""
ATTACK 2 — damage concentration on the REPAIRED construction (L3' probe).

Freedom exploited: gate_run.py chooses the FIRST legal word in the
length-sorted domain. Length sort is stable but order WITHIN a length class
is arbitrary (pickle order). So at every stitch the constructor could have
picked ANY legal word of the minimal legal length. The adversary uses that:
at every fragile segment stitched BEFORE a chosen target (fragile-first
order => the conspirators are exactly the earlier fragile segments), it
enumerates the full minimal-length legal class and picks the word that
kills the most of the target's word space D*(target).

Base: certified seed-193 level-0 walk (viz/walk3d-data.json), levels 1..3
built by the repaired constructor itself (benign tie-breaks below the
attack level; same-level conspiracy only, per attack spec).

Budgets: CAND_CAP words scored per segment, global DEADLINE seconds,
progress printed per conspirator. Single process, single core.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from math import gcd
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from imbricate193 import apply
from amplify_rich import M_BAL3
from erdos193 import first_disqualifier
from fast_legal import Store, word_legal_fast

BASE = "/Users/erik/homelab/math193"
MENU = candidate_step_vectors(2)
IDX = {s: i for i, s in enumerate(MENU)}
FRAGILE_CUT = 2000
CAND_CAP = 4000          # max words scored per conspirator segment
D5_TRACK = 400           # d5 sample words tracked for greedy scoring
D5_LEDGER = 200          # d5 sample for per-segment ledger measurements
D5_FINAL_EXACT = 60000   # exact final count if |d5| <= this, else sample
D5_FINAL_SAMPLE = 4000
T0 = time.time()
DEADLINE = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0

SHIFT = 21


def dirkey(px, py, pz, qx, qy, qz):
    vx = qx - px
    vy = qy - py
    vz = qz - pz
    g = gcd(gcd(vx if vx >= 0 else -vx, vy if vy >= 0 else -vy),
            vz if vz >= 0 else -vz)
    if g > 1:
        vx //= g
        vy //= g
        vz //= g
    if vx < 0 or (vx == 0 and (vy < 0 or (vy == 0 and vz < 0))):
        vx = -vx
        vy = -vy
        vz = -vz
    return ((vx << SHIFT) + vy << SHIFT) + vz


def load_domains():
    d4 = pickle.load(open(f"{BASE}/connector_domains4.pkl", "rb"))
    doms = {si: sorted(ws, key=len) for si, ws in d4["domains"].items()}
    d24_size = {si: len(ws) for si, ws in doms.items()}
    d5 = pickle.load(open(f"{BASE}/dstar5_fragile.pkl", "rb"))
    d5_by_si = {}
    for step, words in d5.items():
        si = IDX[step]
        assert d24_size[si] < FRAGILE_CUT
        d5_by_si[si] = [tuple(IDX[v] for v in w) for w in words]
        doms[si] = doms[si] + d5_by_si[si]
    return doms, d24_size, d5_by_si


def word_interiors(start, word_idx):
    pts = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = MENU[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        pts.append((x, y, z))
    return pts


def minimal_legal_class(dom, A, store, memo):
    """All legal words of the minimal legal length (the exact set of words
    the constructor could pick, over all within-class orderings)."""
    i, n, checked = 0, len(dom), 0
    while i < n:
        L = len(dom[i])
        j = i
        while j < n and len(dom[j]) == L:
            j += 1
        legal = []
        for w in dom[i:j]:
            checked += 1
            if word_legal_fast(A, w, store, memo, MENU):
                legal.append(w)
        if legal:
            return L, legal, checked
        i = j
    return None, [], checked


def measure_availability(si, A, store, doms24_len, dom, d5_by_si, d24_size,
                         seed, n_d5, exact_d5=False):
    """(exact 2-4 count, d5 legal, d5 sampled, estimated absolute total)."""
    memo = {}
    d24_words = dom[: d24_size[si]]
    ok24 = sum(1 for w in d24_words if word_legal_fast(A, w, store, memo, MENU))
    d5 = d5_by_si.get(si, [])
    if not d5:
        return ok24, 0, 0, ok24
    if exact_d5 and len(d5) <= D5_FINAL_EXACT:
        ok5 = sum(1 for w in d5 if word_legal_fast(A, w, store, memo, MENU))
        return ok24, ok5, len(d5), ok24 + ok5
    rng = Random(seed)
    sample = d5 if len(d5) <= n_d5 else rng.sample(d5, n_d5)
    ok5 = sum(1 for w in sample if word_legal_fast(A, w, store, memo, MENU))
    est = ok24 + round(ok5 / len(sample) * len(d5))
    return ok24, ok5, len(sample), est


class TargetTracker:
    """Incremental legality of a fixed sample of the target's words."""

    def __init__(self, words_ints, store):
        self.items = []
        for ints in words_ints:
            pairs = [
                (a, (b[0] - a[0], b[1] - a[1], b[2] - a[2]))
                for k, a in enumerate(ints)
                for b in ints[k + 1:]
            ]
            self.items.append((ints, pairs))
        self.alive = set()
        self.dirsets = {}
        pts = store.pts
        uniq = {p for ints, _ in self.items for p in ints}
        for p in uniq:
            px, py, pz = p
            self.dirsets[p] = {
                dirkey(px, py, pz, q[0], q[1], q[2]) for q in pts
            }
        # initial alive = legal against current store
        memo = {}
        for wi, (ints, pairs) in enumerate(self.items):
            word_ok = True
            for p in ints:
                if p in store.pset:
                    word_ok = False
                    break
                ds = self.dirsets[p]
                if len(ds) < len(pts):  # direction collision existed
                    word_ok = False
                    break
            if word_ok and pairs and store.lines_hit(pairs):
                word_ok = False
            if word_ok:
                self.alive.add(wi)

    def killed_by(self, Q):
        killed = []
        dirsets = self.dirsets
        for wi in self.alive:
            ints, pairs = self.items[wi]
            dead = False
            for p in ints:
                px, py, pz = p
                ds = dirsets[p]
                seenq = None
                for q in Q:
                    if q == p:
                        dead = True
                        break
                    k = dirkey(px, py, pz, q[0], q[1], q[2])
                    if k in ds:
                        dead = True
                        break
                    if seenq is None:
                        seenq = {k}
                    elif k in seenq:
                        dead = True
                        break
                    else:
                        seenq.add(k)
                if dead:
                    break
            if not dead:
                for (a, d) in pairs:
                    ax, ay, az = a
                    dx, dy, dz = d
                    for q in Q:
                        wx = q[0] - ax
                        wy = q[1] - ay
                        wz = q[2] - az
                        if (wy * dz == wz * dy and wz * dx == wx * dz
                                and wx * dy == wy * dx):
                            dead = True
                            break
                    if dead:
                        break
            if dead:
                killed.append(wi)
        return killed

    def commit(self, Q):
        for wi in self.killed_by(Q):
            self.alive.discard(wi)
        for p, ds in self.dirsets.items():
            px, py, pz = p
            for q in Q:
                if q != p:
                    ds.add(dirkey(px, py, pz, q[0], q[1], q[2]))


def build_level(level, parent_word, parent_pts, doms, d24_size, d5_by_si,
                ledger_fragile=True):
    """Benign repaired constructor (gate_run semantics), with exact fragile
    ledger. Returns (words, anchors, chain_word, chain_pts, ledger)."""
    anchors = [apply(M_BAL3, p) for p in parent_pts]
    store = Store(anchors)
    order = sorted(range(len(parent_word)),
                   key=lambda i: (d24_size[parent_word[i]], i))
    words = {}
    ledger = []
    for done, i in enumerate(order):
        si = parent_word[i]
        A = anchors[i]
        dom = doms[si]
        fragile = d24_size[si] < FRAGILE_CUT
        if ledger_fragile and fragile:
            ok24, ok5, n5, est = measure_availability(
                si, A, store, None, dom, d5_by_si, d24_size,
                f"att2-L{level}-s{i}", D5_LEDGER)
            ledger.append({
                "level": level, "i": i, "pos": done, "step": si,
                "step_vec": MENU[si], "d24": d24_size[si],
                "dstar": len(dom), "ok24": ok24,
                "d5_frac": (ok5 / n5) if n5 else None, "est_abs": est,
                "frac": est / len(dom),
            })
        memo = {}
        chosen = None
        for w in dom:
            if word_legal_fast(A, w, store, memo, MENU):
                chosen = w
                break
        assert chosen is not None, f"benign L{level} seg {i}: JAM"
        store.add_many(word_interiors(A, chosen))
        words[i] = chosen
    chain = [anchors[0]]
    new_word = []
    for i in range(len(parent_word)):
        w = words[i]
        chain.extend(word_interiors(anchors[i], w))
        chain.append(anchors[i + 1])
        new_word.extend(w)
    assert set(chain) == store.pset
    return words, anchors, new_word, chain, ledger


def adversarial_replay(level, parent_word, anchors, doms, d24_size, d5_by_si,
                       target_i, benign_rec, log, adversarial=True):
    """Replay the level with adversarial (or benign) within-class tie-breaks
    at every segment stitched before target_i; measure target availability
    at its stitch time. Returns result dict."""
    store = Store(anchors)
    order = sorted(range(len(parent_word)),
                   key=lambda i: (d24_size[parent_word[i]], i))
    k = order.index(target_i)
    tsi = parent_word[target_i]
    tA = anchors[target_i]
    tdom = doms[tsi]

    # tracker sample: full 2-4 layer + fixed d5 sample
    rng = Random(f"att2-track-L{level}-s{target_i}")
    d24_words = tdom[: d24_size[tsi]]
    d5 = d5_by_si.get(tsi, [])
    d5_sample = d5 if len(d5) <= D5_TRACK else rng.sample(d5, D5_TRACK)
    sample_words = list(d24_words) + list(d5_sample)
    tracker = None
    if adversarial:
        tracker = TargetTracker(
            [word_interiors(tA, w) for w in sample_words], store)
        log(f"  target i={target_i} step={MENU[tsi]} d24={d24_size[tsi]} "
            f"|D*|={len(tdom)} pos-in-order={k}; tracker alive anchors-only: "
            f"{len(tracker.alive)}/{len(sample_words)}")

    min_consp_avail = None
    consp_records = []
    for done in range(k):
        i = order[done]
        si = parent_word[i]
        A = anchors[i]
        memo = {}
        L, cands, checked = minimal_legal_class(doms[si], A, store, memo)
        if L is None:
            log(f"  !! conspirator seg {i} has ZERO legal words — JAM state")
            return {"jam_at_conspirator": i, "records": consp_records}
        capped = len(cands) > CAND_CAP
        if capped:
            cands = cands[:CAND_CAP]
        if adversarial:
            best_w, best_kill = None, -1
            for w in cands:
                Q = word_interiors(A, w)
                nk = len(tracker.killed_by(Q))
                if nk > best_kill:
                    best_kill, best_w = nk, w
            Q = word_interiors(A, best_w)
            tracker.commit(Q)
        else:
            best_w, best_kill = cands[0], None
            Q = word_interiors(A, best_w)
        # conspirator's own availability at its stitch (fragile ledger)
        rec = {"i": i, "step": si, "d24": d24_size[si], "len": L,
               "n_cands": len(cands), "capped": capped, "kill": best_kill,
               "alive_after": len(tracker.alive) if tracker else None}
        if d24_size[si] < FRAGILE_CUT:
            ok24, ok5, n5, est = measure_availability(
                si, A, store, None, doms[si], d5_by_si, d24_size,
                f"att2-L{level}-s{i}", D5_LEDGER)
            rec["est_abs"] = est
            rec["frac"] = est / len(doms[si])
            if min_consp_avail is None or est < min_consp_avail:
                min_consp_avail = est
        store.add_many(Q)
        consp_records.append(rec)
        if adversarial:
            log(f"  consp {done+1}/{k} seg={i} d24={d24_size[si]} len={L} "
                f"cands={len(cands)}{'(cap)' if capped else ''} "
                f"kill={best_kill} alive={len(tracker.alive)} "
                f"avail={rec.get('est_abs','-')} t={time.time()-T0:.0f}s")
    # target's availability at stitch time, exact
    ok24, ok5, n5, est = measure_availability(
        tsi, tA, store, None, tdom, d5_by_si, d24_size,
        f"att2-final-L{level}-s{target_i}", D5_FINAL_SAMPLE,
        exact_d5=True)
    exact = (len(d5) <= D5_FINAL_EXACT)
    mode = "adv" if adversarial else "benign-exact"
    res = {
        "level": level, "target_i": target_i, "step_vec": MENU[tsi],
        "d24": d24_size[tsi], "dstar": len(tdom), "mode": mode,
        "n_conspirators": k,
        "adv_ok24": ok24, "adv_d5_ok": ok5, "adv_d5_n": n5,
        "adv_est_abs": est, "adv_frac": est / len(tdom),
        "d5_exact": exact,
        "tracker_alive_frac":
            len(tracker.alive) / len(sample_words) if tracker else None,
        "benign": benign_rec,
        "min_conspirator_avail": min_consp_avail,
        "conspirators": consp_records,
    }
    log(f"  {mode} TARGET RESULT: avail {est}/{len(tdom)} "
        f"(frac {est/len(tdom):.4f}, ok24={ok24}, "
        f"d5 {'exact' if exact else 'sampled'})")
    return res


def main():
    def log(msg):
        print(msg, flush=True)

    doms, d24_size, d5_by_si = load_domains()
    log(f"domains: {len(doms)} steps, fragile "
        f"{sum(1 for v in d24_size.values() if v < FRAGILE_CUT)}")

    data = json.load(open(f"{BASE}/viz/walk3d-data.json"))
    pts0 = [tuple(p) for p in data["levels"][0]["points"]]
    word0 = [IDX[(b[0] - a[0], b[1] - a[1], b[2] - a[2])]
             for a, b in zip(pts0, pts0[1:])]
    assert first_disqualifier(pts0) is None
    log(f"level 0: {len(word0)} steps (certified base, seed 193)")

    results = {"benign_ledgers": {}, "attacks": []}

    # ---- benign levels 1..3 ----
    prev_word, prev_pts = word0, pts0
    level_data = {}
    for level in (1, 2, 3):
        words, anchors, new_word, chain, ledger = build_level(
            level, prev_word, prev_pts, doms, d24_size, d5_by_si)
        bad = first_disqualifier(chain)
        assert bad is None, f"benign L{level} verify failed: {bad}"
        frs = [r["frac"] for r in ledger]
        log(f"benign L{level}: {len(new_word)} steps, {len(chain)} pts, "
            f"fragile segs {len(ledger)}, frac min/mean "
            f"{min(frs):.4f}/{sum(frs)/len(frs):.4f}, "
            f"min est_abs {min(r['est_abs'] for r in ledger)} "
            f"t={time.time()-T0:.0f}s")
        level_data[level] = (prev_word, anchors, ledger)
        results["benign_ledgers"][level] = ledger
        prev_word, prev_pts = new_word, chain

    # ---- choose targets ----
    def pick_targets(level):
        parent_word, anchors, ledger = level_data[level]
        order = sorted(range(len(parent_word)),
                       key=lambda i: (d24_size[parent_word[i]], i))
        frag = [i for i in order if d24_size[parent_word[i]] < FRAGILE_CUT]
        by_i = {r["i"]: r for r in ledger}
        targets = []
        # last fragile in order (max conspirators)
        targets.append(("last-fragile", frag[-1]))
        # last 46-class segment (smallest 2-4 layer)
        c46 = [i for i in frag if d24_size[parent_word[i]] == 46]
        if c46:
            targets.append(("last-46", c46[-1]))
        # weakest benign fragile segment
        weakest = min(ledger, key=lambda r: r["frac"])["i"]
        targets.append(("benign-weakest", weakest))
        seen, out = set(), []
        for tag, i in targets:
            if i not in seen:
                seen.add(i)
                out.append((tag, i, by_i[i]))
        return out, parent_word, anchors

    for level in (2, 3):
        tlist, parent_word, anchors = pick_targets(level)
        for tag, ti, ben in tlist:
            if time.time() - T0 > DEADLINE:
                log(f"DEADLINE — skipping remaining attacks at L{level}")
                break
            log(f"== ATTACK L{level} target[{tag}] i={ti} ==")
            res = adversarial_replay(level, parent_word, anchors, doms,
                                     d24_size, d5_by_si, ti, ben, log)
            res["tag"] = tag
            # exact benign baseline for the same target, same measurement
            bres = adversarial_replay(level, parent_word, anchors, doms,
                                      d24_size, d5_by_si, ti, ben, log,
                                      adversarial=False)
            res["benign_exact"] = {
                "est_abs": bres["adv_est_abs"], "frac": bres["adv_frac"],
                "ok24": bres["adv_ok24"],
                "min_conspirator_avail": bres["min_conspirator_avail"],
            }
            results["attacks"].append(res)

    with open(f"{BASE}/design/attack2-results.json", "w") as f:
        slim = {
            "benign_ledgers": results["benign_ledgers"],
            "attacks": [
                {k: v for k, v in a.items() if k != "conspirators"}
                | {"conspirators": a.get("conspirators", [])}
                for a in results["attacks"]
            ],
        }
        json.dump(slim, f, indent=1)
    log(f"WROTE design/attack2-results.json t={time.time()-T0:.0f}s")

    # summary
    for a in results["attacks"]:
        if "adv_est_abs" not in a:
            continue
        b = a.get("benign_exact", a["benign"])
        log(f"SUMMARY L{a['level']} {a['tag']} i={a['target_i']} "
            f"step={a['step_vec']} d24={a['d24']}: benign {b['est_abs']} "
            f"({b['frac']:.4f}) -> adversarial {a['adv_est_abs']} "
            f"({a['adv_frac']:.4f}); ok24 {b['ok24']} -> {a['adv_ok24']}; "
            f"conspirators {a['n_conspirators']}, "
            f"min conspirator avail adv={a['min_conspirator_avail']} "
            f"benign={b.get('min_conspirator_avail')}")


if __name__ == "__main__":
    main()
