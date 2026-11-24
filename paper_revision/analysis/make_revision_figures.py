#!/usr/bin/env python3
"""Figures added or regenerated in the revision. Grayscale, STIX serif, 300 dpi PNG plus PDF.
Every plotted value is read from a CSV written by the analysis scripts (source data saved next to each figure).
Usage: python make_revision_figures.py <ana_dir> <exp_out_dir> <fig_dir> [which ...]"""
import sys, os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ANA, EXP, FIG = sys.argv[1:4]; WHICH = set(sys.argv[4:])
os.makedirs(f"{FIG}/source_data", exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 10, "axes.titlesize": 10, "axes.labelsize": 10,
                     "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.grid": True,
                     "grid.color": "#d9d9d9", "grid.linewidth": 0.6, "axes.linewidth": 0.8, "savefig.bbox": "tight",
                     "savefig.pad_inches": 0.03, "legend.framealpha": 1.0, "legend.edgecolor": "#444444"})
def want(k): return not WHICH or k in WHICH
def save(fig, name, data=None):
    fig.savefig(f"{FIG}/{name}.png", dpi=300); fig.savefig(f"{FIG}/{name}.pdf"); plt.close(fig)
    if data is not None: data.to_csv(f"{FIG}/source_data/{name}.csv", index=False)

# ---------------------------------------------------------------- evaluation timeline (Issue 14)
if want("timeline"):
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 3.3))
    def box(ax, x0, x1, txt, fc, ls="-"):
        ax.add_patch(FancyBboxPatch((x0, 0.18), x1 - x0, 0.64, boxstyle="round,pad=0.0,rounding_size=0.03",
                                    fc=fc, ec="black", lw=0.9, ls=ls))
        ax.text((x0 + x1) / 2, 0.5, txt, ha="center", va="center", fontsize=8.6, linespacing=1.15)
    for ax in axes:
        ax.set_xlim(0, 100); ax.set_ylim(0, 1); ax.axis("off")
    a = axes[0]; a.set_title("(a) Original protocol (all headline results)", loc="left", fontsize=9.5)
    box(a, 0, 27, "Calibration phase\n200 benign samples, flat start\n" + r"$\mu_0,\sigma_0,\mu_T,\sigma_T,\tau_\Theta,\tau_{\mathrm{comp}}$", "#e6e6e6")
    box(a, 31, 51, "Test-sequence reset\nflat-start estimator, $P_0$\n$g_k$, jitter window, $\\Theta_k$ = 0", "#ffffff", "--")
    box(a, 55, 100, "60-cycle test sequence, scored from $k=0$\nbenign, or anomalous from $k=0$ to $k=59$\none scenario per sequence, no within-sequence transition", "#bdbdbd")
    for x0, x1 in [(27, 31), (51, 55)]:
        a.annotate("", xy=(x1, 0.5), xytext=(x0, 0.5), arrowprops=dict(arrowstyle="->", lw=0.9))
    b = axes[1]; b.set_title("(b) Onset experiment (Section III-F)", loc="left", fontsize=9.5)
    box(b, 0, 19, "Calibration phase\nsame 200 samples\nand moments as (a)", "#e6e6e6")
    box(b, 22, 40, "Reset, then 30-cycle\nwarm-up (estimator only,\nnot scored)", "#ffffff", "--")
    box(b, 43, 67, "30 benign cycles, scored\ndetectors start at reset state\nfalse alarms, ARL$_0$", "#e6e6e6")
    box(b, 70, 100, "30 anomalous cycles, scored\none class and one tier\ndelay, $P_d$, ARL$_1$, recall", "#bdbdbd")
    for x0, x1 in [(19, 22), (40, 43)]:
        b.annotate("", xy=(x1, 0.5), xytext=(x0, 0.5), arrowprops=dict(arrowstyle="->", lw=0.9))
    b.annotate("onset", xy=(68.5, 0.86), xytext=(68.5, 1.02), ha="center", fontsize=8.5,
               arrowprops=dict(arrowstyle="->", lw=0.9)); b.plot([68.5, 68.5], [0.1, 0.86], color="black", lw=0.9, ls=":")
    fig.tight_layout(h_pad=0.6); save(fig, "Fig_timeline")

# ---------------------------------------------------------------- K=1 versus K=2, five seeds (Issue 6)
if want("k1k2"):
    p1 = pd.read_csv(f"{ANA}/perseed_d_k1.csv"); p2 = pd.read_csv(f"{ANA}/perseed_d_k2.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.05))
    for p, mk, fc, lab in [(p1, "D", "#7f7f7f", "$K=1$"), (p2, "s", "black", "$K=2$")]:
        a1.scatter(p.FPR, p.Recall, marker="o", facecolor="white", edgecolor="black", s=26, zorder=3)
        a1.errorbar(p.FPR.mean(), p.Recall.mean(), xerr=p.FPR.std(ddof=1), yerr=p.Recall.std(ddof=1), fmt=mk,
                    color=fc, mec="black", ms=7, capsize=3, lw=1.1, zorder=4, label=f"{lab}, mean ± SD (5 seeds)")
    a1.scatter([], [], marker="o", facecolor="white", edgecolor="black", s=26, label="Individual seeds")
    lo, hi = p2.FPR.min() - 0.02, p2.FPR.max() + 0.02; ylo, yhi = p2.Recall.min() - 0.0015, p2.Recall.max() + 0.0015
    a1.add_patch(plt.Rectangle((lo, ylo - 0.004), hi - lo, yhi - ylo + 0.008, fill=False, ls="--", lw=0.8, ec="#555555"))
    a1.set_xlim(0, 0.72); a1.set_ylim(0.86, 1.01); a1.set_xlabel("False-positive rate"); a1.set_ylabel("Recall")
    a1.set_title("(a) Operating points, five seeds"); a1.legend(loc="center right")
    a2.scatter(p2.FPR, p2.Recall, marker="o", facecolor="white", edgecolor="black", s=34, zorder=3, label="Individual seeds")
    for s, x, y in zip(p2.seed, p2.FPR, p2.Recall):
        a2.annotate(str(s), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    a2.errorbar(p2.FPR.mean(), p2.Recall.mean(), xerr=p2.FPR.std(ddof=1), yerr=p2.Recall.std(ddof=1), fmt="s",
                color="black", ms=7, capsize=3, lw=1.1, zorder=4, label="Mean ± SD")
    a2.set_xlim(p2.FPR.min() - 0.012, p2.FPR.max() + 0.02); a2.set_xlabel("False-positive rate"); a2.set_ylabel("Recall"); a2.set_title("(b) $K=2$ detail (dashed box in (a))")
    a2.legend(loc="upper right")
    fig.tight_layout(); save(fig, "Fig_k1_k2", pd.concat([p1.assign(rule="K=1"), p2.assign(rule="K=2")]))

# ---------------------------------------------------------------- noise stress test, current code (two seeds)
if want("noise"):
    n = pd.read_csv(f"{EXP}/exp3_exp5_current.csv"); n = n[n.experiment == "Exp5"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 2.75))
    xs = sorted(n.param.unique()); xi = {v: i for i, v in enumerate(xs)}
    for s, ls, fc in [(2026, "-", "white"), (2027, "--", "#7f7f7f")]:
        g = n[n.seed == s].sort_values("param"); x = [xi[v] for v in g.param]
        a1.plot(x, g.F1, ls=ls, marker="o", color="black", mfc=fc, ms=5, lw=1.1, label=f"F1, seed {s}")
        a1.plot(x, g.Recall, ls=ls, marker="s", color="#666666", mfc=fc, ms=5, lw=1.1, label=f"Recall, seed {s}")
        a2.plot(x, g.FPR, ls=ls, marker="^", color="black", mfc=fc, ms=5.5, lw=1.1, label=f"Seed {s}")
    for a in (a1, a2):
        a.set_xticks(range(len(xs))); a.set_xticklabels([f"{v:g}" for v in xs]); a.set_xlabel("Added measurement noise $\\sigma$ (p.u.)")
    a1.set_ylabel("Metric value"); a1.set_title("(a) F1-score and recall"); a2.set_ylabel("False-positive rate"); a2.set_ylim(-0.04, 1.05)
    a2.set_title("(b) False-positive rate")
    a1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False); a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False)
    fig.tight_layout(); save(fig, "Fig_noise", n)

# ---------------------------------------------------------------- latency from Table XIII (repeated measurement only, Issue 31)
if want("latency"):
    l = pd.read_csv(f"{EXP}/latency_repeated.csv")
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.errorbar(l.buses, l.median_ms, yerr=[np.zeros(len(l)), l.p95_ms - l.median_ms], fmt="s-", color="black",
                mfc="#9e9e9e", ms=6, capsize=3, lw=1.1)
    for xb, yv in zip(l.buses, l.median_ms):
        ax.annotate(f"{yv:.3g}", (xb, yv), textcoords="offset points", xytext=(8, -12), fontsize=9)
    ax.set_yscale("log"); ax.set_xlim(0, 130); ax.set_ylim(0.1, 1000)
    ax.set_xlabel("Number of buses"); ax.set_ylabel("Per-step latency (ms)")
    fig.tight_layout(); save(fig, "Fig_latency", l)

# ---------------------------------------------------------------- calibration size versus calibrated thresholds (Issue 34)
if want("calsize"):
    c = pd.concat([pd.read_csv(f"{EXP}/calib_size_{k}.csv") for k in ["case9", "case14", "case30", "case118"] if os.path.exists(f"{EXP}/calib_size_{k}.csv")])
    fig, axes = plt.subplots(1, 4, figsize=(8.0, 2.45), sharey=True)
    styles = ["-", "--", ":", "-.", (0, (5, 1, 1, 1))]
    for ax, (k, nm) in zip(axes, [("case9", "9-bus"), ("case14", "14-bus"), ("case30", "30-bus"), ("case118", "118-bus")]):
        g = c[c.case == k]
        if g.empty: continue
        for (s, h), ls in zip(g.groupby("seed"), styles):
            h = h.sort_values("n"); ax.plot(h.n, h.tau_comp, ls=ls, marker="o", ms=3.5, color="black", mfc="white", lw=1.0, label=str(s))
        ax.set_xscale("log"); ax.set_xticks([50, 100, 200, 400]); ax.set_xticklabels(["50", "100", "200", "400"])
        ax.minorticks_off(); ax.set_title(nm); ax.set_xlabel("Calibration samples")
    axes[0].set_ylabel(r"$\tau_{\mathrm{comp}}$ (99th pct.)")
    axes[-1].legend(title="Seed", loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8)
    fig.tight_layout(); save(fig, "Fig_calsize", c)

# ---------------------------------------------------------------- onset experiment, constant severity (Issues 1, 2, 4)
if want("onset"):
    t = pd.read_csv(f"{ANA}/T_onset_class_tier.csv")
    tiers = ["Tier 1 (Subtle)", "Tier 2 (Moderate)", "Tier 3 (Strong)", "Tier 4 (Severe)"]
    L = [("a_cusum", "Sequential monitor ($\\tau=5$)", "-", "o", "black"), ("d_k2", "Quorum $K=2$", "--", "s", "black"),
         ("m01_cusum_g", "CUSUM $g_k$, matched", "-", "^", "#7f7f7f"), ("m01_ewma", "EWMA, matched", "--", "v", "#7f7f7f"),
         ("m01_win", "Window sum, matched", ":", "D", "#7f7f7f"), ("m01_nis", "Single-cycle NIS, matched", "-.", "x", "black")]
    fig, axes = plt.subplots(1, 4, figsize=(8.0, 2.75), sharey=True)
    for ax, (cls, nm) in zip(axes, [("fdia", "(a) Additive FDIA"), ("load_shift", "(b) Voltage scale"),
                                     ("stealth_drift", "(c) Drift"), ("branch_outage", "(d) Branch outage")]):
        for col, lab, ls, mk, colr in L:
            g = t[(t.cls == cls) & (t.col == col)].set_index("tier").loc[tiers]
            ax.plot(range(1, 5), g.Recall, ls=ls, marker=mk, color=colr, mfc="white" if mk not in "x" else colr, ms=4.5, lw=1.0, label=lab)
        ax.set_xticks(range(1, 5)); ax.set_xticklabels(["T1", "T2", "T3", "T4"]); ax.set_title(nm, fontsize=9.5)
        ax.set_ylim(-0.03, 1.05); ax.set_xlabel("Severity tier")
    axes[0].set_ylabel("Post-onset recall")
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    fig.tight_layout(); save(fig, "Fig_onset_severity", t)
print("figures done")
