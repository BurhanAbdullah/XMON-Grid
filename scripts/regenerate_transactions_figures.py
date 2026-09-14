from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'results/paper_final_verified_20260908'
SRC = ROOT / 'results/independent_validation_run'
OUT = PKG / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.titlesize': 12, 'axes.labelsize': 10,
    'xtick.labelsize': 9, 'ytick.labelsize': 9,
    'legend.fontsize': 9, 'axes.grid': True,
    'grid.alpha': 0.22, 'grid.linestyle': '--',
    'savefig.bbox': 'tight'
})

def rd(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def save(fig, stem):
    fig.savefig(OUT / f'{stem}.pdf')
    fig.savefig(OUT / f'{stem}.png', dpi=600)
    plt.close(fig)

def fig2():
    ms = rd(PKG/'multi_seed_summary.csv')
    comp = rd(PKG/'comparative_results.csv')
    d = {r['Method']: r for r in comp}
    k1 = d['10. XMON-Grid K=1 (Sensitivity Mode)']
    fprs = np.array([float(r['FPR']) for r in ms])
    recs = np.array([float(r['Recall']) for r in ms])
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    ax.scatter(float(k1['FPR']), float(k1['Recall']), s=95, marker='s', edgecolor='black', label='K=1 (primary seed)', zorder=4)
    ax.errorbar(fprs.mean(), recs.mean(), xerr=fprs.std(ddof=1), yerr=recs.std(ddof=1), fmt='D', ms=9, capsize=4, lw=1.2, label='K=2 mean +/- SD', zorder=5)
    ax.scatter(fprs, recs, s=38, facecolor='none', edgecolor='black', label='K=2 individual seeds', zorder=3)
    for r, x, y in zip(ms, fprs, recs):
        ax.annotate(r['seed'], (x, y), xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.annotate('K=1', (float(k1['FPR']), float(k1['Recall'])), xytext=(8, 8), textcoords='offset points', fontweight='bold')
    ax.annotate('K=2 mean', (fprs.mean(), recs.mean()), xytext=(8, -16), textcoords='offset points', fontweight='bold')
    ax.set_xlabel('False-positive rate (FPR)')
    ax.set_ylabel('Recall (sensitivity)')
    ax.set_title('Fig. 2 — K=1 vs. K=2 Operating-Point Trade-off')
    ax.set_xlim(0, .72); ax.set_ylim(.80, 1.03)
    ax.legend(loc='lower left')
    save(fig, 'fig2_k1_vs_k2_tradeoff')

def fig4():
    rows = rd(SRC/'metrics/detector_outputs.csv')
    y = np.array([int(r['y_true']) for r in rows])
    s = np.array([float(r['s_comp']) for r in rows])
    from sklearn.metrics import precision_recall_curve, auc
    p, r, _ = precision_recall_curve(y, s)
    a = auc(r, p)
    fig, ax = plt.subplots(figsize=(6.2, 4.7))
    ax.plot(r, p, lw=2, label=f'$S_{{comp}}$ (PR-AUC={a:.4f})')
    ax.axhline(.80, ls='--', lw=1.2, label='Prevalence baseline (0.80)')
    ax.set_xlabel('Recall (sensitivity)'); ax.set_ylabel('Precision')
    ax.set_title('Fig. 4 — Precision–Recall Curve')
    ax.set_xlim(0, 1); ax.set_ylim(.70, 1.02); ax.legend(loc='lower left')
    save(fig, 'fig4_pr_curve')

def fig5():
    rows = rd(SRC/'audit/audit_5seed_case_wise.csv')
    labels = [r['case'].upper() for r in rows]
    means = np.array([float(r['mean_F1']) for r in rows])
    sd = np.array([float(r['SD_F1']) for r in rows])
    ci = t.ppf(.975, 4) * sd / np.sqrt(5)
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.8, 4.3))
    ax.bar(x, means, yerr=ci, capsize=5, width=.55, edgecolor='black', linewidth=.5)
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(.80, 1.04)
    ax.set_ylabel('Mean F1-score (5 seeds)')
    ax.set_title('Fig. 5 — Case-Wise Performance')
    ax.text(.99, .02, 'Error bars: 95% CI', transform=ax.transAxes, ha='right', va='bottom', fontsize=8)
    save(fig, 'fig5_casewise_performance')

def fig8():
    rows = rd(PKG/'comparative_results.csv')
    wanted = ['1. NIS Standalone','2. CUSUM Standalone','3. Jitter Standalone','8. Sequential-Only Detector','10. XMON-Grid K=1 (Sensitivity Mode)','9. XMON-Grid K=2 (Strict Majority)']
    names = ['NIS','CUSUM','Jitter','Sequential','K=1','K=2']
    d = {r['Method']: r for r in rows}
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    offsets = [(8,8),(8,-14),(8,10),(8,8),(-8,-16),(-8,10)]
    for name, disp, off in zip(wanted, names, offsets):
        r = d[name]; fpr = float(r['FPR']); rec = float(r['Recall']); x = max(fpr, 1e-3)
        marker = 'D' if disp == 'K=2' else ('s' if disp == 'K=1' else 'o')
        ax.scatter(x, rec, s=78, marker=marker, edgecolor='black', zorder=4)
        ax.annotate(disp, (x, rec), xytext=off, textcoords='offset points', fontweight='bold')
    ax.set_xscale('log'); ax.set_xlabel('False-positive rate (FPR) [log scale]')
    ax.set_ylabel('Recall (sensitivity)'); ax.set_title('Fig. 8 — False-Positive / Sensitivity Trade-off')
    ax.set_ylim(-.03, 1.05)
    ax.text(.99, .015, 'Zero-FPR observations are displayed at $10^{-3}$ only for log-axis visibility.', transform=ax.transAxes, ha='right', va='bottom', fontsize=8)
    save(fig, 'fig8_false_positive_tradeoff')

def fig10():
    rows = rd(SRC/'robustness_results.csv')
    rows = [r for r in rows if r['experiment']=='Exp4_Severity_Sweep' and r['seed']=='2026']
    tiers = ['Tier 1 (Subtle)','Tier 2 (Moderate)','Tier 3 (Strong)','Tier 4 (Severe)']
    vals = []
    for tier in tiers:
        tp = sum(float(r['value']) for r in rows if r['param_value']==tier and r['metric']=='TP')
        fn = sum(float(r['value']) for r in rows if r['param_value']==tier and r['metric']=='FN')
        vals.append(tp/(tp+fn) if tp+fn else np.nan)
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    x = np.arange(4)
    ax.bar(x, vals, width=.58, edgecolor='black', linewidth=.5)
    ax.set_xticks(x); ax.set_xticklabels(['Tier 1\nSubtle','Tier 2\nModerate','Tier 3\nStrong','Tier 4\nSevere'])
    ax.set_ylim(0, 1.08); ax.set_ylabel('Detection rate')
    ax.set_title('Fig. 10 — Attack-Severity Spectrum (Descriptive Stratification)')
    for i, v in enumerate(vals): ax.text(i, v+.02, f'{v:.3f}', ha='center', fontsize=9)
    ax.text(.99, .02, 'Primary seed; pooled across evaluated cases/attack classes; non-monotonic descriptive result.', transform=ax.transAxes, ha='right', va='bottom', fontsize=7.5)
    save(fig, 'fig10_severity_robustness')

def fig11():
    rows = rd(SRC/'robustness_results.csv')
    rs = [r for r in rows if r['experiment']=='Exp9_Scalability_Latency' and r['metric']=='per_step_latency_ms']
    pairs = []
    for r in rs:
        b = next(float(x['value']) for x in rows if x['experiment']=='Exp9_Scalability_Latency' and x['case']==r['case'] and x['metric']=='num_buses')
        pairs.append((b, float(r['value'])))
    pairs = sorted(set(pairs))
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    b = [p[0] for p in pairs]; v = [p[1] for p in pairs]
    ax.plot(b, v, 'o-', lw=1.8, label='Measured latency')
    for x, y in pairs:
        dx = -8 if x == 9 else (8 if x == 14 else 0)
        ax.annotate(f'{int(x)}: {y:.3f}', (x, y), xytext=(dx, 10), textcoords='offset points', ha='center', fontsize=8)
    ax.set_xlabel('Number of buses'); ax.set_ylabel('Per-step latency (ms)')
    ax.set_title('Fig. 11 — Empirical Computational Latency Across Benchmark Sizes')
    ax.legend(loc='upper left')
    save(fig, 'fig11_computational_scaling')

def fig12():
    rows = rd(PKG/'current_physical_sanity.csv')
    cases = ['IEEE 9','IEEE 14','IEEE 30','IEEE 118']
    vals = [max(abs(float(r['h_p_max_abs_error'])), abs(float(r['h_q_max_abs_error'])), abs(float(r['power_balance_residual']))) for r in rows]
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    x = np.arange(4)
    ax.bar(x, vals, width=.52, edgecolor='black', linewidth=.5)
    ax.set_yscale('log'); ax.set_xticks(x); ax.set_xticklabels(cases)
    ax.set_ylabel('Maximum absolute numerical residual (p.u.)')
    ax.set_title('Fig. 12 — AC Power-Flow Numerical Consistency')
    ax.set_ylim(1e-16, max(vals)*8)
    for i, v in enumerate(vals): ax.text(i, v*1.35, f'{v:.2e}', ha='center', fontsize=8)
    ax.text(.99, .02, 'Case-wise maximum of |hP|, |hQ|, and |power-balance residual|.', transform=ax.transAxes, ha='right', va='bottom', fontsize=8)
    save(fig, 'fig12_ac_powerflow_consistency')

if __name__ == '__main__':
    # First regenerate every figure using the repository's existing generators.
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT/'scripts/generate_final_figures_1_6.py')], check=True)
    subprocess.run([sys.executable, str(ROOT/'scripts/generate_final_figures_7_12.py')], check=True)
    # Then reconcile the figures whose displayed content/captions needed correction.
    for fn in (fig2, fig4, fig5, fig8, fig10, fig11, fig12):
        fn()
    print('All 12 publication figure pairs regenerated; reconciled figures: 2,4,5,8,10,11,12')
