# Coined quantum-walk experiment with Gaussian digit-sum phases

> **Status:** exploratory finite simulation. This is one chosen quantum embedding; it is
> not implied uniquely by the Erdős 193 theorem and establishes no quantum advantage.

## Model

At time `t`, a Hadamard coin is given relative phase
`u_t=i^popcount(t)` and then the left/right components shift by one lattice site.
Controls replace this sequence with homogeneous, period-four, binary Thue–Morse,
or seeded random phases. Additional variants rotate the coin axis or put the phase
in space and space–time. Spatial sequences use the two-sided index
`zigzag(x)=2x` for `x>=0` and `-2x-1` otherwise; one control shifts that index by
the seed. The initial state is `(L+iR)/sqrt(2)` at the origin.

Run parameters: `{'steps': 8192, 'seed': 193, 'models': ['homogeneous', 'gaussian_time_phase', 'gaussian_space_phase'], 'checkpoint_interval': 512}`

## Results

The exponent `beta` is fitted from `variance ~ time^beta` over the final eighth of
the run onward. Ballistic, diffusive, and localized reference values are 2, 1, and 0.

| model | beta | variance/t² | participation | P(origin) | coin-position entanglement |
|---|---:|---:|---:|---:|---:|
| `homogeneous` | 1.999999 | 0.292893 | 1525.33 | 7.77029e-05 | 0.872430 |
| `gaussian_time_phase` | 1.281821 | 0.000322725 | 67.9343 | 0.0347024 | 0.958757 |
| `gaussian_space_phase` | -0.030115 | 2.06614e-07 | 3.12467 | 0.524405 | 0.774100 |

## Automated reading

- Gaussian time modulation has `beta=1.2818`, versus
  `beta=2.0000` for the homogeneous walk.
- Its final ballistic coefficient `variance/t²=0.000322725` should be
  checked across larger powers of two before assigning an asymptotic regime.
- The spatial digit-sum phase has `beta=-0.0301`. A value well below
  two would identify deterministic suppression of ballistic transport, but finite
  runs alone cannot distinguish localization from a long crossover.

## Interpretation limits

A time-only coin remains translation invariant and is not a disordered material.
The random control is one deterministic seed, and fitted exponents are effective
finite-time slopes. A promising signal requires size scaling, multiple random
controls, spectral analysis of the unitary operator, and preferably an analytic
renormalization argument. Full dyadic records and final distributions are in JSON.
