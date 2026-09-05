#!/usr/bin/env python3
"""Bisect trace width W so geometric-mean impedance hits a target.

Zgm falls monotonically as W grows (fixed S, h), so bisection is safe.
Each evaluation = 2 FDM solves (C + C0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crosstalk_model import Geometry, modal_parameters  # noqa: E402


def zgm_for_width(w_mil, gap_mil, height_mil, er=4.0, **kw):
    geom = Geometry(name="tune", width_mil=w_mil, gap_mil=gap_mil,
                    height_mil=height_mil, er=er)
    return modal_parameters(geom, **kw)["Z_geometric_mean_ohm"]


def tune_width(gap_mil, height_mil, target_zgm, tol=0.5, er=4.0,
               lo=1.0, hi=12.0, max_iter=25, **kw):
    """Return (W_mil, achieved_Zgm). Raises if the bracket is invalid."""
    z_lo = zgm_for_width(lo, gap_mil, height_mil, er, **kw)
    z_hi = zgm_for_width(hi, gap_mil, height_mil, er, **kw)
    if not (z_lo >= target_zgm >= z_hi):
        raise ValueError(
            f"target {target_zgm} ohm outside bracket [{z_hi}, {z_lo}] ohm")
    best_w, best_z, best_err = None, None, float("inf")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        z = zgm_for_width(mid, gap_mil, height_mil, er, **kw)
        err = abs(z - target_zgm)
        if err < best_err:
            best_w, best_z, best_err = mid, z, err
        if z > target_zgm:
            lo = mid
        else:
            hi = mid
        if best_err <= tol and (hi - lo) < 0.01:
            break
    # Local refine: conductor edges snap to FDM cells, so Z(W) is
    # stepwise and bisection can straddle the target band. Scan the
    # snapped neighbourhood and keep the true best.
    w = best_w - 0.2
    while w <= best_w + 0.2 + 1e-12:
        z = zgm_for_width(w, gap_mil, height_mil, er, **kw)
        err = abs(z - target_zgm)
        if err < best_err:
            best_w, best_z, best_err = w, z, err
        w += 0.025
    return best_w, best_z
