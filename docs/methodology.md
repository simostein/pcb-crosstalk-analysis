# Methodology

All numerical results in this repository are **simulated**, not measured.
The model is a coupled-transmission-line analysis built from first
principles, verified against textbook signal-integrity references
(see `docs/references.md`). It is deliberately first-order: enough
physics to study spacing, length, plane distance, edge rate, and
impedance effects honestly, while remaining reproducible with only
NumPy/SciPy/Matplotlib.

## 1. Field solution: per-unit-length C and L matrices

For each cross-section (trace width `W`, edge-to-edge spacing `S`,
dielectric height `h`, relative permittivity `er = 4.0`), we solve
`div(eps * grad(phi)) = 0` on a 2-D grid (0.25 mil cell) covering the
substrate plus an air region above, with a solid ground plane at the
bottom and distant grounded truncation boundaries. Two excitations
(1 V on line 1, then on line 2) give the 2x2 Maxwell capacitance
matrix `C'` from the outward electric flux around each conductor.

Repeating the solve with `er = 1` gives the free-space matrix `C0'`,
from which the external inductance matrix follows under the quasi-TEM
assumption:

```
L' = mu0 * eps0 * inv(C0')
```

The conductors are modelled with zero thickness and no solder mask.
Conductor and dielectric loss are omitted (lossless line).

## 2. Modal propagation

The symmetric pair is diagonalised into even/odd modes with
impedances `Ze, Zo = sqrt(L/C)` and delays `tau = sqrt(L*C)` per mode.
Each mode propagates as a lossy-free transmission line of the coupled
length, driven by a Thevenin source (`Rs = 40 ohm`) into a load
(`RL = 50 ohm`) per conductor. The far-end victim voltage is
`0.5 * (Ve - Vo)` evaluated in the frequency domain and transformed
back for a trapezoidal source pulse (1.2 V swing, 250 ps 10-90 %
rise time, 9 ns flat top so the tail returns to zero and no FFT
wraparound contaminates the window).

## 3. What the model supports - and what it does not

| Trace separation S (mutual C/L fall with distance) | Loss, dispersion, solder mask, glass weave |
| Coupled length (modal delay x length) | Vias, connectors, package coupling, stitching vias |
| Plane distance h (field confinement) | Receiver nonlinearity, equalisation |
| Rise time / source amplitude (linear scaling checks) | Stripline, differential pairs, guard traces |
| Near-end (NEXT) and far-end (FEXT) victim voltage | |
| Single-ended microstrip only | |

Guard traces, via stitching, and stripline are therefore discussed
only qualitatively in the article - the model cannot generate numbers
for them, and we do not invent any.

## 4. Fair-comparison rules

* Baseline and improved cases use the **same** stimulus, terminations,
  coupled length (3 in), and post-processing window (0.5-4 ns).
* Sweeps vary **one** variable at a time.
* The stackup sweep (`h = 2..6 mil`) keeps `W = 4 mil` fixed, so the
  geometric-mean impedance shifts with `h` (reported in
  `data/stackup_sweep.csv`). The improved layout narrows `W` to 3 mil
  at `h = 2 mil` to bring impedance back toward the baseline value -
  this is stated wherever the stackup result is used, so the two
  studies are never silently mixed.
* Peak metric: maximum absolute far-end victim voltage in the window.
  The waveform is predominantly negative-going FEXT-type, so the
  positive and negative peaks are reported separately in the CSVs.

## 6. Why the air-run gives the inductance matrix

For a multiconductor line in a homogeneous medium, propagation is TEM
and the per-unit-length matrices satisfy `L*C = mu*eps*I`. Replace the
substrate by vacuum (`C -> C0`) and the wave speed must be `c`, so
`L*C0 = mu0*eps0*I`, i.e. `L = mu0*eps0*inv(C0)`. The external
inductance depends only on conductor geometry and the (non-magnetic)
surroundings, so this `L` remains the correct external inductance when
the dielectric is restored - the dielectric enters only through `C`.
Conductor internal inductance and skin-effect redistribution are not
modelled (zero-thickness conductors); the model is quasi-TEM, not
full-wave. References: C. R. Paul, *Analysis of Multiconductor
Transmission Lines* (2nd ed., Wiley), Ch. 3-5; E. Bogatin, *Signal
and Power Integrity - Simplified* (3rd ed.), Ch. 2-3; B. Simonovich,
"Coupled Transmission Lines and Crosstalk," Signal Integrity Journal,
2022. In code, `C` is the Maxwell capacitance matrix with the real
dielectric stack, `C0` the same geometry in vacuo, and both are
explicitly symmetrised before inversion and modal reduction.

## 7. Stimulus definition

The source is an illustrative high-speed digital edge, not the edge of
any claimed DDR generation or interface standard: 1.2 V trapezoidal
step, 250 ps 10-90 % rise time (312.5 ps 0-100 % ramp), ~9 ns flat top
returning to zero (avoids FFT wraparound), 40 ohm Thevenin source per
conductor, 50 ohm load per conductor. The 250 ps value was chosen as a
representative sub-nanosecond edge that exercises modal delay skew
(roughly 150 ps/in) over inch-scale coupling - fast enough to show
FEXT-type structure, slow enough for the quasi-TEM lossless model.

## 8. Constant-impedance studies and their framing

The v1 fixed-width stackup sweep varies `h` at fixed `W`, so impedance
shifts with it (48-80 ohm); it is kept as a raw geometry study and
labelled accordingly. The constant-impedance studies instead retune
`W` at each `(S, h)` so the geometric-mean impedance matches the
baseline value 60.14 ohm within 0.5 ohm. Two geometric variables
change there, so they are described as constant-impedance studies
answering "how does coupling change when the trace moves relative to
its plane at fixed impedance" - never as varying `h` alone. 60.1 ohm
is the baseline's own impedance, chosen for comparability, not as a
universal target.

## 9. Reproducibility versus validity

Bit-identical regeneration of CSVs/figures (verified by clean
rebuilds) proves the code is reproducible. Physical validity is argued
separately (`src/validate_model.py`, `src/robust_check.py`,
`data/validation_summary.json`, `data/robustness.json`):

* Grid convergence (dx = 0.5/0.25/0.125 mil): peak far-end voltage
  30.82, 33.46, 34.72 mV - refinement steps of -7.9 % and -3.6 %.
  The production grid (0.25) sits ~7 % below the Richardson
  extrapolation, so absolute millivolts carry that discretization
  bias; ratios and rankings (the basis of every design conclusion)
  are far less sensitive.
* Domain convergence (half-width/top = 30/20, 45/30, 60/40 mil):
  33.46, 37.28, 38.72 mV - steps of -10.3 % and -3.7 %. Walls at
  +-30 mil shunt fringe field and suppress absolute peaks ~15 % vs
  the extrapolated open boundary. Spot-checking the four controlled
  cases on the larger domain moves reductions only a few points
  (47.1 -> 43.1, 17.9 -> 21.3, 63.7 -> 62.7 %): the headline and the
  ranking survive.
* Hammerstad-Jansen isolated-line benchmark (zero thickness both
  sides, S=40 line vs closed form): 61.24 vs 64.15 ohm, error -4.5 %,
  with effective-Er agreement 3.077 vs 2.974. The residual is the
  documented boundary shunt capacitance, not a coding error.
* Large-separation limit: mutual C 0.04 %, mutual L 0.21 % of
  self terms, Ze-Zo = 0.15 ohm, victim 0.94 mV (2.8 % of baseline)
  scaling with length - genuine weak coupling, not a noise floor.
* Zero coupled length: exactly 0.000 mV at both ends.
* NEXT: positive plateau from source launch, duration matching the
  round trip (0.91 vs 0.88 ns at 3 in), saturating with length
  (28.37, 30.49, 31.73 mV at 1/3/5 in) while FEXT accumulates.
* Width tuning is limited by FDM staircasing: conductor edges snap to
  0.25 mil cells, so Z(W) moves in ~1-2 ohm steps at small h and the
  tuner cannot always reach +-0.5 ohm (achieved +0.45, -1.21,
  -1.04 ohm). A +-1-snap sensitivity check moves peaks 0-2.9 %,
  bounding the mismatch impact; achieved Z is reported per case,
  never hidden.

## 10. Earlier verification (v1, preserved)

* `C'` symmetry and passivity sanity checks (reciprocity enforced by
  explicit symmetrisation; diagonal dominance confirmed).
* Homogeneous-medium limit (`er = 1`): even/odd delays converge, and
  the victim response collapses toward zero as expected for a
  velocity-matched pair.
* Large-spacing limit: mutual terms decay and victim peaks shrink
  monotonically (see `data/spacing_sweep.csv`).
* Baseline cross-check: the baseline peak (33.46 mV) reproduces the
  independently generated value from the earlier validated model run
  (`Crosstalk_Figure4_Simulation_Parameters.json`, same equations).
* Every number quoted in `README.md` / `article.md` is read back from
  the CSVs by the review step, not hand-copied.
