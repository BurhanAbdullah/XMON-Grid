#!/usr/bin/env python3
"""Generate clean Figures 7--12 without changing underlying data.

Figures 7, 8 and 12 read directly from the frozen verification package.
Figures 9--11 require a fresh current `results/independent_validation_run/`
robustness artifact; they are not treated as authoritative until that run is
completed and the resulting files are copied/hash-recorded in the final package.
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "results" / "paper_final_verified_20260908"
SRC = ROOT / "results" / "independent_validation_run"
OUT = PKG / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linestyle": "--",
    "savefig.bbox": "tight",
})


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.png", dpi=600)
    plt.close(fig)


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def fig7():
    rows = read_csv(PKG / "ablation_results.csv")
    labels = ["A. Full XMON-Grid\n(K=2)", "B. w/o NIS\n(CUSUM + Jitter)",
              "C. w/o CUSUM\n(NIS + Jitter)", "D. w/o Jitter\n(NIS + CUSUM)",
              "E. w/o Sequential\n(Memoryless)", "F. w/o Quorum\n(Continuous $S_{comp}$)"]
    f1 = [float(r["F1"]) for r in rows]
    fpr = [float(r["FPR"]) for r in rows]
    y = np.arange(len(labels))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    ax1.barh(y, f1, height=0.62, edgecolor="black", linewidth=0.5)
    ax2.barh(y, fpr, height=0.62, edgecolor="black", linewidth=0.5)
    ax1.set_xlim(0, 1.02); ax2.set_xlim(0, max(fpr) * 1.25)
    ax1.set_xlabel("F1-score"); ax2.set_xlabel("False-positive rate")
    ax1.set_yticks(y); ax1.set_yticklabels(labels)
    ax1.invert_yaxis()
    ax1.set_title("(a) F1-score"); ax2.set_title("(b) False-positive rate")
    for i, v in enumerate(f1): ax1.text(v + 0.012, i, f"{v:.4f}", va="center", fontsize=8)
    for i, v in enumerate(fpr): ax2.text(v + max(fpr)*0.02, i, f"{v:.4f}", va="center", fontsize=8)
    fig.suptitle("Fig. 7 — Component Ablation Study", y=1.01)
    fig.tight_layout()
    save(fig, "fig7_ablation_study")


def fig8():
    rows = read_csv(PKG / "comparative_results.csv")
    wanted = ["1. NIS Standalone", "2. CUSUM Standalone", "3. Jitter Standalone",
              "8. Sequential-Only Detector", "10. XMON-Grid K=1 (Sensitivity Mode)",
              "9. XMON-Grid K=2 (Strict Majority)"]
    data = {r["Method"]: r for r in rows}
    pts = []
    for name in wanted:
        r = data[name]
        pts.append((name, float(r["FPR"]), float(r["Recall"])))

    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    styles = {
        "1. NIS Standalone": ("o", "NIS"),
        "2. CUSUM Standalone": ("o", "CUSUM"),
        "3. Jitter Standalone": ("o", "Jitter"),
        "8. Sequential-Only Detector": ("o", "Sequential"),
        "10. XMON-Grid K=1 (Sensitivity Mode)": ("s", "XMON-Grid K=1"),
        "9. XMON-Grid K=2 (Strict Majority)": ("D", "XMON-Grid K=2"),
    }
    plotted_x = []
    for idx, (name, fpr, rec) in enumerate(pts, start=1):
        x = max(fpr, 1e-3)
        marker, label = styles[name]
        ax.scatter(x, rec, marker=marker, s=75, facecolor="white" if "Sequential" in name else "#4F6F8F",
                   edgecolor="black", linewidth=0.9, label=label, zorder=5)
        dx = 7 if x < 0.01 else -7
        ha = "left" if dx > 0 else "right"
        dy = 10 if rec < 0.95 else -14
        ax.annotate(str(idx), (x, rec), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=9, fontweight="bold")
        plotted_x.append(x)

    ax.set_xscale("log")
    ax.set_xlabel("False-positive rate (FPR) [log scale]")
    ax.set_ylabel("Recall (sensitivity)")
    ax.set_title("Fig. 8 — False-Positive / Sensitivity Trade-off")
    ax.set_ylim(-0.03, 1.05)
    ax.grid(True, which="both")
    ax.legend(title="Detector", loc="lower right", frameon=True)
    ax.text(0.99, 0.015, "Zero-FPR observations are plotted at $10^{-3}$ for log-axis visibility.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="0.35")
    fig.tight_layout()
    save(fig, "fig8_false_positive_tradeoff")


def fig9():
    rows = read_csv(SRC / "robustness_results.csv")
    rows = [r for r in rows if r["experiment"] == "Exp5_Measurement_Noise_Sweep" and r["seed"] == "2026"]
    scales = sorted({float(r["param_value"]) for r in rows})
    f1 = [float(next(r["value"] for r in rows if float(r["param_value"]) == x and r["metric"] == "F1")) for x in scales]
    fpr = [float(next(r["value"] for r in rows if float(r["param_value"]) == x and r["metric"] == "FPR")) for x in scales]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.plot(scales, f1, marker="o", linewidth=2, label="F1-score")
    ax2 = ax.twinx()
    ax2.plot(scales, fpr, marker="s", linewidth=2, linestyle="--", label="FPR")
    ax.set_xlabel(r"Measurement-noise standard deviation $\sigma_v$ (p.u.)")
    ax.set_ylabel("F1-score"); ax2.set_ylabel("False-positive rate")
    ax.set_ylim(0.70, 1.02); ax2.set_ylim(-0.01, max(0.15, max(fpr)*1.2))
    ax.set_title("Fig. 9 — Measurement-Noise Robustness Sweep")
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], loc="best")
    fig.tight_layout(); save(fig, "fig9_noise_robustness")


def fig10():
    rows = read_csv(SRC / "robustness_results.csv")
    rows = [r for r in rows if r["experiment"] == "Exp4_Severity_Sweep" and r["case"] == "case9" and r["seed"] == "2026"]
    tiers = ["Tier 1\nSubtle", "Tier 2\nModerate", "Tier 3\nStrong", "Tier 4\nSevere"]
    raw = ["Tier 1 (Subtle)", "Tier 2 (Moderate)", "Tier 3 (Strong)", "Tier 4 (Severe)"]
    f1 = [float(next(r["value"] for r in rows if r["param_value"] == t and r["metric"] == "F1")) for t in raw]
    rec = [float(next(r["value"] for r in rows if r["param_value"] == t and r["metric"] == "Recall")) for t in raw]
    x = np.arange(4); w = 0.36
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(x-w/2, f1, w, label="F1-score", edgecolor="black", linewidth=0.5)
    ax.bar(x+w/2, rec, w, label="Recall", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tiers); ax.set_ylim(0.60, 1.05)
    ax.set_ylabel("Metric value"); ax.set_title("Fig. 10 — Attack-Severity Spectrum Robustness")
    ax.legend(loc="lower right")
    fig.tight_layout(); save(fig, "fig10_severity_robustness")


def fig11():
    rows = read_csv(SRC / "robustness_results.csv")
    lat = [r for r in rows if r["experiment"] == "Exp9_Scalability_Latency" and r["metric"] == "per_step_latency_ms"]
    buses, vals = [], []
    for r in lat:
        buses.append(int(next(x["value"] for x in rows if x["experiment"] == "Exp9_Scalability_Latency" and x["case"] == r["case"] and x["metric"] == "num_buses")))
        vals.append(float(r["value"]))
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.plot(buses, vals, "o-", linewidth=1.8, label="Measured latency")
    for b, v in zip(buses, vals): ax.annotate(f"{b}: {v:.3f}", (b, v), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)
    ax.set_xlabel("Number of buses"); ax.set_ylabel("Per-step latency (ms)")
    ax.set_title("Fig. 11 — Computational Latency Across Benchmark Sizes")
    ax.legend(loc="upper left")
    fig.tight_layout(); save(fig, "fig11_computational_scaling")


def fig12():
    rows = read_csv(PKG / "current_physical_sanity.csv")
    cases = ["IEEE 9", "IEEE 14", "IEEE 30", "IEEE 118"]
    errors = [max(float(r["h_p_max_abs_error"]), float(r["h_q_max_abs_error"]), abs(float(r["power_balance_residual"]))) for r in rows]
    labels = [f"{x:.2e}" for x in errors]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    x = np.arange(len(cases))
    ax.bar(x, errors, width=0.52, edgecolor="black", linewidth=0.5)
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(cases)
    ax.set_ylabel("Maximum absolute numerical residual (p.u.)")
    ax.set_title("Fig. 12 — AC Power-Flow Numerical Consistency")
    ax.set_ylim(1e-16, max(errors)*8)
    for i, (v, lab) in enumerate(zip(errors, labels)): ax.text(i, v*1.35, lab, ha="center", va="bottom", fontsize=8)
    fig.tight_layout(); save(fig, "fig12_ac_powerflow_consistency")


if __name__ == "__main__":
    fig7(); fig8(); fig12()
    # These three require fresh robustness outputs and are intentionally separated
    # from the frozen verification values above.
    if (SRC / "robustness_results.csv").exists():
        fig9(); fig10(); fig11()
    else:
        print("NOTE: robustness_results.csv not present; Figures 9--11 were not generated.")
    print(f"Figures written to {OUT}")
