"""
Exhaustive (or budgeted) maximum triple-free walk in 2D with the flattened
menu: all 24 nonzero vectors with coords in [-2,2]. First move restricted to
the 5 orbit representatives of the dihedral symmetry group D4 (sound: any
walk maps to one starting with a representative, preserving collinearity).
"""
from __future__ import annotations

import sys
from math import gcd

MENU = [(x, y) for x in range(-2, 3) for y in range(-2, 3) if (x, y) != (0, 0)]
FIRST_REPS = [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)]


def pdir(vx, vy):
    g = gcd(abs(vx), abs(vy))
    vx //= g
    vy //= g
    if vx < 0 or (vx == 0 and vy < 0):
        vx, vy = -vx, -vy
    return (vx, vy)


def legal(points, pset, p):
    if p in pset:
        return False
    seen = set()
    px, py = p
    for (qx, qy) in points:
        d = pdir(qx - px, qy - py)
        if d in seen:
            return False
        seen.add(d)
    return True


def main(budget):
    best = 0
    best_word = None
    nodes = 0
    exhausted = True

    for first in FIRST_REPS:
        points = [(0, 0), first]
        pset = {(0, 0), first}
        word = [first]
        stack = [iter(MENU)]
        while stack:
            if nodes >= budget:
                exhausted = False
                break
            it = stack[-1]
            advanced = False
            for s in it:
                nodes += 1
                p = (points[-1][0] + s[0], points[-1][1] + s[1])
                if legal(points, pset, p):
                    points.append(p)
                    pset.add(p)
                    word.append(s)
                    if len(word) > best:
                        best = len(word)
                        best_word = list(word)
                        print(f"  new best {best} (nodes {nodes})", flush=True)
                    stack.append(iter(MENU))
                    advanced = True
                    break
            if not advanced:
                stack.pop()
                if len(word) > 1:
                    pset.discard(points.pop())
                    word.pop()
        if nodes >= budget:
            break
        print(f"first move {first} subtree exhausted (nodes so far {nodes})", flush=True)

    tag = "EXHAUSTIVE (true maximum)" if exhausted else "budget-limited lower bound"
    print(f"\n2D flattened menu (24 moves): max walk = {best} [{tag}] "
          f"nodes={nodes}")
    if best_word:
        print("word:", best_word)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000_000)
