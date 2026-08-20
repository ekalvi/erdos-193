from chiral_accel import *

def hr(t): print("\n" + "=" * 70 + "\n" + t + "\n" + "=" * 70)

# ---- 1. CHIRAL MENUS (n=3) ----
hr("1. CHIRAL MENU CANDIDATES (n=3)")
menus = {
 "SQ4  square-climb":      [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1)],
 "SQ4b tilted-climb":      [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,2)],
 "HELIX5 climb+forward":   [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0)],
 "HEX6 hex-climb":         [(1,0,1),(0,1,1),(-1,1,1),(-1,0,1),(0,-1,1),(1,-1,1)],
 "SCREW6 handed":          [(2,1,1),(-1,2,1),(-2,-1,1),(1,-2,1),(1,0,0),(0,0,-1)],
 "MIN4 corner":            [(1,0,0),(0,1,0),(0,0,1),(1,1,1)],
}
for name, S in menus.items():
    try:
        chiral, ngrp, dets = is_chiral(S)
    except Exception as ex:
        print(f"{name:24s} ERROR {ex}"); continue
    negcl = negation_closed(S)
    gen = minors_gcd(S)
    chi = handedness_chi(S)
    print(f"{name:24s} chiral={chiral!s:5s} |Aut|={ngrp:2d} "
          f"improper={any(d==-1 for d in dets)!s:5s} neg-closed={negcl!s:5s} "
          f"generates_Z3={gen==1!s:5s}(g={gen}) chi={chi}")

# ---- 2. ACCELERATING EQUAL-MODULI MATRICES ----
hr("2a. n=3 accelerating block family  M3(a)=[[a,0,0],[0,0,-a^2],[0,1,-1]]")
for a in range(2, 8):
    M = M3(a)
    cp = charpoly(M)
    roots = durand_kerner(cp)
    mods = sorted(round(abs(z), 6) for z in roots)
    pb = matpow_scaled_norm(M, a, 40)
    print(f"a={a}: charpoly(lo->hi)={cp}  |eig|={mods}  "
          f"all~={a}?{all(abs(abs(z)-a)<1e-6 for z in roots)}  "
          f"power-bound(M/a)^<=40 = {pb:.3f}")

hr("2b. n=3 COUPLED (unimodular-conjugated, non-block) -- same spectrum")
for a in range(2, 6):
    M = M3_coupled(a)
    cp = charpoly(M)
    roots = durand_kerner(cp)
    print(f"a={a}: M={M}  charpoly={cp}  "
          f"|eig|={sorted(round(abs(z),4) for z in roots)}")

hr("2c. n=4 accelerating DOUBLE-ROTATION  (two irrational angles, no invariant line)")
for a in range(2, 8):
    # pick smallest valid distinct b,c
    bc = [x for x in range(1, 2*a) if block2_angle_ok(a, x)]
    if len(bc) < 2: print(f"a={a}: <2 valid angles"); continue
    b, c = bc[0], bc[1]
    M = M4(a, b, c)
    cp = charpoly(M)
    roots = durand_kerner(cp)
    mods = sorted(round(abs(z), 5) for z in roots)
    print(f"a={a} b={b} c={c}: |eig|={mods} all~={a}?"
          f"{all(abs(abs(z)-a)<1e-5 for z in roots)} "
          f"cos1={F(-b,2*a)} cos2={F(-c,2*a)}")

# ---- 3. WHY ACCELERATION: spiral (growing r) vs constant helix ----
hr("3. NON-STATIONARITY IS NECESSARY: constant helix has collinear triples, "
   "accelerating spiral does not")
# constant-radius rational-angle helix (square-climb analogue): expect collinear
ph = spiral_points(60, 40, 1.0, 3.0, pi/2)   # 90deg steps, no growth
ft = first_triple(ph)
print(f"constant helix (r=40,growth=1.0,ang=90deg): first triple = {ft} "
      f"({'COLLINEAR FOUND -> fatal' if ft else 'clean'})")
# accelerating spiral, irrational-ish angle
psp = spiral_points(60, 8, 1.06, 3.0, 2.3999632)  # growth>1, irrational angle
ft2 = first_triple(psp)
print(f"accel spiral   (r0=8,growth=1.06,ang~2.3999): first triple = {ft2} "
      f"({'clean over %d pts' % len(psp) if not ft2 else 'triple '+str(ft2)})")

# ---- 4. HELICAL BRIDGE T2 proof-of-concept ----
hr("4. T2 HELICAL BRIDGE: fixed chiral menu bridges a large gap, triple-free")
menu = menus["SCREW6 handed"]
for gap in [(30, 12, 9), (100, -40, 25), (0, 0, 90)]:
    best = None
    for turns in (2, 3, 4, 5):
        for rad in (6, 10, 16):
            for seed in range(3):
                pts, ok, reached = helical_bridge(gap, menu, rad, turns, seed)
                if ok and len(pts) > 3:
                    if best is None or len(pts) > best[0]:
                        best = (len(pts), turns, rad, reached, ok)
    print(f"gap={gap}: best triple-free helical bridge -> "
          f"{best[0] if best else 0} pts, turns={best[1] if best else '-'}, "
          f"rad={best[2] if best else '-'}, reached_exact={best[3] if best else '-'}")
