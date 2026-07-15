"""
ROUTE 3 (LOCAL-TIME / POTENTIAL). Does a scalar potential Phi:Z^3->R with
amortized drift bound the local time #{i: W(i) in B(q,rho)} = O(rho)?

The clean lemma we test:
  if Phi(W(j))-Phi(W(i)) >= delta*(j-i) - C0  for all i<j  (amortized ballistic in Phi)
  and Phi varies by <= K*rho across any Cheb-rho ball,
  then for indices i_1<...<i_m in a ball:  Phi(W(i_m))-Phi(W(i_1)) <= K*rho,
  and  >= delta*(i_m - i_1) - C0, so  i_m - i_1 <= (K*rho + C0)/delta
  and local time  m <= (i_m - i_1) + 1 <= (K*rho+C0)/delta + 1 = O(rho).

CRITICAL failure mode to expose: a scalar potential only sees the INDEX SPAN
i_m - i_1 (== the recurrence window W(2rho)), NOT the local time m.  If the walk
is recurrent, span >> m and the bound is useless (== the already-rejected
c <= W(2rho)+1 window bound).  We MEASURE span vs local time on the densest balls.

Candidate potential: Phi(p)=x = <p,u>, u=(1,0,0) the LEFT eigenvector of M with
eigenvalue 3 (u M = 3u exactly; M row0=(3,0,0)).  Under M: Phi(Mp)=3 Phi(p).
Measure per-step Delta-x distribution (drift), and the amortized-drift floor
   d(n) = min_i [Phi(W(i+n)) - Phi(W(i))]   (best possible delta if >0).
"""
import sys, pickle, json
from collections import defaultdict, Counter
sys.path.insert(0, "/Users/erik/homelab/math193")
from gate_run import word_interiors

def build_chain(pkl):
    st = pickle.load(open(pkl, 'rb'))
    anchors, words, pw = st['anchors'], st['words'], st['parent_word']
    chain = [anchors[0]]
    for i in range(len(pw)):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i+1])
    return chain

def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

def ball_indices(chain, grid, cell, q, rho):
    cx, cy, cz = q[0]//cell, q[1]//cell, q[2]//cell
    out = []
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                for j in grid.get((cx+dx,cy+dy,cz+dz), ()):
                    if cheb(chain[j], q) <= rho:
                        out.append(j)
    out.sort()
    return out

def arcs_of(idxs):
    arcs=[]; cur=[idxs[0]]
    for a in idxs[1:]:
        if a==cur[-1]+1: cur.append(a)
        else: arcs.append(cur); cur=[a]
    arcs.append(cur); return arcs

def analyze(level, pkl):
    chain = build_chain(pkl)
    N = len(chain)
    # repeats? (path => local time == distinct count only if injective)
    nrepeat = N - len(set(chain))
    res = {"level": level, "N": N, "repeated_vertices": nrepeat, "per_rho": {}}
    # potential drift, Phi = x-coordinate
    xs = [p[0] for p in chain]
    dx = [xs[i+1]-xs[i] for i in range(N-1)]
    from collections import Counter as C2
    res["dx_hist"] = dict(C2(dx))
    res["x_net_drift_total"] = xs[-1]-xs[0]
    res["x_range_total"] = max(xs)-min(xs)
    # amortized floor d(n)=min_i x(i+n)-x(i) for a few n
    dfloor={}
    for n in (5,10,20,40,80,160):
        if n<N:
            dfloor[n]=min(xs[i+n]-xs[i] for i in range(N-n))
    res["x_amortized_floor_min_over_i"]=dfloor  # if <=0 => not monotone-amortized in x

    for rho in range(1, 11):
        cell = rho
        grid = defaultdict(list)
        for i,p in enumerate(chain):
            grid[(p[0]//cell,p[1]//cell,p[2]//cell)].append(i)
        best = None  # densest ball
        maxspan_ratio = None
        for qi in range(N):
            q = chain[qi]
            idxs = ball_indices(chain, grid, cell, q, rho)
            m = len(idxs)
            span = idxs[-1]-idxs[0]
            arcs = arcs_of(idxs)
            rec = (m, span, len(arcs), qi)
            if best is None or m > best[0]:
                best = rec
        # recompute detail at the densest center
        m,span,nA,qi = best
        idxs = ball_indices(chain, grid, cell, chain[qi], rho)
        arcs = arcs_of(idxs)
        arclens = sorted((len(a) for a in arcs), reverse=True)
        # x-extent of the ball points and x span among visits
        xvals = [chain[j][0] for j in idxs]
        res["per_rho"][rho] = {
            "max_localtime_m": m,
            "index_span_at_densest": span,     # == realized recurrence window
            "span_over_m": round(span/m,1),
            "num_arcs": nA,
            "arc_lengths": arclens[:6],
            "x_extent_of_ball_pts": max(xvals)-min(xvals),  # <= 2rho always
            "potential_bound_if_delta_eq_dfloor": None,
        }
    return res

def main():
    files = [(6,'gate2-l7-construction-L6.pkl'),
             (7,'gate2-l7-construction-L7.pkl'),
             (8,'gate2-l7-construction-L8.pkl')]
    out={"levels":{}}
    for L,pkl in files:
        print("analyzing L%d..."%L, flush=True)
        out["levels"][L]=analyze(L, '/Users/erik/homelab/math193/'+pkl)
        r=out["levels"][L]
        print(" N=%d repeats=%d net_drift_x=%d range_x=%d"%(r["N"],r["repeated_vertices"],r["x_net_drift_total"],r["x_range_total"]))
        print(" x amortized floor (min_i x(i+n)-x(i)):", r["x_amortized_floor_min_over_i"])
        for rho in (2,5,8,10):
            d=r["per_rho"][rho]
            print("  rho=%2d  m=%3d  span=%5d  span/m=%6.1f  arcs=%d  arclens=%s"%(
                rho,d["max_localtime_m"],d["index_span_at_densest"],d["span_over_m"],d["num_arcs"],d["arc_lengths"]))
    json.dump(out, open("/Users/erik/homelab/math193/design/tight/route3_localtime.json","w"), indent=2, default=int)
    print("wrote route3_localtime.json")

if __name__=="__main__":
    main()
