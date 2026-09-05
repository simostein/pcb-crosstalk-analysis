#!/usr/bin/env python3
"""Coupled-length and reference-plane-distance studies (SIMULATED data).

Outputs:
  data/length_sweep.csv   (baseline cross-section, length varied)
  data/stackup_sweep.csv  (width/spacing fixed, dielectric height varied;
                           trace width is NOT retuned here, so Z0 shifts and
                           is reported alongside - see methodology note)

Usage:
  python src/sweep_geometry.py
"""
import csv
import os
import sys
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crosstalk_model import BASELINE, modal_parameters, peaks_mV, simulate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

LENGTHS_IN = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
HEIGHTS_MIL = [2.0, 3.0, 4.0, 5.0, 6.0]


def window(t):
    return (t >= 0.5e-9) & (t <= 4.0e-9)


def main():
    # --- Length sweep: cross-section (and modal params) computed once ---
    mp0 = modal_parameters(BASELINE)
    lrows = []
    for L in LENGTHS_IN:
        geom = replace(BASELINE, name=f"L={L}in", coupled_length_in=L)
        t, vs, victim, aggressor, mp = simulate(geom)
        pk = peaks_mV(victim[window(t)])
        lrows.append({"length_in": L, **pk})
        print(f"L={L} in  peak_abs={pk['peak_abs_mV']:.3f} mV")

    path = os.path.join(DATA, "length_sweep.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(lrows[0].keys()))
        writer.writeheader()
        writer.writerows(lrows)
    print(f"wrote {path}")

    # --- Stackup sweep: fixed W/S, varying h (Z0 reported, not retuned) ---
    srows = []
    for h in HEIGHTS_MIL:
        geom = replace(BASELINE, name=f"h={h}mil", height_mil=h)
        t, vs, victim, aggressor, mp = simulate(geom)
        pk = peaks_mV(victim[window(t)])
        srows.append({
            "height_mil": h,
            "width_mil": geom.width_mil,
            "gap_mil": geom.gap_mil,
            **pk,
            "Z_even_ohm": mp["Z_even_ohm"],
            "Z_odd_ohm": mp["Z_odd_ohm"],
            "Z_geometric_mean_ohm": mp["Z_geometric_mean_ohm"],
        })
        print(f"h={h} mil  peak_abs={pk['peak_abs_mV']:.3f} mV  "
              f"Zgm={mp['Z_geometric_mean_ohm']:.2f} ohm")

    path = os.path.join(DATA, "stackup_sweep.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(srows[0].keys()))
        writer.writeheader()
        writer.writerows(srows)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
