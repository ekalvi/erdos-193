# Referee audit: proposed 3-adic reachable-secant depth

**Auditor:** OpenAI Codex
**Audited Git object:** `de57e6761d3abf8ce916d8b3383ab58fe71f4b75`
**Disposition:** **PROVED — STOP CONDITION 6**
**Scope:** source/history audit, exact algebra, representation counterexamples, and replay of the repository's existing macrocycle certificate. No guarded birth census or alternate-history search was started after the stop condition fired.

## 1. Referee verdict

**PROVED.** The quadratic form

\[
q(g)=3g_y^2-g_yg_z+3g_z^2
\]

is repository-backed, and its transport identity is exact.

**REFUTED.** The raw scalar

\[
\min(v_3(g_x),v_3(q(g)))
\]

is not a geometric-line invariant. The same line represented by `g=(1,1,0)` and `3g=(3,3,0)` has raw depths `0` and `1`.

**PROVED.** The repository does not propose that raw scalar as a theorem. Its rank-facing `g` is a canonical primitive affine-line direction in a Plücker token `(g,mu)`. The only implemented equivalent scalar is

```text
min(v3(g_x)//2, (v3(q(g))-1)//4),
```

and it is used only as a positive control for one abstract latent family.

**PROVED.** That latent family has an exact fixed-macrocycle countdown, but the repository repeatedly states that its lines have not been proved to be secants born from two endpoints in a reachable legal ordered-path history.

**PROVED.** No repository source derives a universal reachable-newborn bound, a strict silent-transition decrease, or a finite promotion theorem from `q`-depth. The general plan instead requires contact residuals, affine moment, correlated address/control, and a future-congruence/SCC proof.

**PROVED — STOP CONDITION 6.** The universal reachable-secant rank in the question is an extrapolation from a fixed-family diagnostic, not a repository-backed incidence-lifetime theorem. Per the requested stop protocol, phases requiring major L5/L6 or alternate-history computation were not run.

## 2. Exact source and history audit

### 2.1 Origin timeline

| Classification | Commit | Date | What entered |
|---|---|---|---|
| **PROVED source fact** | `00fb71108a0c886d74af72965e599737c99f1e96` | 2026-07-15 | The invariant positive form `Q_full=x^2+6y^2-2yz+6z^2=x^2+2q(y,z)` and `M^T Q_full M=9Q_full`. This was a metric/bounded-distortion object, not a secant lifetime rank. |
| **PROVED source fact** | `927b754d036607fe8e376cc9e7af7bbedfc66029` | 2026-07-18 | The projective ratio `J=q/r^2`, invariant-cone guards, and latent carried-line obstruction. |
| **EXACT FINITE source fact** | `ee404916326738008f2605ec93c2bb0e6884aa84` | 2026-07-19 | Guarded L6 audit pin using the same cone polynomial. |
| **EXACT FINITE source fact** | `681c851690376d4be70cb23f4ecc5d914c6eafc3` | 2026-07-19 | Role-first L5 range merge using the cone polynomial. |
| **EXACT FINITE source fact** | `d412d39bbb387638085e9d39f9f6cfa9b1e757da` | 2026-07-28 | Consecutive guarded L5→L6 transition and finite-spectrum inheritance statement. |
| **PROVED source fact** | `94ab4a9eda85ad918f451a7d9e10953b276cf086` | 2026-07-29 | Expository site summary of the guarded cone result. |
| **PROVED source fact** | `de57e6761d3abf8ce916d8b3383ab58fe71f4b75` | 2026-07-29 | The first explicit scalar latent depth, exact macrocycle algebra, finite residue census, and independent verifier. |

**PROVED.** The exact raw expression `min(v3(gx),v3(q(g)))` occurs nowhere in the audited history. The only source-level scalar combining both channels is the weighted latent-family expression at `design/padic_macrocycle_lift.py:509`, independently repeated at `design/verify_padic_macrocycle_lift.py:321` and serialized in `design/padic-macrocycle-lift-summary.json`.

The complete machine-readable commit/file inventory is in `padic-reachable-secant-depth-audit-summary.json` under `source_audit.history`.

### 2.2 Every current explicit `q`, `J`, or cone-polynomial source

The 28 current sources are partitioned below by the meaning of their direction argument. The partition is checked exactly by the independent verifier.

#### Guarded finite endpoint chords

**EXACT FINITE.** These evaluate the homogeneous cone equation on the raw endpoint difference and store a canonical primitive direction/moment when a line key is required. Their domain is a fixed finite L5/L6 pair or birth scan, not all reachable histories.

```text
design/GUARDED-L5-L6-TRANSITION.md
design/guarded_l5_l6_common.py
design/guarded_l5_to_l6.py
design/lattice-T-projective-spectrum-census-summary.json
design/lattice_t_l5_cone_guard_audit.py
design/lattice_t_l6_cone_birth_guard.py
design/lattice_t_l6_cone_guard_audit.py
design/lattice_t_l6_cone_guard_pin_report.py
design/lattice_t_projective_spectrum_census.py
design/lattice_t_projective_spectrum_diagnostic.py
```

#### Abstract holonomy or reveal descriptors

**EXACT FINITE.** Here the argument is a canonical primitive rational direction from a fixed point or pulled-back candidate. It need not be an endpoint difference. Physical secant birth, global legality, or repeatability is explicitly outside the result.

```text
design/lattice_t_role_first_holonomy_reachability.py
design/lattice_t_role_first_l5_range_merge.py
design/lattice_t_short_return_holonomy.py
```

#### Abstract carried-line obstructions

**PROVED.** Here `g` is a canonical primitive affine-line direction and must be paired with its Plücker moment. The domain includes silent and returning integer lattice lines on fixed geometric policies, but not proved reachable secants.

```text
design/LATENT-REENTRY-OBSTRUCTION.md
design/nonx-cycle-invariant-certificate-summary.json
design/nonx-latent-reentry-certificate-summary.json
design/nonx_cycle_invariant_certificate.py
design/nonx_latent_reentry_certificate.py
```

#### Primitive Plücker operator and open plan

**PROVED.** These define exact general line-token transport. Their positive reachable-birth/rank claims are explicitly requirements or conjectural gates, not theorems.

```text
design/FAR-SECANT-BIRTH-OPERATOR.md
design/FAR-SECANT-RANK-LEMMA.md
design/GHOST-LANGUAGE-AUTOMATON.md
design/ORDERED-PATH-SAFETY-GATE.md
design/UNCONDITIONAL-INDUCTION-PLAN.md
```

#### Fixed latent-depth positive control

**PROVED algebra / EXACT FINITE regression.** These use canonical primitive `g_n=N^(2n)(55,34,18)`. The algebra is all-depth; the committed regression ends at depth 16. Reachable secant birth is explicitly not proved.

```text
design/padic-macrocycle-lift-summary.json
design/padic_macrocycle_lift.py
design/verify_padic_macrocycle_lift.py
```

#### Expository summaries

**PROVED source fact.** These add no theorem and inherit the scopes above.

```text
REPORT.md
viz/proof-steps.html
```

### 2.3 Full invariant-form ancestors

**PROVED source fact.** The following 32 files contain the older equivalent full form `Q_full=x^2+2q` or its exact similarity identity. These occurrences concern metric similarity, clearance, or covering unless also listed above; they do not define the proposed secant lifetime rank.

```text
CONDITIONAL-THEOREM.md
PROOF-SKELETON.md
REPORT.md
design/FAR-SECANT-BIRTH-OPERATOR.md
design/FAR-SECANT-RANK-LEMMA.md
design/GHOST-LANGUAGE-AUTOMATON.md
design/arch_sep/arch_omega_reconcile.py
design/arch_sep/clearance-L7.log
design/arch_sep/clearance-L8.log
design/arch_sep/geometric_clearance.py
design/lemma/ahlfors/VERDICT.json
design/lemma/ahlfors/ahlfors-round.json
design/lemma/ahlfors/route3-qmetric-CONCLUSION.json
design/lemma/ahlfors/route3_qmetric.py
design/lemma/dim/fractal-round.json
design/lemma/dim/route1_affinity.py
design/mprime/forcing_and_walk.py
design/osc/closure_multiplicity.py
design/osc/dg_closure_uniform.py
design/osc/neighbor_type_automaton.py
design/osc/nuniform_covering_bound.py
design/osc/tight_worstcase.py
design/osc_decide/SUMMARY.json
design/osc_decide/carry_automaton.py
design/osc_decide/lineB_min_sep.py
design/osc_decide/touch_overlap.py
design/osc_decide/v3_closer.py
design/tight/bound2_crosslevel.py
design/tight/bound2_induction.py
erdos-193-conditional-resolution.md
lineA_grouped_scales.py
lineA_margins.py
```

## 3. Algebra audit

For `g=(x,y,z)`,

\[
Mg=(3x,-3z,3y-z).
\]

Therefore

\[
\begin{aligned}
q(Mg)
 &=3(-3z)^2-(-3z)(3y-z)+3(3y-z)^2\\
 &=27y^2-9yz+27z^2\\
 &=9q(g).
\end{aligned}
\]

**PROVED.** `q(Mg)=9q(g)` is an integer polynomial identity. The constructor checks coefficient vectors; the verifier independently checks `M^T Q_lat M=9Q_lat` over exact `Fraction` arithmetic.

**PROVED.** For an exact carried chord `d_k=M^k d_0`,

\[
v_3((d_k)_x)=v_3((d_0)_x)+k,
\qquad
v_3(q(d_k))=v_3(q(d_0))+2k.
\]

**PROVED.** This statement is about an unnormalized exact chord. For the repository's canonical primitive direction,

\[
g'={\varepsilon Mg\over t},\qquad t=\gcd(Mg)\in\{1,3,9\},
\]

so

\[
v_3(g'_x)=v_3(g_x)+1-v_3(t),
\qquad
v_3(q(g'))=v_3(q(g))+2-2v_3(t).
\]

The automatic-growth formula and the repository's primitive `g` are not interchangeable.

## 4. Representation audit

| Representation | Definition | Referee finding |
|---|---|---|
| Exact chord | `d=b-a` | **PROVED:** retains endpoint separation and obeys `d'=Md` under pure common carriage. It is not a geometric-line key because nonzero scalar multiples define the same line. |
| Primitive integer chord | `g=canonprim(b-a)` | **PROVED:** canonical projective direction. With `mu=a×g`, it determines the exact affine lattice line. It removes arbitrary representation scaling but not endpoint genealogy. |
| Genealogical pullback | `M^(-k_genealogical)(b-a)` | **PROVED definition:** legitimate only when joint endpoint provenance proves `k_genealogical` common inherited affine scales. |
| Maximal algebraic pullback | `M^(-k_algebraic)(b-a)` integral, maximal `k_algebraic` | **PROVED definition:** a divisibility property of the chord, not an ancestry fact. It may factor accidental cancellation or a newborn residual. |

**REFUTED.** Raw depth is representation-independent. Exact witness:

| Representative | `q` | `v3(gx)` | `v3(q)` | raw min | weighted min |
|---|---:|---:|---:|---:|---:|
| `(1,1,0)` | 3 | 0 | 1 | 0 | 0 |
| `(3,3,0)` | 27 | 1 | 3 | 1 | 1 |
| `(9,9,0)` | 243 | 2 | 5 | 2 | 2 |

**PROVED.** Projective representation dependence can be repaired by setting

\[
c=\min_i v_3(g_i),\quad
v_x^*=v_3(g_x)-c,\quad
v_q^*=v_3(q(g))-2c,
\]

which is equivalent, for these valuations, to using the 3-primitive direction. This repairs only the choice of representative; it does not prove a future-return bound.

**PROVED abstract witness / CONJECTURED reachability.** For stipulated unrelated integer endpoints `(0,0,0)` and `(3,0,0)`, genealogical depth is `0`, while maximal algebraic depth is `1` because `M^-1(3,0,0)=(1,0,0)` but `M^-2(3,0,0)=(1/3,0,0)`. This proves that definitions C and D can differ as mathematical definitions. The audit does not claim that this stipulated provenance pair is a reachable guarded birth.

**PROVED.** Exact future lattice-line incidence is preserved by either `(a,g)` with exact base point and nonzero direction or the canonical primitive Plücker pair

\[
(g,\mu),\qquad \mu=a\times g.
\]

Direction valuations alone discard affine offset, phase/cursor, and endpoint provenance; they cannot predict exact candidate incidence.

## 5. Canonical birth and provenance

The repository-backed birth rule is exact.

**PROVED.** A secant is born once, when its later endpoint is inserted. If a selected connector word inserts interiors `I_w`, then before reframing

\[
E^+=E\cup I_w,
\]

\[
L^+=L
 \cup\{\operatorname{line}(i,e):i\in I_w,e\in E\}
 \cup\{\operatorname{line}(i,j):i,j\in I_w,i<j\}.
\]

This covers anchor/old–connector births and same-word connector–connector births. Cross-word connector pairs are old–new births when the later word inserts its endpoint.

**PROVED.** An inherited anchor–anchor line is not reborn. A deep–deep line was born when its later endpoint was inserted and is merely carried. Reconstructing it after an abstraction discarded it is an import operation, not a physical birth.

**PROVED.** The required distinctions are:

- `birth`: insertion of the later endpoint;
- `carriage`: transport of an already-born endpoint pair through a common affine descendant map;
- `cursor import`: first exposure to a local retained state after an unrelated same-level frame change;
- `current effect`: at least one current candidate atom lies on the line;
- `silent transport`: current exact candidate mask is empty while the line token is retained and transported;
- `return/reactivation`: a later exact candidate mask becomes nonempty;
- `promotion`: placement of a proved recurrent future-congruence class into a finite exact retained block.

**PROVED.** For a purely carried exact endpoint pair through `j` common linear scales,

\[
d_{current}=M^j d_{birth},\qquad M^{-j}d_{current}=d_{birth}.
\]

For canonical primitive directions, scalar contents must be divided at every transition; the exact chord identity must not be silently substituted for the primitive direction update.

## 6. Exact transport equations and the fatal rank mismatch

Let one endpoint update by `a'=Ma+delta_a` and another by `b'=Mb+delta_b`. Put

\[
d=b-a,\qquad \eta=\delta_b-\delta_a.
\]

Then

\[
d'=Md+\eta,
\qquad
d'_x=3d_x+\eta_x.
\]

**PROVED.** Pure carriage is exactly `eta=0` together with the same inherited affine map for both endpoints. A nonzero `eta` is a birth/residual update, even if accidental divisibility makes `d'` algebraically pull back through `M`.

**PROVED.** Inverse transport of the exact chord is integral exactly when `d'-eta` lies in `M Z^3`. Since

\[
M^{-1}(x,y,z)=\left(x/3,(3z-y)/9,-y/3\right),
\]

this requires `3|x`, `3|y`, and `9|(3z-y)`. Algebraic integrality does not certify common endpoint ancestry.

For an affine line `(g,mu)` in a corridor frame with common prefix control `c`, the repository's exact primitive transition is

\[
g'={\varepsilon Mg\over t},
\qquad
\mu'={\varepsilon\operatorname{cof}(M)(\mu-c\times g)\over t},
\qquad t=\gcd(Mg).
\]

For a same-level cursor displacement `Delta`,

\[
g'=g,
\qquad
\mu'=\mu-\Delta\times g.
\]

A candidate site `x` is hit exactly when

\[
x\times g=\mu.
\]

**PROVED.** A contact is silent at a transition iff no candidate site in the current exact corridor satisfies that equation. It returns after a future correlated edge string `alpha` iff a pulled-back ghost site satisfies

\[
\Phi_\alpha(x)\times g=\mu.
\]

This depends on `mu`, the cursor/control string, phase, and candidate site—not on direction valuation alone.

**REFUTED.** The proposed forced-scale residuals form a strict carriage countdown. For `d_0=(1,1,0)` and `d_k=M^k d_0`, the exact records are

| `k` | `d_k` | `v3(dx)` | `v3(q)` | `rx=v3(dx)-k` | `rq=v3(q)-2k` |
|---:|---|---:|---:|---:|---:|
| 0 | `(1,1,0)` | 0 | 1 | 0 | 1 |
| 1 | `(3,0,3)` | 1 | 3 | 0 | 1 |
| 2 | `(9,-9,-3)` | 2 | 5 | 0 | 1 |
| 3 | `(27,9,-24)` | 3 | 7 | 0 | 1 |

The birth pullback and the residual pair are exactly constant. They remove inherited scale; they do not measure elapsed time or remaining first-return time.

**CONJECTURED.** Connector offsets can reset, increase, or cancel x-depth through `3d_x+eta_x`; the same issue occurs in the full contact residual. The audit did not enumerate the legal offset alphabet because STOP CONDITION 6 fired before the requested x laboratory. No legal-reachability claim is made from the abstract affine equation alone.

## 7. What is actually proved about lifetime

**PROVED.** For

\[
g_n=N^{2n}(55,34,18),\qquad N=9M^{-1},
\]

one has

\[
v_3((g_n)_x)=2n,
\qquad
v_3(q(g_n))=4n+1.
\]

Consequently

\[
D_{latent}(g_n)
=\min\left(\left\lfloor{v_3((g_n)_x)\over2}\right\rfloor,
{v_3(q(g_n))-1\over4}\right)=n.
\]

Under the fixed primitive `M^2` line transition, `M^2g_n` has content `81` and canonical primitive direction `g_(n-1)`. The associated affine line is silent and returns after the exact fixed-macrocycle countdown established in `LATENT-REENTRY-OBSTRUCTION.md`.

**PROVED scope boundary.** These are genuine integer lattice lines, but the repository has not proved that any `L_n` is a secant of two placed points in a reachable globally legal history. Thus this is a positive control for a candidate rank mechanism, not the required birth theorem.

**EXACT FINITE.** `design/padic-macrocycle-lift-summary.json` covers 66,429 projective residue edges through modulus `3^5` and checks the latent record stream through depth 16. Its independent verifier reproduced payload SHA-256 `6ef9b78dfe8760d9e152c1bf05722ff0dfff628e0e4bf7e317f832cc7daed8f6`.

**REFUTED.** The guarded L5→L6 cone census supplies a universal transition law. It is exact for one chronology only.

**CONJECTURED.** A contact-residual/address rank may exist after a complete singular-component and reachable-birth theorem. The repository plan explicitly treats that as future work.

## 8. Zero and recurrent channels

Use `v3(0)=infinity` in any total implementation.

**PROVED.** Over integer directions, `q(g)=0` iff `g_y=g_z=0`; this is the x-parallel direction channel represented primitively by `(1,0,0)`.

**REFUTED terminology.** `g_x=0` is not the x-parallel channel. For example `(0,1,0)` has `g_x=0` and `q=3`; it lies in the lateral plane. The simultaneous nonzero locus `g_x=q(g)=0` exists only over the relevant 3-adic extension, not as a nonzero rational/integer direction.

**PROVED.** Exact recurrent channels cannot be assigned a finite countdown merely by replacing infinity with a cap. They require a proved finite promoted future-congruence class or a reachability exclusion.

## 9. Desired four-part result: disposition

1. **CONJECTURED:** uniformly bounded normalized residual depth for every reachable newborn. No such theorem is present.
2. **REFUTED for the proposed birth-normalized scalar:** pure-carriage residuals are constant. **CONJECTURED** for a different contact-residual/address rank.
3. **CONJECTURED:** every non-decreasing or recurrent channel enters a finite promoted class. Existing x and non-x audits expose recurrent behavior but do not prove finite universal promotion closure.
4. **REFUTED as an implication from bounded scalar rank alone:** rank does not bound simultaneous multiplicity, occupancy, births, imports, offsets, or whole-word correlations. **CONJECTURED** after all those additional finite closures are independently proved.

## 10. Why bounded rank is not finite state

**REFUTED.** `rank in {0,...,R}` implies a finite safety abstraction. Even infinitely many distinct lines can share rank zero, and each may have a different moment, owner/address, future right language, or killed-word mask.

**PROVED requirement inventory.** A sound finite abstraction still needs finite, closed representations for:

- affine line offsets/moments and base-point phase;
- endpoint occupancy and exact collision information;
- multiplicity and simultaneous coexistence;
- all old–new, same-word new–new, and cross-word births;
- near/far and far/far pair formation;
- whole-word correlation rather than independent atom marginals;
- unrelated cursor imports and zero-mask returns;
- owner/address-shell information and joint endpoint ancestry.

**PROVED scope boundary.** The existing x-parallel Bellman core addresses a synchronized carried x-line channel. Repository sources explicitly exclude occupancy, births, unrelated cursor jumps, and non-x secants from that theorem.

## 11. Corrected theorem statement

**PROVED.** Let `g_n=N^(2n)(55,34,18)` and represent each direction canonically primitive. Then

\[
v_3((g_n)_x)=2n,
\qquad v_3(q(g_n))=4n+1,
\qquad D_{latent}(g_n)=n,
\]

and the fixed primitive `M^2` line transition sends `g_n` to `g_(n-1)`. This is an exact theorem for the repository's abstract integer latent-line family. It is not a reachable-secants theorem and supplies neither a uniform newborn bound nor a finite safety controller.

No stronger corrected reachable-secant theorem is warranted.

## 12. Remaining lemmas

1. **CONJECTURED:** canonical joint-endpoint provenance and a theorem identifying the legitimate genealogical scale.
2. **CONJECTURED:** exact correlated contact-residual transition for every legal stitch, whole word, and cursor move.
3. **CONJECTURED:** a uniform reachable-newborn residual bound covering every birth channel.
4. **CONJECTURED:** strict, bounded-block, lexicographic, or amortized decrease for every reachable silent transition outside promoted classes.
5. **CONJECTURED:** finite exact promotion of every reachable recurrent SCC, including moments and future masks.
6. **CONJECTURED:** finite occupancy/multiplicity closure under births, joins, and imports.
7. **CONJECTURED:** a correlated whole-word poison-mask greatest fixed point with positive availability.

## 13. Required four answers

### What exactly is `g`?

**PROVED.** In the repository's rank proposal, `g` is the canonical primitive affine-line direction in a Plücker token `(g,mu)`. Some homogeneous cone guards evaluate `q` on the raw chord `b-a`, which is harmless for cone equality. A genealogically normalized exact chord is a new object and must not be substituted silently.

### When exactly is the secant born?

**PROVED.** At insertion of its later endpoint. Old–new and same-word new–new lines are injected then. A cross-word connector pair is old–new at insertion of the later word's point. Carriage and cursor import are not rebirth.

### What inherited scale may legitimately be factored out?

**PROVED.** Arbitrary line-representation scale may be removed by canonical primitive normalization. An `M`-scale may be removed genealogically only when joint endpoint provenance proves common inherited carriage. Maximal algebraic integrality is not ancestry and cannot replace that proof.

### Why does the rank decrease or enter finite promotion during silent transport?

**PROVED negative answer.** No general reason has been established. Birth-normalized exact-chord valuations are constant. The fixed latent family decreases only after its specific canonical primitive macrotransition. No universal reachable silent-SCC promotion theorem exists.

## 14. Claim ledger

| ID | Classification | Claim |
|---|---|---|
| C1 | **PROVED** | `q(Mg)=9q(g)`. |
| C2 | **REFUTED** | Raw min depth is independent of chord representative. |
| C3 | **PROVED** | Primitive 3-content normalization repairs projective representation dependence only. |
| C4 | **PROVED** | Repository rank-facing `g` is primitive line direction, not exact chord. |
| C5 | **PROVED** | Weighted depth is the exact countdown on the abstract latent family. |
| C6 | **CONJECTURED** | Reachable newborns have a uniform corrected rank after singular promotion. |
| C7 | **REFUTED** | Birth-normalized residual valuations strictly decrease under pure carriage. |
| C8 | **EXACT FINITE** | Existing macrocycle certificate: 66,429 edges, modulus through `3^5`, depth 16. |
| C9 | **EXACT FINITE** | Guarded L5→L6 result covers one fixed chronology. |
| C10 | **REFUTED** | Bounded scalar rank alone implies bounded multiplicity or finite state. |
| C11 | **MEASURED** | No measurement is used as proof here; deeper rank/lifetime measurements were stopped. |

## 15. Artifacts and independent verification

### Deliverables

```text
design/PADIC-REACHABLE-SECANT-DEPTH-AUDIT.md
design/padic_reachable_secant_depth_audit.py
design/verify_padic_reachable_secant_depth_audit.py
design/padic-reachable-secant-depth-audit-summary.json
design/padic-reachable-secant-depth-witness.json
```

Canonical payloads:

```text
summary  ef01f0937873e3da322e50ab1ffdf70fa268563d26134ede105ef6d37424d6b8
witness  69465942289d18ec0108729d98be73674792c7af30f5dbd1a245fdc9dec99edb
```

### Signed estimate

```bash
python3 -B design/padic_reachable_secant_depth_audit.py estimate
```

Every progress line is explicitly prefixed:

```text
[OpenAI Codex][3-adic secant audit] ...
```

### Checkpointed run

Use a new checkpoint path for a fresh run:

```bash
python3 -B design/padic_reachable_secant_depth_audit.py run \
  --checkpoint /tmp/padic-reachable-secant-depth-audit-run.json
```

### Deterministic pause/resume smoke test

```bash
python3 -B design/padic_reachable_secant_depth_audit.py run \
  --checkpoint /tmp/padic-reachable-secant-depth-audit-pause.json \
  --summary /tmp/padic-reachable-secant-depth-audit-summary.json \
  --witness /tmp/padic-reachable-secant-depth-witness.json \
  --max-phases 2

python3 -B design/padic_reachable_secant_depth_audit.py run \
  --resume \
  --checkpoint /tmp/padic-reachable-secant-depth-audit-pause.json \
  --summary /tmp/padic-reachable-secant-depth-audit-summary.json \
  --witness /tmp/padic-reachable-secant-depth-witness.json
```

`--max-seconds N` also pauses at the next exact phase boundary. Each completed phase is atomically checkpointed. An interrupted in-progress phase is replayed; no partial phase is accepted. Code, audited Git object, and regex inputs are fingerprinted, so incompatible resumes fail closed.

### Independent verifier

```bash
python3 -B design/verify_padic_reachable_secant_depth_audit.py
python3 -B design/verify_padic_macrocycle_lift.py
```

Expected primary result:

```json
{"audited_head":"de57e6761d3abf8ce916d8b3383ab58fe71f4b75","auditor":"OpenAI Codex","claims":11,"explicit_q_files":28,"history_q_commits":6,"status":"verified","stop_condition":6,"summary_payload_sha256":"ef01f0937873e3da322e50ab1ffdf70fa268563d26134ede105ef6d37424d6b8","witness_payload_sha256":"69465942289d18ec0108729d98be73674792c7af30f5dbd1a245fdc9dec99edb"}
```

---

**Signed:** OpenAI Codex
**Referee action:** stop at condition 6; do not spend major compute on L5→L6 births or alternate histories until the contact-residual transition and reachable-birth definitions are settled.
