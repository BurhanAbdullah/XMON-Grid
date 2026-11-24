#!/usr/bin/env python3
"""Builds the data-driven paragraphs of the revision from the analysis CSVs (no number typed by hand).
Usage: python build_text.py <ana_dir>"""
import sys, json, numpy as np, pandas as pd
A = sys.argv[1]
on = pd.read_csv(f"{A}/T_onset_summary.csv"); ct = pd.read_csv(f"{A}/T_onset_class_tier.csv")
okt = pd.read_csv(f"{A}/T_onset_kappa_tau.csv"); ps = pd.read_csv(f"{A}/T_param_sensitivity.csv")
cz = pd.read_csv(f"{A}/calib_size_all.csv"); oo = pd.read_csv(f"{A}/T_outage_resolved.csv").set_index("case")
of = pd.read_csv(f"{A}/T_outage_fixed_state.csv").set_index("case"); vm = pd.read_csv(f"{A}/variants_meta.csv").set_index("case")
sc = pd.read_csv(f"{A}/onset_scored_with_rules.csv")
def O(r, t="fixed"): return on[(on.rule == r) & (on.threshold == t)].iloc[0]
def pc(x): return f"{100*x:.1f}%"
fx = {k: O(v) for k, v in [("nis", "NIS test, chi-square threshold"), ("cu", "Sequential monitor (tau=5)"), ("th", "Leaky accumulator (tau_Theta)"), ("k2", "Quorum K=2")]}
mt = {k: O(v, "alpha=0.01") for k, v in [("nis", "NIS (single cycle)"), ("win", "Sliding sum of NIS (10 cycles)"), ("ewma", "EWMA of standardized NIS"), ("g", "CUSUM recursion g"), ("th", "Leaky accumulator Theta")]}
m5 = {k: O(v, "alpha=0.05") for k, v in [("nis", "NIS (single cycle)"), ("win", "Sliding sum of NIS (10 cycles)"), ("ewma", "EWMA of standardized NIS"), ("g", "CUSUM recursion g"), ("th", "Leaky accumulator Theta")]}
# class-level recall pooled over tiers, and median delay among detected sequences, for the two low-amplitude classes
on_ = sc[sc.kind == "onset"]
def cls_stats(cls, col):
    t = on_[on_.cls == cls]; rec = t[t.y_true == 1][col].mean(); dl = []
    for _, s in t.groupby(["case", "seed", "seq"]):
        a = s.sort_values("k"); a = a[a.k >= a.onset.iloc[0]][col].values; h = np.flatnonzero(a); dl.append(h[0] if h.size else np.nan)
    dl = np.array(dl, float)
    return rec, np.nanmedian(dl) if (~np.isnan(dl)).any() else np.nan, (~np.isnan(dl)).mean()
cs = {(c, k): cls_stats(c, col) for c in ["load_shift", "stealth_drift"] for k, col in
      [("g", "m01_cusum_g"), ("th", "m01_theta_seq"), ("ewma", "m01_ewma"), ("win", "m01_win"), ("nis", "m01_nis"), ("cu", "a_cusum"), ("k2", "d_k2")]}
pd.DataFrame([dict(cls=c, det=k, recall=v[0], median_delay=v[1], Pd=v[2]) for (c, k), v in cs.items()]).to_csv(f"{A}/T_onset_lowamp_classes.csv", index=False)
def T4(cls, col): return ct[(ct.cls == cls) & (ct.col == col) & (ct.tier == "Tier 4 (Severe)")].Recall.iloc[0]
def T1(cls, col): return ct[(ct.cls == cls) & (ct.col == col) & (ct.tier == "Tier 1 (Subtle)")].Recall.iloc[0]
easy = ct[(ct.cls.isin(["fdia", "branch_outage"])) & (ct.tier != "Tier 1 (Subtle)") & (ct.col.isin(["m01_cusum_g", "m01_ewma", "m01_win", "m01_nis"]))].Recall.min()

ACC = ["m01_cusum_g", "m01_theta_seq", "m01_ewma", "m01_win"]
tiers = ["Tier 1 (Subtle)", "Tier 2 (Moderate)", "Tier 3 (Strong)", "Tier 4 (Severe)"]
nodip = all(ct[(ct.cls == c) & (ct.col == col) & (ct.tier == tiers[1])].Recall.iloc[0] >= ct[(ct.cls == c) & (ct.col == col) & (ct.tier == tiers[0])].Recall.iloc[0] - 1e-12
            for c in ct.cls.unique() for col in ACC)
peak = all(ct[(ct.cls == c) & (ct.col == col)].set_index("tier").loc[tiers].Recall.values.argmax() >= 2 or
           ct[(ct.cls == c) & (ct.col == col)].Recall.max() >= ct[(ct.cls == c) & (ct.col == col) & (ct.tier.isin(tiers[2:]))].Recall.max() - 1e-12
           for c in ct.cls.unique() for col in ACC)
mono = all(np.all(np.diff(ct[(ct.cls == c) & (ct.col == col)].set_index("tier").loc[tiers].Recall.values) >= -1e-12) for c in ct.cls.unique() for col in ACC)
assert nodip and peak
SEV = ("With one class and one constant tier per sequence, the Moderate-tier dip disappears. For every anomaly class and every "
       "accumulating statistic, recall at the Moderate tier is at least as high as at the Subtle tier, and the highest recall falls at "
       "the Strong or Severe tier" + (", rising monotonically with severity." if mono else "."))
nm = {"case9": "9-bus", "case14": "14-bus", "case30": "30-bus", "case118": "118-bus"}
def caselist(cs_):
    order = [c for c in ["case9", "case14", "case30", "case118"] if c in cs_]; nums = [nm[c].replace("-bus", "") for c in order]
    return (nums[0] + "-bus case") if len(nums) == 1 else (", ".join(n_ + "-" for n_ in nums[:-1]) + (", and " if len(nums) > 2 else " and ") + nums[-1] + "-bus cases")

# per-case check of the low-amplitude advantage of the long-memory accumulators
lo = on_[(on_.y_true == 1) & on_.cls.isin(["load_shift", "stealth_drift"])]
pcase = lo.groupby("case")[["m01_cusum_g", "m01_theta_seq", "m01_ewma", "m01_win", "m01_nis"]].mean()
pcase.to_csv(f"{A}/T_onset_lowamp_by_case.csv")
LONG_WINS = [c for c in pcase.index if min(pcase.loc[c, "m01_cusum_g"], pcase.loc[c, "m01_theta_seq"]) > max(pcase.loc[c, "m01_ewma"], pcase.loc[c, "m01_win"])]
LOSE = [c for c in pcase.index if c not in LONG_WINS]
yk = {c: (lo[lo.case == c].y > 0.5).mean() for c in pcase.index}
def lose_txt():
    if not LOSE: return "."
    parts = [f"{pcase.loc[c,'m01_cusum_g']:.4f} for g_{{k}}, {pcase.loc[c,'m01_theta_seq']:.4f} for Θ_{{k}}, {pcase.loc[c,'m01_ewma']:.4f} for the EWMA, and {pcase.loc[c,'m01_win']:.4f} for the sliding sum" for c in LOSE]
    return (", where the recall on these cycles is " + " and ".join(parts) + ". On " + ("that case" if len(LOSE) == 1 else "those cases") +
            " y_{k} exceeds κ=0.5 in only " + ", ".join(pc(yk[c]) for c in LOSE) + " of these cycles, so g_{k} rarely grows.")
txt = {}
txt["p1"] = (
 f"With the start-up transient removed by the warm-up, the sequential monitor and the quorum raise few false alarms. The quorum has FPR "
 f"{fx['k2'].FPR:.4f} and the sequential monitor {fx['cu'].FPR:.4f}, against {fx['nis'].FPR:.4f} for the NIS test with its χ^{{2}} "
 "threshold, whose false alarms remain frequent because of the miscalibration discussed in Section III-E. The fixed thresholds of the "
 "sequential monitor, the quorum, and the leaky accumulator rest on calibration moments inflated by the flat-start transient, so "
 f"after convergence they are conservative. The sequential monitor detects {pc(fx['cu'].Pd)} of the onset sequences within 30 cycles, "
 f"the quorum {pc(fx['k2'].Pd)}, and the leaky accumulator {pc(fx['th'].Pd)}, and their post-onset recall is "
 f"{fx['cu'].Recall:.4f}, {fx['k2'].Recall:.4f}, and {fx['th'].Recall:.4f}. Detected sequences are found quickly: the median delay "
 f"is {fx['cu'].delay_median:.0f} cycles for the sequential monitor and the quorum and {fx['th'].delay_median:.0f} cycles for the "
 f"leaky accumulator, with ARL_{{1}} of {fx['cu'].ARL1:.2f}, {fx['k2'].ARL1:.2f}, and {fx['th'].ARL1:.2f}. The misses concentrate in "
 "the Subtle tier of the additive FDIA and in the voltage-scale and drift classes (Fig. 13).")
txt["p2"] = (
 "At thresholds frozen on the benign calibration sequences, the continuous statistics run at realized test FPRs of "
 f"{min(v.FPR for v in mt.values()):.4f} to {max(v.FPR for v in mt.values()):.4f}, close to the nominal 0.01. Detection probability "
 "within the window is a weak discriminator here, because the additive FDIA and the branch outage above the Subtle tier are detected "
 f"{'in every cycle' if easy >= 0.9995 else 'in at least ' + pc(easy) + ' of cycles'} by every statistic, and because a statistic with more false alarms also alarms more often by "
 f"chance after the onset. The post-onset recall separates them. It is {mt['g'].Recall:.4f} for g_{{k}}, {mt['th'].Recall:.4f} for "
 f"Θ_{{k}}, {mt['win'].Recall:.4f} for the sliding sum, {mt['ewma'].Recall:.4f} for the EWMA, and {mt['nis'].Recall:.4f} for the "
 "single-cycle NIS. The difference lies in the two persistent low-amplitude classes. On voltage-scale cycles the recall is "
 f"{cs[('load_shift','g')][0]:.4f} for g_{{k}} and {cs[('load_shift','th')][0]:.4f} for Θ_{{k}}, against "
 f"{cs[('load_shift','ewma')][0]:.4f} for the EWMA, {cs[('load_shift','win')][0]:.4f} for the sliding sum, and "
 f"{cs[('load_shift','nis')][0]:.4f} for the single-cycle NIS, and on drift cycles it is {cs[('stealth_drift','g')][0]:.4f}, "
 f"{cs[('stealth_drift','th')][0]:.4f}, {cs[('stealth_drift','ewma')][0]:.4f}, {cs[('stealth_drift','win')][0]:.4f}, and "
 f"{cs[('stealth_drift','nis')][0]:.4f}. At the Severe tier, g_{{k}} retains {pc(T4('load_shift','m01_cusum_g'))} of voltage-scale "
 f"and {pc(T4('stealth_drift','m01_cusum_g'))} of drift cycles, Θ_{{k}} {pc(T4('load_shift','m01_theta_seq'))} and "
 f"{pc(T4('stealth_drift','m01_theta_seq'))}, the EWMA {pc(T4('load_shift','m01_ewma'))} and {pc(T4('stealth_drift','m01_ewma'))}, "
 f"and the sliding sum {pc(T4('load_shift','m01_win'))} and {pc(T4('stealth_drift','m01_win'))}. At the Subtle tier no statistic "
 f"exceeds {pc(max(T1(c, col) for c in ['load_shift','stealth_drift'] for col in ['m01_cusum_g','m01_theta_seq','m01_ewma','m01_win','m01_nis']))} "
 "on these two classes. The advantage of the long-memory accumulators on the voltage-scale and drift cycles holds on the " + caselist(LONG_WINS) + (" but not on the " + caselist(LOSE) if LOSE else "") + lose_txt() + " " + SEV + " This points to the interleaving of the original protocol, rather than the amplitude, as the cause of the dip in "
 f"Fig. 10. At a calibrated rate of 0.05 the ordering is unchanged (post-onset recall {m5['g'].Recall:.4f}, {m5['th'].Recall:.4f}, "
 f"{m5['win'].Recall:.4f}, {m5['ewma'].Recall:.4f}, and {m5['nis'].Recall:.4f}).")
txt["p3"] = (
 "The two experiments agree that temporal accumulation of innovation evidence is more important than the single-cycle statistic or "
 "the voting rule. They differ on whether the accumulation rule matters. Under the reset protocol, every accumulator separates the "
 "persistent anomalies perfectly once the filter settles, and the CUSUM recursion cannot be told apart from an EWMA or a window sum. "
 "When the anomaly starts after convergence and thresholds are calibrated beforehand, the long-memory accumulators, the CUSUM "
 "recursion and the leaky accumulator, retain more of the low-amplitude voltage-scale and drift cycles than the EWMA with λ=0.2 and "
 "the 10-cycle window, whose memory is short, pooled over the four systems and on the " + caselist(LONG_WINS) + (", but not on the " + caselist(LOSE) if LOSE else "") + ". The CUSUM recursion is not uniquely effective, since the leaky accumulator performs "
 "similarly, and these comparisons are empirical and specific to the synthetic scenarios, the single onset time, and the parameter "
 "values tested. Accumulation-based approaches to detecting injected data and drift have been explored in [13], [14]. The present "
 "results are consistent with their underlying motivation, although no direct comparison with those methods was conducted.")
# calibration size

def crosses(c):
    g = cz[cz.case == c].pivot(index="n", columns="seed", values="tau_comp")
    return list(g.loc[g.index.min()].rank()) != list(g.loc[g.index.max()].rank())
CROSS = [c for c in cz.case.unique() if crosses(c)]
g = cz.groupby(["case", "seed"])
rng_ = {c: (cz[cz.case == c].tau_comp.min(), cz[cz.case == c].tau_comp.max()) for c in cz.case.unique()}
_items = [f"{rng_[c][0]:.4f} and {rng_[c][1]:.4f} on the {nm[c]} case" for c in [x for x in ["case9", "case14", "case30", "case118"] if x in rng_]]
txt["calsize"] = ("Over 50 to 400 calibration samples, τ_{comp} varies between " + ", ".join(_items[:-1]) + ", and " + _items[-1] +
    "." + ((" The ordering of the seeds changes with the sample size on the " + caselist(CROSS) + ", so the 99th-percentile "
    "threshold is not stable at these sample sizes.") if CROSS else " The 99th-percentile threshold is not stable at these sample sizes."))
# parameter sensitivity
def P_(setting, rule): return ps[(ps.setting == setting) & (ps.rule == rule)].iloc[0]
b = P_("base", "Sequential monitor"); bk = P_("base", "Quorum K=2")
k25 = P_("kappa=0.25, tau=5", "Sequential monitor"); k1 = P_("kappa=1.0, tau=5", "Sequential monitor")
t3 = P_("kappa=0.5, tau=3", "Sequential monitor"); t7 = P_("kappa=0.5, tau=7", "Sequential monitor")
q01, q10, r05, r2 = (P_(s, "Sequential monitor") for s in ["Qx0.1", "Qx10", "Rx0.5", "Rx2"])
q01k, q10k, r05k, r2k = (P_(s, "Quorum K=2") for s in ["Qx0.1", "Qx10", "Rx0.5", "Rx2"])
n01, n10, n05, n2 = (P_(s, "NIS test") for s in ["Qx0.1", "Qx10", "Rx0.5", "Rx2"]); nb = P_("base", "NIS test")
ok = okt.set_index(["kappa", "tau"])
txt["params"] = (
 "Table XVIII varies one parameter at a time on the original protocol. Over κ∈{0.25,0.5,1.0} and τ_{cusum}∈{3,5,7}, the F1 of the "
 f"sequential monitor stays between {ps[(ps.factor=='kappa/tau')&(ps.rule=='Sequential monitor')].F1.min():.4f} and "
 f"{ps[(ps.factor=='kappa/tau')&(ps.rule=='Sequential monitor')].F1.max():.4f}, and the main effect is on false alarms: its FPR falls "
 f"from {k25.FPR:.4f} at κ=0.25 to {k1.FPR:.4f} at κ=1.0, and from {t3.FPR:.4f} at τ_{{cusum}}=3 to {t7.FPR:.4f} at τ_{{cusum}}=7. "
 f"The quorum stays between F1 {ps[(ps.factor=='kappa/tau')&(ps.rule=='Quorum K=2')].F1.min():.4f} and "
 f"{ps[(ps.factor=='kappa/tau')&(ps.rule=='Quorum K=2')].F1.max():.4f}. The estimator covariances matter more for the NIS test and the quorum. Scaling Q by 0.1 or 10 "
 f"gives sequential-monitor F1 {q01.F1:.4f} and {q10.F1:.4f} and quorum FPR {q01k.FPR:.4f} and {q10k.FPR:.4f}, against {b.F1:.4f} and "
 f"{bk.FPR:.4f} at the reported setting. Scaling R by 0.5 or 2 gives sequential-monitor F1 {r05.F1:.4f} and {r2.F1:.4f} and quorum FPR "
 f"{r05k.FPR:.4f} and {r2k.FPR:.4f}. The NIS test is the stream most affected by Q and R, with FPR {n01.FPR:.4f} and {n10.FPR:.4f} for "
 f"the two Q scalings and {n05.FPR:.4f} and {n2.FPR:.4f} for the two R scalings, against {nb.FPR:.4f}. In the onset experiment the same "
 f"κ and τ_{{cusum}} grid moves the post-onset recall of the sequential monitor between {okt.Recall.min():.4f} and {okt.Recall.max():.4f} "
 f"and its FPR between {okt.FPR.min():.4f} and {okt.FPR.max():.4f}. The reported setting is therefore not the best on F1 within this grid, and the results "
 "depend on the covariance settings of the estimator, which were fixed a priori and not tuned.")
txt["concl"] = (
 "When the anomaly began after the estimator had converged and thresholds were calibrated on separate benign data, the "
 f"long-memory accumulators retained the most low-amplitude cycles (post-onset recall {mt['g'].Recall:.4f} for the CUSUM recursion "
 f"and {mt['th'].Recall:.4f} for the leaky accumulator, against {mt['ewma'].Recall:.4f} for the EWMA, {mt['win'].Recall:.4f} for "
 f"the window sum, and {mt['nis'].Recall:.4f} for the single-cycle NIS), so under onset conditions the memory length of the "
 "accumulator also mattered, on the " + caselist(LONG_WINS) + (" but not on the " + caselist(LOSE) if LOSE else "") + ".")
# outage variant
rows = []
for c in ["case9", "case14", "case30", "case118"]:
    if c in oo.index: rows.append(c)
oo_k2 = oo.loc[rows, "d_k2"]; of_k2 = of.loc[rows, "d_k2"]
import re
dv = {c: re.findall(r"max\|V_post-V_pre\|=([0-9.]+)", vm.loc[c, "gen"])[0] for c in rows}
txt["outage"] = (
 "A second outage construction checks the dependence on the fixed pre-outage state. It switches off the same branch, re-solves the "
 "AC power flow with PYPOWER, and generates the measurements from the physically settled post-outage state with the same "
 "tier-dependent state noise and the repository calibration, detectors, and measurement function (one 60-cycle sequence per case and "
 f"seed). The largest change of a bus voltage magnitude between the pre- and post-outage solutions ranges from "
 f"{min(float(v) for v in dv.values()):.5f} p.u. on the {nm[min(dv, key=lambda c: float(dv[c]))]} case to "
 f"{max(float(v) for v in dv.values()):.5f} p.u. on the {nm[max(dv, key=lambda c: float(dv[c]))]} case. K=2 detects {oo_k2.min():.4f} to {oo_k2.max():.4f} of these cycles, "
 f"against {of_k2.min():.4f} to {of_k2.max():.4f} for the fixed-state outage over five seeds, and the NIS test and the sequential "
 f"monitor detect at least {min(oo.loc[rows,'a_nis'].min(), oo.loc[rows,'a_cusum'].min()):.4f}. On these four branches the outage "
 "class is detected almost completely in both constructions, so its detectability here does not hinge on whether the equilibrium is "
 "recomputed.")
txt["lose_cases"] = caselist(LOSE) if LOSE else ""
json.dump(txt, open(f"{A}/onset_text.json", "w"), ensure_ascii=False, indent=1)
rows18 = [["base", "Reported (κ=0.5, τ_{cusum}=5, Q, R)"], ["kappa=0.25, tau=5", "κ=0.25"], ["kappa=1.0, tau=5", "κ=1.0"],
          ["kappa=0.5, tau=3", "τ_{cusum}=3"], ["kappa=0.5, tau=7", "τ_{cusum}=7"], ["Qx0.1", "Q×0.1"], ["Qx10", "Q×10"], ["Rx0.5", "R×0.5"], ["Rx2", "R×2"]]
json.dump(rows18, open(f"{A}/param_rows.json", "w"), ensure_ascii=False)
for k, v in txt.items(): print(f"--- {k}\n{v}\n")
