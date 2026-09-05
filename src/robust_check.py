#!/usr/bin/env python3
"""Post-hoc robustness analyses (SIMULATED, diagnostic - not publication data).

1. Width sensitivity: for each tuned case, W +/- one staircase snap
   (0.125 mil) -> change in Zgm and far peak. Bounds the impact of the
   residual Z mismatch from grid staircasing.
2. Modal delay skew per constant-Z stackup row and controlled case,
   to explain the non-monotonic far-end trend with h.
3. Domain robustness: the 4 controlled cases re-simulated on the
   enlarged (45, 30) mil domain -> do the % reductions hold?

Output: data/robustness.json
Usage: python src/robust_check.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crosstalk_model import Geometry, modal_parameters, peaks_mV  # noqa: E402
from crosstalk_model import simulate_with_near_end  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

CASES = {
    "Spacing-only": (4.09375, 8.0, 3.0),
    "Plane-only": (2.890625, 4.0, 2.0),
    "Combined": (2.890625, 8.0, 2.0),
}
STACKUP_W = {2.0: 2.890625, 3.0: 4.09375, 4.0: 5.46875, 5.0: 6.5,
             6.0: 7.53125}


def far_peak(geom, **kw):
    t, vs, Vf, Vn, _, _, mp = simulate_with_near_end(geom, **kw)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    return peaks_mV(Vf[mask])["peak_abs_mV"], mp


def skew_ps_per_in(mp):
    return ((mp["delay_even_s_per_m"] - mp["delay_odd_s_per_m"])
            * 0.0254 * 1e12)


out = {"width_sensitivity": {}, "skew": {}, "domain_robustness": {}}

for name, (w, s, h) in CASES.items():
    base_geom = Geometry(name, w, s, h)
    p0, mp0 = far_peak(base_geom)
    row = {"W_used": w, "Z_used": mp0["Z_geometric_mean_ohm"],
           "far_used": p0, "shifts": []}
    for dw in (-0.125, 0.125):
        g = Geometry(name, w + dw, s, h)
        p, mp = far_peak(g)
        row["shifts"].append({
            "dW_mil": dw,
            "dZ_ohm": mp["Z_geometric_mean_ohm"]
            - mp0["Z_geometric_mean_ohm"],
            "dpeak_pct": (p - p0) / p0 * 100.0})
        print(f"{name} dW={dw:+}: dZ={row['shifts'][-1]['dZ_ohm']:+.2f} "
              f"dpeak={row['shifts'][-1]['dpeak_pct']:+.2f}%")
    out["width_sensitivity"][name] = row

for h, w in STACKUP_W.items():
    mp = modal_parameters(Geometry(f"h{h}", w, 4.0, h))
    out["skew"][f"h={h}"] = {
        "W_mil": w, "skew_ps_per_in": skew_ps_per_in(mp),
        "Ze_minus_Zo_ohm": mp["Z_even_ohm"] - mp["Z_odd_ohm"]}
    print(f"h={h}: skew={out['skew'][f'h={h}']['skew_ps_per_in']:.2f} "
          f"ps/in  dZ={out['skew'][f'h={h}']['Ze_minus_Zo_ohm']:.2f} ohm")

base_big, _ = far_peak(Geometry("Baseline", 4.0, 4.0, 3.0),
                       domain_half_width_mil=45.0, domain_top_mil=30.0)
for name, (w, s, h) in [("Baseline", (4.0, 4.0, 3.0))] + [
        (k, v) for k, v in CASES.items()]:
    p, mp = far_peak(Geometry(name, w, s, h),
                     domain_half_width_mil=45.0, domain_top_mil=30.0)
    red = (base_big - p) / base_big * 100.0
    out["domain_robustness"][name] = {
        "far_mV_large_domain": p, "reduction_pct_large_domain": red}
    print(f"large-domain {name}: far={p:.2f} mV red={red:.1f}%")

with open(os.path.join(DATA, "robustness.json"), "w") as f:
    json.dump(out, f, indent=2)
print("wrote robustness.json")
