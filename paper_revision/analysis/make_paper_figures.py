#!/usr/bin/env python3
"""Regenerates every data figure of the manuscript that is not produced by make_revision_figures.py.

Sources (all committed in the repository):
  results/paper_final_verified_20260908/comparative_results.csv   Figs. 4 and 12 (primary seed, constituents)
  results/paper_final_verified_20260908/ablation_results.csv      Fig. 11 (primary seed, configurations A-F)
  results/paper_final_verified_20260908/current_physical_sanity.csv Fig. 17 (power-balance audit)
  paper_revision/results/raw/detector_outputs_5seed.csv           Figs. 6-10 (frozen five-seed trace)
  core.grid_topology.get_ieee_case_data (PYPOWER cases)            Fig. 2 (network graphs)
Each figure is written as PNG (300 dpi) and PDF, with its plotted values in source_data/.
Usage: python make_paper_figures.py <repo_root> <trace_csv> <out_dir>
"""
import sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, auc

REPO, TRACE, OUT = sys.argv[1:4]
sys.path.insert(0, REPO)
from core.grid_topology import get_ieee_case_data
os.makedirs(f"{OUT}/source_data", exist_ok=True)
RES = f"{REPO}/results/paper_final_verified_20260908"
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 10, "axes.titlesize": 10, "axes.labelsize": 10,
                     "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.grid": True,
                     "grid.color": "#d9d9d9", "grid.linewidth": 0.6, "axes.linewidth": 0.8, "savefig.bbox": "tight",
                     "savefig.pad_inches": 0.03, "legend.framealpha": 1.0, "legend.edgecolor": "#444444",
                     "hatch.linewidth": 0.6})
BARS = [dict(color="#262626", edgecolor="black"), dict(color="#a6a6a6", edgecolor="black", hatch="///"),
        dict(color="white", edgecolor="black", hatch="...")]
def save(fig, name, data):
    fig.savefig(f"{OUT}/{name}.png", dpi=300); fig.savefig(f"{OUT}/{name}.pdf"); plt.close(fig)
    data.to_csv(f"{OUT}/source_data/{name}.csv", index=False)
CASES = ["case9", "case14", "case30", "case118"]; CN = {"case9": "9-bus", "case14": "14-bus", "case30": "30-bus", "case118": "118-bus"}
d = pd.read_csv(TRACE); p = d[d.seed == 2026]

# ---------------- Fig. 2: benchmark networks (branch lists of the PYPOWER cases)
import networkx as nx
fig, axes = plt.subplots(2, 2, figsize=(8.0, 7.6)); rows = []
for ax, c, lab in zip(axes.ravel(), CASES, "abcd"):
    cd = get_ieee_case_data(c); br = np.asarray(cd["branch"], float); n = int(cd["num_buses"])
    g = nx.Graph(); g.add_nodes_from(range(1, n + 1)); g.add_edges_from((int(f), int(t)) for f, t in br[:, :2])
    pos = nx.kamada_kawai_layout(g)
    small = n <= 30
    nx.draw_networkx_edges(g, pos, ax=ax, width=0.9 if small else 0.6, edge_color="#555555")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_size=260 if small else 18, node_color="white", edgecolors="black", linewidths=0.9)
    if small: nx.draw_networkx_labels(g, pos, ax=ax, font_size=7.5, font_family="serif")
    ax.set_title(f"({lab}) {CN[c]}: {n} buses, {len(br)} branches", fontsize=9.5); ax.axis("off"); ax.grid(False)
    rows += [dict(case=c, from_bus=int(f), to_bus=int(t)) for f, t in br[:, :2]]
fig.tight_layout(); save(fig, "Fig02_networks", pd.DataFrame(rows))

# ---------------- Fig. 4: constituents and quorum modes, primary seed (comparative_results.csv)
cr = pd.read_csv(f"{RES}/comparative_results.csv"); cr["key"] = cr.Method.str.split(". ", n=1).str[1]
sel = [("NIS Standalone", "NIS"), ("CUSUM Standalone", "Sequential\nmonitor"), ("Jitter Standalone", "Jitter"),
       ("Sequential-Only Detector", "Leaky\naccumulator"), ("XMON-Grid K=1 (Sensitivity Mode)", "Quorum\n$K=1$"),
       ("XMON-Grid K=2 (Strict Majority)", "Quorum\n$K=2$")]
t4 = cr.set_index("key").loc[[s for s, _ in sel], ["F1", "Recall", "FPR"]].reset_index()
fig, ax = plt.subplots(figsize=(8.0, 3.6)); x = np.arange(len(sel)); w = 0.27
for i, (m, st) in enumerate(zip(["F1", "Recall", "FPR"], BARS)):
    ax.bar(x + (i - 1) * w, t4[m], w, label=m if m != "F1" else "F1-score", lw=0.8, **st)
ax.set_xticks(x); ax.set_xticklabels([l for _, l in sel]); ax.set_ylim(0, 1.08); ax.set_ylabel("Metric value")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=3, frameon=False); ax.grid(axis="x", visible=False)
fig.tight_layout(); save(fig, "Fig04_constituents", t4)

# ---------------- Fig. 6: ROC and PR of S_comp, primary seed (all cases pooled)
fpr, tpr, _ = roc_curve(p.y_true, p.s_comp); pr, rc, _ = precision_recall_curve(p.y_true, p.s_comp)
A_roc = roc_auc_score(p.y_true, p.s_comp); A_pr = auc(rc, pr); prev = p.y_true.mean()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.3))
a1.plot(fpr, tpr, "k-", lw=1.4, label=f"$S_{{comp}}$ (AUC = {A_roc:.4f})"); a1.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="Chance")
a1.set_xlabel("False-positive rate"); a1.set_ylabel("True-positive rate"); a1.set_title("(a) ROC curve"); a1.legend(loc="lower right")
a2.plot(rc, pr, "k-", lw=1.4, label=f"$S_{{comp}}$ (PR-AUC = {A_pr:.4f})"); a2.axhline(prev, ls="--", color="gray", lw=1, label=f"Prevalence = {prev:.2f}")
a2.set_xlabel("Recall"); a2.set_ylabel("Precision"); a2.set_ylim(0.7, 1.01); a2.set_title("(b) Precision–recall curve"); a2.legend(loc="lower left")
fig.tight_layout(); save(fig, "Fig06_roc_pr", pd.DataFrame(dict(metric=["ROC_AUC", "PR_AUC_trapezoid", "prevalence"], value=[A_roc, A_pr, prev])))

# ---------------- Fig. 7: K=2 by topology, primary seed
def met(y, a):
    tp = ((y == 1) & (a == 1)).sum(); fn = ((y == 1) & (a == 0)).sum(); fp = ((y == 0) & (a == 1)).sum(); tn = ((y == 0) & (a == 0)).sum()
    prc = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn); return dict(F1=2 * prc * r / (prc + r) if prc + r else 0, Recall=r, FPR=fp / (fp + tn))
t7 = pd.DataFrame([dict(case=c, **met(p[p.case == c].y_true.values, p[p.case == c].d_k2.values)) for c in CASES])
fig, ax = plt.subplots(figsize=(8.0, 3.5)); x = np.arange(4)
for i, (m, st) in enumerate(zip(["F1", "Recall", "FPR"], BARS)):
    b = ax.bar(x + (i - 1) * w, t7[m], w, label=m if m != "F1" else "F1-score", lw=0.8, **st)
    if m == "FPR":
        for xi, v in zip(x, t7[m]): ax.annotate(f"{v:.3f}", (xi + w, v), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels([CN[c] for c in CASES]); ax.set_ylim(0, 1.08); ax.set_ylabel("Metric value ($N=300$ per case)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=3, frameon=False); ax.grid(axis="x", visible=False)
fig.tight_layout(); save(fig, "Fig07_topology", t7)

# ---------------- Fig. 8: fraction of five seeds alarmed at each benign cycle index, K=2 and NIS
b = d[d.y_true == 0]
H = {col: b.groupby(["case", "sample_idx"])[col].mean().unstack().loc[CASES] for col in ["d_k2", "a_nis"]}
fig, axes = plt.subplots(2, 1, figsize=(8.0, 3.6), sharex=True)
for ax, col, ttl in zip(axes, ["d_k2", "a_nis"], ["(a) $K=2$ quorum", "(b) NIS test"]):
    im = ax.imshow(H[col].values, cmap="Greys", vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    ax.set_yticks(range(4)); ax.set_yticklabels([CN[c] for c in CASES]); ax.axvline(19.5, color="black", ls="--", lw=0.9)
    ax.set_title(ttl, loc="left", fontsize=9.5); ax.grid(False)
axes[1].set_xlabel("Cycle index $k$ within benign test sequence")
cb = fig.colorbar(im, ax=axes, fraction=0.03, pad=0.02); cb.set_label("Fraction of 5 seeds alarmed")
src = pd.concat([H[c].stack().rename("fraction").reset_index().assign(rule=c) for c in H])
save(fig, "Fig08_benign_alarms_by_cycle", src)

# ---------------- Figs. 9 and 10: K=2 recall by anomaly class and by tier, primary seed, with counts
a = p[p.y_true == 1]
cls = [("branch_outage", "Branch\noutage"), ("fdia", "Additive\nFDIA"), ("load_shift", "Voltage\nscale"), ("stealth_drift", "Low-amp.\ndrift")]
tiers = [("Tier 1 (Subtle)", "Tier 1\nSubtle"), ("Tier 2 (Moderate)", "Tier 2\nModerate"), ("Tier 3 (Strong)", "Tier 3\nStrong"), ("Tier 4 (Severe)", "Tier 4\nSevere")]
for name, key, groups, ylab, st in [("Fig09_class_recall", "scenario", cls, "Recall at $K=2$ ($N=240$ each)", BARS[1]),
                                     ("Fig10_tier_recall", "severity_tier", tiers, "Detection rate at $K=2$", dict(color="#bfbfbf", edgecolor="black", hatch=".."))]:
    rows = [dict(group=g, hits=int(a[a[key] == g].d_k2.sum()), n=int((a[key] == g).sum())) for g, _ in groups]
    t = pd.DataFrame(rows); t["rate"] = t.hits / t.n
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.bar(range(4), t.rate, 0.6, lw=0.8, **st)
    for i, r in t.iterrows(): ax.annotate(f"{r.rate:.3f}\n({r.hits}/{r.n})", (i, r.rate), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5)
    ax.set_xticks(range(4)); ax.set_xticklabels([l for _, l in groups]); ax.set_ylim(0, 1.22); ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel(ylab); ax.grid(axis="x", visible=False); fig.tight_layout(); save(fig, name, t)

# ---------------- Fig. 11: exploratory detector removal A-F, primary seed (ablation_results.csv)
ab = pd.read_csv(f"{RES}/ablation_results.csv"); ab["cfg"] = ab.Configuration.str[0]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 2.9))
for ax, m, st, ttl, yl in [(a1, "F1", BARS[0], "(a) F1-score", "F1-score"), (a2, "FPR", BARS[1], "(b) False-positive rate", "False-positive rate")]:
    ax.bar(ab.cfg, ab[m], 0.6, lw=0.8, **st)
    for xi, v in zip(ab.cfg, ab[m]): ax.annotate(f"{v:.3f}", (xi, v), textcoords="offset points", xytext=(0, 2), ha="center", fontsize=8)
    ax.set_title(ttl); ax.set_xlabel("Configuration"); ax.set_ylabel(yl); ax.grid(axis="x", visible=False)
a1.set_ylim(0, 1.1); a2.set_ylim(0, ab.FPR.max() * 1.2)
fig.tight_layout(); save(fig, "Fig11_detector_removal", ab[["Configuration", "F1", "Recall", "FPR", "MCC"]])

# ---------------- Fig. 12: recall versus FPR of the constituents, primary seed (comparative_results.csv)
mk = [("NIS Standalone", "NIS", "o", "white"), ("CUSUM Standalone", "Sequential monitor", "s", "white"), ("Jitter Standalone", "Jitter", "^", "white"),
      ("Sequential-Only Detector", "Leaky accumulator $\\Theta_k$", "v", "#7f7f7f"), ("XMON-Grid K=1 (Sensitivity Mode)", "Quorum $K=1$", "D", "#7f7f7f"),
      ("XMON-Grid K=2 (Strict Majority)", "Quorum $K=2$", "P", "black")]
t12 = cr.set_index("key").loc[[k for k, *_ in mk], ["Recall", "FPR"]].reset_index()
fig, ax = plt.subplots(figsize=(6.2, 3.4))
for (k, lab, m_, fc), (_, r) in zip(mk, t12.iterrows()):
    ax.scatter(max(r.FPR, 1e-3), r.Recall, marker=m_, s=70, facecolor=fc, edgecolor="black", lw=1.0, label=lab, zorder=3)
ax.set_xscale("log"); ax.set_xlim(7e-4, 1.3); ax.set_ylim(-0.05, 1.08)
ax.set_xlabel("False-positive rate (log scale, zero plotted at $10^{-3}$)"); ax.set_ylabel("Recall")
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False); fig.tight_layout(); save(fig, "Fig12_constituents", t12)

# ---------------- Fig. 17: power-balance audit (current_physical_sanity.csv)
ps = pd.read_csv(f"{RES}/current_physical_sanity.csv")
fig, ax = plt.subplots(figsize=(8.0, 3.2)); x = np.arange(4)
for i, (col, lab, st) in enumerate(zip(["h_p_max_abs_error", "h_q_max_abs_error", "power_balance_residual"],
                                       ["max $|h_P|$ error", "max $|h_Q|$ error", "$|$balance residual$|$"], BARS)):
    ax.bar(x + (i - 1) * w, ps[col].abs(), w, label=lab, lw=0.8, **st)
ax.set_yscale("log"); ax.set_ylim(1e-16, 1e-12); ax.set_xticks(x); ax.set_xticklabels([CN[c] for c in ps.case]); ax.set_ylabel("Absolute discrepancy (p.u.)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, frameon=False); ax.grid(axis="x", visible=False)
fig.tight_layout(); save(fig, "Fig17_power_balance_audit", ps)
print("paper figures done", f"ROC-AUC={A_roc:.4f} PR-AUC={A_pr:.4f}")
