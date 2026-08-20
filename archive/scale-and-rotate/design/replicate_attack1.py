"""Independent skeptical replication of the attack1 band72 jam claim.

Uses ONLY the reference legality path (gate_run.word_legal -> amplify193.
legal_against) for the constructor replay; the attacker's replay used
fast_legal. Verifies:
  1. crafted_band(Random(72),18) reproduces the claimed base word;
  2. base is triple-free AND stepwise-legal (=> reachable by find_base
     under adversarial rng shuffles: find_base takes first legal step of a
     shuffled menu);
  3. exact gate constructor replay (fragile-first (d24,i) order,
     shortest-first scan dom[:2000] then dom[2000:], reference legality)
     at level 1 reaches seg i=9 with NO legal word in the FULL domain;
  4. step 115 facts: d24, fragile?, domain contains length-5 words?;
  5. independent exhaustive ID-DFS to depth 4 (node budget, progress);
  6. dfs_fallback (constructor's last resort) finds a length-5 escape;
  7. band71 near-jam: worst exact availability across L1 == 2;
  8. menu/band bookkeeping: 18 fragile steps, band [2000,16000] count,
     min band d24.
Budget: single process; node counter printed; IDDFS budget 1e6 nodes.
"""
import sys, time, json
from random import Random

sys.path.insert(0, "/Users/erik/homelab/math193")
sys.path.insert(0, "/Users/erik/homelab/math193/design")
import os
os.chdir("/Users/erik/homelab/math193")

from gate_run import (load_domains, MENU, FRAGILE_CUT, word_interiors,
                      word_legal, dfs_fallback)
from erdos193 import first_disqualifier
from amplify193 import legal_against
from imbricate193 import apply
from amplify_rich import M_BAL3
from attack1_wave2 import crafted_band

CLAIMED_BASE = [64,77,22,107,8,64,107,46,28,115,1,83,16,95,77,19,98,40]
CLAIMED_71   = [2,115,98,5,83,46,100,14,89,118,28,16,100,14,46,115,14,113]

t0 = time.time()
doms, d24 = load_domains()
print(f"domains loaded {time.time()-t0:.0f}s", flush=True)

# --- 8. bookkeeping ---
frag = sorted(k for k, v in d24.items() if v < FRAGILE_CUT)
band = sorted(k for k, v in d24.items() if 2000 <= v <= 16000)
print(f"menu {len(MENU)} steps; fragile {len(frag)}; band[2000,16000] "
      f"{len(band)}; band d24 range {min(d24[k] for k in band)}"
      f"..{max(d24[k] for k in band)}", flush=True)
print(f"MENU[115]={MENU[115]}, d24[115]={d24[115]}, fragile={d24[115]<FRAGILE_CUT}",
      flush=True)
maxlen115 = max(len(w) for w in doms[115])
n5_115 = sum(1 for w in doms[115] if len(w) >= 5)
print(f"dom[115]: {len(doms[115])} words, max len {maxlen115}, "
      f"len>=5 words: {n5_115}", flush=True)
# fragile step gets len-5 layer?
fs = frag[0]
print(f"sample fragile step {fs}: d24 {d24[fs]}, dom size {len(doms[fs])}, "
      f"len5 words {sum(1 for w in doms[fs] if len(w)==5)}", flush=True)

# --- 1+2. base ---
ultra = {k for k, v in d24.items() if v == 46}
bandset = set(band)
bw = crafted_band(Random(72), 18, bandset, ultra, False)
print(f"base match claimed: {bw == CLAIMED_BASE}  ({bw})", flush=True)
pts = [(0, 0, 0)]
ok_stepwise = True
for si in bw:
    s = MENU[si]
    p = (pts[-1][0]+s[0], pts[-1][1]+s[1], pts[-1][2]+s[2])
    if not legal_against(pts, set(pts), p):
        ok_stepwise = False
    pts.append(p)
print(f"base stepwise-legal (find_base-reachable): {ok_stepwise}; "
      f"triple-free: {first_disqualifier(pts) is None}", flush=True)
xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; zs=[p[2] for p in pts]
box=(max(xs)-min(xs)+1, max(ys)-min(ys)+1, max(zs)-min(zs)+1)
print(f"base box {box}, {len(pts)} pts, density "
      f"{len(pts)/(box[0]*box[1]*box[2]):.3f}", flush=True)
nband = sum(1 for si in bw if si in bandset)
print(f"band steps in base: {nband}/{len(bw)}", flush=True)

# --- 3. exact reference replay of the repaired constructor, level 1 ---
anchors = [apply(M_BAL3, p) for p in pts]
assert len(set(anchors)) == len(anchors)
points = list(anchors)
point_set = set(anchors)
order = sorted(range(len(bw)), key=lambda i: (d24[bw[i]], i))
print(f"stitch order (i,d24): {[(i, d24[bw[i]]) for i in order]}", flush=True)
NODES = 0
jam = None
for pos, i in enumerate(order):
    si = bw[i]
    A, B = anchors[i], anchors[i+1]
    dom = doms[si]
    memo = {}
    chosen = None
    # exact gate choice rule (2000-cap + escalation == ordered full scan)
    for w in dom[:2000]:
        NODES += 1
        if word_legal(A, w, points, point_set, memo):
            chosen = w
            break
    if chosen is None:
        for w in dom[2000:]:
            NODES += 1
            if word_legal(A, w, points, point_set, memo):
                chosen = w
                break
    if chosen is None:
        # full exhaustive recount for certainty
        surv = 0
        memo2 = {}
        for w in dom:
            NODES += 1
            if word_legal(A, w, points, point_set, memo2):
                surv += 1
        jam = dict(pos=pos+1, of=len(order), i=i, step=si, d24=d24[si],
                   dstar=len(dom), survivors=surv, points=len(points),
                   A=A, B=B)
        print(f"JAM at order pos {pos+1}/{len(order)}, seg i={i}, step {si} "
              f"{MENU[si]}: {surv}/{len(dom)} survivors, "
              f"{len(points)} points placed, A={A} B={B}", flush=True)
        break
    ints = word_interiors(A, chosen)
    end = ints[-1] if ints else A
    s = MENU[chosen[-1]]
    assert (end[0]+s[0], end[1]+s[1], end[2]+s[2]) == B
    points.extend(ints)
    point_set.update(ints)
    print(f"  pos {pos+1}: seg i={i} step {si} d24={d24[si]} -> word len "
          f"{len(chosen)}", flush=True)
print(f"replay nodes {NODES}, {time.time()-t0:.0f}s", flush=True)

result = {"jam": jam and {k: (list(v) if isinstance(v, tuple) else v)
                          for k, v in jam.items()}}

if jam:
    # --- 5. independent exhaustive IDDFS to depth 4 ---
    BUD = 1_000_000
    nodes = [0]
    found = None
    for depth_limit in range(2, 5):
        seg_pts, seg_word = [], []
        def dfs(depth):
            nodes[0] += 1
            if nodes[0] > BUD:
                raise RuntimeError("budget")
            last = seg_pts[-1] if seg_pts else jam["A"]
            B = jam["B"]
            if max(abs(B[k]-last[k]) for k in range(3)) > depth*2:
                return False
            for si2, s2 in enumerate(MENU):
                p = (last[0]+s2[0], last[1]+s2[1], last[2]+s2[2])
                if p == B:
                    if depth == 1:
                        seg_word.append(si2)
                        return True
                    continue
                if depth > 1 and legal_against(points+seg_pts,
                                               point_set | set(seg_pts), p):
                    seg_pts.append(p)
                    seg_word.append(si2)
                    if dfs(depth-1):
                        return True
                    seg_pts.pop()
                    seg_word.pop()
            return False
        if dfs(depth_limit):
            found = list(seg_word)
            break
        print(f"  IDDFS depth {depth_limit}: exhausted, none "
              f"({nodes[0]} nodes)", flush=True)
    print(f"IDDFS<=4: found={found}, nodes={nodes[0]}", flush=True)
    result["iddfs4"] = {"found": found, "nodes": nodes[0]}

    # --- 6. constructor's dfs_fallback (its real last resort) ---
    w = dfs_fallback(jam["A"], jam["B"], points, point_set,
                     Random("gate-L1-s9"), maxlen=8)
    print(f"dfs_fallback escape: {w} (len {w and len(w)})", flush=True)
    result["dfs_fallback"] = w

# --- 7. band71 near-jam exact worst ---
bw71 = crafted_band(Random(71), 18, bandset, ultra, False)
print(f"band71 match: {bw71 == CLAIMED_71}", flush=True)
pts71 = [(0, 0, 0)]
for si in bw71:
    s = MENU[si]
    p = pts71[-1]
    pts71.append((p[0]+s[0], p[1]+s[1], p[2]+s[2]))
assert first_disqualifier(pts71) is None
anch = [apply(M_BAL3, p) for p in pts71]
points = list(anch); point_set = set(anch)
order = sorted(range(len(bw71)), key=lambda i: (d24[bw71[i]], i))
worst = None
for i in order:
    si = bw71[i]
    A, B = anch[i], anch[i+1]
    dom = doms[si]
    memo = {}
    surv = 0
    first = None
    for w in dom:
        NODES += 1
        if word_legal(A, w, points, point_set, memo):
            if first is None:
                first = w
            surv += 1
    assert first is not None
    if worst is None or surv < worst[0]:
        worst = (surv, i, si, len(dom))
    ints = word_interiors(A, first)
    points.extend(ints)
    point_set.update(ints)
print(f"band71 L1 worst exact: {worst[0]} survivors at seg {worst[1]} "
      f"step {worst[2]} {MENU[worst[2]]} of {worst[3]}", flush=True)
result["band71_worst"] = {"survivors": worst[0], "seg_i": worst[1],
                          "step_idx": worst[2], "dstar": worst[3]}
print(f"TOTAL word-legality checks {NODES}, wall {time.time()-t0:.0f}s",
      flush=True)
print("REPLICATION RESULT:", json.dumps(result, default=str), flush=True)
