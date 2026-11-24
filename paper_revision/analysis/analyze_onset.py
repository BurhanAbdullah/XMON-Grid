#!/usr/bin/env python3
"""Analysis of the onset experiment (outputs of onset_experiment.py).

Statistics on the same NIS stream, all restarted at the first scored cycle of each sequence:
  NIS xi_k (single cycle), CUSUM g_k (repository value), EWMA e_k = 0.2 y_k + 0.8 e_{k-1} of the
  standardized NIS y_k = (xi_k - mu0)/sigma0 (repository calibration moments), sliding sum of the
  last 10 NIS values, leaky accumulator Theta_k (repository value).
Matched operating point: for each case and seed, the threshold of each statistic is the
(1 - alpha) quantile ('higher' method) of its values on the four benign calibration sequences,
frozen before the test sequences are scored. Alarm: statistic > threshold.
Repository rules keep their own fixed thresholds.
Metrics:
  FPR       alarms / benign scored cycles (benign test sequences and pre-onset segments)
  Pd        fraction of onset sequences with an alarm in the 30 post-onset cycles
  delay     first alarm index at or after onset minus onset (0 = alarm in the onset cycle)
  ARL1      mean of (delay + 1) over detected sequences
  ARL0      censored geometric estimate: total benign cycles observed up to and including the
            first false alarm (or segment end) divided by the number of segments with a false alarm
  recall    alarms / attacked cycles
Usage: python analyze_onset.py <out_dir> <onset_csv> [<onset_csv> ...]
"""
import sys, numpy as np, pandas as pd
OUT = sys.argv[1]
d = pd.concat([pd.read_csv(f) for f in sys.argv[2:]], ignore_index=True)
d = d.sort_values(["case", "seed", "kind", "seq", "k"]).reset_index(drop=True)
d["y"] = (d.nis - d.mu0) / d.sd0
def ewma(v):
    e, o = 0.0, []
    for x in v:
        e = 0.2 * x + 0.8 * e; o.append(e)
    return o
g = d.groupby(["case", "seed", "kind", "seq"], sort=False)
d["ewma"] = np.concatenate([ewma(x.values) for _, x in g.y])
d["win"] = g.nis.transform(lambda s: s.rolling(10, min_periods=1).sum())
STATS = [("NIS (single cycle)", "nis"), ("Sliding sum of NIS (10 cycles)", "win"), ("EWMA of standardized NIS", "ewma"),
         ("CUSUM recursion g", "cusum_g"), ("Leaky accumulator Theta", "theta_seq")]
REPO = [("NIS test, chi-square threshold", "a_nis"), ("Sequential monitor (tau=5)", "a_cusum"), ("Timing jitter", "a_jitter"),
        ("Leaky accumulator (tau_Theta)", "a_seq"), ("Quorum K=1", "d_k1"), ("Quorum K=2", "d_k2")]
for alpha in [0.01, 0.05]:
    for lab, col in STATS:
        thr = d[d.kind == "calib"].groupby(["case", "seed"])[col].quantile(1 - alpha, interpolation="higher").rename("thr")
        d = d.merge(thr, left_on=["case", "seed"], right_index=True, how="left")
        d[f"m{int(alpha*100):02d}_{col}"] = (d[col] > d.thr).astype(int); d = d.drop(columns="thr")
test = d[d.kind != "calib"].copy()
RULES = [(l, c, "fixed") for l, c in REPO] + [(l, f"m01_{c}", "alpha=0.01") for l, c in STATS] + [(l, f"m05_{c}", "alpha=0.05") for l, c in STATS]

def seg_metrics(t, col):
    ben = t[t.y_true == 0]; att = t[t.y_true == 1]
    fpr = ben[col].mean(); rec = att[col].mean()
    # benign segments: benign test sequences and pre-onset parts of onset sequences
    tot, nal = 0, 0
    for _, s in ben.groupby(["case", "seed", "seq"]):
        a = s.sort_values("k")[col].values; hit = np.flatnonzero(a)
        if hit.size: tot += hit[0] + 1; nal += 1
        else: tot += len(a)
    arl0 = tot / nal if nal else np.inf
    dl = []
    on = t[t.kind == "onset"]
    for _, s in on.groupby(["case", "seed", "seq"]):
        s = s.sort_values("k"); a = s[col].values[s.k.values >= s.onset.values[0]]; hit = np.flatnonzero(a)
        dl.append(hit[0] if hit.size else np.nan)
    dl = np.array(dl, float); det = ~np.isnan(dl)
    return dict(FPR=fpr, Recall=rec, Pd=det.mean(), Missed=1 - det.mean(), delay_median=np.nanmedian(dl) if det.any() else np.nan,
                delay_mean=np.nanmean(dl) if det.any() else np.nan, ARL1=np.nanmean(dl + 1) if det.any() else np.nan, ARL0=arl0,
                benign_segments_alarmed=nal)
rows = []
for lab, col, mode in RULES:
    r = dict(rule=lab, col=col, threshold=mode, **seg_metrics(test, col))
    per = pd.DataFrame([seg_metrics(t, col) for _, t in test.groupby("seed")])
    for m in ["FPR", "Recall", "Pd"]:
        r[m + "_sd_seeds"] = per[m].std(ddof=1)
    rows.append(r)
res = pd.DataFrame(rows); res.to_csv(f"{OUT}/T_onset_summary.csv", index=False)
# per case
pc = pd.DataFrame([dict(case=c, rule=l, col=col, threshold=mode, **seg_metrics(t, col)) for c, t in test.groupby("case") for l, col, mode in RULES])
pc.to_csv(f"{OUT}/T_onset_by_case.csv", index=False)
# constant severity: class x tier
SEL = ["a_nis", "a_cusum", "a_seq", "d_k2", "m01_nis", "m01_win", "m01_ewma", "m01_cusum_g", "m01_theta_seq"]
on = test[test.kind == "onset"]
ct = []
for (cls, tier), t in on.groupby(["cls", "tier"]):
    for col in SEL:
        m = seg_metrics(t, col)
        ct.append(dict(cls=cls, tier=tier, col=col, Recall=m["Recall"], Pd=m["Pd"], delay_median=m["delay_median"]))
pd.DataFrame(ct).to_csv(f"{OUT}/T_onset_class_tier.csv", index=False)
# kappa / tau sensitivity of the recursion on the onset protocol (post hoc from the NIS stream)
ks = []
for kap in [0.25, 0.5, 1.0]:
    gg = np.zeros(len(test)); prev_key = None; gv = 0.0
    keys = list(zip(test.case, test.seed, test.kind, test.seq)); yv = test.y.values
    for i in range(len(test)):
        if keys[i] != prev_key: gv = 0.0; prev_key = keys[i]
        gv = max(0.0, gv + yv[i] - kap); gg[i] = gv
    for tau in [3.0, 5.0, 7.0]:
        test["_a"] = (gg > tau).astype(int)
        ks.append(dict(kappa=kap, tau=tau, **seg_metrics(test, "_a")))
pd.DataFrame(ks).to_csv(f"{OUT}/T_onset_kappa_tau.csv", index=False)
test.drop(columns=["_a"]).to_csv(f"{OUT}/onset_scored_with_rules.csv", index=False)
pd.set_option("display.width", 250)
print(res[["rule", "threshold", "FPR", "Recall", "Pd", "delay_median", "ARL1", "ARL0", "benign_segments_alarmed"]].round(4).to_string())
print(pd.DataFrame(ks).round(4).to_string())
