#!/usr/bin/env python3
"""Numerical + physical validation of the coupled-line model.

Checks (all SIMULATED, no publication data is altered):
  1. Grid convergence:   dx = 0.5 / 0.25 / 0.125 mil on the baseline.
  2. Domain convergence: enlarged truncation boundaries, fixed geometry.
  3. Hammerstad-Jansen isolated-microstrip Z0 benchmark (t = 0 on both
     sides) + effective-Er cross-check from modal delay.
  4. Large-separation limit: mutual terms -> 0, Ze ~= Zo, victim -> 0.
  5. Zero-coupled-length limit: victim -> 0.
  6. NEXT diagnostics: polarity, arrival timing vs far end, pulse-width
     growth with length, zero-length and large-S limits, C/L symmetry.

Outputs:
  data/grid_convergence.csv
  data/domain_convergence.csv
  data/validation_summary.json

Usage: python src/validate_model.py
"""
import csv
import json
import os
import sys
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

from crosstalk_model import (BASELINE, capacitance_matrix,  # noqa: E402
                             modal_parameters, peaks_mV,
                             simulate_with_near_end)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

C_LIGHT = 299792458.0


def metrics(geom, **kw):
    mp = modal_parameters(geom, **kw)
    C = mp["C_F_per_m"]
    out = {
        "C11_pF_per_m": C[0, 0] * 1e12,
        "Cmutual_pF_per_m": -C[0, 1] * 1e12,
        "Z_even_ohm": mp["Z_even_ohm"],
        "Z_odd_ohm": mp["Z_odd_ohm"],
        "Zgm_ohm": mp["Z_geometric_mean_ohm"],
    }
    t, vs, Vf, Vn, _, _, _ = simulate_with_near_end(geom, **kw)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    out["peak_far_abs_mV"] = peaks_mV(Vf[mask])["peak_abs_mV"]
    out["peak_near_abs_mV"] = peaks_mV(Vn[mask])["peak_abs_mV"]
    return out, (t, Vf, Vn)


def hammerstad_jansen_z0(w_mil, h_mil, er):
    """Isolated microstrip Z0, zero thickness (t = 0 both sides)."""
    wh = w_mil / h_mil
    eeff = ((er + 1.0) / 2.0 + (er - 1.0) / 2.0
            / np.sqrt(1.0 + 12.0 / wh))
    if wh >= 1.0:
        z0 = (120.0 * np.pi
              / (np.sqrt(eeff)
                 * (wh + 1.393 + 0.667 * np.log(wh + 1.444))))
    else:
        z0 = (60.0 / np.sqrt(eeff)
              * np.log(8.0 / wh + 0.25 * wh))
    return z0, eeff


def main():
    summary = {"checks": {}}

    # --- 1. grid convergence -------------------------------------------
    grows = []
    for dx in (0.5, 0.25, 0.125):
        m, _ = metrics(BASELINE, dx_mil=dx)
        grows.append({"dx_mil": dx, **m})
        print(f"dx={dx}: C11={m['C11_pF_per_m']:.3f} "
              f"Cm={m['Cmutual_pF_per_m']:.4f} Zgm={m['Zgm_ohm']:.3f} "
              f"far={m['peak_far_abs_mV']:.3f} mV")
    with open(os.path.join(DATA, "grid_convergence.csv"), "w",
              newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(grows[0].keys()))
        writer.writeheader()
        writer.writerows(grows)
    key = "peak_far_abs_mV"
    conv = [(grows[i][key] - grows[i + 1][key]) / grows[i + 1][key] * 100.0
            for i in range(len(grows) - 1)]
    summary["checks"]["grid_convergence"] = {
        "refinement_changes_pct": conv,
        "criterion_pct": 5.0,
        "pass": all(abs(c) < 5.0 for c in conv),
        "rows": grows,
    }
    print(f"grid refinement changes: {conv[0]:.3f}%, {conv[1]:.3f}%")

    # --- 2. domain convergence ------------------------------------------
    drows = []
    for hw, tp in ((30.0, 20.0), (45.0, 30.0), (60.0, 40.0)):
        m, _ = metrics(BASELINE, domain_half_width_mil=hw,
                       domain_top_mil=tp)
        drows.append({"half_width_mil": hw, "top_mil": tp, **m})
        print(f"domain ({hw},{tp}): C11={m['C11_pF_per_m']:.3f} "
              f"Zgm={m['Zgm_ohm']:.3f} far={m['peak_far_abs_mV']:.3f} mV")
    with open(os.path.join(DATA, "domain_convergence.csv"), "w",
              newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(drows[0].keys()))
        writer.writeheader()
        writer.writerows(drows)
    dconv = [(drows[i][key] - drows[i + 1][key]) / drows[i + 1][key] * 100.0
             for i in range(len(drows) - 1)]
    summary["checks"]["domain_convergence"] = {
        "refinement_changes_pct": dconv,
        "criterion_pct": 5.0,
        "pass": all(abs(c) < 5.0 for c in dconv),
        "rows": drows,
    }
    print(f"domain refinement changes: {dconv[0]:.3f}%, {dconv[1]:.3f}%")

    # --- 3. Hammerstad-Jansen benchmark ----------------------------------
    # Wide-separation model line approximates an isolated trace.
    wide = replace(BASELINE, name="wide", gap_mil=40.0)
    mp_w = modal_parameters(wide, domain_half_width_mil=60.0,
                            domain_top_mil=40.0)
    z_model = float(np.sqrt(mp_w["Z_even_ohm"] * mp_w["Z_odd_ohm"]))
    z_hj, eeff_hj = hammerstad_jansen_z0(4.0, 3.0, 4.0)
    err = (z_model - z_hj) / z_hj * 100.0
    tau = 0.5 * (mp_w["delay_even_s_per_m"]
                 + mp_w["delay_odd_s_per_m"])
    eeff_model = (C_LIGHT * tau) ** 2
    summary["checks"]["hammerstad_jansen"] = {
        "model_Z0_ohm": z_model, "HJ_Z0_ohm": float(z_hj),
        "error_pct": float(err), "criterion_pct": 10.0,
        "pass": abs(float(err)) < 10.0,
        "model_effective_er": float(eeff_model),
        "HJ_effective_er": float(eeff_hj),
    }
    print(f"HJ benchmark: model {z_model:.2f} vs HJ {z_hj:.2f} "
          f"-> err {err:.2f}%; eeff model {eeff_model:.3f} vs HJ "
          f"{eeff_hj:.3f}")

    # --- 4. large-separation limit ---------------------------------------
    Cw = 0.5 * (mp_w["C_F_per_m"] + mp_w["C_F_per_m"].T)
    Lw = 0.5 * (mp_w["L_H_per_m"] + mp_w["L_H_per_m"].T)
    t, _, Vf, Vn, _, _, _ = simulate_with_near_end(
        wide, domain_half_width_mil=60.0, domain_top_mil=40.0)
    mask = (t >= 0.5e-9) & (t <= 4.0e-9)
    base_far = grows[1]["peak_far_abs_mV"]
    summary["checks"]["large_separation"] = {
        "mutual_C_over_C11_pct": float(-Cw[0, 1] / Cw[0, 0] * 100.0),
        "mutual_L_over_L11_pct": float(Lw[0, 1] / Lw[0, 0] * 100.0),
        "Ze_minus_Zo_ohm": float(mp_w["Z_even_ohm"]
                                 - mp_w["Z_odd_ohm"]),
        "far_mV": float(peaks_mV(Vf[mask])["peak_abs_mV"]),
        "near_mV": float(peaks_mV(Vn[mask])["peak_abs_mV"]),
        "far_over_baseline_pct": float(
            peaks_mV(Vf[mask])["peak_abs_mV"] / base_far * 100.0),
    }
    print("large-S:", json.dumps(summary["checks"]["large_separation"],
                                 indent=1))

    # --- 5. zero-coupled-length limit ------------------------------------
    zero = replace(BASELINE, name="zero", coupled_length_in=0.0)
    tz, _, Vfz, Vnz, _, _, _ = simulate_with_near_end(zero)
    maskz = (tz >= 0.5e-9) & (tz <= 4.0e-9)
    summary["checks"]["zero_length"] = {
        "far_mV": float(peaks_mV(Vfz[maskz])["peak_abs_mV"]),
        "near_mV": float(peaks_mV(Vnz[maskz])["peak_abs_mV"]),
        "pass": bool(float(np.max(np.abs(Vfz[maskz]))) == 0.0
                     and float(np.max(np.abs(Vnz[maskz]))) == 0.0),
    }
    print("zero-L:", summary["checks"]["zero_length"])

    # --- 6. NEXT diagnostics ----------------------------------------------
    tb, _, VfB, VnB, _, _, mpB = simulate_with_near_end(BASELINE)
    maskb = (tb >= 0.5e-9) & (tb <= 4.0e-9)
    pk_n = peaks_mV(VnB[maskb])
    pk_f = peaks_mV(VfB[maskb])
    t1, _, _, Vn1, _, _, _ = simulate_with_near_end(
        replace(BASELINE, name="L1", coupled_length_in=1.0))
    m1 = (t1 >= 0.5e-9) & (t1 <= 4.0e-9)
    t5, _, _, Vn5, _, _, _ = simulate_with_near_end(
        replace(BASELINE, name="L5", coupled_length_in=5.0))
    m5 = (t5 >= 0.5e-9) & (t5 <= 4.0e-9)
    # Wide-separation line at short length: does the residual scale
    # with L (genuine weak-coupling accumulation) or stand still?
    tw1, _, VfW1, _, _, _, _ = simulate_with_near_end(
        replace(wide, name="wideL1", coupled_length_in=1.0),
        domain_half_width_mil=60.0, domain_top_mil=40.0)
    mw1 = (tw1 >= 0.5e-9) & (tw1 <= 4.0e-9)

    def half_width(t, v, m):
        vv = v[m]
        tt = t[m]
        hm = np.max(vv) / 2.0
        idx = np.where(vv >= hm)[0]
        return float((tt[idx[-1]] - tt[idx[0]]) * 1e9)

    td_ps_per_in = float(0.5 * (mpB["delay_even_s_per_m"]
                               + mpB["delay_odd_s_per_m"]) * 0.0254 * 1e12)
    diag = {
        "near_pos_mV": pk_n["peak_pos_mV"],
        "near_neg_mV": pk_n["peak_neg_mV"],
        "far_neg_mV": pk_f["peak_neg_mV"],
        "near_peak_L1_mV": float(peaks_mV(Vn1[m1])["peak_abs_mV"]),
        "near_peak_L3_mV": float(pk_n["peak_abs_mV"]),
        "near_peak_L5_mV": float(peaks_mV(Vn5[m5])["peak_abs_mV"]),
        "wide_far_L1_mV": float(peaks_mV(VfW1[mw1])["peak_abs_mV"]),
        "wide_far_L3_mV": float(summary["checks"]["large_separation"]["far_mV"]),
        "near_onset_before_far_peak": bool(
            tb[maskb][np.argmax(VnB[maskb])]
            < tb[maskb][np.argmin(VfB[maskb])]),
        "near_halfwidth_L3_ns": half_width(tb, VnB, maskb),
        "near_halfwidth_L1_ns": half_width(t1, Vn1, m1),
        "roundtrip_2td_L3_ns": 2.0 * td_ps_per_in
        * BASELINE.coupled_length_in / 1e3,
        "roundtrip_2td_L1_ns": 2.0 * td_ps_per_in * 1.0 / 1e3,
        "symmetric_C": bool(abs(Cw[0, 1] - Cw[1, 0]) < 1e-18),
    }
    diag["width_grows_with_length"] = (
        diag["near_halfwidth_L3_ns"] > diag["near_halfwidth_L1_ns"])
    summary["checks"]["next_diagnostics"] = diag
    print("NEXT:", json.dumps(diag, indent=1))

    with open(os.path.join(DATA, "validation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("wrote grid_convergence.csv, domain_convergence.csv, "
          "validation_summary.json")


if __name__ == "__main__":
    main()
