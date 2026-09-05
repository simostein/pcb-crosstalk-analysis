#!/usr/bin/env python3
"""Trace-spacing sweep at fixed width, height, length, and stimulus.

Output (SIMULATED data): data/spacing_sweep.csv

Usage:
  python src/sweep_spacing.py
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

GAPS_MIL = [4, 5, 6, 8, 10, 12, 16, 20]


def main():
    rows = []
    for gap in GAPS_MIL:
        geom = replace(BASELINE, name=f"S={gap}mil", gap_mil=float(gap))
        t, vs, victim, aggressor, mp = simulate(geom)
        mask = (t >= 0.5e-9) & (t <= 4.0e-9)
        pk = peaks_mV(victim[mask])
        rows.append({
            "gap_mil": gap,
            "s_over_h": gap / geom.height_mil,
            **pk,
            "Z_even_ohm": mp["Z_even_ohm"],
            "Z_odd_ohm": mp["Z_odd_ohm"],
            "Z_geometric_mean_ohm": mp["Z_geometric_mean_ohm"],
        })
        print(f"S={gap} mil  peak_abs={pk['peak_abs_mV']:.3f} mV  "
              f"Zgm={mp['Z_geometric_mean_ohm']:.2f} ohm")

    path = os.path.join(DATA, "spacing_sweep.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
