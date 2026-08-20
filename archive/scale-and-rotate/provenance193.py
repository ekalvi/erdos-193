"""
Deterministic replay of the modulus-3 amplified walk with PROVENANCE:
each point records its parent index in the previous level (anchors map to
their pre-image; stitch points map to their segment's start anchor).
Logic is copied from amplify193.amplify_level with identical rng consumption
so the replay reproduces amplified-193-8292.txt exactly, then verified.

Provenance enables the first-divergence stratification requested in expert
review: for a triple of final-level points, r = deepest level at which all
three share an ancestor; nu_3(Omega) envelopes are then plotted against
divergence depth rather than Euclidean diameter.
"""
from __future__ import annotations

import json
from random import Random

from erdos193 import first_disqualifier
from search193 import candidate_step_vectors
from amplify193 import find_base, apply as _unused  # noqa: F401
from imbricate193 import apply
from imbricate_seam import walk_points
from amplify_rich import M_BAL3
from bnb193 import legal as legal2  # noqa: F401  (not used; kept for parity)
from amplify193 import legal_against


def amplify_level_prov(word, steps, M, rng, seg_maxlen=12, seg_tries=8, restarts=6):
    """amplify193.amplify_level (route='short') + parent tracking.
    Must consume rng identically to the original."""
    anchors = [apply(M, p) for p in walk_points(word, steps)]
    max_step = max(max(abs(c) for c in s) for s in steps)
    best_progress = 0

    for _ in range(restarts):
        points = [anchors[0]]
        parents = [0]
        point_set = {anchors[0]}
        new_word = []
        failed = False

        for seg_index, target in enumerate(anchors[1:]):
            done = False
            future = anchors[seg_index + 2 :]
            for _ in range(seg_tries):
                order = list(range(len(steps)))
                seg_points, seg_word = [], []
                nodes = [0]
                depth_cap = [0]

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

                gap0 = max(abs(target[i] - points[-1][i]) for i in range(3))
                min_depth = max(1, -(-gap0 // max_step))
                found = False
                for depth_limit in range(min_depth, seg_maxlen + 1):
                    nodes[0] = 0
                    depth_cap[0] = depth_limit
                    if dfs(depth_limit):
                        found = True
                        break
                    seg_points.clear()
                    seg_word.clear()
                if found:
                    points.extend(seg_points)
                    point_set.update(seg_points)
                    new_word.extend(seg_word)
                    # parents: intermediate stitches -> segment start (prev idx
                    # seg_index); the final point IS the target anchor -> its
                    # pre-image is prev idx seg_index + 1.
                    for t in range(len(seg_points)):
                        last_one = t == len(seg_points) - 1
                        parents.append(seg_index + 1 if last_one else seg_index)
                    done = True
                    break
            if not done:
                best_progress = max(best_progress, seg_index)
                failed = True
                break
            best_progress = max(best_progress, seg_index + 1)

        if not failed:
            assert first_disqualifier(points) is None
            return new_word, parents
    print(f"    (stitcher best progress: {best_progress}/{len(anchors)-1})", flush=True)
    return None, None


if __name__ == "__main__":
    rng = Random(193)
    menu = candidate_step_vectors(2)
    base = find_base(menu, rng, length=20, tries=200)
    print(f"base: {len(base)}", flush=True)

    word = base
    level_parents = []  # parents[L][j] = parent index of point j (level L+1) in level L
    level_sizes = [len(base) + 1]
    level = 0
    while len(word) <= 6000:
        level += 1
        new_word, parents = amplify_level_prov(word, menu, M_BAL3, rng)
        if new_word is None:
            print(f"level {level}: FAILED", flush=True)
            break
        word = new_word
        level_parents.append(parents)
        level_sizes.append(len(word) + 1)
        print(f"level {level}: length {len(word)}", flush=True)

    # verify replay reproduces the canonical walk
    canonical = open("amplified-193-8292.txt").read()
    assert repr(word) == canonical, "replay mismatch!"
    print("replay MATCHES amplified-193-8292.txt", flush=True)

    json.dump(
        {"sizes": level_sizes, "parents": level_parents},
        open("provenance-8292.json", "w"),
    )
    print("wrote provenance-8292.json", flush=True)
