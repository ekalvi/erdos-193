# AI resume checkpoint: sharp unit-step dimension

**Snapshot: September 6, 2026. Status: research WIP, not a finished joint paper.**
Start here, then read only the linked material needed for the next task.

## 1. The target and the boundary

Determine the least dimension $d_*$ admitting an infinite positive
standard-basis walk with no three collinear vertices. Prove an infinite
construction and a lower bound applying to **every** walk in smaller dimensions.
The exact [problem statement](PROBLEM.md) is the canonical short task definition.

- **Proved:** $d_*\ge4$, by unavoidable ternary abelian squares.
- **Proposed upper bound:** $d_*\le6$, pending independent review of the 6D draft.
- **Open here:** existence in 4D and 5D; no value of $d_*$ is conjectured as fact.
- **Already distinct and settled:** the original Erdős 193 construction allows
  an arbitrary finite step set in Z³, not only the three positive basis vectors.
  Its Lean theorem and site acceptance do not verify the follow-ups.

The desired research end state is a joint synthesis involving **Stijn Cambie,
Erik Kalviainen, and Jeffrey Shallit**, explaining the sharp threshold through
geometry and combinatorics. This is a proposed collaboration goal, not an agreed
new byline. Reconciliation and independent review come before journal packaging.
Do not hold the original result hostage to solving every extension.

Four-collinear constructions are secondary unless they clarify the common
mechanism. Applications are optional research questions, not established
engineering consequences. Related exploration remains separate in
[PR #38](https://github.com/ekalvi/erdos-193/pull/38) and
[PR #44](https://github.com/ekalvi/erdos-193/pull/44); those titles are not evidence
of a validated application and those branches are not folded into this checkpoint.

## 2. Read the source manuscripts with attribution

The [manuscript archive](../../paper/followups/README.md) indexes all five core
PDFs, the available editable sources, and the explicit missing-source inventory.
The [artifact catalogue](artifacts.json) supplies checksums, statuses, and text
paths. Read the original PDF when extracted mathematical text is ambiguous.

| Stage | Credit | What it contributes |
|---|---|---|
| Original finite-step Z³ theorem | Cambie and Kalviainen | Gaussian/valuation foundation; original Lean proof. |
| 16D positive unit steps | Shallit | Basis encoding, explicit morphism, word equivalence, smaller candidates. |
| 14D simplification | Cambie | Offsets identifying two pairs of spatial steps. |
| Proposed 6D improvement | Kalviainen, using Cambie's offsets and Shallit's encoding | Alternating signed-Gaussian source restricts the transition menu. |
| Four-letter weak-abelian-cube draft | Supplied by Shallit, no PDF byline; reported AI-generated | Ternary valuation and return blocks; forbids four, not three, collinear vertices after basis encoding. |

Human responsibility and source-reported AI assistance are documented per
manuscript. Do not silently assign all documents to all three people or rewrite
the original paper's Cambie–Kalviainen citation.

## 3. Proof/evidence ledger

| Claim | Actual evidence and limit |
|---|---|
| Original Erdős 193 negative answer | [Paper/source](../../paper/erdos193.tex), [Lean package](../../formal/Hilbert193/README.md), [site acceptance](https://www.erdosproblems.com/forum/thread/193/proof-claims#proof-claim-239). Applies to arbitrary finite step sets. |
| Three positive directions cannot suffice | [Short extension-tree certificate and independent exhaustive check](../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#1-why-three-positive-coordinate-directions-cannot-work): every ternary eight-letter word contains an ordinary abelian square. This finite exhaustive obstruction proves an infinite impossibility. |
| A six-coordinate construction | [Two-page draft](../../paper/unit_step_walk_N6_short.pdf), [source](../../paper/unit_step_walk_N6_short.tex), [scheme notes](../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md). Exact written argument, independent review pending, not Lean-formalized. |
| Six is optimal in the stated tagging scheme | Analytic argument in the [scheme notes](../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md#optimality-inside-this-tag-scheme). Not a global dimension lower bound. |
| Fixed transition recoding cannot give 4D/5D | [Certificates](../../results/unit-step-dimension-probe.json), [independent validator](../../design/check_unit_step_dimension_results.py): all 1,701 onto four-label codings fail within 44 steps; all 1,050 five-label codings fail within 85 steps. Does not exclude context-dependent coding. |
| Shallit's five-letter candidate survives a finite prefix | [Result](../../results/shallit-five-prefix.json): 38,416 steps, 38,417 vertices, 737,913,736 exact chord checks. **Not an infinite 5D proof.** |
| Naive substitution descent is incomplete | [Exact diagnostic](../../results/shallit-substitution-algebra.json), [derivation](../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#exact-descent-available-so-far): 170 nonzero integral boundary corrections already for equal adjacent lengths. These are not 170 actual counterexamples. |
| Four-letter cube draft | [Review notes](../../design/WEAK-ABELIAN-CUBE-DRAFT-REVIEW.md), [bounded checker](../../design/check_weak_abelian_cube_draft.mjs), [result](checks/weak-abelian-cube.json): five substitution identities and displacement rows checked; 66,248 equal-state pairs tested. Preliminary audit, not full independent certification or a novelty claim. |

The [period-8 audit](../../results/signed-gaussian-unit-step-audit.json) is
preserved, and the [period-16 audit](checks/signed-gaussian-period-16.json) was
regenerated for this checkpoint because its earlier result was temporary.
Only the two alternating patterns reach six in those finite searches (rules 85
and 170 at period 8; indices 21845 and 43690 at period 16). The
six-dimensional PDF proves existence; **it does not contain the separate
no-5D-within-scheme argument**. Keep that earlier scope correction explicit.

## 4. Construction data needed to resume

For $g_{85}$, use $\sigma(n)=\sum_j(-1)^j b_j(n)\pmod4$ and
$u_n=i^{\sigma(n)}$. The six spatial step types are

| Type | State transitions | Spatial vector |
|---|---|---|
| A | 01 | (1,0,5) |
| B | 12 | (0,3,5) |
| C | 23 | (-1,-2,5) |
| D | 30 | (0,-1,1) |
| E | 02,13 | (1,1,6) |
| F | 20,31 | (-1,-1,2) |

Rule 170 is the sign-reversed companion and gives the same dimension bound,
not literally the identical six spatial vectors. Rule 85 alone proves the
proposed existence result. The independent four-uniform transition generator
and its coding are in [the consequences note](../../design/UNIT-STEP-CONSEQUENCES.md).

Shallit's leading 5D candidate is

$$
 h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5
$$

letterwise, with fixed point starting at 0. For its incidence matrix $M$,
$F(14n)=MF(n)$, $\det M=14\cdot421$, and aligned triples descend. The missing
step is a proof covering partial blocks and **arbitrary unequal adjacent
lengths**, not a larger prefix scan. The candidate might still fail later.

## 5. Next proof-oriented work

1. **Vet and reconcile.** Independently check the 6D argument and audit the
   others with their authors. Use the [working synthesis](FRAMEWORK.md) to
   separate the shared valuation mechanism from the dimension bottleneck.
2. **Attack the exact minimum on two fronts.** Seek 4D/5D infinite constructions
   and general combinatorial obstructions. For Shallit's candidate, target a
   certified all-ratios boundary-state descent, or an exact counterexample.
3. **Do not repeat exhausted work.** Merely merging fixed g85 transitions has
   been exhaustively refuted. Any new reduction needs more than that coding.
4. **Keep an honest stopping/review checkpoint.** A sharp result is the ambition,
   not a guaranteed consequence of more AI searches. If the gap persists,
   distinguish a publishable synthesis from a complete optimality theorem.

## 6. Reproduction, limits, and preserved WIP

No Gmail access, private `/tmp` file, or prior chat is required to read and
recheck the archived PDFs and completed evidence. One editable attachment is
still missing, as explicitly recorded in the archive.

Quick archive and model checks (run from repository root):

```sh
node research/unit-step/check.mjs
node design/unit-step-explainer/test.mjs
node design/check_weak_abelian_cube_draft.mjs
```

Independently validate the saved dimension certificates and the C++ checker:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
src=design/verify_unit_step_prefix.cpp
g++ -O2 -std=c++17 -Wall -Wextra -pedantic \
  -DSOURCE_SHA=\"$(sha256sum "$src" | cut -d' ' -f1)\" \
  "$src" -o /tmp/verify_unit_step_prefix
python3 design/check_unit_step_dimension_results.py --binary /tmp/verify_unit_step_prefix
```

The preserved period-16 audit can be regenerated independently:

```sh
python3 design/signed_gaussian_unit_step_audit.py --period 16 \
  --output research/unit-step/checks/signed-gaussian-period-16.json \
  --checkpoint .checkpoint-unit-step-period-16/state.json \
  --log .checkpoint-unit-step-period-16/run.jsonl
```

Full generation commands, resume semantics, and the larger 38,416-step run are
in [the investigation](../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#4-reproduction-and-validation).
Do not rerun the large prefix by default: it cannot settle infinity. Checkpoints
and timestamped logs remain under ignored `.checkpoint-*` paths. Final evidence
is tracked separately. Enforce the repository's maximum **four aggregate CPU
cores**, and checkpoint all substantive Python work.

To regenerate searchable PDF text, using pinned extraction tooling:

```sh
uv run --with pypdf==6.17.0 python research/unit-step/extract_text.py
```

Extraction validates source hashes, atomically writes/checkpoints each PDF,
resumes compatible completed work, and rejects incompatible or corrupt state.
Text hashes are validated by `check.mjs`; inspect intentional extraction changes
rather than silently changing the immutable PDF hash.

The [interactive explainer](../../design/unit-step-explainer/README.md) includes
modular source, arithmetic/browser tests, and standalone offline HTML. It is
tracked research, not a production-site addition. Any LAN service uses root
`q5m.yaml` and the managed lifecycle; do not assume an old process or URL is alive.
The new research-only `results/` JSONs are explicitly excluded by `.dockerignore`.

The local investigation and explainer originated in commits
`0c667641d34a3ab6427d121f6640c0a44e0c013d` and
`bebc640e86903ab3c1186ec89cc197c033264034`, retained in this checkpoint branch.
Older work remains in Git history; do not replace it with a fabricated unified
proof. [All PDFs and provenance](../../paper/followups/README.md) remain indexed.

## Copyable AI task

> Read AGENTS.md and research/unit-step/AI-CHECKPOINT.md, then PROBLEM.md.
> Determine the exact minimum dimension for an infinite positive standard-basis
> walk with no three collinear vertices. Preserve author attribution and the
> distinction between the original proved theorem, unreviewed drafts, exact
> finite obstructions, and finite positive evidence. Choose one bounded,
> proof-oriented next step, state what it can establish, and preserve resumable
> results. Do not present 4D/5D as resolved or fixed-coding impossibility as a
> global lower bound. Do not publish or deploy a new result without authorization.
