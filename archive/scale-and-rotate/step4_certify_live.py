"""
Step-4 phase 2 (CPython + numpy): certified upper bound on p_H.

Per side state sigma (successor-class map g_sigma from phase 1):
  N_c(sigma, o) = sum_{o_y} m(o_y) [g_sigma(o_y - o) = c]
  p^o(c) = N_c / Z,  esc^o = (N_E3 + N_E4) / Z
  A(sigma)^2 = sum_o (m(o)/Z) ||p^o||^2

Soundness chain:
  Pr[pair not separated | shared o] <= <p_u^o, p_v^o> + esc_u^o + esc_v^o
     (separation happens whenever the two successor projective classes mod 3
      differ; anything ambiguous or escaped counts as failure)
  sum_o w_o <p_u^o, p_v^o> <= A(s_u) A(s_v)      (Cauchy-Schwarz twice)
  q_bar = (max_sigma A)^2 + 2 esc_max            (worst pair state)
  p_H <= q_bar^H                                  (worst-case Markov product)

Implementation: gather matrix IDX[o_y, o] -> lattice index of (o_y - o),
then per class N_c = W_flat @ (codes == c). No FFT index pitfalls.
"""
from __future__ import annotations

import ast
import json
import math
import time

import numpy as np

L = 25
L3 = L * L * L
N_SIDE = 78728
NCLASS = 13
TOTAL_WORDS = 7_114_584

collar = {ast.literal_eval(k): v
          for k, v in json.load(open("collar_multiplicity4.json")).items()}
# LIVE law: anchor endpoint mass excluded (fossilization is absorbing, not a perturbation)
Z = float(sum(collar.values()))

# cells: all offsets in [-6,6]^3 (superset of collar support)
cells = [(x, y, z) for x in range(-6, 7) for y in range(-6, 7) for z in range(-6, 7)]
NC = len(cells)  # 2197
W_flat = np.array([collar.get(c, 0) for c in cells], dtype=np.float64)
w_o = W_flat / Z  # shared-anchor weight per o cell

def lat_idx(d):
    return ((d[0] + 12) * L + (d[1] + 12)) * L + (d[2] + 12)

IDX = np.empty((NC, NC), dtype=np.int32)
for i, oy in enumerate(cells):
    for j, o in enumerate(cells):
        IDX[i, j] = lat_idx((oy[0] - o[0], oy[1] - o[1], oy[2] - o[2]))

g = np.memmap("g_sigma.bin", dtype=np.int8, mode="r", shape=(N_SIDE, L3))

A2 = np.zeros(N_SIDE)
escmax = np.zeros(N_SIDE)
t0 = time.time()
COLKEY = (np.arange(NC, dtype=np.int64) * 16)[None, :]   # per-o key base
WREP = np.repeat(W_flat, NC)                              # weight per (oy, o) entry

for idx in range(N_SIDE):
    codes = np.asarray(g[idx])[IDX]           # (NC oy, NC o) int8
    keys = (codes.astype(np.int64) + COLKEY).ravel()
    N = np.bincount(keys, weights=WREP, minlength=NC * 16).reshape(NC, 16)
    P = N[:, :NCLASS] / Z                      # (o, class)
    esc = (N[:, 13] + N[:, 14]) / Z
    A2[idx] = float(w_o @ (P * P).sum(axis=1))
    escmax[idx] = float(esc.max())
    if idx % 2000 == 0:
        el = time.time() - t0
        eta = el / max(1, idx + 1) * (N_SIDE - idx - 1)
        print(f"  {idx}/{N_SIDE} A={math.sqrt(A2[idx]):.4f} "
              f"elapsed {el/60:.1f}m eta {eta/60:.0f}m", flush=True)

A = np.sqrt(A2)
esc_max = float(escmax.max())
q_bar = float(A.max()) ** 2 + 2 * esc_max
print("\n=== STEP 4 CERTIFIED BOUNDS ===")
print(f"max A(sigma) = {A.max():.6f}  (mean {A.mean():.6f}, "
      f"p99 {np.percentile(A, 99):.6f})")
print(f"esc_max = {esc_max:.3e}")
print(f"q_bar (certified worst single-level non-separation) = {q_bar:.6f}")

L_TEMPLATES = 6.5e7
closed = None
for H in range(1, 61):
    pH = q_bar ** H
    d = 3 * (H + 1) * L_TEMPLATES
    lhs = math.e * pH * (d + 1)
    if H <= 14 or lhs <= 1:
        print(f"  H={H}: p_H<={pH:.3e}  e*p_H*(d+1)={lhs:.3e}")
    if lhs <= 1 and closed is None:
        closed = H
        print(f"SYMMETRIC LLL CLOSES at H = {H}")
        break
if closed is None:
    print("LLL does not close by H=60 with these bounds")

np.save("step4_A_live.npy", A)
np.save("step4_escmax_live.npy", escmax)
print("wrote step4_A_live.npy, step4_escmax_live.npy", flush=True)
