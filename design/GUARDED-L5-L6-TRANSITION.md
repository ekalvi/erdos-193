# Consecutive guarded-L5 → guarded-L6 checkpoint

This is the live proof ledger for the requested consecutive transition.  It
starts from repository commit
`e73a9cd1f7e775a98f8d4809eb18ed557c7a216f` on branch
`agent/guarded-l5-l6-20260728`.

## Ledger before the L6 run

### PROVED

**Finite-spectrum inheritance lemma.**  Put

\[
 Q(y,z)=3y^2-yz+3z^2,
 \qquad M(r,y,z)=(3r,-3z,3y-z).
\]

Then

\[
 Q(-3z,3y-z)=9Q(y,z),\qquad (3r)^2=9r^2.
\]

Thus each projective cone `J=Q/r²=constant` is invariant under `M`.
Moreover `det(M)=27`, so `M` is injective and preserves distinctness,
incidence, and non-incidence.  Let `S` be any finite collection of such
invariant projective direction sets.  Suppose a completed level has no
`S`-pair with a connector endpoint.  After applying `M`, every `S`-pair among
the new anchors is exactly the image of an old anchor--anchor `S`-pair.  If the
next connector selector rejects every old--new and same-word new--new `S`-pair,
then its completed level again has no connector-involving `S`-pair.  Induction
proves that all future `S`-pairs are images of the finite inherited base set,
**conditional on connector availability at every stitch**.

This proves inheritance, not non-emptiness of the guarded connector domain.

**Fractional backward-ghost obstruction.**  The reported one-break reduction
is correct: `||M^-1||∞=4/9`, the invariant radius is `72/5`, and an integral
suffix has 24,389 possible spatial sites.  It does not make the fractional tail
harmless or finite-state.  The bounded ghosts
`y_n=M^-n(0,1,0)=N^n(0,1,0)/9^n` have pairwise distinct lattice-line incidence
types: the integer line through `0` and `N^n(0,1,0)` contains `y_n` and no
`y_m`, `m!=n`.  Nonperiodicity follows from `u+u^-1=-17/9` for the non-x
eigenvalue ratio.  See `FRACTIONAL-GHOST-TAIL.md`.  This is an unrestricted
incidence no-go, not a reachable-birth theorem.

### CERTIFIED FINITE

The sole parent is the independently certified two-cone guarded L5 lineage on
main:

- historical source SHA-256:
  `e22a0f71516e152f93f2d8f1c25a43fe79e6b7be384196845ebdb153bb2c0e01`;
- committed terminal-summary SHA-256:
  `35ff40afbe13aa95a374285ab98994f4ed335b65d012f772a441a64789f3baf2`;
- 2,457 stitches, 8,296 points, 34,407,660 unordered pairs;
- selection-record SHA-256:
  `dc39dcf34f5a15458ecd42641d39c481ac856f19921f82edbd980c70518b73a6`;
- 4,211 independently reproduced cone rejections;
- exactly 246 terminal guarded-cone pairs, all inherited anchor--anchor pairs.

A fresh selector run reproduced the selection digest, ordered point stream,
point set, fibre state, maximum ordinal, ordinal sum, and cone-rejection count
exactly.  Its raw source SHA-256 was
`3f0fa8ba596def754c3212d979077e723b7d881a1d4291ea6d0db787915476dc`.
An independent fresh 34,407,660-pair scan then produced the deterministic sole
parent artifact:

- `/tmp/guarded-L5-parent-canonical-v1.json`;
- 458,159 bytes;
- SHA-256 `86f068ad8de131e68c44710d976bb2bec9b4872a732359540ffe51f5ba4520a7`;
- payload SHA-256
  `70a4ab65bc766b056cadb9a28699bb94667da8692dbf91575c0bae702fb6c258`.

Changing only volatile timing/RSS fields in the reproduced source and exporting
again gave a byte-identical canonical parent.

### REFUTED

The existing raw-JSON prerequisite pin is not deterministically reproducible.
A fresh exact non-x graph scan reproduced the committed mathematical counts and
semantic digests, but its SHA-256 was `6ffd4f…`, not historical `e0f576…`,
because the JSON includes elapsed time, RSS, inode, ctime, and mtime.  The same
issue propagates to action-result JSON.  This is a certificate-boundary defect,
not a detected mathematical discrepancy.

The deterministic binary action sidecar *did* reproduce byte-for-byte:

`f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb`.

All four disjoint chunk sidecars also matched their historical hashes.  New
code therefore accepts the pinned binary sidecar and its committed summary,
not a runtime-dependent raw JSON identity.

### REPORTED / UNAUDITED

All interstitial affine recurrences, q-uniform classifications, and six latent
U/V families in the task statement remain unaudited here.  None is used by
this transition.  The fractional 3-adic-tail reduction has now been audited:
its bounded/one-break part is proved, while finite spatial classification of
the fractional tail is refuted without a reachable-birth restriction.

### CERTIFIED FINITE — consecutive transition (new)

The pinned guarded-L5 state has a legal first survivor at all 8,295 guarded-L6
stitches.  The constructor completed with 28,804 placed points.  A separate
checker then reproduced every first choice with fresh fast/reference memos and
scanned all 414,820,806 terminal pairs.

- construction source: 22,851,024 bytes, SHA-256
  `420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9`;
- construction selection stream SHA-256:
  `d92fd868c5aa76b678953741545e9c6f631ab7bfc9b9fb928dc44ebd166d911f`;
- independent terminal summary: `design/guarded-L5-to-L6-audit-summary.json`,
  SHA-256
  `965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36`;
- natural 28,804-point walk: 442,351 bytes, SHA-256
  `1cacf0b2c07364fdccf2f19ca00ca8710bfda403068e14e14badb98d74280a85`;
- natural point-stream SHA-256:
  `7c091257cd2f02c683a6ec77a575c428df3eb09ce2bfed339cd4cd97ea450a70`;
- no repeated point and no collinear triple;
- exactly 246 guarded-cone pairs (`242` in `J=11/3`, `4` in
  `J=348/275`), all transformed parent-anchor pairs; zero connector-born
  guarded-cone pairs;
- selected ordinals: minimum `1`, maximum `9,325`, sum `387,776`; the exact
  distribution is committed in the terminal summary.

Guarded-cone rejections before the selected words were:

| channel | count |
|---|---:|
| old--new anchor, `J=11/3` | 1,548 |
| old--new anchor, `J=348/275` | 138 |
| old--new earlier connector, `J=11/3` | 11,707 |
| old--new earlier connector, `J=348/275` | 266 |
| same-word new--new, `J=11/3` | 23 |
| same-word new--new, `J=348/275` | 0 |

The output has exactly the same two-cone, zero-envelope, and global-fresh-yz
invariant needed to initialize guarded L7.  This is one finite consecutive
transition, not a uniform `k→k+1` theorem.

### CONJECTURED

Every reachable state satisfying this guarded invariant has a guarded
successor.  The new finite transition does not prove that universal claim.

### CERTIFIED FINITE — incomplete all-choice census

The exact all-choice census has a complete domain of 756,512,535 word
occurrences.  The literal independent implementation scanned the first 14,976
words of stitch 0 and found 6,209 survivors before its 600-second checkpoint.
This is an exact partial-domain statement only.  It does **not** provide the
requested exact minimum/distribution over all stitches.  Atom-level memoization
reproduced that prefix exactly and completed stitch 0 experimentally, but that
optimization is not yet a committed independent certificate.  The terminal
firstness certificate is unaffected.

## Frozen L6 preflight

- connector metadata SHA-256:
  `5674283f3f05a55d7a02116e0b61257ab6c955ced1b3146cc81f522bf64c701a`;
- complete cache SHA-256:
  `da6c8c39825719d379decc15d2c702f82c3f6fb66fa115bde87af49af4cb56a7`;
- action bitset SHA-256:
  `f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb`;
- connector order: all cache ordinals in increasing order;
- domain: 124 blocks, 12,537,146 words in one copy of the menu, and
  756,512,535 word occurrences across the actual 8,295 L6 gaps;
- schedule SHA-256:
  `51ff3cce63a5fe3b38dd955772cc7e8e59b3bce68050346da6c1ce01c5d69c5f`;
- transformed-anchor stream SHA-256:
  `c06bbc86e67aa03fc4b2f178f256bef16a56e4448858cf08f0cd7aeccca127b8`;
- guarded spectra: exactly `J=11/3` and `J=348/275`;
- pair classes rejected: old--new-anchor, old--new-connector, and same-word
  new--new;
- endpoint, spatial, and secant-distance cutoffs: none;
- checkpoint: sealed JSON with a mid-domain ordinal/cache cursor and a complete
  rejection-channel RLE on hard jam.

Code hashes are printed by `self-check` and `preflight` and are frozen by the
first code commit.  The independent auditor must be supplied the exact final
constructor-checkpoint SHA-256; it rescans every ordinal through every winner
and every unordered terminal point pair.  Its optional `census` mode scans all
756,512,535 domain occurrences to obtain the exact survivor distribution.

## Preregistered interpretation

- **Construction success:** proves only that this certified parent has one
  complete guarded L6 transition, pending the independent audit.
- **Construction failure:** proves that this exact first-survivor guarded policy
  jams at the first recorded stitch; every domain ordinal is classified.
- **Audit success:** certifies one finite consecutive transition and the exact
  invariant needed to initialize guarded L7.
- **Census success:** additionally gives the exact minimum and distribution of
  choices on this chronology; it still says nothing universal about alternate
  reachable states.

## Obligation graph

```text
certified guarded L5
  -> DONE: exact guarded L6 availability on this chronology
  -> DONE: independent firstness + terminal all-pairs audit
  -> OPEN: exhaustive all-choice census (finite reporting obligation)
  -> optional adversarial guarded L6 -> L7 test
  -> CURRENT THEOREM GAP: universal reachable-state non-emptiness
       requires reachable-birth exclusion/promotion for fractional tails
       + all reachable line births
       + unrelated-cursor imports
       + exclusion/control of latent U/V returns
  -> all-level induction
```
