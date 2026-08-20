"""
ATTACK 1, finale — exact full-word-space survivor counts at the worst
stitch-time states found in waves 1-2. Replays the given seeds through the
exact repaired constructor and, at every segment whose 200-sample frac <=
FRAC_CUT (and dstar <= DSTAR_CUT), counts survivors over the ENTIRE domain.
Usage: pypy3 -u design/attack1_exact.py tag1 tag2 ...
"""
from __future__ import annotations

import json
import sys
import time
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193/design")

from attack1_seed import (  # noqa: E402
    MENU, FRAGILE_CUT, NODES, crafted_base, wcheck,
)
from attack1_wave2 import crafted_band  # noqa: E402
from gate_run import load_domains, word_interiors  # noqa: E402
from amplify193 import find_base  # noqa: E402
from erdos193 import first_disqualifier  # noqa: E402
from imbricate193 import apply  # noqa: E402
from amplify_rich import M_BAL3  # noqa: E402
from fast_legal import Store  # noqa: E402

FRAC_CUT = 0.06
DSTAR_CUT = 60_000
SAMPLE_N = 200
LEVELS = (1, 2, 3)


def base_from_tag(tag, doms, d24):
    fragile = {k for k, v in d24.items() if v < FRAGILE_CUT}
    ultra = {k for k, v in d24.items() if v == 46}
    band = {k for k, v in d24.items() if 2000 <= v <= 16000}
    kind, ln = tag.split("-")
    L = int(ln.replace("len", ""))
    if kind.startswith("fb"):
        return find_base(MENU, Random(int(kind[2:])), length=L, tries=60)
    if kind.startswith("hugF"):
        return crafted_base(Random(int(kind[4:])), L, True, fragile, ultra)
    if kind.startswith("hug"):
        return crafted_base(Random(int(kind[3:])), L, False, fragile, ultra)
    if kind.startswith("band"):
        return crafted_band(Random(int(kind[4:])), L, band, ultra, False)
    if kind.startswith("alt"):
        return crafted_band(Random(int(kind[3:])), L, band, ultra, True)
    raise ValueError(tag)


def replay_exact(tag, base_word, doms, d24):
    pts = [(0, 0, 0)]
    for si in base_word:
        s = MENU[si]
        p = pts[-1]
        pts.append((p[0] + s[0], p[1] + s[1], p[2] + s[2]))
    assert first_disqualifier(pts) is None
    word = list(base_word)
    out = []
    t0 = time.time()
    for level in LEVELS:
        anchors = [apply(M_BAL3, p) for p in pts]
        store = Store(anchors)
        order = sorted(range(len(word)), key=lambda i: (d24[word[i]], i))
        words = {}
        for done, i in enumerate(order):
            si = word[i]
            A, B = anchors[i], anchors[i + 1]
            dom = doms[si]
            memo = {}
            chosen = None
            for w in dom:
                if wcheck(A, w, store, memo):
                    chosen = w
                    break
            assert chosen is not None, f"{tag} L{level} seg {i}: JAM"
            rng = Random(f"gate-L{level}-s{i}")
            sample = dom if len(dom) <= SAMPLE_N else rng.sample(dom, SAMPLE_N)
            surv = sum(1 for w in sample if wcheck(A, w, store, memo))
            frac = surv / len(sample)
            if frac <= FRAC_CUT and len(dom) <= DSTAR_CUT:
                exact = sum(1 for w in dom if wcheck(A, w, store, memo))
                out.append({"tag": tag, "level": level, "i": i, "step": si,
                            "d24": d24[si], "dstar": len(dom),
                            "frac": round(frac, 4), "exact_survivors": exact,
                            "exact_frac": round(exact / len(dom), 5)})
                print(f"  {tag} L{level} seg {i} step {si} d24 {d24[si]}: "
                      f"sample {frac:.3f} -> EXACT {exact}/{len(dom)} "
                      f"({exact/len(dom):.4f}) [{time.time()-t0:.0f}s, "
                      f"{NODES[0]/1e6:.1f}M nodes]", flush=True)
            ints = word_interiors(A, chosen)
            store.add_many(ints)
            words[i] = chosen
        chain = [anchors[0]]
        nw = []
        for i in range(len(word)):
            chain.extend(word_interiors(anchors[i], words[i]))
            chain.append(anchors[i + 1])
            nw.extend(words[i])
        word, pts = nw, chain
        print(f"  {tag} L{level} done ({len(word)} steps, "
              f"{time.time()-t0:.0f}s)", flush=True)
    return out


def main():
    tags = sys.argv[1:]
    t = time.time()
    doms, d24 = load_domains()
    print(f"domains loaded {time.time()-t:.0f}s", flush=True)
    allout = []
    for tag in tags:
        bw = base_from_tag(tag, doms, d24)
        print(f"replaying {tag}: base {bw}", flush=True)
        allout.extend(replay_exact(tag, bw, doms, d24))
    allout.sort(key=lambda r: r["exact_survivors"])
    with open("design/attack1-exact.json", "w") as f:
        json.dump(allout, f, indent=1)
    print("==== EXACT WORST ====", flush=True)
    for r in allout[:10]:
        print(r, flush=True)


if __name__ == "__main__":
    main()
