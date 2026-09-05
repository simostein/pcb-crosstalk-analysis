#!/usr/bin/env python3
"""Controlled constant-impedance baseline-vs-improved comparison.

Target Zgm = baseline geometric-mean impedance (computed live), so the
original baseline stays the reference. Four cases isolate spacing and
plane-height effects at comparable impedance:

  Baseline      W=4 fixed, S=4, h=3   (original v1 geometry, untouched)
  Spacing-only  S=8, h=3, W tuned
  Plane-only    S=4, h=2, W tuned
  Combined      S=8, h=2, W tuned     (constant-Z counterpart of v1 improved)

Outputs (SIMULATED):
  data/controlled_comparison.csv
  data/controlled_comparison.json  (target, tolerance, achieved Z per case)

Usage: python src/controlled_comparison.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crosstalk_model import (BASELINE, Geometry, peaks_mV,  # noqa: E402
                             simulate_with_near_end)
from tune_width import tune_width  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

TOL = 0.5  # ohm, preferred tighter tolerance


def run_case(geom):
    t, vs, Vf, Vn, Va_f, Va_n, mp = simulate_with_near_end(geom)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    return peaks_mV(Vf[mask]), peaks_mV(Vn[mask]), mp


def main():
    _, _, _, _, _, _, mp0 = simulate_with_near_end(BASELINE)
    target = mp0["Z_geometric_mean_ohm"]
    print(f"constant-Z target (baseline Zgm): {target:.4f} ohm")

    cases = [("Baseline", 4.0, 4.0, 3.0)]
    for name, gap, h in (("Spacing-only", 8.0, 3.0),
                         ("Plane-only", 4.0, 2.0),
                         ("Combined", 8.0, 2.0)):
        w, z = tune_width(gap, h, target, tol=TOL)
        print(f"tuned {name}: W={w:.4f} mil -> Zgm={z:.4f} ohm "
              f"(err {z - target:+.3f})")
        cases.append((name, w, gap, h))

    rows = []
    for name, w, gap, h in cases:
        geom = Geometry(name=name, width_mil=w, gap_mil=gap,
                        height_mil=h)
        pk_far, pk_near, mp = run_case(geom)
        rows.append({
            "case": name, "W_mil": w, "S_mil": gap, "h_mil": h,
            "Z_even_ohm": mp["Z_even_ohm"],
            "Z_odd_ohm": mp["Z_odd_ohm"],
            "Zgm_ohm": mp["Z_geometric_mean_ohm"],
            "far_pos_mV": pk_far["peak_pos_mV"],
            "far_neg_mV": pk_far["peak_neg_mV"],
            "far_abs_mV": pk_far["peak_abs_mV"],
            "near_pos_mV": pk_near["peak_pos_mV"],
            "near_neg_mV": pk_near["peak_neg_mV"],
            "near_abs_mV": pk_near["peak_abs_mV"],
        })
        print(f"{name}: W={w:.3f} Zgm={mp['Z_geometric_mean_ohm']:.3f} "
              f"far={pk_far['peak_abs_mV']:.3f} mV "
              f"near={pk_near['peak_abs_mV']:.3f} mV")

    base = rows[0]["far_abs_mV"]
    for r in rows:
        r["far_reduction_vs_baseline_pct"] = (base - r["far_abs_mV"]) / base * 100.0

    with open(os.path.join(DATA, "controlled_comparison.csv"), "w",
              newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with open(os.path.join(DATA, "controlled_comparison.json"), "w") as f:
        json.dump({"target_Zgm_ohm": target, "tolerance_ohm": TOL,
                   "note": "Simulated. Constant-Z design-optimization study; "
                           "distinct from the v1 combined geometry "
                           "(W=3,S=8,h=2, 64.3% headline).",
                   "cases": rows}, f, indent=2)
    print("wrote controlled_comparison.csv/json")


if __name__ == "__main__":
    main()
