#!/usr/bin/env python3
"""Constant-impedance stackup (reference-plane) study.

For each dielectric height h, trace width W is retuned so Zgm matches
the baseline value. Two variables change (h and W), so this is a
constant-impedance study answering: "how does coupling change when the
trace moves relative to its plane while impedance is held?" - NOT a
perfect isolation of h. The v1 fixed-width sweep is kept separately.

Outputs (SIMULATED):
  data/stackup_constant_impedance.csv
  data/stackup_constant_impedance.json

Usage: python src/sweep_stackup_constZ.py
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

HEIGHTS_MIL = [2.0, 3.0, 4.0, 5.0, 6.0]
GAP_MIL = 4.0
TOL = 0.5


def main():
    _, _, _, _, _, _, mp0 = simulate_with_near_end(BASELINE)
    target = mp0["Z_geometric_mean_ohm"]
    print(f"constant-Z target (baseline Zgm): {target:.4f} ohm")

    rows = []
    for h in HEIGHTS_MIL:
        w, z = tune_width(GAP_MIL, h, target, tol=TOL)
        geom = Geometry(name=f"h={h}", width_mil=w, gap_mil=GAP_MIL,
                        height_mil=h)
        t, vs, Vf, Vn, _, _, mp = simulate_with_near_end(geom)
        mask = (t >= 0.5e-9) & (t <= 4.0e-9)
        pk_far, pk_near = peaks_mV(Vf[mask]), peaks_mV(Vn[mask])
        rows.append({
            "h_mil": h, "W_mil": w, "S_mil": GAP_MIL,
            "Z_even_ohm": mp["Z_even_ohm"],
            "Z_odd_ohm": mp["Z_odd_ohm"],
            "Zgm_ohm": mp["Z_geometric_mean_ohm"],
            "far_abs_mV": pk_far["peak_abs_mV"],
            "far_neg_mV": pk_far["peak_neg_mV"],
            "near_abs_mV": pk_near["peak_abs_mV"],
            "near_pos_mV": pk_near["peak_pos_mV"],
        })
        print(f"h={h} mil: W={w:.4f} Zgm={mp['Z_geometric_mean_ohm']:.3f} "
              f"far={pk_far['peak_abs_mV']:.3f} mV "
              f"near={pk_near['peak_abs_mV']:.3f} mV")

    with open(os.path.join(DATA, "stackup_constant_impedance.csv"), "w",
              newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with open(os.path.join(DATA, "stackup_constant_impedance.json"),
              "w") as f:
        json.dump({"target_Zgm_ohm": target, "tolerance_ohm": TOL,
                   "note": "Simulated constant-impedance stackup study.",
                   "rows": rows}, f, indent=2)
    print("wrote stackup_constant_impedance.csv/json")


if __name__ == "__main__":
    main()
