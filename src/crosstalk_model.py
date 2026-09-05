#!/usr/bin/env python3
"""Quasi-TEM coupled-microstrip crosstalk core (SIMULATED data only).

Method
------
1. Solve div(epsilon grad(phi)) = 0 on a 2-D microstrip cross-section
   with finite differences to obtain the Maxwell capacitance matrix C'.
2. Repeat with epsilon_r = 1 to obtain C0'.
3. Compute the external-inductance matrix L' = mu0*epsilon0*inv(C0').
   (See docs/methodology.md for the derivation and references.)
4. Transform the symmetric two-line system into even/odd modes.
5. Propagate a finite-rise-time Thevenin source through each lossless
   mode and reconstruct victim voltages:
     far end (FEXT-type): 0.5 * (Ve_far - Vo_far) via modal ABCD,
     near end (NEXT-type): 0.5 * (Ve_near - Vo_near) via modal input
       impedance Zin = (A*RL + B) / (C*RL + D), Vin = Vs*Zin/(Rs+Zin).
   The modal impedance and delay mismatch creates the victim response.

Limits: lossless, zero-thickness copper, no solder mask, no vias,
connectors, package coupling, or receiver nonlinearity. Single-ended
microstrip, uniform coupled lines only. All dimensions and assumptions
are written to the accompanying CSV/JSON outputs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.constants import epsilon_0, mu_0
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

MIL = 25.4e-6


@dataclass(frozen=True)
class Geometry:
    name: str
    width_mil: float       # trace width W (conductor plane)
    gap_mil: float         # edge-to-edge spacing S
    height_mil: float      # dielectric height h (trace to reference plane)
    er: float = 4.0
    coupled_length_in: float = 3.0


BASELINE = Geometry("Baseline", width_mil=4.0, gap_mil=4.0, height_mil=3.0)
IMPROVED = Geometry("Revised", width_mil=3.0, gap_mil=8.0, height_mil=2.0)

# Electrical assumptions (shared by every run for a fair comparison)
V_SWING = 1.2             # V, Thevenin source step
TR_10_90 = 250e-12        # s, source 10-90 % rise time
RS = 40.0                 # ohm per conductor (source)
RL = 50.0                 # ohm per conductor (load)

# Default FDM discretisation / domain (overridable for convergence tests)
DX_MIL = 0.25             # finite-difference cell size
DOMAIN_HALW_MIL = 30.0    # air/dielectric half-width each side of origin
DOMAIN_TOP_MIL = 20.0     # domain height above the reference plane


def _cross_section(geom: Geometry, er_override: float | None = None,
                   dx_mil: float = DX_MIL,
                   domain_half_width_mil: float = DOMAIN_HALW_MIL,
                   domain_top_mil: float = DOMAIN_TOP_MIL):
    """Return x/y grids, relative permittivity map, and conductor masks."""
    dx = dx_mil * MIL
    x = np.arange(-domain_half_width_mil * MIL,
                  domain_half_width_mil * MIL + dx / 2, dx)
    y = np.arange(0, domain_top_mil * MIL + dx / 2, dx)
    X, Y = np.meshgrid(x, y)
    er_sub = geom.er if er_override is None else er_override
    er = np.where(Y <= geom.height_mil * MIL, er_sub, 1.0)

    # Two zero-thickness microstrip conductors centered symmetrically at y=h.
    center_sep = (geom.width_mil + geom.gap_mil) * MIL
    centers = (-center_sep / 2, center_sep / 2)
    iy = int(round(geom.height_mil / dx_mil))
    masks = []
    for xc in centers:
        mask = np.zeros_like(er, dtype=bool)
        mask[iy, np.abs(x - xc) <= geom.width_mil * MIL / 2 + dx * 0.01] = True
        masks.append(mask)
    return x, y, er, masks


def capacitance_matrix(geom: Geometry, er_override: float | None = None,
                       dx_mil: float = DX_MIL,
                       domain_half_width_mil: float = DOMAIN_HALW_MIL,
                       domain_top_mil: float = DOMAIN_TOP_MIL):
    """Solve the 2-D electrostatic problem and return C' [F/m]."""
    x, y, er, cond = _cross_section(geom, er_override, dx_mil,
                                    domain_half_width_mil, domain_top_mil)
    ny, nx = er.shape
    fixed = np.zeros((ny, nx), dtype=bool)
    fixed[0, :] = True       # solid reference plane
    fixed[-1, :] = True      # distant grounded truncation boundary
    fixed[:, 0] = True
    fixed[:, -1] = True
    fixed |= cond[0] | cond[1]

    unknown_coords = np.argwhere(~fixed)
    uid = -np.ones((ny, nx), dtype=int)
    for k, (j, i) in enumerate(unknown_coords):
        uid[j, i] = k

    # Arithmetic face averaging is consistent with the finite-volume flux form.
    def face_eps(j1, i1, j2, i2):
        return epsilon_0 * 0.5 * (er[j1, i1] + er[j2, i2])

    A = lil_matrix((len(unknown_coords), len(unknown_coords)), dtype=float)
    neighbor_cache = []
    for row, (j, i) in enumerate(unknown_coords):
        entries = []
        diag = 0.0
        for jj, ii in ((j - 1, i), (j + 1, i), (j, i - 1), (j, i + 1)):
            ef = face_eps(j, i, jj, ii)
            diag += ef
            if not fixed[jj, ii]:
                A[row, uid[jj, ii]] = -ef
            entries.append((jj, ii, ef))
        A[row, row] = diag
        neighbor_cache.append(entries)
    A = A.tocsr()

    C = np.zeros((2, 2), dtype=float)
    for excitation in range(2):
        fixed_v = np.zeros((ny, nx), dtype=float)
        fixed_v[cond[excitation]] = 1.0
        b = np.zeros(len(unknown_coords))
        for row, entries in enumerate(neighbor_cache):
            for jj, ii, ef in entries:
                if fixed[jj, ii]:
                    b[row] += ef * fixed_v[jj, ii]
        v_unknown = spsolve(A, b)
        V = fixed_v.copy()
        V[~fixed] = v_unknown

        # Charge per unit length on each conductor from outward electric flux.
        for k, cmask in enumerate(cond):
            q = 0.0
            vc = 1.0 if k == excitation else 0.0
            for j, i in np.argwhere(cmask):
                for jj, ii in ((j - 1, i), (j + 1, i), (j, i - 1), (j, i + 1)):
                    if cmask[jj, ii]:
                        continue
                    ef = face_eps(j, i, jj, ii)
                    q += ef * (vc - V[jj, ii])
            C[k, excitation] = q

    return 0.5 * (C + C.T)


def modal_parameters(geom: Geometry, dx_mil: float = DX_MIL,
                     domain_half_width_mil: float = DOMAIN_HALW_MIL,
                     domain_top_mil: float = DOMAIN_TOP_MIL):
    C = capacitance_matrix(geom, None, dx_mil,
                           domain_half_width_mil, domain_top_mil)
    C0 = capacitance_matrix(geom, 1.0, dx_mil,
                            domain_half_width_mil, domain_top_mil)
    L = mu_0 * epsilon_0 * np.linalg.inv(C0)

    # Symmetrize the numerically extracted matrices before modal reduction.
    C = 0.5 * (C + C.T)
    L = 0.5 * (L + L.T)
    Cs, Cx = C[0, 0], C[0, 1]  # Cx is negative in Maxwell form
    Ls, Lm = L[0, 0], L[0, 1]
    Ce, Co = Cs + Cx, Cs - Cx
    Le, Lo = Ls + Lm, Ls - Lm
    Ze, Zo = np.sqrt(Le / Ce), np.sqrt(Lo / Co)
    tau_e, tau_o = np.sqrt(Le * Ce), np.sqrt(Lo * Co)  # s/m
    return {
        "C_F_per_m": C,
        "L_H_per_m": L,
        "Z_even_ohm": float(Ze),
        "Z_odd_ohm": float(Zo),
        "delay_even_s_per_m": float(tau_e),
        "delay_odd_s_per_m": float(tau_o),
        "Z_geometric_mean_ohm": float(np.sqrt(Ze * Zo)),
    }


def _abcd(freq, Zm, delay_per_m, length_m):
    theta = 2 * np.pi * freq * delay_per_m * length_m
    A = np.cos(theta)
    B = 1j * Zm * np.sin(theta)
    C = 1j * np.sin(theta) / Zm
    D = A
    return A, B, C, D


def modal_transfer(freq, Zm, delay_per_m, length_m):
    """Far-end (load) voltage per mode for a Thevenin source Vs (RMS phasor
    ratio Vload/Vs). Unchanged legacy path - used for FEXT."""
    A, B, C, D = _abcd(freq, Zm, delay_per_m, length_m)
    return 1.0 / (A + RS * C + (B + RS * D) / RL)


def modal_near_end(freq, Zm, delay_per_m, length_m):
    """Near-end (source-side) voltage per mode for a Thevenin source Vs.

    Zin = (A*RL + B)/(C*RL + D) is the loaded input impedance of the
    finite line, so Vin = Vs * Zin/(Rs + Zin). Includes the actual
    far-end termination and finite length (reflections included).
    """
    A, B, C, D = _abcd(freq, Zm, delay_per_m, length_m)
    Zin = (A * RL + B) / (C * RL + D)
    return Zin / (RS + Zin)


def source_waveform(t):
    """Finite trapezoidal pulse; returning to zero prevents FFT wraparound."""
    full_ramp = TR_10_90 / 0.8
    t0 = 1.0e-9
    t1 = 10.0e-9
    rise = np.clip((t - t0) / full_ramp, 0.0, 1.0)
    fall = np.clip((t1 + full_ramp - t) / full_ramp, 0.0, 1.0)
    return V_SWING * np.minimum(rise, fall)


def _propagate(vs, H):
    return np.fft.irfft(np.fft.rfft(vs) * H, n=len(vs))


def simulate(geom: Geometry, n=32768, dt=1e-12, dx_mil: float = DX_MIL,
             domain_half_width_mil: float = DOMAIN_HALW_MIL,
             domain_top_mil: float = DOMAIN_TOP_MIL):
    """Return (t, v_source, v_victim_far, v_aggressor_far, modal_params).

    Legacy far-end-only path; bit-identical to v1 outputs at defaults.
    """
    mp = modal_parameters(geom, dx_mil,
                          domain_half_width_mil, domain_top_mil)
    t = np.arange(n) * dt
    vs = source_waveform(t)
    freq = np.fft.rfftfreq(n, dt)
    length_m = geom.coupled_length_in * 0.0254
    Ve = modal_transfer(freq, mp["Z_even_ohm"], mp["delay_even_s_per_m"],
                        length_m)
    Vo = modal_transfer(freq, mp["Z_odd_ohm"], mp["delay_odd_s_per_m"],
                        length_m)
    Vf = _propagate(vs, 0.5 * (Ve - Vo))
    Va = _propagate(vs, 0.5 * (Ve + Vo))
    return t, vs, Vf, Va, mp


def simulate_with_near_end(geom: Geometry, n=32768, dt=1e-12,
                           dx_mil: float = DX_MIL,
                           domain_half_width_mil: float = DOMAIN_HALW_MIL,
                           domain_top_mil: float = DOMAIN_TOP_MIL):
    """Return (t, vs, v_victim_far, v_victim_near, v_agg_far, v_agg_near, mp)."""
    mp = modal_parameters(geom, dx_mil,
                          domain_half_width_mil, domain_top_mil)
    t = np.arange(n) * dt
    vs = source_waveform(t)
    freq = np.fft.rfftfreq(n, dt)
    length_m = geom.coupled_length_in * 0.0254
    Ve_f = modal_transfer(freq, mp["Z_even_ohm"], mp["delay_even_s_per_m"],
                          length_m)
    Vo_f = modal_transfer(freq, mp["Z_odd_ohm"], mp["delay_odd_s_per_m"],
                          length_m)
    Ve_n = modal_near_end(freq, mp["Z_even_ohm"], mp["delay_even_s_per_m"],
                          length_m)
    Vo_n = modal_near_end(freq, mp["Z_odd_ohm"], mp["delay_odd_s_per_m"],
                          length_m)
    Vf = _propagate(vs, 0.5 * (Ve_f - Vo_f))
    Vn = _propagate(vs, 0.5 * (Ve_n - Vo_n))
    Va_f = _propagate(vs, 0.5 * (Ve_f + Vo_f))
    Va_n = _propagate(vs, 0.5 * (Ve_n + Vo_n))
    return t, vs, Vf, Vn, Va_f, Va_n, mp


def peaks_mV(victim_window):
    return {
        "peak_pos_mV": float(np.max(victim_window) * 1e3),
        "peak_neg_mV": float(np.min(victim_window) * 1e3),
        "peak_abs_mV": float(np.max(np.abs(victim_window)) * 1e3),
    }
