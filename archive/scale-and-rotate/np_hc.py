"""
NP-HC side-state machinery (Stage-4 Step 2, winning design of the panel —
see design/step2-design-panel.json, Design 2 + grafts).

Side state sigma = (a, k, U): a = v_3(u) exact (a < A_CAP), k in {1..K_MAX}
digits of the primitive part held, U = (u/3^a) mod 3^k primitive.
Transition F(sigma, d): r = (3^a * (M U mod 3^k) + d) mod 3^{a+k};
t = v_3(r); E4 if r == 0 at horizon, E3 if t >= A_CAP; else
(a', k', U') = (t, min(K_MAX, a+k-t), (r/3^t) mod 3^{k'}).
Horizon conservation: a'+k' = min(a'+K_MAX, a+k). Carries are sound because
M is integral, d exact, and residues are of the UNNORMALIZED chord below the
horizon (upward-only carry flow) — the panel's Lemma A.

The ambient side space: 4 contents x (18,954 + 702 + 26) = 78,728 states.
"""
from __future__ import annotations

M = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
Q = 2
K_MAX = 3
A_CAP = 4  # a' >= 4 escapes (E3)

POW3 = [1, 3, 9, 27, 81, 243, 729, 2187]

# ---- side-state indexing -----------------------------------------------

# enumerate primitive residues per k; index = offset + rank
_PRIM = {}      # k -> list of U tuples
_PRIM_IDX = {}  # k -> {U: rank}
for k in (1, 2, 3):
    mod = POW3[k]
    lst = []
    for x in range(mod):
        for y in range(mod):
            for z in range(mod):
                if x % 3 or y % 3 or z % 3:
                    lst.append((x, y, z))
    _PRIM[k] = lst
    _PRIM_IDX[k] = {u: i for i, u in enumerate(lst)}

_K_OFFSET = {1: 0, 2: 26, 3: 26 + 702}
_PER_A = 26 + 702 + 18954  # 19,682
N_SIDE = 4 * _PER_A        # 78,728

E1, E2, E3, E4 = -1, -2, -3, -4  # escape codes (E1/E2 are pair-level)


def side_index(a, k, U):
    return a * _PER_A + _K_OFFSET[k] + _PRIM_IDX[k][U]


def side_unpack(idx):
    a, r = divmod(idx, _PER_A)
    for k in (3, 2, 1):
        if r >= _K_OFFSET[k]:
            return a, k, _PRIM[k][r - _K_OFFSET[k]]
    raise AssertionError


def v3_vec_mod(r, h):
    """valuation of residue vector r (each coord in [0, 3^h)) as element of
    (Z/3^h)^3; returns h if r == 0."""
    t = 0
    x, y, z = r
    while t < h and x % 3 == 0 and y % 3 == 0 and z % 3 == 0:
        x //= 3
        y //= 3
        z //= 3
        t += 1
    return t, (x, y, z)


def F(a, k, U, d):
    """Side transition. Returns side index or escape code."""
    h = a + k
    modh = POW3[h]
    modk = POW3[k]
    # M U mod 3^k
    mu0 = (M[0][0] * U[0] + M[0][1] * U[1] + M[0][2] * U[2]) % modk
    mu1 = (M[1][0] * U[0] + M[1][1] * U[1] + M[1][2] * U[2]) % modk
    mu2 = (M[2][0] * U[0] + M[2][1] * U[1] + M[2][2] * U[2]) % modk
    pa = POW3[a]
    r = ((pa * mu0 + d[0]) % modh, (pa * mu1 + d[1]) % modh, (pa * mu2 + d[2]) % modh)
    if r == (0, 0, 0):
        return E4
    t, stripped = v3_vec_mod(r, h)
    if t >= h:
        return E4
    if t >= A_CAP:
        return E3
    kp = K_MAX if (h - t) > K_MAX else (h - t)
    modkp = POW3[kp]
    Up = (stripped[0] % modkp, stripped[1] % modkp, stripped[2] % modkp)
    return side_index(t, kp, Up)


# ---- projective classification (for pair availability) ------------------

def proj3_class(U):
    """Projective class of primitive U mod 3 in P^2(Z/3): 13 classes.
    Canonical: first unit coordinate normalized to 1."""
    u = (U[0] % 3, U[1] % 3, U[2] % 3)
    for chart in range(3):
        if u[chart] % 3:
            inv = 1 if u[chart] == 1 else 2  # inverse mod 3
            return (
                chart,
                (u[0] * inv) % 3,
                (u[1] * inv) % 3,
                (u[2] * inv) % 3,
            )
    raise AssertionError


PROJ3_ALL = sorted({proj3_class(U) for U in _PRIM[1]})
PROJ3_RANK = {c: i for i, c in enumerate(PROJ3_ALL)}  # 13 classes
assert len(PROJ3_ALL) == 13
