"""
Tuned legality core for the gate: semantically identical to
amplify193.legal_against + gate_run.word_legal, ~3-4x faster under PyPy.

Tricks: points held as three parallel int lists (no tuple unpacking in the
hot loop); primitive directions packed into a single int key (no tuple
allocation); canonical sign inlined. Validated by reproducing the inline
level-5 gate walk and ledger exactly (see gate_l7.py dry-run).

Direction-key packing requires |component| < 2**20 after gcd division —
asserted on construction from the bounding box (level-7 coords are ~2**15).
"""
from __future__ import annotations

from math import gcd

SHIFT = 21
LIMIT = 1 << 20


class Store:
    __slots__ = ("xs", "ys", "zs", "pts", "pset")

    def __init__(self, pts):
        self.xs = [p[0] for p in pts]
        self.ys = [p[1] for p in pts]
        self.zs = [p[2] for p in pts]
        self.pts = list(pts)
        self.pset = set(pts)
        assert len(self.pset) == len(pts)
        span = max(
            max(self.xs) - min(self.xs),
            max(self.ys) - min(self.ys),
            max(self.zs) - min(self.zs),
        )
        assert span < LIMIT, "direction key packing would overflow"

    def add_many(self, pts):
        self.xs.extend(p[0] for p in pts)
        self.ys.extend(p[1] for p in pts)
        self.zs.extend(p[2] for p in pts)
        self.pts.extend(pts)
        self.pset.update(pts)

    def legal(self, p):
        """p must not repeat a vertex nor be collinear with two stored points."""
        if p in self.pset:
            return False
        px, py, pz = p
        xs, ys, zs = self.xs, self.ys, self.zs
        seen = set()
        add = seen.add
        for i in range(len(xs)):
            vx = xs[i] - px
            vy = ys[i] - py
            vz = zs[i] - pz
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
            k = ((vx << SHIFT) + vy << SHIFT) + vz
            if k in seen:
                return False
            add(k)
        return True

    def lines_hit(self, pairs):
        """True iff some stored point lies on a line through one of the given
        (anchor, direction) pairs."""
        flat = [(a[0], a[1], a[2], d[0], d[1], d[2]) for a, d in pairs]
        xs, ys, zs = self.xs, self.ys, self.zs
        for i in range(len(xs)):
            qx = xs[i]
            qy = ys[i]
            qz = zs[i]
            for (ax, ay, az, dx, dy, dz) in flat:
                wx = qx - ax
                wy = qy - ay
                wz = qz - az
                if wy * dz == wz * dy and wz * dx == wx * dz and wx * dy == wy * dx:
                    return True
        return False


def word_legal_fast(start, word_idx, store, memo, menu):
    """Drop-in equivalent of gate_run.word_legal against a Store."""
    ints = []
    x, y, z = start
    for si in word_idx[:-1]:
        s = menu[si]
        x, y, z = x + s[0], y + s[1], z + s[2]
        ints.append((x, y, z))
    for p in ints:
        v = memo.get(p)
        if v is None:
            v = store.legal(p)
            memo[p] = v
        if not v:
            return False
    if len(ints) >= 2:
        pairs = [
            (a, (b[0] - a[0], b[1] - a[1], b[2] - a[2]))
            for k, a in enumerate(ints)
            for b in ints[k + 1 :]
        ]
        if store.lines_hit(pairs):
            return False
    return True
