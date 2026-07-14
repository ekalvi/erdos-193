"""ATTACK 3 -- length-5 layer exhaustion, static analysis of dstar5_fragile.pkl.

Worst fragile step (2,2,-2): |D_2-4| = 46, |D_5| = 47,421, total 47,467 words.
Segment chord: A0 = (0,0,0) -> A1 = M.s = (6,6,8).

Kill model (exactly gate_run.word_legal semantics, single obstacle point P):
  (a) P equals an interior point of w                      [repeat / legal_against]
  (b) P lies on a line through TWO interiors of w          [E2 branch of word_legal]
  (c) some interior of w is collinear with (P, A0) or (P, A1)
      [legal_against: interior on a line through two placed points; the segment's
       own anchors are ALWAYS placed at stitch time]
Model A = (a)+(b) only (no anchor help), Model B = (a)+(b)+(c).

Outputs:
  1. correlation stats: distinct interior points/directions, top-coverage,
     sampled pairwise-sharing fractions.
  2. greedy set-cover hitting set (upper bound) + N/kmax lower bound, per model.

Budgets: candidate box Chebyshev<=BOXR around chord center; MAX_ROUNDS greedy
rounds; progress printed every round. Single process, single core.
"""
import pickle, sys, time
from array import array
from bisect import bisect_left
from math import gcd
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
import os
os.chdir("/Users/erik/homelab/math193")
from search193 import candidate_step_vectors

T0 = time.time()
MENU = candidate_step_vectors(2)
IDX = {s: i for i, s in enumerate(MENU)}
STEP = (2, 2, -2)
A0 = (0, 0, 0)
A1 = (6, 6, 8)          # M_BAL3 . (2,2,-2), verified
CX, CY, CZ = 3, 3, 4    # chord center
BOXR = 20               # candidate box: |coord - center|_inf <= BOXR
MAX_ROUNDS = 80
OFF = 64                # packing offset
MODEL = sys.argv[1] if len(sys.argv) > 1 else "B"

def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a)
    sys.stdout.flush()

# ---------- load words ----------
d4 = pickle.load(open("connector_domains4.pkl", "rb"))
dom24 = sorted(d4["domains"][IDX[STEP]], key=len)
d5 = pickle.load(open("dstar5_fragile.pkl", "rb"))
w5 = d5[STEP]
words = [tuple(MENU[i] for i in w) for w in dom24] + [tuple(w) for w in w5]
N = len(words)
log("words: |D2-4|=%d |D5|=%d total=%d model=%s" % (len(dom24), len(w5), N, MODEL))

def interiors(w):
    pts, x, y, z = [], 0, 0, 0
    for s in w[:-1]:
        x += s[0]; y += s[1]; z += s[2]
        pts.append((x, y, z))
    return pts

INT = [interiors(w) for w in words]
assert all(sum(c[i] for c in w) == A1[i] for w in words for i in range(3))

def prim(v):
    g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    v = (v[0] // g, v[1] // g, v[2] // g)
    if v[0] < 0 or (v[0] == 0 and (v[1] < 0 or (v[1] == 0 and v[2] < 0))):
        v = (-v[0], -v[1], -v[2])
    return v

def pack(p):
    return ((p[0] + OFF) << 14) | ((p[1] + OFF) << 7) | (p[2] + OFF)

def unpack(k):
    return ((k >> 14) - OFF, ((k >> 7) & 127) - OFF, (k & 127) - OFF)

# chord line points (unplaceable obstacles: collinear with A0,A1)
CHORD = set()
dch = prim((6, 6, 8))  # (3,3,4)
t = -20
while t <= 20:
    p = (dch[0] * t, dch[1] * t, dch[2] * t)
    CHORD.add(p); t += 1

# ---------- correlation statistics ----------
from collections import Counter
ptc = Counter()      # interior point -> #words (all 47,467)
dir0c = Counter()    # primitive dir(interior - A0) -> #words
dir1c = Counter()
INTSET = []
D0SET = []; D1SET = []
for ints in INT:
    s = set(ints); INTSET.append(s)
    for p in s: ptc[p] += 1
    d0 = set(prim(p) for p in s)
    d1 = set(prim((p[0] - 6, p[1] - 6, p[2] - 8)) for p in s)
    D0SET.append(d0); D1SET.append(d1)
    for d in d0: dir0c[d] += 1
    for d in d1: dir1c[d] += 1
log("distinct interior points: %d  (total interior slots %d)" %
    (len(ptc), sum(len(i) for i in INT)))
log("top-10 interior points (pt, #words, frac): %s" %
    [(p, c, round(c / N, 4)) for p, c in ptc.most_common(10)])
log("distinct A0-directions: %d ; top-5: %s" %
    (len(dir0c), [(d, c, round(c / N, 4)) for d, c in dir0c.most_common(5)]))
log("distinct A1-directions: %d ; top-5: %s" %
    (len(dir1c), [(d, c, round(c / N, 4)) for d, c in dir1c.most_common(5)]))

rng = Random(193)
SP = 100_000
sh_pt = sh_dir = 0
for _ in range(SP):
    i = rng.randrange(N); j = rng.randrange(N)
    while j == i: j = rng.randrange(N)
    if INTSET[i] & INTSET[j]: sh_pt += 1
    if (D0SET[i] & D0SET[j]) or (D1SET[i] & D1SET[j]): sh_dir += 1
log("sampled %d pairs: share interior POINT %.4f ; share anchor-DIRECTION %.4f"
    % (SP, sh_pt / SP, sh_dir / SP))

# ---------- build per-word candidate kill-point arrays ----------
LO = -OFF + 1
HI = OFF - 1

def line_pts(p, d, out):
    """lattice points of line p + t*d inside box, packed into set out"""
    # find t range per axis
    tlo, thi = -10**6, 10**6
    for ax in range(3):
        c = (CX, CY, CZ)[ax]
        if d[ax] == 0:
            if abs(p[ax] - c) > BOXR: return
        else:
            a = (c - BOXR - p[ax]) / d[ax]
            b = (c + BOXR - p[ax]) / d[ax]
            if a > b: a, b = b, a
            if a > tlo: tlo = a
            if b < thi: thi = b
    import math
    t = int(math.ceil(tlo - 1e-9))
    te = int(math.floor(thi + 1e-9))
    while t <= te:
        q = (p[0] + d[0] * t, p[1] + d[1] * t, p[2] + d[2] * t)
        if q not in CHORD and q != A0 and q != A1:
            out.add(pack(q))
        t += 1

CANDS = []
budget = 0
for wi in range(N):
    ints = INT[wi]
    cs = set()
    for p in ints:
        if max(abs(p[0] - CX), abs(p[1] - CY), abs(p[2] - CZ)) <= BOXR \
           and p not in CHORD:
            cs.add(pack(p))
    k = len(ints)
    for a in range(k):
        for b in range(a + 1, k):
            pa, pb = ints[a], ints[b]
            d = prim((pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]))
            line_pts(pa, d, cs)
    if MODEL == "B":
        for p in ints:
            line_pts(p, prim(p), cs)                                   # line(p,A0)
            line_pts(p, prim((p[0] - 6, p[1] - 6, p[2] - 8)), cs)      # line(p,A1)
    a = array("l", sorted(cs))
    CANDS.append(a)
    budget += len(a)
    if wi % 10000 == 0:
        log("build %d/%d  incidences so far %d" % (wi, N, budget))
log("build done: total (point,word) incidences = %d, avg %.1f/word"
    % (budget, budget / N))

# ---------- greedy set cover ----------
alive = bytearray([1]) * N
alive = bytearray(b"\x01" * N)
remaining = N
picks = []
kmax_first = None
for rnd in range(1, MAX_ROUNDS + 1):
    cnt = {}
    for wi in range(N):
        if not alive[wi]: continue
        for k in CANDS[wi]:
            cnt[k] = cnt.get(k, 0) + 1
    if not cnt:
        log("round %d: no candidate kills any remaining word -> STOP; %d words unkillable in box" % (rnd, remaining))
        break
    best = max(cnt, key=cnt.get)
    bc = cnt[best]
    if kmax_first is None: kmax_first = bc
    # kill
    killed = 0
    for wi in range(N):
        if not alive[wi]: continue
        a = CANDS[wi]
        i = bisect_left(a, best)
        if i < len(a) and a[i] == best:
            alive[wi] = 0; killed += 1
    remaining -= killed
    picks.append((unpack(best), bc, killed, remaining))
    log("round %2d: pick %s kills %d (frac %.4f) -> remaining %d"
        % (rnd, unpack(best), killed, killed / N, remaining))
    if remaining == 0:
        break

log("=" * 60)
log("MODEL %s RESULT: greedy hitting set size = %d (remaining %d), "
    "kmax(single point) = %d -> LB >= ceil(%d/%d) = %d"
    % (MODEL, len(picks), remaining, kmax_first, N, kmax_first,
       -(-N // kmax_first)))
log("picks: %s" % [(p, k) for p, k, _, _ in picks])
# sanity: mutual legality of picked points w.r.t. each other + anchors
pts = [A0, A1] + [p for p, _, _, _ in picks]
bad = 0
for i in range(len(pts)):
    for j in range(i + 1, len(pts)):
        for k in range(j + 1, len(pts)):
            ax, ay, az = pts[i]; bx, by, bz = pts[j]; cx2, cy2, cz2 = pts[k]
            ux, uy, uz = bx - ax, by - ay, bz - az
            vx, vy, vz = cx2 - ax, cy2 - ay, cz2 - az
            if uy * vz - uz * vy == 0 and uz * vx - ux * vz == 0 and ux * vy - uy * vx == 0:
                bad += 1
log("collinear triples among {A0,A1,picks}: %d  (0 => the obstacle set is itself triple-free)" % bad)
