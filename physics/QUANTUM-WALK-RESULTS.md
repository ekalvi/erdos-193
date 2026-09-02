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

Run parameters: `{'steps': 4096, 'seed': 193, 'models': ['homogeneous', 'gaussian_time_phase', 'periodic_time_phase', 'thue_morse_time_phase', 'random_time_phase', 'gaussian_time_axis', 'gaussian_space_phase', 'gaussian_space_shifted_phase', 'periodic_space_phase', 'thue_morse_space_phase', 'random_space_phase', 'gaussian_spacetime_phase'], 'checkpoint_interval': 256}`

## Results

The exponent `beta` is fitted from `variance ~ time^beta` over the final eighth of
the run onward. Ballistic, diffusive, and localized reference values are 2, 1, and 0.

| model | beta | variance/t² | participation | P(origin) | coin-position entanglement |
|---|---:|---:|---:|---:|---:|
| `homogeneous` | 1.999998 | 0.292893 | 822.188 | 0.000155387 | 0.872430 |
| `gaussian_time_phase` | 1.301288 | 0.000536564 | 56.1274 | 0.0488845 | 0.944136 |
| `periodic_time_phase` | 1.999926 | 0.0317543 | 342.294 | 0.00214666 | 0.768812 |
| `thue_morse_time_phase` | 1.877066 | 0.000947621 | 31.5954 | 0.129885 | 0.901085 |
| `random_time_phase` | 0.996773 | 0.000294777 | 86.1995 | 0.00100384 | 0.993278 |
| `gaussian_time_axis` | 1.893370 | 0.0408746 | 427.495 | 0.0293345 | 0.999992 |
| `gaussian_space_phase` | -0.043307 | 1.58974e-06 | 2.67713 | 0.585634 | 0.675942 |
| `gaussian_space_shifted_phase` | -0.075283 | 4.79482e-07 | 2.25709 | 0.643581 | 0.720771 |
| `periodic_space_phase` | 2.005051 | 0.162131 | 375.132 | 6.51702e-09 | 0.884160 |
| `thue_morse_space_phase` | 1.221314 | 0.00018561 | 9.61871 | 0.284681 | 0.915943 |
| `random_space_phase` | 0.033210 | 1.07048e-06 | 5.69118 | 0.188735 | 0.897062 |
| `gaussian_spacetime_phase` | 0.980462 | 0.000131376 | 54.5317 | 0.0497392 | 0.993858 |

## Automated reading

- Gaussian time modulation has `beta=1.3013`, versus
  `beta=2.0000` for the homogeneous walk.
- Its final ballistic coefficient `variance/t²=0.000536564` should be
  checked across larger powers of two before assigning an asymptotic regime.
- The spatial digit-sum phase has `beta=-0.0433`. A value well below
  two would identify deterministic suppression of ballistic transport, but finite
  runs alone cannot distinguish localization from a long crossover.

## Interpretation limits

A time-only coin remains translation invariant and is not a disordered material.
The random control is one deterministic seed, and fitted exponents are effective
finite-time slopes. A promising signal requires size scaling, multiple random
controls, spectral analysis of the unitary operator, and preferably an analytic
renormalization argument. Full dyadic records and final distributions are in JSON.
