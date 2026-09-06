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

Parameters: `{'max_level': 30, 'samples': 65536, 'seed': 194, 'checkpoint_interval': 2048}`

Late-level variance exponent: **1.085085**
(levels 23–30).

| level | time | variance | conservative MC relative SE | local beta |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 0.000% | — |
| 1 | 2 | 1.99999414 | 0.001% | 0.999996 |
| 2 | 4 | 4.0005894 | 0.395% | 1.000217 |
| 3 | 8 | 9.62765544 | 0.349% | 1.266972 |
| 4 | 16 | 22.5971062 | 0.327% | 1.230882 |
| 5 | 32 | 22.802509 | 0.277% | 0.013055 |
| 6 | 64 | 37.0557428 | 0.322% | 0.700505 |
| 7 | 128 | 95.0554843 | 0.379% | 1.359073 |
| 8 | 256 | 243.966004 | 0.453% | 1.359838 |
| 9 | 512 | 613.08478 | 0.524% | 1.329406 |
| 10 | 1,024 | 1402.35058 | 0.584% | 1.193689 |
| 11 | 2,048 | 3667.06905 | 0.628% | 1.386780 |
| 12 | 4,096 | 9066.85007 | 0.674% | 1.305974 |
| 14 | 16,384 | 56312.936 | 0.782% | 1.373657 |
| 16 | 65,536 | 324107.608 | 0.922% | 1.209972 |
| 18 | 262,144 | 1577289.82 | 0.902% | 1.101693 |
| 20 | 1,048,576 | 6597412.39 | 0.889% | 1.045826 |
| 22 | 4,194,304 | 28750277.2 | 0.955% | 1.029505 |
| 24 | 16,777,216 | 122151995 | 1.078% | 1.051791 |
| 26 | 67,108,864 | 558416209 | 1.332% | 1.095781 |
| 28 | 268,435,456 | 2.49790867e+09 | 1.693% | 1.084177 |
| 30 | 1,073,741,824 | 1.13346381e+10 | 2.371% | 1.098958 |

## Reading

A stable asymptotic power law would make the local exponents settle. Persistent
level-to-level motion instead indicates discrete-scale oscillation or multifractal
transport. Statistical error bars quantify only momentum quadrature, not finite-level
bias. Direct position-space simulation supplies an independent check through level 12.
