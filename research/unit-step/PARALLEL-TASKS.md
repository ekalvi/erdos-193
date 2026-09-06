# Parallel research handoffs

**Research WIP, September 6, 2026.** Start new sessions from a fresh `origin/main`
after the checkpoint PR is merged. Use a separate branch/worktree for each
track; do not share a working directory or edit another session's checkpoints.
These are proposed bounded tasks, not four promised solutions or an agreed
publication plan.

Read [AGENTS.md](../../AGENTS.md), the [AI checkpoint](AI-CHECKPOINT.md), and
[JOINT-MINIMUM.md](JOINT-MINIMUM.md) first. The target is exact $(d_*,s_*)$.
The original Erdős 193 theorem is settled; the follow-up bounds, infinite
proofs, finite evidence, and construction-family limits must remain distinct.

## Shared operating rules

- The host-wide limit is **four aggregate CPU cores across all sessions**,
  not four per session. Default to one computational core per active track;
  coordinate before using more or running subprocesses. Keep native numerical
  thread counts at one. Do not launch an unbounded agent/worker fan-out.
- Use durable logs and identity-checked, atomic checkpoints for substantive
  computations, with interruption/resume support. Do not repeat the completed
  737-million-chord scan or the exhausted fixed g85 codings by default.
- Choose one bounded proof-oriented subtask, announce its scope and ETA, and
  stop at a useful result, explicit obstruction, or honest time boundary.
- Preserve received manuscripts unchanged and retain document-specific
  attribution. An AI-assisted review is not collaborator approval or a new
  byline. Do not send correspondence, merge other tracks, or deploy a new
  result without authorization.
- Write track-specific notes under `research/unit-step/tracks/` or a clearly
  named design note. Keep logs/checkpoints out of final proof artifacts.
  Avoid concurrent edits to the central problem/checkpoint files; propose
  their updates in the track's PR for later synthesis.

## A. Independently audit the six-step / 6D proof

Suggested branch: `research/review-six-step`.

**Question:** does the existing written infinite argument establish the claimed
six-step 3D walk and hence its six-coordinate basis encoding?

Start with [the short source](../../paper/unit_step_walk_N6_short.tex), the
[original Gaussian proof](../../paper/erdos193.tex), and the
[signed-family notes](../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md).
Audit the alternating source identity, all-state tags, distinct/increasing
heights, exact occurring step menu, and the encoding implication. Review the
separate family-specific optimality argument under its actual hypotheses.

**Deliverable:** a line-by-line argument or a precisely located gap, with any
small independent checks labelled as finite. Do not equate passing prefixes
with proof, or promote scheme optimality to a global lower bound.

## B. Settle Shallit's five-letter candidate

Suggested branch: `research/shallit-five-proof`.

**Question:** does the cyclic substitution with
$h(0)=01213101314310$ and $h(r)=h(0)+r\pmod5$ avoid weak abelian squares forever?

Start with the [investigation](../../design/UNIT-STEP-4D-5D-INVESTIGATION.md),
[algebra diagnostic](../../design/shallit_substitution_algebra.py), and
[certificate validator](../../design/check_unit_step_dimension_results.py).
Aligned blocks descend; arbitrary partial boundaries and unequal interval
ratios remain unresolved. The 170 nonzero integral corrections are algebraic
possibilities, not 170 observed collinear triples. The validator independently
reconstructs their complete set and rejects missing, duplicate, or altered rows.

**Deliverable:** a bounded all-ratios boundary-state lemma advancing an infinite
proof, a rigorously justified reduction to a finite certificate, or an exact
counterexample with indices and count vectors. Do not substitute another
unbounded prefix scan for the missing argument.

## C. Attack the four-letter basis threshold

Suggested branch: `research/four-basis-threshold`.

**Question:** can an infinite four-letter word avoid adjacent nonempty blocks
with identical normalized letter counts, including unequal lengths?

Start with the [word formulation](PROBLEM.md) and the
[joint implication matrix](JOINT-MINIMUM.md#1-two-models-and-the-logic-matrix).
Choose a genuinely general necessary condition, a rigorously bounded extension
tree, or a new construction mechanism. Ordinary equal-length abelian-square
avoidance alone is insufficient. The 4D/5D failures of fixed g85 relabelings
must not be repeated or treated as universal impossibility.

**Deliverable:** one proved reduction, an exhaustive obstruction with a complete
certificate, or a new candidate with an explicit infinite-proof obligation.
A 4D impossibility theorem leaves $(5,5),(5,6),(6,6)$ under the proposed upper
bound; a 4D construction fixes only $d_*=4$, not automatically $s_*=4$.

## D. Seek economical 3D realizations

Suggested branch: `research/small-three-dimensional-menu`.

**Question:** can four or five fixed integer step vectors support an infinite
triple-free 3D walk, possibly as a projection of a basis candidate?

Start with [projection quantifiers and the rank criterion](JOINT-MINIMUM.md#4-projection-the-existential-question-versus-the-universal-one)
and the [uniformity/compactness distinction](JOINT-MINIMUM.md#5-a-second-unification-the-order-of-the-quantifiers).
For a chosen basis word, the same integer matrix must work at all lengths.
Testing one matrix can refute it; finite success alone proves no infinite
claim. Clock-height columns $(a_r,b_r,1)$ form a restricted search family,
not a normalization valid for every 3D construction.

**Deliverable:** a promising fixed menu plus an explicit arithmetic proof
obligation, a certified obstruction to a stated projection class, or a
uniform-bounded-realization lemma. A proof of a projected construction also
certifies its basis lift. Failure of one candidate to project does not prove
that the two minima differ. Do not assume all valid walks obey the 2-adic law.

## Copyable session prompt

> Work on track [A/B/C/D] in research/unit-step/PARALLEL-TASKS.md, using a new
> branch from current origin/main and a separate worktree. Read AGENTS.md,
> AI-CHECKPOINT.md, and JOINT-MINIMUM.md before choosing one bounded subtask.
> Coordinate the host-wide four-core budget; use one computational core by
> default and make substantive computations resumable. State the exact claim
> your work could establish, its assumptions, and an ETA. Preserve attribution
> and distinguish infinite proof, exhaustive finite obstruction, finite positive
> evidence, and family-specific limitations. Finish with a reproducible note,
> explicit blockers, and a proposed next step. Do not merge or deploy on your own.
