# Lattice-envelope whole-word action region

Status: exact finite certificate.  The algebraic theorem, four full-cache
action chunks, merged ordinal bitsets, and compact summary are complete.

## 1. Exact whole-word graph

For a parent step `s`, let `C_s` be the full candidate-site set.  A whole
connector word `w` has proper-interior set `I_s(w)` and ordered slot roles

```text
P_s(w) = ((t_j,c_j))_j.
```

Its exact direction-blind, source-site-compatible edge set is

```text
E_s(w) = { ((s,x),(t_j,M(x-c_j))) :
             x in C_s \ I_s(w), M(x-c_j) in C_(t_j) }.
```

This definition is atomic in `w`: its slots and its interior-avoidance mask
are never taken from different words.

## 2. The image-lattice envelope

For

```text
M(a,b,d) = (3a,-3d,3b-d),
```

the exact image lattice is

```text
L = M Z^3
  = { (X,Y,Z) in Z^3 : X = 0 (mod 3), Y = 0 (mod 3),
                            Y-3Z = 0 (mod 9) }.
```

Both directions are elementary.  Every image has the three displayed
congruences.  Conversely, if they hold, then

```text
a = X/3,  d = -Y/3,  b = (Z-Y/3)/3
```

are integers and `M(a,b,d)=(X,Y,Z)`.

Every direction-blind edge has target site `M(x-c)`, hence its target lies in
`L`.  Consequently every vertex on every directed cycle has its site in `L`.
Define the finite envelope

```text
T = { (s,x) : x in C_s intersect L }.
```

The prepared candidate table contains exactly 780 such vertices, spread over
120 steps with 0--16 per step.  Their sorted record stream
`(step,x,y,z)`, with signed little-endian 64-bit fields, has SHA-256
`cb07c8c0f10f0de7d4032a346bd0a827d9dce554b777033b5c168108f4d3c09e`.
The checker recomputes these commitments from the pinned prepared table.

## 3. Zero-envelope theorem

For a role, define the exact bad-source mask

```text
B_T(s,t,c) = { x in C_s intersect L : M(x-c) in C_t }.
```

Define

```text
A_s^0 = { w in D_s :
          union_((t,c) in P_s(w)) B_T(s,t,c) is a subset of I_s(w) }.
```

### Theorem

The arbitrary-action union

```text
H^0 = union_s union_(w in A_s^0) E_s(w)
```

is acyclic.

### Proof

The subset test says exactly that `H^0` has no edge whose source lies in
`T`.  If `H^0` contained a directed cycle, every vertex on it would be the
target of the preceding edge.  The image-lattice calculation therefore puts
every cycle vertex in `T`.  Each cycle edge would then have its source in
`T`, contradicting the definition of `H^0`.

The subset test retains the crucial same-word exception: a role may map an
envelope source to a candidate target, yet no edge is induced when that
source is a proper interior of the very same chosen word.

This theorem needs neither the 4.77-million-edge graph reconstruction nor
the previously reported 768-vertex SCC.  The 780-vertex algebraic envelope
is 12 vertices larger than that SCC, but the proof does not rely on this
comparison.

## 4. Guaranteed ordered-envelope fallback

The zero-envelope filter is sufficient, not necessary.  Fix a total order
`pi` on `T` and retain

```text
A_s^pi = { w in D_s : every (u,v) in E_s(w) with u in T
                         satisfies pi(u) < pi(v) }.
```

Every edge target is already in `T`.  Thus any cycle is wholly inside `T`,
where the strict order rules it out.

Use a deterministic topological order of the exact 1,321-edge fixed-policy
DAG restricted to `T`.  This guarantees at least the already selected fixed
word at every step: all edges induced by those 124 words follow the common
order.  It does **not** guarantee that the fixed word is chronologically
legal at every occurrence; the exact L5 replay already refutes that stronger
claim.

The full-cache census reports both `A^0` and `A^pi`.  The latter only rejects
backward envelope edges.  Both are much less restrictive than applying the
old height-two potential to all 34,520 vertices, which retained only 601
words in total.

The exact merged census retains 8,367,038 zero-envelope words (minimum 2,570
per step) and 10,252,458 ordered-envelope words (minimum 2,570 per step).
After intersecting intrinsic lateral-fibre cleanliness, the minima are still
2,422 for both filters.  The ordered filter retains 215,647 of the 216,322
baseline projection-role masks and all 124 fixed-policy words.  These are
static action-region counts, not chronological survivor floors.

## 5. Exact resumable checker

The checker pins the metadata, compact cache, prepared candidate table,
fixed-policy result, and their producing checkers.  It reconstructs `T`, the
selected whole-word actions, and the deterministic topological order before
scanning any action.

Scan the disjoint, approximately word-slot-balanced ranges `0..32`, `33..62`,
`63..94`, and `95..123` sequentially on one low-priority thread.  For each
encountered role, cache two small integer masks over the
at-most-16 local envelope sites:

- all role sources in `T` that map to a candidate target;
- the subset whose induced edge is backward in `pi`.

For every word, OR the masks of all ordered slots, compute that same word's
exact envelope-interior mask, and apply the subset tests.  In the same pass
report:

- accepted word counts per step for both filters;
- accepted ordered projection signatures and unordered projection-role
  masks;
- intersections with intrinsic fibre cleanliness and 3-adic digit
  simplicity;
- acceptance of each of the 124 fixed-policy words;
- exact first rejected witnesses;
- packed ordinal bitsets for later chronological replay;
- role-mask and accepted-bitset digests.

An initial `0..60` attempt finished its last step at 115.17 seconds and about
60 MiB RSS, then aborted cleanly at the 115-second hard gate without
committing an artifact.  The balanced four-way split is therefore planned at
55--75 seconds and below 100 MiB per chunk.  Enforce one process, one
numerical thread, `nice >= 15`, the same 115-second work deadline, and a
280-MiB abort threshold.  The merge re-reads and validates all sidecars and
must reproduce
the pinned 12,537,146-word, 55,513,526-slot, 840,794-role, and baseline
projection censuses.

## 6. Expansion if the fixed order remains narrow

Each remaining whole word has a finite batch `F_w` of envelope-source edges.
A sound greedy expansion maintains a DAG `Q` on the 780 vertices.  It accepts
a whole-word signature only when adding **all** edges in `F_w` leaves `Q`
acyclic, then permanently adds the batch.  Round-robin admission by source
step targets minimum per-step diversity.  A 780-row bitset transitive closure
supports exact batch tests and updates.

Words may be quotiented for this isolated objective only by their exact
envelope-edge batch.  A projection mask or chronological witness must retain
an actual member word; edge equality is not a sound quotient for later
legality.

An exact optimization has a position `p_v` for each envelope vertex and a
Boolean `z_a` for every whole-word/envelope-edge signature class.  For every
`(u,v) in F_a`, impose

```text
z_a = 1  =>  p_u + 1 <= p_v.
```

Weighted per-step lower bounds can maximize the minimum retained word count;
separate coverage variables are needed for projection-role masks.  This is a
maximum-acyclic-subgraph ordering problem and may require SAT/CP-SAT CEGAR.
Any candidate is certified simply by rebuilding the accepted union and
checking one topological order.

## 7. Proof boundary

A large census gives state-independent action diversity and a common
acyclicity certificate for the synchronized direction-blind compatible
channel under arbitrary switching among retained whole words.

It does not prove that one retained word is globally legal at every
chronological stitch.  It also does not control nondegenerate selector
changes, latent empty-effect re-entry, unrelated cursor jumps, newly born
lines, or near/deep and deep/deep secants.  The next necessary experiment is
an exact chronological replay intersecting the new ordinal bitsets with the
realized legal domains, followed by a successor-closed safety policy if that
replay succeeds.
