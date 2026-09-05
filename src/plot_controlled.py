#!/usr/bin/env python3
"""Figures for the controlled (constant-Z) studies + NEXT/FEXT.

Reads:  data/controlled_comparison.csv, data/stackup_constant_impedance.csv
        data/baseline_results.csv (+ near-end waveform, regenerated live
        from the model at default settings for the NEXT/FEXT overlay)
Writes: figures/controlled_geometry_comparison.png/.svg
        figures/stackup_constant_impedance.png/.svg
        figures/next_fext_waveforms.png/.svg

Usage: python src/plot_controlled.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from crosstalk_model import BASELINE, simulate_with_near_end  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.linewidth": 0.9,
    "lines.linewidth": 2.0,
})
RED = "#b8473d"
BLUE = "#176b87"
GREY = "#64748b"


def read_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return rows


def save(fig, stem):
    fig.savefig(os.path.join(FIG, stem + ".png"), dpi=240, bbox_inches="tight")
    fig.savefig(os.path.join(FIG, stem + ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png/.svg")


def controlled_comparison():
    rows = read_csv(os.path.join(DATA, "controlled_comparison.csv"))
    labels = [r["case"] for r in rows]
    far = [float(r["far_abs_mV"]) for r in rows]
    near = [float(r["near_abs_mV"]) for r in rows]
    zgm = [float(r["Zgm_ohm"]) for r in rows]
    x = range(len(rows))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    b1 = ax.bar([i - w / 2 for i in x], far, w, color=RED, label="Far-end peak")
    b2 = ax.bar([i + w / 2 for i in x], near, w, color=BLUE, label="Near-end peak")
    for i, (f, n, z) in enumerate(zip(far, near, zgm)):
        ax.text(i - w / 2, f + 0.4, f"{f:.2f}", ha="center", fontsize=8.5)
        if n > 0.5:
            ax.text(i + w / 2, n + 0.4, f"{n:.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{l}\nZ={z:.1f} Ω" for l, z in zip(labels, zgm)])
    ax.set_ylabel("Peak victim voltage (mV)")
    ax.set_title("Controlled constant-impedance comparison (simulated)",
                 weight="bold")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", color="#d9e2e7", lw=0.7)
    fig.tight_layout()
    save(fig, "controlled_geometry_comparison")


def stackup_const_z():
    rows = read_csv(os.path.join(DATA, "stackup_constant_impedance.csv"))
    h = [float(r["h_mil"]) for r in rows]
    far = [float(r["far_abs_mV"]) for r in rows]
    w = [float(r["W_mil"]) for r in rows]
    fig, ax1 = plt.subplots(figsize=(7.6, 4.6))
    ax1.plot(h, far, "o-", color=BLUE, markersize=6,
             label="Peak far-end voltage")
    ax1.set_xlabel("Dielectric height h (mil)")
    ax1.set_ylabel("Peak far-end victim voltage (mV)", color=BLUE)
    ax2 = ax1.twinx()
    ax2.plot(h, w, "s--", color="#c47b2d", markersize=6,
             label="Retuned width W")
    ax2.set_ylabel("Trace width W (mil)", color="#c47b2d")
    ax1.set_title("Constant-impedance stackup study (simulated, Zgm ~ 60 Ω)",
                  weight="bold")
    ax1.grid(True, color="#d9e2e7", lw=0.7)
    fig.tight_layout()
    save(fig, "stackup_constant_impedance")


def next_fext_waveforms():
    t, vs, Vf, Vn, _, _, _ = simulate_with_near_end(BASELINE)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(t[mask] * 1e9, Vf[mask] * 1e3, color=RED, label="Far end (FEXT)")
    ax.plot(t[mask] * 1e9, Vn[mask] * 1e3, color=BLUE, label="Near end (NEXT)")
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Victim voltage (mV)")
    ax.set_title("Simulated NEXT vs FEXT, baseline geometry", weight="bold")
    ax.grid(True, color="#d9e2e7", lw=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, "next_fext_waveforms")


def main():
    controlled_comparison()
    stackup_const_z()
    next_fext_waveforms()


if __name__ == "__main__":
    main()
