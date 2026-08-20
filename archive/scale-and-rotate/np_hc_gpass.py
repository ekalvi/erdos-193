"""
Step-4 phase 1 (PyPy): tabulate g_sigma(d) = successor class code for every
side state sigma and every delta on the dense [-12,12]^3 difference lattice.

Codes: 0..12 = projective class mod 3 of the successor's primitive part
(separation classification needs only these); 13 = E3; 14 = E4; 15 = lattice
point not in Delta4 (unreachable difference; weight will be zero anyway).

Output: g_sigma.bin, int8 array of shape (N_SIDE, 25^3), ~1.2 GB.
"""
from __future__ import annotations

import pickle
import time

from np_hc import E3, E4, F, N_SIDE, PROJ3_RANK, proj3_class, side_unpack

L = 25  # lattice [-12,12]
L3 = L * L * L


def lattice_index(d):
    return ((d[0] + 12) * L + (d[1] + 12)) * L + (d[2] + 12)


def main():
    deltas = pickle.load(open("delta4.pkl", "rb"))
    dcodes = [(d, lattice_index(d)) for d in deltas]
    out = open("g_sigma.bin", "wb")
    t0 = time.time()
    for idx in range(N_SIDE):
        a, k, U = side_unpack(idx)
        row = bytearray([15]) * L3
        for d, li in dcodes:
            s = F(a, k, U, d)
            if s == E3:
                row[li] = 13
            elif s == E4:
                row[li] = 14
            else:
                _, _, U2 = side_unpack(s)
                row[li] = PROJ3_RANK[proj3_class(U2)]
        out.write(bytes(row))
        if idx % 4000 == 0:
            el = time.time() - t0
            eta = el / max(1, idx + 1) * (N_SIDE - idx - 1)
            print(f"  {idx}/{N_SIDE} elapsed {el/60:.1f}m eta {eta/60:.0f}m", flush=True)
    out.close()
    print(f"wrote g_sigma.bin ({N_SIDE} x {L3} int8)", flush=True)


if __name__ == "__main__":
    main()
