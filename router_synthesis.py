"""
Stage 1-3 of the ranked-router synthesis experiment (strategy-agent round 5).

Question: after first divergence, can stitch routing always either projectively
separate a chord pair mod 3^q or strictly decrease a finite unresolved rank?

This module implements, in exact integer arithmetic:
  - connector enumeration: all 2-3 step menu words realizing each scaled step
    M.s, internally non-collinear (Stage 3 substrate);
  - the offset collar O (positions of connector-interior points relative to
    the segment start) and the chord-perturbation set Delta = O - O;
  - the pair-transition map (u, v) -> (Mu + d1, Mv + d2) tracked modulo 3^W
    (W = working depth > q, so content computations up to the cap are exact);
  - projective-agreement depth j(u, v) = c_3(U x V) capped at q+1, where U, V
    are 3-primitive parts (this is kappa_3, the agent's cancellation defect);
  - for a given unresolved pair state, the census of transitions: separated /
    rank-decreased / rank-equal / rank-increased.

Soundness notes (deliberate, documented):
  - residues are tracked mod 3^W with W = q + 3; content is capped at W-1, so
    any content comparison below the cap is exact;
  - the census treats each chord pair independently (optimistic abstraction);
    a full viability GAME (one stitch serves many pairs) is Stage 4+ and is
    NOT claimed here.
"""
from __future__ import annotations

from itertools import product

from search193 import candidate_step_vectors, cross, sub

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))  # modulus-3 irrational rotation
MENU = candidate_step_vectors(2)
Q = 2            # certificate modulus depth: 3^Q = 9
W = Q + 3        # working depth: residues mod 3^W = 243
MODW = 3 ** W


def apply_M(v):
    return (
        M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
        M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
        M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2],
    )


def content3(v, cap=W - 1):
    """3-adic content of a vector, capped (exact below the cap)."""
    if v == (0, 0, 0):
        return cap
    c = 0
    x, y, z = v
    while c < cap and x % 3 == 0 and y % 3 == 0 and z % 3 == 0:
        x //= 3
        y //= 3
        z //= 3
        c += 1
    return c


def primitive3(v):
    c = content3(v)
    return c, (v[0] // 3**c, v[1] // 3**c, v[2] // 3**c)


def agreement_depth(u, v, cap=Q + 1):
    """j = kappa_3(u, v) = c_3(U x V), capped. j >= 1 means the primitive
    directions agree projectively mod 3^j (unresolved at depth j)."""
    _, U = primitive3(u)
    _, V = primitive3(v)
    return content3(cross(U, V), cap=cap)


def connectors(scaled, max_len=3):
    """All menu words of length 2..max_len summing to `scaled`, whose partial
    sums are pairwise non-collinear with 0 and scaled (exact check on the
    connector's own 3-4 points)."""
    out = []
    menu_set = set(MENU)
    for a in MENU:
        b = sub(scaled, a)
        if b in menu_set and b != a:
            pts = [(0, 0, 0), a, scaled]
            if _noncollinear(pts):
                out.append((a, b))
    if max_len >= 3:
        for a in MENU:
            r = sub(scaled, a)
            for b in MENU:
                c = sub(r, b)
                if c in menu_set:
                    p1 = a
                    p2 = (a[0] + b[0], a[1] + b[1], a[2] + b[2])
                    pts = [(0, 0, 0), p1, p2, scaled]
                    if len(set(pts)) == 4 and _noncollinear(pts):
                        out.append((a, b, c))
    return out


def _noncollinear(pts):
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if cross(sub(pts[j], pts[i]), sub(pts[k], pts[i])) == (0, 0, 0):
                    return False
    return True


def offset_collar():
    """All interior-point offsets (relative to segment start) across all
    connectors of all scaled menu steps. Anchors contribute offset 0."""
    offsets = {(0, 0, 0)}
    for s in MENU:
        scaled = apply_M(s)
        for w in connectors(scaled):
            acc = (0, 0, 0)
            for step in w[:-1]:  # interior partial sums only
                acc = (acc[0] + step[0], acc[1] + step[1], acc[2] + step[2])
                offsets.add(acc)
    return sorted(offsets)


def delta_set(offsets):
    """Chord perturbations d = o2 - o1, deduplicated as EXACT integer tuples
    (mod-3^W dedup would be unsound near the content cap)."""
    seen = set()
    for o1 in offsets:
        for o2 in offsets:
            seen.add((o2[0] - o1[0], o2[1] - o1[1], o2[2] - o1[2]))
    return sorted(seen)


MODQ1 = 3 ** (Q + 1)


def _primitive_class(w):
    """Primitive part of w reduced mod 3^(Q+1); None if content >= cap (the
    conservative bucket — never counted as separated)."""
    c, P = primitive3(w)
    if c >= W - 1:
        return None
    return (P[0] % MODQ1, P[1] % MODQ1, P[2] % MODQ1)


def _depth_from_classes(A, B):
    """Agreement depth (capped at Q+1) from primitive classes mod 3^(Q+1).
    Sound: cross is bilinear, so cross(U,V) mod 3^(Q+1) is determined by the
    classes; content below the cap is exact."""
    if A is None or B is None:
        return Q + 1  # conservative: treat as unresolved at the cap
    cx = (
        (A[1] * B[2] - A[2] * B[1]) % MODQ1,
        (A[2] * B[0] - A[0] * B[2]) % MODQ1,
        (A[0] * B[1] - A[1] * B[0]) % MODQ1,
    )
    if cx == (0, 0, 0):
        return Q + 1
    c = 0
    x, y, z = cx
    while x % 3 == 0 and y % 3 == 0 and z % 3 == 0:
        x //= 3
        y //= 3
        z //= 3
        c += 1
    return c


def transition_census(u, v, deltas):
    """For unresolved pair (u, v) at depth j0 >= 1, classify ALL single-level
    transitions (u, v) -> (Mu + d1, Mv + d2), exactly, via independent
    class-bucketing of each side.

    Returns (j0, counts): counts[key] = number of (d1, d2) pairs with
      separated: j' = 0;  down: 0 < j' < j0;  same: j' = j0;  up: j' > j0.
    """
    # Guard (adversarial-verification finding): the content cap makes j0
    # inexact for chords with 3-content >= W-1, which would fabricate
    # spurious rank-down transitions. Realized walk chords have content <= 2.
    assert content3(u) <= W - 2 and content3(v) <= W - 2, (
        "transition_census requires chord 3-content <= W-2; raise W for "
        "deeper inputs"
    )
    j0 = agreement_depth(u, v)
    Mu = apply_M(u)
    Mv = apply_M(v)

    def side_classes(base):
        cls = {}
        for d in deltas:
            w = (base[0] + d[0], base[1] + d[1], base[2] + d[2])
            key = _primitive_class(w)
            cls[key] = cls.get(key, 0) + 1
        return cls

    cu = side_classes(Mu)
    cv = side_classes(Mv)
    counts = {"separated": 0, "down": 0, "same": 0, "up": 0}
    for A, na in cu.items():
        for B, nb in cv.items():
            j = _depth_from_classes(A, B)
            n = na * nb
            if j == 0:
                counts["separated"] += n
            elif j < j0:
                counts["down"] += n
            elif j == j0:
                counts["same"] += n
            else:
                counts["up"] += n
    return j0, counts
