# Preregistered role-first birth-range plan

This plan was frozen before reading any output from
`lattice_t_role_first_holonomy_reachability.py`.  It prevents favorable
later-endpoint ranges from being selected after their geometry is known.

## Frozen checker and inputs

- Checker SHA-256:
  `19b95490e8f9f74cb0ae7ea89e8caed58c36c107dcd0143ef3f280c36b388f64`.
- Primary L5 source/terminal and primary L6 source/terminal are exactly the
  immutable artifacts pinned in that checker.
- The raw short-return holonomy artifact and its compact summary are exactly
  the immutable artifacts pinned in that checker.
- Every run uses one thread, `nice >= 15`, `--max-seconds 120`,
  `--max-births 20000`, and `--max-effects 20000`.

The originally preregistered checker `735737590a1fb497...` failed closed before
scanning a birth pair because one character in its primary-L5 ordered-stream
pin was wrong; it wrote no range output.  The checker above corrects that pin
and adds explicit L5/L6 auditor, provenance, extent, result, and final-yz
checks.  This amendment was frozen before any successful range output.

## Complete deterministic partition

Scan the `l5` birth layer first and the `l6` birth layer second.  Within each
layer scan increasing half-open later-endpoint ranges

```text
[1 + 128*j, min(1 + 128*(j+1), N))
```

where `N=8268` for L5 and `N=28665` for L6.  Thus L5 has 65 initial ranges
(`j=0,...,64`) and L6 has 224 (`j=0,...,223`).  No successful, empty, or
unfavorable range may be skipped.  Output names are

```text
/tmp/lattice-T-role-first-{layer}-{first:05d}-{last:05d}-v1.json
```

and are immutable once written.

If an initial range writes no certificate because it reaches a time, matched-
birth, or effect cap, replace only that failed range by its two half-open
integer halves at the floor midpoint and scan the left half before the right.
Repeat this deterministic bisection until every endpoint ID is covered by one
successful immutable leaf certificate or a singleton range produces a
recorded hard failure.  Never raise a cap or inspect a later range to choose a
different split.

## Interpretation

Each leaf certificate is an exact no-cutoff finite census for its explicit
endpoint-ID partition.  Even complete coverage proves only which abstract
short-return guard channels occur and affect connector domains on these two
pinned finite lineages.  It does not prove repeatability, tail contraction,
uniform availability, a safety greatest fixed point, or an unconditional
theorem.
