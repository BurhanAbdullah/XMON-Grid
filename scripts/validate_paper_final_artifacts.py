#!/usr/bin/env python3
"""Validate manuscript provenance and frozen verification values."""
from pathlib import Path
import csv
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "main.tex"
PKG = ROOT / "results" / "paper_final_verified_20260908"
FIG = PKG / "figures"


def fail(msg):
    raise SystemExit(f"FAIL: {msg}")


def close(a, b, tol=5e-4):
    return abs(a - b) <= tol


def main():
    if not PAPER.exists():
        fail("paper/main.tex is missing")
    if not PKG.exists():
        fail("frozen verification package is missing")

    tex = PAPER.read_text(encoding="utf-8")
    if "../results/independent_validation_run/paper_figures/" in tex:
        fail("main.tex still references historical independent_validation_run figures")
    if "../results/paper_final_verified_20260908/figures/" not in tex:
        fail("main.tex does not point to the frozen final figure directory")

    # Verify manuscript Table I against the frozen five-seed CSV.
    rows = list(csv.DictReader((PKG / "multi_seed_summary.csv").open()))
    metrics = ["Accuracy", "Precision", "Recall", "F1", "FPR", "MCC"]
    for metric in metrics:
        vals = [float(r[metric]) for r in rows]
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals)
        pattern = r"F1-score & ([0-9.]+) & ([0-9.]+)" if metric == "F1" else rf"{re.escape(metric)} & ([0-9.]+) & ([0-9.]+)"
        m = re.search(pattern, tex)
        if not m:
            fail(f"manuscript table entry missing for {metric}")
        if not close(float(m.group(1)), mean) or not close(float(m.group(2)), sd):
            fail(f"{metric} manuscript value disagrees with frozen CSV: mean={mean:.6f}, sd={sd:.6f}")

    # Physical audit values are derived from the frozen CSV itself.
    prow = list(csv.DictReader((PKG / "current_physical_sanity.csv").open()))
    hp = max(float(r["h_p_max_abs_error"]) for r in prow)
    hq = max(float(r["h_q_max_abs_error"]) for r in prow)
    pb = max(abs(float(r["power_balance_residual"])) for r in prow)

    for value, label in [(hp, "hP"), (hq, "hQ"), (pb, "power-balance")]:
        if value <= 0:
            fail(f"non-positive physical audit value: {label}")

    # Match the two-decimal scientific notation printed in the manuscript.
    expected = {
        "active power": f"{hp:.2e}",
        "reactive power": f"{hq:.2e}",
        "active-power balance": f"{pb:.2e}",
    }
    for label, number in expected.items():
        coeff, exp = number.split("e")
        exp_int = int(exp)
        coeff = coeff.rstrip("0").rstrip(".")
        pattern = rf"{re.escape(coeff)}\\times10\^\{{{exp_int}}}"
        if not re.search(pattern, tex):
            fail(f"{label} value is not the frozen CSV maximum: expected {number}")

    # Every manuscript figure reference must resolve to an artifact.
    expected_figures = [
        "fig1_overall_performance.pdf",
        "fig2_k1_vs_k2_tradeoff.pdf",
        "fig3_roc_curve.pdf",
        "fig4_pr_curve.pdf",
        "fig5_casewise_performance.pdf",
        "fig6_attackwise_performance.pdf",
        "fig10_severity_robustness.pdf",
        "fig12_ac_powerflow_consistency.pdf",
    ]
    for name in expected_figures:
        if not (FIG / name).exists():
            fail(f"missing final figure artifact: {name}")

    print("PASS: final manuscript provenance and frozen quantitative values are consistent.")
    print(f"  five-seed rows: {len(rows)}")
    print(f"  physical maxima: hP={hp:.3e}, hQ={hq:.3e}, balance={pb:.3e}")
    print(f"  figure directory: {FIG}")


if __name__ == "__main__":
    main()
