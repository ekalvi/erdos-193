"""Independent verification of the refill maxima that drive C*, plus base-case
small-radius incidence for the full walk (needed for Q's domain [0.5,10])."""
import os, sys, pickle, random
os.chdir("/Users/erik/homelab/math193"); sys.path.insert(0, "/Users/erik/homelab/math193")
import gate_run


def build(level):
    d = pickle.load(open("gate2-l7-construction-L%d.pkl" % level, "rb"))
    anchors = d["anchors"]; words = d["words"]
    chain = [anchors[0]]; interiors = []
    for i in range(len(anchors) - 1):
        ints = gate_run.word_interiors(anchors[i], words[i])
        interiors.extend(ints); chain.extend(ints); chain.append(anchors[i + 1])
    return anchors, interiors, chain


def mc_realmax(points, rho, iters=400000, seed=0):
    """Monte-Carlo lower bound on sup_q #{pts in Cheb(q,rho)}: jitter centres
    near random points + local hill-climb on the 6 face positions."""
    rnd = random.Random(seed)
    cell = 2 * int(rho) + 2
    H = {}
    for p in points:
        H.setdefault((p[0] // cell, p[1] // cell, p[2] // cell), []).append(p)
    def cnt(q):
        kx, ky, kz = int((q[0]) // cell), int((q[1]) // cell), int((q[2]) // cell)
        n = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    b = H.get((kx + dx, ky + dy, kz + dz))
                    if b:
                        for p in b:
                            if abs(p[0]-q[0])<=rho and abs(p[1]-q[1])<=rho and abs(p[2]-q[2])<=rho:
                                n += 1
        return n
    best = 0; N = len(points)
    for _ in range(iters):
        p = points[rnd.randrange(N)]
        q = [p[0]+rnd.uniform(-rho,rho), p[1]+rnd.uniform(-rho,rho), p[2]+rnd.uniform(-rho,rho)]
        c = cnt(q)
        # a few random nudges
        for _ in range(6):
            q2 = [q[i]+rnd.uniform(-0.5,0.5) for i in range(3)]
            c2 = cnt(q2)
            if c2 > c: q, c = q2, c2
        if c > best: best = c
    return best


if __name__ == "__main__":
    for L in (6, 7):
        anc, inter, chain = build(L)
        print("L%d stitch=%d" % (L, len(inter)))
        for rho in (0.5, 1.0, 1.5, 2.0):
            print("  MC refill real-max rho=%.1f -> %d" % (rho, mc_realmax(inter, rho)))
    # base-case (full walk) small-radius incidence, real centres, via MC
    anc, inter, chain = build(5)
    print("L5 full-walk base, chain=%d" % len(chain))
    for rho in (0.5, 0.75, 1.0):
        print("  MC full real-max rho=%.2f -> %d  (target C*rho+1, C=6: %.1f)"
              % (rho, mc_realmax(chain, rho), 6*rho+1))
