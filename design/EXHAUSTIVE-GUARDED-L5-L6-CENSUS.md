# Exact all-choice census for the consecutive guarded L5 → L6 chronology

## Scope

This is a finite reporting certificate, not an induction.  It counts every
connector satisfying the frozen guarded policy at each of the 8,295 realized
prefixes of the independently certified consecutive transition.  The complete
domain has 756,512,535 word occurrences.

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
between ranks.  Shards may run independently at low priority.  For example,
with ranges listed in `/tmp/ranges`:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  xargs -P 8 -n 2 sh -c '
    nice -n 15 python3 -B design/exhaustive_guarded_l5_l6_census.py shard \
      --first-rank "$0" --last-rank "$1" \
      --output "/tmp/guarded-census-$0-$1.json"
  ' < /tmp/ranges

python3 -B design/exhaustive_guarded_l5_l6_census.py merge \
  --chunks /tmp/guarded-census-*.json \
  --output /tmp/guarded-L5-to-L6-survivor-census-v2.json
```

The merger accepts only an exact `[0,8295)` partition, checks every rank
identity, requires all 756,512,535 outcomes to be partitioned by channel, and
emits the exact minimum and distribution.

## Proof boundary

Even a positive minimum at all 8,295 prefixes proves availability only on this
one chronology.  It does not quantify over alternate choices or all reachable
safe states and cannot be promoted to a uniform `k→k+1` theorem.
