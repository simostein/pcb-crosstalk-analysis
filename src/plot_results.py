#!/usr/bin/env python3
"""Regenerate every figure from the saved CSVs (no re-simulation).

Usage:
  python src/plot_results.py

Reads:  data/*.csv
Writes: figures/*.png + figures/*.svg
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

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
RED = "#b8473d"     # aggressor / baseline
BLUE = "#176b87"    # victim / improved
GREY = "#64748b"
COPPER = "#c47b2d"
SUBSTRATE = "#dce8dd"


def read_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0].keys()}


def save(fig, stem):
    fig.savefig(os.path.join(FIG, stem + ".png"), dpi=240, bbox_inches="tight")
    fig.savefig(os.path.join(FIG, stem + ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png/.svg")


# ---------------------------------------------------------------- waveforms
def waveform_comparison():
    base = read_csv(os.path.join(DATA, "baseline_results.csv"))
    imp = read_csv(os.path.join(DATA, "improved_results.csv"))
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(base["time_ns"], base["victim_mV"], color=RED, label="Baseline victim")
    ax.plot(imp["time_ns"], imp["victim_mV"], color=BLUE, label="Improved victim")
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Far-end victim voltage (mV)")
    ax.set_title("Simulated victim crosstalk: baseline vs improved", weight="bold")
    ax.grid(True, color="#d9e2e7", lw=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, "victim_waveform_comparison")


def baseline_waveform():
    base = read_csv(os.path.join(DATA, "baseline_results.csv"))
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.plot(base["time_ns"], base["victim_mV"], color=RED, label="Victim (far end)")
    ax.plot(base["time_ns"], base["aggressor_mV"], color=GREY, lw=1.4,
            label="Aggressor (far end, reference)")
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Voltage (mV)")
    ax.set_title("Baseline far-end waveforms (simulated)", weight="bold")
    ax.grid(True, color="#d9e2e7", lw=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, "baseline_victim_waveform")


# ------------------------------------------------------------------- sweeps
def spacing_plot():
    d = read_csv(os.path.join(DATA, "spacing_sweep.csv"))
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(d["gap_mil"], d["peak_abs_mV"], "o-", color=BLUE, markersize=6)
    ax.set_xlabel("Edge-to-edge spacing S (mil)")
    ax.set_ylabel("Peak far-end victim voltage (mV)")
    ax.set_title("Simulated crosstalk vs trace spacing (W = 4 mil, h = 3 mil)",
                 weight="bold")
    ax.grid(True, color="#d9e2e7", lw=0.7)
    fig.tight_layout()
    save(fig, "spacing_vs_crosstalk")


def length_plot():
    d = read_csv(os.path.join(DATA, "length_sweep.csv"))
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(d["length_in"], d["peak_abs_mV"], "s-", color=BLUE, markersize=6)
    ax.set_xlabel("Coupled parallel length (in)")
    ax.set_ylabel("Peak far-end victim voltage (mV)")
    ax.set_title("Simulated crosstalk vs coupled length (baseline cross-section)",
                 weight="bold")
    ax.grid(True, color="#d9e2e7", lw=0.7)
    fig.tight_layout()
    save(fig, "parallel_length_vs_crosstalk")


def stackup_plot():
    d = read_csv(os.path.join(DATA, "stackup_sweep.csv"))
    fig, ax1 = plt.subplots(figsize=(7.6, 4.6))
    ax1.plot(d["height_mil"], d["peak_abs_mV"], "o-", color=BLUE,
             markersize=6, label="Peak victim voltage")
    ax1.set_xlabel("Dielectric height h (mil)")
    ax1.set_ylabel("Peak far-end victim voltage (mV)", color=BLUE)
    ax2 = ax1.twinx()
    ax2.plot(d["height_mil"], d["Z_geometric_mean_ohm"], "x--", color=RED,
             markersize=6, label="Geom.-mean Z")
    ax2.set_ylabel("Geometric-mean impedance (ohm)", color=RED)
    ax1.set_title("Fixed-width stackup sweep (simulated, W = 4 mil held)",
                  weight="bold")
    ax1.grid(True, color="#d9e2e7", lw=0.7)
    fig.tight_layout()
    save(fig, "stackup_vs_crosstalk")


# ------------------------------------------------------- layout illustrations
def _plan_view(ax, W, S, L_in, title, subtitle):
    """Top-view schematic of the coupled pair (dimensions in mil / in)."""
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")
    ax.set_title(title, color="#123b5d", weight="bold", fontsize=12)
    ax.text(50, 41.5, subtitle, ha="center", fontsize=9, color=GREY)
    y_a, y_v = 30, 16
    # scale: 1 mil lateral -> 1.1 units; length runs full width
    ax.add_patch(Rectangle((8, y_a - W * 0.55), 84, W * 1.1,
                           facecolor=RED, edgecolor="#7f2d28"))
    ax.add_patch(Rectangle((8, y_v - W * 0.55), 84, W * 1.1,
                           facecolor=BLUE, edgecolor="#0d4557"))
    ax.text(4, y_a, "A", color=RED, weight="bold", va="center", fontsize=11)
    ax.text(4, y_v, "V", color=BLUE, weight="bold", va="center", fontsize=11)
    # spacing arrow between inner edges
    ax.annotate("", xy=(60, y_a - W * 0.55), xytext=(60, y_v + W * 0.55),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(62, (y_a + y_v) / 2, f"S = {S:g} mil", va="center", fontsize=9)
    # coupled-length arrow below
    ax.annotate("", xy=(8, 6), xytext=(92, 6),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(50, 3.2, f"coupled length = {L_in:g} in", ha="center", fontsize=9)
    # source / load ends
    ax.text(8, y_a + 4.2, "source", ha="left", fontsize=8, color=GREY)
    ax.text(92, y_v - 5.2, "victim load", ha="right", fontsize=8, color=GREY)


def _cross_section(ax, W, S, h, title, subtitle):
    """Cross-section schematic (lateral mil units, vertical exaggerated)."""
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")
    ax.set_title(title, color="#123b5d", weight="bold", fontsize=12)
    ax.text(50, 41.5, subtitle, ha="center", fontsize=9, color=GREY)
    # substrate + reference plane
    ax.add_patch(Rectangle((10, 8), 80, 14, facecolor=SUBSTRATE,
                           edgecolor=GREY, hatch="///"))
    ax.add_patch(Rectangle((10, 5.5), 80, 2.5, facecolor=GREY))
    ax.text(92, 6.7, "GND", ha="left", va="center", fontsize=8, color="black")
    cx = 50
    pitch = W + S
    for xc, col, lab in ((cx - pitch / 2, RED, "A"), (cx + pitch / 2, BLUE, "V")):
        ax.add_patch(Rectangle((xc - W / 2, 22), W, 3.4, facecolor=COPPER,
                               edgecolor="#7a4d1a"))
        ax.text(xc, 28.5, lab, ha="center", fontsize=10, weight="bold", color=col)
    # h arrow
    ax.annotate("", xy=(16, 8), xytext=(16, 22),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(18, 15, f"h = {h:g} mil", va="center", fontsize=9)
    # S arrow
    ax.annotate("", xy=(cx - pitch / 2 + W / 2, 33), xytext=(cx + pitch / 2 - W / 2, 33),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(cx, 35.2, f"S = {S:g} mil", ha="center", fontsize=9)


def layout_figures():
    for stem, W, S, h, tag, sub in (
            ("baseline_layout", 4, 4, 3, "Baseline layout", "W=4 mil, S=4 mil, h=3 mil, L=3 in"),
            ("improved_layout", 3, 8, 2, "Improved layout", "W=3 mil, S=8 mil, h=2 mil, L=3 in")):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.4))
        _plan_view(a1, W, S, 3.0, f"{tag} - plan view", sub)
        _cross_section(a2, W, S, h, f"{tag} - cross-section", sub + ", er=4.0")
        fig.suptitle(f"{tag} (simulated geometry, not to scale)",
                     color="#123b5d", weight="bold")
        fig.tight_layout()
        save(fig, stem)


def cross_section_figure():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.6))
    _cross_section(a1, 4, 4, 3, "Baseline cross-section", "W=4 mil, S=4 mil, h=3 mil")
    _cross_section(a2, 3, 8, 2, "Improved cross-section", "W=3 mil, S=8 mil, h=2 mil")
    fig.suptitle("Reference-plane geometry change (simulated, not to scale)",
                 color="#123b5d", weight="bold")
    fig.tight_layout()
    save(fig, "cross_section_comparison")


def main():
    waveform_comparison()
    baseline_waveform()
    spacing_plot()
    length_plot()
    stackup_plot()
    layout_figures()
    cross_section_figure()


if __name__ == "__main__":
    main()
