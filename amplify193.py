"""
Anchor-guided amplification for Problem #193 (v3 of the imbricated machinery).

Take a triple-free walk W (word over a step menu). Its image M.W under an
expanding integer matrix M is triple-free automatically (M is linear, so it
preserves collinearity). Fabricate the next level by walking from anchor to
anchor of M.W using menu steps, where every proposed point is checked against
ALL points placed so far at this level — a global check, so there are no
seam blind spots and no context-free-tile bottleneck. Different occurrences
of the same base letter may use different connecting segments.

Each successful level multiplies walk length by the mean segment length while
staying fully verified, so k levels give exponential length from polynomial
work. Recovered periodicity in segment choices would point back to a true
morphism and a finite certificate.
"""
from __future__ import annotations

import sys
from random import Random

from erdos193 import first_disqualifier
from imbricate193 import (
    M_IRRATIONAL,
    M_PERIODIC,
    apply,
    random_menu,
    solution_multisets,
)
from imbricate_seam import walk_points


def menu_reachable(steps, M, maxlen):
    """Every scaled step M.s must be an integer non-negative combination of
    menu steps (necessary for any segment to exist). Cheap pre-filter."""
    return all(
        solution_multisets(steps, apply(M, s), maxlen, node_budget=40_000, max_solutions=1)
        for s in steps
    )


def legal_against(points_list, point_set, p):
    """p must not repeat a vertex nor be collinear with two existing ones."""
    if p in point_set:
        return False
    from math import gcd

    seen = set()
    px, py, pz = p
    for (qx, qy, qz) in points_list:
        vx, vy, vz = qx - px, qy - py, qz - pz
        g = gcd(gcd(abs(vx), abs(vy)), abs(vz))
        w = (vx // g, vy // g, vz // g)
        for c in w:
            if c:
                if c < 0:
                    w = (-w[0], -w[1], -w[2])
                break
        if w in seen:
            return False
        seen.add(w)
    return True


def amplify_level(word, steps, M, rng, seg_maxlen=16, seg_tries=6, restarts=8):
    """
    One amplification level. Returns the new word (over the same menu) whose
    walk visits the M-scaled anchors of `word`'s walk, or None.

    Greedy with segment-level randomized retries and level restarts: segments
    are DFS'd one at a time against the global point set; a stuck segment
    triggers re-randomization, and a stuck level triggers a full restart.
    """
    anchors = [apply(M, p) for p in walk_points(word, steps)]
    max_step = max(max(abs(c) for c in s) for s in steps)
    best_progress = 0

    for _ in range(restarts):
        points = [anchors[0]]
        point_set = {anchors[0]}
        new_word = []
        failed = False

        for seg_index, target in enumerate(anchors[1:]):
            done = False
            # Future anchors are known: treat them as obstacles NOW so a
            # stitch can never form a line that pre-poisons a later target.
            future = anchors[seg_index + 2 :]
            for _ in range(seg_tries):
                # randomized DFS for one segment against the global state
                order = list(range(len(steps)))
                seg_points, seg_word = [], []
                nodes = [0]

                def dfs(depth):
                    nodes[0] += 1
                    if nodes[0] > 30_000:
                        return False
                    last = points[-1] if not seg_points else seg_points[-1]
                    gap = max(abs(target[i] - last[i]) for i in range(3))
                    if gap == 0:
                        return True
                    if depth == 0 or gap > depth * max_step:
                        return False
                    rng.shuffle(order)
                    for si in list(order):
                        s = steps[si]
                        p = (last[0] + s[0], last[1] + s[1], last[2] + s[2])
                        if p == target or legal_against(
                            points + seg_points + [target] + future,
                            point_set | set(seg_points) | {target} | set(future),
                            p,
                        ):
                            seg_points.append(p)
                            seg_word.append(si)
                            if dfs(depth - 1):
                                return True
                            seg_points.pop()
                            seg_word.pop()
                    return False

                # iterative deepening: shortest stitch first (less congestion,
                # smaller growth factor per level)
                gap0 = max(abs(target[i] - points[-1][i]) for i in range(3))
                min_depth = max(1, -(-gap0 // max_step))
                found = False
                for depth_limit in range(min_depth, seg_maxlen + 1):
                    nodes[0] = 0
                    if dfs(depth_limit):
                        found = True
                        break
                    seg_points.clear()
                    seg_word.clear()
                if found:
                    points.extend(seg_points)
                    point_set.update(seg_points)
                    new_word.extend(seg_word)
                    done = True
                    break
            if not done:
                best_progress = max(best_progress, seg_index)
                failed = True
                break
            best_progress = max(best_progress, seg_index + 1)

        if not failed:
            # independent global verification of the whole level
            assert first_disqualifier(points) is None
            return new_word
    print(
        f"    (stitcher best progress: {best_progress}/{len(anchors) - 1} segments)",
        flush=True,
    )
    return None


def run(menu, M, base_word, steps, rng, max_levels=6, cap=20000):
    word = list(base_word)
    print(f"level 0: length {len(word)}", flush=True)
    for level in range(1, max_levels + 1):
        if len(word) > cap:
            print(f"stopping: word length {len(word)} exceeds cap", flush=True)
            break
        new = amplify_level(word, steps, M, rng)
        if new is None:
            print(f"level {level}: FAILED to amplify", flush=True)
            return word, level - 1
        word = new
        print(f"level {level}: length {len(word)} (triple-free, verified)", flush=True)
    return word, max_levels


def find_base(steps, rng, length=12, tries=4000):
    """Short random triple-free walk over the menu to seed level 0."""
    best = None
    for _ in range(tries):
        points = [(0, 0, 0)]
        pset = {(0, 0, 0)}
        word = []
        for _ in range(length):
            sis = list(range(len(steps)))
            rng.shuffle(sis)
            placed = False
            for si in sis:
                s = steps[si]
                p = (
                    points[-1][0] + s[0],
                    points[-1][1] + s[1],
                    points[-1][2] + s[2],
                )
                if legal_against(points, pset, p):
                    points.append(p)
                    pset.add(p)
                    word.append(si)
                    placed = True
                    break
            if not placed:
                break
        if best is None or len(word) > len(best):
            best = word
        if len(best) >= length:
            return best
    return best


if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    rng = Random(193)
    matrices = {"periodic(M^3=2I)": M_PERIODIC, "irrational-rot": M_IRRATIONAL}
    best = {name: 0 for name in matrices}

    for trial in range(trials):
        menu = random_menu(rng, rng.choice((6, 7)))
        if menu is None:
            continue
        base = find_base(menu, rng)
        if base is None or len(base) < 8:
            continue
        for name, M in matrices.items():
            if not menu_reachable(menu, M, maxlen=16):
                continue
            print(f"trial={trial} {name}: menu reachable, amplifying {menu}", flush=True)
            word, levels = run(menu, M, base, menu, rng)
            if len(word) > best[name]:
                best[name] = len(word)
                print(
                    f"trial={trial} {name}: NEW BEST length={len(word)} "
                    f"({levels} levels) menu={menu}",
                    flush=True,
                )
    print("FINAL", best)
