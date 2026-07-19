# Paused proof state — 2026-07-18

No proof computation was left running when this checkpoint was committed.  All
large resumable artifacts remain local under `/tmp`; the hashes below identify
the exact files from which work can resume.

## Primary chronological lattice-`T` L6

- Construction: complete, all `8,267` stitches, `28,665` placed points, no
  obstruction.
- Constructor: `design/lattice_t_l6_continuation.py`, SHA-256
  `048c4c5457f75b7d45bf6f4bc22fcfec77d99b114f02e68982849db229358906`.
- Source checkpoint: `/tmp/lattice-T-chronological-L6-checkpoint-v1.json`,
  SHA-256
  `82cfa4999a6e75948c72ed34a3b9e5ac43fc3de396f24841f93644c03405c8f7`,
  payload
  `772b8ed41c2d7685b260c1ab6d0be4075499419a28703c704f82084b9d6ddcaa`.
- Maximum selected first-survivor ordinal: `19,221`.
- Independent firstness audit: complete for all `8,267` stitches, with no
  discrepancy.
- Natural-order audit: paused at point `8,233 / 28,665`, after exactly
  `33,887,028` unordered pairs, with no duplicate or collinear triple.
- Audit checkpoint:
  `/tmp/lattice-T-chronological-L6-audit-checkpoint-v1.json`, SHA-256
  `f59a887f308e47fff7105d1d1c36c94012248ceeda3bdb8d2754bcf036b665c4`.
- Auditor: `design/lattice_t_l6_audit.py`, SHA-256
  `b9f39fd20dfad194d45420b221617cf6b1baa872aa2aa1f4a38182274dece6f5`.

The construction is exact finite evidence.  It is not terminally certified
until the remaining ordered-pair scan finishes.

## Two-cone guarded lineages

- Guarded L5 is terminally and independently certified: all `2,457` stitches,
  `8,296` points, `4,211` independently reproduced cone rejections, and all
  `34,407,660` terminal pairs.  Exactly `246` target-cone pairs remain and all
  are inherited anchor--anchor pairs; no connector-born target-cone secant and
  no collinear triple remains.  The compact certificate is
  `design/lattice-T-L5-cone-guard-audit-summary.json`.
- A separate guarded L6 run, rooted in the ordinary audited `8,268`-point
  primary L5 path (not the guarded-L5 path), is paused at
  `6,348 / 8,267` stitches with no obstruction.  Its checkpoint is
  `/tmp/lattice-T-chronological-L6-cone-guard-v1.json`, SHA-256
  `9d90c43d8563ff75f859f554d0978532c15f2f008e0ffa672f2551f7f769d282`.
- `design/lattice_t_l6_cone_guard_audit.py` is independently reviewed,
  self-checked, and fail-closed pending terminal constructor pins.  Its SHA-256
  is `acdc552fbda593695f14cdbd0d176fcbdb84bf7cbe780362a5f5721212547aa7`.

These two finite successes are not consecutive levels of one guarded lineage,
and the guard covers only `J=11/3` and `J=348/275`.

## Far-secant experiments waiting on terminal L6 pins

- The exact short-return holonomy census found `3,136` affine return maps,
  `2,094` fixed points, and `47,942` primitive full-candidate guard
  polynomials outside the four known classes.  These are algebraic action
  channels, not proved reachable secants.
- `design/lattice_t_role_first_holonomy_reachability.py` is reviewed,
  syntax-checked, and fail-closed until the primary L6 terminal audit is
  sealed.  It preserves actual whole-word/slot/child-gap correlation and
  rejects the unrelated guarded-L5 lineage.
- `design/lattice_t_birth_shell_transition_v2.py` is now an honest five-corridor
  chronological mask census: one exact L5 parent and four L6 corridors, each
  scanned before and after its actual placement on the same domain.  It is not
  a repeated-state stabilization certificate.
- `design/ordered_path_matched_transition_experiment.py` is the prepared
  follow-up for poison-blind repeated-state selection and exact
  source/successor comparison.  Its source and successor classes use the same
  full `(theta, F, actual_action)` key, after static review caught and removed
  an inconsistent successor-lookahead pre-grouping.  Its SHA-256 is
  `b181b1f859a1097975b35e63b05a0a0d0c48d01a8779d8727e71e5a26fadd87e`.
  Heavy execution has not begun, and pending terminal/manifest pins keep it
  fail-closed.

The remaining theorem gap is unchanged: classify or rank every reachable
far-secant birth/import channel and prove that the resulting exact poison mask
always leaves a successor-closed legal connector.
