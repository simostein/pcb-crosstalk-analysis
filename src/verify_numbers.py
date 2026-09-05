#!/usr/bin/env python3
"""Verify every reported number traces back to generated CSVs/JSONs.

Two layers:
  1. JSON summaries must reproduce their sibling CSVs (tight tolerance).
  2. Headline values in README.md / article.md / docs/methodology.md must
     match the CSV values at the stated rounding (e.g. CSV 33.4597 mV vs
     prose "33.46 mV" passes; a hand-typed contradiction fails).

Usage: python src/verify_numbers.py  (exit 0 = all agree)
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print("MISMATCH:", msg)


def load_csv(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def fnum(x):
    return float(x)


# ---------------------------------------------------------------- layer 1
def check_json_vs_csv():
    # simulation_summary.json vs baseline/improved_results.csv
    s = json.load(open(os.path.join(DATA, "simulation_summary.json")))
    for geom, csv_name in (("Baseline", "baseline_results.csv"),
                           ("Revised", "improved_results.csv")):
        rows = load_csv(csv_name)
        peak = max(abs(fnum(r["victim_mV"])) for r in rows)
        rep = s["geometries"][geom]["peak_abs_mV"]
        if abs(peak - rep) > 1e-6 * max(1.0, abs(rep)):
            fail(f"summary {geom}: json {rep} vs csv {peak}")
    b, r = (s["geometries"]["Baseline"]["peak_abs_mV"],
            s["geometries"]["Revised"]["peak_abs_mV"])
    if abs(s["comparison"]["reduction_percent"] - (b - r) / b * 100) > 1e-9:
        fail("summary reduction_percent miscomputed")

    # controlled_comparison.json vs .csv
    c = json.load(open(os.path.join(DATA, "controlled_comparison.json")))
    rows = {r["case"]: r for r in load_csv("controlled_comparison.csv")}
    if abs(c["target_Zgm_ohm"] - 60.13661041224333) > 1e-6:
        fail("controlled target drifted from baseline Zgm")
    for case in c["cases"]:
        r = rows[case["case"]]
        for k in ("far_abs_mV", "near_abs_mV", "Zgm_ohm", "W_mil"):
            if abs(fnum(r[k]) - case[k]) > 1e-9 * max(1.0, abs(case[k])):
                fail(f"controlled {case['case']}.{k}: json vs csv")
        base = fnum(rows["Baseline"]["far_abs_mV"])
        exp = (base - fnum(r["far_abs_mV"])) / base * 100.0
        if abs(fnum(r["far_reduction_vs_baseline_pct"]) - exp) > 1e-9:
            fail(f"controlled {case['case']}: reduction miscomputed")

    # stackup_constant_impedance.json vs .csv
    z = json.load(open(os.path.join(DATA, "stackup_constant_impedance.json")))
    rows = load_csv("stackup_constant_impedance.csv")
    for jrow, crow in zip(z["rows"], rows):
        for k in ("far_abs_mV", "Zgm_ohm", "W_mil"):
            if abs(fnum(crow[k]) - jrow[k]) > 1e-9 * max(1.0, abs(jrow[k])):
                fail(f"constZ h={crow['h_mil']}.{k}: json vs csv")


# ---------------------------------------------------------------- layer 2
def expect(value, decimals, *files):
    """The correctly rounded value must appear in each listed prose file."""
    text_hits = {}
    for fn in files:
        with open(os.path.join(ROOT, fn)) as f:
            text_hits[fn] = f.read()
    want = f"{value:.{decimals}f}"
    tol = 0.5 * 10 ** (-decimals) + 1e-12
    # numeric tokens in prose, compared by value so rounding/sign
    # formatting cannot cause false failures
    for fn, text in text_hits.items():
        toks = [float(x) for x in re.findall(r"-?\d+\.\d+", text)]
        if not any(abs(t - value) <= tol for t in toks):
            fail(f"{fn}: expected rounded value {want} not found")


def check_prose():
    base = load_csv("baseline_results.csv")
    imp = load_csv("improved_results.csv")
    b = max(abs(fnum(r["victim_mV"])) for r in base)
    r = max(abs(fnum(r["victim_mV"])) for r in imp)
    red = (b - r) / b * 100.0
    for v, d in ((b, 2), (r, 2)):
        expect(v, d, "README.md", "article.md")
    expect(red, 1, "README.md", "article.md")

    sp = load_csv("spacing_sweep.csv")
    for row in sp:  # every sweep point quoted in the README table
        expect(fnum(row["peak_abs_mV"]), 2, "README.md")

    ln = load_csv("length_sweep.csv")
    for row in ln:
        expect(fnum(row["peak_abs_mV"]), 2, "README.md")

    cc = load_csv("controlled_comparison.csv")
    for row in cc:
        if row["case"] == "Baseline":
            continue
        expect(fnum(row["far_abs_mV"]), 2, "README.md", "article.md")
        expect(fnum(row["far_reduction_vs_baseline_pct"]), 1,
               "README.md", "article.md")
        expect(fnum(row["Zgm_ohm"]), 1, "README.md", "article.md")

    cz = load_csv("stackup_constant_impedance.csv")
    for row in cz:
        expect(fnum(row["far_abs_mV"]), 2, "README.md", "article.md")
        expect(fnum(row["W_mil"]), 2, "README.md", "article.md")

    v = json.load(open(os.path.join(DATA, "validation_summary.json")))
    g = v["checks"]["grid_convergence"]["refinement_changes_pct"]
    expect(g[-1], 1, "docs/methodology.md")  # finest-step change (signed)
    d = v["checks"]["domain_convergence"]["refinement_changes_pct"]
    expect(d[-1], 1, "docs/methodology.md")
    expect(v["checks"]["hammerstad_jansen"]["error_pct"], 1,
           "docs/methodology.md")


def main():
    check_json_vs_csv()
    check_prose()
    if FAILURES:
        print(f"\n{len(FAILURES)} numerical agreement failure(s)")
        return 1
    print("verify_numbers: all JSON/CSV/prose values agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
