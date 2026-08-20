"""
Parallel triple-free verifier (striped direction-hash).

Semantics identical to erdos193.first_disqualifier: for every k, the primitive
directions from points[k] to all earlier points must be pairwise distinct, and
no vertex repeats. Worker K of N handles the stripe k ≡ K (mod N); the union of
stripes is exactly the serial check. Direction keys are packed ints (requires
coordinate span < 2^20 — asserted).

  pypy3 verify_parallel.py all 6 --level 8 --prefix gate2   # spawn 6 workers
  pypy3 verify_parallel.py worker K N --level 8 --prefix gate2
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from math import gcd

from fast_legal import LIMIT, SHIFT


def load_points(level, prefix):
    os.environ["GATE_PREFIX"] = prefix
    import gate_l7
    gate_l7.PREFIX = prefix
    word, pts = gate_l7.get_parent(level + 1)  # walks {prefix}-193-L{level}.txt
    return pts


def worker(points, K, N):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    assert span < LIMIT, "key packing overflow"
    t0 = time.time()
    n = len(points)
    for k in range(K, n, N):
        px, py, pz = xs[k], ys[k], zs[k]
        seen = set()
        add = seen.add
        for i in range(k):
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
            key = ((vx << SHIFT) + vy << SHIFT) + vz
            if key in seen:
                print(f"COLLINEAR: k={k} shares a direction among i<{k} "
                      f"(point {points[k]})", flush=True)
                return False
            add(key)
        if k % (50 * N) < N and k:
            el = time.time() - t0
            done = (k * k) / (n * n)
            print(f"worker {K}/{N}: k={k}/{n} ({100*done:.1f}% of work, "
                  f"{el:.0f}s)", flush=True)
    print(f"worker {K}/{N}: STRIPE CLEAN ({time.time()-t0:.0f}s)", flush=True)
    return True


if __name__ == "__main__":
    mode = sys.argv[1]
    level = int(sys.argv[sys.argv.index("--level") + 1])
    prefix = (sys.argv[sys.argv.index("--prefix") + 1]
              if "--prefix" in sys.argv else "gate")
    if mode == "worker":
        pts = load_points(level, prefix)
        ok = worker(pts, int(sys.argv[2]), int(sys.argv[3]))
        sys.exit(0 if ok else 1)
    elif mode == "all":
        n = int(sys.argv[2])
        procs = [subprocess.Popen(
            [sys.executable, "-u", __file__, "worker", str(k), str(n),
             "--level", str(level), "--prefix", prefix])
            for k in range(n)]
        codes = [p.wait() for p in procs]
        if all(c == 0 for c in codes):
            print(f"PARALLEL-VERIFIED: level {level} ({prefix}) triple-free, "
                  f"no repeated vertex", flush=True)
        else:
            print(f"VERIFY FAILED: worker exit codes {codes}", flush=True)
            sys.exit(1)
