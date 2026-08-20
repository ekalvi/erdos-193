# Day-3 screen design panel (2026-07-16)
Verify code: design/mprime/dayscreen_verify.py  (exact integer; run PYTHONPATH=. python3)

## Rigorous absorbing-separation criterion
Omega(Mp,Mq,Mr)=cof(M).Omega. Let valuation prime p | r (r=contraction ratio, the
direction of geometric contraction; k=v_p(r)). Write cof(M')=p^a.U, U primitive.
ABSORBING (separation preserved under descent, OSC-consistent plateau)
  <=>  U invertible mod p  (rank 3 in GL_3(F_p)).
Facts (all exact-verified):
- det(cof)=det(M')^2=r^6  => v_p(det cof)=6k ALWAYS  => cof is NEVER invertible mod p
  (a>=1 forced). So the "a=0" ideal is IMPOSSIBLE whenever p|r.
- U full-rank => v_p(det cof)=3a=6k => a=2k EXACTLY.
- a=2k with U full rank <=> Smith normal form of M' over Z_p is p^k.I_3
  <=> M' = p^k . A with A integer, p ∤ det(A)  (M'/p^k invertible mod p).
- For a SIMILARITY M'=r.O': cof(M')=±r^2 O'^{-T}=±r.Q M' Q^{-1}, so primitive(cof) is
  p-adically GL-conjugate to primitive(M'); rank(U mod p)=rank(primitive(M') mod p).

## M_BAL3 baseline fingerprint (r=3 prime, p=3)
cof=[[9,0,0],[0,-3,-9],[0,9,0]]=3.N, a=1 (< 2k=2), rank(N mod 3)=1 (rank-deficient) => FAIL.
Twist cos=-1/6 (irrational, Niven) — so it passes similarity+twist, fails ONLY the screen.
Excess valuation E(g)=vp(cof^g.Omega)-a*g over primitive Omega: [0,2,3,3,3,3,3,3] (>0 => decay).

## Satisfiability
SATISFIABLE, but NOT for prime-power r. Escape requires r = p^k . m, gcd(m,p)=1, m>1,
with an integer similarity A of ratio m carrying the irrational twist, and M' = p^k . A
(pure homothety p^k hosts the p-adic valuation; twist lives in the coprime part).
Then cof(M')=p^{2k}.cof(A), cof(A) invertible mod p => PASS.
Prime-power r (e.g. M_BAL3 r=3): only prime is p; m coprime to p forces m=1 => A a signed
permutation => finite-order (rational) twist. FUNDAMENTALLY OBSTRUCTED for prime-power r.

## Candidate M' verified PASS
M'=2A, A=[[3,-4,0],[4,3,0],[0,0,5]] (ratio 5, twist arctan 4/3, cos=3/5 irrational);
r=10, screen p=2: cof=4.cof(A), a=2=2k, rank(U mod2)=3, E(g)=0 (plateau). PASS.
Pythagorean family A=[[a,-b,0],[b,a,0],[0,0,m]], a^2+b^2=m^2: all PASS at any p|(r=p^k.m), p∤m.

## CROSS-CHECK + IMPOSSIBILITY (2026-07-16, independent algebraic angle)
Scripts: design/mprime/multiprime_screen.py, impossibility_search.py, comparison_table.py
CRITICAL correction to the search agent's "SATISFIABLE / M'=2A escape":
the screen MUST pass at EVERY prime dividing r (design's own risk(2)). Applied fully:
  M'=2A (r=10): p=2 PASS (E=0 plateau) but p=5 FAIL rank(U mod5)=1, E(g)->3 -> DECAY.
  => M'=2A reproduces the EXACT M_BAL3 failure fingerprint at prime 5.
  Same for every p^k.A: fails at each prime dividing the twist ratio m (Pythag primes).
The agent repeated the original methodological error one meta-level up (screened only
the convenient prime p=2, missed p=5) -- identical to the missed day-3 warning.

IMPOSSIBILITY THEOREM (integer expand-and-twist similarity):
  Pass day-screen at ALL primes p|r  <=>  SNF_Z(M')=diag(r,r,r)=r.I
  <=>  M'=r.W with W integer  <=>  W=M'/r is an integral isometry of the invariant
  positive-definite lattice  <=>  W finite order  <=>  twist angle rational.pi (Niven).
  Therefore NO integer similarity with IRRATIONAL twist passes the full screen.
Empirical seal: 504 irrational-twist integer similarities M^TM=r^2 I (r=2..12, incl.
axis-free 3D-mixing quaternion rotations = design family (2)) -> 0 pass all primes.
Control: finite-order (rational-twist) r.(signed perm) all PASS all primes (SNF=rI).
CONCLUSION: under the multi-prime criterion the escape is FUNDAMENTALLY OBSTRUCTED;
the single-prime "PASS" of M'=2A is an artifact of screening the wrong (convenient)
prime. Caveat: if the OSC descent is governed by a SINGLE prime, M'=2A is a genuine
p=2 plateau -- but which single prime governs r=10 is unresolved and the geometric
ratio r involves all prime factors symmetrically in the scale r^{2g}.
