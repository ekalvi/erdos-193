"""
ROUTE 1 - BALLISTIC SOJOURN.  Test the ballistic lower bound that yields a
LINEAR sojourn cap L(rho) <= (2/c)*rho.

Two candidate "ballistic" quantities over the walk chain W (a PATH):
  (E) endpoint displacement:  Gmin(n) = min_i |W(i+n)-W(i)|_inf
      -> ratio Gmin(n)/n.  Claim: this FAILS (recurrence: walk returns close
         to itself over long path-gaps => ratio -> 0).
  (D) segment DIAMETER:       Smin(n) = min_i diam_cheb( W[i..i+n] )
      -> ratio Smin(n)/n.  This is the RIGHT quantity: an arc that stays in a
         Cheb-rho ball (radius rho) has diameter <= 2*rho, so if Smin(n) >= c*n
         then any such arc has length n <= 2*rho/c, i.e. SOJOURN L(rho) <= (2/c)rho.
      diam_cheb of a contiguous segment = max_coord (max-min) via bounding box: O(1)/extend.

Also the exact SOJOURN law directly:  L(rho) = max{ n : Smin(n) <= 2*rho }.
"""
import sys, pickle, json
sys.path.insert(0, "/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_interiors
MENU = candidate_step_vectors(2)

def load_chain(level):
    d = pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl","rb"))
    an = d["anchors"]; w = d["words"]
    chain = [an[0]]
    for i in range(len(an)-1):
        chain.extend(word_interiors(an[i], w[i])); chain.append(an[i+1])
    return chain

def endpoint_ballistic(chain, Nmax):
    N = len(chain)
    G = {}
    for n in range(1, Nmax+1):
        best = None
        for i in range(0, N-n):
            a = chain[i]; b = chain[i+n]
            d = abs(a[0]-b[0])
            t = abs(a[1]-b[1]);  d = t if t>d else d
            t = abs(a[2]-b[2]);  d = t if t>d else d
            if best is None or d < best:
                best = d
        G[n] = best
    return G

def segment_diam(chain, Nmax):
    """Smin(n)=min_i cheb-diameter of contiguous segment [i,i+n] (n+1 points)."""
    N = len(chain)
    S = {}
    for n in range(1, Nmax+1):
        S[n] = 10**9
    for i in range(N):
        x0=x1=chain[i][0]; y0=y1=chain[i][1]; z0=z1=chain[i][2]
        jmax = min(i+Nmax, N-1)
        for n in range(1, jmax-i+1):
            p = chain[i+n]
            if p[0]<x0: x0=p[0]
            elif p[0]>x1: x1=p[0]
            if p[1]<y0: y0=p[1]
            elif p[1]>y1: y1=p[1]
            if p[2]<z0: z0=p[2]
            elif p[2]>z1: z1=p[2]
            dm = x1-x0
            t = y1-y0;  dm = t if t>dm else dm
            t = z1-z0;  dm = t if t>dm else dm
            if dm < S[n]:
                S[n] = dm
    return S

def sojourn_law(S, rho_max=12):
    """L(rho) = max{n : Smin(n) <= 2*rho}."""
    L = {}
    for rho in range(1, rho_max+1):
        thr = 2*rho
        best = 0
        for n, dm in S.items():
            if dm <= thr and n > best:
                best = n
        L[rho] = best
    return L

if __name__ == "__main__":
    Nmax = 40
    out = {"Nmax": Nmax, "levels": {}}
    for lv in (6, 7, 8):
        chain = load_chain(lv)
        S = segment_diam(chain, Nmax)
        L = sojourn_law(S, 12)
        # ballistic constant from diameter: c = min_n Smin(n)/n
        cvals = {n: S[n]/n for n in S}
        c_min = min(cvals.values())
        c_at = min(cvals, key=lambda n: cvals[n])
        # endpoint ballistic only for small level to show failure cheaply
        rec = {
            "N": len(chain),
            "Smin": {n: S[n] for n in range(1, Nmax+1)},
            "Smin_over_n": {n: round(S[n]/n, 4) for n in range(1, Nmax+1)},
            "ballistic_c_diam_min": round(c_min, 4),
            "ballistic_c_argmin_n": c_at,
            "sojourn_L": L,
            "L_over_rho": {rho: round(L[rho]/rho, 3) for rho in L},
        }
        out["levels"][lv] = rec
        print(f"L{lv}: N={len(chain)} c_diam_min={c_min:.4f} at n={c_at}", flush=True)
        print("  Smin(n)/n:", {n: round(S[n]/n,3) for n in range(1,21)}, flush=True)
        print("  sojourn L(rho):", L, flush=True)
    # endpoint failure demo on L6 only
    ch6 = load_chain(6)
    G = endpoint_ballistic(ch6, min(200, len(ch6)-1))
    Gr = {n: (G[n]/n if G[n] is not None else None) for n in G}
    out["endpoint_ballistic_L6"] = {
        "Gmin": {n: G[n] for n in sorted(G)},
        "Gmin_over_n": {n: round(Gr[n],4) for n in sorted(Gr)},
        "min_ratio": round(min(Gr.values()),4),
        "argmin_n": min(Gr, key=lambda n: Gr[n]),
    }
    print("ENDPOINT L6 min |disp|/n over n<=200:", out["endpoint_ballistic_L6"]["min_ratio"],
          "at n=", out["endpoint_ballistic_L6"]["argmin_n"], flush=True)
    json.dump(out, open("/Users/erik/homelab/math193/design/tight/route1_ballistic.json","w"), indent=1)
    print("WROTE route1_ballistic.json", flush=True)
