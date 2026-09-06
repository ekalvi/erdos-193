# Dyadic renormalization of the Gaussian-phase quantum walk

> **Status:** finite Monte Carlo integration of exact momentum-space recursions.
> This supports a quantum-walk research direction, not a quantum application of the
> Erdős 193 theorem and not an asymptotic theorem.

## Exact recursion

For a block beginning with phase offset `a`, the digit-sum word splits into an
unshifted half followed by a half with offset `a+1 (mod 4)`. With chronological
operators multiplying right-to-left,

```text
B[r+1,a](k) = B[r,a+1](k) B[r,a](k).
```

The same product rule is differentiated in momentum. Parseval's identities give
the first position moment from `-i psi† dpsi/dk` and the second from
`||dpsi/dk||²`. Momentum integration is estimated by deterministic pseudorandom
uniform samples.

Parameters: `{'max_level': 30, 'samples': 131072, 'seed': 193, 'checkpoint_interval': 2048}`

Late-level variance exponent: **1.085830**
(levels 23–30).

| level | time | variance | conservative MC relative SE | local beta |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 0.000% | — |
| 1 | 2 | 1.99997714 | 0.001% | 0.999984 |
| 2 | 4 | 4.01201788 | 0.278% | 1.004345 |
| 3 | 8 | 9.65548677 | 0.246% | 1.267021 |
| 4 | 16 | 22.6143828 | 0.231% | 1.227820 |
| 5 | 32 | 22.7873567 | 0.196% | 0.010993 |
| 6 | 64 | 37.1835997 | 0.227% | 0.706433 |
| 7 | 128 | 95.3079835 | 0.267% | 1.357931 |
| 8 | 256 | 244.421037 | 0.319% | 1.358699 |
| 9 | 512 | 614.017658 | 0.369% | 1.328912 |
| 10 | 1,024 | 1397.78171 | 0.414% | 1.186787 |
| 11 | 2,048 | 3651.14626 | 0.443% | 1.385210 |
| 12 | 4,096 | 9000.31207 | 0.476% | 1.301626 |
| 14 | 16,384 | 56478.045 | 0.553% | 1.378622 |
| 16 | 65,536 | 324848.231 | 0.651% | 1.205131 |
| 18 | 262,144 | 1586647.18 | 0.641% | 1.110652 |
| 20 | 1,048,576 | 6655809.19 | 0.631% | 1.059414 |
| 22 | 4,194,304 | 29140718.8 | 0.681% | 1.032850 |
| 24 | 16,777,216 | 124513075 | 0.768% | 1.051342 |
| 26 | 67,108,864 | 560448557 | 0.939% | 1.087563 |
| 28 | 268,435,456 | 2.52280238e+09 | 1.180% | 1.091703 |
| 30 | 1,073,741,824 | 1.15818343e+10 | 1.722% | 1.095038 |

## Reading

A stable asymptotic power law would make the local exponents settle. Persistent
level-to-level motion instead indicates discrete-scale oscillation or multifractal
transport. Statistical error bars quantify only momentum quadrature, not finite-level
bias. Direct position-space simulation supplies an independent check through level 12.
