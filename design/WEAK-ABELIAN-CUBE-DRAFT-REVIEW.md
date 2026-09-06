# Preliminary review: four letters avoiding weak abelian cubes

**September 6, 2026. Status: initial mathematical reading and bounded checks,
not full independent certification, Lean formalization, or a novelty claim.**

## Attribution and source

The [unaltered PDF](../paper/followups/2026-09-06-shallit-weak-abelian-cubes.pdf),
*A four-letter infinite word avoiding weak abelian cubes*, was supplied by
Jeffrey Shallit. No author byline appears in the document. Shallit described it
as AI-generated and not carefully checked. It explicitly credits the valuation
method of Stijn Cambie and Erik Kalviainen. These review notes and the checker
are repository-side AI-assisted work, not statements approved by the suppliers.

## What it claims

Let

| Auxiliary letter | Substitution image | Output | Return block |
|---|---|---|---|
| A | AB | 0 | 01 |
| B | AACA | 1 | 0232 |
| C | ADE | 2 | 013231 |
| D | AACCE | 3 | 02323231 |
| E | ADCCA | 3 | 01323232 |

The coded fixed point beginning at A contains no three consecutive nonempty
blocks with the same normalized letter counts. Their lengths may differ.
These are weak abelian cubes, not weak abelian squares.

The source four-letter substitution is

$$
\sigma(0)=010,\quad\sigma(1)=232,\quad
\sigma(2)=101,\quad\sigma(3)=323.
$$

## Why the written argument is plausible

1. The five intertwining identities identify the auxiliary letters with all
   successive returns to source state 0. Every return word has exactly one 0,
   at its start.
2. The ternary recursion gives, at equal endpoint states,
   $\nu_3((\Delta X)^2-3(\Delta Y)^2)=\nu_3(\Delta n)$, with the form nonzero.
   Equal terminal ternary digits permit descent; unequal terminal digits give
   a nonzero square modulo 3.
3. Four collinear return vertices would force all six index differences to
   have the same 3-adic valuation. After rescaling, four pairwise distinct
   residues modulo 3 would be required, an impossibility.
4. Return displacements depend only on the four output letters, because D and
   E both give $(-4,0,8)$. Equal normalized counts in three blocks would then
   give four collinear return vertices. The positive height component prevents
   a collapsed image.

The logical structure is coherent on an initial reading. Detailed independent
review and a literature check are still required. The
[working synthesis](../research/unit-step/FRAMEWORK.md) isolates its connection
to the binary argument without asserting a general construction for all primes.

## What was independently checked

The [bounded Node checker](check_weak_abelian_cube_draft.mjs) verifies:

- all five exact substitution identities;
- each return word's unique initial 0, count vector, and displacement;
- agreement of independently expanded finite source and return words;
- the displayed state and prefix-sum recurrences on a 6,561-letter source prefix;
- the key valuation identity for every equal-state pair among indices 0 through
  728: **66,248 pairs**;
- an explicit collinear triple in the coded basis walk, illustrating the
  difference from the main follow-up problem.

[Tracked result](../research/unit-step/checks/weak-abelian-cube.json) includes
code/PDF SHA-256, fixed parameters, the return table, and the exact triple.
Recompute and compare with it:

```sh
node design/check_weak_abelian_cube_draft.mjs
```

`--write` atomically regenerates the small result after a deliberate code or
source update. No finite-prefix check is substituted for the infinite argument.

## Consequence and a concrete scope guard

If vetted, the four-letter word gives an infinite positive basis-step walk in
4D with **no four collinear vertices**. It does not solve triple avoidance:
the word begins `0100`, so its vertices at indices 2, 3, 4 are

$$
(1,1,0,0),\quad(2,1,0,0),\quad(3,1,0,0),
$$

which are collinear. This is not a counterexample to the manuscript's theorem.
It is a reason not to confuse its conclusion with the
[minimum-dimension triples problem](../research/unit-step/PROBLEM.md).

No minimal alphabet size for cubes, engineering application, or new 4D/5D
triple-avoidance result is established by this review.
