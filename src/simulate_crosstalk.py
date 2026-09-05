#!/usr/bin/env python3
"""Run the baseline and improved geometries with the identical stimulus.

Outputs (SIMULATED data):
  data/baseline_results.csv   time_ns, victim_mV, aggressor_mV, source_V
  data/improved_results.csv   (same columns)
  data/simulation_summary.json  parameters + peak metrics + modal data

Usage:
  python src/simulate_crosstalk.py
"""
import csv
import json
import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from crosstalk_model import BASELINE, IMPROVED, peaks_mV, simulate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)


def run_and_save(geom, csv_path):
    t, vs, victim, aggressor, mp = simulate(geom)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_ns", "victim_mV", "aggressor_mV", "source_V"])
        for row in zip(t[mask] * 1e9, victim[mask] * 1e3,
                       aggressor[mask] * 1e3, vs[mask]):
            writer.writerow([f"{v:.9g}" for v in row])
    return t, vs, victim, aggressor, mp, mask


def main():
    summary = {"model": "Simulated - quasi-TEM FDM + lossless MTL modal "
                        "propagation (far-end victim voltage only)",
               "geometries": {}}
    out = {}
    for geom, fname in ((BASELINE, "baseline_results.csv"),
                        (IMPROVED, "improved_results.csv")):
        t, vs, victim, aggressor, mp, mask = run_and_save(
            geom, os.path.join(DATA, fname))
        pk = peaks_mV(victim[mask])
        out[geom.name] = (t, victim, aggressor, mp, pk)
        summary["geometries"][geom.name] = {
            **asdict(geom), **pk,
            "Z_even_ohm": mp["Z_even_ohm"],
            "Z_odd_ohm": mp["Z_odd_ohm"],
            "Z_geometric_mean_ohm": mp["Z_geometric_mean_ohm"],
            "delay_even_ps_per_in": mp["delay_even_s_per_m"] * 0.0254 * 1e12,
            "delay_odd_ps_per_in": mp["delay_odd_s_per_m"] * 0.0254 * 1e12,
            "C_matrix_pF_per_m": (mp["C_F_per_m"] * 1e12).tolist(),
            "L_matrix_nH_per_m": (mp["L_H_per_m"] * 1e9).tolist(),
        }

    b = summary["geometries"]["Baseline"]["peak_abs_mV"]
    r = summary["geometries"]["Revised"]["peak_abs_mV"]
    summary["comparison"] = {
        "baseline_peak_abs_mV": b,
        "improved_peak_abs_mV": r,
        "reduction_percent": (b - r) / b * 100.0,
    }
    with open(os.path.join(DATA, "simulation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary["comparison"], indent=2))


if __name__ == "__main__":
    main()
