# Four-dimensional lower-bound track: exact return blocks and a local obstruction

**September 6, 2026. Necessary-condition audit, not a 4D impossibility proof.**
This is separate from the [fixed-ratio certificates for Shallit's 5D candidate](SHALLIT-RATIO-DESCENT.md).
The [positive-basis minimum](../PROBLEM.md) remains unresolved.

## 1. An exact finite return alphabet

Assume an infinite four-letter triple-free word exists. Every eight-letter
factor uses all four letters: otherwise the proved ternary abelian-square
obstruction applies. Fix the letter 3 and discard the finite prefix before
its first occurrence. The remaining word has a unique decomposition

\[
(3u_0)(3u_1)(3u_2)\cdots,
\]

where each \(u_i\) is a nonempty word on \(\{0,1,2\}\), of length at most
seven, with no ordinary abelian square. Empty tails would give `33`; tails
of length eight contradict the ternary bound. Thus consecutive returns to
3 have lengths between two and eight.

The complete short-tail enumeration is:

| Tail length | Possible tails |
|---|---:|
| 1 | 3 |
| 2 | 6 |
| 3 | 12 |
| 4 | 18 |
| 5 | 30 |
| 6 | 30 |
| 7 | 18 |
| **Total** | **117** |

These 117 return words have **41 different Parikh vectors**. The full list
and count types are preserved in [the exact result](checks/four-return-blocks.json).
Each listed `3u3` is individually triple-free. This is an exact alphabet of
individually admissible short returns, not a claim that all 117 occur in one
hypothetical infinite avoider.

At return vertices, each displacement has the form
\((|u|_0,|u|_1,|u|_2,1)\). Collinearity there is proportionality of sums over
consecutive groups of these displacements. There are also vertices **inside**
returns. Replacing all 117 words by only 41 vectors loses their internal
order, so a return-vertex test alone does not encode the full original
avoidance condition. Return displacements are not three positive basis steps.

## 2. Two-return compatibility adds no unequal-length information

In an ordinary-abelian-square-free four-letter word, an unequal weak abelian
square must use all four letters. Indeed, writing its Parikh vectors as
\(a v,b v\), with primitive nonnegative integer \(v\), gives total length
at least \(3\|v\|_1\). With support at most three this exceeds the respective
one-, two-, or three-letter ordinary-square-free maximum (1, 3, or 7).

In particular such an unequal square contains at least **three occurrences
of the letter 3**: both blocks use 3, and \((a+b)v_3\ge3\).
A concatenation of two return words has only two occurrences of 3. Therefore

> A two-return concatenation avoids all weak abelian squares if and only if
> it avoids ordinary abelian squares.

The [bounded checker](four_return_blocks.mjs) independently tests all
\(117^2=13,689\) ordered pairs. Exactly 7,164 are compatible, and every weak
square test agrees with its ordinary-square counterpart.

Thus a lower-bound argument based only on this pair-compatibility graph would
not yet exploit the new unequal-length requirement. A finite return alphabet
does not by itself make global avoidance a finite-memory property.

## 3. Even a three-return local test has a periodic countermodel

The periodic word

```
(30 | 31 | 32)^omega
```

satisfies every three-consecutive-return test and uses all four letters in
every eight-letter window. In fact every factor of at most eleven steps is
triple-free. Yet it has a collinear triple at indices \((0,6,12)\), from
two identical periods. Its failure lies outside the three-return checks.

This does **not** refute a 4D impossibility theorem. It refutes the sufficiency
of these particular local conditions. The next lower-bound step must control
longer groups and interior offsets, or use a global invariant rather than
assuming finite local compatibility settles infinity.

## 4. Reproduction

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/four_return_blocks.mjs
```

Use `--write` to regenerate the deterministic evidence. The program checkpoints
completed pair rows atomically under `.checkpoint-four-return-blocks/`, with
source/dependency identity, checksum validation, timestamped logs, and
SIGINT/SIGTERM handling at row boundaries. Repeating a compatible command
resumes or reuses completed work. Logs/checkpoints are not proof artifacts.
This small complete audit supplies no new minimum-dimension bound.
