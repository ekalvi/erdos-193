# Referee audit: the fixed 3-adic latent family and its macrocycle

**Audit date:** 2026-07-30
**Audited Git object:** `de57e6761d3abf8ce916d8b3383ab58fe71f4b75`
**Disposition:** **PROVED — STOP CONDITION 2**
**Supported Phase-9 outcome:** **F. INSUFFICIENT ABSTRACTION**

## 1. Executive finding

The repository contains one exact all-depth latent affine-line family and one exact two-word macrocycle on that family. It does **not** contain a finite promoted contact class or a construction-closed line-token automaton.

- **PROVED:** For
  \[
  M=\begin{pmatrix}3&0&0\\0&0&-3\\0&3&-1\end{pmatrix},\quad
  N=9M^{-1},\quad h=(55,34,18),
  \]
  the directions `g_n=N^(2n)h` and the affine moments defined below form an exact all-`n` family.
- **PROVED:** On the pinned phase cycle `8 -> 16 -> 8`, a complete normalized transition sends `L_n` to `L_(n-1)` for every `n>=1`.
- **PROVED:**
  \[
  R(g)=\min\left(\left\lfloor\frac{v_3(g_x)}2\right\rfloor,
  \left\lfloor\frac{v_3(q(g))-1}4\right\rfloor\right),
  \qquad q(g)=3g_y^2-g_yg_z+3g_z^2,
  \]
  satisfies `R(g_n)=n`. The first edge of the pinned macrocycle changes the displayed scalar by `-1`; the second changes it by `0`.
- **EXACT FINITE:** The audit independently regenerated all `66,429` committed projective residue edges through modulus `3^5`, with matching per-precision digests.
- **REFUTED:** Those `66,429` edges are not an inductive line-token countdown certificate. They are the sum of five separate finite-precision direction graphs. Their states omit the Plücker moment, exact primitive representative, phase/action, poison effect, birth/import data, occupancy, and provenance.
- **REFUTED:** The fixed family is not a finite promoted class. It is an infinite ranked orbit with infinitely many distinct reveal countdowns.
- **EXACT FINITE:** The committed L5–L8 known-template scan reports zero live secants in its tested translated family instances.
- **CONJECTURED:** No translated `L_n` is born in any globally legal reachable construction history.

The user-specified stop protocol therefore fires at **STOP CONDITION 2**: the `66,429`-edge result is bounded finite regression, not an inductive theorem. No new guarded-orbit census, alternate-history search, closure proof, or promotion synthesis was run after that determination.

## 2. Source and history reconstruction

### 2.1 Origin commits

**PROVED:** The family and the scalar entered the repository in different commits.

1. `927b754d036607fe8e376cc9e7af7bbedfc66029`, authored `2026-07-18T23:59:24-04:00`, subject `proof: harden ordered-path far-secant certificates`:
   - introduced the exact all-depth latent line family;
   - introduced its fixed-policy certificate and finite known-template birth probe;
   - stated the reachability boundary explicitly.
2. `de57e6761d3abf8ce916d8b3383ab58fe71f4b75`, authored `2026-07-29T23:28:20-04:00`, subject `proof: isolate 3-adic macrocycle lift`:
   - introduced the weighted scalar `R`;
   - introduced the bounded projective residue graphs;
   - introduced the depth-16 family regression and compact verifier.

The complete remaining matching history consists of three non-origin commits:

- `ee404916326738008f2605ec93c2bb0e6884aa84`, authored `2026-07-19T01:04:12-04:00`, `proof: freeze guarded L6 audit pins`: incidental same-cone use in `lattice_t_l6_cone_guard_pin_report.py`;
- `d412d39bbb387638085e9d39f9f6cfa9b1e757da`, authored `2026-07-28T23:34:53-04:00`, `proof: prepare consecutive guarded L5 to L6 gate`: incidental same-cone use in `audit_guarded_l5_to_l6.py` and `guarded_l5_l6_common.py`;
- `bac08af86dea84956f2476acef6354d8e17050e2`, authored `2026-07-29T22:36:13-04:00`, `docs: plan unconditional inductive proof`: expository macrocycle reference in `UNCONDITIONAL-INDUCTION-PLAN.md`.

The rank is therefore not the definition of the older family. It is a later scalar attached to that family.

### 2.2 Defining sources

**PROVED:** The theorem-bearing sources are:

| Source | Relevant lines at audited object | Role |
|---|---:|---|
| `design/LATENT-REENTRY-OBSTRUCTION.md` | 35–99, 101–203 | Exact affine line token, carried transition, fixed two-word cycle, all-`n` silence/re-entry theorem, reachability boundary |
| `design/nonx_latent_reentry_certificate.py` | 265–339, 349–500, 526–659 | Pinned words, exact candidate extraction, equal-`J` frontier, arithmetic proof, certificate construction |
| `design/nonx-latent-reentry-certificate-summary.json` | 1–126 | Compact all-`n` theorem and pinned-input commitments |
| `design/padic_macrocycle_lift.py` | 115–121, 186–228, 260–395, 398–481, 484–583, 634–756 | Primitive-normalization check, projective residue graph, exact token algebra, depth-16 regression |
| `design/verify_padic_macrocycle_lift.py` | 95–102, 151–176, 179–296, 299–413, 416–482 | Independent verifier for the compact bounded certificate |
| `design/padic-macrocycle-lift-summary.json` | 1–520 | Committed `66,429`-edge graph and depth-16 regression payload |
| `design/known_template_weighted_birth_probe.py` | 1–31, 130–151, 795–969 | Exact requested-line scan over finite L5–L8 ranges |
| `design/known-template-weighted-birth-probe-summary.json` | 146–205 | Committed zero-live-secant result in those ranges |

The defining executable symbols are:

- `nonx_latent_reentry_certificate.py`: `selected_policy_cycle`, `candidate_sites`, `affine_cycle_and_frontier`, `arithmetic_certificate`, and `run`;
- `padic_macrocycle_lift.py`: `canonical_primitive`, `normalization_certificate`, `inverse_lift_edge`, `functional_graph_stats`, `compute_precision`, `contact_model_certificate`, `integer_line_moment`, `latent_positive_control`, and `run`;
- `verify_padic_macrocycle_lift.py`: `canonical_primitive`, `normalization_data`, `edge`, `graph_stats`, `verify_precision`, `latent_record_stream`, `verify_contact_model`, and `verify`;
- `known_template_weighted_birth_probe.py`: `inverse_macro_direction`, `latent_relative_moment`, `template_spec`, and `chronological_template_scan`.

**PROVED:** No dedicated test module or construction state class defines the family. The executable audits and verifiers above are the tests. `TimeBudgetExpired` in `padic_macrocycle_lift.py` is the only associated class and is execution control, not family state.

**PROVED:** The following files contain proof-boundary or expository references but do not enlarge the family theorem: `CONDITIONAL-THEOREM.md`, `README.md`, `REPORT.md`, `design/FAR-SECANT-BIRTH-OPERATOR.md`, `design/FAR-SECANT-RANK-LEMMA.md`, `design/ORDERED-PATH-SAFETY-GATE.md`, `design/UNCONDITIONAL-INDUCTION-PLAN.md`, and the earlier reachable-secant depth audit artifacts.

**PROVED:** Same-cone direction tests in the guarded lattice scripts are incidental geometric matches, not definitions of family membership. The relevant files are `design/lattice_t_projective_spectrum_census.py`, `design/lattice_t_projective_spectrum_diagnostic.py`, `design/lattice_t_l5_cone_guard_audit.py`, `design/lattice_t_l6_cone_birth_guard.py`, `design/lattice_t_l6_cone_guard_audit.py`, `design/lattice_t_l6_cone_guard_pin_report.py`, `design/audit_guarded_l5_to_l6.py`, and `design/guarded_l5_l6_common.py`.

**PROVED:** There is no latent-family state class. `TimeBudgetExpired` in `padic_macrocycle_lift.py` is execution control only. The family index `n` is a theorem parameter, not a stored finite-state field.

## 3. Exact mathematical family

Let

\[
p=\left(-\frac92,-\frac{39}{11},-\frac{31}{11}\right),\qquad
P=22p=(-99,-78,-62),\qquad a=(-2,-2,-2),
\]
\[
h=22(a-p)=(55,34,18),\qquad g_n=N^{2n}h.
\]
Define

\[
\mu_n=p\times g_n=\frac{P\times g_n}{22},
\qquad
L_n=\{x\in\mathbb Q^3:x\times g_n=\mu_n\}.
\]

### 3.1 Direction and moment normalization

**PROVED:** Every `g_n` is primitive. The canonical sign is the sign for which the first nonzero coordinate is positive.

**PROVED:** `g_n mod 22` has period five and `P cross g_n` is coordinatewise divisible by `22`, so every `mu_n` is integral.

**PROVED:** A primitive integer direction generates the full lattice of integer differences parallel to it. Since `mu_n` is an integral vector perpendicular to `g_n`, each `L_n` contains integer lattice points.

**PROVED:** A geometric line is represented by a correlated Plücker pair `(g,mu)` satisfying `g dot mu=0`, modulo common nonzero scaling. Canonical primitive normalization must act on the pair, including the same sign. Normalizing `g` while forgetting `mu` loses the affine offset and is not a line normalization.

### 3.2 State actually represented

At the phase-8 macro-boundary, the theorem state retains:

- phase in `{8,16}`;
- exact canonical primitive direction `g`;
- exact integral Plücker moment `mu`;
- the pinned selected word and slot control;
- family index `n` as an unbounded theorem parameter.

It does **not** retain:

- endpoint identities or a secant birth prefix;
- owner, address, shell, or endpoint provenance;
- occupancy or whole-word correlation beyond the two pinned words;
- alternate-action legality.

**PROVED:** Membership is exact for one countable affine-line orbit and its phase-16 intermediates.

**PROVED:** As a class of construction contacts, this is a strict underapproximation. Newborn lines, endpoint insertion, cursor imports, unrelated owner changes, near–far and far–far joins, and alternate connector choices are outside the definition.

**UNPROVED:** Any `L_n` is the line through two points that coexist in a globally legal reachable ordered-path history.

## 4. Derivation of the implemented rank

### 4.1 Algebra

Direct multiplication gives

\[
q(Mg)=9q(g).
\]

Because `N=9M^(-1)` and `q` is homogeneous of degree two,

\[
q(N^2g)=81q(g).
\]

For the seed,

\[
q(h)=3828,
\qquad v_3(q(h))=1.
\]

The exact family satisfies

\[
(g_n)_x=55\cdot 9^n,
\]
so

\[
v_3((g_n)_x)=2n,
\qquad
v_3(q(g_n))=4n+1.
\]

Therefore

\[
R(g_n)=\min\left(\frac{2n}{2},\frac{(4n+1)-1}{4}\right)=n.
\]

**PROVED:** The division by two measures the two `x`-valuation units added by one inverse macrocycle `N^2`.

**PROVED:** The offset by one removes the seed valuation `v_3(q(h))=1`.

**PROVED:** The division by four measures the four `q`-valuation units added by one inverse macrocycle.

**PROVED:** The floor operations have no theorem-bearing effect on this family: both numerators are exactly divisible. Off the family they merely totalize the displayed arithmetic on some nonzero directions; no off-family transition law was proved.

### 4.2 Domain and representation dependence

**PROVED:** The implementation is defined only when both `g_x` and `q(g)` are nonzero. Its `exact_v3` routine raises on zero. Zero channels are neither assigned infinite rank nor promoted.

**PROVED:** `R` is invariant under sign and is well-defined on the canonical primitive direction.

**REFUTED:** `R` is not invariant under arbitrary representations of the same line. For example, `h` and `9h` define the same direction, but `R(h)=0` and `R(9h)=1`.

**PROVED:** The scalar depends only on `g`; the latent-family transition and poison behavior do not. Family membership, affine transport, silence, and reveal also require `mu`, phase, and the pinned action.

## 5. Exact macrocycle

### 5.1 One-edge line transport

For an ancestral slot with prefix control `c`, points transform as

\[
x'=M(x-c).
\]

Let `C=cof(M)`, `tau=gcd(Mg)`, and let `epsilon` choose the canonical sign. Exact affine-line transport is

\[
g'=\epsilon\frac{Mg}{\tau},
\qquad
\mu'=\epsilon\frac{C(\mu-c\times g)}{\tau}.
\]

The candidate effect at cursor `q` is derived, not guessed:

\[
\operatorname{Mask}_q(g,\mu)=\{x\in C_q:x\times g=\mu\}.
\]

**PROVED:** `(phase,g,mu)` is transition-sufficient for the one already-born line under the pinned direct carriage channel. Direction alone is not.

### 5.2 Pinned two-word cycle

The macrocycle is:

1. phase 8, selected word `[0,1,16]`, zero-based slot `2`, control `c=(-4,-4,-3)`;
2. phase 16, selected word `[8,23,24]`, zero-based slot `0`, control `c=(0,0,0)`;
3. return to phase 8.

Its affine point map is

\[
F(x)=M^2(x-c),
\]
with `F(p)=p`.

Since `M^2N^2=81I`, common projective scaling gives

\[
F(L_n)=L_{n-1}\quad(n\ge1).

Write
\[
d_n=N^{2n-1}h,\qquad
\nu_n=M(p-c)\times d_n,\qquad c=(-4,-4,-3).
\]
The complete phase record is:

| Stage | Exact token and action | Raw then canonical output | Candidate mask/effect | Displayed rank |
|---|---|---|---|---:|
| phase-8 input | `(8,g_n,mu_n)`, word `[0,1,16]`, slot `2`, control `c` | — | empty and silent for `n>=1` | `n` |
| `8 -> 16` | apply `x'=M(x-c)` | raw `(Mg_n,C(mu_n-c cross g_n))`; divisor `9`, sign `+1`; output `(16,d_n,nu_n)` | phase-16 mask empty and silent | `n-1` |
| `16 -> 8` | word `[8,23,24]`, slot `0`, control `0` | raw `(Md_n,C nu_n)`; divisor `9`, sign `+1`; output `(8,g_(n-1),mu_(n-1))` | empty if `n>1`; for `n=1`, mask `{(-2,-2,-2)}` kills the selected phase-8 word | `n-1` |

There is no separate visibility bit in this theorem: visibility/effect is recomputed exactly from `(phase,g,mu)` and the phase candidate set. The only terminal case in the family transition is `n=1 -> L_0 -> reveal`; `L_0` is not silently advanced to an invented `L_(-1)`. Zero coordinates, nonfamily directions, other controls, births, imports, and alternate words are outside this transition theorem.
\]

**PROVED:** Each edge has primitive normalization divisor `9` on this orbit.

**PROVED:** On phase-8 input `L_n`, the first edge changes the displayed direction scalar from `n` to `n-1`. The second edge leaves it at `n-1`. Thus a complete macrocycle changes `R` by exactly `-1`.

**PROVED:** This decrease is not ordinary raw carriage. Unnormalized multiplication by `M` raises raw valuations. The decrease is caused by canonical division by `9` on each pinned edge plus restriction to the special inverse orbit `g_n`.

**PROVED:** `L_n` has an empty full candidate mask at both phases for every `n>=1`. After exactly `n` complete cycles it becomes `L_0`; `L_0` hits `a=(-2,-2,-2)`, an interior of the selected phase-8 word, and kills that word. There is no continuing family state `L_(-1)`.

### 5.3 Independent candidate-frontier replay

The focused auditor independently reconstructed the two selected words from the exact compact domain cache and replayed all candidate sites.

- **EXACT FINITE:** `31,840` domain words were scanned.
- **EXACT FINITE:** There are `214` phase-8 sites and `214` phase-16 sites.
- **EXACT FINITE:** The canonical site-stream digest is `6cda4eea1d2499f796493a5ed062579bd210fe5e5e50a0d1aea373e7a8a9bf33`.
- **PROVED:** Under
  \[
  J(r,y,z)=\frac{3y^2-yz+3z^2}{r^2},
  \]
  all family directions have `J=348/275`.
- **EXACT FINITE:** Exactly two phase-adjusted candidates have that `J` value:
  - phase 8: site `(-2,-2,-2)`, primitive direction `(55,34,18)`;
  - phase 16: site `(-4,1,2)`, primitive direction `(165,-20,102)` in the common phase-8 pullback frame.
- **PROVED:** Since `(g_n)_x=55*9^n`, neither frontier direction is `g_n` for `n>=1`; hence the all-`n` empty-mask statement follows.

The original full fixed-policy checker was not rerun because the locally reconstructed policy artifact has SHA-256 `0f4e340177e7c1aacba00ec7048b983d38ff487eed673fb088876babdf1a518e`, while the committed certificate pins `e30732d2833b3c93ae2ccbbc5f37ddd3069346899c24d49fc18aabfa1a48485e`. The independent candidate replay uses the still-matching metadata and compact-domain hashes and verifies that both selected words are present in their exact domains. This is a fail-closed distinction, not a silent acceptance of the stale policy artifact.

## 6. Audit of the `66,429`-edge certificate

### 6.1 What the graph is

For each `k=1,...,5`, the committed script builds a separate functional graph on the y-unit projective chart

\[
[x:1:z]\pmod{3^k}.
\]

The deterministic inverse direction map is

\[
(x,z)\longmapsto
\left(\frac{9x}{u},\frac{3-9z}{u}\right),
\qquad u=-8-3z,
\]
where `u` is always a 3-adic unit.

**PROVED:** Every chart state has one valid successor for this direction map.

**EXACT FINITE:** The independent auditor regenerated every state/edge and reproduced the committed per-precision digests.

| `k` | modulus | states = edges | image states | SCCs | recurrent SCCs | maximum tail distance |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 9 | 1 | 9 | 1 singleton | 1 |
| 2 | 9 | 81 | 1 | 81 | 1 singleton | 1 |
| 3 | 27 | 729 | 3 | 729 | 1 singleton | 2 |
| 4 | 81 | 6,561 | 9 | 6,561 | 1 singleton | 2 |
| 5 | 243 | 59,049 | 81 | 59,049 | 1 singleton | 3 |
| **sum** | — | **66,429** | — | — | **5 across disjoint graphs** | **3** |

There are no terminal states in any graph. The total `66,429` is a sum over five overlapping precision universes, not the size of one construction automaton.

### 6.2 What the graph is not

Each residue state omits:

- exact integer primitive direction;
- Plücker moment `mu`;
- phase and selected construction action;
- poison mask and effect;
- terminal or promoted classification;
- births, endpoint insertion, cursor imports, owners, occupancy, provenance, and whole-word correlation.

Consequently:

- **UNDEFINED:** minimum/maximum exact rank, rank-change histogram, zero-decrease count, increasing-edge count, and countdown slack on these residue states;
- **NOT REPRESENTED:** exact line-token transition, integer primitive normalization, poison/effect transition, and terminal/promotion transition;
- **PROVED ONLY FOR THE ABSTRACT MAP:** successor completeness for the one deterministic projective inverse-direction map;
- **REFUTED:** successor completeness for construction actions or reachable contacts.

### 6.3 Minimal finite-residue collision

At the finest committed modulus `3^5=243`,

- `g_3=(40095,-20990,12306)`, `R=3`, three cycles to reveal;
- `g_4=(360855,131002,-173724)`, `R=4`, four cycles to reveal;

both normalize to projective state `[0:1:30] mod 243`.

**PROVED:** The finest committed graph merges two exact family tokens with different ranks and different future reveal times. No state function on that graph can equal the exact countdown on both.

### 6.4 Minimal direction-only poison collision

Take direction `h=(55,34,18)`.

- The line through `(-2,-2,-2)` has moment `(32,-74,42)` and hits the phase-8 reveal site.
- Its parallel translate through `(-1,-2,-2)` has moment `(32,-92,76)` and does not hit that site.

**PROVED:** Equal direction does not imply equal poison behavior. Omitting `mu` merges incompatible line effects.

### 6.5 Meaning of “depth 16”

**EXACT FINITE:** The committed regression checks the `17` arithmetic records `g_0,...,g_16`.

**PROVED:** The all-`n` theorem does not follow from those records. It follows separately from the symbolic `J`-frontier proof and the exact identity `F(L_n)=L_(n-1)`.

**REFUTED:** “Verified through depth 16” is an induction or a finite-state closure theorem.

This is exactly **STOP CONDITION 2**.

## 7. Reachability and closure boundary

The committed known-template scan reports:

- level 5: address shells `0..2`, `15` source corridors per shell;
- level 6: address shells `0..3`, `40` source corridors per shell;
- level 7: address shells `0..3`, `155` source corridors per shell;
- level 8: address shells `0..4`, `374` source corridors per shell.

**EXACT FINITE:** No tested requested latent-template line was a live secant in those finite ranges.

**UNPROVED:** The zero result extends to all levels, all address shells, all legal histories, arbitrary directions, old–new births, deep–deep pairs, or unrelated cursor imports.

**REFUTED:** The current artifacts establish closure under new births, endpoint insertion, arbitrary cursor imports, near–far/far–far joins, alternate words, owner/address changes, occupancy, or whole-word correlated action choices.

The macrocycle theorem is conditional on an already existing `L_n` and the two pinned words. It neither supplies the two endpoints needed to make `L_n` a secant nor proves those actions globally legal in the presence of every other poison channel.

## 8. Promotion verdict and Phase-9 classification

### A. Universal promotion

**REFUTED.** No finite promotion predicate is supplied, and the exact family contains unbounded countdowns.

### B. Finite family cover

**REFUTED.** Merging all `L_n` loses future reveal time; the family has infinitely many distinct right languages under the pinned continuation.

### C. Ranked escape plus promotion

**REFUTED AS CURRENTLY ESTABLISHED.** A rank exists on the fixed family, but no closed promotion class or construction-wide ranked escape theorem exists.

### D. Recorded-orbit-only coverage

**INSUFFICIENT AS THE FINAL CLASSIFICATION.** The committed finite L5–L8 scan is useful exact finite evidence, but the theorem being audited is broader and the residue graph is not a recorded-orbit contact classifier.

### E. Reachable counterexample

**UNPROVED.** The family is an exact geometric obstruction, but no audited artifact proves that an `L_n` is a reachable secant or that all competing poison constraints allow the macrocycle from such a state.

### F. Insufficient abstraction

**PROVED.** This is the only supported Phase-9 outcome. The residue state lacks exact countdown, affine offset, poison effect, construction actions, and reachability data. The fixed family is a ranked infinite orbit, not a finite promoted class.

## 9. Next lemma

### Uniform reachable exclusion of translated latent templates

**CONJECTURED.** For every level `ell>=0`, every globally legal reachable ordered-path prefix `S` at level `ell`, every phase-8 corridor anchor `r` in `S`, every `n>=1`, and every two distinct points `a,b` already placed in `S`, it is not the case simultaneously that

\[
\exists k\in\mathbb Z\setminus\{0\}\text{ such that }b-a=k g_n,
\]

and

\[
(a-r)\times g_n=\frac{P\times g_n}{22},
\qquad P=(-99,-78,-62).
\]

This is the precise next target because it is causal, quantifies each birth prefix and corridor translation, and would exclude the whole latent orbit from reachable secants. It does not pretend that bounded direction residues promote the orbit.

## 10. Claim ledger

| ID | Classification | Claim |
|---|---|---|
| C1 | **PROVED** | The all-`n` affine family and fixed-cycle countdown are symbolically valid. |
| C2 | **PROVED** | `R(g_n)=n`; a complete pinned macrocycle changes `R` by `-1`. |
| C3 | **PROVED** | The first pinned edge changes `R` by `-1`; the second by `0`. |
| C4 | **EXACT FINITE** | All `66,429` projective residue edges through `3^5` were regenerated with matching digests. |
| C5 | **REFUTED** | Those edges form an inductive line-token countdown certificate. |
| C6 | **REFUTED** | Direction residue alone preserves Plücker and poison information. |
| C7 | **EXACT FINITE** | The committed L5–L8 requested-line scan found no live translated family secant in its tested ranges. |
| C8 | **CONJECTURED** | No translated `L_n` is ever born in any globally legal reachable history. |
| C9 | **REFUTED** | The fixed family is currently a sound finite promoted class. |
| C10 | **MEASURED** | No new construction-orbit measurement was run after the stop condition fired. |

## 11. Reproducibility

Primary focused artifacts:

- `design/padic_latent_family_macrocycle_audit.py`
- `design/verify_padic_latent_family_macrocycle_audit.py`
- `design/padic-latent-family-macrocycle-audit-summary.json`
- `design/padic-latent-family-macrocycle-witness.json`

Producer prerequisites are the pinned local exact-domain inputs `/tmp/no-new-x-line-L5-canonical.json` (SHA-256 `5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a`) and `/tmp/no-new-x-line-domains.bin` (SHA-256 `da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7`). The verifier is restart-safe from the hashed witness artifact alone and additionally replays those raw inputs when they are present.

Run:

```bash
python3 -B design/padic_latent_family_macrocycle_audit.py
python3 -B design/verify_padic_latent_family_macrocycle_audit.py
```

Observed focused payload commitments:

- summary payload SHA-256: `bc77d62382fd5e830025c97a5b8f9ae6aca778aab89160679c6801cb15168d64`;
- witness payload SHA-256: `ee4efe3f6b6fd073a0552b56ca7a2f1a3511a4f92e3b501087f6f888466330f4`;
- total regenerated states/edges: `66,429`;
- committed latent regression depth: `16`;
- stop condition: `2`.

The verifier independently reconstructs the family formulas, exact phase transitions, candidate frontier, every bounded projective edge, SCC/tail metrics, source-history inventory, and proof-boundary claims. It does not trust producer-computed verdict text as a substitute for those checks.

## 12. Authorized follow-up: guarded reachable-entry exclusion

The original audit stopped before reachable-history work, as required by
STOP CONDITION 2.  The user subsequently authorized the narrow next-lemma
audit below.  This follow-up does not change the original disposition: the
`66,429` direction-residue edges are still not a line-token induction
certificate.

### 12.1 Exact family/guard relation

Put

\[
F(g)=275q(g)-348g_x^2.
\]

**PROVED.** The `348/275` guarded cone is exactly `F(g)=0`.  Direct integer
algebra gives

\[
F(H)=0,\qquad F(Mg)=9F(g),\qquad F(Ng)=9F(g),\qquad NM=9I,
\]

for `H=(55,34,18)`.  Hence every primitive direction in the projective
`N`-orbit of `H`, including every phase-8 `g_n=N^(2n)H` and phase-16
intermediate, lies in that guarded cone.

The exact entry recognizer first reduces `b-a` to its canonical signed
primitive direction, retaining the signed chord multiplier separately, and
then checks the corridor-centred Pluecker moment.  Thus its geometric-line
predicate is independent of arbitrary chord scaling.  For birth exclusion,
however, the moment is not needed: the two-cone guard rejects every old--new
and same-word new--new pair whose direction satisfies `F=0`.

### 12.2 Policy-relative all-level theorem

**PROVED.** For every finite history descended from the canonical guarded-L5
parent in which every inserted connector word satisfies the same two-cone
birth guard, no translated phase-8 line `L_n` with `n>=1`, and no phase-16
intermediate, is a secant at any prefix.

The proof is an induction on insertions:

1. **EXACT FINITE:** An all-pairs scan of the `8,296` canonical parent points
   finds exactly four `F=0` pairs.  Their canonical L5 directions are
   `(165,102,-20)`, `(165,82,84)`, `(165,84,82)`, and
   `(165,-84,-82)`.
2. **PROVED:** None of those four directions is in the projective `N`-orbit
   of `H`.  Its x-coordinate would force orbit index one, whose direction is
   `(165,20,-102)`.  Since `NM=9I`, pure carriage cannot move a disjoint
   projective lineage into that orbit.
3. **PROVED:** Every newly created latent-family secant would have `F=0` and
   is rejected by the birth guard.  Existing secants only carry.  The
   induction therefore closes for every finite guarded continuation.

This proves exclusion of this one infinite latent orbit under the existing
guard; it does not promote the orbit into a finite contact class.

### 12.3 Finite chronology checks

The symbolic theorem is supplemented, but not replaced, by these exact
finite checks:

- **EXACT FINITE:** On the recorded guarded L5 -> L6 chronology, the
  `8,296` anchors plus `20,508` connector interiors contain no requested
  phase-8 family entry.  Shells `n=1,2` were tested on each of the `51`
  phase-8 source corridors; `n>=3` is excluded because the first such
  primitive x-spacing, `40,095`, exceeds the exact final x-span `10,943`.
  The scan also found no pair parallel to any translation of a requested
  line.
- **EXACT FINITE:** Every connector word in the stored domain at each of the
  `8,295` recorded prefixes was classified: `756,512,535` word
  occurrences, `136,317,832` survivors, and `245,555` rejections by the
  `348/275` guard.  This is a census at recorded prefixes, not proof that a
  successor remains available after taking an alternate word.

### 12.4 Remaining boundary

- **UNPROVED:** Connector availability for every guarded continuation.
- **UNPROVED:** Exclusion in globally triple-free histories that omit the
  two-cone guard.
- **UNPROVED:** Closure of births, imports, occupancy, and poison effects
  outside this one fixed latent orbit.

Accordingly the new result discharges the fixed-family reachable-entry
branch only.  It is not an unconditional proof of Erdos #193 and does not
establish Gate D or the availability fixed point.

### 12.5 Follow-up artifacts and reproduction

- `design/latent_family_reachable_entry_audit.py`
- `design/verify_latent_family_reachable_entry_audit.py`
- `design/latent-family-reachable-entry-audit-summary.json`
- `design/latent-family-reachable-entry-witness.json`

Run:

```bash
python3 -B design/latent_family_reachable_entry_audit.py
python3 -B design/verify_latent_family_reachable_entry_audit.py
```

Observed payload commitments:

- summary payload SHA-256:
  `4f821c5c04479fa0998a191a47e6d87cfba683797421ef2957026ff45d28496d`;
- witness payload SHA-256:
  `51a9f175a5d643c735aaf1f9462154dcb93d7e09cffd448abe60f7ec96ccf60b`.

The verifier does not import either producer module.  It reloads the pinned
parent, chronology, and alternate-domain artifacts; reconstructs the family
and cone algebra; repeats the inherited-core and recorded-line scans; and
reaggregates every alternate-prefix outcome count.


---

Audit and artifacts signed in repository prose by **[OpenAI Codex]**.
