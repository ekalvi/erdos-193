# Erdős Problem #193: A Conditional Resolution and a Map of the Obstruction

> **SUPERSEDED (2026-07-17).**  The conditional reduction in this document is
> not referee-valid.  Lemma R as stated is already implied by the repository's
> qualitative uniform crowding bound on its fixed radius interval, yet it does
> not imply connector availability.  Exact replay shows that global far secants
> kill 51–68% of the apparent radius-40 survivors at key bottlenecks.  The actual
> missing hypothesis is a reachable connector-survivor safety invariant, or a
> sharp near-mask bound plus a separate uniform far-secant lemma.  See
> `CONDITIONAL-THEOREM.md` and `design/ORDERED-PATH-SAFETY-GATE.md`.  Historical
> claims below are retained as a research record, not as the current theorem.

*An AI–human "centaur" attack on the no-three-collinear infinite-walk problem. This document reports exactly what was proven, what remains open, and why the endpoint resists every standard tool. It is written to be checked by a referee and read by a curious non-specialist. Every load-bearing number below was re-verified in exact or high-precision arithmetic against the working repository.*

---

## 1. What the problem is, and what we did and did not achieve

### The question

Erdős Problem #193 asks a deceptively simple question about walks on a grid. Fix a dimension *n* and a **finite** set of allowed steps `S ⊂ ℤⁿ`. An *S-walk* is an infinite sequence of lattice points in which every point differs from the previous one by some step in `S` (steps may repeat). The question:

> **Does there exist a dimension *n* and a finite step-set `S` admitting an infinite S-walk in which no three visited points are collinear?**

"No three collinear" is the hard endpoint — sometimes written **k = 3** (never three on a line). Both a non-constructive existence proof and a proof for *any* dimension *n* would count as a resolution.

### The known history

- **Gerver–Ramsey (1979).** In the plane (2D) this is impossible: any infinite walk with a finite step-set is forced to contain three collinear points, and in fact collinearity is unavoidable and unbounded. In 3D they showed one can keep the number of collinear points *bounded* — their bound was enormous (at most 5¹¹).
- **Lidbetter (2023, arXiv:2303.14579).** Improved the 3D bound: an explicit walk with at most **6** collinear points on a line, and a general bound lowered to **≤ 189**. This is a large improvement, but it still never reaches the k = 3 endpoint.

So #193, at k = 3, is **open**. Every prior construction admits some small but positive number of collinear points.

### What we achieved (and what we did not)

We did **not** resolve #193 unconditionally. We want to be completely clear about that up front, because this problem has a documented history of over-eager "it's solved" claims.

What we did produce is two things:

1. **A corrected conditional theorem.** We give an explicit scale-and-rotate construction and prove that it succeeds provided a reachable-state connector-safety invariant, **Lemma A**, holds with a sound treatment of far secants.  The earlier claim “YES modulo bounded-crowding Lemma R” was too weak and is withdrawn.  A record finite instance has been machine-verified triple-free at **311,738 points**.

2. **A rigorous map of why the unconditional endpoint resists.** We prove **five negative results** — "the five walls" — each showing that a specific standard proof technique *cannot* supply Lemma R, plus a global-analysis reconnaissance showing the heavy machinery of modern harmonic and arithmetic analysis is likewise blind to the obstruction. These are genuine theorems about the *tools*, not about the walk. They explain, precisely, why the last step is hard.

**Honest odds.** We estimate the walk almost certainly exists (~85%), while a full *unconditional* proof with currently-known tools is unlikely (roughly 1–5%). These are calibrated guesses, held separately and stated conservatively.

Every negative result in this document is a statement about a proof strategy. **None of them is inflated into a claim that #193 is false, and none of them is the missing unconditional proof.** The single open lemma is marked clearly throughout.

### Notation used throughout

| Symbol | Meaning |
|---|---|
| `M` | the construction matrix `M_BAL3 = [[3,0,0],[0,0,−3],[0,3,−1]]`, `det M = 27` |
| `Q` | invariant form `[[1,0,0],[0,6,−1],[0,−1,6]]`; `MᵀQM = 9Q` exactly (M is a ratio-3 Q-similarity) |
| `θ` | the twist angle `arccos(−1/6) ≈ 99.594°` |
| `C = cof(M)` | cofactor matrix `[[9,0,0],[0,−3,−9],[0,9,0]]`, `det C = 729 = 27²`; an exact ratio-9 similarity |
| `Ω(x,y,z)` | collinearity form `(y−x)×(z−x) ∈ ℤ³`; three points collinear ⟺ `Ω = 0` |
| `Δ` | a first-difference between two walk addresses reaching a common anchor |
| `E = D − D` | the digit / connector-difference alphabet, `|E| = 15,545` |
| `c` | a normalized "carry", `c = M⁻ᵍΔ` at generation `g` |
| **Lemma R** | the single open hypothesis: uniform bounded crowding / arc-incidence |

---

## 2. The conditional theorem: Erdős #193 is YES, modulo one geometric lemma

In plain terms: we have an explicit recipe that grows an infinite non-self-crossing walk in 3D whose points never line up three-in-a-row, and we can prove it never gets stuck — *provided* one clean geometric fact holds: that the walk stays a **thread**, never thickening into a **blob**. Every other link in the argument is either exact algebra or exhaustively machine-checked. This single remaining fact is the whole gap between "conjecture" and "theorem."

### The theorem we prove

> **Theorem (conditional).** Let `S ⊂ ℤ³` be the 124-vector menu of all integer steps that the construction below uses (coordinates in {−2,…,2}). If **Lemma R** (below) holds, then there exists an infinite S-walk visiting lattice points **no three of which are collinear** — i.e. Erdős #193 has answer **YES**.

The affirmative resolution of #193 is therefore reduced to a single, sharply stated regularity lemma. Nothing else is assumed.

### The construction (one paragraph)

Fix the integer expansion matrix `M = [[3,0,0],[0,0,−3],[0,3,−1]]`, `det M = 27`. All three eigenvalues of `M` have modulus exactly 3: the *x*-axis contributes 3, and the lower 2×2 block `[[0,−3],[3,−1]]` has characteristic polynomial `λ²+λ+9` (discriminant −35), i.e. it is 3× an irrational rotation through the twist angle **θ = arccos(−1/6) ≈ 99.594°**. Starting from a short hand-built triple-free walk `W₀`, each level is formed by

    W_{k+1} = (M · W_k) ⊔ S_k

— blow the current walk up by `M` (the images are the **anchors**), then **stitch** each anchor-to-anchor gap with a short connector word drawn from `S`, chosen to keep the whole configuration triple-free. Because `M` is linear it preserves collinearity, so the anchors inherit triple-freeness for free; only freshly stitched points can create a new collinear triple, and only at the moment they are placed. If every level completes, the nested limit is an infinite triple-free walk. A record instance has been built and machine-verified: **311,738 points, no three collinear, no repeated vertex** (parallel exact-integer verifier, log line `PARALLEL-VERIFIED: level 8 (gate2) triple-free, no repeated vertex`).

### The proof chain

Writing `Ω(x,y,z) = (y−x)×(z−x)` for the exact integer collinearity form (three points collinear ⟺ `Ω = 0`):

- **L1 — Base [PROVEN].** A triple-free walk over `S` exists; verified up to 311,738 points by an independent exact-integer verifier.
- **L2 — Inheritance [PROVEN].** Cross products transform by the cofactor matrix: `(Ma)×(Mb) = C·(a×b)`, with `C = cof(M) = [[9,0,0],[0,−3,−9],[0,9,0]]`, `det 729`, invertible. Hence a triple that is non-collinear when created stays non-collinear at **every** later level; completed levels are frozen safe forever. (This is also the exact reduction "three collinear ⟺ a carry-cross vanishes": an *integer* condition, so "≠ 0" means "|·| ≥ 1" — a hard 0-vs-≥1 gap with no metric slack. See §3.)
- **L3 — Availability [OPEN].** At every reachable stitch at least one exact connector word must survive every local and far secant.  The reported 317 / 180 / 271 values are extrapolations from samples of at most 200 words per stitch, not exhaustive lower bounds.
- **L4′ / Lemma A — the open hypothesis.** A policy-independent finite history abstraction, finitely represented invariant, and total selector must supply a legal connector for every represented concrete history and keep every sound abstract successor safe.  A separate far-secant/tail lemma is required for any truncated poison state.  Saying only "reachable under the certified policy" is circular unless this total closure certificate is provided.
- **L5 — Induction plus König [PROVEN given L1–L4′].** The hypotheses inductively produce valid finite walks of unbounded length over the same finite step alphabet.  These levels are not nested point sets; König's infinity lemma applied to the finitely branching tree of valid prefixes extracts an infinite triple-free walk.

So **L1, L2, and the formal induction step are proven; the theorem is conditional on the direct reachable-state safety Lemma A, not on generic bounded crowding.**

### Lemma R — withdrawn as an availability hypothesis

> **Lemma R (bounded crowding / arc-incidence).** For the construction orbit there is a level-independent constant `C_R` such that, for every level `k`, every centre `q`, and every radius `r ∈ [1, 10]`,
>
>   `c_k(q, r) := #{walk points within Chebyshev distance r of q} ≤ C_R · r^d`,
>
> with `d = log λ / log 3 ≈ 1.10` (`λ ≈ 3.36` the per-level point-growth ratio).

On the fixed interval `1 <= r <= 10`, the already-claimed level-uniform cubic
crowding bound implies the existence of some such `C_R`.  Therefore this
statement is too weak to imply connector availability.  Exact replay also
shows that secants with distant endpoints kill many words that survive a
radius-40 truncation.  A useful replacement must be either a sharp numerical
bound coupled to an exhaustive local poison calculation and a uniform tail
bound, or the direct reachable-state Lemma A above.

### The proven machinery around Lemma R (verified constants)

Every number below was re-verified in exact arithmetic:

- **Exact self-similarity.** `Q = [[1,0,0],[0,6,−1],[0,−1,6]]` satisfies **`MᵀQM = 9Q` exactly** (result `[[9,0,0],[0,54,−9],[0,−9,54]] = 9Q`), so `M` is a genuine Q-similarity of ratio 3.
- **Exact 0-overlap recursion.** `W_{k+1} = M·W_k ⊔ S_k` is a genuine disjoint union (0 duplicate points, 0 anchor-interior collisions over 8,252 + 27,696 stitches), so crowding partitions exactly by birth level.
- **Anisotropic contraction pole.** In `M`'s singular-value metric the renormalization pull-back factor is **`φ = σ₁(M⁻¹)·σ₂(M⁻¹)^{d−1} ≈ 0.351 < 1`** (singular values of `M⁻¹` = 0.39349, 0.33333, 0.28238; `d = 1.1036`). The map contracts — the naive isotropic 4/9-recursion diverged; this one does not.
- **Deep-tail collapse.** `M³ = [[27,0,0],[0,9,24],[0,−24,17]]` and **`min` over nonzero integer `v` of `|M³v|∞ = 24`** > 2r for all r ≤ 10. Hence any ball meets ≤ 1 point born more than three levels back: the infinite recursion collapses to a finite ≤ 4-birth-level bound.
- **Birth telescope.** Because `M⁻¹` decays at the spectral rate 1/3, the pull-back series converges: **`S = Σ_j ‖M⁻ʲ‖∞ = 1.67693`** (exact), strictly below the isotropic 9/5 = 1.8. This dissolves the divergent charge that killed the isotropic recursion and reduces the crowding law to a single-level refill slope, giving the rigorous linear bound `C_R ≤ E·S`.
- **Self-avoidance [PROVEN].** The realized single-connector walk is vertex-self-avoiding (`Δ = Mᵍ(p_v − p_u) = 0 ⟺` a repeated vertex, forbidden), certified by a closed 8,649-state carry-automaton.
- **Qualitative no-blow-up [full theorem].** The anchor 3-separation packing bound gives a level-independent *cubic* crowding bound for all `k`, finite-menu-certified over all ~79M menu words: the walk provably never densifies without limit.

### The honest status

What is not proved is a finitely certified connector-survivor invariant and
total selector that includes
global secant poisoning.  The measured crowding and sampled connector data are
useful finite evidence, but neither promotes the old Lemma R to availability.
The corrected conditional statement is therefore: the construction continues
forever if Lemma A, the exact finite-invariant safety assertion, is proved; the
resulting arbitrarily long words yield an infinite one by König's lemma.

---

## 3. The exact reduction: collinearity becomes a single integer cross-product

**In one sentence.** Asking "do three points of the walk lie on a line?" turns out to be exactly the same question as "is one specific vector of whole numbers equal to zero?" — and because those numbers are integers, the answer is never *almost* zero: it is either exactly `0` (collinear) or at least `1` in size (safely off the line), with nothing in between.

### The collinearity form

Three points `x, y, z ∈ ℤ³` are collinear iff the two edge vectors out of `x` are parallel. The exact test is the cross product

    Ω(x, y, z) := (y − x) × (z − x) ∈ ℤ³,   and   x, y, z collinear ⟺ Ω = 0.

Because the points are integer lattice points, `Ω` is an **integer vector**: every component is a determinant of integer entries. This is the pivot of the whole reduction — collinearity is not a real-valued "how close to a line" quantity, it is the vanishing of an integer vector.

### How the construction matrix acts on the form

The one clean fact that makes the construction tractable is that `M` acts *linearly and invertibly* on the collinearity form, via the cofactor matrix `C = cof(M) = [[9,0,0],[0,−3,−9],[0,9,0]]`, `det C = 729`. Two exact identities hold (both re-verified in PyPy):

- **Inheritance / single step.** `(M·u) × (M·v) = C·(u × v)`, equivalently `Ω(Mx, My, Mz) = C · Ω(x, y, z)`. Since `det C = 729 ≠ 0`, `C` is invertible over ℚ, so `Ω = 0 ⟺ C·Ω = 0`: a triple is collinear at one level iff its image is collinear at the next. Non-collinearity, once achieved, is preserved forever. (This is exactly Lemma L2.)
- **Iterated / any depth.** By induction `(Mᵍ u) × (Mᵍ v) = Cᵍ (u × v)`.

`C` is not arbitrary: it is itself an exact **ratio-9 similarity**, the mate of `M`'s ratio-3 similarity `MᵀQM = 9Q`. Concretely `Cᵀ·adj(Q)·C = 81·adj(Q) = 9²·adj(Q)`, and a 3D similarity of ratio 9 necessarily has determinant `9³ = 729` — exactly `det C`. So the reduction lives inside the same rigid self-similar geometry as the walk itself.

### From walk points to the carry automaton

Specialize to two difference vectors `Δ₁, Δ₂` measured from a common base point, both formed at generation `g`. Each address-difference is an integer combination `Δ = Σⱼ Mʲ δⱼ` with digits `δ ∈ E = D − D`. Writing the normalized **carry** `cᵢ := M⁻ᵍ Δᵢ` (so `Δᵢ = Mᵍ cᵢ`), the iterated identity gives the clean bilinear collapse

    Δ₁ × Δ₂ = (Mᵍ c₁) × (Mᵍ c₂) = Cᵍ (c₁ × c₂).

Since `Cᵍ` is invertible,

    three points collinear  ⟺  Δ₁ × Δ₂ = 0  ⟺  c₁ × c₂ = 0.

This is the payoff: the geometric question at every scale `g` reduces to a **carry-cross** test on the two carries. The carries are not free integer vectors — each single-stream carry stays inside a *finite* set (the proven `Q(c) ≤ Emax/4` ball, an 8,649-state certificate), the same finiteness that powers self-avoidance. So "can two coexisting arcs be parallel?" becomes "does the finite pair-automaton over `E×E` reach a state with `c₁ × c₂ = 0`?"

### Why the integer 0-vs-≥1 gap is the crux

Both `Ω` and the carry-cross `c₁ × c₂` are **integer vectors**. Therefore

    "not collinear"  ⟺  Ω ≠ 0  ⟺  ‖Ω‖∞ ≥ 1,

with no intermediate values: a nonzero integer vector has a coordinate of absolute value at least 1. There is no continuous "margin of collinearity" to bound below — the separation is binary, `0` versus `≥ 1`.

This is exactly why the standard machinery of density, measure, and equidistribution gains no purchase on the *unconditional* endpoint. Those tools work by proving a **positive metric separation** — a lower bound on a real-valued quantity such as the normalized sine `‖Δ₁ × Δ₂‖ / (‖Δ₁‖‖Δ₂‖)`. But that normalized angle is *not* the invariant here: as the walk grows, `‖Δᵢ‖ → ∞`, so even with the integer cross fixed at its minimum `‖c₁ × c₂‖∞ = 1`, the geometric angle between two arcs can shrink toward zero. The only quantity that stays robustly bounded away from `0` is the integer cross itself — and it carries **no metric magnitude**, only the yes/no fact of vanishing. A measure-theoretic or Fourier argument, constitutively blind to a measure-zero exact-integer condition, has nothing to measure.

That is the reduction in full: `collinear ⟺ Ω = 0 ⟺ Δ₁ × Δ₂ = 0 ⟺ c₁ × c₂ = 0`, via the invertible cofactor similarity `C`, `det C = 729`. It is exact, finite-state, and converts an infinite geometric constraint into a hard integer `0`-versus-`≥1` gap — clarifying both why the *realized* walk stays triple-free (its carries never hit 0) and why closing the gap *unconditionally* resists every metric tool.

---

## 4. The Five Walls

Each wall is a rigorous **negative result**: a proof that one standard route to Lemma R (or to an unconditional resolution) cannot work. None of them says the walk fails to exist; each closes a *proof strategy* and sharpens the frontier. Throughout, "the realized walk" means the single-connector adaptive construction of §2, which self-avoids and dodges every overlap the walls exploit.

### Wall W1 — The Open Set Condition fails on the connector menu-closure

**In one sentence.** The most natural way to *prove* Lemma R — the classical self-similar-tiling toolkit (Mauldin–Williams / Schief's Open Set Condition) — is provably unavailable here, because two genuinely different two-step recipes land on the very same point of the fractal, and that single coincidence is exactly what the OSC forbids; crucially, the *actual* walk never uses both recipes at once, so this closes a proof *route* without denying the result.

**What we wanted, and why.** The textbook machine for a crowding estimate like Lemma R is the theory of graph-directed iterated function systems (GD-IFS): if a GD-IFS satisfies the **Open Set Condition** (equivalently, by Schief's theorem, if the identity is *not* in the Bandt–Graf neighbor set), then the attractor has positive Hausdorff measure, cylinders overlap only on a measure-zero set, and Lemma R follows essentially for free.

**The system tested.** Phrase the construction as the **menu-closure graph-directed system**: a node is keyed by its outgoing menu-step type (124 states), and its available children are the union over *all* legal connector choices for that step. Two length-2 words `u ≠ v` give the *same* contraction map (hence identical cylinders, hence the identity in the Bandt–Graf neighbor set, hence OSC failure) exactly when they share start type, end type, and generation-2 **anchor** `V = M·d₁ + d₂`.

The search is made rigorous by a finite **carry automaton**. With `E = D − D` (`|E| = 15,545`, `Emax_Q = 2116`), the carry obeys `|c'|_Q = (1/3)|c+e|_Q`, forcing `Q(c) ≤ 529`. That ball has **8,649 states and is closed under all 4,979,157 legal transitions with 0 escapes** — a finiteness certificate that `Δ = 0` is decidable for *all* generations at once. (A norm/lattice argument alone cannot exclude `Δ = 0`: there is an explicit unconstrained integer zero-cycle of length 2, `[(−12,−12,−7),(4,1,−4)]` summing to `(0,0,0)`, so the verdict turns entirely on legality, not size.)

**The g = 2 exact overlap (anchor (−2, 2, 1)).** Legality does not save the OSC. A type-blind pass finds 83,951 distinct-pair anchor collisions (22,085,602 legal pairs over 27 residue shards); requiring same start *and* end type does not kill the flood (a probe over start types {0,1,2} reports 17,219,577 identical-cylinder pairs). One collision is reconstructed with explicit certified-legal connectors as the referee witness:

- **Start type 1, end type 22, anchor `V = (−2, 2, 1)`.**
- **Word w₁:** digits `(0,1,0)` then `(−2,2,−2)`, via leg-1 connector `(66,0,20,21)` (interior `(0,1,0)` at intermediate state `s₁ = 0`) and leg-2 connector `(20,22,20)`.
- **Word w₂:** digits `(0,0,0)` then `(−2,2,1)`, via leg-1 connector `(5,20,21)` (interior `(0,0,0)` at a *different* intermediate state `s₁ = 5`) and leg-2 connector `(23,22,20)`.

Both compute `M·d₁ + d₂ = (−2,2,1)`. Same start type, anchor, end type, generation ⇒ `f_{w₁} = f_{w₂}` and identical cylinders. Two distinct legal words with the same map put the identity in the Bandt–Graf neighbor set, so the OSC **fails**. The essential feature is that **w₁ and w₂ reach the coincidence through different root connectors** (`(66,0,20,21)` vs `(5,20,21)`); the closure's freedom to be the union over *all* legal connectors is precisely what manufactures the overlap.

**Why this does not touch the realized walk.** The realized walk uses **one** connector per gap. Under that discipline the two words are never both present, and the construction provably self-avoids: `Δ = Mᵍ(p_v − p_u)`, so **`Δ = 0` ⟺ a repeated lattice vertex**, which the builder rejects. The recorded L8 walk has 311,738 chain points that are 311,738 distinct lattice points, and the measured reach-≤4 closure has 0-dimensional contact (interface counts saturate while cylinders grow ~3ᵍ; maximum shared-point overlap under the closest-approach translation is exactly 1 at every generation, ratio → 0).

**What W1 establishes.** The OSC/Mauldin–Williams/Schief route to Lemma R is **dead** — the identity is provably in the neighbor set of the menu-closure GDS. This is a negative result about a proof strategy and nothing more; it does **not** refute Lemma R and does **not** resolve #193 negatively. Lemma R, if true, must be proven directly as a metric arc-incidence estimate on the sparse realized subsystem, not lifted from a generic OSC on the full closure.

### Wall W2 — No better matrix: the crystallographic (Niven) impossibility

**In one sentence.** The construction survives only because its expand-and-twist matrix rotates by an *irrational* angle (`arccos(−1/6) ≈ 99.6°`); we prove this is not a fixable accident — any integer expand-and-twist matrix that would pass the separation screen an OSC proof needs is forced by Niven's theorem to twist by a *crystallographic* (finite-order) angle instead, and those angles make the walk periodic and hence collinear. The very feature that lets the walk dodge collinearity is inseparable from the recurrence that defeats every separation argument.

**The twist.** `M = 3·O` with `O` a Q-orthogonal rotation, and `cos θ = (tr M − λ_real)/(2·3) = (2 − 3)/6 = −1/6`, `θ ≈ 99.594°`. Because `−1/6` is rational, "is θ a rational multiple of π?" is exactly the hypothesis of Niven's theorem.

**Niven's theorem.** If θ is a rational multiple of π and cos θ is rational, then `cos θ ∈ {0, ±1/2, ±1}` — the crystallographic angles (rotation orders 1, 2, 3, 4, 6). For any integer similarity of integer ratio `r`, `cos θ = tr(M)/(2r) ∓ 1/2` is automatically rational, so Niven forces a **dichotomy**:

- **(crystallographic branch)** `cos θ ∈ {0, ±1/2, ±1}`: `O` has *finite order*, the map is a lattice symmetry, its direction sequence is eventually **periodic**, and periodicity forces three collinear points; **or**
- **(irrational branch)** `cos θ ∉ {0, ±1/2, ±1}` (as here, −1/6): `θ` is an *irrational* multiple of π, an equidistributed / recurrent rotation of the circle.

Our construction sits squarely in the irrational branch. That the crystallographic branch really collapses to collinearity we observed independently in the search phase: the periodic matrix (e.g. `M³ = 2I`) "densifies every level and must eventually jam", and "adjacent identical tiles are always fatal (anchors 0, D, 2D collinear)" is the periodicity ⇒ collinearity mechanism made concrete. This is the same obstruction Gerver–Ramsey exploit in the plane.

**Why "just pick a better matrix" is impossible.** The hope: replace `M` by another expand-and-twist integer similarity `M′` (irrational twist, so still dodging periodicity) that *additionally* satisfies the absorbing-separation screen an OSC proof needs — a *p*-adic non-degeneracy condition on `cof(M′)` at every prime `p | r`. We proved it cannot be met:

> **Impossibility theorem (integer expand-and-twist similarity).** For an integer similarity `M′` of ratio `r`:
> screen passes at ALL primes `p | r` ⇔ `SNF_ℤ(M′) = diag(r,r,r) = r·I` ⇔ `M′ = r·W` with `W` integer ⇔ `W = M′/r` is an integral isometry (a signed permutation, hence FINITE order) ⇔ the twist angle is a rational multiple of π (Niven ⇒ crystallographic).

The middle links are pure lattice theory: an integer orthogonal matrix is a signed permutation (the hyperoctahedral group), which has finite order; a finite-order rotation is crystallographic; Niven pins its cosine to {0, ±1/2, ±1}. **Contrapositive:** no integer similarity with an *irrational* twist can pass the screen.

**Empirical seal (re-run in PyPy).** Enumerating *all* integer Euclidean similarities `MᵀM = r²I` with `2 ≤ r ≤ 12`, entries in [−6, 6] (including axis-free 3D-mixing rotations) yields **504** matrices with irrational twist, and **0** pass the screen at all primes dividing `r`. The **control** — rational-twist matrices `r·(signed permutation)` — *all* pass (verified for r = 2, 3, 5, 6, 10). Exactly the predicted dichotomy. For `M` itself, `cof(M) = 3·N` with `rank(N mod 3) = 1`, so it **fails** the screen at p = 3 (`SNF_ℤ(M) = diag(1,3,9) ≠ diag(3,3,3)`) — it fails for the same reason it works: its twist is irrational.

**Honest scope.** (i) The theorem shows no irrational-twist integer similarity passes the *multi-prime* screen; that screen is *necessary* for the OSC plateau only if the OSC descent is genuinely governed by all primes dividing `r` at once. The residual loophole is recorded honestly: if the descent were governed by a *single* prime, a composite-ratio candidate like `M′ = 2A` (r = 10) is a genuine p = 2 plateau (passes at p = 2, fails only at p = 5), and which single prime governs r = 10 is unresolved. (ii) Nothing here proves the walk cannot exist — it proves the *algebraic-similarity design lever* cannot be tuned to make an OSC finiteness proof go through while keeping the anti-collinearity twist. The recurrence and the collinearity-avoidance are two faces of Niven's dichotomy; you cannot buy one without paying the other. That inseparability is the wall.

### Wall W3 — Local-automaton impossibility: no finite-window rule can force the walk apart

**In one sentence.** The most natural way to *prove* the walk never puts three points on a line would be a local rule — a bookkeeping gadget watching a bounded number of steps around each vertex and ruling out collinearity as it goes; W3 shows, by exhaustively building that gadget, that no such finite-window rule can work, because the gadget's state graph is a single tightly-connected blob that always regenerates every collinear configuration you tried to forbid.

**The object.** Via the exact reduction (§3), `Δ₁ × Δ₂ = Cᵍ (c₁ × c₂)` and, since `C` is invertible, *three points collinear ⟺ c₁ × c₂ = 0*. The carries live on a **single-stream automaton** over `E = D − D` (`|D| = 2103`, `|E| = 15,545`, `max Q(e) = 2116`). The contraction `|c'|_Q = (1/3)|c + e|_Q` pins every reachable carry inside `Q(c) ≤ 529`, a ball of exactly **8,649 integer lattice points** closed under all **4,979,157 legal transitions with 0 escapes** — an all-generation finiteness certificate. *(Distinction for the referee: the 8,649-state ball is the ambient closed finiteness certificate; the reachable automaton that actually forms the primitive SCC below has 1,727 states.)*

**One primitive strongly-connected component.** BFS-from-0 reaches a set `R` of **1,727 carries** (1,726 nonzero). Two decisive facts:

1. **Single SCC.** Tarjan returns `#SCCs = 1`, one component of size 1,727 that contains 0 and covers *all* nonzero states (forward-closure test: 20/20 sampled nonzero states reach all of `R`). From any carry you can drive to any other.
2. **Primitive (aperiodic).** A parity-BFS from 0 finds all 1,726 nonzero states reachable by walks of *both* even and odd length, so the digraph is non-bipartite. Strongly connected + non-bipartite ⟹ **primitive**: some `N` joins every ordered state pair by a walk of *every* length `≥ N`.

Primitivity is the engine: after any bounded prefix, the tail dynamics of two coupled streams refill to the *entire* product `R × R` at matched generation — nothing a finite window did at the start survives.

**Negation-symmetry ⇒ 863 forced antipodal survivors.** `E` is symmetric under negation, and this pushes to `R`: `R = −R`. So every nonzero `v ∈ R` has `−v ∈ R`, and each pair `(v, −v)` is parallel (`v × (−v) = 0`) — a collinear terminal. Over the 718 primitive directions of `R` this gives exactly **863 antipodal `(v, −v)` collinear pairs** that no rule respecting negation-symmetry can remove. The full parallel bad-set on `R × R` is **1,827 unordered pairs = 863 antipodal + 964 proper**, with explicit witnesses `(5,0,0)/(−5,0,0)`, `(1,1,1)/(5,5,5)`, `(−2,−2,3)/(−4,−4,6)`, each jointly reachable at matched depth with cross-product 0.

**The impotence theorem — an exhaustive two-horn dichotomy.** Can a finite, depth-independent rule near the junction sever all these parallels? No, and it splits into two exhaustive horns (labelled here HORN1 / HORN2 — these are our labels for what the scripts demonstrate, not tokens in the code):

- **HORN1 — bounded-window rules are impotent.** Take the strongest honest local rule: for the first `k = 3` joint connector steps, forbid the two arcs' steps *and* partial carries from being parallel, then let the streams run free. This reads only a fixed prefix, so it is genuinely local. The coupled BFS shows it prunes nothing that matters (per-step frontier sizes stay `≥ 8000`); by primitivity the free-product tail refills to the full `R × R`. Both streams reach all 1,727 carries post-window and the surviving parallel set is again the entire **1,827 pairs (863 antipodal)** — the window removed **zero** collinear terminals.
- **HORN2 — potent rules are circular.** The only escape from HORN1 is a rule that constrains the *arbitrary-depth* terminal carry `c_g` rather than a bounded prefix. But `c₁_g × c₂_g = 0` **is** collinearity (by §3). A rule potent enough to forbid it is not a local finite-window rule at all — it presupposes the statement to be proved. Potency ⟺ assuming the theorem: **circular.**

The horns are exhaustive (a rule either reads a bounded window or constrains the unbounded tail), so **no local finite-window rule can force the walk triple-free**, and the junction-window coupling — the sharpest local coupling available — is likewise impotent because primitivity refills `R × R` after any prefix.

**What W3 says and does not say.** A rigorous negative result about a class of proof techniques, not about the walk. The "watch a bounded neighborhood and forbid collinearity locally" strategy is dead. It says **nothing** against the walk existing — the realized single-connector walk (provable self-avoidance and triple-freeness on the 311,738-point record) dodges all these menu-closure parallels; the closure's freedom to mix connectors is what this wall exploits and the realized subsystem does not have. W3 maps the boundary: a proof must be genuinely global/non-local, reaching past every bounded window into the arbitrary-depth carry.

### Wall W4 — Metric separation is exactly zero on the true menu-closure

**In plain terms.** The most natural way to prove the walk never crowds is to show that any two "branches" passing through the same small ball keep a fixed minimum distance apart — a positive *separation constant*. If it existed, Lemma R would follow almost for free. W4 proves that this constant is not merely small but *exactly zero*: the construction contains an exact integer coincidence that drives separation to 0 at the shallowest possible depth, and every attempt to engineer it away either reproduces the coincidence or only hides it behind a search-window artifact. The positive-separation form of the lemma is therefore **provably false**.

**The object being bounded.** With `E = D − D`, two addresses reaching the same anchor differ by `Δ = M^J · B`, where the residual geometry lives in the **normalized telescoping bracket**

    B_J = δ_J + M⁻¹( δ_{J−1} + M⁻¹( δ_{J−2} + … ) ),   δ_* ∈ E,  δ_J ≠ 0.

A uniform separation `c > 0` is exactly `μ := inf { |B_J| : nontrivial address, δ_J ≠ 0 } > 0`. Because `M` is an exact ratio-3 Q-similarity, `|Δ| = 3^J · |B_J|_Q`, so `μ > 0` would give the arc-incidence bound directly. W4 computes `μ` exactly. Re-verified against the actual repo digit set: `|D| = 2103`, `|E| = 15,545`, `max|E|_Q = 2116`, `0 ∈ E`, and `E` spans coordinates −12…12 on each axis.

**The exact depth-1 zero-cycle: μ = 0, attained.** The infimum is not approached — it is **hit exactly at depth J = 1** by an integer zero-cycle. Take

    e₁ = ( 4,  1, −4) ∈ E   (Q = 126)
    e₀ = (−12, −12, −7) ∈ E   (Q = 1134)

Then `M·(4,1,−4) = (12,12,7) = −(−12,−12,−7) = −e₀`, so `e₀ + M·e₁ = (0,0,0)` and the bracket collapses exactly: `B = e₁ + M⁻¹ e₀ = (0,0,0)` (exact, over ℚ). Both `e₁` and `−e₀ = (12,12,7)` are genuine members of `E`, and `0 ∈ E` fills the tail, so this is a *nontrivial* address (`δ_J = e₁ ≠ 0`) whose bracket is exactly zero. Hence `μ = 0`, **attained**. The same object is the shortest nontrivial `0 → 0` cycle of the length-2 carry automaton, tying W4 to the primitivity of W3. Moreover the *nonzero* brackets accumulate at 0 as well (planting a nonzero digit `n` levels below the zero-cycle gives `|B|_Q = 3^{−(n+1)}·|δ|_Q → 0`), so `μ = 0` is the limit of a whole family, not an isolated coincidence.

**Accelerating equal-moduli variants do not escape it (a new Niven mask).** The natural repair — a different, strictly-larger-inflation matrix at each level, hoping the growing scale flushes the resonant digits out of range — fails, because the coincidence rides an **`a`-independent O(1) shear channel**. For the accelerating equal-moduli family `M3(a) = [[a,0,0],[0,0,−a²],[0,1,−1]]` (all eigenvalue moduli `a`, twist `cosθ = −1/(2a)`, irrational by Niven for every `a`), the bottom companion row `(0,1,−1)` carries no `a`, so

    M3(a) · (0, −2, 0) = (0, 0, −2)   for every a = 2, 3, 5, 17, 50, …

— a resonance living entirely inside the small proxy box, *independent of the inflation `a`*. Branch-and-bound confirms `min|B_J| = 0` at every depth for the whole accelerating `M3(a)` and double-rotation `M4(a,b,c)` families. This is the W2 Niven obstruction wearing a new mask: "integer + equal moduli + irrational angle" *forces* an `a`-free shear pair, so acceleration is powerless against it.

**The prescaled "floor" is only a small-box signal.** One family — the *prescaled/squared* maps `M3(a)²` (moduli `a²`, angle `2θ`) — shows a positive bracket floor on the truncated search box: `μ_{J1..J5} ≈ 0.613, 0.732, 0.831, 0.885, 0.917`. Three checks sharply limit what this means: (1) **prescale, not acceleration, does the work** — the fixed prescaled control reproduces the first-level floor and incommensurate acceleration adds no demonstrated benefit; (2) **the floor is box-dependent** — enlarging the proxy digit box lowers it and can reintroduce exact zero; (3) the resonant digits for the baseline fixed system lie outside the smallest proxy box. The accelerating/chiral computation did **not** propagate the true `|E| = 15,545` difference closure, so one cannot transfer the baseline closure verdict to that system without another exact run.

**Conclusion.** For the baseline fixed-matrix system, the true closure `E` has `μ = inf|B_J| = 0`, attained by an exact integer zero-cycle, so its positive-metric-separation route is closed.  For the accelerating/chiral variants, the current computation is only a prescaled small-box experiment; the full 15,545-element closure remains untreated.  It supplies neither a positive separation theorem nor a full-closure refutation.

### Wall W5 — Information theory: a symbolic argument cannot see the geometry

**Lay intro.** One last hope was to argue by *information*: if the walk's turn-by-turn instruction sequence is "simple" (low-complexity), surely the curve must be geometrically thin. And if two strands ever crowd into the same small ball, maybe they'd have to be *statistically different* enough (measured by cross-entropy / KL divergence) that only a few could fit. Both intuitions are false for this construction, and we can prove they fail.

**What the lemma needs, and the two hopes.** The open link is **single-level arc-incidence**: a Chebyshev ball of radius `r` meets `O(r)` — not `O(r³)` — connector-arcs of a single generation, uniformly across scales. Two information-theoretic routes:

- **(Hope A — cross-entropy floor.)** If two arcs co-occupy one ball, force their step-distributions to diverge, `D(P_A‖P_B) ≥ floor > 0`; a positive floor caps how many arcs can stack.
- **(Hope B — subword complexity.)** Show the instruction word has low complexity `p(n) ~ K·n` (curve-like), and bridge "low symbolic complexity ⟹ low geometric crowding."

Both are measured directly on the realized gate2 walks (chains of 27,697 / 92,732 / 311,738 points at L6/L7/L8, menu alphabet of 124 letters).

**Hope A refuted: the cross-entropy / KL floor is exactly zero.**

- *Structural.* Coexisting arcs that matter are **same-birth-level**: by `W_{k+1} = M·W_k ⊔ S_k`, all level-`j` arcs are `M^j`-images of one identical level-0 interior alphabet. Same generating rule ⟹ identical step-marginals ⟹ `D(P_A‖P_B) = 0` exactly where a positive floor is needed. Geometrically these are **forced parallel lattice arcs**: they stay triple-free not by pointing in different directions but by a lateral **integer** offset (cross product `≥ 1`, never 0) — the same measure-zero integer 0-vs-≥1 gap as every other wall.
- *Measured.* Once stacking becomes nontrivial (`ρ ≥ 7`), the minimum cross-entropy and minimum pair-angle hit exactly zero: L7 `ρ=7`: `min_pair_angle = 0.0°`, `min_pair_KL = 0.0`; L7 `ρ=9`: `0.0`/`0.0`; L8 `ρ=7`: `0.0`/`0.0`. The floor *decreases toward 0 as ρ grows* — the opposite of what a capping bound requires. `KL = 0.0` even after add-α smoothing means the histograms are literally identical, confirming the structural claim. About 1% of coexisting pairs at `ρ≥7` are exactly parallel (`parallel_pair_frac ≈ 0.011`), but a lower-bound argument dies on the *single* zero-divergence pair, not the average. **Verdict: REFUTED.**

(A companion diagnostic, per-ball arc-identity entropy, is *bounded* (`≤ log(#arcs)`, `#arcs ≈ 3–5`) and flat in `ρ` — but that is a *restatement* of arc-incidence, not a derivation: the observed `O(r)` crowding is driven by a single long arc's **sojourn** through the ball, not by many arcs stacking.)

**Hope B refuted: subword complexity is near-maximal, and low complexity ≠ thin geometry.** Subword complexity `p(n)` on the L8 chain: `p(8) = 308,405`, i.e. `p(8)/L = 308405/311738 = 0.989` — essentially every length-≥8 window is distinct (same near-maximality at L6: 0.998, L7: 0.996). So in the *load-bearing finite window* the realized word is generic/high-complexity, not `p(n) ~ K·n`. The asymptotic linearity that does exist (primitivity ⟹ linearly recurrent, Durand 1998) is invisible in the finite window and comes from primitivity, **not** the irrational twist (a scale-only `3·I` control gives identical densities to 3 sig figs). And the bridge is false in general: a space-filling curve has a primitive-substitutive instruction sequence yet is a geometric blob with crowding `~ r²/r³`. Hence **low symbolic complexity provably does not imply low geometric crowding.**

**Why this is the same wall.** The only rigorous bridge from symbolic complexity to geometric `O(r)` crowding *is* the finite-window OSC / bounded-overlap hypothesis — which is arc-incidence restated. OSC-as-proven here (disjoint recursion) delivers the exponent only *asymptotically* (`r→0`), while the load-bearing quantity is the finite-window constant on `r ∈ [1,10]`. So the bridge is **non-circular only down to the already-known cubic bound, and circular for the tight sub-cubic (arc-like) bound.** Same wall, restated in information-theoretic language — bottoming out, again, at the exact-integer 0-vs-≥1 gap that density/entropy tools are constitutively blind to.

---

## 5. The global-analysis scout

Having closed the five local walls, we ran one reconnaissance pass over the heavy machinery of modern harmonic and arithmetic analysis — the tools one reaches for to prove a statement about "a set that stays spread out forever." The plain-language upshot: none of them can even see the obstruction, because the obstruction is a single exact-integer equation, and these tools only measure *how much* of something there is, never whether one specific integer is zero. The scout ranked six candidate global tools; only one survives as more than a longshot, and even that collapses into circularity on inspection.

- **Subspace / Elekes–Szabó (the sole survivor, still a longshot).** The collinearity condition, through the exact reduction, is a rank-2 minor vanishing — an *S-unit / rank-2 equation*, exactly the shape the Subspace Theorem and Elekes–Szabó (ESS) machinery are built for. So the tool genuinely fits the *form* of the problem. But ESS controls only the **non-degenerate** stratum, and a fixed exact similarity (`MᵀQM = 9Q`) manufactures self-similar, line-preserving *degenerate* families precisely where ESS is silent. The non-degeneracy hypothesis one would need is, on inspection, the theorem restated — circular — and the heights are ineffective. The only route not rated dead outright.
- **Transversality — dead.** Gives "for almost every parameter θ" conclusions; constitutively silent on the single measure-zero integer point our matrix sits at. (The Bernoulli-convolution literature is the cautionary precedent: the algebraic parameters are exactly the *exceptional* set the a.e. theorems exclude.)
- **Probabilistic / Lovász Local Lemma — dead.** Collinearity events do not decay fast enough: per-scale collinearity mass falls only **polynomially** (`≈ g^−1.6`), not exponentially, so the dependency neighbourhood outweighs the event probability and LLL never closes.
- **Fourier analysis — dead.** No self-affine invariant measure to run a decay argument on; ε-neighbourhood incidence counts diverge; nothing for a Fourier-dimension bound to bite.
- **Additive combinatorics (ESS as an incidence bound) — dead.** Yields an `o(n²)` bound on collinear triples, not zero; and any structured pole it exploits corresponds to a collinear-*abundant* regime — the wrong direction.
- **Homogeneous dynamics (Ratner / Benoist–Quint / BFLM equidistribution) — dead.** Our expansion matrix fails the BFLM hypotheses, and equidistribution statements are blind to a measure-zero condition anyway.

*(The tool verdicts are reasoned scout assessments, not machine certificates; the exact identities they invoke — `MᵀQM = 9Q`, `det C = 729` — are re-verified, but "Fourier is dead" is an argued judgment, not a theorem-with-a-certificate.)*

The scout's aggregate assessment: a genuinely global attack has roughly a **3–5%** chance of an unconditional proof with currently-known tools, concentrated almost entirely in the ESS longshot. It also issued a constructive redirect — aim creativity at the *construction* rather than the analysis (non-conformal expansion to break ESS-degeneracy and escape Niven; or a high-dimension summable menu exploiting "any n counts" via Borel–Cantelli). Both seeds were tried; the non-conformal / chiral-acceleration seed produced the most substantive new construction idea of the project but reduced back to the same open fixed-menu stitching problem.

---

## 6. The unifying theorem and honest odds

Standing back from the five walls and the global scout, one pattern is unmistakable.

> **Meta-theorem (informal).** Every route we tried collapses onto the *same* obstruction: an exact integer 0-versus-≥1 gap, or Niven's rational-angle dichotomy wearing a new mask. Density, measure, and equidistribution tools are *constitutively* blind to this obstruction, because it is a measure-zero exact-integer condition. The only residual path to an unconditional proof is a genuinely **global / non-local** argument outside every tool tried.

Two rigorous facts anchor it.

1. **The 0-versus-≥1 gap.** Three walk points are collinear exactly when an integer cross product vanishes; under `M` this pushes through `C = cof(M)` (`det 729`, invertible), so *collinear ⟺ carry-cross `c₁×c₂ = 0`*. Every quantity in the decision is an integer, so "≠ 0" is identically "|·| ≥ 1": a hard unit gap, no intermediate metric value. Tools that estimate sizes, densities, or measures cannot resolve a gap living entirely at the boundary between 0 and 1.
2. **The Niven mask.** The irrational twist the construction needs is `arccos(−1/6) ≈ 99.594°`. Niven forbids it from being a rational multiple of π (−1/6 ∉ {0, ±½, ±1}), so it is *irrational* — forced recurrent, never periodic. This same dichotomy — rational angle ⇒ periodic ⇒ collinear vs. irrational ⇒ recurrent — reappears in W2 (crystallographic no-better-matrix), W4 (metric separation), and W5 (information theory). One obstruction seen from many sides.

Four of the six global tools reduce visibly to fact (1); the matrix-redesign and construction routes reduce to fact (2). That is the sense in which the walls are not six independent dead ends but one wall with six faces.

**Honest odds** (two separate, deliberately conservative estimates):

- **Does the infinite triple-free walk exist? ~85% (historical subjective estimate).** The 311,738-point certified walk and stable finite-level density are positive evidence.  The availability values are sampled extrapolations, not non-eroding certified floors, so they should not be counted as a theorem-level input.
- **Can it be proven unconditionally with currently-known tools? Roughly 1–5%.** The figure varies by route in our records: the local-automaton program is rated ≤1% (route proven dead within its formalization), and the global-analysis scout puts the total global-attack chance at ~3–5% (nearly all of it the ESS longshot). We report the range, not a point estimate.

One-line summary: **the walk almost certainly exists; an unconditional proof almost certainly requires a genuinely new, non-local idea that no tool in the current kit supplies.**

---

## 7. What would it take, and the centaur framing

**What would close it.** Every wall points the same direction: the missing argument must be *global / non-local*. It must reach past every bounded window into the arbitrary-depth carry (W3), must not rely on any positive metric margin (W4) or any density/measure/entropy quantity (W1, W5, §5), and must survive the fact that the design lever itself is pinned by Niven (W2). The one tool whose *form* fits — Subspace / Elekes–Szabó — needs a non-degeneracy input that is currently the theorem restated; making it non-circular (e.g. by a genuinely non-conformal construction that breaks the self-similar degenerate stratum while still dodging periodicity) is the single most promising, and still speculative, direction. Absent that, the direct reachable-state Lemma A remains open.  Exact L7 cones now give finite floors 59 and six, plus a precommitted early action with a frozen-future floor 45 and one 2,747-survivor successor edge.  None supplies a causal cross-level fixed point or the required far-tail rank.

**The centaur framing.** This is, as far as we know, the **first sustained assault on a hard open Erdős problem by an AI–human "centaur"** — a human steering, an AI system doing all of the mathematics and computation, with **no participating human mathematicians**. The division of labour was strict: the human supplied direction, creative seeds (the "imbrication / dishwasher" enlargement, the fishing-line-spool coordinate, the "dark-energy + chirality" accelerating-expansion idea), and go/no-go judgment; every construction, proof attempt, certificate, and refutation was generated and machine-checked by the agentic system.

Two features keep the claim honest rather than hype:

- **What was actually produced is a corrected conditional theorem plus a map of why the endpoint resists.** The affirmative answer stands only modulo the direct reachable-state safety Lemma A, including far secants; generic bounded crowding is insufficient.  It is **not** an unconditional resolution.
- **Adversarial self-verification was essential and load-bearing.** This problem has a documented history of agent overclaims; across the multi-agent rounds the skeptic/verifier phase caught five to six distinct "the lemma is proven" overclaims (agents repeatedly mistaking finite-depth or p-adic readings for the full statement). The guardrail — never trust a positive verdict without the across-generations, geometric-not-p-adic recheck — is the reason the conditional theorem here can be trusted where earlier drafts could not.

**Bottom line.** The repository contains exceptional finite `Z^3` evidence but
no unconditional solution.  Closing the scale-and-rotate route requires the
global reachable-state safety Lemma A; the old bounded-crowding Lemma R does
not suffice.
