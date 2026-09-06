# Pauli-control consequence of no three collinear vertices

> **Status:** the nonvanishing statement is an unconditional corollary of the
> Erdős 193 construction. Numerical margins below are finite-prefix diagnostics,
> not a demonstrated quantum-control application.

For a chord `A`, define `G_A=A_x X+A_y Y+A_z Z`. The Pauli identity gives

```text
[G_A,G_B] = 2 i (A cross B).sigma.
```

For every `a<b<c`, use `A=P_b-P_a` and `B=P_c-P_b`. No three vertices are
collinear, so this commutator is never zero. Moreover, `G_A`, `G_B`, and their
commutator span `su(2)`. Thus each pair is Lie-algebraically universal for a
single qubit if the two aggregate Hamiltonians can be independently addressed.
Equivalently, the finite step word has noncommuting aggregate generators for
every pair of adjacent nonempty blocks, regardless of their lengths.

Parameters: `{'points': 131072, 'max_block': 16384}`

The normalized ratio is `|A cross B|/(|A||B|)=sin(theta)`. It is the
commutator margin when both aggregate generators are normalized. The unnormalized
Pauli commutator has spectral norm `2|A cross B|`.

| equal block length | triples | min sin(theta) | median sin(theta) | min |A×B| | median |A×B| |
|---:|---:|---:|---:|---:|---:|
| 1 | 131,070 | 0.2 | 0.43969687 | 4.8989795 | 9.1651514 |
| 2 | 131,068 | 0.080629908 | 0.46423077 | 6.6332496 | 32.496154 |
| 4 | 131,064 | 0.041061231 | 0.40245959 | 12 | 109.90905 |
| 8 | 131,056 | 0.026150133 | 0.29779603 | 28.565714 | 321.47162 |
| 16 | 131,040 | 0.015384615 | 0.22378921 | 64.992307 | 939.58289 |
| 32 | 131,008 | 0.0066395996 | 0.16360682 | 107.03271 | 2712.7786 |
| 64 | 130,944 | 0.0031995898 | 0.11630975 | 208 | 7719.5316 |
| 128 | 130,816 | 0.0017876008 | 0.082859966 | 466.75047 | 21778.739 |
| 256 | 130,560 | 0.00097560976 | 0.058845609 | 1024.9995 | 61857.606 |
| 512 | 130,048 | 0.00048030018 | 0.041721977 | 2016.5079 | 175275.11 |
| 1,024 | 129,024 | 0.00024020772 | 0.0294507 | 4032 | 494451.35 |
| 2,048 | 126,976 | 0.00012109447 | 0.020747156 | 8128.5039 | 1392552.9 |
| 4,096 | 122,880 | 6.1031431e-05 | 0.01481527 | 16385 | 3977281 |
| 8,192 | 114,688 | 3.0164151e-05 | 0.010215415 | 32386.53 | 10969461 |
| 16,384 | 98,304 | 1.5317927e-05 | 0.0066081673 | 65792 | 28382389 |

## Scale dependence

For block lengths at least 64, the median
normalized margin fits approximately `L^-0.5100`.
The minimum fits approximately `L^-0.9746`.
Thus the exact all-scale noncommutation does not provide a scale-independent
normalized robustness margin. Local one-step blocks are substantially better:
their minimum `sin(theta)` is 0.200.

## Interpretation

This is a direct use of non-collinearity and can be read as a persistently
non-Abelian finite-alphabet pulse word. Conditional on independent access to
the block Hamiltonians, every adjacent block pair generates all of `su(2)`.
It may be relevant to qubit-control identifiability or protocols designed to
avoid commuting aggregate controls.
However, large normalized blocks become nearly parallel, and unitary products
depend on pulse durations and higher Magnus terms, not only vector sums. A useful
application requires a robustness theorem or a finite-prefix experimental task.
