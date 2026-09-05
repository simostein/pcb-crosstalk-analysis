# PCB Crosstalk Analysis and Reduction

## The setup

I routed two 4-mil microstrip traces on 4-mil spacing, 3 mil over the
plane, running parallel for 3 inches. One carries a 1.2 V step with a
250 ps edge; the other sits quiet, terminated in 50 ohms. That is the
whole experiment: how much of the edge shows up where it was never
invited, and what layout changes actually push it back down.

The baseline is deliberately tight. At 1W spacing the aggressor's
fringe field terminates on the victim almost as readily as on the
plane, and three inches of adjacency gives the coupling room to
accumulate. The stackup (h = 3 mil, er = 4.0) is an ordinary
multilayer build - nothing exotic, which is the point. Most crosstalk
problems look exactly this mundane.

## How I modelled it

No full-wave solver was practical for a reproducible article project,
so I built a coupled-transmission-line model from the field up
(`src/crosstalk_model.py`). A 2-D finite-difference solve gives the
capacitance matrix for the cross-section; repeating it in air gives
the inductance matrix; even/odd-mode reduction propagates the pulse
down each mode, and the victim sees half the difference. TI's layout
and DSP guides (SCAA082A, SPRU889, AN-337) plus Simonovich's coupled-line
treatment in the Signal Integrity Journal back every equation - the
full ledger is in `docs/references.md`, and the assumptions in
`docs/methodology.md`.

Two honest limits up front. The model is lossless, with
zero-thickness copper, no mask, no vias - a clean room for comparing
geometries, not a compliance sign-off. It reconstructs both victim
ends (far-end FEXT-type via modal transfer, near-end NEXT via loaded
modal input impedance), and both paths passed polarity, timing,
saturation, and zero-limit checks before anything was published.

## Baseline: 33.46 mV of uninvited signal

The baseline geometry used W = 4 mil, S = 4 mil, h = 3 mil, 3 inches
of coupling, Rs = 40 ohms, 50-ohm loads. The simulation showed a
negative-going far-end pulse peaking at **33.46 mV** - 2.8 % of the
1.2 V swing, and a model-dependent simulated value rather than a
prediction of any measured board (see Limitations). The modal numbers explain it: even-mode 66.4 ohms
against odd-mode 54.4 ohms, with 151.2 vs 143.5 ps/in of delay. That
impedance split and delay skew is the entire signal the victim
responds to; kill the split and you kill the noise.

## When the spacing was increased

I swept edge spacing from 4 to 20 mil holding everything else fixed.
The simulation showed a smooth, monotonic fall: 33.46, 28.69, 24.49,
17.69, 12.72, 9.16, 4.79, and finally 2.52 mV. This result follows
from the field geometry - each extra mil of separation moves the
victim further out of the aggressor's fringe field, shrinking mutual
capacitance and inductance together. The curve bends: the first
doubling (4 to 8 mil) removes nearly half the noise, while 16 to
20 mil buys only a couple of millivolts. That diminishing return is
worth knowing when routing gets crowded; it argues for spending
spacing budget where traces are closest, not spreading everything
evenly.

I deliberately avoid the "3W/spacing cuts crosstalk 70 %" formulation
found in some layout guides. The sweep above is what this stackup
produces. Another stackup will differ, which is why the scripts are
provided.

## What coupled length did

Varying the parallel run from 0.5 to 5 inches at the baseline
cross-section gave 9.00, 17.61, 25.45, 33.46, 41.41, and 49.42 mV -
a steady accumulation. That is the model behaving as FEXT-type theory
says it should: the modal skew acts over the whole length. I report
what the model actually produced rather than forcing a textbook line
through it, and with the caveat that near-end NEXT would saturate
past a critical length instead. Practically: break up long adjacencies, but treat
length as one lever among three, not the whole answer.

## What the plane distance did

Moving the plane from 6 mil out to 2 mil under the fixed 4-mil traces
dropped the peak from 48.35 to 23.51 mV. Closer copper pulls field
lines downward and starves the lateral path - the standard
confinement argument, confirmed numerically. But the impedance moved
with it, from 80.0 down to 48.1 ohms geometric mean. That is a
different transmission line, and comparing crosstalk across it without
saying so would be dishonest. So the stackup sweep is presented with
impedances attached.

That left the real question unanswered: what happens when the plane
moves but the impedance is held? I retuned the width at each height to
hold ~60 ohm - W grew from 2.89 mil at h=2 (4.09, 5.47, 6.50 mil at
h=3, 4, 5) to 7.53 mil at h=6 - and the far-end peaks came out 27.45,
33.46, 35.05, 33.77, 31.52 mV. Non-monotonic: the peak sits at h=4
and then falls, while the near-end peaks climb steadily (20.46,
30.49, 37.79, 43.00, 47.37 mV). Moving the reference plane while
retuning the width changes both the coupling and the even/odd-mode
velocity skew, so there is no reason FEXT must vary monotonically -
and here it doesn't. The modal data shows why: delay skew rises from
6.96 to 7.75 ps/in then falls to 5.35 ps/in across the sweep, while
coupling magnitude keeps growing. Far-end voltage is the product of
the two, so it crests at h=4 where the trends cross. This is also why
nothing in this project claims that a closer plane always reduces
crosstalk: at fixed impedance, the far end can rise, crest, and fall
again depending on which effect wins. The near end is better behaved,
but NEXT and FEXT answer different questions and are reported
separately throughout.

## Separating the effects at constant impedance

The 64.3 % number mixes three changes, so I ran a second study that
isolates them. Each geometry was retuned in width to the baseline's
own impedance, 60.1 ohm (achieved 60.1, 60.6, 58.9, 59.1 ohm - the
residual is FDM grid staircasing, bounded by a sensitivity check and
reported exactly rather than hidden):

| Case | W | S | h | Zgm | Far peak | Near peak | Far reduction |
|---|---|---|---|---|---|---|---|
| Baseline | 4.00 mil | 4 mil | 3 mil | 60.1 ohm | 33.46 mV | 30.49 mV | - |
| Spacing only | 4.09 mil | 8 mil | 3 mil | 60.6 ohm | 17.69 mV | 11.99 mV | 47.1 % |
| Plane only | 2.89 mil | 4 mil | 2 mil | 58.9 ohm | 27.45 mV | 20.46 mV | 17.9 % |
| Combined | 2.89 mil | 8 mil | 2 mil | 59.1 ohm | 12.15 mV | 7.08 mV | 63.7 % |

Spacing does most of the work at 47.1 %. The closer plane alone is
worth 17.9 %. Together they reach 63.7 %, near the original 64.3 % -
reassuring, since the original 3 mil width sits almost on top of the
tuned 2.89 mil. Note the arithmetic coincidence (47.1 + 17.9 = 65.0
against 63.7 actual) for what it is: coincidence, not a rule. Always
simulate the combination.

## The improved layout (original combined geometry)

Three changes, each one backed by a sweep and nothing else:

* spacing 4 mil to 8 mil (the spacing sweep's steep region),
* plane distance 3 mil to 2 mil (the fixed-width sweep's direction,
  confirmed at constant impedance in the stackup study),
* width 4 mil to 3 mil, retuned so the impedance lands at 56.5 ohms
  against the baseline's 60.1 - two routable 50-ohm-class geometries.

Coupled length stays at 3 inches so the comparison is apples to
apples. No guard trace, no via fence: the model cannot simulate them,
so they stay out of the quantitative claim.

Once spacing, reference-plane geometry, and routing constraints are
defined, the same signal-integrity considerations should be carried
into the physical [PCB layout]([JLCPCB PCB LAYOUT SERVICE URL] -
replace with the exact JLCPCB service URL provided by the client).

## Baseline versus improved: 64.3 % lower

Re-running the exact same analysis on the improved geometry gave a
peak of **11.95 mV** against the baseline's **33.46 mV**. Changing the
baseline geometry from W=4 mil, S=4 mil, h=3 mil to the combined
optimized geometry W=3 mil, S=8 mil, h=2 mil reduced the simulated
peak far-end victim voltage from 33.46 mV to 11.95 mV, a
(33.46 - 11.95) / 33.46 x 100 % = 64.3 % reduction under this model
and stimulus. That sentence is carefully worded: three parameters
changed at once, so 64.3 % belongs to the combined optimization, not
to spacing alone, and not to every PCB. The modal split tells
the story: Ze-Zo collapses from 12.0 to 2.2 ohms and the delay skew
from 7.8 to 3.3 ps/in. Spacing weakened the mutual terms while the
closer plane tightened self-terms, and the victim - which only ever
sees the difference - went quiet.

## Reading the two ends: NEXT versus FEXT

Extending the modal solver
to the source-side voltage (loaded input impedance per mode,
reflections included) gave a positive 30.49 mV plateau starting at the
source launch - the classic NEXT shape, duration matching the
there-and-back delay (0.91 ns from the simulated waveform against
0.88 ns computed at 3 inches),
saturating with length (28.37, 30.49, 31.73 mV at 1, 3, 5 inches)
while the far end keeps accumulating. Zero length gives exactly zero;
extreme spacing leaves a 0.94 mV residue that scales with length, i.e.
real weak coupling, not numerical noise. NEXT earned its place in the
figures by passing every check I could devise.

## Limitations

Every millivolt in this article is a model-dependent simulated value,
not a prediction of what a measurement on a fabricated board would
show. The production grid carries roughly 7 % discretization bias and
the finite domain suppresses absolute peaks on the order of 15 %; both
numbers are in `docs/methodology.md` alongside the larger-domain
check that leaves the design trends - and the 63.7 % controlled
headline - substantially stable. The model is quasi-TEM, lossless,
single-ended microstrip, without vias, connectors, package coupling,
mask, or weave. NEXT was implemented and validated, not assumed. None
of these results transfer to another stackup, edge rate, or length
without re-running the scripts.

## What I would do on a real board

Spend spacing first where aggressor-victim gaps are tightest. Route
critical pairs over a close, continuous plane and retune widths to
hold impedance. Break parallel runs when routing allows, but verify
rather than assume the benefit. And treat every rule of thumb as a
starting guess: these millivolts belong to one stackup, one edge
rate, one length. The repository exists so you can substitute your
own and see where your curve bends.

## Reproduce it

```bash
pip install -r requirements.txt
python src/simulate_crosstalk.py      # v1 baseline + combined
python src/sweep_spacing.py           # spacing sweep
python src/sweep_geometry.py          # length + fixed-width stackup
python src/controlled_comparison.py   # constant-Z A/B
python src/sweep_stackup_constZ.py    # constant-Z stackup
python src/validate_model.py          # convergence + benchmarks
python src/robust_check.py            # sensitivity / skew / domain checks
python src/plot_results.py            # v1 figures from the CSVs
python src/plot_controlled.py         # controlled-study figures
python src/verify_numbers.py          # JSON/CSV/prose agreement gate
```

Every plot in this article was generated from the CSVs in `data/` - no
hand-drawn curves. All results are simulated; nothing here is measured
hardware data. Reproducibility (a clean rebuild regenerates every CSV
and figure, checked by `verify_numbers.py`) is kept separate from
physical validation (grid/domain convergence, the Hammerstad-Jansen
benchmark, and the asymptotic checks in `docs/methodology.md`): the
first proves the code runs, the second argues the model means
something.

---

*Analysis project prepared for JLCPCB - all data simulated as labelled.*

<img src="assets/jlcpcb-logo.png" alt="JLCPCB" width="140">
