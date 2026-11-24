#!/usr/bin/env python3
"""Analyses of original_protocol_runs.py, onset outputs and variants (review issues 13, 15, 20, 34; Table XI/XII checks).
Usage: python analyze_original_runs.py <exp_out_dir> <out_dir>"""
import sys, glob, numpy as np, pandas as pd
from scipy.stats import chi2
from sklearn.metrics import roc_auc_score
EXP, OUT = sys.argv[1], sys.argv[2]
import os
CASES = os.environ.get("CASES", "case9,case14,case30,case118").split(","); M = {"case9": 27, "case14": 42, "case30": 90, "case118": 354}
tr = pd.concat([pd.read_csv(f"{EXP}/trace_{c}.csv") for c in CASES]); tr["k"] = tr.sample_idx
cn = pd.concat([pd.read_csv(f"{EXP}/calib_nis_{c}.csv") for c in CASES])
cs = pd.concat([pd.read_csv(f"{EXP}/calib_size_{c}.csv") for c in CASES])
def met(y, p):
    y = np.asarray(y); p = np.asarray(p); tp = ((y == 1) & (p == 1)).sum(); fn = ((y == 1) & (p == 0)).sum(); fp = ((y == 0) & (p == 1)).sum(); tn = ((y == 0) & (p == 0)).sum()
    pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return dict(F1=2 * pr * rc / (pr + rc) if pr + rc else 0, Recall=rc, FPR=fp / (fp + tn) if fp + tn else 0)
def five(df, col):
    a = pd.DataFrame([met(g.y_true, g[col]) for _, g in df.groupby("seed")]); b = pd.DataFrame([met(g.y_true, g[col]) for _, g in df[df.k >= 20].groupby("seed")])
    return {**{f"{m}": a[m].mean() for m in a}, **{f"{m}_sd": a[m].std(ddof=1) for m in a}, **{f"{m}_k20": b[m].mean() for m in b}, **{f"{m}_k20_sd": b[m].std(ddof=1) for m in b}}

# --- reproduction check of the base configuration against the frozen five-seed trace
ref = pd.read_csv(sys.argv[3]) if len(sys.argv) > 3 else None
base = tr[tr.cfg == "base"].copy()
if ref is not None:
    r = ref[ref.case.isin(CASES)].sort_values(["seed", "case", "sample_id"]).reset_index(drop=True)
    b = base.assign(sample_id=base.case + "_" + base.scenario + "_" + base.sample_idx.map(lambda x: f"{x:03d}")).sort_values(["seed", "case", "sample_id"]).reset_index(drop=True)
    chk = {c: bool((b[c].values == r[c].values).all()) for c in ["a_nis", "a_cusum", "a_jitter", "a_seq", "d_k2", "d_k1"]}
    chk["nis_maxabs"] = float(np.abs(b.nis.values - r.nis.values).max()); print("reproduction:", chk)
    pd.DataFrame([chk]).to_csv(f"{OUT}/reproduction_check.csv", index=False)

# --- Issue 20: parameter sensitivity (one factor at a time)
rows = []
for cfg, g in tr.groupby("cfg"):
    for col, lab in [("a_cusum", "Sequential monitor"), ("d_k2", "Quorum K=2"), ("a_nis", "NIS test")]:
        rows.append(dict(factor="Q/R", setting=cfg, rule=lab, **five(g, col)))
b = base.sort_values(["seed", "case", "scenario", "k"]).copy(); b["y"] = (b.nis - b.mu0) / b.sd0
keys = list(zip(b.seed, b.case, b.scenario)); yv = b.y.values
for kap in [0.25, 0.5, 1.0]:
    gg = np.zeros(len(b)); pk = None; gv = 0.0
    for i in range(len(b)):
        if keys[i] != pk: gv = 0.0; pk = keys[i]
        gv = max(0.0, gv + yv[i] - kap); gg[i] = gv
    if kap == 0.5: assert np.allclose(gg, b.cusum_g.values), "recursion check failed"
    for tau in [3.0, 5.0, 7.0]:
        b["_a"] = (gg > tau).astype(int)
        b["_k2"] = ((b.a_nis + b._a + b.a_jitter) >= 2).astype(int)
        rows.append(dict(factor="kappa/tau", setting=f"kappa={kap}, tau={tau:g}", rule="Sequential monitor", **five(b, "_a")))
        rows.append(dict(factor="kappa/tau", setting=f"kappa={kap}, tau={tau:g}", rule="Quorum K=2", **five(b, "_k2")))
sens = pd.DataFrame(rows); sens.to_csv(f"{OUT}/T_param_sensitivity.csv", index=False)

# --- Issue 15: NIS threshold variants, thresholds from the 200 repository calibration NIS values
thr = []
for (c, s), g in cn.groupby(["case", "seed"]):
    v = g.sort_values("j").nis.values
    thr.append(dict(case=c, seed=s, chi2=chi2.ppf(0.99, M[c]), e99=np.quantile(v, 0.99), e95=np.quantile(v, 0.95),
                    e99b=np.quantile(v[20:], 0.99), e95b=np.quantile(v[20:], 0.95)))
thr = pd.DataFrame(thr); thr.to_csv(f"{OUT}/nis_thresholds.csv", index=False)
on = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{EXP}/onset_case*.csv"))]); on = on[on.kind != "calib"]
bt = base.merge(thr, on=["case", "seed"]); ot = on.merge(thr, on=["case", "seed"])
var = []
for col, lab in [("chi2", "Nominal chi-square 0.99 quantile"), ("e99", "Empirical 99th pct., all 200 calibration values"),
                 ("e95", "Empirical 95th pct., all 200 calibration values"), ("e99b", "Empirical 99th pct., calibration values after j=20"),
                 ("e95b", "Empirical 95th pct., calibration values after j=20")]:
    bt["_a"] = (bt.nis > bt[col]).astype(int); ot["_a"] = (ot.nis > ot[col]).astype(int)
    f = five(bt, "_a"); po = pd.DataFrame([met(g.y_true, g._a) for _, g in ot.groupby("seed")])
    var.append(dict(threshold=lab, col=col, FPR=f["FPR"], Recall=f["Recall"], FPR_k20=f["FPR_k20"], Recall_k20=f["Recall_k20"],
                    FPR_onset=po.FPR.mean(), Recall_onset=po.Recall.mean(), FPR_onset_sd=po.FPR.std(ddof=1)))
pd.DataFrame(var).to_csv(f"{OUT}/T_nis_threshold_variants.csv", index=False)

# --- Table XI check: benign NIS diagnostics after the first 20 cycles (five-seed means) and sigma0
diag = []
for c in CASES:
    per = []
    for s, g in base[(base.case == c) & (base.y_true == 0)].groupby("seed"):
        v = g.sort_values("k"); v = v[v.k >= 20].nis.values; m = M[c]
        per.append(dict(mean_m=v.mean() / m, var_2m=v.var(ddof=1) / (2 * m), acf=np.corrcoef(v[:-1], v[1:])[0, 1], exceed=(v > chi2.ppf(0.99, m)).mean()))
    per = pd.DataFrame(per)
    cv = cn[cn.case == c]
    s_all = np.mean([np.std(g.sort_values("j").nis.values) for _, g in cv.groupby("seed")])
    s_20 = np.mean([np.std(g.sort_values("j").nis.values[20:]) for _, g in cv.groupby("seed")])
    first = np.mean([g.sort_values("j").nis.values[0] for _, g in cv.groupby("seed")])
    diag.append(dict(case=c, **per.mean().to_dict(), sigma0_all=s_all, sigma0_after20=s_20, first_calib_nis=first))
pd.DataFrame(diag).to_csv(f"{OUT}/T_nis_diagnostics_check.csv", index=False)

# --- Table XII check: EWMA of standardized NIS, all cycles and k>=20, retrospective 'higher' quantiles
b = base.sort_values(["seed", "case", "scenario", "k"]).copy(); b["y"] = (b.nis - b.mu0) / b.sd0
e, out, pk = 0.0, [], None
for key, yy in zip(zip(b.seed, b.case, b.scenario), b.y.values):
    if key != pk: e = 0.0; pk = key
    e = 0.2 * yy + 0.8 * e; out.append(e)
b["ewma"] = out; b["win"] = b.groupby(["seed", "case", "scenario"]).nis.transform(lambda s: s.rolling(10, min_periods=1).sum())
chk = []
for col in ["ewma", "win"]:
    for name, sub in [("all", b), ("k20", b[b.k >= 20])]:
        au, r05, r15 = [], [], []
        for (s, c), g in sub.groupby(["seed", "case"]):
            au.append(dict(seed=s, auc=roc_auc_score(g.y_true, g[col]))); bb = g[g.y_true == 0][col]; aa = g[g.y_true == 1][col]
            r05.append((aa > np.quantile(bb, 0.95, method="higher")).mean()); r15.append((aa > np.quantile(bb, 0.85, method="higher")).mean())
        A = pd.DataFrame(au).groupby("seed").auc.mean()
        chk.append(dict(stat=col, subset=name, auc=A.mean(), auc_sd=A.std(ddof=1), rec05=np.mean(r05), rec15=np.mean(r15)))
pd.DataFrame(chk).to_csv(f"{OUT}/T_table12_check.csv", index=False)

# --- Issue 34: calibration size
cs.to_csv(f"{OUT}/calib_size_all.csv", index=False)
cs.groupby(["case", "n"]).tau_comp.agg(["min", "max", "mean", "std"]).to_csv(f"{OUT}/T_calib_size_summary.csv")

# --- Issues 12, 13: variants
vf = sorted(glob.glob(f"{EXP}/variants_case*.csv"))
if vf:
    v = pd.concat([pd.read_csv(f) for f in vf])
    meta = v[v.exp == "meta"][["case", "gen"]]; meta.to_csv(f"{OUT}/variants_meta.csv", index=False)
    bp = v[v.exp == "benign_process"].copy(); bp["m"] = bp.case.map(M); bp["r"] = bp.nis / bp.m
    rows = []
    for (c, gname), g in bp.groupby(["case", "gen"]):
        s = g[g.k >= 20]
        rows.append(dict(case=c, gen=gname, mean_ratio=s.r.mean(), exceed_k20=s.a_nis.mean(), nis_fpr_all=g.a_nis.mean(),
                         k2_fpr_all=g.d_k2.mean(), k2_fpr_k20=s.d_k2.mean()))
    pd.DataFrame(rows).to_csv(f"{OUT}/T_benign_process.csv", index=False)
    oo = v[v.exp == "outage_resolved"]
    oo.groupby("case")[["a_nis", "a_cusum", "d_k2"]].mean().to_csv(f"{OUT}/T_outage_resolved.csv")
    # repository fixed-state outage, same detectors, five seeds (original trace)
    base[base.scenario == "branch_outage"].groupby("case")[["a_nis", "a_cusum", "d_k2"]].mean().to_csv(f"{OUT}/T_outage_fixed_state.csv")
pd.set_option("display.width", 250)
for f in ["T_param_sensitivity", "T_nis_threshold_variants", "T_nis_diagnostics_check", "T_table12_check", "T_calib_size_summary", "T_benign_process", "T_outage_resolved", "T_outage_fixed_state"]:
    try: print("==", f); print(pd.read_csv(f"{OUT}/{f}.csv").round(4).to_string())
    except FileNotFoundError: pass
