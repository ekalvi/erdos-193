# Exact all-choice census for the consecutive guarded L5 → L6 chronology

## Scope

This is a finite reporting certificate, not an induction.  It counts every
connector satisfying the frozen guarded policy at each of the 8,295 realized
prefixes of the independently certified consecutive transition.  The complete
domain has 756,512,535 word occurrences.

## Result — CERTIFIED FINITE

All 32 disjoint shards completed, and the exact merger accepted their
`[0,8295)` partition.  Every realized prefix has at least **71** surviving
canonical guarded connectors.

| statistic | exact value |
|---|---:|
| realized prefixes | 8,295 |
| domain word occurrences | 756,512,535 |
| total surviving occurrences | 136,317,832 |
| minimum survivors at one prefix | **71** |
| median survivors | 1,750 |
| maximum survivors | 198,431 |

The unique minimum is construction rank 4,473, gap 1,958, parent step 113.  At
that prefix 71 of 5,257 words survive; the independently selected first
survivor is ordinal 112.  Selected order statistics give 233 survivors at the
1st percentile, 398 at the 5th, 535 at the 10th, and 906 at the 25th.  Thus the
certified chronology has finite local slack throughout, although this says
nothing about continuations after choosing one of the alternate survivors.

The exact first-rejection partition is:

| first failing channel | occurrences |
|---|---:|
| zero-envelope incompatible | 295,354,621 |
| exact global legality | 212,583,520 |
| occupied yz fibre | 25,561,383 |
| same-word yz fibre | 17,043,563 |
| old--new anchor cone, `J=11/3` | 37,899,986 |
| old--new anchor cone, `J=348/275` | 142,596 |
| old--new connector cone, `J=11/3` | 18,487,555 |
| old--new connector cone, `J=348/275` | 102,959 |
| same-word cone, `J=11/3` | 13,018,520 |
| same-word cone, `J=348/275` | 0 |
| survivor | 136,317,832 |

Channels are ordered, so these are a partition by first failure rather than
counts of every overlapping reason.

Certificate identities:

- full 7,079,563-byte merged artifact SHA-256:
  `a69e490c544f65f51bdb178b27cd92b8ad359cb01af52de96c3b9cc796031aa2`;
- full payload SHA-256:
  `197d600065a5611977fd06f9a5b58d600fb9e32d1fff848b0b7e343866df1d25`;
- compact committed summary:
  `guarded-L5-to-L6-survivor-census-summary.json`, SHA-256
  `b49632699f6c0c3bcad43b8282d061ffc01cdbaeb013b98d8e0d9f80eaeadb77`;
- compact payload SHA-256:
  `42a844b40b14702a029a5b5a1125f8fe5d7c26d4eac7996fe923e958c5c340d4`;
- path-normalized merged semantic SHA-256:
  `e4e1eb68ebe4fed4c72b66063fd8c2d78310d179ef3fbe0903e557e6faa8d6e0`.

The full reference file records absolute shard paths (`/private/tmp` on this
machine), so its byte hash is a local artifact identity.  The compact summary
normalizes those paths to basenames before checking the merged semantic hash;
its mathematical contents are reproducible across path layouts.

## Why atomization is exact

At one fixed chronological prefix `P`, the repository's reference connector
legality predicate has exactly two global parts.

1. Every proper interior `p` is fresh and is not collinear with two points of
   `P`.
2. No point of `P` lies on a line through two proper interiors of the same
   word.

Part 1 depends only on `p`, not on which domain word supplied it.  The optimized
`Store.legal(p)` enumerates every `q in P`, canonically primitive-normalizes
`q-p`, and rejects exactly when a direction repeats.  Direction-key packing is
injective here: the complete final coordinate spans plus the radius-eight
candidate margin are checked to be strictly below each signed 21-bit lane.
Memoizing this Boolean by `p` changes no quantifier.

For Part 2, let `d=primitive(b-a)`.  A stored point `q` lies on the line through
`a,b` exactly when

```text
q cross d = a cross d.
```

Thus building the exact set `{q cross d:q in P}` once for each direction and
querying `a cross d` is identical to the reference cross-product loop.

Likewise, whether a new point `p` makes a guarded-cone pair with an old point
is a function only of `p` and `P`; it is memoized after directly testing every
old point against both homogeneous integer equations.  Same-word cone pairs,
yz-fibre conflicts, zero-envelope membership, whole-word correlation, and
cache order are still evaluated for every word.

The complete cache is separately scanned once per shard to prove that all
12,537,146 domain words have the exact scaled parent-step endpoint.  No
endpoint, spatial, or secant-distance cutoff is used.

## Independent sentinels

- Source checkpoint SHA-256:
  `420950b5dc2bf01226d314e74389a4db1c3bff02429d993f3542b218f72277d9`.
- Independent firstness/all-pairs certificate SHA-256:
  `965f8af8ed243df271a390edad23ebf9663932a61b85bc81848b8c758061fe36`.
- At every rank, the first survivor from the full census must equal the winner
  independently audited before this census existed.
- A literal non-atomized run checked the first 14,976 words of rank 0.  The
  atomized evaluator reproduced its complete category counts and semantic
  outcome-chain SHA-256
  `a73c7a42dc839a36ed9839228a0ddecbafcde6363150752b51d45e8725e7be66`.
- The atomized rank-0 completion has 20,188 survivors among all 47,467 words;
  this is a regression sentinel, not a claim about the global minimum.

## Reproduction

Each shard is a disjoint half-open construction-rank range and is resumable
between ranks.  The exact 32-range partition is committed in
`guarded-L5-to-L6-census-ranges.txt` (SHA-256
`61dfdf1d57f2a9745b99f99546ac4d6e56fccf40d060dc04adb44920c05330a4`).
Shards may run independently at low priority:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  xargs -P 8 -n 2 sh -c '
    nice -n 15 python3 -B design/exhaustive_guarded_l5_l6_census.py shard \
      --first-rank "$0" --last-rank "$1" \
      --output "/tmp/guarded-census-$0-$1.json"
  ' < design/guarded-L5-to-L6-census-ranges.txt

chunks=$(awk '{printf "/tmp/guarded-census-%s-%s.json ",$1,$2}' \
  design/guarded-L5-to-L6-census-ranges.txt)
python3 -B design/exhaustive_guarded_l5_l6_census.py merge \
  --chunks $chunks \
  --output /tmp/guarded-L5-to-L6-survivor-census-v2.json

python3 -B design/summarize_guarded_l5_l6_census.py build \
  --full /tmp/guarded-L5-to-L6-survivor-census-v2.json \
  --output design/guarded-L5-to-L6-survivor-census-summary.json
python3 -B design/summarize_guarded_l5_l6_census.py verify \
  --input design/guarded-L5-to-L6-survivor-census-summary.json
```

The merger accepts only an exact `[0,8295)` partition, checks every rank
identity, requires all 756,512,535 outcomes to be partitioned by channel, and
emits the exact minimum and distribution.  The compact summarizer independently
reloads and verifies all 32 sealed shard files, reproduces every aggregate and
commitment from the merged records, and has a lightweight internal verifier.

## Proof boundary

Even a positive minimum at all 8,295 prefixes proves availability only on this
one chronology.  It does not quantify over alternate choices or all reachable
safe states and cannot be promoted to a uniform `k→k+1` theorem.
