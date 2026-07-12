"""
Stage-4 Step 1 (agent round 6): the complete length-<=4 connector word layer.

For every menu step s, enumerate ALL words of length 2..4 over the radius-2
menu whose walk 0 -> M.s satisfies, exactly:
  - correct endpoint (sum of steps = M.s);
  - every step in the menu;
  - no repeated points among {0, partial sums, M.s};
  - no collinear triple among those 3-5 points.

Records per s: word count by length; the multiset of interior offsets with
multiplicities (the word-weighted collar the census must be reweighted by);
and writes the full word lists compactly for Steps 2-4. Then re-runs the
closure GFP at the WORD level: a step survives iff some legal word for M.s
uses only surviving steps; iterate to the greatest fixed point.
"""
from __future__ import annotations

import json
import pickle
from collections import Counter

from search193 import candidate_step_vectors, cross, sub
from router_synthesis import apply_M

MENU = candidate_step_vectors(2)
MENU_INDEX = {v: i for i, v in enumerate(MENU)}


def legal_word(steps_tuple, target):
    pts = [(0, 0, 0)]
    for st in steps_tuple:
        p = pts[-1]
        pts.append((p[0] + st[0], p[1] + st[1], p[2] + st[2]))
    if pts[-1] != target:
        return False
    if len(set(pts)) != len(pts):
        return False
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if cross(sub(pts[j], pts[i]), sub(pts[k], pts[i])) == (0, 0, 0):
                    return False
    return True


def enumerate_words(target):
    """All legal words of length 2..4 summing to target."""
    out = []
    menu_set = set(MENU)
    # length 2
    for a in MENU:
        b = sub(target, a)
        if b in menu_set and legal_word((a, b), target):
            out.append((a, b))
    # length 3
    for a in MENU:
        r1 = sub(target, a)
        for b in MENU:
            c = sub(r1, b)
            if c in menu_set and legal_word((a, b, c), target):
                out.append((a, b, c))
    # length 4
    for a in MENU:
        r1 = sub(target, a)
        for b in MENU:
            r2 = sub(r1, b)
            for c in MENU:
                d = sub(r2, c)
                if d in menu_set and legal_word((a, b, c, d), target):
                    out.append((a, b, c, d))
    return out


if __name__ == "__main__":
    domains = {}
    for idx, s in enumerate(MENU):
        target = apply_M(s)
        words = enumerate_words(target)
        domains[s] = words
        if idx % 8 == 0:
            by_len = Counter(len(w) for w in words)
            print(f"step {idx}/124 {s}: {len(words)} words {dict(by_len)}", flush=True)

    # word-level closure GFP
    surviving = set(MENU)
    rounds = 0
    while True:
        rounds += 1
        dropped = set()
        for s in surviving:
            ok = any(
                all(st in surviving for st in w) for w in domains[s]
            )
            if not ok:
                dropped.add(s)
        if not dropped:
            break
        surviving -= dropped
        print(f"closure round {rounds}: dropped {len(dropped)}, remain {len(surviving)}",
              flush=True)

    # summary + artifacts
    total = sum(len(w) for w in domains.values())
    interior_offsets = Counter()
    for s in surviving:
        for w in domains[s]:
            if all(st in surviving for st in w):
                acc = (0, 0, 0)
                for st in w[:-1]:
                    acc = (acc[0] + st[0], acc[1] + st[1], acc[2] + st[2])
                    interior_offsets[acc] += 1

    print(f"\ntotal legal words (unrestricted): {total}")
    print(f"word-level closure: {len(surviving)}/{len(MENU)} steps survive "
          f"({rounds-0} pruning rounds)")
    print(f"word-weighted collar: {len(interior_offsets)} distinct interior "
          f"offsets, total multiplicity {sum(interior_offsets.values())}")

    with open("connector_domains4.pkl", "wb") as f:
        pickle.dump(
            {
                "domains": {MENU_INDEX[s]: [tuple(MENU_INDEX[st] for st in w)
                                            for w in ws]
                            for s, ws in domains.items()},
                "surviving": sorted(MENU_INDEX[s] for s in surviving),
                "menu": MENU,
            },
            f,
        )
    json.dump(
        {str(k): v for k, v in interior_offsets.items()},
        open("collar_multiplicity4.json", "w"),
    )
    print("wrote connector_domains4.pkl, collar_multiplicity4.json", flush=True)
