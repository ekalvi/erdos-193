"""
NP-HC Step-2 side pass: all 78,728 side states x all 15,545 Delta4
perturbations (~1.22e9 exact transitions).

Per side state, records:
  - escape counts E3 (content overflow), E4 (horizon exhaustion);
  - climb histogram a' - a (certifies the climb law);
  - number of distinct successor side states;
  - 13-bit mask of successor projective classes mod 3 (the availability key:
    if every state's mask has >= 2 bits, any unresolved pair can be steered
    to projective separation in one level — the universal availability
    theorem for all pairs at once);
  - reachability seeds alpha(d) marked, and a closure flag pass afterwards.

Output: np_hc_side.pkl + summary to stdout. Checkpointed every 4,000 states.
"""
from __future__ import annotations

import pickle
import time

from np_hc import (
    A_CAP,
    E3,
    E4,
    F,
    N_SIDE,
    PROJ3_RANK,
    _PER_A,
    proj3_class,
    side_index,
    side_unpack,
)


def main():
    deltas = pickle.load(open("delta4.pkl", "rb"))
    print(f"side pass: {N_SIDE} states x {len(deltas)} deltas", flush=True)

    masks = [0] * N_SIDE
    e3 = [0] * N_SIDE
    e4 = [0] * N_SIDE
    nsucc = [0] * N_SIDE
    climb = {}
    succ_sets_sample = {}

    t0 = time.time()
    for idx in range(N_SIDE):
        a, k, U = side_unpack(idx)
        seen = set()
        mask = 0
        ce3 = ce4 = 0
        for d in deltas:
            s = F(a, k, U, d)
            if s == E3:
                ce3 += 1
                continue
            if s == E4:
                ce4 += 1
                continue
            seen.add(s)
            a2 = s // _PER_A
            key = a2 - a
            climb[key] = climb.get(key, 0) + 1
            _, _, U2 = side_unpack(s)
            mask |= 1 << PROJ3_RANK[proj3_class(U2)]
        masks[idx] = mask
        e3[idx] = ce3
        e4[idx] = ce4
        nsucc[idx] = len(seen)
        if idx < 4:
            succ_sets_sample[idx] = sorted(seen)[:50]
        if idx % 4000 == 0:
            el = time.time() - t0
            eta = el / max(1, idx + 1) * (N_SIDE - idx - 1)
            full = sum(1 for m in masks[: idx + 1] if bin(m).count("1") == 13)
            print(
                f"  {idx}/{N_SIDE} elapsed {el/60:.1f}m eta {eta/60:.0f}m "
                f"full-coverage so far {full}/{idx+1}",
                flush=True,
            )
            pickle.dump(
                {"masks": masks, "e3": e3, "e4": e4, "nsucc": nsucc,
                 "climb": climb, "done_through": idx},
                open("np_hc_side.ckpt.pkl", "wb"),
            )

    total_trans = N_SIDE * len(deltas)
    bits = [bin(m).count("1") for m in masks]
    full13 = sum(1 for b in bits if b == 13)
    ge2 = sum(1 for b in bits if b >= 2)
    print("\n=== SIDE PASS COMPLETE ===")
    print(f"transitions: {total_trans}")
    print(f"E3 total {sum(e3)} ({sum(e3)/total_trans:.2e}), "
          f"E4 total {sum(e4)} ({sum(e4)/total_trans:.2e})")
    print(f"climb histogram (a'-a): {dict(sorted(climb.items()))}")
    print(f"projective mod-3 coverage: full 13/13 for {full13}/{N_SIDE} states; "
          f">=2 classes for {ge2}/{N_SIDE}")
    if ge2 == N_SIDE:
        print("UNIVERSAL AVAILABILITY: every side state can reach >=2 projective "
              "classes -> every unresolved pair separable in one level")
    else:
        bad = [i for i, b in enumerate(bits) if b < 2][:20]
        print(f"EXCEPTIONS: {N_SIDE - ge2} states with coverage <2; first: "
              f"{[(i, side_unpack(i)) for i in bad[:5]]}")
    print(f"successor-count stats: min {min(nsucc)}, max {max(nsucc)}")

    pickle.dump(
        {"masks": masks, "e3": e3, "e4": e4, "nsucc": nsucc, "climb": climb,
         "sample_succ": succ_sets_sample},
        open("np_hc_side.pkl", "wb"),
    )
    print("wrote np_hc_side.pkl", flush=True)


if __name__ == "__main__":
    main()
