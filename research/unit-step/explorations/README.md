# Six-direction exploration of the step minimum

**September 6, 2026. All six agents completed; no exact minimum obtained.**
AI-assisted research, followed by a separate parent proof review and fresh
checker runs. This is not collaborator approval, an external referee report,
a Lean certification, or a claim of literature priority.

**Focused follow-up completed:** [Descent and automatic selectors](descent.md)
records three subsequent agents, exact failures of naive coarsening, a
fixed-menu infinite decision theorem, and an automatic-selector reduction.
An independent verifier also excludes a specified five-vector menu with gaps
up to 27 at every scale. No minimum bound changes; the unrestricted
subsequence theorem remains open.

The target is `s_*`: the minimum cardinality of **one fixed integer step menu**
supporting an infinite distinct-vertex, no-three-collinear walk in `Z³`.
The positive-basis minimum `d_*` is distinct. The established relation remains
`4 <= d_* <= s_*`; the existing six-step written construction gives the proposed
ceiling, with collaborator review still pending. See
[JOINT-MINIMUM.md](../JOINT-MINIMUM.md) and [AI-CHECKPOINT.md](../AI-CHECKPOINT.md).
The original Erdős 193 theorem is separate and unchanged.

## Results and ranking

| Track / report | Strongest outcome | Evidence and boundary |
|---|---|---|
| [Gaussian tags](gaussian-tags.md) | Necessary-and-sufficient classification of arbitrary affine state tags preserving the all-pairs valuation identity, including a constant valuation offset; at least six spatial steps for every admissible lift | Analytic argument for all sign streams and unbounded coefficients. Not a global six-step lower bound. Strongest analytic result of this round. |
| [Return blocks](return-blocks.md) | Every subsequence of the established walk with eventual index gaps at most 16 needs at least six displacements; all 1,048,575 phase/transition selectors also excluded | Exhaustive negative certificates plus proved substitution recurrence. Two independent gap implementations rerun by parent. Not an obstruction for every finite gap bound. |
| [Universal five](universal-five.md) | Exact 236-return-word two-marker formulation covering all endpoints and ratios; return-count compression and justified recurrence reductions | Analytic reductions, not a forcing theorem. Marker and gap equations still need to hold on the same intervals. |
| [New arithmetic](new-arithmetic.md) | Ramified odd-prime norm plus a fixed sum-free leading-unit certificate forces zero-density heights, incompatible with bounded positive height increments | Analytic restricted no-go theorem. A four-state alternative was proved coordinate-equivalent to the existing source. State counts are not step counts. |
| [New words](new-words.md) | Sharp all-ratios iid probability summability threshold; raw overlap-graph/marginal-only local-lemma approaches fail for every finite alphabet, also for iid bounded macroblocks | Analytic probability/method obstruction. Does not rule out conditioned or multiscale methods, and supplies no avoiding word. |
| [3D geometry](three-d-geometry.md) | Sharp 15-step maximum for the family `{a1*u,a2*u,a3*u,v,-v}`; subdiffusive substitution sources fail under every rational 3D projection; open-chamber finite projection lemma | Analytic restrictions and a finite sharpness witness. General full-rank five-step menus remain open. |

**Conclusion:** the results narrow several proof routes; none changes the
numerical bounds, proves `s_*=6`, refutes Shallit's candidate, or establishes
`d_*=s_*`. In particular, a larger restricted obstruction is not a universal
lower bound.

### Recommended next attacks

1. **Infinite-compatible descent / certificate obstruction.** The
   [focused follow-up](descent.md) refutes naive pointwise coarsening and several
   local synchronization shortcuts. A fixed-menu matrix decision theorem and
   reduction to automatic selectors now make the infinite obligation precise.
   Prove that every infinitely extendable five-menu path permits a smaller-gap
   five-menu replacement, or that every five-menu matrix orbit reaches zero.
   A single nonzero cycle would instead supply a construction. No uniform
   menu-height or automatic-state bound has been proved.
2. **Simultaneous marker-pair constraints.** All ten two-marker decompositions
   of a hypothetical five-letter word must come from the same word. Force a
   compatible marker-color and ternary-gap equality, rather than treating the
   individual finite return alphabets as a contradiction.
3. **Genuinely different construction certificates.** Leave the classified
   four-state valuation family. Screen new primitive uniform substitutions
   against the sub-square-root projection obstruction before attempting a
   fixed integer 3D realization. Conditioned/multiscale word constructions
   must evade the raw iid overlap-graph obstruction.
4. **A smaller geometric extension.** Replace the antipodal pair `v,-v` by
   unequal opposite steps `p*v,-q*v`. The current forced-return argument no
   longer works; a genuine temporal argument is required.

Further fixed-tag searches, increases to sign period, iid local-lemma weight
tuning, or longer Shallit prefixes do not address these identified gaps.
The initial round stopped before the separately requested focused follow-up.
Both are now complete; no unbounded research loop is running.

## Parent review and reproducible validation

All six first-round written arguments were read. The parent independently reran
all eight first-round executable checkers, including both bounded-gap
implementations, from fresh local checkpoints. Five further bounded checks
cover the [focused follow-up](descent.md), for thirteen research checkers.
PR review added a bounded CLI regression suite for fresh/resumed gap-checker
exit statuses, making fourteen validation stages in the combined runner.
One wording correction distinguishes **tag-height** cycle increments (sum zero)
from actual step heights (sum `4L`) in the Gaussian proof.
An independent fraction-free partition diagnostic also confirms that merely
requiring four distinct height tags is insufficient: twelve five-class
collision systems survive, but they do not satisfy the avoidance certificate.

A direct sanity example uses `a=2`, `L=4`, height tags `(0,1,2,3)`, and planar
tags `(0,0,2-2i,4-4i)`. It has five displacement vectors, but vertices at
indices 3, 4, 5 are `(2,0,12)`, `(4,0,17)`, `(6,0,22)`, a collinear triple.
Smaller menu arithmetic by itself is not a construction.

| Check rerun | Exact result |
|---|---|
| Gaussian diagnostic | 3,845 partitions; 12 unconstrained distinct-height patterns; 8,448 source-isometry pairs; 192 paired minimal-scale residue assignments |
| Selector families | All 65,535 state/phase and all 1,048,575 transition/phase selectors have six-vector witnesses; exact state-union menus reproduced |
| Gap-16 JavaScript | 35,561,089 DFS calls; no path to 512 from starts 0–15; maximum reachable index 334 |
| Gap-16 independent C++ | 42,138,404 calls; same 16 start maxima and 544-vector universe |
| Two-marker indexing | 7,638 cases; 1,886,685 exact triple comparisons; includes explicitly labeled samples, not a full five-letter search |
| Alternate arithmetic | Exact source conjugacy and norm checks; 746 finite-field permutation graphs and 617 small permutation-matrix pairs |
| iid word formula | 119,490 words; all 42 alphabet/length-pair cases agree with exact probabilities |
| Two-line geometry | 6,561 ternary words; all 560 triples of the sharp 15-step witness; symbolic obstruction at 16 |

Commands and resume semantics are in each report. For the whole bounded suite
(fresh-run runtime about 30–60 seconds on one core):

```sh
bash research/unit-step/explorations/check-all.sh
```

The research-checkpoint CI workflow runs the same bounded suite. Found
counterexamples cause the gap checker to exit nonzero on both fresh and resumed
runs; the runner must not count them as successful obstruction certificates. Local archive,
production-separation, joint-projection, and explainer checks also pass. The
GitHub workflow supplies the current remote CI status; passing checks are not
independent mathematical approval.

The accompanying [local visualization status](../../../viz/unit-step-research.html)
is explicitly research-only, not linked into public navigation and excluded
from the production Docker context. The prior decision to hide the public
six-step callout remains intact. No service was started and nothing deployed.

## Prior work supplied as read-only evidence

These branches were inspected separately during the original research runs,
not silently treated as approved results. They have since been archived on
`main`; the current report paths are linked below, with the original inspected
revisions preserved for provenance:

- `086d0f2a65a989ab5a83943e11e8cfce04e4be48`, [Track A](../tracks/A-SIX-STEP-AUDIT.md): expanded six-step proof
  audit; no core gap found; optimality under precisely fixed tags.
- `b96c2d26209d223193dc38f4741be3e9723b72d5`, [Track C](../tracks/FOUR-LETTER-RETURN-REDUCTION.md): four-letter return
  reduction and local unequal-block obstructions, not a dimension theorem.
- `e036b1efd8645442a67f492d5319c64925eecea9`, [Track D](../tracks/D-SHALLIT-PROJECTION.md): no rational 3D
  substitution-scaling projection of Shallit's word, even after blocking
  and bounded errors; arbitrary projections remain open.
- `b0d73486152a5472c788c35b86954c6e61a2f56d`, [Track B](../tracks/shallit-five/README.md): infinite fixed-ratio
  certificates at `1:1`, `1:2`, and `2:1`, and a per-ratio decision procedure;
  all-ratios avoidance remains open. Shallit's candidate is **not refuted**.

While preparing this archive PR, the separately developed
[higher-sign selector investigation](../tracks/HIGHER-SIGN-TOPOLOGIES.md) also
landed on `main`. It covers all sign streams for its stated state-only and
nonempty tail-state/block selector models, with completed block-size exclusions
through 16. The size-16 result lacks a second full-size implementation check
and external review. It does not settle arbitrary selectors or either minimum.
Those results and their CI checks are preserved, not duplicated here.

## Original research runs and limits

Six isolated agent contexts started from
`aaf038f31f1433fc083360177efe8a67b67e5cb1`. Completed runtimes were approximately
15.8–19.6 minutes per agent, within a 25-minute hard limit. Two agents shared
each of CPUs 0, 1, and 2; the parent and independent checks used CPU 3. Native
thread limits were one, with no nested delegation or package installs.

Sessions, prompts, timestamped progress/event logs, code/config identities,
isolated worktrees, and completed statuses remain under ignored
`.checkpoint-s-star-tournament/`. They are operational records, not proof
artifacts. Individual calculations checkpointed completed units where useful.
Saved sessions permit an explicit continuation; no processes remain running.
Only reports and bounded checkers were brought back from those agent contexts.
During the original research runs, no received manuscript or byline was changed
and no commit, merge, push, publication, or deployment occurred. This PR archives
the resulting notes and checkers without changing their mathematical review status.
