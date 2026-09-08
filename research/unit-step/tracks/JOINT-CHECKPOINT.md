# Joint-minimum checkpoint: uniform Shallit certificates and stopping points

**Packaged September 8, 2026; research from September 6–7.** AI-assisted,
computer-checked research, awaiting outside mathematical review. This is not a
completed construction, a universal lower bound, or a Lean formalization.

## Goal and unchanged bounds

The specification is [the exact joint minimum](../JOINT-MINIMUM.md): determine
both the positive-basis dimension `d_*` and the number `s_*` of fixed integer
step types for one infinite avoiding walk in 3D. The original Cambie–Kalviainen
Erdős 193 theorem is separate and settled. Shallit retains attribution for the
five-letter candidate and basis-word formulation.

This checkpoint changes **neither numerical bound**, eliminates **no possible
ordered pair**, and proves no integer-realization bridge. The unconditional
bounds remain `4 <= d_* <= s_* <= 16`. Subject to vetting the existing six-step
draft, the working pairs remain

```
(4,4), (4,5), (4,6), (5,5), (5,6), (6,6).
```

A complete proof for Shallit's basis word would give only `d_* <= 5`. An
infinite five-step integer 3D construction would improve both upper bounds.
Neither was obtained here.

## What is preserved

| Artifact | Result and scope |
|---|---|
| [Fixed-ratio descent](SHALLIT-RATIO-DESCENT.md) | Separately checked certificates for ratios 1:1, 1:2, 2:1, at all positions and lengths. These complement, not replace, the separately archived [ancestor certificates](shallit-five/README.md). |
| [Uniform neighborhood](SHALLIT-UNIFORM-NEIGHBORHOOD.md) | Full affine midpoint closure and a quantitative proof for a narrow interval around equal gaps. |
| [Wider interval](SHALLIT-INTERVAL-EXTENSION.md) | All ratios from 49:51 through 51:49; 21,694 states and 37,528,109 independently checked candidate transitions. This still does not cover 1:2 through 2:1. |
| [All-ratio direction reduction](SHALLIT-DIRECTION-REDUCTION.md) | A 3,691-state centered-return certificate excludes uniform directions; a finite-language cover excludes directions missing a letter. Positive nonuniform directions remain open. |
| [Contradiction and 4D probe](CONTRADICTION-5D-4D.md) | Necessary discrepancy growth, no contradictory universal upper estimate; a checked finite 128-step 4D witness and a partial DFS, not an infinite construction or an exhaustive 4D obstruction. |
| [Four-letter return blocks](FOUR-RETURN-BLOCKS.md) | Exact local return analysis and explicit failure of its proposed global shortcuts; no four-letter threshold theorem. |

The smaller interval certificates are retained as intermediate proof artifacts,
not advertised as separate changes in either minimum. All mathematical
interpretations of the finite certificates remain outside-review-pending.

## Inconclusive work is not a certificate

- [The full-central interval attempt](checks/shallit-extension-6.json) records
  `outcome: time_budget`: 80,878 discovered states, 80,868 completed expansions,
  and 220,418,298 transitions. It does **not** certify interval avoidance.
- [The earlier interval attempt](checks/shallit-interval-attempt.json) is also
  incomplete. Increasing either budget is not the planned proof step.
- [The saved frontier](checks/shallit-central-frontier.json) reconstructs an
  actual triple with span 18,721,559,584 and nonzero error. It is neither a
  collinear triple nor evidence of a repeatable reachable cycle. The cycle
  detector's positive regression example is explicitly synthetic.
- Literal finite affine lists cannot cover every positive ratio under the
  current guard. Factor gcds are unbounded even for full-support nonuniform
  factors. These method obstructions do not refute Shallit's word.

## Direct joint-goal attempt: stopped

The final bounded audit considered five-step subsampling of the existing
signed-Gaussian 3D walk. Its avoidance would be inherited, but an infinite
selector with one fixed five-vector menu is still missing.

The [already archived descent analysis](../explorations/descent.md) explains
why naive scaling does not preserve the menu. The source indices
`0,17,34,51,78,100,127` use five vectors, yet every rounding
`floor((n+b)/4)`, for `b=0,1,2,3`, produces six parent vectors. A direct BigInt
recheck confirmed those counts and all 35 noncollinear triples among the seven
fine vertices. This reproduces an existing obstruction, not a new result.
The archived [algebra checker](../explorations/descent-algebra-check.mjs)
reproduces the same rounding witness and is included in the validation runner.

That finite witness does not refute an infinite-only replacement theorem.
The fixed-menu decision argument and automatic-selector reduction have state
complexity depending on menu heights. No uniform five-label-preserving repair
was justified. The attempt stopped rather than launching a larger search.

## Validation and safe resumption

On Linux with Node 22, run:

```sh
bash research/unit-step/tracks/check_uniform_checkpoint.sh --help
bash research/unit-step/tracks/check_uniform_checkpoint.sh
```

The runner pins all subprocesses to one available CPU, runs the four independent
validators, byte-compares regenerated validation summaries, and checks exact
arithmetic, mutations, deterministic resumes, interruption, corrupt/config
rejection, the finite obstructions, archive links, and the explainer. It does
not restart the unfinished full-central search. CI runs it in a separate job.

Durable timestamped logs, regenerated summaries, and validated row checkpoints
stay in `.checkpoint-uniform-certificate-validation/`. On restart, validators
resume compatible progress; bounded regressions rerun. Source or certificate
changes reject incompatible checkpoints: choose a fresh directory and preserve
the old one. Packaging normalized the fixed-ratio validator's final newline,
so its older validator checkpoints intentionally have a different identity.
The original producer checkpoints are not changed or committed.

The archived final certificates suffice for fresh verification. Local ignored
search state can resume prior exploratory work, but is not part of the proof
archive and must not be treated as necessary for checking a claimed result.

## Remaining leads, not newly scheduled work

1. A positive exact five-menu certificate would improve both upper bounds;
   no promising five-vector menu is currently supplied.
2. [Simultaneous marker-pair constraints](../explorations/universal-five.md)
   offer a possible universal lower-bound route, but the forcing lemma is
   missing. A contradiction for all five-letter words would imply both minima
   are at least six, not merely exclude one construction family.
3. Shallit's remaining positive nonuniform adjacent blocks require control of
   their shared boundary and actual substitution ancestry. A full candidate
   proof would improve only the basis upper bound.

No lead is asserted to be close to completion. Independent mathematical review
and a newly chosen bounded task should precede further research. This PR is a
checkpoint, not a request to merge, publish a new theorem, or deploy the site.
