"""Independent EXACT check of B_local at integer-W radii (rho=0.5,1,1.5,2).
For integer W=2rho, sup over real centres of #{pts in closed Cheb ball rho}
= max over integer min-corner c in Z^3 of #{pts in [c,c+W]^3}.
Compute by scattering each point into its (W+1)^3 candidate corners."""
import os, sys, pickle
os.chdir("/Users/erik/homelab/math193"); sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run

def build(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    interiors = []
    for i in range(len(anchors) - 1):
        interiors.extend(gate_run.word_interiors(anchors[i], words[i]))
    return interiors

def exact_corner_max(points, W):
    cnt = {}
    R = range(-W, 1)
    for (x, y, z) in points:
        for dx in R:
            cx = x + dx
            for dy in R:
                cy = y + dy
                for dz in R:
                    k = (cx, cy, z + dz)
                    cnt[k] = cnt.get(k, 0) + 1
    return max(cnt.values())

for L in (6, 7):
    inter = build(L)
    print("L%d stitch=%d" % (L, len(inter)))
    for rho in (0.5, 1.0, 1.5, 2.0):
        W = int(round(2 * rho))
        print("  EXACT-corner B_local(rho=%.1f, W=%d) = %d" % (rho, W, exact_corner_max(inter, W)), flush=True)

print("=== BASE CASE: full-walk real-centre incidence vs 6*rho+1 ===")
def build_chain(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = [anchors[0]]
    for i in range(len(anchors) - 1):
        chain.extend(gate_run.word_interiors(anchors[i], words[i])); chain.append(anchors[i+1])
    return chain
for L in (5,6,7):
    ch = build_chain(L)
    for rho in (0.5,1.0):
        W=int(round(2*rho)); v=exact_corner_max(ch,W)
        print("  L%d full B(rho=%.1f)=%d   6*rho+1=%.1f  %s"%(L,rho,v,6*rho+1,"OK" if v<=6*rho+1 else "FAIL"))
