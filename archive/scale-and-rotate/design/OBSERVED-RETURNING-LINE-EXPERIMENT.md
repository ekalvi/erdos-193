# Observed returning-line experiment, guarded L5--L8

**Decision:** **NO-GO for another major 66,429-edge latent-family transition round. PIVOT** to the already-proved two-cone/endpoint-provenance exclusion and to honest cursor-import state.

One GO branch does fire: the existing quadratic cone invariant excludes the abstract fixed `N`-orbit in guard-preserving continuations. That is useful as an exclusion lemma, not evidence that the 66,429-edge family models reachable returns. Four pivot signals also fire: zero family coverage, rapid exact-type growth, no decreasing implemented rank, and cursor imports requiring remote address history.

## Scope and exactness

This is a bounded census of the existing exact realized `x`-parallel old--old--new secant trace. It uses the pinned guarded L5--L8 construction states; it does **not** enumerate arbitrary secant pairs, alternate histories, non-`x` directions, L9, or an all-level closure. A return is

```text
effect -> one or more exact zero-effect states -> effect.
```

Two channels are separate:

- **carriage:** the same endpoint lineage through the actual selected child slots;
- **cursor import:** the same physical line re-entering the retained state later in the same level's exact `gate` cursor order.

Every line is keyed by canonical primitive affine Pluecker data `(g,mu)`, with exact stable endpoint IDs, coordinates, birth/insertion time, level genealogy, carriage normalization, every observed effect cursor, every return interval, all implemented rank values, and latent-family membership. Cursor intervals are reconstructible from exact rank ranges, pinned construction hashes, and exact/full plus line-local stream SHA-256 commitments; the 49,025,756 silent cursor-state visits are not duplicated in the JSON.

Trace minimization removes physical identity, absolute level/gap/rank, and absolute translation. It retains channel, parent step/phase, exact relative primitive Pluecker state, exact effect mask/site offsets, silent length, and ordered transition controls. Thus “type” below is an exact local transition type, not merely the word `effect-silent-effect`.

## Ten answers

### 1. Returning lines at each level

Counts use the **terminal level** of a return. The carriage lines at L7/L8 are already among the cursor-import lines, so the union equals the cursor-import column.

| terminal level | cursor-import lines | carriage lines | union |
|---:|---:|---:|---:|
| L5 | 37 | 0 | 37 |
| L6 | 101 | 0 | 101 |
| L7 | 315 | 4 | 315 |
| L8 | 1,021 | 14 | 1,021 |

There are **1,021 distinct physical returning lines** across the bounded sample. They generate 2,970 cursor-import episodes and 18 carriage episodes.

### 2. Distinct minimized transition-trace types

| terminal level | cursor-import types | carriage types | all types at level | cumulative types |
|---:|---:|---:|---:|---:|
| L5 | 77 | 0 | 77 | 77 |
| L6 | 205 | 0 | 205 | 282 |
| L7 | 635 | 4 | 639 | 921 |
| L8 | 2,045 | 14 | 2,059 | 2,980 |

Answer: **2,980 distinct exact minimized types** among **2,988 episodes**.

### 3. Existing 66,429-edge latent-family coverage

**None.** Coverage is zero for physical lines, episodes, and trace types.

### 4. Coverage fraction and transition faithfulness

- physical lines: **0/1,021**;
- return episodes: **0/2,988**;
- exact trace types: **0/2,980**.

Transition faithfulness is therefore not applicable and cannot be claimed. The observed branches are also structurally different: cursor import has primitive divisor `1`, observed `M` carriage has divisor `3` on each edge, and the fixed latent macrocycle has divisors `9,9`.

### 5. Smallest actual returning witness outside the family

The smallest witness under `(terminal level, silent length, terminal gate rank, source gate rank, line ID)` is a one-silent-cursor L5 import:

```text
line  697ca2bdf93569ed454ed0e5871ef4e84f87e7624adea604911e81a45ccec873
trace 84384cd432f796d70949b3fc437461f462daff5c5c49ea7e716f6c6ca8d69914
birth L4: P767=(-117,261,-210), P776=(-135,261,-210)
insertion: base-path index 776
birth chord=(-18,0,0), content=18, canonical sign flip
birth token:  g=(1,0,0), mu=(0,-210,-261)
L5 global token: g=(1,0,0), mu=(0,993,-630)

rank 562, gap 767, anchor=(-351,630,993), word=(15,0,50,11):
  relative mu=(0,0,0), killed words=10,573
rank 563, gap 769, anchor=(-363,621,978), word=(25,21,30,0):
  relative mu=(0,15,-9), killed words=0
rank 564, gap 774, anchor=(-393,627,995), word=(5,26,40,5):
  relative mu=(0,-2,-3), killed words=976
net cursor translation=(-42,-3,2); normalization divisors=(1,1)
```

Exact cursor-stream SHA-256: `42ead0667feeab362719378590879202c516409ccc4bdc33f29fbce15e85befe`. Exact line-local control-stream SHA-256: `9e604bb58b42dd2ac12450edd6444c57d99cdaefc1881d0aa022c3f55892fd97`.

The smallest carriage witness is separately retained:

```text
line  df46b3c422e8f4460dc33888ce6f7e5ba083e88c8e3e7be24d84273c9d4c2c12
trace 50b9b8e9af5fce6f4ef0caa4333ae44fd374f527654b1404a417473d4dd48994
L5:G813,  step 49, relative mu=(0,4,6),  killed=210
  -- word=(54,3,28), slot=2, c=(-2,-4,3), divisor=3 -->
L6:G2748, step 28, relative mu=(0,-7,3), killed=0
  -- word=(36,25,74,15), slot=3, c=(-1,-4,-5), divisor=3 -->
L7:G9198, step 15, relative mu=(0,5,-6), killed=12,547
```

Its global moments are `(0,785,-582) -> (0,961,2355) -> (0,-8026,2883)`; all three states are in the observed Bellman core. Full endpoint provenance and every exact state/control are in the witness artifact.

### 6. Symbolic-family clustering

At coarse mechanism level there are only two families:

1. `x`-parallel same-level cursor translation;
2. `x`-parallel selected-slot carriage, `zeta' = B(zeta-c_perp)`.

At transition-sound resolution this is **not** a small finite stable family set: those mechanisms split into 2,980 exact local control types. Coarse symbolic clustering therefore does not provide the desired quotient.

### 7. Stabilization from L5 through L8

No stabilization is visible. New terminal-level type counts are

```text
77, 205, 639, 2,059
```

and cumulative counts are

```text
77, 282, 921, 2,980.
```

They continue growing substantially through L8. This is finite-sample evidence only.

### 8. Existing decreasing rank

**No.** On every observed return state:

- primitive direction is `g=(1,0,0)`;
- raw 3-adic depth, weighted projective depth, and latent depth `R` are all identically `0`;
- cone residual `F` is identically `-348`;
- all 18 carriage returns have Bellman profile `core -> core -> core`, so neither a one-edge nor the observed two-edge block decreases;
- the implemented Bellman escape inequality does not apply to unrelated same-level cursor translations.

The table also records the implemented archimedean/content shells and moment diagnostics; none strictly decreases, or decreases over one fixed bounded block, on every unpromoted observed return trace.

### 9. Simple invariant excluding `g_n=N^(2n)(55,34,18)`

**Yes, policy-relative to the existing two-cone guard.** Let

```text
q(g)=3*g_y^2-g_y*g_z+3*g_z^2,
F(g)=275*q(g)-348*g_x^2.
```

The fixed abstract `N`-orbit has `F(g_n)=0`, with `F(Ng)=9F(g)` and `F(Mg)=9F(g)`. Every observed return has `g=(1,0,0)` and hence `F=-348`. The existing guarded-entry certificate proves that the two-cone birth guard rejects new `F=0` secants, while endpoint-orbit provenance excludes inherited entry from the disjoint latent lineage.

This excludes the fixed unbounded abstract family only for continuations preserving that guard. It is not an unguarded, alternate-history, or all-level theorem.

### 10. Smallest state information distinguishing observed return traces

For the observed data, the smallest successful exact description is:

- one channel bit: carriage versus cursor import;
- parent step/phase and relative primitive Pluecker token;
- exact strict effect mask/site-offset state;
- silent-interval length;
- ordered transition controls:
  - carriage: selected word, child slot, prefix control, and primitive divisor;
  - cursor import: ordered cursor translations/phase words plus line birth/activation provenance.

Physical line identity, absolute level/gap/rank, and absolute translation can be removed. A bounded local-history state is **not** supported: silent cursor lengths range from 1 to 87,567 with 2,613 distinct lengths, and the existing cursor-jump audit remains noncongruent after exact jump, local/tile phases, and complete predecessor-core occupancy. Remote birth/address history is still needed in this sample. This is an observed lower bound on the successful state description, not a proof of global minimality.

## Artifacts and verification

| artifact | purpose | file SHA-256 | payload SHA-256 |
|---|---|---|---|
| `observed-returning-line-table.json` | complete machine-readable table | `f7f881eb8b386356818ede347fa09b81cfdcbc2b4f0f2a1b87b47bc26b8c594e` | `1199f4bf1c0d5dc469b5c9a8e41a707740f3de41419c031dad655b377be83e0a` |
| `observed-returning-line-witnesses.json` | minimal exact witnesses | `3548227f10afe97beb2d3c1c72bb3898b6fa8f4fcbdfa09397ff80e3becbc143` | `a4721044decb4be87d840d3c1f025539ad358345358b4069d2f61a4a949d8256` |
| `observed-returning-line-summary.json` | machine-readable ten answers | `395a0a5de40fbfe078a6fc6856a9b2b656671c1b0171b80f64b4ae2d8245628a` | `d1cdeb5aff1721c11d1c685cf4fcb4a219bcbb5845909c97bd29c30bc3b85565` |

Producer: `observed_returning_line_experiment.py`. Independent structural verifier: `verify_observed_returning_line_experiment.py`.

Observed verification result:

```json
{"return_episodes":2988,"returning_lines":1021,"status":"verified","trace_types":2980}
```
